#!/usr/bin/env python3
"""
Epic Validator - Enterprise SDD Extension
Version: 1.0.0

Purpose:
- Validate epic_design.md structure and content
- Validate feature_breakdown.md structure
- Validate EPIC_APPROVAL.md gate status
- Check Epic-level gate conditions

Usage:
    python3 epic_validator.py validate <epic_dir>
    python3 epic_validator.py gates <epic_dir>
    python3 epic_validator.py features <epic_dir>
    python3 epic_validator.py --test
"""

import argparse
import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
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


# ID Conventions (from constitution.md v1.2.6)
ID_PATTERNS = {
    "epic_id": r"^EPIC-[A-Z]{3,}$",
    "team_id": r"^TEAM-[A-Z]{1,3}$",
    # v1.2.6: Extended to support team-prefixed IDs like FEAT-ORD-001
    "feature_id": r"^FEAT-(?:[A-Z]{2,4}-)?[A-Z0-9]{3,}$",
    "milestone_id": r"^EM-[0-9]{2}$",
    "integration_point_id": r"^IP-[0-9]{3}$",
    "dependency_id": r"^DEP-[0-9]{3}$",
    "shared_contract_id": r"^SC-(API|EVT|FILE)-[A-Z0-9]{3,}$",
}


@dataclass
class ValidationResult:
    """Container for validation results."""
    epic_id: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    gate_status: Dict[str, bool] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)

    def add_error(self, code: str, message: str):
        self.errors.append(f"{code}: {message}")

    def add_warning(self, code: str, message: str):
        self.warnings.append(f"{code}: {message}")

    def add_info(self, message: str):
        self.info.append(message)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


