# jhyy-lang-spec `volatile` supplement (v3.0.3)

**Status**: SUPPLEMENT (not part of locked [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md))
**Effective**: v3.0.3 ship (V3-B 3c — sub-sprint of `docs/plans/v3/batch-V3-B-plan.md`)
**Spec baseline reference**: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17.4 (outer-attribute reservation pattern; volatile keyword 在 § 17.6 旧 stub)
**Plan**: [`docs/plans/v3/batch-V3-B-plan.md`](../plans/v3/batch-V3-B-plan.md) § 3c

---

## § 1 Background

jhyy v1.3.0 主 spec 未包含 `volatile` type qualifier。OS kernel / driver 编写需要 volatile 来:
1. 访问 memory-mapped I/O (MMIO) 寄存器 — 不允许寄存器缓存(每次 access 必须 hit mem)
2. 多线程共享内存(同一 thread 内)— 不允许 reordering within single thread

C / Rust 都有 volatile;jhyy 之前缺这个,OS-side D2 region types primary 跟 volatile 语义绑死(per
[`../jhyy_OS/docs/v0.0.2-foundation-revision.md § 4`](../jhyy_OS/docs/v0.0.2-foundation-revision.md)),
所以 3c 是 v3.x batch **M1-required**(per `coordination.md § 3 D8` — M1 launch 强前置 v3.0 3a/3b/3c/3e/3f)。

Spec body 不动(per `feedback_changelog_umbrella` v3.x 锁定纪律);本 supplement 是过渡 doc,v3.x 中 spec
bump 时合入主 spec。

---

## § 2 Syntax

`volatile` 是 **type qualifier prefix**,仅作用于 primitive type:

```jhyy
let mut mmio: volatile i32 = 0 as i32;
let a: i32 = mmio;   // volatile load — no regalloc, no reorder within thread
let b: i32 = mmio;   // 2nd volatile load — must re-read memory
mmio = 42;           // volatile store
```

`volatile` 出现位置:紧跟 `:` 在 type annotation 内,在 primitive type ident 前:

```jhyy
let x: volatile i32;            // OK
let y: volatile i64 = 100;       // OK
let z: volatile bool = true;     // OK
let p: volatile f64;             // OK (f64 也算 primitive)
```

错误用法(parser 阶段拒掉 + sema 阶段兜底):

```jhyy
let s: volatile MyStruct;       // ERROR:struct 不能 volatile (spec § 6 限制)
let p: volatile *i32;           // ERROR:pointer 不能 volatile
let a: volatile [i32; 4];       // ERROR:array 不能 volatile
let v: volatile volatile i32;   // ERROR:chained rejected
```

---

## § 3 Semantics

### § 3.1 内存语义

`volatile T` 修饰的 type 在 jhyy 中语义(per ISO C volatile 跟 Rust volatile 借鉴):

1. **每次 load 必须从内存读** — 不允许寄存器缓存(load 跨 statement 不复用前次 load 的值)
2. **每次 store 必须写到内存** — 不允许 store buffer 推迟 / 合并
3. **single thread 内 no reordering** — volatile load/store 跨其他语句不交换顺序
4. **cross-thread ordering 不保证** — 需要 `fence_*` 系列(那是 3f memory barrier sub-sprint 的职责,
   留 v3.x M1 后续 sprint 实现)

### § 3.2 codegen 主路径(QBE-based)

codegen 主路径走 `jhyy.exe compile → qbe.exe → .s`(per `docs/internal/build.md`)。QBE 本身**不识别**
`volatile` keyword。jhyy 通过以下机制保证 "no regalloc reuse" 尽可能:

1. **每次 cg_expr NODE_IDENT 都 alloc fresh temp** — QBE 不能 fold 不同 temp 的 load 到同一 register
2. **emit `# volatile load` / `# volatile store` 注释** 在 .il 输出 — grep verify + 文档化
3. **cg_emit_load / cg_emit_store_primitive 检查 type.is_volatile=1 后 emit 注释**

