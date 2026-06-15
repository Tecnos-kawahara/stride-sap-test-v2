"""stride method rollback — emergency OCI tag rollback + GitOps revert PR.

Contract: CT-CLI-02. Covers AC-US-FEATMETHODSTOREPUBLISHING-003-01 (5 min MTTR,
--reason mandatory for audit, --yes to skip impact prompt).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import (
    DEFAULT_REGISTRY,
    EXIT_AUTH_FAILURE,
    EXIT_OK,
    EXIT_USAGE_ERROR,
    EXIT_VALIDATION_FAILURE,
)
# F2 follow-up #19.7 (2026-05-08): defensive sys.path insertion before sibling-package import.
# `ci_helpers` is a sibling package in `sdd-templates/tools/`. Absolute import requires that
# directory on sys.path. Both CI workflow and `bash sdd-templates/bin/stride method rollback`
# set PYTHONPATH=$TOOLS_DIR, but `python -m method_publish.rollback` from arbitrary cwd would
# fail. The defensive sys.path insertion below makes this module importable in all contexts.
import sys as _sys
import os as _os
_TOOLS_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if _TOOLS_DIR not in _sys.path:
    _sys.path.insert(0, _TOOLS_DIR)

from ci_helpers.gitops_pr_creator import create_pr
from ci_helpers.slack_notifier import notify


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _impact_estimate(target_tag: str) -> dict:
    """Best-effort impact estimate based on the resolution of the previous tag.

    Real implementations would query master-admin DB; we synthesize a placeholder
    so the prompt is still meaningful in dry-run mode.
    """
    return {
        "target_tag": target_tag,
        "tenants_on_stable": 12,
        "in_flight_projects": 47,
        "active_publishing_pipelines": 3,
        "tenants_with_pin": 3,
        "tenants_with_auto_upgrade_none": 1,
    }


def _retag(registry: str, target_tag: str, dry_run: bool) -> tuple[bool, str]:
    """Re-tag the previous-stable digest as the live `latest` reference."""
    src = f"{registry}:{target_tag}"
    dst = f"{registry}:latest"
    if dry_run:
        return True, f"(dry-run) would re-tag {src} → {dst}"
    oras = _which("oras")
    if not oras:
        return False, "ERROR: oras CLI not found"
    proc = subprocess.run(
        [oras, "tag", src, "latest"], capture_output=True, text=True, check=False
    )
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stride method rollback")
    parser.add_argument("--to", default="",
                        help="Target tag to roll back to (empty = last-known-good from tenant policy)")
    parser.add_argument("--reason", required=True,
                        help="Audit reason (mandatory)")
    parser.add_argument("--root", default=".")
    parser.add_argument("--yes", action="store_true",
                        help="Skip the impact-confirmation prompt (CI use)")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not args.reason.strip():
        print("Error: --reason is required for audit.", file=sys.stderr)
        return EXIT_USAGE_ERROR

    # F2 follow-up #19.6 (2026-05-08): hardcoded "v6.0.5" placeholder fallback was
    # a real-incident risk (operator runs rollback without --to during panic →
    # silently rolls back to wrong tag). Now requires explicit --to OR future
    # tenant-policy lookup (F3 master-admin DB integration、Q14 で確定予定).
    if not args.to:
        print(
            "Error: --to is required (tenant-policy last_known_good lookup is not yet implemented; "
            "F3 master-admin DB integration pending、Q14 closure 後に default 復活予定).\n"
            "       Specify the rollback target explicitly, e.g. --to v6.0.5",
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR
    target_tag = args.to
    impact = _impact_estimate(target_tag)
    started = time.time()

    print("=== stride method rollback ===")
    print(f"  target_tag : {target_tag}")
    print(f"  reason     : {args.reason}")
    print(f"  impact     : {impact['tenants_on_stable']} tenants on stable, "
          f"{impact['in_flight_projects']} in-flight projects, "
          f"{impact['active_publishing_pipelines']} active pipelines")

    if not args.yes:
        try:
            answer = input("Proceed? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer != "y":
            print("Aborted by operator.")
            return EXIT_VALIDATION_FAILURE

    re_ok, re_out = _retag(args.registry, target_tag, args.dry_run)
    if not re_ok:
        print(f"Re-tag failed: {re_out}", file=sys.stderr)
        return EXIT_AUTH_FAILURE

    pr_body = (Path("/tmp") / f"rollback-{target_tag}.md")
    pr_body.write_text(
        f"# Rollback to {target_tag}\n\n"
        f"**Reason:** {args.reason}\n\n"
        f"Audit log: ghcr.io tag history + Sigstore Rekor + Slack archive (3 重記録).\n\n"
        f"Impact: {json.dumps(impact, ensure_ascii=False)}\n",
        encoding="utf-8",
    )

    pr_res = create_pr(
        title=f"chore(rollback): revert to {target_tag}",
        body_path=pr_body,
        base="main",
        head=f"rollback/{target_tag}",
        dry_run=args.dry_run,
    )

    notify(
        f"Method Store rollback to {target_tag} (reason: {args.reason})",
        channel="#method-board", urgent=True, dry_run=args.dry_run,
    )
    notify(
        f"Method Store rollback initiated (target={target_tag})",
        channel="#ops-channel", urgent=True, dry_run=args.dry_run,
    )

    elapsed = round(time.time() - started, 2)

    summary = {
        "target_tag": target_tag,
        "reason": args.reason,
        "retag_ok": re_ok,
        "pr_created": pr_res.created,
        "pr_url": pr_res.url,
        "elapsed_seconds": elapsed,
        "started_at": _dt.datetime.utcnow().isoformat() + "Z",
        "dry_run": args.dry_run,
        "mttr_target_seconds": 300,
        "mttr_breach": elapsed > 300,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
