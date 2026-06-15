#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bpmn_lint.py — Standalone BPMN 2.0 validator for Camunda 8 (8.8 / 8.9 spec).

Validates .bpmn files against:
  - OMG BPMN 2.0 syntax + connection rules
  - Camunda 8 (Zeebe 8.x) execution requirements
  - Tecnos-STRIDE applied conventions
    (vertical swimlane, FEAT/EPIC distinction, BPMN-*/Process_A IDs,
     bpmn:documentation as second SSoT)

Auto-detects FEAT (single-process or 1-participant) vs EPIC (collaboration
with 2+ participants). Override with --feat / --epic.

Dependencies: Python 3.7+, stdlib only (xml.etree, argparse, re, pathlib).
No external pip packages required.

Usage:
  bpmn_lint.py path/to/file.bpmn              # auto-detect kind
  bpmn_lint.py --feat path/to/process.bpmn    # force FEAT (executable)
  bpmn_lint.py --epic path/to/epic_flow.bpmn  # force EPIC (overview)
  bpmn_lint.py --no-placeholder-check ...     # skip {{...}}/XXX checks
  bpmn_lint.py --json path/to/file.bpmn       # machine-readable JSON output
  bpmn_lint.py --version                       # print version

Exit codes:
  0 — PASS  (no errors; may have warnings)
  1 — FAIL  (≥1 error)
  2 — usage error (file not found, parse error)

Origin: Tecnos-STRIDE v5.4.0
  - sdd-templates/tools/stride_lint.py (validate_bpmn for FEAT)
  - sdd-templates/tools/epic_validator.py (validate_epic_bpmn for EPIC)

License: BPMN 2.0 spec (OMG, public). Camunda 8 (fair-use spec ref).
         Tecnos override portion: Tecnos Japan Inc., free re-use as derived work.
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = "1.1.0"

# Standard BPMN namespaces
BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
BPMNDI_NS = "http://www.omg.org/spec/BPMN/20100524/DI"
ZEEBE_NS = "http://camunda.org/schema/zeebe/1.0"
MODELER_NS = "http://camunda.org/schema/modeler/1.0"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# All BPMN flow node tags (subset supported by Camunda 8)
FLOW_NODE_TAGS = [
    "startEvent", "endEvent", "task", "serviceTask", "userTask",
    "sendTask", "receiveTask", "scriptTask", "manualTask",
    "businessRuleTask", "callActivity",
    "exclusiveGateway", "parallelGateway", "inclusiveGateway", "eventBasedGateway",
    "intermediateCatchEvent", "intermediateThrowEvent",
    "subProcess", "adHocSubProcess",
]


# =============================================================================
# Result accumulator
# =============================================================================

