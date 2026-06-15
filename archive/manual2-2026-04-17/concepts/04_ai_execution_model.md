# AI 自律実行モデル

> **対象**: PM / 設計者 / 実行者
> **所要時間**: 15分
> **前提**: [03_phase_gates.md](03_phase_gates.md) を読んでいること
> **In scope**: AI と人間の役割分担、RACI+、Mode、Execution Authority、運用ルール
> **Out of scope**: AI ツールごとの個別設定手順、Hook 実装の詳細

---

## 基本原則

Tecnos-STRIDE の AI 実行モデルは、ひとことで言うと次の通りです。

**AI は実行者、人間は承認者です。**

AI は次のような作業を得意とします。

- テンプレートの下書き作成
- 仕様に沿った実装
- テストの雛形生成
- 整合性確認の反復
- 差分整理や証跡作成の補助

一方で、人間が持つべき役割は次の通りです。

- 優先順位の決定
- 業務妥当性の判断
- 承認と差し戻し
- 例外や逸脱の許容判断

---

## RACI+ で見る役割分担

> **注: RACI**  
> Responsible（実行責任）、Accountable（最終責任）、Consulted（相談先）、Informed（共有先）を整理する考え方です。  
> Tecnos-STRIDE では運用に必要な補助情報も含めて RACI+ と呼んでいます。

簡略化すると、役割分担は次のように考えると理解しやすくなります。

| 役割 | 主な責務 |
|---|---|
| PM | 方向づけ、優先順位、承認、エスカレーション判断 |
| 設計者 / Tech Lead | 仕様妥当性、アーキテクチャ判断、リスク判断 |
| AI | 成果物生成、実装、反復修正、候補提示 |
| QA / レビュー担当 | 品質観点の確認、証跡確認 |

AI に任せる範囲を広げても、最終責任は人間に残ります。

---

## Mode の考え方

Tecnos-STRIDE では、リスクに応じて AI の進み方を変えます。

| Mode | 向いている状況 | 人間の関与 |
|---|---|---|
| `autopilot` | 低リスクで明確な作業 | 事後確認中心 |
| `confirm` | 中程度のリスク、判断ポイントあり | 要所で確認 |
| `validate` | 高リスク、監査・権限・ERP 連携あり | 厳密なレビュー |

この Mode は気分で選ぶものではなく、`risk_flags` や案件特性に応じて決まります。

> **注: `risk_flags`**  
> リスクを表すフラグです。  
> たとえば権限、外部連携、ERP、セキュリティ影響などが含まれます。

---

## Execution Authority

AI にどこまで実行権限を与えるかは、さらに細かく分けて考えます。

| レベル | 意味 |
|---|---|
| `conversational` | 提案中心。人間が明示的に進める |
| `gated` | Gate を守りながら自動実行する |
| `prohibited` | 実行禁止。人間判断が必須 |

この考え方があることで、「AI に全部任せるか、全部止めるか」の二択になりません。

---

## Auto-Continue の役割

`auto-continue` は、現在の承認状態から見て**次に進める作業の並び**を返す補助機能です。

```bash
sdd-templates/bin/stride auto-continue specs/<feature>/
```

これにより、AI や人間が「どこから再開すべきか」で迷いにくくなります。  
ただし、承認が必要な場所は必ず止まります。

つまり、Auto-Continue は「勝手に全部進める機能」ではなく、**止まるべき場所を守りながら流れを整理する機能**です。

---

## Mandatory Output Rules

AI を実務で使うときは、内容だけでなく**出力のしかた**も重要です。  
Tecnos-STRIDE では、必要に応じて出力ルールを明示できます。

```bash
sdd-templates/bin/stride output-rules
```

これは、報告の粒度や PASS / FAIL / WARN の出し方を揃え、レビューしやすくするための仕組みです。

---

## Completeness Principle

Tecnos-STRIDE では、「だいたい動く」で終わらせない姿勢を重視します。  
この考え方を Completeness Principle と呼びます。

意味はシンプルです。

- 受入条件を読んでいないのに完了としない
- テスト戦略を見ずに「大丈夫そう」と言わない
- 証跡が足りないのに Final としない

AI を使うほど作業速度は上がりますが、**完了判定の基準を甘くしない**ことが重要です。

---

## ありがちな誤解

### AI が全部判断してくれるわけではない

AI は候補や実装案を出せますが、業務上の妥当性や責任の所在までは肩代わりできません。

### 承認者が細部を全部書く必要はない

承認者の役割は、成果物を最初から最後まで自分で作ることではありません。  
「何を確認して、どこで止めるか」を押さえることが重要です。

### 自動化が増えるほど、ルールはむしろ必要になる

自由に実行できるからこそ、どこまで進めてよいかを先に決めておく必要があります。

---

## 関連コマンド

```bash
# Gate 状態
sdd-templates/bin/stride phase-status specs/<feature>/

# 次の一手
sdd-templates/bin/stride auto-continue specs/<feature>/

# 出力ルール
sdd-templates/bin/stride output-rules

# Hooks の設定
sdd-templates/bin/stride hooks --tool claude
```

---

## 次に読むべきもの

- Enterprise での拡張を知る: [05_enterprise_scale.md](05_enterprise_scale.md)
- PM の実務へ進む: [../guides/06_pm_guide.md](../guides/06_pm_guide.md)
- 実行フェーズを知る: [../guides/09_execute_phase.md](../guides/09_execute_phase.md)
