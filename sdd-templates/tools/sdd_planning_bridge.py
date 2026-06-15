#!/usr/bin/env python3
"""
SDD Planning Bridge — §10 Run-Planning Integration (v1.0)

Bridges Planning v5.0 (~/.claude/commands/planning/) with SDD WI/Run execution.
Implements sdd_guidelines.md §10 as executable code.

Subcommands:
    init     — Create .planning/ in RUN dir with SDD context (WI info, spec_refs, knowledge)
    sync     — Sync stride-lint results into plan.md Errors table
    evidence — Generate "Planning Evidence" section for walkthrough.md
    learn    — Extract lesson candidates from Run artifacts (Errors, Decisions, findings, lint)

Usage:
    python3 sdd-templates/tools/sdd_planning_bridge.py init <feature_dir> <wi_id> [<run_dir>]
    python3 sdd-templates/tools/sdd_planning_bridge.py sync <feature_dir> [<run_dir>]
    python3 sdd-templates/tools/sdd_planning_bridge.py evidence <feature_dir> <wi_id> [<run_dir>]
    python3 sdd-templates/tools/sdd_planning_bridge.py learn <feature_dir> <wi_id> [<run_dir>] [--apply]

Exit codes:
    0 = Success
    1 = Error (missing files, parse error, etc.)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    yaml = None

from stride_shared_lib import extract_first_yaml_block


# =============================================================================
# Constants
# =============================================================================

KNOWLEDGE_DIR = Path.home() / ".claude" / "knowledge"
PLANNING_TEMPLATES = Path.home() / ".claude" / "commands" / "planning" / "templates"


# =============================================================================
# Helpers
# =============================================================================


def find_latest_run_dir(feature_dir: Path, wi_id: str) -> Optional[Path]:
    """Find the latest RUN directory for a given WI."""
    runs_dir = feature_dir / "runs" / wi_id
    if not runs_dir.exists():
        return None
    run_dirs = sorted(
        [d for d in runs_dir.iterdir() if d.is_dir() and d.name.startswith("RUN-")],
        reverse=True,
    )
    return run_dirs[0] if run_dirs else None


def parse_wi_definition(feature_dir: Path, wi_id: str) -> Dict[str, Any]:
    """Parse a Work Item definition file for context injection."""
    wi_file = feature_dir / "work_items" / f"{wi_id}.md"
    if not wi_file.exists():
        return {"id": wi_id, "title": wi_id, "spec_refs": [], "risk_flags": [], "mode": "autopilot"}

    content = wi_file.read_text(encoding="utf-8")
    result: Dict[str, Any] = {"id": wi_id, "title": wi_id, "spec_refs": [], "risk_flags": [], "mode": "autopilot"}

    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
    if title_match:
        result["title"] = title_match.group(1).strip()

    # Extract canonical YAML block (shared extractor).
    yaml_body = extract_first_yaml_block(content)
    if yaml_body is not None and yaml is not None:
        try:
            data = yaml.safe_load(yaml_body)
            if isinstance(data, dict):
                result["spec_refs"] = data.get("spec_refs", data.get("spec_links", []))
                result["risk_flags"] = data.get("risk_flags", [])
                result["mode"] = data.get("mode", "autopilot")
                result["complexity"] = data.get("complexity", "")
                result["dod"] = data.get("dod", [])
        except Exception:
            pass

    # Fallback: grep for spec_refs line
    if not result["spec_refs"]:
        refs_match = re.findall(r"(?:spec_refs|spec_links):\s*\[([^\]]+)\]", content)
        if refs_match:
            result["spec_refs"] = [r.strip().strip("\"'") for r in refs_match[0].split(",")]

    return result


def parse_feature_name(feature_dir: Path) -> str:
    """Extract feature name from directory path."""
    return feature_dir.name


def search_knowledge(tags: List[str]) -> List[Dict[str, Any]]:
    """Search global knowledge store for relevant items."""
    index_file = KNOWLEDGE_DIR / "index.json"
    if not index_file.exists():
        return []

    try:
        index = json.loads(index_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    feedback: Dict[str, Any] = {}
    feedback_file = KNOWLEDGE_DIR / "feedback.json"
    if feedback_file.exists():
        try:
            feedback = json.loads(feedback_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    results = []
    tag_set = {t.lower() for t in tags}

    for category in ["bestPractices", "troubles"]:
        for item in index.get(category, []):
            item_tags = {t.lower() for t in item.get("tags", [])}
            overlap = tag_set & item_tags
            if len(overlap) >= 1:
                # Check effectiveness
                item_id = item.get("id", "")
                fb = feedback.get(item_id, {})
                effectiveness = fb.get("effectiveness", 1.0)
                if effectiveness < 0.3 and (fb.get("helpedCount", 0) + fb.get("failedCount", 0)) >= 3:
                    continue  # Skip low-effectiveness items
                results.append({
                    "id": item_id,
                    "title": item.get("title", ""),
                    "category": category,
                    "tags": item.get("tags", []),
                    "effectiveness": effectiveness,
                    "reuse_count": item.get("reuseCount", 0),
                })

    return results


def update_reuse_count(item_ids: List[str]) -> None:
    """Increment reuse count for applied knowledge items."""
    index_file = KNOWLEDGE_DIR / "index.json"
    if not index_file.exists() or not item_ids:
        return

    try:
        index = json.loads(index_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    today = datetime.now().strftime("%Y-%m-%d")
    for category in ["bestPractices", "troubles"]:
        for item in index.get(category, []):
            if item.get("id") in item_ids:
                item["reuseCount"] = item.get("reuseCount", 0) + 1
                item["lastUsed"] = today

    index["lastUpdated"] = f"{today}T00:00:00Z"
    index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


# =============================================================================
# Subcommand: init
# =============================================================================


def cmd_init(feature_dir: Path, wi_id: str, run_dir: Optional[Path] = None) -> int:
    """Create .planning/ in RUN dir with SDD context.

    §10 mapping:
    - Step 3: RUN directory creation (assumed done by caller)
    - Step 4: /planning auto-execution with SDD context injection
    """
    # Resolve run directory
    if run_dir is None:
        run_dir = find_latest_run_dir(feature_dir, wi_id)
    if run_dir is None:
        # Create RUN dir if it doesn't exist
        runs_base = feature_dir / "runs" / wi_id
        runs_base.mkdir(parents=True, exist_ok=True)
        run_name = f"RUN-{datetime.now().strftime('%Y%m%d-%H%M')}"
        run_dir = runs_base / run_name
        run_dir.mkdir(exist_ok=True)
        print(f"Created RUN directory: {run_dir.relative_to(feature_dir.parent.parent)}")

    planning_dir = run_dir / ".planning"
    if planning_dir.exists():
        print(f"⚠ .planning/ already exists in {run_dir.name}. Use --force to overwrite.")
        return 1

    planning_dir.mkdir(exist_ok=True)

    # Parse WI context
    wi = parse_wi_definition(feature_dir, wi_id)
    feature_name = parse_feature_name(feature_dir)
    today = datetime.now().strftime("%Y-%m-%d")

    # Security knowledge injection constants
    _SECURITY_RISK_FLAGS = {"authz", "sod", "pii", "audit_log", "security", "accounting_calc"}
    _SECURITY_KNOWLEDGE_TAGS = [
        "llm_trust_boundary",
        "prompt_injection",
        "input_validation",
        "output_verification",
        "authz_bypass",
        "pii_exposure",
        "s2s_authentication",
    ]

    # Search knowledge with SDD-relevant tags
    raw_risk_flags = wi.get("risk_flags", [])
    search_tags = ["sdd", "erp", "stride"] + raw_risk_flags
    if wi.get("mode"):
        search_tags.append(wi["mode"])

    # Inject security knowledge tags when security-related risk_flags are present
    if set(str(f).lower() for f in raw_risk_flags) & _SECURITY_RISK_FLAGS:
        search_tags.extend(_SECURITY_KNOWLEDGE_TAGS)
    knowledge = search_knowledge(search_tags)

    # --- Generate plan.md ---
    applied_rows = ""
    applied_ids = []
    for k in knowledge:
        eff_str = f"{k['effectiveness']:.0%}" if k["effectiveness"] < 1.0 else "—"
        applied_rows += f"| {k['id']} | {k['title']} | | TBD |\n"
        applied_ids.append(k["id"])

    spec_refs_str = ", ".join(wi.get("spec_refs", [])) or "—"
    risk_flags_str = ", ".join(wi.get("risk_flags", [])) or "—"
    dod_items = wi.get("dod", [])
    dod_tasks = "\n".join(f"- [ ] {item}" for item in dod_items) if dod_items else "- [ ] Implement per spec_refs\n- [ ] Write tests\n- [ ] Create walkthrough.md"

    plan_content = f"""# Plan: {wi_id} — {wi['title']}