class LintResult:
    """Collects errors and warnings during validation."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, code, msg, fix_hint=None, refs=None):
        entry = {"code": code, "message": msg}
        if fix_hint:
            entry["fix_hint"] = fix_hint
        if refs:
            entry["refs"] = list(refs)
        self.errors.append(entry)

    def add_warning(self, code, msg, fix_hint=None, refs=None):
        entry = {"code": code, "message": msg}
        if fix_hint:
            entry["fix_hint"] = fix_hint
        if refs:
            entry["refs"] = list(refs)
        self.warnings.append(entry)

    def has_errors(self):
        return bool(self.errors)


# =============================================================================
# Tecnos-STRIDE FEAT ID format conventions (v1.1.0、2026-05-08)
# =============================================================================
# Per memory/constitution.md §id_conventions, FEAT BPMN element ids must be:
#   ^BPMN-(TASK|GW|EVT|FLOW)-[0-9]{3}$    (3-digit zero-padded, hyphenated)
# 2026-05-08 incident: agent generated `BPMN_TASK_01_register_source` style ids
# (underscores, no zero-padding, name embedded). Detect & reject with fix_hint.

FEAT_ID_PATTERNS = {
    # element.tag (without namespace) → expected regex
    "userTask":          re.compile(r"^BPMN-TASK-\d{3}$"),
    "serviceTask":       re.compile(r"^BPMN-TASK-\d{3}$"),
    "task":              re.compile(r"^BPMN-TASK-\d{3}$"),
    "sendTask":          re.compile(r"^BPMN-TASK-\d{3}$"),
    "receiveTask":       re.compile(r"^BPMN-TASK-\d{3}$"),
    "scriptTask":        re.compile(r"^BPMN-TASK-\d{3}$"),
    "manualTask":        re.compile(r"^BPMN-TASK-\d{3}$"),
    "businessRuleTask":  re.compile(r"^BPMN-TASK-\d{3}$"),
    "callActivity":      re.compile(r"^BPMN-TASK-\d{3}$"),
    "exclusiveGateway":  re.compile(r"^BPMN-GW-\d{3}$"),
    "parallelGateway":   re.compile(r"^BPMN-GW-\d{3}$"),
    "inclusiveGateway":  re.compile(r"^BPMN-GW-\d{3}$"),
    "eventBasedGateway": re.compile(r"^BPMN-GW-\d{3}$"),
    "startEvent":        re.compile(r"^BPMN-EVT-\d{3}$"),
    "endEvent":          re.compile(r"^BPMN-EVT-\d{3}$"),
    "intermediateCatchEvent": re.compile(r"^BPMN-EVT-\d{3}$"),
    "intermediateThrowEvent": re.compile(r"^BPMN-EVT-\d{3}$"),
    "sequenceFlow":      re.compile(r"^BPMN-FLOW-\d{3}$"),
}

# Legacy ID pattern (heuristic — matches the 2026-05-08 incident style):
#   underscore-separated AND 1-2 digit number AND embedded name suffix
LEGACY_FEAT_ID_RE = re.compile(r"^BPMN_(TASK|GW|EVT|FLOW)_\d{1,3}(_[a-zA-Z0-9_]+)?$")


def check_feat_id_format(path, root, bpmn_ns, result, legacy_id_warn_only=False):
    """Validate FEAT element id naming against ^BPMN-{TAG}-NNN$ regex.

    Args:
        path: file path (for error message context)
        root: parsed XML root (Element)
        bpmn_ns: BPMN namespace URI
        result: LintResult accumulator
        legacy_id_warn_only: if True, emit warning instead of error for legacy
                             `BPMN_TASK_01_xxx` style ids (transition flag).

    Severity scheme (v1.1.0、2026-05-08):
      1. id matches BPMN_TAG_NN_xxx style (the 2026-05-08 incident pattern)
         → ERROR `BPMN_ID_FORMAT_VIOLATION` (or warn-only with --legacy-id)
      2. id starts with `BPMN-` but doesn't match `BPMN-(TASK|GW|EVT|FLOW)-\\d{3}$`
         → ERROR `BPMN_ID_FORMAT_VIOLATION` (broken attempt at canonical scheme)
      3. id has none of the above markers (e.g. Camunda Modeler default `Activity_xxx`)
         → WARNING `BPMN_ID_NON_TECNOS_SCHEME` (backward compat, recommend rename)

    This preserves backward compatibility with existing canonical examples that
    use Camunda Modeler default ids while still catching the real failure mode.
    """
    if not bpmn_ns:
        return
    refs_canonical = (
        "bpmn/rules/bpmn_quick_reference.md L41 (FEAT ID convention)",
        "bpmn/templates/process_bpmn_template.bpmn (canonical example)",
        "memory/constitution.md §id_conventions bpmn_element_id",
    )
    for elem in root.iter():
        if not elem.tag.startswith("{"):
            continue
        tag_uri, tag_local = elem.tag[1:].split("}", 1)
        if tag_uri != bpmn_ns:
            continue
        if tag_local not in FEAT_ID_PATTERNS:
            continue
        eid = elem.attrib.get("id", "")
        if not eid:
            continue
        pattern = FEAT_ID_PATTERNS[tag_local]
        if pattern.match(eid):
            continue
        # Classify the violation
        is_legacy_underscore = bool(LEGACY_FEAT_ID_RE.match(eid))
        is_bpmn_prefixed = eid.startswith("BPMN-") or eid.startswith("BPMN_")
        fix_hint = (
            f"FEAT element <bpmn:{tag_local}> id must match '{pattern.pattern}' "
            f"(3-digit zero-padded, hyphenated). "
            f"Current id '{eid}' should be renamed (e.g., BPMN-TASK-001). "
            f"Note: name attribute carries the human-readable label, not the id."
        )
        if is_bpmn_prefixed:
            # Hard error: agent attempted Tecnos scheme but got it wrong
            if is_legacy_underscore and legacy_id_warn_only:
                result.add_warning(
                    "BPMN_ID_FORMAT_LEGACY",
                    f"{path}: legacy id format '{eid}' on <bpmn:{tag_local}> "
                    f"(transition allowed under --legacy-id; will be hard error in next major).",
                    fix_hint=fix_hint,
                    refs=refs_canonical,
                )
            else:
                result.add_error(
                    "BPMN_ID_FORMAT_VIOLATION",
                    f"{path}: <bpmn:{tag_local} id='{eid}'> does not match "
                    f"FEAT id pattern '{pattern.pattern}'.",
                    fix_hint=fix_hint,
                    refs=refs_canonical,
                )
        else:
            # Soft warning: non-Tecnos scheme entirely (e.g. Camunda Modeler default)
            result.add_warning(
                "BPMN_ID_NON_TECNOS_SCHEME",
                f"{path}: <bpmn:{tag_local} id='{eid}'> uses non-Tecnos id scheme "
                f"(expected '{pattern.pattern}'). Backward-compat OK; recommend rename for new files.",
                fix_hint=fix_hint,
                refs=refs_canonical,
            )


# =============================================================================
# --diff-against-template (v1.1.0)
# =============================================================================
# Compare a target FEAT BPMN to the canonical template to detect "ゼロから書いた"
# violations (incident #1, 2026-05-08). Output unified diff for the operator.

def diff_against_template(target_path, template_path):
    """Return a unified diff (list[str]) of target vs template.

    If template has placeholders (BPMN-PROC-XXX, {{...}}), we can not require
    byte equality — instead we report structural differences (number of tasks /
    gateways / events / flows + isHorizontal value) so an operator can see at
    a glance whether the target was actually copied from the template.
    """
    import difflib
    if not Path(template_path).exists():
        return [f"# template not found: {template_path}"]
    if not Path(target_path).exists():
        return [f"# target not found: {target_path}"]
    target_lines = Path(target_path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    template_lines = Path(template_path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    diff = difflib.unified_diff(
        template_lines, target_lines,
        fromfile=str(template_path), tofile=str(target_path),
        n=3,
    )
    return list(diff)


# =============================================================================
# Namespace extraction (adapted from stride_lint.py extract_namespaces)
# =============================================================================

def extract_namespaces(root):
    """Extract xmlns prefix→URI mapping from root element + element traversal."""
    ns = {}
    for key, value in root.attrib.items():
        if key.startswith("{http://www.w3.org/2000/xmlns/}"):
            prefix = key.split("}", 1)[1]
            ns[prefix] = value

    def add(prefix, uri):
        if prefix and uri and prefix not in ns:
            ns[prefix] = uri

    if root.tag.startswith("{"):
        root_ns = root.tag.split("}", 1)[0][1:]
        add("bpmn", root_ns)

    for elem in root.iter():
        if elem.tag.startswith("{"):
            uri = elem.tag.split("}", 1)[0][1:]
            if uri == BPMN_NS:
                add("bpmn", uri)
            elif uri == BPMNDI_NS:
                add("bpmndi", uri)
            elif uri == ZEEBE_NS:
                add("zeebe", uri)
        for attr in elem.attrib:
            if attr.startswith("{"):
                attr_uri = attr.split("}", 1)[0][1:]
                if attr_uri == MODELER_NS:
                    add("modeler", attr_uri)
    return ns


# =============================================================================
# Auto-detect FEAT vs EPIC
# =============================================================================

def auto_detect_kind(root, ns):
    """Detect FEAT (executable, single process) vs EPIC (collaboration with 2+ participants)."""
    bpmn_ns = ns.get("bpmn")
    if not bpmn_ns:
        return "feat"
    nsmap = {"bpmn": bpmn_ns}
    for collab in root.findall("bpmn:collaboration", nsmap):
        participants = collab.findall("bpmn:participant", nsmap)
        if len(participants) >= 2:
            return "epic"
    return "feat"


# =============================================================================
# FEAT validator (port of stride_lint.validate_bpmn)
# =============================================================================

def validate_feat(path, root, ns, result, legacy_id_warn_only=False):
    """Validate FEAT process.bpmn against Camunda 8 + Tecnos rules (14 MUST-DO).

    v1.1.0 additions:
      - check_feat_id_format() — BPMN-TASK-NNN regex enforcement (2026-05-08 fix)
    """
    zeebe_ns = ns.get("zeebe")
    modeler_ns = ns.get("modeler")
    bpmn_ns = ns.get("bpmn")
    bpmndi_ns = ns.get("bpmndi")

    # v1.1.0: ID format check (incident #3 of 2026-05-08, BPMN_ID_FORMAT_VIOLATION)
    check_feat_id_format(path, root, bpmn_ns, result, legacy_id_warn_only=legacy_id_warn_only)

    # 1. Namespace presence
    if zeebe_ns != ZEEBE_NS:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing zeebe namespace")
    if modeler_ns != MODELER_NS:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing modeler namespace")

    # 2. Execution platform
    modeler_exec = root.attrib.get(f"{{{modeler_ns}}}executionPlatform") if modeler_ns else None
    modeler_version = root.attrib.get(f"{{{modeler_ns}}}executionPlatformVersion") if modeler_ns else None
    if modeler_exec != "Camunda Cloud":
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: executionPlatform not Camunda Cloud")
    if not (modeler_version and modeler_version.startswith("8.")):
        result.add_error("BPMN_VALIDATION_FAILED",
                         f"{path}: executionPlatformVersion not 8.x (found: {modeler_version})")
    elif not (modeler_version.startswith("8.8") or modeler_version.startswith("8.9")):
        result.add_warning("BPMN_VERSION_NOTICE",
                           f"{path}: recommended 8.8.* or 8.9.*, found {modeler_version}")

    if not bpmn_ns:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing bpmn namespace")
        return

    nsmap = {"bpmn": bpmn_ns, "bpmndi": bpmndi_ns or "", "zeebe": zeebe_ns or ""}

    # 3. Process executable
    processes = root.findall("bpmn:process", nsmap)
    if not processes:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: no bpmn:process")
        return
    for process in processes:
        if process.get("isExecutable") != "true":
            result.add_error("BPMN_VALIDATION_FAILED", f"{path}: process not executable")

    # 11. BPMNDiagram / BPMNPlane
    diagrams = root.findall("bpmndi:BPMNDiagram", nsmap)
    planes = root.findall(".//bpmndi:BPMNPlane", nsmap)
    if not diagrams or not planes:
        result.add_error("BPMN_VALIDATION_FAILED", f"{path}: missing BPMNDiagram/BPMNPlane")
    else:
        process_ids = {p.get("id") for p in processes if p.get("id")}
        collab_ids = {c.get("id") for c in root.findall("bpmn:collaboration", nsmap) if c.get("id")}
        valid_refs = process_ids | collab_ids
        if not any(plane.get("bpmnElement") in valid_refs for plane in planes):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: plane does not reference process or collaboration")

    # 5. Service Task zeebe:taskDefinition
    for task in root.findall(".//bpmn:serviceTask", nsmap):
        task_defs = task.findall(".//zeebe:taskDefinition", nsmap)
        if not task_defs:
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: serviceTask missing zeebe:taskDefinition")
        else:
            for td in task_defs:
                if not td.get("type"):
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: serviceTask missing taskDefinition type")

    # 6. XOR Gateway: default OR conditionExpression on all outgoing
    seq_flows = {f.get("id"): f for f in root.findall(".//bpmn:sequenceFlow", nsmap) if f.get("id")}
    for gw in root.findall(".//bpmn:exclusiveGateway", nsmap):
        outgoing = [o.text for o in gw.findall("bpmn:outgoing", nsmap) if o.text]
        if len(outgoing) <= 1:
            continue
        default_flow = gw.get("default")
        if default_flow:
            if default_flow not in seq_flows:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: default flow not found {default_flow}")
        else:
            missing = []
            for fid in outgoing:
                f = seq_flows.get(fid)
                if f is None:
                    missing.append(fid)
                    continue
                cond = f.find("bpmn:conditionExpression", nsmap)
                if cond is None or not (cond.text and cond.text.strip()):
                    missing.append(fid)
            if missing:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: XOR missing condition {', '.join(missing)}")

    # Message correlation
    uses_message = bool(root.findall(".//bpmn:receiveTask", nsmap)) or \
                   bool(root.findall(".//bpmn:messageEventDefinition", nsmap))
    if uses_message:
        if not root.findall("bpmn:message", nsmap):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: message used but bpmn:message missing")
        subs = root.findall(".//zeebe:subscription", nsmap)
        if not any(s.get("correlationKey") for s in subs):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: zeebe:subscription correlationKey missing")

    # 10. Timer ISO-8601
    for d in root.findall(".//bpmn:timeDuration", nsmap):
        text = (d.text or "").strip()
        if text and not (text.startswith("P") or text.startswith("PT")):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: timeDuration not ISO-8601 {text}")

    # 4. FlowNode incoming/outgoing
    for process in processes:
        for tag in FLOW_NODE_TAGS:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                node_id = node.get("id", "?")
                incoming = node.findall("bpmn:incoming", nsmap)
                outgoing = node.findall("bpmn:outgoing", nsmap)
                is_start = tag == "startEvent"
                is_end = tag == "endEvent"
                is_compensation = node.get("isForCompensation") == "true"
                is_event_subprocess = (tag == "subProcess" and
                                        node.get("triggeredByEvent") == "true")
                if is_compensation or is_event_subprocess:
                    continue
                if not is_start and not incoming:
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: {tag} '{node_id}' missing <incoming>")
                if not is_end and not outgoing:
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: {tag} '{node_id}' missing <outgoing>")
                if is_start and incoming:
                    result.add_warning("BPMN_VALIDATION_FAILED",
                                       f"{path}: startEvent '{node_id}' should not have <incoming>")

    # 9. boundaryEvent attachedToRef
    for be in root.findall(".//bpmn:boundaryEvent", nsmap):
        be_id = be.get("id", "?")
        if not be.get("attachedToRef"):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: boundaryEvent '{be_id}' missing attachedToRef")
        is_comp = be.find("bpmn:compensationEventDefinition", nsmap) is not None
        if not is_comp and not be.findall("bpmn:outgoing", nsmap):
            result.add_error("BPMN_VALIDATION_FAILED",
                             f"{path}: boundaryEvent '{be_id}' missing <outgoing>")

    # 8. sequenceFlow source/targetRef existence
    for process in processes:
        process_node_ids = set()
        for tag in FLOW_NODE_TAGS + ["boundaryEvent"]:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                nid = node.get("id")
                if nid:
                    process_node_ids.add(nid)
        for flow in process.findall("bpmn:sequenceFlow", nsmap):
            fid = flow.get("id", "?")
            src = flow.get("sourceRef")
            tgt = flow.get("targetRef")
            if src and src not in process_node_ids:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: sequenceFlow '{fid}' sourceRef='{src}' not found in process")
            if tgt and tgt not in process_node_ids:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: sequenceFlow '{fid}' targetRef='{tgt}' not found in process")

    # 7. conditionExpression xsi:type & non-empty
    for flow in root.findall(".//bpmn:sequenceFlow", nsmap):
        cond = flow.find("bpmn:conditionExpression", nsmap)
        if cond is not None:
            fid = flow.get("id", "?")
            cond_text = (cond.text or "").strip()
            if not cond_text:
                result.add_error("BPMN_VALIDATION_FAILED",
                                 f"{path}: conditionExpression empty on flow '{fid}'")
            xsi_type = cond.get(f"{{{XSI_NS}}}type")
            if not xsi_type:
                result.add_warning("BPMN_VALIDATION_FAILED",
                                   f"{path}: conditionExpression missing xsi:type on flow '{fid}'")
            elif xsi_type != "bpmn:tFormalExpression":
                result.add_warning("BPMN_VALIDATION_FAILED",
                                   f"{path}: conditionExpression xsi:type should be 'bpmn:tFormalExpression', "
                                   f"found '{xsi_type}' on flow '{fid}'")

    # 12. BPMNShape / BPMNEdge completeness
    if bpmndi_ns:
        di_nsmap = {"bpmndi": bpmndi_ns}
        shape_refs = {s.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", di_nsmap)
                      if s.get("bpmnElement")}
        edge_refs = {e.get("bpmnElement") for e in root.findall(".//bpmndi:BPMNEdge", di_nsmap)
                     if e.get("bpmnElement")}
        for process in processes:
            for tag in FLOW_NODE_TAGS + ["boundaryEvent"]:
                for node in process.findall(f"bpmn:{tag}", nsmap):
                    nid = node.get("id")
                    if nid and nid not in shape_refs:
                        result.add_error("BPMN_VALIDATION_FAILED",
                                         f"{path}: {tag} '{nid}' has no BPMNShape in diagram")
            for flow in process.findall("bpmn:sequenceFlow", nsmap):
                fid = flow.get("id")
                if fid and fid not in edge_refs:
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: sequenceFlow '{fid}' has no BPMNEdge in diagram")

    # 13. Vertical swimlane (Tecnos override)
    if bpmndi_ns:
        di_nsmap = {"bpmndi": bpmndi_ns}
        participant_ids = set()
        for collab in root.findall("bpmn:collaboration", nsmap):
            for p in collab.findall("bpmn:participant", nsmap):
                pid = p.get("id")
                if pid:
                    participant_ids.add(pid)
        for shape in root.findall(".//bpmndi:BPMNShape", di_nsmap):
            ref = shape.get("bpmnElement", "")
            if ref in participant_ids:
                if shape.get("isHorizontal") != "false":
                    result.add_error("BPMN_VALIDATION_FAILED",
                                     f"{path}: participant shape '{ref}' must have "
                                     f'isHorizontal="false" (vertical swimlane required)')

    # 14. documentation warnings (Tecnos override)
    for process in processes:
        doc = process.find("bpmn:documentation", nsmap)
        if doc is None or not (doc.text and doc.text.strip()):
            result.add_warning("BPMN_DOCUMENTATION_MISSING",
                               f"{path}: process '{process.get('id', '?')}' has no <documentation>")
        for tag in ["userTask", "serviceTask", "businessRuleTask", "callActivity"]:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                nid = node.get("id", "?")
                d = node.find("bpmn:documentation", nsmap)
                if d is None or not (d.text and d.text.strip()):
                    result.add_warning("BPMN_DOCUMENTATION_MISSING",
                                       f"{path}: {tag} '{nid}' has no <documentation>")
        for gw in process.findall("bpmn:exclusiveGateway", nsmap):
            gid = gw.get("id", "?")
            outgoing = [o.text for o in gw.findall("bpmn:outgoing", nsmap) if o.text]
            if len(outgoing) > 1:
                d = gw.find("bpmn:documentation", nsmap)
                if d is None or not (d.text and d.text.strip()):
                    result.add_warning("BPMN_DOCUMENTATION_MISSING",
                                       f"{path}: exclusiveGateway '{gid}' has no <documentation>")
        for flow in process.findall("bpmn:sequenceFlow", nsmap):
            cond = flow.find("bpmn:conditionExpression", nsmap)
            if cond is not None:
                fid = flow.get("id", "?")
                d = flow.find("bpmn:documentation", nsmap)
                if d is None or not (d.text and d.text.strip()):
                    result.add_warning("BPMN_DOCUMENTATION_MISSING",
                                       f"{path}: conditional sequenceFlow '{fid}' has no <documentation>")


# =============================================================================
# EPIC validator (port of epic_validator.validate_epic_bpmn)
# =============================================================================

def validate_epic(path, root, ns, result):
    """Validate EPIC epic_flow.bpmn against overview rules (9 MUST-DO)."""
    bpmn_ns = ns.get("bpmn")
    bpmndi_ns = ns.get("bpmndi")

    if not bpmn_ns:
        result.add_error("EPIC_BPMN_INVALID", f"{path}: missing bpmn namespace")
        return

    nsmap = {"bpmn": bpmn_ns}
    if bpmndi_ns:
        nsmap["bpmndi"] = bpmndi_ns

    # 1. Collaboration required
    collabs = root.findall("bpmn:collaboration", nsmap)
    if not collabs:
        result.add_error("EPIC_BPMN_INVALID",
                         f"{path}: must have a bpmn:collaboration element")
        return
    collab = collabs[0]
    collab_id = collab.get("id", "")

    # 2. >= 2 participants
    participants = collab.findall("bpmn:participant", nsmap)
    if len(participants) < 2:
        result.add_error("EPIC_BPMN_INVALID",
                         f"{path}: collaboration needs at least 2 participants "
                         f"(found {len(participants)})")

    # 3. processRef existence
    process_ids = {p.get("id") for p in root.findall("bpmn:process", nsmap) if p.get("id")}
    for p in participants:
        pref = p.get("processRef")
        pid = p.get("id", "?")
        if not pref:
            result.add_error("EPIC_BPMN_INVALID",
                             f"{path}: participant '{pid}' missing processRef")
        elif pref not in process_ids:
            result.add_error("EPIC_BPMN_INVALID",
                             f"{path}: participant '{pid}' processRef='{pref}' "
                             f"not found in process definitions")

    # 7-9. BPMNDiagram / BPMNPlane / Vertical swimlane / messageFlow Edge
    if bpmndi_ns:
        di_nsmap = {"bpmndi": bpmndi_ns}
        diagrams = root.findall("bpmndi:BPMNDiagram", di_nsmap)
        planes = root.findall(".//bpmndi:BPMNPlane", di_nsmap)
        if not diagrams or not planes:
            result.add_error("EPIC_BPMN_INVALID", f"{path}: missing BPMNDiagram/BPMNPlane")
        else:
            plane_ref = planes[0].get("bpmnElement", "")
            if plane_ref != collab_id:
                result.add_warning("EPIC_BPMN_INVALID",
                                   f"{path}: BPMNPlane bpmnElement='{plane_ref}' "
                                   f"should reference collaboration '{collab_id}'")

            all_shapes = root.findall(".//bpmndi:BPMNShape", di_nsmap)
            shape_refs = {s.get("bpmnElement") for s in all_shapes}
            for p in participants:
                pid = p.get("id", "?")
                if pid not in shape_refs:
                    result.add_warning("EPIC_BPMN_INVALID",
                                       f"{path}: participant '{pid}' has no BPMNShape")
                else:
                    for s in all_shapes:
                        if s.get("bpmnElement") == pid:
                            if s.get("isHorizontal") != "false":
                                result.add_error("EPIC_BPMN_INVALID",
                                                 f"{path}: participant '{pid}' must have "
                                                 f'isHorizontal="false" (vertical swimlane required)')

            edge_refs = {e.get("bpmnElement")
                         for e in root.findall(".//bpmndi:BPMNEdge", di_nsmap)}
            for mf in collab.findall("bpmn:messageFlow", nsmap):
                mfid = mf.get("id", "?")
                if mfid not in edge_refs:
                    result.add_warning("EPIC_BPMN_INVALID",
                                       f"{path}: messageFlow '{mfid}' has no BPMNEdge")
    else:
        result.add_warning("EPIC_BPMN_INVALID", f"{path}: missing bpmndi namespace (no diagram)")

    # documentation warnings (collab / participant / messageFlow)
    cdoc = collab.find("bpmn:documentation", nsmap)
    if cdoc is None or not (cdoc.text and cdoc.text.strip()):
        result.add_warning("EPIC_BPMN_DOCUMENTATION_MISSING",
                           f"{path}: collaboration has no <documentation>")
    for p in participants:
        pid = p.get("id", "?")
        pd = p.find("bpmn:documentation", nsmap)
        if pd is None or not (pd.text and pd.text.strip()):
            result.add_warning("EPIC_BPMN_DOCUMENTATION_MISSING",
                               f"{path}: participant '{pid}' has no <documentation>")
    for mf in collab.findall("bpmn:messageFlow", nsmap):
        mfid = mf.get("id", "?")
        md = mf.find("bpmn:documentation", nsmap)
        if md is None or not (md.text and md.text.strip()):
            result.add_warning("EPIC_BPMN_DOCUMENTATION_MISSING",
                               f"{path}: messageFlow '{mfid}' has no <documentation>")

    # 4-5. Inner process flow node integrity
    all_inner_node_ids = set()
    all_inner_flow_ids = set()
    processes = root.findall("bpmn:process", nsmap)
    for process in processes:
        pid = process.get("id", "?")
        process_node_ids = set()
        for tag in FLOW_NODE_TAGS:
            for node in process.findall(f"bpmn:{tag}", nsmap):
                nid = node.get("id")
                if nid:
                    process_node_ids.add(nid)
                    all_inner_node_ids.add(nid)
                node_id = nid or "?"
                incoming = node.findall("bpmn:incoming", nsmap)
                outgoing = node.findall("bpmn:outgoing", nsmap)
                is_start = tag == "startEvent"
                is_end = tag == "endEvent"
                if not is_start and not incoming:
                    result.add_error("EPIC_BPMN_INVALID",
                                     f"{path}: process '{pid}' {tag} '{node_id}' missing <incoming>")
                if not is_end and not outgoing:
                    result.add_error("EPIC_BPMN_INVALID",
                                     f"{path}: process '{pid}' {tag} '{node_id}' missing <outgoing>")
        for flow in process.findall("bpmn:sequenceFlow", nsmap):
            fid = flow.get("id", "?")
            if fid and fid != "?":
                all_inner_flow_ids.add(fid)
            src = flow.get("sourceRef")
            tgt = flow.get("targetRef")
            if src and src not in process_node_ids:
                result.add_error("EPIC_BPMN_INVALID",
                                 f"{path}: process '{pid}' sequenceFlow '{fid}' "
                                 f"sourceRef='{src}' not found")
            if tgt and tgt not in process_node_ids:
                result.add_error("EPIC_BPMN_INVALID",
                                 f"{path}: process '{pid}' sequenceFlow '{fid}' "
                                 f"targetRef='{tgt}' not found")

    # Inner BPMNShape / BPMNEdge existence
    if bpmndi_ns:
        di_nsmap = {"bpmndi": bpmndi_ns}
        inner_shape_refs = {s.get("bpmnElement")
                            for s in root.findall(".//bpmndi:BPMNShape", di_nsmap)
                            if s.get("bpmnElement")}
        inner_edge_refs = {e.get("bpmnElement")
                           for e in root.findall(".//bpmndi:BPMNEdge", di_nsmap)
                           if e.get("bpmnElement")}
        for nid in all_inner_node_ids:
            if nid not in inner_shape_refs:
                result.add_error("EPIC_BPMN_INVALID",
                                 f"{path}: flow node '{nid}' has no BPMNShape in diagram")
        for fid in all_inner_flow_ids:
            if fid not in inner_edge_refs:
                result.add_error("EPIC_BPMN_INVALID",
                                 f"{path}: sequenceFlow '{fid}' has no BPMNEdge in diagram")


# =============================================================================
# Placeholder check (both modes)
# =============================================================================

PLACEHOLDER_PATTERNS = [
    r"\{\{[^}]+\}\}",            # {{プロセス名}}, {{form-id}}, {{job-type}} ...
    r"BPMN-PROC-XXX",            # FEAT placeholder
    r"\bEPIC-XXX\b",             # EPIC placeholder
    r"\bXXX_feature_name\b",     # targetNamespace placeholder
]


def check_placeholders(path, kind, result):
    code = "EPIC_BPMN_PLACEHOLDER" if kind == "epic" else "BPMN_PLACEHOLDER_PRESENT"
    try:
        text = Path(path).read_text(encoding="utf-8")
    except Exception:
        return
    found = set()
    for pat in PLACEHOLDER_PATTERNS:
        for m in re.finditer(pat, text):
            found.add(m.group(0))
    if found:
        result.add_warning(code,
                           f"{path}: unresolved placeholders: {', '.join(sorted(found))}")


# =============================================================================
# Output formatters
# =============================================================================

def output_text(path, kind, result):
    """Human-readable output to stdout."""
    print(f"BPMN Lint Report ({kind.upper()})")
    print("=" * 60)
    if not result.errors and not result.warnings:
        print(f"PASS: 0 errors, 0 warnings")
        return
    for e in result.errors:
        print(f"  ✗ {e['code']}: {e['message']}")
    for w in result.warnings:
        print(f"  ⚠ {w['code']}: {w['message']}")
    print()
    err_count = len(result.errors)
    warn_count = len(result.warnings)
    if err_count == 0:
        print(f"PASS: 0 errors, {warn_count} warning{'s' if warn_count != 1 else ''}")
    else:
        print(f"FAIL: {err_count} error{'s' if err_count != 1 else ''}, "
              f"{warn_count} warning{'s' if warn_count != 1 else ''}")


def output_json(path, kind, result):
    """Machine-readable JSON output."""
    out = {
        "version": VERSION,
        "file": str(path),
        "kind": kind,
        "passed": not result.has_errors(),
        "error_count": len(result.errors),
        "warning_count": len(result.warnings),
        "errors": result.errors,
        "warnings": result.warnings,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


# =============================================================================
# Main entry point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        prog="bpmn_lint",
        description="Standalone BPMN 2.0 validator for Camunda 8 + Tecnos-STRIDE rules",
        epilog=f"Version: {VERSION}",
    )
    parser.add_argument("path", help="Path to .bpmn file")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--feat", action="store_true",
                            help="Validate as FEAT (executable process.bpmn)")
    mode_group.add_argument("--epic", action="store_true",
                            help="Validate as EPIC (overview epic_flow.bpmn)")
    parser.add_argument("--no-placeholder-check", action="store_true",
                        help="Skip {{...}} / BPMN-PROC-XXX / EPIC-XXX placeholder warnings")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON to stdout (machine-readable)")
    parser.add_argument("--legacy-id", action="store_true",
                        help="(v1.1.0) Treat legacy 'BPMN_TASK_01_xxx' style ids as warning "
                             "instead of hard error (transition flag, will be removed)")
    parser.add_argument("--diff-against-template", metavar="TEMPLATE_PATH",
                        help="(v1.1.0) Output unified diff of target file vs canonical template "
                             "(detects ゼロから書いた violation, incident #1 of 2026-05-08)")
    parser.add_argument("--version", action="version",
                        version=f"bpmn_lint.py {VERSION}")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        if args.json:
            print(json.dumps({
                "version": VERSION, "file": str(path), "passed": False,
                "errors": [{"code": "FILE_NOT_FOUND", "message": f"file not found: {path}"}],
                "warnings": [],
            }, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2

    result = LintResult()

    # Parse XML
    try:
        tree = ET.parse(path)
    except Exception as exc:
        result.add_error("BPMN_PARSE_ERROR", f"{path}: {exc}")
        kind = "feat" if not args.epic else "epic"
        if args.json:
            output_json(path, kind, result)
        else:
            output_text(path, kind, result)
        return 1

    root = tree.getroot()
    if not root.tag.endswith("definitions"):
        result.add_error("BPMN_VALIDATION_FAILED",
                         f"{path}: root is not bpmn:definitions")
        kind = "feat" if not args.epic else "epic"
        if args.json:
            output_json(path, kind, result)
        else:
            output_text(path, kind, result)
        return 1

    ns = extract_namespaces(root)

    # Determine kind
    if args.feat:
        kind = "feat"
    elif args.epic:
        kind = "epic"
    else:
        kind = auto_detect_kind(root, ns)

    # v1.1.0: --diff-against-template short-circuits to diff output
    if args.diff_against_template:
        diff_lines = diff_against_template(path, Path(args.diff_against_template))
        sys.stdout.writelines(diff_lines)
        # Heuristic: if there is no diff, target file == template (placeholders unsubstituted).
        # Non-empty diff is the normal case; we exit 0 either way (diff is informational).
        return 0

    # Run validator
    if kind == "feat":
        validate_feat(path, root, ns, result, legacy_id_warn_only=args.legacy_id)
    else:
        validate_epic(path, root, ns, result)

    # Placeholder check (warnings only)
    if not args.no_placeholder_check:
        check_placeholders(path, kind, result)

    # Output
    if args.json:
        output_json(path, kind, result)
    else:
        output_text(path, kind, result)

    return 1 if result.has_errors() else 0


if __name__ == "__main__":
    sys.exit(main())
