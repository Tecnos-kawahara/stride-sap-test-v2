---
artifact: "tasks"
template_id: "TPL-TASKS-TECNOS-001"
feature_id: "FEAT-XXX"
tasks_id: "TASKS-XXX"
version: "1.2.0-tecnos"
title: "<Feature Name> Task Breakdown"
status: "draft" # draft | in_progress | completed | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Tech Lead>", role: "Tech Lead" }
  - { name: "AI Task Agent", role: "Task Generator" }
inputs:
  spec_path: "specs/XXX_feature_name/spec.md"
  plan_path: "specs/XXX_feature_name/plan.md"
  basic_design_path: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
  org_constraints_path: "memory/tecnos_org_constraints.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#1 Canonical Tasks (YAML)**。説明文は補助。
> Rule-1: plan_refs は stable id のみ（CMP/LIB/CT/TS/Phase/G）。
> Tecnos: 監査・SoD・運用のタスクを「後回し」にしない（contracts/test/ops/pmo を最低限入れる）。

# 1. Canonical Tasks (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0-tecnos"

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
      title: "Define interface contract (CT-API-01)"
      type: "contract" # contract | test | impl | docs | research | ops | pmo
      description: "OpenAPI / Event schema / File spec 等、契約としてレビュー可能な形にする"
      spec_refs: ["US-FEATXXX-001", "AC-US-FEATXXX-001-01"]
      plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1", "LIB-01", "CMP-01"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: []
      outputs:
        - "specs/XXX_feature_name/contracts/"
      done_when:
        - "Contract artifact exists and is reviewable"
        - "Versioning policy is documented"
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

    - id: "T-G02-001"
      title: "Define audit / SoD / operational baseline (Ops note)"
      type: "ops"
      description: "監査ログ、職務分掌、再実行性、監視を最低限ドキュメント化し、実装タスクへ落とす"
      spec_refs: []
      plan_refs: ["G-02-security-ops", "Phase-1", "CMP-01"]
      bpmn_refs: []
      depends_on: ["T-G01-001"]
      outputs:
        - "specs/XXX_feature_name/implementation-details/ops.md"
      done_when:
        - "Auditability and SoD requirements are explicitly documented"
        - "Monitoring signals (metrics/logs/traces) are listed"
        - "speckit-lint passes"

    - id: "T-G03-001"
      title: "Write integration tests (TS-INT-01)"
      type: "test"
      description: "可能ならERPサンドボックス等、実環境に近い条件で統合テストを設計する"
      spec_refs: ["AC-US-FEATXXX-001-01"]
      plan_refs: ["TS-INT-01", "CT-API-01", "G-03-integration-tests", "Phase-2"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G02-001"]
      outputs:
        - "specs/XXX_feature_name/tests/integration/"
      done_when:
        - "Integration tests exist and are runnable"
        - "Test data/setup steps are documented"
        - "speckit-lint passes"

  milestones:
    - id: "M-01"
      name: "Contracts ready"
      exit_criteria:
        - "All CT-* are defined"
        - "TS-CON-* exists"
      related_task_ids: ["T-G01-001", "T-G01-002"]

    - id: "M-02"
      name: "Integration test runnable"
      exit_criteria:
        - "TS-INT-* exists"
        - "Integration environment prerequisites are documented"
      related_task_ids: ["T-G03-001"]

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
