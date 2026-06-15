---
template: spec
feature_id: FEAT-ERP-{{DOMAIN}}-{{NNN}}
use_cases:
  - UC-001: "{{use_case_title}}"
acceptance_criteria:
  - id: AC-{{...}}
    tag: integration  # integration|e2e|security|performance|audit
    ears: "WHEN {{trigger}}, THE system SHALL {{response}}."
nfr:
  - id: NFR-001
    type: security
    shall: "{{...}}"
---

# Use Cases
# Acceptance Criteria (EARS)
# NFR (Security/Performance/Audit/Operations)
# Data & Integration Notes
