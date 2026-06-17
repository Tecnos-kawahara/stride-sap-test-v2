---
artifact: "tasks"
template_id: "TPL-TASKS-TECNOS-001"
feature_id: "FEAT-XXX"
tasks_id: "TASKS-XXX"
version: "{{TEMPLATE_VERSION}}"
title: "<Feature Name> Task Breakdown"
status: "draft" # draft | in_progress | completed | ai_reviewed | human_approved | deprecated
owners:
  - { name: "<Tech Lead>", role: "Tech Lead" }
  - { name: "AI Task Agent", role: "Task Generator" }
inputs:
  spec_path: "specs/XXX_feature_name/spec.md"
  plan_path: "specs/XXX_feature_name/plan.md"
  basic_design_path: "specs/XXX_feature_name/basic_design.md"
  process_bpmn_path: "specs/XXX_feature_name/process.bpmn"
  org_constraints_path: "memory/tecnos_org_constraints.md"
created_at: "YYYY-MM-DD"
updated_at: "YYYY-MM-DD"
bdd_mode: "required"  # required | optional — required の場合、全タスクに acceptance_criteria を要求
escalation_policy_ref: "memory/constitution.md#escalation_triggers"
verification_matrix:
  automated_ratio_target: 0.8  # acceptance_criteria の verification: automated の比率目標
  hitl_max: 3                  # hitl 検証の最大数（超過時は WARNING）
---

> Rule-0: このドキュメントの正本は **#1 Canonical Tasks (YAML)**。説明文は補助。
> Rule-1: plan_refs は stable id のみ（CMP/LIB/CT/TS/Phase/G）。
> Tecnos: 監査・SoD・運用のタスクを「後回し」にしない（contracts/test/ops/pmo を最低限入れる）。
> SAP: sap_objects でタスク→開発オブジェクト対応を定義。activation_order で有効化順序を遵守する。
> SAP: sap_dev_order_validated ゲートで DDIC→CDS→BDEF→CLAS→DCLS→SRVD→SRVB→DDLX 順序を検証する。

