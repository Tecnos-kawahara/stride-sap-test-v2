#!/usr/bin/env python3
"""Verify TIER_MISMATCH warning in stride_lint.py.

Uses sdd-templates/specs/sample_feature/ as base fixture,
copies to temp dir, and modifies basic_design.md to test tier detection.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SAMPLE = PROJECT_ROOT / "sdd-templates" / "specs" / "sample_feature"
LINT = SCRIPT_DIR / "stride_lint.py"


def patch_basic_design(bd_path: Path, sec: bool, erp: bool, tier: str = "standard") -> None:
    """Inject security_sensitive, erp_integration, coverage_tier into Canonical YAML."""
    text = bd_path.read_text()
    # Find the basic_design: block inside the Canonical YAML and inject fields
    # Insert after "basic_design:" line (inside the fenced yaml block)
    inject = f"""  coverage_tier: "{tier}"
  security_sensitive: {str(sec).lower()}
  erp_integration: {str(erp).lower()}"""

    # Insert after the first "basic_design:" inside ```yaml block
    pattern = r'(basic_design:\n)'
    replacement = r'\1' + inject + '\n'
    new_text = re.sub(pattern, replacement, text, count=1)
    if new_text == text:
        print(f"  WARNING: Could not inject fields into {bd_path}", file=sys.stderr)
    bd_path.write_text(new_text)


def run_lint_on_copy(sec: bool, erp: bool, tier: str, expect_warn: bool) -> bool:
    """Copy sample_feature, patch it, run lint, check for TIER_MISMATCH."""
    with tempfile.TemporaryDirectory() as td:
        feat = Path(td) / "specs" / "sample_feature"
        shutil.copytree(SAMPLE, feat)
        # Also copy memory/ for constitution.md reference
        mem_src = PROJECT_ROOT / "memory"
        mem_dst = Path(td) / "memory"
        if mem_src.exists():
            shutil.copytree(mem_src, mem_dst)

        patch_basic_design(feat / "basic_design.md", sec, erp, tier)

        r = subprocess.run(
            [sys.executable, str(LINT), str(feat)],
            capture_output=True, text=True, cwd=td
        )
        output = r.stdout + r.stderr
        found = "TIER_MISMATCH" in output
        ok = found == expect_warn
        status = "PASS" if ok else "FAIL"
        label = f"sec={sec} erp={erp} tier={tier} expect_warn={expect_warn}"
        print(f"  {status}: {label} (found={found})")
        if not ok:
            # Show lint output for debugging
            for line in output.splitlines():
                if "TIER" in line or "ERROR" in line or "WARN" in line:
                    print(f"    | {line}")
        return ok


def main():
    if not SAMPLE.exists():
        print(f"ERROR: Sample feature not found: {SAMPLE}", file=sys.stderr)
        sys.exit(1)

    print("TIER_MISMATCH warning tests:")
    print(f"  Sample: {SAMPLE}")
    print(f"  Lint:   {LINT}\n")

    results = [
        run_lint_on_copy(True, True, "standard", True),    # both flags → warn
        run_lint_on_copy(True, False, "standard", True),   # security only → warn
        run_lint_on_copy(False, True, "standard", True),   # erp only → warn
        run_lint_on_copy(False, False, "standard", False),  # neither → no warn
        run_lint_on_copy(True, True, "critical", False),   # already critical → no warn
    ]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} passed")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
