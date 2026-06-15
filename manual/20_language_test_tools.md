# 20. 言語別テストツールガイド

**所要時間**: 約20分

---

## 概要

v1.2.5以降では、主要な5言語（Python、TypeScript、Rust、Go、Java）に対応したテスト設定テンプレートを提供しています。このガイドでは、各言語のベストプラクティスなテストツールと設定方法を解説します。

---

## 対応言語とツール一覧

| 言語 | テストツール | カバレッジ | Linter | セキュリティ |
|------|------------|----------|--------|------------|
| Python | pytest | pytest-cov | ruff, mypy | bandit |
| TypeScript | Vitest | @vitest/coverage-v8 | Oxlint（推奨）/ ESLint | npm audit |
| Rust | cargo test | cargo-tarpaulin | clippy | cargo-audit |
| Go | go test | go tool cover | golangci-lint | govulncheck |
| Java | JUnit 5 | JaCoCo | SpotBugs, PMD | OWASP Dependency-Check |

---

## AI Agent Pre-Flight Checklist

> **AIエージェントは、テスト実行前に必ず依存関係を確認し、不足していれば自動インストールすること。**

### クイックチェック＆インストール（全言語）

```bash
# === Python ===
python -c "import pytest" 2>/dev/null || pip install pytest pytest-cov httpx

# === TypeScript ===
npm list vitest 2>/dev/null || npm install -D vitest @vitest/coverage-v8
npx oxlint --version 2>/dev/null || npm install -D oxlint  # Rust製高速Linter（ESLint代替）

# === Rust ===
cargo tarpaulin --version 2>/dev/null || cargo install cargo-tarpaulin

# === Go ===
golangci-lint --version 2>/dev/null || go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# === Playwright (E2E) ===
npx playwright --version 2>/dev/null || { npm install -D @playwright/test && npx playwright install chromium; }
```

---

## 1. Python テスト

### 1.1 推奨ツール

| ツール | 用途 | インストール |
|--------|------|------------|
| pytest | テストフレームワーク | `pip install pytest` |
| pytest-cov | カバレッジ計測 | `pip install pytest-cov` |
| pytest-asyncio | 非同期テスト | `pip install pytest-asyncio` |
| httpx | HTTPテスト | `pip install httpx` |
| schemathesis | 契約テスト | `pip install schemathesis` |
| ruff | Linter (高速) | `pip install ruff` |
| mypy | 型チェック | `pip install mypy` |
| bandit | セキュリティ検査 | `pip install bandit` |

### 1.2 セットアップ

```bash
# テンプレートをコピー
cp sdd-templates/config/testing/python/conftest.py.template \
   specs/<feature>/tests/conftest.py

cp sdd-templates/config/testing/python/test_api.py.template \
   specs/<feature>/tests/test_api.py

# 依存関係をインストール
pip install pytest pytest-cov pytest-asyncio httpx ruff mypy
```

### 1.3 pyproject.toml 設定

```toml
[tool.pytest.ini_options]
testpaths = ["specs/<feature>/tests"]
addopts = ["-v", "--strict-markers", "-p", "no:asyncio"]  # pytest-asyncio 競合回避
markers = [
    "unit: 単体テスト",
    "integration: 統合テスト",
    "contract: 契約テスト",
    "e2e: E2Eテスト",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

### 1.4 実行コマンド

```bash
# 全テスト
python -m pytest specs/<feature>/tests/

# カバレッジ付き
python -m pytest specs/<feature>/tests/ --cov=src --cov-report=term-missing

# 特定マーカーのみ
python -m pytest -m "unit"           # 単体テスト
python -m pytest -m "integration"    # 統合テスト
python -m pytest -m "not e2e"        # E2E以外

# Lint
ruff check src/
mypy src/

