# Claude Code 指示プロンプト: Enterprise Hierarchy 連動性強化

## 作業ディレクトリ
`/Users/j620h-okzk/ZINOKZ/sdd_template_enterprise`

## 概要
Tecnos-STRIDE v4.6.0 に既に存在する Enterprise 機能（Epic/Feature階層、共有契約、coverage tier等）の **連動性を強化** する。
具体的には、以下の3つの問題を解決する：

1. **`stride` CLIにEpicコマンドがない** — Epic作成・検証は全て手動（`mkdir` + `cp` + `python3`）
2. **`stride_lint.py` がEnterprise拡張を呼んでいない** — `stride lint` でEpic検証が実行されない
3. **Feature作成時にEpic連携が自動化されていない** — `epic_ref` / `team_id` の自動設定がない

Enterprise機能は設定で On/Off を切り替えられるようにする（Off時は従来通りの動作を保証）。

## 現状分析（変更前に必ず確認すべきファイル）

以下のファイルを **必ず** 読み、現在の実装を正確に把握してから変更に着手すること。

### 🔴 最重要（変更対象のコアファイル）
| ファイル | 行数 | 現状の問題 |
|---------|------|-----------|
| `sdd-templates/bin/stride` | 1,313行 | Epic関連のサブコマンドが**一切ない** |
| `sdd-templates/tools/stride_lint.py` | 1,823行 | `stride_lint_enterprise.py` を**呼んでいない**。`--enterprise` フラグがない |
| `sdd-templates/tools/stride_lint_enterprise.py` | 772行 | 単体では動くが、stride CLIから呼ばれない |
| `sdd-templates/tools/epic_validator.py` | 891行 | 単体では動くが、stride CLIから呼ばれない |

### 🟡 参照が必要（構造を理解するために読む）
| ファイル | 用途 |
|---------|------|
| `memory/constitution.md` | ID規約（`epic_id`, `team_id` 等）、Epic Gate定義（line 368-402） |
| `sdd-templates/config/id_conventions.yaml` | ID規約のリファレンスコピー（SSoTはconstitution.md） |
| `sdd-templates/templates/epic_design_template.md` | Epic設計テンプレート（350行、充実済み） |
| `sdd-templates/templates/EPIC_APPROVAL.md` | Epic承認テンプレート（E1-E5 + Final） |
| `sdd-templates/templates/feature_breakdown_template.md` | Feature分割テンプレート |
| `sdd-templates/templates/basic_design_template.md` | line 82-89: `epic_ref`, `team_id`, `coverage_tier` フィールド（**既に存在**） |
| `agent_docs/commands.md` | Section 4: Enterprise Commands（手動手順が記載済み） |
| `archive/sample-specs/EPIC-SAMPLE/` | Epic のサンプルデータ |

### 🟢 影響を受けるドキュメント（最後に更新）
| ファイル | 更新内容 |
|---------|---------|
| `README.md` | stride CLIのコマンド一覧にEpicコマンド追加 |
| `sdd-templates/README.md` | **Tools セクション（line 97〜）のCLI一覧テーブルにEpicコマンド追加** |
| `agent_docs/commands.md` | Section 4の手動手順をstrideコマンドに置換 |
| `agent_docs/project_map.md` | Enterprise構造の説明を追加 |
| `sdd-templates/CHANGELOG.md` | 変更履歴追加 |
| `sdd-templates/VERSION` | バージョン更新 |

## 既存のEnterprise機能マップ（壊さないこと！）

```
constitution.md
├── Article X: Epic-Feature Hierarchy（ID規約・ルール定義済み）
├── Article XI: Shared Contract Governance
├── Article XIII: PM Dashboard Visibility
├── Epic Design Gate（5要件）
├── Feature Breakdown Gate（4要件）
├── Shared Contract Gate（3要件）
└── Epic Progress Gate（6要件）

テンプレート
├── epic_design_template.md — YAML SSoT + 9セクション
├── EPIC_APPROVAL.md — E1〜E5 + Final（6段階）
├── feature_breakdown_template.md
├── epic_progress_report_template.md
├── dependency_manifest_template.yaml
├── cross_refs_template.yaml
├── shared_contract_template.yaml
└── ccp_template.md

ツール
├── epic_validator.py — Epic設計検証・Gate評価・EPIC_APPROVAL解析
├── epic_progress_aggregator.py — PM ダッシュボード生成
├── stride_lint_enterprise.py — Epic/Feature階層・coverage tier・共有契約
├── dependency_checker.py — 依存サイクル検出
└── approval_router.py — 承認ルーティング

ディレクトリ構造
├── epics/ — Epic設計を格納（現在は空 .gitkeep のみ）
├── enterprise/ — CCP・通知（change_proposals/, notifications/）
└── shared/ — ADR・ポリシー・共有契約
    ├── decisions/
    ├── policies/ — coverage_tiers.yaml, dependency_rules.yaml, mode_policy.yaml
    └── contracts/ — （存在しないがテンプレートは用意済み）
```

## Step 1: Enterprise 設定ファイルの作成

`sdd-templates/config/enterprise.yaml` を新規作成する。

```yaml
# Enterprise Hierarchy Configuration
# Default: false (backward compatible with flat Feature structure)
enterprise:
  enabled: false
```

**⚠️ 設定ファイルにはコメントを最小限にすること。** 機能説明は README や manual に記載する。

## Step 2: `stride` CLI に Epic コマンド群を追加

### 2a. `show_help()` に Enterprise セクション追加

既存の `show_help()` 関数内、`symphony` コマンドの説明の後に以下を追加：

