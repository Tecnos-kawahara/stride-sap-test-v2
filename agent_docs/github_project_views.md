# GitHub Project Views: STRIDE Learning Loop (PM Guide)

> PM/Epic Lead 向け GitHub Projects V2 ビュー設定ガイド

## 概要

STRIDE Learning Loop の GitHub Project には以下の7つの推奨ビューを設定する。
各ビューは WI の Run データ（Findings, Decisions, Spec Impact, Learnings）を
PM が可視化するためのものである。

## 前提条件

1. `setup_project_labels.py` で STRIDE ラベルが作成済み
2. `run_report_generator.py` が Run 完了時に自動実行されている
3. GitHub Projects V2 のカスタムフィールドが設定済み（下記「カスタムフィールド一覧」参照）

## カスタムフィールド一覧

### Learning Loop フィールド（Single Select）

| フィールド名 | 選択肢 | 用途 |
|-------------|--------|------|
| Findings | `0` / `1-3` / `4+` | Run で検出した調査発見事項の件数帯 |
| Decisions | `0` / `1-3` / `4+` | Run 中に行われた設計判断の件数帯 |
| Spec Impact | `none` / `proposed` / `required` | 仕様への影響レベル |
| Learning | `—` / `pattern` | 再利用可能パターンの有無 |

### フィールド作成コマンド

```bash
gh project field-create <N> --owner <OWNER> --name "Findings" \
  --data-type "SINGLE_SELECT" --single-select-options "0,1-3,4+"
gh project field-create <N> --owner <OWNER> --name "Decisions" \
  --data-type "SINGLE_SELECT" --single-select-options "0,1-3,4+"
gh project field-create <N> --owner <OWNER> --name "Spec Impact" \
  --data-type "SINGLE_SELECT" --single-select-options "none,proposed,required"
gh project field-create <N> --owner <OWNER> --name "Learning" \
  --data-type "SINGLE_SELECT" --single-select-options "—,pattern"
```

### 自動フィールド更新

Run 完了時に `--project-fields` オプションで自動設定:

```bash
python3 sdd-templates/tools/run_report_generator.py \
  specs/<feature>/runs/<WI>/<RUN>/ \
  --post --issue <N> --labels --project-fields --project <P> --owner <OWNER>
```

## View 1: Findings View (Table)

**目的**: WI ごとの調査発見事項の傾向を把握する

**設定手順**:
1. GitHub Projects → New View → Table
2. Name: "Findings"
3. フィルタ: `label:findings:0,findings:1-3,findings:4+`
4. グループ: Label (findings:*)

**推奨カラムレイアウト**:

| # | カラム名 | 種別 | 目的 |
|---|---------|------|------|
| 1 | Title | 既定 | Issue タイトル |
| 2 | Status | 既定 | Todo / In Progress / Done |
| 3 | WI ID | テキスト | WI 識別子 |
| 4 | **Findings** | Single Select | **0 / 1-3 / 4+** を一目で確認 |
| 5 | Run ID | テキスト | 最新 Run ID |
| 6 | Risk Flags | テキスト | リスクフラグ |
| 7 | Priority | Single Select | P0〜P3 |

**活用方法**:
- `findings:4+` が多い WI は調査難易度が高い → リソース配分の判断材料
- `findings:0` が続く WI は計画通りの進行を示す

## View 2: Decisions View (Table)

**目的**: Run 中の設計判断の一覧と追跡

**設定手順**:
1. GitHub Projects → New View → Table
2. Name: "Decisions"
3. フィルタ: `label:decisions:1-3,decisions:4+`
4. ソート: Priority (descending)

**推奨カラムレイアウト**:

| # | カラム名 | 種別 | 目的 |
|---|---------|------|------|
| 1 | Title | 既定 | Issue タイトル |
| 2 | Status | 既定 | Todo / In Progress / Done |
| 3 | WI ID | テキスト | WI 識別子 |
| 4 | Feature ID | テキスト | Feature 識別子 |
| 5 | **Decisions** | Single Select | **0 / 1-3 / 4+** を一目で確認 |
| 6 | Complexity | Single Select | low / medium / high |
| 7 | Priority | Single Select | P0〜P3 |

**活用方法**:
- `decisions:4+` の WI はアーキテクチャ影響が大きい可能性 → レビュー優先度を上げる
- Decision Log を週次で確認し、一貫性を保つ

## View 3: Spec Impact View (Board)

**目的**: Spec 変更が必要な WI をステータス別に管理

