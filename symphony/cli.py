"""CLI entry point — subcommands: run, dispatch, status, validate."""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

from symphony.config import ConfigLoader, SymphonyConfig
from symphony.logger import get_logger, get_issue_logger, setup_logging
from symphony.models import OrchestratorState, RunResult, Session
from symphony.prompt import render_prompt
from symphony.reconciler import reconcile
from symphony.retry import RetryManager, calculate_backoff, should_retry
from symphony.router import select_engine
from symphony.parallel import run_parallel
from symphony.runner import run_agent
from symphony.stride_bridge import lint, is_approval_pending, is_all_gates_passed
from symphony.tracker import (
    add_label,
    create_janitor_issue,
    fetch_ready_issues,
    has_open_janitor_issue,
    has_recent_pr,
    post_comment,
    remove_label,
    update_project_status,
)
from symphony.workspace import cleanup_workspace, create_workspace, run_hook

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Orchestration loop
# ---------------------------------------------------------------------------

def _build_log_path(log_dir: str, issue_id: int, attempt: int) -> str:
    """Construct a log file path for an agent run."""
    from datetime import datetime, timezone

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    day_dir = os.path.join(log_dir, today)
    os.makedirs(day_dir, exist_ok=True)
    return os.path.join(day_dir, f"issue-{issue_id}-attempt-{attempt}.log")


def _dispatch_issue(
    config: SymphonyConfig,
    prompt_template: str,
    state: OrchestratorState,
    retry_mgr: RetryManager,
    issue_number: int,
    dry_run: bool = False,
) -> Optional[RunResult]:
    """Fetch a single issue by number and dispatch it.

    Used by the `dispatch` subcommand.
    """
    from symphony.tracker import fetch_ready_issues

    issues = fetch_ready_issues(config.tracker.repo, config.tracker.trigger_label)
    target = None
    for iss in issues:
        if iss.number == issue_number:
            target = iss
            break

    if target is None:
        logger.error(
            "Issue #%d not found with label '%s'",
            issue_number, config.tracker.trigger_label,
        )
        return None

    return _process_issue(config, prompt_template, state, retry_mgr, target, dry_run=dry_run)


