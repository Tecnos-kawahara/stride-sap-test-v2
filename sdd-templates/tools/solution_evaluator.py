"""solution_evaluator.py — BABOK KA8 稼働後ソリューション評価 (FEAT-VALC01).

Tecnos-STRIDE VALUE Upstream Extension Phase C の KA8 evaluator。
business_need.yaml.success_criteria を目標 KPI として読み、kpi_source / adoption_survey
/ runs/*/lessons.md から実績を集計し、specs/<feature>/state/solution_eval_<ts>.md として
Markdown レポートを出力する。

Public:
    evaluate_solution(feature_dir, kpi_source, adoption_source) -> dict

attributions:
  - { source: "BABOK v3 (IIBA)", role: "framework backbone (KA8 — Solution Evaluation)", license: "fair-use, names only" }
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

POLICY_VERSION = "0.1.0-phase-a"


def _safe_load_yaml(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    if text.lstrip().startswith("---"):
        parts = text.split("---")
        if len(parts) >= 3:
            return yaml.safe_load(parts[1])
    return yaml.safe_load(text)


def _read_kpi_targets(feature_dir: Path) -> dict[str, Any]:
    bn_path = feature_dir / "upstream" / "phase_0_discovery" / "business_need.yaml"
    bn = _safe_load_yaml(bn_path) or {}
    crits = bn.get("success_criteria") or bn.get("kpis") or {}
    if isinstance(crits, list):
        # list 形式 → dict 化 (id → {target, ...})
        out = {}
        for item in crits:
            if not isinstance(item, dict):
                continue
            key = item.get("id") or item.get("name")
            if key:
                out[key] = item
        return out
    return crits if isinstance(crits, dict) else {}


def _read_kpi_actuals(kpi_source: Path | None) -> dict[str, Any]:
    data = _safe_load_yaml(kpi_source) or {}
    if isinstance(data.get("kpi_actuals"), dict):
        return data["kpi_actuals"]
    return data if isinstance(data, dict) else {}


def _compute_kpi_gaps(targets: dict, actuals: dict) -> dict:
    """各 target に対する actual との差分 (numeric の場合は値、その他は 'mismatch'/'match')."""
    gaps: dict[str, Any] = {}
    for key, tgt in targets.items():
        actual = actuals.get(key)
        if actual is None:
            gaps[key] = {"target": tgt, "actual": None, "status": "missing"}
            continue
        # numeric 比較
        try:
            t_val = tgt.get("target") if isinstance(tgt, dict) else tgt
            a_val = actual.get("actual") if isinstance(actual, dict) else actual
            t_num = float(t_val)
            a_num = float(a_val)
            delta = a_num - t_num
            ratio = (a_num / t_num) if t_num != 0 else None
            gaps[key] = {
                "target": t_num,
                "actual": a_num,
                "delta": delta,
                "ratio": ratio,
                "status": "met" if a_num >= t_num else "missed",
            }
        except (TypeError, ValueError):
            gaps[key] = {"target": tgt, "actual": actual, "status": "non_numeric"}
    return gaps


def _read_adoption(adoption_source: Path | None) -> dict[str, Any] | None:
    data = _safe_load_yaml(adoption_source)
    if data is None:
        return None
    if isinstance(data.get("adoption"), dict):
        return data["adoption"]
    return data if isinstance(data, dict) else None


def _count_issues_in_lessons(feature_dir: Path) -> int:
    """runs/*/lessons.md を再帰 scan して 'Issue' / 'issue:' / '- ' のような issue 件数を数える."""
    runs_dir = feature_dir / "runs"
    if not runs_dir.is_dir():
        return 0
    count = 0
    for lessons_md in runs_dir.rglob("lessons.md"):
        text = lessons_md.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            stripped = line.strip().lower()
            if stripped.startswith("- issue") or stripped.startswith("issue:"):
                count += 1
            elif stripped.startswith("- ") and "issue" in stripped:
                count += 1
    return count


def _generate_recommendations(
    gaps: dict, adoption: dict | None, issues_count: int
) -> list[str]:
    recs: list[str] = []
    missed = [k for k, g in gaps.items() if g.get("status") == "missed"]
    if missed:
        recs.append(
            f"未達 KPI {len(missed)} 件 ({', '.join(missed[:3])}{'…' if len(missed) > 3 else ''}) — 次 iteration で原因分析"
        )
    if adoption:
        rate = adoption.get("rate")
        if isinstance(rate, (int, float)) and rate < 0.5:
            recs.append(f"Adoption rate {rate:.0%} (低水準) — UX/トレーニング強化を検討")
    if issues_count >= 5:
        recs.append(f"Issues {issues_count} 件 — 上位優先度を次 iteration の Discovery にバックログ化")
    if not recs:
        recs.append("KPI / Adoption / Issues とも問題なし。次 iteration へ進行可")
    return recs


def _format_markdown_report(
    feature_id: str,
    targets: dict,
    actuals: dict,
    gaps: dict,
    adoption: dict | None,
    issues_count: int,
    recs: list[str],
    overall_pass: bool,
    timestamp: str,
) -> str:
    lines = [
        f"# Solution Evaluation Report — {feature_id}",
        "",
        f"- Timestamp (UTC): {timestamp}",
        f"- Policy version: {POLICY_VERSION}",
        f"- Overall: **{'PASS' if overall_pass else 'FAIL'}**",
        "",
        "## KPI Targets vs Actuals",
        "",
    ]
    if not gaps:
        lines.append("(no KPI targets defined in business_need.yaml.success_criteria)")
    else:
        lines.append("| KPI | Target | Actual | Status |")
        lines.append("|---|---|---|---|")
        for k, g in gaps.items():
            t = g.get("target")
            a = g.get("actual") if g.get("actual") is not None else "(missing)"
            s = g.get("status", "?")
            lines.append(f"| {k} | {t} | {a} | {s} |")
    lines.append("")

    lines.append("## Adoption")
    if adoption:
        lines.append("")
        for k, v in adoption.items():
            lines.append(f"- {k}: {v}")
    else:
        lines.append("(no adoption data — graceful skip)")
    lines.append("")

    lines.append(f"## Issues count: {issues_count} (from runs/*/lessons.md)")
    lines.append("")
    lines.append("## Recommendations")
    for r in recs:
        lines.append(f"- {r}")
    lines.append("")
    lines.append("## Attribution")
    lines.append("- BABOK v3 (IIBA), KA8 — Solution Evaluation, fair-use names only")
    return "\n".join(lines)


