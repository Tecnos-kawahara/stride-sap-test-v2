---
artifact: "tasks"
feature_id: "FEAT-XXX"
tasks_id: "TASKS-XXX"
version: "1.1.3"
title: "<Feature Name> Task Breakdown"
status: "draft" # draft | in_progress | completed | ai_reviewed | human_approved | deprecated
owners:
  - { name: "Hanako Suzuki", role: "Tech Lead" }
  - { name: "AI Task Agent", role: "Task Generator" }
inputs:
  spec_path: "specs/XXX_feature_name/spec.md"
  plan_path: "specs/XXX_feature_name/plan.md"
  basic_design_path: "specs/XXX_feature_name/basic_design.md"
related_branches:
  - "feature/xxx_feature_name"
related_artifacts:
  data_model_md: "specs/XXX_feature_name/data-model.md"
  contracts_dir: "specs/XXX_feature_name/contracts/"
ai_agent_config:
  agents: ["Task", "Diff"]
  tools: ["/speckit.code", "/speckit.diff"]
generated_by: "/speckit.tasks"
generated_at: "YYYY-MM-DDTHH:MM:SSZ"
updated_at: "YYYY-MM-DDTHH:MM:SSZ"
---

> Rule-0: このドキュメントの正本は 1つ：`tasks:` YAML。説明文は補助。

# 1. Canonical Tasks (YAML) — Source of Truth
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.1.3"

derived_fields:
  counts_are_computed: true
  computed_by: "CI/speckit-lint"
  human_edit: "forbidden"

tasks:
  - id: "T-G01-001"
    title: ""
    group: "G-01-core-lib"
    phase: "Phase-1"
    type: "feature"           # feature | test | infra | doc | spike
    priority: "P1"            # P0/P1/P2/P3
    parallel: true
    depends_on: []
    spec_refs: ["US-FEATXXX-001", "AC-US-FEATXXX-001-01"]
    plan_refs: ["LIB-01", "CT-API-01", "TS-INT-01", "Phase-1", "G-01-core-lib"]  # stable IDs only
    owner: "unassigned"       # human or ai-agent
    status: "todo"            # todo | in_progress | blocked | done | dropped
    tags: ["core"]
    estimated_effort: "4h"
    definition_of_done:
      - ""
    notes: ""

milestones:
  - id: "M-01"
    title: ""
    task_ids: ["T-G01-001"]
    gate_passed: false

risks:
  - id: "R-001"
    text: ""
    impact: ""
    mitigation: ""
    blocked_tasks: []

tasks_gate_check:
  counts:
    tasks: 0
    use_cases_referenced: 0
    acceptance_referenced: 0
    tasks_with_plan_refs: 0
    dependency_edges: 0
    milestones: 0
  rules:
    min_tasks: 1
    min_use_cases_referenced: 1
    min_acceptance_referenced: 1
    all_tasks_must_have_plan_refs: true
    no_dependency_cycles: true
  all_us_covered: false
  all_ac_tested: false
  groups_mapped: false
  no_dependency_errors: true
  constitution_aligned: false
  tasks_ready_for_code: false
```

# 2. Minimal Human Notes（任意）

* 調整事項:
* ブロッカー:

> End of tasks.md