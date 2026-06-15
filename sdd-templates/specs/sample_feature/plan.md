---
artifact: "plan"
template_id: "TPL-PLAN-TECNOS-001"
feature_id: "FEAT-001"
plan_id: "PLAN-001"
version: "{{TEMPLATE_VERSION}}"
title: "Web-EDI受注受付 Implementation Plan"
status: "draft" # draft | in_review | approved | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Tech Lead>", role: "Tech Lead / Architect" }
  - { name: "AI Plan Agent", role: "Plan Generator" }
inputs:
  spec_path: "specs/sample_feature/spec.md"
  basic_design_path: "specs/sample_feature/basic_design.md"
  process_bpmn_path: "specs/sample_feature/process.bpmn"
  constitution_path: "memory/constitution.md"
  org_constraints_path: "memory/tecnos_org_constraints.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Plan (YAML)**。説明文は補助。
> Rule-1: コードは書かない（Planは判断・分解・順序）。コード片は implementation-details/ に退避。
> Tecnos: ERP/SCM/CRM統合の最低要件（監査/SoD/運用）を Plan の contracts/test/ops に落とす。
> v1.2.3: Evidence Pack（CI/SAST/SCA/Secrets/AIプロヴェナンス）とSpec-as-Codeの受入条件を追加。

# 0. Canonical Plan (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

derived_fields:
  counts_are_computed: true
  counts:
    in_use_cases: 1
    libraries: 1
    contracts: 1
    tests: 3
    integration_tests: 1
    e2e_tests: 1
    groups: 4
    exception_items: 0

plan_gate_check:
  counts:
    in_use_cases: 1
    libraries: 1
    contracts: 1
    tests: 3
    integration_tests: 1
    e2e_tests: 1
    groups: 4
    exception_items: 0
  rules:
    min_in_use_cases: 1
    min_libraries: 1
    min_contracts: 1
    min_tests: 2
    min_integration_tests: 1
    min_groups: 3

  contracts_defined: true
  tests_prioritized: true
  groups_and_dependencies_defined: true
  simplicity_gate_passed: true
  anti_abstraction_gate_passed: true
  integration_first_gate_passed: true
  evidence_pack_defined: true
  ai_tasks_ready: true

