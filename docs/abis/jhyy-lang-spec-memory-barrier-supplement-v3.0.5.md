# jhyy-lang-spec memory barrier supplement (v3.0.5)

**Status**: SUPPLEMENT (not part of locked [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md))
**Effective**: v3.0.5 ship (V3-B Phase B Step 3 — 3f memory barrier)
**Spec baseline reference**: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17.7
**Plan**: [`docs/plans/v3/iterative-imagining-thunder.md`](../plans/v3/iterative-imagining-thunder.md)

---

## § 1 Background

[`jhyy-lang-spec-v1.3.0.md` § 17.7](../abis/jhyy-lang-spec-v1.3.0.md) reserves the `fence_seq_cst() / fence_acquire() / fence_release()` builtin ident grammar (LOCKED in v2.2.0 as part of the 6-feature OS 启动前置 grammar). However the codegen / sema implementation has been **D42-stubbed** through V2.x — only the `kind: i64` AST field concept existed; no QBE IL was generated and no raw mnem side-file was emitted.

This supplement specifies the v3.0.5 semantics: codegen writes raw mnem (`mfence` / `lfence` / `sfence`) to a new `_fence.buf` side-file, which `main.jhyy`'s post-QBE-pass concats into temp_asm before `link_with_gcc`. The result: fence mnems appear in the final .exe verbatim, providing x86 TSO memory ordering for SMP / MMIO use cases.

Spec body 不动 (per `feedback_changelog_umbrella` v3.x 锁定纪律);本 supplement 是过渡 doc, v3.x 中 spec bump 时合入主 spec。

---

## § 2 Syntax

Three builtin idents, no-arg calls, statement-position only (return unit):

```jhyy
fn main_jhyy() -> i32 {
    fence_seq_cst();   // x86 mfence  — full seq_cst fence
    fence_acquire();   // x86 lfence  — acquire fence (load-load ordering)
    fence_release();   // x86 sfence  — release fence (store-store ordering)
    fence_seq_cst();   // 多次调用顺序 emit, 每个 .s 占 一行
    return 0 as i32;
}
```

规则:

- **Function-call form only** — 必须带 `()` (no-arg)。`fence_seq_cst` (无括号) = parse error (按未声明 ident → "undefined symbol")
- **No arguments** — `fence_seq_cst(x)` / `fence_seq_cst(a, b)` = parse error: "fence_*() takes no arguments"
- **3 个 builtin 只** — `fence_seq_cst` / `fence_acquire` / `fence_release`。其他 `fence_relaxed` / `fence_acq_rel` 等 = parse error: "unknown fence builtin"
- **Statement-position** — `let x = fence_seq_cst();` = sema error: unit type 不能赋给 i32/具体类型
- **返回值类型** — `unit` (void). 不能作 expr 值使用 (`if (fence_seq_cst()) { ... }` = sema error)

---

## § 3 Semantics

`fence_*()` builtin 出现时编译器执行 side-file pattern (per V3-A no_std + V3-B naked + V3-B inline asm + V3-B link_section 同款):

1. **Parser dispatch** — `parse_expr` IDENT 分支检测 `prev_length == 13` 且 name 在 `{fence_seq_cst, fence_acquire, fence_release}` 集合中,且 next token 是 `(` → dispatch `parse_fence_block`
2. **parse_fence_block** — 校验 no-arg (immediate `)`) → strncmp name → kind (0=seq_cst, 1=acquire, 2=release) → build `NodeBuiltinFence { kind }`
3. **Sema type** — `infer_type` 处理 `NODE_BUILTIN_FENCE` → `type_void(ta)` (unit type). 设 `(*n).type_ptr` 填 unit
4. **Codegen side-file write** — `cg_expr` NODE_BUILTIN_FENCE case:
   - 按 kind 选 mnem: `0 → "mfence"`, `1 → "lfence"`, `2 → "sfence"`
   - `fopen("compiler/build/obj/_fence.buf", "ab")` (binary append, per `feedback_qbe_crlf_root_cause`)
   - 写 `<mnem>\n` (6 bytes for `lfence`/`sfence`/`mfence`)
5. **Post-QBE concat** — `main.jhyy:link_with_gcc` 在 QBE → .s + apply_link_section_directives + inline_asm append 之后,gcc link 之前:
   - `jh_file_stat_ok("_fence.buf") != 0` → 读 binary → append to temp_asm (`fopen("ab")`)
   - `unlink("_fence.buf")` after read (keep next compile clean)
6. **gcc link** — `link_with_gcc` 把 modified temp_asm 传给 gcc, gcc 接受 `mfence`/`lfence`/`sfence` 直接 emit 进 .o

---

## § 4 ABI

`fence_*()` 不改变 jhyy ABI (无 stack / register / struct layout 影响):

- **指令级操作** — `mfence` (x86 全 memory fence, 跨 load/store) / `lfence` (load-only) / `sfence` (store-only)。x86 TSO 模型:mfence 提供 seq_cst;lfence + sfence 配合提供 acquire/release 语义
- **不影响 caller/callee 寄存器** — fence 指令不读 / 不写 GPR,x86 架构无 implicit operands
- **栈对齐** — 不变 (16-byte at call site per standard ABI)
- **不参与 `sret`** — stmt-position,无 return value
- **Cross-thread ordering 范围**:
  - `mfence`: 全序 (all loads + stores 全局 sequential consistency in x86)
  - `lfence`: load-load barrier (后面 load 不重排到前面)
  - `sfence`: store-store barrier (前面 store 不重排到后面)
  - **Within single thread**: 跟 volatile load/store 配合才能保证 reorder-free (per v3.0.3 volatile)
  - **Cross-thread**: 需要 fence + volatile 才完整

