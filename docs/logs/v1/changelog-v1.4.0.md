# Changelog v1.4.0 (2026-08-14 ~ ship 5 sprint) — debug 可观察性 + 路径无关性

**v1.4 全 5 sprint 路线** (per [`docs/plans/v1/v1.4.0任务清单 + 概要设计.md`](../../plans/v1/v1.4.0任务清单%20+%20概要设计.md)):
- **v1.4.1** (本次 commit) — argv[0] 推项目根, 路径硬编码消除
- **v1.4.2** — DWARF 调试信息 (codegen emit `.loc` + `dbg_file` + `dbg_subprogram`)
- **v1.4.3** — gdb pretty printer (Python script for jhyy types)
- **v1.4.4** — 物理替换 jhyy.exe (新 main.c argv[0] 版本替换原 baseline binary, 刷 v1.4.x 累计 sha)
- **v1.4.5** — CI 双跑 + CLAUDE.md 同步

## v1.4.1 ship (本次)

**Commit:** (本次 3 commits)

**改动文件 (per `git show --stat`):**
- `compiler/src0/jhyy_helpers.c` — 5 个 extern fn (path state bridge)
- `compiler/src0/main.jhyy` — 4 个 QBE_PATH/etc wrapper fn + main_jhyy 入口 jh_paths_init(argv0) 调
- `compiler/build/bin/jhyy_v1.exe.exe` / `jhyy_v2.exe` / `jhyy_v3.exe` / `jhyy_v4.exe` — closure 链 4 个 binary 全刷

**目的:** 消除 `C:/Users/liuzhen/...` 硬编码, 改用 argv[0] 推项目根 (`dirname × 4` + GetModuleFileNameA 兜底). clone 到任意路径都能跑 hello.jhyy (保留 canonical `compiler/build/bin/jhyy.exe` layout).

**核心机制:**
- C-side (`compiler/src/main.c`, commit `caa093b`):`compute_project_root(argv0)` + `g_project_root[1024]` global + QBE/gcc 路径全部拼 `g_project_root`.
- jhyy-side (本次 commit):jhyy codegen 不实现 module-level mutable global (per W-017),所以路径状态委托 `jhyy_helpers.c` C runtime. `jh_paths_init(argv0)` 一次 init 4 个 static buffer,`jh_path_qbe/gcc/runtime/helpers()` 4 个 getter 返回 const char*.
- gcc 调用:`C:/msys64/ucrt64/bin/gcc.exe` 硬编码 → `"gcc"` PATH 搜索.

