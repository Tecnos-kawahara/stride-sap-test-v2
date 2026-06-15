# Epic Design: EPIC-SAMPLE - mcframe受注管理アドオン

> **Version**: 1.0.0
> **Status**: in_review
> **Last Updated**: 2026-02-15

---

## 0. Canonical Epic Design (YAML)

```yaml
epic:
  meta:
    epic_id: "EPIC-SAMPLE"
    title: "mcframe受注管理アドオン"
    version: "1.0.0"
    status: "in_review"  # draft | in_review | approved | deprecated
    created_at: "2026-02-01"
    updated_at: "2026-02-15"

  ownership:
    sponsor: "田中太郎"
    epic_lead: "佐藤三郎"
    teams:
      - team_id: "TEAM-SALES"
        name: "営業システムチーム"
        lead: "鈴木次郎"
        features:
          - "FEAT-ERP-OMS"

  scope:
    business_context:
      who: "営業担当者、営業マネージャー、役員（承認者）"
      what: "mcframe ERP上の受注登録・承認・在庫引当を統合管理するWebアドオン"
      why: "受注処理の手動作業を削減し、金額別3段階承認と監査ログでコンプライアンスを強化"
    value_stream: "Order-to-Cash (O2C)"
    strategic_alignment:
      - "DX 2026: 基幹業務プロセスのデジタル化"
      - "コンプライアンス強化: 金額別承認フローと監査証跡の自動化"
    out_of_scope:
      - "請求書発行（mcframe標準機能を使用）"
      - "入金消込（将来Epicで対応）"
      - "在庫補充・予測（mcframe標準機能）"
      - "バッチ受注処理"

  features:
    - feature_id: "FEAT-ERP-OMS"
      name: "mcframe受注管理アドオン"
      team_id: "TEAM-SALES"
      coverage_tier: "standard"
      priority: 1
      dependencies: []
      description: "受注登録・承認フロー・mcframe在庫引当・監査ログを統合管理するWebアプリケーション"

  shared_contracts:
    - contract_ref: "specs/sample_erp_addon/contracts/api.yaml#mcframe-stock-allocation"
      contract_id: "SC-API-MCFRAME"
      name: "mcframe在庫引当API（外部）"
      owner_team: "PLATFORM"
      owner_feature: "mcframe-core"
      consumers:
        - team_id: "TEAM-SALES"
          features: ["FEAT-ERP-OMS"]
      type: "api"

  cross_team_dependencies:
    - dependency_id: "DEP-001"
      from_feature: "FEAT-ERP-OMS"
      to_feature: "mcframe-core"
      type: "blocking"
      interface: "SC-API-MCFRAME"
      description: "受注登録時にmcframe在庫引当APIを呼び出し。mcframe API v2が利用可能であること"

  milestones:
    - id: "EM-01"
      name: "受注登録基盤完了"
      target_date: "2026-02-10"
      features: ["FEAT-ERP-OMS"]
      exit_criteria:
        - "受注登録API（CT-API-01）実装・テスト完了"
        - "確認ダイアログUI実装（AC-US-FEATERPOMS-001-02）"
        - "mcframe在庫引当連携（CT-API-03）動作確認"

    - id: "EM-02"
      name: "権限・承認・監査完了"
      target_date: "2026-03-01"
      features: ["FEAT-ERP-OMS"]
      exit_criteria:
        - "金額別3段階承認フロー実装（AC-US-FEATERPOMS-002-01）"
        - "SoD検証ロジック実装・テスト完了"
        - "全操作の監査ログ出力（AC-US-FEATERPOMS-002-02）"

    - id: "EM-03"
      name: "Epic統合完了・リリース"
      target_date: "2026-03-15"
      features: ["FEAT-ERP-OMS"]
      exit_criteria:
        - "全50テストPASS、カバレッジ≥80%"
        - "Ops Pack完成（transport/rollback/hypercare）"
        - "Final Gate承認"

  integration_points:
    - point_id: "IP-001"
      name: "mcframe在庫引当連携"
      type: "api"
      provider_feature: "mcframe-core"
      consumer_features: ["FEAT-ERP-OMS"]
      contract_ref: "specs/sample_erp_addon/contracts/api.yaml#/paths/~1mcframe~1stock-allocation"
      sla:
        availability: "99.5%"
        latency_p99: "5000ms"
      test_strategy: "contract_test (TS-CON-02) + integration_test (TS-INT-02)"

  risks:
    - risk_id: "ER-001"
      description: "mcframe API月次締め期間（25日-末日）の応答遅延"
      probability: "high"
      impact: "medium"
      mitigation: "リトライ間隔延長（3s→10s）、アラート閾値緩和、PENDING_STOCK状態でのフォールバック"
      owner: "TEAM-SALES"

    - risk_id: "ER-002"
      description: "権限チェック実装の複雑さによるセキュリティリスク"
      probability: "medium"
      impact: "high"
      mitigation: "authz_matrix.yamlでの宣言的権限定義、validate modeでの設計レビュー必須化"
      owner: "TEAM-SALES"

    - risk_id: "ER-003"
      description: "監査ログの欠落によるコンプライアンス違反"
      probability: "low"
      impact: "high"
      mitigation: "ミドルウェアでの自動ログ出力、TS-INT-04での全操作パターン検証"
      owner: "TEAM-SALES"

  team_capacity:
    - team_id: "TEAM-SALES"
      allocated_members: 4
      effort_points: 89
      start_date: "2026-02-01"
      end_date: "2026-03-15"

  critical_path:
    - milestone_id: "EM-01"
      dependent_features: ["FEAT-ERP-OMS"]
      target_date: "2026-02-10"
      status: "completed"
    - milestone_id: "EM-02"
      dependent_features: ["FEAT-ERP-OMS"]
      target_date: "2026-03-01"
      status: "pending"
    - milestone_id: "EM-03"
      dependent_features: ["FEAT-ERP-OMS"]
      target_date: "2026-03-15"
      status: "pending"

  shared_contract_manifest:
    - contract_id: "SC-API-MCFRAME"
      type: "api"
      owner_team: "PLATFORM"
      consumers:
        - team_id: "TEAM-SALES"
          adoption_status: "in_development"
      version_constraint: ">= 2.0.0"

  progress_tracking:
    reporting_frequency: "weekly"
    dashboard_auto_generate: true
    blocker_escalation_sla_hours: 24
    team_status_report_required: true
    artifacts:
      epic_progress_report: "epics/EPIC-SAMPLE/EPIC_PROGRESS_REPORT.md"
      dependency_manifest: "epics/EPIC-SAMPLE/DEPENDENCY_MANIFEST.yaml"
      contract_registry: "specs/sample_erp_addon/contracts/"
      ops_pack_registry: "epics/EPIC-SAMPLE/OPS_PACK_REGISTRY.yaml"

  epic_gate_check:
    counts:
      total_features: 1
      critical_features: 0
      standard_features: 1
      experimental_features: 0
      cross_team_dependencies: 1
      shared_contracts: 1
    rules:
      min_features: 1
      max_critical_per_epic: 5
      max_teams: 5
    all_features_have_team: true
    all_dependencies_mapped: true
    shared_contracts_defined: true
    no_dependency_cycles: true
    ready_for_feature_specs: true
```

