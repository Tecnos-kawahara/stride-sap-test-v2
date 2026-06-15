"""
sap_tool_evidence_validator.py — ツール実行エビデンスの検証

CLAUDE_WORKFLOW_SAP.md の各ステップで実行されるツールが
エビデンスファイル (.tool_evidence/) を出力しているかを検証する。

stride-lint のエクステンションツールとして MANIFEST.yaml に宣言し、自動実行される。
インターフェース: validate_tool_evidence(feature_path, approval_status, coverage_tier)
                  -> (errors, warnings)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

EVIDENCE_DIR_NAME = ".tool_evidence"
REGISTRY_RELATIVE_PATH = Path("extensions/sap/config/tool_evidence_registry.yaml")


def _load_registry(feature_path: Path) -> dict[str, Any] | None:
    """tool_evidence_registry.yaml を読み込む。"""
    if yaml is None:
        return None

    # feature_path から遡ってプロジェクトルートを探す
    # specs/<feature>/ → プロジェクトルート
    candidate = feature_path
    for _ in range(5):
        registry_path = candidate / REGISTRY_RELATIVE_PATH
        if registry_path.is_file():
            return yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        candidate = candidate.parent

    return None


def _evidence_filename(step_id: str, tool_name: str) -> str:
    """エビデンスファイル名を生成する（tool_evidence_writer.py と同一ロジック）。"""
    import re
    tool_basename = Path(tool_name).stem
    safe_step = re.sub(r'[<>:"/\\|?*]', '_', step_id)
    return f"{safe_step}__{tool_basename}.evidence.yaml"


def validate_tool_evidence(
    feature_path: str | Path,
    approval_status: dict[str | int, bool],
    coverage_tier: str,
) -> tuple[list[tuple[str, str, list[str]]], list[tuple[str, str, list[str]]]]:
    """ツール実行エビデンスの存在を検証する。

    Returns:
        (errors, warnings) — 各要素は (error_code, message, details) のタプル
    """
    errors: list[tuple[str, str, list[str]]] = []
    warnings: list[tuple[str, str, list[str]]] = []

    fp = Path(feature_path)
    evidence_dir = fp / EVIDENCE_DIR_NAME

    registry = _load_registry(fp)
    if registry is None:
        warnings.append((
            "TOOL_EVIDENCE_REGISTRY_NOT_FOUND",
            "tool_evidence_registry.yaml が見つからないため、ツール実行エビデンスの検証をスキップします",
            [],
        ))
        return errors, warnings

    phases = registry.get("phases", {})

    # Gate 承認状態を取得
    def gate_approved(gate_num: int) -> bool:
        return (
            approval_status.get(gate_num, False)
            or approval_status.get(str(gate_num), False)
        )

    gate_1_2 = gate_approved(1) and gate_approved(2)
    gate_3 = gate_approved(3)
    gate_5 = gate_approved(5)

    # --- Phase 1.5 チェック: Gate 1,2 承認後 ---
    if gate_1_2:
        _check_phase(fp, evidence_dir, phases.get("phase_1_5", {}), errors, warnings)

    # --- Phase 2 チェック: Gate 1,2 承認後 ---
    if gate_1_2:
        _check_phase(fp, evidence_dir, phases.get("phase_2", {}), errors, warnings)
        # data_preview の全テーブル確認チェック
        _check_data_preview_tables(fp, evidence_dir, "2.5-4", errors, warnings)

    # --- Stage 1 チェック: Gate 5 承認後 ---
    if gate_5:
        _check_phase(fp, evidence_dir, phases.get("stage_1", {}), errors, warnings)

        # Stage 1 が完了していれば Stage 2 もチェック
        stage_1_steps = phases.get("stage_1", {}).get("steps", [])
        stage_1_complete = _all_required_present(evidence_dir, stage_1_steps)
        if stage_1_complete:
            _check_phase(fp, evidence_dir, phases.get("stage_2", {}), errors, warnings)

            # Stage 2 完了なら Stage 3 もチェック
            stage_2_steps = phases.get("stage_2", {}).get("steps", [])
            stage_2_complete = _all_required_present(evidence_dir, stage_2_steps)
            if stage_2_complete:
                _check_phase(fp, evidence_dir, phases.get("stage_3", {}), errors, warnings)

    return errors, warnings


def _all_required_present(evidence_dir: Path, steps: list[dict]) -> bool:
    """必須ステップのエビデンスが全て存在するか確認する。"""
    for step in steps:
        if step.get("optional", False):
            continue
        filename = _evidence_filename(step["step_id"], step["tool"])
        if not (evidence_dir / filename).is_file():
            return False
    return True


def _check_phase(
    feature_path: Path,
    evidence_dir: Path,
    phase_config: dict[str, Any],
    errors: list,
    warnings: list,
) -> None:
    """1つのフェーズのエビデンスをチェックする。"""
    phase_name = phase_config.get("name", "Unknown Phase")
    steps = phase_config.get("steps", [])

    if not steps:
        return

    missing_required = []
    missing_optional = []

    for step in steps:
        step_id = step["step_id"]
        tool = step["tool"]
        optional = step.get("optional", False)
        description = step.get("description", "")

        filename = _evidence_filename(step_id, tool)
        filepath = evidence_dir / filename

        if not filepath.is_file():
            entry = f"Step {step_id}: {tool} ({description})"
            if optional:
                missing_optional.append(entry)
            else:
                missing_required.append(entry)

    if missing_required:
        errors.append((
            "SAP_TOOL_NOT_EXECUTED",
            f"{phase_name}: 以下のツール実行エビデンスがありません。"
            f"CLAUDE_WORKFLOW_SAP.md に従い、--step-id 付きでツールを実行してください。",
            missing_required,
        ))

    if missing_optional:
        warnings.append((
            "SAP_TOOL_OPTIONAL_SKIPPED",
            f"{phase_name}: 以下のオプションステップのエビデンスがありません。"
            f"該当する場合は実行してください。",
            missing_optional,
        ))


def _check_data_preview_tables(
    feature_path: Path,
    evidence_dir: Path,
    step_id: str,
    errors: list,
    warnings: list,
) -> None:
    """data_preview のエビデンスから checked_tables を取得し、plan.md の契約テーブルと突合する。"""
    # plan.md から必須テーブル一覧を取得
    plan_path = feature_path / "plan.md"
    if not plan_path.is_file():
        return

    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).parent))
        from sap_evidence_common import load_yaml_from_md
        plan_data = load_yaml_from_md(plan_path)
    except Exception:
        return

    plan_body = plan_data.get("plan", plan_data)
    contracts = plan_body.get("contracts", {})
    db_config = contracts.get("database", {})
    if not db_config.get("enabled", False):
        return

    required_tables = set()
    for tbl in db_config.get("tables", []):
        table_name = tbl.get("table", "")
        if table_name:
            required_tables.add(table_name.upper())

    if not required_tables:
        return

    # エビデンスファイルから checked_tables を取得
    evidence_filename = _evidence_filename(step_id, "data_preview.js")
    evidence_path = evidence_dir / evidence_filename
    checked_tables = set()

    if evidence_path.is_file():
        content = evidence_path.read_text(encoding="utf-8")
        import re
        match = re.search(r"checked_tables:\s*\[([^\]]*)\]", content)
        if match:
            for t in match.group(1).split(","):
                t = t.strip().strip('"').strip("'")
                if t:
                    checked_tables.add(t.upper())

    missing = required_tables - checked_tables
    if missing:
        errors.append((
            "SAP_DATA_PREVIEW_TABLE_MISSING",
            f"Step {step_id}: 以下のテーブルの data_preview が未実行です。"
            f"plan.md の contracts.database.tables に定義された全テーブルを確認してください。",
            [f"未確認: {t}" for t in sorted(missing)],
        ))
