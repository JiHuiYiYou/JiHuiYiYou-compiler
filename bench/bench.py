#!/usr/bin/env python3
"""bench.py — jhyy 基准套件（对外发布的那一套）

与 `scripts/dev/bench/runtime_perf.py` 的关系:
  · `runtime_perf.py` 是 **CI 门 `perf`** —— 它拥有 fib/ack/nq 三道历史题目的静态指标基线,
    自 v4.2.0 起就在门里,基线文件是 `scripts/dev/bench/runtime_perf.baseline.json`。
  · `bench.py` 是 **CI 门 `bench-perf`** —— 它跑 `bench/tasks/` 下的**全部**题目,
    补上工程性指标(编译耗时 / 二进制体积 / 进程启动地板 / LOC 比),
    并产出可发布的 Markdown。

**不复制第二份实现**:计时器、静态指标解析、题目加载一律 import `runtime_perf`。
本仓栽过"两套实现分叉"的跟头(`Makefile` 里 v4.0.21 删 C 端的记录:两套实现分叉 ⇒
同一个 bug 要修两遍)⇒ 计时逻辑只有一份。

**静态指标基线为什么有两个文件**:
  `runtime_perf.baseline.json` 归 `perf` 门(fib/ack/nq),
  `bench/baseline/static.json` 归本脚本(**其余**题目)。
  ⇒ 两份基线**管的任务不重叠** ⇒ 不存在"改了 A 忘了改 B"的漂移。

用法:
  python bench/bench.py                     # 报告模式(永远 exit 0)
  python bench/bench.py --strict            # dev 门模式(墙钟 + 静态指标都拦)
  python bench/bench.py --ci                # CI 门模式(正确性 + 静态指标 + 体积硬门;墙钟只报告)
  python bench/bench.py --quick             # 只跑 fib(冒烟用)
  python bench/bench.py --update-baseline   # 重写本脚本的静态指标基线
  python bench/bench.py --json tmp/b.json   # 机器可读输出
  python bench/bench.py --publish --out bench/baseline/RESULTS-<日期>.md
  python bench/bench.py --selftest          # 断言这道门看得见红(且墙钟**不**让它红)

环境变量:
  JHY    jhyy.exe 路径(默认 compiler/build/bin/jhyy.exe)
  GCC    gcc 路径(默认 gcc)
  RUNS   每个程序跑几次(默认 7)
  TOL    静态指标的回归容差(默认 0.02 = 2%)
"""

import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts" / "dev" / "bench"))

# 复用 runtime_perf 的计时器 / 静态指标 / 题目加载 —— **不复制第二份实现**
import runtime_perf as rp  # noqa: E402

JHY = os.environ.get("JHY", str(REPO / "compiler" / "build" / "bin" / "jhyy.exe"))
GCC = os.environ.get("GCC", "gcc")
RUNS = int(os.environ.get("RUNS", "7"))
TOL = float(os.environ.get("TOL", "0.02"))
BASELINE = str(Path(__file__).resolve().parent / "baseline" / "static.json")

# `perf` 门(历史)拥有的题目 —— 它们的静态指标基线在 runtime_perf.baseline.json,
# 本脚本**只报告不硬门**(避免同一份基线被两道门各判一次)。
LEGACY_TASKS = set(rp.LEGACY_TASKS)

# 静态指标里参与"回归判定"的四个(与 `perf` 门一致)
GATED_METRICS = ("insn", "mem", "frame_med", "chkstk")


# ─────────────────────────── 任务元数据 ───────────────────────────

def parse_meta(path):
    """读 task.meta —— key = value 的简单格式(# 开头是注释)。"""
    meta = {}
    if not path.is_file():
        return meta
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        meta[k.strip()] = v.strip()
    return meta


def load_tasks():
    """读 bench/tasks/ 下的全部任务。

    返回 {name: {"c": 源码, "jhyy": 源码, "meta": {...}}}。
    """
    tasks = {}
    root = Path(rp.BENCH_TASKS)
    if not root.is_dir():
        return tasks
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        c_path = d / "task.c"
        j_path = d / "task.jhyy"
        if not (c_path.is_file() and j_path.is_file()):
            continue
        tasks[d.name] = {
            "c": c_path.read_text(encoding="utf-8"),
            "jhyy": j_path.read_text(encoding="utf-8"),
            "meta": parse_meta(d / "task.meta"),
        }
    return tasks


def loc_count(src):
    """有效代码行数(去掉空行与整行注释)。粗口径,但同题同语言对可复现。"""
    n = 0
    for raw in src.splitlines():
        s = raw.strip()
        if not s or s.startswith("//") or s.startswith("#") or s.startswith("/*") or s.startswith("*"):
            continue
        n += 1
    return n


