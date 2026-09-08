# jhyy-lang-spec `#[link_section]` supplement (v3.0.4)

**Status**: SUPPLEMENT (not part of locked [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md))
**Effective**: v3.0.4 ship (V3-B Phase B Step 2 — 3e `#[link_section]`)
**Spec baseline reference**: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17.6
**Plan**: [`docs/plans/v3/iterative-imagining-thunder.md`](../plans/v3/iterative-imagining-thunder.md)

---

## § 1 Background

[`jhyy-lang-spec-v1.3.0.md` § 17.6](../abis/jhyy-lang-spec-v1.3.0.md) reserves the `#[link_section("name")]` outer-attribute grammar (LOCKED in v2.2.0 as part of the 6-feature OS 启动前置 grammar). However the codegen / sema implementation has been **D42-stubbed** through V2.x — only the AST field (`link_section: *u8` on `NodeFuncDecl`) and the parser `pending_link_section` slot exist; no `.section <name>` directive was emitted to the .s.

This supplement specifies the v3.0.4 semantics: codegen writes a `<mangled_name>|<section_name>\n` side-file per non-naked function carrying `#[link_section]`, and `main.jhyy`'s post-QBE-pass walker reads that side-file and walks the .s, inserting a `.section <name>\n` directive before the `.balign 16\n.globl <name>\n` triple for each matched function.

Spec body 不动 (per `feedback_changelog_umbrella` v3.x 锁定纪律);本 supplement 是过渡 doc, v3.x 中 spec bump 时合入主 spec。

---

## § 2 Syntax

Outer attribute at function declaration, taking a parenthesized string literal argument naming the ELF section:

```jhyy
#[link_section(".text.boot")]
fn _start() -> i32 {
    return 42 as i32;
}

#[link_section(".text.irq")]
fn irq_entry() {
    asm!("iret");
}

fn main_jhyy() -> i32 {
    let _x: i32 = _start();
    return 0 as i32;
}
```

规则:

- **Function-level only** — `#[link_section("...")]` on `extern` decl / struct / type alias / static var = compile error
- **必须接 `fn`** — 紧跟 `fn <ident>(...) <ret>` declaration (no parens between attr and `fn`)
- **必须 parenthesized string literal** — `#[link_section]` (no arg) / `#[link_section(.text.boot)]` (no parens) / `#[link_section("name", "alias")]` (multi arg) = parse error
- **String literal 必须 quoted** — `#[link_section(.text.boot)]` (= bare ident) = parse error, expect `"..."`
- **Section name 限制** — printable ASCII 0x21..0x7E only (no space / tab / NL / CR / NUL / DEL / non-ASCII / quote). 详见 § 3
- **Naked fn 限定** — `#[naked]` + `#[link_section]` 组合 = out of scope (v3.x 中补); naked fn 不通过 QBE .s emit, link_section walker 跳过 naked fn。Per § 5
- **每 module 任意多个 `#[link_section]`** — 没有 per-file 1 个的限制。多个 fn 共享同一 section 名 = linker 合并(语义等价)

---

## § 3 Semantics

`#[link_section("name")]` 出现时编译器执行 side-file pattern (per V3-A no_std + V3-B naked 同款):

1. **Parser stash** — `parse_attributes` 命中 `link_section` 关键字时, dup 字符串 token (去引号) 进 arena, stashed 到 `(*p).pending_link_section`。`parse_func` 读 `pending_link_section` 传给 `ast_new_func_decl` fold 到 `NodeFuncDecl.link_section` 字段。reset pending = 0 after fold
2. **Sema validate** — `check_link_section_name` (defined BEFORE `check_func_decl` per jhyy no-forward-decl 规则) 校验:
   - empty / NULL → error: `link_section name is empty`
   - byte < 0x21 → error: `link_section name contains non-printable byte`
   - byte > 0x7E → error: `link_section name contains non-ASCII byte`
