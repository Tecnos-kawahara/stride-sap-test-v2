# SAP ADT スクリプト コマンドリファレンス

> **Version**: 2.0 (Tecnos-STRIDE v5)
> **対象**: `extensions/sap/tools/` 配下のスクリプト群

本ドキュメントは SAP ADT スクリプトのコマンドリファレンスです。各ツールの使い方を素早く確認するために使用してください。

---

## 前提条件

### 環境変数（.env）

全スクリプト共通で以下の環境変数が必要です。プロジェクトルートの `.env` に設定してください。

| 変数名 | 必須 | 説明 | 例 |
|--------|------|------|----|
| `SAP_URL` | 必須 | SAP システムの URL | `https://vhcals4hci:44300` |
| `SAP_USERNAME` | 必須 | SAP ユーザー名 | `DEVELOPER` |
| `SAP_PASSWORD` | 必須 | SAP パスワード | `********` |
| `SAP_CLIENT` | 必須 | SAP クライアント番号 | `100` |

GUI 系ツール（gui_launch.js, gui_test.js, evidence_capture.js, update_description.js）では追加で以下を使用します。

| 変数名 | 必須 | 説明 | デフォルト |
|--------|------|------|-----------|
| `SAP_GUI_INSTANCE` | 任意 | DIAG インスタンス番号 | `00` |
| `SAP_GUI_CLIENT` | 任意 | GUI 用クライアント番号 | `SAP_CLIENT` の値 |
| `SAP_GUI_LANGUAGE` | 任意 | ログイン言語 | `JA` |
| `SAP_GUI_SYSTEM` | 任意 | SAPlogon エントリ名 | 自動検出 |

### npm 依存パッケージ

`extensions/sap/` ディレクトリで `npm install` を実行してください。

```bash
cd extensions/sap && npm install
```

主な依存: `abap-adt-api`, `dotenv`, `js-yaml`

### TLS 証明書

全スクリプトで `NODE_TLS_REJECT_UNAUTHORIZED = '0'` を設定しており、自己署名証明書環境に対応しています。

---

## 1. 調査・取得ツール (Phase 1.5: Design 後)

### 1.1 search.js -- オブジェクト検索・パッケージ一覧

SAP システム上の ABAP オブジェクトを名前パターンで検索、またはパッケージ内のオブジェクト一覧を取得する。

#### コマンド構文

```bash
node extensions/sap/tools/search.js object <query> [--type <type>]
node extensions/sap/tools/search.js package <package_name>
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `object` / `package` | サブコマンド | 必須 | 検索モードの選択 |
| `<query>` | 位置引数 | object 時必須 | 検索パターン（ワイルドカード `*` 対応） |
| `<package_name>` | 位置引数 | package 時必須 | パッケージ名 |
| `--type <type>` | オプション | 任意 | オブジェクトタイプでフィルタ（下表参照） |

**--type に指定可能な値:**

| 指定値 | 対象 |
|--------|------|
| `class` | クラス |
| `interface` | インターフェース |
| `program` | プログラム |
| `function_group` | ファンクショングループ |
| `include` | インクルードプログラム |
| `table` | テーブル |
| `structure` | 構造体 |
| `data_element` | データ要素 |
| `domain` | ドメイン |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了（結果 0 件含む） |
| 1 | 引数エラー / 環境変数未設定 / API エラー |

#### 使用例

```bash
# ZCL_LOA で始まるクラスを検索
node extensions/sap/tools/search.js object "ZCL_LOA*" --type class

# 全オブジェクトタイプで検索
node extensions/sap/tools/search.js object "ZIF_LOA*"

# パッケージ内のオブジェクト一覧
node extensions/sap/tools/search.js package ZLOA_ORDER
```

---

### 1.2 read.js -- ソース/DDIC 参照（ファイル出力なし）

SAP オブジェクトのソースコードまたは DDIC 定義をコンソールに表示する。ファイルは出力しない。

#### コマンド構文

```bash
node extensions/sap/tools/read.js <type> <name>
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `<type>` | 位置引数 | 必須 | オブジェクトタイプ |
| `<name>` | 位置引数 | 必須 | SAP オブジェクト名（自動大文字変換） |

