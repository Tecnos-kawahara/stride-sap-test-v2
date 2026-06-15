# ABAP コーディングパターン

AI は対象の処理を実装する際、本ドキュメントのパターンに従うこと。
ここに無い処理は自身の判断で実装してよいが、既存パターンとスタイルを統一すること。

> **注意**: 共通クラスの詳細ルールは `extensions/sap/config/common_class_rules.yaml` を参照。
> 本ドキュメントは人間可読な API リファレンスとして、メソッドシグネチャと呼び出しパターンを提供する。

---

## ABAP 命名制約

| 項目 | 制限 | 備考 |
|------|------|------|
| メソッド名 | **最大30文字** | 超過すると activation 失敗。テストメソッド名（`ut01_xxxx`）は特に注意 |
| 変数名 | 最大30文字 | ローカル変数・パラメータ含む |
| クラス名 | 最大30文字 | `lcl_` プレフィックス分を考慮 |
| テーブル型名 | 最大30文字 | TYPES 定義 |
| RANGE OF パラメータ | **TYPES で事前定義必須** | `IMPORTING ir_xxx TYPE RANGE OF yyy` はインライン不可。ADT API 経由のアップロードで拒否される。`TYPES tyr_xxx TYPE RANGE OF yyy` -> `IMPORTING it_xxx TYPE tyr_xxx` とすること |

> **教訓**: `activate.js` は activation 結果の `success` フラグを検証する。30文字超過エラーは構文エラーとして報告される。
> **教訓**: メソッドパラメータに `RANGE OF` をインラインで記述すると、ABAP 構文としては有効だが ADT REST API 経由のアップロード時に「保存操作中にエラーが発生しました」で拒否される。必ず TYPES で事前定義すること。

---

## abaplint ファイル命名規則

| オブジェクト種別 | ファイル拡張子 |
|----------------|--------------|
| クラス本体 | `.clas.abap` |
| クラステスト | `.clas.testclasses.abap` |
| プログラム | `.prog.abap` |
| 汎用モジュールグループ | `.fugr.abap` |
| インターフェース | `.intf.abap` |

### テストクラスの配置ルール

| オブジェクト種別 | テストクラスの配置 | 理由 |
|----------------|------------------|------|
| **プログラム** (`.prog.abap`) | **メインソースの末尾に含める** | プログラムのテストインクルードは同一ソース内。別ファイルにするとアップロードエラー |
| **グローバルクラス** (`.clas.abap`) | **別ファイル** (`.clas.testclasses.abap`) に分離 | activate.js が自動検出してアップロード |

**プログラムのテストクラスを別ファイルに分離してはならない。必ずメインソースの末尾に記述すること。**

---

## 選択画面パラメータのデフォルト値

### 原則: 静的デフォルト値は DEFAULT で設定する

選択画面パラメータの初期値が定数（リテラルや SY 変数の単純参照）の場合、
`PARAMETERS` / `SELECT-OPTIONS` 文の `DEFAULT` 句を使用する。
`INITIALIZATION` イベントでの設定は、実行時に動的計算が必要な場合のみ使用する。

```abap
" === 推奨: DEFAULT を使用 ===
PARAMETERS: p_bukrs TYPE bukrs   DEFAULT '1000',
            p_gjahr TYPE gjahr   DEFAULT '2026',
            p_test  TYPE xfeld   DEFAULT 'X'.
SELECT-OPTIONS: s_budat FOR bkpf-budat DEFAULT sy-datum.

" === 許容: 動的計算が必要な場合のみ INITIALIZATION ===
PARAMETERS: p_monat TYPE monat.
INITIALIZATION.
  p_monat = sy-datum+4(2).  " 当月を動的に算出
```

```abap
" === NG: 静的リテラルを INITIALIZATION で設定 ===
PARAMETERS: p_bukrs TYPE bukrs.
INITIALIZATION.
  p_bukrs = '1000'.  " -> PARAMETERS の DEFAULT '1000' で書くべき
```

### 判断基準

