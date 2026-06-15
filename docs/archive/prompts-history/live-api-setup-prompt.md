# 指示プロンプト: Multi-Model Evaluator — ライブAPI実行の有効化

**作業ディレクトリ:** `/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

---

## 目的

`stride evaluate` コマンドが現在 `PROVIDER_ERROR` で終了している。
原因は `.venv`（Python 3.12.7、pyenv 管理）に `openai` と `google-genai` が未インストールであること。

このプロンプトでは以下を実現する：

1. `.venv` に必要なパッケージをインストールする
2. `sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --phase design` が正常終了する（exit 0 or 1）ことを確認する
3. `@pytest.mark.api` マーカーで保護されたライブ API テストを `symphony/tests/test_evaluator_live.py` に追加する
4. 既存の **272 テスト**（`symphony/tests/` 244件 + `tests/` 28件）が `-m "not api"` で全 PASS のままであることを確認する

---

## 実装前に必ず読むこと（推測で書かない）

```bash
# 1. .venv の構成を確認（Python バージョン・ベースインタープリタ）
cat .venv/pyvenv.cfg
.venv/bin/python --version
.venv/bin/pip list

# 2. 要件ファイルを確認
cat sdd-templates/requirements-ai-eval.txt

# 3. stride コマンドが .venv/bin/python を使うことを確認
grep -A8 "_resolve_python" sdd-templates/bin/stride | head -12

# 4. multi_model_evaluator.py の --test フラグと _run_self_tests() の実装を確認
grep -n "\-\-test\|_run_self_tests\|args.test" sdd-templates/tools/multi_model_evaluator.py

# 5. _call_gemini の google-genai インポートパスを確認（バージョン依存）
grep -n "from google\|import google\|genai" sdd-templates/tools/multi_model_evaluator.py

# 6. 既存ライブテスト用のパターンを確認（subprocess 方式の参照）
grep -A20 "def test_starter_skip_without_api_keys" symphony/tests/test_evaluator_core.py

# 7. pyproject.toml のテスト収集パスとマーカー定義を確認
cat pyproject.toml
# → testpaths = ["symphony/tests", "tests"] — 両方が収集対象

# 8. 現在のテスト件数を確認（272 件が基準値）
.venv/bin/python -m pytest -m "not api" -q --tb=no 2>&1 | tail -3

# 9. 現在の PROVIDER_ERROR を再現して原因を確認
.venv/bin/python sdd-templates/tools/multi_model_evaluator.py \
    specs/FEAT-ERPSAMPLE/ --phase design --allow-provider-degraded 2>&1

# 10. main() の API キー必須チェック（OPENAI_API_KEY と OPENAI_MODEL の両方が必須）
sed -n '797,803p' sdd-templates/tools/multi_model_evaluator.py
```

---

## Step 1: パッケージインストール

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise
.venv/bin/pip install -r sdd-templates/requirements-ai-eval.txt
```

**期待される結果:** `openai` と `google-genai` がインストールされる。
（`google-cloud-aiplatform` は Vertex AI 用。インストールに時間がかかる場合は先に `openai google-genai` だけ入れてから続行してよい。）

インストール後、インポートが通ることを確認する：

```bash
.venv/bin/python -c "import openai; print('openai:', openai.__version__)"
.venv/bin/python -c "from google import genai; from google.genai import types; print('google-genai: ok')"
```

**⚠️ `from google import genai` が失敗した場合のみ** `_call_gemini` のインポートを修正する。
エラーなければ修正不要。

---

## Step 2: ライブ API 疎通確認

### 2-1. `--test` フラグで OpenAI のみ確認

`multi_model_evaluator.py` には `--test` フラグ（`_run_self_tests()`）が実装済みである。
これを使って OpenAI API が疎通することを最初に確認する：

```bash
.venv/bin/python sdd-templates/tools/multi_model_evaluator.py --test 2>&1
```