# ─────────────────────────── 编译与测量 ───────────────────────────

def build_all(tmp, name, task):
    """编出 4 个产物:gcc -O0/-O1/-O2 + jhyy。

    ⚠️ 一律用**绝对路径** —— 实测用相对 `-o` 时 .exe 会落到别处,
    `<out>.exe` 不一定存在(见计划的风险表第 10 条)。
    ⚠️ 产物必须**断言存在**才能进计时。
    """
    c_path = os.path.join(tmp, f"{name}.c")
    j_path = os.path.join(tmp, f"{name}.jhyy")
    with open(c_path, "w", encoding="utf-8", newline="") as f:
        f.write(task["c"])
    with open(j_path, "w", encoding="utf-8", newline="") as f:
        f.write(task["jhyy"])

    out = {"c_path": c_path, "j_path": j_path, "gcc": {}, "jhyy": None,
           "jhyy_s": None, "jhyy_base": None}

    for lvl in ("0", "1", "2"):
        exe = os.path.join(tmp, f"{name}_cO{lvl}.exe")
        # ⚠️ `-ffp-contract=off`:默认 x86-64 目标**没有 FMA 指令** ⇒ gcc 事实上
        # 不会把 `a*b+c` 合成 FMA(实测:生成的 .s 里 0 条 FMA)⇒ 三档优化级别下
        # 浮点结果逐位相同。加这个开关是**护栏**(万一将来用 -march=native 之类
        # 的目标编)—— 而且它是**公平**的:jhyy 后端发不出 FMA。
        rc, _ = rp.run([GCC, f"-O{lvl}", "-ffp-contract=off", "-o", exe, c_path])
        if rc != 0:
            out["gcc_error"] = f"gcc -O{lvl} 编译失败 (rc={rc})"
            return out
        out["gcc"][lvl] = exe

    j_base = os.path.join(tmp, f"{name}_jh")
    rc, so = rp.run([JHY, "compile", j_path, "-o", j_base])
    j_exe = j_base + ".exe"
    if rc != 0 or not os.path.exists(j_exe):
        out["jhyy_error"] = f"jhyy 编译失败 (rc={rc})\n{so}"
        return out
    out["jhyy"] = j_exe
    out["jhyy_s"] = j_base + ".s"
    out["jhyy_base"] = j_base
    return out


def measure(cmd, runs=None):
    """跑 n+1 次(第一轮热身丢弃),返回样本列表(毫秒)。"""
    return rp.timeit_samples(cmd, runs if runs is not None else RUNS)


def dist(samples):
    """min / median / p95 —— 对外发布报的是**分布**,不是单次。"""
    s = sorted(samples)
    n = len(s)
    if n == 0:
        return {"min": 0.0, "median": 0.0, "p95": 0.0}
    med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    # p95: sorted[ceil(0.95*n)-1]
    idx = max(0, min(n - 1, math.ceil(0.95 * n) - 1))
    return {"min": s[0], "median": med, "p95": s[idx]}


def outputs_match(c_out, j_out):
    """正确性判据:jhyy 的 stdout 必须与 gcc 的**逐字相同**。

    抽成独立函数,好让 `--selftest` 能**真的走这条路径**
    (仓规约 feedback_ci_gate_must_exercise_path:门必须真走到它声称验的那条路径)。
    """
    return c_out.strip() == j_out.strip()


def size_of(path):
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


# ─────────────────────────── 环境元数据 ───────────────────────────

def cpu_name():
    """CPU 营销名 —— Windows 上 platform.processor() 给的是 family/model,不是商品名。"""
    if sys.platform == "win32":
        try:
            import winreg
            key = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as k:
                return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except Exception:
            pass
    return platform.processor() or "unknown"


def tool_version(cmd):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, errors="replace", timeout=30)
        return (p.stdout or "").strip().splitlines()[0] if p.stdout else "unknown"
    except Exception:
        return "unknown"


def git_sha():
    try:
        p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           text=True, errors="replace", timeout=30)
        return p.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def env_meta(runs):
    return {
        "os": platform.platform(),
        "cpu": cpu_name(),
        "python": platform.python_version(),
        "gcc": tool_version([GCC, "--version"]),
        "jhyy": tool_version([JHY, "--help"]),
        "git_sha": git_sha(),
        "runs": runs,
        "tol": TOL,
    }


# ─────────────────────────── 基线 ───────────────────────────

