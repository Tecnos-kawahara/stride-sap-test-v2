# TEIM/PMOゲートへのマッピング（案）

> TEIMの詳細ゲート定義に合わせて調整してください。ここでは「考え方の対応」を示します。

## 1. 対応関係（概念）
- TEIMの「設計品質ゲート」 = Gate 1〜4（Specパックの完成）
- TEIMの「構築/試験ゲート」 = Gate 5 + Run（変更単位の実行/検証）
- TEIMの「移行/稼働ゲート」 = Final（監査パック + Opsパック）

## 2. PMOの運用ポイント
- FB/是正は Run 単位で記録（walkthroughのDecision/Notesに残す）
- 横展開は Run/State をRAG格納（検索可能な単位にする）
- リスクは risk_flags で機械分類（modeの根拠として残す）
