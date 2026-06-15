# Migration Guide: v4.6.x -> v4.7.0-tecnos-stride

本ガイドは、`v4.6.x-tecnos-stride` 系から `v4.7.0-tecnos-stride` へ更新する際の差分だけを扱います。
旧 1.x / 2.x / 3.x 系からの長距離移行は [CHANGELOG.md](./CHANGELOG.md) の該当リリースを順に確認してください。

---

## 1. 何が変わったか

| 項目 | v4.6.x | v4.7.0 |
|------|--------|--------|
| Enterprise Hierarchy の有効化 | 明確な CLI 統合なし | `config/enterprise.yaml` で明示的に On/Off |
| Epic 操作 | Python ツール直呼び中心 | `stride epic init|validate|gates|features|progress|list` |
| Epic 配下 Feature 作成 | 手動で `epic_ref` / `team_id` 記入 | `stride init <feature> --epic <EPIC_ID> [--team <TEAM_ID>]` |
| Enterprise lint | `stride_lint_enterprise.py` 単独実行中心 | `stride lint --enterprise` / `stride lint --all --enterprise` |
| Shared Contract Registry | 参照説明が揺れていた | `shared/contracts/CONTRACT_REGISTRY.yaml` に統一 |

---

## 2. 先に押さえるべき前提

### 2.1 `--scale enterprise` と Enterprise Hierarchy は別物

- `stride init --scale enterprise` は **Monorepo / CI の規模設定**です
- Epic/Feature 階層を有効化するには **別途** `sdd-templates/config/enterprise.yaml` が必要です

```yaml
enterprise:
  enabled: true
```

### 2.2 Enterprise Hierarchy を使わないプロジェクトは従来どおり動く

- `stride init <feature>`
- `stride lint specs/<feature>/`
- `stride lint --all`

これらは `enterprise.enabled: false` のままでもそのまま使えます。

---

## 3. 必須更新

### 3.1 テンプレート / ツール一式を v4.7.0 に更新

最低限、以下は同じリビジョンに揃えてください。

- `sdd-templates/bin/stride`
- `sdd-templates/tools/stride_lint.py`
- `sdd-templates/tools/stride_lint_enterprise.py`
- `sdd-templates/tools/epic_validator.py`
- `sdd-templates/tools/epic_progress_aggregator.py`
- `sdd-templates/templates/epic_*`
- `sdd-templates/templates/shared_contract_registry_template.yaml`
- `sdd-templates/config/enterprise.yaml`

### 3.2 Enterprise Hierarchy を使うなら `config/enterprise.yaml` を追加

```bash
cat > sdd-templates/config/enterprise.yaml <<'YAML'
enterprise:
  enabled: true
YAML
```

### 3.3 ドキュメント / 手順書を CLI ベースに更新

旧運用:

- `python3 sdd-templates/tools/epic_validator.py ...`
- `python3 sdd-templates/tools/stride_lint_enterprise.py ...`
- 手動で `basic_design.md` の `epic_ref` / `team_id` を編集

新運用:

- `stride epic ...`
- `stride init <feature> --epic ...`
- `stride lint --enterprise`

---

## 4. Enterprise Hierarchy を使うプロジェクトの移行手順

### 4.1 Epic を CLI 管理へ寄せる

```bash
stride epic init EPIC-ORDER
stride epic validate EPIC-ORDER
stride epic gates EPIC-ORDER
stride epic features EPIC-ORDER
stride epic progress EPIC-ORDER
```

### 4.2 Feature 作成を `stride init --epic` に統一

```bash
stride init order_import --epic EPIC-ORDER --team TEAM-A
```

- Epic に team が 1 つだけなら `team_id` は自動設定
- 複数 team の Epic では `--team` 必須
- 存在しない team を指定すると早期に失敗

### 4.3 CI を enterprise-aware にする

Enterprise Hierarchy を使うなら、通常の lint に加えて Epic 検証も CI へ入れます。

```bash
stride lint --all --enterprise
```

---

## 5. 動作変更として意識すべき点

### 5.1 `stride lint --enterprise` は明示要求扱い

以下の場合は warning ではなく失敗します。

- `sdd-templates/config/enterprise.yaml` が無い
- `enterprise.enabled: true` になっていない
- enterprise 拡張モジュールを import できない

### 5.2 単一 Feature lint では Epic 全体を検証しない

- `stride lint specs/<feature>/ --enterprise` はその Feature の enterprise 拡張検証のみ
- `stride lint --all --enterprise` のときだけ Epic 検証も追加される

### 5.3 Shared Contract Registry の場所は固定

現在の正しいパスは以下です。

```text
shared/contracts/CONTRACT_REGISTRY.yaml
```

---

## 6. 更新チェックリスト

### 共通

- [ ] `sdd-templates/VERSION` が `4.7.0-tecnos-stride`
- [ ] `sdd-templates/bin/stride` に `epic` サブコマンドがある
- [ ] `sdd-templates/tools/stride_lint.py` に `--enterprise` がある
- [ ] `README / QUICKSTART / CHEATSHEET` が `enterprise.yaml` を案内している

### Enterprise Hierarchy 利用プロジェクトのみ

- [ ] `sdd-templates/config/enterprise.yaml` を配置した
- [ ] `enterprise.enabled: true` を設定した
- [ ] `epics/<EPIC_ID>/` を `stride epic init` で作成した
- [ ] 新規 Feature 作成を `stride init --epic` に統一した
- [ ] CI で `stride lint --all --enterprise` を実行している

---

## 7. 検証コマンド

```bash
# 基本 lint
stride lint specs/<feature>/

# Enterprise 拡張 lint
stride lint specs/<feature>/ --enterprise

# 全体 lint（Epic 検証込み）
stride lint --all --enterprise

# Epic 単体チェック
stride epic validate EPIC-ORDER
stride epic gates EPIC-ORDER
stride epic progress EPIC-ORDER
```

---

## 8. 互換性メモ

- Flat な Feature-only 構成はそのまま維持できます
- `enterprise.yaml` を追加しても `enabled: false` なら従来挙動です
- `--scale enterprise` は v4.7 でも **Monorepo scale の意味のまま**です

---

> End of MIGRATION.md
