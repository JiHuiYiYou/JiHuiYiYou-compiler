"""test_get_il.py — 回归门:jhyy_get_il 必须真的拿到 IL。

2026-10-27 (W-155):这工具**从来没成功过** ——
编译器默认**不落 .il**(`JHY_WRITE_IL` 未设 ⇒ 只写 .s / .exe),
而 `runner.get_il` 去找 `<output>.il` ⇒ 永远 "IL file not found"。

⇒ 修法:给这次编译加 `JHY_WRITE_IL=1`(只表示「额外落一份 .il 供人检视」,
  不影响 .s / .exe)。

⚠ 这条门要真的调编译器(不是 mock)—— 原来的套件里**没有**任何一条覆盖
jhyy_get_il ⇒ 工具坏了没人知道。
"""
import os
import tempfile

import pytest

# mcp_client fixture from conftest.py


@pytest.mark.asyncio
async def test_get_il_returns_il_text(mcp_client):
    """编一个最小程序 → 工具必须返回非空 IL 文本 + .il 文件路径."""
    with tempfile.TemporaryDirectory() as tmp:
        src = os.path.join(tmp, "il_probe.jhyy")
        with open(src, "w", encoding="utf-8", newline="\n") as f:
            f.write(
                "fn main_jhyy() -> i32 {\n"
                "    let x = 1;\n"
                "    return x;\n"
                "}\n"
            )
        result = await mcp_client.call_tool("jhyy_get_il", {"file": src})
        data = result.data

    assert data["ok"] is True, f"jhyy_get_il 失败: {data.get('stderr', '')[:200]}"
    il = data.get("il", "")
    assert il, "IL 文本为空"
    # IL 里应当能看到函数导出/函数体
    assert "export function" in il or "function" in il, f"IL 不像 IL: {il[:200]}"
    assert data.get("il_file", "").endswith(".il")