| デフォルト値 | 方式 | 例 |
|------------|------|-----|
| リテラル定数 | `DEFAULT` | `DEFAULT '1000'` |
| SY 変数（単純参照） | `DEFAULT` | `DEFAULT sy-datum` |
| SY 変数（加工必要） | `INITIALIZATION` | `sy-datum+4(2)` |
| DB 読み取り・ユーザー別値 | `INITIALIZATION` | `SELECT SINGLE ... WHERE uname = sy-uname` |

---

## メッセージ収集 -> 一括出力パターン

メッセージは処理箇所で **BAPIRET2 テーブルに収集** し、処理末尾で **一括出力** する。
共通クラスの `rv_result`（BAPIRET2）もそのまま同じテーブルに追加する。

```abap
" === メッセージ収集用（プログラム冒頭で定義） ===
DATA: gt_messages TYPE STANDARD TABLE OF bapiret2,
      gs_message  TYPE bapiret2.

" === 処理中: メッセージを収集 ===

" 共通クラスの戻り値を収集
lo_check->auth_company(
  EXPORTING iv_bukrs  = lv_bukrs
            iv_actvt  = '03'
  IMPORTING rv_result = gs_message ).
IF gs_message IS NOT INITIAL.
  APPEND gs_message TO gt_messages.
  IF gs_message-type CA 'EA'.
    " エラー -> 後続処理を中断、メッセージ出力へジャンプ
  ENDIF.
ENDIF.

" 独自エラーも同じテーブルに収集（T100 メッセージクラスを使用）
SELECT bukrs, belnr, gjahr, dmbtr
  FROM ztable INTO TABLE @lt_data
  WHERE bukrs = @lv_bukrs.
IF sy-subrc <> 0.
  APPEND VALUE bapiret2(
    type = 'E'  id = 'ZMSG'  number = '001'
    message_v1 = lv_key ) TO gt_messages.
ENDIF.

" === 処理末尾: 一括出力 ===
LOOP AT gt_messages INTO gs_message.
  MESSAGE ID gs_message-id TYPE gs_message-type NUMBER gs_message-number
    WITH gs_message-message_v1 gs_message-message_v2
         gs_message-message_v3 gs_message-message_v4.
ENDLOOP.
```

### ルール

- メッセージは即時出力せず、`gt_messages`（BAPIRET2 テーブル）に収集する
- 共通クラスの `rv_result` は `IS NOT INITIAL` で判定し、そのまま APPEND する
- E/A（エラー）発生時のデフォルト動作は **処理中断 -> 一括出力**（要件で続行指定がある場合は従う）
- 出力方式のデフォルトは `MESSAGE` ループ（要件で ALV メッセージリスト等が指定されればそれに従う）

---

## BAPI 呼出しパターン

SAP 標準 BAPI を使用して DB 更新を行う場合のパターン。

```abap
" === BAPI 呼出し -> RETURN チェック -> COMMIT/ROLLBACK ===
DATA: lt_return TYPE TABLE OF bapiret2.

" BAPI 呼出し
CALL FUNCTION 'BAPI_SALESORDER_CREATEFROMDAT2'
  EXPORTING
    order_header_in = ls_header
  TABLES
    return          = lt_return
    order_items_in  = lt_items.

" RETURN テーブルからエラーを検出
LOOP AT lt_return INTO DATA(ls_return) WHERE type CA 'EA'.
  APPEND ls_return TO gt_messages.
ENDLOOP.

" エラー有無で COMMIT / ROLLBACK
IF line_exists( lt_return[ type = 'E' ] )
   OR line_exists( lt_return[ type = 'A' ] ).
  CALL FUNCTION 'BAPI_TRANSACTION_ROLLBACK'.
ELSE.
  CALL FUNCTION 'BAPI_TRANSACTION_COMMIT'
    EXPORTING
      wait = 'X'.
ENDIF.
```

### ルール

- BAPI の RETURN テーブルは必ずチェックする（E/A があれば ROLLBACK）
- COMMIT には `BAPI_TRANSACTION_COMMIT`（`wait = 'X'`）を使用する（`COMMIT WORK` ではない）
- ROLLBACK には `BAPI_TRANSACTION_ROLLBACK` を使用する
- RETURN のメッセージはメッセージ収集テーブル（`gt_messages`）に追加する

