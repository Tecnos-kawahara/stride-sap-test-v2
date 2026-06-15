# Testing Guide (Tecnos SDD v4.4.0)

Goal: Deterministic gates and traceability from AC → TS → Task.

---

## AI Agent Pre-Flight Checklist

> **AIエージェントは、テスト実行前に必ずこのセクションを確認すること。**

### 依存関係の確認と自動インストール

テスト実行前に、必要なツールがインストールされているか確認し、不足している場合は自動的にインストールする。

#### Python

```bash
# 1. pytest が利用可能か確認
python -c "import pytest" 2>/dev/null || {
  echo "pytest not found. Installing..."
  pip install pytest pytest-cov pytest-asyncio httpx
}

# 2. 追加ツール確認（必要に応じて）
python -c "import schemathesis" 2>/dev/null || pip install schemathesis  # 契約テスト用
python -c "import playwright" 2>/dev/null || {
  pip install playwright pytest-playwright
  playwright install chromium
}
```

#### TypeScript / Node.js

```bash
# 1. vitest が利用可能か確認
npm list vitest 2>/dev/null || {
  echo "vitest not found. Installing..."
  npm install -D vitest @vitest/coverage-v8
}

# 2. Playwright 確認（E2E用）
npx playwright --version 2>/dev/null || {
  npm install -D @playwright/test
  npx playwright install chromium
}
```

#### Rust

```bash
# 1. cargo-tarpaulin（カバレッジ）確認
cargo tarpaulin --version 2>/dev/null || cargo install cargo-tarpaulin

# 2. cargo-audit（セキュリティ）確認
cargo audit --version 2>/dev/null || cargo install cargo-audit
```

#### Go

```bash
# 1. golangci-lint 確認
golangci-lint --version 2>/dev/null || go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# 2. govulncheck 確認
govulncheck --version 2>/dev/null || go install golang.org/x/vuln/cmd/govulncheck@latest
```

### 仮想環境の使用（Python推奨）

Python プロジェクトでは、依存関係の衝突を避けるため仮想環境を使用する：

```bash
# 仮想環境がなければ作成
[ -d ".venv" ] || python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 依存関係をインストール
pip install -e ".[dev]"  # pyproject.toml に dev 依存がある場合
```

### エラーリカバリー

| エラー | 原因 | 対処 |
|--------|------|------|
| `ModuleNotFoundError: No module named 'pytest'` | pytest 未インストール | `pip install pytest` |
| `command not found: vitest` | vitest 未インストール | `npm install -D vitest` |
| `browserType.launch: Executable doesn't exist` | Playwright ブラウザ未インストール | `npx playwright install` |
| `Permission denied` | グローバルインストール権限なし | 仮想環境を使用、または `--user` フラグ |
| `EACCES: permission denied` | npm グローバル権限なし | `sudo npm install -g` または npx を使用 |

### AI の行動規則

1. **テスト実行前に依存関係を確認する**
2. **不足ツールは自動的にインストールする**（ユーザーに確認不要）
3. **インストール失敗時はエラー内容を報告し、代替案を提示する**
4. **仮想環境が存在する場合は必ずそれを使用する**

---

## 1. Test Types and Mapping

| AC Tag | Test Type | Test ID Pattern | Coverage |
|--------|-----------|-----------------|----------|
| (untagged) | Unit | TS-UT-* | 基本機能 |
| `integration` | Integration | TS-INT-* | 統合ポイント |
| `e2e` | E2E Smoke | TS-E2E-* | 重要ユーザージャーニー |
| - | Contract | TS-CON-* | API/契約 |

### Coverage Policy
- **AC Coverage**: 100%（全ACが最低1つのTSでカバー）
- **CT Coverage**: 100%（全CTがTS-CONでカバー）
- **Code Coverage**: LIB=85%/75%, CMP=60%/50%（目標）

---

## 2. Plan Ownership

### 2.1 Test Definition in plan.md

