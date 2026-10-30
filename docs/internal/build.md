# 构建与运行

> JHYY 编译器构建、.jhyy 程序编译与运行、手动验证流水线。

## 关键路径

```
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/
├── compiler/src0/          # 编译器源（jhyy 端自举翻译）—— **唯一的编译器实现**
├── compiler/runtime/       # 运行时（main → main_jhyy 桥接）
├── compiler/tests/         # 测试
│   ├── examples/*.jhyy     # 集成测试
│   └── unit/*.c            # 单元测试
├── mcp-jhyy/               # Claude Code MCP 服务
└── docs/                   # 文档
```

> ⚠️ **v4.0.21 (M5 Part 1)起 `compiler/src/` 已删除** —— C 端编译器(9771 行)
> 不再存在,`make stage0` 目标随之消失。构建语义变成「**jhyy.exe 能把自己编成
> 同一个东西**」(见下节)。

工具：
- GCC：`/c/msys64/ucrt64/bin/gcc.exe` (15.2.0 MSYS2 ucrt64)
- Self-backend (jhyy-side 自研 x86-64 codegen):**v4.0.0 起 sole production path** (QBE 完全移除,per `docs/plans/v2/v4.0.0-plan.md`)
- Git：`/d/Program Files/Git/bin/git.exe`

---

## ⚠️ v4.1.0: installer 自带工具链(装机用户不需要 MSYS2)

**装机版** `jhyy.exe` 从 v4.1.0 起自带一份最小原生 ucrt64 工具链,装在
`<INSTALLDIR>\toolchain\`:

```
<INSTALLDIR>\toolchain\
└── ucrt64\                    ← ⚠️ 这一层的**名字不能改**
    ├── bin\        gcc as ld ar dlltool windres strip nm objdump ranlib + 10 个运行时 DLL
    ├── lib\        crt2.o / default-manifest.o / binmode.o + CRT 与 win32 import libs
    │   └── gcc\x86_64-w64-mingw32\<ver>\
    │       ├── cc1.exe collect2.exe **as.exe ld.exe** libgcc.a crt*.o + 同样那 10 个 DLL
    │       └── include\   gcc 自带头（闭包里用到的那 123 个）
    ├── include\    头文件闭包（297 个，7.6 MB）
    └── LICENSES\ + SOURCES.txt
```

原始 ≈ **92 MB**（MSI CAB 压缩后 ≈ 40 MB）。完整设计见
[`installer/toolchain/README.md`](../../installer/toolchain/README.md)。

### 编译器的解析顺序

`jh_gcc_path()`（`compiler/src0/jhyy_helpers.c`）:

```
JHY_GCC 环境变量 → %JHYY_HOME%\env.txt → **内置 toolchain** → C:\msys64 硬编码 → PATH → 裸 "gcc"
```

⇒ **默认用内置那份**（确定性 + 版本受控 + 不依赖用户 PATH 形态）。
用户要用回自己的 gcc：设 `JHY_GCC` 或写 `env.txt`（installer **不**代写）。

### 四个必须记住的坑

1. **`ucrt64/` 这一层的名字不能改** —— gcc 16 把系统头路径写死成
   `<prefix>/bin/../../ucrt64/include`（实测 gcc 16.2.0 的 `gcc -E -v`）
   ⇒ prefix 目录**必须叫 `ucrt64`**。工具链搬走后 `<prefix>/../ucrt64/include`
   会跑到工具链外面 ⇒ 编译器连自己的 `runtime.c` 都编不过
   （`stdlib.h: No such file or directory`）。gcc 15 不写死这层 ⇒ 保留它两边都成立。
   ⚠️ **本地测不出来** —— 本地 MSYS2 是 gcc 15.2.0，CI 的是 16.2.0。
2. **目录结构不能拍平** —— gcc 用自身位置推导 `cc1` / `collect2` / `as` / `ld`。
3. **`as.exe` / `ld.exe` 必须在 `lib/gcc/<target>/<ver>/` 里再放一份** ——
   gcc 与 collect2 按**裸名**找这两个；PATH 上有个别的 ld（典型：MSYS2 POSIX 层的
   `/usr/bin/ld.exe`）就会被捡走 ⇒ **链接失败且 stderr 零输出**（只有
   `collect2.exe: error: ld returned 9 exit status`）。
4. **头闭包不能只收 `*.h`** —— ucrt 的 `stdio.h` 会 `#include <swprintf.inl>`。

### 门

```bash
# 采集（CI 用 -AllowVersionDrift；release 严格 —— 版本不符响亮失败）
powershell -NoProfile -ExecutionPolicy Bypass -File installer/scripts/collect-toolchain.ps1
# 验（可重定位 / 头闭包 / poisoned PATH / 无 PATH / windres / 预编 .o 字节一致）
powershell -NoProfile -ExecutionPolicy Bypass -File installer/scripts/verify-toolchain.ps1
```

⚠️ 门必须能抓到真失败。新增或改动工具链组成后，**先跑门，再改代码**。

### 预编 .o

