# Method Approval — {{VERSION}}

> ⚠️ このファイルは Method Board 3 person のみが編集可能。AI による編集は禁止。

## Sign-off (PMO) — 事業整合性 + scope review

確認項目:
- [ ] release scope が事業整合
- [ ] tenant impact が想定範囲

承認者: ____________________
日付:   2026-__-__

## Sign-off (Legal) — Attribution / IP boundary review

確認項目:
- [ ] BABOK / Layered Requirements / value-driven の fair-use 維持
- [ ] IP Boundary Audit no_unintended_exposure: true
- [ ] 顧客契約整合 (tenant policy 影響)

承認者: ____________________
日付:   2026-__-__

## Sign-off (Architect) — Schema 整合 + Cross-repo review

確認項目:
- [ ] CT-FILE-01 (method-store-schema) 整合
- [ ] CT-FILE-03 (sdd_tenant_policy_schema) 整合
- [ ] Feature ③ consumer 側 contract 互換性維持
- [ ] cosign signature 検証成功

承認者: ____________________
日付:   2026-__-__
