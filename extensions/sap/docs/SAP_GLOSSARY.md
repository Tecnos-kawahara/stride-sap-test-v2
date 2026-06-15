# SAP Extension 用語集 v2

本テンプレート（SAP Extension Pack v2.0.0 / STRIDE v6.0.0）で使用する
SAP 拡張固有の用語を整理した用語集です。
対象読者: 本テンプレートを初めて使用する開発者およびプロジェクトマネージャー。

---

## 1. SDD フレームワーク用語

SDD 標準フレームワークの用語のうち、SAP 拡張で特有の意味を持つもの。

| 用語 | 説明 |
|------|------|
| **Phase Gate** (Gate 1-5, Final) | 各 Phase 間の承認ポイント。Gate を通過しないと次の Phase に進めない。SAP 拡張では Gate 1,2 承認後に **Phase 1.5** が挿入される。 |
| **AC (Acceptance Criteria)** | 受入条件。**spec.md** で定義し、1 AC = 1 **TS** = 1 テストメソッドの原則で管理する。AC の **SSoT** は spec.md。各 AC には **catalog_refs** を設定する。 |
| **TS (Test Spec)** | テスト仕様。**AC** と 1:1 で対応する。ID 体系は `TS-UT-xx`（単体）/ `TS-INT-xx`（統合）/ `TS-E2E-xx`（E2E）/ `TS-TM-xx`（**Type B** テストマトリクス駆動）。 |
| **WI (Work Item)** | 作業項目。GitHub Issues で管理し、1 WI が 1 つ以上の **AC** に紐づく。Phase 4 の実行単位であり、16-step フローで処理する。 |
| **SSoT (Single Source of Truth)** | 唯一の正本。本テンプレートでは **AC** の SSoT を spec.md に一本化し、他ファイルはそこから参照・展開する。 |
| **S-Evidence** | 正式エビデンス。Stage 3（Step **S3-A2**）で取得するスクリーンショット + JSON データの成果物。`.tool_evidence/` に格納される。 |

---

## 2. SAP 拡張ワークフロー v2 用語

SAP Extension Pack v2.0.0 固有のワークフロー概念。