```yaml
test_strategy:
  tests:
    - id: "TS-CON-01"
      type: "contract"
      scope: "API contract validation"
      covers_acceptance_ids: ["AC-US-FEAT001-001-01"]
      covers_contract_ids: ["CT-API-01"]

    - id: "TS-INT-01"
      type: "integration"
      scope: "External system integration"
      covers_acceptance_ids: ["AC-US-FEAT001-001-02"]
      covers_contract_ids: ["CT-API-01"]

    - id: "TS-E2E-01"
      type: "e2e"
      scope: "Critical user journey"
      covers_acceptance_ids: ["AC-US-FEAT001-001-03"]
```

### 2.2 E2E Reporting Configuration

```yaml
reporting:
  e2e:
    html_report: true
    junit_xml: true
    trace: "on-first-retry"
    screenshot: "only-on-failure"
    video: "retain-on-failure"
    artifacts_dir: "specs/<feature>/tests/reports/e2e/"
```

---

## 3. Test Directory Structure (SDD準拠)

```
specs/<feature>/tests/
├── unit/              # 単体テスト（ビジネスロジック）
├── integration/       # 統合テスト（API、DB接続）
├── contract/          # 契約テスト（OpenAPI検証）
├── e2e/               # E2Eテスト（Playwright）
├── conftest.py        # 共有フィクスチャ (Python)
├── fixtures/          # テストデータ
└── reports/           # テストレポート出力先
    ├── coverage/
    └── e2e/
```

> **重要**: テストは `specs/<feature>/tests/` に配置する（ルートの `/tests/` は使わない）

---

## 4. Language-Specific Testing

### 4.1 Python テスト

```bash
# 全テスト実行
python -m pytest specs/<feature>/tests/

# カバレッジ付き実行
python -m pytest specs/<feature>/tests/ --cov=src --cov-report=term-missing

# 特定マーカーのみ
python -m pytest specs/<feature>/tests/ -m "unit"           # 単体テストのみ
python -m pytest specs/<feature>/tests/ -m "integration"    # 統合テストのみ
python -m pytest specs/<feature>/tests/ -m "contract"       # 契約テストのみ
python -m pytest specs/<feature>/tests/ -m "not e2e"        # E2E以外

# E2E実行（別途）
python -m pytest specs/<feature>/tests/e2e/ --headed

# カバレッジHTML生成
python -m pytest specs/<feature>/tests/ --cov=src --cov-report=html
```

#### よくある問題と解決策

**pytest-asyncio エラー:**
```
AttributeError: 'Package' object has no attribute 'obj'
```
**解決策**: `pyproject.toml` で `asyncio_mode = "auto"` を削除し、以下に変更:
```toml
[tool.pytest.ini_options]
addopts = ["-v", "--strict-markers", "--tb=short", "-p", "no:asyncio"]
```

**カバレッジが低いモジュール:**
1. HTMLレンダリング系は除外対象に追加:
```toml
[tool.coverage.run]
omit = ["src/api/routers/web.py", "src/templates/*"]
```
2. E2Eで別途カバー

### 4.2 TypeScript テスト

```bash
# 全テスト実行
npm run test:unit

# ウォッチモード
npm run test:watch

# カバレッジ付き
npm run test:coverage

# 特定ファイル
npx vitest run specs/<feature>/tests/unit/auth.test.ts
```

### 4.3 Rust テスト

```bash
# 全テスト実行
cargo test

# カバレッジ付き（tarpaulin）
cargo tarpaulin --out Html --output-dir specs/<feature>/tests/reports/coverage

# 特定テスト
cargo test test_order_creation

# ドキュメントテスト
cargo test --doc
```

### 4.4 Java テスト (Gradle)

```bash
# 全テスト実行
./gradlew test

# カバレッジレポート
./gradlew jacocoTestReport

# 特定テストクラス
./gradlew test --tests "com.example.OrderServiceTest"

# 統合テスト
./gradlew integrationTest
```

### 4.5 Go テスト

```bash
# 全テスト実行
go test -v ./...

# カバレッジ付き
go test -v -race -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o coverage.html

# ベンチマーク
go test -bench=. ./...

# 特定パッケージ
go test -v ./internal/order/...
```

