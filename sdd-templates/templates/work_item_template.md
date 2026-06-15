---
wi_id: WI-ERP-{{FEATURE_ID}}-{{NNN}}
title: "{{変更の短い要約}}"
complexity: low|medium|high
mode: autopilot|confirm|validate
risk_flags: ["ui_only"]
dependencies: []
mode_override:
  reason: ""
spec_refs:
  - "basic_design.md"
  - "spec.md"
  - "plan.md"
contract_refs:
  acceptance_ids: ["AC-..."]
  contract_ids: ["CT-..."]
test_refs:
  - "TS-INT-..."
owners:
  pm: "@PM"
  tech_lead: "@TL"
  dev: "@DEV"
  qa: "@QA"
---

# Intent

# Scope (UI/IO/API/MSG/DB/Authz/Migration/Ops)

# Plan (Spec diff summary + execution steps)

## Risk Flags (Yes/No)
- [ ] authz / SoD / audit_log / pii
- [ ] db_schema
- [ ] data_migration
- [ ] update_integration
- [ ] cross_module
- [ ] accounting_calc / inventory_valuation
- [ ] new_api / contract_change
- [ ] performance_sensitive
- [ ] ui_only / message_only / test_only / logging_only

## Spec Links (Single source of truth)
- UI:
- IO:
- API/電文:
- MSG:
- TEST:

## Definition of Done
- [ ] Spec差分レビュー完了
- [ ] 実装完了（影響箇所列挙）
- [ ] テスト追加/更新（契約＋例外＋メッセージ）
- [ ] walkthrough（変更点・理由・検証手順）レビュー完了
- [ ] CI合格
- [ ] Ops更新（輸送/rollback/監視）
