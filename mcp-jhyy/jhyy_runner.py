#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jhyy_runner.py — subprocess 封装 + 诊断解析 + IL diff + selfhost check

Sprint mcp-1 (2026-08-11): 抽 subprocess 共享逻辑 + 2 个核心 helper (il_diff / selfhost_check).

Public API:
    run_subprocess(args, timeout=600) -> dict
    parse_diagnostics(text)           -> list[str]
    il_diff(file_a, file_b, context=3) -> dict
    selfhost_check(src, auto_rebuild=False, timeout=600) -> dict
"""
import subprocess
import os
import re
import json
import hashlib
import difflib
import time
from pathlib import Path
from typing import Optional

# 路径配置
JHYY_ROOT = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou")
JHYY_EXE = JHYY_ROOT / "compiler/build/bin/jhyy.exe"
RUNTIME_C = JHYY_ROOT / "compiler/runtime/runtime.c"


def _resolve_path(p: str) -> str:
    """把相对路径解析为绝对路径 (相对于 JHYY 项目根)"""
    if os.path.isabs(p):
        return p
    return str(JHYY_ROOT / p)


def _build_subprocess_env() -> dict:
    """构造 subprocess env. 修复 MCP server env={} 引起的 'gcc link failed'.

    Root cause (2026-08-12): ~/.claude.json 把 jhyy MCP server 启动为 env={},
    Python 进程 inherit empty env → os.environ 空 → subprocess.run inherit empty →
    jhyy.exe system("C:/msys64/ucrt64/bin/gcc.exe ...") 的 gcc 也 empty env →
    collect2 找不到 tmp dir → silent exit 1 → "gcc link failed".

    Empirical (env -i simulation, 2026-08-12): gcc 需要 TMP/TEMP (collect2 tmp file)
    + PATH 含 /c/msys64/ucrt64/bin (ld.exe). 缺任一 → EXIT=1 silent.

    ⚠️ 2026-08-12 加: 当 MCP server 在 MSYS bash 下 spawn, os.environ['PATH'] 可能是
    `/c/...` 格式. 即使 PATH 不为空, 这种格式传给 jhyy.exe 内部的 cmd.exe 仍然坏:
    cmd.exe 不认 `/c/...` 虚拟路径, gcc subprocess (cc1/as/ld) 找不到 → "gcc link failed".
    所以 PATH 处理必须 FORCE Windows-style, 不是只补缺.

    Fix: 拷贝 os.environ (already-populated 时不动) + 补 critical 缺失 vars
    + sanitize PATH 为 Windows-style.
    Direct python regress.py 调用时 os.environ 已 Windows-style, sanitize no-op —
    不破坏现有 env.
    """
    env = os.environ.copy()
    if not env.get("TMP"):
        env["TMP"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("TEMP"):
        env["TEMP"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    if not env.get("TMPDIR"):
        env["TMPDIR"] = r"C:\Users\liuzhen\AppData\Local\Temp"
    # ALWAYS force Windows-style PATH
    win_path = r"C:\Windows\System32;C:\Windows;C:\msys64\ucrt64\bin;C:\msys64\usr\bin"
    if env.get("PATH") and not env["PATH"].startswith("/"):
        # 已 Windows-style, 补 ucrt64 进 head (gcc/cc1 在这里)
        if r"C:\msys64\ucrt64\bin" not in env["PATH"]:
            env["PATH"] = r"C:\msys64\ucrt64\bin;" + env["PATH"]
    else:
        # 空 / MSYS-style (`/c/...`), 用 Windows fallback
        env["PATH"] = win_path
    if not env.get("SystemRoot"):
        env["SystemRoot"] = r"C:\Windows"
    if not env.get("SystemDrive"):
        env["SystemDrive"] = "C:"
    return env


def _run_cmd(cmd: list, timeout: int = 30, cwd: Optional[str] = None) -> dict:
    """运行命令并返回结果。统一处理 Windows 编码问题。"""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            cwd=cwd or str(JHYY_ROOT),
            env=_build_subprocess_env(),
        )
        return {
            "ok": r.returncode == 0,
            "exit_code": r.returncode,
            "stdout": r.stdout or "",
            "stderr": r.stderr or "",
            "command": " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Timeout ({timeout}s) executing: {' '.join(cmd)}",
            "command": " ".join(cmd),
        }
    except FileNotFoundError as e:
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command not found: {e}",
            "command": " ".join(cmd),
        }


def _safe_remove(path: str, retries: int = 3, delay_ms: int = 500) -> bool:
    """Remove a file, retrying on Windows PermissionError (file lock).

    On Windows, even after subprocess exits, the OS file handle can stay open
    for a few hundred ms. ld.exe open-write to the same path will then fail
    with PermissionError. We sleep + retry up to N times.

    Returns True if removed, False if still locked (caller can decide to
    continue or abort).
    """
    if not os.path.exists(path):
        return True
    for attempt in range(retries):
        try:
            os.remove(path)
            return True
        except PermissionError:
            time.sleep(delay_ms / 1000.0)
        except OSError:
            # File in use or other transient error
            time.sleep(delay_ms / 1000.0)
    return False


def compile_file(file: str, output: Optional[str] = None, extra_inputs: list = None) -> dict: # type: ignore
    """编译 .jhyy 文件为可执行程序。"""
    src = _resolve_path(file)
    if not os.path.exists(src):
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Source file not found: {src}",
        }
    if output is None:
        output = os.path.splitext(os.path.basename(src))[0] + "_mcp_run"
    output = _resolve_path(output)
    # Make output relative to cwd (jhyy.exe writes output relative to its own cwd)
    # We pass absolute path so it works regardless of cwd.
    cmd = [str(JHYY_EXE), "compile", src, "-o", output]
    if extra_inputs:
        for inp in extra_inputs:
            cmd.insert(2, _resolve_path(inp))
    return _run_cmd(cmd, timeout=60)


def run_exe(exe: str, args: list = None, timeout: int = 10) -> dict: # type: ignore
    """运行已编译的 .exe。"""
    exe = _resolve_path(exe)
    # If user passed a path without .exe, try appending it
    if not os.path.exists(exe) and os.path.exists(exe + ".exe"):
        exe = exe + ".exe"
    if not os.path.exists(exe):
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Executable not found: {exe}",
        }
    cmd = [exe]
    if args:
        cmd.extend(args)
    return _run_cmd(cmd, timeout=timeout)


def compile_and_run(file: str, extra_inputs: list = None, timeout: int = 10) -> dict: # type: ignore
    """编译并运行 .jhyy 文件，返回运行结果。"""
    src = _resolve_path(file)
    if not os.path.exists(src):
        return {
            "ok": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Source file not found: {src}",
        }
    output_base = os.path.splitext(os.path.basename(src))[0] + "_mcp_run"
    output = str(JHYY_ROOT / "compiler/build/bin" / output_base)
    cresult = compile_file(file, output, extra_inputs)
    if not cresult["ok"]:
        return {
            "ok": False,
            "stage": "compile",
            "exit_code": cresult["exit_code"],
            "stdout": cresult["stdout"],
            "stderr": cresult["stderr"],
        }
    rresult = run_exe(output, timeout=timeout)
    # Sprint mcp-2 (D): NTSTATUS gate. fib30.jhyy exit 832040 is a normal program
    # exit, NOT a Windows crash (NTSTATUS codes live in 0xC0000000-0xCFFFFFFF).
    # Previously `ok = rresult["ok"]` made any non-zero exit look like a failure.
    # Now: crash iff exit_code is a known NTSTATUS. See jhyy_ntstatus.py.
    from jhyy_ntstatus import ntstatus_name
    ntstatus = ntstatus_name(rresult["exit_code"])
    ok = rresult["ok"] or ntstatus is None
    return {
        "ok": ok,
        "stage": "run",
        "exit_code": rresult["exit_code"],
        "ntstatus": ntstatus,  # None for normal exit, "ACCESS_VIOLATION" for crash
        "stdout": rresult["stdout"],
        "stderr": rresult["stderr"],
        "compile_stderr": cresult["stderr"],
    }


def check_syntax(file: str) -> dict:
    """只做语法/语义检查，不生成可执行文件。"""
    src = _resolve_path(file)
    if not os.path.exists(src):
        return {
            "ok": False,
            "exit_code": -1,
            "errors": [f"Source file not found: {src}"],
        }
    # 用 compile 命令跑一次，看 stderr 是否有错
    tmp_basename = "_mcp_check_" + os.path.basename(src).replace(".jhyy", "")
    tmp_output = str(JHYY_ROOT / "compiler/build/bin" / tmp_basename)
    cmd = [str(JHYY_EXE), "compile", src, "-o", tmp_output]
    r = _run_cmd(cmd, timeout=30)
    if r["ok"]:
        return {
            "ok": True,
            "exit_code": 0,
            "errors": [],
            "warnings": _extract_warnings(r["stderr"]),
        }
    errors = _parse_diagnostics(r["stderr"])
    return {
        "ok": False,
        "exit_code": r["exit_code"],
        "errors": errors,
        "stderr": r["stderr"],
    }


def _extract_warnings(stderr: str) -> list:
    """从编译器 stderr 提取 warning。"""
    warnings = []
    for line in stderr.splitlines():
        if "warning" in line.lower():
            warnings.append(line.strip())
    return warnings


def _parse_diagnostics(stderr: str) -> list:
    """解析编译器错误信息，提取 file:line:col + 消息。"""
    diagnostics = []
    for line in stderr.splitlines():
        m = re.match(r"^([^:]+):(\d+):(\d+):\s*(.+)$", line)
        if m:
            diagnostics.append({
                "file": m.group(1),
                "line": int(m.group(2)),
                "col": int(m.group(3)),
                "message": m.group(4).strip(),
            })
        elif line.strip():
            diagnostics.append({"file": "", "line": 0, "col": 0, "message": line.strip()})
    return diagnostics


def get_il(file: str) -> dict:
    """编译 .jhyy 文件并返回生成的 QBE IL。"""
    src = _resolve_path(file)
    if not os.path.exists(src):
        return {
            "ok": False,
            "exit_code": -1,
            "stderr": f"Source file not found: {src}",
        }
    output_base = os.path.splitext(os.path.basename(src))[0] + "_mcp_il"
    output = str(JHYY_ROOT / "compiler/build/bin" / output_base)
    cresult = compile_file(file, output)
    if not cresult["ok"]:
        return {
            "ok": False,
            "exit_code": cresult["exit_code"],
            "stderr": cresult["stderr"],
        }
    il_file = output + ".il"
    if not os.path.exists(il_file):
        return {"ok": False, "exit_code": -1, "stderr": f"IL file not found: {il_file}"}
    with open(il_file, encoding="utf-8") as f:
        il_text = f.read()
    return {
        "ok": True,
        "exit_code": 0,
        "il": il_text,
        "il_file": il_file,
    }


# ========== Sprint mcp-1: IL diff + Selfhost check ==========

def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def il_diff(file_a: str, file_b: str, context: int = 3) -> dict:
    """Diff two .il files for byte-equality and structural changes.

    Args:
        file_a, file_b: 绝对路径或相对 JHYY_ROOT 路径
        context: 首差异行的 context 行数 (default 3)

    Returns:
        {
            "ok": bool,
            "byte_equal": bool,
            "sha256_a": str, "sha256_b": str,
            "size_bytes_a": int, "size_bytes_b": int,
            "line_count_a": int, "line_count_b": int,
            "first_diff_line": int | None,    # 1-based, None if byte_equal
            "first_diff_context": str | None, # ±context 行 unified diff
        }
    """
    pa = _resolve_binary(file_a) if hasattr(_resolve_path, '__call__') else file_a
    pa = _resolve_path(file_a)
    pb = _resolve_path(file_b)
    if not os.path.exists(pa):
        return {"ok": False, "error": f"file_a not found: {pa}"}
    if not os.path.exists(pb):
        return {"ok": False, "error": f"file_b not found: {pb}"}

    sha_a = _sha256_file(pa)
    sha_b = _sha256_file(pb)
    size_a = os.path.getsize(pa)
    size_b = os.path.getsize(pb)

    with open(pa, encoding="utf-8", errors="replace") as f:
        lines_a = f.readlines()
    with open(pb, encoding="utf-8", errors="replace") as f:
        lines_b = f.readlines()

    line_count_a = len(lines_a)
    line_count_b = len(lines_b)

    if sha_a == sha_b:
        return {
            "ok": True,
            "byte_equal": True,
            "sha256_a": sha_a,
            "sha256_b": sha_b,
            "size_bytes_a": size_a,
            "size_bytes_b": size_b,
            "line_count_a": line_count_a,
            "line_count_b": line_count_b,
            "first_diff_line": None,
            "first_diff_context": None,
        }

    # Find first differing line
    first_diff = None
    for i, (la, lb) in enumerate(zip(lines_a, lines_b)):
        if la != lb:
            first_diff = i + 1  # 1-based
            break
    if first_diff is None:
        # One file is a prefix of the other
        first_diff = min(line_count_a, line_count_b) + 1

    # Generate ±context unified diff around first diff
    start = max(0, first_diff - 1 - context)
    end_a = min(line_count_a, first_diff - 1 + context + 1)
    end_b = min(line_count_b, first_diff - 1 + context + 1)
    a_slice = lines_a[start:end_a]
    b_slice = lines_b[start:end_b]
    diff_text = "".join(difflib.unified_diff(
        a_slice, b_slice,
        fromfile=os.path.basename(pa),
        tofile=os.path.basename(pb),
        fromfiledate="", tofiledate="",
        n=context,
        lineterm="",
    ))

    return {
        "ok": True,
        "byte_equal": False,
        "sha256_a": sha_a,
        "sha256_b": sha_b,
        "size_bytes_a": size_a,
        "size_bytes_b": size_b,
        "line_count_a": line_count_a,
        "line_count_b": line_count_b,
        "first_diff_line": first_diff,
        "first_diff_context": diff_text[:800],  # cap
    }


def _resolve_binary(binary: str) -> str:
    """解析编译器 binary 路径 (同 _resolve_path, 但别名避免名字冲突)."""
    return _resolve_path(binary)


def _maybe_rebuild_v144() -> dict:
    """v1.4.4 改: auto_rebuild=True 时调 stage-0 链:
       gcc → jhyy_stage0.exe (C 端 bootstrap)
       jhyy_stage0.exe compile src0/main.jhyy → jhyy.exe (jhyy-side production)
       cp jhyy.exe → jhyy.exe.exe (新 baseline)
    """
    # Stage 0: gcc 编译 C 端 → jhyy_stage0.exe
    gcc_cmd = ["gcc", "-std=c11", "-Wall", "-Wextra",
               "compiler/src/*.c",
               "-o", "compiler/build/bin/jhyy_stage0.exe",
               "-I", "compiler/src"]
    gcc_result = _run_cmd(gcc_cmd, timeout=120)
    if not gcc_result["ok"]:
        return {"ok": False, "stage": "gcc_compile_stage0",
                "stderr_tail": gcc_result["stderr"][-200:]}
    # Stage 1: jhyy_stage0.exe 编 src0/main.jhyy → jhyy.exe (production)
    stage0_exe = JHYY_ROOT / "compiler/build/bin/jhyy_stage0.exe"
    compile_cmd = [str(stage0_exe), "compile", "compiler/src0/main.jhyy",
                   "-o", "compiler/build/bin/jhyy"]
    compile_result = _run_cmd(compile_cmd, timeout=120)
    if not compile_result["ok"]:
        return {"ok": False, "stage": "stage0_compile_main",
                "stderr_tail": compile_result["stderr"][-200:]}
    # cp jhyy.exe → jhyy.exe.exe (per memory feedback_regress_baseline_binary_hash)
    import shutil
    shutil.copy("compiler/build/bin/jhyy.exe", "compiler/build/bin/jhyy.exe.exe")
    # 同时刷新 jhyy_v1.exe.exe (历史 baseline, regress_v1.py 用)
    # jhyy_v1.exe.exe 在 v1.4.4 后 = jhyy.exe 自身 (因为 jhyy.exe 现在是 jhyy-side 产物)
    # 但保留独立 binary 维持 v1.0.0 historical baseline 可追溯
    shutil.copy("compiler/build/bin/jhyy.exe", "compiler/build/bin/jhyy_v1.exe.exe")
    return {"ok": True}


# v1.4.4: 保留旧函数名作 fallback (向后兼容 — 旧 caller 可能仍调)
def _maybe_rebuild_jhyy_v1() -> dict:
    """v1.4.4 deprecation: 旧函数名转发到 _maybe_rebuild_v144. 保留签名兼容."""
    return _maybe_rebuild_v144()


def selfhost_check(src: str = "compiler/src0/main.jhyy", auto_rebuild: bool = False,
                   timeout: int = 600) -> dict:
    """一键 v1→v2→v3 byte-equal 验证.

    Args:
        src: 编译源文件 (default compiler/src0/main.jhyy)
        auto_rebuild: True 时自动 rebuild jhyy_v1 (per Plan agent risk analysis: 默认 False 防 phantom)
        timeout: 每阶段 timeout (秒, default 600)

    Returns:
        {
            "ok": bool,
            "all_byte_equal": bool,
            "il_sha256": str,             # 共同的 sha256 (byte-equal 时填)
            "binary_chain": [
                {"stage": "jhyy_v1", "path": "...", "sha256": "...", "duration_sec": 12.3},
                {"stage": "jhyy_v2", "path": "...", "sha256": "...", "duration_sec": 11.8},
                {"stage": "jhyy_v3", "path": "...", "sha256": "...", "duration_sec": 12.1},
            ],
            "il_files": {
                "jhyy_v1.il": "sha256...",
                "jhyy_v2.il": "sha256...",
                "jhyy_v3.il": "sha256...",
                "jhyy_v4.il": "sha256...",   # 4-hop 稳定验证
            },
            "early_abort": None | str,
            "duration_sec": float,
        }
    """
    start = time.time()

    # Optional rebuild
    if auto_rebuild:
        rebuild = _maybe_rebuild_jhyy_v1()
        if not rebuild["ok"]:
            return {
                "ok": False, "all_byte_equal": False,
                "il_sha256": None,
                "binary_chain": [],
                "il_files": {},
                "early_abort": f"auto_rebuild failed at {rebuild['stage']}: {rebuild['stderr_tail']}",
                "duration_sec": round(time.time() - start, 2),
            }

    # Check binaries exist
    # W-014 fix (2026-08-12): outputs use _sh_ scratch prefix so pre-stage cleanup
    # doesn't delete the canonical jhyy_v2.exe / jhyy_v3.exe input binaries.
    # Before fix: stages 2/3 had input == output (only .exe suffix differs), so
    # `_safe_remove(output_base + ".exe")` deleted the input → FileNotFoundError
    # → "Command not found (exit=-1)". Canonical closure binaries committed at
    # v1.0.0 tag were destroyed on every selfhost_check call. Now outputs go to
    # scratch files (_sh_vN.exe / _sh_vN.il), leaving canonical binaries intact.
    chain = [
        ("jhyy_v1", "compiler/build/bin/jhyy_v1.exe.exe", "compiler/build/bin/_sh_v1"),
        ("jhyy_v2", "compiler/build/bin/jhyy_v2.exe",     "compiler/build/bin/_sh_v2"),
        ("jhyy_v3", "compiler/build/bin/jhyy_v3.exe",     "compiler/build/bin/_sh_v3"),
        ("jhyy_v4", "compiler/build/bin/jhyy_v3.exe",     "compiler/build/bin/_sh_v4"),  # v4 = v3 编 src 再一次
    ]
    src_abs = _resolve_path(src)

    binary_chain_out = []
    il_files = {}

    # Stage 1: jhyy_v1 → v1.il
    for i, (stage, exe_rel, output_rel) in enumerate(chain):
        # Use absolute paths for subprocess (MSYS2 Python + Windows subprocess doesn't resolve rel paths)
        exe_path = _resolve_path(exe_rel)
        output_base = _resolve_path(output_rel)
        if not os.path.exists(exe_path):
            return {
                "ok": False, "all_byte_equal": False,
                "il_sha256": None,
                "binary_chain": binary_chain_out,
                "il_files": il_files,
                "early_abort": f"{stage} not found at {exe_path}. "
                               f"Run with auto_rebuild=True, or first build it manually.",
                "duration_sec": round(time.time() - start, 2),
            }
        # Sprint mcp-2 (A): pre-stage cleanup. Previous selfhost_check run may have
        # left a stale .exe with Windows file lock held briefly after subprocess exit.
        # ld.exe open-write then fails with PermissionError. Remove + retry on lock.
        _safe_remove(output_base + ".exe")
        _safe_remove(output_base + ".il")
        stage_start = time.time()
        # compile src → output_base (jhyy.exe adds .il suffix automatically per memory)
        cmd = [exe_path, "compile", src_abs, "-o", output_base]
        r = _run_cmd(cmd, timeout=timeout)
        stage_dur = round(time.time() - stage_start, 2)
        if not r["ok"]:
            return {
                "ok": False, "all_byte_equal": False,
                "il_sha256": None,
                "binary_chain": binary_chain_out,
                "il_files": il_files,
                "early_abort": f"{stage} compile failed (exit={r['exit_code']}): {r['stderr'][-200:]}",
                "duration_sec": round(time.time() - start, 2),
            }
        # Resolve IL file (per memory feedback_qbe_crlf_root_cause: Windows fopen "w" adds .il)
        # jhyy.exe writes to <output_base>.il (it appends .il). But user-provided output without .il
        # → jhyy.exe may produce <output_base>.il OR <output_base>.il.il.
        il_candidate = output_base + ".il"
        if not os.path.exists(il_candidate):
            il_candidate = output_base + ".il.il"
        if not os.path.exists(il_candidate):
            # Search build/bin for matching prefix
            build_bin = str(JHYY_ROOT / "compiler/build/bin")
            candidates = [f for f in os.listdir(build_bin)
                          if f.startswith(os.path.basename(output_base)) and f.endswith(".il")]
            if candidates:
                il_candidate = str(JHYY_ROOT / "compiler/build/bin" / candidates[0])
            else:
                return {
                    "ok": False, "all_byte_equal": False,
                    "il_sha256": None,
                    "binary_chain": binary_chain_out,
                    "il_files": il_files,
                    "early_abort": f"{stage} IL not found after compile (looked at {output_base}.il)",
                    "duration_sec": round(time.time() - start, 2),
                }
        il_sha = _sha256_file(il_candidate)
        il_files[f"{stage}.il"] = il_sha
        binary_chain_out.append({
            "stage": stage,
            "binary_path": exe_path,
            "binary_sha256": _sha256_file(exe_path),
            "il_path": il_candidate,
            "il_sha256": il_sha,
            "duration_sec": stage_dur,
        })

    # Check byte-equal: all 4 ILs same sha
    unique_shas = set(il_files.values())
    all_byte_equal = len(unique_shas) == 1
    common_sha = next(iter(unique_shas)) if all_byte_equal else None

    # W-014 cleanup: remove scratch _sh_vN.exe + _sh_vN.il + .s (ld.exe also emits .s).
    # Keep canonical jhyy_vN.exe (committed at v1.0.0) untouched.
    for stage, _, output_rel in chain:
        for ext in (".exe", ".il", ".s"):
            _safe_remove(_resolve_path(output_rel) + ext, retries=2, delay_ms=200)

    return {
        "ok": all_byte_equal,
        "all_byte_equal": all_byte_equal,
        "il_sha256": common_sha,
        "binary_chain": binary_chain_out,
        "il_files": il_files,
        "early_abort": None if all_byte_equal else (
            f"IL files NOT byte-equal! Unique shas: " +
            ", ".join(f"{k}={v[:16]}..." for k, v in il_files.items())
        ),
        "duration_sec": round(time.time() - start, 2),
    }