def _process_issue(
    config: SymphonyConfig,
    prompt_template: str,
    state: OrchestratorState,
    retry_mgr: RetryManager,
    issue,
    attempt: int = 1,
    dry_run: bool = False,
) -> Optional[RunResult]:
    """Process a single issue through the full pipeline."""
    from symphony.models import Issue

    issue_id = issue.number
    issue_log = get_issue_logger(issue_id, config.observability.log_dir)

    if issue_id in state.claimed:
        logger.info("Issue #%d already claimed — skipping", issue_id)
        return None

    # Claim
    state.claimed.add(issue_id)
    if not dry_run:
        try:
            add_label(config.tracker.repo, issue_id, config.tracker.running_label)
        except RuntimeError as exc:
            logger.warning("Failed to add running label: %s", exc)
        # Add phase label for visibility (e.g. phase:design)
        if issue.phase != "unknown":
            try:
                add_label(config.tracker.repo, issue_id, f"phase:{issue.phase}")
            except RuntimeError as exc:
                logger.warning("Failed to add phase label: %s", exc)
        # Update GitHub Projects status
        try:
            update_project_status(issue_id, "In progress")
        except Exception as exc:
            logger.debug("Project status update skipped: %s", exc)

    # Select engine
    engine = select_engine(config, issue.phase, issue)
    issue_log.info(
        "Selected engine=%s for phase=%s", engine, issue.phase,
        extra={"engine": engine, "phase": issue.phase, "issue_id": issue_id},
    )

    # Create workspace
    branch_name = f"{issue.feature_name}-{issue_id}"
    if dry_run:
        workspace_path = f"<dry-run>/{issue_id}"
        logger.info("[DRY RUN] Would create workspace at %s", workspace_path)
    else:
        try:
            workspace_path = create_workspace(
                config, issue_id, branch_name, feature_name=issue.feature_name
            )
        except RuntimeError as exc:
            logger.error("Workspace creation failed for #%d: %s", issue_id, exc)
            state.claimed.discard(issue_id)
            return None

    # Render prompt
    rendered = render_prompt(
        prompt_template,
        issue=issue,
        phase=issue.phase,
        feature_name=issue.feature_name,
        attempt=attempt if attempt > 1 else None,
    )

    # Build log path
    log_path = _build_log_path(config.observability.log_dir, issue_id, attempt)

    # Record session
    started_at = time.time()
    session = Session(
        issue_id=issue_id,
        engine=engine,
        workspace_path=workspace_path,
        started_at=started_at,
        feature_name=issue.feature_name,
        attempt=attempt,
    )
    state.running[issue_id] = session

    if dry_run:
        logger.info(
            "[DRY RUN] Would run %s for #%d (%s / %s)",
            engine, issue_id, issue.phase, issue.feature_name,
        )
        logger.info("[DRY RUN] Prompt length: %d chars", len(rendered))
        state.running.pop(issue_id, None)
        state.claimed.discard(issue_id)
        return RunResult(
            issue_id=issue_id,
            phase=issue.phase,
            attempt=attempt,
            started_at=started_at,
            ended_at=time.time(),
            status="dry_run",
        )

    # Execute agent (with before_run / after_run hooks)
    hook_env = {"SYMPHONY_FEATURE": issue.feature_name, "SYMPHONY_ISSUE": str(issue_id)}
    run_hook(config.hooks.before_run, cwd=workspace_path, env=hook_env)
    agent_result = run_agent(engine, config, workspace_path, rendered, log_path)
    run_hook(config.hooks.after_run, cwd=workspace_path, env=hook_env)
    ended_at = time.time()

    # Determine outcome
    if agent_result.timed_out:
        status = "timeout"
        error_msg = f"{engine} timed out"
    elif agent_result.returncode == 10:
        status = "needs_input"
        error_msg = "Agent requires human input — see issue comments"
    elif agent_result.returncode != 0:
        status = "failure"
        error_msg = agent_result.stderr[:500] if agent_result.stderr else "Non-zero exit"
    else:
        # Check stride-lint for approval-pending
        lint_result = lint(f"specs/{issue.feature_name}", cwd=workspace_path)
        if is_approval_pending(lint_result):
            status = "approval_pending"
            error_msg = None
        else:
            # Agent exited 0 and no APPROVAL_PENDING — treat as success.
            # Other GATE_FAILED (future phases) are expected and not blocking.
            status = "success"
            error_msg = None

    run_result = RunResult(
        issue_id=issue_id,
        phase=issue.phase,
        attempt=attempt,
        started_at=started_at,
        ended_at=ended_at,
        status=status,
        error=error_msg,
        log_path=log_path,
    )

    # Handle outcome
    state.running.pop(issue_id, None)

    if status == "success":
        _handle_success(config, state, issue, workspace_path)
    elif status in ("approval_pending", "needs_input"):
        _handle_blocked(config, state, session, issue)
    elif should_retry(run_result, max_attempts=config.agent.retry.max_attempts):
        backoff = calculate_backoff(
            attempt,
            base_ms=config.agent.retry.backoff_base_ms,
            max_ms=config.agent.retry.backoff_max_ms,
        )
        retry_mgr.enqueue(issue_id, attempt + 1, backoff, error=error_msg)
        state.claimed.discard(issue_id)
        try:
            post_comment(
                config.tracker.repo, issue_id,
                f"Run attempt {attempt} failed ({status}). Retrying in {backoff:.0f}s.\n\nError: {error_msg or 'N/A'}",
            )
        except RuntimeError as exc:
            logger.warning("Failed to post retry comment for #%d: %s", issue_id, exc)
    else:
        _handle_final_failure(config, state, issue, run_result, workspace_path)

    return run_result


