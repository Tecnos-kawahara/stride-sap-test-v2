# Appendix B. stride-lint 使用ガイド

---

## このガイドで学ぶこと

1. stride-lint とは
2. stride CLI（現行 / v4.9対応）
3. 基本的な使い方
4. Lite Mode（3段階承認）
5. Default Coverage Summary
6. エラーコード一覧
7. オプション
8. 出力フォーマット（v5.0.0）
9. CI/CD での使用

---

## 1. stride-lint とは

### 定義

**stride-lint** は、SDDテンプレートの品質を機械検証するツールです。

### 目的

1. **形骸化防止** - ドキュメントが実態と乖離していないか検証
2. **ゲート判定** - 各ゲートの通過条件を機械評価
3. **カバレッジ検証** - AC/CT/テストの網羅性を確認

---

### 1.1 stride-lint がチェックすること（初心者向け）

stride-lint は、**「埋め忘れ」と「整合性の崩れ」**を機械で検出します。  
主に以下の10種類をチェックします。

1. **ファイルと正本ブロック**
   - `basic_design.md / spec.md / plan.md / tasks.md` の Canonical YAML が存在するか
   - `memory/constitution.md` の `id_conventions` / `gates` が読めるか
   - エラー例: `MISSING_FILE`, `CANONICAL_BLOCK_NOT_FOUND`, `YAML_PARSE_ERROR`

2. **ID形式（規約）**
   - すべてのIDが `constitution.md` の正規表現に一致するか
   - エラー例: `ID_REGEX_MISMATCH`

3. **参照整合（リンク切れ検出）**
   - basic_design の US/AC が spec に存在するか
   - plan.tests の `covers_*` が spec/plan のIDに存在するか
   - tasks の `plan_refs` が plan の stable id だけか
   - エラー例: `REF_NOT_FOUND`, `INVALID_PLAN_REF`

4. **カバレッジ（抜け漏れ）**
   - **AC 100%** がテストでカバーされているか
   - `integration` / `e2e` タグが指定テスト種別でカバーされているか
   - `coverage_policy` に従って CT / TS の網羅が満たされているか
   - エラー例: `AC_NOT_COVERED`, `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE`, `CONTRACT_COVERAGE_INCOMPLETE`, `TEST_NOT_TASKED`

5. **Gate条件**
   - `*_gate_check` の counts が実際と一致するか
   - `constitution.md` の `gates.requires` を満たしているか
   - エラー例: `COUNTS_MISMATCH`, `GATE_FAILED`

6. **Spec-as-Code / Evidence Pack**
   - `spec_as_code.artifacts` が定義されているか
   - `evidence_pack.required_artifacts` と `storage.path` があるか
   - エラー例: `SPEC_AS_CODE_MISSING`, `EVIDENCE_PACK_NOT_DEFINED`

7. **BPMN最低要件（Camunda 8）**
   - 必須namespace、executionPlatform、DI、serviceTask 定義など
   - エラー例: `BPMN_VALIDATION_FAILED`

8. **Artifact Registry**
   - `memory/artifact_registry.md` が必須項目を満たしているか
   - エラー例: `ARTIFACT_REGISTRY_INVALID`

9. **プレースホルダ残り / パス命名**
   - `FEAT-XXX` などが残っていないか
   - ファイル名がスネークケースか（ハイフン禁止）
   - エラー例: `PLACEHOLDER_VALUE_PRESENT`, `INVALID_PATH_NAMING`

10. **BDD Acceptance Criteria（v4.5）**
    - `bdd_mode: "required"` の場合、全タスクに `acceptance_criteria` があるか
    - BDD構造（id/scenario/given/when/then/verification）が完全か
    - `verification` が automated/manual/hitl のいずれかか
    - auth/payment/schema/security 関連タスクに `escalation_trigger: true` があるか
    - `automated` 比率が目標以上か
    - エラー例: `BDD_AC_MISSING`, `BDD_AC_INCOMPLETE`, `BDD_AC_INVALID_VERIFICATION`, `BDD_ESCALATION_MISSING`, `BDD_AUTOMATED_RATIO_LOW`

**注意**: stride-lint は **Canonical YAML だけ**を読みます。
本文の説明文だけを更新しても、検証は通りません。

---

## 2. stride CLI（現行 / v4.9対応）

現在は統一CLIツール `stride` が標準です。従来の長い Python パスを入力しなくても、`stride lint` と `stride epic` で主要操作を実行できます。

### 2.1 stride CLI のコマンド一覧