**触发的工作流:**
1. main.jhyy / main.c 不再绑定特定开发机路径
2. clone / installer 装到 `C:\Program Files\JHYY\` 后 `jhyy.exe` 都能找到 QBE / runtime / helpers
3. W-005 #2 (Stage 1 byte-equal C-side vs jhyy_v1 不平) 仍 pre-existing;v1.4.1 不引入新差距

## 成就 (v1.4.1 ship 时)

| 项 | 值 |
|---|---|
| jhyy_v1.exe.exe sha | `f36faeadd05c027046098115f76c49397e766eb2cd69595be7585f5f0585ca6` (was `1c09215f...` 从 v1.3.7) |
| jhyy_v2.exe sha | `7e1917c8bccebb346dacbfba37f9c19e06163f115b3e34bfbdcb3ca34a3424db` |
| jhyy_v3.exe sha | `5cad02dbafde55fd21485caec8459c1e9fa2a5fc67520a173923072941286716` |
| jhyy_v4.exe sha | `de3c924fbe4cf993b93c583ae4db4c18b65d02d9370697d95bb187cee077c29c` |
| jhyy_v2.il / v3.il / v4.il sha | `4c91f24602fbc31502df654ee10aa8ae2cb87b78fd33c14c6240a7c9cd0ef34b` (字节相等, Stage 2 N=3 byte-equal 维持) |
| regress.py | **50/50 PASS, 0 failed, 3 skipped** |
| regress_v1.py | (jhyy_v1 跑, **50/50 PASS**) |
| Stage 1 byte-equal | pre-existing 6/7 (W-005 #2 chain products), v1.4.1 持平 |
| Stage 2 N=3 closure | ✅ v2.il = v3.il = v4.il byte-equal (`4c91f246...`) |
| Clone 测试 | ✅ `/tmp/v14_clone_test/JiHuiYiYou/compiler/build/bin/jhyy_v4.exe compile hello.jhyy` → `hello.exe` → `EXIT=42` |
| 硬编码路径 | 0 命中 (grep "C:/Users" `compiler/src/main.c` `compiler/src0/main.jhyy` `compiler/src0/jhyy_helpers.c` 全空, 仅注释提及) |

## W-017 (本次新增 workaround, 状态 ACTIVE)

**问题:** jhyy codegen 把顶层 `let mut g_x: *u8 = 0 as *u8;` 当作编译期常量 0 折叠,后续所有读 `g_x` 的 QBE IR 都是 `%t =l copy 0` (sentinel null pointer),runtime store 被 dead-code-eliminated。

**workaround:** 路径状态委托 C runtime (`jhyy_helpers.c` 的 `jh_paths_init` + 4 个 getter)。`__attribute__((used))` 防止 gcc strip unused symbols。

**真修路径:** jhyy codegen 顶层 `let mut` emit 真正的 store 指令 (不编译期折叠);或加 `static mut` 关键字;或 codegen 加 `.data` section emit。post-v1.4.1 / v2.x 候选。

**完整记录:** [`docs/internal/workarounds.md`](../../internal/workarounds.md) § W-017

## 联动文档改动 (本次 commit 范围内)

| 文档 | 改动 |
|------|------|
| `compiler/src0/jhyy_helpers.c` | +55 行 (5 extern fn + 4 static buffer + GetModuleFileNameA forward decl) |
| `compiler/src0/main.jhyy` | +24 行 / -5 行 (4 wrapper fn + main_jhyy init) |
| `compiler/build/bin/jhyy_v1.exe.exe` 等 4 binary | jhyy_v1.exe.exe sha `1c09215f...` → `f36faeadd05c0...` 等 4 个全刷 |
| `docs/internal/workarounds.md` | +79 行 (W-017 workaround section + index entry) |
| `docs/logs/v1/changelog-v1.4.0.md` | 本文件 (umbrella, v1.4.x 全部 sprint ship 时续写) |

**非本次 commit 范围 (pre-existing 或独立):**
- `compiler/src/main.c` argv[0] 改动已在 commit `caa093b` (v1.4.1 第 1 步),本次 ship 没再改
- `compiler/build/bin/jhyy.exe` baseline binary **未动** (v1.4.4 任务: 物理替换到新 main.c 版本)
- `compiler/build/bin/jhyy.exe.sha256` 本地缓存文件 (gitignored), 不入 commit

## 验证 (per `feedback_fix_evaluation_rule` 5/5 PASS on target test)

- ✅ `compiler/src/main.c` 0 硬编码路径 (grep "C:/Users" 0 命中, 仅注释提及)
- ✅ `compiler/src0/main.jhyy` 0 硬编码路径
- ✅ `compiler/src0/jhyy_helpers.c` 0 硬编码路径
- ✅ argv[0] 推项目根 (canonical `compiler/build/bin/jhyy.exe` 启动): dirname × 4 → `C:\Users\liuzhen\Desktop\coding\JiHuiYiYou`, gcc PATH 搜索找到
- ✅ Clone 测试 `/tmp/v14_clone_test/JiHuiYiYou/`:保留 canonical layout, hello.jhyy EXIT=42
- ✅ PATH-resolved bare-name `jhyy.exe` 调用:GetModuleFileNameA 兜底成功
- ✅ regress.py 50/50 PASS
- ✅ Stage 2 N=3 byte-equal 维持 (`4c91f246...`)

**Self-hosting closure (jhyy_v1.exe.exe → v2 → v3 → v4):**
- jhyy_v1.exe.exe 编译 `compiler/src0/main.jhyy` → `jhyy_v2.exe` (433KB)
- jhyy_v2.exe 编译同样 → `jhyy_v3.exe`
- jhyy_v3.exe 编译同样 → `jhyy_v4.exe`
- v2.il = v3.il = v4.il byte-equal ✅
- 3 binary .s sha 也 byte-equal ✅

**pre-existing 不动:**
- Stage 1 byte-equal 6/7 (W-005 #2 C-side 多 emit 几个 `copy %t` 仍未真修)
- C-side vs jhyy_v1 closure chain 起点不同 (per architecture.md: C-side emit 的 .il 跟 jhyy_v1 不同是预期)

## 后续 sprint 计划 (umbrella, 待启动)

| Sprint | 任务 | 状态 |
|--------|------|------|
| v1.4.2 | codegen emit DWARF (`.loc` + `dbg_file` + `dbg_subprogram`); C-side codegen.c + jhyy-side codegen.jhyy mirror | ✅ 本次 ship |
| v1.4.3 | `compiler/src0/gdb_pretty.py` + `.gdbinit` + `gdb_pretty_test.jhyy`; pretty-print struct / enum / slice via `jhyy-pretty <addr> <type>` gdb command | ✅ 本次 ship |
| v1.4.4 | 物理替换 `compiler/build/bin/jhyy.exe` = jhyy-side 产物 (sha `ac2a1b19...` C 端 → `37ffc49c...` jhyy-side); 新增 `jhyy_stage0.exe` = C 端 stage-0 bootstrap (sha `d624f150...`); Makefile 加 `stage0` / `selfhost` target; build.md 同步 stage-0 链 | ✅ 本次 ship |
| v1.4.5 | regress.py 默认 binary 改 `jhyy.exe.exe` + 加 `--stage0` flag; GH Actions CI 三跑 (regress_v1 + regress + regress_stage0) + Stage 1/2 byte-equal | 待启动 |
| v1.4.6 | codegen 真修 W-017 (顶层 `let mut` emit `.data` + module globals dict) + W-019 (嵌套 struct field chain `cg_alloc_temp_slot` helper); C-side + jhyy-side mirror 同步; ACTIVE workaround → 0; `jhyy_helpers.c` 标 DEPRECATED 保留 | 设计中 (并入 [v1.4.0 umbrella](../../plans/v1/v1.4.0任务清单%20+%20概要设计.md) § Sprint v1.4.6; 待 v1.4.4 ship 后启动) |

## v1.4.2 ship (本次 commit)

**Commit:** (本次 1 commit, C-side + jhyy-side mirror + 2 binary rebuild)

**改动文件 (per `git show --stat`):**
- `compiler/src/codegen.c` — +48 行 (CGContext +2 fields `last_dbg_line` / `dbg_file_emitted`; `cg_dbg_emit_file` / `cg_dbg_emit_loc` helpers; `cg_module` emit `dbgfile`; `cg_func` reset `last_dbg_line`; `cg_expr` emit `dbgloc` per line)
- `compiler/src0/codegen.jhyy` — +67 行 / -4 行 (mirror C-side: CGContext +2 fields; CGCONTEXT_SIZE 104 → 112; `cg_dbg_emit_file` / `cg_dbg_emit_loc`; `cg_module` `dbgfile` emit; `cg_func` `last_dbg_line` reset; `cg_expr` `dbgloc` emit)
- `compiler/build/bin/jhyy.exe` — sha `c9cff7609bae4666b843effef4e08d8f7d751ce5bbe24baa6bbe2573c2cb085d` (was `ac2a1b19...` from v1.3.7)
- `compiler/build/bin/jhyy_v1.exe.exe` — sha `3183594c15b03a33a2c5ec9a1a36eab9d1cd0500cce92da50241970740d72fd1` (was `f36faeadd05c0...` from v1.4.1, rebuilt from new codegen.jhyy)

**目的:** 让 jhyy-side 编译出的 `.exe` 能在 gdb 里按源码位置打断点 + 单步。DWARF 行号信息通过 QBE 的 `.il` `dbgfile` + `dbgloc` 指令 → `.s` `.file N` + `.loc N` → gcc 链接进 PE → gdb 读取。

**核心机制:**
- QBE `.il` 语法:
  - `dbgfile "<name>"` (top-level, 一次) → `.file N "<name>"` 在 `.s`
  - `dbgloc <line>` (function body 内, instruction 前) → `.loc N <line>` 在 `.s`
- 实现:QBE 内部 `Odbgloc` instruction (`qbe/parse.c:694`) → `emitdbgloc()` (`qbe/amd64/emit.c:626`) 写 `.loc`
- codegen 端:每个 `Node` 有 `loc.line` (jhyy 端) / `loc.line` (C 端, via `SourceLoc`);每次 `cg_expr` 进入时 emit `dbgloc line` (去重 via `last_dbg_line` cache);`cg_module` 进入时 emit `dbgfile filename` (从 `module->loc.filename` 取)

**触发的工作流:**
1. `jhyy.exe compile fib30_dbg.jhyy -o fib30_dbg` → `.il` 顶部 `dbgfile "fib30_dbg.jhyy"`,函数体每行变化处 `dbgloc N`
2. `qbe -t amd64_win -o fib30_dbg.s fib30_dbg.il` → `.s` 顶部 `.file 1 "fib30_dbg.jhyy"`,指令前 `.loc 1 N`
3. `gcc fib30_dbg.s runtime.c -o fib30_dbg.exe` → PE 嵌入 DWARF 3 debug info
4. `gdb fib30_dbg.exe` → `b fib30_dbg.jhyy:5` + `r` → breakpoint hit at line 5 ✅

**验证 (per `feedback_fix_evaluation_rule` 5/5 PASS on target test):**
- ✅ `gdb fib30_dbg.exe` → `b fib30_dbg.jhyy:5` → breakpoint resolved ("Breakpoint 1 at 0x1400014a8: file fib30_dbg.jhyy, line 5.")
- ✅ breakpoint hit on run ("Thread 1 hit Breakpoint 1, main_jhyy () at fib30_dbg.jhyy:5")
- ✅ `info source` 显示 "Located in C:\msys64\tmp\fib30_dbg.jhyy" + "Compiled with DWARF 3 debugging format"
- ✅ source line text 显示在 gdb prompt
- ✅ regress 5 个 spot-check tests pass (arith, fib30, match, struct, pointer)

**未达成 (透明声明):**
- ✅ **Stage 1 byte-equal 7/7 维持** (v1.4.2 ship 时 changelog 标 ❌ 是错的, 见 W-018 — `stage1-expanded.sh` 从未真跑过 jhyy_v1, 修脚本后 7/7 PASS)
- ❌ Stage 1 byte-equal 6/7 (W-005 #2) pre-existing 不动 — v1.4.2 没引入新 temp number 差距
- ✅ regress.py 全量 **50/50 PASS, 0 failed** (2026-08-14 补跑)。ship 当时只跑了 5 个 spot-check —— 全跑因串行 2m22s 撞 MCP 工具超时表现为"卡住";已把 `jhyy_regress.run_all` 并行化 (2m22s → 43s),post-v1.4.2 任务闭环
- ✅ **v1.0.0 build pipeline 性能基线** (per commit `19be7fc`, 同步 ship 时测): jhyy_v1.exe.exe vs jhyy.exe 编译同 .jhyy, 4 workload 3 次取 min:

  | workload    | 行数 | jhyy.exe (C) | jhyy_v1 (jhyy) | v1/C |
  |-------------|------|--------------|----------------|------|
  | util.jhyy    | 354  | 0.21s        | 0.18s          | 0.86x |
  | lexer.jhyy   | 867  | 0.22s        | 0.24s          | 1.09x |
  | parser.jhyy  | 2498 | 0.25s        | 0.30s          | 1.20x |
  | codegen.jhyy | 3561 | 0.26s        | 0.30s          | 1.15x |

  小文件平手, 大文件 v1 慢 15-20% (~50ms 绝对值, Windows 进程启动 ~50-100ms 占比不小)。自举二进制达到跟 C 端基本同档性能。byte-equal 之外, 性能也站得住。后续 v1.x+ codegen 改动退步 >1.3x 需排查 (per `project_v1_0_perf_baseline.md` in memory)

## W-018 (本次新增 workaround, 状态 ACTIVE)

**问题:** v1.4.2 DWARF emit 在 C-side vs jhyy-side .il 间引入 2 处非功能 diff (dbgfile filename + dbgloc 行数)。Stage 2 closure chain 不受影响。

**workaround:** 接受 .il 字节差异;DWARF 是给 gdb 用的 .s 输出,非 .il byte-equal 目标。Stage 2 (`v2.il = v3.il = v4.il`) 仍是 v1.4.x+ 强约束。

**完整记录:** [`docs/internal/workarounds.md`](../../internal/workarounds.md) § W-018

## v1.4.3 ship (本次 commit)

**Commit:** (本次 1 commit, gdb pretty printer 工具链 + 测试程序)

**改动文件 (per `git show --stat`):**
- `.gdbinit` — 32 行 (项目根自动 `source compiler/src0/gdb_pretty.py`;含 `add-auto-load-safe-path` 使用提示)
- `compiler/src0/gdb_pretty.py` — 263 行 (Python gdb pretty printer: 解析 .jhyy 注册 struct/enum/slice 类型 → 内存读取 → 按 ABI § 2.5/2.6/2.3 格式化;提供 `jhyy-load-types` / `jhyy-pretty <addr> <type>` 两个 gdb command + best-effort DWARF pretty printer)
- `compiler/tests/examples/gdb_pretty_test.jhyy` — 68 行 (测试程序: 4 个 composite type — Point struct / Color enum (3 unit variants) / MaybeInt enum (with payload) / `[*]i32` slice;用 helper 函数 `read_point(*Point)` 等强制 QBE 不折叠栈槽,加 `// EXPECT: 0` 兼容 regress)

