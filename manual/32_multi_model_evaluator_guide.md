# Multi-Model Evaluator ガイド

> `stride evaluate` — lint では検出できない意味的な穴を LLM が評価する品質ゲート

## 概要

`stride lint` は構造・ID・カウント整合をチェックする。
`stride evaluate` は **LLM が「意味的な穴」を評価する**補完ゲートである。

検出対象:
- ERP/SAP 統合の盲点（BAPI 制限、転記ロック、会計期間依存）
- AC のテスタビリティ（複数動作の混在、境界条件の欠落）
- SoD / 監査要件の曖昧さ
- 統合アーキテクチャの不備（冪等性、リトライ、サーキットブレーカー未定義）

## 使い方

```bash
# Design Phase の評価
stride evaluate specs/<feature>/ --phase design

# Specify Phase の評価
stride evaluate specs/<feature>/ --phase specify

# Tasking Phase の評価
stride evaluate specs/<feature>/ --phase tasking

# JSON 出力
stride evaluate specs/<feature>/ --phase design --format json

# API 障害時に WARN で続行（exit 0）
stride evaluate specs/<feature>/ --phase design --allow-provider-degraded

# coverage_tier=starter でも強制実行
stride evaluate specs/<feature>/ --phase design --force

# Self-Review Loop（ボーダーライン域を再評価）
stride evaluate specs/<feature>/ --phase design --review
```

### 終了コード

| コード | 意味 |
|--------|------|
| `0` | PASS または WARN（通過） |
| `1` | FAIL（差し戻し — 成果物を修正して再実行） |
| `2` | PROVIDER_ERROR（API エラー）または CONFIG_ERROR（キー未設定） |

## 評価 Rubric

### Design Phase (A1-A4)

| 軸 | Weight | 観点 |
|----|--------|------|
| **A1. Business Risk & ERP Blind Spots** | 35% | ERP 制約の未認識、マスタデータ依存、SoD 曖昧さ |
| **A2. AC Testability** | 30% | 自動テスト可能性、複数動作の混在、エラーフロー不足 |
| **A3. Integration Architecture** | 20% | 冪等性、リトライ、タイムアウト、サーキットブレーカー |
| **A4. Scope Defensibility** | 15% | スコープ境界の防御力、out-of-scope の追跡 |

### Specify Phase (B1-B4)

| 軸 | Weight | 観点 |
|----|--------|------|
| **B1. Cross-Artifact Consistency** | 30% | spec ↔ plan ↔ scenarios の整合 |
| **B2. NFR Feasibility** | 25% | パフォーマンス・セキュリティ目標の実現可能性 |
| **B3. Test Scenario Quality** | 25% | Happy + Error + SoD + 統合障害シナリオ |
| **B4. Audit & Compliance Gaps** | 20% | 監査ログ、承認ワークフロー、データ保持 |

### Tasking Phase (C1-C3)

| 軸 | Weight | 観点 |
|----|--------|------|
| **C1. Implementation Risk** | 40% | mode/risk_flags の適切性、タスク順序の安全性 |
| **C2. Coverage Completeness** | 35% | AC → task カバレッジ、統合テスト対応 |
| **C3. Estimation Realism** | 25% | 粒度、依存関係、マイルストーン妥当性 |

## FAIL 条件

以下のいずれか1つでも該当すれば FAIL:

1. **weighted_score < 70** — 全体スコアが閾値未満
2. **severity: "critical" が1件以上** — critical issue の存在
3. **いずれかの criterion score < 50** — hard floor（弱い軸が平均に隠れない）

## 集計ロジック（Primary + Tie-breaker）

```
Primary (OpenAI):
  ├── Clear PASS (score ≥ 70, no critical, all criteria ≥ 50)  → PASS
  ├── Clear FAIL (score < 60, or 2+ critical, or hard floor)   → FAIL
  └── Borderline (60 ≤ score < 70, 1 critical, no hard floor)
        ├── Secondary FAIL → FAIL
        └── Secondary PASS → WARN (exit 0)

--review オプション追加時:
  └── Borderline 拡張 (70 ≤ score < 85)
        └── Self-Review Loop（最大 3 回）
              ├── critical issue 注入 → FAIL
              └── 問題なし → 通常の Secondary チェックへ
```

- Secondary (Gemini) は optional。`GEMINI_MODEL` 未設定なら Primary only
- Secondary の API エラーは常に許容（Primary の結果で判定）

## Self-Review Loop（`--review`）