**設定手順**:
1. GitHub Projects → New View → Board
2. Name: "Spec Impact"
3. Column field: **Spec Impact** (カスタムフィールド)
4. フィルタ: `label:spec-impact:proposed,spec-impact:required` (none は非表示推奨)

**推奨カラムレイアウト** (Board のカード内表示):

| # | カラム名 | 種別 | 目的 |
|---|---------|------|------|
| 1 | Title | 既定 | Issue タイトル |
| 2 | Status | 既定 | Todo / In Progress / Done |
| 3 | WI ID | テキスト | WI 識別子 |
| 4 | **Spec Impact** | Single Select | Board のカラムとして使用 |
| 5 | **Findings** | Single Select | 調査件数の傾向を同時確認 |
| 6 | Priority | Single Select | P0〜P3 |

**活用方法**:
- `spec-impact:required` は **ブロッカー** → 即座に対応が必要
- `spec-impact:proposed` は次回 Sprint Planning で議論する
- 週次で Board を確認し、未解決の spec impact を追跡する

## View 4: Learnings View (Table)

**目的**: Run から得られた再利用可能なパターンの蓄積と共有

**設定手順**:
1. GitHub Projects → New View → Table
2. Name: "Learnings"
3. フィルタ: `label:learning:pattern`
4. ソート: Created date (descending)

**推奨カラムレイアウト**:

| # | カラム名 | 種別 | 目的 |
|---|---------|------|------|
| 1 | Title | 既定 | Issue タイトル |
| 2 | Status | 既定 | Todo / In Progress / Done |
| 3 | WI ID | テキスト | WI 識別子 |
| 4 | Feature ID | テキスト | Feature 識別子 |
| 5 | **Learning** | Single Select | **— / pattern** を確認 |
| 6 | **Findings** | Single Select | 調査件数との相関を確認 |

**活用方法**:
- 新規 WI の計画時にこのビューを参照し、既知パターンを適用する
- 月次で Learnings を集約し、チーム知識ベースに反映する

## View 5: Amendments (Board)

**目的**: 仕様改訂のライフサイクル追跡

**設定手順**:
1. GitHub Projects → New View → Board
2. Name: "Amendments"
3. Filter: `label:amendment`
4. Column field: Label (`amendment:draft` / `amendment:review` / `amendment:applying` / `amendment:applied`)

**活用方法**:
- `amendment:draft`: 起案済み、レビュー待ち
- `amendment:review`: レビュー中、承認待ち
- `amendment:applying`: PM承認済み、Spec反映PR作成中・レビュー中
- `amendment:applied`: 反映完了、新WI起票済み
- spec-impact:required が蓄積した場合、`amendment_generator.py auto-check` で自動検出

**Amendment 完全ライフサイクル**:

```
spec-impact 検知 → analyze → draft → create (Issue作成)
  → PM承認 (チェックボックス)
  → apply (Spec反映PR作成 + amendment:applying)
  → PR レビュー・マージ
  → finalize (amendment:applied + spec-impact解消 + 新WI起票 + close)
```

## View 6: Process Metrics View (Table)

**目的**: Gate 別の滞留時間と遅延リスクを一覧で把握し、ボトルネック工程を特定する

**設定手順**:
1. GitHub Projects → New View → Table
2. Name: "Process Metrics"
3. フィルタ: `label:work-item`
4. ソート: `Delay Risk` ascending (overdue を先頭に表示)

**推奨カラムレイアウト**:

| # | カラム名 | 種別 | 目的 |
|---|---------|------|------|
| 1 | Title | 既定 | Issue タイトル |
| 2 | Status | 既定 | Todo / In Progress / Done |
| 3 | WI ID | テキスト | WI 識別子 |
| 4 | **Gate** | Single Select | 現在の Gate (`g1`〜`evidence`) |
| 5 | **Gate Age (days)** | Number | 現在 Gate での滞留日数 |
| 6 | **Delay Risk** | Single Select | `on_track` / `at_risk` / `overdue` |
| 7 | Complexity | Single Select | low / medium / high |

**フィルタ例**:
- `Delay Risk is at_risk OR Delay Risk is overdue` — 遅延リスクのある WI のみ表示
- `Gate is evidence` — Evidence Review フェーズの WI のみ
- `Gate Age (days) > 5` — 5日以上滞留している WI

**カスタムフィールド作成コマンド**:

