#!/usr/bin/env python3
"""v2.13.5 workarounds.md: insert explicit <a id="w-NNN"> anchors before H2 headings.

This complements rebuild_index.py which uses #w-NNN short anchors.
Without explicit tags, GitHub auto-anchor = full title slug (~200 chars for W-074.x).
"""
import re
import sys
from pathlib import Path

H2_RE = re.compile(r'^##\s+(W-\d+(?:\.\d+)*)\s*[:：]\s*(.+?)\s*$')


def insert_anchors(input_path: Path, output_path: Path) -> None:
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()

    out_lines = []
    inserted = 0
    for line in lines:
        m = H2_RE.match(line)
        if m:
            h2_id = m.group(1).lower()  # w-074.6 etc
            anchor_tag = f'<a id="{h2_id}"></a>\n'
            # Insert anchor tag BEFORE the H2 line
            out_lines.append(anchor_tag)
            inserted += 1
        out_lines.append(line)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(out_lines)
    print(f'Inserted {inserted} anchor tags')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: v2_13_5_insert_anchors.py <input.md> <output.md>')
        sys.exit(1)
    insert_anchors(Path(sys.argv[1]), Path(sys.argv[2]))