## Goal
Complete {wi_id} ({wi['mode']} mode) for Feature {feature_name}.

## SDD Context
- **Feature:** {feature_name}
- **Work Item:** {wi_id}
- **Mode:** {wi['mode']}
- **Risk Flags:** {risk_flags_str}
- **Spec Refs:** {spec_refs_str}

## Current Phase
Phase 1

## Applied Knowledge
| ID | Title | How Applied | Helped? |
|----|-------|-------------|---------|
{applied_rows}
## Phases

### Phase 1: Preparation
- [ ] Review spec_refs and ACs
- [ ] Confirm WI readiness (wi_readiness_checker)
- [ ] Set up development environment
- **Status:** in_progress

### Phase 2: Implementation
{dod_tasks}
- **Status:** pending

### Phase 3: Verification
- [ ] Run stride-lint → PASS
- [ ] Verify all ACs satisfied (spec_refs full check)
- [ ] Run tests (scenarios.yaml)
- **Status:** pending

### Phase 4: Evidence & Delivery
- [ ] Create walkthrough.md (with Planning Evidence)
- [ ] Create test_results.md (if standard/critical tier)
- [ ] /planning:archive → global knowledge
- [ ] Request WI approval
- **Status:** pending

## Decisions
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|

## Errors
| # | Error | Attempt | Resolution | Phase |
|---|-------|---------|------------|-------|

## Test Results
| # | Test | Expected | Actual | Pass? |
|---|------|----------|--------|-------|
"""
    (planning_dir / "plan.md").write_text(plan_content, encoding="utf-8")

    # --- Generate findings.md ---
    findings_content = f"""# Findings

## Exploration Ladder (Search-First)
- [ ] Project-internal: similar implementations found?
- [ ] Past lessons: relevant knowledge items?
- [ ] External packages: existing solutions?
- [ ] Contract alignment: existing shared contracts?

## Spec References
- Feature: {feature_name}
- Spec Refs: {spec_refs_str}

## Requirements (from ACs)
- [Review spec.md ACs listed in spec_refs]

## Research
-

## Technical Notes
-

## References
-

