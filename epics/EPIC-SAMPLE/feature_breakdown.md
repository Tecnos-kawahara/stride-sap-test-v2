# Feature Breakdown: EPIC-SAMPLE

> **Version**: 1.0.0
> **Status**: in_review
> **Last Updated**: 2026-02-15

---

## 0. Canonical Feature Breakdown (YAML)

```yaml
feature_breakdown:
  meta:
    epic_id: "EPIC-SAMPLE"
    breakdown_id: "FBD-SAMPLE"
    version: "1.0.0"
    status: "in_review"  # draft | in_review | approved
    created_at: "2026-02-01"
    updated_at: "2026-02-15"

  decomposition_rationale:
    principles:
      - "Single feature = single team = clear ownership"
      - "Contract-first: API/DB契約をSpec段階で確定"
      - "Work Item分割は責務とリスクプロファイルで決定"
    decisions:
      - decision_id: "FBD-DEC-001"
        description: "受注登録と権限・承認を2つのWork Itemに分割"
        rationale: "受注登録(UI+API)はlow complexity/autopilot、権限はhigh complexity/validate。リスクプロファイルが異なるため別WIとし、独立したmode制御を適用"
        alternatives_considered:
          - "全機能を1つのWork Itemで実装（リスク混在で不適切）"
          - "UI/API/DB層ごとにWI分割（責務横断で追跡困難）"
      - decision_id: "FBD-DEC-002"
        description: "mcframe連携をFeature内部の統合ポイントとして扱い、別Featureにしない"
        rationale: "mcframe在庫引当は受注登録フローの一部。独立したビジネス価値を持たないため、FEAT-ERPSAMPLE内のCT-API-03として管理"
        alternatives_considered:
          - "mcframe連携を独立Feature化（チーム分割不要なので過剰）"

  features:
    - feature_id: "FEAT-ERPSAMPLE"
      name: "mcframe受注管理アドオン"
      team_id: "TEAM-SLS"
      coverage_tier: "critical"
      priority: 1
      scope:
        in:
          - "受注登録REST API（CT-API-01: createOrder）"
          - "受注一覧取得API（CT-API-02: listOrders）"
          - "mcframe在庫引当連携（CT-API-03: allocateStock）"
          - "権限チェック・承認API（CT-API-04: approveOrder, getPermissions）"
          - "確認ダイアログUI（AC-US-FEATERPOMS-001-02）"
          - "金額別3段階承認フロー（auto/manager/admin）"
          - "SoD検証（受注登録者≠承認者）"
          - "全操作の監査ログ（CREATE/UPDATE/DELETE/APPROVE/REJECT）"
        out:
          - "請求書発行（mcframe標準機能）"
          - "入金消込（将来Epic）"
          - "受注分析・レポーティング"
          - "バッチ受注処理"
      contracts_owned:
        - contract_id: "CT-API-01"
          name: "受注登録API"
          type: "api"
        - contract_id: "CT-API-02"
          name: "受注一覧API"
          type: "api"
        - contract_id: "CT-API-03"
          name: "mcframe在庫引当契約"
          type: "api"
        - contract_id: "CT-API-04"
          name: "権限チェック・承認API"
          type: "api"
        - contract_id: "CT-DB-01"
          name: "ordersテーブル"
          type: "schema"
        - contract_id: "CT-DB-02"
          name: "order_itemsテーブル"
          type: "schema"
        - contract_id: "CT-DB-03"
          name: "approval_recordsテーブル"
          type: "schema"
        - contract_id: "CT-DB-04"
          name: "audit_logsテーブル"
          type: "schema"
      contracts_consumed:
        - contract_ref: "mcframe API v2 /api/v2/stock/allocate"
          name: "mcframe在庫引当外部API"
          owner_team: "PLATFORM"
      estimated_complexity: "high"
      estimated_story_points: 89
      tech_stack:
        - "Python"
        - "FastAPI"
        - "PostgreSQL"
        - "Alembic (migration)"
        - "mcframe SDK v2"

  # 単一FeatureのためFeature間依存はなし。WI間依存を記録
  dependency_graph:
    nodes:
      - id: "FEAT-ERPSAMPLE"
        layer: 0
        team: "TEAM-SLS"
    edges: []
    external_dependencies:
      - id: "EXT-001"
        from: "FEAT-ERPSAMPLE"
        to: "mcframe-core (PLATFORM)"
        type: "api_dependency"
        contract_id: "SC-API-MCFRAME"
        criticality: "high"
        description: "受注登録時にmcframe在庫引当APIを呼び出し"

  # Work Item分割（Feature内部の実行単位）
  work_items:
    - wi_id: "WI-ERP-SAMPLE-001"
      title: "受注登録画面のUI改善"
      complexity: "low"
      mode: "autopilot"
      risk_flags: ["ui_only"]
      covers_ac: ["AC-US-FEATERPOMS-001-02"]
      covers_contracts: ["CT-API-01"]
      test_refs: ["TS-E2E-01"]
      status: "done"
      run_ref: "runs/WI-ERP-SAMPLE-001/RUN-001"

    - wi_id: "WI-ERP-SAMPLE-002"
      title: "権限チェックロジック追加"
      complexity: "high"
      mode: "validate"
      risk_flags: ["authz", "audit_log"]
      covers_ac: ["AC-US-FEATERPOMS-002-01", "AC-US-FEATERPOMS-002-02"]
      covers_contracts: ["CT-API-04"]
      test_refs: ["TS-INT-03", "TS-INT-04"]
      status: "pending"
      depends_on: ["WI-ERP-SAMPLE-001"]

  integration_points:
    - point_id: "IP-001"
      name: "mcframe在庫引当連携"
      type: "api"
      provider_feature: "mcframe-core"
      consumer_features: ["FEAT-ERPSAMPLE"]
      contract_ref: "specs/FEAT-ERPSAMPLE/contracts/api.yaml#/paths/~1mcframe~1stock-allocation"
      sla:
        availability: "99.5%"
        latency_p99: "5000ms"
        rate_limit: "100 req/min"
      error_handling:
        retry_policy: "exponential_backoff"
        circuit_breaker: true
        fallback_behavior: "save_as_PENDING_STOCK"

  cross_team_tests:
    - test_id: "TS-INT-02"
      name: "mcframe在庫引当統合テスト"
      type: "integration"
      participating_features: ["FEAT-ERPSAMPLE"]
      owner_team: "TEAM-SLS"
      schedule: "per_run"
      environment: "staging"
      prerequisites:
        - "mcframe API v2テストエンドポイントが利用可能"
        - "テスト用在庫データがセットアップ済み"

  breakdown_gate_check:
    counts:
      total_features: 1
      total_contracts_owned: 8
      total_dependencies: 1
      cross_team_dependencies: 0
    rules:
      max_features_per_team: 5
      max_dependency_depth: 0
    no_dependency_cycles: true
    all_integration_points_defined: true
    coverage_tiers_assigned: true
    sla_defined_for_all_integration_points: true
    ready_for_feature_specs: true
```

