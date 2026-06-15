# 22. PR Readiness Checker ガイド

> **対象**: PR 作成前の品質チェックを自動化したい開発者・PM
> **所要時間**: 約10分

---

## 5分クイックリファレンス（PM向け）

**v5.1.0 での追加**:
- `--mutation` で Check 8（ミューテーションテスト）を追加。`cosmic-ray` opt-in、閾値は `.env.local` の `MUTATION_THRESHOLD`（デフォルト 80%）

**v4.3 で何が変わったか**:
- 既存の品質チェック（stride-lint, spec:drift, coverage 等）を**8チェック統合**で一括判定
- `PR_READY` / `NOT_READY` の明確な合否判定
- AI が「完了」と報告しても品質が不十分なケースを**機械的にブロック**

**PM が確認すべきこと**:
- PR が `PR_READY` 判定を受けているか
- `NOT_READY` の場合、どのチェックが FAIL しているか

---

## 1. 概要

### 1.1 なぜ PR Readiness Checker が必要か

v4.2 までに個別の品質チェックツールが揃いました：

| ツール | チェック内容 |
|--------|-----------|
| stride-lint | 仕様書の構造・必須フィールド |
| spec_drift_detector | 契約と実装の乖離 |
| evidence_metrics_collector | カバレッジ・テスト結果 |

しかし、これらを**個別に実行**する運用では見落としが発生します。
PR Readiness Checker は、これらを**1コマンドで統合実行**し、PR 作成可否を判定します。

### 1.2 判定フロー

```
stride pr-check <project_root>
        │
        ├── [1] stride-lint       → PASS/FAIL/WARN
        ├── [2] spec:drift         → PASS/FAIL/WARN
        ├── [3] tests              → PASS/FAIL/WARN
        ├── [4] coverage           → PASS/FAIL/WARN
        ├── [5] walkthrough        → PASS/FAIL/WARN
        ├── [6] evidence_pack      → PASS/FAIL/WARN
        ├── [7] TODO/FIXME         → PASS/WARN (--strict で FAIL)
        └── [8] mutation           → PASS/FAIL/WARN (--mutation で有効化)
                │
                ▼
        FAIL が 1 つでもあれば → NOT_READY (exit 1)
        全て PASS/WARN       → PR_READY  (exit 0)
```

---

## 2. 8つのチェック詳細

### Check 1: stride-lint

**方法**: stride_lint モジュールをインポートして `lint_feature()` を実行

| 判定 | 条件 |
|------|------|
| PASS | エラー 0 件 |
| FAIL | エラー 1 件以上（`APPROVAL_PENDING` は除外） |
| WARN | モジュール未インストール / specs/ なし |

> `APPROVAL_PENDING` は意図的に除外されます。承認待ちは「品質問題」ではなく「プロセス状態」であるためです。

### Check 2: spec:drift

**方法**: spec_drift_detector モジュールをインポートして `detect_drift()` を実行

| 判定 | 条件 |
|------|------|
| PASS | ドリフト 0 件 |
| FAIL | critical ドリフト 1 件以上 |
| WARN | high ドリフトのみ（critical なし） |

### Check 3: tests

**方法**: evidence_metrics_collector の `collect_test_results()` を実行

| 判定 | 条件 |
|------|------|
| PASS | 全テスト通過（failed = 0） |
| FAIL | 1 件以上の失敗 |
| WARN | テスト結果ファイルが見つからない |

### Check 4: coverage

**方法**: evidence_metrics_collector の `collect_coverage()` を実行し、`coverage_tier` に基づく閾値と比較

**閾値の自動判定**:

| coverage_tier | 閾値 |
|---------------|------|
| critical | 90% |
| standard | 80% |
| experimental | 60% |

`coverage_tier` は `basic_design.md` の Canonical YAML（`basic_design:` セクション）から自動読み取りされます。

| 判定 | 条件 |
|------|------|
| PASS | カバレッジ >= 閾値 |
| FAIL | カバレッジ < 閾値 |
| WARN | カバレッジデータが見つからない |

```bash
# 閾値を手動で上書き
python3 sdd-templates/tools/pr_readiness_checker.py . --coverage-threshold 95
```

### Check 5: walkthrough checklist

**方法**: `specs/**/walkthrough.md` 内の `# Review Checklist` セクションを解析

| 判定 | 条件 |
|------|------|
| PASS | 全チェックボックスが `[x]` |
| FAIL | `[ ]`（未チェック）が 1 つ以上 |
| WARN | walkthrough.md が見つからない |

