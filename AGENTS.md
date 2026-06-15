# AGENTS.md
# Operating Model: Spec-Driven Development (SDD) - Tecnos-STRIDE v5.3.2

## ⛔ STOP — Read This First (MANDATORY)

**このプロジェクトは SDD (Spec-Driven Development) で開発する。**
**コードを1行も書く前に、必ず `agent_docs/sdd_bootstrap.md` を読み、SDD フローに従うこと。**

## Instruction Precedence (AI が literal に従う順序)

矛盾時は上位を優先する。例: ユーザーレベルの「Parallel Everything」はこのプロジェクトでは Phase Gate 優先で制約される。

```
1. memory/tecnos_org_constraints.md          # 組織 INVIOLABLE 制約
2. memory/constitution.md                     # 憲法（14 Articles, Gates）
3. agent_docs/sdd_bootstrap.md                # SDD 実行 SSoT（このプロジェクトの第一読本）
4. AGENTS.md（このファイル、プロジェクト）    # プロジェクト運用ルール
5. SDD_MANIFESTO.md                           # ツール非依存 SDD コア
6. CLAUDE_WORKFLOW.md                         # Codex 固有補足のみ
7. agent_docs/sdd_guidelines.md               # 詳細ガイドライン
8. agent_docs/commands.md                     # CLI リファレンス
9. ユーザーレベル AGENTS.md（~/AGENTS.md 等） # 汎用ルール。SDD Phase Gate と矛盾時は SDD 側優先
10. その他 plugins / skills                   # 個別指示
```

**衝突例の解決指針 (Opus 4.7 向け明示):**
- 「Parallel Operations: ALL related operations in ONE message」(user-level) vs SDD Phase 順序実行
  → SDD Phase 内での並列化は OK（例: ファイル読取/lint 並列）。**Phase を跨ぐ並列化は禁止**。
- 「Batch Everything」 vs Phase Gate 単位停止
  → Phase 内の小ステップは連続実行 OK。**Gate 承認待ちは必ず停止**。
- 「NEVER save to root folder」 vs AGENTS.md/SDD_MANIFESTO.md 等のルートファイル
  → このプロジェクトのルート直下ガバナンスファイル (Codex*.md, SDD_*.md, SYMPHONY.md, README.md, pyproject.toml 等) は**既存として保護**、新規はルート禁止を維持。
- 「Test-first development」(user-level) vs SDD Phase 3 で tasks/tests 作成
  → SDD では spec.md で AC → scenarios.yaml → tests と先に定義する。この「Spec-first-before-code」を Test-first と解釈する。Phase 4 直前にテスト骨格を確定し、Phase 4 で実装と並行して通す。

いきなりコードを書き始めてはいけない。SDD では以下の順序で進める：

```
1. Design Phase:  basic_design.md + process.bpmn 作成 → Gate 1,2 承認
2. Specify Phase: spec.md + plan.md + contracts/ 作成 → Gate 3,4 承認
3. Tasking Phase: tasks.md 作成 → Gate 5 承認
4. Execute Phase: Work Item 単位で実装 → WI 承認
5. Final:         Evidence Pack + PR Readiness Check → Final 承認
```

**仕様（Spec）が契約。コードは生成物。承認なしに次のPhaseに進んではならない。**

## Bootstrap

**`agent_docs/sdd_bootstrap.md` を読むこと。** このファイルに全必須ルールが集約されている：
- 実行モデル（AI = 実行者、人間 = 承認者）
- Phase Gate ルール
- 品質基準
- コマンド一覧

## Execution Model (v4.4 + v4.6 Schema-Gated)

**Codex = 実行者 (R)** | **人間 = 承認者 (A)**

- Codex が全作業を**自律実行**する（init, lint, テスト, Evidence, 自動修正）
- 人間は APPROVAL.md の編集と業務判断のみ
- **APPROVAL.md / EPIC_APPROVAL.md / WI-*.approval.md を AI が編集することは絶対禁止**

### AI Action Boundary (v4.6 Execution Authority)

