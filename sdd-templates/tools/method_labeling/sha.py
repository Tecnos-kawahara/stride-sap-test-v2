"""Compute git short-sha per file (current HEAD blob)."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


def git_blob_sha(path: Path, repo_root: Path) -> str:
    """Return the git short-sha (7 chars) of the file in the working tree.

    Falls back to a deterministic content sha-1 (mimicking git's blob hash) when
    git is unavailable or the file is unstaged.
    """
    try:
        proc = subprocess.run(
            ["git", "hash-object", str(path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        return proc.stdout.strip()[:7]
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return _content_blob_sha(path)[:7]


def _content_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()
