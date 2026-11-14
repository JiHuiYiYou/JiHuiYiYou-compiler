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


# ── 2026-11-13 新增：人工校订层 + `lookup()` ──────────────────────
#
# ⚠️ **为什么加这一层** —— 自动扫出来的 166 条里 `fix` 只有 8 条
#   ⇒ 模型拿到诊断**大概率还是不知道该改哪儿**。
#   而评测量出来的诊断面**极小**（29 道配对任务里只有 1 种结构化诊断
#   + 1 种链接期失败）⇒ ⇒ **为最高频的那几条手写「怎么改」是划算的**。


@pytest.mark.parametrize(
    "message, must_contain",
    [
        # ⚠️ **这三条是评测任务集里真正出现过的** ⇒ 缺一条就等于评测跑不动
        ("undefined variable", "printf"),
        ("type mismatch in let", "as"),
        ("unexpected token ';' in expression", "struct"),
    ],
)
def test_lookup_has_a_fix(message, must_contain):
    """`lookup()` 得给出**可执行的修法**，不是「这是什么意思」。

    ⚠️ **判据是「修法里有没有那句话」** —— 光有 `meaning` 不算。
    """
    hit = jhyy_errors.lookup(message)
    assert hit is not None, f"查不到：{message}"
    assert hit.get("fix"), f"没有 fix：{message} ⇒ {hit}"
    assert must_contain in hit["fix"], (
        f"fix 里没有「{must_contain}」：{message} ⇒ {hit['fix']}"
    )


def test_lookup_prefers_the_entry_that_has_a_fix():
    """同一个原文有多条条目 ⇒ **优先带 `fix` 的**。

    ⚠️ **实测踩过**：台账那条的 `meaning` 是「两种写法都编译不过:」
       ⇒ 对模型**毫无用处** ⇒ 宁可给校订层那条。
    """
    index = jhyy_errors.build_index()
    dupes = [e for e in index.values() if e.get("text") == "undefined variable"]
    assert dupes, "「undefined variable」不在索引里"
    hit = jhyy_errors.lookup("undefined variable")
    assert hit.get("fix"), "选中的条目没有 fix"


def test_lookup_returns_none_for_garbage():
    """**无关的查询必须查不到** —— 瞎猜比不给更糟。"""
    assert jhyy_errors.lookup("zzz-this-is-not-a-real-jhyy-error-9999") is None


def test_lookup_accepts_a_full_diagnostic_line():
    """用户可能直接粘**整行诊断** ⇒ 路径/前缀都得去掉。"""
    hit = jhyy_errors.lookup(
        r"C:\tmp\main.jhyy:12:5: error: undefined variable"
    )
    assert hit is not None, "整行诊断查不到"
    assert hit.get("fix"), "整行诊断查到了但没有 fix"


def test_check_syntax_enriches_diagnostics():
    """`jhyy_check` 的诊断**要顺带带上修法**。

    ⚠️ **为什么**：评测测出 PostToolUse hook 注入「哪里错」时
       模型被拽去「照诊断改」⇒ **省了 20% 轮数却掉了 10% 正确率**
       ⇒ 诊断里**直接带上「怎么改」** ⇒ 不用多调一次工具。
    """
    import jhyy_runner

    errors = jhyy_runner._enrich_diagnostics(
        [{"file": "main.jhyy", "line": 12, "col": 5, "message": "undefined variable"}]
    )
    assert len(errors) == 1
    assert errors[0].get("fix"), f"诊断没带上修法：{errors[0]}"


def test_check_syntax_enrichment_keeps_unknown_errors_untouched():
    """查不到就**原样返回** —— 不要瞎猜一个意思。"""
    import jhyy_runner

    orig = [{"file": "main.jhyy", "line": 1, "col": 1, "message": "zzz-not-real-9999"}]
    out = jhyy_runner._enrich_diagnostics([dict(e) for e in orig])
    assert out[0]["message"] == "zzz-not-real-9999"
    assert not out[0].get("fix"), "不该给无关报错编一个 fix"
