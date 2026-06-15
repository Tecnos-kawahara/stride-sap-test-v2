"""Tests for stride_harness_report.py (v5.1 harness marker)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))
from stride_harness_report import build_harness_report, _read_coverage_pct, _find_gaps


pytestmark = pytest.mark.harness


def _setup_full_project(p: Path) -> None:
    """Set up a project with all controls present."""
    tools = p / "sdd-templates" / "tools"
    tools.mkdir(parents=True)
    hooks = p / "sdd-templates" / "hooks"
    hooks.mkdir(parents=True)
    for name in [
        "pr_readiness_checker.py", "stride_lint.py", "spec_drift_detector.py",
        "stride_security_checker.py", "stride_health.py", "multi_model_evaluator.py",
    ]:
        (tools / name).write_text("")
    (hooks / "phase_gate_hook.py").write_text("")
    (hooks / "post_edit_guard.py").write_text("")
    tests = p / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("")
    ci = p / ".github" / "workflows"
    ci.mkdir(parents=True)
    (ci / "ci.yml").write_text("")


# ---------------------------------------------------------------------------
# build_harness_report
# ---------------------------------------------------------------------------

def test_report_has_required_keys():
    with tempfile.TemporaryDirectory() as d:
        r = build_harness_report(Path(d))
    assert "coverage_pct" in r
    assert "controls" in r
    assert "gaps" in r
    assert "summary" in r


def test_report_empty_project_has_gaps():
    with tempfile.TemporaryDirectory() as d:
        r = build_harness_report(Path(d))
    assert len(r["gaps"]) > 0
    assert r["summary"] != "FULL"


def test_report_full_project_no_gaps():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        _setup_full_project(p)
        r = build_harness_report(p)
    assert r["gaps"] == []
    assert r["summary"] == "FULL"


def test_report_controls_counts():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        tools = p / "sdd-templates" / "tools"
        tools.mkdir(parents=True)
        (tools / "stride_lint.py").write_text("")
        r = build_harness_report(p)
    assert r["controls"]["present"] >= 1
    assert r["controls"]["total"] >= 1
    assert 0 <= r["controls"]["pct"] <= 100


def test_report_coverage_pct_none_when_absent():
    with tempfile.TemporaryDirectory() as d:
        r = build_harness_report(Path(d))
    assert r["coverage_pct"] is None


def test_report_coverage_pct_from_file():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        cov = p / "coverage"
        cov.mkdir()
        (cov / "coverage-summary.json").write_text(json.dumps({
            "total": {"lines": {"pct": 91.3}}
        }))
        r = build_harness_report(p)
    assert r["coverage_pct"] == 91.3


# ---------------------------------------------------------------------------
# _read_coverage_pct
# ---------------------------------------------------------------------------

def test_read_coverage_pct_coverage_subdir():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "coverage").mkdir()
        (p / "coverage" / "coverage-summary.json").write_text(json.dumps({
            "total": {"lines": {"pct": 77.0}}
        }))
        assert _read_coverage_pct(p) == 77.0


def test_read_coverage_pct_root_level():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        (p / "coverage-summary.json").write_text(json.dumps({
            "total": {"lines": {"pct": 63.5}}
        }))
        assert _read_coverage_pct(p) == 63.5


def test_read_coverage_pct_none_when_absent():
    with tempfile.TemporaryDirectory() as d:
        assert _read_coverage_pct(Path(d)) is None


# ---------------------------------------------------------------------------
# _find_gaps
# ---------------------------------------------------------------------------

def test_find_gaps_no_tests():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        r = build_harness_report(p)
        gap_text = " ".join(r["gaps"])
    assert "test" in gap_text.lower()


def test_find_gaps_no_ci():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)
        # Add tests but no CI
        tests = p / "tests"
        tests.mkdir()
        (tests / "test_x.py").write_text("")
        r = build_harness_report(p)
        gap_text = " ".join(r["gaps"])
    assert "CI" in gap_text or "ci" in gap_text.lower() or "github" in gap_text.lower()