| コマンド | 説明 | 例 |
|----------|------|-----|
| `stride init <feature>` | 機能を全テンプレートで初期化 | `stride init my_feature` |
| `stride init --lite <feature>` | Lite Mode で初期化 | `stride init --lite poc_feature` |
| `stride lint <path>` | 仕様を検証（推奨） | `stride lint specs/my_feature/` |
| `stride lint <path> --enterprise` | Enterprise 拡張検証も実行 | `stride lint specs/FEAT-ERPSAMPLE/ --enterprise` |
| `stride lint --all --enterprise` | 全 Feature + 全 Epic を一括検証 | `stride lint --all --enterprise` |
| `stride lint --lite-mode` | Lite Mode で検証 | `stride lint --lite-mode specs/my_feature/` |
| `stride epic init <EPIC_ID>` | Epic 一式を初期化 | `stride epic init EPIC-ORDER` |
| `stride epic validate <EPIC_ID>` | Epic を検証 | `stride epic validate EPIC-ORDER` |
| `stride epic progress <EPIC_ID>` | Epic 進捗サマリを表示 | `stride epic progress EPIC-ORDER` |
| `stride phase-status` | Phase Gate 承認状況を表示 | `stride phase-status specs/my_feature/` |
| `stride phase-check <file>` | ファイル作成が許可されているか確認 | `stride phase-check specs/my_feature/spec.md` |
| `stride hooks` | Phase Gate hooks を自動設定 | `stride hooks` |
| `stride help` | ヘルプを表示 | `stride help` |

### 2.2 セットアップ

```bash
# PATHに追加する場合
export PATH="$PATH:$(pwd)/sdd-templates/bin"

# または、エイリアスを設定
alias stride="./sdd-templates/bin/stride"
```

### 2.3 クイックスタート

```bash
# 新規機能を初期化（全テンプレート + APPROVAL.md を自動作成）
stride init my_feature

# 仕様を検証
stride lint specs/my_feature/

# Enterprise Hierarchy を使う場合
cat > sdd-templates/config/enterprise.yaml <<'YAML'
enterprise:
  enabled: true
YAML
stride epic init EPIC-ORDER
stride init order_import --epic EPIC-ORDER --team TEAM-A
stride lint specs/order_import/ --enterprise

# Phase Gate 状況を確認
stride phase-status specs/my_feature/
```

### 2.4 従来コマンドとの対応

| 従来（v1.2.3以前） | 新CLI（v1.2.4） |
|--------------------|-----------------|
| `sdd-templates/tools/stride-lint specs/...` | `stride lint specs/...` |
| `python3 sdd-templates/tools/phase_gate.py status` | `stride phase-status` |
| `python3 sdd-templates/tools/setup_hooks.py` | `stride hooks` |

> **注**: 従来のコマンドも引き続き動作しますが、`stride` CLI の使用を推奨します。

---

## 3. 基本的な使い方

### 実行場所の注意

このリポジトリでは同梱版を正本とし、コマンドの正本は `agent_docs/commands.md` に記載します。
PATHに通していない場合は、同梱のコマンドを直接実行します。

```bash
sdd-templates/tools/stride-lint --all
```

### 単一機能の検証

```bash
sdd-templates/tools/stride-lint specs/my_feature/
```

### 警告のみモード

```bash
sdd-templates/tools/stride-lint specs/my_feature/ --warn-only
```

エラーがあっても終了コード 0 で終了（CIで失敗させない）

### カバレッジレポート出力

```bash
sdd-templates/tools/stride-lint specs/my_feature/ --coverage-report
```

**保存したい場合**:
```bash
sdd-templates/tools/stride-lint specs/my_feature/ --coverage-report > coverage_report.yaml
```

### 全機能の検証

```bash
sdd-templates/tools/stride-lint --all
```

### Enterprise 拡張検証

```bash
# 単一 Feature の enterprise 検証
sdd-templates/bin/stride lint specs/FEAT-ERPSAMPLE/ --enterprise

# 全 Feature + 全 Epic の enterprise 検証
sdd-templates/bin/stride lint --all --enterprise
```

`--enterprise` は `epic_ref` / `team_id` / `coverage_tier` / 共有契約の整合性を追加検証します。  
単一 Feature への `--enterprise` は **その Feature のみ** を拡張検証し、Epic まで含めるのは `--all --enterprise` のときだけです。

### 変更ファイルのみ検証

```bash
sdd-templates/tools/stride-lint --changed HEAD~1..HEAD
```

---

## 2.1 いつ実行するべきか（タイミングと頻度）

### 最低限の運用（推奨）

- **作業開始時**: テンプレートをコピーしてID置換が終わったら1回  
- **各ゲート前**: Basic Design / Spec / Plan / Tasks を提出する前に実行  
- **PR作成前**: PRを出す直前に実行（漏れの最終チェック）  
- **CIで毎回**: PRごとに必ず実行（自動で品質を担保）

### より安全な運用（余裕がある場合）

