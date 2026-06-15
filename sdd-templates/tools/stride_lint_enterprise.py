#!/usr/bin/env python3
"""
stride-lint Enterprise Extension
Version: 1.0.0

Purpose:
- Add Enterprise SDD validation capabilities to stride-lint
- Validate Epic/Feature hierarchy
- Validate shared contracts and cross-team dependencies
- Validate tiered coverage requirements
- Check delegated approval rules

Usage:
    python3 stride_lint_enterprise.py <feature_or_epic_dir>
    python3 stride_lint_enterprise.py --enterprise <project_root>
    python3 stride_lint_enterprise.py --test

Integration with stride-lint:
    This module can be imported and used by stride_lint.py to add
    enterprise validation capabilities when --enterprise flag is used.
"""

import argparse
import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, field

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# Enterprise ID Patterns (extends constitution.md)
# =============================================================================

ENTERPRISE_ID_PATTERNS = {
    # Epic-level IDs
    "epic_id": r"^EPIC-[A-Z]{3,}$",
    "team_id": r"^TEAM-[A-Z]{1,3}$",
    "epic_milestone_id": r"^EM-[0-9]{2}$",
    "integration_point_id": r"^IP-[0-9]{3}$",
    "dependency_id": r"^DEP-[0-9]{3}$",
    "shared_contract_id": r"^SC-(API|EVT|FILE)-[A-Z0-9]{3,}$",
    "feature_breakdown_id": r"^FBD-[A-Z0-9]{3,}$",
    "ccp_id": r"^CCP-[0-9]{3}$",

    # Existing patterns from constitution (v1.2.6: supports team-prefixed IDs)
    "feature_id": r"^FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}$",
    "use_case_id": r"^US-FEAT[A-Z0-9]{3,}-[0-9]{3}$",
    "acceptance_id": r"^AC-US-FEAT[A-Z0-9]{3,}-[0-9]{3}-[0-9]{2}$",
    "contract_id": r"^CT-(API|CLI|EVT|FILE|BATCH|EDI|IDOC|DB)-[0-9]{2}$",
    "test_id": r"^TS-(CON|INT|E2E|UT)-[0-9]{2}$",
    "task_id": r"^T-[A-Z0-9]{2,}-[0-9]{3}$",
}

# Coverage tier requirements
COVERAGE_TIERS = {
    "critical": {
        "ac_coverage": 100,
        "ct_coverage": 100,
        "lib_line": 85,
        "lib_branch": 75,
        "cmp_line": 70,
        "cmp_branch": 60,
        "e2e_required": True,
    },
    "standard": {
        "ac_coverage": 100,
        "ct_coverage": 80,
        "lib_line": 70,
        "lib_branch": 60,
        "cmp_line": 60,
        "cmp_branch": 50,
        "e2e_required": False,
    },
    "experimental": {
        "ac_coverage": 80,
        "ct_coverage": 60,
        "lib_line": 50,
        "lib_branch": 40,
        "cmp_line": 40,
        "cmp_branch": 30,
        "e2e_required": False,
    },
}