**対応タイプ:**
- ソースコード系: `class`, `interface`, `program`, `function_group`, `include`
- DDIC 系: `table`, `structure`, `data_element`, `domain`

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | 引数エラー / 環境変数未設定 / API エラー |

#### 使用例

```bash
node extensions/sap/tools/read.js class ZCL_LOA_SALES_ORDER
node extensions/sap/tools/read.js table ZTLOA_ORDHEAD
node extensions/sap/tools/read.js data_element ZLOA_ORDER_ID
```

---

### 1.3 pull.js -- SAP ソースをローカルに取得

SAP からソースコードをダウンロードし、abaplint 命名規約に従ったローカルファイルとして保存する。クラスの場合、テストクラスも自動取得。

#### コマンド構文

```bash
node extensions/sap/tools/pull.js <name> <type> [--dir <package_dir>] [--fugr <group_name>]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 | デフォルト |
|------|------|------|------|-----------|
| `<name>` | 位置引数 | 必須 | SAP オブジェクト名（自動大文字変換） | -- |
| `<type>` | 位置引数 | 必須 | オブジェクトタイプ（下表参照） | -- |
| `--dir <package_dir>` | オプション | 任意 | パッケージディレクトリ名 | SAP から自動取得 |
| `--fugr <group_name>` | オプション | function_module 時必須 | 親の汎用グループ名 | -- |

**対応タイプ:** `class`, `interface`, `program`, `function_group`, `function_module`, `include`

#### 出力先

```
src/{package_dir}/{lowercase_name}/{lowercase_name}.{ext}.abap
```

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | 引数エラー / 環境変数未設定 / API エラー |

#### 使用例

```bash
# クラスのソースを取得（パッケージ自動検出）
node extensions/sap/tools/pull.js ZCL_LOA_SALES_ORDER class

# インターフェースを指定ディレクトリに取得
node extensions/sap/tools/pull.js ZIF_LOA_SALES_ORDER interface --dir zloa_order

# 汎用モジュールを取得（親グループ指定必須）
node extensions/sap/tools/pull.js Z_MY_FM function_module --fugr ZFGR_MY_GROUP
```

---

## 2. 実装ツール (Phase 4: Execute)

### 2.1 create_object.js -- 新規オブジェクト作成

SAP システム上に新規 ABAP オブジェクトの「箱」を作成する。ソースのアップロードや有効化は行わない。

#### コマンド構文

```bash
node extensions/sap/tools/create_object.js <type> <name> <description> [--package <pkg>] [--transport <tr>] [--parent <group>]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 | デフォルト |
|------|------|------|------|-----------|
| `<type>` | 位置引数 | 必須 | オブジェクトタイプ（下表参照） | -- |
| `<name>` | 位置引数 | 必須 | オブジェクト名（自動大文字変換） | -- |
| `<description>` | 位置引数 | 必須 | オブジェクトの説明 | -- |
| `--package <pkg>` | オプション | 任意 | パッケージ名 | `$TMP` |
| `--transport <tr>` | オプション | 条件付 | 移送依頼番号（`$TMP` 以外は必須） | -- |
| `--parent <group>` | オプション | function_module 時必須 | 親の汎用グループ名 | -- |

**対応タイプ:**

| 指定値 | 対象 | 備考 |
|--------|------|------|
| `class` | クラス | |
| `interface` | インターフェース | |
| `program` | プログラム | |
| `function_group` | 汎用グループ | |
| `function_module` | 汎用モジュール | `--parent` 必須 |
| `msag` | メッセージクラス | |

#### 移送番号バリデーション

| パッケージ | 移送番号 | 動作 |
|-----------|---------|------|
| `$TMP` | なし | 正常 |
| `$TMP` 以外 | あり | 正常 |
| `$TMP` 以外 | **なし** | **エラー終了** |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了（既存オブジェクトのスキップ含む） |
| 1 | 引数エラー / 移送番号不足 / API エラー |

#### 使用例

