---
artifact: "spec"
template_id: "TPL-SPEC-TECNOS-001"
feature_id: "FEAT-ERP-OMS"
spec_id: "SPEC-SAMPLE-001"
version: "4.3.0-tecnos-stride"
title: "mcframe受注管理アドオン Specification"
status: "approved"
owners:
  - { name: "田中太郎", role: "Product Owner / Business" }
  - { name: "鈴木次郎", role: "Tech Lead" }
links:
  basic_design_ref: "specs/sample_erp_addon/basic_design.md"
  process_bpmn_ref: "specs/sample_erp_addon/process.bpmn"
  plan_md_ref: "specs/sample_erp_addon/plan.md"
  tasks_md_ref: "specs/sample_erp_addon/tasks.md"
created_at: "2026-02-01"
updated_at: "2026-02-08"
---

# 0. Canonical Spec (YAML)
```yaml
spec_gate_check:
  counts:
    use_cases: 2
    acceptance_criteria: 5
    integration_tagged_ac: 2
    e2e_tagged_ac: 1
    blocking_questions: 0
    nfr_items: 12
    security_items: 2
    integration_items: 3
    data_items: 2
    spec_as_code_artifacts: 4
  rules:
    min_use_cases: 1
    min_total_acceptance_criteria: 3
    min_integration_acceptance_criteria: 1
    max_blocking_questions: 0
    min_nfr_items: 6
    min_security_items: 1
    min_integration_items: 1
    min_data_items: 1
    min_spec_as_code_artifacts: 1
  no_blocking_open_questions: true
  spec_as_code_defined: true
  ai_plan_ready: true

spec:
  overview:
    who: "営業部門の受注担当者・営業マネージャー"
    what: "mcframe連携の受注登録・承認ワークフローWebアドオン"
    why: "Excel運用の月次3日遅延を解消し、受注リードタイム50%短縮"

  business_value:
    kpis: ["受注登録リードタイム -50%", "月次締め遅延 0日", "監査指摘ゼロ"]
    financial_hypotheses:
      revenue_uplift: "受注処理速度向上による機会損失削減"
      cost_reduction: "手作業工数 -200h/月"
      risk_reduction: "監査指摘ゼロ（承認フロー・監査ログ完備）"

  goals:
    - "受注登録から在庫引当まで3秒以内で完了する"
    - "金額に応じた承認フローが自動で分岐する"
    - "全操作が監査ログに記録される"
  non_goals:
    - "請求書発行（FEAT-ERP-INVOICE-001）"
    - "出荷指示（FEAT-ERP-SHIP-001）"

  domain_terms:
    - term: "受注（Order）"
      definition: "顧客からの注文データ。品目・数量・金額・納期を含む"
    - term: "在庫引当（Stock Allocation）"
      definition: "受注に対してmcframe上の在庫を確保する処理"
    - term: "承認フロー（Approval Flow）"
      definition: "受注金額に応じた段階的承認プロセス"

  use_cases:
    - id: "US-FEATERPOMS-001"
      title: "受注登録"
      primary_actor: "受注担当者"
      trigger: "顧客から注文書を受領"
      preconditions:
        - "担当者がログイン済み"
        - "顧客マスタに顧客が登録済み"
      main_flow:
        - "1. 受注登録画面を開く"
        - "2. 顧客・品目・数量・納期を入力"
        - "3. 登録ボタンをクリック"
        - "4. 確認ダイアログで内容確認"
        - "5. 受注データがDBに保存"
        - "6. mcframe在庫引当APIで在庫確保"
        - "7. 成功メッセージ表示"
      alternate_flows:
        - "4a. キャンセル → 入力画面に戻る"
        - "6a. 在庫不足 → 警告表示、受注はPENDING状態で保存"
      postconditions:
        - "受注データがDBに保存されている"
        - "mcframeで在庫が引当済み（在庫十分な場合）"
        - "監査ログが記録されている"
      acceptance:
        - id: "AC-US-FEATERPOMS-001-01"
          statement: "必須項目（顧客ID, 品目コード, 数量, 納期）入力後、登録ボタンで受注データがDB保存される。レスポンスに order_id が含まれる"
          tags: ["integration"]
          priority: "must"
        - id: "AC-US-FEATERPOMS-001-02"
          statement: "登録ボタンクリック時に確認ダイアログが表示され、OKで保存・キャンセルで入力画面に戻る"
          tags: ["e2e"]
          priority: "must"
        - id: "AC-US-FEATERPOMS-001-03"
          statement: "受注登録成功後、mcframe在庫引当API（POST /api/v2/stock/allocate）が呼出され、在庫引当結果がレスポンスに含まれる"
          tags: ["integration"]
          priority: "must"

    - id: "US-FEATERPOMS-002"
      title: "受注承認"
      primary_actor: "営業マネージャー / 部長 / 役員"
      trigger: "受注が登録され、承認待ち状態になる"
      preconditions:
        - "承認者がログイン済み"
        - "受注が承認待ち状態"
      main_flow:
        - "1. 承認待ち一覧を開く"
        - "2. 受注詳細を確認"
        - "3. 承認/却下を選択"
        - "4. 承認記録がDBに保存"
      alternate_flows:
        - "3a. 却下 → 受注担当者に差戻し通知"
      postconditions:
        - "承認記録がDBに保存されている"
        - "受注ステータスが更新されている"
      acceptance:
        - id: "AC-US-FEATERPOMS-002-01"
          statement: "金額100万円未満は自動承認、100万円以上は部長承認、500万円以上は役員承認が必要"
          tags: ["security"]
          priority: "must"
        - id: "AC-US-FEATERPOMS-002-02"
          statement: "受注の作成・更新・削除・承認の全操作が audit_logs テーブルに記録される。各レコードに user_id, action, timestamp, target_id が含まれる"
          tags: ["ops"]
          priority: "must"

  requirements:
    integration:
      - "mcframe API呼出しにはCorrelation IDを付与し、監査ログに記録"
      - "在庫引当APIはidempotency keyで冪等性を確保"
      - "mcframe APIタイムアウトは10秒、3回リトライ"
    data_governance:
      - "受注データはアドオンDBがSoR（mcframeへは非同期同期）"
      - "保持期間: 会計データ7年、監査ログ7年"
    performance:
      - "受注登録API: P95 < 3秒"
      - "在庫引当連携: P95 < 5秒"
      - "同時受注: 10件/秒"
    security_privacy:
      - "ロールベースアクセス制御（RBAC）: admin, manager, operator"
      - "受注登録者と承認者のSoD（職務分掌）"
    operations:
      - "全APIエンドポイントにヘルスチェック"
      - "mcframe連携障害時はPENDING状態で保存し、リトライキューで自動再送"

  spec_as_code:
    artifacts:
      - type: "openapi"
        path: "specs/sample_erp_addon/contracts/api.yaml"
        schema_version: "3.1.0"
        status: "approved"
      - type: "database_schema"
        path: "specs/sample_erp_addon/contracts/database_schema.yaml"
        schema_version: "1.0"
        status: "approved"
      - type: "authz_matrix"
        path: "specs/sample_erp_addon/implementation-details/authz_matrix.yaml"
        schema_version: "1.0"
        status: "approved"
      - type: "test_scenarios"
        path: "specs/sample_erp_addon/tests/scenarios.yaml"
        schema_version: "1.0"
        status: "approved"
```

---

# 1. Human-readable Spec

## 1.1 Goals / Non-goals
- **Goals**: 受注登録3秒以内、承認フロー自動分岐、全操作監査ログ
- **Non-goals**: 請求書発行、出荷管理

## 1.2 Acceptance Criteria

| ID | Statement | Tags | Priority |
|---|---|---|---|
| AC-US-FEATERPOMS-001-01 | 必須項目入力後、登録でDB保存。order_id返却 | integration | must |
| AC-US-FEATERPOMS-001-02 | 確認ダイアログ表示、OK→保存、Cancel→戻る | e2e | must |
| AC-US-FEATERPOMS-001-03 | mcframe在庫引当API連携、引当結果返却 | integration | must |
| AC-US-FEATERPOMS-002-01 | 金額別3段階承認（100万/500万閾値） | security | must |
| AC-US-FEATERPOMS-002-02 | 全操作の監査ログ（user_id, action, timestamp, target_id） | ops | must |
