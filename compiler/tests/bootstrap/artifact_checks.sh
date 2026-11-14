#!/usr/bin/env bash
# artifact_checks.sh — 产物级门:验那些**不在程序返回值里**的失效模式
#
# 2026-10-15 建(v4.0.8)。为什么需要这份:
#
#   `compiler/tests/examples/*.jhyy` 无论怎么写都验不到下面这几条 —— 它们的
#   失效模式在**编译产物的字节布局**里,不在程序的返回值里。写 .jhyy 测试会 PASS。
#   今天已经实测过一次:per-fn 表 1024 上限(W-107)写「1100 函数 + 递归」会
#   **PASS**(结果全对、递归深度无变化),只有 .s 里 `subq $N, %rsp` 从 8368
#   跳到 96928 才看得出。
#
#   这类门跟 .jhyy 测试是**互补**关系,不是替代。
#
# 每条检查独立报告 PASS / FAIL,并在末尾给总判定。
# 新增检查时必须遵守 feedback_ci_gate_must_exercise_path:
#   **ship 前造红灯** —— 先证明它在 bug 存在时会 FAIL,再信它的 PASS。
#
# 用法:
#   bash compiler/tests/bootstrap/artifact_checks.sh              # 全部
#   bash compiler/tests/bootstrap/artifact_checks.sh --only=link_section
#
# 退出码:0 = 无 FAIL 且无 UNEXPECTED-PASS;1 = 有 FAIL;2 = 环境不可用
#
# ════════════════════════════════════════════════════════════════════════════
# 已知失败的登记(2026-10-18 重构)
# ════════════════════════════════════════════════════════════════════════════
#
# **为什么改。** 本脚本此前是「4 条已登记 ACTIVE → 必然全红 → CI 配
# `continue-on-error: true` 忽略」。CI 日志每轮固定打 `0 PASS / 4 FAIL`,
# 于是这个红在读日志的人眼里约等于不存在。一个恒红且被忽略的步骤比没有门更糟:
# 它训练人忽略红色(feedback_ci_gate_must_exercise_path)。
#
# **改成 expected-FAIL 模型。** 已知问题显式登记,登记与实际一致就是**绿的**;
# 红只留给「不该红的情况」。
#
# | 实际结果                          | 登记?      | 判定              |
# |-----------------------------------|-----------|-------------------|
# | 断言失败 + 签名吻合               | 有        | KNOWN-FAIL(绿)   |
# | 断言失败 + 签名**不**吻合         | 有        | FAIL(红)         |
# | 断言失败                          | 无        | FAIL(红)         |
# | 通过                              | 有        | UNEXPECTED-PASS(红)|
# | 通过                              | 无        | PASS(绿)          |
# | 环境/编译失败(badenv)             | —          | FAIL(红)          |
#
# 两条关键设计:
#
# 1) **带签名,不只带 W 号。** 只登记 W 号的话,一条已登记的 check 以**另一种
#    原因**失败会被当成「已知」吞掉 —— 那是一个新 bug 躲在旧 bug 后面。
#    签名不符一律翻红。
#
# 2) **UNEXPECTED-PASS 是红的。** 对应 regress 的 XPASS 语义
#    (feedback: 修好了必须有人看见)。workaround 修好后没人删登记,状态就永久
#    失真 —— 那正是 XFAIL 语义存在的理由。workaround 转 RESOLVED 时,删掉
#    `KNOWN_FAIL` 里对应那一行即可自动升级成真门,**不需要改 CI 配置**。
#
# 维护:新增 check 时,若它当前是红的,必须同时往 KNOWN_FAIL 加一行并写明签名。
#     加 check 不加登记 → 第一次跑就红(这是有意的)。

set -uo pipefail

JHYY_ROOT="${JHYY_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$JHYY_ROOT" || { echo "ERR: cd $JHYY_ROOT failed" >&2; exit 2; }

JHYY_EXE="${JHYY_EXE:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"
WORK="${WORK:-$JHYY_ROOT/compiler/build/bin/_artifact_checks}"
ONLY=""
SELFTEST=0

for arg in "$@"; do
    case "$arg" in
        --only=*)   ONLY="${arg#*=}" ;;
        --selftest) SELFTEST=1 ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

mkdir -p "$WORK"

PASS_N=0
FAIL_N=0
KNOWN_N=0
SKIP_N=0
declare -a FAILED=()
declare -a KNOWN=()
declare -a SKIPPED=()

# ════════════════════════════════════════════════════════════════════════════
# 已知失败登记表:`<check_id>|<W-NNN>|<签名1>[|<签名2>...]`
# 签名之间是「或」关系 —— 命中任一即视为已知失败。
# ════════════════════════════════════════════════════════════════════════════
#
# ⚠️ 这里每一行都对应 docs/internal/workarounds.md 里一条 **ACTIVE** 条目。
#    那条转 RESOLVED 时,**删掉这里对应的一行** —— check 会自动变成真门。
#    不要用「把签名改宽」的方式让它继续绿,那等于把新 bug 一起吞掉。
#
# 为什么 asm_before_ret 有两个签名:W-113 在 `check_asm_before_ret` 里有**两条**
# 失败路径,同一个 bug 的两种形态 ——
#   精确形态: cpuid 落在某函数体内、但在 ret 之后 → `BAD main_jhyy (cpuid@333 ret@332)`
#   退化形态: cpuid 不落在任何函数体内           → "没有任何函数体包含它"
# 两条都是「asm 字节落在 ret 之后,永不执行」。只登记其中一条会让另一条被误判成
# 新 bug(2026-10-18 实测踩到了:先只登记了退化形态,精确形态立刻翻红)。
declare -A KNOWN_FAIL=(
    # W-113 已修(2026-10-20,v4.0.18)—— asm 文本经 IL(`dbgasm <hex>`)内联进
    #   函数体,不再是「append 到 .s 末的死字节」⇒ 这一项升级成真门。
    # W-116 已修(2026-10-19),同一机制。
    #
    # W-223 已修(2026-11-09,v4.1.5)—— `#[naked]` 的**标签与函数体现在走同一条
    #   通道**(旁路文件 `_inline_asm.buf`)⇒ 两者相邻 ⇒ 产物里 `irq_entry` 的
    #   首指令就是 `iret` ⇒ 这一项升级成真门。
)

# 从 "link_section(.text.boot 已出现在产物里)" 里取出 "link_section"
_check_id() { printf '%s' "${1%%[ (]*}"; }

hdr()  { echo; echo "── $* ──────────────────────────────────────"; }

# ok <id+说明>
# 已登记却通过了 → UNEXPECTED-PASS,红(对应 regress 的 XPASS 语义)
ok() {
    local cid; cid=$(_check_id "$1")
    local w="${KNOWN_FAIL[$cid]:-}"
    if [ -n "$w" ]; then
        printf "  ❌ UNEXPECTED-PASS %s [%s]\n" "$cid" "${w%%|*}"
        echo "    ${1}"
        echo "    这条 check 对应的 workaround 看起来修好了 —— 但 KNOWN_FAIL 里的登记还在。"
        echo "    去 docs/internal/workarounds.md 确认状态,若是 RESOLVED 就删掉 KNOWN_FAIL 里"
        echo "    '${cid}' 那一行,check 会自动升级成真门。状态不失真是这一条存在的全部意义。"
        FAIL_N=$((FAIL_N+1)); FAILED+=("$cid(UNEXPECTED-PASS)")
    else
        printf "  ✅ PASS %s\n" "$1"; PASS_N=$((PASS_N+1))
    fi
}

# bad <id> <原因>  —— 断言失败(可能落在已知登记里)
bad() {
    local cid="$1" reason="$2"
    local w="${KNOWN_FAIL[$cid]:-}"
    if [ -z "$w" ]; then
        printf "  ❌ FAIL %s\n    %s\n" "$cid" "$reason"
        echo "    (未登记的失败 —— 要么是新 bug,要么是新加的 check 没在 KNOWN_FAIL 里登记)"
        FAIL_N=$((FAIL_N+1)); FAILED+=("$cid")
        return
    fi
    local wno="${w%%|*}" sigs="${w#*|}"
    local hit=0 sig
    local IFS='|'
    for sig in $sigs; do
        [[ -n "$sig" ]] || continue
        if [[ "$reason" == *"$sig"* ]]; then hit=1; break; fi
    done
    unset IFS
    if [ "$hit" -eq 1 ]; then
        printf "  ⚠️  KNOWN-FAIL %s [%s]\n    %s\n" "$cid" "$wno" "$reason"
        KNOWN_N=$((KNOWN_N+1)); KNOWN+=("$cid($wno)")
    else
        printf "  ❌ FAIL %s (签名不吻合)\n    实际:%s\n" "$cid" "$reason"
        printf "    期望包含以下之一: %s   [登记于 %s]\n" "${sigs//|/ 或 }" "$wno"
        echo "    已登记的 check 以**另一种原因**失败 —— 这是一个新 bug,不要被已知状态吞掉。"
        FAIL_N=$((FAIL_N+1)); FAILED+=("$cid(签名不吻合)")
    fi
}

# badenv <id> <原因> —— 环境/编译失败。**永远红**,不查登记:
# 「因为环境坏了所以没验到」不能算「已知问题仍在位」。
badenv() {
    printf "  ❌ FAIL %s (环境/编译失败)\n    %s\n" "$1" "$2"
    FAIL_N=$((FAIL_N+1)); FAILED+=("$1(env)")
}

# skip <id> <原因> —— 没跑成,什么都没验到。
#
# ⚠️ 2026-11-06 真修:**必须红**。
#   此前本函数只递增 SKIP_N,而退出码只看 FAIL_N ⇒ check 没跑成时脚本打印
#   「✅ 无 FAIL、无 UNEXPECTED-PASS。」并 exit 0 —— **门在什么都没验的状态下
#   报绿**。脚本自己的注释写着「不算绿」,行为却相反。
#   与 badenv 同义(环境/编译失败 ⇒ 什么都没验到 ⇒ 红),SKIP_N 只保留给
#   汇总里点名「哪几道没跑」;`FAILED` 的 "(env)" 标记正是红项表里列的
#   三种合法红来源之一。
#
#   可达性(实测,别照抄旧数字):真正**会触发**的只有 `objdump 不在 PATH`
#   那一条(check_asm_before_ret)—— 实测 objdump 缺失时该门 exit 0 并打印
#   「✅ 无 FAIL」,改后 exit 1。其余 15 处 `[ -x "$JHYY_EXE" ]` 守卫实际
#   不可达:脚本开头已用 `[ -f "$JHYY_EXE" ] || exit 2` 硬退出,且 MSYS2/NTFS
#   上 `-x` 对普通文件几乎恒真。留它们是冗余保险,本函数改成红**主要是**
#   为了「skip 这个概念本身不能再是绿的」。
skip() {
    printf "  ❌ FAIL %s (环境/编译失败,什么都没验到)\n    %s\n" "$1" "$2"
    SKIP_N=$((SKIP_N+1)); SKIPPED+=("$1")
    FAIL_N=$((FAIL_N+1)); FAILED+=("$1(env)")
}

