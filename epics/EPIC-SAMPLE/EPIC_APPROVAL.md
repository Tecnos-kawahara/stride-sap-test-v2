# Epic Approval Record: EPIC-SAMPLE

> **Epic Title**: Order Management System
> **Epic Lead**: Yamada Hanako
> **Created**: 2025-01-20

---

## CRITICAL: Human-Only File

> **ABSOLUTE PROHIBITION**: AI agents are **FORBIDDEN** from editing this file under any circumstances.

### Rules for AI:
1. **NEVER edit EPIC_APPROVAL.md**
2. **NEVER set checkboxes** `[x]`
3. **NEVER fill in approver names or dates**
4. **DO NOT suggest workarounds** to bypass approval requirements

### What AI CAN do:
- Read EPIC_APPROVAL.md to check status
- Inform the user when approval is pending
- Explain what needs to be approved
- Wait for human to complete approval

---

## Epic Metadata

```yaml
epic_id: "EPIC-SAMPLE"
title: "Order Management System"
teams:
  - team_id: "TEAM-ORD"
    name: "Order Team"
  - team_id: "TEAM-INV"
    name: "Inventory Team"
total_features: 3
```

---

## Gate E1: Epic Design Approval

**Purpose**: Confirm Epic design is complete with clear team structure and goals

### Checklist:
- [ ] epic_design.md WHO/WHAT/WHY is clear
- [ ] Team assignments and Feature allocation is appropriate
- [ ] Strategic alignment is confirmed
- [ ] Epic Lead is appointed
- [ ] Success metrics are defined

### Approval:
```
Approver: _____________________
Role:     _____________________
Date:     _____________________
Comment:  ___________________
```

---

## Gate E2: Feature Breakdown Approval

**Purpose**: Confirm Feature decomposition is appropriate with clear dependencies

### Checklist:
- [ ] feature_breakdown.md is complete
- [ ] Each Feature scope is clear
- [ ] Coverage Tiers are appropriately assigned
- [ ] Dependency graph has no cycles
- [ ] Integration Points are defined
- [ ] Feature priorities are determined

### Approval:
```
Approver: _____________________
Role:     _____________________
Date:     _____________________
Comment:  ___________________
```

---

## Gate E3: Shared Contract Approval

**Purpose**: Confirm shared contracts are defined and consumer teams have agreed

### Checklist:
- [ ] All shared contracts are defined
- [ ] Contract owner team is clear for each
- [ ] Consumer teams have reviewed contract contents
- [ ] SLAs are defined
- [ ] Change management process is agreed

### Team Confirmation:

**TEAM-ORD (Contract Owner)**:
```
Confirmed by: _____________________
Date:         _____________________
```

**TEAM-INV (Contract Consumer)**:
```
Confirmed by: _____________________
Date:         _____________________
Confirmation: Contract contents reviewed and agreed as consumer
```

### Final Approval:
```
Approver: _____________________
Role:     Architecture Board
Date:     _____________________
Comment:  ___________________
```

---

## Gate E4: Cross-Team Integration Plan Approval

**Purpose**: Confirm cross-team integration plan is established with clear test strategy

### Checklist:
- [ ] Cross-team integration tests are defined
- [ ] Test environment is prepared (or plan exists)
- [ ] Test schedule is agreed
- [ ] Escalation path for failures is clear
- [ ] Test responsibilities for each team are clear

### Team Confirmation:

**TEAM-ORD**:
```
Confirmed by: _____________________
Date:         _____________________
Test Responsibility: TS-CROSS-001 (owner), TS-CROSS-002 (owner)
```

**TEAM-INV**:
```
Confirmed by: _____________________
Date:         _____________________
Test Responsibility: TS-CROSS-001 (participant), TS-CROSS-002 (participant)
```

### Final Approval:
```
Approver: _____________________
Role:     Epic Lead
Date:     _____________________
Comment:  ___________________
```

---

## Gate E5: Feature Specs Ready

**Purpose**: Confirm each Feature Spec can be created

### Feature Status:

| Feature ID | Team | Spec Ready | Approved By |
|------------|------|------------|-------------|
| FEAT-ORD-001 | TEAM-ORD | [ ] | ____________ |
| FEAT-ORD-002 | TEAM-ORD | [ ] | ____________ |
| FEAT-INV-001 | TEAM-INV | [ ] | ____________ |

### Checklist:
- [ ] All Feature dependencies can be resolved
- [ ] Shared contracts are stable
- [ ] Each team is ready to create Specs

### Final Approval:
```
Approver: _____________________
Role:     Epic Lead
Date:     _____________________
Comment:  ___________________
```

---

## Final Gate: Epic Integration Complete

**Purpose**: Confirm entire Epic integration is complete and all Features are release-ready

### Checklist:
- [ ] All Features have passed their Final Gate
- [ ] All cross-team integration tests have succeeded
- [ ] Shared contracts are deployed to production
- [ ] All Evidence Packs are collected
- [ ] Release notes are created

### Feature Final Status:

| Feature ID | Final Gate | Evidence Pack | Release Ready |
|------------|------------|---------------|---------------|
| FEAT-ORD-001 | [ ] | [ ] | [ ] |
| FEAT-ORD-002 | [ ] | [ ] | [ ] |
| FEAT-INV-001 | [ ] | [ ] | [ ] |

### Team Final Confirmation:

**TEAM-ORD**:
```
Confirmed by: _____________________
Role:         Tech Lead
Date:         _____________________
```

**TEAM-INV**:
```
Confirmed by: _____________________
Role:         Tech Lead
Date:         _____________________
```

### Epic Final Approval:
```
Approver: _____________________
Role:     Epic Lead
Date:     _____________________

Approver: _____________________
Role:     Architecture Board
Date:     _____________________
```

---

## Approval History

| Gate | Status | Approved By | Date | Notes |
|------|--------|-------------|------|-------|
| E1: Epic Design | Pending | - | - | - |
| E2: Feature Breakdown | Pending | - | - | - |
| E3: Shared Contract | Pending | - | - | - |
| E4: Integration Plan | Pending | - | - | - |
| E5: Feature Specs Ready | Pending | - | - | - |
| Final: Integration Complete | Pending | - | - | - |

---

## Re-Approval Log

> When modifying artifacts of approved Gates, re-approval is required.

| Date | Gate | Change Description | Re-approved By |
|------|------|-------------------|----------------|
| - | - | - | - |
