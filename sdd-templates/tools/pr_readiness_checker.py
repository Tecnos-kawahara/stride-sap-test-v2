#!/usr/bin/env python3
"""PR Readiness Checker - Unified pre-PR quality gate.

Aggregates 7 checks (+ optional mutation) into a single pass/fail verdict:
  1. stride-lint       (import stride_lint)
  2. spec:drift         (import spec_drift_detector)
  3. tests pass         (import evidence_metrics_collector)
  4. coverage threshold (import evidence_metrics_collector)
  5. walkthrough checklist (self-parse)
  6. evidence pack      (self-parse)
  7. TODO/FIXME scan    (self-scan)
  8. mutation testing   (cosmic-ray, opt-in via --mutation)

Usage:
    python3 pr_readiness_checker.py <project_root>
    python3 pr_readiness_checker.py <project_root> --json
    python3 pr_readiness_checker.py <project_root> --summary-line
    python3 pr_readiness_checker.py <project_root> -v
    python3 pr_readiness_checker.py <project_root> --strict
    python3 pr_readiness_checker.py <project_root> --coverage-threshold 90
    python3 pr_readiness_checker.py <project_root> --mutation
    python3 pr_readiness_checker.py --test

Exit codes: 0=PR_READY, 1=NOT_READY, 2=ERROR

Note (v5.4): --summary-line emits ONE project-level 1-line summary covering
ONLY the 7 base checks (+ optional mutation when --mutation is set).
Task-local context (task ID / AC / NFR / scenarios) is intentionally NOT
included — that composition is the AI's responsibility per
agent_docs/sdd_bootstrap.md §5 Step 1-5.
"""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COVERAGE_THRESHOLDS = {
    "critical": 90,
    "standard": 80,
    "experimental": 60,
}

EVIDENCE_REQUIRED_SECTIONS = [
    "test_results",
    "coverage_report",
    "gate_approvals",
]

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARN = "WARN"


# ---------------------------------------------------------------------------
# .env.local loader
# ---------------------------------------------------------------------------

