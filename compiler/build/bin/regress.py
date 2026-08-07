#!/usr/bin/env python3
"""Run all integration tests and report pass/fail."""
import subprocess
import sys
import os
import re

JHYY = os.path.abspath(os.environ.get("JHYY_CC", "compiler/build/bin/jhyy.exe"))
TEST_DIR = os.path.abspath("compiler/tests/examples")
TIMEOUT = 10

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

def ntstatus_name(code):
    if code is None or code < 0:
        return None
    if code >= 0xC0000000:
        return NTSTATUS_NAMES.get(code, f"NTSTATUS_0x{code:08X}")
    return None

def run_test(jhyy_file):
    """Compile and run a single .jhyy test, return (passed, expected_exit, actual_exit, output)."""
    name = os.path.splitext(os.path.basename(jhyy_file))[0]
    out_base = f"compiler/build/bin/_regress_{name}"

    # Sprint 4.4 C: stale .exe hardening — 避免 stale cache 掩盖 cleanup crash
    for ext in (".il", ".s", ".exe"):
        p = out_base + ext
        if os.path.exists(p):
            os.remove(p)

    # Read expected exit from comment if present
    expected = None
    has_main = False
    try:
        with open(jhyy_file, encoding='utf-8') as f:
            src = f.read()
        m = re.search(r'//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)', src)
        if m:
            expected = int(m.group(1))
        # Skip library files (no main entry)
        has_main = bool(re.search(r'\bfn\s+main_jhyy\b', src))
    except UnicodeDecodeError:
        pass

    if not has_main:
        # Library file: skip (no standalone run possible)
        return (True, None, None, "skipped (library)")

    # Compile
    r = subprocess.run([JHYY, "compile", jhyy_file, "-o", out_base],
                       capture_output=True, text=True, timeout=20,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return (False, expected, -1, f"compile failed: {r.stderr[:200]}")
    exe = os.path.abspath(out_base + ".exe")
    if not os.path.exists(exe):
        return (False, expected, -2, "exe not created")

    # Run
    try:
        r2 = subprocess.run([exe], capture_output=True, text=True, timeout=TIMEOUT,
                             encoding='utf-8', errors='replace')
        actual = r2.returncode
        output = (r2.stdout or "") + (r2.stderr or "")
    except subprocess.TimeoutExpired:
        return (False, expected, -3, f"timeout ({TIMEOUT}s)")

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

def main():
    files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".jhyy") and not f.startswith("_"))

    passed, failed, total, skipped = 0, 0, 0, 0
    for fname in files:
        path = os.path.join(TEST_DIR, fname)
        ok, exp, act, msg = run_test(path)
        total += 1
        if ok and msg == "skipped (library)":
            print(f"SKIP  {fname:<30}  (library, no main)")
            skipped += 1
        elif ok:
            print(f"PASS  {fname:<30}  EXIT={act}")
            passed += 1
        else:
            print(f"FAIL  {fname:<30}  expected={exp} got={act}  {msg[:80]}")
            failed += 1

    print(f"\n===== {passed}/{total} passed, {failed} failed, {skipped} skipped =====")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
