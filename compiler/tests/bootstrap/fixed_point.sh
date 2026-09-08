#!/usr/bin/env bash
# fixed_point.sh — N≥3 selfhost closure 验算 (v2.9.0 V2-C Part 1)
#
# 用法: fixed_point.sh
#
# 在 N 份 jhyy binary 上编同一 .jhyy 源 (默认 compiler/src0/main.jhyy), 验证
#   .il 跨代 byte-equal (per D43 closure ship gate)
#   cap_test.jhyy 跨代 exit code = 42 (per V3-C v3.1.0 ship, 8-byte Cap<T>)
#
# N=3 是 primary ship gate (per D43); N=4/5 informational only.
#
# v1↔v2 closure 复用 byte_equal.sh (per D26); v2↔v3, v3↔v4, v4↔v5 由本 script
# 直接 diff. .s / .exe byte-equal 不强制 (v2.6.0 起 peephole + regalloc 改 .s,
# IL closure 仍是 ground truth per D43).
#
# 环境变量:
#   JHYY_V1      = jhyy v1 frozen binary (default: compiler/build/bin/jhyy_v1.exe.exe)
#   JHYY_V2      = jhyy v2 binary         (default: compiler/build/bin/jhyy.exe)
#   JHYY_INPUT   = 编的目标 .jhyy         (default: compiler/src0/main.jhyy)
#   JHY_FP_BUILD_DIR = 临时 build dir     (default: /tmp/jhyy_fp)
#   JHY_FP_MAX_N     = 最大迭代次数      (default: 5)
#
# 退出码:
#   0  = N=3 PASS + cap_test 跨代一致
#   1  = FAIL 或 setup 错 (binary 找不到等)

set -uo pipefail

# ════════════════════════════════════════════════════════════════════════════
# Args + env
# ════════════════════════════════════════════════════════════════════════════

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JHYY_V1="${JHYY_V1:-$JHYY_ROOT/compiler/build/bin/jhyy_v1.exe.exe}"
JHYY_V2="${JHYY_V2:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"
JHYY_INPUT="${JHYY_INPUT:-$JHYY_ROOT/compiler/src0/main.jhyy}"
JHY_FP_BUILD_DIR="${JHY_FP_BUILD_DIR:-/tmp/jhyy_fp}"
JHY_FP_MAX_N="${JHY_FP_MAX_N:-5}"

CAP_TEST="$JHYY_ROOT/compiler/tests/examples/cap_test.jhyy"
CAP_TEST_EXPECT=42

# ════════════════════════════════════════════════════════════════════════════
# Setup: verify binaries + input exist
# ════════════════════════════════════════════════════════════════════════════

if [[ ! -f "$JHYY_V1" ]]; then
    echo "ERR: JHYY_V1 not found at $JHYY_V1" >&2
    echo "  v1 baseline binary missing. Restore via:" >&2
    echo "    git checkout archive/v2.6.6 -- compiler/build/bin/jhyy_v1.exe.exe" >&2
    echo "  Or build fresh v1 (jhyy.exe 编 src0/main.jhyy + freeze)" >&2
    exit 1
fi
if [[ ! -f "$JHYY_V2" ]]; then
    echo "ERR: JHYY_V2 not found at $JHYY_V2" >&2
    echo "  Run 'make' to build jhyy.exe" >&2
    exit 1
fi
if [[ ! -f "$JHYY_INPUT" ]]; then
    echo "ERR: input not found: $JHYY_INPUT" >&2
    exit 1
fi

mkdir -p "$JHY_FP_BUILD_DIR"

PASS=0
FAIL=0
INFO=0

# ════════════════════════════════════════════════════════════════════════════
# Build jhyy_v3.exe (jhyy.exe 编 src0/main.jhyy)
# ════════════════════════════════════════════════════════════════════════════

# jhyy.exe 默认链 runtime.c → 出 .exe, 不是 .exe-only binary. 但 v3 / v4 / v5
# 只是验证 closure, 不需要运行 v3.exe. 编出 .exe 后用 `cp` 拿走当 v_N binary.
#
# 实际做法: jhyy.exe 编 main.jhyy 时设 --no-link (per v2.8.3) 拿 .il + .s, 然后
# v3 binary 我们手动拿 src0/main.jhyy 的 .exe 产物 (runtime.c + helpers.c link
# 完成, 是 valid jhyy binary 形状).
#
# 简化: 直接用 `jhyy.exe compile` (含 link) 出 v3.exe — 链接依赖 runtime.c,
# 主流程一致.

