#!/usr/bin/env bash
# byte_equal_selfbackend.sh — V3 self-backend REAL execution gate (Gate-0)
#
# 验证: V3 self-backend (`JHY_SELF_BACKEND=1`) 跟 QBE (`QBE_FALLBACK=1`) 对
#   同一 .jhyy emit **真 byte-equal** .s (不是 byte-equal trivially 因为
#   两 path 都 fallback QBE — 那是 byte_equal_amd64.sh 的 false positive)。
#
# Why this script exists (per 用户 2026-09-23 反馈):
#   - W-083 ship commit 68b4b48 走 default QBE 路径 + regress + byte_equal_amd64
#     5/5 PASS 全是 false positive (三 gate 全不跑 self-backend; default compile
#     不设 JHY_SELF_BACKEND → run_backend 落 run_qbe path per main.jhyy:823-824)。
#   - W-083 真 execution path 是 `JHY_SELF_BACKEND=1`, 但被 W-086 (Layer 2 emit_*
#     字段约定冲突 + Layer 3 lexer 不 consume operand) 阻塞 produce 0-byte .s。
#   - Gate-0 是 V3 self-backend 唯一真 execution gate — 必须先造红灯 (3/3 FAIL)
#     才能给 W-086 真修一个有判定标准的验收 gate。
#
# 当前 v3.0.6 status (2026-09-23):
#   - 3/3 FAIL red (per W-086 阻塞, V3 self-backend 对 fmod 类测试 produce 0-byte .s)
#   - 灯转绿条件: W-086 (b)+(c) one-commit 真修 + run 此 script = 3/3 PASS green
#
# 与 byte_equal_amd64.sh 的区别:
#   byte_equal_amd64.sh  — 同一 binary 不同 codegen 路径, 但两 path 都 fallback QBE
#                          (default 不设 JHY_SELF_BACKEND → run_qbe, false positive)
#   byte_equal_selfbackend.sh — 显式 set JHY_SELF_BACKEND=1 强制真 self-backend 路径
#                               + 跟 QBE_FALLBACK=1 强 QBE baseline 比对 (真 exercise)
#
# 用法: byte_equal_selfbackend.sh [--save-baseline <path>] [--no-strict]
#
# 环境变量:
#   JHYY_BIN = jhyy binary path (default: compiler/build/bin/jhyy.exe)
#
# 退出码:
#   0  = all PASS (strict: 无 SKIP)
#   1  = 任一 FAIL (或 strict mode 下任一 SKIP)
#   2  = usage error
#
# Baseline 约定:
#   路径: compiler/tests/bootstrap/baseline/<input_base>.s.sha256
#   内容: QBE_FALLBACK=1 跑同样 input 出来的 .s 的 sha256 hash
#   gitignored: transient parity state (跟 byte_equal_amd64.sh 同 pattern)

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
# CLI parsing
# ════════════════════════════════════════════════════════════════════════════

SAVE_BASELINE_DIR=""
STRICT=1   # default ON

usage() {
    cat <<EOF >&2
用法: byte_equal_selfbackend.sh [--save-baseline <path>] [--no-strict]
  --save-baseline <path>  QBE-path .s sha256 → <path>/<base>.s.sha256 (refresh QBE baseline)
  --no-strict             SKIP 不再计入 FAIL (debug only)

环境: JHYY_BIN = jhyy binary path (default: compiler/build/bin/jhyy.exe)

Gate-0 预期 (2026-09-23 v3.0.6 status):
  红灯 (W-086 阻塞): 3/3 FAIL (0-byte .s + gcc link fail + exit code 异常)
  绿灯 (W-086 (b)+(c) 真修后): 3/3 PASS (.s non-empty + sha byte-equal to baseline)
EOF
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --save-baseline) SAVE_BASELINE_DIR="$2"; shift 2 ;;
        --no-strict)     STRICT=0; shift ;;
        -h|--help)       usage ;;
        *)               echo "ERR: unknown arg $1" >&2; usage ;;
    esac
done

# 3 测试 (per W-058 真修 ship in v3.0.6/Ph.2):
#   fmod_basic     — 7.0 % 2.0    exit 1
#   fmod_negative  — -7.5 % 2.0   exit 99 (trunc 区分 floor 关键)
#   fmod_f32       — 7.0_f32 % 2.0_f32  exit 1 (polymorphic f32 fold)
#
# 这 3 个测试 exercise:
#   - binop (5 IL insns polymorphic by tok.qbe_type, per Ph.2)
#   - conv (stosi/dtosi/swtof, per Ph.3 — 真正覆盖 W-083 Layer 1 真修)
#   - copy IMM + copy TEMP + call (emit_call return)
TESTS=(
    "examples/fmod_basic.jhyy|1"
    "examples/fmod_negative.jhyy|99"
    "examples/fmod_f32.jhyy|1"
)

EXAMPLES_DIR="$JHYY_ROOT/compiler/tests"
BASELINE_DIR="$JHYY_ROOT/compiler/tests/bootstrap/baseline"

PASS=0
SKIP=0
FAIL=0

echo "=== byte_equal_selfbackend (Gate-0) ==="
echo "  JHYY_BIN=$JHYY_BIN"
echo "  BASELINE_DIR=$BASELINE_DIR"
[[ -n "$SAVE_BASELINE_DIR" ]] && echo "  --save-baseline=$SAVE_BASELINE_DIR"
echo "  strict=$STRICT"
echo

