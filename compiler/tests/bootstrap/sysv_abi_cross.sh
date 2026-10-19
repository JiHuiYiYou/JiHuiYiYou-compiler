#!/usr/bin/env bash
# sysv_abi_cross.sh — W-104 的跨实现 ABI 对拍(jhyy ↔ gcc)
#
# 目的:证明 jhyy 编译出来的 SysV 代码**能与 gcc 编译的代码互调**。
#
# 为什么必须有这个门:W-104 这类缺陷的特征是「自洽但不兼容」——
#
#   jhyy caller → jhyy callee  ✅(两者约定一致,所有现有测试都过)
#   jhyy caller → gcc  callee  ❌(约定不同 → 错开)
#
# 纯 jhyy 测试**永远看不到**这一类。实测 W-104 存在期间:
#   jhyy caller → gcc callee 退出码 **171**(正确应为 44)
#
# 而 locked 规范 `docs/abis/jhyy-abi-v1.0.0.md:872` 要求 SysV 的
# struct pass-by-value 遵循 SysV ABI —— 只有与真正的 SysV 实现对拍才能验这条。
#
# 用法: bash compiler/tests/bootstrap/sysv_abi_cross.sh <dir>
# 退出: 0 = ABI 一致;1 = 不一致;2 = 环境/输入不可用
#
# 前置(由调用方负责):
#   · <dir>/sysv_abi_caller.s —— jhyy 用 --target=amd64_sysv_freestanding 编出
#   · runtime/linux_elf/{crt0.S,link.ld}
#   · gcc 能编 SysV(本门在 ubuntu runner 上跑)

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || echo "$HERE/../../..")"
SRCDIR="${1:-}"
EXPECT=44

if [ -z "$SRCDIR" ] || [ ! -d "$SRCDIR" ]; then
    echo "ERR: 用法 $0 <dir>" >&2; exit 2
fi
if [ ! -f "$SRCDIR/sysv_abi_caller.s" ]; then
    echo "ERR: 缺 $SRCDIR/sysv_abi_caller.s" >&2; exit 2
fi
for f in runtime/linux_elf/crt0.S runtime/linux_elf/link.ld; do
    [ -f "$ROOT/$f" ] || { echo "ERR: 缺 $ROOT/$f" >&2; exit 2; }
done
command -v gcc >/dev/null || { echo "ERR: 没有 gcc" >&2; exit 2; }

echo "=== sysv_abi_cross.sh — jhyy ↔ gcc 的 SysV struct 传参对拍 ==="
echo "  root = $ROOT"
echo "  gcc  = $(gcc --version | head -1)"
echo "  期望退出码 = $EXPECT (41 + 3)"
echo

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# gcc 侧:按真正的 SysV ABI 接收 struct
cat > "$WORK/callee.c" <<'EOF'
struct Mixed { int i_field; double d_field; };
int gcc_take(struct Mixed m) { return m.i_field + (int)m.d_field; }
EOF

if ! gcc -O0 -c "$WORK/callee.c" -o "$WORK/callee.o" 2>"$WORK/cc.log"; then
    echo "ERR: gcc 编译 callee 失败:"; sed 's/^/    /' "$WORK/cc.log" | head -8; exit 2
fi

# 链接:jhyy 的 caller.s + gcc 的 callee.o + 自带的 crt0/link.ld
if ! gcc -nostdlib -static -T "$ROOT/runtime/linux_elf/link.ld" \
        -o "$WORK/abi.elf" "$ROOT/runtime/linux_elf/crt0.S" \
        "$SRCDIR/sysv_abi_caller.s" "$WORK/callee.o" 2>"$WORK/ld.log"; then
    echo "ERR: 链接失败:"; sed 's/^/    /' "$WORK/ld.log" | head -8; exit 2
fi

"$WORK/abi.elf"; rc=$?
echo
if [ "$rc" = "$EXPECT" ]; then
    echo "  ✅ 退出码 = $rc(期望 $EXPECT)—— jhyy 的 SysV struct 传参与 gcc 一致"
    exit 0
fi
echo "  ❌ 退出码 = $rc(期望 $EXPECT)—— jhyy 与 gcc 的 SysV struct 传参**不一致**"
echo "     (W-104 回归:struct 参数应按 eightbyte 分类传值,而不是整体退化成传指针)"
exit 1
