---
description: 完璧な dev 環境を備えた新規顧客 PoC リポジトリを 1 コマンドで bootstrap。GitHub MCP で新規 private repo 作成 + Tecnos-STRIDE template から派生 + stride new-project 実行 + Phase Gate hooks + .claude/settings.json + GitHub Actions CI + branch protection を全自動で整え、Cowork (上流) → Claude Code (Phase 4 着手) の継ぎ目のない接続を実現。
argument-hint: "<repo_name> [--org <github_org>] [--profile enterprise-erp|saas-integration|prototype] [--scale starter|standard|enterprise] [--first-feature <feature_name>]"
---

# /stride:bootstrap-repo

Tecnos-STRIDE VALUE Cowork Plugin から **「完璧な開発環境を備えた新規顧客 PoC リポジトリ」を 1 コマンドで作成** します。Cowork で上流ドキュメント (Phase 0/1) を作成する前提条件として、Claude Code 担当者が **clone 即時 Phase 4 (Execute) 着手可能** な状態を bootstrap します。

> Phase G UX-prep 新規 (PR-D): Cowork (上位コンサル) → Claude Code (実装) の **継ぎ目のない接続** を実現する Repository Bootstrap Command。

## Usage

```
/stride:bootstrap-repo <repo_name> [--org <github_org>] [--profile <P>] [--scale <S>] [--first-feature <F>]
```

### 引数

| 引数 | 必須/任意 | 説明 | デフォルト |
|---|---|---|---|
| `<repo_name>` | 必須 | 新規リポジトリ名 (snake_case 推奨、例: `<client>_supply_management`) | — |
| `--org <github_org>` | 任意 | GitHub Organization 名 (例: `tecnos-japan-cbp`) | コンサル個人アカウント |
| `--profile <P>` | 任意 | enterprise-erp / saas-integration / prototype | enterprise-erp |
| `--scale <S>` | 任意 | starter / standard / enterprise (Monorepo scale) | starter |
| `--first-feature <F>` | 任意 | 同時に作成する初期 feature 名 (snake_case) | (省略時は repo bootstrap のみ) |

### 例

```
/stride:bootstrap-repo my_client_supply_management --org tecnos-japan-cbp --profile enterprise-erp --scale standard --first-feature customer_a_supply_management
```

## Workflow

### 1. Validate Input

- `<repo_name>` は GitHub repo 命名規約 (英小文字 / 数字 / ハイフン / アンダースコア、64 文字以内)
- `--org` 指定時は **コンサル GitHub アカウントが該当 Organization で repo create 権限** を持つこと
- `--profile` / `--scale` の妥当性チェック
- 既存リポジトリ名衝突チェック (`gh repo view <org>/<repo_name>` で existence 確認 → 衝突時 [BLOCKER])

### 2. ★ Pre-flight 環境確認 (Phase F WI-013 dev 依存自動化準拠)

```bash
# Tecnos-STRIDE 本体 clone 済前提
if [ ! -f sdd-templates/bin/stride ]; then
  echo "⛔ [BLOCKER] Tecnos-STRIDE 本体未 clone。"
  echo "対処: git clone https://github.com/tecnos-japan-cbp/tecnos-stride.git ~/work/tecnos-stride"
  exit 1
fi

# 必要 CLI 確認
for cmd in gh git python3; do
  command -v $cmd >/dev/null 2>&1 || { echo "⛔ [BLOCKER] $cmd 未 install"; exit 1; }
done

# GitHub 認証確認 (gh auth status)
gh auth status >/dev/null 2>&1 || { echo "⛔ [BLOCKER] gh auth 未認証。`gh auth login` を実行"; exit 1; }

# Python dev 依存 (Phase F WI-013 と同じパターン、unfortunately not auto-installable)
for module in yaml jsonschema; do
  python3 -c "import ${module}" 2>/dev/null || {
    echo "ℹ Python module ${module} 未 install。対処:"
    echo "    pip install pyyaml jsonschema"
    echo "コンサル承認後、再度 /tecnos-stride-value:stride-bootstrap-repo を実行してください。"
    exit 2
  }
done

echo "✅ pre-flight checks passed"
```

### 3. ★ GitHub MCP 経由 新規 private repo 作成

