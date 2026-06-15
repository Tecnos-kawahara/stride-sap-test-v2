# 19. カバレッジポリシーガイド

---

## このガイドで学ぶこと

1. Coverage Policy とは
2. PM向けの読み方
3. 3層モデルの詳細
4. タグ付きACの強制
5. 設定方法
6. 検証方法

---

## 0. 5分クイックリファレンス（PM向け）

**Coverage Policyとは**: 「テストの抜け漏れを防ぐルール」です。

**見るべき数字（この3つだけ）**:
1. **AC Coverage = 100%**（受入条件がすべてテストで確認されているか）
2. **CT Coverage = 100%**（外部連携の契約がテストされているか）
3. **Code Coverage = 目標値 + 例外管理**（内部品質は目標＋理由付き例外）

**判断の目安**:
- AC/CTが100%未達 → **止める**
- Code Coverage未達 → **例外の理由と代替策があれば進める**

**見る場所**:
- `plan.md` の `test_strategy.coverage_policy`
- `sdd-templates/tools/stride-lint --coverage-report` の `summary` と `uncovered`

---

## 1. Coverage Policy とは

### まず一言で言うと

Coverage Policyは「**仕様・契約・コードが、どこまでテストされているかを決めるルール**」です。  
“テストをどこまでやったか”を感覚ではなく、**数字と基準**で示します。

### どうして必要なのか（PM視点）

- **品質の説明責任**: 「どこまで検証したか」を数字で説明できる
- **外部連携のリスク低減**: 契約違反による障害を防ぎやすい
- **判断の統一**: 人によって「十分」の判断がぶれない

**Coverage Policyがないと起きること**:
- 仕様の抜け漏れがあっても気づけない
- 外部連携の事故が発生しやすい
- 「どこまでテストしたか」が人によって違う

### 専門用語を言い換えると（PM向け）

| 用語 | ひと言で言うと |
|------|----------------|
| AC Coverage | 受入条件が全部テストされたか |
| CT Coverage | 外部連携の約束が全部テストされたか |
| Code Coverage | 内部品質の目安（目標＋例外） |
| Tag（integration/e2e） | 重要度の目印 |

### 定義

**Coverage Policy** は、テストの網羅性を3つの層で管理する方針です。

```
┌─────────────────────────────────────────────────┐
│          Coverage Policy 3層モデル               │
├─────────────────────────────────────────────────┤
│                                                  │
│  Layer-1: AC Coverage    ← 仕様カバレッジ        │
│  「全ての受入条件がテストでカバーされているか」   │
│  ────────────────────────────────────           │
│  必須: 100%                                      │
│                                                  │
│  Layer-2: CT Coverage    ← 契約カバレッジ        │
│  「全ての契約が契約テストでカバーされているか」   │
│  ────────────────────────────────────           │
│  原則: 100%                                      │
│                                                  │
│  Layer-3: Code Coverage  ← コードカバレッジ      │
│  「コードの行/分岐がテストでカバーされているか」  │
│  ────────────────────────────────────           │
│  目標値 + 例外管理                               │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 初心者向けの最小設定（まずはこれ）

```yaml
coverage_policy:
  acceptance_coverage_required: true
  acceptance_coverage_target_pct: 100
  tagged_acceptance_requirements:
    integration: { enforce: true, required_test_type: "integration" }
    e2e: { enforce: true, required_test_type: "e2e" }
  contract_coverage_required: true
  contract_coverage_target_pct: 100
  tests_must_be_tasked: true
