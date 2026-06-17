# Phase 4: Execute（SAP 拡張）

> **Compaction re-read**: コンテキスト圧縮後、このファイルを再読み込みすること。
> Phase 4 の SAP 固有実装サイクル・テスト・エビデンス手順が記載されている。

---

## 1. Execution Authority（3層テーブル）

| 分類 | 権限 | 対象ツール / アクション |
|------|------|----------------------|
| **conversational** | 自律実行可（承認不要） | `search.js`, `read.js`, `data_preview.js`, `create_object.js`, `activate.js`, `run_tests.js`, `gui_test.js`, `evidence_capture.js`, lint 系ツール（`clean_abap`, `abaplint`, `sap_common_class_lint`, `sap_quality_score`） |
| **gated** | 人間承認必須 | `pull.js` |
| **prohibited** | 絶対禁止 | SAP 本番系への直接アクセス、TR の本番リリース、ユーザーマスタ変更 |

**gated ツール（`pull.js`）の実行前**: 人間に対象オブジェクトと操作内容を提示し、承認を得ること。
承認なしの gated ツール実行は Execution Authority 違反。

---

## 2. WI フロー（SAP 統合版）

標準 sdd_bootstrap.md の 16-step WI フローをベースに、SAP 固有ステップを統合する。
本セクションの SAP 固有ステップ（Step 6 の 6-1〜6-4、Stage 2、Stage 3）は
**ABAP 開発（ソース実装）を伴う WI でのみ実行する**。
ABAP 開発を伴わない WI（MSAG 作成等）は、標準 16-step フローをそのまま実行する。

以下は SAP 拡張が影響するステップのみ記載。記載のないステップは標準フローに従う。

---

### Step 1: WI 定義作成

- 標準フロー + SAP メタデータ（Rule S4）:
  - `sap_transport`: TR 番号（人間提示必須）
  - `sap_objects`: 対象オブジェクト配列（type + name）
  - `sap_owner`: `.env` の `SAP_USERNAME`
- TR 番号未設定 or sap_objects 空 → Step 6 進行禁止

### Step 3: Mode 判定後の事前承認

- validate mode（`accounting_calc`, `db_schema`, `authz` 等）→ design_diff + plan_review を人間に提示
- confirm mode → plan_review を人間に提示
- autopilot mode → 事前承認なしで進行

---

### Step 6: SAP 実装サイクル（6-1 〜 6-4）

Step 6 は SAP 固有の実装サイクルに展開される。

#### 複数 SAP オブジェクトを含む WI の場合

1 WI に複数の SAP オブジェクト（例: MSAG + PROG）が含まれる場合、
tasks.md の `activation_order` に従い、依存先オブジェクトから順に 6-1（create）を実行する。
全オブジェクトの create が完了した後、6-2 TDD サイクルで実装・テストを実行し、6-3/6-4 で確認する。

> **注**: 既存ソースの取得（pull.js）は Phase 2 前準備 (R3) で実施済み。
> 新規オブジェクトには取得すべきソースがなく、既存オブジェクトは Phase 2 前準備で取得済みのため、
> Phase 4 で pull.js を実行する場面は発生しない。

| Sub-step | アクション | 権限 | 詳細 |
|----------|----------|------|------|
| **6-1** | `create_object.js` でオブジェクト作成 | conversational | type, name, TR を指定。devclass は basic_design から取得 |
| **6-2** | TDD サイクル（AC 単位で繰り返し） | - | 下記「TDD サイクル」参照 |
| **6-3** | `data_preview.js` でテストデータ特定 | conversational | 下記「Step 6-3: テストデータ特定」参照 |
| **6-4** | `gui_test.js` で GUI テスト実行 | conversational | 画面ありプログラムの場合のみ。WSF 設定は `testing_sap.md` 参照。**6-3 で特定した値を使用すること。FAIL 時は `gui_test_fail_analysis.md` を参照** |

#### Step 6-2: TDD サイクル

AC 単位で以下のサイクルを繰り返す。一括実装→一括テストは**禁止**。