- **大きな編集の直後**: AC追加やテスト変更をしたら即実行  
- **BPMN更新後**: BPMNの整合性チェックのため必ず実行  
- **E2E追加後**: triageやreportingの漏れを検出するため実行  

### 目的別の使い分け

| 目的 | コマンド | 使いどころ |
|------|----------|-----------|
| 変更だけを確認したい | `sdd-templates/tools/stride-lint --changed <range>` | 小さな修正の後 |
| 全体をまとめて確認 | `sdd-templates/tools/stride-lint --all` | PR前 / リリース前 |
| まず警告だけ見たい | `sdd-templates/tools/stride-lint --warn-only` | 初期導入 / 既存案件 |

---

## 3.1 stride-lint（同梱版）

```bash
sdd-templates/tools/stride-lint specs/my_feature/ --warn-only
```

**依存関係**: Python環境に `PyYAML` が必要です（`pip install pyyaml`）。

**Homebrew Pythonの場合（macOS）**: `pip install` が拒否されることがあるため、
テンプレ内に venv を作成して実行します（同梱の `stride-lint` が自動で利用します）。

```bash
python3 -m venv sdd-templates/.venv
sdd-templates/.venv/bin/pip install pyyaml
```

---

## 4. Lite Mode（3段階承認）

### 4.1 Lite Mode とは

**Lite Mode** は、小規模プロジェクト、PoC、ソロ開発向けの簡易版ワークフローです。

通常の6段階ゲート（Gate 1〜5 + Final）を、3段階（Gate A, B, C）に簡略化します。

| 通常モード | Lite Mode | 含まれる内容 |
|-----------|-----------|-------------|
| Gate 1 (Design) + Gate 2 (BPMN) | Gate A | 基本設計 + BPMN承認 |
| Gate 3 (Spec) + Gate 4 (Plan) | Gate B | 仕様 + 計画 |
| Gate 5 (Tasks) + Final | Gate C | タスク + 最終承認 |

### 4.2 Lite Mode の使い方

```bash
# Lite Mode で初期化
stride init --lite my_poc_feature

# Lite Mode で検証
stride lint --lite-mode specs/my_poc_feature/

# APPROVAL.md の内容から自動検出
# (ファイルに "Gate A:" または "Lite Mode" が含まれていれば Lite Mode と判定)
```

### 4.3 APPROVAL.md (Lite Mode) の構造

```markdown
# APPROVAL (Lite Mode)

## Gate A: Design & Flow
- [ ] basic_design.md の WHO/WHAT/WHY が正しい
- [ ] 業務フロー（process.bpmn）が適切である

承認者: _____________________
日付:   _____________________

## Gate B: Spec & Plan
- [ ] spec.md 完了
- [ ] plan.md 完了

承認者: _____________________
日付:   _____________________

## Gate C: Implementation & Verification
- [ ] tasks.md 完了
- [ ] 実装完了
- [ ] Evidence Pack 収集完了

承認者: _____________________
日付:   _____________________
```

### 4.4 Lite Mode を使うべきケース

| ケース | 推奨 |
|--------|------|
| PoC / プロトタイプ | ✅ Lite Mode |
| ソロ開発 | ✅ Lite Mode |
| 小規模機能（AC 5件以下） | ✅ Lite Mode |
| エンタープライズ案件 | ❌ 通常モード |
| チーム開発（3人以上） | ❌ 通常モード |
| 監査対応が必要 | ❌ 通常モード |

---

## 5. Default Coverage Summary

### 5.1 v1.2.4 新機能

v1.2.4 から、`stride lint` を実行すると、**カバレッジ概要が常に表示**されます。

```
Coverage: ✓ AC 5/5 (100%)  ○ CT 2/3 (66.7%)
```

| 記号 | 意味 |
|------|------|
| ✓ | 100% カバー（完了） |
| ○ | カバレッジ不足あり |

### 5.2 表示項目

- **AC**: 受入条件のテストカバレッジ
- **CT**: 契約のテストカバレッジ

### 5.3 詳細レポート

詳細が必要な場合は `--coverage-report` を追加：

```bash
stride lint specs/my_feature/ --coverage-report
```

これにより、以下の詳細が出力されます：
- 未カバーのAC一覧
- 未カバーのCT一覧
- タグ付きACのカバレッジ（integration, e2e）
- 未タスク化のテスト一覧

---

## 6. エラーコード一覧

### ファイル・パース関連

| コード | 説明 | 対処 |
|--------|------|------|
| `MISSING_FILE` | ファイルが存在しない | パスを確認 |
| `CANONICAL_BLOCK_NOT_FOUND` | Canonical YAML ブロックがない | テンプレート構造を確認 |
| `YAML_PARSE_ERROR` | YAML構文エラー | インデント・構文を確認 |
| `INVALID_PATH_NAMING` | 参照パスのファイル名にハイフンがある | スネークケースに修正 |