```
  # Enterprise Hierarchy (requires config/enterprise.yaml enabled: true)
  epic init <epic_id>          Initialize an Epic (epics/<epic_id>/)
  epic validate <epic_id>      Validate an Epic
  epic gates <epic_id>         Show Epic gate status
  epic features <epic_id>      List features in an Epic
  epic progress <epic_id>      Show progress summary (add --format markdown --output <path> for file)
  epic list                    List all Epics

  init <feature> --epic <id>   Create Feature under an Epic (auto-sets epic_ref & team_id)
    --team <TEAM_ID>           Override team_id (default: auto-detect from epic_design.md)
  lint <path> --enterprise     Also run enterprise validation (epic_ref, coverage_tier)
  lint --all --enterprise      Lint all Features + all Epics
```

### 2b. Enterprise 有効チェック関数を追加

`stride` スクリプトの先頭付近（`show_help()` の前）に追加：

```bash
# Resolve Python interpreter using the same strategy as stride-lint wrapper
# (sdd-templates/tools/stride-lint: prefers .venv/bin/python, falls back to python3)
_resolve_python() {
    local VENV_PY="$TEMPLATE_DIR/.venv/bin/python"
    if [[ -x "$VENV_PY" ]]; then
        echo "$VENV_PY"
    else
        echo "python3"
    fi
}

check_enterprise_enabled() {
    ENTERPRISE_CONFIG="$TEMPLATE_DIR/config/enterprise.yaml"
    if [ ! -f "$ENTERPRISE_CONFIG" ]; then
        echo -e "${RED}Error: Enterprise mode is not configured.${NC}"
        echo "Create sdd-templates/config/enterprise.yaml with 'enterprise.enabled: true'"
        return 1
    fi
    # Use same Python as stride-lint for reliable YAML parsing + venv PyYAML
    local PY
    PY=$(_resolve_python)
    local ENABLED
    ENABLED=$("$PY" -c "
import yaml, sys
try:
    data = yaml.safe_load(open('$ENTERPRISE_CONFIG'))
    print('true' if data and data.get('enterprise', {}).get('enabled') is True else 'false')
except Exception:
    print('false')
" 2>/dev/null) || ENABLED="false"

    if [ "$ENABLED" = "true" ]; then
        return 0
    else
        echo -e "${RED}Error: Enterprise mode is not enabled.${NC}"
        echo "Set 'enterprise.enabled: true' in sdd-templates/config/enterprise.yaml"
        return 1
    fi
}
```

> **⚠️ venv 整合性**: `stride-lint` wrapper（`sdd-templates/tools/stride-lint` line 5-7）は
> `sdd-templates/.venv/bin/python` を優先し、なければ `python3` にフォールバックする。
> `check_enterprise_enabled()` も `_resolve_python()` で同じ戦略を使い、
> PyYAML が venv にしか入っていない環境でも動作するようにする。

### 2c. `cmd_epic()` 関数を追加

```bash
cmd_epic() {
    check_enterprise_enabled || exit 1

    local SUBCMD="${1:-}"
    shift || true  # shift だけで SUBCMD を消費。残りの引数はそのまま "$@" で下位関数に渡る

    case "$SUBCMD" in
        init)
            cmd_epic_init "$@"
            ;;
        validate)
            cmd_epic_validate "$@"
            ;;
        gates)
            cmd_epic_gates "$@"
            ;;
        features)
            cmd_epic_features "$@"
            ;;
        progress)
            cmd_epic_progress "$@"
            ;;
        list)
            cmd_epic_list "$@"
            ;;
        *)
            echo -e "${RED}Unknown epic subcommand: $SUBCMD${NC}"
            echo "Usage: stride epic <init|validate|gates|features|progress|list> [args]"
            exit 1
            ;;
    esac
}
```

> **⚠️ 引数渡しの注意**: `shift` は1回だけ（SUBCMDを消費）。`shift 2` にすると
> `stride epic init EPIC-ORDER` の `EPIC-ORDER` が消えて下位関数に空引数が渡る。

### 2d. `cmd_epic_init()` 関数