---

## 1. Executive Summary

### 1.1 Business Context

| 項目 | 内容 |
|------|------|
| **WHO** | 営業担当者、営業マネージャー、役員（承認者） |
| **WHAT** | mcframe ERP上の受注登録・承認・在庫引当を統合管理するWebアドオン |
| **WHY** | 受注処理の手動作業を削減し、金額別3段階承認と監査ログでコンプライアンスを強化 |
| **VALUE STREAM** | Order-to-Cash (O2C) |

### 1.2 Strategic Alignment

- DX 2026: 基幹業務プロセスのデジタル化
- コンプライアンス強化: 金額別承認フローと監査証跡の自動化

### 1.3 Success Criteria

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| 受注登録所要時間 | < 30秒 | API応答時間の平均 |
| 承認フロー自動化率 | 100万円未満=100%自動 | 自動承認率の計測 |
| 監査ログカバレッジ | 全操作100% | audit_logsテーブルのレコード数/操作数 |
| テストカバレッジ | ≥ 80% | pytest --cov レポート |

---

## 2. Team Organization

### 2.1 Team Structure

```
Epic Lead: 佐藤三郎 (PMO)
│
└─ TEAM-SALES: 営業システムチーム
    ├─ Lead: 鈴木次郎 (Tech Lead / Architect)
    ├─ Features: FEAT-ERP-OMS
    ├─ Members:
    │   ├─ @tanaka (PM / Product Owner)
    │   ├─ @suzuki (Tech Lead)
    │   ├─ @yamada (Developer)
    │   └─ @sato (QA)
    └─ Responsibilities: 受注登録API、承認フロー、mcframe連携、監査ログ
```

### 2.2 RACI Matrix

| Activity | TEAM-SALES | Epic Lead | ARCH_BOARD |
|----------|-----------|-----------|------------|
| Epic Design Approval | R | A | I |
| Feature Breakdown | R | A | I |
| mcframe連携契約定義 | R | A | I |
| 権限マトリクス設計 | R | A | I |
| Final Integration | R | A | I |

---

## 3. Feature Breakdown

### 3.1 Feature Overview

