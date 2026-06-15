# 52. Phase F Lessons Learned + Cowork Plugin v0.2.0-stable 運用ガイド

> Version: v6.0.0-tecnos-stride-value (Phase F, FEAT-VALF01) / Plugin 0.2.0-stable / Last reviewed: 2026-05-01

Phase F (FEAT-VALF01) は Cowork Plugin v0.1.0-poc → **v0.2.0-stable** への運用品質引き上げを実現したフェーズです。fc-sd 案件 (jm_costco_supply_management、enterprise-erp profile) で発見された 16 件改善要望を 17 Work Items で反映、Tecnos-STRIDE 本体 VERSION 6.0.0 不変、Plugin 独立 SemVer。

本章は Phase F の 11 章構成: ① 概要 / ② Phase F ミッション + スコープ / ③ 17 WI 対応総括 / ④ Phase F-1 緊急 6 件 / ⑤ Phase F-1 高優先 3 件 / ⑥ Phase F-2 中優先 4 件 / ⑦ Phase F-3 仕上げ 3 件 / ⑧ 実機運用 lessons / **⑨ fc-sd 相当の Plugin 導入手順** (WI-VALF01-017 で追記) / ⑩ Phase G への申し送り / ⑪ References。

## 1. 概要

Phase E (PR #10/#11/#12/#13 マージ済) で Cowork Plugin v0.1.0-poc が Anthropic 公式 `knowledge-work-plugins` 仕様準拠で構造的に完成しました。本日 (2026-04-30) の fc-sd 実機運用で発見された 16 件の改善要望を反映し、上位コンサルが業務で安全に使えるレベルに引き上げたのが Phase F です。

| 軸 | Phase E v0.1.0-poc | Phase F v0.2.0-stable |
|---|---|---|
| 構造妥当性 | Anthropic 仕様準拠 ✅ | 維持 ✅ |
| Cowork セッション内 機械検証 | 不在 | **bash 1-liner で 4 ファイル + 必須セクション grep** ✅ |
| CI 統合 | 不在 | **`.github/workflows/cowork-plugin-validate.yml`** ✅ |
| state.yaml Phase 2-4 schema | 不在 | **`phase_2/3/4/final` セクション** + 検証テスト +3 ✅ |
| handoff サニタイズ | 手動 | **§Rule 15-B grep -E 自動化** ✅ |
| HTML 出力 | 不在 | **`scripts/build_basic_design_html.py` + `/stride:export-html`** ✅ |
| 3 profile dogfood | enterprise-erp のみ | **saas-integration / prototype scaffold** (実 dogfooding は Phase F PR merge 後 follow-up) ✅ |
| Skill auto-trigger | 汎用語衝突あり | **Tecnos-STRIDE 固有語必須前置詞化** ✅ |
| commands 数 | 9 | **11** (`stride-export-html` + `stride-tasking` 追加) ✅ |
| reference_files | 49 | **49 維持** (`scripts/` + `.claude-template/` は別ディレクトリ計上) ✅ |
| Plugin VERSION | 0.1.0-poc | **0.2.0-stable** ✅ |

## 2. Phase F ミッション + スコープ

### ミッション
> Cowork Plugin v0.1.0-poc を v0.2.0-stable に引き上げる運用品質改善 + fc-sd 実機運用 16 件改善要望反映 + 17 WI 実装

### In Scope (Phase F)
- 16 改善要望対応 (Gap-F-001..008 + 改善要望-09..16) と 17 WI 実装
- Plugin 独立 SemVer 0.1.0-poc → 0.2.0-stable
- CI 統合 + state.yaml schema 拡張 + サニタイズ自動化
- 3 profile (enterprise-erp / saas-integration / prototype) の dogfood scaffold

### Out of Scope (Phase G/H 候補)
- Anthropic Plugin Marketplace 公開 / OSS 化 (Phase G 候補)
- Plugin VERSION 1.0.0 への bump (Phase G)
- Tecnos-STRIDE 本体 VERSION bump (6.0.0 維持)
- Constitution 改変 / 顧客向けカスタマイズ機能 / 多言語対応

## 3. 17 Work Items 対応総括

| WI | 改善要望 | 優先度 | Sprint |
|---|---|---|---|
| WI-VALF01-001 | handoff workflow Cowork 内機械検証 | 🔴 緊急 | F-1 W1 |
| WI-VALF01-002 | GitHub Actions CI 統合 | 🔴 緊急 | F-1 W1 |
| WI-VALF01-003 | Skill description 衝突回避 (7 件) | 🟠 高 | F-1 W2 |
| WI-VALF01-004 | handoff サニタイズ自動 grep | 🟠 高 | F-1 W2 |
| WI-VALF01-005 | OpenAPI / Plugin spec 関係明示 | 🟡 中 | F-1 W2 |
| WI-VALF01-006 | Test-2 saas-integration scaffold | 🟡 中 | F-2 W3 |
| WI-VALF01-007 | Test-3 prototype scaffold | 🟡 中 | F-2 W3 |
| WI-VALF01-008 | manual/52 lessons 集約 | 🟢 仕上げ | F-3 W4 |
| WI-VALF01-009 | Plugin VERSION 0.2.0-stable bump | 🟢 仕上げ | F-3 W4 |
| WI-VALF01-010 | state.yaml Phase 2-4 schema + tests +3 | 🟠 高 | F-1 W1 |
| WI-VALF01-011 | HTML 出力 + stride-export-html | 🟡 中 | F-2 W3 |
| WI-VALF01-012 | GitHub MCP 検証 evidence scaffold | 🟠 高 | F-1 W1 |
| WI-VALF01-013 | dev 依存自動化 (stride-design SKILL) | 🟠 高 | F-1 W1 |
| WI-VALF01-014 | cowork-plugin/scripts/ 同梱 | 🟡 中 | F-2 W3 |
| WI-VALF01-015 | .claude-template/settings.json | 🟢 仕上げ | F-3 W4 |
| WI-VALF01-016 | stride-tasking command 新規 | 🟠 高 | F-1 W1 |
| WI-VALF01-017 | manual/52 §9 fc-sd 導入手順 (本章 §9) | 🟢 仕上げ | F-3 W4 |

総工数 11.8 日、4 週間スプリント。

## 4. Phase F-1 緊急 6 件 (Week 1)

### 4.1 WI-001 — handoff workflow Cowork セッション内 機械検証 (Gap-F-001)

**問題**: Phase E 時点では handoff 直前に Cowork セッション内で 4 ファイルの存在 + 必須セクションを機械検証する手段が無く、コンサルが見落としたまま handoff してしまうリスクがあった。

**解決**: `cowork-plugin/commands/stride-handoff.md` の Workflow §2 に bash 1-liner を追加。`basic_design.md` / `process.bpmn` / `upstream/claude_code_handoff.md` / `upstream/acceptance_criteria.yaml` の存在 + `basic_design` の 7 必須セクション + BPMN の 4 必須要素を grep 検証。1 件でも欠落で `[BLOCKER]` 停止。

### 4.2 WI-002 — GitHub Actions CI 統合 (Gap-F-002)

**問題**: PR で Plugin 関連変更があっても CI が無く、defect が main マージ後に発覚するリスクがあった。

**解決**: `.github/workflows/cowork-plugin-validate.yml` を新規作成。`cowork-plugin/**` / `.claude-plugin/**` / `scripts/build_basic_design_html.py` / `tests/test_cowork_plugin_*.py` の path 変更時にのみ trigger (path filter)、ubuntu-latest + Python 3.11 + claude CLI で `claude plugin validate` + 関連 pytest 実行。Plugin 無関係 PR では trigger されず CI 時間を節約。

### 4.3 WI-010 — state.yaml Phase 2-4 schema + tests +3 (改善要望-09)

**問題**: VALUE pack handoff 後の SDD Phase 2-4 進捗を `state.yaml` で機械追跡する schema が無かった。

**解決**: `state.yaml` に `phase_2` / `phase_3` / `phase_4` / `final` セクションを拡張。各セクションに `status` / `*_done` (bool) / `approved_at` を持つ flat schema。`tests/test_cowork_plugin_state_yaml_phases.py` で +3 tests を追加 (Phase 2 / Phase 3 / Phase 4+Final schema 検証)。baseline 789 → 792。

### 4.4 WI-012 — GitHub MCP 検証 evidence scaffold (改善要望-11)

**問題**: `cowork-plugin/.mcp.json` の GitHub MCP 設定が実機検証されておらず、上位コンサル環境で動くか不明だった。

**解決**: `docs/evidence/phase_f/wi_012_mcp_validation.md` を新規作成し、検証手順 + 期待 schema + sanitized snapshot 例を scaffold。**実 GitHub API 検証は Phase F PR merge 後に Hitoshi さん follow-up** として記録 (AI 単独では PAT + private repo 作成不可)。

### 4.5 WI-013 — dev 依存自動化 (改善要望-12)

**問題**: 上位コンサル環境で `pyyaml` / `jsonschema` / `markdown` / `jinja2` が未 install のまま `/stride:design` を起動するとエラーになる。

**解決**: `cowork-plugin/commands/stride-design.md` の Workflow §0 で起動時に必要 module を `python3 -c "import ..."` で検出し、未 install の場合は `pip install ...` コマンドを提案。AI が自動で install することはせず、コンサルが手動で install → 再起動する想定 (権限境界を維持)。

### 4.6 WI-016 — stride-tasking command 新規 (改善要望-15)

**問題**: VALUE pack (Phase 1) 完了後、SDD Phase 3 (Tasking) に進むには手動で `tasks.md` + `work_items/` を作る必要があり、上位コンサルにとってハードルが高かった。

**解決**: `cowork-plugin/commands/stride-tasking.md` を新規作成。VALUE pack → Phase 3 を 1 コマンド連結し、`tasks.md` scaffold + `work_items/WI-*.md` scaffold を生成。Phase 3 を機械化。

## 5. Phase F-1 高優先 3 件 (Week 2)

### 5.1 WI-003 — Skill description キーワード衝突回避 (Gap-F-003)

**問題**: Phase E の 7 SKILL.md の description が「Discovery」「Elicit」「ワークショップ」等の汎用語を auto-trigger に含んでいたため、Tecnos-STRIDE と無関係な依頼でも誤起動するケースがあった。

**解決**: 7 SKILL.md description を **Tecnos-STRIDE 固有語前置詞必須** に改修。「BACCM Discovery」「BABOK Elicitation」「Tecnos-STRIDE Phase 0」などの固有語を必須キーワードとし、汎用語単独では起動しない設計に変更。Workflow セクションは Phase E から不変 (Rule 1-A 範囲内)。

### 5.2 WI-004 — handoff サニタイズ自動 grep (Gap-F-004)

**問題**: handoff 時に §Rule 15-B 禁止キーワード (顧客名 / 担当者名 / 金額 / 契約番号) のサニタイズ漏れリスクが手作業任せだった。

**解決**: `cowork-plugin/commands/stride-handoff.md` Workflow §3 に `grep -E` で禁止キーワード集を `upstream/*.yaml` + `lessons_learned` に対し検査するステップを追加。ヒット時は `[BLOCKER]` で停止。パターンは Tecnos 内部固有名詞ベースに限定し、汎用業務語 (注文 / 在庫 / 顧客) は除外して false-positive を抑制。

### 5.3 WI-005 — OpenAPI / Plugin spec 関係明示 (Gap-F-005)

**問題**: `cowork-plugin/contracts/openapi.yaml` (SDD contract 例) と `.claude-plugin/plugin.json` (Plugin runtime SSoT) と Anthropic Plugin spec の関係が `cowork-plugin/README.md` に未記載で混乱を招いていた。

**解決**: `cowork-plugin/README.md §1.1 Architecture Notes` セクションを追加し、3 階層 (Plugin runtime SSoT / SDD contracts / Anthropic Plugin spec) の役割分担を表で明示。`OpenAPI 例は Plugin runtime とは独立` を明記。

## 6. Phase F-2 中優先 4 件 (Week 3)

### 6.1 WI-011 — HTML 出力 + /stride:export-html (改善要望-10)

**問題**: 顧客レビュー時に `basic_design.md` を Markdown のまま見せると読みづらく、HTML 化が欲しかった。

**解決**: `scripts/build_basic_design_html.py` を Tecnos-STRIDE 本体 helper として新規作成 (`markdown` package 使用、self-contained HTML、CSS inline)。`cowork-plugin/commands/stride-export-html.md` から呼び出す。**DR-103**: Plugin 配布物の最小化のため、HTML helper は Plugin 同梱せず本体 `scripts/` 配下に集中管理 (Plugin 利用は Tecnos-STRIDE clone 前提)。

### 6.2 WI-014 — cowork-plugin/scripts/ ディレクトリ同梱 (改善要望-13)

**問題**: 上位コンサル環境で Plugin 補助スクリプトを使うために、本体の `scripts/` を別途取得する必要があった。

**解決**: `cowork-plugin/scripts/` 新規ディレクトリに `validate_state_yaml.py` + `check_handoff_files.py` + `README.md` を配置。Plugin install 時に同梱配布される。`reference_files = 49 不変` を `cowork-plugin/scripts/` を別ディレクトリ計上することで維持。

### 6.3 WI-006 / WI-007 — saas-integration / prototype profile dogfood scaffold (Gap-F-006/007)

**問題**: enterprise-erp profile は fc-sd で dogfood 完了したが、saas-integration / prototype profile は未検証で playbook の有効性が不明だった。

**解決**: `memory/lessons_learned/upstream_dogfooding/saas_integration_pilot_01.md` + `prototype_pilot_01.md` を scaffold で配置。検証手順 + 期待 lessons 構造 + Q-102 (PoC 案件選定) follow-up タスクを記録。**実 dogfooding は Phase F PR merge 後に Hitoshi さん + 上位コンサルが追加実施**。

## 7. Phase F-3 仕上げ 3 件 (Week 4)

### 7.1 WI-015 — .claude-template/settings.json (改善要望-14)

**問題**: 上位コンサル毎に `.claude/settings.json` の設定が異なり、Plugin 動作の再現性が低かった。

**解決**: `cowork-plugin/.claude-template/settings.json` 新規作成し、Plugin install 時に推奨 hook (Phase Gate Hook) + permission (Edit/Write は specs/cowork-plugin に制限、APPROVAL.md は deny) + env 説明を配布。reference_files = 49 不変。

### 7.2 WI-008 + WI-017 — manual/52 11 章 (本章) + §9 fc-sd 導入手順

**問題**: Phase F lessons が未集約で、上位コンサル展開時の学びの再利用ができなかった。fc-sd 案件相当の Plugin 導入手順が manual に未記載で、外部 fc-sd repo に手順書を置く案もあったが、外部 repo 改変は scope 外。

**解決**: 本章 (manual/52) を 11 章構成で新規作成。`§9` に fc-sd 相当の Plugin 導入手順を追記 (★ v2 P0-5: スコープ内、外部 fc-sd repo は触らない、DR-104)。`manual/_sidebar.md` / `agent_docs/project_map.md` / `README.md` に Phase F section 追記 (Rule 1-A 範囲内)。

### 7.3 WI-009 — Plugin VERSION 0.1.0-poc → 0.2.0-stable

**問題**: Phase F 全 16 改善要望対応完了後、Plugin VERSION の bump で配布開始可能状態にする必要があった。

**解決**: `cowork-plugin/.claude-plugin/plugin.json` の `version` フィールドのみ更新 (`0.1.0-poc` → `0.2.0-stable`)。他フィールドは Phase E から不変 (Rule 1-A 範囲内)。Tecnos-STRIDE 本体 VERSION (`6.0.0-tecnos-stride-value`) は不変、Plugin 独立 SemVer。

## 8. 実機運用 Lessons (sanitized)

Phase F の実装作業 (Hitoshi さん × Claude Code Opus 4.7) で得られた lessons:

### 8.1 Plugin runtime SSoT vs SDD contracts の混乱回避

`contracts/openapi.yaml` と `.claude-plugin/plugin.json` を **同列に並べない**。SDD contracts は論理 contract surface で Plugin runtime とは独立、Plugin runtime SSoT は `.claude-plugin/plugin.json` のみ。WI-005 で README に明文化。

### 8.2 hash 保護 + 許可リスト判定で安全な変更管理

Phase E v3.1 で確立した **`shasum -c` で FAILED ファイル抽出 → 許可リスト判定** 方式を Phase F でも踏襲。174 ファイルを baseline、12 ファイルのみ許可リスト (Rule 1-bis)、許可外の hash 変更は即 `[BLOCKER]`。

### 8.3 dogfooding の AI / 人間境界

実 dogfooding (saas-integration / prototype profile での 1 PoC 完走) は **AI 単独では完遂不可**。Plugin 配布物の scaffold + 検証手順 + 期待 lessons schema は AI が完成形で配置、実 dogfooding 結果の追記は Hitoshi さん + 上位コンサルの follow-up。Phase F PR merge は scaffold 配置で closure し、実 dogfooding は別 PR で追記する two-step 戦略。

### 8.4 CI 統合は早期投入で残 WI 開発を機械検証下で実施

WI-002 (CI workflow) を Week 1 の最初に倒すことで、Week 2 以降の 11 WI は PR で `claude plugin validate` + 関連 pytest が機械検証されながら開発可能になり、defect の post-merge 検出を抑制。

## 9. fc-sd 相当の Plugin 導入手順 (★ WI-VALF01-017 / 改善要望-16)

> 本セクションは fc-sd 案件 (jm_costco_supply_management、enterprise-erp profile) 相当の **新規顧客 PoC** に Cowork Plugin v0.2.0-stable を導入する標準手順を sanitized 形式で記載。**外部 fc-sd repo (実 PoC リポジトリ) には変更を加えない** (★ v2 P0-5、DR-104)。fc-sd 案件チームは本章を Tecnos-STRIDE 本体 clone で参照する。

### 9.1 前提環境

- Claude Cowork または Claude Code (CLI v2+) install 済
- Tecnos-STRIDE 本体 clone 可能 (GitHub `tecnos-japan-cbp/tecnos-stride`)
- Python 3.11+ + pip
- (任意) GitHub Personal Access Token (`stride-handoff` の GitHub MCP 連携で必要)

### 9.2 ステップ 1: marketplace 経由で Plugin install

```bash
# 1. Tecnos-STRIDE 本体を clone (顧客 PJ の Cowork Project とは別ディレクトリ)
git clone https://github.com/tecnos-japan-cbp/tecnos-stride.git ~/work/tecnos-stride
cd ~/work/tecnos-stride

# 2. Tecnos-STRIDE 全体を local marketplace として登録
claude plugin marketplace add "$(pwd)"
# 期待: ✔ Successfully added marketplace: tecnos-stride

# 3. Plugin install
claude plugin install tecnos-stride-value@tecnos-stride
# 期待: ✔ Plugin tecnos-stride-value@0.2.0-stable installed
```

### 9.3 ステップ 2: 推奨 .claude/settings.json 導入

```bash
# 顧客 PJ Cowork Project ローカルに移動 (Tecnos-STRIDE clone とは別)
cd <顧客 PJ Cowork Project ローカル>

# 推奨 settings.json をコピー (既存があれば手動マージ)
mkdir -p .claude
cp ~/work/tecnos-stride/cowork-plugin/.claude-template/settings.json .claude/settings.json
```

### 9.4 ステップ 3: 初回 intake (Phase 0 着手)

Cowork セッションを起動し、以下 commands を順次実行:

```
/tecnos-stride-value:stride-init <feature_name> --profile enterprise-erp
/tecnos-stride-value:stride-discovery <feature_name>
/tecnos-stride-value:stride-elicit <feature_name>
/tecnos-stride-value:stride-context-model <feature_name>
/tecnos-stride-value:stride-validate <feature_name>
```

各 command 起動後、Skill が **Tecnos-STRIDE 固有語必須前置詞** で auto-trigger される (WI-VALF01-003)。汎用業務語 (注文 / 在庫 等) では誤起動しない。

### 9.5 ステップ 4: Phase 1 設計 + handoff

```
/tecnos-stride-value:stride-bridge <feature_name>
/tecnos-stride-value:stride-design <feature_name>
   # 起動時に dev 依存自動検出 (pyyaml/markdown/jinja2 等)、未 install なら pip install を提案 (WI-013)
/tecnos-stride-value:stride-epic-init <EPIC_ID>      # 必要時のみ
/tecnos-stride-value:stride-export-html <feature_name>
   # basic_design.md → HTML 変換、顧客レビュー用 (WI-011)
/tecnos-stride-value:stride-handoff <feature_name> [--repo <github_url>]
   # Cowork 内機械検証 + サニタイズ自動 grep + GitHub PR draft 作成 (WI-001 + WI-004)
```

### 9.6 ステップ 5: Phase 3 (Tasking) → Phase 4 (Execute、Claude Code 担当)

```
/tecnos-stride-value:stride-tasking <feature_name>   # WI-016 (Phase F 新規)
   # work_items/ scaffold + tasks.md 生成、Phase 3 を 1 コマンド連結
```

handoff PR を Claude Code 担当者が pull し、Phase 4 (Execute) を実施 (各 WI 単位で実装 → state.yaml 更新)。

### 9.7 トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `claude plugin install` で "Plugin tecnos-stride-value not found" | marketplace 未登録 | `claude plugin marketplace add <Tecnos-STRIDE clone path>` を再実行 |
| `/stride:design` 起動時に "ImportError: No module named 'yaml'" | dev 依存未 install | `pip install pyyaml jsonschema markdown jinja2` |
| `/stride:handoff` で `[BLOCKER] §Rule 15-B sanitize hit` | 顧客固有名詞が upstream/*.yaml に残存 | 該当箇所をサニタイズ (固有名詞 → 抽象化) して再実行 |
| GitHub MCP 接続失敗 | PAT scope 不足 | `cowork-plugin/CONNECTORS.md §2 §4` 参照、scope = repo + pull_request + metadata |
| CI が PR で trigger されない | path filter に該当しない | `.github/workflows/cowork-plugin-validate.yml` の `paths:` を確認、`cowork-plugin/**` 等の path に変更が含まれることを確認 |

### 9.8 関連 References (本章の独立性)

- `cowork-plugin/CONNECTORS.md` (PAT scope, MCP server 設定)
- `cowork-plugin/.claude-template/settings.json` (推奨 hook + permission)
- `cowork-plugin/scripts/{validate_state_yaml.py,check_handoff_files.py}` (補助スクリプト)
- `manual/51_cowork_plugin_install_guide.md` (Phase E 完成 install ガイド、本章は補完)

> **重要**: 本章は外部 fc-sd repo (実 PoC リポジトリ) には書き込まない (★ v2 P0-5、DR-104)。Tecnos-STRIDE 本体内で導入手順を集中管理することで、scope 境界を厳守。

## 10. Phase G への申し送り

- **Plugin VERSION 1.0.0 への bump**: 本格 OSS 化と同タイミングで Phase G にて bump
- **Anthropic Plugin Marketplace 公開**: Phase G の登録要件を確認 (WI-VALF01-012 evidence + 検証手順は再利用)
- **顧客向けカスタマイズ機能**: 顧客固有の `profile_policy.yaml` 拡張を Phase G で検討
- **多言語対応**: 英語版 manual + Plugin description は Phase H 候補
- **Q-102 closure**: saas-integration / prototype profile の実 dogfooding を 2026-05-15 までに完了し、本 manual §6 + lessons_learned/upstream_dogfooding/ に追記

## 11. References

- Phase F prompt: `docs/Tecnos-STRIDE Upstream Extension_F.md`
- Phase F SDD 自己適用成果物: `specs/val_f01/{basic_design.md,process.bpmn,spec.md,plan.md,tasks.md,contracts/openapi.yaml}`
- Constitution: `memory/constitution.md` (v6.0.0-tecnos-stride-value、Article XV-XVII ratified)
- Phase E 完成成果物: `cowork-plugin/` (Skills 7 + Commands 11 + reference_files 49 + MCP 2 + scripts/ + .claude-template/)
- Phase E 章: `manual/51_cowork_plugin_install_guide.md`
- Phase D 章: `manual/{39-50}_*.md`
- Profile policies: `shared/policies/profile_policy.yaml` + `shared/policies/baccm_completeness.yaml`

> Phase F (FEAT-VALF01) 完成。Plugin v0.2.0-stable 配布開始可能、saas-integration / prototype profile 実 dogfooding と GitHub MCP 実機検証は Phase F PR merge 後の Hitoshi さん follow-up。
