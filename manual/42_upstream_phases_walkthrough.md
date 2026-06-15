# 42. Phase 0 → 0.3 → 0.5 → Phase 1 ウォークスルー

> 本章は VALUE Upstream Extension の 3 フェーズを実例で追う運用ガイドである。
> 仮想案件「ERP 受注処理リードタイム短縮」を題材に、Phase 0 → 0.3 → 0.5 → Phase 1 の連続フローを示す。
> Phase A 時点ではテンプレートのみ提供。実行ツール (`stride upstream init / validate / iterate`) は Phase B 以降。

## 42.1 仮想案件設定

- **背景:** Tecnos の顧客 X 社で、SAP S/4HANA 上の受注処理のリードタイムが月平均 72h、目標 24h との乖離が経営課題
- **依頼者:** X 社 営業部長
- **対象システム:** SAP S/4HANA / Salesforce CRM / 自社受注ポータル
- **制約:** 監査要件 (J-SOX) / 既存 IDoc 連携の維持
- **タイムライン:** Discovery 着手から Phase 1 Design 完了まで 4 週間

## 42.2 Phase 0 — Discovery (Week 1)

### 42.2.1 Iteration 1 — bootstrap (網羅性優先)

- **使用技法 (`technique_library.yaml`):** `brainstorming` / `mind_mapping` / `stakeholder_list_map_or_personas`
- **会議体:** X 社の営業部長 / 営業担当 / 物流担当 / IT 担当 / 監査担当 を集めた半日ワークショップ
- **生成成果物 (1 巡目、粗い状態):**
  - `business_need.yaml` (BNE-001): problem_statement に「受注処理リードタイムが目標を 3 倍超過」と暫定記述
  - `stakeholder_map.yaml` (SHM-001): stakeholders に上記 5 ロールを SH-001〜005 として登録
  - `value_canvas.yaml` (VLC-001): from_state「平均 72h」 → to_state「平均 24h 以下」
  - `risk_register.yaml` (RRG-001): R-001「IDoc 互換性」、R-002「監査要件への影響」を粗く列挙

### 42.2.2 Iteration 2 — structure (依存関係付与)

- **使用技法:** `functional_decomposition` / `process_modelling` / `scope_modelling` / `business_capability_analysis`
- **生成成果物 (構造化):**
  - `context_map.yaml` (CTX-001): internal_context に「営業部 → 物流 → 経理の 3 部門連携」、external_context に「Salesforce SFA 連携」を整理
  - `goal_tree.yaml` (GLT-001): root_goal「受注 24h 以内 ERP 反映」、subgoals に「与信判定自動化」「IDoc 受信即時確認」「例外承認フロー高速化」
  - `change_strategy.yaml` (CHS-001): solution_scope「与信自動化 + 受信確認自動化」、transition_states に「現状 → ロジック標準化 → 自動化 → 評価」

### 42.2.3 Iteration 3 — refinement (詳細化)

- **使用技法:** `business_rules_analysis` / `decision_modelling` / `state_modelling`
- **詳細化:** value_metrics として「月平均リードタイム」「P95 リードタイム」「与信例外率」を確定。anti_value に「営業 OJT 機会の減少」を明示。
- **BACCM 6 軸完全性チェック:** Article XV (proposed) の criteria に従い検証 → すべて充足

### 42.2.4 Gate 0 (Discovery Gate)

- BACCM 6 軸完全性 100% (Phase B では `stride upstream validate <feature> --gate 0` で機械検証)
- Phase A 時点では人間レビューでチェックリスト確認
- ⛔ ステークホルダー (営業部長 + IT 部門長) の承認待ち → 承認後 Phase 0.3 へ

## 42.3 Phase 0.3 — Elicitation (Week 2)

### 42.3.1 elicitation_plan の確定

- **使用技法:** `interviews` / `workshops` / `document_analysis` / `observation`
- `elicitation_plan.yaml` (ELP-001):
  - techniques: ["interviews", "document_analysis", "observation"]
  - target_stakeholders: ["SH-001", "SH-003", "SH-004"] (営業部長 + 物流担当 + IT 担当)
  - schedule: 「Week 2 月-水: インタビュー、Week 2 木-金: 業務観察」
  - resources: 「会議室 + IDoc 受信ログ + 経理締めスケジュール」

