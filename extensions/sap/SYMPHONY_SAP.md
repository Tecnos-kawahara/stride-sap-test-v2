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

SAP 開発ではオープン系開発よりも転写精度が求められるため、Symphony エージェントは Phase 完了時の Issue コメントに以下の**トレーサビリティ報告**を含めなければならない。

この報告は、後続のローカル Claude Code での修正作業において、エージェントの判断を追跡するための唯一のコンテキストとなる。

### 報告テンプレート

```markdown
## Phase N 完了報告

### 成果物
- （生成したファイル一覧）

### 転写整合性レポート（Phase 1 のみ）

#### コピー対象セクションの転写結果
| yaml セクション | 転写結果 | 備考 |
|----------------|---------|------|
| catalogs.calculations | ✅ N件転写 | |
| catalogs.checks | ✅ N件転写 | |
| （全マッピング対象を列挙） | | |

#### 検出した不整合
ソース YAML 内で検出した不整合を列挙する。不整合がない場合は「なし」と記載。
- （例: processes.P3.body 内の MSG-013 参照が catalogs.messages に存在しない）
- （例: object_definitions.interfaces が空配列だが、header/processes の記述からインターフェース機能と推定される）

#### AI 構成セクション
マッピングテーブルの「AI 導出セクション」および「自然言語セクション」として AI が構成した内容の要約。
- traceability_rows: N件生成（RQ-001〜RQ-NNN）
- devObjects: （生成したオブジェクト一覧）
- context/scope/bpmn_descriptions 等: （構成の要点）

### バリデータ実行結果
- （バリデータ名: PASS/FAIL + 件数）

### stride-lint 結果
- Phase N 固有エラー: N件
- 残エラー: N件（原因の要約）
```

### 報告ルール

1. **転写整合性レポートは Phase 1 (Design) で必須**。他の Phase では省略可
2. **検出した不整合は必ず全件列挙する**。マッピングルール（phase1_design.md）により AI による無断修正は禁止されているため、不整合はエラーとして報告し人間の判断を仰ぐ
3. **AI 構成セクションは「何を構成したか」の概要**を記載する。構成の詳細は basic_design.md 本体を参照
4. この報告は出力トークンの制約内で簡潔に記載する。詳細な判断理由や思考過程は不要
