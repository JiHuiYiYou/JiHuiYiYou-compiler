#!/usr/bin/env python3
"""runtime_perf.py — 自研后端生成代码的**运行时**性能测量(取代 bench.sh)

为什么不用 shell 计时(2026-10-29 实测):
  - MSYS2 的 `date +%s.%N` 不可靠 —— 实测 `sleep 1.0` 量成 1.445~1.756 秒
    (误差 45%~76%)。`compiler/tests/bootstrap/bench.sh` 的计时器就用它
    ⇒ 它的数字不可信。
  - MSYS2 bash 里 fork+exec 一个 Windows exe 的开销极大(实测 gcc -O2 的
    fib 被量成 197ms,真实 50ms)。
  - 本脚本用 `time.perf_counter()`(CPython → Win32 QueryPerformanceCounter)
    + 直接 Win32 CreateProcess,绕开上面两条。

三件事(旧 bench.sh 一件都没做):
  1. **验正确性** —— bench.sh 只计时,程序输出全错也算"跑成功"。
     本脚本逐个比对 jhyy 产物与 gcc 产物的 stdout,不一致直接 FAIL。
  2. **参照系用 gcc -O0** —— 对 fib/ack/nqueens 这类程序,gcc -O0 ≈ gcc -O2
     (实测 91ms vs 50ms / 24ms vs 19ms),差距几乎全在 codegen 质量而非
     优化 pass ⇒ 用 -O2 当门槛是拿错了尺子。-O2 留作报告项。
  3. **静态指标** —— 指令数 / 访存数(从 .s 与 objdump 统计)。墙钟受机器
     负载影响,静态指标稳定得多,适合做 CI 门。

用法:
  python scripts/dev/bench/runtime_perf.py            # 报告模式(永远 exit 0)
  python scripts/dev/bench/runtime_perf.py --strict    # dev 门模式(墙钟 + 静态指标)
  python scripts/dev/bench/runtime_perf.py --ci        # CI 门模式(**只**静态指标硬门)
  python scripts/dev/bench/runtime_perf.py --quick     # 只跑 fib(冒烟用)
  python scripts/dev/bench/runtime_perf.py --update-baseline   # 重写基线文件

被测题目来自 `bench/tasks/<name>/task.{c,jhyy}`(v4.3.0 起;此前内联在本脚本里)。
`bench/bench.py` 是它的超集(加题目、加工程性指标、加可发布输出),
两边共用同一份任务源码与同一个计时器 —— **不复制第二份实现**。

模式说明:
  · **墙钟**(jhyy/gcc-O0 比值)在 CI 的共享 runner 上噪声大(宿主负载不可控)
    ⇒ `--ci` 模式**只报告不拦**。要卡墙钟请在本地用 `--strict`。
  · **静态指标**(指令数 / 访存数 / 帧大小 / chkstk 次数)是编译产物的
    **确定性函数** ⇒ 同一份源码 + 同一个编译器 ⇒ 逐字节相同
    ⇒ `--ci` 拿它做硬门。基线在 `runtime_perf.baseline.json`。

环境变量:
  JHY    jhyy.exe 路径(默认 compiler/build/bin/jhyy.exe)
  GCC    gcc 路径(默认 gcc)
  THRESHOLD  墙钟门模式的倍率阈值(默认 2.0 —— 对 gcc -O0;旧 bench.sh 用 1.1
           对 gcc -O2,那个门槛在这几个程序上 gcc 自己都达不到,不可达)
  RUNS   每个程序跑几次取 min(默认 7)
  TOL    静态指标的回归容差(默认 0.02 = 2%)
"""

import json
import os
import re
import subprocess
import sys
import time
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
JHY = os.environ.get("JHY", os.path.join(REPO, "compiler", "build", "bin", "jhyy.exe"))
GCC = os.environ.get("GCC", "gcc")
THRESHOLD = float(os.environ.get("THRESHOLD", "2.0"))
RUNS = int(os.environ.get("RUNS", "7"))
BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "runtime_perf.baseline.json")
# 静态指标的回归容差。基线 0 的指标(chkstk 归零后)上限也是 0 ⇒ 任何 >0 都红。
TOL = float(os.environ.get("TOL", "0.02"))

# ── 被测程序:C 版与 jhyy 版语义等价,输出逐字相同(本脚本据此验正确性) ──
#
# v4.3.0:源码从 `bench/tasks/<name>/task.{c,jhyy}` 读,不再内联在本脚本里。
# 为什么:同一道题在两个 harness 里各存一份 ⇒ 必然漂移 ⇒ 两边测的其实是不同的东西。
# `bench/tasks/` 是**唯一真源**;`bench/bench.py`(对外发布用的那套)也从这里读。
#
# ⚠️ 搬迁**必须零影响**:源码逐字相同 ⇒ 生成的 .s 逐字节相同 ⇒
# `runtime_perf.baseline.json` 一个字节都不用改。这是"搬迁没搞坏东西"的廉价证明。
BENCH_TASKS = os.path.join(REPO, "bench", "tasks")

