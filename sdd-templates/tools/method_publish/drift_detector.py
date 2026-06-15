"""drift_detector — compare local Method Store source against deployed tag.

Computes a snapshot from the current repository state and compares its sha256
to the `manifest.json` recorded for the deployed tag (latest stable by default).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import DEFAULT_REGISTRY, EXIT_OK, EXIT_VALIDATION_FAILURE
from .snapshot_builder import build


def _pull_manifest_digest(registry: str, tag: str) -> str | None:
    """Return the sha256 digest of the artifact layer for the given tag."""
    oras = shutil.which("oras")
    if not oras:
        return None
    proc = subprocess.run(
        [oras, "manifest", "fetch", f"{registry}:{tag}"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        m = json.loads(proc.stdout)
        layers = m.get("layers", [])
        if layers:
            return layers[0].get("digest", "").replace("sha256:", "")
    except Exception:
        pass
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stride method drift")
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--tag", default="latest", help="deployed tag to compare against")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    # F2 follow-up #19.4 (2026-05-08): tempfile を context manager 化、確実 cleanup
    with tempfile.TemporaryDirectory(prefix="stride-drift-") as workdir_str:
        workdir = Path(workdir_str)
        snap = build(root, "staging", workdir)

        deployed_digest = _pull_manifest_digest(args.registry, args.tag)

        if deployed_digest is None:
            result = {
                "drift": "unknown",
                "reason": "deployed manifest unavailable (oras missing or not authenticated)",
                "source_sha256": snap.sha256,
            }
            if args.format == "json":
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print("=== stride method drift ===")
                for k, v in result.items():
                    print(f"  {k}: {v}")
            return EXIT_OK

        drift = snap.sha256 != deployed_digest
        result = {
            "drift": drift,
            "source_sha256": snap.sha256,
            "deployed_sha256": deployed_digest,
            "tag": args.tag,
        }
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("=== stride method drift ===")
            for k, v in result.items():
                print(f"  {k}: {v}")

        return EXIT_VALIDATION_FAILURE if drift else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
