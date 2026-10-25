"""test_lang_ref.py — jhyy_lang_ref 回归测试 (Sprint mcp-2)

之前 jhyy_lang_ref 用 stale spec_data.json (v0.5.0) — multi-word 查询永远 0 命中.
现在用 jhyy_spec_doc.load_spec_doc 读 locked v4.0.0 spec, token-AND search.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jhyy_lang_ref


def test_version_is_locked_v4_0_0():
    r = jhyy_lang_ref.search("anything")
    assert r["ok"]
    assert r["version"] == "4.0.0", f"expected locked v4.0.0, got {r['version']!r}"


def test_struct_pass_by_value_finds_section_8():
    """v4.0.0 重排后,struct 按值传递在 § 8「结构体」(旧 v1.x 是 § 10.4)."""
    r = jhyy_lang_ref.search("struct pass-by-value")
    assert r["ok"]
    assert len(r["matches"]) >= 1, f"0 matches for 'struct pass-by-value'"
    # Best match should be § 8 (结构体) — top score
    top = r["matches"][0]
    assert top["section"] == "8", f"top match should be § 8, got § {top['section']}"
    assert top["score"] >= 2


def test_namespace_finds_section_13():
    """v4.0.0 重排后,模块命名空间在 § 13「模块与导入」(旧 v1.x 是 § 12.4)."""
    r = jhyy_lang_ref.search("命名空间")
    assert r["ok"]
    assert len(r["matches"]) >= 1
    top = r["matches"][0]
    assert top["section"] == "13", f"top match should be § 13, got § {top['section']}"


def test_break_continue_finds_section_5_4():
    """v4.0.0 重排后,break/continue 在 § 5.4(旧 v1.x 是 § 7.3)."""
    r = jhyy_lang_ref.search("break continue")
    assert r["ok"]
    sections = [m["section"] for m in r["matches"]]
    assert "5.4" in sections, f"§ 5.4 break/continue not found; got {sections}"


def test_multi_word_token_and_search():
    """多词查询必须用 token-AND — atomic substring 永远 0 命中."""
    r = jhyy_lang_ref.search("how do I declare a namespace")
    assert r["ok"]
    # 至少要有 namespace 相关的命中 (token "namespace")
    # v4.0.0 的 § 13 标题是「模块与导入」(命名空间一节并入其中)
    assert any("namespace" in m["title"].lower() or "命名空间" in m["title"]
               or "模块" in m["title"]
               for m in r["matches"]), f"namespace match missing; got {[m['title'] for m in r['matches']]}"


def test_empty_query_returns_no_matches():
    r = jhyy_lang_ref.search("")
    assert r["ok"]
    assert r["matches"] == []


def test_limit_respected():
    r = jhyy_lang_ref.search("type", limit=3)
    assert r["ok"]
    assert len(r["matches"]) <= 3


if __name__ == "__main__":
    # CLI smoke test (no pytest dependency)
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)