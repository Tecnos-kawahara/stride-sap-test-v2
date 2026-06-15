# Hypercare Runbook - mcframe受注管理アドオン

Feature: FEAT-ERP-OMS

## Hypercare Period
- **開始**: リリース日
- **終了**: リリース後 2週間
- **体制**: 平日 9:00-18:00 オンコール

## Monitoring Dashboard
- Grafana: `https://grafana.tecnos.local/d/order-addon`
- Alerts: Slack #ops-order-addon

## Key Metrics to Watch
| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| API Response Time (P95) | < 3s | 3-5s | > 5s |
| Error Rate | < 1% | 1-5% | > 5% |
| mcframe Allocation Latency | < 5s | 5-10s | > 10s |
| DB Connection Pool Usage | < 70% | 70-90% | > 90% |

## Known Issues & Workarounds
1. **mcframe APIタイムアウト**: 月次締め期間（毎月25-末日）は処理集中のため応答遅延の可能性あり
   - **対応**: リトライ間隔を延長（3s → 10s）、アラート閾値を緩和
2. **在庫不足PENDING**: 在庫引当失敗の受注はPENDING_STOCK状態で滞留
   - **対応**: 毎朝9:00にPENDINGリストを営業担当にメール通知

## Escalation Path
1. **L1**: 開発チーム（@yamada, @sato）→ 30分以内に応答
2. **L2**: Tech Lead（@suzuki）→ 1時間以内に判断
3. **L3**: PM（@tanaka）+ mcframe チーム → ロールバック判断
