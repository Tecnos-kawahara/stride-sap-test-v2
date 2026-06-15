"""
sap_program_type_validator.py — program_type 整合性検証ツール

basic_design.md の program_type に基づいて、Gate Check の min_sap_objects や
RAP 固有ゲートの整合性を検証する。

検証内容:
- program_type と min_sap_objects の整合性
- program_type: rap_bo 以外の場合に RAP 固有ゲートが不当に要求されていないか
- program_type: rap_bo の場合に最低限の SAP オブジェクト（DDLS+BDEF+CLAS）が登録されているか
- program_type と sap_object_registry のオブジェクト種別の整合性

stride-lint のエクステンションツールとして MANIFEST.yaml に宣言し、自動実行される。
インターフェース: validate_sap_program_type(feature_path, approval_status, coverage_tier)
                  -> (errors, warnings)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _load_yaml_from_md(md_path: Path) -> dict:
    """Markdown ファイルから最初の ```yaml ブロックを抽出して dict を返す。"""
    if not md_path.exists():
        return {}
    text = md_path.read_text(encoding="utf-8")
    blocks = []
    in_block = False
    current: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```yaml") and not in_block:
            in_block = True
            current = []
        elif line.strip() == "```" and in_block:
            in_block = False
            blocks.append("\n".join(current))
        elif in_block:
            current.append(line)
    if not blocks:
        return {}
    try:
        return yaml.safe_load(blocks[0]) or {}
    except yaml.YAMLError:
        return {}


# program_type ごとの min_sap_objects 期待値
PROGRAM_TYPE_MIN_OBJECTS = {
    "rap_bo": 3,
    "report": 1,
    "interface": 1,
    "fugr": 1,
    "enhancement": 1,
}

# program_type ごとの期待される主要オブジェクト種別
PROGRAM_TYPE_EXPECTED_TYPES = {
    "rap_bo": {"DDLS", "BDEF", "CLAS"},
    "report": {"PROG"},
    "interface": {"PROG", "CLAS"},
    "fugr": {"FUGR"},
    "enhancement": {"CLAS", "ENHO"},
}

# program_type ごとの spec_gate_check ルール期待値
PROGRAM_TYPE_SPEC_RULES = {
    "rap_bo": {"min_odata_acceptance_criteria": 1, "min_spec_as_code_artifacts": 3},
    "report": {"min_odata_acceptance_criteria": 0, "min_spec_as_code_artifacts": 2},
    "interface": {"min_odata_acceptance_criteria": 0, "min_spec_as_code_artifacts": 2},
    "fugr": {"min_odata_acceptance_criteria": 0, "min_spec_as_code_artifacts": 2},
    "enhancement": {"min_odata_acceptance_criteria": 0, "min_spec_as_code_artifacts": 2},
}


def validate_sap_program_type(
    feature_path: str | Path,
    approval_status: dict[str | int, bool],
    coverage_tier: str,
) -> tuple[list[tuple[str, str, list[str]]], list[tuple[str, str, list[str]]]]:
    """
    program_type と Gate Check / Object Registry の整合性を検証する。

    Returns:
        (errors, warnings) — 各要素は (error_code, message, details) のタプル
    """
    errors: list[tuple[str, str, list[str]]] = []
    warnings: list[tuple[str, str, list[str]]] = []

    feature_dir = Path(feature_path)
    bd_path = feature_dir / "basic_design.md"
    bd_doc = _load_yaml_from_md(bd_path)
    if not bd_doc:
        return errors, warnings

    basic_design = bd_doc.get("basic_design", {})
    program_type = basic_design.get("program_type", "rap_bo")

    if program_type not in PROGRAM_TYPE_MIN_OBJECTS:
        warnings.append((
            "UNKNOWN_PROGRAM_TYPE",
            f"basic_design.program_type '{program_type}' は未知の値です。"
            f"有効な値: {', '.join(PROGRAM_TYPE_MIN_OBJECTS.keys())}",
            [],
        ))
        return errors, warnings

    # --- Gate Check の min_sap_objects 検証 ---
    # 7.2 セクションの YAML ブロックを読む（2番目の yaml ブロック）
    text = bd_path.read_text(encoding="utf-8")
    yaml_blocks = []
    in_block = False
    current: list[str] = []
    for line in text.splitlines():
        if line.strip().startswith("```yaml") and not in_block:
            in_block = True
            current = []
        elif line.strip() == "```" and in_block:
            in_block = False
            yaml_blocks.append("\n".join(current))
        elif in_block:
            current.append(line)

    gate_check_doc = {}
    if len(yaml_blocks) >= 2:
        try:
            gate_check_doc = yaml.safe_load(yaml_blocks[1]) or {}
        except yaml.YAMLError:
            pass

    gate_check = gate_check_doc.get("basic_design_gate_check", {})
    rules = gate_check.get("rules", {})
    min_sap_objects = rules.get("min_sap_objects")
    expected_min = PROGRAM_TYPE_MIN_OBJECTS[program_type]

    if min_sap_objects is not None and min_sap_objects != expected_min:
        errors.append((
            "PROGRAM_TYPE_MIN_OBJECTS_MISMATCH",
            f"program_type '{program_type}' の min_sap_objects は {expected_min} であるべきですが、"
            f"Gate Check では {min_sap_objects} に設定されています",
            [],
        ))

    # --- SAP Object Registry の種別検証 ---
    registry = basic_design.get("sap_object_registry", {})
    objects = registry.get("objects", [])
    # 名前が空でないオブジェクトのみカウント
    actual_objects = [o for o in objects if o.get("name")]
    actual_types = {o.get("type", "") for o in actual_objects}
    expected_types = PROGRAM_TYPE_EXPECTED_TYPES.get(program_type, set())

    if actual_objects and expected_types:
        if not actual_types & expected_types:
            warnings.append((
                "PROGRAM_TYPE_OBJECT_TYPE_MISMATCH",
                f"program_type '{program_type}' では {expected_types} 型のオブジェクトが期待されますが、"
                f"登録されているのは {actual_types} です",
                [],
            ))

    # --- RAP 固有ゲートの不要な要求チェック ---
    if program_type != "rap_bo":
        rap_defined = gate_check.get("rap_pattern_defined")
        data_model_defined = gate_check.get("sap_data_model_defined")
        if rap_defined is True:
            warnings.append((
                "RAP_GATE_UNNECESSARY",
                f"program_type '{program_type}' では rap_pattern_defined は不要です（N/A）",
                [],
            ))
        if data_model_defined is True:
            warnings.append((
                "DATA_MODEL_GATE_UNNECESSARY",
                f"program_type '{program_type}' では sap_data_model_defined は不要です（N/A）",
                [],
            ))

    # --- spec_gate_check ルールの整合性検証 ---
    spec_path = feature_dir / "spec.md"
    spec_doc = _load_yaml_from_md(spec_path)
    if spec_doc:
        spec_gate_check = spec_doc.get("spec_gate_check", {})
        spec_rules = spec_gate_check.get("rules", {})
        expected_spec_rules = PROGRAM_TYPE_SPEC_RULES.get(program_type, {})

        for rule_key, expected_value in expected_spec_rules.items():
            actual_value = spec_rules.get(rule_key)
            if actual_value is not None and actual_value != expected_value:
                errors.append((
                    "PROGRAM_TYPE_SPEC_RULE_MISMATCH",
                    f"program_type '{program_type}' の {rule_key} は {expected_value} であるべきですが、"
                    f"spec_gate_check では {actual_value} に設定されています",
                    [],
                ))

    return errors, warnings
