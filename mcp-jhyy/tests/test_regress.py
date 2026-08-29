"""test_regress.py — smoke test for jhyy_regress tool.

验证:
- 调用通过 MCP client 发出, server 返回结构化结果
- 默认 enforce_baseline_hash=True 在 baseline 缺失时给 warning 而非 fail
- subset 跑测试 (tests=[...]) 工作
- binary drifted → early_abort 报告

Sprint mcp-1 (2026-08-11).
"""
import os
from pathlib import Path

import pytest

# mcp_client fixture from conftest.py


@pytest.mark.asyncio
async def test_regress_default_binary(mcp_client):
    """jhyy_regress(binary='compiler/build/bin/jhyy.exe', tests=['hello.jhyy'])"""
    result = await mcp_client.call_tool(
        "jhyy_regress",
        {
            "binary": "compiler/build/bin/jhyy.exe",
            "tests": ["hello.jhyy"],
            "timeout": 15,
            "enforce_baseline_hash": False,  # skip hash check (may not have baseline file)
        },
    )
    data = result.data
    assert data["ok"] is True, f"hello.jhyy should PASS: {data}"
    assert data["total"] == 1
    assert data["passed"] == 1
    assert data["failed"] == 0
    assert "binary_sha256" in data
    assert data["binary"].endswith("jhyy.exe")


@pytest.mark.asyncio
async def test_regress_subprocess_fallback():
    """直接调 jhyy_regress.run_all 验证 run_test 不破 regress baseline (回归保护)."""
    import jhyy_regress as rm
    result = rm.run_all(
        binary="compiler/build/bin/jhyy.exe",
        tests=["hello.jhyy"],
        timeout=15,
        enforce_baseline_hash=False,
    )
    assert result["ok"] is True
    assert result["passed"] >= 1


@pytest.mark.asyncio
async def test_regress_missing_binary_fails(mcp_client):
    """不存在的 binary 应 fail-fast + early_abort 报 'binary not found'."""
    result = await mcp_client.call_tool(
        "jhyy_regress",
        {
            "binary": "compiler/build/bin/__nonexistent_binary__.exe",
            "tests": ["hello.jhyy"],
            "enforce_baseline_hash": False,
        },
    )
    data = result.data
    assert data["ok"] is False
    assert data["early_abort"] is not None
    assert "not found" in data["early_abort"]
    assert data["total"] == 0  # 没跑任何测试 (fail-fast in run_all)


@pytest.mark.asyncio
async def test_regress_baseline_drift_detection(mcp_client):
    """baseline 文件存在但不匹配 → early_abort 报 'binary drifted'.

    Setup: 临时建一个 fake baseline 文件, sha 跟实际 binary 不匹配.
    """
    bin_path = str(Path(__file__).resolve().parents[2] / "compiler/build/bin/jhyy.exe")
    sha_path = bin_path + ".sha256"

    # Backup real baseline if it exists
    backup = None
    if os.path.exists(sha_path):
        backup = sha_path + ".test_backup"
        os.rename(sha_path, backup)

    try:
        # Write fake baseline (definitely doesn't match real binary)
        with open(sha_path, "w", encoding="utf-8") as f:
            f.write("0" * 64 + "\n")

        result = await mcp_client.call_tool(
            "jhyy_regress",
            {
                "binary": "compiler/build/bin/jhyy.exe",
                "tests": ["hello.jhyy"],
                "enforce_baseline_hash": True,
            },
        )
        data = result.data
        assert data["ok"] is False
        assert data["early_abort"] is not None
        assert "binary drifted" in data["early_abort"]
        assert data["baseline_match"] is False
    finally:
        # Restore real baseline (or remove fake)
        if os.path.exists(sha_path):
            os.remove(sha_path)
        if backup is not None and os.path.exists(backup):
            os.rename(backup, sha_path)