# SAP 拡張 バージョン更新チェックリスト (v2)

本ドキュメントはテンプレート保守者がSAP拡張パックを更新する際のチェックリストです。
対象: SAP 拡張パック v2.0.0 (STRIDE v6.0.0+)。

関連ドキュメント:
- [SAP_TOOL_DEVELOPMENT_GUIDE.md](SAP_TOOL_DEVELOPMENT_GUIDE.md) -- ツール開発手順
- [migration_from_v1.md](migration_from_v1.md) -- v1 からの移行情報
- [SAP_TROUBLESHOOTING.md](SAP_TROUBLESHOOTING.md) -- トラブルシューティング

---

## 1. 更新前チェック

### 1.1 MANIFEST.yaml の確認

`MANIFEST.yaml` に記載されたファイル一覧（tools, config, templates, scaffold, agent_docs）が、
実際のファイル構成と一致しているか確認する。

```bash
# 変更ファイルがすべてテンプレートファイルか確認
git diff <base-branch>...HEAD --stat
```

**確認項目:**
- [ ] 新規追加したファイルが `MANIFEST.yaml` の該当セクションに追記されているか
- [ ] 削除したファイルが `MANIFEST.yaml` から除去されているか
- [ ] `MANIFEST.yaml` の `manifest_version` / `extension.version` が更新されているか
- [ ] 成果物ディレクトリ（`specs/`, `epics/`, `.tool_evidence/`, `src/`）がコミットに含まれていないか

### 1.2 ブランチ運用

- [ ] 作業ブランチで変更を行っているか（main への直接コミット禁止）
- [ ] `.env` ファイルがコミットに含まれていないか

---

## 2. ワークフロードキュメント変更時

v2 では Phase 別ドキュメント（`agent_docs/phase*.md`）にワークフロー手順が分離されている。
モノリシックなワークフロー文書は存在しない。

### 2.1 ステップ ID の変更

ステップ ID（`1-A1`, `2P-B1`, `2-D3`, `4-A1`, `5-B2` 等）を変更した場合、以下のすべてを更新する。

- [ ] `extensions/sap/MANIFEST.yaml` -- `phase_steps` セクション内の全 `id` フィールド
- [ ] `extensions/sap/CLAUDE_SAP.md` -- ルール参照、ステップ参照テーブル
- [ ] `extensions/sap/CLAUDE_WORKFLOW_SAP.md` -- Phase 概要、参照テーブル
- [ ] `extensions/sap/agent_docs/phase1_design.md` -- Phase 1 手順内のステップ ID
- [ ] `extensions/sap/agent_docs/phase2_pre_sap_context.md` -- Phase 2 前準備手順内のステップ ID
- [ ] `extensions/sap/agent_docs/phase2_specify.md` -- Phase 2 手順内のステップ ID
- [ ] `extensions/sap/agent_docs/phase3_tasking.md` -- Phase 3 手順内のステップ ID
- [ ] `extensions/sap/agent_docs/phase4_execute.md` -- Phase 4 手順内のステップ ID
- [ ] `extensions/sap/agent_docs/phase_final.md` -- Final 手順内のステップ ID
- [ ] `extensions/sap/config/tool_evidence_registry.yaml` -- 全ステップの `step_id` フィールド
- [ ] `extensions/sap/tools/*.py` -- 各ツールの Usage/help テキスト内のステップ ID 参照
- [ ] `extensions/sap/tools/*.js` -- 各ツールのバナー/コメント内のステップ ID 参照
- [ ] `extensions/sap/templates/*.md` -- テンプレート内のステップ参照
- [ ] `extensions/sap/docs/*.md` -- ドキュメント内のステップ参照

**検索コマンド:**
```bash
# 旧ステップ ID の残存を検索
grep -r "旧ステップID" extensions/sap/
```

### 2.2 Phase 別ドキュメントの変更

Phase 別ドキュメント（`agent_docs/phase*.md`）の内容を変更した場合:

- [ ] `CLAUDE_WORKFLOW_SAP.md` の Phase 概要・参照テーブルと整合しているか
- [ ] `CLAUDE_SAP.md` のルール（S1--S7）との矛盾がないか
- [ ] `MANIFEST.yaml` の `agent_docs` セクションの `description` / `load_timing` が正しいか
- [ ] `MANIFEST.yaml` の `phase_steps` セクションの `doc_ref` アンカーがドキュメント内の見出しと一致するか
- [ ] 補助文書（`testing_sap.md`, `conventions_sap.md`, `error_recovery_sap.md`）への参照が正しいか

---

## 3. 設定ファイル変更時

### 3.1 common_class_rules.yaml

- [ ] 新規ルールの `id` が既存ルールと重複していないか
- [ ] `trigger_pattern` が正規表現として有効か
- [ ] `forbidden_patterns` が実際の ABAP ソースパターンと一致するか
- [ ] `sap_common_class_lint.py` で正しく検出されるか検証

### 3.2 quality_score_config.yaml

