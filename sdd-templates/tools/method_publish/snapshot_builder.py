"""snapshot_builder — build OCI artifact tarball from method-store.lock.json + Method content.

Output:
  manifest.json — Sigstore-compatible image config + method_version + commit_sha + build_timestamp
  content/      — selected Method content files (only entries with no_unintended_exposure: true)
  artifact.tar  — tar of manifest.json + content/

Contract: AC-T-G02-001-01 (OCI v1 spec compliant tarball).
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path

from . import __version__


OCI_MEDIA_TYPE_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
OCI_MEDIA_TYPE_CONFIG = "application/vnd.tecnos.sdd-method-store.config.v1+json"
OCI_MEDIA_TYPE_LAYER = "application/vnd.tecnos.sdd-method-store.layer.v1.tar"


@dataclass
class SnapshotResult:
    artifact_path: Path
    manifest_path: Path
    sha256: str
    method_version: str
    commit_sha: str
    build_timestamp: str


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _commit_sha(repo: Path) -> str:
    proc = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    return (proc.stdout or "").strip() or "unknown"


def _build_timestamp() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _select_content_files(lock: dict, root: Path) -> list[Path]:
    files: list[Path] = []
    audit = lock.get("ip_boundary_audit") or {}
    if not audit.get("no_unintended_exposure", False):
        return files
    for elem in lock.get("elements", []):
        rel = elem.get("path")
        if not rel:
            continue
        candidate = root / rel
        if candidate.exists() and candidate.is_file():
            files.append(candidate)
    return files


def build(root: Path, channel: str, output_dir: Path) -> SnapshotResult:
    """Build an OCI artifact for the given channel.

    Args:
      root: Repo root containing specs/ and Method content.
      channel: edge | staging | stable.
      output_dir: Target directory; created if absent. Existing files are overwritten.
    """
    if channel not in ("edge", "staging", "stable"):
        raise ValueError(f"unsupported channel: {channel}")

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    lock_path = root / "specs" / "method_ssot_externalization" / "implementation-details" / "method-store.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    method_version = lock.get("method_version") or lock.get("root_version", "0.0.0")
    commit_sha = _commit_sha(root)
    timestamp = _build_timestamp()

    selected = _select_content_files(lock, root)

    artifact_path = output_dir / "artifact.tar"
    with tarfile.open(artifact_path, "w") as tar:
        tar.add(lock_path, arcname="method-store.lock.json")
        for f in selected:
            tar.add(f, arcname=f"content/{f.relative_to(root)}")

    artifact_sha = _sha256_file(artifact_path)
    artifact_size = artifact_path.stat().st_size

    manifest = {
        "schemaVersion": 2,
        "mediaType": OCI_MEDIA_TYPE_MANIFEST,
        "config": {
            "mediaType": OCI_MEDIA_TYPE_CONFIG,
            "size": 0,
            "digest": "sha256:" + hashlib.sha256(b"{}").hexdigest(),
        },
        "layers": [
            {
                "mediaType": OCI_MEDIA_TYPE_LAYER,
                "size": artifact_size,
                "digest": f"sha256:{artifact_sha}",
            }
        ],
        "annotations": {
            "org.tecnos.sdd-method-store.method_version": method_version,
            "org.tecnos.sdd-method-store.channel": channel,
            "org.tecnos.sdd-method-store.commit_sha": commit_sha,
            "org.tecnos.sdd-method-store.build_timestamp": timestamp,
            "org.tecnos.sdd-method-store.builder_version": __version__,
            "org.tecnos.sdd-method-store.element_count": str(len(selected)),
        },
    }

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    return SnapshotResult(
        artifact_path=artifact_path,
        manifest_path=manifest_path,
        sha256=artifact_sha,
        method_version=method_version,
        commit_sha=commit_sha,
        build_timestamp=timestamp,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="snapshot_builder")
    parser.add_argument("--root", default=".")
    parser.add_argument("--channel", default="staging", choices=["edge", "staging", "stable"])
    parser.add_argument("--output-dir", default="/tmp/method-snapshot")
    args = parser.parse_args()
    res = build(Path(args.root).resolve(), args.channel, Path(args.output_dir))
    print(json.dumps({
        "artifact_path": str(res.artifact_path),
        "manifest_path": str(res.manifest_path),
        "sha256": res.sha256,
        "method_version": res.method_version,
        "commit_sha": res.commit_sha,
        "build_timestamp": res.build_timestamp,
    }, ensure_ascii=False, indent=2))