```bash
REPO_NAME="<repo_name>"
ORG="${ORG:-$(gh api user --jq '.login')}"

# 3-A. リポジトリ衝突チェック
if gh repo view "${ORG}/${REPO_NAME}" >/dev/null 2>&1; then
  echo "⛔ [BLOCKER] ${ORG}/${REPO_NAME} は既に存在します。"
  echo "対処: 別の repo_name を指定するか、既存リポジトリを使用してください。"
  exit 1
fi

# 3-B. 新規 private repo 作成 (template 経由ではなく clone + new-project でカスタマイズ)
gh repo create "${ORG}/${REPO_NAME}" --private --description "Tecnos-STRIDE-based SDD project: ${REPO_NAME}"

echo "✅ private repo created: https://github.com/${ORG}/${REPO_NAME}"
```

### 4. ★ Local clone + stride new-project でカスタマイズ

```bash
# 4-A. Tecnos-STRIDE template から新規 repo へのコピー (clone + remote 切り替え)
WORKSPACE="${WORKSPACE:-$(pwd)/work}"
mkdir -p "${WORKSPACE}"
cd "${WORKSPACE}"

# Tecnos-STRIDE 本体を template として使用 (shallow clone、history 引き継がない)
git clone --depth 1 https://github.com/tecnos-japan-cbp/tecnos-stride.git "${REPO_NAME}"
cd "${REPO_NAME}"

# 4-B. .git を削除して新しい history を開始
rm -rf .git
git init
git remote add origin "https://github.com/${ORG}/${REPO_NAME}.git"

# 4-C. stride new-project でカスタマイズ
sdd-templates/bin/stride new-project "${REPO_NAME}" \
  --org "${ORG}" \
  --scale "${SCALE:-starter}" \
  ${FIRST_FEATURE:+--first-feature "${FIRST_FEATURE}"} \
  ${PROFILE:+--profile "${PROFILE}"}

echo "✅ stride new-project complete (sample 削除 + 名前置換 + Phase Gate hooks + CI 設定)"
```

### 5. ★ Phase Gate hooks + .claude/settings.json deploy

```bash
# 5-A. .claude/settings.json を Plugin 推奨値で配備 (Phase F WI-015 の .claude-template から)
mkdir -p .claude
if [ -f cowork-plugin/.claude-template/settings.json ]; then
  cp cowork-plugin/.claude-template/settings.json .claude/settings.json
  echo "✅ .claude/settings.json deployed (Plugin 推奨値)"
fi

# 5-B. Phase Gate hooks (stride hooks --tool claude --force)
sdd-templates/bin/stride hooks --tool claude --force 2>&1 | tail -3
echo "✅ Phase Gate hooks installed"
```

### 6. ★ GitHub Actions CI deploy (Phase F WI-002 の cowork-plugin-validate.yml + 一般 CI)

```bash
# 6-A. .github/workflows/ は git clone 時に既に template から copy 済
# Phase F の cowork-plugin-validate.yml も含まれる

# 6-B. CI 動作確認の placeholder commit
ls .github/workflows/ | head -5
echo "✅ GitHub Actions CI configured (cowork-plugin-validate.yml + ci.yml + stride-*.yml)"
```

### 7. ★ Initial commit + push + branch protection

```bash
# 7-A. Initial commit
git add -A
git commit -m "chore: bootstrap ${REPO_NAME} from Tecnos-STRIDE template

Bootstrapped via /tecnos-stride-value:stride-bootstrap-repo:
- profile: ${PROFILE:-enterprise-erp}
- scale: ${SCALE:-starter}
- first feature: ${FIRST_FEATURE:-(none)}

Cowork コンサルから Claude Code 担当者への引き渡し用 PoC repo。
Plugin: tecnos-stride-value@0.2.0-stable (Cowork Plugin)
Methodology: Tecnos-STRIDE 6.0.0-tecnos-stride-value (Phase A-F 完成形)
"

# 7-B. main branch push
git branch -M main
git push -u origin main

# 7-C. Branch protection (main: PR 必須 + CI green 必須)
gh api -X PUT "repos/${ORG}/${REPO_NAME}/branches/main/protection" \
  --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["quality", "validate-plugin", "stride-lint"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
echo "✅ main branch protection enabled (PR + CI green required)"
```

### 8. ★ (任意) Linear / GitHub Project V2 binding (stride new-project --linear-project / --github-project)

```bash
# stride new-project が既に処理済なら skip
# 認証済 (gh auth + LINEAR_API_KEY) の場合のみ自動 binding
```

### 9. Output

stdout に以下を表示:

