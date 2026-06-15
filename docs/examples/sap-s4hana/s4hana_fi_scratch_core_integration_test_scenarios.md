# S/4HANA FI × スクラッチ基幹 システム連携 統合テストシナリオ

対象 BPMN: [s4hana_fi_scratch_core_integration_epic_flow.bpmn](/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise/s4hana_fi_scratch_core_integration_epic_flow.bpmn)

## 1. 目的

このシナリオ集は、S/4HANA を FI 専用で利用し、業務トランザクション SoR をスクラッチ基幹に残す構成において、以下を統合テストで確認するためのものです。

- 会計マスタ差分と会計仕訳イベントが正しい順序と粒度で連携されること
- S/4HANA FI が会計伝票起票、入出金消込、月次レポート生成を正しく実行すること
- スクラッチ基幹が起票結果・消込結果を受けて業務ステータスを正しく更新すること
- 月次締めに必要な例外情報が経理へ漏れなく連携されること

## 2. テスト範囲

### 2.1 対象 participant

- `Participant_Core`: スクラッチ基幹システム
- `Participant_FI`: S/4HANA FI
- `Participant_Bank`: 銀行・決済サービス
- `Participant_Accounting`: 経理部門

### 2.2 対象 messageFlow

- `MsgFlow_CoreToFI_MasterDelta`
- `MsgFlow_CoreToFI_AccountingEvent`
- `MsgFlow_FIToCore_PostingResult`
- `MsgFlow_BankToFI_BankStatement`
- `MsgFlow_FIToCore_ClearingResult`
- `MsgFlow_FIToAccounting_CloseReport`

### 2.3 カバレッジ方針

本シナリオ集では、BPMN 上の「統合テスト対象ブロック」を以下 26 要素と定義します。

- 業務ブロック 20 要素
  - `Task_Core_RecordTransaction`
  - `Task_Core_SendMasterDelta`
  - `Task_Core_SendAccountingEvent`
  - `Task_Core_ReceivePostingResult`
  - `Task_Core_UpdateBusinessStatus`
  - `Task_Core_ReceiveClearingResult`
  - `Task_Core_UpdateARAPStatus`
  - `Task_FI_ReceiveMasterDelta`
  - `Task_FI_ValidateMasterMapping`
  - `Task_FI_ReceiveAccountingEvent`
  - `Task_FI_PostAccountingDocument`
  - `Task_FI_SendPostingResult`
  - `Task_FI_ReceiveBankStatement`
  - `Task_FI_ClearOpenItems`
  - `Task_FI_SendClearingResult`
  - `Task_FI_SendCloseReport`
  - `Task_Bank_ExecuteSettlement`
  - `Task_Bank_SendBankStatement`
  - `Task_Accounting_ReceiveCloseReport`
  - `Task_Accounting_ReconcileException`
- messageFlow 6 要素
  - `MsgFlow_CoreToFI_MasterDelta`
  - `MsgFlow_CoreToFI_AccountingEvent`
  - `MsgFlow_FIToCore_PostingResult`
  - `MsgFlow_BankToFI_BankStatement`
  - `MsgFlow_FIToCore_ClearingResult`
  - `MsgFlow_FIToAccounting_CloseReport`

### 2.4 カバレッジ結果

| 観点 | 対象 | 本シナリオ集でカバー | カバレッジ |
|---|---:|---:|---:|
| participant | 4 | 4 | 100% |
| messageFlow | 6 | 6 | 100% |
| 統合テスト対象ブロック | 26 | 26 | 100% |

80% 要件に対して、対象ブロック基準で 100% を満たします。

## 3. 共通前提

- スクラッチ基幹の業務イベント送信基盤は疎通済みで、`event_id` と `correlation_id` を保持できる
- S/4HANA FI はテスト会社コード、勘定コード、BP、税コードを投入済み
- 銀行・決済サービスはテスト用の入出金明細を返せる
- 全 messageFlow に対して送信ログ、受信ログ、再送ログ、エラーログを採取できる
- 起票結果は `journal_entry_id`、消込結果は `clearing_status` / `residual_amount`、月次レポートは `close_report_id` で追跡できる

