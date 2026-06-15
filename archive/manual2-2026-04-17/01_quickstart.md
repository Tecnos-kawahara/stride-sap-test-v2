# クイックスタート

> **対象**: PM / 設計者 / 実行者
> **所要時間**: 10分
> **前提**: [index.md](index.md) を開いていること
> **In scope**: 最短でプロジェクトと最初の feature を立ち上げる流れ、各 Gate で何を見るか
> **Out of scope**: 各成果物の詳細な書き方、全 CLI オプション、Enterprise の細かな運用

---

## 30 秒で理解する Tecnos-STRIDE

Tecnos-STRIDE は、**要件を仕様に落とし、その仕様を AI が実行し、人間が節目で承認する開発方法**です。

```text
要件を伝える
  ↓
AI が成果物を作る
  ↓
人間が Gate で確認・承認する
  ↓
AI が次工程を進める
  ↓
実装・テスト・証跡を揃えて完了する
```

> **注: Gate**  
> Gate は「次へ進んでよいか」を判定する確認ポイントです。  
> 書類の承認欄ではなく、品質の境目です。

---

## 最短フロー

### Step 1. プロジェクトを作る

新規プロジェクトなら、まずテンプレートから土台を作ります。

```bash
sdd-templates/bin/stride new-project my_project --first-feature order_entry
```

既存プロジェクトに後から導入する場合は、feature 単位で始めても構いません。

```bash
sdd-templates/bin/stride intake order_entry
```

`intake` は、最初に簡易ヒアリング用のファイルを作るコマンドです。  
いきなりすべてのテンプレートを埋めるより、業務の意図を整理しやすいのが利点です。

### Step 2. 最初の feature を作る

推奨は `intake` から始める方法です。

```bash
sdd-templates/bin/stride intake order_entry
```

ヒアリングを済ませたら、AI に「この intake から `basic_design.md` を作ってください」と依頼します。  
フルテンプレートを一括生成したい場合は `init` も使えます。

```bash
sdd-templates/bin/stride init order_entry --detect
```

> **注: `--detect`**  
> 既存の言語や構成を検出して、テンプレートの初期値に反映する補助オプションです。

### Step 3. lint で整合性を確認する

成果物を書いたら、まず `stride lint` で確認します。

```bash
sdd-templates/bin/stride lint specs/order_entry/
```

`lint` はファイルを自動修正しません。  
問題点と、次に何をすべきかのヒントを返す**読み取り専用の検証**です。

### Step 4. Gate を承認する

承認は `APPROVAL.md` で行います。  
AI は承認できません。必ず人間が確認して進めます。

見る観点は次の通りです。

| Gate | 主に見ること |
|---|---|
| Gate 1 | 目的、対象範囲、制約が明確か |
| Gate 2 | BPMN や業務フローが実態と合っているか |
| Gate 3 | ユースケースと受入条件が足りているか |
| Gate 4 | テスト戦略、リスク、依存関係が現実的か |
| Gate 5 | タスク分解が粗すぎたり細かすぎたりしないか |
| Final | 実装、テスト、証跡、PR 前チェックが揃っているか |

### Step 5. 次に進む

次に何をやればよいか迷ったら、`auto-continue` と `phase-status` を使います。

```bash
sdd-templates/bin/stride phase-status specs/order_entry/
sdd-templates/bin/stride auto-continue specs/order_entry/
```

`phase-status` は現在地の確認、`auto-continue` は次の実行候補の確認に向いています。

### Step 6. PR 前に最終確認する

実装とテストが揃ったら、PR 作成前に `pr-check` を実行します。

```bash
sdd-templates/bin/stride pr-check .
```

---

## 迷ったときの基本原則

### 1. 仕様を先に直す

コードと仕様がずれたときは、先に仕様が正しいかを確認します。  
「コードは動くが仕様が曖昧」という状態は、後で大きな手戻りになりやすいためです。

### 2. 承認なしで次工程へ進めない

特に `spec.md`、`plan.md`、`tasks.md`、実装コードは、前段の承認状態と強く結びつきます。  
急いでいても Gate を飛ばさないでください。

### 3. わからなければ小さく進める

feature を小さめに切り、早めに `lint` と承認を回す方が安全です。

---

## よく使うコマンド

```bash
# 新規プロジェクト
sdd-templates/bin/stride new-project my_project --first-feature order_entry

# 推奨の開始方法
sdd-templates/bin/stride intake order_entry

# フルテンプレート生成
sdd-templates/bin/stride init order_entry --detect

# 検証
sdd-templates/bin/stride lint specs/order_entry/

# 現在地と次の一手
sdd-templates/bin/stride phase-status specs/order_entry/
sdd-templates/bin/stride auto-continue specs/order_entry/

# PR 前チェック
sdd-templates/bin/stride pr-check .
```

> **補足**  
> 正確なコマンド構文は [reference/13_cli_reference.md](reference/13_cli_reference.md) ではなく、最終的には `agent_docs/commands.md` を正本として確認してください。

---

## 役割別の次の読み先

### PM

- [guides/06_pm_guide.md](guides/06_pm_guide.md)
- [guides/11_quality_gates.md](guides/11_quality_gates.md)

### 設計者

- [guides/07_design_phase.md](guides/07_design_phase.md)
- [guides/08_specify_phase.md](guides/08_specify_phase.md)

### 実装者

- [guides/09_execute_phase.md](guides/09_execute_phase.md)
- [guides/10_testing.md](guides/10_testing.md)

---

## 次に読むべきもの

- 背景から理解したい: [concepts/02_sdd_fundamentals.md](concepts/02_sdd_fundamentals.md)
- PM の判断基準を知りたい: [guides/06_pm_guide.md](guides/06_pm_guide.md)
- 実際に設計を書き始めたい: [guides/07_design_phase.md](guides/07_design_phase.md)