```bash
cmd_epic_init() {
    local EPIC_ID="$1"
    if [ -z "$EPIC_ID" ]; then
        echo -e "${RED}Error: Epic ID required${NC}"
        echo "Usage: stride epic init <EPIC_ID>"
        echo "Example: stride epic init EPIC-ORDER"
        exit 1
    fi

    # Validate EPIC_ID format (must match ^EPIC-[A-Z]{3,}$)
    if ! echo "$EPIC_ID" | grep -qE '^EPIC-[A-Z]{3,}$'; then
        echo -e "${RED}Error: Invalid Epic ID format: $EPIC_ID${NC}"
        echo "Expected: EPIC-<3+ uppercase letters> (e.g., EPIC-ORDER, EPIC-PRICE)"
        exit 1
    fi

    local EPIC_DIR="epics/$EPIC_ID"

    if [ -d "$EPIC_DIR" ]; then
        echo -e "${YELLOW}Warning: $EPIC_DIR already exists${NC}"
        read -p "Overwrite templates? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi

    echo -e "${GREEN}Creating Epic: $EPIC_ID${NC}"

    # Create directories
    mkdir -p "$EPIC_DIR"/{features,docs}

    # Copy templates
    local TEMPLATES_DIR="$TEMPLATE_DIR/templates"
    local COPIED_FILES=()

    echo "  Copying epic_design.md..."
    cp "$TEMPLATES_DIR/epic_design_template.md" "$EPIC_DIR/epic_design.md"
    COPIED_FILES+=("$EPIC_DIR/epic_design.md")

    if [ -f "$TEMPLATES_DIR/feature_breakdown_template.md" ]; then
        echo "  Copying feature_breakdown.md..."
        cp "$TEMPLATES_DIR/feature_breakdown_template.md" "$EPIC_DIR/feature_breakdown.md"
        COPIED_FILES+=("$EPIC_DIR/feature_breakdown.md")
    fi

    echo "  Copying EPIC_APPROVAL.md..."
    cp "$TEMPLATES_DIR/EPIC_APPROVAL.md" "$EPIC_DIR/EPIC_APPROVAL.md"
    COPIED_FILES+=("$EPIC_DIR/EPIC_APPROVAL.md")

    if [ -f "$TEMPLATES_DIR/epic_progress_report_template.md" ]; then
        echo "  Copying EPIC_PROGRESS_REPORT.md..."
        cp "$TEMPLATES_DIR/epic_progress_report_template.md" "$EPIC_DIR/EPIC_PROGRESS_REPORT.md"
        COPIED_FILES+=("$EPIC_DIR/EPIC_PROGRESS_REPORT.md")
    fi

    # Multi-team scaffolding (agent_docs/commands.md Section 5 参照)
    if [ -f "$TEMPLATES_DIR/cross_team_dependency_manifest_template.yaml" ]; then
        echo "  Copying DEPENDENCY_MANIFEST.yaml..."
        cp "$TEMPLATES_DIR/cross_team_dependency_manifest_template.yaml" "$EPIC_DIR/DEPENDENCY_MANIFEST.yaml"
        COPIED_FILES+=("$EPIC_DIR/DEPENDENCY_MANIFEST.yaml")
    fi
    if [ -f "$TEMPLATES_DIR/ops_pack_registry_template.yaml" ]; then
        echo "  Copying OPS_PACK_REGISTRY.yaml..."
        cp "$TEMPLATES_DIR/ops_pack_registry_template.yaml" "$EPIC_DIR/OPS_PACK_REGISTRY.yaml"
        COPIED_FILES+=("$EPIC_DIR/OPS_PACK_REGISTRY.yaml")
    fi

    # Shared contracts directory and registry
    mkdir -p shared/contracts/{api,events}
    # CONTRACT_REGISTRY.yaml はファイル存在有無で判定（ディレクトリだけ存在するケースに対応）
    if [ ! -f "shared/contracts/CONTRACT_REGISTRY.yaml" ]; then
        if [ -f "$TEMPLATES_DIR/shared_contract_registry_template.yaml" ]; then
            cp "$TEMPLATES_DIR/shared_contract_registry_template.yaml" "shared/contracts/CONTRACT_REGISTRY.yaml"
            COPIED_FILES+=("shared/contracts/CONTRACT_REGISTRY.yaml")
            echo "  Copying CONTRACT_REGISTRY.yaml..."
        fi
    else
        echo "  CONTRACT_REGISTRY.yaml already exists, skipping"
    fi

    # Replace placeholders
    echo "  Replacing placeholders..."
    for f in "${COPIED_FILES[@]}"; do
        if [ -f "$f" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/EPIC-XXX/$EPIC_ID/g" "$f"
                sed -i '' "s/{{EPIC_ID}}/$EPIC_ID/g" "$f"
                sed -i '' "s/{{TEMPLATE_VERSION}}/$TEMPLATE_VERSION/g" "$f"
            else
                sed -i "s/EPIC-XXX/$EPIC_ID/g" "$f"
                sed -i "s/{{EPIC_ID}}/$EPIC_ID/g" "$f"
                sed -i "s/{{TEMPLATE_VERSION}}/$TEMPLATE_VERSION/g" "$f"
            fi
        fi
    done

    echo ""
    echo -e "${GREEN}Epic initialized: $EPIC_DIR/${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Edit $EPIC_DIR/epic_design.md (define features, teams, dependencies)"
    echo "  2. stride epic validate $EPIC_ID"
    echo "  3. Create features: stride init <feature> --epic $EPIC_ID"
    echo ""
}
```

### 2e. 他の `cmd_epic_*` 関数（既存ツールをラップ）

```bash
cmd_epic_validate() {
    local EPIC_ID="$1"
    if [ -z "$EPIC_ID" ]; then
        echo -e "${RED}Error: Epic ID required${NC}"
        exit 1
    fi
    local PY; PY=$(_resolve_python)
    "$PY" "$TOOLS_DIR/epic_validator.py" validate "epics/$EPIC_ID/"
}

cmd_epic_gates() {
    local EPIC_ID="$1"
    if [ -z "$EPIC_ID" ]; then
        echo -e "${RED}Error: Epic ID required${NC}"
        exit 1
    fi
    local PY; PY=$(_resolve_python)
    "$PY" "$TOOLS_DIR/epic_validator.py" gates "epics/$EPIC_ID/"
}

cmd_epic_features() {
    local EPIC_ID="$1"
    if [ -z "$EPIC_ID" ]; then
        echo -e "${RED}Error: Epic ID required${NC}"
        exit 1
    fi
    local PY; PY=$(_resolve_python)
    "$PY" "$TOOLS_DIR/epic_validator.py" features "epics/$EPIC_ID/"
}

cmd_epic_progress() {
    local EPIC_ID="$1"
    if [ -z "$EPIC_ID" ]; then
        echo -e "${RED}Error: Epic ID required${NC}"
        exit 1
    fi
    shift
    local PY; PY=$(_resolve_python)
    # デフォルトは summary 表示。--format markdown --output で Markdown ファイル生成も可能。
    # 追加引数はそのまま epic_progress_aggregator.py に渡す。
    # 例: stride epic progress EPIC-ORDER --format markdown --output epics/EPIC-ORDER/EPIC_PROGRESS_REPORT.md
    "$PY" "$TOOLS_DIR/epic_progress_aggregator.py" "epics/$EPIC_ID/" "$@"
}

cmd_epic_list() {
    echo "Epics:"
    echo "======"
    local FOUND=false
    for epic_dir in epics/EPIC-*/; do
        if [ -d "$epic_dir" ] && [ -f "$epic_dir/epic_design.md" ]; then
            FOUND=true
            local eid=$(basename "$epic_dir")
            echo "  $eid/"
        fi
    done
    if [ "$FOUND" = false ]; then
        echo "  (no epics found)"
    fi
}
```