# ════════════════════════════════════════════════════════════════════════════
# 7. W-107 / W-120 — 函数数 / temp id 越界时,编译器是否仍然产出**正确**的代码
# ════════════════════════════════════════════════════════════════════════════
#
# 两个悬崖,症状都是**静默产出错代码**:
#
#   · W-107:五张 per-fn 表按固定上限分配(256 → 1024 → 4096)→ 超出部分被
#     **丢弃** → 那些函数的 per_fn_max 保持 0 → 帧算成 8 字节 → 局部变量
#     **冲出帧** → 踩坏调用者的帧 → 被编译程序的 target 变成随机值。
#   · W-120:temp_slot_for_id 按固定 65536 分配 → temp id 越界时**静默**跳过
#     查表 → 落到 formula 兜底 → 同一个 temp 在「写」和「读」两处解析成
#     **不同的槽** → 值静默丢失。
#
# 为什么这个 check 必须是「产物级」的:两个悬崖的共同症状是
# **编译成功、链接成功、运行成功、结果是错的**。只看退出码的测试抓不到它
# —— 除非它恰好断言了那个值。所以这里断言**打印出来的和**。
#
# 用例:4100 个函数(> 旧的 4096 表长上限)。每个函数返回 9,main 求和
# → 期望 9 × 4100 = 36900。
# **这一个文件同时踩中两个悬崖**:4100 个函数 × ~16 个 temp ≈ 65600 > 65536
# → temp id 也越界 ✓(实测 4100 函数时最大 temp id = 65607)。
check_many_functions() {
    hdr "W-107/W-120  函数数 / temp id 越界时是否仍然产出正确的代码"
    [ -x "$JHYY_EXE" ] || { skip "many_functions" "jhyy.exe 不存在"; return; }

    local N=4100
    local i=0
    {
        echo 'extern fn printf(fmt: *u8, a: i32, b: i32) -> i32;'
        while [ "$i" -lt "$N" ]; do
            echo "fn f$i() -> i32 {"
            echo "    let mut x: i32 = 1;"
            echo "    let mut y: i32 = 2;"
            echo "    let mut z: i32 = x + y;"
            echo "    let mut w: i32 = z * 3;"
            echo "    return w;"
            echo "}"
            i=$((i+1))
        done
        echo 'fn main_jhyy() -> i32 {'
        echo '    let mut s: i32 = 0;'
        i=0
        while [ "$i" -lt "$N" ]; do
            echo "    s = s + f$i();"
            i=$((i+1))
        done
        echo '    printf("MANYFUNC %d\n" as *u8, s, 0);'
        echo '    return s;'
        echo '}'
    } > "$WORK/many.jhyy"

    if ! "$JHYY_EXE" compile "$WORK/many.jhyy" -o "$WORK/many" > "$WORK/many.log" 2>&1; then
        badenv "many_functions" "编译失败:$(tail -3 "$WORK/many.log" | tr '\n' ' ')"
        return
    fi
    if [ ! -x "$WORK/many.exe" ]; then
        badenv "many_functions" "编译成功但没产出 exe"
        return
    fi
    # ── 这道门必须真的踩中两个悬崖,否则它就是一道「永远绿」的门 ──
    #   · 函数数 4101 > 4032(旧 per-fn 表上限)→ 旧编译器在这里**编译失败**
    #   · max temp id > 65536(旧 temp 表上限)→ 旧编译器在这里**静默算错**
    # 第二个断言尤其重要:temp id 只差 71 就越界(实测 65607),合成文件的
    # 语句数一变就可能悄悄掉回 65536 以下 → 门变成空门而不报任何东西。
    local maxt
    maxt=$(grep -o '%t[0-9]*' "$WORK/many.s" 2>/dev/null | sed 's/%t//' | sort -n | tail -1)
    if [ -z "$maxt" ]; then
        badenv "many_functions" "产物 .s 里找不到 %tN —— 合成文件或产物异常"
        return
    fi
    if [ "$maxt" -le 65536 ]; then
        bad "many_functions" "合成文件的最大 temp id = $maxt(需要 > 65536)—— 这个用例**没有**踩到 W-120 的悬崖,门是空的"
        return
    fi
    local out want
    out=$("$WORK/many.exe" 2>/dev/null | tr -d '\r')
    want=$((9 * N))
    if [ "$out" != "MANYFUNC $want" ]; then
        bad "many_functions" "求和 = '$out'(期望 MANYFUNC $want)—— 越界的函数/temp 拿到了错误的槽(W-107/W-120 未修)"
        return
    fi
    ok "many_functions($N 个函数求和 = $want ✓)"
}

# ════════════════════════════════════════════════════════════════════════════
# 1. W-112 — `#[link_section(".x")]` 必须真的产生一个 .section 指令
# ════════════════════════════════════════════════════════════════════════════
#
# 症状:`#[link_section]` 被 parser 认、codegen 收了,但生成的 .s 里**一个
# `.section` 指令都没有** —— `codegen.jhyy:4478-4485` 写
# `obj/_section_directive.buf` 的那条链是断的(buf 实测 0 字节)。
# `link_section_boot.jhyy` 这个 V3-B 3e 的 ship gate 一直空转,因为它只断言
# `_start()` 返回 42 —— 那个值跟 section 归属毫无关系。

check_link_section() {
    hdr "W-112  #[link_section] 是否产生 .section 指令"
    [ -x "$JHYY_EXE" ] || { skip "link_section" "jhyy.exe 不存在"; return; }

    cat > "$WORK/ls.jhyy" <<'EOF'
#[link_section(".text.boot")]
fn _start() -> i32 { return 42; }
fn main_jhyy() -> i32 { return _start(); }
EOF

    if ! "$JHYY_EXE" compile --target=amd64_win --no-link "$WORK/ls.jhyy" \
            -o "$WORK/ls" > "$WORK/ls.log" 2>&1; then
        badenv "link_section" "编译失败:$(tail -3 "$WORK/ls.log" | tr '\n' ' ')"
        return
    fi

    # 注意:`grep -c` 无匹配时输出 0 但退出码为 1,`|| echo 0` 会拼成两行 0(第一版
    # 就栽在这,报了个假的高段错误)。
    local nsect
    nsect=$(grep -cE '^[[:space:]]*\.section' "$WORK/ls.s" 2>/dev/null || true)
    nsect=${nsect:-0}
    if [ "$nsect" -eq 0 ]; then
        bad "link_section" "生成的 .s 里 0 条 .section 指令 —— 属性是 no-op(W-112 未修)"
        return
    fi
    if ! grep -qE '\.section[[:space:]]+\.text\.boot' "$WORK/ls.s"; then
        bad "link_section" "有 $nsect 条 .section,但没有 .text.boot —— 属性名没生效"
        return
    fi
    ok "link_section(.text.boot 已出现在产物里)"
}

