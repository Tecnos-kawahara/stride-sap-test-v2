---
artifact: "plan"
template_id: "TPL-PLAN-TECNOS-001"
feature_id: "FEAT-XXX"
plan_id: "PLAN-XXX"
version: "{{TEMPLATE_VERSION}}"
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
> SAP: テストシナリオは scenarios_template.yaml（tests/ 配下）で管理する。plan 内の test_scenarios は使用しない。

# 0. Canonical Plan (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

derived_fields:
  counts_are_computed: true
  counts:
    in_use_cases: 0
    libraries: 0
    contracts: 0
    tests: 0
    contract_tests: 0
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
    contract_tests: 0
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
  evidence_pack_defined: false
  ai_tasks_ready: false

plan:
  inputs:
    spec_path: "specs/XXX_feature_name/spec.md"
    basic_design_path: "specs/XXX_feature_name/basic_design.md"
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    constitution_path: "memory/constitution.md"
    org_constraints_path: "memory/tecnos_org_constraints.md"

  tecnos_context:
    delivery_method: "TEIM"
    target_domains: []  # 例: ["ERP", "SCM", "CRM"]

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

  # ─────────────────────────────────────────────────────
  # SAP コンポーネント一覧（開発オブジェクト → タスク対応）
  # ─────────────────────────────────────────────────────
  sap_components:
    - object_type: "PROG"        # PROG / CLAS / INTF / FUGR / TABL / DTEL 等
      object_name: ""
      task_ref: ""               # TASK-XXX 参照
      dependency: []             # 依存先オブジェクト名

  # ─────────────────────────────────────────────────────
  # 移送戦略（移送順序、依存関係）
  # ─────────────────────────────────────────────────────
  transport_strategy:
    sequence:
      - order: 1
        objects: ["TABL", "DTEL", "DOMA"]
        reason: "データ辞書オブジェクトが先"
      - order: 2
        objects: ["PROG", "FUGR", "CLAS"]
        reason: "プログラムオブジェクトが後"

  # ─────────────────────────────────────────────────────
  # パス分析（正常系・異常系・AI 判断）
  # 転記元: phase2_specify.md — spec.md の AC/シナリオから導出
  # ─────────────────────────────────────────────────────
  path_analysis:
    normal_paths:
      - path_id: ""             # PATH-N-001 等
        description: ""         # 正常パスの説明
        steps: []               # ステップ列（自然言語）
    abnormal_paths:
      - path_id: ""             # PATH-A-001 等
        description: ""         # 異常パスの説明
        trigger: ""             # 異常発生条件
        recovery: ""            # リカバリ方法
    ai_decisions:
      - decision_id: ""         # AI-D-001 等
        context: ""             # AI が判断を求められる場面
        rule: ""                # 判断ルール

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

    # データベース契約（任意）
    database:
      enabled: false  # false の場合は省略可
      schema_ref: "specs/XXX_feature_name/contracts/database_schema.yaml"
      tables: []
      # - id: "CT-DB-01"
      #   name: ""           # テーブル名
      #   purpose: ""
      #   sor: true          # System of Record（このfeatureがマスタか）
      #   operations: ["SELECT", "INSERT", "UPDATE", "DELETE"]
      #   owner_component: "CMP-01"
      #   audit_notes: ""    # 監査・SoD観点のメモ

    # ─────────────────────────────────────────────────────
    # ファイル契約（SAP 帳票・データ出力等）
    # stride_lint 独立セクション読み取り対応
    # ─────────────────────────────────────────────────────
    file:
      - id: "CT-FILE-01"
        name: ""
        purpose: ""
        format: ""                # csv / tsv / fixed / excel / xml / json
        direction: "outbound"     # inbound / outbound
        owner_component: ""       # CMP-XX 参照
        audit_notes: ""

  # ─────────────────────────────────────────────────────
  # 選択画面フィールド定義
  # AS CHECKBOX パラメータには type: "checkbox" を必須とする（IMP-037）
  # evidence_capture.js が type を読んで GUI 要素 ID（chkXXX / ctxtXXX）を切り替えるため必須
  # ─────────────────────────────────────────────────────
  selection_fields:
    - name: ""
      technical_name: ""          # SAP 技術名（例: P_BUKRS）
      type: ""                    # parameter / select_option / checkbox
      data_element: ""
      required: false

  test_strategy:
    principles:
      - "Contract-first"
      - "Integration-first"
      - "Trace AC-* to TS-*"
      - "Prefer realistic env (ERP sandbox) when possible"
      - "E2E is smoke/regression for e2e-tagged AC only"
      - "Deterministic CI gate (no exploratory agent in gate)"
      - "MCP is for generate/triage/reproduce only"

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

    tooling:
      e2e_runner: "playwright-test"
      playwright_mcp:
        enabled: true
        usage: ["explore", "generate_test_skeleton", "reproduce_failure", "triage_report"]
        prohibited_in_ci_gate: true

      language_runners:
        typescript:
          enabled: false
          unit_runner: "vitest"
          unit_config: "vitest.config.ts"
          coverage_tool: "istanbul-v8"
          mock_framework: "vitest-mocks"
          dom_testing: "@testing-library/react"
          coverage_targets:
            line_pct: 80
            branch_pct: 70
        python:
          enabled: false
          unit_runner: "pytest"
          unit_config: "pyproject.toml"
          coverage_tool: "pytest-cov"
          async_client: "httpx"
          fixtures: "pytest-fixtures"
          coverage_targets:
            line_pct: 80
            branch_pct: 70
        rust:
          enabled: false
          unit_runner: "cargo-test"
          unit_config: "Cargo.toml"
          coverage_tool: "cargo-tarpaulin"
          mock_framework: "mockall"
          property_test: "proptest"
          coverage_targets:
            line_pct: 80
            branch_pct: 70
        java:
          enabled: false
          unit_runner: "junit5"
          build_tool: "gradle"
          unit_config: "build.gradle.kts"
          coverage_tool: "jacoco"
          mock_framework: "mockito"
          assertion_lib: "assertj"
          container_test: "testcontainers"
          arch_test: "archunit"
          static_analysis: ["spotbugs", "checkstyle", "pmd"]
          sca: "dependency-check"
          coverage_targets:
            line_pct: 80
            branch_pct: 70
        go:
          enabled: false
          unit_runner: "go-test"
          unit_config: "go.mod"
          coverage_tool: "go-cover"
          mock_framework: "gomock"
          lint: "golangci-lint"
          race_detection: true
          fuzz: "go-fuzz"
          sca: "govulncheck"
          coverage_targets:
            line_pct: 80
            branch_pct: 70

      cross_language_contracts:
        enabled: false
        tools:
          - type: "openapi"
            schema_path: "contracts/openapi.yaml"
            validation: "schemathesis"
          - type: "pact"
            contracts_dir: "contracts/pacts/"
            broker_url: ""

    reporting:
      e2e:
        html_report: true
        junit_xml: true
        trace: "on-first-retry"
        screenshot: "only-on-failure"
        video: "retain-on-failure"
        artifacts_dir: "specs/XXX_feature_name/tests/reports/e2e/"

    evidence_pack:
      required_artifacts:
        - "ci_results"
        - "test_reports"
        - "sast"
        - "sca"
        - "secrets_scan"
        - "ai_provenance"
      storage:
        path: "specs/XXX_feature_name/implementation-details/evidence_pack.md"
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
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

      - id: "TS-INT-01"
        type: "integration"
        scope: ""
        covers_acceptance_ids: ["AC-US-FEATXXX-001-01"]
        covers_contract_ids: ["CT-API-01"]
        covers_bpmn_element_ids: ["BPMN-TASK-001"]

      - id: "TS-E2E-01"
        type: "e2e"
        scope: "critical-smoke"
        covers_acceptance_ids: ["AC-US-FEATXXX-001-02"]
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
- Evidence Pack: CI/SAST/SCA/Secrets/AIプロヴェナンスを保存
- SAP: sap_components でオブジェクト→タスク対応、transport_strategy で移送順序を定義
- SAP: selection_fields[].type で選択画面フィールド型を宣言（checkbox/parameter/select_option）
- SAP: contracts.file でファイル出力契約を定義
- SAP: テストシナリオは scenarios_template.yaml（tests/ 配下）で管理
- Next step: set `plan_gate_check.ai_tasks_ready: true` then run `/stride.tasks`

> End of plan.md
