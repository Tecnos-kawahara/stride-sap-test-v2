"""Tests for symphony.prompt."""
from __future__ import annotations

import pytest
from jinja2 import UndefinedError

from symphony.models import Issue
from symphony.prompt import render_prompt


TEMPLATE = """\
Phase: {{ phase }}
Feature: {{ feature_name }}
Issue: {{ issue.identifier }}
URL: {{ issue.url }}
Description: {{ issue.description }}
{% if attempt %}Attempt: {{ attempt }}{% endif %}
"""


def _make_issue(**kwargs) -> Issue:
    defaults = dict(
        number=42, title="T", body="Body text",
        url="https://github.com/owner/repo/issues/42",
        priority="P1", phase="design", feature_name="f",
    )
    defaults.update(kwargs)
    return Issue(**defaults)


class TestRenderPrompt:
    def test_design_phase(self):
        result = render_prompt(TEMPLATE, _make_issue(), "design", "order_import")
        assert "Phase: design" in result
        assert "Feature: order_import" in result

    def test_specify_phase(self):
        result = render_prompt(TEMPLATE, _make_issue(), "specify", "order_import")
        assert "Phase: specify" in result

    def test_tasking_phase(self):
        result = render_prompt(TEMPLATE, _make_issue(), "tasking", "order_import")
        assert "Phase: tasking" in result

    def test_execute_phase(self):
        result = render_prompt(TEMPLATE, _make_issue(), "execute", "order_import")
        assert "Phase: execute" in result

    def test_issue_description_accessible(self):
        issue = _make_issue(body="This is the description content")
        result = render_prompt(TEMPLATE, issue, "design", "f")
        assert "Description: This is the description content" in result

    def test_issue_url_accessible(self):
        issue = _make_issue(url="https://example.com/issues/99")
        result = render_prompt(TEMPLATE, issue, "design", "f")
        assert "URL: https://example.com/issues/99" in result

    def test_attempt_variable_injection(self):
        result = render_prompt(TEMPLATE, _make_issue(), "design", "f", attempt=3)
        assert "Attempt: 3" in result

    def test_attempt_none_omitted(self):
        result = render_prompt(TEMPLATE, _make_issue(), "design", "f", attempt=None)
        assert "Attempt:" not in result

    def test_undefined_variable_raises(self):
        bad_template = "{{ nonexistent_variable }}"
        with pytest.raises(UndefinedError):
            render_prompt(bad_template, _make_issue(), "design", "f")