- [ ] スコア閾値の変更が妥当か（デフォルト: 85）
- [ ] 新規チェック項目の重み付けが適切か
- [ ] 減点ルール（QR-01--QR-14）の ID 採番に欠番・重複がないか

### 3.3 test_perspective_master.yaml

- [ ] 新規 processing_type が追加されている場合、対応する test_perspective が定義されているか
- [ ] test_suggest_config.yaml との整合性が保たれているか

### 3.4 tool_evidence_registry.yaml

- [ ] 新規ツールが正しいフェーズ・ステップに登録されているか
- [ ] `optional` フラグが正しく設定されているか
- [ ] `tool` フィールドが `MANIFEST.yaml` の tools セクション内のツール名と一致しているか

### 3.5 tag_branch_rules.yaml

- [ ] 新規タグパターンの `tag` が既存パターンと重複していないか
- [ ] `branch_logic` の定義が `sap_path_enumerator.py` で正しく解釈されるか
- [ ] `sap_scenario_generator.py` が新規パターンからシナリオを生成できるか検証
- [ ] `agent_docs/phase2_specify.md` のパス列挙手順と整合しているか

### 3.6 test_suggest_config.yaml

- [ ] test_perspective_master.yaml との整合性が保たれているか
- [ ] テスト提案ルールが現行の Phase 2 シナリオ設計ルールと矛盾しないか

---

## 4. ツール変更時

### 4.1 Python ツールの変更 -- ValidatorContext 方式 (validators)

v2 の validators は `ValidatorContext` を受け取り `ValidationResult` を返す。
stride_lint から動的にロードされ、スタンドアロン実行はしない。

- [ ] `ValidatorContext` を正しく受け取っているか（`ctx.feature_dir`, `ctx.spec`, `ctx.plan` 等）
- [ ] `ValidationResult` を返しているか（`errors`, `warnings` のリスト形式）
- [ ] `MANIFEST.yaml` の `tools.validators` に `trigger` / `severity` が正しく設定されているか
- [ ] 既存の validator との重複チェック（同じ検証を二重実行していないか）
- [ ] Windows 環境でのエンコーディング問題がないか（cp932 対応）

### 4.2 Python ツールの変更 -- CLI 方式 (utilities)

- [ ] `argparse` で適切な引数定義がされているか
- [ ] `--step-id` 引数を受け付けるか（エビデンス記録が必要な場合）
- [ ] `tool_evidence_writer` でエビデンスを出力しているか（必要な場合）
- [ ] `sys.exit(1)` でエラー終了しているか
- [ ] Windows 環境でのエンコーディング問題がないか（cp932 対応）

### 4.3 Node.js ツールの変更 (sap_operations)

- [ ] `.env` バリデーション（SAP 接続情報の検証）が含まれているか
- [ ] エラー時に `process.exit(1)` で終了しているか
- [ ] `--step-id` と `--feature-dir` オプションを受け付けるか
- [ ] `abap-adt-api` の API 変更に対応しているか
- [ ] `MANIFEST.yaml` の `tools.sap_operations` に `authority`（gated / conversational）が正しく設定されているか

### 4.4 依存関係の更新

- [ ] `extensions/sap/package.json` の依存バージョンが更新されているか
- [ ] `npm install` 後に全ツールが動作するか検証
- [ ] Python の追加依存がある場合、ドキュメントに記載されているか

---

## 5. テンプレート変更時

### 5.1 テンプレートファイルの変更

v2 では「完成版方式」（substitutions）を採用し、SAP 拡張 ON 時に標準テンプレートを差し替える。

- [ ] テンプレートの YAML 構造変更が、対応する validator の検証ロジックと整合しているか
- [ ] `MANIFEST.yaml` の `templates.substitutions` の `source` パスが正しいか
- [ ] `MANIFEST.yaml` の `templates.partial_templates` が正しいか（contracts, tests）
- [ ] Gate Check ルール（最小値チェック）が適切か
- [ ] scaffold ファイルの変更が `stride init` 後のファイル構造と整合するか

### 5.2 scaffold ファイルの変更

- [ ] `MANIFEST.yaml` の `scaffold.files` に新規ファイルが記載されているか
- [ ] `scaffold.inject` のコピー先パスが正しいか
- [ ] `state/state.yaml` の初期構造が Phase 1 の期待と整合しているか

### 5.3 共通クラス・共通 Include の追加

- [ ] `config/common_class_rules.yaml` にルール定義が追加されているか
- [ ] `agent_docs/conventions_sap.md` にクラスの使用方法が記載されているか

---

## 6. MANIFEST.yaml 更新時

MANIFEST.yaml は v2 のメタ定義の中心。変更時は以下を確認する。

### 6.1 validators セクション

- [ ] `name` がツールファイルのベースネームと一致しているか
- [ ] `path` が実在するファイルを指しているか
- [ ] `trigger` が正しい Phase を指しているか（`phase:design`, `phase:specify`, `phase:execute`, `phase:final` 等）
- [ ] `severity` が適切か（`error` / `warning`）
- [ ] `description` に検証 ID（C1--C8 等）が記載されているか

