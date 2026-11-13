#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成「IDE 知识包」—— 给内嵌 Claude 会话常驻的 JHYY 知识。

    python scripts/gen-knowledge.py

产物：
    docs/generated/jhyy-knowledge.md    常驻知识包（中文，进仓）
    docs/generated/jhyy-knowledge.json  同样的内容（机器可读）

## 为什么要有它

S1 的评测实测出来的结论：**模型的失败模式不是「不知道规则」，而是「多绕几圈」** ——
它会先翻文件、再去查规范（`jhyy_lang_ref`）、再改、再验。

⇒ 这份知识包的目标**不是「再教一遍规则」**（规范已经能查了），
而是**让模型少绕**：

1. **规范章节目录**（24 章）⇒ 模型一眼知道该查哪一节，不用「我想查什么来着」
2. **附录 B「未实装 / 已实装但受限」**⇒ **模型不会主动想到去查这个**，
   而它恰好是最容易踩的坑（`fn(i32)` 函数指针类型、块表达式、guard pattern…）
3. **标准库签名**⇒ 名字不好记（`std_io_print` vs `io_print`），抄一遍省事

## 它是**生成**的，不是手写的

家族规约：「canonical pattern（设计如此，不是 bug）的落点是**语言规范**」⇒
真相源是规范，手写第二份 = 制造漂移源。

⇒ 生成器从规范 + 标准库源码抽，产物提交进仓；规范改了 ⇒ 重新生成。

## 章节解析复用现成的模块

规范分节用 `mcp-jhyy/jhyy_spec_doc.py` 的 `load_spec_doc()`（**单一真相源**，
跟 `jhyy_lang_ref` / `jhyy_abi_info` 用的是同一个口径）⇒ 不重写解析逻辑。
"""

import json
import os
import re
import sys
from pathlib import Path

JHYY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(JHYY_ROOT / "mcp-jhyy"))

from jhyy_spec_doc import load_spec_doc  # noqa: E402

SPEC_PATH = JHYY_ROOT / "docs" / "abis" / "jhyy-lang-spec-v4.0.0.md"
STD_DIR = JHYY_ROOT / "compiler" / "src0" / "std"
OUT_DIR = JHYY_ROOT / "docs" / "generated"
OUT_MD = OUT_DIR / "jhyy-knowledge.md"
OUT_JSON = OUT_DIR / "jhyy-knowledge.json"

# 规范里的 ⚠ 标记 —— 规范第 10 行原文说「凡带 ⚠️ 的行是『与直觉/与旧规范不同』」
WARN_MARK = "⚠️"


def load_spec():
    return load_spec_doc(SPEC_PATH)


def iter_with_parent(doc):
    """按顺序产出 (section, parent_h2)。

    ⚠️ **必须带父章** —— 规范里附录 B 的内容在 **h3** 里（`### 未实装`），
    而 h3 没有自己的编号（num=''）⇒ 只按 section 自己的 num 找附录会**一个都找不到**。
    父章的 num 是字母（'A'/'B'/'C'/'D'，不是 '附录 B'）。
    """
    parent = None
    for sec in doc["sections"]:
        if sec.get("level") == 2:
            parent = sec
        yield sec, parent


def section_label(sec) -> str:
    """章节引用：§ 8 结构体 / § 附录 B。"""
    if sec.get("num"):
        return f"§ {sec['num']} {sec.get('title', '')}".rstrip()
    return sec.get("title", "")


def collect_toc(doc):
    """规范章节目录（只到 h2）+ 每个章的一句话范围。

    为什么要目录：模型看到「§ 5.6 match」这一行，就知道**存在**一个 match 章节
    ⇒ 会去查。**不知道存在**是检索失败最常见的原因，比「查了没查到」更致命。
    """
    toc = []
    for sec in doc["sections"]:
        if sec.get("level") != 2:
            continue
        body = sec.get("body", "")
        # 第一句**散文**当范围说明。
        # ⚠️ 别直接取第一行 —— 很多章的第一行是代码围栏（```jhyy）或表头
        #    （| 码 | 触发 |）⇒ 目录里会出现一堆没意义的片段（实测踩过）。
        # ⚠️ **代码围栏的「内容行」不以 ``` 开头** ⇒ 光跳 ``` 行不够，
        #    还得**跟踪围栏状态**，否则会取到 `let x = 42;` 这种代码行。
        scope = ""
        in_code = False
        for line in body.splitlines():
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
            scope = t[:70]
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

    每条 = 一行文字 + 所属章节号。**不重写内容**，只索引 + 跳转目标。
    """
    out = []
    for sec in doc["sections"]:
        body = sec.get("body", "")
        for line in body.splitlines():
            if WARN_MARK not in line:
                continue
            text = line.strip()
            if text.startswith(">"):
                # 引用块里的 ⚠ 是「整章都反直觉」的提示 ⇒ 归到章级
                continue
            # 去掉行首的 markdown 列表符号
            text = re.sub(r"^[-*+]\s*", "", text)
            text = re.sub(r"^\d+\.\s*", "", text)
            # ⚠️ **别剥 `**`** —— 它是 markdown 的粗体标记，剥掉会**破坏代码内容**
            #   （实测：`(C 的 `char **`)` 被剥成 `(C 的 `char `)` ⇒ 语义丢了）。
            #   原文照抄，粗体标记留着（markdown 里本来就该有）。
            if len(text) < 8:
                continue
            out.append({"text": text, "section": section_label(sec), "kind": "trap"})
    return out


