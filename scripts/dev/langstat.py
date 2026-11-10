#!/usr/bin/env python3
"""语言构成统计 —— 我们自己的「语言条」，因为 GitHub Linguist 不认 `.jhyy`。

**为什么需要它**（2026-11-10 实测）：

GitHub 侧栏那个语言条是 Linguist 算的 —— Linguist 没有 `.jhyy` 的映射 ⇒
**编译器真正的实现（`compiler/src0/*.jhyy` 等 377 个 `.jhyy` 文件）在那个条上
根本不存在**，取而代之的是 Python（参考实现 + 工具链，50.1%）。
⇒ 仓库主页上，一个「用这门语言自己写的编译器」看起来像是用 Python 写的。

这不是统计口径的问题，是 **Linguist 不认识这门语言**。所以口径自己定，工具自己写。

**本工具做什么**：

- **文件清单取自 `git ls-files`** ⇒ 生成物与 vendored 代码自动排除
  （`.gitignore` 已经在管它们：`compiler/build/`、`vscode-ext/node_modules/`、
  `installer/build-artifacts/`、`tmp/`、`*.s` / `*.il` / `*.exe` …）
  —— **不维护第二份排除清单 = 不会有第二个漂移源**。
- **扩展名 → 语言映射表自己维护**，含 Linguist 缺的那一条：**`.jhyy` → JHYY**。
- **只统计编程语言**：文档/标记/资源（`.md` / `.txt` / `.json` / `.yaml` / `.svg` /
  `.png` / …）不算 —— 与 Linguist 的口径一致（它也不把 Markdown 画进语言条）。
- **口径是代码行数**（非空、非纯注释），不是字节 —— 字节口径会被 vendored 的
  压缩文件带偏，而「这个编译器是用什么写的」这个问题问的是行。
- 产出 `docs/internal/langstat.json`（机器可读）+ `langstat.svg`（浅）+
  `langstat-dark.svg`（深）—— 两版让 README 用 `<picture>` 跟主题走。
- `--check` 模式：比对**已提交的产物**与**当前源码树**是否一致（漂了 ⇒ 红）。

**用法**：

    python scripts/dev/langstat.py            # 重新生成产物
    python scripts/dev/langstat.py --check    # 只校验（CI 门用）

**退出码**：0 = 一致；1 = 有漂移（逐条列出）。
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_OUT = ROOT / "docs" / "internal" / "langstat.json"
SVG_LIGHT = ROOT / "docs" / "internal" / "langstat.svg"
SVG_DARK = ROOT / "docs" / "internal" / "langstat-dark.svg"
FACTS = ROOT / "docs" / "internal" / "FACTS.md"

# FACTS.md 里由本工具拥有的那一节（标记之间的一切由本工具重写）
BLOCK_BEGIN = "<!-- langstat:begin"
BLOCK_END = "<!-- langstat:end -->"

# 两份 README 的「Status」表里各有一行由本工具拥有（标记在最后一个格子里）
ROW_MARK = "<!-- langstat:row -->"
README_ROWS = {
    "README.md": (
        "| Language composition | **{pct}%** of the code is JHYY — {top} of {total} lines, "
        "{files} files — [FACTS.md § 7](docs/internal/FACTS.md) " + ROW_MARK + " |"
    ),
    "README.zh-CN.md": (
        "| 语言构成 | **{pct}%** 的代码是 JHYY —— {total} 行里的 {top} 行，{files} 个文件 —— "
        "[FACTS.md § 7](docs/internal/FACTS.md) " + ROW_MARK + " |"
    ),
}

# ── 扩展名 → 语言 ──────────────────────────────────────────────────────────
# 只收**编程语言**。文档/标记/资源（.md/.txt/.json/.yaml/.xml/.wxs/.svg/.png/
# .bmp/.rtf/.url/.meta/.ico/无扩展名）一律不算 —— 与 Linguist 的口径一致。
LANGS: dict[str, str] = {
    ".jhyy": "JHYY",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".py": "Python",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript",
    ".cs": "C#",
    ".sh": "Shell", ".bash": "Shell",
    ".ps1": "PowerShell",
    ".bat": "Batchfile", ".cmd": "Batchfile",
    ".s": "Assembly", ".asm": "Assembly",
    ".rs": "Rust", ".java": "Java", ".go": "Go",
    ".lua": "Lua",
}

# 每种语言的注释前缀：(行注释前缀们, 块注释起止 or None)
COMMENTS: dict[str, tuple[tuple[str, ...], tuple[str, str] | None]] = {
    "JHYY": (("//",), None),
    "C": (("//",), ("/*", "*/")),
    "C++": (("//",), ("/*", "*/")),
    "C#": (("//",), ("/*", "*/")),
    "JavaScript": (("//",), ("/*", "*/")),
    "TypeScript": (("//",), ("/*", "*/")),
    "Java": (("//",), ("/*", "*/")),
    "Go": (("//",), ("/*", "*/")),
    "Rust": (("//",), ("/*", "*/")),
    "Python": (("#",), None),
    "Shell": (("#",), None),
    "PowerShell": (("#",), None),
    "Lua": (("--",), None),
    "Assembly": ((";", "#"), None),
    "Batchfile": (("rem", "::"), None),
}

# 语言 → 色标（固定映射，不随排名漂 —— 颜色是识别位，不是装饰）
COLORS: dict[str, str] = {
    "JHYY": "#00d4aa",
    "Python": "#4c8fbd",
    "C": "#6e7781",
    "Shell": "#5fa85f",
    "PowerShell": "#a06bb5",
    "Assembly": "#c98a4b",
    "C#": "#3f9e4f",
    "Batchfile": "#b9a55f",
    "JavaScript": "#d9c04a",
    "TypeScript": "#4a90c4",
    "C++": "#f34b7d",
    "Rust": "#dea584",
    "Java": "#b07219",
    "Go": "#00add8",
    "Lua": "#000080",
}

# 主题：文字色 / 底色 / 描边
THEMES = {
    "light": {"fg": "#24292f", "muted": "#57606a", "rule": "#d0d7de"},
    "dark": {"fg": "#f0f6fc", "muted": "#9198a1", "rule": "#30363d"},
}

WIDTH = 760
BAR_H = 30
LEGEND_ROW = 22
COLS = 2


def fail(msg: str) -> None:
    problems.append(msg)


problems: list[str] = []


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def tracked_files() -> list[str]:
    """仓内跟踪的文件清单 —— 生成物/vendored 已经被 .gitignore 排除。"""
    try:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            capture_output=True, check=True,
        ).stdout.decode("utf-8", errors="replace")
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"[langstat] ERR —— 跑不了 `git ls-files`（{e}）。"
              f"本工具要靠它才知道哪些文件是源码。", file=sys.stderr)
        raise SystemExit(2) from e
    return [p for p in out.split("\0") if p]


def count_code_lines(path: Path, lang: str) -> int:
    """非空、非纯注释的行数。"""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    prefixes, block = COMMENTS.get(lang, ((), None))
    n = 0
    in_block = False
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if in_block:
            if block and block[1] in s:
                in_block = False
            continue
        if block and s.startswith(block[0]):
            if block[1] not in s:
                in_block = True
            continue
        low = s.lower()
        if any(low.startswith(p) for p in prefixes):
            continue
        n += 1
    return n


def collect() -> dict:
    """统计结果：按语言聚合代码行数与文件数。"""
    lines: Counter[str] = Counter()
    files: Counter[str] = Counter()
    for rel in tracked_files():
        ext = Path(rel).suffix.lower()
        lang = LANGS.get(ext)
        if lang is None:
            continue
        p = ROOT / rel
        if not p.is_file():
            continue
        n = count_code_lines(p, lang)
        if n == 0:
            continue
        lines[lang] += n
        files[lang] += 1
    total = sum(lines.values())
    order = [l for l, _ in lines.most_common()]
    rows = []
    for lang in order:
        rows.append({
            "lang": lang,
            "lines": lines[lang],
            "files": files[lang],
            "pct": round(lines[lang] / total * 100, 1) if total else 0.0,
            "color": COLORS.get(lang, "#8b949e"),
        })
    return {
        "total_lines": total,
        "total_files": sum(files.values()),
        "languages": rows,
    }


def render_svg(data: dict, theme: str) -> str:
    """浅/深两版图表。语言名是 ASCII ⇒ 不依赖任何字体。"""
    t = THEMES[theme]
    rows = data["languages"]
    total = data["total_lines"]

    bar_parts: list[str] = []
    x = 0.0
    for r in rows:
        w = r["lines"] / total * WIDTH if total else 0.0
        if w <= 0:
            continue
        bar_parts.append(
            f'<rect x="{x:.2f}" y="0" width="{w:.2f}" height="{BAR_H}" fill="{r["color"]}"/>'
        )
        x += w

    # 图例：两列固定列位（名字 / 百分比 / 文件数），不靠猜字宽对齐
    legend: list[str] = []
    col_w = WIDTH // COLS
    for i, r in enumerate(rows):
        cx = (i % COLS) * col_w
        cy = BAR_H + 20 + (i // COLS) * LEGEND_ROW
        mono = "SFMono-Regular,Consolas,Liberation Mono,monospace"
        # 单复数：不写嵌套同型引号的 f-string（那是 3.12+ 才有的语法）
        nfiles = "1 file" if r["files"] == 1 else f'{r["files"]} files'
        legend.append(
            f'<rect x="{cx}" y="{cy + 4}" width="10" height="10" rx="2.5" fill="{r["color"]}"/>'
            f'<text x="{cx + 18}" y="{cy + 14}" font-family="{mono}" font-size="13" '
            f'fill="{t["fg"]}">{r["lang"]}</text>'
            f'<text x="{cx + 296}" y="{cy + 14}" font-family="{mono}" font-size="13" '
            f'fill="{t["fg"]}" text-anchor="end">{r["pct"]}%</text>'
            f'<text x="{cx + 366}" y="{cy + 14}" font-family="{mono}" font-size="12" '
            f'fill="{t["muted"]}" text-anchor="end">{nfiles}</text>'
        )

    n_rows = (len(rows) + COLS - 1) // COLS
    height = BAR_H + 20 + n_rows * LEGEND_ROW + 6

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="Language composition by code lines">\n'
        f'  <title>Language composition — code lines</title>\n'
        f'  <g>\n'
        f'    <clipPath id="bar"><rect x="0" y="0" width="{WIDTH}" height="{BAR_H}" rx="6"/></clipPath>\n'
        f'    <g clip-path="url(#bar)">\n'
        + "".join(f"      {p}\n" for p in bar_parts)
        + f'    </g>\n'
        f'    <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{BAR_H - 1}" rx="5.5" fill="none" '
        f'stroke="{t["rule"]}" stroke-opacity="0.6"/>\n'
        + "".join(f"    {p}\n" for p in legend)
        + f'  </g>\n'
        f'</svg>\n'
    )


def render_facts_block(data: dict) -> str:
    """FACTS.md 里由本工具拥有的那一节（`docs/internal/FACTS.md` § 7）。"""
    rows = data["languages"]
    out = [
        BLOCK_BEGIN + " —— 这一节由 `scripts/dev/langstat.py` 生成，别手改 -->",
        "",
        "| 语言 | 代码行 | 占比 | 文件数 |",
        "|---|---|---|---|",
    ]
    for r in rows:
        out.append(f"| {r['lang']} | {r['lines']} | {r['pct']}% | {r['files']} |")
    out += [
        f"| **合计** | **{data['total_lines']}** | **100%** | **{data['total_files']}** |",
        "",
        "> 口径：**代码行数**（非空、非纯注释）；文件清单取自 `git ls-files`",
        "> ⇒ 生成物与 vendored 代码自动被 `.gitignore` 排除（不维护第二份排除清单）。",
        "> **`.jhyy` → JHYY 这条映射是 GitHub Linguist 没有的** —— Linguist 不认这门语言，",
        "> 所以 GitHub 侧栏那个语言条里，编译器真正的实现**一行都不出现**。",
        BLOCK_END,
    ]
    return "\n".join(out)


def replace_facts_block(data: dict) -> bool:
    """把 FACTS.md § 7 的标记之间换成新内容。标记不在 ⇒ False（不自己造小节）。"""
    if not FACTS.is_file():
        return False
    text = FACTS.read_bytes().decode("utf-8")
    i = text.find(BLOCK_BEGIN)
    j = text.find(BLOCK_END)
    if i < 0 or j < 0 or j < i:
        return False
    FACTS.write_bytes(
        (text[:i] + render_facts_block(data) + text[j + len(BLOCK_END):]).encode("utf-8"))
    return True


def readme_row(name: str, data: dict) -> str:
    """两份 README 的 Status 表里那一行（英文版 / 中文版各一行）。"""
    if not data["languages"]:
        return ""
    top = data["languages"][0]
    return README_ROWS[name].format(
        pct=top["pct"], top=top["lines"], total=data["total_lines"],
        files=top["files"])


def replace_readme_rows(data: dict) -> list[str]:
    """重写两份 README 里带标记的那一行。返回没找到的清单。

    走 read_bytes/write_bytes —— `read_text` 会把 CRLF 折成 LF、`write_text`
    又会写回 os.linesep ⇒ 一次重写就能把整份文件的行尾改掉。仓内 `*.md`
    由 `.gitattributes` 钉死 LF，但这条工具不该依赖那个前提。
    """
    missing: list[str] = []
    for name in README_ROWS:
        p = ROOT / name
        if not p.is_file():
            missing.append(name)
            continue
        raw = p.read_bytes()
        text = raw.decode("utf-8")
        row = readme_row(name, data)
        out_lines = []
        hit = False
        for line in text.split("\n"):
            if ROW_MARK in line:
                # 保住这一行原来的行尾（\r\n 还是 \n）
                eol = "\r" if line.endswith("\r") else ""
                out_lines.append(row + eol)
                hit = True
            else:
                out_lines.append(line)
        if not hit:
            missing.append(f"{name}（没有 {ROW_MARK} 标记）")
            continue
        p.write_bytes("\n".join(out_lines).encode("utf-8"))
    return missing


def build() -> dict:
    data = collect()
    payload = {
        "metric": "code lines (non-blank, non-comment-only)",
        "source": "git ls-files",
        "total_lines": data["total_lines"],
        "total_files": data["total_files"],
        "languages": data["languages"],
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    SVG_LIGHT.write_bytes(render_svg(data, "light").encode("utf-8"))
    SVG_DARK.write_bytes(render_svg(data, "dark").encode("utf-8"))
    if not replace_facts_block(data):
        print("[langstat] ⚠ FACTS.md 里没有 langstat 标记 —— § 7 的小节需要人工建一次")
    for miss in replace_readme_rows(data):
        print(f"[langstat] ⚠ {miss} —— 那一行需要人工建一次（带 {ROW_MARK} 标记）")
    return data


def check() -> int:
    """比对已提交的产物与当前源码树。"""
    print("[langstat] 核对语言构成产物是否与源码树一致……\n")
    if not JSON_OUT.is_file():
        fail("docs/internal/langstat.json 不存在 —— 跑 python scripts/dev/langstat.py")
        print("[langstat] FAIL —— 产物缺失:")
        for p in problems:
            print("  x", p)
        return 1
    fresh = collect()
    try:
        old = json.loads(read(JSON_OUT))
    except json.JSONDecodeError as e:
        fail(f"docs/internal/langstat.json 解析失败: {e}")
        old = None

    if old is not None:
        if old.get("total_lines") != fresh["total_lines"]:
            fail(f"总行数漂了: 产物 {old.get('total_lines')} vs 现算 {fresh['total_lines']}")
        old_map = {r["lang"]: r for r in old.get("languages", [])}
        new_map = {r["lang"]: r for r in fresh["languages"]}
        for lang in sorted(set(old_map) | set(new_map)):
            o = old_map.get(lang)
            n = new_map.get(lang)
            if o is None:
                fail(f"产物里没有 {lang}（现在 {n['lines']} 行 / {n['files']} 文件）")
            elif n is None:
                fail(f"产物里有 {lang}，但源码树里已经没有了")
            elif (o["lines"], o["files"]) != (n["lines"], n["files"]):
                fail(f"{lang} 漂了: 产物 {o['lines']} 行 / {o['files']} 文件 "
                     f"vs 现算 {n['lines']} 行 / {n['files']} 文件")

    data = fresh
    for p, theme in ((SVG_LIGHT, "light"), (SVG_DARK, "dark")):
        if not p.is_file():
            fail(f"{p.relative_to(ROOT)} 不存在 —— 跑 python scripts/dev/langstat.py")
            continue
        want = render_svg(data, theme)
        if read(p) != want:
            fail(f"{p.relative_to(ROOT)} 与当前源码树不一致 —— 跑 python scripts/dev/langstat.py")

    # FACTS.md § 7 —— 本工具拥有的一段，必须与源码树一致
    if not FACTS.is_file():
        fail("docs/internal/FACTS.md 不存在")
    else:
        text = read(FACTS)
        i = text.find(BLOCK_BEGIN)
        j = text.find(BLOCK_END)
        if i < 0 or j < 0 or j < i:
            fail("FACTS.md 里没有 langstat:begin / langstat:end 标记 —— § 7 的小节不见了")
        else:
            have = text[i:j + len(BLOCK_END)]
            if have != render_facts_block(data):
                fail("FACTS.md § 7 与当前源码树不一致 —— 跑 python scripts/dev/langstat.py")

    # 两份 README 的 Status 行 —— 门面上的数也会漂
    for name in README_ROWS:
        p = ROOT / name
        if not p.is_file():
            fail(f"{name} 不存在")
            continue
        text = p.read_bytes().decode("utf-8")
        rows = [ln for ln in text.split("\n") if ROW_MARK in ln]
        if not rows:
            fail(f"{name} 里没有 {ROW_MARK} 标记 —— Status 表的那一行不见了")
            continue
        want = readme_row(name, data)
        if rows[0].rstrip("\r") != want:
            fail(f"{name} 的语言构成行与当前源码树不一致 —— 跑 python scripts/dev/langstat.py")

    if problems:
        print(f"[langstat] FAIL —— {len(problems)} 处漂移:")
        for p in problems:
            print("  x", p)
        return 1
    print(f"[langstat] OK —— {data['total_lines']} 行 / {data['total_files']} 个文件，"
          f"产物与源码树一致。")
    for r in data["languages"]:
        print(f"       {r['lang']:<12}{r['lines']:>8} 行  {r['pct']:>5.1f}%  {r['files']} 文件")
    return 0


def main() -> int:
    if "--check" in sys.argv:
        return check()
    data = build()
    print(f"[langstat] 已生成：{data['total_lines']} 行 / {data['total_files']} 个文件\n")
    for r in data["languages"]:
        print(f"  {r['lang']:<12}{r['lines']:>8} 行  {r['pct']:>5.1f}%  {r['files']} 文件")
    print(f"\n  → {JSON_OUT.relative_to(ROOT)}")
    print(f"  → {SVG_LIGHT.relative_to(ROOT)}")
    print(f"  → {SVG_DARK.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
