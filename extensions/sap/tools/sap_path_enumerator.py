"""
sap_path_enumerator.py — v6 再設計版
参照仕様: 04_ツール §C-5

process_definitions[].body のステップ + config/tag_branch_rules.yaml から
有効なパスを列挙する。

v5 → v6 変更:
  旧入力: spec.md の processing_steps[].tag
  新入力: basic_design.process_definitions[].body.steps[] + config/tag_branch_rules.yaml

出力: パス一覧（各パスの通過ステップ + 分岐タイプ）— JSON / Markdown

Usage:
  python3 extensions/sap/tools/sap_path_enumerator.py specs/<feature>/ --step-id 2-C2
"""

from __future__ import annotations

import json
import re
import sys
from itertools import product
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


def load_yaml_from_md(md_path: Path) -> dict:
    """Markdown ファイルから最初の YAML ブロックを読み取る。"""
    content = md_path.read_text(encoding="utf-8")
    m = re.search(r"```yaml\r?\n([\s\S]*?)```", content)
    if not m:
        return {}
    if yaml is None:
        raise ImportError("PyYAML is required: pip install pyyaml")
    return yaml.safe_load(m.group(1)) or {}


def load_tag_branch_rules(config_dir: Path) -> dict[str, list[dict]]:
    """tag_branch_rules.yaml からタグ→分岐ルールのマッピングを読み込む。"""
    rules_path = config_dir / "tag_branch_rules.yaml"
    if not rules_path.exists():
        return {}
    if yaml is None:
        raise ImportError("PyYAML is required")
    data = yaml.safe_load(rules_path.read_text(encoding="utf-8")) or {}
    result: dict[str, list[dict]] = {}
    for rule in data.get("rules", []):
        tag = rule.get("tag", "")
        if tag:
            result[tag] = rule.get("branches", [])
    return result


def extract_steps_from_process_definitions(bd: dict) -> list[dict]:
    """basic_design の process_definitions[].body からステップを抽出する。

    body はテキスト形式。各行をステップとして扱い、
    タグキーワード（EXIST, BAPI, VALIDATE 等）を検出して分岐情報を付与する。
    """
    steps: list[dict] = []
    processes = bd.get("process_definitions", [])
    for proc in processes:
        proc_id = proc.get("id", "")
        body = proc.get("body", "")
        if not body:
            continue
        # body を行単位で解析
        for i, line in enumerate(body.strip().split("\n")):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            step_id = f"{proc_id}_S{i+1:02d}"
            # タグ検出: 大文字キーワードをタグとして認識
            tags: list[str] = []
            for keyword in [
                "EXIST", "BAPI", "VALIDATE", "AUTH", "DB_READ", "DB_WRITE",
                "FILE_OUTPUT", "APPLOG", "IDOC", "MAIL", "DB_READ_MULTI",
            ]:
                if keyword in line.upper():
                    tags.append(keyword)
            # CHK/CALC/MSG パターンからもタグを推定
            if re.search(r"CHK-\d+", line):
                if "VALIDATE" not in tags:
                    tags.append("VALIDATE")
            if re.search(r"CALC-\d+", line):
                tags.append("CALC")
            steps.append({
                "id": step_id,
                "process_id": proc_id,
                "text": line,
                "tags": tags,
                "line_num": i + 1,
            })
    return steps


def enumerate_paths(
    steps: list[dict],
    tag_rules: dict[str, list[dict]],
) -> list[dict]:
    """ステップとタグルールからパスを列挙する。

    各ステップのタグに基づく分岐を展開し、全有効パスの組み合わせを生成する。
    """
    # 各ステップの分岐選択肢を収集
    step_choices: list[list[dict]] = []
    for step in steps:
        choices: list[dict] = []
        if not step["tags"]:
            # タグなし: 通過のみ
            choices.append({
                "step_id": step["id"],
                "text": step["text"],
                "branch": "pass_through",
                "branch_type": "normal",
            })
        else:
            for tag in step["tags"]:
                if tag in tag_rules:
                    for branch in tag_rules[tag]:
                        choices.append({
                            "step_id": step["id"],
                            "text": step["text"],
                            "tag": tag,
                            "branch": branch.get("label", ""),
                            "branch_type": branch.get("type", "normal"),
                            "description": branch.get("description", ""),
                        })
                else:
                    # ルールにないタグ: normal のみ
                    choices.append({
                        "step_id": step["id"],
                        "text": step["text"],
                        "tag": tag,
                        "branch": f"{tag.lower()}_ok",
                        "branch_type": "normal",
                    })
            # 重複排除
            seen = set()
            unique = []
            for c in choices:
                key = (c["step_id"], c["branch"])
                if key not in seen:
                    seen.add(key)
                    unique.append(c)
            choices = unique
        step_choices.append(choices)

    # パスの組み合わせ生成（爆発防止: 最大 200 パス）
    MAX_PATHS = 200
    paths: list[dict] = []

    # 全組み合わせの積を計算
    total = 1
    for choices in step_choices:
        total *= len(choices)
        if total > MAX_PATHS:
            break

    if total <= MAX_PATHS:
        for combo in product(*step_choices):
            steps_in_path = list(combo)
            # 異常分岐があるステップ以降は打ち切り（異常系は次ステップに進まない）
            effective_steps = []
            for s in steps_in_path:
                effective_steps.append(s)
                if s["branch_type"] == "abnormal":
                    break
            path_type = "normal" if all(
                s["branch_type"] == "normal" for s in effective_steps
            ) else "abnormal"
            paths.append({
                "path_id": f"PATH-{len(paths)+1:03d}",
                "type": path_type,
                "steps": effective_steps,
            })
    else:
        # 組み合わせが多すぎる場合は正常系 + 各ステップの異常系のみ
        # 正常系: 各ステップで最初の normal を選択
        normal_path = []
        for choices in step_choices:
            normal = next((c for c in choices if c["branch_type"] == "normal"), choices[0])
            normal_path.append(normal)
        paths.append({"path_id": "PATH-001", "type": "normal", "steps": normal_path})
        # 異常系: 各ステップで abnormal を選択、他は normal
        for si, choices in enumerate(step_choices):
            for choice in choices:
                if choice["branch_type"] == "abnormal":
                    abnormal_path = []
                    for sj, chs in enumerate(step_choices):
                        if sj < si:
                            n = next((c for c in chs if c["branch_type"] == "normal"), chs[0])
                            abnormal_path.append(n)
                        elif sj == si:
                            abnormal_path.append(choice)
                            break
                    paths.append({
                        "path_id": f"PATH-{len(paths)+1:03d}",
                        "type": "abnormal",
                        "steps": abnormal_path,
                    })

    return paths