```bash
# ローカルオブジェクトとしてインターフェースを作成
node extensions/sap/tools/create_object.js interface ZIF_LOA_SALES_ORDER "受注データAPI IF" --package \$TMP

# パッケージ指定でクラスを作成
node extensions/sap/tools/create_object.js class ZCL_LOA_SALES_ORDER "受注データAPI" --package ZLOA_ORDER --transport DEVK900001

# 汎用モジュールを作成（--parent で親グループを指定）
node extensions/sap/tools/create_object.js function_module Z_SAMPLE_FM "サンプル汎用M" --parent ZFGR_SAMPLE --package \$TMP

# メッセージクラスを作成
node extensions/sap/tools/create_object.js msag ZMSG_EXAMPLE "サンプルメッセージクラス" --package \$TMP
```

---

### 2.2 activate.js -- Lock -> Upload -> Activate -> Unlock

ローカルファイルの ABAP ソースを SAP にアップロードし、有効化する。クラスの場合、テストクラスファイルが同ディレクトリに存在すれば自動アップロード。

#### コマンド構文

```bash
node extensions/sap/tools/activate.js <file_path> [<transport_number>] [--type <type>] [--name <name>] [--package <pkg>] [--fugr <group>] [--main-program <prog>]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 | デフォルト |
|------|------|------|------|-----------|
| `<file_path>` | 位置引数 | 必須 | ABAP ソースファイルのパス | -- |
| `<transport_number>` | 位置引数 | 条件付 | 移送依頼番号（`$TMP` 以外は必須） | -- |
| `--type <type>` | オプション | 任意 | オブジェクトタイプ | 拡張子から自動検出 |
| `--name <name>` | オプション | 任意 | オブジェクト名 | ファイル名から自動検出 |
| `--package <pkg>` | オプション | 任意 | パッケージ名 | SAP から自動取得 |
| `--fugr <group>` | オプション | FM 時必須 | 親の汎用グループ名 | -- |
| `--main-program <prog>` | オプション | Include 時任意 | Include の親プログラム名 | 自動検索 |

**拡張子による自動検出:**

| 拡張子 | 検出されるタイプ |
|--------|------------------|
| `.clas.abap` | class (main) |
| `.clas.testclasses.abap` | class (testclasses) |
| `.prog.abap` | program |
| `.intf.abap` | interface |
| `.fugr.abap` | function_group |
| `.incl.abap` | include |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了（アップロード + 有効化完了） |
| 1 | 引数エラー / ファイル未発見 / 移送番号不足 / ロック失敗 / 有効化失敗 |

#### 使用例

```bash
# クラスのアップロード & 有効化（$TMP）
node extensions/sap/tools/activate.js src/zloa_order/zcl_loa_sales_order/zcl_loa_sales_order.clas.abap

# 移送番号指定
node extensions/sap/tools/activate.js src/zloa_order/zcl_loa_sales_order/zcl_loa_sales_order.clas.abap DEVK900001

# 汎用モジュール
node extensions/sap/tools/activate.js src/z_my_fm.fugr.abap --fugr ZFGR_MY_GROUP --name Z_MY_FM

# Include（親プログラム指定）
node extensions/sap/tools/activate.js src/zcmai000101.incl.abap --main-program ZREP_MAIN_PROGRAM
```

---

### 2.3 run_tests.js -- ABAP Unit テスト実行

SAP 上で ABAP Unit テストを実行し、結果を表示する。テスト失敗時は終了コード 1 を返す。

#### コマンド構文

```bash
node extensions/sap/tools/run_tests.js <name> [--type <type>] [--output <report.md>]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 | デフォルト |
|------|------|------|------|-----------|
| `<name>` | 位置引数 | 必須 | SAP オブジェクト名（自動大文字変換） | -- |
| `--type <type>` | オプション | 任意 | オブジェクトタイプ | `class` |
| `--output <path>` | オプション | 任意 | Markdown レポート出力先 | -- |

**対応タイプ:** `class`（デフォルト）, `program`, `function_group`

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 全テスト成功 / テストなし |
| 1 | 1 件以上のテスト失敗 / 実行エラー |

#### 使用例

```bash
# クラスのテスト実行（デフォルト）
node extensions/sap/tools/run_tests.js ZCL_LOA_SALES_ORDER

# プログラムのテスト実行
node extensions/sap/tools/run_tests.js ZLOAP000200 --type program

# 結果をファイルに出力
node extensions/sap/tools/run_tests.js ZCL_MY_CLASS --output tests/abap_unit_report.md
```

