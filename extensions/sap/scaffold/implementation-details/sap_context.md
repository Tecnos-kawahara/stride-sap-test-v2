# SAP Context - FEAT-XXX
> Step 1.5-SAP (R1-R4) コンテキスト記録
> 実施日:

## R1: 対象オブジェクト確認

| オブジェクト | タイプ | パッケージ | 状態 | 確認結果 |
|---|---|---|---|---|
| | | | | |

## R2: パッケージ / TR 確認

- **パッケージ**:
- **移送番号**:

## R3: ソース取得

-

## R4: コンテキスト記録

### 参照テーブル（実機確認済み）

| テーブル | 用途 | 確認方法 | フィールド確認 |
|---|---|---|---|
| | | | |

### 使用する Released API

| API | 用途 |
|---|---|
| | |

### 権限オブジェクト

| オブジェクト | フィールド | チェック値 |
|---|---|---|
| | | |

### ABAP Cloud 制約

- **Tier**:
- **制約**:
- **DDIC新規作成**:

### テストデータの状況

-

## メタデータ（ツール参照用 — sap_context_metadata.py で自動生成）

> このセクションは `sap_ac_generator.py` / `evidence_capture.js` が参照する構造化データ。
> `sap_context_metadata.py` で DDL / ソース / data_preview から自動生成する。
> 手動編集も可能だが、自動生成後に手動で追記・修正した場合はコメントで明記すること。

```yaml
metadata:
  # テーブルメタデータ（Phase 1.5 R3 で adt_read_table_ddl + adt_data_preview から生成）
  tables: {}
  # 例:
  #   MCHB:
  #     label: "ロット在庫"
  #     key_fields: ["MATNR", "WERKS", "LGORT", "CHARG"]
  #     quantity_fields: ["CLABS", "CINSM", "CSPEM"]
  #     fields:
  #       MATNR: { label: "品目コード" }
  #       WERKS: { label: "プラント" }

  # 選択画面メタデータ（Phase 1.5 R2 で既存ソースから、または Phase 2.2 で spec から生成）
  selection_screen: []
  # 例:
  #   - { name: "S_WERKS", type: "select-options", table_field: "MCHB-WERKS", obligatory: true, label: "プラント" }
  #   - { name: "P_ZERO", type: "checkbox", obligatory: false, label: "ゼロ在庫除外" }
```
