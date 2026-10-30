#!/usr/bin/env bash
# self_host_bench.sh — Measure JHYY self-hosting compile time
# Mirrors TPV's "self-hosting 2 min" and "+ llc + link 2:50" framing.
#
# Usage: bash scripts/dev/bench/self_host_bench.sh
#
# ⚠️ 本脚本是**纯报告**工具 —— CI 的性能门是 `runtime_perf.py --ci`
#    (静态指标:指令数 / 访存数 / 帧大小 / chkstk 次数,基线在
#    `scripts/dev/bench/runtime_perf.baseline.json`)。本脚本只出墙钟时间,
#    不喂任何门 ⇒ 改它不会动 CI 结论。

set -u
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

JHYV_BIN="./compiler/build/bin/jhyy.exe"          # current jhyy-side production
JHYV_V1="./compiler/build/bin/jhyy_v1.exe.exe"    # jhyy.exe 的同内容副本
MAIN="compiler/src0/main.jhyy"

# 产物落 `compiler/build/bench/`(build 树内 ⇒ 被 .gitignore 的
# `compiler/build/*` 命中,`make clean` 也会清掉)。**不要落在
# compiler/src0/** —— 那是源码目录。
#
# 2026-10-30:此前本脚本不传 `-o`,产物直接写在 `compiler/src0/main.s`
# (12.8 MB)—— 源码目录被编译产物污染。现全部走 `-o`。
OUT_DIR="compiler/build/bench"
OUT_BUILD="$OUT_DIR/build/main"      # A 段(不链接)
OUT_COMPILE="$OUT_DIR/compile/main"  # B 段(链接)

mkdir -p "$(dirname "$OUT_BUILD")" "$(dirname "$OUT_COMPILE")"

# run3 <label> <cmd...> — 3 runs, take min, also print all 3 raw values
run3() {
    local label="$1"; shift
    local -a times
    # warmup
    bash -c "$*" >/dev/null 2>&1 || true
    for i in 1 2 3; do
        local t
        t=$( { /usr/bin/time -f "%e" bash -c "$* >/dev/null 2>/dev/null" ; } 2>&1 | tr -d '\n' )
        times+=("$t")
    done
    # min
    local mn
    mn=$(printf '%s\n' "${times[@]}" | sort -g | head -1)
    printf "%-50s | runs=%s,%s,%s  min=%s\n" "$label" "${times[0]}" "${times[1]}" "${times[2]}" "$mn"
}

# ── A 段:前端(lex→parse→sema→codegen→emit .s),不链接 ──
#
# ⚠️ 为什么用 `compile --no-link` 而不是 `build`:
#   `jhyy build` **不解析 `-o`**(usage 串写着支持,实现漏了)⇒ 产物必定落在
#   input 同目录,没法重定向。而 `compile --no-link` 支持 `-o`,且产出的 .s
#   与 `build` **逐字节相同**(实测 13,427,368 B 完全一致)⇒ 测的是同一件事。
#   这也是项目既有的惯用法 —— `compiler/tests/bootstrap/closure_check.sh`
#   用的正是 `compile --no-link -o`。
echo "===== A. jhyy compile --no-link (codegen only, no gcc link) ====="
run3 "A1 jhyy.exe       compile --no-link src0/main.jhyy"  "$JHYV_BIN compile --no-link $MAIN -o $OUT_BUILD"
run3 "A2 jhyy_v1.exe    compile --no-link src0/main.jhyy"  "$JHYV_V1 compile --no-link $MAIN -o $OUT_BUILD"

echo
echo "===== B. jhyy compile (full pipeline: codegen + gcc link) ====="
run3 "B1 jhyy.exe       compile src0/main.jhyy"  "$JHYV_BIN compile $MAIN -o $OUT_COMPILE"
run3 "B2 jhyy_v1.exe    compile src0/main.jhyy"  "$JHYV_V1 compile $MAIN -o $OUT_COMPILE"

# ── C 段(QBE)已删除 ──
# 2026-10-30:本脚本此前有一段「C. QBE step alone」,跑
#   `./qbe/qbe.exe -t amd64_win compiler/src0/main.il > main.s`
# 那段**测的是空气**,三重失效:
#   ① QBE 已在 v2.16.0 从编译器里完全移除(现在是 in-mem 自研后端),
#      它不再是编译器的任何一步;
#   ② `compiler/src0/main.il` 默认根本不存在 —— in-mem 后端默认不落 .il
#      (只有 JHY_WRITE_IL=1 才落),所以前置的「jhyy build 补生成」也补不出来;
#   ③ 实测 qbe 对不存在的文件 exit 1 + "cannot open" + 产出 0 字节 ⇒
#      run3 报的那个耗时是**进程启动时间**,不是编译时间。
# ⇒ 整段删除;`qbe/` 目录也一并从仓里删掉(见 docs/internal/workarounds.md)。

echo
echo "===== File sizes ====="
ls -la "$OUT_BUILD.s" "$OUT_COMPILE.s" "$OUT_COMPILE.exe" 2>/dev/null | awk '{print $5, $9}'
echo
echo "产物目录: $OUT_DIR   (build 树内,被 .gitignore 命中;'make clean' 会清掉)"