for entry in "${TESTS[@]}"; do
    IFS='|' read -r t expected_exit <<< "$entry"
    INPUT="$EXAMPLES_DIR/$t"
    INPUT_NAME="$(basename "$INPUT")"
    INPUT_BASE="${INPUT_NAME%.jhyy}"
    INPUT_DIR="$(dirname "$INPUT")"

    if [[ ! -f "$INPUT" ]]; then
        echo "SKIP $t (file not found)"
        SKIP=$((SKIP + 1))
        continue
    fi

    echo "=== $t (expected exit=$expected_exit) ==="

    # Cleanup stale (defensive)
    rm -f "$INPUT_DIR/${INPUT_BASE}_self.il" "$INPUT_DIR/${INPUT_BASE}_self.s"
    rm -f "$INPUT_DIR/${INPUT_BASE}_qbe.il" "$INPUT_DIR/${INPUT_BASE}_qbe.s"
    rm -f "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}.s"

    # 路径 A: QBE (QBE_FALLBACK=1 显式, 强 QBE 路径)
    # 拿 .s sha 当 baseline (跟 self-backend path 比对)
    (cd "$INPUT_DIR" && QBE_FALLBACK=1 "$JHYY_BIN" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.s" ]]; then
        echo "  ❌ FAIL (QBE path didn't produce .s — baseline 不可用)"
        FAIL=$((FAIL + 1))
        continue
    fi
    QBE_S_SHA=$(sha256sum "$INPUT_DIR/${INPUT_BASE}.s" | awk '{print $1}')
    QBE_S_SIZE=$(wc -c < "$INPUT_DIR/${INPUT_BASE}.s")
    echo "  [QBE] .s size=${QBE_S_SIZE}B sha=${QBE_S_SHA:0:16}..."

    # Save QBE baseline FIRST (deterministic; serves as green target)
    if [[ -n "$SAVE_BASELINE_DIR" ]]; then
        mkdir -p "$SAVE_BASELINE_DIR"
        echo "$QBE_S_SHA" > "$SAVE_BASELINE_DIR/${INPUT_BASE}.s.sha256"
    fi

    # 路径 B: self backend (JHY_SELF_BACKEND=1 显式 — 强制真 self-backend 路径)
    (cd "$INPUT_DIR" && JHY_SELF_BACKEND=1 "$JHYY_BIN" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true

    # [1/4] .s 非空 (size > 100B 防 0-byte 漏)
    if [[ ! -f "$INPUT_DIR/${INPUT_BASE}.s" ]]; then
        echo "  ❌ FAIL (self path didn't produce .s)"
        FAIL=$((FAIL + 1))
        continue
    fi
    SELF_S_SIZE=$(wc -c < "$INPUT_DIR/${INPUT_BASE}.s")
    if [[ $SELF_S_SIZE -le 100 ]]; then
        echo "  ❌ FAIL (.s size $SELF_S_SIZE <= 100B — likely 0-byte, W-086 阻塞)"
        FAIL=$((FAIL + 1))
        continue
    fi

    SELF_S_SHA=$(sha256sum "$INPUT_DIR/${INPUT_BASE}.s" | awk '{print $1}')
    echo "  [self] .s size=${SELF_S_SIZE}B sha=${SELF_S_SHA:0:16}..."

    # [2/4] sha byte-equal to QBE baseline
    if [[ "$SELF_S_SHA" == "$QBE_S_SHA" ]]; then
        echo "  ✅ PASS (.s sha byte-equal to QBE baseline)"
        PASS=$((PASS + 1))
    else
        echo "  ❌ FAIL (.s sha drift: got=${SELF_S_SHA:0:16}... expected=${QBE_S_SHA:0:16}...)"
        FAIL=$((FAIL + 1))
        continue
    fi

    # [3/4] gcc link success — 通过 compile exit code 间接验证 (compile 包含 link 步骤)
    # 完整重建 + run 验证 exit code 太慢, 这里用 .s non-empty + sha byte-equal
    # 当代理 (W-086 fix 后 .s 正确, link 自然 pass per regress baseline)

    # [4/4] exit code 期望值验证 (运行 .exe, 拿 exit code)
    if [[ -x "$INPUT_DIR/${INPUT_BASE}.exe" ]] || [[ -f "$INPUT_DIR/${INPUT_BASE}.exe" ]]; then
        actual_exit=$("$INPUT_DIR/${INPUT_BASE}.exe" 2>/dev/null; echo $?)
        # bash $? 是 8-bit truncate; 但 expected 都在 0-127, 不冲突
        if [[ "$actual_exit" == "$expected_exit" ]]; then
            echo "  ✅ PASS (.exe exit=$actual_exit == expected=$expected_exit)"
            PASS=$((PASS + 1))
        else
            echo "  ❌ FAIL (.exe exit=$actual_exit, expected=$expected_exit)"
            FAIL=$((FAIL + 1))
            continue
        fi
    else
        # compile 没产 .exe → gcc link fail → W-086 阻塞证据
        echo "  ⚠️  SKIP (exit code check; .exe 不存在 = gcc link fail, W-086 阻塞证据)"
        SKIP=$((SKIP + 1))
    fi
done

echo
echo "=== byte_equal_selfbackend (Gate-0) 总结: $PASS PASS / $SKIP SKIP / $FAIL FAIL (strict=$STRICT) ==="
echo
echo "Gate-0 status interpretation:"
echo "  红灯 (3/3 FAIL): W-086 阻塞, V3 self-backend produce 0-byte .s (current state per 2026-09-23)"
echo "  绿灯 (3/3 PASS): W-086 (b)+(c) 真修后, V3 self-backend 跟 QBE byte-equal"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
if [[ $STRICT -eq 1 && $SKIP -gt 0 ]]; then
    exit 1
fi
exit 0