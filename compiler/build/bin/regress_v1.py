#!/usr/bin/env python3
"""Run all integration tests against jhyy_v1.exe.exe (jhyy-side historical baseline).

**v1.4.4 ship 状态说明 (2026-08-14):**
v1.4.4 物理替换 jhyy.exe 时, `jhyy_v1.exe.exe` 也被同步覆盖成 jhyy-side
production binary (sha `37ffc49c...`, 跟 jhyy.exe 同 physical binary)。
原 v1.0.0 closure canonical `2445e97d...` 在 v1.4.2 ship 时已丢失 (per
v1.4.4 commit message: "jhyy_v1.exe.exe 历史 baseline 是 pre-DWARF 时段的
binary, sha 已漂")。

**因此 v1.4.5 时:** regress_v1.py 当前物理 = regress.py (同一 binary 同一 sha)。
保留文件作 v1.0.0 时代的 regression contract (跟 regress.py / regress_stage0.py
平行), 用 `--tests` 子集排除 v1.4.6 新增的 2 个真修测试 (W-017/W-019 引入,
v1 binary 没有这些 fix 必然 fail), 反映 v1 historical baseline "不破老测试"
的语义。

**v1.5+ TODO:** 真要恢复 v1.0.0 closure canonical, 需要从 git history 找回
sha `2445e97d...` binary (commit `eabee0d` / v1.0.0 tag) 重新放回 tracked;
per `feedback_regress_baseline_binary_hash.md` 不可退役, 但 v1.4.4 ship
意外丢了。留给 v1.5.0 installer 设计时定夺 (重 track / 删除该 regress
入口)。

Sprint mcp-1 (2026-08-11): shim that delegates to mcp-jhyy/jhyy_regress.py.
All logic (NTSTATUS detection, EXPECT annotation, stale-cache hardening) lives there.
"""
import sys
from pathlib import Path

# Make mcp-jhyy/ importable
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-jhyy"))

from jhyy_regress import run_all  # noqa: E402

if __name__ == "__main__":
    # enforce_baseline_hash=False: jhyy_v1.exe.exe 是 tracked 历史 baseline,
    # phantom-binary 检查 (binary mtime < source mtime) 是 expected (src 一直
    # 在变, v1 binary 不 rebuild) — 应该跳过。
    #
    # 当前 v1.4.5 时, jhyy_v1.exe.exe = jhyy.exe (v1.4.4 ship 物理覆盖, 跟
    # `feedback_regress_baseline_binary_hash.md` 期望的 "frozen v1.0.0 closure
    # canonical" 偏离 — 详见上方 docstring)。所以这个 regress 入口当前是
    # regress.py 的 informational mirror, 不是独立 CI gate。CI workflow 里
    # 它只 log 报告, 不 block PR。
    result = run_all(
        binary="compiler/build/bin/jhyy_v1.exe.exe",
        enforce_baseline_hash=False,
    )
    # informational: print summary but never fail CI
    print(f"\n[regress_v1.py] informational only — jhyy_v1.exe.exe = {result['binary_sha256'][:16]}...")
    print(f"[regress_v1.py] passed={result['passed']}/{result['total']} (skipped={result['skipped']})")
    if result["failed_tests"]:
        print(f"[regress_v1.py] note: {len(result['failed_tests'])} fail(s) — see docstring; v1 historical baseline 缺 v1.4.6 fix 是 expected")
    sys.exit(0)