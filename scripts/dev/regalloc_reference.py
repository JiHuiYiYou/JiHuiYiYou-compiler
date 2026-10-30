#!/usr/bin/env python3
"""regalloc_reference.py — 寄存器分配器的**独立参考实现**(Python)

用途:跟 jhyy 侧的实现(`compiler/src0/codegen_amd64_rcache.jhyy`)**对拍**。

为什么要有两个实现:两套**独立写的**算法给出同一个数,才说明这个数是对的;
一套实现自己验自己,只能说明它没崩。

跑法:
    JHY_WRITE_IL=1 ./compiler/build/bin/jhyy.exe build compiler/src0/main.jhyy
    python scripts/dev/regalloc_reference.py compiler/src0/main.il

⚠️ `compiler/src0/main.il` 落在**源码目录**里是刻意的,不是污染:
   `jhyy build` **不解析 `-o`**(usage 串写着支持,实现漏了)⇒ 产物必定落在
   input 同目录,没法重定向。而 in-mem 后端默认不落 .il,只有
   `JHY_WRITE_IL=1` 才落 —— 所以这个 .il 只有在显式 opt-in 时才出现,
   且是本对拍流程的输入,不是残留。**别去"顺手清理"它。**

对拍点(实测两者**逐项相同**):
    · 合格候选(def+所有 use 同基本块 + 期间无 call + 整数类型)
    · 实际分配到寄存器的 temp 数(5 个寄存器池)
    · 因池满而退化成栈槽的个数

⚠️ **历史上踩过的坑**(2026-10-29):第一版参考实现**只扫 def 行来找 use**
   ⇒ 漏掉了 `store` / `ret` / `jnz` 等**非 def 指令里的 use** ⇒ 活跃区间
   被低估 ⇒ 覆盖率被低估(38.3% vs 真实的 75.7%)⇒ 差点据此否掉整个方案。
   ⇒ 下面这版扫**全部**行。
"""

import collections
import re
import sys

POOL = 5

DEF_RE = re.compile(r'^%(t\d+)\s*=\s*([wlsd])\s+(\S+)')
LABEL_RE = re.compile(r'^@(\w+)\s*$')

# ⚠️ **不要**在这里白名单「哪些 op 定义 temp」。
# lexer 的规则是:**任何 `%tN =<qt> <op>` 行都定义一个 temp** —— op 是什么
# 只决定它被归到哪个 ILTOK_*(BINOP / CALL / COPY / LOAD / …),
# 但**全都是 def**。白名单会漏掉新 op(2026-10-29 第一次写这个参考实现就踩了:
# 漏了 498 条 ⇒ 合格候选少 2978 ⇒ 对拍对不上)。
# ⇒ 规则:**匹配 DEF_RE ⇒ 就是 def**。