plan:
  inputs:
    spec_path: "specs/sample_feature/spec.md"
    basic_design_path: "specs/sample_feature/basic_design.md"
    process_bpmn_path: "specs/sample_feature/process.bpmn"
    constitution_path: "memory/constitution.md"
    org_constraints_path: "memory/tecnos_org_constraints.md"

  tecnos_context:
    delivery_method: "TEIM"
    target_domains: ["ERP", "B2B"]

  scope:
    in_use_cases: ["US-FEAT001-001"]
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
        name: "WebEdiOrderService"
        responsibility: "受注受付・検証・ERP登録"
        boundaries: "Web-EDI Portal/ERP境界は契約越しのみ"

    libraries:
      - id: "LIB-01"
        name: "OrderValidationLib"
        responsibility: "受注データの検証・変換ロジック"
        public_interfaces: ["CT-API-01"]
        dependencies: []

  contracts:
    cli: []

    apis_events:
      - id: "CT-API-01"
        name: "Web-EDI受注受付API"
        kind: "api"       # api | event | file | batch | edi | idoc
        direction: "inbound" # inbound | outbound | bidirectional
        target_system: "Trading Partner"
        protocol: "REST"
        data_format: "JSON"
        purpose: "取引先からWeb-EDI発注を受け付ける"
        versioning: "semver"
        owner_component: "CMP-01"
        audit_notes: "取引先コード/受注番号をログに記録"

  test_strategy:
    principles:
      - "Contract-first"
      - "Integration-first"
      - "Trace AC-* to TS-*"
      - "Prefer realistic env (ERP sandbox) when possible"
      - "E2E is smoke/regression for e2e-tagged AC only"
      - "Deterministic CI gate (no exploratory agent in gate)"
      - "MCP is for generate/triage/reproduce only"

    # v1.2.3: Coverage Policy（3層モデル）
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

    # v1.2.3: E2E Tooling（Playwright MCP / Test）
    tooling:
      e2e_runner: "playwright-test"
      playwright_mcp:
        enabled: true
        usage: ["explore", "generate_test_skeleton", "reproduce_failure", "triage_report"]
        prohibited_in_ci_gate: true

    # v1.2.3: E2E Reporting（成果物定義）
    reporting:
      e2e:
        html_report: true
        junit_xml: true
        trace: "on-first-retry"        # always | on-first-retry | retain-on-failure
        screenshot: "only-on-failure"  # always | only-on-failure | off
        video: "retain-on-failure"     # on | retain-on-failure | off
        artifacts_dir: "specs/sample_feature/tests/reports/e2e/"

    # v1.2.3: Evidence Pack（ゲート証跡）
    evidence_pack:
      required_artifacts:
        - "ci_results"
        - "test_reports"
        - "sast"
        - "sca"
        - "secrets_scan"
        - "ai_provenance"
      storage:
        path: "specs/sample_feature/implementation-details/evidence_pack.md"
      provenance:
        record_provider_surface: true
        record_model_id: true
        record_model_version: true
        record_prompt_version: true
        record_inputs_hash: true
        record_execution_settings: true
        record_budget_controls: true
        record_tokenizer_notes: true
        record_cyber_safeguards_status: true

    tests:
      - id: "TS-CON-01"
        type: "contract"
        scope: "Web-EDI受注受付API契約検証"
        covers_acceptance_ids: ["AC-US-FEAT001-001-01"]
        covers_contract_ids: ["CT-API-01"]              # v1.2.3: CT→TSの紐付け
        covers_bpmn_element_ids: ["BPMN-TASK-001"]      # 任意（BPMNトレース強化）

      - id: "TS-INT-01"
        type: "integration"
        scope: "Web-EDI→ERP連携テスト"
        covers_acceptance_ids:
          - "AC-US-FEAT001-001-01"  # integrationタグ付きAC
          - "AC-US-FEAT001-001-02"
          - "AC-US-FEAT001-001-03"
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

      - id: "TS-E2E-01"
        type: "e2e"
        scope: "Web-EDI受注受付主要フロー"
        covers_acceptance_ids: ["AC-US-FEAT001-001-02"]  # e2eタグ付きAC
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

  phases:
    - id: "Phase-1"
      name: "Contracts & Test Skeleton"
      objective: "契約定義とテスト骨格を固める"
      groups:
        - id: "G-01-contracts"
          name: "Define contracts"
          objective: "Web-EDI受注受付APIの契約をレビュー可能にする"
          deliverables:
            - "specs/sample_feature/contracts/"
          stable_refs:
            components: ["CMP-01"]
            libraries: ["LIB-01"]
            contracts: ["CT-API-01"]
            tests: ["TS-CON-01"]
            phases: ["Phase-1"]
            groups: ["G-01-contracts"]
          bpmn_refs: ["BPMN-TASK-001"]
          depends_on_groups: []

        - id: "G-02-security-ops"
          name: "Security/Ops baseline"
          objective: "監査・SoD・運用の最低要件をPlan/Tasksへ落とす"
          deliverables:
            - "specs/sample_feature/implementation-details/ops.md"
            - "specs/sample_feature/implementation-details/evidence_pack.md"
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
      objective: "統合/E2Eの品質ゲートを成立させる"
      groups:
        - id: "G-03-integration-tests"
          name: "Integration tests"
          objective: "統合テスト（TS-INT-*）を整備し、integrationタグ付きACをカバーする"
          deliverables:
            - "specs/sample_feature/tests/integration/"
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
            - "specs/sample_feature/tests/e2e/"
            - "specs/sample_feature/tests/reports/e2e/"
            - "specs/sample_feature/implementation-details/e2e-triage.md"
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
      risk: "ERPテスト環境の利用制限により、統合テストが遅延する"
      impact: "TS-INT/TS-E2Eの実行が遅れ、Gate通過が後ろ倒しになる"
      mitigation: "早期にERPサンドボックス枠を確保し、代替としてモック環境を用意する"

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
- Next step: set `plan_gate_check.ai_tasks_ready: true` then run `/stride.tasks`

> End of plan.md
