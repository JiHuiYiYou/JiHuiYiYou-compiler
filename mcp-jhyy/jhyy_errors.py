"""jhyy_errors.py —— 「编译器报错 → 该改哪」的索引 + 检索。

Public API:
    search(query, limit=5) -> {"ok", "version", "query", "matches": [...]}

## 为什么有这个

评测的**语言对照**（同一 AST 的 C 实现 vs JHYY 实现，29 对）测出来的结论：

- JHYY 总体只比 C 多 2% 轮数 ⇒ **「多绕」不是语法难**
- 但「少声明」「格式符错」这两类在 JHYY 上**多 5~8 轮**
- 根因：**C 的编译器报错自带修复线索**（`implicit declaration of function 'printf'`）
  而 JHYY 只说「undefined variable printf」⇒ **模型得自己查规范才知道怎么改**

⇒ 这个索引做的就是那一步翻译：**报错原文 → 含义 / 修法 / 该查哪一节 / 相关台账条目**。

## 数据来源（全部**只读**，不改编译器）

| 来源 | 提供什么 | 为什么可信 |
|---|---|---|
| `compiler/src0/*.jhyy` 静态扫描 | 编译器**真的会发**的诊断文本 | 唯一真相（编译器） |
| 规范 § 18「错误码与诊断」 | 错误码 + 高频文本 + 触发说明 | 规范是 canonical pattern 的落点 |
| 规范附录 B「已实装但受限」 | 现象说明 | 同上 |
| `compiler/tests/examples/*` 的 `EXPECT-ERROR` | **实测**的报错子串 | 真跑出来的，最可信 |
| `docs/internal/workarounds.md` | 相关 W-ID + 症状 + 绕法 | 台账 |

## ⚠️ 为什么**静态扫描**而不是往编译器里加注册表

家族规约：改 `compiler/src0/*.jhyy` 的**逻辑**会移位模块级 temp 编号
⇒ 自举产物行为漂移 ⇒ 要走全量 regress + `make` 刷锚点 + 三个 closure 门
（**不是免费改动**）。⇒ 索引**只读**编译器源码。
"""

import re
import sys
from pathlib import Path

JHYY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(JHYY_ROOT / "mcp-jhyy"))

from jhyy_workarounds import parse_workarounds, _parse_status  # noqa: E402

SPEC_PATH = JHYY_ROOT / "docs" / "abis" / "jhyy-lang-spec-v4.0.0.md"
SRC_DIR = JHYY_ROOT / "compiler" / "src0"
EXAMPLES_DIR = JHYY_ROOT / "compiler" / "tests" / "examples"
LEDGER_PATH = JHYY_ROOT / "docs" / "internal" / "workarounds.md"

# ── 归一化 ──────────────────────────────────────────────────────

# 诊断行的形态：`C:\path\file.jhyy:12:5: error: type mismatch in let`
# ⇒ 检索时用户可能直接粘**整行**，也可能只粘**消息部分**。
_PATH_LINE_RE = re.compile(r"^.*?:\d+:\d+:\s*")
_PREFIX_RE = re.compile(r"^(error|warning)\s*:\s*", re.I)


def normalize(text: str) -> str:
    """把一行诊断归一化成「消息部分」。

    ⇒ 去路径、去 `error:`/`warning:` 前缀、**去反引号**、去空白。

    ⚠️ **必须去反引号** —— 规范 § 18 的「高频文本」表里，报错原文是**反引号包着**的
    （`` `unexpected token ';' in expression` ``）⇒ 不去掉的话，用户拿着编译器
    打印出来的**裸文本**来查**匹配不上**（2026-11-13 实测）。
    """
    if not text:
        return ""
    t = _PATH_LINE_RE.sub("", text.strip())
    t = _PREFIX_RE.sub("", t)
    t = t.replace("`", "").replace("**", "")
    return " ".join(t.split()).strip()


# 英文停用词 —— 算「最长公共连续词串」时**必须剔掉**，
# 否则 "is not" / "a" 这种到处都有的词串会让**完全无关**的查询蹭到分。
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "doing", "to", "of", "in", "on", "at", "by",
    "for", "with", "from", "as", "not", "no", "or", "and", "but", "if",
    "it", "its", "this", "that", "these", "those", "i", "you", "we", "they",
})


