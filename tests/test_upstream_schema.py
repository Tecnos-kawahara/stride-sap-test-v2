"""Test: Upstream artifact template schema integrity (FEAT-VALA01 Phase A).

Validates all 15 templates under sdd-templates/templates/upstream/ parse as YAML,
have required common metadata fields, and follow the TPL-UP-XXX-NNN template_id
regex. Also verifies the 4 manual chapters (39-42) exist with at least 3000 chars.

Covers AC-US-FEATVALA01-001-01 (schema integrity) and AC-US-FEATVALA01-001-05
(manual chapters) per spec.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_DIR = REPO_ROOT / "sdd-templates" / "templates" / "upstream"
MANUAL_DIR = REPO_ROOT / "manual"

EXPECTED_TEMPLATES = [
    "business_need_template.yaml",
    "value_canvas_template.yaml",
    "stakeholder_map_template.yaml",
    "context_map_template.yaml",
    "risk_register_template.yaml",
    "change_strategy_template.yaml",
    "goal_tree_template.yaml",
    "elicitation_plan_template.yaml",
    "elicitation_results_template.yaml",
    "actor_system_template.yaml",
    "business_usecase_template.yaml",
    "information_state_template.yaml",
    "condition_variation_template.yaml",
    "usecase_complex_template.yaml",
    "requirements_architecture_template.yaml",
]

REQUIRED_KEYS = {
    "artifact",
    "template_id",
    "phase",
    "profile_applicability",
    "links",
}

VALID_PHASES = {
    "phase_0_discovery",
    "phase_0_3_elicit",
    "phase_0_5_context_modelling",
}

VALID_PROFILES = {"enterprise-erp", "saas-integration", "prototype"}

TEMPLATE_ID_PATTERN = re.compile(r"^TPL-UP-[A-Z]{3,4}-[0-9]{3}$")


def _load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as f:
        text = f.read()
    # 各テンプレートはフロントマター区切りを持つ。--- でフレーム化された YAML を扱う。
    if text.startswith("---"):
        # split into [empty, frontmatter, body]
        parts = text.split("---", 2)
        body = parts[2] if len(parts) > 2 else ""
    else:
        body = text
    return yaml.safe_load(body)


def test_all_15_templates_exist():
    """sdd-templates/templates/upstream/ に 15 テンプレが揃っている"""
    assert UPSTREAM_DIR.is_dir(), f"upstream/ ディレクトリ不存在: {UPSTREAM_DIR}"
    actual = sorted(p.name for p in UPSTREAM_DIR.glob("*_template.yaml"))
    assert actual == sorted(EXPECTED_TEMPLATES), (
        f"テンプレート集合が期待値と一致しない\n"
        f"  expected: {sorted(EXPECTED_TEMPLATES)}\n"
        f"  actual:   {actual}"
    )


def test_readme_exists():
    """sdd-templates/templates/upstream/README.md が索引として存在"""
    readme = UPSTREAM_DIR / "README.md"
    assert readme.is_file(), f"README.md が不存在: {readme}"
    text = readme.read_text(encoding="utf-8")
    assert len(text) > 1000, "README.md は 1000 字以上が想定"


@pytest.mark.parametrize("filename", EXPECTED_TEMPLATES)
def test_template_yaml_parses_and_has_required_keys(filename: str):
    """各テンプレが YAML として parse 可能で必須キーを持つ"""
    path = UPSTREAM_DIR / filename
    data = _load_yaml(path)
    assert isinstance(data, dict), f"{filename} は YAML map として parse できる必要がある"

    missing = REQUIRED_KEYS - set(data.keys())
    assert not missing, f"{filename}: 必須キー欠落 {missing}"

    # template_id 正規表現
    tpl_id = data["template_id"]
    assert TEMPLATE_ID_PATTERN.match(tpl_id), (
        f"{filename}: template_id={tpl_id!r} が ^TPL-UP-[A-Z]{{3,4}}-[0-9]{{3}}$ に一致しない"
    )

    # phase 値域
    phase = data["phase"]
    assert phase in VALID_PHASES, f"{filename}: phase={phase!r} が許可値範囲外 {VALID_PHASES}"

    # profile_applicability 値域
    profiles = data.get("profile_applicability") or []
    assert isinstance(profiles, list) and profiles, (
        f"{filename}: profile_applicability は非空リスト必須"
    )
    bad = set(profiles) - VALID_PROFILES
    assert not bad, f"{filename}: 不正な profile {bad}"

    # links 必須参照
    links = data.get("links") or {}
    for required_link in [
        "upstream_policy_ref",
        "baccm_completeness_ref",
        "iteration_policy_ref",
    ]:
        assert required_link in links, f"{filename}: links.{required_link} 欠落"


def test_unique_template_ids():
    """15 テンプレの template_id がすべてユニーク"""
    ids = []
    for filename in EXPECTED_TEMPLATES:
        data = _load_yaml(UPSTREAM_DIR / filename)
        ids.append(data["template_id"])
    assert len(set(ids)) == len(ids), f"template_id 重複あり: {ids}"
    assert len(ids) == 15, f"template_id 件数 {len(ids)} != 15"


@pytest.mark.parametrize(
    "chapter",
    [
        "39_value_upstream_overview.md",
        "40_baccm_guide.md",
        "41_layered_requirements_modeling_guide.md",
        "42_upstream_phases_walkthrough.md",
    ],
)
def test_manual_chapter_exists_and_has_min_chars(chapter: str):
    """manual/39-42 が存在し最低 3000 字 (AC-05 lower bound)"""
    path = MANUAL_DIR / chapter
    assert path.is_file(), f"manual chapter 不存在: {path}"
    chars = len(path.read_text(encoding="utf-8"))
    assert chars >= 3000, f"{chapter}: {chars} 字 (3000 字以上必須)"


def test_sidebar_contains_new_chapters():
    """manual/_sidebar.md に新章 39-42 のリンクが追記されている"""
    sidebar = MANUAL_DIR / "_sidebar.md"
    text = sidebar.read_text(encoding="utf-8")
    for chapter_path in [
        "39_value_upstream_overview.md",
        "40_baccm_guide.md",
        "41_layered_requirements_modeling_guide.md",
        "42_upstream_phases_walkthrough.md",
    ]:
        assert chapter_path in text, f"_sidebar.md に {chapter_path} のリンクがない"


def test_project_map_has_value_section():
    """agent_docs/project_map.md に Upstream/VALUE/BACCM のいずれかを含む追記がある"""
    pm = REPO_ROOT / "agent_docs" / "project_map.md"
    text = pm.read_text(encoding="utf-8")
    assert any(kw in text for kw in ["Upstream", "VALUE", "BACCM"]), (
        "project_map.md に Upstream/VALUE/BACCM 追記がない"
    )
