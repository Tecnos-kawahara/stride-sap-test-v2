---
artifact: "spec"
feature_id: "FEAT-XXX"
spec_id: "SPEC-XXX"
version: "1.2.0"
title: "<Feature Name> Specification"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "Taro Yamada", role: "Product Owner" }
  - { name: "Hanako Suzuki", role: "Tech Lead" }
links:
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

# 0. Canonical Spec (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0"

derived_fields:
  counts_are_computed: true
  counts:
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0

spec_gate_check:
  counts:
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0
  rules:
    min_use_cases: 1
    min_total_acceptance_criteria: 3
    min_integration_acceptance_criteria: 1
    max_blocking_questions: 0
    min_nfr_items: 3
  no_blocking_open_questions: false
  ai_plan_ready: false

spec:
  overview:
    who: ""
    what: ""
    why: ""

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
          tags: ["integration"]  # integration | e2e | security | performance ...
          priority: "must"       # must | should | could

  requirements:
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

## 1.3 Non-Functional Requirements（NFR）
- Performance / Availability / Security / Ops を最低限埋める（countsでチェック）。

> End of spec.md
