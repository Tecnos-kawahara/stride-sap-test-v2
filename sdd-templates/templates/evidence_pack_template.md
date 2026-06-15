---
artifact: "evidence_pack"
template_id: "TPL-EVID-TECNOS-001"
feature_id: "FEAT-XXX"
evidence_pack_id: "EVID-XXX"
version: "{{TEMPLATE_VERSION}}"
status: "draft" # draft | in_review | approved | deprecated
owners:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Tech Lead", role: "Tech Lead" }
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Evidence Pack (YAML)**。説明文は補助。
> Purpose: Gate判定に必要な証跡（CI結果/テストレポート/セキュリティスキャン/AIプロヴェナンス）を一元管理する。
> Tecnos: 監査対応として、Evidence Packは承認後7年間保持する。

# 0. Canonical Evidence Pack (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

evidence_pack:
  gate_id: "Gate-X"           # Gate-1 | Gate-2 | ... | Gate-5 | Final
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

  # Planning Evidence (v3.0.1)
  planning_evidence:
    plan_summary: ""            # Brief summary of .planning/plan.md
    findings_count: 0           # Number of investigation findings
    key_decisions: []            # Major decisions from plan.md
    lessons_learned: []          # Reusable patterns from lessons.md
    planning_dir: ""            # Relative path e.g. "runs/WI-xxx/RUN-xxx/.planning/"

  # Metrics Trend (v4.2)
  metrics_trend:
    coverage_trend: []          # [{date, pct}] — coverage % over time
    test_time_trend: []         # [{date, seconds}] — test execution time over time
    cache_hit_rate: 0.0         # Turbo cache hit rate (%)
    gate_lead_time_hours: 0.0   # Total hours from first gate to last gate
    spec_drift_count: 0         # Number of spec drift items at last check

  # Findings & Issues
  findings:
    open_issues:
      - id: ""
        severity: ""          # critical | high | medium | low
        description: ""
        owner: ""
        due: ""
    exceptions:
      - article: ""           # Constitution Article reference
        reason: ""
        mitigation: ""
        approved_by: ""

  # Next Steps
  next_steps:
    - task: ""
      owner: ""
      due: ""
      status: "pending"       # pending | in_progress | completed
```

---

# 1. Gate Evidence Summary

## 1.1 Gate Information
- **Gate ID**: (Gate-1, Gate-2, etc.)
- **Decision**: 合格 | 条件付き合格 | 不合格

## 1.2 Required Evidence Checklist

### CI/CD
- [ ] CI パイプライン成功
- [ ] 全テスト合格

### Test Coverage
- [ ] Unit tests: coverage ≥ 80%
- [ ] Contract tests: 全CT カバー
- [ ] Integration tests: integration タグ付きAC カバー
- [ ] E2E tests: e2e タグ付きAC カバー（該当がある場合）

### Security Scans
- [ ] SAST: Critical/High = 0
- [ ] SCA: 脆弱性なし or 許容済み
- [ ] Secrets scan: 検出なし

### AI Provenance
- [ ] provider / surface / model / execution settings を記録
- [ ] security workflow の場合は cyber safeguards / CVP 状態を記録
- [ ] 人間によるレビュー完了

### Planning Evidence (v3.0.1)
- [ ] `.planning/plan.md` exists in Run directory
- [ ] `.planning/findings.md` documents investigation results
- [ ] `.planning/lessons.md` captures reusable patterns
- [ ] `walkthrough.md` "Planning Evidence" section references `.planning/` summary

### Metrics & Drift (v4.2)
- [ ] `evidence_metrics_collector.py` run with latest CI data
- [ ] `spec_drift_detector.py` run — 0 critical drifts
- [ ] `metrics_trend` section populated in Canonical YAML

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
| - | - | - | - |

---

> End of evidence_pack.md