# 本脚本(`perf` 门)拥有的题目 —— 它们的静态指标基线在
# `scripts/dev/bench/runtime_perf.baseline.json`,**由本脚本独家判**。
#
# ⚠️ 为什么是固定列表而不是"目录里有什么就跑什么":
#   `bench/tasks/` 会随新题目增长。若本脚本也跟着跑,新题目的基线就得写进
#   本文件 ⇒ 两道门(fib/ack/nq 的历史基线 vs 其余题目的新基线)就混在一起了。
#   ⇒ 固定列表 ⇒ 两份基线**管的任务不重叠** ⇒ 没有"改了 A 忘了改 B"的漂移。
#   ⇒ 新题目的静态指标由 `bench/bench.py`(`bench-perf` 门)判。
LEGACY_TASKS = ("fib", "ack", "nq")


def load_programs():
    """从 bench/tasks/<name>/ 读成对的 (C 源码, jhyy 源码)。

    目录里没有 task.c 或 task.jhyy 的子目录一律跳过(不是任务)。
    读到的源码**逐字**使用 —— 不做任何 strip / normalize,
    否则 .s 会变、静态指标基线就会漂。
    """
    out = {}
    if not os.path.isdir(BENCH_TASKS):
        return out
    for name in sorted(os.listdir(BENCH_TASKS)):
        d = os.path.join(BENCH_TASKS, name)
        c_path = os.path.join(d, "task.c")
        j_path = os.path.join(d, "task.jhyy")
        if not (os.path.isfile(c_path) and os.path.isfile(j_path)):
            continue
        with open(c_path, encoding="utf-8") as f:
            c_src = f.read()
        with open(j_path, encoding="utf-8") as f:
            j_src = f.read()
        out[name] = (c_src, j_src)
    return out


def run(cmd, cwd=None):
    """返回 (rc, stdout_text)。"""
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, errors="replace")
    return p.returncode, p.stdout


def timeit_samples(cmd, n):
    """跑 n+1 次,返回**去掉第一轮热身**之后的 n 个墙钟样本(毫秒)。

    第一轮是热身(把产物读进 OS 文件缓存),不计入。
    返回全部样本而不是只有 min —— 对外发布要报中位数和 p95,
    只报 min 会把"运气好的一次"当成典型值。
    """
    ts = []
    for i in range(n + 1):
        t0 = time.perf_counter()
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        dt = (time.perf_counter() - t0) * 1000.0
        if i:
            ts.append(dt)
    return ts


def timeit(cmd, n):
    """min-of-n 墙钟(毫秒)。第一轮是热身,不计入。

    保留这个"只要 min"的入口是为了**不改变既有语义** ——
    CI 硬门与基线 JSON 都建立在它上面;要分位数请用 timeit_samples。
    """
    return min(timeit_samples(cmd, n))


