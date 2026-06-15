# Conventions (Tecnos SDD v4.4)

このドキュメントはAIエージェントおよび開発者が遵守すべき規約を定義します。
前半はSDD固有ルール、後半は汎用コーディング規約です。

---

## SDD固有ルール

### 1) Source of truth
- ID conventions: `memory/constitution.md#id_conventions`.
- Org constraints and gates: `memory/tecnos_org_constraints.md`.
- Artifact registry: `memory/artifact_registry.md`.

### 2) File naming
- Use snake_case for spec files: `basic_design.md`, `spec.md`, `plan.md`, `tasks.md`.
- Avoid hyphens in spec file names; lint expects snake_case.

### 3) Canonical YAML blocks
- Do not delete or rename canonical YAML sections; `stride-lint` extracts these blocks.
- Edit data first, then update counts to match lint suggestions (COUNTS_SUGGESTION).

### 4) IDs and references
- Use stable IDs for components, libraries, contracts, tests, phases, and groups.
- `tasks.plan_refs` must reference stable IDs only.
- `spec_refs` must reference valid US-* and AC-* IDs.

### 5) Placeholders
- Replace template placeholders (FEAT-XXX, FEATXXX, XXX_feature_name) before gating.

### 6) Test File Location (CRITICAL)
- **正しい場所**: `specs/<feature>/tests/`
- **間違い**: プロジェクトルートの `tests/` や `test/`
- テストファイルは必ず機能ディレクトリ内に格納する
- これにより以下が実現される：
  - 機能単位でのポータビリティ（`specs/<feature>/` をコピーするだけで移行可能）
  - stride-lintのトレーサビリティチェックが正確に動作
  - Evidence Packのパス参照が整合
- `pyproject.toml` の `testpaths` は `["specs/<feature>/tests"]` に設定する

### 7) AI Test Tool Auto-Install (MANDATORY)
- **テスト実行前に依存関係を確認し、不足ツールは自動インストールする**
- ユーザーに確認を求めずに進める（テストツールのインストールは安全な操作）
- 仮想環境（`.venv`）が存在する場合は必ず使用する
- インストール失敗時はエラーを報告し、代替案を提示する
- 詳細: `agent_docs/testing.md` の「AI Agent Pre-Flight Checklist」

#### クイックリファレンス
```bash
# Python: pytest確認＆インストール
python -c "import pytest" 2>/dev/null || pip install pytest pytest-cov httpx

# TypeScript: vitest確認＆インストール
npm list vitest 2>/dev/null || npm install -D vitest @vitest/coverage-v8

# Playwright: E2E用ブラウザ
npx playwright --version 2>/dev/null || { npm install -D @playwright/test && npx playwright install chromium; }
```

---

## 汎用コーディング規約

### 1. 全般規約

#### 1.1 ファイル命名

| カテゴリ | 規約 | 例 |
|---------|------|-----|
| ソースファイル | snake_case (Python), camelCase (TypeScript) | `order_service.py`, `orderService.ts` |
| テストファイル | `test_*.py`, `*.test.ts`, `*.spec.ts` | `test_order_service.py`, `orderService.test.ts` |
| 型定義ファイル | `*.d.ts` または `types/` 配下 | `types/api.d.ts` |
| 設定ファイル | 小文字、ドット区切り | `tsconfig.json`, `eslint.config.mjs` |

#### 1.2 ディレクトリ構造

```
src/
├── domain/        # ドメインモデル、ビジネスロジック
├── api/           # APIエンドポイント
├── repository/    # データアクセス層
├── services/      # アプリケーションサービス
└── types/         # 型定義 (TypeScript)
specs/<feature>/
└── tests/         # テストファイル (specs配下に配置)
```

---

### 2. TypeScript 型安全性規約 (CRITICAL)

> **この規約はTecnos組織における必須要件であり、違反は許容されない。**

#### 2.1 `any` 型の禁止 (INVIOLABLE)

```typescript
// ❌ 禁止: any型の使用
function processData(data: any): any {
  return data.value;
}

// ✅ 正解: 適切な型定義
interface DataPayload {
  value: string;
  timestamp: Date;
}

function processData(data: DataPayload): string {
  return data.value;
}
```

