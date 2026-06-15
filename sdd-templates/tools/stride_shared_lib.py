#!/usr/bin/env python3
"""stride_shared_lib — shared YAML extraction utilities for SDD tooling.

Single source of truth for Canonical YAML block handling, previously
duplicated across stride_lint, multi_model_evaluator, wi_readiness_checker,
sdd_planning_bridge, and post_edit_guard.

Path-based API:    extract_canonical_yaml / extract_frontmatter_yaml /
                   find_all_canonical_blocks
Text primitives:   extract_yaml_blocks / extract_yaml_after_marker /
                   extract_frontmatter / extract_first_yaml_block

Primitives mirror stride_lint's historical line-scan semantics, so
migrating callers produces byte-identical output. strict=True raises
MalformedYAMLError on parse failure or non-mapping payload; strict=False
returns None. stdlib + PyYAML only.
"""
from __future__ import annotations

import pathlib
import re
import sys
from typing import Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

__all__ = [
    "extract_canonical_yaml",
    "extract_frontmatter_yaml",
    "find_all_canonical_blocks",
    "extract_yaml_blocks",
    "extract_yaml_after_marker",
    "extract_frontmatter",
    "extract_first_yaml_block",
    "load_yaml_with_frontmatter",
    "CANONICAL_SECTION_MARKERS",
    "MalformedYAMLError",
]


class MalformedYAMLError(ValueError):
    """Raised by strict=True helpers when YAML cannot be parsed."""


CANONICAL_SECTION_MARKERS: Dict[str, str] = {
    "basic_design": "Canonical Basic Design",
    "spec": "Canonical Spec",
    "plan": "Canonical Plan",
    "tasks": "Canonical Tasks",
    "epic_design": "Canonical Epic Design",
    "feature_breakdown": "Canonical Feature Breakdown",
}

# Identifies canonical heading lines such as:
#   # 0. Canonical Basic Design (YAML)
#   ## 0. Canonical Epic Design (YAML)
#   # 1. Canonical Tasks (YAML)
_CANONICAL_HEADING_RE = re.compile(
    r"^#+\s+\d+\.\s+Canonical\s+(?P<name>.+?)\s+\(YAML\)\s*$"
)


# ---------------------------------------------------------------------------
# Text-based primitives (mirror stride_lint's historical contract)
# ---------------------------------------------------------------------------

def extract_yaml_blocks(text: str) -> List[str]:
    """Every fenced ```yaml ... ``` block body as raw strings (line-scan)."""
    blocks: List[str] = []
    lines = text.splitlines()
    in_block = False
    buf: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_block and stripped.startswith("```yaml"):
            in_block = True
            buf = []
            continue
        if in_block and stripped.startswith("```"):
            blocks.append("\n".join(buf))
            in_block = False
            buf = []
            continue
        if in_block:
            buf.append(line)
    return blocks


def extract_first_yaml_block(text: str) -> Optional[str]:
    """First ```yaml ... ``` block body, or None."""
    blocks = extract_yaml_blocks(text)
    return blocks[0] if blocks else None


def extract_yaml_after_marker(text: str, marker: str) -> Optional[str]:
    """First ```yaml body whose opening fence follows a line containing *marker*."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if marker in line:
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith("```yaml"):
                    start = j + 1
                    for k in range(start, len(lines)):
                        if lines[k].strip().startswith("```"):
                            return "\n".join(lines[start:k])
    return None


def extract_frontmatter(text: str) -> Optional[str]:
    """Raw YAML frontmatter body between leading ``---`` fences, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i])
    return None


# ---------------------------------------------------------------------------
# Parsing / helpers
# ---------------------------------------------------------------------------

def _parse_yaml(block: Optional[str], *, strict: bool) -> Optional[dict]:
    """Parse a YAML body into a dict. Strict mode raises MalformedYAMLError;
    non-strict returns None. Empty documents normalize to {}."""
    if block is None:
        return None
    if yaml is None:
        if strict:
            raise RuntimeError("PyYAML is required. Install with `pip install pyyaml`.")
        return None
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        if strict:
            raise MalformedYAMLError(str(exc)) from exc
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        if strict:
            raise MalformedYAMLError(
                f"Expected YAML mapping, got {type(data).__name__}"
            )
        return None
    return data


def _normalize_section(heading_name: str) -> str:
    return heading_name.strip().lower().replace(" ", "_")