```

**ポイント**: まずは「AC/CTが全部テストされる」状態を作り、  
Code Coverageは目標値と例外を後から整備しても構いません。

### なぜ3層か

| 層 | 観点 | 重要度 |
|-----|------|-------|
| Layer-1 | ビジネス要件（AC）の充足 | 最重要 |
| Layer-2 | 外部連携（CT）の品質 | 重要 |
| Layer-3 | 内部実装の品質 | 補助 |

**PM向けの判断の目安**:
- Layer-1が未達なら進めない（合格基準が満たされていない）
- Layer-2が未達なら外部連携のリスクが高い
- Layer-3は「目標＋例外」で管理（例外理由が重要）

---

## 1.1 条件付き合格のケース例（PM向け）

**ケース1: Code Coverageが目標未達だが例外が明記**

- 事象: LIBの行カバレッジが80%（目標85%）だが例外理由と代替策が記録済み
- 判断: 条件付き合格（例外の妥当性が確認できるため）

**ケース2: AC/CTは100%だがe2eタグの一部が未実行**

- 事象: e2eタグ付きACが1件未実行、原因と期限が明記
- 判断: 条件付き合格（期限と責任者が明記されている場合）

**ケース3: coverage_reportが未作成**

- 事象: overall_pass が確認できない
- 判断: 不合格（根拠が不足）

---

## 1.2 不合格の典型例（PM向け）

**ケース1: AC Coverageが100%未達**

- 事象: 未カバーのACが残っている
- 理由: 合否基準そのものが満たされていない
- 判断: 不合格

**ケース2: CT Coverageが100%未達**

- 事象: 外部連携の契約がテスト未実施
- 理由: 外部連携の事故リスクが高い
- 判断: 不合格

**ケース3: 例外の理由と代替策がない**

- 事象: Code Coverage未達だが、例外の根拠が未記録
- 理由: PM判断の根拠が不足
- 判断: 不合格

---

## 1.3 合格の典型例（PM向け）

**ケース1: AC/CTが100%で、overall_passがtrue**

- 事象: AC/CTともに未カバーなし、coverage_reportでoverall_passがtrue
- 理由: 合否基準と外部連携の検証が揃っている
- 判断: 合格

**ケース2: Code Coverageは目標達成、例外なし**

- 事象: 目標値を満たし、除外ルールに依存していない
- 理由: 内部品質が基準を満たしている
- 判断: 合格

---

## 2. Layer-1: AC Coverage（仕様カバレッジ）

### 定義

```
全ての受入条件（AC）が、少なくとも1つのテスト（TS）でカバーされている
```

### 目標

```yaml
acceptance_coverage_required: true
acceptance_coverage_target_pct: 100  # 100%必須
```

**PMの見るべき値**: `acceptance_coverage_target_pct` が 100 か、未カバーACがないか。

### 検証方法

```
spec.mdの全AC集合: {AC-US-FEAT001-001-01, AC-US-FEAT001-001-02, ...}
plan.mdのcovers_acceptance_ids和集合: {AC-US-FEAT001-001-01, AC-US-FEAT001-001-02, ...}

差分 = 0 → ✅ Pass
差分 > 0 → ❌ Fail (AC_NOT_COVERED)
```

### 例

```yaml
# spec.md
use_cases:
  - id: "US-FEAT001-001"
    acceptance:
      - id: "AC-US-FEAT001-001-01"  # ← このACは...
      - id: "AC-US-FEAT001-001-02"  # ← このACも...

# plan.md
tests:
  - id: "TS-INT-01"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-01"  # ← カバー ✅
      - "AC-US-FEAT001-001-02"  # ← カバー ✅
```

---

## 3. Layer-1b: タグ付きACの強制

### 定義

ACにタグが付いている場合、対応するテスト種別でカバーされなければならない。

| ACタグ | 必要なテスト種別 | テストID形式 |
|--------|-----------------|-------------|
| `integration` | 統合テスト | TS-INT-* |
| `e2e` | E2Eテスト | TS-E2E-* |

### 設定

```yaml
tagged_acceptance_requirements:
  integration:
    enforce: true               # 強制する
    required_test_type: "integration"
  e2e:
    enforce: true               # 強制する
    required_test_type: "e2e"
```

**PMの見るべき値**: `integration/e2e` が強制されているか、タグ付きACが未カバーになっていないか。

### 検証方法

```
integrationタグ付きAC: {AC-US-FEAT001-001-01}
TS-INT-*のcovers_acceptance_ids: {AC-US-FEAT001-001-01}