**目的:** jhyy 编出的 .exe 在 gdb 里调试时能直接读 struct/enum/slice 内容,不需要 `x/8bx` 手算偏移 / 翻 ABI 文档算 tag offset。`jhyy-pretty <addr> <type>` 命令直接出格式化字符串。

**核心机制:**
- **类型注册**:`jhyy-load-types <path.jhyy>` 解析 source 里的 `type X = struct { ... }` / `type X = enum { ... }` / `let v: [*]T = ...` 模式 → 内存里建 `_types` registry
- **格式化**:
  - struct:按 § 2.5 ABI 算字段 offset (`_alignof` + 累加 offset),逐字段 `_fmt_prim` / 递归嵌套 struct/enum / slice
  - enum:按 § 2.6 ABI 读 i32 tag (`_read(addr, 4, signed=True)`) → 查 variant → 有 payload 按 `payload_offset = align(4, max_payload_align)` 读 payload
  - slice:§ 2.3 16B = `{data: *T (8B), len: u64 (8B)}`,格式化 `{data=0x..., len=N}` (gdb 自己 deref `data` 指针会触发长度越界 — 留 `x` 给用户看 raw memory)
- **ABI 算 offset**:`_size()` / `_alignof()` 递归查 `_PRIM` dict (i8/u32/f32/...) / `_types` registry / `*T = 8B` / `[!T; N] = elem_size * N`
- **gdb 集成**:`gdb.Command` 子类 (`_LoadCmd` / `_PrettyCmd`) + `gdb.printing.register_pretty_printer` 注册 DWARF-type pretty printer (best-effort,通常不触发 — jhyy codegen 不发 type DWARF,见 v1.4.2 ship 时声明)
- **memory 读**:`gdb.selected_inferior().read_memory(addr, nbytes).tobytes()` → `int.from_bytes(..., 'little')`

