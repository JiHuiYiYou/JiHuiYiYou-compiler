#!/usr/bin/env python3
"""寄存器分配器的**独立实现对拍门** —— 两套独立写的算法必须给出同一个数。

**为什么需要这道门**(2026-11-03 门审计实测):
`scripts/dev/regalloc_reference.py` 是一份**独立写的** Python 参考实现,
它的存在理由写在它自己的开头:「两套独立写的算法给出同一个数,才说明这个数
是对的;一套实现自己验自己,只能说明它没崩」。

**但它从来没被任何门跑过** ⇒ 它自己烂掉了也没人知道。实测:2026-11-03 第一次
真跑它,两侧对不上 ——

| 数 | 参考实现 | 编译器侧 |
|---|---|---|
| 候选 | 59870 | 59870 ✓ |
| 实际分配到寄存器 | **58495** | **58489** ✗ 差 6 |

⇒ 差的那 6 个正好是**浮点 temp**:`s`/`d` 类型不能进 GPR 寄存器池,而
**参考实现自己漏了「整数类型」这一维**(尽管它的 docstring 写着
「合格候选 = … + 整数类型」)。⇒ **编译器侧是对的,参考实现是错的** ——
这正是「独立实现」本该抓的那类 bug,只不过这次 bug 在参考实现自己身上。

修好之后(参考实现补上类型这一维),两侧**逐项相同**:
候选 59870 · 可分配 59864 · 实际分配 58489 · 池满 1375。

**这道门做什么**:
1. 用当前编译器编出 src0 的 `.il`(`JHY_WRITE_IL=1` —— 自 v4.0.8 起它只是
   「要不要额外落一份 .il」的**纯副作用**,不再切换编译路径,见 W-097);
2. 跑 Python 参考实现算出四个数;
3. 跑编译器(`JHY_RCACHE=1 JHY_RCACHE_STATS=1`)读出它自己报的四个数;
4. **逐项对拍** —— 不一致就红。

⚠️ **编译器侧那一步会以「internal consistency violation」失败** —— 那是
**设计如此**,不是 bug:寄存器分配目前只到 v4.4.0 的**阶段一**(算出每个 temp
住哪个寄存器),**阶段二**(emit 层真的消费寄存器)还没做 ⇒ 分配了寄存器却
仍走槽位路径 ⇒ 守卫**响亮失败**(v4.4.0 plan 的验收条件 #3:
「分配了寄存器但走槽位路径 ⇒ 编译失败」)。
⇒ 本门**不看退出码**,只看**统计数字**;但「统计没打出来」⇒ 红
(那说明连分配阶段都没跑到,数字无从对拍)。

**退出码**:0 = 两侧逐项相同;1 = 不一致(逐条列出)。

**用法**:
    python scripts/dev/check_regalloc_parity.py
    python scripts/dev/check_regalloc_parity.py --il compiler/build/regalloc/main.il
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import regalloc_reference as ref  # noqa: E402

DEFAULT_BIN = ROOT / "compiler" / "build" / "bin" / "jhyy.exe"
SRC = ROOT / "compiler" / "src0" / "main.jhyy"

# 编译器侧打印的统计行:
#   jhyy rcache: candidates = 59870, rejected(block) = 714, ..., ok_pass = 59864, ...
#   jhyy rcache: allocated temps = 58489, functions using callee-saved = 1062
KV_RE = re.compile(r"([a-z_]+(?:\s+[a-z]+)*)\s*=\s*(\d+)")


def parse_compiler_stats(stderr: str) -> dict[str, int]:
    """从编译器 stderr 里抠出统计数字。"""
    out: dict[str, int] = {}
    for line in stderr.splitlines():
        if "jhyy rcache:" not in line:
            continue
        for m in KV_RE.finditer(line):
            key = re.sub(r"\s+", "_", m.group(1))
            out[key] = int(m.group(2))
    return out


def run(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=str(ROOT), env=e)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bin", default=str(DEFAULT_BIN), help="编译器二进制路径")
    ap.add_argument("--il", default=None,
                    help="已有的 .il 路径(不给就现场编一份)")
    ap.add_argument("--keep", action="store_true", help="保留中间产物")
    args = ap.parse_args()

    binary = Path(args.bin)
    if not binary.is_absolute():
        binary = ROOT / binary
    if not binary.is_file():
        print(f"ERR: 编译器不存在: {binary}(先跑 `make`)", file=sys.stderr)
        return 2
    if not SRC.is_file():
        print(f"ERR: 找不到 {SRC}", file=sys.stderr)
        return 2

    workdir = None
    try:
        if args.il:
            il_path = Path(args.il)
            if not il_path.is_absolute():
                il_path = ROOT / il_path
        else:
            workdir = Path(tempfile.mkdtemp(prefix="jhyy-regalloc-"))
            il_path = workdir / "main.il"
            print(f"[check_regalloc_parity] 编 src0 的 .il({il_path})……")
            r = run([str(binary), "build", str(SRC), "-o", str(workdir / "main")],
                    env={"JHY_WRITE_IL": "1"})
            if not il_path.is_file():
                print("ERR: 没产出 .il —— 无法对拍", file=sys.stderr)
                print((r.stdout or "")[-2000:], file=sys.stderr)
                print((r.stderr or "")[-2000:], file=sys.stderr)
                return 1

        # ── 1. Python 参考实现 ────────────────────────────────────────
        print("[check_regalloc_parity] 跑 Python 参考实现……")
        ref_r = ref.analyse(str(il_path))
        print(f"  参考实现: 候选={ref_r['eligible']} 可分配={ref_r['allocable']} "
              f"实际分配={ref_r['allocated']} 池满={ref_r['pool_full']}")

        # ── 2. 编译器侧 ──────────────────────────────────────────────
        print("[check_regalloc_parity] 跑编译器侧统计(JHY_RCACHE=1)……")
        out_dir = workdir if workdir else ROOT / "compiler" / "build" / "regalloc"
        out_dir.mkdir(parents=True, exist_ok=True)
        r = run([str(binary), "build", str(SRC), "-o", str(out_dir / "main_rc")],
                env={"JHY_RCACHE": "1", "JHY_RCACHE_STATS": "1"})
        stats = parse_compiler_stats(r.stderr or "")
        if not stats:
            print("ERR: 编译器没打统计 —— 连分配阶段都没跑到,数字无从对拍", file=sys.stderr)
            print((r.stdout or "")[-2000:], file=sys.stderr)
            print((r.stderr or "")[-2000:], file=sys.stderr)
            return 1
        print(f"  编译器侧: 候选={stats.get('candidates')} "
              f"可分配={stats.get('ok_pass')} "
              f"实际分配={stats.get('allocated_temps')} "
              f"池满={stats.get('skip_nopool')}")
        if r.returncode != 0:
            print("  (编译器这一步**以失败告终** —— 那是 v4.4.0 阶段一的守卫"
                  "「分配了寄存器却走槽位路径 ⇒ 响亮失败」,设计如此)")

        # ── 3. 逐项对拍 ──────────────────────────────────────────────
        pairs = [
            ("候选", ref_r["eligible"], stats.get("candidates")),
            ("其中可分配(整数类型)", ref_r["allocable"], stats.get("ok_pass")),
            ("实际分配到寄存器", ref_r["allocated"], stats.get("allocated_temps")),
            ("池满(退化成栈槽)", ref_r["pool_full"], stats.get("skip_nopool")),
        ]
        bad = [(name, a, b) for name, a, b in pairs if a != b]
        if bad:
            print(f"\n[check_regalloc_parity] FAIL —— {len(bad)} 项对不上:")
            for name, a, b in bad:
                print(f"  x {name}: 参考实现 {a} != 编译器侧 {b}")
            print("\n  两套**独立实现**给出不同的数 ⇒ 至少有一边是错的。")
            print("  先查参考实现(它已经错过一次:漏了「整数类型」这一维),")
            print("  再查编译器侧;**不要**改判据让它们「对上」。")
            return 1
        print("\n[check_regalloc_parity] OK —— 两套独立实现逐项相同。")
        return 0
    finally:
        if workdir and not args.keep:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
