# Symphony 運用ガイド（SAP 拡張）

## 概要

Symphony は GitHub Issue をトリガーにして Claude Code を自動起動し、SDD の各 Phase を自律実行するオーケストレーターです。

**重要: Symphony の役割は「初期生成」のみです。修正・承認はローカルの Claude Code で行います。**

## 運用フロー

```
┌─ GitHub ─────────────────────────────┐
│                                       │
│  1. Issue 作成（テンプレート選択）     │
│     ↓                                 │
│  2. Symphony が自動検出・実行          │
│     ↓                                 │
│  3. PR 作成 + 承認依頼コメント        │
│                                       │
└───────────────────────────────────────┘
         ↓ ここからローカル
┌─ ローカル Claude Code ───────────────┐
│                                       │
│  4. PR のブランチを checkout           │
│  5. 生成内容をレビュー                │
│  6. 修正が必要なら Claude Code で指示 │
│  7. APPROVAL.md を編集して承認        │
│  8. push                              │
│                                       │
└───────────────────────────────────────┘
```

## 手順詳細

### 1. Issue 作成（GitHub）

GitHub の Issues → New Issue からテンプレートを選択:

| テンプレート | Phase | 入力項目 |
|-------------|-------|---------|
| Symphony: Design (Phase 1) | design | Feature Name, Priority, Description, **Group/Feature YAML パス** |
| Symphony: Specify (Phase 2) | specify | Feature Name, Priority, Description |
| Symphony: Tasking (Phase 3) | tasking | Feature Name, Priority, Description |
| Symphony: Execute (Phase 4) | execute | Feature Name, Priority, Description |

- YAML パスは Phase 1 (Design) のみ。仕様書エディタから出力した YAML を `docs/yaml/` に配置しておく
- Issue 作成と同時に `symphony:ready` ラベルが付与される

### 2. Symphony 実行

```bash
# 特定の Issue を実行
stride symphony dispatch --issue <番号>

# または: ready な Issue を全て実行（ポーリング）
stride symphony run --once
```

Symphony が Claude Code をサブプロセスとして起動し、指定された Phase の作業を自律実行します。

### 3. 結果確認

Symphony の実行結果は Issue のラベルとコメントで通知されます:

| ラベル | 意味 |
|--------|------|
| `symphony:blocked` | APPROVAL_PENDING — 人間の承認待ち |
| `symphony:done` | Phase 完了 |
| `symphony:failed` | 実行失敗（リトライ上限到達） |

### 4. ブランチ checkout（ローカル）

```bash
# Symphony が作成したブランチを checkout
git fetch origin
git checkout symphony/<feature_name>-<issue番号>

# 例
git checkout symphony/edi_shipment_report_import-12
```

### 5. レビューと修正（ローカル Claude Code）

生成された成果物をレビューし、必要に応じて修正します:

```bash
# 生成内容の確認
cat specs/<feature_name>/basic_design.md
cat specs/<feature_name>/process.bpmn

# Claude Code で修正指示（例）
# 「basic_design.md の processes セクションの P2 チェック処理の body を修正して」
# 「process.bpmn の GW-002 の分岐条件を変更して」
```

**修正は Symphony を再実行するのではなく、ローカルの Claude Code で直接指示してください。**
修正は対話的な判断が必要なため、Issue ベースの自動実行より Claude Code 直接操作のほうが適しています。

### 6. 承認（ローカル）

```bash
# APPROVAL.md を編集して Gate を承認
# エディタで specs/<feature_name>/APPROVAL.md を開き、チェックボックスを [x] に変更
```

### 7. push

```bash
git add -A
git commit -m "fix: <修正内容>"
git push origin symphony/<feature_name>-<issue番号>
```

## よくあるケース

### AI の生成内容に誤りがあった場合

1. ブランチを checkout
2. Claude Code で修正を指示
3. 修正内容を commit & push
4. レビューして問題なければ APPROVAL.md で承認

**Symphony を再実行する必要はありません。**

### 仕様書 YAML 自体に誤りがあった場合

1. `docs/yaml/` 内のソース YAML を修正
2. main にマージ
3. 新しい Issue を作成して Symphony を再実行

### 次の Phase に進みたい場合

1. 前の Phase の Gate が全て承認済みであることを確認
2. 次の Phase のテンプレートで Issue を作成
3. Symphony を実行
