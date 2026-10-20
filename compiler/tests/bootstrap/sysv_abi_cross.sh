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
# ── 本门覆盖的三个用例 ──────────────────────────────────────────────────
#
#   ① small(≤16B)  jhyy → gcc   struct {i32, f64}  → 44
#      eightbyte 分类:INTEGER(rdi) + SSE(xmm0)
#
#   ② big(>16B)   jhyy → gcc   struct {i64,i64,i64} → 42
#      MEMORY class:整体拷到栈上,不占任何整数寄存器
#
#   ③ big(>16B)   gcc  → jhyy  struct {i64,i64,i64} → 42
#      callee 侧从 16(%rbp) 读栈上的那份拷贝
#
# 用法: bash compiler/tests/bootstrap/sysv_abi_cross.sh <dir>
# 退出: 0 = 全部一致;1 = 有不一致;2 = 环境/输入不可用
#
# 前置(由调用方负责):
#   · <dir>/sysv_abi_caller.s     —— jhyy 用 --target=amd64_sysv_freestanding 编出
#   · <dir>/sysv_abi_mem_caller.s —— 同上
#   · <dir>/sysv_abi_mem_callee.s —— 同上
#   · runtime/linux_elf/{crt0.S,link.ld}
#   · gcc 能编 SysV(本门在 ubuntu runner 上跑)

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null || echo "$HERE/../../..")"
SRCDIR="${1:-}"

if [ -z "$SRCDIR" ] || [ ! -d "$SRCDIR" ]; then
    echo "ERR: 用法 $0 <dir>" >&2; exit 2
fi
for f in sysv_abi_caller.s sysv_abi_mem_caller.s sysv_abi_mem_callee.s; do
    if [ ! -s "$SRCDIR/$f" ]; then
        echo "ERR: 缺(或为空) $SRCDIR/$f" >&2; exit 2
    fi
done
for f in runtime/linux_elf/crt0.S runtime/linux_elf/link.ld; do
    [ -f "$ROOT/$f" ] || { echo "ERR: 缺 $ROOT/$f" >&2; exit 2; }
done
command -v gcc >/dev/null || { echo "ERR: 没有 gcc" >&2; exit 2; }

echo "=== sysv_abi_cross.sh — jhyy ↔ gcc 的 SysV struct 传参对拍 ==="
echo "  root = $ROOT"
echo "  gcc  = $(gcc --version | head -1)"
echo

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# ── gcc 侧的三个实现 ────────────────────────────────────────────────────
#
# ① ≤16B struct:按真正的 SysV ABI 接收 —— INTEGER(rdi) + SSE(xmm0)。
#    gcc 生成的代码实测:movl %edi,%eax / movq %xmm0,%rdx
cat > "$WORK/callee_small.c" <<'EOF'
struct Mixed { int i_field; double d_field; };
int gcc_take(struct Mixed m) { return m.i_field + (int)m.d_field; }
EOF

# ② >16B struct:MEMORY class —— gcc 会把整份拷贝放在栈上。
cat > "$WORK/callee_big.c" <<'EOF'
struct Big { long a; long b; long c; };
int gcc_take_big(struct Big m) { return (int)(m.a + m.b + m.c); }
EOF

# ③ gcc 当 caller:调 jhyy 编译出来的 jhyy_take_big。
#    自己写 _start(SYS_exit=60),不链 crt0.S —— crt0 会去调 main_jhyy。
cat > "$WORK/caller_big.c" <<'EOF'
struct Big { long a; long b; long c; };
int jhyy_take_big(struct Big m);
static void sys_exit(int c) { __asm__ volatile("syscall" :: "a"(60), "D"(c)); }
void _start(void) {
    struct Big m; m.a = 10; m.b = 20; m.c = 12;
    sys_exit(jhyy_take_big(m));
}
EOF

for c in callee_small callee_big caller_big; do
    if ! gcc -O0 -c "$WORK/$c.c" -o "$WORK/$c.o" 2>"$WORK/$c.cc.log"; then
        echo "ERR: gcc 编译 $c.c 失败:"; sed 's/^/    /' "$WORK/$c.cc.log" | head -8; exit 2
    fi
done

PASS=0
FAIL=0

# run_case <名称> <期望退出码> <链接命令...>
run_case() {
    local name="$1"; shift
    local want="$1"; shift
    local elf="$WORK/$name.elf"
    if ! gcc -nostdlib -static -o "$elf" "$@" 2>"$WORK/$name.ld.log"; then
        echo "  ❌ $name 链接失败:"
        sed 's/^/       /' "$WORK/$name.ld.log" | grep -v "GNU-stack\|deprecated" | head -6
        FAIL=$((FAIL+1)); return
    fi
    "$elf"; local got=$?
    if [ "$got" = "$want" ]; then
        echo "  ✅ $name EXIT=$got(期望 $want)"
        PASS=$((PASS+1))
    else
        echo "  ❌ $name EXIT=$got(期望 $want)—— jhyy 与 gcc 的 SysV struct 传参**不一致**"
        FAIL=$((FAIL+1))
    fi
}

# ① ≤16B:jhyy caller + gcc callee(crt0 提供 _start → 调 main_jhyy)
run_case "small_jhyy_to_gcc" 44 \
    -T "$ROOT/runtime/linux_elf/link.ld" \
    "$ROOT/runtime/linux_elf/crt0.S" \
    "$SRCDIR/sysv_abi_caller.s" "$WORK/callee_small.o"

# ② >16B(MEMORY class):jhyy caller + gcc callee
run_case "big_jhyy_to_gcc" 42 \
    -T "$ROOT/runtime/linux_elf/link.ld" \
    "$ROOT/runtime/linux_elf/crt0.S" \
    "$SRCDIR/sysv_abi_mem_caller.s" "$WORK/callee_big.o"

# ③ >16B(MEMORY class):gcc caller + jhyy callee
#    不链 crt0.S —— gcc 侧自带 _start。
run_case "big_gcc_to_jhyy" 42 \
    "$WORK/caller_big.o" "$SRCDIR/sysv_abi_mem_callee.s"

echo
echo "=== sysv_abi_cross 结果: $PASS PASS / $FAIL FAIL ==="
if [ "$FAIL" -gt 0 ]; then
    echo "  (W-104 回归:SysV 的 struct 参数必须按 eightbyte(≤16B)或"
    echo "   MEMORY class(>16B)传值,而不是整体退化成传指针)"
    exit 1
fi
exit 0
