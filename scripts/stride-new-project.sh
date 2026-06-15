#!/usr/bin/env bash
#
# stride-new-project.sh — Initialize a new project from sdd_template_enterprise
#
# Usage:
#   stride new-project <project_name> [options]
#
# This script is called by `stride new-project` or can be run standalone.
# It automates the post-clone setup when using sdd_template_enterprise
# as a GitHub Template Repository.
#
# What it does:
#   1. Remove sample specs, epics, and archive (optional)
#   2. Replace placeholder names with your project name
#   3. Initialize label_feature_map.json
#   4. Set up .claude/settings.json hooks
#   5. Create initial feature (optional)
#   6. Initialize git (if not already)
#

set -e

# ─── Colors ───────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Defaults ─────────────────────────────────────────────
PROJECT_NAME=""
ORG_NAME=""
SCALE="starter"
KEEP_SAMPLES=false
FIRST_FEATURE=""
EPIC_PREFIX=""
DRY_RUN=false
SKIP_GIT=false
JSON_OUTPUT=false
# v5.3.1: external tracker auto-creation
GITHUB_PROJECT_TITLE=""         # empty → derive from PROJECT_NAME; set "-" to skip
LINEAR_PROJECT_NAME=""          # empty → derive from PROJECT_NAME; set "-" to skip
NO_GITHUB_PROJECT=false
NO_LINEAR_PROJECT=false

# ─── Help ─────────────────────────────────────────────────
show_help() {
    cat << 'EOF'
stride new-project — Initialize a new project from SDD Template Enterprise

Usage:
  stride new-project <project_name> [options]

Arguments:
  project_name          Project name (e.g., my_erp_addon, cbp-marketplace)

Options:
  --org <name>          GitHub organization (e.g., tecnos-japan-cbp)
  --scale <level>       Monorepo scale: starter (default), standard, enterprise
  --epic-prefix <pfx>   Epic prefix for WI IDs (e.g., ERP, SF, MKT). Auto-derived if omitted.
  --first-feature <name> Create an initial feature with stride init
  --keep-samples        Keep sample specs/epics/archive (don't delete)
  --skip-git            Don't initialize git or make initial commit
  --dry-run             Show what would be done without doing it
  --json                Output structured JSON to stdout (for AI agents)

  # v5.3.1: external tracker binding
  --github-project <t>  Title for the per-project GitHub Project V2
                        (default: "<project_name> SDD Board"; use "-" to skip)
  --linear-project <n>  Name for the per-project Linear Project
                        (default: <project_name>; use "-" to skip)
  --no-github-project   Skip GitHub Project V2 auto-creation
  --no-linear-project   Skip Linear Project auto-creation (alias: --no-linear)

  --help                Show this help

Examples:
  # After cloning from GitHub Template:
  cd my-new-project
  ./scripts/stride-new-project.sh my_erp_addon --org tecnos-japan-cbp

  # With initial feature and enterprise scale:
  stride new-project cbp_marketplace --org tecnos-japan-cbp \
    --scale enterprise --first-feature order_import --epic-prefix MKT

  # Preview changes:
  stride new-project my_project --dry-run

Workflow:
  1. GitHub: "Use this template" → create new repo
  2. git clone <new-repo>
  3. cd <new-repo>
  4. stride new-project <name> [options]    ← THIS SCRIPT
  5. stride intake <first_feature>          (or use --first-feature)
EOF
}

# ─── Parse Arguments ──────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --org)
            ORG_NAME="$2"
            shift 2
            ;;
        --scale)
            case "$2" in
                starter|standard|enterprise) SCALE="$2" ;;
                *) echo -e "${RED}Error: Invalid scale: $2. Use starter|standard|enterprise${NC}" >&2; exit 2 ;;
            esac
            shift 2
            ;;
        --epic-prefix)
            EPIC_PREFIX="$2"
            shift 2
            ;;
        --first-feature)
            FIRST_FEATURE="$2"
            shift 2
            ;;
        --keep-samples)
            KEEP_SAMPLES=true
            shift
            ;;
        --skip-git)
            SKIP_GIT=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --json)
            # Agent-friendly: structured JSON output for AI agents
            JSON_OUTPUT=true
            shift
            ;;
        --github-project)
            GITHUB_PROJECT_TITLE="$2"
            shift 2
            ;;
        --linear-project)
            LINEAR_PROJECT_NAME="$2"
            shift 2
            ;;
        --no-github-project)
            NO_GITHUB_PROJECT=true
            shift
            ;;
        --no-linear-project|--no-linear)
            NO_LINEAR_PROJECT=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option: $1${NC}" >&2
            show_help >&2
            exit 2
            ;;
        *)
            if [ -z "$PROJECT_NAME" ]; then
                PROJECT_NAME="$1"
            else
                echo -e "${RED}Error: Unexpected argument: $1${NC}" >&2
                exit 2
            fi
            shift
            ;;
    esac
