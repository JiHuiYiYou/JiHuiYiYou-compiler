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
    """status='ACTIVE' → 只返 ACTIVE (substring 匹配).

    Sprint 4.7: workarounds.md 有 ACTIVE / ACTIVE (dormant) / RESOLVED / SUPERSEDED 多种 status.
    """
    result = await mcp_client.call_tool(
        "jhyy_workarounds",
        {"query": "W-", "status": "ACTIVE"},
    )
    data = result.data
    assert data["ok"] is True
    # 所有 matches status 应含 ACTIVE (substring 匹配)
    for m in data["matches"]:
        assert "ACTIVE" in m["status"].upper(), (
            f"Match {m['id']} status={m['status']!r} should contain ACTIVE"
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