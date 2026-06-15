#!/usr/bin/env python3
"""
Epic Progress Aggregator - Enterprise SDD Extension
Version: 1.0.0

Purpose:
- Aggregate progress metrics across all features in an Epic
- Compute gate completion matrix, team status, milestone progress
- Identify blockers and risk escalations
- Output as summary (terminal), JSON, or markdown (EPIC_DASHBOARD.md)

Usage:
    python3 epic_progress_aggregator.py <epic_dir> [--format summary|json|markdown] [--output <path>]
    python3 epic_progress_aggregator.py <epic_dir> --weekly-summary [--post --epic <N>] [--repo owner/repo]
    python3 epic_progress_aggregator.py --test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# Gate names matching APPROVAL.md structure (5 gates + Final)
FEATURE_GATES = ["Gate 1", "Gate 2", "Gate 3", "Gate 4", "Gate 5", "Final"]

# WI status values
WI_STATUSES = {"pending", "in_progress", "done"}

# Mode severity for risk escalation
MODE_ORDER = {"autopilot": 0, "confirm": 1, "validate": 2}

# Full ops pack files
FULL_OPS_PACK = [
    "transport_manifest.yaml",
    "release_checklist.md",
    "rollback_plan.md",
    "hypercare_runbook.md",
]


def _read_text(path: Path) -> str:
    """Read file as UTF-8 text."""
    return path.read_text(encoding="utf-8")


def _load_yaml_file(path: Path) -> Dict[str, Any]:
    """Load a YAML file safely."""
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(_read_text(path)) or {}
    except Exception:
        return {}


def _extract_yaml_from_md(md_path: Path) -> Optional[Dict[str, Any]]:
    """Extract first YAML block from markdown file."""
    if not md_path.exists():
        return None
    try:
        content = _read_text(md_path)
        match = re.search(r'```yaml\s*(.*?)```', content, re.DOTALL)
        if match:
            return yaml.safe_load(match.group(1))
        return None
    except Exception:
        return None


def _parse_front_matter(md_text: str) -> Dict[str, Any]:
    """Parse YAML front matter from markdown file."""
    if not md_text.startswith("---"):
        return {}
    parts = md_text.split("\n---", 2)
    if len(parts) < 2:
        return {}
    yml = parts[0].lstrip("-").strip()
    try:
        return yaml.safe_load(yml) or {}
    except Exception:
        return {}


def _parse_approval_gates(approval_path: Path) -> Dict[str, bool]:
    """Parse APPROVAL.md to determine which gates are passed.

    Returns dict mapping gate names to True/False.
    """
    result = {g: False for g in FEATURE_GATES}
    if not approval_path.exists():
        return result

    try:
        content = _read_text(approval_path)
    except Exception:
        return result

    # Split content by gate sections
    gate_sections = re.split(r'(?=## (?:Gate \d|Final))', content)

    for section in gate_sections:
        gate_name = None
        if re.match(r'## Gate 1\b', section):
            gate_name = "Gate 1"
        elif re.match(r'## Gate 2\b', section):
            gate_name = "Gate 2"
        elif re.match(r'## Gate 3\b', section):
            gate_name = "Gate 3"
        elif re.match(r'## Gate 4\b', section):
            gate_name = "Gate 4"
        elif re.match(r'## Gate 5\b', section):
            gate_name = "Gate 5"
        elif re.match(r'## Final\b', section):
            gate_name = "Final"

        if gate_name is None:
            continue

        # Gate is passed if it has at least one [x] checkbox AND a non-placeholder approver
        has_checked = bool(re.search(r'\[x\]', section, re.IGNORECASE))
        has_approver = bool(re.search(
            r'(?:\u627f\u8a8d\u8005|Approver):\s*([^\s_][^\n]*)',
            section, re.IGNORECASE,
        ))
        result[gate_name] = has_checked and has_approver

    return result


@dataclass
class FeatureProgress:
    """Progress data for a single feature."""
    feature_id: str
    name: str = ""
    team_id: str = ""
    coverage_tier: str = "standard"
    gates: Dict[str, bool] = field(default_factory=dict)
    wi_total: int = 0
    wi_done: int = 0
    wi_in_progress: int = 0
    wi_pending: int = 0
    risk_wis: List[str] = field(default_factory=list)  # WIs with validate mode or high-risk in_progress
    blockers: List[str] = field(default_factory=list)
    ops_pack_complete: bool = False
    wi_details: List["WorkItemCard"] = field(default_factory=list)
    autonomy_bias: str = "balanced"


@dataclass
class WorkItemCard:
    """Individual WI data for Kanban display."""
    wi_id: str
    title: str = ""
    status: str = "pending"
    mode: str = "autopilot"
    risk_flags: List[str] = field(default_factory=list)
    complexity: str = "low"
    feature_id: str = ""


@dataclass
class DependencyLink:
    """Cross-team dependency for graph display."""
    dep_id: str
    from_feature: str = ""
    to_feature: str = ""
    dep_type: str = "blocking"
    status: str = "pending"
    from_team: str = ""
    to_team: str = ""


@dataclass
class WeeklyRunData:
    """Data from a single run for weekly summary."""
    wi_id: str
    run_id: str
    feature_id: str = ""
    findings_count: int = 0
    decisions_count: int = 0
    spec_impact: str = "none"
    lessons: List[str] = field(default_factory=list)


@dataclass
class TeamStatus:
    """Aggregated team-level status."""
    team_id: str
    name: str = ""
    feature_count: int = 0
    gates_total: int = 0
    gates_passed: int = 0
    wi_total: int = 0
    wi_done: int = 0


@dataclass
class MilestoneProgress:
    """Progress for a single milestone."""
    milestone_id: str
    name: str = ""
    target_date: str = ""
    feature_ids: List[str] = field(default_factory=list)
    status: str = "on-track"  # on-track | at-risk | blocked


@dataclass
class EpicProgressReport:
    """Complete Epic progress report."""
    epic_id: str = "UNKNOWN"
    epic_title: str = ""
    features: List[FeatureProgress] = field(default_factory=list)
    teams: List[TeamStatus] = field(default_factory=list)
    milestones: List[MilestoneProgress] = field(default_factory=list)
    total_blockers: int = 0
    risk_escalations: List[str] = field(default_factory=list)
    dependencies: List[DependencyLink] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def _find_project_root(epic_dir: Path) -> Path:
    """Find project root by looking for memory/ or sdd-templates/ directory."""
    current = epic_dir.resolve()
    for _ in range(5):
        if (current / "memory").exists() or (current / "sdd-templates").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # Fallback: epics/<epic>/ -> 2 levels up
    return epic_dir.resolve().parent.parent


def aggregate_epic_progress(epic_dir: str | Path) -> EpicProgressReport:
    """Aggregate progress metrics across all features in an Epic.

    Args:
        epic_dir: Path to epics/<EPIC-ID>/ directory

    Returns:
        EpicProgressReport with all computed metrics
    """
    epic_path = Path(epic_dir).resolve()
    report = EpicProgressReport()

    if not epic_path.exists() or not epic_path.is_dir():
        report.errors.append(f"Epic directory not found: {epic_path}")
        return report

    project_root = _find_project_root(epic_path)
    specs_dir = project_root / "specs"

    # --- Parse epic_design.md ---
    epic_design_path = epic_path / "epic_design.md"
    epic_data = _extract_yaml_from_md(epic_design_path)
    if not epic_data or "epic" not in epic_data:
        report.errors.append(f"Cannot parse epic_design.md or missing 'epic' key in {epic_design_path}")
        return report

    epic = epic_data["epic"]
    meta = epic.get("meta", {})
    report.epic_id = meta.get("epic_id", "UNKNOWN")
    report.epic_title = meta.get("title", "")

    # Build team lookup
    team_map: Dict[str, str] = {}  # team_id -> name
    for team in epic.get("ownership", {}).get("teams", []):
        tid = team.get("team_id", "")
        team_map[tid] = team.get("name", tid)

    # Build feature list from epic_design
    feature_list = epic.get("features", [])
    feature_lookup: Dict[str, Dict[str, Any]] = {}
    for feat in feature_list:
        fid = feat.get("feature_id", "")
        if fid:
            feature_lookup[fid] = feat

    # --- Parse feature_breakdown.md for additional info ---
    breakdown_path = epic_path / "feature_breakdown.md"
    breakdown_data = _extract_yaml_from_md(breakdown_path)
    breakdown_features: Dict[str, Dict[str, Any]] = {}
    if breakdown_data and "feature_breakdown" in breakdown_data:
        for feat in breakdown_data["feature_breakdown"].get("features", []):
            fid = feat.get("feature_id", "")
            if fid:
                breakdown_features[fid] = feat

    # --- Process each feature ---
    team_accum: Dict[str, TeamStatus] = {}

    for fid, feat_info in feature_lookup.items():
        fp = FeatureProgress(
            feature_id=fid,
            name=feat_info.get("name", ""),
            team_id=feat_info.get("team_id", ""),
            coverage_tier=feat_info.get("coverage_tier", "standard"),
        )

        feature_spec_dir = specs_dir / fid

        # Try to read basic_design.md for team_id/coverage_tier overrides
        bd_path = feature_spec_dir / "basic_design.md"
        if bd_path.exists():
            bd_data = _extract_yaml_from_md(bd_path)
            if bd_data:
                # Navigate various possible structures
                for key in ("basic_design", "feature"):
                    if key in bd_data:
                        sub = bd_data[key]
                        if "team_id" in sub:
                            fp.team_id = sub["team_id"]
                        if "coverage_tier" in sub:
                            fp.coverage_tier = sub["coverage_tier"]
                        break

        # --- Parse APPROVAL.md for gate status ---
        approval_path = feature_spec_dir / "APPROVAL.md"
        fp.gates = _parse_approval_gates(approval_path)

        # --- Parse state/state.yaml for WI statuses ---
        state_path = feature_spec_dir / "state" / "state.yaml"
        state = _load_yaml_file(state_path)
        fp.autonomy_bias = state.get("autonomy_bias", "balanced")
        wi_statuses: Dict[str, str] = {}
        wi_modes: Dict[str, str] = {}
        for wi_entry in (state.get("work_items") or []):
            if isinstance(wi_entry, dict) and wi_entry.get("wi_id"):
                wi_id = wi_entry["wi_id"]
                status = wi_entry.get("status", "pending")
                wi_statuses[wi_id] = status
                wi_modes[wi_id] = wi_entry.get("mode", "autopilot")

        fp.wi_total = len(wi_statuses)
        fp.wi_done = sum(1 for s in wi_statuses.values() if s == "done")
        fp.wi_in_progress = sum(1 for s in wi_statuses.values() if s == "in_progress")
        fp.wi_pending = sum(1 for s in wi_statuses.values() if s == "pending")

        # --- Parse work_items/WI-*.md for risk_flags ---
        wi_dir = feature_spec_dir / "work_items"
        if wi_dir.exists():
            for wi_file in sorted(wi_dir.glob("WI-*.md")):
                if wi_file.name.endswith(".approval.md"):
                    continue
                try:
                    fm = _parse_front_matter(_read_text(wi_file))
                except Exception:
                    continue

                wi_id = fm.get("wi_id", "")
                mode = fm.get("mode", "autopilot")
                risk_flags = fm.get("risk_flags") or []
                complexity = fm.get("complexity", "low")
                title = fm.get("title", "")

                # Capture WI detail for Kanban display
                status = wi_statuses.get(wi_id, "pending")
                fp.wi_details.append(WorkItemCard(
                    wi_id=wi_id,
                    title=title,
                    status=status,
                    mode=wi_modes.get(wi_id, mode),
                    risk_flags=list(risk_flags),
                    complexity=complexity,
                    feature_id=fid,
                ))

                # Risk escalation: validate mode or high-risk flags while still in_progress
                if status == "in_progress":
                    is_high_risk = mode == "validate" or any(
                        f in risk_flags for f in (
                            "authz", "sod", "audit_log", "pii",
                            "accounting_calc", "inventory_valuation",
                            "db_schema", "data_migration",
                        )
                    )
                    if is_high_risk:
                        fp.risk_wis.append(wi_id)
                        report.risk_escalations.append(
                            f"{fid}/{wi_id}: mode={mode}, risk_flags={risk_flags}"
                        )

        # --- Ops readiness ---
        ops_dir = feature_spec_dir / "ops"
        if ops_dir.exists():
            missing_ops = [r for r in FULL_OPS_PACK if not (ops_dir / r).exists()]
            fp.ops_pack_complete = len(missing_ops) == 0
        else:
            fp.ops_pack_complete = False

        # --- Accumulate team stats ---
        tid = fp.team_id
        if tid not in team_accum:
            team_accum[tid] = TeamStatus(
                team_id=tid,
                name=team_map.get(tid, tid),
            )
        ts = team_accum[tid]
        ts.feature_count += 1
        ts.gates_total += len(FEATURE_GATES)
        ts.gates_passed += sum(1 for v in fp.gates.values() if v)
        ts.wi_total += fp.wi_total
        ts.wi_done += fp.wi_done

        report.features.append(fp)

    report.teams = list(team_accum.values())

    # --- Cross-team dependencies ---
    for dep in epic.get("cross_team_dependencies", []):
        report.dependencies.append(DependencyLink(
            dep_id=dep.get("dependency_id", ""),
            from_feature=dep.get("from_feature", ""),
            to_feature=dep.get("to_feature", ""),
            dep_type=dep.get("type", "blocking"),
            status=dep.get("status", "pending"),
            from_team=dep.get("from_team", ""),
            to_team=dep.get("to_team", ""),
        ))

    # --- Milestones ---
    for ms in epic.get("milestones", []):
        mp = MilestoneProgress(
            milestone_id=ms.get("id", ""),
            name=ms.get("name", ""),
            target_date=ms.get("target_date", ""),
            feature_ids=ms.get("features", []),
        )

        # Determine milestone status from constituent features
        has_blocked = False
        has_at_risk = False
        all_done = True

        for fid in mp.feature_ids:
            feat = next((f for f in report.features if f.feature_id == fid), None)
            if feat is None:
                has_at_risk = True
                all_done = False
                continue

            # If feature has no Final gate pass -> not done
            if not feat.gates.get("Final", False):
                all_done = False

            # If feature has risk WIs in progress -> at risk
            if feat.risk_wis:
                has_at_risk = True

            # If feature has zero gates passed and WIs pending -> blocked
            gates_passed = sum(1 for v in feat.gates.values() if v)
            if gates_passed == 0 and feat.wi_total > 0 and feat.wi_done == 0:
                has_blocked = True

        if has_blocked:
            mp.status = "blocked"
        elif has_at_risk or not all_done:
            if all_done:
                mp.status = "on-track"
            elif has_at_risk:
                mp.status = "at-risk"
            else:
                mp.status = "on-track"
        else:
            mp.status = "on-track"

        report.milestones.append(mp)

    # --- Total blockers ---
    report.total_blockers = sum(len(f.blockers) for f in report.features)

    return report


# ── Output Formatters ──────────────────────────────────────────────────


def _format_summary(report: EpicProgressReport) -> str:
    """Format report as compact terminal summary with box-drawing chars."""
    lines: List[str] = []
    w = 72

    lines.append("\u250c" + "\u2500" * (w - 2) + "\u2510")
    title = f" Epic Progress: {report.epic_id} "
    pad = w - 2 - len(title)
    lines.append("\u2502" + title + " " * max(pad, 0) + "\u2502")
    if report.epic_title:
        sub = f" {report.epic_title} "
        pad2 = w - 2 - len(sub)
        lines.append("\u2502" + sub + " " * max(pad2, 0) + "\u2502")
    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    # Errors
    if report.errors:
        for err in report.errors:
            lines.append(f"\u2502  ERROR: {err[:w - 12]}" + " " * max(0, w - 12 - len(err[:w - 12])) + "\u2502")
        lines.append("\u2514" + "\u2500" * (w - 2) + "\u2518")
        return "\n".join(lines)

    # Gate Completion Matrix
    lines.append("\u2502  Gate Completion Matrix" + " " * (w - 26) + "\u2502")
    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    header = "\u2502  Feature" + " " * 10
    for g in FEATURE_GATES:
        short = g.replace("Gate ", "G") if g != "Final" else "Fin"
        header += f" {short:>4}"
    pad_h = w - 1 - len(header)
    header += " " * max(pad_h, 0) + "\u2502"
    lines.append(header)

    for feat in report.features:
        row = f"\u2502  {feat.feature_id:<17}"
        for g in FEATURE_GATES:
            passed = feat.gates.get(g, False)
            mark = " \u2713" if passed else " \u00b7"
            row += f" {mark:>4}"
        pad_r = w - 1 - len(row)
        row += " " * max(pad_r, 0) + "\u2502"
        lines.append(row)

    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    # Team Status
    lines.append("\u2502  Team Status" + " " * (w - 16) + "\u2502")
    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    for team in report.teams:
        gate_pct = (team.gates_passed / team.gates_total * 100) if team.gates_total > 0 else 0
        wi_pct = (team.wi_done / team.wi_total * 100) if team.wi_total > 0 else 0
        row = (
            f"\u2502  {team.team_id:<10} "
            f"feat={team.feature_count}  "
            f"gate={gate_pct:5.1f}%  "
            f"WI={team.wi_done}/{team.wi_total} ({wi_pct:.0f}%)"
        )
        pad_r = w - 1 - len(row)
        row += " " * max(pad_r, 0) + "\u2502"
        lines.append(row)

    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    # Milestones
    lines.append("\u2502  Milestones" + " " * (w - 15) + "\u2502")
    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    for ms in report.milestones:
        indicator = {"on-track": "\u25cf", "at-risk": "\u25b2", "blocked": "\u2716"}.get(ms.status, "?")
        row = f"\u2502  {indicator} {ms.milestone_id} {ms.name:<28} [{ms.status}]"
        pad_r = w - 1 - len(row)
        row += " " * max(pad_r, 0) + "\u2502"
        lines.append(row)

    lines.append("\u251c" + "\u2500" * (w - 2) + "\u2524")

    # Risk Escalations
    esc_count = len(report.risk_escalations)
    lines.append(f"\u2502  Risk Escalations: {esc_count}" + " " * (w - 23 - len(str(esc_count))) + "\u2502")
    for esc in report.risk_escalations[:5]:
        row = f"\u2502    {esc[:w - 8]}"
        pad_r = w - 1 - len(row)
        row += " " * max(pad_r, 0) + "\u2502"
        lines.append(row)
    if esc_count > 5:
        row = f"\u2502    ... and {esc_count - 5} more"
        pad_r = w - 1 - len(row)
        row += " " * max(pad_r, 0) + "\u2502"
        lines.append(row)

    lines.append("\u2514" + "\u2500" * (w - 2) + "\u2518")
    return "\n".join(lines)


def _format_json(report: EpicProgressReport) -> str:
    """Format report as structured JSON."""
    data = {
        "epic_id": report.epic_id,
        "epic_title": report.epic_title,
        "generated_at": date.today().isoformat(),
        "features": [],
        "teams": [],
        "milestones": [],
        "total_blockers": report.total_blockers,
        "risk_escalations": report.risk_escalations,
        "errors": report.errors,
    }

    for feat in report.features:
        data["features"].append({
            "feature_id": feat.feature_id,
            "name": feat.name,
            "team_id": feat.team_id,
            "coverage_tier": feat.coverage_tier,
            "gates": feat.gates,
            "work_items": {
                "total": feat.wi_total,
                "done": feat.wi_done,
                "in_progress": feat.wi_in_progress,
                "pending": feat.wi_pending,
            },
            "risk_wis": feat.risk_wis,
            "ops_pack_complete": feat.ops_pack_complete,
        })

    for team in report.teams:
        gate_pct = (team.gates_passed / team.gates_total * 100) if team.gates_total > 0 else 0
        wi_pct = (team.wi_done / team.wi_total * 100) if team.wi_total > 0 else 0
        data["teams"].append({
            "team_id": team.team_id,
            "name": team.name,
            "feature_count": team.feature_count,
            "gate_pass_pct": round(gate_pct, 1),
            "wi_total": team.wi_total,
            "wi_done": team.wi_done,
            "wi_completion_pct": round(wi_pct, 1),
        })

    for ms in report.milestones:
        data["milestones"].append({
            "milestone_id": ms.milestone_id,
            "name": ms.name,
            "target_date": ms.target_date,
            "feature_ids": ms.feature_ids,
            "status": ms.status,
        })

    return json.dumps(data, indent=2, ensure_ascii=False)


def _format_markdown(report: EpicProgressReport) -> str:
    """Format report as EPIC_DASHBOARD.md content."""
    lines: List[str] = []

    lines.append(f"# Epic Dashboard: {report.epic_id}")
    lines.append("")
    lines.append(f"> **Title**: {report.epic_title}")
    lines.append(f"> **Generated**: {date.today().isoformat()}")
    lines.append("")

    if report.errors:
        lines.append("## Errors")
        lines.append("")
        for err in report.errors:
            lines.append(f"- {err}")
        lines.append("")
        return "\n".join(lines)

    # Gate Completion Matrix
    lines.append("## Gate Completion Matrix")
    lines.append("")
    header = "| Feature | " + " | ".join(
        g.replace("Gate ", "G") if g != "Final" else "Final" for g in FEATURE_GATES
    ) + " |"
    sep = "|---------|" + "|".join("-----" for _ in FEATURE_GATES) + "|"
    lines.append(header)
    lines.append(sep)

    for feat in report.features:
        cells = []
        for g in FEATURE_GATES:
            passed = feat.gates.get(g, False)
            cells.append(" [x] " if passed else " [ ] ")
        lines.append(f"| {feat.feature_id} |{'|'.join(cells)}|")
    lines.append("")

    # Team Status
    lines.append("## Team Status")
    lines.append("")
    lines.append("| Team | Features | Gate Pass % | WI Done | WI Total | WI % |")
    lines.append("|------|----------|-------------|---------|----------|------|")
    for team in report.teams:
        gate_pct = (team.gates_passed / team.gates_total * 100) if team.gates_total > 0 else 0
        wi_pct = (team.wi_done / team.wi_total * 100) if team.wi_total > 0 else 0
        lines.append(
            f"| {team.team_id} | {team.feature_count} | {gate_pct:.1f}% "
            f"| {team.wi_done} | {team.wi_total} | {wi_pct:.0f}% |"
        )
    lines.append("")

    # Milestones
    lines.append("## Milestone Progress")
    lines.append("")
    lines.append("| Milestone | Name | Target | Features | Status |")
    lines.append("|-----------|------|--------|----------|--------|")
    for ms in report.milestones:
        feat_str = ", ".join(ms.feature_ids)
        status_icon = {"on-track": "on-track", "at-risk": "AT-RISK", "blocked": "BLOCKED"}.get(ms.status, ms.status)
        lines.append(f"| {ms.milestone_id} | {ms.name} | {ms.target_date} | {feat_str} | {status_icon} |")
    lines.append("")

    # Feature Details
    lines.append("## Feature Details")
    lines.append("")
    for feat in report.features:
        gates_passed = sum(1 for v in feat.gates.values() if v)
        wi_pct = (feat.wi_done / feat.wi_total * 100) if feat.wi_total > 0 else 0
        lines.append(f"### {feat.feature_id}: {feat.name}")
        lines.append("")
        lines.append(f"- **Team**: {feat.team_id}")
        lines.append(f"- **Tier**: {feat.coverage_tier}")
        lines.append(f"- **Gates Passed**: {gates_passed}/{len(FEATURE_GATES)}")
        lines.append(f"- **Work Items**: {feat.wi_done}/{feat.wi_total} done ({wi_pct:.0f}%)")
        lines.append(f"- **Ops Pack**: {'Complete' if feat.ops_pack_complete else 'Incomplete'}")
        if feat.risk_wis:
            lines.append(f"- **Risk WIs**: {', '.join(feat.risk_wis)}")
        lines.append("")

    # Risk Escalations
    if report.risk_escalations:
        lines.append("## Risk Escalations")
        lines.append("")
        for esc in report.risk_escalations:
            lines.append(f"- {esc}")
        lines.append("")

    # Summary
    total_features = len(report.features)
    total_gates = total_features * len(FEATURE_GATES)
    total_gates_passed = sum(
        sum(1 for v in f.gates.values() if v) for f in report.features
    )
    total_wi = sum(f.wi_total for f in report.features)
    total_wi_done = sum(f.wi_done for f in report.features)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Features**: {total_features}")
    lines.append(f"- **Overall Gate Progress**: {total_gates_passed}/{total_gates}")
    lines.append(f"- **Overall WI Progress**: {total_wi_done}/{total_wi}")
    lines.append(f"- **Risk Escalations**: {len(report.risk_escalations)}")
    lines.append(f"- **Blockers**: {report.total_blockers}")
    lines.append("")

    return "\n".join(lines)


def _format_html(report: EpicProgressReport) -> str:
    """Format report as self-contained HTML dashboard."""
    from html import escape as _esc

    today = date.today().isoformat()

    # ── Compute aggregate metrics ─────────────────────────────────────
    total_features = len(report.features)
    total_gates = total_features * len(FEATURE_GATES)
    total_gates_passed = sum(
        sum(1 for v in f.gates.values() if v) for f in report.features
    )
    total_wi = sum(f.wi_total for f in report.features)
    total_wi_done = sum(f.wi_done for f in report.features)
    total_wi_ip = sum(f.wi_in_progress for f in report.features)
    gate_pct = (total_gates_passed / total_gates * 100) if total_gates else 0
    wi_pct = (total_wi_done / total_wi * 100) if total_wi else 0
    risk_count = len(report.risk_escalations)

    if risk_count >= 3 or gate_pct < 30:
        health_cls, health_lbl = "red", "AT RISK"
    elif risk_count >= 1 or gate_pct < 60:
        health_cls, health_lbl = "yellow", "CAUTION"
    else:
        health_cls, health_lbl = "green", "ON TRACK"

    # ── Build WI Kanban cards ─────────────────────────────────────────
    all_wis: List[WorkItemCard] = []
    for feat in report.features:
        all_wis.extend(feat.wi_details)

    def _wi_card(wi: WorkItemCard) -> str:
        mc = {"validate": "mode-validate", "confirm": "mode-confirm"}.get(
            wi.mode, "mode-autopilot"
        )
        rc = len(wi.risk_flags)
        risk = f'<span class="rc">{rc} risk{"s" if rc != 1 else ""}</span>' if rc else ""
        title = _esc(wi.title[:42]) if wi.title else ""
        bias_feat = next(
            (f for f in report.features if f.feature_id == wi.feature_id), None
        )
        bias_icon = {"autonomous": "\u26a1", "controlled": "\U0001f6e1\ufe0f"}.get(
            bias_feat.autonomy_bias if bias_feat else "", ""
        )
        return (
            f'<div class="wc {mc}" data-f="{_esc(wi.feature_id)}">'
            f'<div class="wc-h"><span class="wid">{_esc(wi.wi_id)}</span>'
            f'<span class="mb {mc}">{_esc(wi.mode)}</span></div>'
            f'<div class="wc-t">{title}</div>'
            f'<div class="wc-f"><span class="ft">{_esc(wi.feature_id)}'
            f'{bias_icon}</span>{risk}</div></div>'
        )

    pending_cards = "\n".join(_wi_card(w) for w in all_wis if w.status == "pending")
    ip_cards = "\n".join(_wi_card(w) for w in all_wis if w.status == "in_progress")
    done_cards = "\n".join(_wi_card(w) for w in all_wis if w.status == "done")
    cnt_p = sum(1 for w in all_wis if w.status == "pending")
    cnt_i = sum(1 for w in all_wis if w.status == "in_progress")
    cnt_d = sum(1 for w in all_wis if w.status == "done")

    feat_opts = '<option value="all">All Features</option>'
    for f in report.features:
        feat_opts += (
            f'<option value="{_esc(f.feature_id)}">'
            f'{_esc(f.feature_id)}: {_esc(f.name)}</option>'
        )

    # ── Gate Pipeline rows ────────────────────────────────────────────
    gate_rows = ""
    for feat in report.features:
        tier_cls = {
            "critical": "t-crit", "standard": "t-std", "experimental": "t-exp",
        }.get(feat.coverage_tier, "t-std")
        steps = ""
        found_current = False
        for g in FEATURE_GATES:
            short = g.replace("Gate ", "G") if g != "Final" else "Fin"
            if feat.gates.get(g, False):
                cls = "st done"
            elif not found_current:
                cls = "st cur"
                found_current = True
            else:
                cls = "st"
            steps += f'<div class="{cls}"><span>{short}</span></div>'
        gp = sum(1 for v in feat.gates.values() if v)
        gpct = gp / len(FEATURE_GATES) * 100
        bias_icon = {"autonomous": "\u26a1", "controlled": "\U0001f6e1\ufe0f"}.get(
            feat.autonomy_bias, ""
        )
        gate_rows += (
            f'<div class="pr"><div class="pi">'
            f'<span class="fn">{_esc(feat.feature_id)}</span>'
            f'<span class="tb {tier_cls}">{_esc(feat.coverage_tier)}</span>'
            f'{bias_icon}</div>'
            f'<div class="gs">{steps}</div>'
            f'<span class="gp">{gpct:.0f}%</span></div>'
        )

    # ── Health Cards ──────────────────────────────────────────────────
    health_cards = ""
    for team in report.teams:
        tg = (team.gates_passed / team.gates_total * 100) if team.gates_total else 0
        tw = (team.wi_done / team.wi_total * 100) if team.wi_total else 0
        tc = "red" if (tg < 30 or tw < 40) else ("yellow" if (tg < 60 or tw < 70) else "green")
        health_cards += (
            f'<div class="tc"><div class="tc-h">'
            f'<h3>{_esc(team.name or team.team_id)}</h3>'
            f'<span class="hd {tc}"></span></div>'
            f'<div class="tm"><label>Gates</label>'
            f'<div class="pb"><div class="fl fl-{tc}" style="width:{tg:.0f}%">'
            f'<span>{tg:.0f}%</span></div></div></div>'
            f'<div class="tm"><label>WIs</label>'
            f'<div class="pb"><div class="fl fl-{tc}" style="width:{tw:.0f}%">'
            f'<span>{tw:.0f}%</span></div></div></div>'
            f'<div class="tc-s">{team.feature_count} feat '
            f'&middot; {team.wi_done}/{team.wi_total} WIs</div></div>'
        )

    # ── Milestones ────────────────────────────────────────────────────
    ms_rows = ""
    for ms in report.milestones:
        mc = {"on-track": "green", "at-risk": "yellow", "blocked": "red"}.get(
            ms.status, "green"
        )
        mft = len(ms.feature_ids)
        mfd = sum(
            1 for fid in ms.feature_ids
            if any(f.feature_id == fid and f.gates.get("Final", False) for f in report.features)
        )
        mpct = (mfd / mft * 100) if mft else 0
        days_html = ""
        if ms.target_date:
            try:
                delta = (date.fromisoformat(ms.target_date) - date.today()).days
                if delta < 0:
                    days_html = f'<span class="dl over">{abs(delta)}d overdue</span>'
                elif delta == 0:
                    days_html = '<span class="dl today">Today</span>'
                else:
                    days_html = f'<span class="dl">{delta}d left</span>'
            except ValueError:
                pass
        feats = ", ".join(ms.feature_ids)
        ms_rows += (
            f'<div class="mr"><div class="mi">'
            f'<span class="msid">{_esc(ms.milestone_id)}</span>'
            f'<span class="msn">{_esc(ms.name)}</span>'
            f'<span class="badge {mc}">{_esc(ms.status.upper())}</span></div>'
            f'<div class="mb2"><div class="pb">'
            f'<div class="fl fl-{mc}" style="width:{mpct:.0f}%">'
            f'<span>{mpct:.0f}%</span></div></div>'
            f'<span class="msd">{_esc(ms.target_date)}</span>{days_html}</div>'
            f'<div class="mf">{_esc(feats)}</div></div>'
        )

    # ── Blockers & Risks ──────────────────────────────────────────────
    blk_html = ""
    if report.risk_escalations:
        for i, esc_t in enumerate(report.risk_escalations):
            blk_html += (
                f'<div class="bi"><span class="sd red"></span>'
                f'<span class="bt">{_esc(esc_t)}</span></div>'
            )
    else:
        blk_html = '<div class="empty">No active risks or blockers</div>'

    # ── Dependency SVG ────────────────────────────────────────────────
    dep_svg = ""
    dep_table = ""
    if report.dependencies:
        feat_ids = [f.feature_id for f in report.features]
        n = len(feat_ids)
        nw, nh, gx, gy = 140, 44, 50, 40
        cols = min(n, 4)
        rws = (n + cols - 1) // cols
        sw = cols * (nw + gx) + gx
        sh = rws * (nh + gy) + gy + 10
        pos: Dict[str, tuple] = {}
        for i, fid in enumerate(feat_ids):
            cx = gx + (i % cols) * (nw + gx) + nw // 2
            cy = gy + (i // cols) * (nh + gy) + nh // 2
            pos[fid] = (cx, cy)
        # Nodes
        snodes = ""
        for fid, (cx, cy) in pos.items():
            ft = next((f for f in report.features if f.feature_id == fid), None)
            sc = {"critical": "#de350b", "standard": "#0052cc", "experimental": "#6554c0"}.get(
                ft.coverage_tier if ft else "standard", "#0052cc"
            )
            snodes += (
                f'<rect x="{cx - nw // 2}" y="{cy - nh // 2}" width="{nw}" '
                f'height="{nh}" rx="6" fill="#fff" stroke="{sc}" stroke-width="2"/>'
                f'<text x="{cx}" y="{cy + 4}" text-anchor="middle" font-size="11" '
                f'font-family="-apple-system,sans-serif" fill="#172b4d">{_esc(fid)}</text>'
            )
        # Arrows
        acol = {"resolved": "#00875a", "in_progress": "#0065ff",
                "blocked": "#de350b", "pending": "#97a0af"}
        sarrows = ""
        for dep in report.dependencies:
            if dep.from_feature in pos and dep.to_feature in pos:
                x1, y1 = pos[dep.from_feature]
                x2, y2 = pos[dep.to_feature]
                c = acol.get(dep.status, "#97a0af")
                da = "" if dep.dep_type == "blocking" else ' stroke-dasharray="6,3"'
                sx, sy, ex, ey = x1 + nw // 2, y1, x2 - nw // 2, y2
                if abs(y1 - y2) < 5:
                    sarrows += (
                        f'<line x1="{sx}" y1="{sy}" x2="{ex - 8}" y2="{ey}" '
                        f'stroke="{c}" stroke-width="2"{da}/>'
                        f'<polygon points="{ex},{ey} {ex - 8},{ey - 5} '
                        f'{ex - 8},{ey + 5}" fill="{c}"/>'
                    )
                else:
                    mx = (sx + ex) // 2
                    sarrows += (
                        f'<path d="M{sx},{sy} C{mx},{sy} {mx},{ey} {ex - 8},{ey}" '
                        f'fill="none" stroke="{c}" stroke-width="2"{da}/>'
                        f'<polygon points="{ex},{ey} {ex - 8},{ey - 5} '
                        f'{ex - 8},{ey + 5}" fill="{c}"/>'
                    )
        dep_svg = (
            f'<svg viewBox="0 0 {sw} {sh}" width="100%" '
            f'xmlns="http://www.w3.org/2000/svg">{sarrows}{snodes}</svg>'
        )
        # Also build table rows
        for dep in report.dependencies:
            dc = acol.get(dep.status, "#97a0af")
            ty_icon = "\u2192" if dep.dep_type == "blocking" else "\u21e2"
            dep_table += (
                f'<tr><td>{_esc(dep.from_feature)}</td>'
                f'<td style="color:{dc};font-size:1.3em">{ty_icon}</td>'
                f'<td>{_esc(dep.to_feature)}</td>'
                f'<td><span class="badge" style="background:{dc};color:#fff">'
                f'{_esc(dep.dep_type)}</span></td>'
                f'<td><span class="badge" style="background:{dc};color:#fff">'
                f'{_esc(dep.status)}</span></td></tr>'
            )
    else:
        dep_svg = ""
        dep_table = '<tr><td colspan="5" class="empty">No cross-team dependencies</td></tr>'

    # ── CSS ────────────────────────────────────────────────────────────
    css = """