---

## 1. Decomposition Rationale

### 1.1 Guiding Principles

1. **Single Feature = Single Team**: FEAT-ERPSAMPLE は TEAM-SLS が完全オーナーシップ
2. **Contract-First**: API（CT-API-01~04）とDB（CT-DB-01~04）の契約をSpec段階で確定
3. **Risk-based WI Split**: Work Itemはリスクプロファイルに基づき分割

### 1.2 Key Decisions

| Decision ID | Description | Rationale |
|-------------|-------------|-----------|
| FBD-DEC-001 | 受注登録と権限・承認を2つのWIに分割 | リスクプロファイルが異なる（ui_only vs authz+audit_log） |
| FBD-DEC-002 | mcframe連携をFeature内部のCT-API-03として管理 | 独立したビジネス価値を持たず、別Feature化は過剰 |

---

## 2. Feature Details

### 2.1 FEAT-ERPSAMPLE: mcframe受注管理アドオン

| 属性 | 値 |
|------|-----|
| **Team** | TEAM-SLS |
| **Coverage Tier** | standard |
| **Priority** | 1 |
| **Complexity** | high |
| **Story Points** | 89 |
| **Work Items** | 2 (WI-001: done, WI-002: pending) |

**Scope**:
- 受注登録REST API（CT-API-01）
- 受注一覧取得API（CT-API-02）
- mcframe在庫引当連携（CT-API-03）
- 権限チェック・承認API（CT-API-04）
- 確認ダイアログUI
- 金額別3段階承認フロー
- SoD検証
- 全操作の監査ログ