done

# ─── Logging & JSON helpers ──────────────────────────────
log() {
    if [ "$JSON_OUTPUT" = true ]; then
        echo -e "$@" >&2
    else
        echo -e "$@"
    fi
}

STEPS_COMPLETED=()
STEPS_SKIPPED=()

json_output() {
    local ok="$1"
    local exit_code="$2"
    local error_msg="${3:-}"
    local suggested="${4:-}"

    python3 -c "
import json, sys
ok = sys.argv[5] == 'true'
exit_code = int(sys.argv[6])
data = {
    'ok': ok,
    'project_name': sys.argv[7],
    'org_name': sys.argv[8],
    'scale': sys.argv[9],
    'steps_completed': sys.argv[1].split(',') if sys.argv[1] else [],
    'steps_skipped': sys.argv[2].split(',') if sys.argv[2] else [],
    'exit_code': exit_code,
}
if ok:
    data['message'] = 'Project initialized successfully'
else:
    data['error'] = sys.argv[3]
    data['suggested_action'] = sys.argv[4]
json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
print()
" "$(IFS=,; echo "${STEPS_COMPLETED[*]}")" "$(IFS=,; echo "${STEPS_SKIPPED[*]}")" "$error_msg" "$suggested" "$ok" "$exit_code" "$PROJECT_NAME" "${ORG_NAME:-}" "$SCALE"
}

if [ "$JSON_OUTPUT" = true ]; then
    trap 'json_output false 1 "Step failed: check stderr for details" "stride-new-project.sh を --dry-run で再実行して原因を確認してください"' ERR
fi

if [ -z "$PROJECT_NAME" ]; then
    if [ "$JSON_OUTPUT" = true ]; then
        json_output false 2 "Project name is required" "stride new-project <project_name> の形式で指定してください"
    else
        echo -e "${RED}Error: Project name is required${NC}"
        echo ""
        show_help
    fi
    exit 2
fi

# ─── Derived Values ───────────────────────────────────────

# Project ID: uppercase, no punctuation (for FEAT- prefix)
PROJECT_ID=$(echo "$PROJECT_NAME" | tr '[:lower:]' '[:upper:]' | tr -d '[:punct:]' | tr -d '_' | tr -d '-')

# Epic prefix: use provided or derive from project name (first 3+ chars)
if [ -z "$EPIC_PREFIX" ]; then
    EPIC_PREFIX=$(echo "$PROJECT_ID" | cut -c1-4)
fi

# Human-readable project title
PROJECT_TITLE=$(echo "$PROJECT_NAME" | tr '_-' ' ' | sed 's/\b\(.\)/\u\1/g' 2>/dev/null || echo "$PROJECT_NAME")

# ─── Dry Run Wrapper ─────────────────────────────────────
run() {
    if [ "$DRY_RUN" = true ]; then
        log "  ${CYAN}[dry-run]${NC} $*"
    else
        eval "$@"
    fi
}

# ─── Banner ───────────────────────────────────────────────
log ""
log "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
log "${BOLD}║  stride new-project — SDD Template Initialization   ║${NC}"
log "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
log ""
log "  Project:      ${GREEN}${PROJECT_NAME}${NC}"
log "  Project ID:   ${GREEN}${PROJECT_ID}${NC}"
log "  Epic Prefix:  ${GREEN}${EPIC_PREFIX}${NC}"
log "  Scale:        ${GREEN}${SCALE}${NC}"
[ -n "$ORG_NAME" ] && log "  Organization: ${GREEN}${ORG_NAME}${NC}"
[ -n "$FIRST_FEATURE" ] && log "  First Feature:${GREEN}${FIRST_FEATURE}${NC}"
log ""