---

## 汎用モジュール（Function Module）パターン

### ソースコード形式

ADT API で汎用モジュールのソースをアップロードする場合、**ABAP 宣言構文形式**で記述する。
`*"` コメントブロック形式は ADT API で拒否されるため使用禁止。

```abap
" OK: ABAP 宣言構文形式（ADT API で使用する形式）
FUNCTION z_my_function_module
  IMPORTING
    i_bukrs TYPE bukrs
    i_belnr TYPE belnr_d
  CHANGING
    c_result TYPE ztable_type
  EXCEPTIONS
    no_data.

  " ソースコード本体

ENDFUNCTION.
```

```abap
" NG: *" コメントブロック形式（ADT API で拒否される）
FUNCTION z_my_function_module.
*"----------------------------------------------------------------------
*"*"Lokale Schnittstelle:
*"  IMPORTING
*"     VALUE(I_BUKRS) TYPE  BUKRS
*"----------------------------------------------------------------------
```

### ツールコマンド

```bash
# 汎用グループ作成
node extensions/sap/tools/create_object.js function_group ZFGR_SAMPLE "説明" --package $TMP

# 汎用モジュール作成（--parent で親グループを指定）
node extensions/sap/tools/create_object.js function_module Z_MY_FM "説明" --parent ZFGR_SAMPLE --package $TMP

# ソースアップロード + 有効化（--fugr で親グループを指定）
node extensions/sap/tools/activate.js src/z_my_fm.fugr.abap --fugr ZFGR_SAMPLE --name Z_MY_FM

# ソース取得（--fugr で親グループを指定）
node extensions/sap/tools/pull.js Z_MY_FM function_module --fugr ZFGR_SAMPLE
```

### 注意事項

- パラメータ定義（IMPORTING/EXPORTING/CHANGING/TABLES/EXCEPTIONS）はソース内の宣言構文で定義される。SE37 での個別設定は不要
- DDIC オブジェクト（構造・テーブル型）をパラメータに使用する場合、先に SE11 で作成・有効化しておくこと
- 金額フィールド（CURR 型: DMBTR, WRBTR 等）を持つ構造は、通貨参照フィールドの設定が必須

### 内容説明テキスト（description）の変更

ADT REST API ではオブジェクトの内容説明テキストを作成後に変更できない（API 未実装）。
変更が必要な場合は `update_description.js` を使用する。

```bash
node extensions/sap/tools/update_description.js --type function_module --name Z_MY_FM --description "新しい説明"
node extensions/sap/tools/update_description.js --type program --name ZREPORT --description "新しいタイトル"
node extensions/sap/tools/update_description.js --type class --name ZCL_MY_CLASS --description "新しい説明"
```

このツールは SAP GUI スクリプティング（COM API）経由で対象トランザクション（SE37/SE38/SE24）の description フィールドを直接更新する。

---

## 共通クラス（Common Class Registry）

AI は以下の処理を実装する際、対応する共通クラスのメソッドを**必ず使用**すること。
インラインでの同等処理実装は禁止。全メソッドは `BAPIRET2` 型の `rv_result` を返却するため、
呼び出し側は `rv_result-type` でエラーハンドリングすること。

> **注意**: 共通クラスは Read-Only（ルール S4）。修正が必要な場合は人間にエスカレーションすること。
> **ルール定義**: `extensions/sap/config/common_class_rules.yaml`

---

### ローカルファイル系（ZCL_CMA_LOCAL_FILE）

