#!/usr/bin/env python3
"""Run all integration tests and report pass/fail."""
import subprocess
import sys
import os
import re

JHYY = "compiler/build/bin/jhyy.exe"
TEST_DIR = "compiler/tests/examples"
TIMEOUT = 10

def run_test(jhyy_file):
    """Compile and run a single .jhyy test, return (passed, expected_exit, actual_exit, output)."""
    name = os.path.splitext(os.path.basename(jhyy_file))[0]
    out_base = f"compiler/build/bin/_regress_{name}"

    # Read expected exit from comment if present
    expected = None
    try:
        with open(jhyy_file, encoding='utf-8') as f:
            src = f.read()
        m = re.search(r'//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)', src)
        if m:
            expected = int(m.group(1))
    except UnicodeDecodeError:
        pass

    # Compile
    r = subprocess.run([JHYY, "compile", jhyy_file, "-o", out_base],
                       capture_output=True, text=True, timeout=20,
                       encoding='utf-8', errors='replace')
    if r.returncode != 0:
        return (False, expected, -1, f"compile failed: {r.stderr[:200]}")
    exe = out_base + ".exe"
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
        # No EXPECT annotation: pass if compiles and runs
        return (True, actual, actual, output)
    return (actual == expected, expected, actual, output)

def main():
    files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".jhyy") and not f.startswith("_"))

    passed, failed, total = 0, 0, 0
    for fname in files:
        path = os.path.join(TEST_DIR, fname)
        ok, exp, act, msg = run_test(path)
        total += 1
        if ok:
            print(f"PASS  {fname:<30}  EXIT={act}")
            passed += 1
        else:
            print(f"FAIL  {fname:<30}  expected={exp} got={act}  {msg[:80]}")
            failed += 1

    print(f"\n===== {passed}/{total} passed, {failed} failed =====")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
