# SAP Extension Pack: v1 → v2 移行ガイド

## 概要

SAP Extension Pack v2.0.0 は STRIDE v6.0.0 向けに全面再設計されました。
v1（STRIDE v5.x 向け）からの移行には以下の変更への対応が必要です。

## 破壊的変更

### 1. processing_steps 廃止

| 項目 | v1 | v2 |
|------|----|----|
| 処理定義 | `spec.processing_steps[]` | `basic_design.process_definitions[].body` |
| パス列挙 | processing_steps[].tag | process_definitions body + `config/tag_branch_rules.yaml` |
| シナリオ生成 | processing_steps + spec | path_enumerator output + basic_design |

**対応**: spec.md の processing_steps を basic_design.md の process_definitions に移行する。

### 2. referenced_tables → data_references

| 項目 | v1 | v2 |
|------|----|----|
| テーブル参照 | `basic_design.referenced_tables[]` | `basic_design.database.data_references[].tables[]` |
| バリデータ | なし | `sap_ddic_gate_validator.py` |

**対応**: referenced_tables の全テーブルを data_references 形式に変換する。

### 3. T100 status 値セット変更

| 項目 | v1 | v2 |
|------|----|----|
| 有効な status | registered / unregistered / pending / ok / empty | **ok / empty のみ** |
| バリデータ | なし | `sap_message_t100_validator.py` |

**対応**: catalogs.messages[].t100.status を ok または empty に修正する。

### 4. test_matrix 形式変更

| 項目 | v1 | v2 |
|------|----|----|
| テストケース | `cases[].axis` (文字列 ID) | `test_cases[].id` (数値型) + `columns/values` マトリクス |
| テストパス | 要件駆動のみ | Type A (要件駆動) + Type B (テスト仕様駆動) |

**対応**: cases[] を test_cases[] + columns 形式に変換。Type B シナリオを追加。

### 5. テンプレート方式変更

| 項目 | v1 | v2 |
|------|----|----|
| テンプレート | 独立完全版 | overlay 方式（v6.0.0 標準への差分のみ） |
| 削除セクション | — | ed_cf_score / autonomy_bias / agentops_policy / e2e_policy |

### 6. ワークフロー文書構造変更

| 項目 | v1 | v2 |
|------|----|----|
| CLAUDE_SAP.md | ルール + 手順 + 権限テーブル (~4000 tokens) | **ルールのみ** (~800 tokens) |
| CLAUDE_WORKFLOW_SAP.md | 全手順一括 | **概要のみ** + agent_docs/ 参照 |
| agent_docs/ | 3 ファイル (testing/conventions/error_recovery) | **9 ファイル** (Phase別 6 + 引継 3) |

## 新機能

### evidence_capture.js 拡張
- `--recapture <scenario>`: シナリオ再実行 + SLG1 再キャプチャ
- `--replace-screenshot <name> <file>`: スクショ差し替え
- `--update-data <table> <json>`: データセクション再生成
- EC-01〜EC-05: SELECT-OPTIONS -LOW / BALHDR→SLG1 / evidence_data 自動削除 / BALHDR タイムフィルタ / columns パラメータ

### update_description.js S/4HANA 対応
- SE38: `radRS38M-FUNC_HEAD` + `btnCHAP` + wnd[1] モーダル（確定パッチ）
- SE37/SE24: S/4HANA モーダル自動検出 + ECC フォールバック

### create_object.js --textpool
- プログラム作成後の textpool 自動登録（ADT API / GUI フォールバック）

### 新規バリデータ 7 件
C1〜C7: basic_design_completeness / catalogs_consistency / glossary_ref / sap_message_t100 / sap_ddic_gate / sap_ac_granularity / plan_quality

## ツール分類（引継 / 再設計 / 除外）

### 引継ツール（v1 からそのまま or 改修して継続使用）

| ツール | 分類 | 改修内容 |
|--------|------|---------|
| `evidence_capture.js` | 引継・改修 | EC-01〜05 バグ修正 + EC-M1〜M3 モード追加 |
| `evidence_merge_report.js` | 引継 | 変更なし |
| `create_object.js` | 引継・改修 | `--textpool` オプション追加 |
| `activate.js` | 引継 | 変更なし |
| `pull.js` | 引継 | 変更なし |
| `read.js` | 引継 | 変更なし |
| `search.js` | 引継 | 変更なし |
| `data_preview.js` | 引継 | 変更なし |
| `run_tests.js` | 引継 | 変更なし |
| `gui_test.js` | 引継 | 変更なし |
| `update_description.js` | 引継・改修 | S/4HANA モーダル対応パッチ |
| `clean_abap.js` | 引継 | 変更なし |
| `sap_quality_score.py` | 引継・改修 | template_compliance カテゴリを新版テンプレに合わせて更新 |
| `sap_common_class_lint.py` | 引継 | 変更なし |
| `sap_context_metadata.py` | 引継 | 変更なし |
| `sap_branch_analyzer.py` | 引継 | 変更なし |
| `sap_program_type_validator.py` | 引継 | 変更なし |
| `sap_tool_evidence_validator.py` | 引継 | 変更なし |
| `sap_s_evidence_validator.py` | 引継・改修 | test_green_confirmation の v2 構造に対応 |

### 再設計ツール（v1 にも存在したが v2 で完全再設計）

| ツール | 旧版 | 新版の設計 |
|--------|------|-----------|
| `sap_path_enumerator.py` | processing_steps[].tag ベースのパス列挙 | process_definitions[].body + tag_branch_rules.yaml ベースに完全再設計 |
| `sap_scenario_generator.py` | path_enumerator 出力から直接シナリオ生成 | 提案モード（SSoT ではない）+ `_proposal: True` フラグ付き |

