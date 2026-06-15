# Task: v4.6 Execution Authority Separation / wi_readiness Check 8 / Symphony Janitor の end-to-end 実動検証

## 前提コンテキスト

- プロジェクト: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`（Tecnos-STRIDE v5.1.0）
- v4.6 で追加された制御:
  - `shared/policies/mode_policy.yaml` の `execution_authority` 宣言（conversational / gated / prohibited 3層）
  - `wi_readiness_checker.py` Check 8（WI mode と execution_authority 宣言の整合性検証）
  - Article XIV（Constitution）
- v5.1 で追加された Symphony Janitor は autopilot + starter tier + リスクフラグ除外のスコープで動作
- 問題: 各制御はユニットテストでは検証済み（wi_readiness 17/17 PASS）だが、**実際の WI 作成 → Run → PR までの E2E での挙動が未検証**。Opus 4.7 の literal-follow 下で v4.6 制御が「宣言した通り」動くか保証がない。

## 目的

以下の 3 つが宣言通りに動くことを **end-to-end で実証**:

1. **正常系 (PASS)**: conversational 行為は承認なしに実行、gated 行為はスキーマ検証を通過した場合のみ実行、prohibited 行為はブロック
2. **異常系 (FAIL)**: gated 行為がスキーマ検証を通さずに試みられた場合、`WI_EXECUTION_AUTHORITY_VIOLATION` または同等のエラーで停止
3. **Janitor 経路**: Symphony Janitor が生成した Issue も Check 8 を通過し、リスクフラグ違反を持つ WI を作成しない

成果物として、再現可能な E2E テストを `sdd-templates/tests/test_execution_authority_e2e.py` に追加する。

## 作業開始前に読むファイル（順序厳守）

1. `agent_docs/sdd_bootstrap.md` §1-2, §5, §6（AI Action Boundary、WI フロー）
2. `memory/constitution.md` Article XIV（Execution Authority Separation）
3. `memory/tecnos_org_constraints.md` §6.4 RACI+ と §6.6 Spec-as-Code
4. `SDD_MANIFESTO.md` の「Execution Authority Separation」セクション
5. `shared/policies/mode_policy.yaml`（execution_authority 宣言の実体）
6. `sdd-templates/tools/wi_readiness_checker.py` 全体（Check 8 実装）
7. `sdd-templates/tools/wi_readiness_checker.py` `_run_self_tests()` の Test 15, 16, 17（execution_authority 関連）
8. `symphony/config.py`（JanitorConfig dataclass）
9. `symphony/cli.py`（_run_janitor_scan、create_janitor_issue 呼出し経路）
10. `symphony/tracker.py`（has_recent_pr, create_janitor_issue）
11. `specs/FEAT-ERPSAMPLE/`（サンプル feature、WI 定義含む）
12. 関連論文: Cook et al. (2026) "Talk Freely, Execute Strictly" arXiv:2603.06394（概念理解のため、全読不要）

## 作業手順

### Phase A: 現状把握（read-only）

1. `mode_policy.yaml` の `execution_authority` セクションを parse。conversational/gated/prohibited アクションリストを列挙
2. `wi_readiness_checker.py` の Check 8 ロジックを読む。どの入力が FAIL を誘発するか特定
3. 既存の Test 15/16/17 を再実行し、どのケースがカバーされているか確認:
   ```bash
   python3 sdd-templates/tools/wi_readiness_checker.py --test 2>&1 | grep -A1 "execution_authority"
   ```
4. カバレッジギャップを列挙:
   - 実 feature ディレクトリを作って end-to-end で走らせる試験が**現状ない**はず
   - Janitor 経由で生成した WI が Check 8 を通るか試験が**現状ない**はず
   - これらが追加すべきギャップ

### Phase B: 検証環境準備

1. テスト用 feature の雛形を作る（実プロジェクトの specs/ を汚さないため、pytest tmpdir 内で動作）:
   ```python
   # sdd-templates/tests/test_execution_authority_e2e.py
   @pytest.fixture
   def sample_feature(tmp_path):
       feat = tmp_path / "specs" / "FEAT-TEST-EA"
       feat.mkdir(parents=True)
       # basic_design.md, spec.md, plan.md, tasks.md, APPROVAL.md (all approved), state.yaml を生成
       # mode_policy.yaml のコピーを shared/policies/ に配置
       return feat
   ```

2. mode_policy.yaml のモックを用意（execution_authority 宣言のバリアント）:
   - (a) conservative: conversational のみ、gated/prohibited はフル宣言
   - (b) liberal: prohibited 最小（APPROVAL.md 編集のみ）
   - (c) legacy: execution_authority 無宣言（v4.6 以前互換）

### Phase C: 正常系テスト（E2E PASS）

1. **Test EA-1**: autopilot WI + conversational 行為（lint 修正のみ）→ Check 8 PASS
2. **Test EA-2**: confirm WI + gated 行為（new_api contract）+ plan_review 承認済 → Check 8 PASS
3. **Test EA-3**: validate WI + design_diff + plan_review 両承認済 → Check 8 PASS
4. **Test EA-4**: legacy mode_policy.yaml（execution_authority 無宣言）→ Check 8 PASS（後方互換）

### Phase D: 異常系テスト（E2E FAIL）

1. **Test EA-F1**: autopilot WI + validate-level リスクフラグ（pii 等）あり → Check 8 FAIL（mode_override.reason 無しの場合）
2. **Test EA-F2**: autopilot WI + validate-level リスクフラグ + mode_override.reason 記載あり → Check 8 WARN（FAIL ではない）
3. **Test EA-F3**: critical tier + autopilot → AUTOPILOT_FORBIDDEN_BY_TIER（既存 error code）
4. **Test EA-F4**: prohibited 行為を WI.actions に宣言 → WI_EXECUTION_AUTHORITY_VIOLATION（新 error code、存在しなければ追加提案）
5. **Test EA-F5**: gated 行為なのに対応する schema validator 宣言が無い → Check 8 FAIL with gap 列挙

### Phase E: Janitor 統合テスト

1. **Test JN-1**: Janitor enabled + autopilot feature + no risk flags + no recent PR → Issue 生成 PASS
2. **Test JN-2**: Janitor enabled + feature に `risk:authz` → Issue 生成 skipped（exclude 効く）
3. **Test JN-3**: Janitor enabled + feature に直近 PR あり（< 7 days） → Issue 生成 skipped
4. **Test JN-4**: Janitor が生成した Issue を WI として materialize した時、Check 8 を**通過する**ことを確認
5. **Test JN-5**: Janitor が誤って tier:standard feature を拾わないこと（scope 制限）

### Phase F: ドキュメント・レポート

1. 検出した実装ギャップを `manual/36_harness_guide.md` または `agent_docs/harness.md` に追記（該当すれば）
2. Article XIV の criteria 項目（wi_readiness Check 8 が gaps を検出する）が実動作で実証できたか記録
3. 次の tune-up 候補を `ROADMAP` 相当（README か memory/）に登録

## 制約（INVIOLABLE）

- テストは `tmp_path` / fixture で完結。**実プロジェクト specs/ を絶対に汚さない**
- 実 GitHub API を叩かない（Janitor テストは `has_recent_pr` / `create_janitor_issue` を mock）
- `mode_policy.yaml` の実ファイルを書き換えない（テスト用コピーを使用）
- `APPROVAL.md` / `WI-*.approval.md` / `EPIC_APPROVAL.md` は絶対に編集しない
- 既存 17/17 self-tests を壊さない
- Test 追加は ±400 行以内。超える場合は Phase 分割を提案して停止
- `wi_readiness_checker.py` に新エラーコード追加が必要な場合、**既存 error codes 辞書への破壊的変更禁止**。新規コードは append のみ

## 完了条件

- [ ] `sdd-templates/tests/test_execution_authority_e2e.py` に 14 テスト (EA-1〜EA-F5 + JN-1〜JN-5) 追加、全 PASS
- [ ] `wi_readiness_checker.py --test` が **17/17 以上 PASS**（既存維持、新規追加は別ファイルで）
- [ ] `symphony/tests/test_janitor.py` の既存 10 tests 全 PASS 継続
- [ ] カバレッジギャップレポートを報告に記載（どの v4.6/v5.1 条文が今回実証済みか、未実証の残余）
- [ ] 検出した実装バグがあれば Issue 候補として報告（PR は別セッションで — このタスクは検証まで）

## 検証コマンド

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

# 新規テスト
python3 -m pytest sdd-templates/tests/test_execution_authority_e2e.py -v --tb=short

# 既存テスト回帰
python3 sdd-templates/tools/wi_readiness_checker.py --test
cd symphony && python3 -m pytest tests/test_janitor.py -v && cd ..

# mode_policy.yaml 整合性
python3 -c "
import yaml
with open('shared/policies/mode_policy.yaml') as f:
    d = yaml.safe_load(f)
ea = d.get('execution_authority', {})
print('conversational:', len(ea.get('conversational', [])))
print('gated:', len(ea.get('gated', [])))
print('prohibited:', len(ea.get('prohibited', [])))
"

# Article XIV 参照
grep -A 20 '"XIV"' memory/constitution.md | head -30
```

