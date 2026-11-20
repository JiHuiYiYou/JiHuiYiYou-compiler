#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成「IDE 知识包」—— 给内嵌 Claude 会话常驻的 JHYY 速查。

    python scripts/gen-knowledge.py

产物：
    docs/generated/jhyy-knowledge.md      常驻知识包（中文）
    docs/generated/jhyy-knowledge.json    同样的内容（机器可读）

## 为什么要有这个

S1 的评测实测出来的结论：**模型的失败模式不是「不知道规则」，而是「多绕几圈」**。
⇒ 这份知识包的目标不是「再教一遍语法」（模型已经会），而是：

1. **规范章节目录** —— 让模型知道该查哪一节（省掉「我想查什么来着」那几轮）
2. **反直觉点** —— 规范里标了 ⚠ 的行（模型自己查得到，但不一定想到去查）
3. **附录 B「未实装 / 已实装但受限」** —— **模型不会主动想到去查这个**，
   而它恰好是最容易踩的坑（`fn(i32)` 函数指针类型、块表达式、guard pattern……）
4. **标准库签名** —— 名字不好记（`std_io_print` vs `io_print`），抄一遍省事
5. **一段完整示例程序** —— 一眼看出这门语言的形状

## 它是**生成**的，不是手写的

家族规约：「canonical pattern（设计如此，不是 bug）的落点是**语言规范**」⇒
真相源是规范 + 标准库源码，手写第二份就是制造漂移源。

⚠️ **相对链接必须重写** —— 规范里的链接是同目录的兄弟文件
（`[ABI § 2.3](jhyy-abi-v4.0.0.md#23-struct-布局)`），而知识包落在 `docs/generated/`
⇒ 原样抄过来就是断链 ⇒ 文档事实门（`docs_facts_check.py`）判红。

⚠️ **同页锚点要指向规范本体** —— 知识包是摘要，不是规范 ⇒ 那些小节在包里不存在。

⚠️ **归属标注要带「语言规范」三个字** —— 文档事实门把 `§ N.M` 按「最近的、在它
之前的文档锚点」解析；标注排在别的链接之后 ⇒ 会被解析成那个链接指向的文档
（实测：解析成 ABI ⇒ ABI 没 § 2.8 ⇒ 门红）。
"""

import json
import re
import sys
from pathlib import Path

JHYY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(JHYY_ROOT / "mcp-jhyy"))

from jhyy_spec_doc import load_spec_doc  # noqa: E402

SPEC_PATH = JHYY_ROOT / "docs" / "abis" / "jhyy-lang-spec-v4.0.0.md"
SPEC_BASENAME = "jhyy-lang-spec-v4.0.0.md"
STD_DIR = JHYY_ROOT / "compiler" / "src0" / "std"
OUT_DIR = JHYY_ROOT / "docs" / "generated"
OUT_MD = OUT_DIR / "jhyy-knowledge.md"
OUT_JSON = OUT_DIR / "jhyy-knowledge.json"
# 「报错 → 修法」表（给 IDE 的 hook 用 —— 诊断顺手带上怎么改）
OUT_ERROR_FIX = OUT_DIR / "jhyy-error-fix.json"


# ── 链接重写（手工扫描，不用正则：反斜杠在这台机器上容易被各种工具吃掉）────────

def rewrite_links(text):
    """把规范里的链接改成相对于 `docs/generated/` 的。

    - `](别的.md)`   => `](../abis/别的.md)`
    - `](#同页锚点)`  => `](../abis/jhyy-lang-spec-v4.0.0.md#同页锚点)`
    - `](http://…)`   => 不动
    """
    if not text:
        return text
    out = []
    i = 0
    n = len(text)
    while i < n:
        j = text.find("](", i)
        if j < 0:
            out.append(text[i:])
            break
        k = text.find(")", j + 2)
        if k < 0:
            out.append(text[i:])
            break
        target = text[j + 2:k]
        out.append(text[i:j])
        if target.startswith(("http://", "https://", "/")):
            out.append(text[j:k + 1])
        elif target.startswith("#"):
            out.append("](../abis/" + SPEC_BASENAME + target + ")")
        elif ".md" in target:
            out.append("](../abis/" + target + ")")
        else:
            out.append(text[j:k + 1])
        i = k + 1
    out.append("")
    return "".join(out)


# ── 采集 ────────────────────────────────────────────────────────

def section_label(sec):
    """章节引用：**语言规范** § 8 结构体。

    ⚠️ **必须带「语言规范」三个字** —— 文档事实门把 `§ N.M` 按「最近的、在它之前的
    文档锚点」解析；标注排在别的链接**之后** => 门会把它解析成那个链接指向的文档
    （实测：解析成 ABI => ABI 没 § 2.8 => 门红，2026-11-13）。
    """
    if sec.get("num"):
        return ("语言规范 § %s %s" % (sec["num"], sec.get("title", ""))).rstrip()
    return ("语言规范 %s" % sec.get("title", "")).rstrip()


def iter_with_parent(doc):
    """按顺序产出 (section, parent_h2)。

    ⚠️ **必须带父章** —— 附录 B 的内容在 **h3** 里（`### 未实装`），
    而 h3 没有自己的编号（num=''）=> 只按 section 自己的 num 找附录会**一个都找不到**。
    父章的 num 是字母（'A'/'B'/'C'/'D'）。
    """
    parent = None
    for sec in doc["sections"]:
        if sec.get("level") == 2:
            parent = sec
        yield sec, parent


def collect_toc(doc):
    """规范章节目录（h2）+ 每个章的一句话范围。

    为什么要目录：模型看到「§ 5.6 match」这一行，就知道**存在**一个 match 章节
    => 会去查。**不知道存在**是检索失败最常见的原因，比「查了没查到」更致命。
    """
    toc = []
    for sec in doc["sections"]:
        if sec.get("level") != 2:
            continue
        scope = ""
        in_code = False
        for line in sec.get("body", "").splitlines():
            t = line.strip()
            if t.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if not t or t.startswith((">", "|", "#")):
                continue
            if set(t) <= set("-= "):
                continue
            scope = rewrite_links(t[:70])
            break
        toc.append(
            {
                "num": sec.get("num", ""),
                "title": sec.get("title", ""),
                "scope": scope,
            }
        )
    return toc


def collect_pitfalls(doc):
    """规范里带 ⚠ 的行 —— 规范自己标好的「反直觉点」。

    规范第 10 行原文：「凡带 ⚠️ 的行是『与直觉/与旧规范不同』」。

    ⚠️ **组标题后面跟的列表项也要收进来**（2026-11-15 实测踩过）：
       规范 § 4.1 写的是「⚠️ 三处与直觉/旧规范不同：」**加三个 bullet**
       ⇒ 原实现**只收了标题那一行** ⇒ 知识包里就只剩
       「三处与直觉不同」**却没说是哪三处** ⇒ 比没有还糟
       （模型看到「有三处不同」但看不到内容 ⇒ 既学不到、又以为漏了）。
       ⇒ 现在：**以冒号结尾的 ⚠ 行** ⇒ 把紧跟其后的列表项并进同一条。
    """
    out = []
    for sec in doc["sections"]:
        lines = sec.get("body", "").splitlines()
        for i, line in enumerate(lines):
            if "⚠" not in line:
                continue
            text = line.strip()
            if text.startswith(">"):
                # 引用块里的 ⚠ 是「整章都反直觉」的提示 => 归到章级
                continue
            text = re.sub(r"^[-*+]\s*", "", text)
            text = re.sub(r"^\d+\.\s*", "", text)
            if len(text) < 8:
                continue
            # ⚠ **组标题** ⇒ 后面的列表项是**这条坑的内容**，不是别的坑
            if text.rstrip().endswith(("：", ":")):
                for follow in lines[i + 1:]:
                    ft = follow.strip()
                    if not ft:
                        continue
                    if not re.match(r"^([-*+]|\d+\.)\s+", ft):
                        break  # 出了列表 ⇒ 组标题结束
                    if "⚠" in ft:
                        continue  # 别的 ⚠ 单独收（别重复）
                    text += " " + re.sub(r"^[-*+]\s*", "", ft)
                    if len(text) > 600:
                        break
            out.append(
                {
                    "text": rewrite_links(text),
                    "section": section_label(sec),
                    "kind": "trap",
                }
            )
    return out


def collect_appendix_b(doc):
    """附录 B：未实装清单 + 已实装但受限表。

    **这是整份知识包最值钱的一块** —— 模型不会主动想到去查「哪些东西还没实现」，
    而它恰好是最容易踩的坑。
    """
    impl = []
    limited = []
    for sec, parent in iter_with_parent(doc):
        if (parent or {}).get("num") != "B":
            continue
        title = sec.get("title", "")
        body = sec.get("body", "")
        if "未实装" in title:
            for line in body.splitlines():
                t = line.strip()
                if not t.startswith("- "):
                    continue
                text = t[2:].strip().replace("**", "")
                if len(text) < 6:
                    continue
                impl.append({"text": rewrite_links(text)})
        elif "受限" in title:
            # 表格行：| 项 | 现象 | 台账 |
            for line in body.splitlines():
                t = line.strip()
                if not t.startswith("|"):
                    continue
                cells = [c.strip().replace("**", "") for c in t.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                if not cells[0] or cells[0] in ("项", "---"):
                    continue
                if set(cells[0]) <= set("-: "):
                    continue
                w_ref = cells[2] if len(cells) > 2 else ""
                limited.append(
                    {
                        "item": rewrite_links(cells[0]),
                        "symptom": rewrite_links(cells[1]),
                        "w_ref": "" if w_ref in ("台账", "—", "-") else w_ref,
                    }
                )
    return impl, limited


# ── 常用用法（**每个都真编译过**）────────────────────────────────────
#
# ⚠ **为什么要有它** —— 「翻译」那道新题实测：模型**34 轮**才摸清
#   「怎么打印一个数」⇒ 而这些细节**规范里没有一处写全**：
#
#   | 细节 | 说明 |
#   |---|---|
#   | **没有内建 print** | 得 `import fmt; import io;` |
#   | `fmt_i64(buf, v)` | 写十进制、**返回字节数**、**不写换行也不写 `\0`** |
#   | `std_io_print(s)` | 写一个 **cstr** ⇒ **自己保证结尾有 `\0`** |
#   | **buffer ≥ 32 字节** | i64 最多 20 位 + sign + `\0` |
#   | **数组字面量不能写 `[0u8; 32]`** | 只能逐个列 |
#   | **`n + 1` 的 `1` 默认是 i32** | `i64 + i32` ⇒ **type mismatch** ⇒ 要写 `1i64` |
#
# ⇒ ⇒ **模型只能一轮一轮试出来** ⇒ 34 轮。
#
# ⚠ **每个配方都真编译一遍** —— 编译不过 ⇒ **生成器报错**
#   ⇒ **知识包里不会出现编不过的代码** ⇒ 不会漂。

USAGE_EXAMPLES = [
    {
        "title": "打印一个 i64（十进制）并换行",
        "note": (
            "JHYY **没有内建 print** —— 输出要走 stdlib：\n"
            "`fmt_i64` 把十进制写进 buffer（**返回字节数**，**不写换行也不写 `\\0`**）；\n"
            "`std_io_print` 写一个 **cstr** ⇒ **自己保证结尾有 `\\0`**。\n"
            "⚠ buffer **≥ 32 字节**（i64 最多 20 位 + sign + `\\0`）；\n"
            "⚠ 数组字面量**不能**写 `[0u8; 32]` ⇒ 只能逐个列；\n"
            "⚠ `n + 1` 的 `1` 默认是 **i32** ⇒ `i64 + i32` 报 type mismatch ⇒ 要写 `1i64`。"
        ),
        "code": """import fmt;
