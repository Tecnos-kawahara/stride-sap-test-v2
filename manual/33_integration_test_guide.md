# 統合テストフレームワーク ガイド

> 600 テストの pytest スイートで全 STRIDE ツールチェーンの回帰を保護（v5.2 で hermetic 化、v5.3 系で Linear + GitHub Project 系 18 テスト追加、v5.4 で Profile Policy 20 テスト追加）

## 概要

Tecnos-STRIDE の 31 個の Python ツール（v5.2 `stride_shared_lib.py` / v5.3 `linear_bridge.py` / v5.3.1 `github_project_bridge.py`、v5.4 は既存ツール拡張のみ）と CLI サブコマンドは、pytest ベースの統合テストで保護されている。
テストは `tmp_path` に isolated project root を動的生成し、repo root を汚さず、ネットワーク非依存で deterministic に実行される。

**v5.2 の hermetic 設計**: `pyproject.toml` に `addopts = "-m 'not api'"` と `testpaths = [symphony/tests, tests, sdd-templates/tests]` を確定。default `pytest` は API 到達性不要で確実に通る。

## テスト構成

```bash
# default（hermetic、API テストは自動 deselect）
python3 -m pytest -q --tb=short                     # 596 passed / 1 skipped / 3 deselected

# Harness Maturity スイート
python3 -m pytest -m "harness" -q --tb=short        # 64 passed

# Execution Authority E2E（v5.2 新規）
python3 -m pytest sdd-templates/tests/ -q           # 14 passed

# Profile Policy（v5.4 新規）
python3 -m pytest tests/test_profile_policy.py -q   # 20 passed

# E2E — CLI + Enterprise
python3 -m pytest -m "e2e" -q --tb=short            # 25 passed

# Live API（要 .env.local + provider 到達性）
python3 -m pytest -m "api" -q --tb=short            # 3 tests (default では deselect)

# 全テスト（addopts を上書きして api 含む全て実行）
python3 -m pytest --override-ini="addopts=" -q      # 600 total
```

### Marker 一覧

| Marker | 用途 | default 実行 |
|--------|------|-------------|
| `api` | 実 API 呼び出し（OpenAI, Gemini）| **自動 deselect**（pyproject.toml addopts で制御） |
| `e2e` | stride CLI の subprocess 実行 | 実行対象 |
| `slow` | 長時間テスト | 実行対象（必要に応じて `-m "not slow"`）|
| `harness` | Harness Maturity 関連（v5.1+） | 実行対象 |

## テストファイル一覧

### Unit Tests (symphony/tests/) — 262 tests

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `test_evaluator_core.py` | 14 | multi_model_evaluator コアロジック |
| `test_stride_bridge_evaluate.py` | 3 | stride_bridge evaluate API |
| `test_evaluator_live.py` | 3 | @api ライブ API（v5.2 で default deselect） |
| `test_stride_bridge.py` | 15 | stride_bridge lint/sync/PR |
| `test_janitor.py` | 18 | Symphony Janitor（v5.1 で追加、v5.2 で 18 tests へ拡張） |
| その他 13 ファイル | 209 | symphony engine |

### Execution Authority E2E (sdd-templates/tests/) — 14 tests (v5.2 新規)

| ファイル | テスト数 | 対象 |
|---------|---------|------|
| `test_execution_authority_e2e.py` | 14 | Normal (4) + Failure (5) + Janitor (5) の end-to-end 検証（v4.6 Article XIV / wi_readiness Check 8 / Janitor 統合） |

### Integration Tests (tests/) — 282 tests

