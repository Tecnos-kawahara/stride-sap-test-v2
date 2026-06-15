# 23. Turborepo Monorepo リファレンス

**所要時間**: 約20分

---

## 5分クイックリファレンス（PM向け）

**Monorepo とは**: 複数のサービス・ライブラリを1つのリポジトリで管理する手法です。

**なぜ Monorepo か**:
- AI 開発では、仕様・契約・実装・テストを一元管理するメリットが大きい
- コード共有・型共有が容易で、契約の整合性を保ちやすい
- CI/CD で差分ビルド（変更パッケージのみ実行）により効率化

**Scale Levels（段階的導入）**:

| Scale | 対象 | CI 実行時間 |
|-------|------|------------|
| **starter** | 初回導入・小規模 | 1-3分 |
| **standard** | 複数サービス | 3-5分（差分実行） |
| **enterprise** | 大規模・本番 | 3-5分（リモートキャッシュ） |

---

## 1. Turborepo とは

### 1.1 基本概念

**Turborepo** は、JavaScript/TypeScript のモノレポ向けビルドシステムです。

```
┌─────────────────────────────────────────────────────────────────┐
│  Turborepo の役割                                                │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │ packages/ │   │  libs/   │   │ services/│                    │
│  │  shared   │   │  domain  │   │   api    │                    │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                    │
│       │              │              │                            │
│       └──────────────┼──────────────┘                            │
│                      │                                           │
│              ┌───────▼───────┐                                   │
│              │   Turborepo   │   ← タスク実行を最適化            │
│              │ (turbo.json)  │   ← キャッシュで重複排除          │
│              └───────┬───────┘   ← 依存順序を自動解決            │
│                      │                                           │
│       ┌──────────────┼──────────────┐                            │
│       │              │              │                            │
│   lint → typecheck → test → build                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 SDD における Monorepo のメリット

| メリット | 説明 |
|---------|------|
| **契約の一元管理** | `contracts/` をモノレポ内で共有し、ドリフトを検出可能 |
| **型の共有** | TypeScript の型定義を `packages/` で共有、不整合を防止 |
| **差分実行** | 変更パッケージのみ lint/test/build を実行（CI 高速化） |
| **Evidence Pack 統合** | 全パッケージの coverage/test-results を一括収集 |
| **仕様⇔実装の近接** | `specs/` と `src/` が同一リポジトリ、Spec Drift を CI で検出 |

---

## 2. Scale Levels

### 2.1 概要

SDD では、プロジェクトの規模に応じて **3段階の Scale Level** を用意しています。

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  starter ──────→ standard ──────→ enterprise                     │
│                                                                  │
│  build + test    + lint          + リモートキャッシュ            │
│  簡易 CI         + typecheck     + fetch-depth: 0                │
│                  + test:coverage + Evidence Pack 90日            │
│                  + test:contract + Evidence Metrics 収集          │
│                  + spec:drift    + Full Build 検証               │
│                  + 差分 CI                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Starter

**対象**: SDD 初回導入、小規模プロジェクト、PoC

```bash
stride init my_feature                   # デフォルトで Starter
```

**配置ファイル**:

| ファイル | 配置先 |
|---------|--------|
| `turbo.starter.json` → `turbo.json` | プロジェクトルート |
| `tsconfig.base.json` | プロジェクトルート |
| `ci-starter.yml` → `.github/workflows/ci.yml` | CI |

**turbo.json タスク**:

```json
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"],
      "cache": true
    },
    "test": {
      "dependsOn": [],
      "outputs": [],
      "cache": true
    }
  }
}
```

### 2.3 Standard

**対象**: 複数サービスの実プロジェクト

```bash
stride init my_feature --scale standard
```

**追加ファイル**:

| ファイル | 配置先 |
|---------|--------|
| `turbo.standard.json` → `turbo.json` | プロジェクトルート |
| `vitest.workspace.ts` | プロジェクトルート |
| `ci-standard.yml` → `.github/workflows/ci.yml` | CI |

**turbo.json タスク（Standard 以上）**:

| タスク | 目的 | SDD 関連 |
|--------|------|---------|
| `lint` | ESLint 実行 | コード品質 |
| `typecheck` | TypeScript 型チェック | 型安全性 |
| `test` | 単体テスト | AC Coverage |
| `test:coverage` | カバレッジレポート生成 | Evidence Pack |
| `test:contract` | 契約テスト | CT Coverage |
| `spec:drift` | 仕様⇔実装 乖離検出 | Living Spec Drift (v4.2) |
| `build` | TypeScript コンパイル | 成果物生成 |

### 2.4 Enterprise

**対象**: 大規模本番プロジェクト、リモートキャッシュ活用

```bash
stride init my_feature --scale enterprise
```

**Standard との差分（CI 設定のみ）**:

| 機能 | Standard | Enterprise |
|------|----------|------------|
| キャッシュ | ローカル (.turbo/) | **リモート** (Vercel/カスタム) |
| fetch-depth | 2 | **0** (完全履歴) |
| Evidence Pack 保持 | 30日 | **90日** |
| Evidence Metrics | — | **自動収集** |
| Full Build 検証 | — | **main push 時** |

**リモートキャッシュ設定**:

```bash
# Vercel リモートキャッシュ
npx turbo login
npx turbo link

