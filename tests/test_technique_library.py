"""Test: BABOK v3 §10 Technique Library catalogue integrity (FEAT-VALA01 Phase A).

Verifies shared/policies/technique_library.yaml lists exactly 50 techniques
with required fields, snake_case unique ids, and valid typical_phase values.

Covers AC-US-FEATVALA01-001-03 (technique 50 件 + 命名規約 + 重複なし) per spec.md.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_PATH = REPO_ROOT / "shared" / "policies" / "technique_library.yaml"

REQUIRED_FIELDS = {
    "id",
    "name_en",
    "name_ja",
    "purpose",
    "babok_section",
    "typical_phase",
    "typical_artifacts",
}

VALID_PHASES = {
    "phase_0_discovery",
    "phase_0_3_elicit",
    "phase_0_5_context_modelling",
    "stride_core",
}

ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
SECTION_PATTERN = re.compile(r"^10\.\d{1,2}$")


def _load():
    return yaml.safe_load(LIBRARY_PATH.read_text(encoding="utf-8"))


def test_library_exists():
    assert LIBRARY_PATH.is_file(), f"technique_library.yaml 不存在: {LIBRARY_PATH}"


def test_exactly_50_techniques():
    data = _load()
    techs = data.get("techniques")
    assert isinstance(techs, list), "techniques は list 必須"
    assert len(techs) == 50, f"techniques 件数 {len(techs)} != 50 ちょうど"


def test_each_technique_has_required_fields():
    data = _load()
    for t in data["techniques"]:
        missing = REQUIRED_FIELDS - set(t.keys())
        assert not missing, f"technique {t.get('id', '?')}: 必須フィールド欠落 {missing}"


def test_id_naming_convention_and_uniqueness():
    data = _load()
    ids = [t["id"] for t in data["techniques"]]
    # 重複なし
    assert len(set(ids)) == len(ids), f"id 重複あり: {ids}"
    # 全 id が snake_case 規約に一致
    bad = [i for i in ids if not ID_PATTERN.match(i)]
    assert not bad, f"id 命名規約違反: {bad}"


def test_typical_phase_values():
    data = _load()
    for t in data["techniques"]:
        phases = t["typical_phase"]
        assert isinstance(phases, list) and phases, (
            f"{t['id']}: typical_phase は非空リスト必須"
        )
        bad = set(phases) - VALID_PHASES
        assert not bad, f"{t['id']}: 不正な phase {bad}"


def test_babok_section_format():
    data = _load()
    for t in data["techniques"]:
        sec = t["babok_section"]
        assert SECTION_PATTERN.match(sec), (
            f"{t['id']}: babok_section={sec!r} は ^10\\.\\d+$ 形式必須"
        )


def test_attribution_present():
    data = _load()
    attrs = data.get("attributions")
    assert isinstance(attrs, list) and attrs, "attributions: 行が必須"
    sources = [a.get("source", "") for a in attrs]
    assert any("BABOK v3" in s for s in sources), (
        "attributions に BABOK v3 (IIBA) 由来の記述が必要"
    )


def test_purpose_is_concise_summary():
    """purpose は Claude 独自の 1 行要約 (原典文の長文転記禁止)。簡易チェックとして 200 字以内 + 改行なし"""
    data = _load()
    for t in data["techniques"]:
        purpose = t["purpose"]
        assert "\n" not in purpose, f"{t['id']}: purpose に改行 (長文転記の兆候)"
        assert len(purpose) <= 200, (
            f"{t['id']}: purpose が長すぎる ({len(purpose)} 字、200 字以下必須)"
        )
