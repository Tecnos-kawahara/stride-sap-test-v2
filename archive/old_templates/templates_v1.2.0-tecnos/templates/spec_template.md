---
artifact: "spec"
template_id: "TPL-SPEC-TECNOS-001"
feature_id: "FEAT-XXX"
spec_id: "SPEC-XXX"
version: "1.2.0-tecnos"
title: "<Feature Name> Specification"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Business Owner>", role: "Product Owner / Business" }
  - { name: "<Tech Lead>", role: "Tech Lead" }
links:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  basic_design_ref: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  plan_md_ref: "specs/XXX_feature_name/plan.md"
  tasks_md_ref: "specs/XXX_feature_name/tasks.md"
  constitution_ref: "memory/constitution.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Spec (YAML)**。説明文は補助。
> Constraint: ここには HOW（実装・技術選定・API設計詳細）を書かない。Planへ。
> Tecnos: 監査・統合・運用の最低要件は `{{ links.org_constraints_ref }}` を参照。

# 0. Canonical Spec (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0-tecnos"

derived_fields:
  counts_are_computed: true
  counts:
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0
    security_items: 0
    integration_items: 0
    data_items: 0

spec_gate_check:
  counts:
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0
    security_items: 0
    integration_items: 0
    data_items: 0
  rules:
    min_use_cases: 1
    min_total_acceptance_criteria: 3
    min_integration_acceptance_criteria: 1
    max_blocking_questions: 0
    min_nfr_items: 6
    min_security_items: 1
    min_integration_items: 1
    min_data_items: 1
  no_blocking_open_questions: false
  ai_plan_ready: false

spec:
  overview:
    who: ""
    what: ""
    why: ""

  business_value:
    kpis: []  # 例: ["受注登録リードタイム -30%", "月次締め遅延=0"]
    financial_hypotheses:
      revenue_uplift: ""    # 例: "ARPU +X / Upsell"
      cost_reduction: ""    # 例: "工数 -Y"
      risk_reduction: ""    # 例: "監査指摘ゼロ"

  flow_reference:
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    notes: ""

  goals: []
  non_goals: []

  domain_terms: []
  # - term: ""
  #   definition: ""

  use_cases:
    - id: "US-FEATXXX-001"
      title: ""
      primary_actor: ""
      trigger: ""
      preconditions: []
      main_flow: []
      alternate_flows: []
      postconditions: []
      acceptance:
        - id: "AC-US-FEATXXX-001-01"
          statement: ""
          tags: ["integration"]  # integration | e2e | security | performance | data | ops
          priority: "must"       # must | should | could

  requirements:
    # Tecnos: 統合・データ・監査の明文化を必須に寄せる
    integration: []
    # - "外部入力は冪等で再送可能（idempotency key など）"
    # - "Correlation ID をログ/監査へ必ず出力できる"

    data_governance: []
    # - "SoR（System of Record）をマスタ単位で定義する"
    # - "保持期間（retention）と削除方針を明記する"

    performance: []
    availability_reliability: []
    security_privacy: []
    operations: []

  out_of_scope: []

  open_questions:
    - id: "Q-001"
      question: ""
      blocking: true
      owner: ""
      due: "YYYY-MM-DD"

  assumptions:
    - id: "A-001"
      assumption: ""
      rationale: ""
      risk_if_false: ""
```

---

# 1. Human-readable Spec（任意）
## 1.1 Goals / Non-goals
- Goals:
- Non-goals:

## 1.2 Acceptance Criteria（重要）
- ACは **テスト可能**、**曖昧語禁止**、**否定形も明確**。
- integration タグは統合テスト優先の印。

## 1.3 Non-Functional Requirements（Tecnos最小）
- **integration / data_governance / security_privacy** は最低1件ずつ。
- 監査・SoD・運用（ログ/監視/再実行性）は、外部連携の有無に関わらず論点化する。

> End of spec.md
