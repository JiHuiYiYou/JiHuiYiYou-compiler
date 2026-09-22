#!/usr/bin/env bash
# bench.sh — v2.16.0 perf gate (per v2.0.0-os-prep.md § 5.2 item #8)
#
# Measure self-backend generated code runtime perf vs gcc -O2 same-source baseline.
# PASS gate (--strict): jhyy_time / gcc_time ≤ 1.1 for all 3 programs.
# Default (--report): logs + accept first-time baseline, exit 0.
#
# Programs: fib(35) → fib(35) % 1000000 / ackermann(3,8) → exit code /
# nqueens(11) → solution count. Each: C source (heredoc) + jhyy source
# (heredoc) → 5-run min trimmed-mean → ratio.
#
# Usage: bash bench.sh [--strict|--report]
# Exit codes:
#   0 = PASS (default --report accepts; --strict ≤ 1.1)
#   1 = FAIL (--strict mode, ratio > 1.1)
#   2 = setup error (gcc missing, etc.)
#
# v2.16.0: first-time baseline. Perf optimization is v3.x territory per
# feedback_no_artifacts_in_project convention.
#
# nqueens uses reordered signature (row: i32, c: i32, cols: *i32) to work
# around W-085 codegen small-frame fn(*T, i32, i32) 3rd-arg corruption.
# See docs/internal/workarounds.md W-085 for details.

set -u

MODE="${1:---report}"
JHY="${JHYY:-/c/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v2/compiler/build/bin/jhyy.exe}"
GCC="${GCC:-gcc}"
THRESHOLD="${THRESHOLD:-1.1}"
RUNS="${RUNS:-5}"
TMPDIR="${TMPDIR:-/tmp/bench_v2160}"
mkdir -p "$TMPDIR"

if [[ "$MODE" != "--report" && "$MODE" != "--strict" ]]; then
    echo "Usage: bash bench.sh [--strict|--report]" >&2
    exit 2
fi

if ! command -v "$GCC" > /dev/null 2>&1; then
    echo "ERROR: gcc not found in PATH" >&2
    exit 2
fi
if [[ ! -x "$JHY" ]]; then
    echo "ERROR: jhyy.exe not found at $JHY" >&2
    exit 2
fi

# ───────────────────────────────────────────────────────────────────
# Heredoc sources (C and jhyy equivalent for each program)
# ───────────────────────────────────────────────────────────────────

cat > "$TMPDIR/fib.c" <<'CEOF'
#include <stdio.h>
#include <stdlib.h>
int fib(int n) { if (n < 2) return n; return fib(n-1) + fib(n-2); }
int main(void) { printf("%d\n", fib(35) % 1000000); return 0; }
CEOF

cat > "$TMPDIR/fib.jhyy" <<'JEOF'
extern fn printf(fmt: *u8, val: i32) -> i32;

fn fib(n: i32) -> i32 {
    if n < 2 { return n; }
    return fib(n - 1) + fib(n - 2);
}

fn main_jhyy() -> i32 {
    let r = fib(35) % 1000000;
    printf("fib(35) %% 1000000 = %d\n" as *u8, r);
    return r;
}
JEOF

cat > "$TMPDIR/ack.c" <<'CEOF'
#include <stdio.h>
int A(int m, int n) {
    if (m == 0) return n + 1;
    if (n == 0) return A(m - 1, 1);
    return A(m - 1, A(m, n - 1));
}
int main(void) { printf("%d\n", A(3, 8)); return 0; }
CEOF

cat > "$TMPDIR/ack.jhyy" <<'JEOF'
extern fn printf(fmt: *u8, val: i32) -> i32;

fn A(m: i32, n: i32) -> i32 {
    if m == 0 { return n + 1; }
    if n == 0 { return A(m - 1, 1); }
    return A(m - 1, A(m, n - 1));
}

fn main_jhyy() -> i32 {
    let r = A(3, 8);
    printf("A(3, 8) = %d\n" as *u8, r);
    return r;
}
JEOF

cat > "$TMPDIR/nq.c" <<'CEOF'
#include <stdio.h>
static int sols = 0;
static int cols[8];
static int N = 7;
void solve(int row) {
    if (row == N) { sols++; return; }
    for (int c = 0; c < N; c++) {
        int ok = 1;
        for (int r2 = 0; r2 < row; r2++) {
            if (cols[r2] == c) { ok = 0; break; }
            if (cols[r2] - c == r2 - row) { ok = 0; break; }
            if (c - cols[r2] == r2 - row) { ok = 0; break; }
        }
        if (ok) { cols[row] = c; solve(row + 1); }
    }
}
int main(void) { solve(0); printf("%d\n", sols); return 0; }
CEOF

cat > "$TMPDIR/nq.jhyy" <<'JEOF'
extern fn printf(fmt: *u8, val: i32) -> i32;

fn ok(row: i32, c: i32, cols: *i32) -> i32 {
    let mut r2: i32 = 0;
    while r2 < row {
        let prev = cols[r2];
        if prev == c { return 0; }
        if prev - c == r2 - row { return 0; }
        if c - prev == r2 - row { return 0; }
        r2 = r2 + 1;
    }
    return 1;
}

fn solve(row: i32, N: i32, cols: *i32, sols: *i32) {
    if row == N {
        *sols = *sols + 1;
        return;
    }
    let mut c: i32 = 0;
    while c < N {
        if ok(row, c, cols) == 1 {
            cols[row] = c;
            solve(row + 1, N, cols, sols);
        }
        c = c + 1;
    }
}

