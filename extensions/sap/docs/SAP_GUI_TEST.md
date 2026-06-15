# SAP GUI テストフレームワーク技術リファレンス

> 本ドキュメントは SAP GUI テストの技術リファレンスです。テスト作成手順は `agent_docs/testing_sap.md` を参照してください。

> **対象**: `extensions/sap/tools/gui_*.js` + `extensions/sap/templates/tests/gui_test_template.wsf`
> **前提**: Node.js 18+、Windows + SAP GUI for Windows（Scripting 有効）、`.env` ファイルによる接続設定

---

## アーキテクチャ

```
+------------------------------------------------------+
| gui_test.js (テスト実行エンジン -- GREEN確認のみ)      |
|  +-- --auto -> gui_launch.js で SAP GUI 起動・ログイン |
|  +-- テスト実行（PASS/FAIL 判定のみ）                  |
|  +-- --auto -> gui_launch.js --close でセッション終了  |
+------------------------------------------------------+
         | cscript //NoLogo
         v
+------------------------------------------------------+
| gui_test_<program>.wsf (テストスクリプト)              |
|  +-- [CONFIG] プログラム固有の設定                     |
|  +-- [BOILERPLATE] ヘルパー関数・COM 接続(テンプレート) |
|  +-- [STANDARD TESTS] CONFIG 駆動の標準テスト          |
|  +-- [CUSTOM TESTS] プロジェクト固有の追加テスト        |
+------------------------------------------------------+
         | COM API (GetObject("SAPGUI"))
         v
+------------------------------------------------------+
| SAP GUI for Windows                                   |
+------------------------------------------------------+
```

### 通信プロトコル

WSF スクリプトは `WScript.Echo(KEY=VALUE)` で結果を stdout に出力し、`gui_test.js` がパースする。

| キー | 説明 |
|------|------|
| `CONNECT` | `OK` / `FAIL` |
| `SYSTEM`, `CLIENT`, `USER` | SAP システム情報 |
| `TEST_COUNT` | テスト総数 |
| `TEST_<i>_ID` | テスト ID（例: `T0`） |
| `TEST_<i>_DESC` | テスト名 |
| `TEST_<i>_STATUS` | `PASS` / `FAIL` |
| `TEST_<i>_DETAIL` | 結果詳細 |
| `TEST_<i>_CHECK` | 確認内容 |
| `TEST_<i>_CRITERIA` | 判定基準 |
| `SS_<name>` | スクリーンショットファイルパス |
| `ALV_COL_COUNT`, `ALV_COL_FOUND`, `ALV_COL_MISSING` | ALV カラム情報 |

---

## 環境設定

### .env（GUI 固有変数）

```env
# SAP GUI 固有（任意・デフォルト値あり）
SAP_GUI_INSTANCE=00       # DIAG インスタンス番号（default: 00）
SAP_GUI_CLIENT=200        # GUI ログインクライアント（default: SAP_CLIENT）
SAP_GUI_LANGUAGE=JA       # ログオン言語（default: JA）
SAP_GUI_SYSTEM=           # SAPlogon エントリ名（未設定時は SAPUILandscape.xml から自動検出）
```

> `SAP_URL`, `SAP_USERNAME`, `SAP_PASSWORD` 等の共通変数は別途設定済みであること。

### SAP GUI 側の前提設定

- SAP GUI Scripting が有効であること（RZ11: `sapgui/user_scripting` = `TRUE`）
- SAP GUI for Windows がインストール済みであること
- SAPlogon に DIAG 接続エントリが登録済みであること

---

## コマンドリファレンス

### gui_test.js

```
node extensions/sap/tools/gui_test.js <test.wsf> [--auto]
```

| オプション | 説明 |
|-----------|------|
| `<test.wsf>` | テストスクリプトのパス（必須） |
| `--auto` | SAP GUI の起動・ログインからセッション終了まで自動実行 |

| 終了コード | 意味 |
|-----------|------|
| 0 | 全テスト合格 |
| 1 | 不合格あり または エラー |

> gui_test.js はテスト GREEN の確認のみを行い、ファイル出力は行わない。
> コンソールに PASS/FAIL 結果を表示し、exit code で結果を返す。

### gui_launch.js

```
node extensions/sap/tools/gui_launch.js [--close]
```

| オプション | 説明 |
|-----------|------|
| (なし) | SAP GUI を起動しログイン |
| `--close` | 既存セッションを `/nex` で終了 |

接続先は `.env` の `SAP_URL` + `SAP_GUI_INSTANCE` から自動検出（`SAPUILandscape.xml` の DIAG エントリをマッチング）。
`SAP_GUI_SYSTEM` を明示設定すれば自動検出をスキップ。

