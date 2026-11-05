#!/usr/bin/env bash
# artifact_fresh_check.sh — 「提交进仓的那份 jhyy.exe」对「现编出来的那份」的**行为**对拍
#
# 门要问的问题:**fresh clone 拿到的那份二进制,和当前源码编出来的那份,是同一个编译器吗?**
#
# 为什么比 `.s` 不比 `.exe`:
#   `.exe` = (源码 × 编译器 × **host gcc 版本**) 的函数 ⇒ 跨 toolchain 比必假阳性
#   (W-117 那条 TOOLCHAIN-DRIFT 就是拿 `.exe` 跨 toolchain 比出来的噪音 ——
#    ci.yml 的 build 步注释里已经写明「实测两次 make 同得 1eeb81b5,但 CI runner 的
#    gcc 16.2.0 与开发机的 15.2.0 必然产出不同字节」)。
#   `.s`  = (源码 × 编译器) 的函数 ⇒ 与 host gcc 无关 ⇒ 跨 toolchain 仍是判据。
#
# 门的边界(**别夸大它**):
#   · 它比的是**行为**,不是字节 ⇒ 任何 codegen 中性的源码改动它都看不见
#     (实测:W-117 修复前后那两个编译器编同一份 src0,产出逐字节相同)。
#   · 覆盖面 = src0 一个文件 ⇒ 编译器在别的语法上的差异它抓不到。
#     那是 regress 门的事(它测的是**当前源码**编出来的那份)。
#
# 为什么要抽成脚本(2026-11-05):这道判据原先只有 ci.yml 里的一段内联 shell。
# release job 自己那次 `make` 重建**从来没做过这道对拍** ⇒ 「唯一能抓工具链漂移的
# 门,在最该生效的那次构建上不存在」(2026-11-05 审计)。
# ⇒ 抽成一份实现,ci.yml 与 release.yml **都调它** —— 两套实现必然分叉
#   (Makefile 顶部记着 C 端/jhyy 端两套实现的旧账:W-127/128/129 就是分叉出来的)。
#
# 退出码:0 = PASS(行为一致),1 = FAIL(不一致),2 = 环境/用法错误
#
# 用法:artifact_fresh_check.sh [现编那份二进制路径]
#   默认现编那份 = compiler/build/bin/jhyy.exe
#   提交那份 = git show HEAD:compiler/build/bin/jhyy.exe(必须能取到 —— 这是 git 工作树)

set -uo pipefail

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BIN_REL="compiler/build/bin/jhyy.exe"
FRESH="${1:-$JHYY_ROOT/$BIN_REL}"
SRC="$JHYY_ROOT/compiler/src0/main.jhyy"

if [[ ! -f "$FRESH" ]]; then
    echo "artifact_fresh_check: 现编那份二进制不存在: $FRESH" >&2
    exit 2
fi
if [[ ! -f "$SRC" ]]; then
    echo "artifact_fresh_check: main.jhyy 不存在: $SRC" >&2
    exit 2
fi

# ── 提交进仓那份 ──────────────────────────────────────────────────────
# ⚠️ 必须从 git 对象里取,不能直接读工作树里的那个文件 ——
#   `make` 结束时会把新编出来的那份 `mv` 覆盖到 $BIN_REL 上
#   ⇒ 工作树里那个文件**已经是现编的那份**了,拿它比等于自己跟自己比。
if ! git -C "$JHYY_ROOT" rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "artifact_fresh_check: 没有 HEAD 可取(非 git 工作树?)—— 这道门需要 git 元数据" >&2
    exit 2
fi

WORK="$JHYY_ROOT/tmp/artifact_fresh_check.$$"
# ⚠️ 工作目录**必须在仓内** —— jhyy 用 `argv[0]` 推导 project root
# (放到 /tmp 会直接报 "cannot derive project root from argv[0]" 而编不了任何东西)。
mkdir -p "$WORK"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

COMMITTED="$WORK/committed.exe"
if ! git -C "$JHYY_ROOT" show "HEAD:$BIN_REL" > "$COMMITTED" 2>/dev/null; then
    echo "::error::仓里没有 $BIN_REL —— bootstrap 种子没了,fresh clone 无法自举" >&2
    exit 1
fi
chmod +x "$COMMITTED"

echo "=============================================================="
echo " artifact-fresh:提交产物 vs 现编产物(比 .s,不比 .exe)"
echo "=============================================================="
echo "  提交版 : $(sha256sum "$COMMITTED" | cut -c1-16)  ($COMMITTED)"
echo "  现编版 : $(sha256sum "$FRESH" | cut -c1-16)  ($FRESH)"
echo "  源码   : compiler/src0/main.jhyy"
echo

# ── 两份各自编 src0,比 .s ─────────────────────────────────────────────
# `! -s` 守卫是 W-086 那一类:编译器静默 exit 0 但不产 .s,那时 cmp 会因为
# 文件缺失而给出误导性的「不同」。
for who in committed fresh; do
    exe="$COMMITTED"; [ "$who" = fresh ] && exe="$FRESH"
    if ! timeout 300 "$exe" compile "$SRC" --no-link -o "$WORK/$who" >"$WORK/$who.log" 2>&1; then
        echo "::error::$who 版编译器编 src0 失败(见 $WORK/$who.log)" >&2
        tail -5 "$WORK/$who.log" >&2
        exit 1
    fi
    if [ ! -s "$WORK/$who.s" ]; then
        echo "::error::$who 版没产出 .s —— 门无法判定" >&2
        exit 1
    fi
    echo "  $who.s $(wc -c < "$WORK/$who.s") B  sha $(sha256sum "$WORK/$who.s" | cut -c1-16)"
done

echo
if cmp -s "$WORK/committed.s" "$WORK/fresh.s"; then
    echo "PASS — 提交产物对当前源码的行为与现编产物一致(fresh clone 的自举链是完整的)"
    exit 0
fi

echo "FAIL — 提交产物与现编产物对同一份 src0 的输出不同" >&2
echo "  ⇒ 提交进仓的那份编译器与现编出来的那份**行为不同**。" >&2
echo "  ⇒ 常见原因:换了 host gcc / 换了 runtime.c —— 编译器可能已经'变成另一个'" >&2
echo "    (W-117:工具链一换,编译器会静默变成另一个,而既有门照样全绿)。" >&2
echo "  差异行数: $(diff "$WORK/committed.s" "$WORK/fresh.s" 2>/dev/null | grep -c '^[<>]')" >&2
echo "  首个差异:" >&2
diff "$WORK/committed.s" "$WORK/fresh.s" 2>/dev/null | head -12 | sed 's/^/    /' >&2
exit 1
