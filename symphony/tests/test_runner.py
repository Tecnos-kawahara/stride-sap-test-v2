"""Tests for symphony.runner."""
from __future__ import annotations

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from symphony.config import AgentConfig, ClaudeCodeAgentConfig, CodexAgentConfig, SymphonyConfig
from symphony.runner import AgentResult, run_agent


def _make_config(
    claude_timeout_ms: int = 60_000,
    claude_model: str | None = None,
    claude_effort_level: str | None = None,
    claude_max_output_tokens: int | None = None,
    codex_timeout_ms: int = 60_000,
) -> SymphonyConfig:
    config = SymphonyConfig()
    config.agent.claude_code = ClaudeCodeAgentConfig(
        timeout_ms=claude_timeout_ms,
        model=claude_model,
        effort_level=claude_effort_level,
        max_output_tokens=claude_max_output_tokens,
    )
    config.agent.codex = CodexAgentConfig(timeout_ms=codex_timeout_ms)
    return config


class TestRunAgentClaude:
    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_claude_command_construction(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        config = _make_config()

        run_agent("claude-code", config, "/ws/42", "do stuff", "/logs/test.log")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == ["claude", "-p", "--dangerously-skip-permissions"]
        assert call_args[1]["cwd"] == "/ws/42"
        assert call_args[1]["input"] == "do stuff"
        assert "CLAUDE_CODE_MAX_OUTPUT_TOKENS" not in call_args[1]["env"]

    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_claude_timeout_converted_to_seconds(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        config = _make_config(claude_timeout_ms=120_000)

        run_agent("claude-code", config, "/ws", "prompt", "/log.log")
        assert mock_run.call_args[1]["timeout"] == 120.0

    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_claude_appends_model_and_effort_flags(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        config = _make_config(
            claude_model="claude-opus-4-7",
            claude_effort_level="xhigh",
        )

        run_agent("claude-code", config, "/ws", "prompt", "/log.log")

        cmd = mock_run.call_args[0][0]
        assert cmd == [
            "claude",
            "-p",
            "--dangerously-skip-permissions",
            "--model",
            "claude-opus-4-7",
            "--effort",
            "xhigh",
        ]

    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_claude_sets_max_output_tokens_env(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        config = _make_config(claude_max_output_tokens=65_536)

        run_agent("claude-code", config, "/ws", "prompt", "/log.log")

        env = mock_run.call_args[1]["env"]
        assert env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] == "65536"
        assert env["PATH"] == os.environ["PATH"]


class TestRunAgentCodex:
    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_codex_command_construction(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        config = _make_config()

        run_agent("codex", config, "/ws/42", "do stuff", "/logs/test.log")

        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert cmd == ["codex", "exec", "--full-auto", "-C", "/ws/42", "do stuff"]

    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_codex_no_input(self, mock_makedirs, mock_run):
        """Codex uses positional arg, not stdin input."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        config = _make_config()

        run_agent("codex", config, "/ws", "prompt", "/log.log")
        # No 'input' key for codex
        assert "input" not in mock_run.call_args[1]


class TestTimeout:
    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_timeout_returns_timed_out_result(self, mock_makedirs, mock_run):
        exc = subprocess.TimeoutExpired(cmd=["claude"], timeout=60)
        exc.stdout = b"partial"
        exc.stderr = b"err"
        mock_run.side_effect = exc
        config = _make_config()

        result = run_agent("claude-code", config, "/ws", "prompt", "/log.log")

        assert result.timed_out is True
        assert result.returncode == -1
        assert "partial" in result.stdout
        assert "err" in result.stderr


class TestLogWriting:
    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_log_file_written(self, mock_makedirs, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout="hello stdout", stderr="hello stderr")
        config = _make_config()
        log_path = str(tmp_path / "test.log")

        run_agent("claude-code", config, "/ws", "prompt", log_path)

        log_content = (tmp_path / "test.log").read_text()
        assert "=== STDOUT ===" in log_content
        assert "hello stdout" in log_content
        assert "=== STDERR ===" in log_content
        assert "hello stderr" in log_content


class TestCustomCommand:
    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_claude_uses_config_command_and_args(self, mock_makedirs, mock_run):
        """Command and args should come from config, not hardcoded."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        config = SymphonyConfig()
        config.agent.claude_code = ClaudeCodeAgentConfig(
            command="/usr/local/bin/claude",
            args=["-p", "--verbose"],
            model="claude-opus-4-7",
            effort_level="high",
            timeout_ms=60_000,
        )

        run_agent("claude-code", config, "/ws", "prompt", "/log.log")
        cmd = mock_run.call_args[0][0]
        assert cmd == [
            "/usr/local/bin/claude",
            "-p",
            "--verbose",
            "--model",
            "claude-opus-4-7",
            "--effort",
            "high",
        ]

    @patch("symphony.runner.subprocess.run")
    @patch("symphony.runner.os.makedirs")
    def test_codex_uses_config_command_and_args(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        config = SymphonyConfig()
        config.agent.codex = CodexAgentConfig(
            command="openai-codex",
            subcommand="run",
            args=["--sandbox"],
            timeout_ms=60_000,
        )

        run_agent("codex", config, "/ws/42", "prompt", "/log.log")
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "openai-codex"
        assert cmd[1] == "run"
        assert "--sandbox" in cmd


class TestUnknownEngine:
    @patch("symphony.runner.os.makedirs")
    def test_unknown_engine_raises(self, mock_makedirs):
        config = _make_config()
        with pytest.raises(ValueError, match="Unknown engine"):
            run_agent("unknown", config, "/ws", "prompt", "/log.log")
