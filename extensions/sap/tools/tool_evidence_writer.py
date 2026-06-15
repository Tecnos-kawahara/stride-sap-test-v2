"""
tool_evidence_writer.py — ツール実行エビデンスファイルの書き出しヘルパー

各 SAP 拡張ツールが正常終了時に呼び出し、
specs/<feature>/.tool_evidence/ にエビデンスファイルを出力する。

stride-lint の sap_tool_evidence_validator.py がこのファイルの有無をチェックし、
ワークフローステップの実行漏れを検出する。
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

JST = timezone(timedelta(hours=9))

EVIDENCE_DIR_NAME = ".tool_evidence"


def _sanitize_step_id(step_id: str) -> str:
    """ファイル名に使えない文字を置換する。"""
    return re.sub(r'[<>:"/\\|?*]', '_', step_id)


def evidence_filename(step_id: str, tool_name: str) -> str:
    """エビデンスファイル名を生成する。

    命名規則: {step_id}__{tool_basename}.evidence.yaml
    """
    tool_basename = Path(tool_name).stem
    safe_step = _sanitize_step_id(step_id)
    return f"{safe_step}__{tool_basename}.evidence.yaml"


def write_evidence(
    feature_dir: str | Path,
    step_id: str,
    tool_name: str,
    command: str,
    options: list[str] | None = None,
    exit_code: int = 0,
    result_summary: str = "",
    outputs: list[dict[str, str]] | None = None,
    duration_ms: int | None = None,
) -> Path:
    """エビデンスファイルを出力する。

    Args:
        feature_dir: specs/<feature>/ のパス
        step_id: ワークフローステップ ID（例: "1.5-B2", "2-B4", "S1-E1"）
        tool_name: ツールのスクリプト名（例: "sap_context_metadata.py"）
        command: 実行されたフルコマンド文字列
        options: コマンドオプションのリスト
        exit_code: ツールの終了コード
        result_summary: 結果の要約テキスト
        outputs: 出力ファイルリスト [{"path": "...", "action": "created|modified"}]
        duration_ms: 実行時間（ミリ秒）

    Returns:
        書き出したエビデンスファイルのパス
    """
    feature_path = Path(feature_dir)
    evidence_dir = feature_path / EVIDENCE_DIR_NAME
    evidence_dir.mkdir(parents=True, exist_ok=True)

    filename = evidence_filename(step_id, tool_name)
    filepath = evidence_dir / filename

    data = {
        "tool_evidence": {
            "schema_version": "1.0",
            "step_id": step_id,
            "tool": tool_name,
            "command": command,
            "options": options or [],
            "timestamp": datetime.now(JST).isoformat(),
            "exit_code": exit_code,
            "result_summary": result_summary,
        }
    }
    if duration_ms is not None:
        data["tool_evidence"]["duration_ms"] = duration_ms
    if outputs:
        data["tool_evidence"]["outputs"] = outputs

    if yaml is not None:
        content = yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
    else:
        lines = [
            "tool_evidence:",
            '  schema_version: "1.0"',
            f'  step_id: "{step_id}"',
            f'  tool: "{tool_name}"',
            f'  command: "{command}"',
            f"  options: {options or []}",
            f'  timestamp: "{datetime.now(JST).isoformat()}"',
            f"  exit_code: {exit_code}",
            f'  result_summary: "{result_summary}"',
        ]
        content = "\n".join(lines) + "\n"

    filepath.write_text(content, encoding="utf-8")
    return filepath
