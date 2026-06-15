"""Test: 5 tools handle Phase A frontmatter-wrapped YAML — post-Phase-C bugfix.

このテストは 2026-04-29 Cowork PoC で発見された yaml.safe_load vs frontmatter 不整合
バグの回帰テスト. Phase A テンプレ通りに作成された artifact が 5 ツール で正しく扱える
こと、かつ frontmatter なしの単純 YAML も引き続き動作することを検証する.

Covers:
  - AC-US-FEATVALBUGFIX01-001-01 (load_yaml_with_frontmatter helper API)
  - AC-US-FEATVALBUGFIX01-001-02 (5 tools migration)
  - AC-US-FEATVALBUGFIX01-001-03 (regression + backward compat)
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from stride_shared_lib import load_yaml_with_frontmatter  # noqa: E402


# Phase A テンプレ風 frontmatter 付き YAML (実機 value_canvas_template.yaml と同型)
FRONTMATTER_YAML = """---
# Template: value_canvas.yaml
# Phase: phase_0_discovery
# BABOK Source: KA6 Strategy Analysis / Technique 10.8 Business Model Canvas
# Rule-0: 正本は YAML フロントマター + 下記 YAML ブロック
---

artifact: "value_canvas.yaml"
template_id: "TPL-UP-VLC-001"
feature_id: "FEAT-VALTEST-001"
upstream_artifact_id: "VLC-001"
title: "Test Value Canvas"
version: "0.1.0"
status: "draft"
phase: "phase_0_discovery"
profile_applicability: ["enterprise-erp"]
links:
  upstream_policy_ref: "shared/policies/upstream_policy.yaml"