def evaluate_solution(
    feature_dir: Path,
    kpi_source: Path | None = None,
    adoption_source: Path | None = None,
) -> dict:
    """KA8 稼働後評価レポートを生成。

    Returns dict with:
        feature_id, kpi_targets, kpi_actuals, kpi_gaps, adoption, issues_count,
        recommendations, policy_version, overall_pass, report_path, report_markdown,
        warnings
    """
    feature_dir = Path(feature_dir)
    if not feature_dir.is_dir():
        raise FileNotFoundError(f"feature directory not found: {feature_dir}")

    feature_id = f"FEAT-{feature_dir.name.upper().replace('_', '')}"
    warnings: list[str] = []

    targets = _read_kpi_targets(feature_dir)
    if not targets:
        warnings.append(
            "business_need.yaml.success_criteria が空 or 未定義 — KPI 目標なしで graceful skip"
        )

    actuals: dict[str, Any] = {}
    if kpi_source is None:
        warnings.append("--kpi-source 未指定 — 実績 KPI 集計をスキップ")
    else:
        kpi_path = Path(kpi_source)
        if not kpi_path.is_file():
            warnings.append(f"kpi-source ファイル不在: {kpi_path}")
        else:
            actuals = _read_kpi_actuals(kpi_path)

    gaps = _compute_kpi_gaps(targets, actuals) if targets else {}

    adoption = None
    if adoption_source is None:
        warnings.append("--adoption-survey 未指定 — Adoption 集計をスキップ")
    else:
        adoption_path = Path(adoption_source)
        if not adoption_path.is_file():
            warnings.append(f"adoption-survey ファイル不在: {adoption_path}")
        else:
            adoption = _read_adoption(adoption_path)

    issues_count = _count_issues_in_lessons(feature_dir)
    recs = _generate_recommendations(gaps, adoption, issues_count)

    # overall_pass 判定: 著しい未達 (50% 以上の KPI が missed) または Issues 10 件以上で FAIL
    if gaps:
        missed = sum(1 for g in gaps.values() if g.get("status") == "missed")
        overall_pass = (missed / len(gaps) < 0.5) and issues_count < 10
    else:
        overall_pass = True

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    md = _format_markdown_report(
        feature_id, targets, actuals, gaps, adoption, issues_count, recs,
        overall_pass, timestamp,
    )

    state_dir = feature_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    report_path = state_dir / f"solution_eval_{timestamp}.md"
    report_path.write_text(md, encoding="utf-8")

    return {
        "feature_id": feature_id,
        "kpi_targets": targets,
        "kpi_actuals": actuals,
        "kpi_gaps": gaps,
        "adoption": adoption,
        "issues_count": issues_count,
        "recommendations": recs,
        "policy_version": POLICY_VERSION,
        "overall_pass": overall_pass,
        "report_path": str(report_path),
        "report_markdown": md,
        "warnings": warnings,
    }


def format_solution_report(result: dict) -> str:
    """stride_retro.py から呼び出される format helper (Markdown 整形済み文字列を返す)."""
    return result.get("report_markdown", "")


def main():
    """直接実行は推奨されない (stride retro --solution-eval 経由を使用)."""
    if len(sys.argv) < 2:
        sys.stderr.write(
            "Usage: solution_evaluator <feature_dir> [<kpi_source>] [<adoption_source>]\n"
        )
        return 2
    feature_dir = Path(sys.argv[1])
    kpi_src = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    adoption_src = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    try:
        result = evaluate_solution(feature_dir, kpi_src, adoption_src)
    except FileNotFoundError as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        return 1
    except yaml.YAMLError as e:
        sys.stderr.write(f"[ERROR] YAML parse failed: {e}\n")
        return 2

    print(result["report_markdown"])
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
