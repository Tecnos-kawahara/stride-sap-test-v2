"""Bridge to existing STRIDE CLI tools — wraps subprocess calls."""
from __future__ import annotations

import subprocess
from typing import NamedTuple, Optional

from symphony.logger import get_logger

logger = get_logger(__name__)


class ToolResult(NamedTuple):
    """Standard return from a STRIDE tool invocation."""

    exit_code: int
    stdout: str
    stderr: str


# ---------------------------------------------------------------------------
# Marker parsing
# ---------------------------------------------------------------------------

def _has_marker(output: str, marker: str) -> bool:
    """Check if a specific marker string appears in combined output."""
    return marker in output


def is_approval_pending(result: ToolResult) -> bool:
    """Check if the tool output indicates an APPROVAL_PENDING gate."""
    combined = result.stdout + result.stderr
    return _has_marker(combined, "APPROVAL_PENDING")


def is_all_gates_passed(result: ToolResult) -> bool:
    """Check if stride-lint reports all gates passed."""
    combined = result.stdout + result.stderr
    return _has_marker(combined, "ALL_GATES_PASSED") or (
        result.exit_code == 0 and "FAIL" not in combined
    )


# ---------------------------------------------------------------------------
# Tool wrappers
# ---------------------------------------------------------------------------

def _run(
    cmd: list[str],
    cwd: Optional[str] = None,
    timeout: int = 120,
) -> ToolResult:
    """Run a subprocess and return a ToolResult."""
    logger.debug("Running: %s (cwd=%s)", " ".join(cmd), cwd)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        return ToolResult(
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    except subprocess.TimeoutExpired:
        logger.warning("Command timed out: %s", " ".join(cmd))
        return ToolResult(exit_code=-1, stdout="", stderr="[TIMEOUT]")
    except FileNotFoundError as exc:
        logger.error("Command not found: %s — %s", cmd[0], exc)
        return ToolResult(exit_code=-2, stdout="", stderr=str(exc))


def lint(feature_path: str, cwd: Optional[str] = None) -> ToolResult:
    """Run stride-lint on a feature spec directory.

    Args:
        feature_path: path to the feature spec dir (e.g. "specs/my-feature")
        cwd: working directory for the subprocess
    """
    return _run(
        ["bash", "sdd-templates/tools/stride-lint", feature_path],
        cwd=cwd,
    )


def wi_sync(feature_id: str, cwd: Optional[str] = None) -> ToolResult:
    """Sync GitHub Issues → WI files for a feature.

    Args:
        feature_id: the feature identifier (e.g. "my-feature")
        cwd: working directory
    """
    return _run(
        ["python3", "sdd-templates/tools/stride_wi_sync.py", "--feature", feature_id],
        cwd=cwd,
    )


def pr_check(project_root: str, cwd: Optional[str] = None) -> ToolResult:
    """Run the PR readiness checker.

    Args:
        project_root: root directory of the project
        cwd: working directory
    """
    return _run(
        ["bash", "sdd-templates/bin/stride", "pr-check", project_root],
        cwd=cwd,
    )


def auto_continue(feature_path: str, cwd: Optional[str] = None) -> ToolResult:
    """Run stride auto-continue to advance through phases.

    Args:
        feature_path: path to the feature spec dir
        cwd: working directory
    """
    return _run(
        ["bash", "sdd-templates/bin/stride", "auto-continue", feature_path],
        cwd=cwd,
    )


def run_report(
    run_dir: str,
    issue_number: int,
    project: Optional[str] = None,
    owner: Optional[str] = None,
    cwd: Optional[str] = None,
) -> ToolResult:
    """Generate a run report and optionally post to GitHub Projects.

    Args:
        run_dir: directory containing run artifacts
        issue_number: GitHub issue number
        project: GitHub Projects board name (optional)
        owner: GitHub Projects owner (optional)
        cwd: working directory
    """
    cmd = [
        "python3", "sdd-templates/tools/run_report_generator.py",
        run_dir,
        "--post", "--issue", str(issue_number),
    ]
    if project:
        cmd.extend(["--project-fields", "--project", str(project)])
    if owner:
        cmd.extend(["--owner", owner])
    return _run(cmd, cwd=cwd)


def evaluate(
    feature_path: str,
    phase: str = "design",
    allow_degraded: bool = False,
    cwd: Optional[str] = None,
) -> ToolResult:
    """Run multi-model semantic evaluator on a feature spec directory.

    Args:
        feature_path: path to the feature spec dir (e.g. "specs/my-feature")
        phase: evaluation phase — "design", "specify", or "tasking"
        allow_degraded: if True, API errors produce WARN (exit 0) instead of ERROR (exit 2).
                        Default False — evaluator is a hard gate.
        cwd: working directory for the subprocess
    """
    cmd = [
        "sdd-templates/bin/stride", "evaluate",
        feature_path,
        "--phase", phase,
    ]
    if allow_degraded:
        cmd.append("--allow-provider-degraded")
    return _run(cmd, cwd=cwd)


def is_evaluation_passed(result: ToolResult) -> bool:
    """Check if the evaluator returned PASS or WARN (both treated as non-blocking)."""
    return result.exit_code == 0


def is_evaluation_failed(result: ToolResult) -> bool:
    """Check if the evaluator returned FAIL (semantic issues found, rework needed)."""
    return result.exit_code == 1


def wi_readiness(
    feature_path: str,
    wi_id: str,
    cwd: Optional[str] = None,
) -> ToolResult:
    """Check readiness of a specific Work Item.

    Args:
        feature_path: path to the feature spec dir
        wi_id: Work Item identifier (e.g. "WI-001")
        cwd: working directory
    """
    return _run(
        [
            "python3", "sdd-templates/tools/wi_readiness_checker.py",
            feature_path,
            wi_id,
        ],
        cwd=cwd,
    )
