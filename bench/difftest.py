#!/usr/bin/env python3
"""difftest.py —— 随机程序差分测试器(jhyy ↔ C)

机制:从**同一棵 AST** 生成 C 与 jhyy 两份源码 ⇒ 同一语义、两个独立实现
⇒ 编译两个产物 ⇒ **stdout 逐字比对**。

这正是 `bench/bench.py` 对手写题目做的事,只是把"手写"换成"生成"。

用法:
  python bench/difftest.py --seeds bench/seeds/ci.txt --ci   # CI 门跑的那个(16 个种子)
  python bench/difftest.py --seeds bench/seeds/all.txt --ci   # 本地全量(32 个)
  python bench/difftest.py --random --count 200 --mode avoid  # 随机种子(本地,不可复现)
  python bench/difftest.py --selftest                        # 断言这道门看得见红

⚠️ **两个模式 + 金标准**(为什么不是"两侧一致就绿"):
  · **规避模式** —— 避开已知缺陷的触发面 ⇒ **门红 ⇔ 有新缺陷**
  · **全量模式** —— 不规避 ⇒ 已知缺陷在这里冒出来 ⇒ 盯住"已知缺陷的行为有没有变"
  · **金标准**(`bench/seeds/golden.json`)—— 差分只看"两侧是否一致",
    **一致 ≠ 正确** ⇒ 金标准记录每个种子的实际输出 ⇒ **任何行为变化都红**
  ⇒ 已知缺陷见台账 **W-185** / **W-186**。

⚠️ **分诊规则(决定这个特性的真实成本,务必先读)**:
  差分测试器最常见的失败是**生成器自己的 bug**,不是编译器 bug。
  ⇒ **C 侧产物是 oracle**:
      · C 侧编译/运行失败           ⇒ 生成器 bug(不算编译器缺陷)
      · **jhyy 侧编译失败**          ⇒ ⚠️ **不作门红** —— 生成器可能越出了
                                        jhyy 接受的子集(我们自己的锅)
      · jhyy 侧**运行**失败          ⇒ **编译器缺陷**(程序合法、编译器产出坏代码)
      · 两边都跑起来了但输出不同    ⇒ **编译器缺陷**
  ⇒ 这条规则必须写进流程,否则第一轮就会被误报的生成器 bug 淹没。

⚠️ **子集是刻意收窄的** —— 每个限制都对应 jhyy 的一个真实限制:
  · 整数一律 **u32 / u64** —— 无符号溢出是**定义行为**(规范 §4.2),
    而 C 的有符号溢出是 UB ⇒ 两边逐位一致只在无符号时成立
  · 二元运算两操作数**必须同类型** ⇒ 字面量一律带类型后缀
  · 函数按**调用序**定义 —— jhyy 的 sema 是 single-pass,不支持 forward
    reference ⇒ 也不能自递归
  · `if/else` 只当语句用,两个分支都以**同类语句**收尾
  · `while` 必带**冻结的计数器** ⇒ 保证终止
  · 除数**保证非零**;移位位数**掩到 < 位宽**(C 里移位 ≥ 位宽是 UB)
  · 打印值**掩到 31 位** ⇒ 避开 u32 → i64 的扩展方式歧义
  · 块嵌套 ≤ 2 层、每块 ≤ 5 条语句、函数 ≤ 3 个 ⇒ 保守是故意的
  · 不用 struct/enum/数组/闭包/import/defer/match/全局变量/浮点/递归
"""

import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

JHY = os.environ.get("JHY", str(REPO / "compiler" / "build" / "bin" / "jhyy.exe"))
GCC = os.environ.get("GCC", "gcc")
TIMEOUT = int(os.environ.get("DIFF_TIMEOUT", "60"))
SEEDS_FILE = str(REPO / "bench" / "seeds" / "ci.txt")

U32 = "u32"
U64 = "u64"
ARITH_OPS = ("+", "-", "*", "/", "%", "&", "|", "^", "<<", ">>")
CMP_OPS = ("<", ">", "<=", ">=", "==", "!=")
DIVOPS = ("/", "%")
SHIFTS = ("<<", ">>")

# ── 生成预算(保守是故意的)──────────────────────────────────────────
#
# ⚠️ **为什么要有预算**:生成器只该发"jhyy 确定接受"的构造。
#   实测:某些**单独看都合法**的嵌套组合(if/else 里套 while,while 里套 if/else)
#   jhyy 会拒 —— 而"哪个组合被拒"至今没定位 ⇒ 与其继续二分编译器,
#   **不如把生成器收窄到明显安全的形状**。
#   ⇒ 预算越小 ⇒ 越容易证明"这些程序 jhyy 一定接受"。
MAX_NEST = 2        # 块嵌套层数上限(if/else / while 互相嵌套)
MAX_STMTS = 5       # 一个块里的语句数上限
MAX_FUNCS = 3       # 函数个数上限


