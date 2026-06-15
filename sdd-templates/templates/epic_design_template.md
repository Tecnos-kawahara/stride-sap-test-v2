# Epic Design: EPIC-XXX - {{Epic Title}}

> **Version**: 1.0.0
> **Status**: draft
> **Last Updated**: YYYY-MM-DD

---

## 0. Canonical Epic Design (YAML)

```yaml
epic:
  meta:
    epic_id: "EPIC-XXX"
    title: "{{Epic Title}}"
    version: "1.0.0"
    status: "draft"  # draft | in_review | approved | deprecated
    created_at: "YYYY-MM-DD"
    updated_at: "YYYY-MM-DD"

  ownership:
    sponsor: "{{Sponsor Name}}"
    epic_lead: "{{Epic Lead Name}}"
    teams:
      - team_id: "TEAM-A"
        name: "{{Team A Name}}"
        lead: "{{Team A Lead}}"
        features:
          - "FEAT-XXX"
          - "FEAT-YYY"
      - team_id: "TEAM-B"
        name: "{{Team B Name}}"
        lead: "{{Team B Lead}}"
        features:
          - "FEAT-ZZZ"

  scope:
    business_context:
      who: "{{Primary stakeholders / end users}}"
      what: "{{What the Epic delivers}}"
      why: "{{Business value / strategic alignment}}"
    value_stream: "{{e.g., O2C, P2P, Record-to-Report}}"
    strategic_alignment:
      - "{{Strategic initiative 1}}"
      - "{{Strategic initiative 2}}"
    out_of_scope:
      - "{{Explicitly excluded item 1}}"
      - "{{Explicitly excluded item 2}}"

  features:
    - feature_id: "FEAT-XXX"
      name: "{{Feature X Name}}"
      team_id: "TEAM-A"
      coverage_tier: "critical"  # critical | standard | experimental
      priority: 1
      dependencies: []
      description: "{{Brief description}}"

    - feature_id: "FEAT-YYY"
      name: "{{Feature Y Name}}"
      team_id: "TEAM-A"
      coverage_tier: "standard"
      priority: 2
      dependencies:
        - "FEAT-XXX"
      description: "{{Brief description}}"

    - feature_id: "FEAT-ZZZ"
      name: "{{Feature Z Name}}"
      team_id: "TEAM-B"
      coverage_tier: "standard"
      priority: 2
      dependencies:
        - "FEAT-XXX"
      description: "{{Brief description}}"

  shared_contracts:
    - contract_ref: "shared/contracts/api/{{contract_name}}.yaml"
      contract_id: "SC-API-XXX"
      name: "{{Shared Contract Name}}"
      owner_team: "TEAM-A"
      owner_feature: "FEAT-XXX"
      consumers:
        - team_id: "TEAM-B"
          features: ["FEAT-ZZZ"]
      type: "api"  # api | event | file | schema

  cross_team_dependencies:
    - dependency_id: "DEP-001"
      from_feature: "FEAT-YYY"
      to_feature: "FEAT-XXX"
      type: "blocking"  # blocking | soft
      interface: "CT-API-01"
      description: "{{Dependency description}}"

    - dependency_id: "DEP-002"
      from_feature: "FEAT-ZZZ"
      to_feature: "FEAT-XXX"
      type: "blocking"
      interface: "SC-API-XXX"
      description: "{{Dependency description}}"

  milestones:
    - id: "EM-01"
      name: "{{Milestone 1 Name}}"
      target_date: "YYYY-MM-DD"
      features: ["FEAT-XXX"]
      exit_criteria:
        - "{{Exit criterion 1}}"
        - "{{Exit criterion 2}}"

    - id: "EM-02"
      name: "{{Milestone 2 Name}}"
      target_date: "YYYY-MM-DD"
      features: ["FEAT-YYY", "FEAT-ZZZ"]
      exit_criteria:
        - "{{Exit criterion 1}}"

  integration_points:
    - point_id: "IP-001"
      name: "{{Integration Point Name}}"
      type: "api"  # api | event | file | database
      provider_feature: "FEAT-XXX"
      consumer_features: ["FEAT-YYY", "FEAT-ZZZ"]
      contract_ref: "specs/FEAT-XXX/contracts/openapi.yaml"
      sla:
        availability: "99.9%"
        latency_p99: "200ms"
      test_strategy: "contract_test + integration_test"

  risks:
    - risk_id: "ER-001"
      description: "{{Risk description}}"
      probability: "medium"  # low | medium | high
      impact: "high"  # low | medium | high
      mitigation: "{{Mitigation strategy}}"
      owner: "TEAM-A"

  # v3.0: Team Capacity & Critical Path
  team_capacity:
    - team_id: "TEAM-A"
      allocated_members: 0       # チーム人数
      effort_points: 0           # 見積りストーリーポイント
      start_date: "YYYY-MM-DD"
      end_date: "YYYY-MM-DD"
    - team_id: "TEAM-B"
      allocated_members: 0
      effort_points: 0
      start_date: "YYYY-MM-DD"
      end_date: "YYYY-MM-DD"

  critical_path:
    - milestone_id: "EM-01"
      dependent_features: ["FEAT-XXX"]
      target_date: "YYYY-MM-DD"
      status: "on_track"  # on_track | at_risk | blocked
    - milestone_id: "EM-02"
      dependent_features: ["FEAT-YYY", "FEAT-ZZZ"]
      target_date: "YYYY-MM-DD"
      status: "pending"

  # v3.0: Shared Contract Manifest
  shared_contract_manifest:
    - contract_id: "SC-API-XXX"
      type: "api"
      owner_team: "TEAM-A"
      consumers:
        - team_id: "TEAM-B"
          adoption_status: "planned"  # planned | in_development | stable | deprecated
      version_constraint: ">= 1.0.0"

  # EPIC Flow BPMN 業務記述正本
  epic_flow_descriptions:
    overview:
      purpose: "{{Epic の全体業務フロー概要}}"
      scope: "{{Epic のスコープ}}"
      out_of_scope: "{{スコープ外}}"
    participants:
      - participant_id: "Participant_A"
        name: "{{Participant A Name}}"
        role: "{{internal_team / external_system / partner}}"
        responsibility: "{{責務概要}}"
        owner: "TEAM-A"
      - participant_id: "Participant_B"
        name: "{{Participant B Name}}"
        role: "{{internal_team / external_system / partner}}"
        responsibility: "{{責務概要}}"
        owner: "TEAM-B"
    message_flows:
      - message_flow_id: "MsgFlow_AtoB"
        summary: "{{メッセージフロー概要}}"
        payload: "{{送受信データ}}"
        contract_ref: ""
        dependency_ref: ""
        sla: ""
        business_expectation: "{{業務上の期待}}"
      - message_flow_id: "MsgFlow_BtoA"
        summary: "{{メッセージフロー概要}}"
        payload: "{{送受信データ}}"
        contract_ref: ""
        dependency_ref: ""
        sla: ""
        business_expectation: "{{業務上の期待}}"

  # v3.0: Progress Tracking Configuration
  progress_tracking:
    reporting_frequency: "weekly"    # daily | weekly | biweekly
    dashboard_auto_generate: true
    blocker_escalation_sla_hours: 24
    team_status_report_required: true
    artifacts:
      epic_progress_report: "epics/EPIC-XXX/EPIC_PROGRESS_REPORT.md"
      epic_flow_bpmn: "epics/EPIC-XXX/epic_flow.bpmn"
      dependency_manifest: "epics/EPIC-XXX/DEPENDENCY_MANIFEST.yaml"
      contract_registry: "shared/contracts/CONTRACT_REGISTRY.yaml"
      ops_pack_registry: "epics/EPIC-XXX/OPS_PACK_REGISTRY.yaml"

  epic_gate_check:
    counts:
      total_features: 0      # 自動計算
      critical_features: 0   # 自動計算
      standard_features: 0   # 自動計算
      experimental_features: 0  # 自動計算
      cross_team_dependencies: 0  # 自動計算
      shared_contracts: 0    # 自動計算
    rules:
      min_features: 2
      max_critical_per_epic: 5
      max_teams: 5
    all_features_have_team: false
    all_dependencies_mapped: false
    shared_contracts_defined: false
    no_dependency_cycles: false
    ready_for_feature_specs: false
```

