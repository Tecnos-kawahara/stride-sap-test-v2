# CLAUDE_SAP.md — SAP Extension Pack v2.0.0 Rules

## Rule S1: basic_design 起点必須

Phase 2 以降の全成果物は **basic_design.md を起点として生成**すること。
yaml は参考参照のみ許可。成果物に書く内容の起点は必ず basic_design から取ること。

## Rule S2: サンクチュアリ保護（SAP 追加分）

v6.0.0 標準の保護対象に加え、`extensions/sap/MANIFEST.yaml` も保護対象。
バージョン・検出条件の変更は人間判断。AI が編集してはならない。

## Rule S3: SAP ツール実行権限

- **conversational**（自律実行可）: `search.js`, `read.js`, `data_preview.js`, `create_object.js`, `activate.js`, `run_tests.js`, `gui_test.js`, `evidence_capture.js`, lint 系ツール
- **gated**（人間承認必須）: `pull.js`
- **prohibited**: SAP 本番系への直接アクセス、TR の本番リリース、ユーザーマスタ変更

`pull.js` を人間の承認なしに実行することは gated authority 違反。

## Rule S4: WI メタデータ必須

Phase 4 WI 開始時に以下を記録すること:
- `sap_transport`: TR 番号（人間から提示されるまで WI を開始しない）
- `sap_objects`: 対象 SAP オブジェクト配列（type + name）
- `sap_owner`: 担当者

TR 番号未設定 or sap_objects 空の状態で Step 6（実装）に進むことは prohibited。

## Rule S5: ABAP メッセージ・エラーハンドリング

- T100 メッセージクラスから引き当てること。ハードコード禁止
- 禁止例: `MESSAGE 'テキスト' TYPE 'E'.`
- 正しい例: `MESSAGE e001(zmsg_class) WITH lv_field.`
- エラーハンドリングは T100 + CX_ 例外クラスで統一

## Rule S6: ABAP 実装指針

**(a) 共通クラス優先**: `config/common_class_rules.yaml` の共通クラスが適用可能なら使用する
**(b) SAP 標準 API 優先**: カスタムロジックより BAPI / CDS ビュー / 標準関数モジュールを優先

## Rule S7: SAP 固有 risk_flags ガイダンス

以下の risk_flags が検出された WI は validate mode で実行する:
- `accounting_calc`: CALC カタログに金額計算がある場合
- `db_schema`: data_references に新規テーブル（gate: empty）がある場合
- `authz`: screens[].access_control にロール別制御がある場合
