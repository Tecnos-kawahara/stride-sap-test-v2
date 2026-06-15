# Appendix D. トラブルシューティング

---

## このガイドについて

SDDテンプレート使用時によくある問題と解決方法をまとめています。

---

## 1. stride-lint エラー

### 1.1 PLACEHOLDER_VALUE_PRESENT

**症状**:
```
WARNING: PLACEHOLDER_VALUE_PRESENT
  Found: "FEAT-XXX" in feature_id
```

**原因**: テンプレートのプレースホルダが置換されていない

**解決方法**:
```bash
# 一括置換（サブディレクトリも含む）
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/my_feature/*.md specs/my_feature/*/*.md specs/my_feature/*/*.yaml
sed -i '' 's/FEATXXX/001/g' specs/my_feature/*.md specs/my_feature/*/*.md specs/my_feature/*/*.yaml
sed -i '' 's/XXX_feature_name/my_feature/g' specs/my_feature/*.md specs/my_feature/*/*.md specs/my_feature/*/*.yaml
sed -i '' 's/{{FEATURE_NAME}}/my_feature/g' specs/my_feature/*.md specs/my_feature/*/*.md specs/my_feature/*/*.yaml
sed -i '' 's/{{FEATURE_ID}}/001/g' specs/my_feature/*.md specs/my_feature/*/*.md specs/my_feature/*/*.yaml
```

---

### 1.2 AC_NOT_COVERED

**症状**:
```
ERROR: AC_NOT_COVERED
  AC-US-FEAT001-001-03 is not covered by any test
```

**原因**: 受入条件がテストでカバーされていない

**解決方法**:
```yaml
# plan.md のテストに追加
tests:
  - id: "TS-INT-02"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-03"  # 追加
```

---

### 1.3 TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE

**症状**:
```
ERROR: TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE
  AC-US-FEAT001-001-01 (tag: integration) covered by TS-UT-01 (type: unit)
```

**原因**: integrationタグのACがユニットテストでしかカバーされていない

**解決方法**:
```yaml
# plan.md - テスト種別を変更
tests:
  - id: "TS-INT-01"            # TS-INT-* に変更
    type: "integration"        # integration に変更
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-01"
```

---

### 1.4 TEST_NOT_TASKED

**症状**:
```
ERROR: TEST_NOT_TASKED
  TS-INT-01 is not tasked
```

**原因**: plan.md のテストが tasks.md でタスク化されていない

**解決方法**:
```yaml
# tasks.md
tasks:
  - id: "T-G03-001"
    plan_refs:
      - "TS-INT-01"  # 追加
```

---

### 1.5 REF_NOT_FOUND

**症状**:
```
ERROR: REF_NOT_FOUND
  Reference "AC-US-FEAT001-001-01" not found in spec.md
```

**原因**: IDのタイポまたは参照先が存在しない

**解決方法**:
1. IDを確認（ハイフン、数字の桁数）
2. 参照元と参照先のIDを完全一致させる
3. コピペを推奨

---

### 1.6 INVALID_PLAN_REF

**症状**:
```
ERROR: INVALID_PLAN_REF
  "random-name" is not a valid stable id
```

**原因**: plan_refs に不正なIDが含まれている

**解決方法**:
```yaml
# tasks.md - stable id のみ使用
plan_refs:
  # ✅ 許可される形式
  - "CMP-01"
  - "LIB-01"
  - "CT-API-01"
  - "TS-INT-01"
  - "Phase-1"
  - "G-01-contracts"

  # ❌ 許可されない形式
  # - "random-name"
  # - "some-task"
```

---

### 1.7 E2E_TAG_OVERUSE（v1.2.4）

**症状**:
```
WARNING: E2E_TAG_OVERUSE
  e2e tagged ACs: 8 (26.7% of total 30 ACs)
  Recommended: max 5 or 20% of total ACs
```

**原因**: e2eタグが過剰に使用されている（5件超または20%超）

**解決方法**:
- e2eタグは重要なユーザージャーニー（例: ログイン→購入→決済）のみに限定
- 単体機能のテストは `integration` タグを使用

```yaml
# spec.md - e2eを厳選する
acceptance_criteria:
  - id: "AC-US-FEAT001-001-01"
    tags: ["e2e"]           # ← クリティカルパスのみ
  - id: "AC-US-FEAT001-001-02"
    tags: ["integration"]   # ← その他はintegrationに
```

---

### 1.8 POST_APPROVAL_CHANGE（v1.2.4）

**症状**:
```
WARNING: POST_APPROVAL_CHANGE
  File specs/my_feature/spec.md was modified after Gate 3 approval
```

