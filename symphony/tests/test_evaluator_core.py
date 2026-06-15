"""Unit tests for multi_model_evaluator.py core logic (no API calls)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Add tools dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sdd-templates" / "tools"))
from multi_model_evaluator import (
    aggregate_results,
    build_compact_packet,
    build_design_prompt,
    build_specify_prompt,
    build_tasking_prompt,
    extract_canonical_yaml,
    is_hard_fail,
    load_env_local,
    parse_model_response,
    should_skip_evaluation,
)


@pytest.fixture
def tmp_feature(tmp_path):
    """Create a minimal feature directory for tests."""
    feature = tmp_path / "specs" / "FEAT-TEST"
    feature.mkdir(parents=True)

    # basic_design.md
    (feature / "basic_design.md").write_text(
        "# Basic Design\n"
        "# 0. Canonical Basic Design (YAML)\n"
        "```yaml\n"
        "basic_design:\n"
        "  feature_id: FEAT-TEST\n"
        "  coverage_tier: standard\n"
        "  scope:\n"
        "    in: [order management]\n"
        "```\n"
        "# End\n",
        encoding="utf-8",
    )

    # process.bpmn
    (feature / "process.bpmn").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">\n'
        '  <process id="p1">\n'
        '    <userTask id="t1" name="Check Order" />\n'
        '    <serviceTask id="t2" name="Post to SAP" />\n'
        '    <exclusiveGateway id="g1" name="Approved?" />\n'
        '  </process>\n'
        '</definitions>\n',
        encoding="utf-8",
    )

    # spec.md
    (feature / "spec.md").write_text(
        "# Spec\n"
        "# 0. Canonical Spec (YAML)\n"
        "```yaml\n"
        "spec:\n"
        "  use_cases:\n"
        "    - id: US-FEATTEST-001\n"
        "```\n",
        encoding="utf-8",
    )

    # plan.md (mirrors real structure: plan.test_strategy.coverage_policy / tests)
    (feature / "plan.md").write_text(
        "# Plan\n"
        "# 0. Canonical Plan (YAML)\n"
        "```yaml\n"
        "plan:\n"
        "  test_strategy:\n"
        "    coverage_policy:\n"
        "      acceptance_coverage_required: true\n"
        "    tests:\n"
        "      - id: TS-CON-01\n"
        "```\n",
        encoding="utf-8",
    )

    # tasks.md (mirrors real structure: tasks.tasks, not tasks.task_list)
    (feature / "tasks.md").write_text(
        "# Tasks\n"
        "# 1. Canonical Tasks (YAML)\n"
        "```yaml\n"
        "tasks:\n"
        "  tasks:\n"
        "    - id: T-TE-001\n"
        "      spec_refs: [AC-US-FEATTEST-001-01]\n"
        "```\n",
        encoding="utf-8",
    )

    # tests/scenarios.yaml
    tests_dir = feature / "tests"
    tests_dir.mkdir()
    (tests_dir / "scenarios.yaml").write_text(
        "scenarios:\n  - id: SC-01\n    ac_refs: [AC-US-FEATTEST-001-01]\n",
        encoding="utf-8",
    )

    # contracts/
    contracts_dir = feature / "contracts"
    contracts_dir.mkdir()
    (contracts_dir / "api.yaml").write_text("openapi: 3.0.0\n", encoding="utf-8")

    return feature


# === Test 1: load_env_local reads from .env.local ===
def test_load_env_local_reads_vars(tmp_path):
    env_file = tmp_path / ".env.local"
    env_file.write_text("TEST_KEY_ABC=hello_world\n", encoding="utf-8")
    # Clear any prior value
    os.environ.pop("TEST_KEY_ABC", None)
    load_env_local(tmp_path)
    assert os.environ.get("TEST_KEY_ABC") == "hello_world"
    os.environ.pop("TEST_KEY_ABC", None)


# === Test 2: load_env_local no error when file missing ===
def test_load_env_local_missing_file(tmp_path):
    load_env_local(tmp_path / "nonexistent")  # Should not raise


# === Test 3: extract_canonical_yaml with valid marker ===
def test_extract_canonical_yaml_valid(tmp_feature):
    result = extract_canonical_yaml(tmp_feature / "basic_design.md", "Canonical Basic Design")
    assert result is not None
    assert "feature_id: FEAT-TEST" in result


# === Test 4: extract_canonical_yaml with missing marker ===
def test_extract_canonical_yaml_missing_marker(tmp_feature):
    result = extract_canonical_yaml(tmp_feature / "basic_design.md", "Nonexistent Marker")
    assert result is None


# === Test 5: build_compact_packet design phase ===
def test_build_compact_packet_design(tmp_feature):
    packet = build_compact_packet(tmp_feature, "design")
    assert "feature_id: FEAT-TEST" in packet
    assert "userTask" in packet or "Check Order" in packet


# === Test 6: build_compact_packet specify phase ===
def test_build_compact_packet_specify(tmp_feature):
    packet = build_compact_packet(tmp_feature, "specify")
    assert "use_cases" in packet
    assert "coverage_policy" in packet or "Canonical Plan" in packet
    assert "scenarios" in packet
    assert "api.yaml" in packet


# === Test 7: build_compact_packet tasking phase (real YAML structure) ===
def test_build_compact_packet_tasking(tmp_feature):
    packet = build_compact_packet(tmp_feature, "tasking")
    assert "T-TE-001" in packet
    assert "AC-US-FEATTEST-001-01" in packet
    # Verify plan coverage summary is extracted from test_strategy path
    assert "coverage_policy" in packet
    assert "acceptance_coverage_required" in packet


# === Test 8: aggregate_results — primary PASS ===
def test_aggregate_primary_pass():
    primary = {
        "overall": "PASS",
        "weighted_score": 85,
        "scores": {"a": 90, "b": 80},
        "critical_issues": [],
    }
    result = aggregate_results(primary, None)
    assert result["exit_code"] == 0
    assert result["overall"] == "PASS"


# === Test 9: aggregate_results — primary clear FAIL ===
def test_aggregate_primary_clear_fail():
    primary = {
        "overall": "FAIL",
        "weighted_score": 45,
        "scores": {"a": 60, "b": 30},
        "critical_issues": [
            {"severity": "critical", "criterion": "a", "description": "bad", "ref": "AC-1"},
            {"severity": "critical", "criterion": "b", "description": "worse", "ref": "AC-2"},
        ],
    }
    result = aggregate_results(primary, {"overall": "PASS", "weighted_score": 90, "scores": {"a": 90, "b": 90}, "critical_issues": []})
    assert result["exit_code"] == 1
    assert result["overall"] == "FAIL"


# === Test 10: aggregate_results — borderline + secondary PASS → WARN ===
def test_aggregate_borderline_secondary_pass():
    primary = {
        "overall": "FAIL",
        "weighted_score": 65,
        "scores": {"a": 70, "b": 60},
        "critical_issues": [{"severity": "critical", "criterion": "a", "description": "x", "ref": "r"}],
    }
    secondary = {
        "overall": "PASS",
        "weighted_score": 80,
        "scores": {"a": 80, "b": 80},
        "critical_issues": [],
    }
    result = aggregate_results(primary, secondary)
    assert result["exit_code"] == 0
    assert result["overall"] == "WARN"


# === Test 11: aggregate_results — hard floor violation (criterion < 50) → FAIL ===
def test_aggregate_hard_floor_violation():
    primary = {
        "overall": "PASS",
        "weighted_score": 75,
        "scores": {"a": 90, "b": 45},  # b < 50 → hard floor
        "critical_issues": [],
    }
    result = aggregate_results(primary, None)
    assert result["exit_code"] == 1
    assert result["overall"] == "FAIL"
    assert "hard floor" in result.get("reason", "").lower()


# === Test 12: should_skip_evaluation — starter tier ===
def test_should_skip_starter(tmp_path):
    feature = tmp_path / "specs" / "FEAT-SKIP"
    feature.mkdir(parents=True)
    (feature / "basic_design.md").write_text(
        "# BD\n# 0. Canonical Basic Design (YAML)\n```yaml\n"
        "basic_design:\n  coverage_tier: starter\n```\n",
        encoding="utf-8",
    )
    assert should_skip_evaluation(feature) is True


# === Test 13: should_skip_evaluation — critical tier ===
def test_should_skip_critical(tmp_path):
    feature = tmp_path / "specs" / "FEAT-CRIT"
    feature.mkdir(parents=True)
    (feature / "basic_design.md").write_text(
        "# BD\n# 0. Canonical Basic Design (YAML)\n```yaml\n"
        "basic_design:\n  coverage_tier: critical\n```\n",
        encoding="utf-8",
    )
    assert should_skip_evaluation(feature) is False


# === Test 14: starter skip works without API keys (main() order test) ===
def test_starter_skip_without_api_keys(tmp_path, monkeypatch):
    """coverage_tier=starter should SKIP (exit 0) even when API keys are absent."""
    feature = tmp_path / "specs" / "FEAT-STARTER"
    feature.mkdir(parents=True)
    (feature / "basic_design.md").write_text(
        "# BD\n# 0. Canonical Basic Design (YAML)\n```yaml\n"
        "basic_design:\n  coverage_tier: starter\n```\n",
        encoding="utf-8",
    )
    # Ensure no API keys
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "multi_model_evaluator", str(feature), "--phase", "design"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent / "sdd-templates" / "tools"),
        env={**os.environ, "OPENAI_API_KEY": "", "OPENAI_MODEL": ""},
    )
    assert result.returncode == 0, f"Expected exit 0 (SKIP), got {result.returncode}: {result.stdout} {result.stderr}"
    assert "SKIP" in result.stdout
