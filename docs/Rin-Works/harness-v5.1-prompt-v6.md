# Tecnos-STRIDE v5.1.0 "Harness Maturity" v6 Claude Code 指示プロンプト

作業ディレクトリ: `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

## WI: HARNESS-001-v6 / v5.1.0 "Harness Maturity"
## feat(harness): Fowler-inspired Harness Integration (Mutation post-integration / Self-review / Runtime sensors / Janitor proposals / Feedforward guide)

### Step 0: 準備
```bash
git checkout -b feat/harness-v5.1-v6
git pull origin main
```

### Step 1: 現状把握
必ず以下を読むこと:
- `README.md`
- `pyproject.toml`
- `requirements-dev.txt`
- `sdd-templates/bin/stride`
- `sdd-templates/tools/pr_readiness_checker.py`
- `sdd-templates/tools/multi_model_evaluator.py`
- `symphony/config.py`
- `symphony/tracker.py`
- `symphony/cli.py`
- `SYMPHONY.md`
- `agent_docs/`
- `tests/project_builder.py`
- `manual/35_retro_guide.md` を確認し、新規ガイドは `manual/36_harness_guide.md` にする

確認コマンド:
```bash
grep -rn "run_all_checks\|format_human_readable\|def main" sdd-templates/tools/pr_readiness_checker.py
grep -rn "aggregate_results\|def main" sdd-templates/tools/multi_model_evaluator.py
grep -rn "class SymphonyConfig\|_build_dataclass" symphony/config.py
grep -rn "def fetch_ready_issues\|def post_comment" symphony/tracker.py
grep -rn "def cmd_run" symphony/cli.py
```

### 実装方針
- Mutation testing は高コストなので `pr-check` のデフォルトには入れず、`--mutation` opt-in とする。
- Self-review は `aggregate_results()` に CLI 状態を持ち込まず、`main()` で borderline 判定して primary result に反映してから集計する。
- Janitor は自動 PR ではなく GitHub Issue 提案のみ。低リスク条件は `issue.labels` と `has_recent_pr()` で判定する。
- Feedforward は `agent_docs/harness.md` に集約し、未定義の `SYMPHONY.md` front-matter key は追加しない。
- `MUTATION_THRESHOLD=80` は記事の固定値ではなく、このテンプレートの project policy として `.env.local` で定義する。

### Step 2: Mutation Testing
対象: `sdd-templates/tools/pr_readiness_checker.py`, `sdd-templates/bin/stride`, `requirements-dev.txt`

実装:
- `requirements-dev.txt` に `cosmic-ray` を追加する。`sdd-templates/requirements.txt` は汚さない。
- `pr_readiness_checker.py` に `mutation_check(project_root: Path, threshold: int) -> dict` を追加する。
- 返却形式は既存 check と揃え、`{"status": STATUS_PASS|STATUS_FAIL, "kill_rate": <float>, "threshold": <int>, "detail": <str>}` とする。
- threshold は `int(os.getenv("MUTATION_THRESHOLD", "80"))` を使う。
- `run_all_checks(project_root, strict=False, coverage_threshold=None, verbose=False, include_mutation=False)` に拡張し、`include_mutation` が真のときのみ mutation check を append する。
- `main()` に `parser.add_argument("--mutation", action="store_true", help="Run optional mutation testing")` を追加し、`run_all_checks(..., include_mutation=args.mutation)` を呼ぶ。
- `format_human_readable()` は固定 `[idx/7]` をやめ、`total = len(result["checks"])` を使って `[idx/{total}]` 表示に直す。
- `sdd-templates/bin/stride` の help 文言も `7 checks + optional mutation` に更新する。`cmd_pr_check()` は引数 passthrough のままでよい。

### Step 3: Self-Review Loop
対象: `sdd-templates/tools/multi_model_evaluator.py`, `sdd-templates/bin/stride`

実装:
- `multi_model_evaluator.py` に `self_review_loop(review_packet: dict[str, Any], max_iters: int = 3) -> dict[str, Any]` を追加する。
- `review_packet` は少なくとも `{"feature_dir": str(feature_dir), "phase": phase, "prompt": prompt, "primary_result": openai_result}` を含める。
- `main()` に `parser.add_argument("--review", action="store_true", help="Run self-review loop for borderline primary results")` を追加する。
- `sdd-templates/bin/stride` の `cmd_evaluate()` も `--review` を受け取り、`multi_model_evaluator.py` にそのまま forward する。
- `main()` の流れは以下に固定する:
  1. prompt を構築する
  2. `openai_result` / `gemini_result` を取得する
  3. `args.review` かつ `70 <= openai_result.get("weighted_score", 0) < 85` かつ primary error でない場合のみ `self_review_loop(review_packet)` を実行する
  4. review の結果を `openai_result["self_review_issues"]` に格納する
  5. review に `severity == "critical"` があれば、それを `openai_result["critical_issues"]` に追記し、`openai_result["overall"] = "FAIL"` に更新する
  6. その後で `aggregate_results(openai_result, gemini_result, args.allow_provider_degraded)` を呼ぶ
- `aggregate_results()` 自体は pure な集計責務のままにし、`args` や `review_packet` を参照させない。

### Step 4: Runtime Sensors + Harness Coverage
対象: `sdd-templates/tools/stride_health.py`, `sdd-templates/tools/stride_harness_report.py`, `sdd-templates/bin/stride`

実装:
- 新規 `sdd-templates/tools/stride_health.py` を追加する。
- CLI は `python3 stride_health.py <project_root> [--runtime] [--json]` とする。
- 最低限の runtime sensors:
  - pylint dead code 系: `W0611`, `W0612`, `W0613`, `W0614`
  - coverage decay: 直近 baseline と比較して低下率を出す
  - `alert` 判定: dead code > 0 または coverage 低下が project policy 超過
- 新規 `sdd-templates/tools/stride_harness_report.py` を追加する。
- CLI は `python3 stride_harness_report.py <project_root> [--json]` とする。
- 出力は少なくとも `coverage_pct`, `controls`, `gaps` を持たせる。
- `sdd-templates/bin/stride` に `health` と `harness-report` の help / case / dispatch を追加する。

### Step 5: Janitor Proposals
対象: `symphony/config.py`, `symphony/tracker.py`, `symphony/cli.py`, `SYMPHONY.md`

実装:
- `symphony/config.py` に以下を追加する:
  - `@dataclass class JanitorConfig:`
  - `enabled: bool = False`
  - `interval_hours: int = 6`
  - `exclude_recent_pr_days: int = 7`
  - `risk_flags_exclude: list[str] = field(default_factory=lambda: ["risk:authz", "risk:pii", "risk:external_api", "risk:sod"])`
- `SymphonyConfig` に `janitor: JanitorConfig = field(default_factory=JanitorConfig)` を追加する。
- `SYMPHONY.md` front-matter に nested config として以下を追加する:
```yaml
janitor:
  enabled: true
  interval_hours: 6
  exclude_recent_pr_days: 7
  risk_flags_exclude:
    - risk:authz
    - risk:pii
    - risk:external_api
    - risk:sod
