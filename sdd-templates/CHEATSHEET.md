# SDD Templates Cheatsheet

クイックリファレンス用のチートシートです。

> Version: 5.3.3-tecnos-stride

---

## 1. ID規約一覧

### 1.1 正規表現

| ID種別 | 正規表現 | 例 |
|--------|----------|-----|
| Feature | `^FEAT-[A-Z0-9]{3,}$` | FEAT-001, FEAT-ABC |
| Epic | `^EPIC-[A-Z]{3,}$` | EPIC-ORDER, EPIC-PRICE |
| Team | `^TEAM-[A-Z]{1,3}$` | TEAM-A, TEAM-ABC |
| Use Case | `^US-FEAT[A-Z0-9]{3,}-[0-9]{3}$` | US-FEAT001-001 |
| Acceptance Criteria | `^AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}$` | AC-US-FEAT001-001-01 |
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
| Shared Contract | `^SC-(API|EVT|FILE)-[A-Z0-9]{3,}$` | SC-API-ORDER |
| Dependency | `^DEP-[0-9]{3}$` | DEP-001 |
| CCP | `^CCP-[0-9]{3}$` | CCP-001 |

### 1.2 ID階層構造

```
FEAT-001
└── US-FEAT001-001
    └── AC-US-FEAT001-001-01
        └── TS-INT-01 (covers_acceptance_ids)
            └── T-G03-001 (plan_refs)
```

### 1.3 TEIM Test Process IDs（Txx）

| ID | Test Process |
|---|---|
| T04 | 機能連携 |
| T05 | アドオン顧客確認 |
| T06 | 権限 |
| T07 | ジョブ |
| T08 | IF |
| T09 | 機能単位性能 |
| T10 | 機能単位障害 |
| T11 | 結合 |
| T12 | 業務場面想定性能 |
| T13 | 総合（業務/非機能） |
| T14 | 業務運用 |
| T15 | システム運用 |

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
| `delivery_model_defined` | true | requirements-driven / ftos / hybrid を決定 |
| `raci_plus_defined` | true | Human/AI/CIの責任境界が定義済み |
| `ai_policy_defined` | true | AI Policy（入力制御/監査）が明示済み |
| `artifact_registry_defined` | true | 成果物マスターが確定済み |
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
| `min_spec_as_code_artifacts` | 1 | 機械可読仕様が最低1件 |
| `spec_as_code_defined` | true | Spec-as-Codeが定義済み |
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
| `evidence_pack_defined` | true | ゲート証跡（Evidence Pack）が定義済み |
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

### 4.5 AI/HITL系

| Code | 説明 | 対処 |
|------|------|------|
| `SPEC_AS_CODE_MISSING` | Spec-as-Codeが未定義 | `spec.spec_as_code.artifacts`を追加 |
| `EVIDENCE_PACK_NOT_DEFINED` | Evidence Packが未定義 | `plan.test_strategy.evidence_pack`を追加 |
| `PLACEHOLDER_VALUE_PRESENT` | プレースホルダが残っている | `FEAT-XXX` 等を置換 |
| `ARTIFACT_REGISTRY_INVALID` | 成果物マスターの構造不備 | `memory/artifact_registry.md` を修正 |
| `COUNTS_MISMATCH` | 宣言されたcountsと計算値が不一致 | `COUNTS_SUGGESTION` の値をコピペ |
| `COUNTS_SUGGESTION` | 正しいcounts値の提案 | 表示されたYAMLをコピーして貼り付け |

### 4.6 Phase Gate / Approval系

| Code | 説明 | 対処 |
|------|------|------|
| `APPROVAL_PENDING` | 人間の承認待ち | APPROVAL.md でチェックボックスを `[x]` に変更 |
| `APPROVAL_FILE_MISSING` | APPROVAL.md がない | テンプレートからコピー |
| `POST_APPROVAL_CHANGE` | 承認後にファイルが変更された | 該当ゲートの再承認が必要 |

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

## 7. stride CLI / lint コマンド

`--scale enterprise` は Monorepo / CI 規模の指定です。Epic/Feature 階層は `sdd-templates/config/enterprise.yaml` の `enterprise.enabled: true` で別途有効化します。

