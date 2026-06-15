"""Mini project root generator for integration tests."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Self


# Path to the real repo root (resolved at import time)
_REPO_ROOT = Path(__file__).resolve().parent.parent


class ProjectBuilder:
    """Build an isolated STRIDE project root in a temporary directory.

    Usage:
        project = (
            ProjectBuilder(tmp_path)
            .add_feature("FEAT-TEST", mode="full", phase=2, coverage_tier="standard")
            .done()
            .build()
        )
        # project is a Path to the mini project root
    """

    def __init__(self, root: Path):
        self.root = root
        self._features: list[FeatureBuilder] = []
        self._epics: list[EpicBuilder] = []
        self._enterprise_enabled: bool = False

    def add_feature(self, feature_id: str, **kwargs) -> FeatureBuilder:
        """Add a feature and return its builder for further customization."""
        fb = FeatureBuilder(self, feature_id, **kwargs)
        self._features.append(fb)
        return fb

    def add_epic(self, epic_id: str, **kwargs) -> EpicBuilder:
        """Add an epic and return its builder for further customization."""
        eb = EpicBuilder(self, epic_id, **kwargs)
        self._epics.append(eb)
        return eb

    def enable_enterprise(self) -> Self:
        """Enable enterprise mode in config."""
        self._enterprise_enabled = True
        return self

    def build(self) -> Path:
        """Construct the project root and return its path."""
        self._setup_sdd_templates()
        self._setup_memory()
        self._setup_shared()
        self._setup_config()
        self._create_specs_dir()

        for eb in self._epics:
            eb._build()

        for fb in self._features:
            fb._build()

        return self.root

    def _setup_sdd_templates(self) -> None:
        """Symlink read-only dirs, copy mutable ones."""
        sdd = self.root / "sdd-templates"
        sdd.mkdir(parents=True, exist_ok=True)

        # Symlink: read-only resources
        for name in ("tools", "templates", "hooks", "bin", "specs"):
            src = _REPO_ROOT / "sdd-templates" / name
            if src.exists():
                dst = sdd / name
                dst.symlink_to(src)

        # Copy: mutable resources
        for name in ("config",):
            src = _REPO_ROOT / "sdd-templates" / name
            if src.exists():
                shutil.copytree(src, sdd / name)

        # VERSION file
        version_file = _REPO_ROOT / "sdd-templates" / "VERSION"
        if version_file.exists():
            shutil.copy2(version_file, sdd / "VERSION")

        # requirements files
        for req in _REPO_ROOT.glob("sdd-templates/requirements*.txt"):
            shutil.copy2(req, sdd / req.name)

    def _setup_memory(self) -> None:
        """Copy memory/ — lint_feature() requires constitution.md and artifact_registry.md."""
        src = _REPO_ROOT / "memory"
        if src.exists():
            shutil.copytree(src, self.root / "memory")

    def _setup_shared(self) -> None:
        """Copy shared/ — enterprise and dependency tools need this."""
        src = _REPO_ROOT / "shared"
        if src.exists():
            shutil.copytree(src, self.root / "shared")

    def _setup_config(self) -> None:
        """Adjust enterprise config if needed."""
        if self._enterprise_enabled:
            config_path = self.root / "sdd-templates" / "config" / "enterprise.yaml"
            if config_path.exists():
                text = config_path.read_text(encoding="utf-8")
                text = re.sub(r"enabled:\s*false", "enabled: true", text)
                config_path.write_text(text, encoding="utf-8")

    def _create_specs_dir(self) -> None:
        (self.root / "specs").mkdir(exist_ok=True)


class FeatureBuilder:
    """Build a feature directory inside a ProjectBuilder project."""

    # Gate sets for each phase level
    _FULL_GATES = {
        0: set(),
        1: set(),                          # Phase 1 in progress (no gates approved yet)
        2: {1, 2},                         # Design approved -> Specify in progress
        3: {1, 2, 3, 4},                   # Specify approved -> Tasking in progress
        4: {1, 2, 3, 4, 5},               # Tasking approved -> Execute in progress
        5: {1, 2, 3, 4, 5, "final"},      # All approved
    }
    _LITE_GATES = {
        0: set(),
        1: set(),
        2: {"A"},
        3: {"A", "B"},
        4: {"A", "B", "C"},  # All approved
    }

    def __init__(
        self,
        project: ProjectBuilder,
        feature_id: str,
        mode: str = "full",
        phase: int = 5,  # default: fully approved
        coverage_tier: str = "standard",
    ):
        self._project = project
        self.feature_id = feature_id
        self.mode = mode
        self.phase = phase
        self.coverage_tier = coverage_tier
        self._erp_addon = False
        self._epic_ref: str | None = None
        self._team_id: str | None = None
        self._lint_mutations: list[str] = []
        self._custom_gates: set | None = None
        self._dep_manifest: list[dict] | None = None
        self._amendment_artifacts: bool = False
        self._approval_dates: dict[str | int, str] | None = None

    def with_erp_addon(self) -> Self:
        self._erp_addon = True
        return self

    def with_enterprise(self, epic_id: str, team_id: str = "TEAM-TEST") -> Self:
        self._epic_ref = epic_id
        self._team_id = team_id
        return self

    def mutate_lint_error(self, error_type: str) -> Self:
        """Queue a mutation that will break the feature in a specific way.

        error_types:
            'missing_ac' -- remove acceptance criteria from spec
            'broken_traceability' -- break spec_refs in tasks
            'missing_nfr' -- remove NFR section from spec
            'missing_bpmn' -- delete process.bpmn
            'phase_violation' -- create Phase 2 files without Gate 1,2 approval
        """
        self._lint_mutations.append(error_type)
        return self

    def with_approval(self, gates: set) -> Self:
        """Override auto-calculated gates with explicit set."""
        self._custom_gates = gates
        return self

    def done(self) -> ProjectBuilder:
        """Return to the parent ProjectBuilder for chaining."""
        return self._project

    def _build(self) -> Path:
        """Generate the feature directory."""
        feature_dir = self._project.root / "specs" / self.feature_id
        sample_dir = _REPO_ROOT / "specs" / "FEAT-ERPSAMPLE"

        # Copy base files from FEAT-ERPSAMPLE (excluding state/)
        for item in sample_dir.iterdir():
            if item.name == "state":
                continue  # Skip timestamp-bearing evaluator outputs
            dst = feature_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst)

        # state/ dir (empty, for tools that write to it)
        (feature_dir / "state").mkdir(exist_ok=True)

        # Rewrite feature_id in all files
        self._rewrite_ids(feature_dir)

        # Set coverage_tier in basic_design
        self._set_coverage_tier(feature_dir)

        # Set enterprise fields
        if self._epic_ref:
            self._set_enterprise_fields(feature_dir)

        # Set APPROVAL.md based on mode and phase
        self._write_approval(feature_dir)

        # Apply lint error mutations
        for mutation in self._lint_mutations:
            self._apply_mutation(feature_dir, mutation)

        # Dependency manifest
        if self._dep_manifest is not None:
            self._build_dependency_manifest(feature_dir)

        # Amendment artifacts
        if self._amendment_artifacts:
            self._build_amendment_artifacts(feature_dir)

        # ERP Addon
        if not self._erp_addon:
            # Remove ERP addon dirs if they exist (copied from sample)
            for d in ("work_items", "runs", "ops"):
                p = feature_dir / d
                if p.exists():
                    shutil.rmtree(p)
            for f in ("erp_addon_mode_policy.yaml", "erp_addon_risk_taxonomy.yaml"):
                p = feature_dir / f
                if p.exists():
                    p.unlink()

        return feature_dir

    def _rewrite_ids(self, feature_dir: Path) -> None:
        """Replace FEAT-ERPSAMPLE / FEATERPOMS with the new feature_id.

        ID conventions expect sub-IDs like US-FEAT<SHORT>-001, so FEATERPOMS
        must be replaced with FEAT<short_id> to keep regex compliance.
        """
        new_id = self.feature_id
        short_id = new_id.replace("FEAT-", "").replace("-", "")
        # FEATERPOMS is the compact sub-ID prefix; must keep FEAT prefix
        compact_id = "FEAT" + short_id

        for p in feature_dir.rglob("*"):
            if p.is_file() and p.suffix in (".md", ".yaml", ".yml", ".bpmn"):
                try:
                    text = p.read_text(encoding="utf-8")
                    text = text.replace("FEAT-ERPSAMPLE", new_id)
                    text = text.replace("FEATERPOMS", compact_id)
                    text = text.replace("ERPSAMPLE", short_id)
                    p.write_text(text, encoding="utf-8")
                except UnicodeDecodeError:
                    pass

    def _set_coverage_tier(self, feature_dir: Path) -> None:
        bd = feature_dir / "basic_design.md"
        if bd.exists():
            text = bd.read_text(encoding="utf-8")
            text = re.sub(r'coverage_tier:\s*"\w+"', f'coverage_tier: "{self.coverage_tier}"', text)
            bd.write_text(text, encoding="utf-8")

    def _set_enterprise_fields(self, feature_dir: Path) -> None:
        bd = feature_dir / "basic_design.md"
        if bd.exists():
            text = bd.read_text(encoding="utf-8")
            text = re.sub(r'epic_ref:\s*"[^"]*"', f'epic_ref: "{self._epic_ref}"', text)
            text = re.sub(r'team_id:\s*"[^"]*"', f'team_id: "{self._team_id}"', text)
            bd.write_text(text, encoding="utf-8")

    def _write_approval(self, feature_dir: Path) -> None:
        """Generate APPROVAL.md with correct mode and gate approvals.

        Format must match what phase_gate.get_approved_gates() parses:
        - ## Gate N headers (Full) or ## Gate A/B/C (Lite)
        - [x] for approved checkboxes, [ ] for unapproved
        - approver field filled for approved gates
        """
        if self._custom_gates is not None:
            approved = self._custom_gates
        elif self.mode == "lite":
            approved = self._LITE_GATES.get(self.phase, set())
        else:
            approved = self._FULL_GATES.get(self.phase, set())

        lines: list[str] = []
        if self.mode == "lite":
            lines.append("# APPROVAL (Lite Mode)")
            lines.append("")
            for gate in ("A", "B", "C"):
                check = "x" if gate in approved else " "
                lines.append(f"## Gate {gate}")
                lines.append(f"- [{check}] Review complete")
                if gate in approved:
                    lines.append("承認者: Test Approver")
                else:
                    lines.append("承認者: ___________")
                lines.append("")
        else:
            lines.append("# APPROVAL")
            lines.append("")
            for gate in (1, 2, 3, 4, 5, "final"):
                title = "Final" if gate == "final" else f"Gate {gate}"
                check = "x" if gate in approved else " "
                lines.append(f"## {title}")
                lines.append(f"- [{check}] Review complete")
                if gate in approved:
                    lines.append("承認者: Test Approver")
                    if self._approval_dates and gate in self._approval_dates:
                        lines.append(f"日付: {self._approval_dates[gate]}")
                    else:
                        lines.append("日付: ___________")
                else:
                    lines.append("承認者: ___________")
                    lines.append("日付: ___________")
                lines.append("")

        (feature_dir / "APPROVAL.md").write_text("\n".join(lines), encoding="utf-8")

    def _apply_mutation(self, feature_dir: Path, mutation: str) -> None:
        """Apply a destructive mutation for error testing."""
        if mutation == "missing_ac":
            spec = feature_dir / "spec.md"
            if spec.exists():
                text = spec.read_text(encoding="utf-8")
                text = re.sub(r"acceptance:\n(\s+-.*\n)+", "acceptance: []\n", text)
                spec.write_text(text, encoding="utf-8")

        elif mutation == "broken_traceability":
            tasks = feature_dir / "tasks.md"
            if tasks.exists():
                text = tasks.read_text(encoding="utf-8")
                text = text.replace("spec_refs:", "spec_refs_BROKEN:")
                tasks.write_text(text, encoding="utf-8")

        elif mutation == "missing_nfr":
            spec = feature_dir / "spec.md"
            if spec.exists():
                text = spec.read_text(encoding="utf-8")
                text = re.sub(
                    r"requirements:\n(\s+\w+:.*\n(\s+-.*\n)*)+",
                    "requirements: {}\n",
                    text,
                )
                spec.write_text(text, encoding="utf-8")

        elif mutation == "missing_bpmn":
            bpmn = feature_dir / "process.bpmn"
            if bpmn.exists():
                bpmn.unlink()

        elif mutation == "phase_violation":
            # Create Phase 2 file when Phase 1 not approved
            if self._custom_gates is None:
                self._custom_gates = set()  # No gates approved
            self._write_approval(feature_dir)  # Rewrite with no gates
            # spec.md already exists (copied from sample) -- this IS the violation

    def with_approval_dates(self, gate_dates: dict[str | int, str]) -> Self:
        """Set approval dates for gates. Keys: 1-5 or 'final', values: 'YYYY-MM-DD'."""
        self._approval_dates = gate_dates
        return self

    def with_dependency_manifest(self, deps: list[dict]) -> Self:
        """Add a dependency manifest to the feature."""
        self._dep_manifest = deps
        return self

    def with_amendment_artifacts(self) -> Self:
        """Add run artifacts suitable for amendment_generator analyze."""
        self._amendment_artifacts = True
        return self

    def _build_dependency_manifest(self, feature_dir: Path) -> None:
        dep_dir = feature_dir / "dependencies"
        dep_dir.mkdir(exist_ok=True)
        content = {
            "dependency_manifest": {
                "feature_info": {
                    "feature_id": self.feature_id,
                    "team_id": self._team_id or "",
                    "epic_id": self._epic_ref or "",
                },
                "external_dependencies": self._dep_manifest,
            }
        }
        import yaml
        (dep_dir / "dependency_manifest.yaml").write_text(
            yaml.dump(content, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )

    def _build_amendment_artifacts(self, feature_dir: Path) -> None:
        """Create .planning/ and run artifacts for amendment analysis."""
        # Create a run directory with findings and decisions
        run_dir = feature_dir / "runs" / "WI-TEST-001" / "RUN-20260301-1000"
        run_dir.mkdir(parents=True, exist_ok=True)

        planning = run_dir / ".planning"
        planning.mkdir(exist_ok=True)

        (planning / "findings.md").write_text(
            "# Findings\n\n"
            "| # | Type | Finding | Impact |\n"
            "|---|------|---------|--------|\n"
            "| 1 | Technical | API timeout needs increase | high |\n"
            "| 2 | Bug | Null check missing | medium |\n",
            encoding="utf-8",
        )

        (planning / "plan.md").write_text(
            "# Plan\n\n"
            "## Decisions\n\n"
            "| # | Decision | Status |\n"
            "|---|----------|--------|\n"
            "| 1 | Use retry with backoff | accepted |\n",
            encoding="utf-8",
        )

        (run_dir / "walkthrough.md").write_text(
            "# Walkthrough\n\nImplementation completed.\n\n"
            "## spec-impact: required\n\nAPI timeout spec needs update.\n",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# EpicBuilder
# ---------------------------------------------------------------------------

class EpicBuilder:
    """Build an epic directory from EPIC-SAMPLE."""

    def __init__(
        self,
        project: ProjectBuilder,
        epic_id: str,
        feature_ids: list[str] | None = None,
    ):
        self._project = project
        self.epic_id = epic_id
        self._feature_ids = feature_ids or []
        self._approved_gates: set[str] = set()

    def with_features(self, *feature_ids: str) -> Self:
        self._feature_ids = list(feature_ids)
        return self

    def with_approval(self, gates: set[str]) -> Self:
        """Set approved epic gates (E1, E2, etc.)."""
        self._approved_gates = gates
        return self

    def done(self) -> ProjectBuilder:
        return self._project

    def _build(self) -> Path:
        epic_dir = self._project.root / "epics" / self.epic_id
        sample = _REPO_ROOT / "epics" / "EPIC-SAMPLE"

        if sample.exists():
            shutil.copytree(sample, epic_dir)
        else:
            epic_dir.mkdir(parents=True, exist_ok=True)

        # Rewrite IDs
        for p in epic_dir.rglob("*"):
            if p.is_file() and p.suffix in (".md", ".yaml", ".yml", ".bpmn"):
                try:
                    text = p.read_text(encoding="utf-8")
                    text = text.replace("EPIC-SAMPLE", self.epic_id)
                    # Update feature list in epic_design if needed
                    if self._feature_ids and p.name == "epic_design.md":
                        for fid in self._feature_ids:
                            if fid not in text:
                                text = text.replace(
                                    '- "FEAT-ERPSAMPLE"',
                                    '- "FEAT-ERPSAMPLE"\n          - "' + fid + '"',
                                    1,
                                )
                    p.write_text(text, encoding="utf-8")
                except UnicodeDecodeError:
                    pass

        # Write EPIC_APPROVAL.md with correct gates
        self._write_epic_approval(epic_dir)

        return epic_dir

    def _write_epic_approval(self, epic_dir: Path) -> None:
        lines = [
            f"# Epic Approval Record: {self.epic_id}",
            "",
            "## Epic Metadata",
            "",
            f"```yaml",
            f'epic_id: "{self.epic_id}"',
            "```",
            "",
        ]
        for gate in ("E1", "E2", "E3", "E4", "E5"):
            check = "x" if gate in self._approved_gates else " "
            lines.append(f"## Gate {gate}: Epic Gate")
            lines.append(f"- [{check}] Review complete")
            if gate in self._approved_gates:
                lines.append("承認者: Test Epic Approver")
                lines.append("日付: 2026-03-01")
            else:
                lines.append("承認者: ___________")
                lines.append("日付: ___________")
            lines.append("")

        (epic_dir / "EPIC_APPROVAL.md").write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Brownfield / Spec-Drift / ADR / Hooks / Run helpers (Phase 3)
# ---------------------------------------------------------------------------

def add_brownfield_indicators(root: Path, lang: str = "node", monorepo: bool = False) -> None:
    """Add brownfield project indicators to a project root."""
    if lang == "node":
        (root / "package.json").write_text(
            '{"name":"test","version":"1.0.0","dependencies":{"express":"^4.0"},"devDependencies":{"jest":"^29.0"}}',
            encoding="utf-8",
        )
        (root / "tsconfig.json").write_text('{"compilerOptions":{"target":"ES2020"}}', encoding="utf-8")
        (root / "src").mkdir(exist_ok=True)
        (root / "src" / "index.ts").write_text("export const app = 'hello';", encoding="utf-8")
    elif lang == "python":
        (root / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "1.0.0"\n', encoding="utf-8")
        (root / "src").mkdir(exist_ok=True)
        (root / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
    elif lang == "go":
        (root / "go.mod").write_text("module test\n\ngo 1.21\n", encoding="utf-8")
        (root / "cmd").mkdir(exist_ok=True)
        (root / "cmd" / "main.go").write_text("package main\nfunc main() {}", encoding="utf-8")
    if monorepo:
        (root / "turbo.json").write_text('{"tasks":{}}', encoding="utf-8")
        (root / "pnpm-workspace.yaml").write_text("packages:\n  - packages/*\n", encoding="utf-8")


def add_spec_drift_artifacts(root: Path, missing_impl: bool = False, extra_impl: bool = False, schema_mismatch: bool = False) -> None:
    """Add OpenAPI contracts and route implementations for drift detection."""
    contracts = root / "contracts"
    contracts.mkdir(exist_ok=True)
    src = root / "src"
    src.mkdir(exist_ok=True)

    # Base contract
    endpoints = [
        {"path": "/api/users", "method": "get", "params": ["limit", "offset"]},
        {"path": "/api/users/{id}", "method": "get", "params": ["id"]},
        {"path": "/api/orders", "method": "post", "params": ["body"]},
    ]
    if missing_impl:
        endpoints.append({"path": "/api/reports", "method": "get", "params": []})

    paths = {}
    for ep in endpoints:
        path_key = ep["path"]
        if path_key not in paths:
            paths[path_key] = {}
        params = [{"name": p, "in": "query"} for p in ep["params"]]
        paths[path_key][ep["method"]] = {"parameters": params, "responses": {"200": {"description": "OK"}}}
        if schema_mismatch and ep["path"] == "/api/users":
            paths[path_key][ep["method"]]["parameters"].append({"name": "extra_field", "in": "query"})

    contract_yaml = "openapi: '3.0.0'\ninfo:\n  title: Test API\n  version: '1.0.0'\npaths:\n"
    for path, methods in paths.items():
        contract_yaml += f"  {path}:\n"
        for method, spec in methods.items():
            contract_yaml += f"    {method}:\n"
            if spec.get("parameters"):
                contract_yaml += "      parameters:\n"
                for p in spec["parameters"]:
                    contract_yaml += f"        - name: {p['name']}\n          in: {p['in']}\n"
            contract_yaml += "      responses:\n        '200':\n          description: OK\n"

    (contracts / "api.yaml").write_text(contract_yaml, encoding="utf-8")

    # Source routes
    route_lines = [
        "// Routes",
        "app.get('/api/users', handler);",
        "app.get('/api/users/:id', handler);",
        "app.post('/api/orders', handler);",
    ]
    if extra_impl:
        route_lines.append("app.delete('/api/legacy', handler);")
    (src / "routes.ts").write_text("\n".join(route_lines), encoding="utf-8")


def add_adr_artifacts(root: Path, count: int = 3, broken_frontmatter: bool = False) -> None:
    """Create shared/decisions/ with ADR files."""
    decisions = root / "shared" / "decisions"
    decisions.mkdir(parents=True, exist_ok=True)
    for i in range(1, count + 1):
        lines = [
            "---",
            f"adr_id: ADR-{i:03d}",
            f"status: {'accepted' if i != count else 'proposed'}",
            f"date: 2026-03-{i:02d}",
            f"title: Decision about feature {i}",
            "---",
            "",
            f"# ADR-{i:03d}: Decision about feature {i}",
            "",
            "## Context",
            f"We need to decide about feature {i}.",
        ]
        (decisions / f"ADR-{i:03d}-decision-feature-{i}.md").write_text("\n".join(lines), encoding="utf-8")
    if broken_frontmatter:
        (decisions / f"ADR-{count + 1:03d}-broken.md").write_text(
            "---\nbroken: [unclosed\n---\n# Broken ADR\n", encoding="utf-8"
        )


def add_hooks_settings(root: Path, state: str = "missing") -> None:
    """Create .claude/settings.json in various states."""
    claude_dir = root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"
    if state == "missing":
        pass  # Don't create the file
    elif state == "empty":
        settings_path.write_text("", encoding="utf-8")
    elif state == "broken":
        settings_path.write_text("{broken json", encoding="utf-8")
    elif state == "existing":
        import json
        settings_path.write_text(json.dumps({
            "hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [
                {"type": "command", "command": "echo existing"}
            ]}]}
        }, indent=2), encoding="utf-8")


def add_coverage_summary(root: Path, line_pct: float = 85.0, branch_pct: float = 70.0, func_pct: float = 90.0) -> None:
    """Create coverage/coverage-summary.json (Istanbul format)."""
    cov_dir = root / "coverage"
    cov_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "total": {
            "lines": {"total": 1000, "covered": int(10 * line_pct), "skipped": 0, "pct": line_pct},
            "branches": {"total": 500, "covered": int(5 * branch_pct), "skipped": 0, "pct": branch_pct},
            "functions": {"total": 200, "covered": int(2 * func_pct), "skipped": 0, "pct": func_pct},
            "statements": {"total": 1200, "covered": 1020, "skipped": 0, "pct": 85.0},
        }
    }
    import json
    (cov_dir / "coverage-summary.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_junit_xml(root: Path, total: int = 10, failures: int = 1, errors: int = 0, skipped: int = 0, time_sec: float = 2.5) -> None:
    """Create test-results.xml (JUnit XML format)."""
    xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuites tests="{total}" failures="{failures}" errors="{errors}" '
        f'skipped="{skipped}" time="{time_sec}">\n'
        f'  <testsuite name="test" tests="{total}" failures="{failures}" '
        f'errors="{errors}" skipped="{skipped}" time="{time_sec}">\n'
    )
    for i in range(total):
        xml += f'    <testcase name="test_{i}" classname="suite" time="0.1"'
        if i < failures:
            xml += '>\n      <failure message="fail"/>\n    </testcase>\n'
        else:
            xml += '/>\n'
    xml += '  </testsuite>\n</testsuites>\n'
    (root / "test-results.xml").write_text(xml, encoding="utf-8")


def add_turbo_cache(root: Path, total: int = 10, cached: int = 7) -> None:
    """Create .turbo/ dir with JSON files to simulate cache hit stats."""
    turbo = root / ".turbo"
    turbo.mkdir(parents=True, exist_ok=True)
    import json
    for i in range(total):
        data = {"hash": f"abc{i:03d}", "status": "HIT" if i < cached else "MISS"}
        (turbo / f"task-{i:03d}.json").write_text(json.dumps(data), encoding="utf-8")


def add_testreport_artifacts(feature_dir: Path, cases: list[dict] | None = None,
                              mapping: list[dict] | None = None,
                              report_html: bool = False, use_evidence_dir: bool = False) -> None:
    """Create testreport/ or evidence/ with cases.json and stride_mapping.yaml."""
    target = feature_dir / ("evidence" if use_evidence_dir else "testreport")
    target.mkdir(parents=True, exist_ok=True)
    import json
    cases = cases or [
        {"id": "01_login", "name": "Login flow", "status": "passed"},
        {"id": "02_order", "name": "Order creation", "status": "passed"},
        {"id": "03_approval", "name": "Approval flow", "status": "failed"},
    ]
    (target / "cases.json").write_text(json.dumps(cases, indent=2), encoding="utf-8")
    if mapping is not None:
        import yaml
        (target / "stride_mapping.yaml").write_text(
            yaml.dump({"mappings": mapping}, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
    if report_html:
        (target / "report.html").write_text("<html><body>Report</body></html>", encoding="utf-8")


def add_state_yaml(feature_dir: Path, work_items: list[dict] | None = None,
                   epic_ref: str | None = None) -> None:
    """Create state/state.yaml with work_items and optional epic_ref."""
    state_dir = feature_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    import yaml
    data: dict = {}
    if epic_ref:
        data["epic_ref"] = epic_ref
    if work_items:
        data["work_items"] = work_items
    (state_dir / "state.yaml").write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )


def add_pm_dashboard(epic_dir: Path) -> None:
    """Create PM_DASHBOARD.md in an epic directory."""
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "PM_DASHBOARD.md").write_text(
        "# PM Dashboard\n\n## Gate Progress\n\n(auto-generated)\n\n---\n\n## Notes\n\n",
        encoding="utf-8",
    )


def add_run_lifecycle(feature_dir: Path, wi_id: str, run_id: str, artifacts: list[str] | None = None) -> Path:
    """Create a run directory with specified artifacts.

    artifacts can include: "findings", "plan", "decision_log", "test_results", "walkthrough"
    """
    run_dir = feature_dir / "runs" / wi_id / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    planning = run_dir / ".planning"
    planning.mkdir(exist_ok=True)
    artifacts = artifacts or []

    if "findings" in artifacts:
        (planning / "findings.md").write_text(
            "# Findings\n\n| # | Type | Finding | Impact |\n|---|------|---------|--------|\n"
            "| 1 | Technical | API timeout | high |\n| 2 | Bug | Null check | medium |\n",
            encoding="utf-8",
        )
    if "plan" in artifacts:
        (planning / "plan.md").write_text(
            "# Plan\n\n## Approach\nImplement incrementally.\n\n## Phases\n1. Setup\n2. Core\n3. Tests\n\n"
            "## Decisions\n| # | Decision | Status |\n|---|----------|--------|\n"
            "| 1 | Use retry with backoff | accepted |\n",
            encoding="utf-8",
        )
    if "decision_log" in artifacts:
        (run_dir / "decision_log.md").write_text(
            "# Decision Log\n\n| # | Decision | Rationale | ADR |\n|---|----------|-----------|-----|\n"
            "| 1 | Use retry | Resilience | ADR-001 |\n",
            encoding="utf-8",
        )
    if "test_results" in artifacts:
        (run_dir / "test_results.md").write_text(
            "# Test Results\n\n## Summary\n- Total: 10\n- Passed: 9\n- Failed: 1\n",
            encoding="utf-8",
        )
    if "walkthrough" in artifacts:
        (run_dir / "walkthrough.md").write_text(
            "# Walkthrough\n\nImplementation completed.\n\n## Files Changed\n"
            "| File | Change | Summary |\n|------|--------|---------|\n"
            "| src/api.ts | modified | Add retry logic |\n\n"
            "## spec-impact: required\n\nAPI timeout spec needs update.\n",
            encoding="utf-8",
        )
    return run_dir