def format_paths_markdown(paths: list[dict]) -> str:
    """パス一覧を Markdown 形式で出力する。"""
    lines = [
        "## パス列挙結果",
        "",
        f"合計: {len(paths)} パス "
        f"(正常系: {sum(1 for p in paths if p['type'] == 'normal')}, "
        f"異常系: {sum(1 for p in paths if p['type'] == 'abnormal')})",
        "",
    ]
    for p in paths:
        ptype = "正常系" if p["type"] == "normal" else "異常系"
        lines.append(f"### {p['path_id']} ({ptype})")
        lines.append("")
        lines.append("| # | ステップ | テキスト | 分岐 | タイプ |")
        lines.append("|---|---------|---------|------|--------|")
        for i, s in enumerate(p["steps"]):
            tag = s.get("tag", "")
            branch = s.get("branch", "pass_through")
            btype = s.get("branch_type", "normal")
            text = s.get("text", "")[:60]
            lines.append(f"| {i+1} | {s['step_id']} | {text} | {branch} | {btype} |")
        lines.append("")
    return "\n".join(lines)


def format_paths_json(paths: list[dict]) -> str:
    """パス一覧を JSON 形式で出力する。"""
    return json.dumps(paths, ensure_ascii=False, indent=2)


def main() -> None:
    original_argv = sys.argv.copy()

    step_id = None
    output_format = "markdown"

    # 引数パース
    filtered_argv = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--step-id" and i + 1 < len(sys.argv):
            step_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--format" and i + 1 < len(sys.argv):
            output_format = sys.argv[i + 1]
            i += 2
        else:
            filtered_argv.append(sys.argv[i])
            i += 1

    if step_id is None:
        print(
            "ERROR: --step-id is required.\n"
            "Usage: python3 sap_path_enumerator.py specs/<feature>/ --step-id 2-C2",
            file=sys.stderr,
        )
        sys.exit(1)

    if not filtered_argv:
        print(
            "Usage: python3 sap_path_enumerator.py specs/<feature>/ --step-id 2-C2 [--format markdown|json]",
            file=sys.stderr,
        )
        sys.exit(1)

    feature_dir = Path(filtered_argv[0])
    bd_path = feature_dir / "basic_design.md"

    if not bd_path.exists():
        print(f"ERROR: {bd_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    # basic_design.md から process_definitions を読み取る
    bd_doc = load_yaml_from_md(bd_path)
    bd = bd_doc.get("basic_design", bd_doc)

    # config/tag_branch_rules.yaml を読み込む
    # extensions/sap/config/ を探索
    config_dir = Path(__file__).resolve().parent.parent / "config"
    tag_rules = load_tag_branch_rules(config_dir)

    # ステップ抽出
    steps = extract_steps_from_process_definitions(bd)
    if not steps:
        print("WARNING: process_definitions に body ステップがありません", file=sys.stderr)
        if write_evidence and step_id:
            write_evidence(
                feature_dir=str(feature_dir),
                step_id=step_id,
                tool_name="sap_path_enumerator.py",
                command=" ".join(original_argv),
                options=[],
                result_summary="0 steps extracted (process_definitions empty)",
            )
        sys.exit(0)

    # パス列挙
    paths = enumerate_paths(steps, tag_rules)

    # 出力
    if output_format == "json":
        output = format_paths_json(paths)
    else:
        output = format_paths_markdown(paths)

    sys.stdout.buffer.write(output.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")

    if write_evidence and step_id:
        normal_count = sum(1 for p in paths if p["type"] == "normal")
        abnormal_count = sum(1 for p in paths if p["type"] == "abnormal")
        write_evidence(
            feature_dir=str(feature_dir),
            step_id=step_id,
            tool_name="sap_path_enumerator.py",
            command=" ".join(original_argv),
            options=[],
            result_summary=f"{len(steps)} step(s), {len(paths)} path(s) "
                          f"(normal: {normal_count}, abnormal: {abnormal_count})",
        )


if __name__ == "__main__":
    main()
