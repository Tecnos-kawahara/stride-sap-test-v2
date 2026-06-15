# 成果物テンプレートリファレンス

> **対象**: 設計者 / 実装者 / レビュー担当
> **所要時間**: 18分
> **前提**: [../guides/07_design_phase.md](../guides/07_design_phase.md) または [../guides/08_specify_phase.md](../guides/08_specify_phase.md) を読んでいること
> **In scope**: 主要成果物の役割、いつ作るか、何を見るか
> **Out of scope**: 全フィールドの完全仕様、テンプレート全文の転載

---

## まず見る表

| 成果物 | 主なフェーズ | 役割 |
|---|---|---|
| `basic_design.md` | Design | 背景、目的、対象範囲、制約 |
| `process.bpmn` | Design | 業務フロー、判断点、連携の流れ |
| `epic_design.md` | Enterprise Design | Epic 全体の目的、体制、マイルストーン |
| `epic_flow.bpmn` | Enterprise Design | チーム間・システム間の受け渡しの俯瞰 |
| `feature_breakdown.md` | Enterprise Design | Epic をどの Feature に分けるか |
| `spec.md` | Specify | ユースケース、受入条件、機能要件 |
| `plan.md` | Specify | テスト戦略、リスク、依存関係 |
| `tasks.md` | Tasking | 実行単位への分解 |
| `APPROVAL.md` | 全体 | Gate 承認の記録 |
| `evidence_pack.md` | Execute / Final | 完了判断の根拠 |
| `contracts/*` | Specify | API、DB、イベントなどの契約 |

---

## `basic_design.md`

### 役割

- なぜ作るのか
- 何を対象にするのか
- どんな制約があるのか

### こんなときに見る

- feature の目的を確認したい
- 対象外範囲を確認したい
- 業務上の前提条件を確認したい

---

## `process.bpmn`

### 役割

- 業務や処理の流れを図で表す
- 誰が、どこで、どう判断するかを見えるようにする

### こんなときに見る

- 業務フローの認識合わせをしたい
- 外部連携や例外処理の位置を確認したい

---

## `epic_design.md`

### 役割

- Epic 全体の目的、対象、体制を整理する
- チーム構成やマイルストーンを共有する

### こんなときに見る

- Epic が何のためにあるか確認したい
- どのチームがどう関わるか見たい

---

## `epic_flow.bpmn`

### 役割

- チーム間・システム間の受け渡しを俯瞰する
- Feature 個別図に入れすぎたくない横断フローを整理する

### こんなときに見る

- Enterprise 案件の全体像を確認したい
- どの participant 間に依存や受け渡しがあるか見たい

> **補足**  
> `epic_flow.bpmn` は `process.bpmn` の上位版ではなく、役割が違う別の図です。  
> Feature の実装詳細は `process.bpmn`、Epic の横断概観は `epic_flow.bpmn` で持ち分けます。
> 作図ルールの詳細は、この辞書ページでは扱いません。

---

## `feature_breakdown.md`

### 役割

- Epic を複数 Feature へ分ける
- team_id、priority、dependency を整理する

### こんなときに見る

- 実装単位への切り分けを確認したい
- Feature 間依存を俯瞰したい

---

## `spec.md`

### 役割

- ユースケースと受入条件を定義する
- 機能として何を満たすべきかを明確にする

### こんなときに見る

- 完了条件を確認したい
- 異常系の扱いを確認したい
- セキュリティ要件の有無を確認したい

---

## `plan.md`

### 役割

- テスト戦略を定める
- リスク、依存関係、実装上の注意点を整理する

### こんなときに見る

- どんなテストが必要か確認したい
- 依存関係や前提条件を把握したい

---

## `tasks.md`

### 役割

- 実装を Work Item 単位に分解する
- 進める順序やリスクを見えるようにする

### こんなときに見る

- 着手順を確認したい
- テストや証跡タスクが入っているか見たい

---

## `APPROVAL.md`

### 役割

- Gate 承認の記録
- 次工程へ進めるかどうかの状態管理

### 重要な注意

- AI は編集しません
- 人間が確認して記入します

---

## `evidence_pack.md`

### 役割

- 実装と検証の結果をまとめる
- 完了判断の根拠を残す

### こんな内容が入る

- テスト結果
- 監査やセキュリティ結果
- 必要なログやレポート
- AI 実行の履歴情報

---

## `contracts/*`

### 代表例

- `openapi.yaml`
- `database_schema.yaml`
- イベントスキーマ
- ファイル契約

### 役割

- システム間の約束事を明示する
- Contract Test の基準になる

---

## `database_schema.yaml`

### 役割

- DB を使う feature のデータ契約を定義する
- テーブル、カラム、制約、説明を機械可読に残す

### こんなときに見る

- テーブル設計の前提を確認したい
- DB 変更が仕様として明文化されているか見たい
- テストや監査の観点でデータ構造を確認したい

### 合わせて見るもの

- `basic_design.md` の `database` セクション
- 必要に応じて migration や ORM schema

> **補足**  
> DB 案件では、`database_schema.yaml` だけを見れば十分、というわけではありません。  
> 何を設計の正本とし、何を配備の正本とするかは `basic_design.database` の `ssot_model`、`design_ssot`、`deployment_ssot` と合わせて見ます。
> ただし、このページは成果物の辞書です。DB ライフサイクル全体の運用ルールまでは扱いません。

---

## 補助成果物

案件によっては、次のような補助成果物も使います。

- `constitution.md`
- `artifact_registry.md`
- `walkthrough.md`
- `test_results.md`
- `lessons.md`
- `tests/scenarios.yaml`
- `implementation-details/ops.md`

これらは feature の状況に応じて使い分けます。

---

## 次に読むべきもの

- CLI の使い方: [13_cli_reference.md](13_cli_reference.md)
- ID の意味を引く: [15_id_conventions.md](15_id_conventions.md)
- 実務の流れを見る: [../appendix/19_tutorial_web_edi.md](../appendix/19_tutorial_web_edi.md)
