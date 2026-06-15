# MCP Connectors — Tecnos-STRIDE VALUE Cowork Plugin

このプラグインは MCP (Model Context Protocol) を使って **filesystem** と **github** の 2 servers に接続します。`/stride:handoff` コマンドが動作するには `github` MCP の設定が必須です。

## 1. filesystem MCP

`${WORKSPACE}` 配下のファイルシステムへ読み書き可能にします。Cowork セッションが起動したワークスペースに対するアクセスのみ許可。

### 環境変数

| 変数 | 用途 | 既定値 |
|---|---|---|
| `WORKSPACE` | filesystem アクセス制限の root | カレントディレクトリ |

### `.mcp.json` 抜粋

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${WORKSPACE}"]
    }
  }
}
```

## 2. github MCP

GitHub API 経由でブランチ push、PR 作成、コミット等を行います。`/stride:handoff` コマンドの裏側で動作します。

### 必要な PAT scope (最小権限)

GitHub Personal Access Token (Fine-grained PAT 推奨) は以下の scope のみで動作します:

| Scope | 用途 |
|---|---|
| `Contents: Read & Write` | feature ブランチ push、ファイル更新 |
| `Pull requests: Read & Write` | PR draft 作成 |
| `Metadata: Read-only` | リポジトリメタデータ取得 |

**最小権限の原則**: `Administration` / `Workflows` / `Environments` の scope は不要です。Fine-grained PAT で対象リポジトリのみに権限を限定してください (Tecnos-STRIDE 組織ポリシー準拠)。

### 環境変数

| 変数 | 用途 | 必須 |
|---|---|---|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | github MCP 認証 token | はい |

### `.mcp.json` 抜粋

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

## 3. セットアップ手順

```bash
# 1. PAT の発行 (Fine-grained PAT、上記 3 scope のみ)
# GitHub > Settings > Developer settings > Personal access tokens > Fine-grained tokens

# 2. 環境変数設定 (~/.zshrc 等に永続化推奨)
export GITHUB_TOKEN="<your-fine-grained-pat>"
export WORKSPACE="$(pwd)"

# 3. Plugin 動作確認
claude plugin validate ./cowork-plugin
```

## 4. トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `/stride:handoff` で `Forbidden` | PAT scope 不足 | §2 の必要 scope (Contents R/W + PR R/W + Metadata R) を再確認 |
| `npx` が見つからない | Node.js / npm 未インストール | Node.js 18+ をインストール、`which npx` で確認 |
| filesystem MCP が起動しない | `${WORKSPACE}` 未設定 | `export WORKSPACE="$(pwd)"` を実行してから再試行 |
| github MCP が `unauthorized` | 環境変数 `GITHUB_PERSONAL_ACCESS_TOKEN` 未設定 | `export GITHUB_TOKEN="..."` 後に Cowork セッション再起動 |
| `/stride:handoff` で `[BLOCKER] §Rule 15-B sanitize hit` | Phase F (WI-VALF01-004) のサニタイズ自動 grep が `upstream/*.yaml` + `lessons_learned` から顧客名/担当者名/金額/契約番号等の禁止キーワードを検出 | 該当箇所を抽象化 (固有名詞 → 一般語) して再実行。サニタイズパターンは Tecnos 内部固有名詞ベースに限定 (汎用業務語は誤検出されない) |
| `/stride:handoff` で `[BLOCKER] missing required section` | basic_design.md / process.bpmn / claude_code_handoff.md / acceptance_criteria.yaml の 4 ファイルのいずれかが欠落、または basic_design.md の必須セクション (`# 0. Canonical Basic Design` / `basic_design:` / `context:` / `scope:` / `bpmn_descriptions:` / `traceability_rows:` / `basic_design_gate_check:`) が不足 | `/stride:validate` で完全性を再チェックし、不足箇所を補完してから再実行 |
| `/stride:design` で `ImportError: No module named 'yaml'` 等 | Phase F (WI-VALF01-013) の dev 依存自動検出が未 install module を発見 | 提案された `pip install pyyaml jsonschema markdown jinja2` を実行してから再試行 |
| `/stride:export-html` で "Tecnos-STRIDE 本体 helper not found" | DR-103 により `scripts/build_basic_design_html.py` は Tecnos-STRIDE 本体 (`scripts/`) 配下に配置、Plugin に同梱されない設計 | Tecnos-STRIDE 本体を clone (`git clone https://github.com/tecnos-japan-cbp/tecnos-stride.git`) してから再実行 |
| GitHub MCP の実機検証 evidence を取得したい (Phase G 入口準備) | WI-VALF01-012 の検証手順を参照 | `docs/evidence/phase_f/wi_012_mcp_validation.md` の §2-A〜2-C に従って Hitoshi さんが follow-up 実施 (Issue #15) |

## 5. 参考リンク

- [MCP server-filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)
- [MCP server-github](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [Anthropic Plugin spec](https://github.com/anthropics/knowledge-work-plugins) (Markdown + JSON のみ、コードなし)