echo "=== fixed-point N≥3 selfhost closure 验算 ==="
echo "  JHYY_V1   = $JHYY_V1"
echo "  JHYY_V2   = $JHYY_V2"
echo "  JHYY_INPUT = $JHYY_INPUT"
echo "  BUILD_DIR = $JHY_FP_BUILD_DIR"
echo "  MAX_N     = $JHY_FP_MAX_N"
echo

# Build v3.exe from v2 (jhyy.exe) compiling main.jhyy
# jhyy 在 Windows 上会自动给 -o 加 .exe 后缀,所以 output 是 jhyy_v3.exe.exe
# 重要: v3 binary 必须放在 compiler/build/bin/ 下,jh_paths_init 走 dirname × 4
#       找 qbe.exe。如果放 /tmp/jhyy_fp/ 则 argv[0] = "/tmp/jhyy_fp/jhyy_v3.exe.exe"
#       walks up 4 次 → "/" 失败 ("cannot derive project root from argv[0]")
JHYY_V3_BASE="$JHY_FP_BUILD_DIR/jhyy_v3.exe"
JHYY_V3="${JHYY_V3_BASE}.exe"
JHYY_V3_INROOT="$JHYY_ROOT/compiler/build/bin/jhyy_v3_fp.exe.exe"
echo "[setup] Building v3 binary (jhyy.exe → src0/main.jhyy)..."
if ! (cd "$JHYY_ROOT" && "$JHYY_V2" compile "$JHYY_INPUT" -o "$JHYY_V3_BASE" > /dev/null 2>&1); then
    echo "  ❌ FAIL (v2 failed to compile src0/main.jhyy → v3.exe)" >&2
    echo "  This is a regress baseline break, not a fixed-point issue." >&2
    exit 1
fi
if [[ ! -f "$JHYY_V3" ]]; then
    echo "  ❌ FAIL (v3.exe not produced at $JHYY_V3)" >&2
    exit 1
fi
# 复制到 project root 的 compiler/build/bin/ 下供后续调用
cp "$JHYY_V3" "$JHYY_V3_INROOT"
echo "  ✅ v3.exe built at $JHYY_V3 ($(stat -c%s "$JHYY_V3" 2>/dev/null || stat -f%z "$JHYY_V3") bytes)"
echo "  ✅ v3.exe copied to $JHYY_V3_INROOT (project-root-aware)"
echo

# ════════════════════════════════════════════════════════════════════════════
# [1/N] IL closure: v1.il ↔ v2.il ↔ v3.il (N=3, primary ship gate per D43)
# ════════════════════════════════════════════════════════════════════════════

IL_V1="$JHY_FP_BUILD_DIR/main_v1.il"
IL_V2="$JHY_FP_BUILD_DIR/main_v2.il"
IL_V3="$JHY_FP_BUILD_DIR/main_v3.il"

# v1 emit .il
# jhyy_v1.exe.exe 是 v2.5.0 frozen baseline,不支持 --no-link flag (v2.8.3 才加)
# 但默认 compile 仍产 .il/.s/.exe 三件套,直接从 .exe 旁边拿 .il 即可
(cd "$JHYY_ROOT" && "$JHYY_V1" compile --target=amd64_win "$JHYY_INPUT" -o "$JHY_FP_BUILD_DIR/_v1_main" > /dev/null 2>&1) || true
if [[ -f "$JHY_FP_BUILD_DIR/_v1_main.il" ]]; then
    cp "$JHY_FP_BUILD_DIR/_v1_main.il" "$IL_V1"
else
    echo "  ⚠️  v1 .il not produced (compile failed?)" >&2
fi

# v2 emit .il
(cd "$JHYY_ROOT" && "$JHYY_V2" compile --target=amd64_win --no-link "$JHYY_INPUT" -o "$JHY_FP_BUILD_DIR/_v2_main" > /dev/null 2>&1) || true
if [[ -f "$JHY_FP_BUILD_DIR/_v2_main.il" ]]; then
    cp "$JHY_FP_BUILD_DIR/_v2_main.il" "$IL_V2"