def _handle_success(config, state, issue, workspace_path):
    """Handle a successful agent run."""
    state.completed.add(issue.number)
    state.claimed.discard(issue.number)

    try:
        remove_label(config.tracker.repo, issue.number, config.tracker.trigger_label)
        remove_label(config.tracker.repo, issue.number, config.tracker.running_label)
        remove_label(config.tracker.repo, issue.number, config.tracker.blocked_label)
        add_label(config.tracker.repo, issue.number, config.tracker.done_label)
    except RuntimeError as exc:
        logger.warning("Label update failed for #%d: %s", issue.number, exc)

    try:
        post_comment(
            config.tracker.repo, issue.number,
            f"Phase **{issue.phase}** completed successfully for `{issue.feature_name}`.",
        )
    except RuntimeError as exc:
        logger.warning("Failed to post success comment for #%d: %s", issue.number, exc)

    # Generate run report if stride_board is enabled
    sb = config.observability.stride_board
    if sb.enabled:
        from symphony.stride_bridge import run_report
        run_report(
            workspace_path, issue.number,
            project=sb.project, owner=sb.owner,
            cwd=workspace_path,
        )

    # Update GitHub Projects status
    try:
        update_project_status(issue.number, "Done")
    except Exception as exc:
        logger.debug("Project status update skipped: %s", exc)

    cleanup_workspace(workspace_path)
    logger.info("Issue #%d: completed successfully", issue.number)


def _handle_blocked(config, state, session, issue):
    """Handle an APPROVAL_PENDING result."""
    session.status = "blocked"
    state.running[issue.number] = session

    try:
        add_label(config.tracker.repo, issue.number, config.tracker.blocked_label)
    except RuntimeError:
        pass

    try:
        post_comment(
            config.tracker.repo, issue.number,
            f"Phase **{issue.phase}** is waiting for human approval (APPROVAL_PENDING).\n"
            f"Please review and approve the gate in `specs/{issue.feature_name}/APPROVAL.md`, "
            f"then the orchestrator will auto-continue.",
        )
    except RuntimeError as exc:
        logger.warning("Failed to post blocked comment for #%d: %s", issue.number, exc)
    logger.info("Issue #%d: blocked on approval", issue.number)


def _handle_final_failure(config, state, issue, result, workspace_path):
    """Handle a run that has exhausted all retries."""
    state.claimed.discard(issue.number)

    try:
        remove_label(config.tracker.repo, issue.number, config.tracker.running_label)
        remove_label(config.tracker.repo, issue.number, config.tracker.blocked_label)
        add_label(config.tracker.repo, issue.number, config.tracker.failed_label)
    except RuntimeError:
        pass

    try:
        post_comment(
            config.tracker.repo, issue.number,
            f"Phase **{issue.phase}** failed after {result.attempt} attempt(s).\n\n"
            f"Error: {result.error or 'Unknown'}\n\n"
            f"Log: `{result.log_path}`\n\n"
            f"Manual intervention required.",
        )
    except RuntimeError as exc:
        logger.warning("Failed to post failure comment for #%d: %s", issue.number, exc)
    # Update GitHub Projects status
    try:
        update_project_status(issue.number, "Done")
    except Exception as exc:
        logger.debug("Project status update skipped: %s", exc)
    cleanup_workspace(workspace_path)
    logger.error("Issue #%d: final failure after %d attempts", issue.number, result.attempt)


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

def _run_janitor_scan(config: SymphonyConfig, issues: list) -> None:
    """Scan autopilot/starter issues without recent PRs and propose janitor fixes.

    Runs only when config.janitor.enabled is True.
    Safe: only creates GitHub Issues (no auto-PR, no code changes).
    """
    janitor = config.janitor
    if not janitor.enabled:
        return

    for issue in issues:
        label_names = issue.labels

        # Janitor scope: autopilot + starter only
        if "mode:autopilot" not in label_names:
            continue
        if "tier:starter" not in label_names:
            continue

        # Skip risk-flagged issues
        if any(flag in label_names for flag in janitor.risk_flags_exclude):
            continue

        # Skip if merged PR exists recently
        if has_recent_pr(config.tracker.repo, issue.feature_name, janitor.exclude_recent_pr_days):
            continue

        # Dedup: skip if an open janitor proposal already exists
        if has_open_janitor_issue(config.tracker.repo, issue.feature_name):
            logger.debug("Janitor: open proposal already exists for %s, skipping", issue.feature_name)
            continue

        drift_summary = (
            f"Automated scan: no merged PR for '{issue.feature_name}' in the last "
            f"{janitor.exclude_recent_pr_days} day(s). "
            "Review for style/cyclomatic improvements."
        )

        logger.info("Janitor: proposing cleanup for %s (#%d)", issue.feature_name, issue.number)
        try:
            issue_num = create_janitor_issue(
                config.tracker.repo, issue.feature_name, drift_summary
            )
            if issue_num > 0:
                logger.info("Janitor: created issue #%d for %s", issue_num, issue.feature_name)
        except Exception as exc:
            logger.warning("Janitor: failed to create issue for %s: %s", issue.feature_name, exc)


