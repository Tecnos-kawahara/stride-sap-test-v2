"""stride method validate — strict pre-publish gate.

Runs Feature ① checkers (plane_label_completeness + ip_boundary + attribution + audit)
in strict mode. Fails fast on any violation.

Contract: CT-CLI-02. Covers: AC-US-FEATMETHODSTOREPUBLISHING-001-01 (validation portion).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import EXIT_OK, EXIT_PATH_NOT_FOUND, EXIT_VALIDATION_FAILURE


CHECKER_SCRIPTS = [
    ("plane_label_completeness_checker.py", []),
    ("ip_boundary_checker.py", []),
    ("method_labels_checker.py", ["--check"]),
    ("method_audit.py", ["--strict"]),
]


def _run_checker(tools_dir: Path, script: str, extra_args: list[str], root: Path) -> tuple[bool, str]:
    script_path = tools_dir / script
    if not script_path.exists():
        return False, f"checker not found: {script_path}"
    cmd = [sys.executable, str(script_path), *extra_args]
    if "--root" not in extra_args and script != "method_audit.py":
        cmd.extend(["--root", str(root)])
    if script == "method_audit.py":
        cmd.extend(["--root", str(root)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0, proc.stdout + proc.stderr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stride method validate")
    parser.add_argument("--strict", action="store_true", default=True,
                        help="Strict mode (warnings treated as errors). Always on.")
    parser.add_argument("--root", default=".", help="target root directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"Error: root not found: {root}", file=sys.stderr)
        return EXIT_PATH_NOT_FOUND

    tools_dir = Path(__file__).resolve().parent.parent

    results = []
    for script, extra in CHECKER_SCRIPTS:
        ok, output = _run_checker(tools_dir, script, extra, root)
        results.append({"checker": script, "passed": ok, "output_excerpt": output[:500]})

    all_passed = all(r["passed"] for r in results)

    if args.format == "json":
        print(json.dumps({
            "validation_pass": all_passed,
            "strict": True,
            "checkers": results,
        }, ensure_ascii=False, indent=2))
    else:
        print("=== stride method validate (strict) ===")
        for r in results:
            mark = "PASS" if r["passed"] else "FAIL"
            print(f"  [{mark}] {r['checker']}")
        print(f"\nOverall: {'PASS' if all_passed else 'FAIL'}")

    return EXIT_OK if all_passed else EXIT_VALIDATION_FAILURE


if __name__ == "__main__":
    raise SystemExit(main())
