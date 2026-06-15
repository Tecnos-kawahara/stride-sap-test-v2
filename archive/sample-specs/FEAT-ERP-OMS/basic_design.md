---
artifact: "basic_design"
template_id: "TPL-BD-TECNOS-001"
feature_id: "FEAT-ERP-OMS"
basic_design_id: "BD-SAMPLE-001"
title: "Basic Design - mcframe受注管理アドオン"
version: "4.3.0-tecnos-stride"
status: "approved"
owners:
  - { name: "田中太郎", role: "Product Owner / Business" }
  - { name: "鈴木次郎", role: "Tech Lead / Architect" }
  - { name: "佐藤三郎", role: "PMO (TEIM)" }
reviewers:
  - { name: "高橋花子", role: "Quality (QA Lead)" }
  - { name: "渡辺五郎", role: "Security Lead" }
  - { name: "伊藤六郎", role: "ERP/Integration Lead" }
links:
  org_constraints_ref: "memory/tecnos_org_constraints.md"
  artifact_registry_ref: "memory/artifact_registry.md"
  ai_policy_ref: "memory/tecnos_org_constraints.md#6.3"
  raci_plus_ref: "memory/tecnos_org_constraints.md#6.4"
  process_bpmn_ref: "specs/sample_erp_addon/process.bpmn"
  spec_md_ref: "specs/sample_erp_addon/spec.md"
  plan_md_ref: "specs/sample_erp_addon/plan.md"
  tasks_md_ref: "specs/sample_erp_addon/tasks.md"
  constitution_ref: "memory/constitution.md"
created_at: "2026-02-01"
updated_at: "2026-02-10"
---

> **Rule-0**: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "4.3.0-tecnos-stride"

