# Article XV (ratified) — BACCM Completeness Gate

> **Status:** **ratified** (2026-04-29, Phase C, FEAT-VALC01)
> **Phase:** C (ratified)
> **Reviewer:** Tecnos Architecture Board
> **Target merge:** Phase B (with `meta.version` bump and `amendment_history` entry)

## 1. Purpose

Tecnos-STRIDE v5.4 までの Phase 1 Design は `basic_design.md` を起点としていたが、その手前 (Why / Stakeholder / Value / Context が確定していない段階) で `basic_design.md` の作成に踏み込んでしまう事案が散見された。
本 Article は、Phase 1 着手前のゲートとして **BABOK v3 §2.1 Business Analysis Core Concept Model (BACCM)** の **6 軸 (Change / Need / Solution / Stakeholder / Value / Context)** が **すべて満たされていること** を明示的な前提条件として宣言する。

## 2. Article (proposed YAML)

```yaml
articles_proposed:
  - id: "XV"
    name: "BACCM Completeness Gate (Discovery Phase 0)"
    summary: "Phase 1 Design 着手前に BACCM 6 軸を完全性ゲートとして必須化する"
    rules:
      - "Phase 1 (Design) を開始するには、BACCM 6 軸 (Change / Need / Solution / Stakeholder / Value / Context) を支える Phase 0 成果物 (business_need / value_canvas / stakeholder_map / context_map / change_strategy / goal_tree) がすべて確定していること"
      - "Stakeholder 軸は最低 3 件のステークホルダー記述を要求する"
      - "Profile 別適用度は shared/policies/upstream_policy.yaml に従う (enterprise-erp = required / saas-integration = required / prototype = lite)"
      - "BACCM 完全性は shared/policies/baccm_completeness.yaml の axes 定義で機械検証可能とする"
    criteria:
      - "BACCM 6 軸の各 source_artifact が存在し、required_keys / required_min_count を満たす"
      - "completeness_scoring.threshold_for_gate_0 == 100 (partial credit を許容しない)"
      - "Phase 0 成果物に対する明示的な Gate 0 (Discovery Gate) が APPROVAL.md で承認される"
```

## 3. Rationale

- BABOK v3 は **BACCM (§2.1)** を Business Analysis の中核概念として定義しており、Change / Need / Solution / Stakeholder / Value / Context のいずれか 1 軸でも欠落すると業務分析の整合性が破綻する。
- Tecnos の ERP / SCM / CRM 統合案件では「価値と利害関係者が曖昧なまま設計に着手 → 後工程で前提崩壊 → 大規模手戻り」というパターンが繰り返し発生していた。
- BACCM の完全性を **機械検証可能** な形で Phase 1 着手前のゲートにすることで、上流の安全弁が常時 active となる。

## 4. Phase A における取り扱い

- 本 Article は **proposed** 段階に留まる。Constitution 本体 (`memory/constitution.md`) の `meta.version` および `amendment_history` は Phase A では更新しない。
- Phase A では `shared/policies/baccm_completeness.yaml` の policy 定義と、Phase 0 の 7 テンプレート (business_need / value_canvas / stakeholder_map / context_map / risk_register / change_strategy / goal_tree) を同梱するのみ。
- Phase B 以降で Constitution 本体への正式マージを検討する際、本ファイルが起点となる。

## 5. Dependencies

- **下流の Articles に対する破壊的変更:** なし。Article I-XIV はすべて維持される。
- **追加: Article XVI (Layered Requirement Architecture)** との併存可能。Article XVI が Context Modelling 層の完全性を扱い、本 Article XV は Discovery 層の完全性を扱う (上下に直交)。

## 6. Acceptance Criteria for Future Merge (Phase B)

- `stride upstream validate` ツールが BACCM 6 軸の充足を JSON で出力できること
- `phase_gate.py` が Phase 1 着手前に `Discovery Gate` 状態を判定できること
- 本 Article 採択時に `meta.version` と `amendment_history` を bump する PR が独立に提出されること

---

## Attribution

- **BABOK v3 (IIBA)** — BACCM definition source (§2.1, p.12) — fair-use, axis names and concept refs only.
- 本ドキュメントの記述はすべて Claude (Opus 4.7) による独自要約であり、原典テキストの逐語的引用は含まない。