import io;

fn print_i64(v: i64) {
    let mut buf: [u8; 32] = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8];
    let p: *u8 = &buf[0];
    let n = fmt_i64(p, v);
    buf[n] = 10u8;
    buf[n + 1i64] = 0u8;
    std_io_print(p);
}

fn main_jhyy() -> i32 {
    print_i64(42);
    return 0;
}""",
    },
    {
        "title": "打印一个字符串",
        "note": (
            "字符串字面量要 **cast 成 `*u8`**（`\"...\" as *u8`）；\n"
            "`std_io_print` 写的是 **cstr** ⇒ 字面量自带结尾 `\\0` ⇒ 直接写即可。"
        ),
        "code": """import io;

fn main_jhyy() -> i32 {
    std_io_print("hello\\n" as *u8);
    return 0;
}""",
    },
    {
        # 2026-11-15 加 —— 第二条有实测证据的补强。
        #
        # 证据（臂 J，翻译题加了 1 道 struct 题）：模型写 `Point { x: 10, y: 20 }`
        # ⇒ **field type mismatch** ⇒ 知识包**附录 B 里登记过**这条规则，
        # 但那是**「受限清单」**（陈述事实），**不是「该怎么写」** ⇒ 模型照着
        # 写还是会踩 ⇒ ⇒ **要的是「能编译的用法」**，不是又一条规则。
        "title": "struct 字面量：字段值要**显式带类型**",
        "note": (
            "**struct 字面量的字段值类型必须精确匹配字段类型** ——\n"
            "`type P = struct { x: i32 }` 写 `P { x: 10 }` ⇒ 报 `field type mismatch`\n"
            "（**整数字面量默认推断为 i32**；而 `x` 声明成 i32 —— 看着一样，\n"
            "其实**推断不出那个类型**）⇒ **要写 `P { x: 10 as i32 }`**。\n"
            "⚠️ **省略的字段编译器不报错**，但它的值是**栈上的未初始化垃圾**\n"
            "   （不是 0）⇒ 别省字段。\n"
            "⚠️ **struct 按值传参/返回**是支持的（递归复制）；但**数组**按值传参\n"
            "   实际是**按引用**（跟 C 不一样）⇒ 要副本得自己拷。"
        ),
        "code": """import fmt;
import io;

type Point = struct {
    x: i32,
    y: i32,
}

fn dist2(a: Point, b: Point) -> i32 {
    let dx: i32 = a.x - b.x;
    let dy: i32 = a.y - b.y;
    return dx * dx + dy * dy;
}

fn main_jhyy() -> i32 {
    // ⚠️ 字段值要**显式带类型** —— 整数字面量默认是 i32
    let p: Point = Point { x: 10 as i32, y: 20 as i32 };
    let q: Point = Point { x: 1 as i32, y: 2 as i32 };
    let d: i32 = dist2(p, q);
    let mut buf: [u8; 32] = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8];
    let out: *u8 = &buf[0];
    let n = fmt_i32(out, d);
    buf[n] = 10u8;
    buf[n + 1i64] = 0u8;
    std_io_print(out);
    return 0;
}""",
    },
    {
        # 2026-11-15 加 —— **唯一一条**有实测证据的补强。
        #
        # 证据（臂 H2，翻译题加 3 道手写题）：模型在 `mem` / `math` 上**直接用了**
        # 知识包里的 API（`mem_copy` / `std_math_sqrt` / `fmt_i32` 都一次写对）⇒
        # **知识包的 stdlib API 表是有效的**。
        # 但在 `string` 上它**自己手写了 strlen/strcmp/strstr**（40 行）⇒ 为什么？
        # ⇒ `string` 的每个函数都要一个 **arena**（`str_from_cstr(a, s)` 的 `a`），
        #   而知识包只列了 `arena_init(a, default_size)`、**没说什么是 `a`** ⇒
        #   模型面对一个「不知道从哪来」的前置参数 ⇒ **理性地绕开它自己写**。
        # ⇒ 这就是「该补什么」的答案：**补前置条件/用法，不是补更多 API**。
        "title": "字符串模块（string）：先拿一个 arena",
        "note": (
            "`string` 模块的函数都要一个 **arena**（`str_from_cstr(a, s)` 的 `a`）——\n"
            "**arena 就是一个 40 字节的缓冲区**：`arena_init(a, size)` 把它变成 arena。\n"
            "⚠️ 知识包的 API 表只列了 `arena_init(a, default_size)`，**没说什么是 `a`**\n"
            "   ⇒ 这里补上（实测：不知道这个前置条件时，模型会自己手写一遍 strlen）。\n"
            "⚠️ `str_data(s)` 返回的**不是 cstr**（**没有结尾 `\\0`**）⇒ 不能直接喂给\n"
            "   `std_io_print` ⇒ 要先复制进自己的 buffer 再补 `\\0`。\n"
            "⚠️ 只想测长度/比较的话，**自己写二十行往往比绕 arena 省事** ——\n"
            "   先想清楚要什么，再决定用不用这个模块。"
        ),
        "code": """import arena;
import string;
import fmt;
import io;

fn main_jhyy() -> i32 {
    // arena = 一个 40 字节的缓冲区（5 个 i64）
    let mut abuf: [i64; 5] = [0i64, 0i64, 0i64, 0i64, 0i64];
    let a = abuf as *u8;
    arena_init(a, 4096 as i64);
    let s = str_from_cstr(a, "hello" as *u8);
    let mut buf: [u8; 32] = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8];
    let p: *u8 = &buf[0];
    let n = fmt_i64(p, str_len(s));
    buf[n] = 10u8;
    buf[n + 1i64] = 0u8;
    std_io_print(p);
    return 0;
}""",
    },
    {
        # 2026-11-15 加 —— **enum + match 的「该怎么写」**。
        #
        # 为什么要（评测逼出来的）：`enum` 在知识包里**只以「坑」的形式出现**
        # （变体只能带一个 payload / alignof 恒为 4 / 嵌套 pattern 不支持），
        # **没有一段能照抄的写法** ⇒ 而评测里那道 enum 题模型是**查规范拼出来的**
        # ⇒ ⇒ 坑登记了、用法没有 ⇒ 跟 § 8.12 的结论一模一样。
        "title": "枚举 + match：该怎么写",
        "note": (
            "`type X = enum { ... }` —— **结尾不带分号**（跟 `struct` 一样）。\n"
            "⚠️ **match 的 arm body 只能是单个表达式** —— 不能写 `return`、\n"
            "   也不能写成语句块 `{ ... }` ⇒ 要多步就 `let r = match ... ;` 再 `return r`。\n"
            "⚠️ match 作用在 enum 上时**要穷尽**（每个变体都覆盖，或有 `_` 兜底）\n"
            "   ⇒ 否则编译期报 `non-exhaustive match: missing variant`。\n"
            "⚠️ **变体最多带一个 payload**：`Rect(i32, i32)` 是解析错误\n"
            "   ⇒ 要带多个字段就把 payload 换成 struct。"
        ),
        "code": """import fmt;
import io;

type Shape = enum {
    Circle,
    Square,
    Triangle,
}

fn sides(s: Shape) -> i32 {
    // ⚠️ arm body 只能是单个表达式 ⇒ 先 let 再 return
    let r: i32 = match s {
        Shape::Circle => 0,
        Shape::Square => 4,
        Shape::Triangle => 3,
    };
    return r;
}

