#!/usr/bin/env python3
"""扫全 repo .md 找悬空相对路径引用。"""
import os, re, urllib.parse

ROOT = os.environ.get("JHYY_ROOT") or os.getcwd()
SKIP_DIRS = {"node_modules", ".git", "qbe", ".agents"}
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# 真零宽字符(无空字符串,无普通空格)
ZERO_WIDTH = {"​", "‌", "‍", "﻿"}

def is_skipped(path):
    rel = os.path.relpath(path, ROOT)
    parts = rel.split(os.sep)
    return any(p in SKIP_DIRS for p in parts)

def resolve(file_dir, target):
    # title form: [text](url "title") — 找第一个成对引号对
    t = target
    if '"' in t:
        # find first '"' that's not at very start
        first = t.find('"')
        if first > 0:
            # url 部分 = 第一个 " 之前的部分(可能有 trailing space)
            t = t[:first].rstrip()
    path_part = t.split("#", 1)[0].strip()
    if not path_part:
        return None
    if re.match(r"^(https?|mailto|ftp):", path_part):
        return None
    # URL decode (处理 %20+%20 → ' + ')
    try:
        decoded = urllib.parse.unquote(path_part)
    except Exception:
        decoded = path_part
    if os.path.isabs(decoded):
        return os.path.normpath(decoded)
    if decoded.startswith("/"):
        return os.path.normpath(os.path.join(ROOT, decoded.lstrip("/").replace("/", os.sep)))
    return os.path.normpath(os.path.join(file_dir, decoded))

def main():
    md_files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.lower().endswith(".md"):
                p = os.path.join(dirpath, f)
                if not is_skipped(p):
                    md_files.append(p)
    md_files.sort()

    dangling = []
    hidden = []
    checked = 0
    for fp in md_files:
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
        except Exception as e:
            print(f"SKIP {fp}: {e}")
            continue
        file_dir = os.path.dirname(fp)
        for i, line in enumerate(lines, 1):
            if "[" in line and "](" in line:
                for zw in ZERO_WIDTH:
                    if zw in line:
                        hidden.append((fp, i, hex(ord(zw)), line.rstrip()[:140]))
                        break
            for m in LINK_RE.finditer(line):
                target = m.group(2).strip()
                text = m.group(1)
                abs_t = resolve(file_dir, target)
                if abs_t is None:
                    continue
                checked += 1
                if not os.path.exists(abs_t):
                    dangling.append((fp, i, text, target, abs_t))

    print(f"Scanned {len(md_files)} .md files, checked {checked} local markdown links\n")
    if hidden:
        print(f"=== HIDDEN CHARS in markdown link lines ({len(hidden)}) ===")
        for h in hidden[:30]:
            rel = os.path.relpath(h[0], ROOT)
            print(f"  {rel}:{h[1]} ZW={h[2]}\n    {h[3]}")
        if len(hidden) > 30:
            print(f"  ... +{len(hidden)-30} more")
        print()
    print(f"=== DANGLING local refs ({len(dangling)}) ===")
    # group by file for readability
    from collections import defaultdict
    by_file = defaultdict(list)
    for d in dangling:
        by_file[os.path.relpath(d[0], ROOT)].append(d)
    for rel, items in sorted(by_file.items()):
        print(f"  {rel} ({len(items)})")
        for d in items:
            print(f"    L{d[1]}  [{d[2]}] -> {d[3]}")
            print(f"      resolved={d[4]}")

if __name__ == "__main__":
    main()