---

## 1. Executive Summary

### 1.1 Business Context

| 項目 | 内容 |
|------|------|
| **WHO** | {{Primary stakeholders, end users}} |
| **WHAT** | {{What the Epic delivers}} |
| **WHY** | {{Business value, strategic alignment}} |
| **VALUE STREAM** | {{e.g., Order-to-Cash, Procure-to-Pay}} |

### 1.2 Strategic Alignment

- {{Strategic initiative 1}}
- {{Strategic initiative 2}}

### 1.3 Success Criteria

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| {{KPI 1}} | {{Target}} | {{Measurement method}} |
| {{KPI 2}} | {{Target}} | {{Measurement method}} |

---

## 2. Team Organization

### 2.1 Team Structure

```
Epic Lead: {{Epic Lead Name}}
│
├─ TEAM-A: {{Team A Name}}
│   ├─ Lead: {{Team A Lead}}
│   ├─ Features: FEAT-XXX, FEAT-YYY
│   └─ Responsibilities: {{Key responsibilities}}
│
└─ TEAM-B: {{Team B Name}}
    ├─ Lead: {{Team B Lead}}
    ├─ Features: FEAT-ZZZ
    └─ Responsibilities: {{Key responsibilities}}
```

### 2.2 RACI Matrix

| Activity | TEAM-A | TEAM-B | Epic Lead | ARCH_BOARD |
|----------|--------|--------|-----------|------------|
| Epic Design Approval | C | C | R | A |
| Feature Breakdown | R | R | A | I |
| Shared Contract Definition | R | C | A | I |
| Cross-team Integration Test | R | R | A | I |
| Final Integration | C | C | R | A |

