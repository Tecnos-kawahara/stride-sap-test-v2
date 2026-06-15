#!/usr/bin/env python3
"""Retrospective Report Generator - Quantitative feature/epic retrospective.

Collects phase durations, WI statistics, test coverage, and lesson counts
to generate a data-driven retrospective report.

Inspired by gstack /retro (garrytan/gstack, MIT License).

Usage:
    python3 stride_retro.py specs/<feature>/
    python3 stride_retro.py specs/<feature>/ --json
    python3 stride_retro.py epics/<EPIC_ID>/
    python3 stride_retro.py --test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# YAML parsing helpers
# ---------------------------------------------------------------------------

def _parse_canonical_yaml(file_path: Path, header_pattern: str) -> dict | None:
    """Parse canonical YAML block from a markdown file."""
    if not file_path.is_file():
        return None
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return None

    pattern = re.compile(
        rf"#\s*0\.\s*{header_pattern}.*?\n```yaml\s*\n(.*?)```",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return None

    if yaml is None:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def _read_file_text(file_path: Path) -> str:
    """Read file text, return empty string on failure."""
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Metric collectors
# ---------------------------------------------------------------------------

def _parse_approval_dates(approval_path: Path) -> dict:
    """Parse gate dates from APPROVAL.md.

    Supports both '日付: YYYY-MM-DD' and 'Date: YYYY-MM-DD' formats.
    Returns: {"Gate 1": "2026-01-10", "Gate 5": "2026-01-20", "Final": "2026-02-01", ...}
    """
    dates = {}
    if not approval_path.is_file():
        return dates

    content = _read_file_text(approval_path)
    if not content:
        return dates

    date_pattern = re.compile(r"(?:日付|Date)\s*:\s*(\d{4}-\d{2}-\d{2})")
    gate_pattern = re.compile(r"##\s*(Gate\s*\d+|Final)[^\n]*", re.IGNORECASE)

    current_gate = None
    for line in content.splitlines():
        gate_match = gate_pattern.match(line)
        if gate_match:
            current_gate = gate_match.group(1).strip()
            continue
        if current_gate:
            date_match = date_pattern.search(line)
            if date_match:
                dates[current_gate] = date_match.group(1)
                current_gate = None

    return dates


def _compute_phase_durations(gate_dates: dict) -> dict:
    """Compute phase durations from gate dates.

    Returns: {"design_to_specify": "2d 4h", "specify_to_tasking": "1d", ...}
    """
    result = {
        "design_to_specify": "N/A",
        "specify_to_tasking": "N/A",
        "tasking_to_execute": "N/A",
        "total_lead_time": "N/A",
    }

    def _get_date(key_pattern: str) -> datetime | None:
        for k, v in gate_dates.items():
            if re.match(key_pattern, k, re.IGNORECASE):
                try:
                    return datetime.strptime(v, "%Y-%m-%d")
                except ValueError:
                    return None
        return None

    gate1 = _get_date(r"Gate\s*1")
    gate3 = _get_date(r"Gate\s*3")
    gate5 = _get_date(r"Gate\s*5")
    final = _get_date(r"Final")

    def _fmt_delta(d1, d2):
        if d1 is None or d2 is None:
            return "N/A"
        delta = d2 - d1
        days = delta.days
        hours = delta.seconds // 3600
        if days > 0 and hours > 0:
            return f"{days}d {hours}h"
        elif days > 0:
            return f"{days}d"
        elif hours > 0:
            return f"{hours}h"
        else:
            return "0d"

    result["design_to_specify"] = _fmt_delta(gate1, gate3)
    result["specify_to_tasking"] = _fmt_delta(gate3, gate5)
    result["tasking_to_execute"] = _fmt_delta(gate5, final)

    # Total lead time
    all_dates = []
    for v in gate_dates.values():
        try:
            all_dates.append(datetime.strptime(v, "%Y-%m-%d"))
        except ValueError:
            continue
    if len(all_dates) >= 2:
        all_dates.sort()
        result["total_lead_time"] = _fmt_delta(all_dates[0], all_dates[-1])

    return result


def _collect_wi_stats(feature_dir: Path) -> dict:
    """Collect WI statistics from state/state.yaml."""
    result = {
        "total": 0,
        "mode_breakdown": {},
        "status_breakdown": {},
        "avg_attempts": 0.0,
        "per_wi_attempts": [],  # [{wi_id, attempts, mode}, ...]
    }

    state_path = feature_dir / "state" / "state.yaml"
    if not state_path.is_file() or yaml is None:
        return result

    try:
        data = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError):
        return result

    if not data:
        return result

    work_items = data.get("work_items", [])
    if not work_items:
        return result

    result["total"] = len(work_items)

    # Mode breakdown
    mode_counter = Counter()
    status_counter = Counter()
    known_statuses = {"done", "pending", "in_progress", "blocked"}

    # Build wi_id -> mode lookup
    wi_modes: dict[str, str] = {}
    for wi in work_items:
        mode = wi.get("mode", "other")
        mode_counter[mode] += 1
        wi_id = wi.get("wi_id", "")
        if wi_id:
            wi_modes[wi_id] = mode

        status = wi.get("status", "other")
        if status not in known_statuses:
            status = "other"
        status_counter[status] += 1

    result["mode_breakdown"] = dict(mode_counter)
    result["status_breakdown"] = dict(status_counter)

    # Per-WI attempt counts from runs/ directories
    runs_dir = feature_dir / "runs"
    total_runs = 0
    per_wi: list[dict] = []
    if runs_dir.is_dir():
        for wi_dir in runs_dir.iterdir():
            if wi_dir.is_dir():
                run_count = sum(1 for r in wi_dir.iterdir() if r.is_dir() and r.name.startswith("RUN-"))
                total_runs += run_count
                if run_count > 0:
                    per_wi.append({
                        "wi_id": wi_dir.name,
                        "attempts": run_count,
                        "mode": wi_modes.get(wi_dir.name, "unknown"),
                    })

    per_wi.sort(key=lambda x: x["attempts"], reverse=True)
    result["per_wi_attempts"] = per_wi

    if result["total"] > 0:
        result["avg_attempts"] = round(total_runs / result["total"], 1)

    return result


def _collect_test_stats(feature_dir: Path) -> dict:
    """Collect test statistics from tests/scenarios.yaml and spec.md."""
    result = {
        "scenario_count": 0,
        "ac_total": 0,
        "ac_covered": 0,
        "ac_coverage_pct": 0.0,
    }

    # Count ACs from spec.md
    spec_data = _parse_canonical_yaml(feature_dir / "spec.md", "Canonical Spec")
    if spec_data:
        spec = spec_data.get("spec", {})
        for uc in spec.get("use_cases", []) or []:
            result["ac_total"] += len(uc.get("acceptance", []) or [])

    # Parse scenarios.yaml
    scenarios_path = feature_dir / "tests" / "scenarios.yaml"
    if scenarios_path.is_file() and yaml:
        try:
            sdata = yaml.safe_load(scenarios_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            sdata = None

        if sdata:
            scenarios = sdata.get("scenarios", [])
            result["scenario_count"] = len(scenarios)

            # Collect covered ACs
            covered_acs = set()
            for sc in scenarios:
                covers = sc.get("covers_ac", [])
                if isinstance(covers, list):
                    for ac_id in covers:
                        covered_acs.add(str(ac_id))
                elif covers:
                    covered_acs.add(str(covers))

            result["ac_covered"] = len(covered_acs)

    if result["ac_total"] > 0:
        result["ac_coverage_pct"] = round(result["ac_covered"] / result["ac_total"] * 100, 1)

    return result


def _collect_lessons(feature_dir: Path) -> dict:
    """Collect lesson counts from runs/**/. planning/lessons.md."""
    result = {
        "total": 0,
        "categories": {},
    }

    # Search for lessons.md files
    category_pattern = re.compile(r"^##\s*(Best Practices?|Troubles?|Technical Knowledge|Reusable Patterns?)", re.IGNORECASE)

    for lessons_path in feature_dir.rglob("lessons.md"):
        if ".planning" not in str(lessons_path):
            continue

        content = _read_file_text(lessons_path)
        if not content:
            continue

        current_category = None
        for line in content.splitlines():
            cat_match = category_pattern.match(line)
            if cat_match:
                # Normalize category name
                raw = cat_match.group(1).lower().rstrip("s")
                if "best" in raw:
                    current_category = "best_practice"
                elif "trouble" in raw:
                    current_category = "trouble"
                elif "technical" in raw:
                    current_category = "technical"
                elif "reusable" in raw or "pattern" in raw:
                    current_category = "reusable_pattern"
                else:
                    current_category = raw
                continue
            if current_category and line.strip().startswith("- "):
                result["total"] += 1
                result["categories"][current_category] = result["categories"].get(current_category, 0) + 1

    return result


def _collect_change_events(feature_dir: Path) -> int:
    """Count change log entries from implementation-details/change_log.md."""
    changelog_path = feature_dir / "implementation-details" / "change_log.md"
    if not changelog_path.is_file():
        return 0

    content = _read_file_text(changelog_path)
    # Count entries (lines starting with '- ' or '| ' in table format, after header)
    entries = 0
    in_log = False
    for line in content.splitlines():
        if re.match(r"^#+\s", line):
            in_log = True
            continue
        if in_log and (line.strip().startswith("- ") or re.match(r"^\|\s*\d", line)):
            entries += 1

    return entries


# ---------------------------------------------------------------------------
# Feature-level retro
# ---------------------------------------------------------------------------

def generate_feature_retro(feature_dir: Path) -> dict:
    """Generate a retrospective report for a single feature."""
    feature_dir = Path(feature_dir)

    # Phase durations
    gate_dates = _parse_approval_dates(feature_dir / "APPROVAL.md")
    phase_durations = _compute_phase_durations(gate_dates)

    # WI stats
    wi_stats = _collect_wi_stats(feature_dir)

    # Test stats
    test_stats = _collect_test_stats(feature_dir)

    # Lessons
    lessons = _collect_lessons(feature_dir)

    # Change events
    change_entries = _collect_change_events(feature_dir)

    # Insights
    insights = _generate_insights(phase_durations, wi_stats)

    return {
        "target": str(feature_dir),
        "kind": "feature",
        "phase_durations": phase_durations,
        "gate_dates": gate_dates,
        "wi_stats": wi_stats,
        "test_stats": test_stats,
        "lessons": lessons,
        "change_entries": change_entries,
        "insights": insights,
    }


def _duration_to_hours(s: str) -> float:
    """Convert a formatted duration string like '10d 4h' to total hours."""
    if s == "N/A":
        return -1.0
    total = 0.0
    m_days = re.search(r"(\d+)d", s)
    m_hours = re.search(r"(\d+)h", s)
    if m_days:
        total += int(m_days.group(1)) * 24
    if m_hours:
        total += int(m_hours.group(1))
    return total


def _generate_insights(phase_durations: dict, wi_stats: dict) -> list[str]:
    """Generate human-readable insights from metrics."""
    insights = []

    # Bottleneck phase — compare by numeric hours, not string
    phase_names = {
        "design_to_specify": "Design -> Specify",
        "specify_to_tasking": "Specify -> Tasking",
        "tasking_to_execute": "Tasking -> Execute",
    }
    longest_phase = None
    longest_hours = -1.0
    longest_label_str = ""
    for key, label in phase_names.items():
        val = phase_durations.get(key, "N/A")
        hours = _duration_to_hours(val)
        if hours > longest_hours:
            longest_hours = hours
            longest_phase = label
            longest_label_str = val
    if longest_phase and longest_hours > 0:
        insights.append(f"Bottleneck phase: {longest_phase} ({longest_label_str})")

    # Highest retry WI — identify the specific WI with most attempts
    per_wi = wi_stats.get("per_wi_attempts", [])
    if per_wi:
        top = per_wi[0]  # already sorted desc by attempts
        if top["attempts"] > 1:
            insights.append(
                f"Highest retry WI: {top['wi_id']} ({top['attempts']} attempts, mode: {top['mode']})"
            )
            if top["mode"] == "validate":
                insights.append(
                    "Recommendation: validate mode の WI が retry 多 → 事前 design_diff / authz review 強化を検討"
                )

    return insights


def _generate_epic_insights(feature_retros: list[dict]) -> list[str]:
    """Generate epic-level cross-feature insights."""
    insights = []
    if not feature_retros:
        return insights

    # Longest phase across all features
    longest_phase = None
    longest_hours = -1.0
    longest_feature = ""
    longest_label = ""
    phase_keys = {
        "design_to_specify": "Design -> Specify",
        "specify_to_tasking": "Specify -> Tasking",
        "tasking_to_execute": "Tasking -> Execute",
    }
    for fr in feature_retros:
        pd = fr.get("phase_durations", {})
        for key, label in phase_keys.items():
            val = pd.get(key, "N/A")
            hours = _duration_to_hours(val)
            if hours > longest_hours:
                longest_hours = hours
                longest_phase = label
                longest_label = val
                longest_feature = fr.get("target", "")
    if longest_phase and longest_hours > 0:
        insights.append(f"Longest phase: {longest_phase} ({longest_label}) in {Path(longest_feature).name}")

    # Highest retry WI across all features — find the specific WI
    top_wi = None
    top_feature = ""
    for fr in feature_retros:
        per_wi = fr.get("wi_stats", {}).get("per_wi_attempts", [])
        if per_wi and per_wi[0]["attempts"] > (top_wi["attempts"] if top_wi else 0):
            top_wi = per_wi[0]
            top_feature = fr.get("target", "")
    if top_wi and top_wi["attempts"] > 1:
        insights.append(
            f"Highest retry WI: {top_wi['wi_id']} ({top_wi['attempts']} attempts, mode: {top_wi['mode']}) in {Path(top_feature).name}"
        )

    return insights


# ---------------------------------------------------------------------------
# Epic-level retro
# ---------------------------------------------------------------------------

def generate_epic_retro(epic_dir: Path) -> dict:
    """Generate a retrospective report for an epic by aggregating features."""
    epic_dir = Path(epic_dir)

    # Parse epic_design.md to get feature list
    epic_data = _parse_canonical_yaml(epic_dir / "epic_design.md", "Canonical Epic Design")
    feature_ids = []
    if epic_data:
        features = epic_data.get("epic", {}).get("features", [])
        for f in (features or []):
            fid = f.get("feature_id") if isinstance(f, dict) else str(f)
            if fid:
                feature_ids.append(fid)

    # Resolve feature directories (relative to epic's grandparent)
    project_root = epic_dir.parent.parent  # epics/EPIC-X/ -> project root
    feature_retros = []
    for fid in feature_ids:
        fdir = project_root / "specs" / fid
        if fdir.is_dir():
            feature_retros.append(generate_feature_retro(fdir))

    # Aggregate
    total_wis = sum(r["wi_stats"]["total"] for r in feature_retros)
    total_scenarios = sum(r["test_stats"]["scenario_count"] for r in feature_retros)
    total_ac = sum(r["test_stats"]["ac_total"] for r in feature_retros)
    total_ac_covered = sum(r["test_stats"]["ac_covered"] for r in feature_retros)
    total_lessons = sum(r["lessons"]["total"] for r in feature_retros)
    total_changes = sum(r["change_entries"] for r in feature_retros)

    ac_coverage = round(total_ac_covered / max(total_ac, 1) * 100, 1)

    # Epic-level insights
    epic_insights = _generate_epic_insights(feature_retros)

    return {
        "target": str(epic_dir),
        "kind": "epic",
        "feature_count": len(feature_retros),
        "feature_ids": feature_ids,
        "aggregate": {
            "total_wis": total_wis,
            "total_scenarios": total_scenarios,
            "ac_total": total_ac,
            "ac_covered": total_ac_covered,
            "ac_coverage_pct": ac_coverage,
            "total_lessons": total_lessons,
            "total_changes": total_changes,
        },
        "insights": epic_insights,
        "features": feature_retros,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_feature_report(retro: dict) -> str:
    """Format a feature retro for terminal output."""
    lines = []
    lines.append(f"=== STRIDE Retro: {retro['target']} ===")
    lines.append("")

    # Phase Durations
    pd = retro["phase_durations"]
    lines.append("Phase Durations")
    lines.append(f"  Design  -> Specify:  {pd['design_to_specify']}")
    lines.append(f"  Specify -> Tasking:  {pd['specify_to_tasking']}")
    lines.append(f"  Tasking -> Execute:  {pd['tasking_to_execute']}")
    lines.append(f"  Total lead time:     {pd['total_lead_time']}")
    lines.append("")

    # Work Items
    ws = retro["wi_stats"]
    mode_parts = " | ".join(f"{k}: {v}" for k, v in ws["mode_breakdown"].items())
    status_parts = " | ".join(
        f"{k.replace('_', ' ').title()}: {v}" for k, v in ws["status_breakdown"].items()
    )
    lines.append("Work Items")
    lines.append(f"  Total: {ws['total']} | {mode_parts}")
    lines.append(f"  {status_parts}")
    lines.append(f"  Avg attempts/WI: {ws['avg_attempts']}")
    lines.append("")

    # Tests
    ts = retro["test_stats"]
    lines.append("Tests")
    lines.append(f"  Scenarios: {ts['scenario_count']} | ACs covered: {ts['ac_covered']}/{ts['ac_total']} ({ts['ac_coverage_pct']}%)")
    lines.append("")

    # Lessons
    ls = retro["lessons"]
    cat_parts = ", ".join(f"{k}: {v}" for k, v in ls["categories"].items())
    cat_str = f" ({cat_parts})" if cat_parts else ""
    lines.append("Lessons")
    lines.append(f"  Captured: {ls['total']}{cat_str}")
    lines.append("")

    # Spec Changes
    lines.append("Spec Changes")
    lines.append(f"  Change log entries: {retro['change_entries']}")
    lines.append("")

    # Insights
    if retro["insights"]:
        lines.append("Insights")
        for insight in retro["insights"]:
            lines.append(f"  - {insight}")

    return "\n".join(lines)


def format_epic_report(retro: dict) -> str:
    """Format an epic retro for terminal output."""
    lines = []
    lines.append(f"=== STRIDE Retro (Epic): {retro['target']} ===")
    lines.append(f"Features: {retro['feature_count']} ({', '.join(retro['feature_ids'])})")
    lines.append("")

    agg = retro["aggregate"]
    lines.append("Aggregate")
    lines.append(f"  Total WIs: {agg['total_wis']}")
    lines.append(f"  Total scenarios: {agg['total_scenarios']}")
    lines.append(f"  AC coverage: {agg['ac_covered']}/{agg['ac_total']} ({agg['ac_coverage_pct']}%)")
    lines.append(f"  Total lessons: {agg['total_lessons']}")
    lines.append(f"  Total change entries: {agg['total_changes']}")
    lines.append("")

    # Epic-level insights
    epic_insights = retro.get("insights", [])
    if epic_insights:
        lines.append("Insights")
        for insight in epic_insights:
            lines.append(f"  - {insight}")
        lines.append("")

    for fr in retro["features"]:
        lines.append(f"--- Feature: {fr['target']} ---")
        lines.append(format_feature_report(fr))
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Retrospective Report Generator - Quantitative feature/epic retrospective",
    )
    parser.add_argument("target", nargs="?", help="Feature or Epic directory path")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    # v6.0 Phase C: BABOK KA8 solution evaluation extension
    parser.add_argument(
        "--solution-eval",
        action="store_true",
        dest="solution_eval",
        help="Run BABOK KA8 solution evaluation (post-deployment KPI/Adoption/Issues)",
    )
    parser.add_argument(
        "--kpi-source",
        type=Path,
        default=None,
        dest="kpi_source",
        help="Path to actual KPI YAML (used with --solution-eval)",
    )
    parser.add_argument(
        "--adoption-survey",
        type=Path,
        default=None,
        dest="adoption_survey",
        help="Path to adoption survey YAML (used with --solution-eval)",
    )
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.target:
        parser.error("target is required (or use --test)")

    target = Path(args.target)
    if not target.is_dir():
        print(f"Error: '{args.target}' is not a directory", file=sys.stderr)
        sys.exit(2)

    # v6.0 Phase C: --solution-eval 分岐 (BABOK KA8)
    if args.solution_eval:
        # solution_evaluator.py を遅延 import (循環参照回避)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from solution_evaluator import evaluate_solution, format_solution_report

        try:
            result = evaluate_solution(target, args.kpi_source, args.adoption_survey)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            # yaml.YAMLError 等 (パース失敗) を含む。yaml import 失敗環境では Exception で catch.
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)

        if args.json:
            # report_markdown は重複するので JSON では除外
            payload = {k: v for k, v in result.items() if k != "report_markdown"}
            print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        else:
            print(format_solution_report(result))

        sys.exit(0 if result["overall_pass"] else 1)

    # Detect if target is an epic or feature
    is_epic = (target / "epic_design.md").is_file()

    if is_epic:
        retro = generate_epic_retro(target)
        if args.json:
            print(json.dumps(retro, indent=2, ensure_ascii=False))
        else:
            print(format_epic_report(retro))
    else:
        retro = generate_feature_retro(target)
        if args.json:
            print(json.dumps(retro, indent=2, ensure_ascii=False))
        else:
            print(format_feature_report(retro))


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Run self-tests using temporary directories."""
    print("Running stride_retro.py self-tests...")
    passed = 0
    total = 0

    def test(name, func):
        nonlocal passed, total
        total += 1
        try:
            func()
            print(f"  Test {total} passed: {name}")
            passed += 1
        except AssertionError as e:
            print(f"  Test {total} FAILED: {name} -- {e}")

    # Test 1: APPROVAL.md parsing with 日付:
    def test_approval_ja():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "APPROVAL.md").write_text(
                "## Gate 1: Basic Design\n承認者: テスト太郎\n日付: 2026-01-10\n\n"
                "## Gate 3: Spec\n承認者: テスト太郎\n日付: 2026-01-15\n\n"
                "## Final: Implementation\n承認者: テスト太郎\n日付: 2026-01-25\n"
            )
            dates = _parse_approval_dates(p / "APPROVAL.md")
            assert "Gate 1" in dates, f"Gate 1 not found in {dates}"
            assert dates["Gate 1"] == "2026-01-10"
            assert "Gate 3" in dates
            assert "Final" in dates

    test("APPROVAL.md parsing with 日付:", test_approval_ja)

    # Test 2: APPROVAL.md parsing with Date: (backward compat)
    def test_approval_en():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "APPROVAL.md").write_text(
                "## Gate 1: Basic Design\nApprover: Test\nDate: 2026-02-01\n\n"
                "## Gate 5: Tasks\nApprover: Test\nDate: 2026-02-10\n"
            )
            dates = _parse_approval_dates(p / "APPROVAL.md")
            assert "Gate 1" in dates, f"Gate 1 not found in {dates}"
            assert dates["Gate 1"] == "2026-02-01"
            assert "Gate 5" in dates

    test("APPROVAL.md parsing with Date: (backward compat)", test_approval_en)

    # Test 3: WI statistics from state.yaml
    def test_wi_stats():
        if yaml is None:
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            state_dir = p / "state"
            state_dir.mkdir()
            (state_dir / "state.yaml").write_text(yaml.dump({
                "work_items": [
                    {"wi_id": "WI-001", "status": "done", "mode": "autopilot"},
                    {"wi_id": "WI-002", "status": "done", "mode": "autopilot"},
                    {"wi_id": "WI-003", "status": "pending", "mode": "validate"},
                    {"wi_id": "WI-004", "status": "in_progress", "mode": "confirm"},
                ],
            }))
            stats = _collect_wi_stats(p)
            assert stats["total"] == 4, f"expected 4 WIs, got {stats['total']}"
            assert stats["mode_breakdown"]["autopilot"] == 2
            assert stats["status_breakdown"]["done"] == 2
            assert stats["status_breakdown"]["pending"] == 1

    test("WI statistics from state.yaml", test_wi_stats)

    # Test 4: Lessons count from .planning/lessons.md
    def test_lessons():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            lessons_dir = p / "runs" / "WI-001" / "RUN-001" / ".planning"
            lessons_dir.mkdir(parents=True)
            (lessons_dir / "lessons.md").write_text(
                "## Best Practices\n- Always validate input\n- Use retry pattern\n\n"
                "## Troubles\n- API timeout issue\n\n"
                "## Technical Knowledge\n- mcframe uses correlation ID\n"
            )
            ls = _collect_lessons(p)
            assert ls["total"] == 4, f"expected 4 lessons, got {ls['total']}"
            assert ls["categories"].get("best_practice") == 2
            assert ls["categories"].get("trouble") == 1
            assert ls["categories"].get("technical") == 1

    test("Lessons count from .planning/lessons.md", test_lessons)

    # Test 5: Epic-level cross-feature aggregation
    def test_epic_retro():
        if yaml is None:
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)

            # Create epic with features list
            epic_dir = p / "epics" / "EPIC-TEST"
            epic_dir.mkdir(parents=True)
            (epic_dir / "epic_design.md").write_text(
                "# 0. Canonical Epic Design (YAML)\n```yaml\nepic:\n  features:\n    - feature_id: FEAT-A\n    - feature_id: FEAT-B\n```\n"
            )

            # Create features
            for fid in ("FEAT-A", "FEAT-B"):
                fdir = p / "specs" / fid
                state_dir = fdir / "state"
                state_dir.mkdir(parents=True)
                (state_dir / "state.yaml").write_text(yaml.dump({
                    "work_items": [
                        {"wi_id": f"WI-{fid}-001", "status": "done", "mode": "autopilot"},
                    ],
                }))
                (fdir / "APPROVAL.md").write_text(
                    "## Gate 1: Design\n日付: 2026-01-01\n"
                )

            retro = generate_epic_retro(epic_dir)
            assert retro["kind"] == "epic"
            assert retro["feature_count"] == 2
            assert retro["aggregate"]["total_wis"] == 2

    test("Epic cross-feature aggregation via epic_design.md", test_epic_retro)

    # Test 6: JSON output structure
    def test_json_structure():
        if yaml is None:
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "APPROVAL.md").write_text("## Gate 1\n日付: 2026-03-01\n")
            state_dir = p / "state"
            state_dir.mkdir()
            (state_dir / "state.yaml").write_text(yaml.dump({
                "work_items": [{"wi_id": "WI-001", "status": "done", "mode": "autopilot"}],
            }))

            retro = generate_feature_retro(p)
            json_str = json.dumps(retro, ensure_ascii=False)
            parsed = json.loads(json_str)

            # Verify required keys
            for key in ("target", "kind", "phase_durations", "wi_stats", "test_stats", "lessons", "insights"):
                assert key in parsed, f"missing key '{key}' in JSON output"

    test("JSON output structure validation", test_json_structure)

    print(f"\nAll {passed}/{total} self-tests passed." if passed == total else f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    main()
