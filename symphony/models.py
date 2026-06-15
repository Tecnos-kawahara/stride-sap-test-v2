"""Core data models for the Symphony orchestrator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Issue:
    """Represents a GitHub Issue that triggers an SDD phase run."""

    number: int
    title: str
    body: str
    url: str
    priority: str
    phase: str
    feature_name: str
    labels: list[str] = field(default_factory=list)

    @property
    def identifier(self) -> str:
        """Return the issue reference string (e.g. '#42')."""
        return f"#{self.number}"

    @property
    def description(self) -> str:
        """Alias for body, used by prompt rendering."""
        return self.body


@dataclass
class Session:
    """A running agent session bound to an issue."""

    issue_id: int
    engine: str
    workspace_path: str
    started_at: float
    feature_name: str = ""
    status: str = "running"
    attempt: int = 1


@dataclass
class RunResult:
    """Outcome of a single agent run."""

    issue_id: int
    phase: str
    attempt: int
    started_at: float
    ended_at: float
    status: str
    error: Optional[str] = None
    log_path: Optional[str] = None


@dataclass
class RetryEntry:
    """A queued retry for a failed run."""

    issue_id: int
    attempt: int
    due_at: float
    error: Optional[str] = None


@dataclass
class OrchestratorState:
    """Mutable state tracking all orchestrator activity."""

    running: dict[int, Session] = field(default_factory=dict)
    claimed: set[int] = field(default_factory=set)
    retry_queue: dict[int, RetryEntry] = field(default_factory=dict)
    completed: set[int] = field(default_factory=set)
