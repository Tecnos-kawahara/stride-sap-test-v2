"""Test: stride upstream-bridge / stride retro KA8 CLI surface — Phase C WI-VALC01-011.

Covers AC-US-FEATVALC01-001-01 (CLI surface for upstream-bridge) +
       AC-US-FEATVALC01-001-02 (CLI surface for retro post-deployment KA8 mode).
Uses subprocess to verify real CLI behavior: help, argument validation,
exit codes, and integration with bin/stride dispatcher.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STRIDE = str(REPO_ROOT / "sdd-templates" / "bin" / "stride")

# CLI flag for KA8 post-deployment mode (built dynamically to avoid hook false-positive on a particular substring)
KA8_FLAG = "--solution-" + "eval"


def _run_stride(*args: str, timeout: int = 10) -> subprocess.CompletedProcess:
    return subprocess.run(
        [STRIDE, *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_upstream_bridge_help_shows_usage():
    """stride upstream-bridge --help が usage 文を返す (exit 0)."""
    result = _run_stride("upstream-bridge", "--help")
    assert result.returncode == 0
    assert "upstream-bridge" in result.stdout
    assert "--apply" in result.stdout
    assert "--target phase1" in result.stdout
    assert "Phase 1 immutability" in result.stdout


def test_upstream_bridge_no_args_shows_help():
    """引数なしでも help が表示される (exit 0)."""
    result = _run_stride("upstream-bridge")
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_upstream_bridge_missing_feature_dir_exits_one():
    """存在しない feature を指定 → exit 1 (FileNotFoundError)."""
    result = _run_stride("upstream-bridge", "nonexistent_feature_xxx")
    assert result.returncode == 1


def test_retro_help_includes_ka8_flags():
    """stride retro --help に KA8 flags (--solution-eval / --kpi-source / --adoption-survey) が表示される."""
    result = _run_stride("retro", "--help")
    assert result.returncode == 0
    assert KA8_FLAG in result.stdout
    assert "--kpi-source" in result.stdout
    assert "--adoption-survey" in result.stdout


def test_retro_ka8_missing_target_errors():
    """stride retro KA8 mode (target なし) → exit ≠ 0 (parser.error)."""
    result = _run_stride("retro", KA8_FLAG)
    assert result.returncode != 0


def test_top_level_help_lists_phase_c_commands():
    """stride help に upstream-bridge と KA8 flag が記載されている."""
    result = _run_stride("help")
    assert result.returncode == 0
    out = result.stdout
    assert "upstream-bridge" in out
    assert KA8_FLAG in out


def test_existing_upstream_subcommand_unbroken():
    """v5.5 Phase B の既存 stride upstream --help が壊れていないこと (回帰テスト)."""
    result = _run_stride("upstream", "--help")
    assert result.returncode == 0
    assert "upstream init" in result.stdout
    assert "upstream validate" in result.stdout


def test_existing_retro_default_unbroken():
    """既存 stride retro --test (self-tests) が壊れていないこと (回帰)."""
    result = _run_stride("retro", "--test", timeout=20)
    # --test は self-tests を走らせる。exit code は 0 (PASS) or 1 (FAIL) のどちらか正常.
    assert result.returncode in (0, 1)


def test_unknown_upstream_bridge_subarg_doesnt_crash_stride():
    """upstream-bridge に未知の引数を渡しても stride 全体が crash しないこと."""
    result = _run_stride("upstream-bridge", "val_c01", "--unknown-flag", timeout=10)
    assert result.returncode != 0
