"""Tests for symphony.models."""
from __future__ import annotations

from symphony.models import Issue, OrchestratorState, RetryEntry, RunResult, Session


class TestIssue:
    def test_creation(self, sample_issue: Issue):
        assert sample_issue.number == 42
        assert sample_issue.title == "Design order_import"
        assert sample_issue.phase == "design"
        assert sample_issue.feature_name == "order_import"

    def test_identifier(self, sample_issue: Issue):
        assert sample_issue.identifier == "#42"

    def test_description_returns_body(self, sample_issue: Issue):
        assert sample_issue.description == sample_issue.body
        assert "Test description content" in sample_issue.description

    def test_labels_default_empty(self):
        issue = Issue(
            number=1, title="t", body="b", url="u",
            priority="P2", phase="design", feature_name="f",
        )
        assert issue.labels == []


class TestSession:
    def test_defaults(self):
        s = Session(issue_id=1, engine="claude-code", workspace_path="/w", started_at=0.0)
        assert s.status == "running"
        assert s.attempt == 1

    def test_custom_values(self):
        s = Session(
            issue_id=5, engine="codex", workspace_path="/x",
            started_at=100.0, status="blocked", attempt=3,
        )
        assert s.status == "blocked"
        assert s.attempt == 3


class TestRunResult:
    def test_defaults(self):
        r = RunResult(issue_id=1, phase="design", attempt=1, started_at=0.0, ended_at=1.0, status="success")
        assert r.error is None
        assert r.log_path is None

    def test_with_error(self):
        r = RunResult(
            issue_id=2, phase="execute", attempt=2,
            started_at=0.0, ended_at=1.0,
            status="failure", error="boom",
        )
        assert r.error == "boom"


class TestRetryEntry:
    def test_defaults(self):
        e = RetryEntry(issue_id=1, attempt=2, due_at=100.0)
        assert e.error is None


class TestOrchestratorState:
    def test_defaults(self):
        state = OrchestratorState()
        assert state.running == {}
        assert state.claimed == set()
        assert state.retry_queue == {}
        assert state.completed == set()
