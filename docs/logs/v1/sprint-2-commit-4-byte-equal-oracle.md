# Sprint 2 commit 4 — byte-equal oracle 框架

**日期**: 2026-06-24
**对应 plan**: [`../../plans/v1/v1.0.0详细实现方案.md`](../../plans/v1/v1.0.0详细实现方案.md) line 263 + 369
**状态**: 完成 ✅

## 目标

为 sprint 5 自举 byte-equal 验证准备好工具链：
1. C 端 jhyy 能把任意 .jhyy 文件 dump 成结构化 AST 文本
2. Python 脚本能 diff 两份 AST 文本并定位差异
3. 用 C 端 jhyy 跑 47 个 regress 测试生成 golden 文件

## 实现

### 1. C 端 AST dump

- **新增** `void ast_dump(Node *n)` 到 `compiler/src/ast.c`
- **声明** 在 `compiler/src/ast.h`
- **格式**：每行 kind/字段名 = 值，嵌套节点用 2-space 缩进
- **覆盖**：全部 49 个 NodeKind + sub-struct（NodeFieldInit / StructFieldDecl / EnumVariantDecl / NodeFuncDeclParam）+ Sym（name + kind）+ NodeKind 名（用现有 `node_kind_name`）
- **跳过**：`NODE_SIZEOF` / `NODE_ALIGNOF` 的 `Type*` 字段（sema 阶段才填，dump 时跳过避免依赖 Type 内部表示）

### 2. CLI 命令

- **新增** `jhyy dump <file.jhyy>` 到 `compiler/src/main.c`
- 走 lexer → parser，dump AST 到 stdout
- parse 报错走 stderr 并返回非零退出码

### 3. Python 比较脚本

- **新增** `compiler/tests/ast_oracle.py`
- 入口：`python ast_oracle.py <expected.ast.txt> <actual.ast.txt>`
- 退出码：0 = byte-equal, 1 = mismatch, 2 = error
- 输出：line-by-line diff（行号 + expected + actual），写到 stderr

### 4. Golden 文件

- **新增** `compiler/tests/golden/<test>.ast.txt`，47 个文件，覆盖全部 regress 测试
- 总行数：12141（hello.ast.txt 12 行 → dungeon_game.ast.txt 最大 ~700 行）

## 验证

- ✅ `jhyy.exe` 重新构建成功（无 warning）
- ✅ `jhyy dump` 在 hello.jhyy / array_test.jhyy / dungeon_game.jhyy / match.jhyy / struct.jhyy 全部输出合理
- ✅ `python ast_oracle.py hello.ast.txt hello.ast.txt` → `OK (12 lines byte-equal)`
- ✅ `python ast_oracle.py hello.ast.txt match.ast.txt` → `FAIL (30 of 38 lines differ)`，diff 格式清晰
- ✅ `regress.py` 44/47 passed, 0 failed（dump 是只读新功能，未破坏现有 C 端编译）

## 已知限制（sprint 5 验证时留意）

- **Sym 内 name 字段是 const char***：若 jhyy_0/jhyy_1 走不同 arena 分配器/字符串 intern 策略，Sym→name 指针本身可能不同，但字符串内容应该一致。sprint 5 需要加 `expected == actual` 改 `strcmp(expected, actual) == 0` 检查。
- **dump 不打印 Type**：sema 阶段填的 type 字段不 dump，避免把 Type 的内部表示绑进 oracle。sprint 5 需另写 type dump。
- **dump 不打印 SourceLoc**：loc.filename 字段不 dump（指针不稳定），但 loc.line 也没 dump。sprint 5 需要决定：要不要 dump loc（用于诊断差异），还是完全省掉。

## 下一步

按 plan 接下来是 **sprint 3 commit 1: lexer.jhyy 翻译**（30+ token type 状态机）。预计单文件 ~500 jhyy 行 → commit 1 估 1 个 sprint 子 commit。