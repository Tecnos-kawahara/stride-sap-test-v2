# 指示プロンプト: STRIDE 統合テストフレームワーク Phase 2

作業ディレクトリ: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

## 現在地

Phase 1 は完了済み。
現状は `python -m pytest -m "not api" -q --tb=short` で `272 passed, 3 deselected`。
Phase 1 では以下が整備済み:

- `tests/project_builder.py`
- `tests/conftest.py`
- `tests/test_stride_lint_integration.py`
- `tests/test_phase_gate_integration.py`
- `tests/test_auto_continue_integration.py`
- `tests/test_pr_readiness_integration.py`
- `tests/test_stride_cli_integration.py`
- `symphony/tests/test_pr_readiness_checker.py`
- `symphony/tests/test_evaluator_live.py`

Phase 2 では、まだ薄い Enterprise / ERP Addon / Dependency / Amendment の統合テストを追加する。
今回は「テスト基盤の拡張と deterministic な統合テスト」を実装する。テンプレート本体の新機能追加は不要。既存実装の不具合が見つかった場合のみ最小修正する。

## 目的

以下を実現すること。

1. `epic_validator.py` / `epic_progress_aggregator.py` / `stride_lint_enterprise.py` の統合テスト追加
2. `dependency_checker.py` の統合テスト追加
3. `erp_addon_exec_tracking.py` の統合テスト追加
4. `amendment_generator.py` の deterministic な統合テスト追加
5. 既存の Phase 1 テスト資産を再利用し、repo root を汚さず `tmp_path` ベースで完結
6. `python -m pytest -m "not api" -q --tb=short` が引き続き全 PASS

## 実装前に必ず読むこと

推測で書かない。以下を必ず確認してから実装すること。

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

grep -n "^def \|^class " tests/project_builder.py
sed -n '1,260p' tests/project_builder.py
sed -n '1,220p' tests/conftest.py

sed -n '1,220p' tests/test_stride_lint_integration.py
sed -n '1,220p' tests/test_phase_gate_integration.py
sed -n '1,220p' tests/test_auto_continue_integration.py
sed -n '1,220p' tests/test_pr_readiness_integration.py
sed -n '1,220p' tests/test_stride_cli_integration.py

grep -n "^def \|^class " sdd-templates/tools/epic_validator.py
sed -n '1,260p' sdd-templates/tools/epic_validator.py
grep -n "^def \|^class " sdd-templates/tools/epic_progress_aggregator.py
sed -n '1,260p' sdd-templates/tools/epic_progress_aggregator.py
grep -n "^def \|^class " sdd-templates/tools/dependency_checker.py
sed -n '1,260p' sdd-templates/tools/dependency_checker.py
grep -n "^def \|^class " sdd-templates/tools/erp_addon_exec_tracking.py
sed -n '1,260p' sdd-templates/tools/erp_addon_exec_tracking.py
grep -n "^def \|^class " sdd-templates/tools/amendment_generator.py
sed -n '1,260p' sdd-templates/tools/amendment_generator.py
grep -n "enterprise.yaml\|enterprise_config\|load_enterprise_config" sdd-templates/tools/stride_lint.py | head -10
grep -n "def get_approved_gates\|return approved" sdd-templates/tools/phase_gate.py

