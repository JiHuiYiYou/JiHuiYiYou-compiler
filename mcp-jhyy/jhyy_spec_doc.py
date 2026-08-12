"""jhyy_spec_doc.py — 共享 markdown spec/ABI doc loader + token-AND search.

Sprint mcp-2 (2026-08-12): 给 jhyy_lang_ref / jhyy_abi_info 共用. 取代各自的
inline JSON 快照 (spec_data.json v0.5.0 / abi_data.json v1.0.0 40% 覆盖).
直接从 `docs/abis/jhyy-lang-spec-v*.md` / `jhyy-abi-v*.md` 读 markdown, 按 h2/h3
split sections, 用 token-AND search (split on whitespace, score = token hit count).

Public API:
    load_spec_doc(path) -> {"version": str, "sections": [{num, title, level, body}, ...]}
    search_spec_doc(doc, query, limit=20) -> {"version", "query", "matches": [...]}
"""
import re
from pathlib import Path
from typing import Optional, List, Dict, Any


# Match ANY markdown h2/h3/h4 heading. The leading "num" (if any) is extracted
# separately — JHYY spec uses:
#   `## 1.` / `### 1.2` / `#### 11.3` → numbered (num = "1.2.3")
#   `## 附录 A：` / `## 附录 B：`       → appendix (num = "A")
#   `### v0.4.0 新增`                  → changelog (num = "v0.4.0")
#   `### 状态变化` / `### 推荐的 v0.6` → unnumbered content headings
# Any h2/h3/h4 line flushes a section boundary so content doesn't bleed.
_HEADING_RE = re.compile(r"^(#{2,4})\s+(.+?)\s*$")
_NUM_PREFIX_RE = re.compile(
    r"^(?:(\d+(?:\.\d+)?)\.?|附录\s+([A-Z])[：:]|v(\d+\.\d+\.\d+))[\s:：]*(.+)$"
)
_VERSION_RE = re.compile(r"(?:spec|abi)[-_ ]v?(\d+\.\d+\.\d+)", re.IGNORECASE)

# Changelog sections: num is a bare version like "0.4.0" / "0.5.0" / "v0.4.0"
# (not a chapter.section like "10.4").
_CHANGELOG_NUM_RE = re.compile(r"^v?\d+\.\d+\.\d+$")


