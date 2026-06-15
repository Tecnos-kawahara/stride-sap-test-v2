#!/usr/bin/env python3
"""Security Checker - Executable security audit for SDD features.

Two scan modes:
  --daily: Lightweight pre-Gate check (high-confidence findings only, >=8/10)
  --audit: Comprehensive pre-Final check (all findings, >=2/10)

Inspired by gstack /cso (garrytan/gstack, MIT License).

Usage:
    python3 stride_security_checker.py <feature_path> --daily
    python3 stride_security_checker.py <feature_path> --audit
    python3 stride_security_checker.py <feature_path> --daily --json
    python3 stride_security_checker.py --test
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_WARN = "WARN"

# Severity -> status mapping
_FAIL_SEVERITIES = {"CRITICAL", "HIGH"}
_WARN_SEVERITIES = {"MEDIUM", "LOW"}

# SEC-004 exclusion patterns
_SECRET_PLACEHOLDERS = {
    "your_api_key", "your_token", "xxx", "changeme", "dummy",
    "example", "sample", "bearer", "jwt", "your-api-key", "your-token", "test",
}

_SECRET_PATTERN = re.compile(
    r"(api[_\-]?key|secret|password|token)\s*[:=]\s*[\"']([^\"']{8,})[\"']",
    re.IGNORECASE,
)

# SEC-006 AI integration trigger keywords (case-insensitive)
_AI_TRIGGER_KEYWORDS = [
    "LLM", "AI agent", "agent integration", "model output",
    "prompt injection", "MCP server", "tool calling",
]

# SEC-006 provenance-only keywords to EXCLUDE from triggering
_PROVENANCE_ONLY_KEYWORDS = [
    "record_provider_surface",
    "record_model_id",
    "record_model_version",
    "record_prompt_version",
    "record_inputs_hash",
    "record_execution_settings",
    "record_budget_controls",
    "record_tokenizer_notes",
    "record_cyber_safeguards_status",
]

# SEC-006 trust boundary — four required facets (ALL must be present)
_TRUST_BOUNDARY_FACETS = {
    "boundary": ["trusted", "untrusted", "trust boundary", "trust_boundary"],
    "input_validation": ["input validation", "input_validation"],
    "output_verification": ["output verification", "output_verification"],
    "fallback": ["fallback", "human escalation"],
}

# SEC-005 audit/correlation keywords
_AUDIT_KEYWORDS = [
    "audit", "監査", "correlation", "Correlation ID", "correlation_id",
    "idempotency", "冪等", "idempotent",
]

# SEC-010 direct ERP DB write patterns
# Word boundary (\b) after system name prevents matching addon tables
# like erp_addon_buffer, sap_local_staging, mcframe_ext_log
_DIRECT_ERP_WRITE_PATTERNS = [
    re.compile(r"direct\s+db\s+write\s+to\s+\w+", re.IGNORECASE),
    re.compile(r"INSERT\s+INTO\s+(mcframe|sap|erp)\b(?!_)", re.IGNORECASE),
    re.compile(r"UPDATE\s+(mcframe|sap|erp)\b(?!_)", re.IGNORECASE),
    re.compile(r"system[\-\s]of[\-\s]record.{0,20}直接(更新|書込|書き込み)", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# YAML parsing helpers
# ---------------------------------------------------------------------------

class YAMLParseError(Exception):
    """Raised when canonical YAML is present but malformed."""

    def __init__(self, file_path: Path, cause: Exception):
        self.file_path = file_path
        self.cause = cause
        super().__init__(f"YAML parse error in {file_path}: {cause}")


def _parse_canonical_yaml(file_path: Path, header_pattern: str) -> dict | None:
    """Parse canonical YAML block from a markdown file.

    Returns None if the file doesn't exist or has no canonical YAML block.
    Raises YAMLParseError if a YAML block is found but cannot be parsed.
    """
    if not file_path.is_file():
        return None
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        return None

    # Find yaml block after the header
    pattern = re.compile(
        rf"#\s*0\.\s*{header_pattern}.*?\n```yaml\s*\n(.*?)```",
        re.DOTALL,
    )
    match = pattern.search(content)
    if not match:
        return None

    if yaml is None:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        raise YAMLParseError(file_path, e) from e


def _read_file_text(file_path: Path) -> str:
    """Read file text, return empty string on failure."""
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Check implementations
# ---------------------------------------------------------------------------

def check_sec001_openapi_security(feature_dir: Path, spec_data: dict | None) -> dict:
    """SEC-001: OpenAPI securitySchemes defined."""
    result = {
        "id": "SEC-001", "severity": "HIGH", "confidence": 9,
        "message": "", "status": STATUS_PASS,
    }

    contracts_dir = feature_dir / "contracts"
    if not contracts_dir.is_dir():
        result["message"] = "contracts/ なし (スキップ)"
        return result

    has_security_privacy = False
    if spec_data:
        sp = spec_data.get("spec", {}).get("requirements", {}).get("security_privacy")
        if sp:
            has_security_privacy = True

    openapi_files = []
    for f in contracts_dir.iterdir():
        if f.suffix in (".yaml", ".yml") and f.is_file():
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8")) if yaml else None
            except Exception:
                data = None
            if data and isinstance(data, dict) and "openapi" in data:
                openapi_files.append((f, data))

    if not openapi_files:
        result["message"] = "OpenAPI 契約なし (スキップ)"
        return result

    for fpath, data in openapi_files:
        # Check if security-sensitive operations exist
        paths = data.get("paths", {})
        sensitive_ops = {"approve", "auth", "create", "update", "delete", "post", "put", "patch"}
        has_sensitive = has_security_privacy

        if not has_sensitive:
            for path_key, methods in (paths or {}).items():
                path_lower = path_key.lower()
                for method in (methods or {}):
                    if method.lower() in sensitive_ops or any(kw in path_lower for kw in sensitive_ops):
                        has_sensitive = True
                        break
                if has_sensitive:
                    break

        if not has_sensitive:
            continue

        # Check for securitySchemes and security declaration
        components = data.get("components", {})
        has_schemes = bool(components.get("securitySchemes"))
        has_security = bool(data.get("security"))

        if not has_security:
            # Check operation-level security
            for _path, methods in (paths or {}).items():
                if isinstance(methods, dict):
                    for _method, op in methods.items():
                        if isinstance(op, dict) and op.get("security"):
                            has_security = True
                            break
                if has_security:
                    break

        if not has_schemes or not has_security:
            result["status"] = STATUS_FAIL
            result["message"] = f"OpenAPI に securitySchemes / security 宣言が未定義 ({fpath.name})"
            return result

    result["message"] = "OpenAPI security 定義あり"
    return result


def check_sec002_authz_artifact(feature_dir: Path, spec_data: dict | None) -> dict:
    """SEC-002: Security-tagged AC has authz_matrix artifact."""
    result = {
        "id": "SEC-002", "severity": "HIGH", "confidence": 9,
        "message": "", "status": STATUS_PASS,
    }

    if not spec_data:
        result["message"] = "spec.md なし (スキップ)"
        return result

    spec = spec_data.get("spec", {})
    use_cases = spec.get("use_cases", [])

    has_security_ac = False
    for uc in (use_cases or []):
        for ac in (uc.get("acceptance", []) or []):
            tags = ac.get("tags", [])
            if isinstance(tags, list) and "security" in tags:
                has_security_ac = True
                break
        if has_security_ac:
            break

    if not has_security_ac:
        result["message"] = "security タグ付き AC なし (スキップ)"
        return result

    # Check spec_as_code.artifacts for type: authz_matrix
    artifacts = spec.get("spec_as_code", {}).get("artifacts", [])
    has_authz = False
    authz_path = None
    for art in (artifacts or []):
        if art.get("type") == "authz_matrix":
            has_authz = True
            authz_path = art.get("path", "")
            break

    if not has_authz:
        result["status"] = STATUS_FAIL
        result["message"] = "security tagged AC に authz_matrix 定義なし"
        return result

    # Check file exists (path may be feature-relative or repo-relative)
    if authz_path:
        full_path = feature_dir / authz_path
        if not full_path.is_file():
            # Try repo-relative: walk up from feature_dir to project root
            # e.g. specs/FEAT-X/implementation-details/authz_matrix.yaml
            project_root = feature_dir.parent.parent  # specs/FEAT-X -> project root
            repo_path = project_root / authz_path
            if not repo_path.is_file():
                result["status"] = STATUS_FAIL
                result["message"] = f"authz_matrix ファイルが存在しない: {authz_path}"
                return result

    result["message"] = "security tagged AC に authz_matrix 定義あり"
    return result


def check_sec003_security_requirements(spec_data: dict | None) -> dict:
    """SEC-003: security_privacy requirements present."""
    result = {
        "id": "SEC-003", "severity": "HIGH", "confidence": 10,
        "message": "", "status": STATUS_PASS,
    }

    if not spec_data:
        result["status"] = STATUS_FAIL
        result["message"] = "spec.md なし — requirements.security_privacy 未定義"
        return result

    sp = spec_data.get("spec", {}).get("requirements", {}).get("security_privacy")
    if not sp:
        result["status"] = STATUS_FAIL
        result["message"] = "requirements.security_privacy が未定義または空"
        return result

    result["message"] = "requirements.security_privacy あり"
    return result


def check_sec004_secrets(feature_dir: Path) -> dict:
    """SEC-004: No hardcoded secrets in feature files."""
    result = {
        "id": "SEC-004", "severity": "CRITICAL", "confidence": 10,
        "message": "", "status": STATUS_PASS,
    }

    findings = []
    for root, _dirs, files in os.walk(feature_dir):
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix not in (".md", ".yaml", ".yml", ".json", ".py", ".ts", ".js"):
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for i, line in enumerate(content.splitlines(), 1):
                # Skip YAML description lines
                stripped = line.strip()
                if stripped.startswith("description:"):
                    continue

                match = _SECRET_PATTERN.search(line)
                if match:
                    value = match.group(2).lower().strip()
                    # Check exclusions
                    if value in _SECRET_PLACEHOLDERS:
                        continue
                    if any(value.startswith(prefix) for prefix in ("tpl-",)):
                        continue
                    findings.append(f"{fpath.name}:{i}")

    if findings:
        result["status"] = STATUS_FAIL
        result["message"] = f"ハードコードされたシークレット検出: {', '.join(findings[:3])}"
    else:
        result["message"] = "ハードコードされたシークレットなし"

    return result


def check_sec005_audit_correlation(feature_dir: Path, spec_data: dict | None, bd_data: dict | None) -> dict:
    """SEC-005: Audit trail and correlation ID defined."""
    result = {
        "id": "SEC-005", "severity": "MEDIUM", "confidence": 8,
        "message": "", "status": STATUS_PASS,
    }

    search_texts = []

    if spec_data:
        spec = spec_data.get("spec", {})
        reqs = spec.get("requirements", {})
        for key in ("integration", "operations"):
            val = reqs.get(key)
            if val:
                search_texts.append(str(val))

    if bd_data:
        bd = bd_data.get("basic_design", {})
        flows = bd.get("integration_flows")
        if flows:
            search_texts.append(str(flows))

    combined = " ".join(search_texts).lower()

    found = any(kw.lower() in combined for kw in _AUDIT_KEYWORDS)
    if not found:
        result["status"] = STATUS_WARN
        result["message"] = "監査・相関ID・冪等性の記述が不足"
    else:
        result["message"] = "監査・相関・冪等性の言及あり"

    return result


def check_sec006_llm_trust_boundary(feature_dir: Path) -> dict:
    """SEC-006: LLM trust boundary defined for AI-integrated features."""
    result = {
        "id": "SEC-006", "severity": "HIGH", "confidence": 7,
        "message": "", "status": STATUS_PASS,
    }

    # Read relevant files
    search_files = ["spec.md", "basic_design.md", "plan.md"]
    full_text = ""
    for fname in search_files:
        full_text += _read_file_text(feature_dir / fname) + "\n"

    # Check if this is an AI-integrated feature
    text_lower = full_text.lower()

    # Remove provenance-only keywords before checking
    stripped_text = text_lower
    for kw in _PROVENANCE_ONLY_KEYWORDS:
        stripped_text = stripped_text.replace(kw.lower(), "")

    has_ai_integration = any(kw.lower() in stripped_text for kw in _AI_TRIGGER_KEYWORDS)

    if not has_ai_integration:
        result["message"] = "AI/LLM統合機能なし (スキップ)"
        return result

    # Check for trust boundary definitions — ALL four facets required
    missing_facets = []
    for facet_name, keywords in _TRUST_BOUNDARY_FACETS.items():
        if not any(kw.lower() in text_lower for kw in keywords):
            missing_facets.append(facet_name)

    if missing_facets:
        result["status"] = STATUS_FAIL
        result["message"] = (
            f"LLM trust boundary 不完全 — 不足: {', '.join(missing_facets)}。"
            " 4観点すべて必要: boundary, input_validation, output_verification, fallback"
        )
    else:
        result["message"] = "LLM trust boundary 4観点すべて定義あり"

    return result


def check_sec007_sod_in_authz(feature_dir: Path) -> dict:
    """SEC-007: SoD rules in authz_matrix."""
    result = {
        "id": "SEC-007", "severity": "MEDIUM", "confidence": 6,
        "message": "", "status": STATUS_PASS,
    }

    authz_path = feature_dir / "implementation-details" / "authz_matrix.yaml"
    if not authz_path.is_file():
        result["message"] = "authz_matrix.yaml なし (スキップ)"
        return result

    content = _read_file_text(authz_path).lower()
    sod_keywords = ["sod_rules", "separation_of_duties", "conflict_rules", "sod"]
    has_sod = any(kw in content for kw in sod_keywords)

    if not has_sod:
        result["status"] = STATUS_WARN
        result["message"] = "authz_matrix に SoD (Separation of Duties) 定義なし"
    else:
        result["message"] = "SoD 定義あり"

    return result


def check_sec008_data_class_retention(spec_data: dict | None, bd_data: dict | None) -> dict:
    """SEC-008: Data class and retention defined."""
    result = {
        "id": "SEC-008", "severity": "LOW", "confidence": 5,
        "message": "", "status": STATUS_PASS,
    }

    # Check basic_design data_policy
    if bd_data:
        dp = bd_data.get("basic_design", {}).get("data_policy", {})
        has_classes = bool(dp.get("data_classes"))
        has_retention = bool(dp.get("retention_policy"))
        if has_classes and has_retention:
            result["message"] = "data_classes + retention_policy あり"
            return result

    # Check spec data_governance
    if spec_data:
        dg = spec_data.get("spec", {}).get("requirements", {}).get("data_governance")
        if dg:
            dg_str = str(dg).lower()
            if ("分類" in dg_str or "class" in dg_str) and ("保持" in dg_str or "retention" in dg_str):
                result["message"] = "data_governance にデータ分類・保持期間の言及あり"
                return result

    result["status"] = STATUS_WARN
    result["message"] = "データ分類 (data_classes) または保持期間 (retention_policy) が未定義"
    return result


def check_sec009_org_constraints_ref(feature_dir: Path) -> dict:
    """SEC-009: org_constraints_ref present."""
    result = {
        "id": "SEC-009", "severity": "MEDIUM", "confidence": 4,
        "message": "", "status": STATUS_PASS,
    }

    bd_path = feature_dir / "basic_design.md"
    content = _read_file_text(bd_path)

    if "org_constraints_ref" in content or "tecnos_org_constraints.md" in content:
        result["message"] = "org_constraints 参照あり"
    else:
        result["status"] = STATUS_WARN
        result["message"] = "org_constraints_ref / tecnos_org_constraints.md 参照なし"

    return result


def check_sec010_direct_erp_write(feature_dir: Path) -> dict:
    """SEC-010: No direct ERP DB writes."""
    result = {
        "id": "SEC-010", "severity": "CRITICAL", "confidence": 3,
        "message": "", "status": STATUS_PASS,
    }

    search_files = ["plan.md", "basic_design.md"]
    combined = ""
    for fname in search_files:
        combined += _read_file_text(feature_dir / fname) + "\n"

    # Also check traceability_rows in tasks.md
    combined += _read_file_text(feature_dir / "tasks.md") + "\n"

    for pat in _DIRECT_ERP_WRITE_PATTERNS:
        match = pat.search(combined)
        if match:
            result["status"] = STATUS_FAIL
            result["message"] = f"外部 ERP への直接 DB 書き込みの疑い: {match.group(0)}"
            return result

    result["message"] = "直接 ERP DB 書き込みなし"
    return result


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_security_checks(feature_dir: Path, mode: str = "daily") -> dict:
    """Run security checks in the specified mode."""
    feature_dir = Path(feature_dir)

    # Parse canonical YAMLs — malformed YAML is an ERROR (exit 2)
    try:
        spec_data = _parse_canonical_yaml(feature_dir / "spec.md", "Canonical Spec")
        bd_data = _parse_canonical_yaml(feature_dir / "basic_design.md", "Canonical Basic Design")
    except YAMLParseError as e:
        return {
            "mode": mode,
            "feature": str(feature_dir),
            "summary": {"total": 0, "pass": 0, "fail": 0, "warn": 0},
            "checks": [],
            "result": "ERROR",
            "error": str(e),
            "exit_code": 2,
        }

    # Collect all checks
    all_checks = []

    # Daily checks (confidence >= 8)
    all_checks.append(check_sec001_openapi_security(feature_dir, spec_data))
    all_checks.append(check_sec002_authz_artifact(feature_dir, spec_data))
    all_checks.append(check_sec003_security_requirements(spec_data))
    all_checks.append(check_sec004_secrets(feature_dir))
    all_checks.append(check_sec005_audit_correlation(feature_dir, spec_data, bd_data))

    # Audit-only checks (confidence < 8)
    all_checks.append(check_sec006_llm_trust_boundary(feature_dir))
    all_checks.append(check_sec007_sod_in_authz(feature_dir))
    all_checks.append(check_sec008_data_class_retention(spec_data, bd_data))
    all_checks.append(check_sec009_org_constraints_ref(feature_dir))
    all_checks.append(check_sec010_direct_erp_write(feature_dir))

    # Filter by mode
    confidence_threshold = 8 if mode == "daily" else 2
    filtered = [c for c in all_checks if c["confidence"] >= confidence_threshold]

    # Determine status for each check
    for check in filtered:
        if check["status"] == STATUS_PASS:
            continue
        if check["severity"] in _FAIL_SEVERITIES:
            check["status"] = STATUS_FAIL
        elif check["severity"] in _WARN_SEVERITIES:
            check["status"] = STATUS_WARN

    # Aggregate
    fails = sum(1 for c in filtered if c["status"] == STATUS_FAIL)
    warns = sum(1 for c in filtered if c["status"] == STATUS_WARN)
    passes = sum(1 for c in filtered if c["status"] == STATUS_PASS)

    if fails > 0:
        verdict = "NOT_SECURE"
        exit_code = 1
    else:
        verdict = "SECURE"
        exit_code = 0

    return {
        "mode": mode,
        "feature": str(feature_dir),
        "summary": {
            "total": len(filtered),
            "pass": passes,
            "fail": fails,
            "warn": warns,
        },
        "checks": filtered,
        "result": verdict,
        "exit_code": exit_code,
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

_SEVERITY_SHORT = {"CRITICAL": "CRIT", "HIGH": "HIGH", "MEDIUM": "MED ", "LOW": "LOW "}


def format_human_readable(result: dict) -> str:
    """Format results for terminal output."""
    lines = []
    lines.append(f"=== STRIDE Security Check: {result['mode']} ===")
    lines.append(f"Feature: {result['feature']}")

    s = result["summary"]
    lines.append(f"Checks: {s['total']} | PASS: {s['pass']} | FAIL: {s['fail']} | WARN: {s['warn']}")
    lines.append("")

    for c in result["checks"]:
        sev = _SEVERITY_SHORT.get(c["severity"], c["severity"])
        if c["status"] == STATUS_FAIL:
            lines.append(f"FAIL  {c['id']} [{sev} conf:{c['confidence']}/10] {c['message']}")
        elif c["status"] == STATUS_WARN:
            lines.append(f"WARN  {c['id']} [{sev} conf:{c['confidence']}/10] {c['message']}")
        else:
            lines.append(f"PASS  {c['id']} {c['message']}")

    lines.append("")
    lines.append(f"Result: {result['result']} (exit {result['exit_code']})")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Security Checker - Executable security audit for SDD features",
    )
    parser.add_argument("feature_path", nargs="?", help="Feature directory path")
    parser.add_argument("--daily", action="store_true", help="Lightweight pre-Gate check (confidence >= 8)")
    parser.add_argument("--audit", action="store_true", help="Comprehensive pre-Final check (confidence >= 2)")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.feature_path:
        parser.error("feature_path is required (or use --test)")

    feature_dir = Path(args.feature_path)
    if not feature_dir.is_dir():
        print(f"Error: '{args.feature_path}' is not a directory", file=sys.stderr)
        sys.exit(2)

    if not args.daily and not args.audit:
        args.daily = True  # Default to daily

    mode = "audit" if args.audit else "daily"

    result = run_security_checks(feature_dir, mode)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(format_human_readable(result))

    sys.exit(result["exit_code"])


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Run self-tests using temporary directories."""
    print("Running stride_security_checker.py self-tests...")
    passed = 0
    total = 0

    def test(name, func):
        nonlocal passed, total
        total += 1
        try:
            func()
            print(f"  Test {total} passed: {name}")
            passed += 1
        except AssertionError as e:
            print(f"  Test {total} FAILED: {name} -- {e}")

    # Test 1: SEC-001 FAIL — OpenAPI without securitySchemes
    def test_sec001_fail():
        if yaml is None:
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            contracts = p / "contracts"
            contracts.mkdir()
            spec_dir = p
            (contracts / "api.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "info": {"title": "Test", "version": "1.0"},
                "paths": {
                    "/api/orders": {
                        "post": {"responses": {"200": {"description": "OK"}}},
                    },
                },
            }))
            # Create spec.md with security_privacy
            (spec_dir / "spec.md").write_text(
                "# 0. Canonical Spec (YAML)\n```yaml\nspec:\n  requirements:\n    security_privacy:\n      - auth required\n```\n"
            )
            spec_data = _parse_canonical_yaml(spec_dir / "spec.md", "Canonical Spec")
            r = check_sec001_openapi_security(p, spec_data)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}: {r['message']}"

    test("SEC-001 FAIL: OpenAPI without securitySchemes", test_sec001_fail)

    # Test 2: SEC-001 PASS — OpenAPI with securitySchemes + security
    def test_sec001_pass():
        if yaml is None:
            return
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            contracts = p / "contracts"
            contracts.mkdir()
            (contracts / "api.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "info": {"title": "Test", "version": "1.0"},
                "components": {
                    "securitySchemes": {
                        "bearerAuth": {"type": "http", "scheme": "bearer"},
                    },
                },
                "security": [{"bearerAuth": []}],
                "paths": {
                    "/api/orders": {
                        "post": {"responses": {"200": {"description": "OK"}}},
                    },
                },
            }))
            (p / "spec.md").write_text(
                "# 0. Canonical Spec (YAML)\n```yaml\nspec:\n  requirements:\n    security_privacy:\n      - auth\n```\n"
            )
            spec_data = _parse_canonical_yaml(p / "spec.md", "Canonical Spec")
            r = check_sec001_openapi_security(p, spec_data)
            assert r["status"] == STATUS_PASS, f"expected PASS, got {r['status']}: {r['message']}"

    test("SEC-001 PASS: OpenAPI with securitySchemes", test_sec001_pass)

    # Test 3: SEC-003 FAIL — no security_privacy
    def test_sec003_fail():
        spec_data = {"spec": {"requirements": {}}}
        r = check_sec003_security_requirements(spec_data)
        assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}"

    test("SEC-003 FAIL: requirements.security_privacy absent", test_sec003_fail)

    # Test 4: SEC-003 PASS — security_privacy present
    def test_sec003_pass():
        spec_data = {"spec": {"requirements": {"security_privacy": ["auth required"]}}}
        r = check_sec003_security_requirements(spec_data)
        assert r["status"] == STATUS_PASS, f"expected PASS, got {r['status']}"

    test("SEC-003 PASS: requirements.security_privacy present", test_sec003_pass)

    # Test 5: SEC-004 FAIL — hardcoded secret
    def test_sec004_fail():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "config.yaml").write_text(
                "api_key: 'sk-1234567890abcdef'\nother: value\n"
            )
            r = check_sec004_secrets(p)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}: {r['message']}"

    test("SEC-004 FAIL: hardcoded secret detected", test_sec004_fail)

    # Test 6: SEC-004 PASS — clean
    def test_sec004_pass():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "config.yaml").write_text("name: test\nversion: 1.0\n")
            r = check_sec004_secrets(p)
            assert r["status"] == STATUS_PASS, f"expected PASS, got {r['status']}: {r['message']}"

    test("SEC-004 PASS: no secrets", test_sec004_pass)

    # Test 7: SEC-006 FAIL — AI integration without trust boundary
    def test_sec006_fail():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "spec.md").write_text(
                "# 0. Canonical Spec (YAML)\n```yaml\nspec:\n  overview:\n    what: AI agent integration\n```\n"
                "\n## Features\nThis feature uses an AI agent to process orders.\n"
                "The LLM model output is used for classification.\n"
            )
            (p / "basic_design.md").write_text("# Basic Design\nStandard implementation.\n")
            (p / "plan.md").write_text("# Plan\nImplement AI agent.\n")
            r = check_sec006_llm_trust_boundary(p)
            assert r["status"] == STATUS_FAIL, f"expected FAIL, got {r['status']}: {r['message']}"

    test("SEC-006 FAIL: AI integration without trust boundary", test_sec006_fail)

    # Test 8: daily mode filters confidence < 8
    def test_daily_filter():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            # Minimal spec without security_privacy -> SEC-003 FAIL (conf=10, should show)
            (p / "spec.md").write_text(
                "# 0. Canonical Spec (YAML)\n```yaml\nspec:\n  requirements: {}\n```\n"
            )
            (p / "basic_design.md").write_text(
                "# 0. Canonical Basic Design (YAML)\n```yaml\nbasic_design: {}\n```\n"
            )
            result = run_security_checks(p, mode="daily")
            # In daily mode, only confidence >= 8 should be reported
            for c in result["checks"]:
                assert c["confidence"] >= 8, f"daily mode should not include {c['id']} with confidence {c['confidence']}"

            # Run audit mode for comparison
            result_audit = run_security_checks(p, mode="audit")
            assert len(result_audit["checks"]) > len(result["checks"]), \
                f"audit should have more checks than daily ({len(result_audit['checks'])} vs {len(result['checks'])})"

    test("daily mode filters confidence < 8", test_daily_filter)

    print(f"\nAll {passed}/{total} self-tests passed." if passed == total else f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    main()
