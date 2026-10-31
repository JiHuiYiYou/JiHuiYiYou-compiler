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
    python scripts/dev/audit_test_assertions.py --baseline docs/internal/FACTS.md
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
RE_XFAIL = re.compile(r"//\s*XFAIL\s*:")
RE_MAIN = re.compile(r"\bfn\s+main_jhyy\b")
# 2026-10-24 (W-124):`#[no_std]` 程序的入口是 `fn main`(sema 强制要求,
# compiler/src0/sema.jhyy:3160),不是 `fn main_jhyy`。harness 已认它
# (jhyy_regress.py 的 has_main),审计脚本必须**同口径** —— 两边判据漂移时
# 「harness 跑、审计说没跑」会长期对不上(那是 rglob 那次踩过的坑)。
RE_MAIN_NOSTD = re.compile(r"\bfn\s+main\s*\(")
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
    # hello 是 byte-equal 基线 fixture(hello.il / hello_qbe.il / hello_self.il),
    # main_jhyy 体就是 `42` —— 退出码本身就是被测对象,同 exit_zero_extend 一族。
    "hello.jhyy",
}



def strip_comments(src: str) -> str:
    """去掉注释,只留代码 —— 判据指令必须来自代码,不能来自文档。

    2026-10-15 踩到:重写 `generics_err_unsubst.jhyy` 时,我在文件头的说明文字里
    写了「此前是 `return 42` + `//EXPECT:42`」,结果那条 `//EXPECT:42` **真的
    变成了判据指令** —— harness 的正则扫全文,不区分注释与代码。于是「这段文档在
    描述旧行为」变成了「这个测试断言退出码 42」。

    这不是笔误能概括的问题:任何人写 changelog 式注释时提到一个指令,就会静默
    给自己造一条断言(或造一个永不失败的断言)。判据扫描必须先剥注释。
    """
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '"' or c == "'":
            # 字符串字面量:原样拷贝到闭合引号(处理 \ 转义)
            q = c
            out.append(c); i += 1
            while i < n:
                if src[i] == "\\" and i + 1 < n:
                    out.append(src[i]); out.append(src[i + 1]); i += 2; continue
                out.append(src[i])
                if src[i] == q:
                    i += 1; break
                if src[i] == "\n":
                    break
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i + 1 < n and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c); i += 1
    return "".join(out)


RE_DIRECTIVE_TAIL = re.compile(
    r'^\s*(EXPECT|EXPECT-ERROR|EXPECT-OUT|XFAIL|SKIP|SKIP-QBE|SETENV)')


def _comment_tail(line: str) -> str:
    """返回一行里**第一个不在字符串字面量中的 `//` 之后**的文本;没有则 ""。

    必须跳过字符串:`let s = "// EXPECT: 42";` 这种不该被判成一条指令。
    """
    in_str = None
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if in_str:
            if c == "\\" and i + 1 < n:
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in "\"'":
            in_str = c
            i += 1
            continue
        if c == "/" and i + 1 < n and line[i + 1] == "/":
            return line[i + 2:]
        i += 1
    return ""


def directive_source(raw: str) -> str:
    """只保留「注释部分就是一条指令」的行,丢掉其余注释。

    为什么不能简单地把所有注释剥掉再扫:判据指令本身就是 `//` 注释
    (`// EXPECT: 42`),剥掉注释等于把指令也剥了。

    为什么不能直接在全文里搜:那样**文档里提到一个指令就会凭空生成一条**。
    实测踩到过 —— 重写 `generics_err_unsubst.jhyy` 时在说明文字里写了
    「此前是 `return 42` + `//EXPECT:42`」,结果那条真的变成了断言。

    判据:取该行**第一个不在字符串里的 `//` 之后**的文本,去掉空白后必须
    以指令关键字开头。两种写法都支持:
        `// EXPECT: 42`               (整行注释)
        `    return 42;  // EXPECT: 42` (行尾注释 —— null_*.jhyy 就是这种)
    散文里提到指令的那一行,`//` 后面是别的字,匹配不上。
    """
    out = []
    for line in raw.splitlines():
        tail = _comment_tail(line)
        if tail and RE_DIRECTIVE_TAIL.match(tail):
            # 把 `//` 加回去:下游的 RE_EXPECT / RE_EXPECT_OUT / ... 都以 `//` 开头,
            # 剥掉会让它们全部匹配不上(踩过一次)。
            out.append("//" + tail)
    return "\n".join(out)


