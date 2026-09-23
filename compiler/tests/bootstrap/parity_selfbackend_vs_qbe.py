#!/usr/bin/env python3
"""
parity_selfbackend_vs_qbe.py — Pre-Ph.5a full self-backend vs QBE parity sweep.

Per 用户 2026-09-23 反馈 "Ph.5a qbe/ git rm 是单向门, 删之前必须证明 self-backend
能扛住全量": 遍历所有 examples/*.jhyy, 同时跑 JHY_SELF_BACKEND=1 self path +
. 默认 QBE path, 对照 .s 字节差异。

输出:
  - PASS: 字节一致 (strict byte-equal)
  - DIFF: .s 字节差异 (打印 diff 头部 + 行数)
  - FAIL: self/QBE 某一边失败 (link fail / 0-byte .s / other)
  - SKIP: 例外 (sysv_abi 等跨平台)

退出码:
  0 = 全部 PASS
  1 = 有 DIFF/FAIL (清单 → v3.0.9 scope)
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

JHYY_ROOT = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v3").resolve()
JHYY_EXE = JHYY_ROOT / "compiler/build/bin/jhyy.exe"
EXAMPLES_DIR = JHYY_ROOT / "compiler/tests/examples"
SELF_OUT_DIR = Path("/tmp/self_v307")
QBE_OUT_DIR = Path("/tmp/qbe_v307")
DIFF_LOG = Path("/tmp/parity_v307_diff.log")

def compile_one(jhyy_args, out_dir, base_name):
    """Compile single .jhyy; return (success, s_file_path)"""
    src = EXAMPLES_DIR / f"{base_name}.jhyy"
    if not src.exists():
        return False, None
    work_dir = out_dir / base_name
    work_dir.mkdir(parents=True, exist_ok=True)
    # Copy .jhyy into work_dir (jhyy writes output next to source)
    dst_src = work_dir / f"{base_name}.jhyy"
    try:
        shutil.copy2(src, dst_src)
    except Exception:
        pass
    # Run jhyy compile --target=amd64_win <file>
    proc = subprocess.run(
        jhyy_args + ["compile", "--target=amd64_win", f"{base_name}.jhyy"],
        cwd=str(work_dir),
        capture_output=True,
        timeout=30,
    )
    s_file = work_dir / f"{base_name}.s"
    if proc.returncode != 0 or not s_file.exists() or s_file.stat().st_size < 50:
        return False, s_file
    return True, s_file

def main():
    if SELF_OUT_DIR.exists():
        shutil.rmtree(SELF_OUT_DIR)
    if QBE_OUT_DIR.exists():
        shutil.rmtree(QBE_OUT_DIR)
    SELF_OUT_DIR.mkdir(parents=True, exist_ok=True)
    QBE_OUT_DIR.mkdir(parents=True, exist_ok=True)

    jhyy = str(JHYY_EXE)
    examples = sorted(EXAMPLES_DIR.glob("*.jhyy"))
    print(f"=== parity_selfbackend_vs_qbe (Pre-Ph.5a sweep) ===")
    print(f"  JHYY_EXE={jhyy}")
    print(f"  examples={len(examples)}")
    print()

    pass_n = diff_n = fail_n = skip_n = 0
    diff_cases = []

    for src in examples:
        base = src.stem
        # Skip sysv_abi etc (cross-platform, expect fail on Win)
        if "sysv" in base.lower() or "freestanding" in base.lower() or "efi" in base.lower():
            skip_n += 1
            continue

        # Copy .jhyy into both output dirs (jhyy writes output next to source)
        for d in (SELF_OUT_DIR, QBE_OUT_DIR):
            shutil.copy2(src, d / f"{base}.jhyy")

        # 1. JHY_SELF_BACKEND=1 path
        env_self = {**os.environ, "JHY_SELF_BACKEND": "1"}
        proc_self = subprocess.run(
            [jhyy, "compile", "--target=amd64_win", f"{base}.jhyy"],
            cwd=str(SELF_OUT_DIR),
            capture_output=True,
            timeout=30,
            env=env_self,
        )
        self_s = SELF_OUT_DIR / f"{base}.s"
        self_ok = proc_self.returncode == 0 and self_s.exists() and self_s.stat().st_size >= 50

        # 2. default (QBE) path
        proc_qbe = subprocess.run(
            [jhyy, "compile", "--target=amd64_win", f"{base}.jhyy"],
            cwd=str(QBE_OUT_DIR),
            capture_output=True,
            timeout=30,
        )
        qbe_s = QBE_OUT_DIR / f"{base}.s"
        qbe_ok = proc_qbe.returncode == 0 and qbe_s.exists() and qbe_s.stat().st_size >= 50

        if not self_ok or not qbe_ok:
            fail_n += 1
            print(f"  FAIL  {base}.jhyy  self={'OK' if self_ok else 'FAIL'}  qbe={'OK' if qbe_ok else 'FAIL'}")
            continue

        # Byte-equal compare
        self_data = self_s.read_bytes()
        qbe_data = qbe_s.read_bytes()
        if self_data == qbe_data:
            pass_n += 1
        else:
            diff_n += 1
            diff_cases.append(base)
            print(f"  DIFF  {base}.jhyy  self={len(self_data)}B  qbe={len(qbe_data)}B")

    print()
    print(f"=== parity summary: {pass_n} PASS / {diff_n} DIFF / {fail_n} FAIL / {skip_n} SKIP ===")
    print()
    if diff_cases:
        print("DIFF cases (v3.0.9 scope candidates):")
        for c in diff_cases:
            print(f"  {c}")
    elif fail_n == 0:
        print("清单空 → 直接 Ph.5a, 删 QBE, 往前冲")
    else:
        print("FAIL cases (需要调查):")
        # FAIL details printed above

    sys.exit(0 if diff_n == 0 and fail_n == 0 else 1)

if __name__ == "__main__":
    main()