### 2f. コマンドディスパッチャーに `epic` を追加

`stride` スクリプト末尾の `case` 文に以下を追加（`symphony)` の前に）：

```bash
    epic)
        shift
        cmd_epic "$@"
        ;;
```

### 2g. `cmd_init()` に `--epic` オプションを追加

`cmd_init()` の引数パーサー内に `--epic` オプションを追加する。

**変数宣言部分**（既存の `SCALE=""` の後に追加）：
```bash
    EPIC_REF=""
```

**case文に追加**（既存の `--scale)` ケースの後に）：
```bash
            --epic)
                if [ -z "$2" ] || [[ "$2" == -* ]]; then
                    echo -e "${RED}Error: --epic requires an Epic ID (e.g., EPIC-ORDER)${NC}"
                    exit 1
                fi
                EPIC_REF="$2"
                shift 2
                ;;
```

**Enterprise 有効チェック + team_id 事前解決**（`--epic` 指定時、**ディレクトリ作成より前** に追加）：

> **⚠️ 順序が重要**: team_id の判定は scaffolding（mkdir, cp）の **前** に行う。
> 複数チーム Epic で `--team` 未指定の場合、ここで `exit 1` して Feature を作らない。
> scaffolding 後に exit すると、中途半端なディレクトリが残ってワークツリーを汚す。

```bash
    if [ -n "$EPIC_REF" ]; then
        check_enterprise_enabled || exit 1
        # Validate epic exists
        if [ ! -d "epics/$EPIC_REF" ]; then
            echo -e "${RED}Error: Epic not found: epics/$EPIC_REF/${NC}"
            echo "Create it first: stride epic init $EPIC_REF"
            exit 1
        fi

        # Resolve and validate team_id BEFORE scaffolding (fail early without creating files)
        local PY
        PY=$(_resolve_python)

        # Extract team list from epic_design.md (used for both auto-detect and validation)
        local TEAM_DETECT_RESULT
        TEAM_DETECT_RESULT=$("$PY" -c "
import yaml, sys, re
try:
    with open('epics/$EPIC_REF/epic_design.md') as f:
        match = re.search(r'\`\`\`yaml\s*(.*?)\`\`\`', f.read(), re.DOTALL)
    if match:
        data = yaml.safe_load(match.group(1))
        teams = data.get('epic', {}).get('ownership', {}).get('teams', [])
        team_ids = [t.get('team_id', '') for t in teams if t.get('team_id')]
        if len(team_ids) == 1:
            print('ONE:' + team_ids[0])
        elif len(team_ids) > 1:
            print('MULTI:' + ','.join(team_ids))
        else:
            print('NONE:')
except Exception:
    print('ERROR:')
" 2>/dev/null) || TEAM_DETECT_RESULT="ERROR:"

        if [ -z "$TEAM_ID" ]; then
            # Auto-detect: single team → use it, multiple → require --team
            case "$TEAM_DETECT_RESULT" in
                ONE:*)
                    TEAM_ID="${TEAM_DETECT_RESULT#ONE:}"
                    echo "  Auto-detected team_id: $TEAM_ID (single team in $EPIC_REF)"
                    ;;
                MULTI:*)
                    local AVAILABLE_TEAMS="${TEAM_DETECT_RESULT#MULTI:}"
                    echo -e "${RED}Error: $EPIC_REF has multiple teams: $AVAILABLE_TEAMS${NC}"
                    echo "Specify --team explicitly: stride init $FEATURE_NAME --epic $EPIC_REF --team <TEAM_ID>"
                    exit 1
                    ;;
                *)
                    echo -e "${YELLOW}Warning: Could not detect team_id from $EPIC_REF.${NC}"
                    echo "Set team_id manually after creation, or use: stride init $FEATURE_NAME --epic $EPIC_REF --team TEAM-A"
                    ;;
            esac
        else
            # Validate: explicit --team must exist in epic_design.md's team list
            case "$TEAM_DETECT_RESULT" in
                ONE:*|MULTI:*)
                    local ALL_TEAMS="${TEAM_DETECT_RESULT#*:}"  # strip prefix
                    if ! echo ",$ALL_TEAMS," | grep -Fq ",$TEAM_ID,"; then
                        echo -e "${RED}Error: Team '$TEAM_ID' is not defined in $EPIC_REF.${NC}"
                        echo "Available teams: $ALL_TEAMS"
                        exit 1
                    fi
                    ;;
                *)
                    echo -e "${YELLOW}Warning: Could not read teams from $EPIC_REF to validate --team $TEAM_ID.${NC}"
                    ;;
            esac
        fi
    fi
```

**`epic_ref` と `team_id` の書き込み**（プレースホルダ置換の後、`echo "Feature initialized"` の前に追加）：

> この時点では team_id は事前解決済み。scaffolding は成功しているので sed で書き込むだけ。

```bash
    if [ -n "$EPIC_REF" ]; then
        echo "  Setting epic_ref to $EPIC_REF..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/epic_ref: null/epic_ref: \"$EPIC_REF\"/" "$FEATURE_DIR/basic_design.md"
        else
            sed -i "s/epic_ref: null/epic_ref: \"$EPIC_REF\"/" "$FEATURE_DIR/basic_design.md"
        fi

        if [ -n "$TEAM_ID" ]; then
            echo "  Setting team_id to $TEAM_ID..."
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/team_id: null/team_id: \"$TEAM_ID\"/" "$FEATURE_DIR/basic_design.md"
            else
                sed -i "s/team_id: null/team_id: \"$TEAM_ID\"/" "$FEATURE_DIR/basic_design.md"
            fi
        fi
    fi
```

**`--team` オプションの追加**（`cmd_init()` の引数パーサーに `--epic` と並べて追加）：