**原因**: ゲート承認後にファイルが変更された

**解決方法**:
1. APPROVAL.md の該当ゲートを再承認
2. または `git checkout` で変更を元に戻す

---

### 1.9 COUNTS_MISMATCH（v1.2.4）

**症状**:
```
ERROR: COUNTS_MISMATCH
  spec.counts.acceptance_criteria: declared=3, actual=5

SUGGESTION: Copy the following to fix counts:
---
counts:
  acceptance_criteria: 5
---
```

**原因**: counts の宣言値と実際の数が一致しない

**解決方法**:
提示されたYAMLをコピペして修正

```yaml
# spec.md
derived_fields:
  counts:
    acceptance_criteria: 5   # ← 提示された値に更新
```

---

### 1.10 APPROVAL_PENDING（v1.2.4）

**症状**:
```
ERROR: APPROVAL_PENDING
  Gate 3 (Spec) requires approval before proceeding
```

**原因**: 次のPhaseに進むために必要な承認が未完了

**解決方法**:
1. 人間が APPROVAL.md を編集
2. 該当ゲートのチェックボックスをオン `[x]`
3. 署名と日付を記入

```markdown
## Gate 3: Spec
- [x] 受入条件（AC）が適切に定義されている
- [x] 非機能要件（NFR）が定義されている

承認者: 山田太郎
日付:   2025-01-15
```

---

## 2. YAML パースエラー

### 2.1 インデントエラー

**症状**:
```
ERROR: YAML_PARSE_ERROR
  Indentation error at line 50
```

**原因**: YAMLのインデントが不正

**解決方法**:
```yaml
# ❌ 間違い（インデント不一致）
tasks:
  - id: "T-G01-001"
  title: "Task 1"     # ← インデントが足りない

# ✅ 正しい
tasks:
  - id: "T-G01-001"
    title: "Task 1"   # ← 正しいインデント
```

---

### 2.2 クォートの問題

**症状**:
```
ERROR: YAML_PARSE_ERROR
  Unexpected character at line 30
```

**原因**: 特殊文字がエスケープされていない

**解決方法**:
```yaml
# ❌ 間違い
statement: This contains: a colon

# ✅ 正しい（クォートで囲む）
statement: "This contains: a colon"
```

---

## 3. ゲート通過できない

### 3.1 Basic Design Gate

**チェック項目**:
- [ ] traceability_rows が 1行以上ある
- [ ] integration_flows が 1件以上ある
- [ ] blocking質問が 0件
- [ ] delivery_model が設定されている
- [ ] raci_plus が設定されている
- [ ] ready_for_bpmn が true

**確認方法**:
```yaml
# basic_design.md の gate_check を確認
basic_design_gate_check:
  traceability_present: true    # ← true か?
  delivery_model_defined: true  # ← true か?
  ready_for_bpmn: true          # ← true か?
```

---

### 3.2 Spec Gate

**チェック項目**:
- [ ] use_cases が 1件以上
- [ ] acceptance_criteria が 3件以上
- [ ] integration タグ付きACが 1件以上
- [ ] nfr_items が 6件以上（各カテゴリ1件以上）
- [ ] spec_as_code が定義されている
- [ ] blocking質問が 0件

---

### 3.3 Plan Gate

**チェック項目**:
- [ ] contracts が 1件以上
- [ ] tests が 2件以上
- [ ] integration_tests が 1件以上
- [ ] groups が 3件以上
- [ ] evidence_pack が定義されている

---

### 3.4 Tasks Gate

**チェック項目**:
- [ ] tasks が 5件以上
- [ ] 全 TS が tasks に紐付いている
- [ ] 循環依存がない
- [ ] plan_refs が stable id のみ

---

## 4. IDの問題

### 4.1 IDの形式がわからない

**参照**: [08. ID規約リファレンス](appendix_a_id_conventions.md)

| カテゴリ | 形式 | 例 |
|----------|------|-----|
| Feature | FEAT-XXX | FEAT-001 |
| Use Case | US-FEATXXX-NNN | US-FEAT001-001 |
| Acceptance | AC-US-FEATXXX-NNN-NN | AC-US-FEAT001-001-01 |
| Contract | CT-TYPE-NN | CT-API-01 |
| Test | TS-TYPE-NN | TS-INT-01 |
| Task | T-GNN-NNN | T-G01-001 |

---

### 4.2 IDが重複している

**症状**:
```
ERROR: DUPLICATE_ID
  ID "AC-US-FEAT001-001-01" appears multiple times
```

