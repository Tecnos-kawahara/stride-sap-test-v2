---
artifact: "plan"
feature_id: "FEAT-XXX"
plan_id: "PLAN-XXX"
version: "1.2.0"
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
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Plan (YAML)**。説明文は補助。
> Rule-1: コードは書かない（Planは判断・分解・順序）。コード片は implementation-details/ に退避。

# 0. Canonical Plan (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0"

derived_fields:
  counts_are_computed: true
  counts:
    in_use_cases: 0
    libraries: 0
    contracts: 0
    tests: 0
    integration_tests: 0
    groups: 0
    exception_items: 0

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
    min_tests: 2
    min_integration_tests: 1
    min_groups: 2

  contracts_defined: false
  tests_prioritized: false
  groups_and_dependencies_defined: false
  simplicity_gate_passed: false
  anti_abstraction_gate_passed: false
  integration_first_gate_passed: false
  ai_tasks_ready: false

plan:
  inputs:
    spec_path: "specs/XXX_feature_name/spec.md"
    basic_design_path: "specs/XXX_feature_name/basic_design.md"
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    constitution_path: "memory/constitution.md"

  scope:
    in_use_cases: ["US-FEATXXX-001"]
    out_of_scope: []

  flow_mapping:
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"
    groups_to_bpmn:
      - group_id: "G-01-contracts"
        bpmn_refs: ["BPMN-TASK-001"]

  architecture:
    components:
      - id: "CMP-01"
        name: ""
        responsibility: ""
        boundaries: ""

    libraries:
      - id: "LIB-01"
        name: ""
        responsibility: ""
        public_interfaces: ["CT-CLI-01", "CT-API-01"]
        dependencies: []

  contracts:
    cli:
      - id: "CT-CLI-01"
        name: ""
        purpose: ""
        io_profile: "text-in/text-out + JSON"
        versioning: "semver"
        owner_component: "CMP-01"

    apis_events:
      - id: "CT-API-01"
        name: ""
        kind: "api"     # api | event
        direction: "inbound" # inbound | outbound | bidirectional
        purpose: ""
        versioning: "semver"
        owner_component: "CMP-01"

  test_strategy:
    principles:
      - "Contract-first"
      - "Integration-first"
      - "Trace AC-* to TS-*"
    tests:
      - id: "TS-CON-01"
        type: "contract"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]
      - id: "TS-INT-01"
        type: "integration"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]

  phases:
    - id: "Phase-1"
      name: "Contracts & Test Skeleton"
      objective: ""
      groups:
        - id: "G-01-contracts"
          name: "Define contracts"
          objective: ""
          deliverables:
            - "specs/XXX_feature_name/contracts/"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-CLI-01", "CT-API-01"]
            tests: ["TS-CON-01"]
            phases: ["Phase-1"]
            groups: ["G-01-contracts"]
          bpmn_refs: ["BPMN-TASK-001"]
          depends_on_groups: []

    - id: "Phase-2"
      name: "Integration"
      objective: ""
      groups:
        - id: "G-02-integration"
          name: "Integration tests"
          objective: ""
          deliverables:
            - "specs/XXX_feature_name/tests/"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01"]
            tests: ["TS-INT-01"]
            phases: ["Phase-2"]
            groups: ["G-02-integration"]
          bpmn_refs: ["BPMN-TASK-001"]
          depends_on_groups: ["G-01-contracts"]

  risks:
    - id: "R-001"
      risk: ""
      impact: ""
      mitigation: ""

  exceptions: []
  # - article: "VIII"
  #   reason: ""
  #   mitigation: ""
```

---

# 1. Human-readable Summary（最小）
- Flow reference: {{ inputs.process_bpmn_path }}
- Next step: set `plan_gate_check.ai_tasks_ready: true` then run `/speckit.tasks`

> End of plan.md
