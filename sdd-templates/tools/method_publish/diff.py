"""stride method diff — Method Store diff vs. previous tag, draft RELEASE_NOTES.

Contract: CT-CLI-02. Covers: input for AC-US-FEATMETHODSTOREPUBLISHING-002-01.
Output Markdown matches CT-FILE-02 (release_notes_schema) summary section.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import EXIT_OK, EXIT_USAGE_ERROR, EXIT_VALIDATION_FAILURE


def _git(*args: str, cwd: Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False).stdout


def _resolve_tag_ref(against: str, repo: Path) -> str:
    if against in ("stable", "staging", "edge"):
        # In real usage, query ghcr.io for the latest tag of the channel.
        # For local diff, fall back to tag pattern match.
        if against == "stable":
            tags = _git("tag", "--list", "v[0-9]*", "--sort=-v:refname", cwd=repo).splitlines()
        elif against == "staging":
            tags = _git("tag", "--list", "v[0-9]*-rc.*", "--sort=-v:refname", cwd=repo).splitlines()
        else:
            tags = _git("tag", "--list", "edge-*", "--sort=-creatordate", cwd=repo).splitlines()
        if not tags:
            return "HEAD~10"
        return tags[0].strip()
    return against


def _grouped_changes(repo: Path, ref: str) -> dict[str, list[str]]:
    diff_output = _git("diff", "--name-only", f"{ref}..HEAD", cwd=repo)
    files = [line for line in diff_output.splitlines() if line.strip()]
    groups: dict[str, list[str]] = {
        "templates": [],
        "skills": [],
        "policies": [],
        "hooks": [],
        "validators": [],
        "method_content_other": [],
    }
    for f in files:
        if f.startswith("sdd-templates/templates/"):
            groups["templates"].append(f)
        elif f.startswith("cowork-plugin/skills/") or f.endswith(".skill.md"):
            groups["skills"].append(f)
        elif f.startswith("shared/policies/"):
            groups["policies"].append(f)
        elif f.startswith("sdd-templates/hooks/"):
            groups["hooks"].append(f)
        elif "validator" in f or "checker" in f:
            groups["validators"].append(f)
        elif f.startswith("docs/") or f.startswith("memory/") or f.startswith("archive/"):
            groups["method_content_other"].append(f)
    return groups


def _render_markdown(against: str, ref: str, groups: dict[str, list[str]]) -> str:
    out = [f"## Changes from {against} ({ref})\n"]
    total = 0
    for key, files in groups.items():
        if not files:
            out.append(f"- {key}: 0 changes")
            continue
        out.append(f"- {key}: {len(files)} modified")
        total += len(files)
    out.append(f"\n**Total Method element changes: {total}**\n")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stride method diff")
    parser.add_argument("--against", default="stable",
                        help="Compare base (stable | staging | edge | <semver tag>)")
    parser.add_argument("--root", default=".", help="repo root")
    parser.add_argument("--output", default="",
                        help="Output path for RELEASE_NOTES draft (empty = stdout)")
    parser.add_argument("--format", choices=["text", "json", "markdown"], default="markdown")
    args = parser.parse_args(argv)

    repo = Path(args.root).resolve()
    if not (repo / ".git").exists():
        print(f"Error: not a git repository: {repo}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    ref = _resolve_tag_ref(args.against, repo)
    if not ref:
        print(f"Error: cannot resolve tag for {args.against}", file=sys.stderr)
        return EXIT_VALIDATION_FAILURE

    groups = _grouped_changes(repo, ref)

    if args.format == "json":
        rendered = json.dumps({
            "against": args.against,
            "resolved_ref": ref,
            "groups": groups,
        }, ensure_ascii=False, indent=2)
    else:
        rendered = _render_markdown(args.against, ref, groups)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"diff written to: {args.output}")
    else:
        print(rendered)

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
