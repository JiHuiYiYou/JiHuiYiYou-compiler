#!/usr/bin/env python3
"""jhyy_env.py — MCP 各模块**共用**的 subprocess env 构造器。

2026-10-27 (W-156) 新增。此前 `jhyy_runner.py` 与 `jhyy_regress.py` 各有**一份**
`_build_subprocess_env()`,两份**分叉**了:

  · `jhyy_runner.py` 那份:**强制 Windows-style PATH** + 把 `C:\\msys64\\ucrt64\\bin`
    提到 PATH 头(注释写明:MSYS bash 下 `/c/...` 格式的 PATH 传给 jhyy.exe 内部的
    cmd.exe 会坏 ⇒ gcc/cc1/as/ld 找不到 ⇒ "gcc link failed");
  · `jhyy_regress.py` 那份:**完全不碰 PATH**(注释说「jhyy.exe 自己负责探测 gcc 路径」)。

⇒ 分叉的后果:CLI `python regress.py` 继承的是用户 shell 的 PATH ⇒ 正常;
**MCP server 启动时若 env 里没有 ucrt64** ⇒ regress 跑编译器时挑到**错的 gcc**
⇒ `windres` 预处理失败 ⇒ **207/277 个测试全挂**(而 `jhyy_run` 走的是 runner 那份
⇒ 正常 ⇒ 同一个编译器、同一个二进制,两条路径一个绿一个红)。

⇒ 现在**只有这一份实现**,两个模块都从这儿取 ⇒ 不会再分叉。
"""
import os
import tempfile


def build_subprocess_env() -> dict:
    """构造 subprocess env(Windows 友好)。

    要点:
    · TMP / TEMP / TMPDIR / SystemRoot / SystemDrive 缺了要补(gcc 的 collect2
      需要 tmp dir;缺了会**静默 exit 1**);
    · **PATH 只「追加」,绝不「替换」**:
        - 继承来的 PATH **必须保留** —— CI(setup-msys2)把 MSYS2 装在
          `$RUNNER_TEMP\\msys64`,真正的 ucrt64 在**那里**;一旦整个替换掉,
          windres 就找不到 ⇒ 每个要链 .exe 的测试都挂(W-132 icon embedding
          failed)。2026-10-27 实测踩过:第一版「MSYS 形式 ⇒ 整个替换成
          Windows fallback」把 CI 弄红了 207 个测试。
        - 末尾**追加**一份 Windows 形式的 MSYS2 目录作为**兜底**:MSYS bash 起的
          MCP server 继承到的 PATH 可能是 `/c/...` 形式,那种路径 jhyy.exe 内部的
          cmd.exe 不认 ⇒ gcc/cc1/as/ld/windres 找不到 ⇒ "gcc link failed"。
          追加(而不是替换)⇒ 两种环境都能用。
    """
    default_tmp = tempfile.gettempdir()
    env = os.environ.copy()
    if not env.get("TMP"):
        env["TMP"] = default_tmp
    if not env.get("TEMP"):
        env["TEMP"] = default_tmp
    if not env.get("TMPDIR"):
        env["TMPDIR"] = default_tmp
    # Windows 形式的 MSYS2 目录(gcc/cc1/as/ld/windres 都在那儿)—— 追加在**末尾**
    win_fallback = r"C:\Windows\System32;C:\Windows;C:\msys64\ucrt64\bin;C:\msys64\usr\bin"
    if env.get("PATH"):
        env["PATH"] = env["PATH"] + ";" + win_fallback
    else:
        env["PATH"] = win_fallback
    if not env.get("SystemRoot"):
        env["SystemRoot"] = r"C:\Windows"
    if not env.get("SystemDrive"):
        env["SystemDrive"] = "C:"
    return env
