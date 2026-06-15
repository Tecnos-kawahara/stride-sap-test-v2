# 02. SDD とテクノス既存フォーマット（SAPアドオン）の比較ガイド

本書は、テクノス既存フォーマット「アドオン設計書（基本・詳細）」と、SDD（Specification-Driven Development）テンプレートの違いを、SAPインプリ（Z開発/アドオン）実務の用語に寄せて整理したものです。

---

## 1. まず押さえる根本の違い

### 1) 正本の位置づけ
- **テクノス既存フォーマット**: 設計書が正本、実装はその写像。レビューは人手中心。
- **SDD**: **Specが正本**（`basic_design.md` → `process.bpmn` → `spec.md` → `plan.md` → `tasks.md`）。Enterprise では Epic overview を `epic_flow.bpmn` で併用。コードは生成物として扱い、**lintとGateで機械検証**。

### 2) 進行管理
- **テクノス既存フォーマット**: 文書完了・レビュー・承認の人手運用が中心。
- **SDD**: **Phase Gate**と`APPROVAL.md`で承認を記録。`stride-lint`が通らない限り次フェーズに進めない。

### 3) 機械可読な仕様
- **テクノス既存フォーマット**: 文章や図が中心。
- **SDD**: **Spec-as-Code**（OpenAPI/移行マッピング/権限マトリクス/テストシナリオなど）を機械可読で保持。

### 4) テストと証跡
- **テクノス既存フォーマット**: テストは別紙／後工程で計画されがち。
- **SDD**: **AC→TSのトレーサビリティとCoverage Policy**が必須。Evidence PackにCI/SAST/SCA/Secrets/AIプロヴェナンスを記録。

---

## 2. 補足: SDD用語ミニ辞典（まずここだけ）

- **Canonical YAML**: 各ドキュメント先頭のYAMLブロック（`#0`や`#1`）。ここが正本で、説明文は補助。まずYAMLを更新し、`stride-lint`の提案（COUNTS_SUGGESTION）で整合を取る。
- **`stride-lint`**: SDD専用の構文・参照・カバレッジ検証。通らない限り次フェーズに進めない。
- **Phase Gate / `APPROVAL.md`**: 進行管理の関門。人間承認のみ有効で、AIは編集禁止。
- **Spec-as-Code**: OpenAPI/権限マトリクス/移行マッピング/テストシナリオなどを機械可読で保持し、検証可能にする考え方。
- **Evidence Pack**: CI結果・テストレポート・SAST/SCA・Secrets検査・AIプロヴェナンスをまとめた監査証跡。
- **AIプロヴェナンス**: 生成時のモデル/プロンプト/入力ハッシュ等の記録。監査・説明責任のために必須。
- **Coverage Policy**: ACカバレッジ100%、CTカバレッジ原則100%、コードカバレッジ目標値を明文化し、機械検証する方針。
- **AC / TS / CT**: Acceptance Criteria / Test / Contract。IDでトレースし、**AC→TS**、**CT→TS-CON** の関係を強制する。
- **Tagged AC（integration/e2e）**: ACにタグを付け、対応するテスト種別（TS-INT/TS-E2E）で必ずカバーする。
- **Artifact Registry**: 成果物の唯一正本リスト。作成物が多いSAP案件で「正本の場所」を明確にする。
- **RACI+**: Human/AI/CIを含む責任分界。AIはAccountableになれない。
- **BPMN（Camunda 8準拠）**: フローの機械可読正本。SDDのトレーサビリティ起点になる。

---

## 3. ドキュメント対応表（テクノス既存フォーマット → SDD）

