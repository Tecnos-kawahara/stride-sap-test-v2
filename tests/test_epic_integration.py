"""Integration tests for Epic validation and progress tools."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from epic_validator import EpicValidator
from epic_progress_aggregator import aggregate_epic_progress, _format_json, _format_summary


class TestEpicValidator:
    """Tests for epic_validator.py."""

    def test_valid_epic_passes(self, enterprise_project):
        """Valid enterprise epic with features passes validation."""
        epic_dir = enterprise_project / "epics" / "EPIC-TEST"
        validator = EpicValidator(epic_dir)
        result = validator.validate()
        assert result.epic_id == "EPIC-TEST"
        # Structural validation should pass — no critical errors
        critical_errors = [e for e in result.errors if "MISSING_FILE" in e]
        assert not critical_errors, f"Unexpected critical errors: {critical_errors}"

    def test_missing_epic_design_detected(self, tmp_path):
        """Epic without epic_design.md is flagged."""
        epic_dir = tmp_path / "epics" / "EPIC-BROKEN"
        epic_dir.mkdir(parents=True)
        (epic_dir / "EPIC_APPROVAL.md").write_text("# Empty", encoding="utf-8")
        validator = EpicValidator(epic_dir)
        result = validator.validate()
        assert not result.is_valid, "Missing epic_design.md should cause errors"
        has_missing = any("MISSING_FILE" in e for e in result.errors)
        assert has_missing, f"Expected MISSING_FILE error, got: {result.errors}"

    def test_epic_id_regex_validated(self, enterprise_project):
        """Epic IDs that match the regex pass, and the validator identifies the epic."""
        epic_dir = enterprise_project / "epics" / "EPIC-TEST"
        validator = EpicValidator(epic_dir)
        result = validator.validate()
        assert result.epic_id == "EPIC-TEST"
        # No ID regex mismatch for valid epic
        id_errors = [e for e in result.errors if "ID_REGEX_MISMATCH" in e and "EPIC-TEST" in e]
        assert not id_errors, f"Valid epic ID should not trigger mismatch: {id_errors}"


class TestEpicProgress:
    """Tests for epic_progress_aggregator.py."""

    def test_progress_json_is_valid(self, enterprise_project):
        """JSON format output contains expected structure."""
        epic_dir = enterprise_project / "epics" / "EPIC-TEST"
        report = aggregate_epic_progress(epic_dir)
        json_str = _format_json(report)
        data = json.loads(json_str)
        assert "epic_id" in data
        assert data["epic_id"] == "EPIC-TEST"
        assert "features" in data or "summary" in data

    def test_summary_contains_epic_id(self, enterprise_project):
        """Summary output mentions the epic ID."""
        epic_dir = enterprise_project / "epics" / "EPIC-TEST"
        report = aggregate_epic_progress(epic_dir)
        summary = _format_summary(report)
        assert "EPIC-TEST" in summary


class TestEnterpriseLint:
    """Tests for stride_lint_enterprise.py integration."""

    def test_enterprise_lint_on_valid_feature(self, enterprise_project):
        """Enterprise lint on a properly linked feature returns a result."""
        from stride_lint_enterprise import EnterpriseValidator

        validator = EnterpriseValidator(enterprise_project)
        feature_dir = enterprise_project / "specs" / "FEAT-ETEST"
        result = validator.validate_feature_enterprise(feature_dir)
        # With proper epic_ref/team_id set, should return a result object
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        # epic_ref and team_id are set, so no MISSING_EPIC_REF or MISSING_TEAM_ID errors
        error_codes = [e.split(":")[0].strip() for e in result.errors]
        assert "MISSING_EPIC_REF" not in error_codes, f"epic_ref should be set: {result.errors}"
        assert "MISSING_TEAM_ID" not in error_codes, f"team_id should be set: {result.errors}"