# セキュリティ
bandit -r src/
```

### 1.5 pytest-asyncio 競合回避（重要）

`asyncio_mode = "auto"` を使用すると競合が発生する場合があります。以下の設定で回避:

```toml
[tool.pytest.ini_options]
addopts = ["-v", "--strict-markers", "-p", "no:asyncio"]
```

---

## 2. TypeScript テスト

### 2.1 推奨ツール

| ツール | 用途 | インストール |
|--------|------|------------|
| Vitest | テストフレームワーク | `npm install -D vitest` |
| @vitest/coverage-v8 | カバレッジ計測 | `npm install -D @vitest/coverage-v8` |
| @testing-library/react | Reactテスト | `npm install -D @testing-library/react` |
| MSW | APIモック | `npm install -D msw` |
| **Oxlint** | **Linter（推奨）** | `npm install -D oxlint` |
| **Oxfmt** | **Formatter（推奨）** | `npm install -D oxfmt` |
| ESLint | Linter（従来） | `npm install -D eslint` |
| Playwright | E2Eテスト | `npm install -D @playwright/test` |

> **💡 Oxlint / Oxfmt について:** Rust製の高速リンター/フォーマッター。ESLintの50-100倍、Prettierの数十倍高速。ESLintルールの大半を互換サポートしているため、移行コストが低い。Symphony並列実行やCI高速化に特に効果的。ESLint/Prettierからの移行は `vp migrate`（[Vite+](https://github.com/voidzero-dev/vite-plus)）で自動化可能。

### 2.2 セットアップ

```bash
# vitest.config.ts をコピー
cp sdd-templates/config/testing/vitest.config.ts ./

# 依存関係をインストール
npm install -D vitest @vitest/coverage-v8 @testing-library/react

# package.json にスクリプトを追加
npm pkg set scripts.test:unit="vitest run"
npm pkg set scripts.test:watch="vitest"
npm pkg set scripts.test:coverage="vitest run --coverage"
```

### 2.3 vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./specs/<feature>/tests/setup.ts'],
    include: ['specs/**/tests/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      reportsDirectory: 'specs/<feature>/tests/reports/coverage',
      thresholds: {
        lines: 80,
        branches: 70,
        functions: 80,
        statements: 80,
      },
    },
  },
});
```

### 2.4 実行コマンド

```bash
# 全テスト
npm run test:unit

# ウォッチモード
npm run test:watch

# カバレッジ付き
npm run test:coverage

# 特定ファイル
npx vitest run specs/<feature>/tests/unit/auth.test.ts

# Lint
npx eslint src/

# セキュリティ
npm audit
```

---

## 3. Rust テスト

### 3.1 推奨ツール

| ツール | 用途 | インストール |
|--------|------|------------|
| cargo test | テストフレームワーク | 標準搭載 |
| cargo-tarpaulin | カバレッジ計測 | `cargo install cargo-tarpaulin` |
| cargo-audit | セキュリティ検査 | `cargo install cargo-audit` |
| clippy | Linter | 標準搭載 |
| rustfmt | フォーマッター | 標準搭載 |

### 3.2 Cargo.toml 設定

```toml
[dev-dependencies]
tokio = { version = "1", features = ["full", "test-util"] }
assert_matches = "1.5"
mockall = "0.11"
test-case = "3.0"

[profile.test]
opt-level = 0
debug = true
```

### 3.3 実行コマンド

```bash
# 全テスト
cargo test

# カバレッジ付き（tarpaulin）
cargo tarpaulin --out Html --output-dir specs/<feature>/tests/reports/coverage

# 特定テスト
cargo test test_order_creation

# ドキュメントテスト
cargo test --doc

# Lint
cargo clippy -- -D warnings

# フォーマット
cargo fmt --check

# セキュリティ
cargo audit
```

---

## 4. Go テスト

### 4.1 推奨ツール