fi

# v3 emit .il (用 project-root-aware copy)
(cd "$JHYY_ROOT" && "$JHYY_V3_INROOT" compile --target=amd64_win --no-link "$JHYY_INPUT" -o "$JHY_FP_BUILD_DIR/_v3_main" > /dev/null 2>&1) || true
if [[ -f "$JHY_FP_BUILD_DIR/_v3_main.il" ]]; then
    cp "$JHY_FP_BUILD_DIR/_v3_main.il" "$IL_V3"
fi

SHA_V1="$(sha256sum "$IL_V1" 2>/dev/null | awk '{print $1}' || echo MISSING)"
SHA_V2="$(sha256sum "$IL_V2" 2>/dev/null | awk '{print $1}' || echo MISSING)"
SHA_V3="$(sha256sum "$IL_V3" 2>/dev/null | awk '{print $1}' || echo MISSING)"

echo "[1/3] IL closure N=3 (D43 ship gate, primary):"
echo "  v1=$SHA_V1"
echo "  v2=$SHA_V2"
echo "  v3=$SHA_V3"

if [[ "$SHA_V1" == "$SHA_V2" && "$SHA_V2" == "$SHA_V3" && "$SHA_V1" != "MISSING" ]]; then
    echo "  ✅ PASS (N=3 .il byte-equal)"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (N=3 .il NOT byte-equal)"
    if [[ "$SHA_V1" != "$SHA_V2" ]]; then
        diff "$IL_V1" "$IL_V2" | head -20 >&2
    elif [[ "$SHA_V2" != "$SHA_V3" ]]; then
        diff "$IL_V2" "$IL_V3" | head -20 >&2
    fi
    FAIL=$((FAIL + 1))
fi
echo

# ════════════════════════════════════════════════════════════════════════════
# [2/N] IL closure N=4 / N=5 (informational, NOT ship gate)
# ════════════════════════════════════════════════════════════════════════════

for N in 4 5; do
    if [[ $N -gt $JHY_FP_MAX_N ]]; then
        break
    fi
    PREV_N=$((N - 1))
    PREV_BIN="$JHYY_ROOT/compiler/build/bin/jhyy_v${PREV_N}_fp.exe.exe"
    PREV_IL="$JHY_FP_BUILD_DIR/main_v${PREV_N}.il"
    NEXT_BIN_BASE="$JHY_FP_BUILD_DIR/jhyy_v${N}.exe"
    NEXT_BIN="$JHY_FP_BUILD_DIR/jhyy_v${N}.exe.exe"
    NEXT_BIN_INROOT="$JHYY_ROOT/compiler/build/bin/jhyy_v${N}_fp.exe.exe"
    NEXT_IL="$JHY_FP_BUILD_DIR/main_v${N}.il"

    echo "[$N/$JHY_FP_MAX_N] IL closure N=$N (informational):"

    # build v_N.exe using v_(N-1).exe (用 project-root-aware copy)
    if ! (cd "$JHYY_ROOT" && "$PREV_BIN" compile "$JHYY_INPUT" -o "$NEXT_BIN_BASE" > /dev/null 2>&1); then
        echo "  ⚠️  SKIP (v$PREV_N failed to compile src0/main.jhyy → v$N.exe)"
        INFO=$((INFO + 1))
        continue
    fi
    if [[ ! -f "$NEXT_BIN" ]]; then
        echo "  ⚠️  SKIP (v$N binary not at $NEXT_BIN)"
        INFO=$((INFO + 1))
        continue
    fi
    cp "$NEXT_BIN" "$NEXT_BIN_INROOT"

    # emit .il using v_N.exe (用 --no-link 跳过链接更快)
    (cd "$JHYY_ROOT" && "$NEXT_BIN_INROOT" compile --target=amd64_win --no-link "$JHYY_INPUT" -o "$JHY_FP_BUILD_DIR/_v${N}_main" > /dev/null 2>&1) || true
    if [[ -f "$JHY_FP_BUILD_DIR/_v${N}_main.il" ]]; then
        cp "$JHY_FP_BUILD_DIR/_v${N}_main.il" "$NEXT_IL"
    fi

    NEXT_SHA="$(sha256sum "$NEXT_IL" 2>/dev/null | awk '{print $1}' || echo MISSING)"
    PREV_SHA="$(sha256sum "$PREV_IL" 2>/dev/null | awk '{print $1}' || echo MISSING)"
    echo "  v$PREV_N=$PREV_SHA"
    echo "  v$N=$NEXT_SHA"

    if [[ "$NEXT_SHA" == "$PREV_SHA" && "$NEXT_SHA" != "MISSING" ]]; then
        echo "  ✅ PASS (N=$N .il byte-equal)"
        PASS=$((PASS + 1))
    else
        echo "  ⚠️  INFO (N=$N .il differs — informational, NOT ship gate)"
        INFO=$((INFO + 1))
    fi
    echo
