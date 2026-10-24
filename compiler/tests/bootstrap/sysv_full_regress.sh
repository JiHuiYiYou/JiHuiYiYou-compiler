#!/usr/bin/env bash
# sysv_full_regress.sh — v2.13.0 Phase 2 ship gate (V.3) — 真 amd64_sysv codegen 全覆盖
#
# 跑 6 sysv regress tests (sysv_abi_test / sysv_enum_match / sysv_struct_mixed /
# sysv_struct_pass / sysv_struct_ret / sysv_vararg_basic) 走 self-backend 真 emit
# → docker gcc:12 chain 链 crt0.S + link.ld → 跑 ELF。6/6 expected exit codes:
#   sysv_abi_test    = 28 (1+2+3+4+5+6+7)
#   sysv_enum_match  = 217 (enum 参数/返回值/sret/嵌套,W-114)
#   sysv_struct_mixed= 42 (41+1)
#   sysv_struct_pass = 35 (10+25)
#   sysv_struct_ret  = 18 (struct return)
#   sysv_vararg_basic= 42 (10+32)
#
# Per `feedback_fix_evaluation_rule`:5 consecutive runs 必 6/6 PASS (count by PASS=0)。
#
# 用法:
#   bash compiler/tests/bootstrap/sysv_full_regress.sh
#   bash compiler/tests/bootstrap/sysv_full_regress.sh --runs=N   (default --runs=5)
#
# Exit code:
#   0 = 6/6 PASS on every run
#   1 = any FAIL or non-6/6 result
#
# 环境要求:
#   - docker daemon 启动 (gcc:12 image cached)
#   - compiler/build/bin/jhyy.exe (jhyy-side binary, Phase 2 真 emit)

set -uo pipefail

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JHYY_EXE="$JHYY_ROOT/compiler/build/bin/jhyy.exe"
DOCKER_BIN="${DOCKER_BIN:-/c/Program Files/Docker/Docker/resources/bin/docker.exe}"

RUNS=5
for arg in "$@"; do
    case "$arg" in
        --runs=*) RUNS="${arg#*=}" ;;
        *) echo "unknown arg: $arg" >&2; exit 1 ;;
    esac
done

# 2026-10-15:期望值搬进各个 .jhyy 文件本身(`// EXPECT: N`),本表从那里读 ——
# 单一事实来源。此前它们只住在这个脚本里,于是 cross-env 那条路径
# (regress.py --cross)拿不到期望值,只要 ELF 跑起来就报 PASS:W-116 的
# `sysv_abi_test` 退出 22 / 期望 28 就这样被放过。
read_expect() {
    grep -oE '//[[:space:]]*EXPECT[[:space:]]*[:=][[:space:]]*[0-9]+'         "$JHYY_ROOT/compiler/tests/examples/$1" | head -1 | grep -oE '[0-9]+'
}
EXPECTED_ABITEST=$(read_expect sysv_abi_test.jhyy)
EXPECTED_MIXED=$(read_expect sysv_struct_mixed.jhyy)
EXPECTED_PASS=$(read_expect sysv_struct_pass.jhyy)
EXPECTED_RET=$(read_expect sysv_struct_ret.jhyy)
EXPECTED_VARARG=$(read_expect sysv_vararg_basic.jhyy)
EXPECTED_ENUM=$(read_expect sysv_enum_match.jhyy)
echo "期望值(从 .jhyy 读): abi=$EXPECTED_ABITEST mixed=$EXPECTED_MIXED pass=$EXPECTED_PASS ret=$EXPECTED_RET vararg=$EXPECTED_VARARG enum=$EXPECTED_ENUM"

# 2026-10-24:加 sysv_enum_match(W-114 新增)—— CI 的 sysv job 已经在跑 6 个,
#   本地脚本还停在 5 个 → 「本地 5/5 绿、CI 6 个」的对不齐。单一事实来源:
#   测试名单 = CI job 的名单。
SYSV_TESTS=(sysv_abi_test sysv_enum_match sysv_struct_mixed sysv_struct_pass sysv_struct_ret sysv_vararg_basic)
declare -A EXPECTED=(
    [sysv_abi_test]=$EXPECTED_ABITEST
    [sysv_enum_match]=$EXPECTED_ENUM
    [sysv_struct_mixed]=$EXPECTED_MIXED
    [sysv_struct_pass]=$EXPECTED_PASS
    [sysv_struct_ret]=$EXPECTED_RET
    [sysv_vararg_basic]=$EXPECTED_VARARG
)

if [[ ! -f "$JHYY_EXE" ]]; then
    echo "ERR: jhyy.exe not found at $JHYY_EXE" >&2
    echo "  Run 'make' to build first" >&2
    exit 1
