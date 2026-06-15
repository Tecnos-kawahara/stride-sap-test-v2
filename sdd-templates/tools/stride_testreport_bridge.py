#!/usr/bin/env python3
"""
stride-testreport-bridge: Bridge between testreport CLI and STRIDE ecosystem.

Reads testreport's cases.json, checks report.html existence, optionally runs
testreport validate, and maps test cases to STRIDE acceptance criteria via
stride_mapping.yaml.

Usage:
    python3 stride_testreport_bridge.py <feature_dir> [--json] [--mapping-file <path>]
    python3 stride_testreport_bridge.py --test
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def find_cases_json(feature_dir: Path) -> Path | None:
    """Locate cases.json under feature_dir/testreport/ or feature_dir/evidence/."""
    for sub in ("testreport", "evidence"):
        candidate = feature_dir / sub / "cases.json"
        if candidate.is_file():
            return candidate
    return None


def load_cases(cases_path: Path) -> list[dict]:
    """Parse cases.json and return list of test case objects."""
    text = cases_path.read_text(encoding="utf-8")
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "cases" in data:
        return data["cases"]
    return []


def load_mapping(mapping_path: Path) -> dict:
    """Load stride_mapping.yaml. Returns dict with 'mappings' list and optional 'gate'."""
    if not mapping_path.is_file():
        return {}
    if yaml is None:
        return {}
    text = mapping_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return {}
    return data


def build_mapping_index(mapping_data: dict) -> dict[str, list[str]]:
    """Build case_id -> stride_refs index from mapping data."""
    index = {}
    for entry in mapping_data.get("mappings", []):
        case_id = entry.get("case_id", "")
        refs = entry.get("stride_refs", [])
        if case_id:
            index[case_id] = refs if isinstance(refs, list) else [refs]
    return index


def run_testreport_validate(testreport_dir: Path) -> dict:
    """Run testreport validate if the command is available.

    Returns dict with keys: available(bool), success(bool), message(str).
    """
    if not shutil.which("testreport"):
        return {"available": False, "success": True, "message": "testreport not in PATH"}

    try:
        proc = subprocess.run(
            ["testreport", "validate", str(testreport_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "available": True,
            "success": proc.returncode == 0,
            "message": proc.stdout.strip() or proc.stderr.strip(),
        }
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"available": True, "success": False, "message": str(exc)}


def check_report_html(testreport_dir: Path) -> dict:
    """Check if report.html exists in testreport_dir."""
    report = testreport_dir / "report.html"
    return {
        "exists": report.is_file(),
        "path": str(report) if report.is_file() else str(report),
    }


def analyze(feature_dir: Path, mapping_file: Path | None = None) -> dict | None:
    """Run full analysis. Returns None if cases.json not found."""
    feature_dir = Path(feature_dir)
    cases_path = find_cases_json(feature_dir)
    if cases_path is None:
        return None

    testreport_dir = cases_path.parent
    cases = load_cases(cases_path)

    # Mapping
    if mapping_file is None:
        mapping_file = testreport_dir / "stride_mapping.yaml"
    mapping_data = load_mapping(mapping_file)
    mapping_index = build_mapping_index(mapping_data)

    case_ids = []
    for c in cases:
        cid = c.get("id", c.get("case_id", c.get("name", "")))
        if cid:
            case_ids.append(str(cid))

    unmapped = [cid for cid in case_ids if cid not in mapping_index]
    mapped_ac_refs = set()
    for refs in mapping_index.values():
        mapped_ac_refs.update(refs)

    # Evidence files (images etc. in testreport_dir excluding json/yaml/html/md)
    evidence_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".pdf", ".mp4"}
    evidences = [
        f for f in testreport_dir.iterdir()
        if f.is_file() and f.suffix.lower() in evidence_exts
    ] if testreport_dir.is_dir() else []

    # Validate
    validate_result = run_testreport_validate(testreport_dir)

    # Report
    report_result = check_report_html(testreport_dir)

    return {
        "cases_count": len(cases),
        "case_ids": case_ids,
        "evidences_count": len(evidences),
        "mapped_ac_count": len(mapped_ac_refs),
        "unmapped_cases": unmapped,
        "validate_status": "pass" if validate_result["success"] else "fail",
        "validate_available": validate_result["available"],
        "validate_message": validate_result["message"],
        "report_exists": report_result["exists"],
        "report_path": report_result["path"],
        "gate": mapping_data.get("gate", ""),
    }


# ---------------------------------------------------------------------------
# stride-lint integration API
# ---------------------------------------------------------------------------

def check_testreport_integration(feature_dir) -> dict | None:
    """Check testreport integration status for stride-lint.

    Returns None if cases.json not found (testreport not used).
    Returns dict with: report_missing, validate_failed, validate_message, unmapped_cases.
    """
    result = analyze(Path(feature_dir))
    if result is None:
        return None

    return {
        "report_missing": not result["report_exists"],
        "validate_failed": result["validate_status"] == "fail" and result["validate_available"],
        "validate_message": result["validate_message"],
        "unmapped_cases": result["unmapped_cases"],
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_text(result: dict) -> str:
    """Format analysis result for terminal output."""
    lines = []
    lines.append("testreport Bridge Report")
    lines.append("=" * 24)
    lines.append(f"Test cases:     {result['cases_count']}")
    lines.append(f"Evidence files: {result['evidences_count']}")
    lines.append(f"Mapped ACs:     {result['mapped_ac_count']}")

    if result["unmapped_cases"]:
        lines.append(f"Unmapped cases: {', '.join(result['unmapped_cases'])}")
    else:
        lines.append("Unmapped cases: (none)")

    if result["validate_available"]:
        status = "PASS" if result["validate_status"] == "pass" else "FAIL"
        lines.append(f"Validate:       [{status}] {result['validate_message']}")
    else:
        lines.append(f"Validate:       [SKIP] {result['validate_message']}")

    report_status = "PASS" if result["report_exists"] else "MISSING"
    lines.append(f"Report HTML:    [{report_status}] {result['report_path']}")

    if result.get("gate"):
        lines.append(f"Gate:           {result['gate']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="stride-testreport-bridge: Bridge between testreport and STRIDE",
    )
    parser.add_argument("feature_dir", nargs="?", help="Feature directory path")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--mapping-file", help="Path to stride_mapping.yaml")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.feature_dir:
        parser.error("feature_dir is required (or use --test)")

    feature_dir = Path(args.feature_dir)
    if not feature_dir.is_dir():
        print(f"Error: '{args.feature_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    mapping_file = Path(args.mapping_file) if args.mapping_file else None
    result = analyze(feature_dir, mapping_file)

    if result is None:
        print("No cases.json found — testreport not configured for this feature.")
        sys.exit(0)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Run self-tests using temporary directories."""
    print("Running stride_testreport_bridge.py self-tests...")
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

    # Test 1: No cases.json returns None
    def test_no_cases():
        with tempfile.TemporaryDirectory() as d:
            result = analyze(Path(d))
            assert result is None, f"Expected None, got {result}"

    test("No cases.json returns None", test_no_cases)

    # Test 2: cases.json in testreport/ subdir
    def test_cases_in_testreport():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([
                {"id": "01_login", "name": "Login test"},
                {"id": "02_logout", "name": "Logout test"},
            ]))
            result = analyze(p)
            assert result is not None
            assert result["cases_count"] == 2
            assert result["report_exists"] is False

    test("cases.json in testreport/ subdir", test_cases_in_testreport)

    # Test 3: cases.json in evidence/ subdir
    def test_cases_in_evidence():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            ev = p / "evidence"
            ev.mkdir()
            (ev / "cases.json").write_text(json.dumps({"cases": [
                {"id": "01_test"},
            ]}))
            result = analyze(p)
            assert result is not None
            assert result["cases_count"] == 1

    test("cases.json in evidence/ subdir", test_cases_in_evidence)

    # Test 4: report.html exists
    def test_report_exists():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "01"}]))
            (tr / "report.html").write_text("<html></html>")
            result = analyze(p)
            assert result["report_exists"] is True

    test("report.html detection", test_report_exists)

    # Test 5: Mapping file loaded
    def test_mapping():
        if yaml is None:
            print("    (skipped — pyyaml not installed)")
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([
                {"id": "01_login"},
                {"id": "02_logout"},
                {"id": "03_unmapped"},
            ]))
            mapping = {
                "mappings": [
                    {"case_id": "01_login", "stride_refs": ["AC-US-FEAT001-001-01"]},
                    {"case_id": "02_logout", "stride_refs": ["AC-US-FEAT001-002-01"]},
                ],
                "gate": "Tasks Gate",
            }
            (tr / "stride_mapping.yaml").write_text(yaml.dump(mapping))
            result = analyze(p)
            assert result["mapped_ac_count"] == 2, f"Expected 2 mapped ACs, got {result['mapped_ac_count']}"
            assert result["unmapped_cases"] == ["03_unmapped"]
            assert result["gate"] == "Tasks Gate"

    test("Mapping file loaded and unmapped detected", test_mapping)

    # Test 6: Evidence file counting
    def test_evidence_counting():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "01"}]))
            (tr / "screenshot1.png").write_text("")
            (tr / "screenshot2.jpg").write_text("")
            (tr / "video.mp4").write_text("")
            (tr / "notes.txt").write_text("")  # not counted
            result = analyze(p)
            assert result["evidences_count"] == 3, f"Expected 3, got {result['evidences_count']}"

    test("Evidence file counting", test_evidence_counting)

    # Test 7: check_testreport_integration returns None when no cases
    def test_lint_api_none():
        with tempfile.TemporaryDirectory() as d:
            result = check_testreport_integration(d)
            assert result is None

    test("check_testreport_integration returns None", test_lint_api_none)

    # Test 8: check_testreport_integration with report missing
    def test_lint_api_report_missing():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "01"}]))
            result = check_testreport_integration(d)
            assert result is not None
            assert result["report_missing"] is True

    test("check_testreport_integration report_missing", test_lint_api_report_missing)

    # Test 9: check_testreport_integration with report present
    def test_lint_api_report_present():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "01"}]))
            (tr / "report.html").write_text("<html></html>")
            result = check_testreport_integration(d)
            assert result is not None
            assert result["report_missing"] is False

    test("check_testreport_integration report present", test_lint_api_report_present)

    # Test 10: Custom mapping file path
    def test_custom_mapping_path():
        if yaml is None:
            print("    (skipped — pyyaml not installed)")
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "01_a"}, {"id": "02_b"}]))
            custom = p / "custom_mapping.yaml"
            mapping = {"mappings": [{"case_id": "01_a", "stride_refs": ["AC-01"]}]}
            custom.write_text(yaml.dump(mapping))
            result = analyze(p, mapping_file=custom)
            assert result["unmapped_cases"] == ["02_b"]

    test("Custom mapping file path", test_custom_mapping_path)

    # Test 11: Empty cases.json list
    def test_empty_cases():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([]))
            result = analyze(p)
            assert result is not None
            assert result["cases_count"] == 0
            assert result["unmapped_cases"] == []

    test("Empty cases.json list", test_empty_cases)

    # Test 12: testreport/ preferred over evidence/
    def test_testreport_preferred():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "from_tr"}]))
            ev = p / "evidence"
            ev.mkdir()
            (ev / "cases.json").write_text(json.dumps([{"id": "from_ev"}]))
            result = analyze(p)
            assert result["case_ids"] == ["from_tr"]

    test("testreport/ preferred over evidence/", test_testreport_preferred)

    # Test 13: format_text output
    def test_format_text():
        data = {
            "cases_count": 3,
            "evidences_count": 2,
            "mapped_ac_count": 1,
            "unmapped_cases": ["case_x"],
            "validate_available": False,
            "validate_status": "pass",
            "validate_message": "testreport not in PATH",
            "report_exists": True,
            "report_path": "/tmp/report.html",
            "gate": "Tasks Gate",
        }
        text = format_text(data)
        assert "Test cases:     3" in text
        assert "case_x" in text
        assert "[SKIP]" in text
        assert "[PASS]" in text

    test("format_text output formatting", test_format_text)

    # Test 14: validate_failed only when testreport available
    def test_validate_failed_requires_available():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            tr = p / "testreport"
            tr.mkdir()
            (tr / "cases.json").write_text(json.dumps([{"id": "01"}]))
            result = check_testreport_integration(d)
            # testreport likely not in PATH during tests
            assert result["validate_failed"] is False

    test("validate_failed only when testreport available", test_validate_failed_requires_available)

    print(f"\n{passed}/{total} tests passed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    main()
