#!/usr/bin/env python3
"""stride method labels --check — CI-friendly plane labeling completeness gate.

Wraps `method_audit.audit()` and emits a CI-grade summary. Exit 1 on any
error-severity violation (unset plane labels on plane!=public elements).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from method_audit import audit  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(prog="stride method labels --check")
    parser.add_argument("--root", default=str(THIS_DIR.parent.parent))
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest, violations = audit(root, strict=False)

    has_error = any(v["severity"] == "error" for v in violations)

    if args.format == "json":
        print(json.dumps({
            "summary": {
                "total_method_content_count": len(manifest["elements"]),
                "with_plane_label_count": sum(
                    1 for el in manifest["elements"]
                    if el.get("plane") in {"internal", "public", "sample"}
                ),
                "violations_count": len(violations),
            },
            "violations": violations,
        }, indent=2, ensure_ascii=False))
    else:
        total = len(manifest["elements"])
        labeled = sum(
            1 for el in manifest["elements"]
            if el.get("plane") in {"internal", "public", "sample"}
        )
        coverage = (labeled / total * 100.0) if total else 100.0
        plane_summary = (
            f"  plane=internal: {sum(1 for el in manifest['elements'] if el['plane']=='internal')}"
            f" / plane=public: {sum(1 for el in manifest['elements'] if el['plane']=='public')}"
            f" / plane=sample: {sum(1 for el in manifest['elements'] if el['plane']=='sample')}"
        )
        warns = [v for v in violations if v["severity"] == "warning"]
        if has_error:
            print(f"Method labeling: FAIL ({sum(1 for v in violations if v['severity']=='error')} errors / {len(warns)} warnings / {coverage:.2f}% coverage)")
            for v in violations[:10]:
                print(f"  [{v['severity']}] {v['code']}: {v['path']} — {v['message']}")
            if len(violations) > 10:
                print(f"  ... ({len(violations) - 10} more)")
            print("Run: stride method labels --suggest <path>  for AI-suggested frontmatter.")
        elif warns:
            print(f"Method labeling: PASS with warnings ({total} elements, 0 errors, {len(warns)} warnings, {coverage:.2f}% labeled-or-classified)")
            print(plane_summary)
            for v in warns[:5]:
                print(f"  [warning] {v['code']}: {v['path']}")
            if len(warns) > 5:
                print(f"  ... ({len(warns) - 5} more warnings)")
        else:
            print(f"Method labeling: PASS ({total} elements, 0 violations)")
            print(plane_summary)
            print(f"  coverage:       {coverage:.2f}%")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
