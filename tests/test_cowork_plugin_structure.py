"""Test: Cowork Plugin 構造の機械検証 — Phase E (FEAT-VALE01).

Covers AC-US-FEATVALE01-001-01 (plugin.json valid + 必須 keys) と
AC-US-FEATVALE01-002-01 (reference_files 49 件厳守) と
AC-US-FEATVALE01-005-01 (Skills 7 + Commands 9 個数厳守)。

baseline 780 → 783+ passed を担保 (3 件分)。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "cowork-plugin"


# =====================================================================
# TS-CON-01 / TS-INT-01: plugin.json valid + 必須 keys
# =====================================================================


def test_plugin_json_is_valid_with_required_keys():
    """plugin.json が valid JSON で、name/version/description/author/license の必須項目を含む.

    AC-US-FEATVALE01-001-01 の機械検証.
    Anthropic 公式 knowledge-work-plugins schema 準拠 (`claude plugin validate` でも検証可能).
    """
    plugin_json_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    assert plugin_json_path.is_file(), f"plugin.json が見つからない: {plugin_json_path}"

    data = json.loads(plugin_json_path.read_text(encoding="utf-8"))

    # 必須 keys
    required_keys = ["name", "version", "description", "author", "license"]
    missing = [k for k in required_keys if k not in data]
    assert not missing, f"plugin.json に必須 keys が不足: {missing}"

    # 値の妥当性
    assert data["name"] == "tecnos-stride-value", f"plugin name 不一致: {data['name']}"
    # Phase F (WI-VALF01-009) で 0.1.0-poc → 0.2.0-stable に bump。0.x 系は受容、それ以外は不正。
    assert data["version"].startswith("0."), (
        f"plugin version は 0.x 系を維持 (Phase F 完了時 0.2.0-stable、Phase G で 1.0.0 候補): {data['version']}"
    )
    assert data["license"] == "MIT", f"license 不一致: {data['license']}"
    assert "BABOK" in data["description"] and (
        "Layered Context Modelling" in data["description"]
        or "Layered Requirements" in data["description"]
        or "4-layer Requirements Architecture" in data["description"]
    ), (
        "plugin.json description が BABOK + Layered (Context Modelling | Requirements Architecture) に言及していない "
        "(Plugin の本質: BABOK + 4-layer Requirements Architecture、固有商標名は使用しない方針)"
    )

    # author は dict (name 含む) — Anthropic spec
    assert isinstance(data["author"], dict) and "name" in data["author"], (
        f"author は {{name: ...}} 形式必須、実際: {data['author']}"
    )


def test_plugin_json_repository_is_string_per_anthropic_spec():
    """plugin.json の repository フィールドが string であること (Anthropic 公式仕様).

    Post-merge defect (PR #10) の回帰防止: npm package.json では repository を object
    ({type, url}) で記述するが、Anthropic knowledge-work-plugins では string (URL) のみ受け入れる。
    `claude plugin validate` で `repository: Invalid input: expected string, received object`
    エラーになる実装を防ぐ.
    """
    plugin_json_path = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    data = json.loads(plugin_json_path.read_text(encoding="utf-8"))

    # repository は optional だが、含める場合は string (Anthropic spec)
    if "repository" in data:
        assert isinstance(data["repository"], str), (
            f"repository は string が必須 (Anthropic plugin spec)、"
            f"実際: {type(data['repository']).__name__} = {data['repository']!r}\n"
            f"NPM 形式の {{type, url}} object は受け付けられない (claude plugin validate FAIL の原因)"
        )
        # URL 形式の最小限チェック (https:// または http:// で開始)
        assert data["repository"].startswith(("https://", "http://", "git+https://", "git@")), (
            f"repository は URL string であること、実際: {data['repository']!r}"
        )

    # homepage も同様に string であることを確認 (現行実装の lock-in)
    if "homepage" in data:
        assert isinstance(data["homepage"], str), (
            f"homepage は string が必須、実際: {type(data['homepage']).__name__}"
        )


# =====================================================================
# TS-CON-02 / TS-INT-02: reference_files 49 件厳守
# =====================================================================


def test_reference_files_count_is_exactly_49():
    """cowork-plugin/reference_files/ 配下のファイル数が 46 件であること.

    AC-US-FEATVALE01-002-01 の機械検証 (Hitoshi さん v3 P0-2 確定値、Phase E は 49)。
    BPMN package integration v0.4.0 (commit 6acd3fe) で BPMN 4 ファイル
    (bpmn_quick_reference.md / camunda_bpmn_practice_guide.md / camunda_bpmn_dictionary_complete.md /
    bpmn_generator_rules.md) を reference_files/docs/ から bpmn/rules/ + bpmn/spec/ に移動 (drift 防止)、
    49 → 46 に正規化 (関数名は historical reference として維持)。
    """
    ref_dir = PLUGIN_DIR / "reference_files"
    assert ref_dir.is_dir(), f"reference_files/ が見つからない: {ref_dir}"

    files = [p for p in ref_dir.rglob("*") if p.is_file()]
    actual = len(files)
    expected = 46  # v0.4.0-bpmn-package-integration 以降の確定値

    if actual != expected:
        # ドリフト検出時は内訳を出力 (デバッグ補助)
        breakdown = {}
        for f in files:
            top = f.relative_to(ref_dir).parts[0] if f.parent != ref_dir else "(root)"
            breakdown[top] = breakdown.get(top, 0) + 1
        breakdown_str = "\n".join(f"  {k}: {v}" for k, v in sorted(breakdown.items()))
        pytest.fail(
            f"reference_files 件数ドリフト: 期待 {expected} / 実際 {actual}\n"
            f"内訳:\n{breakdown_str}\n"
            f"対応: scripts/sync_cowork_plugin_reference.sh の find 範囲点検 + counts 同期更新"
        )

    assert actual == expected


# =====================================================================
# TS-INT-03 / TS-INT-04: Skills 7 + Commands 11 個数厳守 (Phase E 9 + Phase F 新規 2)
# =====================================================================


def test_skills_and_commands_count_match_phase_e_spec():
    """Skills 8 + Commands 14 が存在し、ファイル名規約に準拠.

    AC-US-FEATVALE01-003-01 + AC-US-FEATVALE01-005-01 の機械検証.
    Phase F (WI-VALF01-011/016) で stride-export-html + stride-tasking が追加され 9 → 11 に bump、
    Phase G UX-prep PR-D で stride-bootstrap-repo 追加 11 → 12、PR-E で stride-conductor skill + /start command 追加 (skills 7→8、commands 12→13)、
    BPMN package integration (commit 6acd3fe v0.4.0) で stride-bpmn-validate 追加 13 → 14。
    """
    skills_dir = PLUGIN_DIR / "skills"
    commands_dir = PLUGIN_DIR / "commands"
    assert skills_dir.is_dir() and commands_dir.is_dir()

    # Skills: 8 個 (Phase E 7 + Phase G UX-prep 新規 1: stride-conductor、各 <name>/SKILL.md)
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    expected_skills = {
        # Phase E (7 個、Phase G PR-A で rdra → layered rename 済)
        "baccm-discovery",
        "babok-elicitation",
        "layered-context-modelling",
        "upstream-bridge",
        "basic-design-authoring",
        "bpmn-authoring",
        "epic-decomposition",
        # Phase G UX-prep 新規 (1 個): master orchestrator (自然言語入口)
        "stride-conductor",
    }
    actual_skill_names = {p.parent.name for p in skill_files}
    assert actual_skill_names == expected_skills, (
        f"Skills 名不一致: 期待 {expected_skills} / 実際 {actual_skill_names}"
    )
    assert len(skill_files) == 8

    # Commands: 14 個 (Phase E 9 + Phase F 新規 2 + Phase G UX-prep 新規 2 + BPMN package 1)
    # Phase G PR-F-hotfix で start.md は stride- prefix なし (Hitoshi さんが期待する短い slash `/tecnos-stride-value:start` 正規化)。
    # BPMN package integration (commit 6acd3fe v0.4.0) で stride-bpmn-validate.md 追加。
    # glob は *.md (全件) に拡げる。
    command_files = sorted(commands_dir.glob("*.md"))
    expected_commands = {
        # Phase E (9 個)
        "stride-init",
        "stride-discovery",
        "stride-elicit",
        "stride-context-model",
        "stride-validate",
        "stride-bridge",
        "stride-design",
        "stride-epic-init",
        "stride-handoff",
        # Phase F 新規 (2 個)
        "stride-export-html",
        "stride-tasking",
        # Phase G UX-prep 新規 (2 個): Repository Bootstrap (PR-D) + Simple UX 1-cmd entry (PR-E + PR-F-hotfix で stride-start → start rename)
        "stride-bootstrap-repo",
        "start",
        # BPMN package integration v0.4.0 (1 個): /stride:bpmn-validate (FEAT 14 / EPIC 9 MUST-DO 自動検証)
        "stride-bpmn-validate",
    }
    actual_command_names = {p.stem for p in command_files}
    assert actual_command_names == expected_commands, (
        f"Commands 名不一致: 期待 {expected_commands} / 実際 {actual_command_names}"
    )
    assert len(command_files) == 14
