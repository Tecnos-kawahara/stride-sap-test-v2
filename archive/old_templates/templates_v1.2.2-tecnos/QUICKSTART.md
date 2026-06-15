# Quick Start Guide: templates_v1.2.2-tecnos

新規参画者向けの最短ルートガイドです。5ステップで SDD テンプレートの使い方を理解できます。

---

## Step 1: 全体像を把握する（5分）

### SDD (Specification-Driven Development) とは？

```
Human → basic_design.md → BPMN → spec.md → plan.md → tasks.md → Implementation
         (WHAT/WHY)     (Flow)  (WHAT)    (HOW)     (DO)       (Code)
```

- **Spec が正本**: コードより Spec が正しい
- **HITL (Human-in-the-Loop)**: AI生成物は必ず人間がレビュー
- **Gate System**: 各フェーズで品質チェック

### ファイル構成

```
specs/<feature_name>/
├── basic_design.md    # 認識合わせ（WHAT/WHY）
├── process.bpmn       # 業務フロー（Camunda 8形式）
├── spec.md            # 仕様書（ACが主役）
├── plan.md            # 実装方針（テスト戦略含む）
├── tasks.md           # 実行タスク
└── implementation-details/
    └── e2e-triage.md  # E2E失敗時の対応手順
```

---

## Step 2: 最初の10行を理解する（10分）

### basic_design.md の冒頭

```yaml
---
artifact: "basic_design"
feature_id: "FEAT-XXX"           # 機能ID
basic_design_id: "BD-XXX"        # 設計書ID
title: "Basic Design - <機能名>"
version: "1.2.2-tecnos"          # テンプレートバージョン
status: "draft"                  # draft → in_review → approved
---
```

**ポイント**: YAML Front Matter で ID と状態を管理

### spec.md の重要部分

```yaml
use_cases:
  - id: "US-FEATXXX-001"
    title: "ユースケース"
    acceptance:
      - id: "AC-US-FEATXXX-001-01"
        statement: "前提/操作/期待結果を1文で記述"
        tags: ["integration"]    # ← テストタイプを示すタグ
        priority: "must"
```

**ポイント**: AC の `tags` が対応するテストタイプを決定

### plan.md の重要部分

```yaml
test_strategy:
  coverage_policy:
    acceptance_coverage_required: true    # 全ACをテストでカバー必須
    tagged_acceptance_requirements:
      integration:
        enforce: true
        required_test_type: "integration"  # integrationタグ→TS-INT
      e2e:
        enforce: true
        required_test_type: "e2e"          # e2eタグ→TS-E2E
```

**ポイント**: Coverage Policy が品質ゲートを定義

---

## Step 3: ID規約を覚える（5分）

| カテゴリ | 形式 | 例 |
|----------|------|-----|
| Feature | `FEAT-XXX` | FEAT-001 |
| Use Case | `US-FEAT<ID>-NNN` | US-FEAT001-001 |
| Acceptance Criteria | `AC-US-<US_ID>-NN` | AC-US-FEAT001-001-01 |
| Contract | `CT-<TYPE>-NN` | CT-API-01, CT-EVT-01 |
| Test Spec (Unit) | `TS-UT-NN` | TS-UT-01 |
| Test Spec (Integration) | `TS-INT-NN` | TS-INT-01 |
| Test Spec (Contract) | `TS-CON-NN` | TS-CON-01 |
| Test Spec (E2E) | `TS-E2E-NN` | TS-E2E-01 |
| Task | `T-<GROUP>-NNN` | T-G01-001 |
| BPMN Element | `BPMN-(TASK\|GW\|EVT)-NNN` | BPMN-TASK-001 |

**覚え方**: `<種別>-<親ID>-<連番>`

---

## Step 4: speckit-lint を実行する（5分）

### 基本コマンド

```bash
# 単一機能を検証
speckit-lint specs/feature_name/

# カバレッジレポート出力
speckit-lint specs/feature_name/ --coverage-report

# 警告のみ（fail しない）
speckit-lint specs/feature_name/ --warn-only
```

### よくあるエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `AC_NOT_COVERED` | ACがテストでカバーされていない | TSに`covers_acceptance_ids`追加 |
| `REF_NOT_FOUND` | 参照先IDが存在しない | IDのtypoを確認 |
| `TAGGED_AC_NOT_COVERED...` | タグに対応するテストがない | integrationタグ→TS-INT追加 |

---

## Step 5: 最初の機能を作成する（15分）

### 5.1 ディレクトリ作成

```bash
mkdir -p specs/my_first_feature/implementation-details
```

### 5.2 テンプレートをコピー

```bash
cp templates_v1.2.2-tecnos/templates/basic_design_template.md specs/my_first_feature/basic_design.md
cp templates_v1.2.2-tecnos/templates/spec_template.md specs/my_first_feature/spec.md
cp templates_v1.2.2-tecnos/templates/plan_template.md specs/my_first_feature/plan.md
cp templates_v1.2.2-tecnos/templates/tasks_template.md specs/my_first_feature/tasks.md
```

### 5.3 ID を置換

```bash
# FEATXXX → 実際のID に置換
sed -i 's/FEATXXX/001/g' specs/my_first_feature/*.md
sed -i 's/XXX_feature_name/my_first_feature/g' specs/my_first_feature/*.md
```

### 5.4 最小限の内容を記入

**basic_design.md**:
1. `context.who/what/why` を埋める
2. `traceability_rows` に最低1行追加
3. `integration_flows` に最低1フロー追加

**spec.md**:
1. `use_cases` に最低1つのUSを追加
2. ACを合計3件以上にし、integrationタグ付きACを最低1件含める
3. NFRを合計6件以上にし、integration/data/security を最低1件ずつ含める
4. `derived_fields.counts` を更新

**plan.md**:
1. `contracts` に最低1つのCTを追加
2. `tests` に各ACをカバーするTSを追加
3. `coverage_policy` を設定

**tasks.md**:
1. 各TSに対応するタスクを追加
2. `milestones` にゲートを設定

### 5.5 検証

```bash
speckit-lint specs/my_first_feature/ --warn-only
```

---

## よくある間違いと対処法

### 1. ID の不一致

```yaml
# ❌ 間違い: AC-ID と covers_acceptance_ids が一致しない
acceptance:
  - id: "AC-US-FEAT001-001-01"  # ← 実際のID

tests:
  - covers_acceptance_ids: ["AC-US-FEAT001-01"]  # ← typo（-001 が抜けている）
```

**対処**: IDは完全一致が必要。コピペを推奨。

### 2. タグとテストタイプの不一致

```yaml
# ❌ 間違い: integration タグなのに TS-UT でカバー
acceptance:
  - id: "AC-..."
    tags: ["integration"]

tests:
  - id: "TS-UT-01"  # ← TS-INT-* であるべき
    covers_acceptance_ids: ["AC-..."]
```

**対処**: タグに応じたテストタイプを使用
- `integration` → `TS-INT-*`
- `e2e` → `TS-E2E-*`

### 3. counts の更新忘れ

```yaml
# ❌ 間違い: ACを追加したが counts を更新していない
use_cases:
  - acceptance:
      - id: "AC-1"
      - id: "AC-2"  # ← 追加した

derived_fields:
  counts:
    acceptance_criteria: 1  # ← 2 であるべき
```

**対処**: AC/US/CT を追加したら必ず counts を更新

### 4. plan_refs の欠落

```yaml
# ❌ 間違い: tasks にテストがタスク化されていない
# plan.md
tests:
  - id: "TS-INT-01"

# tasks.md
tasks:
  - id: "T-G03-001"
    plan_refs: []  # ← TS-INT-01 がない
```

**対処**: Plan の各テストは Tasks でタスク化必須（`tests_must_be_tasked: true`）

---

## 次のステップ

1. **CHEATSHEET.md** を参照して ID規約を確認
2. **constitution.md** を読んで Nine Articles を理解
3. **speckit_lint_spec.md** を読んで検証ルールを把握
4. **tecnos_org_constraints.md** を読んで組織制約を確認

---

## サポート

- テンプレート質問: Arch チームへ
- speckit-lint エラー: エラーメッセージで検索 or Arch チームへ
- 移行相談: MIGRATION.md を参照

---

> End of QUICKSTART.md