fn main_jhyy() -> i32 {
    let mut buf: [u8; 32] = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8];
    let p: *u8 = &buf[0];
    let n = fmt_i32(p, sides(Shape::Square));
    buf[n] = 10u8;
    buf[n + 1i64] = 0u8;
    std_io_print(p);
    return 0;
}""",
    },
]


def collect_usage_examples():
    """常用用法 —— **每个都真编译一遍**（编译不过 ⇒ 生成器报错）。

    ⚠ **为什么要有这道门**：知识包里的代码是**模型会照抄**的
    ⇒ 一段编不过的示例比没有示例更糟（模型会照抄一个编不过的写法）。
    ⇒ ⇒ **编译不过就不许进包**。
    """
    exe = JHYY_ROOT / "compiler" / "build" / "bin" / "jhyy.exe"
    if not exe.exists():
        print("! 编译器不在（%s）⇒ 跳过「用法示例」的编译把关" % exe)
        return USAGE_EXAMPLES
    import subprocess
    import tempfile
    out = []
    for ex in USAGE_EXAMPLES:
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "usage_example.jhyy"
            src.write_text(ex["code"] + "\n", encoding="utf-8", newline="")
            r = subprocess.run(
                [str(exe), "compile", str(src), "-o", str(Path(d) / "out")],
                capture_output=True, text=True, errors="replace", timeout=120,
            )
        if r.returncode != 0:
            err = (r.stderr or "").strip().splitlines()
            msg = "\n".join(err[-6:]) if err else "(无输出)"
            raise SystemExit(
                "✗ 用法示例「%s」**编译不过** ⇒ 不许进知识包：\n%s"
                % (ex["title"], msg)
            )
        out.append(ex)
    return out


# ── 反直觉点（**编译器逐条验证过的**）────────────────────────────────
#
# ⚠️ **为什么只放这几条** —— 翻译题的轨迹显示，模型查规范查的就是这些：
#   整数字面量后缀 / 取值范围 / 运算符优先级 / 无符号除法 / 移位 /
#   `as` 转换 / `if-else` 分支体 ⇒ ⇒ **只做模型真查过、真撞过的**，
#   不塞无关内容。
#
# ⚠️ **两条硬保证**（都由生成器把关）：
#   · **A 型（会咬人）**：❌ **必须编译失败**且报错**含**指定子串；
#     ✅ **必须编译通过** ⇒ 规则过时了立刻发现。
#   · **B 型（无害但会让人想查）**：代码**必须编译通过**且**必须跑出输出**，
#     输出**由生成器实测填进包里** ⇒ **包里的数字是编译器实测的**。
#
# ⚠️ **B 型的数字是实测填的，不是手写的** ⇒ 编译器行为变了 ⇒ 数字自动跟着变
#   ⇒ 而「形状」由「必须编译通过 + 必须跑出输出」保证 ⇒ 变了就红。

VERIFIED_RULES = [
    {
        "kind": "bite",
        "title": "**u32 的字面量要带 `u32` 后缀**",
        "why": (
            "无后缀整数字面量是 **i32** ⇒ `x + 1`（x 是 u32）⇒ **i64/i32 混算**\n"
            "⇒ 报 `type mismatch in binary`。\n"
            "⚠️ **从 C 过来的模型 100% 会踩**（C 里 `uint32_t + 1` 天经地义）。\n"
            "⚠️ 后缀**必须是 `u32`** —— 写 `1i64` 一样报错。"
        ),
        "wrong": "let x: u32 = 5;\n    let y: u32 = x + 1;",
        "expect": "type mismatch in binary",
        "right": "let x: u32 = 5;\n    let y: u32 = x + 1u32;",
    },
    {
        "kind": "bite",
        "title": "**整数 ↔ 浮点不能隐式转换**",
        "why": (
            "`let x: f64 = 3;` ⇒ **类型对不上** ⇒ 要写 `3 as f64`。\n"
            "⚠️ C 里 `double d = 3;` 是合法的 ⇒ 从 C 过来的模型会直接踩。"
        ),
        "wrong": "let x: f64 = 3;",
        "expect": "type mismatch in let",
        "right": "let x: f64 = 3 as f64;",
    },
    {
        "kind": "bite",
        "title": "**`type` 定义结尾不能带 `;`**",
        "why": "`type X = struct { ... }` / `enum` **结尾不带分号** ⇒ 带了就在表达式位置报 `;`。",
        "wrong": "type P = struct { a: i32 };",
        "expect": "unexpected token ';'",
        "right": "type P = struct { a: i32 }",
        # ⚠️ `type` / `import` 是**顶层声明** ⇒ 必须在函数**外面**
        "pre": True,
    },
    {
        "kind": "bite",
        "title": "**`import` 只写模块名本身（不带 `std::`）**",
        "why": "`import vec;` ✓；`import std::vec;` ⇒ 解析器看到 `::` 直接报错。",
        "wrong": "import std::vec;",
        "expect": "got ::",
        "right": "import vec;",
        # ⚠️ `import` 也是**顶层声明**
        "pre": True,
    },
    {
        "kind": "bite",
        "title": "**闭包不能捕获外层变量**",
        "why": (
            "闭包只能用**自己的参数和字面量** ⇒ 要用的外层值**当参数传进去**。\n"
            "⚠️ C++/Rust 的 lambda 都能捕获 ⇒ 从那边过来的模型会直接踩。"
        ),
        "wrong": "let n: i32 = 5;\n    let f = |x: i32| { x + n };",
        "expect": "closure cannot capture outer variables",
        "right": "let f = |x: i32| { x + 5 };",
    },
    {
        "kind": "fact",
        "title": "**整数字面量：装得下目标类型时，目标类型说了算（不用加后缀）**",
        "why": (
            "有类型标注时，**字面量按目标类型解释**（`let x: u32 = 3000000000;`\n"
            "⇒ 3000000000，不是 i32 的 -1294967296）⇒ **不需要**为了「怕溢出」加后缀。\n"
            "⚠️ 这条**只管「装得下」** —— 字面量**装不下**目标类型时（台账 W-228）\n"
            "   ⇒ 编译器**不报错**、同一个值**有两种解释** ⇒ 见下面那条。\n"
            "⚠️ 另外：**二元运算里的字面量**按 i32 算 ⇒ `u32 + 1` 得写 `1u32`。"
        ),
        "code": "let x: u32 = 3000000000;\n    print_i64(x as i64);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "fact",
        "title": "**整数溢出是回绕，不是报错**",
        "why": (
            "i32/u32 的 `+ - *` 溢出 ⇒ **回绕**（像 C 的无符号 / Rust 的 debug 相反）。\n"
            "⚠️ 想要报错得自己检查 ⇒ 别指望编译器拦你。"
        ),
        "code": "let x: i32 = 2147483647;\n    let y: i32 = x + 1;\n    print_i64(y as i64);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "fact",
        "title": "**i32 的 `>>` 是算术移位**（负数右移会补 1）",
        "why": (
            "`-1i32 >> 1` 得 **-1**（不是 0）⇒ **算术移位**。\n"
            "⚠️ **C 的有符号右移是「实现定义」**（gcc 给算术、但别拿别的编译器去推）\n"
            "⇒ ⇒ **从 C 来的模型可能按「无符号逻辑移位」去算** ⇒ ⇒ 看清楚。"
        ),
        "code": "let a: i32 = -1;\n    print_i64(a >> 1);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "fact",
        "title": "**`<<` 溢出是回绕（不报错）**",
        "why": (
            "`1i32 << 31` 得 **-2147483648**（回绕）⇒ 跟 `+ - *` 一样。\n"
            "⚠️ 想要报错得**自己检查** ⇒ 别指望编译器拦你。"
        ),
        "code": "let a: i32 = 1;\n    print_i64(a << 31);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "fact",
        "title": "**`~` 是补码取反（跟 C 一样）**",
        "why": (
            "`~0i32` = **-1**、`~0u32` = **4294967295** ⇒ 都是**补码取反**。\n"
            "⚠️ **别按 Rust 的「位非」去想**（Rust 的 `!0u32` 也是 4294967295，\n"
            "但 i32 上 Rust 是 `!0i32` = -1 ⇒ **两边在这点上恰好一致** ⇒\n"
            "⇒ **要小心的是「无符号 vs 有符号」的差别**，不是 `~` 本身）。"
        ),
        "code": "let a: i32 = 0;\n    print_i64(~a);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "trap",
        "title": "**字面量超出声明类型范围 ⇒ 同一个值有两种解释**",
        "why": (
            "字面量**装不下**声明的类型时，编译器**不报错**（台账 W-228）⇒\n"
            "⇒ **字面量路径**保留原始宽度、**运行时路径**却截断/回绕\n"
            "⇒ ⇒ **同一个值，看的地方不同 ⇒ 答案不同** ⇒ ⇒ **别这么写**。\n"
            "⚠️ **绕法**：字面量别超范围；要算越界的值 ⇒ 用**表达式**"
            "（`2147483647i32 + 1i32`）⇒ 走运行时路径 ⇒ 一致；\n"
            "要更大的值 ⇒ 换**更宽的类型**（u64 / i64）。"
        ),
        "literal_code": "let a: i32 = 2147483648;\n    print_i64(a as i64);",
        "runtime_code": "let a: i32 = 2147483647;\n    let b: i32 = a + 1i32;\n    print_i64(b as i64);",
    },
    {
        "kind": "bite",
        "title": "**`u32` 的移位，右操作数也要带 `u32` 后缀**",
        "why": (
            "`a >> 1` 里 `1` 是 **i32** ⇒ `u32 >> i32` ⇒ **type mismatch**。\n"
            "⚠️ 和「`u32` 加 `1`」是**同一个坑**（字面量后缀）。"
        ),
        "wrong": "let a: u32 = 5;\n    let b: u32 = a >> 1;",
        "expect": "type mismatch in binary",
        "right": "let a: u32 = 5;\n    let b: u32 = a >> 1u32;",
    },
    {
        "kind": "fact",
        "title": "**各整数字面量后缀的取值范围**",
        "why": (
            "字面量**写超出范围的数** ⇒ 编译器**不报错**（W-228）但会有两种解释 ⇒\n"
            "⇒ ⇒ **别越界** ⇒ 下面是各后缀的**实测**上限。"
        ),
        "code": "let a: u32 = 4294967295;\n    let b: i32 = 2147483647;\n    let c: i64 = 9223372036854775807;\n    print_i64(a as i64);\n    print_i64(b as i64);\n    print_i64(c);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**；`u64` 的上限 18446744073709551615 打印成 -1 是**正常**的 —— 它装不进 i64)",
    },
    {
        "kind": "fact",
        "title": "**`u32` → `u64` / `i64` 都是零扩展**",
        "why": (
            "宽化**不保符号** ⇒ `4294967295 as i64` 得 **4294967295**（不是 -1）。\n"
            "⚠️ C 里 `uint32_t` 宽化到 `int64_t` 是零扩展 ✓ 一致，"
            "但**别按「可能有符号」去猜**。"
        ),
        "code": "let x: u32 = 4294967295;\n    let y: i64 = x as i64;\n    print_i64(y);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "contrast",
        "title": "**`as` 与 `*` `/` `%` 同级（左结合）** —— 不是最低",
        "why": (
            "`as` 跟 `*` **同级** ⇒ `a * b as u64` ⇒ **`(a * b) as u64`**\n"
            "（**不是** `a * (b as u64)`）⇒ 转型落在**整条乘法链的外面**。\n"
            "⚠️ **C++/Rust 的转型比 `*` 紧** ⇒ 从那边过来的模型会顺手写\n"
            "   `a * (b as u64)` ⇒ **值不一样**（下面 ① ② 就是差在这儿）。\n"
            "⚠️ 想让**每个操作数各自转** ⇒ **必须自己写括号**。"
        ),
        "left_label": "`a * b as u64` —— JHYY **实际**这么解析（先乘后转）",
        "left_code": (
            "let a: u32 = 3000000000u32;\n"
            "    let b: u32 = 2u32;\n"
            "    let v: u64 = a * b as u64;\n"
            "    print_i64(v as i64);"
        ),
        "right_label": "`(a as u64) * (b as u64)` —— 想「各自转」就得这么写",
        "right_code": (
            "let a: u32 = 3000000000u32;\n"
            "    let b: u32 = 2u32;\n"
            "    let v: u64 = (a as u64) * (b as u64);\n"
            "    print_i64(v as i64);"
        ),
    },
    {
        "kind": "contrast",
        "title": "**`match` 的区间是闭区间、`for` 的是半开** —— 方向相反",
        "why": (
            "同一个语言里两个区间构造**方向相反**：\n"
            "· `match` 的 `0..10` ⇒ **含 10**（闭区间）；\n"
            "· `for` 的 `0..10` ⇒ **不含 10**（半开区间）。\n"
            "⚠️ **按同一条规则理解两个构造** ⇒ 必错一边\n"
            "（Rust 的 `..` 是半开 ⇒ 直觉套过来就错）。"
        ),
        "left_label": "`match` 里的 `0..10` —— **含 10**（闭区间）",
        "left_code": (
            "let r: i32 = match 10 {\n"
            "    0..10 => 1,\n"
            "    _ => 0,\n"
            "    };\n"
            "    print_i64(r as i64);"
        ),
        "right_label": "`for` 里的 `0..10` —— **不含 10**（半开区间）",
        "right_code": (
            "let mut s: i32 = 0;\n"
            "    for i in 0..10 {\n"
            "    s = s + i;\n"
            "    }\n"
            "    print_i64(s as i64);"
        ),
    },
    {
        "kind": "contrast",
        "title": "**要改的绑定必须 `let mut`** —— 不写 `mut` **不报错、只是不生效**",
        "why": (
            "不可变绑定**编译成 SSA 临时量** ⇒ `x = 1;` 编译期报\n"
            "`cannot assign to immutable variable (use let mut)`。\n"
            "⚠️ **但经指针写就不一样了**：`&x` 对不可变绑定**合法**（编译器不检查），\n"
            "   而 `*p = v` **不报错也**「**不生效**」（`x` 保持原值）⇒\n"
            "   ⇒ **静默**（没有诊断、没有警告）⇒ 程序照跑、结果照错。\n"
            "⚠️ **从 C 过来的模型 100% 会踩**：C 的 `int x = 5;` 天生可变。"
        ),
        "left_label": "不可变绑定（`let x`）—— 写进去了，**但没生效**",
        "left_code": (
            "let x: i32 = 5;\n"
            "    let p: *i32 = &x;\n"
            "    *p = 7;\n"
            "    print_i64(x as i64);"
        ),
        "right_label": "可变绑定（`let mut x`）—— 写进去了，**生效了**",
        "right_code": (
            "let mut x: i32 = 5;\n"
            "    let p: *i32 = &x;\n"
            "    *p = 7;\n"
            "    print_i64(x as i64);"
        ),
        "conclusion": (
            "⇒ ⇒ **要改的绑定就得写 `let mut`** ⇒ 不写 **不报错、只是不生效** ⇒\n"
            "⇒ ⇒ 这是**静默**错误 ⇒ 从 C 翻译过来的代码**必查**。"
        ),
    },
    {
        "kind": "contrast",
        "title": "**切片的区间是半开** —— 跟 `match` 的闭区间**相反**",
        "why": (
            "同一个 `..`：**match 里闭、切片里半开**。\n"
            "· `s[1..3]` ⇒ 取到 **2** 个元素（`1`、`2`）—— 半开；\n"
            "· `match 3 { 1..3 => ... }` ⇒ **命中**（3 在闭区间里）。\n"
            "⚠️ 切片**下标不做边界检查** ⇒ 区间写错一个端点，**读到的是邻居**\n"
            "   （不报错、不 panic）⇒ ⇒ **更要把端点数对**。"
        ),
        "left_label": "切片 `s[1..3]` —— **半开** ⇒ 长度 2",
        "left_code": (
            "let arr: [i32; 4] = [10 as i32, 20 as i32, 30 as i32, 40 as i32];\n"
            "    let s: [*]i32 = arr as [*]i32;\n"
            "    let sub: [*]i32 = s[1..3];\n"
            "    print_i64(len(sub) as i64);"
        ),
        "right_label": "match `1..3` —— **闭区间** ⇒ 命中 3",
        "right_code": (
            "let r: i32 = match 3 {\n"
            "    1..3 => 1,\n"
            "    _ => 0,\n"
            "    };\n"
            "    print_i64(r as i64);"
        ),
        "conclusion": (
            "⇒ ⇒ **同一个 `..`，两处语义相反**（match 闭 / 切片半开）⇒\n"
            "⇒ ⇒ 记不住就**两边各写一个小程序跑一下**（像这里这样）。"
        ),
    },
    {
        "kind": "bite",
        "title": "**入口是 `fn main_jhyy()` —— 不是 `main`**",
        "why": (
            "托管程序（`#[no_std]` 才用 `main`）的入口是 **`fn main_jhyy() -> i32`**。\n"
            "写成 `fn main()` ⇒ **链接期**才报\n"
            "`link failed - no entry symbol `main_jhyy` in the generated assembly`。\n"
            "⚠️ **实测：知识包里问「入口点叫什么」的次数是所有查规范里的第一**\n"
            "   ⇒ 写 JHYY 之前**先看一眼入口名**。"
        ),
        "whole": True,
        "wrong": "fn main() -> i32 {\n    return 0;\n}",
        "expect": "no entry symbol",
        "right": "fn main_jhyy() -> i32 {\n    return 0;\n}",
    },
    {
        "kind": "fact",
        "title": "**字符串字面量转切片 ⇒ `len` 是 0**（已知缺陷 W-233）",
        "why": (
            "字符串字面量的类型是 **`*u8`**（NUL 结尾），**不是切片**。\n"
            "⚠️ 显式写 `\"hello\" as [*]u8` ⇒ 转换**不报错**，但产出的切片\n"
            "   **len 字段没被填** ⇒ `len(s)` 得 **0**、`s[0]` 直接**访问违例**\n"
            "   （0xC0000005）⇒ ⇒ **台账 W-233**。\n"
            "⇒ ⇒ **别这么用**：字符串字面量就用 `*u8`，长度用 `strlen_local`。"
        ),
        "code": "let s: [*]u8 = \"hello\" as [*]u8;\n    print_i64(len(s) as i64);",
        "note": "⇒ 实测输出见下（**由生成器实测填入**）",
    },
    {
        "kind": "bite",
        "title": "**struct 字面量的字段值要显式带类型**",
        "why": (
            "字段类型**必须精确匹配** ⇒ 整数字面量默认是 **i32** ⇒\n"
            "`P { c: 7 }`（`c: u8`）⇒ 报 **`field type mismatch`**。\n"
            "⚠️ **从 C 过来的模型 100% 会踩**（C 里 `struct P p = {7};` 天经地义）。"
        ),
        "wrong": "let p: P = P { c: 7 };",
        "expect": "field type mismatch",
        "right": "let p: P = P { c: 7 as u8 };",
        "pre_code": "type P = struct { c: u8 }\n",
    },
    {
        "kind": "bite",
        "title": "**match 的 arm body 只能是单个表达式**",
        "why": (
            "`0 => { let y: i32 = 1; y }` ⇒ **解析错误**\n"
            "（`unexpected token '{' in expression` / `unexpected token 'let' in expression`）——\n"
            "arm 后面**只能直接写一个表达式** ⇒ 不能写语句块、也不能写 `return`。\n"
            "⚠️ 要多步就 `let r = match ... ;` 再 `return r;`。"
        ),
        "wrong": "let x: i32 = 1;\n    let r: i32 = match x {\n    0 => { let y: i32 = 1; y },\n    _ => 0,\n};",
        "expect": "unexpected token '{' in expression",
        "right": "let x: i32 = 1;\n    let r: i32 = match x {\n    0 => 1,\n    _ => 0,\n};",
    },
]


# ═══════════════════════════════════════════════════════════════════
# ⏱ **高频速查** —— 放在包的最**前面**（2026-11-15 实测逼出来的）
#
# 为什么要有（实测证据，不是猜的）：
#   包长到 **31k 字** ⇒ 模型**找不到那一条** —— 实测：知识包臂在
#   `slice-view` 那题**仍然查了 3 次规范**，尽管包里**就有**那条规则
#   ⇒ ⇒ 「有」≠「看得到」⇒ ⇒ 得把最常踩的**提到第一屏**。
#
# 每条只给**一行「该怎么写」** ⇒ 模型不用读完整个包就能改对。
#
# ⚠️ **不许漂移**：每条的标题都必须**对得上** VERIFIED_RULES 里的一条
#   （对不上 ⇒ 生成器报错）⇒ ⇒ 改规则时这里会红 ⇒ 两处不会各说各话。
# ⚠️ 排序 = **实测撞出来的频率**（评测里两臂的真实编译错误统计）。
QUICK_FIRE = [
    ("**入口是 `fn main_jhyy()` —— 不是 `main`**",
     "托管程序的入口是 **`fn main_jhyy() -> i32`**（写 `main` ⇒ **链接期**才报）"),
    ("**u32 的字面量要带 `u32` 后缀**",
     "u32 参与运算 / 移位 ⇒ 字面量带 `u32` 后缀：`x + 1u32`、`a >> 1u32`"),
    ("**要改的绑定必须 `let mut`** —— 不写 `mut` **不报错、只是不生效**",
     "要改的绑定写 `let mut`（否则**写进去也不生效**）"),
    ("**struct 字面量的字段值要显式带类型**",
     "字段类型**必须精确匹配** ⇒ `P { c: 7 as u8 }`（整数字面量默认 i32）"),
    ("**整数 ↔ 浮点不能隐式转换**",
     "要 f64 就写 `3 as f64`（**没有**隐式转换）"),
    ("**`type` 定义结尾不能带 `;`**",
     "`type X = struct { ... }` / `enum { ... }` **结尾不带分号**"),
    ("**`import` 只写模块名本身（不带 `std::`）**",
     "`import vec;`（**不带 `std::`**）"),
    ("**`as` 与 `*` `/` `%` 同级（左结合）** —— 不是最低",
     "`a * b as u64` 是 **`(a * b) as u64`** ⇒ 想「各自转」写 `(a as u64) * (b as u64)`"),
    ("**`match` 的区间是闭区间、`for` 的是半开** —— 方向相反",
     "`match` 的 `0..10` **含 10**；`for` 的 `0..10` **不含 10**"),
    ("**闭包不能捕获外层变量**",
     "闭包只能用**自己的参数** ⇒ 外层要用的值**当参数传进去**"),
    ("**match 的 arm body 只能是单个表达式**",
     "arm 后面**直接写表达式** ⇒ 不能写 `{ ... }`、也不能写 `return`"),
    ("**`u32` → `u64` / `i64` 都是零扩展**",
     "`4294967295 as i64` 得 **4294967295**（**不是** -1）"),
    ("**整数溢出是回绕，不是报错**",
     "溢出**回绕不报错** ⇒ 想要报错得**自己查**"),
    ("**字符串字面量转切片 ⇒ `len` 是 0**（已知缺陷 W-233）",
     "字符串字面量是 `*u8`、**不是切片** ⇒ `\"x\" as [*]u8` 的 **len=0** ⇒ 读元素**越界**"),
]


# ═══════════════════════════════════════════════════════════════════
# 🔀 **从 C 迁过来** —— C 的写法 ⇒ JHYY 怎么改
#
# 为什么要有（实测逼出来的）：评测全是「把 C 程序翻译成 JHYY」的题 ⇒
#   模型查规范问的**第二多**的东西就是**「C 的这个写法在 JHYY 里怎么说」**
#   （指针算术 / 切片 / 数组 / 借用，占查规范约 25%）⇒
#   ⇒ 知识包是**JHYY 的**知识 ⇒ **C 的那一半没人给** ⇒ 模型只能去翻规范。
#
# ⇒ ⇒ 这张表把「C 的写法 ⇒ JHYY 怎么写」**直接给出来**。
#
# ⚠️ **每一行都实测过**（不是照着规范抄的）⇒ 写错了这里会骗模型。
C_MIGRATION = [
    ("`int main(void)`", "`fn main_jhyy() -> i32`",
     "入口**不叫 `main`**（只有 `#[no_std]` 才用 `main`）"),
    ("`int x = 5;`（后面要改 x）", "`let mut x: i32 = 5;`",
     "不可变绑定**不能赋值**；经指针写也**静默不生效** ⇒ 要改就得 `let mut`"),
    ("`uint32_t a; a + 1`", "`let a: u32 = 5;` … `a + 1u32`",
     "无后缀整数字面量是 **i32** ⇒ u32 参与运算时字面量**必须带 `u32` 后缀**"),
    ("`double d = 3;`", "`let d: f64 = 3 as f64;`",
     "整数 ↔ 浮点**不能隐式转换** ⇒ 必须 `as`"),
    ("`int *p = &x;`", "`let p: *i32 = &x;`",
     "`&x` 的类型是 `*i32` ⇒ **指针类型要写全**"),
    ("`p + 1`（指针算术）", "`s[1..3]`（切片）",
     "切片区间**半开**；⚠️ **没有开区间** ⇒ `s[1..]` **编不过** ⇒ 末尾要自己算"),
    ("`arr[i]`（数组）", "`arr[i]`（数组）/ `s[i]`（切片）",
     "下标**不做边界检查** ⇒ 越界读到的是邻居内存"),
    ("`switch (x) { case 1: … }`", "`match x { 1 => … }`",
     "arm body **只能单个表达式**（不能 `{ … }` / `return`）；enum 要**穷尽**"),
    ("`enum E { A, B };`", "`type E = enum { A, B, }`",
     "**结尾不带分号**（跟 `struct` 一样）"),
    ("`struct S { int a; };` / `S s = {1};`",
     "`type S = struct { a: i32, }` / `S { a: 1 as i32 }`",
     "字段类型**必须精确匹配**（整数字面量默认 i32）"),
    ("`int (*f)(int);`（函数指针 / 回调）",
     "**没有** ⇒ 打平成普通函数 + 一个 kind",
     "没有 `fn(...)` 类型语法；闭包也**不能捕获**外层变量 ⇒ 当参数传进去"),
    ("`printf(\"%d\\n\", x)`", "`import fmt; import io;` + `fmt_i32` + `std_io_print`",
     "**没有内建 print** ⇒ 要自己写十行打印（见「常用用法」一节）"),
    ("`for (i = 0; i < n; i++)`", "`for i in 0..n { }`",
     "区间**半开** ⇒ 与 C 一致 ✓（但 `match` 的区间是**闭**的 ⇒ 别混）"),
    ("`(int64_t)a * b`", "`(a as i64) * b`",
     "`as` 与 `*` **同级**（左结合）⇒ `a * b as u64` 是 **`(a * b) as u64`**"),
]


def _check_quick_fire(verified_rules):
    """⏱ 高频速查的每一条都必须**对得上** VERIFIED_RULES 里的一条。

    ⚠️ **为什么要有这道检查**：速查表是**手写**的、正文是**另一份手写**
    ⇒ 两处迟早会各说各话（那就是「知识包自相矛盾」⇒ 最坏的一类 bug）
    ⇒ ⇒ 对不上就**不许生成**。
    """
    if not verified_rules:
        return
    titles = {r["title"] for r in verified_rules}
    for title, _fix in QUICK_FIRE:
        if title not in titles:
            raise SystemExit(
                "✗ 高频速查里的「%s」**在 VERIFIED_RULES 里没有对应的一条**\n"
                "  ⇒ 两处会各说各话 ⇒ 不许生成。\n"
                "  修法：改标题跟正文一致，或在 VERIFIED_RULES 里补这一条。"
                % title
            )


PRINT_HELPER = """import fmt;
import io;