sed -n '1,220p' tests/test_enterprise_smoke.sh
sed -n '1,220p' manual/24_multi_team_guide.md
sed -n '1,220p' agent_docs/commands.md
```

## 重要な方針

- Phase 1 の `ProjectBuilder` を拡張する。新しい別系統 builder は作らない。
- static fixture を大量追加しない。`tmp_path` に動的生成する。
- repo root を直接変更するテストは禁止。
- GitHub / `gh` / ネットワーク依存のテストは禁止。`amendment_generator.py` は mock または `--dry-run` で検証する。
- `does not crash` だけの弱いアサーションは避ける。可能な限り構造・終了コード・主要フィールドを assert する。
- 既存の live API テストには触らない。今回の対象は `not api` 側。

## Step 1: `ProjectBuilder` を Phase 2 用に拡張

`tests/project_builder.py` を拡張し、最低限以下を扱えるようにすること。

- `ProjectBuilder.add_epic(epic_id: str)` または同等の仕組み
- `epics/EPIC-SAMPLE` をコピー元にした isolated epic 生成
- enterprise mode の有効化と feature 側 `epic_ref` / `team_id` の整合設定
- feature dependency manifest の生成・改変
- ERP Addon 用の `work_items/`, `runs/`, `state/`, `ops/` の段階的生成
- amendment テスト用の run artifacts / findings / decisions を作る補助

既存の `enable_enterprise()`, `with_enterprise()`, `with_erp_addon()` を活かし、足りないものだけ増やすこと。
epic は文字列で一から組み立てず、feature 側と同じくサンプルをコピーして ID を書き換える方式を優先すること。

## Step 2: fixture を `tests/conftest.py` に追加

以下の fixture を追加すること。

- `enterprise_project`
- `enterprise_project_with_cycle`
- `erp_addon_project`
- `erp_addon_project_invalid_mode`
- `amendment_project`

命名は変えてもよいが、役割は分かるようにすること。

## Step 3: 新規テストファイルを追加

以下の4ファイルを新規追加すること。

### 3-1. `tests/test_epic_integration.py`

対象:

- `epic_validator.py`
- `epic_progress_aggregator.py`
- `stride lint --enterprise`
- 必要なら `stride epic validate`, `stride epic progress`

最低限入れるテスト:

- 正常な enterprise project で epic validate が PASS/正常終了
- `epic_ref` / `team_id` 不整合でエラーになる
- `epic_progress_aggregator.py --format json` が妥当な JSON を返す
- markdown / summary 出力に feature 数や team 情報が含まれる
- `stride lint specs/<feature> --enterprise` が enterprise 検証を通る

注意:

- `stride lint --enterprise` は `stride_lint.py` の `load_enterprise_config()` が参照する `sdd-templates/config/enterprise.yaml` を使う。実装前に参照パスを確認し、`ProjectBuilder.enable_enterprise()` の書き換え先と一致していることを前提にテストを組むこと。
- ⚠️ `load_enterprise_config()` は `Path(__file__).parent.parent / "config" / "enterprise.yaml"` を参照する。`ProjectBuilder` は `sdd-templates/tools` を symlink しているため、`__file__` の解決先は repo root 側になる可能性がある。その場合、tmp_path 配下の `enterprise.yaml` ではなく repo root の `enterprise.yaml` を読んでしまう。
- この問題を回避するには、少なくとも以下のいずれかを採ること:
  - `test_stride_lint_integration.py` 等の既存テストで同種のパス問題をどう扱っているか先に確認する
  - `stride lint --enterprise` の subprocess 検証に固執せず、`stride_lint_enterprise.py` / `EnterpriseValidator` を import して project root を明示的に渡す
  - 必要なら `ProjectBuilder` 側の配置方式を見直し、enterprise config の参照先が deterministic になるよう最小修正する

### 3-2. `tests/test_dependency_integration.py`

対象:

- `dependency_checker.py`

最低限入れるテスト:

- 非循環 dependency graph は成功
- 循環 dependency graph は cycle を検出
- `graph` コマンドが DOT を返す
- manifest validate が壊れた YAML / 不正 ID / 欠落で失敗する
- 可能なら feature 間依存と epic dependency manifest の両方を1件ずつカバー

### 3-3. `tests/test_erp_addon_integration.py`

対象:

- `erp_addon_exec_tracking.py`
- 必要なら `stride_lint.py` 経由の ERP Addon 検証

最低限入れるテスト:

- ERP Addon 非活性 feature では skip/空結果になる
- Gate 5 前は検証が走らない
- Gate 5 後の active feature で必要ファイル不足を検出する
- invalid mode / risk flag / policy mismatch を検出する
- full ops pack が揃っている正常系を通す

注意:

- `validate_erp_addon_execution_tracking()` の第2引数 `approval_status` は `dict[str | int, bool]`。
- `APPROVAL.md` を `ProjectBuilder` で生成しただけでは足りないので、必要に応じて `phase_gate.get_approved_gates()` を使って approved gate 集合を取り、テスト用 dict に変換するか、目的に応じて直接 dict を組み立てること。

### 3-4. `tests/test_amendment_integration.py`

対象:

- `amendment_generator.py`

方針:

- `gh` 実呼び出しは禁止
- `create/apply/finalize` は mock または `--dry-run` で検証
- deterministic にすること
- `cmd_draft` には `--dry-run` はない。stdout 出力のみで副作用がないため、`argparse.Namespace` を組み立てて直接呼ぶか subprocess で直接実行して検証すること
- `cmd_draft` は `_next_amd_id()` を通じて amendment Issue 一覧を参照する。必要なら `_run_gh` または `_search_issues_by_label` を monkeypatch し、AMD ID の採番を deterministic にすること

最低限入れるテスト:

- `analyze` が findings / decisions / affected spec を抽出できる
- `draft` が AMD ID / title / scope / approval section を含む
- `apply --dry-run` が spec patch 候補と PR 作成意図を出す
- `finalize --dry-run` が derived WI 作成意図を出す
- `cmd_analyze` は `gh` 系ヘルパーを内部で呼ぶため、`_run_gh` を `(1, "", "gh not found")` で monkeypatch して外部依存を無効化するか、`_search_issues_by_label` / `_detect_related_risk_dep` を直接 monkeypatch して deterministic にすること
- 必要なら `_run_gh` / `_run_cmd` を monkeypatch して lifecycle を局所的に検証する

## Step 4: 既存テスト資産を壊さないこと

以下は維持必須。

- `tests/` と `symphony/tests/` の既存テストは削除しない
- `pyproject.toml` の `testpaths` / `markers` は壊さない
- `symphony/tests/test_evaluator_live.py` は変更不要
- timestamp 付き state 出力を fixture 正本にしない

## Step 5: 検証

実装後は以下を順番に実行すること。

```bash
python3 sdd-templates/tools/epic_validator.py --test
python3 sdd-templates/tools/epic_progress_aggregator.py --test
python3 sdd-templates/tools/dependency_checker.py --test
python3 sdd-templates/tools/erp_addon_exec_tracking.py --test
python3 sdd-templates/tools/amendment_generator.py --test

