#!/usr/bin/env python3
"""v2.13.5 workarounds.md: insert explicit <a id="w-NNN"> anchors before H2 headings.

This complements rebuild_index.py which uses #w-NNN short anchors.
Without explicit tags, GitHub auto-anchor = full title slug (~200 chars for W-074.x).

2026-10-27 (W-153) 改成**幂等**:原来这个脚本对每个 H2 无条件插一个锚点 ⇒
在已经有锚点的文件上再跑一遍 ⇒ **给已有的锚点插重复的** ⇒ HTML 里出现两个
同名 id ⇒ 浏览器跳转到第一个(旧的那个)⇒ 看起来「插了没用」。
⇒ 现在:已经紧邻着同 id 锚点的 H2 **跳过**;重复跑 N 次结果都一样。

用法:
    python scripts/dev/v2_13_5_insert_anchors.py <input.md> <output.md>
    python scripts/dev/v2_13_5_insert_anchors.py --check <file.md>
        # 只检查不写:报缺失 / 重复的锚点,退出码 1 = 有问题
"""
import re
import sys
from pathlib import Path

# ⚠ 口径必须与 rebuild_index.py 一致(那边是 `#{2,3}`):H3 的子条目
#   (W-073..W-079 / W-074.6 等)也会进索引 ⇒ 没锚点就是死链。
H2_RE = re.compile(r'^#{2,3}\s+(W-\d+(?:\.\d+)*)\s*[:：]\s*(.+?)\s*$')
ANCHOR_RE = re.compile(r'^<a id="(w-[0-9.]+)"></a>\s*$')


def collect(lines):
    """返回 (已存在的锚点 id 集合, 缺失锚点的 H2 列表, 重复的锚点列表)"""
    have = set()
    dup = []
    missing = []
    for i, line in enumerate(lines):
        m_anchor = ANCHOR_RE.match(line.rstrip('\n'))
        if m_anchor:
            aid = m_anchor.group(1)
            if aid in have:
                dup.append((i + 1, aid))
            have.add(aid)
            continue
        m_h2 = H2_RE.match(line)
        if m_h2:
            aid = m_h2.group(1).lower()
            # 往前找最近的非空行:若已是同 id 的锚点 ⇒ 已有 ⇒ 跳过
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            prev_is_anchor = j >= 0 and ANCHOR_RE.match(lines[j].rstrip('\n')) \
                and ANCHOR_RE.match(lines[j].rstrip('\n')).group(1) == aid
            if not prev_is_anchor:
                missing.append((i + 1, aid))
    return have, missing, dup


def insert_anchors(input_path: Path, output_path: Path) -> None:
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()

    out_lines = []
    inserted = 0
    skipped = 0
    for i, line in enumerate(lines):
        m = H2_RE.match(line)
        if m:
            h2_id = m.group(1).lower()
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                j -= 1
            prev_is_anchor = j >= 0 and ANCHOR_RE.match(lines[j].rstrip('\n')) \
                and ANCHOR_RE.match(lines[j].rstrip('\n')).group(1) == h2_id
            if not prev_is_anchor:
                out_lines.append(f'<a id="{h2_id}"></a>\n')
                inserted += 1
            else:
                skipped += 1
        out_lines.append(line)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(out_lines)
    print(f'Inserted {inserted} anchor tags (skipped {skipped} already-anchored)')


def check(input_path: Path) -> int:
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()
    have, missing, dup = collect(lines)
    print(f'anchors present : {len(have)}')
    print(f'missing (H2 无锚点): {len(missing)}')
    for ln, aid in missing[:20]:
        print(f'   line {ln}: {aid}')
    print(f'duplicated      : {len(dup)}')
    for ln, aid in dup[:20]:
        print(f'   line {ln}: {aid}')
    return 1 if (missing or dup) else 0


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--check':
        sys.exit(check(Path(sys.argv[2])))
    if len(sys.argv) != 3:
        print('Usage: v2_13_5_insert_anchors.py <input.md> <output.md>')
        print('       v2_13_5_insert_anchors.py --check <file.md>')
        sys.exit(1)
    insert_anchors(Path(sys.argv[1]), Path(sys.argv[2]))
