"""Test: upstream_migration_helper.migrate_v5x_to_v6() — Phase D WI-VALD01-006 (TS-UT-01/02).

Covers AC-US-FEATVALD01-005-01 (helper CLI surface: dry-run / --apply / failure cases /
BACCM 6 axis label assignment) and AC-US-FEATVALD01-006-01 (regression防止 + +5 件以上).

baseline 769 → 774+ passed を担保。既存テスト破壊 0 件。
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from upstream_migration_helper import (
    ARTIFACTS,
    BACCM_AXES,
    PHASE_0_DIR,
    migrate_v5x_to_v6,
)


def _write_basic_design(path: Path, *, profile: str = "enterprise-erp", feature_id: str = "FEAT-VTEST01"):
    """v5.x 風の basic_design.md を生成 (frontmatter + canonical YAML block)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(f"""\
            ---
            artifact: "basic_design"
            feature_id: "{feature_id}"
            title: "Test v5.x basic_design"
            owners:
              - {{ name: "Test Owner", role: "PM" }}
            ---

            > Rule-0: 正本は #0 Canonical Basic Design (YAML)。

            # 0. Canonical Basic Design (YAML)
            ```yaml
            id_conventions_ref: "memory/constitution.md#id_conventions"

            basic_design:
              profile: "{profile}"
              context:
                who: "業務部門 + IT 部門"
                what: "テスト用の v5.x 基本設計"
                why: "Phase D helper の動作検証"
              business_domain:
                value_chain: "P2P"
                capability: "テスト DX"
                domain_objects: ["Test", "Vendor"]
              scope:
                in:
                  - "テスト用機能の追加"
                out:
                  - "本番デプロイ"
              systems:
                - system: "TestERP"
                  category: "ERP"
                  owner: "QA Team"
                  integration_modes: ["API"]
              raci_plus:
                actors: ["TJ_Human_PM", "TJ_AI_CodingAgent"]
                rules:
                  - "AI は Accountable になれない"
              delivery_model:
                type: "requirements-driven"
                rationale: "テスト用"
              decisions:
                - id: "DR-001"
                  context: "テスト判断"
                  options: ["A", "B"]
                  decision: "A"
                  consequences: "テストが進む"
              exceptions: []
            ```

            # 1. Document Intent
            (auxiliary)
            """),
        encoding="utf-8",
    )


