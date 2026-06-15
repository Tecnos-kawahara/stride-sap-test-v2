# Quick Start Guide: sdd-templates

新規参画者向けの最短ルートガイドです。5ステップで SDD テンプレートの使い方を理解できます。

---

## Step 1: 全体像を把握する（5分）

### SDD (Specification-Driven Development) とは？

```
Human → basic_design.md → BPMN → spec.md → plan.md → tasks.md → Implementation
         (WHAT/WHY)     (Flow)  (WHAT)    (HOW)     (DO)       (Code)
              ↓           ↓        ↓          ↓          ↓
           Gate 1,2    approval  Gate 3,4  approval   Gate 5   → Final
```

- **Spec が正本**: コードより Spec が正しい
- **HITL (Human-in-the-Loop)**: AI生成物は必ず人間がレビュー
- **Gate System**: 各フェーズで品質チェック
- **APPROVAL.md**: 人間のみが編集できる承認記録（AIは編集禁止）

### ファイル構成

```
specs/<feature_name>/
├── APPROVAL.md        # 承認記録（人間のみ編集可能）
├── basic_design.md    # 認識合わせ（WHAT/WHY）
├── process.bpmn       # 業務フロー（Camunda 8形式）
├── spec.md            # 仕様書（ACが主役）
├── plan.md            # 実装方針（テスト戦略含む）
├── tasks.md           # 実行タスク
├── contracts/         # Spec-as-Code（OpenAPI等）
├── tests/             # テスト資産（scenarios.yaml等）
└── implementation-details/
    ├── e2e-triage.md      # E2E失敗時の対応手順
    ├── evidence_pack.md   # Evidence Pack（ゲート証跡）
    ├── migration_mapping.yaml
    └── authz_matrix.yaml
```

---

## Step 2: 最初の10行を理解する（10分）

### basic_design.md の冒頭

```yaml
---
artifact: "basic_design"
feature_id: "FEAT-XXX"           # 機能ID
basic_design_id: "BD-XXX"        # 設計書ID
title: "Basic Design - Web-EDI受注受付"
version: "{{TEMPLATE_VERSION}}"  # テンプレートバージョン（stride initで自動設定）
status: "draft"                  # draft → in_review → approved
---
```

**ポイント**: YAML Front Matter で ID と状態を管理

### spec.md の重要部分

```yaml
use_cases:
  - id: "US-FEATXXX-001"
    title: "Web-EDI発注送信"
    acceptance:
      - id: "AC-US-FEATXXX-001-01"
        statement: "発注CSV(10行)を送信すると、60秒以内に受注番号が表示される"
        tags: ["integration", "performance"]    # ← テストタイプを示すタグ
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

### spec.md のSpec-as-Code（追加）

```yaml
spec_as_code:
  artifacts:
    - type: "openapi"
      path: "specs/my_feature/contracts/openapi.yaml"
    - type: "database_schema"  # DB使用時のみ
      path: "specs/my_feature/contracts/database_schema.yaml"
    - type: "migration_mapping"
      path: "specs/my_feature/implementation-details/migration_mapping.yaml"
```

**ポイント**: 機械可読仕様のパスを必ず列挙

**DB使用時の補助テンプレート**:
```bash
cp sdd-templates/templates/contracts/database_schema_input.csv /tmp/tables.csv
```

### plan.md のEvidence Pack（追加）

```yaml
evidence_pack:
  required_artifacts: ["ci_results", "sast", "sca", "secrets_scan", "ai_provenance"]
  storage:
    path: "specs/my_feature/implementation-details/evidence_pack.md"
```

**ポイント**: ゲート判定の証跡（CI/SAST/SCA/Secrets/AIプロヴェナンス）を固定

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

## Step 4: stride CLI を実行する（5分）

### stride CLI の基本

```bash
# stride を PATH に追加（推奨）
export PATH="$PATH:$(pwd)/sdd-templates/bin"