差分 = 0 → ✅ Pass
差分 > 0 → ❌ Fail (TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE)
```

### 例

```yaml
# spec.md
acceptance:
  - id: "AC-US-FEAT001-001-01"
    tags: ["integration"]  # ← integrationタグ付き

# plan.md
tests:
  - id: "TS-INT-01"            # ← TS-INT-* (統合テスト)
    type: "integration"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-01" # ← カバー ✅

  # ❌ NG例：TS-UT-* ではダメ
  - id: "TS-UT-01"             # ← ユニットテスト
    type: "unit"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-01" # ← integrationタグなのにTS-UTでカバー ❌
```

---

## 4. Layer-2: CT Coverage（契約カバレッジ）

### 定義

```
全ての契約（CT）が、契約テスト（TS-CON）でカバーされている
```

### 目標

```yaml
contract_coverage_required: true
contract_coverage_target_pct: 100  # 100%原則
```

**PMの見るべき値**: `contract_coverage_target_pct` が 100 か、未カバーの契約がないか。

### 検証方法

```
plan.mdの全CT集合: {CT-API-01, CT-API-02, CT-EVT-01}
TS-CON-*のcovers_contract_ids和集合: {CT-API-01, CT-API-02, CT-EVT-01}

差分 = 0 → ✅ Pass
差分 > 0 → ❌ Fail (CONTRACT_COVERAGE_INCOMPLETE)
```

### 例

```yaml
# plan.md
contracts:
  apis_events:
    - id: "CT-API-01"  # ← この契約は...
    - id: "CT-API-02"  # ← この契約も...

tests:
  - id: "TS-CON-01"
    type: "contract"
    covers_contract_ids:
      - "CT-API-01"    # ← カバー ✅
      - "CT-API-02"    # ← カバー ✅
```

---

## 5. Layer-3: Code Coverage（コードカバレッジ）

### 定義

```
コードの行/分岐がテストでカバーされている割合
```

### 目標値

```yaml
code_coverage_targets:
  - scope: "LIB-*"         # ライブラリ（ビジネスロジック）
    line_pct: 85           # 行カバレッジ 85%
    branch_pct: 75         # 分岐カバレッジ 75%
  - scope: "CMP-*"         # コンポーネント（オーケストレーション）
    line_pct: 60           # 行カバレッジ 60%
    branch_pct: 50         # 分岐カバレッジ 50%
```

**PMの見るべき値**: 目標値が設定されているか、例外は理由と代替策があるか。

### 例外管理

```yaml
code_coverage_exclusions:
  - path_glob: "**/generated/**"
    reason: "Generated code"
    mitigation: "Contract/Integration tests cover behavior"

  - path_glob: "**/migrations/**"
    reason: "Database migrations"
    mitigation: "Integration tests verify migration results"
```

**ポイント**: 例外は必ず `reason` と `mitigation` をセットで記録

---

## 6. 設定方法

### plan.md での設定

```yaml
test_strategy:
  coverage_policy:
    # Layer-1: AC Coverage
    acceptance_coverage_required: true
    acceptance_coverage_target_pct: 100

    # Layer-1b: タグ付きAC強制
    tagged_acceptance_requirements:
      integration:
        enforce: true
        required_test_type: "integration"
      e2e:
        enforce: true
        required_test_type: "e2e"

    # Layer-2: CT Coverage
    contract_coverage_required: true
    contract_coverage_target_pct: 100

    # Layer-3: Code Coverage
    code_coverage_targets:
      - scope: "LIB-*"
        line_pct: 85
        branch_pct: 75
      - scope: "CMP-*"
        line_pct: 60
        branch_pct: 50

    code_coverage_exclusions:
      - path_glob: "**/generated/**"
        reason: "Generated code"
        mitigation: "Contract tests cover behavior"

    # 計画の規律
    tests_must_be_tasked: true
