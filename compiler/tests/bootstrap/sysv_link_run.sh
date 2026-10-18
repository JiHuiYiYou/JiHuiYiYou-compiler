#!/usr/bin/env bash
# sysv_link_run.sh — SysV ABI 门的**第二段**:链 + 运行 + 判期望值
#
# 2026-10-18 建。与 sysv_full_regress.sh 的分工:
#   sysv_full_regress.sh   整条链,但要求 Windows 侧的 jhyy.exe + docker
#                          (只能在开发机上跑,GitHub windows-latest 没有
#                          Docker daemon —— 那正是 regress.py 的
#                          `--cross=auto` 在 CI 上探测失败、5 个 sysv 测试
#                          永远 SKIP 的原因)
#   本脚本                  只做「给一份 .s,链起来跑,比期望值」,
#                          纯 Linux + 原生 gcc,可以放在 ubuntu-latest 上
#
# 为什么值得拆成两个 job:那 5 个测试此前在 CI 上**根本没有门**。而
# W-104(SysV caller 侧分类错)与 W-116(SysV callee 只 spill 4 个寄存器)
# 都在待清零的 ACTIVE 名单里 —— 一个 ACTIVE 条目没有门,等于没登记。
#
# 输入:一个目录,里面有 `<name>.s`(由 windows 侧 jhyy.exe 用
#       `--target=amd64_sysv_freestanding --no-link` 编出)
#       以及对应的 `<name>.jhyy`(用于读 `// EXPECT: N`)
#
# 期望值从 .jhyy 读,不硬编码在本脚本里 —— 单一事实来源。W-116 的
# `sysv_abi_test` 退出 22 / 期望 28 之所以被放过,正是因为期望值只住在
# regress.py 里而 cross-env 那条路径拿不到。
#
# 用法: bash compiler/tests/bootstrap/sysv_link_run.sh <dir-with-.s>
# 退出: 0 = 全部匹配;1 = 有不匹配;2 = 环境/输入不可用

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JHYY_ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || echo "$HERE/../../..")"

CRT0="$JHYY_ROOT/runtime/linux_elf/crt0.S"
LINKLD="$JHYY_ROOT/runtime/linux_elf/link.ld"
SRCDIR="${1:-}"

if [ -z "$SRCDIR" ] || [ ! -d "$SRCDIR" ]; then
    echo "ERR: 用法 $0 <dir-with-.s>" >&2; exit 2
fi
if [ ! -f "$CRT0" ];  then echo "ERR: 缺 $CRT0" >&2; exit 2; fi
if [ ! -f "$LINKLD" ]; then echo "ERR: 缺 $LINKLD" >&2; exit 2; fi

echo "=== sysv_link_run.sh — SysV ABI 第二段(链 + 运行) ==="
echo "  root   = $JHYY_ROOT"
echo "  srcs   = $SRCDIR"
echo "  gcc    = $(gcc --version | head -1)"
echo

# 从 .jhyy 读 `// EXPECT: N`。取不到就**判失败**,不默认放过 ——
# 「跑起来就算过」正是 W-116 被放过一天的直接原因。
read_expect() {
    grep -m1 -oE '//[[:space:]]*EXPECT:[[:space:]]*[0-9]+' "$1" 2>/dev/null \
        | grep -oE '[0-9]+$' || true
}

PASS=0; FAIL=0; MISS=0
for s in "$SRCDIR"/*.s; do
    [ -f "$s" ] || continue
    name="$(basename "$s" .s)"
    jhyy="$SRCDIR/$name.jhyy"
    [ -f "$jhyy" ] || jhyy="$JHYY_ROOT/compiler/tests/examples/$name.jhyy"

    exp="$(read_expect "$jhyy")"
    if [ -z "$exp" ]; then
        printf "  ❌ %-24s 读不到 // EXPECT: —— 判失败(不默认放过)\n" "$name"
        FAIL=$((FAIL+1)); continue
    fi
    [ -s "$s" ] || { printf "  ❌ %-24s .s 为空\n" "$name"; FAIL=$((FAIL+1)); continue; }

    if ! gcc -nostdlib -static -T "$LINKLD" -o "/tmp/${name}.elf" \
         "$CRT0" "$s" > "/tmp/${name}.link.log" 2>&1; then
        printf "  ❌ %-24s 链接失败:\n" "$name"; sed 's/^/       /' "/tmp/${name}.link.log" | head -6
        FAIL=$((FAIL+1)); continue
    fi

    # ELF 的非 0 退出是预期(这些测试用退出码当断言),所以不能 set -e。
    "/tmp/${name}.elf"; act=$?
    if [ "$act" = "$exp" ]; then
        printf "  ✅ %-24s EXIT=%s (期望 %s)\n" "$name" "$act" "$exp"; PASS=$((PASS+1))
    else
        printf "  ❌ %-24s EXIT=%s 期望 %s\n" "$name" "$act" "$exp"; FAIL=$((FAIL+1))
    fi
done

if [ "$((PASS+FAIL))" -eq 0 ]; then
    echo; echo "  ❌ 一份 .s 都没找到 —— 输入目录不对,不能报绿"; exit 2
fi

echo
echo "=== sysv 结果: $PASS PASS / $FAIL FAIL ==="
if [ "$FAIL" -gt 0 ]; then exit 1; fi
echo "  ✅ 全部匹配 // EXPECT: —— SysV codegen 的这几条 ABI 契约成立"
exit 0
