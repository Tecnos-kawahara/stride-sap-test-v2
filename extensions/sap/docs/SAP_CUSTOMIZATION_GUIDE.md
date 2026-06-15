# SAP 拡張 カスタマイズガイド (v2)

本ドキュメントは YAML 設定ファイルのカスタマイズ手順を説明します。

## はじめに

- このテンプレートはプロジェクト固有の要件に合わせてカスタマイズ可能です
- カスタマイズ可能な項目はすべて `extensions/sap/config/` の YAML ファイルに集約されています
- YAML ファイルの変更はテンプレート本体（Python/JS ツール）の修正不要です
- 設定ファイルを変更した場合、関連ツールが自動的に新しい設定を読み込みます

### カスタマイズは AI（Claude Code）に実行させること

**カスタマイズ作業は人間が YAML ファイルを手動編集するのではなく、Claude Code に指示して実行させてください。**

理由:
- YAML の構文エラー（インデント、クォート）を防げる
- 関連ツールの動作確認まで一貫して実行できる
- 既存ルールとの重複チェックや整合性検証を AI が自動で行える

**手順:**
1. このガイドの該当セクションを読み、やりたいことを把握する
2. わかる範囲の情報だけで Claude Code に「〇〇を追加して」と指示する（全部揃っていなくて OK）
3. 足りない情報があれば AI が質問してくるので、それに回答する
4. AI が YAML を編集し、関連ツールで動作確認まで実行する

各セクション冒頭の「AI に伝える情報」テーブルは、AI が質問してくる項目の一覧でもあります。事前に揃えておくとやり取りが減りますが、必須ではありません。

---

## 目次

