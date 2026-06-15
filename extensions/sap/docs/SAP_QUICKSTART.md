# SAP 拡張パック v2.0.0 クイックスタートガイド

本ドキュメントは SAP 拡張パック v2.0.0 の概要を5分で理解するためのクイックスタートガイドです。

---

## 1. 前提条件

| 項目 | 要件 |
|------|------|
| Node.js | 18 以上 |
| Python | 3.8 以上 |
| Claude Code | 最新版 |
| STRIDE | v6.0.0 以上 |
| SAP 環境 | S/4HANA 開発環境（ADT REST API 有効） |
| 接続情報 | `.env` ファイルに SAP_URL / SAP_CLIENT / SAP_USERNAME / SAP_PASSWORD を設定済み |

> `.env` の設定方法やインストール手順の詳細は [SETUP.md](../SETUP.md) を参照してください。

---

## 2. 全体の流れ -- 5 Phase で理解する

SDD（Spec-Driven Development）では「仕様が契約、コードは生成物」という原則のもと、以下の 5 フェーズ（+ Final）で開発を進めます。

```
Phase 1: Design         --> basic_design.md 作成 + AI 構成 --> Gate 1,2 承認
                              |
Phase 1.5: SAP Context  --> SAP 実機からコンテキスト取得（任意）
                              |
Phase 2: Specify         --> spec.md + plan.md + contracts/ 作成 --> Gate 3,4 承認
                              |
Phase 3: Tasking         --> tasks.md 作成 --> Gate 5 承認
                              |
Phase 4: Execute         --> WI 16-step フロー（実装 + テスト）--> WI 承認
                              |
Final                    --> 受入テスト + エビデンス + PR Readiness --> Final 承認
```

### 各フェーズの概要

| フェーズ | 何をするか | 主な検証ツール |
|---------|-----------|---------------|
| **Phase 1: Design** | basic_design.md を yaml から転記・作成し、sap_context を構成する。Gate 1,2 で人間が承認。 | `basic_design_completeness_validator`, `catalogs_consistency_validator`, `stride lint` |
| **Phase 1.5: SAP Context** | SAP 実機から既存ソース・テーブル定義・DDIC 情報を取得し sap_context.md に記録する（任意フェーズ）。 | `sap_message_t100_validator`, `sap_ddic_gate_validator` |
| **Phase 2: Specify** | 詳細仕様（spec.md）、実行計画（plan.md）、contracts/ を作成する。Gate 3,4 で人間が承認。 | `sap_ac_granularity_validator`, `plan_quality_validator`, `glossary_ref_validator`, `stride lint` |
| **Phase 3: Tasking** | SAP 開発順序に準拠した実装タスク一覧（tasks.md）を作成する。Gate 5 で人間が承認。 | `stride lint`（tasks_gate_check） |
| **Phase 4: Execute** | ABAP ソースの実装 -- アクティベーション -- テスト。WI 16-step フローで SAP 固有ステップを統合して実行。 | `sap_quality_score` >= 85pt, `sap_common_class_lint` |
| **Final** | 受入テスト + エビデンス取得 + Ops Pack 作成。統合レポート生成と PR Readiness Check。 | `erp_addon_exec_tracking`, `stride pr-check` 7/7 |

---

## 3. クイックセットアップ（初回のみ）

初回のみ以下を実行します。詳細な手順は [SETUP.md](../SETUP.md) を参照してください。

### 3-1. `.env` ファイルを設定

テンプレートルート（`CLAUDE.md` が存在するディレクトリ）に `.env` を作成し、SAP 接続情報を記入します。

```
SAP_URL=https://10.1.1.8:44300
SAP_CLIENT=240
SAP_USERNAME=DEVELOPER
SAP_PASSWORD=********
```

### 3-2. 依存パッケージをインストール

```bash
cd extensions/sap/
npm install
```

### 3-3. SAP 接続テスト

```bash
node extensions/sap/tools/search.js object TADIR
```

正常にオブジェクト一覧が返れば接続成功です。

---

## 4. 人間がやること / AI がやること

| 作業 | 担当 | 備考 |
|------|------|------|
| basic_design.md の要件記入 | 人間 | program_type, branches, message_class 等 |
| Gate 承認（APPROVAL.md 編集） | 人間 | AI が APPROVAL.md を編集することは絶対禁止 |
| TR 番号の確定 | 人間 | SE09/SE10 で確認。TR 未設定では Execute に進めない |
| テストデータの準備 | 人間 | AI がデータ不足を検知して依頼する |
| pull.js の実行承認 | 人間 | gated authority -- 人間の承認なしに実行禁止 |
| basic_design 構成 + 検証 | AI | `basic_design_completeness_validator`, `catalogs_consistency_validator` |
| SAP コンテキスト取得 | AI | `search.js`, `read.js`, `pull.js`（承認後）, `sap_context_metadata.py` |
| T100 / DDIC 整合性検証 | AI | `sap_message_t100_validator`, `sap_ddic_gate_validator` |
| spec.md / plan.md / contracts 作成 | AI | パス列挙・シナリオ生成 + 各種 validator で品質保証 |
| tasks.md 作成 | AI | SAP 開発順序でタスク構成 |
| ABAP ソース実装 | AI | `create_object.js` + `activate.js` |
| テスト実行 | AI | `run_tests.js` + `gui_test.js` -- 全テスト GREEN まで自律ループ |
| エビデンス取得 | AI | `evidence_capture.js` |
| 統合レポート生成 | AI | `evidence_merge_report.js` |
| 品質スコア算定 | AI | `sap_quality_score` >= 85pt |
| 最終レビュー | 人間 | エビデンスレポートの目視確認 |

