# Feature Breakdown: EPIC-XXX

> **Version**: 1.0.0
> **Status**: draft
> **Last Updated**: YYYY-MM-DD

---

## 0. Canonical Feature Breakdown (YAML)

```yaml
feature_breakdown:
  meta:
    epic_id: "EPIC-XXX"
    breakdown_id: "FBD-XXX"
    version: "1.0.0"
    status: "draft"  # draft | in_review | approved
    created_at: "YYYY-MM-DD"
    updated_at: "YYYY-MM-DD"

  decomposition_rationale:
    principles:
      - "Single responsibility per feature"
      - "Clear contract boundaries"
      - "Independent deployability"
      - "Team autonomy maximization"
    decisions:
      - decision_id: "FBD-DEC-001"
        description: "{{Decision description}}"
        rationale: "{{Why this decision was made}}"
        alternatives_considered:
          - "{{Alternative 1}}"
          - "{{Alternative 2}}"

  features:
    - feature_id: "FEAT-XXX"
      name: "{{Feature X Name}}"
      team_id: "TEAM-A"
      coverage_tier: "critical"
      priority: 1
      scope:
        in:
          - "{{In-scope item 1}}"
          - "{{In-scope item 2}}"
        out:
          - "{{Out-of-scope item 1}}"
      contracts_owned:
        - contract_id: "CT-API-01"
          name: "{{Contract name}}"
          type: "api"
        - contract_id: "CT-EVT-01"
          name: "{{Event contract name}}"
          type: "event"
      contracts_consumed:
        - contract_ref: "shared/contracts/api/auth_service.yaml"
          name: "Auth Service API"
          owner_team: "PLATFORM"
      estimated_complexity: "medium"  # low | medium | high
      estimated_story_points: 21
      tech_stack:
        - "TypeScript"
        - "Express.js"
        - "PostgreSQL"

    - feature_id: "FEAT-YYY"
      name: "{{Feature Y Name}}"
      team_id: "TEAM-A"
      coverage_tier: "standard"
      priority: 2
      scope:
        in:
          - "{{In-scope item 1}}"
        out:
          - "{{Out-of-scope item 1}}"
      contracts_owned:
        - contract_id: "CT-API-02"
          name: "{{Contract name}}"
          type: "api"
      contracts_consumed:
        - contract_ref: "specs/FEAT-XXX/contracts/openapi.yaml"
          name: "Feature X API"
          owner_team: "TEAM-A"
      estimated_complexity: "low"
      estimated_story_points: 13
      tech_stack:
        - "React"
        - "TypeScript"

    - feature_id: "FEAT-ZZZ"
      name: "{{Feature Z Name}}"
      team_id: "TEAM-B"
      coverage_tier: "standard"
      priority: 2
      scope:
        in:
          - "{{In-scope item 1}}"
        out:
          - "{{Out-of-scope item 1}}"
      contracts_owned: []
      contracts_consumed:
        - contract_ref: "shared/contracts/api/{{shared_contract}}.yaml"
          name: "{{Shared contract name}}"
          owner_team: "TEAM-A"
      estimated_complexity: "medium"
      estimated_story_points: 21
      tech_stack:
        - "Python"
        - "FastAPI"

  dependency_graph:
    nodes:
      - id: "FEAT-XXX"
        layer: 0  # 0 = foundation, higher = depends on lower
        team: "TEAM-A"
      - id: "FEAT-YYY"
        layer: 1
        team: "TEAM-A"
      - id: "FEAT-ZZZ"
        layer: 1
        team: "TEAM-B"
    edges:
      - edge_id: "E-001"
        from: "FEAT-YYY"
        to: "FEAT-XXX"
        type: "api_dependency"
        contract_id: "CT-API-01"
        criticality: "high"
        description: "Feature Y calls Feature X API for {{purpose}}"
      - edge_id: "E-002"
        from: "FEAT-ZZZ"
        to: "FEAT-XXX"
        type: "api_dependency"
        contract_id: "SC-API-XXX"
        criticality: "high"
        description: "Feature Z uses shared contract from Feature X"

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
        rate_limit: "1000 req/min"
      error_handling:
        retry_policy: "exponential_backoff"
        circuit_breaker: true
        fallback_behavior: "return_cached_or_error"

  cross_team_tests:
    - test_id: "TS-CROSS-001"
      name: "{{Cross-team test name}}"
      type: "integration"
      participating_features: ["FEAT-XXX", "FEAT-YYY"]
      owner_team: "TEAM-A"
      schedule: "nightly"
      environment: "staging"
      prerequisites:
        - "FEAT-XXX deployed to staging"
        - "FEAT-YYY deployed to staging"

  breakdown_gate_check:
    counts:
      total_features: 0           # 自動計算
      total_contracts_owned: 0    # 自動計算
      total_dependencies: 0       # 自動計算
      cross_team_dependencies: 0  # 自動計算
    rules:
      max_features_per_team: 5
      max_dependency_depth: 3
    no_dependency_cycles: false
    all_integration_points_defined: false
    coverage_tiers_assigned: false
    sla_defined_for_all_integration_points: false
    ready_for_feature_specs: false
```

---

## 1. Decomposition Rationale

### 1.1 Guiding Principles

1. **Single Responsibility**: 各Featureは単一の責務を持つ
2. **Clear Contract Boundaries**: 契約によって明確な境界を定義
3. **Independent Deployability**: 可能な限り独立してデプロイ可能
4. **Team Autonomy**: チームが自律的に開発・デプロイできる単位

