"""test_error_lookup.py — jhyy_error_lookup 的回归测试。

## 为什么这个工具要有

评测的**语言对照**（同一 AST 的 C 实现 vs JHYY 实现，29 对）测出来的结论：
「少声明」「格式符错」这两类错在 JHYY 上**多 5~8 轮** ⇒ 根因是
**C 的编译器报错自带修复线索**（`implicit declaration of function 'printf'`），
而 JHYY 只说「undefined variable printf」⇒ 模型得自己查规范才知道怎么改。

⇒ 这个索引做的就是那一步翻译：**报错原文 → 含义 / 修法 / 该查哪一节 / 台账编号**。

## 这些测试守的**不是**「索引有多少条」

而是「**用户拿编译器打印的原文来查，能不能查到**」——
⚠️ 这一点很容易被做坏：规范 § 18 的报错原文是**反引号包着**的
（`` `unexpected token ';' in expression` ``）⇒ 归一化时忘了去反引号，
用户拿着编译器打印的**裸文本**来查就**匹配不上**（2026-11-13 实测踩过）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import jhyy_errors


def test_index_is_not_empty():
    """索引得非空 —— 编译器 + 规范 + 语料 + 台账 四个来源都得抽到东西。"""
    index = jhyy_errors.build_index()
    assert len(index) > 50, f"索引只有 {len(index)} 条 ⇒ 抽不动了"
    kinds = {e.get("kind") for e in index.values()}
    assert "sema" in kinds, f"没抽到 sema 的诊断：{kinds}"
    assert "parse" in kinds, f"没抽到 parser 的诊断：{kinds}"
    assert "corpus" in kinds, f"没抽到语料实测的报错：{kinds}"
    assert "spec" in kinds, f"没抽到规范的条目：{kinds}"


def test_lookup_type_mismatch():
    """最常见的一类：类型不匹配。"""
    r = jhyy_errors.search("type mismatch in let")
    assert r["ok"]
    assert r["matches"], "0 命中"
    assert r["matches"][0]["text"].startswith("type mismatch in let")


def test_lookup_unexpected_token_semicolon():
    """`type` 声明后多写了 `;` ⇒ 规范 § 18 的高频文本表里有它。

    ⚠️ **这条是「裸文本」查** —— 规范里的原文是**反引号包着**的
    ⇒ 归一化忘了去反引号就查不到（2026-11-13 实测踩过）。
    """
    r = jhyy_errors.search("unexpected token ';' in expression")
    assert r["matches"], "0 命中"
    top = r["matches"][0]
    assert top["text"] == "unexpected token ';' in expression"
    # 含义 + 章节
    assert top.get("meaning"), "没有含义"
    assert top.get("spec_ref"), "没有章节引用"


def test_lookup_returns_fix_and_ledger_ref():
    """聚合比较的报错 ⇒ 附录 B 里有**修法** + 台账编号。

    这是这个工具最有价值的场景：报错文本本身看不出怎么改，但附录 B 写了
    「把结果先落进变量再比」⇒ 还能顺带给出 W-133.2。
    """
    r = jhyy_errors.search(
        "ordering comparison of a function call result is not supported for aggregate types"
    )
    assert r["matches"], "0 命中"
    blob = " ".join(
        "%s %s" % (m.get("meaning", ""), m.get("fix", "")) for m in r["matches"]
    )
    assert "变量" in blob, f"没有给出「落进变量再比」的修法：{blob[:200]}"
    assert any(m.get("w_ref") for m in r["matches"]), "没有关联台账条目"


def test_lookup_accepts_full_diagnostic_line():
    """整行诊断（带路径 + 行列号 + error: 前缀）也得能查到。"""
    line = r"C:\Users\me\proj\main.jhyy:12:5: error: unexpected token ';' in expression"
    r = jhyy_errors.search(line)
    assert r["matches"], "整行诊断查不到 ⇒ 归一化没剥掉路径前缀"
    assert r["matches"][0]["text"] == "unexpected token ';' in expression"


def test_lookup_immutable_variable():
    r = jhyy_errors.search("cannot assign to immutable variable (use let mut)")
    assert r["matches"], "0 命中"
    assert any(m.get("spec_ref") for m in r["matches"])


def test_unknown_error_returns_no_matches():
    """查不到就**老实返回空** —— 别瞎猜一个意思。"""
    r = jhyy_errors.search("zzz-this-is-not-a-real-jhyy-error-9999")
    assert r["ok"]
    assert not r["matches"], f"不该有命中：{r['matches']}"


@pytest.mark.asyncio
async def test_tool_is_reachable_through_mcp_client(mcp_client):
    """**走 server 层**（不绕过）—— 现有的 test_abi_info.py 直接调模块 ⇒
    server 层零覆盖 ⇒ 工具压根没注册也不会被发现（2026-11-13 实测过这个洞）。"""
    result = await mcp_client.call_tool("jhyy_error_lookup", {"error": "type mismatch in let"})
    data = result.data
    assert data["ok"]
    assert data["matches"], "通过 MCP 调不到（工具没注册？）"