---

## 5. pytest Fixtures Best Practices

### 5.1 conftest.py 推奨構造

```python
# tests/conftest.py
import os
import pytest
from playwright.sync_api import Page, expect

# ─────────────────────────────────────────────────────
# Session-scoped fixtures (shared across all tests)
# ─────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Browser context configuration for all tests."""
    return {
        **browser_context_args,
        "base_url": os.getenv("E2E_BASE_URL", "http://localhost:8001"),
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }

@pytest.fixture(scope="session")
def test_users():
    """Test user credentials."""
    return {
        "buyer": {"username": "buyer", "password": "buyer123"},
        "supplier": {"username": "supplier", "password": "supplier123"},
        "admin": {"username": "admin", "password": "admin123"},
    }

# ─────────────────────────────────────────────────────
# Function-scoped fixtures (fresh for each test)
# ─────────────────────────────────────────────────────

@pytest.fixture
def authenticated_buyer_page(page: Page, test_users):
    """Authenticated page as buyer role."""
    _login(page, test_users["buyer"])
    yield page

@pytest.fixture
def authenticated_supplier_page(page: Page, test_users):
    """Authenticated page as supplier role."""
    _login(page, test_users["supplier"])
    yield page

@pytest.fixture
def authenticated_admin_page(page: Page, test_users):
    """Authenticated page as admin role."""
    _login(page, test_users["admin"])
    yield page

# ─────────────────────────────────────────────────────
# Helper functions
# ─────────────────────────────────────────────────────

def _login(page: Page, credentials: dict):
    """Perform login and wait for session establishment."""
    page.goto("/login")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="username"]', credentials["username"])
    page.fill('input[name="password"]', credentials["password"])
    page.click('button[type="submit"]')
    page.wait_for_url("**/orders**")
    page.wait_for_load_state("networkidle")
    # Verify session is established
    expect(page.locator(f"text={credentials['username']}")).to_be_visible()
```

### 5.2 Database Reset Strategy

```python
@pytest.fixture(autouse=True)
def reset_database():
    """Reset database before each test."""
    # テスト前にDBリセット
    db.drop_all()
    db.create_all()
    seed_test_data()
    yield
    # テスト後のクリーンアップ（必要に応じて）
```

### 5.3 Session-scoped vs Function-scoped

| Scope | 用途 | 例 |
|-------|------|-----|
| `session` | 全テスト共通設定 | browser_context_args, test_users |
| `module` | モジュール単位の設定 | module-specific DB state |
| `function` | 各テスト独立 | authenticated_*_page |

---

## 6. E2E Tests (Playwright)

### 6.1 言語選択ガイド

| 言語 | テンプレート | 推奨ケース |
|------|-------------|-----------|
| **Python** | `e2e.spec.template.py`, `conftest_e2e.template.py` | FastAPI/Django プロジェクト |
| **TypeScript** | `e2e.spec.template.ts`, `playwright.config.template.ts` | Next.js/React プロジェクト |

**選択基準**: プロジェクトのメイン言語に合わせて選択。

### 6.2 セットアップ

**TypeScript:**
```bash
npm install -D @playwright/test
npx playwright install chromium
```

**Python:**
```bash
pip install playwright pytest-playwright
playwright install chromium
```

### 6.3 テンプレートのコピー

**TypeScript:**
```bash
cp sdd-templates/templates/tests/e2e.spec.template.ts \
   specs/<feature>/tests/e2e/test_example.spec.ts
cp sdd-templates/templates/tests/playwright.config.template.ts \
   specs/<feature>/tests/e2e/playwright.config.ts
```

**Python:**
```bash
cp sdd-templates/templates/tests/e2e.spec.template.py \
   specs/<feature>/tests/e2e/test_example.py
cp sdd-templates/templates/tests/conftest_e2e.template.py \
   specs/<feature>/tests/e2e/conftest.py
```

### 6.4 実行コマンド

