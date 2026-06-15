# CI/CD Integration Guide

Version: 5.3.3-tecnos-stride

This guide explains how to integrate stride-lint and the SDD workflow into your CI/CD pipeline.

> Note:
> `--scale enterprise` is a monorepo/CI sizing option.
> Enterprise Hierarchy (Epic/Feature lint) is enabled separately via `sdd-templates/config/enterprise.yaml`.

---

## Quick Start

### GitHub Actions

Create `.github/workflows/stride-lint.yml`:

```yaml
name: SDD Spec Validation

on:
  push:
    paths:
      - 'specs/**'
  pull_request:
    paths:
      - 'specs/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install pyyaml

      - name: Run stride-lint
        run: |
          chmod +x sdd-templates/bin/stride
          sdd-templates/bin/stride lint --all

      - name: Upload lint report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: stride-lint-report
          path: |
            specs/**/implementation-details/evidence_pack.md
```

### GitHub Actions (Enterprise Hierarchy project)

If the repository uses Epic/Feature hierarchy, commit `sdd-templates/config/enterprise.yaml` with `enterprise.enabled: true` and run:

```yaml
      - name: Run stride-lint (enterprise)
        run: |
          chmod +x sdd-templates/bin/stride
          sdd-templates/bin/stride lint --all --enterprise
```

### GitLab CI

Create `.gitlab-ci.yml`:

```yaml
stages:
  - validate
  - test
  - deploy

stride-lint:
  stage: validate
  image: python:3.11-slim
  before_script:
    - pip install pyyaml
    - chmod +x sdd-templates/bin/stride
  script:
    - sdd-templates/bin/stride lint --all
  rules:
    - changes:
        - specs/**/*
  artifacts:
    when: always
    paths:
      - specs/**/implementation-details/evidence_pack.md
```

### Azure DevOps

Create `azure-pipelines.yml`:

```yaml
trigger:
  paths:
    include:
      - specs/*

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: |
      pip install pyyaml
      chmod +x sdd-templates/bin/stride
      sdd-templates/bin/stride lint --all
    displayName: 'Run stride-lint'

  - task: PublishBuildArtifacts@1
    inputs:
      pathToPublish: 'specs'
      artifactName: 'spec-artifacts'
    condition: always()
```

---

## Pipeline Stages

### Recommended Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Spec Lint   │ -> │ Unit Tests  │ -> │ Int Tests   │ -> │ E2E Tests   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       v                  v                  v                  v
 SPEC_VALID=true    UNIT_PASS=true    INT_PASS=true    E2E_PASS=true
```

### Stage Definitions

#### 1. Spec Validation (stride-lint)

```bash
# Run all specs
stride lint --all

# Run changed specs only (for PR validation)
stride lint --changed origin/main...HEAD

# Strict mode (fail on warnings)
stride lint --all --fail-on APPROVAL_PENDING,PLACEHOLDER_VALUE_PRESENT
```

#### 2. Unit Tests

```bash
# After spec validation passes
npm test -- --coverage
```

#### 3. Integration Tests

```bash
# Run integration tests
npm run test:integration

# With coverage
npm run test:integration -- --coverage
```

#### 4. E2E Tests

```bash
# Run Playwright E2E tests
npx playwright test --config=specs/<feature>/tests/e2e/playwright.config.ts

# Generate HTML report
npx playwright show-report
```

---

## Gate-Based Deployment

### Phase Gate Integration

Use stride-lint exit codes to enforce phase gates:

```yaml
# GitHub Actions example
jobs:
  phase-gate-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check Phase Gate Status
        run: |
          sdd-templates/bin/stride phase-status specs/${{ github.event.inputs.feature }}/

      - name: Verify Approval
        run: |
          # Exit 1 if approval pending
          sdd-templates/bin/stride lint specs/${{ github.event.inputs.feature }}/ \
            --fail-on APPROVAL_PENDING
```

### Deployment Gate Matrix

| Environment | Required Gates | stride Command |
|-------------|----------------|-----------------|
| Dev | None | `stride lint --warn-only` |
| Staging | Gate 1-4 | `stride lint` |
| Production | Gate 1-5 + Final | `stride lint --fail-on APPROVAL_PENDING` |

---

## Coverage Reporting

### Generate Coverage Report

```bash
# Full coverage report
stride lint specs/<feature>/ --coverage-report

