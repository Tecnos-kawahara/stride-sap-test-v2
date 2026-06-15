# 25. PMダッシュボードガイド

> **Version**: v5.4.0-tecnos-stride
> **対象**: PM / Epic Lead

---

## 21.1 ダッシュボード概要

Tecnos-STRIDE v3.1 では、PMがEpic横断でプロジェクト健全性を把握するための **4つの出力形式** を提供します。

| 形式 | コマンド | 用途 |
|------|---------|------|
| **HTML** (v3.1) | `--format html` | ブラウザで閲覧するビジュアルダッシュボード |
| **Markdown** | `--format markdown` | GitHub/Docsifyで表示するテキストダッシュボード |
| **JSON** | `--format json` | CI/CD連携・カスタムツール向けデータ |
| **Summary** | `--format summary`（デフォルト） | ターミナル確認用コンパクト表示 |

### HTMLダッシュボード（v3.1 新規）

ブラウザで開くだけでプロジェクト全体を一覧できる **ビジュアルダッシュボード** です。

```bash
# HTML ダッシュボードを生成
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format html

# → epics/EPIC-ORDER/EPIC_DASHBOARD.html が生成される
# → ブラウザで開くだけで閲覧可能（外部依存なし）
```

#### 6パネル構成

```
┌─────────────────────────────────────────────────────────────┐
│  Header: Epic ID / Title / Health Badge / 生成日            │
├──────────────────┬──────────────────┬───────────┬──────────┤
│ Features         │ Gates Passed     │ WIs Done  │ Risks    │
│ (KPI)            │ (KPI)            │ (KPI)     │ (KPI)    │
├──────────────────┴──────┬───────────┴──────────┴──────────┤
│  ① Team Health          │  ② Gate Pipeline                 │
│  ┌──────┐ ┌──────┐      │  FEAT-001 [■■■■■□] G5  83%      │
│  │TEAM-A│ │TEAM-B│      │  FEAT-002 [■■■□□□] G3  50%      │
│  │● 68% │ │▲ 42% │      │  FEAT-003 [■□□□□□] G1  17%      │
│  └──────┘ └──────┘      │                                  │
├─────────────────────────┴──────────────────────────────────┤
│  ③ Work Items (Kanban)                      [Feature ▼]    │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐                   │
│  │ Pending  │  │In Progress│  │  Done   │                   │
│  │ ┌─────┐ │  │ ┌──────┐ │  │ ┌─────┐ │                   │
│  │ │WI-03│ │  │ │WI-02 │ │  │ │WI-01│ │                   │
│  │ │ auto│ │  │ │⚠valid│ │  │ │ auto│ │                   │
│  │ └─────┘ │  │ └──────┘ │  │ └─────┘ │                   │
│  └─────────┘  └──────────┘  └─────────┘                   │
├──────────────────────┬─────────────────────────────────────┤
│  ④ Milestones        │  ⑤ Blockers & Risks                 │
│  EM-01 [████░░] 67%  │  ● FEAT-A/WI-002: validate+authz   │
│  2026-03 (32d left)  │  ● FEAT-B/WI-005: pii in_progress  │
├──────────────────────┴─────────────────────────────────────┤
│  ⑥ Cross-Team Dependencies (SVG + Table)                   │
│  [FEAT-A] ──blocking──→ [FEAT-B]  pending                  │
└────────────────────────────────────────────────────────────┘
```

| # | パネル | 機能 |
|---|--------|------|
| ① | **Team Health** | チーム別カード、Gate%/WI%プログレスバー、GREEN/YELLOW/RED色分け |
| ② | **Gate Pipeline** | Feature毎の6段階ステップバー、Coverage Tierバッジ、Autonomy Biasアイコン |
| ③ | **WI Kanban** | 3列ボード（Pending/In Progress/Done）、Mode色分け、Feature フィルタ |
| ④ | **Milestones** | プログレスバー、残日数/超過日数表示、ステータスバッジ |
| ⑤ | **Blockers & Risks** | リスクエスカレーション一覧、severity色分け |
| ⑥ | **Dependencies** | SVGグラフ＋テーブル表示、blocking/soft区別、ステータス色分け |