3. **Codegen side-file write** — `cg_module` Pass B 打开 `compiler/build/obj/_section_directive.buf` (binary mode, per `feedback_qbe_crlf_root_cause`). 遍历每个 non-naked `NODE_FUNC_DECL`,若 `link_section != NULL`,写 `<mangled_name>|<section_name>\n` (fwrite binary, no CRLF). Naked fn skip (走 `_inline_asm.buf`, 不进 QBE .s)
4. **Post-QBE .s walk** — `main.jhyy:apply_link_section_directives(temp_asm)` 在 QBE → .s 后、`link_with_gcc` 前执行:
   - 若 `_section_directive.buf` 不存在 (无 link_section fn), no-op return
   - read side-file → parse 32×128 name/section arrays (cap 32 entries)
   - read temp_asm into 1MB buffer
   - line-walk with 2-line sliding window, 检测 `.text\n.balign 16\n.globl <name>\n` pattern, 若 `<name>` match 任何 side-file entry, replace `.text\n` with `.section <name>\n`, 跳过 prev_prev (`.text`), emit prev (`balign`) + current (`globl`)
   - CRLF-aware line_len 计算 (per `feedback_qbe_crlf_root_cause`:Windows QBE .s 是 \r\n,line walker 必须 detect trailing `\r` 在 `line_len - 2` 位置)
5. **gcc link** — 后续 `link_with_gcc` 把 modified temp_asm + `_inline_asm.buf` concat 后传 gcc. gcc 接受 `.section <name>` directive 直接 emit 到 .o

---

## § 4 ABI

`#[link_section]` 不改变 jhyy ABI (调用约定 / struct pass-by-value / 寄存器使用都同标准 fn):

- **Function symbol 仍在 symbol table** — `.globl <mangled>` 由 QBE emit (per V3-A naked + V3-B inline_asm path 同), `.section` directive 只决定 .o 输出 section
- **Caller 调用透明** — 普通 fn call site (`callq _start`) 不变, linker 在 link 阶段 resolve cross-section reference
- **多 fn 共 section** — `#[link_section(".text.boot")]` 在 fn A + fn B 都出现, linker 合并 (默认 `.text` aggregator; Linux ELF / SysV ABI 各自 section aggregation 规则由 linker 决定)
- **Windows MinGW 行为** — MinGW linker (PE/COFF backend) 把 `.text.*` 合并进 `.text` final section (Windows PE section semantics). Compiler 仍 emit `.section .text.boot`; linker 最终 merge. 在 OS M1 launch 用 SysV / Linux target 下, section preserved verbatim
- **Callee-saved 寄存器** — 标准 ABI 同, 无 special override
- **栈对齐** — 同标准 fn (16-byte at call site)
- **不参与 `sret`** — naked 限定外, 同标准 fn sret ABI

---

## § 5 Interaction with Other V3-B Features

`#[link_section]` 跟 V3-B 其他 feature 交互:

- **`#[naked]` (v3.0.2)** — naked fn 不走 QBE .s emit (走 `_inline_asm.buf` side-file concat). `apply_link_section_directives` 跳过 naked fn (cg_module Pass B 写 side-file 时 skip naked). 若 user 同时声明 `#[naked]` + `#[link_section]`, parser / sema 不报错, codegen skip 两者 → linker 仍把 naked fn emit 到 default `.text` section. 真正支持需 v3.x 中改 `_inline_asm.buf` 路径加 `.section <name>` header
- **`#[inline]` (v0.4)** — `#[inline]` 跟 `#[link_section]` 可同声明. inline fn 也写 side-file entry; linker 处理 inline body 跨 fn 共享 section (per-target 行为)
- **`asm!()` (v3.0.1)** — `#[link_section]` fn body 可含 `asm!(...)`. 普通 fn codegen 仍 emit QBE IL + asm side-file concat, link_section directive 写在 fn symbol 之前, 影响整 fn

---

## § 6 Limitations & Out of Scope