### ID関連

| コード | 説明 | 対処 |
|--------|------|------|
| `ID_REGEX_MISMATCH` | ID形式が不正 | ID規約を確認 |
| `DUPLICATE_ID` | IDが重複 | ユニークなIDに変更 |
| `REF_NOT_FOUND` | 参照先IDが存在しない | 参照先を確認 |
| `INVALID_PLAN_REF` | plan_refs に不正なIDがある | stable idのみ使用 |
| `PLACEHOLDER_VALUE_PRESENT` | プレースホルダが残存 | XXXを実際の値に置換 |

### カバレッジ関連

| コード | 説明 | 対処 |
|--------|------|------|
| `AC_NOT_COVERED` | ACがテストでカバーされていない | covers_acceptance_ids に追加 |
| `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE` | タグ付きACが適切なテスト種別でカバーされていない | 正しいテスト種別を使用 |
| `CONTRACT_COVERAGE_INCOMPLETE` | CTがTS-CONでカバーされていない | TS-CON を追加 |
| `TEST_NOT_TASKED` | TSがタスク化されていない | tasks.md の plan_refs に追加 |
| `COVERAGE_POLICY_NOT_DEFINED` | coverage_policy が未定義 | plan.md に設定を追加 |

### レポート関連

| コード | 説明 | 対処 |
|--------|------|------|
| `E2E_REPORTING_NOT_CONFIGURED` | E2Eレポート設定がない | reporting.e2e を設定 |
| `E2E_TRIAGE_NOT_DEFINED` | E2E triage手順がない | e2e-triage.md を作成 |

### v1.2.3 追加

| コード | 説明 | 対処 |
|--------|------|------|
| `SPEC_AS_CODE_MISSING` | Spec-as-Codeが未定義 | spec.spec_as_code.artifacts を追加 |
| `EVIDENCE_PACK_NOT_DEFINED` | Evidence Packが未定義 | plan.test_strategy.evidence_pack を追加 |
| `ARTIFACT_REGISTRY_INVALID` | 成果物マスターが不正 | artifact_registry.md を確認 |

### v1.2.4 追加

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `E2E_TAG_OVERUSE` | WARNING | e2eタグが過剰に使われている | e2eは重要なユーザージャーニーのみに限定（5件以下、全体の20%以下を推奨） |
| `POST_APPROVAL_CHANGE` | WARNING | 承認後にファイルが変更された | APPROVAL.md の該当ゲートを再承認するか、変更を元に戻す |
| `COUNTS_MISMATCH` | WARNING | counts値が実際と不一致 | 提示されたYAMLをコピペして修正 |
| `COUNTS_SUGGESTION` | INFO | counts値の修正候補 | 警告として表示、コピペ可能な正しい値が提示される |
| `APPROVAL_PENDING` | ERROR | ゲート承認が未完了 | 人間がAPPROVAL.mdを編集して承認 |
| `APPROVAL_FILE_MISSING` | ERROR | APPROVAL.md が存在しない | `stride init` で自動生成するか、手動でテンプレートをコピー |

### v1.2.5 追加

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `ID_REGEX_MISMATCH` | ERROR | IDが constitution.md の正規表現に一致しない | ID規約を確認し、正しい形式に修正 |
| `DATABASE_SCHEMA_UNDEFINED` | ERROR | database_schema_id が spec.md に未定義 | spec_as_code.artifacts に database_schema を追加 |
| `GATE_EXPRESSION_UNRESOLVED` | ERROR | ゲート式が未解決 | constitution.md の gates.requires を確認 |

### 多言語承認フィールド（v1.2.5）

APPROVAL.md の承認フィールドは日本語・英語の両方に対応しています：

| 日本語 | 英語 | 説明 |
|--------|------|------|
| `承認者:` | `Approver:` | 承認者名 |
| `日付:` | `Date:` | 承認日 |

**stride-lint はどちらの形式も認識します。**

```markdown
# 日本語形式（推奨）
承認者: 山田太郎
日付:   2025-01-15

# 英語形式（国際チーム向け）
Approver: Taro Yamada
Date:     2025-01-15
```

### v4.5 追加（BDD Acceptance Criteria）

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `BDD_AC_MISSING` | WARNING | `bdd_mode: "required"` なのに `acceptance_criteria` がない | タスクに acceptance_criteria を追加 |
| `BDD_AC_INCOMPLETE` | ERROR | BDD構造が不完全（id/scenario/given/when/then/verification のいずれかが欠如） | 欠けているフィールドを追加 |
| `BDD_AC_INVALID_VERIFICATION` | ERROR | `verification` が automated/manual/hitl 以外 | 正しい値に修正 |
| `BDD_ESCALATION_MISSING` | WARNING | auth/payment/schema/security キーワードを含むタスクに `escalation_trigger: true` が未設定 | 該当 acceptance_criteria に `escalation_trigger: true` を追加 |
| `BDD_AUTOMATED_RATIO_LOW` | WARNING | `verification: "automated"` の比率が `automated_ratio_target` 未満 | automated 検証可能なACを増やすか、target を調整 |

