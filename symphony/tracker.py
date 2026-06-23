"""GitHub Issues adapter — fetches, labels, and comments via `gh` CLI."""
from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Optional

import yaml

from symphony.models import Issue


# ---------------------------------------------------------------------------
# Priority ordering
# ---------------------------------------------------------------------------

_PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def _priority_key(issue: Issue) -> int:
    """Sort by priority prefix (P0 > P1 > P2 > P3).

    Handles both short ('P1') and long ('P1-High') forms by extracting
    the first two characters.
    """
    prefix = issue.priority[:2] if len(issue.priority) >= 2 else issue.priority
    return _PRIORITY_ORDER.get(prefix, 99)


# ---------------------------------------------------------------------------
# Body field extraction
# ---------------------------------------------------------------------------

def extract_field(body: str, field_name: str) -> str:
    """Extract a dropdown / text value from a GitHub Issue body.

    Matches patterns like:
        ### Phase

        Design

    Returns the first non-empty line after the heading.
    Raises ValueError if the field is not found.
    """
    pattern = rf"###\s+{re.escape(field_name)}\s*\n\s*\n\s*(.+)"
    match = re.search(pattern, body)
    if not match:
        raise ValueError(f"Field '{field_name}' not found in issue body")
    value = match.group(1).strip()
    if not value or value == "_No response_":
        raise ValueError(f"Field '{field_name}' has no value in issue body")
    return value


# ---------------------------------------------------------------------------
# gh CLI wrappers
# ---------------------------------------------------------------------------

def _run_gh(*args: str, input_text: Optional[str] = None) -> subprocess.CompletedProcess[str]:
    """Execute a `gh` CLI command and return the CompletedProcess."""
    cmd = ["gh", *args]
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            input=input_text,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"gh CLI not found: {exc}") from exc