def _tokens(text: str, drop_stop: bool = False):
    ts = [t for t in re.split(r"[^A-Za-z0-9_]+", text) if t]
    if drop_stop:
        ts = [t for t in ts if t.lower() not in _STOPWORDS]
    return ts


# ── 来源 1：编译器源码里的诊断文本 ────────────────────────────────

def _scan_parser_messages():
    """`parser.jhyy` / `main.jhyy` 里的 `jh_fputs_stderr("error: …")` 字面量。

    ⚠️ **只认 `error: ` / `warning: ` 开头的字面量** ⇒ 自动排掉测试 harness 的
    噪声（`"FAIL T13 error_count"` 之类）。
    """
    out = {}
    for name in ("parser.jhyy", "main.jhyy", "codegen.jhyy"):
        path = SRC_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            for lit in re.findall(r'"((?:error|warning)\s*:[^"]{3,90})"', line):
                msg = lit.replace("\\n", "").strip()
                # 格式前缀（`"error: "` 后面接变量）不是消息 ⇒ 跳过
                if len(msg) <= len("error: ") + 1:
                    continue
                out.setdefault(msg, name)
    return out


def _scan_sema_messages():
    """`sema.jhyy` 里 `sema_error_str(...)` / `sema_error_str_int(...)` 的**消息参数**。

    ⚠️ 消息是**调用参数**（不是以 `error: ` 开头的字面量）⇒ 得按调用点抓。
    形态：`sema_error_str(ctx, file, line, col, "消息文本" as *u8)`
    ⇒ 取**第一个字符串字面量**。
    """
    out = {}
    path = SRC_DIR / "sema.jhyy"
    if not path.exists():
        return out
    text = path.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"sema_error_str(?:_int)?\s*\(", text):
        # 从调用括号往后取一段，找第一个字符串字面量
        chunk = text[m.end():m.end() + 600]
        # 跳过前 4 个位置参数（ctx/file/line/col）⇒ 只找 `, "..."` 形态
        lit = None
        for lm in re.finditer(r'"([^"\\]{3,120})"', chunk):
            cand = lm.group(1)
            if cand.startswith(("E00", "E01", "E02")) or cand[0].isalpha():
                lit = cand
                break
        if lit:
            out.setdefault(lit, "sema.jhyy")
    return out


# ── 来源 2：规范 § 18 ────────────────────────────────────────────

def _load_spec_errors():
    """规范 § 18「错误码与诊断」：错误码表 + 高频文本表。

    返回 {错误码/文本: {"meaning": ..., "spec_ref": "§ 18"}}
    """
    if not SPEC_PATH.exists():
        return {}
    lines = SPEC_PATH.read_text(encoding="utf-8").splitlines()
    out = {}
    in_18 = False
    for line in lines:
        if line.startswith("## 18."):
            in_18 = True
            continue
        if in_18 and line.startswith("## "):
            break
        if not in_18:
            continue
        t = line.strip()
        if not t.startswith("|"):
            continue
        cells = [c.strip().replace("**", "") for c in t.strip("|").split("|")]
        if len(cells) < 2:
            continue
        key = cells[0]
        if not key or key in ("码", "---", "文本"):
            continue
        if set(key) <= set("-: "):
            continue
        meaning = cells[1] if len(cells) > 1 else ""
        out[key] = {"meaning": meaning, "spec_ref": "§ 18"}
    return out


# ── 来源 3：附录 B「已实装但受限」的现象 ─────────────────────────

