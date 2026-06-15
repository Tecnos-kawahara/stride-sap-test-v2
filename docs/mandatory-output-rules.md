# Mandatory Output Rules

These rules standardize AI-generated terminal output for readability and consistency.

## Rules

1. No fixed-width ASCII tables.
2. For options, use `N - **Option**: Description`.
3. Status labels must be one of: `PASS`, `FAIL`, `WARN`, `SKIP`.
4. Multi-step progress must use `[n/N]` format.
5. HITL checkpoints must be explicit and marked as `WARN`.

## Command

```bash
sdd-templates/bin/stride output-rules
```
