#!/usr/bin/env bash
# byte_equal_selfbackend.sh — V3 self-backend REAL execution gate (Gate-0)
#
# 验证: V3 self-backend (`JHY_SELF_BACKEND=1`) 对同一 .jhyy emit **真 .s**,
#       跟 V2 (axis-v2 v2.16.0) self-backend golden 对照 byte-equal 或
#       mnemonically equivalent (允许寄存器分配 / 指令顺序差异)。
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
# 当前 v3.0.7 status (2026-09-23):
#   - 3/3 FAIL red (per W-086 阻塞, V3 self-backend 对 fmod 类测试 produce 0-byte .s)
#   - 灯转绿条件: W-086 (b)+(c) one-commit 真修 + run 此 script = 3/3 PASS green
#
# 与 byte_equal_amd64.sh 的区别:
#   byte_equal_amd64.sh  — 同一 binary 不同 codegen 路径, 但两 path 都 fallback QBE
#                          (default 不设 JHY_SELF_BACKEND → run_qbe, false positive)
#   byte_equal_selfbackend.sh — 显式 set JHY_SELF_BACKEND=1 强制真 self-backend 路径
#                               + 跟 V2 self-backend golden 比对 (真 exercise)
#
# 用法: byte_equal_selfbackend.sh [--no-strict]
#
# 环境变量:
#   JHYY_BIN = jhyy binary path (default: compiler/build/bin/jhyy.exe)
#
# 退出码:
#   0  = all PASS (strict: 无 SKIP)
#   1  = 任一 FAIL (或 strict mode 下任一 SKIP)
#   2  = usage error
#
# Baseline 约定 (per v3.0.7/Commit 0):
#   路径: compiler/tests/bootstrap/baseline_v2_self/v2_self_<name>.s
#   内容: V2 (axis-v2 v2.16.0) self-backend 实跑产出 .s (静态 golden,commit 入仓)
#   3 测试: fmod_basic (exit 1) / fmod_negative (exit 99) / fmod_f32 (exit 1)
#
# [2/4] adaptive sha strategy (per 用户 2026-09-23 反馈 补强 #2):
#   1. Strict sha: V3 self .s sha256 vs V2 golden sha256
#   2. Strict fail → fallback: extract mnemonics (sorted opcode multiset),
#      compare. 允许寄存器分配/指令顺序差异, 要求 op coverage 一致。
#   3. 两种 mode 结果都打: strict_first (PASS/FAIL) + mnemonic_fallback (PASS/FAIL)
#   4. [2/4] PASS if 任一 mode PASS (覆盖 V3 emit_conv 实现不同的合理差异)
#   5. workarounds.md 记 "V3 emit_conv 与 V2 emit_conv_* 实现不同源" 当 mnemonic mode 触发

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

STRICT=1   # default ON

