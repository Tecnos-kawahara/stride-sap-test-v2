#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bd_bpmn_sync.py — Validate basic_design.md ↔ process.bpmn id sync.

Purpose:
  Detect mismatches between `basic_design.md`'s `bpmn_descriptions.elements[].bpmn_id`
  list and the actual `id` attributes inside `process.bpmn`. Per Tecnos-STRIDE
  MUST-DO #14, the two must be in 1:1 correspondence (excluding sequenceFlow ids,
  which are typically not enumerated in basic_design.md).

Origin:
  Created 2026-05-08 in response to BPMN vertical-flow violation incident
  (`docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md`, item #5).

Dependencies:
  Python 3.7+, stdlib only (xml.etree, argparse, re, pathlib).

Usage:
  bd_bpmn_sync.py path/to/basic_design.md path/to/process.bpmn
  bd_bpmn_sync.py --json basic_design.md process.bpmn
  bd_bpmn_sync.py --include-flows basic_design.md process.bpmn  (also require BPMN-FLOW-NNN sync)

Exit codes:
  0 — PASS  (id sets match within scope)
  1 — FAIL  (mismatch detected)
  2 — usage error (file not found, parse error)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = "1.0.0"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"

# basic_design.md may have YAML wrapped in a fenced code block:
#   ```yaml
#   bpmn_descriptions: ...
#   ```
# We extract the bpmn_id values via regex to avoid PyYAML dependency.
BPMN_ID_RE = re.compile(r"^\s*-?\s*bpmn_id:\s*[\"']?(?P<id>[A-Za-z0-9_\-]+)[\"']?\s*$", re.MULTILINE)


def extract_bpmn_ids_from_basic_design(path: Path) -> set[str]:
    """Extract all bpmn_id values from basic_design.md.

    Looks for lines of the form `bpmn_id: BPMN-TASK-001` (with optional quotes
    and list-item marker). Operates on raw text — no YAML parser required.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    ids: set[str] = set()
    for m in BPMN_ID_RE.finditer(text):
        ids.add(m.group("id"))
    return ids


def extract_ids_from_process_bpmn(path: Path, include_flows: bool = False) -> set[str]:
    """Extract all element ids from process.bpmn.

    By default excludes sequenceFlow ids (BPMN-FLOW-NNN), since basic_design.md
    typically enumerates only "named" elements (events / tasks / gateways).
    Pass include_flows=True to require flow id sync as well.
    """
    tree = ET.parse(path)
    root = tree.getroot()
    ids: set[str] = set()
    flow_tag = f"{{{BPMN_NS}}}sequenceFlow"
    process_tag = f"{{{BPMN_NS}}}process"
    collab_tag = f"{{{BPMN_NS}}}collaboration"
    participant_tag = f"{{{BPMN_NS}}}participant"
    definitions_tag_local = "definitions"  # root
    # Tags that hold ids but are wrappers / DI / metadata, not content elements
    EXCLUDED_LOCAL = {
        "definitions", "process", "collaboration", "participant",
        "BPMNDiagram", "BPMNPlane", "BPMNShape", "BPMNEdge",
        "extensionElements", "documentation", "incoming", "outgoing",
        "messageFlow", "association", "textAnnotation", "group",
    }
    for elem in root.iter():
        eid = elem.attrib.get("id")
        if not eid:
            continue
        # Get local tag name (without namespace)
        local = elem.tag.split("}", 1)[1] if "}" in elem.tag else elem.tag
        if local in EXCLUDED_LOCAL:
            continue
        # Exclude flow ids unless requested
        if not include_flows and elem.tag == flow_tag:
            continue
        ids.add(eid)
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="bd_bpmn_sync",
        description="Validate basic_design.md ↔ process.bpmn id sync (Tecnos-STRIDE MUST-DO #14)",
    )
    parser.add_argument("basic_design_path", help="path to basic_design.md")
    parser.add_argument("process_bpmn_path", help="path to process.bpmn")
    parser.add_argument("--include-flows", action="store_true",
                        help="also require BPMN-FLOW-NNN sync (default: skip flow ids)")
    parser.add_argument("--json", action="store_true",
                        help="emit JSON report (machine-readable)")
    parser.add_argument("--version", action="version", version=f"bd_bpmn_sync.py {VERSION}")
    args = parser.parse_args()

    bd_path = Path(args.basic_design_path)
    bpmn_path = Path(args.process_bpmn_path)

    if not bd_path.exists():
        print(f"ERROR: basic_design.md not found: {bd_path}", file=sys.stderr)
        return 2
    if not bpmn_path.exists():
        print(f"ERROR: process.bpmn not found: {bpmn_path}", file=sys.stderr)
        return 2

    try:
        bd_ids = extract_bpmn_ids_from_basic_design(bd_path)
        bpmn_ids = extract_ids_from_process_bpmn(bpmn_path, include_flows=args.include_flows)
    except Exception as exc:
        print(f"ERROR: parse failure: {exc}", file=sys.stderr)
        return 2

    only_in_bd = sorted(bd_ids - bpmn_ids)
    only_in_bpmn = sorted(bpmn_ids - bd_ids)

    errors = []
    if only_in_bd:
        errors.append({
            "code": "BD_BPMN_SYNC_BD_ORPHAN",
            "message": f"basic_design.md mentions bpmn_id(s) absent from process.bpmn: {only_in_bd}",
            "fix_hint": (
                "Either add the missing element(s) to process.bpmn (with matching id) "
                "or remove the orphan bpmn_id from basic_design.md.bpmn_descriptions. "
                "1:1 correspondence is mandatory (FEAT MUST-DO #14)."
            ),
            "refs": [
                "bpmn/rules/bpmn_quick_reference.md",
                "cowork-plugin/skills/bpmn-authoring/SKILL.md §STEP 0",
            ],
        })
    if only_in_bpmn:
        errors.append({
            "code": "BD_BPMN_SYNC_BPMN_ORPHAN",
            "message": f"process.bpmn has element id(s) not enumerated in basic_design.md: {only_in_bpmn}",
            "fix_hint": (
                "Either add a matching entry to basic_design.md.bpmn_descriptions.elements[] "
                "(with bpmn_id, name, type, purpose) or remove the unused element from process.bpmn. "
                "1:1 correspondence is mandatory (FEAT MUST-DO #14)."
            ),
            "refs": [
                "bpmn/rules/bpmn_quick_reference.md",
                "cowork-plugin/skills/basic-design-authoring/SKILL.md",
            ],
        })

    summary = {
        "version": VERSION,
        "basic_design": str(bd_path),
        "process_bpmn": str(bpmn_path),
        "include_flows": args.include_flows,
        "bd_id_count": len(bd_ids),
        "bpmn_id_count": len(bpmn_ids),
        "passed": not errors,
        "errors": errors,
    }

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("BD ↔ BPMN Sync Report")
        print("=" * 60)
        print(f"basic_design.md: {bd_path}  (bpmn_id count: {len(bd_ids)})")
        print(f"process.bpmn:    {bpmn_path}  (id count: {len(bpmn_ids)})")
        print(f"include_flows: {args.include_flows}")
        print()
        if not errors:
            print("PASS: all bpmn_id values in basic_design.md match ids in process.bpmn")
        else:
            for e in errors:
                print(f"ERROR: {e['code']}")
                print(f"  {e['message']}")
                print(f"  fix: {e['fix_hint']}")
                for r in e.get("refs", []):
                    print(f"  see: {r}")
                print()
            print(f"FAIL: {len(errors)} mismatch(es)")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