#### PM向け機能

- **Feature フィルタ**: Kanbanボードをドロップダウンで Feature別に絞り込み
- **Mode 凡例**: autopilot(緑)/confirm(黄)/validate(赤) の色分け
- **残日数表示**: Milestoneの期限までの日数を自動計算、超過は赤表示
- **Coverage Tier バッジ**: critical(赤)/standard(青)/experimental(紫) で視認性向上
- **Autonomy Bias アイコン**: ⚡(autonomous)/🛡️(controlled) をFeature名横に表示
- **レスポンシブ**: PC/タブレット/プロジェクター対応
- **印刷対応**: `Ctrl+P` でそのまま印刷可能

### Markdown ダッシュボード（従来形式）

```
EPIC_PROGRESS_REPORT.md
├── Executive Summary（全体健全性: GREEN/YELLOW/RED）
├── Team Status Table（チーム別進捗）
├── Gate Completion Matrix（Feature × Gate マトリクス）
├── Milestone Progress（マイルストーン進捗）
├── Cross-Team Dependencies（依存ステータス）
├── Risk Register（リスク一覧）
├── Blocker List（ブロッカー一覧）
└── Next Period Actions（次期アクション）
```

---

## 21.2 Gate Completion Matrixの読み方

```
Feature          | G1  | G2  | G3  | G4  | G5  | Final
─────────────────┼─────┼─────┼─────┼─────┼─────┼──────
FEAT-ORD-001     | ✅  | ✅  | ✅  | ✅  | 🔄  |  -
FEAT-ORD-002     | ✅  | ✅  | 🔄  |  -  |  -  |  -
FEAT-ORD-003     | ✅  | ⛔  |  -  |  -  |  -  |  -
```

| 記号 | 意味 |
|------|------|
| ✅ | Gate通過（APPROVAL.md承認済み） |
| 🔄 | 作業中（成果物あり、承認待ち） |
| ⛔ | ブロック（前提条件未充足） |
| `-` | 未着手 |

---

## 21.3 Team Statusメトリクス

各チームの健全性を以下の指標で評価:

| 指標 | 算出方法 | 閾値 |
|------|----------|------|
| Gate Pass Rate | 通過Gate数 / 全Gate数 × 100 | GREEN: ≥60%, YELLOW: ≥30%, RED: <30% |
| WI Completion | done WI / 全WI × 100 | GREEN: ≥70%, YELLOW: ≥40%, RED: <40% |
| Blocker Count | ブロッカー数 | GREEN: 0, YELLOW: 1-2, RED: ≥3 |

---

## 21.4 Milestone Tracking

```yaml
milestones:
  - id: "EM-01"
    name: "基盤Feature完了"
    target_date: "2026-03-15"
    status: "on_track"       # on_track | at_risk | blocked | complete
    features_required: ["FEAT-ORD-001"]
    features_complete: ["FEAT-ORD-001"]
    gate_required: "Gate 5"
```

### ステータス判定ロジック

- **on_track**: 全required featuresが予定Gate以上に到達
- **at_risk**: 残日数 < 見積り工数の120%
- **blocked**: 1つ以上のrequired featureがblocked依存を持つ
- **complete**: 全required featuresが指定Gateを通過

---

## 21.5 リスクエスカレーション

### 自動検知されるリスク

| リスク | 検知条件 | アクション |
|--------|----------|-----------|
| High-Risk WI長期化 | validate mode WI が in_progress > 5日 | PMに通知 |
| Gate停滞 | Gate承認待ち > 7日 | Epic Leadに通知 |
| 依存遅延 | blocking依存が at_risk | 両チームリードに通知 |
| Ops未準備 | Go-Live 14日前でOps Pack未完了 | PMに通知 |

### エスカレーションフロー

```
Team Lead → Epic Lead → PM → ARCH_BOARD
         24h          48h       72h
```

---

## 21.6 ダッシュボード生成

### 手動生成

```bash
# HTML ダッシュボード（推奨 — ブラウザで開くだけ）
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format html

# Markdown ダッシュボード（GitHub表示用）
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format markdown

# JSON（CI/カスタムツール連携）
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format json

# カスタム出力パス
python3 sdd-templates/tools/epic_progress_aggregator.py epics/EPIC-ORDER/ --format html --output docs/dashboard.html
```