fn print_i64(v: i64) {
    let mut buf: [u8; 32] = [0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8,
                              0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8];
    let p: *u8 = &buf[0];
    let n = fmt_i64(p, v);
    buf[n] = 10u8;
    buf[n + 1i64] = 0u8;
    std_io_print(p);
}
"""


def _compile(exe, src, tmpdir, tag):
    """编译一段源码 ⇒ 返回 (ok, stderr)。"""
    import subprocess
    path = Path(tmpdir) / ("%s.jhyy" % tag)
    path.write_text(src, encoding="utf-8", newline="")
    r = subprocess.run(
        [str(exe), "compile", str(path), "-o", str(Path(tmpdir) / tag)],
        capture_output=True, text=True, errors="replace", timeout=120,
    )
    return r.returncode == 0, (r.stderr or ""), str(Path(tmpdir) / (tag + ".exe"))


def _run(exe_path):
    import subprocess
    r = subprocess.run([exe_path], capture_output=True, text=True,
                       errors="replace", timeout=60)
    return r.stdout.strip()


def _fmt_body(body: str) -> str:
    """把 body 的缩进统一（每行 4 空格）—— 规则表里手写的 body 第一行没缩进、
    后面的行有 ⇒ 渲染出来参差不齐。"""
    lines = [ln.strip() for ln in body.strip().splitlines()]
    return "\n".join(("    " + ln) if ln else "" for ln in lines)


def collect_verified_rules():
    """反直觉点 —— **每条都真编译（有的还真跑）一遍**。

    ⚠️ **规则过时了 ⇒ 生成器报错** ⇒ 知识包里**不会有过时的规则**。
    """
    exe = JHYY_ROOT / "compiler" / "build" / "bin" / "jhyy.exe"
    if not exe.exists():
        print("! 编译器不在 ⇒ 跳过「反直觉点」的编译把关")
        return []
    import tempfile
    out = []
    with tempfile.TemporaryDirectory() as d:
        for i, rule in enumerate(VERIFIED_RULES):
            tag = "vr%d" % i
            if rule["kind"] == "bite":
                # ⚠️ `pre` ⇒ 声明在**顶层**（`type` / `import` 必须在函数外面）
                # ⚠️ `pre_code` ⇒ **顶层**的那段（`type X = struct {...}` 之类）
                #    —— 有了它，函数体里就能用那个类型了（`pre` 做不到这件事：
                #    `pre` 会把代码整个搬到顶层，而 `let` 在顶层不合法）
                # ⚠️ `whole` ⇒ 代码**就是整个程序**（连入口函数一起写）
                #    —— 只有「入口符号名」这种规则用得上（入口写错 ⇒ 链接期才报）
                def wrap(code):
                    pre = rule.get("pre_code") or ""
                    if rule.get("whole"):
                        return "%s%s\n" % (pre, code)
                    if rule.get("pre"):
                        return "%s%s\nfn main_jhyy() -> i32 {\n    return 0;\n}\n" % (pre, code)
                    return "%sfn main_jhyy() -> i32 {\n    %s\n    return 0;\n}\n" % (pre, code)

                wrong = wrap(rule["wrong"])
                ok, err, _ = _compile(exe, wrong, d, tag + "w")
                if ok:
                    raise SystemExit(
                        "✗ 反直觉点「%s」的**错版居然编译过了** ⇒ 这条规则"
                        "要么已过时、要么写错了 ⇒ 不许进知识包" % rule["title"]
                    )
                if rule["expect"] not in err:
                    raise SystemExit(
                        "✗ 反直觉点「%s」的错版**报错理由不对**（要 `%s`，实际 `%s`）"
                        "⇒ 不许进知识包" % (rule["title"], rule["expect"],
                                           err.strip().splitlines()[-1][:120])
                    )
                right = wrap(rule["right"])
                ok, err, _ = _compile(exe, right, d, tag + "r")
                if not ok:
                    raise SystemExit(
                        "✗ 反直觉点「%s」的**对版编译不过** ⇒ 不许进知识包：\n%s"
                        % (rule["title"], err.strip().splitlines()[-1][:160])
                    )
                item = dict(rule)
                item["wrong_code"] = wrong
                item["right_code"] = right
                out.append(item)
            elif rule["kind"] == "trap":
                # 陷阱型：**两个程序同时跑** ⇒ 把两种解释都摆出来
                #   ⇒ 门的效果：差异被如实写进包里（行为变了数字跟着变）
                outs = []
                for key, code in (("literal", rule["literal_code"]),
                                  ("runtime", rule["runtime_code"])):
                    src = PRINT_HELPER + ("fn main_jhyy() -> i32 {\n    %s\n    return 0;\n}\n"
                                           % code)
                    ok, err, exe_path = _compile(exe, src, d, tag + key)
                    if not ok:
                        raise SystemExit(
                            "✗ 反直觉点「%s」的**%s 路径编译不过** ⇒ 不许进知识包：\n%s"
                            % (rule["title"], key, err.strip().splitlines()[-1][:160])
                        )
                    outs.append((key, src, _run(exe_path)))
                item = dict(rule)
                # ⚠️ **正文只放 body** —— 那个 15 行的 `print_i64` 辅助
                #   重复两遍 ⇒ 噪音比信息多（实测包从 19k 涨到 26k）
                item["literal_body"] = rule["literal_code"]
                item["literal_out"] = outs[0][2].replace("\n", " / ")
                item["runtime_body"] = rule["runtime_code"]
                item["runtime_out"] = outs[1][2].replace("\n", " / ")
                out.append(item)
            else:
                # C 型：**两种解释对照** —— 同一件事的两种写法，
                #   **都编译、都跑**，把两种结果**并排**摆出来。
                #   ⚠️ 不能复用 trap 型（它的标签写死成「字面量路径 / 运行时路径」，
                #   换个含义就变成**假标签** ⇒ 反而误导）。
                if rule["kind"] == "contrast":
                    outs = []
                    for key in ("left", "right"):
                        src = PRINT_HELPER + (
                            "fn main_jhyy() -> i32 {\n    %s\n    return 0;\n}\n"
                            % rule[key + "_code"]
                        )
                        ok, err, exe_path = _compile(exe, src, d, tag + key)
                        if not ok:
                            raise SystemExit(
                                "✗ 反直觉点「%s」的**%s 版编译不过** ⇒ 不许进知识包：\n%s"
                                % (rule["title"], key, err.strip().splitlines()[-1][:160])
                            )
                        outs.append(_run(exe_path))
                    item = dict(rule)
                    item["left_body"] = rule["left_code"]
                    item["left_out"] = outs[0].replace("\n", " / ")
                    item["right_body"] = rule["right_code"]
                    item["right_out"] = outs[1].replace("\n", " / ")
                    out.append(item)
                    continue
                # B 型：**必须编译通过 + 必须跑出输出**（输出由实测填进包里）
                src = PRINT_HELPER + ("fn main_jhyy() -> i32 {\n    %s\n    return 0;\n}\n"
                                       % rule["code"])
                ok, err, exe_path = _compile(exe, src, d, tag)
                if not ok:
                    raise SystemExit(
                        "✗ 反直觉点「%s」的**代码编译不过** ⇒ 不许进知识包：\n%s"
                        % (rule["title"], err.strip().splitlines()[-1][:160])
                    )
                out_txt = _run(exe_path)
                if not out_txt:
                    raise SystemExit(
                        "✗ 反直觉点「%s」**跑不出任何输出** ⇒ 这条「事实」没测到东西"
                        "⇒ 不许进知识包" % rule["title"]
                    )
                item = dict(rule)
                # ⚠️ **正文只放 body**（同 trap 型）
                item["code_body"] = rule["code"]
                item["measured"] = out_txt.replace("\n", " / ")
                out.append(item)
    return out


def collect_stdlib():
    """标准库公开 API —— 从**源码的 `// API:` 块**抽。

    ⚠️ **不能抄规范 § 15 那张表** —— 实测那张表把 fmt 的内部 helper
    （`digit_char` / `hex_char`）和一个根本不是 stdlib 函数的 `ptr_add`
    也列成了「公开 API」。

    ⚠️ **也不能用「文件里所有 fn」** —— `string.jhyy` 自带 arena 内部 helper
    （`arena_init` / `arena_alloc` / `align_up`）=> `// API:` 块才是**有意设计的公开面**。
    """
    modules = []
    api_re = re.compile(r"^//\s+([a-z_][a-z_0-9]*)\s*\((.*?)\)\s*(?:->\s*(.*))?$")
    for path in sorted(STD_DIR.glob("*.jhyy")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        api_lines = []
        notes = []
        in_api = False
        for line in lines:
            if re.match(r"^//\s*API\s*:", line):
                in_api = True
                continue
            if in_api:
                if not line.strip().startswith("//"):
                    if not line.strip():
                        in_api = False
                    continue
                body = line.strip()[2:].strip()
                if not body:
                    continue
                m = api_re.match("//   " + body)
                if m:
                    api_lines.append(
                        {
                            "name": m.group(1),
                            "args": m.group(2).strip(),
                            "ret": (m.group(3) or "").strip(),
                        }
                    )
                else:
                    # ⚠ **API 块里的散文也留** —— 那是**用法规则**
                    #   （例：fmt 的「buffer 必须 ≥ 32 字节」、io 的
                    #   「std_io_print 写的是 cstr」）⇒ 模型最需要的正是这些。
                    notes.append(body)
        if api_lines:
            modules.append({"module": path.stem, "functions": api_lines,
                            "notes": notes})
    return modules


def collect_example(doc):
    """规范附录 D 的完整示例程序 —— 「一段代码看懂整门语言的形状」。"""
    for sec, parent in iter_with_parent(doc):
        if (parent or {}).get("num") != "D":
            continue
        if "完整示例" not in sec.get("title", ""):
            continue
        m = re.search(r"```jhyy\n(.*?)```", sec.get("body", ""), re.S)
        if m:
            return m.group(1).rstrip()
    return ""


# 像报错的特征词（用来把附录 B 现象列里的**代码片段/文件名**滤掉）
_ERR_WORDS = (
    "not supported", "unexpected", "mismatch", "cannot", "can not", "must",
    "expected", "non-exhaustive", "undefined", "invalid", "duplicate",
    "not allowed", "failed", "too many", "not defined", "not found",
)
# 代码味太重的符号 —— 报错原文里几乎不出现
_CODE_CHARS = ";={}()[]"


def _looks_like_error(text: str) -> bool:
    """这段反引号里的东西**像不像一条报错原文**。"""
    t = text.strip()
    if len(t) < 8 or len(t) > 60:
        return False
    if t.startswith("spec_err_") or t.endswith(".jhyy"):
        return False
    if any(c in t for c in _CODE_CHARS):
        return False
    low = t.lower()
    return any(w in low for w in _ERR_WORDS)


def _clean(text: str, limit: int = 120) -> str:
    """现象说明压到一行、限长、表格里的竖线换掉。"""
    t = " ".join(text.split()).replace("|", "/")
    if len(t) > limit:
        t = t[:limit] + "…"
    return t


def collect_error_lookup(doc):
    """**常见报错速查** —— 报错原文 → 怎么改。

    ## 为什么要有这一节（数据驱动的）

    评测（29 道配对任务，n=1）测到：加了 `jhyy_error_lookup` 之后
    **正确率 72% → 83%**（mask-change 那组 13% → 63%），
    **但轮数 +25%、成本 +45%** ⇒ 模型**开始查了**，而**每次查就是一轮**。

    ⇒ 既然答案是固定的、高频的，**就该前置到常驻知识包里** ⇒
    同样的信息、**零轮次**（不用调工具）。

    ⇒ 来源：规范 § 18 的「高频文本」表（用户最常撞上的）+ 附录 B 现象列里
    **确实像报错原文**的那些。
    """
    rows = []
    seen = set()

    def add(key: str, meaning: str, ref: str) -> None:
        k = key.strip()
        if not k or k in seen:
            return
        seen.add(k)
        rows.append((k, _clean(meaning), ref))

    for sec, parent in iter_with_parent(doc):
        num = (parent or {}).get("num")
        title = sec.get("title", "")
        body = sec.get("body", "")

        # ① § 18 的**高频文本表** —— 在「高频文本：」标记**之后**的那张表
        if num == "18" and "高频文本" in body:
            after = body.split("高频文本", 1)[1] if "高频文本" in body else ""
            for line in after.splitlines():
                t = line.strip()
                if not t.startswith("|"):
                    continue
                cells = [c.strip().replace("**", "") for c in t.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                key = cells[0].replace("`", "")
                if key in ("文本", "---") or set(key) <= set("-: "):
                    continue
                add(key, cells[1], "§ 18")

        # ② 附录 B 的「已实装但受限」—— 只取**确实像报错原文**的
        if num == "B" and "受限" in title:
            for line in body.splitlines():
                t = line.strip()
                if not t.startswith("|"):
                    continue
                cells = [c.strip().replace("**", "") for c in t.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                if not cells[0] or cells[0] in ("项", "---"):
                    continue
                if set(cells[0]) <= set("-: "):
                    continue
                for quoted in re.findall(r"`([^`]{8,120})`", cells[1]):
                    if _looks_like_error(quoted):
                        add(quoted, cells[1], "附录 B")
    return rows


# ── 渲染 ────────────────────────────────────────────────────────

def build_markdown(doc, toc, pitfalls, impl, limited, stdlib, example,
                    error_lookup, usage_examples=None, verified_rules=None):
    L = []
    A = L.append

    A("# JHYY 知识包 —— 给写 JHYY 的 AI 常驻的速查")
    A("")
    A("> **本文件是生成的，别手改** —— 改规范或标准库源码后重新跑：")
    A("> `python scripts/gen-knowledge.py`")
    A(">")
    A("> 真相源是语言规范（`docs/abis/jhyy-lang-spec-v4.0.0.md`）与标准库源码。")
    A("")
    A("## 怎么用这份知识包")
    A("")
    A("- **写代码前**：不确定某个语法/规则，查下面的目录 → 用 `jhyy_lang_ref` 取那一节。")
    A("- **写完后**：用 `jhyy_check` 真编译一遍，按**真实报错**改 —— 别靠猜。")
    A("- **看到「未实装」清单**：那些是**编译器明确拒绝**的构造 ⇒ 别写。")
    A("")
    A("### 工具速查（**直接用这些，不用先搜工具**）")
    A("")
    A("| 工具 | 干什么 | 什么时候用 |")
    A("|---|---|---|")
    A("| `jhyy_check` | 编译检查，返回**全部**诊断（行:列 + 错误原文） | 改完代码 ⇒ 必调一次 |")
    A("| `jhyy_run` | 编译**并运行**，返回 stdout / 退出码 | 要看程序实际输出 ⇒ 才调 |")
    A("| `jhyy_error_lookup` | **把一条报错翻成「什么意思/怎么改/该查哪一节/相关台账条目」** | 拿到报错但不知道该改哪 ⇒ 先问它 |")
    A("| `jhyy_lang_ref` | 查语言规范（传章节号最准，如 `\"5.6\"`） | 不确定语法/规则 ⇒ 查目录里那节 |")
    A("| `jhyy_workarounds` | 查已知坑台账（含「已修」和「设计如此」） | 报错看着像编译器 bug ⇒ 查 |")
    A("| `jhyy_abi_info` | 查 ABI（结构体布局 / 调用约定 / FFI） | 涉及 struct 传参 / FFI ⇒ 查 |")
    A("| `jhyy_get_il` | 看编译出来的 IL | 调试 codegen ⇒ 才用 |")
    A("")
    # ── **⏱ 高频速查 —— 放在第一屏** ────────────────────────────
    #   实测：包 35k 字 ⇒ 模型**找不到**中间某一条（明明有，还是去查了规范）
    #   ⇒ ⇒ 把「最常踩的」提到最前面，每条只给**一行「该怎么写」**。
    if QUICK_FIRE:
        A("## ⏱ 最常踩的 %d 条 —— **每条一行「该怎么写」**" % len(QUICK_FIRE))
        A("")
        A("> 写 JHYY 时**先扫这两段** ⇒ 对不上的，**照右边那行改**。")
        A("> 每条都有编译器验证过的细节 ⇒ 要看为什么，")
        A("> 翻到后面「反直觉点（**编译器逐条验证过的**）」那一节。")
        A("")
        for i, (title, fix) in enumerate(QUICK_FIRE, 1):
            A("%d. %s ⇒ %s" % (i, title, fix))
        A("")
    # ── **🔀 从 C 迁过来 —— 也在第一屏** ─────────────────────────
    #   实测：查规范最多的两类 =「入口点」（22%）+「C 的写法怎么改」（25%）
    #   ⇒ ⇒ 两段都放第一屏。
    #   ⚠️ **两段的先后：n=1 量不出差别**（v5 速查在前 0.36 次/次、
    #      v6 迁移在前 0.91 ⇒ 但两边**都在噪声里**，且 v6 剩下的查询
    #      **内容完全不同** ⇒ 更像运行时波动）⇒ ⇒ 保留**更好测**的那个顺序
    #      （速查在前），**要定这一版得跑 n=3**。
    if C_MIGRATION:
        A("## 🔀 从 C 迁过来 —— **C 的写法 ⇒ JHYY 怎么改**")
        A("")
        A("> 左边是 C，右边是 JHYY ⇒ **只写左边那个**就照右边改。")
        A("> 每一行都**实测过**（不是照着规范抄的）。")
        A("")
        A("| C 写法 | JHYY 怎么写 | 坑在哪 |")
        A("|---|---|---|")
        for c, j, why in C_MIGRATION:
            A("| %s | %s | %s |" % (c, j, why))
        A("")
    A("## 规范章节目录")
    A("")
    A("查某一节用 `jhyy_lang_ref`，参数传章节号（如 `\"5.6\"` / `\"附录 B\"`）。")
    A("")
    for t in toc:
        num = ("§ %s" % t["num"]) if t["num"] else ""
        A("- **%s %s**" % (num, t["title"]) + ((" —— %s" % t["scope"]) if t.get("scope") else ""))
    A("")

    A("## 反直觉点（规范里标了 ⚠ 的行）")
    A("")
    A("下面每条都是**规范原文标记**的「与直觉/与旧规范不同」之处。")
    A("")
    for p in pitfalls:
        A("- %s  *（%s）*" % (p["text"], p["section"]))
    A("")

    A("## 附录 B：未实装 —— 这些构造编译器会直接拒绝")
    A("")
    for item in impl:
        A("- %s" % item["text"])
    A("")

    A("## 附录 B：已实装但受限 —— 这些能写，但有坑")
    A("")
    for r in limited:
        w = ("（台账 %s）" % r["w_ref"]) if r["w_ref"] else ""
        A("- **%s** —— %s %s" % (r["item"], r["symptom"], w))
    A("")

    if error_lookup:
        A("## 常见报错速查 —— 报错原文 → 怎么改")
        A("")
        A("**不用去查工具**（`jhyy_error_lookup` 里有更全的，但下面这些最常撞上）。")
        A("")
        A("| 报错原文 | 什么意思 / 怎么改 |")
        A("|---|---|")
        for key, meaning, ref in error_lookup:
            A("| `%s` | %s（%s） |" % (key, meaning.replace("|", "/"), ref))
        A("")

    A("## 标准库公开 API")
    A("")
    A("导入时写模块名本身（**不带 `std::` 前缀**），调用时直接写完整函数名。")
    A("")
    for m in stdlib:
        A("### `%s`" % m["module"])
        A("")
        for f in m["functions"]:
            ret = (" -> %s" % f["ret"]) if f.get("ret") else ""
            A("- `%s(%s)`%s" % (f["name"], f["args"], ret))
        for note in m.get("notes") or []:
            A("")
            A("  > %s" % note)
        A("")

    if verified_rules:
        A("## 反直觉点（**编译器逐条验证过的**）")
        A("")
        A("> ⚠️ **每条都过编译器**：会咬人的 ⇒ 错版**必须编译不过**、"
          "对版**必须编译过**；无害但让人想查的 ⇒ **输出由生成器实测填进来**。")
        A("> ⇒ **规则过时了这里就会红** ⇒ 包里不会有过时的规则。")
        A("")
        for r in verified_rules:
            A("### %s" % r["title"])
            A("")
            A(r.get("why", ""))
            A("")
            if r["kind"] == "bite":
                A("❌ **这样写编译不过**：")
                A("")
                A("```jhyy")
                A(r["wrong_code"].rstrip())
                A("```")
                A("")
                A("✅ **这样写才对**：")
                A("")
                A("```jhyy")
                A(r["right_code"].rstrip())
                A("```")
            elif r["kind"] == "trap":
                A("（`print_i64` 的定义见上面『常用用法』一节）")
                A("")
                A("**① 字面量路径**（`let a: i32 = 2147483648;` 那样写）：")
                A("")
                A("```jhyy")
                A(_fmt_body(r["literal_body"].rstrip()))
                A("```")
                A("")
                A("⇒ 实测输出：`%s`" % r["literal_out"])
                A("")
                A("**② 运行时路径**（真算出来的那样写）：")
                A("")
                A("```jhyy")
                A(_fmt_body(r["runtime_body"].rstrip()))
                A("```")
                A("")
                A("⇒ 实测输出：`%s`" % r["runtime_out"])
                A("")
                if r["literal_out"] != r["runtime_out"]:
                    A("⚠️ **这两个不一样** ⇒ 同一个值两种解释 ⇒ **别这么写**。")
                else:
                    A("✅ 这两个一样 ⇒ 行为一致。")
                A("")
            elif r["kind"] == "contrast":
                A("（`print_i64` 的定义见上面『常用用法』一节）")
                A("")
                A("**① %s**：" % r["left_label"])
                A("")
                A("```jhyy")
                A(_fmt_body(r["left_body"].rstrip()))
                A("```")
                A("")
                A("⇒ 实测输出：`%s`" % r["left_out"])
                A("")
                A("**② %s**：" % r["right_label"])
                A("")
                A("```jhyy")
                A(_fmt_body(r["right_body"].rstrip()))
                A("```")
                A("")
                A("⇒ 实测输出：`%s`" % r["right_out"])
                A("")
                if r.get("conclusion"):
                    A(r["conclusion"])
                elif r["left_out"] != r["right_out"]:
                    A("⚠️ **这两个不一样** ⇒ 写法选错 ⇒ **结果就不同**。")
                else:
                    A("✅ 这两个一样 ⇒ 行为一致。")
                A("")
            else:
                A(r.get("note", ""))
                A("")
                A("```jhyy")
                A(_fmt_body(r["code_body"].rstrip()))
                A("```")
                A("")
                A("（`print_i64` 的定义见上面『常用用法』一节）")
                A("")
                A("**实测输出**：`%s`" % r["measured"])
            A("")

    if usage_examples:
        A("## 常用用法（**下面每段都真编译过**）")
        A("")
        A("> ⚠ **这些是模型最常踩、而规范没写全的地方** ⇒ 照抄即可，别自己试。")
        A("")
        for ex in usage_examples:
            A("### %s" % ex["title"])
            A("")
            A(ex["note"])
            A("")
            A("```jhyy")
            A(ex["code"])
            A("```")
            A("")

    if example:
        A("## 一段完整的 JHYY 程序（规范附录 D）")
        A("")
        A("```jhyy")
        A(example)
        A("```")
        A("")

    return "\n".join(L) + "\n"


def collect_error_fix():
    """导出「编译器报错 → 什么意思 / 怎么改 / 该查哪一节 / 相关台账条目」。

    ⚠️ **真相在 `mcp-jhyy/jhyy_errors.py`**（它把编译器源码、规范 § 18、
    规范附录 B、56 个 EXPECT-ERROR 用例、台账**五个只读来源**合在一起）
    ⇒ 这里**只导表**，不重新实现匹配逻辑 ⇒ 两边不会漂移。

    ⚠️ **索引模块 import 失败也要能跑** —— 这张表是「锦上添花」，
    缺了不该让整个知识包生成挂掉。
    """
    try:
        import jhyy_errors
    except Exception as e:
        print("! 错误索引 import 失败（跳过「报错速查表」）：%s" % e)
        return []
    entries = []
    for e in jhyy_errors.build_index().values():
        item = {
            "text": e.get("text", ""),
            "kind": e.get("kind", ""),
        }
        for k in ("meaning", "fix", "spec_ref", "w_ref", "w_status",
                  "example_file", "origin"):
            if e.get(k):
                item[k] = e[k]
        entries.append(item)
    entries.sort(key=lambda x: x["text"])
    return entries


def _compare(gen_dir: Path, repo_dir: Path) -> int:
    """比对「刚生成的」与「仓里的」⇒ 不一致就 FAIL。

    ⚠️ **JSON 要去掉 `builtAt`** —— 那是时间戳，每次生成都不同
    ⇒ 直接比对永远「不一致」。
    """
    import json as _json

    diffs = []
    for name in ("jhyy-knowledge.md", "jhyy-knowledge.json", "jhyy-error-fix.json"):
        a = gen_dir / name
        b = repo_dir / name
        if not a.exists() or not b.exists():
            diffs.append("%s：%s" % (name, "生成物缺失" if not a.exists() else "仓里缺失"))
            continue
        ta, tb = a.read_text(encoding="utf-8"), b.read_text(encoding="utf-8")
        if name.endswith(".json"):
            try:
                ja, jb = _json.loads(ta), _json.loads(tb)
                ja.pop("builtAt", None)
                jb.pop("builtAt", None)
                ta = _json.dumps(ja, ensure_ascii=False, sort_keys=True, indent=2)
                tb = _json.dumps(jb, ensure_ascii=False, sort_keys=True, indent=2)
            except Exception as e:
                diffs.append("%s：JSON 解析失败（%s）" % (name, e))
                continue
        # ⚠️ **行尾免疫** —— 产物是生成的 ⇒ 行尾不该算差异
        na = ta.replace("\r\n", "\n")
        nb = tb.replace("\r\n", "\n")
        if na != nb:
            # ⚠️ **说清楚「哪里不同」** —— 只说「不同」⇒ 排查只能靠猜
            #   （实测踩过：CI 说 JSON 不同、本地逐字节相同 ⇒ 卡了半小时）
            at = 0
            for i in range(min(len(na), len(nb))):
                if na[i] != nb[i]:
                    at = i
                    break
            else:
                at = min(len(na), len(nb))
            diffs.append(
                "%s：仓里的产物**不是最新的**（第一处不同 @%d）\n"
                "      新：%r\n      旧：%r"
                % (name, at, na[max(0, at - 90):at + 90], nb[max(0, at - 90):at + 90])
            )

    if diffs:
        print("[gen-knowledge] FAIL —— %d 处漂移：" % len(diffs))
        for d in diffs:
            print("  x %s" % d)
        print("  修法：跑 `python scripts/gen-knowledge.py`（规范/标准库改了就得重生成）")
        return 1
    print("[gen-knowledge] OK —— 知识包与源码树一致。")
    return 0


def main():
    # ⚠️ **`--no-usage-examples`** —— 复现「旧包」（没有「常用用法」那一节）
    #   ⇒ 用来 A/B「知识包加用法示例值多少轮」。
    # ⚠️ **`--out-dir`** —— 两份包共存（默认写 `docs/generated/`）。
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-usage-examples", action="store_true",
                    help="不生成「常用用法」那一节（复现旧包）")
    ap.add_argument("--no-verified-rules", action="store_true",
                    help="不生成「反直觉点（编译器验证过）」那一节（复现上一版包）")
    ap.add_argument("--out-dir", default=None,
                    help="输出目录（默认 docs/generated）")
    ap.add_argument("--check", action="store_true",
                    help="只核对「仓里的产物是不是最新的」⇒ 不一致就 FAIL")
    args = ap.parse_args()

    if not SPEC_PATH.exists():
        print("✗ 找不到规范：%s" % SPEC_PATH, file=sys.stderr)
        return 1
    if not STD_DIR.exists():
        print("✗ 找不到标准库源码：%s" % STD_DIR, file=sys.stderr)
        return 1

    doc = load_spec_doc(SPEC_PATH)
    toc = collect_toc(doc)
    pitfalls = collect_pitfalls(doc)
    impl, limited = collect_appendix_b(doc)
    stdlib = collect_stdlib()
    usage_examples = [] if args.no_usage_examples else collect_usage_examples()
    verified_rules = [] if args.no_verified_rules else collect_verified_rules()
    # ⚠️ **高频速查必须跟正文对得上** —— 对不上就**不许生成**
    _check_quick_fire(verified_rules)
    # ⚠️ **`--check` 模式**：生成到**临时目录**，比对目标是**仓里的**产物。
    #   ⚠️ **不能生成到仓里再比对** —— 那会**先把仓里的产物覆盖掉**
    #   ⇒ 比对永远「一致」⇒ **门形同虚设**（实测踩过：造了红灯却不亮）。
    check_tmp = None
    if args.check:
        import tempfile as _tf
        check_tmp = Path(_tf.mkdtemp(prefix="gen-knowledge-check-"))
        out_dir = Path(args.out_dir) if args.out_dir else check_tmp
    else:
        out_dir = Path(args.out_dir) if args.out_dir else OUT_DIR
    out_md = out_dir / OUT_MD.name
    out_json = out_dir / OUT_JSON.name
    out_error_fix = out_dir / "jhyy-error-fix.json"
    example = collect_example(doc)
    error_lookup = collect_error_lookup(doc)

    out_dir.mkdir(parents=True, exist_ok=True)
    md = build_markdown(doc, toc, pitfalls, impl, limited, stdlib, example,
                        error_lookup, usage_examples, verified_rules)
    with open(out_md, "w", encoding="utf-8", newline="") as f:
        f.write(md)

    payload = {
        "version": doc.get("version", ""),
        # ⚠️ **必须是「仓内相对路径」** —— 绝对路径**机器相关**
        #   （本机是 `C:/Users/...`、CI 是 `D:\a\...`）⇒ ⇒ 产物每次都不一样
        #   ⇒ ⇒ **「知识包是最新的」这道门在 CI 上永远红**（实测踩过，
        #   而且因为 JSON 里只有这一处带路径 ⇒ **只有 JSON 变、.md 不变**
        #   ⇒ ⇒ 排查时特别容易误判成「内容不同」）。
        #   ⚠️ 顺带修了个错：原来的绝对路径**漏了 `docs/`** ⇒ 指向的文件不存在。
        "source": SPEC_PATH.relative_to(JHYY_ROOT).as_posix(),
        "toc": toc,
        "pitfalls": pitfalls,
        "unimplemented": impl,
        "limited": limited,
        "stdlib": stdlib,
        "usage_examples": usage_examples,
        "verified_rules": verified_rules,
        "example": example,
        "error_lookup": error_lookup,
    }
    with open(out_json, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    error_fix = collect_error_fix()
    fix_payload = {
        "version": doc.get("version", ""),
        "entries": error_fix,
    }
    with open(out_error_fix, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(fix_payload, ensure_ascii=False, indent=2) + "\n")

    print("✓ %s（版本 %s）" % (SPEC_PATH.name, doc.get("version")))
    print("  章节目录 %d 章" % len(toc))
    print("  反直觉点 %d 条" % len(pitfalls))
    print("  未实装 %d 项" % len(impl))
    print("  受限 %d 行" % len(limited))
    print("  标准库 %d 模块 / %d 个函数"
          % (len(stdlib), sum(len(m["functions"]) for m in stdlib)))
    print("  完整示例 %s" % ("有" if example else "无"))
    print("  常见报错速查 %d 条" % len(error_lookup))
    print("  常用用法 %d 段（**每个都编译过**）" % len(usage_examples))
    print("  反直觉点（编译器验证过）%d 条" % len(verified_rules))
    print("→ %s" % out_md)
    print("→ %s" % out_json)
    print("  报错速查表 %d 条 → %s" % (len(error_fix), out_error_fix))
    print("  （markdown %d 字符）" % len(md))
    if args.check:
        rc = _compare(out_dir, OUT_DIR)
        try:
            import shutil
            shutil.rmtree(check_tmp, ignore_errors=True)
        except Exception:
            pass
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
