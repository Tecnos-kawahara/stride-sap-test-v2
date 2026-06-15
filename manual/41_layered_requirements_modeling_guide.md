# 41. Layered Requirements Architecture — Phase 0.5 Context Modelling

> 本章は VALUE Upstream Extension の **Phase 0.5 (Context Modelling)** で扱う **Layered Requirements Modeling 由来の 4 レイヤー要求アーキテクチャ** の STRIDE 流運用を解説する。
> 概念は Layered Requirements Modeling ((concept reference, no proprietary brand)) を参照する (fair-use, layer/diagram names only)。詳細な手法・ダイアグラム作法は原典で確認すること。

## 41.1 4 レイヤーの全体像

Layered Requirements Modeling が提唱する **要求アーキテクチャ (Requirements Architecture)** は、業務文脈を外側から内側へ段階的に絞り込む 4 階層構造を持つ。STRIDE では各レイヤーを別 YAML テンプレートとして配置し、cross_layer_links で連結する。

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER-SYS    System  (アクター・外部システム・コンテキスト)   │
│   ↓                                                          │
│ LAYER-BIZ    Business  (ビジネスユースケース)                 │
│   ↓                                                          │
│ LAYER-BUC    BusinessUseCase Complex                          │
│              (BUC × Actor × Information × Condition の交差点) │
│   ↓                                                          │
│ LAYER-COND   Conditions  (条件・バリエーション・状態)         │
└─────────────────────────────────────────────────────────────┘
```

外側 (System) は「誰と / どのシステムが関わるか」、内側 (Conditions) は「何が成立すれば AC として検証可能か」を扱う。STRIDE の AC (BDD: Given-When-Then) は最下層 Conditions から派生する。

## 41.2 レイヤー別の責務と STRIDE テンプレート

### 41.2.1 LAYER-SYS — System

**責務:** 案件に関与するアクター (人 / システム / 外部組織) と、それらが置かれるコンテキスト境界を確定する。

**STRIDE テンプレート:** `actor_system_template.yaml` (ACS)

**主要フィールド:**
- `actors`: 人 / システム / 外部 (kind: human / system / external) の体系化
- `systems`: 連携対象 (SAP / mcframe / Salesforce / 自社システム等)
- `interactions`: アクター ↔ システム間の関与関係概要

**Layered Requirements Modeling 由来概念:** アクター・外部システム図 (Actor / External System Diagram)

### 41.2.2 LAYER-BIZ — Business

**責務:** 業務側でアクターが達成したい価値の発生点 (ビジネスユースケース) を整理する。

**STRIDE テンプレート:** `business_usecase_template.yaml` (BUC)

**主要フィールド:**
- `usecases[]`: 各 BUC は actor_ids / trigger / outcome / pre_conditions / main_flow / alternate_flows / post_conditions を持つ
- `linked_information_ids` / `linked_condition_ids`: 下位レイヤーへの参照

**Layered Requirements Modeling 由来概念:** ビジネスユースケース図 (Business Use Case Diagram)

### 41.2.3 LAYER-BUC — BusinessUseCase Complex

**責務:** 1 つの BUC が「どのアクター・どの情報・どの条件と関わるか」を多角的に重ね合わせる。

**STRIDE テンプレート:** `usecase_complex_template.yaml` (UCX)

**主要フィールド:**
- `usecase_ref`: 対象 BUC への参照
- `actor_refs` / `information_refs` / `condition_refs`: 関連オブジェクト
- `flow_summary`: 4 軸を貫いた業務フローの要約 (BPMN 化前段階)

**Layered Requirements Modeling 由来概念:** UC 複合図 (UC Complex Diagram)

UCX は STRIDE の `process.bpmn` (Phase 1) に直接接続できる粒度を持つ。Phase 0.5 で UCX を確定すれば、Phase 1 の BPMN 作成は **テンプレートからの単純翻訳** に近づく。

### 41.2.4 LAYER-COND — Conditions

**責務:** 業務判断ロジックを条件式・決定表・状態遷移として **テスタブル** に落とす。

**STRIDE テンプレート:**
- `condition_variation_template.yaml` (CVR) — 条件 + バリエーション + 決定表
- `information_state_template.yaml` (INS) — 情報モデル + 状態遷移

**主要フィールド (CVR):**
- `conditions[]`: 各 condition は expression + variations + linked_usecase_ids + business_rule_source
- `decision_tables`: DMN 形式の決定表 (任意)

**主要フィールド (INS):**
- `information_items[]`: 各 entity は states + transitions + master_or_transaction + sor_system

**Layered Requirements Modeling 由来概念:** 条件モデル / 状態モデル

このレイヤーが、STRIDE Phase 2 spec.md の **Acceptance Criteria** に直接接続される。Conditions レイヤーで `expression: "顧客クラス = '与信限度超過' AND 受注金額 > 1000000"` のように書かれた条件は、AC の `given` / `when` / `then` に翻訳される。

## 41.3 Cross Layer Links — 上下レイヤー間トレーサビリティ

`requirements_architecture_template.yaml` (RAR) は 4 レイヤーをまとめて参照し、`cross_layer_links` でレイヤー間の解像度推移をトレース可能にする。

例:

```yaml
layers:
  - id: "LAYER-SYS"
    items: ["ACT-001", "SYS-001"]
  - id: "LAYER-BIZ"
    items: ["BUC-001"]
  - id: "LAYER-BUC"
    items: ["UCX-001"]
  - id: "LAYER-COND"
    items: ["CND-001", "INF-001"]

