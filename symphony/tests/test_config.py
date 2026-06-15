"""Tests for symphony.config."""
from __future__ import annotations

import os
import time

import pytest

from symphony.config import ConfigLoader, RetryConfig, SymphonyConfig, _split_frontmatter


class TestConfigLoaderParsing:
    """Test successful SYMPHONY.md parsing."""

    def test_parses_config(self, tmp_symphony_md):
        loader = ConfigLoader(tmp_symphony_md)
        config = loader.config
        assert isinstance(config, SymphonyConfig)
        assert config.version == "1.0"
        assert config.tracker.repo == "owner/repo"
        assert config.tracker.trigger_label == "symphony:ready"
        assert config.polling.interval_seconds == 30
        assert config.polling.max_issues_per_cycle == 3
        assert config.workspace.root == ".symphony/workspaces"
        assert config.agent.max_parallel == 4

    def test_parses_prompt_template(self, tmp_symphony_md):
        loader = ConfigLoader(tmp_symphony_md)
        template = loader.prompt_template
        assert "{{ feature_name }}" in template
        assert "{{ phase }}" in template

    def test_parses_routing(self, tmp_symphony_md):
        loader = ConfigLoader(tmp_symphony_md)
        config = loader.config
        assert "design" in config.agent.routing
        assert config.agent.routing["design"].engine == "claude-code"
        assert "execute" in config.agent.routing
        assert config.agent.routing["execute"].engine == "codex"

    def test_parses_agent_timeouts(self, tmp_symphony_md):
        loader = ConfigLoader(tmp_symphony_md)
        config = loader.config
        assert config.agent.claude_code.timeout_ms == 600_000
        assert config.agent.codex.timeout_ms == 300_000

    def test_parses_label_names(self, tmp_symphony_md):
        loader = ConfigLoader(tmp_symphony_md)
        config = loader.config
        assert config.tracker.running_label == "symphony:running"
        assert config.tracker.failed_label == "symphony:failed"
        assert config.tracker.done_label == "symphony:done"
        assert config.tracker.blocked_label == "symphony:blocked"

    def test_parses_retry_config(self, tmp_symphony_md):
        loader = ConfigLoader(tmp_symphony_md)
        config = loader.config
        assert isinstance(config.agent.retry, RetryConfig)
        assert config.agent.retry.max_attempts == 3
        assert config.agent.retry.backoff_base_ms == 10_000
        assert config.agent.retry.backoff_max_ms == 300_000

    def test_parses_agent_command_and_args(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "agent:\n  claude_code:\n    command: /opt/claude\n"
            "    args: [\"-p\", \"--verbose\"]\n"
            "    model: claude-opus-4-7\n"
            "    effort_level: xhigh\n"
            "    max_output_tokens: 65536\n"
            "    timeout_ms: 120000\n"
            "---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        config = loader.config
        assert config.agent.claude_code.command == "/opt/claude"
        assert config.agent.claude_code.args == ["-p", "--verbose"]
        assert config.agent.claude_code.model == "claude-opus-4-7"
        assert config.agent.claude_code.effort_level == "xhigh"
        assert config.agent.claude_code.max_output_tokens == 65_536
        assert config.agent.claude_code.timeout_ms == 120_000


class TestConfigValidation:
    def test_placeholder_repo_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: '{{GITHUB_REPO}}'\n---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="placeholder"):
            _ = loader.config

    def test_stride_board_enabled_without_project_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "observability:\n  stride_board:\n    enabled: true\n---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="stride_board"):
            _ = loader.config

    def test_stride_board_disabled_without_project_ok(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "observability:\n  stride_board:\n    enabled: false\n---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        config = loader.config
        assert config.observability.stride_board.enabled is False
        assert config.observability.stride_board.project is None

    def test_invalid_claude_effort_level_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "agent:\n  claude_code:\n    effort_level: turbo\n"
            "---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="effort_level"):
            _ = loader.config

    def test_non_positive_max_output_tokens_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "agent:\n  claude_code:\n    max_output_tokens: 0\n"
            "---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="max_output_tokens"):
            _ = loader.config


# ---------------------------------------------------------------------------
# Regression: P2-b — deep validation (engine whitelist + Jinja syntax)
# ---------------------------------------------------------------------------

class TestEngineWhitelist:
    """Invalid engine names in routing must be caught at validate time."""

    def test_invalid_routing_engine_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "agent:\n  routing:\n    design:\n      engine: gpt-4\n"
            "---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="not a valid engine"):
            _ = loader.config

    def test_valid_engines_pass(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "agent:\n  routing:\n    design:\n      engine: claude-code\n"
            "    execute:\n      engine: codex\n"
            "---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        config = loader.config
        assert config.agent.routing["design"].engine == "claude-code"
        assert config.agent.routing["execute"].engine == "codex"

    def test_invalid_complexity_override_engine_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n"
            "agent:\n  complexity_override:\n    enabled: true\n"
            "    high_complexity_engine: gemini\n"
            "    low_complexity_engine: codex\n"
            "---\nPrompt\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="not a valid engine"):
            _ = loader.config


class TestJinjaValidation:
    """Invalid Jinja2 syntax in prompt template must be caught at validate time."""

    def test_invalid_jinja_syntax_raises(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n---\n"
            "{{ unclosed_variable\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        with pytest.raises(ValueError, match="invalid Jinja2 syntax"):
            _ = loader.config

    def test_valid_jinja_passes(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n---\n"
            "Hello {{ feature_name }}! {% if phase %}Phase: {{ phase }}{% endif %}\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        config = loader.config
        assert config.tracker.repo == "owner/repo"

    def test_empty_prompt_passes(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\n---\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        config = loader.config
        assert config.tracker.repo == "owner/repo"


class TestConfigHotReload:
    def test_mtime_change_triggers_reload(self, tmp_path):
        md = tmp_path / "SYMPHONY.md"
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\npolling:\n  interval_seconds: 30\n---\nPromptV1\n",
            encoding="utf-8",
        )
        loader = ConfigLoader(md)
        assert loader.config.polling.interval_seconds == 30
        assert "PromptV1" in loader.prompt_template

        # Simulate mtime change
        time.sleep(0.05)
        md.write_text(
            "---\ntracker:\n  repo: owner/repo\npolling:\n  interval_seconds: 90\n---\nPromptV2\n",
            encoding="utf-8",
        )
        # Force mtime to differ (some filesystems have coarse granularity)
        new_mtime = os.path.getmtime(str(md)) + 1
        os.utime(str(md), (new_mtime, new_mtime))

        assert loader.config.polling.interval_seconds == 90
        assert "PromptV2" in loader.prompt_template


class TestSplitFrontmatter:
    def test_missing_opening_raises(self):
        with pytest.raises(ValueError, match="YAML front-matter"):
            _split_frontmatter("no frontmatter here")

    def test_missing_closing_raises(self):
        with pytest.raises(ValueError, match="closing ---"):
            _split_frontmatter("---\nkey: val\n")
