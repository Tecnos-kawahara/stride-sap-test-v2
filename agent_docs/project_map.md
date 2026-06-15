# Project Map - SDD Template Pack (Tecnos v4.4.0)
# Keep factual and pointer-based.

## 1) Template pack
```
sdd-templates/
├── templates/                 # Canonical templates
├── memory/                    # Constitution, org constraints, registry
├── policies/                  # BPMN generator rules
├── tools/                     # stride-lint
├── examples/                  # BPMN skeletons
└── specs/                     # Template examples (if present)
```

## 2) Working specs
Each feature lives under `specs/<feature>/`:
- `basic_design.md`
- `process.bpmn`
- `spec.md`
- `plan.md`
- `tasks.md`
- `contracts/`
- `tests/`
- `implementation-details/`
  - `evidence_pack.md`
  - `e2e-triage.md` (when E2E tests exist)

## 3) Governance references
- `memory/constitution.md`
- `memory/tecnos_org_constraints.md`
- `memory/artifact_registry.md`

## 4) Linting tool
- `sdd-templates/bin/stride lint`

## 5) VALUE Upstream Extension (Phase A scaffold)
VALUE Upstream Extension は Phase 1 Design 着手前の Phase 0 (Discovery, BABOK KA6) / Phase 0.3 (Elicit, BABOK KA4) / Phase 0.5 (Context Modelling, BABOK KA7 + 4-layer Requirements Architecture) の上流フェーズを補強する基盤 (Phase A) を提供する。
- Policies: `shared/policies/upstream_policy.yaml` / `baccm_completeness.yaml` / `technique_library.yaml` (BABOK 50 techniques) / `upstream_iteration_policy.yaml`
- Templates: `sdd-templates/templates/upstream/` (15 artifact YAML + README)
- Constitution: `memory/constitution_amendments/XV-XVII.md` (proposed のみ、本体不変)
- Manual: `manual/39-42` (4 章。詳細: 39 章 概要)。

## 6) VALUE Upstream Extension (Phase B tools, v5.5)
Phase B では Phase A の schema 基盤を実コマンド化する。
- Python tools: `sdd-templates/tools/{upstream_scaffolder,baccm_completeness_checker,upstream_iteration_evaluator,technique_library_query,upstream_lint}.py`
- CLI: `stride upstream init/validate` (新サブコマンド) + `stride lint --upstream` + `stride evaluate --phase discovery`
- stride_lint 4 新エラーコード: BACCM_INCOMPLETE / Layered Requirements Modeling_BROKEN_LINK / UPSTREAM_TEMPLATE_DRIFT / BABOK_TECHNIQUE_UNKNOWN
- Static schemas: `sdd-templates/static/upstream_schemas/` (15 artifact JSON Schema, Draft 2020-12)
- Manual: `manual/43_upstream_cli_guide.md` / `44_upstream_iteration_workflow.md`

## 7) VALUE Upstream Extension 完成 (Phase C, v6.0)
Phase C で VALUE Upstream Extension を完成形 (v6.0.0-tecnos-stride-value) へ昇華した (FEAT-VALC01, 2026-04-29)。
- Python tools: `sdd-templates/tools/{upstream_bridge,solution_evaluator}.py` 新規 2 件
- CLI: `stride upstream-bridge` (Phase 0/0.3/0.5 → Phase 1 自動 populate、Gate 1/2 immutability check 付き) + `stride retro --solution-eval` (BABOK KA8 稼働後評価ループ、KPI/Adoption/Issues 集計レポート)
- Constitution: Article XV (BACCM Completeness Gate) / XVI (Layered Requirement Architecture) / XVII (Solution Evaluation Loop) を `articles[]` 配列にマージ + amendments status proposed → ratified に遷移 + トップレベル version 5.4.0 → 6.0.0-tecnos-stride-value MAJOR bump + amendment_history +3 entries
- Tests: `tests/test_{upstream_bridge,solution_evaluator,constitution_xv_xvi_xvii_ratified,stride_cli_phase_c}.py` 新規 4 件 + `test_constitution_amendments.py` を Phase C 状態用に改修 (Hitoshi さん明示承認 §Rule 1-A 例外)
- Manual: `manual/45_upstream_bridge_guide.md` / `46_solution_evaluation_guide.md` / `47_v60_release_notes.md` 新規 3 章