## 4. シナリオ一覧

| ID | 種別 | シナリオ名 | 主対象 |
|---|---|---|---|
| `TS-INT-FI-001` | 正常系 | 売上請求イベントの会計起票成功 | マスタ差分、仕訳イベント、起票結果返却 |
| `TS-INT-FI-002` | 正常系 | 入金明細による売掛消込成功 | 銀行明細、消込結果、月次レポート |
| `TS-INT-FI-003` | 正常系 | 支払実行明細による買掛決済成功 | 支払結果の FI 反映と基幹同期 |
| `TS-INT-FI-004` | 準正常 | 会計イベントがマスタ差分到着前に送られる | 順序ずれ耐性 |
| `TS-INT-FI-005` | 異常系 | 勘定/取引先マッピング不備で起票差戻し | 起票失敗と業務保留 |
| `TS-INT-FI-006` | 異常系 | 会計イベント重複送信時の冪等制御 | 重複起票防止 |
| `TS-INT-FI-007` | 異常系 | 銀行明細が未照合で消込不能 | 未消込差異の返却 |
| `TS-INT-FI-008` | 準正常 | 部分入金により残額が残る | 一部消込と残高同期 |
| `TS-INT-FI-009` | 異常系 | 締め時点で未解決例外を含む月次レポート | 経理差異照合 |
| `TS-INT-FI-010` | 回復系 | マスタ修正後の再送・再起票成功 | リカバリと締め反映 |

## 5. 詳細シナリオ

### TS-INT-FI-001 正常系: 売上請求イベントの会計起票成功

- 目的:
  - スクラッチ基幹の売上請求確定から S/4HANA FI の会計伝票起票、起票結果返却までが正常完了することを確認する
- カバー BPMN ID:
  - `Task_Core_RecordTransaction`
  - `Task_Core_SendMasterDelta`
  - `Task_Core_SendAccountingEvent`
  - `Task_FI_ReceiveMasterDelta`
  - `Task_FI_ValidateMasterMapping`
  - `Task_FI_ReceiveAccountingEvent`
  - `Task_FI_PostAccountingDocument`
  - `Task_FI_SendPostingResult`
  - `Task_Core_ReceivePostingResult`
  - `Task_Core_UpdateBusinessStatus`
  - `MsgFlow_CoreToFI_MasterDelta`
  - `MsgFlow_CoreToFI_AccountingEvent`
  - `MsgFlow_FIToCore_PostingResult`
- 前提:
  - 顧客 BP、売掛勘定、税コード、支払条件が S/4HANA FI に存在する
  - スクラッチ基幹の請求イベント `EVT-AR-0001` が作成済み
- 手順:
  1. スクラッチ基幹で請求確定処理を実行する
  2. 会計マスタ差分を S/4HANA FI に送信する
  3. 会計仕訳イベントを S/4HANA FI に送信する
  4. S/4HANA FI で会計伝票を起票する
  5. 起票結果をスクラッチ基幹へ返却する
- 期待結果:
  - `MsgFlow_CoreToFI_MasterDelta` の payload に会計に不要な業務属性が含まれない
  - `MsgFlow_CoreToFI_AccountingEvent` に `event_id` と重複排除キーが含まれる
  - S/4HANA FI に会計伝票が 1 件だけ起票される
  - スクラッチ基幹の業務ステータスが `POSTED` に更新される
  - 起票結果に `journal_entry_id`、会計年度、成功ステータスが返る
- 検証:
  - 送受信ログ確認
  - S/4HANA 会計伝票確認
  - スクラッチ基幹ステータス確認

### TS-INT-FI-002 正常系: 入金明細による売掛消込成功

- 目的:
  - 銀行明細受領後に S/4HANA FI が売掛を全額消込し、その結果を基幹と経理へ連携できることを確認する