<!-- 2-Action Rule: update after every 2 search/browse operations -->
"""
    (planning_dir / "findings.md").write_text(findings_content, encoding="utf-8")

    # --- Generate lessons.md ---
    inherited_rows = ""
    for k in knowledge:
        inherited_rows += f"| global | {k['id']} | {k['title']} | Yes | TBD | |\n"

    lessons_content = f"""# Lessons Learned

## Project Info
- **Project:** {feature_name}
- **Work Item:** {wi_id}
- **Mode:** {wi['mode']}
- **Date:** {today}

## Inherited Knowledge Effectiveness
| Source | ID | Title | Applied? | Helped? | Notes |
|--------|-----|-------|----------|---------|-------|
{inherited_rows}
## Best Practices Discovered

## Troubles Resolved

## Technical Knowledge

## Archive Summary
| ID | Type | Title | Reusability | Archive? |
|----|------|-------|-------------|----------|
"""
    (planning_dir / "lessons.md").write_text(lessons_content, encoding="utf-8")

    # --- Initialize ops counter ---
    (planning_dir / ".findings_ops").write_text("0", encoding="utf-8")

    # --- Update reuse counts ---
    if applied_ids:
        update_reuse_count(applied_ids)

    # --- Report ---
    print(f"✅ Planning initialized for {wi_id}")
    print(f"   Run: {run_dir.name}")
    print(f"   Goal: Complete {wi_id} ({wi['mode']} mode)")
    print(f"   Phases: 4 (Preparation → Implementation → Verification → Evidence)")
    print(f"   Knowledge: {len(knowledge)} past item(s) applied")
    print(f"   Files: .planning/plan.md, findings.md, lessons.md")

    # --- Optional Linear sync (v5.3) ---
    _maybe_sync_linear("init", feature_dir, wi_id=wi_id)

    return 0


def _maybe_sync_linear(operation: str, feature_dir: Path, *, wi_id: Optional[str] = None, run_dir: Optional[Path] = None) -> None:
    """Opt-in hook: forward Run lifecycle events to linear_bridge.

    Activation: STRIDE_LINEAR_AUTO=1 AND LINEAR_API_KEY set. Failures are non-fatal.
    """
    import subprocess
    if os.environ.get("STRIDE_LINEAR_AUTO") != "1":
        return
    if not os.environ.get("LINEAR_API_KEY"):
        return
    bridge = Path(__file__).parent / "linear_bridge.py"
    if not bridge.exists():
        return
    try:
        if operation == "init" and wi_id:
            cmd = [sys.executable, str(bridge), "init", str(feature_dir), wi_id]
        elif operation == "sync" and run_dir:
            cmd = [sys.executable, str(bridge), "sync", str(run_dir)]
        else:
            return
        subprocess.run(cmd, check=False, timeout=60)
    except Exception as exc:  # pragma: no cover
        print(f"   ⚠ Linear sync skipped ({operation}): {exc}")


# =============================================================================
# Subcommand: sync
# =============================================================================


def cmd_sync(feature_dir: Path, run_dir: Optional[Path] = None, wi_id: Optional[str] = None) -> int:
    """Sync stride-lint results into plan.md Errors table.

    §10 mapping:
    - Step 5: Implementation — error tracking during work
    - Integrates stride-lint output with planning error log
    """
    import subprocess

    # Find planning dir
    planning_dir = None
    if run_dir and (run_dir / ".planning").exists():
        planning_dir = run_dir / ".planning"
    else:
        # Search for active .planning in latest run
        if wi_id:
            latest = find_latest_run_dir(feature_dir, wi_id)
            if latest and (latest / ".planning").exists():
                planning_dir = latest / ".planning"

    # Fallback: project-level .planning
    if planning_dir is None:
        project_root = feature_dir.parent.parent
        if (project_root / ".planning").exists():
            planning_dir = project_root / ".planning"

    if planning_dir is None:
        print("⚠ No .planning/ found. Run 'bridge init' first.")
        return 1

    plan_file = planning_dir / "plan.md"
    if not plan_file.exists():
        print("⚠ plan.md not found in .planning/")
        return 1

    # Run stride-lint and capture output
    lint_cmd = str(feature_dir.parent.parent / "sdd-templates" / "tools" / "stride-lint")
    try:
        result = subprocess.run(
            [lint_cmd, str(feature_dir)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lint_output = result.stdout + result.stderr
        lint_rc = result.returncode
    except FileNotFoundError:
        # Try as Python script
        try:
            result = subprocess.run(
                [sys.executable, str(feature_dir.parent.parent / "sdd-templates" / "tools" / "stride_lint.py"), str(feature_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            lint_output = result.stdout + result.stderr
            lint_rc = result.returncode
        except Exception as e:
            print(f"⚠ Could not run stride-lint: {e}")
            return 1
    except Exception as e:
        print(f"⚠ stride-lint execution error: {e}")
        return 1

    # Parse FAIL lines from lint output
    fail_lines = []
    for line in lint_output.splitlines():
        if "FAIL" in line and "APPROVAL" not in line:
            fail_lines.append(line.strip())

    # Read current plan.md
    plan_content = plan_file.read_text(encoding="utf-8")

    # Find Errors table and append new errors
    if fail_lines:
        # Count existing errors
        existing_errors = len(re.findall(r"^\|\s*\d+\s*\|", plan_content, re.MULTILINE))

        new_rows = ""
        for i, fail in enumerate(fail_lines, start=existing_errors + 1):
            # Clean up the fail message
            clean_fail = fail.replace("|", "/").strip()
            new_rows += f"| {i} | {clean_fail} | 1 | [pending] | — |\n"

        # Append to Errors table (before Test Results)
        if "## Test Results" in plan_content:
            plan_content = plan_content.replace(
                "## Test Results",
                f"{new_rows}\n## Test Results",
            )
        else:
            plan_content += f"\n{new_rows}"

        plan_file.write_text(plan_content, encoding="utf-8")
        print(f"📝 Synced {len(fail_lines)} lint error(s) to plan.md Errors table")
    else:
        print(f"✅ stride-lint {'PASS' if lint_rc == 0 else 'completed'} — no new errors to sync")

    # Update phase status if lint passed
    if lint_rc == 0 and "Phase 3: Verification" in plan_content:
        plan_content = plan_content.replace(
            '### Phase 3: Verification\n- [ ] Run stride-lint → PASS',
            '### Phase 3: Verification\n- [x] Run stride-lint → PASS',
        )
        plan_file.write_text(plan_content, encoding="utf-8")

    return 0


# =============================================================================
# Subcommand: evidence
# =============================================================================


def cmd_evidence(feature_dir: Path, wi_id: str, run_dir: Optional[Path] = None) -> int:
    """Generate "Planning Evidence" section for walkthrough.md.

    §10 mapping:
    - Step 6: walkthrough.md creation — Planning Evidence section
    - Summarizes .planning/ content for audit trail
    """
    # Resolve run directory
    if run_dir is None:
        run_dir = find_latest_run_dir(feature_dir, wi_id)
    if run_dir is None:
        print(f"⚠ No RUN directory found for {wi_id}")
        return 1

    planning_dir = run_dir / ".planning"
    if not planning_dir.exists():
        print(f"⚠ No .planning/ in {run_dir.name}. Run 'bridge init' first.")
        return 1

    # Parse plan.md
    plan_file = planning_dir / "plan.md"
    plan_content = plan_file.read_text(encoding="utf-8") if plan_file.exists() else ""

    goal_match = re.search(r"^## Goal\n(.+?)(?=\n##|\Z)", plan_content, re.MULTILINE | re.DOTALL)
    goal = goal_match.group(1).strip().split("\n")[0] if goal_match else "—"

    # Extract decisions
    decisions = []
    decisions_match = re.search(r"## Decisions\n\|[^\n]+\n\|[-| ]+\n(.*?)(?=\n##|\Z)", plan_content, re.DOTALL)
    if decisions_match:
        for line in decisions_match.group(1).strip().splitlines():
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 2 and cols[1]:
                decisions.append(f"- {cols[1]}: {cols[2] if len(cols) > 2 else ''}")

    # Extract errors
    errors = []
    errors_match = re.search(r"## Errors\n\|[^\n]+\n\|[-| ]+\n(.*?)(?=\n##|\Z)", plan_content, re.DOTALL)
    if errors_match:
        for line in errors_match.group(1).strip().splitlines():
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3 and cols[1]:
                errors.append(f"- {cols[1]} → {cols[3] if len(cols) > 3 else 'pending'}")

    # Parse findings.md
    findings_file = planning_dir / "findings.md"
    findings_content = findings_file.read_text(encoding="utf-8") if findings_file.exists() else ""
    findings_count = len([
        line for line in findings_content.splitlines()
        if line.startswith("- ") and line.strip() != "-" and not line.startswith("- [")
    ])

    # Parse lessons.md
    lessons_file = planning_dir / "lessons.md"
    lessons_content = lessons_file.read_text(encoding="utf-8") if lessons_file.exists() else ""
    lesson_ids = re.findall(r"^### ([KTB][P-]*-\d+):", lessons_content, re.MULTILINE)

    # Extract inherited knowledge effectiveness
    inherited = []
    inherited_match = re.search(
        r"## Inherited Knowledge Effectiveness\n\|[^\n]+\n\|[-| ]+\n(.*?)(?=\n##|\Z)",
        lessons_content,
        re.DOTALL,
    )
    if inherited_match:
        for line in inherited_match.group(1).strip().splitlines():
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 5 and cols[1]:
                helped = cols[4] if len(cols) > 4 else "TBD"
                inherited.append(f"- {cols[1]} ({cols[2]}): Helped={helped}")

    # Generate evidence section
    evidence = f"""## Planning Evidence

