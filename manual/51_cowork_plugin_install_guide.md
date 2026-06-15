# 51. Cowork Plugin インストール + 使い方ガイド

> Version: v6.0.0-tecnos-stride-value (Phase E, FEAT-VALE01) / Plugin 0.1.0-poc / Last reviewed: 2026-04-30

`cowork-plugin/` は **上位コンサル (非技術者)** が Claude Cowork 上で Tecnos-STRIDE VALUE Upstream Extension を直接利用できるようにする Anthropic 公式 `knowledge-work-plugins` 仕様準拠のプラグインです。Phase 0 (Discovery / Elicit / Context Modelling) → Phase 1 (basic_design.md + process.bpmn) → 必要時 Epic 階層 → Claude Code への引き渡し (GitHub PR 経由) を一気通貫で支援します。

## 1. Plugin の目的

技術者 (Claude Code 操作者) に依存せず、**上位コンサル単独** で Phase 0/1 を完成させる体制を実現します。BABOK v3 / Layered Requirements Modeling / value-driven discovery method の業務知識を持つコンサルが Cowork セッションで対話するだけで、SDD 準拠の Phase 0 yaml 群 + basic_design.md + process.bpmn が生成され、Claude Code が Phase 2-4 (実装) に集中できる **上下流完全分業** を実現します。

ターゲットユーザー: 中規模 PoC (enterprise-erp) / API 連携案件 (saas-integration) / 社内 PoC (prototype) のいずれも対応。

## 2. インストール手順

### 2.1 ローカル marketplace 経由 (推奨、実機検証済)

