---
name: "SDD Work Item"
about: "Spec-Driven Development ワークアイテム（Tecnos-STRIDE）"
title: "[WI] "
labels: "work-item, status:pending"
assignees: ""
---

<!-- ============================================================
  SDD Work Item Template (Tecnos-STRIDE)
  
  日常の管理は GitHub Issues で行い、Gate 審査時に
  `stride wi sync` で specs/*/work_items/WI-*.md に同期します。
  
  ⚠️ メタデータブロック（下の YAML）は必ず記入してください。
     stride wi sync がパースして WI ファイルに変換します。
============================================================ -->

```yaml
# === SDD Metadata (required) ===
wi_id: "WI-ERP-XXX-NNN"
feature_id: "FEAT-XXX"
complexity: "medium"        # low | medium | high
mode: "autopilot"           # autopilot | confirm | validate
priority: "P2-Medium"       # P0-Critical | P1-High | P2-Medium | P3-Low
risk_flags: []              # erp_addon_risk_taxonomy.yaml 参照
spec_refs:
  - "basic_design.md"
  - "spec.md"
  - "plan.md"
contract_refs:
  acceptance_ids: []        # AC-US-XXX-NNN
  contract_ids: []          # CT-API-NNN
test_refs: []               # TS-INT-XXX, TS-E2E-XXX
owners:
  pm: "@PM"
  tech_lead: "@TL"
  dev: "@DEV"
  qa: "@QA"
```

## Intent

<!-- この WI で達成したいこと（1-2文） -->

## Scope

<!-- 変更対象（UI / IO / API/電文 / MSG / DB / Authz / Migration / Ops） -->

## Plan

<!-- 実装計画・ステップ -->

## Risk Flags

- [ ] authz / SoD — 認可・職務分離ロジックの変更
- [ ] audit_log / pii — 監査ログ・個人情報への影響
- [ ] db_schema — DBスキーマ変更
- [ ] data_migration — データ移行を伴う
- [ ] update_integration — 外部連携の更新
- [ ] cross_module — モジュール横断
- [ ] accounting_calc / inventory_valuation — 会計計算・在庫評価
- [ ] new_api / contract_change — API追加・契約変更
- [ ] performance_sensitive — パフォーマンス影響
- [ ] ui_only / message_only / test_only / logging_only — 低リスク変更

## Spec Links (Single source of truth)

- UI: 
- IO: 
- API/電文: 
- MSG: 
- TEST: 

## Acceptance Criteria

<!-- spec.md の AC を参照 -->
- AC-XXX-NNN-01: 
- AC-XXX-NNN-02: 

## Definition of Done

- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新（契約＋例外＋メッセージ）
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）

## Links

- Spec: `specs/<feature>/spec.md`
- Plan: `specs/<feature>/plan.md`
- Tasks: `specs/<feature>/tasks.md`
