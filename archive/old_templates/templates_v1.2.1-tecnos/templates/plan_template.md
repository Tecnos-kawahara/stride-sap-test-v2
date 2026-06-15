---
artifact: "plan"
template_id: "TPL-PLAN-TECNOS-001"
feature_id: "FEAT-XXX"
plan_id: "PLAN-XXX"
version: "1.2.1-tecnos"
title: "<Feature Name> Implementation Plan"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Tech Lead>", role: "Tech Lead / Architect" }
  - { name: "AI Plan Agent", role: "Plan Generator" }
inputs:
  spec_path: "specs/XXX_feature_name/spec.md"
  basic_design_path: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
  constitution_path: "memory/constitution.md"
  org_constraints_path: "memory/tecnos_org_constraints.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Plan (YAML)**。説明文は補助。
> Rule-1: コードは書かない（Planは判断・分解・順序）。コード片は implementation-details/ に退避。
> Tecnos: ERP/SCM/CRM統合の最低要件（監査/SoD/運用）を Plan の contracts/test/ops に落とす。
> v1.2.1: Coverage Policy（AC/CT/Code）、E2E Tooling/Reporting、AgentOps Loop を定義。

# 0. Canonical Plan (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.1-tecnos"

derived_fields:
  counts_are_computed: true
  counts:
    in_use_cases: 0
    libraries: 0
    contracts: 0
    tests: 0
    integration_tests: 0
    e2e_tests: 0
    groups: 0
    exception_items: 0