```bash
gh project field-create <N> --owner <OWNER> --name "Gate Age (days)" \
  --data-type "NUMBER"
gh project field-create <N> --owner <OWNER> --name "Delay Risk" \
  --data-type "SINGLE_SELECT" --single-select-options "on_track,at_risk,overdue"
gh project field-create <N> --owner <OWNER> --name "Inject Rate" \
  --data-type "SINGLE_SELECT" --single-select-options "0%,1-20%,21-50%,50%+"
gh project field-create <N> --owner <OWNER> --name "Lead Time (days)" \
  --data-type "NUMBER"
gh project field-create <N> --owner <OWNER> --name "Gate" \
  --data-type "SINGLE_SELECT" --single-select-options "g1,g2,g3,g4,g5,evidence"
```

**自動フィールド更新**:

state.yaml の変更がプッシュされた際に `stride-sync.yml` ワークフローが
`stride_process_metrics.py` を実行し、Process Metrics フィールドを自動更新する。

```bash
# 手動実行
python scripts/stride_process_metrics.py \
  --feature specs/<feature>/ --output table

# ダッシュボード自動更新
python scripts/stride_process_metrics.py \
  --feature specs/<feature>/ --update-dashboard
```

**活用方法**:
- 週次で `Delay Risk` が `at_risk` または `overdue` の WI を確認 → PM エスカレーション判断
- `Gate Age (days)` の推移を追跡し、特定 Gate にボトルネックがないか分析
- `Gate` フィールドでグルーピングすることで、どの工程に WI が集中しているか可視化
- プロセスタイム分析データを GitHub Projects V2 上で確認可能

## View 7: Sentry Issues (Table)

**目的**: Sentryで検出されたエラーに紐づくGitHub Issueを追跡し、エラー解決の進捗を管理する

**前提条件**:
1. Sentry プロジェクトが作成済み
2. Sentry GitHub Integration が設定済み（双方向同期ON）
3. `setup_project_labels.py` で Sentry ラベルが作成済み

**設定手順**:
1. GitHub Projects → New View → Table
2. Name: "Sentry Issues"
3. フィルタ: `label:sentry,sentry:critical,sentry:error,sentry:warning`
4. ソート: Priority (descending)

**推奨カラムレイアウト**:

| # | カラム名 | 種別 | 目的 |
|---|---------|------|------|
| 1 | Title | 既定 | Issue タイトル（Sentry Issue リンク含む） |
| 2 | Status | 既定 | Todo / In Progress / Done |
| 3 | WI ID | テキスト | 関連 WI 識別子 |
| 4 | Priority | Single Select | P0〜P3 |
| 5 | Assignees | 既定 | 担当者 |

**活用方法**:
- `sentry:critical` は即時対応 → P0 として扱う
- `sentry:error` は当日〜翌営業日対応
- `sentry:warning` は次回 Sprint で検討
- Sentry ダッシュボードとの双方向同期により、GitHub Issue を close すると Sentry も自動 resolve

**Sentry → GitHub Issue 連携**:
- Sentry ダッシュボードから「Create GitHub Issue」で直接 Issue を作成可能
- 作成された Issue には自動で `sentry` ラベルが付与される
- Sentry Issue のコメントが GitHub Issue にも同期される（Sentry設定で有効化）

**Sentry 導入手順（新規プロジェクト向け）**:
1. Sentry にプロジェクト作成（Node.js / Express）
2. `@sentry/node` + `@sentry/profiling-node` を依存追加
3. アプリ起動の最初に `Sentry.init()` を呼び出す（OTel統合あり）
4. Sentry Settings → Integrations → GitHub で対象リポジトリを接続
5. 同期設定をすべてON（Status / Assignment / Comments）

## カラム追加手順（UI操作ガイド）

### Table ビューでのカラム追加

1. ビューを開く（Findings / Decisions / Learnings）
2. テーブル右端の **「+」** ボタンをクリック
3. フィールド一覧から追加したいフィールドを選択（例: `Findings`）
4. カラムが追加されたら、ヘッダーをドラッグして推奨レイアウトの順序に並べ替え
5. 不要なカラムはヘッダー右クリック → **「Hide field」** で非表示

### Board ビューでの Column field 変更

1. ビューを開く（Spec Impact / Amendments）
2. ビュー名の横の **「▼」** → **「Column field」** を選択
3. `Spec Impact` フィールドを選択すると、`none` / `proposed` / `required` のカラムに自動分類
4. カード内にフィールドを表示するには、**「Fields」** メニューから追加

### フィルタの設定

1. ビュー上部の **「Filter」** をクリック
2. フィルタ条件を入力（例: `label:findings:4+` や `Spec Impact is required`）
3. カスタムフィールドでもフィルタ可能（例: `Findings is 4+`）

### ソートの設定