| テクノス既存フォーマット | 目的 | SDDでの置き場 |
|---|---|---|
| 文書情報・変更履歴 | ドキュメント管理 | `APPROVAL.md`（人手承認）＋各ファイルのfrontmatter |
| 目的/背景・対象範囲 | 企画/背景 | `basic_design.md` の `context` / `scope` |
| RICEFW分類 | 方式分類 | `basic_design.md` または `spec.md` に明記（分類は任意） |
| 処理概要＋フロー図 | 業務フロー | `process.bpmn`（Feature 実装フロー）＋ `basic_design.md` の `integration_flows`。チーム間/システム間は `epic_flow.bpmn` |
| 入出力一覧 | IFの概要 | `spec.md` の `spec_as_code` と `plan.md` の `contracts` |
| 権限要件 | 認可/SoD | `spec.md` の `security_privacy` + `implementation-details/authz_matrix.yaml` |
| 性能・ロック・コミット方針 | 非機能要件 | `spec.md` の NFR（performance/data/ops） |
| メッセージ一覧 | エラー設計 | `plan.md` の contracts／必要なら `implementation-details/` |
| 画面設計・項目定義 | UI仕様 | `spec.md` の AC／必要に応じて `implementation-details/` |
| 処理詳細（BAPI/ENQUEUE等） | 技術設計 | `plan.md`（HOW）＋詳細は `implementation-details/` |
| DB参照/構造 | データ仕様 | `contracts/database_schema.yaml` + `implementation-details/migration_mapping.yaml` |
| テスト観点/ケース | テスト設計 | `spec.md` の AC と `plan.md` の `test_strategy`、`tests/scenarios.yaml` |
| 運用・移送 | 運用/手順 | `implementation-details/ops.md`（必要時） |

> ポイント: **テクノス既存フォーマットの「詳細設計」に含まれていた内容は、SDDでは `plan.md` と Spec-as-Code に分散される**。

---

## 4. SAP用語の読み替え（現場用語に合わせた表現）

| SAP/旧来の呼称 | SDDでの相当 | 補足 |
|---|---|---|
| 基本設計（機能仕様） | `basic_design.md` | 目的/背景/範囲/統合フローの正本 |
| 詳細設計（技術仕様） | `plan.md` + `implementation-details/` | 実装方針・依存・技術判断の置き場 |
| IF定義（BAPI/IDoc/FILE等） | `plan.md` の `contracts` + `contracts/` | CT-API/CT-IDOC/CT-FILE/CT-BATCHとして管理 |
| 画面設計/ALV/Forms | `spec.md` のAC + `implementation-details/` | UI期待結果はAC、レイアウトは補助資料 |
| 権限設計（PFCG/権限オブジェクト） | `implementation-details/authz_matrix.yaml` | `spec.md` の security に要件化 |
| ジョブ/バッチ運用 | `plan.md` + `implementation-details/ops.md` | スケジュール/監視/再実行を明文化 |
| 移送（CTS）/導入 | `implementation-details/ops.md` + Evidence Pack | 実施手順と証跡を分離管理 |
| 開発オブジェクト一覧 | `memory/artifact_registry.md` | 成果物の唯一正本リスト |

> RICEFW分類は、必要に応じて `basic_design.md` / `spec.md` に明記します（分類よりも契約・フローを重視）。

---

## 5. SAPインプリ視点の違い（実務での影響）

### 1) BAPI/IDoc/EDI/FILEの扱い
- **テクノス既存フォーマット**: 処理詳細に仕様として混在。
- **SDD**: **契約（CT-API/CT-IDOC/CT-EDI/CT-FILE/CT-BATCH）として明文化**し、`plan.md` と `contracts/` に分離。

### 2) 権限とSoD
- **テクノス既存フォーマット**: 権限要件として本文に書く。
- **SDD**: `spec.md` の security で要件化し、**`authz_matrix.yaml` を機械可読で保持**。SoD（職務分掌）を監査要件として明示。

### 3) 監査・証跡
- **テクノス既存フォーマット**: 監査要件は本文に記述。
- **SDD**: **Evidence Pack**としてCI/テスト/SAST/SCA/AIプロヴェナンスを保存し、監査観点を運用に組み込む。

### 4) テストの位置づけ
- **テクノス既存フォーマット**: テスト設計は後工程になりやすい。
- **SDD**: **AC→TSの完全トレースが必須**。Integration/E2Eはタグ管理し、`stride-lint`で強制。

---

## 6. SE向け: 変わらなくてはいけない理由

### 1) 統合の複雑化で「漏れ」が起きやすい
- SAPはBAPI/IDoc/FILE/EDIなど**複数の契約が並走**するため、文書だけだとIF漏れや前提ズレが起きやすい。
- SDDは**契約（CT-*)とテスト（TS-*）を必須化**し、機械的に漏れを検出できる。

### 2) 後工程の手戻りコストが大きすぎる
- 仕様と実装のズレは、結合・総合・ユーザー検証で発覚すると修正コストが大きい。
- SDDは**Spec→Plan→Tasksで段階的に固定**し、`stride-lint`で早期に差分を発見する。

