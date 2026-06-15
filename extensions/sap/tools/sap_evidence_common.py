"""
sap_evidence_common.py — SAP エビデンス関連ツールの共通関数

YAML パース（Markdown 内の ```yaml ブロック、フロントマター、純粋 YAML）を提供する。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def load_yaml_from_md(path: Path) -> dict[str, Any]:
    """Markdown ファイルから YAML を読み取る。

    対応形式:
    1. ```yaml ブロック（plan.md 等の Canonical YAML）
    2. フロントマター（--- で囲まれた YAML）
    3. 純粋な YAML ファイル
    """
    if not path.is_file():
        return {}
    if yaml is None:
        return {}
    text = path.read_text(encoding="utf-8")

    # 1. ```yaml ブロックを探す
    m = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if m:
        try:
            return yaml.safe_load(m.group(1)) or {}
        except Exception:
            return {}

    # 2. フロントマター（--- で囲まれた YAML）
    fm = re.match(r"\A---\n(.*?)^---\s*$", text, re.DOTALL | re.MULTILINE)
    if fm:
        try:
            return yaml.safe_load(fm.group(1)) or {}
        except Exception:
            return {}

    # 3. そのまま YAML として読む
    try:
        return yaml.safe_load(text) or {}
    except Exception:
        return {}


def load_yaml_file(path: Path) -> dict[str, Any]:
    """純粋な YAML ファイルを読み取る。"""
    if not path.is_file() or yaml is None:
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
