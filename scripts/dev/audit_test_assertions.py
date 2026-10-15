#!/usr/bin/env python3
"""测试断言强度审计 — 找出「跑了但不验任何东西」的用例。

## 为什么需要这个

`mcp-jhyy/jhyy_regress.py` 的判据只认退出码（stdout 被捕获后仅用于显示）。
于是有两类测试看起来有覆盖、实际零信号:

1. **crash-only**:源文件里没写任何指令 → `expected is None` 分支只查
   NTSTATUS,进程没崩就算 PASS。
2. **literal-return**:写了 `// EXPECT: 42`,但 `main_jhyy` 的所有 `return`
   都是同一个字面量 42 → EXPECT 只是把字面量抄了一遍,不可能失败。
   `generics_enum.jhyy` 就是这一类:它比 crash-only 更具欺骗性,因为它
   连「看起来有 EXPECT」这个信号都给了,任何按「有没有 directive」统计的
   工具(以及人)都会被它骗过。

浮点比较 bug(W-109)能活到现在,靠的就是 `float_cmp.jhyy` 同时具备上述两点。

## 用法

    python scripts/dev/audit_test_assertions.py             # 报告
    python scripts/dev/audit_test_assertions.py --strict     # 有违规就 exit 1
    python scripts/dev/audit_test_assertions.py --baseline docs/internal/tests.md
    python scripts/dev/audit_test_assertions.py --json

`--strict` 适合挂 CI / pre-commit:新增一个 crash-only 或 literal-return
测试就会让它翻红。

退出码:0 = 无违规;1 = 有违规(--strict 下)。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "compiler" / "tests" / "examples"

# 与 jhyy_regress.py 的解析保持一致:jhyy 注释行可写成 `//EXPECT:42`,
# 也可写成 `// EXPECT: 42`。
RE_EXPECT = re.compile(r"//\s*EXPECT(?:ECT)?\s*[:=]\s*(\d+)")
RE_EXPECT_ERR = re.compile(r'//\s*EXPECT-ERROR\s*[:=]\s*"([^"]+)"')
RE_EXPECT_OUT = re.compile(r'//\s*EXPECT-OUT\s*[:=]\s*"([^"]+)"')
RE_SKIP = re.compile(r"//\s*SKIP\s*:")
RE_MAIN = re.compile(r"\bfn\s+main_jhyy\b")
RE_RETURN = re.compile(r"^\s*return\s+(-?\d+)\s*;?\s*$")

# 判为「被测对象就是退出码本身」的例外 —— 这类测试 return 字面量是正确的,
# 因为退出码正是它要验的东西。key 是文件名。
EXIT_CODE_IS_SUBJECT = {
    "exit_zero_extend_0.jhyy",
    "exit_zero_extend_1.jhyy",
    "exit_zero_extend_127.jhyy",
    "exit_zero_extend_128.jhyy",
    "exit_zero_extend_255.jhyy",
    "exit_zero_extend_256.jhyy",
}


def classify(path: Path) -> dict:
    """给单个测试文件分类。"""
    src = path.read_text(encoding="utf-8", errors="replace")
    has_main = bool(RE_MAIN.search(src))
    expect = RE_EXPECT.search(src)
    has_out = RE_EXPECT_OUT.search(src) is not None
    has_err = RE_EXPECT_ERR.search(src) is not None
    is_skip = RE_SKIP.search(src) is not None

    info = {
        "file": str(path.relative_to(EXAMPLES)),
        "has_main": has_main,
        "expect": int(expect.group(1)) if expect else None,
        "has_out": has_out,
        "has_expect_error": has_err,
        "is_skip": is_skip,
    }

    if not has_main:
        info["class"] = "library"
        return info

    body = _main_body(src)
    # 只看真正的 return 语句 —— 不能把空行/注释算进分母,否则
    # `len(literal_codes) != len(returns)` 恒成立,all_literal 恒假,
    # 整个 literal-return 分类会静默失效(第一版就踩了这个坑)。
    ret_stmts = [l for l in body.splitlines() if re.match(r"^\s*return\b", l)]
    literals = [RE_RETURN.match(l) for l in ret_stmts]
    codes = {m.group(1) for m in literals if m}
    implicit = ""
    if not ret_stmts:
        # jhyy 允许隐式返回:`fn main_jhyy() -> i32 { 42 }`(hello.jhyy)或
        # `{ err }`(int_width_arith.jhyy)。没有 return 语句时,函数体最后一个
        # 非注释非空行就是返回值 —— 它是字面量的话同样零信号。
        tail = [l.strip() for l in body.splitlines()
                if l.strip() and not l.strip().startswith(("//", "}", "{", "#"))]
        if tail and re.fullmatch(r"-?\d+", tail[-1]):
            implicit = tail[-1]
            codes = {implicit}
            ret_stmts = [tail[-1]]
    all_literal = bool(ret_stmts) and all(m is not None for m in literals)
    info["return_codes"] = sorted(codes)
    info["implicit_return"] = implicit
    info["n_returns"] = len(ret_stmts)
    # 「所有 return 都是字面量」本身不等于零信号:不同失败分支返回不同常量
    # (如 std_os_basic 的 return 1..9)是真断言。判据要看 if 的条件是否
    # 拿**计算值**做比较。第一版漏了这一层,把 30 个有真断言的测试误判成
    # 违规 —— 分类器自己有假阳性比没有分类器更糟。
    guarded = bool(re.search(r"\bif\b[^\n]*[!=<>]=?", body)) and bool(
        re.search(r"\bif\b[^\n]*[A-Za-z_]\w*[^\n]*[!=<>]=?", body))
    info["guarded_returns"] = guarded
    if guarded:
        all_literal = False

    if is_skip:
        info["class"] = "skipped"
    elif has_out:
        info["class"] = "out-asserted"
    elif expect and not all_literal:
        info["class"] = "real"
    elif expect and all_literal:
        # EXPECT 存在,但 main 的返回是字面量。若 EXPECT 值恰好等于那个字面量,
        # 这条断言在数学上不可能失败 —— 零信息量。
        if expect.group(1) in set(info["return_codes"]) and path.name not in EXIT_CODE_IS_SUBJECT:
            info["class"] = "literal-return"
        else:
            info["class"] = "literal-return-ok"
    elif has_err:
        info["class"] = "expect-error"
    else:
        info["class"] = "crash-only"
    return info


def _main_body(src: str) -> str:
    m = re.search(r"\bfn\s+main_jhyy\b[^\n{]*\{(.*?)\n\}", src, re.S)
    return m.group(1) if m else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true",
                    help="有违规就 exit 1(挂 CI 用)")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--baseline", metavar="FILE",
                    help="与该文件里写的基线数字对照,超了算违规")
    args = ap.parse_args()

    if not EXAMPLES.is_dir():
        print(f"ERR: {EXAMPLES} not found", file=sys.stderr)
        return 2

    files = sorted(p for p in EXAMPLES.rglob("*.jhyy") if not p.name.startswith("_"))
    results = [classify(p) for p in files]

    buckets: dict[str, list[dict]] = {}
    for r in results:
        buckets.setdefault(r["class"], []).append(r)

    real = len(buckets.get("real", [])) + len(buckets.get("out-asserted", []))
    violations = buckets.get("crash-only", []) + buckets.get("literal-return", [])
    runnable = len([r for r in results if r["has_main"] and r["class"] != "skipped"])

    if args.json:
        print(json.dumps({
            "total": len(results),
            "runnable": runnable,
            "real_assertions": real,
            "violations": len(violations),
            "buckets": {k: [r["file"] for r in v] for k, v in sorted(buckets.items())},
        }, ensure_ascii=False, indent=2))
    else:
        print(f"扫描 {len(results)} 个 .jhyy, 可跑 {runnable} 个")
        print(f"  真断言(real + out-asserted): {real}")
        for k in ("literal-return", "crash-only", "literal-return-ok",
                  "expect-error", "skipped", "library"):
            if k in buckets:
                print(f"  {k:24s} {len(buckets[k]):3d}")
        print(f"\n零信号违规合计: {len(violations)}")
        if violations:
            print("\n--- crash-only(只验「进程没崩」)---")
            for r in buckets.get("crash-only", []):
                print(f"    {r['file']}")
            print("\n--- literal-return(有 EXPECT 但不可能失败)---")
            for r in buckets.get("literal-return", []):
                print(f"    {r['file']}  (return {'/'.join(r['return_codes'])}, "
                      f"EXPECT={r['expect']})")

    if args.baseline:
        bp = Path(args.baseline)
        if not bp.is_file():
            print(f"ERR: baseline {bp} not found", file=sys.stderr)
            return 2
        m = re.search(r"有 `main_jhyy` 但无任何指令\*\*?[^0-9]*\*\*(\d+)\*\*", bp.read_text(encoding="utf-8"))
        if not m:
            m = re.search(r"\| \*\*有 `main_jhyy` 但无任何指令\*\*\s*\|\s*\*\*(\d+)\*\*", bp.read_text(encoding="utf-8"))
        if not m:
            print(f"WARN: baseline {bp} 里找不到 crash-only 计数,跳过基线比对", file=sys.stderr)
        else:
            allowed = int(m.group(1))
            got = len(buckets.get("crash-only", []))
            if got > allowed:
                print(f"FAIL: crash-only {got} > baseline {allowed} —— 有测试退化成不验证结果",
                      file=sys.stderr)
                return 1
            print(f"baseline OK: crash-only {got} <= {allowed}")

    if args.strict and violations:
        print(f"FAIL: {len(violations)} 个测试零信号", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
