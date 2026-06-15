# Knowledge Update: SDD Templates v1.2.1-tecnos

**Date**: 2025-12-30
**Tags**: sdd-templates, v1.2.1-tecnos, documentation, migration-guide, quickstart, cheatsheet

---

## 1. Documentation Updates Summary

### 追加ドキュメント

| ファイル | 目的 | 所要時間 |
|----------|------|----------|
| `MIGRATION.md` | v1.2.0→v1.2.1 移行ガイド | 15分 |
| `QUICKSTART.md` | 新規参画者向け最短ルート | 30分 |
| `CHEATSHEET.md` | ID規約・タグ・エラー一覧 | 参照用 |

### README.md 更新
- Getting Started セクション追加
- Contents を 4 カテゴリに整理

---

## 2. v1.2.1-tecnos Core Architecture

### Coverage Policy（3層カバレッジモデル）

```yaml
coverage_policy:
  acceptance_coverage_required: true      # Layer 1: AC Coverage = 100%
  acceptance_coverage_target_pct: 100
  contract_coverage_required: true        # Layer 2: CT Coverage = 100%
  contract_coverage_target_pct: 100
  tagged_acceptance_requirements:
    integration:
      enforce: true
      required_test_type: "integration"
    e2e:
      enforce: true
      required_test_type: "e2e"
  code_coverage_targets:                  # Layer 3: Code Coverage = 目標値
    - scope: "LIB-*"
      line_pct: 85
      branch_pct: 75
    - scope: "CMP-*"
      line_pct: 60
      branch_pct: 50
  code_coverage_exclusions:
    - path_glob: "**/generated/**"
      reason: "Generated code"
      mitigation: "Contract/Integration tests cover behavior"
```

### Tagged Acceptance Requirements

| AC Tag | 必須テストタイプ | テストID形式 |
|--------|------------------|--------------|
| `integration` | Integration Test | `TS-INT-*` |
| `e2e` | E2E Test | `TS-E2E-*` |
| (なし) | Unit Test | `TS-UT-*` |

### Double Loop Design（二重ループ設計）

- **Inner Loop（高速反復）**: AI + Playwright MCP
  - 探索、テスト骨格生成、失敗再現、triage
- **Outer Loop（品質ゲート）**: CI決定論的実行
  - Playwright Test、Gate判定

### E2E Triage 4分類

| 分類 | 説明 | 対処先 |
|------|------|--------|
| `product_bug` | 製品のバグ | Spec/Plan/Tasks → 修正タスク追加 |
| `spec_gap` | 仕様の抜け漏れ | Spec AC更新 → Plan/Tasks修正 |
| `test_bug` | テストコードのバグ | テスト修正 |
| `flake` | 非決定的な失敗 | 安定化 |

---

## 3. ID Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `FEAT-XXX` | FEAT-001 |
| Use Case | `US-FEAT<ID>-NNN` | US-FEAT001-001 |
| Acceptance Criteria | `AC-US-<US_ID>-NN` | AC-US-FEAT001-001-01 |
| Contract | `CT-<TYPE>-NN` | CT-API-01, CT-EVT-01 |
| Test (Unit) | `TS-UT-NN` | TS-UT-01 |
| Test (Integration) | `TS-INT-NN` | TS-INT-01 |
| Test (Contract) | `TS-CON-NN` | TS-CON-01 |
| Test (E2E) | `TS-E2E-NN` | TS-E2E-01 |
| Task | `T-GNN-NNN` | T-G01-001 |

---

## 4. speckit-lint Failure Codes (v1.2.1 新規)

| Code | 説明 | 対処 |
|------|------|------|
| `AC_NOT_COVERED` | ACがTSでカバーされていない | TSに`covers_acceptance_ids`追加 |
| `TAGGED_AC_NOT_COVERED_BY_REQUIRED_TEST_TYPE` | タグ不整合 | タグに応じたTS追加 |
| `CONTRACT_COVERAGE_INCOMPLETE` | CTがTS-CONでカバーされていない | `covers_contract_ids`追加 |
| `TEST_NOT_TASKED` | PlanのTSがTasksにタスク化されていない | Tasksにタスク追加 |
| `E2E_REPORTING_NOT_CONFIGURED` | E2E使用時にreporting未設定 | plan.mdにreporting追加 |
| `E2E_TRIAGE_NOT_DEFINED` | E2E使用時にtriage手順未定義 | e2e-triage.md作成 |

---

## 5. File Structure (Final)

```
templates_v1.2.1-tecnos/
├── README.md                    # Updated
├── MIGRATION.md                 # NEW - Migration guide
├── QUICKSTART.md                # NEW - Quick start
├── CHEATSHEET.md                # NEW - Cheat sheet
├── templates/
│   ├── basic_design_template.md
│   ├── spec_template.md
│   ├── plan_template.md
│   └── tasks_template.md
├── policies/
│   └── bpmn_generator_rules.md
├── examples/
│   └── process_bpmn_template.bpmn
├── memory/
│   ├── constitution.md
│   ├── tecnos_org_constraints.md
│   └── knowledge_updates_2025-12-30.md  # This file
└── tools/
    └── speckit_lint_spec.md
```

---

## 6. Related Documents

- `templates_v1.2.1-tecnos_evaluation.md` - 別AIによる評価
- `templates_v1.2.1-tecnos_evaluation_response.md` - 評価への回答と改善提案

---

## 7. Next Steps (v1.2.2 Candidates)

| 改善案 | 効果 | 工数 | 優先度 |
|--------|------|------|--------|
| Scaffold Generator | 高 | 高 | ⭐⭐⭐ |
| Minimal Template | 中 | 低 | ⭐⭐⭐ |
| speckit-lint 実装ガイド | 高 | 中 | ⭐⭐⭐ |
| Mutation Testing | 中 | 中 | ⭐ |
| Security Scanning | 中 | 中 | ⭐ |
| Coverage Trend Tracking | 低 | 中 | ⭐ |

---

> End of knowledge_updates_2025-12-30.md
