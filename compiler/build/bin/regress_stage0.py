#!/usr/bin/env python3
"""Run all integration tests against jhyy_stage0.exe (C-side stage 0 compiler).

v1.4.5 (2026-08-14): stage 0 bootstrap regression check. Per
`docs/plans/v1/v1.4.0任务清单 + 概要设计.md` § Sprint v1.4.5: 验证改 src/ 后
rebuild stage0 + stage1 链不破坏任何 regress 用例。跟 regress.py (jhyy.exe
jhyy-side production) 平行 — 两跑都需 PASS 才算 CI 守门通过。

注意: stage0 是 C 端 bootstrap, 改了 src/*.c 后必须 `make stage0` 重建。
CI workflow 应先 `make stage0` 再跑本脚本, 否则会用 stale binary。

Shim 模式跟 regress.py / regress_v1.py 一致 — 所有逻辑
(NTSTATUS / EXPECT annotation / stale-cache hardening) 在 mcp-jhyy/jhyy_regress.py。
"""
import sys
from pathlib import Path

# Make mcp-jhyy/ importable
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-jhyy"))

from jhyy_regress import run_all  # noqa: E402

if __name__ == "__main__":
    # enforce_baseline_hash=False: stage0 binary 每次 gcc 链接 sha 都变
    # (gcc 不确定 timestamp / debug info layout), baseline 比对无意义;
    # 守门靠 regress 测试本身通过 + Stage 1 byte-equal (stage0.il == jhyy.il)
    result = run_all(
        binary="compiler/build/bin/jhyy_stage0.exe",
        enforce_baseline_hash=False,
    )
    sys.exit(0 if result["ok"] else 1)