**変数宣言部分**（`EPIC_REF=""` の後に）：
```bash
    TEAM_ID=""
```

**case文に追加**（`--epic)` ケースの後に）：
```bash
            --team)
                if [ -z "$2" ] || [[ "$2" == -* ]]; then
                    echo -e "${RED}Error: --team requires a Team ID (e.g., TEAM-A)${NC}"
                    exit 1
                fi
                TEAM_ID="$2"
                shift 2
                ;;
```

## Step 3: `stride_lint.py` から Enterprise 検証を呼び出す

### 3a. `main()` に `--enterprise` フラグを追加

`stride_lint.py` の `main()` 関数内、既存の `parser.add_argument` の後に追加：

```python
    parser.add_argument("--enterprise", action="store_true",
                       help="Also run enterprise validation (epic_ref, coverage_tier, shared contracts)")
```

### 3b. Enterprise 設定の読み込み関数を追加

`stride_lint.py` の先頭付近（`load_id_conventions()` がある場合はその後、なければ適切な位置）に追加：

```python
def load_enterprise_config():
    """Load enterprise configuration from config/enterprise.yaml.
    
    Returns True if enterprise mode is enabled, False otherwise.
    """
    if yaml is None:
        return False
    
    script_dir = Path(__file__).parent.parent
    config_path = script_dir / "config" / "enterprise.yaml"
    
    if not config_path.exists():
        return False
    
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return bool(data.get("enterprise", {}).get("enabled", False))
    except Exception:
        return False
```

### 3c. `lint_feature()` の後に Enterprise 検証を追加

`main()` 関数内で `results` リストを構築した後、`report_results()` の前に以下を追加：

```python
    # Enterprise validation (when --enterprise flag is explicitly set)
    if args.enterprise:
        enterprise_enabled = load_enterprise_config()
        if not enterprise_enabled:
            print("Error: --enterprise flag requires enterprise.enabled: true in "
                  "sdd-templates/config/enterprise.yaml", file=sys.stderr)
            return 1  # 明示的に要求されたチェックが実行不能なので非0終了
        else:
            try:
                tools_dir = Path(__file__).parent
                sys.path.insert(0, str(tools_dir))
                
                # --- Feature-level enterprise checks ---
                # Uses stride_lint_enterprise.py (validates epic_ref, team_id, coverage_tier)
                from stride_lint_enterprise import EnterpriseValidator
                validator = EnterpriseValidator(base_dir)
                
                for feature in features:
                    ent_result = validator.validate_feature_enterprise(feature)
                    if ent_result.errors or ent_result.warnings:
                        for res in results:
                            if str(feature) in res.feature_path:
                                for err in ent_result.errors:
                                    res.add_error(err["code"], f"[Enterprise] {err['message']}")
                                for warn in ent_result.warnings:
                                    res.add_warning(warn["code"], f"[Enterprise] {warn['message']}")
                                break
                
                # --- Epic-level checks (--all 時のみ) ---
                # ⚠️ --all なしの単一Feature lintでは Epic を検証しない。
                # 単一 Feature が正常でも別 Epic の不備で lint が落ちるのを防ぐため。
                if args.all:
                    from epic_validator import EpicValidator
                    epics_dir = base_dir / "epics"
                    if epics_dir.exists():
                        for epic_dir in sorted(epics_dir.iterdir()):
                            if epic_dir.is_dir() and (epic_dir / "epic_design.md").exists():
                                ev = EpicValidator(epic_dir)
                                ev_result = ev.validate()
                                # EpicValidator の結果を LintResult に変換
                                epic_lint_result = LintResult(str(epic_dir))
                                for err_msg in ev_result.errors:
                                    # epic_validator は "CODE: message" 形式の文字列を返す
                                    parts = err_msg.split(": ", 1)
                                    code = parts[0] if len(parts) > 1 else "EPIC_ERROR"
                                    msg = parts[1] if len(parts) > 1 else err_msg
                                    epic_lint_result.add_error(code, f"[Epic] {msg}")
                                for warn_msg in ev_result.warnings:
                                    parts = warn_msg.split(": ", 1)
                                    code = parts[0] if len(parts) > 1 else "EPIC_WARNING"
                                    msg = parts[1] if len(parts) > 1 else warn_msg
                                    epic_lint_result.add_warning(code, f"[Epic] {msg}")
                                if epic_lint_result.errors or epic_lint_result.warnings:
                                    results.append(epic_lint_result)
                
            except ImportError as e:
                print(f"Error: Enterprise module not found ({e}). "
                      f"Cannot run --enterprise validation.", file=sys.stderr)
                return 1  # 明示的に要求されたチェックのモジュールがない = 失敗
```

### 3d. `LintConfig` に `enterprise` パラメータを追加

`LintConfig.__init__` に `enterprise` を追加：

```python
class LintConfig:
    def __init__(self, warn_only=False, coverage_report=False, fmt="text",
                 verbose=False, fail_on=None, lite_mode=False, enterprise=False):
        # ... existing fields ...
        self.enterprise = enterprise
```

`main()` の `LintConfig` 生成部分にも `enterprise=args.enterprise` を追加。

## Step 4: Epic 検証の経路整理

**設計ポイント（P1-3/P2-1 対策として重要）：**

| コマンド | Feature enterprise検証 | Epic検証 | 備考 |
|---------|----------------------|---------|------|
| `stride lint specs/foo/` | なし | なし | 従来通り |
| `stride lint specs/foo/ --enterprise` | ✅ `stride_lint_enterprise.py` | ❌ なし | 単一Feature lint では Epic を検証しない |
| `stride lint --all` | なし | なし | 従来通り |
| `stride lint --all --enterprise` | ✅ 全Feature | ✅ 全Epic（`epic_validator.py` 経由） | 全体検証 |
| `stride epic validate EPIC-ORDER` | なし | ✅ `epic_validator.py` | Epic単体検証 |