安装版每次链接都**现场重编** `runtime.c` + `jhyy_helpers.c` 是 5045ms；用预编 `.o`
是 531ms。installer 从 v4.1.0 起随包发 `runtime.o` / `jhyy_helpers.o`
（由**收集进来的那份 gcc** 编，保证 ABI 一致），编译器经
`jh_path_runtime()` / `jh_path_helpers()` 优先取 `.o`（**仅安装布局**；
源码树仍走相对路径 `compiler/build/obj/`，行为不变）。
`.c` 仍然随包发，作为 `.o` 缺失时的回落 —— 回落路径要编 C，所以头闭包仍然必需。

### 终端 / bash（v4.1.0 二期）

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


---

## 宿主平台

**编译器宿主 = Windows x64。这是设计决策,不是缺陷,也不在 backlog 里。**

证据链(免得下次 audit 又把它当 bug 挖出来):

- `compiler/build/bin/jhyy.exe` 是 **PE32+ Windows 可执行文件**(git 跟踪的产物)。
  `make` 的自举闭环必须**执行**它 ⇒ 宿主必须是 Windows(或 Wine)。
- C 端编译器已于 v4.0.21 (`b6efe61`)删除 ⇒ **不存在**「用 Linux gcc 编出一个
  原生 ELF 版 jhyy」这条路;`compiler/src0/*.jhyy` 是用 jhyy 自己写的(鸡生蛋),
  唯一的种子就是上面那个 PE。
- `compiler/src0/jhyy_helpers.c` 的 C 桥有 4 个 **只在 `#ifdef _WIN32` 内定义、
  没有 `#else`** 的必需 FFI 符号 —— `jh_mktemp_ascii` / `jh_file_copy` /
  `jh_rename_file` / `jh_unlink_file`(helpers.c:626-715)⇒ Linux 上编这个桥会
  undefined reference。这 4 个在**每次编译的关键路径上**(建临时 .asm/.exe →
  拷 .s → rename 到输出路径 → 清理)。
