"""Git worktree management for isolated agent workspaces."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from symphony.config import SymphonyConfig
from symphony.logger import get_logger

logger = get_logger(__name__)


def run_hook(
    hook_script: Optional[str],
    cwd: str,
    env: Optional[dict[str, str]] = None,
) -> None:
    """Run a shell hook script in *cwd* with optional extra env vars."""
    if not hook_script:
        return

    full_env = {**os.environ, **(env or {})}
    logger.info("Running hook: %s in %s", hook_script, cwd)

    try:
        result = subprocess.run(
            ["bash", "-c", hook_script],
            cwd=cwd,
            env=full_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
    except FileNotFoundError as exc:
        logger.warning("Hook executable not found: %s", exc)
        return
    except subprocess.TimeoutExpired:
        logger.warning("Hook timed out: %s", hook_script[:80])
        return

    if result.returncode != 0:
        logger.warning(
            "Hook exited with %d: %s", result.returncode, result.stderr.strip()
        )
    else:
        logger.debug("Hook stdout: %s", result.stdout.strip())


def create_workspace(
    config: SymphonyConfig,
    issue_id: int,
    branch_name: str,
    feature_name: str = "",
) -> str:
    """Create a git worktree for the given issue.

    Returns the absolute path to the new worktree directory.

    Raises:
        ValueError: if the resolved path escapes the workspace root.
        RuntimeError: if `git worktree add` fails.
    """
    ws_root = os.path.abspath(config.workspace.root)
    ws_path = os.path.join(ws_root, str(issue_id))

    # Security: ensure resolved path is under workspace root
    real_path = os.path.realpath(ws_path)
    real_root = os.path.realpath(ws_root)
    if not real_path.startswith(real_root + os.sep) and real_path != real_root:
        raise ValueError(
            f"Workspace path '{ws_path}' escapes root '{ws_root}'"
        )

    # Ensure root exists
    os.makedirs(ws_root, exist_ok=True)

    full_branch = f"{config.workspace.branch_prefix}{branch_name}"

    # If workspace already exists (e.g. retry), reuse it
    if os.path.isdir(ws_path):
        logger.info("Reusing existing workspace at %s (branch: %s)", ws_path, full_branch)
        return ws_path

    result = subprocess.run(
        ["git", "worktree", "add", ws_path, "-b", full_branch],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"git worktree add failed for #{issue_id}: {result.stderr.strip()}"
        )

    logger.info("Created workspace at %s (branch: %s)", ws_path, full_branch)

    # Run after_create hook
    run_hook(
        config.hooks.after_create,
        cwd=ws_path,
        env={"SYMPHONY_FEATURE": feature_name or str(issue_id)},
    )

    return ws_path


def cleanup_workspace(path: str) -> None:
    """Remove a git worktree (force)."""
    result = subprocess.run(
        ["git", "worktree", "remove", path, "--force"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )

    if result.returncode != 0:
        logger.warning(
            "git worktree remove failed for %s: %s",
            path,
            result.stderr.strip(),
        )
    else:
        logger.info("Cleaned up workspace: %s", path)
