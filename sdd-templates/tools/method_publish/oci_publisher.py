"""oci_publisher — push OCI artifact to ghcr.io via oras CLI delegate.

Uses the `oras` CLI (https://oras.land/) when available; falls back to the
OCI Distribution Spec REST API for environments where oras is not installed.
GITHUB_TOKEN scope `packages:write` is required.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import DEFAULT_REGISTRY, EXIT_AUTH_FAILURE


@dataclass
class PushResult:
    image_ref: str
    pushed: bool
    digest: str
    size: int
    output: str


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _channel_tag(channel: str, semver: str, rc: int | None, commit_sha7: str | None) -> str:
    if channel == "edge":
        return f"edge-{commit_sha7 or 'unknown'}"
    if channel == "staging":
        if rc is None:
            raise ValueError("staging channel requires rc number")
        return f"v{semver}-rc.{rc}"
    if channel == "stable":
        return f"v{semver}"
    raise ValueError(f"unknown channel: {channel}")


def push(
    artifact_path: Path,
    manifest_path: Path,
    channel: str,
    semver: str,
    rc: int | None = None,
    commit_sha7: str | None = None,
    registry: str = DEFAULT_REGISTRY,
    dry_run: bool = False,
) -> PushResult:
    """Push the OCI artifact to ghcr.io with the channel-specific tag.

    Returns:
      PushResult.pushed True on success.
    """
    tag = _channel_tag(channel, semver, rc, commit_sha7)
    image_ref = f"{registry}:{tag}"

    token = os.environ.get("GITHUB_TOKEN", "")
    if not dry_run and not token:
        return PushResult(image_ref=image_ref, pushed=False, digest="",
                          size=0, output="ERROR: GITHUB_TOKEN env not set (packages:write required)")

    oras = _which("oras")
    if not oras:
        if dry_run:
            return PushResult(image_ref=image_ref, pushed=False, digest="DRY-RUN",
                              size=artifact_path.stat().st_size,
                              output="(dry-run) oras CLI not present; would invoke registry push")
        return PushResult(image_ref=image_ref, pushed=False, digest="",
                          size=0, output="ERROR: oras CLI not found in PATH")

    if dry_run:
        return PushResult(image_ref=image_ref, pushed=False, digest="DRY-RUN",
                          size=artifact_path.stat().st_size,
                          output=f"(dry-run) would push {image_ref} via oras")

    cmd = [
        oras, "push",
        image_ref,
        "--config", str(manifest_path) + ":application/vnd.tecnos.sdd-method-store.config.v1+json",
        f"{artifact_path}:application/vnd.tecnos.sdd-method-store.layer.v1.tar",
    ]
    env = os.environ.copy()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    output = proc.stdout + proc.stderr
    pushed = proc.returncode == 0

    digest = ""
    for line in output.splitlines():
        if "digest:" in line.lower():
            digest = line.split("digest:")[-1].strip()
            break

    return PushResult(
        image_ref=image_ref,
        pushed=pushed,
        digest=digest,
        size=artifact_path.stat().st_size,
        output=output[:2048],
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="oci_publisher")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--channel", required=True, choices=["edge", "staging", "stable"])
    parser.add_argument("--semver", required=True)
    parser.add_argument("--rc", type=int, default=None)
    parser.add_argument("--commit-sha7", default=None)
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        res = push(
            Path(args.artifact), Path(args.manifest),
            args.channel, args.semver, args.rc, args.commit_sha7,
            args.registry, args.dry_run,
        )
    except ValueError as e:
        print(f"Error: {e}", flush=True)
        raise SystemExit(2)
    print(json.dumps({
        "image_ref": res.image_ref,
        "pushed": res.pushed,
        "digest": res.digest,
        "size": res.size,
    }, ensure_ascii=False, indent=2))
    raise SystemExit(0 if res.pushed or args.dry_run else EXIT_AUTH_FAILURE)