```
- `symphony/tracker.py` に `has_recent_pr(repo: str, feature_name: str, days: int) -> bool` を追加する。
- 実装は `gh pr list --repo <repo> --state merged --search "\"<feature_name>\" in:title merged:>=<YYYY-MM-DD>" --json number` で十分。1件でもあれば `True`。
- `symphony/cli.py` の `cmd_run()` に `last_janitor_scan_at = 0.0` を置き、polling loop 内で `config.janitor.enabled` かつ `interval_hours` 経過時のみ janitor scan を走らせる。
- v5.1 の janitor scan 対象は、既に取得している `issues` のうち以下を満たすものに限定する:
  - `'mode:autopilot' in issue.labels`
  - `'tier:starter' in issue.labels`
  - `not any(flag in issue.labels for flag in config.janitor.risk_flags_exclude)`
  - `not has_recent_pr(config.tracker.repo, issue.feature_name, config.janitor.exclude_recent_pr_days)`
- action は自動 PR ではなく、`Janitor: fix style/cyclomatic <feature>` という GitHub Issue を起票して drift report を本文に入れること。

### Step 6: Feedforward Guide
対象: `agent_docs/harness.md`, 必要なら `SYMPHONY.md` 本文

実装:
- 新規 `agent_docs/harness.md` を追加する。
- 内容は以下を含める:
  - Martin Fowler 記事の要点
  - この repo での対応: feedforward / feedback / runtime sensors / janitor proposals
  - scale ごとの運用差: starter / standard / enterprise
- もし参照導線が必要なら、`SYMPHONY.md` 本文か `agent_docs/sdd_bootstrap.md` から `agent_docs/harness.md` へのリンクを追加する。
- `harness_scale_bias` のような未定義 front-matter key は追加しない。

### Step 7: テスト
対象: `pyproject.toml`, `tests/`, `symphony/tests/`

実装:
- `pyproject.toml` の `markers` に `harness: harness maturity tests` を追加する。
- 新規テスト:
  - `tests/test_harness_mutation.py`
  - `tests/test_self_review.py`
  - `tests/test_stride_health.py`
  - `tests/test_harness_report.py`
  - `symphony/tests/test_janitor.py`
- mutation / review / health / report / janitor を各 10 fixture 程度で検証する。
- 既存の `tests/project_builder.py` を fixture 生成に使ってよい。

### Step 8: 検証
```bash
pip install -r requirements-dev.txt
pytest -m harness -q --tb=short
sdd-templates/bin/stride lint --all --enterprise
sdd-templates/bin/stride pr-check . --mutation --json
sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --review
sdd-templates/bin/stride health . --runtime --json
sdd-templates/bin/stride harness-report . --json
python3 -m symphony validate
```

### Step 9: Docs / Release
- `README.md` に v5.1.0 Harness Maturity を追記する
- `manual/36_harness_guide.md` を追加する
- コミットメッセージ案: `feat(harness): v5.1.0 Harness Maturity [HARNESS-001-v6]`
- tag 案: `v5.1.0-tecnos-stride-v6`

### 完了条件
- Placeholder や未定義 key が残っていない
- `mutation` は opt-in のみ
- `self-review` は final verdict に影響する
- `JanitorConfig` は loader で実際に読まれる
- verify コマンドは現行 CLI 形状に一致する