@dataclass
class EnterpriseLintResult:
    """Container for enterprise lint results."""
    path: str
    errors: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[Dict[str, str]] = field(default_factory=list)
    info: List[str] = field(default_factory=list)

    def add_error(self, code: str, message: str):
        self.errors.append({"code": code, "message": message})

    def add_warning(self, code: str, message: str):
        self.warnings.append({"code": code, "message": message})

    def add_info(self, message: str):
        self.info.append(message)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def merge(self, other: 'EnterpriseLintResult'):
        """Merge another result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)


class EnterpriseValidator:
    """Enterprise-level SDD validation."""

    def __init__(self, project_root: Path):
        self.root = Path(project_root)
        self.result = EnterpriseLintResult(str(project_root))
        self._load_policies()

    def _load_policies(self):
        """Load enterprise policies from shared/policies/."""
        self.coverage_tiers = COVERAGE_TIERS.copy()
        self.dependency_rules = {}

        # Try to load custom coverage tiers
        tiers_path = self.root / "shared" / "policies" / "coverage_tiers.yaml"
        if tiers_path.exists():
            try:
                with open(tiers_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if data and "coverage_tiers" in data:
                    self._parse_coverage_tiers(data["coverage_tiers"])
            except Exception as e:
                self.result.add_warning("POLICY_LOAD_ERROR", f"Failed to load coverage_tiers.yaml: {e}")

        # Try to load dependency rules
        rules_path = self.root / "shared" / "policies" / "dependency_rules.yaml"
        if rules_path.exists():
            try:
                with open(rules_path, 'r', encoding='utf-8') as f:
                    self.dependency_rules = yaml.safe_load(f) or {}
            except Exception as e:
                self.result.add_warning("POLICY_LOAD_ERROR", f"Failed to load dependency_rules.yaml: {e}")

    def _parse_coverage_tiers(self, tiers_data: Dict):
        """Parse coverage tiers from YAML."""
        for tier_name, tier_def in tiers_data.get("tiers", {}).items():
            if tier_name in self.coverage_tiers:
                reqs = tier_def.get("coverage_requirements", {})
                self.coverage_tiers[tier_name] = {
                    "ac_coverage": reqs.get("acceptance_coverage", {}).get("target_pct", 100),
                    "ct_coverage": reqs.get("contract_coverage", {}).get("target_pct", 100),
                    "lib_line": reqs.get("code_coverage", {}).get("lib", {}).get("line_pct", 70),
                    "lib_branch": reqs.get("code_coverage", {}).get("lib", {}).get("branch_pct", 60),
                    "cmp_line": reqs.get("code_coverage", {}).get("cmp", {}).get("line_pct", 60),
                    "cmp_branch": reqs.get("code_coverage", {}).get("cmp", {}).get("branch_pct", 50),
                    "e2e_required": reqs.get("e2e", {}).get("required", False),
                }

    def load_yaml(self, path: Path) -> Optional[Dict]:
        """Load a YAML file safely."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.result.add_error("YAML_LOAD_ERROR", f"Failed to load {path}: {e}")
            return None

    def extract_yaml_from_md(self, md_path: Path) -> Optional[Dict]:
        """Extract first YAML block from markdown file."""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'```yaml\s*(.*?)```', content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1))
            return None
        except Exception as e:
            self.result.add_error("YAML_EXTRACT_ERROR", f"Failed to extract YAML from {md_path}: {e}")
            return None

    def validate_id(self, id_type: str, value: str, context: str, result: EnterpriseLintResult = None) -> bool:
        """Validate an ID against its pattern.

        Args:
            id_type: The type of ID to validate (e.g., 'feature_id', 'epic_id')
            value: The actual ID value to check
            context: Human-readable context for error messages
            result: Optional result object to write errors to (defaults to self.result)
        """
        target_result = result if result is not None else self.result

        if id_type not in ENTERPRISE_ID_PATTERNS:
            return True  # Unknown type, skip

        pattern = ENTERPRISE_ID_PATTERNS[id_type]
        if not re.match(pattern, value):
            target_result.add_error(
                "ID_REGEX_MISMATCH",
                f"{context}: '{value}' does not match {id_type} pattern {pattern}"
            )
            return False
        return True

    # =========================================================================
    # Epic Validation
    # =========================================================================

    def validate_epic(self, epic_dir: Path) -> EnterpriseLintResult:
        """Validate an epic directory."""
        result = EnterpriseLintResult(str(epic_dir))

        # Check epic_design.md exists
        epic_design = epic_dir / "epic_design.md"
        if not epic_design.exists():
            result.add_error("MISSING_FILE", "epic_design.md not found")
            return result

        # Extract and validate epic YAML
        data = self.extract_yaml_from_md(epic_design)
        if not data or "epic" not in data:
            result.add_error("INVALID_STRUCTURE", "epic_design.md missing 'epic' root key")
            return result

        epic = data["epic"]

        # Validate meta
        meta = epic.get("meta", {})
        epic_id = meta.get("epic_id", "UNKNOWN")

        if not epic_id or epic_id == "EPIC-XXX":
            result.add_error("PLACEHOLDER_VALUE", f"epic_id is placeholder: {epic_id}")
        else:
            self.validate_id("epic_id", epic_id, "meta.epic_id", result)

        # Validate teams
        teams = epic.get("ownership", {}).get("teams", [])
        team_ids = set()
        for team in teams:
            tid = team.get("team_id")
            if tid:
                self.validate_id("team_id", tid, f"teams[{tid}]", result)
                team_ids.add(tid)

        if not team_ids:
            result.add_error("MISSING_TEAMS", "No teams defined in epic")

        # Validate features
        features = epic.get("features", [])
        feature_ids = set()

        for feature in features:
            fid = feature.get("feature_id")
            if fid:
                self.validate_id("feature_id", fid, f"features[{fid}]", result)
                feature_ids.add(fid)

                # Check team assignment
                fteam = feature.get("team_id")
                if fteam and fteam not in team_ids:
                    result.add_error(
                        "INVALID_TEAM_REF",
                        f"Feature {fid} references undefined team {fteam}"
                    )

                # Validate coverage tier
                tier = feature.get("coverage_tier", "standard")
                if tier not in self.coverage_tiers:
                    result.add_warning("INVALID_TIER", f"Feature {fid} has unknown tier: {tier}")

        # Validate cross-team dependencies
        deps = epic.get("cross_team_dependencies", [])
        for dep in deps:
            did = dep.get("dependency_id")
            if did:
                self.validate_id("dependency_id", did, f"dependencies[{did}]", result)

            from_f = dep.get("from_feature")
            to_f = dep.get("to_feature")

            feat_pattern = ENTERPRISE_ID_PATTERNS.get("feature_id", "")
            for ref_label, ref_val in [("from_feature", from_f), ("to_feature", to_f)]:
                if not ref_val or ref_val in feature_ids:
                    continue
                if re.match(feat_pattern, ref_val):
                    result.add_error("INVALID_FEATURE_REF", f"Dependency references undefined {ref_label}: {ref_val}")
                elif ref_val.upper().startswith("FEAT"):
                    result.add_warning("SUSPICIOUS_FEATURE_REF", f"{ref_label} '{ref_val}' looks like Feature ID but doesn't match pattern")

        # Validate shared contracts
        contracts = epic.get("shared_contracts", [])
        for contract in contracts:
            cid = contract.get("contract_id")
            if cid:
                self.validate_id("shared_contract_id", cid, f"shared_contracts[{cid}]", result)

        # Check feature_breakdown.md if exists
        fb_path = epic_dir / "feature_breakdown.md"
        if fb_path.exists():
            fb_result = self._validate_feature_breakdown(fb_path, feature_ids)
            result.merge(fb_result)

        # Check EPIC_APPROVAL.md
        approval_path = epic_dir / "EPIC_APPROVAL.md"
        if not approval_path.exists():
            result.add_warning("APPROVAL_FILE_MISSING", "EPIC_APPROVAL.md not found")

        self.result.merge(result)
        return result

    def _validate_feature_breakdown(self, fb_path: Path, expected_features: Set[str]) -> EnterpriseLintResult:
        """Validate feature_breakdown.md."""
        result = EnterpriseLintResult(str(fb_path))

        data = self.extract_yaml_from_md(fb_path)
        if not data or "feature_breakdown" not in data:
            result.add_error("INVALID_STRUCTURE", "feature_breakdown.md missing 'feature_breakdown' root key")
            return result

        fb = data["feature_breakdown"]

        # Validate features match
        fb_features = set()
        for feature in fb.get("features", []):
            fid = feature.get("feature_id")
            if fid:
                fb_features.add(fid)

        # Check for missing features
        missing = expected_features - fb_features
        if missing:
            result.add_warning("FEATURE_MISMATCH", f"Features in epic_design but not in breakdown: {missing}")

        extra = fb_features - expected_features
        if extra:
            result.add_warning("FEATURE_MISMATCH", f"Features in breakdown but not in epic_design: {extra}")

        # Check for cycles in dependency graph
        dep_graph = fb.get("dependency_graph", {})
        edges = dep_graph.get("edges", [])

        adj = {}
        for edge in edges:
            from_node = edge.get("from")
            to_node = edge.get("to")
            if from_node and to_node:
                if from_node not in adj:
                    adj[from_node] = []
                adj[from_node].append(to_node)

        # DFS cycle detection
        visited = set()
        rec_stack = set()

        def has_cycle(node, path):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path + [neighbor]):
                        return True
                elif neighbor in rec_stack:
                    cycle = path[path.index(neighbor):] + [neighbor] if neighbor in path else [node, neighbor]
                    result.add_error("DEPENDENCY_CYCLE", f"Cycle in feature_breakdown: {' -> '.join(cycle)}")
                    return True

            rec_stack.remove(node)
            return False

        for node in adj:
            if node not in visited:
                has_cycle(node, [node])

        return result

    # =========================================================================
    # Feature Enterprise Extensions
    # =========================================================================

    def validate_feature_enterprise(self, feature_dir: Path) -> EnterpriseLintResult:
        """Validate enterprise extensions in a feature."""
        result = EnterpriseLintResult(str(feature_dir))

        # Check basic_design.md for enterprise fields
        bd_path = feature_dir / "basic_design.md"
        if not bd_path.exists():
            result.add_error("MISSING_FILE", "basic_design.md not found")
            return result

        data = self.extract_yaml_from_md(bd_path)
        if not data:
            return result

        bd = data.get("basic_design", data)

        # Extract enterprise fields
        epic_ref = bd.get("epic_ref") or bd.get("meta", {}).get("epic_ref")
        team_id = bd.get("team_id") or bd.get("meta", {}).get("team_id")
        coverage_tier = bd.get("coverage_tier") or bd.get("meta", {}).get("coverage_tier", "standard")

        # Validate epic_ref if present
        if epic_ref:
            self.validate_id("epic_id", epic_ref, "basic_design.epic_ref", result)

            # Check epic exists
            epic_dir = self.root / "epics" / epic_ref
            if not epic_dir.exists():
                result.add_warning("EPIC_NOT_FOUND", f"Referenced epic not found: epics/{epic_ref}/")

        # Validate team_id if present
        if team_id:
            self.validate_id("team_id", team_id, "basic_design.team_id", result)
        else:
            result.add_info("team_id not set - enterprise team tracking disabled")

        # Validate coverage tier
        if coverage_tier not in self.coverage_tiers:
            result.add_error("INVALID_TIER", f"Unknown coverage_tier: {coverage_tier}")
        else:
            # Validate coverage policy matches tier requirements
            tier_reqs = self.coverage_tiers[coverage_tier]
            plan_path = feature_dir / "plan.md"

            if plan_path.exists():
                plan_data = self.extract_yaml_from_md(plan_path)
                if plan_data:
                    plan = plan_data.get("plan", plan_data)
                    # coverage_policy is under test_strategy in the template
                    test_strategy = plan.get("test_strategy", {})
                    policy = test_strategy.get("coverage_policy", {})

                    # Fallback to direct coverage_policy for backward compatibility
                    if not policy:
                        policy = plan.get("coverage_policy", {})

                    # Check AC coverage target
                    ac_target = policy.get("acceptance_coverage_target_pct", 100)
                    if ac_target < tier_reqs["ac_coverage"]:
                        result.add_error(
                            "COVERAGE_TIER_MISMATCH",
                            f"AC coverage target {ac_target}% is below {coverage_tier} tier requirement {tier_reqs['ac_coverage']}%"
                        )

                    # Check CT coverage target
                    ct_target = policy.get("contract_coverage_target_pct", 100)
                    if ct_target < tier_reqs["ct_coverage"]:
                        result.add_warning(
                            "COVERAGE_TIER_MISMATCH",
                            f"CT coverage target {ct_target}% is below {coverage_tier} tier requirement {tier_reqs['ct_coverage']}%"
                        )

        # Check dependency manifest
        dep_manifest = feature_dir / "dependencies" / "dependency_manifest.yaml"
        if dep_manifest.exists():
            dep_result = self._validate_dependency_manifest(dep_manifest)
            result.merge(dep_result)

        # Check cross_refs.yaml
        cross_refs = feature_dir / "cross_refs.yaml"
        if cross_refs.exists():
            xref_result = self._validate_cross_refs(cross_refs)
            result.merge(xref_result)

        self.result.merge(result)
        return result

    def _validate_dependency_manifest(self, manifest_path: Path) -> EnterpriseLintResult:
        """Validate dependency_manifest.yaml."""
        result = EnterpriseLintResult(str(manifest_path))

        data = self.load_yaml(manifest_path)
        if not data or "dependency_manifest" not in data:
            result.add_error("INVALID_STRUCTURE", "dependency_manifest.yaml missing 'dependency_manifest' root key")
            return result

        manifest = data["dependency_manifest"]

        # Validate external dependencies
        for i, dep in enumerate(manifest.get("external_dependencies", [])):
            prefix = f"external_dependencies[{i}]"

            # Check required fields
            if not dep.get("contract_ref"):
                result.add_error("MISSING_FIELD", f"{prefix}: missing contract_ref")

            if not dep.get("version_constraint"):
                result.add_error("MISSING_FIELD", f"{prefix}: missing version_constraint")
            else:
                # Validate semver constraint
                vc = dep["version_constraint"]
                if not re.match(r'^[\^~>=<\d\.\*\s|]+$', vc):
                    result.add_warning("INVALID_VERSION_CONSTRAINT", f"{prefix}: suspicious version_constraint format: {vc}")

            # Check high criticality has fallback
            if dep.get("criticality") == "high":
                fallback = dep.get("error_handling", {}).get("fallback_behavior")
                if not fallback:
                    result.add_warning("MISSING_FALLBACK", f"{prefix}: high criticality dependency missing fallback_behavior")

            # Validate contract_id if present
            cid = dep.get("contract_id")
            if cid:
                # Could be regular or shared contract
                if cid.startswith("SC-"):
                    self.validate_id("shared_contract_id", cid, f"{prefix}.contract_id", result)
                else:
                    self.validate_id("contract_id", cid, f"{prefix}.contract_id", result)

        return result

    def _validate_cross_refs(self, xref_path: Path) -> EnterpriseLintResult:
        """Validate cross_refs.yaml."""
        result = EnterpriseLintResult(str(xref_path))

        data = self.load_yaml(xref_path)
        if not data or "cross_refs" not in data:
            result.add_error("INVALID_STRUCTURE", "cross_refs.yaml missing 'cross_refs' root key")
            return result

        xrefs = data["cross_refs"]

        # Validate external dependencies
        for i, dep in enumerate(xrefs.get("external_dependencies", [])):
            prefix = f"external_dependencies[{i}]"

            # Check contract_ref exists
            cref = dep.get("contract_ref")
            if cref:
                ref_path = self.root / cref
                if not ref_path.exists():
                    result.add_warning("REF_NOT_FOUND", f"{prefix}: contract_ref not found: {cref}")

            # Validate spec_refs exist
            for spec_ref in dep.get("spec_refs", []):
                self.validate_id("acceptance_id", spec_ref, f"{prefix}.spec_refs", result)

        return result

    # =========================================================================
    # Shared Contract Validation
    # =========================================================================

    def validate_shared_contracts(self) -> EnterpriseLintResult:
        """Validate all shared contracts in shared/contracts/."""
        result = EnterpriseLintResult(str(self.root / "shared" / "contracts"))

        contracts_dir = self.root / "shared" / "contracts"
        if not contracts_dir.exists():
            result.add_info("No shared/contracts/ directory found")
            return result

        # Find all YAML files
        for yaml_file in contracts_dir.rglob("*.yaml"):
            if yaml_file.name.startswith("_"):
                continue

            data = self.load_yaml(yaml_file)
            if not data:
                continue

            # Check if it's a shared contract definition
            if "shared_contract" in data:
                contract = data["shared_contract"]
                cid = contract.get("meta", {}).get("contract_id")

                if cid:
                    self.validate_id("shared_contract_id", cid, f"{yaml_file.name}.contract_id", result)

                # Check owner team
                owner_team = contract.get("ownership", {}).get("owner_team")
                if not owner_team:
                    result.add_warning("MISSING_OWNER", f"{yaml_file.name}: missing owner_team")

                # Check consumers list
                consumers = contract.get("consumers", [])
                if not consumers:
                    result.add_info(f"{yaml_file.name}: no consumers registered")

        self.result.merge(result)
        return result

    # =========================================================================
    # Full Enterprise Lint
    # =========================================================================

    def lint_enterprise(self) -> EnterpriseLintResult:
        """Run full enterprise lint on project."""
        # Validate all epics
        epics_dir = self.root / "epics"
        if epics_dir.exists():
            for epic_dir in epics_dir.iterdir():
                if epic_dir.is_dir() and (epic_dir / "epic_design.md").exists():
                    self.validate_epic(epic_dir)

        # Validate all features with enterprise extensions
        specs_dir = self.root / "specs"
        if specs_dir.exists():
            for feature_dir in specs_dir.iterdir():
                if feature_dir.is_dir() and (feature_dir / "basic_design.md").exists():
                    self.validate_feature_enterprise(feature_dir)

        # Validate shared contracts
        self.validate_shared_contracts()

        # Run dependency cycle detection across all features
        try:
            from dependency_checker import DependencyChecker
            checker = DependencyChecker(self.root)
            success, dep_results = checker.check()

            if not success:
                for error in dep_results.get("errors", []):
                    self.result.add_error("DEPENDENCY_ERROR", error)
                for cycle in dep_results.get("cycles", []):
                    self.result.add_error("DEPENDENCY_CYCLE", f"Cycle: {' -> '.join(cycle)}")
        except ImportError:
            pass  # dependency_checker not available

        return self.result


