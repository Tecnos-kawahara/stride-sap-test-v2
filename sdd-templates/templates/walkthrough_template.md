---
run_id: RUN-{{YYYYMMDD-HHMM}}
wi_id: WI-ERP-{{FEATURE_ID}}-{{NNN}}
mode: autopilot|confirm|validate
---

# What changed
- Spec diff:
- Code diff:
- Files changed:

# Why
- Decisions:
- Brownfield constraints & mitigations:

# How to verify
- Tests executed:
- Expected results summary:

# Risks / Rollback
- Residual risks:
- Rollback steps:

# Evidence
- CI link:
- Artifacts:

# Review Checklist

> Run 完了前に全項目を確認すること。該当しない項目は N/A + 理由を記載。

## Security
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] Input validation at system boundaries
- [ ] No SQL/NoSQL injection risks
- [ ] Error messages do not leak internal details

## AC Coverage
- [ ] All spec_refs ACs verified against implementation
- [ ] All expected values in scenarios.yaml tested
- [ ] Edge cases from NFR addressed

## Code Quality
- [ ] No unused imports or dead code introduced
- [ ] Functions under 50 lines / files under 500 lines
- [ ] Naming follows project conventions

# Mode Decision Rationale (v3.1)
- Selected mode: {{autopilot|confirm|validate}}
- Autonomy bias: {{autonomous|balanced|controlled}}
- Bias-adjusted: {{yes|no}}
- Rationale:

# Spec Drift Status (v4.2)
- Drift check executed: yes|no
- Critical drifts: 0
- High drifts: 0
- Resolution notes:

# Evidence Metrics (v4.2)
- Coverage: {{N}}% (threshold: {{N}}%)
- Test pass rate: {{passed}}/{{total}}
- Cache hit rate: {{N}}%
- Gate lead time: {{N}}h

# PR Readiness (v4.3)
- `stride pr-check` result: PR_READY|NOT_READY
- Warnings:
- Notes:

# Planning Evidence

> このセクションは `/planning` スキルにより自動生成されます。
> Run 実行時の計画・調査・判断の証跡として `.planning/` の内容を要約します。

## Plan Summary
- Goal:
- Phases completed:
- Key decisions:

## Findings Summary
- Investigation count:
- Key discoveries:

## Lessons Learned
- Reusable patterns:
- Errors encountered and resolutions:
