"""Live API tests for multi_model_evaluator.py.

These tests call real APIs and require:
  - .env.local with OPENAI_API_KEY and OPENAI_MODEL set
  - openai and google-genai packages installed

Run:  pytest -m api symphony/tests/test_evaluator_live.py -v
Skip: pytest -m "not api" (default for CI)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "sdd-templates" / "tools"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURE_DIR = PROJECT_ROOT / "specs" / "FEAT-ERPSAMPLE"


def _skip_if_no_api_config():
    """OPENAI_API_KEY と OPENAI_MODEL の両方が必要。"""
    env_local = PROJECT_ROOT / ".env.local"
    if not env_local.exists():
        pytest.skip("No .env.local found")
    content = env_local.read_text()
    has_key = any(
        line.startswith("OPENAI_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
        for line in content.splitlines()
    )
    has_model = any(
        line.startswith("OPENAI_MODEL=") and len(line.split("=", 1)[1].strip()) > 0
        for line in content.splitlines()
    )
    if not (has_key and has_model):
        pytest.skip("OPENAI_API_KEY and/or OPENAI_MODEL not configured in .env.local")
    if not FEATURE_DIR.exists():
        pytest.skip(f"{FEATURE_DIR} not found")


@pytest.mark.api
def test_live_evaluate_design_exits_normally():
    """ライブ API で design フェーズを評価し、exit 0(PASS/WARN) or 1(FAIL) を返す。"""
    _skip_if_no_api_config()
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "multi_model_evaluator.py"),
         str(FEATURE_DIR), "--phase", "design"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
        timeout=300,
    )
    assert result.returncode in (0, 1), \
        f"Expected exit 0 or 1, got {result.returncode}:\nstdout: {result.stdout}\nstderr: {result.stderr}"


@pytest.mark.api
def test_live_evaluate_degraded_secondary_error():
    """secondary に無効な API key を渡して意図的に失敗させ、
    --allow-provider-degraded 付きでも primary の結果で正常終了すること。"""
    _skip_if_no_api_config()
    # GEMINI_MODEL が設定されていなければ secondary 自体が呼ばれないので skip
    env_local = PROJECT_ROOT / ".env.local"
    content = env_local.read_text()
    has_gemini_model = any(
        line.startswith("GEMINI_MODEL=") and len(line.split("=", 1)[1].strip()) > 0
        for line in content.splitlines()
    )
    if not has_gemini_model:
        pytest.skip("GEMINI_MODEL not configured — secondary never called, cannot test degraded path")
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = "invalid-key-for-testing"
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "multi_model_evaluator.py"),
         str(FEATURE_DIR), "--phase", "design", "--allow-provider-degraded"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
        timeout=300,
    )
    assert result.returncode in (0, 1), \
        f"Expected exit 0 or 1 with degraded mode, got {result.returncode}:\n{result.stderr}"


@pytest.mark.api
def test_live_evaluate_json_output_is_valid():
    """--format json で出力が JSON パース可能で overall/exit_code キーを持つ。"""
    _skip_if_no_api_config()
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "multi_model_evaluator.py"),
         str(FEATURE_DIR), "--phase", "design", "--format", "json"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
        timeout=300,
    )
    assert result.returncode in (0, 1), \
        f"Expected exit 0 or 1, got {result.returncode}:\n{result.stderr}"
    data = json.loads(result.stdout)
    assert data["overall"] in ("PASS", "FAIL", "WARN"), \
        f"Unexpected overall: {data['overall']}"
    assert isinstance(data["exit_code"], int)
