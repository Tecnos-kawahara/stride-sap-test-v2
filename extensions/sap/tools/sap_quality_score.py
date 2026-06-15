"""
sap_quality_score.py -- ABAP ソース品質スコアリング（減点方式）

100点満点からスタートし、違反ごとに減点する。
小さくシンプルなプログラムでも違反がなければ100点。

カテゴリ:
  1. エラーハンドリング漏れ（最大-30点）
  2. 命名規約違反（最大-20点）
  3. テンプレート準拠（最大-15点）
  4. 実行効率（最大-20点）— ルール S7 対応
  5. 保守性（最大-15点）

Usage:
  python3 extensions/sap/tools/sap_quality_score.py <source_file_or_dir>
  python3 extensions/sap/tools/sap_quality_score.py <source_file_or_dir> --spec <spec.md>

終了コード:
  0: PASS（合格基準点以上）
  1: FAIL（合格基準点未満）
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from tool_evidence_writer import write_evidence

sys.path.insert(0, str(Path(__file__).parent))
from sap_evidence_common import load_yaml_file, load_yaml_from_md


# ---------------------------------------------------------------------------
# A_命名規約.md 準拠プレフィックス
# ---------------------------------------------------------------------------
NAMING_PREFIXES = {
    # ローカル DATA
    "LDF_", "LDS_", "LDT_", "LDT_R_",
    # グローバル DATA
    "GDF_", "GDS_", "GDT_", "GDT_R_",
    # ローカル TYPES
    "LTF_", "LTS_", "LTT_", "LTT_R_",
    # グローバル TYPES
    "GTF_", "GTS_", "GTT_", "GTT_R_",
    # CONSTANTS
    "LCF_", "LCS_", "GCF_", "GCS_",
    # 参照変数
    "LRO_", "LRD_", "LRB_", "LRX_", "LRI_",
    "GRO_", "GRD_", "GRB_", "GRX_", "GRI_",
    # メソッド引数
    "PIF_", "PIS_", "PIT_", "PIT_R_", "PIR_",
    "POF_", "POS_", "POT_", "POT_R_", "POR_",
    # 選択画面
    "P_", "S_", "R_", "G_", "C_", "B_",
}

# フィールドシンボル
FIELD_SYMBOL_PREFIXES = {"<GFF_", "<GFS_", "<GFT_", "<GFR_", "<LFF_", "<LFS_", "<LFT_", "<LFR_"}


def _find_config(start_dir: Path) -> Path | None:
    """quality_score_config.yaml を探す。"""
    for parent in [start_dir] + list(start_dir.parents):
        candidate = parent / "extensions" / "sap" / "config" / "quality_score_config.yaml"
        if candidate.is_file():
            return candidate
    return None


def _find_common_class_rules(start_dir: Path) -> Path | None:
    """common_class_rules.yaml を探す。"""
    for parent in [start_dir] + list(start_dir.parents):
        candidate = parent / "extensions" / "sap" / "config" / "common_class_rules.yaml"
        if candidate.is_file():
            return candidate
    return None


def _load_common_class_names(start_dir: Path) -> set[str]:
    """共通クラス名を common_class_rules.yaml から取得する。"""
    rules_path = _find_common_class_rules(start_dir)
    if not rules_path:
        return set()
    data = load_yaml_file(rules_path)
    names = set()
    for rule in data.get("common_class_rules") or []:
        for cls in rule.get("classes") or []:
            name = cls.get("name", "")
            if name:
                names.add(name.upper())
    return names


def _read_source(file_path: Path) -> str:
    """ソースファイルを読み込む。"""
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        try:
            return file_path.read_text(encoding="cp932")
        except (OSError, UnicodeDecodeError):
            return ""


def _is_comment_line(line: str) -> bool:
    """コメント行かどうか。"""
    stripped = line.lstrip()
    return stripped.startswith('"') or stripped.startswith("*")


def _is_blank_line(line: str) -> bool:
    """空行かどうか。"""
    return line.strip() == ""


# ---------------------------------------------------------------------------
# カテゴリ1: エラーハンドリング漏れ
# ---------------------------------------------------------------------------

def _check_error_handling(
    lines: list[str], common_class_names: set[str], config: dict,
) -> tuple[int, list[str]]:
    """エラーハンドリング漏れを検出し、減点を返す。"""
    cfg = config.get("error_handling", {})
    max_deduction = config.get("max_deductions", {}).get("error_handling", 35)
    deduction = 0
    violations = []

    code_lines = [(i, line) for i, line in enumerate(lines, 1) if not _is_comment_line(line)]

    # SELECT後のSY-SUBRCチェック
    penalty_per = cfg.get("select_without_subrc", 5)
    for idx, (line_no, line) in enumerate(code_lines):
        upper = line.upper().strip()
        if re.match(r"^\s*SELECT\s", line, re.IGNORECASE) and "INTO" in upper:
            # 後続10行以内にsy-subrcチェックがあるか
            found = False
            for j in range(idx + 1, min(idx + 11, len(code_lines))):
                if "SY-SUBRC" in code_lines[j][1].upper():
                    found = True
                    break
            if not found:
                deduction += penalty_per
                violations.append(
                    f"[ERROR_HANDLING] line {line_no}: SELECT後にSY-SUBRCチェックがありません"
                )

    # 共通クラス呼出し後のBAPIRET2チェック
    penalty_per = cfg.get("common_class_without_check", 5)
    for idx, (line_no, line) in enumerate(code_lines):
        upper = line.upper()
        # 型参照（TYPE zcl_xxx=>ty_xxx）はメソッド呼出しではないので除外
        if re.search(r"\bTYPE\s", upper):
            continue
        for cls_name in common_class_names:
            if cls_name in upper and ("=>" in upper or "->" in upper):
                # 後続10行以内にresult-type / rv_result / BAPIRET2チェックがあるか
                found = False
                for j in range(idx + 1, min(idx + 11, len(code_lines))):
                    check_line = code_lines[j][1].upper()
                    if "RESULT" in check_line and ("TYPE" in check_line or "'E'" in check_line):
                        found = True
                        break
                    if "BAPIRET2" in check_line or "SY-SUBRC" in check_line:
                        found = True
                        break
                if not found:
                    deduction += penalty_per
                    violations.append(
                        f"[ERROR_HANDLING] line {line_no}: {cls_name} 呼出し後にBAPIRET2チェックがありません"
                    )
                break  # 同じ行で複数クラスマッチは1件としてカウント

    # TRY-CATCHの存在確認（ファイルI/O等）
    # 簡易チェック: ファイルI/O系の呼出しがTRY-CATCH外にあるか
    penalty_per = cfg.get("external_call_without_try", 3)
    in_try = False
    for line_no, line in code_lines:
        upper = line.upper().strip()
        if upper.startswith("TRY"):
            in_try = True
        elif upper.startswith("ENDTRY"):
            in_try = False
        elif not in_try:
            if "GUI_UPLOAD" in upper or "GUI_DOWNLOAD" in upper or "OPEN DATASET" in upper:
                deduction += penalty_per
                violations.append(
                    f"[ERROR_HANDLING] line {line_no}: 外部呼出しがTRY-CATCH外にあります"
                )

    # MESSAGE文の存在確認
    penalty = cfg.get("no_message_statement", 10)
    has_message = any(
        re.search(r"\bMESSAGE\b", line, re.IGNORECASE)
        for _, line in code_lines
    )
    if not has_message:
        deduction += penalty
        violations.append("[ERROR_HANDLING] MESSAGE文が1つもありません")

    return min(deduction, max_deduction), violations


# ---------------------------------------------------------------------------
# カテゴリ2: 命名規約違反
# ---------------------------------------------------------------------------

def _check_naming(lines: list[str], config: dict) -> tuple[int, list[str]]:
    """命名規約違反を検出し、減点を返す。"""
    cfg = config.get("naming_convention", {})
    max_deduction = config.get("max_deductions", {}).get("naming_convention", 25)
    deduction = 0
    violations = []

    # DATA宣言の変数名を収集
    total_vars = 0
    compliant_vars = 0

    for line_no, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        # DATA: xxx TYPE ... / DATA xxx TYPE ...
        m = re.match(r"\s*DATA[:\s]+(\w+)\s", line, re.IGNORECASE)
        if m:
            var_name = m.group(1).upper()
            if var_name == "DATA":
                continue
            total_vars += 1
            if any(var_name.startswith(p) for p in NAMING_PREFIXES):
                compliant_vars += 1

    # 遵守率に基づく減点
    if total_vars > 0:
        ratio = compliant_vars / total_vars
        thresholds = cfg.get("compliance_thresholds", [
            {"min_ratio": 0.9, "deduction": 0},
            {"min_ratio": 0.7, "deduction": 10},
            {"min_ratio": 0.5, "deduction": 20},
            {"min_ratio": 0.0, "deduction": 25},
        ])
        for t in thresholds:
            if ratio >= t["min_ratio"]:
                deduction += t["deduction"]
                if t["deduction"] > 0:
                    violations.append(
                        f"[NAMING] 命名規約遵守率 {ratio:.0%} ({compliant_vars}/{total_vars})"
                    )
                break

    # インライン宣言チェック
    penalty_per = cfg.get("inline_declaration", 3)
    for line_no, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if re.search(r"\bDATA\(", line, re.IGNORECASE):
            deduction += penalty_per
            violations.append(
                f"[NAMING] line {line_no}: インライン宣言 DATA( を検出。DATA文で事前宣言してください"
            )

    # CALL METHOD 使用チェック
    penalty_per = cfg.get("call_method_usage", 5)
    for line_no, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if re.search(r"\bCALL\s+METHOD\b", line, re.IGNORECASE):
            deduction += penalty_per
            violations.append(
                f"[NAMING] line {line_no}: CALL METHOD を検出。メソッド短縮形（obj=>method( ) / obj->method( )）を使用してください"
            )

    return min(deduction, max_deduction), violations


# ---------------------------------------------------------------------------
# カテゴリ3: テンプレート準拠
# ---------------------------------------------------------------------------

def _check_template_compliance(
    lines: list[str], config: dict, spec_path: Path | None, start_dir: Path,
) -> tuple[int, list[str]]:
    """テンプレート準拠違反を検出し、減点を返す。"""
    cfg = config.get("template_compliance", {})
    max_deduction = config.get("max_deductions", {}).get("template_compliance", 20)
    deduction = 0
    violations = []

    # 任意テキストメッセージ
    penalty_per = cfg.get("arbitrary_message", 10)
    for line_no, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if re.search(r"\bMESSAGE\s+'", line, re.IGNORECASE):
            deduction += penalty_per
            violations.append(
                f"[TEMPLATE] line {line_no}: 任意テキストメッセージ MESSAGE '...' を検出。T100を使用してください"
            )

    # 共通クラス未使用（spec宣言あり）
    if spec_path and spec_path.is_file():
        penalty = cfg.get("unused_declared_class", 10)
        spec_doc = load_yaml_from_md(spec_path)
        spec = spec_doc.get("spec", {})
        cc_app = spec.get("common_class_applicability") or []

        declared_classes = set()
        for entry in cc_app:
            for rule in entry.get("rules") or []:
                cls = rule.get("class", "")
                if cls:
                    declared_classes.add(cls.upper())

        if declared_classes:
            source_upper = "\n".join(lines).upper()
            # 共通クラス自身のソースは除外（ファイル名でチェック）
            common_names = _load_common_class_names(start_dir)
            for cls in declared_classes:
                if cls not in source_upper and cls not in common_names:
                    deduction += penalty
                    violations.append(
                        f"[TEMPLATE] {cls} が spec で宣言されていますがソース内に参照がありません"
                    )

    return min(deduction, max_deduction), violations


# ---------------------------------------------------------------------------
# カテゴリ4: 実行効率（ルール S7 — Design Rationality Principle）
# ---------------------------------------------------------------------------

def _check_runtime_efficiency(lines: list[str], config: dict) -> tuple[int, list[str]]:
    """実行効率に関する違反を検出し、減点を返す。

    検出対象:
      - SELECT * 使用（DB→AS間の不要カラム転送）
      - MOVE-CORRESPONDING 使用（実行時フィールドマッチング）
      - CATCH cx_root 使用（想定外例外の握りつぶし）
      - 1 FORM 内に複数 @STEP（メモリスコープ肥大化）
    """
    cfg = config.get("runtime_efficiency", {})
    max_deduction = config.get("max_deductions", {}).get("runtime_efficiency", 20)
    deduction = 0
    violations = []

    code_lines = [(i, line) for i, line in enumerate(lines, 1) if not _is_comment_line(line)]

    # テストクラス範囲を事前計算
    # DEFINITION FOR TESTING でテストクラス名を収集し、
    # 同名クラスの IMPLEMENTATION 部分もテストコードとして扱う
    test_class_names: set[str] = set()
    test_ranges: list[tuple[int, int]] = []
    current_class_start: int | None = None
    current_class_is_test = False

    for line_no, line in enumerate(lines, 1):
        upper = line.upper()
        # CLASS xxx DEFINITION FOR TESTING → テストクラス名を記録
        m_def = re.match(r"\s*CLASS\s+(\w+)\s+DEFINITION\b.*FOR\s+TESTING\b", line, re.IGNORECASE)
        if m_def:
            test_class_names.add(m_def.group(1).upper())
            current_class_start = line_no
            current_class_is_test = True
        # CLASS xxx IMPLEMENTATION → テストクラスの IMPLEMENTATION 部分か判定
        elif not m_def:
            m_impl = re.match(r"\s*CLASS\s+(\w+)\s+IMPLEMENTATION\b", line, re.IGNORECASE)
            if m_impl:
                current_class_start = line_no
                current_class_is_test = m_impl.group(1).upper() in test_class_names
            # CLASS xxx DEFINITION (非テスト)
            elif re.match(r"\s*CLASS\s+\w+\s+DEFINITION\b", line, re.IGNORECASE):
                current_class_start = line_no
                current_class_is_test = False
        # ENDCLASS
        if re.match(r"\s*ENDCLASS\b", line, re.IGNORECASE) and current_class_start is not None:
            if current_class_is_test:
                test_ranges.append((current_class_start, line_no))
            current_class_start = None
            current_class_is_test = False

    def _in_test_code(ln: int) -> bool:
        return any(s <= ln <= e for s, e in test_ranges)

    # --- SELECT * 検出 ---
    penalty_per = cfg.get("select_star", 5)
    for line_no, line in code_lines:
        # SELECT * FROM ... / SELECT SINGLE * FROM ...
        # テストコード内でも SELECT * は非効率なので検出対象とする
        if re.search(r"\bSELECT\s+(SINGLE\s+)?\*\s+FROM\b", line, re.IGNORECASE):
            deduction += penalty_per
            violations.append(
                f"[RUNTIME_EFFICIENCY] line {line_no}: SELECT * を検出。"
                "plan.md の fields_used に基づきフィールドを明示してください（ルール S7 / AP-01）"
            )

    # --- MOVE-CORRESPONDING 検出 ---
    penalty_per = cfg.get("move_corresponding", 3)
    for line_no, line in code_lines:
        if re.search(r"\bMOVE-CORRESPONDING\b", line, re.IGNORECASE):
            deduction += penalty_per
            violations.append(
                f"[RUNTIME_EFFICIENCY] line {line_no}: MOVE-CORRESPONDING を検出。"
                "フィールド単位の明示的転送に書き換えてください（ルール S7 / AP-02）"
            )

    # --- CATCH cx_root 検出（テストコード内は除外）---
    penalty_per = cfg.get("broad_catch_cx_root", 5)
    for line_no, line in code_lines:
        if _in_test_code(line_no):
            continue
        if re.search(r"\bCATCH\s+cx_root\b", line, re.IGNORECASE):
            deduction += penalty_per
            violations.append(
                f"[RUNTIME_EFFICIENCY] line {line_no}: CATCH cx_root を検出。"
                "発生しうる個別例外クラスを指定してください（ルール S7 / AP-04）"
            )

    # --- 1 FORM 内に複数 @STEP 検出 ---
    penalty_per = cfg.get("steps_per_form_exceeded", 5)
    form_name = ""
    form_start_line = 0
    step_count = 0
    step_names: list[str] = []

    for line_no, line in enumerate(lines, 1):
        stripped = line.strip().upper()

        # FORM 開始
        m = re.match(r"\s*FORM\s+(\w+)", line, re.IGNORECASE)
        if m:
            form_name = m.group(1)
            form_start_line = line_no
            step_count = 0
            step_names = []

        # @STEP アノテーション（コメント行内）
        if re.search(r"@STEP\s+\w+", line, re.IGNORECASE):
            step_count += 1
            step_m = re.search(r"@STEP\s+(\w+)", line, re.IGNORECASE)
            if step_m:
                step_names.append(step_m.group(1))

        # ENDFORM — FORM 終了時に判定
        if re.match(r"\s*ENDFORM\b", line, re.IGNORECASE):
            if step_count > 1:
                deduction += penalty_per
                names_str = ", ".join(step_names)
                violations.append(
                    f"[RUNTIME_EFFICIENCY] FORM {form_name} (line {form_start_line}): "
                    f"{step_count} 個の @STEP を検出 ({names_str})。"
                    "processing_steps と 1:1 で FORM を分離してください（ルール S7 / AP-03）"
                )
            form_name = ""
            step_count = 0
            step_names = []

    return min(deduction, max_deduction), violations


# ---------------------------------------------------------------------------
# カテゴリ5: 保守性
# ---------------------------------------------------------------------------

def _check_maintainability(lines: list[str], config: dict) -> tuple[int, list[str]]:
    """保守性違反を検出し、減点を返す。"""
    cfg = config.get("maintainability", {})
    max_deduction = config.get("max_deductions", {}).get("maintainability", 20)
    deduction = 0
    violations = []

    # コメント率
    total = len(lines)
    if total > 0:
        comment_count = sum(1 for line in lines if _is_comment_line(line))
        ratio = comment_count / total

        thresholds = cfg.get("comment_ratio", [
            {"min_ratio": 0.10, "deduction": 0},
            {"min_ratio": 0.05, "deduction": 5},
            {"min_ratio": 0.00, "deduction": 10},
        ])
        for t in thresholds:
            if ratio >= t["min_ratio"]:
                deduction += t["deduction"]
                if t["deduction"] > 0:
                    violations.append(
                        f"[MAINTAINABILITY] コメント率 {ratio:.1%} (推奨: 10%以上)"
                    )
                break

    # 過長メソッド
    threshold = cfg.get("long_method_threshold", 100)
    penalty_per = cfg.get("long_method_deduction", 5)
    method_start = None
    method_name = ""
    for line_no, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        upper = line.upper().strip()
        m = re.match(r"\s*METHOD\s+(\w+)", line, re.IGNORECASE)
        if m and "ENDMETHOD" not in upper:
            method_start = line_no
            method_name = m.group(1)
        elif upper.startswith("ENDMETHOD") and method_start is not None:
            length = line_no - method_start
            if length > threshold:
                deduction += penalty_per
                violations.append(
                    f"[MAINTAINABILITY] METHOD {method_name} が {length} 行（上限: {threshold}行）"
                )
            method_start = None

    return min(deduction, max_deduction), violations


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def score_file(
    file_path: Path,
    config: dict,
    common_class_names: set[str],
    spec_path: Path | None = None,
) -> dict[str, Any]:
    """単一ファイルのスコアリングを実行する。"""
    source = _read_source(file_path)
    if not source:
        return {"file": str(file_path), "score": 0, "error": "Cannot read file"}

    lines = source.splitlines()
    all_violations = []

    d1, v1 = _check_error_handling(lines, common_class_names, config)
    d2, v2 = _check_naming(lines, config)
    d3, v3 = _check_template_compliance(
        lines, config, spec_path, file_path.parent,
    )
    d4, v4 = _check_runtime_efficiency(lines, config)
    d5, v5 = _check_maintainability(lines, config)

    all_violations.extend(v1)
    all_violations.extend(v2)
    all_violations.extend(v3)
    all_violations.extend(v4)
    all_violations.extend(v5)

    total_deduction = d1 + d2 + d3 + d4 + d5
    final_score = max(0, 100 - total_deduction)

    return {
        "file": str(file_path),
        "score": final_score,
        "deductions": {
            "error_handling": d1,
            "naming_convention": d2,
            "template_compliance": d3,
            "runtime_efficiency": d4,
            "maintainability": d5,
        },
        "total_deduction": total_deduction,
        "violations": all_violations,
    }


def main() -> None:
    original_argv = sys.argv.copy()

    step_id = None
    if "--step-id" in sys.argv:
        idx = sys.argv.index("--step-id")
        if idx + 1 < len(sys.argv):
            step_id = sys.argv[idx + 1]
            sys.argv = sys.argv[:idx] + sys.argv[idx + 2:]

    if step_id is None:
        print(
            "ERROR: --step-id is required.\n"
            "Usage: python3 sap_quality_score.py <source> --step-id <step>\n"
            "See: CLAUDE_WORKFLOW_SAP.md",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python3 sap_quality_score.py <source_file_or_dir> --step-id <step>\n"
            "  python3 sap_quality_score.py <source_file_or_dir> --spec <spec.md> --step-id <step>",
            file=sys.stderr,
        )
        sys.exit(1)

    target = Path(sys.argv[1])
    spec_path = None
    if "--spec" in sys.argv:
        idx = sys.argv.index("--spec")
        if idx + 1 < len(sys.argv):
            spec_path = Path(sys.argv[idx + 1])

    # 設定読み込み
    search_start = target if target.is_dir() else target.parent
    config_path = _find_config(search_start)
    if config_path:
        config_data = load_yaml_file(config_path)
        config = config_data.get("quality_score", {})
    else:
        print("Warning: quality_score_config.yaml not found. Using defaults.", file=sys.stderr)
        config = {}

    threshold = config.get("pass_threshold", 85)
    common_class_names = _load_common_class_names(search_start)

    # ファイル収集
    files = []
    if target.is_file():
        files.append(target)
    elif target.is_dir():
        for ext in ("*.clas.abap", "*.prog.abap", "*.fugr.abap", "*.intf.abap"):
            files.extend(target.rglob(ext))

    if not files:
        print(f"No ABAP source files found in {target}", file=sys.stderr)
        sys.exit(1)

    all_pass = True
    all_results = []
    for f in files:
        result = score_file(f, config, common_class_names, spec_path)
        all_results.append(result)

        print(f"\n=== Quality Score Report: {result['file']} ===\n")
        print("Base Score: 100\n")

        d = result["deductions"]
        print(f"1. Error Handling:       -{d['error_handling']}")
        print(f"2. Naming Convention:    -{d['naming_convention']}")
        print(f"3. Template Compliance:  -{d['template_compliance']}")
        print(f"4. Runtime Efficiency:   -{d['runtime_efficiency']}")
        print(f"5. Maintainability:      -{d['maintainability']}")

        score = result["score"]
        status = "PASS" if score >= threshold else "FAIL"
        print(f"\nTotal Deductions: -{result['total_deduction']}")
        print(f"Final Score: {score}/100  {status} (threshold: {threshold})")

        if result["violations"]:
            print("\nViolations:")
            for v in result["violations"]:
                print(f"  {v}")

        if score < threshold:
            all_pass = False

    if step_id:
        # Derive feature_dir from --spec path or walk up from target
        feature_dir_path = None
        if spec_path:
            feature_dir_path = spec_path.parent
        if not feature_dir_path:
            d = target.resolve()
            for _ in range(10):
                if d.parent.name == "specs":
                    feature_dir_path = d
                    break
                if d.parent == d:
                    break
                d = d.parent
            if not feature_dir_path:
                feature_dir_path = target.parent

        # Summarize across all files
        scores_str = ", ".join(
            f"{Path(r['file']).name}={r['score']}"
            for r in all_results
        ) if len(all_results) <= 5 else f"{len(all_results)} files"
        options_list = []
        if spec_path:
            options_list.append(f"--spec {spec_path}")
        write_evidence(
            feature_dir=str(feature_dir_path),
            step_id=step_id,
            tool_name="sap_quality_score.py",
            command=" ".join(original_argv),
            options=options_list,
            result_summary=f"{'PASS' if all_pass else 'FAIL'} threshold={threshold} {scores_str}",
        )

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
