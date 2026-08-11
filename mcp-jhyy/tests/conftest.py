"""conftest.py — 给 tests/ 提供共用 fixture: mcp client."""
import sys
from pathlib import Path

# 让 test_<tool>.py 能 import mcp-jhyy 兄弟模块
MCP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(MCP_DIR))

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from fastmcp import Client  # noqa: E402
import server  # noqa: E402


@pytest_asyncio.fixture
async def mcp_client():
    """Per-test in-memory MCP client connected to server.mcp.

    Uses Client(server.mcp) — FastMCP's in-memory transport, no subprocess.
    """
    client = Client(server.mcp)
    async with client:
        yield client