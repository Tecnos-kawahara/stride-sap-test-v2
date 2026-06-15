# Camunda BPMN作成機能 更新プロンプト Phase 1

対象リポジトリ:
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

このプロンプトは Claude Code 用です。Tecnos-STRIDE の BPMN作成機能について、Camunda 8.8 前提の基礎整備を行ってください。今回は Phase 1 のみ実装してください。目的は「方針・雛形・CLI・lint・サンプル・ガイドの整合回復」です。新機能の拡張より先に、今ある機能を実際に使える状態へ揃えることを優先してください。

最初に現状確認してください。少なくとも次のファイルを読んでください。
- `sdd-templates/policies/bpmn_generator_rules.md`
- `sdd-templates/templates/process_bpmn_template.bpmn`
- `sdd-templates/bin/stride`
- `sdd-templates/tools/stride_lint.py`
- `manual/10_bpmn_guide.md`
- `sdd-templates/specs/sample_feature/process.bpmn`
- `specs/FEAT-ERPSAMPLE/process.bpmn`
- `sdd-templates/examples/process_bpmn_example.bpmn`

現状のテンプレートには、少なくとも次の問題がある前提で着手してください。
- `stride init` が `process.bpmn` を生成していない
- `process_bpmn_template.bpmn` が `incoming/outgoing` や XOR 条件の方針と整合していない
- sample / example / guide / lint の基準が揃っていない
- lint が BPMN品質基準の一部しか機械検証していない

実装スコープは次の通りです。

1. `stride init` で `process.bpmn` を必ず生成するようにしてください。
- `sdd-templates/templates/process_bpmn_template.bpmn` を `specs/<feature>/process.bpmn` にコピーする処理を追加
- 他テンプレートと同じ placeholder replacement の対象に含める
- README や実際の挙動が一致する状態にする
- 実装位置は `sdd-templates/bin/stride` の `cmd_init()` 内の既存ファイルコピー群に合わせ、`basic_design.md` や `spec.md` をコピーしているのと同じパターンで追加してください

2. BPMN雛形を Camunda 8.8 の最小実用ベースラインに更新してください。
- `xmlns:xsi` を追加
- `modeler:executionPlatform` と `modeler:executionPlatformVersion` を明示
- StartEvent は `outgoing`、EndEvent は `incoming`、その他の主要 FlowNode は `incoming/outgoing` を持つ
- XOR は default flow か全条件式のどちらかを満たす形にする
- `conditionExpression` は `xsi:type="bpmn:tFormalExpression"` を付ける
- User Task は標準パターンとして `zeebe:userTask`、`formDefinition`、`assignmentDefinition` の例を含める
- Service Task は `zeebe:taskDefinition` を持つ
- BPMNDI は全ての flow node / sequence flow に対応する shape / edge を持つ
- 雛形は「Camunda 8.8 の基本形」として使いやすくし、過度に複雑にしない

3. lint を強化して、雛形と品質基準が一致するようにしてください。
最低限、以下を機械検証してください。
- FlowNode の `incoming/outgoing` 整合
- `serviceTask` の `zeebe:taskDefinition/type`
- XOR の default または `conditionExpression`
- `conditionExpression` の空値チェックと `xsi:type` の妥当性
- `BPMNDiagram/BPMNPlane` だけでなく、全 flow node に `BPMNShape`、全 sequence flow に `BPMNEdge` があること
- `boundaryEvent` の `attachedToRef`
- `timeDuration` の基本形式
- `executionPlatformVersion` は 8.x を許容しつつ、8.8 以外は warning にする現在方針は維持してよい

lint については、「既存チェック済み」と「今回新規追加するチェック」を明確に区別してください。実装前に現状を把握し、最終報告でもどこを強化したか整理してください。

既存チェック済みの例:
- XML parse / definitions root
- zeebe / modeler namespace
- executionPlatform / executionPlatformVersion
- process の isExecutable
- BPMNDiagram / BPMNPlane
- serviceTask の `zeebe:taskDefinition/type`
- message 使用時の message / subscription
- `timeDuration` の基本形式

今回新規追加すべきチェックの例:
- FlowNode の `incoming/outgoing`
- XOR の default または `conditionExpression`
- `conditionExpression` の `xsi:type`
- 全 flow node の `BPMNShape`
- 全 sequence flow の `BPMNEdge`
- `boundaryEvent` の `attachedToRef`

4. サンプルとガイドを実装に同期してください。
- `sdd-templates/specs/sample_feature/process.bpmn` を新ルールに合わせる
- `specs/FEAT-ERPSAMPLE/process.bpmn` も lint が通る形に修正
- `sdd-templates/examples/process_bpmn_example.bpmn` も現在の lint 基準と整合させる
- `manual/10_bpmn_guide.md` を、実際に生成される雛形と lint 挙動に合わせて修正
- 「Agentic Orchestration 対応」をデフォルト品質基準として強く主張しないでください。今回の Phase 1 では、advanced pattern は optional として扱ってください
- lint 強化後に既存 BPMN が fail し、その修正が必要になることは想定内です。これは回帰ではなく、基準と実装を揃えるための意図した変更として扱ってください

5. スコープ外
- Web Modeler API 連携の実装
- Orchestration Cluster API のアプリ統合
- element templates の新規仕組み実装
- agentic orchestration の本格実装
- MCP connector の導入

設計判断の方針です。
- ルール文書と実装が衝突したら、「Camunda 8.8 の最小実用ベースライン」に寄せて整理してください
- 文書だけが先行している高度機能は、削るのではなく optional / advanced として位置づけ直してください
- backward compatibility は意識するが、明らかに壊れた scaffold は修正を優先してください
- unrelated files は触らないでください

作業後は必ず検証してください。
- 一時 feature を作って `stride init` で `process.bpmn` が生成されることを確認
- `python3 sdd-templates/tools/stride_lint.py specs/<temp_feature>` を実行
- `python3 sdd-templates/tools/stride_lint.py specs/FEAT-ERPSAMPLE` を実行
- 必要なら `sdd-templates/specs/sample_feature` も検証
- 何を直し、何をまだ保留にしたかを最後に簡潔にまとめてください

編集時の制約です。
- 既存の unrelated change は戻さない
- `apply_patch` で編集する
- まず調査、その後に短い実装計画を出してから編集する
- 最後に変更ファイル、検証結果、残課題を報告する
