# Phase 1.5: SAP Context Acquisition — 詳細手順

> **compaction 後は本ファイルを再読すること。**

Phase 1.5 は **任意** のフェーズ。SAP 実機接続による情報補完が必要な場合にのみ実行する。

## Step 1.5-A1: SAP オブジェクト検索

- **ツール**: `search.js`（**conversational** — 自律実行可）
- basic_design.sap_context を参照し、関連 SAP オブジェクトを検索

## Step 1.5-A2: SAP ソース参照

- **ツール**: `read.js`（**conversational** — 自律実行可）
- 検索結果のオブジェクトのソースコード・メタデータを参照

## Step 1.5-A3: SAP ソース取得

- **ツール**: `pull.js`（**gated** — 人間承認必須。Rule S3）
- 取得対象オブジェクトのソースをローカルにプル
- **pull.js を人間の承認なしに実行することは gated authority 違反**

## Step 1.5-B1: sap_context.md 記録

- **実行主体**: AI
- `implementation-details/sap_context.md` に以下を記録:
  - SAP パッケージ情報
  - 参照テーブルの構造確認結果
  - T100 メッセージ引当状況
  - 既存類似オブジェクトの調査結果
- basic_design.sap_context を源泉として参照

## Step 1.5-B2: テーブルメタデータ記録

- **ツール**: `sap_context_metadata.py --tables`
- basic_design.database.data_references[].tables のメタデータを sap_context.md に追記

## Step 1.5-C1: T100 メッセージ検証

- **ツール**: `sap_message_t100_validator.py`
- basic_design.catalogs.messages[].t100 の class/number が SAP 実機に実在するか検証
- 未登録の T100 → WARNING（新規登録が必要）

## Step 1.5-C2: DDIC 存在検証

- **ツール**: `sap_ddic_gate_validator.py`
- basic_design.database.data_references[].tables が DDIC に実在するか検証
- 存在しないテーブル → ERROR

## 承認済み成果物の変更ルール

本 Phase の作業中に、先行 Gate で承認済みの成果物（basic_design.md, process.bpmn 等）を修正する必要が生じた場合:
1. `implementation-details/change_log.md` に変更内容・理由・影響範囲を記録する
2. 意味的変更（要件追加・削除等）の場合は人間に再承認を相談する
3. フォーマット修正のみ（lint 準拠等）の場合は change_log 記録のみで続行可

**change_log を記録せずに承認済み成果物を変更してはならない。**
