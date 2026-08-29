"""test_selfhost_check.py — smoke test for jhyy_selfhost_check tool.

注意: selfhost_check 端到端跑 v1→v2→v3 (3 次编译, ~30 秒). smoke test 只验证
fail-fast 路径 (binary 缺失 + 错误 src) 不验证全链路, 全链路留给 regress / 手动跑.

Sprint mcp-1 (2026-08-11).
"""
import os
from pathlib import Path

import pytest

# mcp_client fixture from conftest.py


@pytest.mark.asyncio
async def test_selfhost_check_fail_fast_missing_binary(mcp_client):
    """jhyy_v1.exe 缺失 → fail-fast + clear error."""
    # Setup: rename jhyy_v1.exe.exe 临时避开
    bin_path = str(Path(__file__).resolve().parents[2] / "compiler/build/bin/jhyy_v1.exe.exe")
    backup = bin_path + ".test_backup"
    renamed = False
    if os.path.exists(bin_path):
        os.rename(bin_path, backup)
        renamed = True

    try:
        result = await mcp_client.call_tool(
            "jhyy_selfhost_check",
            {"src": "compiler/src0/main.jhyy", "auto_rebuild": False},
        )
        data = result.data
        assert data["ok"] is False
        assert data["all_byte_equal"] is False
        assert data["early_abort"] is not None
        assert "jhyy_v1" in data["early_abort"] or "not found" in data["early_abort"]
        assert data["binary_chain"] == []
        assert data["il_files"] == {}
    finally:
        if renamed and os.path.exists(backup):
            os.rename(backup, bin_path)


@pytest.mark.asyncio
async def test_selfhost_check_result_schema(mcp_client):
    """完整跑 (跳过 missing-binary 测试) 验证 schema 字段."""
    bin_path = str(Path(__file__).resolve().parents[2] / "compiler/build/bin/jhyy_v1.exe.exe")
    if not os.path.exists(bin_path):
        pytest.skip("jhyy_v1.exe.exe not built — skip end-to-end schema test")

    # Use _repro_t0.jhyy which is known to work (per memory project_v1_0_0_closure).
    repro_src = str(Path(__file__).resolve().parents[2] / "compiler/tests/examples/_repro_t0.jhyy")
    if not os.path.exists(repro_src):
        pytest.skip(f"_repro_t0.jhyy not found at {repro_src}")

    result = await mcp_client.call_tool(
        "jhyy_selfhost_check",
        {"src": repro_src, "auto_rebuild": False, "timeout": 300},
    )
    data = result.data
    # Schema fields should always be present
    assert "ok" in data
    assert "all_byte_equal" in data
    assert "il_sha256" in data
    assert "binary_chain" in data
    assert "il_files" in data
    assert "early_abort" in data
    assert "duration_sec" in data
    # If success, all_byte_equal should be True with common sha
    if data["ok"]:
        assert data["all_byte_equal"] is True
        assert data["il_sha256"] is not None
        assert len(data["binary_chain"]) >= 1
        for stage in data["binary_chain"]:
            assert "stage" in stage
            assert "binary_sha256" in stage
            assert "il_sha256" in stage
            assert "duration_sec" in stage