---

## 5. よく使うコマンド -- Phase 別リファレンス

### Phase 1: Design

```bash
# Feature 初期化
stride init <feature_name> --detect

# 構造検証
sdd-templates/bin/stride lint specs/<feature>/

# basic_design 完全性チェック
python3 extensions/sap/tools/basic_design_completeness_validator.py specs/<feature>/

# カタログ整合性チェック
python3 extensions/sap/tools/catalogs_consistency_validator.py specs/<feature>/
```

### Phase 1.5: SAP Context

```bash
# SAP オブジェクト検索
node extensions/sap/tools/search.js object <search_term>

# ソース読取
node extensions/sap/tools/read.js <object_type> <object_name>

# ソース取得（gated -- 人間の承認必須）
node extensions/sap/tools/pull.js <object_type> <object_name>

# SAP コンテキストメタデータ生成
python3 extensions/sap/tools/sap_context_metadata.py specs/<feature>/

# T100 メッセージ整合性検証
python3 extensions/sap/tools/sap_message_t100_validator.py specs/<feature>/

# DDIC ゲート検証
python3 extensions/sap/tools/sap_ddic_gate_validator.py specs/<feature>/
```

### Phase 2: Specify

```bash
# テストパス列挙
python3 extensions/sap/tools/sap_path_enumerator.py specs/<feature>/

# テストシナリオ生成
python3 extensions/sap/tools/sap_scenario_generator.py specs/<feature>/

# AC 粒度検証
python3 extensions/sap/tools/sap_ac_granularity_validator.py specs/<feature>/

# 計画品質検証
python3 extensions/sap/tools/plan_quality_validator.py specs/<feature>/

# 用語集参照整合性チェック
python3 extensions/sap/tools/glossary_ref_validator.py specs/<feature>/

# 構造検証（各 Phase 完了時に必ず実行）
sdd-templates/bin/stride lint specs/<feature>/
```

### Phase 4: Execute

```bash
# SAP オブジェクト作成
node extensions/sap/tools/create_object.js <object_type> <object_name> <package> <tr_number>

# アクティベーション（Lock -> Upload -> Activate -> Unlock）
node extensions/sap/tools/activate.js <object_type> <object_name>

# ABAP Unit テスト実行
node extensions/sap/tools/run_tests.js <object_type> <object_name>

# GUI テスト実行
node extensions/sap/tools/gui_test.js <scenario_file>

# エビデンス取得
node extensions/sap/tools/evidence_capture.js specs/<feature>/

# 品質スコア算定（>= 85pt 必須）
python3 extensions/sap/tools/sap_quality_score.py specs/<feature>/

# 共通クラス lint
python3 extensions/sap/tools/sap_common_class_lint.py specs/<feature>/
```

### Final

```bash
# 統合エビデンスレポート生成
node extensions/sap/tools/evidence_merge_report.js specs/<feature>/

# ERP アドオン実行追跡
python3 sdd-templates/tools/erp_addon_exec_tracking.py specs/<feature>/

# PR Readiness Check（7/7 必須）
sdd-templates/bin/stride pr-check <project_root>
```

---

## 6. ドキュメント索引

### AI 向けドキュメント（agent_docs/ -- Phase 別詳細手順）

| ドキュメント | 内容 |
|-------------|------|
| `agent_docs/phase1_design.md` | Phase 1: Design の詳細手順 |
| `agent_docs/phase15_sap_context.md` | Phase 1.5: SAP Context Acquisition の詳細手順 |
| `agent_docs/phase2_specify.md` | Phase 2: Specify の詳細手順 |
| `agent_docs/phase3_tasking.md` | Phase 3: Tasking の詳細手順 |
| `agent_docs/phase4_execute.md` | Phase 4: Execute の詳細手順 |
| `agent_docs/phase_final.md` | Final Phase の詳細手順 |
| `agent_docs/conventions_sap.md` | SAP 命名規約 |
| `agent_docs/testing_sap.md` | SAP テスト詳細 |
| `agent_docs/codegen_sap.md` | SAP コード生成ガイド |
| `agent_docs/error_recovery_sap.md` | SAP エラーリカバリ手順 |
| `agent_docs/gui_test_fail_analysis.md` | GUI テスト失敗分析ガイド |

### ルール・設定ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [CLAUDE_SAP.md](../CLAUDE_SAP.md) | SAP 固有ルール（S1--S7） |
| [CLAUDE_WORKFLOW_SAP.md](../CLAUDE_WORKFLOW_SAP.md) | Phase 別ワークフロー概要（正本） |
| [SETUP.md](../SETUP.md) | 環境セットアップ手順 |

### 利用者向けドキュメント（docs/）

| ドキュメント | 内容 |
|-------------|------|
| [SAP_QUICKSTART.md](SAP_QUICKSTART.md) | 本ドキュメント（クイックスタート） |
| [SAP_TROUBLESHOOTING.md](SAP_TROUBLESHOOTING.md) | トラブルシューティング |
| [SAP_GUI_TEST.md](SAP_GUI_TEST.md) | GUI テストガイド |
| [SAP_TOOL_DEVELOPMENT_GUIDE.md](SAP_TOOL_DEVELOPMENT_GUIDE.md) | ツール開発ガイド |
| [migration_from_v1.md](migration_from_v1.md) | v1 からの移行ガイド |
| [phase4_final_structure.md](phase4_final_structure.md) | Phase 4 / Final の成果物構造 |
