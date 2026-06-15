# Contract Change Proposal: CCP-XXX

> **Status**: draft
> **Created**: YYYY-MM-DD
> **Review Deadline**: YYYY-MM-DD

---

## 0. Proposal Metadata (YAML)

```yaml
ccp:
  meta:
    proposal_id: "CCP-XXX"
    status: "draft"  # draft | review | approved | rejected | implemented | cancelled
    created_at: "YYYY-MM-DD"
    review_deadline: "YYYY-MM-DD"
    implementation_target: "YYYY-MM-DD"

  proposer:
    team_id: "TEAM-A"
    feature_id: "FEAT-XXX"
    author: "{{author@example.com}}"
    author_name: "{{Author Name}}"

  affected_contract:
    contract_ref: "specs/FEAT-XXX/contracts/openapi.yaml"
    contract_id: "CT-API-01"
    contract_name: "{{Contract Name}}"
    current_version: "1.0.0"
    proposed_version: "2.0.0"

  change_classification:
    type: "breaking"  # breaking | non_breaking | deprecation | sunset
    impact_scope: "cross_team"  # single_team | cross_team | organization
    urgency: "normal"  # emergency | high | normal | low
    reversible: false

  impact_analysis:
    consumers:
      - team_id: "TEAM-B"
        features: ["FEAT-YYY"]
        impact_level: "high"
        migration_required: true
        estimated_effort_days: 3
        acknowledged: false
        acknowledged_by: null
        acknowledged_at: null

      - team_id: "TEAM-C"
        features: ["FEAT-ZZZ"]
        impact_level: "medium"
        migration_required: true
        estimated_effort_days: 1
        acknowledged: false
        acknowledged_by: null
        acknowledged_at: null

  timeline:
    proposal_created: "YYYY-MM-DD"
    review_deadline: "YYYY-MM-DD"
    approval_target: "YYYY-MM-DD"
    deprecation_notice: "YYYY-MM-DD"
    new_version_release: "YYYY-MM-DD"
    migration_deadline: "YYYY-MM-DD"
    old_version_sunset: "YYYY-MM-DD"

  approvals:
    consumer_acknowledgments:
      required: true
      quorum: "all"  # all | majority
      status: "pending"
    arch_board:
      required: true
      status: "pending"
      approved_by: null
      approved_at: null
```

---

## 1. Summary

### 1.1 Change Overview

| 項目 | 内容 |
|------|------|
| **Contract** | CT-API-01 ({{Contract Name}}) |
| **Current Version** | 1.0.0 |
| **Proposed Version** | 2.0.0 |
| **Change Type** | Breaking Change |
| **Impact Scope** | Cross-team |

### 1.2 Brief Description

{{Brief description of the proposed change - 1-2 sentences}}

### 1.3 Motivation

{{Why is this change necessary? What problem does it solve?}}

---

## 2. Detailed Change Description

### 2.1 Current State

```yaml
# Current contract structure (relevant parts)
paths:
  /example:
    get:
      responses:
        200:
          schema:
            type: object
            properties:
              old_field:
                type: string
```

### 2.2 Proposed State

```yaml
# Proposed contract structure (relevant parts)
paths:
  /example:
    get:
      responses:
        200:
          schema:
            type: object
            properties:
              new_field:
                type: string
              # old_field: REMOVED
```

### 2.3 Breaking Changes Detail

| Change | Before | After | Breaking? |
|--------|--------|-------|-----------|
| Field `old_field` | Present | Removed | ✅ Yes |
| Field `new_field` | N/A | Added (required) | ✅ Yes |

---

## 3. Impact Analysis

### 3.1 Consumer Impact Summary

| Team | Features | Impact Level | Migration Required | Effort (days) |
|------|----------|--------------|-------------------|---------------|
| TEAM-B | FEAT-YYY | High | Yes | 3 |
| TEAM-C | FEAT-ZZZ | Medium | Yes | 1 |

### 3.2 TEAM-B Impact Details

**Affected Features**: FEAT-YYY

**Usage Points**:
- `src/services/feature_x_client.ts:42` - API call to `/example`
- `src/handlers/data_processor.ts:156` - Response parsing

**Migration Steps**:
1. Update response type definition
2. Update data processing logic
3. Update unit tests
4. Run integration tests

**Estimated Effort**: 3 days

### 3.3 TEAM-C Impact Details

**Affected Features**: FEAT-ZZZ

**Usage Points**:
- `src/integration/feature_x_adapter.py:89` - API call

**Migration Steps**:
1. Update response parsing
2. Run integration tests

**Estimated Effort**: 1 day

---

## 4. Migration Path

### 4.1 Migration Strategy

{{Describe the recommended migration approach}}

**Option A: Parallel Version Support (Recommended)**
1. Provider releases v2.0.0 alongside v1.0.0
2. Consumers migrate at their own pace
3. v1.0.0 sunset after migration deadline

**Option B: Big Bang Migration**
1. Coordinated release date
2. All consumers migrate simultaneously

