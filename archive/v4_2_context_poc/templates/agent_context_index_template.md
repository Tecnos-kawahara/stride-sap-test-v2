# AGENT CONTEXT INDEX (PoC Template)

Use this as an include snippet for AGENTS.md or CLAUDE.md in experiment branches only.

```text
[SDD Context Index]|root:{{ROOT}}|generated:{{GENERATED_AT}}|files:{{TOTAL_FILES}}|dirs:{{TOTAL_DIRS}}
|IMPORTANT: Prefer retrieval-led reasoning over pre-training-led reasoning for SDD tasks.
|IMPORTANT: If uncertain, open one referenced file before writing or editing code.
|{{DIR_1}}:{file_a.md,file_b.md,...}
|{{DIR_2}}:{file_c.md,file_d.md,...}
```

## Rules

1. Keep only index lines in prompt context.
2. Keep source documents on disk and retrieve them on demand.
3. Do not duplicate SSoT content into AGENTS.md directly.

