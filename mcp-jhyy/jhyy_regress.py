#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jhyy_regress.py — 共享 regress 逻辑 (mcp-jhyy tool + regress.py shim 共用)

Sprint mcp-1 (2026-08-11): 抽 NTSTATUS_NAMES + run_test + run_all 出来, 消除 regress.py 重复.
Sprint v1.4.7 (2026-08-14): regress.py 合并成单入口 (--all / --include-informational),
                             regress_v1.py / regress_stage0.py 删除, 此模块只剩 MCP tool + regress.py shim 共用.

Public API:
    ntstatus_name(code)            -> str | None
    run_test(jhyy_file, binary, ...) -> (passed, expected, actual, message)
    run_all(binary, tests=None, timeout=300, enforce_baseline_hash=True) -> dict
    save_baseline_hash(binary)     -> str (sha256)
"""
import subprocess
import sys
import os
import re
import hashlib
import signal
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Tuple, Dict

# 路径配置 — derive from script location (works on any machine, no
# hardcoded user path; per v1.5.5 release.yml CI fix).
# mcp-jhyy/jhyy_regress.py → parents[1] = project root
JHYY_ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = JHYY_ROOT / "compiler/tests/examples"


# ── 单测试超时(死循环探测上限,秒)—— **单一事实来源** ──────────────────
#
# 2026-10-18:此前这个数字散在**四个**地方且互相矛盾:
#
#   regress.py   --timeout            default=300
#   jhyy_regress --timeout            default=300
#   run_all()    签名默认              **10**    ← 病灶
#   server.py    jhyy_regress MCP 工具 default=**20**
#
# 危害:`server.py:323` 按位置传参,所以 MCP 走的是 20 而不是 10 —— 但任何
# **直接调 `run_all(...)` 而不显式传 timeout** 的调用方(包括将来的代码、
# 一次性的排查脚本)都会拿到 **10 秒**。单次编译实测 1.26s,并发争抢下
# 会被放大好几倍(`:328-331` 自己的注释就写了这件事),于是变成随机被杀:
# 失败看起来像「这个测试坏了」,实际是超时太紧。**这种 flake 比没有门更糟**,
# 因为它会诱导人去改一个没坏的测试。
#
# 300 不是随便挑的:`Makefile:225` 与 regress 实测单次完整编译(编译器 + gcc
# 链接)约 1.26s,300s 对它是 240 倍余量。它的职责是抓**永不返回**的循环,
# 不是性能预算 —— 所以宁可宽裕。
#
# 改这里,不要在任何调用点再写数字。
DEFAULT_TIMEOUT = 300


# Sprint mcp-2: NTSTATUS table 抽到 jhyy_ntstatus.py 共享给 jhyy_runner.compile_and_run.
# Re-export here 保 back-compat (test_regress.py / regress.py shim 都 import 此模块).
from jhyy_ntstatus import NTSTATUS_NAMES, ntstatus_name  # noqa: E402,F401


def _resolve_binary(binary: str) -> str:
    """解析 binary 路径 (相对 JHYY_ROOT 或绝对)."""
    if os.path.isabs(binary):
        return binary
    return str(JHYY_ROOT / binary)


def _build_subprocess_env() -> dict:
    """构造 subprocess env. 基础 env (TMP / SystemRoot / SystemDrive).

    v1.5.6 (superseder W-027 v8): jhyy.exe 自己负责探测 gcc 路径 (见
    jh_gcc_path() 4-tier probe), 不再需要 Python 侧主动 prepend MSYS2 bin
    到 PATH. 之前 W-026/W-027 全部 MSYS2 探测逻辑 (~30 行) 收敛到 jhyy.exe
    内部一处, regress.py 只保留基础 env + SETENV 注入.

    Mirror jhyy_runner.py:_build_subprocess_env (modules 独立, 不互相 import).

    历史 (per docs/internal/workarounds.md W-027 v8):
    W-026 (2026-08-15): CI GH Actions release.yml regress 53/53 FAIL,
      'gcc is not recognized'.
    W-027 v4 (2026-08-15): setup-msys2@v2 装 MSYS2 到 $RUNNER_TEMP\\msys64
      (CI) 不在 C:\\msys64. 试了 shutil.which / cmd where / bash cmd where,
      都有 quoting / encoding 问题. v4 用 deterministic MSYS2 root + 已知
      bin subdirs.
    v1.5.6 fix: 把 W-027 v4 整段 (含 found_dirs + shutil.which + msys2_roots)
      删掉, 改由 jhyy.exe jh_gcc_path() 接管. 见 workarounds.md W-029.
    """
    import tempfile
    default_tmp = tempfile.gettempdir()
    env = os.environ.copy()
    if not env.get("TMP"):
        env["TMP"] = default_tmp
    if not env.get("TEMP"):
        env["TEMP"] = default_tmp
    if not env.get("TMPDIR"):
        env["TMPDIR"] = default_tmp
    if not env.get("SystemRoot"):
        env["SystemRoot"] = r"C:\Windows"
    if not env.get("SystemDrive"):
        env["SystemDrive"] = "C:"
    return env


def _kill_process_tree(pid: int) -> None:
    """杀掉 `pid` 及其**后代**,不碰父进程。

    2026-10-18 补回。背景:`_run_capture` 超时时只 `proc.kill()` 直接子进程,
    而 jhyy.exe 是通过 `system()` / CreateProcess 调 gcc 的 —— gcc / cc1 / as
    这些**孙进程会活下来**,在一次 201 个测试的运行里持续累积。它们占 CPU、
    占句柄、占 exe 文件锁,表现为「某些测试随机挂」(harness 自己的注释
    `:328-331` 就记着这个症状)。

    ⚠️ 为什么当年 `taskkill /T` 把 harness 自己的 shell 一起杀了(2026-10-17,
    连丢三轮 CI 数据):那次**没有带 `/PID`**,是按进程名杀的。
    **`/PID` 是必须的** —— 带显式 PID 时 taskkill 只杀那棵以它为根的子树,
    父进程(harness)不在其中。

    两道守卫,防止任何情况下误伤自己:
      · 目标 pid 不得是本进程或父进程
      · 只在 Windows 上执行,其余平台直接返回(POSIX 上子进程不 fork 孙进程)

    失败一律吞掉:清理是 best-effort,不该让一次测试失败变成 harness 崩溃
    —— 那正是 2026-10-17 那三轮 CI 的失败形态。
    """
    if os.name != "nt":
        return
    try:
        if not pid or pid <= 0:
            return
        me, parent = os.getpid(), os.getppid()
        if pid in (me, parent):
            return
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass


def _run_capture(cmd, timeout: int, env: dict) -> tuple:
    """跑 cmd 并抓取输出,超时则**杀整棵进程树**。

    不用 `subprocess.run` 的两个原因(都踩过):

    1. 它超时只 TerminateProcess 直接子进程 —— 这正是我们要的(见下面
       「为什么不用 taskkill /T」)。
    2. 它**不把 Popen 对象交出来**,而 `TimeoutExpired` 上只有
       cmd/timeout/output/stderr,**没有 `.pid`** —— 事后想补杀后代都做不到。
       (2026-10-17 加 `_kill_tree(exc.pid)` 时踩到:AttributeError 直接打死
       整个 regress。)

    返回 `(returncode, stdout_str, stderr_str)`。stdout/stderr **统一解码成
    str**:调用点不必再猜类型 —— 原先 `run(text=True)` 正常返回给 str、超时时
    给 bytes,两处都得判类型,漏一处就是 TypeError。

    超时时抛 `TimeoutExpired`,其 output/stderr 已是 str;并在异常上挂两个
    调用方要用的属性:
      `child_exited` — 子进程**是否已经退出**。
        False = 它自己卡住(真死循环/真阻塞);
        True  = 它早退了,`communicate()` 是在等**孙进程持有的管道写端**
                (gcc/as 继承了 stdout/stderr)。这两种的修法完全不同,
                报告里必须分开,否则又是一句「超时了没法行动」。
      `child_rc` — 已退出时的退出码。
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, env=env)
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        child_exited = proc.poll() is not None
        child_rc = proc.returncode
        # 先杀直接子进程,再扫掉它的后代(gcc/cc1/as)。
        #
        # 2026-10-17 之所以只留 `proc.kill()`:那次试 `taskkill /T` 把 harness
        # 自己的 shell 一起杀了(step 零输出 + exit 2304,连丢三轮 CI 数据)。
        # 复盘:那次**没带 `/PID`**,是按进程名杀的。带显式 `/PID` 时只杀那棵
        # 以它为根的子树,harness 作为父进程不在其中 —— `_kill_process_tree()`
        # 里另有两道守卫(不得是本进程/父进程、Windows 限定)。
        #
        # 只在超时路径上扫:正常完成时 jhyy.exe 已经等过 gcc 了,没有遗留。
        proc.kill()
        _kill_process_tree(proc.pid)
        # 排空只给 2s。管道写端可能被**孙进程**持有(见 child_exited),那种情况
        # 下无论等多久都关不上 —— 第一版给 30s,单次超时就多烧 30s,3 个测试 ×
        # 2 次重试 = 白等 3 分钟。拿不到就用 TimeoutExpired 里已有的部分输出。
        try:
            out, err = proc.communicate(timeout=2)
        except Exception:
            out, err = exc.output, exc.stderr
        dec = lambda b: (b or b"").decode("utf-8", "replace") \
            if isinstance(b, bytes) else (b or "")
        err_exc = subprocess.TimeoutExpired(cmd, timeout,
                                            output=dec(out), stderr=dec(err))
        # 挂在新异常对象上 —— 直接 raise exc 会丢属性(raise 的是新构造的对象)。
        err_exc.child_exited = child_exited
        err_exc.child_rc = child_rc
        raise err_exc
    dec = lambda b: b.decode("utf-8", "replace") if b else ""
    return proc.returncode, dec(out), dec(err)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def save_baseline_hash(binary: str) -> str:
    """算 binary sha256 并写到 <binary>.sha256 文件. 返回 sha256.

    ⚠️ .exe binary build 是非确定性的 (时间戳 / relocation / PIC), 同一份
    source 每次 build 都得到不同 sha. baseline sha 只在 build 之后立刻
    写一次有意义; 之后任何时刻的 sha 都可能漂移, 不要拿它做 byte-equal
    信号. 真正的回归信号是 .il byte-equal (per [[feedback_il_byte_equal]]).
    """
    bin_path = _resolve_binary(binary)
    sha = _sha256_file(bin_path)
    sha_path = bin_path + ".sha256"
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write(sha + "\n")
    return sha


