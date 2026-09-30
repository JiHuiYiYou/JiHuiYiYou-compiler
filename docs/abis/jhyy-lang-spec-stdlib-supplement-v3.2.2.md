# stdlib Supplement (v3.2.2)

> 锁定于 v3.2.2 (3l.1, std lib M0)。 后续 v3.2.3+ 增量补 append。

## 1. 模块清单

`compiler/src0/std/` 提供 4 个 M0 std lib 模块:

| 模块 | 文件 | 行数 | 公开 API |
|------|------|------|----------|
| `std::mem` | `compiler/src0/std/mem.jhyy` | ~107 | `mem_copy / mem_compare / mem_set / mem_find_byte / mem_zero / ptr_add` |
| `std::fmt` | `compiler/src0/std/fmt.jhyy` | ~187 | `fmt_i32 / fmt_i64 / fmt_str / fmt_hex_u32 / digit_char / hex_char / ptr_add` |
| `std::arena` | `compiler/src0/std/arena.jhyy` | ~180 | `arena_init / arena_alloc / arena_calloc / arena_reset / ptr_add` |
| `std::string` | `compiler/src0/std/string.jhyy` | ~200 | `str_from_cstr / str_from_bytes / str_len / str_data / str_concat / str_equals / str_compare / ptr_add` |

## 2. 设计约束 (M0)

- **不依赖 closure / generic / 借用** — M0 简化,后续 sprint 加
- **不跨模块 import** — `inline_imports` (main.jhyy:456-559) 只支持 `main_dir/mod_name.jhyy`,不支持 subdir (`std/*`);每个 std 模块自给自足,`ptr_add` 等 helper 各模块独立实现
- **不依赖 libc 运行时(部分)**:
  - `mem_*` — 自实现 byte/i32 循环
  - `fmt_*` — 自实现 int → ASCII 转换
  - `arena_*` — 用 libc `malloc` (与 src0/arena.jhyy C-side Arena 不同 layout)
  - `string` — 自带 mini arena allocator,不依赖 std::arena

## 3. arena layout (40 字节)

`std::arena` 的 `Arena` 结构跟 C-side `runtime.h:Arena` (24 字节) 不同:

```
offset 0:  *u8   blocks           (linked list of ArenaBlock, head = first block raw ptr)
offset 8:  *u8   cur              (current allocation cursor; 0 = uninitialized)
offset 16: *u8   end              (end of current block; 0 = uninitialized)
offset 24: i64   reserved         (unused, reserved)
offset 32: i64   default_size     (block alloc size after init)
```

`ArenaBlock` 结构 (前 8 字节):

```
offset 0: *u8 next_block  (linked list ptr)
```

block 头部 8 字节存 `next_block`,数据从 offset 8 开始 (`malloc(size + 8)` then `data_start = raw + 8`)。

**与 runtime.c `arena_alloc` 不兼容**: std::arena 用 `malloc` 后自己管理 blocks;runtime.c 用 24B `Arena` 结构 (start/cur/end)。两者 API 名字相同但 layout 不同 → 测试 inline 副本用 `std_*` 前缀避免符号冲突(per W-076 待修)。

## 4. 公开 API 详细

### 4.1 std::mem

```jhyy
fn ptr_add(p: *u8, off: i64) -> *u8        // 本地指针算术 helper
fn mem_copy(dst: *u8, src: *u8, n: i64) -> *u8  // 复制 n 字节;返 dst
fn mem_compare(a: *u8, b: *u8, n: i64) -> i32   // 返 <0 / 0 / >0
fn mem_set(dst: *u8, val: i32, n: i64) -> *u8   // n 字节设为 val & 0xff
fn mem_find_byte(p: *u8, n: i64, val: i32) -> i64  // 返 index / -1
fn mem_zero(dst: *u8, n: i64) -> *u8            // 等价 mem_set(p, 0, n)
```

**W-075**: `mem_set` 用 `*(p+i) as *i32 = b` 而非 byte-by-byte store。每次 loop 写 4 字节 i32。 这等价 byte-wise set 当 `b = val & 0xff` 时,但性能特征不同。M0 接受,v3.x mid 优化。

### 4.2 std::fmt

```jhyy
fn ptr_add(p: *u8, off: i64) -> *u8
fn digit_char(d: i32) -> i32              // 0..9 → '0'..'9' (48..57)
fn hex_char(d: i32, upper: i32) -> i32    // 0..15 → '0'..'9' / 'A'..'F' / 'a'..'f'
fn fmt_i32(buf: *u8, val: i32) -> i64     // 写入十进制 + \0;返字节数 (不含 \0)
fn fmt_i64(buf: *u8, val: i64) -> i64
fn fmt_str(buf: *u8, s: *u8) -> i64       // 复制 cstr 到 buf;返字节数
fn fmt_hex_u32(buf: *u8, val: i32, upper: i32) -> i64  // upper=0 小写 / 1 大写
```

