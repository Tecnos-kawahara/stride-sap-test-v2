"""Test: Constitution amendments (XV / XVI / XVII) integrity.

History:
  - Phase A (FEAT-VALA01, c3fb26d): proposed-only invariants + constitution body unchanged
  - Phase C (FEAT-VALC01, 2026-04-29): ratification + body merge complete
    Per Hitoshi さん明示承認 (§Rule 1-A 例外、Phase A 不変条件は Phase C 完了で論理的に置換)、
    test_each_amendment_has_proposed_status / test_constitution_main_unchanged を削除し、
    test_each_amendment_has_ratified_status / test_constitution_main_version_after_phase_c
    に置き換える。Phase A 起源の意図 (3 amendments + Attribution) は保存。

Covers AC-US-FEATVALC01-001-03 (Phase C 状態検証) +
       AC-US-FEATVALA01-001-04 の Phase C 進化版 (amendments ratified + 本体マージ済み).
"""
from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
AMENDMENTS_DIR = REPO_ROOT / "memory" / "constitution_amendments"
CONSTITUTION_MAIN = REPO_ROOT / "memory" / "constitution.md"

EXPECTED_AMENDMENTS = {
    "XV": "XV_baccm_completeness.md",
    "XVI": "XVI_layered_requirement_architecture.md",
    "XVII": "XVII_solution_evaluation_loop.md",
}


def test_amendments_directory_exists():
    assert AMENDMENTS_DIR.is_dir(), (
        f"constitution_amendments/ 不存在: {AMENDMENTS_DIR}"
    )


def test_three_amendment_files_exist():
    for article_id, filename in EXPECTED_AMENDMENTS.items():
        path = AMENDMENTS_DIR / filename
        assert path.is_file(), f"Article {article_id} 不存在: {path}"


def test_each_amendment_has_ratified_status():
    """各 amendment は status: ratified + Phase C 表記を含む (Phase C 完了状態)."""
    for article_id, filename in EXPECTED_AMENDMENTS.items():
        text = (AMENDMENTS_DIR / filename).read_text(encoding="utf-8")
        normalized = text.lower().replace("**", "")
        assert "status:" in normalized and "ratified" in normalized, (
            f"Article {article_id}: status: ratified 宣言が見つからない (Phase C で proposed → ratified に遷移済みのはず)"
        )
        # ratified 日付 + Phase C + FEAT-VALC01 の参照が見出し or status 行に含まれるべき
        assert "phase c" in normalized or "feat-valc01" in normalized, (
            f"Article {article_id}: Phase C / FEAT-VALC01 への参照が見つからない (ratified 履歴の追跡性)"
        )


def test_each_amendment_has_attribution():
    """各 amendment は Attribution セクションを含む"""
    for article_id, filename in EXPECTED_AMENDMENTS.items():
        text = (AMENDMENTS_DIR / filename).read_text(encoding="utf-8")
        lower = text.lower()
        has_attribution = (
            "attribution" in lower or "fair-use" in lower or "fair use" in lower
        )
        assert has_attribution, (
            f"Article {article_id}: Attribution / fair-use 表明が含まれていない"
        )


def test_constitution_main_version_after_phase_c():
    """memory/constitution.md がトップレベル version='6.0.0-tecnos-stride-value' に bump され、
    articles[] 配列に id: "XV" / "XVI" / "XVII" が存在する (Phase C 完了状態)."""
    text = CONSTITUTION_MAIN.read_text(encoding="utf-8")
    assert 'version: "6.0.0-tecnos-stride-value"' in text, (
        "memory/constitution.md トップレベル version が '6.0.0-tecnos-stride-value' でない "
        "(Phase C で MAJOR bump されているはず)"
    )
    # Article XV / XVI / XVII が articles[] 配列に追加されていること
    for article_id in ("XV", "XVI", "XVII"):
        assert f'id: "{article_id}"' in text, (
            f"memory/constitution.md articles[] に id: \"{article_id}\" が含まれていない "
            f"(Phase C で本体マージ済みのはず)"
        )
    # last_reviewed_at が 2026-04-29 (Phase C 完了日) に更新されている
    assert 'last_reviewed_at: "2026-04-29"' in text, (
        "memory/constitution.md last_reviewed_at が Phase C 完了日 '2026-04-29' に更新されていない"
    )


def test_attributions_have_required_sources():
    """Article XV は BABOK v3 / Article XVI は 4-layer Requirements Architecture + BABOK / Article XVII は BABOK"""
    expectations = {
        "XV": ["babok"],
        "XVI": ["layered", "babok"],
        "XVII": ["babok"],
    }
    for article_id, required in expectations.items():
        filename = EXPECTED_AMENDMENTS[article_id]
        text = (AMENDMENTS_DIR / filename).read_text(encoding="utf-8").lower()
        for keyword in required:
            assert keyword in text, (
                f"Article {article_id}: '{keyword}' への参照が見つからない (attribution 不足)"
            )
