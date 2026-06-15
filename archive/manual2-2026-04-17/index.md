# Tecnos-STRIDE マニュアル

> **対象**: PM / 設計者 / 実行者（AI と人間）
> **所要時間**: 5分
> **前提**: なし
> **In scope**: このマニュアル全体の読み方、読者別の入口、構成の全体像
> **Out of scope**: 個別コマンドの全オプション、成果物の全フィールド仕様、CI 実装詳細

---

## このマニュアルについて

Tecnos-STRIDE は、**仕様を中心に据えて AI と人間が協働するための開発テンプレート**です。  
このマニュアルは、テンプレートの思想を説明するだけではなく、実際にどう使えば安全に前へ進めるかを、人間が読みやすい形で整理したものです。

最初に覚えてほしい要点は 3 つです。

1. **仕様が正本です**  
   コードを書く前に、何を作るのかを成果物として明文化します。
2. **AI は実行者、人間は承認者です**  
   AI が多くの作業を進めても、最終判断は人間が担います。
3. **ゲートで品質を止めます**  
   各フェーズの区切りで確認し、抜け漏れを次工程へ持ち込みません。

> **注: SSoT**  
> Single Source of Truth の略です。  
> 「正本はどこか」を明確にし、同じ情報が複数の場所で食い違う状態を防ぐ考え方です。

---

## 最初に読むページ

### PM の方へ

- まずは [01_quickstart.md](01_quickstart.md) を読んで全体像を掴んでください。
- 日々の見方と承認の判断基準は [guides/06_pm_guide.md](guides/06_pm_guide.md) にまとめています。
- 品質の見方は [guides/11_quality_gates.md](guides/11_quality_gates.md) を参照してください。

### 設計者の方へ

- はじめに [01_quickstart.md](01_quickstart.md)
- その後、[guides/07_design_phase.md](guides/07_design_phase.md) と [guides/08_specify_phase.md](guides/08_specify_phase.md)
- 成果物の辞書的な参照は [reference/14_artifact_reference.md](reference/14_artifact_reference.md)

### 実装者・AI エージェントと協働する方へ

- はじめに [01_quickstart.md](01_quickstart.md)
- 実行の流れは [guides/09_execute_phase.md](guides/09_execute_phase.md)
- テストは [guides/10_testing.md](guides/10_testing.md)
- コマンド一覧は [reference/13_cli_reference.md](reference/13_cli_reference.md)

---

## Tecnos-STRIDE の全体像

```text
要件を伝える
  ↓
Design（基本設計・業務フロー）
  ↓ Gate 1, 2
Specify（仕様・計画・契約）
  ↓ Gate 3, 4
Tasking / Execute（タスク化・実装・検証）
  ↓ Gate 5, Final
PR / リリース判断
```

この流れの中で、主に次の成果物を扱います。

| 成果物 | 役割 | ひとことで言うと |
|---|---|---|
| `basic_design.md` | 背景、目的、業務像を定める | なぜ作るか |
| `process.bpmn` | 業務や処理の流れを図で表す | どう流れるか |
| `spec.md` | ユースケースと受入条件を定義する | 何ができればよいか |
| `plan.md` | テスト、リスク、依存関係を整理する | どう検証し、どう進めるか |
| `tasks.md` | 実装を作業単位へ分解する | 誰が何を進めるか |
| `evidence_pack.md` | 実施結果と証跡を残す | 何を確認して完了としたか |

---

## このマニュアルの構成

### 1. クイックスタート

最短で動き出したい方向けの入口です。  
「何から始めればよいか」を 10 分で把握できます。

### 2. Concepts

考え方を理解する章です。  
なぜこのテンプレートがこういう構造なのかを説明します。

### 3. Guides

実務で使うための章です。  
PM、設計、仕様策定、実行、テスト、品質ゲート、移行の進め方を扱います。

### 4. Reference

必要なときに引くための章です。  
CLI、成果物、ID 規約、14 原則を整理しています。

### 5. Appendix

学習用チュートリアル、トラブルシューティング、履歴などを置いています。

---

## 正本の考え方

このリポジトリには複数の文書群があります。迷ったときは次の順で見てください。

| 文書 | 役割 |
|---|---|
| `manual2/` | 人間向けの説明、判断基準、導線 |
| `agent_docs/commands.md` | CLI コマンドと実行例の正本 |
| `sdd-templates/docs/` | 実装者向けの詳細資料 |

> **注: 正本の使い分け**  
> この `manual2/` は「わかりやすく説明する」ことを優先します。  
> 正確なコマンド構文を確認するときは `agent_docs/commands.md` を優先してください。

---

## はじめの一歩

迷ったら、次の順で読み進めてください。

1. [01_quickstart.md](01_quickstart.md)
2. [concepts/02_sdd_fundamentals.md](concepts/02_sdd_fundamentals.md)
3. 自分の役割に合う Guide

---

## 次に読むべきもの

- 最短で始めたい: [01_quickstart.md](01_quickstart.md)
- 背景から理解したい: [concepts/02_sdd_fundamentals.md](concepts/02_sdd_fundamentals.md)
- PM の運用を見たい: [guides/06_pm_guide.md](guides/06_pm_guide.md)
