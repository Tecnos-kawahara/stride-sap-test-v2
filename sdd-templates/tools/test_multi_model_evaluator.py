#!/usr/bin/env python3
"""
Self-test for multi_model_evaluator.py (API calls — not for CI).

Usage:
    python3 sdd-templates/tools/test_multi_model_evaluator.py --test
"""

import subprocess
import sys
from pathlib import Path


def main():
    if "--test" not in sys.argv:
        print("Usage: python3 test_multi_model_evaluator.py --test")
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent.parent
    evaluator = project_root / "sdd-templates" / "tools" / "multi_model_evaluator.py"
    sample = project_root / "specs" / "FEAT-ERPSAMPLE"

    if not sample.exists():
        print(f"SKIP: {sample} not found")
        sys.exit(0)

    print("Running self-test: multi_model_evaluator.py --test")
    result = subprocess.run(
        [sys.executable, str(evaluator), "--test"],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"FAIL: exit code {result.returncode}")
        sys.exit(result.returncode)

    print("Self-test passed.")


if __name__ == "__main__":
    main()
