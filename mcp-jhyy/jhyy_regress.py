#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jhyy_regress.py — 共享 regress 逻辑 (mcp-jhyy tool + regress.py / regress_v1.py shim 共用)

Sprint mcp-1 (2026-08-11): 抽 NTSTATUS_NAMES + run_test + run_all 出来, 消除 regress.py / regress_v1.py 95% 重复.

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
from typing import Optional, List, Tuple

# 路径配置
JHYY_ROOT = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou")
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
    """构造 subprocess env. 修复 MCP server env={} 引起的 'gcc link failed'.

    Mirror jhyy_runner.py:_build_subprocess_env (modules 独立, 不互相 import).
    Rationale + empirical 见 jhyy_runner.py.

    ⚠️ 必须 FORCE 写 Windows-style PATH — 不能只补缺. 当 MCP server 自身在 MSYS bash 下
    启动, os.environ['PATH'] 是 `/c/...` 格式, jhyy.exe 内部 `system("cmd /c gcc ...")` 拿这个
    PATH 给 cmd.exe 用, cmd.exe 不认 `/c/...` 路径 → gcc 找 cc1/as/ld 失败 → "gcc link failed".
    """
    env = os.environ.copy()
    if not env.get("TMP"):
        env["TMP"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("TEMP"):
        env["TEMP"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("TMPDIR"):
        env["TMPDIR"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    # ALWAYS force Windows-style PATH (即使 os.environ 已有, 也要 sanitize 掉 MSYS `/c/...` 格式)
    win_path = r"C:\Windows\System32;C:\Windows;C:\msys64\ucrt64\bin;C:\msys64\usr\bin"
    if env.get("PATH") and not env["PATH"].startswith("/") and not env["PATH"].startswith("/c"):
        # 已 Windows-style, 补 ucrt64 进 head (gcc/cc1 在这里)
        if r"C:\msys64\ucrt64\bin" not in env["PATH"]:
            env["PATH"] = r"C:\msys64\ucrt64\bin;" + env["PATH"]
    else:
        # 空 / MSYS-style / 其他, 用 Windows fallback
        env["PATH"] = win_path
    if not env.get("SystemRoot"):
        env["SystemRoot"] = r"C:\Windows"
    if not env.get("SystemDrive"):
        env["SystemDrive"] = "C:"
    return env


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def save_baseline_hash(binary: str) -> str:
    """算 binary sha256 并写到 <binary>.sha256 文件. 返回 sha256."""
    bin_path = _resolve_binary(binary)
    sha = _sha256_file(bin_path)
    sha_path = bin_path + ".sha256"
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write(sha + "\n")
    return sha


def _check_baseline_hash(binary: str, sha_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """对比 binary 当前 sha256 跟 sha_path. 返回 (match, current_sha, baseline_sha_or_None)."""
    current = _sha256_file(binary)
    if not os.path.exists(sha_path):
        return (True, current, None)  # missing baseline = skip (warning, not fail)
    with open(sha_path, encoding="utf-8") as f:
        baseline = f.read().strip()
    return (current == baseline, current, baseline)


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
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=20,
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
    return (actual == expected, expected, actual, output)


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

    # Baseline hash check
    sha_path = bin_path + ".sha256"
    if enforce_baseline_hash:
        match, current_sha, baseline_sha = _check_baseline_hash(bin_path, sha_path)
        if not match and baseline_sha is not None:
            return {
                "ok": False,
                "binary": binary,
                "binary_sha256": current_sha,
                "baseline_match": False,
                "baseline_sha256": baseline_sha,
                "total": 0, "passed": 0, "failed": 0, "skipped": 0,
                "failed_tests": [],
                "duration_sec": time.time() - start,
                "baseline_warning": None,
                "early_abort": (
                    f"binary drifted since baseline lock: current={current_sha[:16]}... "
                    f"baseline={baseline_sha[:16]}... Run `python -m jhyy_regress --save-baseline` "
                    f"to update, or pass enforce_baseline_hash=False to bypass."
                ),
            }
        baseline_match = match
        baseline_warning = None if baseline_sha else (
            f"baseline file missing at {sha_path} — skipping hash check "
            f"(run `python -m jhyy_regress --save-baseline` to lock)"
        )
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
    for fname in files:
        path = str(TEST_DIR / fname)
        ok, exp, act, msg = run_test(path, binary, timeout=timeout)
        if ok and msg == "skipped (library)":
            print(f"SKIP  {fname:<30}  (library, no main)")
            skipped += 1
        elif ok:
            print(f"PASS  {fname:<30}  EXIT={act}")
            passed += 1
        else:
            print(f"FAIL  {fname:<30}  expected={exp} got={act}  {msg[:80]}")
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
                    help="Save current binary sha256 as baseline")
    ap.add_argument("--no-baseline-check", action="store_true",
                    help="Skip baseline hash enforcement")
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
    sys.exit(0 if result["ok"] else 1)