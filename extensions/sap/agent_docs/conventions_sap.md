# ABAP Development Conventions（SAP固有）

> SAP 拡張パックの命名規約・ファイル構成ルール。標準の `agent_docs/conventions.md` と併用すること。

## ファイル命名規則（abaplint準拠）

| オブジェクト種別 | ファイル拡張子 | ディレクトリ構成 |
|----------------|--------------|----------------|
| クラス本体 | `.clas.abap` | `src/<package>/<name>/<name>.clas.abap` |
| クラステスト | `.clas.testclasses.abap` | `src/<package>/<name>/<name>.clas.testclasses.abap` |
| プログラム | `.prog.abap` | `src/<package>/<name>/<name>.prog.abap` |
| 汎用モジュールグループ | `.fugr.abap` | `src/<package>/<name>/<name>.fugr.abap` |
| インターフェース | `.intf.abap` | `src/<package>/<name>/<name>.intf.abap` |

## SAP オブジェクト名規約
- カスタムオブジェクトは `Z` または `Y` 名前空間プレフィックスを使用
- abaplint で検証: `extensions/sap/config/abaplint.json`
- 詳細パターン: `extensions/sap/templates/abap/PATTERNS.md`

## SAP WI メタデータ拡張フィールド
WI に以下の SAP 固有メタデータを記録する:
- `sap_transport`: TR番号（$TMP の場合は空文字）
- `sap_objects`: 対象SAPオブジェクト一覧
- `sap_owner`: `.env` の `SAP_USERNAME`