| 分類 | AI の権限 | 例 |
|------|----------|----|
| **MUST DO** | 承認不要で実行 | stride-lint 実行、lint FAIL 自動修正（APPROVAL_PENDING 除く）、placeholder 置換、canonical YAML 修正、ファイル作成（現在の Phase に許可された範囲内）、spec↔contracts↔code の整合維持 |
| **MUST ASK** | 人間の業務判断を待つ | 要件曖昧、設計方針未決、autonomy_bias 引き下げ、tecnos_org_constraints.md の「禁止」違反可能性、例外記録の内容、複数の実装選択肢 |
| **MUST ASK** | 人間の承認後に実行 | DDIC 操作（テーブル/ドメイン/データエレメントの ADT API 経由での登録・変更）— 実行前に対象・内容を提示し人間の承認を得ること |
| **MUST NOT DO** | 絶対禁止 | APPROVAL.md / WI-*.approval.md 編集、Gate スキップ、ERP ランタイムデータへの直接書込（DDIC スキーマ定義を除く）、秘密情報コミット、承認済み Gate の成果物変更（change_log.md + 再承認なしに）、Phase N+1 ファイルを Phase N 承認前に作成 |

### 新しい機能を作る場合の正しい手順

```bash
# Step 1: Intake（対話式ヒアリング）で要件を整理
sdd-templates/bin/stride intake <feature_name>

# または: フルテンプレートで初期化
sdd-templates/bin/stride init <feature_name> --detect

# Step 2: basic_design.md を作成（コードではなく仕様から始める）
# Step 3: stride lint → Gate 承認 → 次の Phase へ
```

**❌ 間違い:** ユーザーの要件を聞いていきなりコードを書く
**✅ 正しい:** まず `stride intake` or `stride init` → basic_design.md → Phase Gate を順に通過

## Inviolable Rules

- **SSoT**: Intent → Specs → Contracts → Code. Code 変更前に Specs を更新。
- **Phase Gates**: Design → Specify → Tasking → Execute. 各 Gate で人間の承認必須。
- **Auto-Lint**: Phase 完了のたびに `stride lint` を自動実行、APPROVAL以外のエラーは自動修正。

## Phase-Specific References (必要時のみ読む)

| Phase | 追加で読むファイル |
|-------|-------------------|
| 全 Phase | `agent_docs/commands.md`（全コマンド一覧） |
| Execute | `agent_docs/testing.md`（テスト詳細）, `agent_docs/conventions.md`（命名規約） |
| 制約確認 | `memory/constitution.md`, `memory/tecnos_org_constraints.md` |
| 詳細設定 | `CLAUDE_WORKFLOW.md`（Codex 固有）, `SDD_MANIFESTO.md`（ツール非依存ルール） |

## Tooling
- `stride lint`: `sdd-templates/bin/stride lint specs/<feature>/`
- `stride wi sync`: `python3 sdd-templates/tools/stride_wi_sync.py --feature <feature_id>` (GitHub Issues → WI ファイル同期)
- `stride pr-check`: `sdd-templates/bin/stride pr-check <project_root>`
- Phase Gate hook: See `CLAUDE_WORKFLOW.md` for `.Codex/settings.json` setup

## WI Management (Hybrid)
- **日常:** GitHub Issues (`work-item` ラベル) で管理
- **Gate 時:** `stride wi sync` で `specs/*/work_items/WI-*.md` にスナップショット生成
- **詳細:** `sdd-templates/docs/wi-management-guide.md`

## Symphony Orchestration (Optional)

GitHub Issues をトリガーとしたエージェント自律実行パイプライン。
`SYMPHONY.md` にオーケストレーション設定 + プロンプトテンプレートを定義する。

- **Phase 1-3**: Codex（判断・設計）
- **Phase 4**: Codex（並列実装）
- APPROVAL_PENDING → 自動停止 + 人間に承認依頼
- **APPROVAL.md / WI-*.approval.md をエージェントが編集することは絶対禁止**
- コマンド: `agent_docs/commands.md` の「Symphony Orchestration」セクション参照