**TypeScript:**
```bash
# 全E2E実行
npx playwright test specs/<feature>/tests/e2e/

# UIモード（デバッグ用）
npx playwright test --ui

# 特定ブラウザ
npx playwright test --project=chromium

# レポート生成（パスを指定）
npx playwright show-report specs/<feature>/tests/reports/e2e/playwright-report
```

**Python:**
```bash
# 全E2E実行
python -m pytest specs/<feature>/tests/e2e/ --headed

# ヘッドレス実行
python -m pytest specs/<feature>/tests/e2e/

# スローモーション（デバッグ用）
python -m pytest specs/<feature>/tests/e2e/ --slowmo 500

# 特定ブラウザ
python -m pytest specs/<feature>/tests/e2e/ --browser chromium
```

---

## 7. E2E Best Practices (v1.2.5)

### 7.1 HTMX/SPA フォーム送信

**問題**: PlaywrightでHTMXフォームをクリックしても送信されない

**解決策**: JavaScriptで直接フォームをsubmit

```python
# NG: 通常のクリック
page.click('button[type="submit"]')

# OK: JavaScript submit
page.evaluate("""
    () => {
        document.querySelector('form[action="/orders/new"]').submit();
    }
""")
page.wait_for_load_state("networkidle")
```

**HTMXボタン（hx-post）の場合**:

```python
page.evaluate("""
    () => {
        const form = document.querySelector('form[hx-post*="/confirm"]');
        if (form) htmx.trigger(form, 'submit');
    }
""")
```

### 7.2 Playwright Strict Mode 対策

**問題**: 複数要素にマッチしてエラー

```
Error: strict mode violation: locator("text=completed")
resolved to 3 elements
```

**解決策**:

```python
# 1. .first を使用
expect(page.locator("text=completed").first).to_be_visible()

# 2. より具体的なセレクタ
expect(page.locator("span.status-badge:has-text('completed')")).to_be_visible()

# 3. data-testid を使用（推奨）
expect(page.locator("[data-testid='order-status']")).to_have_text("completed")
```

### 7.3 セッション管理

**問題**: ユーザー切り替え時にセッションCookieが残る

**解決策**: 明示的にログアウトしてから切り替え

```python
# 明示的ログアウト
page.click('button:has-text("Logout")')
page.wait_for_url("**/login**")
page.wait_for_load_state("networkidle")

# 新しいユーザーでログイン
page.fill('input[name="username"]', "new_user")
page.fill('input[name="password"]', "password")
page.click('button[type="submit"]')
```

### 7.4 安定セレクタの使用

```python
# NG: テキストベース（変更に弱い）
page.click('text=Submit Order')

# OK: data-testid（推奨）
page.click('[data-testid="submit-order-btn"]')

# OK: role + name
page.click('button[name="submit"]')
```

### 7.5 待機戦略

```python
# NG: 固定待機
time.sleep(2)

# OK: 条件付き待機
page.wait_for_load_state("networkidle")
page.wait_for_url("**/orders**")
expect(page.locator("[data-testid='success']")).to_be_visible()
```

---

## 8. Coverage Improvement Guide

### 8.1 低カバレッジモジュールの特定

```bash
# Python
python -m pytest --cov=src --cov-report=term-missing | grep -E "^\w+.*\d+%"

# 80%未満をフィルタ
python -m pytest --cov=src --cov-report=term-missing 2>&1 | awk '$NF+0 < 80'
```

### 8.2 優先度付けの指針

| 優先度 | 対象 | 理由 |
|--------|------|------|
| 高 | ビジネスロジック (service/) | バグが致命的 |
| 高 | 認証/認可 (auth/) | セキュリティ |
| 中 | APIエンドポイント (routers/) | ユーザー影響 |
| 低 | リポジトリ層 (repository/) | 統合テストでカバー |
| 除外 | HTMLレンダリング (web.py) | E2Eでカバー |

### 8.3 カバレッジ目標

| レイヤー | 対象 | 目標 |
|----------|------|------|
| Layer-1 | AC (受入条件) | 100% |
| Layer-2 | CT (契約テスト) | 100% |
| Layer-3 | Code | Line 80%, Branch 70% |