```
AC ごとに繰り返し:
  1. テストクラス記述（RED を期待）
  2. 品質チェック: clean_abap → abaplint → sap_common_class_lint → sap_quality_score
  3. textpool チェック（D010TINF の R3STATE='I' が無いことを確認）
  4. activate.js でアクティベーション
  5. run_tests.js で ABAP Unit 実行 → RED 確認
  6. AC の実装コード記述（下記「共通クラス判断プロセス」に従うこと）
  7. 品質チェック: clean_abap → abaplint → sap_common_class_lint → sap_quality_score
  8. textpool チェック
  9. activate.js
  10. run_tests.js → GREEN 確認（FAIL → 6 に戻る）
```

- **品質チェックの実行順序は固定**: clean_abap → abaplint → sap_common_class_lint → sap_quality_score。途中からの再実行は不可。先頭から再実行すること
- **sap_common_class_lint はネガティブチェック専用**: `common_class_rules.yaml` の `forbidden_patterns` に該当するパターンを検出する。共通クラスの使用有無の判定（ポジティブチェック）は行わない。使用判断は下記「共通クラス判断プロセス」で管理する
- **sap_quality_score >= 85pt** は全 AC 実装完了時点で必須。サイクル途中で下回っていても実装継続可
- テストクラスは AC / ロジック区分ごとに分割する（1-2 クラスへの圧縮は**禁止**）
- 各テストクラスは `FOR TESTING RISK LEVEL HARMLESS DURATION SHORT` を付与

#### 共通クラス判断プロセス（Step 6-2 内で実施）

AC の実装コード記述（ステップ 6）において、**各処理ブロックごとに**
`common_class_rules.yaml` の共通クラスで実装できるかを検討する。

```
各処理ブロックごとに:
  1. common_class_rules.yaml の trigger_pattern に該当するか確認
  2. 該当する場合:
     a. 共通クラスのメソッドで実装可能か検討
     b. 可能 → 共通クラスを使用して実装する（原則）
     c. 「実装できないかもしれない」と感じた場合:
        i.  まず共通クラスでの実装を試みる（試さずに除外しない）
        ii. 試した結果、技術的に不可能な場合のみ exclusion として記録
  3. tests/common_class_decisions.yaml に判断結果を記録:
     - 使用した場合 → usages に追加
     - 使用しなかった場合 → exclusions に追加（理由 + リスク評価）
```

**原則: 共通クラスの使用が第一選択肢**。exclusions は「検討した結果どうしても
使えなかった場合」のみ許容される。以下は exclusion の正当な理由にならない:
- 「直接記述の方が簡単」（共通クラスの存在意義を否定する）
- 「共通クラスの使い方がわからない」（rules.yaml にメソッド定義がある）
- 「環境制約で今は使えない」（環境の問題であり、コードの問題ではない）

**exclusion が正当となるケースの例**:
- 共通クラスに該当メソッドが存在しない（例: S_TCODE 権限チェックは AUTH_COMPANY 等と異なる）
- 共通クラスのメソッドシグネチャが処理要件に合わない（例: 共通 Include が提供する項目構成とプログラムの選択画面構成が不一致）

**記録タイミング**: 各 AC の実装完了時（ステップ 10 の GREEN 確認後）に
`common_class_decisions.yaml` を更新する。全 AC 完了後にまとめて記録するのではなく、
AC 単位で逐次記録すること。

**exclusions の理由には以下を含めること**:
- 共通クラスのどのメソッドを検討し、なぜ適用できなかったか
- プログラム内で直接実装した場合のリスク（low / medium / high）
- 将来的に共通クラス側を拡張すれば対応可能かどうか

**エビデンスとの連携**: Stage 3 のエビデンス HTML に「共通クラス使用判断」セクション
として表示される。人間は exclusions の理由の妥当性をレビューする。
exclusions に「理由をひねり出した」形跡がある場合（本来修正すべきものを除外している）、
人間は差し戻してソース修正を指示できる。

**テンプレート**: `extensions/sap/templates/tests/common_class_decisions_template.yaml`

#### textpool チェック詳細

```sql
SELECT * FROM d010tinf WHERE r3state = 'I' AND prog = '<プログラム名>'
```

- `R3STATE='I'`（未活性）のレコードが存在 → textpool が未活性状態
- activate.js 実行前に textpool を解消すること（activate 時にエラーの原因になる）

#### Step 6-3: テストデータ特定

