#!/usr/bin/env python3
"""stride harness-report — Harness coverage summary.

Collects coverage_pct, controls (checks in place), and gaps (missing coverage)
from the project's test harness infrastructure.

Usage:
    python3 stride_harness_report.py <project_root> [--json]
    python3 stride_harness_report.py --test

Exit codes:
    0: SUCCESS
    1: GAPS_FOUND
    2: ERROR
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Controls inventory
# ---------------------------------------------------------------------------

def _has_pr_readiness(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "tools" / "pr_readiness_checker.py").is_file()


def _has_stride_lint(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "tools" / "stride_lint.py").is_file()


def _has_spec_drift(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "tools" / "spec_drift_detector.py").is_file()


def _has_security_checker(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "tools" / "stride_security_checker.py").is_file()


def _has_runtime_sensors(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "tools" / "stride_health.py").is_file()


def _has_semantic_evaluator(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "tools" / "multi_model_evaluator.py").is_file()


def _has_phase_gate_hook(project_root: Path) -> bool:
    hooks = project_root / "sdd-templates" / "hooks"
    return any(hooks.rglob("phase_gate_hook.py")) if hooks.is_dir() else False


def _has_post_edit_guard(project_root: Path) -> bool:
    return (project_root / "sdd-templates" / "hooks" / "post_edit_guard.py").is_file()


CONTROLS = [
    ("pr-readiness",     "PR quality gate (7+ checks)",        _has_pr_readiness),
    ("stride-lint",      "SDD artifact linter",                 _has_stride_lint),
    ("spec-drift",       "Spec/contract drift detector",        _has_spec_drift),
    ("security-checker", "Security audit (daily/audit)",        _has_security_checker),
    ("runtime-sensors",  "Dead code + coverage decay",          _has_runtime_sensors),
    ("semantic-eval",    "LLM semantic quality gate",           _has_semantic_evaluator),
    ("phase-gate-hook",  "Phase gate enforcement hook",         _has_phase_gate_hook),
    ("post-edit-guard",  "Post-edit YAML guard",                _has_post_edit_guard),
]


# ---------------------------------------------------------------------------
# Coverage pct from coverage-summary.json
# ---------------------------------------------------------------------------

def _read_coverage_pct(project_root: Path) -> float | None:
    for candidate in [
        project_root / "coverage" / "coverage-summary.json",
        project_root / "coverage-summary.json",
    ]:
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                return float(data.get("total", {}).get("lines", {}).get("pct", 0))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                pass
    return None


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------

def _find_gaps(project_root: Path, controls_status: list[dict]) -> list[str]:
    """Identify harness gaps based on missing controls and project structure."""
    gaps = []

    for c in controls_status:
        if not c["present"]:
            gaps.append(f"missing control: {c['name']}")

    # Check for test files
    tests_dir = project_root / "tests"
    symphony_tests = project_root / "symphony" / "tests"
    has_tests = (
        (tests_dir.is_dir() and any(tests_dir.rglob("test_*.py")))
        or (symphony_tests.is_dir() and any(symphony_tests.rglob("test_*.py")))
    )
    if not has_tests:
        gaps.append("no test files found (tests/ or symphony/tests/)")

    # Check for CI configuration
    ci_dir = project_root / ".github" / "workflows"
    if not (ci_dir.is_dir() and any(ci_dir.glob("*.yml"))):
        gaps.append("no GitHub Actions CI workflow found")

    return gaps


# ---------------------------------------------------------------------------
# Main report
# ---------------------------------------------------------------------------

def build_harness_report(project_root: Path) -> dict[str, Any]:
    """Build the harness coverage report."""
    controls_status = [
        {
            "name": name,
            "description": description,
            "present": check_fn(project_root),
        }
        for name, description, check_fn in CONTROLS
    ]

    coverage_pct = _read_coverage_pct(project_root)
    gaps = _find_gaps(project_root, controls_status)

    controls_present = sum(1 for c in controls_status if c["present"])
    controls_total = len(controls_status)

    return {
        "coverage_pct": coverage_pct,
        "controls": {
            "present": controls_present,
            "total": controls_total,
            "pct": round(controls_present / controls_total * 100, 1) if controls_total else 0.0,
            "items": controls_status,
        },
        "gaps": gaps,
        "summary": "FULL" if not gaps else f"{len(gaps)} gap(s)",
    }


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    import tempfile
    print("Running stride_harness_report.py self-tests...")
    passed = 0
    total = 0

    def test(name, func):
        nonlocal passed, total
        total += 1
        try:
            func()
            print(f"  Test {total} passed: {name}")
            passed += 1
        except AssertionError as e:
            print(f"  Test {total} FAILED: {name} -- {e}")

    def t1():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            r = build_harness_report(p)
            assert "coverage_pct" in r
            assert "controls" in r
            assert "gaps" in r
            assert len(r["gaps"]) > 0

    test("empty project has gaps", t1)

    def t2():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            r = build_harness_report(p)
            assert r["coverage_pct"] is None

    test("no coverage file -> coverage_pct None", t2)

    def t3():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            cov = p / "coverage"
            cov.mkdir()
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {"lines": {"pct": 87.5}}
            }))
            r = build_harness_report(p)
            assert r["coverage_pct"] == 87.5

    test("coverage file -> coverage_pct=87.5", t3)

    def t4():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tools = p / "sdd-templates" / "tools"
            tools.mkdir(parents=True)
            (tools / "pr_readiness_checker.py").write_text("")
            (tools / "stride_lint.py").write_text("")
            r = build_harness_report(p)
            assert r["controls"]["present"] >= 2

    test("present controls counted", t4)

    def t5():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            r = build_harness_report(p)
            gap_labels = " ".join(r["gaps"])
            assert "test" in gap_labels.lower()

    test("no tests -> gap detected", t5)

    def t6():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tools = p / "sdd-templates" / "tools"
            tools.mkdir(parents=True)
            hooks = p / "sdd-templates" / "hooks"
            hooks.mkdir(parents=True)
            for name in [
                "pr_readiness_checker.py", "stride_lint.py", "spec_drift_detector.py",
                "stride_security_checker.py", "stride_health.py", "multi_model_evaluator.py",
            ]:
                (tools / name).write_text("")
            (hooks / "phase_gate_hook.py").write_text("")
            (hooks / "post_edit_guard.py").write_text("")
            tests = p / "tests"
            tests.mkdir()
            (tests / "test_sample.py").write_text("")
            ci = p / ".github" / "workflows"
            ci.mkdir(parents=True)
            (ci / "ci.yml").write_text("")
            r = build_harness_report(p)
            assert len(r["gaps"]) == 0
            assert r["summary"] == "FULL"

    test("all controls present -> FULL", t6)

    print(f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="stride harness-report — Harness coverage summary",
    )
    parser.add_argument("project_root", nargs="?", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.project_root:
        parser.error("project_root is required")

    root = Path(args.project_root)
    if not root.is_dir():
        print(f"Error: '{args.project_root}' is not a directory", file=sys.stderr)
        sys.exit(2)

    report = build_harness_report(root)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        cov_str = f"{report['coverage_pct']:.1f}%" if report["coverage_pct"] is not None else "N/A"
        ctrl = report["controls"]
        print(f"Harness Report: {report['summary']}")
        print(f"  coverage_pct:  {cov_str}")
        print(f"  controls:      {ctrl['present']}/{ctrl['total']} ({ctrl['pct']}%)")
        if report["gaps"]:
            print(f"  gaps ({len(report['gaps'])}):")
            for gap in report["gaps"]:
                print(f"    - {gap}")

    sys.exit(1 if report["gaps"] else 0)


if __name__ == "__main__":
    main()
