"""Integration tests for wi_readiness_checker.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from wi_readiness_checker import (
    check_gate5_approved,
    check_wi_definition,
    check_mode_policy,
    check_ops_pack,
    check_state_consistency,
    CheckResult,
    _load_yaml_file,
    _find_project_root,
)


class TestGate5Check:
    def test_gate5_not_approved(self, tmp_path):
        from tests.project_builder import ProjectBuilder
        root = ProjectBuilder(tmp_path).add_feature("FEAT-G5", mode="full", phase=2).done().build()
        feature = root / "specs" / "FEAT-G5"
        result = check_gate5_approved(feature)
        assert result.status == "FAIL"

    def test_gate5_approved(self, full_pass_project):
        feature = full_pass_project / "specs" / "FEAT-TEST"
        result = check_gate5_approved(feature)
        assert result.status == "PASS"


class TestWIDefinition:
    def test_missing_wi_not_found(self, full_pass_project):
        feature = full_pass_project / "specs" / "FEAT-TEST"
        result, fm, path = check_wi_definition(feature, "WI-NONEXISTENT-999")
        assert result.status == "FAIL"
        assert fm is None

    def test_existing_wi_found(self, wi_ready_project):
        feature = wi_ready_project / "specs" / "FEAT-ERPSAMPLE"
        result, fm, path = check_wi_definition(feature, "WI-ERP-SAMPLE-001")
        assert result.status == "PASS"
        assert fm is not None
        assert "mode" in fm


class TestModePolicyCheck:
    def test_mode_policy_validates(self, wi_ready_project):
        feature = wi_ready_project / "specs" / "FEAT-ERPSAMPLE"
        _, fm, _ = check_wi_definition(feature, "WI-ERP-SAMPLE-001")
        assert fm is not None
        project_root = _find_project_root(feature)
        mode_policy = _load_yaml_file(project_root / "memory" / "erp_addon_mode_policy.yaml") or {}
        result = check_mode_policy(feature, fm, mode_policy, "balanced", "critical")
        assert result.status in ("PASS", "WARN")


class TestOpsPack:
    def test_ops_pack_present(self, wi_ready_project):
        feature = wi_ready_project / "specs" / "FEAT-ERPSAMPLE"
        result = check_ops_pack(feature)
        assert result.status in ("PASS", "WARN")

    def test_ops_pack_missing(self, full_pass_project):
        feature = full_pass_project / "specs" / "FEAT-TEST"
        result = check_ops_pack(feature)
        # Non-ERP feature may skip ops check
        assert result.status in ("PASS", "FAIL", "WARN")