Step 6-2 の TDD サイクルが全 AC 完了した後、GUI テスト（6-4）に進む前に実施する。
**目的**: scenarios.yaml および WSF テンプレートの全テストケースについて、各ケースの条件に合致する実機上のデータを特定し、テストデータセットとして整理する。

「テーブルにデータがある」だけでは不十分。**各テストケースが要求する条件**に実際に当てはまるデータを探して確定させること。
事前にこれをやらなければ、各テストの実行時に再度データを探しなおすか、条件に合わないデータで無意味なテストを実施することになる。

```
手順:
  1. テストケース条件の洗い出し
     scenarios.yaml + WSF テンプレートの全テストパターン（T0〜T11、カスタムテスト）から、
     各テストケースが必要とするデータ条件を一覧化する。
     例:
       - 正常系（T2: ALV 表示）: 指定条件でデータが N 件以上返ること
       - 0 件系（T6: No Data）: 指定条件でデータが 0 件になること
       - フィルタ系（T7: Filter）: 絞込条件で件数が減ること
       - 内容検証系（T8: Content）: 特定カラムに値が入っていること（例: NAME1 が空でない）
       - 回帰系（T9: Regression）: 特定の伝票番号で期待値と一致すること

  2. 各条件に合致する実機データを data_preview.js で探す
     例:
       node data_preview.js VBAK --distinct BUKRS_VF        # 存在する会社コード一覧
       node data_preview.js VBAK --where "BUKRS_VF = '<値>'" --columns VBELN,KUNNR,VKORG,...
       node data_preview.js KNA1 --where "KUNNR = '<値>'"   # JOIN 先にもデータがあるか
       node data_preview.js VBAP --where "VBELN = '<値>'"   # 明細データがあるか

  3. テストケースとデータの対応表を作成する
     全テストケースについて、使用する具体的な値と期待結果を整理する。

     例:
     | テストケース | 条件 | 使用する値 | 期待結果 |
     |------------|------|-----------|---------|
     | T2 正常表示 | BUKRS_VF に有効データあり | P_BUKRS=C34A | 2 件の ALV 表示 |
     | T6 0件     | 存在しない会社コード | P_BUKRS=ZZZZ | MSG-003 表示 |
     | T7 フィルタ | VKORG で絞込 | S_VKORG=C34A | T2 より件数が減る or 同じ |
     | T8 NAME1   | KNA1.NAME1 が空でない | (T2 と同じ) | NAME1 カラムに値あり |
     | T9 回帰    | 特定伝票の NETWR 一致 | VBELN=0000000116 | NETWR_TOTAL=1000 |

  4. ABAP Unit テスト内のハードコード値も同様に検証する
     テストクラスで使用している値（会社コード等）が実機に存在することを確認する。
     存在しない値を「valid ケース」として使用していないか確認する。

  5. 期待出力データを算出する
     手順 2〜3 で確定した入力データに対して、spec.md のビジネスロジック（CALC ルール等）を
     適用し、プログラムが出力すべきデータを算出する。
       - ALV 表示系: 表示されるべき行と各カラムの値を算出
         例: CALC-001（trunc(NETWR*100)/100）→ VBELN=116 の NETWR_TOTAL=1000.00
       - DB 更新系: INSERT/UPDATE 後の期待レコード状態を算出
       - エラー系・0 件系: expected_output は不要（null）
     注意:
       - 計算カラム（例: NETWR_TOTAL = SUM(VBAP-NETWR)）はテーブルに存在しないので、
         ビジネスロジックから導出する
       - JOIN 結果（例: KNA1-NAME1）は JOIN 先テーブルの実機値を使用する
       - S/4HANA 固有の注意点（例: GBSTK は VBUK ではなく VBAK から取得）を考慮する

  6. scenarios.yaml の expected_output に記録する
     手順 5 の算出結果を各シナリオの sap_specifics.expected_output に記録する。
       expected_output:
         format: "alv"          # alv | db_change | message_only
         description: "ALV Grid 表示データ（N 件）"
         columns: [COL1, COL2, ...]
         rows:
           - { COL1: "val1", COL2: "val2", ... }
     注意:
       - columns には evidence_capture.js が data_preview.js に渡す --columns の元になる。
         テーブルに存在しない計算カラム（例: NETWR_TOTAL）も columns に含めてよいが、
         evidence_capture.js が se16_checks 生成時に自動除外する
       - エラー系・0 件系シナリオには expected_output を設定しない（null のまま）
```

