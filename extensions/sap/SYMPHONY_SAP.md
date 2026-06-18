# SYMPHONY_SAP.md — Symphony 実行時の SAP 拡張設定

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

## Issue コメント報告要件（SAP 拡張）

SAP 開発ではオープン系開発よりも転写精度が求められるため、Symphony エージェントは Phase 完了時の Issue コメントに**トレーサビリティ報告**を含めなければならない。

この報告には 2 つの目的がある:
1. **後続のローカル Claude Code での修正作業**において、エージェントの判断を追跡するためのコンテキスト
2. **上流インプット（ソース YAML 等）の改善**に繋げるため、AI がどう解釈・判断したかの記録

### 報告テンプレート

```markdown
## Phase N 完了報告

### 成果物
- （生成したファイル一覧）

### 転写サマリ（Phase 1 のみ）
- 転写件数: catalogs N件 / object_definitions N件 / processes N件 / ...
- 正常転写: 問題なし or 以下の例外あり

### 検出した不整合（Phase 1 のみ）
ソース YAML 内で検出した不整合を全件列挙する。不整合がない場合は「なし」と記載。
各不整合について**なぜ不整合と判断したか**（どの記述とどの記述が矛盾しているか等）を記載する。

- 例: `processes.P3.body` に `MSG-013` への参照があるが、`catalogs.messages` には MSG-001〜MSG-008 しか定義されていない。P3 の文脈（「登録失敗時」）から MSG-007 が該当すると推定されるが、ソース YAML 側の修正が必要
- 例: `object_definitions.interfaces` が空配列だが、`header.ricefPattern` に「#4 AP-File入力→アドオンDB」と記載されており、外部ファイル連携のインターフェース定義が記載漏れと推定される

### AI が判断・構成したセクション（Phase 1 のみ）
マッピングテーブルの「AI 導出セクション」「自然言語セクション」として AI が構成した内容について、**何をどう判断して構成したか**を記載する。

- traceability_rows: N件生成。（どの processes/checks から導出したかの要点）
- devObjects: （何を根拠にどのオブジェクトを導出したか）
- context/scope: （group YAML と feature YAML のどの部分をどう統合したか）
- bpmn_descriptions: （processes からどうマッピングしたか）

### バリデータ実行結果
- （バリデータ名: PASS/FAIL + 件数）

### stride-lint 結果
- Phase N 固有エラー: N件
- 残エラー: N件（原因の要約）
```

### 報告ルール

1. **転写サマリ・不整合・AI 判断セクションは Phase 1 (Design) で必須**。他の Phase では省略可
2. **正常に転写できたセクションは件数のみ**でよい。全セクションの表形式列挙は不要
3. **検出した不整合は全件列挙する**。マッピングルール（phase1_design.md）により AI による無断修正は禁止されているため、不整合はエラーとして報告し人間の判断を仰ぐ
4. **AI の判断・解釈の思考過程を残す**。「なぜそう判断したか」が分かれば、上流のインプットファイルをどう修正すべきかの判断材料になる。単に「何をしたか」だけでなく「ソース YAML のどの記述をどう解釈した結果こうなった」まで書く
