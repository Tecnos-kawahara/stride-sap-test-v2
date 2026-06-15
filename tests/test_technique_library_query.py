"""Test: technique_library_query — Phase B WI-008 (TS-INT-06).

Covers AC-US-FEATVALA01-001-01 / AC-US-FEATVALB01-001-01 (one of the 5 tools).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "sdd-templates" / "tools"))

from technique_library_query import (
    lookup_technique,
    list_techniques,
    technique_count,
    VALID_PHASES,
)


def test_count_is_50():
    assert technique_count(repo_root=REPO_ROOT) == 50


def test_lookup_known_technique():
    t = lookup_technique("brainstorming", repo_root=REPO_ROOT)
    assert t["id"] == "brainstorming"
    assert t["babok_section"] == "10.5"
    assert "phase_0_discovery" in t.get("typical_phase", [])


def test_lookup_unknown_raises():
    with pytest.raises(KeyError):
        lookup_technique("nonexistent_technique_id", repo_root=REPO_ROOT)


def test_list_all():
    items = list_techniques(repo_root=REPO_ROOT)
    assert len(items) == 50
    ids = {t["id"] for t in items}
    assert "brainstorming" in ids
    assert "workshops" in ids


def test_list_filter_by_phase():
    discovery_items = list_techniques(typical_phase="phase_0_discovery", repo_root=REPO_ROOT)
    assert len(discovery_items) > 0
    for t in discovery_items:
        assert "phase_0_discovery" in t.get("typical_phase", [])


def test_list_invalid_phase_raises():
    with pytest.raises(ValueError):
        list_techniques(typical_phase="invalid_phase", repo_root=REPO_ROOT)


def test_valid_phases_constant():
    assert VALID_PHASES == {
        "phase_0_discovery",
        "phase_0_3_elicit",
        "phase_0_5_context_modelling",
        "stride_core",
    }
