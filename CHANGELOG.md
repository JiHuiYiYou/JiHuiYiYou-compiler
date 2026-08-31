# Changelog

> **入口**:GitHub Release / 包管理器 / cache 层从这个文件读版本号。具体变更看 [`docs/CHANGELOG.md`](docs/CHANGELOG.md) (完整索引) → [`docs/logs/v*/changelog-vX.Y.{0,md}`](docs/logs/) (per-version umbrella)。

## 最新 release

### v1.8.3 — 2026-08-29 — **v1.x FINAL** 🎯

**Tag**: `v1.8.3` `98c8272`
**Status**: v1.x 终结,v0.9 wip 冻结,下一步 v2.x (QBE 重写) / v3.x (语言扩展) 并行启动。

**Highlights**:

- **Stage 2 N=4 byte-equal 自举闭环稳定** — `jhyy_v1 → v2 → v3 → v4 → v5` 产出 byte-equal `.il` (sha `03a1cdd4...`)
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
| **v2.x** | QBE 完整重写 + amd64_sysv / freestanding | ⚪ next (OS 准备) |
| **v3.x** | 语言特性扩展 (inline asm / `#[no_std]` / `&mut` + lifetime) | ⚪ next (与 v2.x 并行) |

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

**v2.x (QBE 重写)** + **v3.x (语言扩展)** 并行启动 — OS 准备:

- 路线图: [`docs/plans/roadmap/v2-v3-parallel-sprint-plan.md`](docs/plans/roadmap/v2-v3-parallel-sprint-plan.md)
- OS 启动链路: [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md)
- 跨项目协调: [`../jhyy_OS/docs/coordination.md`](../jhyy_OS/docs/coordination.md)

## 编写约定

per `feedback_changelog_umbrella.md`:

1. **vX.Y 轴只 1 个 umbrella changelog** — 不创建 `changelog-vX.Y.Z.md` / `changelog-vX.Y.Z-wNNN.md` 之类 standalone
2. **Umbrella 包含**:承接上版本 + 触发原因 + scope 决策 + sprint 状态总览 + 关键数字 + 决策点 + 跨 sprint 影响
3. **Patch 版本**(vX.Y.Z where Z>0) 内容回填到 vX.Y 的 umbrella changelog
4. **本文件**(根 `CHANGELOG.md`) 是 GitHub Release / 包管理器入口,**不重复** `docs/CHANGELOG.md` 内容