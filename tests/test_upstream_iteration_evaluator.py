"""Test: upstream_iteration_evaluator.evaluate_iteration() — Phase B WI-003 (TS-INT-03).

Covers AC-US-FEATVALB01-001-01.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from upstream_iteration_evaluator import evaluate_iteration, MAX_ITERATIONS


def _touch(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("dummy: true\n", encoding="utf-8")


@pytest.fixture
def iter_feature(tmp_path: Path) -> Path:
    feature_dir = tmp_path / "specs" / "feat_iter"
    (feature_dir / "upstream").mkdir(parents=True)
    (tmp_path / "shared").mkdir()
    (tmp_path / "shared" / "policies").mkdir()
    (tmp_path / "shared" / "policies" / "upstream_iteration_policy.yaml").symlink_to(
        REPO_ROOT / "shared" / "policies" / "upstream_iteration_policy.yaml"
    )
    return tmp_path


def test_iteration_1_complete(iter_feature: Path):
    feature_dir = iter_feature / "specs" / "feat_iter"
    _touch(feature_dir / "upstream" / "phase_0_discovery" / "stakeholder_map.yaml")
    _touch(feature_dir / "upstream" / "phase_0_discovery" / "value_canvas.yaml")
    result = evaluate_iteration(feature_dir, repo_root=iter_feature)
    assert result["iteration_complete"] == 1
    assert result["iteration_details"][1]["complete"] is True
    assert result["iteration_details"][2]["complete"] is False


def test_iteration_2_complete(iter_feature: Path):
    feature_dir = iter_feature / "specs" / "feat_iter"
    base = feature_dir / "upstream" / "phase_0_discovery"
    for f in ("stakeholder_map.yaml", "value_canvas.yaml", "goal_tree.yaml", "change_strategy.yaml"):
        _touch(base / f)
    result = evaluate_iteration(feature_dir, repo_root=iter_feature)
    assert result["iteration_complete"] == 2


def test_iteration_3_complete(iter_feature: Path):
    feature_dir = iter_feature / "specs" / "feat_iter"
    discovery = feature_dir / "upstream" / "phase_0_discovery"
    context = feature_dir / "upstream" / "phase_0_5_context_modelling"
    for f in ("stakeholder_map.yaml", "value_canvas.yaml", "goal_tree.yaml", "change_strategy.yaml"):
        _touch(discovery / f)
    for f in ("condition_variation.yaml", "information_state.yaml"):
        _touch(context / f)
    result = evaluate_iteration(feature_dir, repo_root=iter_feature)
    assert result["iteration_complete"] == 3


def test_max_iterations_exceeded_returns_error(iter_feature: Path):
    """iteration_num > max_iterations → error フィールドに記録"""
    result = evaluate_iteration(
        iter_feature / "specs" / "feat_iter",
        iteration_num=4,
        repo_root=iter_feature,
    )
    assert result["error"] is not None
    assert "exceeds" in result["error"]


def test_max_iterations_constant():
    assert MAX_ITERATIONS == 3