### 42.3.2 elicitation_results の蓄積

- **findings:**
  - FND-001: 「IDoc 受信から確認応答まで現状平均 8h、最大 28h」(source: SH-004 インタビュー)
  - FND-002: 「与信例外で営業部長承認待ちが平均 18h 発生」(source: SH-001 インタビュー)
  - FND-003: 「物流側は現状 2h で出荷可能」(source: SH-003 インタビュー、業務観察併用)
- **unresolved_questions:**
  - Q-001: 「夜間バッチでの IDoc 再送ロジックの正本は誰が持っているか?」
- **contradictions:**
  - 営業部長は「与信 = 営業判断」、IT は「与信 = ERP マスタ」と回答。要調停。
- **deferred_topics:**
  - 「将来的な海外拠点展開」は本案件のスコープ外として保留

### 42.3.3 Gate 0.3 (Elicitation Gate)

- 主要 SH への elicitation 完了
- unresolved_questions の blocking 件数 0 (Q-001 は IT 部門長への follow-up で確認済み)
- contradictions の調停を `change_strategy.transition_states` に反映 (与信判定の段階的移行を Iteration 3 で再確定)

## 42.4 Phase 0.5 — Context Modelling (Week 3)

### 42.4.1 LAYER-SYS

- `actor_system.yaml` (ACS-001):
  - actors: ACT-001「営業担当」、ACT-002「物流担当」、ACT-003「経理担当」
  - systems: SYS-001「SAP S/4HANA」、SYS-002「Salesforce SFA」、SYS-003「自社受注ポータル」
  - interactions: 「営業担当 → 自社ポータル → IDoc 経由 SAP」「物流担当 → SAP 出荷オーダー」

### 42.4.2 LAYER-BIZ

- `business_usecase.yaml` (BUC-001 「受注登録」):
  - actor_ids: ["ACT-001"]
  - trigger: 「顧客 PO 受領」
  - outcome: 「ERP 受注番号採番 + Salesforce 案件更新」
  - main_flow: 「自社ポータル入力 → 与信判定 → SAP 連携 → 確認応答」
- `business_usecase.yaml` (BUC-002 「与信例外承認」):
  - actor_ids: ["ACT-001", "営業部長 (SH-001)"]
  - trigger: 「与信限度超過受注」

### 42.4.3 LAYER-COND

- `information_state.yaml` (INS-001 「受注」):
  - states: ["登録待ち", "与信判定中", "登録済み", "出荷準備", "完了", "差戻し"]
  - transitions: 「与信判定中 → (与信内) → 登録済み」 / 「与信判定中 → (与信外) → 営業部長承認待ち」
  - sor_system: SYS-001 (SAP)
- `condition_variation.yaml` (CVR-001 「与信判定」):
  - expression: "顧客.与信限度 >= 受注.金額"
  - variations: 「PASS → 自動登録」 / 「FAIL → 営業部長承認待ち」
  - linked_usecase_ids: ["BUC-001", "BUC-002"]

### 42.4.4 LAYER-BUC

- `usecase_complex.yaml` (UCX-001):
  - usecase_ref: "BUC-001"
  - actor_refs: ["ACT-001"]
  - information_refs: ["INF-001"]
  - condition_refs: ["CND-001"]
  - flow_summary: 「ACT-001 が ポータル入力 → CND-001 評価 → INF-001 状態遷移」

### 42.4.5 LAYER-RAR

- `requirements_architecture.yaml` (RAR-001):
  - 4 レイヤーすべて填まり、cross_layer_links が SYS → BIZ → BUC → COND の単方向 5 本で接続される
  - 循環なし、孤児ノードなし

### 42.4.6 Gate 0.5 (Context Modelling Gate)