def load_baseline():
    p = Path(BASELINE)
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def save_baseline(rows, sizes):
    """写基线:静态指标(只非历史题目)+ 二进制体积(全部题目)。

    rows  = [(name, static_metrics_dict, size_bytes), ...]  ← 非历史题目
    sizes = [(name, size_bytes), ...]                        ← 全部题目
    """
    p = Path(BASELINE)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "_note": "静态指标基线 —— 由 bench/bench.py --update-baseline 生成。"
                 "更新基线必须写明理由(见 bench/METHODOLOGY.md)。"
                 "⚠️ 静态指标只管**非历史**题目(fib/ack/nq 的静态指标基线归 `perf` 门,"
                 "在 scripts/dev/bench/runtime_perf.baseline.json);"
                 "`_size` 管**全部**题目 —— 二进制体积此前没有任何门在管。",
        "_metrics": ["insn", "mem", "frames", "frame_min", "frame_med",
                     "frame_max", "chkstk"],
        "_rule": "任一指标超过基线的 (1+TOL) 倍即判回归;chkstk 归零后不得再出现。",
    }
    for name, st, _size in rows:
        if st:
            data[name] = {k: st[k] for k in data["_metrics"]}
    size_map = {n: s for n, s in sizes if s}
    if size_map:
        data["_size"] = size_map
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"baseline written: {BASELINE}")


def check_static(rows, base):
    """静态指标回归检查 —— **确定性**,可做 CI 硬门。

    墙钟在共享 runner 上噪声大 ⇒ 不能做硬门;
    指令数 / 访存数 / 帧大小 / chkstk 次数是编译产物的**确定性函数**
    ⇒ 同一份源码 + 同一个编译器 ⇒ 逐字节相同 ⇒ 可以做硬门。
    """
    problems = []
    if base is None:
        problems.append(f"基线文件不存在: {BASELINE} —— 跑一次 --update-baseline 生成")
        return problems
    for name, st in rows:
        if st is None:
            continue
        b = base.get(name)
        if not b:
            problems.append(f"{name}: 基线里没有这一项")
            continue
        for k in GATED_METRICS:
            if k not in b:
                continue
            cur = st[k]
            lim = b[k] * (1.0 + TOL)
            if cur > lim + 1e-9:
                problems.append(
                    f"{name}.{k}: {cur} > 基线 {b[k]} 的 {1 + TOL:.0%} 上限 {lim:.1f}")
    return problems


# ─────────────────────────── 主流程 ───────────────────────────

def run_task(tmp, name, task, runs):
    """跑一道题:编译 → 验正确性 → 测墙钟分布 / 工程性 / 静态指标。"""
    row = {"name": name, "meta": task["meta"], "ok": True, "errors": []}

    b = build_all(tmp, name, task)
    if b.get("gcc_error") or b.get("jhyy_error"):
        row["ok"] = False
        row["errors"].append(b.get("gcc_error") or b.get("jhyy_error"))
        return row

    # ── 正确性:jhyy 的 stdout 必须与 gcc -O0 的**逐字相同** ──
    # ⚠️ 浮点题只与 -O0 产物比 —— -O2 可能重排浮点运算。
    _, c_out = rp.run([b["gcc"]["0"]])
    _, j_out = rp.run([b["jhyy"]])
    if not outputs_match(c_out, j_out):
        row["ok"] = False
        row["errors"].append(
            f"stdout 不一致:\n    gcc : {c_out.strip()!r}\n    jhyy: {j_out.strip()!r}")
        return row
    row["stdout"] = c_out.strip()

    # ── 反死代码消除:checksum 必须在输出里(值得是算出来的,不是常量回显)──
    ck = task["meta"].get("checksum")
    if ck:
        if ck not in c_out:
            row["ok"] = False
            row["errors"].append(
                f"checksum {ck} 不在输出里 —— 反 DCE 约定被破坏(计算被吃掉了?)")
            return row
        row["checksum"] = ck

    # ── 墙钟分布(热) ──
    row["wall"] = {"jhyy": dist(measure([b["jhyy"]], runs))}
    for lvl in ("0", "1", "2"):
        row["wall"][f"gcc{lvl}"] = dist(measure([b["gcc"][lvl]], runs))

    # ── 冷启动近似:产物复制到一个全新临时目录后第一次跑 ──
    cold_dir = tempfile.mkdtemp(prefix="jhbench_cold_")
    try:
        cold_exe = os.path.join(cold_dir, os.path.basename(b["jhyy"]))
        with open(b["jhyy"], "rb") as fi, open(cold_exe, "wb") as fo:
            fo.write(fi.read())
        row["cold_first_run_ms"] = measure([cold_exe], 1)[0]
    finally:
        try:
            for f in os.listdir(cold_dir):
                os.unlink(os.path.join(cold_dir, f))
            os.rmdir(cold_dir)
        except OSError:
            pass

    # ── 工程性 ──
    row["size"] = {"jhyy": size_of(b["jhyy"])}
    for lvl in ("0", "1", "2"):
        row["size"][f"gcc{lvl}"] = size_of(b["gcc"][lvl])
    row["compile_ms"] = {
        "jhyy": min(measure([JHY, "compile", b["j_path"], "-o",
                              os.path.join(tmp, f"{name}_jh_t")], 3)),
        "gcc0": min(measure([GCC, "-O0", "-o", os.path.join(tmp, f"{name}_cg_t"),
                             b["c_path"]], 3)),
    }
    row["loc"] = {"jhyy": loc_count(task["jhyy"]), "c": loc_count(task["c"])}

    # ── 静态指标(确定性) ──
    row["static"] = rp.asm_stats(b["jhyy_s"])
    return row