1. カラムヘッダーをクリック → **「Sort ascending / descending」**
2. 複数ソート: **「Sort」** ボタン → **「+ Add sort」** で追加

## ラベル一覧

| ラベル | 色 | 説明 |
|--------|-----|------|
| `findings:0` | #c5def5 | Run findings: 0 items |
| `findings:1-3` | #0075ca | Run findings: 1-3 items |
| `findings:4+` | #003f8a | Run findings: 4+ items |
| `decisions:0` | #e8d5f5 | Run decisions: 0 items |
| `decisions:1-3` | #7b2d8e | Run decisions: 1-3 items |
| `decisions:4+` | #4a0e5c | Run decisions: 4+ items |
| `spec-impact:none` | #0e8a16 | No spec changes needed |
| `spec-impact:proposed` | #fbca04 | Spec changes proposed |
| `spec-impact:required` | #e11d48 | Spec changes required (blocker) |
| `learning:pattern` | #0d9488 | Reusable pattern discovered |
| `amendment` | #d4a017 | Specification amendment |
| `amendment:draft` | #fef3c7 | Amendment drafted, pending review |
| `amendment:review` | #f59e0b | Amendment under review |
| `amendment:applying` | #2563eb | Amendment spec changes in PR review |
| `amendment:applied` | #059669 | Amendment approved and applied to spec |
| `amendment-derived` | #c2e0c6 | WI derived from amendment |
| `sentry` | #362d59 | Linked to Sentry issue |
| `sentry:critical` | #b60205 | Sentry critical/fatal error |
| `sentry:error` | #d93f0b | Sentry error level issue |
| `sentry:warning` | #fbca04 | Sentry warning level issue |

## CLI コマンド

```bash
# ラベル一括作成
python3 sdd-templates/tools/setup_project_labels.py --repo owner/repo

# Run レポート生成 + ラベル適用
python3 sdd-templates/tools/run_report_generator.py \
  specs/<feature>/runs/<WI>/<RUN>/ \
  --post --issue <N> --labels

# Run レポート + ラベル + プロジェクトフィールド自動設定
python3 sdd-templates/tools/run_report_generator.py \
  specs/<feature>/runs/<WI>/<RUN>/ \
  --post --issue <N> --labels \
  --project-fields --project <P> --owner <OWNER>

# 週次サマリ生成
python3 sdd-templates/tools/epic_progress_aggregator.py \
  epics/<EPIC>/ --weekly-summary

# 週次サマリを Issue に投稿
python3 sdd-templates/tools/epic_progress_aggregator.py \
  epics/<EPIC>/ --weekly-summary --post --epic <N>

# Amendment 影響分析
python3 sdd-templates/tools/amendment_generator.py analyze \
  --feature FEAT-XXX --topic "トピック"

# Amendment ドラフト生成
python3 sdd-templates/tools/amendment_generator.py draft \
  --feature FEAT-XXX --title "改訂タイトル" --spec-sections "AC-001"

# Amendment Issue 作成
python3 sdd-templates/tools/amendment_generator.py create \
  --feature FEAT-XXX --draft draft.md

# Amendment 承認後 → Spec反映PR作成
python3 sdd-templates/tools/amendment_generator.py apply --issue <N>

# Amendment PRマージ後 → WI起票 + 完了
python3 sdd-templates/tools/amendment_generator.py finalize --issue <N>

# spec-impact 蓄積チェック（自動トリガー）
python3 sdd-templates/tools/amendment_generator.py auto-check \
  --feature FEAT-XXX --threshold 2
```

## 運用フロー

```
Run 完了 → run_report_generator.py --labels --project-fields
           → Issue コメント + ラベル + Project フィールド自動設定
    ↓
週次   → epic_progress_aggregator.py --weekly-summary → Epic Issue コメント
    ↓
PM確認 → Findings/Decisions/Spec Impact/Learnings の5ビューで確認
    ↓
spec-impact 蓄積 → amendment_generator.py auto-check → ドラフト生成
    ↓
PM承認 → amendment_generator.py apply → Spec反映PR作成 (amendment:applying)
    ↓
PM PRレビュー・マージ
    ↓
finalize → amendment:applied + spec-impact解消 + 新WI起票 + close
    ↓
Amendments ビューで改訂ライフサイクルを追跡
    ↓
Sentry エラー → Sentry ダッシュボードから GitHub Issue 作成 → sentry ラベル付与
    → GitHub Issue close → Sentry 自動 resolve（双方向同期）
    → Sentry Issues ビューで解決進捗を追跡
```