def _freshness_src_dirs(binary: str) -> list:
    """这个二进制该跟哪些源树比 mtime。

    2026-10-18:此前这里硬编码 `src_dir="compiler/src"`,而 `compiler/src`
    是**已冻结的 C 端**(v0.x,最后改动 2026-09-30)。它的 mtime 一直很旧,
    于是对 `jhyy.exe` 而言 `bin_mtime >= newest_src` 恒成立 —— **这道
    phantom-binary 保护从来没触发过**,只是看起来在跑。

    而 `jhyy.exe` 真正是从 `compiler/src0/*.jhyy`(jhyy 端语言)编的,
    并且链接了两个 host-gcc 编的 `.o`:
        compiler/build/obj/_jhyy_runtime.o     ← compiler/runtime/runtime.c
        compiler/build/obj/_jhyy_helpers.o   ← compiler/src0/jhyy_helpers.c
    所以它的依赖面是 **src0 + runtime**。

    不能一刀切成 src0:`jhyy_stage0.exe` 确实是从 `compiler/src/*.c` 编的,
    拿 src0 去比它就是另一处失效。按二进制选。

    Returns:
        [相对 JHYY_ROOT 的目录路径, ...];不存在的目录会被静默跳过。
    """
    name = os.path.basename(binary).lower()
    if name == "jhyy_stage0.exe":
        # C 端 bootstrap:编译器源码 + 运行时
        return ["compiler/src", "compiler/runtime"]
    # jhyy 端(jhyy.exe / jhyy_v1.exe.exe / 任何 gen-N 副本)
    return ["compiler/src0", "compiler/runtime"]


# v4.0.16 (W-103): `compiler/src0/std/` 下的 8 个 std lib 模块**不是编译器的输入**。
#
# 它们是**发给用户**的库源码(现在也装进 MSI 的 bin\std\,`import <mod>;` 从那里
# 找),jhyy.exe 里一个字节都不含它们 —— 编译器只 import `ffi` / `util` /
# `arena` / `ast` / … 这些**同目录**模块,`std/` 子目录从来没进过编译单元。
#
# 但 freshness 检查用 `rglob("*")` 扫 `compiler/src0`,会把 std/ 一起扫进来 →
# **只改一个 std 模块就让 regress 报「binary is older than source / suspect
# phantom binary」并 early_abort**,而二进制其实一个字节都没变。
#
# 实测(2026-10-20):改完 `std/os.jhyy` 跑 regress,0 个测试被执行,
# 直接 early_abort —— 一道**假阳性**的门比没有门更糟:它训练人忽略红色。
#
# 所以这里把 std/ 从 jhyy 端二进制的 freshness 依赖面里排除。
# ⚠️ 排除的是**依赖面**,不是检查本身 —— 改 `compiler/src0/*.jhyy` 仍然会触发
#    这道门(见本轮验证:touch main.jhyy → 照样 early_abort)。
_FRESHNESS_EXCLUDE_JHY = ("compiler/src0/std",)


