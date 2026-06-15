#!/usr/bin/env python3
"""
Run Report Generator — STRIDE Learning Loop 可視化 (v4.5)

Run 完了時に .planning/ と walkthrough.md を解析し、
GitHub Issue 用の構造化コメント（Markdown）を生成する。

Usage:
    python3 sdd-templates/tools/run_report_generator.py <run-dir>
    python3 sdd-templates/tools/run_report_generator.py <run-dir> --post --issue 7
    python3 sdd-templates/tools/run_report_generator.py <run-dir> --post --issue 7 --labels
    python3 sdd-templates/tools/run_report_generator.py --test
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    yaml = None  # Optional — only needed for frontmatter parsing


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class Finding:
    index: int = 0
    finding_type: str = "investigation"
    description: str = ""
    impact: str = "medium"
    action: str = ""


@dataclass
class Decision:
    index: int = 0
    decision: str = ""
    rationale: str = ""
    status: str = "accepted"
    adr: str = "—"


@dataclass
class ChangelogEntry:
    file_path: str = ""
    change_type: str = "modified"
    summary: str = ""


@dataclass
class SpecImpact:
    target: str = ""
    impact_type: str = ""
    description: str = ""
    resolution: str = "🟢 対応済み"


@dataclass
class RunReport:
    run_id: str = ""
    wi_id: str = ""
    mode: str = "autopilot"
    duration: str = "—"
    findings: List[Finding] = field(default_factory=list)
    decisions: List[Decision] = field(default_factory=list)
    changelog: List[ChangelogEntry] = field(default_factory=list)
    spec_impacts: List[SpecImpact] = field(default_factory=list)
    spec_impact_level: str = "none"  # none / proposed / required
    plan_phases: int = 0
    plan_decisions: int = 0
    findings_count: int = 0
    lessons_count: int = 0
    has_lessons: bool = False


# =============================================================================
# Parsers
# =============================================================================


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        return {}
    yml = parts[0].lstrip("-").strip()
    if yaml:
        try:
            return yaml.safe_load(yml) or {}
        except Exception:
            pass
    # Fallback: simple key: value parse
    result = {}
    for line in yml.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def parse_findings(text: str) -> List[Finding]:
    """Parse findings.md into Finding objects."""
    findings = []
    if not text.strip():
        return findings

    # Split by ## Investigation or ## Finding headings
    sections = re.split(r'(?=## (?:Investigation|Finding)\s*\d*)', text)
    for i, section in enumerate(sections):
        if not re.match(r'## (?:Investigation|Finding)', section):
            continue

        f = Finding(index=i)

        # Extract type from heading
        heading_match = re.match(r'## (Investigation|Finding)\s*\d*:\s*(.*)', section)
        if heading_match:
            f.finding_type = heading_match.group(1).lower()
            f.description = heading_match.group(2).strip()

        # Extract sub-fields
        question = re.search(r'\*\*(?:Question|質問)\*\*:\s*(.*)', section)
        finding = re.search(r'\*\*(?:Finding|発見)\*\*:\s*(.*)', section)
        decision = re.search(r'\*\*(?:Decision|判断)\*\*:\s*(.*)', section)

        if finding:
            f.description = finding.group(1).strip()
        elif question and not f.description:
            f.description = question.group(1).strip()

        if decision:
            f.action = decision.group(1).strip()

        # Infer impact from keywords
        desc_lower = (f.description + " " + f.action).lower()
        if any(w in desc_lower for w in ("セキュリティ", "security", "authz", "critical", "ブロッカー")):
            f.impact = "high"
        elif any(w in desc_lower for w in ("新規", "new", "追加", "add", "作成", "create")):
            f.impact = "medium"
        else:
            f.impact = "low"

        findings.append(f)

    # Re-index
    for i, f in enumerate(findings):
        f.index = i + 1

    return findings


def parse_decisions(text: str) -> List[Decision]:
    """Parse plan.md Decisions/Approach or Phase table."""
    decisions = []
    if not text.strip():
        return decisions

    # Method 1: Parse "## Approach" numbered items
    approach = re.search(r'## Approach\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    if approach:
        for match in re.finditer(r'^\d+\.\s+(.+)', approach.group(1), re.MULTILINE):
            decisions.append(Decision(
                decision=match.group(1).strip(),
                rationale="Plan approach step",
                status="accepted",
            ))

    # Method 2: Parse "## Phases" table
    phases_match = re.search(r'## Phases\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    phase_count = 0
    if phases_match:
        for row in re.finditer(r'\|\s*\d+\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|', phases_match.group(1)):
            phase_count += 1

    # Method 3: Parse explicit "## Decisions" section
    dec_section = re.search(r'## Decisions\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
    if dec_section:
        for match in re.finditer(r'[-*]\s+\*\*(.+?)\*\*:\s*(.*)', dec_section.group(1)):
            decisions.append(Decision(
                decision=match.group(1).strip(),
                rationale=match.group(2).strip(),
                status="accepted",
            ))

    # Re-index
    for i, d in enumerate(decisions):
        d.index = i + 1

    return decisions


def parse_changelog(walkthrough_text: str) -> List[ChangelogEntry]:
    """Parse walkthrough.md for changed files."""
    entries = []
    if not walkthrough_text.strip():
        return entries

    # Parse "Code diff:" section items
    code_diff = re.search(r'(?:Code diff|Files changed|変更ファイル)[:\n](.*?)(?=\n#|\n\n[A-Z]|\Z)', walkthrough_text, re.DOTALL | re.IGNORECASE)
    if code_diff:
        for match in re.finditer(r'[-*]\s+`?([^\s`]+(?:\.\w+)?)`?\s*[—\-–:]\s*(.*)', code_diff.group(1)):
            filepath = match.group(1).strip()
            summary = match.group(2).strip()
            change_type = "added" if "新規" in summary or "new" in summary.lower() else "modified"
            entries.append(ChangelogEntry(file_path=filepath, change_type=change_type, summary=summary))

    # Parse explicit file list with +/- stats
    stats_match = re.search(r'Files changed:\s*(\d+)\s*files?\s*\(([^)]+)\)', walkthrough_text)
    if not entries and stats_match:
        entries.append(ChangelogEntry(
            file_path=f"({stats_match.group(1)} files)",
            change_type="modified",
            summary=stats_match.group(2).strip(),
        ))

    return entries


def parse_spec_impact(walkthrough_text: str, findings_text: str) -> tuple:
    """Determine spec impact level and details."""
    impacts = []
    level = "none"

    spec_files = ("spec.md", "plan.md", "tasks.md", "contracts/")

    # Check if walkthrough mentions spec file changes
    for sf in spec_files:
        if sf in walkthrough_text.lower():
            section_match = re.search(
                rf'{re.escape(sf)}.*?(?:変更|追加|修正|update|add|change)',
                walkthrough_text, re.IGNORECASE,
            )
            if section_match:
                impacts.append(SpecImpact(
                    target=sf,
                    impact_type="更新",
                    description=section_match.group(0)[:60],
                    resolution="🟢 対応済み",
                ))

    # Check findings for unresolved spec proposals
    if findings_text:
        proposal_patterns = [
            r'仕様.*(?:変更|追加|見直し)',
            r'spec.*(?:change|update|add)',
            r'AC.*(?:追記|追加)',
            r'閾値.*変更',
        ]
        for pat in proposal_patterns:
            for m in re.finditer(pat, findings_text, re.IGNORECASE):
                impacts.append(SpecImpact(
                    target="findings",
                    impact_type="提案",
                    description=m.group(0)[:60],
                    resolution="🟡 proposed",
                ))
                if level == "none":
                    level = "proposed"

    # Check for "Spec Drift Status" section in walkthrough
    drift_section = re.search(r'# Spec Drift Status.*?(?=\n# |\Z)', walkthrough_text, re.DOTALL)
    if drift_section:
        critical = re.search(r'Critical drifts:\s*(\d+)', drift_section.group(0))
        high = re.search(r'High drifts:\s*(\d+)', drift_section.group(0))
        if critical and int(critical.group(1)) > 0:
            level = "required"
            impacts.append(SpecImpact(
                target="spec.md",
                impact_type="drift:critical",
                description=f"Critical drift: {critical.group(1)} items",
                resolution="🔴 未対応",
            ))
        elif high and int(high.group(1)) > 0:
            if level != "required":
                level = "proposed"

    if impacts and level == "none":
        level = "proposed" if any(i.resolution != "🟢 対応済み" for i in impacts) else "none"

    return level, impacts


def count_phases(plan_text: str) -> int:
    return len(re.findall(r'\|\s*\d+\s*\|', plan_text))


def count_lessons(lessons_text: str) -> int:
    if not lessons_text.strip():
        return 0
    patterns = re.findall(r'[-*]\s+\*\*', lessons_text)
    if patterns:
        return len(patterns)
    # Fallback: count ## headings minus title
    headings = re.findall(r'^## ', lessons_text, re.MULTILINE)
    return max(len(headings) - 1, 0) if headings else (1 if len(lessons_text) > 50 else 0)


# =============================================================================
# Report Generation
# =============================================================================


def generate_report(run_dir: Path) -> RunReport:
    """Parse a Run directory and generate a RunReport."""
    report = RunReport()

    # Determine run_id and wi_id from path
    # Expected: specs/<feature>/runs/<WI-ID>/RUN-YYYYMMDD-HHMM/
    report.run_id = run_dir.name
    if run_dir.parent.name.startswith("WI-"):
        report.wi_id = run_dir.parent.name

    # Read walkthrough.md
    wt_text = _read(run_dir / "walkthrough.md")
    if wt_text:
        fm = _parse_frontmatter(wt_text)
        report.run_id = fm.get("run_id", report.run_id)
        report.wi_id = fm.get("wi_id", report.wi_id)
        report.mode = fm.get("mode", "autopilot")

    # Read .planning/ files
    planning_dir = run_dir / ".planning"
    plan_text = _read(planning_dir / "plan.md")
    findings_text = _read(planning_dir / "findings.md")
    lessons_text = _read(planning_dir / "lessons.md")

    # Parse findings
    report.findings = parse_findings(findings_text)
    report.findings_count = len(report.findings)

    # Parse decisions from plan.md
    report.decisions = parse_decisions(plan_text)
    report.plan_phases = count_phases(plan_text)
    report.plan_decisions = len(report.decisions)

    # Parse changelog from walkthrough
    report.changelog = parse_changelog(wt_text)

    # Parse spec impact
    report.spec_impact_level, report.spec_impacts = parse_spec_impact(wt_text, findings_text)

    # Lessons
    report.lessons_count = count_lessons(lessons_text)
    report.has_lessons = report.lessons_count > 0

    # Duration from lessons.md Time Breakdown
    time_match = re.search(r'合計[：:]?\s*(.*)', lessons_text)
    if time_match:
        report.duration = time_match.group(1).strip()

    return report


def format_report(report: RunReport) -> str:
    """Format RunReport as GitHub Issue comment markdown."""
    lines = []
    lines.append(f"## 🏃 Run Complete: {report.run_id}")
    lines.append("")
    lines.append(f"**WI:** {report.wi_id} | **Mode:** {report.mode} | **Duration:** {report.duration}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Findings
    fc = len(report.findings)
    lines.append(f"### 📋 Findings ({fc}件)")
    lines.append("")
    if report.findings:
        lines.append("| # | 種別 | 発見内容 | 影響度 | 対応 |")
        lines.append("|---|------|---------|--------|------|")
        for f in report.findings:
            lines.append(f"| F-{f.index} | {f.finding_type} | {f.description} | {f.impact} | {f.action or '—'} |")
    else:
        lines.append("_なし_")
    lines.append("")

    # Decisions
    dc = len(report.decisions)
    lines.append(f"### 🔍 Decisions ({dc}件)")
    lines.append("")
    if report.decisions:
        lines.append("| # | 判断内容 | 根拠 | ステータス | ADR |")
        lines.append("|---|---------|------|-----------|-----|")
        for d in report.decisions:
            lines.append(f"| D-{d.index} | {d.decision} | {d.rationale} | {d.status} | {d.adr} |")
    else:
        lines.append("_なし_")
    lines.append("")

    # Changelog
    lines.append("### 📝 Changelog")
    lines.append("")
    if report.changelog:
        lines.append("| ファイル | 変更種別 | 概要 |")
        lines.append("|---------|---------|------|")
        for c in report.changelog:
            lines.append(f"| {c.file_path} | {c.change_type} | {c.summary} |")
    else:
        lines.append("_変更なし_")
    lines.append("")

    # Spec Impact
    lines.append("### 🔄 Spec Impact")
    lines.append("")
    if report.spec_impacts:
        lines.append("| 影響先 | 種別 | 内容 | 対応状況 |")
        lines.append("|--------|------|------|---------|")
        for s in report.spec_impacts:
            lines.append(f"| {s.target} | {s.impact_type} | {s.description} | {s.resolution} |")
    else:
        lines.append("_仕様への影響なし_")
    lines.append("")

    # Planning Evidence
    lines.append("### 📊 Planning Evidence")
    lines.append("")
    lines.append(f"- plan.md: {report.plan_phases} phases, {report.plan_decisions} decisions recorded")
    lines.append(f"- findings.md: {report.findings_count} findings")
    lines.append(f"- lessons.md: {report.lessons_count} reusable pattern(s)")
    lines.append("")
    lines.append("---")
    lines.append(f"> 🤖 Auto-generated by Claude Code (SDD v4.5)")
    lines.append(f"> Run artifacts: `{report.run_id}/`")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# GitHub Integration
# =============================================================================


def _run_gh(*args: str) -> tuple:
    """Run gh CLI, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def post_comment(issue_number: str, comment: str) -> bool:
    """Post markdown comment to GitHub Issue."""
    rc, out, err = _run_gh("issue", "comment", issue_number, "--body", comment)
    if rc != 0:
        print(f"ERROR: Failed to post comment: {err}", file=sys.stderr)
        return False
    print(f"Comment posted to issue #{issue_number}")
    return True


