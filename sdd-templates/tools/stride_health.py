#!/usr/bin/env python3
"""stride health — Runtime sensors for dead code and coverage decay.

Usage:
    python3 stride_health.py <project_root> [--runtime] [--json]
    python3 stride_health.py --test

Exit codes:
    0: HEALTHY
    1: ALERT (dead code or coverage decay exceeded policy)
    2: ERROR
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# pylint dead-code warning codes
DEAD_CODE_MSGS = {"W0611", "W0612", "W0613", "W0614"}

# Default coverage decay threshold (overridden by .env.local / env var at runtime)
_DEFAULT_COVERAGE_DECAY_THRESHOLD = 5.0


# ---------------------------------------------------------------------------
# .env.local loader
# ---------------------------------------------------------------------------

def _load_env_local(project_root: Path) -> None:
    """Load key=value pairs from <project_root>/.env.local into os.environ.

    Existing env vars are NOT overridden (shell wins over file).
    """
    env_file = project_root / ".env.local"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


# ---------------------------------------------------------------------------
# Dead code detection via pylint
# ---------------------------------------------------------------------------

def detect_dead_code(project_root: Path) -> dict[str, Any]:
    """Run pylint on tools/ to detect unused imports/variables."""
    result: dict[str, Any] = {"count": 0, "items": [], "detail": ""}

    tools_dir = project_root / "sdd-templates" / "tools"
    if not tools_dir.is_dir():
        result["detail"] = "sdd-templates/tools/ not found"
        return result

    # Find Python files (exclude test files and __pycache__)
    py_files = [
        str(f) for f in tools_dir.rglob("*.py")
        if "__pycache__" not in str(f) and not f.name.startswith("test_")
    ]
    if not py_files:
        result["detail"] = "no Python files found"
        return result

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pylint", "--disable=all",
             "--enable=" + ",".join(DEAD_CODE_MSGS),
             "--output-format=text", "--score=no"] + py_files,
            capture_output=True, text=True, timeout=60, cwd=str(project_root),
        )
        output = proc.stdout + proc.stderr
    except FileNotFoundError:
        result["detail"] = "pylint not found"
        return result
    except subprocess.TimeoutExpired:
        result["detail"] = "pylint timed out"
        return result

    items = []
    for line in output.splitlines():
        # pylint format: path:line:col: W0611(unused-import) message
        m = re.search(r"([A-Z]\d{4})\b", line)
        if m and m.group(1) in DEAD_CODE_MSGS:
            items.append(line.strip())

    result["count"] = len(items)
    result["items"] = items
    result["detail"] = f"{len(items)} dead code warning(s)" if items else "no dead code"
    return result


# ---------------------------------------------------------------------------
# Coverage decay detection
# ---------------------------------------------------------------------------

def detect_coverage_decay(project_root: Path) -> dict[str, Any]:
    """Compare current coverage against a stored baseline.

    Baseline is read from .coverage_baseline (plain float, e.g. "85.3").
    If no baseline exists, the current coverage becomes the new baseline.
    """
    result: dict[str, Any] = {"current_pct": None, "baseline_pct": None, "decay_pct": 0.0, "detail": ""}

    # Find coverage-summary.json
    cov_file = None
    for candidate in [
        project_root / "coverage" / "coverage-summary.json",
        project_root / "coverage-summary.json",
    ]:
        if candidate.is_file():
            cov_file = candidate
            break

    if cov_file is None:
        result["detail"] = "no coverage-summary.json found"
        return result

    try:
        data = json.loads(cov_file.read_text(encoding="utf-8"))
        current_pct = float(data.get("total", {}).get("lines", {}).get("pct", 0))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        result["detail"] = "cannot parse coverage-summary.json"
        return result

    result["current_pct"] = current_pct

    baseline_file = project_root / ".coverage_baseline"
    if not baseline_file.is_file():
        # First run — store current as baseline
        baseline_file.write_text(f"{current_pct:.2f}\n", encoding="utf-8")
        result["baseline_pct"] = current_pct
        result["detail"] = f"baseline established at {current_pct:.1f}%"
        return result

    try:
        baseline_pct = float(baseline_file.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        result["detail"] = "cannot read .coverage_baseline"
        return result

    result["baseline_pct"] = baseline_pct
    decay = baseline_pct - current_pct
    result["decay_pct"] = round(decay, 2)

    if decay > 0:
        result["detail"] = f"{current_pct:.1f}% (baseline {baseline_pct:.1f}%, decay {decay:.1f}%)"
    else:
        result["detail"] = f"{current_pct:.1f}% (baseline {baseline_pct:.1f}%, stable)"
    return result


def _get_coverage_decay_threshold(project_root: Path) -> float:
    """Return coverage decay threshold, loading .env.local first."""
    _load_env_local(project_root)
    return float(os.environ.get("COVERAGE_DECAY_THRESHOLD_PCT", str(_DEFAULT_COVERAGE_DECAY_THRESHOLD)))


# ---------------------------------------------------------------------------
# Alert judgment
# ---------------------------------------------------------------------------

def compute_alert(dead_code: dict, coverage_decay: dict, threshold: float = _DEFAULT_COVERAGE_DECAY_THRESHOLD) -> bool:
    """Return True if any runtime sensor is in alert state."""
    if dead_code.get("count", 0) > 0:
        return True
    decay = coverage_decay.get("decay_pct", 0.0)
    if decay > threshold:
        return True
    return False


# ---------------------------------------------------------------------------
# Main health check
# ---------------------------------------------------------------------------

def run_health_check(project_root: Path, runtime: bool = True) -> dict[str, Any]:
    """Run all health sensors and return aggregated result."""
    result: dict[str, Any] = {
        "alert": False,
        "sensors": {},
    }

    if runtime:
        dc = detect_dead_code(project_root)
        cd = detect_coverage_decay(project_root)
        result["sensors"]["dead_code"] = dc
        result["sensors"]["coverage_decay"] = cd
        result["alert"] = compute_alert(dc, cd, _get_coverage_decay_threshold(project_root))
    else:
        result["sensors"]["note"] = "runtime sensors skipped (use --runtime)"

    return result


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Self-tests using temporary directories."""
    import tempfile
    print("Running stride_health.py self-tests...")
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

    # Test 1: No tools dir -> detail not alert
    def t1():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            r = detect_dead_code(p)
            assert r["count"] == 0
            assert "not found" in r["detail"]

    test("no tools dir -> count=0", t1)

    # Test 2: No coverage-summary.json -> current_pct None
    def t2():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            r = detect_coverage_decay(p)
            assert r["current_pct"] is None
            assert "no coverage" in r["detail"]

    test("no coverage file -> current_pct None", t2)

    # Test 3: Coverage baseline establishment
    def t3():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            cov = p / "coverage"
            cov.mkdir()
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {"lines": {"pct": 85.0}}
            }))
            r = detect_coverage_decay(p)
            assert r["current_pct"] == 85.0
            assert "baseline established" in r["detail"]

    test("coverage baseline establishment", t3)

    # Test 4: Coverage decay above threshold -> alert
    def t4():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            cov = p / "coverage"
            cov.mkdir()
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {"lines": {"pct": 70.0}}
            }))
            (p / ".coverage_baseline").write_text("80.0\n")
            r = detect_coverage_decay(p)
            assert r["decay_pct"] == 10.0
            assert compute_alert({"count": 0}, r) is True

    test("coverage decay > threshold -> alert", t4)

    # Test 5: Coverage stable -> no alert
    def t5():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            cov = p / "coverage"
            cov.mkdir()
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {"lines": {"pct": 85.0}}
            }))
            (p / ".coverage_baseline").write_text("84.0\n")
            r = detect_coverage_decay(p)
            assert r["decay_pct"] == -1.0 or r["decay_pct"] <= 0
            assert compute_alert({"count": 0}, r) is False

    test("coverage stable -> no alert", t5)

    # Test 6: run_health_check returns alert=False on empty project (no runtime)
    def t6():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            r = run_health_check(p, runtime=False)
            assert r["alert"] is False
            assert "note" in r["sensors"]

    test("run_health_check no-runtime -> no alert", t6)

    print(f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="stride health — Runtime sensors for dead code and coverage decay",
    )
    parser.add_argument("project_root", nargs="?", help="Project root directory")
    parser.add_argument("--runtime", action="store_true",
                        help="Run runtime sensors (dead code + coverage decay)")
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

    result = run_health_check(root, runtime=args.runtime)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        alert_str = "ALERT" if result["alert"] else "HEALTHY"
        print(f"stride health: {alert_str}")
        sensors = result.get("sensors", {})
        dc = sensors.get("dead_code")
        if dc:
            print(f"  dead_code:       {dc.get('detail', '')}")
        cd = sensors.get("coverage_decay")
        if cd:
            print(f"  coverage_decay:  {cd.get('detail', '')}")
        note = sensors.get("note")
        if note:
            print(f"  {note}")

    sys.exit(1 if result["alert"] else 0)


if __name__ == "__main__":
    main()
