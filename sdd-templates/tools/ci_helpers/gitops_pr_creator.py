"""gitops_pr_creator — auto-create GitHub PR for stable releases or rollback events.

Uses the gh CLI (GitHub Actions runners ship with it). For local dry-run no
external auth is performed.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PRResult:
    created: bool
    url: str
    title: str
    output: str


def create_pr(title: str, body_path: Path, base: str, head: str, dry_run: bool = False) -> PRResult:
    gh = shutil.which("gh")
    if not gh:
        return PRResult(False, "", title,
                        f"(dry-run) gh CLI not found; would create PR {head} → {base}")

    if dry_run:
        return PRResult(False, "", title,
                        f"(dry-run) gh pr create -t {title} -B {base} -H {head}")

    if not os.environ.get("GITHUB_TOKEN"):
        return PRResult(False, "", title, "ERROR: GITHUB_TOKEN env not set")

    cmd = [gh, "pr", "create",
           "--title", title,
           "--body-file", str(body_path),
           "--base", base,
           "--head", head]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    output = (proc.stdout + proc.stderr).strip()

    url = ""
    for line in proc.stdout.splitlines():
        if line.startswith("https://github.com/") and "/pull/" in line:
            url = line.strip()
            break

    return PRResult(proc.returncode == 0, url, title, output[:2048])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gitops_pr_creator")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", required=True, help="Path to PR body Markdown file")
    parser.add_argument("--base", default="main")
    parser.add_argument("--head", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    res = create_pr(args.title, Path(args.body), args.base, args.head, args.dry_run)
    print(json.dumps({
        "created": res.created,
        "url": res.url,
        "title": res.title,
    }, ensure_ascii=False, indent=2))
    return 0 if (res.created or args.dry_run) else 3


if __name__ == "__main__":
    raise SystemExit(main())