### v4.5.1 追加（Tier Mismatch）

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `TIER_MISMATCH` | WARNING | `coverage_tier: standard` だが `security_sensitive: true` または `erp_integration: true` が basic_design.md に設定されている | `coverage_tier: critical` に昇格するか、該当フラグを見直す |

> **判定ロジック**: `basic_design.md` の `coverage_tier` が `standard` かつ、`security_sensitive` または `erp_integration` が `true` の場合に WARNING を出力します。セキュリティやERP連携を含む Feature は `critical` tier で管理すべきです。

### BPMN関連

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `BPMN_VALIDATION_FAILED` | ERROR | BPMN 構造検証失敗（parse, namespace, executionPlatform, isExecutable, DI, serviceTask taskDefinition, XOR condition, FlowNode incoming/outgoing, BPMNShape/Edge 完全性, boundaryEvent attachedToRef、補償boundary以外の outgoing、participant 使用時の `isHorizontal="false"`） | BPMN を修正 |
| `BPMN_DOCUMENTATION_MISSING` | WARN | process / userTask / serviceTask / businessRuleTask / callActivity / 分岐 exclusiveGateway / 条件付き sequenceFlow に `<documentation>` がない | `bpmn:documentation` を追加 |
| `BPMN_PLACEHOLDER_PRESENT` | WARN | `{{...}}` や `BPMN-PROC-XXX` が未置換 | プレースホルダーを実値に置換 |
| `BPMN_ID_MISMATCH` | WARN | `bpmn_descriptions` / `traceability_rows` の bpmn_id が process.bpmn に存在しない | ID を一致させる |
| `BPMN_ID_NOT_DESCRIBED` | WARN | process.bpmn の業務ブロックが `bpmn_descriptions` に未記載 | YAML に説明を追加 |
| `BPMN_VERSION_MISMATCH` | WARN | executionPlatformVersion が 8.8 以外 | 8.8.0 推奨 |

### EPIC BPMN 関連（epic_validator.py）

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `EPIC_BPMN_MISSING` | WARN | epic_flow.bpmn が存在しない | `stride epic init` で生成 |
| `EPIC_BPMN_PARSE_ERROR` | ERROR | XML パース失敗 | XML を修正 |
| `EPIC_BPMN_INVALID` | ERROR/WARN | collaboration 構造不備、participant 不足、processRef 不在、DI 不備、participant `isHorizontal="false"` 違反、messageFlow edge 不備 | BPMN を修正 |
| `EPIC_BPMN_DOCUMENTATION_MISSING` | WARN | collaboration / participant / messageFlow に `<documentation>` がない | 追加 |
| `EPIC_BPMN_PLACEHOLDER` | WARN | EPIC-XXX が未置換 | 置換 |
| `EPIC_BPMN_ID_MISMATCH` | WARN | YAML の ID が BPMN に不在 | ID を一致させる |
| `EPIC_BPMN_ID_NOT_DESCRIBED` | WARN | BPMN の participant / messageFlow が YAML に未記載 | YAML に追加 |
| `EPIC_BPMN_OVERVIEW_MISSING` | WARN | `epic_flow_descriptions.overview.purpose` が空、または BPMN collaboration の documentation が空/placeholder | 追加 |

### ゲート関連

| コード | レベル | 説明 | 対処 |
|--------|--------|------|------|
| `GATE_FAILED` | ERROR | ゲート条件未達 | 各ゲート条件を確認 |
| `GATE_EXPRESSION_UNRESOLVED` | ERROR | ゲート式が評価不能 | constitution.md の gates 定義を確認 |

---

## 5. エラー詳細と対処例

### AC_NOT_COVERED

```
ERROR: AC_NOT_COVERED
  AC-US-FEAT001-001-03 is not covered by any test
```

**対処**:
```yaml
# plan.md
tests:
  - id: "TS-INT-02"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-03"  # ← 追加
```

### TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE

```
ERROR: TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE
  AC-US-FEAT001-001-01 has tag 'integration' but is covered by TS-UT-01 (type: unit)
```

**対処**:
```yaml
# plan.md
tests:
  - id: "TS-INT-01"            # ← TS-INT-* に変更
    type: "integration"        # ← type も integration に
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-01"
```

### TEST_NOT_TASKED

