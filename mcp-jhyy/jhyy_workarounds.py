#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""jhyy_workarounds.py — 解析 + 搜索 docs/internal/workarounds.md

Sprint mcp-1 (2026-08-11). 处理中英字段混用 (workarounds.md 实际有 ID/状态/日期/触发面/...).

Public API:
    parse_workarounds(path=None) -> list[dict]
    search(query, status=None, path=None) -> dict
"""
import os
import re
from pathlib import Path
from typing import Optional

# JHYY_ROOT derived from script location (works on any machine; per
# v1.5.5 release.yml CI fix). mcp-jhyy/ → parents[1] = project root.
JHYY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = JHYY_ROOT / "docs/internal/workarounds.md"

# 字段 alias 表: canonical_field → [alias1, alias2, ...]
# workarounds.md 实际混用中英, 解析时按列表顺序匹配
# 字段格式: **alias:** value  (markdown bold 包裹 "alias:")
FIELD_ALIASES = {
    "id": ["ID"],
    "status": ["状态"],
    "date": ["日期"],
    "trigger": ["触发面"],
    "symptom": ["症状"],
    "root_cause": ["根因嫌疑"],
    "workaround": ["workaround", "Workaround"],
    "scope": ["影响范围"],
    "failure_condition": ["失效条件"],
    "superseder": ["superseder"],
    "fix": ["修复"],
    "verify": ["验证"],
    "reference": ["引用"],
}


def _build_alias_regex() -> re.Pattern:
    """编译一个能匹配任何 alias 字段标记的正则. 格式: **alias:** 或 **alias：**"""
    all_aliases = []
    for aliases in FIELD_ALIASES.values():
        all_aliases.extend(aliases)
    # Sort longest first to avoid prefix conflicts (e.g., "ID" vs "ID:")
    all_aliases.sort(key=len, reverse=True)
    # Pattern: **<alias>:**  (followed by space or value)
    pattern = r"^\*\*(" + "|".join(re.escape(a) for a in all_aliases) + r"):\*\*\s*"
    return re.compile(pattern)


_ALIAS_RE = _build_alias_regex()


def _split_entries(text: str) -> list[tuple[str, str]]:
    """切分 workarounds.md 为 [(heading, body), ...]."""
    lines = text.splitlines(keepends=True)
    entries = []
    current_heading = None
    current_body_lines = []
    for line in lines:
        # W-XXX entry 标题: "## W-XXX: ..." or "## W-XXX RESOLVED — ..." or "## W-XXX anything"
        m = re.match(r"^##\s+(W-\d+)(?:[:\s—\-].*)?$", line)
        if m:
            # Push previous
            if current_heading is not None:
                entries.append((current_heading, "".join(current_body_lines)))
            current_heading = m.group(1)
            current_body_lines = []
        else:
            if current_heading is not None:
                current_body_lines.append(line)
    # Push last
    if current_heading is not None:
        entries.append((current_heading, "".join(current_body_lines)))
    return entries


def _parse_entry_body(body: str) -> dict:
    """从 entry body 提取 alias 字段. 格式: '**alias:** value' 多行连续算一个字段."""
    fields = {}
    current_field = None
    current_value_lines = []
    for line in body.splitlines():
        # Try to match any **<alias>:** field marker
        matched_field = None
        m = _ALIAS_RE.match(line)
        if m:
            matched_alias = m.group(1)
            # Map alias back to canonical field
            for canonical, aliases in FIELD_ALIASES.items():
                if matched_alias in aliases:
                    matched_field = canonical
                    break
        if matched_field:
            # Push previous
            if current_field is not None:
                fields[current_field] = "\n".join(current_value_lines).strip()
            current_field = matched_field
            # Strip the field marker from the line
            stripped = _ALIAS_RE.sub("", line, count=1)
            current_value_lines = [stripped] if stripped else []
        else:
            if current_field is not None:
                # Continuation of current field
                current_value_lines.append(line)
    # Push last
    if current_field is not None:
        fields[current_field] = "\n".join(current_value_lines).strip()
    return fields


def parse_workarounds(path: Optional[Path] = None) -> list[dict]:
    """解析整个 workarounds.md, 返回 [{id, status, date, trigger, symptom, ...}, ...]."""
    p = Path(path) if path else DEFAULT_PATH
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8", errors="replace")
    entries = []
    for heading, body in _split_entries(text):
        fields = _parse_entry_body(body)
        fields["id"] = heading  # override with actual heading
        # Default empty fields
        for canonical in FIELD_ALIASES:
            fields.setdefault(canonical, "")
        entries.append(fields)
    return entries


def search(query: str, status: Optional[str] = None, path: Optional[Path] = None) -> dict:
    """搜索 workarounds.md.

    Args:
        query: 搜索词 (substring, 大小写不敏感). 可为 W-XXX ID 或 触发模式 (let mut / sentinel / ...)
        status: 可选过滤 "ACTIVE" / "RESOLVED" / "SUPERSEDED"
        path: 可选 workarounds.md 路径

    Returns:
        {
            "ok": bool,
            "query": str,
            "status_filter": str | None,
            "matches": [
                {"id": "W-005", "status": "RESOLVED", "date": "...",
                 "trigger": "...", "symptom": "...", "root_cause": "...",
                 "workaround": "...", "scope": "...", "superseder": "..."},
                ...
            ],
            "active_count": int,
            "resolved_count": int,
            "superseded_count": int,
            "total": int,
        }
    """
    p = Path(path) if path else DEFAULT_PATH
    if not p.exists():
        return {"ok": False, "error": f"workarounds.md not found: {p}"}

    all_entries = parse_workarounds(p)
    q_lower = query.lower()
    matches = []
    for entry in all_entries:
        # status filter (substring match — entries often have "ACTIVE (dormant)" etc)
        if status and status.upper() not in entry.get("status", "").upper():
            continue
        # query match: check ID + trigger + symptom + workaround + root_cause
        haystacks = [
            entry.get("id", ""),
            entry.get("trigger", ""),
            entry.get("symptom", ""),
            entry.get("workaround", ""),
            entry.get("root_cause", ""),
            entry.get("scope", ""),
        ]
        haystack = "\n".join(haystacks).lower()
        if q_lower in haystack:
            matches.append({
                "id": entry.get("id", ""),
                "status": entry.get("status", ""),
                "date": entry.get("date", ""),
                "trigger": entry.get("trigger", "")[:300],
                "symptom": entry.get("symptom", "")[:300],
                "root_cause": entry.get("root_cause", "")[:300],
                "workaround": entry.get("workaround", "")[:300],
                "scope": entry.get("scope", "")[:200],
                "superseder": entry.get("superseder", "")[:200],
            })

    active_count = sum(1 for e in all_entries if "ACTIVE" in e.get("status", "").upper())
    resolved_count = sum(1 for e in all_entries if "RESOLVED" in e.get("status", "").upper())
    superseded_count = sum(1 for e in all_entries if "SUPERSEDED" in e.get("status", "").upper())

    return {
        "ok": True,
        "query": query,
        "status_filter": status,
        "matches": matches,
        "active_count": active_count,
        "resolved_count": resolved_count,
        "superseded_count": superseded_count,
        "total": len(all_entries),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python jhyy_workarounds.py <query> [status]")
        sys.exit(1)
    q = sys.argv[1]
    s = sys.argv[2] if len(sys.argv) > 2 else None
    result = search(q, s)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))