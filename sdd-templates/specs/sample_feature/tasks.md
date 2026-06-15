---
artifact: "tasks"
template_id: "TPL-TASKS-TECNOS-001"
feature_id: "FEAT-001"
tasks_id: "TASKS-001"
version: "{{TEMPLATE_VERSION}}"
title: "Web-EDI受注受付 Task Breakdown"
status: "draft" # draft | in_progress | completed | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Tech Lead>", role: "Tech Lead" }
  - { name: "AI Task Agent", role: "Task Generator" }
inputs:
  spec_path: "specs/sample_feature/spec.md"
  plan_path: "specs/sample_feature/plan.md"
  basic_design_path: "specs/sample_feature/basic_design.md"
  process_bpmn_path: "specs/sample_feature/process.bpmn"
  org_constraints_path: "memory/tecnos_org_constraints.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
---

> Rule-0: このドキュメントの正本は **#1 Canonical Tasks (YAML)**。説明文は補助。
> Rule-1: plan_refs は stable id のみ（CMP/LIB/CT/TS/Phase/G）。
> Tecnos: 監査・SoD・運用のタスクを「後回し」にしない（contracts/test/ops/pmo を最低限入れる）。
> v1.2.3: Evidence Pack/AIプロヴェナンスを含め、Planの全TSがTasksに落ちていることを担保する。

# 1. Canonical Tasks (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

derived_fields:
  counts_are_computed: true
  counts:
    tasks: 8
    use_cases_referenced: 1
    acceptance_referenced: 3
    tasks_with_plan_refs: 8
    dependency_edges: 7
    milestones: 3

tasks_gate_check:
  counts:
    tasks: 8
    use_cases_referenced: 1
    acceptance_referenced: 3
    tasks_with_plan_refs: 8
    dependency_edges: 7
    milestones: 3
  rules:
    min_tasks: 5
    min_use_cases_referenced: 1
    min_acceptance_referenced: 1

  all_us_covered: true
  all_ac_tested: true
  groups_mapped: true
  no_dependency_errors: true
  constitution_aligned: true
  tasks_ready_for_code: true