# または GitHub Secrets に設定
# TURBO_TOKEN: Vercel Access Token
# TURBO_TEAM: Vercel Team Slug
```

---

## 3. CI/CD テンプレート

### 3.1 Starter CI

最小構成。build + test + stride-lint のみ。

```yaml
jobs:
  quality:
    steps:
      - run: npm ci
      - run: npx turbo run build
      - run: npx turbo run test
      - run: sdd-templates/bin/stride lint --all --warn-only
```

### 3.2 Standard CI

差分実行 + Evidence Pack 収集。

```yaml
jobs:
  quality:
    steps:
      - run: npm ci
      # 差分実行（変更パッケージのみ）
      - run: npx turbo run lint --filter=...[HEAD~1]
      - run: npx turbo run typecheck --filter=...[HEAD~1]
      - run: npx turbo run test --filter=...[HEAD~1]
      # Spec Drift Detection（v4.2）
      - run: npx turbo run spec:drift || python3 sdd-templates/tools/spec_drift_detector.py . --json
        continue-on-error: true
      - run: sdd-templates/bin/stride lint --all --warn-only

  coverage:  # main/develop push のみ
    steps:
      - run: npx turbo run test:coverage
      - run: npx turbo run test:contract
      - uses: actions/upload-artifact@v4
        with:
          name: evidence-pack-${{ github.sha }}
          retention-days: 30
```

### 3.3 Enterprise CI

リモートキャッシュ + Evidence Metrics + Full Build。

```yaml
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ secrets.TURBO_TEAM }}

jobs:
  quality:     # ← Standard と同じ + リモートキャッシュ
  coverage:    # ← Standard + Evidence Metrics
    steps:
      - run: npx turbo run test:coverage
      - run: npx turbo run test:contract
      # Evidence Metrics 収集（v4.2）
      - run: python3 sdd-templates/tools/evidence_metrics_collector.py . --json > evidence-metrics.json
      - uses: actions/upload-artifact@v4
        with:
          retention-days: 90  # Enterprise は 90日保持
  build:       # ← main push のみ、全パッケージビルド
    if: github.ref == 'refs/heads/main'
    steps:
      - run: npx turbo run build
```

---

## 4. SDD 固有タスクの詳細

### 4.1 `spec:drift` — Living Spec Drift Detection (v4.2)

`contracts/` の OpenAPI YAML と `src/` のルート実装を比較し、乖離を検出します。

```bash
# Turbo 経由（推奨）
npx turbo run spec:drift

