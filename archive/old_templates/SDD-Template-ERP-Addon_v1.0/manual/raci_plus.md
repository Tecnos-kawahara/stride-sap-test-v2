# RACI+（ERPアドオン版：Tecnos標準）

## 目的
AI実装前提でも「意思決定・承認・説明責任」を崩さないため、RACIにAI/CIを追加する。

## 役割
- PM: スコープ/合意/リスク/対顧客
- Tech Lead: 設計品質/技術判断/レビュー
- Dev: 実装/テスト実装
- QA: テスト戦略/品質ゲート/再現性
- Ops: 輸送/リリース/監視/ハイパーケア
- AI: 提案/下書き生成/実装支援（承認は不可）
- CI: 自動検証（SAST/SCA/Secrets/Coverage/Tests）

## Gate×責務（要約）
| Gate | 主成果物 | R | A | C | I |
|---|---|---|---|---|---|
| 1 | basic_design.md | PM | PM | TL/QA | Ops/顧客 |
| 2 | process.bpmn | PM/TL | PM | QA | Ops/顧客 |
| 3 | spec.md | PM | PM | TL/QA | Ops/顧客 |
| 4 | plan.md | TL | TL | PM/QA | Ops |
| 5 | tasks.md + WI/state | TL | TL | PM/QA | Ops |
| Run | walkthrough + CI | Dev/AI | TL | QA/Ops | PM |
| Final | evidence_pack + ops | QA/Ops | PM+TL | Dev | 顧客 |

注：RunのAは「mode」により変動（validateはOpsもC→A寄り）。
