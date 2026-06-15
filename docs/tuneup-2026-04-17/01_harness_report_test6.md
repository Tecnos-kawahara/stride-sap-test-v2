# Task: stride_harness_report.py Test 6 「all controls present → FULL」失敗の修正

## 前提コンテキスト

- プロジェクト: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`（Tecnos-STRIDE v5.1.0）
- 対象ツール: `sdd-templates/tools/stride_harness_report.py`（v5.1 新規、8 controls inventory）
- 関連 CLI: `stride harness-report <project_root> [--json]`

## 目的

`--test` セルフテストで **5/6 pass (Test 6 FAIL)** の状態。Test 6 は「全 8 controls 揃ったとき report.overall が FULL」と期待している。これが失敗している原因を特定し、テスト側とコード側のどちらが正しいかを判定して修正する。結果: **6/6 pass**。

## 作業開始前に読むファイル（順序厳守）

1. `agent_docs/sdd_bootstrap.md` §1-2（実行モデル・絶対ルール・AI Action Boundary）
2. `agent_docs/sdd_bootstrap.md` §5（Task Completion Checklist — 報告テンプレート厳守）
3. `agent_docs/harness.md`（8 controls 一覧・v5.1 設計思想）
4. `sdd-templates/CHANGELOG.md` の v5.1.0 エントリ
5. `sdd-templates/tools/stride_harness_report.py` 全体
6. 同ファイル末尾の `_run_self_tests()` Test 6 関数

## 再現手順

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise
python3 sdd-templates/tools/stride_harness_report.py --test
# → "5/6 tests passed" と "Test 6 FAILED: all controls present -> FULL" を観察
```

## 作業手順（sequential）

1. Test 6 のアサート条件と、`build_harness_report()` の overall 判定ロジックを並べて読む
2. 不一致の原因を特定（列挙すべき仮説）:
   - (a) Test 6 のフィクスチャが実際には 8 controls 全てを配置していない
   - (b) `build_harness_report()` の overall 判定が `coverage_pct == 100.0` と `gaps == []` の厳密 AND で、floating-point 誤差を許容していない
   - (c) 8 controls の検出キー（ファイル存在判定）が Test 6 のフィクスチャと不整合
   - (d) overall = "FULL" 文字列 vs "full" の case 齟齬
3. 根本原因を特定したら**最小修正**で fix（既存の Test 1-5 / 実機運用を壊さない範囲）
4. セルフテストを再実行し **6/6 PASS** を確認
5. `agent_docs/harness.md` の「Harness Report」行に、今回判明した判定ロジック（overall = FULL の厳密条件）を1行で追記

## 制約

- **公開インターフェース（`build_harness_report()` の戻り値 shape, CLI exit code, `--json` スキーマ）を変更しない**
- Test 1-5 に影響する変更は禁止（既存 PASS を壊さない）
- テストを削除・skip マーク・xfail 化で「通った」ことにしてはならない
- `stride-lint` / `stride pr-check` 実行対象のファイルではない（tools/ 配下）ので Phase Gate の対象外。ただしコミットメッセージと PR 本文は SDD の報告形式に従う
- APPROVAL.md / WI-*.approval.md は絶対に編集しない

## 完了条件（machine-checkable）

- [ ] `python3 sdd-templates/tools/stride_harness_report.py --test` → **6/6 tests passed**
- [ ] `stride harness-report .` を実機でも実行し、`--json` 出力が valid JSON
- [ ] 他ツールのセルフテストが **全て PASS** を維持:
  - pr_readiness_checker.py (10/10)
  - wi_readiness_checker.py (17/17)
  - evidence_metrics_collector.py (6/6)
  - stride_health.py (6/6)
  - amendment_generator.py (61/61)
- [ ] 修正は diff で ±15 行以内（Completeness 湖判定の範囲内）

## 検証コマンド

```bash
python3 sdd-templates/tools/stride_harness_report.py --test
python3 sdd-templates/tools/pr_readiness_checker.py --test
python3 sdd-templates/tools/wi_readiness_checker.py --test
python3 sdd-templates/tools/evidence_metrics_collector.py --test
python3 sdd-templates/tools/stride_health.py --test
python3 sdd-templates/tools/amendment_generator.py --test
sdd-templates/bin/stride harness-report . --json | python3 -m json.tool > /dev/null
git diff --stat  # ±15 行以内確認
```

## 報告テンプレート（bootstrap §5 準拠）

```
## Task Completion Report: stride_harness_report Test 6 fix

### Root cause
<原因を 1-2 文で>

### Fix
<何を何行変更したか>

### Self-tests
stride_harness_report: 6/6 PASS
pr_readiness_checker: 10/10 PASS
wi_readiness_checker: 17/17 PASS
evidence_metrics_collector: 6/6 PASS
stride_health: 6/6 PASS
amendment_generator: 61/61 PASS

### Doc update
agent_docs/harness.md: <追記 1 行>

### Diff size
±<N> lines (湖判定 ✅)
```