# または直接実行
./sdd-templates/bin/stride <command>
```

### 基本コマンド

```bash
# 新規機能の初期化（テンプレートを自動コピー）
stride init my_feature

# 単一機能を検証
stride lint specs/feature_name/

# カバレッジレポート出力
stride lint specs/feature_name/ --coverage-report

# 警告のみ（fail しない）
stride lint specs/feature_name/ --warn-only

# Phase Gate 状態確認
stride phase-status specs/feature_name/

# ヘルプ表示
stride help
```

※ 旧コマンド `python3 sdd-templates/tools/stride_lint.py` も引き続き使用可能です。

### Enterprise Hierarchy（オプション）

`--scale enterprise` は Monorepo / CI 規模の指定であり、Epic/Feature 階層の有効化とは別です。階層型で運用する場合は `sdd-templates/config/enterprise.yaml` を有効にします。

```bash
# 1. Enterprise Hierarchy を有効化
cat > sdd-templates/config/enterprise.yaml <<'YAML'
enterprise:
  enabled: true
YAML

# 2. Epic を作成
stride epic init EPIC-ORDER

# 3. Epic 配下に Feature を作成
stride init order_import --epic EPIC-ORDER --team TEAM-A

# 4. Enterprise 拡張 lint
stride lint specs/order_import/ --enterprise
```

> Epic に team が 1 つだけ定義されている場合は `team_id` が自動設定されます。複数 team の Epic では `--team` 指定が必要です。
>
> Enterprise 機能のサンプルは `epics/EPIC-SAMPLE/` と `specs/FEAT-ERPSAMPLE/` を参照してください。
> `stride epic features EPIC-SAMPLE` で Epic 配下の Feature 一覧を確認できます。

### よくあるエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `AC_NOT_COVERED` | ACがテストでカバーされていない | TSに`covers_acceptance_ids`追加 |
| `REF_NOT_FOUND` | 参照先IDが存在しない | IDのtypoを確認 |
| `TAGGED_AC_NOT_COVERED...` | タグに対応するテストがない | integrationタグ→TS-INT追加 |
| `SPEC_AS_CODE_MISSING` | Spec-as-Codeが未定義 | `spec.spec_as_code.artifacts`を追加 |
| `EVIDENCE_PACK_NOT_DEFINED` | Evidence Packが未定義 | `plan.test_strategy.evidence_pack`を追加 |
| `PLACEHOLDER_VALUE_PRESENT` | プレースホルダが残っている | `FEAT-XXX` 等を置換 |
| `ARTIFACT_REGISTRY_INVALID` | 成果物マスターが不正 | `memory/artifact_registry.md` を見直す |
| `APPROVAL_PENDING` | 人間の承認待ち | APPROVAL.md でチェックボックスを `[x]` に変更 |
| `APPROVAL_FILE_MISSING` | APPROVAL.md がない | テンプレートからコピー |

---

## Step 5: 最初の機能を作成する（5分）

### 推奨: stride init を使用

```bash
# 一発でテンプレートを配置（推奨）
stride init my_first_feature

# Epic 配下に作る場合（Enterprise Hierarchy 有効時）
stride init my_first_feature --epic EPIC-ORDER --team TEAM-A