### 3) 監査・証跡要求が年々厳しくなる
- 監査ログ、SoD、権限管理は「書いただけ」では不十分になっている。
- SDDは**Evidence Pack**として、CI/テスト/SAST/SCA/AIプロヴェナンスを保存し、説明責任を担保する。

### 4) 人手レビューだけでは限界がある
- 人手レビューは属人化・抜け漏れが避けられない。
- SDDは**LintとGateで機械的にチェック**し、レビューを「判断」に集中させる。

### 5) AI/自動化時代に対応するため
- 今後はAI支援や自動生成が前提になるが、**検証ルールがなければ品質が揺らぐ**。
- SDDはSpec-as-CodeとGateで**AIの出力を制御可能**にする。

---

## 7. SEが実際に変わるポイント

| 従来のやり方 | SDDでのやり方 | 変える理由 |
|---|---|---|
| 設計書中心 | Canonical YAML中心 + Lint | 機械検証で漏れ防止 |
| 詳細設計に実装情報を集約 | `plan.md` と `implementation-details/` に分割 | 仕様と実装の責務分離 |
| テストは後工程で整理 | AC→TSを最初に定義 | 手戻り抑制と網羅性確保 |
| 承認は文書レビュー中心 | Gateと`APPROVAL.md`で段階承認 | 進行管理の明確化 |
| 承認後に文書を修正しがち | 変更は再承認 | 改訂履歴と監査の担保 |

### 変わらないこと
- SAPの業務知識、BAPI/IDoc/ALV等の専門知識は**これまで通り必須**。
- 要件を整理し、業務を理解し、関係者調整する役割は**むしろ重要性が増す**。

---

## 8. 具体例: BAPI/IDoc/ALV/ENQUEUE の落とし込み

- **BAPI/RFC呼び出し**  
  - テクノス既存フォーマット: 詳細設計に引数・戻り値・例外を記述  
  - SDD: `plan.md` の `contracts.apis_events` に CT-API を定義し、詳細は `contracts/` に明文化。テストは TS-CON/TS-INT でカバー。

- **IDoc連携（Inbound/Outbound）**  
  - テクノス既存フォーマット: IDocセグメント定義・マッピングを本文で管理  
  - SDD: CT-IDOC として `contracts/` に構造定義、`implementation-details/migration_mapping.yaml` にマッピング。統合テストで検証。

- **ALV/帳票（Spool/Forms含む）**  
  - テクノス既存フォーマット: 帳票レイアウト/項目定義を設計書本文で管理  
  - SDD: 期待結果は `spec.md` の AC に明記し、レイアウトは `implementation-details/` に補助資料として保持。外部出力がある場合は CT-FILE として契約化。

- **ENQUEUE/ロック方針**  
  - テクノス既存フォーマット: 詳細設計に排他設計を記載  
  - SDD: 競合/整合性要件を `spec.md` の NFR（data/availability）に落とし、実装方針は `plan.md` に記載。

---

## 9. テクノス既存フォーマットの項目をSDDに落とすときの実務ルール

1. **機能概要・背景・範囲**  
   - `basic_design.md` の `context` と `scope` に記載。

2. **フロー図**  
   - Feature 実装フローは `process.bpmn` を正本にする（Camunda 8準拠）。  
   - 複数チーム/システムの受け渡し概観は `epic_flow.bpmn` に切り出す。

3. **詳細設計（BAPI/ENQUEUE/SQL等）**  
   - `plan.md` に「方針」と「依存」を書く。  
   - 実装寄りの詳細は `implementation-details/` に退避。

4. **権限・監査・運用**  
   - `spec.md` の NFR（security_privacy / operations）に要件化。  
   - `authz_matrix.yaml` と `ops.md` を使う。

5. **テストケース**  
   - `spec.md` の AC を起点に `plan.md` の `test_strategy` で分解。  
   - シナリオは `tests/scenarios.yaml` に落とす。

---

## 10. まとめ（違いを一言で）

- **テクノス既存フォーマット**: 「設計書が正本、人手レビューが中心」
- **SDD**: 「**Specが正本、Gateと機械検証で進行制御**」

SAPインプリの強み（契約/監査/運用/SoD）を生かすために、SDDは **仕様を機械可読で固定し、品質ゲートで漏れを潰す設計**になっています。
