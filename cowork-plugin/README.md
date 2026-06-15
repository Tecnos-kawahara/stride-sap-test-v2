# Tecnos-STRIDE VALUE Cowork Plugin

> Version: **0.4.0-bpmn-package-integration** (Phase G+ — `bpmn/` 単独パッケージ統合、Tecnos-STRIDE 6.0.0-tecnos-stride-value 同梱)
>
> **v0.4.0 changes**: BPMN 2.0 / Camunda 8 作成ルールを `bpmn/` first-class component (rules + spec + templates + examples + validators) として統合。`/stride:bpmn-validate` を新設。`reference_files/` の BPMN 重複 6 ファイルを削除しドリフト防止。詳細は [`bpmn/README.md`](bpmn/README.md) と §6 (BPMN Package) を参照。

## 1. Overview

このプラグインは **上位コンサル (非技術者)** が Claude Cowork 上で Tecnos-STRIDE VALUE Upstream Extension を直接利用できるようにする拡張パッケージです。**BABOK v3** を framework backbone とし、**4-layer Requirements Architecture** (System / Business / Condition / Business Use Case) と **value-driven discovery** (考え方のみ、固有商標名は使用しない) を統合した SDD ライフサイクルの **Phase 0 (Discovery / Elicit / Layered Context Modelling) → Phase 1 (basic_design.md + process.bpmn) → 必要時 Epic 階層** を、自然言語の顧客要件から SDD 準拠成果物として完成させ、Claude Code への引き渡し (GitHub PR 経由) まで一気通貫で支援します。

**ターゲットユーザー**: BABOK + 4-layer Requirements Architecture + value-driven discovery の業務知識を持つが、Claude Code / SDD CLI に未習熟な上位コンサル。

### 1.1 Architecture Notes — Plugin runtime SSoT vs SDD contracts vs OpenAPI (★ Phase F WI-VALF01-005 / Gap-F-005)

本リポジトリには本 Plugin 関連で 3 種類の "spec / contract" が並存します。それぞれの役割を明確にすると以下の通りです:

| 階層 | ファイル | 役割 | SSoT? |
|---|---|---|---|
| **Plugin runtime** | `cowork-plugin/.claude-plugin/plugin.json` + `.mcp.json` + `skills/*/SKILL.md` + `commands/*.md` | Anthropic 公式 `knowledge-work-plugins` 仕様準拠の **Plugin runtime SSoT**。Claude Cowork が読み込む実行 manifest。 | ✅ Plugin runtime SSoT |
| **SDD contracts (例)** | `specs/val_*/contracts/openapi.yaml` ほか | Tecnos-STRIDE SDD の **論理 contract surface 例** (CLI Commands + File deliverables を OpenAPI 3.1 で表現)。Plugin runtime とは独立した SDD ライフサイクル成果物。 | ✅ SDD spec_as_code SSoT |
| **Anthropic Plugin spec** | (外部) `https://github.com/anthropics/knowledge-work-plugins` | Plugin の正規仕様書 (Markdown + JSON のみ)。本 Plugin が準拠する公式 schema。 | (外部、本リポジトリは consumer) |

**重要な独立性**: `specs/val_*/contracts/openapi.yaml` は **Plugin runtime とは独立** しています。OpenAPI ファイルが Plugin の動作を規定することはなく、SDD ライフサイクルでの contract-first 設計を支援する論理表現です。Plugin runtime の挙動は完全に `cowork-plugin/.claude-plugin/plugin.json` + `.mcp.json` + Skills/Commands 配下の Markdown + JSON で決定されます。

**Plugin 仕様準拠 (Markdown + JSON only)**: Plugin package (`cowork-plugin/` 配下) は Anthropic 公式仕様に従い Markdown + JSON のみで実装されます。ただし、Plugin が外部スクリプト (Tecnos-STRIDE 本体の `scripts/build_basic_design_html.py` 等) を呼ぶことは Plugin 仕様に反しません。同梱される `cowork-plugin/scripts/` (WI-VALF01-014) は顧客 PJ で Plugin を使う際の補助ツールボックスとして位置づけられています。

## 2. Installation

### 2.1 ローカル開発 (本リポジトリ clone 済み)