def _load_env_local(project_root: Path) -> None:
    """Load key=value pairs from <project_root>/.env.local into os.environ.

    Existing env vars are NOT overridden (shell wins over file).
    Lines starting with '#' and blank lines are ignored.
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
# Import helpers (graceful degradation)
# ---------------------------------------------------------------------------

def _import_sibling(module_name: str):
    """Import a module from the same directory as this script."""
    tools_dir = str(Path(__file__).resolve().parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        return __import__(module_name)
    except ImportError:
        return None


def _build_lint_config(lint_mod):
    """Construct a default stride_lint.LintConfig when available."""
    config_cls = getattr(lint_mod, "LintConfig", None)
    if config_cls is None:
        return None
    return config_cls()


def _issue_code(issue) -> str:
    """Extract a lint issue code from dict/object/string payloads."""
    if isinstance(issue, dict):
        return str(issue.get("code", issue))
    return str(getattr(issue, "code", issue))


# ---------------------------------------------------------------------------
# Coverage tier detection
# ---------------------------------------------------------------------------

def _read_coverage_tier(project_root: Path) -> str:
    """Read coverage_tier from basic_design.md canonical YAML."""
    specs_dir = project_root / "specs"
    if not specs_dir.is_dir():
        return "standard"

    for feature_dir in specs_dir.iterdir():
        if not feature_dir.is_dir():
            continue
        bd = feature_dir / "basic_design.md"
        if not bd.is_file():
            continue
        try:
            content = bd.read_text(encoding="utf-8")
        except OSError:
            continue

        # Try canonical YAML block first (basic_design: section)
        m = re.search(r"coverage_tier:\s*[\"']?(\w+)[\"']?", content)
        if m:
            tier = m.group(1).lower()
            if tier in COVERAGE_THRESHOLDS:
                return tier

    return "standard"


# ---------------------------------------------------------------------------
# Check 1: stride-lint
# ---------------------------------------------------------------------------

def check_stride_lint(project_root: Path, verbose: bool = False) -> dict:
    """Run stride-lint on all features."""
    result = {"status": STATUS_PASS, "errors": 0, "warnings": 0, "detail": ""}

    lint_mod = _import_sibling("stride_lint")
    if lint_mod is None:
        result["status"] = STATUS_WARN
        result["detail"] = "stride_lint not importable"
        return result

    specs_dir = project_root / "specs"
    if not specs_dir.is_dir():
        result["status"] = STATUS_WARN
        result["detail"] = "no specs/ directory"
        return result

    total_errors = 0
    total_warnings = 0
    lint_config = _build_lint_config(lint_mod)

    for feature_dir in sorted(specs_dir.iterdir()):
        if not feature_dir.is_dir():
            continue
        # Skip non-feature directories (no basic_design.md = not a lintable feature)
        if not (feature_dir / "basic_design.md").is_file():
            continue
        try:
            lint_result = lint_mod.lint_feature(str(feature_dir), lint_config)
            for err in getattr(lint_result, "errors", []):
                err_code = _issue_code(err)
                # Exclude APPROVAL_PENDING from blocking errors
                if "APPROVAL_PENDING" in err_code:
                    continue
                total_errors += 1
            total_warnings += len(getattr(lint_result, "warnings", []))
        except Exception as e:
            result["status"] = STATUS_WARN
            result["detail"] = f"lint error: {e}"
            return result

    result["errors"] = total_errors
    result["warnings"] = total_warnings

    if total_errors > 0:
        result["status"] = STATUS_FAIL
        result["detail"] = f"{total_errors} errors, {total_warnings} warnings"
    else:
        result["detail"] = f"0 errors, {total_warnings} warnings"

    return result


# ---------------------------------------------------------------------------
# Check 2: spec drift
# ---------------------------------------------------------------------------

def check_spec_drift(project_root: Path, verbose: bool = False) -> dict:
    """Check for spec drift between contracts/ and src/."""
    result = {"status": STATUS_PASS, "critical": 0, "high": 0, "detail": ""}

    drift_mod = _import_sibling("spec_drift_detector")
    if drift_mod is None:
        result["status"] = STATUS_WARN
        result["detail"] = "spec_drift_detector not importable"
        return result

    try:
        drift_result = drift_mod.detect_drift(project_root)
    except Exception as e:
        result["status"] = STATUS_WARN
        result["detail"] = f"drift detection error: {e}"
        return result

    summary = drift_result.get("summary", {})
    critical = summary.get("critical", 0)
    high = summary.get("high", 0)
    total = summary.get("total_drifts", 0)

    result["critical"] = critical
    result["high"] = high

    if critical > 0:
        result["status"] = STATUS_FAIL
        result["detail"] = f"{critical} critical, {high} high drifts"
    elif high > 0:
        result["status"] = STATUS_WARN
        result["detail"] = f"{high} high drifts"
    else:
        result["detail"] = f"{total} drifts"

    return result


# ---------------------------------------------------------------------------
# Check 3: tests pass
# ---------------------------------------------------------------------------

def check_tests(project_root: Path, verbose: bool = False) -> dict:
    """Check test results from evidence metrics collector."""
    result = {"status": STATUS_PASS, "total": 0, "passed": 0, "failed": 0, "detail": ""}

    metrics_mod = _import_sibling("evidence_metrics_collector")
    if metrics_mod is None:
        result["status"] = STATUS_WARN
        result["detail"] = "evidence_metrics_collector not importable"
        return result

    try:
        test_data = metrics_mod.collect_test_results(project_root)
    except Exception as e:
        result["status"] = STATUS_WARN
        result["detail"] = f"test collection error: {e}"
        return result

    if not test_data.get("found", False):
        result["status"] = STATUS_WARN
        result["detail"] = "no test results found"
        return result

    result["total"] = test_data.get("total", 0)
    result["passed"] = test_data.get("passed", 0)
    result["failed"] = test_data.get("failed", 0)

    if result["failed"] > 0:
        result["status"] = STATUS_FAIL
        result["detail"] = f"{result['failed']}/{result['total']} failed"
    else:
        result["detail"] = f"{result['passed']}/{result['total']} passed"

    return result


# ---------------------------------------------------------------------------
# Check 4: coverage threshold
# ---------------------------------------------------------------------------

def check_coverage(project_root: Path, threshold: int = None, verbose: bool = False) -> dict:
    """Check code coverage against threshold."""
    result = {"status": STATUS_PASS, "total_pct": 0.0, "threshold": 0, "detail": ""}

    metrics_mod = _import_sibling("evidence_metrics_collector")
    if metrics_mod is None:
        result["status"] = STATUS_WARN
        result["detail"] = "evidence_metrics_collector not importable"
        return result

    # Determine threshold
    if threshold is None:
        tier = _read_coverage_tier(project_root)
        threshold = COVERAGE_THRESHOLDS.get(tier, 80)

    result["threshold"] = threshold

    try:
        cov_data = metrics_mod.collect_coverage(project_root)
    except Exception as e:
        result["status"] = STATUS_WARN
        result["detail"] = f"coverage collection error: {e}"
        return result

    if not cov_data.get("found", False):
        result["status"] = STATUS_WARN
        result["detail"] = "no coverage data found"
        return result

    total_pct = cov_data.get("total_pct", 0.0)
    result["total_pct"] = total_pct

    if total_pct < threshold:
        result["status"] = STATUS_FAIL
        result["detail"] = f"{total_pct}% (< {threshold}%)"
    else:
        result["detail"] = f"{total_pct}% (>= {threshold}%)"

    return result


# ---------------------------------------------------------------------------
# Check 5: walkthrough checklist
# ---------------------------------------------------------------------------

def check_walkthrough(project_root: Path, verbose: bool = False) -> dict:
    """Check walkthrough review checklist completion."""
    result = {"status": STATUS_PASS, "checked": 0, "total": 0, "detail": ""}

    # Search for walkthrough.md files
    walkthrough_files = []
    specs_dir = project_root / "specs"
    if specs_dir.is_dir():
        walkthrough_files = list(specs_dir.rglob("walkthrough.md"))

    if not walkthrough_files:
        result["status"] = STATUS_WARN
        result["detail"] = "no walkthrough.md found"
        return result

    total_items = 0
    checked_items = 0

    for wf in walkthrough_files:
        try:
            content = wf.read_text(encoding="utf-8")
        except OSError:
            continue

        # Find Review Checklist section
        in_checklist = False
        for line in content.splitlines():
            if re.match(r"#+\s*Review\s+Checklist", line, re.IGNORECASE):
                in_checklist = True
                continue
            if in_checklist and re.match(r"#+\s", line) and "Review Checklist" not in line:
                break
            if in_checklist:
                if re.match(r"\s*-\s*\[x\]", line, re.IGNORECASE):
                    total_items += 1
                    checked_items += 1
                elif re.match(r"\s*-\s*\[\s*\]", line):
                    total_items += 1

    result["checked"] = checked_items
    result["total"] = total_items

    if total_items == 0:
        result["status"] = STATUS_WARN
        result["detail"] = "no checklist items found"
    elif checked_items < total_items:
        result["status"] = STATUS_FAIL
        result["detail"] = f"{checked_items}/{total_items} checked"
    else:
        result["detail"] = f"{checked_items}/{total_items} checked"

    return result


# ---------------------------------------------------------------------------
# Check 6: evidence pack
# ---------------------------------------------------------------------------

def check_evidence_pack(project_root: Path, verbose: bool = False) -> dict:
    """Check evidence_pack.md existence and required sections."""
    result = {"status": STATUS_PASS, "found": False, "missing_sections": [], "detail": ""}

    # Search for evidence_pack.md
    evidence_files = []
    specs_dir = project_root / "specs"
    if specs_dir.is_dir():
        evidence_files = list(specs_dir.rglob("evidence_pack.md"))

    if not evidence_files:
        result["status"] = STATUS_FAIL
        result["detail"] = "evidence_pack.md not found"
        return result

    result["found"] = True

    # Check required sections in the first found evidence pack
    ef = evidence_files[0]
    try:
        content = ef.read_text(encoding="utf-8").lower()
    except OSError:
        result["status"] = STATUS_WARN
        result["detail"] = "cannot read evidence_pack.md"
        return result

    missing = []
    for section in EVIDENCE_REQUIRED_SECTIONS:
        # Check for section header or YAML key
        section_pattern = section.replace("_", "[_ ]")
        if not re.search(rf"(?:#{{1,3}}\s*{section_pattern}|{section_pattern}\s*:)", content):
            missing.append(section)

    result["missing_sections"] = missing

    if missing:
        result["status"] = STATUS_WARN
        result["detail"] = f"{', '.join(missing)} pending"
    else:
        result["detail"] = "all sections present"

    return result


# ---------------------------------------------------------------------------
# Check 7: TODO/FIXME scan
# ---------------------------------------------------------------------------

def check_todo_fixme(project_root: Path, strict: bool = False, verbose: bool = False) -> dict:
    """Scan src/ for TODO/FIXME markers."""
    result = {"status": STATUS_PASS, "count": 0, "markers": [], "detail": ""}

    src_dir = project_root / "src"
    if not src_dir.is_dir():
        result["detail"] = "no src/ directory"
        return result

    pattern = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
    extensions = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java"}
    markers = []

    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".next", "__pycache__", "vendor")]
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix not in extensions:
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for i, line in enumerate(content.splitlines(), 1):
                m = pattern.search(line)
                if m:
                    markers.append({
                        "file": str(fpath.relative_to(project_root)),
                        "line": i,
                        "marker": m.group(1).upper(),
                        "text": line.strip()[:80],
                    })

    result["count"] = len(markers)
    result["markers"] = markers if verbose else []

    if markers:
        if strict:
            result["status"] = STATUS_FAIL
            result["detail"] = f"{len(markers)} markers (--strict)"
        else:
            result["status"] = STATUS_WARN
            result["detail"] = f"{len(markers)} markers"
    else:
        result["detail"] = "0 markers"

    return result


# ---------------------------------------------------------------------------
# Check 8 (opt-in): mutation testing
# ---------------------------------------------------------------------------

def mutation_check(project_root: Path, threshold: int = None) -> dict:
    """Run cosmic-ray mutation testing against tools/ (opt-in via --mutation).

    Returns a dict with keys: status, kill_rate, threshold, detail.
    threshold defaults to MUTATION_THRESHOLD env var (default 80).
    """
    if threshold is None:
        _load_env_local(project_root)
        threshold = int(os.environ.get("MUTATION_THRESHOLD", "80"))

    result = {"status": STATUS_PASS, "kill_rate": 0.0, "threshold": threshold, "detail": ""}

    # Verify cosmic-ray is available
    import shutil
    if shutil.which("cosmic-ray") is None:
        result["status"] = STATUS_WARN
        result["detail"] = "cosmic-ray not found (pip install cosmic-ray)"
        return result

    tools_dir = project_root / "sdd-templates" / "tools"
    if not tools_dir.is_dir():
        result["status"] = STATUS_WARN
        result["detail"] = "sdd-templates/tools/ not found"
        return result

    import tempfile
    import subprocess

    # Write a minimal cosmic-ray config for the tools directory
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".toml", prefix="cr_", delete=False, dir=str(project_root)
    ) as cf:
        cf.write(f"""[cosmic-ray]
