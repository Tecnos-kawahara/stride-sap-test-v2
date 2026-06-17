# SAP 拡張 設定ファイルリファレンス v2

本ドキュメントは SAP 拡張パック v2.0.0 の全設定ファイルのフィールドリファレンスです。

`extensions/sap/config/` 配下の YAML ファイルは、SAP 拡張テンプレートの動作を制御する設定ファイル群である。
各ファイルの全フィールドをこのドキュメントで解説する。

対象読者: テンプレート利用者およびテンプレートメンテナー。

---

## 目次

1. [common_class_rules.yaml](#1-common_class_rulesyaml) -- 共通クラス・共通 Include 使用ルール
2. [test_perspective_master.yaml](#2-test_perspective_masteryaml) -- テスト観点マスタ
3. [quality_score_config.yaml](#3-quality_score_configyaml) -- 品質スコアリング設定
4. [tool_evidence_registry.yaml](#4-tool_evidence_registryyaml) -- ツールエビデンス登録簿
5. [test_suggest_config.yaml](#5-test_suggest_configyaml) -- テスト提案設定
6. [tag_branch_rules.yaml](#6-tag_branch_rulesyaml) -- タグベース分岐パターン定義 (v2 新規)

---

## 1. common_class_rules.yaml

**パス:** `extensions/sap/config/common_class_rules.yaml`
**参照元ツール:** sap_checklist_suggest.py, sap_common_class_lint.py, sap_quality_score.py

このファイルは 2 つのセクションで構成される: `common_class_rules`（共通クラスルール）と `common_include_rules`（共通 Include ルール）。

### v1 からの変更点

- v1 では 6 ルール（CC-FILE-01 ~ CC-MSG-01）のみ。v2 では **11 ルール** に拡張。
- v2 追加: CC-ORG-01（組織系 4 クラス）, CC-BP-01（取引先）, CC-TYPE-01（DDIC 型検証）, CC-TRACE-01（ランタイムトレース）, CC-RANGE-01（RANGE TABLE）。
- v2 追加クラスは HTML 仕様書（参考資料/要対応事項/共通クラス類追加/）から抽出。合計 16+1 CLAS/IF, 92 メソッドが完全登録されている。
- CC-AUTH-01 の forbidden_patterns に `AUTHORITY-CHECK` を追加（v1 では空リスト）。
- CC-ALV-01 の forbidden_patterns に `CL_SALV_TABLE`, `CL_GUI_ALV_GRID` を追加。

---

### 1.1 common_class_rules セクション

共通クラスの適用判定ルールおよび禁止パターンを定義する。各ルールは以下の構造を持つ。

#### ルール構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `id` | 文字列 | ルールの一意識別子（例: `CC-FILE-01`） | lint エラーメッセージやログの識別子が変わる。既存の参照と整合性を保つこと |
| `trigger_pattern` | 文字列（正規表現） | AC（受入基準）の記述に対してマッチする正規表現パターン | sap_checklist_suggest.py が AC 文をこの正規表現でスキャンし、マッチしたルールを適用候補として spec.md の `common_class_applicability` に出力する。パターンを広げると誤検知が増え、狭めると検知漏れが増える |
| `forbidden_patterns` | 文字列リスト | ABAP ソースコード内で使用を禁止するパターン | sap_common_class_lint.py がソースコードをスキャンし、このリスト内のパターンが検出された場合に lint エラーを報告する。共通クラスの代わりに標準 API を直接使用しているケースを検出する目的。空リスト `[]` の場合は禁止パターンチェックなし |
| `classes` | リスト | 適用対象の共通クラス群 | 空リスト `[]` の場合、そのルールは `forbidden_patterns` のみのチェックとなる（例: CC-MSG-01） |

#### classes 配下の構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `name` | 文字列 | 共通クラス名（例: `ZCL_CMA_LOCAL_FILE`） | lint 対象のクラス名が変わる。共通クラス自身のソースファイルは lint 対象外として自動除外される |
| `condition` | 文字列（任意） | このクラスが適用される条件の説明（例: `ローカルファイル`） | チェックリスト提案時の表示テキストに影響。未指定可 |
| `description` | 文字列（任意） | クラスの説明（例: `ローカルファイル入出力`） | sap_checklist_suggest.py が spec.md の `common_class_applicability` に `class_description` として出力する。開発時にクラスの用途を把握するために使用 |
| `methods` | リスト | クラスが提供するメソッド群 | 定義されたメソッドのみが使用可能。未定義メソッドの呼び出しは lint エラーとなる |

#### methods 配下の構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `name` | 文字列 | メソッド名（例: `INPUT_CSV`） | lint がパラメータ突合を行う対象メソッドが変わる |
| `description` | 文字列（任意） | メソッドの説明（例: `ローカルCSVファイル読込`） | sap_checklist_suggest.py が spec.md の `common_class_applicability` にメソッド説明として出力する |
| `parameters` | リスト | メソッドのパラメータ定義 | ここに定義されたパラメータのみ使用可能。未定義パラメータは lint エラーとなる |

#### parameters 配下の構造

| フィールド | 型 | 有効値 | 説明 |
|---|---|---|---|
| `name` | 文字列 | 任意 | パラメータ名（例: `iv_path`） |
| `direction` | 文字列 | `IMPORTING`, `EXPORTING`, `CHANGING`, `RETURNING` | パラメータの方向。ABAP メソッドの方向に対応 |
| `type` | 文字列 | ABAP データ型名 | パラメータの型（例: `string`, `BUKRS`, `BAPIRET2`, `TY_ROWS`） |
| `optional` | 真偽値 | `true` / `false` | 省略時は `false`（必須パラメータ）。`true` の場合、呼び出し時にパラメータを省略可能 |
| `default` | 文字列（任意） | 任意 | デフォルト値（例: `'Sheet1'`）。指定された場合はパラメータ省略時にこの値が適用される |

---

#### 現在定義されているルール一覧 (v2: 全 11 ルール)

| ID | trigger_pattern（対象キーワード） | クラス | 概要 |
|---|---|---|---|
| CC-FILE-01 | ファイル, file, CSV, TSV, Excel, 固定長, アップロード, ダウンロード | ZCL_CMA_LOCAL_FILE (12 methods), ZCL_CMA_AP_FILE (10 methods) | ファイル操作。GUI_UPLOAD / GUI_DOWNLOAD / OPEN DATASET 等 9 パターンを禁止 |
| CC-AUTH-01 | 権限, AUTHORITY, 会社コード, プラント, 販売エリア, 購買組織 | ZCL_CMA_COMMON_CHECK (8 methods) | 権限チェック・存在チェック。`AUTHORITY-CHECK` 直書きを禁止 |
| CC-ALV-01 | ALV, 一覧表示, 一覧出力 | ZCL_CMA_ALV_GENERIC (11 methods), ZCL_CMA_ALV_HANDLER (2 methods), ZIF_CMA_ALV_CALLBACK (1 method) | ALV 表示。REUSE_ALV_*/CL_SALV_TABLE/CL_GUI_ALV_GRID を禁止 |
| CC-LOG-01 | アプリケーションログ, SLG1, ログ出力, ログ記録 | ZCL_CMA_APPLOG (3 methods) | アプリケーションログ。BAL_LOG_CREATE/BAL_LOG_MSG_ADD/BAL_DB_SAVE を禁止 |
| CC-JOBRESULT-01 | 処理結果, JOB.?RESULT, 成功件数, エラー件数, 処理サマリ | ZCL_CMA_JOB_RESULT (1 method) | 処理結果集計 |
| CC-MSG-01 | メッセージ, MESSAGE, エラー通知, 警告, 通知 | (なし -- classes: []) | T100 メッセージクラス使用強制。`MESSAGE '` リテラル直書きを禁止 |
| **CC-ORG-01** | 会社, 組織, プラント, 販売エリア, 購買組織 | ZCL_CMA_COMPANY (6 methods), ZCL_CMA_SALESAREA (6 methods), ZCL_CMA_PURORG (6 methods), ZCL_CMA_PLANT (6 methods) | **v2 追加** -- 組織系クラス群。権限チェック・存在チェック・住所/名称取得（単一/複数/詳細） |
| **CC-BP-01** | 取引先, BP, ビジネスパートナー | ZCL_CMA_BP (4 methods) | **v2 追加** -- 取引先(BP)住所情報取得 |
| **CC-TYPE-01** | 型検証, DDIC, TYPE, 入力チェック | ZCL_CMA_TYPE_CHECK (9 methods) | **v2 追加** -- DDIC 型情報に基づく入力値の検証・変換 |
| **CC-TRACE-01** | トレース, デバッグ, ランタイム | ZCL_CMA_RUNTIME_TRACE (4 methods), ZCG_CMA_RUNTIME_TRACE (0 methods) | **v2 追加** -- ランタイム情報を LOG-POINT 経由で記録 |
| **CC-RANGE-01** | RANGE, SELECT-OPTIONS, 選択条件 | ZCL_CMA_RANGE_UTIL (4 methods) | **v2 追加** -- RANGE TABLE エントリ構築ユーティリティ |

---

### 1.2 common_include_rules セクション

選択画面の共通 Include プログラムに関するルールを定義する。ABAP プログラムで INCLUDE 文により取り込む。

#### ルール構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `id` | 文字列 | ルールの一意識別子（例: `CI-ORG-01`） | lint メッセージの識別子に影響 |
| `name` | 文字列 | Include プログラム名（例: `ZCMAI000101`） | ABAP ソース内の INCLUDE 文で参照される実際のプログラム名 |
| `description` | 文字列 | Include の説明（例: `会社コード共通画面(単一)`） | チェックリスト提案時の表示テキスト |
| `trigger_pattern` | 文字列（正規表現） | AC / selection_screen の記述にマッチする正規表現 | マッチした場合に適用候補として提示される。sap_checklist_suggest.py が spec.md の `common_include_applicability` に出力 |
| `provides` | 文字列 | Include が提供する選択画面項目の概要 | 提案時に利用者に表示される説明テキスト。Include が定義する PARAMETERS / SELECT-OPTIONS の概要 |

#### 現在定義されている Include ルール

**組織系 (CI-ORG-01 ~ CI-ORG-06)**

| ID | Include 名 | 説明 | trigger_pattern（主要キーワード） | 提供項目 |
|---|---|---|---|---|
| CI-ORG-01 | ZCMAI000101 | 会社コード共通画面(単一) | 会社コード, BUKRS, company.?code | P_BUKRS |
| CI-ORG-02 | ZCMAI000102 | 販売エリア共通画面(単一) | 販売エリア, 販売組織, 流通チャネル, 製品部門, VKORG, VTWEG, SPART, sales.?area | P_VKORG, P_VTWEG, P_SPART |
| CI-ORG-03 | ZCMAI000103 | 販売組織共通画面(単一) | 販売組織, VKORG, sales.?org | P_VKORG |
| CI-ORG-04 | ZCMAI000104 | 購買組織共通画面(単一) | 購買組織, EKORG, purchasing.?org | P_EKORG |
| CI-ORG-05 | ZCMAI000105 | プラント共通画面(単一) | プラント, WERKS, plant | P_WERKS |
| CI-ORG-06 | ZCMAI000106 | 管理領域共通画面(単一) | 管理領域, KOKRS, controlling.?area | P_KOKRS |

**ファイル系 (CI-FILE-01 ~ CI-FILE-04)**

| ID | Include 名 | 説明 | trigger_pattern（主要キーワード） | 提供項目 |
|---|---|---|---|---|
| CI-FILE-01 | ZCMAI000107 | Local ファイル共通画面 | ローカルファイル, local.?file, アップロード, ダウンロード, ファイルパス | P_FILE |
| CI-FILE-02 | ZCMAI000108 | Local ファイル(エラー)共通画面 | エラーファイル, error.?file, エラーダウンロード | P_EFILE |
| CI-FILE-03 | ZCMAI000109 | AP ファイル共通画面 | サーバーファイル, AP.?ファイル, server.?file | P_DPATH, P_DFILE |
| CI-FILE-04 | ZCMAI000110 | AP ファイル(エラー)共通画面 | サーバーエラーファイル, AP.?エラー | P_EDPATH, P_EDFILE |

**テスト・ALV 系**

| ID | Include 名 | 説明 | trigger_pattern（主要キーワード） | 提供項目 |
|---|---|---|---|---|
| CI-TEST-01 | ZCMAI000111 | テスト実行共通画面 | テスト実行, テストモード, test.?run, test.?mode | P_TEST |
| CI-ALV-01 | ZCMAI000112 | ALV 共通画面 | ALV, バリアント, 一覧表示, variant | P_VARI |

---

## 2. test_perspective_master.yaml

**パス:** `extensions/sap/config/test_perspective_master.yaml`
**参照元ツール:** sap_expand_traceability.py, sap_scenario_generator.py, sap_ac_generator.py

テスト観点の「マスタデータ」。処理種別ごとに分岐パターンとテスト観点コードを定義する。

---

### 2.1 processing_types セクション

処理種別（processing_type）をキーとし、各処理種別の分岐パターンを定義する。

#### processing_types のトップレベル

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| (キー名) | 文字列 | 処理種別の名前。basic_design.md の `processing_type` で参照される | 新しい処理種別を追加すると sap_scenario_generator.py の分岐パターン候補が増える。キー名は basic_design.md 側と一致させること |
| `branches` | リスト | 分岐パターンの配列。空リスト `[]` の場合、自動分岐生成の対象外 | 分岐を追加するとテスト観点の候補が増え、テストカバレッジが広がる |

#### branches 配下の構造

| フィールド | 型 | 有効値 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `pattern` | 文字列 | 任意 | 分岐パターン名（例: `権限あり`, `読込失敗`） | テストシナリオ生成時のパターン名として使用される |
| `type` | 文字列 | `normal`, `abnormal` | 正常系/異常系の分類 | テストカバレッジの正常系・異常系の分類に影響。`abnormal` は必ずエラー系のテスト観点を含む |
| `perspectives` | 文字列リスト | 観点コード名 | この分岐で検証すべきテスト観点のリスト | sap_scenario_generator.py が covers_ts を生成する際に参照。perspective_expected_checks と連動 |
| `default_expected_result` | リスト | check オブジェクト群 | デフォルトの期待結果定義 | AI が初期提案として使用し、レビュー・修正する。`__PLACEHOLDER__` は AI が具体値に置き換える必要がある |
| `evidence_method` | 文字列（任意） | `auto`（デフォルト）, `manual_required` | エビデンス取得方法 | `manual_required` の場合、自動テストではカバーできず手動テストが必要であることを示す |
| `evidence_reason` | 文字列（任意） | 任意 | `manual_required` の理由説明 | テスト計画書に手動テストが必要な理由として出力される |

#### default_expected_result の check オブジェクト

| check 種別 | 追加フィールド | 説明 |
|---|---|---|
| `no_error` | なし | エラーなしで処理が継続すること |
| `message_type` | `value`: メッセージタイプ (`S`, `E`, `I`, `W`) | 特定タイプのメッセージが表示されること |
| `message_text_contains` | `value`: 含まれる文字列 | メッセージ本文に特定の文字列が含まれること |
| `alv` | `value`: `true` | ALV が表示されること |
| `alv_min_rows` | `value`: 最小行数 | ALV の最小表示行数 |
| `screen_number` | なし | 画面遷移が正しいこと |
| `db_changed` | `table`, `keys`, `expected` (`true`/`false`), `mode` (`insert`/`update`/`delete`) | DB テーブルの変更検証 |
| `file_output` | `path`, `contains` または `expected_error` | ファイル出力の検証 |
| `log_output` | `object`, `subobject`, `contains` | アプリケーションログの検証 |
| `print_output` | `contains` | 帳票出力の検証 |
| `mail_sent` | `recipient`, `subject_contains` または `expected_error` | メール送信の検証 |
| `bdc_result` | `transaction`, `expected_status` | BDC 処理結果の検証 |
| `rfc_return` | `function_module`, `expected_type` | RFC 呼出し結果の検証 |
| `bapi_return` | `function_module`, `expected_type` | BAPI RETURN テーブルの検証 |
| `lock_verify` | `lock_object`, `lock_key`, `expected` | ロックエントリの存在検証（SM12 相当） |
| `field_value_set` | `field`, `expected_value` | F4 ヘルプ選択後のフィールド値検証 |
| `idoc_status` | `idoc_type`, `expected_status` | IDoc ステータスの検証 |
| `wf_status` | `workflow_id`, `expected_status` | ワークフローステータスの検証 |

#### __PLACEHOLDER__ について

`__PLACEHOLDER__` の値は AI が必ず具体的な値に置き換えなければならない。このファイルでは初期テンプレートとして `__PLACEHOLDER__` を記述し、sap_scenario_generator.py が実際のプログラム仕様に基づいて具体値を代入する。

#### 現在定義されている処理種別一覧

| 処理種別 | 分岐パターン数 | 概要 |
|---|---|---|
| AUTH | 2 | 権限チェック（権限あり / 権限なし）。権限なしは `manual_required` |
| EXIST | 2 | 存在チェック（存在する / 存在しない） |
| F4HELP | 2 | 検索ヘルプ（標準検索ヘルプ / ファイル選択ダイアログ）。両方 `normal`。選択値のフィールド設定まで検証 |
| FILE_READ | 4 | ファイル読込（読込成功 / 読込失敗 / 区切り文字不正 / 0件入力） |
| FILE_WRITE | 3 | ファイル書出（出力成功 / 桁数超過 / 0件出力） |
| VALIDATE | 4 | 入力バリデーション（正常入力 / 必須項目空 / 異常値 / 編集エラー） |
| ALV | 1 | ALV 一覧表示 |
| MSG | 2 | メッセージ（正常メッセージ / エラーメッセージ） |
| DB_READ | 2 | DB 参照（データあり / データなし） |
| DB_WRITE | 4 | DB 更新（INSERT / UPDATE / DELETE / 失敗） |
| CALC | 3 | 計算処理（正常範囲 / 上限超過 / 0件） |
| CONVERT | 2 | データ変換（変換成功 / 変換失敗） |
| COMMIT | 2 | コミット制御（COMMIT / ROLLBACK） |
| COMMIT_ROLLBACK | 2 | COMMIT のエイリアス。basic_design.md で `processing_type: "COMMIT_ROLLBACK"` を使用する場合に対応 |
| LOCK | 2 | ロック制御（ロック成功 / ロック競合）。SM12 でのエントリ確認・別セッションでの競合確認 |
| LOG | 2 | アプリケーションログ（正常ログ / エラーログ） |
| PRINT | 1 | 帳票出力 |
| MAIL | 2 | メール送信（送信成功 / 送信失敗） |
| RFC | 2 | RFC 呼出し（呼出成功 / 呼出失敗）。リモート関数呼出し用 |
| BAPI | 2 | BAPI 標準 DB 更新（更新成功 / 更新失敗）。BAPI_TRANSACTION_COMMIT/ROLLBACK 付き |
| BADI | 2 | BAdI 拡張（拡張成功 / 拡張失敗） |
| BDC | 2 | BDC 処理（投入成功 / 投入失敗） |
| IDOC | 2 | IDoc 送受信（送受信成功 / 送受信失敗） |
| WF | 2 | ワークフロー（起動成功 / 起動失敗） |
| OTHER | 0 | その他。branches 空（自動分岐生成なし） |

---

### 2.2 perspective_expected_checks セクション

テスト観点コード（perspective）ごとに、正常系（`success`）および異常系（`failure`）の期待チェック項目を定義する。sap_scenario_generator.py が `covers_ts` の `expected_checks` を生成する際に参照する。

#### 構造

各観点コードをキーとし、`success` / `failure` のいずれかまたは両方を持つ。

```yaml
PERSPECTIVE_CODE:
  success:
    - { check: "チェック種別", description: "説明" }
  failure:
    - { check: "チェック種別", description: "説明" }
```

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `check` | 文字列 | check 種別名（前述の check 種別を参照） | テストシナリオの expected_checks に使用される検証項目が変わる |
| `description` | 文字列 | テスト項目の説明文 | テスト仕様書に出力される説明が変わる |

#### 現在定義されている観点コード一覧

| 観点コード | success | failure | 説明 |
|---|---|---|---|
| BRANCH_BIZ | no_error | message_type | 業務分岐処理 |
| ERROR_MSG | message_type (S) | message_type (E) | エラーメッセージ |
| ERROR_LOGIC | -- | screen_number | エラー処理ロジック |
| F4_HELP | no_error | -- | F4 検索ヘルプ |
| F4_VALUE_SET | field_value_set | -- | F4 ヘルプ選択値のフィールド設定 |
| FILE_DELIMITER | no_error | message_type | ファイル区切り文字処理 |
| FILE_ZERO_INPUT | -- | no_error | 0件ファイル入力 |
| FILE_FIELD_LENGTH | no_error | message_type | フィールド桁数 |
| FILE_ZERO_OUTPUT | -- | message_type | 0件出力 |
| FORMAT_CONVERT | no_error | message_type | データ変換 |
| BOUNDARY_VALUE | no_error | message_type | 境界値 |
| ZERO_DATA_EDIT | -- | message_type | 0件データ編集 |
| INPUT_VALIDATE | -- | message_type | 入力バリデーション |
| REQUIRED_FIELD | -- | message_type | 必須項目 |
| EDIT_ERROR | -- | message_type | 編集チェック |
| DB_CRUD_RESULT | db_changed | -- | DB CRUD 結果 |
| ROLLBACK_EXEC | -- | db_changed | ROLLBACK 実行 |
| COMMIT_ROLLBACK | db_changed | db_changed | COMMIT/ROLLBACK |
| PROGRAM_TERMINATE | -- | no_error | プログラム終了 |
| ERROR_COUNT | -- | message_text_contains | エラー件数 |
| SCREEN_LAYOUT | no_error | -- | 画面レイアウト |
| OUTPUT_FIELD | no_error | -- | 出力フィールド |
| ALL_FIELDS_OUTPUT | no_error | -- | 全出力項目 |
| OUTPUT_LAYOUT | no_error | -- | 出力レイアウト |
| PAGE_BREAK | no_error | -- | 改ページ |
| LOG_CONTENT | log_output | log_output | ログ内容 |
| DB_SELECT_MATCH | no_error | -- | DB SELECT 結果 |
| MAIL_SEND | mail_sent | -- | メール送信 |
| BDC_DATA_VERIFY | bdc_result | -- | BDC データ検証 |
| BDC_SCREEN_VERIFY | bdc_result | -- | BDC 画面遷移検証 |
| WF_TRIGGER | wf_status | -- | ワークフロー起動 |
| BAPI_RETURN_VERIFY | bapi_return | bapi_return | BAPI RETURN テーブル検証 |
| BAPI_COMMIT_VERIFY | db_changed | -- | BAPI COMMIT 後のデータ確定 |
| LOCK_ACQUIRE | lock_verify | -- | ENQUEUE 後のロックエントリ存在 |
| LOCK_SM12_VERIFY | lock_verify | -- | SM12 でのロックオブジェクト確認 |
| LOCK_CONFLICT | -- | message_type | 別セッションからのロック競合 |
| TRY_CATCH_BIZ | -- | message_type | 例外処理 |

---

### 2.3 screen_perspectives セクション

画面系テスト観点の定義。選択画面および画面定義に関するテスト観点を列挙する。

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `code` | 文字列 | 観点コード | テスト観点の識別子 |
| `source` | 文字列 | `selection_screen`, `screen_definition` | 観点のソース種別。選択画面由来か画面定義由来かを区別 |
| `description` | 文字列 | 観点の説明 | テスト仕様書に出力される |

現在の定義:

| code | source | description |
|---|---|---|
| SCREEN_LAYOUT | selection_screen | 選択画面レイアウト |
| BUTTON_CTRL | screen_definition | ボタン制御 |
| MENU_CTRL | screen_definition | メニュー制御 |
| SCREEN_NAVIGATE | screen_definition | 画面遷移制御 |
| INITIAL_VALUE | selection_screen | 入力項目の初期値 |

---

### 2.4 mixed_check_patterns セクション (v2)

親処理種別の配下に出現しやすいサブステップの処理種別を定義する。
sap_expand_traceability.py が RQ の statement / branches 内のキーワードを走査し、サブステップが独立 RQ として切り出されていない場合に WARNING を出力する。

#### 構造

```yaml
mixed_check_patterns:
  PARENT_TYPE:
    - keywords: ["検出キーワード群"]
      sub_type: サブステップの処理種別
      description: "人間が読む説明"
```

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| (キー名) | 文字列 | 親処理種別 | この処理種別に属する RQ がキーワードを含む場合にチェック対象 |
| `keywords` | 文字列リスト | 検出キーワード群 | マッチした場合にサブステップ独立を推奨する WARNING が出力される |
| `sub_type` | 文字列 | サブステップの処理種別 | 独立させるべき処理種別名 |
| `description` | 文字列 | 説明 | WARNING メッセージに出力される |

#### 現在定義されている混在チェックパターン

| 親処理種別 | sub_type | キーワード（主要） | 説明 |
|---|---|---|---|
| DB_READ | VALIDATE | 0件, データなし, 存在しない, 該当なし | DB_READ の 0件チェックは VALIDATE として独立 |
| DB_READ | MSG | エラーメッセージ, エラー出力, 警告メッセージ | DB_READ 後のエラーメッセージ出力は MSG として独立 |
| FILE_READ | VALIDATE | 0件, データなし, 空ファイル | FILE_READ の 0件チェックは VALIDATE として独立 |
| FILE_READ | VALIDATE | 区切り文字, フォーマット, 桁数, 型不正 | FILE_READ のフォーマット検証は VALIDATE として独立 |
| FILE_READ | MSG | エラーメッセージ, エラー出力 | FILE_READ 後のエラーメッセージ出力は MSG として独立 |
| DB_WRITE | FILE_WRITE | エラーデータ出力, エラーファイル, エラーリスト出力 | DB_WRITE 時のエラーデータファイル出力は FILE_WRITE として独立 |
| DB_WRITE | MSG | エラーメッセージ, エラー出力, 失敗メッセージ | DB_WRITE 後のエラーメッセージ出力は MSG として独立 |
| CALC | VALIDATE | 0件, データなし, 計算不能 | CALC の 0件/計算不能チェックは VALIDATE として独立 |
| CALC | MSG | エラーメッセージ, エラー出力 | CALC 後のエラーメッセージ出力は MSG として独立 |
| COMMIT | FILE_WRITE | エラーデータ出力, エラーファイル | COMMIT 時のエラーデータ出力は FILE_WRITE として独立 |
| COMMIT | MSG | エラーメッセージ, エラー出力 | COMMIT 後のエラーメッセージ出力は MSG として独立 |

---

## 3. quality_score_config.yaml

**パス:** `extensions/sap/config/quality_score_config.yaml`
**参照元ツール:** sap_quality_score.py

ABAP ソースコードの品質スコアリング設定。100 点満点からの減点方式で評価する。

### v1 からの変更点

- v1 では 4 カテゴリ（error_handling/naming_convention/template_compliance/maintainability）。v2 では **5 カテゴリ**（`runtime_efficiency` を追加）。
- max_deductions のバランスが変更: error_handling 30, naming_convention 20, template_compliance 15, maintainability 15, runtime_efficiency 20（合計 100）。
- v2 で `sap_specific_rules` セクション（QR-01 ~ QR-14）を追加。ABAP ソースのパターンマッチで検出する SAP 固有品質ルール群。
- template_compliance にコメントとして v2 新版テンプレートの記述が追加。

---

### 3.1 トップレベル設定

| フィールド | 型 | 値 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `pass_threshold` | 整数 | `85` | 合格基準点。この点数以上で PASS 判定 | 値を下げると品質基準が緩くなり、上げるとより厳しくなる。0~100 の範囲 |

### 3.2 max_deductions（カテゴリ別最大減点）

各カテゴリの減点上限を定義する。個別ルールの減点累計がこの値を超えた場合、上限でキャップされる。

| カテゴリ | 値 | 説明 | 変更時の影響 |
|---|---|---|---|
| `error_handling` | `30` | エラーハンドリング漏れの最大減点 | 値を変更するとこのカテゴリの減点影響度が変わる |
| `naming_convention` | `20` | 命名規約違反の最大減点 | 同上 |
| `template_compliance` | `15` | テンプレート準拠の最大減点 | 同上 |
| `maintainability` | `15` | 保守性の最大減点 | 同上 |
| **`runtime_efficiency`** | **`20`** | **実行効率の最大減点（v2 新規）** | 同上 |

> **注意:** 全カテゴリの max_deductions 合計（30+20+15+15+20=100）が 100 点満点と一致する設計。合計値を変更する場合は全体のバランスに注意すること。

---

### 3.3 error_handling カテゴリ（エラーハンドリング漏れ）

| ルール | 減点 | 単位 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `select_without_subrc` | `5` | /件 | SELECT 文の後に SY-SUBRC チェックがない場合 | 減点値を上げるとチェック漏れへのペナルティが強くなる |
| `common_class_without_check` | `5` | /件 | 共通クラス呼出しの後に BAPIRET2 の戻り値チェックがない場合 | 同上 |
| `external_call_without_try` | `3` | /件 | 外部呼出し（RFC 等）に TRY-CATCH がない場合 | 同上 |
| `no_message_statement` | `10` | /プログラム | プログラム全体で MESSAGE 文が 1 つも存在しない場合 | メッセージ出力がないプログラムへの固定減点 |

---

### 3.4 naming_convention カテゴリ（命名規約違反）

#### compliance_thresholds（命名規約遵守率による減点）

命名規約の遵守率（0.0~1.0）に応じた段階的な減点を定義する。上から順に評価され、最初にマッチした閾値の減点が適用される。

| min_ratio | deduction | 説明 |
|---|---|---|
| `0.9` | `0` | 遵守率 90% 以上: 減点なし |
| `0.7` | `10` | 遵守率 70~90%: -10 点 |
| `0.5` | `20` | 遵守率 50~70%: -20 点 |
| `0.0` | `25` | 遵守率 50% 未満: -25 点（最大減点） |

#### その他のルール

| ルール | 減点 | 単位 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `inline_declaration` | `3` | /件 | `DATA(` によるインライン宣言の使用 | SAP 標準ではインライン宣言は推奨されるが、テンプレートでは明示的宣言を要求する方針 |
| `call_method_usage` | `5` | /件 | `CALL METHOD` 構文の使用（新構文 `object->method( )` を推奨） | 旧構文使用に対するペナルティ。減点値を調整可能 |

---

### 3.5 template_compliance カテゴリ（テンプレート準拠）

| ルール | 減点 | 単位 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `arbitrary_message` | `10` | /件 | `MESSAGE '任意テキスト'` のように T100 メッセージクラスを使用せずリテラル文字列でメッセージを出力している場合 | T100 メッセージクラスの使用強制。CC-MSG-01 の forbidden_patterns と連動 |
| `unused_declared_class` | `10` | /プログラム | spec.md で宣言済みの共通クラスがソースコード内で使用されていない場合 | 宣言と実装の乖離に対するペナルティ |

v2 ではコメントとして以下の新版テンプレート準拠事項が記載されている:
- `catalogs.messages` の type は `error`/`warning`/`info`/`success`（E/W/I/S/A は旧仕様）
- `test_matrix` は `columns` + `test_cases`（`cases[]` は旧仕様）
- `database` は `data_references` 構造（`referenced_tables` は旧仕様）

---

### 3.6 runtime_efficiency カテゴリ（実行効率）-- v2 新規

| ルール | 減点 | 単位 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `select_star` | `5` | /件 | `SELECT *` の使用 -- DB-AS 間の不要カラム転送を検出 | SELECT 文で明示的にフィールド指定を強制 |
| `move_corresponding` | `3` | /件 | `MOVE-CORRESPONDING` の使用 -- 実行時フィールドマッチングのオーバーヘッド | 明示的フィールド代入を推奨 |
| `broad_catch_cx_root` | `5` | /件 | `CATCH cx_root` の使用 -- 想定外例外の握りつぶしを検出 | 具体的な例外クラスでの CATCH を強制 |
| `steps_per_form_exceeded` | `5` | /件 | 1 FORM 内に複数 @STEP が存在 -- メモリスコープ肥大化を検出 | FORM/メソッドの責務分割を推奨 |

---

### 3.7 maintainability カテゴリ（保守性）

#### comment_ratio（コメント比率による減点）

コメント行の比率に応じた段階的な減点を定義する。

| min_ratio | deduction | 説明 |
|---|---|---|
| `0.10` | `0` | コメント比率 10% 以上: 減点なし |
| `0.05` | `5` | コメント比率 5~10%: -5 点 |
| `0.00` | `10` | コメント比率 5% 未満: -10 点 |

#### long_method（過長メソッド）

| フィールド | 値 | 説明 | 変更時の影響 |
|---|---|---|---|
| `long_method_threshold` | `100` | この行数を超えるメソッド / FORM を「過長」と判定 | 閾値を下げるとより厳しい判定になる |
| `long_method_deduction` | `5` | 過長メソッド 1 件あたりの減点 | 検出件数 x 減点値が累計される（max_deductions でキャップ） |

---

### 3.8 sap_specific_rules セクション -- SAP 固有品質ルール (v2 新規)

sap_quality_score.py が ABAP ソースに対してパターンマッチで検出する SAP 固有ルール群。
各ルールは上記 5 カテゴリのいずれかに帰属し、合計減点はカテゴリ上限で頭打ちになる。

#### ルール構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `id` | 文字列 | ルール ID（例: `QR-01`） | lint 出力で識別子として使用 |
| `category` | 文字列 | 帰属カテゴリ（`code_structure`, `error_handling`, `naming`） | そのカテゴリの max_deductions でキャップされる |
| `deduction` | 整数（負値） | 検出時の減点（例: `-5`） | 減点幅を調整可能 |
| `pattern` | 文字列 | 検出パターンの説明（正規表現またはロジック説明） | パターンを変更するとマッチ精度に影響 |
| `description` | 文字列 | ルールの説明 | lint 出力メッセージに表示 |

#### 全ルール一覧 (QR-01 ~ QR-14)

**code_structure カテゴリ**

| ID | 減点 | description | 検出内容 |
|---|---|---|---|
| QR-01 | -5 | TABLES 文使用禁止 | `TABLES` 文の使用 |
| QR-05 | -3 | 即時 CLEAR される中間テーブルコピー | `INTO TABLE gt_xxx. gt_xxx = gt_xxx. CLEAR gt_` パターン |
| QR-07 | -3 | コメント内に別プログラム名 | ヘッダコメントの Report 名と REPORT 文の不一致 |
| QR-08 | -2 | 連続空白行(3行以上) | 3 行以上の空行 |
| QR-09 | -10 | ABAP Unit 圧縮クラス検出 | テストクラス定義数<=2 かつ メソッド定義数>=10 |
| QR-10 | -5 | イベントブロック内 lcl_ 直接呼出 | AT SELECTION-SCREEN/START-OF-SELECTION 内の `lcl_xxx=>` |

**error_handling カテゴリ**

| ID | 減点 | description | 検出内容 |
|---|---|---|---|
| QR-02 | -8 | BAPI RETURN 判定で type='A' 漏れ | `WHERE type = 'E'` に `OR type = 'A'` がない |
| QR-03 | -8 | BAPI エラー後の全件記録 LOOP なし | BAPI 呼出後の ROLLBACK/lv_has_error ブロック内に `LOOP AT.*return` なし |
| QR-04 | -10 | save_log->job_result 順序違反 | job_result 呼出前方に save_log 呼出なし |
| QR-12 | -8 | spec message_mapping type 不一致 | ABAP MESSAGE 文の type と spec.md message_mapping[].type の不一致 |
| QR-13 | -5 | 0件シナリオのステバー上書き | `MESSAGE sXXX` 直後に `PERFORM finish` なし |
| QR-14 | -5 | DISPLAY LIKE 句の type 誤認 | `DISPLAY LIKE 'E'` 付き MESSAGE の type と sbar.MessageType の不一致 |

**naming カテゴリ**

| ID | 減点 | description | 検出内容 |
|---|---|---|---|
| QR-06 | -3 | MESSAGE 文中ハードコードフォーマット | `MESSAGE...WITH '(TSV|CSV|EXCEL|FIX)'` パターン |
| QR-11 | -3 | BAPI フィールドに非標準型使用 | BAPI 構造体フィールドへの代入元が TYPE p で BAPICURR 系でない |

---

## 4. tool_evidence_registry.yaml

**パス:** `extensions/sap/config/tool_evidence_registry.yaml`
**参照元ツール:** sap_tool_evidence_validator.py（stride_lint 経由）

各フェーズ・ステージで必要なエビデンスファイルとその生成ツールの対応表を定義する。
`specs/<feature>/.tool_evidence/` ディレクトリ内のエビデンスファイルの有無をチェックする際に使用される。

### v1 からの変更点

- `schema_version` が `"1.0"` から **`"2.0"`** に変更。
- v1 の Phase 構成（phase_1_5 / phase_2 / stage_1 / stage_2 / stage_3）を v2 では完全再構成。
- v2 では Phase 4 の WI 16-step フローに統合: `phase_4_step_6`（SAP 実装）, `phase_4_step_6_sap`（SAP 固有追加）。
- 旧版 Stage 1 は廃止し、品質チェックツールは Phase 4 Step 6 に移動。
- v2 で `read.js`（ソース参照）, `create_object.js`（オブジェクト作成）, `evidence_merge_report.js`（統合レポート生成）を追加。
- v2 では `s8d_rerun_steps` セクションは定義されていない。

---

### 4.1 トップレベル設定

| フィールド | 型 | 値 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `schema_version` | 文字列 | `"2.0"` | スキーマバージョン。v1 は `"1.0"` | 将来の互換性管理用 |

---

### 4.2 phases セクション

フェーズ/ステージごとにステップの配列を定義する。

#### フェーズ構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `name` | 文字列 | フェーズの表示名 | lint 出力のフェーズ名称に影響 |
| `check_condition` | 文字列 | チェック実行条件 | この条件を満たす場合にのみエビデンスチェックが実行される |
| `steps` | リスト | ステップ定義の配列 | ステップを追加/削除すると必須エビデンスファイルが変わる |

#### check_condition の有効値 (v2)

| 値 | 説明 |
|---|---|
| `gate_1_and_2_approved` | Gate 1, 2 が承認済みの場合にチェック |
| `gate_5_approved` | Gate 5 が承認済みの場合にチェック |
| `step_6_complete` | Step 6 完了時にチェック |
| `all_wi_complete` | 全 WI 完了時にチェック |
| `stage_2_complete` | Stage 2 完了時にチェック |

#### steps 配下の構造

| フィールド | 型 | 有効値 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `step_id` | 文字列 | フェーズ内のステップ ID（例: `2P-A1`, `6-3`, `S2-A1`） | ステップの識別子。エビデンスファイル名 `{step_id}__{tool_basename}.evidence.yaml` に使用される | ファイル名が変わるため既存エビデンスとの整合性に注意 |
| `tool` | 文字列 | ツールのファイル名（例: `sap_checklist_suggest.py`, `activate.js`） | このステップで実行されるツール名 | エビデンスファイル名の一部となる |
| `description` | 文字列 | 任意 | ステップの説明 | lint 出力のメッセージに表示される |
| `optional` | 真偽値 | `true` / `false` | 省略時は `false`。`true` の場合、エビデンスファイルがなくても lint エラーにならない | `true` にすると条件付きスキップが可能 |

---

### 4.3 現在定義されているフェーズとステップ (v2)

#### phase_2_pre: Phase 2 前準備 -- SAP コンテキスト取得

check_condition: `gate_1_and_2_approved`

| step_id | ツール | 説明 | optional |
|---|---|---|---|
| 2P-A1 | search.js | SAP オブジェクト検索 | false |
| 2P-A2 | read.js | SAP ソース参照 | true（参照不要の場合スキップ） |
| 2P-A3 | pull.js | SAP ソース取得（gated authority: 人間承認必須） | true（新規作成の場合スキップ） |
| 2P-B2 | sap_context_metadata.py | テーブルメタデータ記録（--tables） | false |

#### phase_4_step_6: Phase 4 Step 6 -- SAP 実装 (v2 新規)

check_condition: `gate_5_approved`

| step_id | ツール | 説明 | optional |
|---|---|---|---|
| 6-1 | create_object.js | SAP オブジェクト作成 | true（modify の場合スキップ） |
| 6-2 | pull.js | 既存ソース取得（modify 時） | true（create の場合スキップ） |
| 6-3 | clean_abap.js | ABAP 自動クリーンアップ（順序 1/4） | false |
| 6-4 | sap_common_class_lint.py | 共通クラス使用準拠チェック（順序 2/4） | false |
| 6-5 | sap_quality_score.py | 品質スコアチェック >= 85 点（順序 3/4） | false |

#### phase_4_step_6_sap: Phase 4 Step 6-SAP -- SAP 固有追加 (v2 新規)

check_condition: `step_6_complete`

| step_id | ツール | 説明 | optional |
|---|---|---|---|
| 6-SAP-1 | activate.js | SAP アクティベーション | false |
| 6-SAP-2 | run_tests.js | ABAP Unit テスト実行 | false |
| 6-SAP-3 | data_preview.js | テストデータ確認 | true（データ参照がない場合スキップ） |
| 6-SAP-4 | gui_test.js | SAP GUI テスト実行 | true（画面なしプログラムの場合スキップ） |

#### stage_2: Stage 2 -- 受入テスト

check_condition: `all_wi_complete`

| step_id | ツール | 説明 | optional |
|---|---|---|---|
| S2-A1 | sap_branch_analyzer.py | spec-coverage + impl-coverage 分析 | false |
| S2-B1 | evidence_capture.js | シナリオ実行 + スクリーンショット | false |

#### stage_3: Stage 3 -- エビデンス取得

check_condition: `stage_2_complete`

| step_id | ツール | 説明 | optional |
|---|---|---|---|
| S3-A1 | evidence_capture.js | フルエビデンス取得 | false |
| S3-A3 | evidence_merge_report.js | 統合レポート生成 | false |

---

## 5. test_suggest_config.yaml

**パス:** `extensions/sap/config/test_suggest_config.yaml`
**参照元ツール:** sap_test_suggest.py（非推奨だが設定は引き続き参照される）

テスト提案の自動生成に関する設定。

> **注意:** sap_test_suggest.py は deprecated（非推奨）であるが、この設定ファイルは他のツールからも参照される場合がある。

---

### 5.1 tag_mapping セクション

AC（受入基準）のタグからテスト種別と ID プレフィックスへのマッピングを定義する。

| タグ | type | prefix | 説明 |
|---|---|---|---|
| `authorization` | `unit` | `TS-UT` | 権限チェック関連のテスト。単体テストとして分類 |
| `integration` | `integration` | `TS-INT` | 結合テスト |
| `data` | `unit` | `TS-UT` | データ操作関連のテスト。単体テストとして分類 |
| `e2e` | `e2e` | `TS-E2E` | エンドツーエンドテスト |

| フィールド | 説明 | 変更時の影響 |
|---|---|---|
| `type` | テスト種別（`unit`, `integration`, `e2e`） | テストの分類が変わる。auto_evidence_types との連動に注意 |
| `prefix` | テスト ID のプレフィックス | 生成されるテスト ID の命名に影響。テンプレート共通の ID 規約（`sdd-templates/config/id_conventions.yaml` の `test_id`）を参照 |

---

### 5.2 auto_evidence_types セクション

自動エビデンス取得の対象となるテスト種別のリスト。

```yaml
auto_evidence_types: ["unit", "contract", "integration", "gui", "e2e"]
```

| 値 | 説明 | 変更時の影響 |
|---|---|---|
| `unit` | 単体テスト | リストから除外すると、該当テスト種別のエビデンスが手動取得に変わる |
| `contract` | コントラクトテスト | 同上 |
| `integration` | 結合テスト | 同上 |
| `gui` | GUI テスト | 同上 |
| `e2e` | エンドツーエンドテスト | 同上 |

リストに含まれるテスト種別は自動エビデンス取得対象となり、含まれないテスト種別は手動でエビデンスを取得する必要がある。

---

### 5.3 default_transaction セクション

プログラム種別に対するデフォルトのトランザクションコードを定義する。

| プログラム種別 | デフォルト tcode | 説明 | 変更時の影響 |
|---|---|---|---|
| `report` | `SA38` | レポートプログラム | テスト実行時のデフォルトトランザクションが変わる |
| `interface` | `SA38` | インターフェースプログラム | 同上 |
| `rap_bo` | `SE80` | RAP ビジネスオブジェクト | 同上 |
| `fugr` | `SE37` | 汎用モジュールグループ | 同上 |
| `enhancement` | `SE80` | 拡張（BAdI 等） | 同上 |

---

### 5.4 name_max_length / scope_max_length

| フィールド | 値 | 説明 | 変更時の影響 |
|---|---|---|---|
| `name_max_length` | `120` | テスト名の最大文字数 | 上限を超えるテスト名は切り詰められるか警告が出る |
| `scope_max_length` | `120` | テストスコープの最大文字数 | 同上 |

---

### 5.5 default_field_strategies セクション

`verify_data_strategy` の値から `field_strategies` を推論するためのデフォルトマッピング。YAML ルールに `field_strategies` が明示的に定義されていない場合にこのマッピングが使用される。

#### 共通フィールド

各戦略は以下のフィールドで構成される:

| フィールド | 説明 | 有効値 |
|---|---|---|
| `target_field` | 対象フィールドの検証戦略 | `valid`（有効値を使用）, `nonexistent`（存在しない値を使用） |
| `other_db` | 他テーブル参照フィールドの戦略 | `valid`, `nonexistent` |
| `file` | ファイル系フィールドの戦略 | `test_value`（テスト用の値を使用） |
| `checkbox` | チェックボックスの戦略 | `keep`（現在値を維持） |
| `free` | 自由入力フィールドの戦略 | `skip`（スキップ） |

#### 定義済み戦略

| 戦略名 | target_field | other_db | 用途 |
|---|---|---|---|
| `default` | `valid` | `valid` | 標準的な正常系テストデータ |
| `nonexistent` | `nonexistent` | `nonexistent` | 存在チェック異常系のテストデータ |
| `filter_2nd` | `valid` | `valid` | 2番目のフィルタ条件用テストデータ |

---

## 6. tag_branch_rules.yaml (v2 新規)

**パス:** `extensions/sap/config/tag_branch_rules.yaml`
**参照元ツール:** sap_path_enumerator.py

タグベースの分岐パターン定義。sap_path_enumerator.py が `process_definitions[].body` のステップタグから分岐パスを展開する際に使用する。

> **注意:** このファイルは v1 には存在しない。v2 で新規追加されたファイルである。

---

### 6.1 トップレベル設定

| フィールド | 型 | 値 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `schema_version` | 文字列 | `"1.0"` | スキーマバージョン | 将来の互換性管理用 |

---

### 6.2 rules セクション

各ルールはステップに付与されるタグ名と、そのタグから展開される分岐パターンを定義する。

#### ルール構造

| フィールド | 型 | 説明 | 変更時の影響 |
|---|---|---|---|
| `tag` | 文字列 | ステップに付与されるタグ名（正規表現対応） | sap_path_enumerator.py がステップタグとマッチさせる。タグ名を変更すると既存の process_definitions との整合性に注意 |
| `branches` | リスト | 展開される分岐パターンの配列 | 分岐を追加/削除するとパス列挙結果が変わる |

#### branches 配下の構造

| フィールド | 型 | 有効値 | 説明 | 変更時の影響 |
|---|---|---|---|---|
| `type` | 文字列 | `normal`, `abnormal`, `error` | 分岐タイプ | テストカバレッジの正常系・異常系分類に影響 |
| `label` | 文字列 | 任意 | 分岐ラベル（パス名に使用） | パス列挙結果のパス名が変わる |
| `description` | 文字列 | 任意 | 分岐の説明 | 人間が読む説明として出力される |

---

### 6.3 現在定義されているルール一覧 (全 11 ルール)

| tag | 分岐数 | 分岐パターン（type: label） | 概要 |
|---|---|---|---|
| EXIST | 2 | normal: exist_ok, abnormal: exist_ng | 存在チェック（マスタ/トランザクション） |
| BAPI | 3 | normal: check_ok, normal: post_success, abnormal: post_fail | BAPI/RFC 呼び出し（CHECK/POST/失敗） |
| VALIDATE | 2 | normal: valid, abnormal: invalid | バリデーション（入力チェック） |
| AUTH | 2 | normal: authorized, abnormal: unauthorized | 権限チェック |
| DB_READ | 2 | normal: data_found, abnormal: no_data | DB 読取（SELECT） |
| DB_WRITE | 2 | normal: write_ok, abnormal: write_fail | DB 更新（INSERT/UPDATE/DELETE） |
| FILE_OUTPUT | 2 | normal: file_ok, abnormal: file_fail | ファイル出力 |
| APPLOG | 1 | normal: log_ok | アプリケーションログ出力 |
| IDOC | 2 | normal: idoc_ok, abnormal: idoc_fail | IDoc 送信 |
| MAIL | 2 | normal: mail_ok, abnormal: mail_fail | メール送信 |
| DB_READ_MULTI | 3 | normal: all_found, normal: partial_found, abnormal: none_found | DB 複数テーブル読取（部分取得対応） |

---

## 設定ファイル相互依存マップ

各設定ファイルがどのツールから参照されるかの一覧。設定変更時に影響範囲を確認する際に使用する。

| 設定ファイル | 参照元ツール | 変更時の再テスト対象 |
|---|---|---|
| common_class_rules.yaml | sap_checklist_suggest.py, sap_common_class_lint.py, sap_quality_score.py | spec.md 生成結果, lint 結果, 品質スコア |
| test_perspective_master.yaml | sap_expand_traceability.py, sap_scenario_generator.py, sap_ac_generator.py | テストシナリオ生成結果, AC 生成結果, 分岐カバレッジ |
| quality_score_config.yaml | sap_quality_score.py | 品質スコア判定結果 |
| tool_evidence_registry.yaml | sap_tool_evidence_validator.py (stride_lint 経由) | lint のエビデンスチェック結果 |
| test_suggest_config.yaml | sap_test_suggest.py (deprecated) | テスト提案生成結果 |
| tag_branch_rules.yaml | sap_path_enumerator.py | 分岐パス列挙結果 |
