r"""test_env.py — subprocess env 构造器的**单一来源**门。

2026-10-27 (W-156):`jhyy_runner.py` 与 `jhyy_regress.py` 原来各有一份
`_build_subprocess_env()`,两份**分叉**了:

  · runner 那份:强制 Windows-style PATH + 把 `C:\msys64\ucrt64\bin` 提到头;
  · regress 那份:**完全不碰 PATH**。

⇒ MCP server 启动时若 env 缺 ucrt64,regress 跑编译器就会挑到**错的 gcc**
⇒ `windres` 预处理失败 ⇒ **207/277 个测试全挂**(CLI 直跑却正常,因为继承的是
用户 shell 的 PATH ⇒ 同一个二进制、同一个 harness,两条路径一个绿一个红)。

⇒ 修法:抽成唯一实现 `jhyy_env.py`,两个模块都 import 成**真别名**。

⚠ 第二条纪律(也是 2026-10-27 踩的):PATH 只许**追加**、**不许替换** ——
CI(setup-msys2)把 MSYS2 装在 `$RUNNER_TEMP\msys64`,真正的 ucrt64 在**那里**;
第一版「MSYS 形式 ⇒ 整个替换成 Windows fallback」把 CI 弄红了 207 个测试
(每个都报 `W-132: windres failed`)。⇒ 本门守住「继承来的 PATH 一个字都不能丢」。
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
    """env 里没有 ucrt64 时,构造器必须把 Windows 形式的 MSYS2 目录**追加**进去
    (否则挑到错的 gcc ⇒ windres 预处理失败 ⇒ 链接类测试全挂)。"""
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


def test_inherited_path_is_preserved():
    """继承来的 PATH **一个字符都不能丢** ——
    CI 上真正的 MSYS2 在 `$RUNNER_TEMP\\msys64`(不在 C:\\msys64)⇒
    整个替换 ⇒ windres 找不到 ⇒ 207/277 个测试全挂(2026-10-27 实测)。"""
    saved = dict(os.environ)
    try:
        os.environ.clear()
        inherited = r"C:\Users\runneradmin\AppData\Local\Temp\msys64\ucrt64\bin;C:\Windows"
        os.environ.update({
            "SystemRoot": r"C:\Windows",
            "SystemDrive": "C:",
            "PATH": inherited,
        })
        env = jhyy_env.build_subprocess_env()
    finally:
        os.environ.clear()
        os.environ.update(saved)
    assert env["PATH"].startswith(inherited), "继承来的 PATH 被改动了 ⇒ CI 会找不到真正的 MSYS2"
    assert r"C:\msys64\ucrt64\bin" in env["PATH"], "兜底的 Windows 形式 MSYS2 目录没追加"


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
