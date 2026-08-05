#!/bin/bash
# stage1-expanded.sh — v0.9 wip commit 2.5
# Stage 1 byte-equal baseline verification across v0 (jhyy_0) and jhyy_v1.
# 每个测试: jhyy_0 build vs jhyy_1 build → diff 必须空。

set -u

JHY_0="C:\\Users\\liuzhen\\Desktop\\coding\\JiHuiYiYou\\compiler\\build\\bin\\jhyy.exe"
JHY_1="C:\\Users\\liuzhen\\Desktop\\coding\\JiHuiYiYou\\compiler\\build\\bin\\jhyy_v1.exe"
EXAMPLES_DIR="C:\\Users\\liuzhen\\Desktop\\coding\\JiHuiYiYou\\compiler\\tests\\examples"
OUT_DIR="/tmp/stage1-expanded"

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
    src="${EXAMPLES_DIR}\\${t}.jhyy"
    v0_il="${OUT_DIR}/${t}_v0.il"
    v1_il="${OUT_DIR}/${t}_v1.il"

    # v0 build
    "${JHY_0}" build "${src}" -o "${t}_v0_tmp" >/dev/null 2>&1
    # jhyy_v1 build (cmd_build 不解析 -o, 写到 input 同目录 .il)
    "${JHY_1}" build "${src}" -o "${t}_v1_tmp" >/dev/null 2>&1

    # v0 自动加 .il 后缀 (hello_v0_tmp.il)
    # jhyy_v1 写到 input 同目录 <basename>.il
    v0_actual="${OUT_DIR}/${t}_v0_tmp.il"
    v1_actual="${EXAMPLES_DIR}\\${t}.il"

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