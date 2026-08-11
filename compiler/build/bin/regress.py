#!/usr/bin/env python3
"""Run all integration tests against jhyy.exe (C-side compiler).

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