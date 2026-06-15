# 21. Living Spec Drift Detection & Evidence Metrics ガイド

> **対象**: contracts/ と src/ の整合性を自動管理したい開発者・PM
> **所要時間**: 約15分

---

## 5分クイックリファレンス（PM向け）

**v4.2 で何が変わったか**:
- `contracts/`（OpenAPI仕様）と `src/`（実装）の**乖離を自動検出**
- Evidence Pack に**定量メトリクス**（カバレッジ推移、テスト時間、キャッシュ率、Gate リードタイム）を追加
- CI で自動実行し、ドリフトがあれば PR をブロック可能

**PM が確認すべきこと**:
1. Spec Drift の `critical` が 0 であること（契約に書いてあるのに未実装は最も危険）
2. Evidence Metrics の coverage が閾値以上であること
3. Gate リードタイムが健全か（長すぎないか）

---

## Part 1: Living Spec Drift Detection

### 1.1 概要

**SSoT（Single Source of Truth）原則の自動検証**です。

```
contracts/api.yaml    ← 仕様の正本
        ↓ spec:drift
src/routes/api.ts     ← 実装
        ↓
乖離（drift）を4種別で検出
```

SDD では仕様が正本であり、コードは仕様に従います。
しかし実装が進むと、仕様と実装の間に乖離が生じることがあります。
`spec_drift_detector` はこの乖離を自動検出し、SSoT 原則の違反を早期に発見します。

### 1.2 ドリフト検出の4種別

| Type | Severity | 説明 | 例 |
|------|----------|------|-----|
| `endpoint_not_implemented` | **critical** | 契約にあるが src/ にない | `POST /orders` が仕様にあるのにルート未実装 |
| `contract_outdated` | **high** | src/ にあるが契約にない | 実装に `DELETE /orders/:id` があるのに仕様に未記載 |
| `schema_mismatch` | medium | レスポンスフィールドが型と不一致 | 仕様の `totalPrice` が TypeScript 型に不在 |
| `parameter_missing` | medium | 必須パラメータがハンドラで未使用 | 仕様で `required: true` の `orderId` が `req.params` に未参照 |

### 1.3 仕組み

1. **Contract Parsing**: `contracts/` 配下の OpenAPI YAML を解析し、エンドポイント一覧を抽出
2. **Source Scanning**: `src/` 配下のルート定義（Express, Fastify, NestJS, Flask, Go 等）をスキャン
3. **Drift Comparison**: 契約のエンドポイントと実装ルートを突合し、乖離を検出

#### 対応フレームワーク

| Framework | パターン例 |
|-----------|-----------|
| Express.js | `app.get('/path', ...)`, `router.post('/path', ...)` |
| Fastify | `fastify.get('/path', ...)` |
| NestJS | `@Get('/path')`, `@Post('/path')` |
| Flask / FastAPI | `@app.get('/path')`, `@router.post('/path')` |
| Go (Echo/Gin) | `.GET("/path", ...)`, `.POST("/path", ...)` |

### 1.4 使い方

```bash
# 基本実行
python3 sdd-templates/tools/spec_drift_detector.py <project_root>

# JSON出力（CI向け）
python3 sdd-templates/tools/spec_drift_detector.py <project_root> --json

# 詳細出力
python3 sdd-templates/tools/spec_drift_detector.py <project_root> --verbose

# stride CLI経由
stride drift-check <project_root>
```

### 1.5 出力例

```
=== Spec Drift Detection ===
Project: /path/to/project
Contracts: 3 endpoints (from contracts/api.yaml)
Source routes: 5 routes (from src/)

Drifts found: 2

1 - [critical] endpoint_not_implemented
    POST /orders (contracts/api.yaml)
    → No matching route in src/

2 - [high] contract_outdated
    DELETE /orders/{id} (src/routes/orders.ts)
    → No matching endpoint in contracts/

Summary: 1 critical, 1 high, 0 medium
```

### 1.6 CI 統合

`standard` / `enterprise` の CI テンプレートに `spec:drift` ステップが自動追加されます。

```yaml
# turbo.standard.json / turbo.enterprise.json に含まれるタスク
"spec:drift": {
  "dependsOn": ["^build"],
  "outputs": []
}
```

CI での実行:
```yaml
# ci-standard.yml / ci-enterprise.yml
- name: Spec Drift Check
  run: npx turbo run spec:drift
```

### 1.7 セルフテスト

```bash
python3 sdd-templates/tools/spec_drift_detector.py --test
# 6 tests pass:
#   Test 1: non-existent path handling
#   Test 2: empty project (no drift)
#   Test 3: endpoint_not_implemented detection
#   Test 4: contract_outdated detection
#   Test 5: schema_mismatch detection
#   Test 6: parameter_missing detection
```

---

## Part 2: Evidence Metrics Collection

### 2.1 概要

Evidence Pack を**ポイントインタイムのスナップショット**から**推移追跡可能な定量基盤**に拡張します。

```
[v4.2前] Evidence Pack = coverage + test-results（スナップショット）
[v4.2後] Evidence Pack = coverage推移 + テスト実行時間 + キャッシュヒット率 + Gate リードタイム
```

### 2.2 計測対象

