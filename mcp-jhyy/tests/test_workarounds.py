"""test_workarounds.py — smoke test for jhyy_workarounds tool.

验证:
- 搜 W-005 → 命中
- 搜 "let mut" → 命中 (含触发模式 workaround)
- status="ACTIVE" filter → 只返 ACTIVE
- 不存在的 query → matches 为空但 ok=True (parse 仍跑)

Sprint mcp-1 (2026-08-11).
"""
import pytest

# mcp_client fixture from conftest.py


@pytest.mark.asyncio
async def test_workarounds_search_w_id(mcp_client):
    """搜 W-005 → 应该命中 W-005 entry."""
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "W-005"},
    )
    data = result.data
    assert data["ok"] is True
    assert data["query"] == "W-005"
    # W-005 必须出现在 matches
    ids = [m["id"] for m in data["matches"]]
    assert "W-005" in ids, f"W-005 not in matches: {ids}"


@pytest.mark.asyncio
async def test_workarounds_search_trigger_pattern(mcp_client):
    """搜 'let mut' → 命中含 let mut 触发的 workaround."""
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "let mut"},
    )
    data = result.data
    assert data["ok"] is True
    # 至少有一个匹配 (W-003 是 let mut 触发)
    assert len(data["matches"]) >= 1


@pytest.mark.asyncio
async def test_workarounds_status_filter_active(mcp_client):
    """status='ACTIVE' → 只返 ACTIVE (v2.13.6 mini 严格 token match).

    Pre-v2.13.6: substring match (W-051 RESOLVED 但 body 写 '强标 ACTIVE 不解决任何 active 问题'
    的 entry 会被误分类到 ACTIVE filter).
    Post-v2.13.6: 严格 first-token match against 5-state enum.
    """
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "W-", "status": "ACTIVE"},
    )
    data = result.data
    assert data["ok"] is True
    for m in data["matches"]:
        assert m["status"].upper().startswith("ACTIVE"), (
            f"Match {m['id']} status={m['status']!r} should start with ACTIVE"
        )


@pytest.mark.asyncio
async def test_workarounds_status_filter_deferred(mcp_client):
    """status='DEFERRED' → 只返 DEFERRED (v2.13.6 mini 5 态新增)."""
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "W-", "status": "DEFERRED"},
    )
    data = result.data
    assert data["ok"] is True
    for m in data["matches"]:
        assert m["status"].upper().startswith("DEFERRED"), (
            f"Match {m['id']} status={m['status']!r} should start with DEFERRED"
        )


@pytest.mark.asyncio
async def test_workarounds_counts(mcp_client):
    """active_count / resolved_count / total 字段填对."""
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "W-"},
    )
    data = result.data
    assert data["ok"] is True
    assert data["total"] >= 5
    assert data["active_count"] >= 0
    assert data["resolved_count"] >= 0


@pytest.mark.asyncio
async def test_workarounds_no_match(mcp_client):
    """不存在 query → matches 为空但 ok=True."""
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "non-existent-pattern-xyz-12345"},
    )
    data = result.data
    assert data["ok"] is True
    assert data["matches"] == []

# ── 2026-10-27 (W-154):工具与索引表必须**条目数一致** ──
#
# 背景:工具的切分口径与 `scripts/dev/v2_13_5_rebuild_index.py` 不一致 ⇒
#   · 工具把「## W-001 RESOLVED — ...」这种**详情节**当成独立条目 ⇒ 同一个
#     W-NNN 被数两次 + 冒出一堆状态为空的幽灵条目(实测 9 个);
#   · 工具只认 `##`(H2)⇒ H3 子条目(W-073..W-080)看不见;
#   · 工具的 alias 表里只有「状态」⇒ 写 `**Status:**`(英文)的条目读不出来。
# ⇒ 结果:工具报 138 条、索引表 142 行,两边对不上,且**幽灵 UNKNOWN** 掩盖了
#   「6 条条目根本没有状态行」这个真问题。
#
# ⇒ 现在两个口径统一(条目 = H2/H3 + 冒号),并加下面这条**一致性门**:
#   工具解析出的条目数 **必须等于** 索引表的行数。


@pytest.mark.asyncio
async def test_workarounds_total_matches_index_table(mcp_client):
    """工具解析出的条目数 == 索引表行数,且没有状态读不出来的条目."""
    import re
    from pathlib import Path

    ledger = Path(__file__).resolve().parents[2] / "docs" / "internal" / "workarounds.md"
    text = ledger.read_text(encoding="utf-8")
    index_rows = len(re.findall(r"^\| \[W-", text, re.M))

    result = await mcp_client.call_tool("jhyy_workarounds", {"query": "W-"})
    data = result.data

    assert data["total"] == index_rows, (
        f"工具条目数 {data['total']} != 索引表行数 {index_rows} "
        f"(两个口径不一致 ⇒ 计数不可信)"
    )
    assert data["unknown_count"] == 0, (
        f"有 {data['unknown_count']} 条状态读不出来(幽灵条目或条目缺状态行): "
        f"{[m['id'] for m in data['matches'] if not m.get('status')][:10]}"
    )
