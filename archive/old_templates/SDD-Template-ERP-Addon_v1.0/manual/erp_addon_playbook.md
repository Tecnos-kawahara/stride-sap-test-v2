# ERPアドオン向け SDD-Template Playbook（Tecnos版）

## 0. 目的
ERPアドオン（既存ERPへの拡張・改修）を、**Spec（契約）を唯一の真実**として、AI実装を安全にスケールさせる。
- 変更が連鎖するERPの現実に合わせ、**Run/State/Mode**で「実行」を追跡する
- 既存の**Gate 1〜Final**を維持し、監査・合意形成を壊さない

## 1. 基本原則（3つ）
1) Spec is canonical: 仕様（Spec）が契約。実装と食い違う場合は「どちらを直すか」を意思決定し、必ず差分として残す  
2) Artifacts = State: 会話ではなく成果物（Spec/Run/State）が唯一の状態  
3) AI proposes, human validates: 承認は必ず人、AIは提案と実行を担当  

## 2. 全体構造（Macro Gate × Micro Run）
- Macro: Gate 1〜Final（仕様パックの完成・監査パックの完成）
- Micro: Work Item / Run（変更単位の実行追跡）

## 3. ディレクトリ標準
- specs/<feature>/ : 機能（アドオン単位）の仕様パック
- specs/<feature>/work_items/ : 変更単位（Work Item）
- specs/<feature>/runs/ : 実行ログ（Run）
- specs/<feature>/state/state.yaml : 進捗の単一真実
- specs/<feature>/ops/ : ERP運用パック（輸送/ロールバック/検証/監視）

## 4. Gate定義（温存＋ERP向けの追加DoD）
- Gate 1: basic_design.md（目的/範囲/統合点/トレース）
- Gate 2: process.bpmn（業務プロセス＋入出力）
- Gate 3: spec.md（AC/NFR/タグ付きAC）
- Gate 4: plan.md（Contracts/Tests/Coverage policy）
- Gate 5: tasks.md（タスク定義）＋ Work Item化（WI/Mode/State初期化）
- Final: evidence_pack.md（CI結果/Run索引/運用パック）

## 5. Mode（Run単位の可変儀式）
- autopilot: 0 checkpoint（事後にwalkthrough review必須）
- confirm: 1 checkpoint（実行前にplan review）
- validate: 2 checkpoints（design diff review + plan review、必要ならops review）

## 6. 典型運用（おすすめ）
1) SIMPLEで specパック骨子（requirements/design/tasks相当）を短時間で作る
2) Gate 1〜4を確定（顧客・業務合意）
3) Gate 5で Work Item分割、Mode付与、State初期化
4) Runを回す（walkthrough + CI + State更新）
5) Finalで監査パック化（evidence + ops + run index）

## 7. ERP特有の注意
- 権限/SoD/会計計算/在庫評価/更新系IF/移行/輸送 は基本 validate 扱い
- “Spec=正”を絶対視せず、brownfieldでは「現行=観測、Spec=契約」として差分を管理

このPlaybookに対応するテンプレは `sdd-templates/` 以下に格納。
