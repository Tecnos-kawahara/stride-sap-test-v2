# CLAUDE_WORKFLOW_SAP.md
# SAP Extension Pack v2.0.0 — Phase Workflow Overview
# このファイルは Phase 概要のみ。各 Phase の詳細手順は agent_docs/ を参照すること。

## ⛔ 前提: 標準フローの完了ステップ

**SAP 拡張ワークフローは標準 STRIDE フローの「途中から」を引き継ぐ。以下が完了していなければ Phase 1 に進んではならない。**

```
1. sdd_bootstrap.md を読み込み済み（標準の実行モデル・Phase Gate ルールを理解）
2. stride init <feature> --detect を実行し、specs/<feature>/ が scaffold 済み
   → basic_design_template.md, APPROVAL.md, state_template.yaml 等が配置される
3. .stride-extensions.yaml で SAP 拡張パックが検出されている
4. CLAUDE_SAP.md（本拡張のルール S1-S7）を読み込み済み
5. 本ファイル（CLAUDE_WORKFLOW_SAP.md）を読み込み済み ← 今ここ
```

**`stride init` を実行せずに yaml → basic_design 転記を開始してはならない。**
scaffold が存在しない状態で成果物を作成すると、ディレクトリ構造・テンプレート・APPROVAL.md が欠落し、以降の stride lint や Phase Gate が正常に動作しない。

## Phase 別ワークフロー

| Phase | Detail Doc | 概要 |
|-------|-----------|------|
| Phase 1: Design | `agent_docs/phase1_design.md` | yaml→basic_design 転記 + AI 構成 + 検証 |
| Phase 1.5: SAP Context | `agent_docs/phase15_sap_context.md` | SAP 実機接続による情報補完（任意） |
| Phase 2: Specify | `agent_docs/phase2_specify.md` | spec/plan/contracts 生成 + AC 品質保証 |
| Phase 3: Tasking | `agent_docs/phase3_tasking.md` | SAP 開発順序でタスク構成 |
| Phase 4: Execute | `agent_docs/phase4_execute.md` | WI 16-step + SAP 固有実装サイクル |
| Final | `agent_docs/phase_final.md` | 受入テスト + エビデンス + Ops Pack |

## Phase 1: Design

> ⛔ MANDATORY: `agent_docs/phase1_design.md` を読んでから作業を開始すること。

| 成果物 | 品質基準 |
|--------|---------|
| basic_design.md | yaml 全要素が YAML canonical に転記済み。sap_context 構成済み |
| process.bpmn | v6.0.0 §4-BPMN 準拠 |

**検証**: `basic_design_completeness_validator` + `catalogs_consistency_validator` + `stride lint`

## Phase 1.5: SAP Context Acquisition（任意）

> ⛔ MANDATORY: 実行する場合は `agent_docs/phase15_sap_context.md` を読むこと。

| 成果物 | 品質基準 |
|--------|---------|
| sap_context.md | SAP 実機から取得した補完情報を記録済み |

**検証**: `sap_message_t100_validator` + `sap_ddic_gate_validator`

## Phase 2: Specify

> ⛔ MANDATORY: `agent_docs/phase2_specify.md` を読んでから作業を開始すること。

### Phase 2 開始前チェック

0. **Phase 1.5（SAP Context Acquisition）の確認**:
   - `specs/<feature>/sap_context.md` が存在するか確認
   - 存在しない場合、Phase 1.5 のステップ（A1〜C2）を先に実行
   - `sap_context.md` が既に存在し、内容が十分であればスキップ

| 成果物 | 品質基準 |
|--------|---------|
| spec.md | 全カタログ項目が独立 AC 化。catalog_refs 設定済み |
| plan.md | coverage_policy 定義。contracts.file セクション含む |
| contracts/* | basic_design.object_definitions から生成 |
| tests/scenarios.yaml | Type A（traceability_ref）+ Type B（test_matrix_ref）展開 |

**検証**: `stride lint` + `catalogs_consistency_validator` + `sap_ac_granularity_validator` + `glossary_ref_validator` + `plan_quality_validator`

## Phase 3: Tasking

> ⛔ MANDATORY: `agent_docs/phase3_tasking.md` を読んでから作業を開始すること。

| 成果物 | 品質基準 |
|--------|---------|
| tasks.md | SAP 開発順序準拠。bdd_mode=required。risk_flags per task |

**検証**: `stride lint`（tasks_gate_check）

## Phase 4: Execute

> ⛔ MANDATORY: `agent_docs/phase4_execute.md` を読んでから作業を開始すること。

v6.0.0 WI 16-step フローに SAP 固有ステップを統合して実行する。

**SAP 固有ツール**: create_object.js / pull.js / activate.js / run_tests.js / gui_test.js / data_preview.js / evidence_capture.js
**品質**: sap_quality_score >= 85pt（`quality_score_config.yaml`）

## Final

> ⛔ MANDATORY: `agent_docs/phase_final.md` を読んでから作業を開始すること。

| 成果物 | 品質基準 |
|--------|---------|
| evidence_pack_sap.md | v6.0.0 拡充版 + SAP 固有セクション |
| test_green_confirmation | unit_test + gui_test = all_passed: true |

**検証**: `erp_addon_exec_tracking` + `stride pr-check` 7/7