def collect_appendix_b(doc):
    """附录 B：未实装清单 + 已实装但受限表。

    **这是整份知识包最值钱的一块** —— 模型不会主动想到去查「哪些东西还没实现」，
    而它恰好是最容易踩的坑。
    """
    impl = []
    limited = []
    for sec, parent in iter_with_parent(doc):
        # 附录 B 的内容在 h3 里 ⇒ 认**父章**的编号（'B'）
        in_appendix_b = (parent or {}).get("num") == "B"
        if not in_appendix_b:
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
                impl.append({"text": text})
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
                        "item": cells[0],
                        "symptom": cells[1],
                        "w_ref": "" if w_ref in ("台账", "—", "-") else w_ref,
                    }
                )
    return impl, limited


def collect_stdlib():
    """标准库公开 API —— 从**源码的 `// API:` 块**抽。

    ⚠️ **不要抄规范 §15 那张表** —— 实测那张表把 fmt 的内部 helper
    （`digit_char` / `hex_char`）和一个根本不是 stdlib 函数的 `ptr_add`
    也列成了「公开 API」。源码的 `// API:` 块才是**有意设计的公开面**。

    ⚠️ **也不能用「文件里所有 fn」** —— `string.jhyy` 自带 arena 内部 helper。
    """
    modules = []
    api_re = re.compile(r"^//\s+([a-z_][a-z_0-9]*)\s*\((.*?)\)\s*(?:->\s*(.*))?$")
    for path in sorted(STD_DIR.glob("*.jhyy")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        api_lines = []
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
        if api_lines:
            modules.append({"module": path.stem, "functions": api_lines})
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


def build_markdown(doc, toc, pitfalls, impl, limited, stdlib, example):
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
    A("| `jhyy_lang_ref` | 查语言规范（传章节号最准，如 `\"5.6\"`） | 不确定语法/规则 ⇒ 查目录里那节 |")
    A("| `jhyy_workarounds` | 查已知坑台账（含「已修」和「设计如此」） | 报错看着像编译器 bug ⇒ 查 |")
    A("| `jhyy_abi_info` | 查 ABI（结构体布局 / 调用约定 / FFI） | 涉及 struct 传参 / FFI ⇒ 查 |")
    A("| `jhyy_get_il` | 看编译出来的 IL | 调试 codegen ⇒ 才用 |")
    A("")
    A("⚠️ **`jhyy_check` 一次就返回全部诊断** ⇒ 不要一个错误查一次。")
    A("⚠️ **别顺手改注释、别做额外验证**（不用证明断言非空、不用探测别的边界）——")
    A("　　那些是**任务范围外**的事，做了只会浪费轮数。")
    A("")
    A("## 规范章节目录")
    A("")
    A("查某一节用 `jhyy_lang_ref`，参数传章节号（如 `\"5.6\"` / `\"附录 B\"`）。")
    A("")
    for t in toc:
        num = f"§ {t['num']}" if t["num"] else ""
        A(f"- **{num} {t['title']}**" + (f" —— {t['scope']}" if t.get("scope") else ""))
    A("")

    A("## 反直觉点（规范里标了 ⚠ 的行）")
    A("")
    A("下面每条都是**规范原文标记**的「与直觉/与旧规范不同」之处。")
    A("")
    for p in pitfalls:
        A(f"- {p['text']}  *（{p['section']}）*")
    A("")

    A("## 附录 B：未实装 —— 这些构造编译器会直接拒绝")
    A("")
    for item in impl:
        A(f"- {item['text']}")
    A("")

    A("## 附录 B：已实装但受限 —— 这些能写，但有坑")
    A("")
    for r in limited:
        w = f"（台账 {r['w_ref']}）" if r["w_ref"] else ""
        A(f"- **{r['item']}** —— {r['symptom']} {w}")
    A("")

    A("## 标准库公开 API")
    A("")
    A("导入时写模块名本身（**不带 `std::` 前缀**），调用时直接写完整函数名。")
    A("")
    for m in stdlib:
        A(f"### `{m['module']}`")
        A("")
        for f in m["functions"]:
            ret = f" -> {f['ret']}" if f.get("ret") else ""
            A(f"- `{f['name']}({f['args']})`{ret}")
        A("")

    if example:
        A("## 一段完整的 JHYY 程序（规范附录 D）")
        A("")
        A("```jhyy")
        A(example)
        A("```")
        A("")

    return "\n".join(L) + "\n"


def main():
    if not SPEC_PATH.exists():
        print(f"✗ 找不到规范：{SPEC_PATH}", file=sys.stderr)
        return 1
    if not STD_DIR.exists():
        print(f"✗ 找不到标准库源码：{STD_DIR}", file=sys.stderr)
        return 1

    doc = load_spec()
    toc = collect_toc(doc)
    pitfalls = collect_pitfalls(doc)
    impl, limited = collect_appendix_b(doc)
    stdlib = collect_stdlib()
    example = collect_example(doc)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = build_markdown(doc, toc, pitfalls, impl, limited, stdlib, example)
    with open(OUT_MD, "w", encoding="utf-8", newline="") as f:
        f.write(md)

    payload = {
        "version": doc.get("version", ""),
        "source": str(SPEC_PATH).replace("\\", "/"),
        "toc": toc,
        "pitfalls": pitfalls,
        "unimplemented": impl,
        "limited": limited,
        "stdlib": stdlib,
        "example": example,
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    print(f"✓ {SPEC_PATH.name}（版本 {doc.get('version')}）")
    print(f"  章节目录 {len(toc)} 章")
    print(f"  反直觉点 {len(pitfalls)} 条")
    print(f"  未实装 {len(impl)} 项")
    print(f"  受限 {len(limited)} 行")
    print(f"  标准库 {len(stdlib)} 模块 / {sum(len(m['functions']) for m in stdlib)} 个函数")
    print(f"  完整示例 {'有' if example else '无'}")
    print(f"→ {OUT_MD}")
    print(f"→ {OUT_JSON}")
    print(f"  （markdown {len(md)} 字符）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