# ════════════════════════════════════════════════════════════════════════════
# 1b. W-170 — `jhyy build` 必须与 `jhyy compile --no-link` 产出**逐字节相同**的 .s
# ════════════════════════════════════════════════════════════════════════════
#
# 症状(2026-10-30 实测,修前):`jhyy build` 产出的 .s 里**一条 .section 都没有**
# —— `#[link_section(".text.boot")]` 在 build 路径上完全失效且**零告警**
# (W-112 于 2026-10-20 修好了 compile 路径,漏了 build 路径)。
#
# 为什么是「逐字节比」而不是「grep .section」:
#   ① 只 grep build 侧 ⇒ compile 侧被动过(丢了 .section)时门不会红
#      —— 现有 check_link_section 覆盖那一侧,但它不在同一道门里。
#   ② 两侧**各自独立**断言(.section 在 + 归属 _start)⇒ **两侧同时退化也红**。
#   ③ 再加「两侧 .s 逐字节相同」⇒ 任何**残留**差异都红。
#      (两条路径的 codegen 输入逐字节相同:同一个 build_il / 同一块 IR buffer /
#       同一个 target / .s 里不嵌任何路径 ⇒ 产物必须逐字节相同)
#
# ⚠️ 覆盖面:只覆盖 in-mem 路径(四个 target 全是 BACKEND_SELF,正常路径恒走它)。
#    fallback(in-mem 后端失败 ⇒ build_il 只落 .il、**不产 .s**)不覆盖 ——
#    那是 W-170 之外的另一个缺口(W-171)。
check_link_section_build() {
    hdr "W-170  jhyy build 与 compile --no-link 的 .s 是否逐字节相同(含 #[link_section])"
    [ -x "$JHYY_EXE" ] || { skip "link_section_build" "jhyy.exe 不存在"; return; }

    local src="$WORK/lsb.jhyy"
    local b="$WORK/lsb_b"      # build 产物(无扩展名 ⇒ .s 落在它旁边)
    local c="$WORK/lsb_c"      # compile --no-link 产物
    cat > "$src" <<'EOF'
#[link_section(".text.boot")]
fn _start() -> i32 { return 42; }
fn main_jhyy() -> i32 { return _start(); }
EOF

    # ⚠️ 先删干净:上一轮的陈旧 .s 绝不能被当成本轮产物
    # (W-086 那类「编译器静默 exit 0 但不产 .s」的假阳性)。
    rm -f "$WORK/lsb_b.s" "$WORK/lsb_c.s" "$WORK/lsb_b.il" "$WORK/lsb_c.il"

    if ! "$JHYY_EXE" build --target=amd64_win "$src" -o "$b" > "$WORK/lsb_b.log" 2>&1; then
        badenv "link_section_build" "build 失败:$(tail -3 "$WORK/lsb_b.log" | tr '\n' ' ')"
        return
    fi
    if ! "$JHYY_EXE" compile --target=amd64_win --no-link "$src" -o "$c" > "$WORK/lsb_c.log" 2>&1; then
        badenv "link_section_build" "compile --no-link 失败:$(tail -3 "$WORK/lsb_c.log" | tr '\n' ' ')"
        return
    fi
    if [ ! -s "$WORK/lsb_b.s" ]; then
        badenv "link_section_build" "build 没产出 .s(lsb_b.s 不存在或为空)"
        return
    fi
    if [ ! -s "$WORK/lsb_c.s" ]; then
        badenv "link_section_build" "compile --no-link 没产出 .s(lsb_c.s 不存在或为空)"
        return
    fi

    # ── 断言 1(两侧**各自独立**):.section .text.boot 必须在,且归属 _start ──
    #
    # 「归属 _start」用 awk 看**紧随 .section 之后的第一个 .globl 行** ——
    # 只 grep `.section` 会漏掉「section 贴到别的函数上」这种错位。
    local side f nsec owner
    for side in b c; do
        f="$WORK/lsb_$side.s"
        # 注意:`grep -c` 无匹配时输出 0 但退出码为 1,`|| echo 0` 会拼成两行 0
        # (第一版就栽在这)。用 `|| true`。
        nsec=$(grep -cE '^[[:space:]]*\.section' "$f" 2>/dev/null || true)
        nsec=${nsec:-0}
        if [ "$nsec" -eq 0 ]; then
            bad "link_section_build" "$side 侧的 .s 里 0 条 .section 指令 —— #[link_section] 是 no-op(b 侧=W-170 未修 / c 侧=W-112 回归)"
            return
        fi
        if ! grep -qE '\.section[[:space:]]+\.text\.boot' "$f"; then
            bad "link_section_build" "$side 侧有 $nsec 条 .section,但没有 .text.boot —— 属性名没生效"
            return
        fi
        owner=$(awk '
            /^[[:space:]]*\.section[[:space:]]+\.text\.boot/ { want = 1; next }
            want && /^[[:space:]]*\.globl/ { print $2; exit }
        ' "$f")
        if [ "$owner" != "_start" ]; then
            bad "link_section_build" "$side 侧 .section .text.boot 归属的函数是 '$owner'(期望 _start)—— section 贴错函数了"
            return
        fi
    done

    # ── 断言 2(最强):两条路径的 .s 必须**逐字节相同** ──
    if ! cmp -s "$WORK/lsb_b.s" "$WORK/lsb_c.s"; then
        bad "link_section_build" "build 的 .s 与 compile --no-link 的 .s **不逐字节相同** —— 两条路径仍有差异:$(diff "$WORK/lsb_b.s" "$WORK/lsb_c.s" 2>/dev/null | head -4 | tr '\n' ' ')"
        return
    fi

    ok "link_section_build(build ≡ compile --no-link,逐字节相同,含 .section .text.boot)"
}

# ════════════════════════════════════════════════════════════════════════════
# 2. W-113 — asm!/fence 的字节必须落在 `ret` 之前
# ════════════════════════════════════════════════════════════════════════════
#
# 症状:`inline_asm_cpuid` 的 `cpuid`(0f a2)确实进了 exe,但落在
# `main_jhyy` 的 **ret 之后**,永不执行。所以那两个 ship gate 的退出码对
# asm 内容零敏感 —— 把整个 asm 删掉照样 PASS。
#
# 验法:在生成物里找 `ret`,比较 asm 特征字节相对它的位置。**只看「emit 了」
# 是不够的**(现有测试就是栽在这)。

check_asm_before_ret() {
    hdr "W-113  asm!/fence 字节是否在 ret 之前"
    [ -x "$JHYY_EXE" ] || { skip "asm_before_ret" "jhyy.exe 不存在"; return; }
    command -v objdump >/dev/null || { skip "asm_before_ret" "objdump 不在 PATH"; return; }

    local f="$WORK/asm.jhyy"
    cat > "$f" <<'EOF'
fn with_asm() -> i32 { asm!("cpuid"); return 1; }
fn main_jhyy() -> i32 { return with_asm(); }
EOF
    # 必须**链接出 .exe**:asm 字节不进 .s(第一版去 grep .s 里的 `cpuid` 找不到,
    # 因为 .s 里只有外层的拼接痕迹,真正的 cpuid 指令要到 .exe 的反汇编里才看得到)。
    if ! "$JHYY_EXE" compile --target=amd64_win "$f" -o "$WORK/asm" \
            > "$WORK/asm.log" 2>&1; then
        badenv "asm_before_ret" "编译失败:$(tail -3 "$WORK/asm.log" | tr '\n' ' ')"
        return
    fi
    local exe; exe=$(cygpath -w "$WORK/asm.exe" 2>/dev/null || echo "$WORK/asm.exe")
    [ -f "$exe" ] || { badenv "asm_before_ret" "没产出 .exe"; return; }

    local dis
    dis=$(objdump -d "$exe" 2>/dev/null)
    grep -qi 'cpuid' <<< "$dis" || { bad "asm_before_ret" "反汇编里找不到 cpuid —— asm 根本没 emit"; return; }

    # 判定:cpuid 必须落在**某个函数体内部**,且在该函数的 ret 之前。
    #
    # 症状实测(objdump -d)—— 注意 cpuid 前面**根本没有函数头**:
    #     ...: 5d      pop  %rbp
    #     ...: c3      ret        ← 上一个函数在此返回
    #     ...: 0f a2   cpuid      ← 没有任何函数头包着它
    #     ...: 90      nop
    # 也就是说 asm 被 emit 在**所有函数之外**,是死字节。所以「找不到含 cpuid 的
    # 函数体」本身就是结论,不是「无法判定」。
    #
    # objdump 每行格式 `addr:\tbytes...\tmnemonic operands`,助记符列随字节数变
    # (2 或 3 字节指令),不能取固定列 —— 按文本匹配。
    local verdict
    verdict=$(awk '
        /^[0-9a-f]+ <[^>]*>:/ { fname=$2; gsub(/[<>:]/,"",fname); cpu=-1; rp=-1; next }
        /cpuid/   { if (fname != "" && cpu < 0) cpu = NR }
        /\tret/   { if (fname != "" && rp  < 0) rp  = NR }
        fname != "" && cpu > 0 && rp > 0 {
            if (cpu < rp) print "OK " fname
            else          print "BAD " fname " (cpuid@" cpu " ret@" rp ")"
            fname=""
        }
        END { if (fname != "" && cpu > 0 && rp <= 0) print "BAD " fname " (有 cpuid 但无 ret)" }
    ' <<< "$dis")

    if [ -z "$verdict" ]; then
        local outside
        outside=$(grep -c 'cpuid' <<< "$dis")
        bad "asm_before_ret" "反汇编里有 $outside 条 cpuid,但**没有任何函数体包含它** —— asm 被 emit 在所有函数之外,是死字节(W-113 未修)"
        return
    fi
    if grep -q '^BAD' <<< "$verdict"; then
        bad "asm_before_ret" "$(grep '^BAD' <<< "$verdict" | head -3 | tr '\n' ' ')"
        return
    fi
    ok "asm_before_ret(asm 字节都在某个函数体的 ret 之前)"
}

# ════════════════════════════════════════════════════════════════════════════
# 3b. W-223 — `#[naked]` 的**标签与函数体**必须落在同一处
# ════════════════════════════════════════════════════════════════════════════
#
# 症状(2026-11-09 实测,v4.1.4):`#[naked] fn irq_entry() { asm!("iret"); }`
#   ① 最终 exe 里 **`irq_entry` 符号存在**(`.globl` + 标签进了产物);
#   ② 但它的**首指令是一串 `nop` 填充,不是 `iret`**;
#   ③ 那串 `iret` 字节落在 **`.text` 段的最开头**(所有函数之外)。
#   ⇒ 标签与函数体**永不相遇**:跳进 irq_entry 只会执行一串 nop,不会 iret。
#
# 根因(W-113 的修复边界没覆盖到 naked 路径 —— 两个通道分家了):
#   · **头**(`.globl irq_entry` + `irq_entry:`)仍写进旁路文件 `_inline_asm.buf`
#     —— `compiler/src0/abi_amd64_win.jhyy` 的 `emit_naked_func_header`;
#   · **体**(`asm!` 的字节)自 W-113(2026-10-20,v4.0.18)起走 IL(`dbgasm <hex>`)
#     —— `compiler/src0/codegen.jhyy` 的 NODE_ASM_BLOCK 分支;
#   · 而 naked 函数**不 emit QBE IR** ⇒ 那条 `dbgasm` 落在 IL 的**顶层**
#     ⇒ 后端把它写在 .text 段开头(所有函数之外);
#   · 链接时旁路文件被拼到 .s **末尾**(`main.jhyy` 的 `link_with_gcc`)
#     ⇒ 标签在文件尾、函数体在文件头 ⇒ 两者永不相遇。
#
# ⚠️ 为什么这道门不能省:
#   · `compiler/tests/examples/naked_interrupt_entry.jhyy` 只断言 `EXPECT: 0`
#     (main_jhyy 的退出码)⇒ 裸中断入口整个坏掉,它照样 PASS(它自己的注释就写了
#     「哪怕 codegen 明天给它套上完整 prologue,这个测试照样 PASS」)。
#   · `asm_before_ret` 那道门只覆盖 **hosted** 函数的 inline asm ⇒ 也不覆盖 naked。
#   ⇒ 两道门都绿着,而 naked 入口是坏的 —— 这类「测的是副本 / 测的不是这一条」
#     的覆盖缺口,只有产物级的门才抓得到。
#
# ⚠️ 隔离说明:本 check 只验「标签与函数体在一起」,**不**验旁路文件能不能写
#   (那是 W-224 的面)⇒ 仍然把 `compiler/build/obj/` 建出来,让两个面互不污染。
#   (W-224 已修 ⇒ 旁路文件现在落在 OS 临时目录;这一步只是保险。)
check_naked_symbol() {
    hdr "W-223  #[naked] 函数的标签与函数体必须在一起"
    [ -x "$JHYY_EXE" ] || { skip "naked_symbol" "jhyy.exe 不存在"; return; }
    command -v objdump >/dev/null || { skip "naked_symbol" "objdump 不在 PATH"; return; }
    mkdir -p "$JHYY_ROOT/compiler/build/obj" 2>/dev/null || {
        badenv "naked_symbol" "建不出 compiler/build/obj/"; return; }

    local f="$WORK/naked.jhyy"
    cat > "$f" <<'EOF'
#[naked]
fn irq_entry() {
    asm!("iret");
}
fn main_jhyy() -> i32 { return 0 as i32; }
EOF
    if ! "$JHYY_EXE" compile "$f" -o "$WORK/naked" > "$WORK/naked.log" 2>&1; then
        badenv "naked_symbol" "编译失败:$(tail -3 "$WORK/naked.log" | tr '\n' ' ')"
        return
    fi
    local exe; exe=$(cygpath -w "$WORK/naked.exe" 2>/dev/null || echo "$WORK/naked.exe")
    [ -f "$exe" ] || { badenv "naked_symbol" "没产出 .exe"; return; }

    local dis
    dis=$(objdump -d "$exe" 2>/dev/null)

    # ① 符号在不在(.globl + 标签进了最终产物没有)
    if ! grep -q '<irq_entry>:' <<< "$dis"; then
        bad "naked_symbol" "产物里没有 irq_entry 符号 —— naked 函数的 .globl/标签没进最终 exe"
        return
    fi

    # ② 标签处的**第一条指令**必须就是函数体
    # objdump 每行格式 `addr:\tbytes...\tmnemonic operands` —— 助记符列随字节数
    # 变(1 或 2 字节指令),按文本取第 3 列。
    local first
    first=$(awk '/<irq_entry>:/ {f=1; next} f && /^ *[0-9a-f]+:/ {print $3; exit}' <<< "$dis")
    if [ "$first" != "iret" ]; then
        bad "naked_symbol" "irq_entry 的首指令不是 iret(实际是 ${first:-?})—— 函数体与标签分离(W-223 已修,这里又红了 ⇒ 回归了)"
        return
    fi

    # ③ 函数体不许还有一份游离在所有函数之外
    local nret
    nret=$(grep -c 'iret' <<< "$dis")
    if [ "$nret" -gt 1 ]; then
        bad "naked_symbol" "反汇编里有 $nret 条 iret —— 函数体还有一份落在函数之外"
        return
    fi

    ok "naked_symbol(irq_entry 符号存在,首指令就是 iret ✓)"
}

# ════════════════════════════════════════════════════════════════════════════
# W-224 (2026-11-09 真修):旁路文件(side-file)的路径**不能相对 CWD**
# ════════════════════════════════════════════════════════════════════════════
#
# 为什么这道门必须**换 CWD** 跑:
#   W-224 那条 bug 的形态是「**只在某些目录里**发作」——
#   编译器在仓库根目录跑(所有现有门都在那儿跑)⇒ `compiler/build/obj/`
#   恰好存在 ⇒ 旁路文件写得出 ⇒ **门全绿**。
#   而真实的用户场景恰恰是「在自己项目目录里编译」⇒ 那个目录**没有**
#   `compiler/build/obj/` ⇒ 写侧静默失败 ⇒ 两种后果:
#     ① `#[no_std]` 的 `_no_std.flag` 没写出来 ⇒ 链成 hosted ⇒ hosted
#        `runtime.c` 的 `main` 跟用户的 `fn main` 撞名 ⇒ **链接失败**;
#     ② `#[naked]` 的 `.globl` + 标签**整个丢失** ⇒ 产物里没有那个符号。
#   ⇒ 这道门在一个**没有** `compiler/build/obj/` 的临时目录里跑编译器。
#
# 门验两件事(都是 W-224 的两条症状):
#   ① `#[no_std]` 程序在任意目录里都能链出来,跑起来退出码 42;
#   ② `#[naked]` 函数的标签不会因为「写不进去」而整个丢失。
#
# 修复前:①链接失败 ②产物里没有 irq_entry 符号 ⇒ 两件都红。
check_no_std_any_cwd() {
    hdr "W-224  旁路文件不能相对 CWD —— 在任意目录里都要编得出"
    [ -x "$JHYY_EXE" ] || { skip "no_std_any_cwd" "jhyy.exe 不存在"; return; }
    command -v objdump >/dev/null || { skip "no_std_any_cwd" "objdump 不在 PATH"; return; }

    # 临时「项目目录」—— **没有** compiler/build/obj/ ⇒ 相对路径的旧实现在这儿必然失败。
    local proj="$WORK/proj_any_cwd"
    rm -rf "$proj" 2>/dev/null
    mkdir -p "$proj" || { badenv "no_std_any_cwd" "建不出临时项目目录"; return; }

    # ① #[no_std] 程序 —— 链接行由旁路文件(_no_std.flag)决定。
    cat > "$proj/prog.jhyy" <<'EOF'
#[no_std]
fn main() -> i32 {
    let a: i32 = 20;
    let b: i32 = 22;
    return a + b;
}
EOF
    local out rc exe
    out=$(cd "$proj" && "$JHYY_EXE" compile prog.jhyy -o prog.exe 2>&1)
    rc=$?
    if [ "$rc" != "0" ]; then
        bad "no_std_any_cwd" "在**没有** compiler/build/obj/ 的目录里编 #[no_std] 程序失败(退出码 $rc)—— 旁路文件路径仍相对 CWD ⇒ 走了 hosted 链接行。gcc 报错:$(printf '%s' "$out" | tail -2 | tr '\n' ' ')"
        return
    fi
    exe=$(cygpath -w "$proj/prog.exe" 2>/dev/null || echo "$proj/prog.exe")
    [ -f "$exe" ] || { badenv "no_std_any_cwd" "没产出 prog.exe"; return; }
    "$exe" >/dev/null 2>&1
    local prc=$?
    if [ "$prc" != "42" ]; then
        bad "no_std_any_cwd" "no_std 程序跑出来的退出码是 $prc(期望 42)"
        return
    fi

    # ② #[naked] 函数的标签 —— 写侧失败 ⇒ `.globl` + 标签整个丢失。
    cat > "$proj/naked.jhyy" <<'EOF'
#[naked]
fn irq_entry() {
    asm!("iret");
}
fn main_jhyy() -> i32 { return 0 as i32; }
EOF
    out=$(cd "$proj" && "$JHYY_EXE" compile naked.jhyy -o naked.exe 2>&1)
    rc=$?
    if [ "$rc" != "0" ]; then
        bad "no_std_any_cwd" "在项目目录里编 #[naked] 函数失败(退出码 $rc):$(printf '%s' "$out" | tail -2 | tr '\n' ' ')"
        return
    fi
    exe=$(cygpath -w "$proj/naked.exe" 2>/dev/null || echo "$proj/naked.exe")
    [ -f "$exe" ] || { badenv "no_std_any_cwd" "没产出 naked.exe"; return; }
    # ⚠️ **先收再匹配**,不要 `objdump | grep -q`:脚本开着 `set -o pipefail` ⇒
    #   `grep -q` 一命中就退出 ⇒ objdump 收到 SIGPIPE(141)⇒ 管道状态非零 ⇒
    #   `if !` 判成「没找到」—— 明明符号就在那儿!(2026-11-09 实测踩到)
    local dis
    dis=$(objdump -d "$exe" 2>/dev/null)
    if ! grep -q '<irq_entry>:' <<< "$dis"; then
        bad "no_std_any_cwd" "产物里没有 irq_entry 符号 —— naked 的标签在项目目录里被整个写丢了"
        return
    fi

    ok "no_std_any_cwd(任意目录里 #[no_std] 链得出且退出码 42 ✓ · #[naked] 的标签也在 ✓)"
}

# ════════════════════════════════════════════════════════════════════════════
# 3. W-107 — per-fn 表 1024 上限:高索引函数的帧不应比低索引大一个量级
# ════════════════════════════════════════════════════════════════════════════
#
# 症状:五个 per-fn pre-scan 表硬编码 1024。越过之后 emit_func_header 的
# `use_per_fn` 判据失败,静默退回 legacy 全局 max 帧路径。
# 实测(1100 函数模块):f0–f1022 帧 8368 字节,**f1023+ 帧 96928 字节**。
#
# 这个失效模式**不会算错、也不会砍递归深度**(虚预留不提交页),所以任何
# .jhyy 测试都验不到 —— 只能量 .s。

check_per_fn_frame() {
    hdr "W-107  per-fn 表 1024 上限后的帧大小"
    [ -x "$JHYY_EXE" ] || { skip "per_fn_frame" "jhyy.exe 不存在"; return; }

    local N=1100 f="$WORK/fn.jhyy"
    python - "$N" "$f" <<'PY'
import sys
N, out = int(sys.argv[1]), sys.argv[2]
L = [f"fn f{i}(a: i32) -> i32 {{ return a * 3; }}" for i in range(N)]
L += ["fn main_jhyy() -> i32 {", "    let mut r: i32 = 0;"]
for i in range(N):
    L.append(f"    r = f{i}({i}); if r != {i*3} {{ return 900 + {i}; }}")
L += ["    return 0;", "}"]
open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
PY
    [ -f "$f" ] || { badenv "per_fn_frame" "生成测试模块失败"; return; }

    if ! "$JHYY_EXE" compile --target=amd64_win --no-link "$f" -o "$WORK/fn" \
            > "$WORK/fn.log" 2>&1; then
        badenv "per_fn_frame" "编译失败:$(tail -3 "$WORK/fn.log" | tr '\n' ' ')"
        return
    fi

    # 先取那一行,再用 grep -o 抽数字 —— 早先用 substr(RSTART+6, RLENGTH-13)
    # 把 8368 截成 836(尾部 `, %rsp` 是 6 字符,不是 7)。
    local low high ratio
    low=$(awk '/^f500:/{f=1} f && /subq \$[0-9]+, %rsp/{print; exit}' "$WORK/fn.s" | grep -oE '[0-9]+' | head -1)
    high=$(awk '/^f1099:/{f=1} f && /subq \$[0-9]+, %rsp/{print; exit}' "$WORK/fn.s" | grep -oE '[0-9]+' | head -1)
    [ -n "$low" ] && [ -n "$high" ] || { badenv "per_fn_frame" "量不到帧大小(low='$low' high='$high')"; return; }

    ratio=$(( high / (low > 0 ? low : 1) ))
    if [ "$ratio" -ge 4 ]; then
        bad "per_fn_frame" "f500 帧 ${low}B vs f1099 帧 ${high}B —— ${ratio}× 膨胀(1024 上限已触发)"
        return
    fi
    ok "per_fn_frame(f500=${low}B / f1099=${high}B,比值 ${ratio}×)"
}

# ════════════════════════════════════════════════════════════════════════════
# v4.2.1 — 帧尺寸:alloc 池预留从「写死 8192」改成「按函数实际需要」
# ════════════════════════════════════════════════════════════════════════════
#
# 背景(2026-10-29 实测,不是判断):
#   `codegen_amd64_emit_ctrl.jhyy` 的 alloc_pool_size = 8192 + per_fn_alloc
#   ⇒ **每个函数的帧 ≥8352 字节**,与该函数实际用几个 temp 无关
#     (一个只用一个 temp 的函数也照样拿 8KB 栈)
#   ⇒ 帧 > 4096 ⇒ Windows x64 ABI 要求探页 ⇒ **每个函数每次调用都走一次
#      ___chkstk_ms**(实测自举产物 1045 个函数 **100%** 如此)
#   ⇒ 实测 **~41% 的运行时**在这上面(消融:8384 帧 + chkstk = 335ms →
#     128 帧无 chkstk = 197ms;gcc -O0 = 98ms)
#
# 两条门:
#   G1 check_frame_bloat —— 帧不许大 + chkstk 次数必须为 0(**收益锁**)
#   G2 check_frame_slots —— 每个 rbp 相对槽位必须落在该函数的帧内
#                           (**安全网**:帧算小了,槽位越界就踩坏调用者的栈)
#
# ⚠️ G2 在修之前就该是**绿的**(帧本来就大)—— 它的作用不是「证明这次修好了」,
#    是「将来谁再把预留算小,当场响」。G1 才是这次修好的证据。

# _frame_stats <file.s> — 输出 "maxframe chkstk nviol [viol 细节]"
#
# 帧的识别:**函数序言里 pushq %rbp 之后的第一个** `subq $N, %rsp`。
# 函数体里 call 之前的 `subq $32, %rsp` 是**出参区**,不是帧 —— 两者形态完全
# 一样(`subq $N, %rsp`),只能靠「前面有没有 pushq %rbp」区分。
_frame_stats() {
    python - "$1" <<'PY'
import re, sys
lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().split("\n")
fn_re = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):\s*$')
slot_re = re.compile(r'-(\d+)\(%rbp\)')
frame = 0            # 当前函数的预留帧;0 = 还没量到
in_prologue = False
maxframe = 0
chk = 0
viol = 0
detail = []
for l in lines:
    s = l.strip()
    if fn_re.match(l.rstrip()):
        frame = 0
        in_prologue = False
        continue
    if s == "pushq %rbp":
        in_prologue = True
        continue
    m = re.match(r'subq \$(\d+), %rsp$', s)
    if m:
        if in_prologue:
            frame = int(m.group(1))
            in_prologue = False
            if frame > maxframe:
                maxframe = frame
        # 否则是 call 的出参区 —— 忽略
        continue
    if s == "call ___chkstk_ms":
        chk += 1
    if frame:
        for sm in slot_re.finditer(l):
            off = int(sm.group(1))
            if off > frame:
                viol += 1
                if len(detail) < 3:
                    detail.append(f"槽位 -{off}(%rbp) 越出帧 {frame}")
print(maxframe, chk, viol, "; ".join(detail))
PY
}

check_frame_bloat() {
    hdr "v4.2.1  帧尺寸膨胀 + 每次调用的 chkstk 探页"
    [ -x "$JHYY_EXE" ] || { skip "frame_bloat" "jhyy.exe 不存在"; return; }

    local f="$WORK/fb.jhyy"
    cat > "$f" <<'JEOF'
fn add(a: i32, b: i32) -> i32 { return a + b; }
fn mul(a: i32, b: i32) -> i32 { return a * b; }
fn chain(a: i32) -> i32 { return add(mul(a, 3), add(a, 1)); }
fn main_jhyy() -> i32 {
    let mut r: i32 = 0;
    r = chain(1);
    return r;
}
JEOF
    if ! "$JHYY_EXE" compile --target=amd64_win --no-link "$f" -o "$WORK/fb" \
            > "$WORK/fb.log" 2>&1; then
        badenv "frame_bloat" "编译失败:$(tail -3 "$WORK/fb.log" | tr '\n' ' ')"
        return
    fi
    [ -f "$WORK/fb.s" ] || { badenv "frame_bloat" "没有产出 .s"; return; }

    local stats maxframe chk viol
    stats=$(_frame_stats "$WORK/fb.s")
    maxframe=$(echo "$stats" | cut -d' ' -f1)
    chk=$(echo "$stats" | cut -d' ' -f2)
    viol=$(echo "$stats" | cut -d' ' -f3)
    [ -n "$maxframe" ] || { badenv "frame_bloat" "量不到帧大小"; return; }

    # 阈值:一个小函数(几个 temp)的帧不该超过 1KB。
    # 修之前恒 ≥8352(写死的 8192 预留)⇒ 这条门修之前**必然红**。
    if [ "$maxframe" -gt 1024 ]; then
        bad "frame_bloat" "小函数的帧 ${maxframe}B > 1024B —— alloc 池预留还是写死的 8192"
        return
    fi
    # 帧 < 4096 ⇒ Windows ABI 不要求探页 ⇒ 不该再有 ___chkstk_ms
    if [ "$chk" -ne 0 ]; then
        bad "frame_bloat" "还有 ${chk} 处 ___chkstk_ms —— 帧仍 >4096,每次调用都在探页"
        return
    fi
    ok "frame_bloat(最大帧 ${maxframe}B, chkstk ${chk} 处)"
}

check_frame_slots() {
    hdr "v4.2.1  栈槽必须落在该函数的预留帧内(帧算小的安全网)"
    [ -x "$JHYY_EXE" ] || { skip "frame_slots" "jhyy.exe 不存在"; return; }

    local f="$WORK/fs.jhyy"
    cat > "$f" <<'JEOF'
fn add(a: i32, b: i32) -> i32 { return a + b; }
fn mul(a: i32, b: i32) -> i32 { return a * b; }
fn chain(a: i32) -> i32 { return add(mul(a, 3), add(a, 1)); }
fn main_jhyy() -> i32 {
    let mut r: i32 = 0;
    r = chain(1);
    return r;
}
JEOF
    if ! "$JHYY_EXE" compile --target=amd64_win --no-link "$f" -o "$WORK/fs" \
            > "$WORK/fs.log" 2>&1; then
        badenv "frame_slots" "编译失败:$(tail -3 "$WORK/fs.log" | tr '\n' ' ')"
        return
    fi
    [ -f "$WORK/fs.s" ] || { badenv "frame_slots" "没有产出 .s"; return; }

    local stats viol detail
    stats=$(_frame_stats "$WORK/fs.s")
    viol=$(echo "$stats" | cut -d' ' -f3)
    detail=$(echo "$stats" | cut -d' ' -f4-)
    if [ "$viol" -ne 0 ]; then
        bad "frame_slots" "${viol} 个栈槽越出该函数的预留帧 —— ${detail}"
        return
    fi
    ok "frame_slots(所有 rbp 相对槽位都在帧内)"
}

# ════════════════════════════════════════════════════════════════════════════
# 4. W-116 — SysV callee 参数溢出必须覆盖 6 个整数寄存器
# ════════════════════════════════════════════════════════════════════════════
#
# 症状:callee 的参数溢出循环只做 4 个寄存器,第 5 个开始重复用 %ecx:
#     movl %edi, -8(%rbp)     movl %esi, -16(%rbp)
#     movl %edx, -24(%rbp)    movl %ecx, -32(%rbp)
#     movl %ecx, -40(%rbp)   ← arg5,又读 %ecx
#     movl %ecx, -48(%rbp)   ← arg6
#     movl %ecx, -56(%rbp)   ← arg7
# `%r8d` / `%r9d` / 栈参数在 callee 里从未出现。
#
# 验法:不跑二进制,直接看 .s 里 callee 的溢出序列用了哪几个寄存器。
# 这比「实跑看退出码」快且不受 docker 影响 —— 编译侧就已经错了。

check_sysv_mixed_struct() {
    hdr "W-104  含 f64 的 struct 在 SysV 下是否按 eightbyte 分类(INTEGER + SSE)"
    [ -x "$JHYY_EXE" ] || { skip "sysv_mixed_struct" "jhyy.exe 不存在"; return; }

    cat > "$WORK/sysvmix.jhyy" <<'EOF'
type Mixed = struct { i_field: i32, d_field: f64 }
fn plain_f64(x: f64, y: i32) -> i32 { return (x as i32) + y; }
fn mixed_struct(m: Mixed) -> i32 { return m.i_field + (m.d_field as i32); }
fn main_jhyy() -> i32 { return 0; }
EOF
    if ! "$JHYY_EXE" compile --target=amd64_sysv_freestanding --no-link             "$WORK/sysvmix.jhyy" -o "$WORK/sysvmix" > "$WORK/sysvmix.log" 2>&1; then
        badenv "sysv_mixed_struct" "编译失败:$(tail -3 "$WORK/sysvmix.log" | tr '
' ' ')"
        return
    fi
    [ -s "$WORK/sysvmix.s" ] || { badenv "sysv_mixed_struct" "没产出 .s"; return; }

    # 探针规则(为什么是「第一条 movsd 的源」而不是「有没有 xmm 源 movsd」):
    #   SysV § A.2/A.3:`{i32, f64}` 占**两个** eightbyte —— INTEGER(rdi) +
    #   SSE(xmm0)。所以正确实现的序言里,f64 参数是**直接从 xmm0 落进栈槽**的,
    #   函数体内第一条 `movsd` 的**源操作数必然是 xmm 寄存器**。
    #
    #   ⚠️ 不能只判「有没有 xmm 源的 movsd」—— 那会假阳性:`movsd %xmm0, -N(%rbp)`
    #   是一次**存**,缺陷版本里也有(它是「从内存载入 xmm0」之后的落袋动作)。
    #   必须看**第一条**:它才是「参数以什么形式进来」。
    #
    #   现状:整个 struct 被塞进**一个**整数槽位,第一条 movsd 是
    #   `movsd (%r8), %xmm0` —— f64 是靠 `(%rdi + 8)` 的偏移读出来的。
    #
    #   **对照组 `plain_f64` 保证判据不空转** —— 同一文件里的标量 f64 参数
    #   必须命中 xmm 源,否则说明判据本身写错了,报 env 而不是报 bug。
    local first_ctrl first_mix
    first_ctrl=$(sed -n '/^plain_f64:/,/^  ret/p' "$WORK/sysvmix.s"                  | grep -m1 -E 'movsd' || true)
    first_mix=$(sed -n '/^mixed_struct:/,/^  ret/p' "$WORK/sysvmix.s"                 | grep -m1 -E 'movsd' || true)
    [ -n "$first_ctrl" ] || { badenv "sysv_mixed_struct" "对照组没产出 movsd"; return; }
    [ -n "$first_mix" ]  || { badenv "sysv_mixed_struct" "实测组没产出 movsd"; return; }

    if ! printf '%s' "$first_ctrl" | grep -qE 'movsd[[:space:]]+%xmm'; then
        badenv "sysv_mixed_struct" "对照组 plain_f64 首条 movsd 的源不是 xmm(本该是):$first_ctrl"
        return
    fi
    if printf '%s' "$first_mix" | grep -qE 'movsd[[:space:]]+%xmm'; then
        ok "sysv_mixed_struct(首条 movsd 从 xmm 进来:$first_mix)"
        return
    fi

    # 报告实际读法,便于诊断
    local how
    how=$(sed -n '/^mixed_struct:/,/^  ret/p' "$WORK/sysvmix.s"           | grep -E 'addq[[:space:]]+\$8|movsd' | head -2 | tr '
' ' ')
    bad "sysv_mixed_struct" "含 f64 的 struct 整体退化成一个整数寄存器槽位(d_field 靠偏移读:$how)"
}

check_sysv_arg_spill() {
    hdr "W-116  SysV callee 参数溢出是否覆盖 6 个整数寄存器"
    [ -x "$JHYY_EXE" ] || { skip "sysv_arg_spill" "jhyy.exe 不存在"; return; }

    cat > "$WORK/sysv.jhyy" <<'EOF'
fn seven(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32) -> i32 { e }
fn main_jhyy() -> i32 { return seven(1,2,3,4,5,6,7); }
EOF
    if ! "$JHYY_EXE" compile --target=amd64_sysv_freestanding --no-link \
            "$WORK/sysv.jhyy" -o "$WORK/sysv" > "$WORK/sysv.log" 2>&1; then
        badenv "sysv_arg_spill" "编译失败:$(tail -3 "$WORK/sysv.log" | tr '\n' ' ')"
        return
    fi

    # seven 的序言里应出现 %r8d / %r9d(参数 5、6 的 SysV 整数寄存器)
    local body
    body=$(awk '/^seven:/,/ret/' "$WORK/sysv.s")
    local miss=""
    grep -q 'r8d' <<< "$body" || miss="$miss %r8d"
    grep -q 'r9d' <<< "$body" || miss="$miss %r9d"
    # 第 7 个参数走栈:callee 应从 16(%rbp) 读
    grep -qE '16\(%rbp\)|\(%rbp\),%r1[01]d' <<< "$body" || miss="$miss stack-arg7"

    if [ -n "$miss" ]; then
        bad "sysv_arg_spill" "callee 序言缺少:$miss —— 参数 5/6/7 没被正确读(W-116 未修)"
        return
    fi
    ok "sysv_arg_spill(r8d / r9d / 栈参数都出现在 callee 序言里)"
}

# ════════════════════════════════════════════════════════════════════════════
# W-104(b) MEMORY class(>16B 的 struct 整体落栈)
# ════════════════════════════════════════════════════════════════════════════
#
# ≤16B 的 struct 走 eightbyte 分类(上面那条 check 验的);**>16B** 的走
# MEMORY class(SysV psABI § A.2/A.3):整份拷贝到栈上,不占整数寄存器。
#
# 这条 check **不跑二进制**,只看 .s —— 于是它在 Windows runner 上就能跑,
# 不依赖 docker(跨实现对拍在 sysv job 里,需要 Linux)。
#
# 判据(两条都验,缺一不可):
#   ① caller 侧:调用点前有 `subq $N, %rsp`(N>0)预留 outgoing 区,
#      且 struct 的每个 8 字节 slot 被写到 0/8/16(%rsp)。
#      ⚠️ 没有 outgoing 区的话,slot 会写进**调用者自己帧的最底部** ——
#      踩掉调用者的局部变量。缺陷版本正是这样。
#   ② callee 侧:序言里从 16(%rbp) / 24(%rbp) / 32(%rbp) 读这三个 slot,
#      **而不是**从 %rdi 读(那是 ≤16B 的 INTEGER 路径)。
check_sysv_memory_class() {
    hdr "W-104(b)  >16B 的 struct 在 SysV 下是否走 MEMORY class(整体落栈)"
    [ -x "$JHYY_EXE" ] || { skip "sysv_memory_class" "jhyy.exe 不存在"; return; }

    cat > "$WORK/sysvmem.jhyy" <<'EOF'
type Big = struct { a: i64, b: i64, c: i64 }
extern fn take_big(m: Big) -> i32;
fn callee_big(m: Big) -> i32 { return (m.a + m.b + m.c) as i32; }
fn main_jhyy() -> i32 { let m = Big { a: 1 as i64, b: 2 as i64, c: 3 as i64 }; return callee_big(m); }
EOF
    if ! "$JHYY_EXE" compile --target=amd64_sysv_freestanding --no-link \
            "$WORK/sysvmem.jhyy" -o "$WORK/sysvmem" > "$WORK/sysvmem.log" 2>&1; then
        badenv "sysv_memory_class" "编译失败:$(tail -3 "$WORK/sysvmem.log" | tr '\n' ' ')"
        return
    fi
    [ -s "$WORK/sysvmem.s" ] || { badenv "sysv_memory_class" "没产出 .s"; return; }

    # ① caller 侧:调用点前预留 outgoing 区 + 三个 slot 写到 0/8/16(%rsp)
    local callzone
    callzone=$(awk '/emit_call: SysV/,/call /' "$WORK/sysvmem.s")
    local miss=""
    printf '%s' "$callzone" | grep -qE 'subq[[:space:]]+\$[0-9]+,[[:space:]]*%rsp' \
        || miss="$miss no-outgoing-area"
    for off in 0 8 16; do
        printf '%s' "$callzone" | grep -qE "movq[[:space:]]+%r10,[[:space:]]+$off\(%rsp\)" \
            || miss="$miss slot@$off(%rsp)"
    done

    # ② callee 侧:从 16/24/32(%rbp) 读,且**不是**从 %rdi 读
    local body
    body=$(awk '/^callee_big:/,/ret/' "$WORK/sysvmem.s")
    for off in 16 24 32; do
        printf '%s' "$body" | grep -qE "movq[[:space:]]+$off\(%rbp\)," \
            || miss="$miss read@$off(%rbp)"
    done
    printf '%s' "$body" | grep -qE 'movq[[:space:]]+%rdi,' \
        && miss="$miss read-from-rdi"

    if [ -n "$miss" ]; then
        bad "sysv_memory_class" "MEMORY class 的栈传递不完整:$miss —— >16B 的 struct 没有整体落到栈上"
        return
    fi
    ok "sysv_memory_class(caller 预留 outgoing 区并推 3 个 slot;callee 从 16/24/32(%rbp) 读)"
}

# ════════════════════════════════════════════════════════════════════════════
# 8. W-131/W-132 — 链出来的 exe 必须带 RT_ICON 资源
# ════════════════════════════════════════════════════════════════════════════
#
# 症状(v4.0.8 起):v4.0.8 把 jhyy.exe 的产出从 C 侧编译器改到**自举编译器**,
# 而嵌图标的 windres 步骤只在 C 侧(compiler/src/main.c:503-558)有 —— 自举侧
# 一行都没有。于是每一个 jhyy.exe 都不带图标资源。
#
# 这个失效模式**任何 .jhyy 测试都验不到**:程序照跑、退出码照对,只是图标没了。
# 用户侧的表征是「.jhyy 文件在 Explorer 里全是白板」——
# 因为 installer 的 FileAssoc 把 DefaultIcon 指向 jhyy.exe,0。
#
# 验法:用 **Explorer 同一套 API**(shell32!ExtractIconExW)问「这个 exe 里到底
# 有没有图标」。不用 objdump 猜 .rsrc 节 —— 那个只能证明有资源节,不能证明
# 里面有可取的图标组。
#
# 两条断言:
#   ① 编译器自己(jhyy.exe)带图标 —— v1.8.1 的原意之一;
#   ② **它编出来的程序**带图标 —— v1.8.1 的原意之二(用户天天看的东西)。

# icon_probe <exe> → 打印 ExtractIconEx 拿到的图标个数(0 = 没有图标)
#
# 实现放在独立脚本 compiler/tests/bootstrap/icon_probe.ps1 ✓ —— 因为:
#   · **python 在 CI 上不可用**:CI runner 的 python 是 MSYS2 的 /usr/bin/python
#     (Cygwin 版)—— ctypes 没有 WinDLL,退回 CDLL("shell32") 又被 Cygwin 的
#     _dlopen 挡掉(OSError)。两条路都不通(本地是 Windows python 才绿)。
#   · PowerShell 走 Windows 原生 API ✓,且和 Explorer 用同一套
#     shell32!ExtractIconExW ⇒ 判据最忠实。
#   · 独立 .ps1 文件 ⇒ bash→PowerShell 的引号地狱不存在(param() 收参 ✓)。
icon_probe() {
    powershell -NoProfile -ExecutionPolicy Bypass         -File "$JHYY_ROOT/compiler/tests/bootstrap/icon_probe.ps1" "$1" 2>/dev/null
}

# icon_diag <exe> → 失败时的诊断尾巴:产物里到底有没有 .rsrc 节,以及
# **对照探针** —— jhyy_stage0.exe 是 C 侧编译器(main.c 的 windres)链出来的,
# 走的是同款「windres → .ico.o → 链接」流程:
#   · stage0 **有**图标而 jhyy.exe 没有 ⇒ 链接这一步把 .rsrc 丢了
#   · stage0 **也没有**           ⇒ windres 那一侧的问题(或工具链版本)
# 这条对照是本门能自我定位的关键 —— 光看「取不到图标」分不出这两种。
icon_diag() {
    local exe="$1" out="" sect="" s0=""
    sect=$(objdump -h "$exe" 2>/dev/null | grep -E '\.rsrc' | head -1 | tr -s ' ')
    if [ -n "$sect" ]; then
        out=" | .rsrc 节: $sect"
    else
        out=" | 产物里**没有 .rsrc 节**"
    fi
    if [ -x "$JHYY_ROOT/compiler/build/bin/jhyy_stage0.exe" ]; then
        s0=$(icon_probe "$(cygpath -w "$JHYY_ROOT/compiler/build/bin/jhyy_stage0.exe" 2>/dev/null || echo "$JHYY_ROOT/compiler/build/bin/jhyy_stage0.exe")")
        out="$out | 对照 jhyy_stage0.exe(C 侧 windres 链法)图标数=${s0:-?}"
    fi
    printf '%s' "$out"
}

check_compiler_icon() {
    hdr "W-131/W-132  jhyy.exe 自己是否带图标资源"
    [ -x "$JHYY_EXE" ] || { skip "compiler_icon" "jhyy.exe 不存在"; return; }

    local exe n
    exe=$(cygpath -w "$JHYY_EXE" 2>/dev/null || echo "$JHYY_EXE")
    n=$(icon_probe "$exe")
    if [ "${n:-0}" -eq 0 ]; then
        bad "compiler_icon" "jhyy.exe 里取不到图标(ExtractIconEx=0)—— 自举链接路径没嵌 RT_ICON 资源(W-131/W-132 未修)$(icon_diag "$exe")"
        return
    fi
    ok "compiler_icon(jhyy.exe 带 $n 个图标)"
}

check_program_icon() {
    hdr "W-131/W-132  jhyy 编出来的程序是否带图标资源"
    [ -x "$JHYY_EXE" ] || { skip "program_icon" "jhyy.exe 不存在"; return; }

    cat > "$WORK/icon.jhyy" <<'EOF'
fn main_jhyy() -> i32 { return 7; }
EOF
    # 注意:这里**不传 --target** —— 默认 target 就是 amd64_win(见 target_default()),
    # 而 `--target=` 放文件前面这条形式当前有个**既有**回归(见 workarounds.md 的
    # 「自举产物行为漂移」那条):argv 里的 --target= 没被剥掉 → 编译器把
    # "--target=amd64_win" 当成文件名 → "cannot open file"。
    # 那条不是本门要验的东西,门不该被它拖红。
    if ! "$JHYY_EXE" compile "$WORK/icon.jhyy" -o "$WORK/icon" \
            > "$WORK/icon.log" 2>&1; then
        badenv "program_icon" "编译失败:$(tail -3 "$WORK/icon.log" | tr '\n' ' ')"
        return
    fi
    local exe n
    exe=$(cygpath -w "$WORK/icon.exe" 2>/dev/null || echo "$WORK/icon.exe")
    [ -f "$exe" ] || { badenv "program_icon" "没产出 .exe"; return; }

    n=$(icon_probe "$exe")
    if [ "${n:-0}" -eq 0 ]; then
        bad "program_icon" "编出来的 exe 里取不到图标(ExtractIconEx=0)—— 链接路径没嵌 RT_ICON 资源(W-131/W-132 未修)$(icon_diag "$exe")"
        return
    fi
    ok "program_icon(编出来的 exe 带 $n 个图标)"
}

# 2026-11-06:`jhyy run` 这条路径**回归门完全没覆盖** ——
# regress.py 是**直接跑编出来的 .exe**的,不经过 `jhyy run` ⇒ exe 路径的
# 构造、子进程的启动、退出码的透传、用户 stderr 的去向,**全都没有门**。
# 代价实测过:2026-11-06 把 str_concat_at 改成逐字节时,一个「隐式 NUL 终止」
# 被打破 ⇒ exe 路径变成堆垃圾 ⇒ `jhyy run` 全线失败(exit -1)——
# 而**全量回归是绿的**。这道门补上这个覆盖。
check_run_cmd() {
    hdr "jhyy run 端到端:退出码透传 + 用户的 stderr 看得见"
    [ -x "$JHYY_EXE" ] || { skip "run_cmd" "jhyy.exe 不存在"; return; }

    cat > "$WORK/runme.jhyy" <<'EOF'
extern fn jh_fputs_stderr(s: *u8) -> i32;
fn main_jhyy() -> i32 {
    let _e = jh_fputs_stderr("RUN-STDERR-MARKER\n" as *u8);
    return 42;
}
EOF
    local out rc
    out=$("$JHYY_EXE" run "$WORK/runme.jhyy" 2>&1)
    rc=$?
    # 退出码:子进程的 42 必须原样透传。
    if [ "$rc" != "42" ]; then
        bad "run_cmd" "jhyy run 的退出码是 $rc(期望 42)—— 子进程没被正确启动,或退出码没透传"
        return
    fi
    # 用户的 stderr 必须看得见(修复前它进了管道却从没人读 ⇒ 整个被吞掉)。
    case "$out" in
        *RUN-STDERR-MARKER*) : ;;
        *)
            bad "run_cmd" "用户的 stderr 看不见(输出里没有 RUN-STDERR-MARKER)—— stderr 被吞掉了"
            return
            ;;
    esac
    ok "run_cmd(jhyy run 退出码 42 ✓,用户的 stderr 可见 ✓)"
}

# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
# 自检:证明分类逻辑(而不是编译器行为)本身是对的
# ════════════════════════════════════════════════════════════════════════════
#
# 为什么需要:上面那张判定表里,「绿」只有一个来源(登记一致),「红」有四种。
# 一旦分类逻辑写错(把该红的判绿、或反之),整道门就静默失真 —— 而这正是
# feedback_ci_gate_must_exercise_path 说的那种「从没被见过红的门」。
#
# 成本:纯字符串运算,不碰编译器,不产生任何 .jhyy/.s/.exe,亚秒级。
# 所以它可以被塞进 CI 的 audit job(不需要 build)每轮都跑。
selftest() {
    local st_fail=0

    # _case <说明> <期望 FAIL 增量> <期望 KNOWN 增量> <动作...>
    _case() {
        local desc="$1" xf="$2" xk="$3"; shift 3
        local f0=$FAIL_N k0=$KNOWN_N
        "$@" >/dev/null 2>&1
        local df=$((FAIL_N - f0)) dk=$((KNOWN_N - k0))
        if [ "$df" = "$xf" ] && [ "$dk" = "$xk" ]; then
            printf "  ✅ %-46s (FAIL +%d / KNOWN +%d)\n" "$desc" "$df" "$dk"
        else
            printf "  ❌ %-46s 期望 FAIL +%d / KNOWN +%d,实得 FAIL +%d / KNOWN +%d\n" \
                   "$desc" "$xf" "$xk" "$df" "$dk"
            st_fail=$((st_fail + 1))
        fi
    }

    # 自检用**自己的**登记条目 —— 不复用真表里的任何 check id。
    #
    # 为什么(2026-10-20 实测踩到):真表会随 workaround 修复而变。W-112 修好后
    # `link_section` 从 KNOWN_FAIL 删掉,自检里 3 个以它为例的用例当场失效 ——
    # **分类逻辑本身没坏**,CI 却红了(跑 39389190863 就是这么红的)。
    # 这类「夹具绑在真表上」的自检,每修一条 workaround 都要跟着改一次 ——
    # 而它要验的东西(四种红 + 两种绿的分类)根本跟「当前哪条 check 登记着」无关。
    #
    # 所以自检自带一条假登记,验完就撤 —— 与真表解耦,真表怎么变都不影响它。
    KNOWN_FAIL[selftest_probe]="W-SELFTEST|签名甲|签名乙"

    echo "=== artifact_checks.sh — 分类逻辑自检(不跑编译) ==="
    _case "已登记+签名吻合 → KNOWN-FAIL(绿)" 0 1 \
          bad selftest_probe "生成的 .s 里 0 条 .section 指令 —— 签名甲"
    _case "已登记+第二签名吻合 → KNOWN-FAIL(绿)" 0 1 \
          bad selftest_probe "反汇编里有 2 条 cpuid,但签名乙"
    _case "已登记+签名是子串 → KNOWN-FAIL(绿)" 0 1 \
          bad selftest_probe "xx签名甲yy"
    _case "已登记+签名不吻合 → FAIL(红)" 1 0 \
          bad selftest_probe "有 3 条 .section,但没有 .text.boot —— 属性名没生效"
    _case "未登记的 check 失败 → FAIL(红)" 1 0 \
          bad some_new_check "随便什么失败"
    _case "环境/编译失败 → FAIL(红),不查登记" 1 0 \
          badenv selftest_probe "编译失败:..."
    # 2026-11-06:skip 与 badenv 同义(都红)。此前 skip 只进 SKIP_N、退出码只看
    # FAIL_N ⇒ check 没跑成时门报绿。这条用例锁住「skip 必须红」。
    _case "没跑成(skip)→ FAIL(红),不查登记" 1 0 \
          skip selftest_probe "objdump 不在 PATH"
    _case "已登记却通过 → UNEXPECTED-PASS(红)" 1 0 \
          ok "selftest_probe(.text.boot 已出现在产物里)"
    _case "未登记却通过 → PASS(绿)" 0 0 \
          ok "some_new_check(一切正常)"

    unset 'KNOWN_FAIL[selftest_probe]'

    echo
    if [ "$st_fail" -gt 0 ]; then
        echo "  ❌ 自检 $st_fail 条不符 —— 分类逻辑本身坏了,门已失真"
        exit 1
    fi
    echo "  ✅ 9/9 分类用例通过 —— 四种红与两种绿都能正确触发"
    exit 0
}

