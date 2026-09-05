# V3-A batch plan — v3.0.0 (3d `#[no_std]` 试水)

## Context

**Batch 范围**:V3-A 是 v3 axis 第一 batch,只含 1 个 sub-sprint(v3.0.0)。在 6 个 OS-required 语言扩展中,3d `#[no_std]` / `#![no_std]` 是最纯 AST-level 改动(per D10 软 ship,L1 友好)— 不动 codegen 主体逻辑,只加 attribute parsing + main_jhyy vs main 切换。

**V3-A 目的**:
1. 跑通 v3 axis dev workflow(ship → baseline → push → 进 V3-B)
2. 给 OS kernel 编写者一个最小可用 no_std 入口(panic_handler stub + 自定义 entry)
3. 验证"controller (v3 axis) 跟 producer (v2 axis) file 层零冲突"(per `feedback_no_subagents_for_compiler_work`)

**在 v3 axis 内位置**:
- v2 axis V2-A + V2-B + V2-C 是 v3 axis 完全并行(per 2026-09-01 user 决定)
- v3.0.0 = 3d no_std(本 batch)
- 后接 V3-B(v3.0.1 → v3.0.5 = 3a/3b/3c/3e/3f M1-required 5 件套)
- 后接 V3-C(v3.1.0 → v3.1.2 = 3g/3g.5/3g.7 D27 串行)

**上游依赖(全已 ship)**:
- v1.8.3 ✅ ship(v1.x FINAL,语言规范锁定)
- v2.0 阶段 ✅ ship(v2.0.0 → v2.4.0)
- 自举 baseline `51376ce5...`(v2.4.0 re-baselined per D43)

**跨 axis**:V3-A 不依赖 v2 axis 任何 sub-sprint;v2 axis 也不依赖 V3-A(no_std 软 ship per D10)。

## Sub-sprint 分解

### v3.0.0 (3d `#[no_std]` 试水 + core lib stub)

**Scope**:

#### Part 1: parser attribute 加 no_std 识别

1. `compiler/src0/parser.jhyy:2170` `parse_attributes` 加 `"no_std"` 匹配:
   ```jhyy
   if strcmp(aname, "no_std" as *u8) == (0 as i32) {
       is_no_std = 1 as i32;
   }
   ```
   共 ~6 行新增(已有 `inline` 模式旁路加)
2. `parse_attributes` 改返回签名 → `*ModuleAttr`(struct:`is_inline` + `is_no_std`),或者返回 `is_inline` + 改用全局 / 引用传出 no_std(向后兼容)
3. AST `ModuleAttr` struct 已有 `is_inline: i32`(per src0 当前);加 `is_no_std: i32` 字段(类似 inline 旁)

#### Part 2: sema + codegen 传递 + emit 切换

1. `compiler/src0/sema.jhyy`(改):
   - `ModuleAttr` 沿 parser → sema → codegen 传(CGContext 加 `is_no_std: i32` 字段,沿用 inline 路径)
   - `is_no_std = 1` 时校验:`fn main` 必须存在(per spec);`fn main_jhyy` **不**校验(无 runtime bridge)
2. `compiler/src0/codegen.jhyy:3764` `cg_module`(改):
   - `is_no_std == 1` → emit `.note.GNU-stack noalloc`(减少 stack probing 开销)
   - `is_no_std == 1` → entry symbol `main`(per SysV + MS x64 ELF/PE convention;**不**是 `main_jhyy`)
   - `is_no_std == 1` → skip `runtime.c` link line(只 link `<obj>` + `-nostartfiles -nodefaultlibs`)
   - `is_no_std == 0`(默认)— 维持原 `main_jhyy` + runtime bridge 路径
3. `compiler/src0/main.jhyy` link line 改动:
   - 加 `is_no_std` 检测(从 .jhyy 注释 / module attr 中读)— 实际通过 `cg_module` 写 `.note.GNU-stack` + cmd line 切 link args 双向确认
   - `is_no_std == 1` → gcc cmd 加 `-nostartfiles -nodefaultlibs`(MinGW gcc 支持;Linux gcc 支持)
   - `is_no_std == 0` → 维持 `-nostdlib` 或 default(per target)

#### Part 3: runtime + core lib stub

1. `compiler/runtime/runtime.c`(改,小):
   - `main` → `main_jhyy` bridge(已 ship,v1.4.4 物理 flip)保留
   - `is_no_std` 时 link line 不含 runtime.c → bridge **不**生效