> **Review Checklist のスコープ**: Security, AC Coverage, Code Quality の3カテゴリ（10項目）が対象です。
> v4.3 で追加された Mode Decision Rationale / Spec Drift Status / Evidence Metrics / PR Readiness セクションにはチェックボックスがないため、このチェックには影響しません。

### Check 6: evidence_pack

**方法**: `specs/**/evidence_pack.md` の必須セクション存在チェック

| 必須セクション | 説明 |
|---------------|------|
| `test_results` | テスト実行結果 |
| `coverage_report` | カバレッジレポート |
| `gate_approvals` | Gate 承認記録 |

| 判定 | 条件 |
|------|------|
| PASS | 全必須セクションが存在 |
| FAIL | 1 つ以上の必須セクションが欠落 |
| WARN | evidence_pack.md が見つからない |

### Check 7: TODO/FIXME

**方法**: `src/` 配下のソースコードを正規表現でスキャン

| 判定 | 条件 |
|------|------|
| PASS | TODO/FIXME が 0 件 |
| WARN | TODO/FIXME あり（通常モード） |
| FAIL | TODO/FIXME あり（`--strict` モード） |

```bash
# strict モードで TODO/FIXME を FAIL に
python3 sdd-templates/tools/pr_readiness_checker.py . --strict
```

### Check 8: Mutation Testing

**方法**: `cosmic-ray` を使ってミューテーションテストを実行し、スコアを閾値と比較

> **注: `--mutation` フラグが必要**  
> このチェックはデフォルト無効です。`--mutation` を指定したときのみ実行されます。  
> `cosmic-ray` がインストールされていない場合は WARN になります。

| 判定 | 条件 |
|------|------|
| PASS | ミューテーションスコア >= 閾値 |
| FAIL | ミューテーションスコア < 閾値 |
| WARN | `--mutation` 未指定、または `cosmic-ray` 未インストール |

**閾値の設定**:

```bash
# .env.local で設定（デフォルト: 80%）
MUTATION_THRESHOLD=85
```

ミューテーションテストは「テストが意味のある検証をしているか」を計測します。
コードを意図的に壊した（ミューテーション）場合に、テストが失敗するかどうかで品質を評価します。

```bash
# --mutation オプションで Check 8 を有効化
stride pr-check . --mutation
```

---

## 3. 使い方

### 基本実行

```bash
# stride CLI 経由（推奨）
stride pr-check <project_root>

# 直接実行
python3 sdd-templates/tools/pr_readiness_checker.py <project_root>
```

### オプション

| オプション | 説明 |
|-----------|------|
| `--json` | JSON 形式で出力（CI 連携用） |
| `--summary-line` | **project-level の 1 行サマリを出力（v5.4）** — 7 base checks（`--mutation` 併用時は +1）を `stride pr-check: PR_READY (stride-lint PASS / spec:drift PASS / ...)` 形式で出す |
| `-v`, `--verbose` | 詳細出力 |
| `--strict` | TODO/FIXME を FAIL に昇格 |
| `--coverage-threshold N` | カバレッジ閾値を手動指定（%） |
| `--mutation` | ミューテーションテスト（Check 8）を有効化（`cosmic-ray` 必須） |

#### `--summary-line` の責務境界（v5.4 重要）

v5.4 で追加された `--summary-line` は**意図的に project-level のみ**を出力する:

- **出力する**: 7 base checks (+ optional mutation) の PASS/FAIL — 例 `stride pr-check: PR_READY (stride-lint PASS / spec:drift PASS / tests PASS / coverage PASS / walkthrough checklist PASS / evidence pack PASS / TODO/FIXME scan PASS)`
- **出力しない**: task ID (`T-XXX-001`) / AC-* 全充足 / NFR OK / scenarios.yaml / `(coverage: <tier>)`

task-level の 1 行合成（`✅ T-XXX-001: AC-* 全充足 / NFR OK / stride-lint PASS / pr-check PR_READY (coverage: <tier>)`）は **AI の責務**で、`agent_docs/sdd_bootstrap.md §5 Step 1-5` の実行結果と task 文脈を AI が合成する。
Profile が `prototype` や `saas-integration`（non-critical）の時に使う task-level 1-line は、`--summary-line` の出力を **PR_READY 部分だけ抽出**し、残りは AI が合成する。

詳細: [38. Profile ガイド](38_profile_guide.md)、`agent_docs/sdd_bootstrap.md §5.2`

### 終了コード

| Exit Code | 意味 |
|-----------|------|
| 0 | `PR_READY` — PR 作成可 |
| 1 | `NOT_READY` — 品質チェック不合格 |
| 2 | `ERROR` — ツールエラー |

