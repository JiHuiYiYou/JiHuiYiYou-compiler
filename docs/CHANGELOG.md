# JHYY Changelog Index

> **Entry point**: 找具体版本变更看下面 per-version changelog。Umbrella changelog 包含 sprint 状态总览 + 关键数字 + 决策点 + 跨 sprint 影响。
>
> **轴约定**: `vX.Y.Z` semver; **v0.x** = C 编译器自身 (frozen at v1.0.0 baseline), **v1.x** = jhyy 自举 (v1.8.3 = v1.x FINAL), **v2.x** = QBE 重写 + multi-target (v2.0 阶段 ✅ ship 2026-09-04, v2.x 中/末 ⏳ 未启动), **v3.x** = 语言扩展 (next, v3.0 3a-3f 等 user 启动)。
>
> **Author / Co-author / No date / 5/5 PASS / Audit single commit / Doc fact-check** 等规则 per 项目根 `CLAUDE.md` + `feedback_*` 系列。

---

## v1.x — jhyy 自举 (FINAL = v1.8.3)

| Version | Date | Umbrella Changelog | 摘要 |
|---------|------|--------------------|------|
| **v1.8.3** | 2026-08-29 | [`logs/v1/changelog-v1.8.0.md`](logs/v1/changelog-v1.8.0.md) | installer v1.8.3 WiX + UCPD.sys bypass; v1.x 终结文档整理 + Round 2 复检修复 |
| v1.8.2 | 2026-08-28 | [`logs/v1/changelog-v1.8.0.md`](logs/v1/changelog-v1.8.0.md) | Win10 Feb 2024+ UCPD.sys Deny ACE bypass + 4-layer file assoc cleanup |
| v1.8.1 | 2026-08-28 | [`logs/v1/changelog-v1.8.0.md`](logs/v1/changelog-v1.8.0.md) | jhyy-setuc.exe reverse-engineered Mozilla 算法 (C# port) |
| v1.8.0 | 2026-08-28 | [`logs/v1/changelog-v1.8.0.md`](logs/v1/changelog-v1.8.0.md) | W-059 defer codegen 真修 + W-060/W-061 INVALID 闭环 (1 行 fix) |
| v1.7.3 | 2026-08-28 | (per `git show 57f89dc`) | 32 candidates 完整 ship (Stage 1-5 + v1.7.1/2/3 patches), spec v1.3.0 locked = v1.x FINAL marker |
| v1.7.0 | 2026-08-15 | [`logs/v1/changelog-v1.7.0.md`](logs/v1/changelog-v1.7.0.md) | EXPECT-ERROR annotation + Stage 1-4 |
| v1.6.0 | 2026-08-13 | [`logs/v1/changelog-v1.6.0.md`](logs/v1/changelog-v1.6.0.md) | regress.py 收口 + baseline binary tracking |
| v1.5.x | 2026-08-12 → 2026-08-27 | [`logs/v1/changelog-v1.5.0.md`](logs/v1/changelog-v1.5.0.md) | RunOnce auto-install VSCode ext (v1.5.10); 多次 patch |
| v1.4.x | 2026-08-11 → 2026-08-13 | [`logs/v1/changelog-v1.4.0.md`](logs/v1/changelog-v1.4.0.md) | argv[0] 推项目根 + W-019/W-020 真修 + jhyy_v1.exe.exe canonical |
| v1.3.0 | 2026-08-10 | [`logs/v1/changelog-v1.3.0.md`](logs/v1/changelog-v1.3.0.md) | spec 增量 + slice 文档 |
| v1.2.x | 2026-08-09 → 2026-08-10 | [`logs/v1/changelog-v1.2.0.md`](logs/v1/changelog-v1.2.0.md) | jhyy_v1.exe + mcp-jhyy/server.py 整合 |
| v1.1.0 | 2026-08-08 | [`logs/v1/changelog-v1.1.0.md`](logs/v1/changelog-v1.1.0.md) | Stage 1-3 起步 |
| **v1.0.0** | 2026-08-10 | [`logs/v1/changelog-v1.0.0.md`](logs/v1/changelog-v1.0.0.md) | 真自举 byte-equal 闭环 (Stage 2 N=3) — jhyy 编 jhyy 里程碑 |
| v1.0.0-rc | 2026-08-09 | [`logs/v1/changelog-v1.0.0-rc.md`](logs/v1/changelog-v1.0.0-rc.md) | RC 候选 |

> **v1.x 终结** (2026-08-29): W-019/W-020 ACTIVE workaround 真修 + 11 个 W WIP/INVALID 闭环 + spec/abi locked. ACTIVE workaround 数 = 0. **v2.0 阶段已 ship** (2026-09-02 ~ 09-04, 5 版本串行 per 2026-09-01 user 决定),下一步 = **v3.0 3a-3f** 等 user 启动;v2.x 中/末 ‖ v3 全线 异步并行 — 见 [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](plans/roadmap/v2-v3-parallel-sprint-plan.md) + [`docs/plans/v2/v2.0.0-os-prep.md`](plans/v2/v2.0.0-os-prep.md).

---

## v0.x — C 编译器自身 (frozen at v1.0.0 baseline)

| Version | Date | Changelog | 摘要 |
|---------|------|-----------|------|
| v0.9.0-wip | 2026-08-07 | [`logs/v0/changelog-v0.9.0.md`](logs/v0/changelog-v0.9.0.md) | wip commit 2.83 收尾 (frozen) |
| v0.8.0 | 2026-08-04 | [`logs/v0/changelog-v0.8.0.md`](logs/v0/changelog-v0.8.0.md) | 结构体按值传 + 多文件 + FFI |
| v0.7.0 | 2026-08-02 | [`logs/v0/changelog-v0.7.0.md`](logs/v0/changelog-v0.7.0.md) | break-continue + 切片 + 命名空间 |
| v0.6.x | 2026-07-25 → 2026-08-01 | [`logs/v0/changelog-v0.6.0.md`](logs/v0/changelog-v0.6.0.md) + 后续 patch | jhyy_v0.exe 自举门槛达成 (v0.6+) |
| v0.5.x | 2026-07-15 → 2026-07-24 | [`logs/v0/changelog-v0.5.0.md`](logs/v0/changelog-v0.5.0.md) | ABI 1.0.0 锁定准备 |
| v0.4.x | 2026-07-01 → 2026-07-14 | [`logs/v0/changelog-v0.4.0.md`](logs/v0/changelog-v0.4.0.md) | struct 字段 + 嵌套类型 |
| v0.3.x | 2026-06-22 → 2026-06-30 | [`logs/v0/changelog-v0.3.0.md`](logs/v0/changelog-v0.3.0.md) | 表达式 + 控制流 |
| v0.2.1 | 2026-06-21 | [`logs/v0/changelog-v0.2.1.md`](logs/v0/changelog-v0.2.1.md) | Lexer + Parser |
| v0.0.1 | 2026-06-20 | [`logs/v0/changelog-v0.0.1.md`](logs/v0/changelog-v0.0.1.md) | 项目骨架 |

> **v0.x frozen**: 自 v1.0.0 真自举 ship 后, `src/*.c` + `compiler/src0/` 仅做 critical 维护, 不加新功能. v2.x 末 QBE 自写 + v3.x 末 runtime 重写后, 一次性删 `src/*.c` + untrack QBE + 删 runtime.c, 完成 "jhyy 编 jhyy" 0 C 依赖闭环 — 见 [`docs/plans/roadmap/v1.x-phase-4-m5-boot-from-scratch.md`](plans/roadmap/v1.x-phase-4-m5-boot-from-scratch.md) (M5 推迟决策 2026-08-14).

---

## v2.x — QBE 重写 + multi-target (v2.0 阶段 ✅ ship 2026-09-04)

| Version | Date | Umbrella Changelog | 摘要 |
|---------|------|--------------------|------|
| **v2.4.0** | 2026-09-04 | [`logs/v2/changelog-v2.4.0.md`](logs/v2/changelog-v2.4.0.md) | 多目标 dispatcher 完整化 + byte-equal 三件套 (`gcc -g0 -Wl,--build-id=none` + `SOURCE_DATE_EPOCH`) + D26 reproducibility recipe; tag `v2.4.0` commit `7fb735b` |
| **v2.3.0** | 2026-09-04 | [`logs/v2/changelog-v2.3.0.md`](logs/v2/changelog-v2.3.0.md) | hello-freestanding.efi 跑 OVMF 5/5 PASS — QEMU + OVMF (q35) + FAT12 image + serial capture; tag `v2.3.0` commit `54d93df` |
| v2.2.0 | 2026-09-03 | [`logs/v2/changelog-v2.2.0.md`](logs/v2/changelog-v2.2.0.md) | spec 锁定: lang-spec § 17-20 (OS 启动前置 + freestanding + Debug + Wire); abi § 13/14 restructure; build.md multi-target dispatch update |
| v2.1.0 | 2026-09-03 | [`logs/v2/changelog-v2.1.0.md`](logs/v2/changelog-v2.1.0.md) | QBE-level ABI 抽离: `abi_amd64_win_freestanding` UEFI PE/COFF + codegen dispatch + freestanding .obj 编出 |
| v2.0.0 | 2026-09-02 | [`logs/v2/changelog-v2.0.0.md`](logs/v2/changelog-v2.0.0.md) | target dispatcher 起步 (`Sprint A Stage 1`): `--target=amd64_win` / `amd64_win_freestanding` / `amd64_sysv_stub` CLI 三件套 |

> **v2.0 阶段 ship 走完** (2026-09-04): 5 版本串行 (v2.0.0 → v2.4.0),per 2026-09-01 user 决定。Stage 2 N=4 closure sha `51376ce5...` (re-baselined per D43);regress baseline 104/104 PASS + 4 SKIP;hello-freestanding.efi E2E 5/5 PASS on OVMF;`build-efi.sh` + `run-ovmf.sh` + `install-freestanding-toolchain.sh` 工具链就位;**amd64_sysv 仍是 fatal stub**(per 2026-09-04 user 决定,留 v2.x 中期自写 QBE 后端时实 impl)。下一步 = **v3.0 3a-3f** 等 user 启动;v2.x 中/末 (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point / peephole) 跟 v3.x 异步并行。

---

## 跨版本影响 / Sprint 索引

- **当前 sprint**: 🟢 无活跃 sprint (v2.0 阶段 5 版本 ship 完毕 2026-09-02 ~ 09-04, tags `v2.3.0` / `v2.4.0`)
- **下一阶段**: **v3.0 3a-3f** 等 user 启动 (inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` 软 ship);v2.x 中/末 ‖ v3 全线 异步并行
- **Sprint 设计入口**: [`plans/roadmap/`](plans/roadmap/) (L1) → `plans/v0/v0.X.0任务清单 + 概要设计.md` / `plans/v1/v1.X.0任务清单 + 概要设计.md` (L3) → L4 详细实现方案
- **OS 准备清单**: [`plans/v2/v2.0.0-os-prep.md`](plans/v2/v2.0.0-os-prep.md) (M1-M11 硬前置 + 跨项目时间线)

## Changelog 编写约定 (per `feedback_changelog_umbrella.md`)

1. **vX.Y 轴只 1 个 umbrella changelog** — 不创建 `changelog-vX.Y.Z.md` / `changelog-vX.Y.Z-wNNN.md` 之类 standalone 文件
2. **Umbrella 包含**: 承接上版本 + 触发原因 + scope 决策 + sprint 状态总览表 + 关键数字表 + 决策点 + 跨 sprint 影响
3. **Patch 版本** (vX.Y.Z where Z>0) — 内容回填到 vX.Y 的 umbrella changelog (e.g. v1.7.1/2/3 → [`changelog-v1.7.0.md`](logs/v1/changelog-v1.7.0.md))
4. **Doc fact-check** per `feedback_doc_refactor_factcheck` — 重构前逐条核对限制是否仍存在 / 是否已 ship / 是否措辞过时