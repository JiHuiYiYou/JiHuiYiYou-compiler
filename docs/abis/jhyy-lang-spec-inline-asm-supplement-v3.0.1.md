# jhyy-lang-spec `asm!` inline asm supplement (v3.0.1)

**Status**: SUPPLEMENT (not part of locked [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md))
**Effective**: v3.0.1 ship (V3-B sub-sprint 3a — 单元 A1)
**Spec baseline reference**: [`jhyy-lang-spec-v1.3.0.md`](../abis/jhyy-lang-spec-v1.3.0.md) § 17 (compiler-side language extensions)
**Decision authority**: D42 ([`docs/plans/v2/v2.0.0-os-prep.md`](../plans/v2/v2.0.0-os-prep.md))

---

## § 1 范围 (Scope)

本 supplement 为 jhyy 语言新增 `asm!(...)` 内联汇编宏(form: `asm!("...")`),允许在 jhyy 源码中直接写 x86-64 汇编指令。设计目标:

- 给 OS kernel 编写者(以及性能敏感的 hosted 代码)一个低层 escape hatch
- 不引入新 parser/comptime complexity (走 macro-like 语法,无 operands / 无 templates)
- 走 D42 决议的 QBE .s passthrough 路径:codegen 不 emit QBE IL,直接把 asm 文本 append 到 .s 文件末尾供 gcc 汇编

**硬约束(per `jhyy_OS/docs/coordination.md` D42)**:

> v3.0 3a inline asm 在 v2.x 自写后端完成前走 QBE 工具链 .s 输出路径;v2.x 完成后 asm 走自写后端 'escape hatch' 路径

v3.0.1 走 QBE .s passthrough(V2-A 阶段 backend 仍是 stub)。V2-B 自写 backend 完成后切到 escape hatch 路径(V2-B 改 codegen_amd64_emit_raw_asm 实 impl,V3-B v3.0.1 已填该 stub)。

---

## § 2 语法 (Syntax)

```jhyy
asm!("string-literal");
```

完整语法:

```
AsmExpr ::= "asm" "!" "(" StringLiteral ")" ";"
```

规则:

- **`asm` 标识符必须是小写** — 与 Rust `asm!` macro 风格对齐;jhyy 不区分大小写,但 `ASM!` / `Asm!` 等变体 **不** 触发特殊处理(走 IDENT 分支,fallthrough 到 sema/codegen 的常规 ident 路径 → undefined symbol error)
- **`!` 紧跟 `asm`,中间无空白** — lexer 把 `asm` 跟 `!` 拆成两个 token,parser 在 IDENT 分支用 2-token lookahead (`prev_length==3 && strncmp(prev_start, "asm", 3)==0 && peek(TOKEN_BANG)`) 检测
- **单一 string literal** — v3.0.1 只接受 1 个 string literal 参数;`asm!("a", "b")` 或 `asm!(42)` = compile error(`error: asm!(...) operands are not supported in v3.0.1`)
- **末尾 `;` 必须** — asm! 是 statement-position expr,跟其他 expr-stmt 一致需要 `;` 终止(`{ }` 块末尾可省)
- **stmt-position only** — `let x = asm!("...");` = compile error(sema 报 unit type mismatch)

**示例**:

```jhyy
fn main_jhyy() -> i32 {
    asm!("nop");             // OK,语句位置
    asm!("cpuid");           // OK,语句位置
    // asm!("mov %eax, %ebx"); // OK,可用任何 AT&T 语法 x86-64 指令
    return 0 as i32;
}
```

---

## § 3 语义 (Semantics)

`asm!("text")` 在 codegen 阶段产生 **零 QBE IL 输出**,而把 `text\n` 直接 append 到 `compiler/build/obj/_inline_asm.buf` (side-file, fopen "ab" 二进制模式 — per `feedback_qbe_crlf_root_cause`)。`main.jhyy link_with_gcc` 在 gcc 链接之前:

1. `jh_file_stat_ok(_inline_asm.buf)` 检查存在
2. 若存在:`fopen("rb")` 读全部内容 → `fwrite` 到 `temp_asm` (`.s` 文件,同样 "ab" 二进制)
3. `jh_unlink_file` 删除 side-file(下次 compile 起点干净)

最终 .s 文件 = QBE 生成的 IL emit + asm 文本 appended。gcc 汇编整个 .s,asm 文本作为 global-scope 汇编指令被组装进 `.exe` (or `.efi` per target)。

**类型**(sema):

