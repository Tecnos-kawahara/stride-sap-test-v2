# BPMN 業務記述・連動強化プロンプト

対象リポジトリ:
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

このプロンプトは Claude Code 用です。Tecnos-STRIDE の EPIC / FEAT BPMN について、**全ての業務ブロック単位で詳細な業務記述が残る状態**にアップデートしてください。特に FEAT の `process.bpmn` は `basic_design.md` と同時に作成されるため、**Basic Design の正本情報と BPMN 側の業務説明が連動すること**を重視してください。

今回の目的は「図を描ける」ことではなく、**BPMN の各ブロックが何の業務責務を持ち、何を入力し、何を出力し、どの AC / Contract / integration flow と結びつくかが、機械可読かつ人間にも読める形で残ること**です。

前提:
- `docs/camunda_epic_flow_prompt.md` の実装が完了し、`sdd-templates/templates/epic_flow_template.bpmn` と `epics/EPIC-SAMPLE/epic_flow.bpmn` が存在する状態で実行してください
- もし上記ファイルが未作成なら、このプロンプトの実装より先に EPIC Flow BPMN 導入を完了してください

重要な方針:
- 業務説明の正本は `bpmn:documentation` に寄せてください
- `bpmn:textAnnotation` は図上で見せたい補足に限定してください
- XML コメントは補助的に残してよいですが、業務説明の正本にしないでください
- FEAT は `basic_design.md` の Canonical YAML と `process.bpmn` が相互に追跡可能であること
- EPIC は `epic_design.md` の設計情報と `epic_flow.bpmn` が相互に追跡可能であること

最初に現状確認してください。少なくとも次のファイルを読んでください。
- `sdd-templates/templates/basic_design_template.md`
- `specs/FEAT-ERPSAMPLE/basic_design.md`
- `sdd-templates/templates/process_bpmn_template.bpmn`
- `specs/FEAT-ERPSAMPLE/process.bpmn`
- `sdd-templates/templates/epic_design_template.md`
- `epics/EPIC-SAMPLE/epic_design.md`
- `sdd-templates/templates/epic_flow_template.bpmn`
- `epics/EPIC-SAMPLE/epic_flow.bpmn`
- `manual/10_bpmn_guide.md`
- `docs/camunda_bpmn_practice_guide.md`
- `sdd-templates/tools/stride_lint.py`
- `sdd-templates/tools/epic_validator.py`
- `sdd-templates/policies/bpmn_generator_rules.md`

最初に短い調査結果を整理し、その後に実装計画を提示してから編集してください。

---

## 目的

1. FEAT BPMN の各業務ブロックに、詳細な業務記述を持たせる
2. その内容が `basic_design.md` の Canonical YAML と連動するようにする
3. EPIC BPMN にも participant / message flow / overview レベルの説明を持たせる
4. `documentation` と `textAnnotation` の使い分けを標準化する
5. lint / validator / guide / sample / template を整合させる

---

## 設計方針

### 1. 説明の正本

業務説明の正本は次の順で扱ってください。

- 第1正本: `basic_design.md` / `epic_design.md` の Canonical YAML
- 第2正本: BPMN 要素の `bpmn:documentation`
- 補足表示: `bpmn:textAnnotation`
- 非正本: XML コメント

### 2. `documentation` と `textAnnotation` の使い分け

- `bpmn:documentation`
  - 正本
  - 要素に紐づく説明
  - AI / lint / 将来の自動変換で利用しやすい
- `bpmn:textAnnotation`
  - 図面上で目立たせたい補足
  - SLA / 契約ID / 閾値 / 注意書き / 境界条件に限定
  - 全タスクにベタ打ちしない
- XML コメント
  - AC / Contract の補助メモとして残してもよい
  - ただし説明の唯一の置き場にしない

### 3. FEAT と EPIC の役割分担

- FEAT BPMN: `specs/<feature>/process.bpmn`
  - executable 寄り
  - task / gateway / sequenceFlow 単位で詳細記述
  - `basic_design.md` と強く連動
- EPIC BPMN: `epics/<EPIC>/epic_flow.bpmn`
  - overview / planning 用
  - collaboration / participant / messageFlow の説明が中心
  - participant 内部 task の説明は簡潔でよい

### 4. `traceability_rows` と新設説明セクションの責務分離

- `traceability_rows` は AC / Contract / Test / Task とのトレーサビリティ正本です
- `integration_flows` は外部連携フローの正本です
- 新設する `bpmn_descriptions` は、**BPMN 要素単位の業務記述正本**です
- そのため、`bpmn_descriptions` には AC ID / Contract ID / integration flow ID を重複保持しないでください
- BPMN 要素と AC / Contract / integration flow の対応は、既存の `traceability_rows` / `integration_flows` を参照して解決してください
- つまり責務は次のように分けてください
  - `traceability_rows`: 何を満たすか、どの契約・テスト・タスクに結びつくか
  - `bpmn_descriptions`: その BPMN 要素が業務上何をするか

