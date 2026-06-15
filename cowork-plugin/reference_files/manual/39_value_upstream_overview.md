# 39. VALUE Upstream Extension 概要 (Phase A)

> Tecnos-STRIDE v5.4 + VALUE Upstream Extension (codename: VALUE) Phase A
> 本章は STRIDE の上流 (Phase 1 Design 着手前) を BABOK v3 / Layered Requirements Modeling / value-driven discovery method (思想参考) で補強する VALUE Upstream Extension の全体像を示す。

## 39.1 なぜ VALUE が必要か

Tecnos-STRIDE v5.4 までの開発フローは、Phase 1 (Design) を `basic_design.md` から開始する設計だった。これは「業務側と AI/Tech 側の認識齟齬を潰すハブ」として有効に機能してきた一方、**`basic_design.md` を書き始める手前で「Why / Stakeholder / Value / Context」が言語化されていない**ケースが ERP / SCM / CRM 統合案件で頻発していた。

具体的には次のような事象が観測されていた。

- BPMN のタスク粒度をどこに合わせればよいか分からないまま `process.bpmn` の作成に入ってしまう
- 受入条件 (AC) が「動けば良い」レベルで止まり、価値計測指標 (KPI / KGI) と乖離する
- ステークホルダーマップが暗黙のまま進み、Phase 4 で初めて「決裁者を聞いていなかった」と気付く
- 監査・SoD・統合観点が後工程まで持ち越され、Phase 4 で大きな手戻りが発生する

VALUE Upstream Extension は、これらの上流の薄さを **BABOK v3 (IIBA) の Business Analysis 体系 + Layered Requirements Modeling ((concept reference, no proprietary brand)) の階層的要求モデル + value-driven discovery method の価値設計思想** を組み合わせて補強する。原典テキストの逐語的引用は行わず (fair-use、名前・セクション参照・概念ラベルのみ)、Claude による独自要約 + STRIDE 流の機械可読化 (YAML スキーマ + JSON Schema + 完全性ゲート) として再構築している。

## 39.2 Phase A のスコープ

VALUE Upstream Extension は段階的に導入される。**Phase A は基盤定義のみ** であり、ツール実装・CLI 拡張・lint 拡張は **Phase B** 以降で行う。

Phase A で配備されるのは次の 4 種 32 ファイル + 既存 2 ファイルへの追記である。

| カテゴリ | 件数 | 内容 |
|---------|------|------|
| `shared/policies/upstream_*.yaml` | 4 | Phase 0 / 0.3 / 0.5 適用度・BACCM 6 軸完全性・BABOK 50 技法カタログ・3-iteration pattern |
| `sdd-templates/templates/upstream/*.yaml` + `README.md` | 16 | 15 artifact templates + 索引 |
| `memory/constitution_amendments/XV-XVII.md` | 3 | Article XV (BACCM Gate) / XVI (Layered Requirement Architecture) / XVII (Solution Evaluation Loop) を **proposed** として宣言 |
| `manual/39-42.md` | 4 | 本章を含む VALUE 関連解説 |
| `tests/test_upstream_*.py` | 5 | スキーマ整合性 / BACCM policy / technique 50 件 / policy consistency / amendment proposed-only テスト |
| 既存ファイル追記 (許可された 2 ファイル) | 2 | `manual/_sidebar.md` (新章リンク末尾追加) + `agent_docs/project_map.md` (1 段落 5 行以内) |

**重要:** Constitution 本体 (`memory/constitution.md`) と他の改変禁止リスト 65 ファイルは **Phase A で一切変更しない**。`shasum -c` による hash 検証で完全性を担保する。

## 39.3 3 つのフェーズ (Phase 0 / 0.3 / 0.5)

VALUE Upstream Extension は STRIDE Phase 1 Design の **手前** に 3 段の上流フェーズを追加する。

### Phase 0 — Discovery (BABOK KA6, Gate 0)

**目的:** Why / Stakeholder / Value / Context を発見・整理し、案件の存在意義を確定する。

**成果物 (7 種):**
- `business_need.yaml` (BNE): 解決すべき問題 / 活用すべき機会
- `value_canvas.yaml` (VLC): from_state / to_state / potential_value / anti_value
- `stakeholder_map.yaml` (SHM): 関係者リスト (最低 3 件)
- `context_map.yaml` (CTX): 内部 / 外部文脈・規制
- `risk_register.yaml` (RRG): リスク識別と対応計画
- `change_strategy.yaml` (CHS): 中間状態と段階的展開計画
- `goal_tree.yaml` (GLT): ゴール階層

