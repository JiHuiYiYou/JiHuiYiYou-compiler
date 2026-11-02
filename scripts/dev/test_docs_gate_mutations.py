#!/usr/bin/env python3
"""文档门的**变异测试** —— 证明 `docs_facts_check.py` 真的看得见它声称看的东西。

**为什么需要这道测试（2026-11-02 审计实测）**：
`docs_facts_check.py` 曾有**四个叠加**的盲区，实测每一个都能让**错的数字**绿灯通过：

| # | 盲区 | 症状 |
|---|---|---|
| a | `re.sub(r"```.*?```", "")` 剥掉围栏代码块 | README 的 `265/265 passed`（在 ```bash 块里）**根本没进被检查的正文** |
| b | 上下文关键词必须与数字**同一行** | README 把 "regression" 放在**上一行的标题**里就免检 |
| c | 词表只认 `N PASS` / `N passed` | 「N scanned / N runnable / N real assertions」完全在词表外 |
| d | `HIST_RE` 豁免**任何含日期的行** | 行尾加个日期就免检 |

⇒ 把 `FACTS.md` + 两份 README 的回归数一起改成 **999/1019**（**自洽但假**），
**5 道门全绿**。⇒ 「事实单一真相源」当时只兑现了一半：门强制的是
「这个数只在一个地方被复述」，**从来没从 `regress.py` 重新推导过它**。

**这道测试做什么**：对已知的漏洞各注入一个**故意的错误**，逐个确认门会红。
⇒ 门改了以后，这道测试会告诉你**新写的检查是不是真的看得见**。

**它不能证明什么**（重要）：本测试证明的是「门能抓到这些**已知的**错误形态」，
**不**证明门能抓到所有错误形态，也不证明 FACTS.md 的数**为真** ——
「为真」要靠 CI 里真跑一遍 `regress.py` 再对拍（见 `docs/internal/FACTS.md` § 2）。

**退出码**：0 = 每个变异都被抓到（且不变异时门是绿的）；1 = 有漏网。

**用法**：`python scripts/dev/test_docs_gate_mutations.py`
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "scripts" / "dev" / "docs_facts_check.py"

# (说明, 文件, 原文本, 变异后的文本)
# ⚠️ 每条变异都必须**只改一个数** —— 否则测不出「门看得见哪个数」。
MUTATIONS: list[tuple[str, str, str, str]] = [
    # (a) 盲区:围栏代码块被剥掉 ⇒ 代码块里的数从来没被查过
    ("代码块里的回归通过数", "README.md",
     "# => 265/265 passed (all with assertions), 0 failed, 20 skipped (of 285 total)",
     "# => 264/265 passed (all with assertions), 0 failed, 20 skipped (of 285 total)"),
    # (b) 盲区:上下文关键词必须同一行 ⇒ 「标题在上、数字在下」免检
    ("标题在上、数字在下的场景", "README.md",
     "# => 265/265 passed (all with assertions), 0 failed, 20 skipped (of 285 total)",
     "# => 265/265 passed (all with assertions), 0 failed, 20 skipped (of 279 total)"),
    # (c) 盲区:词表窄 ⇒ 断言审计那套词汇完全在门外
    ("断言审计的 scanned 数", "README.md",
     "| Assertion audit | 285 scanned / 265 runnable / 205 real assertions / 0 zero-signal |",
     "| Assertion audit | 281 scanned / 265 runnable / 205 real assertions / 0 zero-signal |"),
    ("断言审计的 runnable 数（中文门面）", "README.zh-CN.md",
     "| 断言强度审计 | 扫 285 / 可跑 265 / 真断言 205 / 零信号 0 |",
     "| 断言强度审计 | 扫 285 / 可跑 261 / 真断言 205 / 零信号 0 |"),
    ("断言审计的 real assertions 数", "README.md",
     "| Assertion audit | 285 scanned / 265 runnable / 205 real assertions / 0 zero-signal |",
     "| Assertion audit | 285 scanned / 265 runnable / 201 real assertions / 0 zero-signal |"),
    # (d) 盲区:含日期的行被豁免 ⇒ 加个日期就免检
    ("加日期免检（旧漏洞）", "README.md",
     "| `regress.py` | **265 PASS + 0 XFAIL + 0 failed + 20 SKIP** (285 total) |",
     "| `regress.py` | **999 PASS + 0 XFAIL + 0 failed + 20 SKIP** (285 total) | (2026-11-02 实测) |"),
    # (e) SKIP / total / 门数
    ("SKIP 数", "README.md",
     "# => 265/265 passed (all with assertions), 0 failed, 20 skipped (of 285 total)",
     "# => 265/265 passed (all with assertions), 0 failed, 21 skipped (of 285 total)"),
    ("artifact_checks 门数", "README.md",
     "| `artifact_checks.sh` | **18 PASS / 0 FAIL** |",
     "| `artifact_checks.sh` | **14 PASS / 0 FAIL** |"),
    ("artifact_checks 门数（中文门面）", "README.zh-CN.md",
     "| `artifact_checks.sh` | **18 PASS / 0 FAIL** |",
     "| `artifact_checks.sh` | **16 PASS / 0 FAIL** |"),
]


def run_gate() -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main() -> int:
    print("[test_docs_gate_mutations] 证明文档门看得见它声称看的东西……\n")

    # 正对照:不变异时门必须是绿的 —— 否则下面的「红」没有意义
    rc, out = run_gate()
    if rc != 0:
        print("[test_docs_gate_mutations] FAIL —— 正对照就红了（门在未变异的树上就不绿）:")
        print(out)
        return 1
    print("  正对照 ✓（未变异时门是绿的）\n")

    missed: list[str] = []
    for name, rel, old, new in MUTATIONS:
        p = ROOT / rel
        with open(p, "r", encoding="utf-8", newline="") as f:
            orig = f.read()
        if orig.count(old) != 1:
            print(f"  ✗ {name:34} —— 变异点找不到（{rel} 里有 {orig.count(old)} 处）")
            missed.append(name)
            continue
        try:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(orig.replace(old, new))
            rc, out = run_gate()
            if rc != 0:
                first = next((l.strip() for l in out.splitlines() if l.strip().startswith("x")), "")
                print(f"  ✓ {name:34} 红了 —— {first[:78]}")
            else:
                print(f"  ✗ {name:34} **没抓到**（门仍然绿）")
                missed.append(name)
        finally:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(orig)

    # 收尾:确认全部还原
    rc, out = run_gate()
    print()
    if rc != 0:
        print("[test_docs_gate_mutations] FAIL —— 还原后门仍然红（变异没有干净还原）:")
        print(out)
        return 1
    if missed:
        print(f"[test_docs_gate_mutations] FAIL —— {len(missed)} 个变异漏网:")
        for m in missed:
            print("  x", m)
        return 1
    print(f"[test_docs_gate_mutations] OK —— {len(MUTATIONS)} 个变异全部被门抓到，还原后门是绿的。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
