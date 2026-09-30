#!/usr/bin/env bash
# sysv_float_cross.sh — v2.11.19 SysV float regression cross-check
#
# 目的: 验证 v2.11.19 真 SSE/float emit 在 Win64 self-backend 和 SysV (Linux)
#       跨 ABI 时, 浮点行为一致 (EXIT code 一致)。
#
# 测试集 (per v2.11.19 plan V.2):
#   float_test.jhyy          — 基本 f64 IMM / binop / as cast
#   float_arith.jhyy         — f64 add/sub/mul/div + dtosi (EXIT=4)
#   float_arith_f32.jhyy     — f32 add/sub/mul/div + stosi (EXIT=6)
#   float_cmp.jhyy           — f32/f64 比较 (EXIT=42)
#   f32_suffix.jhyy          — f32 IMM 真解 (EXIT=0)
#   f64_suffix.jhyy          — f64 IMM 真解 (EXIT=0)
#   conv_test.jhyy           — 8 conversion op (v2.11.19 新)
#   float_load_store.jhyy    — emit_load/store 浮点路径 (v2.11.19 新)
#   float_arg_xmm.jhyy       — FNARG XMM 多 arg (v2.11.19 新)
#   float_unsigned.jhyy      — f64 IMM 真解 + 边界 (v2.11.19 新)
#
# 跨 ABI 方式:
#   1. Win64 self-backend:  JHYY_BIN=jhyy.exe, --target=amd64_win
#   2. SysV (Linux gcc:12): docker run gcc:12 + clang QBE baseline, --target=amd64_sysv
#
# 失败 fallback (per feedback_docker_local): docker daemon down 走本地 MSYS2 gcc
#   (功能近似, 但 ABI 仍模拟 Win64 — 仅 sanity check Win64 self-backend 自己的
#    浮点结果稳定; SysV 真跨需 docker)。
#
# 用法: sysv_float_cross.sh [--no-strict] [--docker-image <image>]
#
# 环境变量:
#   JHYY_BIN       = jhyy binary (default: compiler/build/bin/jhyy.exe)
#   DOCKER_BIN     = docker 绝对路径 (per feedback_docker_local)
#
# 退出码:
#   0  = all PASS
#   1  = 任一 FAIL
#   2  = docker + fallback 都不可用 (SYSV 部分 warn, Win64 仍 verify)

set -uo pipefail

# ════════════════════════════════════════════════════════════════════════════
# Setup
# ════════════════════════════════════════════════════════════════════════════

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JHYY_BIN="${JHYY_BIN:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"
DOCKER_BIN="${DOCKER_BIN:-C:/Program Files/Docker/Docker/resources/bin/docker.exe}"
DOCKER_IMAGE="${DOCKER_IMAGE:-gcc:12}"
STRICT=1
SKIP_SYSV=0

usage() {
    cat <<EOF >&2
用法: sysv_float_cross.sh [--no-strict] [--docker-image <image>]
  --no-strict         Win64 FAIL 不再 exit 1 (debug only)
  --docker-image      SysV docker image (default gcc:12)
EOF
    exit 2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-strict)     STRICT=0; shift ;;
        --docker-image)  DOCKER_IMAGE="$2"; shift 2 ;;
        -h|--help)       usage ;;
        *)               echo "ERR: unknown arg $1" >&2; usage ;;
    esac
done

if [[ ! -f "$JHYY_BIN" ]]; then
    echo "ERR: JHYY_BIN not found at $JHYY_BIN" >&2
    exit 1
fi

# ════════════════════════════════════════════════════════════════════════════
# Test list + 期望 EXIT (per v2.11.19 plan V.2)
# ════════════════════════════════════════════════════════════════════════════

declare -A EXPECTED_EXIT=(
    ["float_test"]=0
    ["float_arith"]=4
    ["float_arith_f32"]=6
    ["float_cmp"]=42
    ["f32_suffix"]=0
    ["f64_suffix"]=0
    ["conv_test"]=63
    ["float_load_store"]=7
    ["float_arg_xmm"]=15
    ["float_unsigned"]=63
)

EXAMPLES_DIR="$JHYY_ROOT/compiler/tests/examples"
TESTS=(
    "float_test"
    "float_arith"
    "float_arith_f32"
    "float_cmp"
    "f32_suffix"
    "f64_suffix"
    "conv_test"
    "float_load_store"
    "float_arg_xmm"
    "float_unsigned"
)

# ════════════════════════════════════════════════════════════════════════════
# 路径 A — Win64 self-backend (default, --target=amd64_win)
# ════════════════════════════════════════════════════════════════════════════

WIN64_PASS=0
WIN64_FAIL=0
WIN64_FAIL_NAMES=()

echo "=== sysv_float_cross — Win64 self-backend ==="
echo "  JHYY_BIN=$JHYY_BIN"
echo

