#!/usr/bin/env python3
"""plane_label_completeness_checker.py

Checks that every Method Store content file (YAML/MD with frontmatter) declares a
``plane:`` label in the canonical IP boundary classification.

Required by F2 publish workflow strict validate gate (CT-CLI-02).
Source: F1 method_labeling SSoT (frontmatter parser Layer 1a).

Exit codes:
  0 — all files have plane label
  1 — one or more files missing plane label
  2 — invalid invocation / I/O error

Usage:
  python plane_label_completeness_checker.py --root .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_INVALID = 2

# Files containing **Method Store content** require plane: label
# Conservative scope: only Phase 0/1 method artifacts that are exposed via API
RELEVANT_PATHS = (
    "upstream/phase_0_discovery/",
    "upstream/phase_0_2_context_modelling/",
    "upstream/phase_0_3_elicit/",
    "/basic_design.md",
    "method_labeling/",
)
RELEVANT_EXTENSIONS = (".yaml", ".yml", ".md")

EXEMPT_PATTERNS = (
    "README", "CHANGELOG", "AGENTS", "CLAUDE.md", "STRIDE_STATUS",
    ".github/", "node_modules/", "__pycache__/", ".venv/", "dist/", "build/",
    "test", "Test", ".test.", "_test.",
    "_template", "_TEMPLATE",
    "schema.yaml", "schema.yml", "schema.json",
    "/state/", "/state.yaml",
    "/contracts/", "lock.json",
    "/migrations/", "/tests/",
    "openapi.", "asyncapi.",
    "/archive/",
    "/specs/val_",
    "/specs/FEAT-ERPSAMPLE/",
    "/sdd-templates/specs/sample_feature/",
)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
PLANE_RE = re.compile(r"^plane:\s*(\S+)", re.MULTILINE)


def is_method_content_file(path: Path) -> bool:
    if path.suffix not in RELEVANT_EXTENSIONS:
        return False
    rel = str(path).replace("\\", "/")
    if not any(p in rel for p in RELEVANT_PATHS):
        return False
    for pattern in EXEMPT_PATTERNS:
        if pattern in rel:
            return False
    return True


def has_plane_label(path: Path) -> tuple[bool, str | None]:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        return False, f"read error: {e}"

    fm_match = FRONTMATTER_RE.match(content)
    if fm_match:
        plane_match = PLANE_RE.search(fm_match.group(1))
        if plane_match:
            return True, plane_match.group(1)

    if path.suffix in (".yaml", ".yml"):
        plane_match = PLANE_RE.search(content[:2000])
        if plane_match:
            return True, plane_match.group(1)

    return False, "no plane label found"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="plane_label_completeness_checker")
    parser.add_argument("--root", default=".")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return EXIT_INVALID

    violations: list[tuple[Path, str]] = []
    checked_count = 0

    for ext in RELEVANT_EXTENSIONS:
        for path in root.rglob(f"*{ext}"):
            if not is_method_content_file(path):
                continue
            checked_count += 1
            ok, info = has_plane_label(path)
            if not ok:
                violations.append((path.relative_to(root), info or "unknown"))
            elif args.verbose:
                print(f"  [OK] {path.relative_to(root)} → plane={info}")

    print(f"plane_label_completeness: checked {checked_count} files")
    if violations:
        print(f"FAIL: {len(violations)} files missing plane: label")
        for path, reason in violations[:20]:
            print(f"  - {path}: {reason}")
        if len(violations) > 20:
            print(f"  ... and {len(violations) - 20} more")
        return EXIT_VIOLATION

    print("PASS")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
