# 指示プロンプト: Multi-Model Evaluator の実装 (v2)

**作業ディレクトリ:** `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

---

## 背景と目的

Tecnos-STRIDE に **stride evaluate** サブコマンドを追加する。
stride lint（構造・ID整合チェック）の補完として、LLM が「lint では検出できない意味的な穴」
（業務リスク・ERP統合の盲点・ACのテスタビリティ・SoD/監査曖昧さ）を評価するゲートを実装する。

着想元: Anthropic Labs の Generator-Evaluator アーキテクチャ
（https://www.anthropic.com/engineering/harness-design-long-running-apps）

実行経路への接続も含めて実装すること（後述）。

### このプロンプトのスコープと限界

**今回のスコープ:** Design / Specify / Tasking フェーズの **仕様成果物** に対する semantic evaluator。
lint が見逃す意味的な穴（業務リスク、ERP blind spot、AC testability、SoD 曖昧さ）を検出する。

**今回のスコープ外（次フェーズで対応）:** Anthropic 記事の最大の実利である
**runtime QA evaluator**（Playwright で実アプリの UI/API/DB を操作して不具合を検出する仕組み）は
本プロンプトには含まれない。`stride evaluate --phase execute` として別途設計・実装が必要であり、
backlog セクションに詳細を記載している。本プロンプトは「仕様品質ゲート」であり、
「long-running application development の QA ループ」の完全実装ではない。

---

## 実装前に必ず読むこと（推測で書かない）

```bash
# 1. 実行経路を追う
cat sdd-templates/tools/auto_continue_runner.py     # FULL_WORKFLOW / LITE_WORKFLOW の定義を確認
cat symphony/stride_bridge.py                        # ToolResult, _run(), lint(), auto_continue() を確認
cat sdd-templates/bin/stride                         # case ディスパッチャー（末尾）と cmd_lint を確認

# 2. SSoT 構造を確認（全文ではなく Canonical YAML ブロックを見る）
grep -n "Canonical Basic Design\|Canonical Spec\|Canonical Plan\|Canonical Tasks" \
  specs/FEAT-ERPSAMPLE/basic_design.md \
  specs/FEAT-ERPSAMPLE/spec.md \
  specs/FEAT-ERPSAMPLE/plan.md \
  specs/FEAT-ERPSAMPLE/tasks.md

# 3. spec_gate_check, plan_gate_check の counts 構造を確認（rubric 設計の根拠）
grep -A 30 "spec_gate_check:" specs/FEAT-ERPSAMPLE/spec.md
grep -A 30 "plan_gate_check:" specs/FEAT-ERPSAMPLE/plan.md

# 4. scenarios.yaml と contracts/ の存在を確認
ls specs/FEAT-ERPSAMPLE/tests/
ls specs/FEAT-ERPSAMPLE/contracts/

# 5. テスト配置の実態を確認
cat pyproject.toml                                   # testpaths = ["symphony/tests"] のみ
ls sdd-templates/tools/test_*.py                     # test_tier_mismatch.py が存在（直接実行方式）

# 6. stride lint の JSON 出力を確認
python3 sdd-templates/tools/stride_lint.py specs/FEAT-ERPSAMPLE/ --format json

# 7. 環境変数名を確認
cat .env.local
```

---

## Step 1: `sdd-templates/tools/multi_model_evaluator.py` を新規作成する

### 1-1. CLI インターフェース

```bash
python3 sdd-templates/tools/multi_model_evaluator.py specs/<feature>/ \
    [--phase design|specify|tasking] \
    [--format text|json] \
    [--allow-provider-degraded] \  # API 障害時に WARNING で続行して 0 を返す
    [--force]                      # coverage_tier によるスキップを無視して強制実行

