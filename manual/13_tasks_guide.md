# 13. タスクガイド - tasks.md の書き方

**所要時間**: 約20分

---

## このガイドで学ぶこと

1. tasks.md の目的
2. タスクの定義方法
3. 依存関係の管理
4. マイルストーン
5. タスクとPlanの紐付け
6. **Task Completion Checklist（v1.2.5）** - タスク完了検証の必須ワークフロー
7. **BDD Acceptance Criteria（v4.5）** - 構造化受け入れ条件とエスカレーション

---

**サンプル参照**: `sdd-templates/specs/sample_feature` に Web-EDI の参考サンプルがあります（未承認/プレースホルダあり）。  
**注**: パスは例なので、自分の機能では `specs/<feature>` に置き換えます。

## 1. tasks.md の目的

### 何を書くか

**tasks.md** は「DO（何をするか）」を定義する実行可能なタスク分解です。

| 書くこと | 書かないこと |
|----------|-------------|
| 実行可能なタスク | ビジネス要件 |
| 依存関係 | 技術詳細 |
| 完了条件（DoD） | コード |
| マイルストーン | |

### 重要な原則

```
全てのテスト（TS-*）がタスク化されていること
```

### 初心者向けの粒度の目安

- 1タスクは「**1〜2日で終わる範囲**」を目安にする  
- 大きすぎるタスクは、**成果物（outputs）単位**で分割する

### このパートの引き渡し（次の成果物との関係）

tasks は「実行の台本」です。Planで決めたCT/TSを、実際に動ける作業へ落とします。

```
tasks
  -> 実装/テスト      : 作業の順番と依存関係を提供
  -> evidence_pack   : 完了条件を満たした証跡を集める
  -> Gate判定        : Tasks Gateの合否を決める
```

**最低限引き渡すべき項目**:
- plan_refs（CT/TS/Phase/Group）
- done_when（完了条件）
- outputs（成果物パス）
- depends_on（依存関係）

---

## 2. タスクの定義方法

### 2.1 タスクの構造

```yaml
tasks:
  tasks:
    - id: "T-G01-001"
      title: "Define interface contract (CT-API-01)"
      type: "contract"
      description: "OpenAPI形式で契約を定義し、レビュー可能な形にする"
      spec_refs: ["US-FEAT001-001", "AC-US-FEAT001-001-01"]
      plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1", "LIB-01", "CMP-01"]
      bpmn_refs: ["BPMN-TASK-001"]
      depends_on: []
      outputs:
        - "sdd-templates/specs/sample_feature/contracts/openapi.yaml"
      done_when:
        - "Contract artifact exists and is reviewable"
        - "Versioning policy is documented"
        - "stride-lint passes"
```

### 2.2 タスクID命名規則

```
T-<グループ>-<連番>

例: T-G01-001, T-G01-002, T-G02-001
```

### 2.3 タスクタイプ

| type | 説明 | 例 |
|------|------|-----|
| `contract` | 契約定義 | OpenAPI作成、契約テスト |
| `test` | テスト作成・実行 | 統合テスト、E2Eテスト |
| `impl` | 実装 | コード実装 |
| `docs` | ドキュメント | 設計書、手順書 |
| `research` | 調査 | 技術調査、PoC |
| `ops` | 運用 | 監視設定、デプロイ |
| `pmo` | 管理 | 進捗管理、レビュー調整 |

### 2.4 spec_refs（仕様への参照）

```yaml
spec_refs: ["US-FEAT001-001", "AC-US-FEAT001-001-01"]
```

- USやACへの参照を記載
- タスクがどの仕様を満たすかを明示

### 2.5 plan_refs（計画への参照）

```yaml
plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1", "LIB-01", "CMP-01"]
```

**重要**: plan_refs は **stable id のみ** 使用可能

| 許可されるID | 例 |
|-------------|-----|
| CMP-* | CMP-01 |
| LIB-* | LIB-01 |
| CT-* | CT-API-01 |
| TS-* | TS-INT-01 |
| Phase-* | Phase-1 |
| G-* | G-01-contracts |

### 2.6 done_when（完了条件）

```yaml
done_when:
  - "Contract artifact exists and is reviewable"
  - "Versioning policy is documented"
  - "stride-lint passes"
```

- 具体的で検証可能な条件を記載
- 「stride-lint passes」を含めることを推奨
 - **「できたかどうか」を第三者が判断できる書き方**にする

---

## 3. 依存関係の管理

### 3.1 depends_on

