#!/usr/bin/env bash
# bench.sh — 运行时性能测量的**入口别名**
#
# ⚠️ 2026-10-29:本脚本**不再自己实现计时**。
#
# 旧实现(2026-08-24 写)的计时器是坏的:
#   · `t=$(/usr/bin/time -f "%e" "$prog" > /dev/null 2>&1; ...)` —— `2>&1` 把
#     /usr/bin/time 写往 stderr 的输出一起吞了 ⇒ `t` 恒为空
#   · 于是每次都回落到 fallback:`date +%s.%N` —— 而 **MSYS2 的这个时钟不可靠**
#     (实测 `sleep 1.0` 被量成 1.445~1.756 秒,误差 45%~76%)
#   · 再叠上 MSYS2 bash 里 spawn 一个 Windows exe 的巨大开销
#     (同一个 gcc -O2 的 fib:旧脚本量 197ms,真实值 55ms)
#   · 而且它**只计时不验输出** —— 程序输出全错也算「跑成功」
#
# ⇒ 旧脚本记下的基线(fib 1.399x / ack 0.596x / nq 1.020x)**不可信**。
#
# 现在:全部委托给 `scripts/dev/bench/runtime_perf.py`
#   · CPython `time.perf_counter()` → Win32 QueryPerformanceCounter
#   · **先逐字比对 gcc 产物的 stdout**,不一致直接 FAIL
#   · 额外统计静态指标(指令数 / 访存数 / 帧大小 / chkstk 次数)—— 确定性 ⇒ 可做 CI 硬门
#
# 用法(与旧版兼容):
#   bash bench.sh            # 报告模式(永远 exit 0)
#   bash bench.sh --report   # 同上
#   bash bench.sh --strict   # 门模式(超阈值 exit 1)
#
# 退出码: 0 = PASS / 1 = FAIL / 2 = 环境或 setup 错误
#
# 新用法(推荐,能力更多):
#   python scripts/dev/bench/runtime_perf.py [--report|--strict|--ci|--quick]
#   python scripts/dev/bench/runtime_perf.py --update-baseline
#
# 可信基线与消融实验见:
#   docs/perf/self-backend-baseline-2026-10-29.md
# 计划见:
#   docs/plans/v4/self-backend-perf-plan.md

set -u

MODE="${1:---report}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PERF_PY="$REPO_ROOT/scripts/dev/bench/runtime_perf.py"

if [[ "$MODE" != "--report" && "$MODE" != "--strict" ]]; then
    echo "Usage: bash bench.sh [--report|--strict]" >&2
    echo "  (更完整的能力见: python scripts/dev/bench/runtime_perf.py --help 见脚本头注释)" >&2
    exit 2
fi

# ── 找 python ──
# 优先 python3 / python;都没有再试本机的 miniconda3(MSYS2 的 python 没 pip,
# 但本脚本只用标准库,MSYS2 的 python 也够用)。
PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    for c in "/c/Users/liuzhen/miniconda3/python.exe" \
             "/c/Users/liuzhen/AppData/Local/Programs/Python/Python313/python.exe"; do
        if [ -x "$c" ]; then PY="$c"; break; fi
    done
fi
if [ -z "$PY" ]; then
    echo "ERROR: python not found (need python3 or python on PATH)" >&2
    exit 2
fi

exec "$PY" "$PERF_PY" "$MODE"
