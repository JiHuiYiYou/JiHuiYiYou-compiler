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

def build_markdown(doc, toc, pitfalls, impl, limited, stdlib, example, error_lookup):
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
    example = collect_example(doc)
    error_lookup = collect_error_lookup(doc)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = build_markdown(doc, toc, pitfalls, impl, limited, stdlib, example, error_lookup)
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
        "error_lookup": error_lookup,
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    print("✓ %s（版本 %s）" % (SPEC_PATH.name, doc.get("version")))
    print("  章节目录 %d 章" % len(toc))
    print("  反直觉点 %d 条" % len(pitfalls))
    print("  未实装 %d 项" % len(impl))
    print("  受限 %d 行" % len(limited))
    print("  标准库 %d 模块 / %d 个函数"
          % (len(stdlib), sum(len(m["functions"]) for m in stdlib)))
    print("  完整示例 %s" % ("有" if example else "无"))
    print("  常见报错速查 %d 条" % len(error_lookup))
    print("→ %s" % OUT_MD)
    print("→ %s" % OUT_JSON)
    print("  （markdown %d 字符）" % len(md))
    return 0


if __name__ == "__main__":
    sys.exit(main())