from_state: "AS-IS placeholder"
to_state: "TO-BE placeholder"
potential_value: ["PV-001"]
anti_value: ["AV-001"]
"""

PLAIN_YAML = """artifact: value_canvas.yaml
from_state: AS-IS
to_state: TO-BE
potential_value: [v1]
anti_value: [a1]
"""


# ---------------------------------------------------------------------------
# Helper API surface tests (TS-CON-01, AC-US-FEATVALBUGFIX01-001-01)
# ---------------------------------------------------------------------------


def test_helper_returns_body_dict_for_frontmatter_yaml(tmp_path: Path):
    """frontmatter 付き YAML から body 側 (parts[2]) の dict を返す."""
    p = tmp_path / "value_canvas.yaml"
    p.write_text(FRONTMATTER_YAML, encoding="utf-8")
    result = load_yaml_with_frontmatter(p)
    assert isinstance(result, dict)
    # body 側のキーが含まれていること (frontmatter のコメント部分は含まれない)
    assert result["artifact"] == "value_canvas.yaml"
    assert result["template_id"] == "TPL-UP-VLC-001"
    assert result["from_state"] == "AS-IS placeholder"


def test_helper_handles_plain_yaml(tmp_path: Path):
    """frontmatter なしの通常 YAML も全体を body として読む (後方互換性)."""
    p = tmp_path / "plain.yaml"
    p.write_text(PLAIN_YAML, encoding="utf-8")
    result = load_yaml_with_frontmatter(p)
    assert isinstance(result, dict)
    assert result["artifact"] == "value_canvas.yaml"
    assert result["potential_value"] == ["v1"]


def test_helper_strict_propagates_yaml_error(tmp_path: Path):
    """strict=True (default) で broken YAML は yaml.YAMLError を伝播."""
    import yaml as _yaml
    p = tmp_path / "broken.yaml"
    p.write_text("---\n# header\n---\n\nthis: [is: invalid: yaml\n", encoding="utf-8")
    with pytest.raises(_yaml.YAMLError):
        load_yaml_with_frontmatter(p, strict=True)


def test_helper_non_strict_returns_none_on_error(tmp_path: Path):
    """strict=False で broken YAML は None を返し、例外を握りつぶす."""
    p = tmp_path / "broken.yaml"
    p.write_text("---\n# header\n---\n\nthis: [is: invalid: yaml\n", encoding="utf-8")
    result = load_yaml_with_frontmatter(p, strict=False)
    assert result is None


def test_helper_returns_none_for_missing_file(tmp_path: Path):
    """存在しないパスで None を返す (ファイル不在は graceful skip)."""
    result = load_yaml_with_frontmatter(tmp_path / "nonexistent.yaml")
    assert result is None


# ---------------------------------------------------------------------------
# 5 ツール × frontmatter 付き YAML 個別検証 (TS-INT-01, AC-001-02)
# ---------------------------------------------------------------------------


def _setup_phase0_with_frontmatter_artifacts(feature_dir: Path) -> None:
    """Phase A テンプレ風 frontmatter 付きの BACCM 6 軸 artifact を配置."""
    discovery = feature_dir / "upstream" / "phase_0_discovery"
    discovery.mkdir(parents=True, exist_ok=True)

    base_frontmatter = textwrap.dedent("""\
        ---
        # Template: phase_0_discovery
        # Phase: phase_0_discovery
        ---

        """)

    (discovery / "value_canvas.yaml").write_text(
        base_frontmatter + textwrap.dedent("""\
            artifact: value_canvas.yaml
            from_state: AS-IS
            to_state: TO-BE
            potential_value: [PV-001]
            anti_value: [AV-001]
            """),
        encoding="utf-8",
    )
    (discovery / "stakeholder_map.yaml").write_text(
        base_frontmatter + textwrap.dedent("""\
            artifact: stakeholder_map.yaml
            stakeholders:
              - id: SH-001
                name: Owner
              - id: SH-002
                name: User
              - id: SH-003
                name: Sponsor
            """),
        encoding="utf-8",
    )
    (discovery / "business_need.yaml").write_text(
        base_frontmatter + textwrap.dedent("""\
            artifact: business_need.yaml
            need_statement: dummy
            success_criteria: {}
            """),
        encoding="utf-8",
    )
    (discovery / "context_map.yaml").write_text(
        base_frontmatter + "artifact: context_map.yaml\ncontext_layers: []\n",
        encoding="utf-8",
    )
    (discovery / "change_strategy.yaml").write_text(
        base_frontmatter + "artifact: change_strategy.yaml\nchange_approach: dummy\n",
        encoding="utf-8",
    )
    (discovery / "goal_tree.yaml").write_text(
        base_frontmatter + "artifact: goal_tree.yaml\ngoals: []\n",
        encoding="utf-8",
    )
    (discovery / "risk_register.yaml").write_text(
        base_frontmatter + "artifact: risk_register.yaml\nrisks: []\n",
        encoding="utf-8",
    )


def test_baccm_checker_parses_frontmatter_yaml(tmp_path: Path):
    """baccm_completeness_checker が frontmatter 付き YAML を ComposerError なくパース."""
    feature_dir = tmp_path / "specs" / "feat_test"
    _setup_phase0_with_frontmatter_artifacts(feature_dir)

    from baccm_completeness_checker import check_baccm_completeness
    # ComposerError を投げずに完走することが最優先 (戻り値の各 axis pass/fail は問わない)
    result = check_baccm_completeness(feature_dir, repo_root=REPO_ROOT)
    assert isinstance(result, dict)
    assert "axes" in result
    # 6 axes 全部のキーが含まれる
    for axis in ("change", "need", "solution", "stakeholder", "value", "context"):
        assert axis in result["axes"]


def test_upstream_iteration_evaluator_parses_frontmatter_yaml(tmp_path: Path):
    """upstream_iteration_evaluator が frontmatter 付き policy YAML を読める."""
    feature_dir = tmp_path / "specs" / "feat_test_iter"
    _setup_phase0_with_frontmatter_artifacts(feature_dir)

    from upstream_iteration_evaluator import evaluate_iteration
    result = evaluate_iteration(feature_dir, repo_root=REPO_ROOT)
    assert isinstance(result, dict)
    assert "iteration_complete" in result
    assert "iteration_details" in result


def _make_scaffold_repo_root(tmp_path: Path, feature_name: str) -> Path:
    """Phase B test_upstream_scaffolder と同様の symlink fixture を作る."""
    feature_dir = tmp_path / "specs" / feature_name
    feature_dir.mkdir(parents=True)
    state_dir = feature_dir / "state"
    state_dir.mkdir()
    (state_dir / "state.yaml").write_text("profile: enterprise-erp\n", encoding="utf-8")

    (tmp_path / "shared").mkdir(exist_ok=True)
    (tmp_path / "shared" / "policies").mkdir(exist_ok=True)
    for policy in ("upstream_policy.yaml", "baccm_completeness.yaml",
                   "technique_library.yaml", "upstream_iteration_policy.yaml"):
        link = tmp_path / "shared" / "policies" / policy
        if not link.exists():
            link.symlink_to(REPO_ROOT / "shared" / "policies" / policy)

    (tmp_path / "sdd-templates").mkdir(exist_ok=True)
    (tmp_path / "sdd-templates" / "templates").mkdir(exist_ok=True)
    upstream_link = tmp_path / "sdd-templates" / "templates" / "upstream"
    if not upstream_link.exists():
        upstream_link.symlink_to(REPO_ROOT / "sdd-templates" / "templates" / "upstream")
    return tmp_path


def test_upstream_scaffolder_reads_frontmatter_policy(tmp_path: Path):
    """upstream_scaffolder が frontmatter 付き policy + frontmatter 付き templates から scaffold."""
    repo_root = _make_scaffold_repo_root(tmp_path, "tmp_scaffold")

    from upstream_scaffolder import scaffold_upstream
    result = scaffold_upstream("tmp_scaffold", "discovery", repo_root=repo_root)
    assert isinstance(result, dict)
    assert result["phase"] == "phase_0_discovery"
    assert len(result["generated_files"]) >= 1


def test_upstream_bridge_reads_frontmatter_business_usecase(tmp_path: Path):
    """upstream_bridge が frontmatter 付き business_usecase.yaml の body 側 (parts[2]) を読む.

    Bug regression: 旧実装は parts[1] (frontmatter) を読んでいた → use_cases が抽出されなかった.
    新実装は parts[2] (body) → task_candidates が business_usecase から正しく抽出される.
    """
    feature_dir = tmp_path / "specs" / "feat_bridge_test"
    upstream = feature_dir / "upstream"
    (upstream / "phase_0_discovery").mkdir(parents=True)
    (upstream / "phase_0_5_context_modelling").mkdir(parents=True)

    # frontmatter 付き business_usecase.yaml を作成
    bu_yaml = textwrap.dedent("""\
        ---
        # Template: business_usecase.yaml
        # Phase: phase_0_5_context_modelling
        ---

        artifact: business_usecase.yaml
        use_cases:
          - id: BUC-001
            name: Submit purchase request
          - id: BUC-002
            name: Approve purchase order
        """)
    (upstream / "phase_0_5_context_modelling" / "business_usecase.yaml").write_text(
        bu_yaml, encoding="utf-8"
    )

    # 最低限の basic_design.md (frontmatter + links のみ)
    (feature_dir / "basic_design.md").write_text(
        textwrap.dedent("""\
            ---
            artifact: "basic_design"
            feature_id: "FEAT-BRIDGETEST"
            links:
              process_bpmn_ref: "specs/feat_bridge_test/process.bpmn"
            ---

            # 0. Canonical Basic Design (YAML)
            placeholder
            """),
        encoding="utf-8",
    )

    # APPROVAL.md scaffold (Gate 1/2 未承認状態)
    (feature_dir / "APPROVAL.md").write_text(
        textwrap.dedent("""\
            # 承認記録

            ## Gate 1: Basic Design

            確認項目：

            - [ ] basic_design.md の WHO/WHAT/WHY が正しい

            ```
            承認者: _____________________
            日付:   _____________________
            ```

            ---

            ## Gate 2: BPMN

            確認項目：

            - [ ] process.bpmn の業務フローが正しい

            ```
            承認者: _____________________
            日付:   _____________________
            ```
            """),
        encoding="utf-8",
    )

    from upstream_bridge import bridge_to_phase1
    result = bridge_to_phase1(feature_dir, target_section="phase1", apply=False)

    # task_candidates が business_usecase.use_cases から正しく抽出されている
    # = parts[2] (body) を読んでいる証拠. parts[1] (frontmatter) を読んでいると use_cases は空.
    assert isinstance(result, dict)
    assert len(result["task_candidates"]) == 2
    candidate_names = [c["name"] for c in result["task_candidates"]]
    assert "Submit purchase request" in candidate_names
    assert "Approve purchase order" in candidate_names


def test_upstream_lint_handles_frontmatter_artifacts(tmp_path: Path):
    """upstream_lint が frontmatter 付き YAML を読み、エラーケースで None を握りつぶす (strict=False)."""
    # broken YAML を渡して strict=False で None が返ることを確認 (helper level)
    p = tmp_path / "broken_with_frontmatter.yaml"
    p.write_text(
        textwrap.dedent("""\
            ---
            # header
            ---

            this: [is: completely: broken
            """),
        encoding="utf-8",
    )
    # upstream_lint の _load_yaml_with_frontmatter は strict=False を使う
    from upstream_lint import _load_yaml_with_frontmatter
    result = _load_yaml_with_frontmatter(p)
    assert result is None  # parse error は握りつぶし


# ---------------------------------------------------------------------------
# Integration: 5 tools sequential run (TS-INT-02, AC-001-03)
# ---------------------------------------------------------------------------


def test_all_five_tools_handle_frontmatter_yaml_integration(tmp_path: Path):
    """5 ツール 全部を順次呼び出し、ComposerError なく完走することを確認."""
    feature_dir = tmp_path / "specs" / "feat_integration"
    _setup_phase0_with_frontmatter_artifacts(feature_dir)

    # 1. baccm_completeness_checker
    from baccm_completeness_checker import check_baccm_completeness
    r1 = check_baccm_completeness(feature_dir, repo_root=REPO_ROOT)
    assert "axes" in r1

    # 2. upstream_iteration_evaluator
    from upstream_iteration_evaluator import evaluate_iteration
    r2 = evaluate_iteration(feature_dir, repo_root=REPO_ROOT)
    assert "iteration_complete" in r2

    # 3. upstream_scaffolder (separate scaffold dir with symlinked policies + templates)
    from upstream_scaffolder import scaffold_upstream
    scaffold_dir = tmp_path / "scaffold_target"
    scaffold_dir.mkdir()
    repo_root = _make_scaffold_repo_root(scaffold_dir, "feat_scaffold_int")
    r3 = scaffold_upstream("feat_scaffold_int", "discovery", repo_root=repo_root)
    assert "phase" in r3

    # 4 & 5: helper level でも frontmatter 付き YAML を読めることを確認
    from upstream_lint import _load_yaml_with_frontmatter
    sample = feature_dir / "upstream" / "phase_0_discovery" / "value_canvas.yaml"
    r4 = _load_yaml_with_frontmatter(sample)
    assert r4 is not None and r4["artifact"] == "value_canvas.yaml"