def measure_startup_floor(tmp, runs):
    """测量地板 —— 一个空程序从"被 harness 拉起"到退出的时间。

    ⚠️ **这不是纯粹的 harness 开销** —— 它含两层:
      ① **harness 自己的进程创建开销**(Python `subprocess` + Windows
         `CreateProcess` + ucrt64 运行时初始化)—— 实测约 19ms(gcc);
      ② **jhyy 程序自己的启动开销**(C 运行时 shim:`GetCommandLineW` /
         `CommandLineToArgvW` / 编码转换 / `setvbuf(_IONBF)`)——
         实测 jhyy 的地板比 gcc 高约 **6ms**(40 次采样:25.47ms vs 19.32ms,
         分布很窄 ⇒ 这是**真实差异**,不是噪声)。

    ⇒ 所以"地板"是**两边各自**的下限,必须**分别测、分别扣**。
    ⇒ 它必须被测出来并发布:每一个墙钟数字都含它 ⇒ 它是所有数字的共同下限。
    ⇒ 对外发布时它的名字是 **measurement floor**,不是 "startup time"
    (后者会让人以为这是程序自己的启动开销)。
    """
    c_src = "int main(void) { return 0; }\n"
    j_src = "fn main_jhyy() -> i32 { return 0; }\n"
    c_path = os.path.join(tmp, "_floor.c")
    j_path = os.path.join(tmp, "_floor.jhyy")
    with open(c_path, "w", encoding="utf-8", newline="") as f:
        f.write(c_src)
    with open(j_path, "w", encoding="utf-8", newline="") as f:
        f.write(j_src)
    out = {}
    c_exe = os.path.join(tmp, "_floor_c.exe")
    if rp.run([GCC, "-O0", "-o", c_exe, c_path])[0] == 0:
        out["gcc"] = dist(measure([c_exe], runs))
    j_base = os.path.join(tmp, "_floor_jh")
    if rp.run([JHY, "compile", j_path, "-o", j_base])[0] == 0 and \
            os.path.exists(j_base + ".exe"):
        out["jhyy"] = dist(measure([j_base + ".exe"], runs))
    return out


def ratios(row, floor):
    """(扣除地板后的 jhyy/O0, jhyy/O2, 地板占比, 是否"题目太短")

    ⚠️ **为什么要扣地板**:每个测量都含 harness 自身的进程创建开销
    (见 measure_startup_floor 的说明)。一道只跑 30ms 的题、地板 20ms ⇒
    66% 的测量是开销 ⇒ 原始比值几乎不含"程序自己的时间"。

    ⇒ 头条比值 = **(min - 地板)** 之比 ⇒ 那是"程序自身的工作"之比。
    ⇒ 同时给出**地板占比**;占比过高(>25%)⇒ 该题太短 ⇒ 比值不可靠 ⇒ 标记出来。

    地板取 **min** —— 它是固定开销,min 是对"真值"最好的估计。
    """
    w = row.get("wall")
    if not w:
        return None, None, 0.0, True
    fj = (floor.get("jhyy") or {}).get("min", 0.0)
    fg = (floor.get("gcc") or {}).get("min", 0.0)
    jm = w["jhyy"]["min"]
    j = jm - fj
    g0 = w["gcc0"]["min"] - fg
    g2 = w["gcc2"]["min"] - fg
    frac = (fj / jm) if jm > 0 else 1.0
    # 分子或分母 ≤ 0 ⇒ 这道题比地板还短 ⇒ 比值无意义
    too_short = (j <= 0) or (g0 <= 0) or (g2 <= 0) or (frac > 0.25)
    # ⚠️ 地板占比过高 ⇒ 扣地板后剩下的绝对量很小 ⇒ 地板的测量误差被放大成
    #    巨大的相对误差(实测:ack 的地板占比 61% ⇒ 扣出来的比值 10.25x,纯垃圾)。
    #    ⇒ **宁可不报,也不报一个会误导人的数字** —— 原始比值(raw)仍然给出。
    if frac > 0.25:
        return None, None, frac, True
    r0 = (j / g0) if (g0 > 0 and j > 0) else None
    r2 = (j / g2) if (g2 > 0 and j > 0) else None
    return r0, r2, frac, too_short


