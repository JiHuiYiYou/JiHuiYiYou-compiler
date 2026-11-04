#!/usr/bin/env python3
"""事实链的**变异测试** —— 证明这条链真的看得见它声称看的东西。

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

**2026-11-03 补上另一半**：新增 `scripts/dev/check_regress_facts.py`
（拿 `regress.py --summary-json` 的**实测计数**与 FACTS 对拍）。
⇒ 「自洽但假」现在**抓得到**了 —— 本测试的 `CHAIN_MUTATIONS` 就是它的证明：
每次注入一个**自洽但假**的数，先断言 **docs 门仍然是绿的**（它本来就该绿 ——
它只管一致性），再断言 **对拍门变红**（它管「为真」）。
⇒ 两个门**各管一半**，合起来才是「事实为真」。

**第三组（2026-11-03）**：`CI_MUTATIONS` —— 改 workflow，看门清单门
（`docs_facts_check` 的第 J 项）抓不抓得住。实测那个旧实现有**三个**盲区：
扫全文含注释、只认 `scripts/dev/*.py`、判据是「名字在 FACTS 全文出现过」。
现在改成「workflow 里带 `# gate: <id>` 标记 ⇄ FACTS § 2.2 双向对拍 + 每道门
跑的命令也要对得上」⇒ 这 5 个场景每一个都必须红。

**它不能证明什么**（重要）：本测试证明的是「门能抓到这些**已知的**错误形态」，
**不**证明门能抓到所有错误形态。

**退出码**：0 = 每个变异都被抓到（且不变异时门是绿的）；1 = 有漏网。

**用法**：
    python scripts/dev/test_docs_gate_mutations.py
    python scripts/dev/test_docs_gate_mutations.py --regress-summary tmp/regress-summary.json
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_GATE = ROOT / "scripts" / "dev" / "docs_facts_check.py"
FACTS_GATE = ROOT / "scripts" / "dev" / "check_regress_facts.py"

# (相对路径, 原文本, 变异后的文本)
Edit = tuple[str, str, str]


# ⚠️ **W-193 真修 (2026-11-04)**:变异文本里的数**必须动态读**,不能写死。
#
# 写死的后果(实测):回归数一变(加一个用例就会变)⇒ `check_points()` 数
# 「变异点在文件里出现几次」得到 0 ⇒ 报「变异点找不到」⇒ **15 条变异全部漏网**
# ⇒ 门自己变红 ⇒ CI 立刻红 ⇒ 早晚有人去「修」它(最省事的修法是删掉变异或门)
# ⇒ 恰好毁掉「事实链看得见」这个**唯一的证明**。
#
# ⇒ 数从 **FACTS.md**(事实单一真相源)现场读;读不到就**响亮失败**,
#   不再静默退化成「漏网」。
def _facts_numbers() -> dict[str, int]:
    text = (ROOT / "docs" / "internal" / "FACTS.md").read_text(encoding="utf-8")
    m = re.search(
        r"\*\*(\d+) PASS \+ 0 XFAIL \+ 0 failed \+ (\d+) SKIP\*\*\uff08(\d+) total\uff09",
        text)
    if not m:
        raise SystemExit(
            "ERR: FACTS.md 里找不到回归三件套"
            "(`**N PASS + 0 XFAIL + 0 failed + N SKIP**\uff08N total\uff09`)"
            " —— 变异文本靠它拼 ⇒ 读不到就没法跑。")
    a = re.search(r"\u626b\u63cf (\d+) \u00b7 \u53ef\u8dd1 (\d+) \u00b7 \u771f\u65ad\u8a00 (\d+) \u00b7", text)
    if not a:
        raise SystemExit(
            "ERR: FACTS.md 里找不到断言审计三件套"
            "(`\u626b\u63cf N \u00b7 \u53ef\u8dd1 N \u00b7 \u771f\u65ad\u8a00 N \u00b7`)"
            " —— 变异文本靠它拼 ⇒ 读不到就没法跑。")
    return {
        "pass": int(m.group(1)),
        "skip": int(m.group(2)),
        "total": int(m.group(3)),
        "scanned": int(a.group(1)),
        "runnable": int(a.group(2)),
        "assertions": int(a.group(3)),
    }


_N = _facts_numbers()
_P, _S, _T = _N["pass"], _N["skip"], _N["total"]
_SC, _RN, _RA = _N["scanned"], _N["runnable"], _N["assertions"]

# ── 各文件里承载这几个数的**行模板**(数由上面动态填)────────────────────
# README.md(英文门面)
_RB_EN = f"# => {_P}/{_P} passed (all with assertions), 0 failed, {_S} skipped (of {_T} total)"
_RT_EN = f"| `regress.py` | **{_P} PASS + 0 XFAIL + 0 failed + {_S} SKIP** ({_T} total) |"
_AU_EN = f"| Assertion audit | {_SC} scanned / {_RN} runnable / {_RA} real assertions / 0 zero-signal |"
# README.zh-CN.md(中文门面)
_RB_ZH = f"# => {_P}/{_P} passed (\u5168\u90e8\u6709\u65ad\u8a00), 0 failed, {_S} skipped (of {_T} total)"
_RT_ZH = f"| `regress.py` | **{_P} PASS + 0 XFAIL + 0 failed + {_S} SKIP**({_T} total) |"
_AU_ZH = f"| \u65ad\u8a00\u5f3a\u5ea6\u5ba1\u8ba1 | \u626b {_SC} / \u53ef\u8dd1 {_RN} / \u771f\u65ad\u8a00 {_RA} / \u96f6\u4fe1\u53f7 0 |"
# FACTS.md(事实单一真相源)
_FT_REG = f"**{_P} PASS + 0 XFAIL + 0 failed + {_S} SKIP**\uff08{_T} total\uff09"
_FT_AUD = f"\u626b\u63cf {_SC} \u00b7 \u53ef\u8dd1 {_RN} \u00b7 \u771f\u65ad\u8a00 {_RA} \u00b7"

# ⚠️ 每条变异都必须**只改一个数** —— 否则测不出「门看得见哪个数」。
MUTATIONS: list[tuple[str, list[Edit]]] = [
    # (a) 盲区:围栏代码块被剥掉 ⇒ 代码块里的数从来没被查过
    ("代码块里的回归通过数", [(
        "README.md",
        _RB_EN,
        f"# => {_P - 1}/{_P} passed (all with assertions), 0 failed, {_S} skipped (of {_T} total)")]),
    # (b) 盲区:上下文关键词必须同一行 ⇒ 「标题在上、数字在下」免检
    ("标题在上、数字在下的场景", [(
        "README.md",
        _RB_EN,
        f"# => {_P}/{_P} passed (all with assertions), 0 failed, {_S} skipped (of {_T - 1} total)")]),
    # (c) 盲区:词表窄 ⇒ 断言审计那套词汇完全在门外
    ("断言审计的 scanned 数", [(
        "README.md",
        _AU_EN,
        f"| Assertion audit | {_SC - 1} scanned / {_RN} runnable / {_RA} real assertions / 0 zero-signal |")]),
    ("断言审计的 runnable 数（中文门面）", [(
        "README.zh-CN.md",
        _AU_ZH,
        f"| 断言强度审计 | 扫 {_SC} / 可跑 {_RN - 1} / 真断言 {_RA} / 零信号 0 |")]),
    ("断言审计的 real assertions 数", [(
        "README.md",
        _AU_EN,
        f"| Assertion audit | {_SC} scanned / {_RN} runnable / {_RA - 1} real assertions / 0 zero-signal |")]),
    # (d) 盲区:含日期的行被豁免 ⇒ 加个日期就免检
    ("加日期免检（旧漏洞）", [(
        "README.md",
        _RT_EN,
        f"| `regress.py` | **999 PASS + 0 XFAIL + 0 failed + {_S} SKIP** ({_T} total) | (2026-11-04 实测)")]),
    # (e) SKIP / total / 门数
    ("SKIP 数", [(
        "README.md",
        _RB_EN,
        f"# => {_P}/{_P} passed (all with assertions), 0 failed, {_S + 1} skipped (of {_T} total)")]),
    ("artifact_checks 门数", [(
        "README.md",
        "| `artifact_checks.sh` | **18 PASS / 0 FAIL** |",
        "| `artifact_checks.sh` | **14 PASS / 0 FAIL** |")]),
    ("artifact_checks 门数（中文门面）", [(
        "README.zh-CN.md",
        "| `artifact_checks.sh` | **18 PASS / 0 FAIL** |",
        "| `artifact_checks.sh` | **16 PASS / 0 FAIL** |")]),
    # (e) 产物尺寸:FACTS § 1 声明 vs 两份 README
    ("产物尺寸（安装器）", [(
        "README.md",
        "| ~55 MB | GUI installer — compiler + `.jhyy` file association + VS Code extension + PATH |",
        "| ~42 MB | GUI installer — compiler + `.jhyy` file association + VS Code extension + PATH |")]),
    # (f) 台账的前向版本标签:指向一个不存在的版本
    ("台账标签指向不存在的版本", [(
        "docs/internal/workarounds.md",
        "closed 2026-11-02 (v4.1.3) — build 路径缺",
        "closed 2026-11-02 (v4.1.9) — build 路径缺")]),
]

# ── 「自洽但假」的整链变异(2026-11-03 新增)──────────────────────────────
# 这类是**最难抓**的一类:所有文档一起改成同一个假数 ⇒ 「一致性」门全绿。
# 2026-11-02 实测:这类变异能同时骗过 5 道门 ⇒ 那时「事实为真」只是声明。
# 现在:docs 门**仍然绿**(它只管一致性),但对拍门必须**红**。
CHAIN_MUTATIONS: list[tuple[str, list[Edit]]] = [
    ("回归三件套自洽但假", [
        ("docs/internal/FACTS.md",
         _FT_REG,
         f"**999 PASS + 0 XFAIL + 0 failed + {_S} SKIP**\uff081019 total\uff09"),
        ("README.md",
         _RB_EN,
         f"# => 999/999 passed (all with assertions), 0 failed, {_S} skipped (of 1019 total)"),
        ("README.md",
         _RT_EN,
         f"| `regress.py` | **999 PASS + 0 XFAIL + 0 failed + {_S} SKIP** (1019 total) |"),
        ("README.zh-CN.md",
         _RB_ZH,
         f"# => 999/999 passed (\u5168\u90e8\u6709\u65ad\u8a00), 0 failed, {_S} skipped (of 1019 total)"),
        ("README.zh-CN.md",
         _RT_ZH,
         f"| `regress.py` | **999 PASS + 0 XFAIL + 0 failed + {_S} SKIP**(1019 total) |"),
    ]),
    ("断言审计静态数自洽但假", [
        ("docs/internal/FACTS.md",
         _FT_AUD,
         f"\u626b\u63cf 1019 \u00b7 \u53ef\u8dd1 999 \u00b7 \u771f\u65ad\u8a00 {_RA} \u00b7"),
        ("README.md",
         _AU_EN,
         f"| Assertion audit | 1019 scanned / 999 runnable / {_RA} real assertions / 0 zero-signal |"),
        ("README.zh-CN.md",
         _AU_ZH,
         f"| \u65ad\u8a00\u5f3a\u5ea6\u5ba1\u8ba1 | \u626b 1019 / \u53ef\u8dd1 999 / \u771f\u65ad\u8a00 {_RA} / \u96f6\u4fe1\u53f7 0 |"),
    ]),
]

# ── CI 实况的变异(2026-11-03 新增)──────────────────────────────────────
# 门清单门(第 J 项)当时的**三个盲区**,每个一个场景:
#   ① 判据是「名字在 ci.yml 全文出现过」⇒ 删掉调用行、注释里还留着路径 ⇒ 漏
#   ② 只认 `scripts/dev/*.py` ⇒ 新增一道 `.sh` 门 ⇒ 漏
#   ③ 判据是「名字在 FACTS 全文出现过」,不是「在 § 2 门表里」⇒ 漏
# 现在:workflow 里带 `# gate: <id>` 标记 ⇄ FACTS § 2.2 **双向**对拍,
# 外加「每道门跑的命令也要对得上」+「新加步骤必须分类」。
CI_MUTATIONS: list[tuple[str, list[Edit]]] = [
    ("删掉一道门的标记（清单说有、CI 里没跑）", [(
        ".github/workflows/ci.yml",
        "          # gate: spec-consistency\n",
        "")]),
    ("在别的门的 step 里偷偷加一道没登记的 .sh 门", [(
        ".github/workflows/ci.yml",
        "          python scripts/dev/check_spec_consistency.py\n",
        "          python scripts/dev/check_spec_consistency.py\n"
        "          bash compiler/tests/bootstrap/some_new_gate.sh\n")]),
    ("加一个没分类的 CI 步骤", [(
        ".github/workflows/ci.yml",
        "      - name: Spec consistency gate (three specs must agree)",
        "      - name: Some new step nobody classified\n"
        "        shell: msys2 {0}\n"
        "        run: |\n"
        "          echo hello\n"
        "      - name: Spec consistency gate (three specs must agree)")]),
    ("把本地门接进 CI（没移到 § 2.2）", [(
        ".github/workflows/ci.yml",
        "          python scripts/dev/check_spec_consistency.py\n",
        "          python scripts/dev/check_spec_consistency.py\n"
        "          # gate: fixed-point\n")]),
    ("改了门跑的命令但没改清单", [(
        ".github/workflows/ci.yml",
        "          python scripts/dev/check_spec_consistency.py\n",
        "          python scripts/dev/check_arch_claims.py\n")]),
]


def run_gate(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(ROOT))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _read(rel: str) -> tuple[str, str]:
    p = ROOT / rel
    with open(p, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    return text, ("\r\n" if "\r\n" in text else "\n")


def _write(rel: str, text: str) -> None:
    p = ROOT / rel
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def apply_edits(edits: list[Edit]) -> None:
    for rel, old, new in edits:
        text, eol = _read(rel)
        _write(rel, text.replace(old.replace("\n", eol), new.replace("\n", eol)))


def snapshot(edits: list[Edit]) -> dict[str, bytes]:
    """**逐字节**快照 —— 还原必须用它,不能用「反向 replace」。

    ⚠️ 踩过的坑(2026-11-03):反向 replace 写成
    `text.replace(new, old)`,当 `new` 是**空串**时(「删掉一行」那种变异),
    Python 会把 `old` 插进**每个字符之间** ⇒ 文件被放大成 1.2 MB 的垃圾,
    整轮 CI 的 workflow 全废。⇒ 还原一律走字节快照。
    """
    return {rel: (ROOT / rel).read_bytes() for rel, _o, _n in edits}


def restore(snap: dict[str, bytes]) -> None:
    for rel, data in snap.items():
        (ROOT / rel).write_bytes(data)


def check_points(edits: list[Edit], name: str, missed: list[str]) -> bool:
    """每个编辑点必须**恰好命中一处** —— 否则这条变异测的不是它想测的东西。"""
    ok = True
    for rel, old, _new in edits:
        text, eol = _read(rel)
        n = text.count(old.replace("\n", eol))
        if n != 1:
            print(f"  ✗ {name:34} —— 变异点找不到（{rel} 里有 {n} 处）")
            missed.append(name)
            ok = False
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regress-summary", metavar="PATH", default=None,
                    help="regress.py --summary-json 的产物 —— 「自洽但假」那组变异"
                         "需要它(对拍门拿它跟 FACTS 比)。不给则找默认的 "
                         "tmp/regress-summary.json;还没有就跳过那组变异。")
    args = ap.parse_args()

    summary = args.regress_summary
    if summary is None:
        default = ROOT / "tmp" / "regress-summary.json"
        summary = str(default) if default.is_file() else None
    elif not (ROOT / summary).is_file() and not Path(summary).is_file():
        print(f"ERR: --regress-summary 指定的 {summary} 不存在", file=sys.stderr)
        return 2

    print("[test_docs_gate_mutations] 证明事实链看得见它声称看的东西……\n")

    missed: list[str] = []

    # 正对照:不变异时门必须是绿的 —— 否则下面的「红」没有意义
    rc, out = run_gate([sys.executable, str(DOCS_GATE)])
    if rc != 0:
        print("[test_docs_gate_mutations] FAIL —— 正对照就红了（门在未变异的树上就不绿）:")
        print(out)
        return 1
    print("  正对照 ✓（未变异时门是绿的）\n")

    # ── 第一组:docs 门自己的盲区(每条都必须让它红)────────────────────
    print("  ── docs 门(一致性)───────────────────────────────────────────")
    for name, edits in MUTATIONS:
        if not check_points(edits, name, missed):
            continue
        snap = snapshot(edits)
        try:
            apply_edits(edits)
            rc, out = run_gate([sys.executable, str(DOCS_GATE)])
            if rc != 0:
                first = next((l.strip() for l in out.splitlines() if l.strip().startswith("x")), "")
                print(f"  ✓ {name:34} 红了 —— {first[:78]}")
            else:
                print(f"  ✗ {name:34} **没抓到**（门仍然绿）")
                missed.append(name)
        finally:
            restore(snap)

    # ── 第二组:「自洽但假」的整链变异 ─────────────────────────────────
    # 期望:**docs 门绿**(它只管一致性),**对拍门红**(它管「为真」)。
    print("\n  ── 整链变异(自洽但假)──────────────────────────────────────")
    if summary is None:
        print("  ⚠ 跳过:没有 regress 摘要 ⇒ 跑一次 "
              "`python regress.py --all --summary-json tmp/regress-summary.json` 再来")
    else:
        facts_cmd = [sys.executable, str(FACTS_GATE), summary]
        for name, edits in CHAIN_MUTATIONS:
            if not check_points(edits, name, missed):
                continue
            snap = snapshot(edits)
            try:
                apply_edits(edits)
                docs_rc, _ = run_gate([sys.executable, str(DOCS_GATE)])
                facts_rc, out = run_gate(facts_cmd)
                if docs_rc == 0 and facts_rc != 0:
                    first = next((l.strip() for l in out.splitlines() if l.strip().startswith("x")), "")
                    print(f"  ✓ {name:34} docs 门绿 / 对拍门红 —— {first[:66]}")
                elif docs_rc != 0:
                    print(f"  ✗ {name:34} docs 门**也红了** ⇒ 这条不是「自洽」变异,测错了东西")
                    missed.append(name)
                else:
                    print(f"  ✗ {name:34} **没抓到**（对拍门仍然绿）")
                    missed.append(name)
            finally:
                restore(snap)

    # ── 第三组:CI 实况的变异(门清单门必须红)──────────────────────────
    print("\n  ── CI 实况变异(门清单 ⇄ 实况)──────────────────────────────")
    for name, edits in CI_MUTATIONS:
        if not check_points(edits, name, missed):
            continue
        snap = snapshot(edits)
        try:
            apply_edits(edits)
            rc, out = run_gate([sys.executable, str(DOCS_GATE)])
            if rc != 0:
                first = next((l.strip() for l in out.splitlines() if l.strip().startswith("x")), "")
                print(f"  ✓ {name:34} 红了 —— {first[:66]}")
            else:
                print(f"  ✗ {name:34} **没抓到**（门仍然绿）")
                missed.append(name)
        finally:
            restore(snap)

    # 收尾:确认全部还原
    rc, out = run_gate([sys.executable, str(DOCS_GATE)])
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
    print(f"[test_docs_gate_mutations] OK —— {len(MUTATIONS)} + {len(CHAIN_MUTATIONS)} + "
          f"{len(CI_MUTATIONS)} 个变异全部被门抓到，还原后门是绿的。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