---

## 9. Troubleshooting Guide

### 9.1 stride-lint エラー

| エラーコード | 原因 | 解決策 |
|-------------|------|--------|
| `APPROVAL_PENDING` | Gate未承認 | APPROVAL.md を人間が編集 |
| `PLACEHOLDER_VALUE_PRESENT` | プレースホルダー残存 | sed で置換（FEAT-XXX等） |
| `COUNTS_MISMATCH` | カウント値不一致 | 提案された値をコピー |
| `MISSING_PLAN_REFS` | plan_refs 欠落 | タスクにplan_refsを追加 |
| `BPMN_VALIDATION_FAILED` | BPMN形式エラー | Camunda 8形式で再作成 |
| `AC_NOT_COVERED` | ACがテストでカバーされていない | TSにcovers_acceptance_ids追加 |
| `TAGGED_AC_NOT_COVERED...` | タグに対応するテストがない | integrationタグ→TS-INT追加 |
| `SPEC_AS_CODE_MISSING` | Spec-as-Code未定義 | spec.spec_as_code.artifacts追加 |
| `EVIDENCE_PACK_NOT_DEFINED` | Evidence Pack未定義 | plan.test_strategy.evidence_pack追加 |
| `REF_NOT_FOUND` | 参照先IDが存在しない | IDのtypoを確認 |

### 9.2 E2E テスト失敗

| 症状 | 原因 | 解決策 |
|------|------|--------|
| Timeout waiting for navigation | 非同期処理の競合 | JavaScript submitを使用 |
| Strict mode violation | 複数要素マッチ | .first または具体的セレクタ |
| Session lost after form submit | Cookie問題 | networkidle待機を追加 |
| Element not found | セレクタ変更 | data-testidを使用 |
| Flaky tests | タイミング問題 | wait_for_* を適切に使用 |
| Login fails in test | 認証状態の汚染 | fixture でログイン/ログアウト管理 |

### 9.3 デバッグ方法

```bash
# Headed mode でブラウザを表示
pytest tests/e2e/ --headed

# Slowmo で操作を遅くする
pytest tests/e2e/ --slowmo=500

# 特定のテストのみ実行
pytest tests/e2e/test_workflow.py::test_buyer_creates_order -v

# トレースを常に記録
pytest tests/e2e/ --tracing=on

# スクリーンショットを常に撮影
pytest tests/e2e/ --screenshot=on
```

### 9.4 Playwright Trace Viewer

```bash
# トレースファイルを開く
npx playwright show-trace test-results/trace.zip
```

---

## 10. Evidence and Triage

### 10.1 Evidence Pack

Store test reports in `implementation-details/evidence_pack.md`:

- CI results
- Test reports (unit/contract/integration/e2e)
- Security scans (SAST/SCA/secrets)
- AI provenance

### 10.2 E2E Triage Procedure

Define at `implementation-details/e2e-triage.md`:

| Category | Definition | Action |
|----------|------------|--------|
| `product_bug` | プロダクトのバグ | 修正タスク作成 |
| `spec_gap` | 仕様の曖昧さ | Spec AC更新 |
| `test_bug` | テストコードの不具合 | テスト修正 |
| `flake` | 一時的な不安定 | 安定化対策 |

---

## 11. CI/CD Integration

### PR時の必須チェック

```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    python -m pytest specs/*/tests/ \
      --ignore=specs/*/tests/e2e \
      --cov=src \
      --cov-fail-under=80
```

### Nightly E2E

```yaml
# .github/workflows/e2e-nightly.yml
schedule:
  - cron: '0 3 * * *'
steps:
  - name: Run E2E Tests
    run: npx playwright test specs/*/tests/e2e/
```

---

## Related Documents

- `config/testing/README.md` - 言語別設定テンプレート
- `docs/CI_CD_INTEGRATION.md` - CI/CDパイプライン設定
- `docs/TEST_PATTERNS.md` - テストパターン集
- `templates/plan_template.md` - テスト戦略セクション

> End of testing.md
