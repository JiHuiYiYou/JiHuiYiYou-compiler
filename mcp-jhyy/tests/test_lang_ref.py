"""test_lang_ref.py — jhyy_lang_ref 回归测试 (Sprint mcp-2)

之前 jhyy_lang_ref 用 stale spec_data.json (v0.5.0) — multi-word 查询永远 0 命中.
现在用 jhyy_spec_doc.load_spec_doc 读 locked v1.1.0 spec, token-AND search.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jhyy_lang_ref


def test_version_is_locked_v1_1_0():
    r = jhyy_lang_ref.search("anything")
    assert r["ok"]
    assert r["version"] == "1.1.0", f"expected locked v1.1.0, got {r['version']!r}"


def test_struct_pass_by_value_finds_section_10_4():
    """之前返回 1 个 v0.4.0 changelog entry; 现在应命中 spec § 10.4."""
    r = jhyy_lang_ref.search("struct pass-by-value")
    assert r["ok"]
    assert len(r["matches"]) >= 1, f"0 matches for 'struct pass-by-value'"
    # Best match should be § 10.4 (struct 按值传递) — top score
    top = r["matches"][0]
    assert "10.4" in top["section"], f"top match should be § 10.4, got § {top['section']}"
    assert top["score"] >= 2


def test_namespace_finds_section_12_4():
    r = jhyy_lang_ref.search("命名空间")
    assert r["ok"]
    assert len(r["matches"]) >= 1
    top = r["matches"][0]
    assert "12.4" in top["section"], f"top match should be § 12.4, got § {top['section']}"


def test_break_continue_finds_section_7_3():
    r = jhyy_lang_ref.search("break continue")
    assert r["ok"]
    sections = [m["section"] for m in r["matches"]]
    assert "7.3" in sections, f"§ 7.3 break/continue not found; got {sections}"


def test_multi_word_token_and_search():
    """多词查询必须用 token-AND — atomic substring 永远 0 命中."""
    r = jhyy_lang_ref.search("how do I declare a namespace")
    assert r["ok"]
    # 至少要有 namespace 相关的命中 (token "namespace")
    assert any("namespace" in m["title"].lower() or "命名空间" in m["title"]
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