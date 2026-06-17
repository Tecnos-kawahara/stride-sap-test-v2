# SYMPHONY_SAP.md — Symphony 実行時の SAP 拡張入力設定

> このファイルは Symphony オーケストレーション経由で Phase が実行される場合にのみ参照される。
> 手動実行（Claude Code を直接起動）の場合は読む必要はない。

## 仕様書 YAML 入力（Phase 2 前準備）

Symphony 経由で Phase が実行される場合、Issue body に以下の 2 つのフィールドが指定されていることがある。
Phase 2 前準備（SAP Context Acquisition）において、これらの値を参照し basic_design.md への転写に使用する。

| フィールド | 内容 |
|-----------|------|
| `group_spec_yaml_path` | 機能群仕様書 YAML（`function-group-spec/v2`） |
| `feature_spec_yaml_path` | 個別機能仕様書 YAML（`feature-spec/v2`） |

### 取得手順

1. Issue body から `### Group Spec YAML Path` セクションの値を取得する
2. Issue body から `### Feature Spec YAML Path` セクションの値を取得する
3. 両方（または片方）の値が存在し、そのパスにファイルが存在する場合 → 仕様書 YAML として basic_design.md への転写入力に使用する
4. 値が存在しない、または空の場合 → 該当パスなしで処理を続行する

### 仕様書 YAML の扱い

- **機能群 YAML**（`group_spec_yaml_path`）: 業務概要、機能一覧、実行条件、前提条件など機能群全体の情報を含む。basic_design.md の業務仕様セクション（#0 Canonical YAML 等）に転写する
- **機能 YAML**（`feature_spec_yaml_path`）: 対象機能のインプット/アウトプット定義、プロセス定義、チェック仕様、オブジェクト定義など個別機能の詳細を含む。basic_design.md の機能仕様セクションに転写する
- 読み取った YAML は `extensions/sap/agent_docs/phase1_design.md` Step 1-A1 の mapping テーブルに従い、`basic_design.md` に機械的に転写する
