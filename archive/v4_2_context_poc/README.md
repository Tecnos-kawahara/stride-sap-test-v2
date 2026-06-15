# v4.2 Retrieval-Led Context PoC

This PoC is intentionally isolated under `experimental/` so the current release flow is not affected.

## Scope

- Build a compressed context index from local SDD documents.
- Query the index to suggest likely reference files.
- Benchmark index-led lookup against a content-scan baseline.

## Non-impact guarantees

1. No change to `sdd-templates/bin/speckit`.
2. No change to hooks, lint enforcement, or phase gate logic.
3. All outputs are opt-in artifacts generated only when these PoC scripts are run.

## Files

- `tools/context_index_builder.py`
- `templates/agent_context_index_template.md`
- `scripts/context_strategy_eval.sh`
- `evals/query_cases.tsv`
- `evals/query_cases_holdout.tsv`

## Quick run

```bash
bash experimental/v4_2_context_poc/scripts/context_strategy_eval.sh
```

By default, artifacts are written to:

`experimental/v4_2_context_poc/out/`

## Expected outputs

- `sdd-context-index.md`: compressed human-readable index
- `sdd-context-index.json`: machine-readable metadata
- `context-eval-report.json`: benchmark results for the query set
