# Changelog

> **本文件 = 官方推荐的用法 + 每个版本的一句话要点。**
> **详细的逐版本记录**在 [`docs/archive/logs/`](docs/archive/logs/) ——
> v4 轴的 umbrella 在 [`docs/archive/logs/v4/changelog-v4.0.0.md`](docs/archive/logs/v4/changelog-v4.0.0.md)。
>
> 版本号的**唯一真相源**是仓库根的 `VERSION` 文件。
> 改版本号用 `python scripts/dev/bump_version.py set <X.Y.Z>`（**不要手改**）——
> 完整流程（含**不可省的 `make`**）见 [`docs/internal/build.md` § 版本号自动化](docs/internal/build.md#版本号自动化)。

---

## 推荐用法

### 安装（Windows x64 最终用户）

下载 `jhyy-installer-4.1.2.exe`（~55 MB，GUI）或 `jhyy-compiler-4.1.2.msi`（~28 MB，
企业 / SCCM 分发）。

> **自 v4.1.0 起不需要 MSYS2** —— installer 自带一份最小原生 ucrt64 工具链。
> 装完直接用。

### 三条最常用的命令

```bash
jhyy compile hello.jhyy -o hello.exe   # 编译 + 链接
jhyy run     hello.jhyy                # 编译 + 链接 + 执行
jhyy build   hello.jhyy -o hello.s     # 只编译出汇编（不链接）
```

### 看版本

**没有 `jhyy --version`** —— 它从来就不存在（跑它是 `unknown command` + exit 1）。
版本横幅在 **`jhyy --help` 的首行**。

### 交叉编译到 Linux

```bash
jhyy compile hello.jhyy --target=amd64_sysv_freestanding --no-link -o hello
# → hello.s（ELF/SysV ABI 汇编），在 Linux 侧用 gcc 链
```

四个目标三元组见 [`docs/FACTS.md`](docs/FACTS.md) § 5。

### 其它入口

| 想做的事 | 去哪 |
|---|---|
| 了解项目 | [`README.md`](README.md)（英文） / [`README.zh-CN.md`](README.zh-CN.md)（中文） |
| 写 `.jhyy` | [语言规范](docs/abis/jhyy-lang-spec-v4.0.0.md) |
| 碰 FFI / struct 传参 | [ABI 白皮书](docs/abis/jhyy-abi-v4.0.0.md) |
| 贡献代码 | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| 想知道「现在什么状态」 | [`docs/FACTS.md`](docs/FACTS.md) |
| 查已知的坑 | [`docs/workarounds.md`](docs/workarounds.md) |

---

## 当前版本

### v4.1.2 — 2026-10-29

- **`jhyy --version` 从来就不存在** —— 文档 / release note / 脚本里此前让你跑一个
  不存在的命令（跑它是 `unknown command` + exit 1）。版本横幅在 `jhyy --help` 首行。
- **版本号自动化** —— `VERSION` 文件成为唯一真相源；`scripts/dev/bump_version.py`
  提供 `set` / `check` / `finalize` 三条命令 + 两道门（CI 零漂移门 + release 的
  `VERSION == tag` 断言）。
- **真修 `build.ps1 bundle` 静默复用陈旧 MSI** —— bundle 里嵌的是旧编译器。
- 完整记录：[`docs/archive/logs/v4/changelog-v4.0.0.md`](docs/archive/logs/v4/changelog-v4.0.0.md) § v4.1.2

---

## 版本要点

| 版本 | 一句话 |
|---|---|
| **v4.1.2** | `--version` 不存在这件事说清楚 + 版本号自动化（`VERSION` 单一真相源） |
| **v4.1.1** | VSCode 终端 profile 改为探测真实 bash + 新增 `jhyy-bash.cmd` 启动器；**作废「打包 POSIX 层」这条计划** |
| **v4.1.0** | installer 自带最小原生 ucrt64 工具链 ⇒ **装机用户不再需要 MSYS2** |
| **v4.0.22** | lang-spec 覆盖审计：补回归门 + 挖出 std lib 三处真缺陷 + 一处编译器崩溃 |
| **v4.0.21** | side-file per-pid 唯一化（并发编译互踩）+ Makefile 变量漏改 + 跨盘改名失败 + C 端编译器删除 |
| **v4.0.20** | 审计「skip test / 新增 test」挖出的三处**门**自身的问题 |
| **v4.0.19** | workaround 台账 ACTIVE 桶首次清零（14 → 0） |
| **v4.0.18** | `&mut` 最小独占检查 + 死 stub 删除；lexer EOF 守卫；产物可复现；`asm!` / memory barrier 真正内联进函数体 |
| **v4.0.17** | 两张「按固定上限分配」的表改成按实际需要分配（顺带修掉 temp 表越界静默算错值） |
| **v4.0.16** | `std_os_*` 接真 libc + `#[link_section]` 落到真的 `.s` |
| **v4.0.15** | `&mut` 真的能用了 |
| **v4.0.14** | enum 的 ABI 两侧统一（参数按地址 / 返回值走 sret） |
| **v4.0.12** | SysV MEMORY class（>16B struct 走栈） |
| **v4.0.6** | W-101 attempt #7 成功 —— 自举闭环达成 |
| **v4.0.2** | 多条 emit / sema 真修（i64 字面量、mem_set i64-store、per-fn-local counter…） |
| **v4.0.1** | v4.x 轴的第一次真修 |
| **v4.0.0-rc1** | v2.x + v3.x 两轴合并入 main；QBE 工具链移除；自举闭环 |
| **v4.2.0** | 运行时性能门进 CI（静态指标硬门 + 墙钟只报告）+ `bench.sh` 计时器真修 |
| **v4.2.1** | 帧尺寸按函数实际需要算（去掉写死的 8192 预留）⇒ ~41% 运行时 |
| **v4.4.0 阶段一** | 寄存器分配器 + 安全网（**产物逐字节不变**）；阶段二 = emit 层消费寄存器 |

> ⚠️ v4.2.x / v4.4.0 是**性能线**，与 v4.0.x 的编号不按序 —— 排期见
> [`docs/FACTS.md`](docs/FACTS.md) § 4。

---

## 往前的版本

- **v3.x**（语言特性扩展，终结于 v3.4.2）· **v2.x**（QBE 重写 + 多目标，终结于 v2.16.0）·
  **v1.x**（自举，终结于 v1.8.3）· **v0.x**（C 编译器，冻结于 v1.0.0 baseline）
  ⇒ 全部在 [`docs/archive/logs/`](docs/archive/logs/)。
- **逐版本的 sprint 计划** ⇒ [`docs/archive/plans/`](docs/archive/plans/)。