- `asm!("text")` type = `unit ()`
- 不能出现在 expression-position (除 statement 外)

**寄存器 / 内存副作用**:

- v3.0.1 不 emit clobber 声明 / 不 emit register 分配 / 不 emit memory barrier
- **完全由 user 负责** 知道 asm 指令的副作用(例如 `cpuid` clobbers `eax/ebx/ecx/edx`)
- v3.1+ 加 operand constraints 时会引入 `in(reg) out(reg) clobber("eax")` 风格的 constraint list(per spec supplement 跟进)

---

## § 4 ABI 影响 (ABI)

无。

- asm 文本作为 .text 段(global-scope)汇编指令,不影响函数调用约定(struct pass-by-value / sret / AMD64 SysV 寄存器分配都不变)
- 没有引入新的 primitive type / 类型布局 / 寄存器约定
- 不修改 [`jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) 主 spec — 本 supplement 是 transparent addition

---

## § 5 实现 (Implementation) — D42 path

### Codegen 路径

**文件**: `compiler/src0/codegen.jhyy`

`cg_expr` 新增 `case NODE_ASM_BLOCK:` 分支(line ~3499):

```jhyy
let ad = node_asm_block_data(n);
let asm_buf_path = "compiler/build/obj/_inline_asm.buf" as *u8;
let afp = fopen(asm_buf_path, "ab" as *u8);
if afp != (0 as *u8) {
    let text_len = strlen((*ad).text);
    let _w1 = fwrite((*ad).text, 1 as i64, text_len, afp);
    let nl = "\n" as *u8;
    let _w2 = fwrite(nl, 1 as i64, 1 as i64, afp);
    let _c = fclose(afp);
}
return zero;  // asm is stmt-position; zero IRVal discarded
```

**关键点**:

- `fopen "ab"` (append binary) — **不** 用 "a" (per `feedback_qbe_crlf_root_cause`:Windows fopen "a" 会把 `\n` 转 `\r\n`,破坏 asm 指令格式)
- **不 emit QBE IL** — return zero IRVal,正常 Pratt loop / 后续 codegen 不感知 asm block
- **多次调用累积** — 同一文件多个 `asm!()` block 顺序追加 (vs 同时序, vs function 序)

### V2-A escape hatch path

**文件**: `compiler/src0/codegen_amd64.jhyy`

`codegen_amd64_emit_raw_asm` stub(V2-A 已 ship 签名,空 body)。V3-B v3.0.1 填 body:跟 cg_expr 同样 side-file append 实现。两条路径 (QBE .il emit + V2-A 自写后端) 行为一致 — user source 透明。

### main.jhyy 拼接路径

**文件**: `compiler/src0/main.jhyy` (line 865+)

`link_with_gcc` 在 `jh_file_copy(asm_path, temp_asm)` **之后**,gcc 链接 cmd 拼接 **之前**,做 side-file 读取 + 追加:

```jhyy
let inline_asm_path = "compiler/build/obj/_inline_asm.buf" as *u8;
if jh_file_stat_ok(inline_asm_path) != (0 as i32) {
    let ia_fp = fopen(inline_asm_path, "rb" as *u8);
    if ia_fp != (0 as *u8) {
        let ia_buf = malloc(65536 as i64);
        let ia_n = fread(ia_buf, 1 as i64, 65536 as i64, ia_fp);
        let _fc1 = fclose(ia_fp);
        if ia_n > (0 as i64) {
            let asm_fp = fopen(temp_asm, "ab" as *u8);
            if asm_fp != (0 as *u8) {
                let _w = fwrite(ia_buf, 1 as i64, ia_n, asm_fp);
                let _fc2 = fclose(asm_fp);
            }
        }
        free(ia_buf);
        let _u2 = jh_unlink_file(inline_asm_path);
    }
}
```

---

## § 6 限制 (Limitations)

| 限制 | v3.0.1 | v3.1+ (planned) |
|------|--------|------------------|
| Operand constraints | ❌ 不支持(单一 string literal only) | ✅ `asm!("mov {0}, {1}", in(reg) x, out(reg) y)` style |
| 模板字符串 | ❌ `{0}` `{1}` 占位符 not supported | ✅ operands 替代 |
| Inline placement (函数体内) | ❌ appended 到 .s 末 (global scope) | ✅ 占位符 + placement tracking |
| Register clobber declarations | ❌ 不 emit(完全 user 责任) | ✅ `clobber("eax", "ebx", ...)` 自动 emit |
| Memory barrier | ❌ 不 emit | ✅ `memory` 选项 + arch-specific mfence/sfence |
| Multi-line asm | ✅ 支持(text 内可含 `\n`) | ✅ |
| x86-64 AT&T syntax | ✅ | ✅ |
| x86 Intel syntax | ❌ (assume AT&T) | ✅ 切换选项 (留 v3.x 中) |
| ARM64 / RISC-V | ❌ (x86-64 only) | ✅ per-target dialect (留 v3.x 中) |
| Module-level asm! | ❌ (只能函数体内) | ✅ per module directive (留 v3.x 中) |
| 嵌套 `asm!(...)` 内 `asm!` | ❌ | ❌ (留 v3.x 中) |

**Inline placement 限制**(最关键):

由于 codegen 不 emit QBE IL,asm 文本只能 append 到 .s 末。这意味着:

- `asm!("cpuid")` 出现在 `main_jhyy` 函数体内 → codegen 不在函数体 emit `cpuid` 指令;cpuid 被 append 到 .s 末
- gcc 链接时把 cpuid 视为 global-scope 汇编指令 → 排在 `main_jhyy` 的 `ret` 之后
- **运行时行为**:cpuid 在 `main_jhyy` 返回后才执行 → 不能影响 main 的 exit code 或函数内变量
- **典型用例**:定义 global 符号 (`.global _my_marker`)、初始化全局数据、修改 BSS(实际不工作但 asm 可写)、在 entry point 之前 hook

要 inline 调用 asm (在函数体里实际执行),需要 v3.1+ 加 operand constraints + placement tracking。

**当前 ship gate 用例**(per 测试 `compiler/tests/examples/inline_asm_cpuid.jhyy`):

只验证 asm 文本被 append 到 .s 并出现在最终 .exe (objdump 可查 `0f a2` cpuid 字节在 `main_jhyy ret` 紧后),不验证 inline 运行时行为。

---

## § 7 示例 (Examples)

### 示例 1: cpuid 验证(asm 出现在 .exe,inline 不执行)

```jhyy
fn main_jhyy() -> i32 {
    asm!("cpuid");
    return 0 as i32;
}
```

**Compile + verify**:

```bash
jhyy compile compiler/tests/examples/inline_asm_cpuid.jhyy -o build/cpuid_test
objdump -d build/cpuid_test.exe | grep cpuid
# expected: cpuid instruction (0f a2) visible at offset after main_jhyy ret
./build/cpuid_test.exe
# EXIT: 0 (cpuid doesn't affect main's return path — runs after ret)
```

### 示例 2: 自定义 global 符号(asm 实际生效)

```jhyy
fn main_jhyy() -> i32 {
    asm!(".global _jhyy_asm_marker");
    asm!("_jhyy_asm_marker: .byte 0x42");
    return 0 as i32;
}
```

生成的 .s 末会包含:

```
.global _jhyy_asm_marker
_jhyy_asm_marker: .byte 0x42
```

`objdump -t build/cpuid_test.exe` 可查到 `_jhyy_asm_marker` 符号。

### 示例 3: 用户编错(operand 报错)

```jhyy
fn main_jhyy() -> i32 {
    asm!("mov {0}, {1}", "eax", "ebx");  // ❌ v3.0.1 不支持 operands
    return 0 as i32;
}
```

**Compile error**:

```
error: asm!(...) operands are not supported in v3.0.1 (single-string-literal only; v3.1 will add operand constraints)
```

---

## § 8 Cross-references

- D42 决议: [`jhyy_OS/docs/coordination.md`](../../../jhyy_OS/docs/coordination.md) § 3 D42 — inline asm 路径
- V3-A 3d no_std supplement (类似 doc 模板): [`jhyy-lang-spec-no_std-supplement-v3.0.0.md`](./jhyy-lang-spec-no_std-supplement-v3.0.0.md)
- V3-B batch plan: [`docs/plans/v3/batch-V3-B-plan.md`](../plans/v3/batch-V3-B-plan.md)
- ABI 锁: [`jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) — 无变化(本 supplement transparent)
- V2-A codegen_amd64 骨架: [`compiler/src0/codegen_amd64.jhyy`](../../src0/codegen_amd64.jhyy) — `codegen_amd64_emit_raw_asm` stub V3-B v3.0.1 已填 body
- 编码约定: [`docs/internal/conventions.md`](../internal/conventions.md) — fopen 模式 + side-file 约定
- Memory reference: `feedback_qbe_crlf_root_cause` (Windows fopen "a" → \r\n 污染)