def fetch_ready_issues(repo: str, trigger_label: str) -> list[Issue]:
    """Fetch open issues that carry *trigger_label* and convert to Issue models.

    Returns issues sorted by priority (P0 first).
    """
    result = _run_gh(
        "issue", "list",
        "--repo", repo,
        "--label", trigger_label,
        "--json", "number,title,body,labels,url",
        "-L", "200",
        "--state", "open",
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh issue list failed: {result.stderr.strip()}")

    raw_issues: list[dict] = json.loads(result.stdout)
    issues: list[Issue] = []

    for item in raw_issues:
        body: str = item.get("body", "")
        label_names = [lb["name"] for lb in item.get("labels", [])]
        number: int = item["number"]

        try:
            phase = extract_field(body, "Phase")
        except ValueError:
            phase = "unknown"

        try:
            feature_name = extract_field(body, "Feature Name")
        except ValueError:
            feature_name = f"issue-{number}"

        try:
            priority = extract_field(body, "Priority")
        except ValueError:
            priority = "P3"

        try:
            base_branch = extract_field(body, "Base Branch")
        except ValueError:
            base_branch = "main"

        try:
            epic_id = extract_field(body, "Epic ID")
        except ValueError:
            epic_id = ""

        issues.append(Issue(
            number=number,
            title=item.get("title", ""),
            body=body,
            url=item.get("url", ""),
            priority=priority,
            phase=phase,
            feature_name=feature_name,
            labels=label_names,
            base_branch=base_branch,
            epic_id=epic_id,
        ))

    issues.sort(key=_priority_key)
    return issues


# ---------------------------------------------------------------------------
# Label management
# ---------------------------------------------------------------------------

def ensure_label(repo: str, label: str, color: str = "", description: str = "") -> None:
    """Create a label if it does not already exist (idempotent)."""
    result = _run_gh(
        "label", "create", label,
        "--repo", repo,
        "--color", color or "ededed",
        "--description", description,
        "--force",
    )
    # --force makes it idempotent (updates if exists)
    if result.returncode != 0 and "already exists" not in result.stderr:
        pass  # Non-critical: label may already exist with different casing


def add_label(repo: str, issue_number: int, label: str) -> None:
    """Add a label to an issue."""
    result = _run_gh(
        "issue", "edit", str(issue_number),
        "--repo", repo,
        "--add-label", label,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to add label '{label}' to #{issue_number}: {result.stderr.strip()}"
        )


def remove_label(repo: str, issue_number: int, label: str) -> None:
    """Remove a label from an issue."""
    result = _run_gh(
        "issue", "edit", str(issue_number),
        "--repo", repo,
        "--remove-label", label,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to remove label '{label}' from #{issue_number}: {result.stderr.strip()}"
        )


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def post_comment(repo: str, issue_number: int, body: str) -> None:
    """Post a comment on an issue."""
    result = _run_gh(
        "issue", "comment", str(issue_number),
        "--repo", repo,
        "--body", body,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to comment on #{issue_number}: {result.stderr.strip()}"
        )


# ---------------------------------------------------------------------------
# GitHub Projects V2 — Status update
# ---------------------------------------------------------------------------

def _load_project_binding() -> Optional[dict]:
    """Load memory/github_project.yaml from the repository root."""
    path = os.path.join("memory", "github_project.yaml")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not data.get("project_number") or not data.get("owner"):
            return None
        return data
    except Exception:
        return None


# Cache for Status field metadata (populated on first use)
_project_status_cache: dict = {}


def _ensure_status_cache(owner: str, project_number: int, project_id: str) -> bool:
    """Discover and cache the Status field ID and option IDs."""
    if _project_status_cache.get("field_id"):
        return True

    result = _run_gh(
        "project", "field-list", str(project_number),
        "--owner", owner, "--format", "json",
    )
    if result.returncode != 0:
        return False

    try:
        fields = json.loads(result.stdout).get("fields", [])
    except (json.JSONDecodeError, TypeError):
        return False

    for field in fields:
        if field.get("name") == "Status" and field.get("options"):
            _project_status_cache["field_id"] = field["id"]
            _project_status_cache["options"] = {
                opt["name"]: opt["id"] for opt in field["options"]
            }
            _project_status_cache["project_id"] = project_id
            return True
    return False


def _find_project_item_id(owner: str, project_number: int, issue_number: int) -> Optional[str]:
    """Find the Project item ID for a given issue number."""
    result = _run_gh(
        "project", "item-list", str(project_number),
        "--owner", owner, "--format", "json",
    )
    if result.returncode != 0:
        return None

    try:
        items = json.loads(result.stdout).get("items", [])
    except (json.JSONDecodeError, TypeError):
        return None

    for item in items:
        content = item.get("content", {})
        if content.get("number") == issue_number:
            return item.get("id")
    return None


def update_project_status(issue_number: int, status_name: str) -> None:
    """Update GitHub Projects V2 Status field for an issue.

    Reads project binding from memory/github_project.yaml.
    Non-blocking: logs warnings on failure but does not raise.

    Args:
        issue_number: GitHub issue number
        status_name: Status option name (e.g. "Todo", "In progress", "Done")
    """
    binding = _load_project_binding()
    if not binding:
        return

    owner = binding["owner"]
    project_number = binding["project_number"]
    project_id = binding.get("project_id", "")

    if not _ensure_status_cache(owner, project_number, project_id):
        return

    option_id = _project_status_cache["options"].get(status_name)
    if not option_id:
        return

    item_id = _find_project_item_id(owner, project_number, issue_number)
    if not item_id:
        return

    _run_gh(
        "project", "item-edit",
        "--project-id", _project_status_cache["project_id"],
        "--id", item_id,
        "--field-id", _project_status_cache["field_id"],
        "--single-select-option-id", option_id,
    )


# ---------------------------------------------------------------------------
# Janitor helpers
# ---------------------------------------------------------------------------

def has_recent_pr(repo: str, feature_name: str, days: int) -> bool:
    """Return True if a merged PR for feature_name exists within the last `days` days.

    Uses `gh pr list --search` with merged: date filter.
    Returns False if the gh call fails (safe default for janitor exclusion logic).
    """
    from datetime import datetime, timezone, timedelta

    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    result = _run_gh(
        "pr", "list",
        "--repo", repo,
        "--state", "merged",
        "--search", f'"{feature_name}" in:title merged:>={since}',
        "--json", "number",
        "-L", "1",
    )
    if result.returncode != 0:
        return False
    try:
        data = json.loads(result.stdout)
        return len(data) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def has_open_janitor_issue(repo: str, feature_name: str) -> bool:
    """Return True if an open symphony:janitor issue already exists for feature_name.

    Used to deduplicate proposals so repeated scans don't spam the tracker.
    """
    title = f"Janitor: fix style/cyclomatic {feature_name}"
    result = _run_gh(
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--label", "symphony:janitor",
        "--search", f'"{title}" in:title',
        "--json", "number",
        "-L", "1",
    )
    if result.returncode != 0:
        return False
    try:
        return len(json.loads(result.stdout)) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def _ensure_label(repo: str, name: str, color: str, description: str) -> None:
    """Create a GitHub label if it does not exist (idempotent via --force)."""
    _run_gh(
        "label", "create", name,
        "--repo", repo,
        "--color", color,
        "--description", description,
        "--force",
    )


def create_janitor_issue(repo: str, feature_name: str, drift_report: str) -> int:
    """Create a GitHub Issue proposing janitor cleanup for feature_name.

    Ensures the symphony:janitor label exists before creating the issue.
    Returns the created issue number, or -1 on failure.
    """
    _ensure_label(repo, "symphony:janitor", "C2E0C6", "Janitor cleanup proposal")
    title = f"Janitor: fix style/cyclomatic {feature_name}"
    body = (
        f"## Janitor Proposal\n\n"
        f"Feature: `{feature_name}`\n\n"
        f"### Drift Report\n\n{drift_report}\n\n"
        f"---\n*Auto-generated by Symphony Janitor*"
    )
    result = _run_gh(
        "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
        "--label", "symphony:janitor",
    )
    if result.returncode != 0:
        return -1
    # gh issue create outputs the URL; extract issue number from it
    url = result.stdout.strip()
    try:
        return int(url.rstrip("/").split("/")[-1])
    except (ValueError, IndexError):
        return -1