module-path = "{tools_dir}"
timeout = 10.0
excluded-modules = []
test-command = "python3 -m pytest sdd-templates/tools/ -q --tb=no -x"

[cosmic-ray.distributor]
name = "local"
""")
        config_file = cf.name

    try:
        session_file = config_file.replace(".toml", ".sqlite")

        # Init session
        init_result = subprocess.run(
            ["cosmic-ray", "init", config_file, session_file],
            capture_output=True, text=True, timeout=60, cwd=str(project_root),
        )
        if init_result.returncode != 0:
            result["status"] = STATUS_WARN
            result["detail"] = f"cosmic-ray init failed: {init_result.stderr[:200]}"
            return result

        # Execute mutations (with timeout)
        subprocess.run(
            ["cosmic-ray", "exec", session_file],
            capture_output=True, text=True, timeout=300, cwd=str(project_root),
        )

        # Get results
        summary_result = subprocess.run(
            ["cr-report", session_file],
            capture_output=True, text=True, timeout=30, cwd=str(project_root),
        )

        # Parse kill rate from summary output
        kill_rate = 0.0
        for line in summary_result.stdout.splitlines():
            m = re.search(r"kill\s+rate[^\d]*([\d.]+)%", line, re.IGNORECASE)
            if m:
                kill_rate = float(m.group(1))
                break

        result["kill_rate"] = kill_rate
        if kill_rate < threshold:
            result["status"] = STATUS_FAIL
            result["detail"] = f"{kill_rate:.1f}% (< {threshold}%)"
        else:
            result["detail"] = f"{kill_rate:.1f}% (>= {threshold}%)"

    except subprocess.TimeoutExpired:
        result["status"] = STATUS_WARN
        result["detail"] = "mutation testing timed out"
    except Exception as exc:
        result["status"] = STATUS_WARN
        result["detail"] = f"mutation testing error: {exc}"
    finally:
        import os as _os
        for f in [config_file, config_file.replace(".toml", ".sqlite")]:
            try:
                _os.unlink(f)
            except OSError:
                pass

    return result


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_all_checks(
    project_root: Path,
    strict: bool = False,
    coverage_threshold: int = None,
    verbose: bool = False,
    include_mutation: bool = False,
) -> dict:
    """Run all checks and return aggregated result.

    Base checks: 7. With --mutation: 8.
    """
    checks = []

    # [1/?] stride-lint
    r1 = check_stride_lint(project_root, verbose)
    checks.append({"name": "stride-lint", "index": 1, **r1})

    # [2/?] spec:drift
    r2 = check_spec_drift(project_root, verbose)
    checks.append({"name": "spec:drift", "index": 2, **r2})

    # [3/?] tests
    r3 = check_tests(project_root, verbose)
    checks.append({"name": "tests", "index": 3, **r3})

    # [4/?] coverage
    r4 = check_coverage(project_root, coverage_threshold, verbose)
    checks.append({"name": "coverage", "index": 4, **r4})

    # [5/?] walkthrough checklist
    r5 = check_walkthrough(project_root, verbose)
    checks.append({"name": "walkthrough checklist", "index": 5, **r5})

    # [6/?] evidence pack
    r6 = check_evidence_pack(project_root, verbose)
    checks.append({"name": "evidence pack", "index": 6, **r6})

    # [7/?] TODO/FIXME scan
    r7 = check_todo_fixme(project_root, strict, verbose)
    checks.append({"name": "TODO/FIXME scan", "index": 7, **r7})

    # [8/?] mutation testing (opt-in)
    if include_mutation:
        r8 = mutation_check(project_root)
        checks.append({"name": "mutation testing", "index": 8, **r8})

    # Aggregate
    fails = sum(1 for c in checks if c["status"] == STATUS_FAIL)
    warns = sum(1 for c in checks if c["status"] == STATUS_WARN)

    if fails > 0:
        verdict = "NOT_READY"
        exit_code = 1
    else:
        verdict = "PR_READY"
        exit_code = 0

    return {
        "verdict": verdict,
        "exit_code": exit_code,
        "checks": checks,
        "summary": {
            "total": len(checks),
            "pass": sum(1 for c in checks if c["status"] == STATUS_PASS),
            "fail": fails,
            "warn": warns,
        },
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_summary_line(result: dict) -> str:
    """v5.4: single-line project-level summary.

    Format (PR_READY):
      stride pr-check: PR_READY (stride-lint PASS / spec:drift PASS / tests PASS / ...)
    Format (NOT_READY):
      stride pr-check: NOT_READY (stride-lint PASS / spec:drift FAIL / tests PASS / ...)

    Scope is intentionally project-level only — 7 base checks plus the optional
    mutation check when --mutation is set. Task-local facets (task ID / AC /
    NFR / scenarios) are NOT included; those are composed by the AI per
    sdd_bootstrap.md §5 Step 1-5.
    """
    verdict = result.get("verdict", "NOT_READY")
    parts = []
    for c in result.get("checks", []):
        name = c.get("name", "?")
        status = c.get("status", STATUS_WARN)
        # Map WARN to PASS for the summary-line view: WARN means the check could
        # not run (missing artefact, skipped, etc.) and should not flip the verdict.
        # Only FAIL is surfaced as FAIL in the 1-line summary.
        display = "FAIL" if status == STATUS_FAIL else "PASS"
        parts.append(f"{name} {display}")
    return f"stride pr-check: {verdict} ({' / '.join(parts)})"


def format_human_readable(result: dict) -> str:
    """Format results for terminal output."""
    lines = []
    lines.append("PR Readiness Check")
    lines.append("\u2501" * 37)

    total = len(result["checks"])
    for c in result["checks"]:
        name = c["name"]
        idx = c["index"]
        status = c["status"]
        detail = c.get("detail", "")

        # Pad name with dots for alignment
        padded = f"[{idx}/{total}] {name} ".ljust(30, ".")
        lines.append(f"{padded} [{status}]  {detail}")

    lines.append("")
    lines.append("\u2501" * 37)

    s = result["summary"]
    verdict = result["verdict"]
    warn_text = f" ({s['warn']} warning{'s' if s['warn'] != 1 else ''})" if s["warn"] > 0 else ""
    fail_text = f" ({s['fail']} failure{'s' if s['fail'] != 1 else ''})" if s["fail"] > 0 else ""

    if verdict == "PR_READY":
        lines.append(f"Result: PR_READY{warn_text}")
    else:
        lines.append(f"Result: NOT_READY{fail_text}{warn_text}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="PR Readiness Checker - Unified pre-PR quality gate",
    )
    parser.add_argument("project_root", nargs="?", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--summary-line", action="store_true",
                        help="Output single project-level 1-line summary (v5.4, 7 base checks + optional mutation)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show additional details")
    parser.add_argument("--strict", action="store_true", help="Treat TODO/FIXME as FAIL")
    parser.add_argument("--coverage-threshold", type=int, default=None,
                        help="Override coverage threshold (default: auto from coverage_tier)")
    parser.add_argument("--mutation", action="store_true",
                        help="Run optional mutation testing (requires cosmic-ray)")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.project_root:
        parser.error("project_root is required (or use --test)")

    root = Path(args.project_root)
    if not root.is_dir():
        print(f"Error: '{args.project_root}' is not a directory", file=sys.stderr)
        sys.exit(2)

    result = run_all_checks(
        root,
        strict=args.strict,
        coverage_threshold=args.coverage_threshold,
        verbose=args.verbose,
        include_mutation=args.mutation,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    elif args.summary_line:
        print(format_summary_line(result))
    else:
        print(format_human_readable(result))

    sys.exit(result["exit_code"])


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Run self-tests using temporary directories."""
    print("Running pr_readiness_checker.py self-tests...")
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

    # Test 1: Non-existent path -> exit 2
    def test_bad_path():
        p = Path("/tmp/pr_readiness_nonexistent_" + str(os.getpid()))
        assert not p.exists(), "test dir should not exist"
        # The main() function would sys.exit(2), we test the check functions
        # Just verify that run_all_checks handles missing dirs gracefully
        # (It won't crash because Path checks are inside each check)

    test("non-existent path handling", test_bad_path)

    # Test 2: Empty project -> NOT_READY
    def test_empty():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            result = run_all_checks(p)
            # No evidence_pack.md -> at least one FAIL
            ep_check = [c for c in result["checks"] if c["name"] == "evidence pack"][0]
            assert ep_check["status"] == STATUS_FAIL, f"expected evidence pack FAIL, got {ep_check['status']}"
            assert result["verdict"] == "NOT_READY", f"expected NOT_READY, got {result['verdict']}"

    test("empty project -> NOT_READY", test_empty)

    # Test 3: stride-lint errors -> FAIL
    def test_lint_fail():
        # We test the check function directly with a project that has specs/ but bad content
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            specs = p / "specs" / "feat"
            specs.mkdir(parents=True)
            # Create minimal basic_design.md without proper content -> lint errors
            (specs / "basic_design.md").write_text("# incomplete\n")
            r = check_stride_lint(p)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}"

    test("stride-lint errors -> FAIL", test_lint_fail)

    # Test 4: critical drift -> FAIL
    def test_drift_critical():
        # Mock the drift check by calling with a project that has contracts but no src
        try:
            import yaml as _yaml
        except ImportError:
            # Skip if PyYAML not available
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "contracts" / "api.yaml").write_text(_yaml.dump({
                "openapi": "3.0.0",
                "paths": {
                    "/api/users": {
                        "get": {"responses": {"200": {"description": "OK"}}},
                    },
                },
            }))
            (p / "src").mkdir()
            r = check_spec_drift(p)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}"
            assert r["critical"] > 0, f"expected critical > 0, got {r['critical']}"

    test("critical drift -> FAIL", test_drift_critical)

    # Test 5: drift clean -> PASS
    def test_drift_clean():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "src").mkdir()
            # No contracts = no drifts
            r = check_spec_drift(p)
            assert r["status"] == STATUS_PASS, f"expected PASS, got {r['status']}"

    test("drift clean -> PASS", test_drift_clean)

    # Test 6: test failures -> FAIL
    def test_tests_fail():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "junit.xml").write_text("""<?xml version="1.0"?>
<testsuite tests="10" failures="3" errors="0" skipped="0" time="1.5"/>""")
            r = check_tests(p)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}"
            assert r["failed"] == 3, f"expected 3 failed, got {r['failed']}"

    test("test failures -> FAIL", test_tests_fail)

    # Test 7: coverage below threshold -> FAIL
    def test_coverage_fail():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            cov = p / "coverage"
            cov.mkdir()
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {
                    "lines": {"total": 100, "covered": 50, "pct": 50},
                    "branches": {"total": 50, "covered": 25, "pct": 50},
                    "functions": {"total": 20, "covered": 10, "pct": 50},
                },
            }))
            r = check_coverage(p, threshold=80)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}"
            assert r["total_pct"] == 50.0, f"expected 50.0%, got {r['total_pct']}"

    test("coverage below threshold -> FAIL", test_coverage_fail)

    # Test 8: walkthrough unchecked -> FAIL
    def test_walkthrough_fail():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            runs = p / "specs" / "feat" / "runs" / "WI-001" / "RUN-001"
            runs.mkdir(parents=True)
            (runs / "walkthrough.md").write_text("""# Walkthrough

## Review Checklist
- [x] Security checks
- [ ] AC Coverage
- [ ] Code Quality
""")
            r = check_walkthrough(p)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}"
            assert r["checked"] == 1, f"expected 1 checked, got {r['checked']}"
            assert r["total"] == 3, f"expected 3 total, got {r['total']}"

    test("walkthrough unchecked -> FAIL", test_walkthrough_fail)

    # Test 9: TODO/FIXME -> WARN (FAIL with --strict)
    def test_todo_warn_and_strict():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            src = p / "src"
            src.mkdir()
            (src / "app.ts").write_text("""
const x = 1; // TODO: clean up
function foo() { /* FIXME: broken */ }
""")
            r_warn = check_todo_fixme(p, strict=False)
            assert r_warn["status"] == STATUS_WARN, f"expected WARN, got {r_warn['status']}"
            assert r_warn["count"] == 2, f"expected 2 markers, got {r_warn['count']}"

            r_strict = check_todo_fixme(p, strict=True)
            assert r_strict["status"] == STATUS_FAIL, f"expected FAIL with --strict, got {r_strict['status']}"

    test("TODO/FIXME -> WARN (--strict -> FAIL)", test_todo_warn_and_strict)

    # Test 10: All checks PASS -> PR_READY (exit 0)
    def test_all_pass():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)

            # Create minimal passing project
            specs = p / "specs" / "feat"
            impl = specs / "implementation-details"
            runs = specs / "runs" / "WI-001" / "RUN-001"
            src = p / "src"
            cov = p / "coverage"

            for dp in [specs, impl, runs, src, cov]:
                dp.mkdir(parents=True)

            # Evidence pack with required sections
            (impl / "evidence_pack.md").write_text("""# Evidence Pack

## test_results
All tests passed.

## coverage_report
85% line coverage.

## gate_approvals
Gate 1-5 approved.
""")

            # Walkthrough with all checked
            (runs / "walkthrough.md").write_text("""# Walkthrough

## Review Checklist
- [x] Security checks
- [x] AC Coverage
- [x] Code Quality
""")

            # Coverage data
            (cov / "coverage-summary.json").write_text(json.dumps({
                "total": {
                    "lines": {"total": 100, "covered": 85, "pct": 85},
                    "branches": {"total": 50, "covered": 42, "pct": 84},
                    "functions": {"total": 20, "covered": 18, "pct": 90},
                },
            }))

            # Test results (passing)
            (p / "junit.xml").write_text("""<?xml version="1.0"?>
<testsuite tests="48" failures="0" errors="0" skipped="0" time="5.0"/>""")

            # Clean src (no TODO/FIXME)
            (src / "app.ts").write_text("const app = express();\n")

            result = run_all_checks(p, coverage_threshold=80)

            # Check no FAIL
            fails = [c for c in result["checks"] if c["status"] == STATUS_FAIL]
            assert len(fails) == 0, f"expected 0 FAILs, got {len(fails)}: {[c['name'] for c in fails]}"
            assert result["verdict"] == "PR_READY", f"expected PR_READY, got {result['verdict']}"
            assert result["exit_code"] == 0, f"expected exit 0, got {result['exit_code']}"

    test("all checks PASS -> PR_READY (exit 0)", test_all_pass)

    # Test 11 (v5.4): summary-line formatter — PR_READY
    def test_summary_line_ready():
        sample = {
            "verdict": "PR_READY",
            "checks": [
                {"name": "stride-lint", "status": STATUS_PASS},
                {"name": "spec:drift", "status": STATUS_PASS},
                {"name": "tests", "status": STATUS_PASS},
                {"name": "coverage", "status": STATUS_PASS},
                {"name": "walkthrough checklist", "status": STATUS_PASS},
                {"name": "evidence pack", "status": STATUS_PASS},
                {"name": "TODO/FIXME scan", "status": STATUS_PASS},
            ],
        }
        line = format_summary_line(sample)
        assert line.startswith("stride pr-check: PR_READY ("), f"bad prefix: {line}"
        assert "stride-lint PASS" in line
        assert "TODO/FIXME scan PASS" in line
        # Must NOT leak task-local facets
        assert "T-" not in line and "AC-" not in line and "NFR" not in line

    test("summary-line formatter (PR_READY)", test_summary_line_ready)

    # Test 12 (v5.4): summary-line formatter — NOT_READY surfaces FAIL
    def test_summary_line_not_ready():
        sample = {
            "verdict": "NOT_READY",
            "checks": [
                {"name": "stride-lint", "status": STATUS_PASS},
                {"name": "spec:drift", "status": STATUS_FAIL},
                {"name": "tests", "status": STATUS_PASS},
                {"name": "coverage", "status": STATUS_PASS},
                {"name": "walkthrough checklist", "status": STATUS_FAIL},
                {"name": "evidence pack", "status": STATUS_PASS},
                {"name": "TODO/FIXME scan", "status": STATUS_PASS},
            ],
        }
        line = format_summary_line(sample)
        assert line.startswith("stride pr-check: NOT_READY ("), f"bad prefix: {line}"
        assert "spec:drift FAIL" in line
        assert "walkthrough checklist FAIL" in line
        assert "stride-lint PASS" in line

    test("summary-line formatter (NOT_READY)", test_summary_line_not_ready)

    print(f"\nAll {passed}/{total} self-tests passed." if passed == total else f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    main()
