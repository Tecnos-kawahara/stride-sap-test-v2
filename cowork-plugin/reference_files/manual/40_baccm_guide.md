# 40. BACCM 完全性ゲート — Discovery Phase の機械検証

> 本章は VALUE Upstream Extension の **Phase 0 (Discovery)** で導入される **BACCM (Business Analysis Core Concept Model) 6 軸完全性ゲート** の運用ガイドである。
> 概念は BABOK v3 §2.1 を参照する (fair-use, names and section refs only)。詳細な定義・解釈は原典で確認すること。

## 40.1 BACCM とは何か (要約)

BABOK v3 §2.1 で定義される業務分析の中核概念モデル。次の 6 つの軸で構成される。

| 軸 | 概念ラベル (英) | 概念ラベル (和) | STRIDE での位置付け |
|----|----------------|----------------|---------------------|
| **Change** | Change | 変化 | 現状 → 将来状態への意図的変換 |
| **Need** | Need | ニーズ | 解決すべき問題 / 活用すべき機会 |
| **Solution** | Solution | ソリューション | ニーズを満たす具体的な方法 |
| **Stakeholder** | Stakeholder | ステークホルダー | 変化に関係する個人・集団 |
| **Value** | Value | 価値 | 提供される正味の便益 |
| **Context** | Context | 文脈 | 変化を取り巻く内外の環境 |

これら 6 軸は **概念上独立** であり、いずれか 1 軸でも欠落すると業務分析の整合性が破綻する。STRIDE は **Article XV (proposed)** によりこの完全性を Phase 1 Design 着手前のゲートとして機械検証可能にする。

## 40.2 STRIDE での具体化 — 6 軸 → source_artifact

`shared/policies/baccm_completeness.yaml` で各軸を支える Phase 0 成果物を宣言する。要約は次のとおり。

| 軸 | 主たる source_artifact | 必須キー / 件数 |
|----|----------------------|----------------|
| Change | `value_canvas.yaml` + `change_strategy.yaml` | from_state / to_state / transition_states |
| Need | `business_need.yaml` | problem_statement / opportunity_statement |
| Solution | `change_strategy.yaml` + `goal_tree.yaml` | solution_scope / root_goal |
| Stakeholder | `stakeholder_map.yaml` | stakeholders 配列に最低 3 件 |
| Value | `value_canvas.yaml` | potential_value / anti_value |
| Context | `context_map.yaml` | internal_context / external_context |

各 source_artifact が Phase 0 で **すべて作成され、必須キーが空でない** ことを以て BACCM 完全性 100% と判定する (`completeness_scoring.algorithm: "all_axes_pass_required"`、`partial_credit_allowed: false`)。

## 40.3 ゲート判定の運用フロー

### 40.3.1 Phase 0 着手時 (案件開始)

1. `stride upstream init <feature>` (Phase B 以降) で 7 種の Phase 0 テンプレートを scaffold
2. ステークホルダーへの初期ヒアリング・社内レビューを通じて各 YAML を埋める
3. 3 反復パターン (`shared/policies/upstream_iteration_policy.yaml`) に従い:
   - **Iteration 1 (bootstrap):** Brainstorming / Mind Mapping / Stakeholder List で広く出す
   - **Iteration 2 (structure):** Functional Decomposition / Process Modelling / Scope Modelling で組み立てる
   - **Iteration 3 (refinement):** Business Rules Analysis / Decision Modelling / State Modelling で詳細化する
4. Iteration 3 完了時点で BACCM 6 軸完全性チェックを実行

### 40.3.2 BACCM ゲート (Gate 0)

- 6 軸すべてが PASS (各 source_artifact が存在し必須キーが空でない) なら Gate 0 通過
- 1 軸でも FAIL なら **Phase 1 Design 着手不可**。該当 source_artifact を補強して再検証
- 検証は `stride upstream validate <feature>` (Phase B) で機械化される予定

### 40.3.3 Phase 0 → Phase 0.3 / 0.5 への接続

BACCM 完全性が満たされた後、次の上流フェーズへ遷移する。