if [ "$SELFTEST" -eq 1 ]; then
    selftest
fi

echo "=== artifact_checks.sh — 产物级门 ==="
echo "  JHYY_ROOT = $JHYY_ROOT"
echo "  JHYY_EXE  = $JHYY_EXE"
[ -f "$JHYY_EXE" ] || { echo "ERR: jhyy.exe 不存在,先跑 make" >&2; exit 2; }

want() { [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]; }

# ════════════════════════════════════════════════════════════════════════════
# 8. W-130 — address-holder bitmap 的容量在 C 桥接层与 jhyy 侧脱节
# ════════════════════════════════════════════════════════════════════════════
#
# 背景(2026-10-24 定位,数字闭合):
#   jhyy 侧的 address-holder bitmap 按**实际 max temp id 动态扩容**
#   (cg_resize_temp_tables, codegen_amd64_state.jhyy:1862),边界检查
#   (cg_record_temp_holds_address / cg_is_address_holder)也用动态的
#   state.temp_holds_size。但 C 桥接层(jhyy_helpers.c:951/957)仍把索引
#   上限**硬编码 65536**。
#   ⇒ temp id ≥ 65536 的 address-holder 标记**写不进去、读不出来**
#   ⇒ emit_loadsub 的 indirect/slot 分派退化成「读栈槽里**指针的低字节**」
#   ⇒ 编译器**自己**的 `--target=` 9 字节前缀比较失效
#     (症状:unknown command / cannot open file / target 字符串读成路径尾巴)。
#
#   为什么 32/64 位 load 不受影响:W-097 已把 emit_load / emit_store 改成
#   **无条件 indirect** ⇒ 只有**字节/半字节读**会被打坏。
#
#   触发条件是**被编译单元自身的 temp id 规模**(随源码单调增长),不是某个
#   具体改动的语义 ⇒ 这是一条**悬崖**:temp id 越过 65536 就静默产出错代码。
#   同一个坑历史上撞过一次(上限 4096 → 提到 65536),这次是第二次。
#
# 三条门:
#   G2 check_holds_bitmap        产物+行为(主门)—— 字节读在悬崖之上还准不准
#   G3 check_holds_cap_source    源码形态 —— C 桥不得再有字面量上界
#   G4 check_selfhost_target_flag 端到端症状 —— 自举后的编译器还认不认 --target=

