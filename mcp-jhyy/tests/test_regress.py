"""test_regress.py — smoke test for jhyy_regress tool.

验证:
- 调用通过 MCP client 发出, server 返回结构化结果
- 默认 enforce_baseline_hash=True 在 baseline 缺失时给 warning 而非 fail
- subset 跑测试 (tests=[...]) 工作
- binary 比源旧(phantom binary)→ early_abort 报告;baseline sha 漂移**不**算失败

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
async def test_regress_sha_drift_is_not_fatal(mcp_client):
    """baseline 文件存在但 sha 不匹配 → **不得** fail。

    2026-10-24 修正(这个测试此前**恒红**):它原来断言
    「sha 漂移 ⇒ early_abort 报 'binary drifted'」—— 但那正是 commit
    `f72cef4`(v4.0.20)刻意**换掉**的行为:`.exe` 的 sha 随每次构建漂移
    (build 非确定性),拿它当回归信号是**假信号**;真正的 phantom-binary 信号是
    「binary 比源旧」(新鲜度检查,见下一条 test)。

    ⇒ sha 漂移**不得**导致失败。这条门现在验的是「漂移不误报」
    —— 一道**假阳性**的门比没有门更糟:它训练人忽略红色。
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
        assert data["ok"] is True, f"sha drift must not fail the run: {data}"
        assert data["failed"] == 0
        assert data["early_abort"] is None
    finally:
        # Restore real baseline (or remove fake)
        if os.path.exists(sha_path):
            os.remove(sha_path)
        if backup is not None and os.path.exists(backup):
            os.rename(backup, sha_path)


@pytest.mark.asyncio
async def test_regress_stale_binary_detected(mcp_client):
    """binary 比源旧(phantom binary)→ early_abort 报 'older than source'。

    这才是现在的**真门**(commit `f72cef4` 引入的新鲜度检查):忘了重编就跑
    regress,拿到的是**旧编译器** —— 那种「CI 绿、本地行为却是旧版」的组合
    最难查,必须在跑测试**之前**就拦住。

    Setup: 把 binary 的 mtime 拨到 1 天前 ⇒ 必然比 `compiler/src0/*.jhyy` 旧
    (jhyy.exe 的依赖面是 src0 + runtime,见 `_freshness_src_dirs`)。
    """
    bin_path = str(Path(__file__).resolve().parents[2] / "compiler/build/bin/jhyy.exe")
    st = os.stat(bin_path)
    try:
        os.utime(bin_path, (st.st_atime, st.st_mtime - 86400))

        result = await mcp_client.call_tool(
            "jhyy_regress",
            {
                "binary": "compiler/build/bin/jhyy.exe",
                "tests": ["hello.jhyy"],
                "enforce_baseline_hash": True,
            },
        )
        data = result.data
        assert data["ok"] is False, f"stale binary must be rejected: {data}"
        assert data["early_abort"] is not None
        assert "older than source" in data["early_abort"]
        assert data["total"] == 0  # 一个测试都没跑
    finally:
        os.utime(bin_path, (st.st_atime, st.st_mtime))