```yaml
- id: "T-G01-002"
  title: "Write contract tests (TS-CON-01)"
  depends_on: ["T-G01-001"]  # ← T-G01-001 が完了してから着手
```

### 3.2 依存関係の図解

```
T-G01-001 (契約定義)
     │
     ▼
T-G01-002 (契約テスト)
     │
     ▼
T-G02-001 (運用ベースライン)
     │
     ▼
T-G03-001 (統合テスト)
     │
     ▼
T-G04-001 (E2Eセットアップ)
     │
     ▼
T-G04-002 (E2Eテスト作成)
```

### 3.3 循環依存の禁止

```yaml
# ❌ 間違い（循環依存）
- id: "T-G01-001"
  depends_on: ["T-G01-002"]

- id: "T-G01-002"
  depends_on: ["T-G01-001"]  # ← 循環！
```

---

## 4. マイルストーン

### 4.1 マイルストーンの定義

```yaml
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
        - "integrationタグ付きACがTS-INTでカバーされている"
      related_task_ids: ["T-G03-001"]

    - id: "M-03"
      name: "E2E smoke runnable"
      exit_criteria:
        - "TS-E2E-* exists"
        - "e2eタグ付きACがTS-E2Eでカバーされている"
        - "e2e-triage.md が定義されている"
      related_task_ids: ["T-G04-001", "T-G04-002", "T-G04-003"]
```

### 4.2 マイルストーンID命名規則

```
M-<連番>

例: M-01, M-02, M-03
```

---

## 5. テストのタスク化

### 5.1 重要ルール

**Plan の全 TS-* は Tasks にタスク化されていること**

```yaml
# plan.md
tests:
  - id: "TS-INT-01"  # ← このテストは...

# tasks.md
tasks:
  - id: "T-G03-001"
    plan_refs: ["TS-INT-01"]  # ← タスクでplan_refsに含める
```

### 5.2 テストタスクのテンプレート

```yaml
# 契約テスト
- id: "T-G01-002"
  title: "Write contract tests (TS-CON-01)"
  type: "test"
  spec_refs: ["AC-US-FEAT001-001-01"]
  plan_refs: ["TS-CON-01", "CT-API-01", "G-01-contracts"]
  depends_on: ["T-G01-001"]
  outputs:
    - "sdd-templates/specs/sample_feature/tests/contract/"
  done_when:
    - "Tests exist"
    - "covers_contract_ids に CT-API-01 が含まれている"
    - "stride-lint passes"

# 統合テスト
- id: "T-G03-001"
  title: "Write integration tests (TS-INT-01)"
  type: "test"
  spec_refs: ["AC-US-FEAT001-001-01"]
  plan_refs: ["TS-INT-01", "CT-API-01", "G-03-integration-tests"]
  depends_on: ["T-G02-001"]
  outputs:
    - "sdd-templates/specs/sample_feature/tests/integration/"
  done_when:
    - "Integration tests exist and are runnable"
    - "integrationタグ付きACが TS-INT-01 でカバーされている"
    - "stride-lint passes"

# E2Eテスト
- id: "T-G04-002"
  title: "Write E2E smoke test (TS-E2E-01)"
  type: "test"
  spec_refs: ["AC-US-FEAT001-001-02"]
  plan_refs: ["TS-E2E-01", "CT-API-01", "G-04-e2e-tests"]
  depends_on: ["T-G04-001"]
  outputs:
    - "sdd-templates/specs/sample_feature/tests/e2e/"
  done_when:
    - "Test exists and is deterministic"
    - "e2eタグ付きACが TS-E2E-01 でカバーされている"
    - "stride-lint passes"
```

---

## 6. E2E関連タスク

### 6.1 E2Eセットアップタスク

```yaml
- id: "T-G04-001"
  title: "Set up E2E test harness (Playwright)"
  type: "test"
  description: "PlaywrightのE2E基盤とレポート出力を整備"
  plan_refs: ["TS-E2E-01", "G-04-e2e-tests", "Phase-2"]
  depends_on: ["T-G03-001"]
  outputs:
    - "sdd-templates/specs/sample_feature/tests/e2e/"
    - "sdd-templates/specs/sample_feature/tests/reports/e2e/"
  done_when:
    - "E2E tests runnable locally and in CI"
    - "playwright.config.ts に reporting 設定が含まれている"
```

### 6.2 E2E Triageタスク

