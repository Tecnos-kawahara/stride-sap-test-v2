"""Test: stride_lint upstream extension (lint_upstream) — Phase B WI-004 (TS-INT-04).

Verifies the 4 new error codes fire correctly.
Also covers AC-09 sanity (sdd-templates/VERSION + protected hash references).

Covers AC-US-FEATVALB01-001-03 (4 lint codes) and AC-US-FEATVALB01-001-09 (VERSION/hash sanity).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from upstream_lint import (
    lint_upstream,
    BACCM_INCOMPLETE,
    BROKEN_LAYER_LINK,
    UPSTREAM_TEMPLATE_DRIFT,
    BABOK_TECHNIQUE_UNKNOWN,
    SUGGESTED_ACTIONS,
    _ErrorAccumulator,
)


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


@pytest.fixture
def lint_feature(tmp_path: Path) -> Path:
    """Build a tmp feature with policies and an empty upstream/."""
    feature_dir = tmp_path / "specs" / "feat_lint"
    (feature_dir / "upstream").mkdir(parents=True)

    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "policies").mkdir()
    for f in ("baccm_completeness.yaml", "technique_library.yaml"):
        (tmp_path / "shared" / "policies" / f).symlink_to(
            REPO_ROOT / "shared" / "policies" / f
        )
    (tmp_path / "sdd-templates").mkdir()
    (tmp_path / "sdd-templates" / "templates").mkdir()
    (tmp_path / "sdd-templates" / "templates" / "upstream").symlink_to(
        REPO_ROOT / "sdd-templates" / "templates" / "upstream"
    )
    return tmp_path


def test_no_upstream_dir_skips_silently(tmp_path: Path):
    """upstream/ が存在しなければ何もエラーを出さない (Phase A 互換性)"""
    feature_dir = tmp_path / "specs" / "feat_no_upstream"
    feature_dir.mkdir(parents=True)
    result = lint_upstream(feature_dir, repo_root=tmp_path)
    assert len(result.errors) == 0


def test_baccm_incomplete_fires(lint_feature: Path):
    """BACCM 6 軸の必須キーが空 → BACCM_INCOMPLETE 発火"""
    feature_dir = lint_feature / "specs" / "feat_lint"
    discovery = feature_dir / "upstream" / "phase_0_discovery"
    # 完全に空の YAML → 6 軸全てで missing_keys
    for name in ("business_need.yaml", "value_canvas.yaml", "stakeholder_map.yaml",
                 "context_map.yaml", "change_strategy.yaml", "goal_tree.yaml"):
        _write_yaml(discovery / name, {})
    result = lint_upstream(feature_dir, repo_root=lint_feature)
    codes = {e["code"] for e in result.errors}
    assert BACCM_INCOMPLETE in codes


def test_broken_layer_link_fires(lint_feature: Path):
    """requirements_architecture.yaml の cross_layer_links が壊れていれば BROKEN_LAYER_LINK"""
    feature_dir = lint_feature / "specs" / "feat_lint"
    rar_path = feature_dir / "upstream" / "phase_0_5_context_modelling" / "requirements_architecture.yaml"
    _write_yaml(rar_path, {
        "layers": [
            {"id": "LAYER-SYS", "items": ["ACT-001"]},
            {"id": "LAYER-COND", "items": []},
        ],
        "cross_layer_links": [
            {"from_layer": "LAYER-SYS", "from_id": "ACT-999", "to_layer": "LAYER-COND", "to_id": "CND-001"},
        ],
    })
    result = lint_upstream(feature_dir, repo_root=lint_feature)
    codes = {e["code"] for e in result.errors}
    assert BROKEN_LAYER_LINK in codes


def test_template_drift_fires(lint_feature: Path):
    """artifact の template_id が pattern 違反 → UPSTREAM_TEMPLATE_DRIFT"""
    feature_dir = lint_feature / "specs" / "feat_lint"
    art_path = feature_dir / "upstream" / "phase_0_discovery" / "business_need.yaml"
    _write_yaml(art_path, {
        "template_id": "INVALID-FORMAT",  # ^TPL-UP-[A-Z]{3,4}-[0-9]{3}$ に違反
        "problem_statement": "x",
    })
    result = lint_upstream(feature_dir, repo_root=lint_feature)
    codes = {e["code"] for e in result.errors}
    assert UPSTREAM_TEMPLATE_DRIFT in codes


def test_technique_unknown_fires(lint_feature: Path):
    """elicitation_plan.yaml で未知の technique_id → BABOK_TECHNIQUE_UNKNOWN"""
    feature_dir = lint_feature / "specs" / "feat_lint"
    plan_path = feature_dir / "upstream" / "phase_0_3_elicit" / "elicitation_plan.yaml"
    _write_yaml(plan_path, {
        "techniques": ["unknown_made_up_technique", "brainstorming"],
        "target_stakeholders": [],
    })
    result = lint_upstream(feature_dir, repo_root=lint_feature)
    codes = {e["code"] for e in result.errors}
    assert BABOK_TECHNIQUE_UNKNOWN in codes
    assert any(
        "unknown_made_up_technique" in e["message"]
        for e in result.errors if e["code"] == BABOK_TECHNIQUE_UNKNOWN
    )


def test_suggested_actions_present():
    """4 エラーコードすべてに SUGGESTED_ACTIONS エントリがある"""
    for code in (BACCM_INCOMPLETE, BROKEN_LAYER_LINK, UPSTREAM_TEMPLATE_DRIFT, BABOK_TECHNIQUE_UNKNOWN):
        assert code in SUGGESTED_ACTIONS
        assert len(SUGGESTED_ACTIONS[code]) > 0


def test_stride_lint_constants_synced():
    """stride_lint.py 側の SUGGESTED_ACTIONS にも 4 コードが追加されている"""
    stride_lint_path = REPO_ROOT / "sdd-templates" / "tools" / "stride_lint.py"
    text = stride_lint_path.read_text(encoding="utf-8")
    for code in (BACCM_INCOMPLETE, BROKEN_LAYER_LINK, UPSTREAM_TEMPLATE_DRIFT, BABOK_TECHNIQUE_UNKNOWN):
        assert f'"{code}"' in text or f'\'{code}\'' in text


def test_constitution_main_phase_c_state():
    """memory/constitution.md は Phase C 完了状態 (version 6.0.0, articles[]+3 = 17, last_reviewed_at 2026-04-29).

    History:
      - Phase A (FEAT-VALA01): 本体不変、amendments proposed only
      - Phase B (FEAT-VALB01): 本体不変、CLI scaffold のみ
      - Phase C (FEAT-VALC01, 2026-04-29): articles[] に Article XV-XVII 追加 + version
        bump + last_reviewed_at 更新 + amendment_history +3 + amendments status ratified

    Phase B 旧テスト (test_constitution_main_unchanged_via_subprocess) は Phase C 完了で
    論理矛盾するため、Phase C 状態を検証する形に改修済み (Hitoshi さん明示承認 §Rule 1-A
    例外、Phase A 不変条件と同じ論理で Phase C 完了 = 不変条件解除)。
    """
    text = (REPO_ROOT / "memory" / "constitution.md").read_text(encoding="utf-8")
    assert 'version: "6.0.0-tecnos-stride-value"' in text, (
        "constitution.md トップレベル version が Phase C 値 6.0.0-tecnos-stride-value でない"
    )
    for art_id in ("XV", "XVI", "XVII"):
        assert f'id: "{art_id}"' in text, (
            f"constitution.md articles[] に id: \"{art_id}\" が追加されていない"
        )
