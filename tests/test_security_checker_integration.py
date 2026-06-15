"""Integration tests for stride_security_checker.py with real project fixtures."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tools_path():
    """Path to sdd-templates/tools/."""
    return Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"


@pytest.fixture
def _import_checker(tools_path):
    """Import stride_security_checker module."""
    sys.path.insert(0, str(tools_path))
    try:
        import stride_security_checker
        yield stride_security_checker
    finally:
        sys.path.pop(0)
        if "stride_security_checker" in sys.modules:
            del sys.modules["stride_security_checker"]


def _make_spec_md(feature_dir: Path, spec_yaml: dict):
    """Create spec.md with canonical YAML block."""
    yaml_str = yaml.dump(spec_yaml, default_flow_style=False, allow_unicode=True)
    (feature_dir / "spec.md").write_text(
        f"# 0. Canonical Spec (YAML)\n```yaml\n{yaml_str}```\n",
        encoding="utf-8",
    )


def _make_basic_design_md(feature_dir: Path, bd_yaml: dict):
    """Create basic_design.md with canonical YAML block."""
    yaml_str = yaml.dump(bd_yaml, default_flow_style=False, allow_unicode=True)
    (feature_dir / "basic_design.md").write_text(
        f"# 0. Canonical Basic Design (YAML)\n```yaml\n{yaml_str}```\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
class TestSecurityCheckerIntegration:

    def test_sec001_fail_no_security_schemes(self, tmp_path, _import_checker):
        """SEC-001 FAIL: OpenAPI without securitySchemes."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        contracts = feature / "contracts"
        contracts.mkdir()

        # OpenAPI without securitySchemes
        (contracts / "api.yaml").write_text(yaml.dump({
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/api/orders": {
                    "post": {"responses": {"200": {"description": "OK"}}},
                },
            },
        }))

        # Spec with security_privacy
        _make_spec_md(feature, {
            "spec": {
                "requirements": {
                    "security_privacy": ["auth required"],
                },
                "use_cases": [],
            },
        })

        spec_data = mod._parse_canonical_yaml(feature / "spec.md", "Canonical Spec")
        r = mod.check_sec001_openapi_security(feature, spec_data)
        assert r["status"] == "FAIL"
        assert "securitySchemes" in r["message"]

    def test_sec001_pass_with_security(self, tmp_path, _import_checker):
        """SEC-001 PASS: OpenAPI with securitySchemes + security."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        contracts = feature / "contracts"
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

        _make_spec_md(feature, {
            "spec": {
                "requirements": {
                    "security_privacy": ["auth required"],
                },
                "use_cases": [],
            },
        })

        spec_data = mod._parse_canonical_yaml(feature / "spec.md", "Canonical Spec")
        r = mod.check_sec001_openapi_security(feature, spec_data)
        assert r["status"] == "PASS"

    def test_sec003_fail_no_security_privacy(self, _import_checker):
        """SEC-003 FAIL: requirements.security_privacy absent."""
        mod = _import_checker
        spec_data = {"spec": {"requirements": {}}}
        r = mod.check_sec003_security_requirements(spec_data)
        assert r["status"] == "FAIL"

    def test_sec004_fail_hardcoded_secret(self, tmp_path, _import_checker):
        """SEC-004 FAIL: Hardcoded secret detected."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "config.yaml").write_text(
            "api_key: 'sk-1234567890abcdefgh'\nname: test\n"
        )
        r = mod.check_sec004_secrets(feature)
        assert r["status"] == "FAIL"
        assert "シークレット検出" in r["message"]

    def test_sec006_fail_ai_no_trust_boundary(self, tmp_path, _import_checker):
        """SEC-006 FAIL: AI integration without trust boundary."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(
            "# Spec\nThis feature uses an AI agent for order classification.\n"
            "The LLM model output determines the category.\n"
        )
        (feature / "basic_design.md").write_text("# Basic Design\nStandard implementation.\n")
        (feature / "plan.md").write_text("# Plan\nImplement the AI agent pipeline.\n")

        r = mod.check_sec006_llm_trust_boundary(feature)
        assert r["status"] == "FAIL"
        assert "trust boundary" in r["message"]

    def test_daily_mode_filters_low_confidence(self, tmp_path, _import_checker):
        """daily mode should only include confidence >= 8."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_spec_md(feature, {"spec": {"requirements": {}, "use_cases": []}})
        _make_basic_design_md(feature, {"basic_design": {}})

        result = mod.run_security_checks(feature, mode="daily")
        for c in result["checks"]:
            assert c["confidence"] >= 8, (
                f"daily mode included {c['id']} with confidence {c['confidence']}"
            )

    def test_audit_mode_includes_low_confidence(self, tmp_path, _import_checker):
        """audit mode should include checks with confidence >= 2."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_spec_md(feature, {"spec": {"requirements": {}, "use_cases": []}})
        _make_basic_design_md(feature, {"basic_design": {}})

        result_daily = mod.run_security_checks(feature, mode="daily")
        result_audit = mod.run_security_checks(feature, mode="audit")

        assert len(result_audit["checks"]) > len(result_daily["checks"]), (
            f"audit ({len(result_audit['checks'])}) should have more checks than daily ({len(result_daily['checks'])})"
        )

    def test_json_output_valid(self, tmp_path, _import_checker):
        """--json output should be valid JSON with required keys."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)

        _make_spec_md(feature, {"spec": {"requirements": {}, "use_cases": []}})
        _make_basic_design_md(feature, {"basic_design": {}})

        result = mod.run_security_checks(feature, mode="daily")
        json_str = json.dumps(result, ensure_ascii=False)
        parsed = json.loads(json_str)

        for key in ("mode", "feature", "summary", "checks", "result"):
            assert key in parsed, f"missing key '{key}' in JSON output"

    def test_sec006_partial_trust_boundary_still_fails(self, tmp_path, _import_checker):
        """SEC-006 FAIL: Only 1 of 4 trust-boundary facets is not enough."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(
            "# Spec\nThis uses an AI agent.\nLLM model output.\n"
            "Input validation is done for all prompts.\n"
        )
        (feature / "basic_design.md").write_text("")
        (feature / "plan.md").write_text("")

        r = mod.check_sec006_llm_trust_boundary(feature)
        assert r["status"] == "FAIL", f"Expected FAIL with only 1 facet, got {r['status']}"
        assert "boundary" in r["message"]
        assert "output_verification" in r["message"]
        assert "fallback" in r["message"]

    def test_sec006_all_four_facets_pass(self, tmp_path, _import_checker):
        """SEC-006 PASS: All 4 trust-boundary facets present."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(
            "# Spec\nAI agent integration with LLM.\n"
            "Trusted/untrusted boundary defined.\n"
            "Input validation for all prompts.\n"
            "Output verification via schema.\n"
            "Fallback to human escalation.\n"
        )
        (feature / "basic_design.md").write_text("")
        (feature / "plan.md").write_text("")

        r = mod.check_sec006_llm_trust_boundary(feature)
        assert r["status"] == "PASS", f"Expected PASS with all 4 facets, got {r['status']}"

    def test_malformed_yaml_returns_error_exit2(self, tmp_path, _import_checker):
        """Malformed canonical YAML returns ERROR with exit_code 2."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "spec.md").write_text(
            "# 0. Canonical Spec (YAML)\n```yaml\n{invalid: [yaml: broken\n```\n"
        )

        result = mod.run_security_checks(feature, mode="daily")
        assert result["result"] == "ERROR"
        assert result["exit_code"] == 2
        assert "error" in result

    def test_sec010_addon_table_excluded(self, tmp_path, _import_checker):
        """SEC-010 PASS: Feature-owned addon tables are not flagged."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "plan.md").write_text("INSERT INTO erp_addon_buffer VALUES (1, 2)\n")
        (feature / "basic_design.md").write_text("")
        (feature / "tasks.md").write_text("")

        r = mod.check_sec010_direct_erp_write(feature)
        assert r["status"] == "PASS", f"Addon table should not trigger, got {r['status']}: {r['message']}"

    def test_sec010_real_erp_table_detected(self, tmp_path, _import_checker):
        """SEC-010 FAIL: Direct write to ERP system table is detected."""
        mod = _import_checker
        feature = tmp_path / "specs" / "FEAT-TEST"
        feature.mkdir(parents=True)
        (feature / "plan.md").write_text("INSERT INTO erp.master_table VALUES (1)\n")
        (feature / "basic_design.md").write_text("")
        (feature / "tasks.md").write_text("")

        r = mod.check_sec010_direct_erp_write(feature)
        assert r["status"] == "FAIL", f"ERP write should trigger, got {r['status']}"
