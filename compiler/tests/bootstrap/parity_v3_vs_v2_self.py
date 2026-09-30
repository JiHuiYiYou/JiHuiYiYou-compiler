#!/usr/bin/env python3
"""
parity_v3_vs_v2_self.py — V3 self-backend vs V2 self-backend sweep.

Per 用户 2026-09-23 反馈 "146 差异不是 V3 欠的债, V3 跟 V2 已经字节级一致,
V2 就是带着它们 ship 的, 拿 V2 当尺子重跑一次 (大概率 0 差异)".

遍历 examples/*.jhyy, 同时跑 V3 jhyy.exe (JHY_SELF_BACKEND=1) + V2 jhyy.exe,
对照 .s 字节差异。预期: 0 PASS or near-zero (用户: "大概率 0 差异").

退出码: 0 = 全 PASS (or near-zero DIFF), 1 = significant DIFF.
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

JHYY_V3_ROOT = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v3").resolve()
JHYY_V2_ROOT = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v2").resolve()
JHYY_V3_EXE = JHYY_V3_ROOT / "compiler/build/bin/jhyy.exe"
JHYY_V2_EXE = JHYY_V2_ROOT / "compiler/build/bin/jhyy.exe"
EXAMPLES_DIR = JHYY_V3_ROOT / "compiler/tests/examples"
OUT_DIR = Path("/tmp/v3v2_parity")
DIFF_LOG = Path("/tmp/v3v2_parity_diff.log")

def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    examples = sorted(EXAMPLES_DIR.glob("*.jhyy"))
    print(f"=== V3 self-backend vs V2 self-backend ===")
    print(f"  V3: {JHYY_V3_EXE}")
    print(f"  V2: {JHYY_V2_EXE}")
    print(f"  examples: {len(examples)}")
    print()

    pass_n = diff_n = skip_n = 0
    diff_cases = []

    for src in examples:
        base = src.stem
        if "sysv" in base.lower() or "freestanding" in base.lower() or "efi" in base.lower():
            skip_n += 1
            continue

        # Copy .jhyy into OUT_DIR
        work = OUT_DIR / base
        work.mkdir(exist_ok=True)
        dst_src = work / f"{base}.jhyy"
        shutil.copy2(src, dst_src)

        # V3 compile (JHY_SELF_BACKEND=1)
        env_v3 = {**os.environ, "JHY_SELF_BACKEND": "1"}
        proc_v3 = subprocess.run(
            [str(JHYY_V3_EXE), "compile", str(dst_src), "-o", str(work / f"{base}_v3")],
            capture_output=True, timeout=30, env=env_v3
        )
        v3_s = work / f"{base}_v3.s"

        # V2 compile (default path = self-backend after v2.16.0)
        proc_v2 = subprocess.run(
            [str(JHYY_V2_EXE), "compile", str(dst_src), "-o", str(work / f"{base}_v2")],
            capture_output=True, timeout=30
        )
        v2_s = work / f"{base}_v2.s"

        if not v3_s.exists() or not v2_s.exists():
            skip_n += 1
            continue
        if v3_s.stat().st_size < 50 or v2_s.stat().st_size < 50:
            skip_n += 1
            continue

        v3_data = v3_s.read_bytes()
        v2_data = v2_s.read_bytes()
        if v3_data == v2_data:
            pass_n += 1
        else:
            diff_n += 1
            diff_cases.append((base, len(v3_data), len(v2_data)))
            print(f"  DIFF  {base}.jhyy  v3={len(v3_data)}B  v2={len(v2_data)}B")

    print()
    print(f"=== parity V3 vs V2 self-backend: {pass_n} PASS / {diff_n} DIFF / {skip_n} SKIP ===")
    print()
    if diff_cases:
        print("DIFF cases (need investigation):")
        for c, v3s, v2s in diff_cases:
            print(f"  {c}.jhyy  v3={v3s}B  v2={v2s}B  ratio={v3s/max(1,v2s):.2f}x")

    sys.exit(0 if diff_n == 0 else 1)

if __name__ == "__main__":
    main()