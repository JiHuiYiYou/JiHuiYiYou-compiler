#!/usr/bin/env bash
# self_host_bench.sh — Measure JHYY self-hosting compile time
# Mirrors TPV's "self-hosting 2 min" and "+ llc + link 2:50" framing.
#
# Usage: bash tmp/self_host_bench.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

JHYV_BIN="./compiler/build/bin/jhyy.exe"          # current jhyy-side production
JHYV_V1="./compiler/build/bin/jhyy_v1.exe.exe"    # v1.0.0 historical baseline
MAIN="compiler/src0/main.jhyy"

OUT_IL="compiler/src0/main.il"     # jhyy build output: always next to source (-o ignored)
OUT_S="/tmp/jhyy-bench/main.s"

mkdir -p /tmp/jhyy-bench

# run3 <label> <cmd...> — 3 runs, take min, also print all 3 raw values
run3() {
    local label="$1"; shift
    local -a times
    # warmup
    bash -c "$*" >/dev/null 2>&1 || true
    for i in 1 2 3; do
        local t
        t=$( { /usr/bin/time -f "%e" bash -c "$* >/dev/null 2>/dev/null" ; } 2>&1 | tr -d '\n' )
        times+=("$t")
    done
    # min
    local mn
    mn=$(printf '%s\n' "${times[@]}" | sort -g | head -1)
    printf "%-50s | runs=%s,%s,%s  min=%s\n" "$label" "${times[0]}" "${times[1]}" "${times[2]}" "$mn"
}

echo "===== A. jhyy build (compile-to-IL only) ====="
run3 "A1 jhyy.exe       build src0/main.jhyy"   "$JHYV_BIN build $MAIN"
run3 "A2 jhyy_v1.exe    build src0/main.jhyy"   "$JHYV_V1 build $MAIN"

echo
echo "===== B. jhyy compile (full pipeline, includes QBE+link) ====="
run3 "B1 jhyy.exe       compile src0/main.jhyy"  "$JHYV_BIN compile $MAIN"
run3 "B2 jhyy_v1.exe    compile src0/main.jhyy"  "$JHYV_V1 compile $MAIN"

echo
echo "===== C. QBE step alone (on existing main.il) ====="
# Need main.il to exist first; jhyy build it once if missing
if [ ! -f "$OUT_IL" ]; then
    echo "(pre-building main.il for C step)"
    bash -c "$JHYV_BIN build $MAIN" >/dev/null 2>&1
fi
run3 "C1 qbe -t amd64_win main.il > main.s"      "./qbe/qbe.exe -t amd64_win $OUT_IL > $OUT_S"

echo
echo "===== File sizes ====="
ls -la "$OUT_IL" "$OUT_S" 2>/dev/null | awk '{print $5, $9}'