def classify(path: Path) -> dict:
    """给单个测试文件分类。"""
    raw = path.read_text(encoding="utf-8", errors="replace")
    dirs = directive_source(raw)       # 指令:只认独立成行的注释
    code = strip_comments(raw)         # 结构(fn/return/if):只看代码
    has_main = bool(RE_MAIN.search(code)) or (
        "#[no_std]" in code and bool(RE_MAIN_NOSTD.search(code)))
    expect = RE_EXPECT.search(dirs)
    has_out = RE_EXPECT_OUT.search(dirs) is not None
    has_err = RE_EXPECT_ERR.search(dirs) is not None
    is_skip = RE_SKIP.search(dirs) is not None
    is_xfail = RE_XFAIL.search(dirs) is not None

    info = {
        "file": str(path.relative_to(EXAMPLES)),
        "has_main": has_main,
        "expect": int(expect.group(1)) if expect else None,
        "has_out": has_out,
        "has_expect_error": has_err,
        "is_skip": is_skip,
        "is_xfail": is_xfail,
    }

    if not has_main:
        info["class"] = "library"
        return info

    body = _main_body(code)
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
    elif is_xfail:
        # XFAIL = 声明为「预期失败」的测试(对应 bug 未修)。「主程序写死常量」
        # 这类断言强度规则**不适用**于它 —— 它本来就该失败。
        #
        # 那 XFAIL 标记怎么保证不撒谎?靠运行时的 **XPASS**:一旦这个测试转绿,
        # regress 会记 XPASS 并让 suite 失败(意味着 bug 修好了却忘了摘标记)。
        #
        # ⚠️ 但 XPASS 只有在「这个测试真能失败」时才携带信息。
        # harness 对**无 EXPECT** 的测试是「只要不是 NTSTATUS 崩溃就算 PASS」
        # (jhyy_regress.py run_test 的 `if expected is None` 分支)—— 这种测试
        # 无论 bug 在不在都算过,XPASS 恒定触发,安全网是空的。
        #
        # 实测踩到过:codegen_call_return_types.jhyy 有 XFAIL 但**没有 EXPECT**,
        # 于是本地 STACK_OVERFLOW → XFAIL(对),CI 上不崩 → XPASS(假绿),
        # 而 audit --strict 也没报它 —— XFAIL 豁免把它藏住了。
        #
        # 所以:XFAIL 豁免的是「断言强度」,不是「有没有断言」。完全没有断言
        # 指令的 XFAIL 测试必须判违规。
        if not (expect or has_err or has_out):
            info["class"] = "zero-signal-xfail"
            info["violation"] = (
                "XFAIL 测试没有任何断言(无 EXPECT / EXPECT-ERROR / EXPECT-OUT)。"
                "无 EXPECT 时 harness 只要不崩就算 PASS,XPASS 恒定触发,"
                "XFAIL 的安全网是空的。")
        else:
            info["class"] = "xfail"
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
    if m:
        return m.group(1)
    # 2026-10-24 (W-124):`#[no_std]` 程序的入口是 `fn main`。
    # (`\bfn\s+main\s*\(` 不会误配 `fn main_jhyy(` —— `_` 既不是 `(` 也不是空白。)
    m = re.search(r"\bfn\s+main\s*\([^\n{]*\{(.*?)\n\}", src, re.S)
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
    violations = (buckets.get("crash-only", []) + buckets.get("literal-return", [])
                  + buckets.get("zero-signal-xfail", []))
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
                  "expect-error", "xfail", "zero-signal-xfail", "skipped", "library"):
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
            zs = buckets.get("zero-signal-xfail", [])
            if zs:
                print("\n--- zero-signal-xfail(XFAIL 但没有任何断言)---")
                for r in zs:
                    print(f"    {r['file']}")
                    print(f"      {r.get('violation', '')}")

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
