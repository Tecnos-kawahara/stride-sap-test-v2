# SDD Template - Go Testing Configuration Guide

Version: 5.3.3-tecnos-stride

Go には設定ファイルが少なく、テスト設定は主にコマンドと規約で管理します。
このガイドでは、SDD準拠のGoテスト構成を説明します。

---

## 1. ディレクトリ構成 (SDD準拠)

```
project/
├── go.mod
├── go.sum
├── src/                          # メインコード
│   └── ...
├── specs/
│   └── xxx_feature_name/
│       └── tests/
│           └── go/
│               ├── unit/         # 単体テスト (*_test.go)
│               ├── integration/  # 統合テスト
│               ├── fuzz/         # Fuzzテスト
│               └── reports/      # カバレッジレポート
├── .golangci.yml                 # golangci-lint設定
└── Makefile                      # テストコマンド集約
```

---

## 2. .golangci.yml (推奨設定)

```yaml
# .golangci.yml
run:
  timeout: 5m
  go: '1.22'

linters:
  enable:
    # デフォルト
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    # 追加推奨
    - bodyclose
    - contextcheck
    - dupl
    - durationcheck
    - errorlint
    - exhaustive
    - goconst
    - gocritic
    - gocyclo
    - godot
    - gofmt
    - goimports
    - gosec
    - misspell
    - nilerr
    - noctx
    - prealloc
    - revive
    - unconvert
    - unparam
    - wastedassign

linters-settings:
  gocyclo:
    min-complexity: 15
  dupl:
    threshold: 100
  goconst:
    min-len: 3
    min-occurrences: 3
  gosec:
    excludes:
      - G104  # Audit errors not checked

issues:
  exclude-rules:
    - path: _test\.go
      linters:
        - dupl
        - gosec
        - goconst
```

---

## 3. Makefile (テストコマンド集約)

```makefile
# Makefile

FEATURE := xxx_feature_name
TEST_DIR := specs/$(FEATURE)/tests/go
COVERAGE_DIR := $(TEST_DIR)/reports

.PHONY: test test-unit test-integration test-race test-fuzz coverage lint fmt vet security

# フォーマットチェック
fmt:
	@echo "==> Checking format..."
	@test -z "$$(gofmt -l .)" || (gofmt -d . && exit 1)

# Lint (golangci-lint)
lint:
	@echo "==> Running linter..."
	golangci-lint run ./...

# Vet
vet:
	@echo "==> Running go vet..."
	go vet ./...

# 単体テスト
test-unit:
	@echo "==> Running unit tests..."
	go test -v -short ./...

# 統合テスト
test-integration:
	@echo "==> Running integration tests..."
	go test -v -run Integration ./...

# Race検出 (必須: main/nightly)
test-race:
	@echo "==> Running tests with race detection..."
	go test -race -short ./...

# Fuzzテスト
test-fuzz:
	@echo "==> Running fuzz tests..."
	go test -fuzz=. -fuzztime=30s ./...

# カバレッジ
coverage:
	@echo "==> Running tests with coverage..."
	@mkdir -p $(COVERAGE_DIR)
	go test -coverprofile=$(COVERAGE_DIR)/coverage.out -covermode=atomic ./...
	go tool cover -html=$(COVERAGE_DIR)/coverage.out -o $(COVERAGE_DIR)/coverage.html
	@echo "Coverage report: $(COVERAGE_DIR)/coverage.html"

# カバレッジ閾値チェック (80%)
coverage-check: coverage
	@echo "==> Checking coverage threshold..."
	@COVERAGE=$$(go tool cover -func=$(COVERAGE_DIR)/coverage.out | grep total | awk '{print $$3}' | sed 's/%//'); \
	if [ $$(echo "$$COVERAGE < 80" | bc -l) -eq 1 ]; then \
		echo "Coverage $$COVERAGE% is below 80% threshold"; \
		exit 1; \
	fi; \
	echo "Coverage: $$COVERAGE% (OK)"

# セキュリティスキャン
security:
	@echo "==> Running security scan..."
	govulncheck ./...

# 全テスト (CI用)
test: fmt lint vet test-unit test-race coverage-check security
	@echo "==> All tests passed!"
```

---

## 4. テストファイルの書き方

### 4.1 単体テスト

```go
// specs/xxx_feature_name/tests/go/unit/handler_test.go
package unit

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestHandleRequest_Success(t *testing.T) {
    // Given
    input := "test-input"

    // When
    result, err := HandleRequest(input)

    // Then
    require.NoError(t, err)
    assert.Equal(t, "expected", result)
}

func TestHandleRequest_Error(t *testing.T) {
    t.Parallel() // 並列実行

    tests := []struct {
        name    string
        input   string
        wantErr bool
    }{
        {"empty input", "", true},
        {"valid input", "valid", false},
    }

    for _, tt := range tests {
        tt := tt // capture range variable
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()
            _, err := HandleRequest(tt.input)
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}
```

### 4.2 統合テスト

```go
// specs/xxx_feature_name/tests/go/integration/api_test.go
//go:build integration

package integration

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestIntegration_APIEndpoint(t *testing.T) {
    if testing.Short() {
        t.Skip("Skipping integration test in short mode")
    }

    // Setup test server
    server := httptest.NewServer(NewRouter())
    defer server.Close()

    // Test
    resp, err := http.Get(server.URL + "/api/v1/resource")
    if err != nil {
        t.Fatalf("Failed to make request: %v", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        t.Errorf("Expected status 200, got %d", resp.StatusCode)
    }
}
```

### 4.3 Fuzzテスト

```go
// specs/xxx_feature_name/tests/go/fuzz/parser_test.go
package fuzz

import (
    "testing"
)

func FuzzParseInput(f *testing.F) {
    // Seed corpus
    f.Add("valid-input")
    f.Add("")
    f.Add("special!@#$%")

    f.Fuzz(func(t *testing.T, input string) {
        // Should not panic
        _ = ParseInput(input)
    })
}
```

---

## 5. 依存関係 (go.mod)

```go
// go.mod
module example.com/project

go 1.22

require (
    github.com/stretchr/testify v1.9.0
    github.com/golang/mock v1.6.0
)
```

### 推奨テストライブラリ

| ライブラリ | 用途 |
|-----------|------|
| testify | assertion, require, mock |
| gomock | モック生成 |
| httptest | HTTP テスト |
| testcontainers-go | コンテナ統合テスト |

---

## 6. CI コマンドまとめ

```bash
# PR必須
gofmt -l .                    # フォーマットチェック
golangci-lint run ./...       # Lint
go test -v -short ./...       # 単体テスト
govulncheck ./...             # セキュリティ

# main/nightly
go test -race ./...           # Race検出 (必須)
go test -fuzz=. -fuzztime=1m  # Fuzz
go test -coverprofile=...     # カバレッジ
```

---

## 7. 関連ドキュメント

- `docs/CI_CD_INTEGRATION.md` - CI/CDパイプライン設定
- `templates/plan_template.md` - test_strategy.tooling.language_runners.go