def analyse(path):
    raw = open(path, encoding='utf-8', errors='replace').read().split('\n')

    # ① 切函数:「export function」行开头
    fn_bounds = []
    start = None
    for i, l in enumerate(raw):
        if l.strip().startswith('export function'):
            if start is not None:
                fn_bounds.append((start, i))
            start = i
    if start is not None:
        fn_bounds.append((start, len(raw)))

    total_defs = 0
    total_elig = 0
    total_alloc = 0
    total_pool_full = 0
    max_live = 0

    for (fs, fe) in fn_bounds:
        block = 0
        calls = 0
        instrs = []          # (op, dst, qt, block, calls, uses[])
        use_at = collections.defaultdict(list)

        for l in raw[fs:fe]:
            s = l.strip()
            if not s:
                continue
            if LABEL_RE.match(s):
                block += 1
                continue
            if s.startswith(('dbg', 'data', 'export', 'function', 'type', '.', '#', '}', '{')):
                continue
            m = DEF_RE.match(s)
            if m:
                t, qt, op = m.groups()
                isdef = True          # 任何 `%tN =` 行都是 def(见 DEF_RE 处的说明)
                dst = t
            else:
                parts = s.split()
                op = parts[0] if parts else ''
                qt = None
                dst = None
                isdef = False
            i = len(instrs)
            # ⚠️ **call 计数必须在 append 之后自增**(2026-10-30 踩过):
            #   call 指令自身的 calls 值 = **自增前**的计数(它的实参是在这条
            #   call **之前**就要读好的 ⇒ 实参的 use_call 与 def_call 用的是
            #   同一个「自增前」的值 ⇒ 「期间没有 call」才成立)。
            #   先自增 ⇒ 「call 定义的 temp」与「下一个 call 用的 temp」的
            #   def_call / use_call 差 1 ⇒ 合格的被误判成不合格
            #   ⇒ 合格候选少算 ~2600 条(2026-10-29 那版「38.3%」就是这么错的)。
            instrs.append([op, dst, qt, block, calls, isdef])
            if op == 'call':
                calls += 1
            # uses:所有 %tN(**全部行**,不只是 def 行)
            for x in re.findall(r'%t\d+', s):
                if isdef and x[1:] == dst:
                    continue          # 定义处不算「使用」
                use_at[x[1:]].append(i)

        total_defs += sum(1 for e in instrs if e[5])

        # ② 每个 temp 的 def / use 信息
        defidx = {}
        defblk = {}
        defcall = {}
        useblk = {}
        usecall = {}
        lastuse = {}
        hastwo = set()
        for i, e in enumerate(instrs):
            op, dst, qt, blk, cl, isdef = e
            if isdef and dst is not None:
                defidx[dst] = i
                defblk[dst] = blk
                defcall[dst] = cl
            for u, ui in use_at.items():
                pass
        for u, uis in use_at.items():
            if not uis:
                continue
            first = uis[0]
            useblk[u] = instrs[first][3]
            for ui in uis:
                if instrs[ui][3] != useblk[u]:
                    hastwo.add(u)
            usecall[u] = instrs[max(uis)][4]
            lastuse[u] = max(uis)

        # ③ 资格判定
        cand = {}
        for t, di in defidx.items():
            if t not in use_at:
                continue
            if t in hastwo:
                continue
            if useblk[t] != defblk[t]:
                continue
            if usecall[t] != defcall[t]:
                continue
            if defidx[t] is None or lastuse.get(t, -1) < 0:
                continue
            cand[t] = di
        total_elig += len(cand)

        # ④ 线性扫描(5 个寄存器池,lowest reg wins)
        free = list(range(POOL))
        reg = {}
        rel = sorted(cand.items(), key=lambda kv: lastuse[kv[0]])
        ri = 0
        for i, e in enumerate(instrs):
            while ri < len(rel) and lastuse[rel[ri][0]] < i:
                t = rel[ri][0]
                if t in reg:
                    free.append(reg.pop(t))
                ri += 1
            op, dst, qt, blk, cl, isdef = e
            if isdef and dst is not None and dst in cand and cand[dst] == i:
                if free:
                    r = min(free)
                    free.remove(r)
                    reg[dst] = r
                    total_alloc += 1
                else:
                    total_pool_full += 1

        # ⑤ 同时活跃数的极值(校准寄存器池大小用)
        ev = collections.Counter()
        for t in cand:
            ev[defidx[t]] += 1
            ev[lastuse[t] + 1] -= 1
        d = 0
        for p in sorted(ev):
            d += ev[p]
            max_live = max(max_live, d)

    return {
        'defs': total_defs,
        'eligible': total_elig,
        'allocated': total_alloc,
        'pool_full': total_pool_full,
        'max_live': max_live,
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'compiler/src0/main.il'
    r = analyse(path)
    print(f"参考实现(POOL={POOL})  {path}")
    print(f"  def 总数            : {r['defs']}")
    print(f"  ★ 合格候选         : {r['eligible']}")
    print(f"  ★ 实际分配到寄存器 : {r['allocated']}")
    print(f"  池满(退化成栈槽)  : {r['pool_full']}")
    print(f"  ★ 最大同时活跃数   : {r['max_live']}")
    print()
    print("对拍:jhyy 侧跑 `JHY_RCACHE=1 JHY_RCACHE_STATS=1 jhyy build main.jhyy`")
    print("  ⇒ 'candidates' 应等于「合格候选」;'allocated temps' 应等于「实际分配到寄存器」")


if __name__ == '__main__':
    main()