```

**PMの見るべき値**: `coverage_policy` が設定され、AC/CT/Code の基準が明記されているか。

---

## 7. 検証方法

### stride-lint での検証

```bash
# カバレッジレポート出力
sdd-templates/tools/stride-lint specs/my_feature/ --coverage-report
```

### 出力例

```yaml
coverage_report:
  timestamp: "2025-01-15T10:00:00Z"
  feature: "FEAT-001"

  acceptance_coverage:
    total_ac: 5
    covered_ac: 5
    coverage_pct: 100.0
    uncovered: []

  tagged_coverage:
    integration:
      total_tagged: 3
      covered_by_int: 3
      coverage_pct: 100.0
      uncovered: []
    e2e:
      total_tagged: 2
      covered_by_e2e: 2
      coverage_pct: 100.0
      uncovered: []

  contract_coverage:
    total_ct: 4
    covered_ct: 4
    coverage_pct: 100.0
    uncovered: []

  test_tasking:
    total_ts: 6
    tasked_ts: 6
    coverage_pct: 100.0
    untasked: []

  summary:
    ac_coverage_pass: true
    tagged_coverage_pass: true
    contract_coverage_pass: true
    test_tasking_pass: true
    overall_pass: true
```

**PMの見るべき値**: `overall_pass` が true か、`uncovered` が空か。

**初心者向けの読み方**:
1. `summary.overall_pass` が **true** か
2. `acceptance_coverage.uncovered` が **空** か
3. `contract_coverage.uncovered` が **空** か

---

## 8. よくある問題と対処

### 問題1: AC_NOT_COVERED

```
エラー: AC-US-FEAT001-001-03 is not covered by any test
```

**対処**:
```yaml
# plan.md に追加
tests:
  - id: "TS-INT-02"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-03"  # ← カバーを追加
```

### 問題2: TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE

```
エラー: AC-US-FEAT001-001-01 has tag 'integration' but is not covered by integration test
```

**対処**:
```yaml
# plan.md
tests:
  - id: "TS-INT-01"            # ← TS-INT-* を使用
    type: "integration"
    covers_acceptance_ids:
      - "AC-US-FEAT001-001-01"
```

### 問題3: CONTRACT_COVERAGE_INCOMPLETE

```
エラー: CT-API-02 is not covered by any contract test
```

**対処**:
```yaml
# plan.md
tests:
  - id: "TS-CON-02"
    type: "contract"
    covers_contract_ids:
      - "CT-API-02"  # ← カバーを追加
```

### 問題4: TEST_NOT_TASKED

```
エラー: TS-INT-01 is not tasked
```

**対処**:
```yaml
# tasks.md
tasks:
  - id: "T-G03-001"
    plan_refs:
      - "TS-INT-01"  # ← plan_refs に追加
```

---

## 9. ベストプラクティス

1. **ACから始める** - 仕様（AC）を先に固め、テストを後から追加
2. **タグを活用** - 重要なACには `integration` や `e2e` タグを付ける
3. **例外は明示** - カバレッジ例外は必ず理由と代替策を記録
4. **段階的導入** - 既存プロジェクトは `--warn-only` から始める

---

## チェックリスト

### PM向け（最小チェック）

- [ ] AC/CTカバレッジが100%である
- [ ] Code Coverageの例外に理由と代替策がある
- [ ] coverage_report の overall_pass が true

### SE/PG向け

- [ ] acceptance_coverage_required を true に設定
- [ ] tagged_acceptance_requirements を設定
- [ ] contract_coverage_required を true に設定
- [ ] code_coverage_targets を設定
- [ ] 例外がある場合は code_coverage_exclusions に記録
- [ ] tests_must_be_tasked を true に設定
- [ ] sdd-templates/tools/stride-lint --coverage-report で検証

---

## 次のステップ

→ [10. stride-lint使用ガイド](appendix_b_stride_lint.md)

---

> SDD Templates Manual - 09. Coverage Policy Guide