**期待:** `Self-tests passed.`（exit 0）
**失敗した場合:** エラーメッセージを確認し、原因を特定してから Step 2-2 に進む。
`.env.local` のモデル名やキーの問題であれば **Hitoshi に確認を求めること（自分で .env.local を変更しない）**。

### 2-2. `multi_model_evaluator.py` 直接実行でフル確認

```bash
.venv/bin/python sdd-templates/tools/multi_model_evaluator.py \
    specs/FEAT-ERPSAMPLE/ --phase design --format text 2>&1
```

**期待される終了コード:**
- `0` (PASS または WARN) → 正常
- `1` (FAIL) → 正常（API 疎通は成功、仕様側が低評価）
- `2` (PROVIDER_ERROR) → API 呼び出し失敗 → Step 2-3 で切り分ける

**注意:** exit 0 は PASS 専用ではない。`overall="WARN"` も exit 0 を返す（Borderline で secondary が PASS した場合、または `--allow-provider-degraded` 時）。

### 2-3. PROVIDER_ERROR が続く場合の切り分け

```bash
# OpenAI のみで切り分け（Gemini を無効化して確認）
GEMINI_MODEL="" .venv/bin/python sdd-templates/tools/multi_model_evaluator.py \
    specs/FEAT-ERPSAMPLE/ --phase design --allow-provider-degraded 2>&1
```

どちらのモデルが失敗しているかを特定して報告する。

### 2-4. `stride` コマンド経由でのエンドツーエンド確認

**⚠️ このステップは必須。** Python 直接実行で成功しても、`stride` コマンド経由の配線（`_resolve_python()` → `.venv/bin/python`）が壊れていれば本来の目的を達成できない。

```bash
sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --phase design 2>&1
```

**期待:** exit 0 または 1。Step 2-2 と同じ結果が返ること。
**exit 2 が返った場合:** `_resolve_python()` が `.venv/bin/python` を見つけられていない可能性がある。
以下で確認：
```bash
bash -x sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --phase design 2>&1 | grep "VENV_PY\|TEMPLATE_DIR" | head -5
```

---

## Step 3: `@pytest.mark.api` ライブテストの追加

### 3-1. テストファイルの場所と構成

`symphony/tests/test_evaluator_live.py` を新規作成する。

**実装前に必ず確認する事項（推測で書かない）：**

```bash
# テスト内で使う sys.executable が .venv/bin/python を指すか確認
.venv/bin/python -c "import sys; print(sys.executable)"

# FEAT-ERPSAMPLE の coverage_tier を確認（starter だとスキップされるため）
grep "coverage_tier" specs/FEAT-ERPSAMPLE/basic_design.md

# .env.local のキー名を確認（テスト内でスキップ判定に使う）
grep -E "^OPENAI_API_KEY=|^OPENAI_MODEL=|^GEMINI_API_KEY=" .env.local | sed 's/=.*/=***/'
```

### 3-2. テスト実装方針

**subprocess 方式を採用すること**（`test_starter_skip_without_api_keys` と同じパターン）。
理由: `_call_openai()` を直接呼ぶと `load_env_local()` が実行されず `.env.local` のキーがロードされない。
`main()` 全体を subprocess 経由で呼ぶことで実運用と同じ経路をテストできる。

```python
import subprocess, sys, os, json
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "sdd-templates" / "tools"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FEATURE_DIR = PROJECT_ROOT / "specs" / "FEAT-ERPSAMPLE"
```

### 3-3. スキップ条件

`OPENAI_API_KEY` **と** `OPENAI_MODEL` の**両方**が設定されていなければ `pytest.skip` する。
理由: `main()` は `OPENAI_API_KEY` 未設定で exit 2、`OPENAI_MODEL` 未設定でも exit 2 を返す。
API キーだけチェックしてモデル名を見ないと CI で exit 2 を踏む。

