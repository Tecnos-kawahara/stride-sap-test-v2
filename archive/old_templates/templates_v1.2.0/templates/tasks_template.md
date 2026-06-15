---
artifact: "tasks"
feature_id: "FEAT-XXX"
tasks_id: "TASKS-XXX"
version: "1.2.0"
title: "<Feature Name> Task Breakdown"
status: "draft" # draft | in_progress | completed | ai_reviewed | human_approved | deprecated
owners:
  - { name: "Hanako Suzuki", role: "Tech Lead" }
  - { name: "AI Task Agent", role: "Task Generator" }
inputs:
  spec_path: "specs/XXX_feature_name/spec.md"
  plan_path: "specs/XXX_feature_name/plan.md"
  basic_design_path: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#1 Canonical Tasks (YAML)**。説明文は補助。
> Rule-1: plan_refs は stable id のみ（CMP/LIB/CT/TS/Phase/G）。

# 1. Canonical Tasks (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0"

derived_fields:
  counts_are_computed: true
  counts:
    tasks: 0
    use_cases_referenced: 0
    acceptance_referenced: 0
    tasks_with_plan_refs: 0
    dependency_edges: 0
    milestones: 0

tasks_gate_check:
  counts:
    tasks: 0
    use_cases_referenced: 0
    acceptance_referenced: 0
    tasks_with_plan_refs: 0
    dependency_edges: 0
    milestones: 0
  rules:
    min_tasks: 5
    min_use_cases_referenced: 1
    min_acceptance_referenced: 1

  all_us_covered: false
  all_ac_tested: false
  groups_mapped: false
  no_dependency_errors: true
  constitution_aligned: false
  tasks_ready_for_code: false

tasks:
  tasks:
    - id: "T-G01-001"
      title: "Define API contract (CT-API-01)"
      type: "contract" # contract | test | impl | docs | research | ops
      description: ""
      spec_refs: ["US-FEATXXX-001", "AC-US-FEATXXX-001-01"]
      plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1", "LIB-01", "CMP-01"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: []
      outputs:
        - "specs/XXX_feature_name/contracts/api/openapi.yaml"
      done_when:
        - "Contract artifact exists and is reviewable"
        - "speckit-lint passes"
    - id: "T-G01-002"
      title: "Write contract tests (TS-CON-01)"
      type: "test"
      description: ""
      spec_refs: ["AC-US-FEATXXX-001-01"]
      plan_refs: ["TS-CON-01", "CT-API-01", "G-01-contracts", "Phase-1"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G01-001"]
      outputs:
        - "specs/XXX_feature_name/tests/contract/"
      done_when:
        - "Tests exist and fail in Red phase (if applicable)"
        - "speckit-lint passes"

  milestones:
    - id: "M-01"
      name: "Contracts ready"
      exit_criteria:
        - "All CT-* are defined"
        - "TS-CON-* exists"
      related_task_ids: ["T-G01-001", "T-G01-002"]

  risks:
    - id: "R-001"
      risk: ""
      impact: ""
      mitigation: ""
```

---

# 2. Minimal Human Notes（任意）
- 調整事項:
- ブロッカー:

> End of tasks.md
