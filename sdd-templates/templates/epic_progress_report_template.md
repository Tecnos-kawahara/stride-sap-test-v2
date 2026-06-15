# Epic Progress Report: {{EPIC_ID}} - {{Epic Title}}

> **Report Date**: {{DATE}}
> **Report Period**: {{PERIOD_START}} ~ {{PERIOD_END}}
> **Status**: on_track
> **Author**: {{Epic Lead Name}}

---

## 0. Canonical Report Data (YAML)

```yaml
epic_progress_report:
  meta:
    epic_id: "{{EPIC_ID}}"
    title: "{{Epic Title}}"
    report_date: "{{DATE}}"
    period_start: "{{PERIOD_START}}"
    period_end: "{{PERIOD_END}}"
    status: "on_track"  # on_track | at_risk | blocked | completed
    author: "{{Epic Lead Name}}"
    version: "1.0.0"

  executive_summary:
    overall_health: "on_track"  # on_track | at_risk | blocked | completed
    key_highlights:
      - "{{Highlight 1}}"
      - "{{Highlight 2}}"
    key_concerns:
      - "{{Concern 1 or 'None'}}"
    decisions_needed:
      - "{{Decision needed or 'None'}}"

  # Team-level status roll-up
  team_status:
    - team_id: "{{TEAM_ID}}"
      name: "{{Team Name}}"
      lead: "{{Team Lead}}"
      health: "on_track"  # on_track | at_risk | blocked
      features_assigned: 0       # total features assigned to this team
      features_completed: 0      # features that passed Final Gate
      features_in_progress: 0    # features currently being worked on
      features_not_started: 0    # features not yet started
      blockers_count: 0          # active blockers for this team
      summary: "{{Brief team status narrative}}"

  # Gate completion across all features
  gate_completion_matrix:
    - feature_id: "{{FEATURE_ID}}"
      team_id: "{{TEAM_ID}}"
      feature_name: "{{Feature Name}}"
      coverage_tier: "critical"  # critical | standard | experimental
      gates:
        gate_1_design: "approved"     # not_started | in_progress | approved | blocked
        gate_2_bpmn: "approved"       # not_started | in_progress | approved | blocked
        gate_3_spec: "in_progress"    # not_started | in_progress | approved | blocked
        gate_4_plan: "not_started"    # not_started | in_progress | approved | blocked
        gate_5_tasks: "not_started"   # not_started | in_progress | approved | blocked
        final_gate: "not_started"     # not_started | in_progress | approved | blocked
      current_phase: "Specify"        # Design | Specify | Tasking | Execute | Complete
      notes: "{{Any notes about this feature's progress}}"

  # Milestone tracking
  milestone_progress:
    - milestone_id: "EM-01"
      name: "{{Milestone Name}}"
      target_date: "YYYY-MM-DD"
      status: "on_track"  # on_track | at_risk | missed | completed
      completion_pct: 0            # 0-100 percentage
      features_included:
        - feature_id: "{{FEATURE_ID}}"
          status: "in_progress"    # not_started | in_progress | completed
      notes: "{{Milestone status narrative}}"

  # Cross-team dependency status
  cross_team_dependencies:
    - dependency_id: "DEP-001"
      from_feature: "{{FEATURE_ID}}"
      to_feature: "{{FEATURE_ID}}"
      type: "blocking"       # blocking | soft
      status: "pending"      # pending | in_progress | resolved | blocked
      provided_by_team: "{{TEAM_ID}}"
      consumed_by_team: "{{TEAM_ID}}"
      interface_ref: "{{Contract or interface ID}}"
      scheduled_date: "YYYY-MM-DD"
      actual_date: ""        # filled when resolved
      notes: "{{Dependency status details}}"

  # Shared contract status
  shared_contract_status:
    - contract_id: "SC-API-XXX"
      name: "{{Contract Name}}"
      owner_team: "{{TEAM_ID}}"
      version: "1.0.0"
      status: "draft"        # draft | review | published | deprecated
      consumers_adopted: 0   # count of consumers that have adopted
      consumers_total: 0     # total consumers registered
      breaking_changes_pending: 0

  # Risk register (epic-level)
  risk_register:
    - risk_id: "ER-001"
      description: "{{Risk description}}"
      probability: "medium"  # low | medium | high
      impact: "high"         # low | medium | high
      status: "open"         # open | mitigating | mitigated | accepted | closed
      mitigation: "{{Mitigation strategy}}"
      owner_team: "{{TEAM_ID}}"
      escalated: false       # true if escalated to sponsor
      last_updated: "{{DATE}}"

  # Active blockers
  blocker_list:
    - blocker_id: "BLK-001"
      feature_id: "{{FEATURE_ID}}"
      team_id: "{{TEAM_ID}}"
      description: "{{Blocker description}}"
      severity: "high"       # low | medium | high | critical
      raised_date: "{{DATE}}"
      owner: "{{Person responsible for resolution}}"
      status: "open"         # open | in_progress | resolved
      resolution: ""         # filled when resolved
      target_resolution_date: "YYYY-MM-DD"

  # Key decisions made during this period
  key_decisions:
    - decision_id: "RPT-DR-001"
      date: "{{DATE}}"
      description: "{{Decision description}}"
      rationale: "{{Why this decision was made}}"
      impact: "{{Impact on teams/features}}"
      decided_by: "{{Person or board}}"
      affected_teams:
        - "{{TEAM_ID}}"

  # Actions for next period
  next_period_actions:
    - action_id: "ACT-001"
      description: "{{Action item}}"
      owner: "{{Person or team}}"
      due_date: "YYYY-MM-DD"
      priority: "high"       # low | medium | high
      related_feature: "{{FEATURE_ID}}"  # optional

  # Report metrics summary
  report_metrics:
    total_features: 0
    features_completed: 0
    features_on_track: 0
    features_at_risk: 0
    features_blocked: 0
    open_blockers: 0
    open_risks: 0
    dependencies_resolved: 0
    dependencies_pending: 0
    overall_completion_pct: 0  # 0-100
```