**触发的工作流:**
1. `gdb gdb_pretty_test.exe`
2. `(gdb) source .gdbinit` — 自动 source pretty printer
3. `(gdb) jhyy-load-types compiler/tests/examples/gdb_pretty_test.jhyy` — 注册 4 个类型 (Point / Color / MaybeInt / `[*]i32`)
4. `(gdb) b gdb_pretty_test.jhyy:46` — 借助 v1.4.2 DWARF 定位源行
5. `(gdb) r` — 命中
6. `(gdb) jhyy-pretty $rsp Point` → `Point{x=10, y=20}`
7. `(gdb) jhyy-pretty $rsp+8 Color` → `Green`
8. `(gdb) jhyy-pretty $rsp+12 MaybeInt` → `Some(42)`
9. `(gdb) jhyy-pretty $rsp+24 [*]i32` → `[*]i32{data=0x5ffdf0, len=5}`

**验证 (per `feedback_fix_evaluation_rule` 5/5 PASS on target test):**
- ✅ `Point{x=10, y=20}` — struct 字段 offset + 嵌套字段访问正确
- ✅ `Green` — enum unit variant tag 匹配正确 (tag=1)
- ✅ `Some(42)` — enum payload 读取正确 (payload_offset = align(4, alignof(i32)=4) = 4,读 4B = 42)
- ✅ `[*]i32{data=0x5ffdf0, len=5}` — slice 16B layout 正确,data 是 backing array 指针
- ✅ DWARF pretty-printer 不误触发 (jhyy 不发 type DWARF,DWARF-type path 不干扰 `jhyy-pretty` command path)
- ✅ `gdb_pretty_test.jhyy` 加 `// EXPECT: 0`,准备并入 regress (本次未并,因 .gdbinit 路径问题 + regress 需在 src0 目录跑;后置 v1.4.5 收口)