def _load_appendix_b():
    """附录 B 的表格：项 + 现象（+ 台账编号）。

    ⚠️ **现象列里往往直接写着用户会撞上的报错原文**（反引号包着），例如
    `ordering comparison of a function call result is not supported for aggregate types`
    ⇒ ⇒ **要把现象里的报错原文也单独建成索引**（不然用户拿着报错来查，查不到）。

    返回 {key: {"meaning":…, "spec_ref":…, "w_ref":…, "error_text":…}}
    """
    if not SPEC_PATH.exists():
        return {}
    lines = SPEC_PATH.read_text(encoding="utf-8").splitlines()
    out = {}
    in_b = False
    for line in lines:
        if line.startswith("## 附录 B"):
            in_b = True
            continue
        if in_b and line.startswith("## "):
            break
        if not in_b:
            continue
        t = line.strip()
        if not t.startswith("|"):
            continue
        cells = [c.strip() for c in t.strip("|").split("|")]
        if len(cells) < 2:
            continue
        item = cells[0].replace("**", "")
        if not item or item in ("项", "---"):
            continue
        if set(item) <= set("-: "):
            continue
        symptom = cells[1]
        w_ref = cells[2].replace("**", "") if len(cells) > 2 else ""
        if w_ref in ("台账", "—", "-"):
            w_ref = ""
        info = {"meaning": symptom.replace("**", ""), "spec_ref": "附录 B", "w_ref": w_ref}
        out[item] = info
        # 现象列里反引号包着的**报错原文** ⇒ 也建一条
        for quoted in re.findall(r"`([^`]{8,120})`", cells[1]):
            out.setdefault(quoted, {
                "meaning": symptom.replace("**", ""),
                "spec_ref": "附录 B",
                "w_ref": w_ref,
            })
    return out


# ── 来源 4：语料的 EXPECT-ERROR 实测子串 ─────────────────────────