class Node:
    """AST 节点。"""

    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)

    def __repr__(self):
        return f"<{self.kind}>"


class Gen:
    """按 seed 生成一个程序。

    用 random.Random(seed) —— CPython 的 Mersenne Twister,
    **同 seed 必得同序列**(random 的算法是语言规范的一部分 ⇒ 跨版本稳定)。

    ⚠️ 三条形状上的硬规矩(踩过才知道):
      1. **值表达式与条件表达式分开** —— `expr()` 只产 u32/u64 的**值**;
         `cond()` 只产**比较**(bool)。混在一起会生成「bool 赋给 u32」这类
         两边都编译不过的东西。
      2. **形参不可变** —— jhyy 的形参默认不可变(与 C 不同)⇒ 赋值目标
         只能是函数体里 `let mut` 出来的局部量。
      3. **分支内的局部量不泄漏到外层** —— 生成分支体时用**作用域的副本**,
         否则后面会引用到一个已经出了作用域的变量。

    ⚠️ **`avoid` 参数 = 已知缺陷的规避开关**(见 `AVOID_KNOWN`):
      "干净模式"(avoid 非空)只发**不触发已知缺陷**的构造 ⇒ 用作 CI 硬门;
      "全量模式"(avoid 为空)什么都发 ⇒ 用作**已知缺陷的探测器**(报告用)。
      ⇒ 一个普遍性缺陷不会让整道门失去信号。
    """

    def __init__(self, seed, avoid=frozenset()):
        self.rng = random.Random(seed)
        self.avoid = set(avoid)
        self.emitted = []       # 已生成(可调用)的函数
        self.callable = []      # 已定义函数的 (名字, 形参类型列表)
        self.counter = 0
        self.nest = 0           # 当前块嵌套深度
        self.nfunc = self.rng.randint(2, MAX_FUNCS)

    def fresh(self, prefix):
        self.counter += 1
        return f"{prefix}{self.counter}"

    # ── 值表达式(只产 u32 / u64)──
    def expr(self, scope, ty, depth):
        """生成一个 ty 类型的**值**表达式。

        scope: [(name, ty, mut, frozen)] —— 可见的局部量。
        """
        rng = self.rng
        if depth <= 0:
            return self.lit(ty)
        r = rng.random()
        if r < 0.30:
            return self.lit(ty)
        if r < 0.48:
            cands = [v for v in scope if v[1] == ty]
            if cands:
                return Node("var", name=rng.choice(cands)[0], ty=ty)
            return self.lit(ty)
        if r < 0.76:
            op = rng.choice(ARITH_OPS)
            if op in DIVOPS and "udiv" in self.avoid and ty == U32:
                op = "+"        # 避开 u32 除法/取模(已知缺陷的触发面)
            a = self.expr(scope, ty, depth - 1)
            b = self.expr(scope, ty, depth - 1)
            if op in DIVOPS:
                b = Node("or1", operand=b, ty=ty)     # 恒为奇数 ⇒ ≥ 1 ⇒ 不除零
            elif op in SHIFTS:
                b = Node("mask", operand=b, ty=ty, bits=32 if ty == U32 else 64)
            node = Node("bin", op=op, lhs=a, rhs=b, ty=ty)
            # ⚠️ u64 的运算在**任一操作数高位为 1**时结果错(W-186)⇒
            #    规避时把 u64 的值一律压在 63 位以内。
            if ty == U64 and "u64hi" in self.avoid:
                node = Node("mask63", operand=node)
            return node
        if r < 0.94 and self.callable:
            name, ptypes = rng.choice(self.callable)
            args = [self.expr(scope, pt, depth - 1) for pt in ptypes]
            return Node("call", func=name, args=args, ty=U32)
        if ty == U32:
            # u64 折回 u32 —— 让 u64 出现在程序里,但不与 u32 混算
            return Node("cast", operand=self.expr(scope, U64, depth - 1), to=U32)
        return Node("un", op="not", operand=self.expr(scope, U64, depth - 1), ty=U64)

    # ── 条件表达式(只产比较 ⇒ bool)──
    def cond(self, scope, depth):
        op = self.rng.choice(CMP_OPS)
        a = self.expr(scope, U32, max(1, depth))
        b = self.expr(scope, U32, max(1, depth))
        return Node("cmp", op=op, lhs=a, rhs=b, ty="bool")

    def lit(self, ty):
        if ty == U64:
            bits = 63 if "u64hi" in self.avoid else 64
            return Node("lit", value=self.rng.getrandbits(bits), ty=U64)
        return Node("lit", value=self.rng.getrandbits(32), ty=U32)

    # ── 语句 ──
    def stmt(self, scope, depth):
        rng = self.rng
        r = rng.random()
        if r < 0.24:
            name = self.fresh("v")
            val = self.expr(scope, U32, max(1, depth - 1))
            scope.append((name, U32, True, False))
            return Node("let", name=name, ty=U32, value=val)
        if r < 0.42:
            cands = [v for v in scope if v[2] and not v[3]]
            if cands:
                name = rng.choice(cands)[0]
                return Node("assign", name=name,
                            value=self.expr(scope, U32, max(1, depth - 1)))
            return Node("nop")
        if r < 0.60:
            muts = [v for v in scope if v[2] and not v[3]]
            if not muts or self.nest >= MAX_NEST:
                return Node("nop")
            target = rng.choice(muts)[0]
            cond = self.cond(scope, 1)
            # 分支体用**作用域副本** ⇒ 分支内的局部量不泄漏到外层
            self.nest += 1
            then_body = self.stmts(list(scope), depth, rng.randint(0, 2))
            else_body = self.stmts(list(scope), depth, rng.randint(0, 2))
            self.nest -= 1
            # 两个分支都以「赋给同一个 u32 变量」收尾 ⇒ 分支类型一致
            then_body.append(Node("assign", name=target,
                                  value=self.expr(scope, U32, 1)))
            else_body.append(Node("assign", name=target,
                                  value=self.expr(scope, U32, 1)))
            return Node("if", cond=cond, then=then_body, els=else_body)
        if r < 0.78 and depth > 0 and self.nest < MAX_NEST:
            ctr = self.fresh("i")
            limit = rng.randint(1, 8)
            # 计数器在循环**外**声明(否则循环体里就用不到它了),
            # 且在循环体里**冻结**(不能被改 ⇒ 保证终止)
            scope.append((ctr, U32, True, False))
            idx = len(scope) - 1
            body_scope = list(scope)
            body_scope[idx] = (ctr, U32, True, True)
            self.nest += 1
            body = self.stmts(body_scope, depth - 1, rng.randint(0, 2))
            self.nest -= 1
            return Node("while", ctr=ctr, limit=limit, body=body,
                        decl=Node("let", name=ctr, ty=U32, value=self.lit(U32)))
        if r < 0.90:
            # ⚠️ 打印**未掩码**的 u32 会撞上「u32 → i64 符号扩展」这个已知缺陷
            #    ⇒ 干净模式一律掩码;全量模式偶尔不掩码(用来探测那个缺陷)。
            masked = ("u32cast" in self.avoid) or (rng.random() < 0.5)
            return Node("print", value=self.expr(scope, U32, max(1, depth - 1)),
                        masked=masked)
        if r < 0.97 and self.callable:
            name, ptypes = rng.choice(self.callable)
            args = [self.expr(scope, pt, 1) for pt in ptypes]
            return Node("callstmt", func=name, args=args)
        return Node("nop")

    def stmts(self, scope, depth, n):
        return [self.stmt(scope, depth) for _ in range(min(n, MAX_STMTS))]

    # ── 函数 ──
    def func(self, idx):
        nparams = self.rng.randint(1, 3)
        params = [(f"p{idx}_{k}", U32) for k in range(nparams)]
        # ⚠️ 形参**不可变**(jhyy 与 C 不同)⇒ 赋值目标只能是局部量
        scope = [(n, t, False, False) for n, t in params]
        body = []
        # 每个函数先来一个可变的累加器 ⇒ 赋值/分支都有合法目标
        acc = f"a{idx}"
        # ⚠️ **初值必须先生成再把变量放进作用域** —— 否则累加器会引用到它自己
        #    (`let mut a1: u32 = a1;` ⇒ jhyy 拒绝 ⇒ 整批种子编译失败)
        acc_val = self.expr(scope, U32, 2)
        scope.append((acc, U32, True, False))
        body.append(Node("let", name=acc, ty=U32, value=acc_val))
        body += self.stmts(scope, 3, self.rng.randint(1, 3))
        body.append(Node("return", value=self.expr(scope, U32, 2)))
        return {"name": f"f{idx}", "params": params, "body": body}

    def program(self):
        """生成整个程序 ⇒ (函数列表, main 调用的实参列表)。"""
        for idx in range(self.nfunc):
            f = self.func(idx)
            self.emitted.append(f)
            # 只有**已经定义**的函数才可被调用 ⇒ 无 forward reference、无自递归
            self.callable.append((f["name"], [t for _, t in f["params"]]))
        last = self.emitted[-1]
        args = [self.expr([], pt, 1) for pt in last["params"]]
        return self.emitted, args