---

### 2.4 clean_abap.js -- ABAP ソース自動クリーンアップ

ABAP ソースのフォーマット・旧構文を自動修正する。activate.js の前に実行し、ソースファイルを直接上書き。

#### コマンド構文

```bash
node extensions/sap/tools/clean_abap.js <file_or_dir> [options]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `<file_or_dir>` | 位置引数 | 必須 | ABAP ソースファイルまたはディレクトリ |
| `--recursive` | フラグ | 任意 | ディレクトリ内の .abap ファイルを再帰処理 |
| `--dry-run` | フラグ | 任意 | 変更せずにプレビューのみ（差分表示） |
| `--stats` | フラグ | 任意 | 修正統計をサマリー表示 |
| `--verbose` | フラグ | 任意 | 各ルール適用のログを出力 |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | エラー発生 |

#### 使用例

```bash
# 単一ファイルをクリーンアップ
node extensions/sap/tools/clean_abap.js src/zpackage/zcl_example/zcl_example.clas.abap

# ディレクトリを再帰処理
node extensions/sap/tools/clean_abap.js src/ --recursive

# ドライランで差分プレビュー
node extensions/sap/tools/clean_abap.js src/ --recursive --dry-run

# 統計付き
node extensions/sap/tools/clean_abap.js src/ --recursive --stats
```

---

### 2.5 unlock.js -- ロック緊急解除

SAP ADT のオブジェクトロックを緊急解除する。activate.js のエラーでロックが残った場合に使用。

#### コマンド構文

```bash
node extensions/sap/tools/unlock.js --type <type> --name <name>
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `--type <type>` | オプション | 必須 | オブジェクトタイプ |
| `--name <name>` | オプション | 必須 | SAP オブジェクト名（自動大文字変換） |

**対応タイプ:** `class`, `interface`, `program`, `function_group`, `include`

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | ロック解除成功 / ロックされていなかった |
| 1 | 別ユーザーのロック / 引数エラー / その他のエラー |

#### 使用例

```bash
node extensions/sap/tools/unlock.js --type class --name ZCL_LOA_SALES_ORDER
node extensions/sap/tools/unlock.js --type program --name ZLOAP000200
```

> **注意**: 自ユーザーのロックのみ解除可能。別ユーザーのロックは SM12 で解除してください。

---

### 2.6 update_description.js -- 内容説明テキスト更新

SAP GUI スクリプティング経由でオブジェクトの内容説明テキスト（Description / Kurztext）を更新する。ADT REST API では description の事後変更ができないため、本ツールが唯一の変更手段。

#### 前提条件

- SAP GUI がインストールされ、スクリプティングが有効であること（RZ11: `sapgui/user_scripting = TRUE`）
- gui_launch.js で SAP GUI セッションが起動済みであること

#### コマンド構文

```bash
node extensions/sap/tools/update_description.js --type <type> --name <name> --description <text>
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `--type <type>` | オプション | 必須 | オブジェクトタイプ（下表参照） |
| `--name <name>` | オプション | 必須 | オブジェクト名（自動大文字変換） |
| `--description <text>` | オプション | 必須 | 設定する内容説明テキスト |

**対応タイプ:**

| 指定値 | トランザクション | 対象 |
|--------|-----------------|------|
| `function_module` | SE37 | 汎用モジュールの内容説明 |
| `function_group` | SE80 | 汎用グループの内容説明 |
| `program` | SE38 | プログラムのタイトル |
| `class` | SE24 | クラスの内容説明 |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了（説明更新完了） |
| 1 | 引数エラー / SAP GUI セッション確保失敗 / GUI 操作エラー |

#### 使用例

```bash
node extensions/sap/tools/update_description.js --type function_module --name Z_MY_FM --description "新しい説明"
node extensions/sap/tools/update_description.js --type program --name ZREPORT --description "新しいタイトル"
node extensions/sap/tools/update_description.js --type class --name ZCL_MY_CLASS --description "新しい説明"
```

---

## 3. テストツール (Phase 4: Testing)

### 3.1 gui_launch.js -- SAP GUI 自動起動/ログイン/終了

SAP GUI (DIAG) セッションを自動起動・ログインする。既に接続済みの場合はスキップ。

#### コマンド構文

```bash
node extensions/sap/tools/gui_launch.js [--close]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `--close` | フラグ | 任意 | 既存の SAP GUI セッションを閉じる（クリーンアップ用） |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | セッション準備完了 / 正常終了 |
| 1 | セッション確立失敗 |

