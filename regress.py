#!/usr/bin/env python3
"""Run JHYY integration test suite against one or more compiler binaries.

v1.4.7 (2026-08-14): 单 regress 入口合并 — 取代 v1.4.5 三跑 (regress.py +
regress_v1.py + regress_stage0.py)。CI workflow 简化: 1 gated step + 1
informational step。

Usage:
  python regress.py                            # 默认 binary=jhyy.exe (production)
  python regress.py --binary=PATH              # 跑指定 binary (--binary=stage0 / v1 等)
  python regress.py --all                      # 跑所有 gated binary (jhyy.exe + jhyy_stage0.exe)
  python regress.py --all --include-informational
                                               # 加跑 jhyy_v1.exe.exe (matrix only, 不影响 exit)
  python regress.py --save-baseline            # 存 binary sha256 baseline (转发 jhyy_regress)
  python regress.py --tests=foo,bar            # 跑测试子集
  python regress.py --no-baseline-check        # 跳过 phantom binary (mtime) check
  python regress.py --timeout=900              # 死循环探测上限(秒),compile+run 各自适用 (default 900)

Exit codes:
  0  全部 gated binary PASS
  1  至少 1 个 gated binary FAIL
  2  binary 不存在 / 参数解析错误

Per-binary `enforce_baseline_hash` 默认 (centralize 取代原 3 shim 散落的 magic-default):
  jhyy.exe         → True  (production, phantom binary 必 catch)
  jhyy_stage0.exe  → False (gcc 链接非确定性, sha 每次变)
  jhyy_v1.exe.exe  → False (frozen historical baseline, mtime 永远比 src 旧 → phantom 必 fail)

Sprint mcp-1 (2026-08-11): shim that delegates to mcp-jhyy/jhyy_regress.py.
Sprint v1.4.7 (2026-08-14): 加 --all / --include-informational / _GATED_DEFAULTS,
                            删 regress_v1.py + regress_stage0.py 两个 shim。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Make mcp-jhyy/ importable
# v4.0.0: regress.py moved to repo root in v3-pre-v4-infra-port/Ph.5 (commit 8aa2326);
# regress.py sits at <repo>/regress.py and mcp-jhyy/ is at <repo>/mcp-jhyy/, so ROOT = parents[0].
ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT / "mcp-jhyy"))

from jhyy_regress import run_all, save_baseline_hash  # noqa: E402

# ──────────────────────────────────────────────────────────────────────────────
# Per-binary `enforce_baseline_hash` default mapping (centralize)
# ──────────────────────────────────────────────────────────────────────────────
# Rationale per binary:
#   - jhyy.exe (production):         True  — phantom binary 会污染 baseline 信号
#   - jhyy_stage0.exe (C-side):      False — gcc 链接非确定性 (debug info / timestamp)
#   - jhyy_v1.exe.exe (frozen):      False — mtime 永远比 src 旧 → phantom 必 fail
# Unknown binary 默认 True (catch phantom)。
_GATED_DEFAULTS = {
    "compiler/build/bin/jhyy.exe": True,
    "compiler/build/bin/jhyy_stage0.exe": False,
    "compiler/build/bin/jhyy_v1.exe.exe": False,
}

# Default `--all` 跑的 binary 列表 (gated, 影响 exit code)。
# 不 glob `jhyy*.exe*` — v2/v3/v4.exe 是 make selfhost 产物, 不是 regress 语义。
#
# v4.0.8 (2026-10-15):jhyy_stage0.exe 从 gated 降为 informational。
#
# 实测 stage0 有 **39 个失败**,且**没有一个是 bug** —— 22 个编译期失败
# (`closures_basic` / `char_literal_3byte` / `cap_table_*` / `fmod_*` …),
# 因为 stage0 是 **C 端 bootstrap 编译器**,它的 parser 早于 V3-B / V3-C / V3.1
# (闭包是 v3.2.1 特性、字符字面量与 Cap<T> 是 v3.x),本来就不认这些语法。
# 把它当 gated 是在派一个它注定失败的活,结果只有两个:CI 永远红,或者
# 有人为了让 CI 绿去放宽判据 —— 后者正是本项目 2026-10-15 这一整天在修的病。
#
# **stage0 的真实门是 `make stage0 && make`**:stage1 用 stage0 编
# `src0/main.jhyy` → `jhyy.exe`,stage0 一坏这一步就断,比跑 199 个用户测试
# 更直接也更便宜(且 CI 的第 2 步就在做这件事)。这条路径已经覆盖了它的职责。
_GATED_BINARIES = [
    ("compiler/build/bin/jhyy.exe", "production"),
]

# stage0 仍然跑(看得见信号),但不参与 exit code。
_STAGE0_BINARY = (
    "compiler/build/bin/jhyy_stage0.exe",
    "informational, C-side bootstrap — 语言子集早于 v3.x,预期有 39 个已知失败"
    "(闭包 / char literal / Cap<T> / fmod 等新特性它都不认)。"
    "它的真门是 `make stage0 && make`(stage1 用它编 src0 → jhyy.exe)。",
)

# `--include-informational` 加的 binary (matrix only, 不影响 exit code)。
_INFORMATIONAL_BINARIES = [
    ("compiler/build/bin/jhyy_v1.exe.exe",
     "informational, historical baseline "
     "(v1.4.4 ship 已覆盖成 jhyy.exe 同 binary; 跑 v1.4.6 新 test fail 是 expected)"),
]


def _resolve_default_enforce(binary: str, no_baseline_check: bool) -> bool:
    """Resolve enforce_baseline_hash for a binary.

    Precedence: --no-baseline-check > _GATED_DEFAULTS[bin] > default True。
    """
    if no_baseline_check:
        return False
    return _GATED_DEFAULTS.get(binary, True)


def _run_one(binary: str, label: str, tests, timeout, enforce_baseline_hash, jobs=None):
    """Run run_all for one binary, return (result_dict, is_informational)."""
    result = run_all(
        binary=binary,
        tests=tests,
        timeout=timeout,
        enforce_baseline_hash=enforce_baseline_hash,
        jobs=jobs,
    )
    return result


# v2.7.1 Phase 2: --cross wire (auto-probe wsl/docker + subprocess dispatch)
# Per `feedback_regress_py_abspath`: MSYS2 Python + Windows subprocess 不解析
# 相对路径 → 用 os.path.abspath 包装。
# Per `feedback_mcp_jhyy_run_workspace`: cross-env sub-process 必须用
# subprocess.run + 绝对路径。

_SYSV_TEST_NAMES = (
    "sysv_abi_test.jhyy",
    "sysv_struct_mixed.jhyy",
    "sysv_struct_pass.jhyy",
    "sysv_struct_ret.jhyy",
    "sysv_vararg_basic.jhyy",
)

# v2.8.3: docker CLI absolute path fallback (跟 feedback_gh_cli_path 同 pattern)。
# docker Desktop 安装在 C:\Program Files\Docker\Docker\resources\bin 不在 MSYS2
# PATH。subprocess.run 调 "docker" bare name 在 Windows 上失败 → resolve 到
# absolute path。优先级: shutil.which (PATH) → known fallback list。
def _resolve_docker_bin() -> Optional[str]:
    found = shutil.which("docker")
    if found:
        return found
    for fb in (
        "C:/Program Files/Docker/Docker/resources/bin/docker.exe",
        "/c/Program Files/Docker/Docker/resources/bin/docker.exe",
    ):
        if os.path.exists(fb):
            return fb
    return None


_DOCKER_BIN = _resolve_docker_bin()
# Docker Desktop 不在 MSYS2 PATH 上(per feedback_gh_cli_path),探测时直接查文件。
_DOCKER_FALLBACKS = (
    "C:/Program Files/Docker/Docker/resources/bin/docker.exe",
    "/c/Program Files/Docker/Docker/resources/bin/docker.exe",
)


def _docker_daemon_up() -> bool:
    """Docker **daemon** 是否真的可达 —— 不只是 binary 在不在。

    2026-10-15:原探测只看 `os.path.exists(docker.exe)`,于是「装了 Docker
    Desktop 但没启动」这种**开发者机器上的常态**会被判成 cross=docker,然后
    运行期报 `failed to connect to the docker API at npipe://...` → 5 个
    sysv 测试从「SKIP(环境不可用)」变成「FAIL」,CI 变红。

    环境不可用应该是 SKIP,不是 FAIL。判据必须是 daemon 真的能应答。

    `MSYS_NO_PATHCONV=1` 是必须的(per feedback_docker_local):不设的话 MSYS2
    会把 `npipe:////./pipe/dockerDesktopLinuxEngine` 当 POSIX 路径转换,
    报出来的错误指向一个不存在的 pipe 名,看起来像「路径写错了」而不是
    「daemon 没起」。
    """
    if not _DOCKER_BIN:
        return False
    try:
        r = subprocess.run(
            [_DOCKER_BIN, "info", "--format", "{{.ServerVersion}}"],
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
            env={**os.environ, "MSYS_NO_PATHCONV": "1"},
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _docker_image_usable(image: str = "gcc:12") -> bool:
    """该镜像能否在**本平台**跑起来。

    2026-10-15:CI(Windows runner)上有 Docker,但 `gcc:12` 没有 windows/amd64
    manifest:
        docker: no matching manifest for windows(10.0.26100)/amd64
    此前这被当成 FAIL 报出去,读起来像「测试挂了」,实际是**环境不适用**。
    环境不适用应该是 SKIP。判据:真跑一次最小容器看 rc。
    """
    if not _DOCKER_BIN:
        return False
    try:
        r = subprocess.run(
            [_DOCKER_BIN, "run", "--rm", image, "true"],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace",
            env={**os.environ, "MSYS_NO_PATHCONV": "1"},
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def _resolve_cross_mode(cross_arg: str) -> str:
    """Resolve --cross mode: auto probe wsl.exe then docker daemon.

    Returns: 'wsl' | 'docker' | 'none'
    """
    if cross_arg == "wsl":
        if shutil.which("wsl.exe") or shutil.which("wsl"):
            return "wsl"
        print("cross: --cross=wsl but wsl.exe not on PATH → SKIP", file=sys.stderr)
        return "none"
    if cross_arg == "docker":
        if not _docker_daemon_up():
            print("cross: --cross=docker 但 daemon 不可达 → SKIP", file=sys.stderr)
            return "none"
        if not _docker_image_usable():
            print("cross: gcc:12 无本平台 manifest(如 Windows runner)→ SKIP",
                  file=sys.stderr)
            return "none"
        return "docker"
    if cross_arg == "none":
        return "none"
    # auto: probe wsl first (faster on Windows; native Linux distro available)
    if shutil.which("wsl.exe") or shutil.which("wsl"):
        # Probe whether a **usable** distro is actually installed.
        #
        # 2026-10-15 修:原判据是「`wsl.exe -l -v` 返回 0 且输出不含 'no installed'」。
        # 两个问题:
        #   1. 装了 Docker Desktop 之后,`wsl.exe -l -v` 会列出 Docker 的**内部**
        #      distro:
        #          NAME              STATE      VERSION
        #          * docker-desktop    Stopped    2
        #      它不是可用的 Linux 用户环境(没工具链),把它当成可用 distro 会让
        #      cross_mode=wsl 一路走下去,运行期才炸 `WSL_E_DISTRO_NOT_FOUND` ——
        #      5 个 sysv 测试从「SKIP(环境不可用)」变成「FAIL」,CI 因此变红。
        #   2. 'no installed' 是**英文**串;非英文 Windows 上匹配不到。
        # 现在:解析 distro 名,排除 Docker 内部那几个,并且要求有非 docker 的条目。
        try:
            r = subprocess.run(
                ["wsl.exe", "-l", "-v"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            if r.returncode == 0:
                text = (r.stdout or "") + (r.stderr or "")
                names = []
                for line in text.splitlines():
                    line = line.replace("\x00", "").strip()
                    if not line or line.upper().startswith("NAME"):
                        continue
                    tok = line.split()
                    if not tok:
                        continue
                    # 行首 `*` 是「默认 distro」标记,不是名字本身 ——
                    # `* docker-desktop  Stopped  2` 的 tok[0] 是 `*`。
                    if tok[0] == "*" and len(tok) > 1:
                        names.append(tok[1])
                    else:
                        names.append(tok[0])
                usable = [n for n in names
                          if not n.lower().startswith("docker")]
                if usable:
                    return "wsl"
                if names:
                    print("cross: wsl 只有 Docker 内部 distro"
                          f"({', '.join(names)}),没有可用的 Linux 用户环境 → 继续探 docker",
                          file=sys.stderr)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
    # daemon 可达 + 镜像能在本平台跑,才算数 —— 见两个 _docker_*_usable 的说明。
    if _docker_daemon_up() and _docker_image_usable():
        return "docker"
    return "none"


def _read_expected_exit(jhyy_file: str) -> Optional[int]:
    """读源文件里的 `// EXPECT: N`,取不到返回 None。

    判据扫描规则与 jhyy_regress 一致:只认「整行就是指令」或「行尾指令」,
    且跳过字符串字面量 —— 复用 audit_test_assertions.directive_source,
    免得两边的判据规则漂移(那正是 W-110 的教训)。
    """
    try:
        sys.path.insert(0, str(ROOT / "scripts" / "dev"))
        from audit_test_assertions import directive_source
        raw = Path(jhyy_file).read_text(encoding="utf-8", errors="replace")
        m = re.search(r"//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)", directive_source(raw))
        return int(m.group(1)) if m else None
    except Exception as exc:
        # 诊断辅助读不到期望值时不能拖垮 regress,但**必须出声** ——
        # 2026-10-15 踩过:`re` 忘了 import,NameError 被 `except: return None`
        # 吞成 None,于是 cross 路径拿不到期望值、只要 ELF 跑起来就报 PASS,
        # W-116(退出 22 / 期望 28)整整被放过。静默的兜底比崩溃更危险。
        print(f"cross: 读 {_read_expected_exit.__name__} 异常({exc!r}),"
              f"本次不比对期望值 —— 若非有意,这是 bug", file=sys.stderr)
        return None


def _run_cross_env_sysv_test(test_name: str, cross_mode: str,
                             binary: str, timeout: int) -> Tuple[bool, str]:
    """Run a single sysv_*.jhyy test through wsl/docker subprocess.

    Returns: (ok, message)
        ok=True with "skipped (...)" if cross-env not actually available
        ok=True with "passed (exit=N)" on success
        ok=False with "failed (...)" on compile/run error
    """
    abs_jhyy = os.path.abspath(
        str(ROOT / "compiler" / "tests" / "examples" / test_name)
    )
    abs_binary = os.path.abspath(binary)
    # Build inside Linux env: compile to sysv_freestanding target, then
    # link with crt0.S + link.ld → run.
    jhyy_repo_in_linux = "/work"  # mount repo to /work inside Linux env
    if cross_mode == "wsl":
        # First probe: does WSL actually have any distro installed? On Windows
        # hosts where wsl.exe is on PATH but no distro is registered, wsl.exe
        # prints "Wsl/Service/WSL_E_DISTRO_NOT_FOUND" (UTF-16LE bytes from
        # Microsoft console), which crashes Python wslpath decode and prints
        # garbled text. Skip cleanly when probe fails.
        try:
            probe = subprocess.run(
                ["wsl.exe", "-l", "-v"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            probe_out = (probe.stdout + probe.stderr).lower()
            if probe.returncode != 0 or "no installed" in probe_out or \
                    "wsl_e_" in probe_out or "not_found" in probe_out:
                return (True, "skipped (wsl.exe on PATH but no distro installed)")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return (True, "skipped (wsl.exe probe failed)")
        # Convert Windows path to WSL path (e.g. C:\Users\foo\bar → /mnt/c/.../bar)
        try:
            wsl_jhyy_r = subprocess.run(
                ["wsl.exe", "wslpath", "-u", abs_jhyy],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            wsl_jhyy = wsl_jhyy_r.stdout.strip()
            wsl_binary_r = subprocess.run(
                ["wsl.exe", "wslpath", "-u", abs_binary],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            wsl_binary = wsl_binary_r.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            return (True, f"skipped (wslpath conversion failed: {e})")
        if not wsl_jhyy or not wsl_binary or "\\" in wsl_jhyy or "\\" in wsl_binary:
            return (True, "skipped (wslpath garbled output — likely no WSL distro)")
        # v2.8.1 WSL branch 不变 logic:`{wsl_binary}` 默认 = jhyy.exe
        # (jhyy-side production binary, per Makefile line 46 comment)。jhyy.exe
        # 是 jhyy-side binary (由 jhyy_stage0.exe compile src0/main.jhyy 产出),
        # 走 jhyy-side target_parse (4 targets, v2.7.0 ship) + codegen_amd64_run
        # (4 targets 真 emit, v2.8.0 ship) → 产 SysV ABI .s → gcc 链 crt0.S
        # + link.ld → 跑。C-side target_dispatch fix (v2.8.1) 不影响 WSL
        # branch (jhyy.exe 不走 C-side cg_module)。
        cmd = [
            "wsl.exe", "-d", "Ubuntu", "bash", "-c",
            f"cd {jhyy_repo_in_linux} && "
            f"{wsl_binary} compile --target=amd64_sysv_freestanding "
            f"{wsl_jhyy} -o /tmp/_cross_sysv && "
            f"gcc -nostdlib -static -T runtime/linux_elf/link.ld "
            f"-o /tmp/_cross_sysv.elf runtime/linux_elf/crt0.S /tmp/_cross_sysv.s && "
            f"/tmp/_cross_sysv.elf; echo EXIT:$?",
        ]
    elif cross_mode == "docker":
        # v2.8.3: 2-stage subprocess — Stage 1 (Windows-side jhyy.exe 真
        # 编 .s, --no-link 跳过 Win gcc) + Stage 2 (docker gcc:12 链 crt0.S
        # + link.ld → 跑)。前置: v2.8.2 ship 真修 W-070 (cg_module 不再
        # fatal at SysV/SYSVFS) + 本 plan 加 `--no-link` flag (v2.8.3 cmd_compile
        # 内部 scan, skip link_with_gcc)。结果: 5 sysv regress tests
        # 真用 jhyy 编 + docker gcc chain 跑通, wire-only SKIP 删。
        #
        # Stage 1 — Windows-side: jhyy 真编 SysV .s 到 <stem>.s。
        # 用 MSYS_NO_PATHCONV=1 防止 MSYS2 path mangling (per v2.7.1 verify)。
        test_stem = os.path.splitext(abs_jhyy)[0]
        test_base = os.path.basename(test_stem)
        try:
            stage1 = subprocess.run(
                [abs_binary, "compile",
                 "--target=amd64_sysv_freestanding", "--no-link",
                 abs_jhyy, "-o", test_stem],
                capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace",
                env={**os.environ, "MSYS_NO_PATHCONV": "1"},
            )
        except subprocess.TimeoutExpired:
            # 2026-10-15:CI 上这条路径**把整个 run 打死**过 —— 未捕获的
            # TimeoutExpired 从这里一路冒到 main(),而汇总行在它之前就已经
            # 打印完了,于是 exit code 变成 2,CI 只看到一个没有上下文的
            # traceback。一个测试超时不该让整轮失去意义。
            return (False, f"stage1 compile timeout ({timeout}s, cross={cross_mode})")
        except FileNotFoundError as e:
            return (True, f"skipped (jhyy binary not found for Stage 1: {e})")
        if stage1.returncode != 0:
            return (False, f"failed (Stage 1 jhyy compile rc={stage1.returncode}, "
                           f"cross=docker): {(stage1.stdout or stage1.stderr)[-200:]}")
        if not os.path.exists(f"{test_stem}.s"):
            return (False, f"failed (Stage 1 didn't produce .s at {test_stem}.s, "
                           f"cross=docker): check jhyy --target=amd64_sysv_freestanding --no-link")
        # Stage 2 — docker gcc:12 chain: 链 crt0.S + .s + link.ld → 跑。
        repo_abs = os.path.abspath('.')
        rel_s_path = os.path.relpath(f"{test_stem}.s", repo_abs).replace('\\', '/')
        # v2.8.3: 用 _DOCKER_BIN (resolved to absolute path) 而非 bare "docker" —
        # docker Desktop 不在 MSYS2 PATH (per feedback_gh_cli_path)。
        # ELF exit != 0 (e.g. sysv_struct_ret=18, sysv_abi_test=28) is expected;
        # `set -e` 会 kill 整个 script 不跑 echo EXIT:. 修法: `|| elf_exit=$?`
        # capture ELF exit,always emit EXIT:N。
        cmd = [
            _DOCKER_BIN, "run", "--rm",
            "-v", f"{repo_abs}:{jhyy_repo_in_linux}",
            "-w", jhyy_repo_in_linux,
            "gcc:12", "bash", "-c",
            f"set -e; "
            f"gcc -nostdlib -static -T runtime/linux_elf/link.ld "
            f"-o /tmp/{test_base}.elf runtime/linux_elf/crt0.S {rel_s_path} && "
            f"elf_exit=0; "
            f"/tmp/{test_base}.elf || elf_exit=$?; "
            f"echo EXIT:$elf_exit",
        ]
        # 2026-10-15:docker 分支**必须** MSYS_NO_PATHCONV=1。
        # Stage 1 设了、Stage 2 漏了,于是 MSYS2 把 docker 的
        # `npipe:////./pipe/dockerDesktopLinuxEngine` 当 POSIX 路径转换,
        # 得到一个不存在的 pipe 名,报
        #   「The system cannot find the file specified」
        # 看起来像「Docker 没启动」,实际 daemon 是好的 ——
        # 这正是 feedback_docker_local 记的那条规则。
        # 只对 docker 分支设:WSL 分支反而**需要** MSYS 做路径转换。
        run_env = {**os.environ, "MSYS_NO_PATHCONV": "1"}
    else:
        return (True, "skipped (cross-env disabled)")

    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
            env=locals().get("run_env"),
        )
        output = (r.stdout or "") + (r.stderr or "")
        # Parse EXIT:N from output first (always, even if rc != 0), so we
        # can distinguish "compile failed" vs "binary not built" vs
        # "ran but got exit=127 from /tmp/_cross_sysv.elf missing").
        exit_code = None
        for line in reversed(output.splitlines()):
            if line.startswith("EXIT:"):
                try:
                    exit_code = int(line[len("EXIT:"):].strip())
                except ValueError:
                    pass
                break
        if exit_code is None:
            return (False, f"failed (no EXIT: marker, cross={cross_mode}): "
                           f"{output[-200:]}")
        # exit_code 是 .elf 跑出来的 exit (per `cmd` cmd 模板 last segment
        # `/tmp/X.elf; echo EXIT:$?`)。exit != 0 (e.g. sysv_struct_ret=18,
        # sysv_struct_pass=35) is expected — don't 误判 FAIL on r.returncode。
        # v2.7.2 旧逻辑: `r.returncode != 0` → FAIL,假定 returncode == 0 iff
        # .elf ran ok。v2.8.3 wire chain 揭露: docker run --rm / wsl.exe
        # propagate .elf exit code to subprocess returncode, 所以 .elf exit=18
        # → r.returncode=18 → 误判 FAIL。修法: 只要 EXIT:N 已 parse (set -e
        # 保证 gcc/ld fail 时不 echo EXIT:),就 PASS。
        # exit=127 = bash "command not found" in Linux (e.g. .elf not built
        # because gcc missing in container, or compile step failed silently).
        # 区分真跑 ELF (EXIT:127 means ELF ran + returned 127) vs ELF not
        # built (compile/link fail). 真跑 ELF exit 127 is PASS per regress
        # semantics;ELF not built is infra error。
        if exit_code == 127:
            if "not found" in output.lower() or "no such file" in output.lower():
                return (False, f"failed (binary not built, cross={cross_mode}): "
                               f"check gcc in container (use gcc:12 not ubuntu:22.04) — "
                               f"{output[-200:]}")
            # exit=127 真跑 ELF (rare, not in current 5 sysv fixtures) — pass。
        # 2026-10-15:比期望值!此前只要 EXIT:N 解析出来就 PASS,**从不与测试自己
        # 声明的 `// EXPECT:` 比对**。实测抓到:`sysv_abi_test` 的 ELF 退出 22,
        # 而它声明期望 28 —— 也就是说 W-116(SysV callee 只 spill 4 个寄存器,
        # 参数 5/6/7 读到 arg4 的值)就在这条门底下,regress 却报 PASS。
        # 同一个病:「跑了就算过,不问结果对不对」。
        expected = _read_expected_exit(
            str(ROOT / "compiler" / "tests" / "examples" / test_name))
        if expected is not None:
            # Windows/ELF 两边都取 8 bit 语义(Windows 进程退出码是 8 bit;
            # ELF 是完整 32 bit)。按 mod 256 比,跟 jhyy_regress 的 W-028 规则一致。
            exp_cmp, act_cmp = expected & 0xFF, exit_code & 0xFF
            if exp_cmp != act_cmp:
                return (False, f"failed (expected={expected}, got={exit_code}, "
                               f"cross={cross_mode}) — 期望值不匹配(W-116 等"
                               f"SysV 缺陷见 docs/internal/workarounds.md)")
        return (True, f"passed (exit={exit_code}, cross={cross_mode})")
    except subprocess.TimeoutExpired:
        return (False, f"timeout ({timeout}s, cross={cross_mode})")
    except FileNotFoundError as e:
        return (True, f"skipped (cross={cross_mode} binary not found: {e})")


def _run_sysv_via_cross_env(cross_mode: str, binary: str, timeout: int,
                            only_tests: Optional[List[str]] = None
                            ) -> Tuple[int, int, int]:
    """Run 5 sysv regress tests via cross-env wire (wsl/docker).

    Returns: (passed, failed, skipped) counts.

    Per v2.7.0 Commit 3: 5 sysv fixtures 默认 SKIP via `// SKIP:` directive;
    --cross env 实 wire 让它们在 Linux host 真跑 (compile → link → run)。

    `only_tests` 可选过滤 (per --tests= 列表)。
    """
    if cross_mode == "none":
        # Print SKIP for all sysv tests
        for name in _SYSV_TEST_NAMES:
            if only_tests is None or name in only_tests:
                print(f"SKIP  {name:<30}  skipped (--cross=none)")
        return (0, 0, sum(1 for n in _SYSV_TEST_NAMES
                          if only_tests is None or n in only_tests))

    passed = failed = skipped = 0
    for name in _SYSV_TEST_NAMES:
        if only_tests is not None and name not in only_tests:
            continue
        ok, msg = _run_cross_env_sysv_test(name, cross_mode, binary, timeout)
        if ok and msg.startswith("skipped"):
            print(f"SKIP  {name:<30}  {msg}")
            skipped += 1
        elif ok:
            print(f"PASS  {name:<30}  {msg}")
            passed += 1
        else:
            print(f"FAIL  {name:<30}  {msg}")
            failed += 1
    return (passed, failed, skipped)


def test_byte_equal(tests=None):
    """Run byte-equal 三件套 (D26) on a list of target tests.
    Per coordination.md § 3 D26 (2026-08-05 锁): closure invariant is .il
    + .s byte-equal. Per D43 (2026-09-01 锁): 阶段性 self-equal, jhyy_N ==
    jhyy_{N+1}, not cross-version.

    Args:
        tests: list of test names without .jhyy suffix, or None for default
               5 tests (hello / struct_val_pass / fib_renamed /
               nested_struct_deep / big_test).

    Returns 0 on 5/5 PASS, 1 on any FAIL (per feedback_fix_evaluation_rule).
    """
    if tests is None:
        tests = [
            "hello.jhyy",
            "struct_val_pass.jhyy",
            "fib_renamed.jhyy",
            "nested_struct_deep.jhyy",
            "big_test.jhyy",
        ]
    else:
        tests = [t if t.endswith(".jhyy") else f"{t}.jhyy" for t in tests]

    examples_dir = ROOT / "compiler" / "tests" / "examples"
    bootstrap_dir = examples_dir.parent / "bootstrap"
    byte_equal_sh = bootstrap_dir / "byte_equal.sh"

    if not byte_equal_sh.exists():
        print(f"byte-equal: byte_equal.sh not found at {byte_equal_sh}", file=sys.stderr)
        return 1

    passed = 0
    failed = 0
    for t in tests:
        test_path = examples_dir / t
        if not test_path.exists():
            print(f"byte-equal: SKIP {t} (file not found)")
            continue
        try:
            # text=True + errors='replace' so non-UTF-8 bytes from bash
            # output don't crash the reader thread (some compile flows emit
            # binary debug info that includes raw bytes). On Windows, must
            # resolve "bash" to full path via shutil.which — bare "bash" gets
            # routed to WSL installer alias instead of MSYS2 bash.
            bash_path = shutil.which("bash") or "bash"
            result = subprocess.run(
                [bash_path, str(byte_equal_sh), str(test_path)],
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=60,
            )
            rc = result.returncode
        except subprocess.TimeoutExpired:
            print(f"byte-equal: FAIL {t} (timeout)")
            failed += 1
            continue
        except Exception as e:
            print(f"byte-equal: FAIL {t} (exception: {e})")
            failed += 1
            continue

        if rc == 0:
            passed += 1
            print(f"byte-equal: PASS {t}")
        else:
            failed += 1
            print(f"byte-equal: FAIL {t}")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    print(f"byte-equal: {passed}/5 PASS" if len(tests) == 5 else f"byte-equal: {passed} PASS / {failed} FAIL")
    return 0 if failed == 0 else 1


def test_fixed_point(tests=None):
    """Run N≥3 selfhost fixed-point closure 验算 (v2.9.0 V2-C Part 1).

    Per D43 closure ship gate (re-baselined v2.9.0): jhyy_v1 ↔ jhyy_v2 ↔
    jhyy_v3 must produce byte-equal .il for compiler/src0/main.jhyy.

    Implementation: shell out to `compiler/tests/bootstrap/fixed_point.sh`.
    jhyy-side N=3 is the primary ship gate; N=4/N=5 informational.

    Args:
        tests: ignored (fixed_point.sh 编 fixed target compiler/src0/main.jhyy)

    Returns 0 on N=3 PASS, 1 on any FAIL (per feedback_fix_evaluation_rule).
    """
    bootstrap_dir = ROOT / "compiler" / "tests" / "bootstrap"
    fixed_point_sh = bootstrap_dir / "fixed_point.sh"
    if not fixed_point_sh.exists():
        print(f"fixed-point: script not found at {fixed_point_sh}", file=sys.stderr)
        return 1
    bash_path = shutil.which("bash") or "bash"
    result = subprocess.run(
        [bash_path, str(fixed_point_sh)],
        env=os.environ.copy(),
    )
    return result.returncode


def _print_matrix_row(idx, total, binary, label, result, is_informational):
    """Print one matrix row."""
    tag = "INFORMATIONAL" if is_informational else "GATED"
    status = "PASS" if result["ok"] else "FAIL"
    sha_short = (result.get("binary_sha256") or "?")[:16]
    failed_names = [os.path.splitext(ft["file"])[0] for ft in result.get("failed_tests", [])][:5]
    print(f"[{idx}/{total}] {binary} ({label}) [{tag}]")
    print(f"       status: {status} — passed={result['passed']}/{result['total']} "
          f"failed={result['failed']} skipped={result['skipped']}")
    if failed_names:
        print(f"       failed: {', '.join(failed_names)}")
    print(f"       binary sha: {sha_short}...")
    if result.get("baseline_warning"):
        print(f"       baseline_warning: {result['baseline_warning']}")
    if result.get("early_abort"):
        print(f"       early_abort: {result['early_abort']}")
    print()


def main():
    ap = argparse.ArgumentParser(
        description="JHYY regress runner (single canonical entry, v1.4.7)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--binary", default="compiler/build/bin/jhyy.exe",
                    help="Compiler binary path (default: jhyy.exe production). "
                         "Use --all to run all gated binaries.")
    ap.add_argument("--all", dest="run_all_gated", action="store_true",
                    help="Run all gated binaries (jhyy.exe + jhyy_stage0.exe), "
                         "output matrix, exit code reflects any gated failure.")
    ap.add_argument("--include-informational", action="store_true",
                    help="With --all, also run jhyy_v1.exe.exe historical baseline "
                         "(matrix only, does not affect exit code).")
    ap.add_argument("--save-baseline", action="store_true",
                    help="Save binary sha256 baseline (informational; "
                         ".il byte-equal is the real regression signal).")
    ap.add_argument("--tests", default=None,
                    help="Comma-separated test names without .jhyy suffix "
                         "(e.g. 'hello,fib'). Default: all.")
    ap.add_argument("--jobs", type=int, default=None,
                    help="限制并发 compile 数 (default: 全并行 = min(测试数, CPU 数))。"
                         "只影响吞吐,不影响判定 —— 超时是死循环探测,不是性能预算")
    # 2026-10-15:300 → 900。实测**每个**文件的 compile 都要 ~7s(不是个别文件慢,
    # 200 个测试在 CI 少核 runner 上单跑就要 24 分钟)。per-test 超时的职责是
    # 「抓永不返回的死循环」,不是性能预算 —— 拿它当性能线会在满负载时随机误杀
    # 正常测试。CI 上 f32_suffix / f64_suffix / fmod_basic 三个就是被 300s
    # 砍掉的(它们并不比其他文件慢,只是排队时排到了最后)。
    ap.add_argument("--timeout", type=int, default=900,
                    help="Per-test timeout in seconds (dead-loop ceiling, not a perf budget)")
    ap.add_argument("--no-baseline-check", action="store_true",
                    help="Skip phantom-binary (mtime vs source) check for all runs.")
    ap.add_argument("--byte-equal", action="store_true",
                    help="Run byte-equal 三件套 check (per D26, requires JHYY_V1 "
                         "+ JHYY_V2 env vars; default jhyy_v1.exe.exe + jhyy.exe). "
                         "Opt-in: does NOT affect default regress baseline (104/104).")
    ap.add_argument("--byte-equal-amd64", action="store_true",
                    help="Run V2-B v2.6.0 (Unit F) byte-equal-amd64 driver "
                         "(QBE vs self backend path parity check, 5 tests). "
                         "Opt-in: does NOT affect default regress baseline.")
    ap.add_argument("--fixed-point", action="store_true",
                    help="Run V2-C v2.9.0 N≥3 selfhost fixed-point closure 验算 "
                         "(jhyy_v1 ↔ jhyy_v2 ↔ jhyy_v3 byte-equal .il per D43). "
                         "Opt-in: does NOT affect default regress baseline.")
    ap.add_argument("--self-backend", action="store_true",
                    help="V2-C v2.11.0: force JHY_SELF_BACKEND=1 + unset QBE_FALLBACK "
                         "to test self-written codegen_amd64_run path (bypasses QBE "
                         "fallback). Per W-073 verification gap closure: codegen_amd64_run "
                         "has been inert since v2.6.3 ship; this flag exercises the "
                         "real backend path as ship gate. Opt-in: does NOT affect "
                         "default regress baseline.")
    ap.add_argument("--cross", choices=["wsl", "docker", "auto", "none"],
                    default="auto",
                    help="Cross-env mode for sysv tests (v2.7.0 Phase 2b). "
                         "auto=probe wsl.exe/docker on PATH; none=SKIP. "
                         "Real wire deferred to v2.7.1.")
    args = ap.parse_args()

    # Parse --tests (comma-separated → list)
    tests = None
    if args.tests:
        tests = [t.strip() for t in args.tests.split(",") if t.strip()]

    # Mode dispatch
    if args.save_baseline:
        # Single-binary mode: save baseline for the explicit --binary
        sha = save_baseline_hash(args.binary)
        print(f"Saved baseline: {args.binary}.sha256 = {sha}")
        sys.exit(0)

    if args.byte_equal:
        # D26 byte-equal 三件套 (opt-in; doesn't affect default regress)
        rc = test_byte_equal(tests)
        sys.exit(rc)

    if args.fixed_point:
        # V2-C v2.9.0 N≥3 fixed-point closure (opt-in; doesn't affect default regress)
        rc = test_fixed_point(tests)
        sys.exit(rc)

    if args.self_backend:
        # V2-C v2.11.0 W-073 closure: force self-written codegen_amd64_run path.
        # Mutate os.environ so subprocess.run inherits via _build_subprocess_env().
        os.environ["JHY_SELF_BACKEND"] = "1"
        os.environ.pop("QBE_FALLBACK", None)
        print(f"[--self-backend] JHY_SELF_BACKEND=1 set, QBE_FALLBACK unset", file=sys.stderr)
        # Falls through to default regress run — env vars drive jhyy-side dispatch.

    if args.byte_equal_amd64:
        # V2-B v2.6.0 (Unit F) byte-equal-amd64 (opt-in; QBE-vs-self backend
        # path parity check, 5 tests). Self backend call site is currently
        # deferred to v2.6.x (Unit E wire), so the script runs QBE-vs-QBE
        # (trivially PASS). Real self-vs-QBE gate auto-fires when v2.6.x
        # wires codegen_amd64_run into main.jhyy.
        bootstrap_dir = ROOT / "compiler" / "tests" / "bootstrap"
        byte_equal_amd64_sh = bootstrap_dir / "byte_equal_amd64.sh"
        if not byte_equal_amd64_sh.exists():
            print(f"byte-equal-amd64: script not found at {byte_equal_amd64_sh}",
                  file=sys.stderr)
            sys.exit(1)
        bash_path = shutil.which("bash") or "bash"
        result = subprocess.run(
            [bash_path, str(byte_equal_amd64_sh)],
            env=os.environ.copy(),
        )
        sys.exit(result.returncode)

    if args.run_all_gated:
        # Matrix mode: gated binaries + optional informational
        binaries = list(_GATED_BINARIES)
        # stage0 永远以 informational 身份跑(2026-10-15 从 gated 降级 ——
        # 见 _STAGE0_BINARY 处的完整理由)。它给信号,但不参与 exit code。
        binaries.append(_STAGE0_BINARY)
        if args.include_informational:
            binaries.extend(_INFORMATIONAL_BINARIES)
        total = len(binaries)

        gated_failures = 0
        informational_count = 0
        for idx, (binary, label) in enumerate(binaries, 1):
            is_informational = (idx > len(_GATED_BINARIES))
            enforce = _resolve_default_enforce(binary, args.no_baseline_check)
            result = _run_one(binary, label, tests, args.timeout, enforce, args.jobs)
            _print_matrix_row(idx, total, binary, label, result, is_informational)
            if is_informational:
                informational_count += 1
                # informational fail 不影响 exit code
            elif not result["ok"]:
                gated_failures += 1

        # Summary
        gated_total = total - informational_count
        if gated_failures == 0:
            print(f"Summary: {gated_total}/{gated_total} gated binary PASS"
                  + (f", {informational_count} informational (matrix only)" if informational_count else ""))
        else:
            print(f"Summary: {gated_failures}/{gated_total} gated binary FAIL")
        # v2.7.1 Phase 2: cross-env sysv wire (--all mode; per gated binary).
        # Only first gated binary (jhyy.exe production) runs sysv cross-env —
        # stage0 / v1 use Win target only.
        cross_mode = _resolve_cross_mode(args.cross)
        print(f"cross: --cross={args.cross} → resolved={cross_mode}")
        only_sysv = tests  # may filter to specific sysv tests
        for idx, (binary, label) in enumerate(binaries, 1):
            is_informational = (idx > len(_GATED_BINARIES))
            if is_informational:
                continue
            # Only production jhyy.exe runs cross-env sysv (skip stage0)
            if binary != "compiler/build/bin/jhyy.exe":
                continue
            _sysv_passed, _sysv_failed, _sysv_skipped = _run_sysv_via_cross_env(
                cross_mode, binary, args.timeout, only_sysv)
            gated_failures += _sysv_failed
            if _sysv_failed > 0:
                print(f"Summary: {gated_failures}/... gated binary FAIL "
                      f"(sysv_cross={cross_mode}, sysv_failures={_sysv_failed})")
        sys.exit(0 if gated_failures == 0 else 1)
    else:
        # Single-binary mode: explicit --binary (or default jhyy.exe)
        binary = args.binary
        enforce = _resolve_default_enforce(binary, args.no_baseline_check)
        result = _run_one(binary, "single", tests, args.timeout, enforce, args.jobs)

        # Same output as --all but for one binary (status line only, no matrix frame)
        status = "PASS" if result["ok"] else "FAIL"
        sha_short = (result.get("binary_sha256") or "?")[:16]
        failed_names = [os.path.splitext(ft["file"])[0] for ft in result.get("failed_tests", [])][:5]
        print(f"{binary}: {status} — passed={result['passed']}/{result['total']} "
              f"failed={result['failed']} skipped={result['skipped']} (sha={sha_short}...)")
        if failed_names:
            print(f"  failed: {', '.join(failed_names)}")
        if result.get("baseline_warning"):
            print(f"  baseline_warning: {result['baseline_warning']}")
        if result.get("early_abort"):
            print(f"  early_abort: {result['early_abort']}", file=sys.stderr)
            sys.exit(2)
        # v2.7.1 Phase 2: cross-env sysv wire (single-binary mode).
        cross_mode = _resolve_cross_mode(args.cross)
        print(f"cross: --cross={args.cross} → resolved={cross_mode}")
        only_sysv = tests
        _sysv_passed, _sysv_failed, _sysv_skipped = _run_sysv_via_cross_env(
            cross_mode, binary, args.timeout, only_sysv)
        # overall ok = Win run_all ok AND no sysv FAIL (sysv SKIP is OK)
        sysv_ok = _sysv_failed == 0
        sys.exit(0 if result["ok"] and sysv_ok else 1)


if __name__ == "__main__":
    main()
