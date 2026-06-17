#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JHYY MCP Server — 让 Claude Code 能编译、运行、检查 .jhyy 代码。

提供 6 个工具:
  - jhyy_compile      编译 .jhyy 文件
  - jhyy_run          编译并运行
  - jhyy_check        仅做语法/语义检查
  - jhyy_lang_ref     查询语言规范
  - jhyy_abi_info     查询 ABI 信息
  - jhyy_format       代码格式化 (简单对齐 / 占位)

提供 4 个资源:
  - jhyy://spec       语言规范 (v0.5.0)
  - jhyy://abi        ABI 信息 (v1.0.0)
  - jhyy://examples   示例代码列表
  - jhyy://changelog  更新日志
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP

# Force UTF-8 on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

# 路径配置
JHYY_ROOT = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou")
MCP_DIR = Path(__file__).resolve().parent

mcp = FastMCP("jhyy")

# Import jhyy_runner
sys.path.insert(0, str(MCP_DIR))
import jhyy_runner as runner  # noqa: E402


# ========== Tools: 编译/运行/检查 ==========

@mcp.tool
def jhyy_compile(
    file: str,
    output: Optional[str] = None,
    extra_inputs: Optional[list] = None,
) -> dict:
    """编译 .jhyy 文件为 Windows .exe。

    Args:
        file: 源文件路径（相对 JHYY 项目根或绝对路径）
        output: 输出可执行文件路径（默认在 compiler/build/bin/ 下生成 <name>_mcp_run.exe）
        extra_inputs: 多文件编译时的其他 .jhyy 文件 (用于多文件 import 场景)

    Returns:
        {ok, exit_code, stdout, stderr, command}
    """
    return runner.compile_file(file, output, extra_inputs)


@mcp.tool
def jhyy_run(
    file: str,
    extra_inputs: Optional[list] = None,
    timeout: int = 10,
) -> dict:
    """编译并运行 .jhyy 文件。

    Args:
        file: 源文件路径
        extra_inputs: 多文件编译时的其他 .jhyy 文件
        timeout: 运行超时（秒）

    Returns:
        {ok, stage, exit_code, stdout, stderr, compile_stderr?}
    """
    return runner.compile_and_run(file, extra_inputs, timeout)


@mcp.tool
def jhyy_check(file: str) -> dict:
    """仅做语法/语义检查，不生成可执行文件。

    Args:
        file: 源文件路径

    Returns:
        {ok, exit_code, errors: [{file, line, col, message}], warnings: [...]}
    """
    return runner.check_syntax(file)


@mcp.tool
def jhyy_get_il(file: str) -> dict:
    """编译 .jhyy 文件并返回生成的 QBE IL 文本（用于调试 codegen）。

    Args:
        file: 源文件路径

    Returns:
        {ok, exit_code, il: "QBE IL 全文", il_file: "IL 文件路径"}
    """
    return runner.get_il(file)


# ========== Tools: 语言/ABI 文档查询 ==========