plan_gate_check:
  counts:
    in_use_cases: 0
    libraries: 0
    contracts: 0
    tests: 0
    integration_tests: 0
    e2e_tests: 0
    groups: 0
    exception_items: 0
  rules:
    min_in_use_cases: 1
    min_libraries: 1
    min_contracts: 1
    min_tests: 2
    min_integration_tests: 1
    min_groups: 3

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
    org_constraints_path: "memory/tecnos_org_constraints.md"

  tecnos_context:
    delivery_method: "TEIM 6×6"
    target_domains: ["ERP", "SCM", "CRM", "CBP"]

  scope:
    in_use_cases: ["US-FEATXXX-001"]
    out_of_scope: []

  flow_mapping:
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"
    groups_to_bpmn:
      - group_id: "G-01-contracts"
        bpmn_refs: ["BPMN-TASK-001"]

  integration_standards:
    correlation_id: "required"
    idempotency: "required for inbound integrations"
    retry_timeout_policy: "define per contract"
    audit_log: "required for critical operations"
    sod: "define approver/executor separation where applicable"

  architecture:
    components:
      - id: "CMP-01"
        name: ""
        responsibility: ""
        boundaries: ""  # 例: "ERP境界は契約越しのみ"

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
        kind: "api"       # api | event | file | batch | edi | idoc
        direction: "inbound" # inbound | outbound | bidirectional
        target_system: ""   # 例: "SAP" / "mcframe" / "Salesforce"
        protocol: ""        # 例: "REST" / "OData" / "IDoc" / "SFTP"
        data_format: ""     # 例: "JSON" / "CSV" / "XML"
        purpose: ""
        versioning: "semver"
        owner_component: "CMP-01"
        audit_notes: ""     # 監査・SoD観点のメモ（詳細はcontracts/へ）

  test_strategy:
    principles:
      - "Contract-first"
      - "Integration-first"
      - "Trace AC-* to TS-*"
      - "Prefer realistic env (ERP sandbox) when possible"
      - "E2E is smoke/regression for e2e-tagged AC only"
      - "Deterministic CI gate (no exploratory agent in gate)"
      - "MCP is for generate/triage/reproduce only"

    # v1.2.1: Coverage Policy（3層モデル）
    coverage_policy:
      # Layer-1: Spec Coverage（AC coverage）- 必須
      acceptance_coverage_required: true
      acceptance_coverage_target_pct: 100

      # Tagged AC enforcement
      tagged_acceptance_requirements:
        integration:
          enforce: true
          required_test_type: "integration"  # TS-INT-* でカバー
        e2e:
          enforce: true
          required_test_type: "e2e"          # TS-E2E-* でカバー

      # Layer-2: Contract Coverage（CT coverage）- 原則必須
      contract_coverage_required: true
      contract_coverage_target_pct: 100

      # Layer-3: Code Coverage（目標＋例外）
      code_coverage_targets:
        - scope: "LIB-*"
          line_pct: 85
          branch_pct: 75
        - scope: "CMP-*"
          line_pct: 60
          branch_pct: 50
      code_coverage_exclusions:
        - path_glob: "**/generated/**"
          reason: "Generated code"
          mitigation: "Contract/Integration tests cover behavior"

      # Planning discipline
      tests_must_be_tasked: true

      # AgentOps / CI gate policy
      ci_gate_is_deterministic: true
      allow_exploratory_agent_in_ci_gate: false

    # v1.2.1: E2E Tooling（Playwright MCP / Test）
    tooling:
      e2e_runner: "playwright-test"
      playwright_mcp:
        enabled: true
        usage: ["explore", "generate_test_skeleton", "reproduce_failure", "triage_report"]
        prohibited_in_ci_gate: true

    # v1.2.1: E2E Reporting（成果物定義）
    reporting:
      e2e:
        html_report: true
        junit_xml: true
        trace: "on-first-retry"        # always | on-first-retry | retain-on-failure
        screenshot: "only-on-failure"  # always | only-on-failure | off
        video: "retain-on-failure"     # on | retain-on-failure | off
        artifacts_dir: "specs/XXX_feature_name/tests/reports/e2e/"

    tests:
      - id: "TS-CON-01"
        type: "contract"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]
        covers_contract_ids: ["CT-API-01"]              # v1.2.1: CT→TSの紐付け
        covers_bpmn_element_ids: ["BPMN-TASK-001"]      # 任意（BPMNトレース強化）

      - id: "TS-INT-01"
        type: "integration"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]  # integrationタグ付きAC
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

      - id: "TS-E2E-01"
        type: "e2e"
        scope: "critical-smoke"
        covers_acceptance_ids: ["AC-US-FEATXXX-001-02"]  # e2eタグ付きAC
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

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

        - id: "G-02-security-ops"
          name: "Security/Ops baseline"
          objective: "監査・SoD・運用の最低要件をPlan/Tasksへ落とす"
          deliverables:
            - "specs/XXX_feature_name/implementation-details/ops.md"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01"]
            tests: []
            phases: ["Phase-1"]
            groups: ["G-02-security-ops"]
          bpmn_refs: []
          depends_on_groups: ["G-01-contracts"]

    - id: "Phase-2"
      name: "Integration & E2E"
      objective: ""
      groups:
        - id: "G-03-integration-tests"
          name: "Integration tests"
          objective: "統合テスト（TS-INT-*）を整備し、integrationタグ付きACをカバーする"
          deliverables:
            - "specs/XXX_feature_name/tests/integration/"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01"]
            tests: ["TS-INT-01"]
            phases: ["Phase-2"]
            groups: ["G-03-integration-tests"]
          bpmn_refs: ["BPMN-TASK-001"]
          depends_on_groups: ["G-02-security-ops"]

        - id: "G-04-e2e-tests"
          name: "E2E smoke tests (Playwright)"
          objective: "重要ユーザージャーニー（e2eタグAC）の回帰を、決定論的なE2Eで担保する"
          deliverables:
            - "specs/XXX_feature_name/tests/e2e/"
            - "specs/XXX_feature_name/tests/reports/e2e/"
            - "specs/XXX_feature_name/implementation-details/e2e-triage.md"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01"]
            tests: ["TS-E2E-01"]
            phases: ["Phase-2"]
            groups: ["G-04-e2e-tests"]
          bpmn_refs: ["BPMN-TASK-001"]
          depends_on_groups: ["G-03-integration-tests"]

  risks:
    - id: "R-001"
      risk: ""
      impact: ""
      mitigation: ""

  exceptions: []
  # - article: "VII"
  #   reason: ""
  #   mitigation: ""
```

---

# 1. Human-readable Summary（最小）
- Flow reference: {{ inputs.process_bpmn_path }}
- Org constraints: {{ inputs.org_constraints_path }}
- Coverage Policy: AC=100%, CT=100%, Code=目標＋例外
- E2E runner: Playwright Test（決定論的CI）
- MCP usage: 探索/生成/再現/triage（CIゲート外）
- Next step: set `plan_gate_check.ai_tasks_ready: true` then run `/speckit.tasks`

> End of plan.md
