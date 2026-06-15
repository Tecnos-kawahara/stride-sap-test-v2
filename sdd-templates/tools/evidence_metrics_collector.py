#!/usr/bin/env python3
"""Evidence Metrics Collector - Collect CI metrics for outcome-based measurement.

Gathers metrics from coverage reports, test results, Turbo cache stats,
and APPROVAL.md timestamps to build a measurement infrastructure
for Evidence Pack.

Usage:
    python3 evidence_metrics_collector.py <project_root>
    python3 evidence_metrics_collector.py <project_root> --json
    python3 evidence_metrics_collector.py --test
"""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Metric collectors
# ---------------------------------------------------------------------------

def collect_coverage(project_root: Path) -> dict:
    """Collect coverage metrics from coverage-summary.json files.

    Searches for coverage/coverage-summary.json in project root and packages/.
    """
    result = {
        "found": False,
        "total_pct": 0.0,
        "line_pct": 0.0,
        "branch_pct": 0.0,
        "function_pct": 0.0,
        "sources": [],
    }

    # Search patterns for coverage files
    candidates = [
        project_root / "coverage" / "coverage-summary.json",
    ]
    # Monorepo: packages/*/coverage/
    packages_dir = project_root / "packages"
    if packages_dir.is_dir():
        for pkg in packages_dir.iterdir():
            if pkg.is_dir():
                candidates.append(pkg / "coverage" / "coverage-summary.json")

    total_lines = 0
    covered_lines = 0

    for cov_path in candidates:
        if not cov_path.is_file():
            continue
        try:
            data = json.loads(cov_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        total = data.get("total", {})
        if not total:
            continue

        result["found"] = True
        result["sources"].append(str(cov_path.relative_to(project_root)))

        lines = total.get("lines", {})
        result["line_pct"] = lines.get("pct", 0)
        result["branch_pct"] = total.get("branches", {}).get("pct", 0)
        result["function_pct"] = total.get("functions", {}).get("pct", 0)

        # Aggregate for total
        total_lines += lines.get("total", 0)
        covered_lines += lines.get("covered", 0)

    if total_lines > 0:
        result["total_pct"] = round(covered_lines / total_lines * 100, 2)

    return result


def collect_test_results(project_root: Path) -> dict:
    """Collect test results from JUnit XML or JSON reports."""
    result = {
        "found": False,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "execution_time_sec": 0.0,
        "sources": [],
    }

    # Search for vitest/jest JSON results
    json_candidates = list(project_root.rglob("test-results.json")) + \
                      list(project_root.rglob("junit.json"))

    for rpath in json_candidates:
        # Skip node_modules
        if "node_modules" in str(rpath):
            continue
        try:
            data = json.loads(rpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        result["found"] = True
        result["sources"].append(str(rpath.relative_to(project_root)))

        # Vitest format
        if "numTotalTests" in data:
            result["total"] += data.get("numTotalTests", 0)
            result["passed"] += data.get("numPassedTests", 0)
            result["failed"] += data.get("numFailedTests", 0)
            result["skipped"] += data.get("numPendingTests", 0)
            # Time in ms
            start = data.get("startTime", 0)
            end_results = data.get("testResults", [])
            if end_results:
                max_end = max((r.get("endTime", 0) for r in end_results), default=0)
                if start and max_end:
                    result["execution_time_sec"] += (max_end - start) / 1000
            continue

        # Jest format
        if "numTotalTests" not in data and "testResults" in data:
            for suite in data.get("testResults", []):
                result["total"] += suite.get("numPassingTests", 0) + suite.get("numFailingTests", 0)
                result["passed"] += suite.get("numPassingTests", 0)
                result["failed"] += suite.get("numFailingTests", 0)
            result["found"] = True

    # Also try JUnit XML (basic parsing)
    xml_candidates = list(project_root.rglob("junit.xml")) + \
                     list(project_root.rglob("test-results.xml"))

    for xpath in xml_candidates:
        if "node_modules" in str(xpath):
            continue
        try:
            content = xpath.read_text(encoding="utf-8")
        except OSError:
            continue

        result["found"] = True
        result["sources"].append(str(xpath.relative_to(project_root)))

        # Basic XML parsing without external deps
        tests_match = re.search(r'tests="(\d+)"', content)
        failures_match = re.search(r'failures="(\d+)"', content)
        errors_match = re.search(r'errors="(\d+)"', content)
        skipped_match = re.search(r'skipped="(\d+)"', content)
        time_match = re.search(r'time="([\d.]+)"', content)

        if tests_match:
            t = int(tests_match.group(1))
            f = int(failures_match.group(1)) if failures_match else 0
            e = int(errors_match.group(1)) if errors_match else 0
            s = int(skipped_match.group(1)) if skipped_match else 0
            result["total"] += t
            result["failed"] += f + e
            result["skipped"] += s
            result["passed"] += t - f - e - s
        if time_match:
            result["execution_time_sec"] += float(time_match.group(1))

    return result


def collect_cache_stats(project_root: Path) -> dict:
    """Estimate Turbo cache hit rate from dry-run output or .turbo cache dir."""
    result = {
        "found": False,
        "cache_hit_rate": 0.0,
        "total_tasks": 0,
        "cached_tasks": 0,
    }

    # Check .turbo directory for cache artifacts
    turbo_cache = project_root / ".turbo"
    if not turbo_cache.is_dir():
        turbo_cache = project_root / "node_modules" / ".cache" / "turbo"

    if turbo_cache.is_dir():
        result["found"] = True
        # Count cache entries
        cache_entries = list(turbo_cache.rglob("*.json"))
        result["total_tasks"] = max(len(cache_entries), 1)
        result["cached_tasks"] = len(cache_entries)
        if result["total_tasks"] > 0:
            result["cache_hit_rate"] = round(
                result["cached_tasks"] / result["total_tasks"] * 100, 1
            )

    return result


def collect_gate_lead_time(project_root: Path) -> dict:
    """Collect gate approval timestamps from APPROVAL.md to compute lead time."""
    result = {
        "found": False,
        "gate_timestamps": {},
        "total_lead_time_hours": 0.0,
    }

    # Search for APPROVAL.md files
    approval_files = list(project_root.rglob("APPROVAL.md"))

    for apath in approval_files:
        if "node_modules" in str(apath) or "sdd-templates" in str(apath):
            continue
        try:
            content = apath.read_text(encoding="utf-8")
        except OSError:
            continue

        result["found"] = True

        # Extract gate dates
        date_pattern = re.compile(r"日付:\s*(\d{4}-\d{2}-\d{2})")
        gate_pattern = re.compile(r"##\s*(Gate\s*\d+|Final)[^\n]*", re.IGNORECASE)

        current_gate = None
        for line in content.splitlines():
            gate_match = gate_pattern.match(line)
            if gate_match:
                current_gate = gate_match.group(1).strip()
                continue
            if current_gate:
                date_match = date_pattern.search(line)
                if date_match:
                    result["gate_timestamps"][current_gate] = date_match.group(1)
                    current_gate = None

    # Compute lead time between first and last gate
    if len(result["gate_timestamps"]) >= 2:
        dates = []
        for d in result["gate_timestamps"].values():
            try:
                dates.append(datetime.strptime(d, "%Y-%m-%d"))
            except ValueError:
                continue
        if len(dates) >= 2:
            dates.sort()
            delta = dates[-1] - dates[0]
            result["total_lead_time_hours"] = round(delta.total_seconds() / 3600, 1)

    return result


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def collect_all_metrics(project_root: Path) -> dict:
    """Collect all metrics from the project."""
    coverage = collect_coverage(project_root)
    tests = collect_test_results(project_root)
    cache = collect_cache_stats(project_root)
    gates = collect_gate_lead_time(project_root)

    return {
        "timestamp": datetime.now().isoformat(),
        "project_root": str(project_root),
        "coverage": coverage,
        "tests": tests,
        "cache": cache,
        "gate_lead_time": gates,
        "summary": {
            "coverage_pct": coverage["total_pct"],
            "test_pass_rate": round(
                tests["passed"] / max(tests["total"], 1) * 100, 1
            ),
            "test_execution_sec": tests["execution_time_sec"],
            "cache_hit_rate": cache["cache_hit_rate"],
            "gate_lead_time_hours": gates["total_lead_time_hours"],
        },
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_human_readable(metrics: dict) -> str:
    """Format metrics for terminal output."""
    lines = []
    lines.append("Evidence Metrics Report")
    lines.append("=" * 22)
    lines.append(f"Timestamp: {metrics['timestamp']}")
    lines.append("")

    s = metrics["summary"]

    # Coverage
    cov = metrics["coverage"]
    if cov["found"]:
        lines.append(f"[PASS] Coverage: {s['coverage_pct']}%")
        lines.append(f"  Line: {cov['line_pct']}% | Branch: {cov['branch_pct']}% | Function: {cov['function_pct']}%")
    else:
        lines.append("[SKIP] Coverage: no coverage-summary.json found")

    # Tests
    tests = metrics["tests"]
    if tests["found"]:
        status = "PASS" if tests["failed"] == 0 else "FAIL"
        lines.append(f"[{status}] Tests: {tests['passed']}/{tests['total']} passed "
                     f"({s['test_pass_rate']}%), {tests['skipped']} skipped")
        lines.append(f"  Execution time: {s['test_execution_sec']:.1f}s")
    else:
        lines.append("[SKIP] Tests: no test result files found")

    # Cache
    cache = metrics["cache"]
    if cache["found"]:
        lines.append(f"[PASS] Turbo Cache: {s['cache_hit_rate']}% hit rate "
                     f"({cache['cached_tasks']}/{cache['total_tasks']} tasks)")
    else:
        lines.append("[SKIP] Turbo Cache: no cache data found")

    # Gate Lead Time
    gates = metrics["gate_lead_time"]
    if gates["found"]:
        lines.append(f"[PASS] Gate Lead Time: {s['gate_lead_time_hours']}h total")
        for gate, date in sorted(gates["gate_timestamps"].items()):
            lines.append(f"  {gate}: {date}")
    else:
        lines.append("[SKIP] Gate Lead Time: no APPROVAL.md found")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evidence Metrics Collector - CI metrics for outcome-based measurement",
    )
    parser.add_argument("project_root", nargs="?", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.project_root:
        parser.error("project_root is required (or use --test)")

    root = Path(args.project_root)
    if not root.is_dir():
        print(f"Error: '{args.project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    metrics = collect_all_metrics(root)

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print(format_human_readable(metrics))


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Run self-tests using temporary directories."""
    print("Running evidence_metrics_collector.py self-tests...")
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

    # Test 1: Coverage parsing
    def test_coverage():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            cov_dir = p / "coverage"
            cov_dir.mkdir()
            (cov_dir / "coverage-summary.json").write_text(json.dumps({
                "total": {
                    "lines": {"total": 100, "covered": 85, "pct": 85},
                    "branches": {"total": 50, "covered": 40, "pct": 80},
                    "functions": {"total": 20, "covered": 18, "pct": 90},
                },
            }))
            r = collect_coverage(p)
            assert r["found"] is True, "expected found=True"
            assert r["line_pct"] == 85, f"expected line_pct=85, got {r['line_pct']}"
            assert r["branch_pct"] == 80, f"expected branch_pct=80, got {r['branch_pct']}"

    test("coverage parsing from coverage-summary.json", test_coverage)

    # Test 2: Test result parsing (JUnit XML)
    def test_junit():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "junit.xml").write_text("""<?xml version="1.0"?>
<testsuite name="tests" tests="10" failures="2" errors="1" skipped="1" time="3.45">
</testsuite>""")
            r = collect_test_results(p)
            assert r["found"] is True, "expected found=True"
            assert r["total"] == 10, f"expected total=10, got {r['total']}"
            assert r["failed"] == 3, f"expected failed=3 (2+1), got {r['failed']}"
            assert r["skipped"] == 1, f"expected skipped=1, got {r['skipped']}"
            assert r["passed"] == 6, f"expected passed=6, got {r['passed']}"
            assert abs(r["execution_time_sec"] - 3.45) < 0.01

    test("test result parsing from JUnit XML", test_junit)

    # Test 3: Cache rate calculation
    def test_cache():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            turbo = p / ".turbo"
            turbo.mkdir()
            for i in range(5):
                (turbo / f"task_{i}.json").write_text("{}")
            r = collect_cache_stats(p)
            assert r["found"] is True, "expected found=True"
            assert r["cached_tasks"] == 5, f"expected 5 cached, got {r['cached_tasks']}"
            assert r["cache_hit_rate"] == 100.0, f"expected 100% hit, got {r['cache_hit_rate']}"

    test("cache rate calculation from .turbo dir", test_cache)

    # Test 4: Trend computation (gate lead time)
    def test_gate_lead_time():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            specs = p / "specs" / "feat"
            specs.mkdir(parents=True)
            (specs / "APPROVAL.md").write_text("""# Approval

## Gate 1: Design

- [x] Approved

承認者: User
日付: 2026-01-10

---

## Gate 5: Tasking

- [x] Approved

承認者: User
日付: 2026-01-20

---
""")
            r = collect_gate_lead_time(p)
            assert r["found"] is True, "expected found=True"
            assert len(r["gate_timestamps"]) == 2, f"expected 2 gates, got {len(r['gate_timestamps'])}"
            assert r["total_lead_time_hours"] == 240.0, f"expected 240h (10 days), got {r['total_lead_time_hours']}"

    test("gate lead time from APPROVAL.md", test_gate_lead_time)

    # Test 5: Empty data handling
    def test_empty():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            m = collect_all_metrics(p)
            assert m["coverage"]["found"] is False
            assert m["tests"]["found"] is False
            assert m["cache"]["found"] is False
            assert m["gate_lead_time"]["found"] is False
            assert m["summary"]["coverage_pct"] == 0
            # Should not crash
            text = format_human_readable(m)
            assert "SKIP" in text

    test("empty data -> graceful handling", test_empty)

    # Test 6: Multi-run comparison (full collect)
    def test_full_collect():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            # Coverage
            cov = p / "coverage"
            cov.mkdir()
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {
                    "lines": {"total": 200, "covered": 180, "pct": 90},
                    "branches": {"total": 100, "covered": 75, "pct": 75},
                    "functions": {"total": 40, "covered": 38, "pct": 95},
                },
            }))
            # Tests
            (p / "junit.xml").write_text("""<?xml version="1.0"?>
<testsuite tests="50" failures="0" errors="0" skipped="2" time="12.5"/>""")
            # Cache
            turbo = p / ".turbo"
            turbo.mkdir()
            for i in range(3):
                (turbo / f"t{i}.json").write_text("{}")

            m = collect_all_metrics(p)
            assert m["summary"]["coverage_pct"] == 90.0, f"got {m['summary']['coverage_pct']}"
            assert m["summary"]["test_pass_rate"] == 96.0, f"got {m['summary']['test_pass_rate']}"
            assert m["summary"]["cache_hit_rate"] > 0

    test("full metrics collection", test_full_collect)

    print(f"\nAll {passed}/{total} self-tests passed." if passed == total else f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    main()