### 新規ツール（v2 で新たに追加）

| ツール | 用途 |
|--------|------|
| `basic_design_completeness_validator.py` | C1: yaml→basic_design 展開完全性検証 |
| `catalogs_consistency_validator.py` | C2: カタログ整合性検証 |
| `glossary_ref_validator.py` | C3: domain_terms_ref 参照確認 |
| `sap_message_t100_validator.py` | C4: T100 メッセージ存在検証 |
| `sap_ddic_gate_validator.py` | C5: DDIC テーブル存在検証 |
| `sap_ac_granularity_validator.py` | C6: AC catalog_refs カバレッジ検証 |
| `plan_quality_validator.py` | C7: plan 品質検証（PQ-01〜PQ-09） |

### 除外ツール（v1 に存在したが v2 では不要）

| 旧版ツール | 除外理由 | v2 での代替手順 |
|------------|---------|----------------|
| `sap_expand_traceability.py` | yaml の testMatrix は basic_design.test_matrix にそのまま転記。traceability_rows は AI が別途生成（目的が異なる） | basic_design.test_matrix に yaml.testMatrix をそのまま転記。traceability_rows は Phase 1-A1 で AI が生成 |
| `sap_adjust_templates.py` | テンプレート値は新版テンプレに最初から正しく設定されている | `stride init --detect` が SAP 完成版テンプレートを自動配置。手動調整不要 |
| `sap_ac_generator.py` | yaml の checks → basic_design.catalogs.checks → AI が AC に変換（標準 STRIDE フロー） | Phase 2 で AI が catalogs.checks を読み AC を生成。`sap_ac_granularity_validator.py` がカバレッジを検証 |
| `checklist_suggest`（sap_phase2_spec_tools.py 内） | yaml に情報があるため不要 | yaml.checks がそのまま catalogs.checks に転記済み。AI が spec.md で直接参照 |
| `message_suggest`（sap_phase2_spec_tools.py 内） | yaml に情報があるため不要 | yaml.messages がそのまま catalogs.messages に転記済み。AI が spec.md で直接参照 |
| `scenario_generator`（sap_phase2_scenario_tools.py 内） | yaml.testMatrix が源泉のため不要（sap_scenario_generator.py は再設計版として別途存在） | `sap_scenario_generator.py` + `sap_path_enumerator.py` が Type A/B シナリオを自動生成 |

## 旧版固有ファイルの扱い

| ファイル | v1 | v2 での扱い |
|----------|----|-----------| 
| `CLAUDE_SAP.md` | ルール + 手順 + 権限テーブル | **置換**: ルールのみ（Rule S1-S7）に縮小 |
| `CLAUDE_WORKFLOW_SAP.md` | 全手順一括 | **置換**: 概要 + ⛔参照テーブルのみ |
| `agent_docs/testing_sap.md` | テスト戦略ガイド | **引継**: そのまま利用 |
| `agent_docs/conventions_sap.md` | 命名規約 | **引継**: そのまま利用 |
| `agent_docs/error_recovery_sap.md` | エラーリカバリ | **引継**: そのまま利用 |
| `agent_docs/phase*.md` (6 件) | 存在しない | **新規作成**: Phase 別詳細手順 |
| 旧版バッチスクリプト群 | batch_scripts セクション | **削除**: 個別ツールに分解済み |
| 旧版 phase_hooks | phase_hooks セクション | **削除**: v6.0.0 本体の hook メカニズムで代替 |

## 設定ファイルの移行手順

### .stride-extensions.yaml

v1 と同じ形式。`active_extensions` に `sap` が含まれていれば動作する。変更不要。

### MANIFEST.yaml

v1 の MANIFEST.yaml は**全面置換**が必要。v2 では:
- `manifest_version: "2.0.0"` に変更
- `extension` ブロック（name/version/description/min_stride_version/author）に構造変更
- `tools` セクションが validators/mapping_refs/utilities/sap_operations の 4 層に分離
- `phase_steps` セクション新規追加
- `agent_docs` に `load_timing` フィールド追加
- `templates` が overlays/partial_templates の 2 層構造に変更
- `evidence_pack` セクション新規追加

**対応**: `extensions/sap/MANIFEST.yaml` を v2.0.0 版で完全置換する。

### config/ ファイル

| ファイル | 移行 |
|----------|------|
| `quality_score_config.yaml` | template_compliance カテゴリを新版テンプレに合わせて更新。他は変更なし |
| `common_class_rules.yaml` | 変更なし |
| `test_perspective_master.yaml` | 変更なし |
| `test_suggest_config.yaml` | 変更なし |
| `tool_evidence_registry.yaml` | 新版ステップに合わせてステップ→ツール対応表を更新 |
| `tag_branch_rules.yaml` | **新規**: v2 で追加。12 タグルール定義 |

## 移行チェックリスト

- [ ] basic_design.md の processing_steps → process_definitions に変換
- [ ] referenced_tables → database.data_references に変換
- [ ] T100 status を ok/empty に修正
- [ ] test_matrix を columns + test_cases 形式に変換
- [ ] MANIFEST.yaml を v2.0.0 に更新
- [ ] CLAUDE_SAP.md / CLAUDE_WORKFLOW_SAP.md を v2 に置換
- [ ] agent_docs/ に Phase 別 6 ファイルを配置
- [ ] npm install（extensions/sap/ 配下）
