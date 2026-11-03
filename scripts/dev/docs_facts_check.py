#!/usr/bin/env python3
"""文档事实对拍门 —— 让 [`docs/internal/FACTS.md`](../../docs/internal/FACTS.md) 真的是「唯一真相源」。

**为什么需要这道门(2026-10-30 实测)**:
本仓曾把「回归通过数」写在 **31 份文档**里、把「ACTIVE 数」写在 25 份里。
结果两份 README 的版本徽章落后 8 个 release,而 CI 全绿 —— 因为版本门
(`bump_version.py check`)当时只扫 6 个位置,链接检查只解析 markdown 链接。

**这道门查什么**:

| # | 检查 | 成本 |
|---|---|---|
| A | `VERSION` == 两份 README 的徽章版本 | 零 |
| B | 台账索引行数 / ACTIVE 数 == FACTS.md 声明 | 零 |
| C | `artifact_checks.sh` / `fixed_point.sh` 的门数 == FACTS.md 声明 | 零 |
| D | **非 archive 文档里「回归基线」语境下的 PASS 数必须等于 FACTS.md 的数** | 零 |
| E | 全仓 markdown 链接 + 锚点无断链(含显式 `<a id>` 与同页锚点) | 秒级 |
| F | FACTS.md 引用的文件都存在 | 零 |
| G | 台账**正文**解析:5 态枚举 / per-status 计数 / 索引↔正文状态一致 | 零 |
| H | **反引号里的裸路径**指向真实存在的文件(另一类引用面 —— 见 `check_backtick_paths`) | 秒级 |
| I | **`§ N.M` 章节引用**指向真实存在的章节(第三类引用面 —— 见 `check_section_refs`) | 秒级 |
| J | **CI 里跑的门都在 FACTS.md § 2 的门清单里登记**(清单自维护) | 零 |

**退出码**:0 = 全绿;1 = 有漂移(逐条列出)。
"""
from __future__ import annotations

import os
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACTS = ROOT / "docs" / "internal" / "FACTS.md"

problems: list[str] = []


def fail(msg: str) -> None:
    problems.append(msg)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def all_md() -> list[Path]:
    """**只扫 git 跟踪的 .md** —— 门要验的是「CI 看到的那个仓」,
    不是工作树里的临时文件(gitignored 的 .claude/ 等不算)。"""
    import subprocess
    try:
        # ⚠️ **不要用 pathspec `*.md`** —— 实测:同样的 git、同样参数,
        # bash 下 `git ls-files '*.md'` 列 234 个(跨目录),而从 Python subprocess
        # 调同一个二进制只列 4 个(只顶层)⇒ 门会「扫了 4 个文件却报 OK」。
        # ⇒ 不带 pathspec,自己在 Python 里按后缀过滤。
        names = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            check=True).stdout.split("\0")
        names = [n for n in names if n.endswith(".md")]
    except Exception:
        names = []
    if names:
        return sorted(ROOT / n for n in names if (ROOT / n).is_file())
    out = []
    for dp, dn, fn in os.walk(ROOT):
        if ".git" in dp or "node_modules" in dp:
            continue
        for f in fn:
            if f.endswith(".md"):
                out.append(Path(dp) / f)
    return sorted(out)


# --------------------------------------------------------------------------
# A. 版本号
# --------------------------------------------------------------------------
def check_version() -> None:
    """`VERSION` 与 FACTS.md 的一致性。

    ⚠️ **两份 README 的版本徽章不在这里查**(2026-11-03 审计删):
    `bump_version.py check` 已经查了同一断言(`fingerprints()` 扫徽章 +
    README 里其余 5 处版本串),而且查得更全 ⇒ 两道门查同一件事 = 重复,
    改一处漏一处的风险不变、覆盖面却没增加。

    这里只留**`bump_version` 不管的那一条**:FACTS.md 必须提到当前版本。
    """
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not FACTS.is_file():
        fail("docs/internal/FACTS.md 不存在 —— 事实单一真相源必须在")
    elif version not in read(FACTS):
        fail(f"docs/internal/FACTS.md 里没有出现当前版本 {version}")


# --------------------------------------------------------------------------
# 从 FACTS.md 解析声明的数字
# --------------------------------------------------------------------------
def declared() -> dict:
    out: dict[str, int] = {}
    if not FACTS.is_file():
        return out
    ft = read(FACTS)

    m = re.search(r"\*\*(\d+) PASS \+ 0 XFAIL \+ 0 failed \+ (\d+) SKIP\*\*（(\d+) total）", ft)
    if not m:
        fail("FACTS.md: 找不到回归基线那一行")
    else:
        out["pass"] = int(m.group(1))
        out["skip"] = int(m.group(2))
        out["total"] = int(m.group(3))
        if out["pass"] + out["skip"] != out["total"]:
            fail(f"FACTS.md: 回归基线自相矛盾 —— {out['pass']}+{out['skip']} != {out['total']}")

    m = re.search(r"\| 条目总数 \| \*\*(\d+)\*\*", ft)
    if not m:
        fail("FACTS.md: 找不到台账条目总数")
    else:
        out["ledger_total"] = int(m.group(1))

    m = re.search(r"\| ACTIVE \| \*\*(\d+)\*\*", ft)
    if not m:
        fail("FACTS.md: 找不到 ACTIVE 数")
    else:
        out["active"] = int(m.group(1))

    m = re.search(r"\| DEFERRED \| (\d+)", ft)
    if not m:
        fail("FACTS.md: 找不到 DEFERRED 数")
    else:
        out["deferred"] = int(m.group(1))

    m = re.search(r"\| RESOLVED / SUPERSEDED / INVALID \| (\d+) / (\d+) / (\d+)", ft)
    if not m:
        fail("FACTS.md: 找不到 RESOLVED / SUPERSEDED / INVALID 那一行")
    else:
        out["resolved"] = int(m.group(1))
        out["superseded"] = int(m.group(2))
        out["invalid"] = int(m.group(3))

    # 产物级门数(2026-11-03:§ 2 改成「事实 / CI 门 / 本地门」三节后,
    # 门数改记在 § 2.1 的「产物级门数」一行里 —— id 用连字符(`artifact-checks`),
    # 脚本名里是下划线 ⇒ 正则要认两种写法)
    m = re.search(r"`?artifact[-_]checks`?[^\d\n]{0,12}\*\*(\d+)", ft)
    if not m:
        fail("FACTS.md: 找不到 artifact_checks 门数")
    else:
        out["artifact_checks"] = int(m.group(1))

    # 断言强度审计的三个数(2026-11-02 加)—— README 的「Assertion audit」那一行
    # 用的是「N scanned / N runnable / N real assertions」这套词汇,
    # 原 PASS_RE 完全看不见它 ⇒ 这里把它们解析出来,好让门能对拍。
    m = re.search(r"扫描\s*(\d+)\s*·\s*可跑\s*(\d+)\s*·\s*真断言\s*(\d+)", ft)
    if not m:
        fail("FACTS.md: 找不到断言强度审计那一行（`扫描 N · 可跑 N · 真断言 N`）")
    else:
        out["scanned"] = int(m.group(1))
        out["runnable"] = int(m.group(2))
        out["real_assertions"] = int(m.group(3))

    # 产物尺寸(FACTS § 1)—— 两份 README 各复述一遍,原先零门覆盖。
    for key, pat in (("size_installer", r"jhyy-installer-[\d.]+\.exe`\s*\|\s*~([\d.]+)\s*MB"),
                     ("size_msi", r"jhyy-compiler-[\d.]+\.msi`\s*\|\s*~([\d.]+)\s*MB"),
                     ("size_exe", r"编译器二进制[^\n]*?~([\d.]+)\s*MB")):
        m = re.search(pat, ft)
        if not m:
            fail(f"FACTS.md: 找不到 {key} 的尺寸声明")
        else:
            out[key] = m.group(1)

    if "fixed_point.sh" not in ft:
        fail("FACTS.md: 没有提到 fixed_point.sh")

    return out


