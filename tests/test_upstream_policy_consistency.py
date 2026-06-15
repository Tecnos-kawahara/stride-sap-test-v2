"""Test: Upstream policy consistency (FEAT-VALA01 Phase A).

Verifies shared/policies/upstream_policy.yaml profile_applicability matches
shared/policies/profile_policy.yaml profiles, each phase artifacts.template
exists in sdd-templates/templates/upstream/, and policy refs (iteration_policy /
baccm_completeness) point at real files.

Covers AC-US-FEATVALA01-001-02 (schema/policy 整合) per spec.md.
"""
from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_POLICY = REPO_ROOT / "shared" / "policies" / "upstream_policy.yaml"
PROFILE_POLICY = REPO_ROOT / "shared" / "policies" / "profile_policy.yaml"
ITERATION_POLICY = REPO_ROOT / "shared" / "policies" / "upstream_iteration_policy.yaml"
BACCM_POLICY = REPO_ROOT / "shared" / "policies" / "baccm_completeness.yaml"
UPSTREAM_DIR = REPO_ROOT / "sdd-templates" / "templates" / "upstream"

EXPECTED_PHASES = {"phase_0_discovery", "phase_0_3_elicit", "phase_0_5_context_modelling"}


def test_all_referenced_files_exist():
    for p in [UPSTREAM_POLICY, PROFILE_POLICY, ITERATION_POLICY, BACCM_POLICY]:
        assert p.is_file(), f"政策ファイル不存在: {p}"


def test_profile_applicability_keys_match_profile_policy():
    """upstream_policy.profile_applicability の key 集合が profile_policy.profiles と完全一致"""
    upstream = yaml.safe_load(UPSTREAM_POLICY.read_text(encoding="utf-8"))
    profile_pol = yaml.safe_load(PROFILE_POLICY.read_text(encoding="utf-8"))

    upstream_keys = set(upstream["profile_applicability"].keys())
    profile_keys = set(profile_pol["profiles"].keys())

    assert upstream_keys == profile_keys, (
        f"profile_applicability ↔ profile_policy.profiles 不整合\n"
        f"  upstream_policy:   {sorted(upstream_keys)}\n"
        f"  profile_policy:    {sorted(profile_keys)}"
    )


def test_phases_complete():
    """upstream_policy.phases は 3 つの Phase をすべて含む"""
    upstream = yaml.safe_load(UPSTREAM_POLICY.read_text(encoding="utf-8"))
    phases = set(upstream["phases"].keys())
    assert phases == EXPECTED_PHASES, (
        f"phases 集合が期待値と一致しない\n"
        f"  expected: {sorted(EXPECTED_PHASES)}\n"
        f"  actual:   {sorted(phases)}"
    )


def test_each_phase_artifact_template_exists():
    """各 phase の artifacts[].template が sdd-templates/templates/upstream/ に実在"""
    upstream = yaml.safe_load(UPSTREAM_POLICY.read_text(encoding="utf-8"))
    for phase_name, phase_def in upstream["phases"].items():
        for art in phase_def["artifacts"]:
            tpl = art["template"]
            tpl_path = UPSTREAM_DIR / tpl
            assert tpl_path.is_file(), (
                f"{phase_name}: 参照テンプレート不存在 {tpl_path}"
            )


def test_artifact_template_pairs_count():
    """合計 15 (Phase 0=7 + Phase 0.3=2 + Phase 0.5=6)"""
    upstream = yaml.safe_load(UPSTREAM_POLICY.read_text(encoding="utf-8"))
    counts = {phase: len(defn["artifacts"]) for phase, defn in upstream["phases"].items()}
    assert counts["phase_0_discovery"] == 7, (
        f"phase_0_discovery artifacts 件数不一致: {counts['phase_0_discovery']} != 7"
    )
    assert counts["phase_0_3_elicit"] == 2, (
        f"phase_0_3_elicit artifacts 件数不一致: {counts['phase_0_3_elicit']} != 2"
    )
    assert counts["phase_0_5_context_modelling"] == 6, (
        f"phase_0_5_context_modelling artifacts 件数不一致: {counts['phase_0_5_context_modelling']} != 6"
    )
    total = sum(counts.values())
    assert total == 15, f"artifact 合計件数 {total} != 15"


def test_iteration_policy_ref_resolves():
    upstream = yaml.safe_load(UPSTREAM_POLICY.read_text(encoding="utf-8"))
    ref_path = REPO_ROOT / upstream["iteration_policy_ref"]
    assert ref_path.is_file(), f"iteration_policy_ref パス不存在: {ref_path}"


def test_baccm_completeness_ref_resolves():
    upstream = yaml.safe_load(UPSTREAM_POLICY.read_text(encoding="utf-8"))
    ref_path = REPO_ROOT / upstream["baccm_completeness_ref"]
    assert ref_path.is_file(), f"baccm_completeness_ref パス不存在: {ref_path}"


def test_iteration_policy_max_iterations_is_3():
    """upstream_iteration_policy.iteration_pattern.loop_bound.max_iterations == 3"""
    iter_pol = yaml.safe_load(ITERATION_POLICY.read_text(encoding="utf-8"))
    bound = iter_pol["iteration_pattern"]["loop_bound"]["max_iterations"]
    assert bound == 3, f"max_iterations == 3 必須 (現値: {bound})"
