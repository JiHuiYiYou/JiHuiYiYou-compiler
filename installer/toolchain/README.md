# 内置工具链（v4.1.0 起）

installer 自带一份**最小原生 MSYS2 ucrt64 工具链**，让装机用户**不需要 MSYS2**也能编译 `.jhyy`。

## 为什么

v4.1.0 之前，编译器去用户机器上找 gcc（`jh_gcc_path()` 的 `C:\msys64\...` 硬编码 → PATH 两级）：

| 症状 | 根因 |
|---|---|
| **没装 MSYS2 的机器根本装不上编译器** | MSI 有 `<Launch Condition="Installed OR MSYS2_GCC_FOUND">` ⇒ 直接 1603 失败 |
| 装了 MSYS2 的用户，用**他自己那份** gcc | 版本不受控；且 `docs/internal/build.md` §PATH 顺序 记的那个坑（ucrt64 的 ld 捡到别的 DLL ⇒ **链接失败且 stderr 零输出**）照样发作 |

v4.1.0 起：工具链随包分发，**默认用内置那份**（确定性 + 版本受控 + 不依赖用户 PATH 形态）。

## 组成

```
<INSTALLDIR>\toolchain\
├── ucrt64\                    ← ⚠️ 这一层的**名字不能改**（见下）
│   ├── bin\        gcc as ld ar dlltool windres strip nm objdump ranlib + 10 个运行时 DLL
│   ├── lib\        crt2.o / default-manifest.o / binmode.o + CRT 与 win32 import libs
│   │   └── gcc\x86_64-w64-mingw32\<ver>\
│   │       ├── cc1.exe collect2.exe **as.exe ld.exe** libgcc.a crt*.o + 同样那 10 个 DLL
│   │       └── include\   gcc 自带头（闭包里用到的那 123 个）
│   ├── include\    头文件闭包（297 个，7.6 MB）
│   └── LICENSES\ + SOURCES.txt
```

原始体积 ≈ **92 MB**（MSI CAB 压缩后 ≈ 40 MB）。

**砍掉的**：`cc1plus.exe`（C++）、`lto1/lto-wrapper`（无 `-flto`）、`libstdc++`、`include/c++`、`include/isl`、`include/openssl`、以及 ucrt64/include 里没被闭包引用的其余部分。

## 四个**不能拍平 / 不能省**的地方

1. **`ucrt64/` 这一层的名字不能改** —— gcc 16 把系统头路径写死成
   `<prefix>/bin/../../ucrt64/include`（实测 gcc 16.2.0 的 `gcc -E -v`），
   即 **prefix 目录必须叫 `ucrt64`**。工具链搬到别处后，
   `<prefix>/../ucrt64/include` 会跑到**工具链外面** ⇒ 编译器连自己的
   `runtime.c` 都编不过（`stdlib.h: No such file or directory`）。
   gcc 15 不写死这层（`<prefix>/include`）⇒ 保留这一层对两个版本都成立。
   > 这个洞是 **CI** 抓出来的 —— CI 的 MSYS2 是 gcc 16.2.0，本地是 15.2.0，
   > 所以本地怎么测都测不出来。
2. **目录结构必须镜像 ucrt64** —— gcc 用自身位置推导 `cc1` / `collect2` / `as` / `ld`。拍平即废。
3. **`as.exe` / `ld.exe` 必须在 `lib/gcc/<target>/<ver>/` 里再放一份** —— gcc 与 collect2 是按**裸名**找这两个的（MSYS2 只把它们放在 `bin/`，gcc 自己的搜索路径里没有 ⇒ 只能落到 PATH）。PATH 上只要有一个别的 ld（典型：MSYS2 POSIX 层的 `/usr/bin/ld.exe`）就会被捡走 ⇒ 与 ucrt64 的库不匹配 ⇒ **链接失败且 stderr 零输出**（只有一句 `collect2.exe: error: ld returned 9 exit status`）。放进这个目录后全程不碰 PATH。
   > 这个洞是 `installer/scripts/verify-toolchain.ps1` 的 **T3 门（poisoned PATH）** 抓出来的 —— 手工测试时用的是原机器的 PATH，恰好没踩到。
4. **运行时 DLL 要贴 exe 放**（`bin\` 与 `lib/gcc\...\ver\` 各一份）—— `cc1.exe` 在后者，它的 DLL 不在那儿就只能去 PATH 找 ⇒ 捡到用户 MSYS2 的另一份 `libgcc_s_seh-1.dll` ⇒ ABI 错配。

## 头文件闭包

jhyy **发汇编，不发 C** —— 链接期被 gcc 编译的 C 只有 `runtime.c` 与 `jhyy_helpers.c` 两个固定桥接文件。
所以头文件需求 = 它们的依赖闭包（`gcc -M -E` 求并集），**不是**整棵 `ucrt64/include`（135 MB）。
实测 **297 个头 / 7.6 MB**（174 个系统头 + 123 个 gcc 自带）。

⚠️ 闭包不能只收 `*.h`：ucrt 的 `stdio.h` 会 `#include <swprintf.inl>` —— 只收 `.h` 会漏掉 `.inl`，然后工具链**编自己的 runtime.c 都编不过**（`swprintf.inl: No such file or directory`）。这个洞也是门抓出来的。

## 版本钉死

`manifest.json` 钉住 `gcc_version` 与各 MSYS2 包版本。收集脚本在本机 gcc 版本不符时**响亮失败**（不是 warning）—— 产物可复现性的前提。

- **release 构建**：严格（默认）。MSYS2 升级了 gcc ⇒ 发版构建直接失败 ⇒
  维护者 bump manifest + 重跑工具链门 ⇒ 不会悄悄发出一份没钉住的工具链。
- **CI**：`collect-toolchain.ps1 -AllowVersionDrift` ⇒ 版本漂移只告警。
  CI 的 runner 镜像是滚动的（实测 2026-10-28 已经是 gcc 16.2.0，而本地是 15.2.0），
  但那些门（可重定位 / 头闭包 / poisoned PATH）与版本无关 ⇒ 照样每次都跑。

⚠️ **gcc 16 会换掉一些东西**（CI 上实测）：
许可证目录从 `gcc-libs` 变成 `gcc`（⇒ 许可证原文**签进仓里**做基线，MSYS2 的做叠加）；
系统头路径写死了 `ucrt64` 这一层（⇒ 工具链根下必须保留 `ucrt64/`）。

## 用户怎么覆盖

内置优先，但**逃生门**在最上面：

| 方式 | 效果 |
|---|---|
| `JHY_GCC=<gcc.exe 全路径>` 环境变量 | 最高优先级 |
| `%JHYY_HOME%\env.txt` 里写 `JHY_GCC=<gcc.exe 全路径>` | 次之 |
| 什么都不做 | 用内置的（`source: bundled`） |

installer **不代写** env.txt —— 写死绝对路径会在换盘 / 重装时失效，还会盖住用户自己的配置。

## 相关脚本

| 脚本 | 作用 |
|---|---|
| `installer/scripts/collect-toolchain.ps1` | 采集工具链 / 求 DLL 闭包 / 求头闭包 / 编预编 .o / 出 manifest |
| `installer/scripts/gen-toolchain-wxs.ps1` | manifest → WiX `<Fragment>`（按目录一个 Component，GUID 用 UUIDv5 确定性生成） |
| `installer/scripts/verify-toolchain.ps1` | **常驻门**：可重定位 / 头闭包 / poisoned PATH / 无 PATH / windres / 预编 .o 字节一致 |

门必须能抓到真失败（不是恒绿）。新增或改动工具链组成后，**先跑门，再改代码**。
