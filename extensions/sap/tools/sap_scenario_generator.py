"""
sap_scenario_generator.py — v6 再設計版
参照仕様: 04_ツール §C-5

sap_path_enumerator.py の出力（パス列挙結果）からテストシナリオ候補を生成する。

**重要: 出力は「提案」であり SSoT ではない。**
AI が plan.md を作成する際の参考候補として使用し、
最終的な plan.md の内容は AI + 人間が判断する。

v5 → v6 変更:
  旧入力: sap_path_enumerator の出力 + spec.md
  新入力: sap_path_enumerator の出力 + basic_design.md + config/tag_branch_rules.yaml

Usage:
  python3 extensions/sap/tools/sap_scenario_generator.py specs/<feature>/ --step-id 2-C3
  python3 extensions/sap/tools/sap_scenario_generator.py --paths paths.json specs/<feature>/ --step-id 2-C3
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

try:
    from tool_evidence_writer import write_evidence
except ImportError:
    write_evidence = None  # type: ignore

# sap_path_enumerator を import して直接使用可能にする
try:
    from sap_path_enumerator import (
        load_yaml_from_md,
        load_tag_branch_rules,
        extract_steps_from_process_definitions,
        enumerate_paths,
    )
except ImportError:
    load_yaml_from_md = None  # type: ignore


def generate_scenarios(
    paths: list[dict],
    bd: dict,
    tag_rules: dict[str, list[dict]],
) -> list[dict]:
    """パス列挙結果からテストシナリオ候補を生成する。

    各パスに対して:
    - シナリオ ID（TS-XXX 形式）
    - タイトル・説明（パスの分岐から自動生成）
    - selection_fields 推奨値
    - expected_result 推奨値
    - se16_checks 推奨値
    - test_setup 推奨値
    """
    scenarios: list[dict] = []
    data_refs = bd.get("database", {}).get("data_references", [])

    for path in paths:
        path_id = path.get("path_id", "")
        path_type = path.get("type", "normal")
        steps = path.get("steps", [])
        if not steps:
            continue

        # シナリオ ID
        sc_id = f"TS-{path_id.replace('PATH-', '')}"

        # タイトル生成: 最後のステップの分岐ラベルから
        last_step = steps[-1]
        branch_label = last_step.get("branch", "")
        branch_type = last_step.get("branch_type", "normal")
        tag = last_step.get("tag", "")

        if path_type == "normal":
            title = "正常系: " + " → ".join(
                s.get("branch", "pass") for s in steps if s.get("branch") != "pass_through"
            )
            if not title.endswith(": "):
                pass
            else:
                title = "正常系: 全ステップ正常完了"
        else:
            title = f"異常系: {tag} → {branch_label}"

        # description
        desc_parts = []
        for s in steps:
            if s.get("tag"):
                desc_parts.append(f"{s['tag']}={s.get('branch', '')}")
        description = ", ".join(desc_parts) if desc_parts else "全ステップ通過"

        # expected_result 推奨値
        expected_result = _infer_expected_result(last_step, path_type)

        # se16_checks 推奨値
        se16_checks = _infer_se16_checks(steps, data_refs, path_type)

        # test_setup 推奨値
        test_setup = _infer_test_setup(steps, path_type)

        scenario = {
            "id": sc_id,
            "title": title,
            "description": description,
            "path_ref": path_id,
            "type": "Type A" if path_type == "normal" else "Type A",
            "category": tag.lower() if tag else "general",
            "expected_result": expected_result,
            "se16_checks": se16_checks,
            "test_setup": test_setup,
            "steps": [
                {
                    "step_id": s.get("step_id", ""),
                    "tag": s.get("tag", ""),
                    "branch": s.get("branch", ""),
                    "branch_type": s.get("branch_type", ""),
                }
                for s in steps
            ],
            "_proposal": True,  # SSoT ではなく提案であることを明示
        }
        scenarios.append(scenario)

    return scenarios


def _infer_expected_result(last_step: dict, path_type: str) -> list[dict]:
    """最後のステップからexpected_resultを推定する。"""
    tag = last_step.get("tag", "")
    branch = last_step.get("branch", "")
    branch_type = last_step.get("branch_type", "normal")

    results = []
    if branch_type == "abnormal":
        # 異常系: エラーメッセージが表示される
        results.append({"check": "message_type", "value": "E"})
        if "exist" in branch:
            results.append({"check": "message_text_contains", "value": "存在しません"})
    elif tag == "BAPI" and "post_success" in branch:
        results.append({"check": "message_type", "value": "S"})
        results.append({"check": "no_error"})
    elif tag == "DB_READ" and "data_found" in branch:
        results.append({"check": "alv", "value": True})
    elif tag == "DB_READ" and "partial" in branch:
        # IMP-035: partial fetch pattern — first query found, dependent empty
        results.append({"check": "alv", "value": True})
        results.append({"check": "partial_result", "value": "dependent_empty"})
    else:
        results.append({"check": "no_error"})

    return results


def _infer_se16_checks(
    steps: list[dict],
    data_refs: list[dict],
    path_type: str,
) -> dict:
    """ステップからse16_checks（事前/事後確認）を推定する。"""
    pre_checks: list[dict] = []
    post_checks: list[dict] = []

    tables = set()
    for dr in data_refs:
        for t in dr.get("tables", []):
            if t:
                tables.add(t)

    for step in steps:
        tag = step.get("tag", "")
        if tag in ("DB_WRITE", "BAPI") and step.get("branch_type") == "normal":
            # 書き込み系: 事前/事後にテーブル確認
            for table in tables:
                pre_checks.append({
                    "table": table,
                    "keys": "__PLACEHOLDER__",
                    "description": f"事前データ確認（{table}）",
                })
                post_checks.append({
                    "table": table,
                    "keys": "__PLACEHOLDER__",
                    "description": f"事後データ確認（{table}）",
                })

    return {"pre": pre_checks, "post": post_checks}


def _infer_test_setup(steps: list[dict], path_type: str) -> dict:
    """テスト前提条件を推定する。"""
    setup: dict[str, Any] = {}
    for step in steps:
        tag = step.get("tag", "")
        branch = step.get("branch", "")
        if tag == "EXIST" and "exist_ok" in branch:
            setup["prerequisite"] = "対象マスタデータが登録済みであること"
        elif tag == "EXIST" and "exist_ng" in branch:
            setup["prerequisite"] = "対象マスタデータが未登録であること"
        elif tag == "DB_WRITE":
            setup["run_program"] = "__PLACEHOLDER__"
    return setup


def format_scenarios_yaml(scenarios: list[dict]) -> str:
    """シナリオ候補を YAML 形式で出力する。"""
    if yaml is None:
        return json.dumps(scenarios, ensure_ascii=False, indent=2)
    return yaml.dump(
        {"scenario_proposals": scenarios},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )


def format_scenarios_markdown(scenarios: list[dict]) -> str:
    """シナリオ候補を Markdown 形式で出力する。"""
    lines = [
        "## テストシナリオ候補（提案）",
        "",
        "**注意: この出力は AI の参考用提案であり、SSoT ではありません。**",
        "plan.md に反映する際は、AI + 人間が内容を精査・修正してください。",
        "",
        f"合計: {len(scenarios)} シナリオ候補",
        "",
    ]

    for sc in scenarios:
        lines.append(f"### {sc['id']}: {sc['title']}")
        lines.append(f"- パス参照: {sc.get('path_ref', '')}")
        lines.append(f"- カテゴリ: {sc.get('category', '')}")
        lines.append(f"- 説明: {sc.get('description', '')}")

        er = sc.get("expected_result", [])
        if er:
            er_texts = []
            for r in er:
                check = r.get("check", "")
                value = r.get("value", "")
                er_texts.append(f"{check}={value}")
            lines.append(f"- 期待結果: {', '.join(er_texts)}")

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    original_argv = sys.argv.copy()
    step_id = None
    output_format = "yaml"
    paths_file = None

    filtered_argv = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--step-id" and i + 1 < len(sys.argv):
            step_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--format" and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--paths" and i + 1 < len(sys.argv):
            paths_file = sys.argv[i + 1]
            i += 2
        else:
            filtered_argv.append(sys.argv[i])
            i += 1

    if step_id is None:
        print(
            "ERROR: --step-id is required.\n"
            "Usage: python3 sap_scenario_generator.py specs/<feature>/ --step-id 2-C3",
            file=sys.stderr,
        )
        sys.exit(1)

    if not filtered_argv:
        print(
            "Usage: python3 sap_scenario_generator.py specs/<feature>/ --step-id 2-C3 "
            "[--paths paths.json] [--format yaml|markdown|json]",
            file=sys.stderr,
        )
        sys.exit(1)

    feature_dir = Path(filtered_argv[0])
    bd_path = feature_dir / "basic_design.md"

    if not bd_path.exists():
        print(f"ERROR: {bd_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    bd_doc = load_yaml_from_md(bd_path)
    bd = bd_doc.get("basic_design", bd_doc)

    # パス列挙結果の取得
    if paths_file:
        # 外部ファイルからパスを読み込む
        paths_data = json.loads(Path(paths_file).read_text(encoding="utf-8"))
        paths = paths_data if isinstance(paths_data, list) else paths_data.get("paths", [])
    else:
        # D4 を直接実行してパスを取得
        config_dir = Path(__file__).resolve().parent.parent / "config"
        tag_rules = load_tag_branch_rules(config_dir)
        steps = extract_steps_from_process_definitions(bd)
        paths = enumerate_paths(steps, tag_rules)

    if not paths:
        print("WARNING: パスが0件です。シナリオ候補を生成できません。", file=sys.stderr)
        sys.exit(0)

    # tag_branch_rules の読み込み
    config_dir = Path(__file__).resolve().parent.parent / "config"
    tag_rules = load_tag_branch_rules(config_dir)

    # シナリオ候補生成
    scenarios = generate_scenarios(paths, bd, tag_rules)

    # 出力
    if output_format == "json":
        output = json.dumps(scenarios, ensure_ascii=False, indent=2)
    elif output_format == "markdown":
        output = format_scenarios_markdown(scenarios)
    else:
        output = format_scenarios_yaml(scenarios)

    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")

    if write_evidence and step_id:
        write_evidence(
            feature_dir=str(feature_dir),
            step_id=step_id,
            tool_name="sap_scenario_generator.py",
            command=" ".join(original_argv),
            options=[],
            result_summary=f"{len(scenarios)} scenario proposals generated "
                          f"(from {len(paths)} paths). Output is PROPOSAL, not SSoT.",
        )


if __name__ == "__main__":
    main()
