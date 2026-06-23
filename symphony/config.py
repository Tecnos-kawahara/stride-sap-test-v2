"""Configuration loader — parses SYMPHONY.md front-matter + prompt body."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


# ---------------------------------------------------------------------------
# Config dataclass hierarchy
# ---------------------------------------------------------------------------

@dataclass
class TrackerConfig:
    kind: str = "github"
    repo: str = ""
    trigger_label: str = "symphony:ready"
    running_label: str = "symphony:running"
    done_label: str = "symphony:done"
    blocked_label: str = "symphony:blocked"
    failed_label: str = "symphony:failed"


@dataclass
class PollingConfig:
    interval_seconds: int = 60
    max_issues_per_cycle: int = 5


@dataclass
class WorkspaceConfig:
    root: str = ".symphony/workspaces"
    branch_prefix: str = "symphony/"
    strategy: str = "worktree"  # reserved: "worktree" | "copy" (runtime reads root/branch_prefix only)
    base_branch: str = "main"


@dataclass
class ClaudeCodeAgentConfig:
    command: str = "claude"
    args: list[str] = field(default_factory=lambda: ["-p", "--dangerously-skip-permissions"])
    model: Optional[str] = None
    effort_level: Optional[str] = None
    max_output_tokens: Optional[int] = None
    timeout_ms: int = 600_000


@dataclass
class CodexAgentConfig:
    command: str = "codex"
    subcommand: str = "exec"
    args: list[str] = field(default_factory=lambda: ["--full-auto"])
    timeout_ms: int = 600_000


@dataclass
class PhaseRouting:
    engine: str = "claude-code"
    parallel: bool = False
    max_concurrent: int = 4
    reason: str = ""  # documentation-only: explains why this engine was chosen


@dataclass
class ComplexityOverride:
    enabled: bool = False
    high_complexity_engine: str = "claude-code"
    low_complexity_engine: str = "codex"


@dataclass
class RetryConfig:
    max_attempts: int = 3
    backoff_base_ms: int = 10_000
    backoff_max_ms: int = 300_000


@dataclass
class AgentConfig:
    claude_code: ClaudeCodeAgentConfig = field(default_factory=ClaudeCodeAgentConfig)
    codex: CodexAgentConfig = field(default_factory=CodexAgentConfig)
    routing: dict[str, PhaseRouting] = field(default_factory=dict)
    complexity_override: ComplexityOverride = field(default_factory=ComplexityOverride)
    retry: RetryConfig = field(default_factory=RetryConfig)
    max_parallel: int = 4  # deprecated: use routing.*.max_concurrent per phase


@dataclass
class HooksConfig:
    after_create: Optional[str] = None
    before_run: Optional[str] = None
    after_run: Optional[str] = None


@dataclass
class StrideBoardConfig:
    enabled: bool = False
    project: Optional[str] = None
    owner: Optional[str] = None


@dataclass
class ObservabilityConfig:
    log_dir: str = ".symphony/logs"
    structured: bool = True  # reserved: structured logging format toggle
    stride_board: StrideBoardConfig = field(default_factory=StrideBoardConfig)


@dataclass
class JanitorConfig:
    enabled: bool = False
    interval_hours: int = 6
    exclude_recent_pr_days: int = 7
    risk_flags_exclude: list[str] = field(default_factory=lambda: [
        "risk:authz", "risk:pii", "risk:external_api", "risk:sod"
    ])


@dataclass
class SymphonyConfig:
    version: str = "1.0"
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    polling: PollingConfig = field(default_factory=PollingConfig)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    hooks: HooksConfig = field(default_factory=HooksConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    janitor: JanitorConfig = field(default_factory=JanitorConfig)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_dataclass(cls: type, data: dict[str, Any]) -> Any:
    """Recursively construct a dataclass from a dict, ignoring unknown keys."""
    if data is None:
        return cls()
    import dataclasses as _dc
    import typing

    # Resolve type hints properly (handles `from __future__ import annotations`)
    try:
        resolved_hints = typing.get_type_hints(cls)
    except Exception:
        resolved_hints = {}

    field_map = {f.name: f for f in _dc.fields(cls)}
    kwargs: dict[str, Any] = {}
    for key, val in data.items():
        key_clean = key.replace("-", "_")
        if key_clean not in field_map:
            continue
        fld = field_map[key_clean]
        # Use resolved type hint; fall back to raw annotation
        real_type = resolved_hints.get(key_clean, fld.type)
        origin = getattr(real_type, "__origin__", None)
        # If the field type is itself a dataclass, recurse
        if _dc.is_dataclass(real_type) and isinstance(val, dict):
            kwargs[key_clean] = _build_dataclass(real_type, val)
        elif origin is dict and isinstance(val, dict):
            # Special handling for routing dict[str, PhaseRouting]
            args = getattr(real_type, "__args__", None)
            if args and len(args) == 2 and _dc.is_dataclass(args[1]):
                kwargs[key_clean] = {
                    k: _build_dataclass(args[1], v) if isinstance(v, dict) else v
                    for k, v in val.items()
                }
            else:
                kwargs[key_clean] = val
        else:
            kwargs[key_clean] = val
    return cls(**kwargs)


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split a markdown file with YAML front-matter into (yaml_str, body)."""
    text = text.lstrip()
    if not text.startswith("---"):
        raise ValueError("SYMPHONY.md must start with YAML front-matter (---)")
    rest = text[3:]
    end_idx = rest.find("\n---")
    if end_idx == -1:
        raise ValueError("SYMPHONY.md: closing --- not found for front-matter")
    yaml_str = rest[:end_idx]
    body = rest[end_idx + 4:]  # skip \n---
    return yaml_str, body.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ConfigLoader:
    """Loads SYMPHONY.md and supports hot-reload on mtime change."""

    def __init__(self, path: str | Path = "SYMPHONY.md") -> None:
        self._path = Path(path)
        self._mtime: float = 0.0
        self._config: Optional[SymphonyConfig] = None
        self._prompt_template: str = ""

    # -- properties ----------------------------------------------------------
    @property
    def config(self) -> SymphonyConfig:
        self._ensure_loaded()
        assert self._config is not None
        return self._config

    @property
    def prompt_template(self) -> str:
        self._ensure_loaded()
        return self._prompt_template

    # -- internal ------------------------------------------------------------
    def _ensure_loaded(self) -> None:
        current_mtime = self._path.stat().st_mtime
        if self._config is None or current_mtime != self._mtime:
            self._load()
            self._mtime = current_mtime

    def _load(self) -> None:
        raw = self._path.read_text(encoding="utf-8")
        yaml_str, body = _split_frontmatter(raw)
        data = yaml.safe_load(yaml_str) or {}
        self._config = _build_dataclass(SymphonyConfig, data)
        self._prompt_template = body
        self._validate()

    # Valid engine names recognised by runner.run_agent()
    VALID_ENGINES = {"claude-code", "codex"}
    VALID_CLAUDE_CODE_EFFORT_LEVELS = {"low", "medium", "high", "xhigh", "max"}

    def _validate(self) -> None:
        cfg = self._config
        assert cfg is not None

        repo = cfg.tracker.repo
        if repo == "auto":
            repo = self._resolve_repo()
            cfg.tracker.repo = repo
        if not repo or repo == "{{GITHUB_REPO}}":
            raise ValueError(
                "tracker.repo is empty or still set to placeholder '{{GITHUB_REPO}}'. "
                "Please set it to your actual repo (e.g. 'owner/repo'), or use 'auto' "
                "to detect from git remote / GITHUB_REPOSITORY env var."
            )
        if repo.count("/") != 1 or repo.startswith("/") or repo.endswith("/"):
            raise ValueError(
                f"tracker.repo '{repo}' is not in 'owner/repo' format. "
                "Expected exactly one slash, like 'my-org/my-repo'."
            )

        sb = cfg.observability.stride_board
        if sb.enabled:
            if sb.project is None or sb.owner is None:
                raise ValueError(
                    "observability.stride_board.enabled=true requires "
                    "'project' and 'owner' to be set."
                )

        # Validate engine names in routing
        for phase, routing in cfg.agent.routing.items():
            if routing.engine not in self.VALID_ENGINES:
                raise ValueError(
                    f"agent.routing.{phase}.engine '{routing.engine}' is not a "
                    f"valid engine. Must be one of: {sorted(self.VALID_ENGINES)}"
                )

        # Validate complexity_override engine names
        co = cfg.agent.complexity_override
        if co.enabled:
            for attr in ("high_complexity_engine", "low_complexity_engine"):
                engine = getattr(co, attr)
                if engine not in self.VALID_ENGINES:
                    raise ValueError(
                        f"agent.complexity_override.{attr} '{engine}' is not a "
                        f"valid engine. Must be one of: {sorted(self.VALID_ENGINES)}"
                    )

        cc = cfg.agent.claude_code
        if cc.model is not None and not cc.model.strip():
            raise ValueError("agent.claude_code.model must be a non-empty string when set.")
        if cc.effort_level is not None and cc.effort_level not in self.VALID_CLAUDE_CODE_EFFORT_LEVELS:
            raise ValueError(
                "agent.claude_code.effort_level must be one of: "
                f"{sorted(self.VALID_CLAUDE_CODE_EFFORT_LEVELS)}"
            )
        if cc.max_output_tokens is not None and cc.max_output_tokens <= 0:
            raise ValueError("agent.claude_code.max_output_tokens must be a positive integer.")

        # Validate Jinja2 prompt template syntax
        self._validate_prompt_template()

    def _resolve_repo(self) -> str:
        """Resolve repository from environment variable or git remote.

        Resolution order:
          1. GITHUB_REPOSITORY env var (set automatically in GitHub Actions)
          2. git remote origin URL (local development)
        """
        import re
        import subprocess

        # 1. GitHub Actions environment variable
        env_repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
        if env_repo and "/" in env_repo:
            return env_repo

        # 2. git remote origin
        config_dir = str(self._path.resolve().parent) if self._path.parent else "."
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True, text=True, cwd=config_dir,
            )
        except FileNotFoundError:
            raise ValueError(
                "tracker.repo is 'auto' but git is not available. "
                "Install git or set tracker.repo explicitly."
            )

        if result.returncode == 0:
            url = result.stdout.strip()
            # https://github.com/owner/repo.git -> owner/repo
            m = re.search(r"github\.com[/:](.+?)(?:\.git)?$", url)
            if m:
                return m.group(1).rstrip("/")

        raise ValueError(
            "tracker.repo is 'auto' but could not detect repository. "
            "Ensure git remote origin points to a GitHub repo, "
            "or set GITHUB_REPOSITORY env var, "
            "or set tracker.repo explicitly in SYMPHONY.md."
        )

    def _validate_prompt_template(self) -> None:
        """Check that the prompt template is valid Jinja2 syntax."""
        if not self._prompt_template:
            return
        try:
            from jinja2 import Environment, StrictUndefined
            env = Environment(undefined=StrictUndefined)
            env.parse(self._prompt_template)
        except ImportError:
            pass  # Jinja2 not installed — skip syntax check
        except Exception as exc:
            raise ValueError(
                f"Prompt template has invalid Jinja2 syntax: {exc}"
            ) from exc

    def reload(self) -> SymphonyConfig:
        """Force a reload regardless of mtime."""
        self._load()
        self._mtime = self._path.stat().st_mtime
        return self.config
