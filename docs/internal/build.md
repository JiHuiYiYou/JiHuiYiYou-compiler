# 构建与运行

> 编译 JHYY、跑 `.jhyy` 程序、跑门、验证自举闭环。
>
> **会变的数字（回归数 / 门数 / 产物尺寸）见 [`docs/FACTS.md`](../FACTS.md)。**

---

## 宿主平台

**编译器宿主 = Windows x64。这是设计决策,不是缺陷,也不在任何待办里。**

- `compiler/build/bin/jhyy.exe` 是 **PE32+ Windows 可执行文件**（git 跟踪的产物），
  自举闭环必须**执行**它 ⇒ 宿主必须是 Windows（或 Wine）。
- C 端编译器已于 v4.0.21 删除 ⇒ 不存在「用 Linux gcc 编出原生 ELF 版 jhyy」这条路。
- `compiler/src0/jhyy_helpers.c` 的 C 桥有 4 个**只在 `#ifdef _WIN32` 内定义、
  没有 `#else`** 的必需 FFI 符号（`jh_mktemp_ascii` / `jh_file_copy` /
  `jh_rename_file` / `jh_unlink_file`），且都在**每次编译的关键路径上**。
- 路径处理全是 Windows 逻辑（`path_to_win()` 把 `/` 换成 `\`；输出后缀写死 `.exe`）。
- 工具链与分发全 Windows：CI `runs-on: windows-latest` + `shell: msys2 {0}`；
  installer 是 WiX（MSI/EXE）+ VSCode 扩展。

⇒ **别把「宿主能不能是 Linux」当 bug 挖** —— 范围外，不是待办。

**目标（target）侧不受此限**：`--target=amd64_sysv` 产 Linux ELF —— `.s` 在 Windows 上
emit，在 Linux 上 link + run。四个 target 见 [`docs/FACTS.md`](../FACTS.md) § 5。

---

## 编译编译器（自举链）

**本仓没有 C 端了。** `compiler/build/bin/jhyy.exe` 是 **git 跟踪**的产物
（fresh clone 里就有），它**自己**编 src0：

```bash
make            # = 编 jhyy_helpers.o / runtime.o + 自举闭环检查，产 jhyy.exe
make selfhost   # 跨代 .s 逐字节 byte-equal 闭环检查
```

`make` 的 `jhyy.exe` 规则做三件事：

1. 把**当前这个**（已提交的）`jhyy.exe` 复制成 `_boot_anchor.exe`；
2. `_boot_anchor.exe` 编 src0 → `_boot_new`（+`.s`），`_boot_new.exe` 再编一遍 →
   `_boot_new2`（+`.s`）；
3. **闭环检查**：`cmp -s _boot_new.s _boot_new2.s` ⇒ 新编译器编 src0 的产物必须与
   它自己编的逐字节相同（任何 emit 层的非确定性都会当场炸）。

第 3 步之后还有一道**漂移检查**：新产物还要与**提交进仓的那份**逐字节相同 ——
但**只在 src0/runtime 与 HEAD 一致时**才生效（src0 一改，新产物本就该不同）。
谁要发布，谁负责把新的 `compiler/build/bin/jhyy.exe` 提交上去。

构建产物：

- `compiler/build/bin/jhyy.exe` — **git 跟踪**的自举锚点（production，users invoke）
- `compiler/build/bin/jhyy_v1.exe.exe` — jhyy.exe 的**同内容副本**，每次构建重新生成

`-Wall -Wextra` 必须零警告。

---

## 工具链

### 解析顺序

`jh_gcc_path()`（`compiler/src0/jhyy_helpers.c`）：

```
JHY_GCC 环境变量 → %JHYY_HOME%\env.txt → **内置 toolchain** → C:\msys64 硬编码 → PATH → 裸 "gcc"
```

⇒ **默认用内置那份**（确定性 + 版本受控 + 不依赖用户 PATH 形态）。
用户要用回自己的 gcc：设 `JHY_GCC` 或写 `env.txt`（installer **不**代写）。

### 四个必须记住的坑

1. **`ucrt64/` 这一层的名字不能改** —— gcc 16 把系统头路径写死成
   `<prefix>/bin/../../ucrt64/include` ⇒ prefix 目录**必须叫 `ucrt64`**。
   工具链搬走后 `<prefix>/../ucrt64/include` 会跑到工具链外面 ⇒ 编译器连自己的
   `runtime.c` 都编不过（`stdlib.h: No such file or directory`）。
   gcc 15 不写死这层 ⇒ 保留它两边都成立。
   ⚠️ **本地测不出来** —— 本地 MSYS2 是 gcc 15.2.0，CI 的是 16.2.0。
2. **目录结构不能拍平** —— gcc 用自身位置推导 `cc1` / `collect2` / `as` / `ld`。
3. **`as.exe` / `ld.exe` 必须在 `lib/gcc/<target>/<ver>/` 里再放一份** ——
   gcc 与 collect2 按**裸名**找这两个；PATH 上有个别的 ld（典型：MSYS2 POSIX 层的
   `/usr/bin/ld.exe`）就会被捡走 ⇒ **链接失败且 stderr 零输出**。
4. **头闭包不能只收 `*.h`** —— ucrt 的 `stdio.h` 会 `#include <swprintf.inl>`。

