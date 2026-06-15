# 指示プロンプト: STRIDE 統合テストフレームワーク Phase 3

作業ディレクトリ: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

## 現在地

Phase 1 / Phase 2 は完了済み。

現状:
- `python3 -m pytest -m "not api" -q --tb=short` → `299 passed, 3 deselected`
- `python3 -m pytest --collect-only -q` → `302 tests collected`
- `pyproject.toml` には `api` / `slow` / `e2e` marker がある
- ただし現時点で `e2e` / `slow` marker を使う pytest は実質未整備
- `tests/test_enterprise_smoke.sh` は存在するが shell smoke のままで、pytest の E2E 資産として統合されていない

Phase 1/2 でカバー済み:
- `stride_lint.py`
- `phase_gate.py`
- `auto_continue_runner.py`
- `pr_readiness_checker.py`
- `multi_model_evaluator.py`
- `epic_validator.py`
- `epic_progress_aggregator.py`
- `stride_lint_enterprise.py`
- `dependency_checker.py`
- `erp_addon_exec_tracking.py`
- `amendment_generator.py`

Phase 3 の目的は以下:
1. `stride` CLI 全体の bootstrap / enterprise / workflow を isolated root で通す E2E を追加する
2. 未カバーの project analysis / governance / run lifecycle ツールを pytest 統合テスト化する
3. shell smoke 依存を減らし、`@pytest.mark.e2e` を実際に使う
4. repo root を汚さず、ネットワーク非依存で deterministic にする

今回はテンプレート本体の新機能追加は不要。既存実装の不具合が見つかった場合のみ最小修正する。

## 対象スコープ

### Phase 3A: CLI / Bootstrap / E2E
対象:
- `sdd-templates/bin/stride`
- `tests/test_enterprise_smoke.sh` 相当の pytest 化
- `intake`, `init`, `init --detect`, `init --epic --team`
- `epic init|validate|gates|features|progress|list`
- `ddd-init`
- `decisions init|refresh`
- `hooks --tool manual` と可能なら `hooks --tool claude --force`
- `new-project --dry-run`

### Phase 3B: Project Analysis / Governance
対象:
- `brownfield_detector.py`
- `spec_drift_detector.py`
- `decision_index.py`
- `approval_router.py`
- `setup_hooks.py`

### Phase 3C: Run Lifecycle / WI Flow
対象:
- `wi_readiness_checker.py`
- `run_resume_detector.py`
- `run_report_generator.py`
- `sdd_planning_bridge.py`
- `stride_wi_sync.py`

## 今回の Phase 3 では対象外
以下は backlog 扱い。今回は触らなくてよい。
- `evidence_metrics_collector.py`
- `stride_process_metrics.py`
- `stride_testreport_bridge.py`
- `setup_project_labels.py`

## 実装前に必ず読むこと

推測で書かない。以下を必ず確認してから実装すること。

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

sed -n '1,320p' tests/project_builder.py
sed -n '1,260p' tests/conftest.py

sed -n '1,260p' tests/test_stride_cli_integration.py
sed -n '1,260p' tests/test_pr_readiness_integration.py
sed -n '1,260p' tests/test_epic_integration.py
sed -n '1,280p' tests/test_amendment_integration.py
sed -n '1,280p' tests/test_dependency_integration.py
sed -n '1,260p' tests/test_erp_addon_integration.py
sed -n '1,260p' tests/test_enterprise_smoke.sh

sed -n '1,260p' sdd-templates/bin/stride

grep -n "^def \|^class " sdd-templates/tools/brownfield_detector.py
sed -n '1,260p' sdd-templates/tools/brownfield_detector.py

grep -n "^def \|^class " sdd-templates/tools/spec_drift_detector.py
sed -n '1,260p' sdd-templates/tools/spec_drift_detector.py

grep -n "^def \|^class " sdd-templates/tools/decision_index.py
sed -n '1,260p' sdd-templates/tools/decision_index.py

grep -n "^def \|^class " sdd-templates/tools/approval_router.py
sed -n '1,260p' sdd-templates/tools/approval_router.py

grep -n "^def \|^class " sdd-templates/tools/setup_hooks.py
sed -n '1,260p' sdd-templates/tools/setup_hooks.py

