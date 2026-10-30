# FACTS — 事实单一真相源

> **本文件是仓内唯一记录「会变的数字」的地方。**
> 其它文档**引用**这里的值，**不复述**。
> 复述 = 下一个漂移源（本仓 2026-10-30 审计实测：一个回归数被写在 31 份文档里，
> 结果两份 README 徽章落后 8 个 release 而 CI 全绿）。
>
> **维护**：数字变了先改这里，再改引用它的地方。
> **自动校验**：`python scripts/dev/docs_facts_check.py`（CI 会跑）—— 它把这里的值
> 与 `VERSION` / 台账索引 / 门脚本 / 实际回归输出对拍，不一致就红。

---

## 1. 版本与发行产物

| 项 | 值 |
|---|---|
| 当前版本 | **4.1.2**（真相源 = 仓库根 `VERSION` 文件） |
| 最新 release | `v4.1.2`（2026-10-29） |
| 版本轴 | v0.x(C 编译器，冻结于 v1.0.0) · v1.x(自举，终结于 v1.8.3) · v2.x(QBE 重写，终结于 v2.16.0) · v3.x(语言扩展，终结于 v3.4.2) · **v4.x(当前)** |
| 编译器二进制 | `compiler/build/bin/jhyy.exe`（~1.9 MB） |

| 产物 | 体积 |
|---|---|
| `jhyy-installer-4.1.2.exe` | ~55 MB（GUI 安装器；含 .NET 8 Desktop Runtime + **内置 ucrt64 工具链**） |
| `jhyy-compiler-4.1.2.msi` | ~28 MB（企业 / SCCM 分发；含 `jhyy-setuc.exe` + 内置工具链） |
| `jhyy-lang-4.1.2.vsix` | VS Code 扩展 |

> 自 **v4.1.0** 起 installer 自带最小原生 ucrt64 工具链 ⇒ **最终用户不需要 MSYS2**。

---

## 2. 回归与门

| 门 | 值 |
|---|---|
| `python regress.py` | **259 PASS + 0 XFAIL + 0 failed + 20 SKIP**（279 total） |
| 断言强度审计 | 扫描 279 · 可跑 259 · 真断言 200 · literal-return-ok 8 · expect-error 51 · skipped 6 · library 14 · **零信号 0** |
| `compiler/tests/bootstrap/artifact_checks.sh` | **17 道**（`check_*` 函数数）· 0 FAIL |
| `compiler/tests/bootstrap/fixed_point.sh` | N=10 跨代 byte-equal 全绿（`.il` 与 `.s`；门数由脚本内部计数，不在此声明） |
| `compiler/tests/bootstrap/closure_check.sh` | PASS（v2.s == v3.s，逐字节相同） |
| 自举闭环 | `make` **迭代到不动点** —— 生成的 `.s` 跨代逐字节相同 |
| 版本零漂移 | `python scripts/dev/bump_version.py check` —— 覆盖 8 处（含两份 README 的徽章） |
| 文档事实对拍 | `python scripts/dev/docs_facts_check.py` |

---

## 3. workaround 台账

| 项 | 值 |
|---|---|
| 台账 | [`docs/workarounds.md`](workarounds.md) —— **永不归档** |
| 条目总数 | **165** |
| ACTIVE | **1** —— [`W-170`](workarounds.md#w-170)：`jhyy build` 不处理 `#[link_section]` |
| DEFERRED | 0 |
| RESOLVED / SUPERSEDED / INVALID | 153 / 9 / 2 |

---

## 4. v4.x 排期

> 版本号是**预留号** —— 启动那一格时按当时的实际状态复核（每份 plan 自带「启动时复核清单」）。
> 稳定身份是 **OS-N** 序号。

### 4.1 性能线（自研后端 —— 当前主线）

| 版本 | 内容 | 状态 |
|---|---|---|
| **v4.4.0** | **寄存器分配 ①**：位置映射 + 前瞻窗口缓存（**阶段二 = emit 层消费寄存器**） | 🔄 下一版 |
| v4.4.1 | 寄存器分配 ②：call-clobber + 寄存器类 | 🔴 预留号 |
| v4.4.2 | 寄存器分配 ③：跨基本块 + phi 并行移动 | 🔴 预留号 |
| v4.4.3 | 寄存器分配 ④：门 + perf 验证 + 去文本耦合 | 🔴 预留号 |
| v4.4.5 | peephole 4096 真修 + IR 优化框架（v4.2.2 / v4.3.0 降级而来） | 🔴 预留号 |
| v4.5 | M5 Part 3（0-C 闭环 —— 最后一项） | 🔴 预留号 |

> v4.4.0 **阶段一**（寄存器分配器 + 安全网，产物逐字节不变）已于 2026-10-30 完成。
> 已 ship 的 v4.0.x / v4.1.x / v4.2.x sprint 计划见 `docs/archive/plans/v4/`。

### 4.2 OS 线（v4.6 → v4.15）

| 版本 | OS-N | 内容 |
|---|---|---|
| v4.6 | OS-1 | 止血包 |
| v4.7 | OS-2 | 观测（栈上界） |
| v4.8 | OS-3 | 反馈环（最小 kernel.efi） |
| v4.8.5 | OS-4 | 栈与分配 |
| v4.9 | OS-5 | ABI 收敛 |
| v4.10 | OS-6 | 语言自洽 |
| v4.10.5 | OS-7 | 效果最小集 |
| v4.11 | OS-8 | lifetime |
| v4.12 | OS-9 | trait + `dyn Trait` |
| v4.12.3 | OS-10 | const generic |
| v4.12.5 | OS-11 | HKT（一阶） |
| v4.13 | OS-12 | 效果骨架 + 锁序 |
| v4.13.5 | OS-13 | 对象模型冻结（manifest） |
| v4.14 | OS-14 | 能力类型化（`Cap<T>` 真 T） |
| v4.14.5 | OS-15 | 内核数据结构（RCU / PerCpu） |
| v4.15 | OS-16 | 可信工具链（KASAN / KCFI） |

### 4.3 未排期（v4.16 起）

async/await · 包管理器 · 并发 cap + 完整 memory model · 多架构 ABI
—— **不预先落文档**，启动时再领版本号。

---

## 5. 目标三元组

| 三元组 | 含义 |
|---|---|
| `amd64_win` | x86-64-w64-mingw32（默认，hosted Windows） |
| `amd64_win_freestanding` | x86-64-w64-none（UEFI） |
| `amd64_sysv` | x86-64-linux-none |
| `amd64_sysv_freestanding` | x86-64-linux-none-freestanding |

---

## 6. 引用本文件的方式

**正确**：

```markdown
回归基线见 [`../docs/FACTS.md`](../docs/FACTS.md) § 2。
```

**错误**（复述 = 下一个漂移源）：

```markdown
回归 259 PASS + 0 XFAIL + 0 failed + 20 SKIP（279 total）。
```

例外：**仓库门面**（`README.md` / `README.zh-CN.md`）可以在「Status」段直接给数字 ——
但那里的数字由 `docs_facts_check.py` 一并对拍。
