#!/usr/bin/env python3
"""Spec Drift Detector - Detect divergence between contracts/ and src/.

Parses OpenAPI YAML from contracts/ and scans src/ for implementation
indicators (route definitions, handler functions). Reports drift types:
  - endpoint_not_implemented: endpoint in contract but no matching route
  - schema_mismatch: response fields in contract don't match TS types
  - parameter_missing: required params in contract not in handler
  - contract_outdated: implementation has endpoints not in contract

Usage:
    python3 spec_drift_detector.py <project_root>
    python3 spec_drift_detector.py <project_root> --json
    python3 spec_drift_detector.py <project_root> --verbose
    python3 spec_drift_detector.py --test
"""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------

SEVERITY = {
    "endpoint_not_implemented": "critical",
    "contract_outdated": "high",
    "schema_mismatch": "medium",
    "parameter_missing": "medium",
}


# ---------------------------------------------------------------------------
# Contract parsing
# ---------------------------------------------------------------------------

def parse_openapi_contracts(contracts_dir: Path) -> list[dict]:
    """Parse OpenAPI YAML files and extract endpoint definitions.

    Returns list of dicts with keys: path, method, parameters, response_fields, source_file.
    """
    if yaml is None or not contracts_dir.is_dir():
        return []

    endpoints = []
    for f in sorted(contracts_dir.glob("*.yaml")) + sorted(contracts_dir.glob("*.yml")):
        try:
            text = f.read_text(encoding="utf-8")
            doc = yaml.safe_load(text)
        except Exception:
            continue

        if not isinstance(doc, dict):
            continue

        # Must have paths to be an OpenAPI doc
        paths = doc.get("paths")
        if not isinstance(paths, dict):
            continue

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, operation in methods.items():
                if method.startswith("x-") or method in ("summary", "description", "parameters", "servers"):
                    continue
                if not isinstance(operation, dict):
                    continue

                # Extract parameters
                params = []
                for p in operation.get("parameters", []):
                    if isinstance(p, dict) and p.get("name"):
                        params.append({
                            "name": p["name"],
                            "in": p.get("in", "query"),
                            "required": p.get("required", False),
                        })

                # Extract response fields from 200/201 response schema
                response_fields = []
                responses = operation.get("responses", {})
                for code in ("200", "201", 200, 201):
                    resp = responses.get(code)
                    if isinstance(resp, dict):
                        schema = _extract_schema(resp)
                        if schema:
                            response_fields = _extract_field_names(schema)
                        break

                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "parameters": params,
                    "response_fields": response_fields,
                    "source_file": f.name,
                })

    return endpoints


def _extract_schema(response: dict) -> dict:
    """Extract schema from OpenAPI response object."""
    content = response.get("content", {})
    for media_type in ("application/json", "*/*"):
        if media_type in content:
            return content[media_type].get("schema", {})
    # OpenAPI 2.x style
    return response.get("schema", {})


def _extract_field_names(schema: dict, prefix: str = "") -> list[str]:
    """Recursively extract field names from schema properties."""
    fields = []
    if not isinstance(schema, dict):
        return fields

    props = schema.get("properties", {})
    if isinstance(props, dict):
        for name in props:
            full = f"{prefix}{name}" if not prefix else f"{prefix}.{name}"
            fields.append(full)

    # Handle items for array schemas
    items = schema.get("items", {})
    if isinstance(items, dict) and items.get("properties"):
        for name in items["properties"]:
            full = f"{prefix}[].{name}" if prefix else f"[].{name}"
            fields.append(full)

    return fields


# ---------------------------------------------------------------------------
# Source scanning
# ---------------------------------------------------------------------------