def _findings_label(count: int) -> str:
    if count == 0:
        return "findings:0"
    elif count <= 3:
        return "findings:1-3"
    else:
        return "findings:4+"


def _decisions_label(count: int) -> str:
    if count == 0:
        return "decisions:0"
    elif count <= 3:
        return "decisions:1-3"
    else:
        return "decisions:4+"


def _findings_field_value(count: int) -> str:
    """Map findings count to project field option name."""
    if count == 0:
        return "0"
    elif count <= 3:
        return "1-3"
    else:
        return "4+"


def _decisions_field_value(count: int) -> str:
    """Map decisions count to project field option name."""
    if count == 0:
        return "0"
    elif count <= 3:
        return "1-3"
    else:
        return "4+"


def _discover_project_info(owner: str, project_number: int) -> Optional[dict]:
    """Discover project ID, field IDs, and option IDs via gh CLI.

    Returns dict:
        {
            "project_id": "PVT_...",
            "fields": {
                "Findings": {"field_id": "...", "options": {"0": "id", "1-3": "id", "4+": "id"}},
                ...
            }
        }
    """
    import json as _json

    # Get field list as JSON
    rc, out, err = _run_gh(
        "project", "field-list", str(project_number),
        "--owner", owner, "--format", "json",
    )
    if rc != 0:
        print(f"WARNING: Cannot list project fields: {err}", file=sys.stderr)
        return None

    try:
        data = _json.loads(out)
    except Exception as e:
        print(f"WARNING: Cannot parse project fields JSON: {e}", file=sys.stderr)
        return None

    target_fields = {"Findings", "Decisions", "Spec Impact", "Learning"}
    fields = {}
    for f in data.get("fields", []):
        if f["name"] in target_fields:
            options = {}
            for opt in f.get("options", []):
                options[opt["name"]] = opt["id"]
            fields[f["name"]] = {"field_id": f["id"], "options": options}

    if not fields:
        print("WARNING: No Learning Loop fields found on project.", file=sys.stderr)
        return None

    # Discover project node ID via GraphQL
    rc2, out2, err2 = _run_gh(
        "project", "view", str(project_number),
        "--owner", owner, "--format", "json",
    )
    project_id = None
    if rc2 == 0:
        try:
            pdata = _json.loads(out2)
            project_id = pdata.get("id")
        except Exception:
            pass

    if not project_id:
        # Fallback: try item-list to get project ID from items
        rc3, out3, _ = _run_gh(
            "project", "item-list", str(project_number),
            "--owner", owner, "--format", "json", "--limit", "1",
        )
        if rc3 == 0:
            try:
                idata = _json.loads(out3)
                # project ID is in the item data
                for item in idata.get("items", []):
                    if "id" in item:
                        # item ID starts with PVTI_, project ID is PVT_...
                        # We can extract from the item ID prefix
                        pass
            except Exception:
                pass

    return {"project_id": project_id, "fields": fields}


