"""State reconciliation — detects drift between orchestrator state and GitHub."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from symphony.config import SymphonyConfig
from symphony.models import OrchestratorState, Session
from symphony.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReconcileActions:
    """Actions determined by reconciliation."""

    cleanup: list[int] = field(default_factory=list)       # sessions to tear down
    unblock: list[int] = field(default_factory=list)       # sessions to resume
    stale_claims: list[int] = field(default_factory=list)  # claimed but not running


def _issue_has_label(repo: str, issue_number: int, label: str) -> bool:
    """Check if a GitHub issue currently has a specific label."""
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number),
         "--repo", repo,
         "--json", "labels"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    if result.returncode != 0:
        logger.warning(
            "Failed to check labels for #%d: %s",
            issue_number, result.stderr.strip(),
        )
        return False

    try:
        data = json.loads(result.stdout)
        label_names = [lb["name"] for lb in data.get("labels", [])]
        return label in label_names
    except (json.JSONDecodeError, KeyError):
        return False


def _issue_is_open(repo: str, issue_number: int) -> bool:
    """Check if a GitHub issue is still open."""
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number),
         "--repo", repo,
         "--json", "state"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )
    if result.returncode != 0:
        return False

    try:
        data = json.loads(result.stdout)
        return data.get("state", "").upper() == "OPEN"
    except (json.JSONDecodeError, KeyError):
        return False


def _check_approval_resolved(feature_path: str, cwd: str) -> bool:
    """Run stride-lint to check if APPROVAL_PENDING status has resolved.

    Returns True if APPROVAL_PENDING no longer appears in the output.
    Note: Other lint errors (e.g. future-phase GATE_FAILED) are expected
    and should not block unblocking the current phase.
    """
    result = subprocess.run(
        ["bash", "sdd-templates/tools/stride-lint", feature_path],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    output = result.stdout + result.stderr
    if "APPROVAL_PENDING" in output:
        return False
    return True


def reconcile(state: OrchestratorState, config: SymphonyConfig) -> ReconcileActions:
    """Compare orchestrator state with GitHub reality and determine actions.

    Checks:
        1. Running sessions: is the trigger label still present? Is the issue still open?
           If not → mark for cleanup.
        2. Blocked sessions (status == "blocked"): re-run stride-lint to see if
           APPROVAL_PENDING has been resolved. If resolved → mark for unblock.
        3. Claimed but not running: detect orphan claims.

    Returns:
        ReconcileActions describing what the orchestrator should do.
    """
    actions = ReconcileActions()
    repo = config.tracker.repo
    trigger_label = config.tracker.trigger_label

    # 1. Check running sessions
    for issue_id, session in list(state.running.items()):
        # Check if issue is still open
        if not _issue_is_open(repo, issue_id):
            logger.info("Issue #%d is closed — scheduling cleanup", issue_id)
            actions.cleanup.append(issue_id)
            continue

        # Check if trigger label was removed (human cancelled)
        if not _issue_has_label(repo, issue_id, trigger_label):
            logger.info(
                "Issue #%d lost trigger label '%s' — scheduling cleanup",
                issue_id, trigger_label,
            )
            actions.cleanup.append(issue_id)
            continue

        # Check blocked sessions for approval resolution
        if session.status == "blocked":
            feature_path = f"specs/{session.feature_name}"
            if _check_approval_resolved(feature_path, cwd=session.workspace_path):
                logger.info("Issue #%d: approval resolved — scheduling unblock", issue_id)
                actions.unblock.append(issue_id)

    # 2. Detect stale claims (claimed but not running and not in retry queue)
    for issue_id in state.claimed:
        if issue_id not in state.running and issue_id not in state.retry_queue:
            if issue_id not in state.completed:
                logger.warning("Issue #%d: claimed but not running — stale", issue_id)
                actions.stale_claims.append(issue_id)

    return actions