def cmd_run(args: argparse.Namespace) -> int:
    """Main orchestration loop."""
    loader = ConfigLoader(args.config)
    config = loader.config
    prompt_template = loader.prompt_template

    setup_logging(log_dir=config.observability.log_dir)
    logger.info("Symphony orchestrator starting (once=%s, dry_run=%s)", args.once, args.dry_run)

    state = OrchestratorState()
    retry_mgr = RetryManager()
    last_janitor_scan_at: float = 0.0

    while True:
        # Hot-reload config
        try:
            config = loader.config
            prompt_template = loader.prompt_template
        except Exception as exc:
            logger.error("Config reload failed: %s", exc)

        # Process due retries
        for entry in retry_mgr.get_due():
            logger.info("Retrying issue #%d (attempt %d)", entry.issue_id, entry.attempt)
            retry_mgr.remove(entry.issue_id)
            # Re-fetch the issue
            issues = fetch_ready_issues(config.tracker.repo, config.tracker.trigger_label)
            for iss in issues:
                if iss.number == entry.issue_id:
                    _process_issue(
                        config, prompt_template, state, retry_mgr,
                        iss, attempt=entry.attempt, dry_run=args.dry_run,
                    )
                    break

        # Fetch new ready issues
        try:
            issues = fetch_ready_issues(config.tracker.repo, config.tracker.trigger_label)
        except RuntimeError as exc:
            logger.error("Failed to fetch issues: %s", exc)
            issues = []

        # Limit per cycle
        unclaimed = [
            i for i in issues
            if i.number not in state.claimed
            and i.number not in state.completed
            and not retry_mgr.has(i.number)
        ]
        batch = unclaimed[: config.polling.max_issues_per_cycle]

        # Split batch into parallel-eligible (execute phase with parallel=true)
        # and serial issues
        parallel_issues = []
        serial_issues = []
        for issue in batch:
            routing = config.agent.routing.get(issue.phase)
            if routing and routing.parallel and not args.dry_run:
                parallel_issues.append(issue)
            else:
                serial_issues.append(issue)

        # Process serial issues
        for issue in serial_issues:
            _process_issue(
                config, prompt_template, state, retry_mgr,
                issue, dry_run=args.dry_run,
            )

        # Process parallel issues via run_parallel, grouped by phase
        if parallel_issues:
            # Group by phase so each group uses its own max_concurrent
            by_phase: dict[str, list] = {}
            for issue in parallel_issues:
                by_phase.setdefault(issue.phase, []).append(issue)

            for phase, phase_issues in by_phase.items():
                routing = config.agent.routing[phase]
                max_conc = routing.max_concurrent
                tasks = {}
                for issue in phase_issues:
                    tasks[str(issue.number)] = (
                        _process_issue,
                        (config, prompt_template, state, retry_mgr, issue),
                        {"dry_run": False},
                    )
                logger.info(
                    "Dispatching %d %s-phase issues in parallel (max_concurrent=%d)",
                    len(phase_issues), phase, max_conc,
                )
                results = run_parallel(tasks, max_concurrent=max_conc)

                # Route error results through normal retry/failure handling
                issue_by_number = {i.number: i for i in phase_issues}
                for tid, result in results.items():
                    if hasattr(result, "status") and result.status == "error":
                        issue_id = int(tid)
                        error_result = RunResult(
                            issue_id=issue_id,
                            phase=phase,
                            attempt=1,
                            started_at=result.started_at,
                            ended_at=result.ended_at,
                            status="failure",
                            error=result.error,
                        )
                        session = state.running.pop(issue_id, None)
                        ws_path = session.workspace_path if session else ""
                        issue_obj = issue_by_number.get(issue_id)

                        if should_retry(error_result, max_attempts=config.agent.retry.max_attempts):
                            backoff = calculate_backoff(
                                1,
                                base_ms=config.agent.retry.backoff_base_ms,
                                max_ms=config.agent.retry.backoff_max_ms,
                            )
                            retry_mgr.enqueue(issue_id, 2, backoff, error=result.error)
                            state.claimed.discard(issue_id)
                            try:
                                post_comment(
                                    config.tracker.repo, issue_id,
                                    f"Parallel run failed (error). Retrying in {backoff:.0f}s.\n\nError: {result.error or 'N/A'}",
                                )
                            except RuntimeError as exc:
                                logger.warning("Failed to post parallel retry comment for #%d: %s", issue_id, exc)
                        elif issue_obj:
                            _handle_final_failure(config, state, issue_obj, error_result, ws_path)
                        else:
                            state.claimed.discard(issue_id)
                            logger.error(
                                "Issue #%d: parallel error with no retry path: %s",
                                issue_id, result.error,
                            )

        # Reconcile state
        try:
            actions = reconcile(state, config)
            for issue_id in actions.cleanup:
                session = state.running.pop(issue_id, None)
                if session:
                    cleanup_workspace(session.workspace_path)
                state.claimed.discard(issue_id)
                try:
                    remove_label(config.tracker.repo, issue_id, config.tracker.running_label)
                    remove_label(config.tracker.repo, issue_id, config.tracker.blocked_label)
                except RuntimeError:
                    pass
            for issue_id in actions.unblock:
                session = state.running.get(issue_id)
                if session:
                    try:
                        remove_label(config.tracker.repo, issue_id, config.tracker.blocked_label)
                    except RuntimeError:
                        pass
                    # Re-trigger via auto-continue
                    from symphony.stride_bridge import auto_continue
                    auto_continue(
                        f"specs/{session.feature_name}",
                        cwd=session.workspace_path,
                    )
                    # Clear session and re-add trigger label for re-processing
                    state.running.pop(issue_id, None)
                    state.claimed.discard(issue_id)
                    try:
                        add_label(config.tracker.repo, issue_id, config.tracker.trigger_label)
                    except RuntimeError:
                        pass
            for issue_id in actions.stale_claims:
                logger.warning(
                    "Issue #%d: recovering stale claim — releasing back to unclaimed",
                    issue_id,
                )
                state.claimed.discard(issue_id)
                try:
                    remove_label(config.tracker.repo, issue_id, config.tracker.running_label)
                except Exception as label_exc:
                    logger.debug("Could not remove running label from #%d: %s", issue_id, label_exc)
        except Exception as exc:
            logger.error("Reconciliation failed: %s", exc)

        # Janitor scan (interval-gated, config.janitor.enabled)
        if config.janitor.enabled and not args.dry_run:
            interval_secs = config.janitor.interval_hours * 3600
            if time.time() - last_janitor_scan_at >= interval_secs:
                try:
                    _run_janitor_scan(config, issues)
                except Exception as exc:
                    logger.warning("Janitor scan error: %s", exc)
                last_janitor_scan_at = time.time()

        if args.once:
            logger.info("--once mode: exiting after one cycle")
            break

        logger.debug("Sleeping %ds until next poll", config.polling.interval_seconds)
        time.sleep(config.polling.interval_seconds)

    return 0


