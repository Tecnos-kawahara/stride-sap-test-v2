"""Test: BACCM 6-axis completeness policy integrity (FEAT-VALA01 Phase A).

Verifies shared/policies/baccm_completeness.yaml declares the 6 BACCM axes
(Change / Need / Solution / Stakeholder / Value / Context) with proper
source_artifacts that reference real templates under
sdd-templates/templates/upstream/.

Covers AC-US-FEATVALA01-001-06 (BACCM axes structure) per spec.md.
"""
from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
POLICY_PATH = REPO_ROOT / "shared" / "policies" / "baccm_completeness.yaml"
UPSTREAM_DIR = REPO_ROOT / "sdd-templates" / "templates" / "upstream"

EXPECTED_AXES = {"change", "need", "solution", "stakeholder", "value", "context"}


def _load_policy():
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))


def test_policy_file_exists():
    assert POLICY_PATH.is_file(), f"baccm_completeness.yaml 不存在: {POLICY_PATH}"


def test_baccm_has_exactly_6_axes():
    data = _load_policy()
    axes = data.get("baccm_axes")
    assert isinstance(axes, dict), "baccm_axes は map 必須"
    actual = set(axes.keys())
    assert actual == EXPECTED_AXES, (
        f"BACCM axes 集合が完全一致しない\n"
        f"  expected: {sorted(EXPECTED_AXES)}\n"
        f"  actual:   {sorted(actual)}"
    )


def test_each_axis_has_source_artifacts():
    data = _load_policy()
    for axis, defn in data["baccm_axes"].items():
        sources = defn.get("source_artifacts")
        assert isinstance(sources, list) and sources, (
            f"{axis}: source_artifacts は非空リスト必須"
        )
        for src in sources:
            assert "artifact" in src, f"{axis}: source_artifact に artifact キー必須"
            assert "template" in src, f"{axis}: source_artifact に template キー必須"


def test_all_referenced_templates_exist():
    """各軸の source_artifacts.template が sdd-templates/templates/upstream/ に実在"""
    data = _load_policy()
    for axis, defn in data["baccm_axes"].items():
        for src in defn["source_artifacts"]:
            tpl = src["template"]
            tpl_path = UPSTREAM_DIR / tpl
            assert tpl_path.is_file(), (
                f"{axis}: 参照テンプレート不存在 {tpl_path}"
            )


def test_completeness_threshold_is_100():
    data = _load_policy()
    scoring = data.get("completeness_scoring", {})
    threshold = scoring.get("threshold_for_gate_0")
    assert threshold == 100, (
        f"threshold_for_gate_0 == 100 必須 (現値: {threshold})"
    )
    assert scoring.get("partial_credit_allowed") is False, (
        "partial_credit_allowed は False 必須 (BACCM 6 軸は all-pass 要)"
    )


def test_attributions_present():
    data = _load_policy()
    attrs = data.get("attributions")
    assert isinstance(attrs, list) and attrs, "attributions: 行が必須 (fair-use 表明)"
    sources = [a.get("source", "") for a in attrs]
    assert any("BABOK v3" in s for s in sources), (
        "attributions に BABOK v3 (IIBA) 由来の記述が必要"
    )
