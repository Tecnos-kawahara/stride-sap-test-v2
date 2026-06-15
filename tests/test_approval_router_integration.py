"""Integration tests for approval_router.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from approval_router import ApprovalRouter, FeatureContext


@pytest.fixture
def router(tmp_path) -> ApprovalRouter:
    (tmp_path / "memory").mkdir(exist_ok=True)
    return ApprovalRouter(tmp_path)


def _ctx(tier: str = "standard", team: str = "TEAM-A", cross_team: bool = False,
         shared_contract: bool = False, security: bool = False, erp: bool = False) -> FeatureContext:
    return FeatureContext(
        feature_id="FEAT-TEST",
        team_id=team,
        coverage_tier=tier,
        epic_id="EPIC-TEST",
        has_cross_team_deps=cross_team,
        has_shared_contract_changes=shared_contract,
        security_sensitive=security,
        erp_integration=erp,
    )


class TestRouteApproval:
    def test_standard_design_gate(self, router):
        approvers = router.get_required_approvers(_ctx(tier="standard"), "basic_design")
        assert isinstance(approvers, list)
        assert len(approvers) > 0

    def test_critical_tier_escalates(self, router):
        std = router.get_required_approvers(_ctx(tier="standard"), "spec")
        crit = router.get_required_approvers(_ctx(tier="critical"), "spec")
        # critical tier triggers ARCH_BOARD escalation
        assert len(crit) >= len(std)
        assert "ARCH_BOARD" in crit

    def test_cross_team_escalates(self, router):
        base = router.get_required_approvers(_ctx(), "spec")
        cross = router.get_required_approvers(_ctx(cross_team=True), "spec")
        assert "ARCH_BOARD" in cross


class TestValidateApprover:
    def test_pm_can_approve_spec(self, router):
        valid, reason = router.validate_approver(_ctx(), "spec", "PM")
        assert valid is True

    def test_unknown_role_fails(self, router):
        valid, reason = router.validate_approver(_ctx(), "final", "JANITOR")
        assert valid is False
        assert "Unknown" in reason or "not" in reason.lower()


class TestParallelEligibility:
    def test_basic_design_can_parallel_with_bpmn(self, router):
        can, gates = router.check_parallel_eligibility(_ctx(), "basic_design")
        assert can is True
        assert "bpmn" in gates

    def test_security_critical_blocks_parallel(self, router):
        can, gates = router.check_parallel_eligibility(
            _ctx(tier="critical", security=True), "spec"
        )
        # Security sensitive + critical → no parallel
        # (parallel spec requires standard/experimental)
        assert can is False or "plan" not in gates


class TestEnterpriseContext:
    def test_erp_integration_escalates(self, router):
        approvers = router.get_required_approvers(_ctx(erp=True), "spec")
        assert "ARCH_BOARD" in approvers
