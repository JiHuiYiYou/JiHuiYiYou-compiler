#!/usr/bin/env python3
"""Run integration tests with jhyy_v1.exe (self-hosting compiler) and report pass/fail."""
import subprocess
import sys
import os
import re

JHYY_V1 = os.path.abspath(os.environ.get("JHYY_V1_BIN", "compiler/build/bin/jhyy_v1.exe.exe"))
TEST_DIR = os.path.abspath("compiler/tests/examples")
PROJECT_ROOT = os.path.abspath(".")
TIMEOUT = 10

def to_jhyy_arg(p):
    """Convert path for jhyy_v1 invocation: backslash for absolute, relative for cwd-relative."""
    p = os.path.abspath(p)
    if p.startswith("C:"):
        return p.replace("/", "\\")
    return p

def run_test(jhyy_file):
    name = os.path.splitext(os.path.basename(jhyy_file))[0]
    out_base = f"compiler/build/bin/_v1regress_{name}"

    expected = None
    has_main = False
    try:
        with open(jhyy_file, encoding='utf-8') as f:
            src = f.read()
        m = re.search(r'//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)', src)
        if m:
            expected = int(m.group(1))
        has_main = bool(re.search(r'\bfn\s+main_jhyy\b', src))
    except UnicodeDecodeError:
        pass

    if not has_main:
        return (True, None, None, "skipped (library)")

    # Cleanup prior artifacts (避免 stale exe 干扰)
    for ext in (".il", ".s", ".exe"):
        try: os.remove(out_base + ext)
        except FileNotFoundError: pass

    try:
        # Use relative paths from cwd = project root. jhyy_v1 segfaults on
        # absolute paths with forward slashes (buffer overflow in main.c
        # path_to_win replacement), so feed it relative paths via cwd.
        rel_jhyy = os.path.relpath(jhyy_file, PROJECT_ROOT)
        rel_out = os.path.relpath(out_base, PROJECT_ROOT)
        rel_jhyy_v1 = os.path.relpath(JHYY_V1, PROJECT_ROOT)
        r = subprocess.run([rel_jhyy_v1, "compile", rel_jhyy, "-o", rel_out],
                           capture_output=True, text=True, timeout=20,
                           encoding='utf-8', errors='replace', cwd=PROJECT_ROOT)
    except subprocess.TimeoutExpired:
        return (False, expected, -4, "compile timeout")

    # Windows NTSTATUS >= 0x80000000 (= -ve signed) = segfault/access violation
    # (Linux: signal 139 SIGSEGV; Windows: 0xC0000004 / 0xC0000005 etc.)
    if r.returncode < 0 or r.returncode >= 0x80000000:
        return (False, expected, r.returncode, "compile segfault (NTSTATUS)")
    if r.returncode != 0:
        err = (r.stderr or "").strip().split("\n")[0]
        return (False, expected, r.returncode, f"compile failed: {err[:120]}")
    exe = out_base + ".exe"
    if not os.path.exists(exe):
        return (False, expected, -2, "exe not created")
    exe = os.path.relpath(exe, PROJECT_ROOT)

    try:
        r2 = subprocess.run([exe], capture_output=True, text=True, timeout=TIMEOUT,
                             encoding='utf-8', errors='replace')
        actual = r2.returncode
        output = (r2.stdout or "") + (r2.stderr or "")
    except subprocess.TimeoutExpired:
        return (False, expected, -3, f"run timeout ({TIMEOUT}s)")

    if expected is None:
        return (True, actual, actual, output)
    return (actual == expected, expected, actual, output)

def main():
    files = sorted(f for f in os.listdir(TEST_DIR) if f.endswith(".jhyy") and not f.startswith("_"))

    passed, failed, total, skipped = 0, 0, 0, 0
    fails = []
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
            fails.append((fname, exp, act, msg[:80]))

    print(f"\n===== {passed}/{total} passed, {failed} failed, {skipped} skipped =====")
    print(f"\n=== Failures ===")
    for fname, exp, act, msg in fails:
        print(f"  {fname:<30}  expected={exp} got={act}  {msg}")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()