class EpicValidator:
    """Validates Epic-level SDD artifacts."""

    def __init__(self, epic_dir: Path):
        self.epic_dir = Path(epic_dir)
        self.base_dir = self.epic_dir.parent.parent  # epics/<epic>/ -> project root
        self.result = ValidationResult(epic_id="UNKNOWN")

    def load_yaml(self, path: Path) -> Optional[Dict]:
        """Load a YAML file safely."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.result.add_error("YAML_LOAD_ERROR", f"Failed to load {path}: {e}")
            return None

    def extract_yaml_from_md(self, md_path: Path) -> Optional[Dict]:
        """Extract YAML block from markdown file."""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find first YAML block
            pattern = r'```yaml\s*(.*?)```'
            match = re.search(pattern, content, re.DOTALL)

            if match:
                yaml_content = match.group(1)
                return yaml.safe_load(yaml_content)
            return None
        except Exception as e:
            self.result.add_error("YAML_EXTRACT_ERROR", f"Failed to extract YAML from {md_path}: {e}")
            return None

    def validate_id(self, id_type: str, value: str, context: str) -> bool:
        """Validate an ID against its pattern."""
        if id_type not in ID_PATTERNS:
            return True  # Unknown type, skip validation

        pattern = ID_PATTERNS[id_type]
        if not re.match(pattern, value):
            self.result.add_error(
                "ID_REGEX_MISMATCH",
                f"{context}: '{value}' does not match {id_type} pattern {pattern}"
            )
            return False
        return True

    def check_file_exists(self, filename: str, required: bool = True) -> bool:
        """Check if a file exists in the epic directory."""
        path = self.epic_dir / filename
        if not path.exists():
            if required:
                self.result.add_error("MISSING_FILE", f"Required file not found: {filename}")
            return False
        return True

    def validate_epic_design(self) -> Optional[Dict]:
        """Validate epic_design.md."""
        if not self.check_file_exists("epic_design.md"):
            return None

        data = self.extract_yaml_from_md(self.epic_dir / "epic_design.md")
        if not data or "epic" not in data:
            self.result.add_error("INVALID_STRUCTURE", "epic_design.md missing 'epic' root key")
            return None

        epic = data["epic"]

        # Validate meta
        meta = epic.get("meta", {})
        epic_id = meta.get("epic_id", "UNKNOWN")
        self.result.epic_id = epic_id

        if not epic_id or epic_id == "EPIC-XXX":
            self.result.add_error("PLACEHOLDER_VALUE", "epic_id is placeholder or missing")
        else:
            self.validate_id("epic_id", epic_id, "meta.epic_id")

        # Validate ownership
        ownership = epic.get("ownership", {})
        if not ownership.get("epic_lead"):
            self.result.add_warning("MISSING_FIELD", "ownership.epic_lead is not set")

        teams = ownership.get("teams", [])
        if not teams:
            self.result.add_error("MISSING_FIELD", "No teams defined in ownership.teams")

        team_ids = set()
        for team in teams:
            team_id = team.get("team_id")
            if team_id:
                self.validate_id("team_id", team_id, f"teams[{team_id}]")
                team_ids.add(team_id)

        # Validate features
        features = epic.get("features", [])
        self.result.counts["total_features"] = len(features)
        self.result.counts["critical_features"] = 0
        self.result.counts["standard_features"] = 0
        self.result.counts["experimental_features"] = 0

        feature_ids = set()
        for feature in features:
            fid = feature.get("feature_id")
            if fid:
                self.validate_id("feature_id", fid, f"features[{fid}]")
                feature_ids.add(fid)

            # Check team assignment
            feature_team = feature.get("team_id")
            if feature_team:
                self.validate_id("team_id", feature_team, f"features[{fid}].team_id")
                if feature_team not in team_ids:
                    self.result.add_error(
                        "INVALID_TEAM_REF",
                        f"Feature {fid} references undefined team {feature_team}"
                    )
            else:
                self.result.add_error("MISSING_FIELD", f"Feature {fid} has no team_id")

            # Count by tier
            tier = feature.get("coverage_tier", "standard")
            if tier == "critical":
                self.result.counts["critical_features"] += 1
            elif tier == "standard":
                self.result.counts["standard_features"] += 1
            elif tier == "experimental":
                self.result.counts["experimental_features"] += 1
            else:
                self.result.add_warning("INVALID_TIER", f"Feature {fid} has unknown tier: {tier}")

        # Validate cross-team dependencies
        deps = epic.get("cross_team_dependencies", [])
        self.result.counts["cross_team_dependencies"] = len(deps)

        for dep in deps:
            dep_id = dep.get("dependency_id")
            if dep_id:
                self.validate_id("dependency_id", dep_id, f"cross_team_dependencies[{dep_id}]")

            from_feature = dep.get("from_feature")
            to_feature = dep.get("to_feature")

            # Validate feature refs: FEAT-* pattern → must exist in feature_ids.
            # Non-FEAT refs (e.g., "mcframe-core") are external system dependencies — skip.
            # FEAT-prefix but malformed → warn (likely typo).
            feat_pattern = ID_PATTERNS.get("feature_id", "")
            for ref_label, ref_val in [("from_feature", from_feature), ("to_feature", to_feature)]:
                if not ref_val or ref_val in feature_ids:
                    continue
                if re.match(feat_pattern, ref_val):
                    self.result.add_error(
                        "INVALID_FEATURE_REF",
                        f"Dependency {dep_id} references undefined {ref_label}: {ref_val}"
                    )
                elif ref_val.upper().startswith("FEAT"):
                    self.result.add_warning(
                        "SUSPICIOUS_FEATURE_REF",
                        f"Dependency {dep_id}: {ref_label} '{ref_val}' looks like a Feature ID but doesn't match pattern"
                    )

        # Validate shared contracts
        contracts = epic.get("shared_contracts", [])
        self.result.counts["shared_contracts"] = len(contracts)

        for contract in contracts:
            cid = contract.get("contract_id")
            if cid:
                self.validate_id("shared_contract_id", cid, f"shared_contracts[{cid}]")

        # Validate milestones
        milestones = epic.get("milestones", [])
        for ms in milestones:
            ms_id = ms.get("id")
            if ms_id:
                self.validate_id("milestone_id", ms_id, f"milestones[{ms_id}]")

        # Validate integration points
        integration_points = epic.get("integration_points", [])
        for ip in integration_points:
            ip_id = ip.get("point_id")
            if ip_id:
                self.validate_id("integration_point_id", ip_id, f"integration_points[{ip_id}]")

        return epic

    def validate_feature_breakdown(self) -> Optional[Dict]:
        """Validate feature_breakdown.md if exists."""
        if not self.check_file_exists("feature_breakdown.md", required=False):
            return None

        data = self.extract_yaml_from_md(self.epic_dir / "feature_breakdown.md")
        if not data or "feature_breakdown" not in data:
            self.result.add_error("INVALID_STRUCTURE", "feature_breakdown.md missing 'feature_breakdown' root key")
            return None

        breakdown = data["feature_breakdown"]

        # Validate dependency graph for cycles
        dependency_graph = breakdown.get("dependency_graph", {})
        edges = dependency_graph.get("edges", [])

        # Simple cycle detection using DFS
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
                    self.result.add_error(
                        "DEPENDENCY_CYCLE",
                        f"Cycle detected in feature_breakdown: {' -> '.join(cycle)}"
                    )
                    return True

            rec_stack.remove(node)
            return False

        for node in adj:
            if node not in visited:
                has_cycle(node, [node])

        return breakdown

    def validate_epic_approval(self) -> Dict[str, bool]:
        """Validate EPIC_APPROVAL.md and extract gate status."""
        gate_status = {
            "E1_Epic_Design": False,
            "E2_Feature_Breakdown": False,
            "E3_Shared_Contract": False,
            "E4_Integration_Plan": False,
            "E5_Feature_Specs_Ready": False,
            "Final": False,
        }

        if not self.check_file_exists("EPIC_APPROVAL.md", required=False):
            self.result.add_warning("APPROVAL_FILE_MISSING", "EPIC_APPROVAL.md not found")
            return gate_status

        try:
            with open(self.epic_dir / "EPIC_APPROVAL.md", 'r', encoding='utf-8') as f:
                content = f.read()

            # Split content by gate sections to avoid cross-gate matching
            # Gate headers: "## Gate E1", "## Gate E2", etc.
            gate_sections = re.split(r'(?=## (?:Gate E\d|Final Gate))', content)

            # Helper to check if a section has basic approval (supports EN/JP)
            # Used for E1, E2, E5 which have simple approval block
            def has_basic_approval(section: str) -> bool:
                # Check for at least one checked box AND an approver name filled in
                has_checked = bool(re.search(r'\[x\]', section, re.IGNORECASE))
                # Match both Japanese and English approval patterns
                # Look for "承認者:" or "Approver:" followed by non-underscore, non-whitespace chars
                has_approver = bool(re.search(
                    r'(?:承認者|Approver):\s*([^\s_][^\n]*)',
                    section, re.IGNORECASE
                ))
                return has_checked and has_approver

            # Helper to check if a section has FINAL approval (for E3, E4, Final)
            # These gates have Team Confirmation + Final Approval sections
            # We require the Final Approval block to be filled in
            def has_final_approval(section: str) -> bool:
                # Check for checked boxes
                has_checked = bool(re.search(r'\[x\]', section, re.IGNORECASE))
                if not has_checked:
                    return False

                # Find the "Final Approval" or "最終承認" or "Epic Final Approval" subsection
                final_block_pattern = r'(?:###?\s*(?:Final Approval|最終承認|Epic最終承認|Epic Final Approval).*?)(?=###|$)'
                final_match = re.search(final_block_pattern, section, re.DOTALL | re.IGNORECASE)

                if not final_match:
                    return False

                final_block = final_match.group(0)

                # In the final block, check for approver name filled in
                has_final_approver = bool(re.search(
                    r'(?:承認者|Approver):\s*([^\s_][^\n]*)',
                    final_block, re.IGNORECASE
                ))

                return has_final_approver

            for section in gate_sections:
                if '## Gate E1' in section or '## Gate E1:' in section:
                    if has_basic_approval(section):
                        gate_status["E1_Epic_Design"] = True

                elif '## Gate E2' in section or '## Gate E2:' in section:
                    if has_basic_approval(section):
                        gate_status["E2_Feature_Breakdown"] = True

                elif '## Gate E3' in section or '## Gate E3:' in section:
                    # E3 requires Final Approval block (ARCH_BOARD)
                    if has_final_approval(section):
                        gate_status["E3_Shared_Contract"] = True

                elif '## Gate E4' in section or '## Gate E4:' in section:
                    # E4 requires Final Approval block (Epic Lead)
                    if has_final_approval(section):
                        gate_status["E4_Integration_Plan"] = True

                elif '## Gate E5' in section or '## Gate E5:' in section:
                    if has_basic_approval(section):
                        gate_status["E5_Feature_Specs_Ready"] = True

                elif '## Final Gate' in section:
                    # Final requires Epic Final Approval block
                    if has_final_approval(section):
                        gate_status["Final"] = True

        except Exception as e:
            self.result.add_error("APPROVAL_PARSE_ERROR", f"Failed to parse EPIC_APPROVAL.md: {e}")

        return gate_status

    def check_feature_specs_exist(self, epic_data: Dict) -> bool:
        """Check if all feature specs directories exist."""
        if not epic_data:
            return False

        features = epic_data.get("features", [])
        specs_dir = self.base_dir / "specs"

        all_exist = True
        for feature in features:
            fid = feature.get("feature_id")
            if fid:
                feature_dir = specs_dir / fid
                if not feature_dir.exists():
                    self.result.add_warning(
                        "FEATURE_SPEC_MISSING",
                        f"Feature spec directory not found: specs/{fid}/"
                    )
                    all_exist = False

        return all_exist

    def evaluate_gates(self, epic_data: Dict) -> Dict[str, bool]:
        """Evaluate Epic gate conditions."""
        gate_checks = {
            "all_features_have_team": True,
            "all_dependencies_mapped": True,
            "shared_contracts_defined": len(epic_data.get("shared_contracts", [])) > 0 if epic_data else False,
            "no_dependency_cycles": "DEPENDENCY_CYCLE" not in str(self.result.errors),
            "min_features_met": self.result.counts.get("total_features", 0) >= 2,
            "ready_for_feature_specs": False,
        }

        if epic_data:
            # Check all features have team
            for feature in epic_data.get("features", []):
                if not feature.get("team_id"):
                    gate_checks["all_features_have_team"] = False
                    break

            # Check all dependencies mapped
            for dep in epic_data.get("cross_team_dependencies", []):
                if not dep.get("interface"):
                    gate_checks["all_dependencies_mapped"] = False
                    break

        # Ready for feature specs if all other checks pass
        gate_checks["ready_for_feature_specs"] = all([
            gate_checks["all_features_have_team"],
            gate_checks["all_dependencies_mapped"],
            gate_checks["no_dependency_cycles"],
            gate_checks["min_features_met"],
        ])

        return gate_checks

    def validate_epic_bpmn(self):
        """Lightweight validation for epic_flow.bpmn (overview BPMN).

        This is intentionally less strict than stride_lint's feature BPMN validation.
        EPIC BPMNs are planning/architecture artifacts, not executable BPMNs.
        """
        import xml.etree.ElementTree as ET

        bpmn_path = self.epic_dir / "epic_flow.bpmn"
        if not bpmn_path.exists():
            self.result.add_warning("EPIC_BPMN_MISSING",
                                    "epic_flow.bpmn not found (optional but recommended)")
            return

        # XML parse
        try:
            tree = ET.parse(bpmn_path)
        except Exception as exc:
            self.result.add_error("EPIC_BPMN_PARSE_ERROR", f"epic_flow.bpmn: {exc}")
            return

        root = tree.getroot()

        # Root must be definitions
        if not root.tag.endswith("definitions"):
            self.result.add_error("EPIC_BPMN_INVALID", "root element is not bpmn:definitions")
            return

        # Detect bpmn namespace
        bpmn_ns = None
        bpmndi_ns = None
        for elem in root.iter():
            if "}" in elem.tag:
                uri = elem.tag.split("}", 1)[0][1:]
                if uri == "http://www.omg.org/spec/BPMN/20100524/MODEL":
                    bpmn_ns = uri
                elif uri == "http://www.omg.org/spec/BPMN/20100524/DI":
                    bpmndi_ns = uri
        if not bpmn_ns:
            self.result.add_error("EPIC_BPMN_INVALID", "missing bpmn namespace")
            return

        nsmap = {"bpmn": bpmn_ns}
        if bpmndi_ns:
            nsmap["bpmndi"] = bpmndi_ns

        # Collaboration required
        collaborations = root.findall("bpmn:collaboration", nsmap)
        if not collaborations:
            self.result.add_error("EPIC_BPMN_INVALID",
                                  "epic_flow.bpmn must have a bpmn:collaboration element")
            return

        collab = collaborations[0]
        collab_id = collab.get("id", "")

        # At least 2 participants
        participants = collab.findall("bpmn:participant", nsmap)
        if len(participants) < 2:
            self.result.add_error("EPIC_BPMN_INVALID",
                                  f"collaboration needs at least 2 participants (found {len(participants)})")

        # Each participant's processRef must reference an existing process
        process_ids = {p.get("id") for p in root.findall("bpmn:process", nsmap) if p.get("id")}
        for p in participants:
            pref = p.get("processRef")
            pid = p.get("id", "?")
            if not pref:
                self.result.add_error("EPIC_BPMN_INVALID",
                                      f"participant '{pid}' missing processRef")
            elif pref not in process_ids:
                self.result.add_error("EPIC_BPMN_INVALID",
                                      f"participant '{pid}' processRef='{pref}' not found in process definitions")

        # BPMNDiagram / BPMNPlane
        if bpmndi_ns:
            di_nsmap = {"bpmndi": bpmndi_ns}
            diagrams = root.findall("bpmndi:BPMNDiagram", di_nsmap)
            planes = root.findall(".//bpmndi:BPMNPlane", di_nsmap)
            if not diagrams or not planes:
                self.result.add_error("EPIC_BPMN_INVALID",
                                      "missing BPMNDiagram/BPMNPlane")
            else:
                # Plane should reference collaboration
                plane_ref = planes[0].get("bpmnElement", "")
                if plane_ref != collab_id:
                    self.result.add_warning("EPIC_BPMN_INVALID",
                                            f"BPMNPlane bpmnElement='{plane_ref}' should reference collaboration '{collab_id}'")

                # Each participant should have a BPMNShape with isHorizontal="false"
                all_shapes = root.findall(".//bpmndi:BPMNShape", di_nsmap)
                shape_refs = {s.get("bpmnElement") for s in all_shapes}
                for p in participants:
                    pid = p.get("id", "?")
                    if pid not in shape_refs:
                        self.result.add_warning("EPIC_BPMN_INVALID",
                                                f"participant '{pid}' has no BPMNShape")
                    else:
                        for s in all_shapes:
                            if s.get("bpmnElement") == pid:
                                if s.get("isHorizontal") != "false":
                                    self.result.add_error("EPIC_BPMN_INVALID",
                                                          f"participant '{pid}' must have isHorizontal=\"false\" (vertical swimlane required)")

                # Each messageFlow should have a BPMNEdge
                edge_refs = {e.get("bpmnElement") for e in root.findall(".//bpmndi:BPMNEdge", di_nsmap)}
                for mf in collab.findall("bpmn:messageFlow", nsmap):
                    mfid = mf.get("id", "?")
                    if mfid not in edge_refs:
                        self.result.add_warning("EPIC_BPMN_INVALID",
                                                f"messageFlow '{mfid}' has no BPMNEdge")
        else:
            self.result.add_warning("EPIC_BPMN_INVALID", "missing bpmndi namespace (no diagram)")

        # --- documentation missing warnings ---
        collab_doc = collab.find("bpmn:documentation", nsmap)
        if collab_doc is None or not (collab_doc.text and (collab_doc.text or "").strip()):
            self.result.add_warning("EPIC_BPMN_DOCUMENTATION_MISSING",
                                    "collaboration has no <documentation>")
        for p in participants:
            pid = p.get("id", "?")
            pd = p.find("bpmn:documentation", nsmap)
            if pd is None or not (pd.text and (pd.text or "").strip()):
                self.result.add_warning("EPIC_BPMN_DOCUMENTATION_MISSING",
                                        f"participant '{pid}' has no <documentation>")
        for mf in collab.findall("bpmn:messageFlow", nsmap):
            mfid = mf.get("id", "?")
            md = mf.find("bpmn:documentation", nsmap)
            if md is None or not (md.text and (md.text or "").strip()):
                self.result.add_warning("EPIC_BPMN_DOCUMENTATION_MISSING",
                                        f"messageFlow '{mfid}' has no <documentation>")

        # Check for unresolved EPIC-XXX placeholder
        try:
            with open(bpmn_path, "r", encoding="utf-8") as f:
                text = f.read()
            if "EPIC-XXX" in text:
                self.result.add_warning("EPIC_BPMN_PLACEHOLDER",
                                        "epic_flow.bpmn contains unresolved EPIC-XXX placeholder")
        except Exception:
            pass

        # --- v5.3.3: 内部 process の flow node/edge 整合性チェック ---
        # FEAT process.bpmn の validate_bpmn() と同等レベルに引上げ
        flow_node_tags = ["startEvent", "endEvent", "task", "serviceTask", "userTask",
                          "sendTask", "receiveTask", "scriptTask", "manualTask",
                          "businessRuleTask", "callActivity",
                          "exclusiveGateway", "parallelGateway", "inclusiveGateway",
                          "intermediateCatchEvent", "intermediateThrowEvent",
                          "subProcess"]
        all_inner_node_ids = set()
        all_inner_flow_ids = set()
        processes = root.findall("bpmn:process", nsmap)
        for process in processes:
            pid = process.get("id", "?")
            # Collect node IDs in this process
            process_node_ids = set()
            for tag in flow_node_tags:
                for node in process.findall(f"bpmn:{tag}", nsmap):
                    nid = node.get("id")
                    if nid:
                        process_node_ids.add(nid)
                        all_inner_node_ids.add(nid)
                    # incoming/outgoing check
                    node_id = nid or "?"
                    incoming = node.findall("bpmn:incoming", nsmap)
                    outgoing = node.findall("bpmn:outgoing", nsmap)
                    is_start = tag == "startEvent"
                    is_end = tag == "endEvent"
                    if not is_start and not incoming:
                        self.result.add_error("EPIC_BPMN_INVALID",
                                              f"process '{pid}' {tag} '{node_id}' missing <incoming>")
                    if not is_end and not outgoing:
                        self.result.add_error("EPIC_BPMN_INVALID",
                                              f"process '{pid}' {tag} '{node_id}' missing <outgoing>")
            # Sequence flow sourceRef/targetRef check
            for flow in process.findall("bpmn:sequenceFlow", nsmap):
                fid = flow.get("id", "?")
                if fid and fid != "?":
                    all_inner_flow_ids.add(fid)
                src = flow.get("sourceRef")
                tgt = flow.get("targetRef")
                if src and src not in process_node_ids:
                    self.result.add_error("EPIC_BPMN_INVALID",
                                          f"process '{pid}' sequenceFlow '{fid}' sourceRef='{src}' not found")
                if tgt and tgt not in process_node_ids:
                    self.result.add_error("EPIC_BPMN_INVALID",
                                          f"process '{pid}' sequenceFlow '{fid}' targetRef='{tgt}' not found")

        # Inner node BPMNShape / sequenceFlow BPMNEdge existence
        if bpmndi_ns:
            di_nsmap_inner = {"bpmndi": bpmndi_ns}
            inner_shape_refs = {s.get("bpmnElement")
                                for s in root.findall(".//bpmndi:BPMNShape", di_nsmap_inner)
                                if s.get("bpmnElement")}
            inner_edge_refs = {e.get("bpmnElement")
                               for e in root.findall(".//bpmndi:BPMNEdge", di_nsmap_inner)
                               if e.get("bpmnElement")}
            for nid in all_inner_node_ids:
                if nid not in inner_shape_refs:
                    self.result.add_error("EPIC_BPMN_INVALID",
                                          f"flow node '{nid}' has no BPMNShape in diagram")
            for fid in all_inner_flow_ids:
                if fid not in inner_edge_refs:
                    self.result.add_error("EPIC_BPMN_INVALID",
                                          f"sequenceFlow '{fid}' has no BPMNEdge in diagram")

        # --- YAML↔BPMN 連動チェック ---
        epic_data = self._load_epic_yaml()
        if epic_data:
            # epic_flow_descriptions is nested under epic: key
            epic_inner = epic_data.get("epic", epic_data)
            efd = epic_inner.get("epic_flow_descriptions")
            if efd:
                # Overview sync: check that YAML overview exists and BPMN collaboration has documentation
                overview = efd.get("overview", {})
                if not overview.get("purpose"):
                    self.result.add_warning("EPIC_BPMN_OVERVIEW_MISSING",
                                            "epic_flow_descriptions.overview.purpose is empty")
                collab_doc = collab.find("bpmn:documentation", nsmap)
                collab_doc_text = (collab_doc.text or "").strip() if collab_doc is not None else ""
                if overview.get("purpose") and collab_doc_text:
                    # Light check: BPMN collaboration documentation should not be placeholder
                    if "{{" in collab_doc_text:
                        self.result.add_warning("EPIC_BPMN_OVERVIEW_MISSING",
                                                "collaboration documentation contains unresolved placeholders")
                elif overview.get("purpose") and not collab_doc_text:
                    self.result.add_warning("EPIC_BPMN_OVERVIEW_MISSING",
                                            "YAML overview.purpose exists but collaboration has no documentation in BPMN")

                bpmn_participant_ids = {p.get("id") for p in participants}
                bpmn_mf_ids = {mf.get("id") for mf in collab.findall("bpmn:messageFlow", nsmap)}
                yaml_participant_ids = set()
                yaml_mf_ids = set()
                # Forward: YAML → BPMN
                for p_desc in efd.get("participants") or []:
                    pid = p_desc.get("participant_id", "")
                    if pid:
                        yaml_participant_ids.add(pid)
                        if pid not in bpmn_participant_ids:
                            self.result.add_warning("EPIC_BPMN_ID_MISMATCH",
                                                    f"epic_flow_descriptions.participants '{pid}' not found in epic_flow.bpmn")
                for mf_desc in efd.get("message_flows") or []:
                    mfid = mf_desc.get("message_flow_id", "")
                    if mfid:
                        yaml_mf_ids.add(mfid)
                        if mfid not in bpmn_mf_ids:
                            self.result.add_warning("EPIC_BPMN_ID_MISMATCH",
                                                    f"epic_flow_descriptions.message_flows '{mfid}' not found in epic_flow.bpmn")
                # Reverse: BPMN → YAML
                for pid in bpmn_participant_ids:
                    if pid and pid not in yaml_participant_ids:
                        self.result.add_warning("EPIC_BPMN_ID_NOT_DESCRIBED",
                                                f"participant '{pid}' in epic_flow.bpmn has no entry in epic_flow_descriptions")
                for mfid in bpmn_mf_ids:
                    if mfid and mfid not in yaml_mf_ids:
                        self.result.add_warning("EPIC_BPMN_ID_NOT_DESCRIBED",
                                                f"messageFlow '{mfid}' in epic_flow.bpmn has no entry in epic_flow_descriptions")

    def _load_epic_yaml(self):
        """Load epic_design.md Canonical YAML for cross-validation."""
        import re as _re
        design_path = self.epic_dir / "epic_design.md"
        if not design_path.exists():
            return None
        try:
            content = design_path.read_text(encoding="utf-8")
            match = _re.search(r"```yaml\s*\n(.*?)```", content, _re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)) or {}
        except Exception:
            pass
        return None

    def validate(self) -> ValidationResult:
        """Run full validation."""
        # Validate epic_design.md
        epic_data = self.validate_epic_design()

        # Validate feature_breakdown.md
        self.validate_feature_breakdown()

        # Validate epic_flow.bpmn (lightweight, overview BPMN)
        self.validate_epic_bpmn()

        # Validate EPIC_APPROVAL.md
        self.result.gate_status = self.validate_epic_approval()

        # Check feature specs exist
        if epic_data:
            self.check_feature_specs_exist(epic_data)

        # Evaluate gate conditions
        gate_checks = self.evaluate_gates(epic_data)
        self.result.gate_status.update(gate_checks)

        return self.result


def run_tests():
    """Run basic self-tests."""
    print("Running epic_validator.py self-tests...\n")

    # Test 1: ID validation
    print("Test 1: ID pattern validation")
    test_cases = [
        ("epic_id", "EPIC-TEST", True),
        ("epic_id", "EPIC-T", False),  # Too short
        ("epic_id", "epic-test", False),  # Lowercase
        ("team_id", "TEAM-A", True),
        ("team_id", "TEAM-ABC", True),
        ("team_id", "TEAM-ABCD", False),  # Too long
        ("feature_id", "FEAT-001", True),
        ("feature_id", "FEAT-AB", False),  # Too short
        ("milestone_id", "EM-01", True),
        ("milestone_id", "EM-1", False),  # Missing digit
    ]

    all_passed = True
    for id_type, value, expected in test_cases:
        pattern = ID_PATTERNS[id_type]
        result = bool(re.match(pattern, value))
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"  {status} {id_type}: '{value}' -> {result} (expected {expected})")

    if not all_passed:
        print("\n❌ Some tests failed!")
        return False

    # Test 2: Final approval detection logic
    print("\nTest 2: Final approval detection")

    # Test case: E1/E2 basic approval (should pass with simple approval)
    basic_section_approved = """## Gate E1: Epic Design Approval