| トリガー | メソッド | 説明 |
|----------|----------|------|
| ローカルファイルパス入力のF4ヘルプ | F4HELP_PATH_IN | ファイル選択ダイアログ（入力用） |
| ローカルファイルパス出力のF4ヘルプ | F4HELP_PATH_OUT | ファイル選択ダイアログ（出力用） |
| ローカルディレクトリのF4ヘルプ | F4HELP_DIRECTORY | ディレクトリ選択ダイアログ |
| ローカルTSVファイル読み込み | INPUT_TSV | TSVファイル入力 |
| ローカルCSVファイル読み込み | INPUT_CSV | CSVファイル入力 |
| ローカル固定長ファイル読み込み | INPUT_FIX | 固定長ファイル入力 |
| ローカルExcelファイル読み込み | INPUT_EXCEL | Excelファイル入力 |
| ローカルTSVファイル書き込み | OUTPUT_TSV | TSVファイル出力 |
| ローカルCSVファイル書き込み | OUTPUT_CSV | CSVファイル出力 |
| ローカル固定長ファイル書き込み | OUTPUT_FIX | 固定長ファイル出力 |
| ローカルExcelファイル書き込み | OUTPUT_EXCEL | Excelファイル出力 |
| 構造名からレイアウト取得 | GET_LAYOUT | 固定長ファイル用フィールド幅テーブル取得 |

#### パラメータ定義

```abap
" F4ヘルプ系
METHODS f4help_path_in  IMPORTING iv_prompt TYPE string OPTIONAL CHANGING cv_file_path TYPE string.
METHODS f4help_path_out IMPORTING iv_prompt TYPE string OPTIONAL CHANGING cv_file_path TYPE string.
METHODS f4help_directory IMPORTING iv_prompt TYPE string OPTIONAL CHANGING cv_directory TYPE string.

" ファイル入力系（ty_rows = STANDARD TABLE OF ty_row, ty_row = STANDARD TABLE OF string）
METHODS input_tsv   IMPORTING iv_path TYPE string CHANGING rt_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS input_csv   IMPORTING iv_path TYPE string CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS input_fix   IMPORTING iv_path TYPE string it_layout TYPE ty_layout OPTIONAL
                    CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS input_excel IMPORTING iv_path TYPE string iv_sheet TYPE string OPTIONAL
                    CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.

" ファイル出力系
METHODS output_tsv   IMPORTING iv_path TYPE string it_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS output_csv   IMPORTING iv_path TYPE string it_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS output_fix   IMPORTING iv_path TYPE string it_data TYPE ty_rows it_layout TYPE ty_layout OPTIONAL
                     RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS output_excel IMPORTING iv_path TYPE string iv_sheet TYPE string DEFAULT 'Sheet1'
                               it_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.

METHODS get_layout   IMPORTING iv_structure TYPE dd02l-tabname RETURNING VALUE(rt_layout) TYPE ty_layout.
```

#### 呼び出しパターン例

```abap
" F4ヘルプ（選択画面 AT SELECTION-SCREEN ON VALUE-REQUEST）
DATA(lo_local) = NEW zcl_cma_local_file( ).
lo_local->f4help_path_in( CHANGING cv_file_path = p_file ).

" ファイル読み込み + エラーハンドリング
DATA(lt_data) = VALUE zcl_cma_local_file=>ty_rows( ).
DATA(ls_result) = lo_local->input_csv( EXPORTING iv_path = p_file CHANGING ct_file_data = lt_data ).
IF ls_result-type = 'E'.
  MESSAGE ls_result-message TYPE 'E'.
ENDIF.
```

---

### サーバーファイル系（ZCL_CMA_AP_FILE）

| トリガー | メソッド | 説明 |
|----------|----------|------|
| サーバーTSVファイル読み込み | INPUT_TSV | 論理パス/ファイル指定TSV入力 |
| サーバーCSVファイル読み込み | INPUT_CSV | 論理パス/ファイル指定CSV入力 |
| サーバー固定長ファイル読み込み | INPUT_FIX | 論理パス/ファイル指定固定長入力 |
| サーバーExcelファイル読み込み | INPUT_EXCEL | 論理パス/ファイル指定Excel入力 |
| サーバーTSVファイル書き込み | OUTPUT_TSV | 論理パス/ファイル指定TSV出力 |
| サーバーCSVファイル書き込み | OUTPUT_CSV | 論理パス/ファイル指定CSV出力 |
| サーバー固定長ファイル書き込み | OUTPUT_FIX | 論理パス/ファイル指定固定長出力 |
| サーバーExcelファイル書き込み | OUTPUT_EXCEL | 論理パス/ファイル指定Excel出力 |
| 構造名からレイアウト取得 | GET_LAYOUT | 固定長ファイル用フィールド幅テーブル取得 |