**解決方法**: 連番を確認し、ユニークなIDに変更

---

## 5. counts の不一致

### 5.1 counts が実際と合わない

**症状**:
```
WARNING: COUNTS_MISMATCH
  spec.counts.acceptance_criteria: declared=3, actual=5
```

**解決方法**:
```yaml
# counts を更新
derived_fields:
  counts:
    acceptance_criteria: 5  # 実際の数に更新
```

---

## 6. BPMN の問題

### 6.1 incoming/outgoing がない

**症状**:
```
ERROR: BPMN_VALIDATION_FAILED
  Element BPMN-TASK-001 has no incoming/outgoing references
```

**解決方法**:
```xml
<bpmn:serviceTask id="BPMN-TASK-001">
  <bpmn:incoming>Flow_001</bpmn:incoming>  <!-- 追加 -->
  <bpmn:outgoing>Flow_002</bpmn:outgoing>  <!-- 追加 -->
</bpmn:serviceTask>
```

---

### 6.2 zeebe:taskDefinition がない

**症状**:
```
ERROR: BPMN_VALIDATION_FAILED
  ServiceTask BPMN-TASK-001 has no zeebe:taskDefinition
```

**解決方法**:
```xml
<bpmn:serviceTask id="BPMN-TASK-001">
  <bpmn:extensionElements>
    <zeebe:taskDefinition type="my-task-type"/>  <!-- 追加 -->
  </bpmn:extensionElements>
</bpmn:serviceTask>
```

---

## 7. Coverage Policy の問題

### 7.1 coverage_policy がない

**症状**:
```
WARNING: COVERAGE_POLICY_NOT_DEFINED
  plan.test_strategy.coverage_policy is missing
```

**解決方法**:
```yaml
# plan.md に追加
test_strategy:
  coverage_policy:
    acceptance_coverage_required: true
    tagged_acceptance_requirements:
      integration:
        enforce: true
        required_test_type: "integration"
```

---

## 8. 環境・依存関係の問題

### 8.1 PyYAML が見つからない

**症状**:
```
No module named 'yaml'
```

**解決方法**:
```bash
pip install pyyaml
```

---

## 9. よくある質問

### Q: stride-lint をインストールする方法は？

A: テンプレートに **同梱** されています。v1.2.4 からは `stride` CLI が使えます：

```bash
# 推奨: stride CLI（v1.2.4）
export PATH="$PATH:$(pwd)/sdd-templates/bin"
stride lint --all

# 従来の方法（引き続き動作します）
sdd-templates/tools/stride-lint --all
```

それでも動かない場合は PyYAML をインストールしてください。

---

### Q: Lite Mode はどんな時に使う？

A: 小規模プロジェクト、PoC、ソロ開発に適しています：

```bash
# Lite Mode で初期化
stride init --lite my_poc_feature

# Lite Mode で検証
stride lint --lite-mode specs/my_poc_feature/
```

通常の6段階ゲートを3段階（Gate A, B, C）に簡略化します。

---

### Q: 承認後にファイルを変更したら警告が出た

A: `POST_APPROVAL_CHANGE` 警告です。対処方法：

1. **変更が意図的**: APPROVAL.md の該当ゲートを再承認
2. **変更が誤り**: `git checkout` で元に戻す

---

### Q: 既存プロジェクトに導入するには？

A: 段階的に導入することを推奨します：

1. `--warn-only` で現状を確認
2. 重大なエラーから修正
3. 徐々に `--warn-only` を外す

---

### Q: テンプレートを更新する方法は？

A: `sdd-templates/MIGRATION.md` を参照してください。

---

### Q: stride init で「Feature ID is too short」エラーが出る（v1.2.4）

A: Feature ID は最小3文字必要です。Constitution の regex `FEAT-[A-Z0-9]{3,}` に準拠する必要があります：

```bash
# ❌ エラー: 2文字以下
stride init ab          # Error: Feature ID 'AB' is too short

# ✅ 正しい: 3文字以上
stride init abc         # OK → FEAT-ABC
stride init my_feature  # OK → FEAT-MYFEATURE
stride init web_edi     # OK → FEAT-WEBEDI
```

> **注**: アンダースコア、ハイフンは自動的に削除され、大文字に変換されます。

---

### 1.11 ID_REGEX_MISMATCH

**症状**:
```
ERROR: ID_REGEX_MISMATCH
  ID "FEAT-AB" does not match pattern "^FEAT-[A-Z0-9]{3,}$"
```

**原因**: IDがconstitution.mdの正規表現に一致しない

