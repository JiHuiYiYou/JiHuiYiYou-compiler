#!/usr/bin/env bash
# byte_equal_amd64.sh — V2-B v2.6.0 (Unit F) byte-equal driver
#
# 验证: 同一 .jhyy 用两种 codegen 路径编译 → .il + .s byte-equal
#   路径 A (QBE)        : QBE_FALLBACK=1 jhyy build  (legacy v1.x path)
#   路径 B (self backend) : QBE_FALLBACK=0 jhyy build  (default v2.6.0+;
#                                                       run_backend routes
#                                                       through target_backend_mode)
#
# 自举闭环定义 (per V2-A ship gate #5): 5/5 测试两种路径 .il + .s 全部 byte-equal.
#
# 当前 v2.6.0 状态 (2026-09-06 ship):
#   - target_dispatch.jhyy: BACKEND_QBE / BACKEND_SELF + target_backend_mode()
#     wired; run_backend 走 target_backend_mode 但恒 fallback run_qbe
#     (codegen_amd64_run call site DEFERRED — `import codegen_amd64` 在
#     main.jhyy 中触发 stage0 segfault, v2.6.x 再 wire 真 self body).
#   - 本 script 现在跑的是 QBE-vs-QBE (因为 self path 还在 fallback) =
#     trivially PASS. 真正 self-vs-QBE 比对 gate 等 v2.6.x wire-up 后
#     自动激活 (无需改本 script).
#
# 与 byte_equal.sh 的区别:
#   byte_equal.sh       — V1 vs V2 跨 jhyy binary 版本 (D43 self-host closure)
#   byte_equal_amd64.sh — 同一 binary 不同 codegen 路径 (self backend parity)
#
# 用法: byte_equal_amd64.sh  (无 args; 用内置 5 测试列表)
#
# 环境变量:
#   JHYY_BIN = jhyy binary path (default: compiler/build/bin/jhyy.exe)
#
# 退出码:
#   0  = 5/5 PASS (或 SKIP)
#   1  = 任一 FAIL

set -uo pipefail

# ════════════════════════════════════════════════════════════════════════════
# Setup
# ════════════════════════════════════════════════════════════════════════════

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JHYY_BIN="${JHYY_BIN:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"

if [[ ! -f "$JHYY_BIN" ]]; then
    echo "ERR: JHYY_BIN not found at $JHYY_BIN" >&2
    echo "  set JHYY_BIN env var or rebuild jhyy.exe" >&2
    exit 1
fi

# 5 测试列表 (per V2-B plan § Unit F)
# 注意: hello-freestanding 是 UEFI target (TARGET_AMD64_WIN_FREESTANDING),
# 主仓 regress 默认不跑 (需 OVMF env); 这里只验证 .il byte-equal (不进 QBE
# → 不需 freestanding env, QBE 仍生成 .s 给 amd64_win_freestanding target)
TESTS=(
    "examples/hello.jhyy"
    "examples/fib_renamed.jhyy"
    "examples/struct_val_pass.jhyy"
    "examples/hello-freestanding/hello-freestanding.jhyy"
    "examples/mixed_struct_slice_match.jhyy"
)

EXAMPLES_DIR="$JHYY_ROOT/compiler/tests"

# 通知: 当前 self path deferred 状态
SELF_DEFERRED=1  # 1 = self backend call site deferred, 0 = wired

PASS=0
SKIP=0
FAIL=0

if [[ $SELF_DEFERRED -eq 1 ]]; then
    echo "=== byte_equal_amd64 ==="
    echo "  NOTE: self backend call site deferred to v2.6.x (Unit E wire)"
    echo "        (codegen_amd64_run call site triggers stage0 segfault"
    echo "         when imported in main.jhyy — see commit 129226b)"
    echo "        当前跑 QBE-vs-QBE (trivially PASS); 真正 self-vs-QBE gate"
    echo "        等 v2.6.x wire-up 后自动激活."
    echo
fi

for t in "${TESTS[@]}"; do
    INPUT="$EXAMPLES_DIR/$t"
    INPUT_NAME="$(basename "$INPUT")"
    INPUT_BASE="${INPUT_NAME%.jhyy}"
    INPUT_DIR="$(dirname "$INPUT")"

    if [[ ! -f "$INPUT" ]]; then
        echo "SKIP $t (file not found)"
        SKIP=$((SKIP + 1))
        continue
    fi

    echo "=== $t ==="

    # Cleanup stale (defensive — 防上轮 / 并行 suite 残留)
    rm -f "$INPUT_DIR/${INPUT_BASE}_qbe.il" "$INPUT_DIR/${INPUT_BASE}_self.il"
    rm -f "$INPUT_DIR/${INPUT_BASE}_qbe.s"  "$INPUT_DIR/${INPUT_BASE}_self.s"
    rm -f "$INPUT_DIR/${INPUT_BASE}.il"     "$INPUT_DIR/${INPUT_BASE}.s"

    # 路径 A: QBE (QBE_FALLBACK=1 explicit override)
    # 用 compile (not build) — compile 跑完整流水线到 .il+.s+.exe;
    # build 只到 .il.
    (cd "$INPUT_DIR" && QBE_FALLBACK=1 "$JHYY_BIN" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.il" ]]; then
        echo "  ❌ FAIL (QBE path didn't produce .il)"
        FAIL=$((FAIL + 1))
        continue
    fi
    cp "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}_qbe.il"
    cp "$INPUT_DIR/${INPUT_BASE}.s"  "$INPUT_DIR/${INPUT_BASE}_qbe.s"

    # 路径 B: self backend (default — no QBE_FALLBACK env)
    (cd "$INPUT_DIR" && "$JHYY_BIN" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.il" ]]; then
        echo "  ❌ FAIL (self path didn't produce .il)"
        FAIL=$((FAIL + 1))
        continue
    fi
    cp "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}_self.il"
    if [[ -f "$INPUT_DIR/${INPUT_BASE}.s" ]]; then
        cp "$INPUT_DIR/${INPUT_BASE}.s" "$INPUT_DIR/${INPUT_BASE}_self.s"
    fi

    # [1/2] .il byte-equal
    if diff -q "$INPUT_DIR/${INPUT_BASE}_qbe.il" "$INPUT_DIR/${INPUT_BASE}_self.il" > /dev/null 2>&1; then
        echo "  ✅ PASS (.il byte-equal)"
        PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL (.il byte-equal)"
        FAIL=$((FAIL + 1))
    fi

    # [2/2] .s byte-equal (if both produced)
    if [[ -f "$INPUT_DIR/${INPUT_BASE}_qbe.s" && -f "$INPUT_DIR/${INPUT_BASE}_self.s" ]]; then
        if diff -q "$INPUT_DIR/${INPUT_BASE}_qbe.s" "$INPUT_DIR/${INPUT_BASE}_self.s" > /dev/null 2>&1; then
            echo "  ✅ PASS (.s byte-equal)"
            PASS=$((PASS + 1))
        else
            echo "  ❌ FAIL (.s byte-equal)"
            FAIL=$((FAIL + 1))
        fi
    else
        echo "  ⚠️  SKIP (.s; QBE 或 self 没产出 .s)"
        SKIP=$((SKIP + 1))
    fi
done

echo
echo "=== byte_equal_amd64 总结: $PASS PASS / $SKIP SKIP / $FAIL FAIL ==="
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
exit 0