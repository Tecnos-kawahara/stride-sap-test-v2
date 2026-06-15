# ID 規約

> **対象**: 設計者 / 実装者 / レビュー担当
> **所要時間**: 12分
> **前提**: [14_artifact_reference.md](14_artifact_reference.md) を読んでいること
> **In scope**: よく使う ID 種別と読み方、命名で迷いやすい点
> **Out of scope**: 正規表現レベルの完全仕様

---

## このページの位置づけ

ID 規約の詳細正本は設定ファイルと既存付録にあります。  
このページでは、日常的によく使う ID を人間が読みやすい形で整理します。

詳細参照:

- `sdd-templates/config/id_conventions.yaml`
- `manual/appendix_a_id_conventions.md`

---

## よく使う ID

| ID | 意味 |
|---|---|
| `FEAT-*` | Feature |
| `EPIC-*` | Epic |
| `US-*` | ユースケース |
| `AC-*` | 受入条件 |
| `CT-*` | 契約 |
| `TS-*` | テスト |
| `WI-*` | Work Item |
| `BPMN-*` | BPMN 要素 |

---

## 命名の基本

### 1. 省略しすぎない

短すぎる ID は、後から見たときに意味がわかりにくくなります。

### 2. 同じ粒度は同じ規則で揃える

Feature だけ別流儀、テストだけ別流儀、という状態を避けます。

### 3. 手で意味を足しすぎない

ID は説明文ではありません。  
読みやすい短い規則と、本文側の説明を組み合わせます。

---

## 迷いやすい点

### AC と TS の関係

AC は「満たすべき条件」、TS は「どう確かめるか」です。  
1 対 1 とは限りませんが、つながりが追える状態が重要です。

### Epic と Feature の関係

Epic は上位単位、Feature は実行単位です。  
Epic に実装詳細を持たせすぎると、責務が混ざります。

---

## 次に読むべきもの

- 14 原則を見る: [16_fourteen_articles.md](16_fourteen_articles.md)
- 成果物の意味へ戻る: [14_artifact_reference.md](14_artifact_reference.md)
- 詳細版を見る: `manual/appendix_a_id_conventions.md`