**解決方法**:
- Feature ID は最低3文字必要（例: `FEAT-ABC` ✅, `FEAT-AB` ❌）
- ID規約は `memory/constitution.md` の `id_conventions` を参照

---

### 1.12 GATE_EXPRESSION_UNRESOLVED

**症状**:
```
ERROR: GATE_EXPRESSION_UNRESOLVED
  Cannot evaluate gate expression for Gate 3
```

**原因**: constitution.md のゲート式が評価できない

**解決方法**:
1. `memory/constitution.md` の `gates` セクションを確認
2. `requires` フィールドの式が正しい形式か確認
3. 参照している変数が存在するか確認

---

### 1.13 DATABASE_SCHEMA_UNDEFINED

**症状**:
```
ERROR: DATABASE_SCHEMA_UNDEFINED
  database_schema_id referenced but not defined in spec_as_code
```

**原因**: データベーススキーマがspec_as_codeで定義されていない

**解決方法**:
```yaml
# spec.md
spec_as_code:
  artifacts:
    - type: "database_schema"
      path: "specs/<feature>/contracts/schema.sql"
      schema_version: "1.0"
```

---

### 1.14 APPROVAL_FILE_MISSING

**症状**:
```
ERROR: APPROVAL_FILE_MISSING
  APPROVAL.md not found in specs/my_feature/
```

**原因**: APPROVAL.md ファイルが存在しない

**解決方法**:
```bash
# stride init で自動作成
stride init my_feature

# または手動でコピー
cp sdd-templates/templates/APPROVAL.md specs/my_feature/
```

---

### 1.15 SPEC_AS_CODE_MISSING

**症状**:
```
ERROR: SPEC_AS_CODE_MISSING
  spec_gate_check.spec_as_code_defined is true but no artifacts defined
```

**原因**: Spec-as-Codeが必須だが成果物が未定義

**解決方法**:
```yaml
# spec.md
spec_as_code:
  artifacts:
    - type: "openapi"
      path: "specs/my_feature/contracts/openapi.yaml"
```

---

### 1.16 EVIDENCE_PACK_NOT_DEFINED

**症状**:
```
ERROR: EVIDENCE_PACK_NOT_DEFINED
  plan_gate_check.evidence_pack_defined is true but evidence_pack not configured
```

**原因**: Evidence Packの定義が不完全

**解決方法**:
```yaml
# plan.md
test_strategy:
  evidence_pack:
    required_artifacts:
      - "ci_results"
      - "sast"
      - "sca"
    storage:
      path: "specs/my_feature/implementation-details/evidence_pack.md"
```

---

### 1.17 ARTIFACT_REGISTRY_INVALID

**症状**:
```
ERROR: ARTIFACT_REGISTRY_INVALID
  memory/artifact_registry.md is missing required fields
```

**原因**: 成果物マスターが不正または不完全

**解決方法**:
```bash
# テンプレートをコピー
cp sdd-templates/memory/artifact_registry.md memory/
```

---

### 1.18 E2E_REPORTING_NOT_CONFIGURED

**症状**:
```
WARNING: E2E_REPORTING_NOT_CONFIGURED
  e2e-tagged ACs exist but reporting.e2e is not configured
```

**原因**: E2Eタグ付きACがあるのにレポート設定がない

**解決方法**:
```yaml
# plan.md
test_strategy:
  reporting:
    e2e:
      html_report: true
      artifacts_dir: "specs/<feature>/tests/reports/e2e/"
```

---

### 1.19 E2E_TRIAGE_NOT_DEFINED

**症状**:
```
WARNING: E2E_TRIAGE_NOT_DEFINED
  e2e-tagged ACs exist but e2e-triage.md is not defined
```

**原因**: E2E失敗時のトリアージ手順が未定義

**解決方法**:
```bash
# トリアージ手順ファイルを作成
touch specs/<feature>/implementation-details/e2e-triage.md
```

---

### 1.20 INVALID_PATH_NAMING

**症状**:
```
WARNING: INVALID_PATH_NAMING
  Path "my-feature/tests" contains hyphen, use snake_case
```

**原因**: ファイル/ディレクトリ名にハイフンが含まれている

**解決方法**:
- ハイフン `-` をアンダースコア `_` に置換
- 例: `my-feature` → `my_feature`

---

## 10. サポート連絡先

- **テンプレート質問**: Architecture チーム
- **stride-lint エラー**: 本ガイドを確認後、Architecture チームへ
- **移行相談**: MIGRATION.md を参照

---

> SDD Templates Manual - 11. Troubleshooting