**`discover_features()` は変更しない。** Epic の検証は Step 3c で `--all --enterprise` 時にのみ `epics/` を走査する。

**Epic 検証は `epic_validator.py` の `EpicValidator.validate()` を使う。**
`stride_lint_enterprise.py` の `EnterpriseValidator.validate_epic()` は Feature-level の enterprise フィールド検証に使う。
Epic の Gate 判定・EPIC_APPROVAL.md 解析は `epic_validator.py` にしかないため、
lint 統合時もそちらを呼ぶことで `stride epic validate` との判定基準を一致させる。

## Step 5: ドキュメント更新

### 5a. `agent_docs/commands.md`

Section 4 の手動手順を stride コマンドに **併記** する（手動手順は残す — 柔軟性のため）。
先頭に以下を追加：

```markdown
### stride epic コマンド（推奨）

> Enterprise mode が有効な場合に使用可能。
> `sdd-templates/config/enterprise.yaml` で `enterprise.enabled: true` に設定。

- STRIDE_EPIC_INIT: `stride epic init <EPIC_ID>`
- STRIDE_EPIC_VALIDATE: `stride epic validate <EPIC_ID>`
- STRIDE_EPIC_GATES: `stride epic gates <EPIC_ID>`
- STRIDE_EPIC_FEATURES: `stride epic features <EPIC_ID>`
- STRIDE_EPIC_PROGRESS: `stride epic progress <EPIC_ID>`
- STRIDE_EPIC_LIST: `stride epic list`

- STRIDE_INIT_WITH_EPIC: `stride init <feature> --epic <EPIC_ID>`
  - basic_design.md の epic_ref を自動設定

- STRIDE_LINT_ENTERPRISE: `stride lint specs/<feature>/ --enterprise`
  - 従来の lint に加え、epic_ref/team_id/coverage_tier の整合性を検証

- STRIDE_LINT_ALL_ENTERPRISE: `stride lint --all --enterprise`
  - 全 Feature + 全 Epic を一括検証
```

### 5b. `sdd-templates/README.md`

`## Tools` → `### stride CLI (bin/stride)` のテーブル（line 97〜）に行を追加：

```markdown
| `stride epic init <EPIC_ID>` | Epic 初期化 |
| `stride epic validate <EPIC_ID>` | Epic 検証 |
| `stride epic gates <EPIC_ID>` | Epic Gate 状態表示 |
| `stride epic progress <EPIC_ID>` | Epic 進捗サマリ表示 |
| `stride epic list` | Epic 一覧 |
| `stride init --epic <EPIC_ID>` | Epic 配下に Feature 作成 |
| `stride lint --enterprise` | Enterprise 拡張検証 |
```

### 5c. `README.md`（プロジェクトルート）

`## stride CLI` セクションのコマンド一覧に追加：

```markdown
# Enterprise Hierarchy (enterprise.enabled: true)
stride epic init <EPIC_ID>             # Epic 作成
stride epic validate <EPIC_ID>         # Epic 検証
stride epic gates <EPIC_ID>            # Epic Gate 状態
stride epic features <EPIC_ID>         # Feature 一覧
stride epic progress <EPIC_ID>         # 進捗レポート生成
stride epic list                       # Epic 一覧
stride init <feature> --epic <EPIC_ID> # Epic 配下に Feature 作成
stride lint --enterprise               # Enterprise 拡張検証も実行
```

### 5d. `sdd-templates/CHANGELOG.md`

先頭に追加：

```markdown
## [4.7.0-tecnos-stride] - 2026-03-16

### Added

- **Enterprise Hierarchy CLI Integration** — Epic管理をstride CLIに統合
  - `config/enterprise.yaml` — Enterprise On/Off設定（デフォルト: Off、YAML正規パース）
  - `stride epic init <EPIC_ID>` — Epic作成（epic_design, EPIC_APPROVAL, DEPENDENCY_MANIFEST, OPS_PACK_REGISTRY, shared/contracts/ を一括生成）
  - `stride epic validate / gates / features / progress / list` — 既存ツール（epic_validator.py, epic_progress_aggregator.py）をCLIでラップ
  - `stride init <feature> --epic <EPIC_ID> [--team <TEAM_ID>]` — Feature作成時にepic_ref + team_idを自動設定（team_idはepic_design.mdから自動検出）
  - `stride lint --enterprise` — Feature lint時にstride_lint_enterprise.pyを自動呼び出し
  - `stride lint --all --enterprise` — 全Feature + 全Epic（epic_validator.py経由）を一括検証
  - Enterprise Off時は従来通りのフラットFeature構造で完全に動作（後方互換）
```

### 5e. `sdd-templates/VERSION`

```
4.7.0-tecnos-stride
```

## Step 6: 検証

### 6a. 既存テストが壊れていないことの確認

```bash
cd /Users/j620h-okzk/ZINOKZ/sdd_template_enterprise

# 1. Enterprise Off (デフォルト) で既存 sample_feature の lint が通ること
sdd-templates/tools/stride-lint sdd-templates/specs/sample_feature/ --warn-only

# 2. epic_validator.py の自己テストが通ること
python3 sdd-templates/tools/epic_validator.py --test

# 3. stride_lint_enterprise.py の自己テストが通ること
python3 sdd-templates/tools/stride_lint_enterprise.py --test
```

### 6b. Enterprise 機能の検証