### 6.2 tools -- utilities / mapping_refs / sap_operations

- [ ] utilities の `trigger` が正しいか（`manual` / `phase:*`）
- [ ] sap_operations の `authority` が正しいか（`gated` = 承認必要、`conversational` = 自由実行）
- [ ] mapping_refs の `detail_ref` が詳細仕様書の正しいセクションを指しているか

### 6.3 phase_steps セクション

- [ ] 全 Phase（design, sap_context, specify, tasking, execute, final）のステップが網羅されているか
- [ ] `tool` フィールドが `tools` セクション内の `name` と一致しているか（null 以外の場合）
- [ ] `type` が正しいか（`workflow` / `validator` / `utility`）
- [ ] `doc_ref` のアンカーが `agent_docs/phase*.md` 内の実際の見出しと一致するか

### 6.4 agent_docs セクション

- [ ] `load_timing` が正しいか（`bootstrap` / `phase:*`）
- [ ] `path` が実在するファイルを指しているか
- [ ] 新規 agent_docs を追加した場合、`CLAUDE_WORKFLOW_SAP.md` の参照テーブルも更新されているか

### 6.5 config / templates / scaffold セクション

- [ ] `config` の `path` が実在するファイルを指しているか
- [ ] `templates.substitutions` の `source` が実在するファイルを指しているか
- [ ] `scaffold.files` のパスが実在するファイルを指しているか

---

## 7. ドキュメント変更時

### 7.1 相互参照の整合性

- [ ] ドキュメント間のリンク（`[text](file.md)`）が正しいか
- [ ] `CLAUDE_WORKFLOW_SAP.md` の参照テーブルに新規 agent_docs が記載されているか
- [ ] `CLAUDE_SAP.md` のルール番号（S1--S7）に欠番・重複がないか

### 7.2 Phase 別ドキュメント間の整合性

- [ ] Phase 間の入出力（前 Phase の成果物 = 次 Phase の入力）が正しく記述されているか
- [ ] 補助文書（testing_sap, conventions_sap, error_recovery_sap, codegen_sap）との矛盾がないか

---

## 8. 更新後の検証

### 8.1 Level 1: 静的チェック

```bash
# 旧ステップ ID / 旧パスの残存チェック
grep -r "旧ID" extensions/sap/

# YAML 構文チェック（全設定ファイル）
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/config/common_class_rules.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/config/quality_score_config.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/config/test_perspective_master.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/config/tool_evidence_registry.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/config/tag_branch_rules.yaml'))"
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/config/test_suggest_config.yaml'))"

# MANIFEST.yaml 自体の構文チェック
python3 -c "import yaml; yaml.safe_load(open('extensions/sap/MANIFEST.yaml'))"

# MANIFEST.yaml 内のパス実在チェック
python3 -c "
import yaml, os
m = yaml.safe_load(open('extensions/sap/MANIFEST.yaml'))
base = 'extensions/sap'
for cat in ['validators','utilities','sap_operations']:
    for t in m.get('tools',{}).get(cat,[]):
        p = os.path.join(base, t['path'])
        if not os.path.exists(p): print(f'MISSING: {p}')
for d in m.get('agent_docs',[]):
    p = os.path.join(base, d['path'])
    if not os.path.exists(p): print(f'MISSING: {p}')
for c in m.get('config',[]):
    p = os.path.join(base, c['path'])
    if not os.path.exists(p): print(f'MISSING: {p}')
print('Path check complete')
"
```

### 8.2 Level 2: ツール単体テスト

- [ ] validators: stride_lint 経由で実行し、`ValidationResult` が正しく返るか確認
- [ ] utilities: 各ツールを `--help` で実行し、引数パースが正しいか確認
- [ ] sap_operations: `.env` 設定後に接続テスト（`node tools/read.js --help`）

### 8.3 Level 3: 通しフロー検証

テスト用 feature（`specs/test_*`）で Phase 1 → Phase 2 前準備 → Phase 2 → Phase 3 → Phase 4 → Final の通しフローを実行し、全ステップがエラーなく完了することを確認。

- [ ] Phase 1: yaml → basic_design 転記 + validators（C1, C2）が PASS
- [ ] Phase 2 前準備: SAP 実機接続 + sap_context 記録 + validators（C4, C5）が PASS
- [ ] Phase 2: spec/plan/contracts/scenarios 生成 + validators（C3, C6, C7, C8, D1--D4）が PASS
- [ ] Phase 3: tasks.md 生成
- [ ] Phase 4: WI 実装 + 品質チェック（B1--B4）が PASS
- [ ] Final: エビデンス収集 + 最終検証（A1, A2, B1--B3）が PASS

### 8.4 Level 4: エビデンス整合性

- [ ] `.tool_evidence/` ディレクトリに全必須ステップのエビデンスが生成されているか
- [ ] `tool_evidence_registry.yaml` に登録された全 non-optional エントリに対応するエビデンスがあるか
- [ ] `evidence_merge_report` で統合レポートが正常に生成されるか
