"""Tests for Symphony Janitor proposals (v5.1 harness marker)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from symphony.config import JanitorConfig, SymphonyConfig, _build_dataclass
from symphony.tracker import has_recent_pr, has_open_janitor_issue, create_janitor_issue


pytestmark = pytest.mark.harness


# ---------------------------------------------------------------------------
# JanitorConfig dataclass
# ---------------------------------------------------------------------------

def test_janitor_config_defaults():
    j = JanitorConfig()
    assert j.enabled is False
    assert j.interval_hours == 6
    assert j.exclude_recent_pr_days == 7
    assert "risk:authz" in j.risk_flags_exclude
    assert "risk:pii" in j.risk_flags_exclude


def test_janitor_config_custom():
    j = JanitorConfig(enabled=True, interval_hours=12, exclude_recent_pr_days=14)
    assert j.enabled is True
    assert j.interval_hours == 12


def test_symphony_config_has_janitor():
    cfg = SymphonyConfig()
    assert hasattr(cfg, "janitor")
    assert isinstance(cfg.janitor, JanitorConfig)


def test_janitor_loaded_from_dict():
    data = {
        "tracker": {"repo": "owner/repo"},
        "janitor": {
            "enabled": True,
            "interval_hours": 3,
            "exclude_recent_pr_days": 5,
            "risk_flags_exclude": ["risk:authz"],
        },
    }
    cfg = _build_dataclass(SymphonyConfig, data)
    assert cfg.janitor.enabled is True
    assert cfg.janitor.interval_hours == 3
    assert cfg.janitor.exclude_recent_pr_days == 5
    assert cfg.janitor.risk_flags_exclude == ["risk:authz"]


def test_janitor_not_in_dict_uses_defaults():
    data = {"tracker": {"repo": "owner/repo"}}
    cfg = _build_dataclass(SymphonyConfig, data)
    assert cfg.janitor.enabled is False


# ---------------------------------------------------------------------------
# has_recent_pr
# ---------------------------------------------------------------------------

def test_has_recent_pr_returns_true_when_pr_exists():
    fake_output = json.dumps([{"number": 42}])
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = fake_output

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        result = has_recent_pr("owner/repo", "my_feature", days=7)
    assert result is True


def test_has_recent_pr_returns_false_when_no_pr():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = json.dumps([])

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        result = has_recent_pr("owner/repo", "my_feature", days=7)
    assert result is False


def test_has_recent_pr_returns_false_on_gh_failure():
    fake_result = mock.MagicMock()
    fake_result.returncode = 1
    fake_result.stdout = ""

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        result = has_recent_pr("owner/repo", "my_feature", days=7)
    assert result is False


def test_has_recent_pr_returns_false_on_json_error():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "not json"

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        result = has_recent_pr("owner/repo", "my_feature", days=7)
    assert result is False


# ---------------------------------------------------------------------------
# create_janitor_issue
# ---------------------------------------------------------------------------

def test_create_janitor_issue_success():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "https://github.com/owner/repo/issues/99\n"

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        num = create_janitor_issue("owner/repo", "my_feature", "some drift report")
    assert num == 99


def test_create_janitor_issue_gh_failure():
    fake_result = mock.MagicMock()
    fake_result.returncode = 1
    fake_result.stdout = ""

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        num = create_janitor_issue("owner/repo", "my_feature", "report")
    assert num == -1


def test_create_janitor_issue_url_parse_fallback():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "unexpected output\n"

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        num = create_janitor_issue("owner/repo", "my_feature", "report")
    assert num == -1


# ---------------------------------------------------------------------------
# has_open_janitor_issue
# ---------------------------------------------------------------------------

def test_has_open_janitor_issue_returns_true_when_open():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = json.dumps([{"number": 5}])

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        assert has_open_janitor_issue("owner/repo", "my_feature") is True


def test_has_open_janitor_issue_returns_false_when_none():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = json.dumps([])

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        assert has_open_janitor_issue("owner/repo", "my_feature") is False


def test_has_open_janitor_issue_returns_false_on_gh_failure():
    fake_result = mock.MagicMock()
    fake_result.returncode = 1
    fake_result.stdout = ""

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        assert has_open_janitor_issue("owner/repo", "my_feature") is False


def test_has_open_janitor_issue_returns_false_on_json_error():
    fake_result = mock.MagicMock()
    fake_result.returncode = 0
    fake_result.stdout = "bad json"

    with mock.patch("symphony.tracker._run_gh", return_value=fake_result):
        assert has_open_janitor_issue("owner/repo", "my_feature") is False


def test_create_janitor_issue_calls_ensure_label():
    """Verify create_janitor_issue provisions symphony:janitor before creating the issue."""
    calls = []

    def capture_gh(*args):
        calls.append(list(args))
        fake = mock.MagicMock()
        fake.returncode = 0
        fake.stdout = "https://github.com/owner/repo/issues/7\n"
        return fake

    with mock.patch("symphony.tracker._run_gh", side_effect=capture_gh):
        num = create_janitor_issue("owner/repo", "feat_x", "report")

    assert num == 7
    # First call must be label create (--force)
    assert calls[0][0] == "label"
    assert calls[0][1] == "create"
    assert "symphony:janitor" in calls[0]
    assert "--force" in calls[0]
    # Second call must be issue create
    assert calls[1][0] == "issue"
    assert calls[1][1] == "create"


# ---------------------------------------------------------------------------

def test_has_recent_pr_passes_correct_date():
    """Verify the merged: filter uses the correct date format."""
    captured_args = {}

    def capture_gh(*args, **kwargs):
        captured_args["args"] = args
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_result.stdout = json.dumps([])
        return fake_result

    with mock.patch("symphony.tracker._run_gh", side_effect=capture_gh):
        has_recent_pr("owner/repo", "my_feature", days=7)

    # Check that --search was passed and contains merged:>= with a date
    args_list = [str(a) for a in captured_args.get("args", [])]
    search_text = " ".join(args_list)
    assert "merged:>=" in search_text
    import re
    assert re.search(r"merged:>=\d{4}-\d{2}-\d{2}", search_text)