```
✅ Repository Bootstrap 完了

📦 Repository: https://github.com/<org>/<repo_name>
🌿 Branch: main (protected: PR + CI green required)
📂 Local clone: <WORKSPACE>/<repo_name>
🎯 Profile: <profile>
🔧 Scale: <scale>
${FIRST_FEATURE:+🚀 Initial feature: ${FIRST_FEATURE} (specs/${FIRST_FEATURE}/ scaffold 済)}

次のステップ (Cowork コンサル):
  1. Cowork で上流ドキュメント作成:
     /tecnos-stride-value:stride-discovery <feature_name>
     /tecnos-stride-value:stride-elicit <feature_name>
     /tecnos-stride-value:stride-context-model <feature_name>
     /tecnos-stride-value:stride-validate <feature_name>
     /tecnos-stride-value:stride-bridge <feature_name>
     /tecnos-stride-value:stride-design <feature_name>
     /tecnos-stride-value:stride-handoff <feature_name>
     /tecnos-stride-value:stride-tasking <feature_name>

次のステップ (Claude Code 担当者):
  1. git clone https://github.com/<org>/<repo_name>
  2. ↑ で作成された PR / Issue を確認
  3. 即時 Phase 4 (Execute) 着手 — Phase Gate hooks + CI が機械保護
```

## 10. Notes / Limitations

- **AI 単独では完遂困難な部分**: GitHub Personal Access Token + Org への repo create 権限 + LINEAR_API_KEY (任意) は人間環境が前提。AI は **scaffold + 検証手順 + 期待 output schema** を提供するに留まる
- **DR-103 (Phase F)**: HTML helper (`scripts/build_basic_design_html.py`) は Tecnos-STRIDE 本体配下、Plugin 同梱せず — 本 bootstrap で clone した先には含まれている
- **DR-104 (Phase F)**: 顧客固有 PoC 関連の手順 / lessons は本 repo (`memory/lessons_learned/...`) で集中管理、Tecnos-STRIDE template repo は不変
- **§Rule 15-B サニタイズ**: bootstrap した repo の `upstream/*.yaml` + `lessons_learned` には顧客実データを含めない (Phase F WI-004 の handoff サニタイズ自動 grep が機械検証)
- **branch protection の "contexts"**: 本 PoC repo に GitHub Actions が初回 trigger される前は branch protection 設定が拒否される可能性。初回 commit が push された後の **2 回目以降の commit** で protection 有効化される
- **Tecnos-STRIDE 本体 VERSION 連携**: bootstrap した PoC repo は Tecnos-STRIDE 本体 6.0.0-tecnos-stride-value + Plugin 0.2.0-stable を embedded、本体が bump されたら手動で `git pull` で取り込み

## 11. Trouble shooting

| 症状 | 原因 | 対処 |
|---|---|---|
| `gh repo create` で "name already exists" | Org に同名 repo が既存 | 別の `<repo_name>` 指定、または既存 repo 利用 |
| `gh auth status` で unauthorized | gh CLI 未認証 | `gh auth login` を実行 |
| `pip install` 必要 | Python dev 依存 (pyyaml/jsonschema) 未 install | `pip install pyyaml jsonschema` |
| branch protection 設定で "Branch not protected" エラー | 初回 push で main branch 未確立 | initial commit + push 後に protection を再設定 |
| Tecnos-STRIDE 本体 clone 路径不明 | bootstrap 実行 directory が不正 | Tecnos-STRIDE 本体内で実行する (`cd ~/work/tecnos-stride`) |

## 12. References

- 本体 helper: `sdd-templates/bin/stride new-project --help` の全引数を継承
- Phase F WI-002: `.github/workflows/cowork-plugin-validate.yml` (CI 統合)
- Phase F WI-013: stride-design dev 依存自動化 (本コマンドも同パターン採用)
- Phase F WI-015: `cowork-plugin/.claude-template/settings.json` (推奨値配布元)
- Phase F manual: [`../manual/52_phase_f_lessons_learned.md`](../manual/52_phase_f_lessons_learned.md) §9 (fc-sd 相当の Plugin 導入手順)
- Plugin runtime: [`../README.md`](../README.md) §1.1 Architecture Notes (Plugin runtime SSoT vs SDD contracts vs OpenAPI)

> Phase G UX-prep (PR-D) で新設。Cowork (上流) → Claude Code (Phase 4 着手) の **継ぎ目のない接続** を 1 コマンドで実現。