```bash
# 基本検証（推奨）
stride lint specs/<feature>/

# カバレッジレポート出力
stride lint specs/<feature>/ --coverage-report

# 警告のみ（fail しない）
stride lint specs/<feature>/ --warn-only

# 詳細出力
stride lint specs/<feature>/ --verbose

# JSON出力
stride lint specs/<feature>/ --format json

# Enterprise Hierarchy（オプション）
stride epic init EPIC-ORDER
stride epic validate EPIC-ORDER
stride epic gates EPIC-ORDER
stride epic features EPIC-ORDER
stride epic progress EPIC-ORDER
stride init order_import --epic EPIC-ORDER --team TEAM-A
stride lint specs/order_import/ --enterprise
stride lint --all --enterprise
```

> 直接ラッパー `sdd-templates/tools/stride-lint` も引き続き使用可能です。

---

## 8. Phase Gate / APPROVAL.md

### Phase Gate 一覧 (Full Mode)

| Phase | 作成可能ファイル | 作成に必要な承認 |
|-------|-----------------|-----------------|
| 1: Design | basic_design.md, process.bpmn, APPROVAL.md | なし（bootstrap） |
| 2: Specify | spec.md, plan.md, contracts/*, implementation-details/*, tests/scenarios.yaml | Gate 1, 2 承認済み |
| 3: Tasking | tasks.md, tests/* | Gate 3, 4 承認済み |
| 4: Execute | src/* | Gate 5 承認済み |

### Phase Gate 一覧 (Lite Mode) 🆕

| Phase | 作成可能ファイル | 作成に必要な承認 |
|-------|-----------------|-----------------|
| 1: Design & Flow | basic_design.md, process.bpmn, APPROVAL.md | なし（bootstrap） |
| 2: Spec & Plan | spec.md, plan.md, contracts/*, implementation-details/*, tests/* | Gate A 承認済み |
| 3: Implementation | tasks.md, src/* | Gate B 承認済み |

> **セキュリティ**: 未定義のファイルタイプは specs/ 内で **BLOCKED** されます。

### Phase Gate コマンド

```bash
# Phase状態を確認
python3 sdd-templates/tools/phase_gate.py status specs/<feature>/

# ファイル作成前にチェック
python3 sdd-templates/tools/phase_gate.py check <file_path>

# Hook自動セットアップ
python3 sdd-templates/tools/setup_hooks.py
```

### APPROVAL.md ルール（INVIOLABLE）

- **AIは APPROVAL.md を編集してはいけない**
- チェックボックス `[x]` は人間のみが変更可能
- 承認者名と日付は人間が記入
- stride-lint で `APPROVAL_PENDING` が出たら **完全停止**

### APPROVAL.md 記入例

```markdown
## Gate 1: Basic Design
確認項目：
- [x] basic_design.md の WHO/WHAT/WHY が正しい
- [x] トレーサビリティが定義されている
- [x] RACI+ の役割分担が適切である

承認者: 山田太郎
日付:   2025-01-04
```

### Lite Mode（小規模プロジェクト向け）🆕

Lite Mode は PoC・1人開発・小規模プロジェクト向けの簡略化された承認フローです。
6段階を3段階に削減します。

| Full Mode | Lite Mode | 対象ファイル |
|-----------|-----------|-------------|
| Gate 1 + 2 | Gate A | basic_design.md, process.bpmn |
| Gate 3 + 4 | Gate B | spec.md, plan.md, contracts/*, implementation-details/*, tests/* |
| Gate 5 + Final | Gate C | tasks.md, src/* |

#### Lite Mode の使用方法

```bash
# 新規機能を Lite Mode で初期化
stride init my_feature --lite

# Lite Mode でlint
stride lint specs/my_feature/ --lite-mode

# 自動検出: APPROVAL.md に "Gate A:" または "Lite Mode" が含まれると自動的に Lite Mode として扱う
```

#### Lite Mode APPROVAL.md テンプレート

```markdown
# APPROVAL.md - Lite Mode

## Gate A: Design & Flow
- [ ] basic_design.md の WHO/WHAT/WHY が正しい
- [ ] process.bpmn が完成している
承認者: ________
日付:   ________

## Gate B: Spec & Plan
- [ ] spec.md の AC/NFR が完成
- [ ] plan.md の設計が完成
承認者: ________
日付:   ________

## Gate C: Implementation
- [ ] 実装完了
- [ ] テスト完了
承認者: ________
日付:   ________
```

---

## 9. ファイル構成テンプレート

```
specs/<feature_name>/
├── APPROVAL.md              # 承認記録（人間のみ編集可能）
├── basic_design.md          # WHAT/WHY（認識合わせハブ）
├── process.bpmn             # 業務フロー（Camunda 8形式）
├── spec.md                  # 仕様書（US/AC/NFR）
├── plan.md                  # 実装方針（CT/TS/戦略）
├── tasks.md                 # 実行タスク
└── implementation-details/
    ├── e2e-triage.md        # E2E失敗対応手順
    └── *.md                 # その他実装詳細
```

### 9.1 Spec-as-Code テンプレート

| テンプレート | パス | 用途 |
|-------------|------|------|
| OpenAPI | `templates/contracts/openapi_template.yaml` | API仕様スケルトン |
| Database Schema | `templates/contracts/database_schema_template.yaml` | DBスキーマ定義（DB使用時） |
| Database Input CSV | `templates/contracts/database_schema_input.csv` | AI生成用CSV入力（DB使用時） |

---

## 10. Fourteen Articles（十四条）要約

| Article | タイトル | 要点 |
|---------|----------|------|
| I | Library-First | 共通ロジックはライブラリ化 |
| II | Contract/CLI-First | 契約（API/CLI/EVT/FILE/BATCH/EDI/IDOC）を先に定義 |
| III | Test-First | テストを仕様の一部として先に定義 |
| IV | Documentation-First | Spec/Plan/Tasks を先に更新 |
| V | Modularity | 境界を明確にし、ERP境界を破らない |
| VI | Automation | 検証・反復を自動化し証跡を残す |
| VII | Simplicity | 最小構成から始め増やさない |
| VIII | Anti-Abstraction | 不要な抽象化を作らない |
| IX | Integration-First | 実環境に近い統合テストを優先 |
| X | Epic-Feature Hierarchy | 大規模機能を Epic / Feature に分解し team ownership を明示 |
| XI | Shared Contract Governance | 共有契約の owner / consumer / breaking change を統治 |
| XII | Tiered Coverage | critical / standard / experimental の tier 要件で検証 |
| XIII | PM Progress Visibility | Epic 横断の進捗・依存・ブロッカー可視化 |
| XIV | Execution Authority Separation | 会話権限と実行権限を分離し、gated 行為を検証経由に限定 |

---

## 11. クイックコピー

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

## 12. Multi-Language Testing

### 12.1 言語別ツール（5言語対応）

| 言語 | Unit Runner | Coverage | Lint | SCA |
|------|-------------|----------|------|-----|
| TypeScript | Vitest | istanbul/v8 | ESLint | npm audit |
| Python | pytest | pytest-cov | Ruff | pip-audit |
| Rust | cargo test | cargo-tarpaulin | clippy | cargo-audit |
| Java | JUnit5 | JaCoCo | SpotBugs/PMD | OWASP Dep-Check |
| Go | go test | go cover | golangci-lint | govulncheck |

### 12.2 言語別PRゲート必須項目

| 言語 | 必須ゲート |
|------|-----------|
| TypeScript | `tsc --noEmit`, ESLint, Prettier, Vitest |
| Python | Ruff, Black, mypy, pytest + coverage |
| Rust | rustfmt, clippy, cargo test, cargo-audit |
| Java | SpotBugs, Checkstyle, JUnit5, JaCoCo |
| Go | gofmt, golangci-lint, go test, govulncheck |

### 12.3 plan.md での有効化

```yaml
test_strategy:
  tooling:
    language_runners:
      typescript:
        enabled: true  # ← false → true に変更
      java:
        enabled: true
      go:
        enabled: true
```

### 12.4 テスト設定テンプレート

```bash
# TypeScript
cp sdd-templates/config/testing/vitest.config.ts ./

# TypeScript 型安全性設定 (CRITICAL)
cp sdd-templates/config/typescript/tsconfig.json ./
cp sdd-templates/config/typescript/eslint.config.mjs ./

# Python (マージ)
cat sdd-templates/config/testing/pyproject.toml.snippet

# Rust (マージ)
cat sdd-templates/config/testing/Cargo.toml.snippet

# Java/Gradle (マージ)
cat sdd-templates/config/testing/build.gradle.kts.snippet

# Go (ガイド参照)
cat sdd-templates/config/testing/go_test_config.md
```

### 12.5 CI/CD マルチ言語パイプライン

`docs/CI_CD_INTEGRATION.md` の「Multi-Language Pipeline」セクション参照。

```yaml
jobs:
  spec-validation: ...  # 共通
  test-typescript: ...  # TypeScript専用
  test-python: ...      # Python専用
  test-rust: ...        # Rust専用
  test-java: ...        # Java専用
  test-go: ...          # Go専用
  contract-tests: ...   # クロス言語契約検証
  quality-gate: ...     # 統合ゲート
```

### 12.6 クロス言語契約検証

| ツール | 用途 | コマンド |
|--------|------|---------|
| Schemathesis | OpenAPI検証 | `schemathesis run contracts/openapi.yaml` |
| Pact | CDC検証 | `pact-verifier --pact-file contracts/pacts/` |
| Proto | gRPC契約 | `buf lint && buf breaking` |

### 12.7 言語別特殊考慮事項

| 言語 | 注意点 |
|------|-------|
| Go | `-race` フラグは main/nightly で必須（PRでは `-short` 推奨） |
| Java | 統合テストは重いのでPRは軽量、nightlyでフル実行 |
| Rust | ベンチ（criterion）は夜間で実行 |
| Python | AI/ML系は seed/モデル/データの決定性を確保 |

### 12.8 TypeScript 型安全性 (CRITICAL - v1.2.4)

> **AIによる `any` 型の乱用を防ぐための必須設定**

#### 禁止事項

| パターン | 禁止理由 |
|---------|---------|
| `any` 型の使用 | 型安全性が完全に失われる |
| `as any` キャスト | 型エラーを握りつぶす |
| `// @ts-ignore` | 型チェックをバイパス |
| 戻り値型の省略 | 型推論への過度な依存 |

#### 必須設定ファイル

```bash
# プロジェクトルートにコピー
cp sdd-templates/config/typescript/tsconfig.json ./
cp sdd-templates/config/typescript/eslint.config.mjs ./

# 依存関係インストール
npm install -D typescript @types/node eslint @eslint/js typescript-eslint
```

#### tsconfig.json 重要設定

| オプション | 値 | 効果 |
|-----------|-----|------|
| `strict` | `true` | 全厳格オプション有効 |
| `noImplicitAny` | `true` | 暗黙的any禁止 |
| `noUncheckedIndexedAccess` | `true` | インデックスアクセスでundefined考慮 |
| `exactOptionalPropertyTypes` | `true` | オプショナルプロパティ厳格化 |

#### ESLint 重要ルール

| ルール | 設定 | 効果 |
|--------|------|------|
| `@typescript-eslint/no-explicit-any` | `error` | 明示的any禁止 |
| `@typescript-eslint/no-unsafe-*` | `error` | anyからの操作禁止 |
| `@typescript-eslint/explicit-function-return-type` | `error` | 戻り値型必須 |

#### AIエージェントへの指示

```
TypeScriptコードを生成する際、以下を遵守すること：
1. any型は絶対に使用しない
2. 外部APIには必ず型定義を作成 (types/*.ts)
3. 型エラーはキャストではなく根本原因を解決
4. unknown型を使用し、型ガードで絞り込む
```

詳細は `agent_docs/conventions.md` を参照。

---

## 13. Python テストテンプレート (v1.2.4 新規)

### 13.1 テンプレートファイル一覧

| ファイル | 用途 | コピー先 |
|---------|------|---------|
| `config/testing/python/conftest.py.template` | フィクスチャ | specs/\<feature\>/tests/conftest.py |
| `config/testing/python/test_api.py.template` | APIテストパターン | specs/\<feature\>/tests/test_*.py |
| `docs/TEST_PATTERNS.md` | テストパターン集 | 参照のみ |
| `agent_docs/testing.md` | テスト実行ガイド | 参照のみ |

### 13.2 conftest.py テンプレート使用方法

```bash
# テンプレートをコピー
cp sdd-templates/config/testing/python/conftest.py.template \
   specs/<feature>/tests/conftest.py

# プレースホルダを置換
# - アプリケーションインポートを調整
# - DB設定を環境に合わせる
```

### 13.3 主要フィクスチャパターン

| フィクスチャ | 用途 | スコープ |
|-------------|------|---------|
| `client` | TestClient | function |
| `db_session` | トランザクション付きDBセッション | function |
| `buyer_user` | 買い手ユーザー | function |
| `supplier_user` | サプライヤーユーザー | function |
| `admin_user` | 管理者ユーザー | function |
| `buyer_session` | ログイン済み買い手 | function |
| `supplier_session` | ログイン済みサプライヤー | function |

### 13.4 APIテストパターン（TEST_PATTERNS.md準拠）

| パターン | テストクラス | カバー対象 |
|---------|-------------|-----------|
| 認証テスト | TestLogin, TestLogout | ログイン成功/失敗、ログアウト |
| CRUDテスト | TestCreate*, TestGet*, TestUpdate*, TestDelete* | 作成/取得/更新/削除 |
| 認可テスト | TestAuthorization | 403エラーパス |
| バリデーション | TestValidation | 422エラーパス |
| ワークフロー | TestWorkflow | 複数ステップの統合フロー |
| フィルタリング | TestFiltering | クエリパラメータ |
| ページネーション | TestPagination | page/size パラメータ |

### 13.5 pytest 実行コマンド

```bash
# 全テスト実行（E2E除外）
python -m pytest specs/<feature>/tests/ --ignore=specs/<feature>/tests/e2e

# カバレッジ付き
python -m pytest specs/<feature>/tests/ --cov=src --cov-report=term-missing

# マーカー別実行
python -m pytest specs/<feature>/tests/ -m "unit"
python -m pytest specs/<feature>/tests/ -m "integration"
python -m pytest specs/<feature>/tests/ -m "contract"

# E2E実行（Python - pytest-playwright）
python -m pytest specs/<feature>/tests/e2e/ --headed

# E2E実行（TypeScript - Playwright Test Runner）
npx playwright test specs/<feature>/tests/e2e/
npx playwright test --ui  # UIモード（デバッグ用）
```

### 13.6 E2E言語選択ガイド

| 言語 | テンプレート | 実行コマンド | 推奨ケース |
|------|-------------|-------------|-----------|
| **Python** | `e2e.spec.template.py` | `pytest --headed` | FastAPI/Django プロジェクト |
| **TypeScript** | `e2e.spec.template.ts` | `npx playwright test` | Next.js/React プロジェクト |

**選択基準**: プロジェクトのメイン言語に合わせて選択。両方利用する場合は混在可。

### 13.7 pytest-asyncio 設定

pytest-asyncio の設定は、使用するテストパターンによって異なります：

**パターン1: TestClient（同期）を使用する場合**
```toml
# pyproject.toml - TestClient使用時（asyncioプラグイン無効化）
[tool.pytest.ini_options]
addopts = ["-v", "--strict-markers", "--tb=short", "-p", "no:asyncio"]
```

**パターン2: AsyncClient（非同期）を使用する場合**
```toml
# pyproject.toml - 非同期テスト使用時
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

> **推奨**: FastAPI + SQLAlchemy の統合テストでは `TestClient`（同期）を使用し、`-p no:asyncio` を設定するのが最もシンプル。

### 13.8 カバレッジ除外設定

```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    # HTMLレンダリングはE2Eでカバー
    "src/api/routers/web.py",
    "src/templates/*",
]
```

---

## 14. テストパターン集（TEST_PATTERNS.md）

### 14.1 認証テストパターン

```python
class TestLogin:
    def test_login_success(self, client, user):
        response = client.post("/api/v1/auth/login", json={...})
        assert response.status_code == 200

    def test_login_invalid_password(self, client, user):
        response = client.post("/api/v1/auth/login", json={...})
        assert response.status_code == 401
```

### 14.2 認可テストパターン

```python
class TestAuthorization:
    def test_buyer_cannot_access_supplier_endpoint(self, client, buyer_session):
        response = client.post("/api/v1/orders/{id}/shipment", json={...})
        assert response.status_code == 403
```

### 14.3 ワークフローテストパターン

```python
class TestFullWorkflow:
    def test_complete_workflow(self, client, buyer_user, supplier_user):
        # Step 1: 作成
        # Step 2: 確認
        # Step 3: 出荷
        # Step 4: 受領
        # Step 5: 履歴確認
```

### 14.4 カバレッジ改善優先度

| 優先度 | 対象 | 理由 |
|--------|------|------|
| 高 | ビジネスロジック (service/) | バグが致命的 |
| 高 | 認証/認可 (auth/) | セキュリティ |
| 中 | APIエンドポイント (routers/) | ユーザー影響 |
| 低 | リポジトリ層 (repository/) | 統合テストでカバー |
| 除外 | HTMLレンダリング (web.py) | E2Eでカバー |

---

## 15. 実装パターン集 (v1.2.4 追加)

### 15.1 追加ドキュメント一覧

| ドキュメント | パス | 用途 |
|-------------|------|------|
| Datetime/Timezone | `docs/DATETIME_PATTERNS.md` | UTC-first設計、utcnow()禁止 |
| SQLAlchemy Async | `docs/SQLALCHEMY_PATTERNS.md` | 非同期ORM、N+1対策、マイグレーション |
| HTMX Response | `docs/HTMX_PATTERNS.md` | JSON/HTML両立、パーシャル設計 |

### 15.2 追加設定テンプレート一覧

| テンプレート | パス | 用途 |
|-------------|------|------|
| TypeScript設定 | `config/typescript/` | tsconfig.json, ESLint (any禁止) |
| 環境変数 | `config/env/.env.example` | 環境変数テンプレート |
| セキュリティ | `config/security/` | CORS, CSP, セキュリティヘッダー |
| Docker | `config/docker/` | Dockerfile, docker-compose |

### 15.3 クイックセットアップ

```bash
# 全設定を一括コピー
cp sdd-templates/config/typescript/tsconfig.json ./
cp sdd-templates/config/typescript/eslint.config.mjs ./
cp sdd-templates/config/env/.env.example ./.env
cp sdd-templates/config/docker/Dockerfile.python ./Dockerfile
cp sdd-templates/config/docker/docker-compose.yml ./
cp sdd-templates/config/docker/.dockerignore ./
```

### 15.4 重要な禁止事項 (AIエージェント向け)

| 禁止事項 | 理由 | 代替方法 |
|---------|------|---------|
| `datetime.utcnow()` | Python 3.12で非推奨 | `datetime.now(UTC)` |
| `any` 型 (TypeScript) | 型安全性喪失 | `unknown` + 型ガード |
| `/api/v1/` へのHTMX直接アクセス | JSON表示問題 | `/partials/` エンドポイント |
| rootユーザーでDocker実行 | セキュリティリスク | 非rootユーザー |
| `.env` のコミット | シークレット漏洩 | `.env.example` のみコミット |

### 15.5 開発経験から得られた教訓

#### pytest-asyncio 設定

> 詳細は **§13.7 pytest-asyncio 設定** を参照。使用するテストパターンに応じて設定を選択。

#### SQLAlchemy セッション設定

```python
session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # セッション外アクセス許可
    autoflush=False,         # 明示的フラッシュ
)
```

#### HTMX + JSON API 共存

```python
# パターン: エンドポイント分離
/api/v1/orders    → JSON (API利用者向け)
/partials/orders  → HTML (HTMX用)
```

---

## 16. インフラストラクチャ & 可観測性 (v1.2.4 追加)

### 16.1 追加テンプレート一覧

| カテゴリ | パス | 用途 |
|---------|------|------|
| **OpenTelemetry** | `config/observability/opentelemetry.py` | 分散トレーシング、計装 |
| **Prometheus** | `config/observability/prometheus.py` | メトリクス収集、APM |
| **Kubernetes** | `config/kubernetes/` | 本番デプロイマニフェスト |
| **Terraform** | `config/terraform/` | IaC (AWS EKS + RDS + Redis) |

### 16.2 OpenTelemetry クイックスタート

```python
from fastapi import FastAPI
from observability import setup_telemetry, shutdown_telemetry

app = FastAPI()

@app.on_event("startup")
async def startup():
    setup_telemetry(
        app,
        service_name="web-edi",
        instrument_db=True,
        db_engine=engine,
    )

@app.on_event("shutdown")
async def shutdown():
    shutdown_telemetry()
```

**環境変数:**
```bash
OTEL_ENABLED=true
OTEL_SERVICE_NAME=web-edi
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### 16.3 Prometheus メトリクス

```python
from prometheus import setup_metrics, track_db_query, record_order_created

app = FastAPI()
setup_metrics(app, app_name="web-edi", app_version="1.0.0")

# カスタムメトリクス
@track_db_query("select", "orders")
async def get_orders():
    ...

# ビジネスメトリクス
record_order_created(status="success")
```

**標準メトリクス:**
- `http_requests_total` - HTTPリクエスト数
- `http_request_duration_seconds` - リクエスト処理時間
- `db_query_duration_seconds` - DBクエリ時間
- `orders_created_total` - 注文作成数

### 16.4 Kubernetes デプロイ

```bash
# テンプレートをコピー
mkdir -p k8s/base
cp sdd-templates/config/kubernetes/*.yaml k8s/base/

# 変数を置換
export APP_NAME=web-edi
export NAMESPACE=web-edi
export APP_VERSION=1.0.0
envsubst < k8s/base/deployment.yaml > k8s/base/deployment.yaml.tmp
mv k8s/base/deployment.yaml.tmp k8s/base/deployment.yaml

# デプロイ
kubectl apply -k k8s/base/
```

**マニフェスト一覧:**
| ファイル | 説明 |
|---------|------|
| `deployment.yaml` | Pod定義（セキュリティコンテキスト、プローブ、リソース制限） |
| `service.yaml` | ClusterIP サービス |
| `ingress.yaml` | TLS終端、レート制限 |
| `hpa.yaml` | オートスケーリング (CPU/メモリ) |
| `configmap.yaml` | 設定・シークレット |

### 16.5 Terraform IaC

```bash
# テンプレートをコピー
mkdir -p infrastructure/terraform
cp sdd-templates/config/terraform/*.tf infrastructure/terraform/

# 初期化・デプロイ
cd infrastructure/terraform
terraform init
terraform plan -var-file=development.tfvars
terraform apply -var-file=development.tfvars
```

**構成要素:**
- VPC (3 AZ、Public/Private サブネット)
- EKS クラスター (マネージドノードグループ)
- RDS PostgreSQL (Multi-AZ オプション)
- ElastiCache Redis
- Secrets Manager

### 16.6 可観測性アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                      Application                             │
│   FastAPI + OpenTelemetry + Prometheus                      │
└───────────────────────┬─────────────────────────────────────┘
                        │ OTLP (gRPC)
                        ▼
              ┌─────────────────────┐
              │   OTel Collector    │
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  Jaeger  │   │Prometheus│   │   Loki   │
   │ (Traces) │   │ (Metrics)│   │  (Logs)  │
   └──────────┘   └──────────┘   └──────────┘
         │               │               │
         └───────────────┼───────────────┘
                         ▼
                  ┌──────────┐
                  │ Grafana  │
                  │(Dashboard)│
                  └──────────┘
```

### 16.7 インフラセットアップコマンド

```bash
# 依存関係インストール
pip install \
  opentelemetry-api opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-fastapi \
  prometheus-client

# Observability ファイルをコピー
cp sdd-templates/config/observability/opentelemetry.py src/
cp sdd-templates/config/observability/prometheus.py src/

# Docker Compose で観測スタック起動
docker-compose -f docker-compose.observability.yml up -d
```

### 16.8 環境別リソース目安

| 環境 | EKS ノード | RDS | Redis | 月額概算 |
|------|-----------|-----|-------|---------|
| Dev | t3.medium x2 | db.t3.micro | cache.t3.micro | ~$150 |
| Staging | t3.large x2 | db.t3.small | cache.t3.small | ~$250 |
| Prod | m5.large x3 | db.r6g.large (Multi-AZ) | cache.r6g.large | ~$800+ |

---

> End of CHEATSHEET.md