# 終了コード（一貫した定義）
#   0: PASS（全 primary モデルが PASS、または --allow-provider-degraded でエラー免除）
#   1: FAIL（primary モデルが FAIL と判定）
#   2: PROVIDER_ERROR（API エラーかつ --allow-provider-degraded 未指定）
```

### 1-2. 評価入力: Compact Packet（全文ではなく Canonical YAML のみ）

**目的:** 全文投入はノイズ・コスト増・Enterprise で劣化する。SSoT は Canonical YAML ブロックのみ。

フェーズ別に以下を抽出して `compact_packet` を構築する。
抽出関数 `extract_canonical_yaml(filepath, marker)` は
`stride_lint.py` の `extract_yaml_after_marker()` と同じロジックで実装する
（`import stride_lint` は依存関係上禁止。独立実装すること）。

| Phase | 抽出対象 | marker |
|-------|---------|--------|
| `design` | `basic_design.md` | `"Canonical Basic Design"` |
| `design` | `process.bpmn` | BPMNのプロセス要素名・タスク名のみ抽出（全文不要）|
| `specify` | `spec.md` | `"Canonical Spec"` |
| `specify` | `plan.md` | `"Canonical Plan"` |
| `specify` | `tests/scenarios.yaml` | YAML全文（元々コンパクト） |
| `specify` | `contracts/` | ファイル名一覧のみ（`contracts/*.yaml` の basename リスト） |
| `tasking` | `tasks.md` | `"Canonical Tasks"` |
| `tasking` | `plan.md` | `"Canonical Plan"` の `coverage_policy` + `tests[]` セクションのみ抽出 |
| `tasking` | （生成）| AC→task カバレッジマップ（tasks YAML の各 task の `spec_refs` から AC ID を抽出して逆引き生成）|

**BPMN からの抽出（design フェーズ）:**
```python
# xml.etree.ElementTree で bpmn:task, bpmn:userTask, bpmn:serviceTask,
# bpmn:exclusiveGateway の name 属性のみ抽出してリスト化する
# プロセス全文は渡さない
```

### 1-3. 評価 Rubric（フェーズ別に 3 本。lint と重複しない観点のみ）

**重要:** lint がチェックする「構造・ID・カウント整合」は rubric から除外する。
LLM evaluator が見るのは「意味的な穴」のみ。

**実装:** `build_design_prompt()`, `build_specify_prompt()`, `build_tasking_prompt()` の
3 関数を作成し、フェーズに応じて呼び分ける。共通の preamble は定数で持つ。

**共通 preamble（全フェーズ共通、プロンプト冒頭に挿入）:**
```
You are a strict SDD quality evaluator for ERP integration projects.
Find semantic gaps that static linting CANNOT detect.
Do NOT comment on: ID formatting, field counts, YAML structure, APPROVAL status — stride-lint handles those.
Be skeptical. Be thorough.
Every critical_issue MUST reference a specific artifact field, AC ID, scenario ID, or task ID.
Input format: Canonical YAML blocks only (SSoT extracts).
```

**Response Format（全フェーズ共通、プロンプト末尾に挿入）:**
```
## Response Format (JSON only, no prose outside the object)
{
  "overall": "PASS" or "FAIL",
  "scores": { <criterion_key>: <0-100>, ... },
  "weighted_score": <float 0-100>,
  "critical_issues": [
    {"criterion": "<key>", "description": "<concise finding>", "severity": "critical|major|minor", "ref": "<artifact field or ID>"}
  ],
  "suggestions": ["<actionable fix>"],
  "pass_threshold": 70,
  "evaluator_model": "<actual model name used>"
}
FAIL if ANY of the following:
  - weighted_score < 70
  - any critical_issues with severity="critical"
  - any individual criterion score < 50 (hard floor per criterion — prevents a weak axis from being hidden by strong ones)
```

---

#### Rubric A: Design Phase — `build_design_prompt()`

```
Evaluate the DESIGN phase artifacts for feature [{FEATURE_ID}].

[COMPACT_PACKET: basic_design canonical YAML + BPMN process summary]

## Evaluation Criteria

### A1. Business Risk & ERP Blind Spots (weight: 35%)
- Are there ERP/SAP integration constraints that are unacknowledged (e.g., BAPI restrictions, posting locks, fiscal period dependency)?
- Are there implicit dependencies on master data (GL, cost center, vendor) that are not stated in scope.in or systems[]?
- Are audit/compliance requirements (SoD, e.g., same person cannot approve their own orders) ambiguous or missing from scope?

### A2. AC Testability (weight: 30%)
- Can each acceptance criterion in basic_design be verified by an automated test as written?
- Are there ACs that conflate multiple testable behaviors in a single criterion?
- Are error flows and boundary conditions (e.g., "在庫不足", "権限不足") represented as distinct ACs?

### A3. Integration Architecture (weight: 20%)
- Are all external system touch points (APIs, file interfaces, event buses) identified with protocol/auth/error handling noted?
- Are idempotency and retry behaviors specified for each integration in requirements.integration[]?
- Are timeout values and circuit-breaker strategies defined?

### A4. Scope Defensibility (weight: 15%)
- Is the scope boundary (in/out) defensible, or are there likely scope creep vectors?
- Are out-of-scope items linked to specific future features (not just "out of scope")?
- Are there open_questions or assumptions that should be tracked but are embedded in prose?
```

**scores keys:** `business_risk_erp`, `ac_testability`, `integration_architecture`, `scope_defensibility`

---

#### Rubric B: Specify Phase — `build_specify_prompt()`

```
Evaluate the SPECIFY phase artifacts for feature [{FEATURE_ID}].

[COMPACT_PACKET: spec canonical YAML + plan canonical YAML + scenario index + contracts file list]

## Evaluation Criteria

### B1. Cross-Artifact Semantic Consistency (weight: 30%)
- Do the plan's test strategies actually verify the spec's acceptance criteria?
- Are the plan's architecture decisions (libraries[], contracts[]) consistent with the spec's NFRs?
- Do the contracts (API endpoints, DB schema) cover all use cases described in the spec?
- Are there ACs in the spec that have no corresponding test scenario in scenarios.yaml?

### B2. NFR Feasibility (weight: 25%)
- Are performance targets (e.g., "P95 < 3秒") achievable given the described architecture?
- Are security requirements (RBAC, SoD, audit) specific enough to produce test assertions?
- Are data governance policies (retention period, SoR designation) operationally enforceable?

### B3. Test Scenario Coverage Quality (weight: 25%)
- Do scenarios cover both happy path AND error/boundary cases for each AC?
- Are SoD violation scenarios explicitly tested (e.g., "登録者=承認者" → 403)?
- Are integration failure scenarios (timeout, unavailable, partial failure) represented?
- Are e2e-tagged scenarios focused on critical user journeys (not overused)?

### B4. Audit & Compliance Gaps (weight: 20%)
- Are audit log fields (user_id, action, timestamp, target_id) sufficient for regulatory review?
- Is the approval workflow complete for all paths and edge cases (e.g., rejection, re-approval)?
- Are data retention and deletion policies defined with concrete durations and trigger conditions?
```

**scores keys:** `cross_artifact_consistency`, `nfr_feasibility`, `test_scenario_quality`, `audit_compliance`

---

#### Rubric C: Tasking Phase — `build_tasking_prompt()`

```
Evaluate the TASKING phase artifacts for feature [{FEATURE_ID}].

[COMPACT_PACKET: tasks canonical YAML + plan coverage summary + AC-to-task coverage map]

## Evaluation Criteria

### C1. Implementation Risk Assessment (weight: 40%)
- Are high-risk tasks (auth, accounting, data migration) assigned mode=validate with appropriate risk_flags?
- Are risk_flags realistic for each task's actual scope (not under- or over-flagged)?
- Is the task ordering safe? (contracts-first, then implementation, then integration tests)
- Are tasks that touch SoD, audit, or financial calculation flagged as security_sensitive?

### C2. Coverage Completeness (weight: 35%)
- Are all acceptance criteria reachable through the task dependency graph?
- Are integration test tasks paired with the correct contract definition tasks?
- Is there a dedicated task for SoD enforcement testing?
- Does the coverage summary show gaps (ACs without corresponding tasks)?

### C3. Estimation & Dependency Realism (weight: 25%)
- Are task granularities appropriate (not too large to review, not too fragmented to manage)?
- Are dependency chains realistic (no impossible parallelism assumed)?
- Are milestone groupings logical (e.g., all contract tasks in the same milestone)?
- Is the total task count proportional to the spec complexity?
```

**scores keys:** `implementation_risk`, `coverage_completeness`, `estimation_realism`

### 1-4. モデル設定（`.env.local` から読み込む）

**`.env.local` の手動パース（`python-dotenv` 非使用）:**
```python
def load_env_local(project_root: Path) -> None:
    env_path = project_root / ".env.local"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if v:  # 空値は上書きしない
                    os.environ.setdefault(k, v)
```

**OpenAI:**
```python
import openai

openai_api_key = os.environ.get("OPENAI_API_KEY", "")
openai_model = os.environ.get("OPENAI_MODEL", "")  # 空 = 未設定
# 有効値: none, minimal, low, medium, high, xhigh（モデル依存）
reasoning_effort = os.environ.get("OPENAI_REASONING_EFFORT", "xhigh")

if not openai_api_key:
    print("ERROR: OPENAI_API_KEY is not set in .env.local", file=sys.stderr)
    sys.exit(2)  # CONFIG_ERROR
if not openai_model:
    print("ERROR: OPENAI_MODEL is not set in .env.local (e.g., gpt-4.1, o3)", file=sys.stderr)
    sys.exit(2)  # CONFIG_ERROR

client = openai.OpenAI(api_key=openai_api_key)
# 実装時に OpenAI の最新 API docs を確認し、利用可能な API に合わせること
# Responses API を使用する場合（reasoning モデル）:
response = client.responses.create(
    model=openai_model,
    reasoning={"effort": reasoning_effort},
    input=[{"role": "user", "content": prompt}],
    max_output_tokens=4000,
)
content = response.output_text
```

**Gemini（`GEMINI_API_KEY` 設定時は AI Studio 直接、未設定時は Vertex AI）:**

Secondary は optional。`GEMINI_MODEL` 未設定なら secondary は無効（primary only で動作）。

```python
gemini_model = os.environ.get("GEMINI_MODEL", "")  # 空 = secondary 無効
thinking_budget = int(os.environ.get("GEMINI_THINKING_BUDGET", "-1"))
gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

# gemini_model が空なら secondary は無効として扱う（CONFIG_ERROR にしない）
if not gemini_model:
    # Secondary disabled — primary only mode
    return None

if gemini_api_key:
    # AI Studio 経由: google-genai SDK
    from google import genai as google_genai
    from google.genai import types as genai_types
    gclient = google_genai.Client(api_key=gemini_api_key)
    config = genai_types.GenerateContentConfig(
        thinking_config=genai_types.ThinkingConfig(thinking_budget=thinking_budget)
    )
    response = gclient.models.generate_content(
        model=gemini_model,
        contents=prompt,
        config=config,
    )
    content = response.text
else:
    # Vertex AI 経由（ADC 認証）
    import vertexai
    from vertexai.generative_models import GenerativeModel
    project = os.environ.get("VERTEX_AI_PROJECT", "tecnos-cbp")
    location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
    vertexai.init(project=project, location=location)
    model = GenerativeModel(gemini_model)
    response = model.generate_content(
        prompt,
        generation_config={"thinking_config": {"thinking_budget": thinking_budget}},
    )
    content = response.text
```

### 1-5. 集計ロジック（Primary + Tie-breaker 方式）

**2モデル常時 veto ではなく、primary + tie-breaker 方式にする:**

```python
def is_hard_fail(result: dict) -> bool:
    """Check if any individual criterion score is below the hard floor."""
    return any(score < 50 for score in result.get("scores", {}).values())

def aggregate_results(openai_result, gemini_result):
    """
    FAIL 判定（3条件 OR）:
      1. weighted_score < 70
      2. critical_issues に severity="critical" が存在
      3. いずれかの criterion score < 50（hard floor — 弱い軸が平均で隠れない）

    Primary: OpenAI が判定する
    Tie-breaker: Primary が FAIL かつ weighted_score が 60-79 の「境界域」のとき、
                 Gemini も FAIL なら FAIL、Gemini が PASS なら WARN
                 ただし hard floor 違反（criterion < 50）は境界域でも即 FAIL（tie-break しない）

    明確な FAIL（weighted_score < 60 or critical が2件以上 or hard floor 違反）:
        → Primary 単独で FAIL 確定（Secondary は参考情報のみ）

    ERROR の扱い（--allow-provider-degraded フラグ依存）:
        - primary ERROR + --allow-provider-degraded 未指定 → 終了コード 2（hard gate: primary は必須）
        - primary ERROR + --allow-provider-degraded 指定 → WARN / exit 0
        - secondary ERROR のみ（primary は正常） → WARN / exit 0（secondary は補助なので常に許容）
        - both ERROR + --allow-provider-degraded 未指定 → 終了コード 2
        - both ERROR + --allow-provider-degraded 指定 → WARN / exit 0

    返り値: {"overall": "PASS"|"FAIL"|"WARN", "exit_code": 0|1|2, "reason": "..."}
    """
```

**PASS/FAIL/WARN/ERROR の終了コード対応（矛盾なし）:**

| 状態 | exit_code |
|------|-----------|
| PASS | 0 |
| WARN（tie-break 境界域、または secondary のみ ERROR） | 0（ログに WARN を出力） |
| FAIL | 1 |
| PROVIDER_ERROR（primary ERROR かつ --allow-provider-degraded 未指定） | 2 |

### 1-6. 評価レポートの出力

- **JSON 正本:** `specs/<feature>/state/evaluator_latest.json`（上書き、常に最新）
- **Markdown サマリー:** `specs/<feature>/state/eval_report_<phase>_<timestamp>.md`（追記・履歴残し）
- JSON に `evaluator_model` フィールドを含めること（実際に呼んだモデル名を記録）

### 1-7. エラーハンドリング

- `OPENAI_API_KEY` が空 → `stderr` に `ERROR: OPENAI_API_KEY is not set` を出力して終了コード 2
- `OPENAI_MODEL` が空 → `stderr` に `ERROR: OPENAI_MODEL is not set` を出力して終了コード 2
- API 呼び出し失敗 → リトライ 1 回（5 秒待ち）→ それでも失敗なら:
  - `--allow-provider-degraded` 指定時 → WARN に降格（終了コード 0、ログに WARNING 出力）
  - `--allow-provider-degraded` 未指定時 → 終了コード 2（PROVIDER_ERROR）
- JSON パース失敗（モデルが非 JSON を返した場合）→ API_ERROR として集計に渡す（例外を出さない）

---

## Step 2: `sdd-templates/bin/stride` に `evaluate` サブコマンドを追加する

**ファイル末尾の `case` ディスパッチャー**に以下を追加する
（`auto-continue)` の直後、`ddd-init)` の前）:

```bash
evaluate)
    shift
    cmd_evaluate "$@"
    ;;
```

**`cmd_evaluate()` 関数**を `cmd_auto_continue()` の直後に追加する:

```bash
cmd_evaluate() {
    local FEATURE_DIR=""
    local PHASE="design"
    local FORMAT="text"
    local ALLOW_DEGRADED=""
    local FORCE=""

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --phase) PHASE="$2"; shift 2 ;;
            --format) FORMAT="$2"; shift 2 ;;
            --allow-provider-degraded) ALLOW_DEGRADED="--allow-provider-degraded"; shift ;;
            --force) FORCE="--force"; shift ;;
            --lite-mode|--enterprise)
                echo -e "${RED}Error: '$1' is not yet supported by stride evaluate.${NC}"
                echo "stride evaluate does not have mode-specific rubrics yet."
                echo "Remove '$1' to proceed, or wait for a future release."
                exit 1
                ;;
            -*) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
            *) FEATURE_DIR="$1"; shift ;;
        esac
    done

    if [ -z "$FEATURE_DIR" ]; then
        echo -e "${RED}Error: feature path required${NC}"
        echo "Usage: stride evaluate specs/<feature>/ --phase design|specify|tasking"
        exit 1
    fi

    local PY; PY=$(_resolve_python)
    "$PY" "$TOOLS_DIR/multi_model_evaluator.py" \
        "$FEATURE_DIR" \
        --phase "$PHASE" \
        --format "$FORMAT" \
        $ALLOW_DEGRADED \
        $FORCE
}
```

**`show_help()` の Commands リスト**に以下を追加する（`auto-continue` の直後）:

```
  evaluate <feature_path>   Multi-model LLM evaluation (semantic gaps, ERP blind spots)
    --phase <phase>         design (default), specify, tasking
    --format text|json      Output format
    --allow-provider-degraded  Treat API errors as WARN (exit 0)
    --force                 Run even if coverage_tier=starter (normally skipped)
```

---

## Step 3: `sdd-templates/tools/auto_continue_runner.py` の `FULL_WORKFLOW` と `LITE_WORKFLOW` に evaluator ステップを追加する

**変更箇所:** `FULL_WORKFLOW` と `LITE_WORKFLOW` の各フェーズの
「stride lint PASS」ステップの直後に evaluator ステップを挿入する。

**条件付きスキップ:** evaluator はコストがかかるため、全 feature に常時適用するのではなく、
`basic_design.md` の `coverage_tier` に基づいてスキップ判定を行う。

`multi_model_evaluator.py` の冒頭で以下のチェックを入れる:
```python
def should_skip_evaluation(feature_dir: Path) -> bool:
    """coverage_tier が starter の feature では evaluator をスキップする。
    critical/standard のみ evaluator を実行する。"""
    bd_path = feature_dir / "basic_design.md"
    if not bd_path.exists():
        return False  # basic_design がなければスキップ判定不能 → 実行する
    yaml_text = extract_canonical_yaml(bd_path, "Canonical Basic Design")
    if not yaml_text:
        return False
    data = yaml.safe_load(yaml_text)
    tier = data.get("basic_design", {}).get("coverage_tier", "standard")
    return tier == "starter"
```

スキップ時は以下を出力して exit 0 で終了する:
```
SKIP: coverage_tier=starter — evaluator skipped (use --force to override)
```

`--force` フラグを追加し、指定時は coverage_tier に関係なく常に評価を実行する。

**`FULL_WORKFLOW` の変更（3フェーズ）:**

```python
FULL_WORKFLOW: dict[int, dict[str, object]] = {
    1: {
        "phase_name": "Design",
        "steps": [
            ("PASS", "Update `basic_design.md` and `process.bpmn` using current intent.", ""),
            ("PASS", "Run pre-approval lint and resolve structural issues.", "sdd-templates/tools/stride-lint {feature} --warn-only"),
            ("PASS", "Run strict lint and fix all errors except `APPROVAL_PENDING`.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase design"),
            ("WARN", "HITL checkpoint: request Gate 1, 2 approval in `APPROVAL.md`.", ""),
        ],
    },
    2: {
        "phase_name": "Specify",
        "steps": [
            ("PASS", "Update `spec.md`, `plan.md`, and required contract artifacts.", ""),
            ("PASS", "Update `tests/scenarios.yaml` for new/changed acceptance criteria.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase specify"),
            ("WARN", "HITL checkpoint: request Gate 3, 4 approval in `APPROVAL.md`.", ""),
        ],
    },
    3: {
        "phase_name": "Tasking",
        "steps": [
            ("PASS", "Update `tasks.md` and ensure all `plan_refs` are linked.", ""),
            ("PASS", "Create/adjust test tasks for integration/e2e tagged ACs.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase tasking"),
            ("WARN", "HITL checkpoint: request Gate 5 approval in `APPROVAL.md`.", ""),
        ],
    },
    4: {
        "phase_name": "Execute",
        "steps": [
            ("PASS", "Execute tasks one by one and keep spec/plan/task traceability in sync.", ""),
            ("PASS", "Update Run artifacts (`.planning/`, `test_results.md`, `walkthrough.md`).", ""),
            ("PASS", "Run lint and project tests before requesting final approval.", "sdd-templates/tools/stride-lint {feature}"),
            ("WARN", "HITL checkpoint: request Final approval in `APPROVAL.md`.", ""),
        ],
    },
}
```

**`LITE_WORKFLOW` の変更（2フェーズ）:**

```python
LITE_WORKFLOW: dict[int, dict[str, object]] = {
    1: {
        "phase_name": "Design & Flow",
        "steps": [
            ("PASS", "Update `basic_design.md` and `process.bpmn`.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase design"),
            ("WARN", "HITL checkpoint: request Gate A approval in `APPROVAL.md`.", ""),
        ],
    },
    2: {
        "phase_name": "Spec & Plan",
        "steps": [
            ("PASS", "Update `spec.md`, `plan.md`, `contracts/*`, and `tests/*` artifacts.", ""),
            ("PASS", "Run strict lint and resolve non-approval errors.", "sdd-templates/tools/stride-lint {feature}"),
            ("PASS", "Run multi-model semantic evaluation. Fix findings and re-run until PASS.", "sdd-templates/bin/stride evaluate {feature} --phase specify"),
            ("WARN", "HITL checkpoint: request Gate B approval in `APPROVAL.md`.", ""),
        ],
    },
    3: {
        "phase_name": "Implementation & Verification",
        "steps": [
            ("PASS", "Update `tasks.md` and execute implementation changes.", ""),
            ("PASS", "Run lint/tests and gather evidence artifacts.", "sdd-templates/tools/stride-lint {feature}"),
            ("WARN", "HITL checkpoint: request Gate C approval in `APPROVAL.md`.", ""),
        ],
    },
}
```

**注意:** `auto_continue_runner.py` の `_run_self_tests()` が参照しているステップ数
（`total` の期待値）が変わるため、self-test のアサーションも合わせて更新すること。
具体的には、変更前のテスト 1〜4 で `total` を検証している箇所があれば修正する。
（現行コードを読んで確認してから変更する）

---

## Step 4: `symphony/stride_bridge.py` に `evaluate()` 関数を追加する

既存の `lint()` 関数の直後に追加する:

```python
def evaluate(
    feature_path: str,
    phase: str = "design",
    allow_degraded: bool = False,
    cwd: Optional[str] = None,
) -> ToolResult:
    """Run multi-model semantic evaluator on a feature spec directory.

    Args:
        feature_path: path to the feature spec dir (e.g. "specs/my-feature")
        phase: evaluation phase — "design", "specify", or "tasking"
        allow_degraded: if True, API errors produce WARN (exit 0) instead of ERROR (exit 2).
                        Default False — evaluator is a hard gate.
        cwd: working directory for the subprocess
    """
    cmd = [
        "sdd-templates/bin/stride", "evaluate",
        feature_path,
        "--phase", phase,
    ]
    if allow_degraded:
        cmd.append("--allow-provider-degraded")
    return _run(cmd, cwd=cwd)


def is_evaluation_passed(result: ToolResult) -> bool:
    """Check if the evaluator returned PASS or WARN (both treated as non-blocking)."""
    return result.exit_code == 0


def is_evaluation_failed(result: ToolResult) -> bool:
    """Check if the evaluator returned FAIL (semantic issues found, rework needed)."""
    return result.exit_code == 1
```

---

## Step 5: 依存を optional extras に分離する

**`sdd-templates/requirements.txt`（既存・最小構成を維持）:**
```
PyYAML>=6.0
Jinja2>=3.1
```
（変更しない）

**`sdd-templates/requirements-ai-eval.txt`（新規作成）:**
```
# Optional: Multi-Model Evaluator dependencies
# Install: pip install -r sdd-templates/requirements-ai-eval.txt
openai>=1.0
google-genai>=1.0
google-cloud-aiplatform>=1.60
```

**`agent_docs/commands.md` の preconditions セクション末尾に追記する:**
```markdown
### Optional: Multi-Model Evaluator
- INSTALL_AI_EVAL: `pip install -r sdd-templates/requirements-ai-eval.txt`
  - Required for: `stride evaluate` command
  - Only needed if multi-model evaluation is enabled (`.env.local` configured)
```

---

## Step 6: `agent_docs/commands.md` に STRIDE_EVALUATE を追記する

既存の `STRIDE_LINT` の直後に追加する:

```markdown
### Multi-Model Semantic Evaluator
- STRIDE_EVALUATE: `sdd-templates/bin/stride evaluate specs/<feature>/ --phase <design|specify|tasking>`
  - stride lint PASS 後に呼び出す。LLM が意味的な穴（業務リスク・ERP統合盲点・ACテスタビリティ・SoD曖昧さ）を評価する
  - FAIL の場合は差し戻し（exit 1）。Generator が成果物を修正して再実行する
  - 評価レポート JSON: `specs/<feature>/state/evaluator_latest.json`（正本）
  - 評価レポート MD: `specs/<feature>/state/eval_report_<phase>_<timestamp>.md`（履歴）
  - 終了コード: 0=PASS/WARN, 1=FAIL, 2=PROVIDER_ERROR（--allow-provider-degraded 未指定時）
  - API 障害時は --allow-provider-degraded を付けると WARN で続行（exit 0）
```

---

## Step 7: テスト

### 7-1. ユニットテスト — 2ファイル構成

**core ロジックのテスト:** `symphony/tests/test_evaluator_core.py`（通常の `pytest` でカバー）

`pyproject.toml` の `testpaths = ["symphony/tests"]` に含まれるため、
`python3 -m pytest` のデフォルト実行で自動的に拾われる。
API 呼び出しは一切行わない（モックのみ）。

テスト対象の関数を直接インポートしてテストすること。
`unittest.mock.patch` で API 呼び出しをモック化すること。

```python
import sys
from pathlib import Path
# sdd-templates/tools/ を import パスに追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "sdd-templates" / "tools"))
from multi_model_evaluator import (
    load_env_local, extract_canonical_yaml, build_compact_packet,
    aggregate_results, parse_model_response, build_design_prompt,
    build_specify_prompt, build_tasking_prompt, should_skip_evaluation,
    is_hard_fail,
)

# 必須 13 件
# 1. load_env_local(): .env.local からモデル設定が環境変数に読み込まれること
# 2. load_env_local(): .env.local が存在しない場合にエラーが出ないこと
# 3. extract_canonical_yaml(): marker が存在するファイルで YAML ブロックが抽出されること
# 4. extract_canonical_yaml(): marker が存在しないファイルで None が返ること
# 5. build_compact_packet(): design フェーズで basic_design canonical yaml が含まれること
# 6. build_compact_packet(): specify フェーズで spec + plan canonical yaml + scenario index + contracts list が含まれること
# 7. build_compact_packet(): tasking フェーズで tasks canonical yaml + plan coverage + AC-task map が含まれること
# 8. aggregate_results(): primary PASS (score>=80, all criteria>=50) → exit_code=0, overall="PASS"
# 9. aggregate_results(): primary FAIL (score<60, critical あり) → exit_code=1（secondary 無関係）
# 10. aggregate_results(): primary 閾値近傍 (score=75) + secondary PASS → exit_code=0, overall="WARN"（仕様: 境界域+secondary PASS = WARN）
# 11. aggregate_results(): primary weighted_score=75 だが criterion 1つが 45 → exit_code=1（hard floor 違反、tie-break しない）
# 12. should_skip_evaluation(): coverage_tier=starter → True（スキップ）
# 13. should_skip_evaluation(): coverage_tier=critical → False（実行する）
```

**stride_bridge の evaluate() テスト:** `symphony/tests/test_stride_bridge_evaluate.py`（同様に default pytest でカバー）

```python
# 必須 3 件
# 1. evaluate(): exit_code=0 の ToolResult が返ると is_evaluation_passed() が True
# 2. evaluate(): exit_code=1 の ToolResult が返ると is_evaluation_failed() が True
# 3. evaluate(): allow_degraded=True のとき --allow-provider-degraded がコマンドに含まれること
#    （subprocess.run を mock.patch して cmd リストを検証する）
```

**補助: self-test（API 実呼び出しを含む動作確認用）:** `sdd-templates/tools/test_multi_model_evaluator.py`

```python
# python3 sdd-templates/tools/test_multi_model_evaluator.py --test で実行
# CI には含めない（API キーが必要なため）
# 実際の API を呼んで specs/FEAT-ERPSAMPLE/ の評価が通ることを確認する
```

### 7-2. `auto_continue_runner.py` の既存 self-test を壊していないか確認する

```bash
python3 sdd-templates/tools/auto_continue_runner.py --test
# 全 4 テストが PASS すること
# ステップ数が変わった場合は auto_continue_runner.py の self-test も更新済みであること
```

### 7-3. 実際に `specs/FEAT-ERPSAMPLE/` で動作確認する

```bash
# API 呼び出しを行う（.env.local の設定が必要）
python3 sdd-templates/tools/multi_model_evaluator.py specs/FEAT-ERPSAMPLE/ --phase design
# 期待: 終了コード 0 または 1
# 期待: specs/FEAT-ERPSAMPLE/state/evaluator_latest.json が生成される
# 期待: specs/FEAT-ERPSAMPLE/state/eval_report_design_*.md が生成される

# stride subcommand 経由でも動作すること
sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --phase design --allow-provider-degraded
```

### 7-4. symphony/stride_bridge.py の新関数をユニットテストする

既存の `symphony/tests/` に `test_stride_bridge_evaluate.py` を追加する
（既存テストと同じ `pytest` 実行でカバーされるようにすること）。

```python
# 必須 3 件
# 1. evaluate(): exit_code=0 の ToolResult が返ると is_evaluation_passed() が True になること
# 2. evaluate(): exit_code=1 の ToolResult が返ると is_evaluation_failed() が True になること
# 3. evaluate(): allow_degraded=True のとき --allow-provider-degraded がコマンドに含まれること
#    （subprocess の cmd リストを mock で確認する）
```

### 7-5. 既存テストに影響がないことを確認する

```bash
python3 -m pytest symphony/tests/ -v
# 全件 PASS すること
```

---

## Step 8: 検証チェックリスト

```
□ stride evaluate specs/<feature>/ --phase design が動作する（stride subcommand 経由）
□ python3 sdd-templates/tools/multi_model_evaluator.py --help が出る
□ OPENAI_API_KEY が空の場合に明確なエラーメッセージ（exit 2）が出る
□ OPENAI_MODEL / OPENAI_REASONING_EFFORT / GEMINI_MODEL / GEMINI_THINKING_BUDGET が .env.local から読まれること
  （実際の API リクエストを --format json で確認: evaluator_model フィールドが正しいモデル名であること）
□ FAIL 判定時に exit_code=1 が返る（echo $? で確認）
□ PASS 判定時に exit_code=0 が返る
□ --allow-provider-degraded なしで API 障害が起きた場合に exit_code=2 が返る
□ specs/<feature>/state/evaluator_latest.json が生成・上書きされる
□ specs/<feature>/state/eval_report_<phase>_*.md が生成される（履歴）
□ auto_continue_runner.py の FULL_WORKFLOW phase 1-3 に evaluate ステップが含まれる
□ auto_continue_runner.py --test が全 4 件 PASS する
□ symphony/stride_bridge.py に evaluate(), is_evaluation_passed(), is_evaluation_failed() が存在する
□ sdd-templates/bin/stride evaluate が case ディスパッチャーに登録されている
□ agent_docs/commands.md に STRIDE_EVALUATE が追記されている
□ sdd-templates/requirements-ai-eval.txt が存在する（core requirements.txt は変更されていない）
□ criterion score < 50 の場合に weighted_score が 70 以上でも FAIL になること（hard floor）
□ coverage_tier=starter の feature で evaluator がスキップされること（exit 0 + SKIP メッセージ）
□ --force を付けると coverage_tier=starter でもスキップされないこと
□ eval_calibration/ ディレクトリが存在し、golden_sets/design_pass_01.yaml が存在すること
□ --calibrate を渡すと NotImplementedError で exit 2 になること
□ symphony/tests/test_evaluator_core.py 13 件が PASS する（`python3 -m pytest symphony/tests/test_evaluator_core.py -v`）
□ symphony/tests/test_stride_bridge_evaluate.py 3 件が PASS する
□ python3 -m pytest symphony/tests/ -v が全件 PASS する（既存テスト + 新規 16 件すべて含む）
□ `--lite-mode` / `--enterprise` を渡すとエラーで拒否されること（黙って無視しない）
□ OPENAI_MODEL が空の場合に CONFIG_ERROR (exit 2) + 明確なメッセージが出ること
```

---

## 完了したら

openclaw system event --text "Done: stride evaluate サブコマンド実装完了（multi-model evaluator + 実行経路配線）" --mode now

---

## 制約・注意事項

- **APPROVAL.md を編集してはならない**
- **`stride_lint.py` を変更してはならない**（evaluator は lint の補完であり代替ではない）
- **評価 rubric に lint と重複する観点を含めてはならない**（ID・カウント整合は lint の責務）
- **`sdd-templates/requirements.txt` を変更してはならない**（requirements-ai-eval.txt に分離）
- **compact packet は Canonical YAML ブロックのみ**（全文投入禁止）
- `.env.local` はコミットしない（.gitignore 済み）
- `import stride_lint` は禁止（`extract_canonical_yaml` は独立実装）
- GCP 認証は ADC（`~/.config/gcloud/application_default_credentials.json`）を使う（設定済み）

---

## Evaluator Calibration（今回のスコープ: 骨格のみ）

### ディレクトリ構造

`eval_calibration/` を新規作成する:

```
eval_calibration/
├── README.md                          # calibration 運用ガイド
├── golden_sets/
│   ├── design_pass_01.yaml            # 人間が承認した good example
│   ├── design_fail_01.yaml            # 人間が差し戻した bad example
│   ├── specify_pass_01.yaml
│   └── specify_fail_01.yaml
└── calibration_results/
    └── .gitkeep                       # --calibrate 実行結果の保存先
```

### Golden Set のフォーマット

```yaml
# eval_calibration/golden_sets/design_pass_01.yaml
meta:
  feature_id: "FEAT-ERPSAMPLE"
  phase: "design"
  human_judgment: "PASS"               # 人間の最終判定
  human_notes: "承認済み。SoD/監査要件は十分。"
  approved_by: "tanaka"
  approved_at: "2026-02-10"
compact_packet: |
  # ここに extract_canonical_yaml() の出力をそのまま貼る
  basic_design:
    epic_ref: "EPIC-SAMPLE"
    ...
```

### `--calibrate` スタブ（今回は CLI とディレクトリのみ。ロジックは将来実装）

```bash
stride evaluate --calibrate eval_calibration/golden_sets/
```

実行すると:
1. `golden_sets/` の各 YAML を読み込む
2. 各 golden set に対して evaluator を実行
3. evaluator の判定と `human_judgment` を比較
4. precision / recall / F1 を計算して `calibration_results/calibration_<timestamp>.json` に保存
5. 結果をテーブルで stdout に表示

**今回の実装範囲:**
- `eval_calibration/` ディレクトリの作成
- `README.md` に上記のフォーマットと運用ガイドを記述
- `golden_sets/` に FEAT-ERPSAMPLE の design_pass_01.yaml を1件作成（specs/FEAT-ERPSAMPLE/ から extract して human_judgment: PASS）
- `multi_model_evaluator.py` に `--calibrate` 引数を受け付ける argparse 定義のみ追加（呼ばれたら `NotImplementedError: calibration loop is not yet implemented` で exit 2）

**将来の実装（backlog）:**
- calibration ループのフル実装
- precision/recall が目標を下回った場合に rubric の prompt を自動調整する仕組み
- CI で golden set に対する回帰テストを実行

---

## 将来の拡張（backlog — 今回のスコープ外）

### 1. Execute/Final 向け Runtime QA Evaluator（P1 — 最優先）

Anthropic 記事の「いちばん効いている部分」は、仕様評価ではなく **実行中アプリに対する QA evaluator**。
`stride evaluate --phase execute` として以下を追加する:

```
stride evaluate --phase execute specs/<feature>/ --run-dir <RUN_DIR>
```

**設計方針:**
- Playwright で実アプリ（UI/API）を操作し、spec の AC を自動検証する
- DB state を直接チェックして、監査ログの完全性や SoD 違反を検出する
- `evaluator_latest.json` と同じ出力フォーマットで結果を返す
- Final Gate 前に配線する（`FULL_WORKFLOW` の Execute フェーズに挿入）

**必要なもの:**
- `playwright` 依存の追加（`requirements-ai-eval.txt`）
- テスト対象アプリの URL / DB 接続情報の設定（`.env.local`）
- `scenarios.yaml` の各シナリオを Playwright テストに変換するアダプター
- `multi_model_evaluator.py` とは別ファイル（`runtime_qa_evaluator.py`）として実装

### 2. Calibration Loop のフル実装

- `--calibrate` で golden set に対する precision/recall/F1 を計算
- 目標: precision >= 0.85, recall >= 0.90
- golden set は承認済み/差し戻し済みの feature から自動生成するスクリプト
- rubric の prompt tuning 結果をバージョン管理する

### 3. Generator-Evaluator Contract（WI/Execute レベル）

- WI 実行前に「この WI の done 定義」を evaluator と共有するステップ
- `wi_readiness_checker.py` の出力を evaluator の入力に含める
- WI 完了後に「done 定義を満たしたか」を evaluator が判定する

### 4. 適応的 Evaluator 呼び出し

- 現在は `coverage_tier != starter` なら常時呼び出す設計
- 将来は「model 能力境界を超えるときだけ evaluator を呼ぶ」適応型に進化させる
- 例: lint のスコアが十分高い（エラーゼロ + 全 gate_check 数値が閾値の 2 倍以上）なら evaluator をスキップ
- Anthropic 記事の「model が強くなると evaluator の価値境界が動く」を反映
