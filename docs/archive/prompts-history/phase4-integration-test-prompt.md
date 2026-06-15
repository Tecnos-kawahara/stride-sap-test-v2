# 指示プロンプト: STRIDE 統合テストフレームワーク Phase 4

作業ディレクトリ: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

## 現在地

Phase 1 / 2 / 3 は完了済み。

現状:
- `python3 -m pytest -m "not api" -q --tb=short` → `387 passed, 3 deselected`
- `python3 -m pytest -m "e2e" -q --tb=short` → `25 passed`
- `python3 -m pytest -m "api" -q --tb=short` → `3 passed`
- 合計 390 テスト

Phase 4 は Phase 3 で backlog 扱いとした残り 4 ツールの統合テストを追加する。
今回もテンプレート本体の新機能追加は不要。既存実装の不具合が見つかった場合のみ最小修正する。

## 対象ツール

| ツール | 行数 | self-test | 外部依存 |
|--------|------|-----------|---------|
| `evidence_metrics_collector.py` | 530 | 6/6 PASS | なし（ファイル読み取りのみ） |
| `stride_process_metrics.py` | 1003 | 51/51 PASS | なし（ファイル読み取り + dashboard 書き込み） |
| `stride_testreport_bridge.py` | 499 | 14/14 PASS | `testreport` CLI（`shutil.which` で存在チェック、なければ skip） |
| `setup_project_labels.py` | 284 | 41/41 PASS | `gh label create`（`_run_gh` 経由） |

## 実装前に必ず読むこと

推測で書かない。以下を必ず確認してから実装すること。

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

# 既存基盤
grep -n "^def \|^class " tests/project_builder.py
sed -n '1,60p' tests/conftest.py

# 対象ツールの全体構造
grep -n "^def \|^class " sdd-templates/tools/evidence_metrics_collector.py
sed -n '1,260p' sdd-templates/tools/evidence_metrics_collector.py
sed -n '260,530p' sdd-templates/tools/evidence_metrics_collector.py

grep -n "^def \|^class " sdd-templates/tools/stride_process_metrics.py
sed -n '1,260p' sdd-templates/tools/stride_process_metrics.py
sed -n '260,520p' sdd-templates/tools/stride_process_metrics.py
sed -n '520,780p' sdd-templates/tools/stride_process_metrics.py
sed -n '780,1003p' sdd-templates/tools/stride_process_metrics.py

grep -n "^def \|^class " sdd-templates/tools/stride_testreport_bridge.py
sed -n '1,260p' sdd-templates/tools/stride_testreport_bridge.py
sed -n '260,499p' sdd-templates/tools/stride_testreport_bridge.py