def cmd_dispatch(args: argparse.Namespace) -> int:
    """Dispatch a single issue."""
    loader = ConfigLoader(args.config)
    config = loader.config
    prompt_template = loader.prompt_template

    setup_logging(log_dir=config.observability.log_dir)

    state = OrchestratorState()
    retry_mgr = RetryManager()

    result = _dispatch_issue(
        config, prompt_template, state, retry_mgr,
        issue_number=args.issue,
        dry_run=args.dry_run,
    )

    if result is None:
        logger.error("Dispatch failed for issue #%d", args.issue)
        return 1

    logger.info("Dispatch result: %s (status=%s)", result.issue_id, result.status)
    return 0 if result.status in ("success", "dry_run") else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Show current orchestrator status (from a fresh poll)."""
    loader = ConfigLoader(args.config)
    config = loader.config

    print(f"Repo:          {config.tracker.repo}")
    print(f"Trigger label: {config.tracker.trigger_label}")
    print()

    try:
        issues = fetch_ready_issues(config.tracker.repo, config.tracker.trigger_label)
    except RuntimeError as exc:
        print(f"Error fetching issues: {exc}", file=sys.stderr)
        return 1

    if not issues:
        print("No issues with trigger label found.")
        return 0

    print(f"Ready issues ({len(issues)}):")
    for iss in issues:
        print(f"  #{iss.number:>5}  [{iss.priority}] {iss.phase:<12} {iss.feature_name:<20} {iss.title}")

    return 0


def cmd_janitor(args: argparse.Namespace) -> int:
    """Run a one-shot Janitor scan (v5.1 harness maturity).

    Honours ``config.janitor.enabled`` — prints "skipped" and exits 0 if disabled.
    With ``--dry-run``, prints the effective scope without calling GitHub.
    """
    loader = ConfigLoader(args.config)
    config = loader.config

    setup_logging(log_dir=config.observability.log_dir)

    if not config.janitor.enabled:
        print("Janitor: skipped (janitor.enabled=false in SYMPHONY.md)")
        return 0

    j = config.janitor
    print(
        f"Janitor: enabled (interval={j.interval_hours}h, "
        f"exclude_recent_pr={j.exclude_recent_pr_days}d)"
    )
    print("  Scope:    mode:autopilot + tier:starter")
    print(f"  Excludes: {', '.join(j.risk_flags_exclude) or '(none)'}")

    if args.dry_run:
        print("Janitor: dry-run — no GitHub API calls, no issue creation.")
        return 0

    try:
        issues = fetch_ready_issues(config.tracker.repo, config.tracker.trigger_label)
    except RuntimeError as exc:
        print(f"Error fetching issues: {exc}", file=sys.stderr)
        return 1

    _run_janitor_scan(config, issues)
    print(f"Janitor: scan complete ({len(issues)} candidate(s) evaluated).")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate SYMPHONY.md configuration."""
    config_path = args.config
    print(f"Validating {config_path}...")

    try:
        loader = ConfigLoader(config_path)
        config = loader.config
        prompt = loader.prompt_template
    except FileNotFoundError:
        print(f"ERROR: {config_path} not found", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"  version:           {config.version}")
    print(f"  tracker.repo:      {config.tracker.repo}")
    print(f"  polling.interval:  {config.polling.interval_seconds}s")
    print(f"  workspace.root:    {config.workspace.root}")
    print(f"  prompt template:   {len(prompt)} chars")

    routing_phases = list(config.agent.routing.keys())
    if routing_phases:
        print(f"  routing phases:    {', '.join(routing_phases)}")
    else:
        print("  routing phases:    (none configured — default claude-code)")

    sb = config.observability.stride_board
    if sb.enabled:
        print(f"  stride_board:      {sb.owner}/{sb.project}")
    else:
        print("  stride_board:      disabled")

    print()
    print("OK: Configuration is valid.")
    return 0


