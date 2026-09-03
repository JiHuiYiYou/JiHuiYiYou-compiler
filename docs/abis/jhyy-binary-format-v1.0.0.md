# JHYY Binary Format v1.0.0 — `.jhyynb`(jhyy native binary)

**日期**: 2026-09-04
**状态**: 设计文档(完成最终态视图;实装时机另行决定)
**目标**: 为 jhyy_OS user-space + jhyy 编译器自身(M11)+ GDB attach 三重角色,定义一个 **jhyy 原生** 的二进制格式
**不在范围**: 实施 sprint 划分 / 工作量估算 / 时间表(per memory `feedback_no_date_estimates`)
**关联**: [`coordination.md § 3 D44`](../../../../jhyy_OS/docs/coordination.md) | OS 镜像 [`v0.0.5-binary-format.md`](../../../../jhyy_OS/docs/v0.0.5-binary-format.md) | plan 文件 [`c-jihuiyiyou-twinkling-frog.md`](../../../..//Users/liuzhen/.claude/plans/c-jihuiyiyou-twinkling-frog.md)

---

## 1. 设计动机

jhyy_OS kernel 走 `kernel.efi`(PE/COFF,被 UEFI 协议锁,per **D1** 2026-08-04)。但 kernel 起来之后跑的 **user-space 程序**格式由 kernel 决定,有完全自由度。三选一:

| 选项 | 否决理由 |
|---|---|
| **PE/COFF** | Windows 遗产,跟 jhyy 哲学不匹配;重 header(DOS+NT+section,~1KB)为 OS-native use 浪费 |
| **ELF** | Linux 工具全兼容,但"自研 OS 跑 Linux 二进制"哲学上别扭;ABI § 13 多目标 ABI 表跟 jhyy `amd64_sysv` 绑死,会引入 `*T` 语义跟 musl 对齐负担 |
| **.jhyynb(本 spec)** | 最贴合 jhyy 哲学 + 承载 jhyy 独有特性(Cap<T> phantom / region types / `#[ipc_handler]` dispatch / D41 Debug ABI mirror)+ 完整 DWARF 子集(GDB attach)+ 工具栈自主 |

**用户决策**(2026-09-04 锁):
- **目标命名**:`--target=jhyy-os`(由 jhyy 编译器识别)
- **后缀名**:`.jhyynb`
- **覆盖范围**:jhyy_OS user-space 程序 + M11 时 jhyy 编译器自身(jhyy 编译器在 jhyy_OS 上跑也用 .jhyynb)+ **完整 DWARF 子集**(支持 GDB attach)
- **设计哲学**:**"不将就"** = 字段不抄 ELF 历史包袱,但每段都对应 jhyy 一个具体语义契约

---

## 2. 约束(从已锁 D-locks 推导)

- **5 原则**(per [`../../jhyy_OS/docs/v0.0.2-foundation-revision.md § 3.1`](../../../../jhyy_OS/docs/v0.0.2-foundation-revision.md)):可行且简单 / 双线作战 / 寄生 Windows / Debug 在语言里 / Kernel 不解决语言问题
- **D6 + D23**:`Cap<T>` 8 字节 wire = `{cnode_idx:u32@0, depth:u8@4, _pad:u8@5, rights:u16@6}`,phantom 字段 0 字节(codegen skip `_phantom`)
- **D16**:`#[ipc_handler]` cap-offset 表 = `{msg_tag:u32, n_caps:u16, cap_offsets:[u16;n]}`(16B header 之后,payload 之前)
- **D40**:wire-format 表达规则 — 链表 = `*T`(8B),数组 = `[*]T`(16B ptr+len)
- **D41**:jhyy 无 `packed` / `repr(...)`,所有 wire-format struct 必须自然对齐 + 显式 `_pad` 字段
- **D-GUI-12**(2026-09-01):M3 syscall ABI = **MS x64 函数指针 + `#[naked]` interrupt**,**不**走 Linux `syscall` 指令;`.jhyynb` 不需要 syscall 指令编码元数据
- **D42**:v2.x 自写后端完成前,asm 走 QBE .s 输出路径;`.jhyynb` 设计跟这条兼容(asm 块仍可由 QBE 工具链 → .s → post-process 进 .jhyynb)
- **D43**:byte-equal = 阶段性 self-equal,不跨版本;`.jhyynb` 必须 header 内含版本字段,跨大版本不兼容时显式 bump version

---

## 3. 文件总览

```
.jhyynb 文件结构(自顶向下):
┌─────────────────────────────────────────┐
│ § 4 Header (固定 112B,8-aligned)        │ ← magic + version + flags + offsets
├─────────────────────────────────────────┤
│ § 5 Section Table (N × 32B)             │ ← N 个 section 描述符
├─────────────────────────────────────────┤
│ § 6 String Table (variable, 8-aligned)  │ ← section name + symbol name 引用
├─────────────────────────────────────────┤
│ § 7 Cap Init Table (variable)            │ ← 进程启动需要的初始 caps
├─────────────────────────────────────────┤
│ § 8 IPC Dispatch Table (variable)        │ ← #[ipc_handler] 注册表
├─────────────────────────────────────────┤
│ § 9 Region Table (variable)              │ ← region/arena 描述
├─────────────────────────────────────────┤
│ § 10 Section 0 data (e.g. .text)        │
├─────────────────────────────────────────┤
│ § 11 Section 1 data (e.g. .rodata)      │
├─────────────────────────────────────────┤
│ ...                                      │
├─────────────────────────────────────────┤
│ § 12 Debug Sub-section Group             │ ← DWARF 子集 + jhyy 专属
├─────────────────────────────────────────┤
│ § 13 Symbol Table (variable, 可选)       │ ← 函数 + 全局变量符号
├─────────────────────────────────────────┤
│ § 14 Relocation Table (variable, 可选)   │ ← 静态链接用
└─────────────────────────────────────────┘
```

**核心原则**:
- **页对齐**:所有 section data 起始 4 KiB 对齐(便于 kernel 直接 mmap)
- **8 字节对齐**:所有 header / table / entry 8 字节对齐(RAX / DebugEvent 56B / 跨 CPU 一致)
- **小端序**:amd64 决定(预留 future aarch64 时改 header 标志位)
- **可选即零**:任意可选组件缺失时,header 对应 `*_off` = 0

---

## 4. Header(112B, 8-aligned)

```c
struct JhynbHeader {                        // 8-aligned, 全自然对齐, 显式 _pad
    magic:         [4]u8 = 'J','B','E','\x01',  // "JBE\x01" — JBE = Jhyy Binary Executable, \x01 = format version 1;4B magic
    version:       u16 = 1,                  // 格式版本(初始 1)
    flags:         u16,                      // bit 0 = debug_info present
                                                // bit 1 = symbol_table present
                                                // bit 2 = relocation_table present
                                                // bit 3 = cap_init present
                                                // bit 4 = ipc_dispatch present
                                                // bit 5 = region_table present
                                                // bit 6 = pie (position-independent)
                                                // bit 7-15 = reserved
    target:        u8 = 0,                   // 0 = amd64_jhyy_os(预留 1=aarch64, 2=riscv64)
    abi_version:   u8,                       // 对齐 jhyy-abi-v1.x.x 主版本
    _pad0:         u16,                      // 显式 padding(8-aligned 下一字段)

    entry_point:   u64,                      // .text 段内 _start 偏移(vaddr = section[.text].vaddr + entry_point)
    stack_size:    u64,                      // 初始栈大小(per-thread; kernel 创建时 mmap)
    heap_hint:     u64,                      // 初始 heap 起始 hint(user std malloc first-fit 起跳点)

    section_count: u16,                      // section table 条目数
    _pad1:         u16,                      // padding

    section_table_off:   u32,                // section table 文件偏移(相对 .jhyynb 起点)
    section_table_size:  u32,                // N × 32B
    string_table_off:    u32,
    string_table_size:   u32,

    cap_init_off:        u32,                // § 7 cap init table 偏移;0 = 无
    cap_init_count:      u16,                // 条目数
    _pad2:               u16,

    ipc_dispatch_off:    u32,                // § 8 IPC dispatch table 偏移;0 = 无
    ipc_dispatch_count:  u16,
    _pad3:               u16,

    region_table_off:    u32,                // § 9 region table 偏移;0 = 无
    region_table_count:  u16,
    _pad4:               u16,

    debug_off:           u32,                // § 12 debug section 偏移;0 = 无
    debug_size:          u32,

    symbol_table_off:    u32,                // § 13 符号表偏移;0 = 无
    symbol_table_size:   u32,

    reloc_table_off:     u32,                // § 14 relocation 表偏移;0 = 无
    reloc_table_size:    u32,

    header_crc:          u32,                // CRC32(header[0..104]) — transit corruption detect

    _pad5:               u32,                // 尾 padding(8 对齐收尾)
}
// 总 112B, sizeof = 112, alignof = 8
```

**字段语义注释**:
- `entry_point` 是 `.text` 段内偏移,**不是绝对 vaddr**;loader 用 `section[.text].vaddr + entry_point` 算真实入口(per ABI § 9 程序入口)
- `heap_hint` 是 user std lib(`malloc` / arena first-fit)的起点建议;kernel 创建进程时若 hint 已占,改用 mmap 区域尾
- `flags` bit 6 PIE:**未来**支持(v0 走静态 base,M11 之后再开);位定义先定
- `header_crc` 是 header[0..104] 的 CRC32(不包自身 4B + 尾 padding 4B);loader 加载时校验

---

## 5. Section Table(N × 32B, 8-aligned)

```c
struct SectionEntry {                       // 8-aligned, 全自然对齐
    name_idx:        u32,                    // string table 内偏移
    kind:            u8,                     // 0=text, 1=rodata, 2=data, 3=bss,
                                                // 4=cap_init, 5=ipc_dispatch,
                                                // 6=debug_group, 7=region_table,
                                                // 8=tls, 9-255=reserved
    flags:           u8,                     // bit 0 = executable
                                                // bit 1 = writable
                                                // bit 2 = readable
                                                // bit 3 = alloc_in_memory
                                                // bit 4 = no-bits(bss 标志)
                                                // bit 5-7 = reserved
    _pad0:           u16,                    // 显式 padding

    vaddr:           u64,                    // 虚拟地址(loader 创建 mmap 时的基准)
    file_off:        u32,                    // 文件内偏移(4 KiB 对齐)
    file_size:       u32,                    // 文件内大小
    mem_size:        u32,                    // 内存大小(≥ file_size; bss 时 > file_size)
    align:           u32,                    // 对齐要求(通常 = 4 或 4096)
}
// 总 32B, sizeof = 32, alignof = 8
// MVP 上限:file_off / file_size / mem_size 全 u32,单 .jhyynb ≤ 4 GiB;若 debug build DWARF 子节接近此值,M11+ 升级到 u64(per § 17 Open #9)
```

**kind 编码含义**:

| kind | 名称 | flags 默认 | 内容 |
|---|---|---|---|
| 0 | `.text` | RX | 代码(可执行) |
| 1 | `.rodata` | R | 只读数据 |
| 2 | `.data` | RW | 已初始化数据 |
| 3 | `.bss` | RW (bit 4) | 零初始化(不占文件) |
| 4 | `cap_init` | R | § 7 cap init table |
| 5 | `ipc_dispatch` | R | § 8 IPC dispatch table |
| 6 | `debug_group` | R | § 12 DWARF + jhyy 专属 |
| 7 | `region_table` | R | § 9 region descriptors |
| 8 | `.tls` | RW | thread-local storage(预留,M11 后用) |

**关键设计选择**:`cap_init` / `ipc_dispatch` / `region_table` / `debug_group` 是 **jhyy 专属 section** — 这是 .jhyynb 跟 ELF / PE/COFF 最大区别。ELF 只有通用 section;`.jhyynb` 把 jhyy 语言 / runtime 概念当 first-class section 类型,让 kernel / GDB / CodeGraph 不用解析就知道这段是干啥的。

---

## 6. String Table

简单 null-terminated 字符串拼接,首 4B 是 reserved(0)。每字符串以 `\0` 结尾,8B 对齐 padding。

```c
struct StringTable {
    _pad:           u32,                    // 4B 起始 padding
    strings:        []u8,                    // N 个 null-terminated string 拼接
                                                // 末尾 8B 对齐
}
```

**引用方式**:`name_idx` 是相对 StringTable 起点的字节偏移。Section / Symbol / Region name 全部走这个表。

---

## 7. Cap Init Table(per-entry 32B, 8-aligned)

```c
struct CapInitEntry {                       // 8-aligned, 全自然对齐
    type_tag:       u32,                     // 0=endpoint, 1=page, 2=framebuffer,
                                                // 3=console, 4=file, 5=shm,
                                                // 6=compositor, 7=surface,
                                                // 8=seat, 9=buffer, 10=endpoint_focus,
                                                // 11-65535 = OS-specific,
                                                // 65536+ = user-defined
    cnode_idx_hint:  u32,                     // kernel-assigned cnode slot; 0xFFFFFFFF = kernel 自由分配
    rights:         u16,                     // bit 0 = read, 1 = write, 2 = grant, 3 = revoke
    depth:          u8,                      // CSpace 深度(per `v0.0.1-capability.md § 2.1`)
    _pad0:          u8,                      // 显式 padding

    name_idx:       u32,                     // string table 内偏移(符号名,如 "console"/"init_endpoint")
    init_call_off:  u32,                     // .text 内偏移 — binary 启动后调用的初始化函数
                                                // (per-Cap 自定义 init; 0 = 无需 init)
    _pad1:          u32,                     // 显式 padding

    provenance_seed_off: u32,                 // debug build 时 .debug_cap 段内 ProvenanceInfo 初始 seed 偏移
                                                // 0 = 无 seed(runtime 重建);loader 仅在 header.flags bit 0 (debug_info present) = 1 时读此字段
    _pad2:          u32,                     // 显式 padding

}
// 总 32B, sizeof = 32, alignof = 8
```

**为什么这样设计**:
- `type_tag` 是 enum,不是 string — kernel 解析 O(1),不用解析字符串
- `cnode_idx_hint` = 0xFFFFFFFF 时 kernel 自由分配;否则 kernel 尽量按 hint 分配(用于 init 进程持有 root endpoint 之类)
- `rights` 直接对应 `Cap<T>` 8B 布局的 `rights: u16` 字段(per D6),kernel 分配 cap 时直接 copy
- `init_call_off` 允许 per-Cap 初始化逻辑(jhyy-side `#[cap_constructor]` emit);loader 创建 cap 后跳此函数(若非零)
- `provenance_seed_off` 是 jhyy 专属 — debug build 可塞 ProvenanceInfo 初始 snapshot,runtime 不用重建(per Q-OS-003 / D14)
- `_phantom: *T` 字段**不进 binary**(per D23, codegen skip;Cap<T> jhyy-side phantom 不出现于任何 wire format)

---

## 8. IPC Dispatch Table(per-entry 16B, 8-aligned)

```c
struct IpcDispatchEntry {                   // 8-aligned, 全自然对齐
    msg_tag:        u32,                     // IPC 消息 tag(用户层 enum)
    handler_fn_off: u32,                     // .text 内偏移 — handler 函数入口
                                                // (= section[.text].vaddr + off)
    cap_off_count:  u16,                     // cap_offsets 数组长度(对齐 D16 CapOffsetTable.n_caps)
    _pad0:          u16,                     // padding

    cap_off_table_off: u32,                  // .rodata.cap_offsets 段内偏移(D16 wire format)
}
// 总 16B, sizeof = 16, alignof = 8
```

**`cap_off_table_off` 指向的子结构**(在 `.rodata.cap_offsets` 段内):
```c
struct CapOffsetTable {                     // D16 wire format
    n_caps:         u16,                     // caps 数量
    _pad0:          u16,                     // padding(8 对齐)
    cap_offsets:    []u16,                   // Cap<T> 字段在 IPC message struct 内的偏移数组
}
// 大小 = 8 + n_caps * 2B; 末尾 8B 对齐
```

**为什么这样设计**:
- `msg_tag` 直接对应 D13 / D20 `#[ipc_handler(msg: M)]` 的 M 类型 tag;kernel 按此匹配
- `handler_fn_off` 是函数指针等价 — kernel 接 ipc_call 时按 tag 查 dispatch,跳 handler
- `cap_off_table_off` 指向 D16 wire format — kernel 收到 IPC message 后按 cap_offsets 数组原地改写 cnode_idx(避免 deep-copy)
- 整体走 MS x64 函数指针 + `#[naked]` interrupt(per D-GUI-12)— kernel 不需要解析 syscall 指令编码
- 16B 末尾对齐收尾(8 对齐),无需 reserved 字段

---

## 9. Region Table(per-entry 24B, 8-aligned)

```c
struct RegionEntry {                        // 8-aligned
    region_id:      u32,                     // region 唯一 ID(进程内)
    kind:           u8,                      // 0=anon_arena, 1=mmap, 2=raw_mmio, 3=unsafe_share
                                                // 4=cap_namespace, 5=kernel_shared
    rights:         u8,                      // bit 0 = read, 1 = write, 2 = exec, 3 = share
    _pad0:          u16,                     // padding

    base_vaddr:     u64,                     // region 起始 vaddr
    size:           u32,                     // region 大小(4 KiB 倍数)
    flags:          u32,                     // bit 0 = growable, 1 = cow, 2 = pinned, 3 = lazy_commit
}
// 总 24B, sizeof = 24, alignof = 8
```

**为什么这样设计**:
- `region_id` 是 OS 内核 + jhyy 编译器联合管理 — compiler codegen 时每个 `arena_alloc` 携带 region_id(per region types primary, D2)
- `kind` 让 kernel 知道 region 怎么管理(anon_arena 进程退出释放;raw_mmio 不能 swap;unsafe_share 跨进程 ledger 追踪 per D-GUI-2)
- **不携带 borrow checker 数据**(违反 5 原则 #1 + #5)
- `flags` 预留给 M11+ 高级特性(growable / cow)

---

## 10-11. 通用 Section Data(`.text` / `.rodata` / `.data`)

`.text` / `.rodata` / `.data` 三类段是纯字节内容,**不规定内部格式**(kernel 只 mmap 到 vaddr,不解析)— 由编译器 codegen 决定里面写什么(amd64 机器码 / 常量 / 已初始化全局变量)。

**关键规则**:
- `.bss`(`kind=3`, `flags` bit4 = no-bits):`file_size = 0`, `mem_size > 0`,kernel 只 mmap 不读文件
- 所有 section **首地址 4 KiB 对齐**(vaddr / file_off 都是 4 KiB 倍数)— kernel 直接 mmap 即可
- 代码段不需要内嵌 relocations — **MVP 静态链接**(per `v0.0.1-process-model.md` 占位)

---

## 12. Debug Group Section(DWARF 子集 + jhyy 专属)

Debug section 是一个**复合容器**,内部组织成"debug sub-section group":

```
Debug Group 结构:
┌─────────────────────────────────────────┐
│ Debug Group Header (16B)                 │
│  - sub_section_count: u16                │
│  - _pad: u16                              │
│  - total_size: u32 (整个 debug group 大小) │
│  - _pad2: u32                              │
├─────────────────────────────────────────┤
│ Sub-section Table (M × 16B)               │
│  - {name_idx, off, size}                   │
├─────────────────────────────────────────┤
│ Sub-section 0 data                        │
├─────────────────────────────────────────┤
│ Sub-section 1 data                        │
├─────────────────────────────────────────┤
│ ...                                      │
└─────────────────────────────────────────┘
```

**Sub-section Table Entry(16B, 8-aligned)**:
```c
struct DebugSubSection {
    name_idx:       u32,                     // string table 内偏移(DWARF 标准名 + jhyy 专属名)
    file_off:       u32,                     // 相对 debug group 起点的偏移
    size:           u32,                     // sub-section 大小
    flags:          u16,                     // bit 0 = compressed(zlib), bit 1 = required
    _pad0:          u16,                     // padding
}
// 总 16B
```

**标准 DWARF sub-section 名(per DWARF v5 spec)**:

| sub-section 名 | 用途 | 是否必有 |
|---|---|---|
| `debug_info` | DIE(调试信息项) | debug build 必有 |
| `debug_abbrev` | 缩写表 | debug build 必有 |
| `debug_line` | 行号表 | debug build 必有 |
| `debug_str` | 字符串表 | debug build 必有 |
| `debug_frame` | 调用帧信息(backtrace 用) | 可选 |
| `debug_aranges` | 地址范围表(快速定位) | 可选 |
| `debug_ranges` | 范围列表 | 可选 |
| `debug_loc` | 位置描述(变量位置) | 可选 |

**jhyy 专属 sub-section 名**:

| sub-section 名 | 用途 |
|---|---|
| `jhyy_cap` | ProvenanceInfo 初始 seed 表(per-cap provenance link,debug build 用) |
| `jhyy_ipc` | `#[ipc_handler]` 注册 metadata 完整版(handler signature / msg layout) |
| `jhyy_region` | region types 完整描述(region graph + ownership chain) |
| `jhyy_coroutine` | (预留)coroutine state machine 描述(M11+ 后用) |

**GDB 怎么读 .jhyynb 的 DWARF**:
1. jhyy_OS kernel 启动 `jhyy-gdbstub` daemon(类似 Linux kgdb,常驻进程)
2. 用户用 `gdb --remote=<jhyy-os-tcp>` attach
3. gdbstub 通过 GDB remote protocol 响应 `qXfer:features:read:target.xml` 等查询
4. gdbstub 解析 .jhyynb debug group,把 DWARF sub-section 通过 remote protocol 喂给 GDB
5. GDB 拿到标准 DWARF → 正常显示源码 / 单步 / 看变量

**为什么不直接用 ELF**:
- ELF `.debug_info` 段必须按 ELF 解析 → kernel 不解析 ELF 也能让 GDB 通过 stub 拿到 DWARF 字节
- jhyy 专属 sub-section(`.jhyy_cap` 等)GDB 不识别,但 jhyy 自己的 `jhyy-inspect` / CodeGraph 能读

---

## 13. Symbol Table(可选, 16B per entry)

```c
struct SymbolEntry {                        // 8-aligned
    name_idx:       u32,                     // string table 偏移
    section_idx:    u16,                     // 所属 section 在 section table 的索引
    kind:           u8,                      // 0=function, 1=global_var, 2=local_static, 3=cap_constructor
    _pad0:          u8,                      // padding

    vaddr_off:      u32,                     // section 内偏移(vaddr = section.vaddr + vaddr_off)
    size:           u32,                     // 符号占用大小(代码 = 函数体字节数;变量 = sizeof)
}
// 总 16B(可选 24B 带 type metadata)
```

**MVP 简化**:v0 仅 function + global_var 两种 kind;type metadata 留未来扩展(预留 24B form)。

---

## 14. Relocation Table(可选, 16B per entry)

```c
struct RelocEntry {                         // 8-aligned
    section_idx:    u16,                     // 目标 section 索引
    kind:           u8,                      // 0=abs64(8B 绝对地址), 1=rel32(4B 相对偏移)
    _pad0:          u8,                      // padding

    offset:         u32,                     // section 内偏移(要 patch 的位置)
    addend:         u64,                     // 加数(PIE 时 = 0)
}
// 总 16B
```

**MVP 静态链接**:`reloc_table_off = 0` — 编译器 emit 时所有地址已知,不需要 patch

**未来 PIE / shared lib**:bit 6 PIE 标志 + reloc_table 不为零

---

## 15. 关键设计抉择汇总

| 抉择 | 选 | 否决方案 |
|---|---|---|
| 文件 magic | `JBE\x01`(4B) | ELF `\x7fELF`(4B) / PE `MZ`(2B) |
| Endianness | 小端(amd64) | 大端预留 future |
| 对齐 | 8B 通用 / 4KiB section | 4B 通用(AMD64 退化) |
| Section 表 | 32B/entry,固定 | ELF 64B/entry,带 sh_info 等历史字段 |
| Program headers | **无** | ELF 有(描述 segment vs section 映射)— jhyy 简化用 section 直 mmap |
| Dynamic linking | 不支持(预留 PIE 标志) | ELF .dynsym / .dynamic |
| Cap 表 | first-class section(`kind=4`) | ELF note section + custom parser |
| IPC dispatch | first-class section(`kind=5`) | ELF .note + 自定义解析 |
| Region 表 | first-class section(`kind=7`) | ELF .comment + 自定义解析 |
| Debug | 复合 DWARF 子集 + jhyy 专属 | DWARF 全部 + ELF 兼容 |
| Symbol 表 | 简化 16B/entry | ELF 24B/entry + 复杂 binding |

**为什么"first-class section"重要**:jhyy 哲学"Debug 在语言里"(原则 4)+ "Kernel 不解决语言问题"(原则 5)— Cap / IPC / Region 概念是 jhyy 语言层 first-class,不是 OS 后期加的;**.jhyynb 必须让 kernel 不用解析 jhyy 类型就知道这段是干啥的**,loader / GDB / CodeGraph 各自独立解析各 section,互不耦合。

---

## 16. 与 D-locks 对位(可追溯表)

| D-lock | 内容 | .jhyynb 对应字段 |
|---|---|---|
| **D1** | Boot 走 UEFI + PE/COFF | kernel.efi 不变;.jhyynb 仅 user-space |
| **D2** | Region types primary + linear cap + raw MMIO | § 9 region_table + § 7 cap_init |
| **D6** | `Cap<T>` 8B layout | § 7 cap_init_entry.rights + init 字节 + § 8 ipc dispatch cap_offset |
| **D11** | M1-M3 `*mut T`,M4+ `&mut` | jhyy codegen emit 决定;.jhyynb 不感知 |
| **D13 / D20** | `#[ipc_handler]` attribute 不进 spec | § 8 ipc_dispatch + § 12 `.jhyy_ipc` |
| **D16** | Cap-offset 表 wire format | § 8 `cap_off_table_off` + `CapOffsetTable` 子结构 |
| **D17** | `IoResult<T>` 单态化 | 不影响 .jhyynb(enum 单态 emit 跟 ABI 一致) |
| **D22** | arena.jhyy 不扩展 | § 9 region_table 用 cap+offset 自管 |
| **D23** | Phantom sentinel + codegen skip | § 7 cap_init_entry **不进** `_phantom` 字段 |
| **D40** | wire-format 表达规则 | § 7-9 全部链表字段 = `*T`,全部数组字段 = `[*]T`(本设计 0 出现链表数组,都用 u32 offset + count) |
| **D41** | Debug ABI 锁(56B/64B/136B) | § 12 debug group 子结构 + `.jhyy_cap` ProvenanceInfo seed |
| **D-GUI-12** | M3 syscall = MS x64 + naked interrupt | § 8 IPC dispatch 走函数指针,无 syscall 指令编码 |
| **D42** | asm 走 QBE .s 工具链(过渡) | § 10 .text 段容许 inline asm 块(per D42 路径) |
| **D43** | byte-equal 阶段性 self-equal | § 4 `version` 字段跨大版本 bump |

---

## 17. Open(设计文档不锁,实装期讨论)

以下条目是**设计文档需要讨论的开放点**,不是 roadmap 时间:

1. **PIE / ASLR 支持时机**:§ 4 bit 6 PIE 标志预留,但 .reloc table 何时启用
2. **静态 vs 动态链接**:`reloc_table_off = 0` MVP 静态,M11+ 是否引入 shared lib(per `v3.x-language-expansion.md` 3l std lib 影响)
3. **DWARF 版本**:v5(2017 最新)还是 v4?跟 QEMU / GDB 默认版本对齐
4. **`.jhyy_coroutine` 格式**:M11+ coroutine state machine 描述格式(M11 没 sprint,只是预留)
5. **Section kind 9-255 分配策略**:kernel-specific / language-specific 怎么命名空间
7. **String Table 压缩**:debug build 字符串表是否 zlib 压缩
8. **大端序 future 支持**:`target` 字段预留 1=aarch64 / 2=riscv64,header layout 是否需要 endian 标志位
9. **file_off / file_size u32 → u64 升级时机**:MVP 4 GiB 上限对 user-space 程序够;jhyy 编译器自身 debug build 接近此值时(M11 实装期)考虑升级

---

## 18. 验证(实施前后)

**设计层面**(实装前):
1. **ABI 一致性**:§ 16 对位表逐项检查,每个 D-lock 都有对应字段
2. **size 算术**:每个 struct 末尾对齐算一遍;全表 8-aligned;Header 总 112B
3. **cap_init wire format 跟 OS cnode byte-equal**:模拟 .jhyynb § 7 + OS cnode 内存,逐字节 diff
4. **DWARF sub-section 名跟 GDB 期望对齐**:DWARF v5 spec 附录查 .debug_* 完整名清单

**实施后验证**:
1. **loader smoke test**:kernel 启动后加载一个最小 .jhyynb(仅 .text + .data),跳到 entry 跑通
2. **GDB attach 闭环**:`gdb --remote` 拿到 DWARF 后能 `list`、`break`、单步
3. **jhyy-inspect**:`jhyy-inspect foo.jhyynb` 打印 section table / cap_init / ipc_dispatch
4. **CodeGraph 摄入**:`.jhyynb` debug group 进 CodeGraph 后能查到函数 / 类型 / cap 关系
5. **jhyy 自举**:`--target=jhyy-os` 编出 jhyy 编译器自身的 .jhyynb,在 jhyy_OS 上跑通(regress 持平 v1.0.0 baseline)

---

## 19. 不在范围(明确)

- 实施 sprint 划分 / 工作量估算 / 时间表 — 见 memory `feedback_no_date_estimates`
- jhyy 编译器现有 QBE + gcc emit 链路如何迁就 .jhyynb — 是 QBE .s → post-process 包装,还是完全自写后端,设计层面**不锁**,实装期讨论
- DWARF 字节级 emitter 实现细节 — 本文档只 spec 容器结构,不写 emit 代码
- jhyy-OS kernel 如何 mmap .jhyynb sections — OS loader 实现细节,见 [`v0.0.5-binary-format.md`](../../../../jhyy_OS/docs/v0.0.5-binary-format.md)
- aarch64 / riscv64 .jhyynb 字节序 / calling convention 差异 — 留 future

---

## 20. 历史 + 版本

| 版本 | 日期 | 状态 | 摘要 |
|---|---|---|---|
| v1.0.0 | 2026-09-04 | 设计文档 | 初稿(plan 文件 `c-jihuiyiyou-twinkling-frog.md` 转正式 spec) |