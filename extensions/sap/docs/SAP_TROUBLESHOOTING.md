# SAP 拡張 トラブルシューティングガイド

本ドキュメントは人間向けのトラブルシューティングガイドです。AI は `agent_docs/error_recovery_sap.md` を使用して自動対処します。

関連ドキュメント:
- [SAP_QUICKSTART.md](SAP_QUICKSTART.md) -- セットアップ手順
- [SAP_CONFIG_REFERENCE.md](SAP_CONFIG_REFERENCE.md) -- 設定ファイルの詳細
- AI 向けエラー回復ガイド: `extensions/sap/agent_docs/error_recovery_sap.md`

---

## 1. AI 自動対処カテゴリ（クイックリファレンス）

以下のエラーカテゴリは `agent_docs/error_recovery_sap.md` に従い AI が自動で回復処理を行います。
人間の介入は原則不要です。詳細は `agent_docs/error_recovery_sap.md` を参照してください。

| カテゴリ | 概要 |
|---------|------|
| オブジェクトロック競合 | `unlock.js` で自動解除 -- 他ユーザーロック時のみエスカレーション |
| アクティベーションエラー | 構文エラー/依存関係エラーを検出し S1-B1 に戻って修正ループ |
| テスト失敗 | 失敗原因を判定し、ソース修正またはテスト修正で回復 |
| 品質チェック失敗 | clean_abap / abaplint / common_class_lint / quality_score の各段階で自動修正 |
| エビデンス取得エラー | 個別シナリオの再実行 -- merge_report の再生成 |

---

## 2. 環境・依存関係エラー

### 2.1 Node.js / npm の依存関係エラー

**症状:**
```
Error: Cannot find module 'abap-adt-api'
Error: Cannot find module 'dotenv'
```

**対処:**
```bash
cd extensions/sap
npm install
```

`package.json` が `extensions/sap/` にあることを確認。`abap-adt-api` v7.0.0 以上が必要。

### 2.2 npx コマンドが見つからない（Windows）

**症状:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'npx'
```

**原因:** Windows では `npx` は `npx.cmd` バッチファイルであり、`subprocess.run(["npx", ...])` では見つからない。

**対処:** `sap_stage1_quality.py` は `shell=True` で実行するよう修正済み。手動で abaplint を実行する場合:
```bash
npx @abaplint/cli --file "src/<filename>"
```

### 2.3 cp932 エンコーディングエラー（Windows）

**症状:**
```
UnicodeEncodeError: 'cp932' codec can't encode character '\u2717'
```

**原因:** Windows のデフォルトエンコーディング（cp932）で Unicode 文字（チェックマーク等）を出力できない。

**対処:** バッチスクリプトは `sys.stdout.buffer.write()` + UTF-8 エンコーディングで出力するよう修正済み。手動実行時は環境変数を設定:
```bash
export PYTHONIOENCODING=utf-8
```

---

## 3. abaplint 設定の問題

### 3.1 対象外ファイルがリント対象になる

**症状:**
```
src/ZLOAP000900.prog.abap: 10 issues found
```
（開発対象でないファイルのエラーが報告される）

**原因:** `--file` オプション未使用で全 `src/` がスキャンされている。

**対処:** `sap_stage1_quality.py` は `--file` オプションで開発対象ファイルのみを指定する。手動実行時:
```bash
cd extensions/sap
npx @abaplint/cli --file "/../../src/<開発対象ファイル名>"
```

---

## 4. ADT API 制約

### 4.1 内容説明テキスト（Description）が変更できない

**症状:**
```
Error: 423 Invalid Lock Handle (PUT /sap/bc/adt/functions/groups/.../fmodules/.../source/main)
Error: 405 Method Not Allowed (POST _action)
```
または、`create_object.js` で登録時に内容説明を間違えた場合。

**原因:** ADT REST API ではオブジェクトの description を作成後に変更する手段がない（API 制約）。

**対処:**
1. **最善策**: `create_object.js` で作成する際に正しい description を指定する
2. **事後変更**: `update_description.js` を使用して SAP GUI スクリプティング経由で更新:
   ```bash
   node extensions/sap/tools/update_description.js --type function_module --name Z_MY_FM --description "正しい説明"
   node extensions/sap/tools/update_description.js --type program --name ZREPORT --description "正しいタイトル"
   node extensions/sap/tools/update_description.js --type class --name ZCL_MY_CLASS --description "正しい説明"
   ```
3. **前提条件**: SAP GUI がインストール済みで、スクリプティングが有効であること（RZ11: `sapgui/user_scripting = TRUE`）
