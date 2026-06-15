"""Test: state.yaml Phase 2-4 + Final schema 検証 — Phase F (FEAT-VALF01).

Covers AC-US-FEATVALF01-010-01 (state.yaml Phase 2/3/4/Final ステータス schema)。

Phase E v0.1.0-poc では state.yaml は feature/current_gate/autonomy_bias/profile/work_items/run_index のみ。
Phase F WI-VALF01-010 (改善要望-09) で phase_2/phase_3/phase_4/final を追加し、
VALUE pack handoff 後の SDD Phase 2-4 進捗を機械追跡可能にする。

baseline 789 → 792+ passed を担保 (3 件分)。
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
VAL_F01_STATE = REPO_ROOT / "specs" / "val_f01" / "state" / "state.yaml"


@pytest.fixture(scope="module")
def state_yaml() -> dict:
    """Load val_f01/state/state.yaml as the canonical example of Phase F-extended schema."""
    assert VAL_F01_STATE.is_file(), f"state.yaml が見つからない: {VAL_F01_STATE}"
    return yaml.safe_load(VAL_F01_STATE.read_text(encoding="utf-8"))


# =====================================================================
# TS-CON-10 / TS-INT-02 (#1): Phase 2 schema
# =====================================================================


def test_state_yaml_has_phase_2_schema(state_yaml):
    """state.yaml に phase_2 セクションが存在し、必須キー (status / spec_md_done /
    plan_md_done / contracts_done / approved_at) を含む.

    AC-US-FEATVALF01-010-01 の機械検証 (Phase 2 部分).
    """
    assert "phase_2" in state_yaml, "state.yaml に phase_2 セクションが存在しない"
    p2 = state_yaml["phase_2"]
    assert isinstance(p2, dict), "phase_2 は dict であるべき"

    required_keys = ["status", "spec_md_done", "plan_md_done", "contracts_done", "approved_at"]
    missing = [k for k in required_keys if k not in p2]
    assert not missing, f"phase_2 に必須キーが不足: {missing}"

    # status の値域
    valid_status = ("not_started", "in_progress", "completed")
    assert p2["status"] in valid_status, (
        f"phase_2.status は {valid_status} のいずれか、実際: {p2['status']}"
    )
    # bool fields
    for bf in ("spec_md_done", "plan_md_done", "contracts_done"):
        assert isinstance(p2[bf], bool), f"phase_2.{bf} は bool、実際: {type(p2[bf]).__name__}"


# =====================================================================
# TS-CON-10 / TS-INT-02 (#2): Phase 3 schema
# =====================================================================


def test_state_yaml_has_phase_3_schema(state_yaml):
    """state.yaml に phase_3 セクションが存在し、必須キー (status / tasks_md_done /
    work_items_count / approved_at) を含む.

    AC-US-FEATVALF01-010-01 の機械検証 (Phase 3 部分).
    """
    assert "phase_3" in state_yaml, "state.yaml に phase_3 セクションが存在しない"
    p3 = state_yaml["phase_3"]
    assert isinstance(p3, dict), "phase_3 は dict であるべき"

    required_keys = ["status", "tasks_md_done", "work_items_count", "approved_at"]
    missing = [k for k in required_keys if k not in p3]
    assert not missing, f"phase_3 に必須キーが不足: {missing}"

    valid_status = ("not_started", "in_progress", "completed")
    assert p3["status"] in valid_status, (
        f"phase_3.status は {valid_status} のいずれか、実際: {p3['status']}"
    )
    assert isinstance(p3["tasks_md_done"], bool)
    assert isinstance(p3["work_items_count"], int) and p3["work_items_count"] >= 0


# =====================================================================
# TS-CON-10 / TS-INT-02 (#3): Phase 4 + Final schema
# =====================================================================


def test_state_yaml_has_phase_4_and_final_schema(state_yaml):
    """state.yaml に phase_4 + final セクションが存在し、必須キーを含む.

    phase_4: status / wi_total / wi_completed / wi_in_progress / approved_at
    final: status / evidence_pack_done / pr_url / merged_at

    AC-US-FEATVALF01-010-01 の機械検証 (Phase 4 + Final 部分).
    """
    # phase_4
    assert "phase_4" in state_yaml, "state.yaml に phase_4 セクションが存在しない"
    p4 = state_yaml["phase_4"]
    assert isinstance(p4, dict)
    p4_required = ["status", "wi_total", "wi_completed", "wi_in_progress", "approved_at"]
    p4_missing = [k for k in p4_required if k not in p4]
    assert not p4_missing, f"phase_4 に必須キーが不足: {p4_missing}"
    valid_status = ("not_started", "in_progress", "completed")
    assert p4["status"] in valid_status
    assert isinstance(p4["wi_total"], int) and p4["wi_total"] >= 0
    assert isinstance(p4["wi_completed"], int) and 0 <= p4["wi_completed"] <= p4["wi_total"]
    assert isinstance(p4["wi_in_progress"], int) and p4["wi_in_progress"] >= 0

    # final
    assert "final" in state_yaml, "state.yaml に final セクションが存在しない"
    fn = state_yaml["final"]
    assert isinstance(fn, dict)
    fn_required = ["status", "evidence_pack_done", "pr_url", "merged_at"]
    fn_missing = [k for k in fn_required if k not in fn]
    assert not fn_missing, f"final に必須キーが不足: {fn_missing}"
    assert fn["status"] in valid_status
    assert isinstance(fn["evidence_pack_done"], bool)