#### 使用例

```bash
# SAP GUI を起動してログイン
node extensions/sap/tools/gui_launch.js

# セッションを閉じる
node extensions/sap/tools/gui_launch.js --close
```

---

### 3.2 gui_test.js -- SAP GUI テスト実行

GUI テスト WSF スクリプトを実行してテスト GREEN を確認する。エビデンス（スクショ）の生成は行わない。

#### コマンド構文

```bash
node extensions/sap/tools/gui_test.js <test.wsf> [--auto] [--output <report.md>]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `<test.wsf>` | 位置引数 | 必須 | テスト WSF スクリプトのパス |
| `--auto` | フラグ | 任意 | SAP GUI の起動からテスト後のセッション終了まで自動実行 |
| `--output <path>` | オプション | 任意 | 全テスト PASS 時のみ Markdown レポートを出力 |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 全テスト成功 |
| 1 | 1 件以上のテスト失敗 / エラー発生 |

#### 使用例

```bash
# 手動セッションでテスト実行
node extensions/sap/tools/gui_test.js specs/my_feature/tests/test_gui.wsf

# 全自動実行（起動 -> テスト -> 終了）
node extensions/sap/tools/gui_test.js specs/my_feature/tests/test_gui.wsf --auto

# レポート出力付き
node extensions/sap/tools/gui_test.js specs/my_feature/tests/test_gui.wsf --auto --output tests/gui_report.md
```

---

## 4. エビデンスツール

### 4.1 evidence_capture.js -- 正式エビデンス一括取得

plan.md の test_scenarios 定義に基づき、SAP GUI 経由で画面スクショを一括取得する。正式エビデンスの唯一の生成ツール。

3 段階実行モデルに対応:
- **Stage 1（単体テスト）**: `--no-evidence` -- スクショなし、自動判定のみ
- **Stage 2（受入テスト）**: `--no-evidence --screenshot` -- スクショあり、SE16/JSON なし
- **Stage 3（エビデンス）**: オプションなし -- フルエビデンス（スクショ + SE16 + JSON）

#### コマンド構文

```bash
node extensions/sap/tools/evidence_capture.js <feature_dir_or_plan.md> --scenario <id> [options]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `<feature_dir_or_plan.md>` | 位置引数 | 必須 | feature ディレクトリまたは plan.md のパス |
| `--scenario <id>` | オプション | 必須 | テストシナリオ ID（例: SC-01） |
| `--output <dir>` | オプション | 任意 | エビデンス出力先ディレクトリ |
| `--auto` | フラグ | 任意 | SAP GUI の起動 -> 取得 -> 終了を自動実行 |
| `--no-evidence` | フラグ | 任意 | エビデンス取得なし（PASS/FAIL 自動判定のみ） |
| `--screenshot` | フラグ | 任意 | `--no-evidence` と併用時、スクリーンショットのみ取得 |

#### 出力

- `<dir>/evidence_report.html` -- サイドメニュー付き統合エビデンス HTML
- `<dir>/screenshots/{scenario_id}_{seq}.png` -- スクリーンショット PNG

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 全エビデンス取得成功 |
| 1 | エラー発生 |

#### 使用例

```bash
# Stage 1: 単体テスト（自動判定のみ）
node extensions/sap/tools/evidence_capture.js specs/order_list/ --scenario SC-01 --no-evidence --auto

# Stage 2: 受入テスト（スクショあり）
node extensions/sap/tools/evidence_capture.js specs/order_list/ --scenario SC-01 --no-evidence --screenshot --auto

# Stage 3: フルエビデンス
node extensions/sap/tools/evidence_capture.js specs/order_list/ --scenario SC-01 --auto
```

---

### 4.2 evidence_merge_report.js -- 統合エビデンスレポート生成

