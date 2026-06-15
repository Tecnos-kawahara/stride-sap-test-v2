# WI-VALF01-012: GitHub MCP 接続検証 Evidence (改善要望-11)

**Status:** scaffold (実機検証手順 + 期待 schema を記録、実 GitHub API 接続検証は Phase F PR merge 後に Hitoshi さん follow-up)
**Phase F WI:** WI-VALF01-012
**改善要望:** 改善要望-11 (Plugin 配布時に GitHub MCP が確実に動作することを保証したい)
**AC:** AC-US-FEATVALF01-012-01

## 1. 検証目的

cowork-plugin/.mcp.json に定義された **GitHub MCP server** (filesystem MCP と並んで設定) が、上位コンサル環境で確実に動作することを実機検証で保証する。Plugin v0.2.0-stable 配布開始前に GitHub MCP の以下機能が動くことを evidence として記録:

1. **issue 取得** (read): `tecnos-japan-cbp/tecnos-stride` の issue list / issue detail
2. **PR 取得** (read): PR list / PR detail / PR diff
3. **commit 確認** (read): commit history / commit diff
4. **(handoff) feature ブランチ push + PR draft 作成** (write): WI-VALF01-001 の handoff workflow が依存

## 2. 検証手順

### 2-A. 前提環境

```bash
# (1) Plugin v0.2.0-stable 候補 install 済
claude plugin install tecnos-stride-value@tecnos-stride

# (2) GitHub Personal Access Token 環境変数設定済
# scope: repo (read/write) + pull_request (read/write) + metadata (read)
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxx..."

# (3) cowork-plugin/.mcp.json に github MCP server が定義されている
cat cowork-plugin/.mcp.json | python3 -c 'import json, sys; d=json.load(sys.stdin); assert "github" in d.get("mcpServers", {}), "github MCP server 未定義"; print("✅ github MCP server defined")'
```

### 2-B. 実 API 検証 (read 系、Hitoshi さん実施)

Cowork セッション内で以下を順次実行:

```
# (1) issue 取得 (read-only)
mcp__github__list_issues({"owner": "tecnos-japan-cbp", "repo": "tecnos-stride", "state": "all", "limit": 5})

# (2) PR 取得 (read-only)
mcp__github__list_pulls({"owner": "tecnos-japan-cbp", "repo": "tecnos-stride", "state": "all", "limit": 5})

# (3) commit 確認 (read-only)
mcp__github__get_commit({"owner": "tecnos-japan-cbp", "repo": "tecnos-stride", "ref": "main"})
```

### 2-C. 実 API 検証 (write 系、Hitoshi さん実施)

`/stride:handoff` workflow が GitHub MCP 経由で feature ブランチ push + PR draft 作成できることを確認するため、テスト用 private repo を準備:

```
# 推奨 (Phase F PR merge 後の Hitoshi さん follow-up):
# (1) Test repo 作成: tecnos-japan-cbp/cowork-plugin-handoff-test (private)
# (2) Cowork セッションで /stride:handoff 実行:
#     /tecnos-stride-value:stride-handoff test_handoff_001 \
#       --repo https://github.com/tecnos-japan-cbp/cowork-plugin-handoff-test
# (3) GitHub UI で feature ブランチ + PR draft が作成されたことを目視確認
```

## 3. 期待される Sanitized Snapshot Schema

実機検証完了後、以下の sanitized snapshot を本ファイルに追記する想定。

### 3-A. issue list (期待 schema、サニタイズ後の例)

```json
{
  "items": [
    {
      "number": 123,
      "title": "<sanitized internal issue title>",
      "state": "open",
      "labels": ["work-item"],
      "created_at": "<ISO 8601>"
    }
  ]
}
```

(注: 顧客名 / 担当者名 / 案件 ID は §Rule 15-B 準拠でサニタイズ。`<sanitized internal issue title>` は実 issue title から固有名詞を除去した匿名化値で置換する)

### 3-B. PR list (期待 schema、サニタイズ後の例)

```json
{
  "items": [
    {
      "number": 13,
      "title": "<sanitized PR title>",
      "state": "merged",
      "merged_at": "<ISO 8601>"
    }
  ]
}
```

### 3-C. handoff PR draft 作成 (期待 schema)

```json
{
  "pr_url": "https://github.com/tecnos-japan-cbp/cowork-plugin-handoff-test/pull/<N>",
  "branch": "feature/FEAT-<id>-test_handoff_001",
  "draft": true,
  "title": "feat(test_handoff_001): Phase 0/1 — <sanitized>",
  "body_excerpt": "<sanitized handoff request body>"
}
```

## 4. 既知制約

- **AI 単独では実機検証完了不可**: GitHub Personal Access Token は人間環境変数、private repo `cowork-plugin-handoff-test` 作成権限も人間。AI は scaffold + 検証手順 + 期待 schema を提供するに留まる。
- **実 dogfooding は Phase F PR merge 後**: Hitoshi さん follow-up として、本 evidence file に実検証結果 (sanitized snapshot) を追記して closure。
- **Q-101 関連**: Phase G で marketplace 公開する際、本 MCP 検証 evidence は登録要件の 1 つとして再利用。

## 5. Closure 条件

以下 4 件すべてが完了で本 evidence file は **completed** ステータスに移行:

- [ ] 2-A 環境準備完了 (Hitoshi さん)
- [ ] 2-B read 系 3 API 検証完了 (sanitized snapshot を §3 に追記)
- [ ] 2-C write 系 (handoff) 検証完了 (PR draft URL を §3-C に記録)
- [ ] state.yaml `final.evidence_pack_done: true` への更新

## 6. References

- Phase F prompt §4-3-C (GitHub MCP 実機検証)
- cowork-plugin/.mcp.json (github MCP server 設定)
- cowork-plugin/CONNECTORS.md §2 (PAT scope) + §4 (トラブルシューティング)
- cowork-plugin/commands/stride-handoff.md (handoff workflow、WI-VALF01-001 で改修)
- specs/val_f01/spec.md US-FEATVALF01-012 + AC-US-FEATVALF01-012-01

> Phase F (WI-VALF01-012) で MCP 検証手順 + scaffold を整備。実 dogfooding は Hitoshi さん follow-up。