def _check_baseline_freshness(binary: str, src_dirs=None) -> Tuple[bool, str]:
    """检查 binary 是否在它的源之后被构建过. 防止 phantom binary (忘记
    重编就跑 regress).

    Returns:
        (is_fresh, message)
        is_fresh=True 当: 所有源目录都缺失, 或源文件全部比 binary 旧
        is_fresh=False 当: 源里有文件比 binary 新, 怀疑 binary 是旧 build

    Rationale: .il byte-equal 是真回归信号, .exe sha 防不了非确定性 drift
    也没必要防. binary mtime 跟 src mtime 的相对关系才决定 binary 是不是
    "新构建的" — 这才是 phantom binary 场景的真信号.

    ⚠️ 这道检查回答的是**本地**的同一个问题:`ci.yml` 的 `artifact-fresh`
    门回答的是「提交产物 vs 当前源码」。两边曾经一个真一个空,现在对齐了 ——
    否则会出现「CI 绿但本地拿到的是旧编译器」这种最难查的组合。
    """
    bin_mtime = os.path.getmtime(binary)
    dirs = src_dirs if src_dirs is not None else _freshness_src_dirs(binary)
    newest_src = 0.0
    seen = []
    for d in dirs:
        src_root = JHYY_ROOT / d
        if not src_root.exists():
            continue
        seen.append(d)
        bin_name = os.path.basename(binary).lower()
        excludes = () if bin_name == "jhyy_stage0.exe" else _FRESHNESS_EXCLUDE_JHY
        for p in Path(src_root).rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(JHYY_ROOT).as_posix()
            if any(rel == ex or rel.startswith(ex + "/") for ex in excludes):
                continue
            newest_src = max(newest_src, os.path.getmtime(p))
    if not seen:
        return (True, f"src dirs missing ({dirs}), skipping freshness check")
    if bin_mtime + 0.5 >= newest_src:  # 0.5s 容忍文件系统 mtime 精度
        return (True, f"binary mtime {bin_mtime:.0f} >= newest src mtime "
                       f"{newest_src:.0f} (src: {', '.join(seen)})")
    return (False, (
        f"binary is older than source: binary mtime={bin_mtime:.0f}, "
        f"newest src mtime={newest_src:.0f} (src: {', '.join(seen)}) — "
        f"suspect phantom binary. Rebuild before running regress."
    ))


def artifact_slug(jhyy_file: str) -> str:
    """测试路径 → 唯一的 artifact 名(无扩展名)。

    2026-10-18:原来这里只用 `basename`,于是
    `compiler/tests/examples/multi_file/main.jhyy` 与
    `compiler/tests/examples/namespace/main.jhyy` **都**映射到
    `compiler/build/bin/_regress_main.{il,s,exe}`。

    两者自 2026-10-15 改用 rglob 后就进了同一个并发 suite(`:592`),于是
    互相删对方的 .il/.s/.exe、互相覆盖 `-o` 输出、`:407` 甚至可能执行
    **另一个测试**编出来的 .exe。两个测试的期望还不同(EXIT=60 vs EXIT=0)。

    实际后果: `multi_file/main.jhyy` 偶发 FAIL 而单跑必绿 —— 2026-10-17
    实测同一个 binary sha `4e987dd9`,CI 176/176 绿、本地全量 175/176 红,
    红的就是它。当时按 flake 记下了,根因是这个命名冲突。

    现在路径分隔符统一替换成 `__`,路径越深名字越唯一。

    **入参形态不统一,必须在这里归一化。** 两个调用点传的东西不一样:
      - `run_test` 收绝对路径(`:665` 的 `str(TEST_DIR / f)`)
      - cleanup / failed_names 用相对路径(`files` 元素,如 `multi_file/main.jhyy`)
    所以先转成「相对 TEST_DIR」再拼名,否则两边算出两个名字,artifact 永久堆积。

    **建名(run_test)与清名(cleanup)必须都走这个函数** —— 只改一处同样会堆积。
    """
    p = Path(jhyy_file)
    if not p.is_absolute():
        # `files` 元素是「相对 TEST_DIR」的(`multi_file/main.jhyy`)。
        # 不先挂上 TEST_DIR,resolve() 会拿 CWD 去解释,必然 relative_to 失败
        # → 退到 basename → 冲突原样回来。
        p = TEST_DIR / p
    try:
        rel = p.resolve().relative_to(TEST_DIR)
    except ValueError:
        # 真的不在 TEST_DIR 下(`--tests=` 传了外部绝对路径)→ 退到 basename。
        # 这类文件不在 files 里,只可能从 --tests= 进来。
        rel = Path(p.name)
    return str(rel.with_suffix("")).replace(os.sep, "__")


