"""Tests for symphony.retry."""
from __future__ import annotations

import pytest

from symphony.models import RunResult
from symphony.retry import RetryManager, calculate_backoff, should_retry


def _make_result(
    status: str = "failure",
    attempt: int = 1,
    issue_id: int = 1,
) -> RunResult:
    return RunResult(
        issue_id=issue_id, phase="design", attempt=attempt,
        started_at=0.0, ended_at=1.0, status=status,
    )


class TestShouldRetry:
    def test_approval_pending_no_retry(self):
        result = _make_result(status="approval_pending", attempt=1)
        assert should_retry(result, max_attempts=3) is False

    def test_max_attempts_exceeded_no_retry(self):
        result = _make_result(status="failure", attempt=3)
        assert should_retry(result, max_attempts=3) is False

    def test_max_attempts_exceeded_over(self):
        result = _make_result(status="failure", attempt=5)
        assert should_retry(result, max_attempts=3) is False

    def test_success_no_retry(self):
        result = _make_result(status="success", attempt=1)
        assert should_retry(result, max_attempts=3) is False

    def test_failure_with_attempts_remaining(self):
        result = _make_result(status="failure", attempt=1)
        assert should_retry(result, max_attempts=3) is True

    def test_timeout_with_attempts_remaining(self):
        result = _make_result(status="timeout", attempt=2)
        assert should_retry(result, max_attempts=3) is True


class TestCalculateBackoff:
    def test_first_attempt(self):
        # base_ms * 2^(1-1) = 30000 * 1 = 30000ms = 30s
        assert calculate_backoff(1) == 30.0

    def test_second_attempt(self):
        # base_ms * 2^(2-1) = 30000 * 2 = 60000ms = 60s
        assert calculate_backoff(2) == 60.0

    def test_third_attempt(self):
        # base_ms * 2^(3-1) = 30000 * 4 = 120000ms = 120s
        assert calculate_backoff(3) == 120.0

    def test_exponential_growth(self):
        b1 = calculate_backoff(1)
        b2 = calculate_backoff(2)
        b3 = calculate_backoff(3)
        assert b2 == b1 * 2
        assert b3 == b1 * 4

    def test_max_cap(self):
        # Very high attempt should be capped at max_ms
        result = calculate_backoff(20, base_ms=30_000, max_ms=600_000)
        assert result == 600.0  # 600_000 / 1000

    def test_custom_base(self):
        result = calculate_backoff(1, base_ms=10_000)
        assert result == 10.0


class TestRetryManager:
    def test_enqueue_and_has(self):
        mgr = RetryManager()
        mgr.enqueue(42, attempt=2, backoff_seconds=10.0)
        assert mgr.has(42)
        assert not mgr.has(99)

    def test_remove(self):
        mgr = RetryManager()
        mgr.enqueue(42, attempt=2, backoff_seconds=10.0)
        mgr.remove(42)
        assert not mgr.has(42)

    def test_get_due(self):
        mgr = RetryManager()
        # Enqueue with 0 backoff so it's immediately due
        mgr.enqueue(42, attempt=2, backoff_seconds=0)
        due = mgr.get_due()
        assert len(due) == 1
        assert due[0].issue_id == 42

    def test_clear(self):
        mgr = RetryManager()
        mgr.enqueue(1, attempt=1, backoff_seconds=0)
        mgr.enqueue(2, attempt=1, backoff_seconds=0)
        mgr.clear()
        assert mgr.entries == {}