> Auto-generated by `sdd_planning_bridge.py evidence` from `.planning/`

### Goal
{goal}

### Decisions ({len(decisions)})
{chr(10).join(decisions) if decisions else '- None recorded'}

### Errors Encountered ({len(errors)})
{chr(10).join(errors) if errors else '- None'}

### Research Findings
- {findings_count} item(s) recorded in findings.md

### Lessons Captured ({len(lesson_ids)})
{chr(10).join(f'- {lid}' for lid in lesson_ids) if lesson_ids else '- None yet (will be captured at archive)'}

### Inherited Knowledge
{chr(10).join(inherited) if inherited else '- No prior knowledge applied'}
"""

    # Check if walkthrough.md exists and append/insert
    walkthrough_file = run_dir / "walkthrough.md"
    if walkthrough_file.exists():
        wt_content = walkthrough_file.read_text(encoding="utf-8")
        if "## Planning Evidence" in wt_content:
            # Replace existing section
            wt_content = re.sub(
                r"## Planning Evidence.*?(?=\n## |\Z)",
                evidence,
                wt_content,
                flags=re.DOTALL,
            )
        else:
            # Append before Review Checklist if it exists, otherwise at end
            if "## Review Checklist" in wt_content:
                wt_content = wt_content.replace("## Review Checklist", f"{evidence}\n## Review Checklist")
            else:
                wt_content += f"\n{evidence}"
        walkthrough_file.write_text(wt_content, encoding="utf-8")
        print(f"✅ Planning Evidence inserted into walkthrough.md")
    else:
        # Output to stdout for manual insertion
        print(evidence)
        print(f"\n💡 Paste this into walkthrough.md under 'Planning Evidence'")

    # --- Optional Linear sync (v5.3) ---
    _maybe_sync_linear("sync", feature_dir, run_dir=run_dir)

    return 0


# =============================================================================
# Subcommand: learn
# =============================================================================


def cmd_learn(feature_dir: Path, wi_id: str, run_dir: Optional[Path] = None, apply: bool = False) -> int:
    """Extract lesson candidates from Run artifacts.

    Sources:
    - plan.md Errors table: rows with attempt >= 2 → Troubles Resolved
    - plan.md Decisions table: all rows → Best Practices Discovered
    - findings.md ## Technical Notes: non-empty lines → Technical Knowledge
    - stride-lint output: FAIL patterns (excl. APPROVAL) → Troubles Resolved
    """
    import subprocess

    # Resolve run directory
    if run_dir is None:
        run_dir = find_latest_run_dir(feature_dir, wi_id)
    if run_dir is None:
        print(f"⚠ No RUN directory found for {wi_id}")
        return 1

    planning_dir = run_dir / ".planning"
    if not planning_dir.exists():
        print(f"⚠ No .planning/ in {run_dir.name}. Run 'bridge init' first.")
        return 1

    # --- Parse plan.md ---
    plan_file = planning_dir / "plan.md"
    plan_content = plan_file.read_text(encoding="utf-8") if plan_file.exists() else ""

    # Extract Decisions
    decisions: List[Tuple[str, str, str]] = []  # (id, decision, rationale)
    dec_match = re.search(
        r"## Decisions\n\|[^\n]+\n\|[-| ]+\n(.*?)(?=\n## |\Z)", plan_content, re.DOTALL
    )
    if dec_match:
        for line in dec_match.group(1).strip().splitlines():
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 3 and cols[1]:
                decisions.append((cols[0], cols[1], cols[2]))

    # Extract Errors with attempt >= 2
    retried_errors: List[Tuple[str, str, int, str]] = []  # (id, error, attempt, resolution)
    err_match = re.search(
        r"## Errors\n\|[^\n]+\n\|[-| ]+\n(.*?)(?=\n## |\Z)", plan_content, re.DOTALL
    )
    if err_match:
        for line in err_match.group(1).strip().splitlines():
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) >= 4 and cols[1]:
                try:
                    attempt = int(cols[2])
                except (ValueError, IndexError):
                    attempt = 1
                if attempt >= 2:
                    resolution = cols[3] if len(cols) > 3 else "[pending]"
                    retried_errors.append((cols[0], cols[1], attempt, resolution))

    # --- Parse findings.md ---
    findings_file = planning_dir / "findings.md"
    tech_notes: List[str] = []
    if findings_file.exists():
        findings_content = findings_file.read_text(encoding="utf-8")
        tech_match = re.search(
            r"## Technical Notes\s*\n(.*?)(?=\n## |\Z)", findings_content, re.DOTALL
        )
        if tech_match:
            for line in tech_match.group(1).strip().splitlines():
                stripped = line.strip()
                if stripped and stripped != "-" and not stripped.startswith("<!--"):
                    # Remove leading "- " if present
                    if stripped.startswith("- "):
                        stripped = stripped[2:]
                    if stripped:
                        tech_notes.append(stripped)

    # --- Run stride-lint for current FAIL patterns ---
    lint_fails: List[str] = []
    lint_cmd = str(feature_dir.parent.parent / "sdd-templates" / "tools" / "stride-lint")
    try:
        result = subprocess.run(
            [lint_cmd, str(feature_dir)],
            capture_output=True, text=True, timeout=30,
        )
        lint_output = result.stdout + result.stderr
    except FileNotFoundError:
        try:
            result = subprocess.run(
                [sys.executable, str(feature_dir.parent.parent / "sdd-templates" / "tools" / "stride_lint.py"), str(feature_dir)],
                capture_output=True, text=True, timeout=30,
            )
            lint_output = result.stdout + result.stderr
        except Exception:
            lint_output = ""
    except Exception:
        lint_output = ""

    for line in lint_output.splitlines():
        if "FAIL" in line and "APPROVAL" not in line:
            lint_fails.append(line.strip())

    # --- Format output ---
    output_lines: List[str] = []
    output_lines.append(f"=== Lesson Candidates for {wi_id} ===")
    output_lines.append("")

    # Best Practices from Decisions
    output_lines.append("## Best Practices Discovered (from Decisions)")
    if decisions:
        for d_id, decision, rationale in decisions:
            output_lines.append(f"- D{d_id}: {decision} — Rationale: {rationale}")
    else:
        output_lines.append("- (none)")
    output_lines.append("")

    # Troubles Resolved from retried Errors + lint FAILs
    output_lines.append("## Troubles Resolved (from Errors with retries + lint FAILs)")
    has_troubles = False
    if retried_errors:
        for e_id, error, attempt, resolution in retried_errors:
            output_lines.append(f"- E{e_id}: {error} → Fix: {resolution} (attempts: {attempt})")
            has_troubles = True
    if lint_fails:
        for fail in lint_fails:
            output_lines.append(f"- lint: {fail}")
            has_troubles = True
    if not has_troubles:
        output_lines.append("- (none)")
    output_lines.append("")

    # Technical Knowledge from findings.md
    output_lines.append("## Technical Knowledge (from findings.md)")
    if tech_notes:
        for note in tech_notes:
            output_lines.append(f"- {note}")
    else:
        output_lines.append("- (none)")
    output_lines.append("")

    # Archive Summary suggestions
    output_lines.append("## Archive Summary (suggested rows)")
    row_idx = 1
    for _, decision, _ in decisions:
        title = decision[:50] + "..." if len(decision) > 50 else decision
        output_lines.append(f"| BP-{row_idx:03d} | best_practice | {title} | cross-feature | Yes |")
        row_idx += 1
    for _, error, _, _ in retried_errors:
        title = error[:50] + "..." if len(error) > 50 else error
        output_lines.append(f"| TR-{row_idx:03d} | trouble | {title} | feature-specific | Maybe |")
        row_idx += 1
    for note in tech_notes:
        title = note[:50] + "..." if len(note) > 50 else note
        output_lines.append(f"| TK-{row_idx:03d} | technical | {title} | feature-specific | Maybe |")
        row_idx += 1
    if row_idx == 1:
        output_lines.append("| (none) | — | — | — | — |")
    output_lines.append("")

    output_lines.append("To apply: review above and manually add to .planning/lessons.md")
    output_lines.append("Then run: /planning:archive (Claude Code built-in command) to save to global knowledge")

    output_text = "\n".join(output_lines)
    print(output_text)

    # --- Apply mode (idempotent) ---
    if apply:
        lessons_file = planning_dir / "lessons.md"
        if not lessons_file.exists():
            print("\n⚠ lessons.md not found — cannot apply. Run 'bridge init' first.")
            return 1

        lessons_content = lessons_file.read_text(encoding="utf-8")

        def _existing_lines_in_section(content: str, heading: str) -> set:
            """Extract existing bullet lines from a section for dedup."""
            m = re.search(
                rf"## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
            )
            if not m:
                return set()
            return {line.strip() for line in m.group(1).splitlines() if line.strip().startswith("- ")}

        def _append_to_section(content: str, heading: str, new_lines: List[str]) -> str:
            """Append non-duplicate lines after a section heading."""
            if not new_lines:
                return content
            existing = _existing_lines_in_section(content, heading)
            deduped = [line for line in new_lines if line not in existing]
            if not deduped and heading in content:
                return content
            if deduped and f"## {heading}" in content:
                items_text = "\n".join(deduped)
                content = content.replace(f"## {heading}", f"## {heading}\n{items_text}")
            return content

        # Append to Best Practices Discovered
        bp_lines = [f"- D{d_id}: {dec} (Rationale: {rat})" for d_id, dec, rat in decisions]
        lessons_content = _append_to_section(lessons_content, "Best Practices Discovered", bp_lines)

        # Append to Troubles Resolved
        tr_lines: List[str] = []
        if retried_errors:
            tr_lines.extend(
                f"- E{e_id}: {err} → Fix: {res} (attempts: {att})"
                for e_id, err, att, res in retried_errors
            )
        if lint_fails:
            tr_lines.extend(f"- lint: {fail}" for fail in lint_fails)
        lessons_content = _append_to_section(lessons_content, "Troubles Resolved", tr_lines)

        # Append to Technical Knowledge
        tk_lines = [f"- {note}" for note in tech_notes]
        lessons_content = _append_to_section(lessons_content, "Technical Knowledge", tk_lines)

        # Append Archive Summary rows (idempotent: find max existing ID, skip known titles)
        existing_archive = set()
        max_existing_id = 0
        archive_section = re.search(
            r"## Archive Summary\n\|[^\n]+\n\|[-| ]+\n(.*?)(?=\n## |\Z)",
            lessons_content, re.DOTALL,
        )
        if archive_section:
            for line in archive_section.group(1).strip().splitlines():
                cols = [c.strip() for c in line.split("|")]
                # cols: ['', id, type, title, reusability, archive, '']
                if len(cols) >= 5:
                    existing_archive.add(cols[3])  # title column for dedup
                    id_match = re.match(r"[A-Z]{2}-(\d+)", cols[1])
                    if id_match:
                        max_existing_id = max(max_existing_id, int(id_match.group(1)))

        archive_rows: List[str] = []
        row_idx = max_existing_id + 1
        for _, decision, _ in decisions:
            title = decision[:50] + "..." if len(decision) > 50 else decision
            if title not in existing_archive:
                archive_rows.append(f"| BP-{row_idx:03d} | best_practice | {title} | cross-feature | Yes |")
                row_idx += 1
        for _, error, _, _ in retried_errors:
            title = error[:50] + "..." if len(error) > 50 else error
            if title not in existing_archive:
                archive_rows.append(f"| TR-{row_idx:03d} | trouble | {title} | feature-specific | Maybe |")
                row_idx += 1
        for note in tech_notes:
            title = note[:50] + "..." if len(note) > 50 else note
            if title not in existing_archive:
                archive_rows.append(f"| TK-{row_idx:03d} | technical | {title} | feature-specific | Maybe |")
                row_idx += 1
        if archive_rows:
            archive_text = "\n".join(archive_rows)
            lessons_content = re.sub(
                r"(## Archive Summary\n\|[^\n]+\n\|[-| ]+\n)",
                rf"\1{archive_text}\n",
                lessons_content,
            )

        lessons_file.write_text(lessons_content, encoding="utf-8")
        print(f"\n✅ Applied lesson candidates to {lessons_file.relative_to(run_dir)}")

    return 0


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SDD Planning Bridge — §10 Run-Planning Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize planning for a WI run
  python3 sdd-templates/tools/sdd_planning_bridge.py init specs/my-feature/ WI-ERP-FEAT001-001

  # Sync stride-lint results to plan.md
  python3 sdd-templates/tools/sdd_planning_bridge.py sync specs/my-feature/

  # Generate Planning Evidence for walkthrough.md
  python3 sdd-templates/tools/sdd_planning_bridge.py evidence specs/my-feature/ WI-ERP-FEAT001-001

  # Extract lesson candidates from Run artifacts
  python3 sdd-templates/tools/sdd_planning_bridge.py learn specs/my-feature/ WI-ERP-FEAT001-001
  python3 sdd-templates/tools/sdd_planning_bridge.py learn specs/my-feature/ WI-ERP-FEAT001-001 --apply
""",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    init_parser = subparsers.add_parser("init", help="Create .planning/ with SDD context")
    init_parser.add_argument("feature_dir", type=Path, help="Path to specs/<feature>/")
    init_parser.add_argument("wi_id", help="Work Item ID (e.g., WI-ERP-FEAT001-001)")
    init_parser.add_argument("run_dir", type=Path, nargs="?", default=None, help="Optional: specific RUN directory")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Sync stride-lint results to plan.md Errors")
    sync_parser.add_argument("feature_dir", type=Path, help="Path to specs/<feature>/")
    sync_parser.add_argument("run_dir", type=Path, nargs="?", default=None, help="Optional: specific RUN directory")
    sync_parser.add_argument("--wi-id", default=None, help="Work Item ID for run lookup")

    # evidence
    evidence_parser = subparsers.add_parser("evidence", help="Generate Planning Evidence for walkthrough.md")
    evidence_parser.add_argument("feature_dir", type=Path, help="Path to specs/<feature>/")
    evidence_parser.add_argument("wi_id", help="Work Item ID")
    evidence_parser.add_argument("run_dir", type=Path, nargs="?", default=None, help="Optional: specific RUN directory")

    # learn
    learn_parser = subparsers.add_parser("learn", help="Extract lesson candidates from Run artifacts")
    learn_parser.add_argument("feature_dir", type=Path, help="Path to specs/<feature>/")
    learn_parser.add_argument("wi_id", help="Work Item ID")
    learn_parser.add_argument("run_dir", type=Path, nargs="?", default=None, help="Optional: specific RUN directory")
    learn_parser.add_argument("--apply", action="store_true", help="Write candidates directly to lessons.md")

    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args.feature_dir, args.wi_id, args.run_dir)
    elif args.command == "sync":
        return cmd_sync(args.feature_dir, args.run_dir, getattr(args, "wi_id", None))
    elif args.command == "evidence":
        return cmd_evidence(args.feature_dir, args.wi_id, args.run_dir)
    elif args.command == "learn":
        return cmd_learn(args.feature_dir, args.wi_id, args.run_dir, args.apply)
    else:
        parser.print_help()
        return 1