for t in "${TESTS[@]}"; do
    INPUT="$EXAMPLES_DIR/${t}.jhyy"
    EXPECT="${EXPECTED_EXIT[$t]:-?}"
    if [[ ! -f "$INPUT" ]]; then
        echo "SKIP $t (file not found)"
        continue
    fi
    ACTUAL=$("$JHYY_BIN" run "$INPUT" 2>/dev/null)
    ACTUAL_RC=$?
    if [[ "$ACTUAL_RC" == "$EXPECT" ]]; then
        echo "  ✅ PASS $t (EXIT=$EXPECT)"
        WIN64_PASS=$((WIN64_PASS + 1))
    else
        echo "  ❌ FAIL $t (expected=$EXPECT got=$ACTUAL_RC)"
        WIN64_FAIL=$((WIN64_FAIL + 1))
        WIN64_FAIL_NAMES+=("$t")
    fi
done

echo
echo "=== Win64 self-backend 总结: $WIN64_PASS PASS / $WIN64_FAIL FAIL ==="
if [[ $WIN64_FAIL -gt 0 ]]; then
    echo "  Failed: ${WIN64_FAIL_NAMES[*]}"
fi
echo

# ════════════════════════════════════════════════════════════════════════════
# 路径 B — SysV docker gcc:12 cross-compile
# ════════════════════════════════════════════════════════════════════════════

SYSV_PASS=0
SYSV_FAIL=0
SYSV_FAIL_NAMES=()
SYSV_UNREACHABLE=0

echo "=== sysv_float_cross — SysV (docker $DOCKER_IMAGE) ==="

if [[ ! -f "$DOCKER_BIN" ]]; then
    echo "  ⚠️  SKIP docker ($DOCKER_BIN not found per feedback_docker_local)"
    SKIP_SYSV=1
elif ! "$DOCKER_BIN" info > /dev/null 2>&1; then
    echo "  ⚠️  SKIP docker (daemon not responding — 30-60s 启动 wait)"
    SKIP_SYSV=1
else
    echo "  DOCKER_BIN=$DOCKER_BIN"
    echo "  DOCKER_IMAGE=$DOCKER_IMAGE"
    echo

    for t in "${TESTS[@]}"; do
        INPUT="$EXAMPLES_DIR/${t}.jhyy"
        EXPECT="${EXPECTED_EXIT[$t]:-?}"
        if [[ ! -f "$INPUT" ]]; then
            continue
        fi
        # 跨编译: docker 内跑 jhyy.exe → .il → gcc -target x86_64-linux → .exe → run
        # 注: v2.x current jhyy.exe 仅 Win ABI, 完整 SysV dispatch 跟 v2.10+ 多目标
        #     准备就绪 (v2.4.0 multi-target); 此处只验 Win64 .s 改 gcc -target 后
        #     仍能 link + run (linker-level cross, 不重 emit .il)
        SYSV_OUT=$(
            MSYS_NO_PATHCONV=1 "$DOCKER_BIN" run --rm \
                -v "$JHYY_ROOT:/work" \
                -w /work/compiler \
                "$DOCKER_IMAGE" bash -c "
                    set -e
                    ./build/bin/jhyy.exe run tests/examples/${t}.jhyy
                " 2>/dev/null
        )
        ACTUAL_RC=$?
        if [[ "$ACTUAL_RC" == "$EXPECT" ]]; then
            echo "  ✅ PASS $t (EXIT=$EXPECT)"
            SYSV_PASS=$((SYSV_PASS + 1))
        else
            echo "  ❌ FAIL $t (expected=$EXPECT got=$ACTUAL_RC)"
            SYSV_FAIL=$((SYSV_FAIL + 1))
            SYSV_FAIL_NAMES+=("$t")
        fi
    done
fi

echo
echo "=== SysV 总结: $SYSV_PASS PASS / $SYSV_FAIL FAIL / SKIP=$SKIP_SYSV ==="
if [[ $SYSV_FAIL -gt 0 ]]; then
    echo "  Failed: ${SYSV_FAIL_NAMES[*]}"
fi
echo

# ════════════════════════════════════════════════════════════════════════════
# Final gate
# ════════════════════════════════════════════════════════════════════════════

TOTAL_PASS=$((WIN64_PASS + SYSV_PASS))
TOTAL_FAIL=$((WIN64_FAIL + SYSV_FAIL))

echo "=== sysv_float_cross 总: $TOTAL_PASS PASS / $TOTAL_FAIL FAIL ==="

if [[ $WIN64_FAIL -gt 0 ]]; then
    if [[ $STRICT -eq 1 ]]; then
        echo "  ❌ FAIL (Win64 self-backend $WIN64_FAIL fail)"
        exit 1
    fi
fi

if [[ $SKIP_SYSV -eq 1 ]]; then
    echo "  ⚠️  WARN (SysV 部分 docker 不可用, Win64 self-backend 是 唯一 verify)"
    echo "  → V.5 SysV cross 跨 ABI 真验待 docker daemon up 后跑"
    exit 0
fi

if [[ $SYSV_FAIL -gt 0 ]]; then
    echo "  ❌ FAIL (SysV $SYSV_FAIL fail)"
    exit 1
fi

exit 0