---

## 実装スコープ

### 1. FEAT の Canonical YAML に BPMN 記述正本を追加してください

対象:
- `sdd-templates/templates/basic_design_template.md`
- `specs/FEAT-ERPSAMPLE/basic_design.md`

`basic_design` の Canonical YAML に、BPMN 記述用の新しい正本セクションを追加してください。名称は分かりやすければよいですが、例えば `bpmn_descriptions` または `flow_descriptions` のような形を推奨します。

最低限、次の情報を持てる構造にしてください。

- `process`
  - `process_id`
  - `purpose`
  - `start_condition`
  - `end_condition`
  - `business_outcome`
  - `primary_actors`
- `elements`
  - `bpmn_id`
  - `name`
  - `type`
  - `purpose`
  - `business_role`
  - `trigger`
  - `inputs`
  - `outputs`
  - `business_rules`
  - `exceptions`

重要:
- 既存の `traceability_rows`、`integration_flows`、`flow_reference` と矛盾しないこと
- `traceability_rows` は AC / Contract / Test / Task の正本として維持し、`bpmn_descriptions` には業務記述だけを持たせてください
- 既存情報を重複管理するのではなく、**BPMN ブロック説明の正本**として整理してください
- FEAT テンプレートと FEAT sample の両方に入れてください
- `sequenceFlow` の業務意味は、標準では BPMN 側の `bpmn:documentation` に記載してください
- `basic_design.md` の Canonical YAML に `sequence_flows` セクションを標準追加する必要はありません
- 例外として、業務上きわめて重要な分岐条件を YAML にも持たせたい場合だけ optional 扱いにしてください

### 2. FEAT BPMN テンプレートに `documentation` を追加してください

対象:
- `sdd-templates/templates/process_bpmn_template.bpmn`
- `sdd-templates/examples/process_bpmn_example.bpmn`
- `sdd-templates/examples/process_bpmn_advanced_example.bpmn`
- `specs/FEAT-ERPSAMPLE/process.bpmn`

次の要素には `bpmn:documentation` を追加してください。

- `bpmn:process`
- `bpmn:userTask`
- `bpmn:serviceTask`
- `bpmn:exclusiveGateway`
- 条件付き `bpmn:sequenceFlow`
- 必要であれば `boundaryEvent`
- 必要であれば `endEvent`

`documentation` の内容は、最低限次のような情報が入るようにしてください。

- `process`
  - 目的
  - 開始条件
  - 完了条件
  - 参照先 `basic_design.md`
- `task`
  - 目的
  - 主入力
  - 主出力
  - 関連 AC（`traceability_rows` を参照して導出）
  - 関連 Contract（`traceability_rows` を参照して導出）
- `gateway`
  - 判定の業務意味
  - default flow の意味
- `sequenceFlow`
  - 業務条件
  - 条件式の業務意味

テンプレートでは placeholder を追加して構いません。例えば次のような placeholder を使ってください。

- `{{プロセス概要}}`
- `{{開始条件}}`
- `{{完了条件}}`
- `{{業務目的}}`
- `{{主入力}}`
- `{{主出力}}`
- `{{関連AC}}`
- `{{関連Contract}}`
- `{{分岐の業務意味}}`
- `{{条件の業務説明}}`

### 3. EPIC 側にも説明正本を追加してください

対象:
- `sdd-templates/templates/epic_design_template.md`
- `epics/EPIC-SAMPLE/epic_design.md`
- `sdd-templates/templates/epic_flow_template.bpmn`
- `epics/EPIC-SAMPLE/epic_flow.bpmn`

`epic_design.md` の Canonical YAML に、`epic_flow.bpmn` の説明正本を追加してください。名称は分かりやすければよいですが、例えば `epic_flow_descriptions` のような形を推奨します。

最低限、次を持てるようにしてください。

- `overview`
  - `purpose`
  - `scope`
  - `out_of_scope`
- `participants`
  - `participant_id`
  - `name`
  - `role`
  - `responsibility`
  - `owner`
- `message_flows`
  - `message_flow_id`
  - `summary`
  - `payload`
  - `contract_ref`
  - `dependency_ref`
  - `sla`
  - `business_expectation`

`epic_flow.bpmn` には次の `documentation` を入れてください。

- `bpmn:collaboration`
  - epic overview の目的
  - scope / out_of_scope
  - 参照先 `epic_design.md`
- `bpmn:participant`
  - 責務境界
  - owner / team / external system の別
- `bpmn:messageFlow`
  - 受け渡し内容
  - contract / dependency / SLA

### 4. `Text Annotation` の標準運用を定義してください

