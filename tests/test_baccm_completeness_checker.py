"""Test: baccm_completeness_checker.check_baccm_completeness() — Phase B WI-002 (TS-INT-02).

Verifies BACCM 6-axis judgment logic with full / partial / missing scenarios.

Covers AC-US-FEATVALB01-001-01 (one of the 5 Python tools is structurally sound).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from baccm_completeness_checker import check_baccm_completeness, EXPECTED_AXES


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def baccm_feature(tmp_path: Path) -> Path:
    """Build a tmp feature with all 6 BACCM-supporting artifacts populated."""
    feature_dir = tmp_path / "specs" / "feat_baccm"
    discovery_dir = feature_dir / "upstream" / "phase_0_discovery"
    discovery_dir.mkdir(parents=True)

    _write_yaml(discovery_dir / "business_need.yaml", {
        "problem_statement": "業務課題X", "opportunity_statement": "機会Y",
    })
    _write_yaml(discovery_dir / "value_canvas.yaml", {
        "from_state": "現状", "to_state": "目標",
        "potential_value": ["v1"], "anti_value": ["a1"],
    })
    _write_yaml(discovery_dir / "stakeholder_map.yaml", {
        "stakeholders": [
            {"id": "SH-001", "name": "営業部"},
            {"id": "SH-002", "name": "IT部"},
            {"id": "SH-003", "name": "監査部"},
        ],
    })
    _write_yaml(discovery_dir / "context_map.yaml", {
        "internal_context": ["i1"], "external_context": ["e1"],
    })
    _write_yaml(discovery_dir / "change_strategy.yaml", {
        "transition_states": ["s1"], "solution_scope": "scope1",
    })
    _write_yaml(discovery_dir / "goal_tree.yaml", {"root_goal": "RG"})

    # Mirror policy + templates
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "policies").mkdir()
    (tmp_path / "shared" / "policies" / "baccm_completeness.yaml").symlink_to(
        REPO_ROOT / "shared" / "policies" / "baccm_completeness.yaml"
    )
    return tmp_path


def test_all_six_axes_pass(baccm_feature: Path):
    """全 6 軸 PASS → overall_pass=True, score=100"""
    result = check_baccm_completeness(baccm_feature / "specs" / "feat_baccm", repo_root=baccm_feature)
    assert result["overall_pass"] is True
    assert result["score"] == 100
    assert set(result["axes"].keys()) == EXPECTED_AXES


def test_partial_axes_fail_overall(baccm_feature: Path):
    """1 軸欠落 → overall_pass=False"""
    feature_dir = baccm_feature / "specs" / "feat_baccm"
    # context 軸の internal_context を空にする
    ctx_path = feature_dir / "upstream" / "phase_0_discovery" / "context_map.yaml"
    _write_yaml(ctx_path, {"internal_context": [], "external_context": []})
    result = check_baccm_completeness(feature_dir, repo_root=baccm_feature)
    assert result["overall_pass"] is False
    assert result["axes"]["context"]["pass"] is False


def test_required_keys_missing_listed(baccm_feature: Path):
    feature_dir = baccm_feature / "specs" / "feat_baccm"
    bn_path = feature_dir / "upstream" / "phase_0_discovery" / "business_need.yaml"
    _write_yaml(bn_path, {"problem_statement": ""})
    result = check_baccm_completeness(feature_dir, repo_root=baccm_feature)
    assert result["axes"]["need"]["pass"] is False
    assert any("problem_statement" in m for m in result["axes"]["need"]["missing_keys"])
    assert any("opportunity_statement" in m for m in result["axes"]["need"]["missing_keys"])


def test_required_min_count_unsatisfied(baccm_feature: Path):
    """stakeholders < 3 → stakeholder 軸 FAIL"""
    feature_dir = baccm_feature / "specs" / "feat_baccm"
    sm_path = feature_dir / "upstream" / "phase_0_discovery" / "stakeholder_map.yaml"
    _write_yaml(sm_path, {"stakeholders": [{"id": "SH-1"}]})
    result = check_baccm_completeness(feature_dir, repo_root=baccm_feature)
    assert result["axes"]["stakeholder"]["pass"] is False
    assert result["axes"]["stakeholder"]["missing_min_counts"]


def test_missing_artifact_fails_axis(baccm_feature: Path):
    """artifact ファイル自体が存在しない場合も適切に検出"""
    feature_dir = baccm_feature / "specs" / "feat_baccm"
    (feature_dir / "upstream" / "phase_0_discovery" / "business_need.yaml").unlink()
    result = check_baccm_completeness(feature_dir, repo_root=baccm_feature)
    assert result["axes"]["need"]["pass"] is False


def test_score_calculation_partial(baccm_feature: Path):
    """N/6 軸 PASS のとき score = floor(N/6 * 100)"""
    feature_dir = baccm_feature / "specs" / "feat_baccm"
    # 1 軸 (need) を欠陥にする → 5/6 軸 PASS → score = 83
    bn_path = feature_dir / "upstream" / "phase_0_discovery" / "business_need.yaml"
    _write_yaml(bn_path, {})
    result = check_baccm_completeness(feature_dir, repo_root=baccm_feature)
    assert result["score"] == 83  # floor(5/6 * 100)


def test_policy_version_present(baccm_feature: Path):
    result = check_baccm_completeness(baccm_feature / "specs" / "feat_baccm", repo_root=baccm_feature)
    assert "policy_version" in result
    assert isinstance(result["policy_version"], str)