# Route patterns for common frameworks
ROUTE_PATTERNS = [
    # Express.js: app.get('/path', ...) or router.get('/path', ...)
    re.compile(r"""(?:app|router)\.(get|post|put|patch|delete|options|head)\s*\(\s*['"`]([^'"`]+)['"`]""", re.IGNORECASE),
    # Fastify: fastify.get('/path', ...)
    re.compile(r"""fastify\.(get|post|put|patch|delete)\s*\(\s*['"`]([^'"`]+)['"`]""", re.IGNORECASE),
    # NestJS: @Get('/path'), @Post('/path'), etc.
    re.compile(r"""@(Get|Post|Put|Patch|Delete|Options|Head)\s*\(\s*['"`]([^'"`]+)['"`]\s*\)""", re.IGNORECASE),
    # Flask/FastAPI: @app.get('/path') or @router.get('/path')
    re.compile(r"""@(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*['"`]([^'"`]+)['"`]""", re.IGNORECASE),
    # Go: r.GET("/path", ...) or e.GET("/path", ...)
    re.compile(r"""\.\s*(GET|POST|PUT|PATCH|DELETE)\s*\(\s*"([^"]+)""", re.IGNORECASE),
]

# TypeScript type/interface field extraction
TS_FIELD_PATTERN = re.compile(r"""^\s*(\w+)\s*[?:]""", re.MULTILINE)

# Handler parameter patterns
HANDLER_PARAM_PATTERNS = [
    # req.params.name, req.query.name, req.body.name
    re.compile(r"""req\.(params|query|body|headers)\.(\w+)"""),
    re.compile(r"""req\.(params|query|body|headers)\[['"`](\w+)['"`]\]"""),
    # ctx.params(), ctx.query() (Hono/Koa style)
    re.compile(r"""ctx\.(param|query)\s*\(\s*['"`](\w+)['"`]\s*\)"""),
]


def scan_source_routes(src_dir: Path) -> list[dict]:
    """Scan src/ for route definitions.

    Returns list of dicts with keys: path, method, file, params_used.
    """
    if not src_dir.is_dir():
        return []

    routes = []
    extensions = {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs"}

    for root, dirs, files in os.walk(src_dir):
        # Skip node_modules, dist, etc.
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".next", "__pycache__", "vendor")]
        for fname in files:
            fpath = Path(root) / fname
            if fpath.suffix not in extensions:
                continue
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for pattern in ROUTE_PATTERNS:
                for match in pattern.finditer(content):
                    method = match.group(1).upper()
                    path = match.group(2)
                    # Normalize path: Express :param -> OpenAPI {param}
                    normalized = re.sub(r":(\w+)", r"{\1}", path)

                    # Extract params used in the handler (nearby lines)
                    params_used = set()
                    # Get a window of ~30 lines after the route definition
                    start = match.end()
                    window = content[start:start + 2000]
                    for pp in HANDLER_PARAM_PATTERNS:
                        for pm in pp.finditer(window):
                            params_used.add(pm.group(2))

                    routes.append({
                        "path": normalized,
                        "method": method,
                        "file": str(fpath.relative_to(src_dir)),
                        "params_used": list(params_used),
                    })

    return routes


def scan_source_types(src_dir: Path) -> dict[str, list[str]]:
    """Scan src/ for TypeScript interface/type field definitions.

    Returns dict of type_name -> [field_names].
    """
    if not src_dir.is_dir():
        return {}

    types = {}
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in ("node_modules", "dist", ".next")]
        for fname in files:
            if not fname.endswith((".ts", ".tsx")):
                continue
            fpath = Path(root) / fname
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Extract interfaces/types
            for m in re.finditer(
                r"""(?:export\s+)?(?:interface|type)\s+(\w+)\s*(?:=\s*)?{([^}]*)}""",
                content, re.DOTALL,
            ):
                type_name = m.group(1)
                body = m.group(2)
                fields = TS_FIELD_PATTERN.findall(body)
                if fields:
                    types[type_name] = fields

    return types


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

