#!/usr/bin/env python3
"""`.jhyynb` 布局算术门 —— 让 binary-format 规范里的每个 struct 都「可算」。

**为什么需要这道门**（2026-10-31 审计实测）：
`docs/abis/jhyy-binary-format-v1.0.0.md` 是**锁定的**格式规范，但它里每个 struct 的
尺寸是**手写**的，不是算出来的 ⇒ 人算错时没人知道。实测抓到三处真错：

| struct | 文档写 | 实际 | 错在哪 |
|---|---|---|---|
| `JhynbHeader` | 112B | **120B** | `_pad0: u16` 结束于 offset 12，而下一个 `entry_point: u64` 要 8 对齐 ⇒ offset 12 有 **4B 隐式 padding**（而本文档自己的规矩是「padding 显式写成 `_pad*` 字段」） |
| Debug Group Header | 16B | **12B** | 四个字段加起来就 12B |
| `header_crc` 的注释 | `CRC32(header[0..104])` | `header[0..108]` | crc 字段实际在 offset 108 |

⇒ 规范照着实现的人会**二进制错位**，而 CI 全绿。

**这道门验什么**：
1. 每个 `struct` 的**声明尺寸** == 按**自然对齐**算出来的尺寸
2. **没有隐式 padding** —— 每一个对齐间隙都必须是显式的 `_pad*` 字段
3. §4 的 header 与 §12 的 Debug Group Header 同上

**退出码**：0 = 全绿；1 = 有算术错（逐条列出）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "abis" / "jhyy-binary-format-v1.0.0.md"

# 类型 -> (size, align)
SZ = {
    "u8": (1, 1), "i8": (1, 1),
    "u16": (2, 2), "i16": (2, 2),
    "u32": (4, 4), "i32": (4, 4),
    "u64": (8, 8), "i64": (8, 8),
    "[4]u8": (4, 1), "[8]u8": (8, 1),
}

# C struct 里的字段行：`    name: type[ = 值(可含逗号)],  // 注释`
# ⚠️ 值里可能含逗号（`magic: [4]u8 = 'J','B','E','\x01',`）⇒ 值部分必须贪婪。
FIELD_C = re.compile(r"^\s{4}(\w+)\s*:\s*([A-Za-z0-9_\[\]]+)\s*(?:=\s*.*)?,\s*(?://.*)?$")
# 框图里的字段行：`│  - name: type ... │`
FIELD_BOX = re.compile(r"-\s+(\w+)\s*:\s*([A-Za-z0-9_\[\]]+)")
# 变长字段：`[]u8` / `[]u16` —— 尺寸取决于 N ⇒ 整个 struct 的 sizeof 是变的
VARLEN = re.compile(r"^\[\]\w+$")


def layout(fields: list[tuple[str, str]]) -> tuple[int | None, int, list[tuple[int, int, str]]]:
    """按自然对齐算布局 ⇒ (总大小 or None(变长), 结构体 alignof, [(隐式 padding offset, 大小, 后面那个字段)])"""
    off = 0
    maxal = 1
    implicit: list[tuple[int, int, str]] = []
    variable = False
    for name, ty in fields:
        if VARLEN.match(ty):
            variable = True       # 变长字段 ⇒ 之后没有固定尺寸可言
            continue
        size, align = SZ[ty]
        if off % align:
            pad = align - (off % align)
            implicit.append((off, pad, name))
            off += pad
        if align > maxal:
            maxal = align
        off += size
    total = None if variable else (off + maxal - 1) // maxal * maxal
    return total, maxal, implicit


def parse_c_fields(block: str) -> list[tuple[str, str]]:
    out = []
    for line in block.splitlines():
        m = FIELD_C.match(line)
        if m and (m.group(2) in SZ or VARLEN.match(m.group(2))):
            out.append((m.group(1), m.group(2)))
    return out


def main() -> int:
    if not DOC.is_file():
        print(f"[bf_layout] 找不到 {DOC}")
        return 1
    text = DOC.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []

    # ---- 1. 每个 `struct X { ... }` ----------------------------------------
    for m in re.finditer(r"struct (\w+) \{(.*?)\n\}", text, re.S):
        name, block = m.group(1), m.group(2)
        fields = parse_c_fields(block)
        if not fields:
            continue
        total, maxal, implicit = layout(fields)
        # 尺寸断言写在 struct 块的**外面**（紧跟其后的 `// 总 NB, sizeof = NB, alignof = N`）
        tail = text[m.end():m.end() + 400]
        cm = re.search(r"//\s*总\s*(\d+)B,\s*sizeof\s*=\s*(\d+),\s*alignof\s*=\s*(\d+)", tail)
        if total is None:
            # 变长 struct：尺寸随 N 变化 ⇒ 不能拿固定值比，但必须写明「变长」+ 固定部分尺寸
            if not re.search(r"//\s*变长", tail):
                problems.append(
                    f"{name}: 变长 struct（末尾是 `[]T`）需在块后写明 `// 变长：…`"
                    f"（尺寸随 N 变化，不能声明固定 sizeof）")
            else:
                mf = re.search(r"固定部分\s*(\d+)B", tail)
                if not mf:
                    problems.append(
                        f"{name}: 变长 struct 需在 `// 变长：…` 里写明「固定部分 NB」"
                        f"（变长字段的起始偏移）")
                else:
                    # 固定部分 = 变长字段之前的偏移
                    off = 0
                    for fn, ft in fields:
                        if VARLEN.match(ft):
                            break
                        size, align = SZ[ft]
                        if off % align:
                            off += align - (off % align)
                        off += size
                    if int(mf.group(1)) != off:
                        problems.append(
                            f"{name}: 文档写「固定部分 {mf.group(1)}B」，实际变长字段从 offset {off} 开始")
            for off, pad, nxt in implicit:
                problems.append(
                    f"{name}: offset {off} 处有 {pad}B 隐式 padding（在 {nxt} 之前）")
            continue
        if not cm:
            problems.append(f"{name}: 块后没有 `// 总 NB, sizeof = NB, alignof = N` 的尺寸断言")
            continue
        claim = int(cm.group(2))
        if claim != total:
            problems.append(
                f"{name}: 文档写 sizeof={claim}，按自然对齐算是 {total}（差 {total - claim:+d}B）")
        if int(cm.group(3)) != maxal:
            problems.append(
                f"{name}: 文档写 alignof={cm.group(3)}，按自然对齐算是 {maxal}"
                f"（= 最大字段对齐）")
        for off, pad, nxt in implicit:
            problems.append(
                f"{name}: offset {off} 处有 {pad}B **隐式 padding**（在 {nxt} 之前）—— "
                f"规范要求 padding 显式写成 `_pad*` 字段")

    # ---- 2. §4 的 header -------------------------------------------------
    m4 = re.search(r"##\s*4\.\s*Header\((\d+)B,\s*(\d+)-aligned\).*?```c\n(.*?)\n```", text, re.S)
    if not m4:
        problems.append("§4 Header：找不到 `## 4. Header(NB, N-aligned)` + 代码块")
    else:
        claim = int(m4.group(1))
        fields = parse_c_fields(m4.group(3))
        total, maxal, implicit = layout(fields)
        if claim != total:
            problems.append(
                f"§4 Header: 文档写 {claim}B，按自然对齐算是 {total}B（差 {total - claim:+d}B）")
        for off, pad, nxt in implicit:
            problems.append(
                f"§4 Header: offset {off} 处有 {pad}B **隐式 padding**（在 {nxt} 之前）")
        # header_crc 的注释覆盖范围
        mc = re.search(r"header_crc:\s*u32,\s*//\s*CRC32\(header\[0\.\.(\d+)\]\)", m4.group(3))
        if mc:
            off = 0
            for name, ty in fields:
                size, align = SZ[ty]
                if off % align:
                    off += align - (off % align)
                if name == "header_crc":
                    break
                off += size
            if int(mc.group(1)) != off:
                problems.append(
                    f"§4 Header: header_crc 的注释说 CRC 覆盖 header[0..{mc.group(1)}]，"
                    f"但该字段实际在 offset {off}")

    # ---- 3. §12 的 Debug Group Header（框图形式）--------------------------
    m12 = re.search(r"##\s*12\..*?Debug Group Header \((\d+)B\)(.*?)```", text, re.S)
    if not m12:
        problems.append("§12 Debug Group：找不到 `Debug Group Header (NB)` 框图")
    else:
        claim = int(m12.group(1))
        box = m12.group(2)
        fields = []
        for line in box.splitlines():
            mm = FIELD_BOX.search(line)
            if mm and mm.group(2) in SZ:
                fields.append((mm.group(1), mm.group(2)))
        if not fields:
            problems.append("§12 Debug Group：框图里没解析出字段")
        else:
            total, maxal, implicit = layout(fields)
            if claim != total:
                problems.append(
                    f"§12 Debug Group Header: 文档写 {claim}B，字段加起来是 {total}B")
            for off, pad, nxt in implicit:
                problems.append(
                    f"§12 Debug Group Header: offset {off} 处有 {pad}B 隐式 padding")

    print("[bf_layout] 校验 .jhyynb 规范里每个 struct 的尺寸算术……\n")
    if problems:
        print(f"[bf_layout] FAIL —— {len(problems)} 处算术错:")
        for p in problems:
            print("  x", p)
        print("\n  修法:按自然对齐重算尺寸，并把隐式 padding 写成显式 `_pad*` 字段；")
        print("       尺寸断言写在 struct 块的 `// 总 NB, sizeof = NB, alignof = N` 行上。")
        return 1
    print("[bf_layout] OK —— 每个 struct 的声明尺寸都等于自然对齐算出来的尺寸，无隐式 padding。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