### 预编 `.o`

安装版每次链接都**现场重编** `runtime.c` + `jhyy_helpers.c` 是 ~5 秒；用预编 `.o`
是 ~0.5 秒。installer 从 v4.1.0 起随包发 `runtime.o` / `jhyy_helpers.o`
（由**收集进来的那份 gcc** 编，保证 ABI 一致），编译器经 `jh_path_runtime()` /
`jh_path_helpers()` 优先取 `.o`（**仅安装布局**；源码树仍走相对路径
`compiler/build/obj/`）。`.c` 仍然随包发，作为 `.o` 缺失时的回落。

### 终端 / bash

- **VSCode 终端 profile 指向探测到的 bash**（不是 VSCode 自带那个写死路径的
  `bash (MSYS2)` profile —— 它**不会**回落到别的 bash）。探测顺序：
  `$env:MSYS2_ROOT` → `C:\msys64` → MSYS2 注册表的 `InstallLocation`
  → Git for Windows → PATH。探测不到就**不改用户的 VSCode 设置**。
  门：`installer/scripts/verify-vscode-bash-detect.ps1`。
- **`jhyy-bash.cmd`**（装到 `<INSTALLDIR>\bin\`）：自己找 bash 并启动，
  顺带把 `JHYY\bin` 塞进 PATH 并设 `MSYS2_PATH_TYPE=inherit`
  （MSYS2 的 minimal PATH 模式无视 Windows PATH ⇒ 不设它 bash 里找不到 jhyy）。
- ⚠️ **不打包 POSIX 层**（bash + coreutils）—— 实测 MSYS2 的运行时
  **不做「按树搬迁」**（拷出来的 bash 仍然用系统的 `/usr/bin`）⇒ 半残态。
  完整证据见 [`installer/toolchain/README.md`](../../installer/toolchain/README.md) § 二期结论。

### ⚠️ 构建前必读：PATH 顺序（链接失败会**一个字都不打印**）

PATH 里**先出现哪个 `gcc` / `ld` 就用哪个**。典型故障：GitHub runner 镜像自带
**旧 MSYS2 在 `C:\mingw64`** 且排在 PATH 前面 ⇒ 工具链版本 pin 失败。
⇒ 构建时把 MSYS2 根目录**显式传下去**。

---

## 编译 `.jhyy` 程序

```bash
jhyy compile hello.jhyy -o hello.exe     # 编译 + 链接
jhyy build   hello.jhyy -o hello.s      # 只编译出汇编
jhyy run     hello.jhyy                 # 编译 + 链接 + 执行
```

多文件：把每个 `.jhyy` 都列上（`jhyy compile main.jhyy lib.jhyy -o app`）。

**CLI 全集**（含 `--target=` / `--no-link` / `--help`）⇒ `jhyy --help`。
⚠️ **没有 `jhyy --version`** —— 版本横幅在 `--help` 首行。

---

## 多 target

| 三元组 | 产物 | 怎么链 |
|---|---|---|
| `amd64_win`（默认） | PE/COFF `.exe` | Windows 上 gcc 直接链 |
| `amd64_win_freestanding` | PE/COFF `.obj`（UEFI） | `lld-link /SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main` |
| `amd64_sysv` | ELF `.s` | Windows 上出 `.s`，Linux 上链 |
| `amd64_sysv_freestanding` | ELF `.s`（freestanding） | `crt0.S` + `link.ld`（`runtime/linux_elf/`） |

交叉链路（SysV）：

```bash
# Windows 侧只出 .s,不链接
jhyy compile hello.jhyy --target=amd64_sysv_freestanding --no-link -o hello
# 完整 6 用例的门(自带 docker gcc:12 chain:链 crt0.S + link.ld → 跑 ELF)
bash compiler/tests/bootstrap/sysv_full_regress.sh --runs=1
```

---

## 手动验证流水线

排查 codegen / 链接问题时手动走一遍：

```bash
# 1. 只编译不链接 → .s(落在 `-o` 指定的输出**旁边**)
./compiler/build/bin/jhyy.exe compile test.jhyy --no-link -o test
#   ⇒ 产出 test.s(只有汇编;**不加 --no-link 会顺带链出 test.exe**)。
#     **默认不落 .il** —— 只有要看中间表示才加 JHY_WRITE_IL=1。
#     ⚠️ .s 落在 -o 输出旁边,不是 compiler/build/bin/ ⇒ 下一步的 cat 路径要跟着改。

