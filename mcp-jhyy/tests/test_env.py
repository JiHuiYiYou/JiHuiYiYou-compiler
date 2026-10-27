r"""test_env.py — subprocess env 构造器的**单一来源**门。

2026-10-27 (W-156):`jhyy_runner.py` 与 `jhyy_regress.py` 原来各有一份
`_build_subprocess_env()`,两份**分叉**了:

  · runner 那份:强制 Windows-style PATH + 把 `C:\msys64\ucrt64\bin` 提到头;
  · regress 那份:**完全不碰 PATH**。

⇒ MCP server 启动时若 env 缺 ucrt64,regress 跑编译器就会挑到**错的 gcc**
⇒ `windres` 预处理失败 ⇒ **207/277 个测试全挂**(CLI 直跑却正常,因为继承的是
用户 shell 的 PATH ⇒ 同一个二进制、同一个 harness,两条路径一个绿一个红)。

⇒ 现在两份实现都在 `jhyy_env.py` 里,本门守住「不再分叉」+「受限 env 下
PATH 仍含 ucrt64」。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import jhyy_env  # noqa: E402
import jhyy_regress  # noqa: E402
import jhyy_runner  # noqa: E402


def test_both_modules_use_the_shared_builder():
    """runner 与 regress 必须用**同一个** env 构造器(不能各写一份)。"""
    assert jhyy_runner._build_subprocess_env is jhyy_env.build_subprocess_env
    assert jhyy_regress._build_subprocess_env is jhyy_env.build_subprocess_env


def test_restricted_env_still_gets_ucrt64_in_path():
    """env 里没有 ucrt64 时,构造器必须把它补进 PATH(否则挑到错的 gcc)。"""
    saved = dict(os.environ)
    try:
        os.environ.clear()
        os.environ.update({
            "SystemRoot": r"C:\Windows",
            "SystemDrive": "C:",
            "PATH": r"C:\Windows\System32;C:\Windows",
        })
        env = jhyy_env.build_subprocess_env()
    finally:
        os.environ.clear()
        os.environ.update(saved)
    assert r"C:\msys64\ucrt64\bin" in env["PATH"], env["PATH"]
    assert not env["PATH"].startswith("/"), "PATH 必须是 Windows 形式(MSYS 的 /c/... cmd.exe 不认)"


def test_critical_vars_present():
    """TMP/TEMP/SystemRoot 缺了要补(gcc 的 collect2 缺 tmp dir 会静默 exit 1)。"""
    saved = dict(os.environ)
    try:
        for k in ("TMP", "TEMP", "TMPDIR", "SystemRoot", "SystemDrive"):
            os.environ.pop(k, None)
        env = jhyy_env.build_subprocess_env()
    finally:
        os.environ.clear()
        os.environ.update(saved)
    for k in ("TMP", "TEMP", "SystemRoot", "SystemDrive"):
        assert env.get(k), f"{k} 没补上"