def _find_all_canonical_blocks_from_text(
    text: str,
    *,
    strict: bool,
) -> List[Tuple[str, dict]]:
    """Internal: scan *text* for canonical headings and return parsed blocks."""
    results: List[Tuple[str, dict]] = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        heading = _CANONICAL_HEADING_RE.match(lines[i])
        if heading is None:
            i += 1
            continue
        name = heading.group("name")
        # Locate the first ```yaml fence after the heading.
        advanced_to = i + 1
        for j in range(i + 1, n):
            if lines[j].strip().startswith("```yaml"):
                start = j + 1
                for k in range(start, n):
                    if lines[k].strip().startswith("```"):
                        parsed = _parse_yaml(
                            "\n".join(lines[start:k]), strict=strict
                        )
                        if parsed is not None:
                            results.append((_normalize_section(name), parsed))
                        advanced_to = k + 1
                        break
                break
        i = advanced_to
    return results


# ---------------------------------------------------------------------------
# Path-based high-level API
# ---------------------------------------------------------------------------

def extract_canonical_yaml(
    path: pathlib.Path,
    *,
    section: Optional[str] = None,
    strict: bool = False,
) -> Optional[dict]:
    """Return the Canonical YAML block in *path* as a parsed dict.

    section = snake_case name (spec/plan/tasks/basic_design/epic_design) or a
    raw marker substring; None = auto-detect. Auto-detect picks the single
    ``# N. Canonical X (YAML)`` heading, raises TypeError on multiple matches,
    and falls back to the first plain ```yaml``` fence so legacy templates
    and WI files continue to work. strict=False returns None on parse failure.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        if strict:
            raise
        return None

    if section is not None:
        marker = CANONICAL_SECTION_MARKERS.get(section, section)
        return _parse_yaml(extract_yaml_after_marker(text, marker), strict=strict)

    canonical = _find_all_canonical_blocks_from_text(text, strict=strict)
    if len(canonical) == 1:
        return canonical[0][1]
    if len(canonical) > 1:
        names = [s for s, _ in canonical]
        raise TypeError(
            f"{path}: multiple canonical YAML blocks found ({names}); "
            f"pass section= to disambiguate"
        )
    # Legacy fallback: WI files and older templates lack canonical headings.
    return _parse_yaml(extract_first_yaml_block(text), strict=strict)


def extract_frontmatter_yaml(path: pathlib.Path) -> Optional[dict]:
    """Parse leading ``--- ... ---`` YAML frontmatter from *path*."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return _parse_yaml(extract_frontmatter(text), strict=False)


def load_yaml_with_frontmatter(
    path: pathlib.Path,
    *,
    strict: bool = True,
) -> Optional[dict]:
    """Load YAML body, skipping frontmatter ``--- ... ---`` if present.

    Phase A templates (sdd-templates/templates/upstream/*_template.yaml) ship with
    a Markdown-style frontmatter header followed by the actual YAML body::

        ---
        # Template: ...
        # Phase: ...
        ---

        artifact: ...

    Bare ``yaml.safe_load`` chokes on this because YAML treats it as two
    documents (yaml.composer.ComposerError: expected a single document in the
    stream). This helper detects the frontmatter, splits with maxsplit=2 to get
    exactly three parts (``''``, frontmatter, body), and parses the body.

    Args:
        path: YAML file path.
        strict: If True (default), yaml.YAMLError is propagated to caller —
                matches upstream_bridge's existing behavior (main() catches it
                and returns exit code 2). If False, yaml.YAMLError is caught
                and None is returned — matches upstream_lint's existing
                behavior (lint continues checking other rules).

    Returns:
        Parsed YAML body dict (always from ``parts[2]`` after the second
        ``---``, never from ``parts[1]`` which is the frontmatter); or None
        if the file does not exist, the yaml module is unavailable, or
        (when strict=False) the body is malformed.
    """
    path = pathlib.Path(path)
    if not path.exists():
        return None
    if yaml is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        if text.lstrip().startswith("---"):
            # Split into 3 parts: '' (before first ---), frontmatter, body
            parts = text.split("---", 2)
            if len(parts) >= 3:
                return yaml.safe_load(parts[2])
        # No frontmatter → parse the whole text
        return yaml.safe_load(text)
    except yaml.YAMLError:
        if strict:
            raise
        return None