#### 2.2 `unknown` の適切な使用

外部入力やAPI応答など、型が不明な場合は `unknown` を使用し、型ガードで絞り込む。

```typescript
// ✅ 正解: unknownと型ガード
function parseApiResponse(response: unknown): User {
  if (!isUser(response)) {
    throw new TypeError('Invalid user response');
  }
  return response;
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'name' in value
  );
}
```

#### 2.3 戻り値型の明示

すべての関数は明示的な戻り値型を持つこと。

```typescript
// ❌ 禁止: 戻り値型の省略
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// ✅ 正解: 明示的な型
function calculateTotal(items: OrderItem[]): number {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

#### 2.4 型定義ファイルの必須化

以下の場合、必ず型定義ファイル (`types/*.d.ts` または `types/*.ts`) を作成すること：

- 外部APIレスポンス
- データベーススキーマ
- 設定ファイル構造
- ドメインモデル

```
src/types/
├── api/
│   ├── orders.ts      # 注文API型定義
│   └── responses.ts   # 共通レスポンス型
├── domain/
│   ├── order.ts       # 注文ドメインモデル
│   └── user.ts        # ユーザードメインモデル
└── index.ts           # 再エクスポート
```

#### 2.5 型エラーの解決方法

型エラーが発生した場合、以下の順序で解決すること：

1. **根本原因を特定** - エラーメッセージを読み、型の不一致箇所を特定
2. **型定義を修正** - 不正確な型定義があれば修正
3. **型ガードを追加** - ランタイムでの型検証が必要なら型ガードを実装
4. **ジェネリクスを活用** - 再利用可能な型が必要なら汎用化

```typescript
// ❌ 禁止: 型エラーをasで握りつぶす
const data = response as any;

// ❌ 禁止: non-null assertionの乱用
const value = obj!.property!.nested!;

// ✅ 正解: 適切な型ガードとOptional Chaining
const value = obj?.property?.nested ?? defaultValue;
```

---

### 3. Python 型安全性規約

#### 3.1 型ヒントの必須化

Python 3.10+ の型ヒント構文を使用し、すべての関数に型アノテーションを付与。

```python
# ❌ 禁止: 型ヒントなし
def process_order(order_data):
    return order_data.get('id')

# ✅ 正解: 型ヒントあり
from typing import TypedDict

class OrderData(TypedDict):
    id: str
    items: list[OrderItem]

def process_order(order_data: OrderData) -> str:
    return order_data['id']
```

#### 3.2 mypy の設定

`pyproject.toml` に以下の設定を含めること：

```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_any_generics = true
```

---

### 4. テスト規約

#### 4.1 テストファイルの配置

```
specs/<feature>/tests/
├── contract/      # コントラクトテスト
├── integration/   # 統合テスト
└── e2e/          # E2Eテスト
```

> **注意**: ルートの `tests/` ディレクトリではなく、`specs/<feature>/tests/` に配置すること。

#### 4.2 テストカバレッジ要件

| カテゴリ | 最低カバレッジ |
|---------|--------------|
| ライン | 80% |
| ブランチ | 70% |
| 関数 | 90% |

---

### 5. 設定ファイルテンプレート

TypeScriptプロジェクトでは、以下のテンプレートをコピーして使用すること：

```bash
# TypeScript設定のコピー
cp sdd-templates/config/typescript/tsconfig.json .
cp sdd-templates/config/typescript/eslint.config.mjs .
```

---

### 6. CI/CD ゲート要件

PRマージ前に以下のすべてが成功すること：

#### TypeScript
```bash
tsc --noEmit                    # 型チェック
eslint 'src/**/*.ts'            # Lint (any禁止含む)
vitest run                      # テスト
```

#### Python
```bash
mypy src/ --strict              # 型チェック
ruff check src/                 # Lint
pytest specs/                   # テスト
```

---

### 7. AIエージェントへの指示

Claude Codeや他のAIエージェントがコードを生成する際、以下を遵守すること：

1. **型定義ファースト** - 実装前に型定義を作成
2. **any禁止** - エラー回避のために `any` を使用しない
3. **テスト必須** - 実装と同時にテストを作成
4. **エラー解決** - 型エラーは根本原因を解決し、キャストで回避しない