```python
# スキップ条件の定義（各テスト関数の冒頭で呼ぶか、module-level の fixture で使う）
def _skip_if_no_api_config():
    """OPENAI_API_KEY と OPENAI_MODEL の両方が必要。"""
    # load_env_local は subprocess 内で呼ばれるので、
    # ここでは .env.local を直接読んで判定する
    env_local = PROJECT_ROOT / ".env.local"
    if not env_local.exists():
        pytest.skip("No .env.local found")
    content = env_local.read_text()
    has_key = any(line.startswith("OPENAI_API_KEY=") and len(line.split("=", 1)[1].strip()) > 0
                  for line in content.splitlines())
    has_model = any(line.startswith("OPENAI_MODEL=") and len(line.split("=", 1)[1].strip()) > 0
                    for line in content.splitlines())
    if not (has_key and has_model):
        pytest.skip("OPENAI_API_KEY and/or OPENAI_MODEL not configured in .env.local")
```

### 3-4. テスト 3 件

```python
# テスト 1: design フェーズで有効な result（PASS, FAIL, or WARN）を返す
@pytest.mark.api
def test_live_evaluate_design_exits_normally():
    """ライブ API で design フェーズを評価し、exit 0(PASS/WARN) or 1(FAIL) を返す。"""
    _skip_if_no_api_config()
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "multi_model_evaluator.py"),
         str(FEATURE_DIR), "--phase", "design"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode in (0, 1), \
        f"Expected exit 0 or 1, got {result.returncode}:\nstdout: {result.stdout}\nstderr: {result.stderr}"

# テスト 2: secondary を意図的に失敗させ、--allow-provider-degraded で exit 0 or 1
@pytest.mark.api
def test_live_evaluate_degraded_secondary_error():
    """secondary に無効な API key を渡して意図的に失敗させ、
    --allow-provider-degraded 付きでも primary の結果で正常終了すること。"""
    _skip_if_no_api_config()
    # GEMINI_MODEL が設定されていなければ secondary 自体が呼ばれないので skip
    env_local = PROJECT_ROOT / ".env.local"
    content = env_local.read_text()
    has_gemini_model = any(
        line.startswith("GEMINI_MODEL=") and len(line.split("=", 1)[1].strip()) > 0
        for line in content.splitlines()
    )
    if not has_gemini_model:
        pytest.skip("GEMINI_MODEL not configured — secondary never called, cannot test degraded path")
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = "invalid-key-for-testing"
    # GEMINI_MODEL はそのまま（呼び出しを試みて認証エラーで失敗する）
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "multi_model_evaluator.py"),
         str(FEATURE_DIR), "--phase", "design", "--allow-provider-degraded"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    assert result.returncode in (0, 1), \
        f"Expected exit 0 or 1 with degraded mode, got {result.returncode}:\n{result.stderr}"

# テスト 3: --format json で JSON 出力が valid かつ overall キーを持つ
@pytest.mark.api
def test_live_evaluate_json_output_is_valid():
    """--format json で出力が JSON パース可能で overall/exit_code キーを持つ。"""
    _skip_if_no_api_config()
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "multi_model_evaluator.py"),
         str(FEATURE_DIR), "--phase", "design", "--format", "json"],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode in (0, 1), \
        f"Expected exit 0 or 1, got {result.returncode}:\n{result.stderr}"
    data = json.loads(result.stdout)
    assert data["overall"] in ("PASS", "FAIL", "WARN"), \
        f"Unexpected overall: {data['overall']}"
    assert isinstance(data["exit_code"], int)
```

### 3-5. テスト 2 の設計意図（なぜ `GEMINI_MODEL=""` ではダメか）

`GEMINI_MODEL=""` は secondary を**無効化**する（`_call_gemini` が `None` を返す）。
これは degraded mode ではなく「secondary なし」の正常系である。

degraded mode を検証するには、secondary が**呼ばれたが失敗する**状態を作る必要がある。
`GEMINI_API_KEY="invalid-key-for-testing"` を渡すことで、secondary が呼び出され → 認証エラー → `{"error": ...}` が返り → `--allow-provider-degraded` が効く、という実際の degraded 経路を通る。

---

## Step 4: 回帰確認