if [ "$DRY_RUN" = true ]; then
    log "${YELLOW}═══ DRY RUN MODE — no changes will be made ═══${NC}"
    log ""
fi

# ─── Step 1: Clean up samples ────────────────────────────
log "${BOLD}Step 1/7: Clean up sample files${NC}"

if [ "$KEEP_SAMPLES" = true ]; then
    log "  ${YELLOW}Skipped (--keep-samples)${NC}"
    STEPS_SKIPPED+=("remove_samples")
else
    # Remove sample specs
    # Note: val_a01/val_b01/val_c01 は VALUE Upstream Extension Phase A/B/C の SDD 自己適用記録 (v6.0 開発履歴).
    # メインリポでは Constitution Article XV-XVII の根拠 + dogfooding 証跡として保持されるが、
    # テンプレート利用者にとってはノイズなので新プロジェクト初期化時に自動削除する.
    for dir in specs/sample_erp_addon specs/sample_feature specs/salesforce_connector specs/sample_agentic specs/FEAT-ERPSAMPLE specs/val_a01 specs/val_b01 specs/val_c01; do
        if [ -d "$dir" ]; then
            log "  Removing $dir/"
            run "rm -rf '$dir'"
        fi
    done

    # Remove sample epics
    for dir in epics/EPIC-SAMPLE epics/EPIC-SF; do
        if [ -d "$dir" ]; then
            log "  Removing $dir/"
            run "rm -rf '$dir'"
        fi
    done

    # Remove archive (evaluation history, old templates)
    if [ -d "archive" ]; then
        log "  Removing archive/"
        run "rm -rf archive/"
    fi

    # Remove template-repo-specific files
    for f in roadmap.md amendment-fullcycle-prompt.md stride-process-metrics-prompt.md; do
        if [ -f "$f" ]; then
            log "  Removing $f"
            run "rm -f '$f'"
        fi
    done

    # Clean specs/ to only have .gitkeep
    if [ -d "specs" ]; then
        run "touch specs/.gitkeep"
    fi

    # Clean epics/
    if [ -d "epics" ]; then
        run "touch epics/.gitkeep"
    fi

    log "  ${GREEN}Done${NC}"
    STEPS_COMPLETED+=("remove_samples")
fi
log ""

# ─── Step 2: Update project identity ─────────────────────
log "${BOLD}Step 2/7: Update project identity${NC}"

# Determine sed -i syntax
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED_INPLACE="sed -i ''"
else
    SED_INPLACE="sed -i"
fi

# Update CLAUDE.md — replace title
if [ -f "CLAUDE.md" ]; then
    log "  Updating CLAUDE.md"
    run "$SED_INPLACE 's/Tecnos Enterprise Edition v4.4/${PROJECT_TITLE} (SDD v4.4)/g' CLAUDE.md"
fi

# Update label_feature_map.json
LABEL_MAP="sdd-templates/config/label_feature_map.json"
if [ -f "$LABEL_MAP" ]; then
    log "  Initializing label_feature_map.json"
    if [ "$DRY_RUN" = true ]; then
        log "  ${CYAN}[dry-run] Would write empty map with project comment${NC}"
    else
        cat > "$LABEL_MAP" << MAPEOF
{
  "_comment": "GitHub Issue ラベル → specs/ ディレクトリ名のマッピング。featuresを追加するたびに更新してください。",
  "_project": "${PROJECT_NAME}",
  "_epic_prefix": "${EPIC_PREFIX}"
}
MAPEOF
    fi
fi

# Update README.md header
if [ -f "README.md" ]; then
    log "  Updating README.md project name"
    run "$SED_INPLACE 's/# Tecnos-STRIDE: ERP-Ready SDD Methodology/# ${PROJECT_TITLE} — SDD Project/g' README.md"
