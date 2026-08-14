#!/usr/bin/env python3
"""Run all integration tests against jhyy.exe (jhyy-side production compiler).

v1.4.4 (2026-08-14): `jhyy.exe` 物理替换为 jhyy-side 自举编译产物 (was C-side
sha `c9cff76...`, post jhyy-side sha `37ffc49c...`). regress.py 默认 binary
跟着翻 — 现在跑的是真生产路径,不是 C 端 bootstrap。

v1.4.5 (2026-08-14): regress.py 保持默认 `jhyy.exe` (production), stage 0
验证分离到 regress_stage0.py 平行跑 (C 端 byte-equal 守门)。

Sprint mcp-1 (2026-08-11): shim that delegates to mcp-jhyy/jhyy_regress.py.
All logic (NTSTATUS detection, EXPECT annotation, stale-cache hardening) lives there.
"""
import sys
from pathlib import Path

# Make mcp-jhyy/ importable
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-jhyy"))

from jhyy_regress import run_all  # noqa: E402

if __name__ == "__main__":
    result = run_all(binary="compiler/build/bin/jhyy.exe")
    sys.exit(0 if result["ok"] else 1)