| ツール | 用途 | インストール |
|--------|------|------------|
| go test | テストフレームワーク | 標準搭載 |
| testify | アサーション | `go get github.com/stretchr/testify` |
| gomock | モック生成 | `go install github.com/golang/mock/mockgen@latest` |
| golangci-lint | Linter | `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest` |
| govulncheck | 脆弱性検査 | `go install golang.org/x/vuln/cmd/govulncheck@latest` |
| testcontainers-go | コンテナ統合テスト | `go get github.com/testcontainers/testcontainers-go` |

### 4.2 .golangci.yml 設定

```yaml
run:
  timeout: 5m
  go: '1.22'

linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - bodyclose
    - goconst
    - gocritic
    - gocyclo
    - gofmt
    - goimports
    - gosec
    - misspell
    - revive

linters-settings:
  gocyclo:
    min-complexity: 15
  gosec:
    excludes:
      - G104
```

### 4.3 Makefile

```makefile
FEATURE := my_feature
COVERAGE_DIR := specs/$(FEATURE)/tests/reports

.PHONY: test lint coverage security

test:
	go test -v -short ./...

test-race:
	go test -race -short ./...

lint:
	golangci-lint run ./...

coverage:
	@mkdir -p $(COVERAGE_DIR)
	go test -coverprofile=$(COVERAGE_DIR)/coverage.out -covermode=atomic ./...
	go tool cover -html=$(COVERAGE_DIR)/coverage.out -o $(COVERAGE_DIR)/coverage.html

security:
	govulncheck ./...

all: lint test-race coverage security
```

### 4.4 実行コマンド

```bash
# 全テスト
go test -v ./...

# Race検出付き
go test -race ./...

# カバレッジ付き
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html

# Lint
golangci-lint run ./...

# セキュリティ
govulncheck ./...
```

---

## 5. Java テスト (Gradle)

### 5.1 推奨ツール

| ツール | 用途 | 設定 |
|--------|------|------|
| JUnit 5 | テストフレームワーク | `testImplementation("org.junit.jupiter:junit-jupiter:5.10+")` |
| Mockito | モック | `testImplementation("org.mockito:mockito-core:5.+")` |
| AssertJ | アサーション | `testImplementation("org.assertj:assertj-core:3.+")` |
| JaCoCo | カバレッジ | `id("jacoco")` |
| Testcontainers | コンテナテスト | `testImplementation("org.testcontainers:junit-jupiter:1.+")` |
| ArchUnit | アーキテクチャテスト | `testImplementation("com.tngtech.archunit:archunit-junit5:1.+")` |
| SpotBugs | 静的解析 | `id("com.github.spotbugs")` |
| OWASP | 脆弱性検査 | `id("org.owasp.dependencycheck")` |

### 5.2 build.gradle.kts 設定

```kotlin
plugins {
    java
    jacoco
    id("com.github.spotbugs") version "6.+"
    id("org.owasp.dependencycheck") version "9.+"
}

dependencies {
    testImplementation(platform("org.junit:junit-bom:5.10.0"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testImplementation("org.mockito:mockito-core:5.+")
    testImplementation("org.assertj:assertj-core:3.+")
    testImplementation("org.testcontainers:junit-jupiter:1.+")
    testImplementation("com.tngtech.archunit:archunit-junit5:1.+")
}

tasks.test {
    useJUnitPlatform()
    finalizedBy(tasks.jacocoTestReport)
}

tasks.jacocoTestReport {
    dependsOn(tasks.test)
    reports {
        xml.required.set(true)
        html.required.set(true)
        html.outputLocation.set(layout.buildDirectory.dir("reports/jacoco"))
    }
}

jacoco {
    toolVersion = "0.8.11"
}

tasks.jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = "0.80".toBigDecimal()
            }
        }
    }
}
```

### 5.3 実行コマンド

```bash
# 全テスト
./gradlew test

# カバレッジレポート
./gradlew jacocoTestReport

# カバレッジ検証
./gradlew jacocoTestCoverageVerification

# 特定テストクラス
./gradlew test --tests "com.example.OrderServiceTest"

# 静的解析
./gradlew spotbugsMain

# セキュリティ
./gradlew dependencyCheckAnalyze
```