v5.1.0 で追加。スコアが**ボーダーライン域（70〜84点）**に入った評価に対して、LLM が最大 3 回の自己レビューを自動実行します。

```bash
stride evaluate specs/<feature>/ --phase design --review
```

### 動作

1. Primary スコアが 70〜84 点（ボーダーライン）の場合に Self-Review Loop が起動
2. LLM が同じ成果物を最大 3 回再評価
3. critical issue を発見した場合、`primary_result` に注入 → FAIL 判定へ
4. 問題がなければ、通常の Secondary（Gemini）チェックへ進む

### いつ使うべきか

- `critical` / `standard` tier の重要な Phase Gate 前
- ERP 統合など高リスクな設計の最終確認
- スコアがボーダーライン付近を行き来する場合の品質強化

### 注意

- `starter` tier は自動スキップ（`--force` で強制実行可能）
- Self-Review Loop は Primary Provider（OpenAI）のみ対象
- ループ回数が増えると API コストが増加する

## Compact Packet

Evaluator に渡す入力は **Canonical YAML ブロックのみ**。全文投入は禁止。

| Phase | 抽出対象 |
|-------|---------|
| design | basic_design Canonical YAML + BPMN プロセス要素名 |
| specify | spec + plan Canonical YAML + scenarios.yaml + contracts ファイル一覧 |
| tasking | tasks Canonical YAML + plan coverage summary + AC→task カバレッジマップ |

## 設定（`.env.local`）

```bash
# Primary (必須)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.4
OPENAI_REASONING_EFFORT=xhigh    # none|minimal|low|medium|high|xhigh

# Secondary (任意)
GEMINI_MODEL=gemini-3.1-pro-preview  # 空なら secondary 無効
GEMINI_API_KEY=AIza...               # 空なら Vertex AI (ADC)
GEMINI_THINKING_BUDGET=-1            # -1 = dynamic
```

依存パッケージ:

```bash
pip install -r sdd-templates/requirements-ai-eval.txt
```

## ワークフロー統合

`auto_continue_runner.py` の FULL_WORKFLOW / LITE_WORKFLOW に evaluator ステップが組み込まれている:

```
Phase 1 (Design):
  1. basic_design.md + process.bpmn 作成
  2. pre-approval lint
  3. strict lint
  4. ★ stride evaluate --phase design
  5. HITL: Gate 1,2 承認待ち

Phase 2 (Specify):
  1. spec.md + plan.md + contracts/ 作成
  2. scenarios.yaml 更新
  3. strict lint
  4. ★ stride evaluate --phase specify
  5. HITL: Gate 3,4 承認待ち

Phase 3 (Tasking):
  1. tasks.md 作成
  2. テストタスク調整
  3. strict lint
  4. ★ stride evaluate --phase tasking
  5. HITL: Gate 5 承認待ち
```

## Coverage Tier スキップ

`coverage_tier=starter` の feature は evaluator を自動スキップ（コスト最適化）。
API キーが未設定でも `SKIP / exit 0` で終了する。

`--force` を付けると tier に関係なく実行:

```bash
stride evaluate specs/<feature>/ --phase design --force
```

## 出力

| ファイル | 内容 |
|---------|------|
| `specs/<feature>/state/evaluator_latest.json` | 最新評価結果（上書き） |
| `specs/<feature>/state/eval_report_<phase>_<timestamp>.md` | 評価履歴（追記） |

## Calibration（将来実装）

```bash
stride evaluate --calibrate eval_calibration/golden_sets/
```

`eval_calibration/` に golden set（人間判定済みの PASS/FAIL サンプル）を蓄積し、
evaluator の precision/recall/F1 を計測する。現在は CLI stub のみ。

## トラブルシューティング

| 症状 | 原因 | 対処 |
|------|------|------|
| exit 2 + "OPENAI_API_KEY is not set" | `.env.local` にキーがない | `.env.local` を設定 |
| exit 2 + "OPENAI_MODEL is not set" | モデル名未設定 | `OPENAI_MODEL=gpt-5.4` を設定 |
| exit 2 + "max_tokens unsupported" | 古い SDK バージョン | `pip install --upgrade openai` |
| Gemini エラーだけで FAIL にならない | Secondary のエラーは許容 | 正常動作 — Primary で判定 |
| SKIP で終了する | `coverage_tier=starter` | `--force` で強制実行 |
| `--review` でスコアが下がる | Self-Review で critical issue 注入 | 成果物を修正して再実行 |
| `--review` を付けても変化なし | スコアが [70,85) の範囲外 | ボーダーライン外は Loop なし（正常動作） |
