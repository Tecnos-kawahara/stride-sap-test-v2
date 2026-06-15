"""upstream_migration_helper.py — v5.x → v6.0 Phase 0 yaml seed reverse generation (FEAT-VALD01).

Tecnos-STRIDE VALUE Upstream Extension Phase D の中核ツール。
既存 v5.x basic_design.md (canonical YAML SSoT) を読み込み、BACCM 6 軸
(change / need / solution / stakeholder / value / context) ごとに Phase 0 yaml seed を
逆生成する。dry-run は stdout に Markdown 形式で出力、--apply は
specs/<feature>/upstream/phase_0_discovery/*.yaml に実書込。

各フィールドは「自動抽出可能 (auto_extracted)」「要人間確認 (human_review_needed)」
ラベルで分類される。helper は seed (種) のみを生成し、refinement は人間が責務。

実装は upstream_bridge.py パターンに準拠 (positional feature_dir + --apply フラグ)。
stride_shared_lib.{extract_canonical_yaml, extract_frontmatter_yaml} で frontmatter +
canonical YAML block を分離抽出する (bugfix v7 で導入された正規 API)。

Public:
    migrate_v5x_to_v6(feature_dir, apply=False, profile=None) -> dict

Exit codes:
    0 = OK (warnings あっても 0)
    1 = feature_dir または basic_design.md 不在
    2 = ERROR (YAML パース失敗等)

attributions:
  - { source: "BABOK v3 (IIBA)", role: "framework backbone (KA4 / KA6 / KA7)", license: "fair-use, names only" }
  - { source: "4-layer Requirements Architecture (concept reference, no proprietary brand)", role: "structural integrity", license: "fair-use, layer names only" }
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stride_shared_lib import (
    extract_canonical_yaml,
    extract_frontmatter_yaml,
)

PHASE_0_DIR = "phase_0_discovery"

BACCM_AXES = ("change", "need", "solution", "stakeholder", "value", "context")

ARTIFACTS = (
    "business_need.yaml",
    "value_canvas.yaml",
    "stakeholder_map.yaml",
    "context_map.yaml",
    "risk_register.yaml",
    "change_strategy.yaml",
    "goal_tree.yaml",
)


def _safe_get(d: Any, *keys: str, default: Any = None) -> Any:
    """ネストした dict から安全に値を取得する。途中で None や非 dict が出ても default を返す。"""
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def _detect_profile(bd: dict) -> str:
    """basic_design.md SSoT YAML から profile を検出する (見つからなければ enterprise-erp)。"""
    profile = _safe_get(bd, "basic_design", "profile", default=None)
    if profile in ("enterprise-erp", "saas-integration", "prototype"):
        return profile
    return "enterprise-erp"


def _detect_feature_id(bd: dict, feature_dir: Path) -> str:
    """basic_design.md から feature_id を取得、なければ dir 名から推定。"""
    feature_id = bd.get("feature_id") if isinstance(bd, dict) else None
    if isinstance(feature_id, str) and feature_id.startswith("FEAT-"):
        return feature_id
    return f"FEAT-{feature_dir.name.upper().replace('_', '')}"


def _seed_business_need(bd: dict) -> tuple[dict, list[str]]:
    """need 軸 → business_need.yaml seed."""
    auto, human = [], []
    what = _safe_get(bd, "basic_design", "context", "what", default="").strip()
    why = _safe_get(bd, "basic_design", "context", "why", default="").strip()
    domain_caps = _safe_get(bd, "basic_design", "business_domain", "capability", default="")

    if what:
        auto.append("need.what (basic_design.context.what から自動抽出)")
    else:
        human.append("need.what (basic_design.context.what が空、業務専門家確認)")
    if why:
        auto.append("need.why (basic_design.context.why から自動抽出)")
    else:
        human.append("need.why (basic_design.context.why が空、業務専門家確認)")

    seed = {
        "artifact": "business_need",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "need": {
            "what": what or "<TODO: 業務専門家確認>",
            "why": why or "<TODO: 業務専門家確認>",
            "capability": domain_caps or "<TODO: 業務専門家確認>",
        },
    }
    return seed, human


def _seed_value_canvas(bd: dict) -> tuple[dict, list[str]]:
    """value 軸 → value_canvas.yaml seed."""
    auto, human = [], []
    domain = _safe_get(bd, "basic_design", "business_domain", default={})
    objects = domain.get("domain_objects", []) if isinstance(domain, dict) else []
    in_scope = _safe_get(bd, "basic_design", "scope", "in", default=[])

    if objects:
        auto.append("value.domain_objects (basic_design.business_domain.domain_objects から自動抽出)")
    else:
        human.append("value.domain_objects (空、業務専門家確認)")
    if in_scope:
        auto.append("value.proposition (basic_design.scope.in から推定)")
    else:
        human.append("value.proposition (scope.in が空、業務専門家確認)")

    seed = {
        "artifact": "value_canvas",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "value": {
            "current_state": "<TODO: 業務専門家確認>",
            "target_state": "<TODO: 業務専門家確認>",
            "proposition": in_scope[:5] if isinstance(in_scope, list) else [],
            "domain_objects": objects,
        },
    }
    return seed, human


def _seed_stakeholder_map(bd: dict) -> tuple[dict, list[str]]:
    """stakeholder 軸 → stakeholder_map.yaml seed."""
    auto, human = [], []
    raci_actors = _safe_get(bd, "basic_design", "raci_plus", "actors", default=[])
    owners = bd.get("owners", []) if isinstance(bd, dict) else []
    who = _safe_get(bd, "basic_design", "context", "who", default="").strip()

    actors = []
    if isinstance(raci_actors, list):
        actors.extend(raci_actors)
        auto.append("stakeholder.actors (basic_design.raci_plus.actors から自動抽出)")
    if isinstance(owners, list):
        for o in owners:
            if isinstance(o, dict) and o.get("name"):
                actors.append(f"{o['name']} ({o.get('role', '')})")
        if owners:
            auto.append("stakeholder.owners (basic_design top-level owners から追加)")

    if not who:
        human.append("stakeholder.context_who (basic_design.context.who が空、業務専門家確認)")
    else:
        auto.append("stakeholder.context_who (basic_design.context.who から自動抽出)")

    if not actors:
        human.append("stakeholder.actors (raci_plus.actors / owners が空、業務専門家確認)")

    seed = {
        "artifact": "stakeholder_map",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "stakeholder": {
            "actors": actors,
            "context_who": who or "<TODO: 業務専門家確認>",
            "layers_recommended_min": 5,  # enterprise-erp は 5 層以上推奨
        },
    }
    return seed, human


def _seed_context_map(bd: dict) -> tuple[dict, list[str]]:
    """context 軸 → context_map.yaml seed."""
    auto, human = [], []
    systems = _safe_get(bd, "basic_design", "systems", default=[])
    domain = _safe_get(bd, "basic_design", "business_domain", default={})

    if systems:
        auto.append("context.systems (basic_design.systems から自動抽出)")
    else:
        human.append("context.systems (空、業務専門家確認)")
    if domain.get("value_chain") if isinstance(domain, dict) else None:
        auto.append("context.value_chain (basic_design.business_domain.value_chain から自動抽出)")
    else:
        human.append("context.value_chain (空、業務専門家確認)")

    seed = {
        "artifact": "context_map",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "context": {
            "systems": systems,
            "value_chain": _safe_get(bd, "basic_design", "business_domain", "value_chain", default=""),
            "boundaries": "<TODO: 業務専門家確認>",
        },
    }
    return seed, human


def _seed_risk_register(bd: dict) -> tuple[dict, list[str]]:
    """risks → risk_register.yaml seed (BACCM 軸とは独立だが Phase 0 必須)."""
    auto, human = [], []
    decisions = _safe_get(bd, "basic_design", "decisions", default=[])
    exceptions = _safe_get(bd, "basic_design", "exceptions", default=[])

    risks = []
    if isinstance(decisions, list):
        for d in decisions:
            if isinstance(d, dict):
                risks.append({
                    "from": "basic_design.decisions",
                    "id": d.get("id", ""),
                    "context": d.get("context", ""),
                })
        if decisions:
            auto.append("risk.from_decisions (basic_design.decisions から自動抽出)")
    if isinstance(exceptions, list) and exceptions:
        auto.append("risk.from_exceptions (basic_design.exceptions から自動抽出)")
    if not risks:
        human.append("risk.register (基本リスク一覧、業務専門家確認)")

    seed = {
        "artifact": "risk_register",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "risks": risks,
    }
    return seed, human


def _seed_change_strategy(bd: dict) -> tuple[dict, list[str]]:
    """change 軸 → change_strategy.yaml seed."""
    auto, human = [], []
    delivery = _safe_get(bd, "basic_design", "delivery_model", default={})

    if delivery.get("type") if isinstance(delivery, dict) else None:
        auto.append("change.delivery_type (basic_design.delivery_model.type から自動抽出)")
    else:
        human.append("change.delivery_type (空、業務専門家確認)")

    human.extend([
        "change.transition_plan (現行 → 目標の遷移計画、業務専門家必須)",
        "change.training_plan (教育・周知計画、業務専門家必須)",
    ])

    seed = {
        "artifact": "change_strategy",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "change": {
            "delivery_type": delivery.get("type") if isinstance(delivery, dict) else "<TODO>",
            "rationale": delivery.get("rationale") if isinstance(delivery, dict) else "<TODO>",
            "transition_plan": "<TODO: 業務専門家確認>",
            "training_plan": "<TODO: 業務専門家確認>",
        },
    }
    return seed, human


def _seed_goal_tree(bd: dict) -> tuple[dict, list[str]]:
    """solution 軸 → goal_tree.yaml seed."""
    auto, human = [], []
    in_scope = _safe_get(bd, "basic_design", "scope", "in", default=[])
    out_scope = _safe_get(bd, "basic_design", "scope", "out", default=[])

    if in_scope:
        auto.append("goal.in_scope (basic_design.scope.in から自動抽出)")
    else:
        human.append("goal.in_scope (scope.in が空、業務専門家確認)")
    if out_scope:
        auto.append("goal.out_scope (basic_design.scope.out から自動抽出)")
    else:
        human.append("goal.out_scope (scope.out が空、業務専門家確認)")

    human.append("goal.tree_hierarchy (目標の階層構造、業務専門家必須)")

    seed = {
        "artifact": "goal_tree",
        "labels": {"auto_extracted": auto, "human_review_needed": human},
        "goal": {
            "in_scope": in_scope if isinstance(in_scope, list) else [],
            "out_scope": out_scope if isinstance(out_scope, list) else [],
            "tree_hierarchy": "<TODO: 業務専門家確認 (root → sub-goal → tasks の階層)>",
        },
    }
    return seed, human


def _build_drafts(bd: dict) -> tuple[dict[str, str], list[str]]:
    """basic_design SSoT YAML から 7 つの seed を生成、yaml シリアライズ + warnings 集約."""
    drafts: dict[str, str] = {}
    warnings: list[str] = []

    seed_funcs = [
        ("business_need.yaml", _seed_business_need),
        ("value_canvas.yaml", _seed_value_canvas),
        ("stakeholder_map.yaml", _seed_stakeholder_map),
        ("context_map.yaml", _seed_context_map),
        ("risk_register.yaml", _seed_risk_register),
        ("change_strategy.yaml", _seed_change_strategy),
        ("goal_tree.yaml", _seed_goal_tree),
    ]

    for filename, fn in seed_funcs:
        seed, axis_warnings = fn(bd)
        drafts[filename] = yaml.safe_dump(seed, allow_unicode=True, sort_keys=False, default_flow_style=False)
        for w in axis_warnings:
            warnings.append(f"{filename}: {w}")

    return drafts, warnings


def _format_dry_run_markdown(drafts: dict[str, str], feature_id: str, profile: str) -> str:
    """dry-run 出力用 Markdown を組み立てる."""
    parts = [
        f"# upstream_migration_helper dry-run\n",
        f"- feature_id: `{feature_id}`",
        f"- detected_profile: `{profile}`",
        f"- target_dir: `specs/<feature>/upstream/{PHASE_0_DIR}/`",
        "- mode: **dry-run** (no files written; pass `--apply` to write)",
        "",
        "## Generated drafts (7 BACCM axes seeds)",
        "",
    ]
    for filename, body in drafts.items():
        parts.append(f"### {filename}")
        parts.append("")
        parts.append("```yaml")
        parts.append(body.rstrip())
        parts.append("```")
        parts.append("")
    return "\n".join(parts)


def _apply_writes(feature_dir: Path, drafts: dict[str, str]) -> tuple[list[str], list[str]]:
    """--apply: drafts を実ファイル書込 (既存があれば skip + warn)."""
    target_dir = feature_dir / "upstream" / PHASE_0_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    written, skipped = [], []
    for filename, body in drafts.items():
        target = target_dir / filename
        if target.exists():
            skipped.append(str(target))
            continue
        target.write_text(body, encoding="utf-8")
        written.append(str(target))
    return written, skipped


def migrate_v5x_to_v6(feature_dir: Path, apply: bool = False, profile: str | None = None) -> dict:
    """v5.x basic_design.md から Phase 0 yaml seed を逆生成する公開 API.

    Args:
        feature_dir: specs/<feature>/ ディレクトリパス (Path)
        apply: True で実書込、False (デフォルト) は dry-run
        profile: 推奨 profile 上書き (None なら basic_design.md から自動検出)

    Returns:
        dict: { "feature_id", "detected_profile", "drafts" (filename→yaml str),
                "warnings", "post_apply_actions", "written" / "skipped" (apply 時のみ) }

    Raises:
        FileNotFoundError: feature_dir または basic_design.md 不在 (exit 1)
        yaml.YAMLError: basic_design.md パース失敗 (exit 2)
        ValueError: その他構造エラー (exit 2)
    """
    if not feature_dir.is_dir():
        raise FileNotFoundError(
            f"feature_dir not found: {feature_dir}. "
            "対応: 既存 v5.x プロジェクトの specs/<feature>/ パスを確認、または stride init を実行する。"
        )

    bd_path = feature_dir / "basic_design.md"
    if not bd_path.is_file():
        raise FileNotFoundError(
            f"basic_design.md not found: {bd_path}. "
            "対応: 既存 v5.x プロジェクトに basic_design.md が存在するか確認、または stride init を実行する。"
        )

    # frontmatter (top-level: feature_id, owners, links) と canonical YAML (basic_design: 以下)
    # を別々に抽出する。Phase D bugfix v7 後の正規 API。
    fm = extract_frontmatter_yaml(bd_path) or {}
    canonical = extract_canonical_yaml(bd_path, section="basic_design", strict=True)
    if not isinstance(canonical, dict):
        raise ValueError(
            f"basic_design.md canonical YAML block が dict ではありません: {type(canonical).__name__}. "
            "対応: basic_design.md の `# 0. Canonical Basic Design (YAML)` ブロックを確認する。"
        )

    # frontmatter と canonical をマージ (canonical 側が優先、frontmatter は feature_id/owners 補完用)
    bd: dict = {**fm, **canonical}

    detected_profile = profile or _detect_profile(bd)
    feature_id = _detect_feature_id(bd, feature_dir)
    drafts, warnings = _build_drafts(bd)

    result: dict[str, Any] = {
        "feature_id": feature_id,
        "detected_profile": detected_profile,
        "drafts": drafts,
        "warnings": warnings,
        "post_apply_actions": [
            f"Run: sdd-templates/bin/stride upstream validate {feature_dir.name}",
            f"Run: sdd-templates/bin/stride lint --upstream {feature_dir}/",
            "Human review: 各 yaml の labels.human_review_needed リストを業務専門家が確認・refinement",
        ],
    }

    if apply:
        written, skipped = _apply_writes(feature_dir, drafts)
        result["written"] = written
        result["skipped"] = skipped
        if skipped:
            for s in skipped:
                warnings.append(f"already exists, skipped: {s}")

    return result


def main():
    parser = argparse.ArgumentParser(
        prog="upstream_migration_helper",
        description="v5.x basic_design.md → v6.0 Phase 0 yaml seed 逆生成 (FEAT-VALD01)",
    )
    parser.add_argument(
        "feature_dir",
        type=Path,
        help="specs/<feature>/ ディレクトリパス (positional)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="upstream/phase_0_discovery/ に実書込 (なしは dry-run、stdout に Markdown 出力)",
    )
    parser.add_argument(
        "--profile",
        choices=["enterprise-erp", "saas-integration", "prototype"],
        default=None,
        help="推奨 profile (None なら basic_design.md から自動検出)",
    )
    args = parser.parse_args()

    try:
        result = migrate_v5x_to_v6(
            args.feature_dir,
            apply=args.apply,
            profile=args.profile,
        )
    except FileNotFoundError as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        return 1
    except yaml.YAMLError as e:
        sys.stderr.write(f"[ERROR] YAML parse failed: {e}\n")
        return 2
    except ValueError as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        return 2

    if args.apply:
        print(f"# upstream_migration_helper --apply\n")
        print(f"- feature_id: `{result['feature_id']}`")
        print(f"- detected_profile: `{result['detected_profile']}`")
        print(f"- written: {len(result['written'])} files")
        for w in result["written"]:
            print(f"  - {w}")
        if result["skipped"]:
            print(f"- skipped (already exists): {len(result['skipped'])} files")
            for s in result["skipped"]:
                print(f"  - {s}")
        print("\n## post_apply_actions\n")
        for a in result["post_apply_actions"]:
            print(f"- {a}")
    else:
        print(_format_dry_run_markdown(result["drafts"], result["feature_id"], result["detected_profile"]))
        print("\n## post_apply_actions (dry-run hint)\n")
        for a in result["post_apply_actions"]:
            print(f"- {a}")

    if result["warnings"]:
        sys.stderr.write("\n## Warnings\n")
        for w in result["warnings"]:
            sys.stderr.write(f"- {w}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
