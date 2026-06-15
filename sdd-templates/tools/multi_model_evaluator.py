#!/usr/bin/env python3
"""
Multi-Model Semantic Evaluator for SDD artifacts.

Evaluates feature specs using LLM models to detect semantic gaps that
static linting cannot find: business risk, ERP blind spots, AC testability,
SoD/audit ambiguity.

Usage:
    python3 multi_model_evaluator.py specs/<feature>/ \\
        [--phase design|specify|tasking] \\
        [--format text|json] \\
        [--allow-provider-degraded] \\
        [--force] \\
        [--calibrate <golden_sets_dir>]

Exit codes:
    0: PASS (all primary models PASS, or --allow-provider-degraded)
    1: FAIL (primary model FAIL)
    2: PROVIDER_ERROR (API error without --allow-provider-degraded) / CONFIG_ERROR
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PREAMBLE = """\
You are a strict SDD quality evaluator for ERP integration projects.
Find semantic gaps that static linting CANNOT detect.
Do NOT comment on: ID formatting, field counts, YAML structure, APPROVAL status — stride-lint handles those.
Be skeptical. Be thorough.
Every critical_issue MUST reference a specific artifact field, AC ID, scenario ID, or task ID.
Input format: Canonical YAML blocks only (SSoT extracts)."""

RESPONSE_FORMAT = """\
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
  - any individual criterion score < 50 (hard floor per criterion — prevents a weak axis from being hidden by strong ones)"""

DESIGN_RUBRIC = """\
Evaluate the DESIGN phase artifacts for feature [{FEATURE_ID}].

{COMPACT_PACKET}

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
- Are there open_questions or assumptions that should be tracked but are embedded in prose?"""

SPECIFY_RUBRIC = """\
Evaluate the SPECIFY phase artifacts for feature [{FEATURE_ID}].

{COMPACT_PACKET}

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
- Are data retention and deletion policies defined with concrete durations and trigger conditions?"""

TASKING_RUBRIC = """\
Evaluate the TASKING phase artifacts for feature [{FEATURE_ID}].

{COMPACT_PACKET}

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
- Is the total task count proportional to the spec complexity?"""

DISCOVERY_RUBRIC = """\
Evaluate the DISCOVERY phase artifacts for feature [{FEATURE_ID}].

{COMPACT_PACKET}

## Evaluation Criteria (BABOK BACCM 6 axes + iteration loop)

### D1. BACCM Completeness (weight: 50%)
- Change: Is the from_state→to_state transition explicitly described in value_canvas / change_strategy?
- Need: Is the problem_statement vs opportunity_statement distinguishable in business_need?
- Solution: Does goal_tree.root_goal align with change_strategy.solution_scope?
- Stakeholder: Are at least 3 stakeholders identified with influence/interest analysis in stakeholder_map?
- Value: Is potential_value vs anti_value (negative impact) acknowledged in value_canvas?
- Context: Are internal_context and external_context both addressed in context_map?

### D2. Iteration Progress (weight: 30%, BABOK + 4-layer Requirements Architecture inspired)
- Iteration 1 (bootstrap): Coverage > Precision (brainstorming, mind-mapping outputs)
- Iteration 2 (structure): Dependency-aware integration (functional decomposition)
- Iteration 3 (refinement): Conditions, variations, state details (business_rules_analysis)
- Is the artifact set consistent with the declared iteration?