## 8) VALUE Upstream Extension 普及準備 (Phase D, v6.0.x)
Phase D で VALUE Upstream Extension を「使われる状態」に引き上げる普及準備パッケージを提供する (FEAT-VALD01, 2026-04-30)。
- Profile 別 playbook: `manual/48_enterprise_erp_value_playbook.md` / `49_saas_integration_value_playbook.md` / `50_prototype_value_playbook.md` (各 3000-5000 字、6 章構成)
- Migration Guide: `manual/migration/v54_to_v60.md` + `sdd-templates/tools/upstream_migration_helper.py` (v5.x basic_design.md → Phase 0 yaml seed 逆生成 CLI、BACCM 6 軸ごとに「自動抽出可能」「要人間確認」ラベル付与)
- Tests: `tests/test_upstream_migration_helper.py` (+9 件、baseline 769 → 778 passed、回帰 0)
- Lessons: `memory/lessons_learned/upstream_dogfooding/external_scm_pilot_01.md` (primary dogfooding sanitized 学び、§Rule 15-B 匿名化済)
- VERSION: 6.0.0-tecnos-stride-value 維持 (普及準備のため bump なし)

## 9) VALUE Cowork Plugin (Phase E, v6.0.x)
Phase E で **上位コンサル (非技術者)** が Cowork で Phase 0 → Phase 1 を直接執筆できる Cowork Plugin を実装 (FEAT-VALE01, 2026-04-30、Plugin VERSION 0.1.0-poc)。
- Plugin manifest: `cowork-plugin/.claude-plugin/plugin.json` + `README.md` + `CONNECTORS.md` + `.mcp.json` (Anthropic 公式 knowledge-work-plugins 仕様準拠)
- Skills 7: `cowork-plugin/skills/{baccm-discovery,babok-elicitation,layered-context-modelling,upstream-bridge,basic-design-authoring,bpmn-authoring,epic-decomposition}/SKILL.md`
- Slash Commands 9: `cowork-plugin/commands/stride-{init,discovery,elicit,context-model,validate,bridge,design,epic-init,handoff}.md`
- reference_files 49 ファイル同梱 + 同期スクリプト `scripts/sync_cowork_plugin_reference.sh` (49 件厳守チェック内蔵)
- MCP Connectors: filesystem + github (PAT scope 必要最小限: Contents R/W + PR R/W + Metadata R)
- Tests: `tests/test_cowork_plugin_structure.py` (+3) + `tests/test_cowork_plugin_skills_commands.py` (+5) = +8 件、baseline 778 → 788 passed、回帰 0
- Manual: `manual/51_cowork_plugin_install_guide.md` (11 章、3000-5000 字)
- Tecnos-STRIDE 本体 VERSION 6.0.0 維持 (Plugin は独立 SemVer 0.1.0-poc から開始)

## 10) VALUE Cowork Plugin v0.2.0-stable (Phase F, v6.0.x)
Phase F で fc-sd 実機運用 16 件改善要望を 17 WI で反映、Plugin v0.1.0-poc → **v0.2.0-stable** に運用品質引き上げ (FEAT-VALF01, 2026-05-01)。
- CI 統合: `.github/workflows/cowork-plugin-validate.yml` (PR path filter で Plugin 関連変更のみ trigger、ubuntu-latest + Python 3.11 + claude CLI で `claude plugin validate` + pytest)
- Cowork セッション内 機械検証 + サニタイズ自動 grep: `cowork-plugin/commands/stride-handoff.md` 改修 (WI-001 + WI-004)
- state.yaml Phase 2-4 + Final schema 拡張 + tests +3 (`tests/test_cowork_plugin_state_yaml_phases.py`、baseline 789 → 792 passed)
- 新規 commands 2: `stride-export-html` (HTML 出力、WI-011) + `stride-tasking` (Phase 3 連結、WI-016) → commands 9 → **11**
- 同梱 Python スクリプト: `cowork-plugin/scripts/{validate_state_yaml.py, check_handoff_files.py, README.md}` (WI-014、reference_files=49 不変)
- 推奨 settings.json template: `cowork-plugin/.claude-template/settings.json` (WI-015、Phase Gate Hook + permission 推奨値)
- HTML 出力 helper: `scripts/build_basic_design_html.py` (DR-103、Tecnos-STRIDE 本体 scripts/ 配下、Plugin 同梱せず)
- 7 Skill description 改修 (Tecnos-STRIDE 固有語必須前置詞化、WI-003、誤起動回避)
- Manual: `manual/52_phase_f_lessons_learned.md` (11 章、§9 に fc-sd 相当の Plugin 導入手順、WI-008 + WI-017)
- 3 profile dogfood scaffold: `memory/lessons_learned/upstream_dogfooding/{saas_integration,prototype}_pilot_01.md` (WI-006/007、実 dogfooding は Phase F PR merge 後 follow-up)
- GitHub MCP 実機検証 evidence scaffold: `docs/evidence/phase_f/wi_012_mcp_validation.md` (WI-012、実検証は Phase F PR merge 後 follow-up)
- Tecnos-STRIDE 本体 VERSION 6.0.0 維持、Plugin 独立 SemVer 0.2.0-stable
