# Camunda BPMN作成機能 更新マスタープロンプト

対象リポジトリ:
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

このプロンプトは Claude Code 用です。Tecnos-STRIDE の BPMN作成機能を Camunda 8.8 前提で段階的にアップデートしてください。目的は、まず基礎整備を完了し、その後に Camunda 8.8 の拡張機能を安全に導入することです。

重要:
- 必ず Phase 1 → Phase 2 の順で進めてください
- Phase 1 が完了して検証も通るまで Phase 2 に進まないでください
- advanced / optional なものを default template に混ぜ込まないでください
- unrelated files は触らないでください

最初に現状確認してください。少なくとも次のファイルを読んでください。
- `sdd-templates/policies/bpmn_generator_rules.md`
- `sdd-templates/policies/camunda_8_bpmn_llm_dictionary.json`
- `sdd-templates/templates/process_bpmn_template.bpmn`
- `sdd-templates/bin/stride`
- `sdd-templates/tools/stride_lint.py`
- `manual/10_bpmn_guide.md`
- `sdd-templates/specs/sample_feature/process.bpmn`
- `specs/FEAT-ERPSAMPLE/process.bpmn`
- `sdd-templates/examples/process_bpmn_example.bpmn`
- `agent_docs/sdd_bootstrap.md`
- `README.md`

参考として、次の既存プロンプトも確認してください。
- `docs/camunda_bpmn_phase1_prompt.md`
- `docs/camunda_bpmn_phase2_prompt.md`

現状の前提問題として、少なくとも以下を把握した上で進めてください。
- `stride init` が `process.bpmn` を生成していない
- BPMN雛形・sample・guide・lint が相互に整合していない
- lint 強化後は既存 BPMN が fail し、サンプルや既存 fixture の修正が必要になる可能性がある
- これは今回の作業では想定内であり、品質基準の引き上げに伴う意図した変更として扱ってよい

最初に短い調査結果を整理し、その後に実装計画を提示してから編集してください。

---

## 実行順

1. 現状調査
2. Phase 1 実装
3. Phase 1 検証
4. Phase 1 完了条件を満たした場合のみ Phase 2 実装
5. Phase 2 検証
6. 最終報告

---

## Phase 1: 基礎整備

目的:
「方針・雛形・CLI・lint・サンプル・ガイドの整合回復」を行い、Tecnos-STRIDE の BPMN作成機能を Camunda 8.8 の最小実用ベースラインで実際に使える状態へ揃えてください。

### Phase 1 の実装スコープ

1. `stride init` で `process.bpmn` を必ず生成するようにしてください。
- `sdd-templates/templates/process_bpmn_template.bpmn` を `specs/<feature>/process.bpmn` にコピーする処理を追加
- 他テンプレートと同じ placeholder replacement の対象に含める
- README や実際の挙動が一致する状態にする
- 実装位置は `sdd-templates/bin/stride` の `cmd_init()` 内で、既存テンプレートのコピー処理に合わせて追加してください

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

lint 強化では、「既存チェック済み」と「今回新規追加するチェック」を区別して扱ってください。実装前に現状を把握し、最終報告でも分けて整理してください。

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
- 「Agentic Orchestration 対応」をデフォルト品質基準として強く主張しないでください。Phase 1 では advanced pattern は optional として扱ってください

### Phase 1 のスコープ外
- Web Modeler API 連携の実装
- Orchestration Cluster API のアプリ統合
- element templates の新規仕組み実装
- agentic orchestration の本格実装
- MCP connector の導入

### Phase 1 の設計方針
- ルール文書と実装が衝突したら、「Camunda 8.8 の最小実用ベースライン」に寄せて整理してください
- 文書だけが先行している高度機能は、削るのではなく optional / advanced として位置づけ直してください
- backward compatibility は意識するが、明らかに壊れた scaffold は修正を優先してください

