#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jhyy_runner.py — subprocess 封装 + 诊断解析"""
import subprocess
import os
import re
import json
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
    return {
        "ok": rresult["ok"],
        "stage": "run",
        "exit_code": rresult["exit_code"],
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