### 1.2 Key Decisions

| Decision ID | Description | Rationale |
|-------------|-------------|-----------|
| FBD-DEC-001 | {{Decision}} | {{Rationale}} |

---

## 2. Feature Details

### 2.1 FEAT-XXX: {{Feature X Name}}

| 属性 | 値 |
|------|-----|
| **Team** | TEAM-A |
| **Coverage Tier** | critical |
| **Priority** | 1 |
| **Complexity** | medium |
| **Story Points** | 21 |

**Scope**:
- ✅ {{In-scope item 1}}
- ✅ {{In-scope item 2}}
- ❌ {{Out-of-scope item 1}}

**Contracts Owned**:
| Contract ID | Name | Type |
|-------------|------|------|
| CT-API-01 | {{Contract name}} | API |
| CT-EVT-01 | {{Event name}} | Event |

**Contracts Consumed**:
| Contract Ref | Name | Owner |
|--------------|------|-------|
| shared/contracts/api/auth_service.yaml | Auth Service | PLATFORM |

---

### 2.2 FEAT-YYY: {{Feature Y Name}}

| 属性 | 値 |
|------|-----|
| **Team** | TEAM-A |
| **Coverage Tier** | standard |
| **Priority** | 2 |
| **Complexity** | low |
| **Story Points** | 13 |

**Scope**:
- ✅ {{In-scope item 1}}
- ❌ {{Out-of-scope item 1}}

**Dependencies**:
- FEAT-XXX via CT-API-01

---

### 2.3 FEAT-ZZZ: {{Feature Z Name}}

| 属性 | 値 |
|------|-----|
| **Team** | TEAM-B |
| **Coverage Tier** | standard |
| **Priority** | 2 |
| **Complexity** | medium |
| **Story Points** | 21 |

**Scope**:
- ✅ {{In-scope item 1}}
- ❌ {{Out-of-scope item 1}}

**Dependencies**:
- FEAT-XXX via SC-API-XXX (shared contract)

---

## 3. Dependency Graph

### 3.1 Visual Representation

```
Layer 0 (Foundation):
┌─────────────────────────────────────────────┐
│                  FEAT-XXX                   │
│              (TEAM-A, critical)             │
│    Provides: CT-API-01, CT-EVT-01           │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
Layer 1:
┌───────────────┐     ┌───────────────┐
│   FEAT-YYY    │     │   FEAT-ZZZ    │
│   (TEAM-A)    │     │   (TEAM-B)    │
│   standard    │     │   standard    │
│ Uses: CT-API-01│     │Uses: SC-API-XXX│
└───────────────┘     └───────────────┘
```

### 3.2 Dependency Matrix

| From → To | FEAT-XXX | FEAT-YYY | FEAT-ZZZ |
|-----------|----------|----------|----------|
| **FEAT-XXX** | - | - | - |
| **FEAT-YYY** | CT-API-01 | - | - |
| **FEAT-ZZZ** | SC-API-XXX | - | - |

### 3.3 Cycle Analysis

- **Cycles Detected**: None ✅
- **Max Depth**: 1
- **Critical Path**: FEAT-XXX → FEAT-YYY/FEAT-ZZZ

---

## 4. Integration Points

### 4.1 IP-001: {{Integration Point Name}}

| 属性 | 値 |
|------|-----|
| **Type** | API |
| **Provider** | FEAT-XXX |
| **Consumers** | FEAT-YYY, FEAT-ZZZ |
| **Contract** | specs/FEAT-XXX/contracts/openapi.yaml |

**SLA**:
| Metric | Target |
|--------|--------|
| Availability | 99.9% |
| Latency (P99) | 200ms |
| Rate Limit | 1000 req/min |

**Error Handling**:
- Retry Policy: Exponential backoff
- Circuit Breaker: Enabled
- Fallback: Return cached or error

---

## 5. Cross-Team Tests

### 5.1 TS-CROSS-001: {{Test Name}}

| 属性 | 値 |
|------|-----|
| **Type** | Integration |
| **Participants** | FEAT-XXX, FEAT-YYY |
| **Owner** | TEAM-A |
| **Schedule** | Nightly |
| **Environment** | Staging |

**Prerequisites**:
- [ ] FEAT-XXX deployed to staging
- [ ] FEAT-YYY deployed to staging

---

## 6. Implementation Order

### 6.1 Recommended Sequence

```
Phase 1: Foundation
└─ FEAT-XXX (TEAM-A)
   └─ Contract: CT-API-01, CT-EVT-01
   └─ Shared: SC-API-XXX

Phase 2: Dependent Features (parallel)
├─ FEAT-YYY (TEAM-A)
│  └─ Waits for: CT-API-01 stable
└─ FEAT-ZZZ (TEAM-B)
   └─ Waits for: SC-API-XXX stable

Phase 3: Integration
└─ Cross-team integration test
└─ E2E validation
```

### 6.2 Parallel Work Opportunities

| TEAM-A | TEAM-B |
|--------|--------|
| FEAT-XXX (foundation) | Preparation, mock setup |
| FEAT-YYY + integration | FEAT-ZZZ development |
| Integration test (lead) | Integration test (participate) |

---

## 7. Appendix

### 7.1 Related Documents

- `epic_design.md` - Parent Epic設計
- `EPIC_APPROVAL.md` - Epic承認記録
- `dependency_map.yaml` - 依存関係詳細

### 7.2 Change Log

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| YYYY-MM-DD | 1.0.0 | {{Author}} | Initial breakdown |