---

## 1. Executive Summary

### 1.1 Overall Health: {{on_track / at_risk / blocked / completed}}

**Key Highlights**:
- {{Highlight 1}}
- {{Highlight 2}}

**Key Concerns**:
- {{Concern or "None"}}

**Decisions Needed**:
- {{Decision needed or "None"}}

---

## 2. Team Status

| Team ID | Team Name | Lead | Health | Features (Done/Total) | Blockers | Summary |
|---------|-----------|------|--------|-----------------------|----------|---------|
| {{TEAM_ID}} | {{Name}} | {{Lead}} | on_track | 0/0 | 0 | {{Brief status}} |

---

## 3. Gate Completion Matrix

| Feature ID | Team | Tier | Gate 1 | Gate 2 | Gate 3 | Gate 4 | Gate 5 | Final | Phase |
|------------|------|------|--------|--------|--------|--------|--------|-------|-------|
| {{FEATURE_ID}} | {{TEAM_ID}} | critical | approved | approved | in_progress | - | - | - | Specify |

---

## 4. Milestone Progress

| Milestone | Target Date | Status | Completion | Features | Notes |
|-----------|-------------|--------|------------|----------|-------|
| EM-01: {{Name}} | YYYY-MM-DD | on_track | 0% | {{FEATURE_ID}} | {{Notes}} |

---

## 5. Cross-Team Dependencies

| DEP ID | From | To | Type | Status | Provider | Consumer | Scheduled | Actual |
|--------|------|----|------|--------|----------|----------|-----------|--------|
| DEP-001 | {{FEAT}} | {{FEAT}} | blocking | pending | {{TEAM}} | {{TEAM}} | YYYY-MM-DD | - |

---

## 6. Risk Register

| Risk ID | Description | Prob | Impact | Status | Mitigation | Owner | Escalated |
|---------|-------------|------|--------|--------|------------|-------|-----------|
| ER-001 | {{Risk}} | medium | high | open | {{Mitigation}} | {{TEAM_ID}} | No |

---

## 7. Blocker List

| Blocker ID | Feature | Team | Description | Severity | Raised | Owner | Target Resolution |
|------------|---------|------|-------------|----------|--------|-------|-------------------|
| BLK-001 | {{FEATURE_ID}} | {{TEAM_ID}} | {{Description}} | high | {{DATE}} | {{Owner}} | YYYY-MM-DD |

---

## 8. Key Decisions

| Decision ID | Date | Description | Rationale | Affected Teams |
|-------------|------|-------------|-----------|----------------|
| RPT-DR-001 | {{DATE}} | {{Description}} | {{Rationale}} | {{TEAM_ID}} |

---

## 9. Next Period Actions

| Action ID | Description | Owner | Due Date | Priority | Related Feature |
|-----------|-------------|-------|----------|----------|-----------------|
| ACT-001 | {{Action}} | {{Owner}} | YYYY-MM-DD | high | {{FEATURE_ID}} |

---

## 10. Metrics Summary

| Metric | Value |
|--------|-------|
| Total Features | 0 |
| Features Completed | 0 |
| Features On Track | 0 |
| Features At Risk | 0 |
| Features Blocked | 0 |
| Open Blockers | 0 |
| Open Risks | 0 |
| Dependencies Resolved | 0 |
| Dependencies Pending | 0 |
| Overall Completion | 0% |

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| {{DATE}} | {{Author}} | Initial report |