basic_design:
  epic_ref: "EPIC-SAMPLE"
  team_id: "TEAM-SALES"
  coverage_tier: "standard"
  autonomy_bias: "balanced"
  security_sensitive: true
  erp_integration: true

  # Execution Profile: ERP Addon → STRIDE enforcement enabled
  execution_profile: erp_addon

  organization:
    company: "Tecnos Japan"
    strategy_alignment:
      mid_term_plan: "2027-2032"
      target_state: "手動受注 → mcframe連携自動受注"
    program_ref:
      portfolio_items: ["2-11"]
    delivery_methods:
      - "TEIM"
    ai_governance:
      guideline_ref: "AI Guidelines v6 (ISO/IEC 42001 series)"
      policy_ref: "memory/tecnos_org_constraints.md#6.3"
      human_in_the_loop: true
      provenance_required: true

  delivery_model:
    type: "requirements-driven"
    rationale: "既存mcframeシステムへのアドオンのため、要件駆動で進行"
    ftos_exit_criteria:
      enabled: false
    ddd_policy:
      enabled: false

  raci_plus:
    actors:
      - "TJ_Human_PM(@tanaka)"
      - "TJ_Human_TechLead(@suzuki)"
      - "TJ_AI_CodingAgent"
      - "TJ_CI_Gate"
      - "Customer_BizOwner(@client_yamamoto)"
    rules:
      - "AIはAccountableになれない（Aは人間のみ）"
      - "Merge/Release/GoNoGoはHuman A + CI passが前提"
      - "AI生成物はProvenanceを必須記録"

  context:
    who: "営業部門の受注担当者（約30名）、営業マネージャー（5名）、経理部門"
    what: "mcframe ERPと連携した受注登録・承認ワークフローのWebアドオン"
    why: "現行のExcel＋メール運用では月次締めに3日遅延が発生。自動化で受注リードタイムを50%短縮する"

  business_domain:
    value_chain: "O2C"
    capability: "営業DX / 受注管理"
    domain_objects: ["Order", "OrderItem", "Customer", "Product", "StockAllocation", "ApprovalRecord"]

  scope:
    in:
      - "受注登録画面（新規作成・編集・削除）"
      - "受注承認ワークフロー（金額別3段階）"
      - "mcframe在庫引当API連携"
      - "権限チェック（ロールベース）"
      - "全操作の監査ログ"
    out:
      - "請求書発行（別Feature: FEAT-ERP-INVOICE-001）"
      - "出荷管理（別Feature: FEAT-ERP-SHIP-001）"
      - "マスタメンテナンス（顧客・製品マスタ）"

  systems:
    - system: "mcframe"
      category: "ERP/Manufacturing"
      owner: "伊藤六郎"
      integration_modes: ["API"]
    - system: "受注管理アドオン（本Feature）"
      category: "Web Application"
      owner: "鈴木次郎"
      integration_modes: ["API"]

  database:
    enabled: true
    schema_ref: "specs/sample_erp_addon/contracts/database_schema.yaml"
    dialect: "postgresql"
    sor_tables: ["orders", "order_items", "approval_records", "audit_logs"]
    referenced_tables: ["customers", "products"]
    migration_strategy: "versioned"
    migration_tool: "alembic"

  data_policy:
    contains_personal_data: true
    data_classes: ["Internal", "Confidential"]
    audit_log_required: true
    retention_policy: "7 years (accounting)"

  agentops_policy:
    enabled: true
    allowed_action_categories: ["read", "draft", "propose"]
    production_execute_requires: "human approval"
    provenance_required: true
    evidence_pack_required: true
    kill_switch:
      enabled: true
      conditions: ["unexpected write to mcframe", "policy violation"]

  e2e_policy:
    scope: "critical-user-journeys"
    playwright_mcp:
      enabled: true
      usage: ["explore", "generate_test_skeleton", "reproduce_failure"]
      prohibited_in_ci_gate: true
    ci_gate:
      deterministic: true
      runner: "playwright-test"
    triage_flow:
      categories: ["product_bug", "spec_gap", "test_bug", "flake"]
      feedback_to: ["spec", "plan", "tasks"]

  flow_reference:
    process_bpmn_path: "specs/sample_erp_addon/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  integration_flows:
    - id: "FLOW-001"
      name: "受注登録→在庫引当"
      summary: "受注データ登録後、mcframe在庫引当APIで在庫確保"
      kpi_slo: "受注登録P95<3s / 在庫引当P95<5s"
      e2e_target: true
    - id: "FLOW-002"
      name: "受注承認フロー"
      summary: "金額に応じた3段階承認ワークフロー"
      kpi_slo: "承認レスポンス<1s"
      e2e_target: false

  traceability_rows:
    - rq: { id: "RQ-001", statement: "受注データを登録できること" }
      us: { id: "US-FEATERPOMS-001", title: "受注登録" }
      ac: { id: "AC-US-FEATERPOMS-001-01", statement: "必須項目入力後、登録ボタンで受注データが保存される", tags: ["integration"] }
      bpmn: { id: "BPMN-TASK-001", name: "受注データ入力" }
      contract: { id: "CT-API-01" }
      database: { tables: ["orders", "order_items"], operations: ["INSERT"] }
      test: { id: "TS-INT-01", type: "integration" }
      task: { id: "T-G01-001" }

    - rq: { id: "RQ-002", statement: "受注登録時に確認ダイアログが表示されること" }
      us: { id: "US-FEATERPOMS-001", title: "受注登録" }
      ac: { id: "AC-US-FEATERPOMS-001-02", statement: "登録ボタンクリック時に確認ダイアログが表示される", tags: ["e2e"] }
      bpmn: { id: "BPMN-TASK-001", name: "受注データ入力" }
      contract: { id: "CT-API-01" }
      database: { tables: [], operations: [] }
      test: { id: "TS-E2E-01", type: "e2e" }
      task: { id: "T-G04-002" }

    - rq: { id: "RQ-003", statement: "在庫引当がmcframeと連携されること" }
      us: { id: "US-FEATERPOMS-001", title: "受注登録" }
      ac: { id: "AC-US-FEATERPOMS-001-03", statement: "受注登録時にmcframe在庫引当APIが呼出され、在庫が確保される", tags: ["integration"] }
      bpmn: { id: "BPMN-TASK-002", name: "在庫引当" }
      contract: { id: "CT-API-03" }
      database: { tables: ["orders"], operations: ["UPDATE"] }
      test: { id: "TS-INT-02", type: "integration" }
      task: { id: "T-G03-001" }

    - rq: { id: "RQ-004", statement: "権限に基づく承認フローが動作すること" }
      us: { id: "US-FEATERPOMS-002", title: "受注承認" }
      ac: { id: "AC-US-FEATERPOMS-002-01", statement: "金額100万円以上は部長承認、500万円以上は役員承認が必要", tags: ["security"] }
      bpmn: { id: "BPMN-GW-001", name: "金額判定ゲートウェイ" }
      contract: { id: "CT-API-04" }
      database: { tables: ["approval_records"], operations: ["INSERT"] }
      test: { id: "TS-INT-03", type: "integration" }
      task: { id: "T-G03-002" }

    - rq: { id: "RQ-005", statement: "全操作に監査ログが出力されること" }
      us: { id: "US-FEATERPOMS-002", title: "受注承認" }
      ac: { id: "AC-US-FEATERPOMS-002-02", statement: "受注の作成・更新・削除・承認の全操作が監査ログに記録される", tags: ["ops"] }
      bpmn: { id: "BPMN-TASK-003", name: "監査ログ記録" }
      contract: { id: "CT-API-01" }
      database: { tables: ["audit_logs"], operations: ["INSERT"] }
      test: { id: "TS-INT-04", type: "integration" }
      task: { id: "T-G02-001" }

  open_questions: []
  assumptions:
    - id: "A-001"
      assumption: "mcframe在庫引当APIは既存エンドポイント /api/v2/stock/allocate を使用"
      rationale: "mcframe開発チームとの事前調整済み（2026-01-25 MTG議事録参照）"
      risk_if_false: "APIバージョンが異なる場合、契約再定義が必要（+1週間）"
    - id: "A-002"
      assumption: "同時受注登録は最大10件/秒を想定"
      rationale: "過去1年の営業部門の受注件数から推定"
      risk_if_false: "DB接続プール/キューイング設計の追加が必要"

  decisions:
    - id: "DR-001"
      context: "受注データの保存先"
      options: ["mcframe本体DB直結", "アドオン専用DB + API連携"]
      decision: "アドオン専用DB + API連携"
      consequences: "データ二重管理リスクあり。定期同期バッチで整合性担保"
    - id: "DR-002"
      context: "承認フローの実装方式"
      options: ["ワークフローエンジン（Temporal/Camunda）", "状態マシン自前実装"]
      decision: "状態マシン自前実装"
      consequences: "シンプルだが複雑な承認ルート追加時に改修コスト増"

  exceptions: []