fi

# SYMPHONY.md (optional orchestration config)
SYMPHONY_TEMPLATE="sdd-templates/templates/SYMPHONY_template.md"
if [ -f "$SYMPHONY_TEMPLATE" ] && [ ! -f "SYMPHONY.md" ]; then
    log "  Creating SYMPHONY.md"
    run "cp '$SYMPHONY_TEMPLATE' SYMPHONY.md"
fi
# Always replace tracker.repo — covers both freshly copied and GitHub-Template-inherited files
if [ -f "SYMPHONY.md" ]; then
    # Determine target repo: --org flag > git remote > placeholder
    _REPO_ORG="${ORG_NAME}"
    if [ -z "$_REPO_ORG" ] && command -v git >/dev/null 2>&1; then
        _REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
        if [ -n "$_REMOTE_URL" ]; then
            # Extract owner/repo from HTTPS or SSH URL
            _REPO_ORG="$(echo "$_REMOTE_URL" | sed -E 's#.*[:/]([^/]+)/[^/]+(\.git)?$#\1#')"
        fi
    fi
    if [ -n "$_REPO_ORG" ] && [ -n "$PROJECT_NAME" ]; then
        TARGET_REPO="${_REPO_ORG}/${PROJECT_NAME}"
        run "$SED_INPLACE 's|{{GITHUB_REPO}}|${TARGET_REPO}|g' SYMPHONY.md"
        run "$SED_INPLACE 's|repo: \"tecnos-japan-cbp/tecnos-sdd-template-enterprise\"|repo: \"${TARGET_REPO}\"|g' SYMPHONY.md"
        log "  SYMPHONY.md tracker.repo → ${TARGET_REPO}"
    else
        # No org detectable — reset to placeholder so validate catches it
        run "$SED_INPLACE 's|repo: \"tecnos-japan-cbp/tecnos-sdd-template-enterprise\"|repo: \"{{GITHUB_REPO}}\"|g' SYMPHONY.md"
        log "  ${YELLOW}SYMPHONY.md tracker.repo → placeholder (set manually or re-run with --org)${NC}"
    fi
fi

log "  ${GREEN}Done${NC}"
STEPS_COMPLETED+=("replace_placeholders")
log ""

# ─── Step 3: Configure monorepo scale ────────────────────
log "${BOLD}Step 3/7: Configure monorepo (scale: ${SCALE})${NC}"

MONOREPO_DIR="sdd-templates/config/monorepo"

# turbo.json
if [ ! -f "turbo.json" ] && [ -f "$MONOREPO_DIR/turbo.${SCALE}.json" ]; then
    log "  Creating turbo.json (${SCALE})"
    run "cp '$MONOREPO_DIR/turbo.${SCALE}.json' turbo.json"
else
    log "  ${YELLOW}Skipped: turbo.json (already exists or template missing)${NC}"
fi

# tsconfig.base.json
if [ ! -f "tsconfig.base.json" ] && [ -f "$MONOREPO_DIR/tsconfig.base.json" ]; then
    log "  Creating tsconfig.base.json"
    run "cp '$MONOREPO_DIR/tsconfig.base.json' tsconfig.base.json"
fi

# vitest.workspace.ts (standard/enterprise)
if [ "$SCALE" != "starter" ]; then
    if [ ! -f "vitest.workspace.ts" ] && [ -f "$MONOREPO_DIR/vitest.workspace.ts" ]; then
        log "  Creating vitest.workspace.ts"
        run "cp '$MONOREPO_DIR/vitest.workspace.ts' vitest.workspace.ts"
    fi
fi

# CI workflow
CI_SRC="$MONOREPO_DIR/github-actions/ci-${SCALE}.yml"
CI_DEST=".github/workflows/ci.yml"
if [ ! -f "$CI_DEST" ] && [ -f "$CI_SRC" ]; then
    run "mkdir -p .github/workflows"
    log "  Creating CI workflow (${SCALE})"
    run "cp '$CI_SRC' '$CI_DEST'"
fi

log "  ${GREEN}Done${NC}"
STEPS_COMPLETED+=("configure_monorepo")
log ""

