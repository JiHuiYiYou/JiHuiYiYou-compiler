# Changelog

> **入口**:GitHub Release / 包管理器 / cache 层从这个文件读版本号。具体变更看 [`docs/CHANGELOG.md`](docs/CHANGELOG.md) (完整索引) → [`docs/logs/v*/changelog-vX.Y.{0,md}`](docs/logs/) (per-version umbrella)。

## 最新 release

### v2.11.8 — 2026-09-13 — **axis-v2 W-074.7.8 真修 — 4/5 EXIT exact closure** (axis-v2 only; main 待 merge)

**Tag**: `v2.11.8` (axis-v2 branch)
**Status**: W-074.7.8 derived-address tracking **PARTIAL closure** (4/5 EXIT exact); big_test runtime STATUS_INTEGER_OVERFLOW 0xC0000095 deferred v2.11.9+ (W-074.7.9 NEW)

**Highlights**:

- **Derived-address tracking 真修** — bitmap flag 任何 temp holding derived address (alloc-result + binop add/sub on pointer + copy of address-holder); emit_load/store/loadsub 改 full dispatch (slot vs indirect `mov<size> (%r8), %reg` via %r8 scratch); emit_binop 产生 derived-address 时 flag result; emit_copy propagate flag (TEMP + FNARG paths)
- **Self-referential slot bug 真修** — v2.11.5 design 让 pointer-slot == region offset, lea+mov 自我覆盖;真修 SKIP `cg_record_temp_slot`, pointer-slot 走 formula `-(32+t*8)` Win (formula 跟 region 物理分离)
- **FNARG flag propagate** — l-typed fnarg (struct param pointer) 走 FNARG path 不 flag propagate → struct_val_pass EXIT 6→35 flip 真修
- **byte-equal 五件套 4/5 EXIT exact closure**:
  - hello=42 ✅ (跟 baseline 一致)
  - fib_renamed=40 (= 832040 mod 256, 跟 baseline 一致) ✅
  - struct_val_pass=35 (从 v2.11.6 EXIT=6 → v2.11.8 EXIT=35, 真修 closure) ✅
  - nested_struct_deep=22 (从 v2.11.6 EXIT=35 → v2.11.8 EXIT=22, 真修 closure) ✅
  - struct_val_assign=30 ✅ (跟 baseline 一致)
  - big_test = STATUS_INTEGER_OVERFLOW 0xC0000095 ⚠️ (separate deeper bug, **deferred v2.11.9+ W-074.7.9 NEW**)
- **QBE fallback 115/115 PASS preserved** + **self-backend 5/5 link preserved** (v2.11.6 closure 不 regress)
- **self-backend regress +2 flips** (56/115 → 58/115, 远低于 +5 scope DOWN trigger per [[feedback_codegen_amd64_multifn]])
- **D43 closure v1↔v2 .il sha HOLD** (v2/v3/v4/v5 sha = `3f0bfb...` 一致) + **byte_equal_amd64 10/10 PASS preserved** + **fixed_point N≥3 PASS preserved**
- **NEW ship gate per [[feedback_codegen_amd64_run_zerobyte]]**: `main_jhyy.s` = 12 行 / 207 bytes (≥ 100 bytes 阈值, ≥ baseline, no truncation)
- **jhyy.exe.sha256 refresh**: `883680d966cc79a9bf4e7df851e2441fb8bd9fbfe1a0924cc9adaa38c1dca13a`

**完整 changelog**: [`docs/logs/v2/changelog-v2.11.0.md`](docs/logs/v2/changelog-v2.11.0.md) § v2.11.8
**Plan**: [`docs/plans/v2/v2.11.8-plan.md`](docs/plans/v2/v2.11.8-plan.md)

---

### v2.0 阶段 — 2026-09-04 — **v2.0 阶段全 ship ✅**

**Tags**: `v2.3.0` (commit `54d93df`) + `v2.4.0` (commit `7fb735b`); 阶段内 v2.0.0 / v2.1.0 / v2.2.0 未打 tag (per 2026-09-01 user 决定:阶段首批 ship 即可打 tag)
**Status**: v2.0 阶段 (v2.0.0 → v2.4.0) 全 ship;下一步 = **v3.0 3a-3f** (inline asm / `#[naked]` / volatile / `#[link_section]` / memory barrier / `#[no_std]` 软 ship) 等 user 启动;v2.x 中/末 ‖ v3.x 异步并行。

**Highlights**:

- **Multi-target dispatcher** — `jhyy compile --target=amd64_win` / `--target=amd64_win_freestanding` / `--target=amd64_sysv_stub`(stub fatal,推 v2.x 中/末)
- **hello-freestanding.efi 跑 OVMF 5/5 PASS** — QEMU + OVMF (q35 machine) 启动 + FAT12 image + serial capture;ConOut->OutputString 间接调用通过 efi_call_via_ptr
- **spec 锁定**: lang-spec § 17-20 (OS 启动前置 + freestanding + Debug + Wire); abi § 13/14 (Multi-target ABI + wire types)
- **byte-equal 三件套** — `.il + .s + .exe` 三层 byte-equal 跨 jhyy_v1 ↔ jhyy_v2;D26 reproducibility recipe (`gcc -g0 -Wl,--build-id=none` + `SOURCE_DATE_EPOCH=1234567890` via `jh_setenv`)
- **Stage 2 N=4 closure re-baselined** — sha `51376ce5...` (per D43 阶段性 self-equal hold,v2.4.0 Stage 1+2 触发 src0 emit 微变 → 重 baseline)
- regress baseline 104/104 PASS + 4 SKIP (108 total)
- ACTIVE workaround 数 → 0;W-057 / W-058 仍 DEFERRED-to-v2.x 中/末(QBE 自写时修)

