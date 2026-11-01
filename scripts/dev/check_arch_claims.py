#!/usr/bin/env python3
"""架构文档的结构性断言门 —— 盯 `docs/internal/architecture.md` 里的**结构性事实**。

**为什么需要这道门**（2026-11-01 审计实测）：
`architecture.md` 满是可以**当场证伪**的断言（模块清单、NodeKind 个数、
「`regalloc_init` 被注释掉」、「rcache 默认关」、「peephole 4096 字节上限」…），
但**没有任何门盯着它** ⇒ 源码一改，文档就悄悄过期。

实测抓到 13 条过期行数（其中 `parser.jhyy` / `sema.jhyy` 的漂移是**文档自己那轮
match bug 修复加的行**）⇒ 行数已从文档里去掉（会变的数字不进设计文档），
本门改盯**不会每改一次源码就漂**的结构性事实。

**退出码**:0 = 全绿;1 = 有漂移(逐条列出)。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "compiler" / "src0"
ARCH = ROOT / "docs" / "internal" / "architecture.md"

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    print("[check_arch_claims] 核对 architecture.md 的结构性断言……\n")
    if not ARCH.is_file() or not SRC.is_dir():
        print("  (源或文档不存在，跳过)")
        return 0

    doc = read(ARCH)

    # ── 1. 模块清单双向一致 ────────────────────────────────────────────────
    listed = set(re.findall(r"^\|\s*`([\w./]+\.jhyy)`\s*\|", doc, re.M))
    listed = {n for n in listed if n != "std/*.jhyy"}
    actual_top = {p.name for p in SRC.glob("*.jhyy")}
    actual_std = {p.name for p in (SRC / "std").glob("*.jhyy")} if (SRC / "std").is_dir() else set()
    actual = actual_top | actual_std

    for name in sorted(actual_top - listed):
        fail(f"architecture.md 的源文件清单里没有 `compiler/src0/{name}` —— 新增模块忘登记")
    for name in sorted(listed - actual):
        fail(f"architecture.md 列了 `{name}`，但 `compiler/src0/` 里没有这个文件")

    # ── 2. 模块个数 ───────────────────────────────────────────────────────
    m = re.search(r"\*\*(\d+) 个顶层模块 \+ (\d+) 个 std 模块\*\*", doc)
    if not m:
        fail("architecture.md 头部找不到「N 个顶层模块 + N 个 std 模块」的规模声明")
    else:
        n_top, n_std = int(m.group(1)), int(m.group(2))
        if n_top != len(actual_top):
            fail(f"architecture.md 写「{n_top} 个顶层模块」，实际 {len(actual_top)} 个")
        if n_std != len(actual_std):
            fail(f"architecture.md 写「{n_std} 个 std 模块」，实际 {len(actual_std)} 个")

    # ── 3. std 模块名清单 ─────────────────────────────────────────────────
    m = re.search(r"`std/\*\.jhyy`\s*\|[^|]*?([a-z_ ]+)\s*\|", doc)
    if not m:
        fail("architecture.md 找不到 `std/*.jhyy` 那一行的模块名清单")
    else:
        names = {n.strip() for n in m.group(1).replace("`", " ").split() if n.strip()}
        names = {n for n in names if n.endswith(".jhyy")}
        if names:
            want = {n[:-5] for n in actual_std}
            if names != want:
                fail(f"architecture.md 的 std 模块清单 {sorted(names)} ≠ 实际 {sorted(want)}")

    # ── 4. NodeKind 个数 ─────────────────────────────────────────────────
    m = re.search(r"共 \*\*(\d+) 种 `NodeKind`\*\*（`(\d+)\.\.(\d+)`）", doc)
    ast = read(SRC / "ast.jhyy")
    nums = sorted(int(x) for x in
                  re.findall(r"\bNODE_[A-Z0-9_]+\s*\(\)\s*->\s*i32\s*\{\s*return\s+(\d+)", ast))
    if not m:
        fail("architecture.md 找不到「共 N 种 `NodeKind`」的声明")
    elif nums:
        want_n, lo, hi = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if len(nums) != want_n:
            fail(f"architecture.md 写「{want_n} 种 NodeKind」，ast.jhyy 里实际 {len(nums)} 种")
        if (min(nums), max(nums)) != (lo, hi):
            fail(f"architecture.md 写 NodeKind 编号区间 `{lo}..{hi}`，实际 `{min(nums)}..{max(nums)}`")
        holes = set(range(min(nums), max(nums) + 1)) - set(nums)
        if holes:
            fail(f"NodeKind 编号区间有洞：{sorted(holes)}")

    # ── 5. KIND_ 清单双向一致 ─────────────────────────────────────────────
    doc_kinds = set(re.findall(r"^(KIND_[A-Z_]+)\s", doc, re.M))
    real_kinds = set(re.findall(r"\b(KIND_[A-Z_]+)\b", read(SRC / "types.jhyy")))
    real_kinds = {k for k in real_kinds if k != "KIND_UNRESOLVED" or True}
    for k in sorted(real_kinds - doc_kinds):
        fail(f"architecture.md 的 KIND_ 清单里没有 `{k}`（types.jhyy 里有）")
    for k in sorted(doc_kinds - real_kinds):
        fail(f"architecture.md 列了 `{k}`，但 types.jhyy 里没有")

    # ── 6. 「已实现但未接」—— regalloc_init / regalloc_run 必须仍被注释 ────
    cg = read(SRC / "codegen_amd64.jhyy").splitlines()
    for fn in ("regalloc_init", "regalloc_run"):
        hits = [(i, l) for i, l in enumerate(cg, 1) if fn in l]
        if not hits:
            fail(f"codegen_amd64.jhyy 里找不到 `{fn}` —— architecture.md 说它「被注释掉」，"
                 f"但现在连提及都没有了")
            continue
        live = [(i, l) for i, l in hits if not l.lstrip().startswith("//")]
        if live:
            fail(f"codegen_amd64.jhyy:{live[0][0]} `{fn}` **不再是注释** —— "
                 f"architecture.md 说 XMM 分配器「已实现但未接」")

    # ── 7. rcache 默认关（靠环境变量开）──────────────────────────────────
    rc = read(SRC / "codegen_amd64_rcache.jhyy")
    if "JHY_RCACHE" not in rc:
        fail("codegen_amd64_rcache.jhyy 里找不到 `JHY_RCACHE` 开关 —— "
             "architecture.md 说它「默认关，靠环境变量开」")

    # ── 8. peephole 的 4096 字节上限仍在 ─────────────────────────────────
    peep = read(SRC / "codegen_amd64_peephole.jhyy")
    if "4096" not in peep:
        fail("codegen_amd64_peephole.jhyy 里找不到 4096 —— architecture.md 说"
             "「4096 字节上限是已知限制」")
    if "65536" not in peep:
        fail("codegen_amd64_peephole.jhyy 里找不到 65536（max_lines 上限）—— "
             "architecture.md 提到它时按「行数上限」区分")

    # ── 9. 「C 端已于 v4.0.21 删除」 ──────────────────────────────────────
    if (ROOT / "compiler" / "src").exists():
        fail("`compiler/src/` 又出现了 —— architecture.md 说它已于 v4.0.21 删除")

    # ── 10. 对拍工具存在？ ───────────────────────────────────────────────
    if not (ROOT / "scripts" / "dev" / "regalloc_reference.py").is_file():
        fail("architecture.md 提到 `scripts/dev/regalloc_reference.py`，但文件不存在")

    if problems:
        print(f"[check_arch_claims] FAIL —— {len(problems)} 处漂移:")
        for p in problems:
            print("  x", p)
        return 1
    print("[check_arch_claims] OK —— 架构文档的结构性断言与源码一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
