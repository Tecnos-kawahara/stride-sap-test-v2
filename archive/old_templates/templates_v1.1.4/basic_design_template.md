---
artifact: "basic_design"
feature_id: "FEAT-XXX"
basic_design_id: "BD-XXX"
title: "Basic Design - <Feature Name>"
version: "1.1.4"
status: "draft" # draft | in_review | approved | released | deprecated
owners:
  - { name: "Taro Yamada", role: "Product Owner" }
  - { name: "Hanako Suzuki", role: "Tech Lead" }
reviewers:
  - { name: "QA Lead", role: "Quality" }
  - { name: "Security Lead", role: "Security" }
repo: "github.com/your-org/your-repo"
specs_dir: "specs/XXX_feature_name/"
inputs:
  requirements_ref: ""        # PRD/Jira/Backlog URL or ID
  constraints_ref: ""         # relevant ADRs/Policies
related_artifacts:
  basic_design_md: "specs/XXX_feature_name/basic_design.md"
  process_bpmn: "specs/XXX_feature_name/process.bpmn"
  spec_md: "specs/XXX_feature_name/spec.md"
  plan_md: "specs/XXX_feature_name/plan.md"
  tasks_md: "specs/XXX_feature_name/tasks.md"
  data_model_md: "specs/XXX_feature_name/data-model.md"
  contracts_dir: "specs/XXX_feature_name/contracts/"
constitution_md: "memory/constitution.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

# 0. Read Me First（HITLのための読み順）

## 0.1 目的・位置づけ（3〜5行）
- 本書は「要件要求 → 基本設計（HITL判定） → BPMN（HITL承認） → SDD（spec/plan/tasks）」のハブである。
- 人間は本書で、設計妥当性・抜け漏れ・リスク・例外（憲法）を判断する。
- AIは本書を参照して BPMN と spec/plan/tasks を生成・更新する（ただし正本は各ドキュメントの Canonical YAML）。

## 0.2 推奨読み順（レビュー最短経路）
1) 0.6 トレーサビリティ（要件→US→AC→契約→テスト→タスク）  
2) Part A（WHAT/WHY要約）  
3) Part B（HOW方針：境界・契約・テスト・例外）  
4) Part C（運用・フィードバックループ）  
5) 0.7 Decision Log（判断の根拠）

## 0.3 対象範囲（In / Out）
- In:
- Out（非ゴール）:

## 0.4 アーティファクト対応（ハブ）
| Artifact | Path | Purpose | Owner |
|---|---|---|---|
| basic_design.md | {{ related_artifacts.basic_design_md }} | HITL判断ハブ | PO/TL |
| process.bpmn | {{ related_artifacts.process_bpmn }} | ハイレベル業務フロー（HITL承認） | PO/TL |
| spec.md | {{ related_artifacts.spec_md }} | WHAT/WHY（HOW禁止） | PO |
| plan.md | {{ related_artifacts.plan_md }} | HOW方針・分解・順序（コード禁止） | TL |
| tasks.md | {{ related_artifacts.tasks_md }} | 実行可能タスク（YAML正本） | TL |
| contracts/ | {{ related_artifacts.contracts_dir }} | 契約（OpenAPI/proto/CLI） | TL |
| constitution.md | {{ constitution_md }} | Nine Articles / Gate / ID規約 | Arch |

## 0.5 Nine Articles 対応サマリ（レビュー用）
| Article | Principle | Coverage in this doc |
|---|---|
| I | Library-First | B.1 |
| II | Contract/CLI-First | B.2 |
| III | Test-First | B.3 |
| IV | Documentation-First | A / B / C |
| V | Modularity | B.1 |
| VI | Automation | B.4 / C.1 |
| VII | Simplicity | B.6 / B.5 |
| VIII | Anti-Abstraction | B.6 / B.5 |
| IX | Integration-First | A.4 / B.2 / B.3 |

## 0.6 トレーサビリティ（最重要：抜け漏れ検出）
> 可能ならレビュー時点で埋める（空欄が多い場合は差し戻し条件にしてよい）

| Requirement/PRD | US | AC | Contract | Test (type) | Task |
|---|---|---|---|---|---|
| RQ-001 | US-FEATXXX-001 | AC-US-FEATXXX-001-01 | CT-API-01 | integration | T-G01-001 |
| ... | ... | ... | ... | ... | ... |

## 0.7 Decision Log（判断の根拠：後で必ず効く）
- DR-001: <Decision>
  - Context:
  - Options:
  - Decision:
  - Consequences:
  - Date / Owner:

---

# Part A. WHAT/WHY Summary（Specの要約：人間レビュー用）

## A.1 フィーチャ概要（ピッチ）
- Who:
- What:
- Why:

## A.2 背景・目的・ビジネス価値（要点のみ）
- Background:
- Goal:
- Value:

## A.3 要件の要約（US/NFRの“人間向け要約”）
- Key US:
- Key NFR:
- Key Constraints:

## A.4 受入・テスト観点（Integration-First強制）
- Integration critical flows:
- KPI / SLO:

## A.5 未確定事項（推測禁止）
- [NEEDS CLARIFICATION: ]

---

# Part B. HOW Policy（BPMN/Planに渡す“実装方針”のインターフェース）

## B.1 アーキテクチャ & 境界（Library / Modularity）
- Components (high level):
- Libraries (high level):
- Responsibility boundaries:

## B.2 契約（Contract/CLI-First）
- Contract list（ID/名称/目的だけ）:
  - CT-API-01:
  - CT-CLI-01:
- 互換性方針（versioning）:
- Integration critical contracts:

## B.3 テスト戦略（Test/Integration-First）
- Contract tests:
- Integration tests:
- E2E tests:
- Unit tests:

## B.4 Automation / AgentOps（権限・ガードレール）
- Agents:
- Allowed operations:
- Forbidden operations:
- Kill switch conditions:

## B.5 例外管理（Simplicity / Anti-Abstraction）
> 例外がない場合は空配列のまま（例外の“形骸化”防止）

```yaml
exceptions: []
# - article: "VII"
#   reason: ""
#   mitigation: ""
```

## B.6 シンプル設計の上限（明示）

* max_components:
* max_projects:
* max_layers:

---

# Part C. Feedback Loop（運用→差分→再生成）

## C.1 Spec/Plan/Tasks/Code 差分検出（/speckit.diff前提）

* diff targets:
* cadence:
* owners:

## C.2 Observability（メトリクス）

* metrics:
* alert thresholds:
* incident → spec update flow:

## C.3 Versioning / Amendment

* branching/tags:
* constitution amendment trigger:

---

# Part D. Checks（HITL/AI両対応のGate）

## D.1 Human Review Checklist（最小）

* [ ] 0.6 トレーサビリティに重大な欠落がない
* [ ] 未確定事項が明示され、推測で埋めていない
* [ ] Integration critical flow が明確
* [ ] 例外は reason/mitigation がセット（例外が無いなら exceptions は空配列）
* [ ] process.bpmn のレビュー対象範囲（ハイレベル）と、実装詳細の非混入が守られている

## D.2 Machine-readable Gate（basic_design_gate_check）

```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "1.1.4"

basic_design_gate_check:
  traceability_present: false
  integration_flows_identified: false
  exceptions_documented: false

  ready_for_bpmn: false            # Phase 1(HITL) 承認後に true（BPMN生成に進める）
  process_bpmn_linked: false       # process_bpmn パスが確定したら true
  process_bpmn_approved: false     # Phase 1.5(HITL) BPMN承認後に true
  ready_for_specify: false         # process_bpmn_approved==true の後に true（spec/plan/tasks生成に進める）
```

> End of basic_design.md
