# Knowledge Update: SDD Templates v1.2.2-tecnos

**Date**: 2025-12-30
**Tags**: sdd-templates, v1.2.2-tecnos, documentation, migration-guide, quickstart, cheatsheet

---

## 1. Documentation Updates Summary

### 追加ドキュメント

| ファイル | 目的 | 所要時間 |
|----------|------|----------|
| `MIGRATION.md` | v1.2.1→v1.2.2 移行ガイド | 15分 |
| `QUICKSTART.md` | 新規参画者向け最短ルート | 30分 |
| `CHEATSHEET.md` | ID規約・タグ・エラー一覧 | 参照用 |

### README.md 更新
- Getting Started セクション追加
- Contents を 4 カテゴリに整理

---

## 2. v1.2.2-tecnos Core Architecture

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

## 3. v1.2.2 Consistency Fixes

- **Schema alignment**: `use_cases` / `acceptance` を正としてドキュメント例を統一
- **ID alignment**: `TS-*` を 2桁に統一（Constitution と一致）
- **Path alignment**: feature ディレクトリを `snake_case` に統一
- **Coverage policy alignment**: Plan テンプレート準拠のキー名に統一
- **Gate tables**: Cheatsheet の Gate 表を Constitution と一致

---

## 4. ID Conventions

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

## 5. speckit-lint Failure Codes

v1.2.2 で新しい Failure Code は追加されていません（v1.2.1 と同じ）。

---

## 6. File Structure (Final)

```
templates_v1.2.2-tecnos/
├── README.md                    # Updated
├── MIGRATION.md                 # Updated
├── QUICKSTART.md                # Updated
├── CHEATSHEET.md                # Updated
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

## 7. Related Documents

- `templates_v1.2.2-tecnos_evaluation.md` - 別AIによる評価
- `templates_v1.2.2-tecnos_evaluation_response.md` - 評価への回答と改善提案

---

## 8. Next Steps (v1.2.3 Candidates)

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
