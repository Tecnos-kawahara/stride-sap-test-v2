#!/usr/bin/env python3
"""
STRIDE Process Metrics — Gate別滞留時間分析・遅延リスク検知

プロセスタイム分析（工程別滞留時間・遅延リスク検知）機能を提供。
APPROVAL.md の Gate 承認日時差分から工程別滞留日数を計算し、
WI 単位の遅延リスクを自動検知する。

Usage:
    python scripts/stride_process_metrics.py --feature specs/sample_erp_addon --output table
    python scripts/stride_process_metrics.py --epic epics/EPIC-SAMPLE --output json
    python scripts/stride_process_metrics.py --feature specs/sample_erp_addon --update-dashboard
    python scripts/stride_process_metrics.py --feature specs/sample_erp_addon --dry-run --verbose
    python scripts/stride_process_metrics.py --test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# Constants
# =============================================================================

GATE_KEYS = [
    "gate1_design", "gate2_bpmn", "gate3_spec",
    "gate4_plan", "gate5_tasks", "evidence",
]

GATE_DISPLAY = {
    "gate1_design": "Gate 1: Design Review",
    "gate2_bpmn": "Gate 2: BPMN Review",
    "gate3_spec": "Gate 3: Spec Review",
    "gate4_plan": "Gate 4: Plan Review",
    "gate5_tasks": "Gate 5: Tasks Review",
    "evidence": "Evidence Review",
}

APPROVAL_GATE_MAP = {
    "Gate 1": "gate1_design",
    "Gate 2": "gate2_bpmn",
    "Gate 3": "gate3_spec",
    "Gate 4": "gate4_plan",
    "Gate 5": "gate5_tasks",
    "Final": "evidence",
}

# Delay risk thresholds (days): overdue boundary by complexity
OVERDUE_THRESHOLDS = {"low": 3, "medium": 5, "high": 7}
AT_RISK_FACTOR = 0.5  # at_risk = overdue * AT_RISK_FACTOR

# Inject rate thresholds (%)
INJECT_RATE_THRESHOLDS = {"good": 20, "warn": 50}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GateProcessTime:
    start: Optional[str] = None
    end: Optional[str] = None
    days: Optional[int] = None


@dataclass
class WIMetrics:
    wi_id: str = ""
    complexity: str = "medium"
    current_gate: str = ""
    current_gate_age_days: Optional[int] = None
    delay_risk: str = "on_track"


@dataclass
class InjectRateEntry:
    wi_id: str = ""
    initial_tasks: int = 0
    current_tasks: int = 0
    inject_rate_pct: float = 0.0


@dataclass
class FeatureMetrics:
    feature: str = ""
    gate_process_times: Dict[str, GateProcessTime] = field(default_factory=dict)
    total_days: int = 0
    current_gate: str = ""
    current_gate_age_days: Optional[int] = None
    wi_metrics: List[WIMetrics] = field(default_factory=list)
    inject_rates: List[InjectRateEntry] = field(default_factory=list)


# =============================================================================
# Helpers
# =============================================================================

def _load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_yaml_from_md(md_path: Path) -> Optional[dict]:
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


def _find_project_root(start: Path) -> Path:
    current = start.resolve()
    for _ in range(5):
        if (current / "memory").exists() or (current / "sdd-templates").exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return start.resolve().parent.parent


# =============================================================================
# Core: APPROVAL.md Gate Date Parsing
# =============================================================================

def parse_approval_dates(approval_path: Path) -> Dict[str, Optional[str]]:
    """APPROVAL.md から各 Gate の承認日付を抽出する。

    Returns:
        gate_key -> date_str (YYYY-MM-DD) or None if not approved
    """
    dates: Dict[str, Optional[str]] = {k: None for k in GATE_KEYS}

    if not approval_path.exists():
        return dates

    content = _read_text(approval_path)
    sections = re.split(r'(?=## (?:Gate \d|Final))', content)

    for section in sections:
        gate_key = None
        for header, key in APPROVAL_GATE_MAP.items():
            if re.match(rf'## {re.escape(header)}\b', section):
                gate_key = key
                break

        if gate_key is None:
            continue

        has_checked = bool(re.search(r'\[x\]', section, re.IGNORECASE))
        has_approver = bool(re.search(
            r'(?:承認者|Approver):\s*([^\s_][^\n]*)', section, re.IGNORECASE,
        ))
        date_match = re.search(r'(?:日付|Date):\s*(\d{4}-\d{2}-\d{2})', section)

        if has_checked and has_approver and date_match:
            dates[gate_key] = date_match.group(1)

    return dates


# =============================================================================
# Core: Process Time Computation
# =============================================================================

def compute_gate_process_times(
    gate_dates: Dict[str, Optional[str]],
) -> Dict[str, GateProcessTime]:
    """Gate 承認日付から工程別滞留日数を計算する。

    Each gate's process time:
    - start = previous gate's approval date (Gate 1: own date)
    - end = this gate's approval date (None if not approved)
    - days = (end - start).days (None if either is missing)
    """
    result: Dict[str, GateProcessTime] = {}
    prev_date: Optional[str] = None

    for key in GATE_KEYS:
        gate_date = gate_dates.get(key)
        pt = GateProcessTime()

        if key == GATE_KEYS[0]:
            pt.start = gate_date  # Gate 1: start = own date
        else:
            pt.start = prev_date

        if gate_date:
            pt.end = gate_date
            if pt.start:
                try:
                    d_start = date.fromisoformat(pt.start)
                    d_end = date.fromisoformat(pt.end)
                    pt.days = (d_end - d_start).days
                except ValueError:
                    pass
            prev_date = gate_date
        else:
            pt.end = None
            pt.days = None

        result[key] = pt

    return result


def determine_current_gate(gate_dates: Dict[str, Optional[str]]) -> str:
    """未承認の最初の Gate を返す。全承認済みなら 'completed'。"""
    for key in GATE_KEYS:
        if gate_dates.get(key) is None:
            return key
    return "completed"


def compute_current_gate_age(
    gate_dates: Dict[str, Optional[str]],
    current_gate: str,
    today: Optional[date] = None,
) -> Optional[int]:
    """現在 Gate での滞留日数を計算する。"""
    if today is None:
        today = date.today()

    if current_gate == "completed":
        return 0

    idx = GATE_KEYS.index(current_gate) if current_gate in GATE_KEYS else -1
    if idx < 0:
        return None

    if idx == 0:
        return None

    prev_key = GATE_KEYS[idx - 1]
    prev_date_str = gate_dates.get(prev_key)
    if not prev_date_str:
        return None

    try:
        return (today - date.fromisoformat(prev_date_str)).days
    except ValueError:
        return None


def assess_delay_risk(age: Optional[int], complexity: str) -> str:
    """遅延リスクを判定する。"""
    if age is None or age < 0:
        return "on_track"

    overdue = OVERDUE_THRESHOLDS.get(complexity, 5)
    at_risk = overdue * AT_RISK_FACTOR

    if age >= overdue:
        return "overdue"
    elif age >= at_risk:
        return "at_risk"
    return "on_track"


# =============================================================================
# Core: Inject Rate
# =============================================================================

def compute_inject_rates(
    state: dict,
    feature_dir: Path,
) -> List[InjectRateEntry]:
    """差し込み率を計算する。

    initial_tasks: tasks.md の tasks_gate_check.counts.tasks (Gate 5 承認時ロック値)
    current_tasks: tasks.md YAML の実際の tasks 配列長
    """
    tasks_path = feature_dir / "tasks.md"
    tasks_data = _extract_yaml_from_md(tasks_path)
    if not tasks_data:
        return []

    gate_check = tasks_data.get("tasks_gate_check", {})
    initial_total = gate_check.get("counts", {}).get("tasks", 0)

    tasks_obj = tasks_data.get("tasks", {})
    task_list = tasks_obj.get("tasks", []) if isinstance(tasks_obj, dict) else []
    current_total = len(task_list)

    work_items = state.get("work_items", [])
    results: List[InjectRateEntry] = []
    valid_wis = [w for w in work_items if isinstance(w, dict) and w.get("wi_id")]
    wi_count = len(valid_wis)

    if wi_count == 0:
        return results

    init_per_wi = initial_total // wi_count if wi_count > 0 else 0
    curr_per_wi = current_total // wi_count if wi_count > 0 else 0
    remainder_init = initial_total - init_per_wi * wi_count
    remainder_curr = current_total - curr_per_wi * wi_count

    for i, wi in enumerate(valid_wis):
        init_n = init_per_wi + (1 if i < remainder_init else 0)
        curr_n = curr_per_wi + (1 if i < remainder_curr else 0)
        rate = ((curr_n - init_n) / init_n * 100) if init_n > 0 else 0.0
        results.append(InjectRateEntry(
            wi_id=wi["wi_id"],
            initial_tasks=init_n,
            current_tasks=curr_n,
            inject_rate_pct=round(rate, 1),
        ))

    return results


# =============================================================================
# Feature / Epic Analysis
# =============================================================================

def analyze_feature(
    feature_dir: Path,
    today: Optional[date] = None,
    verbose: bool = False,
) -> FeatureMetrics:
    """Feature 単位のプロセスメトリクスを分析する。"""
    if today is None:
        today = date.today()

    feature_name = feature_dir.name
    metrics = FeatureMetrics(feature=feature_name)

    approval_path = feature_dir / "APPROVAL.md"
    gate_dates = parse_approval_dates(approval_path)

    if verbose:
        print(f"  Gate dates: {gate_dates}")

    metrics.gate_process_times = compute_gate_process_times(gate_dates)
    metrics.total_days = sum(
        pt.days for pt in metrics.gate_process_times.values() if pt.days is not None
    )

    metrics.current_gate = determine_current_gate(gate_dates)
    metrics.current_gate_age_days = compute_current_gate_age(
        gate_dates, metrics.current_gate, today,
    )

    state = _load_yaml(feature_dir / "state" / "state.yaml")
    work_items = state.get("work_items", [])

    for wi in work_items:
        if not isinstance(wi, dict) or not wi.get("wi_id"):
            continue

        wi_id = wi["wi_id"]
        complexity = wi.get("complexity", "medium")
        age = metrics.current_gate_age_days
        risk = assess_delay_risk(age, complexity)

        metrics.wi_metrics.append(WIMetrics(
            wi_id=wi_id,
            complexity=complexity,
            current_gate=metrics.current_gate,
            current_gate_age_days=age,
            delay_risk=risk,
        ))

    metrics.inject_rates = compute_inject_rates(state, feature_dir)

    return metrics


def analyze_epic(
    epic_dir: Path,
    today: Optional[date] = None,
    verbose: bool = False,
) -> List[FeatureMetrics]:
    """Epic 配下の全 Feature を分析する。"""
    epic_path = Path(epic_dir).resolve()
    project_root = _find_project_root(epic_path)
    specs_dir = project_root / "specs"

    epic_data = _extract_yaml_from_md(epic_path / "epic_design.md")
    if not epic_data or "epic" not in epic_data:
        print(f"ERROR: Cannot parse epic_design.md in {epic_path}", file=sys.stderr)
        return []

    features = epic_data["epic"].get("features", [])
    results: List[FeatureMetrics] = []

    for feat in features:
        fid = feat.get("feature_id", "")
        if not fid:
            continue
        feat_dir = specs_dir / fid
        if not feat_dir.exists():
            if verbose:
                print(f"  SKIP: {fid} (directory not found)")
            continue
        if verbose:
            print(f"  Analyzing: {fid}")
        results.append(analyze_feature(feat_dir, today, verbose))

    return results


# =============================================================================
# Output Formatters
# =============================================================================

def _risk_icon(risk: str) -> str:
    return {"on_track": "\U0001f7e2", "at_risk": "\U0001f7e1", "overdue": "\U0001f534"}.get(risk, "")


def _inject_label(pct: float) -> str:
    if pct <= INJECT_RATE_THRESHOLDS["good"]:
        return "\U0001f7e2 良好"
    elif pct <= INJECT_RATE_THRESHOLDS["warn"]:
        return "\U0001f7e1 注意"
    return "\U0001f534 要改善"


def format_json(metrics_list: List[FeatureMetrics]) -> str:
    """JSON 形式で出力する。"""
    output = []
    for m in metrics_list:
        for wi in m.wi_metrics:
            entry = {
                "feature": m.feature,
                "wi_id": wi.wi_id,
                "gate_process_times": {
                    k: {"start": pt.start, "end": pt.end, "days": pt.days}
                    for k, pt in m.gate_process_times.items()
                },
                "total_days": m.total_days,
                "current_gate": wi.current_gate,
                "current_gate_age_days": wi.current_gate_age_days,
                "delay_risk": wi.delay_risk,
            }
            output.append(entry)
    if len(output) == 1:
        return json.dumps(output[0], indent=2, ensure_ascii=False)
    return json.dumps(output, indent=2, ensure_ascii=False)


def format_table(metrics_list: List[FeatureMetrics]) -> str:
    """テーブル形式（ターミナル表示用）で出力する。"""
    lines: List[str] = []

    for m in metrics_list:
        lines.append(f"\n{'=' * 60}")
        lines.append(f"Feature: {m.feature}")
        lines.append(f"{'=' * 60}")

        lines.append(f"\n{'Gate':<25} {'Start':<12} {'End':<12} {'Days':>5}")
        lines.append("-" * 56)
        for key in GATE_KEYS:
            pt = m.gate_process_times.get(key, GateProcessTime())
            display = GATE_DISPLAY.get(key, key)
            s = pt.start or "-"
            e = pt.end or "-(進行中)"
            d = str(pt.days) if pt.days is not None else "-"
            lines.append(f"{display:<25} {s:<12} {e:<12} {d:>5}")
        lines.append(f"\nTotal Process Days: {m.total_days}")
        current_label = GATE_DISPLAY.get(m.current_gate, m.current_gate)
        age_str = f"{m.current_gate_age_days}d" if m.current_gate_age_days is not None else "-"
        lines.append(f"Current Gate: {current_label} ({age_str} elapsed)")

        if m.wi_metrics:
            lines.append(f"\n{'WI ID':<22} {'Complexity':<10} {'Gate':<12} {'Age':>5} {'Risk':<10}")
            lines.append("-" * 60)
            for wi in m.wi_metrics:
                gate_short = wi.current_gate
                age = f"{wi.current_gate_age_days}d" if wi.current_gate_age_days is not None else "-"
                lines.append(f"{wi.wi_id:<22} {wi.complexity:<10} {gate_short:<12} {age:>5} {wi.delay_risk:<10}")

        if m.inject_rates:
            lines.append(f"\n{'WI ID':<22} {'Initial':>8} {'Current':>8} {'Rate':>8}")
            lines.append("-" * 48)
            for ir in m.inject_rates:
                lines.append(
                    f"{ir.wi_id:<22} {ir.initial_tasks:>8} "
                    f"{ir.current_tasks:>8} {ir.inject_rate_pct:>7.1f}%"
                )

    return "\n".join(lines)


def format_markdown(metrics_list: List[FeatureMetrics]) -> str:
    """PM_DASHBOARD.md 用 Markdown セクションを生成する。"""
    lines: List[str] = []
    today_str = date.today().isoformat()

    lines.append("## Process Metrics")
    lines.append("")
    lines.append(f"> Generated by `stride_process_metrics.py` | Updated: {today_str}")
    lines.append("")

    for m in metrics_list:
        lines.append("### Gate別滞留時間（プロセスタイム分析）")
        lines.append("")
        lines.append("| Gate | 開始 | 完了 | 滞留日数 | 状態 |")
        lines.append("|------|------|------|---------|------|")

        for key in GATE_KEYS:
            pt = m.gate_process_times.get(key, GateProcessTime())
            display = GATE_DISPLAY.get(key, key)
            s = pt.start or "-"
            if pt.end:
                e = pt.end
                d = f"{pt.days}日" if pt.days is not None else "-"
                icon = "\u2705"
            else:
                e = "-(進行中)"
                age = m.current_gate_age_days
                if age is not None:
                    d = f"**{age}日**"
                    risks = [wi.delay_risk for wi in m.wi_metrics]
                    worst = "on_track"
                    for r in risks:
                        if r == "overdue":
                            worst = "overdue"
                            break
                        elif r == "at_risk":
                            worst = "at_risk"
                    icon = {
                        "on_track": "\U0001f7e2 on_track",
                        "at_risk": "\U0001f7e1 at_risk",
                        "overdue": "\U0001f534 overdue",
                    }.get(worst, "")
                else:
                    d = "-"
                    icon = "\u23f3"

            lines.append(f"| {display} | {s} | {e} | {d} | {icon} |")

        age_str = f"{m.current_gate_age_days}日経過" if m.current_gate_age_days is not None else ""
        suffix = f" + 現在{age_str}" if age_str else ""
        lines.append(f"\n**合計プロセスタイム:** {m.total_days}日（完了Gate）{suffix}")
        lines.append("")

        if m.wi_metrics:
            lines.append("### WI別遅延リスクサマリ")
            lines.append("")
            lines.append("| WI ID | Complexity | 現在Gate | 滞留日数 | リスク |")
            lines.append("|-------|-----------|---------|---------|-------|")
            for wi in m.wi_metrics:
                gate_label = GATE_DISPLAY.get(wi.current_gate, wi.current_gate)
                age = f"{wi.current_gate_age_days}日" if wi.current_gate_age_days is not None else "-"
                icon = _risk_icon(wi.delay_risk)
                lines.append(f"| {wi.wi_id} | {wi.complexity} | {gate_label} | {age} | {icon} {wi.delay_risk} |")
            lines.append("")

        if m.inject_rates:
            lines.append("### 差し込み率")
            lines.append("")
            lines.append("| WI ID | 当初タスク数 | 現在タスク数 | 差し込み率 | 評価 |")
            lines.append("|-------|-----------|-----------|---------|------|")
            for ir in m.inject_rates:
                label = _inject_label(ir.inject_rate_pct)
                lines.append(
                    f"| {ir.wi_id} | {ir.initial_tasks} | {ir.current_tasks} "
                    f"| {ir.inject_rate_pct:.1f}% | {label} |"
                )
            lines.append("")

    return "\n".join(lines)


# =============================================================================
# Dashboard Update
# =============================================================================

def find_dashboard_path(feature_dir: Path) -> Optional[Path]:
    """Feature の state.yaml から epic_ref を辿って PM_DASHBOARD.md を探す。"""
    state = _load_yaml(feature_dir / "state" / "state.yaml")
    epic_ref = state.get("epic_ref", "")
    if not epic_ref:
        return None

    project_root = _find_project_root(feature_dir)
    dashboard = project_root / "epics" / epic_ref / "PM_DASHBOARD.md"
    if dashboard.exists():
        return dashboard
    return None


def update_dashboard(
    dashboard_path: Path,
    markdown_content: str,
    dry_run: bool = False,
    verbose: bool = False,
) -> bool:
    """PM_DASHBOARD.md の ## Process Metrics セクションを更新する。

    セクションが存在しない場合は ## Gate Progress の直後に挿入する。
    """
    if not dashboard_path.exists():
        if verbose:
            print(f"  Dashboard not found: {dashboard_path}")
        return False

    content = _read_text(dashboard_path)

    # Replace existing ## Process Metrics section
    section_pattern = re.compile(
        r'(## Process Metrics\n.*?)(?=\n## [^#]|\Z)',
        re.DOTALL,
    )

    if section_pattern.search(content):
        new_content = section_pattern.sub(markdown_content, content)
    else:
        # Insert after ## Gate Progress ... ---
        gate_progress_end = re.search(
            r'(## Gate Progress\n.*?)(\n---\n)',
            content,
            re.DOTALL,
        )
        if gate_progress_end:
            insert_pos = gate_progress_end.end()
            new_content = (
                content[:insert_pos]
                + "\n" + markdown_content + "\n---\n"
                + content[insert_pos:]
            )
        else:
            new_content = content.rstrip() + "\n\n" + markdown_content + "\n"

    if dry_run:
        if verbose:
            print(f"  [DRY RUN] Would update: {dashboard_path}")
            print(f"  Section length: {len(markdown_content)} chars")
        return True

    dashboard_path.write_text(new_content, encoding="utf-8")
    if verbose:
        print(f"  Updated: {dashboard_path}")
    return True


# =============================================================================
# Self-Tests
# =============================================================================

def run_tests() -> bool:
    """Self-tests."""
    import tempfile

    print("Running stride_process_metrics.py self-tests...\n")
    passed = 0
    total = 0

    def check(name: str, condition: bool, msg: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  PASS: {name}")
        else:
            print(f"  FAIL: {name} -- {msg}")

    # Test 1: parse_approval_dates (fully approved)
    print("Test 1: parse_approval_dates (fully approved)")
    with tempfile.TemporaryDirectory() as tmpdir:
        approval = Path(tmpdir) / "APPROVAL.md"
        approval.write_text(
            "# Approval\n\n"
            "## Gate 1: Basic Design\n- [x] complete\n"
            "承認者: Test User\n日付: 2026-01-10\n\n---\n\n"
            "## Gate 2: BPMN\n- [x] complete\n"
            "承認者: Test User\n日付: 2026-01-12\n\n---\n\n"
            "## Gate 3: Spec\n- [x] complete\n"
            "承認者: Test User\n日付: 2026-01-15\n\n---\n\n"
            "## Gate 4: Plan\n- [x] complete\n"
            "承認者: Test User\n日付: 2026-01-18\n\n---\n\n"
            "## Gate 5: Tasks\n- [x] complete\n"
            "承認者: Test User\n日付: 2026-01-20\n\n---\n\n"
            "## Final: Implementation\n- [x] complete\n"
            "承認者: Test User\n日付: 2026-01-25\n"
        )
        dates = parse_approval_dates(approval)
        check("gate1 date", dates["gate1_design"] == "2026-01-10")
        check("gate2 date", dates["gate2_bpmn"] == "2026-01-12")
        check("gate5 date", dates["gate5_tasks"] == "2026-01-20")
        check("evidence date", dates["evidence"] == "2026-01-25")

    # Test 2: parse_approval_dates (partial)
    print("\nTest 2: parse_approval_dates (partial)")
    with tempfile.TemporaryDirectory() as tmpdir:
        approval = Path(tmpdir) / "APPROVAL.md"
        approval.write_text(
            "## Gate 1: Basic Design\n- [x] complete\n"
            "承認者: User\n日付: 2026-01-10\n\n---\n\n"
            "## Gate 2: BPMN\n- [x] complete\n"
            "承認者: User\n日付: 2026-01-12\n\n---\n\n"
            "## Gate 3: Spec\n- [ ] not complete\n"
            "承認者: ___\n\n---\n\n"
            "## Gate 4: Plan\n- [ ] not complete\n"
        )
        dates = parse_approval_dates(approval)
        check("gate1 approved", dates["gate1_design"] == "2026-01-10")
        check("gate2 approved", dates["gate2_bpmn"] == "2026-01-12")
        check("gate3 not approved", dates["gate3_spec"] is None)
        check("gate4 not approved", dates["gate4_plan"] is None)

    # Test 3: compute_gate_process_times
    print("\nTest 3: compute_gate_process_times")
    gate_dates = {
        "gate1_design": "2026-01-10",
        "gate2_bpmn": "2026-01-12",
        "gate3_spec": "2026-01-15",
        "gate4_plan": None,
        "gate5_tasks": None,
        "evidence": None,
    }
    times = compute_gate_process_times(gate_dates)
    check("gate1 days=0", times["gate1_design"].days == 0, f"got {times['gate1_design'].days}")
    check("gate2 days=2", times["gate2_bpmn"].days == 2, f"got {times['gate2_bpmn'].days}")
    check("gate3 days=3", times["gate3_spec"].days == 3, f"got {times['gate3_spec'].days}")
    check("gate4 pending", times["gate4_plan"].end is None)
    check("gate4 start=gate3 end", times["gate4_plan"].start == "2026-01-15")

    # Test 4: determine_current_gate
    print("\nTest 4: determine_current_gate")
    check("partial -> gate4", determine_current_gate(gate_dates) == "gate4_plan")
    all_dates = {k: "2026-01-01" for k in GATE_KEYS}
    check("all approved -> completed", determine_current_gate(all_dates) == "completed")
    none_dates = {k: None for k in GATE_KEYS}
    check("none approved -> gate1", determine_current_gate(none_dates) == "gate1_design")

    # Test 5: compute_current_gate_age
    print("\nTest 5: compute_current_gate_age")
    test_today = date(2026, 1, 25)
    age = compute_current_gate_age(gate_dates, "gate4_plan", test_today)
    check("age=10 days", age == 10, f"got {age}")
    age_completed = compute_current_gate_age(all_dates, "completed", test_today)
    check("completed age=0", age_completed == 0, f"got {age_completed}")
    age_gate1 = compute_current_gate_age(none_dates, "gate1_design", test_today)
    check("gate1 current age=None", age_gate1 is None)

    # Test 6: assess_delay_risk
    print("\nTest 6: assess_delay_risk")
    check("low/1d -> on_track", assess_delay_risk(1, "low") == "on_track")
    check("low/2d -> at_risk", assess_delay_risk(2, "low") == "at_risk")
    check("low/3d -> overdue", assess_delay_risk(3, "low") == "overdue")
    check("medium/2d -> on_track", assess_delay_risk(2, "medium") == "on_track")
    check("medium/3d -> at_risk", assess_delay_risk(3, "medium") == "at_risk")
    check("medium/5d -> overdue", assess_delay_risk(5, "medium") == "overdue")
    check("high/3d -> on_track", assess_delay_risk(3, "high") == "on_track")
    check("high/4d -> at_risk", assess_delay_risk(4, "high") == "at_risk")
    check("high/7d -> overdue", assess_delay_risk(7, "high") == "overdue")
    check("None -> on_track", assess_delay_risk(None, "low") == "on_track")

    # Test 7: analyze_feature (integration)
    print("\nTest 7: analyze_feature (integration)")
    with tempfile.TemporaryDirectory() as tmpdir:
        feat_dir = Path(tmpdir)
        state_dir = feat_dir / "state"
        state_dir.mkdir()

        (feat_dir / "APPROVAL.md").write_text(
            "## Gate 1: Design\n- [x] ok\n承認者: User\n日付: 2026-02-01\n\n---\n\n"
            "## Gate 2: BPMN\n- [x] ok\n承認者: User\n日付: 2026-02-01\n\n---\n\n"
            "## Gate 3: Spec\n- [x] ok\n承認者: User\n日付: 2026-02-03\n\n---\n\n"
            "## Gate 4: Plan\n- [ ] pending\n\n"
            "## Gate 5: Tasks\n- [ ] pending\n\n"
            "## Final: Evidence\n- [ ] pending\n"
        )
        (state_dir / "state.yaml").write_text(
            "feature: FEAT-TEST\ncurrent_gate: Gate4\n"
            "work_items:\n"
            "  - wi_id: WI-TEST-001\n    status: in_progress\n    complexity: medium\n"
            "  - wi_id: WI-TEST-002\n    status: pending\n    complexity: high\n"
        )

        test_today = date(2026, 2, 8)
        m = analyze_feature(feat_dir, today=test_today)
        check("current_gate=gate4_plan", m.current_gate == "gate4_plan")
        check("total_days=2", m.total_days == 2, f"got {m.total_days}")
        check("age=5 days", m.current_gate_age_days == 5, f"got {m.current_gate_age_days}")
        check("2 WI metrics", len(m.wi_metrics) == 2)
        wi1 = next(w for w in m.wi_metrics if w.wi_id == "WI-TEST-001")
        check("WI-001 overdue (medium, 5d)", wi1.delay_risk == "overdue", f"got {wi1.delay_risk}")
        wi2 = next(w for w in m.wi_metrics if w.wi_id == "WI-TEST-002")
        check("WI-002 at_risk (high, 5d)", wi2.delay_risk == "at_risk", f"got {wi2.delay_risk}")

    # Test 8: Output formats
    print("\nTest 8: Output formats")
    with tempfile.TemporaryDirectory() as tmpdir:
        feat_dir = Path(tmpdir)
        (feat_dir / "state").mkdir()
        (feat_dir / "APPROVAL.md").write_text(
            "## Gate 1: Design\n- [x] ok\n承認者: U\n日付: 2026-01-01\n"
            "## Gate 2: BPMN\n- [x] ok\n承認者: U\n日付: 2026-01-02\n"
            "## Gate 3: Spec\n- [ ] pending\n"
            "## Gate 4: Plan\n- [ ] pending\n"
            "## Gate 5: Tasks\n- [ ] pending\n"
            "## Final: Evidence\n- [ ] pending\n"
        )
        (feat_dir / "state" / "state.yaml").write_text(
            "feature: FEAT-FMT\nwork_items:\n"
            "  - wi_id: WI-FMT-001\n    status: in_progress\n    complexity: low\n"
        )
        metrics = [analyze_feature(feat_dir, today=date(2026, 1, 5))]
        json_out = format_json(metrics)
        parsed = json.loads(json_out)
        check("json has feature", parsed.get("feature") is not None)
        check("json has gate_process_times", "gate_process_times" in parsed)

        table_out = format_table(metrics)
        check("table has Gate 1", "Gate 1" in table_out)

        md_out = format_markdown(metrics)
        check("md has ## Process Metrics", "## Process Metrics" in md_out)
        check("md has WI risk table", "WI別遅延リスクサマリ" in md_out)

    # Test 9: update_dashboard
    print("\nTest 9: update_dashboard")
    with tempfile.TemporaryDirectory() as tmpdir:
        dash = Path(tmpdir) / "PM_DASHBOARD.md"
        dash.write_text(
            "# Dashboard\n\n## Gate Progress\n\n| Gate | Status |\n|------|--------|\n| Gate 1 | Done |\n\n---\n\n"
            "## Risk Register\n\n| Risk |\n|------|\n"
        )
        md_section = "## Process Metrics\n\n> Test content\n\n### Gate Table\n| a | b |\n"
        ok = update_dashboard(dash, md_section, dry_run=False)
        check("update returns True", ok)
        new_content = _read_text(dash)
        check("section inserted", "## Process Metrics" in new_content)
        check("Gate Progress preserved", "## Gate Progress" in new_content)
        check("Risk Register preserved", "## Risk Register" in new_content)

        md_section2 = "## Process Metrics\n\n> Updated content\n"
        update_dashboard(dash, md_section2, dry_run=False)
        final = _read_text(dash)
        check("section replaced", "Updated content" in final)
        check("old content gone", "Test content" not in final)

    # Test 10: dry run
    print("\nTest 10: dry run mode")
    with tempfile.TemporaryDirectory() as tmpdir:
        dash = Path(tmpdir) / "PM_DASHBOARD.md"
        dash.write_text("## Gate Progress\n\n---\n\n## End\n")
        original = _read_text(dash)
        update_dashboard(dash, "## Process Metrics\n\nDry run\n", dry_run=True)
        check("file unchanged after dry run", _read_text(dash) == original)

    # Test 11: inject rate
    print("\nTest 11: compute_inject_rates")
    with tempfile.TemporaryDirectory() as tmpdir:
        feat_dir = Path(tmpdir)
        (feat_dir / "tasks.md").write_text(
            "# Tasks\n\n```yaml\ntasks_gate_check:\n  counts:\n    tasks: 10\n\n"
            "tasks:\n  tasks:\n"
            + "".join(f"    - id: T-{i:03d}\n" for i in range(1, 13))
            + "```\n"
        )
        state = {
            "work_items": [
                {"wi_id": "WI-A", "status": "done"},
                {"wi_id": "WI-B", "status": "pending"},
            ],
        }
        rates = compute_inject_rates(state, feat_dir)
        check("2 inject rate entries", len(rates) == 2)
        total_init = sum(r.initial_tasks for r in rates)
        total_curr = sum(r.current_tasks for r in rates)
        check("initial total=10", total_init == 10, f"got {total_init}")
        check("current total=12", total_curr == 12, f"got {total_curr}")
        check("inject rate > 0", any(r.inject_rate_pct > 0 for r in rates))

    # Summary
    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed")
    if passed == total:
        print("All self-tests passed.")
    else:
        print(f"FAILED: {total - passed} test(s) failed.")
    return passed == total


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="STRIDE Process Metrics -- Gate別滞留時間分析・遅延リスク検知",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "\nExamples:\n"
            "    python scripts/stride_process_metrics.py --feature specs/sample_erp_addon --output table\n"
            "    python scripts/stride_process_metrics.py --epic epics/EPIC-SAMPLE --output json\n"
            "    python scripts/stride_process_metrics.py --feature specs/sample_erp_addon --update-dashboard\n"
            "    python scripts/stride_process_metrics.py --test\n"
        ),
    )
    parser.add_argument("--feature", type=Path, help="Feature directory (e.g., specs/sample_erp_addon)")
    parser.add_argument("--epic", type=Path, help="Epic directory (e.g., epics/EPIC-SAMPLE)")
    parser.add_argument("--output", choices=["json", "table", "markdown"], default="table",
                        help="Output format (default: table)")
    parser.add_argument("--update-dashboard", action="store_true",
                        help="Update PM_DASHBOARD.md with Process Metrics section")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show changes without applying")
    parser.add_argument("--verbose", action="store_true",
                        help="Verbose output for debugging")
    parser.add_argument("--test", action="store_true",
                        help="Run self-tests")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.feature and not args.epic:
        parser.print_help()
        sys.exit(1)

    metrics_list: List[FeatureMetrics] = []

    if args.feature:
        if not args.feature.exists():
            print(f"ERROR: Directory not found: {args.feature}", file=sys.stderr)
            sys.exit(1)
        if args.verbose:
            print(f"Analyzing feature: {args.feature}")
        metrics_list.append(analyze_feature(args.feature, verbose=args.verbose))

    elif args.epic:
        if not args.epic.exists():
            print(f"ERROR: Directory not found: {args.epic}", file=sys.stderr)
            sys.exit(1)
        if args.verbose:
            print(f"Analyzing epic: {args.epic}")
        metrics_list = analyze_epic(args.epic, verbose=args.verbose)

    if not metrics_list:
        print("No metrics computed.", file=sys.stderr)
        sys.exit(1)

    if args.output == "json":
        print(format_json(metrics_list))
    elif args.output == "table":
        print(format_table(metrics_list))
    elif args.output == "markdown":
        print(format_markdown(metrics_list))

    if args.update_dashboard:
        md_content = format_markdown(metrics_list)
        if args.feature:
            dashboard_path = find_dashboard_path(args.feature)
        elif args.epic:
            dashboard_path = args.epic / "PM_DASHBOARD.md"
        else:
            dashboard_path = None

        if dashboard_path:
            ok = update_dashboard(
                dashboard_path, md_content,
                dry_run=args.dry_run, verbose=args.verbose,
            )
            if ok:
                mode = "[DRY RUN] " if args.dry_run else ""
                print(f"\n{mode}Dashboard updated: {dashboard_path}")
            else:
                print(f"\nFailed to update dashboard: {dashboard_path}", file=sys.stderr)
        else:
            print("\nWARNING: Could not find PM_DASHBOARD.md", file=sys.stderr)


if __name__ == "__main__":
    main()
