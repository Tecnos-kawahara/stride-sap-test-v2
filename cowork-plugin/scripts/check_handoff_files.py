#!/usr/bin/env python3
"""check_handoff_files.py — handoff 4 ファイル + 必須セクション検証 (Phase F WI-VALF01-014 同梱)

Cowork Plugin v0.2.0-stable で Phase F WI-VALF01-001 が `stride-handoff` workflow に
組み込んだ機械検証ロジックを CLI から呼び出せる Python 版。コンサル環境で
`python3 cowork-plugin/scripts/check_handoff_files.py specs/<feature>/` 実行で
handoff 前検証を実施できる (二重保険、tests からも import 可能)。

検証対象:
- 4 ファイル存在: basic_design.md / process.bpmn / upstream/claude_code_handoff.md /
  upstream/acceptance_criteria.yaml
- basic_design.md 必須セクション: # 0. Canonical Basic Design / basic_design: / context: /
  scope: / bpmn_descriptions: / traceability_rows: / basic_design_gate_check:
- process.bpmn 必須要素: <bpmn:process / <bpmn:startEvent / <bpmn:endEvent / <bpmndi:BPMNDiagram

Usage:
    python3 cowork-plugin/scripts/check_handoff_files.py specs/val_f01/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REQUIRED_BD_SECTIONS = (
    "# 0. Canonical Basic Design",
    "basic_design:",
    "context:",
    "scope:",
    "bpmn_descriptions:",
    "traceability_rows:",
    "basic_design_gate_check:",
)

REQUIRED_BPMN_ELEMENTS = (
    "<bpmn:process",
    "<bpmn:startEvent",
    "<bpmn:endEvent",
    "<bpmndi:BPMNDiagram",
)


def check(spec_dir: Path) -> list[str]:
    """Return a list of error messages. Empty list = OK."""
    errors: list[str] = []
    if not spec_dir.is_dir():
        return [f"spec dir not found: {spec_dir}"]

    files = {
        "basic_design.md": spec_dir / "basic_design.md",
        "process.bpmn": spec_dir / "process.bpmn",
        "upstream/claude_code_handoff.md": spec_dir / "upstream" / "claude_code_handoff.md",
        "upstream/acceptance_criteria.yaml": spec_dir / "upstream" / "acceptance_criteria.yaml",
    }

    # 1. 4 ファイル存在
    for label, path in files.items():
        if not path.is_file():
            errors.append(f"missing handoff file: {label} ({path})")

    # 2. basic_design.md 必須セクション
    bd_path = files["basic_design.md"]
    if bd_path.is_file():
        text = bd_path.read_text(encoding="utf-8")
        for sec in REQUIRED_BD_SECTIONS:
            if sec not in text:
                errors.append(f"basic_design.md missing required section: {sec}")

    # 3. process.bpmn 必須要素
    bpmn_path = files["process.bpmn"]
    if bpmn_path.is_file():
        text = bpmn_path.read_text(encoding="utf-8")
        for el in REQUIRED_BPMN_ELEMENTS:
            if el not in text:
                errors.append(f"process.bpmn missing required element: {el}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("spec_dir", type=Path, help="Path to specs/<feature>/")
    args = parser.parse_args(argv)

    errors = check(args.spec_dir)
    if errors:
        print(f"⛔ handoff 4 ファイル + 必須セクション検証 FAILED ({len(errors)} errors):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"✅ {args.spec_dir} handoff 4 ファイル + 必須セクション OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
