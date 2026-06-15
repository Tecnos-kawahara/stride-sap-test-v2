# ABAP コード生成品質ルール

> 本ドキュメントは Phase 4 Execute で ABAP コードを生成する際の品質基準を定義する。
> TDD サイクルの手順は `phase4_execute.md` を、コーディングパターンは `templates/abap/PATTERNS.md` を参照すること。

---

## 1. 設計合理性の原則（Design Rationality Principle）

> **AI の最適化目標は「コード生成量の最小化」ではなく「SAP Application Server 上での処理効率の最大化」である。**

コードが長くなることを理由に設計を省略してはならない。
以下の判断基準に従い、**AP（Application Server）上での実行効率**を優先すること。

---

## 2. アンチパターン集（NG → OK）

### AP-01: SELECT *（DB→AS 間の不要カラム転送）

```abap
" NG: フィールド省略（DB から全カラムが AS に転送される）
SELECT * FROM ztable INTO TABLE @lt_data WHERE bukrs = @lv_bukrs.

" OK: plan.md の data_references に基づくフィールド明示
SELECT bukrs, belnr, gjahr, dmbtr
  FROM ztable
  INTO TABLE @lt_data
  WHERE bukrs = @lv_bukrs.
```

**理由:** `SELECT *` は DB→Application Server 間で全カラムのデータを転送する。
カラム数が多いテーブル（BSEG: 300+、VBAP: 200+）では転送量が桁違いに増大する。
plan.md の data_references に宣言されたフィールドのみを明示的に SELECT すること。

### AP-02: MOVE-CORRESPONDING（実行時フィールドマッチング）

```abap
" NG: 暗黙的なフィールドマッチング
MOVE-CORRESPONDING ls_source TO ls_target.

" OK: 明示的なフィールド転送
ls_target-bukrs = ls_source-bukrs.
ls_target-belnr = ls_source-belnr.
ls_target-dmbtr = ls_source-dmbtr.

" OK: VALUE での明示的マッピング（フィールド数が多い場合）
ls_target = VALUE #(
  bukrs = ls_source-bukrs
  belnr = ls_source-belnr
  dmbtr = ls_source-dmbtr ).
```

**理由:** `MOVE-CORRESPONDING` は実行時に構造のフィールド名を動的にマッチングする。
明示的転送はコンパイル時に解決されるため実行時オーバーヘッドがない。
また、意図しないフィールドの上書き（同名だが意味が異なるフィールド）を防止できる。

### AP-03: 処理の圧縮（メモリスコープの肥大化）

```abap
" NG: 複数の処理定義を1つの FORM/METHOD に押し込む
FORM do_everything.
  " VALIDATE + READ + AGGREGATE + WRITE を全部ここで実行
  " → 全内部テーブルが FORM 終了まで解放されない
ENDFORM.

" OK: process_definitions の各処理ブロックに対応して FORM/METHOD を分離
FORM validate_input.    " 完了後に検証用データを解放
ENDFORM.
FORM read_data.
ENDFORM.
FORM aggregate_amount.
ENDFORM.
FORM write_to_table.
ENDFORM.
```

**理由:** FORM/METHOD のローカル変数はスコープ終了時に解放される。
処理を分離すれば、前ブロックで使用した内部テーブルのメモリが次ブロック開始前に解放される。
大量データ処理ではメモリ消費量に大きな差が出る。

### AP-04: 汎用例外ハンドリング（不要な例外オブジェクト生成）

```abap
" NG: 全例外を一括キャッチ
TRY.
    lv_amount = CONV dmbtr( lv_string ).
  CATCH cx_root INTO DATA(lx_err).  " cx_root は全例外の親 → 意図しない例外も捕捉
    " ...
ENDTRY.

" OK: 発生しうる例外を個別にキャッチ
TRY.
    lv_amount = CONV dmbtr( lv_string ).
  CATCH cx_sy_conversion_no_number INTO DATA(lx_conv).
    APPEND VALUE bapiret2(
      type = 'E'  id = 'ZMSG'  number = '010'
      message_v1 = lv_string ) TO gt_messages.
ENDTRY.
```

**理由:** `cx_root` は全例外クラスの親であり、想定外の例外（メモリ不足等）まで握りつぶす。
個別例外クラスを指定すれば、想定外の例外は上位に伝播し、問題の早期検出につながる。

### AP-05: バリデーション手順の簡略化（異常データの後工程流入）

```abap
" NG: spec に3つの検証条件があるのに IS INITIAL チェック1つで済ませる
IF lv_input IS INITIAL.
  " エラー
ENDIF.

" OK: AC に書かれた全検証条件を個別に実装
" AC-01: 会社コードの存在チェック
lo_check->exist_company( EXPORTING iv_bukrs = lv_bukrs IMPORTING rv_result = gs_message ).
" AC-02: 会社コードの権限チェック
lo_check->auth_company( EXPORTING iv_bukrs = lv_bukrs iv_actvt = '03' IMPORTING rv_result = gs_message ).
" AC-03: 金額フィールドの数値チェック
TRY.
    lv_amount = CONV dmbtr( lv_string ).
  CATCH cx_sy_conversion_no_number.
    " ...
ENDTRY.
```

**理由:** バリデーションの省略は、異常データが後続の DB アクセスや計算処理に流入することを意味する。
不要な DB SELECT や計算が発生し、最終的にエラーで ROLLBACK → 全処理がやり直しになる。
異常データを**早期に排除する方が全体の処理効率が高い**。

---

## 3. 絶対禁止事項（違反するとアクティベーション失敗 or lint エラー）

### 3-1. 命名制約（30 文字制限）

SAP ADT REST API はメソッド名・変数名・クラス名が **30 文字** を超えるとアップロードを拒否する。

