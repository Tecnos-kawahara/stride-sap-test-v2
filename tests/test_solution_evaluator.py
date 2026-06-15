"""Test: solution_evaluator.evaluate_solution() — Phase C WI-VALC01-003 (TS-INT-02).

Covers AC-US-FEATVALC01-001-02 (BABOK KA8 KPI/Adoption/Issues 集計 +
Markdown レポート出力 + graceful skip).
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from solution_evaluator import (
    POLICY_VERSION,
    evaluate_solution,
    format_solution_report,
)


def _setup_feature(tmp_path: Path, name: str = "feat_eval") -> Path:
    fd = tmp_path / "specs" / name
    (fd / "upstream" / "phase_0_discovery").mkdir(parents=True)
    (fd / "runs" / "WI-001" / "RUN-X").mkdir(parents=True)
    return fd


def _write_business_need_with_kpis(fd: Path):
    (fd / "upstream" / "phase_0_discovery" / "business_need.yaml").write_text(
        textwrap.dedent("""\
            artifact: business_need
            success_criteria:
              kpi_lead_time:
                target: 30
                unit: days
              kpi_cost_reduction:
                target: 100000
                unit: yen
            """),
        encoding="utf-8",
    )


def _write_kpi_actuals(path: Path, lead_time: float, cost: float):
    path.write_text(
        textwrap.dedent(f"""\
            kpi_actuals:
              kpi_lead_time:
                actual: {lead_time}
              kpi_cost_reduction:
                actual: {cost}
            """),
        encoding="utf-8",
    )


def _write_adoption(path: Path, rate: float, satisfaction: float):
    path.write_text(
        textwrap.dedent(f"""\
            adoption:
              rate: {rate}
              satisfaction: {satisfaction}
            """),
        encoding="utf-8",
    )


def _write_lessons_with_issues(fd: Path, issues_count: int):
    lessons = "\n".join(f"- Issue {i}: sample issue desc" for i in range(issues_count))
    (fd / "runs" / "WI-001" / "RUN-X" / "lessons.md").write_text(
        f"# Lessons\n\n{lessons}\n", encoding="utf-8"
    )


def test_kpi_targets_met_overall_pass(tmp_path: Path):
    """KPI 目標達成 → overall_pass=True."""
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    kpi_src = tmp_path / "kpi.yaml"
    _write_kpi_actuals(kpi_src, lead_time=35, cost=120000)  # 両方 target 以上
    result = evaluate_solution(fd, kpi_source=kpi_src, adoption_source=None)
    assert result["overall_pass"] is True
    assert result["kpi_gaps"]["kpi_lead_time"]["status"] == "met"


def test_kpi_targets_missed_overall_fail(tmp_path: Path):
    """KPI 半数以上未達 → overall_pass=False."""
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    kpi_src = tmp_path / "kpi.yaml"
    _write_kpi_actuals(kpi_src, lead_time=10, cost=50000)  # 両方 target 未満
    result = evaluate_solution(fd, kpi_source=kpi_src, adoption_source=None)
    assert result["overall_pass"] is False
    assert result["kpi_gaps"]["kpi_lead_time"]["status"] == "missed"
    assert result["kpi_gaps"]["kpi_cost_reduction"]["status"] == "missed"


def test_adoption_aggregation(tmp_path: Path):
    """adoption_source 指定で adoption rate/satisfaction が集計される."""
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    adoption_src = tmp_path / "adoption.yaml"
    _write_adoption(adoption_src, rate=0.75, satisfaction=4.2)
    result = evaluate_solution(fd, kpi_source=None, adoption_source=adoption_src)
    assert result["adoption"] is not None
    assert result["adoption"]["rate"] == 0.75
    assert result["adoption"]["satisfaction"] == 4.2


def test_issues_count_from_lessons(tmp_path: Path):
    """runs/*/lessons.md から issue 件数が集計される."""
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    _write_lessons_with_issues(fd, issues_count=3)
    result = evaluate_solution(fd, kpi_source=None, adoption_source=None)
    assert result["issues_count"] == 3


def test_graceful_skip_no_kpi_no_adoption(tmp_path: Path):
    """kpi/adoption 欠損で graceful skip + warnings、overall_pass=True."""
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    result = evaluate_solution(fd, kpi_source=None, adoption_source=None)
    assert result["overall_pass"] is True
    assert any("kpi-source" in w for w in result["warnings"])
    assert any("adoption-survey" in w for w in result["warnings"])


def test_markdown_report_written_to_state_dir(tmp_path: Path):
    """specs/<feature>/state/solution_eval_<ts>.md として Markdown レポートが出力される."""
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    result = evaluate_solution(fd, kpi_source=None, adoption_source=None)
    rp = Path(result["report_path"])
    assert rp.is_file()
    assert rp.parent.name == "state"
    assert rp.name.startswith("solution_eval_") and rp.suffix == ".md"
    md = rp.read_text(encoding="utf-8")
    assert "# Solution Evaluation Report" in md
    assert "BABOK v3" in md  # attribution


def test_format_solution_report_returns_markdown(tmp_path: Path):
    fd = _setup_feature(tmp_path)
    _write_business_need_with_kpis(fd)
    result = evaluate_solution(fd, kpi_source=None, adoption_source=None)
    md = format_solution_report(result)
    assert isinstance(md, str)
    assert len(md) > 100


def test_policy_version_constant():
    assert POLICY_VERSION == "0.1.0-phase-a"


def test_missing_feature_dir_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        evaluate_solution(tmp_path / "nonexistent", None, None)