- Article XVI (proposed) の criteria を満たす
- 4 レイヤーすべて存在 + cross_layer_links 非循環 + 各 layer items 最低 1 件
- ⛔ アーキテクトの承認待ち → 承認後 Phase 1 へ

## 42.5 Phase 1 (Design) への接続

VALUE Upstream Extension が完了した時点で `basic_design.md` の作成は次のように **テンプレートからの翻訳** に近づく。

### 42.5.1 traceability_rows の自動派生

- `requirements_architecture.cross_layer_links` で COND → BUC → BIZ → SYS のチェーンが既に張られている
- これを `basic_design.traceability_rows` に展開 (RQ-NNN → US-NNN → AC-NNN-NN → BPMN-TASK-NNN → CT-API-NN → TS-INT-NN → T-GNN-NNN)
- Phase B の `stride upstream to-design <feature>` ツール (予定) で半自動化

### 42.5.2 process.bpmn の構造起点

- `usecase_complex.flow_summary` が `process.bpmn` の StartEvent → Tasks → EndEvent の骨格を提供
- BPMN-TASK-001..NNN は BUC-001..NNN と 1:1 対応する場合が多い
- §4-BPMN MUST-DO の ID 完全一致ルール (`basic_design.bpmn_descriptions[].bpmn_id` ↔ process.bpmn 実 ID) は変わらず適用

### 42.5.3 spec.md AC への直行

- `condition_variation.conditions[].expression` が `spec.use_cases[].acceptance[].statement` の元素材
- BDD (Given-When-Then) 形式へ翻訳: 「Given 顧客.与信限度 >= 受注.金額 / When 受注登録 / Then ERP 自動登録」

## 42.6 Phase B での自動化予定

| 機能 | コマンド (予定) |
|------|---------------|
| Phase 0-0.5 一括 scaffold | `stride upstream init <feature>` |
| BACCM 6 軸 + 4 レイヤー機械検証 | `stride upstream validate <feature>` |
| 3-iteration pattern 進行管理 | `stride upstream iterate <feature> --phase <0/0.3/0.5>` |
| Discovery → basic_design 半自動翻訳 | `stride upstream to-design <feature>` |
| Multi-Model Evaluator Discovery 拡張 | `stride evaluate <feature> --discovery` |
| 稼働後評価 (Article XVII) | `stride evaluate --post-deployment <feature>` |

## 42.7 Profile 別の所要工数 (経験則的な目安)

| Profile | Phase 0 | Phase 0.3 | Phase 0.5 | 合計 |
|---------|---------|-----------|-----------|------|
| `enterprise-erp` | 1-2 週 | 1 週 | 1-2 週 | 3-5 週 |
| `saas-integration` | 1 週 | 0.5 週 | 1 週 | 2.5 週 |
| `prototype` | 0.5 週 | (option) | (option) | 0.5-1 週 |

(Phase A 時点では実績未集計。上記は STRIDE 既存案件と BABOK / Layered Requirements Modeling 標準的事例からの推定値。Phase B 以降で `stride retro` 連動の実績ベース化を予定。)

## 42.8 関連章 / 参考

- 39 章 — VALUE Upstream Extension 概要
- 40 章 — BACCM 完全性ゲート (Phase 0)
- 41 章 — Layered Requirements Architecture (Phase 0.5)
- `memory/constitution_amendments/XV-XVII.md` — Article XV / XVI / XVII (proposed)
- `shared/policies/upstream_iteration_policy.yaml` — 3-iteration pattern 定義
- `sdd-templates/templates/upstream/README.md` — 15 テンプレート索引

## 42.9 Attribution

- **BABOK v3 (IIBA)** — KA4 / KA6 / KA7 / KA8 / §10 Techniques refs — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — 4-layer architecture and iteration concept refs — fair-use, layer names and structural concept refs only
- **value-driven discovery (philosophical foundation)** — value design models (philosophical inspiration only) — fair-use, model names only
- 本章の仮想案件「ERP 受注処理リードタイム短縮」は VALUE Upstream Extension の運用例示用に Claude が作成した架空の事例であり、特定の実案件・実顧客を指すものではない。
