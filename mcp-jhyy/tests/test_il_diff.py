"""test_il_diff.py — smoke test for jhyy_il_diff tool.

验证:
- 相同内容两个 .il → byte_equal=True
- 改一行 → byte_equal=False + first_diff_line + first_diff_context
- 不存在文件 → ok=False + error

Sprint mcp-1 (2026-08-11).
"""
import os
import tempfile

import pytest

# mcp_client fixture from conftest.py


@pytest.mark.asyncio
async def test_il_diff_byte_equal(mcp_client):
    """相同内容的两个 .il → byte_equal=True."""
    with tempfile.TemporaryDirectory() as tmp:
        a_path = os.path.join(tmp, "a.il")
        b_path = os.path.join(tmp, "b.il")
        content = "export function w $main() {\n@start\n@body\n  ret 0\n}\n"
        # Use newline='' to avoid Windows CRLF translation (per memory feedback_qbe_crlf_root_cause)
        with open(a_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        with open(b_path, "w", encoding="utf-8", newline="") as f:
            f.write(content)

        result = await mcp_client.call_tool(
            "jhyy_il_diff",
            {"file_a": a_path, "file_b": b_path},
        )
    data = result.data
    assert data["ok"] is True
    assert data["byte_equal"] is True
    assert data["sha256_a"] == data["sha256_b"]
    assert data["first_diff_line"] is None
    assert data["first_diff_context"] is None
    # 5 lines: "{", "@start", "@body", "  ret 0", "}"
    assert data["line_count_a"] == 5


@pytest.mark.asyncio
async def test_il_diff_one_line_diff(mcp_client):
    """一行不同 → byte_equal=False + first_diff_line 指向差异行 + ±context diff."""
    with tempfile.TemporaryDirectory() as tmp:
        a_path = os.path.join(tmp, "a.il")
        b_path = os.path.join(tmp, "b.il")
        # Use newline='' to avoid Windows CRLF translation
        with open(a_path, "w", encoding="utf-8", newline="") as f:
            f.write("line1\nline2 original\nline3\nline4\nline5\n")
        with open(b_path, "w", encoding="utf-8", newline="") as f:
            f.write("line1\nline2 modified\nline3\nline4\nline5\n")

        result = await mcp_client.call_tool(
            "jhyy_il_diff",
            {"file_a": a_path, "file_b": b_path},
        )
    data = result.data
    assert data["ok"] is True
    assert data["byte_equal"] is False
    assert data["sha256_a"] != data["sha256_b"]
    assert data["first_diff_line"] == 2  # line2 differs
    assert data["first_diff_context"] is not None
    # ±3 context should include both line2 difference and some surrounding lines
    assert "-line2 original" in data["first_diff_context"]
    assert "+line2 modified" in data["first_diff_context"]


@pytest.mark.asyncio
async def test_il_diff_missing_file(mcp_client):
    """不存在的文件 → ok=False + error."""
    with tempfile.TemporaryDirectory() as tmp:
        a_path = os.path.join(tmp, "missing_a.il")
        b_path = os.path.join(tmp, "missing_b.il")

        result = await mcp_client.call_tool(
            "jhyy_il_diff",
            {"file_a": a_path, "file_b": b_path},
        )
    data = result.data
    assert data["ok"] is False
    assert "file_a not found" in data["error"]


@pytest.mark.asyncio
async def test_il_diff_size_and_line_counts(mcp_client):
    """size_bytes + line_count 字段填对."""
    with tempfile.TemporaryDirectory() as tmp:
        a_path = os.path.join(tmp, "a.il")
        b_path = os.path.join(tmp, "b.il")
        a_content = "abc\ndef\n"
        b_content = "abc\ndef\nghi\n"
        # Use newline='' to avoid Windows CRLF translation (per memory feedback_qbe_crlf_root_cause)
        with open(a_path, "w", encoding="utf-8", newline="") as f:
            f.write(a_content)
        with open(b_path, "w", encoding="utf-8", newline="") as f:
            f.write(b_content)

        result = await mcp_client.call_tool(
            "jhyy_il_diff",
            {"file_a": a_path, "file_b": b_path},
        )
    data = result.data
    assert data["ok"] is True
    assert data["byte_equal"] is False
    assert data["size_bytes_a"] == len(a_content.encode())
    assert data["size_bytes_b"] == len(b_content.encode())
    # splitlines(keepends=True): "abc\ndef\n" → 2 lines, "abc\ndef\nghi\n" → 3 lines
    assert data["line_count_a"] == 2
    assert data["line_count_b"] == 3