"""Integration tests for run_resume_detector.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from run_resume_detector import detect_artifacts, RECOMMENDATIONS
from tests.project_builder import add_run_lifecycle


class TestNoArtifacts:
    def test_empty_run_is_implementation(self, tmp_path):
        """Empty run with .planning/ → IMPLEMENTATION (first artifact after .planning)."""
        run_dir = tmp_path / "runs" / "WI-001" / "RUN-001"
        run_dir.mkdir(parents=True)
        (run_dir / ".planning").mkdir()
        results, resume = detect_artifacts(run_dir)
        assert resume == "IMPLEMENTATION"

    def test_truly_empty_run(self, tmp_path):
        """Completely empty run dir → BEGINNING."""
        run_dir = tmp_path / "runs" / "WI-001" / "RUN-001"
        run_dir.mkdir(parents=True)
        results, resume = detect_artifacts(run_dir)
        assert resume == "BEGINNING"


class TestDecisionLogPresent:
    def test_decision_log_means_testing(self, tmp_path):
        feature = tmp_path / "specs" / "FEAT-X"
        feature.mkdir(parents=True)
        run_dir = add_run_lifecycle(feature, "WI-X-001", "RUN-001",
                                    artifacts=["findings", "plan", "decision_log"])
        results, resume = detect_artifacts(run_dir)
        assert resume == "TESTING"


class TestTestResultsPresent:
    def test_test_results_means_walkthrough(self, tmp_path):
        feature = tmp_path / "specs" / "FEAT-X"
        feature.mkdir(parents=True)
        run_dir = add_run_lifecycle(feature, "WI-X-001", "RUN-001",
                                    artifacts=["findings", "plan", "decision_log", "test_results"])
        results, resume = detect_artifacts(run_dir)
        assert resume == "WALKTHROUGH"


class TestWalkthroughPresent:
    def test_walkthrough_means_complete(self, tmp_path):
        feature = tmp_path / "specs" / "FEAT-X"
        feature.mkdir(parents=True)
        run_dir = add_run_lifecycle(feature, "WI-X-001", "RUN-001",
                                    artifacts=["findings", "plan", "decision_log", "test_results", "walkthrough"])
        results, resume = detect_artifacts(run_dir)
        assert resume == "COMPLETE"


class TestRecommendations:
    def test_interrupted_run_has_recommendation(self, interrupted_run_project):
        feature = interrupted_run_project / "specs" / "FEAT-RUN"
        run_dir = feature / "runs" / "WI-RUN-001" / "RUN-20260301-1000"
        results, resume = detect_artifacts(run_dir)
        assert resume in RECOMMENDATIONS
        rec = RECOMMENDATIONS[resume]
        assert len(rec) > 0
