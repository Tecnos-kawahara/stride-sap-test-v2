# 品質ゲート

> **対象**: PM / 設計者 / 実装者 / QA
> **所要時間**: 18分
> **前提**: [10_testing.md](10_testing.md) を読んでいること
> **In scope**: `stride lint`、`evaluate`、`pr-check`、`security`、`retro`、`health`、`harness-report`、CI 連携の考え方
> **Out of scope**: 各コマンドの全オプション、CI ベンダーごとの YAML 実装例

---

## 「テスト」と「品質ゲート」は同じではない

テストは、機能や振る舞いを確かめるものです。  
品質ゲートは、**次へ進めてよいかを判断するために、複数の観点を束ねて確認する仕組み**です。

Tecnos-STRIDE では、主に次のコマンドが品質ゲートの役割を担います。

| コマンド | 主な役割 |
|---|---|
| `stride lint` | 文書・構造・参照整合性の確認 |
| `stride evaluate` | LLM による意味的な穴の確認 |
| `stride pr-check` | PR 前の総合確認（v5.1: `--mutation` で Check 8 追加） |
| `stride security` | セキュリティ観点の確認 |
| `stride retro` | 実施後のふりかえり |
| `stride health` | ランタイムセンサー（デッドコード・カバレッジ減衰） |
| `stride harness-report` | ハーネス成熟度 8 制御インベントリの確認 |

---

## `stride lint`

`lint` は最も基本となる品質ゲートです。  
ファイルの存在、参照整合、承認状態、契約とテストのつながりなどを確認します。

```bash
sdd-templates/bin/stride lint specs/<feature>/
```

このコマンドは読み取り専用です。  
自動修正ではなく、問題点と次の行動を示します。

---

## `stride evaluate`

`evaluate` は、lint が見つけにくい**意味的な違和感**を拾うための補助ゲートです。

```bash
sdd-templates/bin/stride evaluate specs/<feature>/ --phase design
```

たとえば次のような観点に向いています。

- 受入条件はあるが、業務リスクの観点が薄い
- ERP や監査の重要性に対して記述が軽い
- テスト戦略が形式的で、実際の失敗パターンに弱い

> **注: evaluate は lint の代わりではありません**  
> まず lint で機械的整合性を通し、その後に意味的な品質を見る補助として使います。

---

## `stride pr-check`

`pr-check` は、PR を作る前の総合確認です。

```bash
sdd-templates/bin/stride pr-check .
```

PR 作成前に、最低限これだけは見ておきたい、という観点をまとめて確認します。  
最終盤の抜け漏れ防止に有効です。

---

## `stride security`

セキュリティ確認は、最後に一度だけ行えばよいものではありません。  
Tecnos-STRIDE では、軽量な日常確認と、重めの監査確認を分けて扱えます。

```bash
sdd-templates/bin/stride security specs/<feature>/ --daily
sdd-templates/bin/stride security specs/<feature>/ --audit
```

### どう使い分けるか

- `--daily`: Gate 前の日常的な確認
- `--audit`: Final 前の包括確認

---

## `stride retro`

`retro` は、定量ふりかえりの補助です。

```bash
sdd-templates/bin/stride retro specs/<feature>/
```

開発後に「なんとなく大変だった」で終わらせず、どこで詰まり、何を学んだかを残すのに役立ちます。

---

## `stride health`（v5.1.0）

`health` は、実装後も続く**ランタイム品質センサー**です。

```bash
sdd-templates/bin/stride health specs/<feature>/ --runtime
```

次の観点を確認します。

- **デッドコード**: pylint W0611〜W0614 を使って未使用インポート・未使用変数を検出
- **カバレッジ減衰**: `.coverage_baseline` との比較で、カバレッジが減っていないかを確認

> **設定**  
> `.env.local` に `COVERAGE_DECAY_THRESHOLD_PCT=5` と書くと許容する減衰率（%）を変えられます。デフォルトは 5%。

---

## `stride harness-report`（v5.1.0）

`harness-report` は、テストハーネス全体の成熟度を確認するためのコマンドです。

```bash
sdd-templates/bin/stride harness-report .
```

8 つの制御を検証し、FULL（全制御 OK）または gaps（不足している制御）のレポートを出力します。

制御の例:

- pytest + coverage の設定
- ミューテーションテスト（cosmic-ray）の設定
- デッドコードチェック（pylint フック）
- Self-Review Loop の有効化（`--review`）

`pytest -m harness` でハーネス関連テスト 59 件だけを単独実行することもできます。

---

## Living Spec Drift Detection

仕様と実装が離れていく現象を、ここでは Drift と呼びます。  
Tecnos-STRIDE では、lint や補助ツールを通じて、その兆候を早めに見つける考え方を取ります。

典型例:

- 契約が更新されたのに実装が追従していない
- 実装が変わったのに仕様や証跡が古い
- 承認後の変更が十分に説明されていない

---

## CI/CD との関係

品質ゲートは、ローカルで終わるものではありません。  
PR や main ブランチで再確認できるようにしておくと、属人化を減らせます。

ただし、`manual2/` では CI の詳細 YAML までは扱いません。  
実装時は `sdd-templates/docs/CI_CD_INTEGRATION.md` を参照してください。

---

## 実務での使い分け

### 開発中

- `stride lint`
- 必要に応じて `stride evaluate`

### Gate 前

- `stride lint`
- `stride security --daily`

### PR 前 / Final 前

- `stride pr-check`（必要に応じて `--mutation` を追加）
- `stride security --audit`
- 必要に応じて `stride retro`

### 定期的なハーネス確認

- `stride health --runtime`（カバレッジ減衰・デッドコードの継続確認）
- `stride harness-report .`（8 制御インベントリの全体確認）

---

## 次に読むべきもの

- CLI の一覧: [../reference/13_cli_reference.md](../reference/13_cli_reference.md)
- CI 深掘り: `sdd-templates/docs/CI_CD_INTEGRATION.md`
- トラブル対応: [../appendix/17_troubleshooting.md](../appendix/17_troubleshooting.md)
