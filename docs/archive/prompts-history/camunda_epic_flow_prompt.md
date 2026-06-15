# Epic Flow BPMN 導入プロンプト

対象リポジトリ:
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

このプロンプトは Claude Code 用です。EPIC 用の BPMN overview artifact `epic_flow.bpmn` を Tecnos-STRIDE に追加してください。

今回の設計方針は明確です。
- FEAT: `specs/<feature>/process.bpmn`
  - 単一 feature の実装フロー
  - 標準は laneSet / executable 寄り
  - 既存の `stride_lint.py` の対象
- EPIC: `epics/<EPIC>/epic_flow.bpmn`
  - 複数 team / feature / external system の関係を表す overview
  - 標準は collaboration + participant(pool)
  - 実行用 BPMN ではなく planning / architecture 用
  - `stride_lint.py` ではなく `epic_validator.py` の軽量検証対象

最初に必ず現状確認してください。少なくとも次のファイルを読んでください。
- `sdd-templates/bin/stride`
- `sdd-templates/tools/epic_validator.py`
- `sdd-templates/templates/epic_design_template.md`
- `epics/EPIC-SAMPLE/epic_design.md`
- `docs/bpmn_collaboration_pool_sample.bpmn`
- `docs/camunda_bpmn_practice_guide.md`
- `manual/10_bpmn_guide.md`
- `agent_docs/sdd_bootstrap.md`
- `agent_docs/sdd_guidelines.md`

実装スコープは次の通りです。

1. EPIC 用 BPMN テンプレートを追加してください
- 新規ファイル: `sdd-templates/templates/epic_flow_template.bpmn`
- ベースは `docs/bpmn_collaboration_pool_sample.bpmn` を参考にしてください
- `docs/bpmn_collaboration_pool_sample.bpmn` は collaboration + pool + 縦レイアウトの DI 構造を参考にしてください。ただし、内部タスクの zeebe 拡張（`taskDefinition`, `userTask`, `formDefinition`, `assignmentDefinition` など）は FEAT 用の属性なので、EPIC テンプレートにはコピーしないでください
- ただし用途は EPIC overview です。feature の executable BPMN と混同しないでください
- collaboration + participant(pool) を使う
- pool は縦型表示とし、`isHorizontal="false"` を使う
- 2〜3 participant の最小サンプルにする
  - 例: Business / Feature Team / External System
- participant 間は `messageFlow` で表現する
- 内部フローは上から下へ流れる縦レイアウトにする
- Camunda Modeler で開ける妥当な XML にする
- これは overview artifact なので、feature の `process.bpmn` のような Zeebe 実行定義を標準では要求しない
  - `zeebe:taskDefinition`
  - `zeebe:userTask`
  - `formDefinition`
  - `assignmentDefinition`
  などはデフォルトテンプレートには入れない
- 内部ノードは generic task / sendTask / receiveTask など、overview に適した表現を優先する
- `BPMNPlane` は collaboration を参照すること
- participant の shape、messageFlow の edge を含めること
- プレースホルダーは最小限にする
  - `EPIC-XXX`
  - `{{Epic Title}}`
  - `{{Participant A Name}}`
  - `{{Participant B Name}}`
  程度でよい
- `process.bpmn` という名前は使わず、必ず `epic_flow.bpmn` としてください

2. `stride epic init` に `epic_flow.bpmn` 生成を追加してください
- `sdd-templates/bin/stride` の epic init 処理に、`epic_flow_template.bpmn` を `epics/<EPIC>/epic_flow.bpmn` へコピーする処理を追加
- 既存の epic init の copied files / placeholder replacement フローに組み込む
- 少なくとも `EPIC-XXX`、`{{EPIC_ID}}`、`{{TEMPLATE_VERSION}}` は既存置換に乗せる
- 日本語プレースホルダーや業務名プレースホルダーは残してよい
- epic init の完了メッセージ / next steps に `epic_flow.bpmn` の編集を追加する