---

## 3. Feature Breakdown

### 3.1 Feature Overview

| Feature ID | Name | Team | Coverage Tier | Priority | Dependencies |
|------------|------|------|---------------|----------|--------------|
| FEAT-XXX | {{Name}} | TEAM-A | critical | 1 | - |
| FEAT-YYY | {{Name}} | TEAM-A | standard | 2 | FEAT-XXX |
| FEAT-ZZZ | {{Name}} | TEAM-B | standard | 2 | FEAT-XXX |

### 3.2 Dependency Graph

```
FEAT-XXX (Foundation)
    │
    ├──► FEAT-YYY (depends via CT-API-01)
    │
    └──► FEAT-ZZZ (depends via SC-API-XXX)
```

### 3.3 Coverage Tier Rationale

| Feature | Tier | Rationale |
|---------|------|-----------|
| FEAT-XXX | critical | {{Rationale for critical tier}} |
| FEAT-YYY | standard | {{Rationale for standard tier}} |
| FEAT-ZZZ | standard | {{Rationale for standard tier}} |

---

## 4. Shared Contracts

### 4.1 Contract Registry

| Contract ID | Name | Type | Owner | Consumers |
|-------------|------|------|-------|-----------|
| SC-API-XXX | {{Name}} | API | TEAM-A | TEAM-B |

### 4.2 Contract Change Protocol

1. 契約オーナーがCCP（Contract Change Proposal）を作成
2. 影響分析を自動生成
3. 消費者チームに通知
4. 消費者チームが確認・承認
5. ARCH_BOARD最終承認（breaking changeの場合）
6. 実装・移行

---

## 5. Milestones

### 5.1 Timeline

```
EM-01: {{Milestone 1}}          EM-02: {{Milestone 2}}
    │                               │
    ▼                               ▼
────┼───────────────────────────────┼────────────────►
    │                               │
    FEAT-XXX complete               FEAT-YYY, FEAT-ZZZ complete
```

