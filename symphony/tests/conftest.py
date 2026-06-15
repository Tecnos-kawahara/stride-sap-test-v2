"""Shared fixtures for Symphony test suite."""
from __future__ import annotations

import textwrap

import pytest

from symphony.models import Issue


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_ISSUE_BODY = (
    "### Phase\n\ndesign\n\n"
    "### Feature Name\n\norder_import\n\n"
    "### Priority\n\nP1-High\n\n"
    "### Description\n\nTest description content"
)

SAMPLE_ISSUE_BODY_EXECUTE = (
    "### Phase\n\nexecute\n\n"
    "### Feature Name\n\norder_import\n\n"
    "### Priority\n\nP1-High\n\n"
    "### Description\n\nExecute phase task"
)

SAMPLE_CONFIG_YAML = textwrap.dedent("""\
    version: "1.0"
    tracker:
      repo: "owner/repo"
      trigger_label: "symphony:ready"
      running_label: "symphony:running"
      done_label: "symphony:done"
      blocked_label: "symphony:blocked"
      failed_label: "symphony:failed"
    polling:
      interval_seconds: 30
      max_issues_per_cycle: 3
    workspace:
      root: ".symphony/workspaces"
      branch_prefix: "symphony/"
    agent:
      claude_code:
        timeout_ms: 600000
      codex:
        timeout_ms: 300000
      routing:
        design:
          engine: "claude-code"
        execute:
          engine: "codex"
      complexity_override:
        enabled: false
      retry:
        max_attempts: 3
        backoff_base_ms: 10000
        backoff_max_ms: 300000
      max_parallel: 4
    hooks:
      after_create: "echo created"
    observability:
      log_dir: ".symphony/logs"
      stride_board:
        enabled: false
""")

SAMPLE_PROMPT_TEMPLATE = textwrap.dedent("""\
    You are working on feature {{ feature_name }} in the {{ phase }} phase.

    Issue: {{ issue.identifier }}
    URL: {{ issue.url }}
    Description: {{ issue.description }}

    {% if attempt %}This is retry attempt {{ attempt }}.{% endif %}
""")

SAMPLE_SYMPHONY_MD = f"---\n{SAMPLE_CONFIG_YAML}---\n{SAMPLE_PROMPT_TEMPLATE}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_issue_body() -> str:
    """A string mimicking a GitHub Issue Form body."""
    return SAMPLE_ISSUE_BODY


@pytest.fixture
def sample_issue(sample_issue_body: str) -> Issue:
    """An Issue instance built from sample_issue_body."""
    return Issue(
        number=42,
        title="Design order_import",
        body=sample_issue_body,
        url="https://github.com/owner/repo/issues/42",
        priority="P1",
        phase="design",
        feature_name="order_import",
        labels=["symphony:ready"],
    )


@pytest.fixture
def sample_config_yaml() -> str:
    """Valid SYMPHONY.md YAML front matter string."""
    return SAMPLE_CONFIG_YAML


@pytest.fixture
def sample_symphony_md() -> str:
    """Full SYMPHONY.md content (YAML + prompt template)."""
    return SAMPLE_SYMPHONY_MD


@pytest.fixture
def tmp_symphony_md(tmp_path, sample_symphony_md: str):
    """Write sample_symphony_md to a tmp_path file and return the path."""
    md_path = tmp_path / "SYMPHONY.md"
    md_path.write_text(sample_symphony_md, encoding="utf-8")
    return md_path
