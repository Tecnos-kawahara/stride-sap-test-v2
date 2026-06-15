#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_skill_step0.py — verify all specialized SKILL.md have STEP 0 PRE-FLIGHT block.

Purpose:
  Phase H starter (postmortem 2026-05-08-bpmn-vertical-flow-violation.md Action Items)。
  全 specialized SKILL.md (stride-conductor 除く) に **「STEP 0: PRE-FLIGHT (MANDATORY)」**
  ブロックが存在することを機械検証する。SKILL.md 改修時に STEP 0 が消えると CI が止める。

Usage:
  python3 cowork-plugin/scripts/check_skill_step0.py
  python3 cowork-plugin/scripts/check_skill_step0.py --json

Exit codes:
  0 — PASS (全 7 specialized SKILL.md に STEP 0 ブロック存在)
  1 — FAIL (1 つ以上の SKILL.md に STEP 0 ブロック欠落)
  2 — usage error (skills dir not found)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "1.0.0"

# Specialized skills that MUST have STEP 0 PRE-FLIGHT block
# stride-conductor は orchestrator なので除外 (代わりに「Dispatch 前の MANDATORY Read」を持つ)
SPECIALIZED_SKILLS = {
    "bpmn-authoring",
    "basic-design-authoring",
    "baccm-discovery",
    "babok-elicitation",
    "layered-context-modelling",
    "epic-decomposition",
    "upstream-bridge",
}

STEP0_PATTERN = re.compile(
    r"^##\s+STEP 0[:\s]+PRE-FLIGHT.*MANDATORY",
    re.MULTILINE | re.IGNORECASE,
)


def check_skill_step0(skills_dir: Path) -> tuple[list[str], list[str]]:
    """Return (passes, failures) — list of skill names."""
    passes = []
    failures = []
    for skill_name in sorted(SPECIALIZED_SKILLS):
        skill_path = skills_dir / skill_name / "SKILL.md"
        if not skill_path.exists():
            failures.append(f"{skill_name}: SKILL.md not found at {skill_path}")
            continue
        text = skill_path.read_text(encoding="utf-8")
        if STEP0_PATTERN.search(text):
            passes.append(skill_name)
        else:
            failures.append(
                f"{skill_name}: missing '## STEP 0: PRE-FLIGHT (MANDATORY)' block "
                f"(see docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md Action Item #1)"
            )
    return passes, failures


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="check_skill_step0",
        description="Verify all specialized SKILL.md have STEP 0 PRE-FLIGHT block",
    )
    parser.add_argument("--skills-dir", default=None,
                        help="Path to cowork-plugin/skills/ (default: relative to script)")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--version", action="version", version=f"check_skill_step0.py {VERSION}")
    args = parser.parse_args()

    if args.skills_dir:
        skills_dir = Path(args.skills_dir).resolve()
    else:
        # script is at cowork-plugin/scripts/check_skill_step0.py
        skills_dir = Path(__file__).resolve().parent.parent / "skills"

    if not skills_dir.is_dir():
        print(f"ERROR: skills directory not found: {skills_dir}", file=sys.stderr)
        return 2

    passes, failures = check_skill_step0(skills_dir)

    if args.json:
        print(json.dumps({
            "version": VERSION,
            "skills_dir": str(skills_dir),
            "passed": not failures,
            "passes": passes,
            "failures": failures,
            "expected_count": len(SPECIALIZED_SKILLS),
            "actual_pass_count": len(passes),
        }, ensure_ascii=False, indent=2))
    else:
        print("STEP 0 PRE-FLIGHT Check")
        print("=" * 60)
        for s in passes:
            print(f"  ✓ {s}")
        for f in failures:
            print(f"  ✗ {f}")
        if not failures:
            print(f"\nPASS: {len(passes)}/{len(SPECIALIZED_SKILLS)} specialized skills have STEP 0")
        else:
            print(f"\nFAIL: {len(failures)} skill(s) missing STEP 0 block")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
