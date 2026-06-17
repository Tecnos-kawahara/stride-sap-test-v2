# Phase 1: Design — SAP 拡張詳細手順

> **compaction 後は本ファイルを再読すること。**

## 前提条件（Phase 1 開始前に完了していること）

| # | 条件 | 確認方法 |
|---|------|---------|
| 1 | `stride init <feature> --detect` が実行済み | `specs/<feature>/basic_design.md`（テンプレート）が存在する |
| 2 | `.stride-extensions.yaml` で SAP 拡張が有効 | `active_extensions` に `sap` が含まれている |
| 3 | `CLAUDE_SAP.md` を読み込み済み | Rule S1〜S7 を理解している |
| 4 | `CLAUDE_WORKFLOW_SAP.md` を読み込み済み | Phase 概要と検証ツール一覧を理解している |
| 5 | yaml（function_group_spec + feature_spec）が準備済み | 転記元となる yaml ファイルのパスが特定できている |

**上記が1つでも未完了の場合、Step 1-A1 に進んではならない。**
特に `stride init` を実行せずに basic_design.md を作成すると、APPROVAL.md・state.yaml・ディレクトリ構造が欠落し、stride lint や Phase Gate が正常に動作しない。

---

## Step 1-A1: yaml → basic_design.md 生成

AI（`04_ツール個別設計.md §A-1` マッピングテーブルに従い）転記する。

### 構造化データの転記（マッピングテーブル通りにコピー。要約・解釈・改変は禁止）

| yaml セクション (v2) | basic_design セクション | 備考 |
|---------------------|----------------------|------|
| catalogs.calculations | catalogs.calculations | |
| catalogs.checks | catalogs.checks | |
| catalogs.messages | catalogs.messages | |
| object_definitions.screens | object_definitions.screens | |
| object_definitions.files | object_definitions.files | |
| object_definitions.reports | object_definitions.reports | |
| object_definitions.interfaces | object_definitions.interfaces | |
| object_definitions.tables | object_definitions.tables | |
| **requirements** | **business_requirements** | yaml 側キー名 `requirements` → BD 側キー名 `business_requirements`（**キー名が異なる。変換必要**） |
| sap_context | sap_context | |
| processes | processes | |
| **programDetail** | **sap_context（統合）** | SE38属性等を sap_context 内の対応フィールドに転記 |
| **header.responseRequirement** | **responseRequirement** | **個別機能の方**をマッピング（群ではなく） |
| testMatrix | **test_matrix**（matrix 形式: columns + test_cases） | |

**不整合検出時の行動規範:**
転記中にソース yaml 内の不整合（存在しないカタログ ID の参照、空配列だが文脈上必要と思われるセクション等）を検出した場合:
- **AI が独自判断で修正・補完してはならない**
- 不整合の内容と箇所を明示的にエラーとして報告し、人間に修正を依頼する
- 人間がソース yaml を修正した後、再度転記を実行する

**AI 導出セクション**（yaml からのコピーではない）:
- `traceability_rows`: Phase 1-A1 で AI が `processes[].body` のパターン分岐検出から生成。Phase 1-A2 で追記
- `devObjects`: `header.programType` + `header.programId` から機械的に導出。MSAG は不要（programType で指定されたオブジェクトのみ）

**固定値の設定**:
- `profile: "enterprise-erp"`
- `erp_integration: true`
- `security_sensitive: true`

**削除セクション**: ed_cf_score, autonomy_bias, agentops_policy, e2e_policy

### 自然言語セクションの構成（AI が STRIDE フレーミングに適合する形で構成）

対象: context（who/what/why）、scope（in/out）、bpmn_descriptions（process/elements）、integration_flows、assumptions、decisions、business_value、raci_plus

`flow_reference.process_bpmn_path` を設定。`bpmn_descriptions.elements[].bpmn_id` に BPMN-TASK-NNN 形式を使用。

**このステップが yaml を参照する最後のステップ。** 以降は Rule S1 により basic_design を起点とする。

## Step 1-A2: パターン分岐検出

`processes[].body` のテキストから分岐パターンを検出する:
- 国内/海外、法人/個人、単体/連結 等のパターン分岐
- 検出した分岐を独立した `traceability_rows` エントリとして追記

> **Note**: risk_flags の判定は Phase 3 (Tasking) で WI 作成時に標準フローで行う。Phase 1 では判定しない。

## Step 1-B1: process.bpmn 生成

v6.0.0 §4-BPMN 準拠:
1. FEAT テンプレを literal copy
2. プレースホルダ置換
3. ノード/フロー修正
4. 14 ハード要件チェック（namespace / isExecutable / incoming-outgoing 等）
5. bpmn_descriptions.elements[].bpmn_id とのトレーサビリティ確認

SAP 拡張は BPMN 生成に追加ルールなし。

## Step 1-C1: yaml 全要素の展開確認

**ツール**: `basic_design_completeness_validator.py`

yaml の全要素が basic_design に展開されているか検証。欠落がある場合 ERROR を出力。
この検証により Phase 2 以降で yaml を参照する必要性を排除する（Rule S1 の前提条件）。

## Step 1-C2: カタログ整合性

**ツール**: `catalogs_consistency_validator.py`

- CHK → MSG 紐付け検証（checks[].message_ref → messages[]）
- processes[].body 内の ID 参照（CALC-XX, CHK-XX, MSG-XX）整合性
- object_definitions 内の calc_ref / message_ref 整合性

## Step 1-C3: STRIDE 標準 lint

**ツール**: `stride lint`

- traceability_rows ID 形式検証
- counts 整合性
- BPMN 14 ハード要件
- Gate 状態検証

## サイズ制約

basic_design.md の最終サイズは **~30,000 tokens 以下** であること。
これを超える場合は自然言語セクションの冗長性を削減するか、構造化データの inline 展開を contracts/ に分離する。

## 承認済み成果物の変更ルール

本 Phase の作業中に、先行 Gate で承認済みの成果物を修正する必要が生じた場合:
1. `implementation-details/change_log.md` に変更内容・理由・影響範囲を記録する
2. 意味的変更（要件追加・削除等）の場合は人間に再承認を相談する
3. フォーマット修正のみ（lint 準拠等）の場合は change_log 記録のみで続行可

**change_log を記録せずに承認済み成果物を変更してはならない。**

**Gate 1, 2 承認**: Step 1-C1〜C3 が全て PASS した後、人間が APPROVAL.md の Gate 1/2 を承認する。
