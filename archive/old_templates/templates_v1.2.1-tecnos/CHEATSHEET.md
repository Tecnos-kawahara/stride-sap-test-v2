# SDD Templates v1.2.1-tecnos Cheatsheet

クイックリファレンス用のチートシートです。

---

## 1. ID規約一覧

### 1.1 正規表現

| ID種別 | 正規表現 | 例 |
|--------|----------|-----|
| Feature | `^FEAT-[A-Z0-9]{3,}$` | FEAT-001, FEAT-ABC |
| Use Case | `^US-FEAT[A-Z0-9]+-\d{3}$` | US-FEAT001-001 |
| Acceptance Criteria | `^AC-US-FEAT[A-Z0-9]+-\d{3}-\d{2}$` | AC-US-FEAT001-001-01 |
| Non-Functional Req | `^NFR-[A-Z]+-\d{2}$` | NFR-PERF-01, NFR-SEC-01 |
| Contract (API) | `^CT-API-\d{2}$` | CT-API-01 |
| Contract (Event) | `^CT-EVT-\d{2}$` | CT-EVT-01 |
| Contract (File) | `^CT-FILE-\d{2}$` | CT-FILE-01 |
| Contract (IDoc) | `^CT-IDOC-\d{2}$` | CT-IDOC-01 |
| Test Spec (Unit) | `^TS-UT-\d{2}$` | TS-UT-01 |
| Test Spec (Integration) | `^TS-INT-\d{2}$` | TS-INT-01 |
| Test Spec (Contract) | `^TS-CON-\d{2}$` | TS-CON-01 |
| Test Spec (E2E) | `^TS-E2E-\d{2}$` | TS-E2E-01 |
| Task | `^T-G\d{2}-\d{3}$` | T-G01-001, T-G04-002 |
| Task Group | `^G-\d{2}-.+$` | G-01-library, G-04-e2e-tests |
| Milestone | `^M-\d{2}$` | M-01, M-03 |
| BPMN Task | `^BPMN-TASK-\d{3}$` | BPMN-TASK-001 |
| BPMN Gateway | `^BPMN-GW-\d{3}$` | BPMN-GW-001 |
| BPMN Event | `^BPMN-EVT-\d{3}$` | BPMN-EVT-001 |
| BPMN Flow | `^BPMN-FLOW-\d{3}$` | BPMN-FLOW-001 |
| Decision Record | `^DR-\d{3}$` | DR-001 |
| Question | `^Q-\d{3}$` | Q-001 |
| Assumption | `^A-\d{3}$` | A-001 |
| Requirement | `^RQ-\d{3}$` | RQ-001 |

### 1.2 ID階層構造

```
FEAT-001
└── US-FEAT001-001
    └── AC-US-FEAT001-001-01
        └── TS-INT-01 (covers_acceptance_ids)
            └── T-G03-001 (plan_refs)
```

---

## 2. タグ一覧と対応テスト

| AC Tag | 必須テストタイプ | テストID形式 | 説明 |
|--------|------------------|--------------|------|
| `integration` | Integration Test | `TS-INT-*` | 統合テスト（API連携、DB等） |
| `e2e` | E2E Test | `TS-E2E-*` | エンドツーエンドテスト（UI含む） |
| (なし) | Unit Test | `TS-UT-*` | 単体テスト（デフォルト） |

### タグ使用例

```yaml
acceptance:
  - id: "AC-US-FEAT001-001-01"
    tags: ["integration"]  # → TS-INT-* でカバー必須

  - id: "AC-US-FEAT001-001-02"
    tags: ["e2e"]          # → TS-E2E-* でカバー必須

  - id: "AC-US-FEAT001-001-03"
    tags: []               # → TS-UT-* または任意
```

---

## 3. Gate条件一覧

### 3.1 Basic Design Gate

| 条件 | 値 | 説明 |
|------|-----|------|
| `traceability_present` | true | トレーサビリティ行が存在 |
| `integration_flows_identified` | true | 統合フローが識別済み |
| `exceptions_documented` | true | 例外が明示（空でもOK） |
| `min_traceability_rows` | 1 | 最低1行のトレーサビリティ |
| `min_integration_flows` | 1 | 最低1つの統合フロー |
| `max_blocking_questions` | 0 | 未解決の阻害質問なし |
| `ready_for_bpmn` | true | BPMN作成可能 |

### 3.2 BPMN Approval Gate