def _get_project_item_id(owner: str, project_number: int, issue_number: str) -> Optional[str]:
    """Get the project item ID for a given issue number."""
    import json as _json

    rc, out, _ = _run_gh(
        "project", "item-list", str(project_number),
        "--owner", owner, "--format", "json",
    )
    if rc != 0:
        return None

    try:
        data = _json.loads(out)
        for item in data.get("items", []):
            content = item.get("content", {})
            if str(content.get("number")) == str(issue_number):
                return item["id"]
    except Exception:
        pass

    return None


def update_project_fields(
    issue_number: str,
    report: RunReport,
    owner: str,
    project_number: int,
) -> bool:
    """Update GitHub Project custom fields based on report data.

    Sets Findings, Decisions, Spec Impact, and Learning fields.
    Non-blocking: prints warnings on failure but does not exit.
    """
    info = _discover_project_info(owner, project_number)
    if not info:
        return False

    project_id = info["project_id"]
    if not project_id:
        print("WARNING: Cannot determine project node ID.", file=sys.stderr)
        return False

    item_id = _get_project_item_id(owner, project_number, issue_number)
    if not item_id:
        print(f"WARNING: Issue #{issue_number} not found in project {project_number}.", file=sys.stderr)
        return False

    # Build field value map
    field_values = {
        "Findings": _findings_field_value(report.findings_count),
        "Decisions": _decisions_field_value(len(report.decisions)),
        "Spec Impact": report.spec_impact_level,
        "Learning": "pattern" if report.has_lessons else "—",
    }

    success = True
    for field_name, value in field_values.items():
        field_info = info["fields"].get(field_name)
        if not field_info:
            print(f"WARNING: Field '{field_name}' not found on project.", file=sys.stderr)
            continue

        option_id = field_info["options"].get(value)
        if not option_id:
            print(f"WARNING: Option '{value}' not found for field '{field_name}'.", file=sys.stderr)
            continue

        rc, _, err = _run_gh(
            "project", "item-edit",
            "--project-id", project_id,
            "--id", item_id,
            "--field-id", field_info["field_id"],
            "--single-select-option-id", option_id,
        )
        if rc != 0:
            print(f"WARNING: Failed to set {field_name}={value}: {err}", file=sys.stderr)
            success = False

    if success:
        print(f"Project fields updated for issue #{issue_number}: "
              f"Findings={field_values['Findings']}, "
              f"Decisions={field_values['Decisions']}, "
              f"Spec Impact={field_values['Spec Impact']}, "
              f"Learning={field_values['Learning']}")

    return success


