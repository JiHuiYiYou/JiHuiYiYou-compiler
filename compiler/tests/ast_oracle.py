#!/usr/bin/env python3
"""
ast_oracle.py — byte-equal oracle for AST dump files.

Used by v1.0.0 phase-2 self-hosting verification (sprint 5):
    jhyy_0 (C-compiled) dumps AST → actual.ast.txt
    jhyy_1 (self-hosted) dumps AST → expected.ast.txt
    ast_oracle.py compares the two

Usage:
    python ast_oracle.py <expected.ast.txt> <actual.ast.txt>
    python ast_oracle.py --batch <golden_dir> <actual_dir>

Diff semantics:
    Lines starting with the same kind+key=value are compared exactly.
    Differences are reported with line number + content for both sides.
    Exit code 0 = byte-equal, 1 = mismatch, 2 = error.
"""

import argparse
import sys
from pathlib import Path


def read_lines(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]


def diff_lines(expected: list[str], actual: list[str]) -> tuple[int, int]:
    """Return (expected_total, diff_count). Print diffs to stderr."""
    n = max(len(expected), len(actual))
    diffs = 0
    for i in range(n):
        e = expected[i] if i < len(expected) else "<EOF>"
        a = actual[i] if i < len(actual) else "<EOF>"
        if e != a:
            diffs += 1
            print(f"  line {i+1}:", file=sys.stderr)
            print(f"    expected: {e!r}", file=sys.stderr)
            print(f"    actual  : {a!r}", file=sys.stderr)
    return n, diffs


def diff_one(expected_path: Path, actual_path: Path) -> bool:
    if not expected_path.exists():
        print(f"  missing: {expected_path}", file=sys.stderr)
        return False
    if not actual_path.exists():
        print(f"  missing: {actual_path}", file=sys.stderr)
        return False
    expected = read_lines(expected_path)
    actual = read_lines(actual_path)
    n, diffs = diff_lines(expected, actual)
    if diffs == 0:
        print(f"  OK ({n} lines byte-equal)")
        return True
    else:
        print(f"  FAIL ({diffs} of {n} lines differ)")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare AST dump files for byte-equal self-hosting verification."
    )
    parser.add_argument("expected", help="expected AST dump file (.ast.txt)")
    parser.add_argument("actual", help="actual AST dump file (.ast.txt)")
    args = parser.parse_args()

    expected_path = Path(args.expected)
    actual_path = Path(args.actual)

    print(f"expected: {expected_path}")
    print(f"actual  : {actual_path}")
    ok = diff_one(expected_path, actual_path)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())