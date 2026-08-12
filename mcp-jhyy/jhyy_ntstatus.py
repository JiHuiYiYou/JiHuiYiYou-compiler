"""jhyy_ntstatus.py — Windows NTSTATUS 名称表 (Sprint mcp-2 shared module)

之前 NTSTATUS_NAMES + ntstatus_name() 内联在 jhyy_regress.py — compile_and_run
没法判断 exit code 是 NTSTATUS (crash) 还是普通程序退出, 所以 fib30 exit 832040
被误报 ok=false. 抽到独立模块, jhyy_regress 和 jhyy_runner 都 import.

Public API:
    NTSTATUS_NAMES: dict[int, str]  — code → name (e.g. 0xC0000005 → ACCESS_VIOLATION)
    ntstatus_name(code)             → str | None (None 表示非 NTSTATUS = 普通退出)
"""
from typing import Optional


# Windows NTSTATUS codes JHYY regress cares about. 完整表见
# https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-erref/596a5078-ff23-4eab-b5b8-5591d2443a06
NTSTATUS_NAMES = {
    0xC0000005: "ACCESS_VIOLATION",
    0xC0000006: "INVALID_HANDLE",
    0xC0000008: "INVALID_HANDLE",
    0xC000001D: "ILLEGAL_INSTRUCTION",
    0xC000008C: "ARRAY_BOUNDS_EXCEEDED",
    0xC0000094: "INTEGER_DIVIDE_BY_ZERO",
    0xC0000096: "PRIVILEGED_INSTRUCTION",
    0xC00000FD: "STACK_OVERFLOW",
    0xC0000374: "HEAP_CORRUPTION",
    0xC0000409: "STACK_BUFFER_OVERRUN",
    0xC000041D: "STATUS_FATAL_USER_CALLBACK_EXCEPTION",
}


def ntstatus_name(code: Optional[int]) -> Optional[str]:
    """Return the NTSTATUS name for a Windows exit code, or None if not NTSTATUS.

    A normal program exit (code 0..0xBFFFFFFF, including positive large ints like
    832040 from `exit(832040)`) returns None — this means "not a crash, the program
    just exited with this code". Use this in ok gates:
        ok = (exit_code == 0) or (ntstatus_name(exit_code) is None)

    Args:
        code: process exit code, or None if process didn't exit

    Returns:
        NTSTATUS name string if code is in 0xC0000000-0xCFFFFFFF range, else None.
    """
    if code is None or code < 0:
        return None
    if code >= 0xC0000000:
        return NTSTATUS_NAMES.get(code, f"NTSTATUS_0x{code:08X}")
    return None