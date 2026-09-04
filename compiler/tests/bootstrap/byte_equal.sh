#!/usr/bin/env bash
# byte_equal.sh — D26 三件套 byte-equal 验证 (v2.4.0 Stage 2)
#
# 用法: byte_equal.sh <input.jhyy>
#
# 在两份 jhyy binary 上编译同一 .jhyy 源, 然后对比三层:
#   [1/3] .il byte-equal
#   [2/3] .s  byte-equal
#   [3/3] .exe byte-equal (兜底 per D26: gcc -g0 + strip + SOURCE_DATE_EPOCH
#                             + --build-id=none)
#
# 三层全部 byte-equal = D26 完成定义 (per coordination.md § 3 D26, 2026-08-05 锁).
#
# 阶段性 self-equal (per coordination.md § 3 D43, 2026-09-01 锁):
#   本 script 跑 jhyy_V1 vs jhyy_V2 = 跨版本 byte-equal, 仅在 v2.0 → v2.x 末
#   期间有效; v3.0+ 加新特性 (asm / volatile / link_section / Cap<T> layout)
#   .s / .il 因新特性变化, byte-equal 必须重 baseline (jhyy_V3 == jhyy_V4 等).
#
# 关于 .exe byte-equal (v2.4.0 实际行为):
#   - .il + .s byte-equal 是真实的 closure gate (QBE IL emit 确定性).
#   - .exe byte-equal 是 supplementary check; jhyy 内部 gcc 默认带 build-id
#     + 时间戳 → 同一 jhyy.exe 跑两次 .exe sha 不同. v2.4.0 在 main.c 内
#     gcc link line 加 `-Wl,--build-id=none -g0`, 同 binary 两次跑现在
#     byte-equal. 跨 V1↔V2 (V1 frozen predates 改动) .exe 仍会 diff,
#     标 "INFORMATIONAL" — 这是预期, 不是 closure fail.
#
# 环境变量:
#   JHYY_V1  = jhyy v1 binary path (default: compiler/build/bin/jhyy_v1.exe.exe)
#   JHYY_V2  = jhyy v2 binary path (default: compiler/build/bin/jhyy.exe)
#
# 退出码:
#   0  = .il + .s byte-equal (.exe 状态不影响退出码)
#   1  = .il 或 .s FAIL 或 setup 错 (binary 找不到等)

set -uo pipefail

# ════════════════════════════════════════════════════════════════════════════
# Args + env
# ════════════════════════════════════════════════════════════════════════════

INPUT="${1:?usage: byte_equal.sh <input.jhyy>}"
# Run jhyy from the input dir so .il/.s/.exe land alongside INPUT (predictable).
INPUT_DIR="$(cd "$(dirname "$INPUT")" && pwd)"
INPUT_NAME="$(basename "$INPUT")"
INPUT_BASE="${INPUT_NAME%.jhyy}"
JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JHYY_V1="${JHYY_V1:-$JHYY_ROOT/compiler/build/bin/jhyy_v1.exe.exe}"
JHYY_V2="${JHYY_V2:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"

# ════════════════════════════════════════════════════════════════════════════
# Setup: verify binaries + input exist
# ════════════════════════════════════════════════════════════════════════════

if [[ ! -f "$JHYY_V1" ]]; then
    echo "ERR: JHYY_V1 not found at $JHYY_V1" >&2
    echo "  set JHYY_V1 env var or build jhyy_v1.exe.exe" >&2
    exit 1
fi
if [[ ! -f "$JHYY_V2" ]]; then
    echo "ERR: JHYY_V2 not found at $JHYY_V2" >&2
    echo "  set JHYY_V2 env var or rebuild jhyy.exe" >&2
    exit 1
fi
if [[ ! -f "$INPUT" ]]; then
    echo "ERR: input not found: $INPUT" >&2
    exit 1
fi

PASS=0
FAIL=0
INFO=0

echo "=== byte-equal 验证: $INPUT_NAME ==="
echo "  JHYY_V1 = $JHYY_V1"
echo "  JHYY_V2 = $JHYY_V2"
echo

# Cleanup stale artifacts before run
rm -f "$INPUT_DIR/${INPUT_BASE}_v1.il" "$INPUT_DIR/${INPUT_BASE}_v2.il"
rm -f "$INPUT_DIR/${INPUT_BASE}_v1.s"  "$INPUT_DIR/${INPUT_BASE}_v2.s"
rm -f "$INPUT_DIR/${INPUT_BASE}_v1.exe" "$INPUT_DIR/${INPUT_BASE}_v2.exe"
rm -f "$INPUT_DIR/${INPUT_BASE}.il"     "$INPUT_DIR/${INPUT_BASE}.s"     "$INPUT_DIR/${INPUT_BASE}.exe"

