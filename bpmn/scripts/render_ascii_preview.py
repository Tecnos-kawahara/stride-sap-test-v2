#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_ascii_preview.py — Render a BPMN file as an ASCII grid (lanes + elements).

Purpose:
  Produce a human-readable layout preview from BPMNDI coordinates so that an
  agent / reviewer can visually verify orientation (vertical vs horizontal
  swimlane, Tecnos override #13) without opening Camunda Modeler.

  This is the third leg of the 3-stage completion gate established in the
  2026-05-08 incident postmortem:

      bpmn_lint.py PASS  +  bd_bpmn_sync.py PASS  +  render_ascii_preview review

Origin:
  Created 2026-05-08 in response to BPMN vertical-flow violation incident
  (`docs/postmortems/2026-05-08-bpmn-vertical-flow-violation.md`).

Dependencies:
  Python 3.7+, stdlib only (xml.etree, argparse, pathlib).

Usage:
  render_ascii_preview.py path/to/process.bpmn
  render_ascii_preview.py --width 80 path/to/process.bpmn
  render_ascii_preview.py --json path/to/process.bpmn  (raw layout data)

Exit codes:
  0 — preview rendered (or layout absent → empty grid + warning)
  2 — usage error (file not found, parse error)
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = "1.0.0"
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
DC_NS = "http://www.omg.org/spec/DD/20100524/DC"

# Element type → ASCII glyph.
GLYPH_FOR_TAG = {
    "startEvent": "(START)",
    "endEvent": "(END)",
    "intermediateCatchEvent": "(IC)",
    "intermediateThrowEvent": "(IT)",
    "exclusiveGateway": "<XOR>",
    "parallelGateway": "<AND>",
    "inclusiveGateway": "<OR>",
    "eventBasedGateway": "<EVT>",
    "userTask": "[T]",
    "serviceTask": "[T]",
    "task": "[T]",
    "sendTask": "[T]",
    "receiveTask": "[T]",
    "scriptTask": "[T]",
    "manualTask": "[T]",
    "businessRuleTask": "[T]",
    "callActivity": "[T]",
}


def parse_layout(path: Path):
    """Parse BPMN XML and extract element / shape / participant / edge layout.

    Returns a dict with:
      orientation: "vertical" | "horizontal" | "unknown"
      lanes: list[{name, x, y, width, height}]   (participants)
      elements: list[{id, tag, name, x, y, width, height, glyph}]
      edges: list[{id, sourceRef, targetRef}]
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # Build id → (tag, name) for flow nodes
    nodes = {}
    process_short = lambda t: t.split("}", 1)[1] if "}" in t else t
    for elem in root.iter():
        if not elem.tag.startswith(f"{{{BPMN_NS}}}"):
            continue
        tag = process_short(elem.tag)
        eid = elem.attrib.get("id")
        if not eid:
            continue
        name = elem.attrib.get("name", "")
        if tag in GLYPH_FOR_TAG or tag == "sequenceFlow":
            nodes[eid] = {"tag": tag, "name": name}

    # Collect participants
    participants = {}
    for p in root.iter(f"{{{BPMN_NS}}}participant"):
        pid = p.attrib.get("id", "")
        pname = p.attrib.get("name", "(unnamed)")
        participants[pid] = {"name": pname}

    # Iterate BPMNShape to attach coordinates
    lanes = []
    elements = []
    orientation_votes = {"vertical": 0, "horizontal": 0}
    for shape in root.iter(f"{{{BPMNDI_NS}}}BPMNShape"):
        ref = shape.attrib.get("bpmnElement", "")
        is_horizontal = shape.attrib.get("isHorizontal")
        bounds = shape.find(f"{{{DC_NS}}}Bounds")
        if bounds is None:
            continue
        x = float(bounds.attrib.get("x", 0))
        y = float(bounds.attrib.get("y", 0))
        w = float(bounds.attrib.get("width", 0))
        h = float(bounds.attrib.get("height", 0))
        if ref in participants:
            lanes.append({
                "name": participants[ref]["name"],
                "id": ref,
                "x": x, "y": y, "width": w, "height": h,
                "is_horizontal": is_horizontal,
            })
            if is_horizontal == "false":
                orientation_votes["vertical"] += 1
            elif is_horizontal == "true":
                orientation_votes["horizontal"] += 1
        elif ref in nodes:
            tag = nodes[ref]["tag"]
            glyph = GLYPH_FOR_TAG.get(tag, f"[{tag[:6]}]")
            elements.append({
                "id": ref, "tag": tag, "name": nodes[ref]["name"],
                "x": x, "y": y, "width": w, "height": h, "glyph": glyph,
            })

    # Determine orientation from participant shapes
    if orientation_votes["vertical"] > orientation_votes["horizontal"]:
        orientation = "vertical"
    elif orientation_votes["horizontal"] > 0:
        orientation = "horizontal"
    else:
        # Heuristic fallback: if lanes have width > height, they are horizontal
        if lanes:
            avg_aspect = sum(l["width"] / max(l["height"], 1) for l in lanes) / len(lanes)
            orientation = "horizontal" if avg_aspect > 1 else "vertical"
        else:
            orientation = "unknown"

    # Edges (sequenceFlow)
    edges = []
    for sf in root.iter(f"{{{BPMN_NS}}}sequenceFlow"):
        edges.append({
            "id": sf.attrib.get("id", ""),
            "sourceRef": sf.attrib.get("sourceRef", ""),
            "targetRef": sf.attrib.get("targetRef", ""),
        })

    return {
        "orientation": orientation,
        "orientation_votes": orientation_votes,
        "lanes": sorted(lanes, key=lambda l: l["x"] if orientation == "vertical" else l["y"]),
        "elements": elements,
        "edges": edges,
    }


def render_ascii(layout: dict, max_width: int = 80) -> str:
    """Render layout dict as ASCII art."""
    orientation = layout["orientation"]
    lanes = layout["lanes"]
    elements = layout["elements"]
    edges = layout["edges"]

    out = []
    out.append(f"BPMN Layout Preview  (orientation: {orientation.upper()})")
    out.append("=" * min(max_width, 60))

    if not lanes:
        out.append("(no participant/lane shapes found — cannot render)")
        out.append("")
        out.append(f"Elements: {len(elements)}")
        for e in elements[:20]:
            out.append(f"  {e['glyph']:8s}  id={e['id']:24s}  name={e['name']}")
        return "\n".join(out)

    # Build a per-lane ordered list of elements (sorted by progression axis)
    if orientation == "vertical":
        # Lanes are arranged horizontally (x-axis), elements flow top→bottom (y-axis)
        for lane in lanes:
            lane["elements"] = sorted(
                [e for e in elements
                 if lane["x"] <= e["x"] + e["width"] / 2 < lane["x"] + lane["width"]],
                key=lambda e: e["y"],
            )
        col_width = max(8, min(max_width // max(len(lanes), 1), 14))
        # Header
        header = "+" + "+".join("-" * col_width for _ in lanes) + "+"
        out.append(header)
        out.append(
            "|" + "|".join(lane["name"][:col_width].center(col_width) for lane in lanes) + "|"
        )
        out.append(header)
        # Body — print one row per "vertical step" (max element count)
        max_rows = max((len(lane["elements"]) for lane in lanes), default=0)
        for i in range(max_rows):
            row_cells = []
            for lane in lanes:
                if i < len(lane["elements"]):
                    e = lane["elements"][i]
                    cell = e["glyph"]
                    if "[T]" in cell and e.get("name"):
                        # Compact label
                        label = "[" + (e["id"].split("-")[-1] if "-" in e["id"] else "T") + "]"
                        cell = label
                    row_cells.append(cell.center(col_width))
                else:
                    row_cells.append(" " * col_width)
            out.append("|" + "|".join(row_cells) + "|")
            # Inter-row "|" separator (poor-man's flow indicator)
            sep_cells = []
            for lane in lanes:
                if i + 1 < len(lane["elements"]):
                    sep_cells.append("|".center(col_width))
                else:
                    sep_cells.append(" " * col_width)
            out.append("|" + "|".join(sep_cells) + "|")
        out.append(header)
    else:
        # Horizontal swimlane (or unknown) — render rows = lanes, columns = element progression
        max_per_lane = max((len([e for e in elements if lane["y"] <= e["y"] < lane["y"] + lane["height"]])
                            for lane in lanes), default=0)
        col_width = max(8, min((max_width - 14) // max(max_per_lane, 1), 14))
        for lane in lanes:
            lane_elems = sorted(
                [e for e in elements if lane["y"] <= e["y"] + e["height"] / 2 < lane["y"] + lane["height"]],
                key=lambda e: e["x"],
            )
            label = lane["name"][:12].ljust(12)
            cells = []
            for e in lane_elems:
                cell = e["glyph"]
                if "[T]" in cell:
                    cell = "[" + (e["id"].split("-")[-1] if "-" in e["id"] else "T") + "]"
                cells.append(cell.center(col_width))
            row = label + "| " + " → ".join(cells)
            out.append(row)

    out.append("")
    out.append(f"Total: {len(lanes)} lane(s), {len(elements)} element(s), {len(edges)} flow(s)")
    if orientation == "horizontal":
        out.append("⚠️  WARNING: orientation is HORIZONTAL. Tecnos override #13 mandates "
                   "isHorizontal=\"false\" (vertical swimlane). Re-render with vertical layout.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="render_ascii_preview",
        description="Render BPMN layout as ASCII grid (vertical vs horizontal sanity check)",
    )
    parser.add_argument("path", help="path to .bpmn file")
    parser.add_argument("--width", type=int, default=80, help="max output width (default: 80)")
    parser.add_argument("--json", action="store_true", help="emit raw layout JSON instead of ASCII")
    parser.add_argument("--version", action="version", version=f"render_ascii_preview.py {VERSION}")
    args = parser.parse_args()

    p = Path(args.path)
    if not p.exists():
        print(f"ERROR: file not found: {p}", file=sys.stderr)
        return 2

    try:
        layout = parse_layout(p)
    except Exception as exc:
        print(f"ERROR: parse failure: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(layout, ensure_ascii=False, indent=2))
    else:
        print(render_ascii(layout, max_width=args.width))

    return 0


if __name__ == "__main__":
    sys.exit(main())
