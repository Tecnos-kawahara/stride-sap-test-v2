---
wi_id: WI-ERP-SAMPLE-002
title: "権限チェックロジック追加"
complexity: high
mode: validate
risk_flags: ["authz", "audit_log"]
dependencies: ["WI-ERP-SAMPLE-001"]
mode_override:
  reason: ""
spec_refs:
  - "specs/sample_erp_addon/basic_design.md"
  - "specs/sample_erp_addon/spec.md"
  - "specs/sample_erp_addon/plan.md"
contract_refs:
  acceptance_ids: ["AC-US-FEATERPOMS-002-01", "AC-US-FEATERPOMS-002-02"]
  contract_ids: ["CT-API-04"]
test_refs:
  - "TS-INT-03"
  - "TS-INT-04"
owners:
  pm: "@tanaka"
  tech_lead: "@suzuki"
  dev: "@yamada"
  qa: "@sato"
---

# Intent
受注登録時の権限チェックを強化し、金額に応じた3段階承認フローを実装する。
全操作に対して監査ログを出力し、コンプライアンス要件を満たす。

# Scope
- **Authz**: RBAC（operator / manager / admin）ベースの権限チェック
- **Approval Flow**: 金額別3段階承認（100万円未満:自動、100万円以上:部長、500万円以上:役員）
- **SoD**: 受注登録者と承認者の同一人物チェック
- **Audit**: 全操作（CREATE/UPDATE/DELETE/APPROVE/REJECT）の監査ログ出力

# Plan
1. 権限マトリクス実装（authz_matrix.yaml準拠）
2. 承認フロー状態マシン実装
3. SoD検証ロジック実装
4. 監査ログミドルウェア実装
5. 統合テスト（TS-INT-03: 承認フロー、TS-INT-04: 監査ログ）

## Risk Flags
- [x] authz — 権限制御の追加（誤実装時にセキュリティリスク）
- [x] audit_log — 監査ログの追加（コンプライアンス要件）

## Spec Links (Single source of truth)
- UI: approval_flow.tsx（承認画面）、admin_panel.tsx（権限管理）
- IO: audit_logs テーブル（INSERT）
- API/電文: CT-API-04（権限チェックAPI）
- MSG: 承認依頼通知、承認完了通知
- TEST: TS-INT-03（承認フロー）、TS-INT-04（監査ログ）
- AC: AC-US-FEATERPOMS-002-01, AC-US-FEATERPOMS-002-02
- BPMN: BPMN-GW-001（金額判定ゲートウェイ）
- Authz Matrix: specs/sample_erp_addon/implementation-details/authz_matrix.yaml

## Definition of Done
- [ ] Spec差分レビュー完了（validate mode: 設計差分 + 権限マトリクスTLレビュー）
- [ ] 実装完了（影響箇所列挙）: authz middleware, approval state machine, audit logger
- [ ] テスト追加/更新（契約＋例外＋メッセージ）: TS-CON-03, TS-CON-04、統合: TS-INT-03 9件, TS-INT-04 7件、SoD検証含む
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）: ロールバック手順に権限関連追加
