# jhyy-lang-spec `#[no_std]` supplement (v3.0.0)

**Status**: SUPPLEMENT (not part of locked [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md))
**Effective**: v3.0.0 ship (V3-A — tag pending, integration verify 后由 coordinator 打)
**Spec baseline reference**: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17.4 + § 17.7
**Plan**: [`docs/plans/v3/batch-V3-A-plan.md`](../plans/v3/batch-V3-A-plan.md)

---

## § 1 Background

[`jhyy-lang-spec-v1.3.0.md` § 17.4](../abis/jhyy-lang-spec-v1.3.0.md) reserves `#[no_std]` outer-attribute syntax (LOCKED in v2.2.0 as 6-feature OS 启动前置 grammar). However [§ 17.7](../abis/jhyy-lang-spec-v1.3.0.md) actively rejects `#[no_std]` at sema stage — that reject is **lifted** by this supplement effective v3.0.0 (V3-A batch).

Spec body 不动(per `feedback_changelog_umbrella` v3.x 锁定纪律);本 supplement 是过渡 doc,v3.x 中 spec bump 时合入主 spec。

---

## § 2 Syntax

Outer attribute at module level (file top, before any `fn` / `type` / `extern` declaration):

```jhyy
#[no_std]
fn main() -> i32 { return 42 as i32; }
```

规则:

- **Outer attribute only** — `#![no_std]` 内层 attribute **不**支持(留 v3.x 中;Rust 习惯写法需改 outer)
- **Module-level only** — `#[no_std]` 出现在 `fn` 函数体内 = compile error
- **One per file** — 同一文件出现多次 `#[no_std]` = compile error
- **组合 attribute 限制** — `#[no_std]` + `#[inline]` 组合可工作(走 inline 旁路 + no_std 旁路并行);`#[no_std]` + `#[naked]` / `#[link_section]` 等其他 outer attr 组合 = out of scope(v3.x 中补)

---

## § 3 Semantics

`#[no_std]` 出现时编译器切换到 **freestanding-soft** 路径:

1. **不链 `compiler/runtime/runtime.c`** — hosted `main_jhyy` bridge 不参与(原 `main_jhyy` 仍可写但不会被 link;无 effect)
2. **Link flag** — `main.jhyy` gcc link line 加 `-nostartfiles -nodefaultlibs`(per gcc manual;MinGW gcc + Linux gcc 均支持;`amd64_win_freestanding` target 验证)
3. **Entry symbol** — entry 改为 `main`(per SysV + MS x64 ELF/PE 约定;**不**是 `main_jhyy`)。`fn main` **必须**定义 — 否则 compile error(sema 校验)
4. **`.note.GNU-stack noalloc` directive** — codegen emit 到 IL(对应 QBE `nobytealloc` 数据段),跳过 stack probing,适合 kernel / 中断 handler 写 stack-protector-free 代码
5. **`no_std_core` stubs**(由编译器 link 时隐式提供,user 不可见):
   - `panic_handler() -> ()` — `loop {}` 无限循环(M0 stub;panic message 打印留 v3.x 中)
   - `memcpy(dst, src, n) -> dst` — per-byte loop(SSE/AVX 优化留 v3.x 中)
   - `memset(dst, val, n) -> dst` — per-byte loop
   - `__start_kernel() -> i32` — entry wrapper,调 user `fn main()` 后返回 exit code

User `fn main` 返回值语义保持(hosted 跟 freestanding 一致:`-> i32` exit code)。

---

## § 4 Example

最小 ship gate test:

```jhyy
#[no_std]
fn main() -> i32 {
    return 42 as i32;
}
```

Compile + run(held 路径 = `jhyy run`):

```bash
jhyy run compiler/tests/examples/no_std_hello.jhyy
# expected: exit code 42
```

Kernel target(`target=amd64_win_freestanding`,per v2.4.0 multi-target dispatcher):

```bash
jhyy compile --target=amd64_win_freestanding compiler/tests/examples/no_std_hello.jhyy -o kernel.efi
# expected: kernel.efi 编出(0 runtime dep,只 link jhyy 自带 no_std_core)
```

---

## § 5 Out of scope (v3.0.0)

- `#![no_std]` inner attribute(留 v3.x 中)
- `panic_handler` panic message 打印(M0 stub only)
- `memcpy` / `memset` SIMD 优化(留 v3.x 中)
- `#[no_std]` + `#[naked]` / `#[link_section]` / `#[inline]` 组合的特殊规则
- 自定义 entry point(目前 hardcoded `main`;`#[entry = "..."]` 留 v3.x 中)
- `&mut` / lifetime 跟 `#[no_std]` 集成(V3-C 3g/3g.5/3g.7)
- OS-specific entry(`_start` / `efi_main` / 等等)— `#[no_std]` 默认 `main`;OS-side 特定 entry 走 v2.3.0 已 ship 的 `target=amd64_win_freestanding` + 手动 entry 函数

---

## § 6 软 ship 边界

per **D10**(coordination.md § 3 锁):`#[no_std]` 是 OS kernel 编写者的**便利特性**,不是 M1 launch 的**硬前置**。

- M1 launch 启动条件 = v2.0 阶段 ship ✅ + v3.0 3a/3b/3c/3e/3f 全 ship;**3d (no_std) 软 ship** = 观察 1-2 sprint 后视稳定情况决定是否进 next spec bump
- 若 v3.0.0 ship 后发现在 cross-compile / PE-COFF .efi link 链有稳定性问题,允许 patch 版本(v3.0.1 / v3.0.2 等)继续在 umbrella changelog 内累计;**不**升 semver major

---

## § 7 Cross-references

- Spec 锁: [`jhyy-lang-spec-v1.3.0.md` § 17.4](../abis/jhyy-lang-spec-v1.3.0.md) — 语法草案(LOCKED);[`§ 17.7`](../abis/jhyy-lang-spec-v1.3.0.md) — v2.0 期间 sema 拒绝路径(本 supplement lift)
- ABI 锁: [`jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) § 13 — freestanding ABI 约定(LOCKED)
- Plan: [`docs/plans/v3/batch-V3-A-plan.md`](../plans/v3/batch-V3-A-plan.md) — V3-A batch 完整 scope
- 关联 batch: [`batch-V3-B-plan.md`](../plans/v3/batch-V3-B-plan.md)(v3.0.1 → v3.0.5 = M1-required 5 件套:3a/3b/3c/3e/3f)+ [`batch-V3-C-plan.md`](../plans/v3/batch-V3-C-plan.md)(v3.1.0 → v3.1.2 = 3g/3g.5/3g.7)
- v2.3.0 freestanding E2E: `hello-freestanding.efi` 5/5 PASS on OVMF(per [`docs/logs/v2/changelog-v2.3.0.md`](../logs/v2/changelog-v2.3.0.md))— 走 target-level freestanding mechanism,**不**走 `#[no_std]`。两者 complementary:target 给 OS boot,no_std 给语言层 runtime cut
- v2.4.0 multi-target dispatcher: 提供 `target=amd64_win_freestanding`(本 supplement `#[no_std]` build 依赖该 target)
- 跨项目 OS 时间线: [`../../../jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md)