def detect_drift(project_root: Path, verbose: bool = False) -> dict:
    """Run drift detection and return results.

    Returns dict with keys: drifts (list), summary, contracts_count, routes_count.
    """
    contracts_dir = project_root / "contracts"
    src_dir = project_root / "src"

    # Also check specs/*/contracts/ pattern
    if not contracts_dir.is_dir():
        specs_dir = project_root / "specs"
        if specs_dir.is_dir():
            for feature in specs_dir.iterdir():
                if (feature / "contracts").is_dir():
                    contracts_dir = feature / "contracts"
                    break

    contract_endpoints = parse_openapi_contracts(contracts_dir)
    source_routes = scan_source_routes(src_dir)
    source_types = scan_source_types(src_dir)

    drifts = []

    # Normalize paths for comparison
    def normalize_path(p: str) -> str:
        """Normalize path for comparison: remove trailing slash, lowercase."""
        return p.rstrip("/").lower()

    contract_paths = {
        (normalize_path(ep["path"]), ep["method"])
        for ep in contract_endpoints
    }
    source_paths = {
        (normalize_path(r["path"]), r["method"])
        for r in source_routes
    }

    # 1. endpoint_not_implemented: in contract but not in src
    for ep in contract_endpoints:
        key = (normalize_path(ep["path"]), ep["method"])
        if key not in source_paths:
            drifts.append({
                "type": "endpoint_not_implemented",
                "severity": SEVERITY["endpoint_not_implemented"],
                "path": ep["path"],
                "method": ep["method"],
                "contract_file": ep["source_file"],
                "message": f"{ep['method']} {ep['path']} defined in {ep['source_file']} but not found in src/",
            })

    # 2. contract_outdated: in src but not in contract
    for route in source_routes:
        key = (normalize_path(route["path"]), route["method"])
        if key not in contract_paths and contract_endpoints:
            drifts.append({
                "type": "contract_outdated",
                "severity": SEVERITY["contract_outdated"],
                "path": route["path"],
                "method": route["method"],
                "source_file": route["file"],
                "message": f"{route['method']} {route['path']} found in src/{route['file']} but not in contracts/",
            })

    # 3. parameter_missing: required params in contract not used in handler
    for ep in contract_endpoints:
        key = (normalize_path(ep["path"]), ep["method"])
        matching_routes = [
            r for r in source_routes
            if (normalize_path(r["path"]), r["method"]) == key
        ]
        if not matching_routes:
            continue

        required_params = [p["name"] for p in ep.get("parameters", []) if p.get("required")]
        for route in matching_routes:
            for param in required_params:
                if param not in route.get("params_used", []):
                    drifts.append({
                        "type": "parameter_missing",
                        "severity": SEVERITY["parameter_missing"],
                        "path": ep["path"],
                        "method": ep["method"],
                        "parameter": param,
                        "source_file": route["file"],
                        "message": f"Required param '{param}' for {ep['method']} {ep['path']} not found in src/{route['file']}",
                    })

    # 4. schema_mismatch: response fields in contract don't match TS types
    # (lightweight heuristic: check if any contract response fields are in known types)
    if source_types:
        for ep in contract_endpoints:
            if not ep.get("response_fields"):
                continue
            key = (normalize_path(ep["path"]), ep["method"])
            if key not in source_paths:
                continue  # Already caught by endpoint_not_implemented

            # Check if response fields are in any known type
            contract_fields = set(ep["response_fields"])
            found_matching_type = False
            for type_name, type_fields in source_types.items():
                if contract_fields.issubset(set(type_fields)):
                    found_matching_type = True
                    break

            if not found_matching_type and contract_fields:
                all_src_fields = set()
                for fields in source_types.values():
                    all_src_fields.update(fields)
                missing = contract_fields - all_src_fields
                if missing:
                    drifts.append({
                        "type": "schema_mismatch",
                        "severity": SEVERITY["schema_mismatch"],
                        "path": ep["path"],
                        "method": ep["method"],
                        "missing_fields": sorted(missing),
                        "message": f"Response fields {sorted(missing)} for {ep['method']} {ep['path']} not found in TypeScript types",
                    })

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    drifts.sort(key=lambda d: severity_order.get(d.get("severity", "low"), 3))

    summary = {
        "total_drifts": len(drifts),
        "critical": sum(1 for d in drifts if d["severity"] == "critical"),
        "high": sum(1 for d in drifts if d["severity"] == "high"),
        "medium": sum(1 for d in drifts if d["severity"] == "medium"),
        "low": sum(1 for d in drifts if d["severity"] == "low"),
    }

    return {
        "drifts": drifts,
        "summary": summary,
        "contracts_count": len(contract_endpoints),
        "routes_count": len(source_routes),
    }


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_human_readable(result: dict, verbose: bool = False) -> str:
    """Format drift results for terminal output."""
    lines = []
    lines.append("Spec Drift Detection Results")
    lines.append("=" * 28)
    lines.append(f"Contracts scanned: {result['contracts_count']} endpoints")
    lines.append(f"Source routes found: {result['routes_count']}")
    lines.append("")

    summary = result["summary"]
    if summary["total_drifts"] == 0:
        lines.append("[PASS] No spec drift detected")
        return "\n".join(lines)

    lines.append(f"[WARN] {summary['total_drifts']} drift(s) detected")
    lines.append(f"  Critical: {summary['critical']}, High: {summary['high']}, "
                 f"Medium: {summary['medium']}, Low: {summary['low']}")
    lines.append("")

    for d in result["drifts"]:
        severity_tag = d["severity"].upper()
        lines.append(f"  [{severity_tag}] {d['type']}: {d['message']}")
        if verbose:
            for k, v in d.items():
                if k not in ("type", "severity", "message"):
                    lines.append(f"         {k}: {v}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Spec Drift Detector - Detect divergence between contracts/ and src/",
    )
    parser.add_argument("project_root", nargs="?", help="Project root directory")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show additional details")
    parser.add_argument("--test", action="store_true", help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        sys.exit(_run_self_tests())

    if not args.project_root:
        parser.error("project_root is required (or use --test)")

    root = Path(args.project_root)
    if not root.is_dir():
        print(f"Error: '{args.project_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    result = detect_drift(root, verbose=args.verbose)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_human_readable(result, verbose=args.verbose))

    # Exit with 1 if critical drifts found
    if result["summary"]["critical"] > 0:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def _run_self_tests() -> int:
    """Run self-tests using temporary directories."""
    if yaml is None:
        print("PyYAML not available; cannot run self-tests.")
        return 2

    print("Running spec_drift_detector.py self-tests...")
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
            print(f"  Test {total} FAILED: {name} -- {e}")

    # Test 1: Empty contracts dir -> no drift
    def test_empty():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "src").mkdir()
            r = detect_drift(p)
            assert r["summary"]["total_drifts"] == 0, f"expected 0 drifts, got {r['summary']['total_drifts']}"
            assert r["contracts_count"] == 0

    test("empty contracts -> no drift", test_empty)

    # Test 2: Matching implementation -> no drift
    def test_matching():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "contracts" / "api.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "paths": {
                    "/api/users": {
                        "get": {
                            "summary": "List users",
                            "responses": {"200": {"description": "OK"}},
                        },
                    },
                },
            }))
            (p / "src").mkdir()
            (p / "src" / "routes.ts").write_text("""
import express from 'express';
const router = express.Router();
router.get('/api/users', (req, res) => { res.json([]); });
export default router;
""")
            r = detect_drift(p)
            assert r["contracts_count"] == 1, f"expected 1 contract endpoint, got {r['contracts_count']}"
            assert r["routes_count"] >= 1, f"expected >=1 route, got {r['routes_count']}"
            # No endpoint_not_implemented drift
            not_impl = [d for d in r["drifts"] if d["type"] == "endpoint_not_implemented"]
            assert len(not_impl) == 0, f"expected 0 not_implemented, got {len(not_impl)}"

    test("matching impl -> no endpoint drift", test_matching)

    # Test 3: Missing endpoint -> endpoint_not_implemented
    def test_missing_endpoint():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "contracts" / "api.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "paths": {
                    "/api/users": {
                        "get": {"responses": {"200": {"description": "OK"}}},
                    },
                    "/api/orders": {
                        "post": {"responses": {"201": {"description": "Created"}}},
                    },
                },
            }))
            (p / "src").mkdir()
            (p / "src" / "routes.ts").write_text("""
router.get('/api/users', handler);
""")
            r = detect_drift(p)
            not_impl = [d for d in r["drifts"] if d["type"] == "endpoint_not_implemented"]
            assert len(not_impl) == 1, f"expected 1 not_implemented, got {len(not_impl)}"
            assert not_impl[0]["path"] == "/api/orders"
            assert not_impl[0]["severity"] == "critical"

    test("missing endpoint -> endpoint_not_implemented", test_missing_endpoint)

    # Test 4: Extra endpoint in src -> contract_outdated
    def test_extra_endpoint():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "contracts" / "api.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "paths": {
                    "/api/users": {
                        "get": {"responses": {"200": {"description": "OK"}}},
                    },
                },
            }))
            (p / "src").mkdir()
            (p / "src" / "routes.ts").write_text("""
router.get('/api/users', handler);
router.post('/api/users', createHandler);
""")
            r = detect_drift(p)
            outdated = [d for d in r["drifts"] if d["type"] == "contract_outdated"]
            assert len(outdated) == 1, f"expected 1 contract_outdated, got {len(outdated)}"
            assert outdated[0]["severity"] == "high"

    test("extra endpoint in src -> contract_outdated", test_extra_endpoint)

    # Test 5: Schema drift (response fields not in TS types)
    def test_schema_drift():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "contracts" / "api.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "paths": {
                    "/api/users": {
                        "get": {
                            "responses": {
                                "200": {
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "properties": {
                                                    "id": {"type": "string"},
                                                    "name": {"type": "string"},
                                                    "email": {"type": "string"},
                                                    "department": {"type": "string"},
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                },
            }))
            (p / "src").mkdir()
            (p / "src" / "routes.ts").write_text("""
router.get('/api/users', handler);
""")
            (p / "src" / "types.ts").write_text("""
export interface User {
    id: string;
    name: string;
    email: string;
}
""")
            r = detect_drift(p)
            schema_drifts = [d for d in r["drifts"] if d["type"] == "schema_mismatch"]
            assert len(schema_drifts) >= 1, f"expected >=1 schema_mismatch, got {len(schema_drifts)}"
            # 'department' should be in missing fields
            missing = schema_drifts[0].get("missing_fields", [])
            assert "department" in missing, f"expected 'department' in missing, got {missing}"

    test("schema drift -> schema_mismatch", test_schema_drift)

    # Test 6: Multiple contracts
    def test_multiple_contracts():
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "contracts").mkdir()
            (p / "contracts" / "users.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "paths": {"/api/users": {"get": {"responses": {"200": {"description": "OK"}}}}},
            }))
            (p / "contracts" / "orders.yaml").write_text(yaml.dump({
                "openapi": "3.0.0",
                "paths": {"/api/orders": {"get": {"responses": {"200": {"description": "OK"}}}}},
            }))
            (p / "src").mkdir()
            (p / "src" / "routes.ts").write_text("""
router.get('/api/users', handler);
router.get('/api/orders', handler);
""")
            r = detect_drift(p)
            assert r["contracts_count"] == 2, f"expected 2 contract endpoints, got {r['contracts_count']}"
            not_impl = [d for d in r["drifts"] if d["type"] == "endpoint_not_implemented"]
            assert len(not_impl) == 0, f"expected 0 not_implemented, got {len(not_impl)}"

    test("multiple contracts -> all matched", test_multiple_contracts)

    print(f"\nAll {passed}/{total} self-tests passed." if passed == total else f"\n{passed}/{total} tests passed.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    main()