def run_test(
    jhyy_file: str,
    binary: str,
    timeout: int = 300,
    extra_inputs: Optional[List[str]] = None,
) -> Tuple[bool, Optional[int], int, str]:
    """Compile + run 单个 .jhyy 文件, 返回 (passed, expected, actual, message)."""
    name = artifact_slug(jhyy_file)
    out_base = str(JHYY_ROOT / "compiler/build/bin" / f"_regress_{name}")

    # Sprint 4.4 C: stale .exe hardening — 避免 stale cache 掩盖 cleanup crash
    for ext in (".il", ".s", ".exe"):
        p = out_base + ext
        if os.path.exists(p):
            os.remove(p)

    # Read expected exit from comment if present
    expected = None
    has_main = False
    # v1.7.0 Stage 1: EXPECT-ERROR — 期望 compile fail 且 stderr 含 substring.
    # 跟 EXPECT (整数 exit code) 互斥: 同一 test 只能用一个.
    expect_error_kw = None
    # 2026-10-15 (W-109 教训):EXPECT-OUT —— 断言 stdout 里的子串。
    # 存在是因为 EXPECT 只管退出码,而本编译器**不支持变参 printf**
    # (ABI § 11.2 B8),测试经常只能把结果打印出来;此前 stdout 被捕获后
    # 只用于显示、不参与判定,于是 float_cmp 那类测试的输出全是摆设。
    # 只比 stdout(不比 stderr):混进诊断信息会造成假通过。
    expect_out_kw = None
    # 2026-10-15: XFAIL directive — 「这个测试应该失败,因为对应 bug 还没修」。
    #
    # 为什么不用 SKIP:SKIP 是**不跑**,所以 bug 哪天被修好了它也不会吭声 ——
    # 标记就永久失真了。XFAIL 是**真跑**:失败算预期(不计入 suite 失败),
    # 但**通过就算 XPASS 并让 suite 失败**,因为那意味着有人修了 bug 却忘了摘标记。
    # 「修好了必须有人看见」正是 SKIP 给不了的。
    xfail_reason = None
    # v1.7.3: SKIP directive — 期望 test 暂 skip (有已知 bug 推后续 ship,
    # e.g. defer silent codegen crash 推 v1.8). 形式: `// SKIP: <reason>`.
    skip_reason = None
    # v2.13.0: SKIP-QBE directive — 仅在 default QBE 模式 skip (--self-backend 模式
    # 仍跑)。用法: 自写后端真修的 test,QBE 模式有已知 bug (e.g. xmm_pressure_9args
    # QBE Win ABI f64 stack-arg emit `addsd %rdi, %xmm0` operand type mismatch)。
    skip_qbe_reason = None
    # 2026-10-15 (CI 修复):SKIP-STAGE0 —— 只在 `jhyy_stage0.exe`(C 端 bootstrap)
    # 上跳过。存在的理由:`regress.py --all` 拿 jhyy.exe 与 jhyy_stage0.exe 两个
    # binary 做 gated,而 stage0 是 **C 端编译器**,它的 parser 早于 V3-B / V3-C,
    # 不认 `&mut` / `Cap<T>` / `#[naked]` / `asm!` / `volatile` 这些语法。
    # 这些测试在 jhyy.exe(生产 binary)上必须跑 —— 它们验的是自举后端的行为,
    # 而自举后端**只有 jhyy.exe 这条腿在验**。
    #
    # 与 SKIP-QBE 是镜像关系:SKIP-QBE 是「默认跳,opt进才跑」,本条是
    # 「默认跑,只有 stage0 跳」。两边都不该被笼统的 SKIP 代替 —— 笼统 SKIP
    # 会让这些测试在**两条腿上都不跑**,那才是真的没人验。
    skip_stage0_reason = None
    # v1.5.6: SETENV directive — 解析 // SETENV: KEY=VALUE 行, 注入到
    # _build_subprocess_env() 返回的 env. 测试用: 验证 jh_gcc_path() 在不同
    # env 状态下的探测行为 (Priority 1 JHY_GCC / Priority 2 JHYY_HOME).
    setenv_overrides = {}  # type: Dict[str, str]
    try:
        with open(jhyy_file, encoding="utf-8") as f:
            raw_src = f.read()
        # 判据扫描的两条规则(单一事实来源在 scripts/dev/audit_test_assertions.py):
        #   指令只认「整行就是该指令」的独立注释行 —— 否则**文档里提到一个指令
        #   就会凭空生成一条断言**(实测踩过:注释里写「此前是 `//EXPECT:42`」,
        #   结果那条真的成了断言)。
        #   结构检测(fn main_jhyy)用剥掉注释的源码 —— 否则注释里提到
        #   `fn main_jhyy` 会让一个没有 main 的文件被当成可跑测试。
        try:
            from audit_test_assertions import directive_source as _dir_src,                                                strip_comments as _strip_comments
            src = _dir_src(raw_src)
            code_src = _strip_comments(raw_src)
        except Exception:
            src = raw_src
            code_src = raw_src
        m = re.search(r"//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)", src)
        if m:
            expected = int(m.group(1))
        m_err = re.search(r'//\s*EXPECT-ERROR\s*[:=]\s*"([^"]+)"', src)
        if m_err:
            expect_error_kw = m_err.group(1)
        m_out = re.search(r'//\s*EXPECT-OUT\s*[:=]\s*"([^"]+)"', src)
        if m_out:
            expect_out_kw = m_out.group(1)
        m_xfail = re.search(r"//\s*XFAIL\s*:\s*(.+)", src)
        if m_xfail:
            xfail_reason = m_xfail.group(1).strip()
        m_skip = re.search(r"//\s*SKIP\s*:\s*(.+)", src)
        if m_skip:
            skip_reason = m_skip.group(1).strip()
        m_s0 = re.search(r"//\s*SKIP-STAGE0\s*:\s*(.+)", src)
        if m_s0:
            skip_stage0_reason = m_s0.group(1).strip()
        m_skip_qbe = re.search(r"//\s*SKIP-QBE\s*:\s*(.+)", src)
        if m_skip_qbe:
            skip_qbe_reason = m_skip_qbe.group(1).strip()
        # Skip library files (no main entry) — 用剥掉注释的源码判定,
        # 否则注释里提到 `fn main_jhyy` 会让一个没有 main 的文件被当成可跑测试。
        has_main = bool(re.search(r"\bfn\s+main_jhyy\b", code_src))
        # SETENV: 解析多行 KEY=VALUE (注释行从 # 起; 行尾 # 也算注释)
        for line in src.splitlines():
            line_stripped = line.strip()
            sm = re.match(r"//\s*SETENV\s*:\s*([A-Za-z_][A-Za-z0-9_]*)=(.*?)(?:\s*#.*)?$", line_stripped)
            if sm:
                key, val = sm.group(1), sm.group(2).strip()
                setenv_overrides[key] = val
    except UnicodeDecodeError:
        pass

    # SKIP-STAGE0 判定放在所有声明之后 —— binary 参数在这里可用,变量也已初始化。
    if skip_stage0_reason is not None and os.path.basename(binary) == "jhyy_stage0.exe":
        return (True, None, None, f"skipped (stage0-only: {skip_stage0_reason})")

    if not has_main:
        # Library file: skip (no standalone run possible)
        return (True, None, None, "skipped (library)")

    if skip_reason is not None:
        # v1.7.3: SKIP directive — test 暂 skip (有已知 bug 推后续 ship).
        # 期望后续 sprint 真修 bug 后移除 SKIP 行启用 default regress.
        return (True, None, None, f"skipped ({skip_reason})")

    # v2.13.0: SKIP-QBE directive — QBE 默认模式 skip, --self-backend 模式仍跑
    if skip_qbe_reason is not None and not os.environ.get("JHY_SELF_BACKEND"):
        return (True, None, None, f"skipped (qbe-only: {skip_qbe_reason})")

    # v1.5.6: 用 SETENV 覆盖的 env 跑 compile + run.
    # _build_subprocess_env() 已经在 PATH 段做 MSYS2 探测, SETENV 覆盖在它之上.
    test_env = _build_subprocess_env()
    test_env.update(setenv_overrides)

    # Compile
    cmd = [_resolve_binary(binary), "compile", jhyy_file, "-o", out_base]
    if extra_inputs:
        for inp in extra_inputs:
            cmd.insert(2, _resolve_binary(inp))
    # compile 与 run 共用同一个 --timeout(以前 compile 硬编码 60、run 用参数,
    # 三个默认值还互相打架,--timeout 实际只管 run)。
    # 默认给到 300s 是刻意的:这个上限的职责是抓**永不返回**的无限循环,
    # 不是性能预算。并行跑(min(测试数, CPU 数) 路,每路还各 fork 一个 gcc)时
    # 单个 compile 被 CPU 争抢拉长好几倍是常态;拿 60s 当性能线会随机误杀
    # 慢测试 —— 实测同一份代码在有残留进程时能随机挂掉 cap_table_basic /
    # slice_len,清干净就全绿。慢用 --jobs 限并发解决,不该动超时。
    # 2026-10-15:这里原先是裸 subprocess.run,compile 超时会抛
    # subprocess.TimeoutExpired **穿透 run_test 打死整个 run_all** —— 一个测试
    # 卡住,剩下 170 多个的结果全丢,连「哪些跑过了」都看不到。
    # 编译器挂死/资源争抢是常态(见上面关于并发的注释),不是异常情况,
    # 应该记成该测试 FAIL 并继续跑其余的。
    first_timeout = None
    try:
        # stdin=DEVNULL + 杀进程树 + 统一 str 解码,都在 _run_capture 里。
        rc, stdout_compile, stderr_compile = _run_capture(cmd, timeout, test_env)
    except subprocess.TimeoutExpired as exc:
        # 2026-10-15:重试一次。单个测试 compile 正常 3 秒,300 秒超时对它是
        # 永远不合理的量级 —— 命中即意味着「进程被抢死」而不是「编译真的慢」。
        # 根因是并发下每个测试展开成 jhyy.exe → gcc → cc1 三层进程,CI runner
        # 核少时被压垮(W-113 记的旁路文件竞态是同一个根的另一面)。
        # 重试是**缓解**不是修复:真修要靠给旁路文件按 pid 隔离 + 限制并发。
        first_timeout = exc
        try:
            rc, stdout_compile, stderr_compile = _run_capture(cmd, timeout, test_env)
        except subprocess.TimeoutExpired as exc2:
            # .il 出来但没 .s → 卡在 self-backend emit(可能无限循环)
            # .s 出来但没 .exe → 卡在 gcc 链接(可能是 runner 环境,不是编译器)
            # 什么都没有 → 卡在 parse/sema(逐 token 慢,或扫描/杀软拖慢 IO)
            have = [e for e in (".il", ".s", ".exe")
                    if os.path.exists(out_base + e)]
            # 注意:in-mem self-backend 路径**默认不落 .il**(要 JHY_WRITE_IL=1
            # 才写),所以「没有 .il」不代表没进 emit;但 **.s 是落的** ——
            # asm_path 一直传给 codegen_amd64_run_text(实测 `jhyy.exe compile
            # arith.jhyy` 产出 _probe.s 1272B + _probe.exe)。2026-10-15 我一度
            # 反过来断言「in-mem 路径不落 .s,无产物是常态」,那是错的:
            # 不落盘的只有 .il。这里把两个事实都定死,免得再被推翻一次。
            if ".s" in have:
                stage = ("链接阶段(已产 .s,没有 .exe —— gcc/as 没返回,"
                         "属 runner 环境而非编译器)")
            else:
                stage = "emit 之前(无 .s —— lexer/parser/sema 或 emit 之中)"
            # 带上编译器自己的阶段标记 —— 它每阶段打一行
            # ([1] imports start / [3] sema start / [4] post-sema /
            #  [4a] ir_init done / [4b] cg_module done / [4] codegen done),
            # **它停在哪个标记之后就是精确的阶段**,与产物判定互补。
            # output/stderr 在 _run_capture 里已统一解码成 str,这里直接拼。
            marks = []
            for e in (first_timeout, exc2):
                text = (e.output or "") + (e.stderr or "")
                marks += [ln.strip() for ln in text.splitlines()
                          if ln.strip().startswith("[")]
            marks = list(dict.fromkeys(marks))
            tail = " → ".join(marks[-3:]) if marks else "(无阶段标记)"
            # 「编译器卡住」与「编译器早退了、孙进程占着管道」是两回事。
            if getattr(exc2, "child_exited", False):
                shape = (f"编译器**已退出**(rc={getattr(exc2, 'child_rc', None)})"
                         "——卡住的是管道:gcc/as 继承了 stdout/stderr 写端没关闭")
            else:
                shape = "编译器进程仍在运行 —— 它自己卡住了"
            return (False, expected, -4,
                    f"compile timeout ({timeout}s,重试后仍超时);{shape};"
                    f"卡在{stage};产物={have or '无'};最后阶段标记: {tail}")
        except Exception as exc:
            return (False, expected, -5, f"compile retry failed: {exc!r}")
    if rc != 0:
        # v1.7.0 Stage 1: EXPECT-ERROR test 期望 compile fail.
        # kw check 用 full stderr (compile 启动 log 可能 200+ 字符);
        # display msg 仍 truncate 200 字符 for human readability.
        if expect_error_kw is not None:
            if expect_error_kw in stderr_compile:
                return (True, None, -1, f"compile-failed (expected, kw={expect_error_kw!r})")
            return (False, None, -1,
                    f"compile failed but kw not found: expected={expect_error_kw!r}, "
                    f"got stderr[:200]={stderr_compile[:200]!r}")
        return (False, expected, -1, f"compile failed: {stderr_compile[:200]}")
    exe = os.path.abspath(out_base + ".exe")
    if not os.path.exists(exe):
        return (False, expected, -2, "exe not created")

    # Run
    try:
        actual, stdout_text, stderr_run = _run_capture([exe], timeout, test_env)
        output = stdout_text + stderr_run
    except subprocess.TimeoutExpired:
        return (False, expected, -3, f"timeout ({timeout}s)")

    # EXPECT-OUT check — runs regardless of whether EXPECT is present, so a
    # test can assert exit code and output independently (or output alone).
    # Only stdout: folding stderr in would let a compiler diagnostic that happens
    # to contain the expected text produce a false pass.
    if expect_out_kw is not None and expect_out_kw not in stdout_text:
        return (False, expected, actual,
                f"EXPECT-OUT not found: expected={expect_out_kw!r}, "
                f"got stdout[:200]={stdout_text[:200]!r}")

    if expected is None:
        # No EXPECT annotation: detect NTSTATUS (AV/heap/etc) → FAIL
        nt = ntstatus_name(actual)
        if nt is not None:
            return (False, None, actual, f"runtime crash: {nt} (0x{actual:08X})")
        return (True, actual, actual, output)
    # EXPECT present: if NTSTATUS, FAIL unless expected is that exact code
    nt = ntstatus_name(actual)
    if nt is not None:
        return (False, expected, actual, f"runtime crash: {nt} (0x{actual:08X})")
    # W-028: Windows process exit code is 8-bit (mod 256). On Linux / macOS
    # the exit code is full 32-bit. Compare on Windows with mod 256 to match
    # kernel32 behavior. (Why it ever worked: Python 3.12 subprocess.run on
    # Windows actually does return the truncated value via WaitForSingleObject
    # + GetExitCodeProcess — both honor kernel32 8-bit truncation.)
    #
    # sys.platform on MSYS2-launched Python is "cygwin" (not "win32")! CI
    # runner runs Python via `shell: msys2 {0}` in release.yml, so we get
    # "cygwin" / "msys". Detect any Windows-subsystem Python and apply mod-256.
    _IS_WINDOWS_PY = sys.platform in ("win32", "cygwin", "msys")
    if _IS_WINDOWS_PY and actual >= 0:
        actual_cmp = actual & 0xFF
        expected_cmp = expected & 0xFF
    else:
        actual_cmp = actual
        expected_cmp = expected
    # DEBUG W-028: print raw + cmp
    import os as _os
    if _os.environ.get("JHYY_DEBUG_W028"):
        print(f"[W-028] fname={os.path.basename(jhyy_file)} actual={actual} expected={expected} actual_cmp={actual_cmp} expected_cmp={expected_cmp} sys.platform={sys.platform} is_win_py={_IS_WINDOWS_PY}")
    return (actual_cmp == expected_cmp, expected, actual, output)