### D3. Phase 1 Readiness (weight: 20%)
- Are blocking_questions resolved before Phase 1 Design start?
- Is the Phase 0 → Phase 1 handoff (basic_design.md draft) traceable from the BACCM artifacts?
- Be skeptical. Find semantic gaps that BACCM 6-axis lint cannot catch."""

DESIGN_SCORE_KEYS = ["business_risk_erp", "ac_testability", "integration_architecture", "scope_defensibility"]
SPECIFY_SCORE_KEYS = ["cross_artifact_consistency", "nfr_feasibility", "test_scenario_quality", "audit_compliance"]
DISCOVERY_SCORE_KEYS = ["baccm_completeness", "iteration_progress", "phase1_readiness"]
TASKING_SCORE_KEYS = ["implementation_risk", "coverage_completeness", "estimation_realism"]


# ---------------------------------------------------------------------------
# .env.local loader
# ---------------------------------------------------------------------------

def load_env_local(project_root: Path) -> None:
    """Load environment variables from .env.local (no python-dotenv dependency)."""
    env_path = project_root / ".env.local"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if v:  # empty values do not override
                    os.environ.setdefault(k, v)


# ---------------------------------------------------------------------------
# Canonical YAML extraction (delegated to stride_shared_lib)
# ---------------------------------------------------------------------------

from stride_shared_lib import extract_yaml_after_marker as _extract_yaml_after_marker


def _canonical_yaml_text(filepath: Path, marker: str) -> Optional[str]:
    """Canonical YAML block body (raw text) extracted from a spec file.

    Returns the raw YAML body because build_compact_packet embeds it verbatim
    inside fenced ```yaml``` sections in the prompt — parsing is deferred to
    the caller only when structured access is needed.
    """
    if not filepath.exists():
        return None
    return _extract_yaml_after_marker(filepath.read_text(encoding="utf-8"), marker)


# Backward-compat public alias (pre-v5.1 tune-up callers — e.g. symphony/tests/test_evaluator_core.py)
extract_canonical_yaml = _canonical_yaml_text


def extract_bpmn_summary(bpmn_path: Path) -> Optional[str]:
    """Extract process element names from BPMN XML (tasks, gateways only)."""
    if not bpmn_path.exists():
        return None
    try:
        tree = ET.parse(bpmn_path)
        root = tree.getroot()
    except ET.ParseError:
        return None

    ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
    elements = []
    tag_types = [
        "bpmn:task", "bpmn:userTask", "bpmn:serviceTask",
        "bpmn:sendTask", "bpmn:receiveTask", "bpmn:scriptTask",
        "bpmn:exclusiveGateway", "bpmn:parallelGateway",
        "bpmn:inclusiveGateway", "bpmn:eventBasedGateway",
    ]
    for tag in tag_types:
        for elem in root.iter(tag.replace("bpmn:", f"{{{ns['bpmn']}}}")):
            name = elem.get("name", elem.get("id", "unnamed"))
            elements.append(f"- {tag.split(':')[1]}: {name}")

    if not elements:
        # Fallback: try without namespace prefix
        for elem in root.iter():
            local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local in ("task", "userTask", "serviceTask", "sendTask",
                         "receiveTask", "scriptTask", "exclusiveGateway",
                         "parallelGateway", "inclusiveGateway", "eventBasedGateway"):
                name = elem.get("name", elem.get("id", "unnamed"))
                elements.append(f"- {local}: {name}")

    return "\n".join(elements) if elements else None


# ---------------------------------------------------------------------------
# Compact Packet builders
# ---------------------------------------------------------------------------

def build_compact_packet(feature_dir: Path, phase: str) -> str:
    """Build a compact evaluation packet from canonical YAML blocks."""
    parts: list[str] = []

    if phase == "design":
        bd_yaml = _canonical_yaml_text(feature_dir / "basic_design.md", "Canonical Basic Design")
        if bd_yaml:
            parts.append("## basic_design (Canonical YAML)\n```yaml\n" + bd_yaml + "\n```")
        bpmn = extract_bpmn_summary(feature_dir / "process.bpmn")
        if bpmn:
            parts.append("## BPMN Process Summary\n" + bpmn)

    elif phase == "specify":
        spec_yaml = _canonical_yaml_text(feature_dir / "spec.md", "Canonical Spec")
        if spec_yaml:
            parts.append("## spec (Canonical YAML)\n```yaml\n" + spec_yaml + "\n```")
        plan_yaml = _canonical_yaml_text(feature_dir / "plan.md", "Canonical Plan")
        if plan_yaml:
            parts.append("## plan (Canonical YAML)\n```yaml\n" + plan_yaml + "\n```")
        scenarios_path = feature_dir / "tests" / "scenarios.yaml"
        if scenarios_path.exists():
            scenarios_text = scenarios_path.read_text(encoding="utf-8")
            parts.append("## scenarios.yaml\n```yaml\n" + scenarios_text + "\n```")
        contracts_dir = feature_dir / "contracts"
        if contracts_dir.exists():
            files = sorted(p.name for p in contracts_dir.glob("*.yaml"))
            if files:
                parts.append("## contracts/ files\n" + "\n".join(f"- {f}" for f in files))

    elif phase == "discovery":
        # v5.5 Phase B: Discovery phase = BACCM 6 axes + 50 technique + iteration progress
        upstream_dir = feature_dir / "upstream"
        if upstream_dir.is_dir():
            for phase_subdir in sorted(upstream_dir.iterdir()):
                if not phase_subdir.is_dir():
                    continue
                yaml_files = sorted(phase_subdir.glob("*.yaml"))
                for yf in yaml_files:
                    try:
                        text = yf.read_text(encoding="utf-8")
                        parts.append(
                            f"## upstream/{phase_subdir.name}/{yf.name}\n```yaml\n{text}\n```"
                        )
                    except OSError:
                        continue
        # Include BACCM completeness summary if checker is importable
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from baccm_completeness_checker import check_baccm_completeness
            baccm = check_baccm_completeness(feature_dir)
            parts.append(
                "## BACCM Completeness Summary\n"
                f"- overall_pass: {baccm['overall_pass']}\n"
                f"- score: {baccm['score']}%\n"
                + "\n".join(
                    f"- {axis}: {'PASS' if data['pass'] else 'FAIL'}"
                    for axis, data in baccm["axes"].items()
                )
            )
        except (ImportError, FileNotFoundError, RuntimeError, ValueError):
            pass

    elif phase == "tasking":
        tasks_yaml = _canonical_yaml_text(feature_dir / "tasks.md", "Canonical Tasks")
        if tasks_yaml:
            parts.append("## tasks (Canonical YAML)\n```yaml\n" + tasks_yaml + "\n```")
        # Extract coverage_policy + tests[] from plan
        plan_yaml_text = _canonical_yaml_text(feature_dir / "plan.md", "Canonical Plan")
        if plan_yaml_text and yaml:
            try:
                plan_data = yaml.safe_load(plan_yaml_text)
                plan_root = plan_data.get("plan", plan_data) if isinstance(plan_data, dict) else {}
                # Support both flat (plan.coverage_policy) and nested (plan.test_strategy.coverage_policy)
                test_strategy = plan_root.get("test_strategy", {}) if isinstance(plan_root, dict) else {}
                coverage = test_strategy.get("coverage_policy") or plan_root.get("coverage_policy")
                tests = test_strategy.get("tests") or plan_root.get("tests")
                subset = {}
                if coverage:
                    subset["coverage_policy"] = coverage
                if tests:
                    subset["tests"] = tests
                if subset:
                    parts.append("## plan coverage summary\n```yaml\n" + yaml.dump(subset, default_flow_style=False, allow_unicode=True) + "```")
            except Exception:
                pass
        # AC→task coverage map
        if tasks_yaml and yaml:
            try:
                tasks_data = yaml.safe_load(tasks_yaml)
                tasks_root = tasks_data.get("tasks", tasks_data) if isinstance(tasks_data, dict) else {}
                # Support both tasks.tasks (real) and tasks.task_list (legacy)
                task_list = (tasks_root.get("tasks") or tasks_root.get("task_list") or []) if isinstance(tasks_root, dict) else []
                ac_map: dict[str, list[str]] = {}
                for task in task_list:
                    if not isinstance(task, dict):
                        continue
                    tid = task.get("id", "?")
                    refs = task.get("spec_refs", [])
                    if isinstance(refs, str):
                        refs = [refs]
                    for ref in refs:
                        # Extract AC IDs like AC-US-FEAT...-001-01
                        acs = re.findall(r"AC-[A-Z0-9-]+", str(ref))
                        for ac in acs:
                            ac_map.setdefault(ac, []).append(tid)
                if ac_map:
                    lines = ["## AC → Task Coverage Map"]
                    for ac, tids in sorted(ac_map.items()):
                        lines.append(f"- {ac}: {', '.join(tids)}")
                    parts.append("\n".join(lines))
            except Exception:
                pass

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _feature_id_from_dir(feature_dir: Path) -> str:
    """Extract feature ID from directory name."""
    return feature_dir.name.rstrip("/")


def build_design_prompt(feature_dir: Path) -> str:
    fid = _feature_id_from_dir(feature_dir)
    packet = build_compact_packet(feature_dir, "design")
    body = DESIGN_RUBRIC.replace("{FEATURE_ID}", fid).replace("{COMPACT_PACKET}", packet)
    return f"{PREAMBLE}\n\n{body}\n\n{RESPONSE_FORMAT}"


def build_specify_prompt(feature_dir: Path) -> str:
    fid = _feature_id_from_dir(feature_dir)
    packet = build_compact_packet(feature_dir, "specify")
    body = SPECIFY_RUBRIC.replace("{FEATURE_ID}", fid).replace("{COMPACT_PACKET}", packet)
    return f"{PREAMBLE}\n\n{body}\n\n{RESPONSE_FORMAT}"


def build_tasking_prompt(feature_dir: Path) -> str:
    fid = _feature_id_from_dir(feature_dir)
    packet = build_compact_packet(feature_dir, "tasking")
    body = TASKING_RUBRIC.replace("{FEATURE_ID}", fid).replace("{COMPACT_PACKET}", packet)
    return f"{PREAMBLE}\n\n{body}\n\n{RESPONSE_FORMAT}"


def build_discovery_prompt(feature_dir: Path) -> str:
    """v5.5 Phase B: Discovery phase prompt builder (BACCM 6 axes + iteration loop)."""
    fid = _feature_id_from_dir(feature_dir)
    packet = build_compact_packet(feature_dir, "discovery")
    body = DISCOVERY_RUBRIC.replace("{FEATURE_ID}", fid).replace("{COMPACT_PACKET}", packet)
    return f"{PREAMBLE}\n\n{body}\n\n{RESPONSE_FORMAT}"


# ---------------------------------------------------------------------------
# Coverage tier skip logic
# ---------------------------------------------------------------------------

def should_skip_evaluation(feature_dir: Path) -> bool:
    """coverage_tier=starter features skip evaluator (cost optimization)."""
    bd_path = feature_dir / "basic_design.md"
    if not bd_path.exists():
        return False
    yaml_text = _canonical_yaml_text(bd_path, "Canonical Basic Design")
    if not yaml_text:
        return False
    if yaml is None:
        return False
    try:
        data = yaml.safe_load(yaml_text)
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    tier = data.get("basic_design", {}).get("coverage_tier", "standard")
    return tier == "starter"


# ---------------------------------------------------------------------------
# Model callers
# ---------------------------------------------------------------------------

def _call_openai(prompt: str) -> dict[str, Any]:
    """Call OpenAI API. Returns parsed JSON or error dict."""
    api_key = os.environ.get("OPENAI_API_KEY", "")
    model = os.environ.get("OPENAI_MODEL", "")
    reasoning_effort = os.environ.get("OPENAI_REASONING_EFFORT", "xhigh")

    if not api_key:
        return {"error": "OPENAI_API_KEY is not set"}
    if not model:
        return {"error": "OPENAI_MODEL is not set"}

    try:
        import openai
    except ImportError:
        return {"error": "openai package not installed. Run: pip install -r sdd-templates/requirements-ai-eval.txt"}

    client = openai.OpenAI(api_key=api_key)

    for attempt in range(2):
        try:
            # Use Responses API for reasoning models (o-series), chat completions for others
            if model.startswith("o") or "reasoning" in model.lower():
                response = client.responses.create(
                    model=model,
                    reasoning={"effort": reasoning_effort},
                    input=[{"role": "user", "content": prompt}],
                    max_output_tokens=4000,
                )
                content = response.output_text
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_completion_tokens=4000,
                    temperature=0.1,
                )
                content = response.choices[0].message.content
            return parse_model_response(content, model)
        except Exception as exc:
            if attempt == 0:
                print(f"WARNING: OpenAI API attempt 1 failed: {exc}. Retrying in 5s...", file=sys.stderr)
                time.sleep(5)
            else:
                return {"error": f"OpenAI API failed after 2 attempts: {exc}"}

    return {"error": "OpenAI API failed unexpectedly"}


def _call_gemini(prompt: str) -> Optional[dict[str, Any]]:
    """Call Gemini API. Returns parsed JSON, error dict, or None if disabled."""
    model_name = os.environ.get("GEMINI_MODEL", "")
    if not model_name:
        return None  # Secondary disabled

    thinking_budget = int(os.environ.get("GEMINI_THINKING_BUDGET", "-1"))
    api_key = os.environ.get("GEMINI_API_KEY", "")

    for attempt in range(2):
        try:
            if api_key:
                # AI Studio path
                from google import genai as google_genai
                from google.genai import types as genai_types

                gclient = google_genai.Client(api_key=api_key)
                config = genai_types.GenerateContentConfig(
                    thinking_config=genai_types.ThinkingConfig(thinking_budget=thinking_budget)
                )
                response = gclient.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                content = response.text
            else:
                # Vertex AI path (ADC auth)
                import vertexai
                from vertexai.generative_models import GenerativeModel

                project = os.environ.get("VERTEX_AI_PROJECT", "tecnos-cbp")
                location = os.environ.get("VERTEX_AI_LOCATION", "us-central1")
                vertexai.init(project=project, location=location)
                gen_model = GenerativeModel(model_name)
                response = gen_model.generate_content(
                    prompt,
                    generation_config={"thinking_config": {"thinking_budget": thinking_budget}},
                )
                content = response.text

            return parse_model_response(content, model_name)
        except Exception as exc:
            if attempt == 0:
                print(f"WARNING: Gemini API attempt 1 failed: {exc}. Retrying in 5s...", file=sys.stderr)
                time.sleep(5)
            else:
                return {"error": f"Gemini API failed after 2 attempts: {exc}"}

    return {"error": "Gemini API failed unexpectedly"}


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_model_response(content: str, model_name: str) -> dict[str, Any]:
    """Parse JSON from model response text. Returns error dict on failure."""
    if not content:
        return {"error": "Empty response from model", "evaluator_model": model_name}

    # Try to extract JSON from response (may have markdown fences)
    json_match = re.search(r"\{[\s\S]*\}", content)
    if not json_match:
        return {"error": f"No JSON found in response: {content[:200]}", "evaluator_model": model_name}

    try:
        result = json.loads(json_match.group())
        result["evaluator_model"] = model_name
        return result
    except json.JSONDecodeError as exc:
        return {"error": f"JSON parse failed: {exc}", "evaluator_model": model_name}


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def is_hard_fail(result: dict) -> bool:
    """Check if any individual criterion score is below the hard floor (50)."""
    return any(score < 50 for score in result.get("scores", {}).values())


def aggregate_results(
    openai_result: dict[str, Any],
    gemini_result: Optional[dict[str, Any]],
    allow_degraded: bool = False,
) -> dict[str, Any]:
    """Aggregate primary (OpenAI) + optional secondary (Gemini) results.

    FAIL conditions (3 OR):
      1. weighted_score < 70
      2. critical_issues with severity="critical"
      3. any criterion score < 50 (hard floor)

    Primary: OpenAI decides.
    Tie-breaker: Primary FAIL + weighted_score 60-79 + no hard floor violation →
                 if Gemini PASS → WARN, else → FAIL.
    Clear FAIL: weighted_score < 60 or 2+ critical or hard floor → FAIL (no tie-break).
    """
    primary_error = "error" in openai_result
    secondary_error = gemini_result is not None and "error" in gemini_result
    secondary_disabled = gemini_result is None

    # --- Error handling ---
    if primary_error:
        if allow_degraded:
            return {
                "overall": "WARN",
                "exit_code": 0,
                "reason": f"Primary API error (degraded mode): {openai_result.get('error')}",
                "primary": openai_result,
                "secondary": gemini_result,
            }
        else:
            return {
                "overall": "PROVIDER_ERROR",
                "exit_code": 2,
                "reason": f"Primary API error: {openai_result.get('error')}",
                "primary": openai_result,
                "secondary": gemini_result,
            }

    # Primary succeeded — evaluate
    p_score = openai_result.get("weighted_score", 0)
    p_criticals = [i for i in openai_result.get("critical_issues", [])
                   if i.get("severity") == "critical"]
    p_hard_floor = is_hard_fail(openai_result)
    p_overall = openai_result.get("overall", "FAIL")

    # Determine primary FAIL
    p_fail = (
        p_score < 70
        or len(p_criticals) > 0
        or p_hard_floor
        or p_overall == "FAIL"
    )

    if not p_fail:
        # Primary PASS
        result = {
            "overall": "PASS",
            "exit_code": 0,
            "reason": f"Primary PASS (score={p_score:.1f})",
            "primary": openai_result,
            "secondary": gemini_result,
        }
        if secondary_error:
            result["reason"] += " (secondary API error — ignored)"
        return result

    # Primary FAIL — check for tie-break eligibility
    clear_fail = (
        p_score < 60
        or len(p_criticals) >= 2
        or p_hard_floor
    )

    if clear_fail:
        reason_parts = []
        if p_score < 60:
            reason_parts.append(f"score={p_score:.1f}<60")
        if len(p_criticals) >= 2:
            reason_parts.append(f"{len(p_criticals)} critical issues")
        if p_hard_floor:
            low = {k: v for k, v in openai_result.get("scores", {}).items() if v < 50}
            reason_parts.append(f"hard floor violation: {low}")
        return {
            "overall": "FAIL",
            "exit_code": 1,
            "reason": f"Clear FAIL: {'; '.join(reason_parts)}",
            "primary": openai_result,
            "secondary": gemini_result,
        }

    # Borderline (60 <= p_score < 70, or single critical, no hard floor)
    # → Tie-break with secondary
    if secondary_disabled or secondary_error:
        return {
            "overall": "FAIL",
            "exit_code": 1,
            "reason": f"Borderline FAIL (score={p_score:.1f}), no secondary available for tie-break",
            "primary": openai_result,
            "secondary": gemini_result,
        }

    # Secondary available — check
    s_score = gemini_result.get("weighted_score", 0)
    s_criticals = [i for i in gemini_result.get("critical_issues", [])
                   if i.get("severity") == "critical"]
    s_hard_floor = is_hard_fail(gemini_result)
    s_overall = gemini_result.get("overall", "FAIL")
    s_fail = (
        s_score < 70
        or len(s_criticals) > 0
        or s_hard_floor
        or s_overall == "FAIL"
    )

    if s_fail:
        return {
            "overall": "FAIL",
            "exit_code": 1,
            "reason": f"Borderline FAIL (primary={p_score:.1f}, secondary={s_score:.1f} also FAIL)",
            "primary": openai_result,
            "secondary": gemini_result,
        }
    else:
        return {
            "overall": "WARN",
            "exit_code": 0,
            "reason": f"Borderline — primary FAIL ({p_score:.1f}) but secondary PASS ({s_score:.1f})",
            "primary": openai_result,
            "secondary": gemini_result,
        }


# ---------------------------------------------------------------------------
# Report output
# ---------------------------------------------------------------------------

def _ensure_state_dir(feature_dir: Path) -> Path:
    state_dir = feature_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def write_json_report(feature_dir: Path, aggregated: dict) -> Path:
    """Write evaluator_latest.json (overwrite)."""
    state_dir = _ensure_state_dir(feature_dir)
    out_path = state_dir / "evaluator_latest.json"
    out_path.write_text(json.dumps(aggregated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


def write_markdown_report(feature_dir: Path, phase: str, aggregated: dict) -> Path:
    """Write eval_report_<phase>_<timestamp>.md (append/history)."""
    state_dir = _ensure_state_dir(feature_dir)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = state_dir / f"eval_report_{phase}_{ts}.md"

    lines = [
        f"# Evaluation Report: {phase} ({ts})",
        "",
        f"**Overall:** {aggregated.get('overall', 'N/A')}",
        f"**Reason:** {aggregated.get('reason', 'N/A')}",
        "",
    ]

    primary = aggregated.get("primary", {})
    if primary and "error" not in primary:
        lines.append("## Primary Model")
        lines.append(f"- Model: {primary.get('evaluator_model', 'N/A')}")
        lines.append(f"- Weighted Score: {primary.get('weighted_score', 'N/A')}")
        scores = primary.get("scores", {})
        if scores:
            lines.append("- Scores:")
            for k, v in scores.items():
                lines.append(f"  - {k}: {v}")
        criticals = primary.get("critical_issues", [])
        if criticals:
            lines.append("- Critical Issues:")
            for issue in criticals:
                lines.append(f"  - [{issue.get('severity', '?')}] {issue.get('criterion', '?')}: "
                             f"{issue.get('description', '?')} (ref: {issue.get('ref', '?')})")
        suggestions = primary.get("suggestions", [])
        if suggestions:
            lines.append("- Suggestions:")
            for s in suggestions:
                lines.append(f"  - {s}")
        lines.append("")

    secondary = aggregated.get("secondary")
    if secondary and "error" not in secondary:
        lines.append("## Secondary Model")
        lines.append(f"- Model: {secondary.get('evaluator_model', 'N/A')}")
        lines.append(f"- Weighted Score: {secondary.get('weighted_score', 'N/A')}")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def format_text_output(aggregated: dict) -> str:
    """Format aggregated result for terminal display."""
    lines = []
    overall = aggregated.get("overall", "N/A")
    lines.append(f"Evaluator Result: {overall}")
    lines.append(f"Reason: {aggregated.get('reason', 'N/A')}")

    primary = aggregated.get("primary", {})
    if primary and "error" not in primary:
        lines.append(f"Primary Model: {primary.get('evaluator_model', 'N/A')}")
        lines.append(f"  Weighted Score: {primary.get('weighted_score', 'N/A')}")
        scores = primary.get("scores", {})
        for k, v in scores.items():
            flag = " ← HARD FLOOR" if isinstance(v, (int, float)) and v < 50 else ""
            lines.append(f"  {k}: {v}{flag}")
        criticals = primary.get("critical_issues", [])
        if criticals:
            lines.append(f"  Critical Issues ({len(criticals)}):")
            for issue in criticals:
                lines.append(f"    [{issue.get('severity')}] {issue.get('criterion')}: "
                             f"{issue.get('description')} (ref: {issue.get('ref')})")

    secondary = aggregated.get("secondary")
    if secondary:
        if "error" in secondary:
            lines.append(f"Secondary Model: ERROR — {secondary.get('error')}")
        else:
            lines.append(f"Secondary Model: {secondary.get('evaluator_model', 'N/A')}")
            lines.append(f"  Weighted Score: {secondary.get('weighted_score', 'N/A')}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-review loop
# ---------------------------------------------------------------------------

def self_review_loop(
    review_packet: dict[str, Any],
    max_iters: int = 3,
) -> dict[str, Any]:
    """Run a self-review loop for borderline primary results.

    review_packet must contain at least:
        feature_dir  (str)  — path to specs/<feature>/
        phase        (str)  — "design" | "specify" | "tasking"
        prompt       (str)  — the original evaluation prompt
        primary_result (dict) — the openai_result from _call_openai()

    Returns a dict with keys:
        issues     list[dict]  — additional issues found (each has severity, criterion, description, ref)
        iterations int         — number of review iterations performed
    """
    issues: list[dict[str, Any]] = []
    feature_dir = Path(review_packet.get("feature_dir", "."))
    phase = review_packet.get("phase", "design")
    original_prompt = review_packet.get("prompt", "")
    primary_result = review_packet.get("primary_result", {})

    # Build a focused self-review prompt asking the model to critique its own result
    critiques_json = json.dumps(primary_result.get("critical_issues", []), ensure_ascii=False, indent=2)
    suggestions_json = json.dumps(primary_result.get("suggestions", []), ensure_ascii=False, indent=2)

    review_preamble = f"""\
