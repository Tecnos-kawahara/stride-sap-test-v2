#!/usr/bin/env python3
"""
Approval Router - Enterprise SDD Extension
Version: 1.0.0

Purpose:
- Route approval requests to appropriate approvers based on coverage tier and gate type
- Validate approver authority
- Check parallel processing eligibility
- Apply escalation rules

Usage:
    python3 approval_router.py route <feature_dir> <gate_type>
    python3 approval_router.py validate <feature_dir> <gate_type> <approver_role>
    python3 approval_router.py parallel <feature_dir> <gate_type>
    python3 approval_router.py --test
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
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# Default approval matrix (used if no custom matrix is found)
DEFAULT_APPROVAL_MATRIX = {
    "roles": {
        "TECH_LEAD": {
            "level": "team",
            "can_approve": {
                "basic_design": ["standard", "experimental"],
                "bpmn": ["standard", "experimental"],
                "spec": ["experimental"],
                "plan": ["experimental"],
                "tasks": ["experimental"],
                "final": ["experimental"],
            }
        },
        "PM": {
            "level": "team",
            "can_approve": {
                "spec": ["standard"],
                "plan": ["standard"],
                "tasks": ["standard"],
                "final": ["standard"],  # requires co-approval with TECH_LEAD
            }
        },
        "ARCH_BOARD": {
            "level": "organization",
            "can_approve": {
                "basic_design": ["critical"],
                "bpmn": ["critical"],
                "spec": ["critical"],
                "plan": ["critical"],
                "tasks": ["critical"],
                "final": ["critical"],
                "shared_contract_change": ["*"],
                "cross_team_dependency": ["*"],
            }
        },
        "EPIC_LEAD": {
            "level": "epic",
            "can_approve": {
                "epic_design": ["*"],
                "feature_breakdown": ["*"],
                "integration_plan": ["*"],
                "epic_final": ["*"],
            }
        },
        "SECURITY_OFFICER": {
            "level": "organization",
            "can_approve": {
                "basic_design": ["critical"],
                "spec": ["critical"],
                "final": ["critical"],
            }
        },
    },
    "escalation_rules": [
        {
            "condition": "coverage_tier == 'critical'",
            "escalate_to": "ARCH_BOARD",
            "mandatory": True,
        },
        {
            "condition": "cross_team_dependency == true",
            "escalate_to": "ARCH_BOARD",
            "mandatory": True,
        },
        {
            "condition": "shared_contract_change == true",
            "escalate_to": "ARCH_BOARD",
            "mandatory": True,
        },
        {
            "condition": "security_sensitive == true AND coverage_tier == 'critical'",
            "escalate_to": "SECURITY_OFFICER",
            "mandatory": True,
        },
        {
            "condition": "erp_integration == true",
            "escalate_to": "ARCH_BOARD",
            "mandatory": True,
        },
    ],
    "parallel_processing": {
        "rules": [
            {
                "gate_type": "spec",
                "can_parallel_with": ["plan"],
                "condition": "same_team AND coverage_tier in ['standard', 'experimental']",
            },
            {
                "gate_type": "basic_design",
                "can_parallel_with": ["bpmn"],
                "condition": "same_feature",
            },
        ]
    },
    "co_approval": {
        "final": {
            "standard": ["PM", "TECH_LEAD"],
        }
    }
}


@dataclass
class FeatureContext:
    """Context for a feature being evaluated."""
    feature_id: str
    team_id: str
    coverage_tier: str
    epic_id: Optional[str] = None
    has_cross_team_deps: bool = False
    has_shared_contract_changes: bool = False
    security_sensitive: bool = False
    erp_integration: bool = False

    @classmethod
    def from_basic_design(cls, basic_design_path: Path) -> Optional['FeatureContext']:
        """Extract context from basic_design.md."""
        try:
            with open(basic_design_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML block
            match = re.search(r'```yaml\s*(.*?)```', content, re.DOTALL)
            if not match:
                return None

            data = yaml.safe_load(match.group(1))
            if not data:
                return None

            # Try different possible structures
            bd = data.get("basic_design", data)
            meta = bd.get("meta", bd)

            feature_id = meta.get("feature_id") or "UNKNOWN"
            # Use `or` fallback to handle null values (not just missing keys)
            team_id = bd.get("team_id") or meta.get("team_id") or ""
            coverage_tier = bd.get("coverage_tier") or meta.get("coverage_tier") or "standard"
            epic_id = bd.get("epic_ref") or meta.get("epic_ref")

            # Extract security_sensitive and erp_integration flags
            # Support both root level and nfr nested location for backward compatibility
            nfr = bd.get("nfr", {})
            # Root level takes precedence, fallback to nfr
            security_sensitive = bd.get("security_sensitive", nfr.get("security_sensitive", False))
            erp_integration = bd.get("erp_integration", nfr.get("erp_integration", False))

            # Detect cross-team deps and shared contract changes from feature directory
            feature_dir = basic_design_path.parent
            has_cross_team_deps = cls._detect_cross_team_deps(feature_dir, team_id)
            has_shared_contract_changes = cls._detect_shared_contract_changes(feature_dir)

            return cls(
                feature_id=feature_id,
                team_id=team_id,
                coverage_tier=coverage_tier,
                epic_id=epic_id,
                has_cross_team_deps=has_cross_team_deps,
                has_shared_contract_changes=has_shared_contract_changes,
                security_sensitive=security_sensitive,
                erp_integration=erp_integration,
            )
        except Exception:
            return None

    @staticmethod
    def _detect_cross_team_deps(feature_dir: Path, own_team_id: str = None) -> bool:
        """Detect cross-team dependencies from dependency_manifest.yaml or cross_refs.yaml.

        Cross-team is detected when:
        - external_dependencies has owner_team != own team_id
        - epic_cross_refs.related_features has relationship "depends_on"
        """
        # Check dependencies/dependency_manifest.yaml
        dep_manifest = feature_dir / "dependencies" / "dependency_manifest.yaml"
        if dep_manifest.exists():
            try:
                with open(dep_manifest, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                manifest = data.get("dependency_manifest", data)

                # Get own team_id from manifest if not provided
                if own_team_id is None:
                    feature_info = manifest.get("feature_info", {})
                    own_team_id = feature_info.get("team_id")

                # Check external_dependencies for cross-team
                ext_deps = manifest.get("external_dependencies", [])
                for dep in ext_deps:
                    owner_team = dep.get("owner_team")
                    # Cross-team if owner_team differs and is not null/PLATFORM
                    if owner_team and own_team_id and owner_team != own_team_id:
                        if owner_team not in ["PLATFORM", "SHARED"]:
                            return True
            except Exception:
                pass

        # Check specs/<feature>/cross_refs.yaml (NOT in dependencies/)
        cross_refs_path = feature_dir / "cross_refs.yaml"
        if cross_refs_path.exists():
            try:
                with open(cross_refs_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                cross_refs = data.get("cross_refs", data)

                # Get own team_id from cross_refs if not provided
                if own_team_id is None:
                    feature_info = cross_refs.get("feature_info", {})
                    own_team_id = feature_info.get("team_id")

                # Check external_dependencies for cross-team
                ext_deps = cross_refs.get("external_dependencies", [])
                for dep in ext_deps:
                    owner_team = dep.get("owner_team")
                    if owner_team and own_team_id and owner_team != own_team_id:
                        if owner_team not in ["PLATFORM", "SHARED"]:
                            return True

                # Check epic_cross_refs.related_features
                # Trigger cross-team if:
                # - cross_team: true (explicit)
                # - cross_team not specified AND relationship == "depends_on" (backward compat)
                # Do NOT trigger if cross_team: false (explicit same-team)
                epic_refs = cross_refs.get("epic_cross_refs", {})
                related_features = epic_refs.get("related_features", [])
                for rel in related_features:
                    cross_team_flag = rel.get("cross_team")
                    if cross_team_flag is True:
                        return True
                    elif cross_team_flag is None and rel.get("relationship") == "depends_on":
                        # Backward compatibility: unspecified cross_team with depends_on
                        # assumes cross-team (conservative, triggers escalation)
                        return True
                    # cross_team: false → explicitly same-team, don't trigger
            except Exception:
                pass

        return False

    @staticmethod
    def _detect_shared_contract_changes(feature_dir: Path) -> bool:
        """Detect shared contract changes.

        Shared contract change is detected when:
        - contracts/CONSUMERS.yaml has consumers (we own a contract others use)
        - dependency_manifest.exposed_contracts.consumers_registry points to file with consumers
        - cross_refs.exposed_contracts has registered_consumers
        - cross_refs.epic_cross_refs.shared_contracts has role: owner
        """
        # Check contracts/CONSUMERS.yaml
        consumers = feature_dir / "contracts" / "CONSUMERS.yaml"
        if consumers.exists():
            try:
                with open(consumers, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                consumer_list = data.get("consumers", [])
                if consumer_list and len(consumer_list) > 0:
                    return True
            except Exception:
                pass

        # Check dependency_manifest for exposed_contracts with consumers
        dep_manifest = feature_dir / "dependencies" / "dependency_manifest.yaml"
        if dep_manifest.exists():
            try:
                with open(dep_manifest, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                manifest = data.get("dependency_manifest", data)
                exposed = manifest.get("exposed_contracts", [])
                for contract in exposed:
                    # If consumers_registry is defined, read the file and check for actual consumers
                    reg_path = contract.get("consumers_registry")
                    if reg_path:
                        full_path = feature_dir / reg_path
                        if full_path.exists():
                            try:
                                with open(full_path, 'r', encoding='utf-8') as rf:
                                    reg_data = yaml.safe_load(rf)
                                consumers = reg_data.get("consumers", []) if reg_data else []
                                if consumers and len(consumers) > 0:
                                    return True
                            except Exception:
                                pass
            except Exception:
                pass

        # Check cross_refs.yaml for exposed_contracts with registered_consumers
        cross_refs_path = feature_dir / "cross_refs.yaml"
        if cross_refs_path.exists():
            try:
                with open(cross_refs_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                cross_refs = data.get("cross_refs", data)
                exposed = cross_refs.get("exposed_contracts", [])
                for contract in exposed:
                    consumers = contract.get("registered_consumers", [])
                    if consumers and len(consumers) > 0:
                        return True

                # Also check epic_cross_refs.shared_contracts where we're owner
                epic_refs = cross_refs.get("epic_cross_refs", {})
                shared_contracts = epic_refs.get("shared_contracts", [])
                for sc in shared_contracts:
                    if sc.get("role") == "owner":
                        return True
            except Exception:
                pass

        return False

    @classmethod
    def from_epic_design(cls, epic_design_path: Path) -> Optional['FeatureContext']:
        """Extract context from epic_design.md."""
        try:
            with open(epic_design_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract YAML block
            match = re.search(r'```yaml\s*(.*?)```', content, re.DOTALL)
            if not match:
                return None

            data = yaml.safe_load(match.group(1))
            if not data:
                return None

            epic = data.get("epic", data)
            meta = epic.get("meta", {})
            ownership = epic.get("ownership", {})

            epic_id = meta.get("epic_id", "UNKNOWN")

            # For Epic, use the first team or Epic Lead's team
            teams = ownership.get("teams", [])
            team_id = teams[0].get("team_id", "") if teams else ""

            # For Epic-level approvals, default to critical
            coverage_tier = "critical"

            # Check for cross-team dependencies
            cross_deps = epic.get("cross_team_dependencies", [])
            has_cross_team_deps = len(cross_deps) > 0

            # Check for shared contracts
            shared_contracts = epic.get("shared_contracts", [])
            has_shared_contract_changes = len(shared_contracts) > 0

            return cls(
                feature_id=epic_id,  # Use epic_id as feature_id for routing
                team_id=team_id,
                coverage_tier=coverage_tier,
                epic_id=epic_id,
                has_cross_team_deps=has_cross_team_deps,
                has_shared_contract_changes=has_shared_contract_changes,
            )
        except Exception:
            return None


class ApprovalRouter:
    """Routes approvals based on coverage tier and gate type."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.matrix = self._load_approval_matrix()

    def _load_approval_matrix(self) -> Dict:
        """Load approval matrix from file or use default."""
        matrix_path = self.base_dir / "memory" / "approval_matrix.yaml"
        if matrix_path.exists():
            try:
                with open(matrix_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                if data and "approval_matrix" in data:
                    return self._normalize_matrix(data["approval_matrix"])
            except Exception:
                pass
        return DEFAULT_APPROVAL_MATRIX

    def _normalize_matrix(self, matrix: Dict) -> Dict:
        """Normalize matrix structure from YAML format."""
        normalized = {
            "roles": {},
            "escalation_rules": matrix.get("escalation_rules", []),
            "parallel_processing": matrix.get("parallel_processing", {}),
            "co_approval": matrix.get("co_approval", {}),  # Preserve co_approval from YAML
        }

        for role in matrix.get("roles", []):
            role_id = role.get("role_id")
            if role_id:
                normalized["roles"][role_id] = {
                    "level": role.get("level", "team"),
                    "can_approve": {},
                }
                for approval in role.get("can_approve", []):
                    gate = approval.get("gate_type")
                    tiers = approval.get("coverage_tiers", [])
                    if gate:
                        normalized["roles"][role_id]["can_approve"][gate] = tiers

                    # Extract requires_co_approval and convert to co_approval format
                    # Template format: requires_co_approval: ["TECH_LEAD"]
                    # Internal format: co_approval.gate.tier = [roles]
                    co_approvers = approval.get("requires_co_approval", [])
                    if co_approvers and gate:
                        if gate not in normalized["co_approval"]:
                            normalized["co_approval"][gate] = {}
                        for tier in tiers:
                            if tier == "*":
                                # Wildcard tier applies to all standard tiers
                                for t in ["critical", "standard", "experimental"]:
                                    if t not in normalized["co_approval"][gate]:
                                        normalized["co_approval"][gate][t] = []
                                    for ca in co_approvers:
                                        if ca not in normalized["co_approval"][gate][t]:
                                            normalized["co_approval"][gate][t].append(ca)
                            else:
                                if tier not in normalized["co_approval"][gate]:
                                    normalized["co_approval"][gate][tier] = []
                                for ca in co_approvers:
                                    if ca not in normalized["co_approval"][gate][tier]:
                                        normalized["co_approval"][gate][tier].append(ca)

        return normalized

    def get_required_approvers(
        self,
        context: FeatureContext,
        gate_type: str
    ) -> List[str]:
        """Determine required approvers for a gate."""
        tier = context.coverage_tier
        required = []

        # Check each role
        for role_id, role_config in self.matrix.get("roles", {}).items():
            can_approve = role_config.get("can_approve", {})

            # Check if role can approve this gate for this tier
            if gate_type in can_approve:
                allowed_tiers = can_approve[gate_type]
                if "*" in allowed_tiers or tier in allowed_tiers:
                    required.append(role_id)

            # Check wildcard gate
            if "*" in can_approve:
                allowed_tiers = can_approve["*"]
                if "*" in allowed_tiers or tier in allowed_tiers:
                    if role_id not in required:
                        required.append(role_id)

        # Apply escalation rules
        escalations = self._apply_escalation_rules(context, gate_type)
        for escalation in escalations:
            if escalation not in required:
                required.append(escalation)

        # Filter to most appropriate approvers, preserving escalated roles
        return self._filter_approvers(required, tier, escalated=escalations)

    def _apply_escalation_rules(
        self,
        context: FeatureContext,
        gate_type: str
    ) -> List[str]:
        """Apply escalation rules based on context."""
        escalations = []

        for rule in self.matrix.get("escalation_rules", []):
            condition = rule.get("condition", "")
            escalate_to = rule.get("escalate_to")

            if not escalate_to:
                continue

            # Evaluate condition using proper AND/OR parsing
            triggered = self._evaluate_condition(condition, context)

            if triggered and rule.get("mandatory", False):
                escalations.append(escalate_to)

        return escalations

    def _evaluate_condition(self, condition: str, context: FeatureContext) -> bool:
        """Evaluate a condition string with AND/OR support.

        Supported conditions:
        - coverage_tier == 'critical' / 'standard' / 'experimental'
        - cross_team_dependency == true
        - shared_contract_change == true
        - security_sensitive == true
        - erp_integration == true

        Operators: AND, OR (AND has higher precedence)
        """
        if not condition or not condition.strip():
            return False

        # Build context dict for evaluation
        ctx_vars = {
            "coverage_tier": context.coverage_tier,
            "cross_team_dependency": context.has_cross_team_deps,
            "shared_contract_change": context.has_shared_contract_changes,
            "security_sensitive": context.security_sensitive,
            "erp_integration": context.erp_integration,
        }

        # Split by OR first (lower precedence)
        or_parts = re.split(r'\s+OR\s+', condition, flags=re.IGNORECASE)
        for or_part in or_parts:
            # Split by AND (higher precedence)
            and_parts = re.split(r'\s+AND\s+', or_part, flags=re.IGNORECASE)
            all_and_true = True

            for and_part in and_parts:
                part_result = self._evaluate_single_condition(and_part.strip(), ctx_vars)
                if not part_result:
                    all_and_true = False
                    break

            if all_and_true:
                return True

        return False

    def _evaluate_single_condition(self, condition: str, ctx_vars: Dict) -> bool:
        """Evaluate a single condition (no AND/OR)."""
        # Pattern: var == 'value' or var == true/false
        match = re.match(r"(\w+)\s*==\s*['\"]?(\w+)['\"]?", condition)
        if not match:
            return False

        var_name = match.group(1)
        expected_value = match.group(2)

        actual_value = ctx_vars.get(var_name)
        if actual_value is None:
            return False

        # Handle boolean comparisons
        if expected_value.lower() == "true":
            return actual_value is True
        elif expected_value.lower() == "false":
            return actual_value is False
        else:
            # String comparison
            return str(actual_value) == expected_value

    def _filter_approvers(self, approvers: List[str], tier: str, escalated: List[str] = None) -> List[str]:
        """Filter to get the most appropriate approvers.

        Note: This method keeps all approvers that were collected by get_required_approvers,
        as they're already validated for the specific gate+tier combination.
        Escalated roles are also preserved.

        The approvers list already contains only roles authorized for this gate+tier,
        so we don't need aggressive filtering that could drop legitimate approvers
        like EPIC_LEAD for epic gates or SECURITY_OFFICER for security-sensitive features.
        """
        if escalated is None:
            escalated = []

        # Start with all escalated roles (mandatory)
        result = list(escalated)

        # Add all tier-authorized approvers (already validated by get_required_approvers)
        for approver in approvers:
            if approver not in result:
                result.append(approver)

        return sorted(set(result)) if result else sorted(approvers)

    def validate_approver(
        self,
        context: FeatureContext,
        gate_type: str,
        approver_role: str
    ) -> Tuple[bool, str]:
        """
        Validate if an approver has authority for this gate.
        Returns (is_valid, reason)

        An approver is valid if:
        1. Their can_approve list includes this gate/tier combination, OR
        2. They are required via escalation rules (e.g., ARCH_BOARD for cross_team_dependency), OR
        3. They are required as a co-approver (e.g., TECH_LEAD for standard final)
        """
        tier = context.coverage_tier

        # Check if role exists
        if approver_role not in self.matrix.get("roles", {}):
            return False, f"Unknown role: {approver_role}"

        role_config = self.matrix["roles"][approver_role]
        can_approve = role_config.get("can_approve", {})

        # Check gate-specific approval
        if gate_type in can_approve:
            allowed_tiers = can_approve[gate_type]
            if "*" in allowed_tiers or tier in allowed_tiers:
                return True, f"{approver_role} is authorized for {gate_type} at {tier} tier"

        # Check wildcard gate
        if "*" in can_approve:
            allowed_tiers = can_approve["*"]
            if "*" in allowed_tiers or tier in allowed_tiers:
                return True, f"{approver_role} has wildcard approval authority"

        # Check if role is required via escalation rules
        escalations = self._apply_escalation_rules(context, gate_type)
        if approver_role in escalations:
            return True, f"{approver_role} is authorized via escalation rule"

        # Check if role is required as a co-approver
        co_approvers = self.get_co_approvers(context, gate_type)
        if approver_role in co_approvers:
            return True, f"{approver_role} is authorized as co-approver for {gate_type} at {tier} tier"

        # Not authorized
        required = self.get_required_approvers(context, gate_type)
        return False, f"{approver_role} is not authorized for {gate_type} at {tier} tier. Required: {required}"

    def check_parallel_eligibility(
        self,
        context: FeatureContext,
        gate_type: str
    ) -> Tuple[bool, List[str]]:
        """
        Check if gate can be processed in parallel with others.
        Returns (can_parallel, parallel_gates)
        """
        parallel_config = self.matrix.get("parallel_processing", {})

        # Check if parallel processing is enabled
        if not parallel_config.get("enabled", True):
            return False, []

        parallel_rules = parallel_config.get("rules", [])

        for rule in parallel_rules:
            if rule.get("gate_type") == gate_type:
                condition = rule.get("condition", "")
                can_parallel_with = rule.get("can_parallel_with", [])

                # Evaluate condition
                condition_met = True

                if "same_team" in condition:
                    # Always true for single feature
                    pass

                if "coverage_tier in" in condition:
                    # Extract allowed tiers from condition
                    match = re.search(r"coverage_tier in \[([^\]]+)\]", condition)
                    if match:
                        allowed = [t.strip().strip("'\"") for t in match.group(1).split(",")]
                        if context.coverage_tier not in allowed:
                            condition_met = False

                if condition_met and can_parallel_with:
                    return True, can_parallel_with

        return False, []

    def get_co_approvers(
        self,
        context: FeatureContext,
        gate_type: str
    ) -> List[str]:
        """Get co-approvers required for a gate."""
        tier = context.coverage_tier
        co_approval = self.matrix.get("co_approval", {})

        if gate_type in co_approval:
            tier_config = co_approval[gate_type]
            if tier in tier_config:
                return tier_config[tier]

        return []


def run_tests():
    """Run basic self-tests."""
    print("Running approval_router.py self-tests...\n")

    # Create a test router with default matrix
    router = ApprovalRouter(Path("."))

    # Test 1: Critical tier routing
    print("Test 1: Critical tier routing")
    ctx = FeatureContext(
        feature_id="FEAT-001",
        team_id="TEAM-A",
        coverage_tier="critical"
    )
    approvers = router.get_required_approvers(ctx, "spec")
    if "ARCH_BOARD" in approvers:
        print(f"  ✅ Critical tier routes to ARCH_BOARD: {approvers}")
    else:
        print(f"  ❌ Expected ARCH_BOARD, got: {approvers}")
        return False

    # Test 2: Standard tier routing
    print("Test 2: Standard tier routing")
    ctx2 = FeatureContext(
        feature_id="FEAT-002",
        team_id="TEAM-A",
        coverage_tier="standard"
    )
    approvers2 = router.get_required_approvers(ctx2, "spec")
    if "PM" in approvers2:
        print(f"  ✅ Standard tier routes to PM: {approvers2}")
    else:
        print(f"  ❌ Expected PM, got: {approvers2}")
        return False

    # Test 3: Experimental tier routing
    print("Test 3: Experimental tier routing")
    ctx3 = FeatureContext(
        feature_id="FEAT-003",
        team_id="TEAM-A",
        coverage_tier="experimental"
    )
    approvers3 = router.get_required_approvers(ctx3, "spec")
    if "TECH_LEAD" in approvers3:
        print(f"  ✅ Experimental tier routes to TECH_LEAD: {approvers3}")
    else:
        print(f"  ❌ Expected TECH_LEAD, got: {approvers3}")
        return False

    # Test 4: Approver validation
    print("Test 4: Approver validation")
    valid, reason = router.validate_approver(ctx2, "spec", "PM")
    if valid:
        print(f"  ✅ PM is valid for standard spec: {reason}")
    else:
        print(f"  ❌ PM should be valid: {reason}")
        return False

    valid2, reason2 = router.validate_approver(ctx2, "spec", "TECH_LEAD")
    if not valid2:
        print(f"  ✅ TECH_LEAD correctly rejected for standard spec: {reason2}")
    else:
        print(f"  ❌ TECH_LEAD should be rejected for standard spec")
        return False

    # Test 5: Parallel eligibility
    print("Test 5: Parallel eligibility")
    can_parallel, parallel_gates = router.check_parallel_eligibility(ctx3, "spec")
    if can_parallel and "plan" in parallel_gates:
        print(f"  ✅ Spec can parallel with: {parallel_gates}")
    else:
        print(f"  ⚠️ Parallel check: {can_parallel}, gates: {parallel_gates}")

    # Test 6: Cross-team escalation
    print("Test 6: Cross-team escalation")
    ctx4 = FeatureContext(
        feature_id="FEAT-004",
        team_id="TEAM-A",
        coverage_tier="standard",
        has_cross_team_deps=True
    )
    approvers4 = router.get_required_approvers(ctx4, "spec")
    if "ARCH_BOARD" in approvers4:
        print(f"  ✅ Cross-team deps escalate to ARCH_BOARD: {approvers4}")
    else:
        print(f"  ❌ Expected ARCH_BOARD escalation, got: {approvers4}")
        return False

    # Test 6b: validate_approver accepts escalation-required approvers
    # ARCH_BOARD is not in can_approve for standard/spec, but is required via escalation
    is_valid, reason = router.validate_approver(ctx4, "spec", "ARCH_BOARD")
    if is_valid and "escalation" in reason.lower():
        print(f"  ✅ ARCH_BOARD validated via escalation: {reason}")
    else:
        print(f"  ❌ ARCH_BOARD should be valid via escalation: {reason}")
        return False

    # Test 6c: validate_approver rejects unauthorized non-escalation approvers
    ctx_no_escalation = FeatureContext(
        feature_id="FEAT-005",
        team_id="TEAM-A",
        coverage_tier="standard",
        has_cross_team_deps=False,  # No escalation triggers
    )
    is_valid_no_esc, reason_no_esc = router.validate_approver(ctx_no_escalation, "spec", "ARCH_BOARD")
    if not is_valid_no_esc:
        print(f"  ✅ ARCH_BOARD correctly rejected without escalation: {reason_no_esc}")
    else:
        print(f"  ❌ ARCH_BOARD should be rejected without escalation trigger")
        return False

    # Test 7: requires_co_approval normalization
    print("Test 7: requires_co_approval normalization")
    test_yaml_matrix = {
        "roles": [
            {
                "role_id": "PM",
                "level": "team",
                "can_approve": [
                    {
                        "gate_type": "final",
                        "coverage_tiers": ["standard"],
                        "requires_co_approval": ["TECH_LEAD"]
                    }
                ]
            },
            {
                "role_id": "TECH_LEAD",
                "level": "team",
                "can_approve": [
                    {
                        "gate_type": "basic_design",
                        "coverage_tiers": ["standard", "experimental"]
                    }
                ]
            }
        ]
    }
    normalized = router._normalize_matrix(test_yaml_matrix)
    co_approval = normalized.get("co_approval", {})
    if "final" in co_approval and "standard" in co_approval["final"]:
        if "TECH_LEAD" in co_approval["final"]["standard"]:
            print(f"  ✅ requires_co_approval converted: {co_approval}")
        else:
            print(f"  ❌ TECH_LEAD not in co_approval: {co_approval}")
            return False
    else:
        print(f"  ❌ co_approval structure incorrect: {co_approval}")
        return False

    # Test 8: Get co-approvers
    print("Test 8: Get co-approvers")
    # Use a router with the normalized matrix
    router._ApprovalRouter__matrix = normalized  # Inject test matrix
    router.matrix = normalized
    co_approvers = router.get_co_approvers(ctx2, "final")
    if "TECH_LEAD" in co_approvers:
        print(f"  ✅ Co-approvers for standard final: {co_approvers}")
    else:
        print(f"  ⚠️ Expected TECH_LEAD as co-approver, got: {co_approvers}")

    # Test 8b: validate_approver accepts co-approvers
    # TECH_LEAD is not in can_approve for standard/final as primary,
    # but is required as co-approver via requires_co_approval
    is_valid_co, reason_co = router.validate_approver(ctx2, "final", "TECH_LEAD")
    if is_valid_co and "co-approver" in reason_co.lower():
        print(f"  ✅ TECH_LEAD validated as co-approver: {reason_co}")
    else:
        print(f"  ❌ TECH_LEAD should be valid as co-approver: {reason_co}")
        return False

    # Test 9: Integration test - load fixed YAML fixture
    print("Test 9: Integration test - fixture YAML file loading")

    # Use fixed test fixture (not template which may change)
    script_dir = Path(__file__).parent
    fixture_path = script_dir / "test_fixtures" / "approval_matrix_fixture.yaml"

    if not fixture_path.exists():
        print(f"  ❌ FAIL: Test fixture not found at {fixture_path}")
        print(f"     CI cannot verify integration behavior without fixtures.")
        return False

    try:
        with open(fixture_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)

        matrix_data = yaml_content.get("approval_matrix", yaml_content)

        # Create a new router and normalize the fixture YAML data
        test_router = ApprovalRouter(Path("."))
        normalized_yaml = test_router._normalize_matrix(matrix_data)

        # Verify requires_co_approval was extracted from PM's final gate
        # In the fixture: PM can_approve final with requires_co_approval: ["TECH_LEAD"]
        co_approval = normalized_yaml.get("co_approval", {})

        if "final" in co_approval and "standard" in co_approval.get("final", {}):
            co_approvers_from_yaml = co_approval["final"]["standard"]
            if "TECH_LEAD" in co_approvers_from_yaml:
                print(f"  ✅ requires_co_approval extracted from fixture YAML: {co_approvers_from_yaml}")
            else:
                print(f"  ❌ TECH_LEAD not found in co_approval: {co_approvers_from_yaml}")
                return False
        else:
            print(f"  ❌ co_approval structure not properly normalized from YAML: {co_approval}")
            return False

        # Verify roles were normalized correctly
        roles = normalized_yaml.get("roles", {})
        if "PM" in roles and "TECH_LEAD" in roles and "ARCH_BOARD" in roles:
            print(f"  ✅ All expected roles normalized from fixture YAML: {list(roles.keys())}")
        else:
            print(f"  ❌ Missing expected roles in normalized matrix: {list(roles.keys())}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to load/parse fixture YAML: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 10: escalation_rules and parallel_processing from YAML
    print("Test 10: escalation_rules and parallel_processing from YAML")

    try:
        # Re-use the yaml_content from Test 9
        with open(fixture_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)

        matrix_data = yaml_content.get("approval_matrix", yaml_content)
        test_router = ApprovalRouter(Path("."))
        normalized = test_router._normalize_matrix(matrix_data)

        # Verify escalation_rules were preserved (condition format)
        escalation = normalized.get("escalation_rules", [])
        if len(escalation) >= 2:
            # Check for condition-based rules (not trigger-based)
            conditions = [r.get("condition") for r in escalation]
            rule_ids = [r.get("rule_id") for r in escalation]
            has_cross_team = any("cross_team_dependency" in (c or "") for c in conditions)
            has_contract_change = any("shared_contract_change" in (c or "") for c in conditions)

            if has_cross_team and has_contract_change and all(rule_ids):
                print(f"  ✅ escalation_rules loaded from YAML (condition format): {rule_ids}")
            else:
                print(f"  ❌ Expected condition-based escalation rules not found: {conditions}")
                return False
        else:
            print(f"  ❌ escalation_rules not properly loaded: {escalation}")
            return False

        # Verify parallel_processing was preserved
        parallel = normalized.get("parallel_processing", {})
        if parallel.get("enabled") is True:
            rules = parallel.get("rules", [])
            if len(rules) >= 1 and rules[0].get("gate_type") == "spec":
                can_parallel = rules[0].get("can_parallel_with", [])
                if "plan" in can_parallel:
                    print(f"  ✅ parallel_processing loaded from YAML: spec can parallel with {can_parallel}")
                else:
                    print(f"  ❌ Expected 'plan' in can_parallel_with: {can_parallel}")
                    return False
            else:
                print(f"  ❌ parallel_processing rules not properly loaded: {rules}")
                return False
        else:
            print(f"  ❌ parallel_processing.enabled not True: {parallel}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to verify escalation/parallel from YAML: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 11: Routing with YAML-derived matrix (not just normalization)
    print("Test 11: Routing behavior with YAML-derived matrix")

    try:
        # Load fixture and create router with YAML-derived matrix
        with open(fixture_path, 'r', encoding='utf-8') as f:
            yaml_content = yaml.safe_load(f)

        matrix_data = yaml_content.get("approval_matrix", yaml_content)
        yaml_router = ApprovalRouter(Path("."))
        yaml_router.matrix = yaml_router._normalize_matrix(matrix_data)

        # Test routing with YAML-derived matrix
        # Critical tier should route to ARCH_BOARD (from YAML)
        ctx_critical = FeatureContext(
            feature_id="FEAT-TEST-001",
            team_id="TEAM-A",
            coverage_tier="critical",
        )
        critical_approvers = yaml_router.get_required_approvers(ctx_critical, "spec")
        if "ARCH_BOARD" in critical_approvers:
            print(f"  ✅ YAML matrix routing: critical spec -> {critical_approvers}")
        else:
            print(f"  ❌ Expected ARCH_BOARD for critical spec, got: {critical_approvers}")
            return False

        # Standard tier should route to PM (from YAML)
        ctx_standard = FeatureContext(
            feature_id="FEAT-TEST-002",
            team_id="TEAM-B",
            coverage_tier="standard",
        )
        standard_approvers = yaml_router.get_required_approvers(ctx_standard, "spec")
        if "PM" in standard_approvers:
            print(f"  ✅ YAML matrix routing: standard spec -> {standard_approvers}")
        else:
            print(f"  ❌ Expected PM for standard spec, got: {standard_approvers}")
            return False

        # Experimental tier should route to TECH_LEAD (from YAML)
        ctx_experimental = FeatureContext(
            feature_id="FEAT-TEST-003",
            team_id="TEAM-C",
            coverage_tier="experimental",
        )
        exp_approvers = yaml_router.get_required_approvers(ctx_experimental, "spec")
        if "TECH_LEAD" in exp_approvers:
            print(f"  ✅ YAML matrix routing: experimental spec -> {exp_approvers}")
        else:
            print(f"  ❌ Expected TECH_LEAD for experimental spec, got: {exp_approvers}")
            return False

        # Test co-approval with YAML matrix (PM + TECH_LEAD for standard final)
        co_approvers = yaml_router.get_co_approvers(ctx_standard, "final")
        if "TECH_LEAD" in co_approvers:
            print(f"  ✅ YAML matrix co-approval: standard final -> {co_approvers}")
        else:
            print(f"  ❌ Expected TECH_LEAD as co-approver for standard final, got: {co_approvers}")
            return False

        # Test escalation with YAML matrix (cross_team_deps triggers escalation)
        ctx_cross_team = FeatureContext(
            feature_id="FEAT-TEST-004",
            team_id="TEAM-D",
            coverage_tier="standard",
            has_cross_team_deps=True,
        )
        escalated_approvers = yaml_router.get_required_approvers(ctx_cross_team, "spec")
        # Should include PM (standard spec) + ARCH_BOARD (escalation target from YAML)
        if "PM" in escalated_approvers and "ARCH_BOARD" in escalated_approvers:
            print(f"  ✅ YAML matrix escalation: cross_team_deps -> {escalated_approvers}")
        else:
            print(f"  ❌ Expected PM + ARCH_BOARD for cross_team_deps escalation, got: {escalated_approvers}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to test routing with YAML matrix: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 12: AND condition evaluation and new escalation rules
    print("Test 12: AND condition evaluation and advanced escalation")

    try:
        router = ApprovalRouter(Path("."))

        # Test AND condition: security_sensitive AND critical tier
        # This should only trigger when BOTH conditions are true
        and_condition = "security_sensitive == true AND coverage_tier == 'critical'"

        # Case 1: Both true -> should trigger
        ctx_both_true = FeatureContext(
            feature_id="FEAT-SEC-001",
            team_id="TEAM-A",
            coverage_tier="critical",
            security_sensitive=True,
        )
        result = router._evaluate_condition(and_condition, ctx_both_true)
        if result:
            print(f"  ✅ AND condition (both true): correctly triggered")
        else:
            print(f"  ❌ AND condition (both true): should trigger but didn't")
            return False

        # Case 2: Only security_sensitive true -> should NOT trigger
        ctx_only_security = FeatureContext(
            feature_id="FEAT-SEC-002",
            team_id="TEAM-A",
            coverage_tier="standard",  # Not critical
            security_sensitive=True,
        )
        result = router._evaluate_condition(and_condition, ctx_only_security)
        if not result:
            print(f"  ✅ AND condition (only security): correctly NOT triggered")
        else:
            print(f"  ❌ AND condition (only security): should NOT trigger")
            return False

        # Case 3: Only critical tier true -> should NOT trigger
        ctx_only_critical = FeatureContext(
            feature_id="FEAT-SEC-003",
            team_id="TEAM-A",
            coverage_tier="critical",
            security_sensitive=False,  # Not security sensitive
        )
        result = router._evaluate_condition(and_condition, ctx_only_critical)
        if not result:
            print(f"  ✅ AND condition (only critical): correctly NOT triggered")
        else:
            print(f"  ❌ AND condition (only critical): should NOT trigger")
            return False

        # Test parallel_processing.enabled = false
        disabled_parallel_matrix = {
            "roles": {},
            "parallel_processing": {
                "enabled": False,
                "rules": [
                    {"gate_type": "spec", "can_parallel_with": ["plan"]}
                ]
            }
        }
        disabled_router = ApprovalRouter(Path("."))
        disabled_router.matrix = disabled_parallel_matrix

        can_parallel, gates = disabled_router.check_parallel_eligibility(ctx_both_true, "spec")
        if not can_parallel:
            print(f"  ✅ parallel_processing.enabled=false: correctly disabled")
        else:
            print(f"  ❌ parallel_processing.enabled=false: should be disabled")
            return False

        # Test erp_integration escalation
        erp_condition = "erp_integration == true"
        ctx_erp = FeatureContext(
            feature_id="FEAT-ERP-001",
            team_id="TEAM-A",
            coverage_tier="standard",
            erp_integration=True,
        )
        result = router._evaluate_condition(erp_condition, ctx_erp)
        if result:
            print(f"  ✅ ERP integration condition: correctly triggered")
        else:
            print(f"  ❌ ERP integration condition: should trigger")
            return False

    except Exception as e:
        print(f"  ❌ Failed to test AND conditions: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 13: EPIC_LEAD for epic gates at critical tier
    print("Test 13: EPIC_LEAD for epic gates and security/ERP escalation")

    # Test 13a: EPIC_LEAD is included for epic_design gate at critical tier
    ctx_epic_critical = FeatureContext(
        feature_id="EPIC-TEST",
        team_id="TEAM-A",
        coverage_tier="critical",
    )
    epic_approvers = router.get_required_approvers(ctx_epic_critical, "epic_design")
    if "EPIC_LEAD" in epic_approvers:
        print(f"  ✅ EPIC_LEAD included for epic_design at critical tier: {epic_approvers}")
    else:
        print(f"  ❌ Expected EPIC_LEAD for epic_design, got: {epic_approvers}")
        return False

    # Test 13b: SECURITY_OFFICER escalation for security_sensitive + critical
    ctx_security_critical = FeatureContext(
        feature_id="FEAT-SEC",
        team_id="TEAM-A",
        coverage_tier="critical",
        security_sensitive=True,
    )
    sec_approvers = router.get_required_approvers(ctx_security_critical, "spec")
    if "SECURITY_OFFICER" in sec_approvers and "ARCH_BOARD" in sec_approvers:
        print(f"  ✅ SECURITY_OFFICER + ARCH_BOARD for security_sensitive critical: {sec_approvers}")
    else:
        print(f"  ❌ Expected SECURITY_OFFICER + ARCH_BOARD, got: {sec_approvers}")
        return False

    # Test 13c: No SECURITY_OFFICER for security_sensitive + standard (not critical)
    ctx_security_standard = FeatureContext(
        feature_id="FEAT-SEC",
        team_id="TEAM-A",
        coverage_tier="standard",
        security_sensitive=True,
    )
    sec_std_approvers = router.get_required_approvers(ctx_security_standard, "spec")
    if "SECURITY_OFFICER" not in sec_std_approvers:
        print(f"  ✅ No SECURITY_OFFICER for security_sensitive at standard tier: {sec_std_approvers}")
    else:
        print(f"  ❌ SECURITY_OFFICER should not be included for standard tier: {sec_std_approvers}")
        return False

    # Test 13d: erp_integration escalates to ARCH_BOARD regardless of tier
    ctx_erp_standard = FeatureContext(
        feature_id="FEAT-ERP",
        team_id="TEAM-A",
        coverage_tier="standard",
        erp_integration=True,
    )
    erp_approvers = router.get_required_approvers(ctx_erp_standard, "spec")
    if "ARCH_BOARD" in erp_approvers:
        print(f"  ✅ ARCH_BOARD escalation for erp_integration at standard tier: {erp_approvers}")
    else:
        print(f"  ❌ Expected ARCH_BOARD for erp_integration, got: {erp_approvers}")
        return False

    # Test 14: FeatureContext.from_basic_design flag reading
    print("Test 14: FeatureContext.from_basic_design flag reading")

    import tempfile
    import shutil

    try:
        # Create temp feature directory with basic_design.md
        temp_dir = Path(tempfile.mkdtemp())
        feature_dir = temp_dir / "specs" / "FEAT-FLAG-TEST"
        feature_dir.mkdir(parents=True)

        # Test 14a: Read flags from root level (new template format)
        basic_design = feature_dir / "basic_design.md"
        basic_design.write_text("""
# Basic Design

```yaml
basic_design:
  meta:
    feature_id: FEAT-FLAG-TEST
  team_id: TEAM-A
  coverage_tier: critical
  security_sensitive: true
  erp_integration: true
```
""", encoding='utf-8')

        ctx = FeatureContext.from_basic_design(basic_design)
        if ctx and ctx.security_sensitive and ctx.erp_integration:
            print(f"  ✅ 14a: Flags read from root level (security_sensitive={ctx.security_sensitive}, erp_integration={ctx.erp_integration})")
        else:
            print(f"  ❌ 14a: Failed to read flags from root level")
            shutil.rmtree(temp_dir)
            return False

        # Test 14b: Read flags from nfr level (backward compat)
        basic_design.write_text("""
# Basic Design

```yaml
basic_design:
  meta:
    feature_id: FEAT-FLAG-TEST
  team_id: TEAM-A
  coverage_tier: standard
  nfr:
    security_sensitive: true
    erp_integration: true
```
""", encoding='utf-8')

        ctx = FeatureContext.from_basic_design(basic_design)
        if ctx and ctx.security_sensitive and ctx.erp_integration:
            print(f"  ✅ 14b: Flags read from nfr level (backward compat)")
        else:
            print(f"  ❌ 14b: Failed to read flags from nfr level")
            shutil.rmtree(temp_dir)
            return False

        # Test 14c: Root level takes precedence over nfr
        basic_design.write_text("""
# Basic Design

```yaml
basic_design:
  meta:
    feature_id: FEAT-FLAG-TEST
  team_id: TEAM-A
  coverage_tier: standard
  security_sensitive: false
  erp_integration: false
  nfr:
    security_sensitive: true
    erp_integration: true
```
""", encoding='utf-8')

        ctx = FeatureContext.from_basic_design(basic_design)
        if ctx and not ctx.security_sensitive and not ctx.erp_integration:
            print(f"  ✅ 14c: Root level takes precedence (security_sensitive={ctx.security_sensitive}, erp_integration={ctx.erp_integration})")
        else:
            print(f"  ❌ 14c: Root level should take precedence over nfr")
            shutil.rmtree(temp_dir)
            return False

        # Test 14d: Default to false when not specified
        basic_design.write_text("""
# Basic Design

```yaml
basic_design:
  meta:
    feature_id: FEAT-FLAG-TEST
  team_id: TEAM-A
  coverage_tier: standard
```
""", encoding='utf-8')

        ctx = FeatureContext.from_basic_design(basic_design)
        if ctx and not ctx.security_sensitive and not ctx.erp_integration:
            print(f"  ✅ 14d: Defaults to false when not specified")
        else:
            print(f"  ❌ 14d: Should default to false when not specified")
            shutil.rmtree(temp_dir)
            return False

        # Test 14e: Null values fall back to meta or defaults
        # When root-level keys exist but are null, should use meta values or defaults
        basic_design.write_text("""
# Basic Design

```yaml
basic_design:
  meta:
    feature_id: FEAT-FLAG-TEST
    team_id: TEAM-META
    coverage_tier: critical
  team_id: null
  coverage_tier: null
```
""", encoding='utf-8')

        ctx = FeatureContext.from_basic_design(basic_design)
        if ctx and ctx.team_id == "TEAM-META" and ctx.coverage_tier == "critical":
            print(f"  ✅ 14e: Null values fall back to meta (team_id={ctx.team_id}, coverage_tier={ctx.coverage_tier})")
        else:
            print(f"  ❌ 14e: Null values should fall back to meta, got team_id={ctx.team_id if ctx else None}, coverage_tier={ctx.coverage_tier if ctx else None}")
            shutil.rmtree(temp_dir)
            return False

        # Test 14f: Null values with no meta fall back to defaults
        basic_design.write_text("""
# Basic Design

```yaml
basic_design:
  meta:
    feature_id: FEAT-FLAG-TEST
  team_id: null
  coverage_tier: null
```
""", encoding='utf-8')

        ctx = FeatureContext.from_basic_design(basic_design)
        if ctx and ctx.team_id == "" and ctx.coverage_tier == "standard":
            print(f"  ✅ 14f: Null values with no meta fall back to defaults (team_id='', coverage_tier=standard)")
        else:
            print(f"  ❌ 14f: Should default to empty string / standard, got team_id={ctx.team_id if ctx else None}, coverage_tier={ctx.coverage_tier if ctx else None}")
            shutil.rmtree(temp_dir)
            return False

        shutil.rmtree(temp_dir)

    except Exception as e:
        print(f"  ❌ Test 14 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        if 'temp_dir' in dir() and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
        return False

    # Test 15: Cross-team and shared-contract detection with template-compliant schema
    print("Test 15: Cross-team and shared-contract detection")

    import tempfile
    import shutil

    try:
        # Create temp feature directory structure
        temp_dir = Path(tempfile.mkdtemp())
        feature_dir = temp_dir / "specs" / "FEAT-DETECT"
        deps_dir = feature_dir / "dependencies"
        contracts_dir = feature_dir / "contracts"
        deps_dir.mkdir(parents=True)
        contracts_dir.mkdir(parents=True)

        # Test 13a: Cross-team detection via dependency_manifest.yaml
        dep_manifest = deps_dir / "dependency_manifest.yaml"
        dep_manifest.write_text("""
dependency_manifest:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  external_dependencies:
    - dependency_id: DEP-001
      owner_team: TEAM-B
      dependency_type: api
      contract_ref: shared/contracts/api/user-service.yaml
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if result:
            print(f"  ✅ 15a: Cross-team detected via external_dependencies.owner_team")
        else:
            print(f"  ❌ 15a: Expected cross-team detection (owner_team TEAM-B != TEAM-A)")
            shutil.rmtree(temp_dir)
            return False

        # Test 14b: No cross-team when owner_team matches own team
        dep_manifest.write_text("""
dependency_manifest:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  external_dependencies:
    - dependency_id: DEP-001
      owner_team: TEAM-A
      dependency_type: api
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if not result:
            print(f"  ✅ 15b: No cross-team when owner_team == own team")
        else:
            print(f"  ❌ 15b: Should NOT detect cross-team when owner_team matches")
            shutil.rmtree(temp_dir)
            return False

        # Test 14c: No cross-team for PLATFORM/SHARED owner_team
        dep_manifest.write_text("""
dependency_manifest:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  external_dependencies:
    - dependency_id: DEP-001
      owner_team: PLATFORM
      dependency_type: api
    - dependency_id: DEP-002
      owner_team: SHARED
      dependency_type: event
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if not result:
            print(f"  ✅ 15c: No cross-team escalation for PLATFORM/SHARED")
        else:
            print(f"  ❌ 15c: Should NOT escalate for PLATFORM/SHARED owner_team")
            shutil.rmtree(temp_dir)
            return False

        # Test 14d: Cross-team via cross_refs.yaml epic_cross_refs.related_features with cross_team: true
        dep_manifest.unlink()  # Remove dependency_manifest
        cross_refs = feature_dir / "cross_refs.yaml"
        cross_refs.write_text("""
cross_refs:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  epic_cross_refs:
    related_features:
      - feature_ref: FEAT-OTHER
        relationship: depends_on
        cross_team: true
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if result:
            print(f"  ✅ 15d: Cross-team detected via cross_team: true")
        else:
            print(f"  ❌ 15d: Expected cross-team via cross_team: true flag")
            shutil.rmtree(temp_dir)
            return False

        # Test 14d2: No cross-team when cross_team: false (explicit same-team)
        cross_refs.write_text("""
cross_refs:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  epic_cross_refs:
    related_features:
      - feature_ref: FEAT-OTHER
        relationship: depends_on
        cross_team: false
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if not result:
            print(f"  ✅ 15d2: No cross-team when cross_team: false (explicit same-team)")
        else:
            print(f"  ❌ 15d2: Should NOT trigger when cross_team: false")
            shutil.rmtree(temp_dir)
            return False

        # Test 14d3: Backward compat - cross_team not specified + depends_on = triggers
        cross_refs.write_text("""
cross_refs:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  epic_cross_refs:
    related_features:
      - feature_ref: FEAT-OTHER
        relationship: depends_on
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if result:
            print(f"  ✅ 15d3: Backward compat: depends_on without cross_team triggers escalation")
        else:
            print(f"  ❌ 15d3: Expected backward compat escalation for depends_on")
            shutil.rmtree(temp_dir)
            return False

        # Test 14d4: No escalation for sibling relationship without cross_team
        cross_refs.write_text("""
cross_refs:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  epic_cross_refs:
    related_features:
      - feature_ref: FEAT-OTHER
        relationship: sibling
""", encoding='utf-8')

        result = FeatureContext._detect_cross_team_deps(feature_dir, "TEAM-A")
        if not result:
            print(f"  ✅ 15d4: No escalation for sibling relationship without cross_team")
        else:
            print(f"  ❌ 15d4: Should NOT trigger for sibling without cross_team")
            shutil.rmtree(temp_dir)
            return False

        # Test 14e: Shared contract change via CONSUMERS.yaml
        cross_refs.unlink()
        consumers = contracts_dir / "CONSUMERS.yaml"
        consumers.write_text("""
consumers:
  - consumer_team: TEAM-B
    consumer_feature: FEAT-OTHER
    api_version: "1.0"
""", encoding='utf-8')

        result = FeatureContext._detect_shared_contract_changes(feature_dir)
        if result:
            print(f"  ✅ 15e: Shared contract detected via CONSUMERS.yaml")
        else:
            print(f"  ❌ 15e: Expected shared contract detection via CONSUMERS.yaml")
            shutil.rmtree(temp_dir)
            return False

        # Test 14f: No shared contract when CONSUMERS.yaml is empty
        consumers.write_text("""
consumers: []
""", encoding='utf-8')

        result = FeatureContext._detect_shared_contract_changes(feature_dir)
        if not result:
            print(f"  ✅ 15f: No shared contract when consumers list is empty")
        else:
            print(f"  ❌ 15f: Should NOT detect shared contract with empty consumers")
            shutil.rmtree(temp_dir)
            return False

        # Test 14f2: No shared contract when consumers_registry file exists but is empty
        consumers.unlink()
        # Create dependency_manifest with consumers_registry pointing to empty file
        dep_manifest.write_text("""
dependency_manifest:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  exposed_contracts:
    - contract_id: CT-API-01
      consumers_registry: contracts/CONSUMERS.yaml
""", encoding='utf-8')
        # Create empty CONSUMERS.yaml
        consumers = contracts_dir / "CONSUMERS.yaml"
        consumers.write_text("""
consumers: []
""", encoding='utf-8')

        result = FeatureContext._detect_shared_contract_changes(feature_dir)
        if not result:
            print(f"  ✅ 15f2: No shared contract when consumers_registry file is empty")
        else:
            print(f"  ❌ 15f2: Should NOT trigger shared contract with empty consumers_registry")
            shutil.rmtree(temp_dir)
            return False

        # Clean up for next test
        dep_manifest.unlink()
        consumers.unlink()

        # Test 14g: Shared contract via cross_refs.yaml exposed_contracts.registered_consumers
        cross_refs = feature_dir / "cross_refs.yaml"
        cross_refs.write_text("""
cross_refs:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  exposed_contracts:
    - contract_id: SC-API-USER
      registered_consumers:
        - TEAM-B
        - TEAM-C
""", encoding='utf-8')

        result = FeatureContext._detect_shared_contract_changes(feature_dir)
        if result:
            print(f"  ✅ 15g: Shared contract via exposed_contracts.registered_consumers")
        else:
            print(f"  ❌ 15g: Expected shared contract via registered_consumers")
            shutil.rmtree(temp_dir)
            return False

        # Test 14h: Shared contract via epic_cross_refs.shared_contracts where role=owner
        cross_refs.write_text("""
cross_refs:
  feature_info:
    feature_id: FEAT-DETECT
    team_id: TEAM-A
  epic_cross_refs:
    shared_contracts:
      - contract_ref: SC-API-PAYMENT
        role: owner
""", encoding='utf-8')

        result = FeatureContext._detect_shared_contract_changes(feature_dir)
        if result:
            print(f"  ✅ 15h: Shared contract via epic_cross_refs.shared_contracts role=owner")
        else:
            print(f"  ❌ 15h: Expected shared contract when role=owner")
            shutil.rmtree(temp_dir)
            return False

        # Clean up
        shutil.rmtree(temp_dir)
        print(f"  ✅ Test 15: All cross-team and shared-contract detection tests passed")

    except Exception as e:
        print(f"  ❌ Test 15 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        if 'temp_dir' in dir() and temp_dir.exists():
            shutil.rmtree(temp_dir)
        return False

    print("\n✅ All tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Approval Router - Enterprise SDD Extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Get required approvers
    python3 approval_router.py route specs/FEAT-001/ spec

    # Validate an approver
    python3 approval_router.py validate specs/FEAT-001/ spec PM

    # Check parallel eligibility
    python3 approval_router.py parallel specs/FEAT-001/ spec

    # Run self-tests
    python3 approval_router.py --test
        """
    )

    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    subparsers = parser.add_subparsers(dest="command")

    # Route command
    route_parser = subparsers.add_parser("route", help="Get required approvers")
    route_parser.add_argument("feature_dir", type=Path, help="Feature directory")
    route_parser.add_argument("gate_type", type=str, help="Gate type (basic_design, spec, plan, tasks, final)")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an approver")
    validate_parser.add_argument("feature_dir", type=Path, help="Feature directory")
    validate_parser.add_argument("gate_type", type=str, help="Gate type")
    validate_parser.add_argument("approver_role", type=str, help="Approver role to validate")

    # Parallel command
    parallel_parser = subparsers.add_parser("parallel", help="Check parallel eligibility")
    parallel_parser.add_argument("feature_dir", type=Path, help="Feature directory")
    parallel_parser.add_argument("gate_type", type=str, help="Gate type")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load feature/epic context
    feature_dir = Path(args.feature_dir)
    basic_design = feature_dir / "basic_design.md"
    epic_design = feature_dir / "epic_design.md"

    context = None

    if basic_design.exists():
        context = FeatureContext.from_basic_design(basic_design)
        if not context:
            print(f"Error: Failed to parse basic_design.md", file=sys.stderr)
            sys.exit(1)
    elif epic_design.exists():
        # Handle Epic directory
        context = FeatureContext.from_epic_design(epic_design)
        if not context:
            print(f"Error: Failed to parse epic_design.md", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Error: basic_design.md or epic_design.md not found in {feature_dir}", file=sys.stderr)
        sys.exit(1)

    # Find project root (go up until we find memory/ or specs/)
    project_root = feature_dir
    while project_root.parent != project_root:
        if (project_root / "memory").exists() or (project_root / "specs").exists():
            break
        project_root = project_root.parent

    router = ApprovalRouter(project_root)

    if args.command == "route":
        approvers = router.get_required_approvers(context, args.gate_type)
        co_approvers = router.get_co_approvers(context, args.gate_type)

        if args.json:
            output = {
                "feature_id": context.feature_id,
                "coverage_tier": context.coverage_tier,
                "gate_type": args.gate_type,
                "required_approvers": approvers,
                "co_approvers": co_approvers,
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Approval Routing for: {context.feature_id}")
            print(f"{'=' * 50}")
            print(f"Coverage Tier: {context.coverage_tier}")
            print(f"Gate Type: {args.gate_type}")
            print(f"Required Approvers: {', '.join(approvers)}")
            if co_approvers:
                print(f"Co-Approvers: {', '.join(co_approvers)}")

    elif args.command == "validate":
        valid, reason = router.validate_approver(context, args.gate_type, args.approver_role)

        if args.json:
            output = {
                "valid": valid,
                "reason": reason,
                "approver_role": args.approver_role,
                "gate_type": args.gate_type,
                "coverage_tier": context.coverage_tier,
            }
            print(json.dumps(output, indent=2))
        else:
            icon = "✅" if valid else "❌"
            print(f"{icon} {reason}")

        sys.exit(0 if valid else 1)

    elif args.command == "parallel":
        can_parallel, parallel_gates = router.check_parallel_eligibility(context, args.gate_type)

        if args.json:
            output = {
                "can_parallel": can_parallel,
                "parallel_gates": parallel_gates,
                "gate_type": args.gate_type,
                "coverage_tier": context.coverage_tier,
            }
            print(json.dumps(output, indent=2))
        else:
            if can_parallel:
                print(f"✅ {args.gate_type} can be processed in parallel with: {', '.join(parallel_gates)}")
            else:
                print(f"⬜ {args.gate_type} must be processed sequentially")


if __name__ == "__main__":
    main()
