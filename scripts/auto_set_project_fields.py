#!/usr/bin/env python3
"""
GitHub Projects V2 カスタムフィールド自動設定スクリプト

Issue の Labels / Body を解析し、対応する Projects V2 カスタムフィールドを設定する。
auto-add-to-project.yml ワークフローから呼び出される。

Usage:
    python scripts/auto_set_project_fields.py <item_id> <issue_number>

Environment:
    GH_TOKEN: GitHub Token (project:write scope)
    PROJECT_NUMBER: Project number (default: 2)
    ORG_NAME: Organization name (default: tecnos-japan-cbp)
"""

import json
import os
import re
import subprocess
import sys
from datetime import date


# =============================================================================
# Configuration
# =============================================================================

PROJECT_NUMBER = os.environ.get("PROJECT_NUMBER", "2")
ORG_NAME = os.environ.get("ORG_NAME", "tecnos-japan-cbp")


def run_gh(*args: str) -> str:
    """gh CLI コマンド実行"""
    result = subprocess.run(
        ["gh"] + list(args),
        capture_output=True, text=True
    )
    return result.stdout.strip()


def run_gh_json(*args: str) -> dict:
    """gh CLI コマンド実行 (JSON出力)"""
    out = run_gh(*args)
    if not out:
        return {}
    return json.loads(out)


# =============================================================================
# Field Discovery
# =============================================================================

def get_field_map() -> dict:
    """プロジェクトのフィールド定義を取得してマップ化"""
    raw = run_gh(
        "project", "field-list", PROJECT_NUMBER,
        "--owner", ORG_NAME,
        "--format", "json"
    )
    data = json.loads(raw) if raw else {"fields": []}
    field_map = {}
    for f in data.get("fields", []):
        name = f["name"]
        entry = {"id": f["id"], "type": f["type"]}
        if f.get("options"):
            entry["options"] = {
                o["name"].lower(): o["id"] for o in f["options"]
            }
        field_map[name] = entry
    return field_map


def item_edit(item_id: str, field_id: str, **kwargs):
    """gh project item-edit のラッパー"""
    cmd = [
        "project", "item-edit",
        "--project-id", get_project_id(),
        "--id", item_id,
        "--field-id", field_id,
    ]
    if "text" in kwargs:
        cmd += ["--text", kwargs["text"]]
    elif "option_id" in kwargs:
        cmd += ["--single-select-option-id", kwargs["option_id"]]
    elif "date" in kwargs:
        cmd += ["--date", kwargs["date"]]
    run_gh(*cmd)


_project_id_cache = None


def get_project_id() -> str:
    """プロジェクトのnode IDを取得 (キャッシュ付き)"""
    global _project_id_cache
    if _project_id_cache:
        return _project_id_cache
    raw = run_gh(
        "project", "view", PROJECT_NUMBER,
        "--owner", ORG_NAME,
        "--format", "json"
    )
    data = json.loads(raw) if raw else {}
    _project_id_cache = data.get("id", "")
    return _project_id_cache


# =============================================================================
# Issue Parsing
# =============================================================================

def get_issue_data(issue_number: str) -> dict:
    """Issue の labels と body を取得"""
    raw = run_gh(
        "issue", "view", issue_number,
        "--json", "labels,body,milestone,title,assignees"
    )
    return json.loads(raw) if raw else {}