**完整 changelog**: 5 个 umbrella = [`docs/logs/v2/changelog-v2.0.0.md`](docs/logs/v2/changelog-v2.0.0.md) / [v2.1.0](docs/logs/v2/changelog-v2.1.0.md) / [v2.2.0](docs/logs/v2/changelog-v2.2.0.md) / [v2.3.0](docs/logs/v2/changelog-v2.3.0.md) / [v2.4.0](docs/logs/v2/changelog-v2.4.0.md)

---

### v1.8.3 — 2026-08-29 — **v1.x FINAL** 🎯

**Tag**: `v1.8.3` `98c8272`
**Status**: v1.x 终结,v0.9 wip 冻结;v2.0 阶段 ship ✅ 走完 (2026-09-04),下一步 = v3.0 3a-3f 等 user 启动。

**Highlights**:

- **Stage 2 N=4 byte-equal 自举闭环稳定** — `jhyy_v1 → v2 → v3 → v4 → v5` 产出 byte-equal `.il` (sha `03a1cdd4...` v1.8.0 → `51376ce5...` v2.4.0 re-baseline)
- **Installer v1.8.3 WiX** — UCPD.sys Deny ACE bypass + Windows 文件关联 4 层清理 (HKCR + UserChoice + OpenWithProgids + jhyy_auto_file ProgId)
- **`jhyy-setuc.exe`** reverse-engineered Mozilla UCPD Hash 算法 (C# port),try/finally UCPD restart
- **v1.7.x 32 candidates 完整 ship**(Stage 1-5 + v1.7.1/2/3 patches)
- **spec v1.3.0 锁定** = v1.x FINAL marker; ACTIVE workaround 数 = 0

**完整 changelog**:[`docs/logs/v1/changelog-v1.8.0.md`](docs/logs/v1/changelog-v1.8.0.md) (umbrella)

## 版本轴速览

| 轴 | 范围 | 当前状态 |
|---|---|---|
| **v0.x** | C 编译器自身 (`compiler/src/*.c`) | 🟢 frozen at v1.0.0 baseline |
| **v1.x** | jhyy 自举 (`compiler/src0/*.jhyy`) | 🟢 **v1.8.3 shipped = v1.x FINAL** |
| **v2.x** | QBE 完整重写 + amd64_sysv / freestanding | ✅ **v2.0 阶段 ship** (2026-09-04, tags `v2.3.0` / `v2.4.0`); v2.x 中/末 ⏳ 未启动 (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point) |
| **v3.x** | 语言特性扩展 (inline asm / `#[no_std]` / `&mut` + lifetime) | ⚪ next (v2.0 阶段 ✅ ship, 3a-3f 等 user 启动) |

## v1.x ship 时间线

| Version | Date | Tag / Commit | Highlights |
|---------|------|--------------|-----------|
| **v1.8.3** | 2026-08-29 | `98c8272` | installer v1.8.3 WiX + UCPD.sys bypass |
| v1.8.2 | 2026-08-28 | — | Win10 Feb 2024+ UCPD.sys Deny ACE bypass + 4-layer file assoc cleanup |
| v1.8.1 | 2026-08-28 | — | `jhyy-setuc.exe` reverse-engineered Mozilla 算法 |
| v1.8.0 | 2026-08-28 | — | W-059 defer codegen 真修 + W-060/W-061 INVALID 闭环 |
| v1.7.3 | 2026-08-28 | `57f89dc` | 32 candidates 完整 ship; spec v1.3.0 locked |
| v1.7.0 | 2026-08-15 | — | EXPECT-ERROR annotation + Stage 1-4 |
| v1.6.0 | 2026-08-13 | — | regress.py 收口 + baseline binary tracking |
| v1.5.10 | 2026-08-27 | `c057aa3` | RunOnce auto-install VSCode ext |
| v1.0.0 | 2026-08-10 | `eabee0d` | 真自举 byte-equal 闭环 (Stage 2 N=3) — jhyy 编 jhyy 里程碑 |

**完整时间线 + 每版本 patch 详情**:`docs/CHANGELOG.md` (索引) → `docs/logs/v1/` (per-version umbrella changelog)

## 下一阶段

**v3.0 3a-3f** (语言扩展 OS-required) 等 user 启动 — v2.0 阶段 ✅ ship 走完(2026-09-04);**v2.x 中/末 跟 v3.x 异步并行**(QBE 自写 / amd64_sysv 实 impl / N 代 fixed point 仍待 v2.x 中/末) — OS 准备:

- 路线图: [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](docs/plans/roadmap/v2-v3-parallel-sprint-plan.md)
- OS 启动链路: [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md)
- 跨项目协调: [`../jhyy_OS/docs/coordination.md`](../jhyy_OS/docs/coordination.md)

## 编写约定

per `feedback_changelog_umbrella.md`:

1. **vX.Y 轴只 1 个 umbrella changelog** — 不创建 `changelog-vX.Y.Z.md` / `changelog-vX.Y.Z-wNNN.md` 之类 standalone
2. **Umbrella 包含**:承接上版本 + 触发原因 + scope 决策 + sprint 状态总览 + 关键数字 + 决策点 + 跨 sprint 影响
3. **Patch 版本**(vX.Y.Z where Z>0) 内容回填到 vX.Y 的 umbrella changelog
4. **本文件**(根 `CHANGELOG.md`) 是 GitHub Release / 包管理器入口,**不重复** `docs/CHANGELOG.md` 内容