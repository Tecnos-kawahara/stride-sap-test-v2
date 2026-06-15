"""E2E tests for v4.6 Execution Authority + v5.1 Janitor integration.

Verifies end-to-end that wi_readiness_checker Check 8 honors the
conversational / gated / prohibited declaration, that Symphony Janitor
scope limits are enforced, and that a janitor-materialized WI clears
Check 8. All fixtures use tmp_path — never touches real specs/.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path
from unittest import mock

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "sdd-templates" / "tools"))
sys.path.insert(0, str(_REPO_ROOT))

from wi_readiness_checker import run_readiness_checks  # noqa: E402
from symphony.cli import _run_janitor_scan  # noqa: E402
from symphony.config import JanitorConfig, SymphonyConfig, TrackerConfig  # noqa: E402
from symphony.models import Issue  # noqa: E402


# ---------------------------------------------------------------------------
# Mode policy variants
# ---------------------------------------------------------------------------

_POLICY_BASE = textwrap.dedent("""\
    modes:
      autopilot: {checkpoints: {pre_run: [], post_run: []}}
      confirm: {checkpoints: {pre_run: [plan_review], post_run: []}}
      validate: {checkpoints: {pre_run: [design_diff_review, plan_review], post_run: []}}
    risk_flag_mapping:
      validate: [authz, sod, audit_log, pii, accounting_calc, inventory_valuation,
                 db_schema, data_migration, update_integration, cross_module]
      confirm: [new_api, contract_change, performance_sensitive]
      autopilot: [ui_only, message_only, test_only, logging_only]
    tier_mode_minimum: {critical: confirm, standard: autopilot, experimental: autopilot}
    overrides: {require_reason_when_override: true}
""")

POLICY_CONSERVATIVE = _POLICY_BASE + textwrap.dedent("""\
    execution_authority:
      conversational:
        actions: [interpret spec, propose action, auto-fix lint]
      gated:
        gate_mechanism: stride-lint + phase_gate.py
        actions: [create artifact, start WI, create PR]
      prohibited:
        actions: [edit APPROVAL.md, skip gate, override autonomy_bias, change coverage_tier]
""")

POLICY_LEGACY = _POLICY_BASE  # no execution_authority section


# ---------------------------------------------------------------------------
# Feature builder (minimal Gate-5-approved project)
# ---------------------------------------------------------------------------

_APPROVAL_MD = textwrap.dedent("""\
    # Feature Approval Record

    ## Gate 5: Tasking Review

    ### Checklist
    - [x] tasks.md complete
    - [x] all tasks have plan_refs

    承認者: Test User
    日付: 2026-04-17

    ---
