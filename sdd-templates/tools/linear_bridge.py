#!/usr/bin/env python3
"""linear_bridge — Tecnos-STRIDE Run 成果物 → Linear Issue 同期ブリッジ (v5.3)

SDD Run の実行結果 (walkthrough / findings / lessons / test_results) を Linear
Issue にコメント/状態として投影する。GitHub Issues のハイブリッド WI 管理とは
独立で、両立可能（Linear 側 = 実行証跡ビュー、GitHub 側 = merge ゲート）。

## 責務
- WI 初回起動時に Linear Issue を作成（または既存 Issue を再利用）
- Run 進行に合わせて findings / evidence / lessons を Linear コメントとして投下
- WI 完了時に Linear Issue を Done 遷移
- state.yaml の work_items[].linear_issue_id を Spec-as-Code SSoT として維持

## 認証
- LINEAR_API_KEY env 必須（未設定なら graceful skip, exit 0）
- LINEAR_TEAM_KEY env （既定: "TEC", CLAUDE.md Linear セクション参照）
- LINEAR_PROJECT_ID env (任意、memory/linear.yaml より優先)

## コマンド
    init    <feature_dir> <wi_id>  — Linear Issue 作成/検索 → state.yaml 同期
    findings <run_dir>              — .planning/findings.md を Linear コメント
    evidence <run_dir>              — walkthrough + test_results を Linear コメント
    learn   <run_dir>               — .planning/lessons.md を Linear コメント
    sync    <run_dir>               — findings + evidence + learn を冪等に一括
    close   <feature_dir> <wi_id>   — Linear Issue を Done 遷移
    status  <feature_dir> [<wi_id>] — 現在の Linear Issue 状態表示

    project create <name>           — Linear Project 作成 → memory/linear.yaml 永続化
    project list                    — team 内の Linear Project 一覧
    project use <project_id>        — 既存 Project を紐付け
    project status                  — memory/linear.yaml の現状表示

    --dry-run  API 呼出しせず動作予定を表示
    --test     self-tests 実行
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unittest
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest import mock

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

if sys.platform == "win32":  # pragma: no cover
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


LINEAR_API_URL = "https://api.linear.app/graphql"
DEFAULT_TEAM_KEY = "TEC"
EXIT_OK = 0
EXIT_SKIP = 0  # Graceful skip (no API key) also returns 0
EXIT_ERROR = 2
EXIT_NOT_FOUND = 3


# =============================================================================
# Data models
# =============================================================================


@dataclass
class LinearTeam:
    id: str
    key: str
    name: str


@dataclass
class LinearWorkflowState:
    id: str
    name: str
    type: str  # backlog | unstarted | started | completed | canceled


@dataclass
class LinearIssue:
    id: str
    identifier: str  # "TEC-123"
    title: str
    description: str
    state_name: str
    url: str
    labels: List[str] = field(default_factory=list)


@dataclass
class SyncResult:
    wi_id: str
    issue_identifier: Optional[str]
    action: str  # created | found | updated | commented | transitioned | skipped
    detail: str = ""


# =============================================================================
# GraphQL client (urllib-based, no external deps)
# =============================================================================


class LinearAPIError(RuntimeError):
    pass


class LinearClient:
    """Minimal Linear GraphQL client (POST /graphql)."""

    def __init__(self, api_key: str, endpoint: str = LINEAR_API_URL, timeout: int = 30):
        if not api_key:
            raise LinearAPIError("LINEAR_API_KEY is required")
        self._api_key = api_key
        self._endpoint = endpoint
        self._timeout = timeout

    def request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        req = urllib.request.Request(
            self._endpoint,
            data=payload,
            headers={
                "Authorization": self._api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover (integration-only)
            raise LinearAPIError(f"HTTP {exc.code}: {exc.read().decode('utf-8', 'ignore')}") from exc
        except urllib.error.URLError as exc:  # pragma: no cover
            raise LinearAPIError(f"network error: {exc.reason}") from exc

        data = json.loads(body)
        if "errors" in data and data["errors"]:
            raise LinearAPIError(f"GraphQL errors: {data['errors']}")
        return data.get("data", {})

    # -- Team / state lookup ---------------------------------------------------

    def get_team(self, key: str) -> LinearTeam:
        query = """
        query Team($key: String!) {
          teams(filter: { key: { eq: $key } }) {
            nodes { id key name }
          }
        }
        """
        data = self.request(query, {"key": key})
        nodes = data.get("teams", {}).get("nodes", [])
        if not nodes:
            raise LinearAPIError(f"team not found: key={key}")
        return LinearTeam(id=nodes[0]["id"], key=nodes[0]["key"], name=nodes[0]["name"])

    def list_workflow_states(self, team_id: str) -> List[LinearWorkflowState]:
        query = """
        query States($teamId: String!) {
          workflowStates(filter: { team: { id: { eq: $teamId } } }) {
            nodes { id name type }
          }
        }
        """
        data = self.request(query, {"teamId": team_id})
        return [
            LinearWorkflowState(id=n["id"], name=n["name"], type=n["type"])
            for n in data.get("workflowStates", {}).get("nodes", [])
        ]

    # -- Issue CRUD ------------------------------------------------------------

    def find_issue_by_wi(self, team_key: str, wi_id: str) -> Optional[LinearIssue]:
        """Find an existing Linear Issue whose title starts with `[WI-XXX]`."""
        query = """
        query Issues($teamKey: String!, $title: String!) {
          issues(
            filter: {
              team: { key: { eq: $teamKey } },
              title: { containsIgnoreCase: $title }
            },
            first: 5
          ) {
            nodes {
              id identifier title description url
              state { name type }
              labels { nodes { name } }
            }
          }
        }
        """
        data = self.request(query, {"teamKey": team_key, "title": wi_id})
        nodes = data.get("issues", {}).get("nodes", [])
        # Exact match: title contains "[WI-XXX]" prefix
        for node in nodes:
            if f"[{wi_id}]" in node["title"] or node["title"].startswith(wi_id):
                return _issue_from_node(node)
        return None

    def create_issue(
        self,
        team_id: str,
        title: str,
        description: str,
        label_ids: Optional[List[str]] = None,
        project_id: Optional[str] = None,
    ) -> LinearIssue:
        query = """
        mutation CreateIssue($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id identifier title description url
              state { name type }
              labels { nodes { name } }
            }
          }
        }
        """
        vars_: Dict[str, Any] = {
            "teamId": team_id,
            "title": title,
            "description": description,
        }
        if label_ids:
            vars_["labelIds"] = label_ids
        if project_id:
            vars_["projectId"] = project_id
        data = self.request(query, {"input": vars_})
        result = data.get("issueCreate", {})
        if not result.get("success"):
            raise LinearAPIError(f"issueCreate failed: {result}")
        return _issue_from_node(result["issue"])

    def add_comment(self, issue_id: str, body: str) -> str:
        query = """
        mutation CommentCreate($input: CommentCreateInput!) {
          commentCreate(input: $input) { success comment { id } }
        }
        """
        data = self.request(query, {"input": {"issueId": issue_id, "body": body}})
        result = data.get("commentCreate", {})
        if not result.get("success"):
            raise LinearAPIError(f"commentCreate failed: {result}")
        return result["comment"]["id"]

    def transition_issue(self, issue_id: str, state_id: str) -> None:
        query = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) { success }
        }
        """
        data = self.request(query, {"id": issue_id, "input": {"stateId": state_id}})
        if not data.get("issueUpdate", {}).get("success"):
            raise LinearAPIError("issueUpdate(stateId) failed")

    # -- Project CRUD ----------------------------------------------------------

    def list_projects(self, team_id: str) -> List[Dict[str, Any]]:
        query = """
        query Projects($teamId: String!) {
          projects(filter: { accessibleTeams: { id: { eq: $teamId } } }, first: 100) {
            nodes { id name description url state }
          }
        }
        """
        data = self.request(query, {"teamId": team_id})
        return data.get("projects", {}).get("nodes", [])

    def find_project_by_name(self, team_id: str, name: str) -> Optional[Dict[str, Any]]:
        for proj in self.list_projects(team_id):
            if proj.get("name") == name:
                return proj
        return None

    def create_project(self, team_id: str, name: str, description: str = "") -> Dict[str, Any]:
        query = """
        mutation CreateProject($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            success
            project { id name description url state }
          }
        }
        """
        vars_: Dict[str, Any] = {
            "teamIds": [team_id],
            "name": name,
        }
        if description:
            vars_["description"] = description
        data = self.request(query, {"input": vars_})
        result = data.get("projectCreate", {})
        if not result.get("success"):
            raise LinearAPIError(f"projectCreate failed: {result}")
        return result["project"]