| ファイル | テスト数 | Phase | 対象ツール |
|---------|---------|-------|-----------|
| `test_stride_lint_integration.py` | 22 | 1 | stride_lint.py（CLI UX: suggested_action, color, plain, ndjson, typo, YAML preflight, actor） |
| `test_phase_gate_integration.py` | — | 1 | phase_gate.py |
| `test_auto_continue_integration.py` | — | 1 | auto_continue_runner.py |
| `test_pr_readiness_integration.py` | — | 1 | pr_readiness_checker.py |
| `test_stride_cli_integration.py` | — | 1 | stride CLI |
| `test_epic_integration.py` | 6 | 2 | epic_validator, epic_progress, enterprise lint |
| `test_dependency_integration.py` | 10 | 2 | dependency_checker |
| `test_erp_addon_integration.py` | 5 | 2 | erp_addon_exec_tracking |
| `test_amendment_integration.py` | 6 | 2 | amendment_generator |
| `test_bootstrap_cli_e2e.py` | 14 | 3 | @e2e intake, init, ddd-init, hooks |
| `test_enterprise_cli_e2e.py` | 11 | 3 | @e2e epic CLI, lint --enterprise |
| `test_brownfield_integration.py` | 7 | 3 | brownfield_detector |
| `test_spec_drift_integration.py` | 5 | 3 | spec_drift_detector |
| `test_decision_index_integration.py` | 7 | 3 | decision_index |
| `test_approval_router_integration.py` | 7 | 3 | approval_router |
| `test_hooks_integration.py` | 5 | 3 | setup_hooks |
| `test_wi_readiness_integration.py` | 7 | 3 | wi_readiness_checker |
| `test_run_resume_integration.py` | 6 | 3 | run_resume_detector |
| `test_run_report_integration.py` | 8 | 3 | run_report_generator |
| `test_sdd_planning_bridge_integration.py` | 4 | 3 | sdd_planning_bridge |
| `test_wi_sync_integration.py` | 8 | 3 | stride_wi_sync |
| `test_evidence_metrics_integration.py` | 10 | 4 | evidence_metrics_collector |
| `test_process_metrics_integration.py` | 15 | 4 | stride_process_metrics |
| `test_testreport_bridge_integration.py` | 11 | 4 | stride_testreport_bridge |
| `test_project_labels_integration.py` | 9 | 4 | setup_project_labels |
| `test_self_review.py` | 11 | 4 | multi_model_evaluator self_review_loop（v5.1 Harness）|
| `test_stride_symphony_dispatch.py` | 5 | 4 | stride symphony CLI dispatch（v5.2 新規、1 skipped w/o GH_TOKEN）|
| `test_harness_*.py` / `test_stride_health.py` / `test_harness_report.py` | 30+ | 4 | Harness Maturity（mutation / self-review / health / harness-report）|

## テスト基盤: ProjectBuilder

`tests/project_builder.py` は `tmp_path` に isolated STRIDE project root を動的生成する。

```python
from tests.project_builder import ProjectBuilder

project = (
    ProjectBuilder(tmp_path)
    .enable_enterprise()
    .add_epic("EPIC-TEST")
    .with_features("FEAT-X")
    .with_approval({"E1", "E2"})
    .done()
    .add_feature("FEAT-X", mode="full", phase=5, coverage_tier="critical")
    .with_enterprise("EPIC-TEST", "TEAM-DEV")
    .with_erp_addon()
    .with_approval_dates({1: "2026-01-10", 2: "2026-01-12"})
    .done()
    .build()
)
```

### 主な Builder メソッド

| メソッド | 用途 |
|---------|------|
| `add_feature(id, mode, phase, coverage_tier)` | Feature 追加 |
| `add_epic(id)` | Epic 追加 |
| `enable_enterprise()` | Enterprise モード有効化 |
| `.with_erp_addon()` | ERP Addon 有効化 |
| `.with_enterprise(epic_id, team_id)` | Enterprise フィールド設定 |
| `.with_approval_dates(dates)` | Gate 承認日付設定 |
| `.with_dependency_manifest(deps)` | 依存マニフェスト追加 |
| `.with_amendment_artifacts()` | Amendment 用 run artifacts |
| `.mutate_lint_error(type)` | lint エラーの意図的注入 |

### ヘルパー関数

