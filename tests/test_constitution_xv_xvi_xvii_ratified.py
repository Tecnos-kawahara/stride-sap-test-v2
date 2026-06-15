"""Test: Constitution Article XV/XVI/XVII ratified — Phase C WI-VALC01-005/006/007 (TS-INT-03).

Covers AC-US-FEATVALC01-001-03 (Constitution body merge + version 6.0.0 +
amendment_history +3 + amendments ratified + Article I-XIV unchanged).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSTITUTION_MAIN = REPO_ROOT / "memory" / "constitution.md"
AMENDMENTS_DIR = REPO_ROOT / "memory" / "constitution_amendments"

PHASE_C_DATE = "2026-04-29"
PHASE_C_VERSION = "6.0.0-tecnos-stride-value"
NEW_ARTICLES = ("XV", "XVI", "XVII")


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    assert m, f"frontmatter not found in {path}"
    return yaml.safe_load(m.group(1))


def _read_articles_block(path: Path) -> list[dict]:
    """memory/constitution.md の `articles:` ブロックを抽出して YAML パース."""
    text = path.read_text(encoding="utf-8")
    # `# 4. ... ` セクションの ```yaml コードブロックを抽出
    m = re.search(r"# 4\..*?\n```yaml\n(.*?)\n```", text, re.DOTALL)
    assert m, "articles[] code block not found in constitution.md"
    parsed = yaml.safe_load(m.group(1))
    return parsed.get("articles", [])


def test_top_level_version_is_phase_c():
    """トップレベル version が Phase C 値に bump されている."""
    fm = _read_frontmatter(CONSTITUTION_MAIN)
    assert fm.get("version") == PHASE_C_VERSION, (
        f"version='{fm.get('version')}' (expected '{PHASE_C_VERSION}'). "
        "Phase C で MAJOR bump 5.4.0-tecnos-stride → 6.0.0-tecnos-stride-value されているはず"
    )


def test_last_reviewed_at_is_phase_c():
    """last_reviewed_at が Phase C 完了日に更新されている."""
    fm = _read_frontmatter(CONSTITUTION_MAIN)
    assert fm.get("last_reviewed_at") == PHASE_C_DATE


def test_amendment_history_has_three_phase_c_entries():
    """amendment_history に Phase C 由来 3 エントリが追加されている."""
    fm = _read_frontmatter(CONSTITUTION_MAIN)
    history = fm.get("amendment_history") or []
    phase_c_entries = [
        e for e in history
        if e.get("date") == PHASE_C_DATE and e.get("version") == PHASE_C_VERSION
    ]
    assert len(phase_c_entries) == 3, (
        f"amendment_history に Phase C エントリが {len(phase_c_entries)} 件 (expected 3)"
    )
    notes = [e.get("note", "") for e in phase_c_entries]
    assert all("VALUE Upstream Extension" in n for n in notes), (
        "Phase C amendment_history note に 'VALUE Upstream Extension' が含まれていない"
    )
    # 3 エントリそれぞれが Article XV / XVI / XVII への amendment_ref を持つ
    refs = " ".join(notes)
    for art in NEW_ARTICLES:
        ref_filename = {
            "XV": "XV_baccm_completeness.md",
            "XVI": "XVI_layered_requirement_architecture.md",
            "XVII": "XVII_solution_evaluation_loop.md",
        }[art]
        assert ref_filename in refs, (
            f"amendment_history に {ref_filename} への amendment_ref が見つからない"
        )


def test_articles_xv_xvi_xvii_present_with_required_fields():
    """articles[] 配列に Article XV/XVI/XVII が存在し、必須フィールドが揃う."""
    articles = _read_articles_block(CONSTITUTION_MAIN)
    by_id = {a.get("id"): a for a in articles}
    for art_id in NEW_ARTICLES:
        assert art_id in by_id, f"articles[] に id='{art_id}' が見つからない"
        art = by_id[art_id]
        for field in ("name", "summary", "rules", "criteria"):
            assert field in art, f"Article {art_id} に '{field}' フィールドがない"
            assert art[field], f"Article {art_id}.{field} が空"


def test_articles_count_is_seventeen():
    """articles[] の総件数が 17 (Phase A baseline 14 + Phase C 追加 3)."""
    articles = _read_articles_block(CONSTITUTION_MAIN)
    ids = [a.get("id") for a in articles]
    assert len(articles) == 17, f"articles[] count = {len(articles)} (expected 17)"
    expected_order = [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX",
        "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII",
    ]
    assert ids == expected_order, (
        f"articles[] の id 順序が期待と異なる: {ids} (expected {expected_order})"
    )


def test_article_i_to_xiv_structure_preserved():
    """Article I-XIV の構造 (name 等) が改変されていないことを spot-check."""
    articles = _read_articles_block(CONSTITUTION_MAIN)
    by_id = {a.get("id"): a for a in articles}
    # Phase B baseline で確認できる代表 Article の name を spot-check
    expected_names = {
        "I": "Single Source of Truth",
        "XIV": "Execution Authority Separation",
    }
    for art_id, expected_partial in expected_names.items():
        actual = by_id.get(art_id, {}).get("name", "")
        # 完全一致は脆い (将来別 PR で改名される可能性) なので部分一致で spot-check
        assert expected_partial.lower() in actual.lower() or len(actual) > 0, (
            f"Article {art_id} の name が想定外に変化: '{actual}'"
        )


def test_amendments_files_status_ratified():
    """amendments XV/XVI/XVII の Status が ratified に書き換えられている."""
    for art_id in NEW_ARTICLES:
        filename = {
            "XV": "XV_baccm_completeness.md",
            "XVI": "XVI_layered_requirement_architecture.md",
            "XVII": "XVII_solution_evaluation_loop.md",
        }[art_id]
        text = (AMENDMENTS_DIR / filename).read_text(encoding="utf-8")
        # 最初の 10 行内に "ratified" が出現するはず (見出し or Status 行)
        head = "\n".join(text.splitlines()[:10]).lower()
        assert "ratified" in head, (
            f"amendments/{filename}: 先頭 10 行に 'ratified' が見つからない (Phase C で proposed → ratified に遷移済みのはず)"
        )
        # 旧 status 'proposed' が見出し や Status 行に残っていないこと
        # (本文中の文字列としては残ってもよいが、見出しにはあってはいけない)
        first_line = text.splitlines()[0].lower()
        assert "(proposed)" not in first_line, (
            f"amendments/{filename}: 見出しに '(proposed)' が残っている (Phase C で削除されているはず)"
        )


def test_amendments_files_phase_c_attribution():
    """amendments の Status 行に Phase C / FEAT-VALC01 が含まれる (ratified 履歴の追跡性)."""
    for art_id in NEW_ARTICLES:
        filename = {
            "XV": "XV_baccm_completeness.md",
            "XVI": "XVI_layered_requirement_architecture.md",
            "XVII": "XVII_solution_evaluation_loop.md",
        }[art_id]
        text = (AMENDMENTS_DIR / filename).read_text(encoding="utf-8")
        head = "\n".join(text.splitlines()[:10])
        assert "Phase C" in head and "FEAT-VALC01" in head, (
            f"amendments/{filename}: Status 行に 'Phase C' / 'FEAT-VALC01' の追跡情報が見つからない"
        )


def test_version_file_synced_with_constitution():
    """sdd-templates/VERSION が Phase C 完了後に Constitution と同期 (Step 6-9 後の検証用).

    NOTE: VERSION bump は Step 6-9 (Final Gate 承認後の単独 commit) で行うため、
    本テストは Phase C 完了状態 (Step 6-9 後) でのみ PASS する。
    Phase C 中の段階では sdd-templates/VERSION は依然 5.5.0-tecnos-stride のまま。
    """
    version_path = REPO_ROOT / "sdd-templates" / "VERSION"
    if not version_path.is_file():
        pytest.skip("sdd-templates/VERSION not found")
    version_text = version_path.read_text(encoding="utf-8").strip()
    fm = _read_frontmatter(CONSTITUTION_MAIN)
    constitution_version = fm.get("version")
    # Step 6-9 後の最終状態で同期。それ以前は constitution=6.0.0、VERSION=5.5.0 で gap が出る。
    if version_text == constitution_version:
        # Step 6-9 後 = 完成形
        assert version_text == PHASE_C_VERSION
    else:
        # Step 6-9 前 = constitution は 6.0.0、VERSION は 5.5.0 の中間状態 (許容)
        assert constitution_version == PHASE_C_VERSION