- カバー BPMN ID:
  - `Task_Bank_ExecuteSettlement`
  - `Task_Bank_SendBankStatement`
  - `Task_FI_ReceiveBankStatement`
  - `Task_FI_ClearOpenItems`
  - `Task_FI_SendClearingResult`
  - `Task_FI_SendCloseReport`
  - `Task_Core_ReceiveClearingResult`
  - `Task_Core_UpdateARAPStatus`
  - `Task_Accounting_ReceiveCloseReport`
  - `Task_Accounting_ReconcileException`
  - `MsgFlow_BankToFI_BankStatement`
  - `MsgFlow_FIToCore_ClearingResult`
  - `MsgFlow_FIToAccounting_CloseReport`
- 前提:
  - `TS-INT-FI-001` の起票済み請求が未入金状態で存在する
  - 銀行側に請求額と一致する入金明細がある
- 手順:
  1. 銀行・決済サービスで入金実行を完了させる
  2. 入金明細を S/4HANA FI に送信する
  3. S/4HANA FI で売掛消込を実行する
  4. 消込結果をスクラッチ基幹へ返却する
  5. 月次残高・例外レポートを経理へ送信する
- 期待結果:
  - 対象請求が全額消込される
  - スクラッチ基幹の債権状態が `CLEARED` になる
  - 月次レポートに当該取引が未消込として残らない
  - 経理向け例外件数が 0 件である
- 検証:
  - 銀行明細取込ログ確認
  - 消込結果確認
  - スクラッチ基幹債権台帳確認
  - 月次レポート内容確認

### TS-INT-FI-003 正常系: 支払実行明細による買掛決済成功

- 目的:
  - 買掛側でも同じ連携モデルで決済結果がスクラッチ基幹に返ることを確認する
- カバー BPMN ID:
  - `Task_Bank_ExecuteSettlement`
  - `Task_Bank_SendBankStatement`
  - `Task_FI_ReceiveBankStatement`
  - `Task_FI_ClearOpenItems`
  - `Task_FI_SendClearingResult`
  - `Task_Core_ReceiveClearingResult`
  - `Task_Core_UpdateARAPStatus`
  - `MsgFlow_BankToFI_BankStatement`
  - `MsgFlow_FIToCore_ClearingResult`
- 前提:
  - 支払依頼イベントに基づく買掛伝票が起票済み
  - 決済サービス側に支払完了明細が存在する
- 手順:
  1. 支払実行明細を銀行・決済サービスから返す
  2. S/4HANA FI で買掛決済処理を行う
  3. 結果をスクラッチ基幹へ返却する
- 期待結果:
  - 買掛オープン項目が支払済みになる
  - スクラッチ基幹の支払依頼状態が `PAID` になる
  - 二重支払扱いにならない
- 検証:
  - 支払明細ログ確認
  - FI 側決済状態確認
  - スクラッチ基幹支払状態確認

### TS-INT-FI-004 準正常: 会計イベントがマスタ差分到着前に送られる

- 目的:
  - 順序ずれが起きても、S/4HANA FI が不正起票せずに保留または差戻しできることを確認する
- カバー BPMN ID:
  - `Task_Core_SendAccountingEvent`
  - `Task_FI_ReceiveAccountingEvent`
  - `Task_FI_ValidateMasterMapping`
  - `Task_FI_SendPostingResult`
  - `Task_Core_ReceivePostingResult`
  - `Task_Core_UpdateBusinessStatus`
  - `MsgFlow_CoreToFI_AccountingEvent`
  - `MsgFlow_FIToCore_PostingResult`
- 前提:
  - 対象取引先の会計マスタ差分がまだ未送信
- 手順:
  1. 会計仕訳イベントだけを先行送信する
  2. S/4HANA FI の受信・検証を実行する
  3. 起票結果返却を確認する