---

## 4. 出力例

### 4.1 PR_READY の場合

```
=== PR Readiness Check ===
Project: /path/to/project

[1/8] stride-lint:        PASS (0 errors, 0 warnings)
[2/8] spec:drift:          PASS (0 drifts)
[3/8] tests:               PASS (47/47 passed)
[4/8] coverage:            PASS (87.3% >= 80%)
[5/8] walkthrough:         PASS (10/10 checked)
[6/8] evidence_pack:       PASS (3/3 sections)
[7/8] TODO/FIXME:          WARN (3 items found)
[8/8] mutation:            PASS (85% >= 80%)

Result: PR_READY
```

### 4.2 NOT_READY の場合

```
=== PR Readiness Check ===
Project: /path/to/project

[1/8] stride-lint:        FAIL (2 errors, 1 warnings)
[2/8] spec:drift:          FAIL (1 critical, 0 high drifts)
[3/8] tests:               PASS (47/47 passed)
[4/8] coverage:            FAIL (65.2% < 80%)
[5/8] walkthrough:         FAIL (7/10 checked)
[6/8] evidence_pack:       WARN (evidence_pack.md not found)
[7/8] TODO/FIXME:          PASS (0 items)
[8/8] mutation:            WARN (--mutation not specified)

Result: NOT_READY
Failed checks: stride-lint, spec:drift, coverage, walkthrough
```

### 4.3 JSON 出力

```bash
python3 sdd-templates/tools/pr_readiness_checker.py . --json
```

```json
{
  "result": "NOT_READY",
  "checks": {
    "stride_lint": {"status": "FAIL", "errors": 2, "warnings": 1},
    "spec_drift": {"status": "FAIL", "critical": 1, "high": 0},
    "tests": {"status": "PASS", "total": 47, "passed": 47, "failed": 0},
    "coverage": {"status": "FAIL", "total_pct": 65.2, "threshold": 80},
    "walkthrough": {"status": "FAIL", "checked": 7, "total": 10},
    "evidence_pack": {"status": "WARN", "detail": "not found"},
    "todo_fixme": {"status": "PASS", "count": 0},
    "mutation": {"status": "WARN", "detail": "--mutation not specified"}
  }
}
```

---

## 5. walkthrough_template.md の v4.3 対応

v4.3 では `walkthrough_template.md` に以下のセクションが追加されています：

| セクション | バージョン | 内容 |
|-----------|-----------|------|
| Mode Decision Rationale | v3.1 | autonomy_bias 適用結果、mode 選択理由 |
| Spec Drift Status | v4.2 | drift 検出結果、解決方法 |
| Evidence Metrics | v4.2 | coverage, テスト結果, キャッシュ率, Gate リードタイム |
| PR Readiness | v4.3 | `stride pr-check` 実行結果サマリ |

これらのセクションはプレースホルダのみ（チェックボックスなし）のため、Check 5（walkthrough checklist）には影響しません。

---

## 6. SDD_MANIFESTO との統合

`SDD_MANIFESTO.md` に **PR Readiness Rule** が追加されています：

> AI は PR 作成前に `stride pr-check` を実行し、`PR_READY` 判定を得なければ PR を作成してはならない。

このルールは `agent_docs/sdd_guidelines.md` の Task Completion Checklist にもブロッキングルールとして反映されています。

---

## 7. セルフテスト

```bash
python3 sdd-templates/tools/pr_readiness_checker.py --test
# 10 tests pass:
#   Test 1: non-existent path handling
#   Test 2: empty project -> NOT_READY
#   Test 3: stride-lint errors -> FAIL or WARN
#   Test 4: critical drift -> FAIL
#   Test 5: drift clean -> PASS
#   Test 6: test failures -> FAIL
#   Test 7: coverage below threshold -> FAIL
#   Test 8: walkthrough unchecked -> FAIL
#   Test 9: TODO/FIXME -> WARN (--strict -> FAIL)
#   Test 10: all checks PASS -> PR_READY (exit 0)
```

---

## 関連ドキュメント

- [Spec Drift & Evidence Metrics ガイド](21_spec_drift_metrics_guide.md) — ドリフト検出とメトリクス収集
- [stride-lint ガイド](appendix_b_stride_lint.md) — 仕様書構造チェック
- [Coverage Policy](19_coverage_policy.md) — Tier 別閾値
- [Evidence Pack ガイド](14_evidence_pack_guide.md) — 品質証跡
- [Adaptive Execution ガイド](17_adaptive_execution_guide.md) — Autonomy Bias
