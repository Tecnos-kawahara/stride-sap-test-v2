---
artifact: "plan"
feature_id: "FEAT-XXX"
plan_id: "PLAN-XXX"
version: "1.1.4"
title: "<Feature Name> Implementation Plan"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "Hanako Suzuki", role: "Tech Lead" }
  - { name: "AI Plan Agent", role: "Plan Generator" }
inputs:
  spec_path: "specs/XXX_feature_name/spec.md"
  basic_design_path: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
  constitution_path: "memory/constitution.md"
related_branches:
  - "feature/xxx_feature_name"
related_outputs:
  tasks_md: "specs/XXX_feature_name/tasks.md"
  data_model_md: "specs/XXX_feature_name/data-model.md"
  contracts_dir: "specs/XXX_feature_name/contracts/"
ai_agent_config:
  agents: ["Plan", "Diff"]
  tools: ["/speckit.tasks", "/speckit.diff"]
generated_by: "/speckit.plan"
generated_at: "YYYY-MM-DDTHH:MM:SSZ"
updated_at: "YYYY-MM-DDTHH:MM:SSZ"
---

> Rule-0: コードは書かない。HOW方針・分解・順序・ガードレールを定義する。
> Note: process.bpmn（承認済み）をフロー正本として参照し、タスク/契約/テストへ落とす。

# 0. Canonical Plan (YAML) — AI Source of Truth
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.1.4"

derived_fields:
  counts_are_computed: true
  computed_by: "CI/speckit-lint"
  human_edit: "forbidden"

plan:
  scope:
    in_use_cases: ["US-FEATXXX-001"]
    out_use_cases: []
    in_nfr: []
    out_nfr: []

  technical_context:
    architecture_style: ""     # monolith/microservices/etc
    runtime_frameworks: []
    infra: []
    constraints: []

  architecture:
    components:
      - id: "CMP-01"
        name: ""
        responsibility: ""
        boundary: ""
    libraries:
      - id: "LIB-01"
        name: "lib-xxx"
        responsibility: ""
        use_cases: ["US-FEATXXX-001"]

  data:
    entities:
      - name: ""
        summary: ""
    storage_policy:
      primary_store_type: ""
      consistency: ""
      notes: ""

  contracts:
    cli:
      - id: "CT-CLI-01"
        name: ""
        purpose: ""
        io_format: "json"
    apis_events:
      - id: "CT-API-01"
        name: ""
        type: "rest"
        purpose: ""
        integration_critical: true

  test_strategy:
    tests:
      - id: "TS-CON-01"
        type: "contract"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]
      - id: "TS-INT-01"
        type: "integration"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-02"]
    observability:
      logs: []
      metrics: []
      traces: []

  phases:
    - id: "Phase-1"
      groups:
        - id: "G-01-core-lib"
          purpose: ""
          depends_on: []
          parallel_hint: true

  exceptions: []

plan_gate_check:
  counts:
    in_use_cases: 0
    libraries: 0
    contracts: 0
    tests: 0
    integration_tests: 0
    groups: 0
    exception_items: 0
  rules:
    min_in_use_cases: 1
    min_libraries: 1
    min_contracts: 1
    min_tests: 1
    min_integration_tests: 1
    min_groups: 1
    exception_items_must_have_reason_and_mitigation: true
  all_us_mapped: false
  contracts_defined: false
  tests_prioritized: false
  groups_and_dependencies_defined: false
  simplicity_gate_passed: false
  anti_abstraction_gate_passed: false
  integration_first_gate_passed: false
  ai_tasks_ready: false
```

# 1. Human-readable Summary（最小）

* Flow reference: {{ inputs.process_bpmn_path }}
* Next step: set `ai_tasks_ready: true` then run `/speckit.tasks`

> End of plan.md