---

## トラブルシューティング

### ALV Shell パスが見つからない

`CONFIG.alvShellPath` のデフォルト値 `wnd[0]/usr/cntlGRID1/shellcont/shell` は `CL_SALV_TABLE` および `CL_GUI_ALV_GRID` の標準的なパスです。
カスタムコンテナを使用している場合は、SAP GUI のスクリプト記録機能でパスを確認してください。

### CL_SALV_TABLE と CL_GUI_ALV_GRID の違い

ソート・エクスポートのツールバーボタン ID が異なりますが、テンプレートは複数パターンのフォールバックで両方に対応しています。

### パスワードに特殊文字（&等）が含まれる

`gui_launch.js` は COM API 経由で接続するため、シェルエスケープの問題は発生しません。
`.env` にそのまま記載してください。

### SAPlogon エントリが自動検出されない

`SAP_GUI_SYSTEM` に SAPlogon のエントリ名を明示設定してください。
エントリ名は SAPlogon の一覧画面で確認できます。

---

## SAP GUI Scripting キー操作リファレンス

### sendVKey 番号表

`session.findById("wnd[0]").sendVKey(N)` で送信するファンクションキーの番号。

| 番号 | キー | 説明 |
|------|------|------|
| 0 | Enter | 確定 |
| 1 | F1 | ヘルプ |
| 2 | F2 | 選択 |
| 3 | F3 | 戻る（Back） |
| 4 | F4 | 検索ヘルプ（入力ヘルプ） |
| 5 | F5 | -- |
| 6 | F6 | 変更 |
| 7 | F7 | 照会 |
| 8 | F8 | 実行 |
| 9 | F9 | -- |
| 10 | F10 | メニューバー |
| 11 | F11 | -- |
| 12 | F12 | 中止（Cancel） |
| 13-24 | Ctrl+F1 -- Ctrl+F12 | Ctrl 修飾キー付きファンクションキー（13=Ctrl+F1, 14=Ctrl+F2, ...） |
| 70 | Ctrl+E | -- |
| 71 | Ctrl+F | 検索 |
| 72 | Ctrl+G | -- |
| 73 | Ctrl+P | 印刷 |

> **注意**: sendVKey の番号体系は F1=1, F2=2, ..., F12=12, Ctrl+F1=13, ..., Ctrl+F12=24 と連続する。
> **Ctrl+S（保存）は sendVKey では送信できない。** ツールバーボタン `btn[11].press()` を使用すること。

### ツールバーボタン ID 表

`session.findById("wnd[0]/tbar[N]/btn[M]").press()` で押下するボタン。

**tbar[0] -- システムツールバー（画面上部の標準ボタン行）**

| btn ID | 操作 | 対応キーボードショートカット |
|--------|------|--------------------------|
| btn[0] | Enter | Enter |
| btn[3] | 戻る（Back） | F3 |
| btn[8] | -- | -- |
| btn[11] | **保存** | **Ctrl+S** |
| btn[12] | 中止（Cancel） | F12 / Esc |
| btn[15] | Enter（確定） | -- |
| btn[17] | 終了（Exit） | -- |

**tbar[1] -- アプリケーションツールバー（画面上部の2行目）**

| btn ID | 操作（トランザクション依存） | 備考 |
|--------|--------------------------|------|
| btn[27] | **有効化（Activate）** | **Ctrl+F3** |
| btn[28] | チェック | -- |
| btn[29] | ソース表示 | -- |

> **注意**: tbar[1] のボタンIDはトランザクションごとに異なる。
> 上記は SE38（ABAPエディタ）での配置。他のトランザクションでは異なるIDが割り当てられる可能性がある。
> 不明な場合は Scripting Tracker 等で実際のIDを確認すること。

### 混同しやすい操作の対照表

| やりたい操作 | 正しい方法 | よくある間違い | 間違いの結果 |
|------------|-----------|-------------|------------|
| **保存（Ctrl+S）** | `tbar[0]/btn[11].press()` | `sendVKey(11)` | F11が送信される（保存されない） |
| **有効化（Ctrl+F3）** | `tbar[1]/btn[27].press()` | `sendVKey(15)` | Ctrl+F3 = sendVKey(15) は動作するが、トランザクションによっては期待通りに動作しない場合がある |
| **戻る（F3）** | `sendVKey(3)` または `tbar[0]/btn[3].press()` | どちらも正しい | -- |
| **実行（F8）** | `sendVKey(8)` | -- | -- |
| **中止（F12）** | `sendVKey(12)` または `tbar[0]/btn[12].press()` | どちらも正しい | -- |
