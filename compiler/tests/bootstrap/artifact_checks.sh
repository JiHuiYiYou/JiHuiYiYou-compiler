#!/usr/bin/env bash
# artifact_checks.sh — 产物级门:验那些**不在程序返回值里**的失效模式
#
# 2026-10-15 建(v4.0.1)。为什么需要这份:
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
# 退出码:0 = 全绿;1 = 有 FAIL;2 = 环境不可用(如需要 Docker 而没有)

set -uo pipefail

JHYY_ROOT="${JHYY_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$JHYY_ROOT" || { echo "ERR: cd $JHYY_ROOT failed" >&2; exit 2; }

JHYY_EXE="${JHYY_EXE:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"
WORK="${WORK:-$JHYY_ROOT/compiler/build/bin/_artifact_checks}"
ONLY=""

for arg in "$@"; do
    case "$arg" in
        --only=*) ONLY="${arg#*=}" ;;
        *) echo "unknown arg: $arg" >&2; exit 2 ;;
    esac
done

mkdir -p "$WORK"

PASS_N=0
FAIL_N=0
declare -a FAILED=()

hdr()  { echo; echo "── $* ──────────────────────────────────────"; }
ok()   { printf "  ✅ PASS %s\n" "$1"; PASS_N=$((PASS_N+1)); }
bad()  { printf "  ❌ FAIL %s\n    %s\n" "$1" "$2"; FAIL_N=$((FAIL_N+1)); FAILED+=("$1"); }
skip() { printf "  ⏭  SKIP %s (%s)\n" "$1" "$2"; }

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
        bad "link_section" "编译失败:$(tail -3 "$WORK/ls.log" | tr '\n' ' ')"
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
        bad "asm_before_ret" "编译失败:$(tail -3 "$WORK/asm.log" | tr '\n' ' ')"
        return
    fi
    local exe; exe=$(cygpath -w "$WORK/asm.exe" 2>/dev/null || echo "$WORK/asm.exe")
    [ -f "$exe" ] || { bad "asm_before_ret" "没产出 .exe"; return; }

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
    [ -f "$f" ] || { bad "per_fn_frame" "生成测试模块失败"; return; }

    if ! "$JHYY_EXE" compile --target=amd64_win --no-link "$f" -o "$WORK/fn" \
            > "$WORK/fn.log" 2>&1; then
        bad "per_fn_frame" "编译失败:$(tail -3 "$WORK/fn.log" | tr '\n' ' ')"
        return
    fi

    # 先取那一行,再用 grep -o 抽数字 —— 早先用 substr(RSTART+6, RLENGTH-13)
    # 把 8368 截成 836(尾部 `, %rsp` 是 6 字符,不是 7)。
    local low high ratio
    low=$(awk '/^f500:/{f=1} f && /subq \$[0-9]+, %rsp/{print; exit}' "$WORK/fn.s" | grep -oE '[0-9]+' | head -1)
    high=$(awk '/^f1099:/{f=1} f && /subq \$[0-9]+, %rsp/{print; exit}' "$WORK/fn.s" | grep -oE '[0-9]+' | head -1)
    [ -n "$low" ] && [ -n "$high" ] || { bad "per_fn_frame" "量不到帧大小(low='$low' high='$high')"; return; }

    ratio=$(( high / (low > 0 ? low : 1) ))
    if [ "$ratio" -ge 4 ]; then
        bad "per_fn_frame" "f500 帧 ${low}B vs f1099 帧 ${high}B —— ${ratio}× 膨胀(1024 上限已触发)"
        return
    fi
    ok "per_fn_frame(f500=${low}B / f1099=${high}B,比值 ${ratio}×)"
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

check_sysv_arg_spill() {
    hdr "W-116  SysV callee 参数溢出是否覆盖 6 个整数寄存器"
    [ -x "$JHYY_EXE" ] || { skip "sysv_arg_spill" "jhyy.exe 不存在"; return; }

    cat > "$WORK/sysv.jhyy" <<'EOF'
fn seven(a: i32, b: i32, c: i32, d: i32, e: i32, f: i32, g: i32) -> i32 { e }
fn main_jhyy() -> i32 { return seven(1,2,3,4,5,6,7); }
EOF
    if ! "$JHYY_EXE" compile --target=amd64_sysv_freestanding --no-link \
            "$WORK/sysv.jhyy" -o "$WORK/sysv" > "$WORK/sysv.log" 2>&1; then
        bad "sysv_arg_spill" "编译失败:$(tail -3 "$WORK/sysv.log" | tr '\n' ' ')"
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

echo "=== artifact_checks.sh — 产物级门 ==="
echo "  JHYY_ROOT = $JHYY_ROOT"
echo "  JHYY_EXE  = $JHYY_EXE"
[ -f "$JHYY_EXE" ] || { echo "ERR: jhyy.exe 不存在,先跑 make" >&2; exit 2; }

want() { [ -z "$ONLY" ] || [ "$ONLY" = "$1" ]; }

want link_section    && check_link_section
want asm_before_ret  && check_asm_before_ret
want per_fn_frame    && check_per_fn_frame
want sysv_arg_spill  && check_sysv_arg_spill

echo
echo "=== artifact_checks 结果: $PASS_N PASS / $FAIL_N FAIL ==="
if [ "$FAIL_N" -gt 0 ]; then
    echo "  失败项: ${FAILED[*]}"
    echo "  ⚠️ 这些是**已登记的 ACTIVE workaround**(见 docs/internal/workarounds.md)。"
    echo "     本门的作用是把它们从「没人验」变成「每次都红」—— FAIL 在修完之前是预期状态。"
    exit 1
fi
exit 0