| 条件 | 値 | 説明 |
|------|-----|------|
| `process_bpmn_linked` | true | BPMNパスが確定済み |
| `process_bpmn_approved` | true | BPMN承認済み |
| `ready_for_specify` | true | Spec/Plan/Tasks作成可能 |

### 3.3 Spec Gate

| 条件 | 値 | 説明 |
|------|-----|------|
| `no_blocking_open_questions` | true | ブロッキング質問が解消済み |
| `min_use_cases` | 1 | 最低1つのUS |
| `min_total_acceptance_criteria` | 3 | 最低3つのAC |
| `min_integration_acceptance_criteria` | 1 | integrationタグ付きACを最低1件 |
| `max_blocking_questions` | 0 | 未解決の阻害質問なし |
| `min_nfr_items` | 6 | NFR合計が最低6件 |
| `min_security_items` | 1 | セキュリティ項目が最低1件 |
| `min_integration_items` | 1 | 統合要件が最低1件 |
| `min_data_items` | 1 | データガバナンスが最低1件 |
| `ai_plan_ready` | true | Plan生成可能 |

### 3.4 Plan Gate

| 条件 | 値 | 説明 |
|------|-----|------|
| `contracts_defined` | true | 契約が定義済み |
| `tests_prioritized` | true | テスト優先度が明確 |
| `integration_first_gate_passed` | true | Integration-first 方針が通過 |
| `min_in_use_cases` | 1 | 対象USが最低1件 |
| `min_libraries` | 1 | ライブラリが最低1件 |
| `min_contracts` | 1 | 契約が最低1件 |
| `min_tests` | 2 | テストが最低2件 |
| `min_integration_tests` | 1 | 統合テストが最低1件 |
| `min_groups` | 3 | グループが最低3件 |
| `ai_tasks_ready` | true | Tasks生成可能 |

### 3.5 Tasks Gate

| 条件 | 値 | 説明 |
|------|-----|------|
| `no_dependency_errors` | true | 依存関係の矛盾なし |
| `min_tasks` | 5 | タスクが最低5件 |
| `min_use_cases_referenced` | 1 | 参照USが最低1件 |
| `min_acceptance_referenced` | 1 | 参照ACが最低1件 |
| `tasks_with_plan_refs == tasks` | true | 全タスクがPlan参照を持つ |
| `tasks_ready_for_code` | true | 実装開始可能 |

---

## 4. Failure Code一覧と対処法

### 4.1 参照系

| Code | 説明 | 対処 |
|------|------|------|
| `REF_NOT_FOUND` | 参照先IDが存在しない | IDのtypoを確認、参照先を作成 |
| `INVALID_ID_FORMAT` | ID形式が規約違反 | 正規表現を確認してID修正 |
| `DUPLICATE_ID` | 同一IDが重複 | 重複IDを別IDに変更 |

### 4.2 カバレッジ系

| Code | 説明 | 対処 |
|------|------|------|
| `AC_NOT_COVERED` | ACがTSでカバーされていない | TSに`covers_acceptance_ids`追加 |
| `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE` | タグに対応するテストタイプがない | タグに応じたTS追加 |
| `CONTRACT_COVERAGE_INCOMPLETE` | CTがTS-CONでカバーされていない | TS-CONに`covers_contract_ids`追加 |
| `TEST_NOT_TASKED` | Planのテストがタスク化されていない | Tasksにタスク追加 |

### 4.3 整合性系

| Code | 説明 | 対処 |
|------|------|------|
| `ORPHAN_TASK` | タスクがPlan要素を参照していない | `plan_refs`を追加 |
| `MISSING_CONTRACT` | 統合フローに契約がない | CTを追加 |
| `BPMN_ELEMENT_NOT_FOUND` | BPMN要素が存在しない | BPMNファイルを確認 |

### 4.4 E2E系

| Code | 説明 | 対処 |
|------|------|------|
| `E2E_REPORTING_NOT_CONFIGURED` | E2E使用時にreportingが未設定 | plan.mdにreporting追加 |
| `E2E_TRIAGE_NOT_DEFINED` | E2E使用時にtriage手順が未定義 | e2e-triage.md作成 |

---

## 5. Coverage Policy クイックリファレンス

### 5.1 デフォルト設定

