# Camunda BPMN作成機能 更新プロンプト Phase 2

対象リポジトリ:
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

このプロンプトは Claude Code 用です。Tecnos-STRIDE の BPMN作成機能について、Camunda 8.8 の拡張活用フェーズを実装してください。今回は Phase 2 です。前提として、Phase 1 の「scaffold / template / lint / sample / guide の整合回復」が完了しているものとして進めてください。

今回の目的は、Camunda 8.8 の最新機能を「テンプレートで安全に再利用できる形」に落とすことです。単なる知識追加ではなく、BPMN作成体験の再現性と品質向上につながる成果物を追加してください。

重要な前提:
- Phase 2 は「何でも最新機能を盛り込む」作業ではありません
- 採用するのは、現行テンプレート利用者が誤解せず再利用できるものだけです
- experimental / early-access / custom runtime 前提のものは、標準導入対象にしないでください
- 公式 docs と現行実装の両方に照らして、安全に採用できるものだけを default / standard guidance に昇格させてください

最初に現状確認してください。少なくとも次のファイルを読んでください。
- `sdd-templates/policies/bpmn_generator_rules.md`
- `sdd-templates/policies/camunda_8_bpmn_llm_dictionary.json`
- `sdd-templates/templates/process_bpmn_template.bpmn`
- `sdd-templates/examples/process_bpmn_example.bpmn`
- `manual/10_bpmn_guide.md`
- `agent_docs/sdd_bootstrap.md`
- `README.md`

加えて、Phase 2 の判断に必要な範囲で以下も確認してください。
- `docs/camunda_bpmn_phase1_prompt.md`
- `sdd-templates/specs/sample_feature/process.bpmn`
- `specs/FEAT-ERPSAMPLE/process.bpmn`

最初に、次の 3 区分で対象を選別してください。

1. 今回採用するもの
- 外部 API 連携パターン
  - `serviceTask`
  - `zeebe:taskDefinition`
  - `ioMapping`
- `CallActivity` / `BusinessRuleTask` の標準サンプル
- `task testing` / `FEEL Playground` の利用導線
- Element Templates の文書化
  - ただし今回は実装ではなく利用方針の明文化のみ
- Managed User Task の基本パターン
  - ただし `candidateGroups` を標準承認キューの前提として扱わない
  - `assignee` / フォーム / 入力変数 / authorization 設計の補足を含める

2. 条件付きで限定採用するもの
- Play / test scenario files
  - `tests/scenarios.yaml` と同一視しない
  - Web Modeler の test scenario files は BPMN `processId` に紐づく JSON ベースの別資産だと明記する
  - 既存の `tests/scenarios.yaml` と将来的にどう関係づけうるかを「将来検討」として整理するのは可
- Ad-hoc SubProcess の基本紹介
  - optional advanced として紹介する
  - default template や標準フローには入れない

3. 今回は採用しない、または研究枠として扱うもの
- `candidateGroups` を標準承認パターンの中心に据えること
- Play のシナリオを `tests/scenarios.yaml` と直結させること
- 独自表現の job-worker controlled ad-hoc sub-process 例
- `fromAi()` を前提にした実運用 guidance
- MCP Client connector の導入 guidance
- Vector DB / AI Agent connector の導入 guidance

実装スコープは次の通りです。

1. Web Modeler / Camunda 8.8 の実践機能を、採用対象だけテンプレート側の標準パターンに落としてください。
対象は次の 3 領域です。
- element templates の活用前提を明文化
- task testing / FEEL Playground の導線を文書化
- managed user task を前提にした承認・HITLパターンを強化

Play / test scenario files は「補助的な高度機能」として扱ってください。`tests/scenarios.yaml` と同一視しないでください。

element templates については、今回はコード実装を要求していません。ガイド・README・マニュアルへの記述追加と、どのように使うべきかの標準化方針の明文化に留めてください。

2. BPMN標準パターンを追加してください。
最低限、次の再利用パターンを文書またはサンプルとして追加してください。
- 標準 User Task 承認パターン
  - `zeebe:userTask`
  - `formDefinition`
  - `assignmentDefinition`
  - `taskSchedule`
  - `priorityDefinition`
  - ただし標準例では `candidateGroups` を「承認キューがそのまま成立する推奨形」として書かない
  - `assignee` ベースまたは「assignment は運用・authorization 設計とセットで決める」と明記する
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

次は今回見送ってください。
- 独自表現の job worker controlled ad-hoc sub-process 例
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

7. スコープ外
- 実際の Camunda SaaS 接続
- Web Modeler API を呼ぶ自動化コード
- element template JSON 生成のフル実装
- 本番向け Orchestration Cluster API クライアント実装
- Optimize / Administration API の実装

設計判断の方針です。
- Phase 2 は「高度機能の強制」ではなく「安全な導入ガイド化」を重視してください
- advanced pattern は default template に混ぜ込まず、別サンプル・別節で分離してください
- Camunda 8.8 の新機能は、テンプレート利用者が誤解しないように maturity を明記してください
- experimental / alpha / early-access のものは必ず明記し、今回の標準採用対象からは外してください
- Web Modeler 固有資産と、Tecnos-STRIDE 側の `tests/scenarios.yaml` は混同しないでください
- 公式 docs と異なる独自 XML パターンを新たに標準化しないでください

作業後は必ず検証してください。
- 追加した BPMN サンプルに対して `python3 sdd-templates/tools/stride_lint.py` が通るか確認
- guide / docs / README の参照整合を確認
- 何を採用し、何を条件付き採用にし、何を今回見送ったかを最後に整理

編集時の制約です。
- 既存の unrelated change は戻さない
- `apply_patch` で編集する
- まず調査、その後に短い実装計画を出してから編集する
- 最後に変更ファイル、検証結果、残課題を報告する
