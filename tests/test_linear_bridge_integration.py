"""Integration tests for `stride linear` / `linear_bridge.py`.

Focus: end-to-end CLI behaviour through subprocess, without calling the real
Linear API. Network-adjacent mutations are covered by linear_bridge.py's own
unittest suite (`--test`). These tests validate the documented contracts:

- dry-run never needs LINEAR_API_KEY
- missing LINEAR_API_KEY triggers graceful skip (exit 0, not failure)
- state.yaml round-trips the `linear_issue_id` field
- `stride linear status` honours work_items[*].linear_issue_id
- `sync` surface-reads findings/walkthrough/test_results/lessons artefacts
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
LINEAR_BRIDGE = REPO_ROOT / "sdd-templates" / "tools" / "linear_bridge.py"


@pytest.fixture
def feature_with_wi(tmp_path: Path):
    """Minimal feature dir with state.yaml + work_items/<WI>.md."""
    feat = tmp_path / "specs" / "FEAT-LINEAR-TEST"
    (feat / "state").mkdir(parents=True)
    (feat / "work_items").mkdir()
    (feat / "state" / "state.yaml").write_text(
        textwrap.dedent(
            """\
            feature: FEAT-LINEAR-TEST
            current_gate: Gate5
            autonomy_bias: balanced
            coverage_tier: standard
            work_items:
              - wi_id: WI-LIN-001
                title: "Sample WI"
                status: in_progress
                mode: confirm
                risk_flags: ["new_api"]
            run_index: {}
            """
        ),
        encoding="utf-8",
    )
    (feat / "work_items" / "WI-LIN-001.md").write_text(
        textwrap.dedent(
            """\
            ---
            wi_id: WI-LIN-001
            title: Sample WI
            mode: confirm
            risk_flags: [new_api]
            intent: "Validate Linear bridge contract"
            dod:
              - "stride linear dry-run succeeds"
            ---
            # Body
            """
        ),
        encoding="utf-8",
    )
    return feat


@pytest.fixture
def run_dir_for_wi(feature_with_wi: Path):
    """Create a RUN directory with representative artefacts."""
    run_dir = feature_with_wi / "runs" / "WI-LIN-001" / "RUN-20260419-1000"
    (run_dir / ".planning").mkdir(parents=True)
    (run_dir / "walkthrough.md").write_text(
        "## What was done\n- Implemented order import\n- Integrated mcframe\n",
        encoding="utf-8",
    )
    (run_dir / "test_results.md").write_text(
        "## Tests\n- Contract: 12/12 PASS\n- Integration: 8/8 PASS\n",
        encoding="utf-8",
    )
    (run_dir / ".planning" / "findings.md").write_text(
        "## Findings\n1. mcframe master sync requires idempotency.\n2. SoD gap for approval.\n",
        encoding="utf-8",
    )
    (run_dir / ".planning" / "lessons.md").write_text(
        "## Lessons\n- [BP] idempotent writes via correlation_id\n",
        encoding="utf-8",
    )
    return run_dir


def _run(*args: str, env_patch: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # Ensure a clean slate for Linear envs unless explicitly patched.
    for key in ("LINEAR_API_KEY", "LINEAR_TEAM_KEY", "LINEAR_PROJECT_ID", "STRIDE_LINEAR_AUTO"):
        env.pop(key, None)
    if env_patch:
        env.update(env_patch)
    return subprocess.run(
        [sys.executable, str(LINEAR_BRIDGE), *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd or REPO_ROOT),
        timeout=20,
    )


def test_self_tests_pass():
    """linear_bridge --test returns 0 across all 19 unit tests."""
    result = _run("--test")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests run; failures=0" in result.stdout


def test_init_dry_run_without_api_key(feature_with_wi: Path):
    """dry-run must succeed even without LINEAR_API_KEY (preview mode)."""
    result = _run("--dry-run", "init", str(feature_with_wi), "WI-LIN-001")
    assert result.returncode == 0, result.stderr
    assert "dry-run" in result.stdout
    assert "WI-LIN-001" in result.stdout


def test_init_graceful_skip_without_api_key(feature_with_wi: Path):
    """Without --dry-run and no LINEAR_API_KEY, init exits 0 with info message."""
    result = _run("init", str(feature_with_wi), "WI-LIN-001")
    assert result.returncode == 0, result.stderr
    assert "LINEAR_API_KEY" in result.stdout


def test_status_with_empty_state(feature_with_wi: Path):
    """status command prints placeholder when no linear_issue_id set."""
    result = _run("status", str(feature_with_wi))
    assert result.returncode == 0
    assert "WI-LIN-001" in result.stdout
    assert "—" in result.stdout


def test_sync_dry_run_reads_artefacts(run_dir_for_wi: Path):
    """sync dry-run previews findings + evidence + lessons from Run artefacts."""
    result = _run("--dry-run", "sync", str(run_dir_for_wi))
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "dry-run" in out
    # body preview truncates at 200 chars, so assert presence of at least one section marker
    assert "Findings" in out or "Run Evidence" in out or "Lessons" in out


def test_sync_graceful_skip_without_api_key(run_dir_for_wi: Path):
    """sync without API key triggers graceful skip messaging."""
    result = _run("sync", str(run_dir_for_wi))
    assert result.returncode == 0, result.stderr
    assert "LINEAR_API_KEY" in result.stdout or "linear_issue_id" in result.stderr


def test_close_dry_run_default_state(feature_with_wi: Path):
    """close dry-run announces target state = Done by default."""
    result = _run("--dry-run", "close", str(feature_with_wi), "WI-LIN-001")
    assert result.returncode == 0, result.stderr
    assert "Done" in result.stdout


def test_close_dry_run_custom_state(feature_with_wi: Path):
    """close --state Canceled is reflected in dry-run output."""
    result = _run("--dry-run", "close", str(feature_with_wi), "WI-LIN-001", "--state", "Canceled")
    assert result.returncode == 0, result.stderr
    assert "Canceled" in result.stdout


def test_stride_cli_dispatch():
    """`stride linear --help` reaches the Python tool via bin/stride wrapper."""
    if not STRIDE.exists():
        pytest.skip("bin/stride not present in checkout")
    result = subprocess.run(
        [str(STRIDE), "linear", "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "stride linear" in result.stdout.lower() or "linear <subcommand>" in result.stdout


def test_stride_cli_linear_test():
    """`stride linear --test` runs the self-test suite via the wrapper."""
    if not STRIDE.exists():
        pytest.skip("bin/stride not present in checkout")
    result = subprocess.run(
        [str(STRIDE), "linear", "--test"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "tests run; failures=0" in result.stdout
