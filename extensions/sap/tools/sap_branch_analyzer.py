"""
sap_branch_analyzer.py — ABAP ソースコードの分岐解析ツール

ABAP ソースファイルをパースし、全分岐ステートメント（IF/CASE/TRY-CATCH/LOOP/
DELETE WHERE/AUTHORITY-CHECK/SELECT）を抽出する。
各分岐に対してテストケースの必要性を判定し、plan.md tests[] および tasks.md
への追加提案を branch_analysis.yaml に出力する。

Usage:
  python3 extensions/sap/tools/sap_branch_analyzer.py \\
    --source <abap_source.prog.abap> \\
    --plan <plan.md> \\
    --output <branch_analysis.yaml>

stride-lint から自動実行する場合は MANIFEST.yaml に宣言する。
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from typing import Any

# Windows cp932 で出力できない文字（em dash 等）対策
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from tool_evidence_writer import write_evidence

sys.path.insert(0, str(Path(__file__).parent))
from sap_evidence_common import load_yaml_from_md

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# ABAP ソースパーサー
# ---------------------------------------------------------------------------

def parse_abap_branches(source: str) -> list[dict[str, Any]]:
    """ABAP ソースから全分岐ステートメントを抽出する。

    各分岐に step_marker（@STEP のマーカー）を付与する。
    """
    branches = []
    current_form = "MAIN"
    current_step_marker = ""
    in_test_class = False
    lines = source.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # @STEP コメントの検出
        step_match = re.match(r'^"\s*@STEP:\s*(\S+)', stripped)
        if step_match:
            current_step_marker = step_match.group(1)
            continue

        # コメント行をスキップ
        if stripped.startswith("*") or stripped.startswith('"'):
            continue

        # テストクラス（FOR TESTING）が見つかったら以降全てスキップ
        if re.search(r"CLASS\s+\w+\s+DEFINITION\s+FOR\s+TESTING", stripped, re.IGNORECASE):
            break

        # FORM の検出
        form_match = re.match(r"^FORM\s+(\w+)", stripped, re.IGNORECASE)
        if form_match:
            current_form = form_match.group(1).upper()
            continue
        if re.match(r"^ENDFORM", stripped, re.IGNORECASE):
            current_form = "MAIN"
            current_step_marker = ""
            continue

        # CLASS / METHOD の検出
        method_match = re.match(r"^\s*METHOD\s+(\w+)", stripped, re.IGNORECASE)
        if method_match:
            current_form = method_match.group(1).upper()
            continue
        if re.match(r"^\s*ENDMETHOD", stripped, re.IGNORECASE):
            current_form = "MAIN"
            current_step_marker = ""
            continue

        # --- 分岐ステートメントの検出 ---

        # IF
        if_match = re.match(r"^IF\s+(.+?)\.?\s*$", stripped, re.IGNORECASE)
        if if_match:
            condition = if_match.group(1).strip()
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "IF", "condition": condition,
                "paths": [
                    {"path": "TRUE", "description": f"{condition} が真の場合"},
                    {"path": "FALSE", "description": f"{condition} が偽の場合"},
                ],
            })
            continue

        # ELSEIF
        elseif_match = re.match(r"^ELSEIF\s+(.+?)\.?\s*$", stripped, re.IGNORECASE)
        if elseif_match:
            condition = elseif_match.group(1).strip()
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "ELSEIF", "condition": condition,
                "paths": [
                    {"path": "TRUE", "description": f"{condition} が真の場合"},
                ],
            })
            continue

        # CASE
        case_match = re.match(r"^CASE\s+(.+?)\.?\s*$", stripped, re.IGNORECASE)
        if case_match:
            variable = case_match.group(1).strip()
            # WHEN 句を後続行から収集
            whens = []
            for j in range(i, min(i + 50, len(lines))):
                when_match = re.match(r"^\s*WHEN\s+(.+?)\.?\s*$", lines[j], re.IGNORECASE)
                if when_match:
                    whens.append(when_match.group(1).strip())
                if re.match(r"^\s*ENDCASE", lines[j], re.IGNORECASE):
                    break
            paths = [{"path": f"WHEN {w}", "description": f"{variable} = {w}"} for w in whens]
            if paths:
                branches.append({
                    "line": i, "form": current_form,
                    "step_marker": current_step_marker,
                    "statement": "CASE", "condition": variable,
                    "paths": paths,
                })
            continue

        # TRY / CATCH
        if re.match(r"^TRY\.?\s*$", stripped, re.IGNORECASE):
            # CATCH 句を後続行から収集
            catches = []
            for j in range(i, min(i + 100, len(lines))):
                catch_match = re.match(r"^\s*CATCH\s+(.+?)(?:\s+INTO\s+.+)?\.?\s*$", lines[j], re.IGNORECASE)
                if catch_match:
                    catches.append(catch_match.group(1).strip())
                if re.match(r"^\s*ENDTRY", lines[j], re.IGNORECASE):
                    break
            paths = [{"path": "SUCCESS", "description": "例外なしで正常完了"}]
            for c in catches:
                paths.append({"path": f"CATCH {c}", "description": f"例外 {c} が発生した場合"})
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "TRY/CATCH", "condition": f"CATCH: {', '.join(catches)}",
                "paths": paths,
            })
            continue

        # LOOP
        loop_match = re.match(r"^LOOP\s+AT\s+(.+?)(?:\s+INTO|\s+ASSIGNING|\s+REFERENCE|\s+WHERE|\.)", stripped, re.IGNORECASE)
        if loop_match:
            table = loop_match.group(1).strip()
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "LOOP", "condition": f"LOOP AT {table}",
                "paths": [
                    {"path": "ENTRIES", "description": f"{table} にデータがある場合（ループ実行）"},
                    {"path": "EMPTY", "description": f"{table} が空の場合（ループスキップ）"},
                ],
            })
            continue

        # DELETE WHERE
        delete_match = re.match(r"^DELETE\s+(\w+)\s+WHERE\s+(.+?)\.?\s*$", stripped, re.IGNORECASE)
        if delete_match:
            table = delete_match.group(1).strip()
            condition = delete_match.group(2).strip()
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "DELETE WHERE", "condition": f"DELETE {table} WHERE {condition}",
                "paths": [
                    {"path": "DELETED", "description": f"条件 {condition} に一致するレコードが存在し削除される"},
                    {"path": "NO_MATCH", "description": f"条件に一致するレコードがなく削除なし"},
                    {"path": "ALL_DELETED", "description": f"全レコードが条件に一致し、結果が空になる"},
                ],
            })
            continue

        # AUTHORITY-CHECK
        auth_match = re.match(r"^AUTHORITY-CHECK\s+OBJECT\s+'([^']+)'", stripped, re.IGNORECASE)
        if auth_match:
            auth_obj = auth_match.group(1).strip()
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "AUTHORITY-CHECK", "condition": f"AUTHORITY-CHECK OBJECT '{auth_obj}'",
                "paths": [
                    {"path": "AUTHORIZED", "description": f"権限オブジェクト {auth_obj} の権限チェック成功（sy-subrc = 0）"},
                    {"path": "UNAUTHORIZED", "description": f"権限オブジェクト {auth_obj} の権限チェック失敗（sy-subrc <> 0）"},
                ],
            })
            continue

        # SELECT (データあり/なし)
        select_match = re.match(r"^SELECT\s+", stripped, re.IGNORECASE)
        if select_match and "INTO" in stripped.upper():
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "SELECT", "condition": stripped[:80],
                "paths": [
                    {"path": "DATA_FOUND", "description": "SELECT 結果にデータがある（テスト条件に合致するデータが2件以上必須。1件だと複数件処理のバグを見逃す）"},
                    {"path": "NO_DATA", "description": "SELECT 結果が0件"},
                ],
            })
            continue

        # AT FIRST / END OF / NEW / LAST（ソート制御の分岐）
        at_match = re.match(r"^AT\s+(FIRST|END\s+OF|NEW|LAST)\s*(\w*)", stripped, re.IGNORECASE)
        if at_match:
            at_type = at_match.group(1).upper()
            at_field = at_match.group(2).strip() if at_match.group(2) else ""
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": f"AT {at_type}", "condition": f"AT {at_type} {at_field}".strip(),
                "paths": [
                    {"path": "MATCH", "description": f"AT {at_type} {at_field} に該当する場合".strip()},
                    {"path": "NO_MATCH", "description": f"AT {at_type} {at_field} に該当しない場合".strip()},
                ],
            })
            continue

        # 0除算の可能性（/ 演算子、DIV）
        if re.search(r"\s/\s|\bDIV\b", stripped, re.IGNORECASE) and not stripped.startswith("*"):
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "DIVISION", "condition": stripped[:80],
                "paths": [
                    {"path": "NORMAL", "description": "除数が0でない場合（正常計算）"},
                    {"path": "ZERO_DIVIDE", "description": "除数が0の場合（0除算リスク）"},
                ],
            })
            continue

        # CALL FUNCTION（汎用モジュール呼出）
        call_fm_match = re.match(r"^CALL\s+FUNCTION\s+'([^']+)'", stripped, re.IGNORECASE)
        if call_fm_match:
            fm_name = call_fm_match.group(1)
            branches.append({
                "line": i, "form": current_form,
                "step_marker": current_step_marker,
                "statement": "CALL FUNCTION", "condition": f"CALL FUNCTION '{fm_name}'",
                "paths": [
                    {"path": "SUCCESS", "description": f"FM {fm_name} が正常終了（sy-subrc = 0）"},
                    {"path": "FAIL", "description": f"FM {fm_name} が異常終了（sy-subrc <> 0）"},
                ],
            })
            continue

    return branches


# ---------------------------------------------------------------------------
# 分岐の分類（auto / manual_required / not_reachable）
# ---------------------------------------------------------------------------

def classify_branch_path(branch: dict, path: dict) -> tuple[str, str]:
    """分岐パスを auto / manual_required / not_reachable に分類する。

    Returns: (method, reason)
    """
    stmt = branch["statement"]
    path_name = path["path"]

    # TRY/CATCH の例外パス → manual_required
    if stmt == "TRY/CATCH" and path_name.startswith("CATCH"):
        return "manual_required", f"例外パス（{path_name}）は GUI で再現困難。ABAP Unit でカバー"

    # AUTHORITY-CHECK の失敗 → manual_required
    if stmt == "AUTHORITY-CHECK" and path_name == "UNAUTHORIZED":
        return "manual_required", "権限チェック失敗はテストユーザーの権限変更が必要。環境依存"

    # その他は auto
    return "auto", ""


# ---------------------------------------------------------------------------
# plan.md tests[] との突合
# ---------------------------------------------------------------------------

def _build_step_to_scenarios(spec_path: Path | None, plan_tests: list[dict],
                             plan_scenarios: list[dict]) -> dict[str, list[str]]:
    """@STEP marker からシナリオ ID へのマッピングを構築する。

    Chain: step_marker → processing_step (via source_marker)
           → AC (via processing_step_ref) → tests (via covers_acceptance_ids)
           → scenarios (via covers_ts.ts_id)

    Returns: {step_marker: [scenario_id, ...]}
    """
    if not spec_path or not spec_path.is_file():
        return {}

    spec_doc = load_yaml_from_md(spec_path)
    if not spec_doc:
        return {}

    # 1. source_marker → PS-ID
    processing_steps = (
        spec_doc.get("spec", {}).get("spec_as_code", {}).get("processing_steps", []) or spec_doc.get("spec", {}).get("processing_steps", []) or []
    )
    marker_to_ps: dict[str, str] = {}
    for ps in processing_steps:
        sm = (ps.get("source_marker") or "").strip()
        ps_id = (ps.get("id") or "").strip()
        if sm and ps_id:
            marker_to_ps[sm] = ps_id

    # 2. PS-ID → AC IDs (via processing_step_ref)
    ps_to_ac_ids: dict[str, list[str]] = {}
    use_cases = spec_doc.get("spec", {}).get("use_cases", []) or []
    for uc in use_cases:
        for ac in uc.get("acceptance", []) or []:
            ref = (ac.get("processing_step_ref") or "").strip()
            ac_id = (ac.get("id") or "").strip()
            if ref and ac_id:
                ps_to_ac_ids.setdefault(ref, []).append(ac_id)

    # 3. AC ID → scenario IDs (via covers_ts[].ac_id — 新体系で直接紐づけ)
    ac_to_scenario_ids: dict[str, list[str]] = {}
    for sc in plan_scenarios:
        sc_id = (sc.get("id") or "").strip()
        for cts in sc.get("covers_ts", []) or []:
            ac_id = (cts.get("ac_id") or "").strip()
            if ac_id:
                ac_to_scenario_ids.setdefault(ac_id, []).append(sc_id)

    # 旧体系フォールバック: covers_acceptance_ids 経由
    if not ac_to_scenario_ids and plan_tests:
        ac_to_test_ids: dict[str, list[str]] = {}
        for t in plan_tests:
            t_id = (t.get("id") or "").strip()
            for cov_ac in t.get("covers_acceptance_ids", []) or []:
                ac_to_test_ids.setdefault(cov_ac, []).append(t_id)
        test_to_scenarios: dict[str, list[str]] = {}
        for sc in plan_scenarios:
            sc_id = (sc.get("id") or "").strip()
            for cts in sc.get("covers_ts", []) or []:
                ts_id = (cts.get("ts_id") or "").strip()
                if ts_id:
                    test_to_scenarios.setdefault(ts_id, []).append(sc_id)
        for ac_id_key, test_ids in ac_to_test_ids.items():
            for tid in test_ids:
                ac_to_scenario_ids.setdefault(ac_id_key, []).extend(
                    test_to_scenarios.get(tid, []))

    # Compose: step_marker → scenario IDs
    step_to_scenarios: dict[str, list[str]] = {}
    for marker, ps_id in marker_to_ps.items():
        scenario_ids: list[str] = []
        for ac_id in ps_to_ac_ids.get(ps_id, []):
            scenario_ids.extend(ac_to_scenario_ids.get(ac_id, []))
        # deduplicate while preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for sid in scenario_ids:
            if sid not in seen:
                seen.add(sid)
                unique.append(sid)
        if unique:
            step_to_scenarios[marker] = unique

    return step_to_scenarios


def match_branches_to_tests(branches: list[dict], plan_tests: list[dict],
                            spec_path: Path | None = None,
                            plan_scenarios: list[dict] | None = None) -> list[dict]:
    """各分岐パスを @STEP marker ベースで plan.md tests[] / scenarios と突合し、カバー状況を判定する。

    マッチング優先順位:
      1. step_marker → processing_step (source_marker) → AC (processing_step_ref)
         → tests (covers_acceptance_ids) → scenarios (covers_ts)
      2. step_marker が空、または processing_steps に該当がない場合 → "proposed"
    """
    results = []

    # @STEP → scenario マッピングを構築
    step_to_scenarios = _build_step_to_scenarios(
        spec_path, plan_tests, plan_scenarios or []
    )

    # test ID → test dict (高速ルックアップ用)
    test_by_id: dict[str, dict] = {t.get("id", ""): t for t in plan_tests}

    # AC → test IDs 逆引き（step_marker 経由でテスト ID を取得するため再構築）
    # step_marker → test IDs も直接構築
    step_to_test_ids: dict[str, list[str]] = {}
    if spec_path and spec_path.is_file():
        spec_doc = load_yaml_from_md(spec_path) or {}
        processing_steps = spec_doc.get("spec", {}).get("spec_as_code", {}).get("processing_steps", []) or spec_doc.get("spec", {}).get("processing_steps", []) or []
        marker_to_ps: dict[str, str] = {}
        for ps in processing_steps:
            sm = (ps.get("source_marker") or "").strip()
            ps_id = (ps.get("id") or "").strip()
            if sm and ps_id:
                marker_to_ps[sm] = ps_id

        ps_to_ac_ids: dict[str, list[str]] = {}
        # Primary: processing_steps[].ac_refs (explicit AC mapping)
        for ps in processing_steps:
            ps_id = (ps.get("id") or "").strip()
            ac_refs = ps.get("ac_refs") or []
            if ps_id and ac_refs:
                ps_to_ac_ids[ps_id] = [a.strip() for a in ac_refs if a.strip()]
        # Fallback: spec.md AC.processing_step_ref (legacy, if ac_refs not set)
        if not ps_to_ac_ids:
            use_cases = spec_doc.get("spec", {}).get("use_cases", []) or []
            for uc in use_cases:
                for ac in uc.get("acceptance", []) or []:
                    ref = (ac.get("processing_step_ref") or "").strip()
                    ac_id = (ac.get("id") or "").strip()
                    if ref and ac_id:
                        ps_to_ac_ids.setdefault(ref, []).append(ac_id)

        # 新体系: covers_ts[].ac_id から AC → scenario/test 紐づけ
        ac_to_test_ids: dict[str, list[str]] = {}
        for sc in (plan_scenarios or []):
            sc_id = (sc.get("id") or "").strip()
            for cts in sc.get("covers_ts", []) or []:
                ac_id_val = (cts.get("ac_id") or "").strip()
                ts_id_val = (cts.get("ts_id") or "").strip()
                if ac_id_val and ts_id_val:
                    ac_to_test_ids.setdefault(ac_id_val, []).append(ts_id_val)
        # 旧体系フォールバック
        if not ac_to_test_ids:
            for t in plan_tests:
                t_id = (t.get("id") or "").strip()
                for cov_ac in t.get("covers_acceptance_ids", []) or []:
                    ac_to_test_ids.setdefault(cov_ac, []).append(t_id)

        for marker, ps_id in marker_to_ps.items():
            tids: list[str] = []
            for ac_id in ps_to_ac_ids.get(ps_id, []):
                tids.extend(ac_to_test_ids.get(ac_id, []))
            seen: set[str] = set()
            unique: list[str] = []
            for tid in tids:
                if tid not in seen:
                    seen.add(tid)
                    unique.append(tid)
            if unique:
                step_to_test_ids[marker] = unique

    for branch in branches:
        step_marker = branch.get("step_marker", "")
        # 同一分岐の各パスに同じテストが使われないよう追跡
        used_tests_for_branch: set[str] = set()

        for path in branch.get("paths", []):
            method, reason = classify_branch_path(branch, path)
            matched_test = None
            matched_scenarios: list[str] = []

            # --- @STEP ベースマッチング ---
            if step_marker and step_marker in step_to_test_ids:
                # step_marker に紐づくテスト ID から未使用のものを選択
                for tid in step_to_test_ids[step_marker]:
                    if tid not in used_tests_for_branch:
                        matched_test = tid
                        break

                # 対応するシナリオも取得
                matched_scenarios = step_to_scenarios.get(step_marker, [])

            if matched_test:
                used_tests_for_branch.add(matched_test)

            # ステータス判定
            if matched_test:
                status = "covered"
            elif method == "manual_required":
                status = "manual_required"
            else:
                # step_marker が空、または processing_steps に該当なし → proposed
                status = "proposed"

            results.append({
                "form": branch["form"],
                "line": branch["line"],
                "statement": branch["statement"],
                "condition": branch["condition"],
                "step_marker": step_marker,
                "path": path["path"],
                "description": path["description"],
                "method": method,
                "reason": reason,
                "matched_test": matched_test,
                "matched_scenarios": matched_scenarios if matched_scenarios else None,
                "status": status,
            })

    return results


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------

def generate_analysis(source_path: Path, plan_path: Path,
                      spec_path: Path | None = None) -> dict:
    """分岐解析を実行し結果を返す。"""
    source = source_path.read_text(encoding="utf-8")
    branches = parse_abap_branches(source)

    plan_doc = load_yaml_from_md(plan_path) if plan_path.is_file() else {}
    plan_tests = plan_doc.get("plan", {}).get("test_strategy", {}).get("tests") or []
    plan_scenarios = (
        plan_doc.get("plan", {}).get("test_strategy", {})
        .get("test_scenarios", {}).get("scenarios") or []
    )

    results = match_branches_to_tests(
        branches, plan_tests, spec_path=spec_path, plan_scenarios=plan_scenarios
    )

    total_paths = len(results)
    covered = sum(1 for r in results if r["status"] == "covered")
    proposed = sum(1 for r in results if r["status"] == "proposed")
    manual = sum(1 for r in results if r["status"] == "manual_required")

    return {
        "analysis": {
            "source": str(source_path),
            "total_branch_paths": total_paths,
            "covered": covered,
            "proposed": proposed,
            "manual_required": manual,
        },
        "branches": results,
    }


def format_markdown_table(analysis: dict) -> str:
    """分岐解析結果を Markdown テーブルに整形する。"""
    lines = []
    lines.append("## Branch Analysis（分岐解析結果）")
    lines.append("")
    lines.append(f"> ソース: {analysis['analysis']['source']}")
    lines.append(f"> 全分岐パス: {analysis['analysis']['total_branch_paths']}")
    lines.append(f"> カバー済み: {analysis['analysis']['covered']}")
    lines.append(f"> 追加提案: {analysis['analysis']['proposed']}")
    lines.append(f"> 手動判断: {analysis['analysis']['manual_required']}")
    lines.append("")
    lines.append("**Status 凡例:**")
    lines.append("- **covered** — 既存テストでカバー済み")
    lines.append("- **proposed** — テスト追加が必要（plan.md tests[] と tasks.md に追加してください）")
    lines.append("- **manual_required** — GUI 再現困難。ABAP Unit でカバーし、s_evidence は manual_required とする")
    lines.append("")
    lines.append("| # | FORM | Line | Statement | Path | Description | Status | Matched Test | Reason |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for i, br in enumerate(analysis["branches"], 1):
        lines.append(
            f"| {i} | {br['form']} | {br['line']} | {br['statement']} | {br['path']} "
            f"| {br['description']} | **{br['status']}** | {br['matched_test'] or '—'} | {br['reason'] or '—'} |"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Spec-coverage mode (S1-E1)
# ---------------------------------------------------------------------------

def check_spec_coverage(source_path: Path, spec_path: Path) -> dict:
    """仕様ベースカバレッジ: spec.md の全 branches が実装に存在するかチェックする。

    分母: spec.md の processing_steps.branches
    分子: ABAP ソースの @STEP markers

    Returns: {"total": N, "covered": N, "missing": N, "details": [...], "report": str}
    """
    # 1. spec.md から processing_steps + branches を取得
    spec_doc = load_yaml_from_md(spec_path)
    if not spec_doc:
        return {"total": 0, "covered": 0, "missing": 0, "details": [], "report": "Error: spec.md parse failed"}

    processing_steps = (
        spec_doc.get("spec", {}).get("spec_as_code", {}).get("processing_steps", [])
        or spec_doc.get("spec", {}).get("processing_steps", [])
        or []
    )

    # 2. ABAP ソースから @STEP markers を抽出
    source_text = source_path.read_text(encoding="utf-8", errors="replace")
    import re
    step_markers_in_source = set()
    for m in re.finditer(r'"\s*@STEP:\s*(\S+)', source_text):
        step_markers_in_source.add(m.group(1).strip())

    # 3. 各 processing_step の source_marker が実装に存在するか確認
    details = []
    total = 0
    covered = 0
    missing = 0

    for ps in processing_steps:
        ps_id = ps.get("id", "")
        ps_name = ps.get("name", "")
        source_marker = (ps.get("source_marker") or "").strip()
        branches = ps.get("branches", []) or []

        if not source_marker:
            # source_marker が未定義 → missing
            for b in branches:
                total += 1
                missing += 1
                details.append({
                    "ps_id": ps_id, "ps_name": ps_name,
                    "branch": b.get("pattern", ""), "type": b.get("type", ""),
                    "status": "missing", "reason": "source_marker が未定義"
                })
            continue

        marker_found = source_marker in step_markers_in_source

        for b in branches:
            total += 1
            if marker_found:
                covered += 1
                details.append({
                    "ps_id": ps_id, "ps_name": ps_name,
                    "branch": b.get("pattern", ""), "type": b.get("type", ""),
                    "status": "covered", "reason": f"@STEP: {source_marker}"
                })
            else:
                missing += 1
                details.append({
                    "ps_id": ps_id, "ps_name": ps_name,
                    "branch": b.get("pattern", ""), "type": b.get("type", ""),
                    "status": "missing", "reason": f"@STEP: {source_marker} が実装に存在しない"
                })

    # 4. レポート生成
    lines = [
        "## Spec-Coverage Check (S1-E1)",
        "",
        f"> 仕様の分岐数: {total}",
        f"> 実装で確認済み: {covered}",
        f"> 実装漏れ: {missing}",
        "",
        "| # | PS | 処理名 | 分岐 | 種別 | Status | Reason |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, d in enumerate(details, 1):
        status_mark = "covered" if d["status"] == "covered" else "**MISSING**"
        lines.append(
            f"| {i} | {d['ps_id']} | {d['ps_name']} | {d['branch']} | {d['type']} | {status_mark} | {d['reason']} |"
        )

    if missing == 0:
        lines.append(f"\n**Result: PASS** — 仕様の全 {total} 分岐が実装に存在します。")
    else:
        lines.append(f"\n**Result: FAIL** — {missing}/{total} 分岐が実装に存在しません。S1-B1 に戻って実装してください。")

    return {
        "total": total,
        "covered": covered,
        "missing": missing,
        "details": details,
        "report": "\n".join(lines),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    original_argv = sys.argv.copy()

    import argparse
    parser = argparse.ArgumentParser(description="ABAP branch analyzer")
    parser.add_argument("--source", required=True, help="ABAP source file path")
    parser.add_argument("--plan", required=True, help="plan.md path")
    parser.add_argument("--spec", help="spec.md path (for @STEP-based matching)")
    parser.add_argument("--output", help="Output YAML path (optional)")
    parser.add_argument("--mode", choices=["impl-coverage", "spec-coverage"], default="impl-coverage",
                        help="spec-coverage: 仕様を分母(S1-E1用), impl-coverage: 実装を分母(S2-A1用, デフォルト)")
    parser.add_argument("--step-id", help="Step ID for evidence tracking")
    args = parser.parse_args()

    source_path = Path(args.source)
    plan_path = Path(args.plan)
    spec_path = Path(args.spec) if args.spec else None

    if not source_path.is_file():
        print(f"Error: Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "spec-coverage":
        # S1-E1: 仕様ベースカバレッジ — spec.md の全 branches が実装に存在するか
        if not spec_path or not spec_path.is_file():
            print("Error: --spec is required for spec-coverage mode", file=sys.stderr)
            sys.exit(1)
        result = check_spec_coverage(source_path, spec_path)
        print(result["report"])
        if args.step_id:
            feature_dir = plan_path.parent
            total = result["total"]
            covered = result["covered"]
            pct = f"{covered}/{total} ({covered*100//total if total else 0}%)"
            write_evidence(
                feature_dir=str(feature_dir),
                step_id=args.step_id,
                tool_name="sap_branch_analyzer.py",
                command=" ".join(original_argv),
                options=[f"--mode {args.mode}"],
                result_summary=f"spec-coverage: {pct}",
            )
        if result["missing"] > 0:
            sys.exit(1)
    else:
        # S2-A1: 実装ベースカバレッジ — 実装の全分岐がテストシナリオでカバーされているか
        analysis = generate_analysis(source_path, plan_path, spec_path=spec_path)
        print(format_markdown_table(analysis))
        if args.output and yaml:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                yaml.dump(analysis, allow_unicode=True, default_flow_style=False, sort_keys=False),
                encoding="utf-8"
            )
            print(f"\nAnalysis saved to: {output_path}")
        proposed = analysis["analysis"]["proposed"]
        total_paths = analysis["analysis"]["total_branch_paths"]
        covered = analysis["analysis"]["covered"]
        if args.step_id:
            feature_dir = plan_path.parent
            pct = f"{covered}/{total_paths} ({covered*100//total_paths if total_paths else 0}%)"
            write_evidence(
                feature_dir=str(feature_dir),
                step_id=args.step_id,
                tool_name="sap_branch_analyzer.py",
                command=" ".join(original_argv),
                options=[f"--mode {args.mode}"],
                result_summary=f"impl-coverage: {pct}",
            )
        if proposed > 0:
            print(f"\nWARN: {proposed} 件の未カバー分岐があります。S2-A2 で判断してください。")
            sys.exit(1)


if __name__ == "__main__":
    main()