### 4.2 Step-by-Step Migration Guide

#### For API Consumers:

1. **Update SDK/Client** (if applicable)
   ```bash
   npm install @team-a/feature-x-client@2.0.0
   ```

2. **Update Response Handling**
   ```typescript
   // Before
   const data = response.old_field;

   // After
   const data = response.new_field;
   ```

3. **Run Tests**
   ```bash
   npm test
   npm run test:integration
   ```

### 4.3 Rollback Plan

{{What happens if migration fails? How to roll back?}}

---

## 5. Timeline

```
Proposal Created         Review Deadline         Approval
      │                        │                    │
      ▼                        ▼                    ▼
──────┼────────────────────────┼────────────────────┼──────────────►
      │                        │                    │
  YYYY-MM-DD               YYYY-MM-DD          YYYY-MM-DD


Deprecation Notice    New Version Release    Migration Deadline    Sunset
      │                      │                      │                │
      ▼                      ▼                      ▼                ▼
──────┼──────────────────────┼──────────────────────┼────────────────┼──►
      │                      │                      │                │
  YYYY-MM-DD            YYYY-MM-DD             YYYY-MM-DD       YYYY-MM-DD
```

| Phase | Date | Description |
|-------|------|-------------|
| Proposal | YYYY-MM-DD | CCP created and submitted for review |
| Review Deadline | YYYY-MM-DD | All consumers must respond |
| Approval | YYYY-MM-DD | Architecture board decision |
| Deprecation Notice | YYYY-MM-DD | v1.0.0 marked deprecated |
| New Version Release | YYYY-MM-DD | v2.0.0 available |
| Migration Deadline | YYYY-MM-DD | All consumers must migrate |
| Sunset | YYYY-MM-DD | v1.0.0 removed |

---

## 6. Consumer Acknowledgments

> ⚠️ **CRITICAL**: This section must be completed by **human representatives** from each consuming team.

### 6.1 TEAM-B Acknowledgment

- [ ] We have reviewed the proposed changes
- [ ] We understand the impact on our features
- [ ] We commit to migrating by the migration deadline
- [ ] We have identified resources for migration

```
Team: TEAM-B
Acknowledged by: _____________________
Role: _____________________
Date: _____________________
Migration commitment date: _____________________
Notes: _____________________
```

### 6.2 TEAM-C Acknowledgment

- [ ] We have reviewed the proposed changes
- [ ] We understand the impact on our features
- [ ] We commit to migrating by the migration deadline
- [ ] We have identified resources for migration

```
Team: TEAM-C
Acknowledged by: _____________________
Role: _____________________
Date: _____________________
Migration commitment date: _____________________
Notes: _____________________
```

---

## 7. Architecture Board Approval

> ⚠️ **CRITICAL**: This section must be completed by the **Architecture Board**.

### 7.1 Review Checklist

- [ ] Impact analysis is complete and accurate
- [ ] All consuming teams have acknowledged
- [ ] Migration path is documented
- [ ] Timeline is reasonable
- [ ] Rollback plan is defined
- [ ] Breaking change justification is valid

### 7.2 Approval Decision

```
Decision: [ ] Approved  [ ] Rejected  [ ] Deferred
Approved by: _____________________
Role: Architecture Board
Date: _____________________
Conditions (if any): _____________________
Comments: _____________________
```

---

## 8. Implementation Tracking

### 8.1 Provider Tasks

| Task | Owner | Status | Due Date |
|------|-------|--------|----------|
| Implement v2.0.0 | TEAM-A | Pending | YYYY-MM-DD |
| Update documentation | TEAM-A | Pending | YYYY-MM-DD |
| Deploy to staging | TEAM-A | Pending | YYYY-MM-DD |
| Release to production | TEAM-A | Pending | YYYY-MM-DD |
| Mark v1.0.0 deprecated | TEAM-A | Pending | YYYY-MM-DD |
| Sunset v1.0.0 | TEAM-A | Pending | YYYY-MM-DD |

### 8.2 Consumer Migration Status

| Team | Feature | Migration Status | Completed Date |
|------|---------|------------------|----------------|
| TEAM-B | FEAT-YYY | Not Started | - |
| TEAM-C | FEAT-ZZZ | Not Started | - |

---

## 9. Appendix

### 9.1 Related Documents

- Original contract: `specs/FEAT-XXX/contracts/openapi.yaml`
- Migration guide: `docs/migrations/CT-API-01-v2.md`
- Integration tests: `specs/FEAT-XXX/tests/contract/`

### 9.2 Change Log

| Date | Author | Changes |
|------|--------|---------|
| YYYY-MM-DD | {{Author}} | Initial CCP draft |

---

## ⚠️ AI Agent Notice

> **絶対禁止**: AIエージェントは以下を行ってはならない:
> - Consumer Acknowledgmentセクションのチェックボックスを設定
> - 承認者名・日付を記入
> - Architecture Board Approvalセクションを編集
> - 承認プロセスを回避する方法を提案
