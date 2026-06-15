# Rollback Plan - mcframe受注管理アドオン

Feature: FEAT-ERP-OMS

## Rollback Trigger
以下のいずれかに該当する場合、即座にロールバックを実施:
1. 受注登録API が連続5分間エラー率50%以上
2. mcframe 在庫引当連携が完全に停止
3. 監査ログが出力されない（コンプライアンス違反）
4. DB マイグレーションでデータ不整合が発生

## Rollback Steps
1. **APIサービス**: 前バージョンのコンテナイメージにロールバック
   ```bash
   kubectl rollout undo deployment/order-addon-api
   ```
2. **DBマイグレーション**: Alembic でダウングレード
   ```bash
   alembic downgrade -1
   ```
3. **mcframe連携**: 手動で引当解除（mcframe管理画面から）
4. **通知**: Slack #ops-alert + 関係者メール

## Rollback Verification
- [ ] API ヘルスチェック OK
- [ ] 受注登録テスト OK（手動）
- [ ] 監査ログ出力確認
- [ ] mcframe 在庫整合性確認

## Impact Assessment
- ロールバック中の受注データ: PENDING状態で保持、手動で再処理
- 所要時間: 約15分（DB含む）