def load_spec_doc(path: str | Path) -> dict:
    """Load a markdown spec/ABI doc and split into sections.

    Returns:
        {
            "version": str,            # 提取自文件名/标题, e.g. "1.1.0"
            "path": str,               # 绝对路径
            "sections": [
                {"num": "10.4", "title": "struct 按值传递", "level": 3, "body": "..."},
                ...
            ],
            "section_count": int,
        }
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    sections: List[Dict[str, Any]] = []

    # Split by heading lines, preserving order
    lines = text.splitlines()
    current: Optional[Dict[str, Any]] = None
    body_lines: List[str] = []

    def flush():
        if current is not None:
            current["body"] = "\n".join(body_lines).strip()
            if current["body"]:  # skip empty sections
                sections.append(current)

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            # New heading → flush previous
            flush()
            level = len(m.group(1))
            raw_title = m.group(2).strip()
            # Try to extract a num prefix from the heading text
            num_m = _NUM_PREFIX_RE.match(raw_title)
            if num_m:
                num = num_m.group(1) or num_m.group(2) or ("v" + num_m.group(3)) or ""
                title = num_m.group(4).strip()
            else:
                num = ""
                title = raw_title
            current = {"num": num, "title": title, "level": level, "body": ""}
            body_lines = []
        else:
            if current is not None:
                body_lines.append(line)
            else:
                # content before first heading (frontmatter, top heading) — skip
                pass
    flush()

    # Extract version from filename or first h1
    version = ""
    m = _VERSION_RE.search(p.name)
    if m:
        version = m.group(1)
    else:
        m = _VERSION_RE.search(text[:2000])
        if m:
            version = m.group(1)

    return {
        "version": version,
        "path": str(p.resolve()),
        "sections": sections,
        "section_count": len(sections),
    }


# Common stop words (CN + EN) — filtered from query to avoid breaking token-AND
# on natural-language questions like "how do I declare a namespace".
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "doing",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "into", "during", "until", "against", "about",
    "如何", "怎么", "怎样", "什么", "哪些", "这个", "那个",
    "的", "是", "在", "了", "和", "与", "或", "但", "也", "都", "就",
})


# EN <-> CN term aliases for cross-language spec search.
# Token-AND alone misses cases like "pass-by-value" → § 10.4 "按值传递" because
# the spec body uses CN. Expand each query token to its known equivalents so
# both EN and CN forms contribute to the score.
_ALIASES: Dict[str, List[str]] = {
    # value-passing semantics
    "pass-by-value": ["按值传递", "值传"],
    "pass_by_value": ["按值传递", "值传"],
    "pass":          ["传递"],
    "by-value":      ["按值"],
    "value":         ["值"],
    "return":        ["返回"],
    "sret":          ["返回槽"],
    # module / namespace
    "namespace":     ["命名空间", "模块"],
    "module":        ["模块", "命名空间"],
    "import":        ["导入"],
    # type-system nouns
    "struct":        ["结构体"],
    "structure":     ["结构体"],
    "enum":          ["枚举"],
    "type":          ["类型"],
    "function":      ["函数"],
    "method":        ["方法"],
    "variable":      ["变量"],
    "constant":      ["常量", "顶层 const"],
    "const":         ["顶层 const", "常量"],
    # composite types
    "array":         ["数组"],
    "slice":         ["切片"],
    "pointer":       ["指针"],
    "string":        ["字符串"],
    # control flow
    "loop":          ["循环"],
    "for":           ["循环"],
    "while":         ["循环"],
    "match":         ["匹配"],
    "if":            ["如果"],
    "else":          ["否则"],
    "break":         ["跳出", "中断"],
    "continue":      ["继续"],
    # mutation
    "let":           ["变量"],
    "mut":           ["可变", "mut"],
    "assign":        ["赋值"],
    "declaration":   ["声明"],
    "declare":       ["声明"],
    "definition":    ["定义"],
    "implement":     ["实现"],
    # misc
    "pattern":       ["模式"],
    "scope":         ["作用域"],
    "lifetime":      ["生命周期"],
    "generic":       ["泛型"],
    "trait":         ["trait", "特征"],
    "error":         ["错误"],
}


def _tokenize(text: str, drop_stops: bool = False) -> List[str]:
    """Split text into lowercase tokens (whitespace + common punctuation).

    If drop_stops=True, filter out common stop words (for token-AND queries).
    """
    tokens = [t for t in re.split(r"[\s,;.()\[\]{}<>:/\\'\"]+", text.lower()) if t]
    if drop_stops:
        tokens = [t for t in tokens if t not in _STOP_WORDS]
    return tokens


def search_spec_doc(doc: dict, query: str, limit: int = 20) -> dict:
    """Token-AND search over doc sections with phrase bonus. Returns ranked matches.

    Algorithm:
        1. Tokenize query on whitespace/punctuation. Stop words filtered for token-AND.
        2. **Phrase bonus**: if the full query string (lowercase, trimmed) appears
           in title or body → +8 / +5 score. Handles CN/EN cross-mapping like
           "struct pass-by-value" → § 10.4 "按值传递" (token-AND alone misses it
           because "pass-by-value" splits to ["pass","by","value"] which never
           co-occur in that CN section).
        3. **Token score**: count distinct non-stop query tokens in (title + body).
           Title hits weighted 2x.
        4. Sort by score desc; tie-break on section num (earlier first).
        5. Return up to `limit` matches with excerpt (±200 chars around first hit).

    Returns:
        {
            "ok": True,
            "version": doc["version"],
            "query": query,
            "matches": [
                {"section": "10.4", "title": "...", "level": 3,
                 "score": 5, "excerpt": "..."},
                ...
            ],
        }
    """
    q_lower = query.lower().strip()
    q_tokens = _tokenize(query, drop_stops=True)
    if not q_lower:
        return {"ok": True, "version": doc.get("version", ""), "query": query, "matches": []}

    # Build phrase variants: original + each combo where one query token is
    # replaced by a CN/EN alias. "struct pass-by-value" → also try
    # "struct 按值传递", "结构体 pass-by-value", "struct pass-by 值", etc.
    # This handles cross-language phrase matching for spec sections titled in CN.
    phrase_variants: List[str] = [q_lower]
    for i, t in enumerate(q_tokens):
        aliases = _ALIASES.get(t, [])
        for a in aliases:
            phrase_variants.append(q_lower.replace(t, a))

    matches: List[Dict[str, Any]] = []
    for sec in doc.get("sections", []):
        title_lower = sec["title"].lower()
        body_lower = sec["body"].lower()

        # Phrase bonus — handles cross-language queries like "pass-by-value" → "按值传递"
        phrase_score = 0
        best_body_hit = -1
        for variant in phrase_variants:
            if variant in title_lower:
                phrase_score += 8
            if variant in body_lower:
                phrase_score += 5
                idx = body_lower.find(variant)
                if idx >= 0 and (best_body_hit < 0 or idx < best_body_hit):
                    best_body_hit = idx

        # Token score (stop words dropped) + alias expansion
        expanded_tokens: List[str] = []
        for t in q_tokens:
            expanded_tokens.append(t)
            expanded_tokens.extend(_ALIASES.get(t, []))

        title_hits = sum(1 for t in expanded_tokens if t in title_lower)
        body_hits = sum(1 for t in expanded_tokens if t in body_lower)
        token_score = title_hits * 2 + body_hits

        score = phrase_score + token_score

        # Penalty: changelog sections (`### v0.4.0 新增`) often literally mention
        # spec terms ("struct 按值传递") without being the semantic spec.
        # Users searching for spec semantics want § N.M sections, not changelog.
        # num looks like "v0.4.0" / "0.5.0" — these are changelog versions.
        if sec["num"].startswith("v") or _CHANGELOG_NUM_RE.match(sec["num"]):
            score -= 5
        # Unnumbered content headings ("### 状态变化") and appendix entries often
        # mention spec terms inline without being the spec section itself.
        if not sec["num"]:
            score -= 4
        # Appendix sections ("§ A" / "§ B" / "§ C") often summarize known
        # limitations or version diffs — secondary to the spec itself.
        if sec["num"] in ("A", "B", "C") or re.match(r"^[A-Z]$", sec["num"]):
            score -= 3
        # Penalty: chapter 16 is "完整示例" (complete examples). They're concrete
        # code examples, useful but secondary to the semantic spec section.
        if sec["num"].startswith("16.") and sec["level"] >= 3:
            score -= 2

        if score > 0:
            # Excerpt: prefer best phrase-variant hit location, fall back to first token
            first_hit = best_body_hit
            if first_hit < 0:
                first_hit = body_lower.find(q_lower)
            if first_hit < 0:
                for t in q_tokens:
                    idx = body_lower.find(t)
                    if idx >= 0 and (first_hit < 0 or idx < first_hit):
                        first_hit = idx
            if first_hit < 0:
                first_hit = 0
            start = max(0, first_hit - 100)
            end = min(len(sec["body"]), first_hit + 200)
            excerpt = sec["body"][start:end]
            if start > 0:
                excerpt = "..." + excerpt
            if end < len(sec["body"]):
                excerpt = excerpt + "..."

            matches.append({
                "section": sec["num"],
                "title": sec["title"],
                "level": sec["level"],
                "score": score,
                "excerpt": excerpt,
            })

    # Sort by score desc, then section num
    def sort_key(m):
        try:
            num_tuple = tuple(int(x) for x in m["section"].split("."))
        except ValueError:
            num_tuple = (999,)
        return (-m["score"], num_tuple)

    matches.sort(key=sort_key)
    return {
        "ok": True,
        "version": doc.get("version", ""),
        "query": query,
        "matches": matches[:limit],
    }