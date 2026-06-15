"""Tests for symphony.router."""
from __future__ import annotations

import pytest

from symphony.config import (
    AgentConfig,
    ComplexityOverride,
    PhaseRouting,
    SymphonyConfig,
)
from symphony.models import Issue
from symphony.router import select_engine


def _make_config(
    routing: dict[str, PhaseRouting] | None = None,
    complexity_override: ComplexityOverride | None = None,
) -> SymphonyConfig:
    config = SymphonyConfig()
    config.agent = AgentConfig(
        routing=routing or {},
        complexity_override=complexity_override or ComplexityOverride(),
    )
    return config


def _make_issue(body: str = "", **kwargs) -> Issue:
    defaults = dict(
        number=1, title="T", body=body, url="u",
        priority="P1", phase="design", feature_name="f", labels=[],
    )
    defaults.update(kwargs)
    return Issue(**defaults)


class TestPhaseRouting:
    def test_design_routes_to_claude_code(self):
        config = _make_config(routing={
            "design": PhaseRouting(engine="claude-code"),
            "execute": PhaseRouting(engine="codex"),
        })
        assert select_engine(config, "design") == "claude-code"

    def test_execute_routes_to_codex(self):
        config = _make_config(routing={
            "design": PhaseRouting(engine="claude-code"),
            "execute": PhaseRouting(engine="codex"),
        })
        assert select_engine(config, "execute") == "codex"

    def test_unknown_phase_falls_back_to_claude_code(self):
        config = _make_config(routing={
            "design": PhaseRouting(engine="claude-code"),
        })
        assert select_engine(config, "unknown_phase") == "claude-code"

    def test_empty_routing_defaults_to_claude_code(self):
        config = _make_config()
        assert select_engine(config, "anything") == "claude-code"


class TestComplexityOverride:
    def test_high_complexity_routes_to_claude_code(self):
        config = _make_config(
            complexity_override=ComplexityOverride(
                enabled=True,
                high_complexity_engine="claude-code",
                low_complexity_engine="codex",
            )
        )
        issue = _make_issue(body="### Complexity\n\nHigh\n\nrest")
        assert select_engine(config, "execute", issue=issue) == "claude-code"

    def test_low_complexity_routes_to_codex(self):
        config = _make_config(
            complexity_override=ComplexityOverride(
                enabled=True,
                high_complexity_engine="claude-code",
                low_complexity_engine="codex",
            )
        )
        issue = _make_issue(body="### Complexity\n\nLow\n\nrest")
        assert select_engine(config, "execute", issue=issue) == "codex"

    def test_medium_complexity_routes_to_low_engine(self):
        config = _make_config(
            complexity_override=ComplexityOverride(
                enabled=True,
                high_complexity_engine="claude-code",
                low_complexity_engine="codex",
            )
        )
        issue = _make_issue(body="### Complexity\n\nMedium\n\nrest")
        assert select_engine(config, "execute", issue=issue) == "codex"

    def test_disabled_override_uses_phase_routing(self):
        config = _make_config(
            routing={"execute": PhaseRouting(engine="codex")},
            complexity_override=ComplexityOverride(enabled=False),
        )
        issue = _make_issue(body="### Complexity\n\nHigh\n\nrest")
        assert select_engine(config, "execute", issue=issue) == "codex"

    def test_no_complexity_in_body_falls_through(self):
        config = _make_config(
            routing={"design": PhaseRouting(engine="claude-code")},
            complexity_override=ComplexityOverride(enabled=True),
        )
        issue = _make_issue(body="No complexity info here")
        assert select_engine(config, "design", issue=issue) == "claude-code"
