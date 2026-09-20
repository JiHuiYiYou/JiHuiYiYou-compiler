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
import subprocess
from pathlib import Path
from typing import Optional

# v2.13.6 mini: 5-state enum + 严格 token match (fix v2.13.5 refactor 的
# 旧 3 态 substring match + W-051 误分类问题). 详见 v2.13.6-plan.md.
_STATUS_WORDS = ("ACTIVE", "RESOLVED", "SUPERSEDED", "DEFERRED", "INVALID")
_STATUS_RE = re.compile(
    r"[^\w]*?(?P<status>ACTIVE|RESOLVED|SUPERSEDED|DEFERRED|INVALID)\b",
    re.IGNORECASE,
)


def _msys_to_windows(msys_path: str) -> Path:
    """Convert MSYS2-style path (/c/Users/...) to Windows Path (C:\\Users\\...).

    `git worktree list --porcelain` 在 MSYS2 bash 输出 /c/... 格式;
    Python `Path('/c/...').resolve()` 把它当 relative path 处理 →
    prepended current drive → `C:\\c\\Users\\...` (BAD, 文件不存在).

    转换规则 (per MSYS2 path translation):
    - `/x/...` (x = drive letter) → `X:/...` → resolve → `X:\\...`
    - 其他 (UNC, /tmp, relative) → 原样
    """
    p = msys_path.strip()
    if len(p) >= 3 and p[0] == "/" and p[2] == "/":
        drive = p[1]
        if drive.isalpha():
            p = f"{drive.upper()}:{p[2:]}"
    return Path(p)


