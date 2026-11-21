#!/usr/bin/env python3
"""刷**所有派生产物** —— 一条命令，提交前跑一次就够。

## 派生产物是什么

= **从源码树算出来的、但要进仓**的文件（人看得到的产物，不是构建中间物）。

| 产物 | 生成器 | 什么时候会过期 |
|---|---|---|
| 语言构成（`langstat.json` / 两个 svg / **FACTS.md § 7** / 两份 README 的那一行） | `scripts/dev/langstat.py` | 任何**被计数的源码**变了（行数变了） |
| 知识包（`jhyy-knowledge.md` + `.json` + 报错速查 `.json` + **FACTS.md § 8.1 那一段**） | `scripts/gen-knowledge.py` | 规范 / 标准库 / 报错索引变了 |

## 为什么要有这个脚本

这两样产物**改源码就得跟着刷**，忘了 ⇒ CI 的 `langstat` / `gen-knowledge`
门红 —— 但那是**推送之后**才发现 ⇒ 一轮白等 + 一次返工。

⇒ 把它接进 **pre-commit 钩子**（`.githooks/pre-commit`）⇒ 忘了也不会漏。

## 用法

    python scripts/dev/refresh-artifacts.py            # 按需刷（只刷「触发条件」满足的）
    python scripts/dev/refresh-artifacts.py --all      # 全部刷一遍
    python scripts/dev/refresh-artifacts.py --check    # 只查，不改（= CI 那道门）

⚠️ **钩子会改暂存区**：刷完把产物 `git add` 进去 ⇒ 提交里就带着刷好的产物
（钩子会**打印**它动了哪些文件 ⇒ 不是黑箱）。
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


# ── 派生产物登记表 ──────────────────────────────────────────────────
# ⚠️ **触发条件**是 glob 列表 ⇒ 改了**输入**才刷 ⇒ 便宜的检查不会被白跑。
#   `outputs` = 刷完要 `git add` 的文件。
REFRESHERS = [
    {
        "name": "语言构成（langstat）",
        "check": [sys.executable, "scripts/dev/langstat.py", "--check"],
        "regen": [sys.executable, "scripts/dev/langstat.py"],
        # ⚠️ **langstat 数的是「代码行数」** ⇒ 任何被计数的源文件变了都可能
        #   改数 ⇒ 触发面广。但 `--check` 只要 ~1 秒 ⇒ 干脆**每次都查**。
        "triggers": ["*"],  # = 总是查（check 便宜）
        "outputs": [
            "docs/internal/langstat.json",
            "docs/internal/langstat.svg",
            "docs/internal/langstat-dark.svg",
            "docs/internal/FACTS.md",      # ← § 7 那一节（⚠️ 容易漏 add！）
            "README.md",                     # ← 「语言构成」那一行
            "README.zh-CN.md",               # ← 同上
        ],
    },
    {
        "name": "知识包（gen-knowledge）",
        "check": [sys.executable, "scripts/gen-knowledge.py", "--check"],
        "regen": [sys.executable, "scripts/gen-knowledge.py"],
        # ⚠️ `--check` 要 **~20 秒**（它真编译每段用法示例）⇒ 不能每次都跑
        #   ⇒ 只在**它的输入**变了时跑。
        "triggers": [
            "docs/abis/*",
            # ⚠️ 2026-11-15 补:台账也是知识包的输入 ——
            #   `jhyy-error-fix.json` 由 `mcp-jhyy/jhyy_errors.py` 的**五个只读来源**
            #   合出来,其中一个就是**台账**(workarounds.md)⇒ 台账里新增/修改条目
            #   会改报错索引 ⇒ 不刷 ⇒ CI 的 gen-knowledge 门当场红。
            #   (踩坑实录:W-232 登记那天,钩子只刷了 langstat,知识包没刷 ⇒ CI 红。)
            "docs/internal/workarounds.md",
            # ⚠️ 2026-11-21 补:**FACTS.md § 8.1 的那一段也是本工具的产物**
            #   (数字由生成器写,不许手抄)⇒ 改了 FACTS.md 就得查它那一段。
            "docs/internal/FACTS.md",
            "compiler/src0/*",
            "mcp-jhyy/*",
            "scripts/gen-knowledge.py",
            "scripts/dev/*",
        ],
        "outputs": [
            "docs/generated/jhyy-knowledge.md",
            "docs/generated/jhyy-knowledge.json",
            "docs/generated/jhyy-error-fix.json",
            "docs/internal/FACTS.md",      # ← § 8.1 那一段（⚠️ 与 langstat 共用同一个文件）
        ],
    },
]


def staged_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return []
    return [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]


def triggered(spec: dict, staged: list[str]) -> bool:
    pats = spec.get("triggers") or []
    if pats == ["*"]:
        return True
    for f in staged:
        for p in pats:
            if fnmatch.fnmatch(f, p):
                return True
    return False


def run(cmd: list[str], quiet: bool = False) -> int:
    """跑一条命令。`quiet=True` ⇒ **成功时闭嘴**（检查器的输出没信息量，
    刷的时候刷出来就够；失败时才把它的输出打出来）。"""
    if quiet:
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode != 0:
            sys.stdout.write(p.stdout or "")
            sys.stderr.write(p.stderr or "")
        return p.returncode
    p = subprocess.run(cmd, cwd=str(ROOT))
    return p.returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="全部刷一遍（不管触发条件）")
    ap.add_argument("--check", action="store_true", help="只查不改（= CI 那道门）")
    ap.add_argument("--amend-index", action="store_true",
                    help="刷完把产物 git add 进去（钩子用）")
    args = ap.parse_args()

    staged = staged_files()
    if args.check:
        rc = 0
        for spec in REFRESHERS:
            if not triggered(spec, staged):
                continue
            r = run(spec["check"], quiet=True)
            if r != 0:
                print(f"[refresh-artifacts] ✗ {spec['name']} 过期了", file=sys.stderr)
                rc = 1
        return rc

    changed_any = False
    for spec in REFRESHERS:
        if not args.all and not triggered(spec, staged):
            continue
        if run(spec["check"], quiet=True) == 0:
            continue  # 没过期 ⇒ 不用动
        print(f"[refresh-artifacts] 刷 {spec['name']} ……")
        if run(spec["regen"]) != 0:
            print(f"[refresh-artifacts] ✗ {spec['name']} **刷不出来** ⇒ "
                  f"（生成器坏了？）⇒ 提交中止", file=sys.stderr)
            return 1
        changed_any = True
        if args.amend_index:
            for out in spec["outputs"]:
                p = ROOT / out
                if not p.exists():
                    continue
                # ⚠️ **只 add 生成器真的会动的那几个文件** ⇒ 别的产物别碰
                if subprocess.run(["git", "add", "--", out], cwd=str(ROOT)).returncode != 0:
                    print(f"[refresh-artifacts] ⚠️ git add {out} 失败", file=sys.stderr)

    if changed_any:
        print("[refresh-artifacts] ✓ 已刷好（产物已进暂存区）—— "
              "**提交里会带上它们**。")
        print("[refresh-artifacts]   不想要？`git reset HEAD -- <文件>` 撤掉。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
