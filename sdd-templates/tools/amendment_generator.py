#!/usr/bin/env python3
"""
Amendment Generator — STRIDE Spec Amendment Full Lifecycle (v5.0)

Run の Findings / Decisions から蓄積された spec-impact を、
仕様改訂（Amendment）として正式にライフサイクル管理する。

Full Lifecycle:
  1. analyze    — Impact analysis
  2. draft      — Generate amendment draft
  3. create     — Create Amendment Issue
  4. apply      — PM承認確認 → Spec反映PR作成 (amendment:applying)
  5. finalize   — PRマージ後 → ラベル更新 + spec-impact解消 + 新WI起票 + close
  *  auto-check — spec-impact蓄積の自動検出

Usage:
    python3 sdd-templates/tools/amendment_generator.py analyze --feature FEAT-SF-CONN --topic "通貨"
    python3 sdd-templates/tools/amendment_generator.py draft --feature FEAT-SF-CONN --title "通貨追加" --spec-sections "AC-SF-002" --scope "単一通貨のみ"
    python3 sdd-templates/tools/amendment_generator.py create --feature FEAT-SF-CONN --draft amendment-draft.md
    python3 sdd-templates/tools/amendment_generator.py apply --issue 25
    python3 sdd-templates/tools/amendment_generator.py finalize --issue 25
    python3 sdd-templates/tools/amendment_generator.py auto-check --feature FEAT-SF-CONN
    python3 sdd-templates/tools/amendment_generator.py --test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    yaml = None


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class RelatedFinding:
    wi_id: str = ""
    index: int = 0
    finding_type: str = ""
    description: str = ""
    impact: str = "medium"


@dataclass
class RelatedDecision:
    wi_id: str = ""
    index: int = 0
    decision: str = ""
    status: str = "accepted"


@dataclass
class AffectedSpec:
    file_path: str = ""
    section: str = ""
    summary: str = ""


@dataclass
class AffectedWI:
    wi_id: str = ""
    status: str = ""
    spec_impact: str = ""
    description: str = ""
    issue_number: int = 0


@dataclass
class AnalysisResult:
    feature_id: str = ""
    topic: str = ""
    findings: List[RelatedFinding] = field(default_factory=list)
    decisions: List[RelatedDecision] = field(default_factory=list)
    affected_specs: List[AffectedSpec] = field(default_factory=list)
    affected_wis: List[AffectedWI] = field(default_factory=list)
    related_issues: List[Dict[str, str]] = field(default_factory=list)
    recommendation: str = ""
    risks: str = ""


@dataclass
class SpecDiff:
    file_path: str = ""
    section: str = ""
    change_type: str = ""
    description: str = ""


@dataclass
class NewWICandidate:
    wi_id: str = ""
    description: str = ""


# =============================================================================
# Helpers
# =============================================================================


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _run_gh(*args: str) -> Tuple[int, str, str]:
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _run_cmd(*args: str) -> Tuple[int, str, str]:
    """General command execution (git etc.)"""
    result = subprocess.run(
        list(args),
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _find_project_root(start: Path) -> Path:
    p = start.resolve()
    for _ in range(10):
        if (p / "sdd-templates").exists() or (p / "specs").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return start.resolve()


def _resolve_feature_dir(project_root: Path, feature_id: str) -> Optional[Path]:
    specs = project_root / "specs"
    # Try direct match
    candidate = specs / feature_id
    if candidate.exists():
        return candidate
    # Try all dirs for symlink targets
    if specs.exists():
        for d in specs.iterdir():
            if d.is_dir() or d.is_symlink():
                if d.name == feature_id:
                    return d
    return None


def _get_repo_name() -> str:
    rc, out, _ = _run_gh("repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner")
    return out if rc == 0 else ""


def _search_issues_by_label(label: str, limit: int = 50) -> List[Dict[str, Any]]:
    rc, out, _ = _run_gh(
        "issue", "list", "--label", label,
        "--state", "all", "--limit", str(limit),
        "--json", "number,title,labels,state",
    )
    if rc != 0 or not out:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def _get_issue_body(issue_num: int) -> str:
    rc, out, _ = _run_gh("issue", "view", str(issue_num), "--json", "body", "-q", ".body")
    return out if rc == 0 else ""


def _get_issue_labels(issue_num: int) -> List[str]:
    rc, out, _ = _run_gh("issue", "view", str(issue_num), "--json", "labels", "-q", "[.labels[].name]")
    if rc != 0 or not out:
        return []
    try:
        return json.loads(out)
    except Exception:
        return []


def _next_amd_id(feature_id: str) -> str:
    short = feature_id.replace("FEAT-", "")
    issues = _search_issues_by_label("amendment")
    existing = []
    pattern = re.compile(rf'AMD-{re.escape(short)}-(\d+)', re.IGNORECASE)
    for iss in issues:
        m = pattern.search(iss.get("title", ""))
        if m:
            existing.append(int(m.group(1)))
    next_num = max(existing, default=0) + 1
    return f"AMD-{short}-{next_num:03d}"


# =============================================================================
# Core: analyze
# =============================================================================


def _collect_findings(feature_dir: Path, topic: str) -> List[RelatedFinding]:
    results = []
    runs_dir = feature_dir / "runs"
    if not runs_dir.exists():
        return results
    topic_lower = topic.lower()

    for wi_dir in sorted(runs_dir.iterdir()):
        if not wi_dir.is_dir():
            continue
        wi_id = wi_dir.name
        for run_dir in sorted(wi_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            findings_path = run_dir / ".planning" / "findings.md"
            text = _read_text(findings_path)
            if not text:
                continue

            sections = re.split(r'(?=## (?:Investigation|Finding)\s*\d*)', text)
            for section in sections:
                if not re.match(r'## (?:Investigation|Finding)', section):
                    continue
                if topic_lower not in section.lower():
                    continue

                heading = re.match(r'## (?:Investigation|Finding)\s*(\d*):\s*(.*)', section)
                idx = int(heading.group(1)) if heading and heading.group(1) else 0
                desc = heading.group(2).strip() if heading else ""

                finding_match = re.search(r'\*\*(?:Finding|発見)\*\*:\s*(.*?)(?:\n\n|\n\*\*|\Z)', section, re.DOTALL)
                if finding_match:
                    desc = finding_match.group(1).strip().split("\n")[0]

                impact = "medium"
                s_lower = section.lower()
                if any(w in s_lower for w in ("critical", "ブロッカー", "セキュリティ")):
                    impact = "high"
                elif any(w in s_lower for w in ("仕様変更", "spec change", "ac追記")):
                    impact = "high"

                results.append(RelatedFinding(
                    wi_id=wi_id, index=idx,
                    finding_type="investigation",
                    description=desc[:120],
                    impact=impact,
                ))
    return results


def _collect_decisions(feature_dir: Path, topic: str) -> List[RelatedDecision]:
    results = []
    runs_dir = feature_dir / "runs"
    if not runs_dir.exists():
        return results
    topic_lower = topic.lower()

    for wi_dir in sorted(runs_dir.iterdir()):
        if not wi_dir.is_dir():
            continue
        wi_id = wi_dir.name
        for run_dir in sorted(wi_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            plan_path = run_dir / ".planning" / "plan.md"
            text = _read_text(plan_path)
            if not text or topic_lower not in text.lower():
                continue

            # Parse Approach items
            approach = re.search(r'## Approach\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
            if approach:
                for m in re.finditer(r'^(\d+)\.\s+(.+)', approach.group(1), re.MULTILINE):
                    if topic_lower in m.group(2).lower():
                        results.append(RelatedDecision(
                            wi_id=wi_id, index=int(m.group(1)),
                            decision=m.group(2).strip()[:120],
                            status="accepted",
                        ))

            # Parse Decisions section
            dec_section = re.search(r'## Decisions\n(.*?)(?=\n## |\Z)', text, re.DOTALL)
            if dec_section:
                for m in re.finditer(r'[-*]\s+(.+)', dec_section.group(1)):
                    line = m.group(1).strip()
                    if topic_lower in line.lower():
                        results.append(RelatedDecision(
                            wi_id=wi_id, index=len(results) + 1,
                            decision=line[:120],
                            status="accepted",
                        ))
    return results


def _feature_matches_issue(feature_id: str, title: str, labels: List[str]) -> bool:
    """Check if an issue belongs to a feature using flexible matching."""
    short = feature_id.replace("FEAT-", "")  # e.g. "SF-CONN"
    # Direct match
    if short in title:
        return True
    # Check labels
    if any(feature_id in l for l in labels):
        return True
    # Extract WI prefix: FEAT-SF-CONN → "SF", match WI-SF-*
    parts = short.split("-")
    if parts:
        prefix = parts[0]  # e.g. "SF"
        if re.search(rf'WI-{re.escape(prefix)}-\d', title):
            return True
    return False


def _detect_affected_wis(feature_id: str) -> List[AffectedWI]:
    results = []
    for label in ("spec-impact:required", "spec-impact:proposed"):
        issues = _search_issues_by_label(label)
        for iss in issues:
            title = iss.get("title", "")
            labels = [l.get("name", "") for l in iss.get("labels", [])]
            if _feature_matches_issue(feature_id, title, labels):
                wi_match = re.search(r'WI-[A-Z0-9-]+', title)
                results.append(AffectedWI(
                    wi_id=wi_match.group(0) if wi_match else title[:30],
                    status=iss.get("state", ""),
                    spec_impact=label.split(":")[-1],
                    description=title,
                    issue_number=iss.get("number", 0),
                ))
    return results


def _detect_related_risk_dep(feature_id: str) -> List[Dict[str, str]]:
    results = []
    for label in ("risk", "dependency"):
        issues = _search_issues_by_label(label)
        for iss in issues:
            title = iss.get("title", "")
            labels = [l.get("name", "") for l in iss.get("labels", [])]
            if _feature_matches_issue(feature_id, title, labels):
                results.append({
                    "number": str(iss.get("number", "")),
                    "type": label,
                    "title": title,
                    "state": iss.get("state", ""),
                })
    return results


def cmd_analyze(args: argparse.Namespace) -> int:
    feature_id = args.feature
    topic = args.topic

    project_root = _find_project_root(Path.cwd())
    feature_dir = _resolve_feature_dir(project_root, feature_id)

    result = AnalysisResult(feature_id=feature_id, topic=topic)

    if feature_dir:
        result.findings = _collect_findings(feature_dir, topic)
        result.decisions = _collect_decisions(feature_dir, topic)

    result.affected_wis = _detect_affected_wis(feature_id)
    result.related_issues = _detect_related_risk_dep(feature_id)

    # Format output
    lines = [
        f"## 📊 Amendment Impact Analysis\n",
        f"**Feature:** {feature_id}",
        f"**Topic:** {topic}\n",
    ]

    lines.append(f"### 関連 Findings ({len(result.findings)}件)")
    if result.findings:
        lines.append("| WI | # | 種別 | 内容 | 影響度 |")
        lines.append("|----|----|------|------|--------|")
        for f in result.findings:
            lines.append(f"| {f.wi_id} | F-{f.index} | {f.finding_type} | {f.description} | {f.impact} |")
    else:
        lines.append("（該当なし）")
    lines.append("")

    lines.append(f"### 関連 Decisions ({len(result.decisions)}件)")
    if result.decisions:
        lines.append("| WI | # | 判断 | ステータス |")
        lines.append("|----|---|------|-----------|")
        for d in result.decisions:
            lines.append(f"| {d.wi_id} | D-{d.index} | {d.decision} | {d.status} |")
    else:
        lines.append("（該当なし）")
    lines.append("")

    lines.append("### 影響を受ける WI")
    if result.affected_wis:
        lines.append("| WI | Status | spec-impact | 影響内容 |")
        lines.append("|----|----|------------|---------|")
        for w in result.affected_wis:
            lines.append(f"| {w.wi_id} | {w.status} | {w.spec_impact} | {w.description} |")
    else:
        lines.append("（spec-impact:required/proposed の WI なし）")
    lines.append("")

    lines.append("### 関連 RISK / DEP")
    if result.related_issues:
        lines.append("| Issue | 種別 | タイトル | Status |")
        lines.append("|-------|------|---------|--------|")
        for r in result.related_issues:
            lines.append(f"| #{r['number']} | {r['type']} | {r['title']} | {r['state']} |")
    else:
        lines.append("（該当なし）")
    lines.append("")

    lines.append("### 💡 AI 推奨")
    if result.findings:
        lines.append(f"- {len(result.findings)}件の関連 Finding が検出されました。")
        high = [f for f in result.findings if f.impact == "high"]
        if high:
            lines.append(f"- うち {len(high)}件が高影響度です。Amendment の起案を推奨します。")
        else:
            lines.append("- 全て中〜低影響度です。次回 Sprint Planning での議論を推奨します。")
    else:
        lines.append("- 関連 Finding が見つかりません。追加調査を推奨します。")
    lines.append("")

    lines.append("### ⚠️ リスク・トレードオフ")
    if result.affected_wis:
        req = [w for w in result.affected_wis if w.spec_impact == "required"]
        if req:
            lines.append(f"- spec-impact:required の WI が {len(req)}件あり、仕様更新がブロッカーです。")
    lines.append("- Amendment 適用後、関連 WI のテスト再実行が必要な場合があります。")

    print("\n".join(lines))
    return 0


# =============================================================================
# Core: draft
# =============================================================================


def cmd_draft(args: argparse.Namespace) -> int:
    feature_id = args.feature
    title = args.title
    scope = args.scope or ""
    spec_sections = args.spec_sections or ""
    findings_refs = args.findings or ""
    decisions_refs = args.decisions or ""

    amd_id = _next_amd_id(feature_id)

    is_fast = getattr(args, 'fast', False)

    lines = []
    if is_fast:
        lines.append("> ⚡ **Fast Track Amendment** — analyze ステップ省略。TECH_LEAD 承認のみ。\n")
    lines += [
        f"## 📜 Amendment: {title}\n",
        f"**AMD ID:** {amd_id}",
        f"**Feature:** {feature_id}",
        f"**起案元:** Findings/Decisions 参照",
        f"**スコープ:** {scope}\n",
        "---\n",
        "### 変更概要",
        f"{title}\n",
        "### 変更理由",
        f"以下の Findings/Decisions に基づき仕様改訂が必要。\n",
        "### 根拠となる Findings",
    ]

    if findings_refs:
        for ref in findings_refs.split(","):
            ref = ref.strip()
            lines.append(f"- [ ] {ref}: (詳細を記入)")
    else:
        lines.append("- [ ] (Findings 参照を記入)")
    lines.append("")

    lines.append("### 根拠となる Decisions")
    if decisions_refs:
        for ref in decisions_refs.split(","):
            ref = ref.strip()
            lines.append(f"- [ ] {ref}: (詳細を記入)")
    else:
        lines.append("- [ ] (Decisions 参照を記入)")
    lines.append("")

    lines.append("### 変更内容（Spec Diff 案）")
    lines.append("| ファイル | セクション | 変更種別 | 変更内容 |")
    lines.append("|---------|----------|---------|---------|")
    if spec_sections:
        for sec in spec_sections.split(","):
            sec = sec.strip()
            lines.append(f"| spec.md | {sec} | 更新 | (変更内容を記入) |")
    else:
        lines.append("| spec.md | (セクション) | 更新 | (変更内容を記入) |")
    lines.append("")

    lines.append("### 影響を受けるWI")
    lines.append("- [ ] (WI-ID): (影響内容)")
    lines.append("")

    if scope:
        lines.append("### スコープ外（Phase 2）")
        lines.append(f"{scope}")
        lines.append("")

    lines.append("### 承認")
    if is_fast:
        lines.append("- [ ] Tech Lead承認")
    else:
        lines.append("- [ ] PM承認")
        lines.append("- [ ] Tech Lead承認（アーキテクチャ影響がある場合）")
    lines.append("")
    lines.append("---")
    lines.append(f"> 🤖 Generated by amendment_generator.py (SDD v4.5)")

    print("\n".join(lines))
    return 0


# =============================================================================
# Core: create
# =============================================================================


def cmd_create(args: argparse.Namespace) -> int:
    feature_id = args.feature
    draft_path = Path(args.draft)

    if not draft_path.exists():
        print(f"ERROR: Draft file not found: {draft_path}", file=sys.stderr)
        return 1

    body = _read_text(draft_path)
    if not body.strip():
        print("ERROR: Draft file is empty", file=sys.stderr)
        return 1

    # Extract title from draft
    title_match = re.search(r'## 📜 Amendment:\s*(.*)', body)
    amd_id_match = re.search(r'\*\*AMD ID:\*\*\s*(AMD-[A-Z0-9-]+)', body)

    title = title_match.group(1).strip() if title_match else "Amendment"
    amd_id = amd_id_match.group(1) if amd_id_match else ""

    issue_title = f"[AMD] {amd_id}: {title}" if amd_id else f"[AMD] {title}"

    # Create issue
    rc, out, err = _run_gh(
        "issue", "create",
        "--title", issue_title,
        "--label", "amendment,amendment:draft",
        "--body", body,
    )
    if rc != 0:
        print(f"ERROR: Failed to create issue: {err}", file=sys.stderr)
        return 1

    issue_url = out
    print(f"Amendment Issue created: {issue_url}")

    # Extract issue number from URL
    issue_num_match = re.search(r'/issues/(\d+)', issue_url)
    if not issue_num_match:
        return 0
    issue_num = issue_num_match.group(1)

    # Add to project
    _run_gh("project", "item-add", "2", "--owner", _get_repo_name().split("/")[0], "--url", issue_url)

    # Post cross-reference comments to affected WI issues
    affected_wis = _detect_affected_wis(feature_id)
    for wi in affected_wis:
        if wi.issue_number > 0:
            comment = f"📜 **Amendment 起案**: {issue_title} (#{issue_num})\n\nこの WI の spec-impact に関連する仕様改訂が起案されました。"
            _run_gh("issue", "comment", str(wi.issue_number), "--body", comment)
            print(f"Cross-reference posted to #{wi.issue_number}")

    return 0


# =============================================================================
# Core: apply (Phase 1 — Spec patch + PR creation)
# =============================================================================


def parse_spec_diffs(body: str) -> List[SpecDiff]:
    """Amendment body の Spec Diff テーブルを解析する。

    期待するテーブル形式:
    | ファイル | セクション | 変更種別 | 変更内容 |
    |---------|----------|---------|---------|
    | spec.md | AC-SF-002 | 更新 | currency_code フィールドを追加 |
    """
    diffs: List[SpecDiff] = []
    section = re.search(
        r'### 変更内容[^\n]*\n(.*?)(?=\n### |\Z)',
        body, re.DOTALL,
    )
    if not section:
        return diffs

    for line in section.group(1).strip().split('\n'):
        line = line.strip()
        if not line.startswith('|') or '---' in line:
            continue
        cols = [c.strip() for c in line.split('|')[1:-1]]
        if len(cols) >= 4 and cols[0] not in ('ファイル', ''):
            diffs.append(SpecDiff(
                file_path=cols[0],
                section=cols[1],
                change_type=cols[2],
                description=cols[3],
            ))
    return diffs


def parse_new_wi_candidates(body: str) -> List[NewWICandidate]:
    """Amendment body の「影響を受けるWI」セクションを解析する。

    期待する形式:
    - [ ] WI-SF-002: 通貨コードフィールドの追加実装
    - [ ] (新規): コンフリクト解決ロジックのハッシュ比較対応
    """
    candidates: List[NewWICandidate] = []
    section = re.search(
        r'### 影響を受けるWI[^\n]*\n(.*?)(?=\n### |\n---|\Z)',
        body, re.DOTALL,
    )
    if not section:
        return candidates

    for line in section.group(1).strip().split('\n'):
        m = re.match(r'- \[[ x]\]\s*(WI-[A-Z0-9-]+)?:?\s*(.*)', line)
        if m:
            candidates.append(NewWICandidate(
                wi_id=m.group(1) or "",
                description=m.group(2).strip(),
            ))
    return candidates


def apply_spec_patch(
    feature_dir: Path,
    diff: SpecDiff,
    amd_id: str,
) -> bool:
    """Spec ファイルの指定セクションに Amendment 変更マーカーを挿入する。

    完全な自動書き換えは危険なので、以下の戦略を取る:
    1. 対象セクションを特定（section ID で検索）
    2. セクション末尾に Amendment 変更ブロックを挿入
    3. PMが内容を確認・編集してからマージする（PR レビュー）

    挿入形式:
    <!-- AMD: {amd_id} -->
    > **Amendment {amd_id}** ({change_type})
    > {description}
    <!-- /AMD: {amd_id} -->
    """
    spec_path = feature_dir / diff.file_path
    if not spec_path.exists():
        print(f"  WARN: File not found: {spec_path}")
        return False

    content = spec_path.read_text(encoding="utf-8")

    pattern = re.compile(
        rf'(#{{1,4}}\s+[^\n]*{re.escape(diff.section)}[^\n]*\n)(.*?)(?=\n#{{1,4}}\s|\Z)',
        re.DOTALL,
    )
    match = pattern.search(content)

    amendment_block = (
        f"\n<!-- AMD: {amd_id} -->\n"
        f"> **Amendment {amd_id}** ({diff.change_type})\n"
        f"> {diff.description}\n"
        f"<!-- /AMD: {amd_id} -->\n"
    )

    if match:
        insert_pos = match.end()
        new_content = content[:insert_pos] + amendment_block + content[insert_pos:]
    else:
        print(f"  WARN: Section '{diff.section}' not found in {diff.file_path}, appending to end")
        new_content = content.rstrip() + "\n" + amendment_block

    spec_path.write_text(new_content, encoding="utf-8")
    return True


def create_amendment_pr(
    amd_id: str,
    feature_id: str,
    issue_num: int,
    spec_diffs: List[SpecDiff],
    dry_run: bool = False,
) -> Optional[str]:
    """Amendment 用のブランチを作成し、Spec 変更を commit -> PR を作成する。

    Returns:
        PR URL (or None if failed/dry-run)
    """
    branch_name = f"amendment/{amd_id.lower()}"

    if dry_run:
        print(f"  [DRY RUN] Would create branch: {branch_name}")
        print(f"  [DRY RUN] Would create PR for {len(spec_diffs)} spec changes")
        return None

    # Create branch
    rc, _, err = _run_cmd("git", "checkout", "-b", branch_name)
    if rc != 0:
        _run_cmd("git", "checkout", branch_name)

    # Stage + commit
    _run_cmd("git", "add", "-A")
    commit_msg = (
        f"{amd_id}: Spec amendment for {feature_id}\n\n"
        f"Amendment Issue: #{issue_num}\n\n"
        f"Changes:\n"
        + "\n".join(f"- {d.file_path} ({d.section}): {d.description}" for d in spec_diffs)
    )
    rc, _, err = _run_cmd("git", "commit", "-m", commit_msg)
    if rc != 0:
        print(f"  WARN: git commit failed: {err}")

    # Push
    _run_cmd("git", "push", "-u", "origin", branch_name)

    # Create PR
    pr_body = (
        f"## Amendment: {amd_id}\n\n"
        f"**Feature:** {feature_id}\n"
        f"**Amendment Issue:** #{issue_num}\n\n"
        f"### Spec 変更内容\n\n"
        f"| ファイル | セクション | 変更種別 | 変更内容 |\n"
        f"|---------|----------|---------|---------|"
    )
    for d in spec_diffs:
        pr_body += f"\n| {d.file_path} | {d.section} | {d.change_type} | {d.description} |"

    pr_body += (
        f"\n\n---\n"
        f"> **PMレビュー必須**: Amendment マーカー (`<!-- AMD: ... -->`) 内の記述を"
        f" 正式な仕様文言に書き換えてからマージしてください。\n"
        f"> マージ後に `amendment_generator.py finalize --issue {issue_num}` を実行すると"
        f" ラベル更新 + 新WI起票が自動で行われます。"
    )

    rc, pr_url, err = _run_gh(
        "pr", "create",
        "--title", f"{amd_id}: Spec amendment for {feature_id}",
        "--body", pr_body,
        "--label", "amendment",
        "--head", branch_name,
    )

    if rc != 0:
        print(f"  ERROR: PR creation failed: {err}", file=sys.stderr)
        return None

    print(f"  PR created: {pr_url}")

    # Return to main branch
    _run_cmd("git", "checkout", "main")

    return pr_url


def check_amendment_approval(body: str) -> tuple[bool, str]:
    """Check if amendment body has required approval.

    Returns:
        (approved: bool, error_message: str)
        If approved is True, error_message is empty.
    """
    is_fast_track = bool(re.search(r'Fast Track Amendment', body))

    if is_fast_track:
        tl_approved = bool(re.search(r'- \[x\]\s*Tech Lead承認', body, re.IGNORECASE))
        if not tl_approved:
            return False, "Tech Lead承認が未完了です（Fast Track）。"
        return True, ""
    else:
        pm_approved = bool(re.search(r'- \[x\]\s*PM承認', body, re.IGNORECASE))
        if not pm_approved:
            return False, "PM承認が未完了です。"
        return True, ""


def cmd_apply(args: argparse.Namespace) -> int:
    """Phase 1: PM承認確認 → Spec反映 + PR作成 → amendment:applying"""
    issue_num = args.issue
    dry_run = getattr(args, 'dry_run', False)

    body = _get_issue_body(issue_num)
    if not body:
        print(f"ERROR: Cannot read issue #{issue_num}", file=sys.stderr)
        return 1

    # Approval check (supports fast-track and normal paths)
    approved, err_msg = check_amendment_approval(body)
    if not approved:
        print(f"ERROR: {err_msg} Issue #{issue_num} のチェックボックスを確認してください。",
              file=sys.stderr)
        return 1

    # Extract AMD ID / Feature ID
    amd_id_match = re.search(r'\*\*AMD ID:\*\*\s*(AMD-[A-Z0-9-]+)', body)
    amd_id = amd_id_match.group(1) if amd_id_match else f"AMD-#{issue_num}"
    feature_match = re.search(r'\*\*Feature:\*\*\s*(FEAT-[A-Z0-9-]+)', body)
    feature_id = feature_match.group(1) if feature_match else ""

    print(f"Applying amendment {amd_id}...")

    # Parse Spec Diffs
    spec_diffs = parse_spec_diffs(body)
    if not spec_diffs:
        print("  WARN: No spec diffs found in Amendment body. Skipping spec patch.")
    else:
        print(f"  Found {len(spec_diffs)} spec change(s)")

    # Resolve feature directory
    project_root = _find_project_root(Path.cwd())
    feature_dir = _resolve_feature_dir(project_root, feature_id) if feature_id else None

    # Phase 1: Apply spec patches
    if spec_diffs and feature_dir:
        for diff in spec_diffs:
            ok = apply_spec_patch(feature_dir, diff, amd_id)
            status = "OK" if ok else "SKIP"
            print(f"  {status} {diff.file_path} ({diff.section}): {diff.description}")

    # Phase 1: Create PR
    pr_url = create_amendment_pr(
        amd_id, feature_id, issue_num, spec_diffs, dry_run=dry_run,
    )

    # Labels → amendment:applying
    if not dry_run:
        labels = _get_issue_labels(issue_num)
        remove_labels = [l for l in labels if l in ("amendment:draft", "amendment:review")]
        for rl in remove_labels:
            _run_gh("issue", "edit", str(issue_num), "--remove-label", rl)
        _run_gh("issue", "edit", str(issue_num), "--add-label", "amendment:applying")
        print(f"  Labels updated: → amendment:applying")

        # Post PR link as comment
        if pr_url:
            _run_gh("issue", "comment", str(issue_num),
                    "--body", f"Spec 反映 PR: {pr_url}\n\nPR をレビュー・マージ後に "
                              f"`amendment_generator.py finalize --issue {issue_num}` を実行してください。")

    print(f"\nNext step: PR をレビュー・マージ後に以下を実行:")
    print(f"   python3 sdd-templates/tools/amendment_generator.py finalize --issue {issue_num}")
    return 0


# =============================================================================
# Core: finalize (Phase 2 — WI creation + completion)
# =============================================================================


def create_derived_wi_issues(
    amd_id: str,
    feature_id: str,
    issue_num: int,
    candidates: List[NewWICandidate],
    dry_run: bool = False,
) -> List[str]:
    """Amendment から派生する新 WI Issue を作成する。

    Returns:
        作成した Issue URL のリスト
    """
    created_urls: List[str] = []

    for cand in candidates:
        if cand.wi_id:
            # Existing WI reference — add comment only
            issues = _search_issues_by_label("work-item")
            target_issue = None
            for iss in issues:
                if cand.wi_id in iss.get("title", ""):
                    target_issue = iss
                    break
            if target_issue and not dry_run:
                comment = (
                    f"**Amendment {amd_id}** により仕様が改訂されました。\n\n"
                    f"**対応内容:** {cand.description}\n"
                    f"**Amendment Issue:** #{issue_num}\n\n"
                    f"この WI の実装を改訂仕様に基づいて更新してください。"
                )
                _run_gh("issue", "comment", str(target_issue["number"]), "--body", comment)
                if target_issue.get("state") == "CLOSED":
                    _run_gh("issue", "reopen", str(target_issue["number"]))
                print(f"  Existing WI updated: {cand.wi_id} (#{target_issue['number']})")
                created_urls.append(f"#{target_issue['number']}")
            elif dry_run:
                print(f"  [DRY RUN] Would update existing WI: {cand.wi_id}")
        else:
            # New WI — create Issue
            short = feature_id.replace("FEAT-", "")
            prefix_parts = short.split("-")
            wi_prefix = prefix_parts[0] if prefix_parts else "NEW"

            # Get max existing WI number
            issues = _search_issues_by_label("work-item")
            existing_nums: List[int] = []
            pat = re.compile(rf'WI-{re.escape(wi_prefix)}-(\d+)')
            for iss in issues:
                m = pat.search(iss.get("title", ""))
                if m:
                    existing_nums.append(int(m.group(1)))
            next_num = max(existing_nums, default=0) + 1
            new_wi_id = f"WI-{wi_prefix}-{next_num:03d}"

            title = f"[WI] {new_wi_id}: {cand.description}"
            body = (
                f"# {new_wi_id}: {cand.description}\n\n"
                f"**起源:** Amendment {amd_id} (#{issue_num})\n"
                f"**Feature:** {feature_id}\n\n"
                f"---\n\n"
                f"## Intent\n"
                f"Amendment {amd_id} による仕様改訂に基づく追加実装。\n\n"
                f"## Scope\n"
                f"{cand.description}\n\n"
                f"## References\n"
                f"- Amendment: #{issue_num}\n"
                f"- Feature: {feature_id}\n\n"
                f"---\n"
                f"> Auto-generated by amendment_generator.py finalize"
            )

            if dry_run:
                print(f"  [DRY RUN] Would create WI: {title}")
                continue

            rc, url, err = _run_gh(
                "issue", "create",
                "--title", title,
                "--label", "work-item,amendment-derived",
                "--body", body,
            )
            if rc == 0:
                print(f"  New WI created: {new_wi_id} -> {url}")
                created_urls.append(url)
            else:
                print(f"  ERROR: Failed to create WI: {err}", file=sys.stderr)

    return created_urls


def cmd_finalize(args: argparse.Namespace) -> int:
    """Phase 2: ラベル更新 + spec-impact解消 + 新WI起票 + close"""
    issue_num = args.issue
    dry_run = getattr(args, 'dry_run', False)

    body = _get_issue_body(issue_num)
    if not body:
        print(f"ERROR: Cannot read issue #{issue_num}", file=sys.stderr)
        return 1

    # Check applying label
    labels = _get_issue_labels(issue_num)
    if "amendment:applying" not in labels:
        print(f"WARN: Issue #{issue_num} は amendment:applying ではありません。")
        print(f"  現在のラベル: {labels}")
        print(f"  先に `apply --issue {issue_num}` を実行してください。")
        if not getattr(args, 'force', False):
            return 1
        print("  --force フラグにより続行します。")

    amd_id_match = re.search(r'\*\*AMD ID:\*\*\s*(AMD-[A-Z0-9-]+)', body)
    amd_id = amd_id_match.group(1) if amd_id_match else f"AMD-#{issue_num}"
    feature_match = re.search(r'\*\*Feature:\*\*\s*(FEAT-[A-Z0-9-]+)', body)
    feature_id = feature_match.group(1) if feature_match else ""

    print(f"Finalizing amendment {amd_id}...")

    # 1. Labels → amendment:applied
    if not dry_run:
        for old in ("amendment:draft", "amendment:review", "amendment:applying"):
            _run_gh("issue", "edit", str(issue_num), "--remove-label", old)
        _run_gh("issue", "edit", str(issue_num), "--add-label", "amendment:applied")
        print(f"  Labels -> amendment:applied")

    # 2. Resolve spec-impact
    if feature_id:
        affected_wis = _detect_affected_wis(feature_id)
        for wi in affected_wis:
            if wi.issue_number > 0 and not dry_run:
                for old_label in ("spec-impact:required", "spec-impact:proposed"):
                    _run_gh("issue", "edit", str(wi.issue_number), "--remove-label", old_label)
                _run_gh("issue", "edit", str(wi.issue_number), "--add-label", "spec-impact:none")
                comment = f"{amd_id} により仕様が更新されました。spec-impact を解消しました。"
                _run_gh("issue", "comment", str(wi.issue_number), "--body", comment)
                print(f"  WI #{wi.issue_number} ({wi.wi_id}): spec-impact -> none")

    # 3. Create derived WIs
    candidates = parse_new_wi_candidates(body)
    if candidates:
        print(f"\n  {len(candidates)} WI candidate(s) found")
        created = create_derived_wi_issues(
            amd_id, feature_id, issue_num, candidates, dry_run=dry_run,
        )
        print(f"  Created/Updated: {len(created)} WI(s)")
    else:
        print("  No WI candidates in Amendment body. Skipping WI creation.")

    # 4. Close Amendment Issue
    if not dry_run:
        close_comment = (
            f"**{amd_id} 完了**\n\n"
            f"- Spec 反映済み（PR マージ完了）\n"
            f"- spec-impact 解消済み\n"
        )
        if candidates:
            close_comment += f"- 派生 WI {len(candidates)}件 起票済み\n"
        _run_gh("issue", "close", str(issue_num), "--comment", close_comment)
        print(f"\n  Amendment Issue #{issue_num} closed.")

    return 0


# =============================================================================
# Core: auto-check
# =============================================================================


def cmd_auto_check(args: argparse.Namespace) -> int:
    feature_id = args.feature
    threshold = args.threshold
    do_create = args.create

    affected_wis = _detect_affected_wis(feature_id)
    required_wis = [w for w in affected_wis if w.spec_impact == "required"]

    print(f"Auto-check: {feature_id}")
    print(f"  spec-impact:required WIs: {len(required_wis)}")
    print(f"  Threshold: {threshold}")

    if len(required_wis) >= threshold:
        print(f"\n⚠️ 閾値超過: {len(required_wis)} >= {threshold}")
        print("Amendment ドラフトの作成を推奨します。\n")

        # Generate a basic draft
        wi_ids = ", ".join(w.wi_id for w in required_wis)
        lines = [
            f"## 📜 Amendment: {feature_id} 仕様改訂（自動検出）\n",
            f"**AMD ID:** {_next_amd_id(feature_id)}",
            f"**Feature:** {feature_id}",
            f"**起案元:** auto-check (threshold={threshold})",
            f"**スコープ:** spec-impact:required の解消\n",
            "---\n",
            "### 変更概要",
            f"以下の WI で spec-impact:required が蓄積しています: {wi_ids}\n",
            "### 変更理由",
            f"{len(required_wis)}件の WI が仕様変更を要求しています。\n",
            "### 根拠となる Findings",
        ]
        for w in required_wis:
            lines.append(f"- [ ] {w.wi_id}: {w.description} (#{w.issue_number})")
        lines.extend([
            "",
            "### 根拠となる Decisions",
            "- [ ] (自動検出 — PM が補完してください)",
            "",
            "### 変更内容（Spec Diff 案）",
            "| ファイル | セクション | 変更種別 | 変更内容 |",
            "|---------|----------|---------|---------|",
            "| spec.md | (要確認) | 更新 | (PM が記入) |",
            "",
            "### 影響を受けるWI",
        ])
        for w in required_wis:
            lines.append(f"- [ ] {w.wi_id}: spec-impact:required (#{w.issue_number})")
        lines.extend([
            "",
            "### 承認",
            "- [ ] PM承認",
            "- [ ] Tech Lead承認（アーキテクチャ影響がある場合）",
            "",
            "---",
            "> 🤖 Generated by amendment_generator.py auto-check (SDD v4.5)",
        ])
        draft_text = "\n".join(lines)
        print(draft_text)

        if do_create:
            # Write to temp file and create issue
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write(draft_text)
                tmp_path = f.name
            try:
                # Simulate create by calling gh directly
                title_match = re.search(r'## 📜 Amendment:\s*(.*)', draft_text)
                amd_match = re.search(r'\*\*AMD ID:\*\*\s*(AMD-[A-Z0-9-]+)', draft_text)
                title = title_match.group(1).strip() if title_match else "Auto-detected Amendment"
                amd_id = amd_match.group(1) if amd_match else ""
                issue_title = f"[AMD] {amd_id}: {title}" if amd_id else f"[AMD] {title}"

                rc, out, err = _run_gh(
                    "issue", "create",
                    "--title", issue_title,
                    "--label", "amendment,amendment:draft",
                    "--body", draft_text,
                )
                if rc == 0:
                    print(f"\nAmendment Issue created: {out}")
                else:
                    print(f"ERROR: Failed to create issue: {err}", file=sys.stderr)
            finally:
                os.unlink(tmp_path)
    else:
        print(f"\n✅ 閾値以下: {len(required_wis)} < {threshold}. Amendment 不要。")

    return 0


# =============================================================================
# Self-Tests
# =============================================================================


def run_tests() -> bool:
    """Run self-tests."""
    print("Running amendment_generator.py self-tests...\n")
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

    # Test 1: _collect_findings parsing
    print("Test 1: Findings collection")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        run_dir = tmp_path / "runs" / "WI-TEST-001" / "RUN-001" / ".planning"
        run_dir.mkdir(parents=True)
        (run_dir / "findings.md").write_text("""# Findings: WI-TEST-001