# JSON output for processing
stride lint specs/<feature>/ --format json > coverage.json
```

### Coverage Thresholds

Add to your CI config:

```bash
# Parse coverage from stride output and enforce thresholds
COVERAGE=$(stride lint specs/<feature>/ --format json | jq '.results[0].coverage_report.coverage_report.acceptance_criteria.coverage_pct')

if (( $(echo "$COVERAGE < 80" | bc -l) )); then
  echo "Coverage $COVERAGE% is below 80% threshold"
  exit 1
fi
```

---

## Evidence Pack Generation

### Automated Evidence Collection

```yaml
# GitHub Actions - Collect evidence pack
- name: Generate Evidence Pack
  run: |
    # Run tests with coverage
    npm test -- --coverage --json --outputFile=coverage.json

    # Run SAST
    npm run lint -- --format json > sast-results.json

    # Generate evidence
    cat > specs/<feature>/implementation-details/evidence_pack.md << EOF
    # Evidence Pack

    Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
    Commit: ${{ github.sha }}

    ## CI Results
    - Coverage: $(cat coverage.json | jq '.coveragePercentage')%
    - Tests Passed: $(cat coverage.json | jq '.numPassedTests')

    ## SAST
    - Issues Found: $(cat sast-results.json | jq '.errorCount')
    EOF
```

---

## Error Handling

### Common CI Failures

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | All checks passed | Continue pipeline |
| 1 | Errors found | Review errors, fix specs |
| 1 (APPROVAL_PENDING) | Human approval needed | Wait for APPROVAL.md update |

### Retry Strategy

```yaml
# GitHub Actions - Retry on transient failures
- name: Run stride-lint
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 5
    max_attempts: 3
    command: sdd-templates/bin/stride lint --all
```

---

## Common Quality Gate Standards (v1.2.4)

言語を跨いで統一される品質ゲートの責務分担です。

### Quality Pyramid（テストピラミッド）

```
         ▲ E2E（少量）: 主要業務フローのみ
        ╱ ╲  - Playwright
       ╱───╲ Contract（CDC/Schema）: サービス境界の破壊検知
      ╱─────╲  - OpenAPI, AsyncAPI, Proto, Pact
     ╱───────╲ Integration/API（中量）: HTTP/DB/Queue統合
    ╱─────────╲  - 言語別の統合テストフレームワーク
   ╱───────────╲ Unit（大量）: 言語別の標準ランナーで高速に
  ╱─────────────╲  - Vitest, pytest, cargo test, JUnit5, go test