1. [共通クラスの追加・変更](#1-共通クラスの追加変更) -- 共通クラスルール（ZCL_CMA_*）
2. [共通 Include の追加・変更](#2-共通-include-の追加変更) -- 共通 Include（ZCMAI*）
3. [テスト観点マスタの拡張](#3-テスト観点マスタの拡張) -- 処理種別・分岐パターン
4. [品質スコアの基準調整](#4-品質スコアの基準調整) -- 合格基準・減点ルール・SAP 固有ルール
5. [ABAP lint ルールの調整](#5-abap-lint-ルールの調整) -- 静的解析ルール・命名規約
6. [メッセージクラスの追加](#6-メッセージクラスの追加) -- T100 メッセージ
7. [タグ分岐ルールの追加・変更](#7-タグ分岐ルールの追加変更) -- ステップタグごとの分岐パス展開

---

## 1. 共通クラスの追加・変更

**AI に伝える情報:**

| 項目     | 物理名                   | 意味                                      | 具体例                                                         |
| ------ | --------------------- | --------------------------------------- | ----------------------------------------------------------- |
| クラス名   | `classes[].name`      | 共通クラスの ABAP クラス名                        | `ZCL_CMA_EXCEL_HANDLER`                                     |
| メソッド   | `classes[].methods[]` | クラスが提供するメソッド名とパラメータ（名前・方向・型・任意必須）       | `CREATE_WORKBOOK(iv_template: string, rv_result: bapiret2)` |
| 検出パターン | `trigger_pattern`     | どのような AC 記述のときにこのクラスを適用候補にするか（正規表現のヒント） | 「Excel」「帳票出力」「XLSX」を含む AC                                   |
| 禁止パターン | `forbidden_patterns`  | このクラスを使うべき場面で禁止する直接 API 呼び出し            | `CL_EHFND_XLSX`, `CL_FDT_XL_SPREADSHEET`                    |
| 適用条件   | `classes[].condition` | 同一ルール内で複数クラスを使い分ける場合の条件（省略可）            | 「ローカルファイル」vs「サーバーファイル」                                      |

**対象ファイル:** `extensions/sap/config/common_class_rules.yaml` の `common_class_rules` セクション

このファイルは以下のツールから参照されます:

| ツール | 用途 |
|--------|------|
| `sap_checklist_suggest.py` | spec.md の `common_class_applicability` に適用候補を出力 |
| `sap_common_class_lint.py` | ABAP ソースの禁止パターン検出 + パラメータ突合 |
| `sap_quality_score.py` | 共通クラス使用チェック（未使用は減点対象） |

### 新しい共通クラスを追加する手順

1. `common_class_rules.yaml` の `common_class_rules:` セクション末尾に新しいルールブロックを追加する
2. 以下のフィールドを定義する:

   | フィールド | 必須 | 説明 |
   |-----------|------|------|
   | `id` | はい | 一意の識別子（例: `"CC-EXCEL-01"`）。`CC-` プレフィックスを付けること |
   | `trigger_pattern` | はい | AI がこのクラスを適用候補として検出するための正規表現パターン |
   | `forbidden_patterns` | はい | このクラスを使うべき場面で禁止する直接 API 呼び出しのリスト（空リスト `[]` も可） |
   | `classes` | はい | 共通クラスのリスト。各クラスに `name`, `condition`, `methods` を定義 |
   | `classes[].methods[].parameters` | はい | 各パラメータの `name`, `direction`, `type` を定義。`optional: true` で任意パラメータ |

3. 動作確認: `sap_checklist_suggest.py` を実行し、spec.md の `common_class_applicability` に反映されるか確認する

### 既存クラスにメソッドを追加する手順

1. 対象クラスの `methods:` リストに新しいメソッドブロックを追加する
2. `name` にメソッド名、`parameters` にパラメータ一覧を定義する
3. `parameters` で定義されたパラメータのみ使用可能になる（未定義パラメータは lint エラー）

```yaml
# 既存の methods: リスト末尾に追加
          - name: NEW_METHOD_NAME
            parameters:
              - { name: iv_input, direction: IMPORTING, type: "string" }
              - { name: rv_result, direction: RETURNING, type: "bapiret2" }
```

### forbidden_patterns（禁止パターン）を追加する手順

1. 対象ルールの `forbidden_patterns:` リストに文字列を追加する
2. `sap_common_class_lint.py` が ABAP ソース中にこの文字列を検出するとエラーを報告する
3. 共通クラス自身のソース（`classes[].name` に該当するファイル）は lint 対象外になる

```yaml
    forbidden_patterns:
      - "CL_GUI_FRONTEND_SERVICES=>GUI_UPLOAD"
      - "CL_GUI_FRONTEND_SERVICES=>GUI_DOWNLOAD"
      - "MY_CUSTOM_FORBIDDEN_CALL"          # 追加
```

### 例: ZCL_CMA_EXCEL_HANDLER クラスを追加する場合

```yaml
  - id: "CC-EXCEL-01"
    trigger_pattern: "Excel|XLSX|スプレッドシート|帳票出力"
    forbidden_patterns:
      - "CL_EHFND_XLSX"
      - "CL_FDT_XL_SPREADSHEET"
    classes:
      - name: ZCL_CMA_EXCEL_HANDLER
        condition: "Excel ファイル操作"
        methods:
          - name: CREATE_WORKBOOK
            parameters:
              - { name: iv_template, direction: IMPORTING, type: "string", optional: true }
              - { name: rv_result, direction: RETURNING, type: "bapiret2" }
          - name: ADD_SHEET
            parameters:
              - { name: iv_sheet_name, direction: IMPORTING, type: "string" }
              - { name: it_data, direction: IMPORTING, type: "STANDARD TABLE" }
              - { name: rv_result, direction: RETURNING, type: "bapiret2" }
          - name: SAVE_AS
            parameters:
              - { name: iv_path, direction: IMPORTING, type: "string" }
              - { name: rv_result, direction: RETURNING, type: "bapiret2" }
```

---

## 2. 共通 Include の追加・変更

**AI に伝える情報:**

| 項目 | 物理名 | 意味 | 具体例 |
|------|--------|------|--------|
| Include 名 | `name` | ABAP Include プログラムのオブジェクト名 | `ZCMAI000113` |
| 説明 | `description` | Include の用途の日本語説明 | `利益センター共通画面(単一)` |
| 提供項目 | `provides` | この Include が選択画面に追加するパラメータ名 | `P_PRCTR (利益センター PARAMETERS)` |
| 検出パターン | `trigger_pattern` | どのような AC や選択画面定義のときに適用候補にするか | 「利益センター」「PRCTR」を含む AC |

**対象ファイル:** `extensions/sap/config/common_class_rules.yaml` の `common_include_rules` セクション

> **v2 変更点:** v1 では共通 Include ルールは別ファイルでしたが、v2 では `common_class_rules.yaml` 内の `common_include_rules` セクションに統合されています。

共通 Include は、選択画面に組織項目やファイルパス項目を配置するための共通部品です。
INCLUDE 文で取り込むことで、命名規約に準拠した PARAMETERS / SELECT-OPTIONS が自動的に追加されます。

### 現在定義済みの共通 Include

| ID | Include 名 | 用途 | 提供する画面項目 |
|----|-----------|------|-----------------|
| CI-ORG-01 | ZCMAI000101 | 会社コード共通画面(単一) | P_BUKRS |
| CI-ORG-02 | ZCMAI000102 | 販売エリア共通画面(単一) | P_VKORG, P_VTWEG, P_SPART |
| CI-ORG-03 | ZCMAI000103 | 販売組織共通画面(単一) | P_VKORG |
| CI-ORG-04 | ZCMAI000104 | 購買組織共通画面(単一) | P_EKORG |
| CI-ORG-05 | ZCMAI000105 | プラント共通画面(単一) | P_WERKS |
| CI-ORG-06 | ZCMAI000106 | 管理領域共通画面(単一) | P_KOKRS |
| CI-FILE-01 | ZCMAI000107 | ローカルファイル共通画面 | P_FILE |
| CI-FILE-02 | ZCMAI000108 | ローカルファイル(エラー)共通画面 | P_EFILE |
| CI-FILE-03 | ZCMAI000109 | AP ファイル共通画面 | P_DPATH, P_DFILE |
| CI-FILE-04 | ZCMAI000110 | AP ファイル(エラー)共通画面 | P_EDPATH, P_EDFILE |
| CI-TEST-01 | ZCMAI000111 | テスト実行共通画面 | P_TEST |
| CI-ALV-01 | ZCMAI000112 | ALV 共通画面 | P_VARI |

### 新しい共通 Include を追加する手順

1. `common_class_rules.yaml` の `common_include_rules:` セクション末尾に新しいルールを追加する
2. 以下のフィールドを定義する:

   | フィールド | 必須 | 説明 |
   |-----------|------|------|
   | `id` | はい | 一意の識別子。`CI-` プレフィックスを付けること |
   | `name` | はい | ABAP Include プログラム名（SAP 上のオブジェクト名） |
   | `description` | はい | 日本語での説明 |
   | `trigger_pattern` | はい | AI が適用候補として検出するための正規表現パターン |
   | `provides` | はい | この Include が提供する選択画面項目の概要 |

3. 動作確認: `sap_checklist_suggest.py` を実行し、spec.md の `common_include_applicability` に反映されるか確認する

### 例: 利益センターの共通画面 Include を追加する場合

```yaml
  - id: "CI-ORG-07"
    name: "ZCMAI000113"
    description: "利益センター共通画面(単一)"
    trigger_pattern: "利益センター|PRCTR|profit.?center"
    provides: "P_PRCTR (利益センター PARAMETERS)"
```

---

## 3. テスト観点マスタの拡張

**AI に伝える情報:**

| 項目 | 物理名 | 意味 | 具体例 |
|------|--------|------|--------|
| 処理種別 | `processing_types.<KEY>` | 新規追加 or 既存の処理種別名 | `WORKFLOW`（新規）、`IDOC`（既存に分岐追加） |
| 分岐パターン | `branches[].pattern` | 分岐の日本語名称 | `ワークフロー承認成功`, `ワークフロー却下` |
| 分岐タイプ | `branches[].type` | 正常系 or 異常系 | `normal` / `abnormal` |
| 期待結果 | `branches[].default_expected_result` | check 種別と値 | `message_type: S`, `wf_status: COMPLETED` |
| テスト観点 | `branches[].perspectives` | テスト観点コード（既存 or 新規定義） | `BRANCH_BIZ`, `ERROR_MSG` |

**対象ファイル:** `extensions/sap/config/test_perspective_master.yaml`

テスト観点マスタは、処理種別（processing_type）ごとの分岐パターンとテスト観点コード、デフォルト期待結果を定義します。
`sap_scenario_generator.py` がこのマスタを参照し、テストシナリオの `covers_ts` と `expected_result` を自動生成します。

### 現在定義済みの処理種別

AUTH, EXIST, F4HELP, FILE_READ, FILE_WRITE, VALIDATE, ALV, MSG, DB_READ, DB_WRITE, CALC, CONVERT, COMMIT, COMMIT_ROLLBACK, LOCK, LOG, PRINT, MAIL, RFC, BADI, BDC, IDOC, WF, OTHER

### 新しい処理種別を追加する手順

1. `test_perspective_master.yaml` の `processing_types:` セクションに新しい処理種別キーを追加する
2. `branches:` に分岐パターンのリストを定義する
3. 各分岐パターンに以下を定義する:

   | フィールド | 必須 | 説明 |
   |-----------|------|------|
   | `pattern` | はい | 分岐パターン名（日本語可） |
   | `type` | はい | `normal`（正常系）または `abnormal`（異常系） |
   | `perspectives` | はい | テスト観点コードのリスト |
   | `default_expected_result` | はい | デフォルトの期待結果（check 種別のリスト） |

4. 使用可能な check 種別: `message_type`, `message_text_contains`, `alv`, `alv_min_rows`, `screen_number`, `no_error`, `db_changed`, `file_output`, `log_output`, `print_output`, `idoc_status`, `wf_status`, `mail_sent`, `bdc_result`, `rfc_return`

### 例: EDI 連携用の IDOC 処理種別にカスタム分岐を追加する場合

既に `IDOC` 処理種別は定義済みですが、プロジェクト固有の分岐を追加する場合:

```yaml
  IDOC:
    branches:
    - pattern: 送受信成功
      type: normal
      perspectives:
      - BRANCH_BIZ
      default_expected_result:
      - check: message_type
        value: S
      - check: idoc_status
        idoc_type: __PLACEHOLDER__
        expected_status: __PLACEHOLDER__
    - pattern: 送受信失敗
      type: abnormal
      perspectives:
      - BRANCH_BIZ
      - ERROR_MSG
      - ERROR_LOGIC
      default_expected_result:
      - check: message_type
        value: E
      - check: idoc_status
        idoc_type: __PLACEHOLDER__
        expected_status: __PLACEHOLDER__
    # プロジェクト固有: ステータス戻し
    - pattern: IDoc ステータス戻し
      type: normal
      perspectives:
      - BRANCH_BIZ
      default_expected_result:
      - check: idoc_status
        idoc_type: __PLACEHOLDER__
        expected_status: __PLACEHOLDER__
```

### 既存処理種別に分岐パターンを追加する手順

1. 対象の処理種別の `branches:` リスト末尾に新しい分岐を追加する
2. `pattern`, `type`, `perspectives`, `default_expected_result` を定義する
3. 既存の分岐パターンと重複しないよう注意する

### デフォルト期待結果をカスタマイズする手順

1. 対象の分岐パターンの `default_expected_result:` を編集する
2. `check` フィールドに check 種別を指定し、必要な属性を追加する
3. `__PLACEHOLDER__` は AI が実行時に具体的な値に置換するため、テンプレートレベルでは `__PLACEHOLDER__` のままにしておいてよい

### perspective_expected_checks の拡張

`perspective_expected_checks:` セクションでは、テスト観点コードごとの正常系（`success`）・異常系（`failure`）の check と description を定義します。新しい perspective を追加した場合、ここにも対応するエントリを追加してください。

```yaml
perspective_expected_checks:
  MY_NEW_PERSPECTIVE:
    success:
      - { check: "no_error", description: "カスタム処理が正常に完了すること" }
    failure:
      - { check: "message_type", description: "カスタム処理のエラーが検出されること" }
```

---

## 4. 品質スコアの基準調整

**AI に伝える情報:**

| 項目 | 物理名 | 意味 | 具体例 |
|------|--------|------|--------|
| 合格基準点 | `pass_threshold` | 品質スコアの合格ライン（100点満点） | `75`（緩和）、`90`（厳格化） |
| カテゴリ減点上限 | `max_deductions.<category>` | カテゴリごとの最大減点数 | `error_handling: 30`, `runtime_efficiency: 20` |
| 個別ルール減点値 | 各カテゴリ内のルールキー | 1件あたりの減点数 | `select_without_subrc: 3`（5 -> 3 に緩和） |
| SAP 固有ルール | `sap_specific_rules[].deduction` | QR ルール 1 件あたりの減点数 | `QR-01: -5`（TABLES 文使用禁止） |
| 変更理由 | （YAML外） | なぜ変更するか（AI が妥当性を判断する材料） | 「新規 PJ 初期で既存コードの品質が低い」 |

**注意:** 新しい減点ルールの追加は `sap_quality_score.py` のコード修正も必要です。

**対象ファイル:** `extensions/sap/config/quality_score_config.yaml`

品質スコアは 100 点満点の減点方式で計算され、`sap_quality_score.py` が参照します。

### 合格基準点の変更

`pass_threshold` の値を変更します。デフォルトは `85` です。

```yaml
quality_score:
  pass_threshold: 80    # 例: 85 から 80 に緩和
```

プロジェクトの成熟度に応じて調整してください:
- 新規プロジェクト初期: `75` 程度に緩和することも検討
- 品質重視フェーズ: `90` に引き上げ

### カテゴリ別の最大減点の調整

v2 では **5 カテゴリ** で評価します（v1 の 4 カテゴリから `runtime_efficiency` が追加）。各カテゴリの減点上限を変更できます。5 カテゴリの合計が 100 点を超えないよう注意してください。

```yaml
  max_deductions:
    error_handling: 30       # エラーハンドリング漏れ
    naming_convention: 20    # 命名規約違反
    template_compliance: 15  # テンプレート準拠
    maintainability: 15      # 保守性
    runtime_efficiency: 20   # 実行効率（v2 新規）
```

### 減点ルールの調整

#### エラーハンドリング (`error_handling`)

| ルール | デフォルト | 説明 |
|--------|-----------|------|
| `select_without_subrc` | 5 | SELECT 後 SY-SUBRC チェックなし（1件あたり） |
| `common_class_without_check` | 5 | 共通クラス呼出し後 BAPIRET2 チェックなし（1件あたり） |
| `external_call_without_try` | 3 | TRY-CATCH なし外部呼出し（1件あたり） |
| `no_message_statement` | 10 | MESSAGE 文が 1 つもない |

#### 命名規約 (`naming_convention`)

遵守率に応じた段階的減点を `compliance_thresholds` で調整できます:

```yaml
    compliance_thresholds:
      - { min_ratio: 0.9, deduction: 0 }    # 90% 以上: 減点なし
      - { min_ratio: 0.7, deduction: 10 }   # 70-90%: -10 点
      - { min_ratio: 0.5, deduction: 20 }   # 50-70%: -20 点
      - { min_ratio: 0.0, deduction: 25 }   # 50% 未満: -25 点
```

| ルール | デフォルト | 説明 |
|--------|-----------|------|
| `inline_declaration` | 3 | `DATA(` インライン宣言（1件あたり） |
| `call_method_usage` | 5 | `CALL METHOD` 使用（1件あたり） |

#### テンプレート準拠 (`template_compliance`)

| ルール | デフォルト | 説明 |
|--------|-----------|------|
| `arbitrary_message` | 10 | `MESSAGE '任意テキスト'` 使用（1件あたり） |
| `unused_declared_class` | 10 | spec 宣言済み共通クラス未使用 |

> **v2 補足:** テンプレート準拠カテゴリでは、新版テンプレート（basic_design overlay + scenarios_template.yaml）への準拠もチェックされます。`catalogs.messages` の type は `error/warning/info/success` 形式（旧 `E/W/I/S/A` は非推奨）、`test_matrix` は `columns + test_cases` 構造（旧 `cases[]` は非推奨）です。

#### 実行効率 (`runtime_efficiency`) -- v2 新規カテゴリ

| ルール | デフォルト | 説明 |
|--------|-----------|------|
| `select_star` | 5 | `SELECT *` 使用（1件あたり）-- DB-AS 間の不要カラム転送 |
| `move_corresponding` | 3 | `MOVE-CORRESPONDING` 使用（1件あたり）-- 実行時フィールドマッチング |
| `broad_catch_cx_root` | 5 | `CATCH cx_root` 使用（1件あたり）-- 想定外例外の握りつぶし |
| `steps_per_form_exceeded` | 5 | 1 FORM 内に複数 @STEP が存在（1件あたり）-- メモリスコープ肥大化 |

#### 保守性 (`maintainability`)

コメント率の閾値を `comment_ratio` で調整できます:

```yaml
    comment_ratio:
      - { min_ratio: 0.10, deduction: 0 }    # 10% 以上: 減点なし
      - { min_ratio: 0.05, deduction: 5 }    # 5-10%: -5 点
      - { min_ratio: 0.00, deduction: 10 }   # 5% 未満: -10 点
```

| ルール | デフォルト | 説明 |
|--------|-----------|------|
| `long_method_threshold` | 100 | この行数を超えるメソッドを過長と判定 |
| `long_method_deduction` | 5 | 過長メソッド（1件あたり） |

### SAP 固有品質ルール (QR-01 -- QR-14)

v2 では 14 個の SAP 固有ルールが `sap_specific_rules` セクションに定義されています。各ルールは上記 5 カテゴリのいずれかに帰属し、合計減点はカテゴリ上限で頭打ちになります。

#### code_structure カテゴリの QR ルール

| ID | 減点 | 説明 |
|----|------|------|
| QR-01 | -5 | TABLES 文使用禁止 |
| QR-05 | -3 | 即時 CLEAR される中間テーブルコピー |
| QR-07 | -3 | コメント内に別プログラム名（ヘッダコメントと REPORT 文の不一致） |
| QR-08 | -2 | 連続空白行（3行以上） |
| QR-09 | -10 | ABAP Unit 圧縮クラス検出（テストクラス定義数 <= 2 かつメソッド定義数 >= 10） |
| QR-10 | -5 | イベントブロック内 lcl_ 直接呼出し（AT SELECTION-SCREEN / START-OF-SELECTION 内） |

#### error_handling カテゴリの QR ルール

| ID | 減点 | 説明 |
|----|------|------|
| QR-02 | -8 | BAPI RETURN 判定で type='A' 漏れ（WHERE type = 'E' に OR type = 'A' なし） |
| QR-03 | -8 | BAPI エラー後の全件記録 LOOP なし |
| QR-04 | -10 | save_log -> job_result 順序違反 |
| QR-12 | -8 | spec message_mapping type 不一致（MESSAGE 文の type と spec.md の定義が不一致） |
| QR-13 | -5 | 0件シナリオのステータスバー上書き（MESSAGE s 直後に PERFORM finish なし） |
| QR-14 | -5 | DISPLAY LIKE 句の type 誤認 |

#### naming カテゴリの QR ルール

| ID | 減点 | 説明 |
|----|------|------|
| QR-06 | -3 | MESSAGE 文中ハードコードフォーマット（TSV/CSV/EXCEL/FIX） |
| QR-11 | -3 | BAPI フィールドに非標準型使用（BAPICURR 系でない TYPE p の代入） |

### QR ルールの減点値を調整する

各 QR ルールの `deduction` 値を変更できます:

```yaml
  sap_specific_rules:
    - id: "QR-01"
      category: "code_structure"
      deduction: -3            # -5 から -3 に緩和
      pattern: "^\\s*TABLES[\\s:]"
      description: "TABLES文使用禁止"
```

### 新しい減点ルールを追加する場合の注意

YAML ファイルに新しいキーを追加するだけでは動作しません。`sap_quality_score.py` のコードに対応するチェックロジックを追加する必要があります。これはテンプレート開発者への依頼が必要です。

---

## 5. ABAP lint ルールの調整

**AI に伝える情報:**

| 項目 | 物理名 | 意味 | 具体例 |
|------|--------|------|--------|
| ルール名 | `rules.<rule_name>` | 有効化/無効化/設定変更したいルール | `commented_code`, `method_length` |
| 有効/無効 | `rules.<rule_name>: true/false` | ルールの ON/OFF | `commented_code: false`（無効化） |
| 重要度 | `rules.<rule_name>.severity` | エラーレベル | `Error`（ブロッカー）/ `Warning` / `Info` |
| 設定値 | ルール固有のプロパティ | ルールのパラメータ | `method_length.statements: 100`（上限変更） |
| 命名パターン | `object_naming.<type>` 等 | プロジェクト固有のプレフィックス/正規表現 | `clas: "^Z(CL\|CX)_PRJ_"` |

ルール一覧は https://rules.abaplint.org/ を参照。

**対象ファイル:** `extensions/sap/abaplint.json`

abaplint はオープンソースの ABAP 静的解析ツールです。利用可能なルール一覧は https://rules.abaplint.org/ を参照してください。

### ルールの有効化/無効化

ルールを無効化するには値を `false` に設定します:

```json
{
  "rules": {
    "commented_code": false,
    "unused_variables": {
      "severity": "Warning"
    }
  }
}
```

新しいルールを有効化するには、`rules` オブジェクトにキーを追加します:

```json
{
  "rules": {
    "new_rule_name": true,
    "another_rule": {
      "severity": "Warning"
    }
  }
}
```

### severity の変更

各ルールの `severity` を変更できます。使用可能な値:

| severity | 意味 |
|----------|------|
| `"Error"` | エラー（ビルドブロッカー。修正必須） |
| `"Warning"` | 警告（修正推奨） |
| `"Info"` | 情報（参考レベル） |

```json
"method_length": {
  "severity": "Error",
  "statements": 80,
  "errorWhenExceeding": 100,
  "checkForms": true
}
```

### 命名規約パターンの変更

`object_naming`, `local_variable_names`, `class_attribute_names`, `method_parameter_names` 等のルールで命名パターンを変更できます。パターンは正規表現です。

#### オブジェクト命名規約 (`object_naming`)

現在のデフォルト:

| オブジェクト | パターン | 例 |
|-------------|---------|-----|
| クラス (`clas`) | `^Z(CL\|CX)_[A-Z]{2,3}_` | ZCL_CMA_xxx, ZCX_SD_xxx |
| インターフェース (`intf`) | `^ZIF_[A-Z]{2,3}_` | ZIF_CMA_xxx |
| プログラム (`prog`) | `^[ZY][A-Z0-9_]+$` | ZCMA_REPORT001 |
| 汎用モジュールグループ (`fugr`) | `^Z[A-Z]{3}\d{4}$` | ZCMA0001 |
| テーブル (`tabl`) | `^Z[A-Z]{2,3}_` | ZCMA_TABLE |
| メッセージクラス (`msag`) | `^Z[A-Z]{3}` | ZCMA |
| トランザクション (`tran`) | `^Z[A-Z]{3}\d{4}` | ZCMA0001 |

プロジェクト固有のプレフィックスに変更する場合:

```json
"object_naming": {
  "severity": "Error",
  "patternKind": "required",
  "clas": "^Z(CL|CX)_PRJ_",
  "prog": "^ZPRJ[A-Z0-9_]+$"
}
```

#### ローカル変数命名規約 (`local_variable_names`)

現在のデフォルト:

| 種別 | パターン | 例 |
|------|---------|-----|
| Data | `^(LD[FST]_\|LDT_R_\|LR[ODBXI]_).*$` | LDS_data, LDT_table, LRO_ref |
| Constant | `^LC[FS]_.*$` | LCS_const |
| Field Symbol | `^<LD[FST]_.*>$` | <LDS_work> |

#### メソッドパラメータ命名規約 (`method_parameter_names`)

現在のデフォルト:

| direction | パターン | 例 |
|-----------|---------|-----|
| IMPORTING | `^PI[FSTR]_.*$` | PIS_input |
| EXPORTING | `^PO[FSTR]_.*$` | POS_output |
| CHANGING | `^PC[FSTR]_.*$` | PCS_change |
| RETURNING | `^PR[FSTR]_.*$` | PRS_result |

### その他の主要ルール調整

| ルール | 現在の設定 | 調整ポイント |
|--------|-----------|-------------|
| `line_length` | 120 文字 | プロジェクト標準に合わせて変更 |
| `method_length` | 80 文 (Warning), 100 文 (Error) | `statements` と `errorWhenExceeding` を調整 |
| `nesting` | depth: 2 | ネスト深度の上限 |
| `cyclomatic_complexity` | max: 5 | 循環的複雑度の上限 |
| `sequential_blank` | 4 行 | 連続空白行の上限 |

---

## 6. メッセージクラスの追加

**AI に伝える情報:**

| 項目 | 物理名 | 意味 | 具体例 |
|------|--------|------|--------|
| メッセージクラス ID | `message_class` | SAP T100 テーブルのメッセージクラス名 | `ZPRJ`, `ZCMA01` |
| 作成状況 | （YAML外） | SAP 上で SE91 にて作成済みかどうか | 「作成済み」/「未作成（人間が SE91 で事前作成必要）」 |
| 対象 feature | （コマンド引数） | メッセージを紐づける feature ディレクトリ | `specs/tsv_import_aggregation/` |

**対象ファイル:** 各機能の `basic_design.md` の `message_class` フィールド

`sap_message_suggest.py` が SAP の T100 テーブルからメッセージを取得し、spec.md に反映します。

### プロジェクトで新しいメッセージクラスを使う場合の手順

1. SAP 上で新しいメッセージクラスを作成する（トランザクション SE91）
2. `basic_design.md` の `message_class` フィールドに新しいメッセージクラス ID を設定する

```yaml
message_class: "ZPRJ"    # プロジェクト固有のメッセージクラス
```

3. `sap_message_suggest.py` を実行すると、T100 テーブルから該当メッセージクラスのメッセージ一覧が取得される
4. spec.md の messages セクションに自動的に反映される

### 注意事項

- 共通クラスルール `CC-MSG-01` により、`MESSAGE '任意テキスト'` の直接記述は禁止されています
- 必ず T100 テーブルに登録されたメッセージ番号を使用してください
- メッセージクラスの命名規約は `abaplint.json` の `object_naming.msag` で定義されています（デフォルト: `^Z[A-Z]{3}`）

---

## 7. タグ分岐ルールの追加・変更

**AI に伝える情報:**

| 項目 | 物理名 | 意味 | 具体例 |
|------|--------|------|--------|
| タグ名 | `rules[].tag` | ステップに付与されるタグ名（正規表現対応） | `BAPI`, `DB_READ`, `FILE_OUTPUT` |
| 分岐タイプ | `branches[].type` | 分岐の種別 | `normal`（正常系）/ `abnormal`（異常系）/ `error`（エラー系） |
| 分岐ラベル | `branches[].label` | パス名に使用されるラベル（英語） | `check_ok`, `post_fail`, `no_data` |
| 分岐説明 | `branches[].description` | 分岐の日本語説明 | `BAPI CHECK 成功`, `該当データなし（0件）` |

**対象ファイル:** `extensions/sap/config/tag_branch_rules.yaml`

`sap_path_enumerator.py` が `process_definitions[].body` のステップタグからこのファイルを参照し、分岐パスを自動展開します。

### 現在定義済みのタグルール

| タグ | 分岐数 | 分岐パターン |
|------|--------|-------------|
| `EXIST` | 2 | exist_ok（正常）, exist_ng（異常） |
| `BAPI` | 3 | check_ok（正常）, post_success（正常）, post_fail（異常） |
| `VALIDATE` | 2 | valid（正常）, invalid（異常） |
| `AUTH` | 2 | authorized（正常）, unauthorized（異常） |
| `DB_READ` | 2 | data_found（正常）, no_data（異常） |
| `DB_WRITE` | 2 | write_ok（正常）, write_fail（異常） |
| `FILE_OUTPUT` | 2 | file_ok（正常）, file_fail（異常） |
| `APPLOG` | 1 | log_ok（正常） |
| `IDOC` | 2 | idoc_ok（正常）, idoc_fail（異常） |
| `MAIL` | 2 | mail_ok（正常）, mail_fail（異常） |
| `DB_READ_MULTI` | 3 | all_found（正常）, partial_found（正常）, none_found（異常） |

### 新しいタグルールを追加する手順

1. `tag_branch_rules.yaml` の `rules:` リスト末尾に新しいルールブロックを追加する
2. 以下のフィールドを定義する:

   | フィールド | 必須 | 説明 |
   |-----------|------|------|
   | `tag` | はい | ステップタグ名。大文字英字 + アンダースコア推奨 |
   | `branches` | はい | 分岐パターンのリスト |
   | `branches[].type` | はい | `normal`（正常系）/ `abnormal`（異常系）/ `error`（エラー系） |
   | `branches[].label` | はい | 英字のラベル名（パス展開に使用） |
   | `branches[].description` | はい | 日本語の説明文 |

3. 動作確認: `sap_path_enumerator.py` を実行し、当該タグを含むステップで分岐パスが正しく展開されるか確認する

### 既存タグルールに分岐を追加する手順

1. 対象タグの `branches:` リスト末尾に新しい分岐を追加する
2. `type`, `label`, `description` を定義する
3. `label` が既存の分岐と重複しないよう注意する

### 例: ワークフロー用タグを追加する場合

```yaml
  # ワークフロー承認
  - tag: "WF_APPROVE"
    branches:
      - type: normal
        label: "approved"
        description: "ワークフロー承認済み"
      - type: normal
        label: "rejected"
        description: "ワークフロー却下"
      - type: abnormal
        label: "timeout"
        description: "ワークフロー承認期限切れ"
```

### 例: 既存の DB_READ に部分取得分岐を追加する場合

```yaml
  - tag: "DB_READ"
    branches:
      - type: normal
        label: "data_found"
        description: "データ取得成功（1件以上）"
      - type: abnormal
        label: "no_data"
        description: "該当データなし（0件）"
      - type: normal
        label: "partial_data"
        description: "一部データのみ取得（部分一致）"   # 追加
```

---

## カスタマイズ時の注意事項

### YAML の構文エラーに注意

- インデントはスペース 2 つを使用すること（タブは不可）
- 文字列に `:`, `#`, `{`, `}`, `[`, `]` を含む場合はクォートで囲むこと
- 日本語文字列は基本的にクォートなしで記述可能だが、特殊文字を含む場合はダブルクォートを使用

```yaml
# OK
trigger_pattern: "権限|AUTHORITY|会社コード"

# NG（: を含むためエラー）
description: 注意: これはエラーになる

# OK
description: "注意: これはクォートで囲めばOK"
```

### 変更後は必ず関連ツールを実行して動作確認

| 変更した設定ファイル | 確認に使うツール |
|---------------------|-----------------|
| `common_class_rules.yaml`（共通クラス） | `sap_checklist_suggest.py`, `sap_common_class_lint.py` |
| `common_class_rules.yaml`（共通 Include） | `sap_checklist_suggest.py` |
| `test_perspective_master.yaml` | `sap_scenario_generator.py` |
| `quality_score_config.yaml` | `sap_quality_score.py` |
| `abaplint.json` | abaplint（`abaplint_wrapper`） |
| `tag_branch_rules.yaml` | `sap_path_enumerator.py` |

### テンプレートバージョンアップ時のマージ競合

設定ファイルをカスタマイズした状態でテンプレートをバージョンアップすると、マージ競合が発生する可能性があります。その場合は以下の手順で対応してください:

1. バージョンアップ前にカスタマイズ箇所を一覧化しておく
2. マージ競合が発生したら、テンプレート側の変更内容を確認し、カスタマイズを再適用する
3. 詳細は [migration_from_v1.md](migration_from_v1.md) を参照

---

## 関連ドキュメント

- [SAP_TOOL_DEVELOPMENT_GUIDE.md](SAP_TOOL_DEVELOPMENT_GUIDE.md) -- ツール開発ガイド
- [SAP_TROUBLESHOOTING.md](SAP_TROUBLESHOOTING.md) -- トラブルシューティング
