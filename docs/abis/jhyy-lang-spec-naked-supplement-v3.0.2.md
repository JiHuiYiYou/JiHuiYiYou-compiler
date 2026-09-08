# jhyy-lang-spec `#[naked]` supplement (v3.0.2)

**Status**: SUPPLEMENT (not part of locked [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md))
**Effective**: v3.0.2 ship (V3-B Phase B Step 1 — 3b `#[naked]`)
**Spec baseline reference**: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17.5
**Plan**: [`docs/plans/v3/iterative-imagining-thunder.md`](../plans/v3/iterative-imagining-thunder.md)

---

## § 1 Background

[`jhyy-lang-spec-v1.3.0.md` § 17.5](../abis/jhyy-lang-spec-v1.3.0.md) reserves the `#[naked]` outer-attribute grammar (LOCKED in v2.2.0 as part of the 6-feature OS 启动前置 grammar). However the codegen / sema implementation has been **D42-stubbed** through V2.x — only the AST field (`is_naked: i32` on `NodeFuncDecl`) and the parser `pending_naked` slot exist; no QBE IR is generated for naked functions and no raw-asm side-file was emitted.

This supplement specifies the v3.0.2 semantics: codegen skips QBE export for naked functions and emits the full function (label + asm body) to the existing `_inline_asm.buf` side-file, which `main.jhyy` post-QBE-pass concatenates into the .s before `link_with_gcc`. The result: naked functions appear in the final .exe with `.globl <name>` + `<name>:` + raw asm, no prologue / epilogue, no QBE interference.

Spec body 不动(per `feedback_changelog_umbrella` v3.x 锁定纪律);本 supplement 是过渡 doc,v3.x 中 spec bump 时合入主 spec。

---

## § 2 Syntax

Outer attribute at function declaration:

```jhyy
#[naked]
fn irq_entry() {
    asm!("iret");
}
```

规则:

- **Function-level only** — `#[naked]` on `extern` decl / struct / type alias = compile error
- **必须接 `fn`** — 紧跟 `fn <ident>()` declaration (no parens between attr and `fn`)
- **Body 必须是 `{ ... }` 块** — naked fn body must be a `NODE_BLOCK` containing only `asm!(...)` expr stmts (each either bare `NODE_ASM_BLOCK` or `NODE_EXPR_STMT` wrapping `NODE_ASM_BLOCK`). Local vars / control flow / `return` = compile error
- **无 params / 无 ret type 推荐** — params 合法(可声明,但 codegen 不生成 prologue/epilogue,params 实际由 caller via call-conv 直送),ret type 必须 void-ish (隐式 unit),因为 naked fn 通过 `asm!("ret")` / `asm!("iret")` 等内联指令返回
- **组合 attribute 限制** — `#[naked]` + `#[inline]` 不支持 (semantic conflict — inline 展开 body 必需 prologue);`#[naked]` + `#[link_section]` (v3.0.4) 组合 = out of scope (v3.x 中补)
- **每 module 任意多个 `#[naked]`** — 没有 per-file 1 个的限制(no_std 反例)

---

## § 3 Semantics

`#[naked]` 出现时编译器切换到 **raw-asm escape hatch** 路径:

1. **不 emit QBE IL** — naked fn 不进入 QBE 的 `export function ... {` 生成流程。codegen 跳过 `abi_win_emit_function_header`,跳过 trailing `ret`/`}` closure。QBE 看不到 naked fn declaration → 不生成对应 .s symbol。
2. **Emit raw asm 到 side-file** — `emit_naked_func_header` 写 `.globl <mangled>\n<mangled>:\n` 到 `compiler/build/obj/_inline_asm.buf` (binary append, per `feedback_qbe_crlf_root_cause`)。asm body 由 `cg_expr NODE_ASM_BLOCK` (per v3.0.1 inline asm) append。
3. **Post-QBE concat** — `main.jhyy` 在 QBE → .s 后、`link_with_gcc` 前,read side-file 并 append 到 temp_asm (binary)。最后 gcc link 把 naked fn + 普通 fn 一起链入。
4. **无 prologue / epilogue** — naked fn 无 `push %rbp` / `mov %rsp, %rbp` / `pop %rbp` / `ret` (除非 asm body 显式 emit)。这是 `#[naked]` 的核心价值:让 OS interrupt entry / syscall handler / boot code 完全控制寄存器和栈。
5. **dbgloc skip** — codegen 的 `cg_dbg_emit_loc` 在 naked fn 内跳过 emit (top-level `dbgloc` 不是合法 QBE 语法)。裸 asm body 仍可通过自身指令保留 source line 关联(不需要 DWARF)。

---

## § 4 ABI

Naked fn 不遵循标准 jhyy ABI (无 prologue/epilogue,无 frame pointer):