# --------------------------------------------------------------------------
# B/C. 与现实对拍
# --------------------------------------------------------------------------
LEDGER_STATES = ("ACTIVE", "DEFERRED", "RESOLVED", "SUPERSEDED", "INVALID")


def parse_ledger(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """把台账拆成「正文状态」与「索引状态」两张表。

    **正文**：按 `<a id="w-NNN"></a>` 切块，取每块**第一条** `**状态:**` 行的 5 态枚举。
    **索引**：`| [W-NNN](#anchor) | STATUS | ...` 行。

    两处容错（都是台账里的既有结构，不是 bug）：
    - §1 登记规范的**模板锚点** `w-NNN` —— 它的状态行写的是 `<STATUS>`，不是合法枚举 ⇒ 跳过。
    - 遗留**重复锚点** `w-105-1`（与 `w-105.1` 相邻的空锚点）—— 它没有状态行 ⇒ 跳过。

    为什么要正文解析：`check_ledger()` 原来只数**索引行**，所以正文里的状态漂移
    （条目被改成 ACTIVE、正文整段删掉只留索引行）门都看不见 —— FACTS.md 声明的
    「RESOLVED / SUPERSEDED / INVALID = 153 / 9 / 2」当时**没有任何门在读**。
    """
    idx: dict[str, str] = {}
    for m in re.finditer(r"^\| \[(W-[\w.\-]+)\]\(#[^)]+\) \| ([A-Z]+) \|", text, re.M):
        idx[m.group(1)] = m.group(2)

    body: dict[str, str] = {}
    # 用 finditer 切段而不是 re.split —— 相邻锚点（`w-105-1` 与 `w-105.1`）在
    # split 下会互相吃掉换行，导致后者的正文被算到前者名下。
    anchors = list(re.finditer(r'<a id="(w-[\w.\-]+)"></a>', text))
    for i, a in enumerate(anchors):
        start = a.end()
        end = anchors[i + 1].start() if i + 1 < len(anchors) else len(text)
        m = re.search(r"^\*\*状态:\*\*\s*([A-Z]+)", text[start:end], re.M)
        if not m:
            continue                       # 无状态行（空锚点 / 非条目块）
        if m.group(1) not in LEDGER_STATES:
            continue                       # 规范模板里的 `<STATUS>` 占位
        body[a.group(1).upper()] = m.group(1)
    return body, idx


def check_ledger(d: dict) -> None:
    wm = ROOT / "docs" / "internal" / "workarounds.md"
    if not wm.is_file():
        fail("docs/internal/workarounds.md 不存在")
        return
    text = read(wm)
    idx_rows = len(re.findall(r"^\| \[W-", text, re.M))
    active = len(re.findall(r"^\| \[W-[^\]]+\]\(#[^)]+\) \| ACTIVE \|", text, re.M))
    if "ledger_total" in d and idx_rows != d["ledger_total"]:
        fail(f"台账索引 {idx_rows} 行 != FACTS.md 声明的 {d['ledger_total']} 行")
    if "active" in d and active != d["active"]:
        fail(f"台账 ACTIVE {active} 条 != FACTS.md 声明的 {d['active']} 条")

    # ── 正文解析 + per-status 对拍（原来只查索引行，正文漂移门看不见）──
    body, idx = parse_ledger(text)
    if "ledger_total" in d and len(body) != d["ledger_total"]:
        fail(f"台账正文条目 {len(body)} 条 != FACTS.md 声明的 {d['ledger_total']} 条")

    counts = {s: sum(1 for v in body.values() if v == s) for s in LEDGER_STATES}
    for key, state in (("active", "ACTIVE"), ("deferred", "DEFERRED"),
                        ("resolved", "RESOLVED"), ("superseded", "SUPERSEDED"),
                        ("invalid", "INVALID")):
        if key in d and counts[state] != d[key]:
            fail(f"台账正文 {state} {counts[state]} 条 != FACTS.md 声明的 {d[key]} 条")

    # 索引状态 ↔ 正文状态必须一致（索引是索引表的副本，不是真相）
    for wid, st in idx.items():
        b = body.get(wid.upper())
        if b is None:
            fail(f"台账索引有 {wid}，但正文没有对应条目")
        elif b != st:
            fail(f"台账 {wid}: 索引状态 {st} != 正文状态 {b}")


def check_gates(d: dict) -> None:
    ac = ROOT / "compiler" / "tests" / "bootstrap" / "artifact_checks.sh"
    if ac.is_file():
        n = len(re.findall(r"^check_[a-z_]+", read(ac), re.M))
        if "artifact_checks" in d and n != d["artifact_checks"]:
            fail(f"artifact_checks.sh 有 {n} 个 check != FACTS.md 声明的 {d['artifact_checks']}")
    else:
        fail("compiler/tests/bootstrap/artifact_checks.sh 不存在")

    fp = ROOT / "compiler" / "tests" / "bootstrap" / "fixed_point.sh"
    if not fp.is_file():
        fail("compiler/tests/bootstrap/fixed_point.sh 不存在")


# --------------------------------------------------------------------------
# D. FACTS.md 声明的每一个数,在 live 文档里被复述时必须一致
# --------------------------------------------------------------------------
# **为什么整个重写（2026-11-02 审计实测）**：原实现有**四个叠加**的盲区，
# 实测每一个都能让**错的数字**绿灯通过：
#
#   (a) `re.sub(r"```.*?```", "")` 把围栏代码块整段剥掉 ⇒ README 的
#       `265/265 passed`（在 ```bash 块里）**根本没进被检查的正文**
#   (b) 上下文关键词 `regress|回归` 必须与数字**同一行** ⇒ README 把
#       "regression" 放在**上一行的标题**里就免检
#   (c) `PASS_RE` 只认 `N PASS`/`N passed` ⇒「N scanned / N runnable /
#       N real assertions」这类写法完全在词表外
#   (d) `HIST_RE` 豁免**任何含日期的行** ⇒ 行尾加个日期就免检
#
# 实测：把 FACTS.md + 两份 README 的回归数一起改成 999/1019（**自洽但假**）
# ⇒ **5 道门全绿**。⇒ 门必须覆盖「数字出现的每一种语法形态」。
#
# **重写后的口径**：
# - 上下文单元 = **表格行自成一体** + 其余情况取「最近的标题 + 后续连续正文」
#   ⇒ 表格里一行不会借用同一张表别的行的上下文;而「### Run the regression
#   suite」能管到它下面的代码块
# - **不再剥代码块** —— 代码块里的数同样要查
# - 词表覆盖 FACTS 声明的**每一个**数（回归三件套 + 断言审计三件套 + 门数）
# - 「当时快照」只认**显式标记**（当时 / 快照 / 修前 / 修后 …）——
#   **光有日期不算** ⇒ live 文档里 unmarked 的旧快照就是漂移

# 每个事实数 ⇒ (复述时的正则, 同单元里必须出现的上下文关键词)
FACT_NUMBERS = {
    "pass": (
        r"(?<![\w.])(\d{1,5})\s*(?:/\s*(\d{1,5})\s*)?(?:PASS|passed)\b",
        r"regress|回归"),
    "skip": (
        r"(?<![\w.])(\d{1,5})\s*SKIP(?:ped)?\b",
        r"regress|回归"),
    "total": (
        r"(?<![\w.])(\d{1,5})\s+total\b",
        r"regress|回归"),
    "scanned": (
        r"(?<![\w.])(\d{1,5})\s*scanned\b|扫描\s*(\d{1,5})(?!\w)|扫\s*(\d{1,5})(?!\w)",
        r"assertion|断言|audit"),
    "runnable": (
        r"(?<![\w.])(\d{1,5})\s*runnable\b|可跑\s*(\d{1,5})(?!\w)",
        r"assertion|断言|audit"),
    "real_assertions": (
        r"(?<![\w.])(\d{1,5})\s*real assertions\b|真断言\s*(\d{1,5})(?!\w)",
        r"assertion|断言|audit"),
    "artifact_checks": (
        r"(?<![\w.])(\d{1,3})\s*(?:条\s*)?(?:门|道|gates?|PASS\b)",
        r"artifact_checks|bootstrap|产物级门"),
}

# 「这是当时的快照」—— 只认**显式标记**;**光有日期不算**
# （原实现豁免任何含 `20\d\d-\d\d-\d\d` 的行 ⇒ 行尾加个日期就能免检,已修）
HIST_RE = re.compile(r"当时|快照|历史|持平|baseline|已过时|修前|修后|C-side|反面例子")

# 「其中 4 条门」是**子集**计数,不是「总门数」⇒ 不判
SUBSET_RE = re.compile(r"(?:其中|里有|内有|这\s*)\s*$")


def fact_units(text: str) -> list[tuple[int, str]]:
    """(行号, 上下文单元) —— 用来判断「这个数说的是哪件事」。

    - **表格行(`|`)自成单元** ⇒ 一行里的数字不会借用**同一张表的别的行**的上下文
      （否则 `artifact_checks.sh | 18 PASS` 会借用上一行 `regress.py` 的上下文）
    - 其余情况：连续的正文行 + **最近的上级标题** 合成一个单元
      ⇒ 「### Run the regression suite」能管到它下面的 ```bash 代码块
    - ⚠️ **围栏代码块内的行一律当正文** —— 代码块里的 `# 注释` **不是标题**
      （踩过一次：`# => 265/265 passed` 被当成标题 ⇒ 把上面的真标题顶掉了 ⇒
      上下文关键词丢失 ⇒ 代码块里的数免检）
    """
    units: list[tuple[int, str]] = []
    cur: list[str] = []
    start = 0
    heading = ""
    in_fence = False

    def flush() -> None:
        nonlocal cur
        if cur:
            units.append((start, heading + "\n" + "\n".join(cur)))
            cur = []

    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            if not cur:
                start = i
            cur.append(line)
            continue
        if not in_fence and s.startswith("|"):
            flush()
            units.append((i, line))
            continue
        if not in_fence and not s:
            flush()
            continue
        if not in_fence and s.startswith("#"):
            flush()
            heading = s
            continue
        if not cur:
            start = i
        cur.append(line)
    flush()
    return units


def _first_int(m: re.Match) -> int:
    """取第一个非空捕获组当数(词表里有的写法数字在前、有的在后)。"""
    for g in m.groups():
        if g is not None:
            return int(g)
    return -1


def check_artifact_sizes(d: dict) -> None:
    """产物尺寸在 FACTS.md 与两份 README 之间必须一致。

    ⚠️ **这只保证「一致」,不保证「为真」** —— 真正的尺寸要靠实测产物
    （installer 打包后才知道）。但**两份 README 各复述一遍**、中间没有任何门
    ⇒ 至少要保证它们跟 FACTS 对得上。
    """
    rules = [
        ("size_installer", r"jhyy-installer[-\d.]*\.exe"),
        ("size_msi", r"jhyy-compiler[-\d.]*\.msi"),
        ("size_exe", r"jhyy\.exe"),
    ]
    for key, art_re in rules:
        want = d.get(key)
        if not want:
            continue
        for rel in ("README.md", "README.zh-CN.md"):
            p = ROOT / rel
            if not p.is_file():
                continue
            for i, line in enumerate(read(p).splitlines(), 1):
                if not re.search(art_re, line):
                    continue
                for m in re.finditer(r"~?\s*([\d.]+)\s*MB", line):
                    if m.group(1) != want:
                        fail(f"{rel}:{i}: 产物的尺寸写成 {m.group(1)} MB,"
                             f"FACTS.md § 1 声明的是 {want} MB")


def check_ledger_version_labels() -> None:
    """台账里**前向引用**的 `(vX.Y.Z)` 标签必须指向真实存在的版本记录。

    **为什么需要这道检查（2026-11-02 实测）**：台账的 `**状态:**` 行带一个
    `(vX.Y.Z)` 标签表示「这一版闭合」⇒ 它应该指向一个**已发布**的版本
    (CHANGELOG.md 的 Releases 表)或一个**change slot**
    (umbrella changelog 里的 `## vX.Y.Z` 段)。
    实测:W-170 … W-183 等 14 条标着 `(v4.1.3)`,而 **v4.1.3 在任何 changelog 里
    都不存在** ⇒ 标签指向了一个虚空 ⇒ 而台账的「不删不改」约定让这种漂移永远不会被
    肉眼发现。⇒ 这道检查把它变成响亮的。

    ⚠️ **只查前向引用**（标签的版本 > 当前 `VERSION`）—— 历史版本(v3.2.3 / v4.0.9
    这种)有的在旧轴的 changelog 里、有的压根没单独立段,要求它们全部可解析是不合理的。
    """
    wm = ROOT / "docs" / "internal" / "workarounds.md"
    if not wm.is_file():
        return
    ver_file = ROOT / "VERSION"
    if not ver_file.is_file():
        return
    latest = ver_file.read_text(encoding="utf-8").strip()

    def vt(v: str) -> tuple[int, ...]:
        try:
            return tuple(int(x) for x in v.split("."))
        except ValueError:
            return ()

    latest_t = vt(latest)
    if not latest_t:
        return
    known: set[str] = set()
    rcl = ROOT / "CHANGELOG.md"
    if rcl.is_file():
        known |= set(re.findall(r"\|\s*\*\*v(\d+\.\d+\.\d+)\*\*\s*\|", read(rcl)))
    for umb in (ROOT / "docs" / "archive" / "logs").rglob("changelog-v*.md"):
        known |= set(re.findall(r"^##\s+v(\d+\.\d+\.\d+)\b", read(umb), re.M))
    if not known:
        return
    text = read(wm)
    for m in re.finditer(r"\*\*状态:\*\*\s*([^\n]*)", text):
        line = m.group(1)
        for v in re.findall(r"\((v\d+\.\d+\.\d+)\)", line):
            ver = v[1:]
            if ver in known:
                continue
            vt_ver = vt(ver)
            if not vt_ver or vt_ver <= latest_t:
                continue          # 历史版本 —— 不要求它有独立 changelog 段
            head = text.rfind("\n## ", 0, m.start())
            title = text[head + 1:text.find("\n", head + 1)].strip()
            fail(f"台账条目「{title[:60]}」的标签 ({v}) 指向一个**不存在**的版本 —— "
                 f"它比当前 VERSION({latest}) 还新 ⇒ 要么在 CHANGELOG.md / umbrella "
                 f"changelog 里补上 `{v}` 的记录(已发布或 change slot),要么这个标签写错了")


def check_fact_numbers(d: dict) -> None:
    """FACTS.md 声明的每个数,在 live 文档里被复述时必须一致。"""
    if "pass" not in d:
        return
    for p in all_md():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("docs/archive/") or rel == "docs/internal/workarounds.md":
            continue          # 历史记录不追溯;台账每条 entry 的证据都是当时快照
        text = read(p)
        for lineno, unit in fact_units(text):
            for key, (pat, ctx) in FACT_NUMBERS.items():
                if key not in d:
                    continue
                want = d[key]
                if not re.search(ctx, unit, re.I):
                    continue
                if HIST_RE.search(unit):
                    continue      # 明确标了「当时/快照」⇒ 是历史快照,不是当前基线
                for m in re.finditer(pat, unit, re.I):
                    pre = unit[max(0, m.start() - 8):m.start()]
                    if SUBSET_RE.search(pre):
                        continue      # 「其中 4 条门」= 子集计数,不是总数
                    got = _first_int(m)
                    if got == want:
                        continue
                    fail(f"{rel}:{lineno}: 写了「{m.group(0).strip()}」"
                         f"（{key} 应为 {want}）—— 要么改 FACTS.md,要么改成**引用**它"
                         f"（不要复述数字）")


# --------------------------------------------------------------------------
# E. 链接 + 锚点
# --------------------------------------------------------------------------
def slug(s: str) -> str:
    s = re.sub(r"`", "", s.strip()).lower()
    s = re.sub(r"[^\w\- ]", "", s, flags=re.UNICODE)
    return s.strip().replace(" ", "-")


def anchors_of(path: Path) -> set[str]:
    text = read(path)
    hs = set()
    for m in re.finditer(r"^#{1,6}\s+(.*)$", text, flags=re.M):
        hs.add(slug(m.group(1)))
    for m in re.finditer(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', text, flags=re.I):
        hs.add(m.group(1).lower())
    return hs


def tracked_files() -> set[str]:
    """仓内**被 git 跟踪**的文件(相对路径,正斜杠)。

    为什么必须用这个集合而不是「磁盘上存在」:
    根 `CLAUDE.md` 已移出版本控制(它现在是本地 agent 提示词)⇒ 磁盘上存在、
    但**clone 的人拿不到** ⇒ 指向它的链接对读者就是断的。
    2026-10-30 的 CI 就是这样红了一次而本地是绿的。
    """
    import subprocess
    try:
        # ⚠️ **必须显式 encoding="utf-8"** —— `text=True` 用的是**系统 locale**
        # (中文 Windows = cp936 / CI = cp1252),而 git 的路径是 UTF-8
        # ⇒ 中文文件名被解码成乱码 ⇒ tracked 集合里匹配不上
        # ⇒ 表现为「一堆明明在仓里的文件被判成未入仓」(2026-10-30 CI 实测 183 处假阳性)。
        # `-z` = NUL 分隔 ⇒ 不受行分隔与 core.quotePath 的引号影响。
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", check=True).stdout
    except Exception:
        return set()
    return {ln.replace("\\", "/") for ln in out.split("\0") if ln.strip()}


def check_links() -> None:
    link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    cache: dict[str, set[str]] = {}
    tracked = tracked_files()
    broken = 0
    for p in all_md():
        rel = p.relative_to(ROOT).as_posix()
        body = re.sub(r"```.*?```", "", read(p), flags=re.S)
        for m in link_re.finditer(body):
            t = m.group(1).strip().split(' "')[0].split(" '")[0]
            if t.startswith(("http://", "https://", "mailto:")) or not t:
                continue
            path, _, anc = t.partition("#")
            if not path:
                cand = p                       # 同页锚点
            elif path.startswith("/"):
                cand = ROOT / path.lstrip("/")
            else:
                cand = p.parent / urllib.parse.unquote(path)
            try:
                cand = cand.resolve()
            except OSError:
                pass
            if not cand.exists():
                broken += 1
                if broken <= 20:
                    fail(f"{rel}: 断链 → {t}")
                continue
            # 磁盘上有、但**不在 git 里** ⇒ clone 的人拿不到 ⇒ 同样是断链
            try:
                rel_target = cand.resolve().relative_to(ROOT.resolve()).as_posix()
            except (ValueError, OSError):
                # 解析到了**仓外**(本地恰好有同名文件、CI 上没有 ⇒ 同一个链接两种结果)
                broken += 1
                if broken <= 20:
                    fail(f"{rel}: 指向**仓外**的路径 → {t}"
                         f"（本地可能恰好存在同名文件，clone 后必然断）")
                continue
            # 目录目标:git 不跟踪目录本身,只跟踪里面的文件 ⇒ 用前缀判「非空且被跟踪」
            if rel_target and rel_target.endswith("/"):
                rel_target = rel_target.rstrip("/")
            if rel_target and tracked and cand.is_dir():
                has_tracked = any(k.startswith(rel_target + "/") for k in tracked)
            elif rel_target and tracked:
                has_tracked = rel_target in tracked
            else:
                has_tracked = True
            if rel_target and tracked and not has_tracked:
                broken += 1
                if broken <= 20:
                    fail(f"{rel}: 指向**未入仓**的文件 → {t}"
                         f"（clone 后拿不到；该文件已被移出版本控制）")
            if anc and cand.suffix.lower() == ".md":
                key = str(cand)
                if key not in cache:
                    cache[key] = anchors_of(cand)
                if anc.lower() not in cache[key]:
                    broken += 1
                    if broken <= 20:
                        fail(f"{rel}: 死锚点 → {t}")
    if broken > 20:
        fail(f"…… 断链/死锚点共 {broken} 处（上面只列了前 20 条）")


# --------------------------------------------------------------------------
# E2. 反引号里的裸路径 —— 另一类引用面
# --------------------------------------------------------------------------
# 为什么要这道门：`check_links()` 只匹配 `[text](path)` 形式的 inline 链接。
# **反引号包裹的裸路径**（`` `docs/abis/xxx.md` ``、`` `compiler/src0/foo.jhyy` ``）
# 整类从未被任何门扫过 —— 2026-10-31 审计实测：docs/** 里 1205 处反引号路径
# 指向不存在的目标（live 207 / archive 998）。⇒「inline 链接 0 断链」被读成
# 「文档引用健康」是错的 —— 它只覆盖了引用面的一半。
#
# 口径（宁可漏报也不要误报：误报会让门永远红，等于没有门）：
# - **只看 live 文档** —— `docs/archive/` 按约定「归档的内容不改」，那些是历史快照。
# - **台账 `docs/internal/workarounds.md` 豁免** —— 它的条目按约定「不删不改」，
#   正文里提到已删除的文件（v4.0.21 删掉的 `compiler/src/*.c` 等）是**审计轨迹**。
#   门会把这类引用的条数打出来（信息，不判红）。
# - 目标按**两种基准**解析：相对**当前文档所在目录**、相对**仓库根**（两种写法本仓都在用）。
# - 跳过：占位符（`vX.Y.Z` / `<...>` / `...` / `*`）、绝对路径（`/usr/...`、`C:\...`）、
#   不含 `/` 的裸文件名（`jhyy.exe` 这种无从判断基准）、顶层目录不在仓里的路径、
#   以及 **.gitignore 里的路径**（构建产物：自举 .s、installer/SHA256.txt 等 ——
#   文档引用它们是在描述「产物在哪」，不是引用错路径）。
BACKTICK = re.compile(r"`([^`\n]{2,160})`")
# `path:123` / `path:12-34` —— 行号后缀
LINE_SUFFIX = re.compile(r"^(.*?):(\d+(?:-\d+)?)$")
PATHY = re.compile(
    r"\.(?:md|jhyy|c|h|py|sh|ps1|json|txt|rtf|wxs|yml|yaml|sha256|exe|msi|vsix|asm|s|il|o|ld|flag|buf|sym)$")
PLACEHOLDER = re.compile(r"[<>{}\*…]|\.\.\.|X\.Y|xxx|\$[A-Za-z_]|\bNNN\b")
REPO_TOP = {"compiler", "docs", "installer", "mcp-jhyy", "runtime", "scripts",
            "tools", "vscode-ext", ".github"}
LEDGER_REL = "docs/internal/workarounds.md"


def _gitignored(paths: list[str]) -> set[str]:
    """哪些路径被 .gitignore 忽略（= 构建产物，不是引用错）。批量问 git，一次进程。"""
    if not paths:
        return set()
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--stdin", "-z"],
                           input="\0".join(paths) + "\0",
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
    except Exception:
        return set()
    return {p for p in r.stdout.split("\0") if p}


def _ever_existed() -> set[str]:
    """本仓历史上**曾经存在过**的所有路径（`git log --all --diff-filter=A --name-only`）。

    ⚠️ **不要用这个做判红依据** —— 它依赖克隆深度：CI 的 `actions/checkout@v4`
    默认是 **depth 1 的浅克隆** ⇒ `git log --all` 只能看到 tip 那一个 commit ⇒
    「曾存在过」的路径全都不在集合里 ⇒ 同一份代码本地绿、CI 红。
    ⇒ 门的行为**不能**随克隆深度变化。本函数只用于**报告**（信息），不参与判红。
    """
    import subprocess
    try:
        r = subprocess.run(
            ["git", "-C", str(ROOT), "log", "--all", "--diff-filter=A",
             "--name-only", "--pretty=format:"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
    except Exception:
        return set()
    return {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}


def check_backtick_paths() -> None:
    """反引号里的裸路径是否指向真实存在的文件（口径见上面的注释）。"""
    hist = 0
    cands: list[tuple[Path, list[str], str]] = []   # (文件, 候选路径(仓根相对), token)
    for p in all_md():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("docs/archive/"):
            continue
        body = re.sub(r"```.*?```", "", read(p), flags=re.S)   # 代码块里的是示例
        for m in BACKTICK.finditer(body):
            tok = m.group(1).strip()
            if " " in tok or "/" not in tok:
                continue
            if PLACEHOLDER.search(tok) or tok.startswith("/"):
                continue
            # 盘符路径(`C:\...`)不是仓内路径 ⇒ 跳过
            if re.match(r"^[A-Za-z]:[\\/]", tok):
                continue
            # ⚠️ `path:123` / `path:12-34` 形态的引用 —— **行号后缀不是路径的一部分**
            #    (原实现 `":" in tok ⇒ continue` 把**整类** `file:line` 引用挡在门外
            #     ⇒ `compiler/src0/emit_ctrl.jhyy:565` 这类引用**从来没被检查过**)
            m_ln = LINE_SUFFIX.match(tok)
            if m_ln:
                tok = m_ln.group(1)
                if " " in tok or "/" not in tok:
                    continue
            if not PATHY.search(tok):
                continue
            top = tok.split("/")[0]
            if top not in REPO_TOP and not (ROOT / tok).exists():
                continue
            if (p.parent / tok).exists() or (ROOT / tok).exists():
                continue
            # 两种基准都要试：**仓根相对**（本仓文档最常见的写法）与
            # **相对当前文档目录**。只算一种会把另一种判成「不存在」。
            cands_list = [tok]
            try:
                rel_doc = (p.parent / tok).resolve().relative_to(ROOT.resolve()).as_posix()
                if rel_doc != tok:
                    cands_list.append(rel_doc)
            except (ValueError, OSError):
                pass
            cands.append((p, cands_list, tok))

    flat = [c for _, cs, _ in cands for c in cs]
    ignored = _gitignored(flat)
    for p, cands_list, tok in cands:
        rel = p.relative_to(ROOT).as_posix()
        if any(c in ignored for c in cands_list):
            continue                       # 构建产物（gitignore 的）
        if rel == LEDGER_REL:
            hist += 1
            continue                       # 台账 = 审计轨迹（条目不删不改）
        fail(f"{rel}: 反引号里的裸路径不存在 → {tok}")
    if hist:
        print(f"  （台账 workarounds.md 另有 {hist} 处引用指向已删除文件 —— 按「条目不删不改」"
              f"的审计轨迹约定豁免，不判红）")


# --------------------------------------------------------------------------
# E3. `feedback_*` 代号必须能在仓内的索引里查到
# --------------------------------------------------------------------------
# 2026-10-31 加：工作规约整体搬出仓内后，**代号 → 规约的映射表也没进仓** ⇒
# 63 个 `feedback_*` 代号散落在 143 份文档（外加若干源码 / CI 文件）里，
# 读者**检索得到线索、解析不出含义**。⇒ 把**索引**搬回仓内
# （`docs/internal/feedback-codes.md`；规约正文仍留仓外，工作规约是对内的），
# 并加这道门防它再退化。
#
# 这道门是**零误报**的：索引是仓内的一个已提交文件 ⇒ 判红只可能是「真有个代号
# 没进索引」。**不依赖 git 历史** ⇒ 浅克隆 / 深克隆行为一致。
CODE_TOKEN = re.compile(r"feedback_[a-z0-9_]+")
CODE_TEXT_EXT = (".md", ".jhyy", ".py", ".yml", ".yaml", ".sh", ".ps1", ".ts", ".txt", ".c", ".h")


def check_code_index() -> None:
    """仓内用到的每个 `feedback_*` 代号都必须能在 `docs/internal/feedback-codes.md` 里查到。"""
    idx = ROOT / "docs" / "internal" / "feedback-codes.md"
    if not idx.is_file():
        fail("docs/internal/feedback-codes.md 不存在 —— `feedback_*` 代号索引必须在仓内")
        return
    known = set(CODE_TOKEN.findall(read(idx)))

    used: dict[str, list[str]] = {}
    import subprocess
    names = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"],
                           capture_output=True, text=True, encoding="utf-8").stdout.split("\0")
    for n in names:
        if not n or not n.endswith(CODE_TEXT_EXT):
            continue
        try:
            body = read(ROOT / n)
        except OSError:
            continue
        for c in set(CODE_TOKEN.findall(body)):
            if c != "feedback_xxx":       # 规范里的占位符
                used.setdefault(c, []).append(n)

    for c in sorted(used):
        if c in known:
            continue
        where = used[c]
        fail(f"feedback_* 代号 `{c}` 不在 docs/internal/feedback-codes.md 里"
             f"（{len(where)} 处用到，例：{where[0]}）")


# --------------------------------------------------------------------------
# I. `§ N.M` 跨文档章节引用 —— 指向真实存在的章节
# --------------------------------------------------------------------------
# **为什么单开一道**(2026-11-01 审计实测):`check_links` 只认 markdown 链接,
# **`§ N.M` 这种「章节地址」完全没人查** ⇒ 章节号写错、指向不存在的章节,门不会红。
# 实测跨文档悬空只有 4 条 —— 但真因不是章节写错,而是**把行号写成了章节号**
# (`lang-spec §117` 实指 lang-spec 的第 117 行)。
#
# **章节号有三种形态,漏一种就会把真存在的章节判成悬空**:
#   1. 标题          `### 4.2.1 聚合类型的相等比较`
#   2. 表格行首编号  `| 12.8 | ...`  ← abi § 12 的子项是这种,**不是标题**
#   3. 锚点          `<a id="abi-12-8"></a>` ← 同上
# 另:**合并标题** `## 10-11. 通用 Section Data` 要抽出**两个**号(10 和 11)。
#
# **只查「目标文档明确」的那种引用** —— 裸 `§ N.M` 的目标文档有歧义,查了必假阳;
# 目标由两种方式给出:(a) 文档名 token 紧邻(`abi §12.10`);(b) 同行的 markdown 链接
# (`[...](…/jhyy-abi-v4.0.0.md) § 2.5`)。取**最近的、在其之前**的那个目标。

_DOC_FILES = {
    "lang": "docs/abis/jhyy-lang-spec-v4.0.0.md",
    "abi": "docs/abis/jhyy-abi-v4.0.0.md",
    "binary": "docs/abis/jhyy-binary-format-v1.0.0.md",
    "编译器侧": "docs/coordination/JHYY_编译器侧设计终版.md",
    "OS侧": "docs/coordination/JHYY_OS侧设计终版.md",
}
_DOC_BY_BASENAME = {Path(v).name: k for k, v in _DOC_FILES.items()}
# 文档名 token(小写、空格归一) → 目标文档 key。`本文` = 当前文档自身。
_TOKEN_TO_KEY = {
    "lang-spec": "lang", "语言规范": "lang",
    "abi": "abi",
    "binary-format": "binary", "二进制格式": "binary",
    "编译器侧": "编译器侧",
    "os侧": "OS侧",
    "本文": "SELF",
}

# 文档名 token → 目标文档。`本文` = 当前文档自身。
# ⚠️ **ASCII token 两侧要挡字母** —— 否则 `psABI § 3.2.2`(System V psABI,不是本仓的 abi)
#    会被当成本仓 abi 的引用 ⇒ 假阳性。用 `(?<![A-Za-z])` 而不是 `\b`:
#    **中文字符在 Python 里也是 \w** ⇒ `\b` 会把「见abi §12.10」这种中文紧邻的写法挡掉。
_SEC_TOKEN_RE = re.compile(
    r"(?P<tok>"
    r"(?<![A-Za-z])lang-spec(?![A-Za-z])"
    r"|(?<![A-Za-z])binary-format(?![A-Za-z])"
    r"|(?<![A-Za-z])abi(?![A-Za-z])"
    r"|语言规范|二进制格式|编译器侧|OS\s*侧|本文"
    r")"
    r"\s*(?:\*\*)?\s*[:：]?\s*(?:\*\*)?\s*§\s*(?P<sec>\d+(?:\.\d+)*)",
    re.I)
_SEC_RE = re.compile(r"§\s*(\d+(?:\.\d+)*)")
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _sections_of(text: str) -> set[str]:
    """抽出文本里存在的全部章节号(标题 / 带锚点的表格行 / 锚点 / 合并标题)。"""
    secs: set[str] = set()
    # 1. 标题。⚠️ **不要加 `(?![\d.])` 之类的 lookahead** —— 章节号后面本来就跟 `.`
    #    (`## 8. IPC Dispatch Table`)⇒ 加了就把整份文档的章节抽空,门全线假阳。
    for m in re.finditer(r"^#{1,6}\s*(?:§\s*)?(\d+(?:\.\d+)*)", text, re.M):
        secs.add(m.group(1))
    # 1b. **合并标题** `## 10-11. 通用 Section Data` ⇒ 10 和 11 **两个**号都存在。
    #     要求尾部有 `.`(日期式标题 `## 2026-10-31` 不匹配 ⇒ 不污染)。
    for m in re.finditer(r"^#{1,6}\s*(\d+(?:\.\d+)*)\s*[-–]\s*(\d+(?:\.\d+)*)\s*[.、]", text, re.M):
        secs.add(m.group(1))
        secs.add(m.group(2))
    # 2./3. 带 `<a id="...">` 的表格行 —— abi § 12 的 14 个子项是这种。
    #    ⚠️ **只认带锚点的行**:否则任何「| 1 | ...」的表都会把 `1` 变成一个章节号。
    for m in re.finditer(r'^\|\s*<a id="[^"]*"></a>\s*(\d+(?:\.\d+)*)\s*\|', text, re.M):
        secs.add(m.group(1))
    for m in re.finditer(r'<a id="[a-z]+-(\d+(?:-\d+)*)"></a>', text):
        secs.add(m.group(1).replace("-", "."))
    return secs


def _section_exists(secs: set[str], sec: str) -> bool:
    if sec in secs:
        return True
    # 父章节也算存在:文档里有 § 4.2.1 ⇒ § 4.2 也在(层级蕴含)
    prefix = sec + "."
    return any(s.startswith(prefix) for s in secs)


def check_section_refs() -> None:
    """`§ N.M` 必须指向真实存在的章节。"""
    cache: dict[str, set[str]] = {}

    def secs_of(rel: str) -> set[str]:
        if rel not in cache:
            cache[rel] = _sections_of(read(ROOT / rel))
        return cache[rel]

    for p in all_md():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("docs/archive/"):
            continue  # 归档不改,可能引用旧编号
        for i, line in enumerate(read(p).splitlines(), 1):
            # 目标锚点:(位置, 目标文档 key 或 "SELF")
            anchors: list[tuple[int, str]] = []
            for m in _SEC_TOKEN_RE.finditer(line):
                tok = re.sub(r"\s+", "", m.group("tok")).lower()
                key = _TOKEN_TO_KEY.get(tok)
                if key:
                    anchors.append((m.start(), key))
            for m in _MD_LINK_RE.finditer(line):
                t = m.group(1).split("#")[0].strip()
                if not t:
                    continue
                key = _DOC_BY_BASENAME.get(Path(urllib.parse.unquote(t)).name)
                if key:
                    anchors.append((m.end(), key))
            if not anchors:
                continue
            anchors.sort()
            for m in _SEC_RE.finditer(line):
                # 最近的、在它之前的锚点
                target = None
                for pos, key in anchors:
                    if pos <= m.start():
                        target = key
                    else:
                        break
                if target is None:
                    continue
                trel = rel if target == "SELF" else _DOC_FILES[target]
                secs = secs_of(trel)
                if not secs:
                    continue
                sec = m.group(1)
                if not _section_exists(secs, sec):
                    fail(f"{rel}:{i}: 「§ {sec}」→ {trel} 无此章节 —— {line.strip()[:90]}")


# --------------------------------------------------------------------------
# F. FACTS.md 引用的文件存在
# --------------------------------------------------------------------------
def check_facts_links() -> None:
    if not FACTS.is_file():
        return
    for m in re.finditer(r"\]\(([^)]+)\)", read(FACTS)):
        t = m.group(1).split("#")[0]
        if not t or t.startswith(("http://", "https://")):
            continue
        cand = (FACTS.parent / urllib.parse.unquote(t)).resolve()
        if not cand.exists():
            fail(f"docs/internal/FACTS.md: 引用的文件不存在 → {t}")


# --------------------------------------------------------------------------
# J. CI 里跑的门，必须在 FACTS.md § 2 登记
# --------------------------------------------------------------------------
# **为什么**:FACTS.md § 2 是「门」的**完整清单**（`CONTRIBUTING.md` 明说让读者
# 去那里找）⇒ 少登记一道门,读者就少跑一道。
# 2026-11-01 实测:CI 跑 6 个 `scripts/dev/*.py` 门,FACTS.md 只点名了 2 个
# (`bump_version` / `docs_facts_check`) ⇒ **另外 4 个是「有门但清单里没有」**。
#
# 口径(2026-11-03 重写):**以 CI 为准**,但「以 CI 为准」这句话本身必须有机制兜着。
# 非门脚本(`regalloc_reference.py` 对拍工具、一次性重建脚本、bench/build/install/test 目录)
# 不在 CI 里 ⇒ 不要求登记。
CI = ROOT / ".github" / "workflows" / "ci.yml"
WORKFLOWS = [CI, ROOT / ".github" / "workflows" / "release.yml"]

# 门在 workflow 里的标记:`# gate: <id>`
GATE_MARK_RE = re.compile(r"#\s*gate:\s*([a-z0-9][a-z0-9-]*)")

# ── 非门步骤的**显式白名单** ──────────────────────────────────────────
# CI 里每个**带 run 块**的 step 要么是门(带 `# gate: <id>` 标记),
# 要么在这里显式登记为「不是门」。
# ⇒ 新加一个 step 会被迫分类 —— 这正是「清单自维护」的实现方式:
#   忘了登记 ⇒ 门红;想登记成门 ⇒ 必须在 FACTS § 2.2 里加一行 + 在
#   workflow 里打标记。
#
# ⚠️ 改 workflow 的 step **名字**时,这里也要跟着改(否则门会红)。
NON_GATE_STEPS = {
    ("ci.yml", "Set bash as default shell"),          # 只是把 bash 设成默认 shell
    ("release.yml", "Compute VERSION + IS_RC + JHY_TAG_NAME"),   # 只是算环境变量
    ("release.yml", "Install WiX 4/7 toolchain"),     # 只是装工具
    ("release.yml", "Install vsce (VSCode Extension CLI)"),  # 只是装工具
    ("release.yml", "Create GitHub Release"),         # 发布动作本身(不是判据)
    ("release.yml", "Dry-run summary"),               # 只是打印摘要
}


def _workflow_steps(path: Path) -> list[tuple[str, list[str]]]:
    """把一个 workflow 切成 [(step 名, run 块的行)]。

    不依赖 PyYAML(MSYS2 的 python 没有 pip 装不上)⇒ 按缩进做行级解析:
    `- name:` 开一个 step,`run:` 开一个块,块到缩进回落为止。
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    steps: list[dict] = []
    name = ""
    workdir = ""
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)- name:\s*(.+?)\s*$", line)
        if m:
            name = m.group(2).strip().strip("\"'")
            workdir = ""
            i += 1
            continue
        m = re.match(r"^(\s*)working-directory:\s*(.+?)\s*$", line)
        if m:
            workdir = m.group(2).strip().strip("\"'")
            i += 1
            continue
        m = re.match(r"^(\s*)run:\s*(.*)$", line)
        if m:
            indent = len(m.group(1))
            inline = m.group(2).strip()
            body: list[str] = []
            if inline and inline not in ("|", ">", "|-", ">-", "|+", ">+"):
                body = [inline]
            else:
                j = i + 1
                while j < len(lines):
                    l2 = lines[j]
                    if not l2.strip():
                        body.append("")
                        j += 1
                        continue
                    if len(l2) - len(l2.lstrip()) <= indent:
                        break
                    body.append(l2)
                    j += 1
                i = j - 1
            if body:
                steps.append({"name": name, "workdir": workdir, "body": body})
        i += 1
    return steps


def _facts_gate_rows(section_header: str) -> list[tuple[str, str]]:
    """从 FACTS.md 的某个小节里取门表的 (id, 整行文本)。

    门表的列约定:| 门 | `id` | 查什么 | 在哪跑 · 跑什么 |
    ⇒ id 是**第二格**、反引号包着的 slug。
    """
    if not FACTS.is_file():
        return []
    text = read(FACTS)
    lines = text.splitlines()
    out: list[tuple[str, str]] = []
    inside = False
    for line in lines:
        if re.match(r"^#{2,3}\s", line):
            inside = line.startswith(section_header)
            continue
        if not inside:
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        m = re.fullmatch(r"`([a-z0-9][a-z0-9-]*)`", cells[1])
        if m:
            out.append((m.group(1), line))
    return out


# ── 「一道门跑哪些脚本」的提取 ─────────────────────────────────────────
# 门不只是「有没有跑」,还有「跑的是**哪个**脚本」——
# 否则「在别的门的 step 里偷偷加一道新门」这种注册是看不见的。
SCRIPT_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|sh|ps1|mjs)\b")
# `pytest <路径>` —— 路径必须含 "tests"(否则 `pip install pytest pytest-asyncio`
# 里的 "pytest pytest-asyncio" 会被误当成一个测试目录)
PYTEST_RE = re.compile(r"\bpytest\s+((?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]*tests[A-Za-z0-9_./-]*)")
# 引号里的东西**不是命令** —— 报错消息里提到一个脚本名,不代表它被调用了
QUOTED_RE = re.compile(r"\"[^\"]*\"|'[^']*'")
MAKE_CMD_RE = re.compile(r"(?m)^\s*make\b")


def _scripts_in_ci(cmds: str, workdir: str = "") -> set[str]:
    """CI 步骤的命令里**真正调用了**哪些门脚本 / 门入口。

    - 引号里的片段先剥掉(报错消息里的脚本名不算调用);
    - `make` 只在**行首**才算(免得 echo 的提示语里那个 "make" 被算进去);
    - `workdir` = 该 step 的 `working-directory:` ⇒ 相对路径要拼上,
      否则「在 vscode-ext/ 下跑的 scripts/check-grammar.mjs」和 FACTS 里写的
      「vscode-ext/scripts/check-grammar.mjs」对不上。
    """
    text = QUOTED_RE.sub(" ", cmds)
    out: set[str] = set()
    for p in SCRIPT_RE.findall(text):
        if workdir and not p.startswith(workdir.rstrip("/") + "/"):
            p = f"{workdir.rstrip('/')}/{p}"
        out.add(p)
    for m in PYTEST_RE.finditer(text):
        out.add(m.group(1))
    if MAKE_CMD_RE.search(text):
        out.add("make")
    return out


def _scripts_in_facts(row: str) -> set[str]:
    """FACTS 门表那一行里写了哪些门脚本 / 门入口。

    只认**反引号里**的命令(那是这一列约定的写法)⇒ 行文里顺带提到的
    脚本名不会被算成「这道门跑的东西」。
    """
    out: set[str] = set()
    for token in re.findall(r"`([^`]+)`", row):
        text = QUOTED_RE.sub(" ", token)
        out.update(SCRIPT_RE.findall(text))
        for m in PYTEST_RE.finditer(text):
            out.add(m.group(1))
        if re.fullmatch(r"make\b", token.strip()):
            out.add("make")
    return out


def check_gate_registry() -> None:
    """门清单(FACTS § 2.2) ⇄ CI 实况,**双向**对拍。

    **为什么必须双向**(2026-11-03 门审计实测):原实现只做单向 ——
      `gates = set(re.findall(r"scripts/dev/([a-z_0-9]+\\.py)", ci))`
      ① 正则**扫全文**(含注释)⇒ 删掉门的调用行、注释里还留着路径,它照样判「已登记」;
      ② 只认 `scripts/dev/*.py` ⇒ 新增一道 `.sh`/`.ps1`/`.mjs` 门,它**看不见**;
      ③ 判据是「名字在 FACTS.md **全文**出现过」,不是「在 § 2 门表里」。
    ⇒ 「FACTS § 2 是门的完整清单」这句话当时**没有任何机制兜着**。

    **现在的口径**:
      · CI 里每个带 run 块的 step 要么是门(带 `# gate: <id>` 标记),
        要么在 `NON_GATE_STEPS` 里显式登记 ⇒ **新加 step 会被迫分类**;
      · workflow 里的标记 id ⇄ FACTS § 2.2 的 id **双向相等**;
      · 每道门**跑的是哪些脚本**也要对得上(FACTS 行里写的命令 vs step 里
        真正调用的脚本)—— 否则「在别的门的 step 里偷偷加一道新门」是看不见的;
      · § 2.3(本地门)的 id **不得**出现在 workflow 里(要接 CI 先移到 § 2.2)。
    """
    if not FACTS.is_file():
        return
    ci_ids: list[str] = []
    ci_scripts: dict[str, set[str]] = {}
    for wf in WORKFLOWS:
        if not wf.is_file():
            fail(f"workflow 不存在: {wf}")
            continue
        for st in _workflow_steps(wf):
            step_name = st["name"]
            body = st["body"]
            marks = []
            for line in body:
                for m in GATE_MARK_RE.finditer(line):
                    marks.append(m.group(1))
            uniq = sorted(set(marks))
            if len(uniq) > 1:
                fail(f"{wf.name} 的步骤「{step_name}」有多个门标记 {uniq} —— "
                     f"一个步骤只能是一道门")
            if uniq:
                ci_ids.extend(uniq)
                # 只看**非注释行** —— 注释里提到别的脚本不算「跑了它」
                cmds = "\n".join(l for l in body if not l.strip().startswith("#"))
                ci_scripts.setdefault(uniq[0], set()).update(
                    _scripts_in_ci(cmds, st["workdir"]))
                continue
            if (wf.name, step_name) not in NON_GATE_STEPS:
                fail(f"{wf.name} 的步骤「{step_name}」既没有 `# gate: <id>` 标记,"
                     f"也没登记为非门步骤 ⇒ 门清单与实况对不上。"
                     f"(是门就加标记 + 在 FACTS § 2.2 加一行;不是门就在 "
                     f"docs_facts_check.py 的 NON_GATE_STEPS 里登记)")

    facts_rows = _facts_gate_rows("### 2.2")
    facts_local = [gid for gid, _ in _facts_gate_rows("### 2.3")]
    facts_ci = [gid for gid, _ in facts_rows]
    if not facts_ci:
        fail("FACTS.md 里找不到 § 2.2「CI 门」小节(表头必须是小节标题 `### 2.2 …`)")

    for gid in sorted(set(ci_ids)):
        if gid not in facts_ci:
            fail(f"CI 里跑了门 `{gid}`,但 FACTS.md § 2.2 的门清单里没有它 "
                 f"—— CONTRIBUTING.md 让读者去 FACTS.md 找门的完整清单")
    for gid in facts_ci:
        if gid not in ci_ids:
            fail(f"FACTS.md § 2.2 登记了门 `{gid}`,但 CI 里没有对应的 `# gate: {gid}` 标记 "
                 f"⇒ 它要么没接上 CI,要么已经没人跑了")
    for gid in facts_local:
        if gid in ci_ids:
            fail(f"门 `{gid}` 在 FACTS.md § 2.3 里登记为**本地门**,却出现在 CI 里 "
                 f"⇒ 把它移到 § 2.2(CI 门)并说明为什么")
    dup = [g for g in set(facts_ci) if facts_ci.count(g) > 1]
    if dup:
        fail(f"FACTS.md § 2.2 里有重复的 id: {sorted(dup)}")

    # 每一道门**跑的是哪些脚本**也要对得上
    for gid, row in facts_rows:
        if gid not in ci_scripts:
            continue
        want = _scripts_in_facts(row)
        got = ci_scripts[gid]
        if want != got:
            only_ci = sorted(got - want)
            only_facts = sorted(want - got)
            detail = []
            if only_ci:
                detail.append(f"CI 里多跑了 {only_ci}")
            if only_facts:
                detail.append(f"清单里写了但 CI 没跑 {only_facts}")
            fail(f"门 `{gid}` 跑的命令与 FACTS.md § 2.2 那一行对不上 —— "
                 f"{'; '.join(detail)}")


# --------------------------------------------------------------------------
def main() -> int:
    print("[docs_facts_check] 检查文档事实与现实是否一致……\n")
    check_version()
    d = declared()
    if d:
        print("  FACTS.md 声明:", d)
    check_ledger(d)
    check_ledger_version_labels()
    check_gates(d)
    check_fact_numbers(d)
    check_artifact_sizes(d)
    check_links()
    check_backtick_paths()
    check_code_index()
    check_section_refs()
    check_gate_registry()
    check_facts_links()

    if problems:
        print(f"\n[docs_facts_check] FAIL —— {len(problems)} 处漂移:")
        for p in problems:
            print("  x", p)
        print("\n  修法:数字只写在 docs/internal/FACTS.md,其它文档改成引用它;")
        print("       或改 FACTS.md 让它与现实一致。")
        return 1
    print("\n[docs_facts_check] OK —— 事实与现实一致,无断链。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