```bash
# 1. 構造検証
claude plugin validate ./cowork-plugin

# 2. Plugin 読み込み + slash command 実行
claude -p --plugin-dir ./cowork-plugin "/stride:init my_feature --profile enterprise-erp"
```

### 2.2 (Phase F 後の marketplace 公開後)

```bash
claude plugin install tecnos-stride-value@<marketplace-name>
```

詳細手順とトラブルシューティングは [`manual/51_cowork_plugin_install_guide.md`](../manual/51_cowork_plugin_install_guide.md) を参照してください。

## 3. Quick Start (1 コマンドで全部進む — Phase G UX-prep v0.3.0-simple-ux)

**コンサルが Cowork で打つのはこれだけ:**

```
/tecnos-stride-value:start [<自然言語の指示>]
```

引数なしで打てば conductor が状態を確認して次のおすすめを提示。自然言語ひとこと指示すれば conductor が意図を解釈して適切な専門 skill を自動起動します。

### 例

```
# 新規 PoC 開始
/tecnos-stride-value:start 新規顧客の supply management PoC を始めたい

# Phase 0 進める
/tecnos-stride-value:start Discovery 進めて
/tecnos-stride-value:start ヒアリング進める
/tecnos-stride-value:start 次に進んで

# Phase 1 設計
/tecnos-stride-value:start 設計書と業務フロー作って

# 顧客レビュー
/tecnos-stride-value:start 顧客にレビューしてもらう資料作って

# Claude Code に handoff
/tecnos-stride-value:start Claude Code に渡して

# 状態確認
/tecnos-stride-value:start
```

### 何が起こるか

1. **conductor skill** がコンサルの自然言語を解釈
2. **`state.yaml`** から現状の Phase 進捗を判定
3. **適切な専門 skill** (baccm-discovery / babok-elicitation / layered-context-modelling / upstream-bridge / basic-design-authoring / bpmn-authoring / epic-decomposition) を内部で自動起動
4. **進捗報告 + 次のおすすめ** をコンサルに提示

コンサルは固有語 (Tecnos-STRIDE / BACCM 等) や Phase 番号、引数構文を覚える必要なし — conductor が内部で全部補完する二重構造設計。

> **詳細制御したい場合**: §5 Commands 一覧 に 12 個の専門 commands があります (慣れたコンサルや fallback 用)。通常は `/start` だけで OK。

## 4. Skills 一覧 (8 個 — Phase E 7 + Phase G UX-prep 新規 1)

> **Phase G UX-prep PR-E** で **`stride-conductor`** (master orchestrator) を新規追加。conductor が自然言語をひとこと聞いて状態判定 + 次最適 step 自動選択 + 適切な専門 skill (下記 7 個) 内部起動。
>
> **Phase F (WI-VALF01-003)** で 7 専門 skill description を **Tecnos-STRIDE 固有語必須前置詞化** 済 (誤起動回避)。conductor 経由で呼ばれる時は固有語が補完されるため、コンサルは普通の業務日本語で OK な二重構造設計。

| Skill 名 | 役割 | 起動方法 |
|---|---|---|
| **`stride-conductor`** ★★ | **Master orchestrator** — 自然言語ひとこと → 状態判定 → 次最適 step 自動選択 → 専門 skill 内部起動 | **`/start` 経由 (推奨)** |
| `baccm-discovery` | Tecnos-STRIDE Phase 0 Discovery を BABOK BACCM 6 軸 (change/need/solution/stakeholder/value/context) で対話完成 | conductor 経由 or 直接固有語で |
| `babok-elicitation` | Tecnos-STRIDE Phase 0 で BABOK KA4 Elicitation。50 technique から context 別に 5 件推奨 | 同上 |
| `layered-context-modelling` | Tecnos-STRIDE Phase 0 で 4-layer Requirements Architecture / 5 シート (actor / business_usecase / information_state / condition_variation / requirements_architecture) | 同上 |
| `upstream-bridge` | Tecnos-STRIDE Phase 0 → Phase 1 接続。basic_design.md skeleton 生成 + links populate | 同上 |
| `basic-design-authoring` | Tecnos-STRIDE SDD Phase 1 で basic_design.md を canonical schema (TPL-BD-TECNOS-001) 準拠で完成 | 同上 |
| `bpmn-authoring` | Tecnos-STRIDE SDD Phase 1 で process.bpmn を Camunda 8 BPMN MUST-DO 6 項目厳守で作成 | 同上 |
| `epic-decomposition` | Tecnos-STRIDE Epic 階層判定 + 必要時のみ epic_design.md + feature_breakdown.md 作成 | 同上 |

