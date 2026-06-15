# Final Phase（SAP 拡張）

> **Compaction re-read**: コンテキスト圧縮後、このファイルを再読み込みすること。
> Final Phase の SAP 固有エビデンスパック・Ops Pack・最終検証手順が記載されている。

---

## Step F-1: evidence_pack 完成

### 標準セクション

sdd_bootstrap.md の evidence_pack.md 標準構成に従い、以下を記載:
- AC coverage summary
- テスト結果サマリ（unit_test + gui_test）
- エビデンス HTML へのリンク

### ai_provenance セクション（SAP 拡張 MANDATORY）

evidence_pack に以下の `ai_provenance` セクションを追加:

```yaml
ai_provenance:
  agent: "Claude Code"
  model: "<使用モデル名>"
  session_id: "<セッション ID>"
  generated_files:
    - path: "src/<package>/<name>.clas.abap"
      action: "created"
    - path: "src/<package>/<name>.clas.testclasses.abap"
      action: "created"
  human_reviewed: false  # Final Gate 承認後に true に更新
  review_date: null      # Final Gate 承認日を記録
```

- AI が生成した全ファイルを `generated_files` に列挙
- `human_reviewed` は Final Gate 承認後に人間が true に変更

### test_green_confirmation（SAP 拡張）

```yaml
test_green_confirmation:
  unit_test:
    all_passed: true
    count: <テスト数>
  gui_test:
    all_passed: true
    count: <テスト数>
  all_passed: true        # unit_test.all_passed AND gui_test.all_passed の導出値
```

---

## Step F-2: Ops Pack 検証

`erp_addon_exec_tracking.py` を実行し、SAP 固有の運用追跡を検証:

```bash
python3 extensions/sap/tools/erp_addon_exec_tracking.py specs/<feature>/
```

### 検証内容

- TR 番号の記録完全性
- sap_objects の activate 状態
- テスト実行記録の完全性
- エビデンス取得記録の完全性

### Ops Pack 運用文書の検証

`scaffold/ops/` 配下の4文書が、プロジェクト固有の内容で記入されていることを確認:

| # | ファイル | 確認内容 |
|---|---------|---------|
| 1 | `ops/transport_manifest.yaml` | 移送ルート、TR 番号、依存関係が記入済み |
| 2 | `ops/release_checklist.md` | リリース手順の全ステップが記入済み |
| 3 | `ops/rollback_plan.md` | ロールバック手順（TR 取消、データ復旧）が記入済み |
| 4 | `ops/hypercare_runbook.md` | ハイパーケア期間の監視項目・連絡先が記入済み |

テンプレートのプレースホルダ（`<...>` / `""` / `TODO`）が残っていたら FAIL。

Ops Pack 検証 PASS → Step F-3 に進行。
FAIL → 欠落項目を補完して再実行。

---

## Step F-3: stride pr-check 7/7

```bash
sdd-templates/bin/stride pr-check <project_root>
```

7 つの base check が全て PASS であること:

| # | Check | 確認内容 |
|---|-------|---------|
| 1 | stride-lint | lint エラーなし |
| 2 | spec:drift | spec と実装の乖離なし |
| 3 | tests | 全テスト GREEN |
| 4 | coverage | カバレッジ基準充足 |
| 5 | walkthrough | walkthrough.md 存在・完全性 |
| 6 | evidence | エビデンスパック完全性 |
| 7 | TODO | 未解決 TODO なし |

7/7 PASS → Step F-4 に進行。
いずれか FAIL → 該当項目を修正して再実行（最大 3 回、以降人間に報告）。

---

## Step F-4: Final Gate 承認

```
Final Gate の承認をお願いします。
APPROVAL.md の「Final Gate」セクションで:
  1. チェックボックスを [x] に変更
  2. 承認者名と日付を記入
してください。
```

- 人間が APPROVAL.md を編集するまで待機
- 承認後: `state.yaml` の status を `done` に更新
- 承認後: evidence_pack の `ai_provenance.human_reviewed` を `true` に更新（人間が実施）

---

## 承認済み成果物の変更ルール

本 Phase の作業中に、先行 Gate で承認済みの成果物を修正する必要が生じた場合:
1. `implementation-details/change_log.md` に変更内容・理由・影響範囲を記録する
2. 意味的変更（要件追加・削除等）の場合は人間に再承認を相談する
3. フォーマット修正のみ（lint 準拠等）の場合は change_log 記録のみで続行可

**change_log を記録せずに承認済み成果物を変更してはならない。**

---

## 参照

- `agent_docs/sdd_bootstrap.md` §5（タスク完了チェックリスト）
- `CLAUDE_WORKFLOW_SAP.md` Final セクション
- `agent_docs/testing_sap.md`（エビデンス取得詳細）