**已知 limitation**:QBE 的 `load.c` / `gvn.c` pass 仍会做 constant propagation + register promotion。
对于"初始值是 compile-time constant"的 volatile 变量,QBE 会消除 load(用 constant 替换) — 这违反
ISO C volatile 语义。**Workaround**:初值用 opaque function call(如 `read_sensor()`)防止 constant fold。
本 ship gate test `volatile_mmio.jhyy` 用此 pattern(opaque `read_sensor()` 提供初值)。

### § 3.3 V2-A 路径(codegen_amd64.jhyy direct emit)

V2-A 路径(V2-A = `codegen_amd64.jhyy` 系列)是 self-hosting 时的 fallback codegen,直接 emit `.s`
不走 QBE。该路径下 volatile 语义**严格强制**:

1. `emit_volatile(state, tok)` 识别 `QBE_VOLATILE_MARKER = -1`(per `codegen_amd64_state.jhyy:34`)
2. 后续 `emit_load` / `emit_store` 已经走 "movl mem, %reg" + "movl %reg, mem" direct mem op 路径
3. **不**emit `mfence` / `lock; addq $0, (%rsp)` — 那是 3f 职责,不是 3c

V2-A `emit_volatile` 在 v3.0.3 之前是 stub (per `codegen_amd64_emit_call.jhyy:471`)。v3.0.3 ship 后
填 body 为 "no regalloc + no barrier"(per L4 § X.2 + decision D-v3.0.3-1)。

---

## § 4 ABI 影响

`volatile T` 不改变 ABI:

- **Layout** — `volatile i32` 在 stack / global / struct field 内布局**跟 `i32` 一致**(4 字节, 4 字节对齐)
- **Calling convention** — 通过寄存器传 `volatile i32` 参数时,callee 收到的是值(caller 已经 load 完),
  callee 不再做 volatile load(因为 value 已经在 register 里)
- **Function param** — `volatile` 参数允许,但没额外语义(codegen 在 caller side 已读)
- **MMIO region** — OS side 把 volatile 变量绑到 physical address(per jhyy_OS D2 region types primary)

---

## § 5 Implementation

### § 5.1 改动清单

| 文件 | 改动 |
|------|------|
| `compiler/src0/types.jhyy` | Type struct 加 `is_volatile: i32` 字段 + `_pad_volatile: i32`;TYPE_SIZE 152→160 |
| `compiler/src0/ast.jhyy` | NODE_VOLATILE_TYPE = 52 + NodeVolatileType struct (`inner: *u8`) + ctor/accessor |
| `compiler/src0/lexer.jhyy` | TOKEN_VOLATILE = 72 + lookup_keyword 加 "volatile" + token_kind_name |
| `compiler/src0/parser.jhyy` | parse_type 加 volatile prefix 分支;reject chained / compound / non-primitive |
| `compiler/src0/sema.jhyy` | resolve_type_node 处理 NODE_VOLATILE_TYPE → 分配 new Type + is_volatile=1;infer_type fallback;check_func_decl allow volatile param |
| `compiler/src0/codegen.jhyy` | cg_emit_load / cg_emit_store_primitive 检查 is_volatile → emit `# volatile load/store` 注释 |
| `compiler/src0/codegen_amd64_emit_call.jhyy` | emit_volatile stub 填 body 为 "no regalloc + no barrier" |
| `compiler/tests/examples/volatile_mmio.jhyy` | ship gate smoke test(EXIT: 0) |
| `docs/logs/v3/changelog-v3.0.md` | V3-B v3.0.3 entry |

### § 5.2 验证

- [x] Build: `make` 零 warning
- [x] `jhyy.exe compile volatile_mmio.jhyy -o vol_test.exe` 成功
- [x] `vol_test.exe` EXIT: 0(基本 codegen 路径 smoke test)
- [x] `.il` 含 `# volatile load` / `# volatile store` 注释(grep verify)
- [ ] **NOT verified**:QBE main 路径下 volatile semantic 完全正确(per § 3.2 limitation;需要 OS-level kernel + 物理 MMIO 验证)
- [ ] **NOT verified**:V2-A path emit_volatile 严格行为 — V2-A 路径是 self-hosting 测试边界,本 sprint 不跑 jhyy_selfhost_check

