# トラブルシューティング

> **対象**: PM / 設計者 / 実装者
> **所要時間**: 15分
> **前提**: [../reference/13_cli_reference.md](../reference/13_cli_reference.md) を読んでいること
> **In scope**: よくある lint / Gate / YAML / 参照エラーの初動対応、Harness Maturity（v5.1.0）関連のトラブル対応
> **Out of scope**: すべてのエラーコードの完全説明

---

## 最初に確認すること

エラーが出たときは、まず次の 3 つを切り分けます。

1. **構文の問題か**
2. **承認状態の問題か**
3. **参照や整合性の問題か**

この切り分けを先にすると、無駄な調査が減ります。

---

## `APPROVAL_PENDING`

### 意味

必要な Gate 承認がまだ済んでいません。

### 初動

- `APPROVAL.md` を開く
- 対象 Gate が人間により承認済みか確認する
- `phase-status` で状態を確認する

```bash
sdd-templates/bin/stride phase-status specs/<feature>/
```

---

## `AC_NOT_COVERED`

### 意味

受入条件があるのに、それを担保するテスト戦略が見えていません。

### 初動

- `spec.md` の AC を確認する
- `plan.md` のテスト項目との対応を見る

---

## `REF_NOT_FOUND`

### 意味

参照している ID や要素が見つかりません。

### 初動

- タイプミスがないか
- 古い ID を参照していないか
- ref 先のファイルが最新か

---

## YAML パースエラー

### 起きやすい原因

- インデントずれ
- クォート不足
- コロンを含む文字列の扱い

### 初動

- エラー対象の YAML ブロックを開く
- インデントを揃える
- 必要に応じて値をクォートで囲む

---

## パス指定のミス

最近の `stride lint` は、近いパス候補を提案することがあります。  
ただし、まずは本当に `specs/<feature>/` を指しているかを確認してください。

---

## 承認後変更の扱い

承認後に文書が変わることはあります。  
大切なのは、変更が見えることと、必要なら再承認することです。

「少し直しただけだから黙って進める」は避けてください。

---

## Harness Maturity（v5.1.0）

### `stride health --runtime` でアラートが出る

**意味**: デッドコードまたはカバレッジ減衰が検出されました。

**初動**:

- デッドコードの場合: pylint が報告する W0611〜W0614 の箇所を確認し、不要なインポート・変数を削除する
- カバレッジ減衰の場合: `.coverage_baseline` と現在のカバレッジを比較し、減った原因（テストが消えていないか、新コードにテストが対応しているか）を確認する

閾値を調整する場合は `.env.local` に `COVERAGE_DECAY_THRESHOLD_PCT=10` のように記述します。

---

### `stride harness-report` で gaps が出る

**意味**: 8 制御のうち、不足している制御があります。

**初動**:

- どの制御が gaps になっているか出力を確認する
- `pytest --cov` の設定、`cosmic-ray` のインストール、`post_edit_guard.py` の存在などを確認する
- 段階的に制御を追加して再実行する

---

### `stride pr-check --mutation` が WARN になる

**意味**: `--mutation` が指定されているが、`cosmic-ray` がインストールされていません。

**初動**:

```bash
pip install cosmic-ray
```

インストール後に再実行すると Check 8 が PASS/FAIL として評価されます。

---

### `stride evaluate --review` でスコアが下がる

**意味**: Self-Review Loop が critical issue を検出し、`primary_result` に注入しました。

**初動**:

- 評価レポート（`specs/<feature>/state/evaluator_latest.json`）を開く
- 注入された critical issue の内容を確認する
- 該当する成果物（`basic_design.md`、`spec.md` など）を修正して再実行する

---

## 困ったときに使うコマンド

```bash
sdd-templates/bin/stride lint specs/<feature>/
sdd-templates/bin/stride phase-status specs/<feature>/
sdd-templates/bin/stride auto-continue specs/<feature>/
```

---

## 次に読むべきもの

- CLI 詳細: [../reference/13_cli_reference.md](../reference/13_cli_reference.md)
- 品質ゲート: [../guides/11_quality_gates.md](../guides/11_quality_gates.md)
- 詳細版: `manual/appendix_d_troubleshooting.md`