# 2. 看 .s 汇编
cat test.s

# 3. 手动链接(需 runtime.c + jhyy_helpers.c,jhyy 编 jhyy 必需)
/c/msys64/ucrt64/bin/gcc.exe test.s compiler/runtime/runtime.c compiler/src0/jhyy_helpers.c -o test.exe -lm

# 4. 检查退出码
./test.exe; echo $?
```

⚠️ `jhyy build` 与 `jhyy compile --no-link` **不等价**：前者不跑
`apply_link_section_directives` ⇒ 用了 `#[link_section]` 的程序两条路径产物不同
（`W-170`）。工具链一律用 `compile --no-link`。

---

## 版本号自动化

**版本号的唯一真相源 = 仓库根的 `VERSION` 文件。**

```bash
python scripts/dev/bump_version.py set 4.1.2   # 刷 VERSION + 全仓版本串(hash 置为待填占位)
make                                           # main.jhyy 的字面量变了 -> 自举产物必须重编
pwsh -File installer/build.ps1 bundle          # 构建
python scripts/dev/bump_version.py finalize     # 回填 sha256(scoop hash + winget InstallerSha256)
python scripts/dev/bump_version.py check        # 零漂移门(CI 也跑)
```

**顺序不能反**：编译器版本号只能是 `main.jhyy` 里的**字符串字面量** ——
改成运行时读文件 / 调 extern 需要新增局部变量，而**新增局部变量会移位模块级
temp 编号 ⇒ 自举产物行为漂移**。字符串字面量改动是安全的 ⇒ 自动化只能落在
「改字面量」这一层。

**tag 与 VERSION 的关系**：`VERSION` = 声明的版本（仓内真相源）；**tag** = 发布这个动作。
两者必须一致 ⇒ `release.yml` 在构建前就断言 `VERSION == tag`，不符直接拒发。

---

## 门

| 门 | 查什么 |
|---|---|
| `python regress.py` | 全量回归 |
| `python scripts/dev/audit_test_assertions.py --strict` | 每个测试的断言强度（零信号即红） |
| `compiler/tests/bootstrap/artifact_checks.sh` | 产物级断言（图标 / 帧 / 旁路文件 / 版本 …） |
| `compiler/tests/bootstrap/fixed_point.sh` | 跨代 byte-equal |
| `compiler/tests/bootstrap/closure_check.sh` | v2.s == v3.s |
| `python scripts/dev/bump_version.py check` | 版本零漂移（覆盖 8 处，含两份 README 徽章） |
| `python scripts/dev/docs_facts_check.py` | 文档里的事实与现实对拍 |

工具链侧的门：

```bash
# 采集（CI 用 -AllowVersionDrift；release 严格 —— 版本不符响亮失败）
powershell -NoProfile -ExecutionPolicy Bypass -File installer/scripts/collect-toolchain.ps1
# 验（可重定位 / 头闭包 / poisoned PATH / 无 PATH / windres / 预编 .o 字节一致）
powershell -NoProfile -ExecutionPolicy Bypass -File installer/scripts/verify-toolchain.ps1
```

⚠️ **门必须能抓到真失败**：新增或改动工具链组成后，**先跑门，再改代码**。

---

## 排障

| 症状 | 多半是 |
|---|---|
| `make` 报 `ld returned 1` 且 stderr 全空 | 输出文件被孤儿 `jhyy.exe` 占着（Windows 上 exe 被 map 后 gcc 无法覆写）⇒ `tasklist //FI "IMAGENAME eq jhyy.exe"`（MSYS2 里要 `//`）→ `taskkill //PID <pid> //F`；先**换输出路径复跑一次**做二分，别一上来读 `.s` |
| 链接失败 + stderr 零输出 | PATH 里捡走了别的 `ld` ⇒ 见上面「坑 3」 |
| `stdlib.h: No such file or directory` | 工具链的 `ucrt64/` 层被拍平了 ⇒ 见上面「坑 1」 |
| `make` 绿但 CI 红 | 本地有陈旧产物 / 工具链不同 ⇒ **`make clean && make`** 从干净状态重建；CI 的 fresh checkout 才是「从零能不能建出来」的地标 |
| 改了 `main.jhyy` 的字面量但产物没变 | 忘了 `make`（自举产物是 git 跟踪的，改完要重编 + 提交） |
| 回归偶发 FAIL | 先清残留进程 + 重跑两次；两次一致之前不要改代码 |

---

## 相关

- 事实（版本 / 回归数 / 排期）⇒ [`docs/FACTS.md`](../FACTS.md)
- 架构 ⇒ [`docs/internal/architecture.md`](architecture.md)
- 安装器 ⇒ [`installer/README.md`](../../installer/README.md)
- 工具链设计 ⇒ [`installer/toolchain/README.md`](../../installer/toolchain/README.md)