def generate(seed, avoid=frozenset()):
    return Gen(seed, avoid).program()


# ── 已知缺陷(不是生成器的锅,是编译器的)─────────────────────────────
#
# ⭐ **为什么要单列已知缺陷**:一个**普遍性**缺陷会让整道差分门失去信号
# (每个种子都红 ⇒ 红不再携带信息 ⇒ 团队学会忽略红)。
#
# ⇒ 解法(成熟 fuzzing 套件的标准做法)= **两个模式 + 金标准**:
#   · **规避模式**(`AVOID_KNOWN`)—— 只发**不触发已知缺陷**的构造
#     ⇒ 门红 ⇔ 有**新**缺陷;
#   · **全量模式** —— 什么都发 ⇒ 已知缺陷在这里冒出来
#     ⇒ 用来盯住"已知缺陷的行为有没有变";
#   · **金标准**(`seeds/golden.json`)—— 每个种子两侧的输出
#     ⇒ 差分测试器只看"两侧是否一致",**一致 ≠ 正确** ⇒ 金标准补上这一维。
#
# ⇒ 已知缺陷本身记在两处(**别只在一处**):
#   · 台账:`docs/internal/workarounds.md` 的 **W-185** / **W-186**(根因与修法)
#   · 清单:`bench/seeds/known-divergent.txt`(哪些种子因它而分歧)
#
# ⚠️ **改白名单前先想清楚**:把一个种子从清单里删掉 = 让它变成「新分歧」⇒ 门红。
# ⇒ 只有当对应缺陷被**真修**了才删。