# 1. Canonical Tasks (YAML)
```yaml
id_conventions_ref: "memory/constitution.md#id_conventions"
id_conventions_version: "{{TEMPLATE_VERSION}}"

derived_fields:
  counts_are_computed: true
  counts:
    tasks: 0
    use_cases_referenced: 0
    acceptance_referenced: 0
    tasks_with_plan_refs: 0
    dependency_edges: 0
    milestones: 0

tasks_gate_check:
  counts:
    tasks: 0
    use_cases_referenced: 0
    acceptance_referenced: 0
    tasks_with_plan_refs: 0
    dependency_edges: 0
    milestones: 0
  rules:
    min_tasks: 5
    min_use_cases_referenced: 1
    min_acceptance_referenced: 1

  all_us_covered: false
  all_ac_tested: false
  groups_mapped: false
  no_dependency_errors: true
  constitution_aligned: false
  tasks_ready_for_code: false
  bdd_mode: "required"            # required | optional — front_matter.bdd_mode と一致させる
  sap_dev_order_validated: false  # SAP: activation_order が DDIC→PROG 順序を遵守しているか

tasks:
  # ─────────────────────────────────────────────────────
  # SAP 開発オブジェクト → タスク対応
  # ─────────────────────────────────────────────────────
  sap_objects:
    - task_id: ""                   # TASK-XXX 参照
      objects:
        - type: ""                  # PROG / CLAS / INTF / FUGR / TABL 等
          name: ""                  # オブジェクト名
          action: ""                # create / modify

  # ─────────────────────────────────────────────────────
  # SAP オブジェクト有効化順序
  # DDIC → CDS → BDEF → CLAS → DCLS → SRVD → SRVB → DDLX に従う
  # ─────────────────────────────────────────────────────
  activation_order:
    # Classic ABAP objects
    - step: 1
      objects: ["DOMA", "DTEL", "TABL"]
    - step: 2
      objects: ["TTYP", "VIEW"]
    - step: 3
      objects: ["FUGR", "CLAS"]
    - step: 4
      objects: ["PROG"]
    # RAP stack objects（該当する場合のみ使用）
    - step: 5
      objects: ["CDS"]           # CDS View Entity
    - step: 6
      objects: ["BDEF"]          # Behavior Definition
    - step: 7
      objects: ["DCLS"]          # Access Control
    - step: 8
      objects: ["SRVD"]          # Service Definition
    - step: 9
      objects: ["SRVB"]          # Service Binding
    - step: 10
      objects: ["DDLX"]          # Metadata Extension

  tasks:
    # ─────────────────────────────────────────────────────
    # Phase-1: Contracts & Test Skeleton
    # ─────────────────────────────────────────────────────
    - id: "T-G01-001"
      title: "Define interface contract (CT-API-01)"
      type: "contract" # contract | test | impl | docs | research | ops | pmo
      description: "OpenAPI / Event schema / File spec 等、契約としてレビュー可能な形にする"
      spec_refs: ["US-FEATXXX-001", "AC-US-FEATXXX-001-01"]
      plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1", "LIB-01", "CMP-01"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: []
      # SAP 拡張フィールド
      risk_flags: []              # security_sensitive / erp_integration / db_migration 等 → mode 自動判定
      sap_objects:                # このタスクが関連する SAP 開発オブジェクト（inline）
        - type: ""                # PROG / CLAS / INTF / FUGR / TABL 等
          name: ""
          action: ""              # create / modify
      outputs:
        - "specs/XXX_feature_name/contracts/"
      done_when:
        - "Contract artifact exists and is reviewable"
        - "Versioning policy is documented"
        - "stride-lint passes"
        - "spec_refs の全ACを再読し、ACに記載された全要素を満たしている"
      acceptance_criteria:
        # BDD形式: Given-When-Then で受け入れ条件を構造化する
        # verification: automated（テスト/lint自動検証） | manual（目視確認） | hitl（人間判断必須）
        # escalation_trigger: true にする条件:
        #   - 認証・認可ロジックの変更
        #   - DBスキーマのマイグレーション（既存データに影響）
        #   - 新規外部依存の追加（npm/pypi/Docker）
        #   - 支払・金銭処理に関わるロジック
        #   - セキュリティ設定の変更
        - id: "AC-T-G01-001-01"
          scenario: "契約アーティファクトが存在しレビュー可能である"
          given: "CT-API-01 の契約定義が完了している"
          when: "contracts/ ディレクトリを確認する"
          then: "OpenAPI/EventSchema等の契約ファイルが存在し、バージョニングポリシーが記載されている"
          verification: "automated"
          escalation_trigger: false

    - id: "T-G01-002"
      title: "Write contract tests (TS-CON-01)"
      type: "test"
      description: "契約テストを作成し、CT-API-01をカバーする"
      spec_refs: ["AC-US-FEATXXX-001-01"]
      plan_refs: ["TS-CON-01", "CT-API-01", "G-01-contracts", "Phase-1"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G01-001"]
      outputs:
        - "specs/XXX_feature_name/tests/contract/"
      done_when:
        - "Tests exist and fail in Red phase (if applicable)"
        - "covers_contract_ids に CT-API-01 が含まれている"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G01-002-01"
          scenario: "契約テストがCT-API-01をカバーしている"
          given: "CT-API-01 の契約が定義済みである"
          when: "契約テストスイートを実行する"
          then: "テストが存在し、covers_contract_ids に CT-API-01 が含まれている"
          verification: "automated"
          escalation_trigger: false

    - id: "T-G02-001"
      title: "Define audit / SoD / operational baseline (Ops note)"
      type: "ops"
      description: "監査ログ、職務分掌、再実行性、監視を最低限ドキュメント化し、実装タスクへ落とす"
      spec_refs: []
      plan_refs: ["G-02-security-ops", "Phase-1", "CMP-01"]
      bpmn_refs: []
      depends_on: ["T-G01-001"]
      outputs:
        - "specs/XXX_feature_name/implementation-details/ops.md"
      done_when:
        - "Auditability and SoD requirements are explicitly documented"
        - "Monitoring signals (metrics/logs/traces) are listed"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G02-001-01"
          scenario: "監査・SoD要件がドキュメント化されている"
          given: "機能の基本設計が完了している"
          when: "ops.md を確認する"
          then: "監査ログ要件、職務分掌、監視シグナル（metrics/logs/traces）が明記されている"
          verification: "manual"
          escalation_trigger: false

    - id: "T-G02-002"
      title: "Define Evidence Pack + AI provenance capture"
      type: "ops"
      description: "CI/SAST/SCA/Secrets/AIプロヴェナンスをゲート証跡として定義し、保存先と責任者を明記する"
      spec_refs: []
      plan_refs: ["G-02-security-ops", "Phase-1"]
      bpmn_refs: []
      depends_on: ["T-G02-001"]
      outputs:
        - "specs/XXX_feature_name/implementation-details/evidence_pack.md"
      done_when:
        - "Evidence Pack required artifacts are listed"
        - "Storage path and retention policy are defined"
        - "AI provenance fields (model/prompt/input hash) are defined"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G02-002-01"
          scenario: "Evidence Pack定義が完備している"
          given: "OpsベースラインとCI/CD環境が計画されている"
          when: "evidence_pack.md を確認する"
          then: "必須アーティファクト一覧、保管先、保持ポリシー、AIプロヴェナンスフィールドが定義されている"
          verification: "automated"
          escalation_trigger: false

    # ─────────────────────────────────────────────────────
    # Phase-2: Integration & E2E
    # ─────────────────────────────────────────────────────
    - id: "T-G03-001"
      title: "Write integration tests (TS-INT-01)"
      type: "test"
      description: "可能ならERPサンドボックス等、実環境に近い条件で統合テストを設計する。integrationタグ付きACをカバーする。"
      spec_refs: ["AC-US-FEATXXX-001-01"]
      plan_refs: ["TS-INT-01", "CT-API-01", "G-03-integration-tests", "Phase-2"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G02-001"]
      outputs:
        - "specs/XXX_feature_name/tests/integration/"
      done_when:
        - "Integration tests exist and are runnable"
        - "Test data/setup steps are documented"
        - "integrationタグ付きACが TS-INT-01 でカバーされている"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G03-001-01"
          scenario: "統合テストが実行可能でACをカバーしている"
          given: "契約テストが完了し、テスト環境が構築されている"
          when: "統合テストスイートを実行する"
          then: "テストが成功し、integrationタグ付きACが TS-INT-01 でカバーされている"
          verification: "automated"
          escalation_trigger: false

    # ─────────────────────────────────────────────────────
    # Phase-2: E2E Tests
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
        - "specs/XXX_feature_name/tests/e2e/"
        - "specs/XXX_feature_name/tests/reports/e2e/"
      done_when:
        - "E2E tests runnable locally and in CI"
        - "E2E failure artifacts (html/trace/screenshot/video) are generated and stored"
        - "playwright.config.ts に reporting 設定が含まれている"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G04-001-01"
          scenario: "E2E基盤がローカルとCIで動作する"
          given: "Playwright がインストールされている"
          when: "E2Eテストを実行する"
          then: "テストが実行され、失敗時にHTML/trace/screenshot/videoアーティファクトが生成される"
          verification: "automated"
          escalation_trigger: false

    - id: "T-G04-002"
      title: "Write E2E smoke test (TS-E2E-01)"
      type: "test"
      description: |
        e2eタグ付きACを、UI/操作の観点でスモーク回帰として担保する。
        フレーク最小化：安定セレクタ（data-testid等）/テストデータ固定/待機戦略。
      spec_refs: ["AC-US-FEATXXX-001-02"]
      plan_refs: ["TS-E2E-01", "CT-API-01", "G-04-e2e-tests", "Phase-2"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: ["T-G04-001"]
      outputs:
        - "specs/XXX_feature_name/tests/e2e/"
      done_when:
        - "Test exists and is deterministic (no exploratory steps in CI)"
        - "Artifacts are retained on failure (trace/screenshot/video) for triage"
        - "e2eタグ付きACが TS-E2E-01 でカバーされている"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G04-002-01"
          scenario: "E2Eスモークテストが決定論的に動作する"
          given: "E2E基盤がセットアップ済みである"
          when: "E2Eスモークテストを実行する"
          then: "テストが決定的に成功し、e2eタグ付きACがカバーされている"
          verification: "automated"
          escalation_trigger: false

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
        - "specs/XXX_feature_name/implementation-details/e2e-triage.md"
      done_when:
        - "Triage decision rules (product_bug/spec_gap/test_bug/flake) are documented"
        - "Artifact locations and retention rules are documented"
        - "還流先（Spec/Plan/Tasks）と担当者が明記されている"
        - "stride-lint passes"
      acceptance_criteria:
        - id: "AC-T-G04-003-01"
          scenario: "E2E失敗トリアージ手順が定義されている"
          given: "E2E基盤が稼働している"
          when: "e2e-triage.md を確認する"
          then: "分類ルール（product_bug/spec_gap/test_bug/flake）と還流先が明記されている"
          verification: "manual"
          escalation_trigger: false

  # ─────────────────────────────────────────────────────
  # Completion Verification Rules
  # ─────────────────────────────────────────────────────
  completion_verification:
    mandatory_before_complete:
      - "spec_refs に含まれる全ACを最後まで読み直す"
      - "各ACに記載された全要素を満たしているか確認（ACにない要素は確認不要）"
      - "tests/scenarios.yaml の該当シナリオを特定し、全 expected を検証"
      - "stride-lint が PASS している"

    anti_patterns:
      - "「動いた」だけで「完了」と報告する"
      - "ACの一部だけ読んで判断する"
      - "scenarios.yaml を確認せずに報告する"

    completion_report_includes:
      - "確認した全ACと各要素の充足状況"
      - "確認した scenarios.yaml シナリオと expected 検証結果"
      - "未実装・部分実装の有無（ある場合は明示）"
      - "stride-lint 実行結果"

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