- `jh_paths_init`(helpers.c:240-360)整段是 Windows 路径逻辑(无条件把 `/` 换成
  `\`、`strrchr(path,'\\')`、拼 `%s\\runtime.c`、walk-up 也按 `\` 切)⇒ 布局探测
  在 Linux 上必然失败 ⇒ 连 `runtime.c` / `jhyy_helpers.c` / std 目录都找不到。
- `main.jhyy` 侧:`path_to_win()`(main.jhyy:177)把 `/` 换成 `\`;输出后缀写死
  `.exe`(main.jhyy:1211 / 1609 / 1820)。
- 工具链与分发全 Windows:CI `runs-on: windows-latest` + `shell: msys2 {0}`;
  `release.yml` 同;installer 是 WiX(MSI/EXE)+ VSCode 扩展。

⇒ **别把「宿主能不能是 Linux」当 bug 挖** —— 未启动工作的清单
([`docs/plans/v4/version-schedule.md`](../plans/v4/version-schedule.md) § 四)里
**没有**这一项,那是范围外,不是待办。

**目标(target)侧不受此限:** `--target=amd64_sysv` 产 Linux ELF —— .s 在 Windows
上 emit,在 Linux 上 link + run。CI 里那道 `SysV ABI (6 tests windows-latest can
never run)` job(`ci.yml`, `runs-on: ubuntu-latest`)干的就是这个。四个 target:
`amd64_win`(默认)/ `amd64_win_freestanding` / `amd64_sysv` /
`amd64_sysv_freestanding`。

---

## 编译编译器 (自举链)

**本仓没有 C 端了。** `compiler/build/bin/jhyy.exe` 是 **git 跟踪的**产物
(fresh clone 里就有),它**自己**编 src0:

```bash
make            # = 编 jhyy_helpers.o / runtime.o + 自举闭环检查,产 jhyy.exe
make selfhost   # v1 → v2 → v3 → v4 → v5 .s 逐字节 byte-equal 闭环检查
```

`make` 的 `jhyy.exe` 规则做三件事:

1. 把**当前这个**(已提交的)jhyy.exe 复制成 `_boot_anchor.exe`;
2. `_boot_anchor.exe` 编 src0 → `_boot_new`(+`.s`),`_boot_new.exe` 再编一遍 →
   `_boot_new2`(+`.s`);
3. **闭环检查**:`cmp -s _boot_new.s _boot_new2.s` ⇒ 新编译器编 src0 的产物必须与
   它自己编的逐字节相同(任何 emit 层的非确定性都会当场炸)。

第 3 步之后还有一道**漂移检查**(W-117):新产物还要与**提交进仓的那份**逐字节
相同 —— 但**只在 src0/runtime 与 HEAD 一致时**才生效(src0 一改,新产物本就该
不同,拿它跟旧产物比会挡住每一次正常的源码修改)。谁要发布,谁负责把新的
`compiler/build/bin/jhyy.exe` 提交上去。

构建产物:
- `compiler/build/bin/jhyy.exe` — **git 跟踪**的自举锚点(production, users invoke)
- `compiler/build/bin/jhyy_v1.exe.exe` — jhyy.exe 的**同内容副本**,每次构建重新生成
  (v4.0.8 起;`fixed_point.sh` / `byte_equal*.sh` / `stage1-expanded.sh` 按名引用它)

`-Wall -Wextra` 必须零警告。

---

## ⚠️ 构建前必读:工具链 PATH 顺序(链接失败会**一个字都不打印**)

本机 PATH 里 `/mingw64/bin` 排在 `/c/msys64/ucrt64/bin` **前面**,而前者带的
`libintl-8.dll` / `libiconv-2.dll` / `zlib1.dll` / `libwinpthread-1.dll`
**版本与 ucrt64 的不同**。ucrt64 的 `ld.exe` 于是加载到错版本的运行时 DLL ⇒
**链接失败时 stderr 零字节**,只剩一句 `collect2.exe: error: ld returned 1
exit status` —— **真错误完全看不见**。

**症状对照(同一条链接命令,只改 PATH):**

| PATH | ld 的输出 |
|---|---|
| 当前 PATH(`/mingw64/bin` 在前) | **零字节** |
| ucrt64 优先 | `undefined reference to 'xxx'`(真错误) |

**⇒ 构建 / 链接前先把 ucrt64 提到最前:**

```bash
export PATH="/c/msys64/ucrt64/bin:/c/msys64/usr/bin:$PATH"
```

**⇒ 排查链接失败的第一件事:先把 PATH 调干净,拿到 ld 的真实输出再判断。**
不要凭 exit code 猜。(2026-10-25 实测:因为这条,一次「C 文件编译通过但少了
两个符号」的编译期错误被伪装成了「ld 静默死 / flaky」,查了整整一轮。)

---

## 编译 .jhyy 程序

```bash
./compiler/build/bin/jhyy.exe compile <file.jhyy> -o <output_name>
```

支持多文件（v0.4+）：
```bash
./compiler/build/bin/jhyy.exe compile main.jhyy lib_a.jhyy lib_b.jhyy -o output
```

**v1.8.1 patch — 图标 embed (`windres` 流程)**:

所有 binary 都内嵌 branded "J" 图标(256×256 RGBA, Vista+ 6 frame),通过 MinGW `windres.exe` 把 `installer/jhyy-icon.ico` 编为 COFF `.o` 链入 PE 资源段 `.rsrc`:

- **`jhyy.exe`** **以及所有 user-compiled `.jhyy` 程序**:`compiler/src0/jhyy_helpers.c` 的
  `jh_build_icon_obj()` **现场生成** `.rc` → 调 `windres.exe` 编成临时 `.o`
  → 由 `jh_gcc_invoke()` 插进链接行 → `jh_run()` 在子进程结束后删掉临时 `.o`
  (见 W-132)。
  ⚠️ **v4.0.21 (M5 Part 1)起这套逻辑全在 C 侧**(`jhyy_helpers.c`),
  **`compiler/src/main.c` 已删除** ⇒ 以前那条「C 端的 `compile()` 调 windres」
  的说法不再成立;`compiler/src/jhyy.rc` 这个文件也不存在了(`.rc` 现在是
  运行时生成的)。

**改图标后必须重 build**:
```bash
make
```

(.ico 修改走 `installer/build-jhyy-icons.ps1`,deterministic 重出 6-frame ICO;
改完不重 build,`jhyy.exe` 内嵌的还是旧 icon。)

**path 坑**:`windres` 内部走 `gcc -E` 预处理,路径里的 `\` 会被当 escape 字符吃掉。
C 侧用 `path_to_fwd()` 把 `\` 全部转 `/` 才传给 windres(教训 2026-08-27 v1.8.1 patch 阶段)。

**验证**: `objdump -h compiler/build/bin/jhyy.exe | grep rsrc` 应见 `.rsrc` 段(9184B);
`grep -c '89 50 4e 47' <(objdump -s -j .rsrc ...)` 应为 6(每个 ICO frame 内嵌 PNG signature)。
**常驻门**:`compiler/tests/bootstrap/artifact_checks.sh` 的 `compiler_icon` /
`program_icon` 两道(用 Explorer 同一套 API 问「exe 里到底有没有图标」)。

---

## 编译并运行

```bash
./compiler/build/bin/jhyy.exe run <file.jhyy>
```

> **注意**:**v1.x 已修** (`main.c:591` `path_to_win(exe)` 已处理 MSYS ↔ Win32 路径转换),`run` 子命令可用;v1.8.3.2 patch 加 `cmd_run main_jhyy` byte-scan pre-check (W-065,避免库 snippet 报 "undefined reference to main_jhyy")。

---

## CLI 参考(jhyy 到底支持哪些子命令 / flag)

唯一 CLI 入口 = `compiler/src0/main.jhyy:1864-2000`。**全集如下**(没有别的):

| 形式 | 行为 |
|------|------|
| `jhyy`(无参数) | 打印 `jhyy compiler v<版本> (self-hosted)` + 简版 usage,exit 0 (`main.jhyy:1864-1873`) |
| `jhyy --help` | 打印同一行版本横幅 + **完整** help(子命令 + flag + target 列表),exit 0 (`main.jhyy:1875-1907`) |
| `jhyy compile <file.jhyy> [-o out]` | 编译 + **链接** → `.exe`（库文件(无 main)只编译不链）；`--no-link` 时只出 `.s` |
| `jhyy build   <file.jhyy> [-o out]` | **只编译** → `.s`（源文件旁边），**不链接**；⚠️ 成功时退出码是 **2**（不是 0）—— 那是 `build_il` 的「in-mem 路径已 emit」信号，**不是错误** |
| `jhyy run     <file.jhyy>` | 编译 + 链接 + 执行 |
| `jhyy dump    <file.jhyy>` | 打印 AST / typed IR(调试用) |
| `--target=<triple>` | 选目标(默认 `amd64_win`),可出现在任意位置 (`main.jhyy:1924`) |
| `--no-link` | 只出 `.s`,跳过 gcc 链接(**跟在子命令后面**,`main.jhyy:1560`) |

> ⚠️ **`jhyy --version` 不存在 —— 从来就没有过**(`git log -S'--version' -- compiler/`
> 只命中 `gcc --version` / `wix --version` / `qemu --version`)。
> 想看版本号 ⇒ `jhyy --help` 的**首行**,或不带参数跑 `jhyy`。
> 写文档 / release note / 脚本时**不要**用 `--version`:它会落到 `unknown command`
> 分支 ⇒ stderr 打一行 `unknown command` + **exit 1** (`main.jhyy:1999-2000`)。

---

## 版本号自动化(v4.1.2 起)

### 为什么

版本号散在 **6 个地方、3 种格式**(另加每版的 release note 片段),而其中两处是
**编译期烘进产物**的:

| 位置 | 格式 | 漏改的后果 |
|---|---|---|
| `VERSION` | 纯文本 | **真相源**(v4.1.2 新增) |
| `compiler/src0/main.jhyy` | jhyy 源码里的字符串字面量 | 编译器自报旧版本号;**改了必须重编自举产物** |
| `installer/assets/license.rtf` | RTF | MSI 的 EULA 显示旧版本 |
| `installer/distribution/scoop/jhyy.json` | JSON | scoop 装的是旧版 |
| `installer/distribution/winget/.../JHYY/<ver>/*.yaml` | YAML(**目录名也带版本**) | winget 装的是旧版 |
| `docs/logs/v4/changelog-v4.0.0.md` | Markdown | changelog 缺这一版 |

漏改任何一处的后果都一样:**tag 上写着 v4.1.2,装出来的编译器自报 v4.1.1**。

> 顺带把**每版的 release note 正文**也拆出去了 ——
> `installer/release-notes/<ver>.md`(release.yml 从这里取 `${MAIN_CHANGES}`)。
> 以前 `installer/changelog-template.md` 里写死的是**上一版**的正文 ⇒
> 每发一版都要手改模板 ⇒ 迟早发出去一份描述的是上一版的 release note。
> 详见 [`installer/release-notes/README.md`](../../installer/release-notes/README.md)。

### 一条命令

```bash
# 1. 刷版本号(VERSION + 上面每一处;hash 置为待填占位)
python scripts/dev/bump_version.py set 4.1.2

# 2. 重编自举产物 —— main.jhyy 的字面量变了,产物必须跟上
make

# 3. 构建安装包
pwsh -File installer/build.ps1 bundle

# 4. 回填 sha256(scoop hash + winget InstallerSha256)
python scripts/dev/bump_version.py finalize

# 5. 门:查零漂移(CI 里也跑这一条)
python scripts/dev/bump_version.py check
```

### tag 与 VERSION 的关系

- **`VERSION` 文件** = 声明的版本(仓内真相源)
- **tag** = 发布这个动作

两者必须一致,否则就是「tag v4.1.3 但产物自报 v4.1.2」。所以:

| 门 | 位置 | 查什么 |
|---|---|---|
| 仓内自洽 | `ci.yml` § Version consistency gate | `VERSION` == 每一处的版本串 |
| **VERSION == tag** | `release.yml` § Assert VERSION file matches the tag | tag 与 `VERSION` 不符 ⇒ **构建前**就拒发 |

### 为什么编译器版本号只能是字面量

`main.jhyy` 的横幅是**字符串字面量**。它不能改成运行时读文件 / 调 extern ——
那需要新增局部变量,而**给 `main.jhyy` 加局部变量会移位模块级 temp 编号 ⇒
自举产物行为漂移**(v4.0.20 实测:一条 1 字节读被整条丢掉 ⇒ `--target=` 不再
被识别 ⇒ 6 个 sysv 用例全红)。字符串字面量改动是安全的 ⇒ 自动化只能落在
「改字面量」这一层 ⇒ 脚本改源码 + `make` 重编,顺序不能反。

---

## 手动验证流水线

当需要排查 codegen / 链接问题时，手动走一遍：

```bash
# 1. 编译 .jhyy → 生成 .s (v2.15.0 起默认 in-mem path 不写盘;force 写盘设 JHY_WRITE_IL=1)
./compiler/build/bin/jhyy.exe compile test.jhyy -o test

# 2. v2.15.0+: 默认 in-mem self-backend 不写 .il/.s 文件。如需查看 .s 输出:
JHY_WRITE_IL=1 JHY_SELF_BACKEND=1 ./compiler/build/bin/jhyy.exe compile test.jhyy -o test
cat compiler/build/bin/test.s

# 3. 手动链接(需 runtime.c + jhyy_helpers.c,jhyy 编 jhyy 必需)
/c/msys64/ucrt64/bin/gcc.exe test.s compiler/runtime/runtime.c compiler/src0/jhyy_helpers.c -o test.exe -lm

# 4. 检查退出码
./test.exe; echo $?
```

> **v4.0.0 注**:QBE 工具链已完全移除,不再有 `./qbe/qbe.exe` step。self-backend 是 sole production path (per `docs/plans/v2/v4.0.0-plan.md`)。

---

## 多 target 编译示例 (v2.0.0+)

> v2.0.0 起 `jhyy.exe compile <src.jhyy> --target=<triple> -o <out>` CLI flag 决定目标 target;默认 `amd64_win`(v1.x 兼容)。完整 target 三元组 + ABI 差异表见 [`docs/abis/jhyy-abi-v4.0.0.md` § 13.1-13.2](../abis/jhyy-abi-v4.0.0.md)。

### amd64_win (hosted, default)

```bash
jhyy.exe compile hello.jhyy -o hello.exe                    # 默认 target
jhyy.exe compile hello.jhyy --target=amd64_win -o hello.exe
```

行为跟 v1.x 完全一致。生成 PE/COFF x86-64 `.exe`,链 ucrt + vcruntime(MSYS2 GCC)。

### amd64_win_freestanding (UEFI / 裸机)

```bash
jhyy.exe compile hello_efi.jhyy --target=amd64_win_freestanding -o hello.obj
```

生成 PE/COFF x86-64 `.obj`,**不**链 ucrt / vcruntime / libc。entry 由用户 `extern fn efi_main` / `_start` 提供(per [`docs/abis/jhyy-lang-spec-v4.0.0.md` § 18](../abis/jhyy-lang-spec-v4.0.0.md))。**v2.3.0 已 ship** (tag `v2.3.0` commit `54d93df`, 2026-09-04) — 完整 E2E 链路:`scripts/dev/build/build-efi.sh` (jhyy → .obj → lld-link `/SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main hello.obj /OUT:hello.efi`) + `scripts/dev/test/run-ovmf.sh` (QEMU + OVMF q35 + FAT12 image + serial capture);**E2E 5/5 PASS** 同 .efi 5 次启动输出 "Hello from jhyy freestanding!\n"(详见 [`docs/abis/jhyy-abi-v4.0.0.md` § 13.3 freestanding 约定](../abis/jhyy-abi-v4.0.0.md))。

### amd64_sysv_stub (Linux 兼容 stub)

```bash
jhyy.exe compile hello.jhyy --target=amd64_sysv_stub -o hello.s
```

**当前 `cg_module` 在此 target 仍 fatal**(`amd64_sysv target: 实现留 v2.x M2`,per 2026-09-04 user 决定保留 fatal 不动 `codegen.jhyy:3783-3786`),只产出占位 `.s`;实实现 SysV ABI 推 v2.x M2 (跟 v2.x 中期自写 QBE 后端同期)。target_dispatch + CLI flag + `target_help` / `target_status` 已就位(per [`compiler/src0/target_dispatch.jhyy`](../../compiler/src0/target_dispatch.jhyy) v2.4.0 Stage 1),仅 codegen 路径未实现。

---

## 回归测试

```bash
python compiler/build/bin/regress.py
```

自动运行 `compiler/tests/examples/*.jhyy` 所有测试，输出(v2.4.0 baseline):
```
===== 104/104 passed, 0 failed, 4 skipped (of 108 total) =====
```

无 `main_jhyy` 的库文件（`mylib.jhyy`、`ns_dup_*.jhyy`）自动 SKIP，不计入 passed/failed。

**v2.15.0** — 默认 backend 走 in-mem self path (`JHY_WRITE_IL=0` 不写盘),regress 数提升至 126/147 PASS (per W-074.14 closure)。env var `JHY_WRITE_IL=1` 给 QBE / debug 路径强制走 file I/O round-trip。详见 `docs/internal/architecture.md` §"In-Mem Pipeline"。

---

## 单元测试

**v4.0.21(M5 Part 1)起没有 C 端单元测试了。**

`compiler/tests/unit/test_{lexer,parser,sema,sprint1b}.c` 测的是 **C 端**的
lexer / parser / sema(它们 `#include "../../src/*.h"`)。`compiler/src/` 整个目录
被删掉之后,这几个测试**再也编不出来**,而且它们要测的代码**已经不存在了**
⇒ 已随 M5 Part 1 一并删除。

⇒ 现在的测试覆盖**全部**在 `.jhyy` 集成测试里(`compiler/tests/examples/`),
由 `python regress.py` 跑;C 桥那一层的门是
`compiler/tests/bootstrap/artifact_checks.sh`。

---

## 修改代码后的验证步骤

1. `gcc` 编译零警告
2. `hello.jhyy` 编译运行 → EXIT:42
3. `demo.jhyy` 编译运行 → EXIT:0
4. 改动涉及的相关特性测试编译运行 → 预期退出码
5. 改了 codegen：目视检查 `.il` 文件（QBE IL 语法正确性）
6. 改了 sema：检查错误消息是否包含文件名和行号
7. 全量回归：`python compiler/build/bin/regress.py`

---

## Backend 历史注（v4.0.0 之前）

> **v4.0.0 起**:QBE 工具链**完全移除**。`run_qbe` 改 fatal-stub (签名保留);`qbe/` git rm 41 files;qbe.exe mirror 删;installer/license.rtf/wxs QBE 引用删;`build.md` "QBE 后端坑" section 历史归档 (per `docs/plans/v2/v4.0.0-plan.md`)。self-backend 是 sole production path。

~~**QBE 后端坑（Windows 独有, v4.0.0 起历史归档）**~~:

1. ~~**临时变量必须带字母前缀**：`%t0`, `%t1`... 不能用 `%0`, `%1`（QBE Windows 构建拒绝纯数字）~~
2. ~~**缩进必须是空格**：4 空格，不能用 tab（QBE Windows 构建 tab 解析有 bug）~~
3. ~~**QBE 参数顺序**：`qbe -o output.s input.il`（输出在前，和常见 CLI 相反）~~
4. ~~**目标平台**：`-t <target>` 由 `--target=` CLI flag 决定(v2.0.0+,per [`docs/abis/jhyy-abi-v4.0.0.md` § 13.1](../abis/jhyy-abi-v4.0.0.md));v2.0 接受 `amd64_win` / `amd64_win_freestanding` / `amd64_sysv_stub` 三值,v1.x 仅 `amd64_win`(Windows x64 PE)。QBE 实际 backend 只认 `amd64_win` / `amd64_sysv` 两值,freestanding 复用 `amd64_win`(per D-GUI-12);SYSV 实 impl 推 v2.x M2~~

见 `docs/internal/architecture.md` 中 codegen 相关章节(以 self-backend 路径为准)。

---

## v1.8.2 patch — `.jhyy` 文件图标修复 (UserChoice hijack + OpenWithProgids shadow)

**问题**: v1.8.1 patch 修了 WiX `(default)` 写错位 + `jhyy.exe,0` embedded icon, 但仍有两层独立 hijack 让文件夹视图显示白板文档图标:

1. **VSCode UserChoice hijack**: `HKCU\…\FileExts\.jhyy\UserChoice\ProgId = Applications\Code.exe`, UCPD.sys 加 Deny ACE 防非 admin SetValue
2. **MSYS2 OpenWithProgids 残留**: `HKCU\…\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file` (v1.8.1 step 4 没清)

**修复路径 (v1.8.3.1 ship 后 — MSI install 全自动)**:
- 注册自定义 ProgId `JHYY.EditInVSCode` (`DefaultIcon=jhyy-icon.ico,0` + `shell\open\command=Code.exe "%1"`)
- 用 Mozilla reverse-engineered UserChoice Hash 算法 (`installer/common/jhyy-setuc/Program.cs`, MPL 2.0) 写 `UserChoice\ProgId=JHYY.SourceFile`(v1.8.3.1 起改用 `JHYY.SourceFile`,跟 HKLM 默认 ProgId 对齐)
- MSI install 时 WiX CustomAction `JHYYSetUCForAllUsers` (Execute="deferred" + Impersonate="no" + SYSTEM context, per `installer/compiler/jhyy-compiler.wxs`) 自动跑 `jhyy-setuc.exe --system-context` 写每个 interactive user 的 `HKEY_USERS\<sid>\…\UserChoice`。SYSTEM trust chain bypass UCPD.sys kernel filter,完全无人手参与。
- v1.8.3.1 真修 (`ba071d8`): 3-attempt 修 CustomAction `0x80004005` 静默失败 (property resolve in deferred CA → WiX `<Binary>` ≠ property → `.NET 8 apphost` 缺 `.dll/.deps.json/.runtimeconfig.json`),最终 ship 4 个 .NET 8 file + 2-step immediate→deferred CA pattern。

**新装 MSI (v1.8.3.1+)**: WiX CustomAction install 时自动写 UserChoice, **完全无需手动操作**。老的 v1.8.0/v1.8.1/v1.8.2 机器如需升级 icon, 跑 `powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Program Files\JHYY\bin\manual-fix-icon-cache.ps1"` (admin elevate, **不要用 v1.8.2 时期 `C:\Users\liuzhen\Desktop\JHYY-Fix-Icon.bat`** — 该脚本已删, 它 wrap 的 ps1 现在直接通过 INSTALLDIR 路径跑)。

**jhyy-setuc.exe build** (修改 `installer/common/jhyy-setuc/Program.cs` 后):
```bash
cd installer/common/jhyy-setuc && powershell -NoProfile -ExecutionPolicy Bypass -File ./build.ps1
# 输出: bin/Release/net8.0-windows/jhyy-setuc.exe
```
MSI rebuild 时自动重新包进 `INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe` (WiX `JHYYSetUCExe` Component, per `installer/compiler/jhyy-compiler.wxs`).

**已知 limitation**: 需用户机装 .NET 8 Desktop Runtime. 缺失时 jhyy-setuc.exe 启动失败 → `manual-fix-icon-cache.ps1` 自动降级 Path A (只 reg delete, 不需 .NET).

## v1.8.3 patch — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice (UCPD.sys kernel filter bypass)

**问题**: v1.8.2 Path B (`sc stop UCPD` → Mozilla 算法写 UserChoice) 在 Win10 2024-02+ 失败 — `sc stop UCPD` 返回 exit 5 (access denied), 即使 admin + elevated shell。**UCPD.sys** (User Choice Protection Driver, FILE_SYSTEM_DRIVER Type=2 State=4 RUNNING) 是 kernel filter, 加 non-inherited Deny ACE on `HKCU\…\FileExts\.<ext>\UserChoice`, user-mode caller 即使 admin 也被挡。`sc stop` / `sc pause` / `fltmc unload` / `sc sdset` 全 access denied — UCPD 设计上不可程式化卸载。

**Field diagnosis 2026-08-29** (per `feedback_fix_evaluation_rule` 5/5 PASS on target test):
- `sc create obj= LocalSystem type= own start= demand` 创的 LocalSystem service 调 `Registry.CurrentUser.CreateSubKey(UserChoice)` **成功** — 写 `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` 完整。
- SYSTEM trust chain (有 `SeRestorePrivilege` + `SeBackupPrivilege` + `SeTakeOwnershipPrivilege`) **bypass UCPD Deny ACE**, 不需要停 UCPD。
- SYSTEM 的 HKCU 是 `S-1-5-18` 自己 hive — 要写其他 user HKCU, 直接 enumerate `HKEY_USERS` S-1-5-21-… SIDs + 写每个 user 的 `HKEY_USERS\<sid>\…`。

**修复 (v1.8.3 SYSTEM-context CA + Bundle .NET 8 chain)**:

### Phase 1 — `jhyy-setuc.exe --system-context` mode
新增 CLI flag path (`installer/common/jhyy-setuc/Program.cs`):
```bash
jhyy-setuc.exe --system-context .jhyy JHYY.SourceFile
```
- 遍历 `HKEY_USERS` S-1-5-21-… SIDs (跳过 SYSTEM / LocalService / NetworkService / `_Classes` mirror)
- 对每个 user: 算 Mozilla Hash (用 **target user SID**, 不是 caller SID) + 写 `HKEY_USERS\<sid>\…\FileExts\<ext>\UserChoice` + ApplicationAssociationToasts
- Full success 写 sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied` (HKLM → per-user RunOnce 可读)

### Phase 2 — WiX MSI CustomAction (`installer/compiler/jhyy-compiler.wxs`)
```xml
<Binary Id="JHYYSetUCBin"
        SourceFile="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe" />

<CustomAction Id="JHYYSetUCForAllUsers"
              BinaryRef="JHYYSetUCBin"
              ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile"
              Execute="deferred"
              Impersonate="no"
              Return="ignore" />

<InstallExecuteSequence>
  <Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />
</InstallExecuteSequence>
```

关键 attribute:
- `BinaryRef="JHYYSetUCBin"` + `<Binary>` definition → MSI extract 到 temp + auto-resolve `[JHYYSetUCBin]` property (Type 50 CA, 不需 CustomActionData 预设)
- `Execute="deferred"` + `Impersonate="no"` → **SYSTEM context** (LocalSystem perMachine install)
- `Return="ignore"` → CA 失败不 rollback install (icon 是 best-effort)
- `Condition="NOT Installed"` (WiX 4 必须 `Condition` attribute, 不是 inner text — WIX0400 error)

`<RemoveRegistryValue>` 清 sentinel on uninstall (per `JHYYPathReg` Component)。

### Phase 3 — Bundle .NET 8 chain (`installer/Bundle.wxs`)
```xml
<util:RegistrySearch Id="Net8RuntimeSearch"
                     Variable="Net8RuntimeVersion"
                     Root="HKLM"
                     Key="SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost"
                     Result="value" />

<Chain>
  <ExePackage Id="Net8Runtime"
              SourceFile="$(var.JHY_DOTNET8_RUNTIME_EXE_PATH)"
              DisplayName=".NET 8 Desktop Runtime"
              Compressed="yes" Vital="yes" Permanent="yes"
              InstallArguments="/quiet /norestart"
              RepairArguments="/quiet /norestart"
              UninstallArguments="/uninstall /quiet /norestart"
              DetectCondition="Net8RuntimeVersion" />
  <MsiPackage Id="JHYYCompilerMsi" ... />
</Chain>
```

关键 attribute (WiX 4 跟 v3 不一样):
- `<util:RegistrySearch>` 用 `Result="value"` (不是 v3 `Format="raw"`) — 需要 `WixToolset.Util.wixext` extension
- `<ExePackage>` 用 `InstallArguments` (不是 v3 `InstallCommand`) — `RepairArguments` / `UninstallArguments` 同理
- `DetectCondition` 在 `ExePackage` 是 supported (vs MsiPackage 用 InstallCondition)
- `Permanent="yes"` → shared runtime, Bundle uninstall 不移除

### Phase 4 — install-configure-all.bat sentinel
Step 6 头加 sentinel check:
```batch
reg.exe query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied >nul 2>&1
if not errorlevel 1 (
    echo [install-configure-all] v1.8.3 sentinel found - MSI CustomAction already wrote per-user UserChoice, skipping step 6
    goto :skip_post_install_user_choice
)
```
若 sentinel 存在 → 跳过 `manual-fix-icon-cache.ps1` (避免 RunOnce user-context 重新写覆盖 v1.8.3 SYSTEM-context 写)。

### Bundle build (`installer/build.ps1 bundle`)
- 自动 download .NET 8 Desktop Runtime 8.0.30 (~28MB) 到 `installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe` (从 `https://dotnetcli.azureedge.net/dotnet/Runtime/8.0.30/`),若已 cache skip download
- `wix build ... -ext "$balDll" -ext WixToolset.Util.wixext -d "JHY_DOTNET8_RUNTIME_EXE_PATH=..."`

### 验证 (5/5 PASS per `feedback_fix_evaluation_rule`)
- ✅ jhyy-setuc.exe --system-context 从 SYSTEM service 写 liuzhen HKEY_USERS UserChoice (Hash 含 target SID)
- ✅ HKEY_USERS\S-1-5-18 (SYSTEM) **不动** (v1.8.3 显式 skip)
- ✅ Sentinel 写入 (full success)
- ✅ MSI 1.29 MB (跟 v1.8.2 持平, `<Binary>` reference 不重复 ship)
- ✅ Bundle 29.99 MB (MSI + .NET 8 + Burn overhead)
- ✅ `regress` 102/102 + 4 SKIP (v1.8.2 baseline 持平, v1.8.3 不改 codegen)

---

## v2.13.0 — 真 XMM regalloc + 真 amd64_sysv codegen 全覆盖 + amd64_sysv_freestanding 真 E2E

> **Last updated**: v2.13.0 (2026-09-19) — 🎯 自写后端**真 E2E** (XMM regalloc + SysV codegen + efi 真 boot)。3 个新增验证 recipe:

### 1. XMM regalloc pressure test (`xmm_pressure_9args.jhyy`)

测试 Win XMM0-XMM5 caller-saved + XMM6-XMM15 callee-saved save/restore + 5+ f64 arg stack-arg fallback 真修:

```bash
./compiler/build/bin/jhyy.exe run compiler/tests/examples/xmm_pressure_9args.jhyy 2>&1 | tail -5
# 期望: EXIT=255 (9 f64 arg sum = 255)
```

跑 5 次 (per `feedback_fix_evaluation_rule`) → EXIT=255 每次都对。

### 2. 真 amd64_sysv codegen 全覆盖 (`sysv_full_regress.sh`)

跑 5 sysv tests (`sysv_abi_test` / `sysv_struct_mixed` / `sysv_struct_pass` / `sysv_struct_ret` / `sysv_vararg_basic`) 走 self-backend 真 emit → docker gcc:12 chain crt0.S + link.ld → ELF → 跑真验 exit codes:

```bash
bash compiler/tests/bootstrap/sysv_full_regress.sh 2>&1 | tail -20
# 期望: 5/5 PASS 每次都对 (sysv_abi_test=28 / sysv_struct_mixed=42 / sysv_struct_pass=35 / sysv_struct_ret=18 / sysv_vararg_basic=42)
```

**关键陷阱** (per `feedback_docker_local`):
- **不要 `MSYS_NO_PATHCONV=1` 套 jhyy.exe 调用** — jhyy.exe 是 Win32 binary 不识 POSIX path, MSYS 默认 convert POSIX → Windows 才能 open file
- **Stage 1 (jhyy compile) 用 default path conv**, **Stage 2 (docker chain) 用 `MSYS_NO_PATHCONV=1`** — docker mount volume 需要 POSIX path

### 3. amd64_win_freestanding 真 E2E (`run-ovmf.sh`)

**QEMU 10 chardev syntax 迁移** (vs QEMU 8 `-debugcon file:stdio -global isa-debugcon.iobase=0x402`):

```bash
SERIAL_LOG=/tmp/_ovmf_serial.log
DEBUG_LOG=/tmp/_ovmf_dbg.log

# QEMU (Win32 binary) 不能 open MSYS POSIX path → cygpath -w convert
SERIAL_LOG_WIN=$(cygpath -w "$SERIAL_LOG")
DEBUG_LOG_WIN=$(cygpath -w "$DEBUG_LOG")

bash scripts/dev/test/run-ovmf.sh compiler/tests/examples/hello-freestanding/hello-freestanding.efi 2>&1 | tail -30
# 期望: OVMF QEMU E2E 5/5 PASS (ConOut 可见 "Hello from jhyy freestanding!" + clean shutdown)
```

**QEMU 10 vs QEMU 8 syntax diff**:
- `-debugcon file:stdio` → `-chardev "file,id=dbgcon,path=$DEBUG_LOG_WIN" -device isa-debugcon,chardev=dbgcon`
- `-global isa-debugcon.iobase=0x402` (deprecated, now via -device)
- `-serial "file:$SERIAL_LOG_WIN"` (was `stdio` or `file:<path>` mixed syntax)

**Stray QEMU process 释放 file handle** (per `feedback_il_s_debugging_pattern`):
```bash
powershell -Command "Get-Process qemu-system-x86_64 | Stop-Process -Force"
```

### SysV classification helpers (8-class §A.4)

`abi_amd64_sysv.jhyy` 真修 SysV ABI §A.4 8-class classification:
- `INTEGER` (8/16/32/64-bit 整数 + 指针)
- `SSE` (单精度/双精度 float, 走 XMM 寄存器)
- `SSEUP` (SSE 上半部分, 16-byte float 第二 8 字节)
- `MEMORY` (>16-byte struct, 走 stack memory)
- `NO_CLASS` (空 placeholder)

Class-to-QBE-letter map: `SSE → QBE_S(4B)/QBE_D(8B)`, `INTEGER/SSEUP/MEMORY → QBE_W/QBE_L` per size, `NO_CLASS → 0`。

**关键教训** (per `feedback_jhyy_no_forward_ref`): jhyy sema 是 single-pass,function 定义必须 precede 所有 uses,不支持 forward reference。新加 wrapper 函数 `abi_sysv_classify_arg_full` 调 `abi_sysv_classify_arg`,wrapper 必须放在后者**之后**(call graph topology 排序)。否则 sema 报 "undefined variable" 但指向无关文件(cascading error 误导)。