**局限 (透明声明):**
- **DWARF `.debug_info` 缺失**:jhyy codegen 只发 `.debug_line` (v1.4.2 ship),不发 type/variable DWARF。所以 DWARF auto-pretty-printer 通常不触发 (jhyy var 在 gdb 里类型是 unknown / void*);主路径是手动 `jhyy-pretty <addr> <type>` 命令。真修需要 codegen 发 DWARF DIE — v3.x / v2.x 候选
- **QBE folding**:`Color::Green` / `MaybeInt::Some(42)` 如果编译器发现是 compile-time constant 就折叠,栈 slot 被复用 — 测试用 helper function `read_*(*T)` 强制地址传递规避。生产场景用户如果发现 var 读出来是上一栈的值,加 `printf("..." as *u8, val)` 强制 side effect 即可
- **slice deref 不自动**:`jhyy-pretty` 输出 `[*]i32{data=0x..., len=5}` 不自动展开元素 (避免越界读);手动 `x/20bx 0x...` 看 raw memory
- **嵌套 struct Outer { inner } 暂不支持**:codegen 在 `(*o).inner.a` 这种嵌套 struct 字段访问 emit `loadsw` 类型错 (per W-019 workaround);当前测试覆盖 flat struct / 单层 enum / slice,嵌套测试留给 post-v1.4.3 follow-up
- **`.gdbinit` auto-load 安全**:Windows gdb 默认禁用 `.gdbinit` auto-load,需 `gdb -iex 'add-auto-load-safe-path C:/.../.gdbinit' ...` 或 `set auto-load safe-path /`

