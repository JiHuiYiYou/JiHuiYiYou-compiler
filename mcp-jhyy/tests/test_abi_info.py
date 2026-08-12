"""test_abi_info.py — jhyy_abi_info 回归测试 (Sprint mcp-2)

之前 jhyy_abi_info 用 atomic substring over abi_data.json — multi-word 自然语言
查询永远 0 命中. 现在用 jhyy_spec_doc 读 locked jhyy-abi-v1.0.0.md, token-AND search.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jhyy_spec_doc


ABI_PATH = Path("C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/docs/abis/jhyy-abi-v1.0.0.md")


def _search(query, limit=20):
    """直接走共享 helper, 模拟 server.py jhyy_abi_info 走的方式."""
    doc = jhyy_spec_doc.load_spec_doc(ABI_PATH)
    return jhyy_spec_doc.search_spec_doc(doc, query, limit=limit)


def test_version_is_locked_v1_0_0():
    r = _search("anything")
    assert r["ok"]
    assert r["version"] == "1.0.0", f"expected locked v1.0.0, got {r['version']!r}"


def test_struct_calling_convention_finds_matches():
    """之前返回 0 matches; 现在应命中 § 4 calling convention."""
    r = _search("struct calling convention")
    assert r["ok"]
    assert len(r["matches"]) >= 1, f"0 matches for 'struct calling convention'"
    # 至少有一个 match 提到 calling convention
    assert any("4" in m["section"] or "calling" in m["title"].lower()
               for m in r["matches"]), \
        f"§ 4 calling convention not found; got {[m['section']+' '+m['title'] for m in r['matches']]}"


def test_sret_finds_section_3_or_4():
    r = _search("sret")
    assert r["ok"]
    assert len(r["matches"]) >= 1
    # sret 应该在返回值传递 (通常 § 3.3 或 § 4 系列)
    assert any("3" in m["section"] or "4" in m["section"]
               for m in r["matches"])


def test_token_and_search_works():
    """Multi-word 必须 token-AND. atomic substring 永远 0 命中."""
    r = _search("how does struct return work")
    assert r["ok"]
    # 至少要命中 struct + return (token "struct", "return", "work")
    sections = [m["section"] for m in r["matches"]]
    assert len(sections) >= 1, f"no matches for 'how does struct return work'"


def test_limit_respected():
    r = _search("calling", limit=5)
    assert r["ok"]
    assert len(r["matches"]) <= 5


def test_empty_query_returns_no_matches():
    r = _search("")
    assert r["ok"]
    assert r["matches"] == []


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
    print(f"\n{'='*50}\n{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)