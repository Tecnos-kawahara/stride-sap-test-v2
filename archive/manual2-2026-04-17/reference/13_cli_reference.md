# stride CLI リファレンス

> **対象**: PM / 設計者 / 実装者 / AI と協働する人
> **所要時間**: 20分
> **前提**: [../01_quickstart.md](../01_quickstart.md) を読んでいること
> **In scope**: 現在の主要コマンド、用途、代表例、`stride lint` の出力形式と終了コード、`stride health`、`stride harness-report`
> **Out of scope**: 実装内部の詳細、各補助ツールの全オプション、CI YAML の完成例

---

## 最初に知っておきたいこと

このページは、人間が全体像を掴むためのリファレンスです。  
**正確なコマンド構文の正本は `agent_docs/commands.md` です。**

そのため、日常的にはこのページを使い、細かな構文確認が必要なときだけ `agent_docs/commands.md` に戻る使い方を推奨します。

---

## コマンド早見表

| コマンド | 用途 |
|---|---|
| `stride new-project` | 新規プロジェクトの土台を作る |
| `stride intake` | feature のヒアリングから始める |
| `stride init` | feature のテンプレートを一括生成する |
| `stride lint` | feature 文書の整合性を確認する |
| `stride phase-status` | Gate の現在地を確認する |
| `stride auto-continue` | 次に進める内容を確認する |
| `stride hooks` | AI ツール向けの Gate 連携設定を行う |
| `stride evaluate` | LLM ベースの意味的評価を行う |
| `stride pr-check` | PR 前の総合確認を行う |
| `stride security` | セキュリティ観点を確認する |
| `stride retro` | ふりかえりレポートを作る |
| `stride symphony` | オーケストレーションを扱う |
| `stride epic` | Enterprise の Epic を扱う |
| `stride health` | ランタイムセンサー（デッドコード・カバレッジ減衰）を確認する |
| `stride harness-report` | ハーネス成熟度の 8 制御インベントリを確認する |

---

## 開始系コマンド

### `stride new-project`

新しいリポジトリをテンプレートから立ち上げるときに使います。

```bash
sdd-templates/bin/stride new-project my_project --first-feature order_entry
```

### `stride intake`

推奨の開始方法です。  
簡易ヒアリングから feature を立ち上げたいときに使います。

```bash
sdd-templates/bin/stride intake order_entry
```

### `stride init`

フルテンプレートを一括生成したい場合に使います。

```bash
sdd-templates/bin/stride init order_entry --detect
```

---

## Gate と進行管理

### `stride phase-status`

現在の Gate 状態を確認します。

```bash
sdd-templates/bin/stride phase-status specs/order_entry/
```

### `stride auto-continue`

承認状態を踏まえて、次に進める作業を確認します。

```bash
sdd-templates/bin/stride auto-continue specs/order_entry/
```

### `stride hooks`

AI ツール側へ Gate のルールをつなぐときに使います。

```bash
sdd-templates/bin/stride hooks --tool claude
```

---

## 品質ゲート

### `stride lint`

最も基本となる整合性チェックです。

```bash
sdd-templates/bin/stride lint specs/order_entry/
```

主なオプション:

| オプション | 意味 |
|---|---|
| `-o json` | JSON で出力 |
| `-o ndjson` | 1 feature 1 行の JSON で出力 |
| `--plain` | TSV で出力 |
| `--no-color` | ANSI カラーを無効化 |
| `--warn-only` | エラーがあっても終了コード 0 |
| `--coverage-report` | カバレッジ詳細を表示 |
| `--enterprise` | Enterprise 検証も実行 |

> **注: `--plain` と `-o json/ndjson` は併用できません。**

### `stride evaluate`

```bash
sdd-templates/bin/stride evaluate specs/order_entry/ --phase design
```

### `stride pr-check`

```bash
sdd-templates/bin/stride pr-check .
```

### `stride security`

```bash
sdd-templates/bin/stride security specs/order_entry/ --daily
sdd-templates/bin/stride security specs/order_entry/ --audit
```

### `stride retro`

```bash
sdd-templates/bin/stride retro specs/order_entry/
```

### `stride health`

ランタイムセンサーです。デッドコードとカバレッジ減衰を確認します。

```bash
sdd-templates/bin/stride health specs/order_entry/ --runtime
```

主な確認観点:

- デッドコード（pylint W0611〜W0614）
- カバレッジ減衰（`.coverage_baseline` との比較）

閾値は `.env.local` の `COVERAGE_DECAY_THRESHOLD_PCT`（デフォルト: 5%）で設定できます。

### `stride harness-report`

テストハーネス全体の成熟度を確認します。8 制御を検証し、FULL / gaps レポートを出力します。

```bash
sdd-templates/bin/stride harness-report .
```

---

## `stride lint` の出力形式

| 形式 | 使いどころ |
|---|---|
| text | 人間が端末で読むとき |
| json | プログラムでまとめて扱うとき |
| ndjson | パイプ処理で 1 feature ずつ読みたいとき |
| plain | grep / awk / CI ログ向けの TSV |

---

## `stride lint` の終了コード

| 終了コード | 意味 |
|---|---|
| `0` | 問題なし |
| `1` | lint エラーあり |
| `2` | 引数や使い方の誤り |
| `3` | feature ディレクトリが見つからない |
| `4` | YAML パースエラー |

---

## Enterprise コマンド

Enterprise 機能が有効な場合は、Epic 系コマンドも利用できます。

```bash
sdd-templates/bin/stride epic init EPIC-ORDER
sdd-templates/bin/stride epic validate EPIC-ORDER
sdd-templates/bin/stride epic gates EPIC-ORDER
sdd-templates/bin/stride epic features EPIC-ORDER
sdd-templates/bin/stride epic progress EPIC-ORDER
sdd-templates/bin/stride epic list
```

> **注**  
> Enterprise が無効な状態では、`stride epic --help` でも有効化案内が表示されます。

---

## Symphony

GitHub Issue からエージェント実行を回す運用では、`symphony` を使います。

```bash
sdd-templates/bin/stride symphony run --once
sdd-templates/bin/stride symphony dispatch --issue 123
sdd-templates/bin/stride symphony status
sdd-templates/bin/stride symphony validate
```

---

## 正本リンク

- コマンド構文の正本: `agent_docs/commands.md`
- CI/CD 詳細: `sdd-templates/docs/CI_CD_INTEGRATION.md`

---

## 次に読むべきもの

- 成果物の意味を引きたい: [14_artifact_reference.md](14_artifact_reference.md)
- エラー対応を見たい: [../appendix/17_troubleshooting.md](../appendix/17_troubleshooting.md)
- 品質ゲートの考え方: [../guides/11_quality_gates.md](../guides/11_quality_gates.md)
