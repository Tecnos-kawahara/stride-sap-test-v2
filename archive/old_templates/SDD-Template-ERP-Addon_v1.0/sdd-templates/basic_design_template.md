---
template: basic_design
feature_id: FEAT-ERP-{{DOMAIN}}-{{NNN}}
coverage_tier: standard  # critical|standard|experimental
owners:
  pm: "@PM"
  tech_lead: "@TL"
  qa: "@QA"
context:
  erp: "{{ERP_NAME}}"
  landscape: "{{LANDSCAPE_SUMMARY}}"
traceability_rows:
  - req_id: REQ-{{...}}
    ac_ids: ["AC-{{...}}"]
integration_flows:
  - name: "{{integration_flow_name}}"
    incoming: ["{{system}}:{{message}}"]
    outgoing: ["{{system}}:{{message}}"]
blocking_questions: []
---

# WHO / WHAT / WHY
## Background
## Goal
## Scope (In/Out)
## Non-goals

# Stakeholders / RACI
# Assumptions & Constraints
# Risks (ERP)
- 権限/SoD:
- データ移行:
- 連携（更新系/冪等性）:
- 性能（締め/大量）:

# Traceability
(上のtraceability_rowsを基点に、AC/CT/TSへ接続する)