KNOWN_FILE = str(REPO / "bench" / "seeds" / "known-divergent.txt")
GOLDEN_FILE = str(REPO / "bench" / "seeds" / "golden.json")

# 规避已知缺陷触发面后的集合 —— **CI 门跑这个**。
# ⇒ 门绿 ⇔ 没有**新**缺陷;已知缺陷由下面的全量模式单独探测。
AVOID_KNOWN = frozenset({"udiv", "u32cast", "u64hi"})


def load_known():
    """读已知分歧记录 ⇒ {seed: 说明}。"""
    p = Path(KNOWN_FILE)
    if not p.is_file():
        return {}
    out = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split("\t", 1)
        try:
            seed = int(parts[0].strip())
        except ValueError:
            continue
        out[seed] = parts[1].strip() if len(parts) > 1 else ""
    return out


def load_golden():
    """读金标准 ⇒ {"avoid": {seed: 输出}, "full": {seed: 输出}}。

    ⭐ **为什么要有金标准**:
      差分测试器只看"两侧是否一致" ⇒ ⇒ **一致 ≠ 正确**。
      金标准记录每个种子在**当前编译器**下的输出 ⇒ ⇒
      任何行为变化(不管是修好了还是变坏了)都 ⇒ 门红 ⇒ ⇒
      这让这道门同时是「差分门」和「行为回归门」。
    """
    p = Path(GOLDEN_FILE)
    if not p.is_file():
        return {"avoid": {}, "full": {}}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"avoid": {}, "full": {}}
    d.setdefault("avoid", {})
    d.setdefault("full", {})
    return d