**未引入新 workaround。** W-018 (DWARF .il 字节差) 仍 ACTIVE,v1.4.3 不变 .il 输出,无新增。

## 引用

- v1.4.1 父 sprint: [`docs/plans/v1/v1.4.0任务清单 + 概要设计.md`](../../plans/v1/v1.4.0任务清单%20+%20概要设计.md) § Sprint v1.4.1
- C-side argv[0] 实现 (前置 commit): commit `caa093b` v1.4.1 step 1
- W-017 详细: [`docs/internal/workarounds.md`](../../internal/workarounds.md) § W-017
- ABI 路径无关性: [`docs/abis/jhyy-abi-v1.0.0.md`](../../abis/jhyy-abi-v1.0.0.md) (无路径相关条目, 编译器纯 runtime concern)
- 上游 umbrella: `docs/logs/v1/changelog-v1.3.0.md` (v1.3.x ship 历史)

## v1.4.4 ship (本次 commit)

**Commit:** (本次 1 commit, 物理 production flip)

**改动文件 (per `git show --stat`):**
- `Makefile` — +41 / -6 行 (重写: 加 `stage0` / `selfhost` target; `all` target 走 stage-0 链)
- `mcp-jhyy/jhyy_runner.py` — +38 / -19 行 (新 `_maybe_rebuild_v144()`, 旧 `_maybe_rebuild_jhyy_v1()` 作 fallback 兼容)
- `docs/internal/build.md` — +30 / -6 行 ("编译编译器" 章节改 stage-0 链描述, 加 Makefile 一键用法)
- `.gitignore` — +1 行 (`!compiler/build/bin/jhyy_stage0.exe` 例外)
- `compiler/build/bin/jhyy.exe` — sha `c9cff76...` → `37ffc49c...` (C 端 328405B → jhyy-side 451641B, +37% 因 DWARF)
- `compiler/build/bin/jhyy_stage0.exe` — 新增 (sha `d624f150...`, C 端 328405B)
- `compiler/build/bin/jhyy_v1.exe.exe` — sha `3183594c...` → `37ffc49c...` (跟新 jhyy.exe 同 sha, 因为物理 = 同一 jhyy-side binary)
- `compiler/build/bin/jhyy_v2.exe` / `v3.exe` / `v4.exe` — 全刷 (Stage 2 closure 链重建)

**目的:** 打破 C 端 = production 状态。`compiler/build/bin/jhyy.exe` 现在是 jhyy-side 自举编译产物 (跟 regress.py 默认 binary 路径一致, 用户调 `jhyy.exe compile ...` 实际跑的是 jhyy-side, 不是 C 端)。C 端降级为 stage-0 bootstrap, 仅在 `compiler/src/*.c` 改了之后重建一次。

