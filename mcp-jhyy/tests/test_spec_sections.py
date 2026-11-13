"""test_spec_sections.py — 规范索引的**章节级**可达性回归测试。

## 为什么单独一个文件

`test_lang_ref.py` 测的是「按关键词能不能搜到某个子节」。
这个文件测的是**另一件事**：**章（h2）本身在不在索引里**。

## 它守的是 W-225

规范的组织方式是「章（h2）只做标题，内容全在子节（h3）」⇒
章的 body 是空串 ⇒ 分节器若「正文为空就跳过」，**整段章会消失**。

⇒ 后果：**按章标题查规范查不到** ——
而这正是 AI 最自然的查法（「程序结构是什么」「指针与借用怎么写」）。
实测旧代码 `search("程序结构")` → **0 命中**。

⇒ 这个门必须能红：把 `jhyy_spec_doc.load_spec_doc` 的 flush 改回旧行为
（「正文为空就跳过」）⇒ 下面第一个测试必红。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jhyy_lang_ref
from jhyy_spec_doc import load_spec_doc

SPEC_PATH = Path(__file__).resolve().parents[2] / "docs" / "abis" / "jhyy-lang-spec-v4.0.0.md"


def test_all_top_level_chapters_are_indexed():
    """24 个章（h2 + 附录 + Cross-ref）必须**全部**在索引里（W-225）。"""
    doc = load_spec_doc(SPEC_PATH)
    chapters = [s for s in doc["sections"] if s["level"] == 2]
    assert len(chapters) >= 24, (
        f"索引里只剩 {len(chapters)} 个章（应 ≥24）⇒ "
        f"「正文为空的 section 被丢弃」那个 bug 回来了（W-225）"
    )
    nums = {s["num"] for s in chapters}
    # 规范里编号章 1..20 + 附录 A/B/C/D + Cross-ref
    for n in [str(i) for i in range(1, 21)]:
        assert n in nums, f"§ {n} 不在索引里 ⇒ W-225 回来了"
    for a in ["A", "B", "C", "D"]:
        assert a in nums, f"附录 {a} 不在索引里 ⇒ W-225 回来了"


def test_searching_by_chapter_title_finds_that_chapter():
    """按**章标题**查 ⇒ 必须命中该章本身（不是 0 命中）。"""
    cases = [
        ("程序结构", "1"),
        ("类型系统", "2"),
        ("控制流", "5"),
        ("指针与借用", "7"),
        ("结构体", "8"),
        ("数组与切片", "10"),
    ]
    for query, expect_num in cases:
        r = jhyy_lang_ref.search(query)
        assert r["ok"]
        nums = [m["section"] for m in r["matches"]]
        assert expect_num in nums, (
            f"按章标题查 {query!r} 没命中 § {expect_num} ⇒ W-225 回来了；"
            f"实得 {nums}"
        )


def test_chapter_search_ranks_the_chapter_first():
    """章标题的精确匹配应当**排第一**（不然查到的还是子节，等于没修好）。"""
    r = jhyy_lang_ref.search("程序结构")
    assert r["matches"], "0 matches for '程序结构'"
    top = r["matches"][0]
    assert top["section"] == "1", f"top match should be § 1, got § {top['section']}"


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{'=' * 50}\n{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
