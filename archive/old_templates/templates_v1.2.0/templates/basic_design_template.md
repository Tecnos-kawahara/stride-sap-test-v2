---
artifact: "basic_design"
feature_id: "FEAT-XXX"
basic_design_id: "BD-XXX"
title: "Basic Design - <Feature Name>"
version: "1.2.0"
status: "draft" # draft | in_review | approved | released | deprecated
owners:
  - { name: "Taro Yamada", role: "Product Owner" }
  - { name: "Hanako Suzuki", role: "Tech Lead" }
reviewers:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Security Lead", role: "Security" }
links:
  process_bpmn_ref: "specs/XXX_feature_name/process.bpmn"
  spec_md_ref: "specs/XXX_feature_name/spec.md"
  plan_md_ref: "specs/XXX_feature_name/plan.md"
  tasks_md_ref: "specs/XXX_feature_name/tasks.md"
  constitution_ref: "memory/constitution.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#0 Canonical Basic Design (YAML)**。以下の説明文は補助。
> Purpose: 人間の任意テキスト入力を、AIがSDD（BPMN→Spec/Plan/Tasks）へ落とす前に「認識齟齬」を潰すハブ。

# 0. Canonical Basic Design (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0"

derived_fields:
  counts_are_computed: true
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0

basic_design:
  context:
    who: ""     # 想定ユーザー/ステークホルダー
    what: ""    # 何を実現するか（価値）
    why: ""     # なぜ今それが必要か（背景・課題）

  scope:
    in: []
    out: []

  flow_reference:
    process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
    bpmn_element_id_convention: "BPMN-(TASK|GW|EVT|FLOW)-NNN"

  # Integration critical flows（SLO/KPIが絡む重要フロー）
  integration_flows:
    - id: "FLOW-001"
      name: ""
      summary: ""
      kpi_slo: ""

  # 最重要：抜け漏れ検出（空欄は許容。ただし ready_for_bpmn/ready_for_specify を立てる前に埋める）
  traceability_rows:
    - rq:
        id: "RQ-001"
        statement: ""
      us:
        id: "US-FEATXXX-001"     # 未確定なら "" でも可
        title: ""
      ac:
        id: "AC-US-FEATXXX-001-01"  # 未確定なら "" でも可
        statement: ""
        tags: ["integration"]
      bpmn:
        id: "BPMN-TASK-001"      # 未確定なら "" でも可
        name: ""
      contract:
        id: "CT-API-01"          # 未確定なら "" でも可
      test:
        id: "TS-INT-01"          # 未確定なら "" でも可
        type: "integration"
      task:
        id: "T-G01-001"          # 未確定なら "" でも可

  open_questions:
    - id: "Q-001"
      question: ""
      blocking: true
      owner: ""
      due: "YYYY-MM-DD"

  assumptions:
    - id: "A-001"
      assumption: ""
      rationale: ""
      risk_if_false: ""

  decisions:
    - id: "DR-001"
      context: ""
      options:
        - ""
      decision: ""
      consequences: ""

  # 例外は必ず憲法（Article）に紐付け、reason/mitigation をセットで残す
  exceptions: []
  # - article: "VII"
  #   reason: ""
  #   mitigation: ""
```

---

# 1. Document Intent（読み方）
## 1.1 推奨読み順（レビュー最短経路）
1) **2. Traceability（要件→US→AC→BPMN→契約→テスト→タスク）**  
2) 3. Part A（WHAT/WHY要約）  
3) 4. Part B（HOW方針：境界・契約・テスト・例外）  
4) 5. Part C（運用・フィードバックループ）  
5) 6. Decision Log（判断の根拠）

## 1.2 アーティファクト対応（ハブ）
| Artifact | Path | Role | Owner |
|---|---|---|---|
| process.bpmn | {{ links.process_bpmn_ref }} | ハイレベル業務フロー（Camunda 8形式、HITL承認） | PO/TL |
| spec.md | {{ links.spec_md_ref }} | WHAT/WHY（HOW禁止） | PO |
| plan.md | {{ links.plan_md_ref }} | HOW方針・分解・順序（コード禁止） | TL |
| tasks.md | {{ links.tasks_md_ref }} | 実行可能タスク（実装前の正本） | TL |
| constitution.md | {{ links.constitution_ref }} | 原則 / ID規約 / Gate | Arch |

---

# 2. Traceability（最重要：抜け漏れ検出のビュー）
> NOTE: 本表は #0 YAML の `basic_design.traceability_rows` のビュー。差分が出ないように更新する。

| RQ | US | AC | BPMN | Contract | Test | Task |
|---|---|---|---|---|---|---|
| RQ-001 | US-FEATXXX-001 | AC-US-FEATXXX-001-01 | BPMN-TASK-001 | CT-API-01 | TS-INT-01 | T-G01-001 |
| ... | ... | ... | ... | ... | ... | ... |

---

# 3. Part A. WHAT/WHY Summary（Specに落とす前の理解合わせ）
- Who:
- What:
- Why:
- Goals:
- Non-goals:

---

# 4. Part B. HOW Policy（BPMN/Planに渡す“実装方針”のインターフェース）
## B.1 アーキテクチャ & 境界（Library / Modularity）
- Components (high level):
- Libraries (high level):
- Responsibility boundaries:

## B.2 契約（Contract/CLI-First）
- Contract list（ID/名称/目的だけ）:
  - CT-API-01:
  - CT-CLI-01:
- Versioning policy:
- Integration critical contracts:

## B.3 テスト戦略（Test/Integration-First）
- Contract tests (TS-CON-*):
- Integration tests (TS-INT-*):
- E2E tests (TS-E2E-*):
- Unit tests (TS-UT-*):

## B.4 Automation / AgentOps（権限・ガードレール）
- Agents:
- Allowed operations:
- Forbidden operations:
- Kill switch conditions:

## B.5 例外管理（Simplicity / Anti-Abstraction）
- Exceptions（Article / reason / mitigation）:
  - (none)

---

# 5. Part C. Operations / Feedback Loop（運用から仕様へ還流）
- Observability:
- Metrics/KPIs:
- Incident feedback → Spec/Plan update rule:
- Security feedback → Constraints:

---

# 6. Decision Log（判断の根拠）
- DR-001: <Decision>
- DR-002: ...

---

# 7. Checks（HITL/AI両対応のGate）
## 7.1 Human Review Checklist（最小）
- [ ] Traceability に重大な欠落がない（空欄が多い場合は差し戻し）
- [ ] 未確定事項が明示され、推測で埋めていない
- [ ] Integration critical flow が明確
- [ ] 例外は reason/mitigation がセット（例外が無いなら exceptions は空配列）
- [ ] process.bpmn は Camunda 8 (Zeebe) 互換・DIありでレビュー可能

## 7.2 Machine-readable Gate（basic_design_gate_check）
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.2.0"

basic_design_gate_check:
  counts:
    traceability_rows: 0
    integration_flows: 0
    blocking_questions: 0
  rules:
    min_traceability_rows: 1
    min_integration_flows: 1
    max_blocking_questions: 0

  traceability_present: false
  integration_flows_identified: false
  exceptions_documented: true  # exceptions が空でも true（方針として空を明示できていればOK）

  ready_for_bpmn: false            # HITL承認後に true（BPMN生成へ進める）
  process_bpmn_linked: false       # process_bpmn_path が確定したら true
  process_bpmn_approved: false     # HITLでBPMN承認後に true
  ready_for_specify: false         # process_bpmn_approved==true の後に true（spec/plan/tasks生成へ進める）
```

> End of basic_design.md
