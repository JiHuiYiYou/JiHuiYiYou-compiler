#!/usr/bin/env python3
"""
v2.13.5 workarounds.md status line mechanical rewrite (minimal version).

Maps emoji-laden status labels to 5-state enum + since/closed verb.
Strips emoji and bold-wrapping. Does NOT extract date/version (risky).
Does NOT truncate captions (risky). Does NOT insert Resolution detail (risky).

This is a minimal pure-emoji swap. Manual Edit tool calls handle:
- Date/version extraction
- Caption compression (>120 chars)
- Resolution detail insertion for long narratives

Usage: python v2_13_5_rewrite_workarounds.py <input.md> <output.md>
"""
import re
import sys
from pathlib import Path

# 5-state enum + verb mapping
EMOJI_TO_ENUM = {
    '✅': ('RESOLVED', 'closed'),
    '🟢': ('RESOLVED', 'closed'),
    '🟡': ('DEFERRED', 'since'),
    '❌': ('INVALID', 'since'),
    '⏸': ('DEFERRED', 'since'),
    '📚': ('SUPERSEDED', 'closed'),
    '🔵': ('RESOLVED', 'closed'),
}

# Special emoji-prefix patterns (regex, mapped to enum+verb)
SPECIAL_PATTERNS = [
    (re.compile(r'^🟢\s*\*\*?PARTIAL\*\*?'), ('ACTIVE', 'since')),
    (re.compile(r'^🟢\s*\*\*?FULL\s*CLOSED\*\*?'), ('RESOLVED', 'closed')),
    (re.compile(r'^🟢\s*\*\*?FULLY\s*CLOSED\*\*?'), ('RESOLVED', 'closed')),
    (re.compile(r'^🟢\s*\*\*?STABLE-PRODUCTION\*\*?'), ('SUPERSEDED', 'closed')),
    (re.compile(r'^⏸\s*\*\*?DEFERRED\*\*?'), ('DEFERRED', 'since')),
    (re.compile(r'^📚\s*\*\*?DOCS\*\*?'), ('SUPERSEDED', 'closed')),
    (re.compile(r'^🔵\s*\*\*?PARTIALLY\s*CLOSED\*\*?'), ('RESOLVED', 'closed')),
    (re.compile(r'^🌍\s*\*\*?ENV-ONLY\*\*?'), ('SUPERSEDED', 'closed')),
]

STATUS_LINE_RE = re.compile(r'^(\*\*(?:状态|Status):\*\*)\s*(.+?)$')

# Already-rewritten: starts with enum + (since|closed) + space
ALREADY_REWRITTEN_RE = re.compile(r'^(ACTIVE|RESOLVED|SUPERSEDED|DEFERRED|INVALID)\s+(since|closed)\s')


def map_label(label: str) -> tuple[str, str] | None:
    label_stripped = label.strip()

    # Try special patterns first
    for pat, (enum, verb) in SPECIAL_PATTERNS:
        if pat.match(label_stripped):
            return (enum, verb)

    # Try simple emoji prefix
    for emoji, (enum, verb) in EMOJI_TO_ENUM.items():
        if label_stripped.startswith(emoji):
            return (enum, verb)

    # Plain labels (already in enum, but not yet in since/closed form)
    plain_match = re.match(r'^(ACTIVE|RESOLVED|SUPERSEDED|DEFERRED|INVALID|CLOSED)\b', label_stripped)
    if plain_match:
        word = plain_match.group(1)
        if word == 'CLOSED':
            return ('RESOLVED', 'closed')
        verb = 'closed' if word in ('RESOLVED', 'SUPERSEDED') else 'since'
        return (word, verb)

    return None


def rewrite_status_line(line: str) -> str | None:
    """Rewrite a **状态:** line. Returns new line or None if no rewrite needed."""
    stripped = line.rstrip('\n')
    m = STATUS_LINE_RE.match(stripped)
    if not m:
        return None

    prefix, label = m.group(1), m.group(2)

    # Skip if already rewritten (label starts with enum + since/closed + space)
    if ALREADY_REWRITTEN_RE.match(label.strip()):
        return None

    mapping = map_label(label)
    if not mapping:
        return None

    enum, verb = mapping

    # Strip leading emoji + bold + enum word + whitespace/Chinese-paren
    cleaned = label.strip()
    cleaned = re.sub(r'^[✅🟢🟡❌⏸📚🔵]\s*', '', cleaned)
    cleaned = re.sub(r'^\*\*[^*]+\*\*\s*', '', cleaned)
    # Strip leading enum word (RESOLVED etc.) followed by space OR Chinese punct
    cleaned = re.sub(r'^(ACTIVE|RESOLVED|SUPERSEDED|DEFERRED|INVALID|CLOSED)([\s（(])', r'\2', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    # Drop redundant bold markup in body
    cleaned = re.sub(r'\*\*', '', cleaned)

    # Normalize **Status:** → **状态:**
    if prefix == '**Status:**':
        prefix = '**状态:**'

    new_line = f'{prefix} {enum} {verb} — {cleaned}'

    # Preserve trailing newline
    return new_line + '\n' if line.endswith('\n') else new_line


def rewrite_file(input_path: Path, output_path: Path) -> None:
    """Apply mechanical rewrite to all status lines in file."""
    with open(input_path, 'r', encoding='utf-8', newline='') as f:
        lines = f.readlines()

    rewritten_count = 0
    normalized_count = 0
    unchanged_count = 0

    out_lines = []
    for line in lines:
        # First pass: normalize **Status:** → **状态:** (regardless of content)
        if line.startswith('**Status:**') and not line.startswith('**状态:**'):
            line = line.replace('**Status:**', '**状态:**', 1)
            normalized_count += 1

        new_line = rewrite_status_line(line)
        if new_line is None:
            out_lines.append(line)
            unchanged_count += 1
        else:
            out_lines.append(new_line)
            rewritten_count += 1

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        f.writelines(out_lines)

    print(f'Rewrote: {rewritten_count} | Normalized: {normalized_count} | Unchanged: {unchanged_count}')
    print(f'{input_path} -> {output_path}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: v2_13_5_rewrite_workarounds.py <input.md> <output.md>')
        sys.exit(1)

    rewrite_file(Path(sys.argv[1]), Path(sys.argv[2]))