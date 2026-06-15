#!/usr/bin/env python3
"""
Run Resume Detector

Detects where an interrupted Run should resume based on which artifacts
already exist. Checks for artifacts in order to determine the furthest
completed phase.

Usage:
    python3 run_resume_detector.py <run_dir> [--verbose]

Exit codes:
    0 = Resume point detected successfully
    1 = Run directory not found or invalid
    2 = Error (missing args, etc.)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Artifact detection order
# ---------------------------------------------------------------------------

# (artifact_path, completed_phase, next_phase)
ARTIFACT_PHASES = [
    ("walkthrough.md", "walkthrough", "COMPLETE"),
    ("test_results.md", "testing", "WALKTHROUGH"),
    ("decision_log.md", "implementation", "TESTING"),
]

# Recommendations for each resume point
RECOMMENDATIONS = {
    "COMPLETE": "This run is already complete. No action needed.",
    "WALKTHROUGH": (
        "Testing appears complete. Resume from walkthrough phase.\n"
        "  Next action: Create walkthrough.md with implementation walkthrough."
    ),
    "TESTING": (
        "Implementation appears complete. Resume from testing phase.\n"
        "  Next action: Run tests and create test_results.md"
    ),
    "IMPLEMENTATION": (
        "Planning is complete. Resume from implementation phase.\n"
        "  Next action: Implement changes and create decision_log.md"
    ),
    "BEGINNING": (
        "No artifacts found. Start this run from the beginning.\n"
        "  Next action: Create .planning/ directory and plan.md"
    ),
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Result of a single artifact check."""
    status: str  # "FOUND", "MISSING"
    artifact: str
    optional: bool = False


# ---------------------------------------------------------------------------
# Artifact detection
# ---------------------------------------------------------------------------

