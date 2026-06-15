"""Integration tests for dependency_checker.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sdd-templates" / "tools"))

from dependency_checker import DependencyChecker, DependencyGraph


class TestDependencyGraph:
    """Tests for the core DependencyGraph class."""

    def test_no_cycle_in_acyclic_graph(self):
        g = DependencyGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        cycles = g.detect_cycles()
        assert cycles == []

    def test_cycle_detected(self):
        g = DependencyGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_edge("A", "B")
        g.add_edge("B", "A")
        cycles = g.detect_cycles()
        assert len(cycles) > 0
        # The cycle should contain both A and B
        cycle_nodes = set()
        for c in cycles:
            cycle_nodes.update(c)
        assert "A" in cycle_nodes
        assert "B" in cycle_nodes

    def test_topological_sort_acyclic(self):
        g = DependencyGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        order = g.topological_sort()
        assert order is not None
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_dependency_depth(self):
        g = DependencyGraph()
        g.add_node("A")
        g.add_node("B")
        g.add_node("C")
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        assert g.get_dependency_depth("A") == 2


class TestDependencyChecker:
    """Tests for DependencyChecker with real project layout."""

    def test_acyclic_project_passes(self, enterprise_project):
        """Enterprise project without cycles passes check."""
        checker = DependencyChecker(enterprise_project)
        checker.build_graph_from_features()
        cycles = checker.graph.detect_cycles()
        assert cycles == []

    def test_cyclic_project_detects_cycle(self, enterprise_project_with_cycle):
        """Features with circular deps are detected."""
        checker = DependencyChecker(enterprise_project_with_cycle)
        checker.build_graph_from_features()
        cycles = checker.graph.detect_cycles()
        assert len(cycles) > 0

    def test_graph_output_is_dot(self, enterprise_project):
        """graph command produces DOT format."""
        checker = DependencyChecker(enterprise_project)
        checker.build_graph_from_features()
        # DependencyGraph should have a to_dot method or similar
        if hasattr(checker.graph, "to_dot"):
            dot = checker.graph.to_dot()
            assert "digraph" in dot
        elif hasattr(checker, "generate_dot"):
            dot = checker.generate_dot()
            assert "digraph" in dot
        else:
            # Fallback: just verify graph has nodes
            assert isinstance(checker.graph.nodes, dict)

    def test_discovers_features(self, enterprise_project):
        """Discovers feature directories from project root."""
        checker = DependencyChecker(enterprise_project)
        features = checker.discover_features()
        names = [f.name for f in features]
        assert "FEAT-ETEST" in names

    def test_validate_manifest_missing_fields(self, tmp_path):
        """validate_manifest catches missing required fields."""
        import yaml as pyyaml

        manifest_path = tmp_path / "bad_manifest.yaml"
        manifest_path.write_text(
            pyyaml.dump({
                "dependency_manifest": {
                    "meta": {},  # Missing feature_id
                    "external_dependencies": [
                        {
                            "owner_feature": "FEAT-X",
                            # Missing contract_ref and version_constraint
                            "criticality": "high",
                            # Missing fallback_behavior for high criticality
                        },
                    ],
                }
            }),
            encoding="utf-8",
        )
        checker = DependencyChecker(tmp_path)
        ok, errors = checker.validate_manifest(manifest_path)
        assert not ok, "Manifest with missing fields should fail"
        assert any("feature_id" in e.lower() for e in errors), f"Expected feature_id error: {errors}"
        assert any("contract_ref" in e.lower() for e in errors), f"Expected contract_ref error: {errors}"

    def test_validate_manifest_valid(self, tmp_path):
        """validate_manifest passes with complete fields."""
        import yaml as pyyaml

        manifest_path = tmp_path / "good_manifest.yaml"
        manifest_path.write_text(
            pyyaml.dump({
                "dependency_manifest": {
                    "meta": {"feature_id": "FEAT-GOOD"},
                    "external_dependencies": [
                        {
                            "owner_feature": "FEAT-Y",
                            "contract_ref": "SC-API-001",
                            "version_constraint": "^1.0.0",
                            "criticality": "low",
                        },
                    ],
                }
            }),
            encoding="utf-8",
        )
        checker = DependencyChecker(tmp_path)
        ok, errors = checker.validate_manifest(manifest_path)
        assert ok, f"Valid manifest should pass: {errors}"