| メトリクス | 取得元 | 用途 |
|-----------|--------|------|
| **カバレッジ推移** | `coverage/coverage-summary.json` | 品質トレンドの可視化 |
| **テスト実行結果** | JUnit XML / Vitest JSON / Jest JSON | テスト通過率・失敗検出 |
| **テスト実行時間** | 同上の `time` フィールド | パフォーマンス劣化の早期検出 |
| **キャッシュヒット率** | `.turbo/` キャッシュエントリ | CI 効率の定量化 |
| **Gate 通過リードタイム** | `APPROVAL.md` 日付タイムスタンプ | プロセス効率の計測 |

### 2.3 カバレッジ収集の詳細

`coverage-summary.json`（Istanbul/NYC 形式）を自動検出します。

**検索パス**:
- `<project_root>/coverage/coverage-summary.json`
- `<project_root>/packages/*/coverage/coverage-summary.json`（Monorepo）

**収集フィールド**:
- `total_pct`: 全体カバレッジ率
- `line_pct`: 行カバレッジ
- `branch_pct`: ブランチカバレッジ
- `function_pct`: 関数カバレッジ

### 2.4 テスト結果収集の詳細

以下のフォーマットに対応:

| フォーマット | ファイルパターン | 対応 |
|-------------|-----------------|------|
| Vitest JSON | `test-results.json` | `numTotalTests`, `numPassedTests` 等 |
| Jest JSON | `test-results.json` (Jest形式) | `testResults[].numPassingTests` 等 |
| JUnit XML | `junit.xml`, `test-results.xml` | `tests`, `failures`, `errors` 属性 |

### 2.5 キャッシュヒット率

Turborepo のキャッシュエントリ数から推定します。

**検索パス**:
- `.turbo/` ディレクトリ
- `node_modules/.cache/turbo/`

### 2.6 Gate リードタイム

`APPROVAL.md` のタイムスタンプから、最初の Gate 承認から最後の Gate 承認までの経過時間を算出します。

```
Gate 1 承認: 2026-02-01
Gate 5 承認: 2026-02-10
→ リードタイム: 216.0 時間（9日）
```

### 2.7 使い方

```bash
# 全メトリクス収集
python3 sdd-templates/tools/evidence_metrics_collector.py <project_root>

# JSON出力（CI / Evidence Pack 連携用）
python3 sdd-templates/tools/evidence_metrics_collector.py <project_root> --json
```

### 2.8 出力例

```
=== Evidence Metrics ===
Project: /path/to/project
Timestamp: 2026-02-14T10:30:00

Coverage:
  Total: 87.3%  Line: 89.1%  Branch: 78.5%  Function: 91.2%
  Source: coverage/coverage-summary.json

Tests:
  Total: 47  Passed: 47  Failed: 0  Skipped: 2
  Execution time: 12.3s
  Source: test-results.json

Cache:
  Hit rate: 85.0%  (17/20 tasks cached)

Gate Lead Time:
  Total: 168.0h (Gate 1 → Gate 5)
```

### 2.9 Evidence Pack テンプレートとの連携

`evidence_pack_template.md` に `metrics_trend` YAML セクションが追加されています：

```yaml
metrics_trend:
  coverage_history:
    - date: "YYYY-MM-DD"
      total_pct: 0
  test_execution_time_history:
    - date: "YYYY-MM-DD"
      duration_sec: 0
  cache_hit_rate_history:
    - date: "YYYY-MM-DD"
      rate_pct: 0
  gate_lead_time_hours: 0
```

### 2.10 CI 統合（Enterprise Only）

メトリクス収集は `ci-enterprise.yml` にのみ含まれます（standard / starter には含まれません）。

```yaml
# ci-enterprise.yml (抜粋)
- name: Collect Evidence Metrics
  run: python3 sdd-templates/tools/evidence_metrics_collector.py . --json > evidence-metrics.json

- name: Upload Metrics Artifact
  uses: actions/upload-artifact@v4
  with:
    name: evidence-metrics
    path: evidence-metrics.json
    retention-days: 90
```

### 2.11 セルフテスト

```bash
python3 sdd-templates/tools/evidence_metrics_collector.py --test
# 6 tests pass:
#   Test 1: non-existent path handling
#   Test 2: coverage collection
#   Test 3: test results collection (Vitest/Jest/JUnit)
#   Test 4: cache stats collection
#   Test 5: gate lead time calculation
#   Test 6: full metrics aggregation
```

---

## codegen_config.yaml

v4.2 では、OpenAPI 契約から TypeScript 型を自動生成するための設定テンプレートも提供されます。

```yaml
# sdd-templates/templates/contracts/codegen_config.yaml
generator: openapi-typescript
input: contracts/*.yaml
output: src/types/generated/
options:
  immutable: true
  export_type: named
```

これにより、contracts/ の変更が即座に型定義に反映され、ドリフト発生を予防できます。

---

## 関連ドキュメント

- [Evidence Pack ガイド](14_evidence_pack_guide.md) — Evidence Pack の基本
- [Coverage Policy](19_coverage_policy.md) — Tier による品質要求
- [PR Readiness ガイド](22_pr_readiness_guide.md) — v4.3 の統合品質ゲート
- [Turborepo Monorepo ガイド](23_turborepo_monorepo.md) — CI/CD 統合