| 用語 | 説明 |
|------|------|
| **Phase 1.5** | SAP コンテキスト取得フェーズ（任意）。**Gate 1,2** 承認後、Specify Phase 前に実施する。SAP システムから技術情報を収集し、spec.md の入力とする。ステップ ID は `1.5-A1` -- `1.5-C2`。 |
| **process_definitions** | basic_design.md の処理定義セクション。各処理定義は `body` にステップのシーケンスを持ち、タグベースの分岐パターン（**tag_branch_rules.yaml** 参照）で展開される。v1 の `processing_steps` を置き換える。 |
| **catalog_refs** | AC に設定するフィールド。その AC が独立検証するカタログ項目（CHK/CALC/MSG 等）への参照。独立した条件は独立した AC にする。正常系完了やカタログ外の AC は `catalog_refs: []`。 |
| **Type A パス（要件駆動）** | `traceability_rows` -> spec.md AC -> scenarios.yaml（`traceability_ref` で紐付け）。各要件（RQ）に対応する AC を定義し、AC がシナリオで検証される従来型パス。 |
| **Type B パス（テスト仕様駆動）** | `test_matrix` -> scenarios.yaml（`test_matrix_ref` で紐付け）。**spec AC を経由しない**。test_matrix.test_cases[].id を直接シナリオの test_matrix_ref で参照する。シナリオ ID は `TS-TM-` プレフィックス。RQ に紐付かないテスト仕様を AC に混入させずトレーサビリティを保つための仕組み。 |
| **traceability_ref** | scenarios.yaml の各シナリオに設定するフィールド。**Type A** パスにおいて、traceability_rows の RQ と AC を紐づける参照。 |
| **test_matrix_ref** | scenarios.yaml の各シナリオに設定するフィールド。**Type B** パスにおいて、test_matrix.test_cases[].id を直接参照する。 |
| **risk_flags** | タスクごとに設定されるリスクフラグ。値に応じて実行 **mode** が自動判定される。例: `ui_only`, `message_only`, `test_only`, `logging_only`, `new_api`, `contract_change`, `performance_sensitive`, `accounting_calc`, `db_schema`, `authz`, `sod`, `pii`, `data_migration`。 |
| **mode** | タスクの実行モード。**risk_flags** から自動判定される 3 段階: **autopilot**（事前承認なし）/ **confirm**（plan_review 必須）/ **validate**（design_diff + plan_review 必須）。 |
| **Dual Test Gate** | Phase 4 内の 2 段階テストゲート構造。Stage 1（ABAP Unit + GUI テスト）で単体・画面レベルを検証し、Stage 2 で scenarios.yaml 全シナリオを通しで再実行して漏れを検証する。**Type A** + **Type B** 両系統のシナリオを全て通過することが求められる。 |
| **Ops Pack** | Final Phase（Step **F-2**）で検証する運用文書セット。`ops/transport_manifest.yaml`、`ops/release_checklist.md`、`ops/rollback_plan.md`、`ops/hypercare_runbook.md` の 4 文書で構成される。全文書がプロジェクト固有の内容で記入済みであること。 |
| **activation_order** | tasks.md で定義する SAP オブジェクトの有効化順序。SAP オブジェクト依存関係（DDIC -> CDS -> BDEF -> CLAS -> DCLS -> SRVD -> SRVB -> DDLX）に従い、依存先オブジェクトから順に create/activate する。 |
| **Execution Authority** | Phase 4 のツール実行権限を 3 層で制御する仕組み: **conversational**（自律実行可）/ **gated**（人間承認必須）/ **prohibited**（絶対禁止）。 |
| **path_analysis** | plan.md のパス分析セクション。**process_definitions[].body** を解析し、`normal_paths`（正常系）、`abnormal_paths`（異常系）、`ai_decisions` を列挙する。scenarios.yaml の入力となる。 |
| **covers_ts** | テストシナリオがカバーする **TS** の一覧。パス通過する処理ステップに紐づく E2E AC のみを含める。 |
| **expected_result** | テストシナリオの期待結果。check 種別（`message_type`, `db_changed`, `field_value_set`, `bapi_return`, `lock_verify` 等）の配列で定義する。 |
| **ai_provenance** | evidence_pack に追加する AI 来歴セクション。生成エージェント名、モデル名、セッション ID、生成ファイル一覧、人間レビュー状態を記録する。 |

---

## 3. SAP 技術用語（テンプレート文脈）

テンプレート内で使用される SAP 技術用語。

| 用語 | 説明 |
|------|------|
| **program_type** | プログラム種別。`report`（レポート）/ `interface`（インタフェース）/ `rap_bo`（RAP ビジネスオブジェクト）/ `fugr`（汎用モジュールグループ）/ `enhancement`（拡張）。basic_design.md / spec.md で定義する。 |
| **clean_core_policy.tier** | クリーンコアポリシーの階層。`tier-1`（Released API のみ使用）/ `tier-2`（Classic ABAP + 非リリース API 許可）/ `tier-3`（レガシー）。basic_design.md / spec.md で定義する。 |
| **TR (Transport Request)** | 移送依頼。`$TMP` パッケージ以外では必須。開発オブジェクトの変更を本番環境へ移送する単位。 |
| **ADT (ABAP Development Tools)** | ABAP 開発ツール（Eclipse ベース）。本テンプレートの `tools/*.js` は ADT REST API 経由で SAP システムと通信する。 |
| **ABAP Unit** | SAP 標準の単体テストフレームワーク。Step 6-2 TDD サイクルで使用する。**AC** 1 件につき 1 テストメソッドを作成する。 |
| **Test Double Framework** | `CL_OSQL_TEST_ENVIRONMENT` を利用した DB モック機構。**ABAP Unit** テスト内で DB 依存を排除するために使用する。 |
| **SAP オブジェクト依存順序** | `DDIC -> CDS -> BDEF -> CLAS -> DCLS -> SRVD -> SRVB -> DDLX`。tasks.md のタスク順序および **activation_order** はこの依存関係に従う。 |

---

## 4. ツール・設定ファイル用語

テンプレートで使用する設定ファイルとディレクトリ。