def asm_stats(path):
    """从 .s 文本统计:指令条数 / 栈访存条数 / 帧大小 / chkstk 次数。"""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return None
    lines = src.split("\n")
    insn = 0
    mem = 0
    frames = []
    chk = 0
    for i, l in enumerate(lines):
        s = l.strip()
        if not s or s.startswith("#") or s.startswith("."):
            continue
        if s.startswith(("movl", "movq", "movw", "movb", "movzbl", "movsbl", "movzwl",
                         "add", "sub", "imul", "idiv", "cmp", "test", "set", "cmov",
                         "lea", "push", "pop", "call", "ret", "jmp", "je", "jne",
                         "jl", "jg", "le", "ge", "xor", "and", "or", "shl", "shr",
                         "sal", "sar", "clt", "cdq", "cqo", "xchg", "inc", "dec",
                         "movsd", "movss", "addsd", "subsd", "mulsd", "divsd",
                         "cvtsi2sd", "cvttsd2si", "ucomisd", "comisd", "sqrtsd")):
            insn += 1
            if "(%" in s:
                mem += 1
        m = re.match(r"subq \$(\d+), %rsp$", s)
        if m and any(lines[j].strip() == "pushq %rbp" for j in range(max(0, i - 6), i)):
            frames.append(int(m.group(1)))
        if s == "call ___chkstk_ms":
            chk += 1
    return {
        "insn": insn,
        "mem": mem,
        "frames": len(frames),
        "frame_min": min(frames) if frames else 0,
        "frame_med": sorted(frames)[len(frames) // 2] if frames else 0,
        "frame_max": max(frames) if frames else 0,
        "chkstk": chk,
    }


def load_baseline():
    if not os.path.exists(BASELINE):
        return None
    with open(BASELINE, encoding="utf-8") as f:
        return json.load(f)


def save_baseline(rows):
    """把本轮实测的静态指标写成基线文件。"""
    data = {"_note": "静态指标基线 —— 由 runtime_perf.py --update-baseline 生成。"
                      "更新基线必须写明理由(见 docs/perf/self-backend-baseline-*.md)。",
            "_metrics": ["insn", "mem", "frames", "frame_min", "frame_med",
                         "frame_max", "chkstk"],
            "_rule": "任一指标超过基线的 (1+TOL) 倍即判回归;chkstk 归零后不得再出现。"}
    for name, _r0, _r2, st, _ok in rows:
        if st:
            data[name] = {k: st[k] for k in data["_metrics"]}
    with open(BASELINE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"baseline written: {BASELINE}")


def check_static(rows, base):
    """静态指标回归检查 —— **确定性**,可做 CI 硬门。

    墙钟在共享 runner 上噪声大(且宿主负载不可控)⇒ 不能做硬门;
    指令数 / 访存数 / 帧大小 / chkstk 次数是编译产物的**确定性函数**
    ⇒ 同一份源码 + 同一个编译器 ⇒ 逐字节相同 ⇒ 可以做硬门。
    """
    problems = []
    if base is None:
        problems.append(f"基线文件不存在: {BASELINE} —— 跑一次 --update-baseline 生成")
        return problems
    for name, _r0, _r2, st, _ok in rows:
        if st is None:
            continue
        b = base.get(name)
        if not b:
            problems.append(f"{name}: 基线里没有这一项")
            continue
        for k in ("insn", "mem", "frame_med", "chkstk"):
            if k not in b:
                continue
            cur = st[k]
            lim = b[k] * (1.0 + TOL)
            # chkstk 归零后不允许再出现:基线 0 ⇒ 限值 0 ⇒ 任何 >0 都红
            if cur > lim + 1e-9:
                problems.append(
                    f"{name}.{k}: {cur} > 基线 {b[k]} 的 {1 + TOL:.0%} 上限 {lim:.1f}")
    return problems


def main():
    strict = "--strict" in sys.argv
    ci = "--ci" in sys.argv
    update = "--update-baseline" in sys.argv
    quick = "--quick" in sys.argv
    if not os.path.exists(JHY):
        print(f"ERROR: jhyy.exe not found at {JHY}", file=sys.stderr)
        return 2
    tmp = tempfile.mkdtemp(prefix="jhperf_")
    programs = load_programs()
    if not programs:
        print(f"ERROR: 找不到基准任务 —— {BENCH_TASKS} 下没有 task.c/task.jhyy 配对",
              file=sys.stderr)
        return 2
    names = ["fib"] if quick else [n for n in LEGACY_TASKS if n in programs]
    if not names:
        print(f"ERROR: {BENCH_TASKS} 下找不到本门负责的题目 {LEGACY_TASKS}",
              file=sys.stderr)
        return 2
    rows = []
    failed = False

    mode = "--strict" if strict else ("--ci" if ci else
                                      ("--update-baseline" if update else "--report"))
    print(f"runtime_perf.py — jhyy vs gcc  (mode={mode})")
    print(f"  jhyy : {JHY}")
    print(f"  gcc  : {GCC}")
    print(f"  gate : jhyy/gcc-O0 <= {THRESHOLD}x   (runs={RUNS}, min)")
    if ci:
        print(f"  CI 模式:墙钟**只报告不拦**(共享 runner 噪声大);静态指标做硬门"
              f"(容差 {TOL:.0%})")
    print("")

    for name in names:
        c_src, j_src = programs[name]
        c_path = os.path.join(tmp, name + ".c")
        j_path = os.path.join(tmp, name + ".jhyy")
        open(c_path, "w", encoding="utf-8").write(c_src)
        open(j_path, "w", encoding="utf-8").write(j_src)

        # gcc 三个优化级别
        gcc_exe = {}
        for lvl in ("0", "1", "2"):
            exe = os.path.join(tmp, f"{name}_cO{lvl}.exe")
            rc, _ = run([GCC, f"-O{lvl}", "-o", exe, c_path])
            if rc != 0:
                print(f"  {name}: gcc -O{lvl} COMPILE FAIL")
                failed = True
                break
            gcc_exe[lvl] = exe
        if len(gcc_exe) != 3:
            continue

        # jhyy 产物(jhyy 会自动加 .exe)
        j_base = os.path.join(tmp, name + "_jh")
        rc, out = run([JHY, "compile", j_path, "-o", j_base])
        j_exe = j_base + ".exe"
        if rc != 0 or not os.path.exists(j_exe):
            print(f"  {name}: jhyy COMPILE FAIL (rc={rc})\n{out}")
            failed = True
            continue

        # ── 正确性:jhyy 输出必须与 gcc 输出逐字相同 ──
        _, c_out = run([gcc_exe["0"]])
        _, j_out = run([j_exe])
        if c_out.strip() != j_out.strip():
            print(f"  {name}: OUTPUT MISMATCH")
            print(f"    gcc : {c_out.strip()!r}")
            print(f"    jhyy: {j_out.strip()!r}")
            failed = True
            continue

        t = {"jhyy": timeit([j_exe], RUNS)}
        for lvl in ("0", "1", "2"):
            t[lvl] = timeit([gcc_exe[lvl]], RUNS)

        s_path = j_base + ".s"
        st = asm_stats(s_path)

        r_o0 = t["jhyy"] / t["0"] if t["0"] else float("nan")
        r_o2 = t["jhyy"] / t["2"] if t["2"] else float("nan")
        ok = r_o0 <= THRESHOLD
        # 墙钟不达标:dev 用 --strict 时算失败;CI 用 --ci 时**只报告**(共享 runner
        # 噪声大,而且宿主负载不可控 ⇒ 拿它当硬门只会制造假红)
        if not ok and strict:
            failed = True
        print(f"  {name}: gcc-O0 {t['0']:7.1f}ms  gcc-O1 {t['1']:7.1f}ms  "
              f"gcc-O2 {t['2']:7.1f}ms  jhyy {t['jhyy']:7.1f}ms   "
              f"jhyy/O0 = {r_o0:5.2f}x  jhyy/O2 = {r_o2:5.2f}x  "
              f"[{'PASS' if ok else 'FAIL'}]")
        if st:
            print(f"          .s: insn={st['insn']} mem={st['mem']} "
                  f"frames={st['frames']} (min={st['frame_min']} med={st['frame_med']} "
                  f"max={st['frame_max']}) chkstk={st['chkstk']}")
        rows.append((name, r_o0, r_o2, st, ok))

    print("")
    print(f"{'program':8} {'jhyy/O0':>9} {'jhyy/O2':>9} {'insn':>7} {'mem':>6} "
          f"{'chkstk':>7}  status")
    for name, r_o0, r_o2, st, ok in rows:
        ins = st["insn"] if st else 0
        mem = st["mem"] if st else 0
        ck = st["chkstk"] if st else 0
        print(f"{name:8} {r_o0:8.2f}x {r_o2:8.2f}x {ins:7} {mem:6} {ck:7}  "
              f"{'PASS' if ok else 'FAIL'}")

    # ── 静态指标回归门(确定性 ⇒ 可做 CI 硬门)────────────────────────
    base = load_baseline()
    static_problems = check_static(rows, base)
    print("")
    if static_problems:
        print("静态指标回归:")
        for p in static_problems:
            print(f"  ❌ {p}")
    else:
        print(f"静态指标: 全部在基线的 {1 + TOL:.0%} 容差内 ✅")

    if update:
        save_baseline(rows)
        print("")
        print("RESULT: 基线已更新(--update-baseline)。**更新基线必须写明理由。**")
        return 0

    if ci:
        print("")
        if failed:
            print("RESULT: FAIL (编译/正确性检查没过)")
            return 1
        if static_problems:
            print(f"RESULT: FAIL ({len(static_problems)} 项静态指标回归)")
            return 1
        print(f"RESULT: PASS (静态指标无回归;墙钟只报告 —— 阈值 {THRESHOLD}x)")
        return 0

    print("")
    if strict:
        if failed or static_problems:
            print("RESULT: FAIL")
            return 1
        print(f"RESULT: PASS (all jhyy/gcc-O0 <= {THRESHOLD}x;静态指标无回归)")
        return 0
    # 报告模式:永远 exit 0,但**必须说清楚哪些超了** —— 报告模式不是「一切正常」
    over = [n for n, r0, _r2, _st, _ok in rows if r0 > THRESHOLD]
    if over:
        print(f"RESULT: REPORT — {len(over)}/{len(rows)} 个程序超墙钟阈值 "
              f"{THRESHOLD}x({', '.join(over)});报告模式不阻塞")
    else:
        print(f"RESULT: REPORT — 全部在墙钟阈值 {THRESHOLD}x 内")
    if static_problems:
        print(f"          ⚠️ 另有 {len(static_problems)} 项静态指标回归(见上)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