# ─── Step 4: Set up Phase Gate hooks ─────────────────────
log "${BOLD}Step 4/7: Configure Phase Gate hooks${NC}"
# v5.3.2: always install via `stride hooks --tool claude --force` to avoid
# inheriting unrelated hooks from a cloned template. Previous behaviour skipped
# when .claude/settings.json already existed, which meant any personal hooks
# baked into the template (e.g. upstream maintainer's session hooks) would
# leak into new projects without Phase Gate protection.
TEMPLATE_DIR_EARLY="$(dirname "$(dirname "$0")")/sdd-templates"
[ ! -d "$TEMPLATE_DIR_EARLY" ] && TEMPLATE_DIR_EARLY="$(pwd)/sdd-templates"
STRIDE_CLI_EARLY="$TEMPLATE_DIR_EARLY/bin/stride"
if [ "$DRY_RUN" = true ]; then
    log "  ${CYAN}[dry-run] Would run: stride hooks --tool claude --force${NC}"
    STEPS_SKIPPED+=("phase_gate_hooks")
elif [ -x "$STRIDE_CLI_EARLY" ]; then
    if "$STRIDE_CLI_EARLY" hooks --tool claude --force >/dev/null 2>&1; then
        log "  ${GREEN}Phase Gate hooks configured (.claude/settings.json)${NC}"
        STEPS_COMPLETED+=("phase_gate_hooks")
    else
        log "  ${YELLOW}stride hooks failed — configure manually: stride hooks --tool claude --force${NC}"
        STEPS_SKIPPED+=("phase_gate_hooks")
    fi
else
    log "  ${YELLOW}stride CLI not found — skipping Phase Gate hooks${NC}"
    STEPS_SKIPPED+=("phase_gate_hooks")
fi

log ""

# ─── Step 5: Create first feature (optional) ─────────────
log "${BOLD}Step 5/7: Create initial feature${NC}"

if [ -n "$FIRST_FEATURE" ]; then
    STRIDE_BIN="sdd-templates/bin/stride"
    if [ -x "$STRIDE_BIN" ] || [ -f "$STRIDE_BIN" ]; then
        log "  Running: stride init ${FIRST_FEATURE} --scale ${SCALE}"
        if [ "$DRY_RUN" = true ]; then
            log "  ${CYAN}[dry-run] Would run stride init${NC}"
        else
            bash "$STRIDE_BIN" init "$FIRST_FEATURE" --scale "$SCALE" 2>&1 | sed 's/^/  /'
        fi

        # Update label_feature_map.json with the new feature
        if [ "$DRY_RUN" != true ] && [ -f "$LABEL_MAP" ]; then
            FEATURE_ID=$(echo "$FIRST_FEATURE" | tr '[:lower:]' '[:upper:]' | tr -d '[:punct:]' | tr -d '_')
            python3 -c "
import json
with open('$LABEL_MAP') as f:
    data = json.load(f)