""")


def _wi_frontmatter(wi_id, mode, risk_flags, override_reason="", extra_fields=None):
    """Render a WI front-matter block."""
    import yaml

    fm = {
        "wi_id": wi_id, "title": f"Test WI {wi_id}", "complexity": "medium",
        "mode": mode, "risk_flags": risk_flags, "spec_refs": ["spec.md"],
    }
    if override_reason:
        fm["mode_override"] = {"reason": override_reason}
    if extra_fields:
        fm.update(extra_fields)
    body = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True)
    return f"---\n{body}---\n# Intent\n"


def build_feature(
    tmp_path: Path,
    *,
    feature_id: str = "FEAT-TEST-EA",
    wi_id: str = "WI-TEST-EA-001",
    mode: str = "autopilot",
    risk_flags: list[str] | None = None,
    coverage_tier: str = "standard",
    autonomy_bias: str = "balanced",
    override_reason: str = "",
    extra_wi_fields: dict | None = None,
    policy_text: str = POLICY_CONSERVATIVE,
    pre_run_checkpoints_approved: list[str] | None = None,
) -> tuple[Path, str]:
    """Build an isolated feature dir with Gate-5 approved + WI + state + policy.

    Returns (feature_dir, wi_id). All parts live under tmp_path.
    """
    risk_flags = list(risk_flags) if risk_flags is not None else ["ui_only"]
    project_root = tmp_path
    (project_root / "memory").mkdir(parents=True, exist_ok=True)

    policy_dir = project_root / "shared" / "policies"
    policy_dir.mkdir(parents=True, exist_ok=True)
    (policy_dir / "mode_policy.yaml").write_text(policy_text, encoding="utf-8")

    feature_dir = project_root / "specs" / feature_id
    (feature_dir / "work_items").mkdir(parents=True, exist_ok=True)
    (feature_dir / "state").mkdir(parents=True, exist_ok=True)

    (feature_dir / "APPROVAL.md").write_text(_APPROVAL_MD, encoding="utf-8")
    (feature_dir / "basic_design.md").write_text(
        f'---\nartifact: basic_design\n---\n# Canonical\n```yaml\n'
        f'basic_design:\n  coverage_tier: "{coverage_tier}"\n```\n',
        encoding="utf-8",
    )

    wi_file = feature_dir / "work_items" / f"{wi_id}.md"
    wi_file.write_text(
        _wi_frontmatter(wi_id, mode, risk_flags, override_reason, extra_wi_fields),
        encoding="utf-8",
    )

    if pre_run_checkpoints_approved:
        lines = "\n".join(f"- [x] {cp}: approved" for cp in pre_run_checkpoints_approved)
        (feature_dir / "work_items" / f"{wi_id}.approval.md").write_text(
            f"# WI Approval\n\n## Pre-Run Approval\n{lines}\n",
            encoding="utf-8",
        )

    (feature_dir / "state" / "state.yaml").write_text(
        f"autonomy_bias: {autonomy_bias}\nwork_items:\n  - wi_id: {wi_id}\n    status: pending\n",
        encoding="utf-8",
    )
    return feature_dir, wi_id


def _get_auth_result(results):
    """Find the execution_authority CheckResult in a readiness results list."""
    for r in results:
        if "authority" in r.message.lower():
            return r
    pytest.fail(f"execution_authority result not found in {[r.message for r in results]}")


# ---------------------------------------------------------------------------
# Phase C: Normal path tests (EA-1 .. EA-4)
# ---------------------------------------------------------------------------

class TestExecutionAuthorityNormalPath:
    def test_ea1_autopilot_conversational_only(self, tmp_path):
        """EA-1: autopilot WI + conversational action (ui_only) → Check 8 PASS."""
        feat, wi = build_feature(tmp_path, risk_flags=["ui_only"], mode="autopilot")
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "PASS", r.message
        assert "aligned" in r.message.lower()

    def test_ea2_confirm_new_api_with_plan_review(self, tmp_path):
        """EA-2: confirm WI + new_api (gated) + plan_review approved → Check 8 PASS."""
        feat, wi = build_feature(
            tmp_path,
            mode="confirm",
            risk_flags=["new_api"],
            pre_run_checkpoints_approved=["plan_review"],
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "PASS", r.message

    def test_ea3_validate_both_reviews_approved(self, tmp_path):
        """EA-3: validate WI + authz/pii + design_diff_review + plan_review → Check 8 PASS."""
        feat, wi = build_feature(
            tmp_path,
            mode="validate",
            risk_flags=["authz", "pii"],
            pre_run_checkpoints_approved=["design_diff_review", "plan_review"],
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "PASS", r.message

    def test_ea4_legacy_policy_no_execution_authority(self, tmp_path):
        """EA-4: policy without execution_authority (legacy) → PASS with legacy message."""
        feat, wi = build_feature(
            tmp_path,
            mode="autopilot",
            risk_flags=["ui_only"],
            policy_text=POLICY_LEGACY,
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "PASS"
        assert "legacy" in r.message.lower()


# ---------------------------------------------------------------------------
# Phase D: Failure path tests (EA-F1 .. EA-F5)
# ---------------------------------------------------------------------------

class TestExecutionAuthorityFailurePath:
    def test_eaf1_autopilot_pii_no_override(self, tmp_path):
        """EA-F1: autopilot + pii (validate-level) w/o override → Check 8 FAIL."""
        feat, wi = build_feature(tmp_path, mode="autopilot", risk_flags=["pii"])
        results, code = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "FAIL", r.message
        assert "violation" in r.message.lower()
        assert code == 1

    def test_eaf2_autopilot_pii_with_override_reason(self, tmp_path):
        """EA-F2: autopilot + pii + mode_override.reason → WARN (not FAIL)."""
        feat, wi = build_feature(
            tmp_path,
            mode="autopilot",
            risk_flags=["pii"],
            override_reason="Temporary test exception approved by TECH_LEAD",
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "WARN", r.message
        assert "override" in r.message.lower()

    def test_eaf3_critical_tier_autopilot_enforced(self, tmp_path):
        """EA-F3: critical tier + autopilot + new_api → FAIL.

        Task spec references AUTOPILOT_FORBIDDEN_BY_TIER but that code does
        not exist; the equivalent is a generic violation when mode < scope.
        Using new_api bypasses the balanced-bias tier_min gap (see report).
        """
        feat, wi = build_feature(
            tmp_path,
            mode="autopilot",
            risk_flags=["new_api"],
            coverage_tier="critical",
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "FAIL", r.message
        assert "confirm" in r.message

    def test_eaf4_prohibited_action_in_wi_actions_gap(self, tmp_path):
        """EA-F4: WI declaring prohibited actions (gap test).

        Expected future: WI_EXECUTION_AUTHORITY_VIOLATION. Current: Check 8
        only compares mode vs scope and does NOT inspect WI.actions against
        the prohibited list. Test asserts the gap so a future patch can flip.
        """
        feat, wi = build_feature(
            tmp_path,
            mode="autopilot",
            risk_flags=["ui_only"],
            extra_wi_fields={"actions": ["edit APPROVAL.md", "skip gate"]},
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        # Gap: declared prohibited actions are silently ignored.
        # If this flips to FAIL in a future impl, update to xfail(strict=True).
        assert r.status == "PASS", (
            "GAP DETECTED: Check 8 did NOT flag a WI declaring prohibited "
            f"actions. Actual: {r.status} / {r.message}"
        )

    def test_eaf5_gated_action_missing_validator_gap(self, tmp_path):
        """EA-F5: gated action without validator (gap test).

        Expected future: Check 8 FAIL with gap enumeration. Current: Check 8
        trusts gate_mechanism string and does not cross-check that each gated
        action maps to an available validator tool.
        """
        policy_with_unreferenced_gated = POLICY_CONSERVATIVE.replace(
            "- create artifact",
            "- perform_undocumented_gated_action_xyz",
        )
        feat, wi = build_feature(
            tmp_path,
            mode="autopilot",
            risk_flags=["ui_only"],
            policy_text=policy_with_unreferenced_gated,
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        # Gap: declaration-to-validator mapping is not validated.
        assert r.status == "PASS", (
            "GAP DETECTED: Check 8 did NOT flag an unmapped gated action. "
            f"Actual: {r.status} / {r.message}"
        )


# ---------------------------------------------------------------------------
# Phase E: Janitor integration tests (JN-1 .. JN-5)
# ---------------------------------------------------------------------------

def _mk_issue(
    number: int,
    feature_name: str,
    labels: list[str],
    *,
    title: str | None = None,
) -> Issue:
    return Issue(
        number=number,
        title=title or f"[WI] {feature_name} cleanup",
        body="",
        url=f"https://example.invalid/{number}",
        priority="P2",
        phase="Execute",
        feature_name=feature_name,
        labels=labels,
    )


def _mk_symphony_config(*, enabled: bool = True) -> SymphonyConfig:
    cfg = SymphonyConfig(
        tracker=TrackerConfig(repo="owner/repo"),
        janitor=JanitorConfig(
            enabled=enabled,
            interval_hours=6,
            exclude_recent_pr_days=7,
            risk_flags_exclude=["risk:authz", "risk:pii", "risk:external_api", "risk:sod"],
        ),
    )
    return cfg


class TestJanitorIntegration:
    def test_jn1_autopilot_starter_no_risk_no_recent_pr_creates_issue(self):
        """JN-1: eligible autopilot + starter feature → Issue is created."""
        cfg = _mk_symphony_config(enabled=True)
        issues = [_mk_issue(101, "feat_autopilot_ok", ["mode:autopilot", "tier:starter"])]
        with mock.patch("symphony.cli.has_recent_pr", return_value=False), \
             mock.patch("symphony.cli.has_open_janitor_issue", return_value=False), \
             mock.patch("symphony.cli.create_janitor_issue", return_value=999) as mk:
            _run_janitor_scan(cfg, issues)
        mk.assert_called_once()
        args, _ = mk.call_args
        assert args[0] == "owner/repo"
        assert args[1] == "feat_autopilot_ok"

    def test_jn2_risk_flag_excluded(self):
        """JN-2: feature carrying risk:authz is skipped by exclude filter."""
        cfg = _mk_symphony_config(enabled=True)
        issues = [
            _mk_issue(102, "feat_authz", ["mode:autopilot", "tier:starter", "risk:authz"]),
        ]
        with mock.patch("symphony.cli.has_recent_pr", return_value=False), \
             mock.patch("symphony.cli.has_open_janitor_issue", return_value=False), \
             mock.patch("symphony.cli.create_janitor_issue", return_value=1) as mk:
            _run_janitor_scan(cfg, issues)
        mk.assert_not_called()

    def test_jn3_recent_pr_skipped(self):
        """JN-3: a recently merged PR (< exclude_recent_pr_days) suppresses the proposal."""
        cfg = _mk_symphony_config(enabled=True)
        issues = [_mk_issue(103, "feat_recent_pr", ["mode:autopilot", "tier:starter"])]
        with mock.patch("symphony.cli.has_recent_pr", return_value=True), \
             mock.patch("symphony.cli.has_open_janitor_issue", return_value=False), \
             mock.patch("symphony.cli.create_janitor_issue", return_value=1) as mk:
            _run_janitor_scan(cfg, issues)
        mk.assert_not_called()

    def test_jn4_janitor_materialized_wi_passes_check8(self, tmp_path):
        """JN-4: a WI within Janitor scope (autopilot+low-risk) passes Check 8."""
        feat, wi = build_feature(
            tmp_path,
            feature_id="FEAT-JN-MAT",
            wi_id="WI-JN-MAT-001",
            mode="autopilot",
            risk_flags=["logging_only"],
            coverage_tier="standard",
        )
        results, _ = run_readiness_checks(str(feat), wi)
        r = _get_auth_result(results)
        assert r.status == "PASS", r.message
        assert "violation" not in r.message.lower()

    def test_jn5_tier_standard_skipped(self):
        """JN-5: tier:standard feature (not starter) is excluded from janitor scope."""
        cfg = _mk_symphony_config(enabled=True)
        issues = [_mk_issue(105, "feat_standard", ["mode:autopilot", "tier:standard"])]
        with mock.patch("symphony.cli.has_recent_pr", return_value=False), \
             mock.patch("symphony.cli.has_open_janitor_issue", return_value=False), \
             mock.patch("symphony.cli.create_janitor_issue", return_value=1) as mk:
            _run_janitor_scan(cfg, issues)
        mk.assert_not_called()