# 直接実行
python3 sdd-templates/tools/spec_drift_detector.py .
python3 sdd-templates/tools/spec_drift_detector.py . --json     # 機械可読
python3 sdd-templates/tools/spec_drift_detector.py . --verbose  # 詳細
```

**検出種別**:

| 種別 | 重大度 | 意味 |
|------|--------|------|
| `endpoint_not_implemented` | critical | 契約にあるが実装にない |
| `contract_outdated` | high | 実装にあるが契約にない |
| `schema_mismatch` | medium | レスポンスフィールドの不一致 |
| `parameter_missing` | medium | 必須パラメータの欠落 |

**CI 統合**:
- `continue-on-error: true` — ドリフトは警告であり、CI をブロックしない
- critical ドリフトが見つかった場合、チームが判断して対応

### 4.2 `test:coverage` — Evidence Pack 用カバレッジ

```bash
npx turbo run test:coverage
```

- 出力: `coverage/` ディレクトリ（Istanbul 形式）
- CI で `actions/upload-artifact` によりEvidence Pack に含められる

### 4.3 `test:contract` — 契約テスト

```bash
npx turbo run test:contract
```

- `contracts/` と `tests/` を入力として契約テストを実行
- CT Coverage 100% を目標

### 4.4 Evidence Metrics Collection (Enterprise, v4.2)

```bash
python3 sdd-templates/tools/evidence_metrics_collector.py . --json
```

**収集メトリクス**:

| メトリクス | ソース | 説明 |
|-----------|--------|------|
| カバレッジ率 | `coverage/coverage-summary.json` | Istanbul 形式のカバレッジ |
| テスト結果 | JUnit XML / JSON | pass/fail/skip + 実行時間 |
| キャッシュヒット率 | `.turbo/` | Turbo キャッシュ効率 |
| Gate リードタイム | `APPROVAL.md` | 承認までの所要時間 |

---

## 5. ディレクトリ構成

### 5.1 推奨レイアウト

```
project-root/
├── turbo.json                 ← Turborepo 設定（Scale 別）
├── tsconfig.base.json         ← 共有 TypeScript 設定
├── vitest.workspace.ts        ← テストワークスペース（standard+）
├── package.json               ← workspaces 定義
│
├── packages/                  ← 共有パッケージ
│   ├── shared-types/          #   型定義
│   └── shared-utils/          #   ユーティリティ
│
├── libs/                      ← ライブラリパッケージ
│   └── domain-logic/          #   ドメインロジック
│
├── services/                  ← サービスパッケージ
│   ├── api-gateway/           #   API ゲートウェイ
│   └── order-service/         #   注文サービス
│
├── apps/                      ← アプリケーション
│   └── web-portal/            #   Web ポータル
│
├── specs/                     ← SDD 仕様（Feature 単位）
│   └── order_feature/
│       ├── basic_design.md
│       ├── spec.md
│       ├── contracts/
│       │   └── openapi.yaml
│       └── ...
│
├── sdd-templates/             ← SDD テンプレートパック
│
└── .github/workflows/
    └── ci.yml                 ← CI（Scale 別テンプレート）
```

### 5.2 package.json workspaces 設定

```json
{
  "workspaces": [
    "packages/*",
    "libs/*",
    "services/*",
    "apps/*"
  ]
}
```

---

## 6. Scale のアップグレード

### 6.1 Starter → Standard

```bash
# 1. turbo.json を Standard に置換
cp sdd-templates/config/monorepo/turbo.standard.json turbo.json

# 2. vitest.workspace.ts を追加
cp sdd-templates/config/monorepo/vitest.workspace.ts .

# 3. CI を Standard に置換
cp sdd-templates/config/monorepo/github-actions/ci-standard.yml .github/workflows/ci.yml
```

**または再実行（既存ファイルはスキップ）**:
```bash
stride init <feature> --scale standard
```

### 6.2 Standard → Enterprise

```bash
# 1. turbo.json を Enterprise に置換
cp sdd-templates/config/monorepo/turbo.enterprise.json turbo.json