def apply_labels(issue_number: str, report: RunReport) -> bool:
    """Apply STRIDE Learning Loop labels to the Issue."""
    labels = [
        _findings_label(report.findings_count),
        _decisions_label(len(report.decisions)),
        f"spec-impact:{report.spec_impact_level}",
    ]
    if report.has_lessons:
        labels.append("learning:pattern")

    # Remove old findings/decisions/spec-impact labels first
    rc, out, _ = _run_gh("issue", "view", issue_number, "--json", "labels")
    if rc == 0:
        import json
        try:
            data = json.loads(out)
            existing = [l["name"] for l in data.get("labels", [])]
            old_labels = [l for l in existing if l.startswith(("findings:", "decisions:", "spec-impact:", "learning:"))]
            for old in old_labels:
                _run_gh("issue", "edit", issue_number, "--remove-label", old)
        except Exception:
            pass

    label_str = ",".join(labels)
    rc, _, err = _run_gh("issue", "edit", issue_number, "--add-label", label_str)
    if rc != 0:
        print(f"ERROR: Failed to apply labels: {err}", file=sys.stderr)
        return False
    print(f"Labels applied to issue #{issue_number}: {label_str}")
    return True


# =============================================================================
# Self-Tests
# =============================================================================


def run_tests() -> bool:
    """Run self-tests."""
    import tempfile

    print("Running run_report_generator.py self-tests...\n")
    passed = 0
    total = 0

    def check(name, condition, msg=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  PASS: {name}")
        else:
            print(f"  FAIL: {name} — {msg}")

    # Test 1: Parse findings
    print("Test 1: Parse findings")
    findings_text = """# Findings: WI-TEST

## Investigation 1: 既存UIコンポーネント構成
- **Question**: 既存のDialogで確認ダイアログを実現できるか？
- **Finding**: 既存の AlertDialog はalertのみ対応。confirm用途には新規作成が必要。
- **Decision**: ConfirmDialog を新規作成し、共通コンポーネントとして配置。
- **Source**: src/components/AlertDialog.tsx

## Investigation 2: セキュリティ要件確認
- **Question**: 認可チェックの追加場所は？
- **Finding**: セキュリティ上、サーバーサイドで認可チェックを行う必要がある。
- **Decision**: middleware に authz ガードを追加。
"""
    findings = parse_findings(findings_text)
    check("findings count", len(findings) == 2, f"got {len(findings)}")
    check("findings[0] type", findings[0].finding_type == "investigation")
    check("findings[1] impact high", findings[1].impact == "high", f"got {findings[1].impact}")
    check("findings[0] action", "ConfirmDialog" in findings[0].action)

    # Test 2: Parse decisions
    print("\nTest 2: Parse decisions")
    plan_text = """# Plan: Test

## Goal
Test implementation.

## Approach
1. 既存UIコンポーネント調査
2. ボタン配置変更（CSS修正）
3. ConfirmDialog作成

## Status: COMPLETED

## Phases
| # | Phase | Status |
|---|-------|--------|
| 1 | 調査 | Done |
| 2 | 実装 | Done |
| 3 | テスト | Done |
"""
    decisions = parse_decisions(plan_text)
    check("decisions count", len(decisions) == 3, f"got {len(decisions)}")
    check("decisions[0]", "コンポーネント調査" in decisions[0].decision)
    phases = count_phases(plan_text)
    check("phase count", phases == 3, f"got {phases}")

    # Test 3: Parse changelog
    print("\nTest 3: Parse changelog")
    wt_text = """---
run_id: RUN-20260210-0900
wi_id: WI-TEST-001
mode: autopilot
---

# What changed
- Spec diff: AC-001 に対応
- Code diff:
  - `src/components/OrderEntryForm.tsx` — 登録ボタンを右下に移動
  - `src/components/ConfirmDialog.tsx` — 新規コンポーネント
  - `tests/e2e/order_entry.spec.ts` — E2Eテスト追加
- Files changed: 3 files (+142, -18)
"""
    changelog = parse_changelog(wt_text)
    check("changelog count", len(changelog) == 3, f"got {len(changelog)}")
    check("changelog[1] added", changelog[1].change_type == "added")
    check("changelog[0] modified", changelog[0].change_type == "modified")

    # Test 4: Spec impact
    print("\nTest 4: Spec impact")
    level, impacts = parse_spec_impact(
        "# Spec Drift Status\n- Critical drifts: 0\n- High drifts: 0\n",
        ""
    )
    check("no impact", level == "none")

    level2, impacts2 = parse_spec_impact(
        "# Spec Drift Status\n- Critical drifts: 2\n",
        ""
    )
    check("required impact", level2 == "required", f"got {level2}")

    level3, impacts3 = parse_spec_impact(
        "",
        "AC追記が必要: 新しいバリデーションルール"
    )
    check("proposed impact", level3 == "proposed", f"got {level3}")

    # Test 5: Lessons count
    print("\nTest 5: Lessons count")
    lessons_text = """# Lessons

## Reusable Patterns
- **Pattern A**: Description
- **Pattern B**: Description

## Errors
- なし

## Time Breakdown
- 合計: 約1時間
"""
    lc = count_lessons(lessons_text)
    check("lessons count", lc == 2, f"got {lc}")

    # Test 6: Full report generation from tempdir
    print("\nTest 6: Full report generation")
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / "RUN-20260215-1430"
        run_dir.mkdir()
        planning_dir = run_dir / ".planning"
        planning_dir.mkdir()

        (planning_dir / "plan.md").write_text(plan_text, encoding="utf-8")
        (planning_dir / "findings.md").write_text(findings_text, encoding="utf-8")
        (planning_dir / "lessons.md").write_text(lessons_text, encoding="utf-8")
        (run_dir / "walkthrough.md").write_text(wt_text, encoding="utf-8")

        report = generate_report(run_dir)
        check("report run_id", report.run_id == "RUN-20260210-0900")
        check("report wi_id", report.wi_id == "WI-TEST-001")
        check("report mode", report.mode == "autopilot")
        check("report findings", len(report.findings) == 2)
        check("report decisions", len(report.decisions) == 3)
        check("report changelog", len(report.changelog) == 3)
        check("report duration", "1時間" in report.duration)

        md = format_report(report)
        check("md has run header", "## 🏃 Run Complete" in md)
        check("md has findings table", "| F-1 |" in md)
        check("md has decisions table", "| D-1 |" in md)
        check("md has changelog", "| ファイル |" in md)
        check("md has spec impact", "### 🔄 Spec Impact" in md)
        check("md has planning evidence", "### 📊 Planning Evidence" in md)
        check("md has footer", "SDD v4.5" in md)

    # Test 7: Label generation
    print("\nTest 7: Label generation")
    check("findings:0", _findings_label(0) == "findings:0")
    check("findings:1-3", _findings_label(2) == "findings:1-3")
    check("findings:4+", _findings_label(5) == "findings:4+")
    check("decisions:0", _decisions_label(0) == "decisions:0")
    check("decisions:1-3", _decisions_label(3) == "decisions:1-3")
    check("decisions:4+", _decisions_label(4) == "decisions:4+")

    # Test 8: Empty inputs
    print("\nTest 8: Empty inputs")
    empty_findings = parse_findings("")
    check("empty findings", len(empty_findings) == 0)
    empty_decisions = parse_decisions("")
    check("empty decisions", len(empty_decisions) == 0)
    empty_changelog = parse_changelog("")
    check("empty changelog", len(empty_changelog) == 0)
    level_empty, impacts_empty = parse_spec_impact("", "")
    check("empty spec impact", level_empty == "none")

    # Test 9: Project field value mapping
    print("\nTest 9: Project field value mapping")
    check("findings_field 0", _findings_field_value(0) == "0")
    check("findings_field 1", _findings_field_value(1) == "1-3")
    check("findings_field 3", _findings_field_value(3) == "1-3")
    check("findings_field 4", _findings_field_value(4) == "4+")
    check("findings_field 10", _findings_field_value(10) == "4+")
    check("decisions_field 0", _decisions_field_value(0) == "0")
    check("decisions_field 2", _decisions_field_value(2) == "1-3")
    check("decisions_field 3", _decisions_field_value(3) == "1-3")
    check("decisions_field 5", _decisions_field_value(5) == "4+")

    # Test 10: Field value derivation from report
    print("\nTest 10: Field value derivation from report")
    test_report = RunReport(
        findings_count=2,
        decisions=[Decision(index=1), Decision(index=2), Decision(index=3), Decision(index=4)],
        spec_impact_level="proposed",
        has_lessons=True,
    )
    check("report findings→1-3", _findings_field_value(test_report.findings_count) == "1-3")
    check("report decisions→4+", _decisions_field_value(len(test_report.decisions)) == "4+")
    check("report spec_impact→proposed", test_report.spec_impact_level == "proposed")
    check("report learning→pattern", ("pattern" if test_report.has_lessons else "—") == "pattern")

    test_report2 = RunReport(findings_count=0, decisions=[], spec_impact_level="none", has_lessons=False)
    check("report2 findings→0", _findings_field_value(test_report2.findings_count) == "0")
    check("report2 decisions→0", _decisions_field_value(len(test_report2.decisions)) == "0")
    check("report2 learning→—", ("pattern" if test_report2.has_lessons else "—") == "—")

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    return passed == total


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Run Report Generator — STRIDE Learning Loop (v4.5)",
    )
    parser.add_argument("run_dir", nargs="?", type=Path, help="Run directory path")
    parser.add_argument("--post", action="store_true", help="Post comment to GitHub Issue")
    parser.add_argument("--issue", type=str, help="Issue number for --post")
    parser.add_argument("--labels", action="store_true", help="Apply labels (with --post)")
    parser.add_argument("--project-fields", action="store_true",
                        help="Update project custom fields (Findings/Decisions/Spec Impact/Learning)")
    parser.add_argument("--project", type=int, help="Project number (required with --project-fields)")
    parser.add_argument("--owner", type=str, help="Project owner (auto-detected from repo if omitted)")
    parser.add_argument("--test", action="store_true", help="Run self-tests")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.run_dir:
        parser.print_help()
        sys.exit(1)

    if not args.run_dir.exists():
        print(f"ERROR: Run directory not found: {args.run_dir}", file=sys.stderr)
        sys.exit(1)

    report = generate_report(args.run_dir)
    md = format_report(report)

    if args.post and args.issue:
        post_comment(args.issue, md)
        if args.labels:
            apply_labels(args.issue, report)
        if args.project_fields:
            if not args.project:
                print("ERROR: --project is required with --project-fields", file=sys.stderr)
                sys.exit(1)
            owner = args.owner
            if not owner:
                # Auto-detect owner from current repo
                rc, out, _ = _run_gh("repo", "view", "--json", "owner", "-q", ".owner.login")
                if rc == 0 and out:
                    owner = out
                else:
                    print("ERROR: Cannot detect owner. Use --owner.", file=sys.stderr)
                    sys.exit(1)
            update_project_fields(args.issue, report, owner, args.project)
    else:
        print(md)


if __name__ == "__main__":
    main()
