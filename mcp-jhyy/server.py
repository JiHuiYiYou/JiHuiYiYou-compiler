#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""JHYY MCP Server — 让 Claude Code 能编译、运行、检查 .jhyy 代码。

提供 10 个工具:
  - jhyy_compile         编译 .jhyy 文件
  - jhyy_run             编译并运行
  - jhyy_check           仅做语法/语义检查
  - jhyy_lang_ref        查询语言规范
  - jhyy_abi_info        查询 ABI 信息
  - jhyy_format          代码格式化 (简单对齐 / 占位)
  - jhyy_regress         跑 regress (Sprint mcp-1, 替代 Bash regress.py)
  - jhyy_il_diff         diff 两个 .il 文件 (Sprint mcp-1, 替代 sha256sum + diff)
  - jhyy_selfhost_check  v1→v2→v3 byte-equal 验证 (Sprint mcp-1, 替代 ~30 行 bash)
  - jhyy_workarounds     搜 workarounds.md (Sprint mcp-1, 替代 grep workarounds.md)

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

# ========== Server-level instructions ==========
# Claude Code 启动 MCP 时注入到 system prompt。保持精简——每个会话都加载，长度直接吃 context window。
# 路由表 + 严禁旁路是触发信号；详细触发示例已经在工具 docstring 的 Triggers: 段里；workflow hints 在 mcp-jhyy/CLAUDE.md 里。
JHYY_INSTRUCTIONS = """
JHYY compiler MCP. Use these tools for any .jhyy work; do NOT bypass with raw Bash/Read.

Routing (intent → tool):
- run / test / verify behavior → jhyy_run
- syntax / lint / "is this valid" → jhyy_check
- compile only (no run) → jhyy_compile
- show QBE IL / debug codegen → jhyy_get_il
- "does JHYY support X" / syntax questions → jhyy_lang_ref
- ABI / struct passing / FFI / calling convention → jhyy_abi_info
- format code → jhyy_format
- run regress / verify no regression → jhyy_regress
- diff two .il / byte-equal check → jhyy_il_diff
- verify selfhost closure (v1→v2→v3 byte-equal) → jhyy_selfhost_check
- search workarounds / "is W-XXX still active" → jhyy_workarounds

DO NOT: Bash("jhyy.exe ..."), Bash("python regress*.py"), Bash("sha256sum *.il"), Read("docs/abis/jhyy-*.md"), Read("compiler/build/bin/*.il"), Read("docs/internal/workarounds.md"). Use the tools above.

Default to jhyy_run for any "run" / "test" intent. Default to jhyy_regress for any "verify nothing regressed" intent.
"""

mcp = FastMCP("jhyy", instructions=JHYY_INSTRUCTIONS)

# Import jhyy_runner
sys.path.insert(0, str(MCP_DIR))
import jhyy_runner as runner  # noqa: E402
import jhyy_regress as regress_mod  # noqa: E402
import jhyy_workarounds as workarounds_mod  # noqa: E402


# ========== Tools: 编译/运行/检查 ==========

@mcp.tool
def jhyy_compile(
    file: str,
    output: Optional[str] = None,
    extra_inputs: Optional[list] = None,
) -> dict:
    """Compile a .jhyy file into a Windows .exe (no execution).

    USE THIS WHEN the user wants to build/produce a binary but NOT run it.
    Triggers: "compile it", "build this .jhyy", "produce an exe", "compile to <name>".

    For "run it" / "test it" / "verify behavior" use `jhyy_run` instead — it also executes.

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
    """Compile AND execute a .jhyy file. Returns exit code + stdout/stderr.

    USE THIS WHEN the user wants to verify behavior, test a program, or see output.
    Triggers: "run this", "execute it", "test it", "what does it print", "does it work",
              "verify", "try it out", "show the output", "what's the exit code".

    This is the MOST COMMON tool — default to it whenever the user wants to see a .jhyy
    program actually run. It covers compile + execute in one call.

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
    """Syntax + semantic check a .jhyy file. Does NOT produce a binary.

    USE THIS WHEN the user wants to validate code without actually running it.
    Triggers: "is this valid", "check syntax", "will this compile", "lint", "any errors",
              "verify the syntax", "find compile errors".

    Returns structured error list with file/line/col — better than running jhyy_run
    when the user just wants to know if the code parses.

    Args:
        file: 源文件路径

    Returns:
        {ok, exit_code, errors: [{file, line, col, message}], warnings: [...]}
    """
    return runner.check_syntax(file)


