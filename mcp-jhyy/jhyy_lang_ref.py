"""jhyy_lang_ref.py — JHYY 语言规范查询 (Sprint mcp-2, 取代 inline JSON 快照)

之前 jhyy_lang_ref 用 mcp-jhyy/spec_data.json (v0.5.0, 157 行手写快照, 永远没更新).
现在直接从 `docs/abis/jhyy-lang-spec-v1.3.0.md` 加载 + token-AND search.

Public API:
    search(query, limit=20) -> {"ok", "version", "query", "matches"}
    LANG_SPEC_PATH: Path to locked spec doc
"""
import sys
from pathlib import Path
from typing import Optional

# Allow standalone test (`python mcp-jhyy/jhyy_lang_ref.py "struct pass-by-value"`)
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jhyy_spec_doc import load_spec_doc, search_spec_doc  # noqa: E402


# Locked spec path — per CLAUDE.md authoritative docs.
# JHYY_ROOT derived from script location (works on any machine, no hardcoded
# user path; per v1.5.5 release.yml CI fix). mcp-jhyy/ → parents[1] = root.
JHYY_ROOT = Path(__file__).resolve().parents[1]
LANG_SPEC_PATH = JHYY_ROOT / "docs/abis/jhyy-lang-spec-v1.3.0.md"


# Module-level cache: load once, reuse across MCP calls
_doc_cache: Optional[dict] = None


def _get_doc() -> dict:
    global _doc_cache
    if _doc_cache is None:
        _doc_cache = load_spec_doc(LANG_SPEC_PATH)
    return _doc_cache


def search(query: str, limit: int = 20) -> dict:
    """Search the locked JHYY language spec (v1.3.0).

    Returns:
        {
            "ok": True,
            "version": "1.3.0",
            "query": query,
            "matches": [
                {"section": "10.4", "title": "...", "level": 3, "score": N, "excerpt": "..."},
                ...
            ],
        }
    """
    doc = _get_doc()
    return search_spec_doc(doc, query, limit=limit)


if __name__ == "__main__":
    # CLI for smoke-testing
    import json
    q = sys.argv[1] if len(sys.argv) > 1 else "struct pass-by-value"
    print(json.dumps(search(q), indent=2, ensure_ascii=False))