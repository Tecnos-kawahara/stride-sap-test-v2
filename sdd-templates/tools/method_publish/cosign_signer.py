"""cosign_signer — keyless cosign sign + Rekor transparency log.

Primary: Sigstore Fulcio + Rekor with GitHub Actions OIDC (R-PLAN-002 normal path).
Fallback: Tecnos KMS-managed key (R-PLAN-002 mitigation when Sigstore is down).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import COSIGN_FULCIO, COSIGN_REKOR


@dataclass
class SignResult:
    image_ref: str
    signed: bool
    fulcio_url: str
    rekor_url: str
    fallback_used: bool
    rekor_log_uuid: str
    cosign_output: str


class SigstoreOutage(Exception):
    """Raised when Fulcio + Rekor are both unreachable and fallback is unavailable."""


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _probe_url(url: str, timeout: float) -> bool:
    """Best-effort reachability probe for one URL."""
    if _which("curl"):
        proc = subprocess.run(
            ["curl", "-sSf", "-o", "/dev/null", "--max-time", str(int(timeout)), url],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode == 0:
            return True
    try:
        from urllib import request
        with request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 400
    except Exception:
        return False


def _sigstore_reachable(timeout: float = 5.0) -> bool:
    """Probe BOTH Fulcio AND Rekor (F2 follow-up #19.1, 2026-05-08).

    Sigstore comprises Fulcio (cert issuance) + Rekor (transparency log).
    A Rekor-only outage — historically the more common Sigstore incident —
    will pass a Fulcio-only check, then `cosign sign` fails at Rekor upload.
    Per R-PLAN-002, KMS fallback should activate; this requires both probes.
    """
    fulcio_ok = _probe_url(f"{COSIGN_FULCIO}/api/v1/configuration", timeout)
    if not fulcio_ok:
        return False
    # Rekor public-instance health endpoint
    rekor_ok = _probe_url(f"{COSIGN_REKOR}/api/v1/log", timeout)
    return fulcio_ok and rekor_ok


def sign(image_ref: str, fallback_kms_uri: str | None = None, dry_run: bool = False) -> SignResult:
    """Sign an OCI image reference with cosign.

    GitHub Actions environment variables ACTIONS_ID_TOKEN_REQUEST_URL +
    ACTIONS_ID_TOKEN_REQUEST_TOKEN must be present for keyless flow.
    """
    cosign = _which("cosign")
    if not cosign:
        if dry_run:
            return SignResult(
                image_ref=image_ref, signed=False,
                fulcio_url=COSIGN_FULCIO, rekor_url=COSIGN_REKOR,
                fallback_used=False, rekor_log_uuid="DRY-RUN",
                cosign_output="(dry-run) cosign not installed; would invoke keyless sign",
            )
        raise FileNotFoundError("cosign not found in PATH; install Sigstore cosign first.")

    fallback_used = False
    if not _sigstore_reachable():
        if not fallback_kms_uri:
            raise SigstoreOutage("Sigstore unreachable and no Tecnos KMS fallback configured.")
        fallback_used = True

    if dry_run:
        return SignResult(
            image_ref=image_ref, signed=False,
            fulcio_url=COSIGN_FULCIO, rekor_url=COSIGN_REKOR,
            fallback_used=fallback_used, rekor_log_uuid="DRY-RUN",
            cosign_output=f"(dry-run) would sign {image_ref} (fallback={fallback_used})",
        )

    env = os.environ.copy()
    env.setdefault("COSIGN_EXPERIMENTAL", "1")

    if fallback_used:
        cmd = [cosign, "sign", "--key", fallback_kms_uri, image_ref, "--yes"]
    else:
        cmd = [cosign, "sign", image_ref, "--yes"]

    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)

    rekor_log_uuid = "unknown"
    for line in proc.stderr.splitlines() + proc.stdout.splitlines():
        if "uuid" in line.lower() or "rekor" in line.lower():
            rekor_log_uuid = line.strip()[:120]
            break

    return SignResult(
        image_ref=image_ref,
        signed=proc.returncode == 0,
        fulcio_url=COSIGN_FULCIO,
        rekor_url=COSIGN_REKOR,
        fallback_used=fallback_used,
        rekor_log_uuid=rekor_log_uuid,
        cosign_output=(proc.stdout + proc.stderr)[:1024],
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(prog="cosign_signer")
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--fallback-kms", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    res = sign(args.image_ref, fallback_kms_uri=args.fallback_kms or None, dry_run=args.dry_run)
    print(json.dumps({
        "image_ref": res.image_ref,
        "signed": res.signed,
        "fallback_used": res.fallback_used,
        "rekor_log_uuid": res.rekor_log_uuid,
    }, ensure_ascii=False, indent=2))
