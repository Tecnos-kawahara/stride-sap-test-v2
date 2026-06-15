---
artifact: "spec"
feature_id: "FEAT-XXX"
spec_id: "SPEC-XXX"
version: "1.1.4"
title: "<Feature Name> Specification"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "Taro Yamada", role: "Product Owner" }
  - { name: "Hanako Suzuki", role: "Tech Lead" }
links:
  basic_design_ref: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  related_branches: []
  git_issues: []
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
generated_by: "/speckit.specify"
---

> Rule-0: WHAT/WHY only. HOWは禁止（技術選定・実装詳細・UI詳細は plan.md へ）。
> Note: フロー正本は process.bpmn（承認済み）を参照する。

# 0. Canonical Spec (YAML) — AI Source of Truth
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.1.4"

derived_fields:
  counts_are_computed: true
  computed_by: "CI/speckit-lint"
  human_edit: "forbidden"

spec:
  pitch:
    who: ""
    what: ""
    why: ""

  goals:
    business: []
    user: []
    non_goals: []

  stakeholders:
    personas:
      - id: "P-001"
        name: ""
        summary: ""
        needs: []
    others: []

  usage_context:
    channels: ["web", "api"]
    timing_frequency: ""

  use_cases:
    - id: "US-FEATXXX-001"
      persona: "P-001"
      capability: ""
      reason: ""
      notes: ""
      acceptance:
        - id: "AC-US-FEATXXX-001-01"
          given: ""
          when: ""
          then: ""
          tags: ["functional"]
        - id: "AC-US-FEATXXX-001-02"
          given: ""
          when: ""
          then: ""
          tags: ["integration"]

  nfr:
    performance:
      requirements: []
    availability_reliability:
      requirements: []
    security_privacy:
      requirements: []
    operations:
      requirements: []

  dependencies:
    external_systems:
      - name: ""
        role: ""
        tags: []
    other_teams: []

  open_questions:
    - id: "Q-001"
      text: "[NEEDS CLARIFICATION: ]"
      blocking: true
      issue: ""   # optional

  assumptions:
    - id: "A-001"
      text: ""
      needs_validation_in_plan: true

spec_gate_check:
  counts:
    use_cases: 0
    acceptance_criteria: 0
    integration_tagged_ac: 0
    blocking_questions: 0
    nfr_items: 0
  rules:
    min_use_cases: 1
    min_total_acceptance_criteria: 1
    min_integration_acceptance_criteria: 1
    max_blocking_questions: 0
    min_nfr_items: 1
  all_use_cases_have_ac: false
  no_blocking_open_questions: false
  nfr_covered: false
  integration_critical_ac_present: false
  what_only_no_how: true
  constitution_aligned: false
  ai_plan_ready: false
```

# 1. Human-readable Summary（HITL向け要約）

## 1.1 エレベーターピッチ

* Who:
* What:
* Why:

## 1.2 フロー正本（参照）

* process.bpmn: {{ links.process_bpmn_ref }}

## 1.3 ゴール / 非ゴール

* Goals:
* Non-goals:

> End of spec.md