```yaml
coverage_policy:
  acceptance_coverage_required: true
  acceptance_coverage_target_pct: 100
  tagged_acceptance_requirements:
    integration:
      enforce: true
      required_test_type: "integration"
    e2e:
      enforce: true
      required_test_type: "e2e"
  contract_coverage_required: true
  contract_coverage_target_pct: 100
  code_coverage_targets:
    - scope: "LIB-*"
      line_pct: 85
      branch_pct: 75
    - scope: "CMP-*"
      line_pct: 60
      branch_pct: 50
  code_coverage_exclusions:
    - path_glob: "**/generated/**"
      reason: "Generated code"
      mitigation: "Contract/Integration tests cover behavior"
  tests_must_be_tasked: true
  ci_gate_is_deterministic: true
  allow_exploratory_agent_in_ci_gate: false
```

### 5.2 段階的導入

| Phase | 設定 | 挙動 |
|-------|------|------|
| 1 | `coverage_policy` 未設定 | warning（tagged/contract/test-tasking はスキップ） |
| 2 | `tagged_acceptance_requirements.<tag>.enforce: false` / `contract_coverage_required: false` / `tests_must_be_tasked: false` | warning/skip |
| 3 | `tagged_acceptance_requirements.<tag>.enforce: true` / `contract_coverage_required: true` / `tests_must_be_tasked: true` | **fail** |

---

## 6. E2E Triage 4分類

| 分類 | 説明 | 対処先 |
|------|------|--------|
| `product_bug` | 製品のバグ | Spec/Plan/Tasks → 修正タスク追加 |
| `spec_gap` | 仕様の抜け漏れ | Spec AC更新 → Plan/Tasks修正 |
| `test_bug` | テストコードのバグ | テスト修正（セレクタ/データ等） |
| `flake` | 非決定的な失敗 | 安定化（待機/リトライ/データ固定） |

### Triage フロー

```
E2E fails → Classify → 対処 → Re-run
                ↓
          product_bug → Fix task → Spec/Plan/Tasks更新
          spec_gap    → Spec AC更新 → Plan/Tasks修正
          test_bug    → テスト修正
          flake       → 安定化
```

---

## 7. speckit-lint コマンド

```bash
# 基本検証
speckit-lint specs/<feature>/

# カバレッジレポート出力
speckit-lint specs/<feature>/ --coverage-report

# 警告のみ（fail しない）
speckit-lint specs/<feature>/ --warn-only

# 詳細出力
speckit-lint specs/<feature>/ --verbose

# JSON出力
speckit-lint specs/<feature>/ --format json
```

---

## 8. ファイル構成テンプレート

```
specs/<feature_name>/
├── basic_design.md          # WHAT/WHY（認識合わせハブ）
├── process.bpmn             # 業務フロー（Camunda 8形式）
├── spec.md                  # 仕様書（US/AC/NFR）
├── plan.md                  # 実装方針（CT/TS/戦略）
├── tasks.md                 # 実行タスク
└── implementation-details/
    ├── e2e-triage.md        # E2E失敗対応手順
    └── *.md                 # その他実装詳細
```

---

## 9. Nine Articles（九条）要約

| Article | タイトル | 要点 |
|---------|----------|------|
| I | Library-First | 共通ロジックはライブラリ化 |
| II | Contract-First | API/Event契約を先に定義 |
| III | Test-First | テストを先に書く |
| IV | CLI-First | CLIから設計 |
| V | No Direct DB | 直接DB接続禁止 |
| VI | Simplicity | 複雑さを避ける |
| VII | Anti-Abstraction | 過度な抽象化禁止 |
| VIII | Documentation | 文書化必須 |
| IX | Continuous Improvement | 継続的改善 |

---

## 10. クイックコピー

### 新規AC追加時

```yaml
- id: "AC-US-FEATXXX-001-NN"
  given: ""
  when: ""
  then: ""
  tags: []  # integration, e2e
```

### 新規Contract追加時

```yaml
- id: "CT-API-NN"
  type: "REST"
  name: ""
  provider: ""
  consumer: ""
  schema_ref: ""
```

### 新規Test追加時

```yaml
- id: "TS-INT-NN"
  title: ""
  covers_acceptance_ids: []
  covers_contract_ids: []
  gate: "M-02"
```

### 新規Task追加時

```yaml
- id: "T-GNN-NNN"
  title: ""
  plan_refs: []
  spec_refs: []
  priority: "high"
  estimate_hours: 0
```

---

> End of CHEATSHEET.md