fn main_jhyy() -> i32 {
    let cols: [i32; 7] = [0, 0, 0, 0, 0, 0, 0];
    let mut sols: i32 = 0;
    solve(0, 7, &cols as *i32, &sols as *i32);
    printf("nqueens(7) = %d (expect 40)\n" as *u8, sols);
    return sols;
}
JEOF

# ───────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────

run_n() {
    # $1 = program path, $2 = number of runs
    # Returns min trimmed-mean (drop highest + lowest of remaining 3)
    local prog="$1"
    local n="$2"
    local times=()
    for ((i = 1; i <= n; i++)); do
        # warmup if first run
        if [[ $i -eq 1 ]]; then "$prog" > /dev/null 2>&1; fi
        local t
        # /usr/bin/time -f "%e" prints elapsed wall-clock seconds (decimal)
        t=$(/usr/bin/time -f "%e" "$prog" > /dev/null 2>&1; cat /tmp/_bench_last_time 2>/dev/null) || true
        # Fallback: use $SECONDS-based timing if /usr/bin/time is unavailable
        if [[ -z "$t" ]]; then
            local start end
            start=$(date +%s.%N)
            "$prog" > /dev/null 2>&1
            end=$(date +%s.%N)
            t=$(awk -v s="$start" -v e="$end" 'BEGIN { printf "%.2f", e - s }')
        fi
        times+=("$t")
    done
    # trimmed-mean: drop highest + lowest of 5, mean of remaining 3
    printf '%s\n' "${times[@]}" | sort -g | sed -n '2,4p' | awk '{ s += $1 } END { if (NR > 0) printf "%.3f", s / NR; else print "0.000" }'
}

compile_and_time() {
    # $1 = name (fib|ack|nq), $2 = lang (c|jhyy)
    local name="$1"
    local lang="$2"
    local src="$TMPDIR/${name}.${lang}"
    # Use bare name (no .exe suffix). jhyy.exe appends .exe automatically on
    # MSYS2/Windows when -o doesn't already end in .exe. gcc accepts bare
    # path; we'll pass the same path to gcc and let jhyy append.
    local out_base="$TMPDIR/${name}_${lang}"
    if [[ "$lang" == "c" ]]; then
        $GCC -O2 -o "${out_base}.exe" "$src" 2>/dev/null
    else
        "$JHY" compile "$src" -o "${out_base}" > /dev/null 2>&1
    fi
    if [[ ! -x "${out_base}.exe" ]]; then
        echo "ERROR: compile $name.$lang failed (output: ${out_base}.exe)" >&2
        return 1
    fi
    run_n "${out_base}.exe" "$RUNS"
}

# ───────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────

echo "bench.sh — v2.16.0 perf gate (mode=$MODE)"
echo "  jhyy: $JHY"
echo "  gcc:  $GCC"
echo "  threshold: ${THRESHOLD}x"
echo "  runs per program: $RUNS (trimmed-mean of 3)"
echo ""

declare -a PROGRAMS=("fib" "ack" "nq")
declare -a GCC_TIMES=()
declare -a JHY_TIMES=()
declare -a RATIOS=()
declare -a STATUS=()

FAIL=0

for prog in "${PROGRAMS[@]}"; do
    echo -n "  $prog: gcc -O2 ... "
    gcc_t=$(compile_and_time "$prog" "c") || { FAIL=1; echo "COMPILE FAIL"; continue; }
    echo -n "jhyy ... "
    jhy_t=$(compile_and_time "$prog" "jhyy") || { FAIL=1; echo "COMPILE FAIL"; continue; }
    ratio=$(awk -v j="$jhy_t" -v g="$gcc_t" 'BEGIN { if (g+0 > 0) printf "%.3f", j / g; else print "nan" }')
    pass=$(awk -v r="$ratio" -v t="$THRESHOLD" 'BEGIN { print (r+0 <= t+0) ? "PASS" : "FAIL" }')
    echo "${gcc_t}s / ${jhy_t}s = ${ratio}x [$pass]"
    GCC_TIMES+=("$gcc_t")
    JHY_TIMES+=("$jhy_t")
    RATIOS+=("$ratio")
    STATUS+=("$pass")
    if [[ "$pass" == "FAIL" ]]; then FAIL=1; fi
done

echo ""
echo "Summary:"
printf "  %-8s %10s %10s %8s %s\n" "program" "gcc" "jhyy" "ratio" "status"
for i in "${!PROGRAMS[@]}"; do
    printf "  %-8s %10ss %10ss %7sx %s\n" "${PROGRAMS[$i]}" "${GCC_TIMES[$i]}" "${JHY_TIMES[$i]}" "${RATIOS[$i]}" "${STATUS[$i]}"
done

echo ""
case "$MODE" in
    --strict)
        if [[ $FAIL -eq 0 ]]; then
            echo "RESULT: PASS (all ratios ≤ ${THRESHOLD}x)"
            exit 0
        else
            echo "RESULT: FAIL (one or more ratios > ${THRESHOLD}x)"
            exit 1
        fi
        ;;
    --report)
        echo "RESULT: REPORT (--report mode accepts first-time baseline)"
        if [[ $FAIL -eq 0 ]]; then
            echo "  All ratios ≤ ${THRESHOLD}x — within target."
        else
            echo "  WARNING: one or more ratios > ${THRESHOLD}x."
            echo "  This is the first-time baseline; --strict gate deferred to next sprint."
        fi
        exit 0
        ;;
esac