## 報告テンプレート

```
## Task Completion Report: v4.6 Execution Authority E2E 検証

### Current coverage
- mode_policy.yaml declarations: conversational=<N>, gated=<M>, prohibited=<K>
- Check 8 existing tests: 3 (Test 15/16/17)
- Gaps identified: <bullet list>

### Tests added
- Normal path (EA-1..4): 4/4 PASS
- Failure path (EA-F1..5): 5/5 PASS
- Janitor integration (JN-1..5): 5/5 PASS
Total: 14/14 PASS

### Regressions
wi_readiness_checker: 17/17 PASS (existing) + 14 new = effective coverage
symphony/tests/test_janitor: 10/10 PASS (existing)

### Implementation bugs found
<あれば列挙、無ければ "None — v4.6 controls validated as declared">

### Article XIV criteria status
- "mode_policy.yaml に execution_authority セクション定義": ✅ 確認
- "全 gated 行為が対応スキーマ検証ツールを持つ": <✅ / ⚠ ギャップ>
- "Check 8 が宣言時に検証スコープ整合性を検出": ✅ 検証済 (Test EA-F5)
- "prohibited 行為が既存仕組みで担保": ✅ 検証済 (Test EA-F4)

### Follow-ups
<Optional: 別セッションで取組むべき残件>
```
