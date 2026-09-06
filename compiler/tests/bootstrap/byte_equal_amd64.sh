#!/usr/bin/env bash
# byte_equal_amd64.sh — V2-B v2.6.7 (Commit 5) byte-equal driver
#
# 验证: 同一 .jhyy 用两种 codegen 路径编译 → .il + .s byte-equal
#   路径 A (QBE)        : QBE_FALLBACK=1 jhyy build  (legacy v1.x path)
#   路径 B (self backend) : QBE_FALLBACK=0 jhyy build  (default v2.6.0+;
#                                                       run_backend routes
#                                                       through target_backend_mode)
#
# 自举闭环定义 (per V2-A ship gate #5): 5/5 测试两种路径 .il + .s 全部 byte-equal.
#
# 当前 v2.6.7 状态 (2026-09-06 ship):
#   - real self backend wired (v2.6.6 W-069 fix); default jhyy compile
#     走 target_backend_mode → codegen_amd64_run 真 path.
#   - 本 script 真跑 QBE-vs-self (--target=amd64_win, QBE_FALLBACK=1
#     vs default).
#   - strict mode default-ON (任一 FAIL/SKIP exit 1).
#   - --save-baseline <path> 把 self-path .il/.s sha256 写到 <path>/.
#   - --baseline     <path> 加载存档 baseline 比对 (catches self drift
#     即使 QBE≡self gate 仍 hold).
#
# 与 byte_equal.sh 的区别:
#   byte_equal.sh       — V1 vs V2 跨 jhyy binary 版本 (D43 self-host closure)
#   byte_equal_amd64.sh — 同一 binary 不同 codegen 路径 (self backend parity)
#
# 用法: byte_equal_amd64.sh [--save-baseline <path>] [--baseline <path>] [--no-strict]
#
# 环境变量:
#   JHYY_BIN = jhyy binary path (default: compiler/build/bin/jhyy.exe)
#
# 退出码:
#   0  = all PASS (strict: 无 SKIP)
#   1  = 任一 FAIL (或 strict mode 下任一 SKIP)
#   2  = usage error
#
# Baseline 约定 (--save-baseline 写出的 .sha256 文件):
#   - 路径: <dir>/<input_base>.{il,s}.sha256 (per-input, 排除 .exe)
#   - gitignored: `compiler/tests/bootstrap/baseline/` (transient parity state,
#     跟 *.il/*.s 同类 build artifact)
#   - refresh: codegen 有意 emit 变更后跑 `--save-baseline <dir>` 重写存档
#   - drift: `--baseline <dir>` catches self emit 漂移即使 QBE≡self gate 仍 hold

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

# ════════════════════════════════════════════════════════════════════════════
# CLI parsing (v2.6.7 Commit 5)
# ════════════════════════════════════════════════════════════════════════════

SAVE_BASELINE_DIR=""
LOAD_BASELINE_DIR=""
STRICT=1   # default ON per 2026-09-06 user Q1 decision

usage() {
    cat <<EOF >&2
用法: byte_equal_amd64.sh [--save-baseline <path>] [--baseline <path>] [--no-strict]
  --save-baseline <path>  self-path .il/.s sha256 → <path>/<base>.{il,s}.sha256
  --baseline     <path>  比对 self-path sha 与存档 (catches drift)
  --no-strict            SKIP 不再计入 FAIL (debug only)
EOF
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --save-baseline) SAVE_BASELINE_DIR="$2"; shift 2 ;;
        --baseline)      LOAD_BASELINE_DIR="$2"; shift 2 ;;
        --no-strict)     STRICT=0; shift ;;
        -h|--help)       usage ;;
        *)               echo "ERR: unknown arg $1" >&2; usage ;;
    esac
done

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

PASS=0
SKIP=0
FAIL=0

echo "=== byte_equal_amd64 ==="
echo "  JHYY_BIN=$JHYY_BIN"
[[ -n "$SAVE_BASELINE_DIR" ]] && echo "  --save-baseline=$SAVE_BASELINE_DIR"
[[ -n "$LOAD_BASELINE_DIR"  ]] && echo "  --baseline=$LOAD_BASELINE_DIR"
echo "  strict=$STRICT"
echo

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

    # [3/N] Optional: save self-path sha256 baseline (per v2.6.7)
    if [[ -n "$SAVE_BASELINE_DIR" ]]; then
        mkdir -p "$SAVE_BASELINE_DIR"
        for ext in il s; do
            if [[ -f "$INPUT_DIR/${INPUT_BASE}_self.${ext}" ]]; then
                sha256sum "$INPUT_DIR/${INPUT_BASE}_self.${ext}" \
                    | awk '{print $1}' > "$SAVE_BASELINE_DIR/${INPUT_BASE}.${ext}.sha256"
            fi
        done
    fi

    # [4/N] Optional: compare self-path sha against loaded baseline (drift detection)
    if [[ -n "$LOAD_BASELINE_DIR" ]]; then
        for ext in il s; do
            base="$LOAD_BASELINE_DIR/${INPUT_BASE}.${ext}.sha256"
            if [[ ! -f "$base" ]]; then
                echo "  ⚠️  SKIP (.${ext} baseline missing: $base)"
                SKIP=$((SKIP + 1))
                continue
            fi
            cur_sha=$(sha256sum "$INPUT_DIR/${INPUT_BASE}_self.${ext}" 2>/dev/null | awk '{print $1}')
            exp_sha=$(cat "$base")
            if [[ "$cur_sha" == "$exp_sha" ]]; then
                echo "  ✅ PASS (.${ext} matches baseline)"
                PASS=$((PASS + 1))
            else
                echo "  ❌ FAIL (.${ext} drift: got=${cur_sha:0:16}... expected=${exp_sha:0:16}...)"
                FAIL=$((FAIL + 1))
            fi
        done
    fi
done

echo
echo "=== byte_equal_amd64 总结: $PASS PASS / $SKIP SKIP / $FAIL FAIL (strict=$STRICT) ==="
if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
if [[ $STRICT -eq 1 && $SKIP -gt 0 ]]; then
    exit 1
fi
exit 0