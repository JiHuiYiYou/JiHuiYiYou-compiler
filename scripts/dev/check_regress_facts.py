#!/usr/bin/env python3
"""回归数与 FACTS.md 的**对拍门** —— 让「事实为真」不再只是一句声明。

**为什么需要这道门**(2026-11-03 门审计实测):

`docs_facts_check.py` 强制的是「这个数在**所有文档里一致**」,而它自己的
变异测试(2026-11-02)写得很明白:

    「它不证明 FACTS.md 的数**为真** —— '为真'要靠 CI 里真跑一遍 `regress.py`
      再对拍」

⇒ 那句「再对拍」**从来没落地**。实测:加一个测试文件 → 真实总数从 285 变成 286
⇒ FACTS.md 还写 285 ⇒ **docs 门 / 变异测试 / bump_version 全绿**。
⇒ 全仓被复述最多的数字(曾出现在 31 份文档里)恰恰**没有真相源校验**。

**这道门做什么**:

| # | 对拍 | 判据来源 | 环境依赖 |
|---|---|---|---|
| 1 | `passed` / `skipped` / `total` | `regress.py --summary-json` 的实测计数 | 无 |
| 2 | `failed` | 同上(必须 0) | 无 |
| 3 | `scanned` / `runnable` / `real_assertions` | `audit_test_assertions.py --json` | 无 |
| 4 | XFAIL 数 | 断言审计的 `xfail` 桶 | 无 |

第 3/4 项之所以也算「真相」:它们是**测试文件的静态属性**(扫了多少个 `.jhyy`、
多少个可跑、多少个有真断言)⇒ 与机器/环境无关 ⇒ 谁都能复现同一个数。

**FLAKY 桶(2026-11-15 加)**:harness 有**第三类**结果 —— 「首次红、隔离重跑绿」。
它**既不是通过**(结果不可信)也**不是失败**(重跑确实过了)⇒ 不进 `passed`、
不进 `failed`,但在 `total` 里有它。
⇒ 不变式是 `passed + skipped + flaky == total`,**不是** `passed + skipped == total`。
⇒ 这一轮有 FLAKY 时,`passed` **不与 FACTS 对拍**(它少的那几个就是 flaky)——
   对拍了只会报「FACTS.md 的数错了」,方向是反的:现实没变,是那轮**不可信**。
   这道门此时报的是「间歇性失败 = 真 bug」并点名是哪些测试。

⚠️ **第 1/2 项的环境无关性**:`run_all` 统计的 skip 只有两类 ——
文件里的 `// SKIP:` 指令 与 「library」(没有 `main_jhyy` 的辅助文件)⇒ 静态。
`--cross=auto` 的 wsl/docker 探测只影响**额外**的跨环境复跑(那 6 个 sysv 用例),
**不改**上面这几个计数 ⇒ CI(无 docker)与本地(有 docker)拿到的是同一组数。

**退出码**:0 = FACTS.md 的数与实测一致;1 = 不一致(逐条列出)。

**用法**:
    python regress.py --all --summary-json tmp/regress-summary.json
    python scripts/dev/check_regress_facts.py tmp/regress-summary.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

# 复用 docs 门对 FACTS.md 的解析(单一真相源:同一个正则,同一份声明)
sys.path.insert(0, str(HERE))
import docs_facts_check as dfc  # noqa: E402

AUDIT = HERE / "audit_test_assertions.py"

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def compare(label: str, got, want) -> None:
    if got != want:
        fail(f"{label}: 实测 {got} != FACTS.md 声明的 {want}")


def audit_json() -> dict | None:
    """跑断言审计拿它的 JSON(纯字符串运算,亚秒级)。"""
    if not AUDIT.is_file():
        fail(f"断言审计脚本不存在: {AUDIT}")
        return None
    r = subprocess.run([sys.executable, str(AUDIT), "--json"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(ROOT))
    if r.returncode != 0:
        fail(f"断言审计跑失败(rc={r.returncode}): {(r.stderr or '').strip()[:200]}")
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        fail(f"断言审计的 --json 输出解析不了: {e}")
        return None


def main() -> int:
    print("[check_regress_facts] 对拍 FACTS.md 的回归数与实测……\n")
    # 这一轮有没有 FLAKY —— 决定收尾时给哪条修法(见文件末尾的 footer)。
    flaky_seen = False

    if len(sys.argv) != 2:
        print(f"用法: python {Path(sys.argv[0]).name} <regress-summary.json>",
              file=sys.stderr)
        print("  (摘要由 `python regress.py --all --summary-json <path>` 产出)",
              file=sys.stderr)
        return 2

    summary_path = Path(sys.argv[1])
    if not summary_path.is_absolute():
        summary_path = ROOT / summary_path

    # ── 1. 实测计数(来自 regress 的本轮输出)────────────────────────────
    if not summary_path.is_file():
        fail(f"对拍源缺失: {summary_path} —— 拿不到实测计数 ⇒ 无法证明 FACTS.md 的数为真。"
             "先跑 `python regress.py --all --summary-json <path>`。")
        summary = None
    else:
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            fail(f"{summary_path} 不是合法 JSON: {e}")
            summary = None

    # ── 2. FACTS.md 的声明 ────────────────────────────────────────────
    declared = dfc.declared()
    if dfc.problems:
        for p in dfc.problems:
            fail(f"FACTS.md 解析: {p}")
        print("\n[check_regress_facts] FAIL —— FACTS.md 的声明本身有问题:")
        for p in problems:
            print("  x", p)
        return 1
    print("  FACTS.md 声明:",
          {k: declared[k] for k in ("pass", "skip", "total",
                                    "scanned", "runnable", "real_assertions")
           if k in declared})

    if summary is not None:
        gated = summary.get("gated") or {}
        if not gated:
            fail(f"{summary_path} 里没有 `gated` 段 —— 摘要格式不对?")
        elif "flaky" not in gated:
            # 2026-11-15:摘要必须带 FLAKY 桶。缺它 ⇒ 这个摘要不是本仓
            # regress.py 产的(或是很久以前的旧摘要)⇒ 它的 passed 计数
            # 可能有「不可信」的成分却看不出来 ⇒ 不拿它对拍。
            fail(f"{summary_path} 的 `gated` 段里没有 `flaky` 字段 —— "
                 "这个摘要不是本仓 regress.py 产的?重跑一次 `regress.py --all "
                 "--summary-json <path>`。")
        else:
            flaky = gated.get("flaky") or 0
            flaky_tests = gated.get("flaky_tests") or []
            passed = gated.get("passed") or 0
            skipped = gated.get("skipped") or 0
            total = gated.get("total") or 0
            # total / skipped / failed 不受 FLAKY 影响 ⇒ 照常对拍。
            compare("回归 total", gated.get("total"), declared.get("total"))
            compare("回归 skipped", gated.get("skipped"), declared.get("skip"))
            # failed 恒为 0(FACTS 的基线行写死「0 failed」)
            compare("回归 failed", gated.get("failed"), 0)
            if flaky:
                # FLAKY = 「首次红、隔离重跑绿」—— harness 里的**第三类**结果:
                # 不是通过(结果不可信),也不是失败(重跑确实过了)。
                # ⇒ 这一轮里 passed 少的那几个就是它们 ⇒ **passed 不能跟
                #   FACTS 对拍**:对拍了只会报「FACTS.md 的数错了」——
                #   方向是反的(现实没变,是那一轮的回归结果**不可信**)。
                # ⇒ 报「间歇性失败 = 真 bug」,并点名是哪些测试。
                names = ", ".join(flaky_tests) or "(名字没带过来)"
                flaky_seen = True
                fail(f"回归里有 {flaky} 个 FLAKY(首次失败、隔离重跑绿 —— "
                     f"间歇性问题): {names}。"
                     "这不是 FACTS.md 的数错了,是那一轮的回归结果不可信;"
                     "**别改 FACTS.md** —— 修那个测试(或它的根因)再跑。")
            else:
                compare("回归 passed", gated.get("passed"), declared.get("pass"))
            if passed + skipped + flaky != total:
                fail(f"实测自相矛盾: passed {passed} + skipped {skipped} + "
                     f"flaky {flaky} != total {total}")
            mode = summary.get("mode")
            if mode != "all":
                fail(f"摘要的 mode={mode!r} —— 对拍基线必须用 `--all` 跑(单 binary "
                     "模式的计数口径与基线不同)")
            print(f"  实测(regress): passed={passed} "
                  f"skipped={skipped} total={total} "
                  f"failed={gated.get('failed')} flaky={flaky} (mode={mode}, "
                  f"cross={summary.get('cross_mode')})")

    # ── 3. 断言审计的静态计数(与机器无关)──────────────────────────────
    aud = audit_json()
    if aud is not None:
        compare("审计 scanned", aud.get("total"), declared.get("scanned"))
        compare("审计 runnable", aud.get("runnable"), declared.get("runnable"))
        compare("审计 real_assertions", aud.get("real_assertions"),
                declared.get("real_assertions"))
        xfail = len((aud.get("buckets") or {}).get("xfail") or [])
        compare("审计 xfail", xfail, 0)
        print(f"  实测(audit):  scanned={aud.get('total')} "
              f"runnable={aud.get('runnable')} "
              f"real_assertions={aud.get('real_assertions')} xfail={xfail}")

    if problems:
        print(f"\n[check_regress_facts] FAIL —— {len(problems)} 处与现实对不上:")
        for p in problems:
            print("  x", p)
        if flaky_seen:
            # 有 FLAKY 时,「改 FACTS.md」是**错的方向**:现实没变,
            # 是那一轮的回归结果不可信 ⇒ 该修的是那个间歇性失败的测试。
            print("\n  修法:这是**间歇性失败**(真 bug)—— 修那个测试(或它的根因)再跑。")
            print("       **别改 FACTS.md**(这一轮的数字没错,是那一轮不可信)。")
        else:
            print("\n  修法:数字只写在 docs/internal/FACTS.md;真实值变了就改 FACTS.md")
            print("       (别改门 —— 门红了说明现实变了,不是门错了)。")
        return 1
    print("\n[check_regress_facts] OK —— FACTS.md 的数与实测一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