def _load_corpus_examples():
    """`compiler/tests/examples/*` 里 `// EXPECT-ERROR: "子串"` 的**实测**报错。

    ⇒ 这是**最可信**的一类：真跑出来的。
    """
    if not EXAMPLES_DIR.exists():
        return {}
    out = {}
    pat = re.compile(r'^\s*//\s*EXPECT-ERROR\s*[:=]\s*"([^"]+)"', re.M)
    for path in sorted(EXAMPLES_DIR.glob("*.jhyy")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = pat.search(text)
        if m:
            out.setdefault(m.group(1), path.name)
    return out


# ── 来源 5：台账 ────────────────────────────────────────────────

def _load_ledger():
    """台账里跟诊断相关的条目 ⇒ W-ID + 症状 + 绕法。"""
    if not LEDGER_PATH.exists():
        return {}
    out = {}
    try:
        entries = parse_workarounds(LEDGER_PATH)
    except Exception:
        return {}
    for e in entries:
        eid = e.get("id") or ""
        if not eid:
            continue
        symptom = (e.get("symptom") or "").strip()
        workaround = (e.get("workaround") or "").strip()
        fix = (e.get("fix") or "").strip()
        if not (symptom or workaround or fix):
            continue
        out[eid] = {
            "w_ref": eid,
            "status": _parse_status(e.get("status", "")),
            "meaning": symptom.split("\n")[0][:160] if symptom else "",
            "fix": (fix or workaround).split("\n")[0][:160] if (fix or workaround) else "",
            # 匹配用的整段（症状 + 绕法 + 修法，可能含代码块）
            "blob": " ".join(x for x in (symptom, workaround, fix) if x)[:600],
        }
    return out


# ── 组索引 ──────────────────────────────────────────────────────

_index = None


def build_index():
    """建索引（模块级缓存）。"""
    global _index
    if _index is not None:
        return _index

    entries = {}

    def put(text, kind, **kw):
        key = normalize(text)
        if not key or len(key) < 4:
            return
        e = entries.setdefault(key, {"text": key, "kind": kind})
        for k, v in kw.items():
            if v and not e.get(k):
                e[k] = v

    # 编译器源码（诊断文本本体）
    for msg, origin in _scan_parser_messages().items():
        put(msg, "parse", origin=origin)
    for msg, origin in _scan_sema_messages().items():
        put(msg, "sema", origin=origin)

    # 规范 § 18（错误码 + 高频文本 + 含义）
    for key, info in _load_spec_errors().items():
        put(key, "spec", meaning=info.get("meaning"), spec_ref=info.get("spec_ref"))

    # 附录 B（现象说明 + 台账编号；现象里的报错原文也进来了）
    for item, info in _load_appendix_b().items():
        put(item, "spec", meaning=info.get("meaning"), spec_ref=info.get("spec_ref"),
            w_ref=info.get("w_ref"))

    # 语料实测（最可信）
    for sub, fname in _load_corpus_examples().items():
        put(sub, "corpus", example_file=fname)

    # 台账（按报错文本的子串关联 ⇒ 反向挂）
    # ⚠️ **两个方向都要试** —— 台账的症状是**整段**（可能含代码块），
    # 报错文本往往只是它的一个**片段** ⇒ 只查「症状的前 40 字在报错里」会漏掉一大半。
    ledger = _load_ledger()
    for key, e in entries.items():
        probe = key[:36]
        if len(probe) < 8:
            continue
        for eid, info in ledger.items():
            blob = info.get("blob") or ""
            if not blob:
                continue
            if probe not in blob and key not in blob:
                continue
            e.setdefault("w_ref", eid)
            e.setdefault("w_status", info.get("status"))
            if not e.get("meaning"):
                e["meaning"] = info.get("meaning")
            if not e.get("fix") and info.get("fix"):
                e["fix"] = info.get("fix")
            break

    for i, e in enumerate(sorted(entries.values(), key=lambda x: x["text"]), 1):
        e["id"] = "E-%03d" % i
    _index = entries
    return _index


def _lcs_words(a: list, b: list) -> int:
    """最长公共**连续**词串的词数。

    ⚠️ **为什么是「连续」而不是「集合」** —— 集合重合会让**完全无关**的查询
    蹭到 1 个常见词（"is"）⇒ 基础分 1，再加固定加权就被抬进结果里
    （实测："zzz-this-is-not-a-real-jhyy-error-9999" 拿到 28 分排在第一位）。
    ⇒ 连续词串 ⇒ 无关查询基本没有 ⇒ 直接不返回 ✓
    """
    if not a or not b:
        return 0
    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


# 低于这个分数 ⇒ **不返回**（宁可少给，别瞎猜）
MIN_SCORE = 18


def _score(query: str, entry: dict) -> int:
    """打分：完全相等 > 前缀 > 子串 > 最长公共连续词串。"""
    q = normalize(query).lower()
    t = entry["text"].lower()
    if not q:
        return 0
    if q == t:
        s = 100
    elif t.startswith(q) or q.startswith(t):
        s = 60
    elif q in t or t in q:
        s = 30
    else:
        # ⚠️ **剔掉停用词** —— 否则 "is not" 那种到处都有的词串会让
        #    **完全无关**的查询蹭到分（实测：无关查询拿 49 分排在第一位）。
        lcs = _lcs_words(_tokens(q, drop_stop=True), _tokens(t, drop_stop=True))
        if lcs < 2:
            return 0
        s = min(95, 12 * lcs)
    # 加权：来源越可信、加得越多（**只在基础分够高时才加**）
    if entry.get("kind") == "corpus":
        s += 12
    if entry.get("spec_ref"):
        s += 10
    if entry.get("w_ref"):
        s += 8
    if entry.get("meaning"):
        s += 5
    return s


def search(query: str, limit: int = 5) -> dict:
    """查一条编译器报错 ⇒ 它是什么意思、怎么改、该查哪一节。"""
    index = build_index()
    scored = []
    for e in index.values():
        sc = _score(query, e)
        if sc >= MIN_SCORE:
            scored.append((sc, e))
    scored.sort(key=lambda x: (-x[0], x[1]["text"]))
    matches = []
    for sc, e in scored[:limit]:
        m = {
            "id": e["id"],
            "text": e["text"],
            "kind": e.get("kind", ""),
            "score": sc,
        }
        for k in ("meaning", "fix", "spec_ref", "w_ref", "w_status", "example_file", "origin"):
            if e.get(k):
                m[k] = e[k]
        matches.append(m)
    return {
        "ok": True,
        "version": "4.0.0",
        "query": query,
        "indexed": len(index),
        "matches": matches,
    }


if __name__ == "__main__":
    import json

    q = sys.argv[1] if len(sys.argv) > 1 else "type mismatch in let"
    print(json.dumps(search(q, limit=8), ensure_ascii=False, indent=2))