---

## 6. E2E テスト (Playwright)

### 6.1 言語共通のPlaywright設定

Playwrightは TypeScript/JavaScript と Python の両方で利用可能です。

### 6.2 TypeScript での設定

```bash
# インストール
npm install -D @playwright/test
npx playwright install chromium

# テンプレートをコピー
cp sdd-templates/templates/tests/playwright.config.template.ts specs/<feature>/tests/e2e/playwright.config.ts
cp sdd-templates/templates/tests/e2e.spec.template.ts specs/<feature>/tests/e2e/example.spec.ts
```

### 6.3 Python での設定

```bash
# インストール
pip install playwright pytest-playwright
playwright install chromium
```

### 6.4 実行コマンド

```bash
# TypeScript
npx playwright test specs/<feature>/tests/e2e/

# Python
python -m pytest specs/<feature>/tests/e2e/ --headed

# 特定ブラウザ
npx playwright test --project=chromium

# UIモード（デバッグ）
npx playwright test --ui

# レポート生成（パスを指定）
npx playwright show-report specs/<feature>/tests/reports/e2e/playwright-report
```

---

## 7. CI/CD 統合コマンド

### PR時の必須チェック

| 言語 | コマンド |
|------|---------|
| Python | `python -m pytest --cov=src --cov-fail-under=80` |
| TypeScript | `npx vitest run --coverage` |
| Rust | `cargo test && cargo tarpaulin --fail-under 80` |
| Go | `go test -race ./... && golangci-lint run` |
| Java | `./gradlew test jacocoTestCoverageVerification` |

### セキュリティチェック

| 言語 | コマンド |
|------|---------|
| Python | `bandit -r src/ && pip-audit` |
| TypeScript | `npm audit` |
| Rust | `cargo audit` |
| Go | `govulncheck ./...` |
| Java | `./gradlew dependencyCheckAnalyze` |

---

## 8. ディレクトリ構造（SDD準拠）

すべての言語で以下の構造を推奨:

```
specs/<feature>/tests/
├── unit/              # 単体テスト
├── integration/       # 統合テスト
├── contract/          # 契約テスト
├── e2e/               # E2Eテスト
├── fixtures/          # テストデータ
├── conftest.py        # Python: 共有フィクスチャ
├── setup.ts           # TypeScript: セットアップ
└── reports/           # テストレポート
    ├── coverage/
    └── e2e/
```

---

## 9. Coverage Policy（再掲）

| Layer | 対象 | 目標 |
|-------|------|------|
| Layer-1 | AC (受入条件) | 100% |
| Layer-2 | CT (契約テスト) | 100% |
| Layer-3 | Code | Line 80%, Branch 70% |

---

## 関連ドキュメント

- [テスト実行ガイド](../sdd-templates/agent_docs/testing.md) - AI Pre-Flight Checklist 含む
- [テストパターン集](../sdd-templates/docs/TEST_PATTERNS.md) - 7カテゴリの検証済みパターン
- [CI/CD統合ガイド](../sdd-templates/docs/CI_CD_INTEGRATION.md) - パイプライン設定
- [config/testing/README.md](../sdd-templates/config/testing/README.md) - 設定テンプレート一覧

---

## チェックリスト

- [ ] 使用言語のテストツールを理解した
- [ ] カバレッジツールの設定方法を理解した
- [ ] Linter/静的解析の設定方法を理解した
- [ ] セキュリティ検査ツールを理解した
- [ ] CI/CDでの実行コマンドを理解した
- [ ] SDD準拠のディレクトリ構造を理解した

---

## 次のステップ

→ [テストパターン集](../sdd-templates/docs/TEST_PATTERNS.md) で具体的なテストの書き方を学ぶ

---

> SDD Templates Manual - 12. Language Test Tools Guide