```bash
# 1. enterprise.yaml の enabled を true に変更
echo -e "enterprise:\n  enabled: true" > sdd-templates/config/enterprise.yaml

# 2. Epic 作成
sdd-templates/bin/stride epic init EPIC-ORDER

# 3. epic_design.md が作成され、プレースホルダが置換されていることを確認
grep "EPIC-ORDER" epics/EPIC-ORDER/epic_design.md
grep "EPIC-XXX" epics/EPIC-ORDER/epic_design.md  # ヒットしないこと

# 4. Epic 一覧
sdd-templates/bin/stride epic list

# 5. Epic 検証
sdd-templates/bin/stride epic validate EPIC-ORDER

# 6. Epic Gate 状態
sdd-templates/bin/stride epic gates EPIC-ORDER

# 7. Feature 作成（Epic配下、デフォルトテンプレートは複数チームなので --team 必須）
sdd-templates/bin/stride init test_feature --epic EPIC-ORDER --team TEAM-A

# 8. basic_design.md に epic_ref と team_id が設定されていることを確認
grep "epic_ref" specs/test_feature/basic_design.md
# 期待: epic_ref: "EPIC-ORDER"
grep "team_id" specs/test_feature/basic_design.md
# 期待: team_id: "TEAM-A"

# 9. Enterprise lint（Feature単体）
sdd-templates/tools/stride-lint specs/test_feature/ --enterprise --warn-only

# 10. Enterprise lint（全体）
sdd-templates/tools/stride-lint --all --enterprise --warn-only

# 11. Enterprise Off で epic コマンドがエラーになることを確認
echo -e "enterprise:\n  enabled: false" > sdd-templates/config/enterprise.yaml
sdd-templates/bin/stride epic list  # エラーメッセージが出ること

# 12. テスト用ディレクトリを削除
rm -rf epics/EPIC-ORDER/ specs/test_feature/

# 13. enterprise.yaml を false に戻す
echo -e "enterprise:\n  enabled: false" > sdd-templates/config/enterprise.yaml
```

### 6c. Smoke Test（自動テスト — 必ず実行）

以下の bash スクリプトを `tests/test_enterprise_smoke.sh` として保存し、全テスト完了後に実行すること。
1つでも FAIL があれば修正を完了していない。