cross_layer_links:
  - { from_layer: "LAYER-SYS",  from_id: "ACT-001", to_layer: "LAYER-BIZ",  to_id: "BUC-001" }
  - { from_layer: "LAYER-BIZ",  from_id: "BUC-001", to_layer: "LAYER-BUC",  to_id: "UCX-001" }
  - { from_layer: "LAYER-BUC",  from_id: "UCX-001", to_layer: "LAYER-COND", to_id: "CND-001" }
```

**Article XVI (proposed)** は cross_layer_links が **非循環** であることを criteria に含めている (Phase B で機械検証ツール `stride upstream validate` が実装される)。

## 41.4 4 レイヤーと STRIDE Phase 1-3 への接続

### Phase 1 (Design) への接続

- `actor_system` (SYS) → `basic_design.systems` / `basic_design.context.who`
- `business_usecase` (BUC) → `basic_design.bpmn_descriptions.elements` の各 BPMN-TASK の `purpose` / `business_role`
- `usecase_complex` (UCX) → `process.bpmn` 全体構造 (BPMN フローはここから派生)

Phase 1 の BPMN 作成が UCX からの翻訳に近づくため、`stride lint` の `BPMN_VALIDATION_FAILED` を Phase 1 でいきなり踏むリスクが減る。

### Phase 2 (Specify) への接続

- `condition_variation` (CVR) → `spec.use_cases[].acceptance` の AC 文 (BDD Given-When-Then で構造化)
- `information_state` (INS) → `spec.spec_as_code` の database_schema.yaml 起点

### Phase 3 (Tasking) への接続

- `requirements_architecture.layers` → `tasks.tasks[].plan_refs` の構造的な裏付け

## 41.5 Profile 別の運用ガイド

| Profile | 4 レイヤーの必須度 |
|---------|-------------------|
| `enterprise-erp` | 4 レイヤーすべて必須。各レイヤー最低 1 件 + cross_layer_links 完備 |
| `saas-integration` | 4 レイヤーすべて必須。但し layer items の depth は ERP 案件より軽量で可 |
| `prototype` | optional。実施する場合は LAYER-SYS + LAYER-COND の 2 層に絞ってもよい |

## 41.6 アンチパターン

### 41.6.1 レイヤーをスキップする

- ❌ LAYER-SYS と LAYER-COND だけ書いて間の 2 層を飛ばす
- ✅ enterprise-erp では 4 レイヤーを全層書く。中間 2 層が薄くても **存在を明示** する (空配列ではなく最低 1 件)

### 41.6.2 cross_layer_links の循環

- ❌ LAYER-COND の condition から LAYER-SYS の actor へ「逆流」リンクを張る
- ✅ links は常に 上 → 下 (System → Business → BusinessUseCase → Conditions) のみ。 逆方向の参照は禁止

### 41.6.3 BUC の粒度不一致

- ❌ 1 つの BUC に複数の業務シナリオを詰め込み、トリガーが複数になる
- ✅ 1 BUC = 1 トリガー = 1 outcome の原則を維持。必要なら BUC を分割

### 41.6.4 Conditions レイヤーの自然言語放置

- ❌ condition の expression が「顧客に応じて承認フローが変わる」のような曖昧な記述
- ✅ 機械評価可能な式 (例: `顧客クラス IN ('A', 'B') AND 受注金額 > 1000000`) で書く

## 41.7 Phase B 以降の予定

- `stride upstream validate <feature>` で 4 レイヤー存在 + cross_layer_links 非循環 + items 最低件数を JSON 検証
- `requirements_architecture.yaml` から `basic_design.bpmn_descriptions` を半自動生成する scaffolder
- LAYER-COND の condition から `spec.use_cases[].acceptance` への自動変換
- Constitution 本体への Article XVI 正式マージ

## 41.8 関連章 / 参考

- 39 章 — VALUE Upstream Extension 概要
- 40 章 — BACCM 完全性ゲート (Phase 0)
- 42 章 — Phase 0 → 0.3 → 0.5 → Phase 1 ウォークスルー
- `memory/constitution_amendments/XVI_layered_requirement_architecture.md` — Article XVI (proposed) 全文
- 6 つのテンプレート — `sdd-templates/templates/upstream/{actor_system,business_usecase,information_state,condition_variation,usecase_complex,requirements_architecture}_template.yaml`

## 41.9 Attribution

- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — 4-layer architecture (System / Business / BusinessUseCase / Conditions) and diagram concept refs — fair-use, layer names and structural concept refs only
- **BABOK v3 (IIBA)** — KA7 §7.5 Define Requirements Architecture, §10.41 Scope Modelling, §10.47 Use Cases and Scenarios — fair-use, names and section refs only
- 本章の説明文はすべて Claude (Opus 4.7) による独自要約。原典テキストの逐語的引用は含まない。
