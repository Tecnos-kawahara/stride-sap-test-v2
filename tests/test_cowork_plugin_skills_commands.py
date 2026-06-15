"""Test: Cowork Plugin Skills + Commands frontmatter 機械検証 — Phase E (FEAT-VALE01).

Covers AC-US-FEATVALE01-007-01 (frontmatter parser + cross-reference + reference_files 実在性).

baseline 783 → 788+ passed を担保 (5 件分、test_cowork_plugin_structure.py の 3 件と合わせて +8)。
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "cowork-plugin"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def _parse_frontmatter(path: Path) -> dict:
    """Markdown ファイルの YAML frontmatter を dict として返す."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


# =====================================================================
# TS-UT-01: SKILL.md frontmatter (name + description + argument-hint)
# =====================================================================


def test_all_skills_have_required_frontmatter_fields():
    """全 7 SKILL.md に name + description + argument-hint フィールドが存在.

    AC-US-FEATVALE01-007-01 の Skills 部分.
    """
    skills_dir = PLUGIN_DIR / "skills"
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))
    assert len(skill_files) == 8, f"Skills 8 個必須 (Phase E 7 + Phase G UX-prep 新規 1: stride-conductor)、実際 {len(skill_files)}"

    failures = []
    for skill_path in skill_files:
        fm = _parse_frontmatter(skill_path)
        for required in ("name", "description", "argument-hint"):
            if required not in fm or not fm[required]:
                failures.append(f"{skill_path.parent.name}: missing/empty `{required}`")

    assert not failures, "Skills frontmatter 不備:\n" + "\n".join(failures)


# =====================================================================
# TS-UT-02 (1/2): Skill name が dir 名と一致 (cross-reference)
# =====================================================================


def test_skill_name_matches_directory_name():
    """SKILL.md の frontmatter name が親ディレクトリ名と一致.

    Plugin 利用者が `/<command>` で起動した skill が正しく解決されることを保証.
    """
    skills_dir = PLUGIN_DIR / "skills"
    skill_files = sorted(skills_dir.glob("*/SKILL.md"))

    mismatches = []
    for skill_path in skill_files:
        fm = _parse_frontmatter(skill_path)
        dir_name = skill_path.parent.name
        if fm.get("name") != dir_name:
            mismatches.append(
                f"{dir_name}/SKILL.md: frontmatter name={fm.get('name')!r} != dir name={dir_name!r}"
            )

    assert not mismatches, "Skill name と dir 名の不一致:\n" + "\n".join(mismatches)


# =====================================================================
# TS-UT-02 (2/2): Commands frontmatter (description + argument-hint)
# =====================================================================


def test_all_commands_have_required_frontmatter_fields():
    """全 13 commands/*.md (Phase E 9 + Phase F 新規 2 + Phase G UX-prep 新規 2) に description + argument-hint フィールドが存在.

    AC-US-FEATVALE01-007-01 の Commands 部分.
    Phase F (WI-VALF01-011/016) で stride-export-html + stride-tasking が追加され 9 → 11、
    Phase G UX-prep PR-D で stride-bootstrap-repo 11 → 12、PR-E + PR-F-hotfix で start (元 stride-start) 12 → 13 (Simple UX 1-cmd entry、`/tecnos-stride-value:start` 正規化)。
    """
    commands_dir = PLUGIN_DIR / "commands"
    command_files = sorted(commands_dir.glob("*.md"))
    assert len(command_files) == 14, f"Commands 14 個必須 (Phase E 9 + Phase F 新規 2 + Phase G UX-prep 新規 2 + BPMN package 1: stride-bpmn-validate)、実際 {len(command_files)}"

    failures = []
    for cmd_path in command_files:
        fm = _parse_frontmatter(cmd_path)
        for required in ("description", "argument-hint"):
            if required not in fm or not fm[required]:
                failures.append(f"{cmd_path.name}: missing/empty `{required}`")

    assert not failures, "Commands frontmatter 不備:\n" + "\n".join(failures)


# =====================================================================
# Skill ↔ Command cross-reference (Trigger Skill 整合性)
# =====================================================================


def test_commands_workflow_references_skills_with_unique_namespace():
    """Commands の Workflow が `/stride:<command>` namespace で記述、Skill 起動を明記している.

    Phase E プロンプトの Plugin namespace `/stride:<command>` 形式厳守を機械検証.
    """
    commands_dir = PLUGIN_DIR / "commands"
    command_files = sorted(commands_dir.glob("stride-*.md"))

    failures = []
    for cmd_path in command_files:
        text = cmd_path.read_text(encoding="utf-8")
        cmd_name = cmd_path.stem  # "stride-init" etc.
        # Plugin namespace `/stride:<command>` を Workflow セクションで言及している
        # (`/stride:init`, `/stride:discovery` etc.)
        expected_namespace = "/stride:" + cmd_name.removeprefix("stride-")
        if expected_namespace not in text:
            failures.append(
                f"{cmd_path.name}: Workflow に `{expected_namespace}` の言及なし"
            )

    assert not failures, "Commands namespace 不整合:\n" + "\n".join(failures)


# =====================================================================
# .mcp.json valid JSON + filesystem + github 2 servers
# =====================================================================


def test_mcp_json_has_filesystem_and_github_servers():
    """cowork-plugin/.mcp.json が valid JSON で filesystem + github 2 servers を定義.

    AC-US-FEATVALE01-006-01 の機械検証.
    """
    mcp_json_path = PLUGIN_DIR / ".mcp.json"
    assert mcp_json_path.is_file(), f".mcp.json が見つからない: {mcp_json_path}"

    data = json.loads(mcp_json_path.read_text(encoding="utf-8"))
    assert "mcpServers" in data, ".mcp.json に mcpServers が無い"

    servers = data["mcpServers"]
    expected_servers = {"filesystem", "github"}
    assert set(servers.keys()) == expected_servers, (
        f"MCP servers 不一致: 期待 {expected_servers} / 実際 {set(servers.keys())}"
    )

    # github server は GITHUB_PERSONAL_ACCESS_TOKEN env を使用
    github_env = servers["github"].get("env", {})
    assert "GITHUB_PERSONAL_ACCESS_TOKEN" in github_env, (
        f"github MCP は GITHUB_PERSONAL_ACCESS_TOKEN env が必須、実際 env: {github_env}"
    )

    # filesystem server は ${WORKSPACE} を args で参照
    fs_args = servers["filesystem"].get("args", [])
    assert any("WORKSPACE" in arg for arg in fs_args), (
        f"filesystem MCP は ${{WORKSPACE}} 参照必須、実際 args: {fs_args}"
    )