def _issue_from_node(node: Dict[str, Any]) -> LinearIssue:
    labels = [lbl["name"] for lbl in node.get("labels", {}).get("nodes", [])]
    return LinearIssue(
        id=node["id"],
        identifier=node["identifier"],
        title=node["title"],
        description=node.get("description", "") or "",
        state_name=node.get("state", {}).get("name", ""),
        url=node.get("url", ""),
        labels=labels,
    )


# =============================================================================
# Run / WI artifact parsing
# =============================================================================


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def parse_wi_definition(feature_dir: Path, wi_id: str) -> Dict[str, Any]:
    """Parse work_items/<wi>.md frontmatter to dict."""
    wi_path = feature_dir / "work_items" / f"{wi_id}.md"
    if not wi_path.exists():
        return {}
    text = _read_text(wi_path)
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if not match or yaml is None:
        return {}
    try:
        data = yaml.safe_load(match.group(1))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_state(feature_dir: Path) -> Dict[str, Any]:
    state_path = feature_dir / "state" / "state.yaml"
    if yaml is None or not state_path.exists():
        return {}
    try:
        return yaml.safe_load(_read_text(state_path)) or {}
    except Exception:
        return {}


def save_state(feature_dir: Path, state: Dict[str, Any]) -> None:
    state_path = feature_dir / "state" / "state.yaml"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if yaml is None:  # pragma: no cover
        raise LinearAPIError("PyYAML is required to update state.yaml")
    state_path.write_text(
        yaml.safe_dump(state, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def update_state_linear_id(feature_dir: Path, wi_id: str, issue_identifier: str) -> bool:
    """Set work_items[wi_id].linear_issue_id. Returns True on change."""
    state = load_state(feature_dir)
    wis = state.get("work_items") or []
    changed = False
    for entry in wis:
        if isinstance(entry, dict) and entry.get("wi_id") == wi_id:
            if entry.get("linear_issue_id") != issue_identifier:
                entry["linear_issue_id"] = issue_identifier
                changed = True
            break
    else:
        wis.append({"wi_id": wi_id, "linear_issue_id": issue_identifier})
        state["work_items"] = wis
        changed = True
    if changed:
        save_state(feature_dir, state)
    return changed


def get_state_linear_id(feature_dir: Path, wi_id: str) -> Optional[str]:
    state = load_state(feature_dir)
    for entry in state.get("work_items") or []:
        if isinstance(entry, dict) and entry.get("wi_id") == wi_id:
            return entry.get("linear_issue_id")
    return None


def summarise_markdown(path: Path, max_lines: int = 40) -> str:
    text = _read_text(path)
    if not text:
        return f"_(missing: {path.name})_"
    lines = [ln.rstrip() for ln in text.splitlines()]
    # Strip YAML frontmatter if present
    if lines and lines[0].strip() == "---":
        end = next((i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---"), 0)
        if end:
            lines = lines[end + 1 :]
    content = [ln for ln in lines if ln.strip()][:max_lines]
    summary = "\n".join(content)
    if len(content) == max_lines:
        summary += f"\n\n_(truncated, see {path.name})_"
    return summary or f"_(empty: {path.name})_"


def build_issue_title(wi_id: str, wi: Dict[str, Any]) -> str:
    title = wi.get("title") or wi_id
    return f"[{wi_id}] {title}"


def build_issue_description(feature_dir: Path, wi_id: str, wi: Dict[str, Any]) -> str:
    feature_name = feature_dir.name
    mode = wi.get("mode", "—")
    risk = ", ".join(wi.get("risk_flags", []) or []) or "—"
    tier = wi.get("coverage_tier") or load_state(feature_dir).get("coverage_tier") or "—"
    spec_refs = ", ".join(wi.get("spec_refs", []) or []) or "—"
    dod = "\n".join(f"- {d}" for d in (wi.get("dod") or [])) or "_(define DoD)_"
    intent = wi.get("intent") or wi.get("description") or "_(no intent captured)_"
    return (
        f"## Tecnos-STRIDE Work Item\n\n"
        f"- **WI**: `{wi_id}`\n"
        f"- **Feature**: `{feature_name}`\n"
        f"- **Mode**: `{mode}`  |  **Coverage Tier**: `{tier}`\n"
        f"- **Risk Flags**: {risk}\n"
        f"- **Spec Refs**: {spec_refs}\n\n"
        f"### Intent\n{intent}\n\n"
        f"### Definition of Done\n{dod}\n\n"
        f"---\n"
        f"_This Linear Issue mirrors the SDD WI execution trail._\n"
        f"_Run artefacts (walkthrough / findings / lessons) are posted as comments by `stride linear sync`._"
    )


def build_findings_comment(run_dir: Path) -> str:
    findings = run_dir / ".planning" / "findings.md"
    return (
        "## 🔎 Findings (from `.planning/findings.md`)\n\n"
        f"_Run: `{run_dir.name}`_\n\n"
        f"{summarise_markdown(findings)}"
    )


def build_evidence_comment(run_dir: Path) -> str:
    walkthrough = run_dir / "walkthrough.md"
    test_results = run_dir / "test_results.md"
    return (
        "## 🧪 Run Evidence\n\n"
        f"_Run: `{run_dir.name}`_\n\n"
        "### Walkthrough\n"
        f"{summarise_markdown(walkthrough, max_lines=50)}\n\n"
        "### Test Results\n"
        f"{summarise_markdown(test_results, max_lines=30)}"
    )


def build_lessons_comment(run_dir: Path) -> str:
    lessons = run_dir / ".planning" / "lessons.md"
    return (
        "## 📚 Lessons Learned\n\n"
        f"_Run: `{run_dir.name}`_\n\n"
        f"{summarise_markdown(lessons, max_lines=60)}"
    )


# =============================================================================
# Bridge orchestration helpers
# =============================================================================


def env_api_key() -> Optional[str]:
    return os.environ.get("LINEAR_API_KEY")


def env_team_key() -> str:
    return os.environ.get("LINEAR_TEAM_KEY", DEFAULT_TEAM_KEY)


def env_project_id() -> Optional[str]:
    return os.environ.get("LINEAR_PROJECT_ID") or None


# =============================================================================
# Project-level Linear binding (memory/linear.yaml)
# =============================================================================


def find_repo_root(start: Optional[Path] = None) -> Path:
    """Walk up from start to find repo root (markers: memory/, sdd-templates/, .git)."""
    p = (start or Path.cwd()).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "memory").is_dir() or (candidate / "sdd-templates").is_dir() or (candidate / ".git").is_dir():
            return candidate
    return p


def linear_config_path(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or find_repo_root()
    return root / "memory" / "linear.yaml"


def load_linear_config(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    path = linear_config_path(repo_root)
    if yaml is None or not path.exists():
        return {}
    try:
        return yaml.safe_load(_read_text(path)) or {}
    except Exception:
        return {}


def save_linear_config(cfg: Dict[str, Any], repo_root: Optional[Path] = None) -> Path:
    if yaml is None:
        raise LinearAPIError("PyYAML is required to write memory/linear.yaml")
    path = linear_config_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# memory/linear.yaml — Linear integration binding for this STRIDE project (v5.3.1)\n"
        "# Auto-managed by `stride linear project` subcommands. Safe to hand-edit.\n"
        "# This file is project-wide SSoT; per-feature state lives in specs/*/state/state.yaml\n"
    )
    path.write_text(header + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def resolve_project_id(repo_root: Optional[Path] = None) -> Optional[str]:
    """Resolve Linear Project ID with precedence: env > memory/linear.yaml > None."""
    env = env_project_id()
    if env:
        return env
    cfg = load_linear_config(repo_root)
    pid = cfg.get("project_id")
    return pid if pid else None


def should_skip_gracefully() -> Optional[str]:
    """Return a human-readable reason when Linear integration must be skipped."""
    if not env_api_key():
        return "LINEAR_API_KEY unset — skipping Linear sync (no error)."
    return None


def find_run_dir(feature_dir: Path, wi_id: str, explicit: Optional[Path] = None) -> Optional[Path]:
    if explicit is not None:
        return explicit if explicit.exists() else None
    runs_dir = feature_dir / "runs" / wi_id
    if not runs_dir.exists():
        return None
    candidates = sorted(p for p in runs_dir.iterdir() if p.is_dir() and p.name.startswith("RUN-"))
    return candidates[-1] if candidates else None


def find_feature_and_wi(run_dir: Path) -> Tuple[Path, str]:
    """run_dir = <feature>/runs/<WI-ID>/RUN-YYYYMMDD-HHMM/ を分解。"""
    wi_dir = run_dir.parent
    feature_dir = wi_dir.parent.parent
    return feature_dir, wi_dir.name


def resolve_state_for_transition(states: List[LinearWorkflowState], target: str) -> LinearWorkflowState:
    target_lower = target.lower()
    for s in states:
        if s.name.lower() == target_lower:
            return s
    type_map = {"Todo": "unstarted", "In Progress": "started", "Done": "completed", "Canceled": "canceled"}
    wanted_type = type_map.get(target, None)
    if wanted_type:
        for s in states:
            if s.type == wanted_type:
                return s
    raise LinearAPIError(f"workflow state '{target}' not found")


# =============================================================================
# Subcommand implementations
# =============================================================================


def cmd_init(args: argparse.Namespace) -> int:
    feature_dir = Path(args.feature_dir)
    wi_id = args.wi_id
    wi = parse_wi_definition(feature_dir, wi_id)
    title = build_issue_title(wi_id, wi)
    description = build_issue_description(feature_dir, wi_id, wi)
    if args.dry_run:
        print(f"[dry-run] would create Linear Issue title={title!r}")
        print(description[:200] + ("..." if len(description) > 200 else ""))
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    client = LinearClient(env_api_key() or "")
    team = client.get_team(env_team_key())
    existing = client.find_issue_by_wi(team.key, wi_id)
    if existing:
        issue = existing
        print(f"✓ found existing Linear Issue: {issue.identifier}  ({issue.state_name})")
    else:
        pid = resolve_project_id(find_repo_root(feature_dir))
        issue = client.create_issue(
            team_id=team.id,
            title=title,
            description=description,
            project_id=pid,
        )
        if pid:
            print(f"✓ created Linear Issue: {issue.identifier}  (→ project={pid}, {issue.url})")
        else:
            print(f"✓ created Linear Issue: {issue.identifier}  ({issue.url})")
    update_state_linear_id(feature_dir, wi_id, issue.identifier)
    return EXIT_OK


def _resolve_run_target(args: argparse.Namespace) -> Optional[Tuple[Path, str, Path]]:
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"⚠ run_dir not found: {run_dir}", file=sys.stderr)
        return None
    feature_dir, wi_id = find_feature_and_wi(run_dir)
    return feature_dir, wi_id, run_dir


def _post_comment(feature_dir: Path, wi_id: str, body: str, args: argparse.Namespace) -> int:
    issue_identifier = get_state_linear_id(feature_dir, wi_id)
    if args.dry_run:
        target = issue_identifier or "(issue unknown — run `stride linear init` first)"
        print(f"[dry-run] would post to {target}:\n{body[:200]}...")
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    if not issue_identifier:
        print(
            f"⚠ state.yaml に linear_issue_id がありません（wi={wi_id}）。先に 'stride linear init' を実行してください。",
            file=sys.stderr,
        )
        return EXIT_NOT_FOUND
    client = LinearClient(env_api_key() or "")
    issue = client.find_issue_by_wi(env_team_key(), wi_id)
    if not issue:
        print(f"⚠ Linear Issue {issue_identifier} not found via team/title lookup.", file=sys.stderr)
        return EXIT_NOT_FOUND
    client.add_comment(issue.id, body)
    print(f"✓ commented on {issue.identifier}")
    return EXIT_OK


def cmd_findings(args: argparse.Namespace) -> int:
    target = _resolve_run_target(args)
    if target is None:
        return EXIT_NOT_FOUND
    feature_dir, wi_id, run_dir = target
    return _post_comment(feature_dir, wi_id, build_findings_comment(run_dir), args)


def cmd_evidence(args: argparse.Namespace) -> int:
    target = _resolve_run_target(args)
    if target is None:
        return EXIT_NOT_FOUND
    feature_dir, wi_id, run_dir = target
    return _post_comment(feature_dir, wi_id, build_evidence_comment(run_dir), args)


def cmd_learn(args: argparse.Namespace) -> int:
    target = _resolve_run_target(args)
    if target is None:
        return EXIT_NOT_FOUND
    feature_dir, wi_id, run_dir = target
    return _post_comment(feature_dir, wi_id, build_lessons_comment(run_dir), args)


def cmd_sync(args: argparse.Namespace) -> int:
    target = _resolve_run_target(args)
    if target is None:
        return EXIT_NOT_FOUND
    feature_dir, wi_id, run_dir = target
    body_parts: List[str] = []
    if (run_dir / ".planning" / "findings.md").exists():
        body_parts.append(build_findings_comment(run_dir))
    if (run_dir / "walkthrough.md").exists() or (run_dir / "test_results.md").exists():
        body_parts.append(build_evidence_comment(run_dir))
    if (run_dir / ".planning" / "lessons.md").exists():
        body_parts.append(build_lessons_comment(run_dir))
    if not body_parts:
        print("⚠ Run に同期可能な成果物がありません (findings/evidence/lessons 全て不在)")
        return EXIT_OK
    body = "\n\n---\n\n".join(body_parts)
    # _post_comment handles dry-run preview (no API key needed) and graceful skip.
    return _post_comment(feature_dir, wi_id, body, args)


def cmd_close(args: argparse.Namespace) -> int:
    feature_dir = Path(args.feature_dir)
    wi_id = args.wi_id
    if args.dry_run:
        print(f"[dry-run] would transition {wi_id} → {args.state or 'Done'}")
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    client = LinearClient(env_api_key() or "")
    team = client.get_team(env_team_key())
    issue = client.find_issue_by_wi(team.key, wi_id)
    if not issue:
        print(f"⚠ Linear Issue for {wi_id} not found.", file=sys.stderr)
        return EXIT_NOT_FOUND
    states = client.list_workflow_states(team.id)
    target_state = resolve_state_for_transition(states, args.state or "Done")
    client.transition_issue(issue.id, target_state.id)
    print(f"✓ {issue.identifier} → {target_state.name}")
    return EXIT_OK


def cmd_project_create(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    name = args.name
    description = args.description or f"Tecnos-STRIDE project: {name}"
    if args.dry_run:
        print(f"[dry-run] would create Linear Project name={name!r} in team={env_team_key()}")
        print(f"[dry-run] would persist to {linear_config_path(repo_root)}")
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    client = LinearClient(env_api_key() or "")
    team = client.get_team(env_team_key())
    existing = client.find_project_by_name(team.id, name)
    if existing:
        proj = existing
        print(f"✓ found existing Linear Project: {proj['name']}  (id={proj['id']})")
    else:
        proj = client.create_project(team.id, name, description)
        print(f"✓ created Linear Project: {proj['name']}  ({proj.get('url') or proj['id']})")
    cfg = load_linear_config(repo_root)
    cfg.update({
        "team_key": team.key,
        "project_id": proj["id"],
        "project_name": proj["name"],
        "url": proj.get("url", ""),
    })
    path = save_linear_config(cfg, repo_root)
    print(f"✓ persisted → {path}")
    return EXIT_OK


def cmd_project_list(args: argparse.Namespace) -> int:
    if args.dry_run:
        print("[dry-run] would list Linear Projects for team", env_team_key())
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    client = LinearClient(env_api_key() or "")
    team = client.get_team(env_team_key())
    projs = client.list_projects(team.id)
    if not projs:
        print("(no projects)")
        return EXIT_OK
    for p in projs:
        print(f"  {p['id']}  {p['name']}  [{p.get('state', '')}]")
    return EXIT_OK


def cmd_project_use(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    project_id = args.project_id
    if args.dry_run:
        print(f"[dry-run] would bind Linear Project id={project_id!r} in {linear_config_path(repo_root)}")
        return EXIT_OK
    cfg = load_linear_config(repo_root)
    cfg.update({"team_key": env_team_key(), "project_id": project_id})
    path = save_linear_config(cfg, repo_root)
    print(f"✓ bound Linear Project {project_id} → {path}")
    return EXIT_OK


def cmd_project_status(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    cfg = load_linear_config(repo_root)
    path = linear_config_path(repo_root)
    if not cfg:
        print(f"(not configured — {path} missing or empty)")
        print("Run: stride linear project create <name>   or   stride linear project use <project_id>")
        return EXIT_OK
    print(f"Config: {path}")
    for k, v in cfg.items():
        print(f"  {k}: {v}")
    resolved = resolve_project_id(repo_root)
    if os.environ.get("LINEAR_PROJECT_ID"):
        print(f"(note: LINEAR_PROJECT_ID env overrides memory/linear.yaml → {resolved})")
    return EXIT_OK


def cmd_status(args: argparse.Namespace) -> int:
    feature_dir = Path(args.feature_dir)
    state = load_state(feature_dir)
    wi_filter = args.wi_id
    rows: List[Tuple[str, str]] = []
    for entry in state.get("work_items") or []:
        if not isinstance(entry, dict):
            continue
        wi_id = entry.get("wi_id")
        if wi_filter and wi_id != wi_filter:
            continue
        rows.append((wi_id or "?", entry.get("linear_issue_id") or "—"))
    if not rows:
        print("⚠ work_items が空です。")
        return EXIT_OK
    width = max(len(r[0]) for r in rows)
    for wi_id, linear_id in rows:
        print(f"  {wi_id.ljust(width)}  → {linear_id}")
    return EXIT_OK


# =============================================================================
# CLI entry
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="linear_bridge", description="Sync STRIDE Run artefacts to Linear")
    p.add_argument("--dry-run", action="store_true", help="print intended actions; no API calls")
    p.add_argument("--test", action="store_true", help="run self-tests")
    sub = p.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="create/find Linear Issue for WI")
    p_init.add_argument("feature_dir")
    p_init.add_argument("wi_id")
    p_init.set_defaults(handler=cmd_init)

    for name, handler in (("findings", cmd_findings), ("evidence", cmd_evidence), ("learn", cmd_learn), ("sync", cmd_sync)):
        sp = sub.add_parser(name, help=f"post {name} comment to Linear")
        sp.add_argument("run_dir")
        sp.set_defaults(handler=handler)

    p_close = sub.add_parser("close", help="transition Linear Issue state")
    p_close.add_argument("feature_dir")
    p_close.add_argument("wi_id")
    p_close.add_argument("--state", default="Done", help="target state name (default: Done)")
    p_close.set_defaults(handler=cmd_close)

    p_status = sub.add_parser("status", help="show WI → Linear Issue mapping")
    p_status.add_argument("feature_dir")
    p_status.add_argument("wi_id", nargs="?")
    p_status.set_defaults(handler=cmd_status)

    # project subcommand group (v5.3.1)
    p_proj = sub.add_parser("project", help="manage Linear Project binding")
    proj_sub = p_proj.add_subparsers(dest="project_command")
    p_pc = proj_sub.add_parser("create", help="create a Linear Project")
    p_pc.add_argument("name")
    p_pc.add_argument("--description", default=None)
    p_pc.set_defaults(handler=cmd_project_create)
    p_pl = proj_sub.add_parser("list", help="list Linear Projects for team")
    p_pl.set_defaults(handler=cmd_project_list)
    p_pu = proj_sub.add_parser("use", help="bind an existing Linear Project")
    p_pu.add_argument("project_id")
    p_pu.set_defaults(handler=cmd_project_use)
    p_ps = proj_sub.add_parser("status", help="show current project binding")
    p_ps.set_defaults(handler=cmd_project_status)
    p_proj.set_defaults(handler=lambda a: (p_proj.print_help() or EXIT_ERROR))

    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.test:
        return _run_self_tests()
    if not getattr(args, "command", None):
        parser.print_help()
        return EXIT_ERROR
    try:
        return args.handler(args)
    except LinearAPIError as exc:
        print(f"✗ Linear API error: {exc}", file=sys.stderr)
        return EXIT_ERROR


# =============================================================================
# Self-tests (offline, mock-based)
# =============================================================================


class _Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_env = {
            "LINEAR_API_KEY": os.environ.get("LINEAR_API_KEY"),
            "LINEAR_TEAM_KEY": os.environ.get("LINEAR_TEAM_KEY"),
        }
        os.environ["LINEAR_API_KEY"] = "test-key"
        os.environ["LINEAR_TEAM_KEY"] = "TEC"

    def tearDown(self) -> None:
        for k, v in self._orig_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # -- env handling --------------------------------------------------------

    def test_env_defaults(self):
        self.assertEqual(env_team_key(), "TEC")
        self.assertEqual(env_api_key(), "test-key")

    def test_should_skip_when_no_key(self):
        os.environ.pop("LINEAR_API_KEY", None)
        self.assertIsNotNone(should_skip_gracefully())

    # -- markdown summarisation ---------------------------------------------

    def test_summarise_strips_frontmatter(self):
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("---\nkey: value\n---\nHello\n\n")
            f.write("second line\n")
            path = Path(f.name)
        try:
            summary = summarise_markdown(path)
            self.assertIn("Hello", summary)
            self.assertNotIn("key: value", summary)
        finally:
            path.unlink()

    def test_summarise_missing_file(self):
        self.assertIn("missing", summarise_markdown(Path("/nonexistent.md")))

    # -- state.yaml round-trip ---------------------------------------------

    def test_update_state_linear_id_adds_entry(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            feat = Path(d)
            (feat / "state").mkdir()
            (feat / "state" / "state.yaml").write_text(
                "feature: FEAT-X\nwork_items: []\n", encoding="utf-8"
            )
            changed = update_state_linear_id(feat, "WI-001", "TEC-42")
            self.assertTrue(changed)
            reload = load_state(feat)
            self.assertEqual(reload["work_items"][0]["linear_issue_id"], "TEC-42")

    def test_update_state_linear_id_idempotent(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            feat = Path(d)
            (feat / "state").mkdir()
            (feat / "state" / "state.yaml").write_text(
                "feature: FEAT-X\nwork_items:\n  - wi_id: WI-001\n    linear_issue_id: TEC-42\n",
                encoding="utf-8",
            )
            self.assertFalse(update_state_linear_id(feat, "WI-001", "TEC-42"))

    def test_get_state_linear_id_missing(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            feat = Path(d)
            (feat / "state").mkdir()
            (feat / "state" / "state.yaml").write_text("work_items: []\n", encoding="utf-8")
            self.assertIsNone(get_state_linear_id(feat, "WI-X"))

    # -- issue body builders ------------------------------------------------

    def test_build_issue_title(self):
        self.assertEqual(
            build_issue_title("WI-ERP-001", {"title": "Order register"}),
            "[WI-ERP-001] Order register",
        )

    def test_build_issue_title_fallback(self):
        self.assertEqual(build_issue_title("WI-X", {}), "[WI-X] WI-X")

    def test_build_issue_description_includes_wi_id(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            feat = Path(d)
            (feat / "state").mkdir()
            (feat / "state" / "state.yaml").write_text("coverage_tier: standard\n", encoding="utf-8")
            desc = build_issue_description(feat, "WI-E2E", {"mode": "confirm", "risk_flags": ["new_api"]})
            self.assertIn("WI-E2E", desc)
            self.assertIn("confirm", desc)
            self.assertIn("new_api", desc)

    # -- GraphQL client -----------------------------------------------------

    def test_client_requires_api_key(self):
        with self.assertRaises(LinearAPIError):
            LinearClient("")

    def test_client_raises_on_graphql_errors(self):
        client = LinearClient("test-key")
        with mock.patch("urllib.request.urlopen") as mocked:
            resp = mock.MagicMock()
            resp.read.return_value = json.dumps({"errors": [{"message": "boom"}]}).encode()
            resp.__enter__.return_value = resp
            mocked.return_value = resp
            with self.assertRaises(LinearAPIError):
                client.request("{}", {})

    def test_find_issue_by_wi_matches_prefix(self):
        client = LinearClient("test-key")
        with mock.patch.object(
            client,
            "request",
            return_value={
                "issues": {
                    "nodes": [
                        {
                            "id": "abc",
                            "identifier": "TEC-1",
                            "title": "[WI-ERP-001] Order register",
                            "description": "",
                            "url": "https://linear.app/.../TEC-1",
                            "state": {"name": "Todo", "type": "unstarted"},
                            "labels": {"nodes": []},
                        }
                    ]
                }
            },
        ):
            issue = client.find_issue_by_wi("TEC", "WI-ERP-001")
            self.assertIsNotNone(issue)
            self.assertEqual(issue.identifier, "TEC-1")

    def test_find_issue_by_wi_no_match(self):
        client = LinearClient("test-key")
        with mock.patch.object(client, "request", return_value={"issues": {"nodes": []}}):
            self.assertIsNone(client.find_issue_by_wi("TEC", "WI-MISSING"))

    def test_create_issue_surfaces_failure(self):
        client = LinearClient("test-key")
        with mock.patch.object(
            client, "request", return_value={"issueCreate": {"success": False, "issue": None}}
        ):
            with self.assertRaises(LinearAPIError):
                client.create_issue("team-id", "title", "desc")

    # -- state transitions --------------------------------------------------

    def test_resolve_state_by_name(self):
        states = [
            LinearWorkflowState(id="1", name="Todo", type="unstarted"),
            LinearWorkflowState(id="2", name="Done", type="completed"),
        ]
        self.assertEqual(resolve_state_for_transition(states, "Done").id, "2")

    def test_resolve_state_by_type_fallback(self):
        states = [
            LinearWorkflowState(id="3", name="Completed", type="completed"),
        ]
        self.assertEqual(resolve_state_for_transition(states, "Done").id, "3")

    def test_resolve_state_unknown(self):
        with self.assertRaises(LinearAPIError):
            resolve_state_for_transition([], "Done")

    # -- Run dir resolution -------------------------------------------------

    def test_find_feature_and_wi_from_run(self):
        run = Path("/tmp/specs/FEAT-X/runs/WI-001/RUN-20260419-0900")
        feat, wi = find_feature_and_wi(run)
        self.assertEqual(wi, "WI-001")
        self.assertEqual(feat.name, "FEAT-X")


def _run_self_tests() -> int:
    print("Running linear_bridge.py self-tests...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_Tests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\n{result.testsRun}/{result.testsRun} tests run; failures={len(result.failures)}, errors={len(result.errors)}")
    return EXIT_OK if result.wasSuccessful() else EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