grep -n "^def \|^class " sdd-templates/tools/wi_readiness_checker.py
sed -n '1,260p' sdd-templates/tools/wi_readiness_checker.py

grep -n "^def \|^class " sdd-templates/tools/run_resume_detector.py
sed -n '1,260p' sdd-templates/tools/run_resume_detector.py

grep -n "^def \|^class " sdd-templates/tools/run_report_generator.py
sed -n '1,260p' sdd-templates/tools/run_report_generator.py

grep -n "^def \|^class " sdd-templates/tools/sdd_planning_bridge.py
sed -n '1,260p' sdd-templates/tools/sdd_planning_bridge.py

grep -n "^def \|^class " sdd-templates/tools/stride_wi_sync.py
sed -n '1,260p' sdd-templates/tools/stride_wi_sync.py
```

## 重要な方針

- 既存の `tests/project_builder.py` を拡張する。新しい別系統 builder は作らない。
- static fixture を大量追加しない。`tmp_path` に動的生成する。
- repo root を直接変更するテストは禁止。
- GitHub / `gh` / ネットワーク依存のテストは禁止。必要箇所は monkeypatch / dry-run で deterministic にする。
- shell smoke をそのまま増やさない。pytest に寄せる。
- `does not crash` だけの弱いアサーションは避ける。終了コード、主要フィールド、主要出力文言を assert する。
- `@pytest.mark.e2e` を実際に使うこと。
- 必要に応じて `@pytest.mark.slow` も使ってよいが、乱用しない。
- `symphony/tests/test_evaluator_live.py` には触らない。
- 既存の `api` スイートは今回の対象外。

## Step 1: `ProjectBuilder` を Phase 3 用に拡張

`tests/project_builder.py` を拡張し、最低限以下を扱えるようにすること。

- brownfield project root の生成
  - `package.json`
  - `pyproject.toml`
  - `go.mod`
  - `src/` / `app/` / `cmd/` など
  - monorepo indicator (`turbo.json`, `pnpm-workspace.yaml` 等)
- spec drift 用 project root の生成
  - `contracts/*.yaml`
  - `src/` 配下の route 実装
  - schema mismatch / endpoint missing / contract outdated を作れる
- ADR / decision index 用ディレクトリ生成
  - `shared/decisions/ADR-*.md`
  - `decision-index.md` の初期状態有無を切り替えられる
- hook 用 `.claude/settings.json` の初期状態生成
  - 未作成
  - 空
  - 壊れた JSON
  - 既存 hook あり
- WI / Run lifecycle 用構造生成
  - `work_items/`
  - `runs/<wi>/<run>/`
  - `.planning/findings.md`
  - `.planning/plan.md`
  - `walkthrough.md`
  - `decision_log.md`
  - `test_results.md`
  - `state/state.yaml`
  - `ops/`
- `stride_wi_sync` 用の feature mapping / work item directory 下地
- `stride init --detect` で読む brownfield indicator を builder で自然に作れるようにする

既存の `FeatureBuilder.with_erp_addon()` / `with_amendment_artifacts()` / `with_dependency_manifest()` を活かし、足りない補助だけ増やすこと。

## Step 2: fixture を `tests/conftest.py` に追加

最低限以下を追加すること。

- `brownfield_project`
- `spec_drift_project`
- `adr_project`
- `hooks_project`
- `wi_ready_project`
- `interrupted_run_project`
- `run_report_project`
- `planning_bridge_project`
- `wi_sync_project`
- `bootstrap_project_root`

命名は多少変えてよいが、役割が明確なこと。

## Step 3: 新規テストファイルを追加

### 3-1. `tests/test_bootstrap_cli_e2e.py`
対象:
- `stride intake`
- `stride init`
- `stride init --detect`
- `stride ddd-init`
- `stride decisions init`
- `stride decisions refresh`
- `stride hooks --tool manual`
- 可能なら `stride hooks --tool claude --force`
- `stride new-project --dry-run`

最低限入れるテスト:
- `intake` が `basic_design_intake.md` を作る
- `init` が feature 一式を作る
- `init --detect` が brownfield detection 結果を出力または生成物に反映する
- `ddd-init` が DDD/ADR ファイルを作る
- `decisions init/refresh` が `shared/decisions/decision-index.md` を生成/更新する
- `hooks --tool manual` が説明文を出す
- `hooks --tool claude --force` が tmp project の `.claude/settings.json` を正しく更新する
- `new-project --dry-run` が destructive な変更なしに計画を出力する

注意:
- `stride new-project --dry-run` は `scripts/stride-new-project.sh` を経由する bash 実装で、pytest からの深い制御コストが高い。ここは subprocess で `--dry-run` を実行し、`exit 0` と主要な計画出力文言を確認する程度に留め、内部実装の深追いはしないこと。

このファイルは `@pytest.mark.e2e` を付けること。

### 3-2. `tests/test_enterprise_cli_e2e.py`
対象:
- `tests/test_enterprise_smoke.sh` の pytest 化
- `stride epic init|validate|gates|features|progress|list`
- `stride init --epic --team`
- `stride lint --enterprise`

最低限入れるテスト:
- enterprise off では `epic list` がブロックされる
- enterprise on では `epic list` が通る
- `epic init` が必要ファイルを生成する
- `epic validate` が動作する
- `init --epic` が team 指定なし multi-team epic で失敗する
- `init --epic --team <valid>` が `epic_ref` / `team_id` を設定する
- `epic gates`, `epic features`, `epic progress` が対象 epic を受け取って動く

このファイルも `@pytest.mark.e2e` を付けること。

### 3-3. `tests/test_brownfield_integration.py`
対象:
- `brownfield_detector.py`

最低限入れるテスト:
- greenfield project は `type=greenfield`
- source dir + manifest ありで `type=brownfield`
- monorepo indicator で `structure=monorepo`
- Node/Python/Go の tech stack detection が動く
- `--json` 出力が妥当な JSON

### 3-4. `tests/test_spec_drift_integration.py`
対象:
- `spec_drift_detector.py`

最低限入れるテスト:
- contract と実装が一致する正常系
- contract にある endpoint が未実装
- 実装にある endpoint が contract にない
- parameter mismatch / schema mismatch のいずれか1件
- `--json` 出力の drift type / severity を assert

### 3-5. `tests/test_decision_index_integration.py`
対象:
- `decision_index.py`

最低限入れるテスト:
- `init` で index が作成される
- ADR を複数置いて `refresh` すると index が再構築される
- status/date/title が index に反映される
- 壊れた ADR front matter があっても落ちずに扱えるならその挙動を固定する

### 3-6. `tests/test_approval_router_integration.py`
対象:
- `approval_router.py`

最低限入れるテスト:
- coverage tier と gate type から approver route が返る
- approver authority の validate が PASS/FAIL する
- parallel eligibility の判定が返る
- enterprise fixture の team/tier を使って route が変わることを1件確認する

### 3-7. `tests/test_hooks_integration.py`
対象:
- `setup_hooks.py`
- 可能なら `stride hooks --tool claude`

最低限入れるテスト:
- `.claude/settings.json` が無い状態で作成できる
- 空ファイルから復旧できる
- 壊れた JSON で適切に失敗または警告する
- 既存 hook があると重複追加しない
- 出力 JSON に `phase_gate_hook.py` が含まれる

注意:
- `setup_hooks.py` の `main()` は既存 hook がある場合に `input()` を呼ぶ。テストでは `monkeypatch.setattr("builtins.input", lambda _: "y")` で stdin を差し替えるか、まず既存 hook がない状態の作成パスを優先して検証すること。

### 3-8. `tests/test_wi_readiness_integration.py`
対象:
- `wi_readiness_checker.py`

最低限入れるテスト:
- Gate 5 未承認で NOT READY
- WI file 不足で NOT READY
- mode policy mismatch を検出
- full ops pack と state が揃って READY
- `--verbose` で詳細出力が増えるならその主要文言を確認する

### 3-9. `tests/test_run_resume_integration.py`
対象:
- `run_resume_detector.py`

最低限入れるテスト:
- artifact なし → 最初の resume point
- `decision_log.md` あり → testing へ
- `test_results.md` あり → walkthrough へ
- `walkthrough.md` あり → complete 判定
- 中断 run の recommendation 文言を固定する

### 3-10. `tests/test_run_report_integration.py`
対象:
- `run_report_generator.py`

最低限入れるテスト:
- findings / decisions / changelog / spec-impact を parse できる
- report markdown に WI / run / findings count が出る
- `--post` 相当は monkeypatch で `gh` を無効化し、投稿意図またはコメント生成を検証する
- labels 更新があるなら dry-run / mock 経由で検証する

注意:
- `--post` / project field 更新系の mock 対象は `run_report_generator._run_gh`。`subprocess.run` ではなく、モジュールレベルの `_run_gh` を差し替えて deterministic にすること。

### 3-11. `tests/test_sdd_planning_bridge_integration.py`
対象:
- `sdd_planning_bridge.py`

最低限入れるテスト:
- `init` が `.planning/` と初期 plan context を作る
- `sync` が stride-lint 結果を plan に反映する
- `evidence` が walkthrough 向け evidence section を生成する
- `learn` が findings / lint / decisions から lesson candidate を抽出する

外部依存:
- 必要なら `stride_lint` 呼び出しは monkeypatch
- deterministic にすること

注意:
- `sdd_planning_bridge.py` のグローバル変数 `KNOWLEDGE_DIR = Path.home() / ".claude" / "knowledge"` はホームディレクトリの実ファイルを参照する。テストを deterministic にするには `KNOWLEDGE_DIR` を monkeypatch して `tmp_path` 配下に向けるか、`search_knowledge` を monkeypatch して空リストを返すこと。

### 3-12. `tests/test_wi_sync_integration.py`
対象:
- `stride_wi_sync.py`

最低限入れるテスト:
- `gh api` レスポンスを monkeypatch して WI issue を markdown 化できる
- YAML block ベース issue body を parse できる
- Issue Form ベース body を parse できる
- `--dry-run` でファイルを書かない
- feature filter が正しく効く

注意:
- `stride_wi_sync.py` の `run_gh()` は失敗時に `sys.exit(1)` を呼ぶ。`main()` を通すテストは `subprocess.run` の monkeypatch だけでは不十分。`run_gh` / `get_repo` / `fetch_issues` 自体を monkeypatch するか、`main()` を避けて `parse_yaml_block` / `parse_issue_form` / `issue_to_work_item` / `work_item_to_md` を直接テストする方が安全。

## Step 4: 既存テスト資産を壊さないこと

以下は維持必須。

- `tests/` と `symphony/tests/` の既存テストは削除しない
- `pyproject.toml` の `testpaths` / `markers` は壊さない
- `tests/test_enterprise_smoke.sh` は削除しない
  - ただし pytest 版が揃った後に「実質 superseded」と判断しても、今回は残してよい
- `symphony/tests/test_evaluator_live.py` は変更不要
- timestamp 付き state 出力を fixture 正本にしない

## Step 5: marker 運用

今回から marker を実際に使うこと。

- `@pytest.mark.e2e`
  - `tests/test_bootstrap_cli_e2e.py`
  - `tests/test_enterprise_cli_e2e.py`
- `@pytest.mark.slow`
  - 必要なものだけ。基本は不要。
  - もし付けるなら理由が明確なテストのみに限定

## Step 6: 検証

実装後は以下を順番に実行すること。

```bash
python3 sdd-templates/tools/brownfield_detector.py --test
python3 sdd-templates/tools/spec_drift_detector.py --test
python3 sdd-templates/tools/decision_index.py --test
python3 sdd-templates/tools/approval_router.py --test
python3 sdd-templates/tools/setup_hooks.py >/dev/null 2>&1 || true
python3 sdd-templates/tools/wi_readiness_checker.py --test
python3 sdd-templates/tools/run_resume_detector.py --test
python3 sdd-templates/tools/run_report_generator.py --test
python3 sdd-templates/tools/sdd_planning_bridge.py --test
python3 sdd-templates/tools/stride_wi_sync.py --help >/dev/null

python3 -m pytest \
  tests/test_bootstrap_cli_e2e.py \
  tests/test_enterprise_cli_e2e.py \
  tests/test_brownfield_integration.py \
  tests/test_spec_drift_integration.py \
  tests/test_decision_index_integration.py \
  tests/test_approval_router_integration.py \
  tests/test_hooks_integration.py \
  tests/test_wi_readiness_integration.py \
  tests/test_run_resume_integration.py \
  tests/test_run_report_integration.py \
  tests/test_sdd_planning_bridge_integration.py \
  tests/test_wi_sync_integration.py \
  -v --tb=short

python3 -m pytest -m "not api and not e2e" -q --tb=short
python3 -m pytest -m "e2e" -q --tb=short
python3 -m pytest -m "not api" -q --tb=short
```

## 完了基準

以下がすべて満たされていること。

1. `ProjectBuilder` が brownfield / spec drift / ADR / hooks / WI / run lifecycle fixture を動的生成できる
2. `tests/test_bootstrap_cli_e2e.py` が追加され PASS
3. `tests/test_enterprise_cli_e2e.py` が追加され PASS
4. `tests/test_brownfield_integration.py` が追加され PASS
5. `tests/test_spec_drift_integration.py` が追加され PASS
6. `tests/test_decision_index_integration.py` が追加され PASS
7. `tests/test_approval_router_integration.py` が追加され PASS
8. `tests/test_hooks_integration.py` が追加され PASS
9. `tests/test_wi_readiness_integration.py` が追加され PASS
10. `tests/test_run_resume_integration.py` が追加され PASS
11. `tests/test_run_report_integration.py` が追加され PASS
12. `tests/test_sdd_planning_bridge_integration.py` が追加され PASS
13. `tests/test_wi_sync_integration.py` が追加され PASS
14. `@pytest.mark.e2e` が実際に使われ、`-m e2e` 実行が意味を持つ
15. `python3 -m pytest -m "not api and not e2e" -q --tb=short` が全 PASS
16. `python3 -m pytest -m "e2e" -q --tb=short` が全 PASS
17. `python3 -m pytest -m "not api" -q --tb=short` が全 PASS
18. 追加テスト件数、`e2e` 件数、最終総件数を報告できる
19. repo root 汚染や GitHub 実ネットワークに依存しない

## 完了後の報告形式

以下の形式で報告すること。

```text
=== Phase 3 完了報告 ===

追加したテスト:
  - tests/test_bootstrap_cli_e2e.py: <N> tests
  - tests/test_enterprise_cli_e2e.py: <N> tests
  - tests/test_brownfield_integration.py: <N> tests
  - tests/test_spec_drift_integration.py: <N> tests
  - tests/test_decision_index_integration.py: <N> tests
  - tests/test_approval_router_integration.py: <N> tests
  - tests/test_hooks_integration.py: <N> tests
  - tests/test_wi_readiness_integration.py: <N> tests
  - tests/test_run_resume_integration.py: <N> tests
  - tests/test_run_report_integration.py: <N> tests
  - tests/test_sdd_planning_bridge_integration.py: <N> tests
  - tests/test_wi_sync_integration.py: <N> tests

拡張した基盤:
  - tests/project_builder.py: <要点>
  - tests/conftest.py: <要点>

検証結果:
  - brownfield_detector.py --test: <PASS/結果>
  - spec_drift_detector.py --test: <PASS/結果>
  - approval_router.py --test: <PASS/結果>
  - run_report_generator.py --test: <PASS/結果>
  - targeted Phase 3 tests: <N> passed
  - fast suite (`not api and not e2e`): <N> passed
  - e2e suite (`e2e`): <N> passed
  - all non-api (`not api`): <TOTAL> passed, <DESELECTED> deselected

補足:
  - mock / dry-run にした外部依存箇所
  - pytest 化で実質 superseded になった shell smoke があればその内容
  - 見つけて修正したテンプレート不具合があればその内容
```

## 禁止事項

- 新しい大規模 static fixture ツリーの追加
- repo root 前提の destructive E2E
- `gh` 実呼び出し前提テスト
- `new-project` の実 git 初期化や commit を伴うテスト
- 壊れた経路でも通る弱い assert
- Phase 3 の名目で unrelated な機能追加
*** End Patch
# Copy omitted by tool call argument format
