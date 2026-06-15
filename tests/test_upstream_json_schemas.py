"""Test: 15 JSON Schemas (Draft 2020-12) — Phase B WI-005 (TS-INT-08).

Covers AC-US-FEATVALB01-001-06 (15 JSON schemas) + AC-US-FEATVALB01-001-07 (manual chapters).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "sdd-templates" / "static" / "upstream_schemas"

EXPECTED_SCHEMAS = [
    "business_need.json",
    "value_canvas.json",
    "stakeholder_map.json",
    "context_map.json",
    "risk_register.json",
    "change_strategy.json",
    "goal_tree.json",
    "elicitation_plan.json",
    "elicitation_results.json",
    "actor_system.json",
    "business_usecase.json",
    "information_state.json",
    "condition_variation.json",
    "usecase_complex.json",
    "requirements_architecture.json",
]


def test_static_schema_directory_exists():
    assert SCHEMAS_DIR.is_dir(), f"missing: {SCHEMAS_DIR}"


def test_all_15_schemas_present():
    actual = sorted(p.name for p in SCHEMAS_DIR.glob("*.json"))
    assert actual == sorted(EXPECTED_SCHEMAS)


@pytest.mark.parametrize("filename", EXPECTED_SCHEMAS)
def test_each_schema_is_valid_json(filename: str):
    """JSON parse できる + Draft 2020-12 を宣言"""
    path = SCHEMAS_DIR / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "$schema" in data
    assert "draft/2020-12/schema" in data["$schema"]
    assert "title" in data
    assert "properties" in data
    # Common metadata keys must be in properties
    for required_meta in ("artifact", "template_id", "feature_id", "phase"):
        assert required_meta in data["properties"], f"{filename}: missing {required_meta}"


def test_schema_required_includes_metadata():
    """全 schema が common required (artifact, template_id, feature_id, phase, profile_applicability, links) を含む"""
    common_required = {"artifact", "template_id", "feature_id", "phase", "profile_applicability", "links"}
    for filename in EXPECTED_SCHEMAS:
        data = json.loads((SCHEMAS_DIR / filename).read_text(encoding="utf-8"))
        required = set(data.get("required", []))
        missing = common_required - required
        assert not missing, f"{filename}: missing common required keys {missing}"


# AC-US-FEATVALB01-001-07: Manual 43 / 44 existence + min length
def test_manual_chapter_43_exists():
    path = REPO_ROOT / "manual" / "43_upstream_cli_guide.md"
    assert path.is_file()
    chars = len(path.read_text(encoding="utf-8"))
    assert chars >= 3000, f"43 章の字数 {chars} < 3000"


def test_manual_chapter_44_exists():
    path = REPO_ROOT / "manual" / "44_upstream_iteration_workflow.md"
    assert path.is_file()
    chars = len(path.read_text(encoding="utf-8"))
    assert chars >= 3000, f"44 章の字数 {chars} < 3000"


def test_sidebar_includes_phase_b_chapters():
    sidebar = (REPO_ROOT / "manual" / "_sidebar.md").read_text(encoding="utf-8")
    assert "43_upstream_cli_guide.md" in sidebar
    assert "44_upstream_iteration_workflow.md" in sidebar


def test_project_map_includes_phase_b_section():
    pm = (REPO_ROOT / "agent_docs" / "project_map.md").read_text(encoding="utf-8")
    # Phase B 概要が追記されている
    assert "Phase B" in pm
    assert "upstream" in pm.lower() or "VALUE" in pm
