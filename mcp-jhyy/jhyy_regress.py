#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jhyy_regress.py — 共享 regress 逻辑 (mcp-jhyy tool + regress.py shim 共用)

Sprint mcp-1 (2026-08-11): 抽 NTSTATUS_NAMES + run_test + run_all 出来, 消除 regress.py 重复.
Sprint v1.4.7 (2026-08-14): regress.py 合并成单入口 (--all / --include-informational),
                             regress_v1.py / regress_stage0.py 删除, 此模块只剩 MCP tool + regress.py shim 共用.

Public API:
    ntstatus_name(code)            -> str | None
    run_test(jhyy_file, binary, ...) -> (passed, expected, actual, message)
    run_all(binary, tests=None, timeout=20, enforce_baseline_hash=True) -> dict
    save_baseline_hash(binary)     -> str (sha256)
"""
import subprocess
import sys
import os
import re
import hashlib
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Tuple

# 路径配置 — derive from script location (works on any machine, no
# hardcoded user path; per v1.5.5 release.yml CI fix).
# mcp-jhyy/jhyy_regress.py → parents[1] = project root
JHYY_ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = JHYY_ROOT / "compiler/tests/examples"


# Sprint mcp-2: NTSTATUS table 抽到 jhyy_ntstatus.py 共享给 jhyy_runner.compile_and_run.
# Re-export here 保 back-compat (test_regress.py / regress.py shim 都 import 此模块).
from jhyy_ntstatus import NTSTATUS_NAMES, ntstatus_name  # noqa: E402,F401


def _resolve_binary(binary: str) -> str:
    """解析 binary 路径 (相对 JHYY_ROOT 或绝对)."""
    if os.path.isabs(binary):
        return binary
    return str(JHYY_ROOT / binary)


def _build_subprocess_env() -> dict:
    """构造 subprocess env. 修复 'gcc link failed' ('gcc is not recognized').

    Mirror jhyy_runner.py:_build_subprocess_env (modules 独立, 不互相 import).

    W-026 (2026-08-15): CI GH Actions release.yml regress 53/53 FAIL, real
    error 'gcc is not recognized as an internal or external command'.

    W-027 v4 (2026-08-15 same-day): setup-msys2@v2 把 MSYS2 装到
    `$RUNNER_TEMP\\msys64` (CI = `D:\\a\\_temp\\msys64`), 不在
    `C:\\msys64`。

    Root cause chain (3 failures found):
    v1 hardcode `C:\\msys64\\ucrt64\\bin`: wrong on CI
    v2 shutil.which: returns MSYS2 virtual path (`/ucrt64/bin/gcc`),
      only valid inside MSYS2; converting `/`→`\\` gives `\\ucrt64\\bin`,
      not a valid Win32 path
    v3 `cmd /c where` via Python subprocess: from MSYS2-launched Python,
      subprocess returns interactive shell prompt (not gcc path) — unreliable
    v3.5 `bash -c "cmd //c where gcc"` via Python subprocess: subprocess
      encoding/decoding breaks on bash UTF-16 LE output, returns None,
      and `cmd //c 'where gcc'` from subprocess.run gets eaten by MSYS2
      quoting — only works from real bash, not from Python subprocess

    Fix v4: compute MSYS2 root deterministically.
    - GitHub Actions `setup-msys2@v2` puts MSYS2 at `$RUNNER_TEMP\\msys64`
      where `$RUNNER_TEMP` = `D:\\a\\_temp` on `windows-latest` runner.
    - Local dev: `C:\\msys64` (or wherever user installed).
    Read `os.environ['RUNNER_TEMP']` if set, fall back to `C:\\msys64`.
    Then check known bin subdirs: ucrt64/bin, mingw64/bin, usr/bin, bin.
    Each existing dir is added to found_dirs (in Win32 form).
    """
    env = os.environ.copy()
    if not env.get("TMP"):
        env["TMP"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("TEMP"):
        env["TEMP"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("TMPDIR"):
        env["TMPDIR"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("SystemRoot"):
        env["SystemRoot"] = r"C:\Windows"
    if not env.get("SystemDrive"):
        env["SystemDrive"] = "C:"
    # W-027 v4: deterministic MSYS2 root + known bin subdirs.
    found_dirs = []
    import shutil
    # Source (a): shutil.which — only accept Win32 paths
    for tool in ("gcc", "qbe", "python", "make"):
        loc = shutil.which(tool, path=env.get("PATH", ""))
        if loc and len(loc) >= 3 and loc[1] == ":" and "\\" in loc:
            d_win = os.path.dirname(loc)
            if d_win not in found_dirs:
                found_dirs.append(d_win)
    # Source (b): known MSYS2 install roots (deterministic)
    runner_temp = env.get("RUNNER_TEMP", "")
    msys2_roots = []
    if runner_temp:
        # CI: $RUNNER_TEMP\msys64 — convert /c/foo to C:\foo or D:\a\_temp to D:\a\_temp
        rt_win = runner_temp.replace("/", "\\")
        if not rt_win.endswith("\\"):
            rt_win += "\\"
        msys2_roots.append(rt_win + "msys64")
    msys2_roots.append(r"C:\msys64")  # local dev default
    for root in msys2_roots:
        # Known MSYS2 bin subdirs that contain gcc / qbe / make
        for sub in ("ucrt64\\bin", "mingw64\\bin", "usr\\bin", "bin"):
            candidate = root + "\\" + sub
            if os.path.isdir(candidate) and candidate not in found_dirs:
                found_dirs.append(candidate)
    # Prepend discovered Win32 dirs + System32. Append original PATH.
    win_dirs = ";".join(found_dirs) + ";" + r"C:\Windows\System32;C:\Windows"
    original = env.get("PATH", "")
    env["PATH"] = win_dirs + (";" + original if original else "")
    return env


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


def _check_baseline_freshness(binary: str, src_dir: str = "compiler/src") -> Tuple[bool, str]:
    """检查 binary 是否在 src 之后被构建过. 防止 phantom binary (忘记
    重编就跑 regress).

    Returns:
        (is_fresh, message)
        is_fresh=True 当: 源文件全部比 binary 旧 (binary mtime >= max(src mtime))
                       OR baseline 文件不存在 (warning, 不 fail)
        is_fresh=False 当: 源里有文件比 binary 新, 怀疑 binary 是旧 build

    Rationale: .il byte-equal 是真回归信号, .exe sha 防不了非确定性 drift
    也没必要防. binary mtime 跟 src mtime 的相对关系才决定 binary 是不是
    "新构建的" — 这才是 phantom binary 场景的真信号.
    """
    bin_mtime = os.path.getmtime(binary)
    src_root = JHYY_ROOT / src_dir
    if not src_root.exists():
        return (True, f"src dir missing ({src_root}), skipping freshness check")
    newest_src = max(
        (os.path.getmtime(p) for p in Path(src_root).rglob("*") if p.is_file()),
        default=0.0,
    )
    if bin_mtime + 0.5 >= newest_src:  # 0.5s 容忍文件系统 mtime 精度
        return (True, f"binary mtime {bin_mtime:.0f} >= newest src mtime {newest_src:.0f}")
    return (False, (
        f"binary is older than source: binary mtime={bin_mtime:.0f}, "
        f"newest src mtime={newest_src:.0f} — suspect phantom binary. "
        f"Rebuild before running regress."
    ))


def run_test(
    jhyy_file: str,
    binary: str,
    timeout: int = 10,
    extra_inputs: Optional[List[str]] = None,
) -> Tuple[bool, Optional[int], int, str]:
    """Compile + run 单个 .jhyy 文件, 返回 (passed, expected, actual, message)."""
    name = os.path.splitext(os.path.basename(jhyy_file))[0]
    out_base = str(JHYY_ROOT / "compiler/build/bin" / f"_regress_{name}")

    # Sprint 4.4 C: stale .exe hardening — 避免 stale cache 掩盖 cleanup crash
    for ext in (".il", ".s", ".exe"):
        p = out_base + ext
        if os.path.exists(p):
            os.remove(p)

    # Read expected exit from comment if present
    expected = None
    has_main = False
    try:
        with open(jhyy_file, encoding="utf-8") as f:
            src = f.read()
        m = re.search(r"//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)", src)
        if m:
            expected = int(m.group(1))
        # Skip library files (no main entry)
        has_main = bool(re.search(r"\bfn\s+main_jhyy\b", src))
    except UnicodeDecodeError:
        pass

    if not has_main:
        # Library file: skip (no standalone run possible)
        return (True, None, None, "skipped (library)")

    # Compile
    cmd = [_resolve_binary(binary), "compile", jhyy_file, "-o", out_base]
    if extra_inputs:
        for inp in extra_inputs:
            cmd.insert(2, _resolve_binary(inp))
    # 60s (not 20s): 并行跑时单个 compile 会因 CPU 争抢拉长
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                       encoding="utf-8", errors="replace", env=_build_subprocess_env())
    if r.returncode != 0:
        return (False, expected, -1, f"compile failed: {r.stderr[:200]}")
    exe = os.path.abspath(out_base + ".exe")
    if not os.path.exists(exe):
        return (False, expected, -2, "exe not created")

    # Run
    try:
        r2 = subprocess.run([exe], capture_output=True, text=True, timeout=timeout,
                            stdin=subprocess.DEVNULL,  # ⚠️ MCP server 无有效 stdin → 子进程阻塞
                            encoding="utf-8", errors="replace", env=_build_subprocess_env())
        actual = r2.returncode
        output = (r2.stdout or "") + (r2.stderr or "")
    except subprocess.TimeoutExpired:
        return (False, expected, -3, f"timeout ({timeout}s)")

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


def run_all(
    binary: str,
    tests: Optional[List[str]] = None,
    timeout: int = 10,
    enforce_baseline_hash: bool = True,
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
        files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".jhyy") and not f.startswith("_"))
    else:
        files = tests

    passed, failed, skipped = 0, 0, 0
    failed_tests = []

    workers = min(len(files), os.cpu_count() or 4)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(run_test, str(TEST_DIR / f), binary, timeout): f for f in files}
        results = {futures[fut]: fut.result() for fut in as_completed(futures)}

    for fname in files:
        ok, exp, act, msg = results[fname]
        if ok and msg == "skipped (library)":
            print(f"SKIP  {fname:<30}  (library, no main)")
            skipped += 1
        elif ok:
            print(f"PASS  {fname:<30}  EXIT={act}")
            passed += 1
        else:
            # Sprint v1.5.5: print full stderr so CI logs include QBE/gcc link
            # errors (always after "[4] codegen done", past 80 chars).
            print(f"FAIL  {fname:<30}  expected={exp} got={act}  {msg}")
            failed += 1
            failed_tests.append({
                "file": fname,
                "expected": exp,
                "actual": act,
                "message": msg,
            })

    duration = time.time() - start
    print(f"\n===== {passed}/{passed + failed} passed, {failed} failed, {skipped} skipped "
          f"(of {len(files)} total) =====")

    # Sprint mcp-2: cleanup _regress_* artifacts for tests that didn't fail.
    # Pass → clean dir after run; Fail → keep .il/.s/.exe for inspection
    # (per feedback_il_s_debugging_pattern: .il 比 gdb 无符号更有效).
    failed_names = {os.path.splitext(ft["file"])[0] for ft in failed_tests}
    cleaned = 0
    for fname in files:
        name = os.path.splitext(fname)[0]
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
    ap.add_argument("--timeout", type=int, default=10)
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