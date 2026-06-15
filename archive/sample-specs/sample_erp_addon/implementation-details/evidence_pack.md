# Evidence Pack - mcframe受注管理アドオン

Feature: FEAT-ERP-OMS
Last updated: 2026-02-10

---

## test_results

| Test Suite | Type | Total | Passed | Failed | Skipped |
|-----------|------|-------|--------|--------|---------|
| TS-CON-01 | contract | 8 | 8 | 0 | 0 |
| TS-CON-02 | contract | 5 | 5 | 0 | 0 |
| TS-INT-01 | integration | 12 | 12 | 0 | 0 |
| TS-INT-02 | integration | 6 | 6 | 0 | 0 |
| TS-INT-03 | integration | 9 | 9 | 0 | 0 |
| TS-INT-04 | integration | 7 | 7 | 0 | 0 |
| TS-E2E-01 | e2e | 3 | 3 | 0 | 0 |
| **Total** | | **50** | **50** | **0** | **0** |

---

## coverage_report

| Scope | Line % | Branch % | Target | Status |
|-------|--------|----------|--------|--------|
| LIB-01 (order-domain) | 91.2% | 82.3% | 85/75 | PASS |
| LIB-02 (authz-lib) | 88.5% | 79.1% | 85/75 | PASS |
| LIB-03 (mcframe-client) | 87.3% | 76.8% | 85/75 | PASS |
| CMP-01 (Order Web UI) | 72.1% | 58.4% | 60/50 | PASS |
| CMP-02 (Order API) | 78.9% | 64.2% | 60/50 | PASS |
| **Total** | **83.6%** | **72.2%** | **80** | **PASS** |

---

## gate_approvals

| Gate | Approver | Date | Status |
|------|----------|------|--------|
| Gate 1: Design Review | 田中太郎 | 2026-02-02 | Approved |
| Gate 2: BPMN Review | 田中太郎 | 2026-02-02 | Approved |
| Gate 3: Spec Review | 田中太郎 | 2026-02-02 | Approved |
| Gate 4: Plan Review | 鈴木次郎 | 2026-02-02 | Approved |
| Gate 5: Tasking Review | 鈴木次郎 | 2026-02-02 | Approved |
| Final: Evidence Review | (pending) | - | Pending |

---

## metrics_trend

```yaml
metrics_trend:
  coverage_history:
    - date: "2026-02-05"
      total_pct: 65.2
    - date: "2026-02-08"
      total_pct: 78.1
    - date: "2026-02-10"
      total_pct: 83.6
  test_execution_time_history:
    - date: "2026-02-05"
      duration_sec: 45
    - date: "2026-02-08"
      duration_sec: 38
    - date: "2026-02-10"
      duration_sec: 32
  cache_hit_rate_history:
    - date: "2026-02-10"
      rate_pct: 72.0
  gate_lead_time_hours: 192
```

---

## ai_provenance

| Run | Model | Prompt Version | Input Hash |
|-----|-------|---------------|------------|
| RUN-001 (WI-ERP-SAMPLE-001) | claude-opus-4 | sdd-templates v4.3.0 | sha256:a1b2c3 |