### Phase 1 の完了条件
- `stride init` で `process.bpmn` が生成される
- 新規雛形が lint を通る
- `specs/FEAT-ERPSAMPLE` が lint を通る
- sample / example / guide / CLI / lint の内容が整合している

### Phase 1 の必須検証
- 一時 feature を作って `stride init` で `process.bpmn` が生成されることを確認
- `python3 sdd-templates/tools/stride_lint.py specs/<temp_feature>` を実行
- `python3 sdd-templates/tools/stride_lint.py specs/FEAT-ERPSAMPLE` を実行
- 必要なら `python3 sdd-templates/tools/stride_lint.py sdd-templates/specs/sample_feature` も実行

Phase 1 が終わったら、何を直したか、何を optional 扱いにしたか、Phase 2 に進める理由を短く整理してから次に進んでください。

---

## Phase 2: Camunda 8.8 拡張活用

前提:
Phase 1 の完了条件を満たした場合のみ実施してください。

目的:
Camunda 8.8 の最新機能を「テンプレートで安全に再利用できる形」に落とし込み、BPMN作成体験の再現性と品質を引き上げてください。

### Phase 2 の実装スコープ

Phase 2 に入る前に、対象を次の 3 区分で選別してください。

- 今回採用するもの
  - 外部 API 連携パターン（`serviceTask` / `zeebe:taskDefinition` / `ioMapping`）
  - `CallActivity` / `BusinessRuleTask` の標準サンプル
  - `task testing` / `FEEL Playground` の利用導線
  - Element Templates の文書化
  - Managed User Task の基本パターン
- 条件付きで限定採用するもの
  - Play / test scenario files
  - `adHocSubProcess` の基本紹介
- 今回は採用しないもの
  - `candidateGroups` を標準承認キューの前提にすること
  - `tests/scenarios.yaml` と Play の scenario files を直結させること
  - 独自表現の job-worker controlled ad-hoc sub-process 例
  - `fromAi()` / MCP Client connector / Vector DB / AI Agent connector の導入 guidance

1. Web Modeler / Camunda 8.8 の実践機能を、採用対象だけテンプレート側の標準パターンに落としてください。
対象は次の 3 領域です。
- element templates の活用前提を明文化
- task testing / FEEL Playground の導線を文書化
- managed user task を前提にした承認・HITLパターンを強化

Play / test scenario files は optional advanced guidance として扱ってください。`tests/scenarios.yaml` と同一視しないでください。

element templates については、今回はコード実装を要求していません。文書化と利用方針の整理に留めてください。

2. BPMN標準パターンを追加してください。
最低限、次の再利用パターンを文書またはサンプルとして追加してください。
- 標準 User Task 承認パターン
  - `zeebe:userTask`
  - `formDefinition`
  - `assignmentDefinition`
  - `taskSchedule`
  - `priorityDefinition`
  - ただし標準例では `candidateGroups` を「そのまま推奨の承認キュー」として扱わない
  - `assignee` ベースまたは「assignment は authorization 設計とセットで決める」と明記する
- タイマー付き承認パターン
  - boundary timer
  - overdue / reminder を想定した構造
- 外部API呼び出しパターン
  - `serviceTask`
  - `zeebe:taskDefinition`
  - `ioMapping`
- Call Activity / Business Rule Task の推奨パターン
  - 再利用プロセス
  - DMN 呼び出し

3. optional advanced pattern は「安全に紹介できるものだけ」を追加してください。
ただし、デフォルト雛形には入れないでください。別サンプルまたは別セクションで追加してください。
- `adHocSubProcess` の基本例
  - 公式 docs に沿った XML にしてください
  - `completionCondition` を書く場合は FEEL / formal expression の整合を守ってください
- Play / test scenario files の紹介
  - Web Modeler 固有の JSON 資産であることを明記
  - `tests/scenarios.yaml` とは別物だと明記

