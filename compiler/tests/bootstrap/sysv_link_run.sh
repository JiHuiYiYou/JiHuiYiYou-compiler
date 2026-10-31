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

# ════════════════════════════════════════════════════════════════════════════
# 已知失败登记:`<test>|<W-NNN>|<实际退出值的十进制串>`(签名之间是「或」)
# ════════════════════════════════════════════════════════════════════════════
#
# 为什么需要:这条门 2026-10-18 第一次真跑就抓到 W-116 —— `sysv_abi_test`
# 退出 22 / 期望 28。而这个 22-vs-28 在 `sysv_full_regress.sh` 的注释里
# **早就记着**,之所以一直隐形,是因为当时 cross-env 那条路径拿不到期望值,
# 只要 ELF 跑起来就报 PASS。门建起来之后它立刻现形 —— 这正是这道门要做的。
#
# 但 CI 不能从此常红:一个恒红的 job 会训练人忽略红色(2026-10-18 在
# artifact_checks.sh 上刚消灭过这个形态)。所以走同一套 expected-FAIL 模型:
#   退出值不匹配 + 落在登记里  → KNOWN-FAIL(绿),并在汇总里点名
#   退出值不匹配 + 不在登记里  → FAIL(红)   ← 新 bug 藏在旧 bug 后面
#   已登记却匹配上了            → UNEXPECTED-PASS(红) ← workaround 修好了没删登记
#   链失败 / .s 缺失 / EXPECT 读不到 → FAIL(红)  「没验到」不算「已知问题仍在位」
#
# W-116 转 RESOLVED 时删掉下面那一行,这条检查自动升级成真门。
# 2026-10-19:W-116 已修(callee 侧 SysV arg 寄存器分配),这一项**升级成真门** ——
# 登记表空了,任何 exit 不匹配现在都会红。W-116 当初正是靠「跑起来就算过」被放过
# 一天的;把登记清空才是防止它以别的形式复发的唯一办法。
declare -A KNOWN_FAIL=(
)

# 从 .jhyy 读 `// EXPECT: N`。取不到就**判失败**,不默认放过 ——
# 「跑起来就算过」正是 W-116 被放过一天的直接原因。
read_expect() {
    grep -m1 -oE '//[[:space:]]*EXPECT:[[:space:]]*[0-9]+' "$1" 2>/dev/null \
        | grep -oE '[0-9]+$' || true
}

PASS=0; FAIL=0; KNOWN=0
declare -a KNOWN_IDS=()
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
    reg="${KNOWN_FAIL[$name]:-}"

    if [ "$act" = "$exp" ]; then
        if [ -n "$reg" ]; then
            printf "  ❌ UNEXPECTED-PASS %-18s EXIT=%s 命中期望 —— [%s] 的登记该删了\n" "$name" "$act" "${reg%%|*}"
            FAIL=$((FAIL+1))
        else
            printf "  ✅ %-24s EXIT=%s (期望 %s)\n" "$name" "$act" "$exp"; PASS=$((PASS+1))
        fi
        continue
    fi

    # 不匹配 → 看是否落在登记里
    if [ -z "$reg" ]; then
        printf "  ❌ %-24s EXIT=%s 期望 %s\n" "$name" "$act" "$exp"
        echo "       (未登记 —— 要么是新 bug,要么是新测试忘了登记)"
        FAIL=$((FAIL+1)); continue
    fi
    wno="${reg%%|*}"; sigs="${reg#*|}"
    hit=0; sig=""
    local_ifs_save="${IFS-}"
    IFS='|'
    for sig in $sigs; do
        [ -n "$sig" ] || continue
        [ "$act" = "$sig" ] && { hit=1; break; }
    done
    IFS="$local_ifs_save"
    if [ "$hit" -eq 1 ]; then
        printf "  ⚠️  KNOWN-FAIL %-18s EXIT=%s 期望 %s [%s]\n" "$name" "$act" "$exp" "$wno"
        KNOWN=$((KNOWN+1)); KNOWN_IDS+=("$name($wno)")
    else
        printf "  ❌ %-24s EXIT=%s 期望 %s (签名不吻合)\n" "$name" "$act" "$exp"
        echo "       期望退出值之一: ${sigs//| 或 }   [登记于 $wno]"
        echo "       已登记的测试换了失败方式 —— 这是新 bug,不要被已知状态吞掉。"
        FAIL=$((FAIL+1))
    fi
done

if [ "$((PASS+FAIL+KNOWN))" -eq 0 ]; then
    echo; echo "  ❌ 一份 .s 都没找到 —— 输入目录不对,不能报绿"; exit 2
fi

echo
echo "=== sysv 结果: $PASS PASS / $KNOWN KNOWN-FAIL / $FAIL FAIL ==="
if [ "$KNOWN" -gt 0 ]; then
    echo "  在位的已知问题(见 docs/internal/workarounds.md):"
    for k in "${KNOWN_IDS[@]}"; do echo "    - $k"; done
fi
if [ "$FAIL" -gt 0 ]; then
    echo "  ❌ 红项说明见脚本头部:环境失败 / 未登记 / 签名不吻合 / UNEXPECTED-PASS"
    exit 1
fi
echo "  ✅ 无 FAIL、无 UNEXPECTED-PASS。已知问题的存在是预期状态,不计红。"
exit 0
