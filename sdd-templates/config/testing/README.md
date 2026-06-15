# Testing Configuration Templates

Version: 5.3.3-tecnos-stride

このディレクトリには、各言語のテスト設定テンプレートが含まれています。
プロジェクトで使用する言語に応じて、適切なテンプレートをコピーして使用してください。

---

## AI Agent: 自動依存関係チェック

> **AIエージェントは、テストセットアップ前にツールの存在を確認し、不足していれば自動インストールすること。**

### クイックチェック＆インストール（コピペ用）

```bash
# === Python ===
python -c "import pytest" 2>/dev/null || pip install pytest pytest-cov httpx

# === TypeScript ===
npm list vitest 2>/dev/null || npm install -D vitest @vitest/coverage-v8

# === Rust ===
cargo tarpaulin --version 2>/dev/null || cargo install cargo-tarpaulin

# === Go ===
golangci-lint --version 2>/dev/null || go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# === Playwright (E2E) ===
npx playwright --version 2>/dev/null || { npm install -D @playwright/test && npx playwright install chromium; }
```

> 詳細は `agent_docs/testing.md` の「AI Agent Pre-Flight Checklist」を参照。

---

## 使用方法

### 1. TypeScript プロジェクト

```bash
# vitest.config.ts をプロジェクトルートにコピー
cp sdd-templates/config/testing/vitest.config.ts ./

# package.json に scripts を追加
npm pkg set scripts.test:unit="vitest run"
npm pkg set scripts.test:integration="vitest run --config vitest.integration.config.ts"
npm pkg set scripts.test:watch="vitest"

# 依存関係をインストール
npm install -D vitest @vitest/coverage-v8 @testing-library/react
```

### 2. Python プロジェクト

```bash
# pyproject.toml のテスト設定セクションを参照
cat sdd-templates/config/testing/pyproject.toml.snippet

# conftest.py テンプレートをコピー
cp sdd-templates/config/testing/python/conftest.py.template \
   specs/<feature>/tests/conftest.py

# APIテストテンプレートをコピー
cp sdd-templates/config/testing/python/test_api.py.template \
   specs/<feature>/tests/test_<resource>.py

# 依存関係をインストール
pip install pytest pytest-cov httpx ruff mypy
```

### 3. Rust プロジェクト

```bash
# Cargo.toml のテスト設定を参照
cat sdd-templates/config/testing/Cargo.toml.snippet

# カバレッジツールをインストール
cargo install cargo-tarpaulin cargo-audit
```

### 4. Java プロジェクト (Gradle)

```bash
# build.gradle.kts のテスト設定を参照
cat sdd-templates/config/testing/build.gradle.kts.snippet

# Gradle wrapper がある場合
./gradlew test jacocoTestReport

# 主要な依存関係 (build.gradle.kts に追加)
# - JUnit 5
# - Mockito
# - AssertJ
# - Testcontainers
# - ArchUnit
# - SpotBugs, Checkstyle, PMD
# - OWASP Dependency-Check
```

### 5. Go プロジェクト

```bash
# Go テスト設定ガイドを参照
cat sdd-templates/config/testing/go_test_config.md

# 必須ツールをインストール
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
go install golang.org/x/vuln/cmd/govulncheck@latest

# テスト実行
go test -v -race -coverprofile=coverage.out ./...
```

---

## ファイル一覧

| ファイル | 用途 | コピー先 |
|---------|------|---------|
| `vitest.config.ts` | TypeScript単体テスト設定 | プロジェクトルート |
| `pyproject.toml.snippet` | Python pytest設定 | 既存のpyproject.tomlにマージ |
| `python/conftest.py.template` | Pythonフィクスチャ | specs/\<feature\>/tests/conftest.py |
| `python/test_api.py.template` | Python APIテストパターン | specs/\<feature\>/tests/test_*.py |
| `Cargo.toml.snippet` | Rust テスト設定 | 既存のCargo.tomlにマージ |
| `build.gradle.kts.snippet` | Java/Gradle テスト設定 | 既存のbuild.gradle.ktsにマージ |
| `go_test_config.md` | Go テスト設定ガイド | 参照のみ（設定はMakefile等で管理） |

---

## SDD テストディレクトリ構造

```
specs/<feature>/tests/
├── unit/           # 単体テスト
├── integration/    # 統合テスト
├── e2e/            # E2Eテスト (Playwright)
└── reports/        # テストレポート出力先
    ├── coverage/
    └── e2e/
```

---

## Coverage Policy (from plan.md)

| Layer | 対象 | 目標 |
|-------|------|-----|
| Layer-1 | AC (受入条件) | 100% |
| Layer-2 | CT (契約) | 100% |
| Layer-3 | Code | Line 80%, Branch 70% |

---

## 関連ドキュメント

- `docs/CI_CD_INTEGRATION.md` - CI/CDパイプライン設定
- `templates/plan_template.md` - test_strategy.tooling セクション
- `agent_docs/testing.md` - テスト実行ガイド
