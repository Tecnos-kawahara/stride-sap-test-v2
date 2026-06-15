# Team Status Report: {{TEAM_ID}} - {{Team Name}}

> **Report Date**: {{DATE}}
> **Sprint/Period**: {{PERIOD_NAME}}
> **Team Lead**: {{Team Lead Name}}
> **Epic**: {{EPIC_ID}}

---

## 0. Canonical Report Data (YAML)

```yaml
team_status_report:
  meta:
    team_id: "{{TEAM_ID}}"
    team_name: "{{Team Name}}"
    team_lead: "{{Team Lead Name}}"
    epic_id: "{{EPIC_ID}}"
    report_date: "{{DATE}}"
    period: "{{PERIOD_NAME}}"
    version: "1.0.0"

  # Overall team health
  health:
    status: "on_track"  # on_track | at_risk | blocked
    summary: "{{Brief overall team status}}"

  # Feature gate status for all features owned by this team
  my_features:
    - feature_id: "{{FEATURE_ID}}"
      name: "{{Feature Name}}"
      coverage_tier: "critical"  # critical | standard | experimental
      current_phase: "Specify"   # Design | Specify | Tasking | Execute | Complete
      gates:
        gate_1_design: "approved"     # not_started | in_progress | approved | blocked
        gate_2_bpmn: "approved"       # not_started | in_progress | approved | blocked
        gate_3_spec: "in_progress"    # not_started | in_progress | approved | blocked
        gate_4_plan: "not_started"    # not_started | in_progress | approved | blocked
        gate_5_tasks: "not_started"   # not_started | in_progress | approved | blocked
        final_gate: "not_started"     # not_started | in_progress | approved | blocked
      health: "on_track"  # on_track | at_risk | blocked
      notes: "{{Feature-specific status notes}}"

  # Work item status roll-up
  work_items:
    summary:
      total: 0
      pending: 0
      in_progress: 0
      done: 0
      blocked: 0
    items:
      - wi_id: "WI-ERP-{{FEATURE_ID}}-001"
        title: "{{WI Title}}"
        feature_id: "{{FEATURE_ID}}"
        status: "pending"      # pending | in_progress | done | blocked
        mode: "autopilot"      # autopilot | confirm | validate
        complexity: "medium"   # low | medium | high
        assignee: "{{Assignee}}"
        started_at: ""         # YYYY-MM-DD or empty
        completed_at: ""       # YYYY-MM-DD or empty
        notes: ""

  # Dependencies this team provides to other teams
  dependencies_i_provide:
    - dependency_id: "DEP-001"
      to_team: "{{TEAM_ID}}"
      to_feature: "{{FEATURE_ID}}"
      interface_ref: "{{Contract or interface ID}}"
      status: "in_progress"    # not_started | in_progress | delivered | blocked
      scheduled_date: "YYYY-MM-DD"
      actual_date: ""          # filled when delivered
      notes: "{{Status details}}"

  # Dependencies this team consumes from other teams
  dependencies_i_consume:
    - dependency_id: "DEP-002"
      from_team: "{{TEAM_ID}}"
      from_feature: "{{FEATURE_ID}}"
      interface_ref: "{{Contract or interface ID}}"
      status: "pending"        # pending | available | adopted | blocked
      expected_date: "YYYY-MM-DD"
      notes: "{{Status details}}"

  # Active blockers for this team
  blockers:
    - blocker_id: "BLK-001"
      feature_id: "{{FEATURE_ID}}"
      wi_id: "{{WI_ID or empty}}"
      description: "{{Blocker description}}"
      severity: "high"         # low | medium | high | critical
      raised_date: "{{DATE}}"
      blocking_type: "internal"  # internal | cross_team | external
      blocked_by_team: ""      # TEAM_ID if cross_team, else empty
      owner: "{{Person responsible}}"
      status: "open"           # open | in_progress | resolved
      target_resolution_date: "YYYY-MM-DD"

  # Risks identified by this team
  risks:
    - risk_id: "TR-001"
      description: "{{Risk description}}"
      probability: "medium"    # low | medium | high
      impact: "high"           # low | medium | high
      mitigation: "{{Mitigation plan}}"
      status: "open"           # open | mitigating | mitigated | accepted | closed
      escalated_to_epic: false

  # Resource status
  resource_status:
    team_size: 0
    available: 0               # members currently available
    on_leave: 0                # members on leave/PTO
    capacity_pct: 100          # effective capacity percentage (0-100)
    notes: "{{Resource-related notes, e.g., 'One member joining next sprint'}}"

  # Period accomplishments and next-period plan
  accomplishments:
    - "{{What was completed this period}}"
  next_period_plan:
    - "{{What is planned for next period}}"
```

---

## 1. Team Health: {{on_track / at_risk / blocked}}

{{Brief overall team status}}

---

## 2. My Features (Gate Status)

| Feature ID | Name | Tier | Phase | G1 | G2 | G3 | G4 | G5 | Final | Health |
|------------|------|------|-------|----|----|----|----|----|-------|--------|
| {{FEATURE_ID}} | {{Name}} | critical | Specify | approved | approved | in_progress | - | - | - | on_track |

---

## 3. Work Items

### 3.1 Summary

| Status | Count |
|--------|-------|
| Total | 0 |
| Pending | 0 |
| In Progress | 0 |
| Done | 0 |
| Blocked | 0 |

### 3.2 Work Item Details

| WI ID | Title | Feature | Status | Mode | Complexity | Assignee |
|-------|-------|---------|--------|------|------------|----------|
| WI-ERP-{{FEATURE_ID}}-001 | {{Title}} | {{FEATURE_ID}} | pending | autopilot | medium | {{Assignee}} |

---

## 4. Dependencies I Provide

| DEP ID | To Team | To Feature | Interface | Status | Scheduled | Actual |
|--------|---------|------------|-----------|--------|-----------|--------|
| DEP-001 | {{TEAM_ID}} | {{FEATURE_ID}} | {{Ref}} | in_progress | YYYY-MM-DD | - |

---

## 5. Dependencies I Consume

| DEP ID | From Team | From Feature | Interface | Status | Expected |
|--------|-----------|--------------|-----------|--------|----------|
| DEP-002 | {{TEAM_ID}} | {{FEATURE_ID}} | {{Ref}} | pending | YYYY-MM-DD |

---

## 6. Blockers

| Blocker ID | Feature | Description | Severity | Type | Blocked By | Status | Target Resolution |
|------------|---------|-------------|----------|------|------------|--------|-------------------|
| BLK-001 | {{FEATURE_ID}} | {{Description}} | high | internal | - | open | YYYY-MM-DD |

---

## 7. Risks

| Risk ID | Description | Prob | Impact | Mitigation | Status | Escalated |
|---------|-------------|------|--------|------------|--------|-----------|
| TR-001 | {{Risk}} | medium | high | {{Mitigation}} | open | No |

---

## 8. Resource Status

| Metric | Value |
|--------|-------|
| Team Size | 0 |
| Available | 0 |
| On Leave | 0 |
| Capacity | 100% |

{{Resource-related notes}}

---

## 9. Accomplishments (This Period)

- {{What was completed}}

---

## 10. Plan (Next Period)

- {{What is planned}}

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| {{DATE}} | {{Author}} | Initial report |
