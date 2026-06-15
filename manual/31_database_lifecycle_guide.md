# 31. データベースライフサイクル管理ガイド

**所要時間**: 約20分

> **関連ガイド**: DB設計の定義方法は [spec.md の書き方 §6.5/§6.6](11_spec_guide.md) を参照。
> 本ガイドは設計後の「管理・維持・検証」を扱います。

---

## このガイドで学ぶこと

1. SSOTモデルの選び方（db-first / orm-driven / declarative）
2. `basic_design.database` の新フィールドの書き方
3. tbls の導入と `.tbls.yml` 標準テンプレート
4. CI 再生成ワークフロー
5. migration 運用ルール（forward-only）
6. 実DBとの差分検出
7. AI/RAG 向け schema.json の活用

---

## 1. SSOTモデルの選び方

### 判断ツリー

| 条件 | ssot_model | design_ssot | deployment_ssot |
|------|-----------|-------------|-----------------|
| Prisma 中心の TypeScript アプリ | `orm-driven` | `prisma/schema.prisma` | `prisma/migrations/` |
| Drizzle 中心の TypeScript アプリ | `orm-driven` | `src/db/schema.ts` | `drizzle/` |
| Atlas等の宣言的スキーマ管理 | `declarative` | `schema.hcl` 等 | `migrations/` |
| 上記以外（ERP連携、Polyglot、DB-first） | `db-first` | （空: migrations/が兼ねる） | `migrations/` |

**原則**: 迷ったら `db-first`。ORM を使っている場合でも、ORM が migration を自動生成する仕組みがないなら `db-first` を選ぶ。

### 設計 SSOT と配備 SSOT の関係

```
[Design SSOT]                    [Deployment SSOT]
  schema.prisma ──prisma migrate──▶ prisma/migrations/
  schema.ts     ──drizzle-kit────▶ drizzle/
  (なし)        ──手書きSQL──────▶ migrations/
  schema.hcl    ──atlas migrate──▶ migrations/
```

**配備 SSOT は常に存在する**。deploy/recover/audit の観点で migration 履歴を外さない。

---

## 2. basic_design.database の書き方

### 最小構成（db-first、AI メタデータなし）

```yaml
database:
  enabled: true
  schema_ref: "specs/my_feature/contracts/database_schema.yaml"
  dialect: "postgresql"
  sor_tables: ["orders"]
  referenced_tables: []
  migration_strategy: "versioned"
  migration_tool: "flyway"
  ssot_model: "db-first"
  design_ssot: ""
  deployment_ssot: "migrations/"
  ai_metadata:
    enabled: false
```

### フル構成（orm-driven + tbls + CI 再生成）

```yaml
database:
  enabled: true
  schema_ref: "specs/my_feature/contracts/database_schema.yaml"
  dialect: "postgresql"
  sor_tables: ["orders", "order_items"]
  referenced_tables: ["customers", "products"]
  migration_strategy: "versioned"
  migration_tool: "prisma"
  ssot_model: "orm-driven"
  design_ssot: "prisma/schema.prisma"
  deployment_ssot: "prisma/migrations/"
  ai_metadata:
    enabled: true
    generator: "tbls"
    config_path: ".tbls.yml"
    outputs:
      - type: "markdown"
        path: "docs/schema/my_feature/"
      - type: "mermaid"
        path: "docs/schema/my_feature/erd.mmd"
      - type: "json"
        path: "docs/schema/my_feature/schema.json"
    ci_regenerate: true
    lint_rules:
      description_coverage_min: 0.95
      migration_forward_only: true
```

---

## 3. tbls の導入

### `.tbls.yml` 標準テンプレート

```yaml
# .tbls.yml — tbls configuration
# https://github.com/k1LoW/tbls

dsn: "postgres://user:pass@localhost:5432/mydb?sslmode=disable"

docPath: docs/schema/<feature>  # feature名で分離（例: docs/schema/my_feature）

er:
  format: mermaid
  distance: 2

lint:
  requireColumnComment:
    enabled: true
    exclude: []
  requireTableComment:
    enabled: true
    exclude: []

comments:
  - table: "*"
    columnComments:
      created_at: "レコード作成日時"
      updated_at: "レコード更新日時"
      created_by: "作成者（監査用）"
      updated_by: "更新者（監査用）"
```

### 基本コマンド

| コマンド | 用途 |
|---------|------|
| `tbls doc` | Markdown ドキュメント + schema.json を `docPath` に生成 |
| `tbls out -t mermaid -o docs/schema/<feature>/erd.mmd` | Mermaid ERD を生成 |
| `tbls out -t json -o docs/schema/<feature>/schema.json` | JSON スキーマを生成 |
| `tbls lint` | コメント必須等のルールを検証 |
| `tbls coverage` | 説明網羅率を計測 |
| `tbls diff` | 直前の生成物との差分を検出 |

---

## 4. CI 再生成ワークフロー

### 2段階ワークフロー: PR 検証 + マージ後コミット

schema docs の生成は**2段階**で運用する:
- **PR 時**: 生成してdiffを表示（レビュー用）。コミットはしない
- **マージ後**: 生成してコミット（正本の更新）

```yaml
# .github/workflows/schema-docs-check.yml（PR 時: 差分検証）
name: Schema Docs Check
on:
  pull_request:
    paths:
      - 'migrations/**'
      - 'prisma/schema.prisma'
      - 'src/db/schema.ts'

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup tbls
        run: |
          curl -sL https://github.com/k1LoW/tbls/releases/latest/download/tbls_linux_amd64.tar.gz | tar xz
          sudo mv tbls /usr/local/bin/
      - name: Start DB & apply migrations
        run: |
          docker compose up -d db
          # migration_tool に応じた適用コマンド
      - name: Generate and check diff
        run: |
          SCHEMA_DOCS="docs/schema/${{ env.FEATURE_NAME }}"
          tbls doc --force
          tbls out -t mermaid -o "$SCHEMA_DOCS/erd.mmd"
          tbls out -t json -o "$SCHEMA_DOCS/schema.json"
          if ! git diff --quiet "$SCHEMA_DOCS/"; then
            echo "::warning::Schema docs are outdated. Diff:"
            git diff "$SCHEMA_DOCS/"
          fi
```