- 期待結果:
  - 会計伝票は起票されない
  - 起票結果は `PENDING_MASTER` または同等の保留/差戻し理由を返す
  - スクラッチ基幹の業務ステータスが `WAITING_ACCOUNTING_MASTER` になる
- 検証:
  - FI 起票件数確認
  - 起票結果 payload 確認
  - 基幹側保留状態確認

### TS-INT-FI-005 異常系: 勘定/取引先マッピング不備で起票差戻し

- 目的:
  - マスタ差分が送られても、FI 側の勘定・取引先・税区分マッピング不備を検知して差戻せることを確認する
- カバー BPMN ID:
  - `Task_Core_SendMasterDelta`
  - `Task_FI_ReceiveMasterDelta`
  - `Task_FI_ValidateMasterMapping`
  - `Task_FI_ReceiveAccountingEvent`
  - `Task_FI_SendPostingResult`
  - `Task_Core_ReceivePostingResult`
  - `Task_Core_UpdateBusinessStatus`
  - `MsgFlow_CoreToFI_MasterDelta`
  - `MsgFlow_CoreToFI_AccountingEvent`
  - `MsgFlow_FIToCore_PostingResult`
- 前提:
  - 送信される税コードまたは勘定コードが S/4HANA FI に存在しない
- 手順:
  1. 不正な会計マスタ差分を送信する
  2. 続けて会計仕訳イベントを送信する
  3. S/4HANA FI の検証結果を受信する
- 期待結果:
  - 起票結果が `REJECTED` になる
  - エラー内容に不足マスタが特定できる情報が含まれる
  - スクラッチ基幹の業務ステータスが `ACCOUNTING_ERROR` になる
- 検証:
  - エラーログ確認
  - 起票結果 payload 確認
  - 基幹側例外状態確認

### TS-INT-FI-006 異常系: 会計イベント重複送信時の冪等制御

- 目的:
  - 同一 `event_id` の再送が起きても S/4HANA FI が二重起票しないことを確認する
- カバー BPMN ID:
  - `Task_Core_SendAccountingEvent`
  - `Task_FI_ReceiveAccountingEvent`
  - `Task_FI_PostAccountingDocument`
  - `Task_FI_SendPostingResult`
  - `Task_Core_ReceivePostingResult`
  - `MsgFlow_CoreToFI_AccountingEvent`
  - `MsgFlow_FIToCore_PostingResult`
- 前提:
  - 同一 `event_id=EVT-AR-0002` を 2 回送れる
- 手順:
  1. 同一イベントを 2 回連続送信する
  2. S/4HANA FI の受信結果を確認する
  3. スクラッチ基幹へ返る起票結果を確認する
- 期待結果:
  - 会計伝票は 1 件しか生成されない
  - 2 回目は `DUPLICATE_IGNORED` または同等の結果になる
  - スクラッチ基幹側で二重完了にならない
- 検証:
  - FI 会計伝票件数確認
  - 重複排除ログ確認
  - 基幹側ステータス確認

### TS-INT-FI-007 異常系: 銀行明細が未照合で消込不能

- 目的:
  - 入金/支払明細の照合キーが不一致な場合に、未消込差異として返却されることを確認する
- カバー BPMN ID:
  - `Task_Bank_SendBankStatement`
  - `Task_FI_ReceiveBankStatement`
  - `Task_FI_ClearOpenItems`
  - `Task_FI_SendClearingResult`
  - `Task_Core_ReceiveClearingResult`
  - `Task_Core_UpdateARAPStatus`
  - `MsgFlow_BankToFI_BankStatement`
  - `MsgFlow_FIToCore_ClearingResult`
- 前提:
  - 銀行明細の照合キーが基幹側請求/支払依頼番号と一致しない
- 手順:
  1. 不一致な銀行明細を送信する
  2. S/4HANA FI で消込処理を実行する
  3. 消込結果を基幹へ返却する
