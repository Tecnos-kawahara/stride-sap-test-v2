"""Retry management — exponential backoff with cap."""
from __future__ import annotations

import time
from typing import Optional

from symphony.models import RetryEntry, RunResult
from symphony.logger import get_logger

logger = get_logger(__name__)


def should_retry(result: RunResult, max_attempts: int) -> bool:
    """Determine if a failed run should be retried.

    Returns False when:
        - status is "approval_pending" (needs human action, not a retry)
        - attempt count has reached or exceeded max_attempts
        - status is "success" (nothing to retry)
    """
    if result.status == "success":
        return False
    if result.status == "approval_pending":
        return False
    if result.attempt >= max_attempts:
        logger.info(
            "Issue %d: max attempts (%d) reached, will not retry",
            result.issue_id, max_attempts,
        )
        return False
    return True


def calculate_backoff(attempt: int, base_ms: int = 30_000, max_ms: int = 600_000) -> float:
    """Compute backoff delay in seconds using exponential backoff with cap.

    Formula: min(base_ms * 2^(attempt-1), max_ms)  →  converted to seconds.

    Args:
        attempt: the attempt number (1-based)
        base_ms: base delay in milliseconds
        max_ms: maximum delay in milliseconds

    Returns:
        Delay in seconds (float).
    """
    delay_ms = min(base_ms * (2 ** (attempt - 1)), max_ms)
    return delay_ms / 1000.0


class RetryManager:
    """Manages a queue of retry entries and checks which are due."""

    def __init__(self) -> None:
        self._entries: dict[int, RetryEntry] = {}

    @property
    def entries(self) -> dict[int, RetryEntry]:
        return dict(self._entries)

    def enqueue(
        self,
        issue_id: int,
        attempt: int,
        backoff_seconds: float,
        error: Optional[str] = None,
    ) -> RetryEntry:
        """Add an issue to the retry queue."""
        due_at = time.time() + backoff_seconds
        entry = RetryEntry(
            issue_id=issue_id,
            attempt=attempt,
            due_at=due_at,
            error=error,
        )
        self._entries[issue_id] = entry
        logger.info(
            "Enqueued retry for #%d: attempt=%d, due in %.1fs",
            issue_id, attempt, backoff_seconds,
        )
        return entry

    def get_due(self) -> list[RetryEntry]:
        """Return all entries whose due_at has passed."""
        now = time.time()
        due = [e for e in self._entries.values() if e.due_at <= now]
        return due

    def remove(self, issue_id: int) -> None:
        """Remove an entry from the retry queue."""
        self._entries.pop(issue_id, None)

    def has(self, issue_id: int) -> bool:
        """Check if an issue is in the retry queue."""
        return issue_id in self._entries

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()