# ---------------------------------------------------------------------------
# CLI definition
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser for symphony CLI."""
    parser = argparse.ArgumentParser(
        prog="symphony",
        description="Symphony-style orchestrator for Tecnos-STRIDE Enterprise",
    )
    parser.add_argument(
        "--config", default="SYMPHONY.md",
        help="Path to SYMPHONY.md config file (default: SYMPHONY.md)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = subparsers.add_parser("run", help="Start the polling orchestration loop")
    p_run.add_argument("--once", action="store_true", help="Run one cycle and exit")
    p_run.add_argument("--dry-run", action="store_true", help="Simulate without executing agents")

    # dispatch
    p_dispatch = subparsers.add_parser("dispatch", help="Dispatch a single issue")
    p_dispatch.add_argument("--issue", type=int, required=True, help="GitHub issue number")
    p_dispatch.add_argument("--dry-run", action="store_true", help="Simulate without executing")

    # status
    p_status = subparsers.add_parser("status", help="Show ready issues and orchestrator status")

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate SYMPHONY.md configuration")

    # janitor (v5.1 harness maturity)
    p_janitor = subparsers.add_parser(
        "janitor",
        help="Run a one-shot Janitor scan for cleanup proposals (v5.1)",
    )
    p_janitor.add_argument(
        "--dry-run", action="store_true",
        help="Show effective config without calling GitHub or creating issues",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    """Entry point for `python3 -m symphony`."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "run": cmd_run,
        "dispatch": cmd_dispatch,
        "status": cmd_status,
        "validate": cmd_validate,
        "janitor": cmd_janitor,
    }

    handler = handlers.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    exit_code = handler(args)
    sys.exit(exit_code)