def _xfail_reason(fname: str) -> Optional[str]:
    """该测试是否带 `// XFAIL:` 标记;带则返回原因,不带返回 None。

    在 run_all 里重读一次文件,而不是让 run_test 多返回一个元素 —— run_test 的
    4-tuple 是 Public API(docstring 里写明),改它会波及 MCP tool 与 regress.py。
    """
    path = TEST_DIR / fname
    if not path.exists():
        return None
    try:
        from audit_test_assertions import directive_source
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    m = re.search(r"//\s*XFAIL\s*:\s*(.+)", directive_source(raw))
    return m.group(1).strip() if m else None


def _assertion_kind(fname: str) -> str:
    """这个测试的断言强度 —— PASS / vacuous / noassert。

    分类逻辑不在这里实现,直接复用 `scripts/dev/audit_test_assertions.py`
    (单一事实来源)。harness 和审计脚本若各判各的,两边迟早漂移,那时
    「汇总说 PASS、审计说违规」比没有分类更糟。
    """
    try:
        from audit_test_assertions import classify, EXAMPLES
    except Exception:
        # 审计模块不可用时**不**把测试降级成 noassert —— 宁可保持旧行为,
        # 也不要因为一次 import 失败就把一堆真测试从 PASS 里踢出去。
        return "PASS"
    path = EXAMPLES / fname
    if not path.exists():
        return "PASS"
    cls = classify(path)["class"]
    if cls == "crash-only":
        return "noassert"
    if cls == "literal-return":
        return "vacuous"
    return "PASS"