対象:
- `manual/10_bpmn_guide.md`
- `docs/camunda_bpmn_practice_guide.md`
- sample BPMN

`Text Annotation` は次の用途に限定するようにガイド化してください。

- EPIC:
  - 重要な契約ID
  - blocking dependency
  - SLA / latency
  - out-of-scope 注記
- FEAT:
  - 金額閾値
  - タイムアウト時の扱い
  - 補償や運用上の注意

重要:
- `Text Annotation` を全要素に付ける方針にはしない
- 説明の正本はあくまで `documentation`
- 少なくとも 1 つの EPIC sample と 1 つの FEAT sample に、適切な annotation 例を追加してください

### 5. lint / validator を説明方針に追従させてください

対象:
- `sdd-templates/tools/stride_lint.py`
- `sdd-templates/tools/epic_validator.py`

追加する検証は warning ベースで構いません。Phase 1 の厳格 error とは分けてください。

最低限、次を追加してください。

- FEAT BPMN
  - `bpmn:process` に `documentation` がなければ warning
  - `userTask` / `serviceTask` / `gateway` に `documentation` がなければ warning
  - 条件付き `sequenceFlow` に `documentation` がなければ warning
- EPIC BPMN
  - `collaboration` に `documentation` がなければ warning
  - `participant` に `documentation` がなければ warning
  - `messageFlow` に `documentation` がなければ warning

追加する warning 名は分かりやすくしてください。例えば:

- `BPMN_DOCUMENTATION_MISSING`
- `EPIC_BPMN_DOCUMENTATION_MISSING`

注意:
- 今回は annotation の有無を必須にしないでください
- 既存資産への影響を考え、まずは warning に留めてください

### 6. Basic Design と BPMN の連動ルールを明文化してください

対象:
- `manual/10_bpmn_guide.md`
- `docs/camunda_bpmn_practice_guide.md`
- 必要なら `sdd-templates/policies/bpmn_generator_rules.md`

明文化してほしいポイント:

- `basic_design.md` の `traceability_rows` と BPMN 要素 ID の対応
- `integration_flows` と BPMN の serviceTask / messageFlow の対応
- `bpmn_descriptions` の `bpmn_id` と BPMN XML 要素 ID の一致
- `bpmn_descriptions` は業務記述正本、`traceability_rows` は AC / Contract / Test 正本であること
- `process.bpmn` を更新したら `basic_design.md` の説明正本も同期すること
- EPIC の `epic_flow.bpmn` も `epic_design.md` の説明正本と同期すること

### 7. スコープ外

- BPMN を全文自動生成する新エンジンの実装
- Web Modeler API 連携
- MCP / Agentic 機能の追加
- FEAT の executable BPMN を collaboration へ置き換えること
- EPIC overview BPMN を executable BPMN 化すること

---

## 実装上の注意

- `documentation` は CDATA を使って読みやすくして構いません
- ただし過度に長文化せず、1 要素あたり 4〜8 行程度の構造化記述にしてください
- FEAT の各 task に、少なくとも「目的 / 入力 / 出力 / 関連AC」は残るようにしてください
- EPIC の各 messageFlow に、少なくとも「内容 / contract / dependency or expectation」は残るようにしてください
- placeholder を追加する場合は、lint の placeholder warning 方針と整合させてください
- sample は placeholder を残さず、実際の記述例を入れてください

---

## 検証

作業後は必ず次を実行してください。

- `python3 sdd-templates/tools/stride_lint.py specs/FEAT-ERPSAMPLE`
- `python3 sdd-templates/tools/epic_validator.py validate epics/EPIC-SAMPLE`
- `python3 - <<'PY'` などで以下の XML parse を確認
  - `sdd-templates/templates/process_bpmn_template.bpmn`
  - `sdd-templates/templates/epic_flow_template.bpmn`
  - `specs/FEAT-ERPSAMPLE/process.bpmn`
  - `epics/EPIC-SAMPLE/epic_flow.bpmn`

さらに確認してください。

- `basic_design.md` の新しい正本セクションと BPMN の `documentation` が整合していること
- `traceability_rows` に登場する `bpmn.id` と BPMN 実要素 ID がズレていないこと
- `integration_flows` の説明と BPMN の serviceTask / messageFlow が矛盾しないこと
- guide に `documentation` と `Text Annotation` の使い分けが明記されていること

---

## 最終報告

最後に次を簡潔に報告してください。

- 追加した正本セクション名
- FEAT / EPIC それぞれで `documentation` を追加した要素
- annotation をどこに採用し、どこでは採用しなかったか
- warning として追加した検証
- まだ自動同期していない点や将来改善点

編集時の制約です。
- unrelated files は戻さない
- `apply_patch` で編集する
- まず調査し、その後に短い実装計画を出してから編集する
- 最後に変更ファイル、検証結果、残課題を報告する