**Contracts Owned**:

| Contract ID | Name | Type | Spec Reference |
|-------------|------|------|----------------|
| CT-API-01 | 受注登録API | API | api.yaml#createOrder |
| CT-API-02 | 受注一覧API | API | api.yaml#listOrders |
| CT-API-03 | mcframe在庫引当契約 | API | api.yaml#allocateStock |
| CT-API-04 | 権限チェック・承認API | API | api.yaml#approveOrder |
| CT-DB-01 | ordersテーブル | Schema | database_schema.yaml#orders |
| CT-DB-02 | order_itemsテーブル | Schema | database_schema.yaml#order_items |
| CT-DB-03 | approval_recordsテーブル | Schema | database_schema.yaml#approval_records |
| CT-DB-04 | audit_logsテーブル | Schema | database_schema.yaml#audit_logs |

**Contracts Consumed**:

| Contract Ref | Name | Owner |
|--------------|------|-------|
| mcframe API v2 | mcframe在庫引当外部API | PLATFORM |

---

## 3. Work Item Breakdown

### 3.1 WI-ERP-SAMPLE-001: 受注登録画面のUI改善

| 属性 | 値 |
|------|-----|
| **Complexity** | low |
| **Mode** | autopilot |
| **Risk Flags** | ui_only |
| **Status** | done (RUN-001 complete) |
| **Covers AC** | AC-US-FEATERPOMS-001-02 |
| **Test Refs** | TS-E2E-01 |

**Scope**:
- 登録ボタンの配置変更（右下・プライマリアクション標準位置）
- 確認ダイアログコンポーネント作成（ConfirmDialog）
- E2Eテスト追加

### 3.2 WI-ERP-SAMPLE-002: 権限チェックロジック追加

| 属性 | 値 |
|------|-----|
| **Complexity** | high |
| **Mode** | validate |
| **Risk Flags** | authz, audit_log |
| **Status** | pending |
| **Depends On** | WI-ERP-SAMPLE-001 |
| **Covers AC** | AC-US-FEATERPOMS-002-01, AC-US-FEATERPOMS-002-02 |
| **Test Refs** | TS-INT-03, TS-INT-04 |

**Scope**:
- RBAC権限マトリクス実装（authz_matrix.yaml準拠）
- 金額別3段階承認フロー状態マシン
- SoD検証ロジック（created_by ≠ approver_id）
- 全操作の監査ログミドルウェア
- 統合テスト（承認9件 + 監査ログ7件）

### 3.3 WI Dependency

```
WI-ERP-SAMPLE-001 (low, autopilot, ui_only)
    │ ✅ done
    ▼
WI-ERP-SAMPLE-002 (high, validate, authz+audit_log)
    │ ⏳ pending
    ▼
Final Gate
```

---

## 4. Integration Points

### 4.1 IP-001: mcframe在庫引当連携

| 属性 | 値 |
|------|-----|
| **Type** | API（外部） |
| **Provider** | mcframe-core (PLATFORM) |
| **Consumer** | FEAT-ERPSAMPLE |
| **Contract** | api.yaml#allocateStock |

**SLA**:

| Metric | Target |
|--------|--------|
| Availability | 99.5% |
| Latency (P99) | 5000ms |
| Rate Limit | 100 req/min |

**Error Handling**:
- Retry Policy: Exponential backoff (3s → 10s during month-end)
- Circuit Breaker: Enabled
- Fallback: 在庫引当失敗時は `PENDING_STOCK` 状態で受注を保存