**出力**:
1. テストケース × データの対応表。6-4 の WSF CONFIG および ABAP Unit テストで使用する全ての値が実機確認済みであること。
2. scenarios.yaml の全該当シナリオに expected_output が設定済みであること。

**禁止**: 実機で存在確認していない値を WSF CONFIG や ABAP Unit テストにハードコードすること。

---

#### scenarios.yaml とテスト実行の対応

`tests/scenarios.yaml` は WI 内の全テスト活動の仕様書として機能する。

| テスト活動 | scenarios.yaml との関係 | 実行タイミング |
|-----------|----------------------|-------------|
| ABAP Unit テスト (6-2 TDD サイクル) | コードレベルで検証可能なシナリオをカバー | Step 6-2 TDD サイクル内 |
| GUI テスト (6-4) | 画面操作を伴うシナリオをカバー | Step 6-4 |
| Stage 2 シナリオ実行 (S2-B1) | **全シナリオ**を通しで実行し漏れを検証 | 後続の Stage 2 |
| Stage 3 エビデンス取得 (S3-A2) | **全シナリオ**のエビデンスを取得 | 後続の Stage 3 |

#### BAPI パターンガイド

BAPI 呼び出しを含む実装では以下のパターンに従う:

```
判定 LOOP+EXIT → 全レコード LOOP → save_log → job_result
```

1. **判定 LOOP+EXIT**: 事前チェック。エラーがあれば即 EXIT して後続処理をスキップ
2. **全レコード LOOP**: チェック通過後、全対象レコードを処理
3. **save_log**: 処理結果を SLG1 アプリケーションログに保存
4. **job_result**: ジョブ結果（成功/失敗件数）を返却

---

### Stage 2: 受入テスト（Step 6 完了後に実行）

Step 6 の実装・テストが全て完了した後、Step 7 に進む前に実行する。

#### S2-A1: alignment check

- `branch_analyzer` を実行し spec-coverage / impl-coverage を確認
- `overimpl`（過剰実装）/ `spec-gap`（仕様漏れ）を検出

#### S2-A2: AI 判定

- S2-A1 の結果を基に AI が合否を判定
- 過剰実装 → 実装削除 → Step 6 に戻り再テスト
- 仕様漏れ → 人間に提案 → 承認後実装

#### S2-B1: テストシナリオ実行

- scenarios.yaml の**全シナリオ**を実行
- ABAP Unit + GUI テスト の両方が対象

#### S2-B2: NOT_TESTABLE 判定

- 環境制約でテスト不可のシナリオには `NOT_TESTABLE` バッジを付与
- 理由を記録し、人間に報告

#### S2-B3: stride-lint PASS

- `stride lint specs/<feature>/` が PASS であること

#### Dual Test Gate（MANDATORY）

Stage 3 に進む前提条件:
1. **全 ABAP Unit テスト GREEN**
2. **全 GUI テスト PASS**

いずれか一方でも FAIL → Stage 3 進行禁止。Step 6 に戻って解決すること。

---

### Stage 3: エビデンス取得（Dual Test Gate 通過後に実行）

Stage 2 の Dual Test Gate を通過した後、Step 7 に進む前に実行する。

#### S3-A1: 前提条件チェック

以下を全て満たしていることを確認:
1. 全 ABAP Unit テスト GREEN
2. 全 GUI テスト PASS（画面ありプログラムの場合）
3. 仕様ベース分岐カバレッジ 100%
4. 仕様 = 実装 一致（S2-A1 完了）
5. 全テストシナリオ PASS（S2-B1 完了）
6. stride-lint PASS（S2-B3 完了）

#### S3-A2: シナリオ別エビデンス取得

```bash
node extensions/sap/tools/evidence_capture.js specs/<feature>/ --scenario SC-XX --step-id S3-A2
```

#### S3-A3: 統合レポート生成

```bash
node extensions/sap/tools/evidence_merge_report.js specs/<feature>/
```

#### S3-A4: AC 別検証結果テーブル確認

- 個別シナリオ HTML の AC 別検証結果テーブルが正しいことを確認

