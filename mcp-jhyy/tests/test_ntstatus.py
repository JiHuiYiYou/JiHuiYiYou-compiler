"""test_ntstatus.py — jhyy_ntstatus 回归测试 (Sprint mcp-2 D)

之前 NTSTATUS_NAMES 内联在 jhyy_regress.py — compile_and_run 没法区分
"程序正常 exit 832040" 和 "Windows crash 0xC0000005". 现在 NTSTATUS gate
走 jhyy_ntstatus.ntstatus_name, 普通退出 (0..0xBFFFFFFF) 返回 None, crash
(0xC0000000+) 返回 NTSTATUS 名称.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jhyy_ntstatus


def test_known_ntstatus_access_violation():
    assert jhyy_ntstatus.ntstatus_name(0xC0000005) == "ACCESS_VIOLATION"


def test_known_ntstatus_heap_corruption():
    assert jhyy_ntstatus.ntstatus_name(0xC0000374) == "HEAP_CORRUPTION"


def test_known_ntstatus_stack_overflow():
    assert jhyy_ntstatus.ntstatus_name(0xC00000FD) == "STACK_OVERFLOW"


def test_unknown_ntstatus_in_range_returns_hex():
    """0xC0000999 not in NTSTATUS_NAMES but in NTSTATUS range → hex string."""
    name = jhyy_ntstatus.ntstatus_name(0xC0000999)
    assert name == "NTSTATUS_0xC0000999", f"unexpected: {name!r}"


def test_normal_exit_zero_returns_none():
    assert jhyy_ntstatus.ntstatus_name(0) is None


def test_normal_exit_positive_returns_none():
    """fib30 exit 832040 is a normal program exit, NOT a crash."""
    assert jhyy_ntstatus.ntstatus_name(832040) is None


def test_normal_exit_max_user_code_returns_none():
    """Max user-space exit code before NTSTATUS range = 0x7FFFFFFF."""
    assert jhyy_ntstatus.ntstatus_name(0x7FFFFFFF) is None


def test_below_ntstatus_range_returns_none():
    assert jhyy_ntstatus.ntstatus_name(0xBFFFFFFF) is None


def test_none_returns_none():
    """Process didn't exit (timeout / no returncode)."""
    assert jhyy_ntstatus.ntstatus_name(None) is None


def test_negative_returns_none():
    """Negative codes are Unix signal conventions, not NTSTATUS."""
    assert jhyy_ntstatus.ntstatus_name(-1) is None


def test_regress_back_compat_import():
    """jhyy_regress.py re-exports NTSTATUS_NAMES + ntstatus_name for back-compat."""
    import jhyy_regress
    assert jhyy_regress.NTSTATUS_NAMES is jhyy_ntstatus.NTSTATUS_NAMES
    assert jhyy_regress.ntstatus_name is jhyy_ntstatus.ntstatus_name


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)