**⚠️ `symphony/tests/` だけでなく repo root から実行すること。**
`pyproject.toml` の `testpaths = ["symphony/tests", "tests"]` により、
Phase 1 で追加した統合テスト群（`tests/` 配下の 28 件）も収集対象である。

```bash
# 1. 全テスト（api マーカーを除く）が壊れていないことを確認
.venv/bin/python -m pytest -m "not api" -q --tb=short 2>&1 | tail -5
# 期待: 272 passed（symphony/tests/ 244件 + tests/ 28件）

# 2. evaluator core + bridge tests を個別確認
.venv/bin/python -m pytest \
    symphony/tests/test_evaluator_core.py \
    symphony/tests/test_stride_bridge_evaluate.py \
    -v --tb=short 2>&1 | tail -25
# 期待: 17 passed

# 3. 新規ライブテストを実行
.venv/bin/python -m pytest symphony/tests/test_evaluator_live.py -m api -v --tb=short 2>&1
# 期待: 3 passed（SKIPPED は API 未設定時のみ許容）
```

---

## 完了基準

以下が**すべて**満たされていること：

| # | 確認項目 | 合格条件 |
|---|---------|---------|
| 1 | パッケージインストール | `import openai` / `from google import genai` が `.venv/bin/python` で通る |
| 2 | `--test` フラグ | `Self-tests passed.`（exit 0） |
| 3 | `multi_model_evaluator.py` 直接実行 | `specs/FEAT-ERPSAMPLE/ --phase design` が exit 0 or 1 |
| 4 | **`stride evaluate` コマンド経由** | `sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --phase design` が exit 0 or 1 |
| 5 | ライブテスト追加 | `test_evaluator_live.py` に 3 件の `@pytest.mark.api` テスト、subprocess 方式 |
| 6 | 全テスト回帰なし | repo root で `-m "not api"` 実行し `272 passed` |
| 7 | evaluator core + bridge | `17 passed` |
| 8 | CI-safe | `OPENAI_API_KEY` または `OPENAI_MODEL` のいずれかが未設定の環境では api テストが全 SKIP、残り 272 件が通る |

---

## 完了後の報告

以下の形式で報告すること：

```
=== 完了報告 ===

インストール済みパッケージ:
  openai: <version>
  google-genai: <version>

--test フラグ結果:
  exit code: 0
  出力: Self-tests passed.

stride evaluate 実行結果:
  Python 直接実行:
    exit code: <0|1>
    Overall: <PASS|FAIL|WARN>
    Primary weighted_score: <score>
  stride コマンド経由:
    exit code: <0|1>
    Overall: <PASS|FAIL|WARN>

テスト結果:
  全テスト（-m "not api", repo root）: <N> passed
  evaluator core + bridge: 17 passed
  ライブテスト（-m api）: <N> passed

追加ファイル:
  symphony/tests/test_evaluator_live.py（新規, 3件）
```

---

## トラブルシューティング

### `from google import genai` が失敗する場合

`google-genai` パッケージのインポートパスを確認する：
```bash
.venv/bin/python -c "import google.genai; print(dir(google.genai))" 2>&1
```

パスが異なる場合のみ `_call_gemini` のインポート行を修正する。
ただし **`.env.local` は変更しない**。

### `--test` が失敗する場合（モデル名エラー等）

`.env.local` の `OPENAI_MODEL` が API で認識されない場合は、エラーメッセージをそのまま Hitoshi に確認を求めること。自分で書き換えない。

### `stride` コマンドが `.venv/bin/python` を使わない場合

`_resolve_python()` が `.venv/bin/python` の存在チェックに `TEMPLATE_DIR` を使っている。
`stride` コマンドを `sdd-templates/bin/stride` から実行している限り `TEMPLATE_DIR` は自動設定されるため問題ない。
念のため確認：
```bash
bash -x sdd-templates/bin/stride evaluate specs/FEAT-ERPSAMPLE/ --phase design 2>&1 | grep "TEMPLATE_DIR\|VENV_PY" | head -5
```
