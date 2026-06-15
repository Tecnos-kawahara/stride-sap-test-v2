"""Agent execution — launches Claude Code or Codex as a subprocess."""
from __future__ import annotations

import os
import stat
import subprocess
from typing import NamedTuple, Optional

from symphony.config import ClaudeCodeAgentConfig, SymphonyConfig
from symphony.logger import get_logger

logger = get_logger(__name__)


class AgentResult(NamedTuple):
    """Return value from run_agent."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def run_agent(
    engine: str,
    config: SymphonyConfig,
    workspace_path: str,
    rendered_prompt: str,
    log_path: str,
) -> AgentResult:
    """Launch an agent subprocess and capture its output.

    Args:
        engine: "claude-code" or "codex"
        config: SymphonyConfig for timeout settings
        workspace_path: working directory for the agent
        rendered_prompt: the full prompt string to feed the agent
        log_path: file path to write combined stdout+stderr

    Returns:
        AgentResult with returncode, stdout, stderr, and timed_out flag.
    """
    if engine == "claude-code":
        cc = config.agent.claude_code
        timeout_sec = cc.timeout_ms / 1000
        cmd = _build_claude_code_command(cc)
        input_text = rendered_prompt
        run_kwargs: dict = dict(
            cwd=workspace_path,
            input=input_text,
            capture_output=True,
            env=_build_claude_code_env(cc),
            text=True,
            encoding="utf-8",
            timeout=timeout_sec,
        )
    elif engine == "codex":
        cx = config.agent.codex
        timeout_sec = cx.timeout_ms / 1000
        cwd_path = workspace_path
        # If command is "wsl", convert Windows path to WSL path
        if cx.command == "wsl":
            wsl_result = subprocess.run(
                ["wsl", "--", "wslpath", workspace_path],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if wsl_result.returncode == 0:
                cwd_path = wsl_result.stdout.strip()
        cmd = [cx.command, cx.subcommand] + list(cx.args) + ["-C", cwd_path, rendered_prompt]
        run_kwargs = dict(
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_sec,
        )
    else:
        raise ValueError(f"Unknown engine: {engine}")

    logger.info(
        "Launching %s in %s (timeout=%ds)", engine, workspace_path, int(timeout_sec)
    )

    # Ensure log directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # For WSL-based codex: temporarily convert worktree .git gitdir to WSL path
    gitdir_backup: Optional[str] = None
    if engine == "codex" and config.agent.codex.command == "wsl":
        gitdir_backup = _fix_gitdir_for_wsl(workspace_path)

    try:
        result = subprocess.run(cmd, **run_kwargs)
        _write_log(log_path, result.stdout, result.stderr)
        logger.info(
            "%s exited with code %d for workspace %s",
            engine, result.returncode, workspace_path,
        )
        return AgentResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        _write_log(log_path, stdout, stderr + "\n[TIMEOUT]\n")
        logger.warning(
            "%s timed out after %ds in %s", engine, int(timeout_sec), workspace_path
        )
        return AgentResult(
            returncode=-1,
            stdout=stdout,
            stderr=stderr,
            timed_out=True,
        )
    except FileNotFoundError as exc:
        error_msg = f"Command not found: {cmd[0]} — {exc}"
        _write_log(log_path, "", error_msg)
        logger.error(error_msg)
        return AgentResult(
            returncode=-2,
            stdout="",
            stderr=error_msg,
            timed_out=False,
        )
    finally:
        if gitdir_backup is not None:
            _restore_gitdir(workspace_path, gitdir_backup)


def _fix_gitdir_for_wsl(workspace_path: str) -> Optional[str]:
    """Convert the worktree .git file's gitdir path to WSL format.

    Git worktrees use a .git *file* (not directory) containing a gitdir pointer
    to the main repo.  When the worktree is created on Windows, this path is a
    Windows absolute path (e.g. ``C:/Users/.../.git/worktrees/23``).  WSL-based
    tools cannot resolve that path, so we temporarily rewrite it to a POSIX
    path (``/mnt/c/Users/.../.git/worktrees/23``) before launching the WSL
    agent and restore afterwards.

    Writing is done via WSL (``cat > file``) to avoid Windows/OneDrive
    permission issues on the ``.git`` file.

    Returns the original file content for later restoration, or None if the
    conversion was not applicable / failed.
    """
    git_file = os.path.join(workspace_path, ".git")
    if not os.path.isfile(git_file):
        return None

    try:
        with open(git_file, "r", encoding="utf-8") as f:
            original_content = f.read()

        if not original_content.startswith("gitdir:"):
            return None

        gitdir_path = original_content.split("gitdir:", 1)[1].strip()

        # Convert Windows gitdir path to WSL path
        wsl_result = subprocess.run(
            ["wsl", "--", "wslpath", gitdir_path],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        if wsl_result.returncode != 0:
            logger.warning(
                "wslpath failed for gitdir '%s': %s",
                gitdir_path, wsl_result.stderr.strip(),
            )
            return None

        wsl_gitdir = wsl_result.stdout.strip()

        # Convert workspace path to WSL path for writing
        wsl_ws_result = subprocess.run(
            ["wsl", "--", "wslpath", workspace_path],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        if wsl_ws_result.returncode != 0:
            logger.warning("wslpath failed for workspace: %s", wsl_ws_result.stderr.strip())
            return None

        wsl_git_file = wsl_ws_result.stdout.strip() + "/.git"

        # Write via WSL to bypass Windows/OneDrive file locking
        new_content = f"gitdir: {wsl_gitdir}\n"
        write_result = subprocess.run(
            ["wsl", "--", "bash", "-c", f"cat > '{wsl_git_file}'"],
            input=new_content,
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        if write_result.returncode != 0:
            logger.warning("WSL write to .git failed: %s", write_result.stderr.strip())
            return None

        logger.info("Converted gitdir to WSL path: %s → %s", gitdir_path, wsl_gitdir)
        return original_content
    except Exception as exc:
        logger.warning("Failed to fix gitdir for WSL: %s", exc)
        return None


def _restore_gitdir(workspace_path: str, original_content: str) -> None:
    """Restore the original .git file content after WSL execution."""
    git_file = os.path.join(workspace_path, ".git")
    try:
        # Try Windows-native first
        os.chmod(git_file, stat.S_IREAD | stat.S_IWRITE)
        with open(git_file, "w", encoding="utf-8") as f:
            f.write(original_content)
        logger.debug("Restored original gitdir in %s", git_file)
    except PermissionError:
        # Fall back to WSL write if Windows permissions block us
        try:
            wsl_ws_result = subprocess.run(
                ["wsl", "--", "wslpath", workspace_path],
                capture_output=True, text=True, encoding="utf-8", timeout=10,
            )
            if wsl_ws_result.returncode == 0:
                wsl_git_file = wsl_ws_result.stdout.strip() + "/.git"
                subprocess.run(
                    ["wsl", "--", "bash", "-c", f"cat > '{wsl_git_file}'"],
                    input=original_content,
                    capture_output=True, text=True, encoding="utf-8", timeout=10,
                )
                logger.debug("Restored gitdir via WSL in %s", git_file)
        except Exception as exc2:
            logger.warning("Failed to restore gitdir via WSL: %s", exc2)
    except Exception as exc:
        logger.warning("Failed to restore gitdir in %s: %s", git_file, exc)


def _build_claude_code_command(config: ClaudeCodeAgentConfig) -> list[str]:
    """Construct a Claude Code command with explicit model/effort controls."""
    cmd = [config.command] + list(config.args)
    if config.model:
        cmd.extend(["--model", config.model])
    if config.effort_level:
        cmd.extend(["--effort", config.effort_level])
    return cmd


def _build_claude_code_env(config: ClaudeCodeAgentConfig) -> dict[str, str]:
    """Propagate Claude Code env overrides while preserving the caller environment."""
    env = os.environ.copy()
    if config.max_output_tokens is not None:
        env["CLAUDE_CODE_MAX_OUTPUT_TOKENS"] = str(config.max_output_tokens)
    return env


def _write_log(log_path: str, stdout: str, stderr: str) -> None:
    """Write combined agent output to the log file."""
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("=== STDOUT ===\n")
            f.write(stdout)
            f.write("\n=== STDERR ===\n")
            f.write(stderr)
    except OSError as exc:
        logger.warning("Failed to write log to %s: %s", log_path, exc)