```
ERROR: TEST_NOT_TASKED
  TS-INT-01 is defined in plan but not tasked
```

**対処**:
```yaml
# tasks.md
tasks:
  - id: "T-G03-001"
    title: "Write integration tests (TS-INT-01)"
    plan_refs:
      - "TS-INT-01"  # ← 追加
```

### PLACEHOLDER_VALUE_PRESENT

```
WARNING: PLACEHOLDER_VALUE_PRESENT
  Found placeholder: "FEAT-XXX" in feature_id
```

**対処**:
```bash
# IDを置換
sed -i '' 's/FEAT-XXX/FEAT-001/g' specs/my_feature/*.md
```

### SPEC_AS_CODE_MISSING

```
ERROR: SPEC_AS_CODE_MISSING
  spec_gate_check.spec_as_code_defined is true but no artifacts defined
```

**対処**:
```yaml
# spec.md
spec_as_code:
  artifacts:
    - type: "openapi"
      path: "specs/my_feature/contracts/openapi.yaml"
```

### EVIDENCE_PACK_NOT_DEFINED

```
ERROR: EVIDENCE_PACK_NOT_DEFINED
  plan_gate_check.evidence_pack_defined is true but evidence_pack not configured
```

**対処**:
```yaml
# plan.md
test_strategy:
  evidence_pack:
    required_artifacts:
      - "ci_results"
      - "sast"
      - "sca"
      - "secrets_scan"
      - "ai_provenance"
    storage:
      path: "specs/my_feature/implementation-details/evidence_pack.md"
```

### E2E_TAG_OVERUSE（v1.2.4新規）

```
WARNING: E2E_TAG_OVERUSE
  e2e tagged ACs: 8 (26.7% of total 30 ACs)
  Recommended: max 5 or 20% of total ACs
```

**原因**: e2eタグが付与されたACが多すぎる（5件超または全体の20%超）

**対処**:
```yaml
# spec.md - e2eタグは重要なユーザージャーニーのみに限定
acceptance_criteria:
  - id: "AC-US-FEAT001-001-01"
    tags: ["e2e"]   # ← 本当に必要なものだけ
  - id: "AC-US-FEAT001-001-02"
    tags: ["integration"]   # ← integrationで十分なものはintegrationに
```

**ベストプラクティス**:
- E2Eテストは実行コストが高い
- 重要なユーザージャーニー（ログイン→購入→決済など）のみにe2eを付ける
- 単体機能のテストはintegrationやunitで十分

### POST_APPROVAL_CHANGE（v1.2.4新規）

```
WARNING: POST_APPROVAL_CHANGE
  File specs/my_feature/spec.md was modified after Gate 3 approval
  Gate 3 approved at: 2025-01-15T10:00:00Z
  File modified at: 2025-01-16T14:30:00Z
```

**原因**: ゲート承認後にファイルが変更された

**対処**:
1. **変更が意図的な場合**: APPROVAL.md の該当ゲートを再承認
2. **変更が誤りの場合**: `git checkout` で元に戻す

```bash
# ゲートを再承認する場合
# 1. APPROVAL.md の該当ゲートのチェックボックスをオフに
# 2. 人間が再度レビューして承認
# 3. チェックボックスをオンにして日付と署名を更新
```

### COUNTS_MISMATCH / COUNTS_SUGGESTION（v1.2.4新規）

```
ERROR: COUNTS_MISMATCH
  spec.counts.acceptance_criteria: declared=3, actual=5

SUGGESTION: Copy the following to fix counts:
---
counts:
  acceptance_criteria: 5
  use_cases: 2
---
```

**対処**: 提示されたYAMLをコピペして`spec.md`のcountsを更新

```yaml
# spec.md
derived_fields:
  counts:
    acceptance_criteria: 5   # ← 提示された値に更新
    use_cases: 2
```

---

## 7. オプション一覧

| オプション | 説明 | 備考 |
|-----------|------|------|
| `--all` | 全機能を検証 | |
| `--feature <path>` | 特定機能を検証 | |
| `--changed <range>` | 変更ファイルのみ検証 | |
| `-o`, `--format <fmt>` | 出力フォーマット: `text`(default) / `json` / `ndjson` | v5.0.0 `-o` ショートハンド追加 |
| `--plain` | TSV出力（1行1レコード、grep/awk/CI向け） | v5.0.0 |
| `--no-color` | カラー出力を無効化 | v5.0.0 |
| `--coverage-report` | 詳細カバレッジレポートを追加出力 | 概要はデフォルトで常時表示 |
| `--warn-only` | エラーでも終了コード0 | |
| `--enterprise` | Enterprise 拡張検証を追加 | `--all` 併用時のみ Epic も検証 |
| `--verbose` | 詳細出力 | `-o json/ndjson`・`--plain` と排他 |
| `--fail-on <codes>` | 指定したコードのみ失敗扱い | |
| `--lite-mode` | Lite Mode（3段階承認）で検証 | |