```yaml
# .github/workflows/schema-docs-update.yml（マージ後: 正本更新）
name: Schema Docs Update
on:
  push:
    branches: [main]
    paths:
      - 'migrations/**'
      - 'prisma/schema.prisma'
      - 'src/db/schema.ts'

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup tbls
        run: |
          curl -sL https://github.com/k1LoW/tbls/releases/latest/download/tbls_linux_amd64.tar.gz | tar xz
          sudo mv tbls /usr/local/bin/
      - name: Start DB & apply migrations
        run: |
          docker compose up -d db
          # migration_tool に応じた適用コマンド
      - name: Generate docs
        run: |
          SCHEMA_DOCS="docs/schema/${{ env.FEATURE_NAME }}"
          tbls doc --force
          tbls out -t mermaid -o "$SCHEMA_DOCS/erd.mmd"
          tbls out -t json -o "$SCHEMA_DOCS/schema.json"
      - name: Commit if changed
        run: |
          SCHEMA_DOCS="docs/schema/${{ env.FEATURE_NAME }}"
          git diff --quiet "$SCHEMA_DOCS/" || \
            (git add "$SCHEMA_DOCS/" && git commit -m "chore: regenerate schema docs" && git push)
```

### 生成物の扱い

- `docs/schema/<feature>/` 配下は**手編集禁止**（CI 再生成物として扱う）
- **PR 時**: 生成物の diff を確認し、意図しないスキーマ変更を検出
- **マージ後**: 正本を自動更新（ドリフト防止）
- `.gitignore` には入れない（レビュー可能にするため）

---

## 5. migration 運用ルール

### forward-only 原則

1. **適用済み migration は書き換えない** — 常に新しい migration を追加する
2. **migration ファイル名は時系列で一意にする** — Flyway: `V001__`, Prisma: 自動タイムスタンプ
3. **本番適用前に CI で再現テスト** — `docker compose up → migrate → tbls lint` のパイプライン

### STRIDE での運用

- `database_schema_gate_check.rules.migration_forward_only: true` を宣言
- CI で `deployment_ssot` のパスに対して **既存ファイルの改変** を検出する
- `git diff --name-only` は新規追加と改変を区別できないため、`git diff --diff-filter=M` を使う
- パスは `basic_design.database.deployment_ssot` の値を使う（`migrations/`, `prisma/migrations/`, `drizzle/` 等）

```bash
# deployment_ssot のパスを変数化（プロジェクトに合わせて設定）
DEPLOY_SSOT="prisma/migrations/"  # or "migrations/", "drizzle/", etc.

# 既存 migration ファイルの改変のみを検出（新規追加は正常なので通す）
MODIFIED=$(git diff --diff-filter=M --name-only HEAD~1 -- "$DEPLOY_SSOT")
if [ -n "$MODIFIED" ]; then
  echo "ERROR: Existing migration files were modified (forward-only violation):"
  echo "$MODIFIED"
  exit 1
fi
```

---

## 6. 実DBとの差分検出

### tbls diff

```bash
# 前回の生成物と現在の DB を比較
tbls diff
```

出力が空なら一致。差分があれば、migration の適用漏れか、手動 DDL 変更の可能性。

### 定期チェック（推奨）

- 本番 DB に対して週次で `tbls diff` を実行
- 差分があれば Slack/Teams に通知
- 差分の原因を特定し、migration に反映するか、手動変更を取り消す

---

## 7. AI/RAG 向け schema.json の活用

### schema.json の用途

- **AI Agent**: DB 構造を理解してクエリを生成する際の入力
- **RAG**: スキーマ情報をベクトル DB に格納し、自然言語での検索を可能にする
- **コードレビュー**: PR の DB 変更を schema.json の diff で機械的に検出

### 生成方法

1. **第一候補**: `tbls doc` の自動出力（`docPath` に `schema.json` が同時生成される）
2. **明示出力**: `tbls out -t json -o docs/schema/<feature>/schema.json`

### STRIDE との統合

`spec.md` の `spec_as_code.artifacts` に登録:

```yaml
spec_as_code:
  artifacts:
    - type: "database_schema"
      path: "specs/my_feature/contracts/database_schema.yaml"
      schema_version: "1.0"
      status: "approved"
    - type: "schema_json"           # v4.8.0: AI向け生成物
      path: "docs/schema/my_feature/schema.json"
      schema_version: "1.0"
      status: "generated"           # generated = 自動生成物（ai_metadata有効時）
```

---

## チェックリスト: DB ライフサイクル管理の導入

- [ ] `basic_design.database.ssot_model` を決定した
- [ ] `design_ssot` / `deployment_ssot` のパスを記入した
- [ ] `database_schema.yaml` の全テーブル・全カラムに description を記入した
- [ ] `database_schema_gate_check` で `all_tables_have_description: true` を設定した
- [ ] `stride lint` で `DATABASE_SCHEMA_MISSING_DESCRIPTION` が 0 件
- [ ] tbls を導入した場合: `.tbls.yml` を作成し `tbls lint` が PASS
- [ ] CI 再生成ワークフローを設定した場合: `docs/schema/<feature>/` が自動更新される
- [ ] migration の forward-only ルールをチームに共有した