# 作成されるファイル:
# specs/my_first_feature/
# ├── APPROVAL.md
# ├── basic_design.md
# ├── spec.md
# ├── plan.md
# ├── tasks.md
# ├── contracts/
# │   └── openapi.yaml
# ├── tests/
# └── implementation-details/
#     ├── evidence_pack.md
#     ├── ops.md
#     └── e2e-triage.md
```

> **重要**: APPROVAL.md は人間のみが編集できるファイルです。AIは編集してはいけません。

### 手動セットアップ（stride init を使わない場合）

<details>
<summary>クリックして展開</summary>

#### 5.1 ディレクトリ作成

```bash
mkdir -p specs/my_first_feature/{contracts,tests,implementation-details}
```

#### 5.2 テンプレートをコピー

```bash
cp sdd-templates/templates/APPROVAL.md specs/my_first_feature/APPROVAL.md
cp sdd-templates/templates/basic_design_template.md specs/my_first_feature/basic_design.md
cp sdd-templates/templates/spec_template.md specs/my_first_feature/spec.md
cp sdd-templates/templates/plan_template.md specs/my_first_feature/plan.md
cp sdd-templates/templates/tasks_template.md specs/my_first_feature/tasks.md
cp sdd-templates/templates/evidence_pack_template.md specs/my_first_feature/implementation-details/evidence_pack.md
cp sdd-templates/templates/ops_template.md specs/my_first_feature/implementation-details/ops.md
cp sdd-templates/templates/contracts/openapi_template.yaml specs/my_first_feature/contracts/openapi.yaml
cp sdd-templates/memory/artifact_registry.md memory/artifact_registry.md
```

#### 5.3 ID を置換

```bash
# macOS の場合（サブディレクトリも含む）
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i '' 's/FEATXXX/001/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i '' 's/XXX_feature_name/my_first_feature/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i '' 's/{{FEATURE_NAME}}/my_first_feature/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i '' 's/{{FEATURE_ID}}/001/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml

# Linux の場合（サブディレクトリも含む）
sed -i 's/FEAT-XXX/FEAT-001/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i 's/FEATXXX/001/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i 's/XXX_feature_name/my_first_feature/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i 's/{{FEATURE_NAME}}/my_first_feature/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
sed -i 's/{{FEATURE_ID}}/001/g' specs/my_first_feature/*.md specs/my_first_feature/*/*.md specs/my_first_feature/*/*.yaml
```

</details>

### 5.4 最小限の内容を記入

**basic_design.md**:
1. `context.who/what/why` を埋める
2. `traceability_rows` に最低1行追加
3. `integration_flows` に最低1フロー追加
4. `delivery_model` を決定し、`raci_plus` / `ai_policy` / `artifact_registry` を明記

**spec.md**:
1. `use_cases` に最低1つのUSを追加
2. ACを合計3件以上にし、integrationタグ付きACを最低1件含める
3. NFRを合計6件以上にし、integration/data/security を最低1件ずつ含める
4. `spec_as_code.artifacts` を記入
5. `derived_fields.counts` を更新

**plan.md**:
1. `contracts` に最低1つのCTを追加
2. `tests` に各ACをカバーするTSを追加
3. `coverage_policy` を設定
4. `evidence_pack` を設定

**tasks.md**:
1. 各TSに対応するタスクを追加
2. `milestones` にゲートを設定

### 5.5 Phase Gate 承認

各フェーズの完了後、stride-lint を実行して `APPROVAL_PENDING` が表示されたら：

1. APPROVAL.md を開く
2. 該当ゲートのチェックボックスを `[x]` に変更
3. 承認者名と日付を記入
4. ファイルを保存

```markdown
## Gate 1: Basic Design
確認項目：
- [x] basic_design.md の WHO/WHAT/WHY が正しい    ← [x] に変更
- [x] トレーサビリティ（RQ→US→AC→BPMN）が定義されている

承認者: 山田太郎                                  ← 名前を記入
日付:   2025-01-04                                ← 日付を記入
```

### 5.6 検証

```bash
stride lint specs/my_first_feature/ --warn-only
```

**APPROVAL_PENDING が出たら**: 上記 5.5 に戻って承認を行う

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
3. **stride_lint_spec.md** を読んで検証ルールを把握
4. **tecnos_org_constraints.md** を読んで組織制約を確認
5. **agent_docs/testing.md** を読んでテスト実行方法を把握

---

## テストテンプレート活用

### Python テストセットアップ

```bash
# 1. テストディレクトリ作成（SDD準拠）
mkdir -p specs/my_feature/tests/{unit,integration,contract,e2e}

# 2. conftest.py テンプレートをコピー
cp sdd-templates/config/testing/python/conftest.py.template \
   specs/my_feature/tests/conftest.py

# 3. pyproject.toml に設定を追加（マージ）
# sdd-templates/config/testing/pyproject.toml.snippet を参照
```

### テスト実行

```bash
# 単体・統合テスト実行（E2E除外）
python -m pytest specs/my_feature/tests/ --ignore=specs/my_feature/tests/e2e

# カバレッジ付き
python -m pytest specs/my_feature/tests/ --cov=src --cov-report=term-missing

# マーカー別実行
python -m pytest -m "unit"           # 単体テストのみ
python -m pytest -m "integration"    # 統合テストのみ
python -m pytest -m "contract"       # 契約テストのみ
```

### テストパターン参照

- `docs/TEST_PATTERNS.md` - 認証/CRUD/ワークフローのテストパターン集
- `agent_docs/testing.md` - 5言語対応のテスト実行ガイド
- `CHEATSHEET.md` Section 13-14 - Pythonテストクイックリファレンス

---

## Lite Mode

小規模プロジェクト、PoC、単独開発者向けの簡易承認フローです。

### Full Mode vs Lite Mode

| 項目 | Full Mode（標準） | Lite Mode |
|------|------------------|-----------|
| 承認ステージ | 6段階 | 3段階 |
| Gate数 | Gate 1-5 + Final | Gate A/B/C |
| 推奨用途 | 本番プロジェクト | PoC、プロトタイプ |
| ドキュメント量 | フル | 最小限 |

### Lite Mode の Gate 対応

```
Full Mode          →  Lite Mode
Gate 1 + Gate 2    →  Gate A: Design & Flow
Gate 3 + Gate 4    →  Gate B: Spec & Plan
Gate 5 + Final     →  Gate C: Implementation & Verification
```

### Lite Mode の使い方

```bash
# 1. APPROVAL_LITE.md を使用
cp sdd-templates/templates/APPROVAL_LITE.md specs/my_feature/APPROVAL.md

# 2. stride-lint を --lite-mode で実行
stride lint specs/my_feature/ --lite-mode

# または APPROVAL.md 内に "Gate A:" が含まれていれば自動検出
stride lint specs/my_feature/
```

### Full Mode → Lite Mode への移行

既存プロジェクトをLite Modeに移行する場合：

1. `APPROVAL_LITE.md` をコピー
2. Full Mode の承認状況を Lite Mode にマッピング
   - Gate 1 + 2 承認済み → Gate A を承認済みにする
   - Gate 3 + 4 承認済み → Gate B を承認済みにする
   - Gate 5 + Final 承認済み → Gate C を承認済みにする
3. `--lite-mode` フラグで検証

### Lite Mode → Full Mode への移行

PoC/プロトタイプを本番化する場合：

1. `APPROVAL.md`（Full Mode版）をコピー
   ```bash
   cp sdd-templates/templates/APPROVAL.md specs/my_feature/APPROVAL.md
   ```
2. Lite Mode の承認状況を Full Mode に展開
   - Gate A 承認済み → Gate 1, 2 を承認済みにする（承認者・日付を転記）
   - Gate B 承認済み → Gate 3, 4 を承認済みにする
   - Gate C 承認済み → Gate 5, Final を承認済みにする
3. 各 Gate の詳細チェック項目を確認
   - Lite Mode では省略されていた確認項目があるため、追加レビューが必要な場合がある
4. `--lite-mode` フラグなしで検証
   ```bash
   stride lint specs/my_feature/
   ```
5. 必要に応じて追加承認を取得

**注意**: Lite → Full 移行時は、Full Mode の追加要件（Evidence Pack、詳細なトレーサビリティ等）を満たしているか確認してください。

---

## サポート

- テンプレート質問: Arch チームへ
- stride-lint エラー: エラーメッセージで検索 or Arch チームへ
- 移行相談: MIGRATION.md を参照

---

> End of QUICKSTART.md
