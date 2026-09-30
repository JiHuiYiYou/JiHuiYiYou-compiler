#!/usr/bin/env python3
"""
v2.13.5 workarounds.md index table rebuild (v2).

For each H2 entry (## W-NNN: ...) with a **状态:** line, build row:
| [W-NNN](#anchor) | STATUS | caption |

Caption = H2 title minus W-NNN: prefix, max 80 chars.

Usage: python v2_13_5_rebuild_index.py <input.md> <output.md>
"""
import re
import sys
from pathlib import Path

# Match real W-NNN entries with required colon-or-Chinese-colon separator.
# Sub-section markers like "## W-001 RESOLVED — v0.8 ..." are excluded (no colon).
H2_RE = re.compile(r'^##\s+(W-\d+(?:\.\d+)*)\s*[:：]\s*(.+?)\s*$')
STATUS_RE = re.compile(r'^\*\*(?:状态|Status):\*\*\s+(ACTIVE|RESOLVED|SUPERSEDED|DEFERRED|INVALID)')

# Anchor punctuation to remove (per GitHub markdown auto-anchor rules)
ANCHOR_DROP = re.compile(r'[‘’“"＀`~!@#$%^&*+=,.;:?/\\|<>(){}\[\]]')


def make_anchor(h2_id: str, title: str) -> str:
    """Use short anchor format: 'w-NNN' (matches explicit <a id> tags in file).

    GitHub auto-anchor from full H2 title would be ~200 chars for W-074.x entries.
    V.2 gate target ≤120 char/row requires short anchor. Per W-074.x renumbering,
    we insert explicit `<a id="w-NNN"></a>` tags before each H2 heading, so links
    use short form #w-NNN (or #w-NNN-M for sub-entries).
    """
    return h2_id.lower()


# Per plan § Schema: caption ≤ 120 chars, no emoji, no commit hash inline.
# We strip emoji glyphs from the derived caption (H2 title).
EMOJI_RANGE = re.compile(
    r'[\U0001F300-\U0001FAFF'
    r'\U00002600-\U000027BF'
    r'\U0001F000-\U0001F9FF'
    r'✅✨✳✴❄❇'
    r'✊✋✌✏✒✔✖'
    r']+'
)


def strip_emoji(s: str) -> str:
    return EMOJI_RANGE.sub('', s)


def truncate_caption(caption: str, max_chars: int = 50) -> str:
    """Truncate caption at word boundary, max 50 chars (V.2 row <=120 gate)."""
    if len(caption) <= max_chars:
        return caption
    truncated = caption[:max_chars]
    # Try to break at last space
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.6:
        return truncated[:last_space] + '...'
    return truncated + '...'


def parse_file(content: str) -> list[tuple[str, str, str, str]]:
    """Parse file, return (id, title, status, caption) for entries with status line."""
    lines = content.split('\n')
    entries = []
    current_id = None
    current_title = None
    current_status = None
    next_h2_found = False

    def finalize():
        nonlocal current_id, current_title, current_status
        if current_id is None or current_status is None:
            return
        # Caption: derive from title (strip W-NNN: prefix)
        clean_title = current_title.lstrip(':： ').strip()
        # Remove trailing "(推 vX.Y)" if present
        clean_title = re.sub(r'\s*\(推 v[\d.]+(\+[\w\s]+)?\)\s*$', '', clean_title)
        # Strip emoji (V.2 gate: caption no emoji)
        clean_title = strip_emoji(clean_title)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        caption = truncate_caption(clean_title, 50)
        entries.append((current_id, current_title, current_status, caption))

    for line in lines:
        m = H2_RE.match(line)
        if m:
            # Finalize previous
            finalize()
            current_id = m.group(1)
            current_title = m.group(2).strip()
            current_status = None
            continue

        if current_id is not None:
            m_status = STATUS_RE.match(line)
            if m_status and current_status is None:
                current_status = m_status.group(1)

    finalize()
    return entries


def build_index_rows(entries: list[tuple[str, str, str, str]]) -> list[str]:
    rows = []
    for h2_id, title, status, caption in entries:
        anchor = make_anchor(h2_id, title)
        rows.append(f'| [{h2_id}](#{anchor}) | {status} | {caption} |')
    return rows


def rebuild_file(input_path: Path, output_path: Path) -> None:
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        content = f.read()

    lines = content.split('\n')

    # Find 索引 section bounds
    idx_start = None
    idx_end = None
    for i, l in enumerate(lines):
        if l.startswith('## 索引'):
            idx_start = i
            continue
        if idx_start is not None and l.startswith('## ') and not l.startswith('## 索引'):
            idx_end = i
            break

    if idx_start is None:
        raise ValueError('索引 section not found')
    if idx_end is None:
        idx_end = len(lines)

    # Parse all H2 entries (with status line)
    entries = parse_file(content)
    rows = build_index_rows(entries)

    # Build new index
    new_index_lines = [
        '## 索引',
        '',
        '| ID | 状态 | 简介 |',
        '|----|------|------|',
    ]
    new_index_lines.extend(rows)
    new_index_lines.append('')

    new_lines = lines[:idx_start] + new_index_lines + lines[idx_end:]
    new_content = '\n'.join(new_lines)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.write(new_content)

    print(f'Rebuilt index: {len(rows)} rows')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: v2_13_5_rebuild_index.py <input.md> <output.md>')
        sys.exit(1)
    rebuild_file(Path(sys.argv[1]), Path(sys.argv[2]))