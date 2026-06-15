"""stride method publish — orchestrator (validate → snapshot → sign → push → notify).

Contract: CT-CLI-02. Covers AC-US-FEATMETHODSTOREPUBLISHING-001-01 (staging) +
AC-US-FEATMETHODSTOREPUBLISHING-002-01 (stable, via release_notes_generator + GitHub PR).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from . import (
    DEFAULT_REGISTRY,
    EXIT_AUTH_FAILURE,
    EXIT_OK,
    EXIT_SIGSTORE_OUTAGE,
    EXIT_USAGE_ERROR,
    EXIT_VALIDATION_FAILURE,
)
from .cosign_signer import SigstoreOutage, sign
from .oci_publisher import push
from .snapshot_builder import build


def _read_semver(root: Path) -> str:
    version_file = root / "sdd-templates" / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip().lstrip("v")
    return "0.0.0"


def _next_rc(channel: str) -> int:
    return int(os.environ.get("STRIDE_RC", "1"))


def _commit_sha7(root: Path) -> str:
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, check=False)
    return (proc.stdout or "").strip() or "0000000"


def _run_validate(root: Path) -> int:
    cmd = [sys.executable, "-m", "method_publish.validate", "--root", str(root)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stride method publish")
    parser.add_argument("--target", required=True, choices=["edge", "staging", "stable"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--root", default=".")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: root not found: {root}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    rc = _run_validate(root)
    if rc != 0:
        return EXIT_VALIDATION_FAILURE

    semver = _read_semver(root)
    sha7 = _commit_sha7(root)
    rc_n = _next_rc(args.target)

    # F2 follow-up #19.4 (2026-05-08): tempfile を context manager 化、
    # 確実に cleanup (旧実装は mkdtemp leak していた)
    with tempfile.TemporaryDirectory(prefix="stride-method-publish-") as workdir_str:
        workdir = Path(workdir_str)
        snap = build(root, args.target, workdir)

        image_ref = f"{DEFAULT_REGISTRY}:" + (
            f"edge-{sha7}" if args.target == "edge"
            else f"v{semver}-rc.{rc_n}" if args.target == "staging"
            else f"v{semver}"
        )

        try:
            sign_res = sign(
                image_ref,
                fallback_kms_uri=os.environ.get("TECNOS_KMS_URI"),
                dry_run=args.dry_run,
            )
        except SigstoreOutage as e:
            print(f"Sigstore outage and no fallback configured: {e}", file=sys.stderr)
            return EXIT_SIGSTORE_OUTAGE

        push_res = push(
            snap.artifact_path, snap.manifest_path,
            args.target, semver, rc_n if args.target == "staging" else None, sha7,
            registry=DEFAULT_REGISTRY, dry_run=args.dry_run,
        )

        summary = {
            "target": args.target,
            "image_ref": image_ref,
            "method_version": snap.method_version,
            "commit_sha": snap.commit_sha,
            "build_timestamp": snap.build_timestamp,
            "snapshot_sha256": snap.sha256,
            "signed": sign_res.signed,
            "rekor_uuid_or_log": sign_res.rekor_log_uuid,
            "fallback_used": sign_res.fallback_used,
            "pushed": push_res.pushed,
            "push_digest": push_res.digest,
            "dry_run": args.dry_run,
        }

        if args.format == "json":
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print("=== stride method publish ===")
            for k, v in summary.items():
                print(f"  {k}: {v}")

        if args.dry_run:
            return EXIT_OK
        if not sign_res.signed:
            return EXIT_VALIDATION_FAILURE
        if not push_res.pushed:
            return EXIT_AUTH_FAILURE
        return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