| 用語 | 説明 |
|------|------|
| **MANIFEST.yaml** | SAP Extension Pack の宣言ファイル（v2.0.0）。検出条件、scaffold 定義、ツール一覧（validators / mapping_refs / utilities / sap_operations の 4 層）、Phase 別ステップ定義、テンプレート定義、設定ファイル一覧を記述する。 |
| **tag_branch_rules.yaml** | タグベースの分岐パターン定義ファイル。`sap_path_enumerator.py` が **process_definitions[].body** のステップタグから分岐パスを展開する際に使用する。各タグに対して normal/abnormal/error 分岐を定義する。 |
| **common_class_rules.yaml** | 共通クラス・共通 Include のルール定義ファイル。どの共通部品を使用すべきかを規定する。`forbidden_patterns`（ネガティブチェック）も含む。 |
| **test_perspective_master.yaml** | 処理種別（**処理種別コード**）x 分岐パターン -> テスト観点（**テスト観点コード**）のマッピング定義。plan.md / scenarios.yaml 生成時に参照される。 |
| **quality_score_config.yaml** | 品質スコアの減点ルール（QR-01 -- QR-14）と合格基準（85 点）。Phase 4 の品質チェックで使用する。 |
| **tool_evidence_registry.yaml** | ステップ ID -> ツール -> evidence ファイルの対応表（v2.0）。どのステップでどのツールがどの成果物を生成するかを定義する。 |
| **test_suggest_config.yaml** | **AC** タグ -> テスト種別 / ID プレフィックスのマッピング。**TS** の ID 自動採番に使用する。 |
| **.tool_evidence/** | `specs/<feature>/` 配下のエビデンスファイル格納ディレクトリ。**S-Evidence** およびツール実行ログを保存する。 |
| **scenarios.yaml** | `specs/<feature>/tests/` 配下のテストシナリオ定義ファイル。**Type A**（traceability_ref）+ **Type B**（test_matrix_ref）の 2 系統シナリオを格納する。 |

---

## 5. テスト観点コード

`test_perspective_master.yaml` で定義されるテスト観点コード。scenarios.yaml の観点割り当てに使用する。

### 分岐・業務ロジック系

| コード | 説明 |
|--------|------|
| **BRANCH_BIZ** | 業務分岐テスト。業務ロジックの条件分岐が正しく動作するかを検証する。 |
| **ERROR_MSG** | エラーメッセージ検証。異常系で適切なメッセージが出力されるかを確認する。 |
| **ERROR_LOGIC** | エラー時のロジック検証。異常系でロールバック等の後処理が正しく実行されるかを確認する。 |
| **PROGRAM_TERMINATE** | プログラム終了検証。プログラムが正常終了すること（DUMP しないこと）を検証する。 |
| **ERROR_COUNT** | エラー件数検証。エラーメッセージにエラー概要が含まれることを確認する。 |

### 入力・バリデーション系

| コード | 説明 |
|--------|------|
| **INPUT_VALIDATE** | 入力値バリデーション検証。異常値の入力バリデーションエラーを検出する。 |
| **REQUIRED_FIELD** | 必須項目検証。必須項目未入力時のエラーを検出する。 |
| **EDIT_ERROR** | 編集チェック検証。編集チェックエラーの検出を検証する。 |
| **BOUNDARY_VALUE** | 境界値テスト。計算・集計処理の境界値（上限超過等）を検証する。 |

### F4 ヘルプ・画面系

| コード | 説明 |
|--------|------|
| **F4_HELP** | 検索ヘルプ動作確認。入力項目の F4 検索ヘルプが正しく機能するかを検証する。 |
| **F4_VALUE_SET** | F4 値設定確認。F4 ヘルプで選択した値がフィールドに正しく設定されるかを検証する。 |
| **SCREEN_LAYOUT** | 画面レイアウト検証。選択画面・ALV 等のレイアウト表示を検証する。 |
| **OUTPUT_FIELD** | 出力フィールド検証。出力フィールドが正しく表示されるかを検証する。 |
| **OUTPUT_LAYOUT** | 出力レイアウト検証。出力レイアウトが正しく表示されるかを検証する。 |
| **ALL_FIELDS_OUTPUT** | 全出力項目検証。全出力項目が正しく表示されるかを検証する。 |
| **PAGE_BREAK** | 改ページ検証。帳票出力の改ページが正しく動作するかを検証する。 |

### ファイル系

| コード | 説明 |
|--------|------|
| **FILE_DELIMITER** | ファイル区切り文字テスト。ファイル入出力時の区切り文字の処理を検証する。 |
| **FILE_ZERO_INPUT** | ファイル 0 件入力検証。0 件ファイル入力時にエラーにならないことを検証する。 |
| **FILE_FIELD_LENGTH** | ファイルフィールド桁数検証。フィールド桁数が正しく処理されるかを検証する。 |
| **FILE_ZERO_OUTPUT** | ファイル 0 件出力検証。0 件出力時に適切なメッセージが出力されることを検証する。 |

### DB 系

| コード | 説明 |
|--------|------|
| **DB_CRUD_RESULT** | DB 操作結果確認。INSERT / UPDATE / DELETE 後のテーブル状態を検証する。v1 の **DB_RESULT** に相当。 |
| **DB_SELECT_MATCH** | DB SELECT 結果確認。データが正しく取得されることを検証する。 |
| **ROLLBACK_EXEC** | ロールバック実行確認。ROLLBACK が実行されデータが変更されないことを検証する。 |
| **COMMIT_ROLLBACK** | コミット / ロールバック検証。COMMIT WORK / ROLLBACK WORK の実行結果を検証する。 |
| **ZERO_DATA_EDIT** | 0 件データ編集検証。0 件データに対して適切なメッセージが出力されることを検証する。v1 の **ZERO_INPUT** に相当。 |

### BAPI 系（v2 新規）

| コード | 説明 |
|--------|------|
| **BAPI_RETURN_VERIFY** | BAPI RETURN テーブル検証。BAPI RETURN テーブルにエラーが含まれない（正常系）/ 含まれる（異常系）ことを検証する。 |
| **BAPI_COMMIT_VERIFY** | BAPI コミット検証。BAPI_TRANSACTION_COMMIT 後にデータが確定することを検証する。 |

### ロック系（v2 新規）

| コード | 説明 |
|--------|------|
| **LOCK_ACQUIRE** | ロック取得検証。ENQUEUE 後にロックエントリが存在すること（SM12 で確認）を検証する。 |
| **LOCK_SM12_VERIFY** | SM12 ロック検証。SM12 でロックオブジェクトに対象キーが含まれることを検証する。 |
| **LOCK_CONFLICT** | ロック競合検証。別セッションからの実行でロックエラーが発生することを検証する。 |

### その他（v2 新規を含む）

| コード | 説明 |
|--------|------|
| **TRY_CATCH_BIZ** | 例外処理検証。RFC 呼出失敗等の例外処理が正しく行われることを検証する。 |
| **FORMAT_CONVERT** | データ変換検証。データ変換の正常完了 / エラー検出を検証する。 |
| **LOG_CONTENT** | ログ内容検証。アプリケーションログ（SLG1）が正しく記録されるかを検証する。 |
| **MAIL_SEND** | メール送信検証。メールが正しく送信されるかを検証する。 |
| **BDC_DATA_VERIFY** | BDC データ検証。BDC データが正しく投入されるかを検証する。 |
| **BDC_SCREEN_VERIFY** | BDC 画面遷移検証。BDC 画面遷移が正しく処理されるかを検証する。 |
| **WF_TRIGGER** | ワークフロー起動検証。ワークフローが正しく起動されるかを検証する。 |

---

## 6. v2 ステップ ID 体系

ステップ ID は `{Phase}-{グループ文字}{連番}` の形式で命名する。

### 命名規則

- **Phase 部**: 実行フェーズを示す（`1`, `1.5`, `2`, `3`, `4`, `5`）
- **グループ文字**: 同一フェーズ内の作業グループを示す（`A`, `B`, `C`, `D`）
- **連番**: グループ内の順序を示す（`1`, `2`, `3`, ...）

### Phase 1（Design -- yaml -> basic_design 転記）

| ステップ ID | グループ | 概要 |
|-------------|----------|------|
| **1-A1** | A: 生成 | yaml -> basic_design.md 生成（マッピングテーブルに従い転記） |
| **1-A2** | A: 生成 | パターン分岐の identify + risk_flags 自動判定 |
| **1-B1** | B: BPMN | BPMN 生成 |
| **1-C1** | C: 検証 | yaml 全要素の展開確認（basic_design_completeness_validator） |
| **1-C2** | C: 検証 | カタログ整合性（catalogs_consistency_validator） |
| **1-C3** | C: 検証 | STRIDE 標準 lint |

### Phase 1.5（SAP コンテキスト取得 -- 任意）

| ステップ ID | グループ | 概要 |
|-------------|----------|------|
| **1.5-A1** | A: SAP 調査 | SAP オブジェクト検索（search.js） |
| **1.5-A2** | A: SAP 調査 | SAP ソース参照（read.js） |
| **1.5-A3** | A: SAP 調査 | SAP ソース取得（pull.js -- gated） |
| **1.5-B1** | B: 記録 | sap_context.md 記録 |
| **1.5-B2** | B: 記録 | テーブルメタデータ記録（sap_context_metadata.py） |
| **1.5-C1** | C: 検証 | T100 メッセージ検証（sap_message_t100_validator） |
| **1.5-C2** | C: 検証 | DDIC 存在検証（sap_ddic_gate_validator） |

### Phase 2（Specify）

| ステップ ID | グループ | 概要 |
|-------------|----------|------|
| **2-A1** | A: 仕様定義 | spec.md 作成（AC に **catalog_refs** 設定） |
| **2-A2** | A: 仕様定義 | contracts 作成（SAP 固有テンプレート適用） |
| **2-B1** | B: テスト計画 | plan.md 作成（**path_analysis** セクション含む） |
| **2-C1** | C: シナリオ | scenarios.yaml 作成（**Type A** + **Type B** の 2 系統） |
| **2-D1** | D: 検証 | カタログ整合性（catalogs_consistency_validator） |
| **2-D2** | D: 検証 | glossary 参照確認（glossary_ref_validator） |
| **2-D3** | D: 検証 | AC 粒度検証（sap_ac_granularity_validator） |
| **2-D4** | D: 検証 | plan 品質検証（plan_quality_validator -- PQ-01 -- PQ-15） |

### Phase 3（Tasking）

| ステップ ID | グループ | 概要 |
|-------------|----------|------|
| **3-A1** | A: タスク定義 | tasks.md 作成（SAP 開発順序 + sap_objects + **mode** 自動判定） |

### Phase 4 -- WI 16-step フロー（Execute）

SAP 固有ステップのみ記載。記載のないステップは標準 16-step フローに従う。

| ステップ | 概要 |
|----------|------|
| **Step 1** | WI 定義作成（sap_transport, sap_objects, sap_owner 設定） |
| **Step 3** | Mode 判定後の事前承認（validate / confirm / autopilot） |
| **Step 6-1** | `create_object.js` でオブジェクト作成（**activation_order** 順） |
| **Step 6-2** | TDD サイクル（AC 単位で RED -> GREEN を繰り返し。一括実装禁止） |
| **Step 6-3** | `data_preview.js` でテストデータ特定 |
| **Step 6-4** | `gui_test.js` で GUI テスト実行（画面ありプログラムのみ） |

### Stage 2（受入テスト -- WI 内後続）

| ステップ | 概要 |
|----------|------|
| **S2** | scenarios.yaml 全シナリオの通し実行。ABAP Unit + GUI テストの結果と合わせて漏れを検証する。 |

### Stage 3（エビデンス取得 -- WI 内後続）

| ステップ | 概要 |
|----------|------|
| **S3** | 全シナリオのエビデンスを取得し `.tool_evidence/` に格納する。 |

### Final Phase

| ステップ ID | グループ | 概要 |
|-------------|----------|------|
| **F-1** | evidence_pack | evidence_pack 完成（ai_provenance + test_green_confirmation 含む） |
| **F-2** | Ops Pack | **Ops Pack** 検証（transport_manifest, release_checklist, rollback_plan, hypercare_runbook） |
| **F-3** | pr-check | stride pr-check 7/7 全チェック PASS |
| **F-4** | 承認 | Final Gate 承認（人間が APPROVAL.md を編集） |

---

## 7. 処理種別コード

`test_perspective_master.yaml` で定義される処理種別コード。**process_definitions** の分類に使用する。

| コード | 説明 |
|--------|------|
| **AUTH** | 権限チェック処理 |
| **EXIST** | 存在チェック処理 |
| **F4HELP** | 検索ヘルプ処理（**F4_HELP** / **F4_VALUE_SET** 観点と対応） |
| **FILE_READ** | ファイル読込処理 |
| **FILE_WRITE** | ファイル書出処理 |
| **VALIDATE** | 入力値バリデーション処理 |
| **ALV** | ALV グリッド表示処理 |
| **MSG** | メッセージ出力処理 |
| **DB_READ** | データベース読込処理 |
| **DB_WRITE** | データベース書込処理（**DB_CRUD_RESULT** 観点と対応） |
| **CALC** | 計算・集計処理 |
| **CONVERT** | データ変換処理 |
| **COMMIT** | コミット処理（COMMIT WORK） |
| **COMMIT_ROLLBACK** | コミット / ロールバック処理（COMMIT のエイリアス） |
| **LOCK** | ロック（排他制御）処理（**LOCK_ACQUIRE** / **LOCK_SM12_VERIFY** / **LOCK_CONFLICT** 観点と対応） |
| **LOG** | アプリケーションログ出力処理 |
| **PRINT** | 帳票出力処理 |
| **MAIL** | メール送信処理 |
| **RFC** | RFC（リモート関数呼出）処理。カスタム RFC やリモートシステム連携用（**TRY_CATCH_BIZ** 観点と対応） |
| **BAPI** | BAPI（Business API）処理。SAP 標準 BAPI 経由の DB 更新。BAPI_TRANSACTION_COMMIT/ROLLBACK 付き（**BAPI_RETURN_VERIFY** / **BAPI_COMMIT_VERIFY** 観点と対応） |
| **BADI** | BAdI（ビジネスアドイン）処理 |
| **BDC** | バッチインプット処理（**BDC_DATA_VERIFY** / **BDC_SCREEN_VERIFY** 観点と対応） |
| **IDOC** | IDoc（中間ドキュメント）処理 |
| **WF** | ワークフロー処理（**WF_TRIGGER** 観点と対応） |
| **OTHER** | 上記に該当しないその他の処理 |

---

## 相互参照マップ

主要な用語間の関係を以下に示す。

```
yaml（function_group_spec + feature_spec）
  |
  v  [Phase 1: 1-A1 転記]
basic_design.md (SSoT)
  +-- process_definitions[].body
  |     +-- tag --> tag_branch_rules.yaml --> 分岐パターン展開
  |     +-- path_analysis (plan.md) --> scenarios.yaml
  +-- traceability_rows ------> [Type A] spec AC --> scenarios (traceability_ref)
  +-- test_matrix ------------> [Type B] scenarios (test_matrix_ref)  ※spec AC 非経由
  +-- catalogs (CHK/CALC/MSG)
  |     +-- catalog_refs <-- AC (spec.md)
  +-- sap_context
        +-- dev_objects --> sap_objects (tasks.md)
        +-- activation_order (tasks.md)

spec.md (AC の SSoT)
  +-- AC --- 1:1 --- TS (TS-UT-xx / TS-TM-xx 等)
  |           |
  |           +-- catalog_refs --> catalogs 項目
  |           +-- covers_ts <-- scenarios.yaml
  +-- WI (GitHub Issues) --> 16-step フロー (Phase 4)
        +-- risk_flags --> mode (autopilot/confirm/validate)
        +-- Step 6-2: TDD サイクル (AC 単位)
        +-- Step 6-4: GUI テスト
        +-- S2: 受入テスト (全シナリオ通し)
        +-- S3: エビデンス取得 --> .tool_evidence/

Final Phase
  +-- F-1: evidence_pack (ai_provenance 含む)
  +-- F-2: Ops Pack 検証 (4 文書)
  +-- F-3: stride pr-check 7/7
  +-- F-4: Final Gate 承認
```