### 排他制御

- `--plain` と `-o json`/`-o ndjson` は同時使用不可（exit code 2）
- `--verbose` と機械可読出力（`-o json`/`-o ndjson`/`--plain`）は同時使用不可（exit code 2）

### 終了コード

| コード | 意味 | エージェントのアクション |
|--------|------|------------------------|
| 0 | lint 通過 | 次の Gate へ進む |
| 1 | lint エラーあり | `errors[].suggested_action` を読み、修正して再実行 |
| 2 | 使用方法エラー（引数不正） | `stride lint --help` を確認 |
| 3 | Feature ディレクトリ不在 | パスを確認（stderr に Did-you-mean サジェストあり） |
| 4 | YAML 構文エラー | 報告されたファイルの YAML 構文を修正 |

---

## 8. 出力フォーマット（v5.0.0）

### テキスト出力（デフォルト）

TTY 接続時は自動的にカラー出力されます。エラーには `→` 付きで修正ヒント（`suggested_action`）が表示されます。

```
Feature: specs/FEAT-ORDER
--------------------------
Coverage: [x] AC 5/5 (100.0%)  [x] CT 3/3 (100.0%)
Errors:
  ✗ APPROVAL_PENDING: Gate 1: Basic Design: Unchecked items remain (3/3)
    → APPROVAL.mdの該当Gateを承認してください（人間のみ）
  → Fix errors, then re-run: stride lint specs/FEAT-ORDER/
```