# _max_indirect_byte_base <file.s> — .s 里「间接字节读」的最高 base temp id。
# 形态(W-097 修后):
#     movq -2256(%rbp), %r8        # %t65425 (address-holder)
#     movzbl (%r8), %eax
# base temp id 就在**上一行**装 %r8 的注释里。
# 只认 mov(s|z)[bwl]+ (%r8) 这一族(字节/半字节读);movl/movq (%r8) 是 W-097 的
# 无条件 indirect(本来就是对的),movsd/movss 是浮点,都不算。
_max_indirect_byte_base() {
    awk '
    {
        if (match($0, /, %r8/) && match($0, /%t[0-9]+/)) {
            last = substr($0, RSTART + 2, RLENGTH - 2) + 0
        }
        if (match($0, /mov(s|z)[bwl]+[ \t]*\(%r8\)/)) {
            if (last > max) max = last
        }
    }
    END { print max + 0 }' "$1"
}

check_holds_bitmap() {
    hdr "W-130  address-holder bitmap 越界时,字节读是否仍然正确"
    [ -x "$JHYY_EXE" ] || { skip "holds_bitmap" "jhyy.exe 不存在"; return; }

    # 合成文件:N 个哑函数把 max temp id 顶过 65536,最后放一个**字节读** probe。
    #
    # ⚠️ N 的取值有讲究(实测,别乱改):temp id 是**按函数逐段分配**的,probe 的
    # 段起点 = 哑函数占的量 + 一点余量。N=5000 时 probe 的段起点 ≈ 65003 —— **还在
    # 悬崖之下** ⇒ probe 的字节读 base temp 也不过悬崖 ⇒ 读是对的 ⇒ 这道门测不到
    # W-130(实测踩过:门报了「最高 base = 65003」)。N=5600 时 probe 段起点
    # ≈ 72800 ⇒ 越过悬崖 ⇒ 修前字节读被降级成槽直读 ⇒ probe 退出码 90 ⇒ 红。
    # 门里有前置断言,改这个数后会自己报「门是空的」,不会静默变绿。
    local N=5600
    local i=0
    {
        echo 'extern fn malloc(size: i64) -> *u8;'
        while [ "$i" -lt "$N" ]; do
            echo "fn f$i() -> i32 {"
            echo "    let mut x: i32 = 1;"
            echo "    let mut y: i32 = 2;"
            echo "    let mut z: i32 = x + y;"
            echo "    let mut w: i32 = z * 3;"
            echo "    return w;"
            echo "}"
            i=$((i+1))
        done
        # probe:同一个地址,先用 i64 通路写/读(权威来源,走 W-097 的无条件
        # indirect,一定对),再用 u8 通路读(W-130 的命中点:走 emit_loadsub,
        # 依赖 address-holder flag)。堆指针 16 字节对齐 ⇒ 槽直读拿到的是
        # 指针低字节(16 的倍数),必 ≠ 1 ⇒ 修前必红。
        echo 'fn probe() -> i32 {'
        echo '    let p = malloc(8 as i64);'
        echo '    *(p as *i64) = 1 as i64;'
        echo '    let w: i64 = *(p as *i64);'
        echo '    let expect: i32 = (w & (255 as i64)) as i32;'
        echo '    let b: i32 = (*(p as *u8)) as i32;'
        echo '    if b != expect { return 1; }'
        echo '    return 0;'
        echo '}'
        echo 'fn main_jhyy() -> i32 {'
        echo '    let mut s: i32 = 0;'
        i=0
        while [ "$i" -lt "$N" ]; do
            echo "    s = s + f$i();"
            i=$((i+1))
        done
        echo '    if probe() != 0 { return 90; }'
        echo '    return 0;'
        echo '}'
    } > "$WORK/holds.jhyy"

    if ! "$JHYY_EXE" compile "$WORK/holds.jhyy" -o "$WORK/holds" > "$WORK/holds.log" 2>&1; then
        badenv "holds_bitmap" "编译失败:$(tail -3 "$WORK/holds.log" | tr '\n' ' ')"
        return
    fi
    if [ ! -x "$WORK/holds.exe" ]; then
        badenv "holds_bitmap" "编译成功但没产出 exe"
        return
    fi
    # ── 前置断言:这道门必须真的踩中悬崖,否则它就是一道「永远绿」的门 ──
    #   max temp id 必须 > 65536(C 桥的旧硬上限)⇒ 标记会被丢弃
    local maxt
    maxt=$(grep -o '%t[0-9]*' "$WORK/holds.s" 2>/dev/null | sed 's/%t//' | sort -n | tail -1)
    if [ -z "$maxt" ]; then
        badenv "holds_bitmap" "产物 .s 里找不到 %tN —— 合成文件或产物异常"
        return
    fi
    if [ "$maxt" -le 65536 ]; then
        bad "holds_bitmap" "合成文件的最大 temp id = $maxt(需要 > 65536)—— 这个用例**没有**踩到 W-130 的悬崖,门是空的"
        return
    fi
    # ── 判别 1:产物形态 —— 那处字节读必须是**间接**的,且 base temp 已越过悬崖 ──
    local base
    base=$(_max_indirect_byte_base "$WORK/holds.s")
    if [ "$base" -le 65536 ]; then
        bad "holds_bitmap" "产物里没有「base temp > 65536 的间接字节读」(实测最高 base = $base)—— 字节读被降级成了槽直读(C 桥容量通道未修好)"
        return
    fi
    # ── 判别 2:行为 —— 跑起来必须对 ──
    local rc
    "$WORK/holds.exe" >/dev/null 2>&1
    rc=$?
    if [ "$rc" -ne 0 ]; then
        bad "holds_bitmap" "probe 退出码 = $rc(期望 0)—— 越过 65536 后的 u8 读拿到了错误的字节(address-holder 标记被丢弃)"
        return
    fi
    ok "holds_bitmap(max temp=$maxt, 最高间接字节读 base=$base, probe 正确)"
}

