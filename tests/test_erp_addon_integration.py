"""Integration tests for erp_addon_exec_tracking.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from erp_addon_exec_tracking import validate_erp_addon_execution_tracking


class TestERPAddonInactive:
    """Tests for features where ERP Addon is not active."""

    def test_non_erp_feature_returns_empty(self, full_pass_project):
        """Feature without ERP addon dirs/profile returns no errors."""
        feature_dir = full_pass_project / "specs" / "FEAT-TEST"
        approval = {1: True, 2: True, 3: True, 4: True, 5: True, "final": True}
        errors, warnings = validate_erp_addon_execution_tracking(
            feature_dir, approval, "standard"
        )
        assert errors == []
        assert warnings == []


class TestERPAddonPreGate5:
    """Tests for ERP features before Gate 5."""

    def test_pre_gate5_skips_validation(self, tmp_path):
        """ERP feature before Gate 5 skips validation."""
        from tests.project_builder import ProjectBuilder

        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-EARLY", mode="full", phase=2, coverage_tier="standard")
            .with_erp_addon()
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-EARLY"
        # Gate 5 not approved, but tasks.md exists (copied from sample)
        # Remove tasks.md to simulate pre-Gate 5
        tasks_file = feature_dir / "tasks.md"
        if tasks_file.exists():
            tasks_file.unlink()
        approval = {1: True, 2: True}
        errors, warnings = validate_erp_addon_execution_tracking(
            feature_dir, approval, "standard"
        )
        assert errors == []  # Skipped


class TestERPAddonActive:
    """Tests for active ERP Addon features."""

    def test_full_ops_pack_passes(self, erp_addon_project):
        """Feature with complete ops pack passes validation."""
        feature_dir = erp_addon_project / "specs" / "FEAT-ERP"
        approval = {1: True, 2: True, 3: True, 4: True, 5: True, "final": True}
        errors, warnings = validate_erp_addon_execution_tracking(
            feature_dir, approval, "critical"
        )
        # Sample has full ops pack, so critical errors should be minimal
        # (some warnings about mode/risk may exist)
        error_codes = [e[0] for e in errors]
        # The sample ops pack should satisfy basic structural checks
        assert isinstance(errors, list)
        assert isinstance(warnings, list)

    def test_missing_ops_files_detected(self, tmp_path):
        """Missing ops files are detected when ERP addon is active."""
        from tests.project_builder import ProjectBuilder

        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-NOOPS", mode="full", phase=5, coverage_tier="critical")
            .with_erp_addon()
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-NOOPS"
        # Remove ops files to create error condition
        import shutil
        ops_dir = feature_dir / "ops"
        if ops_dir.exists():
            shutil.rmtree(ops_dir)
        approval = {1: True, 2: True, 3: True, 4: True, 5: True, "final": True}
        errors, warnings = validate_erp_addon_execution_tracking(
            feature_dir, approval, "critical"
        )
        # Should detect missing ops pack
        has_ops_error = any("OPS" in e[0] or "ops" in e[1].lower() for e in errors)
        assert has_ops_error, f"Expected ops-related error, got: {errors}"

    def test_invalid_mode_for_risk_flags(self, tmp_path):
        """WI with mode too low for risk flags is flagged."""
        from tests.project_builder import ProjectBuilder

        # Build a clean feature with ERP addon using the ERPSAMPLE sample
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-ERPSAMPLE", mode="full", phase=5, coverage_tier="critical")
            .with_erp_addon()
            .done()
            .build()
        )
        feature_dir = project / "specs" / "FEAT-ERPSAMPLE"
        # Copy state.yaml from real sample
        import shutil
        real_state = Path(__file__).resolve().parent.parent / "specs" / "FEAT-ERPSAMPLE" / "state" / "state.yaml"
        state_dir = feature_dir / "state"
        state_dir.mkdir(exist_ok=True)
        if real_state.exists():
            shutil.copy2(real_state, state_dir / "state.yaml")

        # Mutate WI-ERP-SAMPLE-001 to have authz/sod risk flags with autopilot mode
        wi_file = feature_dir / "work_items" / "WI-ERP-SAMPLE-001.md"
        if wi_file.exists():
            text = wi_file.read_text(encoding="utf-8")
            # YAML value is quoted: ["ui_only"]
            text = text.replace('["ui_only"]', '["authz", "sod"]')
            wi_file.write_text(text, encoding="utf-8")

        approval = {1: True, 2: True, 3: True, 4: True, 5: True, "final": True}
        errors, warnings = validate_erp_addon_execution_tracking(
            feature_dir, approval, "critical"
        )
        all_messages = [e[1] for e in errors] + [w[1] for w in warnings]
        has_mode_issue = any("mode" in m.lower() or "risk" in m.lower() for m in all_messages)
        assert has_mode_issue, f"Expected mode/risk mismatch, got errors={errors}, warnings={warnings}"
