#!/usr/bin/env python3
"""ip_boundary_checker.py

Checks that public-plane Method Store content does NOT contain ``INTERNAL_*`` markers
that would constitute an intellectual property boundary violation.

Required by F2 publish workflow strict validate gate (CT-CLI-02).
Source: F1 method_labeling SSoT (Layer 1b INTERNAL_* marker parser).

Exit codes:
  0 — no IP boundary violations
  1 — one or more violations found
  2 — invalid invocation / I/O error

Usage:
  python ip_boundary_checker.py --root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_INVALID = 2

INTERNAL_MARKERS = (
    "INTERNAL_METHOD",
    "INTERNAL_LESSON",
    "INTERNAL_RUBRIC",
    "INTERNAL_PROMPT",
)
MARKER_RE = re.compile(
    r"</?(?:" + "|".join(INTERNAL_MARKERS) + r")\b"
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PLANE_RE = re.compile(r"^plane:\s*(\S+)", re.MULTILINE)

CUSTOMER_VISIBLE_PLANES = ("public", "tenant")
RELEVANT_EXTENSIONS = (".yaml", ".yml", ".md", ".json")
SKIP_DIRS = ("node_modules", "__pycache__", ".venv", "dist", "build", ".git")


def _strip_yaml_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] in ('"', "'"):
        return value[1:-1]
    return value


def is_customer_visible(path: Path) -> tuple[bool, str | None]:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False, None

    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        plane_match = PLANE_RE.search(fm_match.group(1))
        if plane_match:
            plane = _strip_yaml_quotes(plane_match.group(1))
            return plane in CUSTOMER_VISIBLE_PLANES, plane

    if path.suffix in (".yaml", ".yml"):
        plane_match = PLANE_RE.search(content[:2000])
        if plane_match:
            plane = _strip_yaml_quotes(plane_match.group(1))
            return plane in CUSTOMER_VISIBLE_PLANES, plane

    return False, None


def find_internal_markers(content: str) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = []
    for line_no, line in enumerate(content.splitlines(), start=1):
        if MARKER_RE.search(line):
            hits.append((line_no, line.strip()[:120]))
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ip_boundary_checker")
    parser.add_argument("--root", default=".")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return EXIT_INVALID

    violations: list[tuple[Path, str, list[tuple[int, str]]]] = []
    public_files_count = 0

    for ext in RELEVANT_EXTENSIONS:
        for path in root.rglob(f"*{ext}"):
            if any(skip in path.parts for skip in SKIP_DIRS):
                continue
            if path.name == "ip_boundary_checker.py":
                continue
            visible, plane = is_customer_visible(path)
            if not visible:
                continue
            public_files_count += 1

            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue

            hits = find_internal_markers(content)
            if hits:
                violations.append((path.relative_to(root), plane or "?", hits))
            elif args.verbose:
                print(f"  [OK] {path.relative_to(root)} (plane={plane})")

    print(f"ip_boundary: scanned {public_files_count} customer-visible files (plane in {CUSTOMER_VISIBLE_PLANES})")
    if violations:
        print(f"FAIL: {len(violations)} files contain INTERNAL_* markers in customer-visible plane")
        for path, plane, hits in violations[:10]:
            print(f"  - {path} (plane={plane}):")
            for line_no, snippet in hits[:3]:
                print(f"      L{line_no}: {snippet}")
        if len(violations) > 10:
            print(f"  ... and {len(violations) - 10} more")
        return EXIT_VIOLATION

    print("PASS")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