次は今回は見送ってください。
- 独自表現の job-worker controlled ad-hoc sub-process 例
- `fromAi()` を使う tool parameter 例の標準化
- MCP Client connector の導入 guidance
- Vector DB / AI Agent connector の導入 guidance

4. 文書とサンプルを追加・更新してください。
少なくとも次のどちらか、できれば両方を実施してください。
- `manual/10_bpmn_guide.md` に Phase 2 の実践セクションを追加
- `docs/` 配下に Camunda 8.8 実践ガイドを追加

含めるべき内容:
- Web Modeler での task testing の使い分け
- Play / test scenario files の位置づけ
  - ただし `tests/scenarios.yaml` とは別資産だと明記
- FEEL Playground を使った条件式検証
- element templates を使って承認タスクや ERP連携タスクを標準化する方針
- managed user task では `candidateGroups` を標準前提にしない方針
- TypeScript SDK / Orchestration Cluster API は BPMN作成後のアプリ統合レイヤで使うものだと整理
- deprecated な Tasklist API / Operate API / 旧 REST API に新規依存しない方針を明記
- experimental / early-access 機能は「今すぐ採用しない」と明記

5. サンプル資産を追加してください。
以下のいずれかを追加してください。
- `sdd-templates/examples/` に `process_bpmn_advanced_example.bpmn`
- または `sdd-templates/specs/sample_feature/` に advanced sample を追加

このサンプルには次を含めてください。
- 承認 User Task
- timer boundary
- businessRuleTask または callActivity
- optional advanced として ad-hoc の基本例

このサンプルには今回は含めないでください。
- `fromAi()`
- MCP Client connector
- Vector DB / AI Agent connector

6. README / bootstrap の表現を現実に合わせて調整してください。
- `Agentic Orchestration 対応` を default requirement のように扱いすぎている箇所があれば、standard / advanced の段階を明示
- Phase 1 の基本品質と Phase 2 の拡張品質を区別
- ユーザーが「まず何を使えばよいか」が分かるようにする

### Phase 2 のスコープ外
- 実際の Camunda SaaS 接続
- Web Modeler API を呼ぶ自動化コード
- element template JSON 生成のフル実装
- 本番向け Orchestration Cluster API クライアント実装
- Optimize / Administration API の実装

### Phase 2 の設計方針
- Phase 2 は「高度機能の強制」ではなく「安全な導入ガイド化」を重視してください
- advanced pattern は default template に混ぜ込まず、別サンプル・別節で分離してください
- Camunda 8.8 の新機能は、テンプレート利用者が誤解しないように maturity を明記してください
- experimental / alpha / early-access のものは必ず明記し、今回の標準採用対象からは外してください
- Web Modeler 固有資産と、Tecnos-STRIDE 側の `tests/scenarios.yaml` は混同しないでください
- 公式 docs と異なる独自 XML パターンを新たに標準化しないでください

### Phase 2 の完了条件
- advanced sample または advanced guide が追加されている
- 標準パターンと advanced pattern の境界が文書上で明確
- README / bootstrap / guide の表現が「default」と「advanced」で整理されている

### Phase 2 の必須検証
- 追加した BPMN サンプルに対して `python3 sdd-templates/tools/stride_lint.py` が通るか確認
- guide / docs / README の参照整合を確認
- 何を採用し、何を条件付き採用にし、何を今回見送ったかを最後に整理

---

## 最終報告

最後は次の形式で簡潔に報告してください。
- 変更ファイル
- Phase 1 の実装内容
- Phase 1 の検証結果
- Phase 2 の実装内容
- Phase 2 の検証結果
- default と advanced の切り分け
- 採用 / 条件付き採用 / 見送りの整理
- 今回見送ったもの

---

## 編集時の制約

- 既存の unrelated change は戻さない
- `apply_patch` で編集する
- まず調査、その後に短い実装計画を出してから編集する
- 各 Phase に入る前に何をやるか短く宣言する
- 検証せずに完了扱いしない
