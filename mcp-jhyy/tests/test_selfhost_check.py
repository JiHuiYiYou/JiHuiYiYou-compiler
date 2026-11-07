"""test_selfhost_check.py — smoke test for jhyy_selfhost_check tool.

注意: selfhost_check 端到端跑自举链(4 次编译, ~60 秒). smoke test 只验证
fail-fast 路径 (binary 缺失 + 错误 src) 不验证全链路, 全链路留给 regress / 手动跑.

2026-11-07:链改了 —— 旧链引用 `jhyy_v2.exe` / `jhyy_v3.exe`,而这两个文件
**既不在仓里、也不由 make 生成** ⇒ 工具从来没能跑过(W-211)。现在链是
「锚点 → gen1 → gen2 → gen3 → gen4」,锚点默认 `compiler/build/bin/jhyy.exe`。
⇒ 「锚点缺失 ⇒ fail-fast」这条改用 `anchor` 参数指向一个不存在的路径来测 ——
**不用再真的把仓里的产物挪走**(那会动到 git 跟踪的文件)。

Sprint mcp-1 (2026-08-11).
"""
import os
from pathlib import Path

import pytest

# mcp_client fixture from conftest.py


@pytest.mark.asyncio
async def test_selfhost_check_fail_fast_missing_binary(mcp_client):
    """锚点缺失 → fail-fast + clear error."""
    result = await mcp_client.call_tool(
        "jhyy_selfhost_check",
        {
            "src": "compiler/src0/main.jhyy",
            "anchor": "compiler/build/bin/_definitely_missing_anchor.exe",
        },
    )
    data = result.data
    assert data["ok"] is False
    assert data["all_byte_equal"] is False
    assert data["early_abort"] is not None
    assert "not found" in data["early_abort"]
    assert data["binary_chain"] == []
    assert data["il_files"] == {}


@pytest.mark.asyncio
async def test_selfhost_check_result_schema(mcp_client):
    """完整跑 (跳过 missing-binary 测试) 验证 schema 字段."""
    bin_path = str(Path(__file__).resolve().parents[2] / "compiler/build/bin/jhyy.exe")
    if not os.path.exists(bin_path):
        pytest.skip("jhyy.exe not built — skip end-to-end schema test")

    # Use _repro_t0.jhyy which is known to work (per memory project_v1_0_0_closure).
    repro_src = str(Path(__file__).resolve().parents[2] / "compiler/tests/examples/_repro_t0.jhyy")
    if not os.path.exists(repro_src):
        pytest.skip(f"_repro_t0.jhyy not found at {repro_src}")

    result = await mcp_client.call_tool(
        "jhyy_selfhost_check",
        {"src": repro_src, "timeout": 300},
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