Tecnos-STRIDE リポジトリ自体を **local marketplace** として登録、Plugin を user scope に install する **再現可能** な手順。`.claude-plugin/marketplace.json` (PR #12 で導入) を利用するため、クローンするだけで誰でも同じ手順で install できる。

```bash
# 1. Tecnos-STRIDE 本体を clone
git clone https://github.com/tecnos-japan-cbp/tecnos-stride.git
cd tecnos-stride

# 2. Plugin 構造の機械検証 (任意、必須ではない)
claude plugin validate ./cowork-plugin
# 期待出力: ✔ Validation passed

# 3. Tecnos-STRIDE 全体を local marketplace として登録
claude plugin marketplace add "$(pwd)"
# 期待出力: ✔ Successfully added marketplace: tecnos-stride

# 4. Plugin を user scope に install
claude plugin install tecnos-stride-value@tecnos-stride
# 期待出力: ✔ Successfully installed plugin: tecnos-stride-value@tecnos-stride (scope: user)

# 5. インストール確認
claude plugin list | grep tecnos-stride-value
# 期待: tecnos-stride-value@tecnos-stride / Version: 0.1.0-poc / Status: ✔ enabled

# 6. (任意) 環境変数の永続化 (~/.zshrc 等、handoff コマンド利用前提)
export WORKSPACE="$(pwd)"
export GITHUB_TOKEN="<your-fine-grained-PAT>"   # Contents R/W + PR R/W + Metadata R
```

★ install 後は ~/.claude/plugins/cache/tecnos-stride/tecnos-stride-value/0.1.0-poc/ に **69 ファイル** (manifest 4 + skills 7 + commands 9 + reference_files 49) が展開され、claude を再起動すれば全 16 slash commands/skills が利用可能になります。

### 2.2 ワンショット実行 (--plugin-dir、開発時の確認用)

install せずにその場でPluginを読み込んで一発実行する方式 (Plugin の動作確認 / CI 用)。

```bash
claude -p --plugin-dir ./cowork-plugin --dangerously-skip-permissions \
  "/tecnos-stride-value:stride-init test_feature_001 --profile prototype"
```

※ user scope 永続化はされないため、毎回 `--plugin-dir` を指定する必要があります。

### 2.3 (Phase F 候補) 公式 marketplace 公開後

```bash
claude plugin install tecnos-stride-value@<official-marketplace-name>
```

★ Phase E では公式 marketplace 未登録のため §2.1 (local marketplace) を推奨。Phase F で `claude-plugins-official` 等への登録 + OSS 公開を予定。

## 2-bis. Plugin の起動方法 (3 通り)

インストール完了後、Plugin に含まれる Skills + Commands を呼び出す方法は 3 通り。

### A. 対話セッション (推奨、上位コンサル想定)

```bash
cd /path/to/your-customer-project   # 顧客 PJ 作業ディレクトリ
claude                               # 対話セッション開始
```

プロンプトに直接入力:
```
/tecnos-stride-value:stride-init customer_x --profile enterprise-erp
```

### B. 自然言語で Skill auto-trigger (Plugin spec の本質的 UX)

コマンドを覚えなくても、`description` のキーワードを自然言語に含めれば該当 Skill が自動発火:

| 入力例 | 起動される Skill |
|---|---|
| 「Phase 0 Discovery を始めたい」「BACCM 6 軸を埋めたい」 | `baccm-discovery` |
| 「elicitation technique を選びたい」「インタビュー計画を作って」 | `babok-elicitation` |
| 「Layered Requirements Modeling で actor を整理したい」「BUC を分解したい」 | `layered-context-modelling` |
| 「Phase 0 から Phase 1 に進みたい」「basic_design 生成」 | `upstream-bridge` |
| 「basic_design.md を完成させたい」「canonical schema」 | `basic-design-authoring` |
| 「process.bpmn を書きたい」「業務フローを XML 化」 | `bpmn-authoring` |
| 「Epic に分割すべきか判定して」「複数チームになりそう」 | `epic-decomposition` |

これは「**コンサルが BABOK / Layered Requirements Modeling の専門用語を覚えなくても起動できる**」という設計意図 (manual/51 §3) の実装。

### C. Headless 一発実行 (CI / 自動化向け)

```bash
claude -p --dangerously-skip-permissions \
  "/tecnos-stride-value:stride-init customer_x --profile enterprise-erp"
```

## 3. Skills 7 個の使い方

各 Skill は `description` 内のキーワードで Claude が auto-trigger します。コンサルが対応 Slash Command を実行する、または自然言語でキーワードを含めれば起動します。

| Skill | auto-trigger キーワード | 役割 |
|---|---|---|
| `baccm-discovery` | Phase 0 / Discovery / BACCM / 需要 / 価値 / ステークホルダー | BACCM 6 軸対話で Phase 0 Discovery 完成 |
| `babok-elicitation` | Elicit / インタビュー / ワークショップ / technique | 50 technique から 5 件推奨 |
| `layered-context-modelling` | Context Modelling / Layered Requirements Modeling / actor / usecase / state | 4-layer Requirements Architecture / 5-sheet structure完成 |
| `upstream-bridge` | Phase 0 → 1 / basic_design 生成 / Phase 1 設計 | basic_design.md skeleton + links populate |
| `basic-design-authoring` | basic_design.md 作成 / canonical schema | basic_design.md 全セクション完成 |
| `bpmn-authoring` | BPMN / process.bpmn / 業務フロー | BPMN MUST-DO 厳守で process.bpmn 完成 |
| `epic-decomposition` | Epic / 複数チーム / feature_breakdown | Epic 階層判定 + 必要時のみ生成 |

## 4. Commands 9 個の使い方 (実機 runtime namespace)

claude plugin runtime は **`/<plugin-name>:<command-file-stem>`** の形式で namespace を生成するため、本 Plugin の commands は実際には以下の名前で利用します:

```
/tecnos-stride-value:stride-init <feature_name> [--profile <P>]      # Step 1: scaffold
/tecnos-stride-value:stride-discovery <feature_name>                 # Step 2: BACCM 6 軸
/tecnos-stride-value:stride-elicit <feature_name>                    # Step 3: BABOK Elicitation
/tecnos-stride-value:stride-context-model <feature_name>             # Step 4: Layered Context Modelling
/tecnos-stride-value:stride-validate <feature_name>                  # Step 5: 完全性チェック
/tecnos-stride-value:stride-bridge <feature_name>                    # Step 6: Phase 0 → 1 接続
/tecnos-stride-value:stride-design <feature_name>                    # Step 7: basic_design + process.bpmn
/tecnos-stride-value:stride-epic-init <EPIC_ID> [--features <list>]  # Step 8 (任意): Epic 階層
/tecnos-stride-value:stride-handoff <feature_name> [--repo <url>]    # Step 9: Claude Code 引き渡し
```

> ⚠️ **設計意図 vs 実機の差**: Phase E プロンプト + 設計意図書では `/stride:init` 形式を想定していたが、Plugin runtime の名前空間生成ルールにより実機では上記の長い形式になります。**Phase F の Plugin polish タスク**で plugin name 短縮 (`stride`) または command file から `stride-` prefix 削除のいずれかで `/stride:init` に近づける予定。本書では**今すぐ動く実機の名前を canonical** として記述します。

## 5. 典型ワークフロー (1 PoC 案件)

1. `/tecnos-stride-value:stride-init customer_master_v2 --profile enterprise-erp` で scaffold
2. 顧客ヒアリング後、`/tecnos-stride-value:stride-discovery customer_master_v2` で BACCM 6 軸対話、BACCM iteration 3 段階で 100% 達成
3. `/tecnos-stride-value:stride-elicit customer_master_v2` で BABOK 50 technique から 5 件選択 + 実施計画策定
4. `/tecnos-stride-value:stride-context-model customer_master_v2` で 4-layer Requirements Architecture / 5-sheet structure完成
5. `/tecnos-stride-value:stride-validate customer_master_v2` で完全性確認 (fail 軸あれば各 skill 再起動で refinement)
6. `/tecnos-stride-value:stride-bridge customer_master_v2` で Phase 0 → 1 接続、basic_design.md skeleton 生成
7. `/tecnos-stride-value:stride-design customer_master_v2` で basic_design.md + process.bpmn 完成
8. (任意) `/tecnos-stride-value:stride-epic-init EPIC-CUSTOMER-MASTER --features customer_master_v2,customer_lookup_api` で Epic 階層
9. `/tecnos-stride-value:stride-handoff customer_master_v2 --repo https://github.com/your-org/your-repo` で GitHub PR draft 作成 → Claude Code 担当者へ引き渡し

> ★ 各ステップで命名空間が長く感じる場合は §2-bis B (自然言語 auto-trigger) を併用してください。例えばステップ 2 は「Phase 0 Discovery を customer_master_v2 で始めたい」と入力すれば `baccm-discovery` skill が起動します。

総所要時間 (enterprise-erp 中規模 PJ 想定): 3-7 営業日 (顧客ヒアリング含む)。

## 6. 顧客 PJ ごとの Project セットアップ (Cowork)

Claude Cowork の Project 機能 + 本 Plugin の併用が推奨:

1. Cowork で **顧客 PJ ごとに Project 作成** (例: `Customer-A_PoC_2026Q2`)
2. Project 内に Plugin を読み込み (`claude plugin install` または Cowork 設定)
3. Project Files に顧客資料 (NDA 締結後の要件定義書、業務フロー図等) をアップロード
4. Plugin の reference_files (Tecnos-STRIDE 本体知識) と Project Files (顧客実データ) が **論理的に分離** されるため、§Rule 15 (顧客実データ保護) 自然準拠
5. 完成成果物 (specs/<feature>/) は `/tecnos-stride-value:stride-handoff` で別 GitHub repo にコミット → Cowork Project には Plugin reference_files の知識のみ残る

## 7. MCP Connectors の設定

`cowork-plugin/.mcp.json` で 2 servers 設定済:

- **filesystem**: `${WORKSPACE}` 配下にアクセス制限
- **github**: `${GITHUB_PERSONAL_ACCESS_TOKEN}` で認証

詳細は [`cowork-plugin/CONNECTORS.md`](../cowork-plugin/CONNECTORS.md) を参照。Fine-grained PAT 推奨 (Contents R/W + PR R/W + Metadata R-only)。

## 8. 更新追従 (reference_files 同期 + Plugin 再 fetch)

Tecnos-STRIDE 本体 (manual / constitution / amendments / policies / templates / SDD 中核) が更新された場合の **2 段階更新フロー**:

### 8.1 reference_files 同期 (Plugin 内コンテンツ)

```bash
bash scripts/sync_cowork_plugin_reference.sh
# 期待出力: ✅ Sync complete. Found: 49 files / ✅ 49 reference files confirmed
```

49 件以外なら exit 1 + 内訳出力 (BLOCKER 検出)。

### 8.2 Plugin 再 fetch (claude CLI 側のキャッシュ更新)

```bash
claude plugin marketplace update tecnos-stride
claude plugin update tecnos-stride-value
# 期待出力: Plugin updated; restart claude session to apply
```

claude セッションを再起動すれば新しい reference_files / Skills / Commands が反映されます。Phase F で公式 marketplace 登録後はリリースサイクルに合わせて月次同期を推奨。

## 9. トラブルシューティング (5 項目以上)

### 9.0 `Unknown command: /stride:init` 等が出る (最頻出)
- 原因: 実機 runtime の namespace は **`/tecnos-stride-value:stride-*`** 形式 (§4 参照)、`/stride:*` 形式は Phase E プロンプトの設計意図でしかない
- 対処: 例えば `/tecnos-stride-value:stride-init <feature> --profile <P>` のように **plugin name + command file stem 連結** で打つ
- Phase F で短縮予定 (plugin name `stride` への変更 or command file の `stride-` prefix 削除)

### 9.1 `claude plugin validate` が FAIL
- 原因: plugin.json の必須項目 (name/version/description/author/license) 不足、または JSON 不正、または `repository` が object (npm 風)
- 対処:
  - `python3 -c "import json; json.load(open('cowork-plugin/.claude-plugin/plugin.json'))"` で JSON 妥当性確認
  - `repository` は **string URL** にする (Anthropic spec 準拠、PR #11 で fix 済)

### 9.2 `/tecnos-stride-value:stride-handoff` で `Forbidden`
- 原因: Fine-grained PAT scope 不足
- 対処: CONNECTORS.md §2 の必要 scope (Contents R/W + PR R/W + Metadata R) を再確認、PAT 再発行

### 9.3 `npx` が見つからない
- 原因: Node.js / npm 未インストール
- 対処: Node.js 18+ をインストール (`brew install node` 等)、`which npx` で確認

### 9.4 Skill が auto-trigger しない
- 原因: コンサルのプロンプト内のキーワードが skill description のキーワード列挙と一致しない
- 対処: §3 のキーワード表を参照、または明示的に `/tecnos-stride-value:<command-name>` (§4) を実行

### 9.5 reference_files 件数ドリフト (49 → N)
- 原因: Tecnos-STRIDE 本体ファイル増減後 sync 未実施
- 対処: `bash scripts/sync_cowork_plugin_reference.sh` 実行、exit 1 なら内訳から原因特定

### 9.6 顧客実データを誤って commit してしまった
- 原因: `/tecnos-stride-value:stride-handoff` 実行時に Cowork Project Files の機密情報が含まれた
- 対処: 即 `git reset HEAD~1` で revert、Hitoshi さんに報告 (§Rule 15 違反)、PAT を即無効化

### 9.7 BPMN MUST-DO 違反
- 原因: incoming/outgoing 不足、XOR Gateway の default 不在、ID 不一致等
- 対処: `cowork-plugin/skills/bpmn-authoring/SKILL.md` の検証チェックリスト全項目を確認、Camunda Modeler で視覚確認

## 10. Phase 1 完成後の Claude Code 引き渡し

★ **事前準備** (handoff 利用前に環境変数を設定):
```bash
export GITHUB_TOKEN="<fine-grained-PAT>"   # Contents R/W + PR R/W + Metadata R-only (CONNECTORS.md §2)
export WORKSPACE="$(pwd)"                   # filesystem MCP のアクセス制限ディレクトリ
```

`/tecnos-stride-value:stride-handoff <feature_name>` 実行後:

1. GitHub に `feature/FEAT-<FEATUREID>-<feature_name>` ブランチ + PR draft が作成される
2. Claude Code 担当者 (Tecnos-STRIDE 技術者) に通知
3. Claude Code 担当者が PR pull、Phase 2 (Specify) → Phase 3 (Tasking) → Phase 4 (Execute) → Final で実装

引き渡し時の確認事項:
- BACCM 6 軸完成度 (`/tecnos-stride-value:stride-validate` の最終結果)
- profile (enterprise-erp / saas-integration / prototype)
- coverage_tier (critical / standard / experimental)
- 関連顧客資料の有無 (Cowork Project 側に保持、PR には含めない)

## 10-bis. Anthropic Cowork (web) で利用する場合 (実機未検証、参考)

本書 §2.1 はローカル Claude Code CLI (Mac / Linux / Windows) での実機検証済 install 手順です。Anthropic Cowork (web 版、claude.ai/projects 等) でも同 Plugin を利用するには、Cowork の UI で marketplace 登録が必要 (Anthropic 側仕様):

1. Cowork セッション or Project を開く
2. Project Settings → Plugins / Marketplaces 画面に移動
3. 「Add marketplace」で **GitHub URL** を入力: `https://github.com/tecnos-japan-cbp/tecnos-stride`
4. 表示された Plugin 一覧から `tecnos-stride-value` を **Install**
5. Project に紐付けたら、コンサルが自然言語で対話開始

⚠️ **重要 caveat**: Cowork web の Plugin loading 仕様は Anthropic 側の更新で頻繁に変わる可能性があります。**本書執筆時点で claude.ai 側 Plugin loading は実機検証していません**。最新の正確な手順は Anthropic 公式ドキュメントを優先してください。実機検証は §2.1 の **CLI 経由のみ完了済**です。

## 11. Attributions

- **BABOK v3 (IIBA)** — framework backbone (KA4 Elicitation / KA6 Strategy Analysis / KA7 Requirements Analysis / KA8 Solution Evaluation)、fair-use, names and section refs only
- **Layered Requirements Modeling ((concept reference, no proprietary brand))** — structural integrity (4-layer)、fair-use, layer/diagram names only
- **value-driven discovery (philosophical foundation)** — philosophical inspiration (value canvas / goal tree)、fair-use, model names only
- **Anthropic Knowledge Work Plugins** — Plugin SDK reference、MIT
- **Camunda 8 / Zeebe** — BPMN 2.0 + Zeebe 拡張仕様 (process.bpmn 構造)、fair-use, spec refs only
