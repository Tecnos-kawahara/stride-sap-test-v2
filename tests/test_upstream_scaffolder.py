"""Test: upstream_scaffolder.scaffold_upstream() - Phase B WI-001 (TS-INT-01).

Verifies that `stride upstream init` correctly scaffolds Phase 0 / 0.3 / 0.5 artifacts
under specs/<feature>/upstream/<phase>/ with proper feature_id substitution and
profile-aware lite mode.

Covers AC-US-FEATVALB01-001-01.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from upstream_scaffolder import (
    scaffold_upstream,
    VALID_PHASES,
    VALID_PROFILES,
    _PHASE_NORMALIZE,
)


@pytest.fixture
def tmp_feature(tmp_path: Path) -> Path:
    """Create a minimal feature directory with mirrors of policy + templates."""
    feature_dir = tmp_path / "specs" / "tmp_feat"
    feature_dir.mkdir(parents=True)
    (feature_dir / "basic_design.md").write_text(
        '---\nartifact: "basic_design"\nprofile: "enterprise-erp"\n---\n', encoding="utf-8"
    )
    state_dir = feature_dir / "state"
    state_dir.mkdir()
    (state_dir / "state.yaml").write_text("profile: enterprise-erp\n", encoding="utf-8")

    # Mirror real policies + templates by symlink (they are read-only refs)
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "policies").mkdir()
    for f in ("upstream_policy.yaml", "baccm_completeness.yaml",
             "technique_library.yaml", "upstream_iteration_policy.yaml"):
        (tmp_path / "shared" / "policies" / f).symlink_to(
            REPO_ROOT / "shared" / "policies" / f
        )

    (tmp_path / "sdd-templates").mkdir()
    (tmp_path / "sdd-templates" / "templates").mkdir()
    (tmp_path / "sdd-templates" / "templates" / "upstream").symlink_to(
        REPO_ROOT / "sdd-templates" / "templates" / "upstream"
    )
    return tmp_path


def test_discovery_phase_generates_seven_files(tmp_feature: Path):
    """enterprise-erp + discovery → 7 ファイル生成"""
    result = scaffold_upstream("tmp_feat", "discovery", repo_root=tmp_feature)
    assert result["phase"] == "phase_0_discovery"
    assert result["profile"] == "enterprise-erp"
    assert len(result["generated_files"]) == 7
    out_dir = tmp_feature / "specs" / "tmp_feat" / "upstream" / "phase_0_discovery"
    assert (out_dir / "business_need.yaml").is_file()
    assert (out_dir / "value_canvas.yaml").is_file()
    assert (out_dir / "stakeholder_map.yaml").is_file()


def test_elicit_phase_generates_two_files(tmp_feature: Path):
    """elicit → 2 ファイル生成"""
    result = scaffold_upstream("tmp_feat", "elicit", repo_root=tmp_feature)
    assert result["phase"] == "phase_0_3_elicit"
    assert len(result["generated_files"]) == 2


def test_context_modelling_phase_generates_six_files(tmp_feature: Path):
    """context_modelling → 6 ファイル生成"""
    result = scaffold_upstream("tmp_feat", "context_modelling", repo_root=tmp_feature)
    assert result["phase"] == "phase_0_5_context_modelling"
    assert len(result["generated_files"]) == 6


def test_kebab_case_phase_normalized(tmp_feature: Path):
    """context-modelling (kebab-case) も受付、内部で snake_case に正規化"""
    result = scaffold_upstream("tmp_feat", "context-modelling", repo_root=tmp_feature)
    assert result["phase"] == "phase_0_5_context_modelling"


def test_prototype_lite_mode(tmp_feature: Path):
    """prototype profile + discovery → stakeholder_map + value_canvas のみ (2 件)"""
    result = scaffold_upstream("tmp_feat", "discovery", profile="prototype", repo_root=tmp_feature)
    assert result["profile"] == "prototype"
    assert len(result["generated_files"]) == 2
    names = [Path(p).name for p in result["generated_files"]]
    assert sorted(names) == ["stakeholder_map.yaml", "value_canvas.yaml"]


def test_existing_artifact_skipped_not_overwritten(tmp_feature: Path):
    """既存ファイルがある場合は skip + warn、上書きしない"""
    result1 = scaffold_upstream("tmp_feat", "discovery", repo_root=tmp_feature)
    assert len(result1["generated_files"]) == 7
    result2 = scaffold_upstream("tmp_feat", "discovery", repo_root=tmp_feature)
    assert len(result2["generated_files"]) == 0
    assert len(result2["skipped_files"]) == 7


def test_invalid_phase_raises(tmp_feature: Path):
    with pytest.raises(ValueError):
        scaffold_upstream("tmp_feat", "invalid_phase", repo_root=tmp_feature)


def test_missing_feature_raises(tmp_feature: Path):
    with pytest.raises(FileNotFoundError):
        scaffold_upstream("nonexistent_feature", "discovery", repo_root=tmp_feature)


def test_valid_phases_set():
    """Public constants are stable"""
    assert VALID_PHASES == {"discovery", "elicit", "context_modelling", "context-modelling"}
    assert VALID_PROFILES == {"enterprise-erp", "saas-integration", "prototype"}