You are re-examining a borderline evaluation result for SDD feature {feature_dir.name} ({phase} phase).

Your previous assessment gave weighted_score={primary_result.get('weighted_score', '?')} with the following findings:

Critical issues identified:
{critiques_json}

Suggestions:
{suggestions_json}

Now, carefully re-read the original evaluation context below and determine:
1. Are there additional critical issues not yet flagged?
2. Are any flagged critical issues actually unfounded (false positives)?

{original_prompt}

## Self-Review Response Format (JSON only)
{{
  "additional_issues": [
    {{"criterion": "<key>", "description": "<finding>", "severity": "critical|major|minor", "ref": "<artifact field or ID>"}}
  ],
  "false_positives": ["<description of any prior finding that is unfounded>"],
  "confidence": "higher|same|lower"
}}
"""

    for iteration in range(1, max_iters + 1):
        result = _call_openai(review_preamble)
        if "error" in result:
            # If model call fails, stop review loop early
            break

        # Parse additional_issues from the review response
        # The response may not be in the standard eval format, so handle flexibly
        additional = result.get("additional_issues", [])
        if not additional:
            # Try top-level critical_issues if model used that key instead
            additional = result.get("critical_issues", [])

        for issue in additional:
            if isinstance(issue, dict) and issue.get("severity") == "critical":
                issues.append(issue)

        # If no new critical issues found, no need to iterate further
        confidence = result.get("confidence", "same")
        if not additional or confidence == "same":
            break

    return {"issues": issues, "iterations": max_iters}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Multi-model semantic evaluator for SDD artifacts.",
    )
    parser.add_argument("feature_dir", nargs="?", help="Path to specs/<feature>/ directory")
    parser.add_argument("--phase", choices=["design", "specify", "tasking", "discovery"], default="design",
                        help="Evaluation phase (default: design). v5.5: discovery added for BACCM 6-axis evaluation.")
    parser.add_argument("--format", dest="output_format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("--allow-provider-degraded", action="store_true",
                        help="Treat API errors as WARN (exit 0) instead of ERROR (exit 2)")
    parser.add_argument("--force", action="store_true",
                        help="Run even if coverage_tier=starter (normally skipped)")
    parser.add_argument("--review", action="store_true",
                        help="Run self-review loop for borderline primary results (score 70-85)")
    parser.add_argument("--calibrate", metavar="GOLDEN_SETS_DIR",
                        help="Run calibration against golden sets (not yet implemented)")
    parser.add_argument("--test", action="store_true", help="Run self-tests (requires API keys)")

    args = parser.parse_args()

    # Calibrate stub
    if args.calibrate:
        print("ERROR: calibration loop is not yet implemented", file=sys.stderr)
        raise SystemExit(2)

    if args.test:
        _run_self_tests()
        return

    if not args.feature_dir:
        parser.error("the following arguments are required: feature_dir")

    feature_dir = Path(args.feature_dir).resolve()
    if not feature_dir.exists() or not feature_dir.is_dir():
        print(f"ERROR: Feature directory not found: {feature_dir}", file=sys.stderr)
        sys.exit(1)

    # Find project root (parent of specs/)
    project_root = feature_dir.parent.parent if feature_dir.parent.name == "specs" else feature_dir.parent
    load_env_local(project_root)

    # Coverage tier skip — check BEFORE API key validation so starter features
    # don't need AI credentials at all (cost optimization path)
    if not args.force and should_skip_evaluation(feature_dir):
        print("SKIP: coverage_tier=starter — evaluator skipped (use --force to override)")
        sys.exit(0)

    # Check API key/model after skip check
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY is not set in .env.local", file=sys.stderr)
        sys.exit(2)
    if not os.environ.get("OPENAI_MODEL"):
        print("ERROR: OPENAI_MODEL is not set in .env.local (e.g., gpt-4.1, o3)", file=sys.stderr)
        sys.exit(2)

    # Build prompt
    phase = args.phase
    if phase == "design":
        prompt = build_design_prompt(feature_dir)
    elif phase == "specify":
        prompt = build_specify_prompt(feature_dir)
    elif phase == "tasking":
        prompt = build_tasking_prompt(feature_dir)
    elif phase == "discovery":
        prompt = build_discovery_prompt(feature_dir)
    else:
        print(f"ERROR: Unknown phase: {phase}", file=sys.stderr)
        sys.exit(1)

    # Call models
    print(f"Calling primary model ({os.environ.get('OPENAI_MODEL')})...", file=sys.stderr)
    openai_result = _call_openai(prompt)

    # Self-review loop for borderline results (70 <= score < 85, no primary error)
    primary_error = "error" in openai_result
    if args.review and not primary_error:
        p_score = openai_result.get("weighted_score", 0)
        if 70 <= p_score < 85:
            print("Running self-review loop (borderline score)...", file=sys.stderr)
            review_packet = {
                "feature_dir": str(feature_dir),
                "phase": phase,
                "prompt": prompt,
                "primary_result": openai_result,
            }
            review_result = self_review_loop(review_packet)
            # Attach review issues to primary result
            openai_result["self_review_issues"] = review_result["issues"]
            # If any review issue is critical, update primary result and force FAIL
            critical_from_review = [i for i in review_result["issues"] if i.get("severity") == "critical"]
            if critical_from_review:
                existing = openai_result.get("critical_issues", [])
                openai_result["critical_issues"] = existing + critical_from_review
                openai_result["overall"] = "FAIL"

    gemini_model = os.environ.get("GEMINI_MODEL", "")
    if gemini_model:
        print(f"Calling secondary model ({gemini_model})...", file=sys.stderr)
        gemini_result = _call_gemini(prompt)
    else:
        gemini_result = None

    # Aggregate
    aggregated = aggregate_results(openai_result, gemini_result, args.allow_provider_degraded)

    # Write reports
    json_path = write_json_report(feature_dir, aggregated)
    md_path = write_markdown_report(feature_dir, phase, aggregated)
    print(f"Reports: {json_path}, {md_path}", file=sys.stderr)

    # Output
    if args.output_format == "json":
        print(json.dumps(aggregated, indent=2, ensure_ascii=False))
    else:
        print(format_text_output(aggregated))

    sys.exit(aggregated.get("exit_code", 2))


def _run_self_tests() -> None:
    """Self-tests that exercise real API calls (requires .env.local)."""
    print("Running self-tests (API calls)...")

    project_root = Path(__file__).resolve().parent.parent.parent
    load_env_local(project_root)

    sample_dir = project_root / "specs" / "FEAT-ERPSAMPLE"
    if not sample_dir.exists():
        print(f"SKIP: {sample_dir} not found")
        sys.exit(0)

    prompt = build_design_prompt(sample_dir)
    print(f"  Prompt length: {len(prompt)} chars")

    result = _call_openai(prompt)
    if "error" in result:
        print(f"  FAIL: OpenAI error: {result['error']}")
        sys.exit(2)

    print(f"  OpenAI result: overall={result.get('overall')}, score={result.get('weighted_score')}")
    print("Self-tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