```yaml
- id: "T-G04-003"
  title: "E2E failure triage procedure"
  type: "ops"
  description: "E2E失敗時の分類と還流手順を定義"
  plan_refs: ["G-04-e2e-tests", "Phase-2"]
  depends_on: ["T-G04-001"]
  outputs:
    - "sdd-templates/specs/sample_feature/implementation-details/e2e-triage.md"
  done_when:
    - "Triage rules (product_bug/spec_gap/test_bug/flake) are documented"
    - "還流先（Spec/Plan/Tasks）と担当者が明記されている"
```

---

## 7. counts の更新

```yaml
derived_fields:
  counts:
    tasks: 7                      # タスク数
    use_cases_referenced: 1       # 参照されたUS数
    acceptance_referenced: 2      # 参照されたAC数
    tasks_with_plan_refs: 7       # plan_refsを持つタスク数
    dependency_edges: 6           # 依存関係の数
    milestones: 3                 # マイルストーン数
```

---

## 8. ゲート通過条件

### Tasks Gate の条件

```yaml
tasks_gate_check:
  rules:
    min_tasks: 5                           # タスク最低5件
    min_use_cases_referenced: 1            # US参照最低1件
    min_acceptance_referenced: 1           # AC参照最低1件

  # 必須条件
  all_us_covered: true                     # 全USがタスクで参照
  all_ac_tested: true                      # 全ACがテストタスクで参照
  groups_mapped: true                      # グループへのマッピング完了
  no_dependency_errors: true               # 依存エラーなし

  # 全タスクがplan_refsを持つ
  tasks_with_plan_refs == tasks

  # 最終フラグ
  tasks_ready_for_code: true
```

---

## 9. よくある間違いと対処法

### 間違い1: テストがタスク化されていない

```yaml
# ❌ 間違い
# plan.md にはTS-INT-01がある
# tasks.md のplan_refsにTS-INT-01がない

# ✅ 正しい
- id: "T-G03-001"
  plan_refs: ["TS-INT-01", ...]  # ← 必ず含める
```

**エラーコード**: `TEST_NOT_TASKED`

### 間違い2: plan_refsに不正なIDを使用

```yaml
# ❌ 間違い（不正なID形式）
plan_refs: ["some-random-name", "Task-1"]

# ✅ 正しい（stable idのみ）
plan_refs: ["CMP-01", "LIB-01", "CT-API-01", "TS-INT-01", "Phase-1", "G-01-contracts"]
```

**エラーコード**: `INVALID_PLAN_REF`

### 間違い3: 循環依存

```yaml
# ❌ 間違い
- id: "T-G01-001"
  depends_on: ["T-G02-001"]
- id: "T-G02-001"
  depends_on: ["T-G01-001"]  # ← 循環

# ✅ 正しい（一方向の依存）
- id: "T-G01-001"
  depends_on: []
- id: "T-G02-001"
  depends_on: ["T-G01-001"]
```

---

## 10. 実践例

### 完成したtasks.md の例（抜粋）

```yaml
tasks:
  tasks:
    # Phase-1: Contracts
    - id: "T-G01-001"
      title: "Define interface contract (CT-API-01)"
      type: "contract"
      spec_refs: ["US-FEAT001-001", "AC-US-FEAT001-001-01"]
      plan_refs: ["CT-API-01", "TS-CON-01", "G-01-contracts", "Phase-1"]
      depends_on: []
      outputs: ["sdd-templates/specs/sample_feature/contracts/openapi.yaml"]
      done_when: ["stride-lint passes"]

    - id: "T-G01-002"
      title: "Write contract tests (TS-CON-01)"
      type: "test"
      spec_refs: ["AC-US-FEAT001-001-01"]
      plan_refs: ["TS-CON-01", "CT-API-01", "G-01-contracts"]
      depends_on: ["T-G01-001"]
      outputs: ["sdd-templates/specs/sample_feature/tests/contract/"]
      done_when: ["stride-lint passes"]

    # Phase-2: Integration & E2E
    - id: "T-G03-001"
      title: "Write integration tests (TS-INT-01)"
      type: "test"
      spec_refs: ["AC-US-FEAT001-001-01"]
      plan_refs: ["TS-INT-01", "G-03-integration-tests"]
      depends_on: ["T-G02-001"]
      outputs: ["sdd-templates/specs/sample_feature/tests/integration/"]
      done_when: ["integrationタグ付きACがカバーされている"]

    - id: "T-G04-002"
      title: "Write E2E smoke test (TS-E2E-01)"
      type: "test"
      spec_refs: ["AC-US-FEAT001-001-02"]
      plan_refs: ["TS-E2E-01", "G-04-e2e-tests"]
      depends_on: ["T-G04-001"]
      outputs: ["sdd-templates/specs/sample_feature/tests/e2e/"]
      done_when: ["e2eタグ付きACがカバーされている"]

  milestones:
    - id: "M-01"
      name: "Contracts ready"
      exit_criteria: ["All CT-* defined", "TS-CON-* covers all CT-*"]
      related_task_ids: ["T-G01-001", "T-G01-002"]
```