def _write_corrupted_basic_design(path: Path):
    """YAML パース失敗を意図的に発生させる basic_design.md。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent("""\
            ---
            artifact: "basic_design"
            ---

            # 0. Canonical Basic Design (YAML)
            ```yaml
            basic_design:
              context:
                who: "test"
                  bad_indent: invalid_yaml
                deep: [unclosed
            ```
            """),
        encoding="utf-8",
    )


# =====================================================================
# TS-UT-01 / TS-CON-01: helper CLI surface (CT-CLI-01) basic dry-run
# =====================================================================


def test_dry_run_returns_drafts_for_all_seven_artifacts(tmp_path):
    """dry-run で 7 つの BACCM 軸 yaml が drafts に生成される (TS-UT-01-01)."""
    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md")

    result = migrate_v5x_to_v6(feature_dir, apply=False)

    assert result["feature_id"] == "FEAT-VTEST01"
    assert result["detected_profile"] == "enterprise-erp"
    assert set(result["drafts"].keys()) == set(ARTIFACTS), (
        f"7 artifacts 期待、実際: {sorted(result['drafts'].keys())}"
    )
    # 各 draft は yaml 文字列で、parse 可能であること
    for filename, body in result["drafts"].items():
        parsed = yaml.safe_load(body)
        assert isinstance(parsed, dict), f"{filename} の yaml が dict でない"
        assert parsed.get("artifact") == filename.replace(".yaml", ""), (
            f"{filename} の artifact 名が不一致"
        )
        assert "labels" in parsed, f"{filename} に labels セクションがない"

    # dry-run では upstream/ ディレクトリは作られない
    assert not (feature_dir / "upstream").exists()


def test_dry_run_baccm_labels_classify_auto_vs_human(tmp_path):
    """各 seed に auto_extracted と human_review_needed の両ラベルが含まれる (TS-UT-01-02)."""
    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md")

    result = migrate_v5x_to_v6(feature_dir)

    for filename, body in result["drafts"].items():
        parsed = yaml.safe_load(body)
        labels = parsed.get("labels", {})
        assert "auto_extracted" in labels, f"{filename} に auto_extracted がない"
        assert "human_review_needed" in labels, f"{filename} に human_review_needed がない"
        # change_strategy.yaml と goal_tree.yaml は必ず human_review が入る (実装上の保証)
        if filename in ("change_strategy.yaml", "goal_tree.yaml"):
            assert len(labels["human_review_needed"]) >= 1, (
                f"{filename} は human_review_needed が必ず 1 件以上含まれるはず"
            )


# =====================================================================
# TS-UT-01: --apply で実書込
# =====================================================================


def test_apply_writes_seven_yaml_files_under_phase_0_discovery(tmp_path):
    """--apply で 7 ファイルが upstream/phase_0_discovery/ 配下に生成 (TS-UT-01-03)."""
    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md")

    result = migrate_v5x_to_v6(feature_dir, apply=True)

    target_dir = feature_dir / "upstream" / PHASE_0_DIR
    assert target_dir.is_dir(), "upstream/phase_0_discovery/ ディレクトリが作成されていない"

    written = result["written"]
    assert len(written) == 7, f"7 ファイル書込期待、実際 {len(written)}"
    assert result["skipped"] == [], "初回 apply で skip があるべきではない"

    # 全 7 ファイルが parse 可能な yaml
    for filename in ARTIFACTS:
        target = target_dir / filename
        assert target.is_file(), f"{filename} が書き込まれていない"
        parsed = yaml.safe_load(target.read_text(encoding="utf-8"))
        assert isinstance(parsed, dict)
        assert "labels" in parsed


def test_apply_is_idempotent_skip_existing_files(tmp_path):
    """既存ファイルがある場合 skip + warn (冪等性、TS-UT-01-04)."""
    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md")

    # 1 回目 apply
    first = migrate_v5x_to_v6(feature_dir, apply=True)
    assert len(first["written"]) == 7
    assert first["skipped"] == []

    # 同じ basic_design で再 apply → 全て skip
    second = migrate_v5x_to_v6(feature_dir, apply=True)
    assert len(second["skipped"]) == 7, f"再 apply で 7 件 skip 期待、実際 {len(second['skipped'])}"
    assert second["written"] == [], "再 apply で書込があるべきではない"
    # warnings に skip メッセージが追加される
    skip_warnings = [w for w in second["warnings"] if "already exists, skipped" in w]
    assert len(skip_warnings) == 7


# =====================================================================
# TS-UT-01: 失敗ケース (exit 1 / exit 2)
# =====================================================================


def test_missing_feature_dir_raises_filenotfound(tmp_path):
    """feature_dir 不在 → FileNotFoundError (CLI exit 1、TS-UT-01-05)."""
    nonexistent = tmp_path / "nonexistent_feature"

    with pytest.raises(FileNotFoundError) as excinfo:
        migrate_v5x_to_v6(nonexistent)

    assert "feature_dir not found" in str(excinfo.value)


def test_missing_basic_design_raises_filenotfound(tmp_path):
    """basic_design.md 不在 → FileNotFoundError (CLI exit 1、TS-UT-01-06)."""
    feature_dir = tmp_path / "specs" / "empty_feat"
    feature_dir.mkdir(parents=True)
    # basic_design.md を作らない

    with pytest.raises(FileNotFoundError) as excinfo:
        migrate_v5x_to_v6(feature_dir)

    assert "basic_design.md not found" in str(excinfo.value)


def test_corrupted_basic_design_raises_yaml_or_value_error(tmp_path):
    """basic_design.md の YAML パース失敗 → YAMLError or ValueError (CLI exit 2、TS-UT-01-07)."""
    feature_dir = tmp_path / "specs" / "broken_feat"
    _write_corrupted_basic_design(feature_dir / "basic_design.md")

    with pytest.raises((yaml.YAMLError, ValueError)):
        migrate_v5x_to_v6(feature_dir)


# =====================================================================
# TS-UT-02 (補助): profile override + post_apply_actions
# =====================================================================


def test_profile_override_overrides_auto_detect(tmp_path):
    """--profile 引数で auto-detect を上書きできる (TS-UT-02-01)."""
    feature_dir = tmp_path / "specs" / "v5x_feat"
    # basic_design は enterprise-erp、override で saas-integration を強制
    _write_basic_design(feature_dir / "basic_design.md", profile="enterprise-erp")

    result = migrate_v5x_to_v6(feature_dir, profile="saas-integration")
    assert result["detected_profile"] == "saas-integration"


def test_post_apply_actions_include_validate_lint_and_review(tmp_path):
    """post_apply_actions に validate / lint / human review が必ず含まれる (TS-UT-02-02)."""
    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md")

    result = migrate_v5x_to_v6(feature_dir)
    actions = " ".join(result["post_apply_actions"])
    assert "stride upstream validate" in actions
    assert "stride lint --upstream" in actions or "lint --upstream" in actions
    assert "Human review" in actions or "human" in actions.lower()


# =====================================================================
# Post-review additions: API guards + CLI surface verification
# =====================================================================


def test_invalid_profile_passes_through_to_detected_profile(tmp_path):
    """API レベルでは argparse の choices 外 profile も pass-through 動作 (TS-UT-02-03、保険的回帰防止).

    CLI argparse は `choices=...` で防御するが、Python API 直接呼び出しでは validation を
    強制しない (caller 責務)。`detected_profile` には override 値がそのまま入り、basic_design
    側の profile が失われないことだけを保証する (現状仕様の lock-in)。
    """
    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md", profile="enterprise-erp")

    # API 直接呼び出し: argparse choices をバイパスする経路
    result = migrate_v5x_to_v6(feature_dir, profile="custom-future-profile")
    assert result["detected_profile"] == "custom-future-profile", (
        "API は profile override をそのまま採用する仕様 (caller 責務)"
    )
    # 7 artifact 生成は profile 値に関係なく成立する
    assert set(result["drafts"].keys()) == set(ARTIFACTS)


def test_main_apply_then_reapply_emits_skip_section_to_stdout(tmp_path, capsys, monkeypatch):
    """CLI main(): --apply 後の再 apply で stdout に skip 一覧が表示される (TS-UT-02-04).

    既存ファイル冪等性 (skip + warn) は API レベルで test_apply_is_idempotent_skip_existing_files が
    検証済。本テストは **CLI 表面 (stdout の "skipped (already exists)" セクション)** を lock-in する。
    """
    from upstream_migration_helper import main

    feature_dir = tmp_path / "specs" / "v5x_feat"
    _write_basic_design(feature_dir / "basic_design.md")

    # 1 回目 apply: 全 7 ファイル written
    monkeypatch.setattr("sys.argv", ["upstream_migration_helper", str(feature_dir), "--apply"])
    rc1 = main()
    assert rc1 == 0
    out1 = capsys.readouterr().out
    assert "written: 7 files" in out1
    assert "skipped (already exists)" not in out1, "初回 apply で skip 表示されてはならない"

    # 2 回目 apply: 全 7 ファイル skipped
    monkeypatch.setattr("sys.argv", ["upstream_migration_helper", str(feature_dir), "--apply"])
    rc2 = main()
    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "written: 0 files" in out2
    assert "skipped (already exists): 7 files" in out2, (
        "再 apply で skip 一覧セクションが stdout に表示されるべき"
    )