### 自動生成（GitHub Actions）

`.github/workflows/epic-progress-report.yml`:

```yaml
name: Epic Progress Report
on:
  schedule:
    - cron: '0 9 * * 1-5'  # 平日9時
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pyyaml
      - run: |
          for epic_dir in epics/EPIC-*/; do
            python3 sdd-templates/tools/epic_progress_aggregator.py "$epic_dir" --format html
            python3 sdd-templates/tools/epic_progress_aggregator.py "$epic_dir" --format markdown
          done
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore(epic): Update progress dashboards"
```

> **テンプレート**: `sdd-templates/templates/github-actions/epic-progress-report.yml` をプロジェクトの `.github/workflows/` にコピーして使用できます。

> **GitHub Pages**: HTML ダッシュボードを `docs/` に出力すれば GitHub Pages で自動公開できます。

---

## 21.7 週次ステアリング会議の進め方

### アジェンダ（推奨30分）

1. **ダッシュボード確認**（5分）
   - 全体ステータス（GREEN/YELLOW/RED）
   - Gate通過率の変化

2. **ブロッカーレビュー**（10分）
   - 新規ブロッカーの確認
   - 既存ブロッカーの進捗
   - エスカレーション判断

3. **依存ステータス**（5分）
   - at_risk / blocked の依存
   - 新規依存の追加

4. **マイルストーン進捗**（5分）
   - 次マイルストーンの達成見込み
   - リスク要因

5. **アクションアイテム**（5分）
   - EPIC_PROGRESS_REPORT.mdのNext Period Actionsを更新

---

## 21.8 ベストプラクティス

1. **ダッシュボードは毎日見る**: `epic_progress_aggregator.py` を日次実行
2. **ブロッカーは即座に登録**: 24h SLAを守る
3. **ステータスレポートの催促を仕組み化**: GitHub Actions + Slack通知
4. **依存の先行解消**: blocking依存は最優先で安定化
5. **Ops Packは早めに着手**: Go-Live 1ヶ月前には50%完了目標

---

## 21.9 プロセスメトリクス（Gate別滞留時間分析）

v4.4 で追加された `stride_process_metrics.py` は、APPROVAL.md の Gate 承認日時から工程別の滞留日数を計算し、WI 単位の遅延リスクを自動検知します。

### コマンド

```bash
# Feature 単位の分析
python3 sdd-templates/tools/stride_process_metrics.py --feature specs/FEAT-ERPSAMPLE --output table

# Epic 単位の分析
python3 sdd-templates/tools/stride_process_metrics.py --epic epics/EPIC-SAMPLE --output json

# PM_DASHBOARD.md を自動更新
python3 sdd-templates/tools/stride_process_metrics.py --feature specs/FEAT-ERPSAMPLE --update-dashboard

# Dry-run（変更を適用せず確認のみ）
python3 sdd-templates/tools/stride_process_metrics.py --feature specs/FEAT-ERPSAMPLE --dry-run --verbose
```

### 出力形式

| 形式 | オプション | 用途 |
|------|----------|------|
| **Table** | `--output table`（デフォルト） | ターミナルでの確認 |
| **JSON** | `--output json` | CI/CD連携・カスタムツール |
| **Markdown** | `--output markdown` | PM_DASHBOARD.md への埋め込み |

### 遅延リスク判定

| リスク | 条件 | アイコン |
|--------|------|---------|
| `on_track` | 滞留日数 < 閾値×50% | 🟢 |
| `at_risk` | 滞留日数 ≥ 閾値×50% | 🟡 |
| `overdue` | 滞留日数 ≥ 閾値 | 🔴 |

閾値は WI の complexity により変動: low=3日, medium=5日, high=7日

### PM_DASHBOARD.md 連携

`--update-dashboard` オプションを使うと、Feature の state.yaml に記載された `epic_ref` を辿り、対応する `epics/<EPIC>/PM_DASHBOARD.md` の `## Process Metrics` セクションを自動更新します。
