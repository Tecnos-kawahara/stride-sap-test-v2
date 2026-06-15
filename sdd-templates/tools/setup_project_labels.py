#!/usr/bin/env python3
"""
STRIDE Learning Loop ラベルセットアップ (v4.5)

GitHub リポジトリに STRIDE Learning Loop 用のラベルを一括作成する。

Usage:
    python3 sdd-templates/tools/setup_project_labels.py --repo owner/repo
    python3 sdd-templates/tools/setup_project_labels.py --repo owner/repo --dry-run
    python3 sdd-templates/tools/setup_project_labels.py --test
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List, Tuple

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


# =============================================================================
# Label Definitions
# =============================================================================

STRIDE_LABELS: List[Tuple[str, str, str]] = [
    # (name, color, description)
    # Findings count
    ("findings:0", "c5def5", "Run findings: 0 items"),
    ("findings:1-3", "0075ca", "Run findings: 1-3 items"),
    ("findings:4+", "003f8a", "Run findings: 4+ items"),
    # Decisions count
    ("decisions:0", "e8d5f5", "Run decisions: 0 items"),
    ("decisions:1-3", "7b2d8e", "Run decisions: 1-3 items"),
    ("decisions:4+", "4a0e5c", "Run decisions: 4+ items"),
    # Spec Impact
    ("spec-impact:none", "0e8a16", "No spec changes needed"),
    ("spec-impact:proposed", "fbca04", "Spec changes proposed"),
    ("spec-impact:required", "e11d48", "Spec changes required (blocker)"),
    # Learning
    ("learning:pattern", "0d9488", "Reusable pattern discovered"),
    # Amendment lifecycle
    ("amendment", "d4a017", "Specification amendment"),
    ("amendment:draft", "fef3c7", "Amendment drafted, pending review"),
    ("amendment:review", "f59e0b", "Amendment under review"),
    ("amendment:applying", "2563eb", "Amendment spec changes in PR review"),
    ("amendment:applied", "059669", "Amendment approved and applied to spec"),
    ("amendment-derived", "c2e0c6", "WI derived from amendment"),
    # Sentry integration
    ("sentry", "362d59", "Linked to Sentry issue"),
    ("sentry:critical", "b60205", "Sentry critical/fatal error"),
    ("sentry:error", "d93f0b", "Sentry error level issue"),
    ("sentry:warning", "fbca04", "Sentry warning level issue"),
]

# =============================================================================
# Symphony Orchestration Labels (追加分 — STRIDE_LABELS とは独立)
# =============================================================================

SYMPHONY_LABELS: List[Tuple[str, str, str]] = [
    ("symphony:ready",   "0E8A16", "Symphony auto-dispatch target"),
    ("symphony:running", "1D76DB", "Symphony agent is executing"),
    ("symphony:blocked", "D93F0B", "Waiting for human approval"),
    ("symphony:done",    "5319E7", "Symphony completed"),
    ("symphony:failed",  "B60205", "Symphony execution failed"),
    ("symphony:janitor", "C2E0C6", "Janitor cleanup proposal"),
    ("phase:design",     "FBCA04", "SDD Phase 1: Design"),
    ("phase:specify",    "F9D0C4", "SDD Phase 2: Specify"),
    ("phase:tasking",    "C5DEF5", "SDD Phase 3: Tasking"),
    ("phase:execute",    "BFD4F2", "SDD Phase 4: Execute"),
]


# =============================================================================
# GitHub CLI
# =============================================================================


def _run_gh(*args: str) -> Tuple[int, str, str]:
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def create_labels(repo: str, dry_run: bool = False) -> dict:
    """Create STRIDE labels on the given repo."""
    results = {"created": 0, "exists": 0, "failed": 0, "details": []}

    for name, color, description in STRIDE_LABELS:
        if dry_run:
            results["details"].append(f"  DRY-RUN: {name} (#{color}) — {description}")
            results["created"] += 1
            continue

        rc, out, err = _run_gh(
            "label", "create", name,
            "--repo", repo,
            "--color", color,
            "--description", description,
            "--force",
        )

        if rc == 0:
            results["details"].append(f"  OK: {name} (#{color})")
            results["created"] += 1
        elif "already exists" in err.lower():
            results["details"].append(f"  EXISTS: {name}")
            results["exists"] += 1
        else:
            results["details"].append(f"  FAIL: {name} — {err}")
            results["failed"] += 1

    return results


# =============================================================================
# Self-Tests
# =============================================================================


def run_tests() -> bool:
    """Run self-tests."""
    print("Running setup_project_labels.py self-tests...\n")
    passed = 0
    total = 0

    def check(name, condition, msg=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  PASS: {name}")
        else:
            print(f"  FAIL: {name} — {msg}")

    # Test 1: Label definitions
    print("Test 1: Label definitions")
    check("total labels", len(STRIDE_LABELS) == 20, f"got {len(STRIDE_LABELS)}")
    names = [l[0] for l in STRIDE_LABELS]
    check("findings:0", "findings:0" in names)
    check("findings:1-3", "findings:1-3" in names)
    check("findings:4+", "findings:4+" in names)
    check("decisions:0", "decisions:0" in names)
    check("spec-impact:none", "spec-impact:none" in names)
    check("spec-impact:proposed", "spec-impact:proposed" in names)
    check("spec-impact:required", "spec-impact:required" in names)
    check("learning:pattern", "learning:pattern" in names)
    check("amendment", "amendment" in names)
    check("amendment:draft", "amendment:draft" in names)
    check("amendment:review", "amendment:review" in names)
    check("amendment:applying", "amendment:applying" in names)
    check("amendment:applied", "amendment:applied" in names)
    check("amendment-derived", "amendment-derived" in names)
    check("sentry", "sentry" in names)
    check("sentry:critical", "sentry:critical" in names)
    check("sentry:error", "sentry:error" in names)
    check("sentry:warning", "sentry:warning" in names)

    # Test 2: Color format
    print("\nTest 2: Color format")
    for name, color, desc in STRIDE_LABELS:
        check(f"{name} color len", len(color) == 6, f"got {len(color)}: {color}")

    # Test 3: No duplicate names
    print("\nTest 3: No duplicates")
    check("unique names", len(names) == len(set(names)))

    # Test 4: Dry-run output
    print("\nTest 4: Dry-run structure")
    results = {"created": 0, "exists": 0, "failed": 0, "details": []}
    for name, color, desc in STRIDE_LABELS:
        results["details"].append(f"  DRY-RUN: {name} (#{color}) — {desc}")
        results["created"] += 1
    check("dry-run count", results["created"] == 20)

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    return passed == total


def create_symphony_labels(repo: str, dry_run: bool = False) -> dict:
    """Create Symphony labels on the given repo (STRIDE_LABELS とは独立)."""
    results = {"created": 0, "exists": 0, "failed": 0, "details": []}
    for name, color, description in SYMPHONY_LABELS:
        if dry_run:
            results["details"].append(f"  DRY-RUN: {name} (#{color}) — {description}")
            results["created"] += 1
            continue
        rc, out, err = _run_gh(
            "label", "create", name, "--repo", repo,
            "--color", color, "--description", description, "--force",
        )
        if rc == 0:
            results["details"].append(f"  OK: {name} (#{color})")
            results["created"] += 1
        elif "already exists" in err.lower():
            results["details"].append(f"  EXISTS: {name}")
            results["exists"] += 1
        else:
            results["details"].append(f"  FAIL: {name} — {err}")
            results["failed"] += 1
    return results


def run_symphony_tests() -> bool:
    """Run Symphony label self-tests (STRIDE tests とは独立)."""
    print("Running Symphony label self-tests...\n")
    passed = total = 0
    def check(name, cond, msg=""):
        nonlocal passed, total
        total += 1
        if cond: passed += 1; print(f"  PASS: {name}")
        else: print(f"  FAIL: {name} — {msg}")
    check("symphony label count", len(SYMPHONY_LABELS) == 10, f"got {len(SYMPHONY_LABELS)}")
    names = [l[0] for l in SYMPHONY_LABELS]
    check("symphony:ready", "symphony:ready" in names)
    check("phase:design", "phase:design" in names)
    check("unique names", len(names) == len(set(names)))
    for name, color, desc in SYMPHONY_LABELS:
        check(f"{name} color len", len(color) == 6, f"got {len(color)}")
    print(f"\nResults: {passed}/{total} passed")
    return passed == total


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Setup STRIDE Learning Loop labels (v4.5)",
    )
    parser.add_argument("--repo", type=str, help="Repository (owner/repo)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument("--symphony", action="store_true",
                        help="Create Symphony orchestration labels (in addition to STRIDE labels)")
    parser.add_argument("--test-symphony", action="store_true",
                        help="Run Symphony label self-tests")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if args.test_symphony:
        success = run_symphony_tests()
        sys.exit(0 if success else 1)

    if not args.repo:
        parser.print_help()
        sys.exit(1)

    print(f"Setting up STRIDE Learning Loop labels on {args.repo}...")
    if args.dry_run:
        print("(DRY-RUN — no changes will be made)\n")
    print()

    results = create_labels(args.repo, args.dry_run)
    for detail in results["details"]:
        print(detail)

    print(f"\nSummary: {results['created']} created, {results['exists']} exists, {results['failed']} failed")

    if args.symphony:
        print(f"\nSetting up Symphony labels on {args.repo}...")
        sym_results = create_symphony_labels(args.repo, args.dry_run)
        for detail in sym_results["details"]:
            print(detail)
        print(f"\nSymphony: {sym_results['created']} created, {sym_results['exists']} exists, {sym_results['failed']} failed")
        if sym_results["failed"] > 0:
            sys.exit(1)

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