```bash
#!/bin/bash
set -e
PASS=0; FAIL=0; TOTAL=0

assert() {
    TOTAL=$((TOTAL + 1))
    if eval "$1" > /dev/null 2>&1; then
        echo "  ✅ $2"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $2"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Enterprise Smoke Tests ==="

# Test 1: Default Off
echo ""
echo "--- Test 1: Enterprise Off (default) ---"
echo -e "enterprise:\n  enabled: false" > sdd-templates/config/enterprise.yaml
assert "! sdd-templates/bin/stride epic list 2>&1 | grep -q 'Epics:'" "epic list blocked when disabled"
assert "sdd-templates/tools/stride-lint sdd-templates/specs/sample_feature/ --warn-only" "sample_feature lint passes with enterprise off"

# Test 2: Enable Enterprise
echo ""
echo "--- Test 2: Enterprise On ---"
echo -e "enterprise:\n  enabled: true" > sdd-templates/config/enterprise.yaml
assert "sdd-templates/bin/stride epic list" "epic list works when enabled"

# Test 3: Epic Init
echo ""
echo "--- Test 3: stride epic init ---"
sdd-templates/bin/stride epic init EPIC-SMOKE > /dev/null 2>&1
assert "test -f epics/EPIC-SMOKE/epic_design.md" "epic_design.md created"
assert "test -f epics/EPIC-SMOKE/EPIC_APPROVAL.md" "EPIC_APPROVAL.md created"
assert "test -f epics/EPIC-SMOKE/DEPENDENCY_MANIFEST.yaml" "DEPENDENCY_MANIFEST.yaml created"
assert "grep -q 'EPIC-SMOKE' epics/EPIC-SMOKE/epic_design.md" "EPIC-XXX placeholder replaced"
assert "! grep -q 'EPIC-XXX' epics/EPIC-SMOKE/epic_design.md" "no EPIC-XXX placeholder remaining"

# Test 4: Epic Validate (should work even with empty epic)
echo ""
echo "--- Test 4: stride epic validate ---"
assert "sdd-templates/bin/stride epic validate EPIC-SMOKE 2>&1 | grep -q 'Epic Validation'" "epic validate runs"

# Test 5: stride init --epic (with team handling)
echo ""
echo "--- Test 5: stride init --epic ---"

# Test 5a: Default template has multiple teams (TEAM-A, TEAM-B) → --team required → should fail
assert "! sdd-templates/bin/stride init smoke_feature --epic EPIC-SMOKE < /dev/null 2>&1" "multi-team epic without --team should fail"
assert "! test -d specs/smoke_feature" "failed init should NOT create feature directory"

# Test 5b: With invalid --team → should fail (team not in epic)
assert "! sdd-templates/bin/stride init smoke_feature --epic EPIC-SMOKE --team TEAM-Z 2>&1" "invalid team should fail"
assert "! test -d specs/smoke_feature" "invalid team should NOT create feature directory"

# Test 5c: With valid --team → should succeed (exit 0)
assert "echo 'y' | sdd-templates/bin/stride init smoke_feature --epic EPIC-SMOKE --team TEAM-A > /dev/null 2>&1" "init with --epic --team should succeed"
assert "test -f specs/smoke_feature/basic_design.md" "basic_design.md created with --team"
assert "grep -q 'epic_ref: \"EPIC-SMOKE\"' specs/smoke_feature/basic_design.md" "epic_ref auto-set"
assert "grep -q 'team_id: \"TEAM-A\"' specs/smoke_feature/basic_design.md" "team_id auto-set"

# Test 6: stride lint --enterprise (single feature, should NOT validate epics)
echo ""
echo "--- Test 6: stride lint --enterprise (single feature) ---"
# Epic 検証ヘッダー "[Epic]" が出力に含まれないことを厳密に確認
assert "! sdd-templates/tools/stride-lint specs/smoke_feature/ --enterprise --warn-only 2>&1 | grep -q '\[Epic\]'" "single feature lint does not include [Epic] validation results"

# Test 7: Argument passing (EPIC_ID reaches subcommands)
echo ""
echo "--- Test 7: Argument passing ---"
assert "sdd-templates/bin/stride epic gates EPIC-SMOKE 2>&1 | grep -q 'Gate Status'" "epic gates receives EPIC_ID"
assert "sdd-templates/bin/stride epic features EPIC-SMOKE 2>&1 | grep -q 'EPIC-SMOKE'" "epic features receives EPIC_ID"

# Cleanup
rm -rf epics/EPIC-SMOKE/ specs/smoke_feature/
echo -e "enterprise:\n  enabled: false" > sdd-templates/config/enterprise.yaml

echo ""
echo "=== Results: $PASS passed, $FAIL failed (of $TOTAL) ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

## チェックリスト（提出前の最終確認）

```
□ enterprise.yaml を作成し、コメントに "enabled: true" 文字列を含めていないか？（R1-P1修正）
□ _resolve_python() は stride-lint wrapper（tools/stride-lint line 5-7）と同じ .venv 解決か？（R2-P2修正）
□ check_enterprise_enabled() は _resolve_python() 経由か？（R2-P2修正）
□ cmd_epic_validate/gates/features/progress は全て _resolve_python() 経由か？（bare python3 禁止）（R3-P2修正）
□ cmd_epic() の shift は1回だけか？（shift 2 にしていないか？）（R1-P1修正）
□ stride lint --enterprise で enterprise 無効時は return 1 で非0終了するか？（R2-P2修正）
□ stride lint --enterprise で ImportError 時も return 1 で非0終了するか？（R3-P2修正）
□ stride lint --enterprise で Epic 検証は --all 時のみか？（R1-P2修正）
□ Epic 検証は epic_validator.py の EpicValidator.validate() を使っているか？（R1-P1修正）
□ cmd_init --epic の team_id 判定は scaffolding（mkdir, cp）の前に実行されるか？（R3-P2修正）
□ 複数チーム Epic で --team 未指定時、Feature ディレクトリが作られずに exit 1 するか？（R3-P2修正）
□ --team で指定した値が epic_design.md の teams に存在しない場合、exit 1 するか？（R4-P2修正）
□ cmd_init に --team オプションを追加したか？（R1-P2修正）
□ cmd_epic_progress() は追加引数（--format, --output）を下位に渡しているか？（R1-P3修正）
□ CONTRACT_REGISTRY.yaml の生成条件はファイル存在有無（!-f）で判定しているか？（R2-P2修正）
□ Enterprise Off 時に sample_feature の lint が通るか？
□ stride bin に check_enterprise_enabled() 関数を追加したか？
□ stride bin に cmd_epic() と 6つのサブコマンドを追加したか？
□ stride bin のコマンドディスパッチャーに epic) を追加したか？
□ stride bin の show_help() に Epic コマンドと --epic/--team/--enterprise の説明を追加したか？
□ stride_lint.py に load_enterprise_config() を追加したか？
□ stride_lint.py の main() に --enterprise フラグを追加したか？
□ stride_lint.py で Feature は stride_lint_enterprise を、Epic は epic_validator を使い分けているか？
□ cmd_epic_init で DEPENDENCY_MANIFEST.yaml, OPS_PACK_REGISTRY.yaml, shared/contracts/ も生成しているか？
□ epic_validator.py --test が通るか？
□ stride_lint_enterprise.py --test が通るか？
□ tests/test_enterprise_smoke.sh が全て PASS するか？
□ agent_docs/commands.md にstrideコマンドを追記したか？
□ README.md（ルート）のCLI一覧を更新したか？
□ sdd-templates/README.md のCLIテーブル（line 97〜）を更新したか？
□ CHANGELOG.md に v4.7.0 のエントリを追加したか？
□ VERSION を 4.7.0-tecnos-stride に更新したか？
□ 変数名・関数名・ファイルパスは実コードから転記したか？（推測で書いていないか？）
□ 既存の epic_validator.py / stride_lint_enterprise.py のインターフェースを変更していないか？
```

## ⚠️ やってはいけないこと

1. **既存の `epic_validator.py` / `stride_lint_enterprise.py` の内部ロジックを変更しない** — これらは単体で動作確認済み。CLIからラップするだけ
2. **`constitution.md` の ID 規約を変更しない** — `epic_id: "^EPIC-[A-Z]{3,}$"` 等は既に定義済み
3. **`basic_design_template.md` の `epic_ref` / `team_id` / `coverage_tier` フィールドを変更しない** — 既にline 82-89に存在
4. **`discover_features()` のロジックを変更しない** — Feature探索は既存のまま。Epicの探索は別パスで
5. **テンプレートファイル（`epic_design_template.md`, `EPIC_APPROVAL.md` 等）を変更しない** — 既に充実している

## 設計判断の根拠

| 判断 | 理由 |
|------|------|
| `enterprise.yaml` で On/Off | 小規模PJ では不要。デフォルトOff で既存互換100% |
| `stride epic` サブコマンド | `stride init` / `stride lint` と同じUXパターン。手動の`mkdir`+`cp`+`python3` を排除 |
| `stride init --epic` | Feature作成時にEpic紐付けを忘れない仕組み。`epic_ref: null` → `epic_ref: "EPIC-ORDER"` を自動 |
| `--enterprise` フラグ | Enterprise拡張の検証は任意。パフォーマンス懸念がある大規模PJでは明示的に指定 |
| 既存ツールをラップ | `epic_validator.py` / `stride_lint_enterprise.py` は完成済み。新コードを最小限に |

---

完了したら:
```
openclaw system event --text "Done: STRIDE Enterprise Hierarchy 連動性強化 v4.7.0" --mode now
```