check_holds_cap_source() {
    hdr "W-130  C 桥的 address-holder bitmap 不得再有字面量上界"
    local f="$JHYY_ROOT/compiler/src0/jhyy_helpers.c"
    [ -f "$f" ] || { badenv "holds_cap_source" "找不到 $f"; return; }

    # 容量通道必须还在(jhyy 侧靠它把实际容量告诉 C 侧)
    if ! grep -q "jh_cgstate_set_holds_table" "$f"; then
        bad "holds_cap_source" "C 侧找不到 jh_cgstate_set_holds_table —— 容量通道不见了(W-130 回归)"
        return
    fi
    # 两个 flag 访问器里不得再出现字面量上界(C 侧不能自己猜容量)
    local hits
    hits=$(
        {
            sed -n '/jh_cgstate_set_holds_flag/,/^}/p' "$f"
            sed -n '/jh_cgstate_get_holds_flag/,/^}/p' "$f"
        } | grep -nE 'idx[[:space:]]*(>=|>)[^;]*[[:space:]][0-9]+' || true
    )
    if [ -n "$hits" ]; then
        bad "holds_cap_source" "C 侧又出现了字面量上界: $hits —— W-130 的原始形态"
        return
    fi
    ok "holds_cap_source(容量从 jhyy 侧同步,C 侧无字面量上界)"
}

check_selfhost_target_flag() {
    hdr "W-130  自举后的编译器必须还能摘掉 --target="
    [ -x "$JHYY_EXE" ] || { skip "selfhost_target_flag" "jhyy.exe 不存在"; return; }

    # compiler/build/bin/jhyy.exe **本身就是自举产物**(v4.0.8 起由它自己编 src0),
    # 所以它跑 --target= 的行为**就是** W-130 的症状本身 —— 不需要另编 stage2。
    #
    # 症状形态(W-130):argv 里的 --target= 没被摘掉 ⇒ cmd_compile 把它当成输入
    # 文件名 ⇒ fopen 失败 ⇒ 打印 "cannot open file";更糟的一档是压缩循环把输入
    # 文件写进 argv[1] ⇒ cmd_dispatched 不再是 "compile" ⇒ "unknown command"。
    if ! "$JHYY_EXE" compile --target=amd64_win --no-link \
            "$JHYY_ROOT/compiler/tests/examples/arith.jhyy" -o "$WORK/tgt" \
            > "$WORK/tgt.log" 2>&1; then
        bad "selfhost_target_flag" "自举后的编译器处理 --target= 失败:$(tail -3 "$WORK/tgt.log" | tr '\n' ' ')—— W-130 回归"
        return
    fi
    # 顺带验普通路径没被带坏(--target= 摘掉之后,剩下的 argv 仍要正确)
    if ! "$JHYY_EXE" compile --no-link \
            "$JHYY_ROOT/compiler/tests/examples/arith.jhyy" -o "$WORK/tgt2" \
            > "$WORK/tgt2.log" 2>&1; then
        badenv "selfhost_target_flag" "普通 compile 也失败了:$(tail -3 "$WORK/tgt2.log" | tr '\n' ' ')"
        return
    fi
    ok "selfhost_target_flag(--target= 被正确摘掉,普通路径也正常)"
}

# ════════════════════════════════════════════════════════════════════════════
# 9. W-136 / W-137 — C 桥导出的符号不得被「未闭合的注释」静默吞掉
# ════════════════════════════════════════════════════════════════════════════
#
# 背景(v4.0.21,W-136 落地时踩的坑;三层叠加,查了整整一轮才定位):
#
#   ① W-136 给 side-file 路径加 pid 后缀时,在 jhyy_helpers.c 里留下一行
#      **未闭合的块注释起始符**,把 `jh_cgstate_get_state` /
#      `jh_cgstate_set_state` 两个 C 桥函数整块吞进注释 ⇒
#        · C 文件**照样编译通过**(gcc 只报一条 `-Wcomment` 警告);
#        · 产物里**没有**这两个符号 ⇒ 链接期才炸 `undefined reference`。
#   ② 当时 Makefile 里 `$(CFLAGS_STAGE0)` 是**未定义变量**(M5 Part 1 改名成
#      `$(CFLAGS_REPRO)` 时漏改这两处,见 W-137)⇒ 两个 .o 根本没带
#      `-Wall -Wextra` ⇒ ① 里那条 `-Wcomment` 警告被**静默**。
#   ③ 本机 PATH 里 `/mingw64/bin` 抢在 ucrt64 前面 ⇒ ld 加载到版本不同的
#      libintl/libiconv/zlib ⇒ **链接失败一个字都不打印** ⇒ 真错误被吞掉。
#
#   ⇒ 失效形态是「编译成功 + 链接失败 + 链接器零输出」——**任何只看退出码的
#     测试都抓不到**,连日志里都没有线索。所以这道门必须**产物级**。
#
# 判定方式:问一个**可判定**的问题 ——
#   **jhyy 侧声明要用的每一个 `extern fn jh_*`,C 桥是不是真的导出了?**
#   答不上来 ⇒ 少符号 ⇒ 链接期必炸 ⇒ 提前红。
#
# ⚠️ 必须**独立编译** jhyy_helpers.c,不复用 compiler/build/obj/_jhyy_helpers.o:
#   那个 .o 的新鲜度由 Makefile 保证,而本门可能在没跑 make 的环境下被单独调用
#   ⇒ 读它会验到**旧**的产物。独立编译只多花 ~2 秒,换来「验的一定是当前源码」。
#
#   新增 C 桥函数 ⇒ provided 变多 ⇒ **不红**(正常演进)。少一个 ⇒ 红。
check_helpers_symbols() {
    hdr "W-136/W-137  C 桥导出的符号不得被未闭合的注释静默吞掉"
    local c="$JHYY_ROOT/compiler/src0/jhyy_helpers.c"
    [ -f "$c" ] || { badenv "helpers_symbols" "找不到 $c"; return; }
    command -v gcc  >/dev/null 2>&1 || { badenv "helpers_symbols" "PATH 里没有 gcc"; return; }
    command -v nm    >/dev/null 2>&1 || { badenv "helpers_symbols" "PATH 里没有 nm"; return; }

    # 1) jhyy 侧(src0 全部模块,含 std/ 与 bootstrap/)声明要用的 C 桥符号
    local req="$WORK/helpers_req.txt"
    grep -rhoE 'extern fn jh_[A-Za-z0-9_]+' "$JHYY_ROOT/compiler/src0" \
        | sed 's/^extern fn //' | sort -u > "$req"
    if [ ! -s "$req" ]; then
        badenv "helpers_symbols" "没从 src0 里解析出任何 extern fn jh_* 声明 —— 提取规则失效"
        return
    fi

    # 2) C 桥**当前源码**真正导出的符号(独立编译 ⇒ 一定是当前源码的产物)
    local obj="$WORK/helpers_gate.o"
    if ! gcc -std=c11 -c "$c" -o "$obj" > "$WORK/helpers_gate.log" 2>&1; then
        badenv "helpers_symbols" "编译 jhyy_helpers.c 失败:$(tail -3 "$WORK/helpers_gate.log" | tr '\n' ' ')"
        return
    fi
    nm --defined-only "$obj" 2>/dev/null | awk '{print $NF}' | grep -E '^jh_' | sort -u > "$WORK/helpers_prov.txt"

    # 3) 差集 = 声明了但 C 桥没导出 ⇒ 链接期必炸 undefined reference
    local missing
    missing=$(comm -23 "$req" "$WORK/helpers_prov.txt")
    if [ -n "$missing" ]; then
        bad "helpers_symbols" "jhyy 侧声明了但 C 桥没导出:$(echo "$missing" | tr '\n' ' ')—— 链接期必炸 undefined reference(W-136 同款:被未闭合的注释吞掉?)"
        return
    fi
    ok "helpers_symbols($(wc -l < "$req") 个 extern fn jh_* 全部由 C 桥导出)"
}