:root{--bg:#f4f5f7;--card:#fff;--bdr:#dfe1e6;--tx:#172b4d;--txm:#5e6c84;
--acc:#0052cc;--grn:#00875a;--ylw:#ff991f;--red:#de350b;--blu:#0065ff;--prp:#6554c0}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
background:var(--bg);color:var(--tx);padding:16px 24px;line-height:1.5}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;
background:var(--card);border-radius:8px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.hdr h1{font-size:1.3rem}.hdr-r{display:flex;align-items:center;gap:12px;font-size:.85rem;color:var(--txm)}
.badge{display:inline-block;padding:3px 10px;border-radius:10px;font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.badge.green{background:#e3fcef;color:var(--grn)}.badge.yellow{background:#fff7e6;color:#974f0c}
.badge.red{background:#ffebe6;color:var(--red)}.badge.blue{background:#deebff;color:var(--blu)}
.kpi{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
.kpi-c{background:var(--card);padding:14px 16px;border-radius:8px;text-align:center;
box-shadow:0 1px 3px rgba(0,0,0,.08)}
.kpi-v{display:block;font-size:1.7rem;font-weight:800;color:var(--acc)}
.kpi-l{font-size:.72rem;color:var(--txm);text-transform:uppercase;letter-spacing:.5px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.panel{background:var(--card);border-radius:8px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.panel h2{font-size:.9rem;font-weight:700;margin-bottom:14px;padding-bottom:8px;
border-bottom:2px solid var(--acc);text-transform:uppercase;letter-spacing:.5px}
.fw{grid-column:1/-1}
.tc{border:1px solid var(--bdr);border-radius:8px;padding:14px;margin-bottom:10px}
.tc-h{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
.tc-h h3{font-size:.85rem}.hd{width:10px;height:10px;border-radius:50%;display:inline-block}
.hd.green{background:var(--grn)}.hd.yellow{background:var(--ylw)}.hd.red{background:var(--red)}
.tm{margin-bottom:8px}.tm label{font-size:.7rem;color:var(--txm);display:block;margin-bottom:3px}
.pb{background:#ebecf0;border-radius:6px;height:20px;overflow:hidden;position:relative}
.fl{height:100%;border-radius:6px;display:flex;align-items:center;justify-content:center;
font-size:.65rem;font-weight:700;color:#fff;min-width:0;transition:width .4s}
.fl-green{background:var(--grn)}.fl-yellow{background:var(--ylw)}.fl-red{background:var(--red)}
.fl span{padding:0 4px;white-space:nowrap}
.tc-s{font-size:.72rem;color:var(--txm);margin-top:6px}
.pr{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #f0f1f3}
.pr:last-child{border-bottom:none}.pi{min-width:170px;display:flex;align-items:center;gap:6px}
.fn{font-size:.8rem;font-weight:600}.tb{font-size:.6rem;padding:2px 6px;border-radius:8px;font-weight:600}
.t-crit{background:#ffebe6;color:var(--red)}.t-std{background:#deebff;color:var(--blu)}
.t-exp{background:#eae6ff;color:var(--prp)}
.gs{display:flex;gap:3px;flex:1}.st{width:36px;height:28px;border-radius:4px;display:flex;
align-items:center;justify-content:center;font-size:.65rem;font-weight:600;
background:#ebecf0;color:var(--txm);border:2px solid transparent}
.st.done{background:#e3fcef;color:var(--grn);border-color:var(--grn)}
.st.cur{background:#deebff;color:var(--blu);border-color:var(--blu);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
.gp{font-size:.75rem;font-weight:700;min-width:36px;text-align:right}
.kb{margin-top:8px}.kb-ctrl{margin-bottom:12px;display:flex;gap:10px;align-items:center}
.kb-ctrl select{padding:6px 10px;border:1px solid var(--bdr);border-radius:6px;font-size:.8rem}
.kb-ctrl .legend{display:flex;gap:8px;margin-left:auto;font-size:.65rem;color:var(--txm)}
.legend span{display:flex;align-items:center;gap:3px}
.legend .dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.board{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.col{background:#f7f8fc;border-radius:8px;padding:10px;min-height:120px}
.col h3{font-size:.78rem;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.col h3 .cnt{background:var(--bdr);border-radius:10px;padding:1px 8px;font-size:.7rem}
.col-p h3{color:#5e6c84}.col-i h3{color:var(--blu)}.col-d h3{color:var(--grn)}
.wc{background:#fff;border-radius:6px;padding:10px;margin-bottom:8px;border-left:3px solid var(--bdr);
box-shadow:0 1px 2px rgba(0,0,0,.06);cursor:default;transition:box-shadow .15s}
.wc:hover{box-shadow:0 2px 8px rgba(0,0,0,.12)}
.wc.mode-validate{border-left-color:var(--red)}.wc.mode-confirm{border-left-color:var(--ylw)}
.wc.mode-autopilot{border-left-color:var(--grn)}
.wc-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.wid{font-size:.72rem;font-weight:700}.mb{font-size:.6rem;padding:2px 6px;border-radius:8px;font-weight:600}
.mb.mode-validate{background:#ffebe6;color:var(--red)}.mb.mode-confirm{background:#fff7e6;color:#974f0c}
.mb.mode-autopilot{background:#e3fcef;color:var(--grn)}
.wc-t{font-size:.75rem;color:var(--tx);margin-bottom:4px;line-height:1.3}
.wc-f{display:flex;justify-content:space-between;align-items:center;font-size:.65rem;color:var(--txm)}
.ft{background:#f0f1f3;padding:1px 6px;border-radius:4px}.rc{color:var(--red);font-weight:600}
.mr{padding:10px 0;border-bottom:1px solid #f0f1f3}.mr:last-child{border-bottom:none}
.mi{display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap}
.msid{font-size:.75rem;font-weight:700}.msn{font-size:.8rem}
.mb2{display:flex;align-items:center;gap:10px;margin-bottom:4px}
.mb2 .pb{flex:1}.msd{font-size:.7rem;color:var(--txm);white-space:nowrap}
.dl{font-size:.65rem;font-weight:600;padding:2px 6px;border-radius:8px;background:#deebff;color:var(--blu)}
.dl.over{background:#ffebe6;color:var(--red)}.dl.today{background:#fff7e6;color:#974f0c}
.mf{font-size:.68rem;color:var(--txm)}
.bi{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid #f0f1f3}
.bi:last-child{border-bottom:none}.sd{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.sd.red{background:var(--red)}.bt{font-size:.78rem;word-break:break-all}
.dep-tbl{width:100%;border-collapse:collapse;font-size:.78rem;margin-top:12px}
.dep-tbl th{text-align:left;font-size:.7rem;color:var(--txm);padding:6px 8px;border-bottom:2px solid var(--bdr)}
.dep-tbl td{padding:6px 8px;border-bottom:1px solid #f0f1f3}
.empty{color:var(--txm);font-size:.8rem;padding:16px;text-align:center}
footer{text-align:center;font-size:.7rem;color:var(--txm);padding:20px 0}
@media(max-width:900px){.grid{grid-template-columns:1fr}.kpi{grid-template-columns:repeat(2,1fr)}
.board{grid-template-columns:1fr}}
@media print{body{padding:8px}
.wc:hover{box-shadow:none}.st.cur{animation:none}}
"""

    # ── JS (feature filter) ───────────────────────────────────────────
    js = """
document.getElementById('ff').addEventListener('change',function(){
  var v=this.value;
  document.querySelectorAll('.wc').forEach(function(c){
    c.style.display=(v==='all'||c.dataset.f===v)?'':'none';
  });
  ['p','i','d'].forEach(function(s){
    var col=document.querySelector('.col-'+s);
    if(!col)return;
    var vis=col.querySelectorAll('.wc[style=""],.wc:not([style])').length;
    var cnt=col.querySelector('.cnt');
    if(cnt)cnt.textContent=vis;
  });
});
"""

    # ── Assemble HTML ─────────────────────────────────────────────────
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Epic Dashboard: {_esc(report.epic_id)}</title>
<style>{css}</style>
</head>
<body>

<div class="hdr">
  <div><h1>{_esc(report.epic_id)}: {_esc(report.epic_title)}</h1></div>
  <div class="hdr-r">
    <span class="badge {health_cls}">{health_lbl}</span>
    <span>Generated: {today}</span>
  </div>
</div>

<div class="kpi">
  <div class="kpi-c"><span class="kpi-v">{total_features}</span><span class="kpi-l">Features</span></div>
  <div class="kpi-c"><span class="kpi-v">{total_gates_passed}/{total_gates}</span><span class="kpi-l">Gates Passed</span></div>
  <div class="kpi-c"><span class="kpi-v">{total_wi_done}/{total_wi}</span><span class="kpi-l">WIs Done</span></div>
  <div class="kpi-c"><span class="kpi-v" style="color:{'var(--red)' if risk_count > 0 else 'var(--grn)'}">{risk_count}</span><span class="kpi-l">Risks</span></div>
</div>

<div class="grid">

<div class="panel">
<h2>Team Health</h2>
{health_cards if health_cards else '<div class="empty">No teams</div>'}
</div>

<div class="panel">
<h2>Gate Pipeline</h2>
{gate_rows if gate_rows else '<div class="empty">No features</div>'}
</div>

</div>

<div class="grid">
<div class="panel fw">
<h2>Work Items</h2>
<div class="kb">
<div class="kb-ctrl">
  <select id="ff">{feat_opts}</select>
  <div class="legend">
    <span><span class="dot" style="background:var(--grn)"></span>autopilot</span>
    <span><span class="dot" style="background:var(--ylw)"></span>confirm</span>
    <span><span class="dot" style="background:var(--red)"></span>validate</span>
  </div>
</div>
<div class="board">
<div class="col col-p"><h3>Pending <span class="cnt">{cnt_p}</span></h3>{pending_cards if pending_cards else '<div class="empty">-</div>'}</div>
<div class="col col-i"><h3>In Progress <span class="cnt">{cnt_i}</span></h3>{ip_cards if ip_cards else '<div class="empty">-</div>'}</div>
<div class="col col-d"><h3>Done <span class="cnt">{cnt_d}</span></h3>{done_cards if done_cards else '<div class="empty">-</div>'}</div>
</div>
</div>
</div>
</div>

<div class="grid">

<div class="panel">
<h2>Milestones</h2>
{ms_rows if ms_rows else '<div class="empty">No milestones defined</div>'}
</div>

<div class="panel">
<h2>Blockers &amp; Risks</h2>
{blk_html}
</div>

</div>

<div class="grid">
<div class="panel fw">
<h2>Cross-Team Dependencies</h2>
{dep_svg}
<table class="dep-tbl">
<thead><tr><th>From</th><th></th><th>To</th><th>Type</th><th>Status</th></tr></thead>
<tbody>{dep_table}</tbody>
</table>
</div>
</div>

<footer>SDD Templates &middot; Tecnos-STRIDE v3.1.0 &middot; Generated by epic_progress_aggregator.py &middot; {today}</footer>

<script>{js}</script>
</body>
</html>"""


# ── Weekly Summary (STRIDE Learning Loop) ─────────────────────────────


def _count_findings(findings_path: Path) -> int:
    """Count investigation sections in findings.md."""
    if not findings_path.exists():
        return 0
    try:
        content = _read_text(findings_path)
        return len(re.findall(r'^## Investigation \d+', content, re.MULTILINE))
    except Exception:
        return 0


def _count_decisions(plan_path: Path) -> int:
    """Count numbered decisions in plan.md Approach section."""
    if not plan_path.exists():
        return 0
    try:
        content = _read_text(plan_path)
        approach = re.search(r'## Approach\s*\n(.*?)(?=\n## |\Z)', content, re.DOTALL)
        if approach:
            return len(re.findall(r'^\d+\.', approach.group(1), re.MULTILINE))
        return 0
    except Exception:
        return 0


def _detect_spec_impact(walkthrough_path: Path) -> str:
    """Detect spec impact level from walkthrough.md."""
    if not walkthrough_path.exists():
        return "none"
    try:
        content = _read_text(walkthrough_path)
        if re.search(r'spec.impact.*required|required.*spec.impact', content, re.IGNORECASE):
            return "required"
        if re.search(r'spec.impact.*proposed|proposed.*spec.impact', content, re.IGNORECASE):
            return "proposed"
        if re.search(r'spec.*drift.*critical|critical.*drift', content, re.IGNORECASE):
            return "required"
        return "none"
    except Exception:
        return "none"


def _parse_lesson_items(lessons_path: Path) -> List[str]:
    """Parse lesson items from lessons.md across all lesson sections.

    Extracts items from:
      - ## Best Practices Discovered  → prefixed [BP]
      - ## Troubles Resolved          → prefixed [TR]
      - ## Technical Knowledge         → prefixed [TK]
      - ## Reusable Patterns           → prefixed [RP] (backward compat)

    Returns List[str] (unchanged contract — WeeklyRunData.lessons stays List[str]).
    """
    if not lessons_path.exists():
        return []
    try:
        content = _read_text(lessons_path)
        section_map = {
            "Best Practices Discovered": "BP",
            "Troubles Resolved": "TR",
            "Technical Knowledge": "TK",
            "Reusable Patterns": "RP",
        }
        results: List[str] = []
        for heading, prefix in section_map.items():
            section = re.search(
                rf'## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)',
                content,
                re.DOTALL,
            )
            if section:
                items = re.findall(r'^[-*]\s+(.+)', section.group(1), re.MULTILINE)
                for item in items:
                    results.append(f"[{prefix}] {item}")
        return results
    except Exception:
        return []


def scan_weekly_runs(epic_dir: str | Path) -> Tuple[List[WeeklyRunData], List[str]]:
    """Scan all run directories under the epic for weekly summary data."""
    epic_path = Path(epic_dir).resolve()
    project_root = _find_project_root(epic_path)
    specs_dir = project_root / "specs"

    epic_data = _extract_yaml_from_md(epic_path / "epic_design.md")
    if not epic_data or "epic" not in epic_data:
        return [], ["Cannot parse epic_design.md"]

    features = epic_data["epic"].get("features", [])
    runs_data: List[WeeklyRunData] = []
    errors: List[str] = []

    for feat in features:
        fid = feat.get("feature_id", "")
        if not fid:
            continue
        runs_dir = specs_dir / fid / "runs"
        if not runs_dir.exists():
            continue

        for wi_dir in sorted(runs_dir.iterdir()):
            if not wi_dir.is_dir():
                continue
            wi_id = wi_dir.name

            for run_dir in sorted(wi_dir.iterdir()):
                if not run_dir.is_dir() or not run_dir.name.startswith("RUN-"):
                    continue

                planning = run_dir / ".planning"
                rd = WeeklyRunData(
                    wi_id=wi_id,
                    run_id=run_dir.name,
                    feature_id=fid,
                    findings_count=_count_findings(planning / "findings.md"),
                    decisions_count=_count_decisions(planning / "plan.md"),
                    spec_impact=_detect_spec_impact(run_dir / "walkthrough.md"),
                    lessons=_parse_lesson_items(planning / "lessons.md"),
                )
                runs_data.append(rd)

    return runs_data, errors


def format_weekly_summary(epic_id: str, runs: List[WeeklyRunData]) -> str:
    """Format weekly STRIDE summary as markdown."""
    lines: List[str] = []
    today = date.today().isoformat()

    lines.append(f"# STRIDE Weekly Summary: {epic_id}")
    lines.append(f"> Week of {today}")
    lines.append("")

    # Findings Trend
    lines.append("## Findings Trend")
    lines.append("")
    lines.append("| WI ID | Run ID | Findings | Decisions | Spec Impact |")
    lines.append("|-------|--------|----------|-----------|-------------|")
    for r in runs:
        impact = {"none": "-", "proposed": "proposed", "required": "**REQUIRED**"}.get(
            r.spec_impact, "-",
        )
        lines.append(
            f"| {r.wi_id} | {r.run_id} | {r.findings_count} "
            f"| {r.decisions_count} | {impact} |"
        )
    lines.append("")

    # Open Spec Impacts
    open_impacts = [r for r in runs if r.spec_impact != "none"]
    lines.append("## Open Spec Impacts")
    lines.append("")
    if open_impacts:
        for r in open_impacts:
            lines.append(f"- **{r.wi_id}** ({r.run_id}): {r.spec_impact}")
    else:
        lines.append("- No open spec impacts")
    lines.append("")

    # Decision Log
    lines.append("## Decision Log")
    lines.append("")
    lines.append("| # | WI ID | Decisions | Source |")
    lines.append("|---|-------|-----------|--------|")
    idx = 1
    for r in runs:
        if r.decisions_count > 0:
            lines.append(
                f"| {idx} | {r.wi_id} | {r.decisions_count} decision(s) "
                f"| {r.run_id}/plan.md |"
            )
            idx += 1
    if idx == 1:
        lines.append("| - | - | No decisions recorded | - |")
    lines.append("")

    # Learnings
    all_lessons: List[Tuple[str, str]] = []
    for r in runs:
        for lesson in r.lessons:
            all_lessons.append((r.wi_id, lesson))

    lines.append("## Learnings")
    lines.append("")
    lines.append("| # | WI ID | Pattern |")
    lines.append("|---|-------|---------|")
    for i, (wi_id, lesson) in enumerate(all_lessons, 1):
        lines.append(f"| {i} | {wi_id} | {lesson} |")
    if not all_lessons:
        lines.append("| - | - | No learnings captured |")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Runs**: {len(runs)}")
    lines.append(f"- **Total Findings**: {sum(r.findings_count for r in runs)}")
    lines.append(f"- **Total Decisions**: {sum(r.decisions_count for r in runs)}")
    lines.append(f"- **Open Spec Impacts**: {len(open_impacts)}")
    lines.append(f"- **Learnings captured**: {len(all_lessons)}")
    lines.append("")

    return "\n".join(lines)


def _post_weekly_to_issue(issue_number: int, body: str, repo: str = "") -> bool:
    """Post weekly summary as a GitHub issue comment."""
    import subprocess as _sp
    cmd = ["gh", "issue", "comment", str(issue_number), "--body", body]
    if repo:
        cmd.extend(["--repo", repo])
    result = _sp.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


# ── Main ───────────────────────────────────────────────────────────────


def run_tests() -> bool:
    """Run self-tests."""
    import shutil
    import tempfile

    print("Running epic_progress_aggregator.py self-tests...\n")

    # Test 1: Non-existent path returns errors
    print("Test 1: Non-existent directory")
    report = aggregate_epic_progress("/nonexistent/path")
    assert len(report.errors) > 0, f"Expected errors for non-existent path, got none"
    print("  PASS: Non-existent directory returns error")

    # Test 2: Minimal epic structure
    print("\nTest 2: Minimal epic structure")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        epic_dir = tmpdir / "epics" / "EPIC-TEST"
        epic_dir.mkdir(parents=True)
        specs_dir = tmpdir / "specs"
        specs_dir.mkdir()
        (tmpdir / "memory").mkdir()

        # Create epic_design.md
        (epic_dir / "epic_design.md").write_text("""# Epic Design: EPIC-TEST

## 0. Canonical Epic Design (YAML)

```yaml
epic:
  meta:
    epic_id: "EPIC-TEST"
    title: "Test Epic"
    version: "1.0.0"
    status: "draft"
  ownership:
    epic_lead: "Test Lead"
    teams:
      - team_id: "TEAM-A"
        name: "Alpha Team"
        features: ["FEAT-A-001"]
      - team_id: "TEAM-B"
        name: "Beta Team"
        features: ["FEAT-B-001"]
  features:
    - feature_id: "FEAT-A-001"
      name: "Feature Alpha"
      team_id: "TEAM-A"
      coverage_tier: "critical"
      priority: 1
      dependencies: []
    - feature_id: "FEAT-B-001"
      name: "Feature Beta"
      team_id: "TEAM-B"
      coverage_tier: "standard"
      priority: 2
      dependencies: ["FEAT-A-001"]
  shared_contracts:
    - contract_id: "SC-API-TEST"
      name: "Test API"
      owner_team: "TEAM-A"
  cross_team_dependencies:
    - dependency_id: "DEP-001"
      from_feature: "FEAT-B-001"
      to_feature: "FEAT-A-001"
      type: "blocking"
      interface: "SC-API-TEST"
  milestones:
    - id: "EM-01"
      name: "Core Complete"
      target_date: "2025-06-30"
      features: ["FEAT-A-001"]
    - id: "EM-02"
      name: "Integration Complete"
      target_date: "2025-09-30"
      features: ["FEAT-A-001", "FEAT-B-001"]
```
""")

        report = aggregate_epic_progress(str(epic_dir))
        assert report.epic_id == "EPIC-TEST", f"Expected EPIC-TEST, got {report.epic_id}"
        assert len(report.features) == 2, f"Expected 2 features, got {len(report.features)}"
        assert len(report.teams) == 2, f"Expected 2 teams, got {len(report.teams)}"
        assert len(report.milestones) == 2, f"Expected 2 milestones, got {len(report.milestones)}"
        print("  PASS: Minimal epic parsed correctly")

        # Test 3: Feature with APPROVAL.md
        print("\nTest 3: Feature with approved gates")
        feat_a_dir = specs_dir / "FEAT-A-001"
        feat_a_dir.mkdir(parents=True)
        (feat_a_dir / "APPROVAL.md").write_text("""# Feature Approval Record

## Gate 1: Design Review

### Checklist
- [x] basic_design.md complete

Approver: Test User
Date: 2025-01-01

---

## Gate 2: BPMN Review

### Checklist
- [x] process.bpmn complete

Approver: Test User
Date: 2025-01-02

---

## Gate 3: Specification Review

### Checklist
- [ ] spec.md complete

Approver: ___________

---

## Gate 4: Plan Review

### Checklist
- [ ] plan.md complete

---

## Gate 5: Tasking Review

### Checklist
- [ ] tasks.md complete

---

## Final: Evidence Review

### Checklist
- [ ] Evidence Pack complete
""")

        report = aggregate_epic_progress(str(epic_dir))
        feat_a = next(f for f in report.features if f.feature_id == "FEAT-A-001")
        assert feat_a.gates["Gate 1"] is True, f"Gate 1 should be True, got {feat_a.gates['Gate 1']}"
        assert feat_a.gates["Gate 2"] is True, f"Gate 2 should be True, got {feat_a.gates['Gate 2']}"
        assert feat_a.gates["Gate 3"] is False, f"Gate 3 should be False"
        assert feat_a.gates["Final"] is False, f"Final should be False"
        print("  PASS: Gate parsing correct (2 passed, 4 pending)")

        # Verify team stats
        team_a = next(t for t in report.teams if t.team_id == "TEAM-A")
        assert team_a.gates_passed == 2, f"Expected 2 gates passed for TEAM-A, got {team_a.gates_passed}"
        print("  PASS: Team gate aggregation correct")

        # Test 4: Feature with state.yaml and WIs
        print("\nTest 4: Feature with work items")
        state_dir = feat_a_dir / "state"
        state_dir.mkdir()
        (state_dir / "state.yaml").write_text("""feature: FEAT-A-001
current_gate: Gate5
work_items:
  - wi_id: WI-A-001
    status: done
    mode: autopilot
  - wi_id: WI-A-002
    status: in_progress
    mode: validate
  - wi_id: WI-A-003
    status: pending
    mode: confirm
""")

        wi_dir = feat_a_dir / "work_items"
        wi_dir.mkdir()
        (wi_dir / "WI-A-001.md").write_text("""---
wi_id: WI-A-001
title: "Done item"
mode: autopilot
risk_flags: ["ui_only"]
complexity: low
---
# Intent
""")
        (wi_dir / "WI-A-002.md").write_text("""---
wi_id: WI-A-002
title: "In progress validate"
mode: validate
risk_flags: ["authz", "pii"]
complexity: high
---
# Intent
""")
        (wi_dir / "WI-A-003.md").write_text("""---
wi_id: WI-A-003
title: "Pending item"
mode: confirm
risk_flags: ["new_api"]
complexity: medium
---
# Intent
""")

        report = aggregate_epic_progress(str(epic_dir))
        feat_a = next(f for f in report.features if f.feature_id == "FEAT-A-001")
        assert feat_a.wi_total == 3, f"Expected 3 WIs, got {feat_a.wi_total}"
        assert feat_a.wi_done == 1, f"Expected 1 done, got {feat_a.wi_done}"
        assert feat_a.wi_in_progress == 1, f"Expected 1 in_progress, got {feat_a.wi_in_progress}"
        assert feat_a.wi_pending == 1, f"Expected 1 pending, got {feat_a.wi_pending}"
        print("  PASS: WI status counts correct")

        # Test risk escalation
        assert len(report.risk_escalations) > 0, "Expected risk escalations"
        assert any("WI-A-002" in e for e in report.risk_escalations), "WI-A-002 should be in risk escalations"
        print("  PASS: Risk escalation detected for validate-mode in_progress WI")

        # Test 5: Output formats
        print("\nTest 5: Output formatters")
        summary = _format_summary(report)
        assert "EPIC-TEST" in summary, "Summary should contain epic ID"
        assert "TEAM-A" in summary, "Summary should contain team ID"
        print("  PASS: Summary format works")

        json_out = _format_json(report)
        parsed = json.loads(json_out)
        assert parsed["epic_id"] == "EPIC-TEST", "JSON epic_id mismatch"
        assert len(parsed["features"]) == 2, "JSON should have 2 features"
        assert len(parsed["teams"]) == 2, "JSON should have 2 teams"
        print("  PASS: JSON format works")

        md_out = _format_markdown(report)
        assert "# Epic Dashboard: EPIC-TEST" in md_out, "Markdown should have title"
        assert "Gate Completion Matrix" in md_out, "Markdown should have gate matrix"
        assert "Team Status" in md_out, "Markdown should have team status"
        print("  PASS: Markdown format works")

        html_out = _format_html(report)
        assert "<!DOCTYPE html>" in html_out, "HTML should start with DOCTYPE"
        assert "EPIC-TEST" in html_out, "HTML should contain epic ID"
        assert "Team Health" in html_out, "HTML should have Team Health panel"
        assert "Gate Pipeline" in html_out, "HTML should have Gate Pipeline panel"
        assert "Work Items" in html_out, "HTML should have Work Items (Kanban) panel"
        assert "Milestones" in html_out, "HTML should have Milestones panel"
        assert "Blockers" in html_out, "HTML should have Blockers panel"
        assert "Dependencies" in html_out, "HTML should have Dependencies panel"
        assert "WI-A-002" in html_out, "HTML should contain WI cards"
        assert "mode-validate" in html_out, "HTML should show validate mode styling"
        assert "FEAT-A-001" in html_out, "HTML should contain feature IDs"
        print("  PASS: HTML format works (6 panels verified)")

        # Test 7: Dependencies captured
        print("\nTest 7: Dependencies captured")
        assert len(report.dependencies) == 1, f"Expected 1 dependency, got {len(report.dependencies)}"
        assert report.dependencies[0].dep_id == "DEP-001", "Dependency ID mismatch"
        assert report.dependencies[0].from_feature == "FEAT-B-001", "Dependency from mismatch"
        assert report.dependencies[0].to_feature == "FEAT-A-001", "Dependency to mismatch"
        print("  PASS: Dependencies correctly extracted")

        # Test 8: WI details captured
        print("\nTest 8: WI details for Kanban")
        feat_a = next(f for f in report.features if f.feature_id == "FEAT-A-001")
        assert len(feat_a.wi_details) == 3, f"Expected 3 WI details, got {len(feat_a.wi_details)}"
        validate_wi = next(w for w in feat_a.wi_details if w.wi_id == "WI-A-002")
        assert validate_wi.mode == "validate", f"WI-A-002 mode should be validate, got {validate_wi.mode}"
        assert validate_wi.status == "in_progress", f"WI-A-002 status should be in_progress"
        assert "authz" in validate_wi.risk_flags, "WI-A-002 should have authz risk flag"
        print("  PASS: WI Kanban details captured correctly")

        # Test 9: Ops readiness
        print("\nTest 9: Ops readiness")
        assert feat_a.ops_pack_complete is False, "Ops pack should be incomplete"
        ops_dir = feat_a_dir / "ops"
        ops_dir.mkdir()
        for name in FULL_OPS_PACK:
            (ops_dir / name).write_text("# ops\n")
        report = aggregate_epic_progress(str(epic_dir))
        feat_a = next(f for f in report.features if f.feature_id == "FEAT-A-001")
        assert feat_a.ops_pack_complete is True, "Ops pack should be complete after creating all files"
        print("  PASS: Ops readiness detection correct")

        # Test 10: Weekly summary - helper parsers
        print("\nTest 10: Weekly summary helpers")
        weekly_dir = tmpdir / "weekly_test"
        weekly_dir.mkdir()

        (weekly_dir / "findings.md").write_text(
            "## Investigation 1: Foo\n- Found X\n\n## Investigation 2: Bar\n- Found Y\n"
        )
        assert _count_findings(weekly_dir / "findings.md") == 2, "Expected 2 findings"
        print("  PASS: _count_findings")

        (weekly_dir / "plan.md").write_text(
            "## Approach\n1. Do A\n2. Do B\n3. Do C\n\n## Phases\n| Phase |\n"
        )
        assert _count_decisions(weekly_dir / "plan.md") == 3, "Expected 3 decisions"
        print("  PASS: _count_decisions")

        (weekly_dir / "walkthrough.md").write_text(
            "# Walkthrough\n\nSpec impact: proposed changes to API contract\n"
        )
        assert _detect_spec_impact(weekly_dir / "walkthrough.md") == "proposed"
        print("  PASS: _detect_spec_impact (proposed)")

        # Test backward compat: old format with only ## Reusable Patterns
        (weekly_dir / "lessons.md").write_text(
            "## Reusable Patterns\n- Cache invalidation via TTL\n- Retry with exponential backoff\n\n## Errors\n"
        )
        lessons = _parse_lesson_items(weekly_dir / "lessons.md")
        assert len(lessons) == 2, f"Expected 2 lessons, got {len(lessons)}"
        assert lessons[0] == "[RP] Cache invalidation via TTL", f"Expected [RP] prefix, got: {lessons[0]}"
        print("  PASS: _parse_lesson_items (backward compat — Reusable Patterns)")

        # Test new format: all 4 sections
        (weekly_dir / "lessons.md").write_text(
            "## Best Practices Discovered\n- Use connection pooling\n\n"
            "## Troubles Resolved\n- YAML parse error on line 42\n- Lint false positive for empty spec\n\n"
            "## Technical Knowledge\n- mcframe uses IDoc for outbound\n\n"
            "## Reusable Patterns\n- Cache invalidation via TTL\n"
        )
        lessons = _parse_lesson_items(weekly_dir / "lessons.md")
        assert len(lessons) == 5, f"Expected 5 lessons from 4 sections, got {len(lessons)}"
        assert lessons[0] == "[BP] Use connection pooling", f"Wrong BP prefix: {lessons[0]}"
        assert lessons[1] == "[TR] YAML parse error on line 42", f"Wrong TR prefix: {lessons[1]}"
        assert lessons[3] == "[TK] mcframe uses IDoc for outbound", f"Wrong TK prefix: {lessons[3]}"
        assert lessons[4] == "[RP] Cache invalidation via TTL", f"Wrong RP prefix: {lessons[4]}"
        print("  PASS: _parse_lesson_items (new format — 4 sections with prefixes)")

        # Test 11: format_weekly_summary
        print("\nTest 11: Weekly summary format")
        test_runs = [
            WeeklyRunData(
                wi_id="WI-TEST-001", run_id="RUN-001", feature_id="FEAT-A",
                findings_count=2, decisions_count=3, spec_impact="proposed",
                lessons=["Cache pattern"],
            ),
            WeeklyRunData(
                wi_id="WI-TEST-002", run_id="RUN-002", feature_id="FEAT-A",
                findings_count=0, decisions_count=1, spec_impact="none",
                lessons=[],
            ),
        ]
        summary = format_weekly_summary("EPIC-TEST", test_runs)
        assert "STRIDE Weekly Summary: EPIC-TEST" in summary, "Missing title"
        assert "Findings Trend" in summary, "Missing Findings Trend"
        assert "WI-TEST-001" in summary, "Missing WI-TEST-001"
        assert "proposed" in summary, "Missing spec impact"
        assert "Cache pattern" in summary, "Missing lesson"
        assert "Total Runs**: 2" in summary, "Wrong run count"
        print("  PASS: format_weekly_summary")

        # Test 12: scan_weekly_runs with run data
        print("\nTest 12: scan_weekly_runs")
        feat_a_runs = specs_dir / "FEAT-A-001" / "runs"
        feat_a_runs.mkdir(parents=True, exist_ok=True)
        wi_run_dir = feat_a_runs / "WI-A-001" / "RUN-20260215-1000"
        wi_run_dir.mkdir(parents=True)
        planning_dir = wi_run_dir / ".planning"
        planning_dir.mkdir()
        (planning_dir / "findings.md").write_text(
            "## Investigation 1: Test\n- Found something\n"
        )
        (planning_dir / "plan.md").write_text(
            "## Approach\n1. First step\n2. Second step\n"
        )
        (wi_run_dir / "walkthrough.md").write_text(
            "# Walkthrough\nSpec impact: none\n"
        )
        (planning_dir / "lessons.md").write_text(
            "## Reusable Patterns\n- Test pattern\n"
        )
        runs, errs = scan_weekly_runs(str(epic_dir))
        assert len(runs) == 1, f"Expected 1 run, got {len(runs)}"
        assert runs[0].findings_count == 1, f"Expected 1 finding"
        assert runs[0].decisions_count == 2, f"Expected 2 decisions"
        assert runs[0].lessons == ["[RP] Test pattern"], f"Expected [RP] prefixed lesson, got {runs[0].lessons}"
        print("  PASS: scan_weekly_runs")

    print("\nAll self-tests passed.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Epic Progress Aggregator - Enterprise SDD Extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Summary (default)
    python3 epic_progress_aggregator.py epics/EPIC-ORDER/

    # JSON output
    python3 epic_progress_aggregator.py epics/EPIC-ORDER/ --format json

    # Generate EPIC_DASHBOARD.md
    python3 epic_progress_aggregator.py epics/EPIC-ORDER/ --format markdown

    # Custom output path
    python3 epic_progress_aggregator.py epics/EPIC-ORDER/ --format json --output report.json

    # Run self-tests
    python3 epic_progress_aggregator.py --test
        """,
    )

    parser.add_argument("epic_dir", nargs="?", type=Path, help="Epic directory path")
    parser.add_argument(
        "--format",
        choices=["summary", "json", "markdown", "html"],
        default="summary",
        help="Output format (default: summary)",
    )
    parser.add_argument("--output", type=Path, help="Write output to file instead of stdout")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument("--weekly-summary", action="store_true",
                        help="Generate STRIDE weekly summary from run data")
    parser.add_argument("--epic", type=int,
                        help="GitHub issue number for Epic (used with --post)")
    parser.add_argument("--repo", type=str,
                        help="Repository (owner/repo) for --post")
    parser.add_argument("--post", action="store_true",
                        help="Post summary as GitHub issue comment")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.epic_dir:
        parser.print_help()
        sys.exit(1)

    if args.weekly_summary:
        runs, errors = scan_weekly_runs(args.epic_dir)
        if errors:
            for e in errors:
                print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)
        epic_data = _extract_yaml_from_md(args.epic_dir / "epic_design.md")
        epic_id = "UNKNOWN"
        if epic_data and "epic" in epic_data:
            epic_id = epic_data["epic"].get("meta", {}).get("epic_id", "UNKNOWN")
        weekly_text = format_weekly_summary(epic_id, runs)
        if args.post and args.epic:
            ok = _post_weekly_to_issue(args.epic, weekly_text, repo=args.repo or "")
            if ok:
                print(f"Weekly summary posted to issue #{args.epic}")
            else:
                print(f"Failed to post to issue #{args.epic}", file=sys.stderr)
                print(weekly_text)
                sys.exit(1)
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(weekly_text, encoding="utf-8")
            print(f"Weekly summary written to {args.output}")
        else:
            print(weekly_text)
        sys.exit(0)

    report = aggregate_epic_progress(args.epic_dir)

    if report.errors and args.format != "json":
        for err in report.errors:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)

    if args.format == "summary":
        output = _format_summary(report)
    elif args.format == "json":
        output = _format_json(report)
    elif args.format == "markdown":
        output = _format_markdown(report)
    elif args.format == "html":
        output = _format_html(report)
    else:
        output = _format_summary(report)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Output written to {args.output}")
    else:
        if args.format == "markdown":
            dashboard_path = args.epic_dir / "EPIC_DASHBOARD.md"
            dashboard_path.write_text(output, encoding="utf-8")
            print(f"Dashboard written to {dashboard_path}")
        elif args.format == "html":
            dashboard_path = args.epic_dir / "EPIC_DASHBOARD.html"
            dashboard_path.write_text(output, encoding="utf-8")
            print(f"HTML Dashboard written to {dashboard_path}")
        else:
            print(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
