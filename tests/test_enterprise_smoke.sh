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

# --- Snapshot files that may be overwritten by stride init ---
SNAPSHOT_DIR=$(mktemp -d)
COLLATERAL_FILES=(
    turbo.json
    tsconfig.base.json
    vitest.workspace.ts
    .github/workflows/ci.yml
    shared/contracts/CONTRACT_REGISTRY.yaml
)
ENTERPRISE_CONFIG="sdd-templates/config/enterprise.yaml"

# Save enterprise.yaml original content
cp "$ENTERPRISE_CONFIG" "$SNAPSHOT_DIR/enterprise.yaml.orig"

# Snapshot any pre-existing collateral files and directories
for f in "${COLLATERAL_FILES[@]}"; do
    if [ -f "$f" ]; then
        mkdir -p "$SNAPSHOT_DIR/$(dirname "$f")"
        cp "$f" "$SNAPSHOT_DIR/$f"
    fi
done
COLLATERAL_DIRS=(shared/contracts/events shared/contracts/api shared/contracts)
for d in "${COLLATERAL_DIRS[@]}"; do
    if [ -d "$d" ]; then
        mkdir -p "$SNAPSHOT_DIR/$d"
    fi
done

# --- Cleanup function (runs on EXIT, including failures) ---
cleanup() {
    # Remove test artifacts
    rm -rf epics/EPIC-SMOKE/ specs/smoke_feature/

    # Restore or remove collateral files
    for f in "${COLLATERAL_FILES[@]}"; do
        if [ -f "$SNAPSHOT_DIR/$f" ]; then
            # File existed before — restore it
            cp "$SNAPSHOT_DIR/$f" "$f"
        else
            # File did not exist before — remove if created
            rm -f "$f"
        fi
    done

    # Remove empty directories only if they were not pre-existing
    for d in shared/contracts/events shared/contracts/api shared/contracts; do
        if [ -d "$d" ] && [ ! -d "$SNAPSHOT_DIR/$d" ]; then
            rmdir "$d" 2>/dev/null || true
        fi
    done

    # Restore enterprise.yaml to its original content
    cp "$SNAPSHOT_DIR/enterprise.yaml.orig" "$ENTERPRISE_CONFIG"

    rm -rf "$SNAPSHOT_DIR"
}
trap cleanup EXIT

echo "=== Enterprise Smoke Tests ==="

# Test 1: Default Off
echo ""
echo "--- Test 1: Enterprise Off (default) ---"
echo -e "enterprise:\n  enabled: false" > "$ENTERPRISE_CONFIG"
assert "! sdd-templates/bin/stride epic list 2>&1 | grep -q 'Epics:'" "epic list blocked when disabled"
assert "sdd-templates/tools/stride-lint sdd-templates/specs/sample_feature/ --warn-only" "sample_feature lint passes with enterprise off"

# Test 2: Enable Enterprise
echo ""
echo "--- Test 2: Enterprise On ---"
echo -e "enterprise:\n  enabled: true" > "$ENTERPRISE_CONFIG"
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

# Test 4: Epic Validate (should work even with template epic)
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

# Test 5c: With valid --team → should succeed
assert "echo 'y' | sdd-templates/bin/stride init smoke_feature --epic EPIC-SMOKE --team TEAM-A > /dev/null 2>&1" "init with --epic --team should succeed"
assert "test -f specs/smoke_feature/basic_design.md" "basic_design.md created with --team"
assert "grep -q 'epic_ref: \"EPIC-SMOKE\"' specs/smoke_feature/basic_design.md" "epic_ref auto-set"
assert "grep -q 'team_id: \"TEAM-A\"' specs/smoke_feature/basic_design.md" "team_id auto-set"

# Test 6: stride lint --enterprise (single feature, should NOT validate epics)
echo ""
echo "--- Test 6: stride lint --enterprise (single feature) ---"
assert "! sdd-templates/tools/stride-lint specs/smoke_feature/ --enterprise --warn-only 2>&1 | grep -q '\[Epic\]'" "single feature lint does not include [Epic] validation results"

# Test 7: Argument passing (EPIC_ID reaches subcommands)
echo ""
echo "--- Test 7: Argument passing ---"
assert "sdd-templates/bin/stride epic gates EPIC-SMOKE 2>&1 | grep -q 'Gate Status'" "epic gates receives EPIC_ID"
assert "sdd-templates/bin/stride epic features EPIC-SMOKE 2>&1 | grep -q 'EPIC-SMOKE'" "epic features receives EPIC_ID"

# cleanup is handled by the EXIT trap

echo ""
echo "=== Results: $PASS passed, $FAIL failed (of $TOTAL) ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
