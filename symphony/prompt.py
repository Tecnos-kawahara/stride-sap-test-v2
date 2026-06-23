"""Jinja2-based prompt rendering for agent instructions."""
from __future__ import annotations

from typing import Optional

from symphony.models import Issue

try:
    from jinja2 import Environment, StrictUndefined
except ImportError as exc:
    raise ImportError(
        "Jinja2 is required for prompt rendering. "
        "Install it with: pip install jinja2"
    ) from exc


def render_prompt(
    template_str: str,
    issue: Issue,
    phase: str,
    feature_name: str,
    attempt: Optional[int] = None,
    base_branch: str = "main",
) -> str:
    """Render a Jinja2 prompt template with the given context.

    Available template variables:
        - issue: the Issue dataclass instance
        - phase: the SDD phase name (e.g. "Design", "Specify")
        - feature_name: the feature identifier
        - attempt: retry attempt number (None on first try)
        - base_branch: the target branch for PRs (default "main")

    Uses StrictUndefined so that missing variables raise immediately
    rather than silently producing empty strings.
    """
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(template_str)
    rendered = template.render(
        issue=issue,
        phase=phase,
        feature_name=feature_name,
        attempt=attempt,
        base_branch=base_branch,
    )
    return rendered