def find_all_canonical_blocks(path: pathlib.Path) -> List[Tuple[str, dict]]:
    """(section_name, parsed_dict) for every canonical heading in *path*.
    Section names are normalized to snake_case."""
    path = pathlib.Path(path)
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return _find_all_canonical_blocks_from_text(text, strict=False)


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    import tempfile

    failures: List[str] = []

    def _check(cond: bool, name: str) -> None:
        if cond:
            print(f"  PASS: {name}")
        else:
            failures.append(name)
            print(f"  FAIL: {name}")

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = pathlib.Path(tmp_str)

        # Test 1: single canonical block — section= and auto-detect.
        p1 = tmp / "spec.md"
        p1.write_text(
            "# 0. Canonical Spec (YAML)\n\n"
            "```yaml\n"
            "spec:\n"
            "  title: hello\n"
            "```\n"
        )
        d1 = extract_canonical_yaml(p1, section="spec")
        _check(d1 is not None and d1["spec"]["title"] == "hello",
               "Test 1a: section='spec' parses single canonical block")
        d1b = extract_canonical_yaml(p1)
        _check(d1b is not None and d1b["spec"]["title"] == "hello",
               "Test 1b: auto-detect returns the single canonical block")

        # Test 2: multi-canonical file with disambiguation.
        p2 = tmp / "combined.md"
        p2.write_text(
            "# 0. Canonical Basic Design (YAML)\n"
            "```yaml\nbasic_design:\n  id: bd1\n```\n\n"
            "# 0. Canonical Spec (YAML)\n"
            "```yaml\nspec:\n  id: s1\n```\n\n"
            "# 0. Canonical Plan (YAML)\n"
            "```yaml\nplan:\n  id: p1\n```\n"
        )
        all_blocks = find_all_canonical_blocks(p2)
        _check(
            len(all_blocks) == 3
            and {n for n, _ in all_blocks} == {"basic_design", "spec", "plan"},
            f"Test 2a: find_all_canonical_blocks finds 3 sections "
            f"(got {[n for n, _ in all_blocks]})",
        )
        d2 = extract_canonical_yaml(p2, section="plan")
        _check(d2 is not None and d2["plan"]["id"] == "p1",
               "Test 2b: section='plan' picks the right block")

        # Test 3: malformed YAML — strict vs non-strict.
        p3 = tmp / "bad.md"
        p3.write_text(
            "# 0. Canonical Spec (YAML)\n"
            "```yaml\n"
            "spec:\n  title: [unclosed\n"
            "```\n"
        )
        _check(
            extract_canonical_yaml(p3, section="spec", strict=False) is None,
            "Test 3a: malformed YAML with strict=False returns None",
        )
        raised = False
        try:
            extract_canonical_yaml(p3, section="spec", strict=True)
        except MalformedYAMLError:
            raised = True
        _check(raised, "Test 3b: malformed YAML with strict=True raises")

        # Test 4: legacy template — no canonical heading, bare fenced block.
        p4 = tmp / "legacy_wi.md"
        p4.write_text(
            "# WI-LEGACY-001: example\n\n"
            "```yaml\n"
            "spec_refs: [AC-001]\n"
            "risk_flags: []\n"
            "```\n"
        )
        d4 = extract_canonical_yaml(p4)
        _check(
            d4 is not None and d4["spec_refs"] == ["AC-001"],
            "Test 4: legacy file without canonical heading falls back to first yaml block",
        )

        # Test 5: frontmatter extraction.
        p5 = tmp / "fm.md"
        p5.write_text(
            "---\n"
            "title: Doc\n"
            "id: 42\n"
            "---\n\n"
            "# Body\n"
        )
        fm = extract_frontmatter_yaml(p5)
        _check(
            fm == {"title": "Doc", "id": 42},
            f"Test 5: extract_frontmatter_yaml parses frontmatter (got {fm})",
        )

        # Test 6: missing path & empty file.
        _check(
            extract_canonical_yaml(tmp / "does_not_exist.md") is None,
            "Test 6a: missing path returns None",
        )
        p6 = tmp / "empty.md"
        p6.write_text("")
        _check(
            extract_canonical_yaml(p6) is None,
            "Test 6b: empty file returns None",
        )

        # Test 7: section specified but no matching heading.
        _check(
            extract_canonical_yaml(p1, section="tasks") is None,
            "Test 7: section='tasks' on spec-only file returns None",
        )

        # Test 8: multiple canonical blocks without section → TypeError.
        raised = False
        try:
            extract_canonical_yaml(p2)
        except TypeError:
            raised = True
        _check(
            raised,
            "Test 8: auto-detect on multi-canonical file raises TypeError",
        )

    total = 8
    passed = total - len(failures)
    print(f"\n{passed}/{total} self-tests passed.")
    if failures:
        for name in failures:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(_run_self_tests())
    print("stride_shared_lib: shared YAML extraction utilities.")
    print("Run with --test to execute self-tests.")