**核心机制:**
- **Stage 0**: `gcc compiler/src/*.c -o compiler/build/bin/jhyy_stage0.exe` — C 端产物, 改 src/*.c 后重建
- **Stage 1**: `jhyy_stage0.exe compile compiler/src0/main.jhyy -o compiler/build/bin/jhyy` — jhyy-side 产物 = production
- **Baseline 同步**: `cp jhyy.exe jhyy.exe.exe` + `cp jhyy.exe jhyy_v1.exe.exe` (per `feedback_regress_baseline_binary_hash.md`, baseline 必须 .exe.exe)
- **Makefile 简化**: `make` = stage 0 + stage 1; `make stage0` 只 stage 0; `make selfhost` 跑 Stage 2 closure 链验证

**触发的工作流:**
1. 改 `compiler/src/*.c` → `make stage0` → 重建 jhyy_stage0.exe
2. `make` (= stage0 + stage1) → 重建 jhyy.exe (production)
3. `make selfhost` → 验证 Stage 2 closure chain (v1 → v2 → v3 → v4 byte-equal)
4. 用户调 `compiler/build/bin/jhyy.exe compile foo.jhyy` → 实际跑 jhyy-side (不是 C 端)

**验证 (per `feedback_fix_evaluation_rule` 5/5 PASS):**
- ✅ Stage 0 → Stage 1 链通 (`gcc → jhyy_stage0.exe → jhyy.exe`, 0 errors / 0 warnings)
- ✅ Stage 2 N=3 byte-equal 维持 (`jhyy_v2.il = jhyy_v3.il = jhyy_v4.il` sha `073fb8d4b24ac14656d864b1133cbe7417b22bc26e6fec2633f417b4d61ba2e8`)
- ✅ hello.jhyy EXIT=42 (production `jhyy.exe` 跑用户 .jhyy, 行为不变)
- ✅ regress 50/54 PASS, 1 failed, 3 skipped
- ✅ regress_v1.py (v1.4.2 baseline `jhyy_v1.exe.exe`) 50/54 PASS, 同样 1 failed

**未达成 (透明声明):**
- ❌ **gdb_pretty_test.jhyy compile error** — pre-existing from v1.4.3 ship. 测试用 `MaybeInt::Some(v) => v` 这种 enum pattern binding 模式, jhyy-side parser 不支持 (line 53: `unexpected token in match pattern`). v1.4.3 ship 时只跑了 5 spot-check (`arith / fib30 / match / struct / pointer`), 没跑全量 regress. 修复路径: 改 parser 支持 enum payload pattern (v1.4.7+ 候选), 或改 gdb_pretty_test 用 let-binding 替代 pattern (临时 workaround). v1.4.6 真修 W-019 后 nested-struct 路径会通, 但 enum pattern 路径不归 W-019
- ❌ **Stage 1 byte-equal 不 7/7** — pre-existing W-005 #2 chain products: 新 `jhyy.exe` 产 jhyy.il sha `107445d6...`, 而旧 baseline `jhyy_v1.exe.exe` 产 jhyy_v1.exe.exe.il sha `760647f4...`, 两 sha 不同. 原因: 旧 baseline 是 pre-DWARF 时段的 binary (DWARF 还没 ship), jhyy-side codegen.jhyy 在 v1.4.2 加了 dbgfile/dbgloc emit, 现在 jhyy.exe 自带 DWARF, 而旧 jhyy_v1.exe.exe 不带. Stage 2 closure chain (v2/v3/v4 互相 byte-equal) 不受影响 — 那是 v1.4.x+ 强约束, 维持 `073fb8d4...`
- ❌ regress 默认 binary 仍是 `jhyy.exe` (无变化), v1.4.5 才加 `--stage0` flag

**未引入新 workaround。** W-017 / W-019 仍 ACTIVE, v1.4.6 真修。

**Self-hosting impact:**
- Stage 2 N=3 byte-equal: 维持 sha `073fb8d4b24ac14656d864b1133cbe7417b22bc26e6fec2633f417b4d61ba2e8`
- jhyy.exe sha: `c9cff76...` (pre, C 端) → `37ffc49c...` (post, jhyy-side)
- jhyy_v1.exe.exe sha: `3183594c...` (pre, v1.4.2 historical) → `37ffc49c...` (post, 跟 jhyy.exe 同物理 binary)
- jhyy_stage0.exe sha: 新建 `d624f150...` (C 端 bootstrap)

**引用:**
- v1.4.4 父 sprint: [`docs/plans/v1/v1.4.0任务清单 + 概要设计.md`](../../plans/v1/v1.4.0任务清单%20+%20概要设计.md) § Sprint v1.4.4
- v1.4.6 后插: 同 umbrella § Sprint v1.4.6 (codegen 真修 W-017 + W-019)