# Changelog v1.0.0-rc (2026-08-10)

**Stage 2 实用闭环达成 — jhyy_v1 自举 jhyy_v2 (sha `c980c785...`) 编译 hello.jhyy → EXIT=42**

## 成就

| 项 | 值 |
|---|---|
| jhyy_v2 binary | 432KB Windows .exe (sha `c980c7856b59596dc709d5bd7ed29a97f087237ec52783b1c842bb5b5546e679`) |
| jhyy_v2 编 hello.jhyy → EXIT | **42** ✓ |
| regress_v1 baseline (jhyy_v1.exe.exe) | **50/53 passed** (持平 pre-rc) |
| fix_il.py 完整化 | ✓ (10 sret + 4148 dupes removed on self-compiled .il) |
| fix_output_il.py on jhyy_v2 output | ✓ (1 ret fix → byte-equal with jhyy_v1 output) |
| 自举链路 | jhyy_v1.exe.exe → jhyy_v2.exe → hello.exe (Stage 2 closure 实证) |

## 已知限制（不算 blocker）

1. **fix_output_il.py 是 escape hatch** — jhyy_v2 的 ret temp corruption 由 fix_output_il.py Fix 6 修。W-005 #2 根因（C-side codegen.c struct pass-by-value）未真修。
2. **jhyy_v2 不能直接 build 大型 .jhyy** — cg_module crash on more complex inputs (let mut + recursion + while loop). 仅 hello.jhyy 实证。
3. **fix_il.py Fix 8 renumbering 改变了所有 temp ID** — 不影响 QBE 输出,但让 j1 vs j2 字节对比需要 fix_output_il.py 后的输出 (Stage 2 byte-equal after fix)。
4. **M4 (byte-equal) 未达成 raw .il** — fix_output_il.py 后的 .il 是 byte-equal,但原始 j2 输出有 ret temp mismatch. Sprint 4.20+ 计划通过 W-005 #2 真修达成 raw byte-equal。

## Sprint 4.18 + 4.19 关键 fix

- **QBE `-o` flag ordering** — 必须 `-o output.s input.il`,非 `input.il -o output.s` (POSIX getopt 约定)
- **fix_il.py Fix 6 (ret temp mismatch)** — jhyy_v2 单函数 ret `%t536` corruption 自动 fix
- **inline_imports new_cap 16384 → 65536** — 6699 decls 容纳

## Sprint 4.20+ 待办

- v0 codegen.c W-005 #2 真修 (用户授权后)
- Stage 2 N=3 byte-equal (M4 hard)
- tag v1.0.0 (post-M4)