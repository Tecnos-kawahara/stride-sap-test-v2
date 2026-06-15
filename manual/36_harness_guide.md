# Harness Maturity Guide

> v5.1.0 — Fowler-inspired test harness integration for Tecnos-STRIDE

---

## 概要

v5.1.0 では、Martin Fowler の Test Harness 思想を基盤に4つの機能を追加します。

| 機能 | コマンド | 目的 |
|------|---------|------|
| **Mutation Testing** | `stride pr-check --mutation` | テストの実効性を測定 |
| **Self-Review Loop** | `stride evaluate --review` | LLM borderline 評価の精度向上 |
| **Runtime Sensors** | `stride health --runtime` | dead code + coverage decay 継続監視 |
| **Harness Report** | `stride harness-report` | harness controls/gaps 可視化 |
| **Janitor Proposals** | Symphony 自動実行 | 技術的負債の定期 Issue 提案 |

---

## Mutation Testing（opt-in）

### なぜ必要か

行カバレッジ 80% でもテストが「正しい値を検証していない」ケースは多い。
Mutation Testing は意図的にコードを壊し、テストが検知できるかを測る。

### セットアップ

```bash
pip install cosmic-ray>=8.3
# MUTATION_THRESHOLD=80 を .env.local に設定（省略時デフォルト 80）
echo "MUTATION_THRESHOLD=80" >> .env.local
```

### 使い方

```bash
# PR 作成前に実行（opt-in）
stride pr-check . --mutation

# JSON 出力
stride pr-check . --mutation --json
```

### 出力例

```
PR Readiness Check
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1/8] stride-lint .................. [PASS]  0 errors, 0 warnings
[2/8] spec:drift ................... [PASS]  0 drifts
...
[8/8] mutation testing ............. [PASS]  83.2% (>= 80%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Result: PR_READY
```

---

## Self-Review Loop（opt-in）

### なぜ必要か

LLM 評価のスコアが 70-85 の「borderline ゾーン」では誤判定が多い。
Self-Review Loop は同じモデルに再評価させ、見落とした critical issue を発見する。

### 使い方

```bash
# borderline 時に自動発動
stride evaluate specs/<feature>/ --phase design --review

# 非 borderline (< 70 or > 85) では loop は実行されない
```

### 動作フロー

```
Primary評価 (OpenAI)
  └─ score 70-85? → self_review_loop() 実行（最大3回）
       └─ critical issue 発見 → primary_result に追記 + overall=FAIL
  └─ それ以外 → review スキップ
       ↓
aggregate_results() で最終判定
```

---

## Runtime Sensors

### Dead Code 検出

```bash
# pylint W0611/W0612/W0613/W0614 を sdd-templates/tools/ に適用
stride health . --runtime

# JSON 出力（CI 統合向け）
stride health . --runtime --json
```

### Coverage Decay 検出

初回実行時に `.coverage_baseline` が作成されます。
以降、`coverage-summary.json` の値が baseline から `COVERAGE_DECAY_THRESHOLD_PCT`（デフォルト 5.0%）以上低下するとアラートになります。

```bash
# .env.local でポリシー設定
COVERAGE_DECAY_THRESHOLD_PCT=3.0
```

### 出力例

```
stride health: HEALTHY
  dead_code:       no dead code
  coverage_decay:  85.2% (baseline 84.0%, stable)
```

---

## Harness Report

```bash
stride harness-report .
stride harness-report . --json
```

### 出力例（FULL）

```
Harness Report: FULL
  coverage_pct:  85.2%
  controls:      8/8 (100.0%)
```

### 出力例（gaps あり）

```
Harness Report: 2 gap(s)
  coverage_pct:  N/A
  controls:      6/8 (75.0%)
  gaps (2):
    - missing control: runtime-sensors
    - no GitHub Actions CI workflow found
```

---

## Janitor Proposals（Symphony 統合）

### 設定

`SYMPHONY.md` の `janitor:` セクションで制御します：

```yaml
janitor:
  enabled: true           # false でオフ（デフォルト）
  interval_hours: 6       # スキャン間隔
  exclude_recent_pr_days: 7   # 直近 N 日以内に PR があれば除外
  risk_flags_exclude:
    - risk:authz          # これらのラベルがある Issue は除外
    - risk:pii
    - risk:external_api
    - risk:sod
```

### スキャン条件

以下をすべて満たす Issue のみが対象になります：
- `mode:autopilot` ラベルあり
- `tier:starter` ラベルあり
- `risk_flags_exclude` 内のラベルなし
- 直近 `exclude_recent_pr_days` 日以内に merged PR なし

### 動作

Janitor は **GitHub Issue を起票するだけ**です（自動 PR は行いません）。
タイトル: `Janitor: fix style/cyclomatic <feature>`

---

## Scale 別推奨設定

| 設定 | starter | standard | enterprise |
|------|---------|----------|-----------|
| `--mutation` | - | CI opt-in | CI 必須 |
| `--review` | - | 推奨 | 必須 |
| `stride health --runtime` | 手動 | CI 推奨 | CI 必須 |
| `stride harness-report` | 月次 | 週次 | 毎日 |
| Janitor | 対象 | 対象 | 設定次第 |

---

## 関連コマンド

```bash
stride pr-check .                      # 7チェック (標準)
stride pr-check . --mutation           # + mutation (opt-in)
stride evaluate specs/<f>/ --review    # self-review loop
stride health . --runtime --json       # runtime sensors
stride harness-report . --json         # harness report
```

---

## 参照

- `agent_docs/harness.md` — AI エージェント向け詳細ガイド
- `manual/22_pr_readiness_guide.md` — PR Readiness Checker
- `manual/32_multi_model_evaluator_guide.md` — Semantic Gate
- `manual/30_symphony_orchestration_guide.md` — Symphony オーケストレーション