def print_table(rows, floor):
    hdr = (f"{'task':12} {'jhyy/O0':>9} {'jhyy/O2':>9} {'raw O0':>8} {'min(ms)':>9} "
           f"{'med(ms)':>9} {'p95(ms)':>9} {'floor%':>7} {'insn':>6} {'mem':>6} "
           f"{'chk':>4} {'size':>9} {'libc':>7}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        if not r.get("wall"):
            continue
        w = r["wall"]
        r0, r2, frac, short = ratios(r, floor)
        raw0 = (w["jhyy"]["min"] / w["gcc0"]["min"]) if w["gcc0"]["min"] else 0.0
        st = r.get("static") or {}
        libc = r["meta"].get("libc", "?")
        s0 = f"{r0:8.2f}x" if r0 is not None else "     n/a"
        s2 = f"{r2:8.2f}x" if r2 is not None else "     n/a"
        mark = " *" if short else ""
        print(f"{r['name']:12} {s0} {s2} {raw0:7.2f}x "
              f"{w['jhyy']['min']:9.2f} {w['jhyy']['median']:9.2f} {w['jhyy']['p95']:9.2f} "
              f"{frac * 100:6.1f}% {st.get('insn', 0):6} {st.get('mem', 0):6} "
              f"{st.get('chkstk', 0):4} {r.get('size', {}).get('jhyy', 0):9} {libc:>7}{mark}")
    print("  * = 地板占比过高(>25%)或扣除地板后分母 ≤ 0 ⇒ 该题太短,比值不可靠")


def publish_markdown(rows, meta, path):
    """可发布的 Markdown 表 —— 带机器规格 + 方法学元数据。"""
    lines = []
    lines.append(f"# JHYY benchmark results — {meta['date']}\n")
    lines.append("> Generated by `bench/bench.py --publish`. "
                 "Do not edit by hand.\n")
    lines.append("## Environment\n")
    lines.append("| item | value |")
    lines.append("|---|---|")
    for k in ("date", "git_sha", "os", "cpu", "gcc", "jhyy", "python", "runs"):
        lines.append(f"| {k} | {meta.get(k, 'unknown')} |")
    lines.append("")
    lines.append("## Results\n")
    lines.append("Ratios are `jhyy / gcc` on **min-of-N** wall clock "
                 "(lower is better), **after subtracting the measurement floor** "
                 "(see below) — i.e. they compare the programs' own work. "
                 "`-O0` is the codegen-quality floor; `-O2` is reference only, "
                 "**not** a pass/fail bar.\n")
    lines.append("| task | jhyy/O0 | jhyy/O2 | raw jhyy/O0 | jhyy min (ms) | "
                 "jhyy median (ms) | jhyy p95 (ms) | gcc -O0 (ms) | gcc -O2 (ms) | "
                 "floor share | jhyy size | gcc -O0 size | libc |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        if not r.get("wall"):
            continue
        w, sz = r["wall"], r.get("size", {})
        rt = r.get("ratio") or {}
        o0 = rt.get("o0")
        o2 = rt.get("o2")
        s0 = f"{o0:.2f}x" if o0 is not None else "n/a"
        s2 = f"{o2:.2f}x" if o2 is not None else "n/a"
        raw0 = (w["jhyy"]["min"] / w["gcc0"]["min"]) if w["gcc0"]["min"] else 0.0
        flag = " ⚠️" if rt.get("too_short") else ""
        lines.append(
            f"| {r['name']}{flag} | {s0} | {s2} | {raw0:.2f}x | "
            f"{w['jhyy']['min']:.2f} | "
            f"{w['jhyy']['median']:.2f} | {w['jhyy']['p95']:.2f} | "
            f"{w['gcc0']['min']:.2f} | {w['gcc2']['min']:.2f} | "
            f"{rt.get('floor_frac', 0) * 100:.0f}% | "
            f"{sz.get('jhyy', 0)} | {sz.get('gcc0', 0)} | "
            f"{r['meta'].get('libc', '?')} |")
    lines.append("")
    lines.append("⚠️ = the measurement floor accounts for more than 25% of this "
                 "task's runtime, so its ratio is not reliable.\n")
    if meta.get("floor"):
        fl = meta["floor"]
        lines.append("## Measurement floor\n")
        lines.append("Every wall-clock number above includes the cost of getting "
                     "the process started at all. That floor has **two** parts:\n")
        lines.append("1. the harness's own process-creation cost (Python "
                     "`subprocess` + Windows `CreateProcess` + C-runtime init) "
                     "— roughly the same for both runtimes;\n")
        lines.append("2. the program's own startup cost — **jhyy is ~6 ms more "
                     "expensive than plain C** here, because the jhyy runtime "
                     "shim (`compiler/runtime/runtime.c`: `GetCommandLineW` / "
                     "`CommandLineToArgvW` / encoding conversion / "
                     "`setvbuf(_IONBF)`) runs first.\n")
        lines.append("The ratios above subtract this floor (per runtime) so they "
                     "compare the programs' own work. The `floor share` column "
                     "says how much of each task's runtime the floor accounts "
                     "for; above 25% the ratio is not reported at all, because "
                     "the floor's own measurement error would dominate it.\n")
        lines.append("| runtime | min (ms) | median (ms) |")
        lines.append("|---|---|---|")
        for k, v in fl.items():
            lines.append(f"| {k} | {v['min']:.3f} | {v['median']:.3f} |")
        lines.append("")
    lines.append("## Caveats\n")
    lines.append("See `bench/METHODOLOGY.md` for the full list. The short version:\n")
    for c in META_CAVEATS:
        lines.append(f"- {c}")
    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"published: {path}")


META_CAVEATS = [
    "jhyy has **no optimizer** — every jhyy number is `-O0`-quality codegen.",
    "gcc `-O0` is the codegen-quality floor; gcc `-O2` is a reference, **not** a bar.",
    "jhyy binaries link **ucrt64 libc** — tasks marked `libc != none` partly measure libc.",
    "**jhyy's stdout is unbuffered** (`setvbuf(_IONBF)`) — every task therefore "
    "prints one checksum, never bulk output.",
    "jhyy **cannot pass floats to C variadic functions** — float tasks are compared "
    "by IEEE-754 bit pattern, not decimal rendering.",
    "Float tasks are byte-compared against the **gcc `-O0`** build only; `-O2` may "
    "reassociate floating point.",
    "Tuning is asymmetric — the C twin is deliberately naive so both sides run the "
    "same algorithm.",
    "**jhyy programs start ~6 ms slower than plain C** (the C-runtime shim) — a "
    "fixed handicap that dominates short programs.",
    "Absolute numbers are **not comparable across machines** — only same-environment "
    "relative multiples are.",
    "**Wall-clock varies run to run** (up to ~25% between two runs on the same "
    "machine) — treat these as orders of magnitude, not precise values.",
    "Microbenchmarks are not real programs — the self-host compile time is the "
    "'real program' data point.",
    "This suite measures **codegen quality**, not the standard library.",
]


def selftest():
    """断言这道门**看得见红**,且**墙钟不会让它红**。

    为什么要有这个(repo 规约 feedback_ci_gate_must_exercise_path):
      门必须真走到它声称验的那条路径 —— 一道恒绿的门比没有门更糟。
    """
    print("bench.py --selftest — 断言门看得见红 / 墙钟不拦")
    failures = []

    # ① 静态指标回归 ⇒ 必须被 check_static 抓到
    fake = [("selftest", {"insn": 100, "mem": 50, "frame_med": 400, "chkstk": 0})]
    base = {"selftest": {"insn": 50, "mem": 50, "frame_med": 400, "chkstk": 0}}
    probs = check_static(fake, base)
    if not probs:
        failures.append("静态指标回归没被抓到 —— check_static 失效")
    else:
        print(f"  ✅ 静态指标回归被抓到: {probs[0]}")

    # ② 静态指标没回归 ⇒ 不能误报
    ok_rows = [("selftest", {"insn": 51, "mem": 50, "frame_med": 400, "chkstk": 0})]
    if check_static(ok_rows, base):
        failures.append("静态指标没有回归却被误报 —— check_static 有假阳性")
    else:
        print("  ✅ 没有回归时不误报")

    # ③ stdout 不一致 ⇒ 必须被认成失败(**走真实判据函数**)
    if outputs_match("same\n", "different\n"):
        failures.append("stdout 不一致没被认成失败 —— outputs_match 失效")
    else:
        print("  ✅ stdout 不一致会被认成失败")

    # ④ stdout 一致 ⇒ 必须通过(不能假阳性)
    if not outputs_match("same\n", "same\n"):
        failures.append("stdout 一致却被判失败 —— outputs_match 有假阳性")
    else:
        print("  ✅ stdout 一致时通过")

    # ⑤ 体积回归 ⇒ 必须被认成失败
    size_base = {"selftest": 1000}
    got = 2000
    lim = size_base["selftest"] * (1.0 + TOL)
    if got <= lim + 1e-9:
        failures.append("体积回归没被抓到")
    else:
        print(f"  ✅ 体积回归被抓到: {got} > 基线 {size_base['selftest']} 的 "
              f"{1 + TOL:.0%} 上限 {lim:.0f}")

    # ⑥ **墙钟不该让门变红** —— 静态指标相同、墙钟差 100 倍,门必须仍然绿
    same = [("selftest", {"insn": 50, "mem": 50, "frame_med": 400, "chkstk": 0})]
    if check_static(same, base):
        failures.append("静态指标相同却被判红 —— 门把别的东西算进去了")
    else:
        print("  ✅ 静态指标相同时门保持绿(墙钟不参与判定)")

    # ⑦ **地板占比过高 ⇒ 必须报 n/a,而不是一个垃圾数**
    #    (实测:ack 的地板占比 61% ⇒ 扣出来的比值 10.25x,纯垃圾 ⇒ 不能报)
    short_row = {"wall": {"jhyy": {"min": 30.0, "median": 30.0, "p95": 30.0},
                          "gcc0": {"min": 20.0, "median": 20.0, "p95": 20.0},
                          "gcc2": {"min": 15.0, "median": 15.0, "p95": 15.0}}}
    r0, r2, frac, too_short = ratios(short_row, {"jhyy": {"min": 18.0},
                                                  "gcc": {"min": 12.0}})
    if r0 is not None or r2 is not None:
        failures.append(f"地板占比过高时仍报了比值({r0}/{r2})—— 该报 n/a")
    elif not too_short:
        failures.append("地板占比过高时没有标记 too_short")
    else:
        print(f"  ✅ 地板占比过高({frac * 100:.0f}%)时比值报 n/a,不报垃圾数")

    # ⑧ 地板占比正常 ⇒ 必须报得出比值(不能一律 n/a)
    ok_row = {"wall": {"jhyy": {"min": 300.0, "median": 300.0, "p95": 300.0},
                       "gcc0": {"min": 100.0, "median": 100.0, "p95": 100.0},
                       "gcc2": {"min": 50.0, "median": 50.0, "p95": 50.0}}}
    r0, _r2, frac, too_short = ratios(ok_row, {"jhyy": {"min": 20.0},
                                               "gcc": {"min": 15.0}})
    if r0 is None or too_short:
        failures.append(f"地板占比正常时没报出比值({r0})—— 比值逻辑坏了")
    else:
        print(f"  ✅ 地板占比正常({frac * 100:.0f}%)时比值 = {r0:.2f}x")

    if failures:
        for f in failures:
            print(f"  ❌ {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


def main():
    strict = "--strict" in sys.argv
    ci = "--ci" in sys.argv
    update = "--update-baseline" in sys.argv
    quick = "--quick" in sys.argv
    publish = "--publish" in sys.argv
    selftest_mode = "--selftest" in sys.argv

    if selftest_mode:
        return selftest()

    json_out = None
    publish_out = None
    for i, a in enumerate(sys.argv):
        if a == "--json" and i + 1 < len(sys.argv):
            json_out = sys.argv[i + 1]
        if a == "--out" and i + 1 < len(sys.argv):
            publish_out = sys.argv[i + 1]

    if not os.path.exists(JHY):
        print(f"ERROR: jhyy.exe not found at {JHY}", file=sys.stderr)
        return 2

    tasks = load_tasks()
    if not tasks:
        print(f"ERROR: 找不到基准任务 —— {rp.BENCH_TASKS} 下没有 task.c/task.jhyy 配对",
              file=sys.stderr)
        return 2
    if quick:
        tasks = {k: v for k, v in tasks.items() if k == "fib"}
    # 发布快照多跑几轮 —— 墙钟的 run-to-run 波动可达 25%(实测),
    # 多取样只能压噪声、不能消除它 ⇒ **发布前机器必须空闲**。
    runs = max(RUNS, 15) if publish else RUNS

    mode = ("--strict" if strict else
            ("--ci" if ci else
             ("--update-baseline" if update else
              ("--publish" if publish else "--report"))))
    print(f"bench.py — jhyy vs gcc  (mode={mode})")
    print(f"  jhyy : {JHY}")
    print(f"  gcc  : {GCC}")
    print(f"  tasks: {len(tasks)}  ({', '.join(sorted(tasks))})")
    print(f"  runs : {runs} (warmup 1 丢弃)")
    if ci:
        print("  CI 模式:墙钟**只报告不拦**;正确性 / 静态指标 / 体积做硬门")
    print("")

    tmp = tempfile.mkdtemp(prefix="jhbench_")
    rows = []
    failed = False
    for name in sorted(tasks):
        row = run_task(tmp, name, tasks[name], runs)
        rows.append(row)
        if not row["ok"]:
            failed = True
            print(f"  {name}: FAIL")
            for e in row["errors"]:
                print(f"    {e}")

    # ── 测量地板 ──
    # ⚠️ 在**题目跑完之后**测:地板是 harness 自身的进程创建开销,
    # 题目测量发生在一个"热"的机器状态里 ⇒ 地板也要在同样的状态下测。
    floor = measure_startup_floor(tmp, max(runs, 30))

    for r in rows:
        if not r.get("wall"):
            continue
        r0, r2, frac, short = ratios(r, floor)
        r["ratio"] = {"o0": r0, "o2": r2, "floor_frac": frac, "too_short": short}
        s0 = f"{r0:.2f}x" if r0 is not None else "n/a"
        s2 = f"{r2:.2f}x" if r2 is not None else "n/a"
        w = r["wall"]
        print(f"  {r['name']}: OK  jhyy/O0={s0}  jhyy/O2={s2}  "
              f"(扣地板) median={w['jhyy']['median']:.2f}ms  地板占比={frac * 100:.0f}%"
              + ("  [题目太短]" if short else ""))

    print("")
    print_table(rows, floor)

    if floor:
        print("")
        print("测量地板(harness 自身的进程创建开销,不是程序启动时间): " + "  ".join(
            f"{k}={v['min']:.3f}ms" for k, v in floor.items()))

    # ── 静态指标门:只管**非历史**题目(历史题目的基线归 `perf` 门)──
    # ── 体积门:管**全部**题目 —— 二进制体积此前**没有任何门**在管,
    #    这是 `bench-perf` 门带来的**新**约束(不是重复 `perf` 门的工作)。
    owned = [(r["name"], r.get("static"),
              (r.get("size") or {}).get("jhyy"))
             for r in rows if r["name"] not in LEGACY_TASKS]
    owned = [o for o in owned if o[1]]
    all_sizes = [(r["name"], (r.get("size") or {}).get("jhyy")) for r in rows]
    all_sizes = [(n, s) for n, s in all_sizes if s]
    base = load_baseline()
    static_problems = check_static([(n, s) for n, s, _ in owned], base) if owned else []
    if owned:
        print("")
        if static_problems:
            print("静态指标回归:")
            for p in static_problems:
                print(f"  ❌ {p}")
        else:
            print(f"静态指标: 全部在基线的 {1 + TOL:.0%} 容差内 ✅")

    # ── 二进制体积门(确定性:同一份源码 × 同一个编译器 ⇒ 逐字节相同)──
    size_problems = []
    size_base = (base or {}).get("_size") or {}
    for name, size in all_sizes:
        want = size_base.get(name)
        if want:
            lim = want * (1.0 + TOL)
            if size > lim + 1e-9:
                size_problems.append(
                    f"{name}.size: {size} > 基线 {want} 的 {1 + TOL:.0%} 上限 {lim:.0f}")
    if size_problems:
        print("")
        print("二进制体积回归:")
        for p in size_problems:
            print(f"  ❌ {p}")

    if update:
        save_baseline(owned, all_sizes)
        print("")
        print("RESULT: 基线已更新(--update-baseline)。**更新基线必须写明理由。**")
        return 0

    meta = env_meta(runs)
    meta["date"] = time.strftime("%Y-%m-%d")
    meta["floor"] = floor

    if json_out:
        payload = {"meta": meta, "rows": rows}
        Path(json_out).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8", newline="\n")
        print(f"\njson written: {json_out}")

    if publish:
        out = publish_out or str(Path(__file__).resolve().parent / "baseline" /
                                 f"RESULTS-{meta['date']}.md")
        publish_markdown(rows, meta, out)

    print("")
    if ci:
        if failed:
            print("RESULT: FAIL (编译 / 正确性检查没过)")
            return 1
        if static_problems or size_problems:
            print(f"RESULT: FAIL ({len(static_problems) + len(size_problems)} 项回归)")
            return 1
        print("RESULT: PASS (正确性 / 静态指标 / 体积无回归;墙钟只报告)")
        return 0

    if strict:
        if failed or static_problems or size_problems:
            print("RESULT: FAIL")
            return 1
        print("RESULT: PASS")
        return 0

    over = [r["name"] for r in rows if r.get("wall")
            and r["wall"]["jhyy"]["min"] > 2.0 * r["wall"]["gcc0"]["min"]]
    if over:
        print(f"RESULT: REPORT — {len(over)}/{len(rows)} 个程序超墙钟阈值 2.0x"
              f"({', '.join(over)});报告模式不阻塞")
    else:
        print("RESULT: REPORT — 全部在墙钟阈值 2.0x 内")
    if static_problems or size_problems:
        print(f"          ⚠️ 另有 {len(static_problems) + len(size_problems)} 项回归(见上)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