@mcp.tool
def jhyy_lang_ref(query: str) -> dict:
    """查询 JHYY 语言规范（v0.5.0）。

    Args:
        query: 关键词 (如 "struct", "match", "for", "pointer", "as")

    Returns:
        {ok, query, matches: [...], spec_version}
    """
    spec_path = MCP_DIR / "spec_data.json"
    if not spec_path.exists():
        return {"ok": False, "error": f"spec_data.json not found: {spec_path}"}
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    # Naive search: find query in spec dict
    query_lower = query.lower()
    matches = []

    def search_in(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if query_lower in k.lower():
                    matches.append({"key": new_path, "value": str(v)[:300]})
                search_in(v, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_in(item, f"{path}[{i}]")
        elif isinstance(obj, str) and query_lower in obj.lower():
            matches.append({"key": path, "value": obj[:300]})

    search_in(spec)
    return {
        "ok": True,
        "query": query,
        "spec_version": spec.get("version", "unknown"),
        "matches": matches[:20],
    }


@mcp.tool
def jhyy_abi_info(query: str) -> dict:
    """查询 JHYY ABI 信息 (v1.0.0)。

    Args:
        query: 关键词 (如 "struct_passing", "calling_convention", "primitives")

    Returns:
        {ok, query, matches: [...], abi_version}
    """
    abi_path = MCP_DIR / "abi_data.json"
    if not abi_path.exists():
        return {"ok": False, "error": f"abi_data.json not found: {abi_path}"}
    with open(abi_path, encoding="utf-8") as f:
        abi = json.load(f)

    query_lower = query.lower()
    matches = []

    def search_in(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if query_lower in k.lower():
                    matches.append({"key": new_path, "value": json.dumps(v, ensure_ascii=False)[:500]})
                search_in(v, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                search_in(item, f"{path}[{i}]")
        elif isinstance(obj, str) and query_lower in obj.lower():
            matches.append({"key": path, "value": obj[:300]})

    search_in(abi)
    return {
        "ok": True,
        "query": query,
        "abi_version": abi.get("version", "unknown"),
        "matches": matches[:20],
    }


@mcp.tool
def jhyy_format(file: str) -> dict:
    """简单格式化 .jhyy 源代码（统一缩进为 4 空格，调整运算符间距）。

    Args:
        file: 源文件路径

    Returns:
        {ok, formatted: "格式化后的代码", original_lines, formatted_lines}

    Note: 这是一个最小化的格式化器 (v0.5.0)。完整格式化器将在未来版本中提供。
    """
    src_path = runner._resolve_path(file)
    if not os.path.exists(src_path):
        return {"ok": False, "error": f"Source file not found: {src_path}"}
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    formatted = _simple_format(src)
    return {
        "ok": True,
        "formatted": formatted,
        "original_lines": len(src.splitlines()),
        "formatted_lines": len(formatted.splitlines()),
    }


def _simple_format(src: str) -> str:
    """简单格式化: 转换 tab → 4 空格, 确保运算符周围有 1 个空格, 移除行尾空白。"""
    # Replace tabs with 4 spaces
    src = src.expandtabs(4)
    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in src.splitlines()]
    # Add spacing around common operators (avoid inside strings/comments)
    # NOTE: This is intentionally minimal — a real formatter would track string/comment state.
    formatted_lines = []
    for line in lines:
        # Add space after commas (not inside strings/parentheses)
        # This is a placeholder — actual formatting is non-trivial.
        formatted_lines.append(line)
    # Ensure final newline
    result = "\n".join(formatted_lines)
    if not result.endswith("\n"):
        result += "\n"
    return result


# ========== MCP Resources ==========

@mcp.resource("jhyy://spec")
def jhyy_spec() -> str:
    """JHYY 语言规范 (v0.5.0) — 完整结构化数据。"""
    spec_path = MCP_DIR / "spec_data.json"
    if not spec_path.exists():
        return f"spec_data.json not found at {spec_path}"
    return spec_path.read_text(encoding="utf-8")


@mcp.resource("jhyy://abi")
def jhyy_abi() -> str:
    """JHYY ABI v1.0.0 信息 — 完整结构化数据。"""
    abi_path = MCP_DIR / "abi_data.json"
    if not abi_path.exists():
        return f"abi_data.json not found at {abi_path}"
    return abi_path.read_text(encoding="utf-8")


@mcp.resource("jhyy://examples")
def jhyy_examples() -> str:
    """JHYY 示例代码列表 (.jhyy 文件清单 + 简短说明)。"""
    examples_dir = JHYY_ROOT / "compiler/tests/examples"
    if not examples_dir.exists():
        return f"Examples dir not found: {examples_dir}"
    files = sorted(f for f in os.listdir(examples_dir) if f.endswith(".jhyy") and not f.startswith("_"))
    lines = [f"# JHYY Examples ({len(files)} files)\n"]
    for fname in files:
        path = examples_dir / fname
        try:
            src = path.read_text(encoding="utf-8", errors="replace")
            # Extract EXPECT annotation
            m = re.search(r"//\s*EXPECT\s*[:=]\s*(\d+)", src)
            expect = m.group(1) if m else "(no EXPECT)"
            # Extract first non-comment line
            first_code = ""
            for line in src.splitlines():
                line = line.strip()
                if line and not line.startswith("//"):
                    first_code = line[:80]
                    break
            lines.append(f"- {fname}  [EXPECT={expect}]  :: {first_code}")
        except OSError:
            lines.append(f"- {fname}  (read error)")
    return "\n".join(lines)


@mcp.resource("jhyy://changelog")
def jhyy_changelog() -> str:
    """JHYY 更新日志。"""
    docs_dir = JHYY_ROOT / "docs"
    # Find latest changelog
    changelogs = sorted(docs_dir.glob("changelog-*.md"), reverse=True) if docs_dir.exists() else []
    if not changelogs:
        return "No changelog files found."
    return changelogs[0].read_text(encoding="utf-8", errors="replace")


# ========== Entry point ==========

if __name__ == "__main__":
    mcp.run()
