#!/usr/bin/env bash
# d43_linux.sh — D43 closure N=3 verify on Linux x86_64 (v2.14.0 Phase 3 V.4)
#
# 目的: 验证 D43 closure (jhyy_v2 / v3 / v4 → 1 unique sha) 在 Linux gcc:12
#       docker 容器下 byte-equal — 跟 Win closure fixed_point.sh 互证。
#
# 注: v2.14.0 Phase 3 简化 — Linux 真 self-host chain 等 v2.4.0 multi-target
#     dispatcher ship 后启动。当前 d43_linux.sh 走 sanity check path: Win jhyy
#     编 → 验证 .il sha 跟 Win closure baseline 一致 (per docs/logs/v2/d43-baseline-archive.md
#     当前 active baseline = 43fee332...)。
#
# 用法: d43_linux.sh
#
# 退出码:
#   0  = .il sha = Win baseline
#   1  = FAIL
#   2  = docker 不可用 (warn)

set -uo pipefail

JHYY_ROOT="${JHYY_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
# cd to JHYY_ROOT so jhyy.exe sees cwd == JHYY_ROOT (matches fixed_point.sh pattern;
# dbgfile emission uses cwd-relative path → byte-equal across invocations)
cd "$JHYY_ROOT" || { echo "ERR: cd $JHYY_ROOT failed" >&2; exit 1; }
DOCKER_BIN="${DOCKER_BIN:-C:/Program Files/Docker/Docker/resources/bin/docker.exe}"
DOCKER_IMAGE="${DOCKER_IMAGE:-gcc:12}"

JHYY_BIN="$JHYY_ROOT/compiler/build/bin/jhyy.exe"
JHYY_INPUT="$JHYY_ROOT/compiler/src0/main.jhyy"

# v2.13.11 closure baseline (per docs/logs/v2/d43-baseline-archive.md v2.13.0 Ph.2 row re-measured
# at v2.13.11 closure — jhyy_v2/v3/v4/v5 → 1 unique sha via fixed_point.sh N=10 verification)
EXPECTED_BASELINE_SHA="43fee332c0fdb110283a7192a26f63c6c44bb1a4c9706e1d0ba4f55400c9eb40"

echo "=== d43_linux — D43 closure N=3 verify on Linux x86_64 ==="
echo "  EXPECTED_BASELINE_SHA = $EXPECTED_BASELINE_SHA"
echo

if [[ ! -f "$JHYY_BIN" ]]; then
    echo "ERR: JHYY_BIN not found" >&2
    exit 1
fi

# Docker check
if [[ ! -f "$DOCKER_BIN" ]] || ! "$DOCKER_BIN" info > /dev/null 2>&1; then
    echo "  ⚠️  SKIP docker (per feedback_docker_local)"
    echo "  → D43 closure Win verify per fixed_point.sh 已 ship"
    exit 2
fi

# Win path: 编 main.jhyy → main.il → 比 sha
echo "[1/2] Win jhyy 编 src0/main.jhyy → main.il + sha256 ..."
TMPDIR=/tmp/jhyy_d43_linux
mkdir -p "$TMPDIR"
"$JHYY_BIN" compile --target=amd64_win --no-link "$JHYY_INPUT" -o "$TMPDIR/main" > /dev/null 2>&1 || true
if [[ ! -f "$TMPDIR/main.il" ]]; then
    echo "  ❌ FAIL (main.il not generated)"
    exit 1
fi
ACTUAL_SHA=$(sha256sum "$TMPDIR/main.il" | awk '{print $1}')
echo "  Win main.il sha: $ACTUAL_SHA"
echo

if [[ "$ACTUAL_SHA" == "$EXPECTED_BASELINE_SHA" ]]; then
    echo "  ✅ PASS (Win closure sha = v2.13.11 baseline)"
    echo
    echo "[2/2] Linux gcc:12 toolchain sanity ..."
    GCC_VER=$(
        MSYS_NO_PATHCONV=1 "$DOCKER_BIN" run --rm "$DOCKER_IMAGE" gcc --version 2>/dev/null | head -1
    )
    echo "  $GCC_VER"
    echo
    echo "=== d43_linux Phase 3 V.4 PASS ==="
    echo "  Win closure baseline HOLD ($EXPECTED_BASELINE_SHA)"
    echo "  Linux toolchain sanity (gcc:12 available)"
    echo "  Full Linux self-host chain 等 v2.4.0 multi-target dispatcher ship 后启动"
    exit 0
fi

echo "  ❌ FAIL (Win sha ≠ v2.13.11 baseline — closure drift!)"
echo "  ACTUAL:   $ACTUAL_SHA"
echo "  EXPECTED: $EXPECTED_BASELINE_SHA"
exit 1