```abap
" NG: 31文字以上
METHODS calculate_total_amount_with_tax.  " → アクティベーション失敗

" OK: 30文字以内
METHODS calc_total_amount_w_tax.
```

**特に注意:**
- テストメソッド名: `ut01_` プレフィックスで 5 文字消費 → 残り 25 文字
- `lcl_` プレフィックスのローカルクラス名
- TYPES 定義のテーブル型名

> 詳細は `templates/abap/PATTERNS.md` の「ABAP 命名制約」を参照。

### 3-2. RANGE OF パラメータの事前定義

**ADT REST API の制約**: `IMPORTING ir_xxx TYPE RANGE OF yyy` のインライン定義はアップロード時にエラーとなる。

```abap
" NG: インライン定義
METHODS get_data IMPORTING ir_bukrs TYPE RANGE OF bukrs.

" OK: TYPES で事前定義
TYPES: tyr_bukrs TYPE RANGE OF bukrs.
METHODS get_data IMPORTING it_bukrs TYPE tyr_bukrs.
```

### 3-3. REFRESH 禁止（廃止命令）

ヘッダ付き内部テーブルが使用禁止のため、`REFRESH` は不要。`CLEAR` で代替する。

```abap
" NG: REFRESH（ヘッダ付き内部テーブル前提の命令）
REFRESH lt_data.

" OK: CLEAR
CLEAR lt_data.
```

**検出:** `clean_abap.js` が自動変換する（`REFRESH itab.` → `CLEAR itab.`）。

> **注**: T100 メッセージルール（ハードコード禁止）は `CLAUDE_SAP.md` Rule S5 を参照。
> 共通クラス直接 API 置換禁止は `phase4_execute.md` の共通クラス判断プロセスを参照。

---

## 4. 選択画面 DEFAULT vs INITIALIZATION

静的デフォルト値は `DEFAULT` 句で設定し、`INITIALIZATION` での定数設定は禁止。

> 詳細なコード例と判断基準表は `templates/abap/PATTERNS.md` の「選択画面パラメータのデフォルト値」を参照。

---

## 5. テストコード生成パターン

### 5-1. ABAP SQL Test Double Framework

テスト内でのデータベースアクセスは **ABAP SQL Test Double Framework** を使用する。

```abap
METHOD ut01_normal_case.
  " テストデータ準備
  DATA lt_test TYPE STANDARD TABLE OF ztable.
  lt_test = VALUE #( ( field1 = 'A' field2 = '100' ) ).

  " SQL Test Double 環境設定
  cl_osql_test_environment=>create(
    i_dependency_list = VALUE #( ( 'ZTABLE' ) )
  )->insert_test_data( lt_test ).

  " テスト実行
  " ...

  " アサーション
  cl_abap_unit_assert=>assert_equals(
    act = lv_actual
    exp = 'expected_value'
    msg = 'テスト説明' ).
ENDMETHOD.
```

### 5-2. テストメソッドの命名規則

```
ut{NN}_{テスト内容の簡潔な説明}
```

例:
- `ut01_normal_case` -- 正常系
- `ut02_invalid_input` -- 異常系（入力バリデーション）
- `ut03_auth_denied` -- 異常系（権限エラー）

**制約:** 30 文字以内（`ut01_` = 5 文字 + 残り 25 文字）。

### 5-3. テストクラスの属性

```abap
CLASS lcl_test DEFINITION FINAL FOR TESTING
  DURATION SHORT       " 必須: SHORT
  RISK LEVEL HARMLESS. " 必須: HARMLESS
  PRIVATE SECTION.
    METHODS ut01_normal_case FOR TESTING RAISING cx_static_check.
    METHODS ut02_error_case  FOR TESTING RAISING cx_static_check.
ENDCLASS.
```

- `DURATION SHORT`: テスト実行時間の上限（必須）
- `RISK LEVEL HARMLESS`: テストがシステムに副作用を与えないことの宣言（必須）
- `RAISING cx_static_check`: テストメソッドに付与（例外伝搬用、必須）

> テストクラスの配置ルール（プログラム末尾 vs 別ファイル）は `templates/abap/PATTERNS.md` を参照。
> テストクラスの AC 単位分割ルールは `phase4_execute.md` Step 6-2 を参照。

---

## 6. コード品質セルフチェックリスト（全 AC 実装完了時）

全 AC の TDD サイクル完了後、Step 6-3 に進む前に以下を確認する。

### 設計合理性

- [ ] SELECT 文で `*` を使用していないか（plan.md の data_references に基づくフィールド明示か）
- [ ] `MOVE-CORRESPONDING` を使用していないか（明示的フィールド転送か）
- [ ] process_definitions の各処理ブロックに対応して FORM/METHOD が分離されているか（圧縮していないか）
- [ ] 例外処理が `cx_root` ではなく個別例外クラスを指定しているか
- [ ] AC に記載された全バリデーション条件が個別に実装されているか（簡略化していないか）

### アクティベーション要件

- [ ] 全メソッド名・変数名が 30 文字以内か
- [ ] RANGE OF パラメータが TYPES で事前定義されているか
- [ ] `REFRESH` を使用していないか（`CLEAR` に置換済みか）
- [ ] テストクラスが正しい場所に配置されているか（プログラム: 末尾埋め込み、クラス: 別ファイル）
- [ ] メッセージが即時出力ではなく BAPIRET2 テーブルに収集され、処理末尾で一括出力されているか
- [ ] テストメソッドに `FOR TESTING RAISING cx_static_check` が付与されているか
- [ ] 選択画面の静的デフォルト値が `DEFAULT` で設定されているか（`INITIALIZATION` で定数を設定していないか）
- [ ] `sap_quality_score` >= 85pt を満たしているか
