"""
sap_common_class_lint.py -- 共通クラス使用準拠チェック（ネガティブチェック専用）

common_class_rules.yaml の forbidden_patterns に基づき、
ABAPソース内の禁止パターンを検出する。
また、共通クラスメソッド呼び出し時の未定義パラメータを検出する。

共通クラス自身のソース（classes[].name に該当するファイル）はチェック対象外。

ポジティブチェック（共通クラスの使用有無の判定）は本スクリプトでは行わない。
共通クラス使用の判断は Step 6 の実装プロセス内で AI が自律的に行い、
不使用の場合は tests/common_class_decisions.yaml に理由を記録する。
詳細は phase4_execute.md の「共通クラス判断プロセス」を参照。

Usage:
  python3 extensions/sap/tools/sap_common_class_lint.py <source_file_or_dir> --step-id <step>

終了コード:
  0: 違反なし
  1: 違反あり
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from tool_evidence_writer import write_evidence

sys.path.insert(0, str(Path(__file__).parent))
from sap_evidence_common import load_yaml_file


def _get_method_names(methods_list: list) -> list[str]:
    """Extract method names from methods list (supports both string and dict format)."""
    names = []
    for m in methods_list or []:
        if isinstance(m, str):
            names.append(m)
        elif isinstance(m, dict):
            names.append(m.get("name", ""))
    return [n for n in names if n]


def _find_rules_file(start_dir: Path) -> Path | None:
    """common_class_rules.yaml を探す。"""
    for parent in [start_dir] + list(start_dir.parents):
        candidate = parent / "extensions" / "sap" / "config" / "common_class_rules.yaml"
        if candidate.is_file():
            return candidate
    return None


def _load_common_class_rules(rules_path: Path) -> list[dict[str, Any]]:
    """common_class_rules.yaml からルールをロードする。"""
    data = load_yaml_file(rules_path)
    return data.get("common_class_rules") or []


def _collect_excluded_names(rules: list[dict]) -> set[str]:
    """共通クラス名の一覧を収集する（lint除外用）。"""
    names = set()
    for rule in rules:
        for cls in rule.get("classes") or []:
            name = cls.get("name", "")
            if name:
                names.add(name.lower())
    return names


def _is_excluded_file(file_path: Path, excluded_names: set[str]) -> bool:
    """ファイルが共通クラス自身のソースかどうかを判定する。"""
    stem = file_path.stem.split(".")[0].lower()
    return stem in excluded_names


def _collect_class_names_for_rule(rule: dict) -> str:
    """ルールの classes から表示用クラス名リストを作成する。"""
    names = []
    for cls in rule.get("classes") or []:
        name = cls.get("name", "")
        if name:
            method_names = _get_method_names(cls.get("methods", []))
            if method_names:
                names.append(f"{name}({', '.join(method_names)})")
            else:
                names.append(name)
    return " / ".join(names)


def lint_file(
    file_path: Path,
    rules: list[dict],
    excluded_names: set[str],
) -> list[dict[str, Any]]:
    """単一ファイルに対してネガティブチェックを実行する。"""
    if _is_excluded_file(file_path, excluded_names):
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        try:
            content = file_path.read_text(encoding="cp932")
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Cannot read {file_path}: {e}", file=sys.stderr)
            return []

    lines = content.splitlines()
    violations = []

    for rule in rules:
        forbidden = rule.get("forbidden_patterns") or []
        if not forbidden:
            continue

        rule_id = rule.get("id", "")
        class_names = _collect_class_names_for_rule(rule)

        for pattern_str in forbidden:
            for line_no, line in enumerate(lines, start=1):
                # コメント行はスキップ
                stripped = line.lstrip()
                if stripped.startswith('"') or stripped.startswith("*"):
                    continue

                if pattern_str.upper() in line.upper():
                    violations.append({
                        "rule_id": rule_id,
                        "file": str(file_path),
                        "line": line_no,
                        "pattern": pattern_str,
                        "class_names": class_names,
                        "source_line": line.rstrip(),
                    })

    return violations


def lint_path(
    target: Path,
    rules: list[dict],
    excluded_names: set[str],
) -> list[dict[str, Any]]:
    """ファイルまたはディレクトリに対してネガティブチェックを実行する。"""
    all_violations = []

    if target.is_file():
        all_violations.extend(lint_file(target, rules, excluded_names))
    elif target.is_dir():
        for ext in ("*.clas.abap", "*.prog.abap", "*.fugr.abap", "*.intf.abap"):
            for f in target.rglob(ext):
                all_violations.extend(lint_file(f, rules, excluded_names))
    else:
        print(f"Error: {target} is not a file or directory", file=sys.stderr)

    return all_violations


# ---------------------------------------------------------------------------
# パラメータ検証: common_class_rules.yaml で定義されたパラメータとの突合
# ---------------------------------------------------------------------------


def _extract_method_params(rules: list[dict]) -> dict[str, dict[str, set[str]]]:
    """Build a dict: { CLASS_NAME: { METHOD_NAME: {param_names} } } from rules."""
    result: dict[str, dict[str, set[str]]] = {}
    for rule in rules:
        for cls in rule.get("classes") or []:
            cls_name = cls.get("name", "").upper()
            if not cls_name:
                continue
            if cls_name not in result:
                result[cls_name] = {}
            for m in cls.get("methods") or []:
                if isinstance(m, dict):
                    method_name = m.get("name", "").upper()
                    params = set()
                    for p in m.get("parameters") or []:
                        pname = p.get("name", "").upper()
                        if pname and p.get("direction", "").upper() != "RETURNING":
                            params.add(pname)
                    if method_name:
                        result[cls_name][method_name] = params
                elif isinstance(m, str):
                    # Old format (string only) — no parameter info
                    result[cls_name][m.upper()] = set()
    return result


def _read_source_content(file_path: Path) -> str:
    """Read source file content."""
    try:
        return file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        try:
            return file_path.read_text(encoding="cp932")
        except (OSError, UnicodeDecodeError):
            return ""


def _resolve_ref_types(lines: list[str]) -> dict[str, str]:
    """Resolve variable -> class name from TYPE REF TO declarations."""
    ref_map: dict[str, str] = {}
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('"') or stripped.startswith("*"):
            continue
        # DATA lo_xxx TYPE REF TO zcl_xxx
        m = re.match(
            r"\s*DATA[:\s]+(\w+)\s+TYPE\s+REF\s+TO\s+(\w+)",
            line,
            re.IGNORECASE,
        )
        if m:
            var_name = m.group(1).upper()
            class_name = m.group(2).upper()
            ref_map[var_name] = class_name
    return ref_map


def check_parameters(
    target: Path,
    rules: list[dict],
    excluded_names: set[str],
) -> list[dict[str, Any]]:
    """Check that method call parameters match the YAML definitions."""
    method_params = _extract_method_params(rules)
    if not method_params:
        return []

    violations: list[dict[str, Any]] = []

    files: list[Path] = []
    if target.is_file():
        files.append(target)
    elif target.is_dir():
        for ext in ("*.clas.abap", "*.prog.abap", "*.fugr.abap", "*.intf.abap"):
            files.extend(target.rglob(ext))

    for file_path in files:
        if _is_excluded_file(file_path, excluded_names):
            continue
        content = _read_source_content(file_path)
        if not content:
            continue
        lines = content.splitlines()
        ref_map = _resolve_ref_types(lines)

        # Scan for method calls: CLASS=>METHOD( or variable->METHOD(
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            if stripped.startswith('"') or stripped.startswith("*"):
                i += 1
                continue

            upper = line.upper()

            # Match patterns: CLASSNAME=>METHOD( or VARIABLE->METHOD(
            call_match = re.search(
                r"(\w+)\s*(=>|->)\s*(\w+)\s*\(",
                upper,
            )
            if not call_match:
                i += 1
                continue

            caller = call_match.group(1)
            arrow = call_match.group(2)
            method_name = call_match.group(3)
            call_line_no = i + 1

            # Resolve class name
            if arrow == "=>":
                class_name = caller
            else:
                # instance call: resolve from ref_map
                class_name = ref_map.get(caller, "")

            if class_name not in method_params:
                i += 1
                continue

            if method_name not in method_params[class_name]:
                i += 1
                continue

            valid_params = method_params[class_name][method_name]
            if not valid_params:
                # No parameter definitions available (old format)
                i += 1
                continue

            # Collect the full call text from ( to ).
            # Find the opening paren position in the current line
            paren_start = upper.find("(", call_match.start())
            call_text = line[paren_start + 1:]  # text after (
            current_line = i

            # Check if closing ). is on the same line or multi-line
            while ")." not in call_text.upper() and ")" not in call_text.upper():
                current_line += 1
                if current_line >= len(lines):
                    break
                next_line = lines[current_line]
                next_stripped = next_line.lstrip()
                if next_stripped.startswith('"') or next_stripped.startswith("*"):
                    continue
                call_text += " " + next_line

            # Extract parameter names from call_text
            used_params = set()
            for pm in re.finditer(r"(\w+)\s*=\s*(?!=)", call_text):
                param_name = pm.group(1).upper()
                used_params.add(param_name)

            # Check for undefined parameters
            for param in used_params:
                if param not in valid_params:
                    violations.append({
                        "file": str(file_path),
                        "line": call_line_no,
                        "class": class_name,
                        "method": method_name,
                        "param": param,
                        "valid_params": sorted(valid_params),
                    })

            i = current_line + 1 if current_line > i else i + 1

    return violations


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
            "Usage: python3 sap_common_class_lint.py <source> --step-id S1-C1\n"
            "See: CLAUDE_WORKFLOW_SAP.md Step S1-C1",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(sys.argv) < 2:
        print(
            "Usage:\n"
            "  python3 sap_common_class_lint.py <source_file_or_dir> --step-id <step>",
            file=sys.stderr,
        )
        sys.exit(1)

    target = Path(sys.argv[1])

    # common_class_rules.yaml を探す
    search_start = target if target.is_dir() else target.parent
    rules_path = _find_rules_file(search_start)
    if not rules_path:
        print("Error: common_class_rules.yaml not found", file=sys.stderr)
        sys.exit(1)

    rules = _load_common_class_rules(rules_path)
    excluded_names = _collect_excluded_names(rules)

    has_error = False

    # --- ネガティブチェック（常に実行）---
    violations = lint_path(target, rules, excluded_names)
    if violations:
        print("=== Negative Check: forbidden pattern violations ===")
        for v in violations:
            print(
                f'ERROR [{v["rule_id"]}] {v["file"]}:{v["line"]}'
                f' -- "{v["pattern"]}" の直接使用を検出。'
                f'{v["class_names"]} のメソッドを使用してください。'
            )
            print(f"  > {v['source_line']}")
        print(f"{len(violations)} violation(s) found.\n")
        has_error = True
    else:
        print("=== Negative Check: PASS (no forbidden patterns found) ===\n")

    # --- パラメータ検証（常に実行）---
    param_violations = check_parameters(target, rules, excluded_names)
    if param_violations:
        print("=== Parameter Check: undefined parameter violations ===")
        for v in param_violations:
            valid_list = ", ".join(v["valid_params"])
            print(
                f'ERROR {v["file"]}:{v["line"]}'
                f' \u2014 {v["class"]}=>{v["method"]}() に未定義パラメータ "{v["param"]}" を検出。'
                f" 有効なパラメータ: [{valid_list}]"
            )
        print(f"{len(param_violations)} parameter violation(s) found.\n")
        has_error = True
    else:
        print("=== Parameter Check: PASS (no undefined parameters found) ===\n")

    if step_id:
        # Derive feature_dir from target path
        feature_dir_path = None
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

        total_violations = len(violations) + len(param_violations)
        write_evidence(
            feature_dir=str(feature_dir_path),
            step_id=step_id,
            tool_name="sap_common_class_lint.py",
            command=" ".join(original_argv),
            options=[],
            result_summary=f"{'FAIL' if has_error else 'PASS'} violations={total_violations}",
        )

    sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()