```

### PR vs main/nightly の分担

| タイミング | 実行内容 | 言語共通 |
|-----------|---------|---------|
| **PR** | Unit + Lint + 型/静的解析 + 軽量Integration + E2Eスモーク + 契約検証 | 高速優先 |
| **main/nightly** | E2E回帰 + 負荷(k6) + DAST + Go `-race` + Rust/Javaベンチ | 重い処理 |

### 境界のSSOT（Single Source of Truth）

| プロトコル | SSOT | 検証ツール |
|-----------|------|-----------|
| HTTP REST | OpenAPI | Schemathesis, Dredd |
| HTTP GraphQL | SDL | Apollo validation |
| gRPC | Proto | buf lint, buf breaking |
| Events | AsyncAPI | Spectral |
| CDC | Pact contracts | Pact Broker |

### AI活用の配置（推奨）

| AI担当 | 人間担当 |
|--------|---------|
| テスト生成 | 合否判定の決定性 |
| 影響分析 | テストデータの正当性 |
| 失敗原因要約 | 境界契約の設計 |
| 修正案PR提案 | 最終承認 |

> ⚠️ "ツール無しでAIが実行判定"はエンプラのゲートでは避ける（決定性・監査性が落ちやすい）

---

## Multi-Language Pipeline (v1.2.4)

### GitHub Actions - Multi-Language Matrix

Create `.github/workflows/test-multi-lang.yml`:

```yaml
name: Multi-Language Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # ===== 共通: Spec検証 =====
  spec-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pyyaml
      - run: chmod +x sdd-templates/bin/stride
      - run: sdd-templates/bin/stride lint --all

  # ===== TypeScript テスト =====
  test-typescript:
    needs: spec-validation
    if: hashFiles('**/vitest.config.ts') != '' || hashFiles('**/package.json') != ''
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Unit Tests (Vitest)
        run: npm run test:unit -- --coverage
      - name: Integration Tests
        run: npm run test:integration
      - uses: actions/upload-artifact@v4
        with:
          name: ts-coverage
          path: coverage/

  # ===== Python テスト =====
  test-python:
    needs: spec-validation
    if: hashFiles('**/pyproject.toml') != ''
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Unit & Integration Tests (pytest)
        run: pytest specs/*/tests/ --cov --cov-report=xml --cov-report=html -v
      - uses: actions/upload-artifact@v4
        with:
          name: py-coverage
          path: |
            coverage.xml
            htmlcov/

  # ===== Rust テスト =====
  test-rust:
    needs: spec-validation
    if: hashFiles('**/Cargo.toml') != ''
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Lint (clippy)
        run: cargo clippy --all-targets --all-features -- -D warnings
      - name: Format check
        run: cargo fmt --all -- --check
      - name: Unit Tests
        run: cargo test --all-features
      - name: Install Tarpaulin
        run: cargo install cargo-tarpaulin
      - name: Coverage
        run: cargo tarpaulin --out Xml --output-dir coverage
      - name: Security Audit
        run: cargo audit
      - uses: actions/upload-artifact@v4
        with:
          name: rust-coverage
          path: coverage/cobertura.xml

  # ===== Java テスト (Gradle) =====
  test-java:
    needs: spec-validation
    if: hashFiles('**/build.gradle*') != '' || hashFiles('**/pom.xml') != ''
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '21'
          cache: 'gradle'
      - name: Lint & Static Analysis
        run: ./gradlew check spotbugsMain checkstyleMain
      - name: Unit Tests (JUnit5)
        run: ./gradlew test
      - name: Integration Tests (Testcontainers)
        run: ./gradlew integrationTest
      - name: Architecture Tests (ArchUnit)
        run: ./gradlew archTest
      - name: Coverage Report (JaCoCo)
        run: ./gradlew jacocoTestReport
      - name: Dependency Check (OWASP)
        run: ./gradlew dependencyCheckAnalyze
      - uses: actions/upload-artifact@v4
        with:
          name: java-coverage
          path: build/reports/jacoco/

  # ===== Go テスト =====
  test-go:
    needs: spec-validation
    if: hashFiles('**/go.mod') != ''
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
          cache: true
      - name: Format check (gofmt)
        run: |
          if [ -n "$(gofmt -l .)" ]; then
            echo "Code is not formatted. Run 'gofmt -w .'"
            gofmt -d .
            exit 1
          fi
      - name: Lint (golangci-lint)
        uses: golangci/golangci-lint-action@v4
        with:
          version: latest
      - name: Unit Tests
        run: go test -v -coverprofile=coverage.out ./...
      - name: Race Detection (nightly recommended)
        run: go test -race -short ./...
      - name: Security Scan (govulncheck)
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          govulncheck ./...
      - uses: actions/upload-artifact@v4
        with:
          name: go-coverage
          path: coverage.out

  # ===== E2E テスト (Playwright) =====
  test-e2e:
    needs: [test-typescript, test-python, test-rust, test-java, test-go]
    if: always() && !cancelled()
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npx playwright install --with-deps
      - name: Start application
        run: npm run start:test &
      - name: Run E2E Tests
        run: npx playwright test --config=specs/*/tests/e2e/playwright.config.ts
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: e2e-report
          path: |
            playwright-report/
            test-results/

  # ===== 契約検証 (OpenAPI/Pact) =====
  contract-tests:
    needs: spec-validation
    if: hashFiles('contracts/openapi.yaml') != ''
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install schemathesis httpx
      - name: Start API server
        run: |
          pip install -e ".[dev]"
          uvicorn src.main:app --host 0.0.0.0 --port 8000 &
          sleep 5
      - name: OpenAPI Contract Validation
        run: schemathesis run contracts/openapi.yaml --base-url http://localhost:8000 --checks all

  # ===== Quality Gate =====
  quality-gate:
    needs: [test-typescript, test-python, test-rust, test-java, test-go, test-e2e, contract-tests]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Check all tests passed
        run: |
          if [[ "${{ needs.test-typescript.result }}" == "failure" ]] || \
             [[ "${{ needs.test-python.result }}" == "failure" ]] || \
             [[ "${{ needs.test-rust.result }}" == "failure" ]] || \
             [[ "${{ needs.test-java.result }}" == "failure" ]] || \
             [[ "${{ needs.test-go.result }}" == "failure" ]] || \
             [[ "${{ needs.test-e2e.result }}" == "failure" ]] || \
             [[ "${{ needs.contract-tests.result }}" == "failure" ]]; then
            echo "One or more test jobs failed"
            exit 1
          fi
          echo "All tests passed!"
```

### Coverage Thresholds per Language

| Language | Tool | Line Target | Branch Target |
|----------|------|-------------|---------------|
| TypeScript | istanbul/v8 | 80% | 70% |
| Python | pytest-cov | 80% | 70% |
| Rust | cargo-tarpaulin | 80% | 70% |
| Java | JaCoCo | 80% | 70% |
| Go | go cover | 80% | 70% |

### Static Analysis per Language

| Language | Lint | Format | SCA | Additional |
|----------|------|--------|-----|------------|
| TypeScript | ESLint | Prettier | npm audit | tsc --noEmit |
| Python | Ruff | Black | pip-audit | mypy/pyright |
| Rust | clippy | rustfmt | cargo-audit | cargo-deny |
| Java | SpotBugs/PMD | Checkstyle | OWASP Dep-Check | ArchUnit |
| Go | golangci-lint | gofmt | govulncheck | -race flag |

### Cross-Language Contract Testing

契約検証ツールの選択:

| ツール | 用途 | 設定場所 |
|--------|------|---------|
| Schemathesis | OpenAPI自動検証 | `contracts/openapi.yaml` |
| Dredd | OpenAPI手動テスト | `dredd.yml` |
| Pact | Consumer-Driven Contracts | `contracts/pacts/` |

---

## Best Practices

### 1. Run on Every PR

Always validate specs in pull requests to catch issues early.

### 2. Fail Fast

Run stride-lint before tests to avoid wasting CI time on invalid specs.

### 3. Cache Dependencies

```yaml
- name: Cache pip packages
  uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-pyyaml
```

### 4. Use Artifacts

Save evidence packs and reports as artifacts for audit trails.

### 5. Notify on Failures

```yaml
- name: Notify on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    channel-id: 'C0XXXXXX'
    slack-message: 'stride-lint failed on ${{ github.ref }}'
```

---

## Troubleshooting

### "YAML not installed"

```bash
pip install pyyaml
```

### "stride command not found"

```bash
chmod +x sdd-templates/bin/stride
export PATH="$PATH:$(pwd)/sdd-templates/bin"
```

### "APPROVAL_PENDING but gates are approved"

Check that:
1. All checkboxes are `[x]` (not `[ ]`)
2. Approver name is filled in (not `_____`)
3. File is saved with UTF-8 encoding

---

## Related Documentation

- `agent_docs/testing.md` - 5言語対応テスト実行ガイド
- `docs/TEST_PATTERNS.md` - 検証済みテストパターン集
- `config/testing/python/conftest.py.template` - Pythonフィクスチャテンプレート
- `config/testing/python/test_api.py.template` - Python APIテストパターン
- `config/testing/README.md` - 言語別テスト設定テンプレート一覧
- `CHEATSHEET.md` Section 12-14 - マルチ言語テストクイックリファレンス

---

## Support

For issues with CI/CD integration:
1. Check the CHEATSHEET.md for error code meanings
2. Run `stride lint --verbose` for detailed output
3. Contact the Arch team for template questions