#### S3-A5: エビデンス自己チェック（IMP-028）

エビデンス HTML を以下の 5 項目で自己チェックする:

| # | チェック項目 | 確認内容 |
|---|------------|---------|
| 1 | 選択画面スクリーンショット | spec.md の `selection_fields` と一致すること |
| 2 | 結果画面メッセージタイプ | `expected_result` のメッセージタイプと一致すること |
| 3 | SLG1 スクリーンショット | ログエントリが **1 件のみ** であること |
| 4 | SE16 データセクション | plan.md で定義された全テーブルの SE16 セクションが存在すること |
| 5 | HTML 構造整合性 | `img` タグが `ss-label`（スクリーンショットラベル）の直後に配置されていること |

5 項目全て OK → Step 7 に進行。1 項目でも NG → 該当エビデンスを再取得。

---

### Step 7〜13: 標準フロー（SAP 固有の追加なし）

以下のステップは標準 sdd_bootstrap.md §6 の手順をそのまま実行する。

| Step | アクション | 備考 |
|------|----------|------|
| **7** | `stride lint specs/<feature>/` 実行 | PASS 必須（exit 0） |
| **8** | `sdd_planning_bridge.py sync` 実行 | plan.md Errors セクション更新 |
| **9** | walkthrough.md 作成 | テンプレート: walkthrough_template.md |
| **10** | `sdd_planning_bridge.py evidence` 実行 | Planning Evidence を walkthrough.md に挿入 |
| **11** | test_results.md 作成 | coverage_tier が standard/critical なら**必須**。basic_design.md の coverage_tier を確認して判定すること |
| **12** | `sdd_planning_bridge.py learn` 実行 | **全 WI で実行する**。lessons 候補が空でも実行する |
| **13** | `/planning:archive` 実行 | **全 WI で実行する**。アーカイブ対象が空でも実行する |

---

### Step 14: SAP 固有完了チェック

標準の 5-step チェックリスト（sdd_bootstrap.md §5）に SAP 拡張を追加:

| # | チェック項目 | done 条件 |
|---|------------|----------|
| 1 | AC coverage | spec_refs → AC-* の全キーワード充足 |
| 2 | NFR 確認 | performance / security / data / integration |
| 3 | scenarios.yaml 検証 | 全 SCN-* の expected 充足 |
| 4 | stride-lint PASS | exit 0 |
| 5 | stride pr-check PR_READY | 7/7 |
| **S-1** | **test_green_confirmation** | `unit_test: all_passed: true` + `gui_test: all_passed: true` |
| **S-2** | **sap_quality_score** | >= 85pt |
| **S-3** | **sap_objects 完全性** | 全 sap_objects が activate 済み |

---

### Step 15〜16: 標準フロー（SAP 固有の追加なし）

| Step | アクション | 備考 |
|------|----------|------|
| **15** | WI 承認依頼（⛔ 停止） | WI-*.approval.md を人間に提示。人間が承認するまで停止 |
| **16** | state.yaml 更新 | 人間承認後、該当 WI の status を done に更新 |

---

## 承認済み成果物の変更ルール

本 Phase の作業中に、先行 Gate で承認済みの成果物を修正する必要が生じた場合:
1. `implementation-details/change_log.md` に変更内容・理由・影響範囲を記録する
2. 意味的変更（要件追加・削除等）の場合は人間に再承認を相談する
3. フォーマット修正のみ（lint 準拠等）の場合は change_log 記録のみで続行可

**change_log を記録せずに承認済み成果物を変更してはならない。**

---

## 参照

- `CLAUDE_SAP.md` Rule S3（ツール実行権限）
- `CLAUDE_SAP.md` Rule S4（WI メタデータ必須）
- `agent_docs/error_recovery_sap.md`（ツールエラー回復手順）
- `agent_docs/testing_sap.md`（テスト詳細 / GUI テスト WSF 設定）
- `agent_docs/gui_test_fail_analysis.md`（GUI テスト FAIL 時の原因分析）
- `agent_docs/codegen_sap.md`（コード生成品質ルール / アンチパターン）
- `agent_docs/conventions_sap.md`（命名規約）
- `templates/abap/PATTERNS.md`（ABAP コーディングパターン / 共通クラス API）