## Investigation 1: Token の問題

**Question**: 通貨変換は？

**Finding**: 通貨コード必要。仕様変更が必要。

**Decision**: 通貨フィールド追加。

## Investigation 2: API制限

**Question**: レートリミットは？

**Finding**: 100 req/min。

**Decision**: スロットリング追加。
""", encoding="utf-8")

        findings = _collect_findings(tmp_path, "通貨")
        check("finds topic match", len(findings) == 1, f"got {len(findings)}")
        if findings:
            check("finding wi_id", findings[0].wi_id == "WI-TEST-001")
            check("finding index", findings[0].index == 1)
            check("finding impact", findings[0].impact == "high", f"got {findings[0].impact}")

        all_findings = _collect_findings(tmp_path, "")
        check("empty topic matches all", len(all_findings) == 2, f"got {len(all_findings)}")

    # Test 2: _collect_decisions parsing
    print("\nTest 2: Decisions collection")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        run_dir = tmp_path / "runs" / "WI-TEST-002" / "RUN-001" / ".planning"
        run_dir.mkdir(parents=True)
        (run_dir / "plan.md").write_text("""# Plan

## Approach

1. 通貨コードフィールドを DB に追加
2. API エンドポイント作成
3. バリデーション追加

## Decisions

- **PKCE 採用**: セキュリティ強化
- **通貨変換**: DatedConversionRate を使用
""", encoding="utf-8")

        decisions = _collect_decisions(tmp_path, "通貨")
        check("decisions found", len(decisions) >= 2, f"got {len(decisions)}")
        check("approach match", any("通貨" in d.decision for d in decisions))
        check("explicit decision match", any("DatedConversionRate" in d.decision for d in decisions))

    # Test 3: Draft generation
    print("\nTest 3: Draft format")
    import io
    from contextlib import redirect_stdout
    captured = io.StringIO()

    class MockArgs:
        feature = "FEAT-TEST"
        title = "テスト改訂"
        scope = "テストスコープ"
        spec_sections = "AC-001,NFR-002"
        findings = "WI-001:F-1"
        decisions = "WI-001:D-1"

    with redirect_stdout(captured):
        cmd_draft(MockArgs())
    draft_output = captured.getvalue()

    check("draft has AMD ID", "AMD ID:" in draft_output)
    check("draft has feature", "FEAT-TEST" in draft_output)
    check("draft has title", "テスト改訂" in draft_output)
    check("draft has scope", "テストスコープ" in draft_output)
    check("draft has spec sections", "AC-001" in draft_output)
    check("draft has PM approval", "PM承認" in draft_output)
    check("draft has TL approval", "Tech Lead承認" in draft_output)
    check("draft has generator tag", "amendment_generator.py" in draft_output)

    # Test 4: Apply approval check
    print("\nTest 4: Approval validation")
    body_approved = "- [x] PM承認\n- [x] Tech Lead承認"
    body_not_approved = "- [ ] PM承認\n- [x] Tech Lead承認"

    pm_ok = bool(re.search(r'- \[x\]\s*PM承認', body_approved, re.IGNORECASE))
    pm_ng = bool(re.search(r'- \[x\]\s*PM承認', body_not_approved, re.IGNORECASE))
    check("approved body detected", pm_ok)
    check("unapproved body detected", not pm_ng)

    # Test 5: AMD ID generation pattern
    print("\nTest 5: AMD ID format")
    test_id = "AMD-SF-CONN-001"
    pattern = re.compile(r'^AMD-[A-Z0-9-]+-\d{3}$')
    check("amd id format", pattern.match(test_id))

    # Test 6: Auto-check threshold logic
    print("\nTest 6: Auto-check threshold")
    mock_wis = [
        AffectedWI(wi_id="WI-001", spec_impact="required"),
        AffectedWI(wi_id="WI-002", spec_impact="required"),
        AffectedWI(wi_id="WI-003", spec_impact="proposed"),
    ]
    required = [w for w in mock_wis if w.spec_impact == "required"]
    check("threshold 2 triggers", len(required) >= 2)
    check("threshold 3 no trigger", not (len(required) >= 3))
    check("proposed excluded", len(required) == 2, f"got {len(required)}")

    # Test 7: Feature dir resolution
    print("\nTest 7: Feature dir resolution")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        specs = tmp_path / "specs" / "FEAT-TEST"
        specs.mkdir(parents=True)
        resolved = _resolve_feature_dir(tmp_path, "FEAT-TEST")
        check("direct resolve", resolved is not None and resolved.name == "FEAT-TEST")
        none_result = _resolve_feature_dir(tmp_path, "FEAT-MISSING")
        check("missing returns None", none_result is None)

    # Test 8: Feature matching
    print("\nTest 8: Feature matching")
    check("direct match", _feature_matches_issue("FEAT-SF-CONN", "[WI] WI-SF-002: test", []))
    check("prefix match", _feature_matches_issue("FEAT-SF-CONN", "[WI] WI-SF-003: test", []))
    check("label match", _feature_matches_issue("FEAT-SF-CONN", "unrelated", ["FEAT-SF-CONN"]))
    check("no match", not _feature_matches_issue("FEAT-SF-CONN", "[WI] WI-ERP-001: test", []))
    check("ERP match", _feature_matches_issue("FEAT-ERP-OMS", "[WI] WI-ERP-001: test", []))

    # Test 9: Analysis output format
    print("\nTest 9: Analysis output format")
    check("analysis heading", "📊 Amendment Impact Analysis" in "## 📊 Amendment Impact Analysis")
    check("risk heading", "⚠️ リスク" in "### ⚠️ リスク・トレードオフ")

    # Test 10: parse_spec_diffs
    print("\nTest 10: Spec Diff parsing")
    test_body = """