#### パラメータ定義

```abap
METHODS input_tsv   IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_encord TYPE char4 OPTIONAL
                    CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS input_csv   IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_encord TYPE char4 OPTIONAL
                    CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS input_fix   IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_encord TYPE char4 OPTIONAL
                              it_layout TYPE ty_layout OPTIONAL
                    CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS input_excel IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_sheet TYPE string OPTIONAL
                    CHANGING ct_file_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.

METHODS output_tsv   IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_encord TYPE char4 OPTIONAL
                               it_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS output_csv   IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_encord TYPE char4 OPTIONAL
                               it_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS output_fix   IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_encord TYPE char4 OPTIONAL
                               it_data TYPE ty_rows it_layout TYPE ty_layout OPTIONAL
                     RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS output_excel IMPORTING iv_path TYPE pathintern iv_file TYPE fileintern iv_sheet TYPE string DEFAULT 'Sheet1'
                               it_data TYPE ty_rows RETURNING VALUE(rv_result) TYPE bapiret2.

METHODS get_layout   IMPORTING iv_structure TYPE dd02l-tabname RETURNING VALUE(rt_layout) TYPE ty_layout.
```

#### 呼び出しパターン例

```abap
DATA(lo_ap) = NEW zcl_cma_ap_file( ).
DATA(lt_data) = VALUE zcl_cma_ap_file=>ty_rows( ).
DATA(ls_result) = lo_ap->input_csv(
  EXPORTING iv_path = 'ZPATH01' iv_file = 'ZFILE01' iv_encord = 'UTF8'
  CHANGING ct_file_data = lt_data ).
IF ls_result-type = 'E'.
  " エラー処理（BAPIRET2にメッセージが格納済み）
ENDIF.
```

---

### 組織チェック系（ZCL_CMA_COMMON_CHECK）

| トリガー | メソッド | 説明 |
|----------|----------|------|
| 会社コード権限チェック | AUTH_COMPANY | AUTHORITY-CHECK 会社コード |
| 販売エリア権限チェック | AUTH_SALESAREA | AUTHORITY-CHECK 販売エリア |
| 購買組織権限チェック | AUTH_PUR_ORG | AUTHORITY-CHECK 購買組織 |
| プラント権限チェック | AUTH_PLANT | AUTHORITY-CHECK プラント |
| 会社コード存在チェック | EXIST_COMPANY | T001参照 |
| 販売エリア存在チェック | EXIST_SALESAREA | TVKO/TVTW/TSPA参照 |
| 購買組織存在チェック | EXIST_PUR_ORG | T024E参照 |
| プラント存在チェック | EXIST_PLANT | T001W参照 |

#### パラメータ定義

```abap
" 権限チェック系
METHODS auth_company    IMPORTING iv_bukrs TYPE bukrs iv_activity TYPE char2 RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS auth_salesarea  IMPORTING iv_salesorg TYPE vkorg iv_salesdist TYPE vtweg iv_salesspart TYPE spart iv_activity TYPE char2 RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS auth_pur_org    IMPORTING iv_porg TYPE ekorg iv_activity TYPE char2 RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS auth_plant      IMPORTING iv_plant TYPE werks_d iv_activity TYPE char2 RETURNING VALUE(rv_result) TYPE bapiret2.

" 存在チェック系
METHODS exist_company    IMPORTING iv_bukrs TYPE bukrs RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS exist_salesarea  IMPORTING iv_salesorg TYPE vkorg iv_salesdist TYPE vtweg iv_salesspart TYPE spart RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS exist_pur_org    IMPORTING iv_porg TYPE ekorg RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS exist_plant      IMPORTING iv_plant TYPE werks_d RETURNING VALUE(rv_result) TYPE bapiret2.
```

#### 呼び出しパターン例