def parse_body_table(body: str) -> dict:
    """Issue body のマークダウンテーブルからフィールド値を抽出"""
    fields = {}
    # | Field | Value | パターンをパース
    for match in re.finditer(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|', body):
        key = match.group(1).strip().lower()
        val = match.group(2).strip()
        if key in ("field", "-------", "---", "item", "dimension"):
            continue  # ヘッダー行をスキップ
        fields[key] = val
    return fields


def parse_risk_flags_checkboxes(body: str) -> list:
    """Risk Flags チェックボックスから有効なフラグを抽出"""
    flags = []
    for match in re.finditer(r'\[x\]\s*(\w+)\s*—', body, re.IGNORECASE):
        flags.append(match.group(1))
    return flags


# =============================================================================
# Label → Field Mapping
# =============================================================================

def extract_fields_from_labels(labels: list) -> dict:
    """ラベルからカスタムフィールド値を推定"""
    result = {}
    label_names = [l["name"] if isinstance(l, dict) else l for l in labels]

    # Issue type detection
    issue_type = None
    for t in ("epic", "milestone", "work-item", "risk", "blocker", "dependency"):
        if t in label_names:
            issue_type = t
            break
    result["_type"] = issue_type

    # Mode: mode:autopilot, mode:confirm, mode:validate
    for l in label_names:
        if l.startswith("mode:"):
            result["sdd_mode"] = l.split(":")[1]

    # Tier: tier:starter, tier:standard, tier:enterprise
    for l in label_names:
        if l.startswith("tier:"):
            result["coverage_tier"] = l.split(":")[1]

    # Status
    status_map = {
        "status:done": "Done",
        "status:in-progress": "In Progress",
        "status:pending": "Todo",
        "status:blocked": "Todo",
    }
    for l in label_names:
        if l in status_map:
            result["status"] = status_map[l]

    # Priority
    for l in label_names:
        if l.startswith("priority:"):
            prio = l.split(":")[1]
            prio_map = {"high": "P1-High", "medium": "P2-Medium", "low": "P3-Low"}
            result["priority"] = prio_map.get(prio, "P2-Medium")

    # Risk flags from labels
    risk_flags = []
    for l in label_names:
        if l.startswith("risk:"):
            risk_flags.append(l.split(":")[1])
    if risk_flags:
        result["risk_flags"] = ", ".join(risk_flags)

    # Gate labels
    for l in label_names:
        if l.startswith("gate:"):
            gate_str = l.split(":")[1]
            gate_map = {
                "1-design": "Gate 1", "2-bpmn": "Gate 2", "3-spec": "Gate 3",
                "4-plan": "Gate 4", "5-tasking": "Gate 5", "final": "Final",
            }
            result["sdd_gate"] = gate_map.get(gate_str, gate_str)

    # Ops readiness
    if "ops-ready" in label_names:
        result["_ops_ready"] = True
    if "ops-not-ready" in label_names:
        result["_ops_ready"] = False

    return result


# =============================================================================
# Field Setting
# =============================================================================

def set_field(item_id: str, field_map: dict, field_name: str, value: str):
    """汎用フィールド設定"""
    if field_name not in field_map:
        return False
    field = field_map[field_name]
    fid = field["id"]

    if "options" in field:
        # Single Select
        opt_id = field["options"].get(value.lower())
        if opt_id:
            item_edit(item_id, fid, option_id=opt_id)
            return True
    elif "Date" in field.get("type", "") or field_name in ("Start date", "Target date"):
        item_edit(item_id, fid, date=value)
        return True
    else:
        # Text
        item_edit(item_id, fid, text=value)
        return True
    return False


def apply_fields(item_id: str, issue_number: str):
    """Issue データからフィールドを自動設定"""
    field_map = get_field_map()
    issue = get_issue_data(issue_number)

    if not issue:
        print(f"ERROR: Could not fetch issue #{issue_number}")
        return

    labels = issue.get("labels", [])
    body = issue.get("body", "") or ""
    title = issue.get("title", "")

    # Label からフィールド推定
    label_fields = extract_fields_from_labels(labels)
    issue_type = label_fields.get("_type")

    # Body テーブルからフィールド推定
    body_fields = parse_body_table(body)

    ok = 0
    total = 0

    def try_set(fname, val):
        nonlocal ok, total
        if val:
            total += 1
            if set_field(item_id, field_map, fname, val):
                ok += 1
                print(f"  OK: {fname} = {val}")
            else:
                print(f"  SKIP: {fname} = {val} (field/option not found)")

    # --- Status ---
    try_set("Status", label_fields.get("status", "Todo"))

    # --- Feature ID ---
    feat_id = body_fields.get("feature") or body_fields.get("feature id")
    if feat_id and feat_id not in ("FEAT-XXX-NNN", "FEAT-XXX"):
        try_set("Feature ID", feat_id)

    # --- WI-specific fields ---
    if issue_type == "work-item":
        wi_id = body_fields.get("wi id")
        if wi_id and wi_id != "WI-XXX-NNN":
            try_set("WI ID", wi_id)

        try_set("SDD Mode", label_fields.get("sdd_mode"))
        try_set("Coverage Tier", label_fields.get("coverage_tier"))
        try_set("Complexity", body_fields.get("complexity"))
        try_set("SDD Gate", label_fields.get("sdd_gate") or body_fields.get("gate"))

        # WI Status from label status
        wi_status_map = {
            "Done": "done", "In Progress": "in_progress", "Todo": "pending_pre_approval"
        }
        status = label_fields.get("status", "Todo")
        try_set("WI Status", wi_status_map.get(status, "pending_pre_approval"))

        # Risk Flags from labels or body checkboxes
        risk_str = label_fields.get("risk_flags")
        if not risk_str:
            flags = parse_risk_flags_checkboxes(body)
            if flags:
                risk_str = ", ".join(flags)
        try_set("Risk Flags", risk_str)

    # --- EPIC fields ---
    elif issue_type == "epic":
        try_set("SDD Gate", label_fields.get("sdd_gate") or body_fields.get("gate"))
        try_set("Coverage Tier", label_fields.get("coverage_tier"))

    # --- Risk fields ---
    elif issue_type == "risk":
        prob = body_fields.get("probability", "")
        impact = body_fields.get("impact", "")
        risk_status = body_fields.get("status", "")
        if prob or impact:
            try_set("Risk Flags", f"probability:{prob}, impact:{impact}")
        if risk_status == "mitigating":
            try_set("Status", "In Progress")

    # --- Priority ---
    try_set("Priority", label_fields.get("priority"))

    # --- Process Metrics fields ---
    # These fields are populated by stride_process_metrics.py analysis
    # Gate Age (days): current gate dwell time
    # Delay Risk: on_track / at_risk / overdue
    # Gate: current gate (g1-g5, evidence)
    if issue_type == "work-item":
        feat_id_val = body_fields.get("feature") or body_fields.get("feature id")
        if feat_id_val and feat_id_val not in ("FEAT-XXX-NNN", "FEAT-XXX"):
            from pathlib import Path as _Path
            feat_dir = _Path("specs") / feat_id_val
            if feat_dir.exists():
                try:
                    _scripts_dir = str(_Path(__file__).resolve().parent)
                    if _scripts_dir not in sys.path:
                        sys.path.insert(0, _scripts_dir)
                    from stride_process_metrics import analyze_feature
                    pm = analyze_feature(feat_dir)
                    # Gate field: map current_gate to short form
                    gate_short_map = {
                        "gate1_design": "g1", "gate2_bpmn": "g2",
                        "gate3_spec": "g3", "gate4_plan": "g4",
                        "gate5_tasks": "g5", "evidence": "evidence",
                        "completed": "evidence",
                    }
                    try_set("Gate", gate_short_map.get(pm.current_gate, ""))
                    if pm.current_gate_age_days is not None:
                        try_set("Gate Age (days)", str(pm.current_gate_age_days))
                    # Delay Risk: use worst risk among WIs
                    wi_id_val = body_fields.get("wi id")
                    for wi_m in pm.wi_metrics:
                        if wi_m.wi_id == wi_id_val:
                            try_set("Delay Risk", wi_m.delay_risk)
                            break
                except Exception as e:
                    print(f"  SKIP: Process Metrics (import error: {e})")

    # --- Dates ---
    today = date.today().isoformat()
    try_set("Start date", today)

    # Target date from milestone if available
    milestone = issue.get("milestone")
    if milestone and milestone.get("dueOn"):
        due = milestone["dueOn"][:10]  # YYYY-MM-DD
        try_set("Target date", due)

    print(f"\nSet {ok}/{total} fields for issue #{issue_number} ({issue_type or 'unknown'})")


# =============================================================================
# Main
# =============================================================================

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <project_item_id> <issue_number>")
        sys.exit(1)

    item_id = sys.argv[1]
    issue_number = sys.argv[2]

    print(f"Setting fields for item {item_id[:20]}... (issue #{issue_number})")
    apply_fields(item_id, issue_number)


if __name__ == "__main__":
    main()