- `business_need` / `value_canvas` で WHY が確定 → `elicitation_plan` (Phase 0.3) で深掘り対象を決められる
- `stakeholder_map` で WHO が確定 → `actor_system` (Phase 0.5) で内部 / 外部システムへ展開できる
- `context_map` で WHERE が確定 → `business_usecase` (Phase 0.5) で業務シーンを切り出せる

## 40.4 Profile 別の適用度

`shared/policies/upstream_policy.yaml` で Profile 別の Discovery 適用度を宣言している。

| Profile | Discovery 適用度 | BACCM 6 軸の必須度 |
|---------|------------------|-------------------|
| `enterprise-erp` | required | 6 軸すべて必須 (Gate 0 100% PASS が前提) |
| `saas-integration` | required | 6 軸すべて必須 (但し source_artifact の depth は ERP 案件より軽量で可) |
| `prototype` | lite | Stakeholder + Value Canvas のみ最低限実施。残り 4 軸はベストエフォート |

`prototype` で軸を緩めるかどうかは現場判断 (value-driven discovery method 思想で「価値起点を絶対崩さない」線は守る)。

## 40.5 アンチパターン

### 40.5.1 完全性ゲートの形骸化

- ❌ `business_need.problem_statement` を「現状の業務効率を改善する」のような空虚な文で埋めて Gate 0 通過させる
- ✅ 「2025-Q3 受注処理の月平均リードタイムが 72h で、目標 24h を超過している」のように **計測可能な現状** を記述

### 40.5.2 Stakeholder 軸の不足

- ❌ stakeholders を 3 件並べたが、すべて IT 部門のメンバー
- ✅ 業務オーナー / 業務担当 / IT / 監査 / 経営層から最低 3 ロール選出して **多様性** を担保

### 40.5.3 anti_value の見落とし

- ❌ value_canvas.potential_value のみ書いて anti_value を空にする
- ✅ 必ず anti_value も明示。「自動化により職員の OJT 機会が減る」のような副作用を上流で論点化

## 40.6 BABOK 50 技法カタログとの接続

`shared/policies/technique_library.yaml` に BABOK §10 の 50 技法が登録されている。各技法には `typical_phase` (`phase_0_discovery` / `phase_0_3_elicit` / `phase_0_5_context_modelling` / `stride_core`) と `typical_artifacts` が設定されており、Discovery で使うべき技法は次のように選び分ける。

| 状況 | 推奨技法 |
|------|---------|
| 何もないところから出発 | `brainstorming` / `mind_mapping` / `stakeholder_list_map_or_personas` |
| 業務全体像を可視化 | `business_capability_analysis` / `business_model_canvas` / `swot_analysis` |
| 価値定量化 | `business_cases` / `financial_analysis` / `metrics_and_kpis` |
| 戦略実行測定 | `balanced_scorecard` / `benchmarking_and_market_analysis` |
| リスク把握 | `risk_analysis_and_management` / `decision_analysis` |
| ゴール体系化 | `goal_tree` 関連の `prioritization` |

Phase B では `stride technique recommend <baccm_axis>` のような半自動推薦も検討する。

## 40.7 Phase B 以降の予定

- `stride upstream validate <feature>` で 6 軸完全性 + 必須キー充足を JSON で出力
- `phase_gate.py` に Discovery Gate (Gate 0) を追加し、Phase 1 着手前に自動判定
- Multi-Model Evaluator (`stride evaluate --discovery`) で意味的完全性 (例: stakeholder 軸の偏り、anti_value の妥当性) を LLM で評価
- Constitution 本体への Article XV 正式マージ (`meta.version` bump + amendment_history)

## 40.8 関連章 / 参考

- 39 章 — VALUE Upstream Extension 概要
- 41 章 — Layered Requirements Architecture
- 42 章 — Phase 0 → 0.3 → 0.5 → Phase 1 ウォークスルー
- `memory/constitution_amendments/XV_baccm_completeness.md` — Article XV (proposed) 全文
- `shared/policies/baccm_completeness.yaml` — 機械可読 policy 定義

## 40.9 Attribution

- **BABOK v3 (IIBA)** — BACCM definition source (§2.1) — fair-use, axis names and concept refs only
- 本章の説明文はすべて Claude (Opus 4.7) による独自要約。原典テキストの逐語的引用は含まない。
