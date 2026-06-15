# Release Checklist - mcframe受注管理アドオン

Feature: FEAT-ERP-OMS

## Pre-Release
- [ ] 全テスト PASS（50/50）
- [ ] カバレッジ ≥ 80%（現在: 83.6%）
- [ ] stride-lint PASS
- [ ] spec:drift 0 critical
- [ ] `stride pr-check` → PR_READY
- [ ] Gate 1-5 承認済み
- [ ] DB マイグレーション検証済み（staging）
- [ ] mcframe API 接続確認済み（staging）

## Deployment
- [ ] DB マイグレーション実行
- [ ] コンテナイメージデプロイ
- [ ] ヘルスチェック確認（/health）
- [ ] mcframe 在庫引当テスト実行（本番データ）

## Post-Release
- [ ] 受注登録の動作確認（営業担当1名）
- [ ] 監査ログ出力確認
- [ ] ハイパーケア体制開始（hypercare_runbook.md参照）
- [ ] Final Gate 承認依頼
