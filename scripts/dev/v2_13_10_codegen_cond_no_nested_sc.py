#!/usr/bin/env python3
"""v2.13.10 — convention enforcement: codegen.jhyy no nested short-circuit in if-conditions.

Per workarounds.md W-082 (v2.13.10 audit-flip docs-only + convention enforced):
trigger pattern is `if A && (B || C)` or `if A || (B && C)` in codegen-internal
if-conditions. W-058 v2.13.8 author hit this when writing
`if d_op == TOKEN_PERCENT() && (op_qt == QBE_D() || op_qt == QBE_S())`.
Workaround = nested plain `if` flag dispatch (W-077 v2.11.11 convention).

This script greps codegen.jhyy for the trigger pattern and exits non-zero on hit.
Convention must be 0 hit post-W-058 v2.13.8 ship (workaround already applied).
If a future author reintroduces nested short-circuit, this fails CI immediately.

Note: this only checks codegen.jhyy. Other src0/ files (ir.jhyy, parser.jhyy,
lexer.jhyy, etc.) don't emit QBE IL directly so the trigger pattern doesn't
apply there.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = REPO / "compiler" / "src0" / "codegen.jhyy"
# Pattern: `if <expr>` containing both && and || (in either order).
# Excludes comment-only lines (// prefix after stripping).
PAT = re.compile(r"\bif\b[^\n]*&&[^\n]*\|\|[^\n]*|\bif\b[^\n]*\|\|[^\n]*&&")


def main() -> int:
    if not TARGET.exists():
        print(f"FAIL: {TARGET} not found", file=sys.stderr)
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="replace")
    hits = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue
        if PAT.search(line):
            hits.append((lineno, line.rstrip()))

    if hits:
        print(f"FAIL: {len(hits)} nested-short-circuit if-condition(s) in codegen.jhyy")
        print(f"      (W-082 convention violation — use nested plain `if` flag dispatch)")
        for lineno, line in hits:
            print(f"  codegen.jhyy:{lineno}: {line}")
        return 1

    print(f"PASS: 0 nested-short-circuit if-condition in codegen.jhyy (W-082 convention HOLD)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