| Feature ID | Name | Team | Coverage Tier | Priority | Dependencies |
|------------|------|------|---------------|----------|--------------|
| FEAT-ERP-OMS | mcframe受注管理アドオン | TEAM-SALES | standard | 1 | mcframe API v2 |

### 3.2 Scope Summary

**In Scope**:
- 受注登録（REST API + Web UI）
- 金額別3段階承認フロー（自動/部長/役員）
- mcframe在庫引当連携
- 確認ダイアログ（誤操作防止）
- RBAC権限チェック + SoD検証
- 全操作の監査ログ

**Out of Scope**:
- 請求書発行、入金消込
- 在庫補充・予測
- バッチ受注処理
- 受注分析・レポーティング

### 3.3 Coverage Tier Rationale

| Feature | Tier | Rationale |
|---------|------|-----------|
| FEAT-ERP-OMS | standard | ERP連携ありだが、既存mcframe APIの上に構築。単一チーム。critical は過剰 |

---

## 4. Shared Contracts

### 4.1 Contract Registry

| Contract ID | Name | Type | Owner | Consumers |
|-------------|------|------|-------|-----------|
| SC-API-MCFRAME | mcframe在庫引当API | API | PLATFORM | TEAM-SALES |

### 4.2 Feature内部契約

| Contract ID | Name | Type | Spec Reference |
|-------------|------|------|----------------|
| CT-API-01 | 受注登録API | API | api.yaml#createOrder |
| CT-API-02 | 受注一覧API | API | api.yaml#listOrders |
| CT-API-03 | mcframe在庫引当契約 | API | api.yaml#allocateStock |
| CT-API-04 | 権限チェックAPI | API | api.yaml#approveOrder, getPermissions |
| CT-DB-01 | ordersテーブル | DB | database_schema.yaml#orders |
| CT-DB-02 | order_itemsテーブル | DB | database_schema.yaml#order_items |
| CT-DB-03 | approval_recordsテーブル | DB | database_schema.yaml#approval_records |
| CT-DB-04 | audit_logsテーブル | DB | database_schema.yaml#audit_logs |

### 4.3 Contract Change Protocol

1. 契約オーナーがCCP（Contract Change Proposal）を作成
2. 影響分析を自動生成（`spec_drift_detector.py` で検出可能）
3. mcframe連携変更の場合、PLATFORM チームにも通知
4. TLレビュー + 回帰テスト実行
5. 共有契約（SC-*）変更の場合は ARCH_BOARD 承認

---

## 5. Milestones

### 5.1 Timeline

```
EM-01: 受注登録基盤      EM-02: 権限・承認        EM-03: リリース
    │                       │                       │
    ▼                       ▼                       ▼
────┼───────────────────────┼───────────────────────┼──────►
    │                       │                       │
    2026-02-10              2026-03-01              2026-03-15
    WI-001完了              WI-002完了              Final Gate
    (✅ completed)          (pending)               (pending)
```

### 5.2 Milestone Details

#### EM-01: 受注登録基盤完了

- **Target Date**: 2026-02-10
- **Status**: completed
- **Features**: FEAT-ERP-OMS (WI-ERP-SAMPLE-001)
- **Exit Criteria**:
  - [x] 受注登録API（CT-API-01）実装・テスト完了
  - [x] 確認ダイアログUI実装（AC-US-FEATERPOMS-001-02）
  - [x] mcframe在庫引当連携（CT-API-03）動作確認

#### EM-02: 権限・承認・監査完了

- **Target Date**: 2026-03-01
- **Status**: pending
- **Features**: FEAT-ERP-OMS (WI-ERP-SAMPLE-002)
- **Exit Criteria**:
  - [ ] 金額別3段階承認フロー実装（AC-US-FEATERPOMS-002-01）
  - [ ] SoD検証ロジック実装・テスト完了
  - [ ] 全操作の監査ログ出力（AC-US-FEATERPOMS-002-02）

#### EM-03: Epic統合完了・リリース

- **Target Date**: 2026-03-15
- **Status**: pending
- **Features**: FEAT-ERP-OMS
- **Exit Criteria**:
  - [ ] 全50テストPASS、カバレッジ≥80%
  - [ ] Ops Pack完成（transport/rollback/hypercare）
  - [ ] Final Gate承認

---

## 6. Integration Strategy

### 6.1 Integration Points

| Point ID | Type | Provider | Consumer | Contract |
|----------|------|----------|----------|----------|
| IP-001 | API | mcframe-core | FEAT-ERP-OMS | api.yaml#allocateStock |

### 6.2 Integration Test Strategy

