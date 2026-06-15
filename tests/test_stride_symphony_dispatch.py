"""E2E tests for `stride symphony <subcmd>` CLI integration.

Verifies that the `bin/stride` wrapper forwards to `symphony.cli` for all five
subcommands (run, dispatch, status, validate, janitor) and that the wrapper's
own help correctly lists them.

Tests that would hit the GitHub API are skipped when no GH_TOKEN / GITHUB_TOKEN
is available in the environment.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STRIDE = str(REPO_ROOT / "sdd-templates" / "bin" / "stride")
GH_TOKEN_AVAILABLE = bool(os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Invoke `sdd-templates/bin/stride` with the given args from REPO_ROOT."""
    return subprocess.run(
        [STRIDE, *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        **kwargs,
    )


def test_symphony_help_lists_five_subcommands():
    """`stride symphony --help` exits 0 and advertises all 5 subcommands."""
    r = _run(["symphony", "--help"])
    assert r.returncode == 0, f"stderr={r.stderr}"
    out = r.stdout + r.stderr
    for sub in ("run", "dispatch", "status", "validate", "janitor"):
        assert sub in out, f"'{sub}' missing from symphony help output"


def test_symphony_validate_reads_symphony_md_with_janitor():
    """`stride symphony validate` loads SYMPHONY.md (including janitor:) and returns OK."""
    r = _run(["symphony", "validate"], timeout=30)
    assert r.returncode == 0, f"stderr={r.stderr}"
    combined = r.stdout + r.stderr
    assert "OK" in combined
    # SYMPHONY.md in this repo declares a concrete tracker.repo; ensure loader saw it.
    assert "tracker.repo" in combined


def test_symphony_run_once_dry_run_exits_cleanly():
    """`stride symphony run --once --dry-run` completes without hitting GitHub."""
    # Explicitly clear tokens so the test exercises the offline dry-run path.
    env = dict(os.environ)
    env.pop("GH_TOKEN", None)
    env.pop("GITHUB_TOKEN", None)
    r = subprocess.run(
        [STRIDE, "symphony", "run", "--once", "--dry-run"],
        capture_output=True, text=True, cwd=str(REPO_ROOT), env=env, timeout=60,
    )
    # Dry-run may log a warning about fetching issues when offline, but the
    # loop must still exit with status 0.
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


def test_symphony_dispatch_unknown_issue_errors():
    """`stride symphony dispatch --issue <nonexistent>` exits non-zero."""
    if not GH_TOKEN_AVAILABLE:
        pytest.skip("requires GH_TOKEN / GITHUB_TOKEN to talk to GitHub")
    r = _run(["symphony", "dispatch", "--issue", "99999999"], timeout=60)
    assert r.returncode != 0, (
        f"Expected non-zero exit for nonexistent issue, got 0.\n"
        f"stdout={r.stdout}\nstderr={r.stderr}"
    )


def test_symphony_janitor_dry_run_reflects_config_state():
    """`stride symphony janitor --dry-run` honours janitor.enabled and skips GitHub."""
    r = _run(["symphony", "janitor", "--dry-run"], timeout=30)
    assert r.returncode == 0, f"stderr={r.stderr}"
    combined = r.stdout + r.stderr
    # Either the janitor is disabled (then output is 'skipped'), or it's enabled
    # and the dry-run prints the scope summary. Both paths prove the CLI wired
    # through and read the config.
    assert ("skipped" in combined) or ("dry-run" in combined), (
        f"Janitor output did not indicate skip or dry-run:\n{combined}"
    )