カラーを無効にするには:
- `--no-color` フラグ
- `NO_COLOR=1` 環境変数（[no-color.org](https://no-color.org/) 準拠）
- パイプ・リダイレクト時は自動無効（非TTY検出）

### Plain TSV 出力（`--plain`）

`grep` / `awk` / CI ログパース向け。1行1レコード、タブ区切り。

```bash
stride lint --all --plain
# FEAT-ORDER	ERROR	APPROVAL_PENDING	Gate 1: ...
# FEAT-ORDER	WARN	POST_APPROVAL_CHANGE	basic_design.md was ...
```

フィールド: `feature_name\tseverity\tcode\tmessage`

### JSON 出力（`-o json`）

全 Feature の結果を1つの JSON オブジェクトにまとめます。`meta` フィールドにアクター情報とタイムスタンプを含みます。

```bash
stride lint --all -o json
```

```json
{
  "results": [
    {"feature": "specs/FEAT-ORDER", "errors": [...], "warnings": [...]}
  ],
  "meta": {
    "invocation_mode": "non-interactive",
    "timestamp": "2026-04-02T12:00:00+00:00"
  }
}
```

### NDJSON 出力（`-o ndjson`）

1 Feature = 1行の JSON。パイプ先のツール（`jq`、`head -1`）が1行ずつ独立して処理可能。

```bash
stride lint --all -o ndjson | jq 'select(.errors | length > 0) | .feature'
```

### アクター追跡（`STRIDE_ACTOR` 環境変数）

JSON/NDJSON 出力の `meta` にアクター情報を含めます。CI/CD やエージェント実行の監査に利用します。

```bash
# 明示的アクター指定
STRIDE_ACTOR=agent:claude-code stride lint --all -o json
# → meta: {"actor": "agent:claude-code", "invocation_mode": "explicit"}

# 自動検出（参考情報、断定には使わない）
# CI環境: {"invocation_mode": "ci:github_actions"}
# TTY: {"invocation_mode": "interactive"}
# パイプ: {"invocation_mode": "non-interactive"}
```

### パス typo サジェスト

存在しないパスを指定した場合、`difflib` で類似候補を提案します（exit code 3）。

```
$ stride lint specs/FEAT-TETS/
ERROR: Feature directory not found: specs/FEAT-TETS/
  Did you mean: specs/FEAT-TEST/ ?
```

### YAML 事前検証（Fail-Fast）

Canonical YAML ブロック（`basic_design.md`、`spec.md`、`plan.md`、`tasks.md`）の構文を lint 前にチェックし、壊れた YAML を早期に exit code 4 で報告します。2,000行の lint を完走した後に「YAML 壊れてた」と判明する無駄を防ぎます。

---

## 9. CI/CD での使用

### GitHub Actions 例

**前提**: Python + PyYAML が利用できる環境。

```yaml
name: SDD Lint

on:
  pull_request:
    paths:
      - 'specs/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run stride-lint
        run: |
          sdd-templates/tools/stride-lint --all --coverage-report > coverage_report.yaml

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage_report.yaml
```

### エージェント / CI 向け JSON 出力

```yaml
      - name: Run stride-lint (JSON)
        run: |
          STRIDE_ACTOR=ci:github-actions \
          sdd-templates/tools/stride-lint --all -o json > lint_results.json

      - name: Upload lint results
        uses: actions/upload-artifact@v4
        with:
          name: lint-results
          path: lint_results.json
```

### 段階的導入（warn-onlyから始める）

```yaml
# Phase 1: 警告のみ
- name: Run stride-lint (warn-only)
  run: sdd-templates/tools/stride-lint --all --warn-only

# Phase 2: 特定のエラーのみ失敗
- name: Run stride-lint
  run: sdd-templates/tools/stride-lint --all --fail-on "AC_NOT_COVERED,TEST_NOT_TASKED"

# Phase 3: 全エラーで失敗
- name: Run stride-lint
  run: sdd-templates/tools/stride-lint --all
```

---

## 7.1 CI実行結果の見方（初心者向け）

### どこを見るか

1. **Workflowステータス**: ✅ 成功 / ❌ 失敗  
2. **Jobログ**: stride-lint の出力（エラー/警告/coverage_report）  
3. **Artifacts**: `coverage-report` をダウンロード

### 成功時の読み方

- **summary.overall_pass = true**  
  → AC/CT/タグ付きAC/タスク化がすべて合格  
- **uncovered / untasked が空**  
  → 抜け漏れなし  

### 失敗時の読み方

- **Errors にあるコードが原因**  
  例: `AC_NOT_COVERED`, `BPMN_VALIDATION_FAILED`  
- **Warnings は必ずしも失敗ではない**  
  ただし運用方針によっては `--fail-on` で失敗扱いにできます

### Artifacts の使い方

1. `coverage-report` をダウンロード  
2. `coverage_report.yaml` を開く  
3. `summary` と `uncovered` を先に確認する

---

## 7.2 読み解きサンプル（coverage_report）

### サンプル出力（抜粋）

```yaml
coverage_report:
  acceptance_coverage:
    total_ac: 3
    covered_ac: 3
    uncovered: []
  tagged_coverage:
    integration:
      total_tagged: 3
      uncovered: []
    e2e:
      total_tagged: 1
      uncovered: []
  contract_coverage:
    total_ct: 1
    uncovered: []
  test_tasking:
    total_ts: 3
    untasked: []
  summary:
    overall_pass: true
```

### この出力が意味すること

- **ACはすべてテストでカバー**（`uncovered` が空）
- **タグ付きACも指定テスト種別でカバー**（integration/e2eとも空）
- **契約（CT）もテストでカバー**（`uncovered` が空）
- **テストがタスク化されている**（`untasked` が空）
- **全体判定: 合格**（`overall_pass: true`）

### もし不合格なら（例）

```yaml
acceptance_coverage:
  uncovered: ["AC-US-FEAT001-001-03"]
summary:
  overall_pass: false
```

この場合は **「ACが1件テストでカバーされていない」** という意味なので、  
`plan.md` の `tests[].covers_acceptance_ids` に追加します。

---

## 8. 検証の流れ

```
stride-lint 実行
       │
       ▼
┌──────────────────────┐
│ 1. ファイル存在確認   │
│    MISSING_FILE      │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 2. YAML パース       │
│    YAML_PARSE_ERROR  │
│    CANONICAL_BLOCK_  │
│    NOT_FOUND         │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 3. ID検証            │
│    ID_REGEX_MISMATCH │
│    DUPLICATE_ID      │
│    PLACEHOLDER_VALUE │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 4. 参照検証          │
│    REF_NOT_FOUND     │
│    INVALID_PLAN_REF  │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 5. カバレッジ検証    │
│    AC_NOT_COVERED    │
│    TAGGED_AC_NOT_... │
│    CONTRACT_COVERAGE │
│    TEST_NOT_TASKED   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 6. BPMN検証          │
│    BPMN_VALIDATION   │
└──────────┬───────────┘
           ▼
┌──────────────────────┐
│ 7. ゲート評価        │
│    GATE_FAILED       │
└──────────┬───────────┘
           ▼
       結果出力
```

---

## 9. ベストプラクティス

1. **開発中は --warn-only** - 開発中は警告モードで実行
2. **PR前にフル検証** - PRを出す前にエラーを修正
3. **CIで強制** - mainブランチへのマージでは必須
4. **カバレッジレポートを保存** - 経時変化を追跡

---

## チェックリスト

- [ ] stride-lint を実行した
- [ ] エラーを全て修正した
- [ ] --coverage-report で網羅性を確認した
- [ ] CI/CD に組み込んだ

---

## 次のステップ

→ [11. トラブルシューティング](appendix_d_troubleshooting.md)

---

> SDD Templates Manual - Appendix B. stride-lint Guide