tasks:
  tasks:
    # ─────────────────────────────────────────────────────
    # Phase-1: Contracts & Test Skeleton
    # ─────────────────────────────────────────────────────
    - id: "T-G01-001"
      title: "Define interface contract (CT-API-01)"
      type: "contract" # contract | test | impl | docs | research | ops | pmo
      description: "Web-EDI受注受付APIをOpenAPIで定義し、契約としてレビュー可能な形にする"
      spec_refs: ["US-FEAT001-001", "AC-US-FEAT001-001-01"]
      plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1", "LIB-01", "CMP-01"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: []
      outputs:
        - "specs/sample_feature/contracts/"
      done_when:
        - "Contract artifact exists and is reviewable"
        - "Versioning policy is documented"
        - "stride-lint passes"

    - id: "T-G01-002"
      title: "Write contract tests (TS-CON-01)"
      type: "test"
      description: "Web-EDI受注受付APIの契約テストを作成し、CT-API-01をカバーする"
      spec_refs: ["AC-US-FEAT001-001-01"]
      plan_refs: ["TS-CON-01", "CT-API-01", "G-01-contracts", "Phase-1"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G01-001"]
      outputs:
        - "specs/sample_feature/tests/contract/"
      done_when:
        - "Tests exist and fail in Red phase (if applicable)"
        - "covers_contract_ids に CT-API-01 が含まれている"
        - "stride-lint passes"

    - id: "T-G02-001"
      title: "Define audit / SoD / operational baseline (Ops note)"
      type: "ops"
      description: "監査ログ、職務分掌、再実行性、監視を最低限ドキュメント化し、実装タスクへ落とす"
      spec_refs: []
      plan_refs: ["G-02-security-ops", "Phase-1", "CMP-01"]
      bpmn_refs: []
      depends_on: ["T-G01-001"]
      outputs:
        - "specs/sample_feature/implementation-details/ops.md"
      done_when:
        - "Auditability and SoD requirements are explicitly documented"
        - "Monitoring signals (metrics/logs/traces) are listed"
        - "stride-lint passes"

    - id: "T-G02-002"
      title: "Define Evidence Pack + AI provenance capture"
      type: "ops"
      description: "CI/SAST/SCA/Secrets/AIプロヴェナンスをゲート証跡として定義し、保存先と責任者を明記する"
      spec_refs: []
      plan_refs: ["G-02-security-ops", "Phase-1"]
      bpmn_refs: []
      depends_on: ["T-G02-001"]
      outputs:
        - "specs/sample_feature/implementation-details/evidence_pack.md"
      done_when:
        - "Evidence Pack required artifacts are listed"
        - "Storage path and retention policy are defined"
        - "AI provenance fields (model/prompt/input hash) are defined"
        - "stride-lint passes"

    # ─────────────────────────────────────────────────────
    # Phase-2: Integration & E2E
    # ─────────────────────────────────────────────────────
    - id: "T-G03-001"
      title: "Write integration tests (TS-INT-01)"
      type: "test"
      description: "ERPサンドボックス等、実環境に近い条件で統合テストを設計し、integrationタグ付きACをカバーする。"
      spec_refs:
        - "AC-US-FEAT001-001-01"
        - "AC-US-FEAT001-001-02"
        - "AC-US-FEAT001-001-03"
      plan_refs: ["TS-INT-01", "CT-API-01", "G-03-integration-tests", "Phase-2"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G02-001"]
      outputs:
        - "specs/sample_feature/tests/integration/"
      done_when:
        - "Integration tests exist and are runnable"
        - "Test data/setup steps are documented"
        - "integrationタグ付きACが TS-INT-01 でカバーされている"
        - "stride-lint passes"

    # ─────────────────────────────────────────────────────
    # Phase-2: E2E Tests (v1.2.3 追加)
    # ─────────────────────────────────────────────────────
    - id: "T-G04-001"
      title: "Set up E2E test harness (Playwright) + reporting"
      type: "test"
      description: |
        PlaywrightのE2E基盤（決定論的実行）とレポート（HTML/trace等）出力を整備する。
        MCPは生成/再現/triage用途に限定し、CIゲートでは決定論的テストのみ実行する。
      spec_refs: []
      plan_refs: ["TS-E2E-01", "G-04-e2e-tests", "Phase-2"]
      bpmn_refs: []
      depends_on: ["T-G03-001"]
      outputs:
        - "specs/sample_feature/tests/e2e/"
        - "specs/sample_feature/tests/reports/e2e/"
      done_when:
        - "E2E tests runnable locally and in CI"
        - "E2E failure artifacts (html/trace/screenshot/video) are generated and stored"
        - "playwright.config.ts に reporting 設定が含まれている"
        - "stride-lint passes"

    - id: "T-G04-002"
      title: "Write E2E smoke test (TS-E2E-01)"
      type: "test"
      description: |
        e2eタグ付きACを、UI/操作の観点でスモーク回帰として担保する。
        フレーク最小化：安定セレクタ（data-testid等）/テストデータ固定/待機戦略。
      spec_refs: ["AC-US-FEAT001-001-02"]
      plan_refs: ["TS-E2E-01", "CT-API-01", "G-04-e2e-tests", "Phase-2"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G04-001"]
      outputs:
        - "specs/sample_feature/tests/e2e/"
      done_when:
        - "Test exists and is deterministic (no exploratory steps in CI)"
        - "Artifacts are retained on failure (trace/screenshot/video) for triage"
        - "e2eタグ付きACが TS-E2E-01 でカバーされている"
        - "stride-lint passes"

    - id: "T-G04-003"
      title: "E2E failure triage & feedback loop procedure"
      type: "ops"
      description: |
        E2E失敗を分類（product_bug/spec_gap/test_bug/flake）し、Spec/Plan/Tasksへ還流する手順を定義する。
        Org Constraintsの「インシデント→還流」をE2E運用に適用する。
      spec_refs: []
      plan_refs: ["G-04-e2e-tests", "Phase-2"]
      bpmn_refs: []
      depends_on: ["T-G04-001"]
      outputs:
        - "specs/sample_feature/implementation-details/e2e-triage.md"
      done_when:
        - "Triage decision rules (product_bug/spec_gap/test_bug/flake) are documented"
        - "Artifact locations and retention rules are documented"
        - "還流先（Spec/Plan/Tasks）と担当者が明記されている"
        - "stride-lint passes"

  milestones:
    - id: "M-01"
      name: "Contracts ready"
      exit_criteria:
        - "All CT-* are defined"
        - "TS-CON-* exists and covers all CT-*"
      related_task_ids: ["T-G01-001", "T-G01-002"]

    - id: "M-02"
      name: "Integration test runnable"
      exit_criteria:
        - "TS-INT-* exists"
        - "Integration environment prerequisites are documented"
        - "integrationタグ付きACがTS-INTでカバーされている"
      related_task_ids: ["T-G03-001"]

    - id: "M-03"
      name: "E2E smoke runnable"
      exit_criteria:
        - "TS-E2E-* exists (when e2e-tagged AC exists)"
        - "E2E report artifacts are retained on failure"
        - "e2eタグ付きACがTS-E2Eでカバーされている"
        - "Triage手順（e2e-triage.md）が定義されている"
      related_task_ids: ["T-G04-001", "T-G04-002", "T-G04-003"]

  risks:
    - id: "R-001"
      risk: ""
      impact: ""
      mitigation: ""
```

---

# 2. Minimal Human Notes（任意）
- 調整事項:
- ブロッカー:

## 2.1 E2E Triage Quick Reference
| Category | Definition | Action |
|---|---|---|
| `product_bug` | プロダクトのバグ | 修正タスク（T-*）を作成し、TS/AC/CT/BPMNにリンク |
| `spec_gap` | 仕様の曖昧さ・不足 | Spec AC を更新し、Plan/Tasks を修正 |
| `test_bug` | テストコードの不具合 | テストを修正（安定セレクタ、テストデータ等） |
| `flake` | 一時的な不安定（環境依存等） | 安定化（待機戦略、リトライポリシー、テストデータ固定） |

> End of tasks.md