def run_tests() -> bool:
    """Self-tests for sdd_planning_bridge.py (cmd_learn focus)."""
    import io as _io
    import shutil
    import tempfile

    print("Running sdd_planning_bridge.py self-tests...\n")
    tmpdir = Path(tempfile.mkdtemp())

    try:
        specs = tmpdir / "specs" / "test-feat"
        specs.mkdir(parents=True)
        # Fake sdd-templates path (stride-lint will fail — that's fine, lint_fails will be empty)
        (tmpdir / "sdd-templates" / "tools").mkdir(parents=True)

        wi_id = "WI-TEST-001"
        run_dir = specs / "runs" / wi_id / "RUN-20260322-1000"
        planning = run_dir / ".planning"
        planning.mkdir(parents=True)

        # --- Setup plan.md ---
        (planning / "plan.md").write_text(
            "# Plan\n\n## Decisions\n"
            "| # | Decision | Rationale | Phase |\n"
            "|---|----------|-----------|-------|\n"
            "| 1 | Use Redis | Low latency | Phase 2 |\n\n"
            "## Errors\n"
            "| # | Error | Attempt | Resolution | Phase |\n"
            "|---|-------|---------|------------|-------|\n"
            "| 1 | YAML indent | 1 | Fixed | Phase 1 |\n"
            "| 2 | Missing coverage | 3 | Added policy | Phase 2 |\n\n"
            "## Test Results\n"
            "| # | Test | Expected | Actual | Pass? |\n"
            "|---|------|----------|--------|-------|\n",
            encoding="utf-8",
        )

        # --- Setup findings.md ---
        (planning / "findings.md").write_text(
            "# Findings\n\n## Research\n- Checked libs\n\n"
            "## Technical Notes\n- IDoc uses XML envelope\n\n## References\n- SAP docs\n",
            encoding="utf-8",
        )

        # --- Setup lessons.md (template from init) ---
        (planning / "lessons.md").write_text(
            "# Lessons Learned\n\n## Inherited Knowledge Effectiveness\n"
            "| Source | ID | Title | Applied? | Helped? | Notes |\n"
            "|--------|-----|-------|----------|---------|-------|\n\n"
            "## Best Practices Discovered\n\n"
            "## Troubles Resolved\n\n"
            "## Technical Knowledge\n\n"
            "## Archive Summary\n"
            "| ID | Type | Title | Reusability | Archive? |\n"
            "|----|------|-------|-------------|----------|\n",
            encoding="utf-8",
        )

        # ── Test 1: dry run (no --apply) ────────────────────────────
        print("Test 1: learn dry run")
        old_stdout = sys.stdout
        sys.stdout = _io.StringIO()
        rc = cmd_learn(specs, wi_id, run_dir, apply=False)
        output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        assert rc == 0, f"Expected rc=0, got {rc}"
        assert "Use Redis" in output, "Decision not in output"
        assert "Missing coverage" in output, "Retried error not in output"
        assert "YAML indent" not in output, "Single-attempt error should be excluded"
        assert "IDoc uses XML" in output, "Tech note not in output"
        # Verify lessons.md unchanged
        lc = (planning / "lessons.md").read_text(encoding="utf-8")
        assert "Use Redis" not in lc, "Dry run should not modify lessons.md"
        print("  PASS: dry run extracts candidates without writing")

        # ── Test 2: --apply writes BP/TR/TK sections ────────────────
        print("\nTest 2: learn --apply writes sections")
        sys.stdout = _io.StringIO()
        rc = cmd_learn(specs, wi_id, run_dir, apply=True)
        sys.stdout = old_stdout
        assert rc == 0, f"Expected rc=0, got {rc}"
        lc = (planning / "lessons.md").read_text(encoding="utf-8")
        assert "Use Redis" in lc, "Decision not applied to Best Practices"
        assert "Missing coverage" in lc, "Retried error not applied to Troubles"
        assert "IDoc uses XML" in lc, "Tech note not applied to Technical Knowledge"
        assert "YAML indent" not in lc, "Single-attempt error should NOT be in lessons"
        print("  PASS: BP/TR/TK sections populated correctly")

        # ── Test 3: --apply also writes Archive Summary rows ────────
        print("\nTest 3: learn --apply updates Archive Summary")
        assert "| BP-001 | best_practice |" in lc, f"Archive Summary BP row missing"
        assert "| TR-002 | trouble |" in lc, f"Archive Summary TR row missing"
        assert "| TK-003 | technical |" in lc, f"Archive Summary TK row missing"
        print("  PASS: Archive Summary rows written")

        # ── Test 4: empty artifacts → no errors ─────────────────────
        print("\nTest 4: empty plan.md/findings.md")
        run_dir2 = specs / "runs" / wi_id / "RUN-20260322-1100"
        planning2 = run_dir2 / ".planning"
        planning2.mkdir(parents=True)
        (planning2 / "plan.md").write_text(
            "# Plan\n\n## Decisions\n"
            "| # | Decision | Rationale | Phase |\n|---|---|---|---|\n\n"
            "## Errors\n| # | Error | Attempt | Resolution | Phase |\n|---|---|---|---|---|\n",
            encoding="utf-8",
        )
        (planning2 / "findings.md").write_text(
            "# Findings\n\n## Technical Notes\n-\n",
            encoding="utf-8",
        )
        (planning2 / "lessons.md").write_text(
            "# Lessons\n\n## Best Practices Discovered\n\n"
            "## Troubles Resolved\n\n## Technical Knowledge\n\n"
            "## Archive Summary\n| ID | Type | Title | Reusability | Archive? |\n"
            "|----|------|-------|-------------|----------|\n",
            encoding="utf-8",
        )
        sys.stdout = _io.StringIO()
        rc = cmd_learn(specs, wi_id, run_dir2, apply=True)
        sys.stdout = old_stdout
        assert rc == 0, f"Expected rc=0 on empty artifacts, got {rc}"
        print("  PASS: empty artifacts handled gracefully")

        # ── Test 5: findings.md Exploration Ladder in init ──────────
        print("\nTest 5: init generates Exploration Ladder in findings.md")
        run_dir3 = specs / "runs" / "WI-TEST-002" / "RUN-20260322-1200"
        run_dir3.mkdir(parents=True, exist_ok=True)
        wi_dir = specs / "work_items"
        wi_dir.mkdir(parents=True, exist_ok=True)
        sys.stdout = _io.StringIO()
        rc = cmd_init(specs, "WI-TEST-002", run_dir3)
        sys.stdout = old_stdout
        assert rc == 0, f"init rc={rc}"
        findings = (run_dir3 / ".planning" / "findings.md").read_text(encoding="utf-8")
        assert "## Exploration Ladder" in findings, "Exploration Ladder missing from findings.md"
        print("  PASS: Exploration Ladder present in generated findings.md")

        # ── Test 6: --apply is idempotent (double-run) ──────────────
        print("\nTest 6: learn --apply idempotency")
        # Re-read state after Test 2/3 applied to run_dir
        lc_before = (planning / "lessons.md").read_text(encoding="utf-8")
        bp_count_before = lc_before.count("Use Redis")
        archive_count_before = lc_before.count("| BP-001 |")
        # Run apply again on the same RUN
        sys.stdout = _io.StringIO()
        rc = cmd_learn(specs, wi_id, run_dir, apply=True)
        sys.stdout = old_stdout
        assert rc == 0, f"Expected rc=0, got {rc}"
        lc_after = (planning / "lessons.md").read_text(encoding="utf-8")
        bp_count_after = lc_after.count("Use Redis")
        archive_count_after = lc_after.count("| BP-001 |")
        assert bp_count_before == bp_count_after, (
            f"BP duplicated: before={bp_count_before}, after={bp_count_after}"
        )
        assert archive_count_before == archive_count_after, (
            f"Archive Summary duplicated: before={archive_count_before}, after={archive_count_after}"
        )
        print("  PASS: double --apply produces no duplicates")

        print("\nAll self-tests passed.")
        return True

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)
    sys.exit(main())