| 関数 | 用途 |
|------|------|
| `add_brownfield_indicators(root, lang, monorepo)` | Brownfield 指標追加 |
| `add_spec_drift_artifacts(root, ...)` | Spec drift 用 contracts + routes |
| `add_adr_artifacts(root, count)` | ADR ファイル生成 |
| `add_hooks_settings(root, state)` | .claude/settings.json 生成 |
| `add_run_lifecycle(feature, wi, run, artifacts)` | Run ディレクトリ + artifacts |
| `add_coverage_summary(root, ...)` | Istanbul coverage JSON |
| `add_junit_xml(root, ...)` | JUnit XML test results |
| `add_turbo_cache(root, total, cached)` | Turbo cache stats |
| `add_testreport_artifacts(feature, ...)` | testreport cases + mapping |
| `add_state_yaml(feature, work_items, epic_ref)` | state/state.yaml |
| `add_pm_dashboard(epic_dir)` | PM_DASHBOARD.md |

## Fixture 一覧

`tests/conftest.py` に定義済み:

| Fixture | 用途 |
|---------|------|
| `full_pass_project` | 全 Gate 承認済みの standard feature |
| `lite_pass_project` | Lite Mode 全承認 |
| `design_phase_project` | Phase 1 進行中 |
| `specify_phase_project` | Phase 2 進行中 |
| `enterprise_project` | Epic + Feature linked |
| `enterprise_project_with_cycle` | 循環依存あり |
| `erp_addon_project` | ERP Addon active |
| `amendment_project` | Amendment run artifacts |
| `brownfield_project` | Node.js brownfield |
| `spec_drift_project` | Drift 検出用 |
| `adr_project` | ADR 3件 |
| `hooks_project` | .claude/ dir |
| `wi_ready_project` | WI readiness 用 |
| `interrupted_run_project` | 中断 Run |
| `run_report_project` | 完全 Run |
| `planning_bridge_project` | Planning bridge 用 |
| `evidence_project` | Coverage + JUnit + Cache |
| `process_metrics_project` | 承認日付 + WI + Dashboard |
| `testreport_project` | cases.json + mapping |
| `bootstrap_project_root` | CLI E2E 用 |

## 外部依存の Mock

| 対象 | Mock 方法 |
|------|----------|
| `amendment_generator._run_gh` | monkeypatch → `(1, "", "gh not found")` |
| `amendment_generator._search_issues_by_label` | monkeypatch → `[]` |
| `sdd_planning_bridge.KNOWLEDGE_DIR` | monkeypatch → `tmp_path` |
| `run_report_generator._run_gh` | monkeypatch → `(0, "ok", "")` |
| `setup_project_labels._run_gh` | monkeypatch → success/exists/failed |
| `stride_wi_sync.get_repo` / `fetch_issues` | monkeypatch → mock data |
| `shutil.which("testreport")` | monkeypatch → None |
| `builtins.input` | monkeypatch → `lambda _: "y"` |

## CI 統合

```yaml
# .github/workflows/stride-test.yml
- name: Run STRIDE tests
  run: python3 -m pytest -q --tb=short
  # pyproject.toml の addopts = "-m 'not api'" により api テストは自動 deselect されます。
  # 明示的に api も走らせたい場合は: python3 -m pytest --override-ini="addopts=" -q
```

**v5.2 hermetic 設計**:
- `@pytest.mark.api` 付きテスト（`symphony/tests/test_evaluator_live.py` の 3 件）は
  `pyproject.toml` の `addopts = "-m 'not api'"` により **default で deselect**（実行前に除外）される。
- これは従来の「API キー不在時の skip」とは異なる仕組み：テストは実行されず、collection 結果の
  `deselected` 欄にカウントされる（`596 passed / 1 skipped / 3 deselected` の `3 deselected` が該当）。
- `1 skipped` は `test_stride_symphony_dispatch.py` の `GH_TOKEN` 未設定時の `pytest.skip` 由来
  （こちらは実行時判定）。
- `e2e` テストは CI でも実行可能（subprocess のみ、ネットワーク不要）。

## テストの追加方法

1. 新ツールを `sdd-templates/tools/` に追加
2. 必要に応じて `tests/project_builder.py` にヘルパーを追加
3. `tests/conftest.py` に fixture を追加
4. `tests/test_<tool>_integration.py` を作成
5. `python3 -m pytest -m "not api" -q --tb=short` で回帰なしを確認