usage() {
    cat <<EOF >&2
用法: byte_equal_selfbackend.sh [--no-strict]

环境: JHYY_BIN = jhyy binary path (default: compiler/build/bin/jhyy.exe)

Gate-0 预期 (2026-09-23 v3.0.7 status):
  红灯 (W-086 阻塞): 3/3 FAIL (0-byte .s + gcc link fail + exit code 异常)
  绿灯 (W-086 (b)+(c) 真修后): 3/3 PASS (.s non-empty + sha/mnemonic 比对通过)
EOF
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
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
BASELINE_DIR="$JHYY_ROOT/compiler/tests/bootstrap/baseline_v2_self"

# Sanity: baseline must exist (per Commit 0 入库)
if [[ ! -d "$BASELINE_DIR" ]]; then
    echo "ERR: V2 golden baseline dir missing: $BASELINE_DIR" >&2
    echo "  这是 v3.0.7/Commit 0 必须落地的资产。详见 $BASELINE_DIR/README.md" >&2
    exit 1
fi

PASS=0
SKIP=0
FAIL=0

echo "=== byte_equal_selfbackend (Gate-0) ==="
echo "  JHYY_BIN=$JHYY_BIN"
echo "  BASELINE_DIR=$BASELINE_DIR (V2 self-backend golden, Commit 0 入库)"
echo "  strict=$STRICT"
echo

for entry in "${TESTS[@]}"; do
    IFS='|' read -r t expected_exit <<< "$entry"
    INPUT="$EXAMPLES_DIR/$t"
    INPUT_NAME="$(basename "$INPUT")"
    INPUT_BASE="${INPUT_NAME%.jhyy}"
    INPUT_DIR="$(dirname "$INPUT")"
    BASELINE_FILE="$BASELINE_DIR/v2_self_${INPUT_BASE}.s"

    if [[ ! -f "$INPUT" ]]; then
        echo "SKIP $t (file not found)"
        SKIP=$((SKIP + 1))
        continue
    fi

    if [[ ! -f "$BASELINE_FILE" ]]; then
        echo "SKIP $t (V2 golden missing: $BASELINE_FILE)"
        SKIP=$((SKIP + 1))
        continue
    fi

    echo "=== $t (expected exit=$expected_exit, V2 golden=${BASELINE_FILE##*/}) ==="

    # Cleanup stale
    rm -f "$INPUT_DIR/${INPUT_BASE}.il" "$INPUT_DIR/${INPUT_BASE}.s" "$INPUT_DIR/${INPUT_BASE}.exe"

    # 路径 A: V3 self backend (JHY_SELF_BACKEND=1 显式 — 强制真 self-backend 路径)
    (cd "$INPUT_DIR" && JHY_SELF_BACKEND=1 "$JHYY_BIN" compile --target=amd64_win "$INPUT_NAME" > /dev/null 2>&1) || true

    # [1/4] .s 非空 (size > 100B 防 0-byte 漏)
    SELF_S="$INPUT_DIR/${INPUT_BASE}.s"
    if [[ ! -f "$SELF_S" ]]; then
        echo "  ❌ FAIL (self path didn't produce .s)"
        FAIL=$((FAIL + 1))
        continue
    fi
    SELF_S_SIZE=$(wc -c < "$SELF_S")
    if [[ $SELF_S_SIZE -le 100 ]]; then
        echo "  ❌ FAIL (.s size $SELF_S_SIZE <= 100B — likely 0-byte, W-086 阻塞)"
        FAIL=$((FAIL + 1))
        continue
    fi

    SELF_S_SHA=$(sha256sum "$SELF_S" | awk '{print $1}')
    GOLDEN_SHA=$(sha256sum "$BASELINE_FILE" | awk '{print $1}')
    echo "  [self]    .s size=${SELF_S_SIZE}B sha=${SELF_S_SHA:0:16}..."
    echo "  [V2 gold] .s size=$(wc -c < "$BASELINE_FILE")B sha=${GOLDEN_SHA:0:16}..."

    # [2/4] adaptive sha strategy (strict first → mnemonic fallback)
    STRICT_PASS=0
    MNEMONIC_PASS=0
    if [[ "$SELF_S_SHA" == "$GOLDEN_SHA" ]]; then
        echo "  ✅ [2/4] strict sha PASS (byte-identical to V2 golden)"
        STRICT_PASS=1
        MNEMONIC_PASS=1
    else
        echo "  ⚠️  [2/4] strict sha FAIL (sha drift; 预期若 V3 emit_conv != V2 emit_conv_*)"
        # Mnemonic fallback: extract opcodes (sorted multiset), compare
        # Strip comment lines (#) and blank lines, take first whitespace-delimited token
        SELF_MNEMONICS=$(grep -v '^\s*#' "$SELF_S" | grep -v '^\s*$' | awk '{print $1}' | sort)
        GOLDEN_MNEMONICS=$(grep -v '^\s*#' "$BASELINE_FILE" | grep -v '^\s*$' | awk '{print $1}' | sort)
        if [[ "$SELF_MNEMONICS" == "$GOLDEN_MNEMONICS" ]]; then
            SELF_UNIQ=$(echo "$SELF_MNEMONICS" | sort -u | wc -l)
            SELF_TOTAL=$(echo "$SELF_MNEMONICS" | wc -l)
            echo "  ✅ [2/4] mnemonic fallback PASS (op coverage identical, ${SELF_TOTAL} insns, ${SELF_UNIQ} unique)"
            MNEMONIC_PASS=1
        else
            echo "  ❌ [2/4] mnemonic fallback FAIL (op coverage drift)"
            # Show diff (sorted, uniq) for diagnosis
            diff <(echo "$SELF_MNEMONICS" | sort -u) <(echo "$GOLDEN_MNEMONICS" | sort -u) | head -20 | sed 's/^/    /'
        fi
    fi

    if [[ $STRICT_PASS -eq 0 && $MNEMONIC_PASS -eq 0 ]]; then
        FAIL=$((FAIL + 1))
        continue
    fi
    PASS=$((PASS + 1))

    # [3/4] gcc link success — implicit via compile exit (V2 W-086 真修后 link pass)

    # [4/4] exit code 期望值验证 (运行 .exe, 拿 exit code)
    EXE="$INPUT_DIR/${INPUT_BASE}.exe"
    if [[ -x "$EXE" ]] || [[ -f "$EXE" ]]; then
        # v3.0.7/Commit 1 fix: 原 "./$EXE" 在 cwd 跑会拼出无效相对路径 →
        # exit=127 ("command not found"), 即使 .exe 是合法的。EXE 是绝对路径,
        # 直接 "$EXE" 即可。
        "$EXE" > /dev/null 2>&1
        actual_exit=$?
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
echo "  红灯 (3/3 FAIL): W-086 阻塞, V3 self-backend produce 0-byte .s (current state pre-W-086-fix)"
echo "  绿灯 (3/3 PASS): W-086 真修后, V3 self-backend .s sha/mnemonic 跟 V2 golden 对齐"

if [[ $FAIL -gt 0 ]]; then
    exit 1
fi
if [[ $STRICT -eq 1 && $SKIP -gt 0 ]]; then
    exit 1
fi
exit 0
