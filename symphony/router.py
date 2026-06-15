"""Agent routing — selects engine (claude-code / codex) per phase and complexity."""
from __future__ import annotations

import re
from typing import Optional

from symphony.config import SymphonyConfig
from symphony.models import Issue


def _extract_complexity(body: str) -> Optional[str]:
    """Extract WI complexity from issue body, if present.

    Looks for patterns like:
        ### Complexity
        High
    or:
        complexity: high
    """
    # Markdown heading style
    match = re.search(r"###\s+Complexity\s*\n\s*\n\s*(\w+)", body, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    # Inline YAML style
    match = re.search(r"complexity:\s*(\w+)", body, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return None


def select_engine(
    config: SymphonyConfig,
    phase: str,
    issue: Optional[Issue] = None,
) -> str:
    """Determine which AI engine to use for a given phase and issue.

    Decision order:
        1. Complexity override (if enabled and issue has complexity info)
        2. Phase-based routing from config
        3. Default: "claude-code"
    """
    co = config.agent.complexity_override

    # 1. Complexity-based override
    if co.enabled and issue is not None:
        complexity = _extract_complexity(issue.body)
        if complexity == "high":
            return co.high_complexity_engine
        if complexity in ("low", "medium"):
            return co.low_complexity_engine

    # 2. Phase-based routing
    routing = config.agent.routing
    if phase in routing:
        return routing[phase].engine

    # 3. Fallback
    return "claude-code"
