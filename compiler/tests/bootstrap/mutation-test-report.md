# Mutation Test Report — v2.14.0

**Date**: 2026-09-22 16:55:20

**JHYY root**: `C:\Users\liuzhen\Desktop\coding\JiHuiYiYou-axis-v2`

## Summary

| Metric | Value |
|---|---|
| Total mutations | 30 |
| Caught | 30 |
| Missed | 0 |
| Setup fail | 0 |
| **Catch rate** | **100.0%** (threshold 80%) |
| Baseline regress PASS | 126 |
| Baseline compile exit | 0 |

## By Category

| Category | Caught | Missed | Setup fail | Catch rate |
|---|---|---|---|---|
| abi | 5 | 0 | 0 | 100.0% |
| codegen | 10 | 0 | 0 | 100.0% |
| parser | 10 | 0 | 0 | 100.0% |
| typechecker | 5 | 0 | 0 | 100.0% |

## Per Mutation Detail

| ID | Category | Status | Expected catch | Description | Time |
|---|---|---|---|---|---|
| M-001 | abi | caught | compile_il_diff | ABI: 8-class SysV NO_CLASS 常量 value 改 → 期望 IL diff | 2.0s |
| M-002 | abi | caught | compile_il_diff | ABI: 8-class SysV classifier 函数 rename → 期望 compil | 2.0s |
| M-003 | abi | caught | compile_il_diff | ABI: borrow marker 常量 rename → 期望 compile_il_diff  | 2.2s |
| M-004 | abi | caught | compile_il_diff | ABI: QBE type letter W (word 64-bit) value 改 → 期望  | 2.1s |
| M-005 | abi | caught | compile_il_diff | ABI: QBE type letter B (boolean) value 改 → 期望 IL d | 2.0s |
| M-006 | codegen | caught | compile_fail | codegen: AST node 构造器 rename (AddrOf 是 V3-A 取址 op) | 0.2s |
| M-007 | codegen | caught | compile_fail | codegen: AST node 构造器 rename (AlignOf 是 V3-A align | 0.2s |
| M-008 | codegen | caught | compile_fail | codegen: AST node 构造器 rename (asm_block 是 V3-A inl | 0.2s |
| M-009 | codegen | caught | compile_fail | codegen: continue AST 节点 rename → 期望 compile fail | 0.2s |
| M-010 | codegen | caught | compile_il_diff | codegen: match arm 上限常量 value 改 → 期望 compile_il_di | 2.4s |
| M-011 | codegen | caught | compile_il_diff | codegen: IL lexer 'volatile' keyword 字符串改 (volatil | 2.0s |
| M-012 | codegen | caught | compile_il_diff | codegen: ILTOK_STORE value 改 (STORE IL emit path)  | 2.1s |
| M-013 | codegen | caught | compile_il_diff | codegen: ILTOK_RET value 改 (RET IL emit path) → 期望 | 2.1s |
| M-014 | codegen | caught | compile_il_diff | codegen: ILTOK_JMP value 改 (JMP IL emit path) → 期望 | 2.0s |
| M-015 | codegen | caught | compile_il_diff | codegen: ILTOK_JNZ value 改 (JNZ IL emit path) → 期望 | 2.1s |
| M-016 | parser | caught | compile_fail | parser: asm_block parse 函数定义 rename (V3-A inline a | 0.2s |
| M-017 | parser | caught | compile_fail | parser: fence_block parse 函数定义 rename → 期望 compile | 0.2s |
| M-018 | parser | caught | compile_fail | parser: generic instantiation recorder rename → 期望 | 0.2s |
| M-019 | parser | caught | compile_fail | parser: type mangling buffer grow 函数 rename → 期望 c | 0.2s |
| M-020 | parser | caught | compile_fail | parser: type node mangling 函数 rename → 期望 compile  | 0.2s |
| M-021 | parser | caught | compile_fail | parser: token name lookup 函数 rename → 期望 compile f | 0.2s |
| M-022 | parser | caught | compile_fail | parser: simple-only dispatch 函数 rename → 期望 compil | 0.2s |
| M-023 | parser | caught | compile_fail | parser: function attributes parse (naked/link_sect | 0.2s |
| M-024 | parser | caught | compile_fail | parser: TOKEN_FN 常量定义 rename → 期望 compile fail (pa | 0.2s |
| M-025 | parser | caught | compile_fail | parser: TOKEN_RETURN 常量定义 rename → 期望 compile fail | 0.2s |
| M-026 | typechecker | caught | compile_il_diff | typechecker: sema context size 常量 value 改 (88 → 9) | 2.1s |
| M-027 | typechecker | caught | compile_fail | typechecker: sema_local_at 函数 rename (locals array | 0.2s |
| M-028 | typechecker | caught | compile_fail | typechecker: sema_local_set 函数 rename (locals arra | 0.2s |
| M-029 | typechecker | caught | compile_il_diff | typechecker: type arena size 常量 value 改 (112 → 9)  | 2.3s |
| M-030 | typechecker | caught | compile_il_diff | typechecker: KIND enum 'unresolved' tag value 改 (9 | 2.0s |

## Verification Gates (per docs/plans/v2/v2.14.0-plan.md Phase 2)

- ✅ Catch rate ≥ 80%: PASS (100.0%)
- ✅ False positive = 0: PASS (no mutation failed application + harness runs OK)
- ✅ mutation-test-report.md 完整: PASS
- ✅ Baseline regress 126 ≥ 126: PASS

