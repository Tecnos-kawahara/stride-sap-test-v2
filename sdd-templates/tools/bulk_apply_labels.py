#!/usr/bin/env python3
"""Bulk-apply plane/visibility/return_policy frontmatter to Method content.

Applies the Classifier ruleset to every .md / .yaml file scanned by method_audit
and merges the resulting labels into existing frontmatter (or creates it).

Usage:
    python3 sdd-templates/tools/bulk_apply_labels.py [--root .] [--dry-run]

Files supported:
    *.md / *.markdown — leading YAML frontmatter (---/---)
    *.yaml / *.yml    — top-level dict merge

Files skipped (recorded in audit manifest but not modified):
    *.py / *.bpmn / *.xml — labeling captured via classifier only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from method_audit import collect_paths  # noqa: E402
from method_labeling.classifier import Classifier  # noqa: E402
from method_labeling.frontmatter import (  # noqa: E402
    MD_FRONTMATTER_RE,
    detect_style,
    has_method_labels,
    parse,
    patch_md_frontmatter,
)


def _patch_yaml(path: Path, labels: dict) -> None:
    """Prepend plane / visibility / return_policy keys to a YAML file.

    Preserves the rest of the file (including comments and ordering) by treating
    the file as text rather than reparsing+redumping. Skips only when the file
    already has all three label keys at top level. Tolerates Jinja-style
    placeholders that break ``yaml.safe_load`` (we fall back to a string scan).
    """
    text = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text) or {}
        if isinstance(data, dict) and "plane" in data and "visibility" in data and "return_policy" in data:
            return  # already labeled
    except yaml.YAMLError:
        # Template-placeholder YAML (e.g. Jinja {{FEATURE_NAME}}). Fall through to
        # a textual scan so we can still prepend label keys.
        first_block = text[:1024]
        if "\nplane:" in "\n" + first_block and "\nvisibility:" in "\n" + first_block:
            return

    rp = labels["return_policy"]
    block_lines = [
        f"plane: \"{labels['plane']}\"",
        f"visibility: \"{labels['visibility']}\"",
        "return_policy:",
        f"  customer: \"{rp['customer']}\"",
        f"  platform_admin: \"{rp['platform_admin']}\"",
        f"  tecnos_admin: \"{rp['tecnos_admin']}\"",
        "",
    ]
    block = "\n".join(block_lines)

    # Insert after any leading comment block / blank lines, before the first key.
    lines = text.splitlines(keepends=True)
    insertion_idx = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            insertion_idx = idx + 1
            continue
        break
    new_text = "".join(lines[:insertion_idx]) + block + "".join(lines[insertion_idx:])
    path.write_text(new_text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="bulk_apply_labels")
    parser.add_argument("--root", default=str(THIS_DIR.parent.parent))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    classifier = Classifier(root / "shared" / "policies" / "plane_classification_ruleset_v1.yaml")

    applied_md = 0
    applied_yaml = 0
    skipped_already_labeled = 0
    skipped_unsupported = 0

    for path in collect_paths(root):
        rel = path.relative_to(root).as_posix()
        cls = classifier.classify(rel)
        labels = {
            "plane": cls.plane,
            "visibility": cls.visibility,
            "return_policy": cls.return_policy,
        }
        try:
            fm = parse(path)
        except Exception:  # pragma: no cover
            continue

        if has_method_labels(fm.data):
            skipped_already_labeled += 1
            continue

        style = detect_style(path)
        if style == "md":
            text = path.read_text(encoding="utf-8")
            new_text = patch_md_frontmatter(text, labels)
            if not args.dry_run:
                path.write_text(new_text, encoding="utf-8")
            applied_md += 1
        elif style == "yaml":
            if not args.dry_run:
                _patch_yaml(path, labels)
            applied_yaml += 1
        else:
            skipped_unsupported += 1

    print(f"bulk_apply_labels: {'DRY-RUN' if args.dry_run else 'APPLIED'}")
    print(f"  applied (md):              {applied_md}")
    print(f"  applied (yaml):            {applied_yaml}")
    print(f"  skipped (already labeled): {skipped_already_labeled}")
    print(f"  skipped (py/xml/json):     {skipped_unsupported}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
