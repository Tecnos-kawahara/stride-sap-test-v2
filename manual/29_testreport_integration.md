# testreport 連携ガイド

## 1. testreport とは

[testreport](https://github.com/Tecnos-Japan-NGB/testreport) は Go 製の CLI ツールで、テストエビデンスを管理し HTML レポートを生成します。

- `cases.json` にテストケースを定義
- フォルダにスクリーンショット等のエビデンスファイルを配置
- `testreport generate` で HTML 1ファイルのレポートを自動生成
- `testreport validate` で cases.json とエビデンスの整合性を検証

STRIDE エコシステムでは **stride-testreport-bridge** を介して testreport の成果物を stride-lint の品質チェックに組み込みます。

## 2. STRIDE との連携方法

### ディレクトリ構成

```
specs/FEAT-XXX/
├── basic_design.md
├── spec.md
├── plan.md
├── tasks.md
├── process.bpmn
├── APPROVAL.md
└── testreport/              ← testreport 専用ディレクトリ
    ├── cases.json           ← テストケース定義
    ├── stride_mapping.yaml  ← STRIDE AC マッピング（任意）
    ├── 01_login.png         ← スクリーンショット等
    ├── 02_data_entry.png
    └── report.html          ← testreport generate の出力
```

> `testreport/` の代わりに `evidence/` ディレクトリも検索対象です。

### セットアップ手順

1. feature ディレクトリ配下に `testreport/` を作成
2. `cases.json` を配置（testreport の仕様に従う）
3. エビデンスファイル（スクリーンショット等）を配置
4. （推奨）`stride_mapping.yaml` を作成し、テストケースを STRIDE の AC に紐付け
5. `testreport generate` でレポート生成
6. `stride-lint` 実行時に自動的に連携チェックが走る

## 3. stride_mapping.yaml の書き方

stride_mapping.yaml は testreport のテストケースと STRIDE の受入基準（AC）を紐付けるファイルです。

```yaml
# stride_mapping.yaml
mappings:
  - case_id: "01_data_register"
    stride_refs:
      - "AC-US-FEAT001-001-01"

  - case_id: "02_data_update"
    stride_refs:
      - "AC-US-FEAT001-002-01"
      - "AC-US-FEAT001-002-02"

  - case_id: "03_validation_error"
    stride_refs:
      - "AC-US-FEAT001-003-01"

gate: "Tasks Gate"  # 任意: どの Gate で検証するか
```

### フィールド説明

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `mappings[].case_id` | ○ | cases.json 内の `id` に対応するテストケース ID |
| `mappings[].stride_refs` | ○ | 対応する STRIDE の AC ID（複数可） |
| `gate` | × | このエビデンスが紐付く Gate（情報用） |

### case_id の特定方法

cases.json の各エントリから以下の優先順で ID を取得します:
1. `id` フィールド
2. `case_id` フィールド
3. `name` フィールド

## 4. stride-lint での検証内容

stride-lint は Evidence Pack 検証の直後に testreport 連携チェックを実行します。

### 検証項目

| コード | レベル | 内容 |
|--------|--------|------|
| `TESTREPORT_REPORT_MISSING` | Warning | cases.json はあるが report.html がない |
| `TESTREPORT_VALIDATE_FAILED` | Warning | `testreport validate` が失敗した |
| `TESTREPORT_UNMAPPED_CASES` | Warning | stride_mapping.yaml に未登録のケースがある |

### 重要な動作仕様

- **cases.json がない場合**: チェックをスキップ（testreport 未使用として扱う）
- **testreport コマンド未インストール**: validate チェックのみスキップ、他は実行
- **stride_mapping.yaml がない場合**: マッピングチェックのみスキップ
- すべて **Warning** レベル（Error ではない）のため、既存の lint パスに影響しない

### CLI での単独実行

```bash
# テキスト出力
python3 sdd-templates/tools/stride_testreport_bridge.py specs/FEAT-XXX/

# JSON 出力
python3 sdd-templates/tools/stride_testreport_bridge.py specs/FEAT-XXX/ --json

# カスタムマッピングファイル指定
python3 sdd-templates/tools/stride_testreport_bridge.py specs/FEAT-XXX/ --mapping-file path/to/mapping.yaml

# セルフテスト
python3 sdd-templates/tools/stride_testreport_bridge.py --test
```

## 5. CI/CD での使い方

### GitHub Actions

`.github/workflows/stride-lint.yml` に testreport 検証ステップが含まれています。

```yaml
- name: Check testreport integration
  if: steps.check-specs.outputs.has_specs == 'true'
  run: |
    if command -v testreport &> /dev/null; then
      for dir in specs/*/testreport; do
        [ -d "$dir" ] && testreport validate "$dir" || true
      done
    fi
  continue-on-error: true
```

- testreport がインストールされている CI 環境でのみ validate を実行
- `continue-on-error: true` により、失敗してもパイプラインは止まらない
- stride-lint 自体の testreport チェックも別途実行される

### testreport を CI にインストールする場合

```yaml
- name: Install testreport
  run: |
    go install github.com/Tecnos-Japan-NGB/testreport@latest
```

## 6. ベストプラクティス

### マッピングの網羅性

すべての testreport ケースを STRIDE AC にマッピングすることを推奨します。`TESTREPORT_UNMAPPED_CASES` 警告が出る場合は、以下を確認してください:

- 新規追加したテストケースのマッピング漏れ
- AC ID の typo
- 探索的テストなど AC に紐付かないケースの意図的な除外

### エビデンスの整理

```
testreport/
├── cases.json
├── stride_mapping.yaml
├── 01_login/              ← ケースごとにサブフォルダも可
│   ├── step1.png
│   └── step2.png
├── 02_data_entry.png
└── report.html
```

### レポート生成のタイミング

- テスト実施後、PR 作成前に `testreport generate` を実行
- `report.html` は Git にコミットするかどうかはプロジェクト方針に従う
- CI で生成する場合は artifacts としてアップロードを推奨

### Evidence Pack との関係

testreport のレポートは Evidence Pack の一部として位置付けられます。`plan.md` の `evidence_pack` セクションで `testreport/report.html` を `required_artifacts` に含めることで、stride-lint の Evidence Pack 検証とも連動します。

```yaml
# plan.md の evidence_pack セクション例
evidence_pack:
  required_artifacts:
    - "testreport/report.html"
    - "coverage/coverage-summary.json"
  storage:
    path: "evidence/"
```
