# Article XVI (ratified) — Layered Requirement Architecture (4-layer aligned)

> **Status:** **ratified** (2026-04-29, Phase C, FEAT-VALC01)
> **Phase G amendment:** terminology rephrased to brand-neutral form (2026-05-01, FEAT-VALG01-prep, PR-C of UX-prep series). Article structure / rules / criteria unchanged; only proprietary brand names are removed in favor of concept-level descriptions.
> **Phase:** C (ratified) → G UX-prep (terminology rephrased)
> **Reviewer:** Tecnos Architecture Board
> **Target merge:** Phase B (with `meta.version` bump and `amendment_history` entry)

## 1. Purpose

Tecnos-STRIDE が扱う ERP / SCM / CRM 統合案件は、業務文脈が **System / Business / BusinessUseCase / Conditions** の 4 階層に自然に分かれている。Phase 0.5 (Context Modelling) 工程として、この 4 階層を **明示的な要求アーキテクチャ** として宣言・トレース可能にすることで、`spec.md` (HOW を含まない WHAT/WHY) と `plan.md` (HOW) の境界を上流で検証できるようにする。

本 Article は **4-layer requirements architecture (System / Business / BusinessUseCase / Conditions)** の階層構造を概念参照として採用するが、特定の固有商標 (proprietary brand) 名は本ドキュメントには含めない。レイヤー名と関係性のみを記述する (concepts only, no proprietary brand names)。

## 2. Article (proposed YAML)

```yaml
articles_proposed:
  - id: "XVI"
    name: "Layered Requirement Architecture (Phase 0.5 Context Modelling Gate)"
    summary: "上流要求を System / Business / BusinessUseCase / Conditions の 4 レイヤーで明示的に階層化する"
    rules:
      - "Phase 0.5 (Context Modelling) では、actor_system (System layer) / business_usecase (Business layer) / usecase_complex (BusinessUseCase layer) / condition_variation (Conditions layer) の 4 レイヤーを揃える"
      - "各レイヤーは下位レイヤーへの cross_layer_links を持ち、上→下の解像度推移をトレース可能とする"
      - "requirements_architecture.yaml が 4 レイヤーすべてを参照し、レイヤー間の不整合 (孤児ノード / 循環参照) がないこと"
      - "Phase 1 Design (basic_design.md) の bpmn_descriptions / traceability_rows は本アーキテクチャの BusinessUseCase + Conditions レイヤーから派生するものとする"
    criteria:
      - "requirements_architecture.layers が 4 レイヤー (System / Business / BusinessUseCase / Conditions) すべて定義されている"
      - "各レイヤーの items が空でない (Phase 0.5 完了時点で最低 1 件ずつ)"
      - "cross_layer_links が定義され、グラフが非循環である"
      - "Conditions レイヤーの各 condition が business_rules / decision_table によりテスタブルである"
```

## 3. Rationale

- **既存問題:** Phase 1 で `basic_design.bpmn_descriptions` を書き始めたとき、ステークホルダーや業務ドメインの輪郭が曖昧で、「BPMN の粒度をどこに合わせればよいか分からない」事案が頻発する。
- **4-layer 構造の貢献:** 4-layer requirements architecture (System / Business / BusinessUseCase / Conditions) は、要求の解像度を「外側から内側へ」「広い文脈から狭い条件へ」と段階的に絞り込む構造を提示する。Tecnos-STRIDE では同じ階層概念を、Constitution Article として明文化する価値がある。
- **STRIDE 統合の利点:** 4 レイヤーの最下層 (Conditions) は STRIDE の `acceptance_criteria` (BDD: Given-When-Then) に直接接続できるため、上流から下流までのトレーサビリティが連続的に成立する。

## 4. Phase A における取り扱い

- 本 Article は **proposed** 段階に留まる。Constitution 本体 (`memory/constitution.md`) は無変更。
- Phase A では Phase 0.5 の 6 テンプレート (actor_system / business_usecase / information_state / condition_variation / usecase_complex / requirements_architecture) のスキーマ定義のみを同梱。
- 4 レイヤー間の cross_layer_links 自動検証ツールは Phase B で実装。

## 5. Dependencies

- **Article XV (BACCM Completeness Gate)** と直交: Article XV は Discovery (Phase 0) 層、本 Article XVI は Context Modelling (Phase 0.5) 層を扱う。
- **既存 Article V (Modularity)** および **Article IX (Integration-First)** と整合: 本 Article は境界明示と統合検証の上流対応版として機能する。
- **既存 Article III (Test-First)** と接続: Conditions レイヤーが BDD `acceptance_criteria` に流れる。

## 6. Acceptance Criteria for Future Merge (Phase B)

- `stride upstream validate` ツールが 4 レイヤーの完全性 + cross_layer_links の非循環性を検証できること
- `requirements_architecture.yaml` から `basic_design.bpmn_descriptions` を半自動生成する scaffolder が動くこと
- 本 Article 採択時に `meta.version` と `amendment_history` を bump する PR が独立に提出されること

---

## Attribution

- **4-layer Requirements Architecture** — System / Business / BusinessUseCase / Conditions のレイヤー名と階層概念を採用 (concepts only, no proprietary brand names).
- **BABOK v3 (IIBA)** — KA7 Requirements Analysis and Design Definition (§7.5 Define Requirements Architecture, Technique 10.41 Scope Modelling) — fair-use, names and section refs only.
- 本ドキュメントの記述はすべて Claude (Opus 4.7) による独自要約であり、原典テキストの逐語的引用は含まない。
