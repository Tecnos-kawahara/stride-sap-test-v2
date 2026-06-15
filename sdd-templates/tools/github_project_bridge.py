#!/usr/bin/env python3
"""github_project_bridge — Tecnos-STRIDE プロジェクト ↔ GitHub Project V2 バインド管理 (v5.3.1)

STRIDE テンプレートをコピーして新規プロジェクトを作るたびに、専用の GitHub
Project V2 を自動作成（または既存を紐付け）し、`memory/github_project.yaml`
に永続化する。既存の `stride_wi_sync.py` / GitHub Actions とは独立した "プロジェクト
レベルの外部トラッカー binding" を担う。

## 責務
- GitHub Project V2 の create / list / use / status を薄くラップ
- 永続化: `memory/github_project.yaml`
- 解決順位: CLI --project-number > GITHUB_PROJECT_NUMBER env > memory file > none

## 認証
- `gh auth status` が OK であること（未認証なら graceful skip, exit 0）

## コマンド
    project create <title> [--owner <owner>] [--description <desc>]
    project list [--owner <owner>]
    project use <project_number> [--owner <owner>]
    project status
    --dry-run / --test
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest import mock

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

EXIT_OK = 0
EXIT_SKIP = 0
EXIT_ERROR = 2


# =============================================================================
# gh CLI wrapper
# =============================================================================


class GhError(RuntimeError):
    pass


def run_gh(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            check=check,
            timeout=60,
        )
    except FileNotFoundError as exc:
        raise GhError("`gh` CLI not found. Install GitHub CLI: https://cli.github.com/") from exc
    except subprocess.CalledProcessError as exc:
        raise GhError(f"gh failed ({exc.returncode}): {exc.stderr.strip()}") from exc
    except subprocess.TimeoutExpired as exc:
        raise GhError(f"gh timeout: {' '.join(args)}") from exc


def gh_authenticated() -> bool:
    try:
        proc = run_gh(["auth", "status"], check=False)
    except GhError:
        return False
    return proc.returncode == 0


def should_skip_gracefully() -> Optional[str]:
    if not gh_authenticated():
        return "`gh` not authenticated — skipping GitHub Project operation (no error). Run `gh auth login`."
    return None


# =============================================================================
# Config persistence
# =============================================================================


def find_repo_root(start: Optional[Path] = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for candidate in [p] + list(p.parents):
        if (candidate / "memory").is_dir() or (candidate / "sdd-templates").is_dir() or (candidate / ".git").is_dir():
            return candidate
    return p


def config_path(repo_root: Optional[Path] = None) -> Path:
    root = repo_root or find_repo_root()
    return root / "memory" / "github_project.yaml"


def load_config(repo_root: Optional[Path] = None) -> Dict[str, Any]:
    path = config_path(repo_root)
    if yaml is None or not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}
    except Exception:
        return {}


def save_config(cfg: Dict[str, Any], repo_root: Optional[Path] = None) -> Path:
    if yaml is None:
        raise GhError("PyYAML is required to write memory/github_project.yaml")
    path = config_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# memory/github_project.yaml — GitHub Project V2 binding for this STRIDE project (v5.3.1)\n"
        "# Auto-managed by `stride project` subcommands. Safe to hand-edit.\n"
        "# Used by: stride_wi_sync.py / sync_projects_to_stride.py / stride-sync workflows\n"
    )
    path.write_text(header + yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


def env_owner() -> Optional[str]:
    return os.environ.get("GITHUB_OWNER") or None


def env_project_number() -> Optional[int]:
    v = os.environ.get("GITHUB_PROJECT_NUMBER")
    try:
        return int(v) if v else None
    except ValueError:
        return None


def resolve_project_number(repo_root: Optional[Path] = None) -> Optional[int]:
    env = env_project_number()
    if env:
        return env
    cfg = load_config(repo_root)
    n = cfg.get("project_number")
    try:
        return int(n) if n else None
    except (TypeError, ValueError):
        return None


# =============================================================================
# Project CRUD via gh CLI
# =============================================================================


def gh_project_create(title: str, owner: Optional[str]) -> Dict[str, Any]:
    args = ["project", "create", "--title", title, "--format", "json"]
    if owner:
        args.extend(["--owner", owner])
    proc = run_gh(args)
    return json.loads(proc.stdout)


def gh_project_list(owner: Optional[str]) -> List[Dict[str, Any]]:
    args = ["project", "list", "--format", "json", "--limit", "100"]
    if owner:
        args.extend(["--owner", owner])
    proc = run_gh(args)
    data = json.loads(proc.stdout)
    return data.get("projects", data) if isinstance(data, dict) else data


def gh_project_view(number: int, owner: Optional[str]) -> Dict[str, Any]:
    args = ["project", "view", str(number), "--format", "json"]
    if owner:
        args.extend(["--owner", owner])
    proc = run_gh(args)
    return json.loads(proc.stdout)


def find_project_by_title(projects: List[Dict[str, Any]], title: str) -> Optional[Dict[str, Any]]:
    for p in projects:
        if p.get("title") == title:
            return p
    return None


# =============================================================================
# Subcommand handlers
# =============================================================================


def cmd_create(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    title = args.title
    owner = args.owner or env_owner()
    if args.dry_run:
        print(f"[dry-run] would create GitHub Project V2 title={title!r} owner={owner or '@me'}")
        print(f"[dry-run] would persist to {config_path(repo_root)}")
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    # Idempotent: look for existing
    try:
        existing = find_project_by_title(gh_project_list(owner), title)
    except GhError as exc:
        print(f"✗ gh list failed: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if existing:
        proj = existing
        print(f"✓ found existing GitHub Project: #{proj.get('number')} {proj.get('title')}")
    else:
        try:
            proj = gh_project_create(title, owner)
        except GhError as exc:
            print(f"✗ gh project create failed: {exc}", file=sys.stderr)
            return EXIT_ERROR
        print(f"✓ created GitHub Project: #{proj.get('number')} {proj.get('title')}  ({proj.get('url') or ''})")
    cfg = load_config(repo_root)
    cfg.update({
        "owner": proj.get("owner", {}).get("login") if isinstance(proj.get("owner"), dict) else owner,
        "project_number": proj.get("number"),
        "project_id": proj.get("id"),
        "project_title": proj.get("title"),
        "url": proj.get("url", ""),
    })
    path = save_config(cfg, repo_root)
    print(f"✓ persisted → {path}")
    return EXIT_OK


def cmd_list(args: argparse.Namespace) -> int:
    owner = args.owner or env_owner()
    if args.dry_run:
        print(f"[dry-run] would list GitHub Projects for owner={owner or '@me'}")
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        return EXIT_SKIP
    try:
        projs = gh_project_list(owner)
    except GhError as exc:
        print(f"✗ gh list failed: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if not projs:
        print("(no projects)")
        return EXIT_OK
    for p in projs:
        print(f"  #{p.get('number')}  {p.get('title')}  {p.get('url', '')}")
    return EXIT_OK


def cmd_use(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    number = int(args.project_number)
    owner = args.owner or env_owner()
    if args.dry_run:
        print(f"[dry-run] would bind GitHub Project #{number} owner={owner or '@me'} in {config_path(repo_root)}")
        return EXIT_OK
    reason = should_skip_gracefully()
    if reason:
        print(f"ℹ {reason}")
        # Still persist what the user gave us; nothing to verify against gh.
    else:
        try:
            proj = gh_project_view(number, owner)
        except GhError as exc:
            print(f"✗ gh view failed: {exc}", file=sys.stderr)
            return EXIT_ERROR
        cfg = load_config(repo_root)
        cfg.update({
            "owner": proj.get("owner", {}).get("login") if isinstance(proj.get("owner"), dict) else owner,
            "project_number": proj.get("number"),
            "project_id": proj.get("id"),
            "project_title": proj.get("title"),
            "url": proj.get("url", ""),
        })
        path = save_config(cfg, repo_root)
        print(f"✓ bound GitHub Project #{number} → {path}")
        return EXIT_OK
    # Fallback persistence when gh unauthenticated
    cfg = load_config(repo_root)
    cfg.update({"owner": owner, "project_number": number})
    path = save_config(cfg, repo_root)
    print(f"✓ persisted project_number={number} → {path} (gh unauthenticated; metadata deferred)")
    return EXIT_OK


def cmd_status(args: argparse.Namespace) -> int:
    repo_root = find_repo_root()
    cfg = load_config(repo_root)
    path = config_path(repo_root)
    if not cfg:
        print(f"(not configured — {path} missing or empty)")
        print("Run: stride project create <title>   or   stride project use <number>")
        return EXIT_OK
    print(f"Config: {path}")
    for k, v in cfg.items():
        print(f"  {k}: {v}")
    resolved = resolve_project_number(repo_root)
    if os.environ.get("GITHUB_PROJECT_NUMBER"):
        print(f"(note: GITHUB_PROJECT_NUMBER env overrides file → {resolved})")
    return EXIT_OK


# =============================================================================
# CLI entry
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="github_project_bridge", description="GitHub Project V2 binding for STRIDE")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--test", action="store_true")
    sub = p.add_subparsers(dest="command")

    p_c = sub.add_parser("create", help="create/find a GitHub Project V2")
    p_c.add_argument("title")
    p_c.add_argument("--owner", default=None, help="GitHub owner (user or org); default: $GITHUB_OWNER or @me")
    p_c.add_argument("--description", default=None)
    p_c.set_defaults(handler=cmd_create)

    p_l = sub.add_parser("list", help="list GitHub Projects V2 for owner")
    p_l.add_argument("--owner", default=None)
    p_l.set_defaults(handler=cmd_list)

    p_u = sub.add_parser("use", help="bind an existing Project")
    p_u.add_argument("project_number")
    p_u.add_argument("--owner", default=None)
    p_u.set_defaults(handler=cmd_use)

    p_s = sub.add_parser("status", help="show current binding")
    p_s.set_defaults(handler=cmd_status)

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
    except GhError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return EXIT_ERROR


# =============================================================================
# Self-tests (offline, mock-based)
# =============================================================================


class _Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_env = {
            "GITHUB_OWNER": os.environ.get("GITHUB_OWNER"),
            "GITHUB_PROJECT_NUMBER": os.environ.get("GITHUB_PROJECT_NUMBER"),
        }
        for k in self._orig_env:
            os.environ.pop(k, None)

    def tearDown(self) -> None:
        for k, v in self._orig_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_resolve_env_wins(self):
        os.environ["GITHUB_PROJECT_NUMBER"] = "42"
        # Even with config present, env should win
        with mock.patch(__name__ + ".load_config", return_value={"project_number": 7}):
            self.assertEqual(resolve_project_number(), 42)

    def test_resolve_file_fallback(self):
        with mock.patch(__name__ + ".load_config", return_value={"project_number": 7}):
            self.assertEqual(resolve_project_number(), 7)

    def test_resolve_none(self):
        with mock.patch(__name__ + ".load_config", return_value={}):
            self.assertIsNone(resolve_project_number())

    def test_find_project_by_title_hit(self):
        projs = [{"title": "a", "number": 1}, {"title": "b", "number": 2}]
        self.assertEqual(find_project_by_title(projs, "b")["number"], 2)

    def test_find_project_by_title_miss(self):
        self.assertIsNone(find_project_by_title([{"title": "a"}], "b"))

    def test_save_and_load_roundtrip(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "memory").mkdir()
            cfg = {"owner": "org", "project_number": 9, "project_title": "STRIDE"}
            save_config(cfg, root)
            reload = load_config(root)
            self.assertEqual(reload["project_number"], 9)
            self.assertEqual(reload["project_title"], "STRIDE")

    def test_skip_when_gh_unauthenticated(self):
        with mock.patch(__name__ + ".gh_authenticated", return_value=False):
            self.assertIsNotNone(should_skip_gracefully())

    def test_skip_when_gh_authenticated(self):
        with mock.patch(__name__ + ".gh_authenticated", return_value=True):
            self.assertIsNone(should_skip_gracefully())

    def test_cmd_status_missing_config(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with mock.patch(__name__ + ".find_repo_root", return_value=Path(d)):
                args = argparse.Namespace()
                self.assertEqual(cmd_status(args), EXIT_OK)

    def test_cmd_create_dry_run(self):
        args = argparse.Namespace(
            title="my-proj", owner="me", description=None, dry_run=True
        )
        self.assertEqual(cmd_create(args), EXIT_OK)


def _run_self_tests() -> int:
    print("Running github_project_bridge.py self-tests...")
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(_Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(f"\n{result.testsRun}/{result.testsRun} tests run; failures={len(result.failures)}, errors={len(result.errors)}")
    return EXIT_OK if result.wasSuccessful() else EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