---

## 5. Test Strategy

### 5.1 Test Coverage Matrix

| Test ID | Type | Covers AC | Covers CT | Tests |
|---------|------|-----------|-----------|-------|
| TS-CON-01 | contract | AC-US-FEATERPOMS-001-01 | CT-API-01 | 8 |
| TS-CON-02 | contract | AC-US-FEATERPOMS-001-03 | CT-API-03 | 5 |
| TS-INT-01 | integration | AC-US-FEATERPOMS-001-01 | CT-API-01, CT-DB-01 | 12 |
| TS-INT-02 | integration | AC-US-FEATERPOMS-001-03 | CT-API-03 | 6 |
| TS-INT-03 | integration | AC-US-FEATERPOMS-002-01 | CT-API-04 | 9 |
| TS-INT-04 | integration | AC-US-FEATERPOMS-002-02 | CT-DB-04 | 7 |
| TS-E2E-01 | e2e | AC-US-FEATERPOMS-001-02 | - | 3 |
| TS-UT-01 | unit | - | - | TBD |
| TS-UT-02 | unit | - | - | TBD |
| **Total** | | **5 AC** | **8 CT** | **50** |

### 5.2 Current Test Results (WI-001 complete)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Tests | 50 | - | - |
| Pass Rate | 100% (50/50) | 100% | PASS |
| Coverage | 83.6% | ≥ 80% | PASS |

---

## 6. Implementation Order

### 6.1 Recommended Sequence

```
Phase 1: 受注登録基盤 (Sprint 1 — EM-01)
└─ WI-ERP-SAMPLE-001 (TEAM-SLS, autopilot)
   ├─ 登録ボタン配置変更
   ├─ 確認ダイアログ実装
   ├─ E2Eテスト追加（TS-E2E-01）
   └─ ✅ completed 2026-02-10

Phase 2: 権限・承認・監査 (Sprint 2 — EM-02)
└─ WI-ERP-SAMPLE-002 (TEAM-SLS, validate)
   ├─ 権限マトリクス実装
   ├─ 承認フロー状態マシン
   ├─ SoD検証ロジック
   ├─ 監査ログミドルウェア
   └─ 統合テスト（TS-INT-03, TS-INT-04）

Phase 3: 統合テスト・リリース (Sprint 3 — EM-03)
└─ Final Integration
   ├─ 全テスト回帰実行
   ├─ Ops Pack完成
   └─ Final Gate申請
```

---

## 7. Appendix

### 7.1 Related Documents

- `epic_design.md` - Parent Epic設計
- `EPIC_APPROVAL.md` - Epic承認記録（人間のみ編集可）
- `EPIC_PROGRESS_REPORT.md` - 進捗レポート
- `specs/FEAT-ERPSAMPLE/` - 全Feature仕様

### 7.2 Traceability Summary

```
Epic: EPIC-SAMPLE
└─ Feature: FEAT-ERPSAMPLE (TEAM-SLS, standard)
   ├─ Use Cases: US-FEATERPOMS-001, US-FEATERPOMS-002
   ├─ ACs: AC-US-FEATERPOMS-001-01~03, AC-US-FEATERPOMS-002-01~02
   ├─ Contracts: CT-API-01~04, CT-DB-01~04, SC-API-MCFRAME
   ├─ Tests: TS-CON-01~02, TS-INT-01~04, TS-E2E-01, TS-UT-01~02
   ├─ Work Items:
   │   ├─ WI-ERP-SAMPLE-001 (done, autopilot, RUN-001)
   │   └─ WI-ERP-SAMPLE-002 (pending, validate)
   └─ Ops: transport_manifest.yaml, rollback_plan.md, hypercare_runbook.md
```

### 7.3 Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-01 | 0.1.0 | 鈴木次郎 | Initial breakdown |
| 2026-02-10 | 0.2.0 | 鈴木次郎 | WI-001完了、テスト結果反映 |
| 2026-02-15 | 1.0.0 | 佐藤三郎 | v4.4.0テンプレート対応、Work Item詳細追加 |