# 2. CI を Enterprise に置換
cp sdd-templates/config/monorepo/github-actions/ci-enterprise.yml .github/workflows/ci.yml

# 3. リモートキャッシュを設定
npx turbo login && npx turbo link
# または GitHub Secrets に TURBO_TOKEN, TURBO_TEAM を設定
```

---

## 7. トラブルシューティング

### 7.1 turbo.json が Invalid JSON

**症状**: `python3 -c "import json; json.load(open('turbo.json'))"` が失敗

**原因**: `//` コメントが含まれている（Turborepo は JSONC 対応だが他ツールは非対応）

**解決**: `//` コメントを削除し、メモが必要な場合は `"// NOTE"` キーパターンを使用

```json
{
  "// NOTE": "Enterprise の差分は CI 設定のみ。turbo.json タスクは Standard と同一。",
  "tasks": { ... }
}
```

### 7.2 差分実行で変更が検出されない

**症状**: `--filter=...[HEAD~1]` で何も実行されない

**原因**: `fetch-depth` が浅すぎる、または `inputs` 設定が不正確

**解決**:
```yaml
# CI で十分な履歴を取得
- uses: actions/checkout@v4
  with:
    fetch-depth: 2   # Standard: 最低2
    # fetch-depth: 0  # Enterprise: 完全履歴（推奨）
```

### 7.3 spec:drift が誤検出する

**症状**: 実装済みエンドポイントが `endpoint_not_implemented` と表示される

**原因**: ルートパターンが対応フレームワーク外、またはパスの正規化不一致

**解決**:
- Express の `:param` は OpenAPI の `{param}` に正規化されるか確認
- 対応フレームワーク: Express, Fastify, NestJS, Flask/FastAPI, Go
- `--verbose` で詳細を確認: `python3 sdd-templates/tools/spec_drift_detector.py . --verbose`

### 7.4 リモートキャッシュが効かない

**症状**: Enterprise CI でキャッシュヒットがゼロ

**原因**: `TURBO_TOKEN` / `TURBO_TEAM` が未設定、またはチーム不一致

**解決**:
```bash
# ローカルで接続確認
npx turbo login
npx turbo link

# GitHub Secrets を確認
# Settings → Secrets and variables → Actions
# TURBO_TOKEN: Vercel Access Token
# TURBO_TEAM: Vercel Team Slug（slug であり表示名ではない）
```

---

## 8. 設定ファイル一覧

| ファイル | Scale | 説明 |
|---------|-------|------|
| `turbo.starter.json` | starter | build + test のみ |
| `turbo.standard.json` | standard | 全 SDD タスク（lint, typecheck, test, coverage, contract, spec:drift, build） |
| `turbo.enterprise.json` | enterprise | Standard と同一（差分は CI 環境変数のみ） |
| `tsconfig.base.json` | 全 Scale | 共有 TypeScript 設定 |
| `vitest.workspace.ts` | standard+ | Vitest テストワークスペース |
| `package.json.snippet` | 全 Scale | workspaces 定義のスニペット |
| `ci-starter.yml` | starter | 簡易 CI |
| `ci-standard.yml` | standard | 差分実行 + Evidence Pack (30日) |
| `ci-enterprise.yml` | enterprise | リモートキャッシュ + Evidence Pack (90日) + Metrics |

**テンプレート配置先**: `sdd-templates/config/monorepo/`

---

## 関連ドキュメント

- [SDD_MANIFESTO.md](../SDD_MANIFESTO.md) — CI/CD Requirements (Monorepo) セクション
- [agent_docs/commands.md](../agent_docs/commands.md) — STRIDE_INIT (--scale) / SPEC_DRIFT_CHECK / EVIDENCE_METRICS
- [config/monorepo/README.md](../sdd-templates/config/monorepo/README.md) — 設定ファイル詳細

---

> SDD Templates Manual - 23. Turborepo Monorepo Reference (v4.5)
