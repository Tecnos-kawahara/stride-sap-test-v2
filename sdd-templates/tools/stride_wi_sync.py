#!/usr/bin/env python3
"""stride_wi_sync — Sync GitHub Work Item Issues → specs/*/work_items/WI-*.md

Hybrid WI management for Tecnos-STRIDE:
  - Day-to-day: WIs live as GitHub Issues (label: work-item)
  - Gate time:  This tool snapshots Issues → local markdown files for
                lint validation, approval tracking, and audit trail.

Usage:
  python3 stride_wi_sync.py                           # sync all WIs
  python3 stride_wi_sync.py --feature master-admin-ui  # sync specific feature
  python3 stride_wi_sync.py --dry-run                  # preview without writing
  python3 stride_wi_sync.py --status open              # only open issues
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


# ─── Helpers ────────────────────────────────────────────────────────

def run_gh(args: list[str]) -> str:
    """Run gh CLI and return stdout."""
    result = subprocess.run(
        ["gh"] + args, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"gh error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def get_repo() -> str:
    """Detect owner/repo from git remote."""
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Cannot detect repository. Run from within a git repo with gh auth.", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def fetch_issues(repo: str, label: str = "work-item", state: str = "all") -> list[dict]:
    """Fetch all Issues with the given label using gh api (paginated)."""
    issues: list[dict] = []
    page = 1
    while True:
        raw = run_gh([
            "api", f"repos/{repo}/issues",
            "-X", "GET",
            "--paginate",
            "-f", f"labels={label}",
            "-f", f"state={state}",
            "-f", "per_page=100",
        ])
        batch = json.loads(raw) if raw.strip() else []
        if not batch:
            break
        issues.extend(batch)
        # gh --paginate handles pagination automatically
        break
    return issues


# ─── Metadata Parsing ──────────────────────────────────────────────

# Matches a ```yaml ... ``` block in the issue body
YAML_BLOCK_RE = re.compile(
    r"```ya?ml\s*\n(.*?)```",
    re.DOTALL,
)

# Matches key: value or key: "value" lines (simple parser, no full YAML dep)
KV_RE = re.compile(r'^(\w[\w_]*):\s*(.+)$', re.MULTILINE)
LIST_ITEM_RE = re.compile(r'^\s*-\s*"?([^"]+)"?\s*$', re.MULTILINE)


def parse_yaml_block(body: str) -> dict[str, Any]:
    """Extract metadata from a ```yaml block in the issue body.
    
    Uses a lightweight regex parser to avoid PyYAML dependency.
    Handles simple key-value pairs, lists, and nested dicts (1 level).
    """
    m = YAML_BLOCK_RE.search(body or "")
    if not m:
        return {}

    block = m.group(1)
    result: dict[str, Any] = {}
    lines = block.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # Skip comments and blanks
        if not line or line.lstrip().startswith("#"):
            i += 1
            continue

        # Check for key: value
        kv = re.match(r'^(\w[\w_]*):\s*(.*)', line)
        if not kv:
            i += 1
            continue

        key = kv.group(1)
        val = kv.group(2).strip()

        if val == "" or val == "|":
            # Could be a nested dict or list — look ahead
            nested: dict[str, Any] = {}
            items: list[str] = []
            i += 1
            while i < len(lines):
                nline = lines[i].rstrip()
                if not nline or nline.lstrip().startswith("#"):
                    i += 1
                    continue
                # Nested key: value (indented)
                nkv = re.match(r'^\s{2,}(\w[\w_]*):\s*(.*)', nline)
                if nkv:
                    nk, nv = nkv.group(1), nkv.group(2).strip()
                    # Nested list
                    if nv in ("[]", ""):
                        nested[nk] = _collect_list(lines, i + 1)
                        # Skip past collected list items
                        i += 1
                        while i < len(lines) and re.match(r'^\s{4,}-', lines[i]):
                            i += 1
                        continue
                    else:
                        nested[nk] = _clean_val(nv)
                    i += 1
                    continue
                # List item
                lm = re.match(r'^\s{2,}-\s*"?([^"]*)"?\s*$', nline)
                if lm:
                    items.append(lm.group(1).strip())
                    i += 1
                    continue
                break  # Back to top-level key

            if nested:
                result[key] = nested
            elif items:
                result[key] = items
            else:
                result[key] = ""
            continue

        # Inline empty list
        if val == "[]":
            result[key] = []
            i += 1
            continue

        # Inline list [a, b, c]
        if val.startswith("["):
            inner = val.strip("[]")
            result[key] = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()] if inner.strip() else []
            i += 1
            continue

        result[key] = _clean_val(val)
        i += 1

    return result


def _collect_list(lines: list[str], start: int) -> list[str]:
    """Collect list items starting from a given line index."""
    items = []
    i = start
    while i < len(lines):
        lm = re.match(r'^\s+-\s*"?([^"]*)"?\s*$', lines[i])
        if lm:
            items.append(lm.group(1).strip())
            i += 1
        else:
            break
    return items


def _clean_val(v: str) -> str:
    """Strip surrounding quotes and inline comments."""
    v = re.sub(r'\s*#.*$', '', v)  # Remove inline comments
    v = v.strip().strip('"').strip("'")
    return v


# ─── Issue Form Parsing ────────────────────────────────────────────

def parse_issue_form(body: str) -> dict[str, Any]:
    """Parse metadata from GitHub Issue Form (### Section format)."""
    result: dict[str, Any] = {}
    if not body:
        return result

    sections = re.split(r'^### (.+)$', body, flags=re.MULTILINE)
    # sections[0] is before first ###, then alternating title/content
    for idx in range(1, len(sections) - 1, 2):
        title = sections[idx].strip()
        content = sections[idx + 1].strip()
        if not content or content == "_No response_":
            continue

        # Map form field titles to metadata keys
        key_map = {
            "WI ID": "wi_id",
            "Feature ID": "feature_id",
            "Complexity": "complexity",
            "Execution Mode": "mode",
            "Priority": "priority",
            "Risk Flags": "risk_flags",
            "Spec References": "spec_refs",
            "Contract References": "contract_refs",
            "Intent": "intent",
            "Scope": "scope",
            "Plan": "plan",
            "Acceptance Criteria": "acceptance_criteria",
        }
        key = key_map.get(title)
        if not key:
            continue

        if key == "risk_flags":
            # Parse checked checkboxes
            flags = []
            for line in content.split("\n"):
                m = re.match(r'- \[X\]\s*(.+?)(?:\s*—|$)', line)
                if m:
                    flags.append(m.group(1).strip())
            result[key] = flags
        elif key in ("spec_refs",):
            result[key] = [l.strip() for l in content.split("\n") if l.strip()]
        elif key == "contract_refs":
            refs: dict[str, list[str]] = {"acceptance_ids": [], "contract_ids": []}
            for line in content.split("\n"):
                if line.strip().startswith("acceptance_ids:"):
                    ids_str = line.split(":", 1)[1].strip()
                    refs["acceptance_ids"] = [x.strip() for x in ids_str.split(",") if x.strip()]
                elif line.strip().startswith("contract_ids:"):
                    ids_str = line.split(":", 1)[1].strip()
                    refs["contract_ids"] = [x.strip() for x in ids_str.split(",") if x.strip()]
            result[key] = refs
        else:
            result[key] = content

    return result


# ─── Label-Feature Map ──────────────────────────────────────────────

def _load_label_feature_map() -> dict[str, str]:
    """Load label→feature_id mapping from config or scan specs/ directories.
    
    Looks for sdd-templates/config/label_feature_map.json first.
    Falls back to auto-generating from specs/ directory names using
    convention: directory_name → FEAT-{UPPERCASE_ABBREV}.
    """
    config_path = Path("sdd-templates/config/label_feature_map.json")
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    # Auto-generate from specs/ directories
    specs_dir = Path("specs")
    if not specs_dir.exists():
        return {}
    
    mapping: dict[str, str] = {}
    for d in specs_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            # Convention: use uppercase first letters as label
            # e.g., sample_erp_addon → FEAT-SEA, agentops-plane → FEAT-AGT
            parts = re.split(r'[-_]', d.name)
            abbrev = "".join(p[0].upper() for p in parts if p)[:4]
            label = f"FEAT-{abbrev}"
            mapping[label] = d.name
    return mapping


# ─── WI File Generation ────────────────────────────────────────────

@dataclass
class WorkItem:
    wi_id: str = ""
    feature_id: str = ""
    title: str = ""
    complexity: str = "medium"
    mode: str = "autopilot"
    priority: str = "P2-Medium"
    risk_flags: list[str] = field(default_factory=list)
    spec_refs: list[str] = field(default_factory=list)
    contract_refs: dict[str, list[str]] = field(default_factory=lambda: {"acceptance_ids": [], "contract_ids": []})
    test_refs: list[str] = field(default_factory=list)
    owners: dict[str, str] = field(default_factory=lambda: {"pm": "@PM", "tech_lead": "@TL", "dev": "@DEV", "qa": "@QA"})
    # Sections
    intent: str = ""
    scope: str = ""
    plan: str = ""
    acceptance_criteria: str = ""
    # GitHub metadata
    issue_number: int = 0
    issue_url: str = ""
    state: str = "open"
    assignees: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)


def issue_to_work_item(issue: dict) -> WorkItem:
    """Convert a GitHub Issue dict to a WorkItem."""
    wi = WorkItem()
    wi.issue_number = issue.get("number", 0)
    wi.issue_url = issue.get("html_url", "")
    wi.state = issue.get("state", "open")
    wi.assignees = [a["login"] for a in (issue.get("assignees") or [])]
    wi.labels = [l["name"] for l in (issue.get("labels") or [])]

    raw_title = issue.get("title", "")
    # Strip common prefixes: [WI], [FEAT-XXX], [SU-N] etc.
    wi.title = re.sub(r'^\[[\w\-]+\]\s*', '', raw_title).strip()
    wi.title = re.sub(r'^\[[\w\-]+\]\s*', '', wi.title).strip()  # Handle double prefix

    body = issue.get("body", "") or ""

    # Try YAML block first (markdown template), then Issue Form format
    meta = parse_yaml_block(body)
    if not meta:
        meta = parse_issue_form(body)

    # Infer wi_id from metadata, title, or issue number
    wi_id_from_title = ""
    # Match patterns like "WI-SF-003", "WI-ERP-SAMPLE-001", "SU-1" in title
    # First try: explicit WI ID after [WI] prefix (e.g., "[WI] WI-SF-003: description")
    title_match = re.search(r'(?:^|\s)((?:WI|SU)-[\w]+-[\w\-]+)', raw_title)
    if not title_match:
        # Fallback: match within brackets (e.g., "[SU-1]")
        title_match = re.search(r'\[((?:WI|SU)-[\w\-]+)\]', raw_title)
    if title_match:
        wi_id_from_title = title_match.group(1)
    wi.wi_id = meta.get("wi_id") or wi_id_from_title or f"WI-{wi.issue_number}"
    # Infer feature_id from metadata, labels, or title
    feature_id = meta.get("feature_id", "")
    if not feature_id:
        # Try to infer from labels using label_feature_map
        # Map is loaded from sdd-templates/config/label_feature_map.json if exists,
        # otherwise uses convention: specs/ directories are scanned
        label_feature_map = _load_label_feature_map()
        for lbl in wi.labels:
            if lbl in label_feature_map:
                feature_id = label_feature_map[lbl]
                break
        # Also try from title prefix like [FEAT-AGT]
        if not feature_id:
            feat_match = re.search(r'\[(FEAT-\w+)\]', raw_title)
            if feat_match and feat_match.group(1) in label_feature_map:
                feature_id = label_feature_map[feat_match.group(1)]
    wi.feature_id = feature_id
    wi.complexity = meta.get("complexity", "medium")
    wi.mode = meta.get("mode", "autopilot")
    wi.priority = meta.get("priority", "P2-Medium")
    wi.risk_flags = meta.get("risk_flags", [])
    wi.spec_refs = meta.get("spec_refs", [])
    wi.test_refs = meta.get("test_refs", [])
    wi.intent = meta.get("intent", "")
    wi.scope = meta.get("scope", "")
    wi.plan = meta.get("plan", "")
    wi.acceptance_criteria = meta.get("acceptance_criteria", "")

    cr = meta.get("contract_refs", {})
    if isinstance(cr, dict):
        wi.contract_refs = {
            "acceptance_ids": cr.get("acceptance_ids", []),
            "contract_ids": cr.get("contract_ids", []),
        }

    owners = meta.get("owners", {})
    if isinstance(owners, dict):
        wi.owners.update(owners)

    return wi


def work_item_to_md(wi: WorkItem) -> str:
    """Render a WorkItem as a markdown file with YAML front-matter."""
    lines = [
        "---",
        f'wi_id: "{wi.wi_id}"',
        f'title: "{wi.title}"',
        f'feature_id: "{wi.feature_id}"',
        f'complexity: "{wi.complexity}"',
        f'mode: "{wi.mode}"',
        f'priority: "{wi.priority}"',
        f'risk_flags: {json.dumps(wi.risk_flags)}',
        f'state: "{wi.state}"',
        "dependencies: []",
        "spec_refs:",
    ]
    for ref in (wi.spec_refs or ["basic_design.md", "spec.md", "plan.md"]):
        lines.append(f'  - "{ref}"')
    lines.append("contract_refs:")
    lines.append(f'  acceptance_ids: {json.dumps(wi.contract_refs.get("acceptance_ids", []))}')
    lines.append(f'  contract_ids: {json.dumps(wi.contract_refs.get("contract_ids", []))}')
    lines.append(f'test_refs: {json.dumps(wi.test_refs)}')
    lines.append("owners:")
    for k, v in wi.owners.items():
        lines.append(f'  {k}: "{v}"')
    lines.append("github:")
    lines.append(f"  issue_number: {wi.issue_number}")
    lines.append(f'  issue_url: "{wi.issue_url}"')
    lines.append(f'  assignees: {json.dumps(wi.assignees)}')
    lines.append(f'  labels: {json.dumps(wi.labels)}')
    lines.append("---")
    lines.append("")

    lines.append("# Intent")
    lines.append("")
    lines.append(wi.intent or "<!-- TBD -->")
    lines.append("")

    lines.append("# Scope (UI/IO/API/MSG/DB/Authz/Migration/Ops)")
    lines.append("")
    lines.append(wi.scope or "<!-- TBD -->")
    lines.append("")

    lines.append("# Plan")
    lines.append("")
    lines.append(wi.plan or "<!-- TBD -->")
    lines.append("")

    lines.append("## Risk Flags")
    risk_all = [
        "authz", "audit_log", "db_schema", "data_migration",
        "cross_module", "new_api", "performance_sensitive", "ui_only",
    ]
    for flag in risk_all:
        checked = "x" if flag in wi.risk_flags else " "
        lines.append(f"- [{checked}] {flag}")
    lines.append("")

    lines.append("# Acceptance Criteria")
    lines.append("")
    lines.append(wi.acceptance_criteria or "<!-- TBD -->")
    lines.append("")

    return "\n".join(lines) + "\n"


# ─── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sync GitHub Work Item Issues → specs/*/work_items/WI-*.md"
    )
    parser.add_argument("--feature", help="Filter by feature_id (specs/ subdirectory)")
    parser.add_argument("--label", default="work-item",
                        help="Issue label to filter (default: work-item)")
    parser.add_argument("--status", default="all", choices=["open", "closed", "all"],
                        help="Issue state filter (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    repo = get_repo()
    print(f"📦 Repository: {repo}")
    print(f"🔍 Fetching work-item issues (state={args.status})...")

    issues = fetch_issues(repo, label=args.label, state=args.status)
    print(f"   Found {len(issues)} issues")

    if not issues:
        print("✅ No work-item issues found.")
        return

    # Convert and group by feature
    work_items: list[WorkItem] = []
    skipped = 0
    for issue in issues:
        # Skip pull requests (they also appear in /issues endpoint)
        if "pull_request" in issue:
            continue
        wi = issue_to_work_item(issue)

        # Filter by feature if specified
        if args.feature and wi.feature_id and wi.feature_id != args.feature:
            skipped += 1
            continue
        # If no feature_id in metadata, use --feature flag
        if not wi.feature_id and args.feature:
            wi.feature_id = args.feature

        if not wi.feature_id:
            print(f"  ⚠️  #{issue['number']} '{issue['title']}' — no feature_id, skipping")
            skipped += 1
            continue

        work_items.append(wi)

    if skipped and args.verbose:
        print(f"   Skipped {skipped} issues (no feature_id or filtered out)")

    # Write files
    written = 0
    for wi in work_items:
        # Sanitize wi_id for filename
        safe_id = re.sub(r'[^\w\-]', '_', wi.wi_id)
        out_dir = Path("specs") / wi.feature_id / "work_items"
        out_file = out_dir / f"{safe_id}.md"
        md = work_item_to_md(wi)

        if args.dry_run:
            print(f"  [dry-run] {out_file}")
            if args.verbose:
                print(f"    wi_id={wi.wi_id} state={wi.state} mode={wi.mode}")
        else:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.write_text(md, encoding="utf-8")
            print(f"  ✅ {out_file}")
        written += 1

    action = "would write" if args.dry_run else "wrote"
    print(f"\n🏁 Done: {action} {written} WI files")


if __name__ == "__main__":
    main()
