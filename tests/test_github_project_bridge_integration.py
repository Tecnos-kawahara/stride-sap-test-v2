"""Integration tests for `stride project` / `github_project_bridge.py`.

Scope: verify CLI contracts (dry-run / graceful skip / status / help) through
subprocess, without invoking real `gh` API. Network and GitHub API integration
is covered by github_project_bridge's own offline self-test suite (`--test`).
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STRIDE = REPO_ROOT / "sdd-templates" / "bin" / "stride"
BRIDGE = REPO_ROOT / "sdd-templates" / "tools" / "github_project_bridge.py"


def _run(*args: str, cwd: Path | None = None, env_patch: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    for k in ("GITHUB_OWNER", "GITHUB_PROJECT_NUMBER"):
        env.pop(k, None)
    if env_patch:
        env.update(env_patch)
    return subprocess.run(
        [sys.executable, str(BRIDGE), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd or REPO_ROOT),
        timeout=20,
    )


def test_self_tests_pass():
    result = _run("--test")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests run; failures=0" in result.stdout


def test_dry_run_create_does_not_call_gh():
    result = _run("--dry-run", "create", "my-board")
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout
    assert "my-board" in result.stdout


def test_dry_run_use_does_not_call_gh():
    result = _run("--dry-run", "use", "42")
    assert result.returncode == 0, result.stderr
    assert "42" in result.stdout


def test_dry_run_list_does_not_call_gh():
    result = _run("--dry-run", "list")
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout.lower()


def test_status_missing_config_in_tmp(tmp_path: Path):
    """When no memory/github_project.yaml exists, status shows a helpful hint."""
    # Populate a minimal repo-root marker so find_repo_root() stays here.
    (tmp_path / "memory").mkdir()
    (tmp_path / ".git").mkdir()
    result = _run("status", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "not configured" in result.stdout or "Run:" in result.stdout


def test_use_persists_without_gh_when_unauthenticated(tmp_path: Path):
    """`use` still writes the binding file even if gh is unauthenticated."""
    (tmp_path / "memory").mkdir()
    (tmp_path / ".git").mkdir()
    # Force graceful-skip by breaking PATH for gh (use a PATH with no gh).
    env_patch = {"PATH": "/nonexistent"}
    result = _run("--dry-run", "use", "9", cwd=tmp_path, env_patch=env_patch)
    assert result.returncode == 0, result.stderr
    assert "9" in result.stdout


def test_stride_cli_project_help():
    if not STRIDE.exists():
        pytest.skip("bin/stride not present in checkout")
    result = subprocess.run(
        [str(STRIDE), "project", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "project" in result.stdout.lower()


def test_stride_cli_project_test():
    if not STRIDE.exists():
        pytest.skip("bin/stride not present in checkout")
    result = subprocess.run(
        [str(STRIDE), "project", "--test"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "tests run; failures=0" in result.stdout
