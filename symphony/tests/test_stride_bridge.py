"""Tests for symphony.stride_bridge."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from symphony.stride_bridge import (
    ToolResult,
    _run,
    auto_continue,
    is_approval_pending,
    is_all_gates_passed,
    lint,
    pr_check,
    run_report,
    wi_readiness,
    wi_sync,
)


class TestLint:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_calls_correct_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        result = lint("specs/order_import", cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == ["sdd-templates/tools/stride-lint", "specs/order_import"]
        assert call_args[1]["cwd"] == "/project"

    @patch("symphony.stride_bridge.subprocess.run")
    def test_returns_tool_result(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="all good", stderr="")
        result = lint("specs/my_feature")
        assert isinstance(result, ToolResult)
        assert result.exit_code == 0
        assert result.stdout == "all good"


class TestWiSync:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_calls_correct_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        wi_sync("order_import", cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == [
            "python3", "sdd-templates/tools/stride_wi_sync.py",
            "--feature", "order_import",
        ]
        assert call_args[1]["cwd"] == "/project"


class TestPrCheck:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_calls_correct_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        pr_check("/project/root", cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == [
            "sdd-templates/bin/stride", "pr-check", "/project/root",
        ]
        assert call_args[1]["cwd"] == "/project"


class TestRunReport:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_calls_positional_run_dir(self, mock_run):
        """run_report must use positional run_dir, not --run-dir flag."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_report("/ws/42", issue_number=42, cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd[0:3] == [
            "python3", "sdd-templates/tools/run_report_generator.py",
            "/ws/42",
        ]
        # Must NOT have --run-dir flag
        assert "--run-dir" not in cmd
        assert "--post" in cmd
        assert "--issue" in cmd

    @patch("symphony.stride_bridge.subprocess.run")
    def test_project_fields_flag(self, mock_run):
        """When project is provided, --project-fields and --project flags must be set."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_report("/ws/42", issue_number=42, project=5, owner="org", cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "--project-fields" in cmd
        assert "--project" in cmd
        assert "--owner" in cmd


class TestWiReadiness:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_calls_positional_args(self, mock_run):
        """wi_readiness must use positional args, not --feature-path/--wi flags."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        wi_readiness("specs/order_import", "WI-001", cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == [
            "python3", "sdd-templates/tools/wi_readiness_checker.py",
            "specs/order_import",
            "WI-001",
        ]
        # Must NOT have --feature-path or --wi flags
        assert "--feature-path" not in cmd
        assert "--wi" not in cmd


class TestApprovalPendingDetection:
    def test_approval_pending_in_stdout(self):
        result = ToolResult(exit_code=1, stdout="APPROVAL_PENDING: Gate 3", stderr="")
        assert is_approval_pending(result) is True

    def test_approval_pending_in_stderr(self):
        result = ToolResult(exit_code=1, stdout="", stderr="APPROVAL_PENDING found")
        assert is_approval_pending(result) is True

    def test_no_approval_pending(self):
        result = ToolResult(exit_code=0, stdout="ALL_GATES_PASSED", stderr="")
        assert is_approval_pending(result) is False


class TestAllGatesPassed:
    def test_explicit_marker(self):
        result = ToolResult(exit_code=0, stdout="ALL_GATES_PASSED", stderr="")
        assert is_all_gates_passed(result) is True

    def test_clean_exit_no_fail(self):
        result = ToolResult(exit_code=0, stdout="Everything looks good", stderr="")
        assert is_all_gates_passed(result) is True

    def test_fail_in_output(self):
        result = ToolResult(exit_code=0, stdout="FAIL: Gate 2 not passed", stderr="")
        assert is_all_gates_passed(result) is False


# ---------------------------------------------------------------------------
# Error paths in _run
# ---------------------------------------------------------------------------


class TestRunTimeout:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_timeout_returns_exit_code_minus_one(self, mock_run):
        import subprocess as sp
        mock_run.side_effect = sp.TimeoutExpired(cmd=["some", "cmd"], timeout=120)
        result = _run(["some", "cmd"], cwd="/project")
        assert result.exit_code == -1
        assert "[TIMEOUT]" in result.stderr


class TestRunFileNotFound:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_file_not_found_returns_exit_code_minus_two(self, mock_run):
        mock_run.side_effect = FileNotFoundError("No such file or directory: 'bad-cmd'")
        result = _run(["bad-cmd"], cwd="/project")
        assert result.exit_code == -2
        assert "bad-cmd" in result.stderr


class TestAutoContinue:
    @patch("symphony.stride_bridge.subprocess.run")
    def test_calls_correct_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="OK", stderr="")
        result = auto_continue("specs/my_feature", cwd="/project")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == ["sdd-templates/bin/stride", "auto-continue", "specs/my_feature"]
        assert call_args[1]["cwd"] == "/project"
        assert result.exit_code == 0