2. `compiler/runtime/no_std_core/`(新,~80-100 行):
   - `panic_handler.jhyy`:`fn panic_handler() -> ! { loop {} }`(M0 stub;留 v3.x 中实现 panic message 打印)
   - `__start_kernel.jhyy`(或叫 `__jhyy_no_std_entry`):`fn __start_kernel() -> i32 { return call_main(); }` — 让 user `fn main()` 自动被调用
   - `memcpy.jhyy` + `memset.jhyy` stub(per byte loop)— 后期 v3.x 中可优化
   - 编译:`jhyy --target=amd64_win_freestanding --no-std-lib ...`
3. `tests/no_std_hello.jhyy`(新,~10 行):
   ```jhyy
   #[no_std]
   fn main() -> i32 {
       return 42 as i32;
   }
   ```
   验证:编出 0-runtime `.exe`,跑 EXIT:42

**Key files**:
- 改 `compiler/src0/parser.jhyy:2170`(`parse_attributes` 加 no_std 识别,~6 行)
- 改 `compiler/src0/sema.jhyy`(`ModuleAttr` 传递 + is_no_std 校验,~30 行)
- 改 `compiler/src0/codegen.jhyy:3764`(cg_module 加 is_no_std 分支 + entry 切换 + link flag,~30 行)
- 改 `compiler/src0/main.jhyy`(link line 加 `-nostartfiles -nodefaultlibs`,~20 行)
- 改 `compiler/runtime/runtime.c`(注释更新;不动逻辑)
- 新建 `compiler/runtime/no_std_core/panic_handler.jhyy`(~10 行 stub)
- 新建 `compiler/runtime/no_std_core/memcpy.jhyy` + `memset.jhyy`(~30 行 stub)
- 新建 `compiler/runtime/no_std_core/__start_kernel.jhyy`(~15 行 stub)
- 新建 `tests/no_std_hello.jhyy`(~10 行)
- 改 `docs/abis/jhyy-lang-spec-v1.X.0.md`(加 no_std 章节 — **不**改锁 spec 主体,加 appendix E 或 supplement doc)

**关键决策**:
- **软 ship per D10**(M1 launch 不依赖)— v3.0.0 ship 后观察 1-2 sprint 验证稳定性
- **`no_std` 是 module 级 outer attr**:syntax `#[no_std]` 在文件顶部(per 当前 `inline` 路径);**不**实现 inner attr `#![no_std]`(留 v3.x 中补)
- **panic_handler M0 stub**:`loop {}` 即可(满足 linker;后期 v3.x 中实现 panic message 打印)
- **memcpy / memset stub**:per byte loop(简单);后期 v3.x 中可换 SSE / AVX
- **0 外部依赖闭环**:`-nostartfiles -nodefaultlibs` + 自带 `__start_kernel` — 不依赖 libc / crt0
- **不**改锁 spec(`jhyy-lang-spec-v1.3.0.md`):写 `jhyy-lang-spec-no_std-supplement-v3.0.0.md` 作为 supplement doc;锁 spec 在 v3.x 中(下一版 spec)再合入

## 跨 axis 硬约束

- **D10** 软 ship:v3.0.0 不阻塞 M1 launch;可独立 ship 后观察
- **V2-A `codegen_amd64.jhyy` 文件层无冲突**:V3-A 只改 parser.jhyy + sema.jhyy + codegen.jhyy:cg_module(emit 主路径)+ main.jhyy(link line);codegen_amd64.jhyy 不动
- **3a-3f(V3-B)不依赖 3d**:no_std 是独立特性,跟 inline asm / naked / volatile / link_section / memory barrier 都无交集
- **D43** 阶段性 self-equal hold:v3.0.0 ship 必须 N=1 self-equal baseline 不变(no_std 默认 off,regress.py 全部测试都不带 `#[no_std]`,baseline 跟 v2.4.0 一致 `51376ce5...`)
- **不**改锁 spec:spec supplement 形式追加

## Batch ship gate

- `tests/no_std_hello.jhyy` 编出 `.exe`(0 runtime dep,只 link 自带 no_std_core);跑 EXIT:42
- 原 regress.py 104/104 PASS 不变(no_std 不影响 default path;默认 is_no_std=0)
- `mcp__jhyy__jhyy_regress` 报 104/104
- `mcp__jhyy__jhyy_selfhost_check` 报 N=1 byte-equal baseline `51376ce5...` 不变
- W-068 no_std workaround 文档登(if any;否则不登)
- `docs/abis/jhyy-lang-spec-no_std-supplement-v3.0.0.md`(新 supplement doc)写 no_std 语法 + 语义 + 示例
- `docs/logs/v3/changelog-v3.0.md` umbrella(per `feedback_changelog_umbrella`,v3.0 = V3-A + V3-B 5 sub-sprint 合并 1 个 umbrella)