- **不支持 `#[link_section]` 在 static var / global 上** — v3.0.4 仅 fn decl. Module-level `#[link_section]` 跟 static var 留 v3.x
- **不支持 naked fn `#[link_section]`** — 详 § 5
- **不支持 ARM / RISC-V linker section aggregation 验证** — v3.0.4 x86-64 only (Windows MinGW / Linux SysV). ARM `.section .text.boot, "ax"` / RISC-V `.section .text.boot` 留 v3.x 末 (与 V2-A amd64_sysv ship 时同时)
- **不支持 Windows section group `$text` 优化** — MSVC `/merge:.text=.text0` 等 Windows-specific section 优化留给 link-time, v3.0.4 emit raw `.section`
- **不支持 `.pushsection` / `.popsection` 多 section stack** — 单次 `.section` directive only. 嵌套 section 留 v3.x
- **不支持 section flag 后缀** — `.section .text.boot,"ax",@progbits` 仅 first part. flag 后缀留 v3.x

---

## § 7 Examples

### 7a) OS boot entry (典型用例)

```jhyy
#[link_section(".text.boot")]
fn _start() -> i32 {
    // UEFI/Linux kernel entry — 必须在 .text.boot section 让 bootloader pick
    return 42 as i32;
}

fn main_jhyy() -> i32 {
    let _x: i32 = _start();
    return 0 as i32;
}
```

### 7b) 编译产物验证 (Windows MinGW)

```
$ grep -A2 "_start:" build/out.s
.section .text.boot          ← 编译器 emit
.balign 16
.globl _start
_start:
    endbr64
    movl $42, %eax
    ret

$ readelf -S build/main_jhyy.exe | grep "\.text"   # MinGW 合并 .text.* 进 .text
.text PROGBITS 0x140001000 ...
```

### 7c) 编译产物验证 (Linux SysV, V2-B 后续 ship)

```
$ readelf -S build/main_jhyy.elf | grep "\.text"
.text           PROGBITS ...
.text.boot      PROGBITS ...    ← V2-B sysv ABI preserved
.text.startup   PROGBITS ...
```

### 7d) Ship gate test (V3-B ship required)

[`compiler/tests/examples/link_section_boot.jhyy`](../../compiler/tests/examples/link_section_boot.jhyy):
- `#[link_section(".text.boot")] fn _start() -> i32 { return 42 as i32; }`
- `fn main_jhyy() -> i32 { let _x: i32 = _start(); return 0 as i32; }`
- 期望 EXIT:0 (`main_jhyy` 返回 0; `_start` 返回 42 丢弃)
- 验证手段:temp_asm dump (per develop-time, 移除前 commit), 显 `.section .text.boot` 在 `_start` symbol 之前

---

## § 8 Changelog 引用

- v3.0.4 (3e `#[link_section]`): ship (per [`docs/logs/v3/changelog-v3.0.md`](../../docs/logs/v3/changelog-v3.0.md))
- D40 wire-format: 不适用
- D41 Debug ABI: 不适用 (无 dbgloc emit 受 link_section 影响)
- D42 inline asm (v3.0.1) 已 ship — naked fn body 可含 `asm!()`
- V3-B 3b `#[naked]` (v3.0.2) 已 ship — naked fn 与 link_section 组合 deferred (见 § 5)

---

## § 9 Cross-Axis Note

V2-B (axis-v2 / amd64_sysv backend) 需在 v2.7.0 独立 ship `codegen_amd64_emit_ctrl.jhyy:emit_section(name)` stub fill (per V3-B plan § "Step 4 Phase B Step 2 备注"), 以让 sysv ABI 也能产生 `.section <name>` directive. 当前 v3.0.4 QBE .s post-process path 不依赖 V2-A (V3-B Phase B ship 时 V2-A 已 merge), 但 sysv target 测试需 V2-B v2.7.0 ship 后再 verify. Per [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](../plans/roadmap/v2-v3-parallel-sprint-plan.md) § 5.1, v2.7.0 ship 后 OS M1 launch 用 sysv ABI 跑 Linux kernel boot, 自然覆盖 link_section SysV 行为.

---

**批准后生效**: v3.0.4 ship tag (commit + push per `feedback_auto_push_after_commit`).