### Checklist:
- [x] Something checked
### Approval:
Approver: John Doe
Role: Tech Lead
Date: 2025-01-20
"""
    basic_section_not_approved = """## Gate E1: Epic Design Approval
### Checklist:
- [ ] Something not checked
### Approval:
Approver: _____________________
"""

    # Test case: E3/E4 with final approval (should require Final Approval block)
    final_section_approved = """## Gate E3: Shared Contract Approval
### Checklist:
- [x] Something checked
### Team Confirmation:
Confirmed by: Team A Lead
### Final Approval:
Approver: Architecture Board Member
Role: ARCH_BOARD
Date: 2025-01-20
"""
    final_section_only_team = """## Gate E3: Shared Contract Approval
### Checklist:
- [x] Something checked
### Team Confirmation:
Confirmed by: Team A Lead
### Final Approval:
Approver: _____________________
"""

    # Helper functions (copied from the class for testing)
    def has_basic_approval(section: str) -> bool:
        has_checked = bool(re.search(r'\[x\]', section, re.IGNORECASE))
        has_approver = bool(re.search(
            r'(?:承認者|Approver):\s*([^\s_][^\n]*)',
            section, re.IGNORECASE
        ))
        return has_checked and has_approver

    def has_final_approval(section: str) -> bool:
        has_checked = bool(re.search(r'\[x\]', section, re.IGNORECASE))
        if not has_checked:
            return False
        final_block_pattern = r'(?:###?\s*(?:Final Approval|最終承認|Epic最終承認|Epic Final Approval).*?)(?=###|$)'
        final_match = re.search(final_block_pattern, section, re.DOTALL | re.IGNORECASE)
        if not final_match:
            return False
        final_block = final_match.group(0)
        has_final_approver = bool(re.search(
            r'(?:承認者|Approver):\s*([^\s_][^\n]*)',
            final_block, re.IGNORECASE
        ))
        return has_final_approver

    # Test basic approval
    if has_basic_approval(basic_section_approved):
        print("  ✅ E1 approved section detected correctly")
    else:
        print("  ❌ E1 approved section should be detected")
        return False

    if not has_basic_approval(basic_section_not_approved):
        print("  ✅ E1 not-approved section detected correctly")
    else:
        print("  ❌ E1 not-approved section should not be detected")
        return False

    # Test final approval detection
    if has_final_approval(final_section_approved):
        print("  ✅ E3 with final approval detected correctly")
    else:
        print("  ❌ E3 with final approval should be detected")
        return False

    if not has_final_approval(final_section_only_team):
        print("  ✅ E3 with only team confirmation correctly rejected")
    else:
        print("  ❌ E3 with only team confirmation should NOT pass")
        return False

    # Test 3: Integration test with fixed test fixtures
    print("\nTest 3: Integration test - fixture file parsing")

    # Use fixed test fixtures (not EPIC-SAMPLE which may change)
    script_dir = Path(__file__).parent
    fixture_dir = script_dir / "test_fixtures"
    fixture_unapproved = fixture_dir / "EPIC_APPROVAL_fixture.md"
    fixture_approved = fixture_dir / "EPIC_APPROVAL_approved_fixture.md"

    # Check both fixtures exist
    for fixture_path in [fixture_unapproved, fixture_approved]:
        if not fixture_path.exists():
            print(f"  ❌ FAIL: Test fixture not found at {fixture_path}")
            print(f"     CI cannot verify integration behavior without fixtures.")
            return False

    import tempfile
    import shutil

    # Test 3a: All unapproved fixture
    print("  Test 3a: All-unapproved fixture")
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            shutil.copy(fixture_unapproved, tmp_path / "EPIC_APPROVAL.md")

            validator = EpicValidator(tmp_path)
            gate_status = validator.validate_epic_approval()

            # Verify all expected gate keys are present
            expected_keys = {"E1_Epic_Design", "E2_Feature_Breakdown", "E3_Shared_Contract",
                           "E4_Integration_Plan", "E5_Feature_Specs_Ready", "Final"}
            if set(gate_status.keys()) != expected_keys:
                print(f"    ❌ Unexpected gate keys: {set(gate_status.keys())}")
                return False
            print(f"    ✅ All 6 gate keys correctly extracted")

            # All gates should be unapproved
            if all(not v for v in gate_status.values()):
                print(f"    ✅ All 6 gates correctly detected as unapproved")
            else:
                approved_gates = [k for k, v in gate_status.items() if v]
                print(f"    ❌ Expected all unapproved, but found approved: {approved_gates}")
                return False

    except Exception as e:
        print(f"    ❌ Failed to parse unapproved fixture: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3b: Partially approved fixture (E1 approved)
    print("  Test 3b: Partially-approved fixture (E1 only)")
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            shutil.copy(fixture_approved, tmp_path / "EPIC_APPROVAL.md")

            validator = EpicValidator(tmp_path)
            gate_status = validator.validate_epic_approval()

            # E1 should be approved, others should not
            if gate_status.get("E1_Epic_Design") is True:
                print(f"    ✅ E1_Epic_Design correctly detected as approved")
            else:
                print(f"    ❌ E1_Epic_Design should be approved but got: {gate_status.get('E1_Epic_Design')}")
                return False

            # Check that other gates are unapproved
            other_gates = ["E2_Feature_Breakdown", "E3_Shared_Contract",
                          "E4_Integration_Plan", "E5_Feature_Specs_Ready", "Final"]
            unapproved_correct = all(not gate_status.get(g) for g in other_gates)
            if unapproved_correct:
                print(f"    ✅ Other 5 gates correctly detected as unapproved")
            else:
                wrongly_approved = [g for g in other_gates if gate_status.get(g)]
                print(f"    ❌ These gates should be unapproved: {wrongly_approved}")
                return False

    except Exception as e:
        print(f"    ❌ Failed to parse approved fixture: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3c: Japanese labels fixture
    print("  Test 3c: Japanese labels fixture (承認者/確認者)")
    fixture_japanese = fixture_dir / "EPIC_APPROVAL_japanese_fixture.md"

    if not fixture_japanese.exists():
        print(f"    ❌ FAIL: Japanese fixture not found at {fixture_japanese}")
        return False

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            shutil.copy(fixture_japanese, tmp_path / "EPIC_APPROVAL.md")

            validator = EpicValidator(tmp_path)
            gate_status = validator.validate_epic_approval()

            # E1 should be approved (Japanese: 承認者: テストアーキテクト)
            if gate_status.get("E1_Epic_Design") is True:
                print(f"    ✅ E1_Epic_Design correctly detected with Japanese label (承認者)")
            else:
                print(f"    ❌ E1_Epic_Design should be approved (Japanese path) but got: {gate_status.get('E1_Epic_Design')}")
                return False

            # Other gates should be unapproved
            other_gates = ["E2_Feature_Breakdown", "E3_Shared_Contract",
                          "E4_Integration_Plan", "E5_Feature_Specs_Ready", "Final"]
            if all(not gate_status.get(g) for g in other_gates):
                print(f"    ✅ Other 5 gates correctly detected as unapproved")
            else:
                wrongly_approved = [g for g in other_gates if gate_status.get(g)]
                print(f"    ❌ These gates should be unapproved: {wrongly_approved}")
                return False

    except Exception as e:
        print(f"    ❌ Failed to parse Japanese fixture: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 3d: Japanese final approval block (最終承認)
    print("  Test 3d: Japanese final approval block (最終承認)")
    fixture_japanese_final = fixture_dir / "EPIC_APPROVAL_japanese_final_fixture.md"

    if not fixture_japanese_final.exists():
        print(f"    ❌ FAIL: Japanese final fixture not found at {fixture_japanese_final}")
        return False

    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            shutil.copy(fixture_japanese_final, tmp_path / "EPIC_APPROVAL.md")

            validator = EpicValidator(tmp_path)
            gate_status = validator.validate_epic_approval()

            # E3 should be approved (Japanese: 最終承認 block with 承認者: アーキテクト佐藤)
            if gate_status.get("E3_Shared_Contract") is True:
                print(f"    ✅ E3_Shared_Contract correctly detected with Japanese 最終承認 block")
            else:
                print(f"    ❌ E3_Shared_Contract should be approved (最終承認 path) but got: {gate_status.get('E3_Shared_Contract')}")
                return False

            # Other gates should be unapproved
            other_gates = ["E1_Epic_Design", "E2_Feature_Breakdown",
                          "E4_Integration_Plan", "E5_Feature_Specs_Ready", "Final"]
            if all(not gate_status.get(g) for g in other_gates):
                print(f"    ✅ Other 5 gates correctly detected as unapproved")
            else:
                wrongly_approved = [g for g in other_gates if gate_status.get(g)]
                print(f"    ❌ These gates should be unapproved: {wrongly_approved}")
                return False

    except Exception as e:
        print(f"    ❌ Failed to parse Japanese final fixture: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n✅ All tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Epic Validator - Enterprise SDD Extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate an epic
    python3 epic_validator.py validate epics/EPIC-ORDER/

    # Check gate status
    python3 epic_validator.py gates epics/EPIC-ORDER/

    # List features in epic
    python3 epic_validator.py features epics/EPIC-ORDER/

    # Run self-tests
    python3 epic_validator.py --test
        """
    )

    parser.add_argument("--test", action="store_true", help="Run self-tests")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    subparsers = parser.add_subparsers(dest="command")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate an epic")
    validate_parser.add_argument("epic_dir", type=Path, help="Epic directory path")

    # Gates command
    gates_parser = subparsers.add_parser("gates", help="Check gate status")
    gates_parser.add_argument("epic_dir", type=Path, help="Epic directory path")

    # Features command
    features_parser = subparsers.add_parser("features", help="List features in epic")
    features_parser.add_argument("epic_dir", type=Path, help="Epic directory path")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    validator = EpicValidator(args.epic_dir)
    result = validator.validate()

    if args.command == "validate":
        if args.json:
            output = {
                "epic_id": result.epic_id,
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "counts": result.counts,
                "gate_status": result.gate_status,
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Epic Validation Results: {result.epic_id}")
            print(f"{'=' * 50}")
            print(f"Valid: {'✅ Yes' if result.is_valid else '❌ No'}")
            print()

            print("Counts:")
            for key, value in result.counts.items():
                print(f"  {key}: {value}")
            print()

            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  ❌ {error}")
                print()

            if result.warnings:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  ⚠️ {warning}")
                print()

            print("Gate Checks:")
            for gate, status in result.gate_status.items():
                icon = "✅" if status else "⬜"
                print(f"  {icon} {gate}")

        sys.exit(0 if result.is_valid else 1)

    elif args.command == "gates":
        print(f"Gate Status for: {result.epic_id}")
        print(f"{'=' * 50}")
        for gate, status in result.gate_status.items():
            icon = "✅" if status else "⬜"
            print(f"  {icon} {gate}")

    elif args.command == "features":
        epic_design = validator.epic_dir / "epic_design.md"
        data = validator.extract_yaml_from_md(epic_design)

        if data and "epic" in data:
            features = data["epic"].get("features", [])
            print(f"Features in {result.epic_id}:")
            print(f"{'=' * 50}")
            for f in features:
                fid = f.get("feature_id", "UNKNOWN")
                name = f.get("name", "")
                team = f.get("team_id", "")
                tier = f.get("coverage_tier", "standard")
                print(f"  {fid}: {name}")
                print(f"    Team: {team}, Tier: {tier}")


if __name__ == "__main__":
    main()
