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
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    for rel, label in (("README.md", "version"), ("README.zh-CN.md", "版本")):
        p = ROOT / rel
        if not p.is_file():
            fail(f"{rel}: 文件不存在")
            continue
        m = re.search(r"badge/" + label + r"-v(\d+\.\d+\.\d+)-", read(p))
        if not m:
            fail(f"{rel}: 找不到版本徽章(badge/{label}-vX.Y.Z-)")
        elif m.group(1) != version:
            fail(f"{rel}: 徽章版本 {m.group(1)} != VERSION {version}")
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

    m = re.search(r"artifact_checks\.sh` \| \*\*(\d+)", ft)
    if not m:
        fail("FACTS.md: 找不到 artifact_checks 门数")
    else:
        out["artifact_checks"] = int(m.group(1))

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
# D. 回归基线的一致性(只管「回归基线」这个语境)
# --------------------------------------------------------------------------
PASS_RE = re.compile(r"\b(\d{2,4})\s*(?:/\s*(\d{2,4})\s*)?(?:PASS|passed)\b")
CTX_RE = re.compile(r"regress|回归")
HIST_RE = re.compile(r"v\d+\.\d+\.\d+|20\d\d-\d\d-\d\d|持平|baseline|历史|C-side|快照")


def check_pass_consistency(d: dict) -> None:
    if "pass" not in d:
        return
    want = d["pass"]
    for p in all_md():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("docs/archive/") or rel == "docs/internal/workarounds.md":
            continue          # 历史记录不追溯;台账每条 entry 的证据都是当时快照
        body = re.sub(r"```.*?```", "", read(p), flags=re.S)
        for line in body.splitlines():
            if not CTX_RE.search(line) or not PASS_RE.search(line):
                continue
            if HIST_RE.search(line):
                continue      # 当时快照,不是「当前基线」
            for m in PASS_RE.finditer(line):
                if int(m.group(1)) == want:
                    continue
                fail(f"{rel}: 写了「{m.group(0).strip()}」,与 FACTS.md 的 {want} 不一致 —— "
                     f"要么改 FACTS.md,要么改成**引用**它(不要复述数字)")


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
def main() -> int:
    print("[docs_facts_check] 检查文档事实与现实是否一致……\n")
    check_version()
    d = declared()
    if d:
        print("  FACTS.md 声明:", d)
    check_ledger(d)
    check_gates(d)
    check_pass_consistency(d)
    check_links()
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