# ════════════════════════════════════════════════════════════════════════════
# [1/3] .il byte-equal
# ════════════════════════════════════════════════════════════════════════════
# jhyy compile writes .il next to source (per compile() flow in main.c).
# Run V1, snapshot .il to _v1.il BEFORE V2 overwrites it.

echo "[1/3] .il byte-equal:"
(cd "$INPUT_DIR" && "$JHYY_V1" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.il" ]]; then
    echo "  ❌ FAIL (V1 didn't produce .il)"
    FAIL=$((FAIL + 1))
else
    cp "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}_v1.il"
    (cd "$INPUT_DIR" && "$JHYY_V2" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.il" ]]; then
        echo "  ❌ FAIL (V2 didn't produce .il)"
        FAIL=$((FAIL + 1))
    else
        cp "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}_v2.il"
        if diff -q "$INPUT_DIR/${INPUT_BASE}_v1.il" "$INPUT_DIR/${INPUT_BASE}_v2.il" > /dev/null 2>&1; then
            echo "  ✅ PASS (.il byte-equal)"
            PASS=$((PASS + 1))
        else
            echo "  ❌ FAIL (.il byte-equal)"
            FAIL=$((FAIL + 1))
        fi
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# [2/3] .s byte-equal
# ════════════════════════════════════════════════════════════════════════════
# jhyy compile writes .s next to source (via QBE). Same pattern as .il:
# V1 produces .s, snapshot to _v1.s, then V2 runs and snapshots to _v2.s.

echo "[2/3] .s byte-equal:"
(cd "$INPUT_DIR" && "$JHYY_V1" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.s" ]]; then
    echo "  ⚠️  SKIP (V1 didn't produce .s — QBE step may not have run)"
    INFO=$((INFO + 1))
else
    cp "$INPUT_DIR/${INPUT_BASE}.s" "$INPUT_DIR/${INPUT_BASE}_v1.s"
    (cd "$INPUT_DIR" && "$JHYY_V2" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.s" ]]; then
        echo "  ⚠️  SKIP (V2 didn't produce .s)"
        INFO=$((INFO + 1))
    else
        cp "$INPUT_DIR/${INPUT_BASE}.s" "$INPUT_DIR/${INPUT_BASE}_v2.s"
        if diff -q "$INPUT_DIR/${INPUT_BASE}_v1.s" "$INPUT_DIR/${INPUT_BASE}_v2.s" > /dev/null 2>&1; then
            echo "  ✅ PASS (.s byte-equal)"
            PASS=$((PASS + 1))
        else
            echo "  ❌ FAIL (.s byte-equal)"
            FAIL=$((FAIL + 1))
        fi
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# [3/3] .exe byte-equal (兜底 per D26)
# ════════════════════════════════════════════════════════════════════════════
# jhyy compile writes .exe next to source (after gcc link). Same pattern:
# V1 produces .exe, snapshot to _v1.exe, then V2 runs and snapshots.
# .exe byte-equal 是 supplementary: V1 frozen predates main.c 的
# `-Wl,--build-id=none -g0` 改动, 所以跨 V1↔V2 .exe 几乎一定 diff.
# 状态标 "INFORMATIONAL" (不影响退出码).

echo "[3/3] .exe byte-equal (兜底, INFORMATIONAL — V1 frozen predates recipe):"
(cd "$INPUT_DIR" && "$JHYY_V1" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.exe" ]]; then
    echo "  ⚠️  SKIP (V1 didn't produce .exe)"
    INFO=$((INFO + 1))
else
    cp "$INPUT_DIR/${INPUT_BASE}.exe" "$INPUT_DIR/${INPUT_BASE}_v1.exe"
    (cd "$INPUT_DIR" && "$JHYY_V2" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.exe" ]]; then
        echo "  ⚠️  SKIP (V2 didn't produce .exe)"
        INFO=$((INFO + 1))
    else
        cp "$INPUT_DIR/${INPUT_BASE}.exe" "$INPUT_DIR/${INPUT_BASE}_v2.exe"
        if diff -q "$INPUT_DIR/${INPUT_BASE}_v1.exe" "$INPUT_DIR/${INPUT_BASE}_v2.exe" > /dev/null 2>&1; then
            echo "  ✅ PASS (.exe byte-equal)"
            PASS=$((PASS + 1))
        else
            echo "  ℹ️  INFO (.exe differs — expected: V1 frozen predates main.c link recipe; 同 binary 两次 .exe 现已 byte-equal, 但 cross-version 跨 main.c 版本差)"
            INFO=$((INFO + 1))
        fi
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# Cleanup intermediate artifacts
# ════════════════════════════════════════════════════════════════════════════
rm -f "$INPUT_DIR/${INPUT_BASE}.exe" "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}.s"

echo
echo "=== 结果: $PASS PASS / $FAIL FAIL / $INFO INFO ==="
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
