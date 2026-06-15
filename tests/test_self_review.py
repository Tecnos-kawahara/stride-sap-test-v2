"""Tests for self_review_loop() in multi_model_evaluator.py (v5.1 harness marker)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))
from multi_model_evaluator import self_review_loop, aggregate_results


pytestmark = pytest.mark.harness


# ---------------------------------------------------------------------------
# self_review_loop unit tests
# ---------------------------------------------------------------------------

def _make_review_packet(feature_dir: str, score: float = 75.0) -> dict:
    return {
        "feature_dir": feature_dir,
        "phase": "design",
        "prompt": "Evaluate this design...",
        "primary_result": {
            "overall": "FAIL",
            "weighted_score": score,
            "scores": {"A1": 70, "A2": 72, "A3": 68, "A4": 80},
            "critical_issues": [],
            "suggestions": [],
        },
    }


def test_self_review_returns_dict():
    """self_review_loop always returns a dict with 'issues' and 'iterations'."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        with mock.patch(
            "multi_model_evaluator._call_openai",
            return_value={"error": "API unavailable"},
        ):
            result = self_review_loop(packet)
    assert "issues" in result
    assert "iterations" in result


def test_self_review_no_critical_issues_returns_empty():
    """When model finds no additional critical issues, issues list is empty."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        mock_response = {
            "additional_issues": [],
            "false_positives": [],
            "confidence": "same",
        }
        with mock.patch("multi_model_evaluator._call_openai", return_value=mock_response):
            result = self_review_loop(packet, max_iters=1)
    assert result["issues"] == []


def test_self_review_critical_issue_surfaced():
    """When model finds a critical issue, it is included in issues."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        critical = {
            "criterion": "A1",
            "description": "SoD not enforced",
            "severity": "critical",
            "ref": "AC-US-FEAT-001-01",
        }
        mock_response = {
            "additional_issues": [critical],
            "false_positives": [],
            "confidence": "higher",
        }
        with mock.patch("multi_model_evaluator._call_openai", return_value=mock_response):
            result = self_review_loop(packet, max_iters=1)
    assert len(result["issues"]) == 1
    assert result["issues"][0]["severity"] == "critical"


def test_self_review_non_critical_not_included():
    """Non-critical additional issues are NOT included in issues list."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        minor = {
            "criterion": "A4",
            "description": "Minor scope note",
            "severity": "minor",
            "ref": "scope.out",
        }
        mock_response = {
            "additional_issues": [minor],
            "false_positives": [],
            "confidence": "same",
        }
        with mock.patch("multi_model_evaluator._call_openai", return_value=mock_response):
            result = self_review_loop(packet, max_iters=1)
    assert result["issues"] == []


def test_self_review_respects_max_iters():
    """self_review_loop stops after max_iters."""
    call_count = {"n": 0}

    def counting_call(prompt):
        call_count["n"] += 1
        return {
            "additional_issues": [
                {"criterion": "A1", "description": "issue", "severity": "critical", "ref": "x"}
            ],
            "false_positives": [],
            "confidence": "higher",
        }

    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        with mock.patch("multi_model_evaluator._call_openai", side_effect=counting_call):
            self_review_loop(packet, max_iters=3)
    # Should call at most 3 times
    assert call_count["n"] <= 3


def test_self_review_api_error_stops_loop():
    """If _call_openai returns an error, the loop stops early."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        with mock.patch(
            "multi_model_evaluator._call_openai",
            return_value={"error": "rate limit"},
        ):
            result = self_review_loop(packet, max_iters=3)
    # No issues found; loop stopped
    assert result["issues"] == []


def test_self_review_critical_updates_primary_overall():
    """Critical issues from review update primary_result overall to FAIL."""
    with tempfile.TemporaryDirectory() as d:
        primary = {
            "overall": "PASS",
            "weighted_score": 78.0,
            "scores": {"A1": 75, "A2": 80, "A3": 75, "A4": 82},
            "critical_issues": [],
            "suggestions": [],
        }
        packet = {
            "feature_dir": d,
            "phase": "design",
            "prompt": "...",
            "primary_result": primary,
        }
        critical = {
            "criterion": "A1",
            "description": "SoD gap",
            "severity": "critical",
            "ref": "spec.authz",
        }
        mock_response = {
            "additional_issues": [critical],
            "false_positives": [],
            "confidence": "higher",
        }
        with mock.patch("multi_model_evaluator._call_openai", return_value=mock_response):
            review_result = self_review_loop(packet, max_iters=1)

        # Simulate what main() does: attach critical issues to primary_result
        existing = primary.get("critical_issues", [])
        critical_from_review = [i for i in review_result["issues"] if i.get("severity") == "critical"]
        if critical_from_review:
            primary["critical_issues"] = existing + critical_from_review
            primary["overall"] = "FAIL"

        assert primary["overall"] == "FAIL"
        assert len(primary["critical_issues"]) == 1


def test_self_review_uses_alternative_key_critical_issues():
    """Review response using 'critical_issues' key (instead of 'additional_issues') is accepted."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        critical = {
            "criterion": "A2",
            "description": "AC not testable",
            "severity": "critical",
            "ref": "AC-001",
        }
        mock_response = {
            "critical_issues": [critical],
            "confidence": "higher",
        }
        with mock.patch("multi_model_evaluator._call_openai", return_value=mock_response):
            result = self_review_loop(packet, max_iters=1)
    assert len(result["issues"]) == 1


def test_self_review_borderline_score_range():
    """self_review_loop is designed for scores 70-85; verify it works at both edges."""
    for score in [70.0, 84.9]:
        with tempfile.TemporaryDirectory() as d:
            packet = _make_review_packet(d, score=score)
            with mock.patch(
                "multi_model_evaluator._call_openai",
                return_value={"additional_issues": [], "confidence": "same"},
            ):
                result = self_review_loop(packet, max_iters=1)
        assert result["issues"] == []


def test_self_review_empty_packet():
    """self_review_loop handles an empty packet without crashing."""
    result = self_review_loop({}, max_iters=1)
    assert "issues" in result
    assert "iterations" in result


def test_self_review_iterations_field():
    """self_review_loop always returns the max_iters value in 'iterations'."""
    with tempfile.TemporaryDirectory() as d:
        packet = _make_review_packet(d)
        with mock.patch(
            "multi_model_evaluator._call_openai",
            return_value={"additional_issues": [], "confidence": "same"},
        ):
            result = self_review_loop(packet, max_iters=2)
    assert result["iterations"] == 2