---

## § 6 限制 (v3.0.3)

- **Primitive types only** — `volatile T` 仅允许 T 是 primitive(i8/i16/i32/i64/u8/u16/u32/u64/f32/f64/bool)
  。compound types(struct / pointer / array / slice / function)在 parser 阶段被 reject,sema 阶段兜底。
- **No chained** — `volatile volatile T` parser 阶段 reject(只一个 volatile prefix)。
- **No cross-thread ordering** — `volatile` 在 single thread 内保证 no-reordering;多线程需要
  `fence_*` 系列(3f sub-sprint 实现,不在本 sprint)。
- **QBE main path has known limitation** — QBE 不识别 volatile;load.c / gvn.c 会做 register promotion
  (per § 3.2)。初值必须 opaque 才能保证 .s 含独立 movl 指令。
- **Function params allowed without extra semantics** — `fn f(x: volatile i32)` 是合法的常见 MMIO callback
  模式,但 callee 收到的 x 是值(caller 已经在 volatile load 后传寄存器)。

Out of scope (本 batch 不做):
- Volatile bitfields
- Volatile pointer 写(MMIO device register 的 deref 写需要 volatile pointer,留 v3.x 中)
- `fence_*` 系列(cross-thread ordering)— 3f sub-sprint
- `#![volatile]` inner attribute
- `volatile` 在 const context(const 上下文里 volatile 不允许 — 跟 Rust 一致)
- `volatile` array / slice 元素

---

## § 7 示例

### § 7.1 MMIO read(OS kernel 写法)

```jhyy
// 假定 MMIO 物理地址 0xFEE00000(UART)被 bind 到 volatile global
// (OS-side D2 region types primary + volatile type 双 spec 配合)

let mut uart_data: volatile i32 = 0 as i32;
// ... OS setup 把 uart_data 绑到 0xFEE00000 ...

// MMIO read — 必须 hit mem,不允许寄存器缓存
let c: i32 = uart_data;

// MMIO write — 必须 hit mem
uart_data = 65 as i32;  // 'A' = 65
```

### § 7.2 Ship gate test

```jhyy
// 期望 EXIT: 0
fn read_sensor() -> i32 { return 42 as i32; }
fn write_log(v: i32) -> i32 { return v; }

fn main_jhyy() -> i32 {
    let mut x: volatile i32 = read_sensor();
    let a: i32 = x;
    let _h1 = write_log(a);
    x = read_sensor();
    let b: i32 = x;
    let _h2 = write_log(b);
    if a == 42 && b == 42 { return 0 as i32; }
    return 1 as i32;
}
```

---

## § 8 Cross-references

- Spec 锁: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17.4 (outer attr reservation)
- ABI 锁: [`jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) § 13 (freestanding + calling convention)
- Plan: [`docs/plans/v3/batch-V3-B-plan.md`](../plans/v3/batch-V3-B-plan.md) § 3c
- D2 region types primary: [`../jhyy_OS/docs/v0.0.2-foundation-revision.md § 4`](../jhyy_OS/docs/v0.0.2-foundation-revision.md)
- 关联 batch: V3-A `no_std` (v3.0.0) + V3-B `inline asm` (v3.0.1) + V3-B `#[naked]` (v3.0.2) +
  V3-B `#[link_section]` (v3.0.4) + V3-B memory barrier (v3.0.5)
- v2.x V2-A codegen_amd64 design: [`docs/internal/architecture.md`](../internal/architecture.md) § V2-A
- D43 baseline: `51376ce5721bccb0c81c7deabead1a6012fb76648c424238391018f1890b5761` (per v2.4.0 ship `7fb735b`)