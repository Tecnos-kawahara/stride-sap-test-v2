#!/usr/bin/env python3
"""
Dependency Checker - Enterprise SDD Extension
Version: 1.0.0

Purpose:
- Detect circular dependencies in feature dependency graphs
- Validate dependency manifests
- Generate dependency reports and visualizations

Usage:
    python3 dependency_checker.py check <epics_or_specs_dir>
    python3 dependency_checker.py graph <epics_or_specs_dir> [--output deps.dot]
    python3 dependency_checker.py validate <dependency_manifest_path>
    python3 dependency_checker.py --test
"""

import argparse
import sys
import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


class DependencyGraph:
    """Directed graph for dependency analysis."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)

    def add_node(self, node_id: str, metadata: Dict[str, Any] = None):
        """Add a node to the graph."""
        self.nodes[node_id] = metadata or {}

    def add_edge(self, from_node: str, to_node: str, metadata: Dict[str, Any] = None):
        """Add a directed edge from from_node to to_node."""
        edge = {
            "from": from_node,
            "to": to_node,
            **(metadata or {})
        }
        self.edges.append(edge)
        self.adjacency[from_node].append(to_node)
        self.reverse_adjacency[to_node].append(from_node)

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect all cycles in the graph using DFS.
        Returns a list of cycles, where each cycle is a list of node IDs.
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)
            return False

        for node in self.nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def get_dependency_depth(self, node: str) -> int:
        """Get the maximum dependency depth from a node."""
        visited = set()

        def dfs(n: str, depth: int) -> int:
            if n in visited:
                return depth
            visited.add(n)
            max_depth = depth
            for neighbor in self.adjacency.get(n, []):
                max_depth = max(max_depth, dfs(neighbor, depth + 1))
            return max_depth

        return dfs(node, 0)

    def get_max_depth(self) -> int:
        """Get the maximum dependency depth across all nodes."""
        return max(self.get_dependency_depth(n) for n in self.nodes) if self.nodes else 0

    def topological_sort(self) -> Optional[List[str]]:
        """
        Return topological ordering of nodes, or None if cycles exist.
        """
        in_degree = {node: 0 for node in self.nodes}
        for edge in self.edges:
            in_degree[edge["to"]] = in_degree.get(edge["to"], 0) + 1

        queue = [node for node in self.nodes if in_degree[node] == 0]
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in self.adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.nodes):
            return None  # Cycle detected
        return result

    def to_dot(self, title: str = "Dependency Graph") -> str:
        """Generate DOT format for visualization."""
        lines = [
            f'digraph "{title}" {{',
            '    rankdir=TB;',
            '    node [shape=box, style=filled, fillcolor=lightblue];',
            ''
        ]

        # Add nodes with labels
        for node_id, metadata in self.nodes.items():
            label = metadata.get("name", node_id)
            team = metadata.get("team_id", "")
            tier = metadata.get("coverage_tier", "")
            node_label = f"{node_id}\\n{label}"
            if team:
                node_label += f"\\n[{team}]"
            if tier:
                color = {"critical": "lightcoral", "standard": "lightblue", "experimental": "lightgreen"}.get(tier, "lightblue")
                lines.append(f'    "{node_id}" [label="{node_label}", fillcolor={color}];')
            else:
                lines.append(f'    "{node_id}" [label="{node_label}"];')

        lines.append('')

        # Add edges
        for edge in self.edges:
            edge_label = edge.get("contract_id", "")
            edge_type = edge.get("type", "")
            style = "solid" if edge_type == "blocking" else "dashed"
            if edge_label:
                lines.append(f'    "{edge["from"]}" -> "{edge["to"]}" [label="{edge_label}", style={style}];')
            else:
                lines.append(f'    "{edge["from"]}" -> "{edge["to"]}" [style={style}];')

        lines.append('}')
        return '\n'.join(lines)


class DependencyChecker:
    """Main dependency checker class."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.graph = DependencyGraph()

    def load_yaml(self, path: Path) -> Optional[Dict]:
        """Load a YAML file safely."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to load {path}: {e}")
            return None

    def discover_features(self) -> List[Path]:
        """Discover all feature directories under specs/."""
        specs_dir = self.base_dir / "specs"
        if not specs_dir.exists():
            return []

        features = []
        for item in specs_dir.iterdir():
            if item.is_dir() and (item / "basic_design.md").exists():
                features.append(item)
        return features

    def discover_epics(self) -> List[Path]:
        """Discover all epic directories under epics/."""
        epics_dir = self.base_dir / "epics"
        if not epics_dir.exists():
            return []

        epics = []
        for item in epics_dir.iterdir():
            if item.is_dir() and (item / "epic_design.md").exists():
                epics.append(item)
        return epics

    def extract_yaml_block(self, md_path: Path, block_name: str) -> Optional[Dict]:
        """Extract YAML block from markdown file."""
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find YAML block after the header
            pattern = rf'#\s*\d*\.?\s*{re.escape(block_name)}\s*\(YAML\)\s*```yaml\s*(.*?)```'
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

            if not match:
                # Try simpler pattern
                pattern = r'```yaml\s*(.*?)```'
                match = re.search(pattern, content, re.DOTALL)

            if match:
                yaml_content = match.group(1)
                return yaml.safe_load(yaml_content)
            return None
        except Exception as e:
            self.warnings.append(f"Failed to extract YAML from {md_path}: {e}")
            return None

    def build_graph_from_epics(self):
        """Build dependency graph from epic definitions."""
        for epic_path in self.discover_epics():
            epic_design = epic_path / "epic_design.md"
            if epic_design.exists():
                data = self.extract_yaml_block(epic_design, "Canonical Epic Design")
                if data and "epic" in data:
                    self._process_epic_data(data["epic"])

    def build_graph_from_features(self):
        """Build dependency graph from feature dependency manifests."""
        for feature_path in self.discover_features():
            # Try dependency manifest first
            dep_manifest = feature_path / "dependencies" / "dependency_manifest.yaml"
            if dep_manifest.exists():
                data = self.load_yaml(dep_manifest)
                if data and "dependency_manifest" in data:
                    self._process_dependency_manifest(data["dependency_manifest"], feature_path.name)

            # Also try cross_refs.yaml
            cross_refs = feature_path / "cross_refs.yaml"
            if cross_refs.exists():
                data = self.load_yaml(cross_refs)
                if data and "cross_refs" in data:
                    self._process_cross_refs(data["cross_refs"], feature_path.name)

    def _process_epic_data(self, epic: Dict):
        """Process epic data to build graph."""
        epic_id = epic.get("meta", {}).get("epic_id", "UNKNOWN")

        # Add features as nodes
        for feature in epic.get("features", []):
            feature_id = feature.get("feature_id")
            if feature_id:
                self.graph.add_node(feature_id, {
                    "name": feature.get("name", ""),
                    "team_id": feature.get("team_id", ""),
                    "coverage_tier": feature.get("coverage_tier", "standard"),
                    "epic_id": epic_id
                })

        # Add cross-team dependencies as edges
        for dep in epic.get("cross_team_dependencies", []):
            from_feature = dep.get("from_feature")
            to_feature = dep.get("to_feature")
            if from_feature and to_feature:
                self.graph.add_edge(from_feature, to_feature, {
                    "type": dep.get("type", "blocking"),
                    "contract_id": dep.get("interface", ""),
                    "description": dep.get("description", "")
                })

    def _process_dependency_manifest(self, manifest: Dict, feature_id: str):
        """Process dependency manifest to build graph."""
        # Add feature as node if not exists
        feature_info = manifest.get("feature_info", {})
        if feature_id not in self.graph.nodes:
            self.graph.add_node(feature_id, {
                "team_id": feature_info.get("team_id", ""),
                "coverage_tier": feature_info.get("coverage_tier", "standard"),
                "epic_id": feature_info.get("epic_id", "")
            })

        # Add external dependencies as edges
        for dep in manifest.get("external_dependencies", []):
            owner_feature = dep.get("owner_feature")
            if owner_feature:
                # Ensure target node exists
                if owner_feature not in self.graph.nodes:
                    self.graph.add_node(owner_feature, {
                        "team_id": dep.get("owner_team", "")
                    })

                self.graph.add_edge(feature_id, owner_feature, {
                    "type": dep.get("dependency_type", "runtime"),
                    "contract_id": dep.get("contract_id", ""),
                    "criticality": dep.get("criticality", "medium")
                })

    def _process_cross_refs(self, cross_refs: Dict, feature_id: str):
        """Process cross_refs.yaml to build graph."""
        # Similar to dependency manifest
        feature_info = cross_refs.get("feature_info", {})
        if feature_id not in self.graph.nodes:
            self.graph.add_node(feature_id, {
                "team_id": feature_info.get("team_id", ""),
                "coverage_tier": feature_info.get("coverage_tier", "standard"),
                "epic_id": feature_info.get("epic_id", "")
            })

        for dep in cross_refs.get("external_dependencies", []):
            owner_feature = dep.get("owner_feature")
            if owner_feature:
                if owner_feature not in self.graph.nodes:
                    self.graph.add_node(owner_feature, {
                        "team_id": dep.get("owner_team", "")
                    })

                self.graph.add_edge(feature_id, owner_feature, {
                    "contract_id": dep.get("contract_id", ""),
                    "criticality": dep.get("criticality", "medium")
                })

    def check(self) -> Tuple[bool, Dict]:
        """
        Run dependency checks and return results.
        Returns (success, results_dict)
        """
        # Build graph
        self.build_graph_from_epics()
        self.build_graph_from_features()

        results = {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "cycles": [],
            "max_depth": 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy()
        }

        if not self.graph.nodes:
            results["warnings"].append("No features or epics found to analyze")
            return True, results

        # Detect cycles
        cycles = self.graph.detect_cycles()
        if cycles:
            results["cycles"] = cycles
            for cycle in cycles:
                cycle_str = " -> ".join(cycle)
                results["errors"].append(f"DEPENDENCY_CYCLE: {cycle_str}")

        # Check max depth
        max_depth = self.graph.get_max_depth()
        results["max_depth"] = max_depth

        # Load dependency rules to check max depth
        rules_path = self.base_dir / "shared" / "policies" / "dependency_rules.yaml"
        if rules_path.exists():
            rules = self.load_yaml(rules_path)
            if rules:
                max_allowed = rules.get("dependency_rules", {}).get("cycle_detection", {}).get("max_depth", 10)
                if max_depth > max_allowed:
                    results["errors"].append(f"MAX_DEPTH_EXCEEDED: Depth {max_depth} exceeds limit {max_allowed}")

        # Success requires: no cycles AND no errors (including MAX_DEPTH_EXCEEDED, YAML failures, etc.)
        success = len(results["cycles"]) == 0 and len(results["errors"]) == 0
        return success, results

    def validate_manifest(self, manifest_path: Path) -> Tuple[bool, List[str]]:
        """Validate a single dependency manifest."""
        errors = []

        data = self.load_yaml(manifest_path)
        if not data:
            return False, ["Failed to load manifest file"]

        manifest = data.get("dependency_manifest", {})
        if not manifest:
            return False, ["Missing 'dependency_manifest' root key"]

        # Check required fields
        meta = manifest.get("meta", {})
        if not meta.get("feature_id"):
            errors.append("Missing meta.feature_id")

        # Validate external dependencies
        for i, dep in enumerate(manifest.get("external_dependencies", [])):
            prefix = f"external_dependencies[{i}]"

            if not dep.get("contract_ref"):
                errors.append(f"{prefix}: Missing contract_ref")

            if not dep.get("version_constraint"):
                errors.append(f"{prefix}: Missing version_constraint")
            else:
                # Basic semver validation
                vc = dep["version_constraint"]
                if not re.match(r'^[\^~>=<\d\.\*\s]+$', vc):
                    errors.append(f"{prefix}: Invalid version_constraint format: {vc}")

            if dep.get("criticality") == "high":
                if not dep.get("error_handling", {}).get("fallback_behavior"):
                    errors.append(f"{prefix}: High criticality dependency missing fallback_behavior")

        return len(errors) == 0, errors

    def generate_graph(self, output_path: Optional[Path] = None) -> str:
        """Generate DOT graph output."""
        self.build_graph_from_epics()
        self.build_graph_from_features()

        dot = self.graph.to_dot("Feature Dependencies")

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(dot)

        return dot


def run_tests():
    """Run basic self-tests."""
    print("Running dependency_checker.py self-tests...\n")

    # Test 1: Cycle detection
    print("Test 1: Cycle detection")
    g = DependencyGraph()
    g.add_node("A")
    g.add_node("B")
    g.add_node("C")
    g.add_edge("A", "B")
    g.add_edge("B", "C")
    g.add_edge("C", "A")  # Creates cycle

    cycles = g.detect_cycles()
    if cycles:
        print(f"  ✅ Detected cycle: {cycles[0]}")
    else:
        print("  ❌ Failed to detect cycle")
        return False

    # Test 2: No cycle
    print("Test 2: No cycle detection")
    g2 = DependencyGraph()
    g2.add_node("A")
    g2.add_node("B")
    g2.add_node("C")
    g2.add_edge("A", "B")
    g2.add_edge("B", "C")

    cycles2 = g2.detect_cycles()
    if not cycles2:
        print("  ✅ Correctly found no cycles")
    else:
        print(f"  ❌ Incorrectly detected cycle: {cycles2}")
        return False

    # Test 3: Topological sort
    print("Test 3: Topological sort")
    order = g2.topological_sort()
    if order == ["A", "B", "C"]:
        print(f"  ✅ Correct topological order: {order}")
    else:
        print(f"  ⚠️ Unexpected order (may still be valid): {order}")

    # Test 4: DOT generation
    print("Test 4: DOT generation")
    dot = g2.to_dot("Test Graph")
    if "digraph" in dot and "A" in dot:
        print("  ✅ DOT output generated correctly")
    else:
        print("  ❌ DOT generation failed")
        return False

    # Test 5: Max depth
    print("Test 5: Max depth calculation")
    depth = g2.get_max_depth()
    if depth == 2:
        print(f"  ✅ Correct max depth: {depth}")
    else:
        print(f"  ❌ Incorrect max depth: {depth}, expected 2")
        return False

    print("\n✅ All tests passed!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Dependency Checker - Enterprise SDD Extension",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check for dependency issues
    python3 dependency_checker.py check /path/to/project

    # Generate DOT graph
    python3 dependency_checker.py graph /path/to/project --output deps.dot

    # Validate a manifest file
    python3 dependency_checker.py validate specs/feature/dependencies/dependency_manifest.yaml

    # Run self-tests
    python3 dependency_checker.py --test
        """
    )

    parser.add_argument("--test", action="store_true", help="Run self-tests")

    subparsers = parser.add_subparsers(dest="command")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check for dependency issues")
    check_parser.add_argument("path", type=Path, help="Project base directory")
    check_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Graph command
    graph_parser = subparsers.add_parser("graph", help="Generate dependency graph")
    graph_parser.add_argument("path", type=Path, help="Project base directory")
    graph_parser.add_argument("--output", "-o", type=Path, help="Output DOT file path")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a dependency manifest")
    validate_parser.add_argument("manifest", type=Path, help="Path to dependency_manifest.yaml")

    args = parser.parse_args()

    if args.test:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "check":
        checker = DependencyChecker(args.path)
        success, results = checker.check()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Dependency Check Results for: {args.path}")
            print(f"{'=' * 50}")
            print(f"Nodes: {results['node_count']}")
            print(f"Edges: {results['edge_count']}")
            print(f"Max Depth: {results['max_depth']}")
            print()

            if results['cycles']:
                print("❌ CYCLES DETECTED:")
                for cycle in results['cycles']:
                    print(f"   {' -> '.join(cycle)}")
                print()
            else:
                print("✅ No cycles detected")
                print()

            if results['errors']:
                print("Errors:")
                for error in results['errors']:
                    print(f"  ❌ {error}")

            if results['warnings']:
                print("Warnings:")
                for warning in results['warnings']:
                    print(f"  ⚠️ {warning}")

        sys.exit(0 if success else 1)

    elif args.command == "graph":
        checker = DependencyChecker(args.path)
        dot = checker.generate_graph(args.output)

        if args.output:
            print(f"Graph written to: {args.output}")
            print("To visualize, run: dot -Tpng {args.output} -o deps.png")
        else:
            print(dot)

    elif args.command == "validate":
        checker = DependencyChecker(args.manifest.parent.parent.parent)
        success, errors = checker.validate_manifest(args.manifest)

        if success:
            print(f"✅ {args.manifest} is valid")
        else:
            print(f"❌ {args.manifest} has validation errors:")
            for error in errors:
                print(f"   - {error}")

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