---

## § 5 Interaction with Other V3-B Features

`fence_*()` 跟 V3-B 其他 feature 交互:

- **`volatile` (v3.0.3)** — fence 配合 volatile 才跨线程有效。`volatile x = 42; fence_release();` 保证 release fence 之前的 volatile store 对其他 CPU 可见。`fence_acquire(); if volatile_y == 0 { ... }` 保证 acquire fence 之后的 volatile load 看到最新值
- **`#[naked]` (v3.0.2)** — naked fn body 可含 `fence_*()` (跟 asm!() 同 stmt-position)。但更 idiomatic 是直接 `asm!("mfence");` (v3.0.1 inline asm 已 ship)
- **`asm!()` (v3.0.1)** — `fence_seq_cst()` 等价 `asm!("mfence")`,但 fence_* 是 typed builtin,跨 backend (x86 / ARM / RISC-V) 只需改 codegen,user code 不变 (v3.x 中)
- **`#[link_section]` (v3.0.4)** — fence 跟 link_section 无 interaction。两者都进 .s,fence 是 global-scope raw mnem,link_section 只决定 fn 放哪个 ELF section

---

## § 6 Limitations & Out of Scope

- **x86-64 only** — 当前 v3.0.5 emit `mfence` / `lfence` / `sfence` (x86 指令)。ARM (`dmb` / `dsb`) / RISC-V (`fence`) 留 V3-C 或 v3.x 末
- **不支持 `fence_relaxed` / `fence_acq_rel`** — v3.0.5 only 3 个 builtin;C11 memory_order_relaxed + acq_rel 留 v3.x
- **不支持 fence 在 fn 参数位置** — stmt-position only,不能 `fence_seq_cst(x)`,不能 `let y = fence_seq_cst()`
- **不保证 LRC / CLFLUSH 等高级 fence** — 是 CPU-specific 优化 fence, 留 OS kernel
- **不参与 MMIO / device ordering 验证** — 物理 MMIO 行为验证需 OS kernel + 物理设备,jhyy unit test 只能 verify binary emit + exe runs

---

## § 7 Examples

### 7a) 经典 Dekker pattern (x86 TSO)

```jhyy
fn thread_a() {
    x.store(1);
    fence_release();   // sfence
    if y.load() == 0 {
        // critical section
    }
}

fn thread_b() {
    y.store(1);
    fence_release();   // sfence
    if x.load() == 0 {
        // critical section
    }
}
```

### 7b) RCU-like grace period (x86)

```jhyy
fn reader_enter() {
    fence_acquire();   // lfence
    // 之后所有 reads 看到 reader section 之前的 writes
}

fn writer_exit() {
    fence_release();   // sfence
    // 之前所有 writes 对其他 CPU 可见
}
```

### 7c) 编译产物验证 (develop-time dump)

```
$ jhyy compile memory_barrier_smp.jhyy
$ dump temp_asm
.file 1 "memory_barrier_smp.jhyy"
.text
.balign 16
.globl main_jhyy
main_jhyy:
    endbr64
    movl $0, %eax
    ret
mfence
lfence
sfence
mfence
```

### 7d) Ship gate test (V3-B ship required)

[`compiler/tests/examples/memory_barrier_smp.jhyy`](../../compiler/tests/examples/memory_barrier_smp.jhyy):
- 4 个 fence 调用 (seq_cst, acquire, release, seq_cst)
- `fn main_jhyy() -> i32 { ...; return 0 as i32; }`
- 期望 EXIT:0
- 验证手段:temp_asm dump (per develop-time, 移除前 commit), 显 4 行 mnems 在 main_jhyy body 之后

---

## § 8 Changelog 引用

- v3.0.5 (3f memory barrier): ship (per [`docs/logs/v3/changelog-v3.0.md`](../../docs/logs/v3/changelog-v3.0.md))
- D40 wire-format: 不适用
- D41 Debug ABI: 不适用 (无 dbgloc emit 受 fence 影响)
- D42 inline asm (v3.0.1) 已 ship — `asm!("mfence")` 等价 `fence_seq_cst()`
- V3-B 3b `#[naked]` (v3.0.2) 已 ship — naked fn body 可含 fence_*
- V3-B 3c `volatile` (v3.0.3) 已 ship — fence 配合 volatile 才跨线程有效
- V3-B 3e `#[link_section]` (v3.0.4) 已 ship — fence 跟 link_section 无 interaction

---

## § 9 Cross-Axis Note

V2-B (axis-v2 / amd64_sysv backend) 需在 v2.7.0 独立 ship `codegen_amd64_emit_ctrl.jhyy:emit_fence(kind)` stub fill, 以让 sysv ABI 也能产生 `mfence` / `lfence` / `sfence` mnems (v3.0.5 QBE .s post-process path 不依赖 V2-A,V2-A 已 merge;sysv target 测试需 V2-B v2.7.0 ship 后再 verify). Per [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../plans/roadmap/v2-v3-parallel-sprint-plan.md) § 5.1, v2.7.0 ship 后 OS M1 launch 用 sysv ABI 跑 Linux kernel SMP boot, 自然覆盖 fence SysV 行为.

ARM / RISC-V fence 留 v3.x 末 — 需要 emit `dmb` / `dsb` (ARM) 或 `fence` (RISC-V),不依赖 V2-B 额外 ship (per V3-C sprint 设计)

---

**批准后生效**: v3.0.5 ship tag (commit + push per `feedback_auto_push_after_commit`).