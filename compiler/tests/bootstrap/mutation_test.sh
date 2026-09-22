#!/usr/bin/env bash
# mutation_test.sh — driver for mutation_test.py
#
# 用法: mutation_test.sh [--baseline-only]
#
# 调用 mutation_test.py 跑 mutation testing protocol, 期望 catch ≥ 80% (24/30)
# per docs/plans/v2/v2.14.0-plan.md Phase 2.
#
# 环境变量:
#   JHY_MUT_LIMIT    = 限制 mutation 数量 (0 = all, default 0)
#   JHY_MUT_CATEGORY = 限制 category (abi / codegen / parser / typechecker, default "")
#
# 退出码:
#   0  = catch rate ≥ 80%
#   1  = catch rate < 80% OR setup 错

set -uo pipefail

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MUTATION_TEST="$JHYY_ROOT/compiler/tests/bootstrap/mutation_test.py"
MUTATIONS_JSON="$JHYY_ROOT/compiler/tests/bootstrap/mutations.json"
OUTPUT_REPORT="$JHYY_ROOT/compiler/tests/bootstrap/mutation-test-report.md"

EXTRA_ARGS=()
if [[ -n "${JHY_MUT_LIMIT:-}" && "${JHY_MUT_LIMIT:-0}" -gt 0 ]]; then
    EXTRA_ARGS+=("--limit" "${JHY_MUT_LIMIT}")
fi
if [[ -n "${JHY_MUT_CATEGORY:-}" ]]; then
    EXTRA_ARGS+=("--category" "${JHY_MUT_CATEGORY}")
fi

echo "=== mutation_test.sh — v2.14.0 mutation testing protocol ==="
echo "  JHYY_ROOT = $JHYY_ROOT"
echo "  MUTATIONS = $MUTATIONS_JSON"
echo "  REPORT    = $OUTPUT_REPORT"
echo "  EXTRA     = ${EXTRA_ARGS[*]:-}"
echo

# Verify setup
if [[ ! -f "$MUTATION_TEST" ]]; then
    echo "ERROR: mutation_test.py not found at $MUTATION_TEST" >&2
    exit 1
fi
if [[ ! -f "$MUTATIONS_JSON" ]]; then
    echo "ERROR: mutations.json not found at $MUTATIONS_JSON" >&2
    exit 1
fi

# Clean stale artifacts
rm -f "$JHYY_ROOT"/compiler/src0/*.jhyy.bak 2>/dev/null
rm -f "$JHYY_ROOT"/_mutation_test_compile_main* 2>/dev/null

# Run
python "$MUTATION_TEST" \
    --mutations "$MUTATIONS_JSON" \
    --output "$OUTPUT_REPORT" \
    "${EXTRA_ARGS[@]}"

EXIT=$?

# Ironclad cleanup: restore ALL .bak files (in case Python crashed mid-run)
# This is a CRITICAL safety net per feedback_unrelated_uncommitted_revert —
# mutation_test.py must NEVER leave src0/ files in mutated state.
for bak in "$JHYY_ROOT"/compiler/src0/*.jhyy.bak; do
    if [[ -f "$bak" ]]; then
        orig="${bak%.bak}"
        if [[ -f "$orig" ]]; then
            cp "$bak" "$orig"
        fi
        rm -f "$bak"
        echo "[mutation_test.sh] restored ${orig##*/} from .bak"
    fi
done

# Final cleanup
rm -f "$JHYY_ROOT"/_mutation_test_compile_main* 2>/dev/null

echo
echo "=== mutation_test.sh 结果: EXIT=$EXIT ==="
echo "  Report: $OUTPUT_REPORT"
exit $EXIT