### 5.2 Milestone Details

#### EM-01: {{Milestone 1 Name}}

- **Target Date**: YYYY-MM-DD
- **Features**: FEAT-XXX
- **Exit Criteria**:
  - [ ] {{Exit criterion 1}}
  - [ ] {{Exit criterion 2}}

#### EM-02: {{Milestone 2 Name}}

- **Target Date**: YYYY-MM-DD
- **Features**: FEAT-YYY, FEAT-ZZZ
- **Exit Criteria**:
  - [ ] {{Exit criterion 1}}

---

## 6. Integration Strategy

### 6.1 Integration Points

| Point ID | Type | Provider | Consumers | Contract |
|----------|------|----------|-----------|----------|
| IP-001 | API | FEAT-XXX | FEAT-YYY, FEAT-ZZZ | openapi.yaml |

### 6.2 Integration Test Strategy

- **Contract Tests**: Provider側で実装、CI/CDで自動実行
- **Integration Tests**: 夜間バッチでstaging環境にて実行
- **Cross-team E2E**: マイルストーン前にepic_leadが調整

---

## 7. Risks & Mitigations

| Risk ID | Description | Probability | Impact | Mitigation | Owner |
|---------|-------------|-------------|--------|------------|-------|
| ER-001 | {{Risk}} | Medium | High | {{Mitigation}} | TEAM-A |

---

## 8. Team Capacity & Progress Tracking (v3.0)

### 8.1 Team Capacity

| Team | Members | Effort (SP) | Start | End | Utilization |
|------|---------|-------------|-------|-----|-------------|
| TEAM-A | 0 | 0 | YYYY-MM-DD | YYYY-MM-DD | - |
| TEAM-B | 0 | 0 | YYYY-MM-DD | YYYY-MM-DD | - |

### 8.2 Critical Path

```
EM-01 (YYYY-MM-DD)          EM-02 (YYYY-MM-DD)
  │ FEAT-XXX                  │ FEAT-YYY, FEAT-ZZZ
  ▼                           ▼
──┼───────────────────────────┼──────────────────►
  [TEAM-A]                    [TEAM-A, TEAM-B]
```

### 8.3 Progress Tracking Artifacts

| Artifact | Location | Update Frequency | Owner |
|----------|----------|------------------|-------|
| EPIC_PROGRESS_REPORT.md | `epics/EPIC-XXX/` | Weekly | PM/Epic Lead |
| TEAM_STATUS_<TEAM_ID>.md | `epics/EPIC-XXX/` | Weekly | Team Leads |
| DEPENDENCY_MANIFEST.yaml | `epics/EPIC-XXX/` | On change | Epic Lead |
| CONTRACT_REGISTRY.yaml | `shared/contracts/` | On CCP approval | Epic Lead |
| OPS_PACK_REGISTRY.yaml | `epics/EPIC-XXX/` | Per WI completion | Team Leads |
| epic_flow.bpmn | `epics/EPIC-XXX/` | On architecture change | Epic Lead |

### 8.4 Reporting Cadence

- **Daily**: `epic_progress_aggregator.py` でターミナル確認（PM）
- **Weekly**: EPIC_PROGRESS_REPORT.md 更新 + チームステータスレポート収集
- **Milestone**: Epic Progress Gate チェック + ステアリング会議
- **Go-Live前**: Ops Pack 100%確認 + Final Integration Test

---

## 9. Open Questions

| ID | Question | Status | Assigned To | Due Date |
|----|----------|--------|-------------|----------|
| EQ-001 | {{Question}} | open | {{Person}} | YYYY-MM-DD |

---

## 9. Appendix

### 9.1 Related Documents

- `feature_breakdown.md` - 詳細なFeature分割
- `EPIC_APPROVAL.md` - Epic承認記録
- `dependency_map.yaml` - 依存関係マップ

### 9.2 Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| YYYY-MM-DD | 1.0.0 | {{Author}} | Initial draft |
