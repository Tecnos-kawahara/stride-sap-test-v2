---
artifact: "plan"
template_id: "TPL-PLAN-TECNOS-001"
feature_id: "FEAT-ERP-OMS"
plan_id: "PLAN-SAMPLE-001"
version: "4.3.0-tecnos-stride"
title: "mcframe受注管理アドオン Implementation Plan"
status: "approved"
owners:
  - { name: "鈴木次郎", role: "Tech Lead / Architect" }
inputs:
  spec_path: "specs/sample_erp_addon/spec.md"
  basic_design_path: "specs/sample_erp_addon/basic_design.md"
  process_bpmn_path: "specs/sample_erp_addon/process.bpmn"
created_at: "2026-02-02"
updated_at: "2026-02-08"
---

# 0. Canonical Plan (YAML)
```yaml
plan_gate_check:
  counts:
    in_use_cases: 2
    libraries: 3
    contracts: 8
    tests: 9
    contract_tests: 4
    integration_tests: 4
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
  scope:
    in_use_cases: ["US-FEATERPOMS-001", "US-FEATERPOMS-002"]

  architecture:
    components:
      - id: "CMP-01"
        name: "Order Web UI"
        responsibility: "受注登録・承認画面"
        boundaries: "ブラウザ上で動作、API経由でバックエンドと通信"
      - id: "CMP-02"
        name: "Order API Service"
        responsibility: "受注CRUD、承認ワークフロー、監査ログ"
        boundaries: "REST API、PostgreSQL接続、mcframe API呼出し"
      - id: "CMP-03"
        name: "mcframe Integration"
        responsibility: "在庫引当API呼出し、リトライ処理"
        boundaries: "mcframe APIのみ。直接DB接続禁止"

    libraries:
      - id: "LIB-01"
        name: "order-domain"
        responsibility: "受注ドメインロジック（承認判定、バリデーション）"
        public_interfaces: ["CT-API-01", "CT-API-02"]
        dependencies: []
      - id: "LIB-02"
        name: "authz-lib"
        responsibility: "権限チェック・承認フロー"
        public_interfaces: ["CT-API-04"]
        dependencies: ["LIB-01"]
      - id: "LIB-03"
        name: "mcframe-client"
        responsibility: "mcframe API クライアント（リトライ・タイムアウト管理）"
        public_interfaces: ["CT-API-03"]
        dependencies: []

  contracts:
    apis_events:
      - id: "CT-API-01"
        name: "受注登録API"
        kind: "api"
        direction: "inbound"
        protocol: "REST"
        data_format: "JSON"
        purpose: "受注データの登録"
        owner_component: "CMP-02"
      - id: "CT-API-02"
        name: "受注一覧API"
        kind: "api"
        direction: "inbound"
        protocol: "REST"
        data_format: "JSON"
        purpose: "受注データの取得・検索"
        owner_component: "CMP-02"
      - id: "CT-API-03"
        name: "mcframe在庫引当連携"
        kind: "api"
        direction: "outbound"
        target_system: "mcframe"
        protocol: "REST"
        data_format: "JSON"
        purpose: "在庫引当の実行"
        owner_component: "CMP-03"
        audit_notes: "Correlation ID必須、idempotency key必須"
      - id: "CT-API-04"
        name: "権限チェックAPI"
        kind: "api"
        direction: "inbound"
        protocol: "REST"
        data_format: "JSON"
        purpose: "ロールベース権限検証"
        owner_component: "CMP-02"

    database:
      enabled: true
      schema_ref: "specs/sample_erp_addon/contracts/database_schema.yaml"
      tables:
        - id: "CT-DB-01"
          name: "orders"
          purpose: "受注ヘッダ"
          sor: true
          operations: ["SELECT", "INSERT", "UPDATE"]
        - id: "CT-DB-02"
          name: "order_items"
          purpose: "受注明細"
          sor: true
          operations: ["SELECT", "INSERT", "UPDATE", "DELETE"]
        - id: "CT-DB-03"
          name: "approval_records"
          purpose: "承認履歴"
          sor: true
          operations: ["SELECT", "INSERT"]
        - id: "CT-DB-04"
          name: "audit_logs"
          purpose: "監査ログ"
          sor: true
          operations: ["INSERT", "SELECT"]

  test_strategy:
    coverage_policy:
      acceptance_coverage_required: true
      acceptance_coverage_target_pct: 100
      contract_coverage_required: true
      contract_coverage_target_pct: 100
      code_coverage_targets:
        - scope: "LIB-*"
          line_pct: 85
          branch_pct: 75
        - scope: "CMP-*"
          line_pct: 60
          branch_pct: 50

    tooling:
      language_runners:
        python:
          enabled: true
          unit_runner: "pytest"
          unit_config: "pyproject.toml"
          coverage_tool: "pytest-cov"

    tests:
      - id: "TS-CON-01"
        type: "contract"
        scope: "受注API契約検証（登録・一覧）"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-001-01"]
        covers_contract_ids: ["CT-API-01", "CT-API-02"]
      - id: "TS-CON-02"
        type: "contract"
        scope: "mcframe在庫引当API契約検証"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-001-03"]
        covers_contract_ids: ["CT-API-03"]
      - id: "TS-INT-01"
        type: "integration"
        scope: "受注登録→DB保存の統合テスト"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-001-01"]
        covers_contract_ids: ["CT-API-01", "CT-DB-01", "CT-DB-02"]
      - id: "TS-INT-02"
        type: "integration"
        scope: "受注登録→mcframe在庫引当の統合テスト"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-001-03"]
        covers_contract_ids: ["CT-API-03"]
      - id: "TS-INT-03"
        type: "integration"
        scope: "承認フロー分岐テスト（金額別）"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-002-01"]
        covers_contract_ids: ["CT-API-04", "CT-DB-03"]
      - id: "TS-INT-04"
        type: "integration"
        scope: "監査ログ出力テスト"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-002-02"]
        covers_contract_ids: ["CT-DB-04"]
      - id: "TS-CON-03"
        type: "contract"
        scope: "権限チェックAPI契約検証"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-002-01"]
        covers_contract_ids: ["CT-API-04"]
      - id: "TS-CON-04"
        type: "contract"
        scope: "DBスキーマ契約検証（全テーブル整合性）"
        covers_acceptance_ids: []
        covers_contract_ids: ["CT-DB-01", "CT-DB-02", "CT-DB-03", "CT-DB-04"]
      - id: "TS-E2E-01"
        type: "e2e"
        scope: "受注登録E2Eスモークテスト"
        covers_acceptance_ids: ["AC-US-FEATERPOMS-001-02"]
        covers_contract_ids: ["CT-API-01"]

    evidence_pack:
      required_artifacts:
        - "ci_results"
        - "test_reports"
        - "sast"
        - "sca"
        - "secrets_scan"
        - "ai_provenance"
      storage:
        path: "specs/sample_erp_addon/implementation-details/evidence_pack.md"
      provenance:
        record_model_version: true
        record_prompt_version: true
        record_inputs_hash: true

  phases:
    - id: "Phase-1"
      name: "Contracts & Test Skeleton"
      groups:
        - id: "G-01-contracts"
          name: "契約定義"
          deliverables: ["specs/sample_erp_addon/contracts/"]
          depends_on_groups: []
        - id: "G-02-security-ops"
          name: "セキュリティ・監査基盤"
          deliverables: ["specs/sample_erp_addon/implementation-details/"]
          depends_on_groups: ["G-01-contracts"]
    - id: "Phase-2"
      name: "Integration & E2E"
      groups:
        - id: "G-03-integration-tests"
          name: "統合テスト"
          deliverables: ["specs/sample_erp_addon/tests/integration/"]
          depends_on_groups: ["G-02-security-ops"]
        - id: "G-04-e2e-tests"
          name: "E2Eテスト"
          deliverables: ["specs/sample_erp_addon/tests/e2e/"]
          depends_on_groups: ["G-03-integration-tests"]

  risks:
    - id: "R-001"
      risk: "mcframe APIのバージョン不一致"
      impact: "在庫引当連携が動作しない"
      mitigation: "開発初期にmcframeサンドボックスで契約テスト実施"
    - id: "R-002"
      risk: "同時受注による在庫競合"
      impact: "在庫の二重引当"
      mitigation: "mcframe側のidempotency key + 楽観的ロック"
```

---

# 1. Human-readable Summary
- **Python + FastAPI** ベースのバックエンド
- **PostgreSQL** でアドオン独自データ管理
- **mcframe REST API** で在庫引当連携
- Coverage Policy: AC=100%, CT=100%, Code=LIB 85%/75%, CMP 60%/50%