**ゲート:** BACCM 6 軸完全性 (Article XV proposed) を 100% 満たすこと。

### Phase 0.3 — Elicitation (BABOK KA4, Gate 0.3)

**目的:** ステークホルダーから情報を引き出し、確認する。

**成果物 (2 種):**
- `elicitation_plan.yaml` (ELP): 採用技法・対象 SH・スケジュール
- `elicitation_results.yaml` (ELR): findings / 未解決質問 / 矛盾

**ゲート:** 主要ステークホルダーへの elicitation が完了し、未解決の blocking question が解消されていること。

### Phase 0.5 — Context Modelling (BABOK KA7, Gate 0.5)

**目的:** 業務文脈を System / Business / BusinessUseCase / Conditions の 4 階層で構造化する。

**成果物 (6 種):**
- `actor_system.yaml` (ACS): アクター・連携システム (Layered Requirements Modeling System layer)
- `business_usecase.yaml` (BUC): ビジネスユースケース (Layered Requirements Modeling Business layer)
- `information_state.yaml` (INS): 情報モデル + 状態モデル
- `condition_variation.yaml` (CVR): ビジネスルール + 決定表
- `usecase_complex.yaml` (UCX): UC 複合 (Layered Requirements Modeling BUC × Actor × Information × Condition)
- `requirements_architecture.yaml` (RAR): 4 レイヤー連結 (Layered Requirements Modeling Requirements Architecture)

**ゲート:** Layered Requirement Architecture (Article XVI proposed) で 4 レイヤーすべてが整い、cross_layer_links が非循環であること。

## 39.4 Profile 別適用度

VALUE は STRIDE v5.4 の Profile 軸 (`enterprise-erp` / `saas-integration` / `prototype`) に応じて適用度を切り替える。

| Profile | Discovery | Elicitation | Context Modelling |
|---------|-----------|-------------|-------------------|
| `enterprise-erp` (default) | required | required | required |
| `saas-integration` | required | recommended | required |
| `prototype` | lite | optional | optional |

`prototype` でも Discovery は最低限 (Stakeholder + Value Canvas) を求めることで、PoC 段階でも「誰のための、何の価値か」を曖昧にしない安全弁を保つ。

## 39.5 STRIDE 既存軸との関係

| 軸 | 単位 | VALUE との関係 |
|----|------|----------------|
| **Coverage Tier** (critical / standard / experimental) | feature | VALUE は Tier の上位概念に直接影響しない |
| **Mode** (autopilot / confirm / validate) | WI | VALUE は Mode を変更しない (Phase 0-0.5 の儀式量は Profile で制御) |
| **Profile** (enterprise-erp / saas-integration / prototype) | feature | VALUE の Phase 0-0.5 適用度を切り替える唯一の軸 |
| **Constitution Articles I-XIV** | グローバル | VALUE は Article XV / XVI / XVII を **proposed** として追加 (Phase A は本体不変) |

## 39.6 Phase B への申し送り

Phase A で実装されない機能 (Phase B 以降):

- `stride upstream init <feature>` — 15 templates 一括 scaffold
- `stride upstream validate <feature>` — BACCM 6 軸完全性 + 4 レイヤー整合性 + JSON Schema 検証
- `stride evaluate --discovery` — Multi-Model Evaluator の Discovery phase 拡張
- `stride upstream iterate` — 3-iteration pattern (bootstrap → structure → refinement) の進行管理
- 稼働後評価 (`stride evaluate --post-deployment`) と `spec-impact:required` Issue 自動起票連動 (Article XVII)
- Constitution 本体への正式マージ (Article XV / XVI / XVII の `meta.version` および `amendment_history` の bump を伴う独立 PR)

## 39.7 関連章

- `40_baccm_guide.md` — BACCM 6 軸の詳細と完全性ゲート
- `41_layered_requirements_modeling_guide.md` — 4-layer Requirements Architectureモデルの STRIDE 流運用
- `42_upstream_phases_walkthrough.md` — Phase 0 → 0.3 → 0.5 → Phase 1 連続フロー実例

## 39.8 Attribution

- **BABOK v3 (IIBA)** — framework backbone (KA4 Elicitation / KA6 Strategy Analysis / KA7 Requirements Analysis / §10 Techniques) — fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — structural integrity (4-layer architecture, diagram names) — fair-use, layer/diagram names only
- **value-driven discovery (philosophical foundation)** — philosophical inspiration (value design models) — fair-use, model names only

原典テキストの長文転記は行わず、説明文はすべて Claude (Opus 4.7) による独自要約。
