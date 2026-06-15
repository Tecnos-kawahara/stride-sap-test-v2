# Migration Guide: v1.2.1-tecnos → v1.2.2-tecnos

本ガイドでは、`templates_v1.2.1-tecnos` から `templates_v1.2.2-tecnos` への移行手順を説明します。

---

## 1. 変更サマリー

| カテゴリ | 変更内容 | 影響度 | 対応必須 |
|----------|----------|--------|----------|
| **Docs/Spec** | `use_cases` / `acceptance` の命名を全ドキュメントで統一 | 低 | 推奨（例・説明の整合） |
| **IDs** | `TS-*` を 2桁に統一（`TS-INT-01`） | 低 | 推奨（例・説明の整合） |
| **Paths** | feature ディレクトリを `snake_case` に統一 | 中 | Yes（lint ルールに一致） |
| **Coverage Policy** | `coverage_policy` のキーを Plan テンプレート準拠に一本化 | 中 | Yes（旧キー使用時のみ） |
| **Cheatsheet** | Gate表を Constitution と一致 | 低 | No |

---

## 2. Breaking Changes

### 2.1 feature ディレクトリ名の統一（snake_case）

**変更点**: 例・テンプレートの `specs/<feature_name>/` を snake_case に統一。

**対応**:
- 既存が `specs/feature-name/` などの場合はリネーム。
- frontmatter / inputs / links のパスも合わせて更新。

### 2.2 Coverage Policy のキー統一

**変更点**: ドキュメント中の Coverage Policy を Plan テンプレート準拠に統一。

```yaml
# v1.2.1 の旧表記（ドキュメントに残っていた例）
code_coverage:
  lib: { target_pct: 85, minimum_pct: 75 }
  components: { target_pct: 60, minimum_pct: 50 }

# v1.2.2 の正規表記
code_coverage_targets:
  - scope: "LIB-*"
    line_pct: 85
    branch_pct: 75
  - scope: "CMP-*"
    line_pct: 60
    branch_pct: 50
code_coverage_exclusions:
  - path_glob: "**/generated/**"
    reason: "Generated code"
    mitigation: "Contract/Integration tests cover behavior"
```

**対応**: 旧キーを使用している場合は上記の正規表記に移行。

### 2.3 Test ID の桁数統一

**変更点**: `TS-*` を 2桁に統一（Constitution の正規表現と一致）。

**対応**: 例・テンプレートの `TS-INT-001` などを `TS-INT-01` 形式に揃える。

---

## 3. speckit-lint 変更

v1.2.2 で新しい Failure Code は追加されていません。検証ルールは v1.2.1 から変更なしです。

---

## 4. 移行チェックリスト

- [ ] feature ディレクトリが `snake_case` になっている
- [ ] frontmatter / inputs / links のパスが新ディレクトリに一致している
- [ ] `TS-*` が 2桁で記述されている
- [ ] `coverage_policy` のキーが Plan テンプレート準拠になっている
- [ ] `use_cases` / `acceptance` に命名が統一されている

---

## 5. 互換性メモ

- `coverage_policy` の enforcement 挙動は v1.2.1 と同じです。
- AC Coverage は `coverage_policy` の有無に関わらず常に検証されます。

---

> End of MIGRATION.md
