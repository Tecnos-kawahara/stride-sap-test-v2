# TypeScript 型安全性設定

## 概要

このディレクトリには、AIによる `any` 型の乱用を防ぐための厳格な TypeScript 設定テンプレートが含まれています。

## ファイル

| ファイル | 説明 |
|---------|------|
| `tsconfig.json` | 厳格モード有効化済みのTypeScriptコンパイラ設定 |
| `eslint.config.mjs` | `any` 型を禁止するESLint設定 (Flat Config形式) |
| `package.json.snippet` | 必要な開発依存関係 |

## セットアップ

### 1. ファイルをプロジェクトルートにコピー

```bash
cp sdd-templates/config/typescript/tsconfig.json .
cp sdd-templates/config/typescript/eslint.config.mjs .
```

### 2. 依存関係をインストール

```bash
npm install -D typescript @types/node eslint @eslint/js typescript-eslint
```

### 3. package.json にスクリプトを追加

```json
{
  "scripts": {
    "typecheck": "tsc --noEmit",
    "lint": "eslint src/**/*.ts",
    "lint:fix": "eslint src/**/*.ts --fix"
  }
}
```

## 重要な設定

### tsconfig.json

| オプション | 値 | 目的 |
|-----------|-----|------|
| `strict` | `true` | 全厳格オプションを有効化 |
| `noImplicitAny` | `true` | 暗黙的any型を禁止 |
| `strictNullChecks` | `true` | null/undefinedの厳格チェック |
| `noUncheckedIndexedAccess` | `true` | インデックスアクセス時にundefinedを考慮 |

### eslint.config.mjs

| ルール | 設定 | 目的 |
|--------|------|------|
| `@typescript-eslint/no-explicit-any` | `error` | 明示的any型を禁止 |
| `@typescript-eslint/no-unsafe-*` | `error` | any型からの安全でない操作を禁止 |
| `@typescript-eslint/explicit-function-return-type` | `error` | 関数の戻り値型を必須化 |

## AIへの指示

Claude Codeや他のAIエージェントがTypeScriptコードを生成する際、以下の規則を遵守させてください：

1. **`any` 型の使用は禁止**
   - エラー回避のために `any` を使用してはならない
   - 代わりに `unknown` を使用し、適切な型ガードで絞り込む

2. **型定義ファイルの作成を必須化**
   - 外部API、データベーススキーマには必ず型定義を作成
   - `types/` ディレクトリに `.d.ts` ファイルを配置

3. **型エラーの解決方法**
   - 型エラーが発生した場合、`as any` でキャストせず、根本原因を解決
   - 複雑な型は `type` または `interface` で分解して定義

## CI/CDゲート

以下のコマンドがすべて成功することをPRマージの必須条件とします：

```bash
npm run typecheck  # tsc --noEmit
npm run lint       # ESLint (any禁止ルール含む)
npm test           # Vitest
```