python3 -m pytest \
  tests/test_epic_integration.py \
  tests/test_dependency_integration.py \
  tests/test_erp_addon_integration.py \
  tests/test_amendment_integration.py \
  -v --tb=short

python3 -m pytest -m "not api" -q --tb=short
```

## 完了基準

以下がすべて満たされていること。

1. `ProjectBuilder` が enterprise / dependency / ERP Addon / amendment 用 fixture を動的生成できる
2. `tests/test_epic_integration.py` が追加され PASS
3. `tests/test_dependency_integration.py` が追加され PASS
4. `tests/test_erp_addon_integration.py` が追加され PASS
5. `tests/test_amendment_integration.py` が追加され PASS
6. 関連 tool の self-test が壊れていない
7. `python3 -m pytest -m "not api" -q --tb=short` が全 PASS
8. 追加テスト件数と最終総件数を報告できる
9. GitHub 実ネットワークや repo root 汚染に依存しない

## 完了後の報告形式

以下の形式で報告すること。

```text
=== Phase 2 完了報告 ===

追加したテスト:
  - tests/test_epic_integration.py: <N> tests
  - tests/test_dependency_integration.py: <N> tests
  - tests/test_erp_addon_integration.py: <N> tests
  - tests/test_amendment_integration.py: <N> tests

拡張した基盤:
  - tests/project_builder.py: <要点>
  - tests/conftest.py: <要点>

検証結果:
  - epic_validator.py --test: PASS
  - epic_progress_aggregator.py --test: PASS
  - dependency_checker.py --test: PASS
  - erp_addon_exec_tracking.py --test: PASS
  - amendment_generator.py --test: PASS
  - 新規 Phase 2 テスト: <N> passed
  - 全体 (`-m "not api"`): <TOTAL> passed

補足:
  - mock / dry-run にした外部依存箇所
  - 見つけて修正したテンプレート不具合があればその内容
```

## 禁止事項

- 新しい大規模 static fixture ツリーの追加
- `gh` 実呼び出し前提のテスト
- repo root 直下のファイル書き換え前提テスト
- 失敗理由を曖昧にする緩い assert への逃げ
- Phase 2 の名目で unrelated な機能追加