grep -n "^def \|^class " sdd-templates/tools/setup_project_labels.py
sed -n '1,284p' sdd-templates/tools/setup_project_labels.py
```

## 重要な方針

- 既存の `tests/project_builder.py` を拡張する。新しい別系統 builder は作らない。
- static fixture を大量追加しない。`tmp_path` に動的生成する。
- repo root を直接変更するテストは禁止。
- GitHub / `gh` / ネットワーク依存のテストは禁止。`setup_project_labels.py` は `_run_gh` を monkeypatch し、`stride_testreport_bridge.py` は `testreport` CLI を monkeypatch または不在前提で検証する。
- `does not crash` だけの弱いアサーションは避ける。構造・終了コード・主要フィールドを assert する。
- 既存のテスト資産（387 + 3 件）を壊さない。

## Step 1: `ProjectBuilder` の拡張

以下を扱えるようにすること。足りない部分だけ追加する。

### evidence_metrics_collector 用
- `coverage/coverage-summary.json` の生成（Istanbul JSON 形式）
- `test-results.xml` の生成（JUnit XML 形式）
- monorepo 構造で `packages/*/coverage/` を複数作れる
- `.turbo/` ディレクトリ（または `node_modules/.cache/turbo/`）に JSON ファイルを生成して cache hit rate を計算させる
- ⚠️ `collect_gate_lead_time()` は `APPROVAL.md` 内の `日付: YYYY-MM-DD` 行を必須とする。既存の `FeatureBuilder._write_approval()` は `承認者:` しか書かず日付を出力しない。テスト用に日付付き APPROVAL.md を生成する補助メソッドを `ProjectBuilder` または `FeatureBuilder` に追加すること（例: `with_approval_dates(gate_dates: dict[str|int, str])`）

### stride_process_metrics 用
- `APPROVAL.md` に日付付き承認を書ける仕組み（`parse_approval_dates` / `compute_gate_process_times` 用）。上記の evidence 用と共通の補助メソッドを使ってよい
- `tasks.md` の Canonical YAML 内に `tasks_gate_check.counts.tasks` と `tasks.tasks` 配列を持つ fixture（inject rate 計算の入力は `work_items/` や `runs/` ではなく `tasks.md` + `state/state.yaml` の `work_items` リスト）
- `state/state.yaml` に `work_items` リスト（`wi_id` / `status` 等）と `epic_ref` を持つ fixture
- `epics/<epic_ref>/PM_DASHBOARD.md` の生成（`update_dashboard` は feature 配下ではなく epic 配下の PM_DASHBOARD.md を更新する。`find_dashboard_path` が `state.yaml` の `epic_ref` → `epics/<epic_ref>/PM_DASHBOARD.md` を辿る）

### stride_testreport_bridge 用
- `testreport/cases.json`（優先）または `evidence/cases.json`（フォールバック）の生成
- `testreport/stride_mapping.yaml`（`cases.json` と同じディレクトリに置く。`ac-mapping.yaml` ではない）
- `testreport/report.html` の有無を切り替え

### setup_project_labels 用
- fixture 不要（ツールは repo を引数で受け取り、`gh` を呼ぶだけ）

## Step 2: fixture を `tests/conftest.py` に追加

最低限以下を追加すること。

- `evidence_project` — coverage + test results + gate approvals が揃った project
- `process_metrics_project` — 複数フェーズの承認日付 + WI + run artifacts がある project
- `testreport_project` — cases.json + stride_mapping.yaml + testreport dir がある feature

命名は多少変えてよいが、役割が明確なこと。

## Step 3: 新規テストファイルを追加

### 3-1. `tests/test_evidence_metrics_integration.py`

対象: `evidence_metrics_collector.py`

最低限入れるテスト:

- `collect_coverage` が coverage-summary.json から line/branch/function pct を読める
- `collect_test_results` が JUnit XML から total/passed/failed を読める
- `collect_cache_stats` が `.turbo/` 配下の JSON ファイルから cache_hit_rate を計算できる
- `collect_cache_stats` が `.turbo/` がない場合に `found: False` で graceful に返る
- `collect_gate_lead_time` が APPROVAL.md の `日付: YYYY-MM-DD` から gate 間の lead time を計算できる
- `collect_all_metrics` が coverage / tests / cache / gate の全メトリクスを統合して返す（`summary.cache_hit_rate` を含む）
- `format_human_readable` が主要セクション見出しを含む
- `--json` 出力が valid JSON で主要キーを持つ
- coverage / test results / cache が存在しない場合に `found: False` で graceful に返る

### 3-2. `tests/test_process_metrics_integration.py`

対象: `stride_process_metrics.py`

最低限入れるテスト:

- `parse_approval_dates` が APPROVAL.md から日付を抽出できる
- `compute_gate_process_times` が gate 間の日数を計算できる
- `determine_current_gate` が正しい gate を返す
- `assess_delay_risk` が complexity と age から risk を判定する
- `compute_inject_rates` が `tasks.md` の `tasks_gate_check.counts.tasks`（初期値）と実タスク配列長（現在値）から inject rate を計算する（入力は `runs/` の findings ではなく `tasks.md` + `state/state.yaml` の `work_items`）
- `analyze_feature` が FeatureMetrics を返す
- `format_json` / `format_table` / `format_markdown` が有効な出力を生成する
- `update_dashboard` に `dry_run=True` を渡して `epics/<epic_ref>/PM_DASHBOARD.md` を変更しないことを確認する
- `find_dashboard_path` が `state/state.yaml` の `epic_ref` → `epics/<epic_ref>/PM_DASHBOARD.md` を正しく辿れる

注意:
- `parse_approval_dates` が期待する APPROVAL.md の日付形式（`日付: YYYY-MM-DD`）を実装から確認すること。既存の `FeatureBuilder._write_approval()` は日付を出力しないので、テスト用に日付付き承認を書く補助メソッドを追加すること。
- `compute_inject_rates` の入力は `tasks.md` の Canonical YAML と `state/state.yaml` の `work_items` リスト。`work_items/WI-*.md` ファイルや `runs/` の findings ではない。
- `update_dashboard` は feature 配下ではなく `epics/<epic_ref>/PM_DASHBOARD.md` を更新する。fixture に epic ディレクトリと PM_DASHBOARD.md を含めること。

### 3-3. `tests/test_testreport_bridge_integration.py`

対象: `stride_testreport_bridge.py`

最低限入れるテスト:

- `find_cases_json` が `testreport/cases.json` を優先的に見つける
- `find_cases_json` が `evidence/cases.json` にフォールバックする
- `load_cases` が cases.json をパースして test case リストを返す
- `build_mapping_index` が `case_id → stride_refs` のマッピングを構築する（AC ID → test case ではない）
- `analyze` が coverage / unmapped / gap を検出する
- `check_report_html` が report.html の存在を検出する
- `run_testreport_validate` は `testreport` CLI が不在の場合に `available: False` を返す
- `format_text` が主要セクション（`Test cases` / `Evidence files` / `Mapped ACs` / `Unmapped cases` / `Validate` / `Report HTML`）を含む

注意:
- `analyze()` の mapping path は `cases.json` と同じディレクトリの `stride_mapping.yaml` に既定される。`evidence/cases.json` フォールバック経路をテストする場合、mapping も `evidence/stride_mapping.yaml` に置くこと。
- `run_testreport_validate` は `shutil.which("testreport")` で存在チェックする。テスト環境に `testreport` CLI がない前提で、`available: False` の経路を検証する。`available: True` の経路をテストしたい場合は `shutil.which` を monkeypatch して `subprocess.run` も差し替えること。

### 3-4. `tests/test_project_labels_integration.py`

対象: `setup_project_labels.py`

最低限入れるテスト:

- `create_labels` に `dry_run=True` を渡して全ラベルが `DRY-RUN:` で報告される
- `create_labels` の `dry_run=True` で `_run_gh` が呼ばれない
- `_run_gh` を monkeypatch して `(0, "", "")` を返す場合に `created` カウントが増える
- `_run_gh` を monkeypatch して `(1, "", "already exists")` を返す場合に `exists` カウントが増える
- `_run_gh` を monkeypatch して `(1, "", "permission denied")` を返す場合に `failed` カウントが増える
- `create_symphony_labels` も `dry_run=True` で同様に動作する
- `STRIDE_LABELS` と `SYMPHONY_LABELS` の定数が空でないことを確認する

注意:
- `_run_gh` の monkeypatch 対象は `setup_project_labels._run_gh`。`subprocess.run` ではなくモジュールレベルの関数を差し替えること。

## Step 4: 既存テスト資産を壊さないこと

以下は維持必須。

- `tests/` と `symphony/tests/` の既存テストは削除しない
- `pyproject.toml` の `testpaths` / `markers` は壊さない
- `symphony/tests/test_evaluator_live.py` は変更不要

## Step 5: 検証

実装後は以下を順番に実行すること。

```bash
# self-test が壊れていないことを確認
python3 sdd-templates/tools/evidence_metrics_collector.py --test
python3 sdd-templates/tools/stride_process_metrics.py --test
python3 sdd-templates/tools/stride_testreport_bridge.py --test
python3 sdd-templates/tools/setup_project_labels.py --test
python3 sdd-templates/tools/setup_project_labels.py --test-symphony

# Phase 4 テストのみ実行
python3 -m pytest \
  tests/test_evidence_metrics_integration.py \
  tests/test_process_metrics_integration.py \
  tests/test_testreport_bridge_integration.py \
  tests/test_project_labels_integration.py \
  -v --tb=short

# 全体回帰
python3 -m pytest -m "not api" -q --tb=short
```

## 完了基準

以下がすべて満たされていること。

| # | 確認項目 | 合格条件 |
|---|---------|---------|
| 1 | `tests/test_evidence_metrics_integration.py` が追加され PASS | |
| 2 | `tests/test_process_metrics_integration.py` が追加され PASS | |
| 3 | `tests/test_testreport_bridge_integration.py` が追加され PASS | |
| 4 | `tests/test_project_labels_integration.py` が追加され PASS | |
| 5 | 関連 tool の self-test が壊れていない | 4 ツールとも全 PASS（`setup_project_labels` は `--test` と `--test-symphony` の両方） |
| 6 | `python3 -m pytest -m "not api" -q --tb=short` が全 PASS | |
| 7 | 追加テスト件数と最終総件数を報告できる | |
| 8 | repo root 汚染や GitHub 実ネットワークに依存しない | |

## 完了後の報告形式

以下の形式で報告すること。

```text
=== Phase 4 完了報告 ===

追加したテスト:
  - tests/test_evidence_metrics_integration.py: <N> tests
  - tests/test_process_metrics_integration.py: <N> tests
  - tests/test_testreport_bridge_integration.py: <N> tests
  - tests/test_project_labels_integration.py: <N> tests

拡張した基盤:
  - tests/project_builder.py: <要点>
  - tests/conftest.py: <要点>

検証結果:
  - evidence_metrics_collector.py --test: <結果>
  - stride_process_metrics.py --test: <結果>
  - stride_testreport_bridge.py --test: <結果>
  - setup_project_labels.py --test: <結果>
  - setup_project_labels.py --test-symphony: <結果>
  - 新規 Phase 4 テスト: <N> passed
  - 全体 (`-m "not api"`): <TOTAL> passed, <DESELECTED> deselected

補足:
  - mock にした外部依存箇所
  - 見つけて修正したテンプレート不具合があればその内容
```

## 禁止事項

- `gh` 実呼び出し前提のテスト
- `testreport` CLI のインストールを前提としたテスト
- repo root 直下のファイル書き換え前提テスト
- 壊れた経路でも通る弱い assert
- Phase 4 の名目で unrelated な機能追加
