"""Test: multi_model_evaluator --phase discovery extension — Phase B WI-005 (TS-INT-05).

Verifies that:
- argparse choices includes 'discovery'
- build_compact_packet handles 'discovery' phase
- DISCOVERY_RUBRIC + build_discovery_prompt are exported
- existing design/specify/tasking phases are unchanged (compatibility)

Covers AC-US-FEATVALB01-001-05.
Mock-based — no real LLM API calls.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))


def test_argparse_includes_discovery_choice():
    """multi_model_evaluator.py の --phase choices に discovery が含まれる"""
    text = (REPO_ROOT / "sdd-templates" / "tools" / "multi_model_evaluator.py").read_text(
        encoding="utf-8"
    )
    assert '"discovery"' in text
    assert 'choices=["design", "specify", "tasking", "discovery"]' in text


def test_discovery_rubric_constant_defined():
    """DISCOVERY_RUBRIC 定数が定義されている"""
    import multi_model_evaluator
    assert hasattr(multi_model_evaluator, "DISCOVERY_RUBRIC")
    rubric = multi_model_evaluator.DISCOVERY_RUBRIC
    assert "{FEATURE_ID}" in rubric
    assert "{COMPACT_PACKET}" in rubric
    assert "BACCM" in rubric


def test_build_discovery_prompt_function_exists():
    import multi_model_evaluator
    assert callable(getattr(multi_model_evaluator, "build_discovery_prompt", None))


def test_build_compact_packet_discovery_branch(tmp_path: Path):
    """build_compact_packet('discovery') が upstream/ を読みに行く"""
    import multi_model_evaluator
    feature_dir = tmp_path / "specs" / "feat_discovery"
    upstream_dir = feature_dir / "upstream" / "phase_0_discovery"
    upstream_dir.mkdir(parents=True)
    (upstream_dir / "business_need.yaml").write_text(
        "problem_statement: x\nopportunity_statement: y\n", encoding="utf-8"
    )
    packet = multi_model_evaluator.build_compact_packet(feature_dir, "discovery")
    # Should contain reference to the upstream artifact
    assert "phase_0_discovery" in packet or "business_need" in packet


def test_existing_design_phase_unchanged():
    """既存 design phase のロジックは変更されていない (互換性)"""
    import multi_model_evaluator
    # 既存定数が残っている
    assert hasattr(multi_model_evaluator, "DESIGN_RUBRIC")
    assert hasattr(multi_model_evaluator, "SPECIFY_RUBRIC")
    assert hasattr(multi_model_evaluator, "TASKING_RUBRIC")
    assert hasattr(multi_model_evaluator, "DESIGN_SCORE_KEYS")
    assert hasattr(multi_model_evaluator, "SPECIFY_SCORE_KEYS")


def test_discovery_score_keys_added():
    """DISCOVERY_SCORE_KEYS が追加されている (3 軸)"""
    import multi_model_evaluator
    keys = getattr(multi_model_evaluator, "DISCOVERY_SCORE_KEYS", None)
    assert keys is not None
    assert len(keys) == 3
    assert "baccm_completeness" in keys
