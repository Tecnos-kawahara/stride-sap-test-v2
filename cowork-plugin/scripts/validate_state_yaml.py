#!/usr/bin/env python3
"""validate_state_yaml.py — state.yaml Phase 2-4 + Final schema 検証 (Phase F WI-VALF01-014 同梱)

Cowork Plugin v0.2.0-stable で Phase F WI-VALF01-010 が拡張した state.yaml schema
(phase_2 / phase_3 / phase_4 / final) を機械検証する補助スクリプト。

`tests/test_cowork_plugin_state_yaml_phases.py` と同じ判定ロジックを CLI から
呼び出せるようにし、コンサル環境でも `python3 cowork-plugin/scripts/validate_state_yaml.py
specs/<feature>/state/state.yaml` で検証可能にする。

Usage:
    python3 cowork-plugin/scripts/validate_state_yaml.py specs/val_f01/state/state.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    print("ERROR: 'pyyaml' module not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


VALID_STATUS = ("not_started", "in_progress", "completed")


def validate(path: Path) -> list[str]:
    """Return a list of error messages. Empty list = OK."""
    errors: list[str] = []
    if not path.is_file():
        return [f"state.yaml not found: {path}"]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [f"state.yaml YAML parse error: {exc}"]

    # phase_2
    if "phase_2" not in data:
        errors.append("phase_2 セクション欠落")
    else:
        p2 = data["phase_2"]
        for k in ("status", "spec_md_done", "plan_md_done", "contracts_done", "approved_at"):
            if k not in p2:
                errors.append(f"phase_2.{k} 欠落")
        if isinstance(p2.get("status"), str) and p2["status"] not in VALID_STATUS:
            errors.append(f"phase_2.status 不正値: {p2['status']}")

    # phase_3
    if "phase_3" not in data:
        errors.append("phase_3 セクション欠落")
    else:
        p3 = data["phase_3"]
        for k in ("status", "tasks_md_done", "work_items_count", "approved_at"):
            if k not in p3:
                errors.append(f"phase_3.{k} 欠落")
        if isinstance(p3.get("status"), str) and p3["status"] not in VALID_STATUS:
            errors.append(f"phase_3.status 不正値: {p3['status']}")
        if "work_items_count" in p3 and (
            not isinstance(p3["work_items_count"], int) or p3["work_items_count"] < 0
        ):
            errors.append(f"phase_3.work_items_count は非負 int 必須")

    # phase_4
    if "phase_4" not in data:
        errors.append("phase_4 セクション欠落")
    else:
        p4 = data["phase_4"]
        for k in ("status", "wi_total", "wi_completed", "wi_in_progress", "approved_at"):
            if k not in p4:
                errors.append(f"phase_4.{k} 欠落")
        if isinstance(p4.get("status"), str) and p4["status"] not in VALID_STATUS:
            errors.append(f"phase_4.status 不正値: {p4['status']}")
        wi_total = p4.get("wi_total", 0)
        wi_completed = p4.get("wi_completed", 0)
        if isinstance(wi_total, int) and isinstance(wi_completed, int):
            if wi_completed > wi_total:
                errors.append(
                    f"phase_4.wi_completed ({wi_completed}) > wi_total ({wi_total}) は不正"
                )

    # final
    if "final" not in data:
        errors.append("final セクション欠落")
    else:
        fn = data["final"]
        for k in ("status", "evidence_pack_done", "pr_url", "merged_at"):
            if k not in fn:
                errors.append(f"final.{k} 欠落")
        if isinstance(fn.get("status"), str) and fn["status"] not in VALID_STATUS:
            errors.append(f"final.status 不正値: {fn['status']}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state_yaml", type=Path, help="Path to specs/<feature>/state/state.yaml")
    args = parser.parse_args(argv)

    errors = validate(args.state_yaml)
    if errors:
        print(f"⛔ state.yaml schema 検証 FAILED ({len(errors)} errors):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"✅ {args.state_yaml} state.yaml Phase 2-4 + Final schema OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