個別シナリオ HTML（evidence_SC-*.html）を走査し、サイドメニュー付き統合レポート HTML（evidence_report.html）を生成する。全シナリオのエビデンス取得完了後に実行する。

#### コマンド構文

```bash
node extensions/sap/tools/evidence_merge_report.js <feature_dir>
```

#### 引数

| 引数 | 種別 | 必須 | 説明 |
|------|------|------|------|
| `<feature_dir>` | 位置引数 | 必須 | feature ディレクトリのパス |

#### 出力

- `<feature_dir>/tests/reports/evidence_report.html` -- 統合エビデンス HTML

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | エラー発生 |

#### 使用例

```bash
node extensions/sap/tools/evidence_merge_report.js specs/test_integration/
```

---

## 5. ユーティリティ

### 5.1 data_preview.js -- テーブル/CDS ビューのデータプレビュー

ADT REST API 経由でテーブルや CDS ビューのデータを取得・表示する（SE16 相当）。テストデータの存在確認や条件値の特定に使用。

#### コマンド構文

```bash
node extensions/sap/tools/data_preview.js <table_name> [options]
```

#### 引数

| 引数 | 種別 | 必須 | 説明 | デフォルト |
|------|------|------|------|-----------|
| `<table_name>` | 位置引数 | 必須 | テーブル名または CDS ビュー名 | -- |
| `--rows <n>` | オプション | 任意 | 取得件数（最大 500） | `10` |
| `--where <cond>` | オプション | 任意 | WHERE 条件 | -- |
| `--columns <cols>` | オプション | 任意 | 表示カラム（カンマ区切り） | -- |
| `--distinct <col>` | オプション | 任意 | 指定カラムのユニーク値一覧を表示 | -- |
| `--format json` | オプション | 任意 | JSON 形式で出力 | -- |
| `--output <file>` | オプション | 任意 | 結果をファイルに保存 | 標準出力 |

#### 終了コード

| コード | 意味 |
|--------|------|
| 0 | 正常終了 |
| 1 | 引数エラー / 環境変数未設定 / API エラー |

#### 使用例

```bash
# テーブルの先頭 10 件を表示
node extensions/sap/tools/data_preview.js MCHB

# 条件指定で 5 件取得
node extensions/sap/tools/data_preview.js MCHB --rows 5 --where "WERKS = '1000'"

# ユニーク値一覧
node extensions/sap/tools/data_preview.js MCHB --distinct WERKS

# カラム指定
node extensions/sap/tools/data_preview.js MCHB --columns MATNR,WERKS,CHARG,CLABS

# JSON 形式でファイル出力
node extensions/sap/tools/data_preview.js MCHB --format json --output data.json
```

---

## クイックリファレンス（全ツール一覧）

| # | ツール | 主な用途 | SAP 接続 | GUI 必要 |
|---|--------|----------|----------|----------|
| 1 | `search.js` | オブジェクト検索・パッケージ一覧 | ADT | -- |
| 2 | `read.js` | ソース/DDIC 参照（コンソール出力のみ） | ADT | -- |
| 3 | `pull.js` | ソースをローカルファイルに取得 | ADT | -- |
| 4 | `create_object.js` | 新規オブジェクト作成（箱のみ） | ADT | -- |
| 5 | `activate.js` | Lock -> Upload -> Activate -> Unlock | ADT | -- |
| 6 | `run_tests.js` | ABAP Unit テスト実行 | ADT | -- |
| 7 | `clean_abap.js` | ABAP ソース自動クリーンアップ | -- | -- |
| 8 | `unlock.js` | ロック緊急解除 | ADT | -- |
| 9 | `update_description.js` | 内容説明テキスト更新 | -- | SAP GUI |
| 10 | `gui_launch.js` | SAP GUI 自動起動/ログイン/終了 | -- | SAP GUI |
| 11 | `gui_test.js` | SAP GUI テスト実行 | -- | SAP GUI |
| 12 | `evidence_capture.js` | 正式エビデンス一括取得 | -- | SAP GUI |
| 13 | `evidence_merge_report.js` | 統合エビデンスレポート生成 | -- | -- |
| 14 | `data_preview.js` | テーブル/CDS データプレビュー | ADT | -- |