---

## 11. Task Completion Checklist（v1.2.5 必須）

> **重要**: タスクを「完了」と報告する前に、以下のチェックリストを必ず実行すること。
> 「動いた」は「完了」ではない。仕様の**全要素**を満たして初めて「完了」となる。

### 11.1 完了報告前の3ステップ検証

#### Step 1: spec.md 全量確認

1. 該当タスクの `spec_refs` に含まれる全ACを読み直す
2. 各ACの全要素を確認（部分的な実装ではないか）:
   - ACに記載された全てのキーワード・条件を見落としていないか
3. **ACに書かれていない要素は確認不要**（過剰な確認は避ける）

#### Step 2: plan.md トレーサビリティ確認

1. 該当タスクの `plan_refs` に含まれるTS（テスト）を確認
2. TSが実装されており、カバレッジ条件を満たしているか

#### Step 3: scenarios.yaml 検証（重要）

1. `tests/scenarios.yaml` を開く
2. 該当タスクに関連するシナリオを特定（`covers_acs` を確認）
3. シナリオの全 `expected` を一つずつ検証
4. `completion_checklist` の全項目を確認

### 11.2 scenarios.yaml の構造

```yaml
test_scenarios:
  feature_id: "FEAT-001"

  scenarios:
    - id: "SCN-001"
      name: "基本フロー（正常系）"
      priority: "critical"   # critical | high | medium | low

      # このシナリオがカバーするAC
      covers_acs:
        - "AC-US-FEAT001-001-01"
        - "AC-US-FEAT001-001-02"

      steps:
        - step: 1
          action: "操作1を記載"
        - step: 2
          action: "操作2を記載"

      expected:
        - id: "EXP-001-01"
          description: "期待結果1を記載"
          verification_method: "UI確認"
        - id: "EXP-001-02"
          description: "期待結果2を記載"
          verification_method: "API確認"

      # 完了検証チェックリスト（AI/開発者用）
      completion_checklist:
        - "全 expected が満たされているか"
        - "covers_acs の全ACに記載された要素を満たしているか"
```

### 11.3 Anti-Patterns（避けるべき行動）

| Anti-Pattern | 問題点 | 正しいアプローチ |
|-------------|--------|-----------------|
| 「正常系が動いた」だけで完了と報告 | エラー系未検証 | scenarios.yaml の全シナリオを検証 |
| expected の一部だけ確認 | 検証漏れ | 全 expected を一つずつ確認 |
| covers_acs を確認せずに完了 | AC見落とし | covers_acs の全ACを spec.md で再読 |
| ACの一部キーワードだけ確認 | 部分的な実装 | ACの全要素を満たす |

### 11.4 完了報告フォーマット

```markdown
## タスク完了報告: T-G01-001

### spec_refs 検証
- US-FEAT001-001: ✅ 全フロー確認済み
- AC-US-FEAT001-001-01: ✅ 全要素確認済み
  - (確認した要素を列挙)

### シナリオ検証: SCN-001
- EXP-001-01: ✅ (検証方法: UI確認)
- EXP-001-02: ✅ (検証方法: API確認)

### Completion Checklist
- [x] 全 expected が満たされているか
- [x] covers_acs の全ACに記載された要素を満たしているか

### 証跡
- stride-lint: PASS
- テスト実行結果: (リンクまたはスクリーンショット)
```

### 11.5 tasks_template.md の completion_verification セクション

tasks.md テンプレートには以下のセクションが含まれています：

```yaml
# tasks.md
completion_verification:
  mandatory_before_complete:
    - "spec_refs に含まれる全ACを最後まで読み直す"
    - "各ACに記載された全要素を満たしているか確認（ACにない要素は確認不要）"
    - "tests/scenarios.yaml の該当シナリオを特定し、全 expected を検証"
    - "stride-lint が PASS している"

  anti_patterns:
    - "「正常系が動いた」だけで完了と報告する"
    - "ACの一部のキーワードだけ確認して完了とする"
    - "scenarios.yaml を確認せずに完了と報告する"
    - "エラー系シナリオを検証せずに完了と報告する"
```

---

## 12. BDD Acceptance Criteria（v4.5）