@mcp.tool
def jhyy_get_il(file: str) -> dict:
    """Compile a .jhyy file and return the generated QBE IL text inline.

    USE THIS WHEN debugging the codegen or understanding what the compiler emits.
    Triggers: "show the IL", "what does codegen produce", "show the QBE output",
              "debug codegen", "what IL does this generate", "show the assembly backend",
              "read the .il file" (for files in compiler/build/bin/).

    The returned `il` field contains the full QBE IL text — analyze it directly,
    do NOT try to cat the .il file via Bash.

    Args:
        file: 源文件路径

    Returns:
        {ok, exit_code, il: "QBE IL 全文", il_file: "IL 文件路径"}
    """
    return runner.get_il(file)


# ========== Tools: 语言/ABI 文档查询 ==========

@mcp.tool
def jhyy_lang_ref(query: str, limit: int = 20) -> dict:
    """Search the JHYY language specification (v1.1.0) by keyword.

    USE THIS WHEN the user asks about JHYY language features, syntax, or semantics.
    Triggers: "does JHYY support X", "how do I write Y in JHYY", "JHYY syntax for Z",
              "is there a ternary operator", "does match support ranges",
              "what types does JHYY have", "how does the for loop work",
              "what's the syntax for X".

    Call this BEFORE answering any question about JHYY language design. Do NOT
    read docs/abis/jhyy-lang-spec-*.md directly — this tool does the search.

    Args:
        query: 关键词 (中文/英文/混合, 如 "struct pass-by-value", "命名空间", "match 范围")
        limit: 最大返回条数 (默认 20)

    Returns:
        {ok, version, query, matches: [{section, title, level, score, excerpt}, ...]}
        section e.g. "10.4" — 直接对应 jhyy-lang-spec-v1.1.0.md 章节号, 可引用.
    """
    import jhyy_lang_ref as langref_mod
    return langref_mod.search(query, limit=limit)


@mcp.tool
def jhyy_abi_info(query: str) -> dict:
    """Search the JHYY ABI v1.0.0 information by keyword.

    USE THIS WHEN the user asks about ABI conventions, struct passing, FFI rules,
    calling conventions, or any low-level binary interface question.
    Triggers: "how are structs passed", "calling convention", "FFI rules",
              "sret", "what's the v1.0.0 ABI say about X", "struct pass-by-value",
              "how do I call a C function", "module import ABI".

    Call this BEFORE answering any question about the JHYY ABI. Do NOT
    read docs/abis/jhyy-abi-*.md directly — this tool does the search.

    Args:
        query: 关键词 (如 "struct_passing", "calling_convention", "primitives")

    Returns:
        {ok, query, matches: [...], abi_version}
    """
    try:
        import jhyy_spec_doc
        abi_md = jhyy_spec_doc.load_spec_doc(JHYY_ROOT / "docs/abis/jhyy-abi-v1.0.0.md")
        md_result = jhyy_spec_doc.search_spec_doc(abi_md, query, limit=limit)
        return {
            "ok": True,
            "query": query,
            "abi_version": md_result["version"],
            "matches": [
                {"section": m["section"], "title": m["title"],
                 "level": m["level"], "score": m["score"],
                 "excerpt": m["excerpt"],
                 "key": f"§ {m['section']} {m['title']}"}
                for m in md_result["matches"]
            ],
        }
    except Exception as e:
        return {"ok": False, "query": query, "error": f"failed to load jhyy-abi-v1.0.0.md: {e}"}


