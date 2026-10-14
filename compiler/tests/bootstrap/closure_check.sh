#!/usr/bin/env bash
# closure_check.sh — 自举闭环 gate:Stage 2 与 Stage 3 必须产出 byte-identical .s
#
# 这是 W-097 收尾的**真判定条件**。之前缺这个门,导致 2026-10-13 一整天连续
# 修 8 个互相掩盖的 emit 缺陷(storeb 不识别 / callee 不读第 5+ 栈传参 /
# t* 参数名误判 / cg_find_arg_idx 匹配前缀 / cg_query_fn_returns_ptr 循环依赖 /
# cg_expr 结构体按值返回 / emit_call subq $32 踩栈帧 ...),而 regress 全程绿。
#
# regress 抓不到这一类:regress 跑的是"最终 .exe 行为对不对",而闭环要问的是
# "编译器对自己编译的结果,和上一代编译器编译自己的结果,是否逐字节相同"。
#
# 原理:
#   Stage N+1 = (Stage N 二进制) compile src0/main.jhyy
#   若 Stage N 的 codegen 是正确的,它的输出 = Stage N+1 的输出(不动点)
#   v2 = jhyy.exe    compile main.jhyy   →  v2.s
#   v3 = jhyy_v2.exe  compile main.jhyy   →  v3.s
#   闭环 ⟺ v2.s == v3.s
#
# 退出码: 0 = PASS(闭环), 1 = FAIL(未闭环), 2 = 环境/用法错误
#
# 用法: closure_check.sh [--keep]
#   JHYY_BIN = Stage 1 二进制路径 (default: compiler/build/bin/jhyy.exe)

set -uo pipefail

KEEP=0
[[ "${1:-}" == "--keep" ]] && KEEP=1

JHYY_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
JHYY_BIN="${JHYY_BIN:-$JHYY_ROOT/compiler/build/bin/jhyy.exe}"
SRC="$JHYY_ROOT/compiler/src0/main.jhyy"

if [[ ! -f "$JHYY_BIN" ]]; then
    echo "closure_check: Stage1 binary not found: $JHYY_BIN" >&2
    exit 2
fi
if [[ ! -f "$SRC" ]]; then
    echo "closure_check: main.jhyy not found: $SRC" >&2
    exit 2
fi

WORK="$(mktemp -d)"
cleanup() { [[ $KEEP -eq 1 ]] || rm -rf "$WORK"; }
trap cleanup EXIT

echo "=============================================================="
echo " 自举闭环 gate — Stage2 vs Stage3 .s byte-equality"
echo "=============================================================="
echo "  Stage1 : $JHYY_BIN"
echo "  source : compiler/src0/main.jhyy"
echo

# ── [1/2] Stage 2:Stage1 二进制编 main.jhyy ──────────────────────────
echo "[1/2] Stage2 = $JHYY_BIN compile main.jhyy ..."
"$JHYY_BIN" compile "$SRC" --no-link -o "$WORK/v2" >"$WORK/v2.log" 2>&1
V2_RC=$?
if [[ $V2_RC -ne 0 || ! -s "$WORK/v2.s" ]]; then
    echo "  FAIL: Stage2 产出失败 (rc=$V2_RC),详见 $WORK/v2.log"
    [[ $KEEP -eq 1 ]] && echo "  (kept: $WORK)" || WORK=""
    exit 1
fi
echo "  v2.s: $(wc -c < "$WORK/v2.s") bytes"

# Stage 2 二进制必须是完整可执行文件(带 .exe),不是 --no-link 的 .s
V2_EXE="$WORK/v2.exe"
if [[ ! -f "$V2_EXE" ]]; then
    # jhyy 对 --no-link 只出 .s;Stage2 需要能跑的完整二进制。
    # 用非 --no-link 再跑一次拿可执行文件。
    echo "  (need runnable Stage2 binary — rebuilding without --no-link)"
    "$JHYY_BIN" compile "$SRC" -o "$WORK/v2full" >"$WORK/v2full.log" 2>&1
    V2FULL_RC=$?
    if [[ $V2FULL_RC -ne 0 || ! -f "$WORK/v2full.exe" ]]; then
        echo "  FAIL: Stage2 链接失败 (rc=$V2FULL_RC)"
        [[ $KEEP -eq 1 ]] && echo "  (kept: $WORK)" || WORK=""
        exit 1
    fi
    V2_EXE="$WORK/v2full.exe"
fi
echo "  Stage2 binary: $(wc -c < "$V2_EXE") bytes"

# Stage2 二进制必须在项目结构里(靠 argv[0] 反推 project root),拷过去
STAGE2_BIN="$JHYY_ROOT/compiler/build/bin/jhyy_closure_v2.exe"
cp "$V2_EXE" "$STAGE2_BIN" || { echo "  FAIL: 无法放置 Stage2 二进制" >&2; exit 2; }

# ── [2/2] Stage 3:Stage2 二进制编同一份 main.jhyy ───────────────────
echo "[2/2] Stage3 = Stage2 binary compile main.jhyy ..."
"$STAGE2_BIN" compile "$SRC" --no-link -o "$WORK/v3" >"$WORK/v3.log" 2>&1
V3_RC=$?
rm -f "$STAGE2_BIN"

if [[ $V3_RC -ne 0 || ! -s "$WORK/v3.s" ]]; then
    echo "  FAIL: Stage3 产出失败 (rc=$V3_RC)"
    if [[ ! -s "$WORK/v3.s" ]]; then
        echo "        → 0-byte .s(Stage2 codegen 静默失败)"
    fi
    [[ $KEEP -eq 1 ]] && echo "  (kept: $WORK)" || WORK=""
    exit 1
fi
echo "  v3.s: $(wc -c < "$WORK/v3.s") bytes"

# ── 判定 ────────────────────────────────────────────────────────────
V2_SHA=$(sha256sum "$WORK/v2.s" | cut -c1-16)
V3_SHA=$(sha256sum "$WORK/v3.s" | cut -c1-16)

echo
echo "--------------------------------------------------------------"
echo "  v2.s sha256: $V2_SHA"
echo "  v3.s sha256: $V3_SHA"
echo "--------------------------------------------------------------"

if cmp -s "$WORK/v2.s" "$WORK/v3.s"; then
    echo "PASS — 自举闭环达成 (v2 == v3, byte-identical)"
    exit 0
fi

echo "FAIL — 自举未闭环,v2 != v3"
echo
DIFFLINES=$(diff "$WORK/v2.s" "$WORK/v3.s" 2>/dev/null | grep -c '^[<>]')
DIFFLINES=${DIFFLINES:-0}
echo "  差异行数: $DIFFLINES"
echo "  首个差异:"
diff "$WORK/v2.s" "$WORK/v3.s" 2>/dev/null | head -12 | sed 's/^/    /'
if [[ $KEEP -eq 1 ]]; then
    echo "  (kept: $WORK)"
else
    WORK=""
fi
exit 1