> **v4.5 新機能**: タスクの完了条件を BDD（振る舞い駆動開発）形式の Given-When-Then で構造化する。
> 人間のレビューポイントを「コードレビュー」から「仕様・受け入れ条件のレビュー」へ上流シフトする。

### 12.1 ヘッダーフィールド

tasks.md のフロントマターに以下を追加：

```yaml
bdd_mode: "required"           # required | optional
escalation_policy_ref: "memory/constitution.md#escalation_triggers"
verification_matrix:
  automated_ratio_target: 0.8  # automated の比率目標（80%以上）
  hitl_max: 3                  # hitl 検証の最大数
```

### 12.2 acceptance_criteria の構造

各タスクの `done_when` の直後に `acceptance_criteria` を追加する（`done_when` は削除しない）。

```yaml
- id: "T-G01-001"
  title: "Define interface contract (CT-API-01)"
  done_when:
    - "Contract artifact exists and is reviewable"
  acceptance_criteria:
    - id: "AC-T-G01-001-01"
      scenario: "契約アーティファクトが存在しレビュー可能である"
      given: "CT-API-01 の契約定義が完了している"
      when: "contracts/ ディレクトリを確認する"
      then: "OpenAPI/EventSchema等の契約ファイルが存在し、バージョニングポリシーが記載されている"
      verification: "automated"
      escalation_trigger: false
```

### 12.3 verification フィールド

| 値 | 意味 | 例 |
|----|------|-----|
| `automated` | テスト/型チェック/stride-lint で自動検証可能 | 契約テスト、lint |
| `manual` | 人間の目視確認が必要 | UIレイアウト、ドキュメント |
| `hitl` | Human-in-the-Loop による判断が必要 | ビジネスロジックの妥当性 |

**目標**: `automated` の比率が `verification_matrix.automated_ratio_target`（デフォルト 80%）以上。

### 12.4 escalation_trigger

以下に該当するタスクは `escalation_trigger: true` を設定し、実装完了後に**人間レビューを必須**とする：

| # | 条件 | 理由 |
|---|------|------|
| 1 | 認証・認可ロジックの変更 | セキュリティ侵害リスク |
| 2 | DBスキーマのマイグレーション（既存データに影響） | データ消失・整合性破損リスク |
| 3 | 新規外部依存の追加（npm/pypi/Docker） | サプライチェーン攻撃リスク |
| 4 | 支払・金銭処理に関わるロジック | 金銭的損失リスク |
| 5 | セキュリティ設定の変更 | 攻撃面拡大リスク |

```yaml
# 例: 認証ロジック変更タスク
- id: "T-G02-003"
  title: "Implement OAuth2 token refresh"
  acceptance_criteria:
    - id: "AC-T-G02-003-01"
      scenario: "トークンリフレッシュが正しく動作する"
      given: "アクセストークンが期限切れである"
      when: "リフレッシュトークンでトークンを再取得する"
      then: "新しいアクセストークンが発行される"
      verification: "automated"
      escalation_trigger: true   # ← 認証ロジックなので必須
```

### 12.5 BDD Lint ルール（stride-lint）

| ルール | 内容 | 違反時 |
|--------|------|--------|
| AC-001 | `acceptance_criteria` フィールドの存在確認 | WARNING |
| AC-002 | BDD構造の完全性（id/scenario/given/when/then/verification） | ERROR |
| AC-003 | `verification` 値の妥当性（automated/manual/hitl） | ERROR |
| AC-004 | auth/payment/schema/security キーワード含むタスクの `escalation_trigger` 確認 | WARNING |
| AC-005 | `automated` 比率が `automated_ratio_target` 以上か | WARNING |

### 12.6 done_when との関係

- `done_when` は**後方互換性**のために維持する（非推奨にはしない）
- `acceptance_criteria` はより構造化された完了条件
- 移行期間中は AC-001 は WARNING（将来的に ERROR 化を検討）

---

## チェックリスト

- [ ] 全テスト（TS-*）をタスク化した
- [ ] plan_refs に stable id のみ使用した
- [ ] 依存関係に循環がない
- [ ] done_when に具体的な完了条件を書いた
- [ ] マイルストーンを定義した
- [ ] counts を更新した
- [ ] **（v1.2.5）完了報告前に Task Completion Checklist を実施した**
- [ ] **（v4.5）全タスクに acceptance_criteria（BDD形式）を記載した**
- [ ] **（v4.5）escalation_trigger 該当タスクに true を設定した**

---

## 次のステップ

→ [07. Evidence Packガイド](14_evidence_pack_guide.md)

---

> SDD Templates Manual - 06. Tasks Guide