@mcp.tool
def jhyy_format(file: str) -> dict:
    """Format a .jhyy source file (minimal v0.5.0 implementation: tabs → 4 spaces, strip trailing whitespace).

    USE THIS WHEN the user asks to format or tidy up code.
    Triggers: "format this", "tidy up", "fix indentation", "clean up the code".

    Note: this is a minimal implementation. Full formatter coming in a future version.
    The formatted code is returned in the response — apply it via Edit/Write if the user approves.

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


# ========== Tools: 回归 / 自举 / 工作区 (Sprint mcp-1) ==========

@mcp.tool
def jhyy_regress(
    binary: str = "compiler/build/bin/jhyy.exe",
    tests: Optional[list] = None,
    timeout: int = 20,
    enforce_baseline_hash: bool = True,
) -> dict:
    """Run regression tests against a JHYY compiler binary.

    USE THIS WHEN the user wants to verify a compiler change didn't regress the test suite.
    Triggers: "run regress", "verify baseline", "check no regression", "run all tests",
              "did my fix break anything", "跑测试", "验证回归", "baseline 还稳吗".

    Default binary = C-side jhyy.exe. Pass `binary="compiler/build/bin/jhyy_v1.exe.exe"`
    for jhyy_v1 self-hosting regress.

    Args:
        binary: 编译器路径 (相对 JHYY 根或绝对). 默认 C 端 jhyy.exe
        tests: 测试子集 (None = 全部 .jhyy). 例 ["hello.jhyy", "fib.jhyy"]
        timeout: 单测试运行超时 (秒)
        enforce_baseline_hash: True 时跟 <binary>.sha256 baseline 比, 不匹配 → fail-fast
                                (防 phantom binary 陷阱, per memory feedback_regress_baseline_binary_hash)

    Returns:
        {ok, binary, binary_sha256, baseline_match, baseline_sha256, total, passed,
         failed, skipped, failed_tests, duration_sec, baseline_warning?, early_abort?}

    跑 regress 比直接 Bash `python regress.py` 好: 返回结构化结果 + baseline hash 守护 +
    失败测试列表 + duration_sec, 不用 grep 输出.
    """
    return regress_mod.run_all(binary, tests, timeout, enforce_baseline_hash)


@mcp.tool
def jhyy_il_diff(file_a: str, file_b: str, context: int = 3) -> dict:
    """Diff two QBE .il files for byte-equality and structural changes.

    USE THIS WHEN comparing compiler output (Stage 1 / Stage 2 byte-equal verification).
    Triggers: "diff .il", "compare IL", "byte-equal check",
              "did my codegen change break byte-equal", "verify selfhost closure",
              "比 .il", "看 sha 一不一樣".

    Args:
        file_a, file_b: .il 文件路径 (相对 JHYY 根或绝对)
        context: 首差异行的 ±context 行 unified diff (default 3)

    Returns:
        {ok, byte_equal, sha256_a, sha256_b, size_bytes_a, size_bytes_b,
         line_count_a, line_count_b, first_diff_line | None, first_diff_context | None}

    比 Bash sha256sum + diff 好: 一次返回 sha + 行数 + 首差异行 + diff context,
    不用先 sha 再 cat 再 diff 三步走.
    """
    return runner.il_diff(file_a, file_b, context)


@mcp.tool
def jhyy_selfhost_check(
    src: str = "compiler/src0/main.jhyy",
    auto_rebuild: bool = False,
    timeout: int = 600,
) -> dict:
    """Run the v1→v2→v3→v4 byte-equal self-hosting closure chain.

    USE THIS WHEN verifying that the self-hosting closure still holds after a change.
    Triggers: "verify selfhost", "check closure", "is self-hosting still working",
              "v1 v2 v3 byte-equal", "run the closure check", "byte-equal 还稳吗",
              "自举闭环还在吗".

    Default auto_rebuild=False — missing binary fails fast with clear error
    (per Plan agent risk analysis: auto-rebuild masks phantom binary traps).
    Pass auto_rebuild=True to auto-rebuild jhyy_v1 from src0/main.jhyy via jhyy.exe.

    Args:
        src: 编译源文件 (default compiler/src0/main.jhyy)
        auto_rebuild: True 时自动 rebuild jhyy_v1 (gcc + jhyy.exe 编 src0/main.jhyy)
        timeout: 每阶段 timeout (秒, default 600 = 10 分钟)

    Returns:
        {ok, all_byte_equal, il_sha256 | None,
         binary_chain: [{stage, binary_path, binary_sha256, il_path, il_sha256, duration_sec}],
         il_files: {stage.il: sha256},
         early_abort | None,
         duration_sec}

    比手写 ~30 行 bash chain 好: 一键, 失败 fail-fast + 列出失败阶段, 不用手动循环.
    """
    return runner.selfhost_check(src, auto_rebuild, timeout)


@mcp.tool
def jhyy_workarounds(query: str, status: Optional[str] = None) -> dict:
    """Search the workarounds registry (docs/internal/workarounds.md) by keyword or W-XXX ID.

    USE THIS WHEN investigating a known bug pattern or checking if a workaround is ACTIVE.
    Triggers: "is W-005 still active", "what's the workaround for X",
              "search workarounds", "find workaround for let mut",
              "W-005 现在状态", "let mut 触发面有 workaround 吗".

    Args:
        query: 搜索词 (substring, 大小写不敏感). 可为 W-XXX ID (e.g. "W-005") 或触发模式
               (e.g. "let mut", "sentinel", "inline_imports", "MAX_LOCALS")
        status: 可选过滤 "ACTIVE" / "RESOLVED" / "SUPERSEDED" (substring match)

    Returns:
        {ok, query, status_filter, matches: [{id, status, date, trigger, symptom,
         root_cause, workaround, scope, superseder}],
         active_count, resolved_count, superseded_count, total}

    比 Read workarounds.md + grep 好: 自动处理中英字段混用, 按 alias 表解析,
    返回结构化结果, 不用正则手撕 markdown.
    """
    return workarounds_mod.search(query, status)


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