data['FEAT-$FEATURE_ID'] = '$FIRST_FEATURE'
with open('$LABEL_MAP', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write('\n')
" 2>/dev/null && log "  ${GREEN}Updated label_feature_map.json${NC}" || true
        fi
        STEPS_COMPLETED+=("create_feature")
    else
        log "  ${YELLOW}Warning: stride CLI not found, skipping feature creation${NC}"
        STEPS_SKIPPED+=("create_feature")
    fi
else
    log "  ${YELLOW}Skipped (no --first-feature specified)${NC}"
    log "  Run later: ${CYAN}sdd-templates/bin/stride intake <feature_name>${NC}"
    STEPS_SKIPPED+=("create_feature")
fi

log ""

# ─── Step 6: Git initialization ──────────────────────────
log "${BOLD}Step 6/7: External tracker bindings (optional)${NC}"
# v5.3.1: Each new STRIDE project gets its own GitHub Project V2 and Linear
# Project for per-project issue isolation. Credentials not available →
# graceful skip (no error). User can manually run `stride project create` /
# `stride linear project create` later.

TEMPLATE_DIR_LOCAL="$(dirname "$(dirname "$0")")/sdd-templates"
if [ ! -d "$TEMPLATE_DIR_LOCAL" ]; then
    TEMPLATE_DIR_LOCAL="$(pwd)/sdd-templates"
fi
STRIDE_CLI="$TEMPLATE_DIR_LOCAL/bin/stride"

# --- GitHub Project V2 auto-create ---
# v5.3.2: fixed two bugs:
#   (1) `if cmd | sed ...; then` evaluated sed's exit code (always 0) — success
#       was reported even when `stride project create` failed.
#   (2) Without --org, `gh project create` requires --owner interactively; in
#       non-interactive pipelines it fails. We now skip early with a hint.
if [ "$NO_GITHUB_PROJECT" = true ]; then
    log "  ${YELLOW}Skipping GitHub Project (--no-github-project)${NC}"
    STEPS_SKIPPED+=("github_project")
elif [ "$GITHUB_PROJECT_TITLE" = "-" ]; then
    log "  ${YELLOW}Skipping GitHub Project (--github-project -)${NC}"
    STEPS_SKIPPED+=("github_project")
elif [ -z "$ORG_NAME" ] && [ -z "${GITHUB_OWNER:-}" ]; then
    log "  ${YELLOW}Skipping GitHub Project: --org / GITHUB_OWNER 未指定（gh project create は owner 必須）${NC}"
    log "  ${CYAN}後で実行: stride project create \"${PROJECT_TITLE} SDD Board\" --owner <owner>${NC}"
    STEPS_SKIPPED+=("github_project")
else
    # Derive title if not provided; owner from --org or $GITHUB_OWNER
    GH_TITLE="${GITHUB_PROJECT_TITLE:-${PROJECT_TITLE} SDD Board}"
    GH_OWNER="${ORG_NAME:-${GITHUB_OWNER:-}}"
    if [ "$DRY_RUN" = true ]; then
        log "  ${CYAN}[dry-run] Would run: stride project create \"${GH_TITLE}\" --owner ${GH_OWNER}${NC}"
        STEPS_SKIPPED+=("github_project")
    elif [ -x "$STRIDE_CLI" ]; then
        if gh auth status >/dev/null 2>&1; then
            # Capture exit code explicitly (pipe-to-sed hid the real exit code)
            GH_STRIDE_OUT=$("$STRIDE_CLI" project create "$GH_TITLE" --owner "$GH_OWNER" 2>&1)
            GH_STRIDE_EXIT=$?
            echo "$GH_STRIDE_OUT" | sed 's/^/    /'
            if [ $GH_STRIDE_EXIT -eq 0 ]; then
                log "  ${GREEN}GitHub Project bound → memory/github_project.yaml${NC}"
                STEPS_COMPLETED+=("github_project")
            else
                log "  ${YELLOW}GitHub Project creation failed (exit=${GH_STRIDE_EXIT}, non-fatal)${NC}"
                STEPS_SKIPPED+=("github_project")
            fi
        else
            log "  ${YELLOW}gh not authenticated — skipping GitHub Project (run 'gh auth login' + 'stride project create' later)${NC}"
            STEPS_SKIPPED+=("github_project")
        fi
    else
        log "  ${YELLOW}stride CLI not found — skipping GitHub Project${NC}"
        STEPS_SKIPPED+=("github_project")
    fi
fi

# --- Linear Project auto-create ---
if [ "$NO_LINEAR_PROJECT" = true ]; then
    log "  ${YELLOW}Skipping Linear Project (--no-linear-project)${NC}"
    STEPS_SKIPPED+=("linear_project")
elif [ "$LINEAR_PROJECT_NAME" = "-" ]; then
    log "  ${YELLOW}Skipping Linear Project (--linear-project -)${NC}"
    STEPS_SKIPPED+=("linear_project")
else
    LN_NAME="${LINEAR_PROJECT_NAME:-${PROJECT_NAME}}"
    if [ "$DRY_RUN" = true ]; then
        log "  ${CYAN}[dry-run] Would run: stride linear project create \"${LN_NAME}\"${NC}"
        STEPS_SKIPPED+=("linear_project")
    elif [ -x "$STRIDE_CLI" ]; then
        if [ -n "${LINEAR_API_KEY:-}" ]; then
            # v5.3.2: capture exit code explicitly (pipe-to-sed hid real result)
            LN_STRIDE_OUT=$("$STRIDE_CLI" linear project create "$LN_NAME" 2>&1)
            LN_STRIDE_EXIT=$?
            echo "$LN_STRIDE_OUT" | sed 's/^/    /'
            if [ $LN_STRIDE_EXIT -eq 0 ]; then
                log "  ${GREEN}Linear Project bound → memory/linear.yaml${NC}"
                STEPS_COMPLETED+=("linear_project")
            else
                log "  ${YELLOW}Linear Project creation failed (exit=${LN_STRIDE_EXIT}, non-fatal)${NC}"
                STEPS_SKIPPED+=("linear_project")
            fi
        else
            log "  ${YELLOW}LINEAR_API_KEY unset — skipping Linear Project (set in .env.local + 'stride linear project create' later)${NC}"
            STEPS_SKIPPED+=("linear_project")
        fi
    else
        log "  ${YELLOW}stride CLI not found — skipping Linear Project${NC}"
        STEPS_SKIPPED+=("linear_project")
    fi
fi

log ""

# ─── Step 7: Git initialization ──────────────────────────
log "${BOLD}Step 7/7: Git setup${NC}"

if [ "$SKIP_GIT" = true ]; then
    log "  ${YELLOW}Skipped (--skip-git)${NC}"
    STEPS_SKIPPED+=("git_init")
elif [ "$DRY_RUN" = true ]; then
    log "  ${CYAN}[dry-run] Would create initial commit${NC}"
    STEPS_COMPLETED+=("git_init")
else
    if [ -d ".git" ]; then
        # Already a git repo (from template clone)
        git add -A 2>/dev/null || true
        CHANGES=$(git diff --cached --stat 2>/dev/null || echo "")
        if [ -n "$CHANGES" ]; then
            git commit -m "chore: initialize ${PROJECT_NAME} from SDD Template Enterprise

- Removed sample specs/epics/archive
- Configured project identity: ${PROJECT_NAME}
- Set monorepo scale: ${SCALE}
- Configured Phase Gate hooks
$([ -n "$FIRST_FEATURE" ] && echo "- Created initial feature: ${FIRST_FEATURE}")" 2>/dev/null
            log "  ${GREEN}Created initial commit${NC}"
        else
            log "  ${YELLOW}No changes to commit${NC}"
        fi
        STEPS_COMPLETED+=("git_init")
    else
        log "  ${YELLOW}Not a git repository. Run 'git init' first.${NC}"
        STEPS_SKIPPED+=("git_init")
    fi
fi

log ""

# ─── Summary ──────────────────────────────────────────────
log "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
log "${BOLD}║  ✅ Project initialization complete!                 ║${NC}"
log "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
log ""
log "  ${BOLD}Next steps:${NC}"
log ""
if [ -z "$FIRST_FEATURE" ]; then
    log "  1. Create your first feature:"
    log "     ${CYAN}sdd-templates/bin/stride intake <feature_name>${NC}"
    log ""
    log "  2. Fill in basic_design_intake.md (10-15 min)"
    log ""
    log "  3. Ask AI to generate full basic_design.md from intake"
    log ""
else
    log "  1. Edit specs/${FIRST_FEATURE}/basic_design.md"
    log ""
    log "  2. Run lint: ${CYAN}sdd-templates/bin/stride lint specs/${FIRST_FEATURE}/${NC}"
    log ""
    log "  3. Approve Gate 1 in specs/${FIRST_FEATURE}/APPROVAL.md"
    log ""
fi
log "  📚 Documentation:  ${CYAN}manual/ (docsify)${NC}"
log "  📖 Quick Start:    ${CYAN}sdd-templates/QUICKSTART.md${NC}"
log "  🔧 CLI Reference:  ${CYAN}sdd-templates/bin/stride help${NC}"
log ""

# ─── JSON output (if --json) ────────────────────────────
if [ "$JSON_OUTPUT" = true ]; then
    json_output true 0
fi