```abap
DATA(lo_check) = NEW zcl_cma_common_check( ).

" 権限チェック（Activity: '03'=照会, '01'=登録, '02'=変更）
DATA(ls_auth) = lo_check->auth_company( iv_bukrs = p_bukrs iv_activity = '03' ).
IF ls_auth-type = 'E'.
  MESSAGE ls_auth-message TYPE 'E'.
ENDIF.

" 存在チェック
DATA(ls_exist) = lo_check->exist_plant( iv_plant = p_werks ).
IF ls_exist-type = 'E'.
  MESSAGE ls_exist-message TYPE 'E'.
ENDIF.
```

---

### ALV系（ZCL_CMA_ALV_GENERIC + ZCL_CMA_ALV_HANDLER + ZIF_CMA_ALV_CALLBACK）

CL_SALV_TABLE をラップし、ALV 表示設定を簡略化する汎用クラス群。

| トリガー | クラス | メソッド | 説明 |
|----------|--------|----------|------|
| ALV データ表示 | ZCL_CMA_ALV_GENERIC | CONSTRUCTOR | データ参照で SALV 生成 |
| 列設定一括 | ZCL_CMA_ALV_GENERIC | SET_COLUMNS | TY_COLUMN_SETTINGS で一括設定 |
| 列テキスト設定 | ZCL_CMA_ALV_GENERIC | SET_COLUMN_TEXT | 短/中/長テキスト設定 |
| ホットスポット | ZCL_CMA_ALV_GENERIC | SET_HOTSPOT | 列をリンク表示に設定 |
| 列非表示 | ZCL_CMA_ALV_GENERIC | HIDE_COLUMN | 列を非表示 |
| 列幅自動調整 | ZCL_CMA_ALV_GENERIC | SET_OPTIMIZE | 全列幅を自動最適化 |
| ゼブラ表示 | ZCL_CMA_ALV_GENERIC | SET_ZEBRA | 交互色分け表示 |
| イベントハンドラ登録 | ZCL_CMA_ALV_GENERIC | REGISTER_HANDLER | コールバック登録 |
| ALV 全画面表示 | ZCL_CMA_ALV_GENERIC | DISPLAY | CL_SALV_TABLE->DISPLAY() |
| SALV 取得 | ZCL_CMA_ALV_GENERIC | GET_SALV | 個別設定用にインスタンス返却 |
| バリアントF4 | ZCL_CMA_ALV_GENERIC | F4HELP_VARIANT | レイアウトバリアント選択 |
| ホットスポットクリック | ZIF_CMA_ALV_CALLBACK | ON_HOTSPOT_CLICK | コールバックメソッド |

#### パラメータ定義

```abap
" ZCL_CMA_ALV_GENERIC
METHODS constructor      IMPORTING i_data TYPE REF TO data.
METHODS set_columns      IMPORTING it_columns TYPE ty_column_settings.
METHODS set_column_text  IMPORTING i_fieldname TYPE lvc_fname i_short_text TYPE scrtext_s OPTIONAL
                                   i_medium_text TYPE scrtext_m OPTIONAL i_long_text TYPE scrtext_l OPTIONAL.
METHODS set_hotspot      IMPORTING i_fieldname TYPE lvc_fname.
METHODS hide_column      IMPORTING i_fieldname TYPE lvc_fname.
METHODS set_optimize.
METHODS set_zebra.
METHODS register_handler IMPORTING i_callback TYPE REF TO zif_cma_alv_callback OPTIONAL.
METHODS display.
METHODS get_salv         RETURNING VALUE(r_salv) TYPE REF TO cl_salv_table.
CLASS-METHODS f4help_variant IMPORTING iv_report TYPE sy-repid OPTIONAL CHANGING cv_variant TYPE slis_vari.

" ZIF_CMA_ALV_CALLBACK
METHODS on_hotspot_click IMPORTING i_row TYPE i i_column TYPE lvc_fname.
```

#### 呼び出しパターン例