- 期待結果:
  - 対象明細は未消込として残る
  - スクラッチ基幹の状態が `UNMATCHED_BANK_STATEMENT` になる
  - 未照合理由が返却 payload に含まれる
- 検証:
  - FI 未消込一覧確認
  - 基幹側例外状態確認
  - 消込結果 payload 確認

### TS-INT-FI-008 準正常: 部分入金により残額が残る

- 目的:
  - 部分入金時に一部消込と残額が正しく返却されることを確認する
- カバー BPMN ID:
  - `Task_Bank_SendBankStatement`
  - `Task_FI_ReceiveBankStatement`
  - `Task_FI_ClearOpenItems`
  - `Task_FI_SendClearingResult`
  - `Task_Core_ReceiveClearingResult`
  - `Task_Core_UpdateARAPStatus`
  - `MsgFlow_BankToFI_BankStatement`
  - `MsgFlow_FIToCore_ClearingResult`
- 前提:
  - 売掛残高 1,000,000 円に対して 600,000 円の入金明細を用意する
- 手順:
  1. 部分入金明細を送信する
  2. S/4HANA FI で部分消込を実行する
  3. 消込結果をスクラッチ基幹へ返却する
- 期待結果:
  - 消込結果が `PARTIAL_CLEARED` になる
  - 残額 400,000 円が基幹側に返る
  - スクラッチ基幹の債権状態が `PARTIALLY_CLEARED` になる
- 検証:
  - 残額確認
  - 基幹側残債権状態確認
  - 消込結果 payload 確認

### TS-INT-FI-009 異常系: 締め時点で未解決例外を含む月次レポート

- 目的:
  - 起票差戻しや未消込が残っている状態で、S/4HANA FI が月次レポートへ例外を反映し、経理が差異照合できることを確認する
- カバー BPMN ID:
  - `Task_FI_SendCloseReport`
  - `Task_Accounting_ReceiveCloseReport`
  - `Task_Accounting_ReconcileException`
  - `MsgFlow_FIToAccounting_CloseReport`
- 前提:
  - `TS-INT-FI-005` または `TS-INT-FI-007` の異常データが未解決で残っている
- 手順:
  1. 月次締め対象期間のレポート生成を実行する
  2. 経理部門でレポートを受領する
  3. 差異照合・調整判断を行う
- 期待結果:
  - レポートに起票エラー件数、未消込件数、差異一覧が含まれる
  - 経理部門が対象取引を特定できる
  - レポートに正常完了データと異常データが区別されている
- 検証:
  - 月次レポート内容確認
  - 経理照合ログ確認
  - 対象取引の追跡性確認

### TS-INT-FI-010 回復系: マスタ修正後の再送・再起票成功

- 目的:
  - 差戻し済みイベントに対し、マスタ修正後の再送で正常起票でき、締めレポートから例外が解消されることを確認する
- カバー BPMN ID:
  - `Task_Core_SendMasterDelta`
  - `Task_Core_SendAccountingEvent`
  - `Task_FI_ReceiveMasterDelta`
  - `Task_FI_ValidateMasterMapping`
  - `Task_FI_ReceiveAccountingEvent`
  - `Task_FI_PostAccountingDocument`
  - `Task_FI_SendPostingResult`
  - `Task_Core_ReceivePostingResult`
  - `Task_Core_UpdateBusinessStatus`
  - `Task_FI_SendCloseReport`
  - `Task_Accounting_ReceiveCloseReport`
  - `MsgFlow_CoreToFI_MasterDelta`
  - `MsgFlow_CoreToFI_AccountingEvent`
  - `MsgFlow_FIToCore_PostingResult`
  - `MsgFlow_FIToAccounting_CloseReport`
- 前提:
  - `TS-INT-FI-005` により差戻し済みのイベントがある
  - 欠落していた勘定/税/取引先マッピングを修正済み
- 手順:
  1. 修正版マスタ差分を再送する
  2. 同一業務取引に対する再送用会計イベントを送る
  3. S/4HANA FI で再起票する
  4. 次回月次レポートを生成する