```

---

# 2. Traceability

| RQ | US | AC | Tags | BPMN | Contract | Database | Test | Task |
|---|---|---|---|---|---|---|---|---|
| RQ-001 | US-FEATERPOMS-001 | AC-US-FEATERPOMS-001-01 | integration | BPMN-TASK-001 | CT-API-01 | orders, order_items (INSERT) | TS-INT-01 | T-G01-001 |
| RQ-002 | US-FEATERPOMS-001 | AC-US-FEATERPOMS-001-02 | e2e | BPMN-TASK-001 | CT-API-01 | - | TS-E2E-01 | T-G04-002 |
| RQ-003 | US-FEATERPOMS-001 | AC-US-FEATERPOMS-001-03 | integration | BPMN-TASK-002 | CT-API-03 | orders (UPDATE) | TS-INT-02 | T-G03-001 |
| RQ-004 | US-FEATERPOMS-002 | AC-US-FEATERPOMS-002-01 | security | BPMN-GW-001 | CT-API-04 | approval_records (INSERT) | TS-INT-03 | T-G03-002 |
| RQ-005 | US-FEATERPOMS-002 | AC-US-FEATERPOMS-002-02 | ops | BPMN-TASK-003 | CT-API-01 | audit_logs (INSERT) | TS-INT-04 | T-G02-001 |

---

# 3. Part A. WHAT/WHY Summary

- **Who**: 営業部門の受注担当者（約30名）、営業マネージャー（5名）、経理部門
- **What**: mcframe ERPと連携した受注登録・承認ワークフローのWebアドオン
- **Why**: 現行のExcel＋メール運用では月次締めに3日遅延が発生。自動化で受注リードタイムを50%短縮する
- **Goals (In Scope)**: 受注登録画面、承認ワークフロー、mcframe在庫引当連携、権限チェック、監査ログ
- **Non-goals (Out of Scope)**: 請求書発行、出荷管理、マスタメンテナンス
- **Value metric**: 営業DX / 受注管理 による月次締め遅延解消

---

# 4. Part B. HOW Policy

## B.1 境界
- **SoR**: mcframe（受注マスタの正本）/ アドオンDB（ワークフロー状態・監査ログ）
- **統合モード**: mcframe API (REST)
- **直接DB連携**: なし（API経由のみ）

## B.2 契約
- CT-API-01: 受注登録API (POST /api/orders)
- CT-API-02: 受注一覧API (GET /api/orders)
- CT-API-03: mcframe在庫引当連携 (POST /api/mcframe/stock-allocation)
- CT-API-04: 権限チェックAPI (GET /api/auth/permissions)

## B.3 テスト戦略
- **Contract tests (TS-CON-*)**: 全CTをカバー
- **Integration tests (TS-INT-*)**: mcframe連携を含む統合テスト
- **E2E tests (TS-E2E-*)**: 受注登録の重要ユーザージャーニー
- **Security tests (TS-SEC-*)**: 権限チェック・監査ログ

## B.4 Ops / Audit
- **監査ログ**: 必須（全操作記録、7年保持）
- **データ分類**: Internal, Confidential
- **SoD**: 受注登録者と承認者は別人

---

# 7. Checks

## 7.1 Human Review Checklist
- [x] Traceability に重大な欠落がない
- [x] 未確定事項が明示され、推測で埋めていない
- [x] Integration critical flow が明確（KPI/SLO含む）
- [x] 監査・SoD・運用の最低要件が触れられている
- [x] 例外は reason/mitigation がセット
- [x] Delivery Modelが決まっている
- [x] RACI+が定義されている
- [x] AI Policyが明示されている

## 7.2 Machine-readable Gate（basic_design_gate_check）
```yaml
basic_design_gate_check:
  id_conventions_ref: "memory/artifact_registry.md"
  id_conventions_version: "v4.3"
  counts:
    traceability_rows: 5
    integration_flows: 2
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0
  traceability_present: true
  integration_flows_identified: true
  exceptions_documented: true
  delivery_model_defined: true
  raci_plus_defined: true
  ai_policy_defined: true
  artifact_registry_defined: true
  ready_for_bpmn: true
  process_bpmn_linked: true
  process_bpmn_approved: true
  ready_for_specify: true
```
