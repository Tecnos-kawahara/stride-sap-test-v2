"""stride method preview — local Method snapshot build (no push).

Contract: CT-CLI-02 (specs/method_store_publishing/contracts/cli_method_publish_schema.yaml)
Covers:   AC-US-FEATMETHODSTOREPUBLISHING-001-01 (preview portion).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import EXIT_OK, EXIT_PATH_NOT_FOUND, EXIT_USAGE_ERROR


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stride method preview")
    parser.add_argument("--serve", action="store_true",
                        help="Start a local MCP placeholder server on port 8765")
    parser.add_argument("--root", default=".", help="target root directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: root not found: {root}", file=sys.stderr)
        return EXIT_PATH_NOT_FOUND

    lock_path = root / "specs" / "method_ssot_externalization" / "implementation-details" / "method-store.lock.json"
    if not lock_path.exists():
        print(f"Error: method-store.lock.json not found at {lock_path}. Run 'stride method audit' first.",
              file=sys.stderr)
        return EXIT_USAGE_ERROR

    with lock_path.open(encoding="utf-8") as fh:
        lock = json.load(fh)

    summary = {
        "feature": "FEAT-METHODSTOREPUBLISHING",
        "preview_root": str(root),
        "lock_path": str(lock_path),
        "schema_version": lock.get("schema_version"),
        "method_version": lock.get("method_version") or lock.get("root_version"),
        "elements_total": len(lock.get("elements", [])),
        "no_unintended_exposure": lock.get("ip_boundary_audit", {}).get("no_unintended_exposure"),
        "serve_local_mcp": args.serve,
    }

    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("=== stride method preview ===")
        for k, v in summary.items():
            print(f"  {k}: {v}")
        if args.serve:
            print("  [serve] Local MCP placeholder is reserved for Feature ③ implementation.")

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
