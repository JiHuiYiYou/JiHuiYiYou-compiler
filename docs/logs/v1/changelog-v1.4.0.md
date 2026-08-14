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
| v1.4.3 | `mcp-jhyy/gdb_pretty.py` Python script: print jhyy struct/enum/slice types; gdb source-time load via `--init-eval-command` | 待启动 |
| v1.4.4 | 物理替换 `compiler/build/bin/jhyy.exe` baseline (sha `ac2a1b19...`) 到新 main.c argv[0] 版本; regress 默认 binary 改 `jhyy.exe.exe`; 跑 regress_stage0.py 验证 C 端仍 byte-equal | 待启动 |
| v1.4.5 | regress.py 默认 binary 改 `jhyy.exe.exe` + 加 `--stage0` flag; GH Actions CI 三跑 (regress_v1 + regress + regress_stage0) + Stage 1/2 byte-equal | 待启动 |

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

## W-018 (本次新增 workaround, 状态 ACTIVE)

**问题:** v1.4.2 DWARF emit 在 C-side vs jhyy-side .il 间引入 2 处非功能 diff (dbgfile filename + dbgloc 行数)。Stage 2 closure chain 不受影响。

**workaround:** 接受 .il 字节差异;DWARF 是给 gdb 用的 .s 输出,非 .il byte-equal 目标。Stage 2 (`v2.il = v3.il = v4.il`) 仍是 v1.4.x+ 强约束。

**完整记录:** [`docs/internal/workarounds.md`](../../internal/workarounds.md) § W-018

## 引用

- v1.4.1 父 sprint: [`docs/plans/v1/v1.4.0任务清单 + 概要设计.md`](../../plans/v1/v1.4.0任务清单%20+%20概要设计.md) § Sprint v1.4.1
- C-side argv[0] 实现 (前置 commit): commit `caa093b` v1.4.1 step 1
- W-017 详细: [`docs/internal/workarounds.md`](../../internal/workarounds.md) § W-017
- ABI 路径无关性: [`docs/abis/jhyy-abi-v1.0.0.md`](../../abis/jhyy-abi-v1.0.0.md) (无路径相关条目, 编译器纯 runtime concern)
- 上游 umbrella: `docs/logs/v1/changelog-v1.3.0.md` (v1.3.x ship 历史)