3. `epic_validator.py` に EPIC BPMN 用の軽量検証を追加してください
重要:
- feature BPMN 用の `stride_lint.py` をそのまま使わないこと
- EPIC overview BPMN を executable BPMN と同じルールで縛らないこと
- `epic_validator.py` の `validate()` メソッド内に、`validate_epic_bpmn()` を `validate_feature_breakdown()` の後、`evaluate_gates()` の前で呼ぶようにしてください

追加する検証は次の範囲に留めてください。
- `epic_flow.bpmn` が存在するか
  - backward compatibility のため、既存 epic にファイルがない場合は error ではなく warning にする
- XML として parse できるか
- root が `bpmn:definitions` か
- `bpmn:collaboration` があるか
- participant が最低 2 つあるか
- participant の `processRef` が存在し、参照先 process が定義されているか
- `bpmndi:BPMNDiagram` / `bpmndi:BPMNPlane` があるか
- plane が collaboration を参照しているか
- 各 participant に `BPMNShape` があるか
- 各 `messageFlow` に `BPMNEdge` があるか
- `EPIC-XXX` のような明白な未置換 ID は warning にする
- ただし feature BPMN のようなチェックはしない
  - `isExecutable=true` 必須
  - `zeebe:*` 必須
  - serviceTask の taskDefinition 必須
  - XOR condition 必須
  - incoming/outgoing の厳格網羅
  は不要

4. sample / docs を実装に同期してください
- 新規ファイル: `epics/EPIC-SAMPLE/epic_flow.bpmn`
- `epics/EPIC-SAMPLE/epic_design.md` に `epic_flow.bpmn` 参照を追加
- `sdd-templates/templates/epic_design_template.md` にも `epic_flow.bpmn` を成果物として明記
- `agent_docs/sdd_bootstrap.md` と `agent_docs/sdd_guidelines.md` に次を反映
  - EPIC は `epic_flow.bpmn` を使う
  - FEAT は `process.bpmn` を使う
  - EPIC の BPMN は overview / planning 用
  - FEAT の BPMN は feature gate 対象
- `docs/camunda_bpmn_practice_guide.md` または `manual/10_bpmn_guide.md` のどちらか適切な方に、EPIC vs FEAT の使い分けを追記してください
- 既存の feature BPMN ガイドの意味を壊さないこと

5. スコープ外
- FEAT の `process.bpmn` を collaboration/pool に置き換えること
- `stride_lint.py` を collaboration 対応へ全面改修すること
- EPIC BPMN を deploy 前提の executable BPMN にすること
- Web Modeler API 連携
- Camunda SaaS 接続
- MCP / Agentic 機能の追加

設計判断の注意点です。
- EPIC BPMN は「実行用」ではなく「責務境界と連携の可視化」が目的です
- そのため、Camunda 8 executable BPMN の厳格ルールを EPIC に持ち込まないでください
- FEAT と EPIC の BPMN を別種の artifact として扱ってください
- backward compatibility を優先し、既存 epic が validator 追加で一斉に error にならないようにしてください
- 現行 sample / docs / init / validator の整合性を最優先で揃えてください

作業後は必ず検証してください。
- `stride epic init EPIC-TESTFLOW` を実行し、`epics/EPIC-TESTFLOW/epic_flow.bpmn` が生成されることを確認
- `python3 sdd-templates/tools/epic_validator.py validate epics/EPIC-TESTFLOW` を実行
- `python3 sdd-templates/tools/epic_validator.py validate epics/EPIC-SAMPLE` を実行
- `epic_flow_template.bpmn` と `epics/EPIC-SAMPLE/epic_flow.bpmn` の XML parse を確認
- 何を追加し、何を warning 扱いに留めたかを最後に簡潔にまとめてください

編集時の制約です。
- unrelated files は戻さない
- `apply_patch` で編集する
- まず調査し、その後に短い実装計画を出してから編集する
- 最後に変更ファイル、検証結果、残課題を報告する
