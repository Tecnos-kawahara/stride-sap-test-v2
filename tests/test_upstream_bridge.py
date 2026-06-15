"""Test: upstream_bridge.bridge_to_phase1() — Phase C WI-VALC01-001 (TS-INT-01).

Covers AC-US-FEATVALC01-001-01 (Phase 0/0.3/0.5 → Phase 1 自動 populate +
Gate 1/2 immutability check + dry-run/apply の双方向 + 既存 skip + Markdown 出力).
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from upstream_bridge import (
    bridge_to_phase1,
    is_gate_approved,
    LINKS_TO_POPULATE,
    VALID_TARGETS,
)


def _write_basic_design_with_links(path: Path, feature_name: str = "tmp_feat"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(f"""\
            ---
            artifact: "basic_design"
            feature_id: "FEAT-{feature_name.upper().replace('_', '')}"
            title: "Test Basic Design"
            links:
              process_bpmn_ref: "specs/{feature_name}/process.bpmn"
              spec_md_ref: "specs/{feature_name}/spec.md"
            ---

            # 0. Canonical Basic Design (YAML)
            placeholder body
            """),
        encoding="utf-8",
    )


def _write_approval_unapproved(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent("""\
            # 承認記録

            ## Gate 1: Basic Design

            確認項目：

            - [ ] basic_design.md の WHO/WHAT/WHY が正しい

            ```
            承認者: _____________________
            日付:   _____________________
            ```

            ---

            ## Gate 2: BPMN

            確認項目：

            - [ ] process.bpmn の業務フローが正しい

            ```
            承認者: _____________________
            日付:   _____________________
            ```
            """),
        encoding="utf-8",
    )


def _write_approval_approved(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent("""\
            # 承認記録

            ## Gate 1: Basic Design

            確認項目：

            - [x] basic_design.md の WHO/WHAT/WHY が正しい

            ```
            承認者: Hitoshi Okazaki
            日付:   2026-04-29
            ```

            ---

            ## Gate 2: BPMN

            確認項目：

            - [x] process.bpmn の業務フローが正しい

            ```
            承認者: Hitoshi Okazaki
            日付:   2026-04-29
            ```
            """),
        encoding="utf-8",
    )


def _write_business_usecase(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent("""\
            artifact: "business_usecase"
            feature_id: "FEAT-TMPFEAT"
            use_cases:
              - id: BUC-001
                name: "Submit purchase request"
              - id: BUC-002
                name: "Approve purchase order"
            """),
        encoding="utf-8",
    )


@pytest.fixture
def feature_dir(tmp_path: Path) -> Path:
    """最小限の feature directory を作成."""
    fd = tmp_path / "specs" / "tmp_feat"
    fd.mkdir(parents=True)
    (fd / "upstream" / "phase_0_discovery").mkdir(parents=True)
    (fd / "upstream" / "phase_0_5_context_modelling").mkdir(parents=True)
    _write_basic_design_with_links(fd / "basic_design.md")
    _write_approval_unapproved(fd / "APPROVAL.md")
    _write_business_usecase(
        fd / "upstream" / "phase_0_5_context_modelling" / "business_usecase.yaml"
    )
    # 最小限のその他成果物 (warnings を抑制)
    for fname in ("business_need.yaml", "value_canvas.yaml", "stakeholder_map.yaml"):
        (fd / "upstream" / "phase_0_discovery" / fname).write_text(
            f"artifact: {fname.replace('.yaml', '')}\n", encoding="utf-8"
        )
    return fd


def test_dry_run_returns_task_candidates_markdown(feature_dir: Path):
    """dry-run (--apply なし) で task candidates Markdown が生成され、basic_design は不変."""
    bd_before = (feature_dir / "basic_design.md").read_text(encoding="utf-8")
    result = bridge_to_phase1(feature_dir, target_section="phase1", apply=False)
    bd_after = (feature_dir / "basic_design.md").read_text(encoding="utf-8")
    assert bd_before == bd_after, "dry-run で basic_design.md が変更されてはいけない"
    assert "BPMN-TASK-001" in result["task_candidates_markdown"]
    assert "BPMN-TASK-002" in result["task_candidates_markdown"]
    assert len(result["task_candidates"]) == 2
    assert result["feature_id"] == "FEAT-TMPFEAT"


def test_apply_populates_basic_design_links(feature_dir: Path):
    """--apply で basic_design.md links に upstream_* が追加される (Gate 1/2 未承認時)."""
    result = bridge_to_phase1(feature_dir, target_section="phase1", apply=True)
    bd = (feature_dir / "basic_design.md").read_text(encoding="utf-8")
    for key in LINKS_TO_POPULATE:
        assert f"{key}:" in bd, f"basic_design.md links に {key} が追加されているはず"
    assert set(result["populated_links"].keys()) == set(LINKS_TO_POPULATE.keys())


def test_apply_blocked_when_gate_approved(feature_dir: Path):
    """Gate 1/2 が承認済みの場合 --apply は PermissionError を raise."""
    _write_approval_approved(feature_dir / "APPROVAL.md")
    with pytest.raises(PermissionError) as excinfo:
        bridge_to_phase1(feature_dir, target_section="phase1", apply=True)
    assert "Phase 1 immutability" in str(excinfo.value)


def test_apply_idempotent_skips_existing(feature_dir: Path):
    """同じ --apply を 2 回実行 → 2 回目は populated 空 + skipped に既存 keys."""
    bridge_to_phase1(feature_dir, target_section="phase1", apply=True)
    result2 = bridge_to_phase1(feature_dir, target_section="phase1", apply=True)
    assert result2["populated_links"] == {}
    assert len(result2["skipped"]) == len(LINKS_TO_POPULATE)


def test_missing_upstream_dir_raises(tmp_path: Path):
    """upstream/ ディレクトリ不在で FileNotFoundError."""
    fd = tmp_path / "specs" / "no_upstream"
    fd.mkdir(parents=True)
    _write_basic_design_with_links(fd / "basic_design.md", "no_upstream")
    _write_approval_unapproved(fd / "APPROVAL.md")
    with pytest.raises(FileNotFoundError):
        bridge_to_phase1(fd, target_section="phase1")


def test_invalid_target_raises(feature_dir: Path):
    """target_section が phase1 以外で ValueError."""
    with pytest.raises(ValueError):
        bridge_to_phase1(feature_dir, target_section="phase2")


def test_is_gate_approved_unapproved(tmp_path: Path):
    """is_gate_approved: 未承認 (placeholder) で False."""
    p = tmp_path / "APPROVAL.md"
    _write_approval_unapproved(p)
    assert is_gate_approved(p, "Gate 1: Basic Design") is False
    assert is_gate_approved(p, "Gate 2: BPMN") is False


def test_is_gate_approved_approved(tmp_path: Path):
    """is_gate_approved: 承認済 (全 [x] + 承認者名) で True."""
    p = tmp_path / "APPROVAL.md"
    _write_approval_approved(p)
    assert is_gate_approved(p, "Gate 1: Basic Design") is True
    assert is_gate_approved(p, "Gate 2: BPMN") is True


def test_is_gate_approved_real_phase_a():
    """is_gate_approved: 実機 specs/val_a01/APPROVAL.md (全 Gate 承認済) で True."""
    real_path = REPO_ROOT / "specs" / "val_a01" / "APPROVAL.md"
    if real_path.exists():
        assert is_gate_approved(real_path, "Gate 1: Basic Design") is True


def test_valid_targets_constant():
    """Public constant stability."""
    assert VALID_TARGETS == {"phase1"}


def test_warnings_for_missing_artifacts(feature_dir: Path):
    """Phase 0 成果物が一部欠損していても warnings に記録、exception にはしない."""
    result = bridge_to_phase1(feature_dir, target_section="phase1", apply=False)
    # business_need / value_canvas / stakeholder_map のみ存在、その他は欠損 → warnings あり
    assert any("missing upstream artifact" in w for w in result["warnings"])


def test_apply_does_not_modify_process_bpmn(feature_dir: Path):
    """--apply で process.bpmn が変更されないこと (BPMN は人間責務、Phase C ルール)."""
    bpmn_path = feature_dir / "process.bpmn"
    original_bpmn = '<?xml version="1.0"?><bpmn:definitions></bpmn:definitions>\n'
    bpmn_path.write_text(original_bpmn, encoding="utf-8")
    bridge_to_phase1(feature_dir, target_section="phase1", apply=True)
    assert bpmn_path.read_text(encoding="utf-8") == original_bpmn, (
        "process.bpmn は --apply で変更されてはいけない (BPMN 編集は人間責務)"
    )


def test_apply_does_not_create_implementation_details(feature_dir: Path):
    """--apply で implementation-details/ が作られないこと (Phase 2 領域、Phase C ルール)."""
    impl_dir = feature_dir / "implementation-details"
    assert not impl_dir.exists(), "前提条件: implementation-details/ が存在しない"
    bridge_to_phase1(feature_dir, target_section="phase1", apply=True)
    assert not impl_dir.exists(), (
        "implementation-details/ は --apply で作られてはいけない (Phase 2 領域)"
    )


def test_is_gate_approved_rejects_underscore_only_approver(tmp_path: Path):
    """is_gate_approved: 承認者欄が underscore のみの偽装パターンを弾く (Phase C 強化)."""
    import textwrap
    p = tmp_path / "APPROVAL_underscore.md"
    # チェックボックスは [x] で承認者欄が短い (4 文字) underscore — 偽装として弾くべき
    p.write_text(
        textwrap.dedent("""\
            # 承認記録

            ## Gate 1: Basic Design

            確認項目：

            - [x] basic_design.md の WHO/WHAT/WHY が正しい

            ```
            承認者: ____
            日付:   2026-04-29
            ```
            """),
        encoding="utf-8",
    )
    assert is_gate_approved(p, "Gate 1: Basic Design") is False, (
        "underscore のみで構成された承認者欄は placeholder として未承認扱いとすべき"
    )


def test_is_gate_approved_accepts_real_japanese_name(tmp_path: Path):
    """is_gate_approved: 実名 (日本語含む) で承認済 True を返す."""
    import textwrap
    p = tmp_path / "APPROVAL_jp.md"
    p.write_text(
        textwrap.dedent("""\
            # 承認記録

            ## Gate 1: Basic Design

            確認項目：

            - [x] basic_design.md の WHO/WHAT/WHY が正しい

            ```
            承認者: 岡崎仁士
            日付:   2026-04-29
            ```
            """),
        encoding="utf-8",
    )
    assert is_gate_approved(p, "Gate 1: Basic Design") is True
