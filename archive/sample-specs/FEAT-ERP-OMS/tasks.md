---
artifact: "tasks"
template_id: "TPL-TASKS-TECNOS-001"
feature_id: "FEAT-ERP-OMS"
tasks_id: "TASKS-SAMPLE-001"
version: "4.3.0-tecnos-stride"
title: "mcframe受注管理アドオン Task Breakdown"
status: "approved"
owners:
  - { name: "鈴木次郎", role: "Tech Lead" }
created_at: "2026-02-02"
updated_at: "2026-02-08"
---

# 1. Canonical Tasks (YAML)
```yaml
tasks_gate_check:
  counts:
    tasks: 11
    use_cases_referenced: 2
    acceptance_referenced: 5
    tasks_with_plan_refs: 11
    dependency_edges: 10
    milestones: 3
  rules:
    min_tasks: 5
    min_use_cases_referenced: 1
    min_acceptance_referenced: 1
  all_us_covered: true
  all_ac_tested: true
  groups_mapped: true
  no_dependency_errors: true
  constitution_aligned: true
  tasks_ready_for_code: true

tasks:
  tasks:
    # Phase-1: Contracts & Test Skeleton
    - id: "T-G01-001"
      title: "受注API契約定義 (CT-API-01, CT-API-02)"
      type: "contract"
      description: "OpenAPI仕様で受注登録・一覧APIを定義"
      spec_refs: ["US-FEATERPOMS-001", "AC-US-FEATERPOMS-001-01"]
      plan_refs: ["CT-API-01", "CT-API-02", "G-01-contracts", "Phase-1"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: []
      outputs: ["specs/sample_erp_addon/contracts/api.yaml"]
      done_when:
        - "OpenAPI仕様がレビュー可能"
        - "stride-lint passes"

    - id: "T-G01-002"
      title: "mcframe連携契約定義 (CT-API-03)"
      type: "contract"
      description: "mcframe在庫引当APIとの連携契約をOpenAPIで定義"
      spec_refs: ["AC-US-FEATERPOMS-001-03"]
      plan_refs: ["CT-API-03", "G-01-contracts", "Phase-1"]
      bpmn_refs: ["BPMN-TASK-002"]
      depends_on: []
      outputs: ["specs/sample_erp_addon/contracts/api.yaml"]
      done_when:
        - "mcframe APIとのインタフェース仕様が確定"

    - id: "T-G01-003"
      title: "権限チェック契約定義 (CT-API-04)"
      type: "contract"
      description: "権限チェックAPIの契約とRBAC定義"
      spec_refs: ["US-FEATERPOMS-002", "AC-US-FEATERPOMS-002-01"]
      plan_refs: ["CT-API-04", "G-01-contracts", "Phase-1"]
      bpmn_refs: ["BPMN-GW-001"]
      depends_on: []
      outputs: ["specs/sample_erp_addon/contracts/api.yaml", "specs/sample_erp_addon/implementation-details/authz_matrix.yaml"]
      done_when:
        - "権限マトリクスが定義済み"
        - "承認閾値（100万/500万）が契約に明記"

    - id: "T-G01-004"
      title: "DB スキーマ定義 (CT-DB-01〜04)"
      type: "contract"
      description: "orders, order_items, approval_records, audit_logs テーブル設計"
      spec_refs: ["AC-US-FEATERPOMS-001-01", "AC-US-FEATERPOMS-002-02"]
      plan_refs: ["CT-DB-01", "CT-DB-02", "CT-DB-03", "CT-DB-04", "G-01-contracts"]
      depends_on: []
      outputs: ["specs/sample_erp_addon/contracts/database_schema.yaml"]
      done_when:
        - "全テーブルにcreated_at, updated_at, created_by, updated_by"
        - "audit_logsにuser_id, action, timestamp, target_id"

    - id: "T-G01-005"
      title: "契約テスト作成 (TS-CON-01〜04)"
      type: "test"
      description: "全CT（API×4, DB×4）の契約テスト"
      spec_refs: ["AC-US-FEATERPOMS-001-01", "AC-US-FEATERPOMS-001-03", "AC-US-FEATERPOMS-002-01"]
      plan_refs: ["TS-CON-01", "TS-CON-02", "TS-CON-03", "TS-CON-04", "G-01-contracts"]
      depends_on: ["T-G01-001", "T-G01-002", "T-G01-003", "T-G01-004"]
      outputs: ["specs/sample_erp_addon/tests/contract/"]
      done_when:
        - "全8CT（CT-API-01~04, CT-DB-01~04）がTS-CON-*でカバー"
        - "stride-lint CONTRACT_COVERAGE_COMPLETE"

    # Phase-1: Security/Ops Baseline
    - id: "T-G02-001"
      title: "監査ログ・SoD基盤定義"
      type: "ops"
      description: "監査ログ出力仕様、SoD（登録者≠承認者）ルール定義"
      spec_refs: ["AC-US-FEATERPOMS-002-02"]
      plan_refs: ["G-02-security-ops", "Phase-1"]
      depends_on: ["T-G01-001"]
      outputs: ["specs/sample_erp_addon/implementation-details/"]
      done_when:
        - "監査ログの出力項目・保持期間が明記"
        - "SoDルールが文書化"

    - id: "T-G02-002"
      title: "Evidence Pack定義"
      type: "ops"
      description: "CI/テスト/カバレッジ/AIプロヴェナンスの証跡定義"
      spec_refs: []
      plan_refs: ["G-02-security-ops", "Phase-1"]
      depends_on: ["T-G02-001"]
      outputs: ["specs/sample_erp_addon/implementation-details/evidence_pack.md"]
      done_when:
        - "必須証跡が列挙されている"

    # Phase-2: Integration & E2E
    - id: "T-G03-001"
      title: "受注登録→mcframe統合テスト (TS-INT-01, TS-INT-02)"
      type: "test"
      description: "受注登録→DB保存→mcframe在庫引当の統合テスト"
      spec_refs: ["AC-US-FEATERPOMS-001-01", "AC-US-FEATERPOMS-001-03"]
      plan_refs: ["TS-INT-01", "TS-INT-02", "G-03-integration-tests", "Phase-2"]
      depends_on: ["T-G02-001"]
      outputs: ["specs/sample_erp_addon/tests/integration/"]
      done_when:
        - "mcframeモック/サンドボックスでテスト成功"
        - "integrationタグ付きACがカバーされている"

    - id: "T-G03-002"
      title: "承認フロー・権限テスト (TS-INT-03, TS-INT-04)"
      type: "test"
      description: "金額別承認分岐と監査ログ出力のテスト"
      spec_refs: ["AC-US-FEATERPOMS-002-01", "AC-US-FEATERPOMS-002-02"]
      plan_refs: ["TS-INT-03", "TS-INT-04", "G-03-integration-tests"]
      depends_on: ["T-G02-001"]
      outputs: ["specs/sample_erp_addon/tests/integration/"]
      done_when:
        - "3段階承認の分岐が全パターンテスト済み"
        - "監査ログに必須項目が出力されている"

    - id: "T-G04-001"
      title: "E2Eテスト基盤セットアップ"
      type: "test"
      description: "Playwright E2E環境構築とレポート設定"
      spec_refs: []
      plan_refs: ["TS-E2E-01", "G-04-e2e-tests", "Phase-2"]
      depends_on: ["T-G03-001"]
      outputs: ["specs/sample_erp_addon/tests/e2e/"]
      done_when:
        - "E2EテストがCI/ローカル両方で実行可能"

    - id: "T-G04-002"
      title: "受注登録E2Eスモークテスト (TS-E2E-01)"
      type: "test"
      description: "受注登録→確認ダイアログ→保存のE2Eテスト"
      spec_refs: ["AC-US-FEATERPOMS-001-02"]
      plan_refs: ["TS-E2E-01", "G-04-e2e-tests", "Phase-2"]
      depends_on: ["T-G04-001"]
      outputs: ["specs/sample_erp_addon/tests/e2e/"]
      done_when:
        - "確認ダイアログのE2Eテストが安定動作"
        - "e2eタグ付きACがカバーされている"

  milestones:
    - id: "M-01"
      name: "Contracts ready"
      exit_criteria: ["全CT定義済み", "契約テスト存在"]
      related_task_ids: ["T-G01-001", "T-G01-002", "T-G01-003", "T-G01-004", "T-G01-005"]
    - id: "M-02"
      name: "Integration test runnable"
      exit_criteria: ["統合テスト成功", "mcframe連携テスト成功"]
      related_task_ids: ["T-G03-001", "T-G03-002"]
    - id: "M-03"
      name: "E2E smoke runnable"
      exit_criteria: ["E2Eテスト安定動作"]
      related_task_ids: ["T-G04-001", "T-G04-002"]
```
