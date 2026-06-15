---
version: "{{VERSION}}"
channel: "{{CHANNEL}}"
generated_at: "{{GENERATED_AT}}"
generator_version: "release_notes_generator.py 1.0"
previous_stable: "{{PREVIOUS_STABLE}}"
---

# Method Store Release Notes — {{VERSION}}

## Summary
{{ONE_OR_TWO_LINE_SUMMARY}}

## Changes from {{PREVIOUS_STABLE}}
- templates: {{N}} modified
- skills: {{N}} added/modified
- policies: {{N}} changes
- hooks: {{N}} changes
- validators: {{N}} modified

## IP Boundary Audit
- no_unintended_exposure: true
- internal_markers_count: {{N}}
- violations: 0

## Attribution Audit
- BABOK v3 (IIBA): fair-use 維持確認
- Layered Requirements Modeling: concept reference 維持
- value-driven discovery: philosophical inspiration 維持

## Test Results
- stride lint: PASS
- stride method audit: PASS (no_unintended_exposure: true)
- smoke test: 3/3 PASS (staging)

## Cosign Signature
- Rekor log entry: {{REKOR_UUID}}
- Fulcio certificate identity: {{FULCIO_IDENTITY}}

## Tenant Impact Estimate
- auto_upgrade=minor 設定 tenant: 推定 {{N}} 件
- pin 設定 tenant: 推定 {{N}} 件で受領しない

## Method Board Sign-off Required
See METHOD_APPROVAL.md in this directory for the 3 person 多人数署名 template.
