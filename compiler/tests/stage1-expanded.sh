#!/bin/bash
# stage1-expanded.sh — v0.9 wip commit 2.5
# Stage 1 byte-equal baseline verification across v0 (jhyy_0) and jhyy_v1.
# 每个测试: jhyy_0 compile --no-link vs jhyy_1 compile --no-link → diff 必须空。
#
# ⚠️ 2026-10-30 修:原脚本用 `build ... -o`,但 `cmd_build` **不解析 `-o`**
# (usage 串写着支持,实现漏了)⇒ 产物落在 input 同目录,而脚本去 OUT_DIR 找
# ⇒ v0_actual 永远不存在 ⇒ cmp 必然 FAIL(7 个测试全红)。
# 同时原脚本比的是 `.il`,而 in-mem 后端默认不落 .il ⇒ 也要改成比 `.s`。

set -u

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN_DIR="$ROOT/compiler/build/bin"
JHY_0="${BIN_DIR}/jhyy.exe"
# ⚠️ 自举二进制真名是 jhyy_v1.exe.exe (双 .exe), 不是 jhyy_v1.exe。
# 之前写错成 jhyy_v1.exe + stderr 被 2>/dev/null 吞掉 → v1 侧从来没构建成功过,
# cmp 拿的是 examples/ 里上次跑剩下的陈旧 .il, 7 个结果全部无意义。
JHY_1="${BIN_DIR}/jhyy_v1.exe.exe"
EXAMPLES_DIR="$ROOT/compiler/tests/examples"
OUT_DIR="/tmp/stage1-expanded"

for b in "$JHY_0" "$JHY_1"; do
    if [ ! -x "$b" ]; then
        echo "[ERROR] compiler not found: $b"
        exit 1
    fi
done

# 测试集 — B 阶段 byte-equal 验证
TESTS=(
    "hello"
    "fib_renamed"
    "struct_val_pass"
    "match_exhaustive"
    "arith"
    "const_array"
    "control_flow"
)

mkdir -p "$OUT_DIR"
cd "$OUT_DIR" || exit 1

pass=0
fail=0
failed_tests=()

echo "=== Stage 1 byte-equal baseline (B 阶段) ==="
echo

for t in "${TESTS[@]}"; do
    src="${EXAMPLES_DIR}/${t}.jhyy"
    v0_actual="${OUT_DIR}/${t}_v0_tmp.s"
    v1_actual="${OUT_DIR}/${t}_v1_tmp.s"

    # 先删干净: 构建失败时要么没文件(loud FAIL), 要么就是本次产物 —
    # 绝不能拿上一次遗留的陈旧产物去比对。
    rm -f "$v0_actual" "$v1_actual"

    # ⚠️ 用 `compile --no-link` 而不是 `build`:
    #   (2026-10-30 W-168 修后 `jhyy build` 已支持 `-o`,但**仍不能**替代本段 ——
    #    `cmd_compile` 产出 .s 后还会跑 `apply_link_section_directives`
    #    (W-112 的 `#[link_section]` 处理),`cmd_build` 不跑 ⇒ 含该属性的程序
    #    两条路径的 .s 不同。)
    #   这也是项目既有的惯用法(compiler/tests/bootstrap/closure_check.sh)。
    if ! "${JHY_0}" compile --no-link "${src}" -o "${t}_v0_tmp" >/dev/null 2>"$OUT_DIR/${t}_v0.err"; then
        echo "[FAIL] $t — v0 compile failed:"
        head -3 "$OUT_DIR/${t}_v0.err" | sed 's/^/       /'
        fail=$((fail+1)); failed_tests+=("$t"); continue
    fi
    if ! "${JHY_1}" compile --no-link "${src}" -o "${t}_v1_tmp" >/dev/null 2>"$OUT_DIR/${t}_v1.err"; then
        echo "[FAIL] $t — v1 compile failed:"
        head -3 "$OUT_DIR/${t}_v1.err" | sed 's/^/       /'
        fail=$((fail+1)); failed_tests+=("$t"); continue
    fi

    if cmp -s "$v0_actual" "$v1_actual"; then
        echo "[PASS] $t"
        pass=$((pass+1))
    else
        echo "[FAIL] $t"
        echo "       v0:  $v0_actual"
        echo "       v1:  $v1_actual"
        diff "$v0_actual" "$v1_actual" 2>/dev/null | head -5
        fail=$((fail+1))
        failed_tests+=("$t")
    fi
done

echo
echo "=== summary ==="
echo "pass: $pass / ${#TESTS[@]}"
echo "fail: $fail"
if [ $fail -gt 0 ]; then
    echo "failed: ${failed_tests[*]}"
    exit 1
fi
echo "✓ Stage 1 byte-equal baseline locked"