def _git_path() -> Optional[str]:
    """Resolve `git` to absolute Windows path.

    v2.13.6.2 mini: MCP subprocess inherits MSYS2 PATH from Claude Code (e.g.
    `/c/Users/.../bin`), Windows CreateProcess + shutil.which 都无法解析 MSYS2
    PATH → 返 None / `FileNotFoundError [WinError 2]`.

    解法: scan known Windows git install locations, return first hit. 比 PATH
    转换简单可靠 (PATH 转 win 后还要处理 MSYS2 root mapping for /mingw64/bin,
    /usr/bin 等非 /x/ 前缀路径, 复杂度高).
    """
    candidates = [
        r"C:\msys64\usr\bin\git.exe",
        r"C:\msys64\mingw64\bin\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def _detect_root() -> Path:
    """Detect JHYY root, prefer active worktree over script location.

    v2.13.6 mini: 解决 axis-vN worktree isolation (per
    feedback_axis_vn_worktree_isolation). .claude.json 硬编码 main worktree
    path 启动 MCP server, 但用户 active dev 在 axis-v2 时要读 axis-v2 的
    workarounds.md.

    3-tier heuristic:
    1. env override `JHYY_MCP_WORKTREE` 显式指定 (escape hatch, 永远走 — 不 cache)
    2. cwd 的 git toplevel (ONLY if cwd branch != main; default Claude Code
       session cwd=main ⇒ 跳过 Tier 2, 让 Tier 3 选 most-recent non-main)
    3. scan git worktree list, pick non-main branch with most-recent commit
       (handles "user session cwd=main 但 active dev 在 axis-v2" case)
    4. fallback = script parents[1] (旧行为)

    60s cache (v2.13.6.2): 防 MCP subprocess 重复调 search() 时 2nd git
    subprocess 偶尔 hang >15s (Windows Defender / console overhead). User
    session 内 worktree 切换频率 (< 1/min) 不受 cache 影响.

    Returns:
        JHYY_ROOT (env override / cwd worktree / most-recent non-main / script-derives fallback)
    """
    # Tier 1 (env override) 永远走 — user 显式指定每次立即生效.
    env_override = os.environ.get("JHYY_MCP_WORKTREE", "").strip()
    if env_override:
        override_path = _msys_to_windows(env_override).resolve()
        if (override_path / "docs/internal/workarounds.md").exists():
            return override_path

    # Cache for Tier 2/3/4 results.
    import time as _time
    now = _time.time()
    if _detect_root_cache["value"] is not None and (now - _detect_root_cache["time"]) < _DETECT_CACHE_TTL:
        return _detect_root_cache["value"]

    result = _detect_root_impl()
    _detect_root_cache["value"] = result
    _detect_root_cache["time"] = now
    return result


def _detect_root_impl() -> Path:
    """Internal: 实际 _detect_root 逻辑 (Tier 2/3/4)."""
    script_root = Path(__file__).resolve().parents[1]
    git_abs = _git_path()
    # subprocess timeout (sec) — 防 git 在某个 worktree 里 hang (e.g. lock, GC)
    _timeout = 15

    # Tier 2: cwd's git toplevel, ONLY if cwd branch is non-main (default Claude
    # Code session cwd=main ⇒ 跳过 Tier 2, 让 Tier 3 选 most-recent non-main
    # worktree). v2.13.6.2 修复: 旧版 cwd=main 时 Tier 2 抢先返回 main,
    # 跳过 Tier 3 选 axis-vN, 导致 MCP 永远显示 stale main workarounds.
    try:
        cwd = Path(os.getcwd())
        toplevel_str = subprocess.check_output(
            [git_abs, "rev-parse", "--show-toplevel"] if git_abs else ["git", "rev-parse", "--show-toplevel"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=_timeout,
        ).strip()
        # v2.13.6.2: defensive MSYS2 → Windows conversion (normal case already
        # Windows-style, but `MSYS_NO_PATHCONV=1` + git.exe may 输出 /c/...).
        cwd_toplevel = _msys_to_windows(toplevel_str).resolve()
        cwd_branch = ""
        try:
            cwd_branch = subprocess.check_output(
                [git_abs, "rev-parse", "--abbrev-ref", "HEAD"] if git_abs else ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(cwd_toplevel),
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=_timeout,
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            cwd_branch = ""
        if cwd_branch != "main" and cwd_toplevel != script_root and (cwd_toplevel / "docs/internal/workarounds.md").exists():
            return cwd_toplevel
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        cwd_toplevel = None

    # Tier 3: scan worktrees, prefer non-main branch with most-recent commit
    # (handles "user cwd=main but active dev in axis-v2")
    try:
        cwd = cwd_toplevel or Path(os.getcwd())
        wt_list = subprocess.check_output(
            [git_abs, "worktree", "list", "--porcelain"] if git_abs else ["git", "worktree", "list", "--porcelain"],
            cwd=str(cwd),
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=_timeout,
        )
        worktrees = []
        cur_path = None
        cur_branch = None
        for line in wt_list.splitlines():
            if line.startswith("worktree "):
                if cur_path:
                    worktrees.append((cur_path, cur_branch))
                cur_path = line[9:].strip()
                cur_branch = None
            elif line.startswith("branch "):
                # "branch refs/heads/axis-v2" or "branch refs/heads/main"
                cur_branch = line[7:].strip().removeprefix("refs/heads/")
        if cur_path:
            worktrees.append((cur_path, cur_branch))

        candidates = []
        for wt_path_str, branch in worktrees:
            # v2.13.6.2 mini: `git worktree list --porcelain` 在 MSYS2 bash 输出
            # /c/... 格式; `Path('/c/...').resolve()` 当 relative 处理 →
            # CWD prepended → C:\c\... (BAD, 文件不存在). 用 _msys_to_windows 转
            # `/c/...` → `C:/...` 再 resolve → C:\Works (CORRECT).
            wt_path = _msys_to_windows(wt_path_str).resolve()
            wd = wt_path / "docs/internal/workarounds.md"
            if not wd.exists():
                continue
            try:
                commit_time_str = subprocess.check_output(
                    [git_abs, "log", "-1", "--format=%ct"] if git_abs else ["git", "log", "-1", "--format=%ct"],
                    cwd=str(wt_path),
                    stderr=subprocess.DEVNULL,
                    text=True,
                    timeout=_timeout,
                ).strip()
                commit_time = int(commit_time_str)
            except (subprocess.CalledProcessError, FileNotFoundError, OSError, ValueError, subprocess.TimeoutExpired):
                continue
            # Sort key: (not_main=0/main=1, -commit_time)
            # Prefer non-main branch, then most recent commit
            is_main = 1 if branch == "main" else 0
            candidates.append((is_main, -commit_time, wt_path))

        if candidates:
            candidates.sort()
            return candidates[0][2]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        pass

    # Tier 4: fallback
    return script_root


# Called every search() (NOT module-level cache) — 让用户在 session 内
# cd 到其他 worktree 后 MCP 立即跟随, 不需 restart.
def _default_path() -> Path:
    """返回当前 cwd git worktree 的 workarounds.md (fallback to script-derived)."""
    return _detect_root() / "docs/internal/workarounds.md"


# Backward-compat: 外部代码可能 import JHYY_ROOT / DEFAULT_PATH
# v2.13.6.2 mini: cache 60s 防 MCP subprocess 重复调 workarounds 时 git
# subprocess hang on 2nd call (Windows Defender / console overhead 偶尔
# 让 2nd `git worktree list` 超时). cache 60s 足够 — user session 内 worktree
# 切换频率低.
_detect_root_cache: dict = {"value": None, "time": 0.0}
_DETECT_CACHE_TTL = 60.0

JHYY_ROOT = _detect_root()
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


def _parse_status(status_str: str) -> str:
    """从 status 字段提取 canonical 5-state enum.

    Handles:
    - Post-v2.13.5 format: 'ACTIVE since 2026-08-15 (v1.5.6) — caption...'
    - Pre-v2.13.5 emoji-prefix: '✅ RESOLVED 2026-08-28 ...' / '🟡 DEFERRED v2.x'
    - Inline state: 'ACTIVE (dormant)' / 'RESOLVED' / 'SUPERSEDED by W-029'

    Returns:
        "ACTIVE" / "RESOLVED" / "SUPERSEDED" / "DEFERRED" / "INVALID" / "UNKNOWN"
    """
    if not status_str:
        return "UNKNOWN"
    first_line = status_str.splitlines()[0].strip()
    m = _STATUS_RE.search(first_line)
    return m.group("status").upper() if m else "UNKNOWN"


def search(query: str, status: Optional[str] = None, path: Optional[Path] = None) -> dict:
    """搜索 workarounds.md.

    Args:
        query: 搜索词 (substring, 大小写不敏感). 可为 W-XXX ID 或 触发模式 (let mut / sentinel / ...)
        status: 可选过滤 5-state enum: "ACTIVE" / "RESOLVED" / "SUPERSEDED" / "DEFERRED" / "INVALID"
                v2.13.6 mini 起严格 token match (不再是 substring), 避免 W-051 RESOLVED
                但 body 写 "强标 ACTIVE 不解决任何 active 问题" 的误分类.
        path: 可选 workarounds.md 路径 (默认 = cwd git worktree 的 docs/internal/workarounds.md,
              v2.13.6 mini worktree 探测; fallback to script parents[1])

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
            "deferred_count": int,
            "invalid_count": int,
            "unknown_count": int,
            "total": int,
        }
    """
    p = Path(path) if path else _default_path()
    if not p.exists():
        return {"ok": False, "error": f"workarounds.md not found: {p}"}

    all_entries = parse_workarounds(p)
    q_lower = query.lower()
    matches = []
    for entry in all_entries:
        entry_status = _parse_status(entry.get("status", ""))
        # status filter — strict 5-state token match (v2.13.6 mini; 旧 substring 误分类)
        if status and entry_status != status.upper():
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

    # 5-state counts
    counts = {s: 0 for s in _STATUS_WORDS}
    counts["UNKNOWN"] = 0
    for e in all_entries:
        s = _parse_status(e.get("status", ""))
        counts[s if s in counts else "UNKNOWN"] += 1

    return {
        "ok": True,
        "query": query,
        "status_filter": status,
        "matches": matches,
        "active_count": counts["ACTIVE"],
        "resolved_count": counts["RESOLVED"],
        "superseded_count": counts["SUPERSEDED"],
        "deferred_count": counts["DEFERRED"],
        "invalid_count": counts["INVALID"],
        "unknown_count": counts["UNKNOWN"],
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