# Phase 2: Specify — SAP 拡張詳細手順

> **compaction 後は本ファイルを再読すること。**

v6.0.0 標準フローに従い、以下の SAP 固有差分を適用する。

## 2系統テストパス（重要）

SAP 拡張では 2 系統のテストパスを運用する:

### Type A: 要件駆動

`traceability_rows` → spec.md AC → scenarios.yaml（`traceability_ref` で紐付け）

- 各要件（RQ）に対応する AC を定義し、AC がシナリオで検証される
- 従来の STRIDE 標準パス

### Type B: テスト仕様駆動

`test_matrix` → scenarios.yaml（`test_matrix_ref` で紐付け）。**spec AC を経由しない。**

- test_matrix.test_cases[].id（数値型）を直接シナリオの test_matrix_ref で参照
- シナリオ ID は `TS-TM-` プレフィックス
- **理由**: RQ に紐付かない AC はトレーサビリティを壊す。test_matrix のテストケースは要件ではなくテスト仕様であり、AC を経由させると整合性が崩れる

## AC 生成ルール（catalog_refs）

spec.md の acceptance 生成時:
- 各 AC に `catalog_refs` フィールドを設定（その AC が独立検証するカタログ項目）
- 独立した条件は独立した AC にする（1 AC に複数独立条件をまとめない）
- 同一 CHK の分岐パス別 AC は可
- 正常系完了やカタログ外の AC は `catalog_refs: []`

## シナリオ設計ルール（SD-01〜SD-08）

| # | ルール |
|---|--------|
| SD-01 | LOG ステップを含むシナリオに BALHDR を se16_checks に付与 |
| SD-02 | INSERT シナリオに test_setup.run_program を設定 |
| SD-03 | DB_READ 複数ステップ → 部分取得シナリオパターン追加 |
| SD-04 | バッチプログラム → expected_result に最終メッセージ、applog_contains に中間メッセージ |
| SD-05 | sap_path_enumerator.py + sap_scenario_generator.py を参考にする（出力は「提案」であり SSoT ではない） |
| SD-06 | covers_ts にはパス通過 PS に紐づく e2e AC のみ含める |
| SD-07 | spec に unit タグ AC がある場合、plan に unit_test_coverage セクションを動的追加 |
| SD-08 | バッチ中間メッセージは applog_contains フィールドを動的追加 |

## plan.path_analysis セクション

basic_design.process_definitions[].body を解析し:
- `normal_paths`: 正常系パス
- `abnormal_paths`: 異常系パス
- `ai_decisions`: AI の判断事項

## SAP 固有 contracts テンプレート

basic_design.object_definitions の内容に応じて、以下のマッピングで contracts/ にファイルを生成する。
該当する object_definitions が空の場合はファイル生成をスキップする。

| object_definitions | contracts ファイル | テンプレート（§B-6） |
|---|---|---|
| screens[] | `contracts/selection_screen.yaml` | ui_specifications_template |
| reports[] | `contracts/report_output.yaml` | report_specifications_template |
| files[] | `contracts/file_specifications.yaml` | file_specifications_template |
| interfaces[] | `contracts/openapi.yaml` | openapi_template |
| — (database.data_references) | `contracts/database_schema.yaml` | database_schema_template |
| — (spec.sap_specifics) | `implementation-details/authz_matrix.yaml` | authz_matrix_template |

## 承認済み成果物の変更ルール

Phase 2 作業中に Gate 1/2 承認済みの成果物（basic_design.md, process.bpmn）を修正する必要が生じた場合:
1. `implementation-details/change_log.md` に変更内容・理由・影響範囲を記録する
2. 意味的変更（要件追加・削除等）の場合は人間に再承認を相談する
3. フォーマット修正のみ（lint 準拠等）の場合は change_log 記録のみで続行可

**change_log を記録せずに承認済み成果物を変更してはならない。**

## 検証（SAP 拡張 lint）

stride lint 実行時に MANIFEST.yaml 経由で以下が自動実行:
- `catalogs_consistency_validator`: カタログ整合性 + message_mapping type 整合性 + **R9: spec.message_class ↔ catalogs.messages[].t100.class 一致**
- `glossary_ref_validator`: domain_terms_ref 参照先存在確認
- `sap_ac_granularity_validator`: catalog_refs カバレッジ + 独立性 + マスタ存在チェック網羅性
- `plan_quality_validator`: covers_ts 形式 + **PQ-09（test_matrix 全件カバレッジ）** + **PQ-10（scenarios.yaml feature_id 一致）** + **PQ-11〜15（plan SAP fields ↔ basic_design クロスファイル整合性）**
- `sap_message_t100_validator`: t100 形式チェック再実行（class/number 非空、status 値検証）
- `sap_contracts_cross_validator`: **CX-01〜05（contracts/ ↔ basic_design/spec クロスファイル整合性）**
- `basic_design_completeness_validator`: **L3-01（spec AC → traceability_rows 逆方向一致）**（Phase 1 で実行済みだが、spec 生成後に再実行して逆方向チェックを追加検証）

**Gate 3, 4 承認**: 全 lint PASS 後、人間が APPROVAL.md の Gate 3/4 を承認する。
