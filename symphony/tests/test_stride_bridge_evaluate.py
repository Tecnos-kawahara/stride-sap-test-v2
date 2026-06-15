"""Unit tests for stride_bridge evaluate() function."""

from __future__ import annotations

from unittest import mock

import pytest

from symphony.stride_bridge import (
    ToolResult,
    evaluate,
    is_evaluation_failed,
    is_evaluation_passed,
)


# === Test 1: is_evaluation_passed returns True for exit_code=0 ===
def test_evaluation_passed():
    result = ToolResult(exit_code=0, stdout="PASS", stderr="")
    assert is_evaluation_passed(result) is True


# === Test 2: is_evaluation_failed returns True for exit_code=1 ===
def test_evaluation_failed():
    result = ToolResult(exit_code=1, stdout="FAIL", stderr="")
    assert is_evaluation_failed(result) is True


# === Test 3: evaluate() passes --allow-provider-degraded when requested ===
@mock.patch("symphony.stride_bridge.subprocess.run")
def test_evaluate_allow_degraded_flag(mock_run):
    mock_run.return_value = mock.Mock(returncode=0, stdout="ok", stderr="")
    evaluate("specs/test-feature/", phase="specify", allow_degraded=True)
    cmd = mock_run.call_args[0][0]
    assert "--allow-provider-degraded" in cmd
    assert "--phase" in cmd
    idx = cmd.index("--phase")
    assert cmd[idx + 1] == "specify"
