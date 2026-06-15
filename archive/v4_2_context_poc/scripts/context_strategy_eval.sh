#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
POC_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$POC_ROOT/../.." && pwd)"

TOOL="$POC_ROOT/tools/context_index_builder.py"
CASES="$POC_ROOT/evals/query_cases.tsv"
OUT_DIR="${1:-$POC_ROOT/out}"

INDEX_TEXT="$OUT_DIR/sdd-context-index.md"
INDEX_META="$OUT_DIR/sdd-context-index.json"
REPORT_JSON="$OUT_DIR/context-eval-report.json"

mkdir -p "$OUT_DIR"

echo "[1/3] Building compressed context index..."
python3 "$TOOL" build \
  --root "$REPO_ROOT" \
  --dirs "manual,docs,agent_docs,sdd-templates/templates" \
  --extensions ".md,.yaml,.yml" \
  --output "$INDEX_TEXT" \
  --metadata "$INDEX_META"

echo "[2/3] Running benchmark (index vs content scan baseline)..."
python3 "$TOOL" benchmark \
  --root "$REPO_ROOT" \
  --dirs "manual,docs,agent_docs,sdd-templates/templates" \
  --extensions ".md,.yaml,.yml" \
  --cases "$CASES" \
  --index-metadata "$INDEX_META" \
  --top-k 3 \
  --json-report "$REPORT_JSON"

echo "[3/3] PoC artifacts"
echo "PASS: index_text=$INDEX_TEXT"
echo "PASS: index_metadata=$INDEX_META"
echo "PASS: benchmark_report=$REPORT_JSON"