## 5. Commands 一覧 (13 個 — Phase E 9 + Phase F 新規 2 + Phase G UX-prep 新規 2)

> **§3 Quick Start で `/start` 1 コマンドだけ覚えれば OK**。下記 13 個の専門 commands は conductor が内部で呼ぶ or 詳細制御したい慣れたコンサルが直接打つ用途の internal reference。

| Command | 引数 | 役割 | Phase |
|---|---|---|---|
| **`/stride:start`** ★★★ | `[<自然言語の指示>]` | **1 コマンド入口** — conductor 経由で状態判定 + 自然言語意図解釈 + 次最適 step 自動選択 + 専門 skill 内部起動。**通常はこれだけで OK** | **G UX-prep 新規 (PR-E)** |
| `/stride:bootstrap-repo` ★★ | `<repo_name> [--org <github_org>] [--profile <P>] [--scale <S>] [--first-feature <F>]` | **完璧な dev 環境を備えた新規顧客 PoC リポジトリを 1 コマンドで bootstrap** — GitHub MCP 新規 private repo + Tecnos-STRIDE template 派生 + stride new-project + Phase Gate hooks + .claude/settings.json + GitHub Actions CI + branch protection 全自動。Cowork (上流) → Claude Code (Phase 4) の **継ぎ目のない接続** を実現 | **G UX-prep 新規 (PR-D)** |
| `/stride:init` | `<feature_name> [--profile <P>]` | specs/<feature>/ scaffold | E |
| `/stride:discovery` | `<feature_name>` | baccm-discovery skill 起動 | E |
| `/stride:elicit` | `<feature_name>` | babok-elicitation skill 起動 | E |
| `/stride:context-model` | `<feature_name>` | layered-context-modelling skill 起動 (Phase G PR-A で rename: rdra-context-modelling → layered-context-modelling) | E |
| `/stride:validate` | `<feature_name>` | BACCM 6 軸 + 4-layer Requirements Architecture 完全性チェック | E |
| `/stride:bridge` | `<feature_name>` | upstream-bridge skill 起動 | E |
| `/stride:design` | `<feature_name>` | basic-design + bpmn-authoring 起動 + **dev 依存自動検出 + pip install 提案** (WI-013) | E + **F 改修** |
| `/stride:epic-init` | `<EPIC_ID> [--features <list>]` | epic-decomposition 起動 | E |
| `/stride:handoff` | `<feature_name> [--repo <url>]` | GitHub MCP 経由 PR draft 作成 + **Cowork セッション内 4 ファイル機械検証 + §Rule 15-B サニタイズ自動 grep** (WI-001 + WI-004) | E + **F 改修** |
| `/stride:export-html` ★ | `<feature_name>` | **basic_design.md → HTML 変換** (顧客レビュー用、`scripts/build_basic_design_html.py` 経由、DR-103: Plugin 同梱せず Tecnos-STRIDE 本体 helper) | **F 新規 (WI-011)** |
| `/stride:tasking` ★ | `<feature_name>` | **VALUE pack → SDD Phase 3 (Tasking) を 1 コマンド連結**、work_items/ scaffold + tasks.md 生成 (★ v2 P0-3 必須化) | **F 新規 (WI-016)** |

## 6. Workflow Diagram (Phase F v0.2.0-stable + Phase G UX-prep)

