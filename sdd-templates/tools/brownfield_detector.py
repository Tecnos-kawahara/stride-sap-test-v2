#!/usr/bin/env python3
"""Brownfield Detector - Workspace analysis for SDD onboarding.

Detects project type, tech stack, test framework, and structure
from manifest files (package.json, pyproject.toml, go.mod, etc.).

Usage:
    python3 brownfield_detector.py <project_root>
    python3 brownfield_detector.py <project_root> --json
    python3 brownfield_detector.py --test
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def detect_workspace(project_root: Path) -> dict:
    """Analyze project root and return workspace detection results."""
    result = {
        "type": "greenfield",
        "structure": "monolith",
        "languages": [],
        "tech_stack": {},
        "detected_files": {
            "manifests": [],
            "source_dirs": [],
            "config_files": [],
        },
    }

    if not project_root.is_dir():
        return result

    # --- Brownfield detection ---
    source_dirs = ["src", "app", "lib", "pkg", "cmd", "internal"]
    for d in source_dirs:
        if (project_root / d).is_dir():
            result["type"] = "brownfield"
            result["detected_files"]["source_dirs"].append(f"{d}/")

    source_files = ["main.py", "index.ts", "index.js", "main.go", "main.rs"]
    for f in source_files:
        if (project_root / f).is_file():
            result["type"] = "brownfield"

    # --- Monorepo detection ---
    monorepo_indicators = [
        "nx.json", "turbo.json", "pnpm-workspace.yaml",
        "lerna.json", "rush.json", "go.work",
    ]
    for indicator in monorepo_indicators:
        if (project_root / indicator).exists():
            result["structure"] = "monorepo"
            result["detected_files"]["config_files"].append(indicator)
            break

    # --- Config file detection ---
    config_files = [
        ".gitignore", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "Makefile", ".env.example", ".editorconfig", "tsconfig.json",
    ]
    for cf in config_files:
        if (project_root / cf).exists():
            result["detected_files"]["config_files"].append(cf)

    # --- Tech stack detection ---

    # Node.js / JavaScript / TypeScript
    pkg_json = project_root / "package.json"
    if pkg_json.is_file():
        result["detected_files"]["manifests"].append("package.json")
        node_info = _parse_package_json(pkg_json)
        if node_info:
            lang = "typescript" if (project_root / "tsconfig.json").is_file() else "javascript"
            if lang not in result["languages"]:
                result["languages"].append(lang)
            result["tech_stack"][lang] = node_info
            result["tech_stack"][lang]["manifest"] = "package.json"

    # Python
    pyproject = project_root / "pyproject.toml"
    setup_py = project_root / "setup.py"
    requirements = project_root / "requirements.txt"
    if pyproject.is_file():
        result["detected_files"]["manifests"].append("pyproject.toml")
        py_info = _parse_pyproject_toml(pyproject)
        if "python" not in result["languages"]:
            result["languages"].append("python")
        result["tech_stack"]["python"] = py_info
        result["tech_stack"]["python"]["manifest"] = "pyproject.toml"
    elif setup_py.is_file() or requirements.is_file():
        manifest = "setup.py" if setup_py.is_file() else "requirements.txt"
        result["detected_files"]["manifests"].append(manifest)
        if "python" not in result["languages"]:
            result["languages"].append("python")
        result["tech_stack"]["python"] = {"manifest": manifest}

    # Go
    go_mod = project_root / "go.mod"
    if go_mod.is_file():
        result["detected_files"]["manifests"].append("go.mod")
        go_info = _parse_go_mod(go_mod)
        if "go" not in result["languages"]:
            result["languages"].append("go")
        result["tech_stack"]["go"] = go_info
        result["tech_stack"]["go"]["manifest"] = "go.mod"

    # Rust
    cargo = project_root / "Cargo.toml"
    if cargo.is_file():
        result["detected_files"]["manifests"].append("Cargo.toml")
        if "rust" not in result["languages"]:
            result["languages"].append("rust")
        result["tech_stack"]["rust"] = {"manifest": "Cargo.toml"}

    # Java
    pom = project_root / "pom.xml"
    gradle = project_root / "build.gradle"
    gradle_kts = project_root / "build.gradle.kts"
    if pom.is_file():
        result["detected_files"]["manifests"].append("pom.xml")
        if "java" not in result["languages"]:
            result["languages"].append("java")
        result["tech_stack"]["java"] = {"manifest": "pom.xml", "build_tool": "maven"}
    elif gradle.is_file() or gradle_kts.is_file():
        manifest = "build.gradle.kts" if gradle_kts.is_file() else "build.gradle"
        result["detected_files"]["manifests"].append(manifest)
        if "java" not in result["languages"]:
            result["languages"].append("java")
        result["tech_stack"]["java"] = {"manifest": manifest, "build_tool": "gradle"}

    # PHP
    composer = project_root / "composer.json"
    if composer.is_file():
        result["detected_files"]["manifests"].append("composer.json")
        if "php" not in result["languages"]:
            result["languages"].append("php")
        result["tech_stack"]["php"] = {"manifest": "composer.json"}

    return result


def _parse_package_json(path: Path) -> dict:
    """Parse package.json for framework and test framework detection."""
    info = {}
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return info

    # Framework detection from dependencies
    deps = {}
    deps.update(data.get("dependencies", {}))
    deps.update(data.get("devDependencies", {}))

    framework_map = {
        "next": "next.js",
        "nuxt": "nuxt",
        "express": "express",
        "fastify": "fastify",
        "react": "react",
        "vue": "vue",
        "@angular/core": "angular",
        "svelte": "svelte",
    }
    for pkg, name in framework_map.items():
        if pkg in deps:
            info["framework"] = name
            break

    # Test framework detection
    test_map = {
        "jest": "jest",
        "vitest": "vitest",
        "mocha": "mocha",
        "@playwright/test": "playwright",
        "cypress": "cypress",
    }
    for pkg, name in test_map.items():
        if pkg in deps:
            info["test_framework"] = name
            break

    # Check scripts.test as fallback
    if "test_framework" not in info:
        scripts = data.get("scripts", {})
        test_cmd = scripts.get("test", "")
        if "jest" in test_cmd:
            info["test_framework"] = "jest"
        elif "vitest" in test_cmd:
            info["test_framework"] = "vitest"
        elif "mocha" in test_cmd:
            info["test_framework"] = "mocha"

    return info


def _parse_pyproject_toml(path: Path) -> dict:
    """Parse pyproject.toml for framework and test framework detection."""
    info = {}
    try:
        content = path.read_text()
    except OSError:
        return info

    # Try tomllib (Python 3.11+)
    try:
        import tomllib
        with open(path, "rb") as f:
            data = tomllib.load(f)

        # Extract dependencies
        deps = data.get("project", {}).get("dependencies", [])
        deps_str = " ".join(deps) if isinstance(deps, list) else ""

        # Framework detection
        framework_map = {
            "django": "django",
            "flask": "flask",
            "fastapi": "fastapi",
            "starlette": "starlette",
        }
        for pkg, name in framework_map.items():
            if pkg in deps_str.lower():
                info["framework"] = name
                break

        # Test framework from [tool.pytest]
        if "tool" in data and "pytest" in data["tool"]:
            info["test_framework"] = "pytest"

        # Python version
        requires = data.get("project", {}).get("requires-python", "")
        if requires:
            info["version"] = requires

        return info

    except ImportError:
        pass

    # Fallback: basic text parsing
    if "[tool.pytest" in content:
        info["test_framework"] = "pytest"

    framework_patterns = {
        "django": "django",
        "flask": "flask",
        "fastapi": "fastapi",
    }
    for pattern, name in framework_patterns.items():
        if pattern in content.lower():
            info["framework"] = name
            break

    return info


def _parse_go_mod(path: Path) -> dict:
    """Parse go.mod for module name and key dependencies."""
    info = {}
    try:
        content = path.read_text()
    except OSError:
        return info

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("module "):
            info["module"] = line.split(None, 1)[1]
        elif line.startswith("go "):
            info["version"] = line.split(None, 1)[1]

    # Framework detection in require block
    framework_map = {
        "gin-gonic/gin": "gin",
        "labstack/echo": "echo",
        "gofiber/fiber": "fiber",
        "gorilla/mux": "gorilla",
    }
    for pkg, name in framework_map.items():
        if pkg in content:
            info["framework"] = name
            break

    return info


def format_human_readable(result: dict) -> str:
    """Format detection result for human-readable terminal output."""
    lines = []
    lines.append("Workspace Detection Results")
    lines.append("=" * 27)
    lines.append(f"Type:      {result['type']}")
    lines.append(f"Structure: {result['structure']}")
    lines.append(f"Languages: {', '.join(result['languages']) if result['languages'] else '(none detected)'}")
    lines.append("")

    if result["tech_stack"]:
        lines.append("Tech Stack:")
        for lang, info in result["tech_stack"].items():
            lines.append(f"  {lang}:")
            for key, val in info.items():
                if key != "manifest":
                    lines.append(f"    {key}: {val}")
            lines.append(f"    manifest: {info.get('manifest', '-')}")
        lines.append("")

    detected = []
    detected.extend(result["detected_files"].get("manifests", []))
    detected.extend(result["detected_files"].get("source_dirs", []))
    detected.extend(result["detected_files"].get("config_files", []))
    if detected:
        lines.append(f"Detected: {', '.join(detected)}")

    return "\n".join(lines)


def run_self_tests():
    """Run self-tests using temporary directories."""
    print("Running brownfield_detector.py self-tests...")
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
            print(f"  Test {total} FAILED: {name} — {e}")

    # Test 1: Empty directory -> greenfield
    def test_empty():
        with tempfile.TemporaryDirectory() as d:
            r = detect_workspace(Path(d))
            assert r["type"] == "greenfield", f"expected greenfield, got {r['type']}"
            assert r["structure"] == "monolith"
            assert r["languages"] == []

    test("empty directory -> greenfield", test_empty)

    # Test 2: Directory with src/ and package.json -> brownfield + node
    def test_node_brownfield():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "src").mkdir()
            (p / "package.json").write_text(json.dumps({
                "dependencies": {"express": "^4.18.0"},
                "devDependencies": {"jest": "^29.0.0"}
            }))
            r = detect_workspace(p)
            assert r["type"] == "brownfield", f"expected brownfield, got {r['type']}"
            assert "javascript" in r["languages"], f"expected javascript in {r['languages']}"
            assert r["tech_stack"]["javascript"]["framework"] == "express"
            assert r["tech_stack"]["javascript"]["test_framework"] == "jest"

    test("src/ + package.json -> brownfield + express + jest", test_node_brownfield)

    # Test 3: Directory with pyproject.toml + [tool.pytest] -> python + pytest
    def test_python_pytest():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "pyproject.toml").write_text('[tool.pytest.ini_options]\ntestpaths = ["tests"]\n\n[project]\ndependencies = ["fastapi>=0.100"]\n')
            r = detect_workspace(p)
            assert "python" in r["languages"], f"expected python in {r['languages']}"
            assert r["tech_stack"]["python"].get("test_framework") == "pytest"

    test("pyproject.toml with [tool.pytest] -> python + pytest", test_python_pytest)

    # Test 4: Directory with go.mod -> go
    def test_go():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "go.mod").write_text("module github.com/example/myapp\n\ngo 1.21\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n)\n")
            r = detect_workspace(p)
            assert "go" in r["languages"], f"expected go in {r['languages']}"
            assert r["tech_stack"]["go"].get("framework") == "gin"
            assert r["tech_stack"]["go"].get("version") == "1.21"

    test("go.mod -> go + gin", test_go)

    # Test 5: Directory with nx.json -> monorepo
    def test_monorepo():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "nx.json").write_text("{}")
            r = detect_workspace(p)
            assert r["structure"] == "monorepo", f"expected monorepo, got {r['structure']}"

    test("nx.json -> monorepo", test_monorepo)

    # Test 6: Non-existent directory -> greenfield (no crash)
    def test_nonexistent():
        r = detect_workspace(Path("/tmp/nonexistent_brownfield_test_dir_12345"))
        assert r["type"] == "greenfield"
        assert r["languages"] == []

    test("non-existent directory -> greenfield (graceful)", test_nonexistent)

    # Test 7: TypeScript detection (tsconfig.json present)
    def test_typescript():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "tsconfig.json").write_text("{}")
            (p / "package.json").write_text(json.dumps({
                "dependencies": {"next": "^14.0.0"},
                "devDependencies": {"vitest": "^1.0.0"}
            }))
            r = detect_workspace(p)
            assert "typescript" in r["languages"], f"expected typescript in {r['languages']}"
            assert r["tech_stack"]["typescript"]["framework"] == "next.js"
            assert r["tech_stack"]["typescript"]["test_framework"] == "vitest"

    test("tsconfig.json + package.json -> typescript + next.js + vitest", test_typescript)

    # Test 8: Multiple languages
    def test_multi_lang():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "package.json").write_text(json.dumps({"dependencies": {"react": "^18.0"}}))
            (p / "pyproject.toml").write_text('[project]\ndependencies = ["django>=4.0"]\n')
            (p / "src").mkdir()
            r = detect_workspace(p)
            assert r["type"] == "brownfield"
            assert len(r["languages"]) >= 2

    test("package.json + pyproject.toml -> multi-language", test_multi_lang)

    print(f"\nAll {passed}/{total} self-tests passed." if passed == total else f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


def main():
    parser = argparse.ArgumentParser(description="Brownfield Detector - Workspace analysis for SDD onboarding")
    parser.add_argument("project_root", nargs="?", help="Project root directory to analyze")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(run_self_tests())

    if not args.project_root:
        parser.error("project_root is required (or use --test)")

    root = Path(args.project_root)
    if not root.is_dir():
        print(f"Error: '{args.project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    result = detect_workspace(root)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human_readable(result))


if __name__ == "__main__":
    main()