check_crossvolume_rename() {
    hdr "W-138  跨盘改名必须带 MOVEFILE_COPY_ALLOWED"
    local f="$JHYY_ROOT/compiler/src0/jhyy_helpers.c"
    [ -f "$f" ] || { badenv "crossvolume_rename" "找不到 $f"; return; }

    # jh_rename_file 用 MoveFileExW 把 %TEMP% 里的临时 exe 改名成用户要的
    # 输出路径。**不带** MOVEFILE_COPY_ALLOWED 时,MoveFileExW 不能跨卷
    # (ERROR_NOT_SAME_DEVICE = 17)⇒ 输出路径与 %TEMP% 不同盘时**产物不落地**。
    #
    # 这条**没法用行为测**(要第二个卷,不是每台机器都有)⇒ 只能测源码契约,
    # 与 holds_cap_source 同款做法(那边也是「源码里不许再出现字面量上界」)。
    local fn
    fn=$(sed -n '/int jh_rename_file/,/^}/p' "$f")
    if [ -z "$fn" ]; then
        badenv "crossvolume_rename" "jhyy_helpers.c 里找不到 jh_rename_file"
        return
    fi
    if ! printf '%s' "$fn" | grep -q "MOVEFILE_COPY_ALLOWED"; then
        bad "crossvolume_rename" "jh_rename_file 的 MoveFileExW 没有 MOVEFILE_COPY_ALLOWED —— 跨盘时产物不落地(W-138 回归)"
        return
    fi
    ok "crossvolume_rename(改名带 MOVEFILE_COPY_ALLOWED,跨盘可落地)"
}

# ════════════════════════════════════════════════════════════════════════════
# W-168 — `jhyy build` 必须真的认 `-o`
# ════════════════════════════════════════════════════════════════════════════
#
# 症状(2026-10-30 修前):`jhyy build x.jhyy -o y` **静默忽略** `-o`
# —— 产物仍落回 x 旁边,零告警。而 usage 串写着 `[-o output]`
# ⇒ CLI 在说谎。连带后果:bench 之类想把产物引开的脚本只能让产物污染源码目录。
#
# 验法:**两个方向都要验** ——
#   ① 带 `-o`   ⇒ 产物落在 `-o` 指的地方,且默认位置**没有**残留;
#   ② 不带 `-o` ⇒ 产物仍落回默认位置(默认行为不许被改坏)。
# 只验①会漏掉「`-o` 生效了但默认行为被改坏」这种反向回归。

check_build_o_flag() {
    hdr "W-168  jhyy build 是否真的认 -o"
    [ -x "$JHYY_EXE" ] || { skip "build_o_flag" "jhyy.exe 不存在"; return; }

    local src="$WORK/bo.jhyy"
    local def="$WORK/bo.s"          # 不带 -o 时的默认产物(input 路径派生)
    local want="$WORK/bo_out.s"      # 带 -o 时的产物
    cat > "$src" <<'EOF'
fn main_jhyy() -> i32 { return 42; }
EOF

    # ① 带 -o
    rm -f "$def" "$want"
    if ! "$JHYY_EXE" build "$src" -o "$WORK/bo_out" > "$WORK/bo.log" 2>&1; then
        badenv "build_o_flag" "build 失败:$(tail -3 "$WORK/bo.log" | tr '\n' ' ')"
        return
    fi
    if [ ! -s "$want" ]; then
        bad "build_o_flag" "-o 指的地方没有产物(bo_out.s 不存在或为空)—— -o 又被忽略了"
        return
    fi
    if [ -e "$def" ]; then
        bad "build_o_flag" "默认位置仍有残留 .s —— -o 没把输出引走"
        return
    fi

    # ② 不带 -o:默认行为不许变
    rm -f "$def" "$want"
    if ! "$JHYY_EXE" build "$src" > "$WORK/bo2.log" 2>&1; then
        badenv "build_o_flag" "build(无 -o) 失败:$(tail -3 "$WORK/bo2.log" | tr '\n' ' ')"
        return
    fi
    if [ ! -s "$def" ]; then
        bad "build_o_flag" "不带 -o 时产物没落在默认位置 —— 默认行为被改坏了"
        return
    fi
    rm -f "$def" "$want"
    ok "build_o_flag(-o 生效 + 默认行为不变)"
}

# ════════════════════════════════════════════════════════════════════════════
# W-226 —— 链接失败时能不能说清「入口符号缺失」
#
# 为什么需要:链接失败时 gcc → collect2 → ld 三层,`ld` 的真实原因
# (undefined reference to `main_jhyy`)没被 collect2 转发 ⇒ 用户只看到
# 「collect2.exe: error: ld returned 1 exit status」⇒ 根本不知道该改什么。
# 而「入口符号缺失」是**编译器自己能判定**的(.s 里没有 `main_jhyy:` 标签)。
#
# ⚠️ 这条门走 `jhyy compile`(不是 `jhyy run`)—— W-065 的编译期预检**只覆盖
# cmd_run** ⇒ compile/build 路径上链接失败时只有这条诊断兜底。
# 这正是 IDE hook 踩到的形态(它跑的就是 `jhyy compile`)。
check_link_entry_diag() {
    hdr "W-226  链接失败时能否点名「入口符号 main_jhyy 缺失」"
    [ -x "$JHYY_EXE" ] || { skip "link_entry_diag" "jhyy.exe 不存在"; return; }

    local src="$WORK/badentry.jhyy"
    cat > "$src" <<'EOF'
fn main() -> i32 { return 0; }
EOF
    local out rc
    out=$("$JHYY_EXE" compile "$src" 2>&1)
    rc=$?
    # ① 必须真的链接失败(入口叫 main ⇒ runtime.c 的 main 找不到 main_jhyy)
    if [ "$rc" = "0" ]; then
        bad "link_entry_diag" "入口写成 \`fn main\` 的程序居然链接成功了 —— 那这条诊断没机会出现"
        return
    fi
    # ② 诊断必须点名 main_jhyy(以前只有 "ld returned 1 exit status")
    case "$out" in
        *main_jhyy*) : ;;
        *)
            bad "link_entry_diag" "链接失败的输出里没有 \`main_jhyy\` ⇒ 用户还是不知道该改什么(输出末尾:$(echo "$out" | tail -3 | tr '\n' ' '))"
            return
            ;;
    esac
    ok "link_entry_diag(链接失败时点名 main_jhyy ✓)"
}

# ════════════════════════════════════════════════════════════════════════════
# W-227 —— `jhyy dump` 打印的 f64 位模式是不是**合法 hex**
#
# 为什么需要:dump 是 AST 的对外视图(for-VEX 线读它)⇒ 位模式必须逐位可解析。
# 此前 nib≥10 的位被打成 'W'..'\' ⇒ 输出**不是合法 hex** ⇒ 下游要么直接失败、
# 要么读到错值(位模式逐位错)。
#
# 判据用两个已知常量:1.5 的 f64 位模式 = 0x3ff8000000000000,
# 0.1 的 f64 位模式 = 0x3fb999999999999a(末尾那个 'a' 正是 nib≥10 的位置)。
check_dump_float_hex() {
    hdr "W-227  jhyy dump 的 f64 位模式是不是合法 hex"
    [ -x "$JHYY_EXE" ] || { skip "dump_float_hex" "jhyy.exe 不存在"; return; }

    local src="$WORK/flt.jhyy"
    cat > "$src" <<'EOF'
fn main_jhyy() -> i32 {
    let a: f64 = 1.5;
    let b: f64 = 0.1;
    return 0;
}
EOF
    local out
    out=$("$JHYY_EXE" dump "$src" 2>&1)
    # ① 1.5 ⇒ 0x3ff8000000000000
    case "$out" in
        *0x3ff8000000000000*) : ;;
        *)
            bad "dump_float_hex" "dump 里没有 1.5 的正确位模式 0x3ff8000000000000 ⇒ hex 打印还是坏的(输出:$(echo "$out" | grep -i FLOAT | head -2 | tr '\n' ' '))"
            return
            ;;
    esac
    # ② 0.1 ⇒ 0x3fb999999999999a(末尾 'a' = nib 10 ⇒ 正是坏掉的那一档)
    case "$out" in
        *0x3fb999999999999a*) : ;;
        *)
            bad "dump_float_hex" "dump 里没有 0.1 的正确位模式 0x3fb999999999999a ⇒ hex 打印还是坏的(输出:$(echo "$out" | grep -i FLOAT | head -2 | tr '\n' ' '))"
            return
            ;;
    esac
    ok "dump_float_hex(f64 位模式是合法 hex ✓)"
}

want helpers_symbols && check_helpers_symbols
want crossvolume_rename && check_crossvolume_rename
want build_o_flag && check_build_o_flag
want link_section    && check_link_section
want link_section_build && check_link_section_build
want asm_before_ret  && check_asm_before_ret
want naked_symbol   && check_naked_symbol
want no_std_any_cwd && check_no_std_any_cwd
want holds_bitmap    && check_holds_bitmap
want holds_cap_source && check_holds_cap_source
want selfhost_target_flag && check_selfhost_target_flag
want per_fn_frame    && check_per_fn_frame
want frame_bloat     && check_frame_bloat
want frame_slots     && check_frame_slots
want sysv_mixed_struct && check_sysv_mixed_struct
want sysv_memory_class && check_sysv_memory_class
want sysv_arg_spill  && check_sysv_arg_spill
want many_functions   && check_many_functions
want compiler_icon    && check_compiler_icon
want program_icon     && check_program_icon
want run_cmd          && check_run_cmd
want link_entry_diag  && check_link_entry_diag
want dump_float_hex   && check_dump_float_hex

echo
echo "=== artifact_checks 结果: $PASS_N PASS / $KNOWN_N KNOWN-FAIL / $FAIL_N FAIL / $SKIP_N SKIP ==="
if [ "$SKIP_N" -gt 0 ]; then
    echo "  未跑成(什么都没验到,不算绿): ${SKIPPED[*]}"
fi
if [ "$KNOWN_N" -gt 0 ]; then
    echo "  在位的已知问题(见 docs/internal/workarounds.md):"
    for k in "${KNOWN[@]}"; do echo "    - $k"; done
fi
if [ "$FAIL_N" -gt 0 ]; then
    echo
    echo "  ❌ 红项: ${FAILED[*]:-none}"
    echo "  这**不是**已知问题的常规状态。红只有三种来源:"
    echo "    · FAIL(env)        环境/编译失败 —— 什么都没验到"
    echo "    · FAIL(未登记)      新 bug,或新 check 忘了在 KNOWN_FAIL 里登记"
    echo "    · FAIL(签名不吻合)   已登记的 check 换了失败方式 —— 新 bug 躲在旧 bug 后面"
    echo "    · UNEXPECTED-PASS    workaround 修好了但登记没删 —— 去 workarounds.md 核实后"
    echo "                        删掉 KNOWN_FAIL 里对应那一行,check 自动升级成真门"
    exit 1
fi
echo
echo "  ✅ 无 FAIL、无 UNEXPECTED-PASS。"
echo "  已知问题在 KNOWN_FAIL 里登记着,它们的存在是**预期状态**,不计红。"
exit 0