```
            ┌────────────────────────────────────┐
            │  /stride:bootstrap-repo (★G、任意) │
            │  完璧な dev 環境付き新規 PoC repo を│
            │  1 コマンドで bootstrap            │
            │  (新規顧客 PoC 開始時のみ)         │
            └─────────────────┬──────────────────┘
                              │ (clone した repo 内で以下実行)
                              ▼
                    ┌─────────────────┐
                    │  /stride:init   │
                    │  (scaffold、     │
                    │   --profile <P>)│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  /stride:discovery   /stride:elicit    /stride:context-model
  (BACCM 6 軸)       (BABOK KA4         (5-sheet Requirements Modeling)
                      50 technique)
         └───────────────────┼───────────────────┘
                             │
                             ▼
                    /stride:validate
                    (BACCM 6 軸 + 4-layer
                     完全性 / profile 別閾値)
                             │
                             ▼
                     /stride:bridge
                    (Phase 0 → Phase 1 接続、
                     basic_design.md skeleton)
                             │
                             ▼
                     /stride:design
                    (basic-design + bpmn-authoring、
                     起動時 dev 依存自動検出 ★F)
                             │
                             ▼
                  /stride:epic-init (任意)
                  (Epic 階層化判定)
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
     /stride:export-html ★F          (顧客レビュー後、修正)
     (basic_design.md → HTML、         basic_design.md 編集
      顧客共有)                         → /stride:export-html 再実行
                │
                └────────────┬────────────┘
                             ▼
                    /stride:handoff
                    (Cowork 内 4 ファイル機械検証 ★F
                     + §Rule 15-B サニタイズ自動 grep ★F
                     + GitHub PR draft 作成)
                             │
                             ▼
                    /stride:tasking ★F
                    (VALUE pack → Phase 3 連結、
                     work_items/ scaffold + tasks.md)
                             │
                             ▼
                    Claude Code 引き渡し
                    (Phase 4 Execute、各 WI 実装)
```

> **★F** = Phase F (v0.2.0-stable) で新規 / 改修。**Phase F の追加機能**: dev 依存自動化 (stride-design) / HTML 出力 (stride-export-html) / Cowork 内機械検証 + サニタイズ grep (stride-handoff) / Phase 3 連結 (stride-tasking)。詳細: [`../manual/52_phase_f_lessons_learned.md`](../manual/52_phase_f_lessons_learned.md)

## 7. Reference Files (49 ファイル同梱)

`cowork-plugin/reference_files/` 配下に Tecnos-STRIDE 本体の知識を 49 ファイル同梱:

- `manual/`: 12 (39-50_*.md、VALUE Upstream + Profile playbooks)
- `constitution.md`: 1 + `constitution_amendments/`: 3 (XV-XVII)
- `policies/`: 5 (upstream / baccm / technique / iteration / profile)
- `templates/upstream/`: 16 (15 yaml + README)
- `templates/`: 6 (basic_design / process_bpmn / epic_design / feature_breakdown / epic_progress_report / epic_flow)
- `migration/`: 1 (v54_to_v60.md)
- `sdd-templates/`: 3 (AGENTS / SDD_MANIFESTO / sdd_bootstrap)
- `docs/`: 2 (bpmn_quick_reference / camunda_bpmn_practice_guide)

**更新追従**: `scripts/sync_cowork_plugin_reference.sh` で Tecnos-STRIDE 本体の更新を反映、49 件厳守チェック内蔵。

## 8. MCP Connectors

`cowork-plugin/.mcp.json` で 2 servers 設定:

- **filesystem**: `${WORKSPACE}` 配下にアクセス制限
- **github**: `${GITHUB_PERSONAL_ACCESS_TOKEN}` で認証 (PAT scope: repo write + PR create)

詳細は [`CONNECTORS.md`](./CONNECTORS.md) 参照。

## 9. Compatibility

- **Claude Cowork** (上位コンサル向け、推奨)
- **Claude Code** (Plugin 形態でも `claude -p --plugin-dir ./cowork-plugin` で動作確認可)

## 10. License + Attributions

License: MIT (Tecnos Japan Inc.)

Attributions:
- **BABOK v3 (IIBA)** — framework backbone (KA4 / KA6 / KA7 / KA8)、fair-use, names and section refs only
- **4-layer Requirements Architecture** — System / Business / Condition / Business Use Case の構造的整合性 (考え方のみ、固有商標名は使用しない)
- **value-driven discovery (philosophical foundation)** — value canvas / goal tree の思想的源流として参照 (考え方のみ、固有商標名は使用しない)
- **Anthropic Knowledge Work Plugins** — Plugin SDK reference、MIT
