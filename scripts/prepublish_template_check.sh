#!/usr/bin/env bash
set -euo pipefail

# Ensure template repository does not accidentally publish local-only artifacts.

if ! command -v rg >/dev/null 2>&1; then
  echo "FAIL: ripgrep (rg) is required for this script."
  exit 1
fi

forbidden_patterns='^(\.brv/|\.entire/|\.planning/|\.swarm/|\.claude-flow/|\.playwright-mcp/|\.claude/settings\.local\.json$|tasks\.md$|\.DS_Store$)'
tracked="$(git ls-files)"

violations="$(printf '%s\n' "$tracked" | rg "$forbidden_patterns" || true)"

if [ -n "$violations" ]; then
  echo "FAIL: Local-only files are tracked and should not be published:"
  printf '%s\n' "$violations"
  exit 1
fi

echo "PASS: No local-only artifacts are tracked."
echo "Next: review 'git status' and publish."
