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
    """
    out = []
    for sec in doc["sections"]:
        for line in sec.get("body", "").splitlines():
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
        "title": "**整数字面量：目标类型说了算（不用加后缀）**",
        "why": (
            "有类型标注时，**超范围的大字面量也按目标类型解释**（不是截断）。\n"
            "⚠️ 没有标注时也能推出来 ⇒ **不需要**为了「怕溢出」去加后缀。"
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
]


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
                def wrap(code):
                    if rule.get("pre"):
                        return "%s\nfn main_jhyy() -> i32 {\n    return 0;\n}\n" % code
                    return "fn main_jhyy() -> i32 {\n    %s\n    return 0;\n}\n" % code

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
        if ta != tb:
            diffs.append("%s：仓里的产物**不是最新的**" % name)

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
        "source": str(SPEC_PATH).replace("\\", "/"),
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