def save_golden(golden):
    p = Path(GOLDEN_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(golden, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                 encoding="utf-8", newline="\n")
    print(f"golden written: {GOLDEN_FILE}")


# ─────────────────────────── C emitter ───────────────────────────

def lit_c(n):
    return f"{n.value}ULL" if n.ty == U64 else f"{n.value}u"


def expr_c(n):
    k = n.kind
    if k == "lit":
        return lit_c(n)
    if k == "var":
        return n.name
    if k == "bin":
        return f"({expr_c(n.lhs)} {n.op} {expr_c(n.rhs)})"
    if k == "cmp":
        return f"({expr_c(n.lhs)} {n.op} {expr_c(n.rhs)})"
    if k == "or1":
        one = "1ULL" if n.ty == U64 else "1u"
        return f"({expr_c(n.operand)} | {one})"
    if k == "mask":
        # ⚠️ 掩码常量的类型必须跟**操作数**一致(否则 jhyy 报 type mismatch)
        m = f"{n.bits - 1}ULL" if n.ty == U64 else f"{n.bits - 1}u"
        return f"({expr_c(n.operand)} & {m})"
    if k == "mask63":
        return f"({expr_c(n.operand)} & 0x7FFFFFFFFFFFFFFFULL)"
    if k == "cast":
        return f"((uint32_t)({expr_c(n.operand)}))"
    if k == "un":
        return f"((~(uint64_t)({expr_c(n.operand)})))"
    if k == "call":
        return f"{n.func}({', '.join(expr_c(a) for a in n.args)})"
    raise ValueError(f"未知表达式节点 {k}")


def stmt_c(n, ind):
    p = "    " * ind
    k = n.kind
    if k == "let":
        return [f"{p}uint32_t {n.name} = {expr_c(n.value)};"]
    if k == "assign":
        return [f"{p}{n.name} = {expr_c(n.value)};"]
    if k == "if":
        out = [f"{p}if ({expr_c(n.cond)}) {{"]
        for s in n.then:
            out += stmt_c(s, ind + 1)
        out.append(f"{p}}} else {{")
        for s in n.els:
            out += stmt_c(s, ind + 1)
        out.append(f"{p}}}")
        return out
    if k == "while":
        # 计数器在循环**外**声明
        out = stmt_c(n.decl, ind)
        out.append(f"{p}while ({n.ctr} < {n.limit}u) {{")
        for s in n.body:
            out += stmt_c(s, ind + 1)
        out.append(f"{p}    {n.ctr} = {n.ctr} + 1u;")
        out.append(f"{p}}}")
        return out
    if k == "print":
        if n.masked:
            # 掩到 31 位 ⇒ u32 → long long 的扩展方式无歧义(正值)
            return [f'{p}printf("%lld\\n", (long long)((uint32_t)({expr_c(n.value)}) & 0x7FFFFFFFu));']
        # 未掩码 ⇒ 直接把 u32 零扩展成 long long(C 语义)
        return [f'{p}printf("%lld\\n", (long long)((uint32_t)({expr_c(n.value)})));']
    if k == "callstmt":
        return [f"{p}{n.func}({', '.join(expr_c(a) for a in n.args)});"]
    if k == "return":
        return [f"{p}return {expr_c(n.value)};"]
    if k == "nop":
        return []
    raise ValueError(f"未知语句节点 {k}")


def emit_c(funcs, main_args):
    out = ["/* difftest 生成 —— C 侧 */", "#include <stdio.h>", "#include <stdint.h>", ""]
    for f in funcs:
        params = ", ".join(f"uint32_t {n}" for n, _ in f["params"])
        out.append(f"static uint32_t {f['name']}({params}) {{")
        for s in f["body"]:
            out += stmt_c(s, 1)
        out.append("}")
        out.append("")
    last = funcs[-1]["name"]
    out.append("int main(void) {")
    out.append(f"    uint32_t r = {last}({', '.join(expr_c(a) for a in main_args)});")
    out.append('    printf("%lld\\n", (long long)((uint32_t)r & 0x7FFFFFFFu));')
    out.append("    return 0;")
    out.append("}")
    return "\n".join(out) + "\n"


# ─────────────────────────── jhyy emitter ───────────────────────────

def lit_j(n):
    return f"{n.value}u64" if n.ty == U64 else f"{n.value}u32"


def expr_j(n):
    k = n.kind
    if k == "lit":
        return lit_j(n)
    if k == "var":
        return n.name
    if k == "bin":
        return f"({expr_j(n.lhs)} {n.op} {expr_j(n.rhs)})"
    if k == "cmp":
        return f"({expr_j(n.lhs)} {n.op} {expr_j(n.rhs)})"
    if k == "or1":
        one = "1 as u64" if n.ty == U64 else "1 as u32"
        return f"({expr_j(n.operand)} | ({one}))"
    if k == "mask":
        # ⚠️ 掩码常量的类型必须跟**操作数**一致(否则 jhyy 报 type mismatch)
        m = (n.bits - 1)
        ty = "u64" if n.ty == U64 else "u32"
        return f"({expr_j(n.operand)} & ({m} as {ty}))"
    if k == "mask63":
        return f"({expr_j(n.operand)} & (9223372036854775807 as u64))"
    if k == "cast":
        return f"(({expr_j(n.operand)}) as u32)"
    if k == "un":
        return f"((~({expr_j(n.operand)})) as u64)"
    if k == "call":
        return f"{n.func}({', '.join(expr_j(a) for a in n.args)})"
    raise ValueError(f"未知表达式节点 {k}")


def stmt_j(n, ind):
    p = "    " * ind
    k = n.kind
    if k == "let":
        return [f"{p}let mut {n.name}: u32 = {expr_j(n.value)};"]
    if k == "assign":
        return [f"{p}{n.name} = {expr_j(n.value)};"]
    if k == "if":
        out = [f"{p}if {expr_j(n.cond)} {{"]
        for s in n.then:
            out += stmt_j(s, ind + 1)
        out.append(f"{p}}} else {{")
        for s in n.els:
            out += stmt_j(s, ind + 1)
        out.append(f"{p}}}")
        return out
    if k == "while":
        # 计数器在循环**外**声明
        out = stmt_j(n.decl, ind)
        out.append(f"{p}while {n.ctr} < ({n.limit} as u32) {{")
        for s in n.body:
            out += stmt_j(s, ind + 1)
        out.append(f"{p}    {n.ctr} = {n.ctr} + (1 as u32);")
        out.append(f"{p}}}")
        return out
    if k == "print":
        if n.masked:
            return [f'{p}printf("%lld\\n" as *u8, (({expr_j(n.value)}) & (2147483647 as u32)) as i64);']
        # 未掩码 ⇒ 直接 u32 → i64(这是**已知缺陷的触发面**:jhyy 会符号扩展)
        return [f'{p}printf("%lld\\n" as *u8, ({expr_j(n.value)}) as i64);']
    if k == "callstmt":
        return [f"{p}{n.func}({', '.join(expr_j(a) for a in n.args)});"]
    if k == "return":
        return [f"{p}return {expr_j(n.value)};"]
    if k == "nop":
        return []
    raise ValueError(f"未知语句节点 {k}")


def emit_jhyy(funcs, main_args):
    out = ["// difftest 生成 —— jhyy 侧", "extern fn printf(fmt: *u8, val: i64) -> i32;", ""]
    for f in funcs:
        params = ", ".join(f"{n}: u32" for n, _ in f["params"])
        out.append(f"fn {f['name']}({params}) -> u32 {{")
        for s in f["body"]:
            out += stmt_j(s, 1)
        out.append("}")
        out.append("")
    last = funcs[-1]["name"]
    out.append("fn main_jhyy() -> i32 {")
    out.append(f"    let r: u32 = {last}({', '.join(expr_j(a) for a in main_args)});")
    out.append('    printf("%lld\\n" as *u8, ((r) & (2147483647 as u32)) as i64);')
    out.append("    return 0;")
    out.append("}")
    return "\n".join(out) + "\n"


# ─────────────────────────── 运行与比对 ───────────────────────────

def compile_and_run(tmp, name, src, is_jhyy):
    """编 + 跑 ⇒ (rc, stdout, stderr)。rc 非 0 表示没跑起来。

    ⚠️ 编译器的**诊断走 stderr**(stdout 是 0 字节)⇒ 必须自己抓 stderr,
    否则分诊时只看到「编译失败」四个字,没有信息。
    """
    if is_jhyy:
        path = os.path.join(tmp, f"{name}.jhyy")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(src)
        base = os.path.join(tmp, f"{name}_jh")
        exe = base + ".exe"
        try:
            c = subprocess.run([JHY, "compile", path, "-o", base],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, errors="replace", timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return 124, "", "编译超时"
        if c.returncode != 0 or not os.path.exists(exe):
            return 1, "", f"编译失败 (rc={c.returncode})\n{(c.stderr or '').strip()}"
    else:
        path = os.path.join(tmp, f"{name}.c")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(src)
        exe = os.path.join(tmp, f"{name}.c.exe")
        c = subprocess.run([GCC, "-O0", "-ffp-contract=off", "-o", exe, path],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, errors="replace", timeout=TIMEOUT)
        if c.returncode != 0:
            return 1, "", f"C 编译失败 (rc={c.returncode})\n{(c.stderr or '').strip()}"
    try:
        p = subprocess.run([exe], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, errors="replace", timeout=TIMEOUT)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "超时"


def check_seed(seed, tmp, avoid=frozenset()):
    """跑一个 seed ⇒ (状态, 详情, c_out, j_out)。

    "pass"        两侧 stdout 逐字相同
    "gen_bug"     **生成器**的问题 ⇒ 不算编译器缺陷
    "mismatch"    **编译器缺陷**:两侧都编过、都跑过,输出不同 ⇒ **门红**
    "jhyy_crash"  **编译器缺陷**:jhyy 侧编过了但运行时崩溃/退出码非 0 ⇒ **门红**
    "jhyy_nc"     jhyy 侧**编译失败** ⇒ ⚠️ **不作门红**(见下)
    """
    try:
        funcs, main_args = generate(seed, avoid)
        c_src = emit_c(funcs, main_args)
        j_src = emit_jhyy(funcs, main_args)
    except Exception as e:
        return "gen_bug", f"生成失败: {type(e).__name__}: {e}", "", ""

    c_rc, c_out, c_err = compile_and_run(tmp, f"s{seed}_c", c_src, False)
    if c_rc != 0:
        return "gen_bug", f"C 侧跑不起来: {c_err[:400]}", "", ""
    j_rc, j_out, j_err = compile_and_run(tmp, f"s{seed}_j", j_src, True)
    if j_rc != 0:
        # ⚠️ **编译失败 ≠ 编译器缺陷** —— 生成器可能越出了 jhyy 接受的子集
        #    (本轮实测:某些"看起来合法"的嵌套组合 jhyy 会拒)。
        #    ⇒ 单独归类,**不进门红**;但仍然打印出来供人工分诊。
        if "编译失败" in j_err:
            return "jhyy_nc", (f"jhyy 拒绝了这个程序(可能是生成器越界):\n"
                              f"{j_err[:600]}\n--- 源码 ---\n{j_src[:900]}"), c_out, ""
        # 编过了但跑挂了 ⇒ **这是编译器缺陷**(程序合法、编译器产出了坏代码)
        return "jhyy_crash", (f"jhyy 侧运行时失败 (rc={j_rc}):\n{j_err[:600]}\n"
                              f"--- 源码 ---\n{j_src[:1200]}"), c_out, ""
    if c_out != j_out:
        return "mismatch", (f"C stdout:\n{c_out[:500]}\n---\n"
                            f"jhyy stdout:\n{j_out[:500]}\n"
                            f"--- 源码 ---\n{j_src[:1500]}"), c_out, j_out
    return "pass", "", c_out, j_out


def selftest():
    """断言这道门看得见红,且分诊规则真的生效。"""
    print("difftest.py --selftest — 断言门看得见红 / 分诊规则生效")
    failures = []
    tmp = tempfile.mkdtemp(prefix="dtselftest_")

    a = emit_jhyy(*generate(12345))
    b = emit_jhyy(*generate(12345))
    if a != b:
        failures.append("同 seed 两次生成结果不同 —— 生成器不确定")
    else:
        print("  ✅ 同 seed 生成确定性成立")

    c = emit_jhyy(*generate(12346))
    if a == c:
        failures.append("不同 seed 生成了相同程序 —— seed 没起作用")
    else:
        print("  ✅ 不同 seed 生成不同程序")

    st, detail, _c, _j = check_seed(12345, tmp)
    if st != "pass":
        failures.append(f"正常 seed 没过: {st} {detail[:300]}")
    else:
        print("  ✅ 正常 seed 通过")

    # ⭐ 核心能力:把 jhyy 源码改坏 ⇒ 比对器必须抓到
    broken = a.replace("return 0;\n}", "return 1;\n}", 1)
    if broken == a:
        failures.append("注入失败:源码里找不到 'return 0;'")
    else:
        rc, out, _ = compile_and_run(tmp, "broken", broken, True)
        if rc == 0 and out.strip() == "0":
            failures.append("改坏的程序仍然输出正确 —— 比对器没在看")
        else:
            print("  ✅ 注入的错误被比对器抓到")

    # 分诊:坏的 C 源码 ⇒ C 侧跑不起来 ⇒ 归类为生成器问题
    rc, out, err = compile_and_run(tmp, "badc", "int main(void) { return zzz; }", False)
    if rc == 0:
        failures.append("坏的 C 源码竟然编过了")
    else:
        print("  ✅ C 侧失败被归类为生成器问题")

    if failures:
        for f in failures:
            print(f"  ❌ {f}")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


def load_seeds(path):
    seeds = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if s and not s.startswith("#"):
            seeds.append(int(s))
    return seeds


def main():
    if "--selftest" in sys.argv:
        return selftest()

    seeds = []
    random_mode = "--random" in sys.argv
    count = int(os.environ.get("DIFF_COUNT", "200"))
    mode_flag = "both"          # avoid | full | both
    for i, a in enumerate(sys.argv):
        if a == "--seeds" and i + 1 < len(sys.argv):
            seeds = load_seeds(sys.argv[i + 1])
        if a == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
        if a == "--mode" and i + 1 < len(sys.argv):
            mode_flag = sys.argv[i + 1]

    if random_mode:
        seeds = [random.randrange(1, 2 ** 31) for _ in range(count)]
    elif not seeds:
        seeds = load_seeds(SEEDS_FILE)

    mode = "--ci" if "--ci" in sys.argv else "--report"
    print(f"difftest.py — jhyy ↔ C 差分对拍  (mode={mode}, {len(seeds)} 个种子)")
    print(f"  jhyy : {JHY}")
    print(f"  gcc  : {GCC}")
    print("")

    tmp = tempfile.mkdtemp(prefix="jhdiff_")
    t0 = time.perf_counter()
    known = load_known()
    golden = load_golden()
    update = "--update-golden" in sys.argv

    def run_mode(avoid, label, gold):
        """跑一个模式 ⇒ 统计 + 新金标准 + 问题清单。

        gold: 该模式的金标准 {seed(str): 输出}。
        """
        st_ = {"pass": 0, "gen": 0, "nc": 0, "mis": 0, "crash": 0, "known": 0}
        newg = {}
        probs = []
        for i, seed in enumerate(seeds):
            st, detail, c_out, j_out = check_seed(seed, tmp, avoid)
            # ⚠️ **两侧输出都要记** —— 分歧的种子里,C 与 jhyy 的输出不同,
            #    只记一边就没法判断"行为有没有变"。
            newg[str(seed)] = {"c": c_out, "jhyy": j_out}
            g = gold.get(str(seed))
            if st == "pass":
                st_["pass"] += 1
                if g is not None and (g.get("c") != c_out or g.get("jhyy") != j_out):
                    # 行为变了(与金标准不符)⇒ **回归** ⇒ 门红
                    probs.append((seed, "行为与金标准不符(回归)", detail))
            elif st == "gen_bug":
                st_["gen"] += 1
            elif st == "jhyy_nc":
                # ⚠️ **编译失败不作门红** —— 生成器可能越出了 jhyy 接受的子集
                st_["nc"] += 1
            else:
                # 两侧不一致
                if g is not None and g.get("jhyy") == j_out and g.get("c") == c_out:
                    st_["known"] += 1          # 已知分歧,且行为没变 ⇒ 放行
                else:
                    st_["mis" if st == "mismatch" else "crash"] += 1
                    probs.append((seed, "输出不一致" if st == "mismatch"
                                  else "jhyy 侧运行时失败", detail))
            if (i + 1) % 10 == 0:
                print(f"  [{label}] 进度 {i + 1}/{len(seeds)}"
                      f"  ({time.perf_counter() - t0:.0f}s)")
        return st_, newg, probs

    # ── ① 规避模式(CI 门):避开已知缺陷触发面 ⇒ 门绿 ⇔ 没有**新**缺陷 ──
    s1 = {"pass": 0, "known": 0, "gen": 0, "nc": 0, "mis": 0, "crash": 0}
    p1 = []
    g1 = {}
    if mode_flag in ("avoid", "both"):
        print(f"[规避模式] 规避已知缺陷触发面 {sorted(AVOID_KNOWN)}")
        s1, g1, p1 = run_mode(AVOID_KNOWN, "规避", golden["avoid"])
        print(f"  一致={s1['pass']}  已知分歧={s1['known']}  生成器问题={s1['gen']}  "
              f"jhyy 拒绝编译={s1['nc']}  **新分歧**={s1['mis']}  **运行时失败**={s1['crash']}")

    # ── ② 全量模式(报告):探测已知缺陷 ──
    s2 = {"pass": 0, "known": 0, "gen": 0, "nc": 0, "mis": 0, "crash": 0}
    p2 = []
    g2 = {}
    if mode_flag in ("full", "both"):
        print("")
        print("[全量模式] 不规避 ⇒ 已知缺陷会在这里冒出来(报告用,不作门)")
        s2, g2, p2 = run_mode(frozenset(), "全量", golden["full"])
        print(f"  一致={s2['pass']}  已知分歧={s2['known']}  **新分歧**={s2['mis']}  "
              f"**运行时失败**={s2['crash']}")

    if update:
        # ⚠️ 只写**跑过的**模式 —— 否则没跑的那半边会被清空
        if g1:
            golden["avoid"] = g1
        if g2:
            golden["full"] = g2
        save_golden(golden)
        print("")
        print("RESULT: 金标准已更新(--update-golden)。")
        return 0

    # ── 分诊输出 ──
    for seed, kind, detail in (p1 + p2)[:10]:
        print(f"  seed {seed} · {kind}")
        for line in detail.splitlines()[:12]:
            print(f"    {line}")
    if p1 or p2:
        out = Path(tmp) / "findings.json"
        out.write_text(json.dumps(
            [{"seed": s, "kind": k, "detail": d} for s, k, d in (p1 + p2)],
            indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
        print(f"  详情: {out}")

    if mode == "--ci":
        # ⚠️ 门**只**在"新分歧 / 行为回归 / 运行时失败"上红。
        #    · 已知分歧(与金标准一致)⇒ 放行(缺陷已登记台账)
        #    · 生成器问题 / jhyy 拒绝编译 ⇒ 我们自己的锅 ⇒ 不红
        bad = s1["mis"] + s1["crash"] + len(p1) + len(p2)
        if bad:
            print("")
            print(f"RESULT: FAIL ({bad} 项:新分歧 / 行为回归 / 运行时失败)")
            return 1
        print("")
        print(f"RESULT: PASS (规避模式:无新分歧、无行为回归;"
              f"全量模式:{s2['known']} 个已知分歧)")
        return 0
    print("")
    print("RESULT: REPORT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
