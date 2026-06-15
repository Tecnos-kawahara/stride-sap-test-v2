"""Integration tests for pr_readiness_checker.py with real project fixtures."""

import subprocess
import sys
from pathlib import Path

import pytest


class TestPRReadinessImport:
    """Import API tests for pr_readiness_checker."""

    def test_check_stride_lint_valid_project(self, full_pass_project):
        """The 7-check pipeline should not crash on a valid project."""
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from pr_readiness_checker import check_stride_lint
            result = check_stride_lint(full_pass_project)
            assert result["status"] in ("PASS", "FAIL", "WARN")
            # If WARN, it must NOT be due to attribute error
            if result["status"] == "WARN":
                assert "attribute" not in result.get("detail", "").lower()
        finally:
            sys.path.pop(0)

    def test_check_spec_drift_valid_project(self, full_pass_project):
        sys.path.insert(0, str(full_pass_project / "sdd-templates" / "tools"))
        try:
            from pr_readiness_checker import check_spec_drift
            result = check_spec_drift(full_pass_project)
            assert result["status"] in ("PASS", "FAIL", "WARN", "SKIP")
        finally:
            sys.path.pop(0)


class TestPRReadinessCLI:
    """CLI smoke tests for stride pr-check."""

    def test_stride_pr_check_does_not_crash(self, full_pass_project):
        result = subprocess.run(
            ["sdd-templates/bin/stride", "pr-check", str(full_pass_project)],
            cwd=str(full_pass_project),
            capture_output=True, text=True,
        )
        # Should not crash with unhandled exception
        assert "Traceback" not in result.stderr, (
            f"pr-check crashed with traceback:\n{result.stderr}"
        )