- 期待結果:
  - 再起票が成功する
  - スクラッチ基幹の業務ステータスが `POSTED` に回復する
  - 月次レポートから当該起票エラーが除外される
- 検証:
  - 再起票ログ確認
  - 基幹側回復状態確認
  - 月次レポート差分確認

## 6. シナリオ別カバレッジマップ

| BPMN ID | カバーするシナリオ |
|---|---|
| `Task_Core_RecordTransaction` | `TS-INT-FI-001` |
| `Task_Core_SendMasterDelta` | `TS-INT-FI-001`, `TS-INT-FI-005`, `TS-INT-FI-010` |
| `Task_Core_SendAccountingEvent` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `Task_Core_ReceivePostingResult` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `Task_Core_UpdateBusinessStatus` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-010` |
| `Task_Core_ReceiveClearingResult` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `Task_Core_UpdateARAPStatus` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `Task_FI_ReceiveMasterDelta` | `TS-INT-FI-001`, `TS-INT-FI-005`, `TS-INT-FI-010` |
| `Task_FI_ValidateMasterMapping` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-010` |
| `Task_FI_ReceiveAccountingEvent` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `Task_FI_PostAccountingDocument` | `TS-INT-FI-001`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `Task_FI_SendPostingResult` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `Task_FI_ReceiveBankStatement` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `Task_FI_ClearOpenItems` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `Task_FI_SendClearingResult` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `Task_FI_SendCloseReport` | `TS-INT-FI-002`, `TS-INT-FI-009`, `TS-INT-FI-010` |
| `Task_Bank_ExecuteSettlement` | `TS-INT-FI-002`, `TS-INT-FI-003` |
| `Task_Bank_SendBankStatement` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `Task_Accounting_ReceiveCloseReport` | `TS-INT-FI-002`, `TS-INT-FI-009`, `TS-INT-FI-010` |
| `Task_Accounting_ReconcileException` | `TS-INT-FI-002`, `TS-INT-FI-009` |
| `MsgFlow_CoreToFI_MasterDelta` | `TS-INT-FI-001`, `TS-INT-FI-005`, `TS-INT-FI-010` |
| `MsgFlow_CoreToFI_AccountingEvent` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `MsgFlow_FIToCore_PostingResult` | `TS-INT-FI-001`, `TS-INT-FI-004`, `TS-INT-FI-005`, `TS-INT-FI-006`, `TS-INT-FI-010` |
| `MsgFlow_BankToFI_BankStatement` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `MsgFlow_FIToCore_ClearingResult` | `TS-INT-FI-002`, `TS-INT-FI-003`, `TS-INT-FI-007`, `TS-INT-FI-008` |
| `MsgFlow_FIToAccounting_CloseReport` | `TS-INT-FI-002`, `TS-INT-FI-009`, `TS-INT-FI-010` |

## 7. 収集すべき証跡

- スクラッチ基幹送信ログ
  - master delta payload
  - accounting event payload
  - correlation id
- S/4HANA FI 受信・起票証跡
  - 受信ログ
  - マッピング検証結果
  - 会計伝票番号
  - 起票エラー詳細
- 銀行・決済サービス証跡
  - bank statement payload
  - 決済完了タイムスタンプ
- 消込/支払証跡
  - clearing status
  - residual amount
  - unmatched reason
- 経理確認証跡
  - close report
  - 例外件数
  - 差異照合メモ

## 8. 補足

- このシナリオ集は `epic_flow.bpmn` の integration overview に対する統合テスト設計です。FEAT 単位の詳細 API/Batch テストへ落とす場合は、各 messageFlow をさらに interface contract test に分解してください。
- 業務 SoR と会計 SoR の境界が崩れていないかを毎シナリオで確認してください。特に、会計に不要な業務属性を S/4HANA 側に持ち込まないこと、逆に法定会計結果をスクラッチ基幹側で正本化しないことが重要です。
