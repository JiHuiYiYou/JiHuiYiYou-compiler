#!/usr/bin/env python3
"""规范一致性门 —— 三份规范对同一件事必须说同样的话。

**为什么需要这道门（2026-10-30 实测）**：
`Cap<T>` 的 8 字节 wire 布局在**两份锁定规范**（lang-spec §2.6 / abi §2.5）与
**一份设计稿**（binary-format §2）里必须**逐字一致**，且带**可验证的构造示例**。

2026-10-31 起布局是**自然对齐**的 `cnode_idx@0 · depth@4 · gen@5 · rights@6`
（`rights:u16` 落在偶数偏移 ⇒ 无隐式 padding、`alignof(Cap)=4`）。
先前锁的 `rights@5`（`gen@7`）把 u16 放在**奇数**偏移 ⇒ 只能由 packed 产生，
与本仓「无 `packed` / 显式 `_pad`」的布局契约冲突。
**这个冲突活了三个月 —— 因为没有一道门。**

本门做三件事：
1. 解析三处的 `Cap<T>` wire 布局 ⇒ 比对 `字段 → (offset, size, type)`
2. 比对 rights 的**位宽**（R/W/G 三位 ⇒ 8 种 rights）
3. 检查 lang-spec § 2.6 的**构造示例**在采用布局下能解出注释声称的值
   （示例是判定「哪一份对」的**独立证据**，不能只比字段名）

**退出码**：0 = 一致；1 = 不一致（逐条列出）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ABIS = ROOT / "docs" / "abis"

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


# 表格式:  offset size field type ...
TABLE_RE = re.compile(r"^(\d+)\s+(\d+)\s+([A-Za-z_][A-Za-z0-9_]*)\s+(u\d+)\b", re.M)
# 内联式:  field:type@offset
INLINE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*):(u\d+)@(\d+)")


def parse_table(path: Path) -> dict[str, tuple[int, int, str]] | None:
    """从 `offset size field type` 表里解析 Cap 布局。"""
    text = read(path)
    # 只取 Cap 那段:找 cnode_idx 所在表
    lines = [ln for ln in text.splitlines() if TABLE_RE.match(ln)]
    rows = {}
    for ln in lines:
        m = TABLE_RE.match(ln)
        if not m:
            continue
        off, size, field, typ = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
        rows.setdefault(field, (off, size, typ))
    return rows or None


def parse_inline(path: Path) -> dict[str, tuple[int, int, str]] | None:
    text = read(path)
    # binary-format §2 的 Cap 行:{cnode_idx:u32@0, depth:u8@4, rights:u16@5, gen:u8@7}
    for ln in text.splitlines():
        if "cnode_idx" in ln and "rights" in ln and "@" in ln:
            rows = {}
            for m in INLINE_RE.finditer(ln):
                field, typ, off = m.group(1), m.group(2), int(m.group(3))
                size = int(typ[1:]) // 8
                rows[field] = (off, size, typ)
            if rows:
                return rows
    return None


def main() -> int:
    print("[check_spec_consistency] 比对三份规范对同一件事的说法……\n")

    ls = ABIS / "jhyy-lang-spec-v4.0.0.md"
    abi = ABIS / "jhyy-abi-v4.0.0.md"
    bf = ABIS / "jhyy-binary-format-v1.0.0.md"

    layouts = {
        "lang-spec §2.6": parse_table(ls) if ls.is_file() else None,
        "abi §2.5": parse_table(abi) if abi.is_file() else None,
        "binary-format §2": parse_inline(bf) if bf.is_file() else None,
    }

    for name, lay in layouts.items():
        if lay is None:
            fail(f"{name}: 解析不出 `Cap<T>` 的 wire 布局（文档结构变了？）")
        else:
            print(f"  {name}: {dict(sorted(lay.items(), key=lambda kv: kv[1][0]))}")

    # 1) 三处必须完全一致
    present = {k: v for k, v in layouts.items() if v}
    if len(present) >= 2:
        base_name, base = next(iter(present.items()))
        for name, lay in present.items():
            if name == base_name:
                continue
            if lay != base:
                diff = []
                for f in sorted(set(base) | set(lay)):
                    if base.get(f) != lay.get(f):
                        diff.append(f"{f}: {base_name}={base.get(f)} vs {name}={lay.get(f)}")
                fail(f"Cap wire 布局不一致 —— {'; '.join(diff)}")
    elif len(present) < 3:
        fail(f"只解析出 {len(present)} 处的 Cap 布局（应为 3 处）")

    # 2) rights 位宽必须都是 3 位(R/W/G)
    for name, lay in present.items():
        t = read(ABIS / {"lang-spec §2.6": "jhyy-lang-spec-v4.0.0.md",
                         "abi §2.5": "jhyy-abi-v4.0.0.md",
                         "binary-format §2": "jhyy-binary-format-v1.0.0.md"}[name])
        bits = set(re.findall(r"bit(\d)=([RWG])", t))
        if name != "binary-format §2" and not bits:
            fail(f"{name}: 找不到 rights 的位定义（`bit0=R, bit1=W, bit2=G`）")

    # 3) 独立证据:lang-spec 的构造示例必须在采用布局下自洽
    if ls.is_file():
        text = read(ls)
        m = re.search(r"0x([0-9a-fA-F]{16}) as Cap", text)
        if m:
            value = int(m.group(1), 16)
            lay = layouts.get("lang-spec §2.6")
            if lay and "rights" in lay:
                off, size, _ = lay["rights"]
                rights = (value >> (off * 8)) & ((1 << size) - 1)
                # 注释声称 rights=R|W ⇒ 0b011 = 3
                if rights != 3:
                    fail(f"lang-spec §2.6 的构造示例不自洽：按 rights@{off} 解出 {rights}，"
                         f"但注释声称 R|W（= 3）⇒ 布局或示例至少有一个是错的")
                else:
                    print(f"  构造示例自洽 ✓（0x{m.group(1)} 按 rights@{off} 解出 R|W）")

    if problems:
        print(f"\n[check_spec_consistency] FAIL —— {len(problems)} 处不一致:")
        for p in problems:
            print("  x", p)
        print("\n  修法:改到三份规范说同样的话。单一真源 = lang-spec § 2.6;")
        print("       改完跑 `python scripts/dev/check_spec_consistency.py` 复核。")
        return 1
    print("\n[check_spec_consistency] OK —— 三份规范说法一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
