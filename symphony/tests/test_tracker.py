"""Tests for symphony.tracker."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from symphony.models import Issue
from symphony.tracker import add_label, extract_field, fetch_ready_issues, post_comment, remove_label


class TestExtractField:
    def test_extract_phase(self, sample_issue_body: str):
        assert extract_field(sample_issue_body, "Phase") == "design"

    def test_extract_feature_name(self):
        body = "### Feature Name\n\norder_import\n\nmore text"
        assert extract_field(body, "Feature Name") == "order_import"

    def test_extract_priority(self, sample_issue_body: str):
        assert extract_field(sample_issue_body, "Priority") == "P1-High"

    def test_missing_field_raises(self, sample_issue_body: str):
        with pytest.raises(ValueError, match="not found"):
            extract_field(sample_issue_body, "NonExistentField")

    def test_no_response_raises(self):
        body = "### Phase\n\n_No response_\n\nOther stuff"
        with pytest.raises(ValueError, match="no value"):
            extract_field(body, "Phase")


class TestFetchReadyIssues:
    @patch("symphony.tracker._run_gh")
    def test_returns_parsed_issues(self, mock_gh: MagicMock):
        raw = [
            {
                "number": 10,
                "title": "Design foo",
                "body": "### Phase\n\ndesign\n\n### Feature Name\n\nfoo\n\n### Priority\n\nP1",
                "labels": [{"name": "symphony:ready"}],
                "url": "https://github.com/owner/repo/issues/10",
            },
            {
                "number": 20,
                "title": "Execute bar",
                "body": "### Phase\n\nexecute\n\n### Feature Name\n\nbar\n\n### Priority\n\nP0",
                "labels": [{"name": "symphony:ready"}],
                "url": "https://github.com/owner/repo/issues/20",
            },
        ]
        mock_gh.return_value = MagicMock(returncode=0, stdout=json.dumps(raw), stderr="")

        issues = fetch_ready_issues("owner/repo", "symphony:ready")

        assert len(issues) == 2
        assert isinstance(issues[0], Issue)
        # P0 should sort before P1
        assert issues[0].priority == "P0"
        assert issues[1].priority == "P1"

    @patch("symphony.tracker._run_gh")
    def test_priority_sorting(self, mock_gh: MagicMock):
        """P0 before P1 before P2."""
        raw = [
            {"number": 1, "title": "A", "body": "### Phase\n\nx\n\n### Priority\n\nP2", "labels": [], "url": "u1"},
            {"number": 2, "title": "B", "body": "### Phase\n\nx\n\n### Priority\n\nP0", "labels": [], "url": "u2"},
            {"number": 3, "title": "C", "body": "### Phase\n\nx\n\n### Priority\n\nP1", "labels": [], "url": "u3"},
        ]
        mock_gh.return_value = MagicMock(returncode=0, stdout=json.dumps(raw), stderr="")

        issues = fetch_ready_issues("owner/repo", "symphony:ready")
        priorities = [i.priority for i in issues]
        assert priorities == ["P0", "P1", "P2"]

    @patch("symphony.tracker._run_gh")
    def test_priority_sorting_with_long_form_values(self, mock_gh: MagicMock):
        """P0-Critical before P1-High before P2-Medium — real issue form values."""
        raw = [
            {"number": 1, "title": "A", "body": "### Phase\n\nx\n\n### Priority\n\nP2-Medium", "labels": [], "url": "u1"},
            {"number": 2, "title": "B", "body": "### Phase\n\nx\n\n### Priority\n\nP0-Critical", "labels": [], "url": "u2"},
            {"number": 3, "title": "C", "body": "### Phase\n\nx\n\n### Priority\n\nP1-High", "labels": [], "url": "u3"},
        ]
        mock_gh.return_value = MagicMock(returncode=0, stdout=json.dumps(raw), stderr="")

        issues = fetch_ready_issues("owner/repo", "symphony:ready")
        priorities = [i.priority for i in issues]
        assert priorities == ["P0-Critical", "P1-High", "P2-Medium"]

    @patch("symphony.tracker._run_gh")
    def test_feature_name_extracted_from_feature_name_field(self, mock_gh: MagicMock):
        """Verify Feature Name (not Feature) is used for extraction."""
        raw = [
            {
                "number": 10,
                "title": "Test",
                "body": "### Phase\n\ndesign\n\n### Feature Name\n\norder_import\n\n### Priority\n\nP1",
                "labels": [],
                "url": "u1",
            },
        ]
        mock_gh.return_value = MagicMock(returncode=0, stdout=json.dumps(raw), stderr="")
        issues = fetch_ready_issues("owner/repo", "symphony:ready")
        assert issues[0].feature_name == "order_import"

    @patch("symphony.tracker._run_gh")
    def test_gh_failure_raises(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=1, stdout="", stderr="auth error")
        with pytest.raises(RuntimeError, match="gh issue list failed"):
            fetch_ready_issues("owner/repo", "symphony:ready")


class TestAddLabel:
    @patch("symphony.tracker._run_gh")
    def test_calls_correct_command(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=0, stdout="", stderr="")
        add_label("owner/repo", 42, "symphony:running")
        mock_gh.assert_called_once_with(
            "issue", "edit", "42",
            "--repo", "owner/repo",
            "--add-label", "symphony:running",
        )

    @patch("symphony.tracker._run_gh")
    def test_failure_raises(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=1, stdout="", stderr="permission denied")
        with pytest.raises(RuntimeError, match="Failed to add label"):
            add_label("owner/repo", 42, "bad-label")


class TestRemoveLabel:
    @patch("symphony.tracker._run_gh")
    def test_calls_correct_command(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=0, stdout="", stderr="")
        remove_label("owner/repo", 42, "symphony:running")
        mock_gh.assert_called_once_with(
            "issue", "edit", "42",
            "--repo", "owner/repo",
            "--remove-label", "symphony:running",
        )

    @patch("symphony.tracker._run_gh")
    def test_failure_raises(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=1, stdout="", stderr="permission denied")
        with pytest.raises(RuntimeError, match="Failed to remove label"):
            remove_label("owner/repo", 42, "bad-label")


class TestPostComment:
    @patch("symphony.tracker._run_gh")
    def test_calls_correct_command(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=0, stdout="", stderr="")
        post_comment("owner/repo", 42, "Hello world")
        mock_gh.assert_called_once_with(
            "issue", "comment", "42",
            "--repo", "owner/repo",
            "--body", "Hello world",
        )

    @patch("symphony.tracker._run_gh")
    def test_failure_raises(self, mock_gh: MagicMock):
        mock_gh.return_value = MagicMock(returncode=1, stdout="", stderr="network error")
        with pytest.raises(RuntimeError, match="Failed to comment on"):
            post_comment("owner/repo", 42, "Hello world")