- **Contract Tests**: CT-API-01~04, CT-DB-01~04 をCI/CDで自動実行（TS-CON-01, TS-CON-02）
- **Integration Tests**: mcframe在庫引当連携（TS-INT-02）、承認フロー（TS-INT-03）、監査ログ（TS-INT-04）
- **E2E Smoke**: 受注登録の主要フロー検証（TS-E2E-01）

---

## 7. Risks & Mitigations

| Risk ID | Description | Probability | Impact | Mitigation | Owner |
|---------|-------------|-------------|--------|------------|-------|
| ER-001 | mcframe API月次締め期間の応答遅延 | High | Medium | リトライ延長+PENDING_STOCKフォールバック | TEAM-SALES |
| ER-002 | 権限チェック実装の複雑さ→セキュリティリスク | Medium | High | authz_matrix.yaml宣言的定義+validate mode | TEAM-SALES |
| ER-003 | 監査ログ欠落→コンプライアンス違反 | Low | High | ミドルウェア自動出力+TS-INT-04全パターン検証 | TEAM-SALES |

---

## 8. Team Capacity & Progress Tracking (v3.0)

### 8.1 Team Capacity

| Team | Members | Effort (SP) | Start | End | Utilization |
|------|---------|-------------|-------|-----|-------------|
| TEAM-SALES | 4 | 89 | 2026-02-01 | 2026-03-15 | 74% |

### 8.2 Critical Path

```
EM-01 (2026-02-10)        EM-02 (2026-03-01)        EM-03 (2026-03-15)
  │ WI-001 ✅ done          │ WI-002 pending          │ Final Gate
  ▼                         ▼                         ▼
──┼─────────────────────────┼─────────────────────────┼───────►
  [TEAM-SALES]              [TEAM-SALES]              [TEAM-SALES]
```

### 8.3 Progress Tracking Artifacts

| Artifact | Location | Update Frequency | Owner |
|----------|----------|------------------|-------|
| EPIC_PROGRESS_REPORT.md | `epics/EPIC-SAMPLE/` | Weekly | 佐藤三郎 (Epic Lead) |
| DEPENDENCY_MANIFEST.yaml | `epics/EPIC-SAMPLE/` | On change | 佐藤三郎 (Epic Lead) |
| OPS_PACK_REGISTRY.yaml | `epics/EPIC-SAMPLE/` | Per WI completion | 鈴木次郎 (TL) |

### 8.4 Reporting Cadence

- **Daily**: `epic_progress_aggregator.py` でターミナル確認（PM）
- **Weekly**: EPIC_PROGRESS_REPORT.md 更新 + チームステータスレポート収集
- **Milestone**: Epic Progress Gate チェック + ステアリング会議
- **Go-Live前**: Ops Pack 100%確認 + Final Integration Test

---

## 9. Open Questions

| ID | Question | Status | Assigned To | Due Date |
|----|----------|--------|-------------|----------|
| EQ-001 | mcframe API v2のSLA正式合意 | resolved | 鈴木次郎 | 2026-02-05 |
| EQ-002 | 監査ログの保存期間（7年 vs 10年） | open | 田中太郎 | 2026-02-28 |

---

## 10. Appendix

### 10.1 Related Documents

- `feature_breakdown.md` - 詳細なFeature分割
- `EPIC_APPROVAL.md` - Epic承認記録（人間のみ編集可）
- `EPIC_PROGRESS_REPORT.md` - 進捗レポート
- `DEPENDENCY_MANIFEST.yaml` - 依存関係マニフェスト
- `OPS_PACK_REGISTRY.yaml` - Ops Pack レジストリ
- `specs/sample_erp_addon/` - Feature仕様・契約・テスト

### 10.2 Feature Specs Reference

| Artifact | Path |
|----------|------|
| Basic Design | `specs/sample_erp_addon/basic_design.md` |
| Spec | `specs/sample_erp_addon/spec.md` |
| Plan | `specs/sample_erp_addon/plan.md` |
| Tasks | `specs/sample_erp_addon/tasks.md` |
| BPMN | `specs/sample_erp_addon/process.bpmn` |
| API Contract | `specs/sample_erp_addon/contracts/api.yaml` |
| DB Schema | `specs/sample_erp_addon/contracts/database_schema.yaml` |
| Test Scenarios | `specs/sample_erp_addon/tests/scenarios.yaml` |
| State | `specs/sample_erp_addon/state/state.yaml` |
| Evidence Pack | `specs/sample_erp_addon/implementation-details/evidence_pack.md` |

### 10.3 Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-02-01 | 0.1.0 | 佐藤三郎 | Initial draft |
| 2026-02-10 | 0.2.0 | 鈴木次郎 | EM-01完了に伴い更新 |
| 2026-02-15 | 1.0.0 | 佐藤三郎 | v4.4.0テンプレート対応、進捗追跡artifacts追加 |