### 変更概要
テスト

### 変更内容（Spec Diff 案）
| ファイル | セクション | 変更種別 | 変更内容 |
|---------|----------|---------|---------|
| spec.md | AC-SF-002 | 更新 | currency_code フィールドを追加 |
| plan.md | NFR-003 | 追加 | 多通貨対応は Phase 2 の明記 |

### 影響を受けるWI
"""
    diffs = parse_spec_diffs(test_body)
    check("2 spec diffs", len(diffs) == 2, f"got {len(diffs)}")
    if diffs:
        check("diff[0] file", diffs[0].file_path == "spec.md")
        check("diff[0] section", diffs[0].section == "AC-SF-002")
        check("diff[0] type", diffs[0].change_type == "更新")
        check("diff[1] file", diffs[1].file_path == "plan.md")

    # Test 11: parse_new_wi_candidates
    print("\nTest 11: WI candidate parsing")
    test_body2 = """
### 影響を受けるWI
- [ ] WI-SF-002: 通貨コードフィールドの追加実装
- [x] WI-SF-003: コンフリクト解決のハッシュ対応
- [ ] (新規): 多通貨変換レート同期ジョブ

### 承認
"""
    candidates = parse_new_wi_candidates(test_body2)
    check("3 candidates", len(candidates) == 3, f"got {len(candidates)}")
    if candidates:
        check("cand[0] wi_id", candidates[0].wi_id == "WI-SF-002")
        check("cand[0] desc", "通貨" in candidates[0].description)
        check("cand[2] new wi (no id)", candidates[2].wi_id == "")
        check("cand[2] desc", "多通貨" in candidates[2].description)

    # Test 12: apply_spec_patch (integration)
    print("\nTest 12: Spec patch application")
    with tempfile.TemporaryDirectory() as tmp:
        feat = Path(tmp)
        spec = feat / "spec.md"
        spec.write_text(
            "# Spec\n\n## AC-SF-001\nFirst section\n\n## AC-SF-002\nSecond section\n\n## AC-SF-003\nThird\n",
            encoding="utf-8",
        )
        diff = SpecDiff(file_path="spec.md", section="AC-SF-002", change_type="更新", description="テスト変更")
        ok = apply_spec_patch(feat, diff, "AMD-TEST-001")
        check("patch applied", ok)
        content = spec.read_text(encoding="utf-8")
        check("marker inserted", "AMD-TEST-001" in content)
        check("original preserved", "Second section" in content)
        check("other sections intact", "First section" in content and "Third" in content)
        amd_pos = content.index("AMD-TEST-001")
        sf003_pos = content.index("## AC-SF-003")
        check("marker before AC-SF-003", amd_pos < sf003_pos)

    # Test 13: apply_spec_patch — missing file
    print("\nTest 13: Spec patch missing file")
    with tempfile.TemporaryDirectory() as tmp:
        feat = Path(tmp)
        diff = SpecDiff(file_path="nonexistent.md", section="AC-001", change_type="更新", description="test")
        ok = apply_spec_patch(feat, diff, "AMD-MISS-001")
        check("missing file returns False", not ok)

    # Test 14: apply_spec_patch — missing section (appends to end)
    print("\nTest 14: Spec patch missing section")
    with tempfile.TemporaryDirectory() as tmp:
        feat = Path(tmp)
        spec = feat / "spec.md"
        spec.write_text("# Spec\n\n## AC-SF-001\nOnly section\n", encoding="utf-8")
        diff = SpecDiff(file_path="spec.md", section="AC-SF-999", change_type="追加", description="new")
        ok = apply_spec_patch(feat, diff, "AMD-APPEND-001")
        check("append returns True", ok)
        content = spec.read_text(encoding="utf-8")
        check("marker appended", "AMD-APPEND-001" in content)
        check("original intact", "Only section" in content)

    # Test 15: parse_spec_diffs — empty body
    print("\nTest 15: Spec Diff empty body")
    empty_diffs = parse_spec_diffs("no diff table here")
    check("empty body returns []", len(empty_diffs) == 0)

    # Test 16: parse_new_wi_candidates — empty body
    print("\nTest 16: WI candidates empty body")
    empty_cands = parse_new_wi_candidates("no candidates here")
    check("empty body returns []", len(empty_cands) == 0)

    # Test 17: --fast flag produces fast track marker in draft
    print("\nTest 17: Fast track draft output")
    import io
    from contextlib import redirect_stdout

    fast_args = argparse.Namespace(
        feature="FEAT-TEST-001", title="Fast Test", scope="",
        spec_sections="", findings="", decisions="", fast=True
    )
    buf = io.StringIO()
    with redirect_stdout(buf):
        cmd_draft(fast_args)
    fast_output = buf.getvalue()
    check("fast track marker present",
          "Fast Track Amendment" in fast_output,
          f"Expected 'Fast Track Amendment' in output")
    check("fast track has Tech Lead approval only",
          "- [ ] Tech Lead承認" in fast_output and "PM承認" not in fast_output,
          "Should have Tech Lead only, no PM")

    # Test 18: Normal draft has PM approval
    print("\nTest 18: Normal draft has PM approval")
    normal_args = argparse.Namespace(
        feature="FEAT-TEST-001", title="Normal Test", scope="",
        spec_sections="", findings="", decisions="", fast=False
    )
    buf2 = io.StringIO()
    with redirect_stdout(buf2):
        cmd_draft(normal_args)
    normal_output = buf2.getvalue()
    check("normal draft has PM approval",
          "PM承認" in normal_output,
          "Normal draft should have PM承認")

    # Test 19: check_amendment_approval() — fast track path
    print("\nTest 19: check_amendment_approval (fast track)")
    ft_approved_body = "> ⚡ **Fast Track Amendment**\n- [x] Tech Lead承認\n"
    ft_unapproved_body = "> ⚡ **Fast Track Amendment**\n- [ ] Tech Lead承認\n"
    ok, msg = check_amendment_approval(ft_approved_body)
    check("fast track approved → True", ok, f"Expected True, got msg={msg}")
    ok2, msg2 = check_amendment_approval(ft_unapproved_body)
    check("fast track unapproved → False", not ok2, "Expected False for unapproved")
    check("fast track error mentions Tech Lead", "Tech Lead" in msg2, f"Got: {msg2}")

    # Test 20: check_amendment_approval() — normal path
    print("\nTest 20: check_amendment_approval (normal)")
    normal_approved_body = "### 承認\n- [x] PM承認\n- [ ] Tech Lead承認\n"
    normal_unapproved_body = "### 承認\n- [ ] PM承認\n"
    ok3, msg3 = check_amendment_approval(normal_approved_body)
    check("normal approved → True", ok3, f"Expected True, got msg={msg3}")
    ok4, msg4 = check_amendment_approval(normal_unapproved_body)
    check("normal unapproved → False", not ok4, "Expected False for unapproved")
    check("normal error mentions PM", "PM" in msg4, f"Got: {msg4}")

    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    return passed == total


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Amendment Generator — STRIDE Spec Amendment Full Lifecycle (v5.0)",
        epilog=(
            "\nFull Lifecycle:\n"
            "  1. analyze  — Impact analysis\n"
            "  2. draft    — Generate amendment draft\n"
            "  3. create   — Create Amendment Issue\n"
            "  4. apply    — PM承認確認 -> Spec反映PR作成 (amendment:applying)\n"
            "  5. finalize — PRマージ後 -> ラベル更新 + spec-impact解消 + 新WI起票 + close\n"
            "  *  auto-check — spec-impact蓄積の自動検出\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--test", action="store_true", help="Run self-tests")

    subparsers = parser.add_subparsers(dest="command")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Impact analysis")
    p_analyze.add_argument("--feature", required=True, help="Feature ID (e.g. FEAT-SF-CONN)")
    p_analyze.add_argument("--topic", required=True, help="Topic keyword for filtering")

    # draft
    p_draft = subparsers.add_parser("draft", help="Generate amendment draft")
    p_draft.add_argument("--feature", required=True, help="Feature ID")
    p_draft.add_argument("--title", required=True, help="Amendment title")
    p_draft.add_argument("--scope", help="Scope description")
    p_draft.add_argument("--spec-sections", help="Comma-separated spec sections")
    p_draft.add_argument("--findings", help="Comma-separated findings refs (e.g. WI-001:F-1)")
    p_draft.add_argument("--decisions", help="Comma-separated decisions refs")
    p_draft.add_argument("--fast", action="store_true",
        help="Low-risk fast track: skip analyze step, TECH_LEAD approval only")

    # create
    p_create = subparsers.add_parser("create", help="Create Amendment Issue")
    p_create.add_argument("--feature", required=True, help="Feature ID")
    p_create.add_argument("--draft", required=True, help="Path to draft markdown file")

    # apply
    p_apply = subparsers.add_parser("apply", help="Apply approved amendment (Spec patch + PR)")
    p_apply.add_argument("--issue", required=True, type=int, help="Amendment issue number")
    p_apply.add_argument("--dry-run", action="store_true", help="Show changes without applying")

    # finalize
    p_finalize = subparsers.add_parser("finalize", help="Finalize amendment (after PR merge)")
    p_finalize.add_argument("--issue", required=True, type=int, help="Amendment issue number")
    p_finalize.add_argument("--dry-run", action="store_true", help="Show changes without applying")
    p_finalize.add_argument("--force", action="store_true", help="Force finalize even if not in applying state")

    # auto-check
    p_auto = subparsers.add_parser("auto-check", help="Auto-check spec-impact accumulation")
    p_auto.add_argument("--feature", required=True, help="Feature ID")
    p_auto.add_argument("--threshold", type=int, default=2, help="Threshold (default: 2)")
    p_auto.add_argument("--create", action="store_true", help="Auto-create Issue if threshold exceeded")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handlers = {
        "analyze": cmd_analyze,
        "draft": cmd_draft,
        "create": cmd_create,
        "apply": cmd_apply,
        "finalize": cmd_finalize,
        "auto-check": cmd_auto_check,
    }

    handler = handlers.get(args.command)
    if handler:
        sys.exit(handler(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