def run_tests():
    """Run basic self-tests."""
    print("Running stride_lint_enterprise.py self-tests...\n")

    # Test 1: ID validation
    print("Test 1: Enterprise ID validation")
    test_cases = [
        ("epic_id", "EPIC-ORDER", True),
        ("epic_id", "EPIC-O", False),  # Too short
        ("team_id", "TEAM-A", True),
        ("team_id", "TEAM-ABCD", False),  # Too long
        ("shared_contract_id", "SC-API-ORDER", True),
        ("shared_contract_id", "SC-XYZ-ORDER", False),  # Invalid type
        ("dependency_id", "DEP-001", True),
        ("dependency_id", "DEP-1", False),  # Wrong format
    ]

    all_passed = True
    for id_type, value, expected in test_cases:
        pattern = ENTERPRISE_ID_PATTERNS[id_type]
        result = bool(re.match(pattern, value))
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  {status} {id_type}: '{value}' -> {result} (expected {expected})")

    if not all_passed:
        print("\n❌ Some tests failed!")
        return False

    # Test 2: Coverage tier lookup
    print("\nTest 2: Coverage tier requirements")
    for tier_name, reqs in COVERAGE_TIERS.items():
        print(f"  {tier_name}: AC={reqs['ac_coverage']}%, CT={reqs['ct_coverage']}%, E2E={reqs['e2e_required']}")

    print("\n✅ All tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="stride-lint Enterprise Extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate an epic
    python3 stride_lint_enterprise.py epics/EPIC-ORDER/

    # Validate a feature with enterprise extensions
    python3 stride_lint_enterprise.py specs/FEAT-001/

    # Run full enterprise lint
    python3 stride_lint_enterprise.py --enterprise .

    # Run self-tests
    python3 stride_lint_enterprise.py --test
        """
    )

    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument("--enterprise", action="store_true", help="Run full enterprise lint")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("path", type=Path, nargs="?", help="Path to validate")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.path:
        parser.print_help()
        sys.exit(1)

    path = Path(args.path)

    # Determine project root
    if args.enterprise:
        project_root = path
    else:
        # Find project root by walking up
        project_root = path
        while project_root.parent != project_root:
            if (project_root / "memory").exists() or (project_root / "specs").exists():
                break
            project_root = project_root.parent

    validator = EnterpriseValidator(project_root)

    if args.enterprise:
        result = validator.lint_enterprise()
    elif (path / "epic_design.md").exists():
        result = validator.validate_epic(path)
    elif (path / "basic_design.md").exists():
        result = validator.validate_feature_enterprise(path)
    else:
        print(f"Error: Cannot determine type of {path}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        output = {
            "path": result.path,
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "info": result.info,
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"Enterprise Lint Results: {result.path}")
        print(f"{'=' * 50}")
        print(f"Valid: {'✅ Yes' if result.is_valid else '❌ No'}")
        print()

        if result.errors:
            print("Errors:")
            for error in result.errors:
                print(f"  ❌ {error['code']}: {error['message']}")
            print()

        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  ⚠️ {warning['code']}: {warning['message']}")
            print()

        if result.info:
            print("Info:")
            for info in result.info:
                print(f"  ℹ️ {info}")

    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
