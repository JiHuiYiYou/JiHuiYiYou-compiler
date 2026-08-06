# docs/logs/v0/ — C 编译器时代 changelog + sprint 实施日志

本目录放 **C 端编译器**（v0.x）时代的版本日志和 sprint 实施日志。

## 版本 changelog（按发布版本号）

| 文件 | 内容 |
|------|------|
| `changelog-v0.0.1.md` | 初版（早期实验）|
| `changelog-v0.2.1.md` | P0 修复 |
| `changelog-v0.3.0.md` | |
| `changelog-v0.4.0.md` | |
| `changelog-v0.5.0.md` | 自举前质量门禁 |
| `changelog-v0.6.0.md` | 自举前最后一期准备 |
| `changelog-v0.6.2.md` | patch：sprint 1 实测沉淀 3 个 codegen / sema bug |
| `changelog-v0.6.3.md` | patch：sprint 2 实测沉淀 #9 f64/f32 比较 + call-site 隐式 f64↔f32 转换 |
| `changelog-v0.6.5.md` | patch：sprint 3 实测沉淀 #2 let mut dead-code（sema 严格化）|
| `changelog-v0.6.4.md` | patch：sprint 2-3 过渡期实测沉淀 |
| `changelog-v0.8.0.md` | wip：自举路径清理（commit 1-12, 5820793 — Stage 0 closure 解锁）|
| `changelog-v0.9.0.md` | wip：W-005 真修 + Stage 1 byte-equal 6/7 持平 + 2 audit (AUDIT + C') (commit 1-2.17, 7691457) |

## Sprint 实施日志（早期 v0.1 时代）

v0.1 时代 sprint 用 `sprint-1[abc...]-*.md` 命名（v0.2.1 之后改用 `v0.X.Y任务清单 + 概要设计.md`）：
- `sprint-1a-lexer.md` … `sprint-1g-module-cli-tests.md`

## 关联

- C 端编译器 sprint 计划 → [`../../plans/v0/`](../../plans/v0/)
- vX.Y 轴路线图 → [`../../plans/roadmap/`](../../plans/roadmap/)
- jhyy 自举 changelog → [`../v1/`](../v1/)（v1.0.0 出后才有内容）