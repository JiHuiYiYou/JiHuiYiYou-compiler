#!/bin/bash
# stage1-expanded.sh — v0.9 wip commit 2.5
# Stage 1 byte-equal baseline verification across v0 (jhyy_0) and jhyy_v1.
# 每个测试: jhyy_0 build vs jhyy_1 build → diff 必须空。

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
    v0_actual="${OUT_DIR}/${t}_v0_tmp.il"
    # jhyy_v1 的 cmd_build 不解析 -o, 固定写到 input 同目录 <basename>.il
    v1_actual="${EXAMPLES_DIR}/${t}.il"

    # 先删干净: 构建失败时要么没文件(loud FAIL), 要么就是本次产物 —
    # 绝不能拿上一次遗留的陈旧 .il 去比对。
    rm -f "$v0_actual" "$v1_actual"

    if ! "${JHY_0}" build "${src}" -o "${t}_v0_tmp" >/dev/null 2>"$OUT_DIR/${t}_v0.err"; then
        echo "[FAIL] $t — v0 build failed:"
        head -3 "$OUT_DIR/${t}_v0.err" | sed 's/^/       /'
        fail=$((fail+1)); failed_tests+=("$t"); continue
    fi
    if ! "${JHY_1}" build "${src}" -o "${t}_v1_tmp" >/dev/null 2>"$OUT_DIR/${t}_v1.err"; then
        echo "[FAIL] $t — v1 build failed:"
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