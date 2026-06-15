#!/usr/bin/env python3
"""Build and benchmark a compressed retrieval index for local SDD docs.

This is an isolated PoC tool and is intentionally not wired into release flows.

Usage:
    python3 context_index_builder.py build --root . --output /tmp/index.md --metadata /tmp/index.json
    python3 context_index_builder.py query --index-metadata /tmp/index.json --q "mandatory output rules"
    python3 context_index_builder.py benchmark --root . --cases evals/query_cases.tsv
    python3 context_index_builder.py --test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_INCLUDE_DIRS = [
    "manual",
    "docs",
    "agent_docs",
    "sdd-templates/templates",
]
DEFAULT_EXTENSIONS = [".md", ".yaml", ".yml"]
IGNORED_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}
TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")
TOKEN_ALIASES: dict[str, list[str]] = {
    "workflow": ["bpmn", "process"],
    "diagram": ["bpmn"],
    "feature": ["spec"],
    "specification": ["spec"],
    "authoring": ["guide", "template"],
    "implementation": ["plan", "execution"],
    "planning": ["plan"],
    "failure": ["troubleshooting", "error"],
    "rulebook": ["rules"],
    "catalog": ["commands"],
    "repository": ["project", "map"],
    "coordination": ["multi", "team"],
    "operation": ["ops", "playbook"],
    "operations": ["ops", "playbook"],
    "checkpoints": ["governance"],
}


@dataclass
class FileEntry:
    rel_path: str
    directory: str
    basename: str
    file_stem: str
    size_bytes: int
    path_tokens: list[str]
    content_tokens: set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "rel_path": self.rel_path,
            "directory": self.directory,
            "basename": self.basename,
            "file_stem": self.file_stem,
            "size_bytes": self.size_bytes,
            "path_tokens": self.path_tokens,
        }

    @staticmethod
    def from_dict(payload: dict) -> "FileEntry":
        return FileEntry(
            rel_path=str(payload["rel_path"]),
            directory=str(payload["directory"]),
            basename=str(payload["basename"]),
            file_stem=str(payload["file_stem"]),
            size_bytes=int(payload.get("size_bytes", 0)),
            path_tokens=list(payload.get("path_tokens", [])),
            content_tokens=set(),
        )


def parse_csv_arg(value: str) -> list[str]:
    items = [part.strip() for part in value.split(",")]
    return [item for item in items if item]


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    pieces = TOKEN_SPLIT_RE.split(lowered)
    return [piece for piece in pieces if len(piece) >= 2]


def expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded: set[str] = set(tokens)
    for token in list(expanded):
        for alias in TOKEN_ALIASES.get(token, []):
            expanded.add(alias)
    return sorted(expanded)


def should_skip_path(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORED_DIR_NAMES:
            return True
    return False


def collect_entries(
    root: Path,
    include_dirs: list[str],
    extensions: set[str],
    with_content_tokens: bool = False,
) -> list[FileEntry]:
    entries: list[FileEntry] = []
    for rel_dir in include_dirs:
        base = root / rel_dir
        if not base.exists() or not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if should_skip_path(path):
                continue
            if not path.is_file():
                continue
            if path.suffix.lower() not in extensions:
                continue

            rel_path = path.relative_to(root).as_posix()
            directory = path.relative_to(root).parent.as_posix()
            size_bytes = path.stat().st_size
            path_tokens = tokenize(rel_path)
            entry = FileEntry(
                rel_path=rel_path,
                directory=directory,
                basename=path.name,
                file_stem=path.stem,
                size_bytes=size_bytes,
                path_tokens=path_tokens,
            )
            if with_content_tokens:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    text = ""
                entry.content_tokens = set(tokenize(text))

            entries.append(entry)
    entries.sort(key=lambda e: e.rel_path)
    return entries


def build_path_token_df(entries: list[FileEntry]) -> dict[str, int]:
    df: dict[str, int] = {}
    for entry in entries:
        unique_tokens = set(entry.path_tokens)
        for token in unique_tokens:
            df[token] = df.get(token, 0) + 1
    return df


def render_index_text(
    entries: list[FileEntry],
    root_label: str,
    max_files_per_dir: int,
) -> str:
    grouped: dict[str, list[str]] = {}
    for entry in entries:
        grouped.setdefault(entry.directory, []).append(entry.basename)

    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    lines: list[str] = []
    lines.append(
        "[SDD Context Index]"
        f"|root:{root_label}"
        f"|generated:{generated}"
        f"|files:{len(entries)}"
        f"|dirs:{len(grouped)}"
    )
    lines.append(
        "|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning for SDD tasks."
    )
    lines.append(
        "|IMPORTANT: If uncertain, open one referenced file before writing or editing code."
    )

    for directory in sorted(grouped.keys()):
        file_names = sorted(set(grouped[directory]))
        truncated = ""
        if len(file_names) > max_files_per_dir:
            remain = len(file_names) - max_files_per_dir
            file_names = file_names[:max_files_per_dir]
            truncated = f",...(+{remain})"
        files_part = ",".join(file_names)
        lines.append(f"|{directory}:{{{files_part}{truncated}}}")

    return "\n".join(lines) + "\n"


def build_stats(entries: list[FileEntry], index_text: str) -> dict:
    raw_bytes = sum(entry.size_bytes for entry in entries)
    index_bytes = len(index_text.encode("utf-8"))
    compression_ratio = (index_bytes / raw_bytes) if raw_bytes > 0 else 0.0
    return {
        "total_files": len(entries),
        "total_raw_bytes": raw_bytes,
        "index_bytes": index_bytes,
        "compression_ratio": round(compression_ratio, 6),
    }


def build_metadata_payload(
    root: Path,
    include_dirs: list[str],
    extensions: list[str],
    entries: list[FileEntry],
    stats: dict,
) -> dict:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "generated_at": generated,
        "root": str(root.resolve()),
        "include_dirs": include_dirs,
        "extensions": extensions,
        "stats": stats,
        "entries": [entry.to_dict() for entry in entries],
    }


def load_metadata_entries(path: Path) -> tuple[list[FileEntry], dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = [FileEntry.from_dict(item) for item in payload.get("entries", [])]
    return entries, payload


def _index_score(
    entry: FileEntry,
    query: str,
    query_tokens: list[str],
    token_df: dict[str, int],
    total_docs: int,
) -> float:
    if not query_tokens:
        return 0.0

    score = 0.0
    rel_lower = entry.rel_path.lower()
    file_tokens = set(tokenize(entry.file_stem))
    dir_tokens = set(tokenize(entry.directory))
    path_tokens = set(entry.path_tokens)

    for token in query_tokens:
        df = token_df.get(token, total_docs)
        rarity = 1.0 + (3.0 / max(1, df))
        if token in file_tokens:
            score += 6.0 * rarity
        elif token in dir_tokens:
            score += 3.0 * rarity
        elif token in path_tokens:
            score += 2.0 * rarity
        elif token in rel_lower:
            score += 1.0 * rarity

    if query.lower() in rel_lower:
        score += 4.0

    if all(token in path_tokens or token in rel_lower for token in query_tokens):
        score += 2.0
    return score


def query_index(entries: list[FileEntry], query: str, top_k: int) -> list[dict]:
    query_tokens = expand_query_tokens(tokenize(query))
    token_df = build_path_token_df(entries)
    total_docs = max(1, len(entries))
    ranked: list[tuple[float, str]] = []
    for entry in entries:
        score = _index_score(entry, query, query_tokens, token_df, total_docs)
        if score > 0.0:
            ranked.append((score, entry.rel_path))
    ranked.sort(key=lambda pair: (-pair[0], pair[1]))
    top = ranked[:top_k]
    return [{"rel_path": rel_path, "score": round(score, 3)} for score, rel_path in top]


def query_content_scan(entries: list[FileEntry], query: str, top_k: int) -> list[dict]:
    query_tokens = expand_query_tokens(tokenize(query))
    ranked: list[tuple[float, str]] = []
    for entry in entries:
        if not entry.content_tokens:
            continue
        score = 0.0
        for token in query_tokens:
            if token in entry.content_tokens:
                score += 1.0
        if score > 0.0:
            ranked.append((score, entry.rel_path))
    ranked.sort(key=lambda pair: (-pair[0], pair[1]))
    top = ranked[:top_k]
    return [{"rel_path": rel_path, "score": round(score, 3)} for score, rel_path in top]


def query_path_baseline(entries: list[FileEntry], query: str, top_k: int) -> list[dict]:
    """Naive path-only baseline without weighted ranking."""
    query_tokens = expand_query_tokens(tokenize(query))
    ranked: list[tuple[float, str]] = []
    for entry in entries:
        rel_lower = entry.rel_path.lower()
        score = 0.0
        for token in query_tokens:
            if token in rel_lower:
                score += 1.0
        if query.lower() in rel_lower:
            score += 1.0
        if score > 0.0:
            ranked.append((score, entry.rel_path))
    ranked.sort(key=lambda pair: (-pair[0], pair[1]))
    top = ranked[:top_k]
    return [{"rel_path": rel_path, "score": round(score, 3)} for score, rel_path in top]


def read_cases(path: Path) -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" not in line:
            raise ValueError(f"Invalid case line (tab required): {line}")
        query, expected = line.split("\t", 1)
        query = query.strip()
        expected = expected.strip()
        if not query or not expected:
            raise ValueError(f"Invalid case line (empty query/expected): {line}")
        cases.append((query, expected))
    return cases


def benchmark(
    index_entries: list[FileEntry],
    scan_entries: list[FileEntry],
    cases: list[tuple[str, str]],
    top_k: int,
) -> dict:
    index_top1 = 0
    index_topk = 0
    scan_top1 = 0
    scan_topk = 0
    path_top1 = 0
    path_topk = 0
    index_total_ms = 0.0
    scan_total_ms = 0.0
    path_total_ms = 0.0
    details: list[dict] = []

    for query, expected in cases:
        t0 = time.perf_counter()
        index_results = query_index(index_entries, query, top_k)
        index_total_ms += (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        scan_results = query_content_scan(scan_entries, query, top_k)
        scan_total_ms += (time.perf_counter() - t1) * 1000.0

        t2 = time.perf_counter()
        path_results = query_path_baseline(index_entries, query, top_k)
        path_total_ms += (time.perf_counter() - t2) * 1000.0

        index_paths = [item["rel_path"] for item in index_results]
        scan_paths = [item["rel_path"] for item in scan_results]
        path_paths = [item["rel_path"] for item in path_results]

        index_hit_top1 = len(index_paths) > 0 and index_paths[0] == expected
        index_hit_topk = expected in index_paths
        scan_hit_top1 = len(scan_paths) > 0 and scan_paths[0] == expected
        scan_hit_topk = expected in scan_paths
        path_hit_top1 = len(path_paths) > 0 and path_paths[0] == expected
        path_hit_topk = expected in path_paths

        if index_hit_top1:
            index_top1 += 1
        if index_hit_topk:
            index_topk += 1
        if scan_hit_top1:
            scan_top1 += 1
        if scan_hit_topk:
            scan_topk += 1
        if path_hit_top1:
            path_top1 += 1
        if path_hit_topk:
            path_topk += 1

        details.append(
            {
                "query": query,
                "expected": expected,
                "index_top1": index_hit_top1,
                "index_topk": index_hit_topk,
                "scan_top1": scan_hit_top1,
                "scan_topk": scan_hit_topk,
                "path_top1": path_hit_top1,
                "path_topk": path_hit_topk,
                "index_predictions": index_paths,
                "scan_predictions": scan_paths,
                "path_predictions": path_paths,
            }
        )

    total = len(cases)
    result = {
        "cases": total,
        "top_k": top_k,
        "index": {
            "top1_hits": index_top1,
            "topk_hits": index_topk,
            "top1_rate": round((index_top1 / total) if total else 0.0, 6),
            "topk_rate": round((index_topk / total) if total else 0.0, 6),
            "avg_ms_per_query": round((index_total_ms / total) if total else 0.0, 6),
        },
        "content_scan": {
            "top1_hits": scan_top1,
            "topk_hits": scan_topk,
            "top1_rate": round((scan_top1 / total) if total else 0.0, 6),
            "topk_rate": round((scan_topk / total) if total else 0.0, 6),
            "avg_ms_per_query": round((scan_total_ms / total) if total else 0.0, 6),
        },
        "path_baseline": {
            "top1_hits": path_top1,
            "topk_hits": path_topk,
            "top1_rate": round((path_top1 / total) if total else 0.0, 6),
            "topk_rate": round((path_topk / total) if total else 0.0, 6),
            "avg_ms_per_query": round((path_total_ms / total) if total else 0.0, 6),
        },
        "details": details,
    }
    return result


def command_build(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    include_dirs = parse_csv_arg(args.dirs)
    extensions = {ext.lower() for ext in parse_csv_arg(args.extensions)}
    entries = collect_entries(root, include_dirs, extensions, with_content_tokens=False)
    index_text = render_index_text(entries, root_label=".", max_files_per_dir=args.max_files_per_dir)
    stats = build_stats(entries, index_text)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(index_text, encoding="utf-8")
        print(f"PASS: wrote index text to {output_path}")
    else:
        print(index_text, end="")

    if args.metadata:
        payload = build_metadata_payload(
            root=root,
            include_dirs=include_dirs,
            extensions=sorted(extensions),
            entries=entries,
            stats=stats,
        )
        metadata_path = Path(args.metadata)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PASS: wrote metadata to {metadata_path}")

    print(
        "PASS: build stats "
        f"files={stats['total_files']} raw_bytes={stats['total_raw_bytes']} "
        f"index_bytes={stats['index_bytes']} compression_ratio={stats['compression_ratio']}"
    )
    return 0


def command_query(args: argparse.Namespace) -> int:
    entries, payload = load_metadata_entries(Path(args.index_metadata))
    results = query_index(entries, args.q, args.top_k)
    print(f"Query: {args.q}")
    print(f"Index: {args.index_metadata}")
    print(f"Entries: {len(entries)}")
    if not results:
        print("WARN: no candidates found")
        return 0
    for idx, item in enumerate(results, start=1):
        print(f"{idx}. score={item['score']} path={item['rel_path']}")
    if args.print_stats and isinstance(payload.get("stats"), dict):
        stats = payload["stats"]
        print(
            "Stats: "
            f"files={stats.get('total_files')} "
            f"compression_ratio={stats.get('compression_ratio')}"
        )
    return 0


def command_benchmark(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    include_dirs = parse_csv_arg(args.dirs)
    extensions = {ext.lower() for ext in parse_csv_arg(args.extensions)}
    cases = read_cases(Path(args.cases))

    if args.index_metadata:
        index_entries, payload = load_metadata_entries(Path(args.index_metadata))
        stats = payload.get("stats", {})
    else:
        index_entries = collect_entries(root, include_dirs, extensions, with_content_tokens=False)
        index_text = render_index_text(index_entries, root_label=".", max_files_per_dir=args.max_files_per_dir)
        stats = build_stats(index_entries, index_text)

    scan_entries = collect_entries(root, include_dirs, extensions, with_content_tokens=True)

    result = benchmark(index_entries, scan_entries, cases, args.top_k)
    result["index_stats"] = stats
    result["root"] = str(root)
    result["include_dirs"] = include_dirs
    result["extensions"] = sorted(extensions)

    index_summary = result["index"]
    scan_summary = result["content_scan"]
    path_summary = result["path_baseline"]
    print(f"PASS: benchmark cases={result['cases']} top_k={result['top_k']}")
    print(
        "PASS: index strategy "
        f"top1={index_summary['top1_hits']}/{result['cases']} "
        f"topk={index_summary['topk_hits']}/{result['cases']} "
        f"avg_ms={index_summary['avg_ms_per_query']}"
    )
    print(
        "PASS: content-scan baseline "
        f"top1={scan_summary['top1_hits']}/{result['cases']} "
        f"topk={scan_summary['topk_hits']}/{result['cases']} "
        f"avg_ms={scan_summary['avg_ms_per_query']}"
    )
    print(
        "PASS: path-only baseline "
        f"top1={path_summary['top1_hits']}/{result['cases']} "
        f"topk={path_summary['topk_hits']}/{result['cases']} "
        f"avg_ms={path_summary['avg_ms_per_query']}"
    )
    print(
        "PASS: compression "
        f"ratio={result['index_stats'].get('compression_ratio')} "
        f"index_bytes={result['index_stats'].get('index_bytes')} "
        f"raw_bytes={result['index_stats'].get('total_raw_bytes')}"
    )

    failures = [
        detail for detail in result["details"]
        if not detail["index_topk"]
    ]
    if failures:
        print(f"WARN: index misses in top-{result['top_k']}: {len(failures)}")
        for detail in failures[:10]:
            print(
                "  "
                f"query='{detail['query']}' expected='{detail['expected']}' "
                f"index_predictions={detail['index_predictions']}"
            )
    else:
        print(f"PASS: index matched all cases within top-{result['top_k']}")

    if args.json_report:
        report_path = Path(args.json_report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"PASS: wrote benchmark report to {report_path}")

    return 0


def _make_temp_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_self_tests() -> None:
    import tempfile

    print("Running self-tests...")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        _make_temp_file(
            root / "docs" / "mandatory-output-rules.md",
            "PASS FAIL WARN SKIP\nPrefer retrieval-led reasoning.\n" * 10,
        )
        _make_temp_file(
            root / "manual" / "23_execution_governance_guide.md",
            "Execution governance and phase gate checks.\n" * 8,
        )
        _make_temp_file(
            root / "agent_docs" / "commands.md",
            "Commands reference and run modes.\n" * 6,
        )
        _make_temp_file(
            root / "sdd-templates" / "templates" / "spec_template.md",
            "spec template acceptance criteria.\n" * 9,
        )

        include_dirs = DEFAULT_INCLUDE_DIRS
        extensions = {".md"}
        entries = collect_entries(root, include_dirs, extensions, with_content_tokens=False)
        assert len(entries) == 4, f"expected 4 entries, got {len(entries)}"
        print("  Test 1 passed: entry collection")

        index_text = render_index_text(entries, root_label=".", max_files_per_dir=100)
        stats = build_stats(entries, index_text)
        assert stats["compression_ratio"] < 1.0, "expected compressed index smaller than source docs"
        assert "|docs:{" in index_text, "expected docs directory in index output"
        print("  Test 2 passed: index rendering and compression stats")

        query_results = query_index(entries, "mandatory output rules", top_k=3)
        assert query_results, "expected query results"
        assert query_results[0]["rel_path"] == "docs/mandatory-output-rules.md", "unexpected top result"
        print("  Test 3 passed: index query ranking")

        scan_entries = collect_entries(root, include_dirs, extensions, with_content_tokens=True)
        scan_results = query_content_scan(scan_entries, "execution governance", top_k=3)
        assert scan_results, "expected scan query results"
        assert scan_results[0]["rel_path"] == "manual/23_execution_governance_guide.md", "content scan top result mismatch"
        print("  Test 4 passed: content-scan baseline")

        cases_path = root / "cases.tsv"
        cases_path.write_text(
            "mandatory output rules\tdocs/mandatory-output-rules.md\n"
            "execution governance\tmanual/23_execution_governance_guide.md\n"
            "spec template\tsdd-templates/templates/spec_template.md\n",
            encoding="utf-8",
        )
        cases = read_cases(cases_path)
        report = benchmark(entries, scan_entries, cases, top_k=3)
        assert report["index"]["topk_hits"] == 3, "expected index to hit all 3 cases"
        assert "path_baseline" in report, "path baseline summary missing"
        print("  Test 5 passed: benchmark pipeline")

        metadata = build_metadata_payload(
            root=root,
            include_dirs=include_dirs,
            extensions=[".md"],
            entries=entries,
            stats=stats,
        )
        metadata_path = root / "index.json"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        loaded_entries, _ = load_metadata_entries(metadata_path)
        assert len(loaded_entries) == len(entries), "metadata round-trip entry count mismatch"
        print("  Test 6 passed: metadata round-trip")

    print("All self-tests passed.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Context index PoC builder and evaluator.",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests.",
    )
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build compressed index and metadata.")
    build_parser.add_argument("--root", default=".", help="Project root path.")
    build_parser.add_argument(
        "--dirs",
        default=",".join(DEFAULT_INCLUDE_DIRS),
        help="Comma-separated include directories relative to root.",
    )
    build_parser.add_argument(
        "--extensions",
        default=",".join(DEFAULT_EXTENSIONS),
        help="Comma-separated file extensions to index.",
    )
    build_parser.add_argument(
        "--max-files-per-dir",
        type=int,
        default=80,
        help="Maximum file names per directory in text output.",
    )
    build_parser.add_argument("--output", help="Write compressed index text to file.")
    build_parser.add_argument("--metadata", help="Write JSON metadata to file.")

    query_parser = subparsers.add_parser("query", help="Query existing metadata index.")
    query_parser.add_argument("--index-metadata", required=True, help="JSON metadata path from build.")
    query_parser.add_argument("--q", required=True, help="Query text.")
    query_parser.add_argument("--top-k", type=int, default=5, help="Number of candidates.")
    query_parser.add_argument("--print-stats", action="store_true", help="Print index stats.")

    bench_parser = subparsers.add_parser("benchmark", help="Benchmark index against content scan.")
    bench_parser.add_argument("--root", default=".", help="Project root path.")
    bench_parser.add_argument(
        "--dirs",
        default=",".join(DEFAULT_INCLUDE_DIRS),
        help="Comma-separated include directories relative to root.",
    )
    bench_parser.add_argument(
        "--extensions",
        default=",".join(DEFAULT_EXTENSIONS),
        help="Comma-separated file extensions to scan.",
    )
    bench_parser.add_argument("--cases", required=True, help="TSV cases file: query<TAB>expected_path.")
    bench_parser.add_argument("--index-metadata", help="Optional metadata JSON from build.")
    bench_parser.add_argument("--top-k", type=int, default=3, help="Top-K hit threshold.")
    bench_parser.add_argument(
        "--max-files-per-dir",
        type=int,
        default=80,
        help="Used only when index-metadata is omitted.",
    )
    bench_parser.add_argument("--json-report", help="Write benchmark report JSON.")

    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.test:
        _run_self_tests()
        return 0

    if args.command == "build":
        return command_build(args)
    if args.command == "query":
        return command_query(args)
    if args.command == "benchmark":
        return command_benchmark(args)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