fi
if [[ ! -x "$DOCKER_BIN" && ! -x "$(command -v docker 2>/dev/null || echo)" ]]; then
    echo "ERR: docker not found at $DOCKER_BIN or on PATH" >&2
    echo "  Start Docker Desktop first" >&2
    exit 1
fi

echo "=== sysv_full_regress.sh — v2.13.0 Phase 2 V.3 gate ==="
echo "  JHYY_EXE   = $JHYY_EXE"
echo "  DOCKER_BIN = $DOCKER_BIN"
echo "  RUNS       = $RUNS"
echo "  Tests: ${SYSV_TESTS[*]}"
echo

OVERALL_PASS=0
OVERALL_FAIL=0

for ((run=1; run<=RUNS; run++)); do
    echo "--- Run $run/$RUNS ---"
    RUN_PASS=0
    RUN_FAIL=0
    RUN_FAIL_LIST=""

    # Stage 1: jhyy.exe 真编 ${#SYSV_TESTS[@]} 个 sysv test (self-backend 真 amd64_sysv_freestanding emit)
    # 注意:不要 MSYS_NO_PATHCONV=1 — jhyy.exe 是 native Win32 binary 不识 POSIX path,
    # MSYS 默认 convert POSIX → Windows 才让 jhyy 能 open file。
    for t in "${SYSV_TESTS[@]}"; do
        if ! (cd "$JHYY_ROOT" && "$JHYY_EXE" compile \
                --target=amd64_sysv_freestanding --no-link \
                "$JHYY_ROOT/compiler/tests/examples/${t}.jhyy" \
                -o "$JHYY_ROOT/compiler/tests/examples/${t}" > /tmp/sysv_stage1.log 2>&1); then
            echo "  $t: ❌ FAIL (Stage 1 jhyy compile — see /tmp/sysv_stage1.log)"
            cat /tmp/sysv_stage1.log
            RUN_FAIL=$((RUN_FAIL + 1))
            RUN_FAIL_LIST="$RUN_FAIL_LIST $t[stage1]"
            continue
        fi
    done

    # Stage 2: docker gcc:12 链 crt0.S + link.ld + N .s → N ELF → 跑 + check exit code
    DOCKER_OUT=$(cd "$JHYY_ROOT" && MSYS_NO_PATHCONV=1 "$DOCKER_BIN" run --rm \
        -v "$(pwd):/work" -w /work gcc:12 bash -c '
        for t in '"$(printf '%s ' "${SYSV_TESTS[@]}")"'; do
            gcc -nostdlib -static -T runtime/linux_elf/link.ld \
                -o /tmp/${t}.elf runtime/linux_elf/crt0.S compiler/tests/examples/${t}.s 2>/dev/null
            /tmp/${t}.elf
            echo "${t}=EXIT=$?"
        done
        ' 2>&1)
    DOCKER_RC=$?

    if [[ $DOCKER_RC -ne 0 ]]; then
        echo "  ❌ docker chain rc=$DOCKER_RC"
        echo "$DOCKER_OUT" | tail -10
        RUN_FAIL=$((RUN_FAIL + 1))
    else
        for t in "${SYSV_TESTS[@]}"; do
            ACTUAL=$(echo "$DOCKER_OUT" | grep "^${t}=EXIT=" | sed "s/^${t}=EXIT=//" | head -1)
            EXP=${EXPECTED[$t]}
            if [[ "$ACTUAL" == "$EXP" ]]; then
                echo "  $t: ✅ PASS (EXIT=$ACTUAL)"
                RUN_PASS=$((RUN_PASS + 1))
            else
                echo "  $t: ❌ FAIL (EXIT=$ACTUAL, expected $EXP)"
                RUN_FAIL=$((RUN_FAIL + 1))
                RUN_FAIL_LIST="$RUN_FAIL_LIST $t[stage2]"
            fi
        done
    fi

    echo "  Run $run: $RUN_PASS PASS / $RUN_FAIL FAIL"
    if [[ $RUN_FAIL -gt 0 ]]; then
        OVERALL_FAIL=$((OVERALL_FAIL + 1))
        echo "  Failed: $RUN_FAIL_LIST"
    else
        OVERALL_PASS=$((OVERALL_PASS + 1))
    fi
    echo
done

echo "=== sysv_full_regress.sh 结果: $OVERALL_PASS/$RUNS runs 全 ${#SYSV_TESTS[@]}/${#SYSV_TESTS[@]} PASS, $OVERALL_FAIL/$RUNS FAIL ==="
[[ $OVERALL_FAIL -eq 0 ]] && exit 0 || exit 1