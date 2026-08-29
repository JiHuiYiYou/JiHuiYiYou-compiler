# compiler/src0/bootstrap/v1.0/

历史 selfhost 闭环节点归档 — v1.0 真自举闭环已完成 (commit `eabee0d`, tag `v1.0.0`),
这些文件是**归档参考**,不再用于 build 或 regress。

## 文件清单

### Sprint 单元测试 driver (10 文件)

每个 sprint 提交时的单元测试入口,验证当前 sprint 新增的模块功能。
退出码约定: `42` (沿用 `_driver.jhyy` 惯例) — 0 = FAIL, 42 = PASS。

| 文件 | 验证模块 | Sprint |
|------|----------|--------|
| `_driver.jhyy` | arena + util | Sprint 1 |
| `_driver_symtab.jhyy` | symtab | Sprint 2 commit 1 |
| `_driver_ast.jhyy` | ast (literals + exprs) | Sprint 2 commit 3a |
| `_driver_ast_3b.jhyy` | ast (stmts + match + patterns) | Sprint 2 commit 3b |
| `_driver_ast_3c.jhyy` | ast (decls + struct/enum literal) | Sprint 2 commit 3c |
| `_driver_ast_3d.jhyy` | ast (NODE_MODULE) | Sprint 2 commit 3d |
| `_driver_lexer.jhyy` | lexer | Sprint 3 commit 1 |
| `_driver_parser.jhyy` | parser | Sprint 3 commit 2 + 3 |
| `_driver_sema.jhyy` | sema | Sprint 3 commit 5 |
| `_driver_ir.jhyy` | ir 基础 emit | Sprint 4 commit 1 |
| `_driver_types.jhyy` | types | (Sprint 5 类型系统补全) |

### 历史 workaround 归档 (2 文件)

- `_test_sema_layout.jhyy` — W-009 (struct layout) 修复期间临时测试,问题已 RESOLVED。
- `_W002_rename_map.txt` — W-002 archive (211 个 src0 identifier 的 `X → X_v1` rename map)。
  - 历史: v0.8 commit 7 (`0453cef`) 引入 W-002 (绕 hash_string *i32 overread)
  - v0.8 commit 9 (`d570c72`) W-001 真修后 W-002 失效
  - v0.9 wip commit 2.12 (`8a9de1c`) 211 revert 回原名
  - 状态: RESOLVED per `docs/internal/workarounds.md` § W-002
  - 用途: archive — 保留作为可重放参考, 未来若需重新引入 W-002 可直接当 input

## 为什么不删

1. **Git history 已经完整保留**,删除不省任何空间。
2. **未来 revert W-002 或 replay sprint driver 时** 这些文件是唯一 input source (CI 不可重现当时的开发环境)。
3. **CLAUDE.md 工作风格要求**: "Document every workaround in docs" — 历史 workaround 必须留可追溯 artifact。

## 为什么不进 build

- `Makefile` L76 用 `$(SRC0_DIR)/*.jhyy` 通配 build,这些文件 underscore-prefixed 不参与 active build (active 12 个 .jhyy 是 arena/ast/codegen/ffi/ir/lexer/main/parser/sema/symtab/types/util)。
- `compiler/regress.py` / `compiler/tests/` 也不再 reference 这些 driver — 已被 v1.x 真自举闭环覆盖。
- 移到此处纯属物理归档,无 build-time 副作用。