- **Caller 必须按平台 ABI 准备 args** — System V AMD64 / Windows x64 按裸寄存器传递(rdi/rsi/rdx/rcx/r8/r9 + xmm0-7)。caller QBE-emitted code 按 ABI 准备 args,naked fn 直接接收。
- **Return 路径** — naked fn 通过 asm 指令返回(`ret` / `iret` / `syscall` 等)。无标准 `ret`。
- **Callee-saved 寄存器** — naked fn 必须保存所有 callee-saved 寄存器如果它要用(`rbx` / `rbp` / `r12-r15` / xmm6-xmm15)。不保存 = 破坏 caller 状态。
- **栈对齐** — caller 必须保证 16-byte stack align at call site(naked fn 不会自动调整)。
- **不参与 `sret`** — naked fn 不接受 struct return(ret type must be void)。

---

## § 5 Interaction with D42 Inline ASM

`#[naked]` 和 `asm!(...)` (v3.0.1) 协同:

- **asm body 必须用 `asm!()`** — naked fn body 是 asm block,直接 emit raw .asm 指令。无 macro / placeholder / register constraint v3.0.2 (operand constraint 留 v3.x 中)。
- **asm body 不分号结尾** — asm!() 内部一行 = 一条 asm 指令(无 trailing `;`)。
- **多个 asm stmt 顺序 emit** — 多个 `asm!(...)` expr stmt 在 naked fn body 中顺序写进 side-file,中间无插入 prologue/epilogue。
- **asm!() 文本由 parser 处理** — 不 escape / 不占位 / 不 register mapping。

---

## § 6 Limitations & Out of Scope

- **不支持 `#[naked]` fn 调非 naked fn** — codegen 无 `call` 指令(裸 asm 写 `call` 可行,但 sema 不警告)。未来 v3.x 中可加 call-from-naked helper。
- **不支持 naked fn 调 naked fn** — 同上。
- **不支持 `#[naked]` + `#[inline]` 组合** — semantic conflict。
- **不支持 ARM / RISC-V naked** — v3.0.2 x86-64 only。ARM `__attribute__((naked))` / RISC-V `.globl naked_fn` 模式留 v3.x 末。
- **不支持 inline asm operand constraint** — v3.0.2 asm!() 只 raw 文本,no `:output(input)` 占位。
- **不支持 goto label / alternative syntax** — 留 v3.x。
- **不支持 `#[naked]` 在 fn body 内部** — 只 fn decl 级。

---

## § 7 Examples

### 7a) OS interrupt entry (典型用例)

```jhyy
#[naked]
fn irq_entry() {
    asm!("pushq %r15");
    asm!("pushq %r14");
    asm!("pushq %r13");
    asm!("pushq %r12");
    asm!("pushq %rbx");
    asm!("sub $0x28, %rsp");
    asm!("mov %rsp, %rdi");
    asm!("callq irq_handler_c");
    asm!("add $0x28, %rsp");
    asm!("popq %rbx");
    asm!("popq %r12");
    asm!("popq %r13");
    asm!("popq %r14");
    asm!("popq %r15");
    asm!("iret");
}

fn main_jhyy() -> i32 { return 0 as i32; }
```

### 7b) 编译产物验证

```
$ grep "push %rbp" naked_test.exe.s          # main_jhyy only — naked fn 无 push %rbp
.globl main_jhyy
.globl main_jhyy
main_jhyy:
    push %rbp
    ...

$ grep "irq_entry" naked_test.exe.s          # naked fn symbol 在 .globl + label
.globl irq_entry
irq_entry:
    pushq %r15
    ...
    iret
```

### 7c) Ship gate test (V3-B ship required)

[`compiler/tests/examples/naked_interrupt_entry.jhyy`](../../compiler/tests/examples/naked_interrupt_entry.jhyy):
- `#[naked] fn irq_entry() { asm!("iret"); }`
- `fn main_jhyy() -> i32 { return 0 as i32; }`
- 期望 EXIT:0 (`main_jhyy` 返回 0;`irq_entry` 永远不会执行因为没 IRQ 触发)
- 验证手段:readelf / objdump 检查 `irq_entry` 在 .exe 里 + `push %rbp` 不出现在 `irq_entry` 函数体内

---

## § 8 Changelog 引用

- v3.0.2 (3b `#[naked]`):ship (per [`docs/logs/v3/changelog-v3.0.md`](../../docs/logs/v3/changelog-v3.0.md))
- D42 inline asm (v3.0.1) 已 ship — `asm!()` 宏作为裸 asm block 入口
- D40 wire-format:不适用
- D41 Debug ABI:不适用(无 dbgloc emit 给 naked fn)

---

## § 9 Cross-Axis Note

V2-B (axis-v2 / amd64_sysv backend) 需在 v2.7.0 独立 ship `emit_naked_func_header` 的 sysv 变体(`.globl mangled` + `mangled:` label 在裸 .s emit,不依赖 MS-specific ABI)。Per [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../plans/roadmap/v2-v3-parallel-sprint-plan.md) § 5.1,v2.7.0 ship 后 OS M1 launch 用 sysv ABI 跑裸 Linux kernel。

---

**批准后生效**:v3.0.2 ship tag (commit + push per `feedback_auto_push_after_commit`)。