## 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Spec 锁后追加 no_std → 改 spec 风险 | spec 锁定原则破坏 | 走 supplement doc 形式(spec body 不动);v3.x 中合入下一版 spec |
| Windows 链接 0-runtime .exe `-nostartfiles -nodefaultlibs` 失败 | ship gate 阻塞 | MinGW gcc 支持;测试 build 验证;fail 退回 `-nostdlib`(libc 仍可用) |
| panic_handler M0 stub `loop {}` 在 OS 启动失败时 hang | OS debug 难 | 接受 stub 局限;v3.x 中补 panic message 打印 |
| 内层 attr `#![no_std]` 不支持 | Rust 习惯写法不能直接抄 | 显式文档 outer attr `#[no_std]` 是 v3.0.0 唯一形式;inner attr 留 v3.x 中 |
| `cg_module` 加 is_no_std 分支影响 default path(0 不走,1 走) | regress 退步 | is_no_std=0 默认分支完全保持现状(regress 104/104 baseline 不变);is_no_std=1 仅 no_std_hello.jhyy 走 |
| Module attr 传递路径 bug | no_std 不到 codegen 端 | 沿用 inline 已有传递路径(inline 已 ship 稳定);no_std 加旁路 |

## Out of scope

- Inner attr `#![no_std]`(留 v3.x 中)
- `panic_handler` 完整实现(只 M0 stub)
- `memcpy` / `memset` SSE/AVX 优化(留 v3.x 中)
- `no_std` + `#[inline]` + `#[link_section]` 等组合(留 v3.x 中)
- inner attr 跟 outer attr 互斥 / 优先级(留 v3.x 中)
- 自定义 entry point(目前 hardcoded `main`;user 改 entry 留 v3.x 中)
- 3a inline asm(留 V3-B v3.0.1)
- 3b #[naked](留 V3-B v3.0.2)
- 3c volatile(留 V3-B v3.0.3)
- 3e #[link_section](留 V3-B v3.0.4)
- 3f memory barrier(留 V3-B v3.0.5)
- 3g &mut + lifetime(留 V3-C)

## 文件变更清单

### 新建
- `compiler/runtime/no_std_core/panic_handler.jhyy`(~10 行)
- `compiler/runtime/no_std_core/memcpy.jhyy`(~15 行)
- `compiler/runtime/no_std_core/memset.jhyy`(~15 行)
- `compiler/runtime/no_std_core/__start_kernel.jhyy`(~15 行)
- `tests/no_std_hello.jhyy`(~10 行)
- `docs/abis/jhyy-lang-spec-no_std-supplement-v3.0.0.md`(supplement,~80 行)
- `docs/logs/v3/changelog-v3.0.md`(umbrella,merge V3-A + V3-B 5 sub-sprint,初版 ~50 行预留)

### 改动
- `compiler/src0/parser.jhyy:2170`(`parse_attributes` 加 no_std 识别,~6 行)
- `compiler/src0/sema.jhyy`(`ModuleAttr` 传递 + 校验,~30 行)
- `compiler/src0/codegen.jhyy:3764`(cg_module 加 is_no_std 分支,~30 行)
- `compiler/src0/main.jhyy`(link line + entry 切换,~20 行)
- `compiler/runtime/runtime.c`(注释更新)
- `compiler/build/bin/regress.py`(无改动;no_std test 单独跑)
- `docs/internal/workarounds.md`(W-068 no_std workaround)

## Commit / tag 节奏

- **Commit 1**:`feat(parser): add no_std attribute recognition`(parser.jhyy 改动)
- **Commit 2**:`feat(codegen): add is_no_std path in cg_module + main.jhyy link line`(codegen + main.jhyy)
- **Commit 3**:`feat(runtime): add no_std_core stubs (panic_handler/memcpy/memset/__start_kernel)`
- **Commit 4**:`test: add tests/no_std_hello.jhyy + validate EXIT:42`
- **Commit 5**:`docs: no_std supplement + changelog-v3.0 reservation`
- **Tag**:`v3.0.0`(V3-A 单 sub-sprint ship 后 user 确认 → tag;V3-B ship 后 re-tag v3.0.1 等;per `feedback_changelog_umbrella` v3.0.x 整 axis 走 1 个 umbrella changelog)

## Cross-ref

- 后续 batch:`docs/plans/v3/batch-V3-B-plan.md`(v3.0.1 → v3.0.5 M1-required 5 件套)
- 后续 batch:`docs/plans/v3/batch-V3-C-plan.md`(v3.1.0 → v3.1.2 D27 串行)
- v2 axis:`docs/plans/v2/batch-V2-A-plan.md`(V2-A 自写后端不动,V3-A no_std 跟 V2-A 独立)
- 跨项目 M 节点:`docs/plans/v2/v2.0.0-os-prep.md § 1 M1`(M1 launch 不依赖 3d,per D10)
- Spec 锁:`docs/abis/jhyy-lang-spec-v1.3.0.md` — V3-A **不**改,加 supplement
