---
template: plan
feature_id: FEAT-ERP-{{DOMAIN}}-{{NNN}}
contracts:
  - id: CT-IO-001
    kind: io
    description: "検索/更新/ファイル入出力契約"
  - id: CT-API-001
    kind: api
    description: "電文/サービス契約"
tests:
  - id: TS-INT-001
    type: integration
    covers_acceptance_ids: ["AC-..."]
  - id: TS-CON-001
    type: contract
    covers_contract_ids: ["CT-IO-001"]
coverage_policy:
  acceptance_coverage_required: true
  acceptance_coverage_target_pct: 100
  contract_coverage_required: true
  contract_coverage_target_pct: 100
  code_coverage_targets:
    - scope: "CMP-*"
      line_pct: 70
      branch_pct: 60
---

# Architecture / Extension Strategy
# Contracts (IO/API/MSG/Audit)
# Test Strategy (UT/SIT/E2E)
# Coverage Policy
# ERP Release/Transport Strategy (pointer to ops/)
