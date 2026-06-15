# Gate Evidence Pack (Web-EDI Sample Feature)

---
artifact: "evidence_pack"
template_id: "TPL-EVID-TECNOS-001"
feature_id: "FEAT-SAMPLE"
evidence_pack_id: "EVID-SAMPLE-001"
version: "{{TEMPLATE_VERSION}}"
status: "draft" # draft | in_review | approved | deprecated
owners:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Tech Lead", role: "Tech Lead" }
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: This document's source of truth is **#0 Canonical Evidence Pack (YAML)**.
> Purpose: Centralized management of evidence artifacts (CI results/test reports/security scans/AI provenance) required for gate decisions.
> Tecnos: Evidence Pack shall be retained for 7 years for audit compliance.

# 0. Canonical Evidence Pack (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

evidence_pack:
  gate_id: "Gate-1"           # Gate-1 | Gate-2 | ... | Gate-5 | Final
  decision: "pending"         # pending | pass | conditional_pass | fail
  decision_rationale: ""
  approver: ""
  approval_date: ""

  # CI/CD Results
  ci_results:
    status: "pending"         # pending | pass | fail
    pipeline_url: ""
    run_id: ""
    timestamp: ""
    summary: ""
    artifacts:
      - name: ""
        path: ""
        type: ""              # log | report | artifact

  # Test Reports
  test_reports:
    unit:
      status: "pending"       # pending | pass | fail | skipped
      passed: 0
      failed: 0
      skipped: 0
      coverage_pct: 0
      report_path: ""

    contract:
      status: "pending"
      passed: 0
      failed: 0
      skipped: 0
      report_path: ""

    integration:
      status: "pending"
      passed: 0
      failed: 0
      skipped: 0
      report_path: ""

    e2e:
      status: "pending"
      passed: 0
      failed: 0
      skipped: 0
      report_path: ""
      artifacts:
        html_report: ""
        trace_dir: ""
        screenshot_dir: ""
        video_dir: ""

  # Security Scans
  security_scans:
    sast:
      tool: ""                # SAST ツール名を記入
      status: "pending"       # pending | pass | fail | skipped
      critical: 0
      high: 0
      medium: 0
      low: 0
      report_path: ""

    sca:
      tool: ""                # e.g., "trivy", "snyk", "dependabot"
      status: "pending"
      vulnerabilities: 0
      license_issues: 0
      report_path: ""

    secrets:
      tool: ""                # e.g., "gitleaks", "trufflehog"
      status: "pending"
      findings: 0
      report_path: ""

  # AI Provenance (v5.2)
  ai_provenance:
    provider: ""              # e.g., "Anthropic"
    surface: ""               # e.g., "claude-code" | "anthropic-api" | "bedrock" | "vertex-ai"
    model_id: ""              # e.g., "claude-opus-4-7"
    model_version: ""         # e.g., "2026-04-16"
    prompt_version: ""        # e.g., "sdd-agent-v5.2.0"
    inputs_hash: ""           # SHA256 of input files
    execution_settings:
      effort_level: ""        # e.g., "xhigh"
      reasoning_mode: ""      # e.g., "adaptive"
      thinking_display: ""    # e.g., "summarized" | "omitted"
      max_output_tokens: 0
    budget_controls:
      task_budget_enabled: false
      task_budget_tokens: 0
      beta_headers: []
      tokenizer_notes: ""
    deployment_controls:
      provider_target: ""     # e.g., "Claude Code" | "Anthropic API" | "Bedrock"
      organization_scope: ""  # org/workspace/tenant/subscription used for approval scope
      cyber_safeguards_reviewed: false
      cvp_status: ""          # not_required | pending | approved | rejected | unavailable
    generated_files:
      - path: ""
        hash: ""
    human_reviewed: false
    reviewer: ""
    review_date: ""

  # Findings & Issues
  findings:
    open_issues: []
    exceptions: []

  # Next Steps
  next_steps:
    - task: "Collect CI/SAST/SCA/Secrets/AI provenance artifacts"
      owner: ""
      due: ""
      status: "pending"       # pending | in_progress | completed
```

---

# 1. Gate Evidence Summary

## 1.1 Gate Information
- **Gate ID**: Gate-1
- **Decision**: Pending

## 1.2 Required Evidence Checklist

### CI/CD
- [ ] CI pipeline success
- [ ] All tests passing

### Test Coverage
- [ ] Unit tests: coverage >= 80%
- [ ] Contract tests: all CT covered
- [ ] Integration tests: integration-tagged AC covered
- [ ] E2E tests: e2e-tagged AC covered (if applicable)

### Security Scans
- [ ] SAST: Critical/High = 0
- [ ] SCA: No vulnerabilities or accepted
- [ ] Secrets scan: No findings

### AI Provenance
- [ ] Provider / surface / model / execution settings recorded
- [ ] Security workflows include cyber safeguards / CVP status
- [ ] Human review completed

---

# 2. Findings & Exceptions

## 2.1 Open Issues
| ID | Severity | Description | Owner | Due |
|----|----------|-------------|-------|-----|
| - | - | - | - | - |

## 2.2 Exceptions
| Article | Reason | Mitigation | Approved By |
|---------|--------|------------|-------------|
| - | - | - | - |

---

# 3. Next Steps
| Task | Owner | Due | Status |
|------|-------|-----|--------|
| Collect CI/SAST/SCA/Secrets/AI provenance artifacts | - | - | pending |

---

> End of evidence_pack.md