def run_all(
    binary: str,
    tests: Optional[List[str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    enforce_baseline_hash: bool = True,
    jobs: Optional[int] = None,
) -> dict:
    """跑全 regress (or 测试子集), 返回结构化 dict.

    Args:
        binary: 编译器路径 (相对 JHYY_ROOT 或绝对)
        tests:   测试文件子集 (None = 全部). 例 ["hello.jhyy", "fib.jhyy"]
        timeout: 单测试运行超时 (秒)
        enforce_baseline_hash: True 时跟 <binary>.sha256 比, 不匹配 → fail-fast

    Returns:
        {
            "ok": bool,
            "binary": str,
            "binary_sha256": str,
            "baseline_match": bool | None,    # None = no baseline file
            "baseline_sha256": str | None,
            "total": int, "passed": int, "failed": int, "skipped": int,
            "failed_tests": [{"file": str, "expected": int | None, "actual": int | None, "message": str}],
            "duration_sec": float,
            "baseline_warning": str | None,  # baseline file missing 时填
            "early_abort": str | None,        # binary drifted 时填
        }
    """
    bin_path = _resolve_binary(binary)
    start = time.time()

    # Early fail if binary missing (avoid _sha256_file FileNotFoundError crash)
    if not os.path.exists(bin_path):
        return {
            "ok": False,
            "binary": binary,
            "binary_sha256": None,
            "baseline_match": None,
            "baseline_sha256": None,
            "total": 0, "passed": 0, "failed": 0, "skipped": 0,
            "failed_tests": [],
            "passed_tests": [],
            "duration_sec": round(time.time() - start, 2),
            "baseline_warning": None,
            "early_abort": f"binary not found: {bin_path}",
        }

    # Freshness check: binary 是否在 src 之后被构建过. 取代之前的 .exe
    # sha 比对 (build 非确定性, .il byte-equal 才是真回归信号).
    if enforce_baseline_hash:
        current_sha = _sha256_file(bin_path)
        sha_path = bin_path + ".sha256"
        if not os.path.exists(sha_path):
            baseline_sha = None
            baseline_warning = (
                f"baseline file missing at {sha_path} — skipping hash check "
                f"(run `python -m jhyy_regress --save-baseline` to record a "
                f"build-time snapshot, informational only)"
            )
        else:
            with open(sha_path, encoding="utf-8") as f:
                baseline_sha = f.read().strip()
            baseline_warning = None
        is_fresh, freshness_msg = _check_baseline_freshness(bin_path)
        if not is_fresh:
            return {
                "ok": False,
                "binary": binary,
                "binary_sha256": current_sha,
                "baseline_match": None,
                "baseline_sha256": baseline_sha,
                "total": 0, "passed": 0, "failed": 0, "skipped": 0,
                "failed_tests": [],
                "duration_sec": time.time() - start,
                "baseline_warning": None,
                "early_abort": freshness_msg,
            }
        baseline_match = None  # sha drift 正常, 不再判定 match
    else:
        current_sha = _sha256_file(bin_path)
        baseline_sha = None
        baseline_match = None
        baseline_warning = "enforce_baseline_hash=False (skip check)"

    # Discover tests
    if tests is None:
        # 2026-10-15: 改 rglob,原来是 os.listdir(**不递归**)。
        # 后果:examples/ 下的 4 个子目录 —— arena_test/(Stage 0 自举验证)、
        # hello-freestanding/(freestanding + UEFI 路径)、multi_file/(多文件 import)、
        # namespace/(命名空间)—— 共 12 个 .jhyy **从来没进过全量回归**。
        # 它们只有被显式 `--tests=multi_file/main.jhyy` 点名时才跑。
        # 更糟的是 `scripts/dev/audit_test_assertions.py` 用的是 rglob(递归),
        # 于是审计脚本看得见这些文件、回归跑不到,两边长期对不上而没人发现。
        # 改成递归后 files 里是相对 TEST_DIR 的路径(如 `multi_file/main.jhyy`),
        # 下面的 `TEST_DIR / f` 拼接方式天然支持子目录。
        files = sorted(
            str(p.relative_to(TEST_DIR)).replace(os.sep, "/")
            for p in Path(TEST_DIR).rglob("*.jhyy")
            if not p.name.startswith("_")
        )
    else:
        files = tests

    passed, failed, skipped = 0, 0, 0
    failed_tests = []
    passed_tests = []
    # 2026-10-15 重构: 「PASS」只计**真的有断言且断言成立**的测试。
    # 以前三种东西在汇总行里长得一模一样:
    #   a) 断言了计算结果   b) main 返回写死的字面量(断言数学上不可能失败)
    #   c) 什么都没断言     —— 只有「进程没崩」
    # (c) 正是 W-109(浮点比较算错)在 `PASS EXIT=42` 里活了很多年的原因。
    # 现在 a 进 passed,b/c 各自另立类别并计数,汇总行直接把它们写出来 ——
    # 「X/Y 全绿」这句话从此不需要额外解释了。
    noassert_tests, vacuous_tests = [], []
    xfail_tests, xpass_tests = [], []
    # FLAKY:首次失败、隔离重跑通过。它**不是**通过(结果不可信),也不是失败
    # (重跑确实过了)—— 单列一类,汇总行点名。
    flaky_tests = []

    # jobs=None → 原行为(全并行);传 N 则限制并发。self-hosted 二进制
    # (jhyy_v2.exe)比 stage0 产物重 3-16x,185 路全并行时单个 compile 会
    # 因 CPU + gcc 争抢超过硬编码的 60s 超时 —— 那不是编译器 bug,是 harness
    # 并行度问题。--jobs 让人能把并发压下来真正跑到 self-hosted 二进制。
    _dev = str(Path(__file__).resolve().parents[1] / "scripts" / "dev")
    if _dev not in sys.path:
        sys.path.insert(0, _dev)

    # 默认并发 = cpu_count // 2,不是 cpu_count。
    #
    # 原因:一个「worker」不是单进程,是**一棵树** —— `jhyy.exe compile` 自己
    # 还会 fork `gcc`,`gcc` 再 fork `cc1`。N 个 worker 最多同时存在 3N 个进程。
    # 8 核机上实测(30 个样本,2026-10-15):
    #     --jobs=1   180s
    #     --jobs=4    45s   ← 拐点
    #     --jobs=8    43s
    #     --jobs=16   41s
    # 吞吐在 4 就饱和:4→16 只快 9%,但进程数翻 4 倍。默认取 cpu_count(=8)
    # 已在拐点之后,额外进程只会加剧争抢 —— 实测出现过单个 compile 从 3.5s
    # 劣化到 300s 超时的情况。
    #
    # 注意**单测编译本身就要 ~3.5s**,那是自举编译器自己的速度,不是 harness
    # 开销。197 个测试在 4 并发下约 172s,这是地板,调并发帮不上。
    cpu = os.cpu_count() or 4
    default_workers = max(2, cpu // 2)
    _t0 = time.time()
    workers = min(len(files), jobs if jobs else default_workers)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_test, str(TEST_DIR / f), binary, timeout): f for f in files}
        results = {futures[fut]: fut.result() for fut in as_completed(futures)}

    total_tests = len(files)
    for idx, fname in enumerate(files, 1):
        ok, exp, act, msg = results[fname]
        # 心跳:CI 上 GitHub 会折叠逐行输出,一个跑了 20 分钟的 regress step
        # 看不到任何中间信息 —— 只能干等,而「哪一步慢」是唯一有用的线索。
        # 每 20 个打一行进度 + 已用时,慢测试跑完立刻能看到它排在第几。
        if idx % 20 == 0 or idx == total_tests:
            print(f"[progress] {idx}/{total_tests} done, {time.time() - _t0:.0f}s elapsed",
                  flush=True)
        xfail = _xfail_reason(fname)
        if xfail is not None:
            # XFAIL 语义(2026-10-15):这个测试**应该失败**。
            #   失败 → XFAIL,预期内,不计入 suite 失败
            #   通过 → XPASS,说明 bug 被修好了却没摘标记 → **计入失败**
            # 「修好了必须有人看见」是 SKIP 给不了的:SKIP 根本不跑,修好了也不吭声。
            if ok and not (msg and msg.startswith("skipped")):
                print(f"XPASS {fname:<27}  (XFAIL 标记已过期 —— 对应 bug 似乎修好了,请摘掉 XFAIL)")
                xpass_tests.append(fname)
                failed += 1
                failed_tests.append({"file": fname, "expected": exp, "actual": act,
                                     "message": f"XPASS: XFAIL 标记过期 ({xfail})"})
            else:
                print(f"XFAIL {fname:<27}  {msg}"[:160])
                xfail_tests.append(fname)
            continue
        if ok and msg and msg.startswith("skipped"):
            # v1.7.3: SKIP directive + library skip 都走这条 path.
            print(f"SKIP  {fname:<30}  {msg}")
            skipped += 1
        elif ok:
            kind = _assertion_kind(fname)
            if kind == "vacuous":
                print(f"VACUOUS {fname:<27}  EXIT={act}   (有 EXPECT,但 main 返回写死字面量 —— 断言不可能失败)")
                vacuous_tests.append(fname)
            elif kind == "noassert":
                print(f"NOASSERT {fname:<27}  EXIT={act}   (无 EXPECT/EXPECT-OUT/EXPECT-ERROR —— 只验了没崩)")
                noassert_tests.append(fname)
            else:
                print(f"PASS  {fname:<30}  EXIT={act}")
                passed += 1
                passed_tests.append(fname)
        else:
            # ── FLAKY 检测(2026-10-18)────────────────────────────────────
            # 单测失败 → **隔离重跑一次**;过了就是 FLAKY,不算 suite 失败。
            #
            # 为什么要有:2026-10-18 反复观测到「全量里随机某个测试红、单跑必绿」。
            # 排除过的嫌疑(全否):产物名冲突(已修)、codegen 并发不确定(70 次并发
            # 编译 .s 逐字节相同)、栈帧算小(1004 函数零越界)、
            # `_section_directive.buf` 竞争(探针未观测到发作)、编译器临时文件
            # 重名(名字含 PID)。
            #
            # 没有这个机制时,每次偶发都要靠人回忆「上次是不是它」——而那正是
            # [[feedback_regress_flaky_rerun]] 说的:单次 FAIL 不能直接改代码,
            # 但也不能当没发生。
            #
            # ⚠️ 代价要说清楚:FLAKY **不阻断**。一个长期偶发的测试会一直绿,
            # 而它的间歇性可能正是真 bug(间歇性错代码比确定性错更危险)。
            # 对冲办法是它每次都**打印出来**并进汇总行与返回值 —— 它会出现在
            # 每一轮 CI 日志里,不是只出现一次。
            _retry_ok, _retry_exp, _retry_act, _retry_msg = run_test(
                str(TEST_DIR / fname), binary, timeout)
            if _retry_ok and not (_retry_msg or "").startswith("skipped"):
                print(f"FLAKY {fname:<27}  首次 FAIL(expected={exp} got={act}),"
                      f"隔离重跑 PASS(EXIT={_retry_act})  ← 间歇性问题,未阻断")
                flaky_tests.append({
                    "file": fname,
                    "first_failure": msg,
                    "first_expected": exp,
                    "first_actual": act,
                    "retry_actual": _retry_act,
                })
                # 不进 failed —— 但也不进 passed:它是「结果不可信」,不是「通过」。
                # 汇总里单列一类,理由见下。
                continue
            print(f"FAIL  {fname:<30}  expected={exp} got={act}  {msg}")
            if not _retry_ok:
                print(f"      └─ 隔离重跑仍失败: expected={_retry_exp} got={_retry_act}  {_retry_msg}")
            failed += 1
            failed_tests.append({
                "file": fname,
                "expected": exp,
                "actual": act,
                "message": msg,
                "retry_message": _retry_msg if not _retry_ok else None,
            })

    duration = time.time() - start
    _flaky_note = f", {len(flaky_tests)} FLAKY(未计 passed)" if flaky_tests else ""
    print(f"\n===== {passed}/{passed + failed} passed (全部有断言), {failed} failed, "
          f"{skipped} skipped{_flaky_note} (of {len(files)} total) =====")
    print(f"  ├─ NOASSERT {len(noassert_tests)}  无断言,只验了「进程没崩」")
    print(f"  ├─ VACUOUS  {len(vacuous_tests)}  有 EXPECT 但断言在数学上不可能失败")
    print(f"  ├─ XFAIL    {len(xfail_tests)}  预期内失败(已知 bug,真跑了)")
    if flaky_tests:
        print(f"  ├─ FLAKY    {len(flaky_tests)}  ⚠️ 全量里红、隔离重跑绿 —— 间歇性问题,未阻断")
        for f in flaky_tests:
            print(f"  │            {f['file']}: 首次 {f['first_failure']}"
                  f" → 重跑 EXIT={f['retry_actual']}")
    if xpass_tests:
        print(f"  ├─ XPASS    {len(xpass_tests)}  ⚠️ XFAIL 标记已过期 —— 对应 bug 修好了但没摘标记")
    if noassert_tests or vacuous_tests:
        print("  └─ ⚠️ 上面两类**不是 PASS**。它们仍会跑(能抓编译器崩溃),但验证不了"
              "任何计算结果。逐个补断言见 docs/internal/tests.md。")

    # Sprint mcp-2: cleanup _regress_* artifacts for tests that didn't fail.
    # Pass → clean dir after run; Fail → keep .il/.s/.exe for inspection
    # (per feedback_il_s_debugging_pattern: .il 比 gdb 无符号更有效).
    #
    # 2026-10-18: 走 artifact_slug(),与 run_test() 的建名保持一致。
    # 原来这里用 splitext(fname)[0] 而 run_test 用 splitext(basename(...))[0],
    # 两边算法不同:子目录测试(multi_file/main.jhyy)在这里被算成
    # 「_regress_multi_file/main.il」—— 一个 run_test 从不产生的路径,
    # 于是清理永远不触发。工作树里实测躺着 _regress_main.exe /
    # _regress_arena_test.s 就是这么来的。
    failed_names = {artifact_slug(ft["file"]) for ft in failed_tests}
    cleaned = 0
    for fname in files:
        name = artifact_slug(fname)
        if name not in failed_names:
            for ext in (".il", ".s", ".exe"):
                p = str(JHYY_ROOT / "compiler/build/bin" / f"_regress_{name}{ext}")
                try:
                    os.remove(p)
                    cleaned += 1
                except FileNotFoundError:
                    pass
    if cleaned > 0:
        print(f"  (cleaned {cleaned} _regress_* artifacts; failed tests preserved)")

    return {
        "ok": failed == 0,
        "binary": binary,
        "binary_sha256": current_sha,
        "baseline_match": baseline_match,
        "baseline_sha256": baseline_sha,
        "total": len(files),
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "failed_tests": failed_tests,
        # 2026-10-15: passed 只含真有断言的;下面两类单独计数,不再混进绿里。
        "passed_tests": passed_tests,
        "noassert_tests": noassert_tests,
        "vacuous_tests": vacuous_tests,
        "xfail_tests": xfail_tests,
        "xpass_tests": xpass_tests,
        "flaky_tests": flaky_tests,
        "duration_sec": round(duration, 2),
        "baseline_warning": baseline_warning,
        "early_abort": None,
    }


# CLI for `python -m jhyy_regress --save-baseline <binary>` style usage
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="JHYY regress runner (shared logic)")
    ap.add_argument("--binary", default="compiler/build/bin/jhyy.exe",
                    help="Compiler binary path (relative JHYY root or absolute)")
    ap.add_argument("--save-baseline", action="store_true",
                    help="Record current binary sha256 as a build-time snapshot "
                         "(informational only — .exe sha is non-deterministic, "
                         ".il byte-equal is the real regression signal)")
    ap.add_argument("--no-baseline-check", action="store_true",
                    help="Skip phantom-binary (mtime) check")
    ap.add_argument("--tests", nargs="*", default=None,
                    help="Subset of tests to run (default: all)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help="死循环探测上限(秒),compile 与 run 各自适用。"
                         "刻意给得很宽:它要抓的是永不返回的无限循环,不是性能预算 —— "
                         "并行跑时单个 compile 会被 CPU 争抢拉长好几倍,"
                         "拿它当性能线会误杀慢测试")
    args = ap.parse_args()

    if args.save_baseline:
        sha = save_baseline_hash(args.binary)
        print(f"Saved baseline: {args.binary}.sha256 = {sha}")
        sys.exit(0)

    result = run_all(
        binary=args.binary,
        tests=args.tests,
        timeout=args.timeout,
        enforce_baseline_hash=not args.no_baseline_check,
    )
    if result["early_abort"]:
        print(f"[ABORT] {result['early_abort']}", file=sys.stderr)
    sys.exit(0 if result["ok"] else 1)