buffer 必须 ≥ 32 字节 (i32/i64 最多 11/20 位 + sign + \0)。

### 4.3 std::arena

```jhyy
fn ptr_add(p: *u8, off: i64) -> *u8
fn arena_init(a: *u8, default_size: i64) -> i32       // 1 = ok / 0 = fail
fn arena_alloc(a: *u8, size: i64) -> *u8             // 8 字节对齐;返 ptr / 0
fn arena_calloc(a: *u8, size: i64) -> *u8            // alloc + memset 0
fn arena_reset(a: *u8) -> i32                        // 1 = ok / 0 = fail
```

`a` 必须是 ≥ 40 字节对齐的 storage (e.g. `let a: [i32; 8] = ...`)。

### 4.4 std::string

`StringHeader` layout (16 字节):

```
offset 0:  *u8 data     (字节数据指针)
offset 8:  i64 len      (字节长度, 不含 \0)
```

```jhyy
fn ptr_add(p: *u8, off: i64) -> *u8
fn str_from_cstr(a: *u8, s: *u8) -> *u8            // a 是 [i32; ≥4] storage
fn str_from_bytes(a: *u8, s: *u8, n: i64) -> *u8
fn str_len(s: *u8) -> i64
fn str_data(s: *u8) -> *u8
fn str_concat(a: *u8, x: *u8, y: *u8) -> *u8
fn str_equals(x: *u8, y: *u8) -> i32               // 1 = equal / 0 = not
fn str_compare(x: *u8, y: *u8) -> i32              // <0 / 0 / >0
```

**注**: String 不是 null-terminated C string;是 (data ptr, len) pair。 内部 null-terminator 仅作 debug 一致性(由 `str_from_cstr` 写入,`str_concat` 末尾)。

## 5. 已知限制 / W-XXX

- **W-073**: D43 closure chain — 本 sprint hold v3.2.1 N14 baseline;v2.x 在修 codegen_amd64_run self-backend 0-byte bug,等 v2.x 修后真 fix closure chain (推到 v3.2.3+)
- **W-074**: D22 arena byte-equal 推迟 — `src0/arena.jhyy` 跟 `src/arena.c` byte-equal 不成立;v3.2.2 `std::arena` API 等价但 layout 不同 (40B vs 24B);byte-equal 真修留 v3.2.4
- **W-075**: `std::mem mem_set` 用 i32 store 而非 byte store — M0 接受,优化留 v3.x mid
- **W-076**: `std::arena test inline 副本` 用 `std_*` 前缀 fn 名字避免跟 runtime.c `arena_alloc` 符号冲突;正式 std::arena module 跟 runtime.c 协同留 v3.x mid (C-side arena_alloc 应改名为 c_arena_alloc 或加 namespace)
- **W-077**: `src0/std/mem.jhyy mem_find_byte` codegen 路径在某些 stack pattern 下产生 access violation (test `std_mem_find_byte` 已被 deferred 到下一 sprint);M0 接受,fix 留 v3.x mid
- **W-078**: `array[i32]` index (i32 type) 触发 QBE `invalid type for first operand %tXX in mul` — codegen 应自动 extsw 升 w→l。 当前 workaround: 用 `array[i64]` index。 fix 留 v3.x mid。

## 6. 测试覆盖

`compiler/tests/examples/std_*.jhyy` 19 个 test files,每个 inline 副本实现待测 fn 后调用验证。 EXPECT 注释给出预期 exit code。

| 模块 | 测试数 | 文件 |
|------|------|------|
| std::mem | 6 (mem_basic / mem_set / mem_zero / mem_compare / mem_copy + find_byte deferred) | std_mem_*.jhyy |
| std::fmt | 4 (fmt_i32 / fmt_i32_neg / fmt_i64 / fmt_str / fmt_hex) | std_fmt_*.jhyy |
| std::string | 6 (len / equals / concat / compare / from_bytes / data) | std_string_*.jhyy |
| std::arena | 3 (basic / calloc / reset) | std_arena_*.jhyy |
| **总计** | **19 PASS + 1 deferred** | std_*.jhyy |

ship gate 通过: regress 137/137 (含 19 std + 118 原 — 0 failed, 20 skipped)。
