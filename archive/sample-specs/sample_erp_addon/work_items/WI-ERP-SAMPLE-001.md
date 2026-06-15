---
wi_id: WI-ERP-SAMPLE-001
title: "受注登録画面のUI改善"
complexity: low
mode: autopilot
risk_flags: ["ui_only"]
dependencies: []
mode_override:
  reason: ""
spec_refs:
  - "specs/sample_erp_addon/basic_design.md"
  - "specs/sample_erp_addon/spec.md"
contract_refs:
  acceptance_ids: ["AC-US-FEATERPOMS-001-02"]
  contract_ids: ["CT-API-01"]
test_refs:
  - "TS-E2E-01"
owners:
  pm: "@tanaka"
  tech_lead: "@suzuki"
  dev: "@yamada"
  qa: "@sato"
---

# Intent
受注登録画面のボタン配置を改善し、誤操作防止の確認ダイアログを追加する。
ユーザーからの「登録ボタンが分かりにくい」「誤って登録してしまう」というフィードバックへの対応。

# Scope
- UI: 受注登録画面（order_entry.tsx）
- 「登録」ボタンを右下に移動（プライマリアクションの標準位置）
- 確認ダイアログの追加（OK → 保存、キャンセル → 入力画面に戻る）

# Plan
1. 登録ボタンの配置変更（CSS + Layout修正）
2. 確認ダイアログコンポーネント作成
3. E2Eテスト追加（TS-E2E-01: ダイアログ表示確認）
4. 既存UIテストの更新

## Risk Flags
- [x] ui_only — UIのみの変更。API/DB/mcframe連携への影響なし

## Spec Links (Single source of truth)
- UI: order_entry.tsx（ボタン配置変更 + 確認ダイアログ）
- IO: なし（UIのみ変更）
- API/電文: CT-API-01（受注登録API — 変更なし、UIレイヤのみ）
- MSG: なし（メッセージ変更なし）
- TEST: TS-E2E-01（E2Eスモーク — 確認ダイアログ）
- AC: AC-US-FEATERPOMS-001-02（確認ダイアログ表示）
- BPMN: BPMN-TASK-001（受注データ入力）

## Definition of Done
- [x] Spec差分レビュー完了（AC-US-FEATERPOMS-001-02準拠）
- [x] 実装完了（影響箇所列挙）: order_entry.tsx ボタン配置変更 + ConfirmDialog新規作成
- [x] テスト追加/更新（契約＋例外＋メッセージ）: TS-CON-01、例外: キャンセル動作、E2E: TS-E2E-01
- [x] walkthrough（変更点・理由・検証手順）レビュー完了
- [x] CI合格（全50テスト PASS、カバレッジ83.6%）
- [x] Ops更新（輸送/rollback/監視）: UIのみのため影響なし
