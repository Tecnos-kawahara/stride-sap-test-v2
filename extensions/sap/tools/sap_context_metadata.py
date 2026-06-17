"""
sap_context_metadata.py — sap_context.md のメタデータ自動生成

DDL / ABAP ソース / data_preview.js からテーブル・選択画面のメタデータを生成し、
sap_context.md の YAML メタデータセクションに書き込む。

Usage:
  # Phase 2 前準備 R3: テーブルメタデータ生成（DDL + data_preview）
  python3 extensions/sap/tools/sap_context_metadata.py specs/<feature>/ --tables MCHB MAKT MARA

  # Phase 2 前準備 2P-A1 / Phase 4 S1-B1: 選択画面メタデータ生成（ABAP ソースから）
  python3 extensions/sap/tools/sap_context_metadata.py specs/<feature>/ --from-source

  # Phase 2.2: 選択画面メタデータ生成（spec.md から推定）
  python3 extensions/sap/tools/sap_context_metadata.py specs/<feature>/ --from-spec
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from tool_evidence_writer import write_evidence


def _safe_print(text: str) -> None:
    """Print text safely on Windows console (UTF-8 forced)."""
    try:
        sys.stdout.buffer.write((text + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()
    except (AttributeError, UnicodeEncodeError):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))


def _find_template_root(feature_dir: Path) -> Path:
    """テンプレートルート（.env がある場所）を探索"""
    d = feature_dir.resolve()
    for _ in range(10):
        if (d / ".env").is_file():
            return d
        parent = d.parent
        if parent == d:
            break
        d = parent
    return feature_dir.resolve().parent.parent


def _find_src_dir(feature_dir: Path) -> Path:
    """src/ ディレクトリを上方探索"""
    d = feature_dir.resolve()
    for _ in range(10):
        candidate = d / "src"
        if candidate.is_dir():
            return candidate
        parent = d.parent
        if parent == d:
            break
        d = parent
    return feature_dir.resolve().parent.parent / "src"


def _run_data_preview(template_root: Path, table: str, rows: int = 1) -> dict[str, str]:
    """data_preview.js を実行してフィールドの日本語ラベルを取得する。

    data_preview.js の出力ヘッダ行からカラム名と Columns: の description を抽出。
    """
    dp_js = template_root / "extensions" / "sap" / "tools" / "data_preview.js"
    if not dp_js.is_file():
        # テンプレートルートからの相対パスで再探索
        for parent in [template_root] + list(template_root.parents):
            candidate = parent / "extensions" / "sap" / "tools" / "data_preview.js"
            if candidate.is_file():
                dp_js = candidate
                break

    if not dp_js.is_file():
        return {}

    try:
        # MCP adt_data_preview と同等の情報を得るために Node.js スクリプトを使う
        # ただし data_preview.js はヘッダに日本語ラベルを出さない
        # → 代わりに MCP の adt_data_preview レスポンスから取得する必要がある
        # ここではフォールバックとして空辞書を返す
        return {}
    except Exception:
        return {}


def parse_ddl_metadata(ddl_text: str) -> dict:
    """DDL テキストからテーブルメタデータを抽出する。

    Returns:
        {
            "ddl_label": "Batch Stocks",
            "key_fields": ["MATNR", "WERKS", ...],
            "quantity_fields": ["CLABS", "CINSM", ...],
            "all_fields": ["MATNR", "WERKS", "CLABS", ...],
        }
    """
    result: dict = {
        "ddl_label": "",
        "key_fields": [],
        "quantity_fields": [],
        "all_fields": [],
    }

    # @EndUserText.label
    label_match = re.search(r"@EndUserText\.label\s*:\s*'([^']*)'", ddl_text)
    if label_match:
        result["ddl_label"] = label_match.group(1)

    # key fields: "key fieldname : type"
    for m in re.finditer(r"key\s+(\w+)\s*:", ddl_text):
        fname = m.group(1).upper()
        if fname != "MANDT":
            result["key_fields"].append(fname)
            result["all_fields"].append(fname)

    # non-key fields: "fieldname : type" (not preceded by "key")
    for m in re.finditer(r"^\s+(\w+)\s+:\s+\w+", ddl_text, re.MULTILINE):
        fname = m.group(1).upper()
        if fname not in result["key_fields"] and fname != "MANDT" and not fname.startswith("INCLUDE"):
            if fname not in result["all_fields"]:
                result["all_fields"].append(fname)

    # quantity fields: @Semantics.quantity.unitOfMeasure
    lines = ddl_text.split("\n")
    for i, line in enumerate(lines):
        if "@Semantics.quantity" in line:
            # 次の行にフィールド定義がある
            for j in range(i + 1, min(i + 3, len(lines))):
                field_match = re.match(r"\s+(\w+)\s+:", lines[j])
                if field_match:
                    result["quantity_fields"].append(field_match.group(1).upper())
                    break

    return result


def parse_source_selection_screen(source_text: str) -> list[dict]:
    """ABAP ソースから選択画面定義を抽出する。

    Returns:
        [
            {"name": "S_WERKS", "type": "select-options", "table_field": "MCHB-WERKS", "obligatory": True},
            {"name": "P_ZERO", "type": "checkbox", "obligatory": False},
        ]
    """
    fields = []

    # SELECT-OPTIONS: s_xxx FOR table-field [OBLIGATORY]
    for m in re.finditer(
        r"(s_\w+)\s+FOR\s+(\w+-\w+)\s*(OBLIGATORY)?",
        source_text, re.IGNORECASE
    ):
        fields.append({
            "name": m.group(1).upper(),
            "type": "select-options",
            "table_field": m.group(2).upper(),
            "obligatory": bool(m.group(3)),
        })

    # PARAMETERS p_xxx TYPE ... AS CHECKBOX
    for m in re.finditer(
        r"PARAMETERS\s+(\w+)\s+.*?AS\s+CHECKBOX",
        source_text, re.IGNORECASE
    ):
        fields.append({
            "name": m.group(1).upper(),
            "type": "checkbox",
            "obligatory": False,
        })

    # PARAMETERS p_xxx TYPE ... (non-checkbox)
    for m in re.finditer(
        r"PARAMETERS\s+(\w+)\s+TYPE\s+(\w+)",
        source_text, re.IGNORECASE
    ):
        pname = m.group(1).upper()
        if not any(f["name"] == pname for f in fields):
            fields.append({
                "name": pname,
                "type": "parameter",
                "obligatory": False,
            })

    return fields


def parse_spec_selection_screen(spec: dict) -> list[dict]:
    """spec.md の spec_as_code.selection_screen から選択画面定義を読み取る。

    spec_as_code.selection_screen に構造化データがある場合はそれをそのまま使用する。
    """
    fields = []

    # spec_as_code.selection_screen から読み取り
    spec_as_code = spec.get("spec_as_code") or {}
    sel_screen = spec_as_code.get("selection_screen") or []

    for entry in sel_screen:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name", "").strip()
        if not name:
            continue
        fields.append({
            "name": name.upper(),
            "type": entry.get("type", "parameter"),
            "table_field": entry.get("table_field", ""),
            "obligatory": bool(entry.get("obligatory", False)),
            "label": entry.get("label", ""),
        })

    return fields


def generate_metadata_yaml(tables_meta: dict, selection_screen: list[dict]) -> str:
    """メタデータを YAML 文字列として生成する。"""
    lines = ["metadata:"]

    # tables
    lines.append("  tables:")
    if not tables_meta:
        lines.append("    {}")
    else:
        for tname, meta in tables_meta.items():
            lines.append(f"    {tname}:")
            label = meta.get("label", meta.get("ddl_label", ""))
            lines.append(f'      label: "{label}"')

            kf = meta.get("key_fields", [])
            kf_str = ", ".join(f'"{f}"' for f in kf)
            lines.append(f"      key_fields: [{kf_str}]")

            qf = meta.get("quantity_fields", [])
            if qf:
                qf_str = ", ".join(f'"{f}"' for f in qf)
                lines.append(f"      quantity_fields: [{qf_str}]")

            fields = meta.get("fields", {})
            if fields:
                lines.append("      fields:")
                for fname, finfo in fields.items():
                    flabel = finfo.get("label", "")
                    lines.append(f'        {fname}: {{ label: "{flabel}" }}')

    # selection_screen
    lines.append("")
    lines.append("  selection_screen:")
    if not selection_screen:
        lines.append("    []")
    else:
        for f in selection_screen:
            parts = [f'name: "{f["name"]}"', f'type: "{f["type"]}"']
            if f.get("table_field"):
                parts.append(f'table_field: "{f["table_field"]}"')
            parts.append(f'obligatory: {"true" if f.get("obligatory") else "false"}')
            if f.get("label"):
                parts.append(f'label: "{f["label"]}"')
            lines.append(f"    - {{ {', '.join(parts)} }}")

    return "\n".join(lines)


def update_sap_context_md(sap_context_path: Path, metadata_yaml: str) -> bool:
    """sap_context.md のメタデータセクションを更新する。"""
    if not sap_context_path.is_file():
        print(f"Error: {sap_context_path} not found", file=sys.stderr)
        return False

    content = sap_context_path.read_text(encoding="utf-8")

    # 既存のメタデータセクションを置換
    pattern = re.compile(
        r"```yaml\nmetadata:[\s\S]*?```",
        re.MULTILINE,
    )
    replacement = f"```yaml\n{metadata_yaml}\n```"

    if pattern.search(content):
        new_content = pattern.sub(replacement, content)
    else:
        # メタデータセクションがない場合は末尾に追加
        new_content = content.rstrip() + f"\n\n## メタデータ（ツール参照用）\n\n{replacement}\n"

    sap_context_path.write_text(new_content, encoding="utf-8")
    return True


def load_metadata_from_sap_context(sap_context_path: Path) -> dict:
    """sap_context.md から YAML メタデータを読み込む。"""
    if not sap_context_path.is_file():
        return {"tables": {}, "selection_screen": []}

    content = sap_context_path.read_text(encoding="utf-8")
    yaml_match = re.search(r"```yaml\r?\n(metadata:[\s\S]*?)```", content)
    if not yaml_match:
        return {"tables": {}, "selection_screen": []}

    try:
        import yaml
        parsed = yaml.safe_load(yaml_match.group(1)) or {}
        # YAML 構造が {"metadata": {"tables": ..., "selection_screen": ...}} の場合、metadata キーを展開
        if "metadata" in parsed and isinstance(parsed["metadata"], dict):
            parsed = parsed["metadata"]
        if "tables" not in parsed:
            parsed["tables"] = {}
        if "selection_screen" not in parsed:
            parsed["selection_screen"] = []
        return parsed
    except Exception:
        # PyYAML がない場合のフォールバック
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from sap_evidence_common import load_yaml_from_md
            # 簡易パース: sap_context.md 内の YAML ブロックを抽出
            import json
            # js-yaml は使えないので、簡易的に正規表現で解析
            return _parse_metadata_yaml_simple(yaml_match.group(1))
        except Exception:
            return {"tables": {}, "selection_screen": []}


def _parse_metadata_yaml_simple(yaml_text: str) -> dict:
    """PyYAML なしで metadata YAML を簡易パースする。"""
    result: dict = {"tables": {}, "selection_screen": []}

    current_table = ""
    current_section = ""
    in_fields = False

    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # tables セクション
        if re.match(r"tables:", stripped):
            current_section = "tables"
            continue
        if re.match(r"selection_screen:", stripped):
            current_section = "selection_screen"
            continue

        if current_section == "tables":
            # テーブル名行: "    MCHB:"
            tbl_match = re.match(r"(\w+):", stripped)
            if tbl_match and not stripped.startswith("label") and not stripped.startswith("key_") and not stripped.startswith("quantity") and not stripped.startswith("fields"):
                current_table = tbl_match.group(1)
                result["tables"][current_table] = {"label": "", "key_fields": [], "quantity_fields": [], "fields": {}}
                in_fields = False
                continue

            if current_table:
                # label
                lm = re.match(r'label:\s*"([^"]*)"', stripped)
                if lm:
                    result["tables"][current_table]["label"] = lm.group(1)
                    continue
                # key_fields
                kf = re.match(r'key_fields:\s*\[(.*)\]', stripped)
                if kf:
                    result["tables"][current_table]["key_fields"] = [
                        f.strip().strip('"') for f in kf.group(1).split(",") if f.strip()
                    ]
                    continue
                # quantity_fields
                qf = re.match(r'quantity_fields:\s*\[(.*)\]', stripped)
                if qf:
                    result["tables"][current_table]["quantity_fields"] = [
                        f.strip().strip('"') for f in qf.group(1).split(",") if f.strip()
                    ]
                    continue
                # fields:
                if stripped == "fields:":
                    in_fields = True
                    continue
                if in_fields:
                    fm = re.match(r'(\w+):\s*\{\s*label:\s*"([^"]*)"\s*\}', stripped)
                    if fm:
                        result["tables"][current_table]["fields"][fm.group(1)] = {"label": fm.group(2)}
                        continue

        if current_section == "selection_screen":
            # - { name: "S_WERKS", type: "select-options", ... }
            sm = re.match(r'-\s*\{(.*)\}', stripped)
            if sm:
                entry = {}
                for kv in re.finditer(r'(\w+):\s*"([^"]*)"', sm.group(1)):
                    entry[kv.group(1)] = kv.group(2)
                for kv in re.finditer(r'(\w+):\s*(true|false)', sm.group(1)):
                    entry[kv.group(1)] = kv.group(2) == "true"
                if entry.get("name"):
                    result["selection_screen"].append(entry)

    return result


def main():
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
            "Usage: python3 sap_context_metadata.py specs/<feature>/ --tables --step-id 2P-B2\n"
            "       python3 sap_context_metadata.py specs/<feature>/ --from-spec --step-id 2-B4\n"
            "See: CLAUDE_WORKFLOW_SAP.md Step 2P-B2 / Step 2-B4",
            file=sys.stderr,
        )
        sys.exit(1)

    args = sys.argv[1:]
    if not args:
        print(
            "Usage:\n"
            "  python3 sap_context_metadata.py specs/<feature>/ --tables [TABLE1 TABLE2 ...] --step-id 2P-B2\n"
            "  python3 sap_context_metadata.py specs/<feature>/ --from-source --step-id 2P-B2\n"
            "  python3 sap_context_metadata.py specs/<feature>/ --from-spec\n"
            "\n"
            "  --tables without arguments: auto-detect from sap_context.md R3 markdown table\n",
            file=sys.stderr,
        )
        sys.exit(1)

    feature_dir = Path(args[0])
    flags = set()
    table_names = []
    has_tables_flag = False
    i = 1
    while i < len(args):
        if args[i] == "--tables":
            has_tables_flag = True
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                table_names.append(args[i].upper())
                i += 1
        elif args[i].startswith("--"):
            flags.add(args[i])
            i += 1
        else:
            i += 1

    sap_context_path = feature_dir / "implementation-details" / "sap_context.md"

    # --tables 引数なし: sap_context.md R4 マークダウンテーブルからテーブル名を自動検出
    if has_tables_flag and not table_names:
        if sap_context_path.is_file():
            content = sap_context_path.read_text(encoding="utf-8")
            # R4 セクション内の「参照テーブル」サブセクションからテーブル名を抽出
            # 形式: "| T001 | 会社コード存在チェック | read.js | BUKRS (キー) |"
            # 「参照テーブル」サブセクション内のマークダウンテーブルのみ対象とし、
            # 「権限オブジェクト」「Released API」等の他テーブルは除外する
            r4_section = re.search(r"## R4.*?(?=\n## |\Z)", content, re.DOTALL)
            r4_text = r4_section.group(0) if r4_section else content
            # 「参照テーブル」サブセクションを抽出（次の ### まで）
            ref_table_section = re.search(r"### 参照テーブル.*?(?=\n### |\Z)", r4_text, re.DOTALL)
            parse_text = ref_table_section.group(0) if ref_table_section else r4_text
            for m in re.finditer(r"\|\s*([A-Z][A-Z0-9_]{2,})\s*\|", parse_text):
                tname = m.group(1).upper()
                if tname not in ("MANDT",) and tname not in table_names:
                    table_names.append(tname)
            if table_names:
                _safe_print(f"Auto-detected tables from sap_context.md: {', '.join(table_names)}")
            else:
                _safe_print("Warning: --tables specified but no tables found in sap_context.md R3 section")

    # 既存メタデータを読み込み
    existing = load_metadata_from_sap_context(sap_context_path)
    tables_meta = existing.get("tables", {})
    selection_screen = existing.get("selection_screen", [])

    # --tables: DDL + data_preview からテーブルメタデータを自動生成
    if table_names:
        _safe_print(f"Generating table metadata for: {', '.join(table_names)}")
        template_root = _find_template_root(feature_dir)
        tools_dir = Path(__file__).parent
        read_js = tools_dir / "read.js"
        dp_js = tools_dir / "data_preview.js"

        for tname in table_names:
            _safe_print(f"\n  --- {tname} ---")

            if tname not in tables_meta:
                tables_meta[tname] = {"label": "", "key_fields": [], "quantity_fields": [], "fields": {}}

            # 1. DDL 解析: sap_context.md の R4 セクションから key/quantity 情報を抽出
            # Phase 2 前準備 R3 で AI が adt_read_table_ddl の結果を記録しているはず
            content = sap_context_path.read_text(encoding="utf-8") if sap_context_path.is_file() else ""
            # パターン: "| MCHB | ... | KEY: MANDT, MATNR(matnr), WERKS(werks_d) / DATA: CLABS(labst) |"
            import re as _re
            tbl_row = _re.search(
                rf"\|\s*{tname}\s*\|[^|]*\|([^|]*)\|",
                content, _re.IGNORECASE
            )
            if tbl_row:
                field_info = tbl_row.group(1)
                # テーブルラベル（「用途」列から取得）
                label_match = _re.search(
                    rf"\|\s*{tname}\s*\|\s*([^|]+?)\s*\|",
                    content, _re.IGNORECASE
                )
                if label_match:
                    label_text = label_match.group(1).strip()
                    # 「ロット在庫（主テーブル）」→ 「ロット在庫」
                    label_clean = _re.sub(r"（.*?）|\(.*?\)", "", label_text).strip()
                    if label_clean:
                        tables_meta[tname]["label"] = label_clean
                # KEY フィールド抽出
                key_match = _re.search(r"KEY:\s*(.*?)(?:/|$)", field_info)
                if key_match:
                    key_text = key_match.group(1)
                    keys = [m.group(1).upper() for m in _re.finditer(r"(\w+)(?:\(\w+\))?", key_text) if m.group(1).upper() != "MANDT"]
                    tables_meta[tname]["key_fields"] = keys

                # DATA フィールド抽出 + quantity 推定
                data_match = _re.search(r"DATA:\s*(.*?)(?:\||$)", field_info)
                if data_match:
                    data_text = data_match.group(1)
                    # 「—」「--」以降のコメント部分を除去してからフィールド名を抽出
                    data_text = _re.split(r"\s*[—–-]{1,2}\s*", data_text)[0]
                    data_fields = []
                    for m in _re.finditer(r"([A-Z][A-Z0-9_]+)(?:\(\w+\))?", data_text, _re.IGNORECASE):
                        fname = m.group(1).upper()
                        if fname != "INCLUDE" and len(fname) >= 3:
                            data_fields.append(fname)
                    # DDL 補足事項から、このテーブルが quantity フィールドを持つか確認
                    # パターン: "MCHBの数量フィールドは@Semantics.quantity..." のように
                    # テーブル名が主語（@Semantics.quantity の前）に出現する場合のみ
                    qty_pattern = _re.compile(
                        rf"{tname}\s+の.*@Semantics\.quantity|{tname}.*数量フィールド",
                        _re.IGNORECASE
                    )
                    if qty_pattern.search(content):
                        tables_meta[tname]["quantity_fields"] = data_fields
                    elif not tables_meta[tname].get("quantity_fields"):
                        # 既存値がなければ空リストに（誤検知防止）
                        tables_meta[tname]["quantity_fields"] = []

                _safe_print(f"  key_fields: {tables_meta[tname].get('key_fields', [])}")
                _safe_print(f"  quantity_fields: {tables_meta[tname].get('quantity_fields', [])}")

            # 4. フィールドラベル取得（data_preview.js --column-labels）
            if dp_js.is_file():
                try:
                    result = subprocess.run(
                        ["node", str(dp_js), tname, "--column-labels"],
                        capture_output=True, text=True, timeout=30, encoding="utf-8",
                        cwd=str(template_root),
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        import json
                        # stderr に Warning が出る場合があるので stdout のみ使う
                        json_line = [l for l in result.stdout.strip().split("\n") if l.startswith("{")]
                        if json_line:
                            labels_map = json.loads(json_line[0])
                            for fname, flabel in labels_map.items():
                                fname_upper = fname.upper()
                                if fname_upper != "MANDT":
                                    tables_meta[tname].setdefault("fields", {})[fname_upper] = {"label": flabel}
                            _safe_print(f"  フィールドラベル: {len(labels_map)} 件取得")
                except (subprocess.TimeoutExpired, FileNotFoundError, OSError, json.JSONDecodeError) as e:
                    print(f"  フィールドラベル取得失敗: {e}", file=sys.stderr)

            meta = tables_meta[tname]
            field_count = len(meta.get("fields", {}))
            _safe_print(f"  label: {meta.get('label', '(none)')}")
            _safe_print(f"  fields: {field_count} 件")
            if field_count == 0:
                _safe_print(f"  WARNING: {tname} のフィールドラベルが0件です。SAP接続を確認し再実行してください。")

    # --from-source: ABAP ソースから選択画面を抽出
    if "--from-source" in flags:
        src_dir = _find_src_dir(feature_dir)
        print(f"Scanning ABAP sources in {src_dir}")
        for prog_file in src_dir.rglob("*.prog.abap"):
            source = prog_file.read_text(encoding="utf-8", errors="ignore")
            parsed = parse_source_selection_screen(source)
            if parsed:
                # 既存 selection_screen のラベルを保持しつつマージ
                existing_labels = {
                    s.get("name", "").upper(): s.get("label", "")
                    for s in selection_screen if s.get("label")
                }
                for f in parsed:
                    fname = f.get("name", "").upper()
                    # 1. 既存ラベルを引き継ぎ
                    if not f.get("label") and existing_labels.get(fname):
                        f["label"] = existing_labels[fname]
                    # 2. tables_meta のフィールドラベルから補完
                    if not f.get("label") and f.get("table_field"):
                        parts = f["table_field"].split("-")
                        if len(parts) == 2:
                            tbl, fld = parts[0].upper(), parts[1].upper()
                            tbl_meta = tables_meta.get(tbl, {})
                            fld_info = tbl_meta.get("fields", {}).get(fld, {})
                            if fld_info.get("label"):
                                f["label"] = fld_info["label"]
                selection_screen = parsed
                print(f"  Found {len(parsed)} selection fields in {prog_file.name}")
                for f in parsed:
                    lbl = f" [{f['label']}]" if f.get("label") else ""
                    print(f"    {f['name']}: {f['type']}{lbl}" + (" OBLIGATORY" if f.get("obligatory") else ""))
                break

    # --from-spec: spec.md から選択画面を推定
    if "--from-spec" in flags:
        spec_path = feature_dir / "spec.md"
        if spec_path.is_file():
            sys.path.insert(0, str(Path(__file__).parent))
            from sap_evidence_common import load_yaml_from_md
            spec_doc = load_yaml_from_md(spec_path)
            spec = spec_doc.get("spec", {})
            parsed = parse_spec_selection_screen(spec)
            if parsed:
                # 既存ラベルを保持（spec にラベルがない場合の補完）
                existing_labels = {
                    s.get("name", "").upper(): s.get("label", "")
                    for s in selection_screen if s.get("label")
                }
                for f in parsed:
                    fname = f.get("name", "").upper()
                    if not f.get("label") and existing_labels.get(fname):
                        f["label"] = existing_labels[fname]
                selection_screen = parsed
                print(f"  Estimated {len(parsed)} selection fields from spec.md")
                for f in parsed:
                    print(f"    {f['name']}: {f['type']}" + (" OBLIGATORY" if f.get("obligatory") else ""))

    # YAML 生成・書き込み
    yaml_str = generate_metadata_yaml(tables_meta, selection_screen)
    if update_sap_context_md(sap_context_path, yaml_str):
        print(f"\nMetadata updated in {sap_context_path}")
    else:
        print(f"\nFailed to update {sap_context_path}", file=sys.stderr)
        sys.exit(1)

    if step_id:
        options = []
        if table_names:
            options.append(f"--tables {' '.join(table_names)}")
        if "--from-source" in flags:
            options.append("--from-source")
        if "--from-spec" in flags:
            options.append("--from-spec")
        write_evidence(
            feature_dir=str(feature_dir),
            step_id=step_id,
            tool_name="sap_context_metadata.py",
            command=" ".join(original_argv),
            options=options,
            result_summary=f"tables={len(tables_meta)} fields={sum(len(m.get('fields', {})) for m in tables_meta.values())} selection_screen={len(selection_screen)}",
        )


if __name__ == "__main__":
    main()