```abap
" 基本パターン: データ参照 -> 列設定 -> 表示
DATA(lo_alv) = NEW zcl_cma_alv_generic( REF #( lt_output ) ).
lo_alv->set_column_text( i_fieldname = 'MATNR' i_medium_text = '品目' ).
lo_alv->hide_column( i_fieldname = 'MANDT' ).
lo_alv->set_optimize( ).
lo_alv->set_zebra( ).
lo_alv->display( ).

" ホットスポット付きパターン（ZIF_CMA_ALV_CALLBACK 実装クラスが必要）
lo_alv->set_hotspot( i_fieldname = 'VBELN' ).
lo_alv->register_handler( i_callback = lo_my_callback ).
lo_alv->display( ).

" バリアントF4ヘルプ（選択画面 AT SELECTION-SCREEN ON VALUE-REQUEST）
zcl_cma_alv_generic=>f4help_variant( CHANGING cv_variant = p_vari ).
```

---

### アプリログ系（ZCL_CMA_APPLOG）

| トリガー | メソッド | 説明 |
|----------|----------|------|
| アプリケーションログの作成 | LOG_CREATE | ログヘッダ作成（BAL_LOG_CREATE相当） |
| メッセージ追加（BAPIRET2） | ADD_MESSAGE | ログへメッセージ追加（BAL_LOG_MSG_ADD相当） |
| ログ保存 | SAVE_LOG | DB保存（BAL_DB_SAVE相当） |

#### パラメータ定義

```abap
METHODS log_create  IMPORTING iv_object TYPE char20 iv_subobject TYPE char20 RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS add_message IMPORTING is_bapiret2 TYPE bapiret2 RETURNING VALUE(rv_result) TYPE bapiret2.
METHODS save_log    RETURNING VALUE(rv_result) TYPE bapiret2.
```

#### 呼び出しパターン例

```abap
DATA(lo_log) = NEW zcl_cma_applog( ).

" ログ作成 -> メッセージ追加 -> 保存
lo_log->log_create( iv_object = 'ZMYOBJ' iv_subobject = 'ZSUB' ).
lo_log->add_message( is_bapiret2 = ls_error_result ).
lo_log->save_log( ).
" SLG1 で確認可能
```

---

### 処理結果系（ZCL_CMA_JOB_RESULT）

| トリガー | メソッド | 説明 |
|----------|----------|------|
| バッチ処理結果（成功/エラー終了メッセージ） | JOB_RESULT | 処理結果サマリ出力 |

#### パラメータ定義

```abap
CLASS-METHODS job_result IMPORTING iv_err TYPE abap_bool.
```

#### 呼び出しパターン例

```abap
" 処理末尾で呼び出す
zcl_cma_job_result=>job_result( iv_err = lv_has_error ).
" iv_err = abap_true -> 正常メッセージ, abap_false -> エラーメッセージ
```

---

## メッセージ出力パターン（T100 必須）

プログラム内のメッセージ出力は、必ず T100 メッセージクラス経由で行うこと。
任意テキスト（`MESSAGE 'テキスト' TYPE 'E'`）は**禁止**。
使用するメッセージは `basic_design.md` の `catalogs.messages` で宣言されたものを使用する。

### 正しい書き方

```abap
" 短縮形（最も一般的）
MESSAGE e001(zcma01) WITH lv_val.
" eNNN = エラー、wNNN = 警告、iNNN = 情報、sNNN = 成功

" 明示形（動的にメッセージを指定する場合）
MESSAGE ID 'ZCMA01' TYPE 'E' NUMBER '001' WITH lv_val.

" BAPIRET2経由（共通クラスの戻り値を転送する場合）
MESSAGE ID ls_ret-id TYPE ls_ret-type NUMBER ls_ret-number
  WITH ls_ret-message_v1 ls_ret-message_v2 ls_ret-message_v3 ls_ret-message_v4.
```

### 禁止される書き方

```abap
" NG: 任意テキストメッセージ（lint CC-MSG-01 で検出される）
MESSAGE 'エラーが発生しました' TYPE 'E'.
MESSAGE 'ファイルが見つかりません' TYPE 'W'.
```

---

## 参照先

- **共通クラスルール定義**: `extensions/sap/config/common_class_rules.yaml`
- **abaplint 設定**: `extensions/sap/abaplint.json`
- **品質スコア設定**: `extensions/sap/config/quality_score_config.yaml`
- **コーディング規約**: `extensions/sap/agent_docs/conventions_sap.md`
