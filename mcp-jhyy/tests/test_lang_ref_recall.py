"""test_lang_ref_recall.py — 检索的**召回**与**形态**回归测试。

## 现有的 test_lang_ref.py 没盖住什么

它只断言「top1 是某个 section 号」「至少 1 条命中」⇒ **不测**：

- **中文自然语言提问**能不能召回（实测「怎么写命名空间」原来 **0 命中**）
- **按章节号**能不能取到那一节（**错误索引指路的前提** —— 它说「查 § 18」，
  那 `jhyy_lang_ref("18")` 就必须取得到 ⇒ 否则链条断在中间）
- 匹配结果里**有没有完整代码块**（excerpt 只截 240 字符 ⇒ 代码块常被切掉）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jhyy_lang_ref


def test_section_number_lookup():
    """按**章节号**精确取节 ⇒ 这是 jhyy_error_lookup 指路的前提。"""
    r = jhyy_lang_ref.search("18")
    assert r["ok"]
    assert r["matches"], "按章节号查不到 § 18 ⇒ 错误索引指的路是断的"
    top = r["matches"][0]
    assert top["section"] == "18"
    assert top["score"] >= 1000, "章节号精确查的分数应该压过关键词匹配"


def test_section_number_lookup_with_sub_sections():
    """取一章时**连它的子节一起给**（模型要的是「这一章讲了什么」）。

    ⚠️ **不是每一章都有子节** —— § 13 / § 15 / § 18 的内容直接写在章下
    ⇒ 用 § 5（控制流，有 5.1~5.7）来验。
    """
    r = jhyy_lang_ref.search("5")
    nums = [m["section"] for m in r["matches"]]
    assert "5" in nums
    assert len(nums) > 1, f"只有 § 5 自己，没有子节：{nums}"
    assert any(n.startswith("5.") for n in nums), f"没有子节：{nums}"


def test_appendix_lookup():
    """「附录 B」也要能查到（§ B 是「未实装」清单 ⇒ 最值钱的一块）。"""
    r = jhyy_lang_ref.search("附录 B")
    assert r["matches"], "「附录 B」查不到"
    assert r["matches"][0]["section"] == "B"


def test_chinese_natural_language_query():
    """**中文自然语言**提问要能召回。

    ⚠️ 实测（2026-11-13）：分词只按空白+ASCII 标点切 ⇒ 中文整串成一个 token
    ⇒ 「怎么写命名空间」在正文里不存在 ⇒ **0 命中**。
    ⇒ 现在中文连续串切 bigram ⇒ 命中得到。
    """
    r = jhyy_lang_ref.search("怎么写命名空间")
    assert r["matches"], "中文自然语言提问 0 命中 ⇒ 分词没切 bigram"
    assert any(m["section"] == "13" for m in r["matches"]), (
        "应该命中 § 13「模块与导入」，实际：%s" % [(m["section"], m["title"]) for m in r["matches"]]
    )


def test_chinese_query_scores_better_than_before():
    """中文查询的分数要比「只有一条弱命中」高（CN→EN 反向别名加成）。"""
    r = jhyy_lang_ref.search("命名空间")
    assert r["matches"]
    assert r["matches"][0]["section"] == "13"
    # 之前是 1 条命中 score 6 ⇒ 现在 top 至少 9（反向别名给了 namespace 的加成）
    assert r["matches"][0]["score"] >= 9, "中文查询的 top 分没涨：%s" % r["matches"][0]["score"]


def test_matches_carry_full_body():
    """匹配结果要带**整节正文**（excerpt 只截 240 字符 ⇒ 代码块常被切掉）。"""
    r = jhyy_lang_ref.search("命名空间")
    assert r["matches"]
    top = r["matches"][0]
    assert top.get("body"), "没有整节正文 ⇒ 代码块拿不到"
    assert len(top["body"]) > len(top.get("excerpt", "")), "body 比 excerpt 还短 ⇒ 没整节"


def test_body_only_for_top_matches():
    """整节正文**只给 top 3** ⇒ 否则一次调用能吐 80k 字符 ⇒ 白吃上下文。"""
    r = jhyy_lang_ref.search("type", limit=20)
    assert len(r["matches"]) > 3, "这个查询命中不足 4 条 ⇒ 测不了 top-3 限制"
    with_body = [m for m in r["matches"] if m.get("body")]
    assert len(with_body) <= 3, "带整节的超过 3 条：%d" % len(with_body)
