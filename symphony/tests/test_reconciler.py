"""Tests for symphony.reconciler."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from symphony.config import SymphonyConfig, TrackerConfig
from symphony.models import OrchestratorState, Session
from symphony.reconciler import (
    ReconcileActions,
    _check_approval_resolved,
    _issue_has_label,
    _issue_is_open,
    reconcile,
)


def _make_config(repo: str = "owner/repo") -> SymphonyConfig:
    config = SymphonyConfig()
    config.tracker = TrackerConfig(repo=repo)
    return config


def _make_session(
    issue_id: int,
    status: str = "running",
    workspace_path: str = "/ws/42",
    feature_name: str = "my_feature",
) -> Session:
    return Session(
        issue_id=issue_id,
        engine="claude-code",
        workspace_path=workspace_path,
        started_at=0.0,
        feature_name=feature_name,
        status=status,
    )


class TestReconcileIssueClose:
    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_closed_issue_triggers_cleanup(self, mock_is_open, mock_has_label):
        mock_is_open.return_value = False  # Issue is closed
        mock_has_label.return_value = True

        state = OrchestratorState()
        state.running[42] = _make_session(42)
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 in actions.cleanup

    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_open_issue_with_label_no_cleanup(self, mock_is_open, mock_has_label):
        mock_is_open.return_value = True
        mock_has_label.return_value = True

        state = OrchestratorState()
        state.running[42] = _make_session(42)
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 not in actions.cleanup


class TestReconcileLabelRemoval:
    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_label_removed_triggers_cleanup(self, mock_is_open, mock_has_label):
        mock_is_open.return_value = True
        mock_has_label.return_value = False  # Label was removed

        state = OrchestratorState()
        state.running[42] = _make_session(42)
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 in actions.cleanup


class TestReconcileApprovalUnblock:
    @patch("symphony.reconciler._check_approval_resolved")
    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_blocked_with_resolved_approval_triggers_unblock(
        self, mock_is_open, mock_has_label, mock_approval
    ):
        mock_is_open.return_value = True
        mock_has_label.return_value = True
        mock_approval.return_value = True  # Approval resolved

        state = OrchestratorState()
        state.running[42] = _make_session(42, status="blocked", workspace_path="/ws/42", feature_name="my_feature")
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 in actions.unblock
        # Verify the feature_name-based path was used
        mock_approval.assert_called_once_with("specs/my_feature", cwd="/ws/42")

    @patch("symphony.reconciler._check_approval_resolved")
    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_blocked_with_pending_approval_no_unblock(
        self, mock_is_open, mock_has_label, mock_approval
    ):
        mock_is_open.return_value = True
        mock_has_label.return_value = True
        mock_approval.return_value = False  # Still pending

        state = OrchestratorState()
        state.running[42] = _make_session(42, status="blocked", workspace_path="/ws/42", feature_name="my_feature")
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 not in actions.unblock


class TestReconcileStaleClaims:
    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_claimed_but_not_running_is_stale(self, mock_is_open, mock_has_label):
        state = OrchestratorState()
        state.claimed.add(99)
        # Not in running, not in retry_queue, not completed
        config = _make_config()

        actions = reconcile(state, config)
        assert 99 in actions.stale_claims

    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_claimed_and_running_not_stale(self, mock_is_open, mock_has_label):
        mock_is_open.return_value = True
        mock_has_label.return_value = True

        state = OrchestratorState()
        state.claimed.add(42)
        state.running[42] = _make_session(42)
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 not in actions.stale_claims

    @patch("symphony.reconciler._issue_has_label")
    @patch("symphony.reconciler._issue_is_open")
    def test_completed_not_stale(self, mock_is_open, mock_has_label):
        state = OrchestratorState()
        state.claimed.add(42)
        state.completed.add(42)
        config = _make_config()

        actions = reconcile(state, config)
        assert 42 not in actions.stale_claims


# ---------------------------------------------------------------------------
# Direct tests for private helper functions (subprocess mocked)
# ---------------------------------------------------------------------------


class TestIssueHasLabel:
    @patch("symphony.reconciler.subprocess.run")
    def test_returns_true_when_label_found(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"labels": [{"name": "bug"}, {"name": "symphony:ready"}]}),
            stderr="",
        )
        assert _issue_has_label("owner/repo", 42, "symphony:ready") is True

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_when_label_not_found(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"labels": [{"name": "bug"}]}),
            stderr="",
        )
        assert _issue_has_label("owner/repo", 42, "symphony:ready") is False

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_on_subprocess_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="auth error",
        )
        assert _issue_has_label("owner/repo", 42, "symphony:ready") is False

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_on_json_decode_error(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="not valid json",
            stderr="",
        )
        assert _issue_has_label("owner/repo", 42, "symphony:ready") is False


class TestIssueIsOpen:
    @patch("symphony.reconciler.subprocess.run")
    def test_returns_true_for_open_state(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"state": "OPEN"}),
            stderr="",
        )
        assert _issue_is_open("owner/repo", 42) is True

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_for_closed_state(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"state": "CLOSED"}),
            stderr="",
        )
        assert _issue_is_open("owner/repo", 42) is False

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="network error",
        )
        assert _issue_is_open("owner/repo", 42) is False


class TestCheckApprovalResolved:
    @patch("symphony.reconciler.subprocess.run")
    def test_returns_true_when_lint_passes(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="ALL_GATES_PASSED",
            stderr="",
        )
        assert _check_approval_resolved("specs/my_feature", cwd="/ws/42") is True

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_when_approval_pending_in_output(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="APPROVAL_PENDING: Gate 3",
            stderr="",
        )
        assert _check_approval_resolved("specs/my_feature", cwd="/ws/42") is False

    @patch("symphony.reconciler.subprocess.run")
    def test_returns_false_on_nonzero_exit_without_approval_pending(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="some other error",
            stderr="lint failed",
        )
        assert _check_approval_resolved("specs/my_feature", cwd="/ws/42") is False