def detect_artifacts(run_dir: Path) -> tuple[list[CheckResult], str]:
    """
    Check for artifacts in the run directory and determine resume point.

    Returns (results, resume_point) where resume_point is one of:
    COMPLETE, WALKTHROUGH, TESTING, IMPLEMENTATION, BEGINNING
    """
    results: list[CheckResult] = []
    resume_point = "BEGINNING"

    # Check main artifacts in order (highest phase first)
    for artifact_path, completed_phase, next_phase in ARTIFACT_PHASES:
        full_path = run_dir / artifact_path
        if full_path.exists():
            results.append(CheckResult("FOUND", artifact_path))
            # The first found artifact (highest phase) determines resume point
            if resume_point == "BEGINNING":
                resume_point = next_phase
        else:
            optional = artifact_path == "decision_log.md"
            results.append(CheckResult("MISSING", artifact_path, optional=optional))

    # Check .planning/ directory
    planning_dir = run_dir / ".planning"
    planning_plan = planning_dir / "plan.md"
    if planning_plan.exists():
        results.append(CheckResult("FOUND", ".planning/plan.md"))
        if resume_point == "BEGINNING":
            resume_point = "IMPLEMENTATION"
    elif planning_dir.exists():
        results.append(CheckResult("FOUND", ".planning/"))
        if resume_point == "BEGINNING":
            resume_point = "IMPLEMENTATION"
    else:
        results.append(CheckResult("MISSING", ".planning/plan.md"))

    return results, resume_point


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_output(
    run_dir: Path,
    results: list[CheckResult],
    resume_point: str,
    verbose: bool = False,
) -> str:
    """Format detection results for terminal output."""
    lines = []
    run_name = run_dir.name
    lines.append(f"Run Resume Detection: {run_name}")
    lines.append("\u2501" * 37)

    for r in results:
        tag = f"[{r.status}]"
        suffix = " (optional)" if r.optional else ""
        if verbose or r.status == "FOUND":
            lines.append(f"{tag} {r.artifact}{suffix}")
        elif not verbose and r.status == "MISSING" and not r.optional:
            lines.append(f"{tag} {r.artifact}")

    lines.append("")
    lines.append(f"Resume Point: {resume_point}")
    recommendation = RECOMMENDATIONS.get(resume_point, "")
    if recommendation:
        lines.append(f"Recommendation: {recommendation}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_detection(
    run_dir_str: str,
    verbose: bool = False,
) -> tuple[list[CheckResult], str, int]:
    """
    Run artifact detection on a run directory.

    Returns (results, resume_point, exit_code).
    """
    run_dir = Path(run_dir_str)
    if not run_dir.exists():
        return [], "", 1
    if not run_dir.is_dir():
        return [], "", 1

    results, resume_point = detect_artifacts(run_dir)
    return results, resume_point, 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect where an interrupted Run should resume.",
    )
    parser.add_argument(
        "run_dir",
        nargs="?",
        help="Path to specs/<feature>/runs/<WI-ID>/RUN-YYYYMMDD-HHMM/",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show all artifact checks including optional ones",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests",
    )

    args = parser.parse_args()

    if args.test:
        _run_self_tests()
        return

    if not args.run_dir:
        parser.error("the following arguments are required: run_dir")

    results, resume_point, exit_code = run_detection(args.run_dir, args.verbose)

    if exit_code != 0:
        print(f"Error: Run directory not found or invalid: {args.run_dir}")
        sys.exit(exit_code)

    run_dir = Path(args.run_dir)
    print(format_output(run_dir, results, resume_point, args.verbose))
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> None:
    """Run self-tests to validate detector behavior."""
    import tempfile

    print("Running self-tests...")

    # Test 1: Non-existent directory -> exit code 1
    results, resume_point, code = run_detection("/nonexistent/path/RUN-20260207-1430")
    assert code == 1, f"Test 1 failed: expected exit code 1, got {code}"
    print("  Test 1 passed: non-existent directory returns exit code 1")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Test 2: Empty run directory -> resume from BEGINNING
        run_dir = tmpdir / "RUN-20260207-1430"
        run_dir.mkdir(parents=True)
        results, resume_point, code = run_detection(str(run_dir))
        assert code == 0, f"Test 2 failed: expected exit code 0, got {code}"
        assert resume_point == "BEGINNING", \
            f"Test 2 failed: expected BEGINNING, got {resume_point}"
        print("  Test 2 passed: empty run directory resumes from BEGINNING")

        # Test 3: Only .planning/ exists -> resume from IMPLEMENTATION
        planning_dir = run_dir / ".planning"
        planning_dir.mkdir()
        (planning_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        results, resume_point, code = run_detection(str(run_dir))
        assert code == 0, f"Test 3 failed: expected exit code 0, got {code}"
        assert resume_point == "IMPLEMENTATION", \
            f"Test 3 failed: expected IMPLEMENTATION, got {resume_point}"
        print("  Test 3 passed: only .planning/ exists resumes from IMPLEMENTATION")

        # Test 4: .planning/ + test_results.md -> resume from WALKTHROUGH
        (run_dir / "test_results.md").write_text("# Test Results\n", encoding="utf-8")
        results, resume_point, code = run_detection(str(run_dir))
        assert code == 0, f"Test 4 failed: expected exit code 0, got {code}"
        assert resume_point == "WALKTHROUGH", \
            f"Test 4 failed: expected WALKTHROUGH, got {resume_point}"
        print("  Test 4 passed: .planning/ + test_results.md resumes from WALKTHROUGH")

        # Test 5: All artifacts present -> COMPLETE
        (run_dir / "walkthrough.md").write_text("# Walkthrough\n", encoding="utf-8")
        (run_dir / "decision_log.md").write_text("# Decisions\n", encoding="utf-8")
        results, resume_point, code = run_detection(str(run_dir))
        assert code == 0, f"Test 5 failed: expected exit code 0, got {code}"
        assert resume_point == "COMPLETE", \
            f"Test 5 failed: expected COMPLETE, got {resume_point}"
        # Verify all artifacts show as FOUND
        found_count = sum(1 for r in results if r.status == "FOUND")
        assert found_count == 4, \
            f"Test 5 failed: expected 4 FOUND, got {found_count}"
        print("  Test 5 passed: all artifacts present means COMPLETE")

        # Test 6: Only walkthrough.md (no test_results) -> COMPLETE
        # walkthrough is the final gate, so its presence means COMPLETE
        run_dir2 = tmpdir / "RUN-20260207-1500"
        run_dir2.mkdir(parents=True)
        (run_dir2 / "walkthrough.md").write_text("# Walkthrough\n", encoding="utf-8")
        results, resume_point, code = run_detection(str(run_dir2))
        assert code == 0, f"Test 6 failed: expected exit code 0, got {code}"
        assert resume_point == "COMPLETE", \
            f"Test 6 failed: expected COMPLETE, got {resume_point}"
        print("  Test 6 passed: only walkthrough.md means COMPLETE (final gate)")

    print("All 6 self-tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
