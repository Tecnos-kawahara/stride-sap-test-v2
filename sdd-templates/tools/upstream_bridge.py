"""upstream_bridge.py — Phase 0/0.3/0.5 → Phase 1 自動 populate (FEAT-VALC01).

Tecnos-STRIDE VALUE Upstream Extension Phase C の中核ツール。
Discovery / Elicit / Context Modelling 成果物を Phase 1 basic_design.md links に
populate (--apply 時のみ実書込) し、business_usecase.yaml ベースで BPMN-TASK-NNN
候補を stdout Markdown で出力する。

Phase 1 immutability: --apply は APPROVAL.md の Gate 1 / Gate 2 が未承認の feature にのみ
許可。Gate 1 or Gate 2 が承認済みなら exit 1 + Phase 1 immutability メッセージ。

実装は process.bpmn を変更しない (BPMN は人間責務) / implementation-details/* も書かない
(Phase 2 領域)。

Public:
    bridge_to_phase1(feature_dir, target_section="phase1", apply=False) -> dict

Exit codes:
    0 = OK (warnings あっても 0)
    1 = upstream/ ディレクトリ不在 / Phase 1 immutability violation
    2 = ERROR (YAML パース失敗等)

attributions:
  - { source: "BABOK v3 (IIBA)", role: "framework backbone (KA7)", license: "fair-use, names only" }
  - { source: "4-layer Requirements Architecture (concept reference, no proprietary brand)", role: "structural integrity (4-layer)", license: "fair-use, layer names only" }
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stride_shared_lib import load_yaml_with_frontmatter

PHASE_DIRS = {
    "phase_0_discovery": [
        "business_need.yaml",
        "value_canvas.yaml",
        "stakeholder_map.yaml",
        "goal_tree.yaml",
        "change_strategy.yaml",
        "context_map.yaml",
        "risk_register.yaml",
    ],
    "phase_0_3_elicit": [
        "elicitation_plan.yaml",
        "elicitation_results.yaml",
    ],
    "phase_0_5_context_modelling": [
        "actor_system.yaml",
        "business_usecase.yaml",
        "information_state.yaml",
        "condition_variation.yaml",
        "usecase_complex.yaml",
        "requirements_architecture.yaml",
    ],
}

VALID_TARGETS = {"phase1"}

LINKS_TO_POPULATE = {
    "upstream_dir_ref": "specs/{feature}/upstream/",
    "upstream_policy_ref": "shared/policies/upstream_policy.yaml",
    "baccm_completeness_ref": "shared/policies/baccm_completeness.yaml",
}

BLOCKER_GATE_APPROVED_MSG = (
    "[BLOCKER] basic_design.md is locked after Gate 1/2 approval (Phase 1 immutability).\n"
    "対応: change_log を作成し、Gate 1/2 を再承認してから --apply を実行する。\n"
    "      または、dry-run (--apply なし) で populate plan のみ確認する。\n"
)


def is_gate_approved(approval_md_path: Path, gate_label: str) -> bool:
    """APPROVAL.md の指定 Gate セクションが承認済みかを判定する.

    Returns True iff:
        - The section under '## <gate_label>' has all checkbox items as '[x]' (no '[ ]')
        - At least one '[x]' exists (空セクション保護)
        - The approver name field is filled (not '_____' placeholder)
    """
    if not approval_md_path.exists():
        return False
    text = approval_md_path.read_text(encoding="utf-8")

    pattern = rf"##\s+{re.escape(gate_label)}\s*\n(.*?)(?:\n---\s*\n|$)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return False
    section = m.group(1)

    if "- [ ]" in section:
        return False
    if "- [x]" not in section:
        return False

    approver_match = re.search(r"承認者:\s*(\S+)", section)
    if not approver_match:
        return False
    approver = approver_match.group(1).strip()
    # placeholder ('_____' のような全 underscore 文字列) を弾く。
    # 任意の長さの underscore のみで構成された文字列を未承認扱い (`_` 1 個でも、
    # 100 個でも判定できる)。実名は必ず非 underscore 文字を含むため True 判定される.
    if not approver or set(approver) <= {"_"}:
        return False

    return True


def _safe_load_yaml(path: Path) -> dict[str, Any] | None:
    """YAML を読み込む (Phase A frontmatter 対応 v6.0 bugfix01 で共通 helper に統合).

    旧実装は parts[1] (frontmatter 側) を返すバグ + maxsplit 指定なしの 2 つの問題があった.
    現在は stride_shared_lib.load_yaml_with_frontmatter(strict=True) に委譲し、parts[2]
    (body 側) を maxsplit=2 固定で正しく返す。

    yaml.YAMLError は strict=True により呼び出し元へ伝播、main() の except 節で exit 2.
    """
    return load_yaml_with_frontmatter(path, strict=True)


def _collect_phase0_artifacts(feature_dir: Path) -> tuple[dict, list, list]:
    """upstream/ 配下の 15 YAML を読み込む。欠損は warnings に記録."""
    artifacts: dict[str, dict] = {}
    warnings: list[str] = []
    found: list[str] = []
    for phase_subdir, files in PHASE_DIRS.items():
        for fname in files:
            path = feature_dir / "upstream" / phase_subdir / fname
            if not path.is_file():
                warnings.append(
                    f"missing upstream artifact: upstream/{phase_subdir}/{fname}"
                )
                continue
            data = _safe_load_yaml(path)
            artifacts[fname] = data if data else {}
            found.append(f"upstream/{phase_subdir}/{fname}")
    return artifacts, warnings, found


def _generate_task_candidates(artifacts: dict[str, dict]) -> list[dict]:
    """business_usecase.yaml の use cases から BPMN-TASK-NNN 候補を生成。"""
    bu = artifacts.get("business_usecase.yaml") or {}
    use_cases = []
    for key in ("use_cases", "business_use_cases", "scenarios"):
        if isinstance(bu.get(key), list):
            use_cases = bu[key]
            break
    candidates = []
    for idx, uc in enumerate(use_cases, start=1):
        if not isinstance(uc, dict):
            continue
        name = uc.get("name") or uc.get("title") or uc.get("id") or f"UseCase {idx}"
        candidates.append(
            {
                "bpmn_id_suggestion": f"BPMN-TASK-{idx:03d}",
                "name": str(name),
                "source_artifact": "business_usecase.yaml",
            }
        )
    return candidates


def _format_task_candidates_markdown(
    candidates: list[dict], feature_id: str
) -> str:
    """Task candidates を Markdown に整形 (stdout 出力用)."""
    if not candidates:
        return (
            f"## BPMN Task Candidates ({feature_id})\n\n"
            "(no candidates: business_usecase.yaml が空 or 未生成)\n"
        )
    lines = [f"## BPMN Task Candidates ({feature_id})", ""]
    lines.append("| Suggested BPMN ID | Task Name | Source |")
    lines.append("|---|---|---|")
    for c in candidates:
        lines.append(
            f"| {c['bpmn_id_suggestion']} | {c['name']} | {c['source_artifact']} |"
        )
    lines.append("")
    lines.append(
        "> ⚠ これは Phase 1 BPMN 設計の参考情報です。"
        "実際の process.bpmn 編集は Gate 2 承認前に人間が行ってください。"
    )
    return "\n".join(lines)


def _populate_basic_design_links(
    feature_dir: Path, feature_id: str, dry_run: bool
) -> tuple[dict, list]:
    """basic_design.md links に upstream_* 参照を追加 (dry_run=False のとき実書込)."""
    bd_path = feature_dir / "basic_design.md"
    populated: dict[str, str] = {}
    skipped: list[str] = []
    feature_name = feature_dir.name

    if not bd_path.is_file():
        return populated, [f"basic_design.md not found: {bd_path}"]

    text = bd_path.read_text(encoding="utf-8")

    # frontmatter links 領域を見つける (--- ... --- の中の links: ブロック)
    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not fm_match:
        return populated, ["frontmatter not found in basic_design.md"]

    fm = fm_match.group(1)
    links_match = re.search(
        r"(^links:\n(?:[ \t]+\w+:.*\n)+)", fm, re.MULTILINE
    )
    if not links_match:
        return populated, ["links: section not found in frontmatter"]
    links_block = links_match.group(1)

    new_lines = []
    for key, template in LINKS_TO_POPULATE.items():
        value = template.format(feature=feature_name)
        if re.search(rf"^[ \t]+{re.escape(key)}:", links_block, re.MULTILINE):
            skipped.append(f"links.{key} already present")
        else:
            new_lines.append(f'  {key}: "{value}"')
            populated[key] = value

    if dry_run or not new_lines:
        return populated, skipped

    insertion = "\n".join(new_lines) + "\n"
    new_links_block = links_block.rstrip() + "\n" + insertion
    new_fm = fm.replace(links_block, new_links_block, 1)
    new_text = text.replace(fm, new_fm, 1)
    bd_path.write_text(new_text, encoding="utf-8")
    return populated, skipped


def _format_populate_plan_markdown(
    populated: dict, skipped: list, feature_id: str, dry_run: bool
) -> str:
    """populate 計画を Markdown に整形 (stdout 出力用)."""
    mode = "dry-run (preview)" if dry_run else "applied"
    lines = [
        f"## basic_design.md links populate plan ({feature_id}, {mode})",
        "",
    ]
    if populated:
        lines.append("**Added (or to be added) keys:**")
        for k, v in populated.items():
            lines.append(f"- `{k}`: `{v}`")
    else:
        lines.append("(no new keys to add — existing links already include upstream refs)")
    lines.append("")
    if skipped:
        lines.append("**Skipped (already present):**")
        for s in skipped:
            lines.append(f"- {s}")
        lines.append("")
    return "\n".join(lines)


def bridge_to_phase1(
    feature_dir: Path,
    target_section: str = "phase1",
    apply: bool = False,
) -> dict:
    """Phase 0 成果物 → Phase 1 basic_design.md links + BPMN Task 候補.

    Returns dict with:
        feature_id, target_section, populated_links, task_candidates,
        task_candidates_markdown, populate_plan_markdown, warnings, skipped
    """
    feature_dir = Path(feature_dir)
    if not feature_dir.is_dir():
        raise FileNotFoundError(f"feature directory not found: {feature_dir}")
    if target_section not in VALID_TARGETS:
        raise ValueError(
            f"invalid target_section: {target_section}. Must be one of {VALID_TARGETS}"
        )

    upstream_dir = feature_dir / "upstream"
    if not upstream_dir.is_dir():
        raise FileNotFoundError(
            f"upstream/ directory not found in {feature_dir}. "
            "Run `stride upstream init <feature> --phase discovery` first."
        )

    feature_id = f"FEAT-{feature_dir.name.upper().replace('_', '')}"

    # --apply の Gate immutability check
    if apply:
        approval_path = feature_dir / "APPROVAL.md"
        if is_gate_approved(approval_path, "Gate 1: Basic Design") or is_gate_approved(
            approval_path, "Gate 2: BPMN"
        ):
            raise PermissionError(BLOCKER_GATE_APPROVED_MSG)

    artifacts, warnings, found = _collect_phase0_artifacts(feature_dir)
    candidates = _generate_task_candidates(artifacts)
    task_md = _format_task_candidates_markdown(candidates, feature_id)

    populated, populate_skipped = _populate_basic_design_links(
        feature_dir, feature_id, dry_run=not apply
    )
    populate_md = _format_populate_plan_markdown(
        populated, populate_skipped, feature_id, dry_run=not apply
    )

    return {
        "feature_id": feature_id,
        "target_section": target_section,
        "populated_links": populated,
        "task_candidates": candidates,
        "task_candidates_markdown": task_md,
        "populate_plan_markdown": populate_md,
        "warnings": warnings,
        "skipped": populate_skipped,
        "artifacts_found": found,
    }


def main():
    parser = argparse.ArgumentParser(
        prog="stride upstream-bridge",
        description="Phase 0/0.3/0.5 → Phase 1 basic_design.md links populate + BPMN Task 候補出力",
    )
    parser.add_argument(
        "feature_dir",
        type=Path,
        help="specs/<feature>/ ディレクトリパス",
    )
    parser.add_argument(
        "--target",
        choices=["phase1"],
        default="phase1",
        dest="target_section",
        help="Target section (Phase C は phase1 のみ)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="basic_design.md links に実書込 (Gate 1/2 未承認 feature のみ許可)",
    )
    args = parser.parse_args()

    try:
        result = bridge_to_phase1(
            args.feature_dir,
            target_section=args.target_section,
            apply=args.apply,
        )
    except FileNotFoundError as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        return 1
    except PermissionError as e:
        sys.stderr.write(str(e))
        return 1
    except yaml.YAMLError as e:
        sys.stderr.write(f"[ERROR] YAML parse failed: {e}\n")
        return 2
    except ValueError as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        return 2

    print(result["populate_plan_markdown"])
    print(result["task_candidates_markdown"])
    if result["warnings"]:
        sys.stderr.write("\n## Warnings\n")
        for w in result["warnings"]:
            sys.stderr.write(f"- {w}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
