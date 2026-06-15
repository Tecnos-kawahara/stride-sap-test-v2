# SYMPHONY_SAP.md — Symphony 実行時の SAP 拡張入力設定

> このファイルは Symphony オーケストレーション経由で Phase が実行される場合にのみ参照される。
> 手動実行（Claude Code を直接起動）の場合は読む必要はない。

## 仕様書 YAML 入力（Phase 1: Design）

Symphony 経由で Phase 1（Design）が実行される場合、Issue body に **`spec_yaml_path`** フィールドが指定されていることがある。

### 取得手順

1. Issue body のマークダウンテーブルから `spec_yaml_path`（または `Spec File`）フィールドを探す
2. 値が存在し、そのパスにファイルが存在する場合 → そのファイルを仕様書 YAML として Phase 1-A1 の入力に使用する
3. 値が存在しない場合 → 従来通り Issue body の内容から Phase 1 を実行する

### 仕様書 YAML の扱い

- ファイルはリポジトリ内の任意のパス（`spec_yaml_path` で指定）
- `function_group_spec.yaml` と `feature_spec.yaml` の 2 ファイル構成、または単一ファイルの場合がある
- ディレクトリパスが指定された場合は、そのディレクトリ内の YAML ファイルを全て読む
- 読み取った YAML は `extensions/sap/agent_docs/phase1_design.md` Step 1-A1 の mapping テーブルに従い、`basic_design.md` の #0 Canonical YAML セクションに機械的に転写する

### Issue テンプレート例

```markdown
| Field | Value |
|-------|-------|
| Feature | FEAT-EDI-001 |
| spec_yaml_path | docs/yaml/FEAT-EDI-001/ |
```