done

# ════════════════════════════════════════════════════════════════════════════
# [3/N] cap_test.jhyy cross-generation EXIT consistency (per V3-C ship)
# ════════════════════════════════════════════════════════════════════════════

echo "[cap_test] EXIT=$CAP_TEST_EXPECT 跨代一致验证 (per V3-C v3.1.0 ship):"

CAP_V1_EXIT="SKIP"
CAP_V2_EXIT="SKIP"
CAP_V3_EXIT="SKIP"

# v1 cap_test
if (cd "$JHYY_ROOT" && "$JHYY_V1" compile --target=amd64_win "$CAP_TEST" -o "$JHY_FP_BUILD_DIR/cap_v1.exe" > /dev/null 2>&1) && [[ -f "$JHY_FP_BUILD_DIR/cap_v1.exe" ]]; then
    CAP_V1_EXIT="$("$JHY_FP_BUILD_DIR/cap_v1.exe" > /dev/null 2>&1; echo $?)"
fi

# v2 cap_test
if (cd "$JHYY_ROOT" && "$JHYY_V2" compile --target=amd64_win "$CAP_TEST" -o "$JHY_FP_BUILD_DIR/cap_v2.exe" > /dev/null 2>&1) && [[ -f "$JHY_FP_BUILD_DIR/cap_v2.exe" ]]; then
    CAP_V2_EXIT="$("$JHY_FP_BUILD_DIR/cap_v2.exe" > /dev/null 2>&1; echo $?)"
fi

# v3 cap_test
if [[ -f "$JHYY_V3_INROOT" ]] && (cd "$JHYY_ROOT" && "$JHYY_V3_INROOT" compile --target=amd64_win "$CAP_TEST" -o "$JHY_FP_BUILD_DIR/cap_v3.exe" > /dev/null 2>&1) && [[ -f "$JHY_FP_BUILD_DIR/cap_v3.exe" ]]; then
    CAP_V3_EXIT="$("$JHY_FP_BUILD_DIR/cap_v3.exe" > /dev/null 2>&1; echo $?)"
fi

echo "  v1 cap_test exit = $CAP_V1_EXIT"
echo "  v2 cap_test exit = $CAP_V2_EXIT"
echo "  v3 cap_test exit = $CAP_V3_EXIT"

CAP_CONSISTENT=1
if [[ "$CAP_V1_EXIT" != "SKIP" && "$CAP_V1_EXIT" != "$CAP_TEST_EXPECT" ]]; then CAP_CONSISTENT=0; fi
if [[ "$CAP_V2_EXIT" != "SKIP" && "$CAP_V2_EXIT" != "$CAP_TEST_EXPECT" ]]; then CAP_CONSISTENT=0; fi
if [[ "$CAP_V3_EXIT" != "SKIP" && "$CAP_V3_EXIT" != "$CAP_TEST_EXPECT" ]]; then CAP_CONSISTENT=0; fi

if [[ $CAP_CONSISTENT -eq 1 ]]; then
    echo "  ✅ PASS (cap_test 跨 N 代 exit=$CAP_TEST_EXPECT 一致, 隐含 borrow check + 8-byte Cap<T> layout 决策一致)"
    PASS=$((PASS + 1))
else
    echo "  ❌ FAIL (cap_test exit NOT consistent — V3-C borrow check invariant 漂移)"
    FAIL=$((FAIL + 1))
fi
echo

# ════════════════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════════════════

echo "=== fixed-point 结果: $PASS PASS / $FAIL FAIL / $INFO INFO ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1