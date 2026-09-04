# 构建与运行

> JHYY 编译器构建、.jhyy 程序编译与运行、手动验证流水线。

## 关键路径

```
C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/
├── compiler/src/*.c        # 编译器源
├── compiler/src0/          # jhyy 端自举翻译（v1.x — 与 src/ byte-equal 输出）
├── compiler/runtime/       # 运行时（main → main_jhyy 桥接）
├── compiler/tests/         # 测试
│   ├── examples/*.jhyy     # 集成测试
│   └── unit/*.c            # 单元测试
├── qbe/qbe.exe             # QBE IL 编译器（vendor）
├── mcp-jhyy/               # Claude Code MCP 服务
└── docs/                   # 文档
```

工具：
- GCC：`/c/msys64/ucrt64/bin/gcc.exe` (15.2.0 MSYS2 ucrt64)
- QBE：`./qbe/qbe.exe -t <target>` — **v2.0+ 起**,`jhyy compile --target=<triple>` CLI flag 决定 target(`amd64_win` / `amd64_win_freestanding` / `amd64_sysv_stub`,per [`jhyy-abi-v1.0.0.md` § 13.1](../abis/jhyy-abi-v1.0.0.md));v1.x 默认 `amd64_win`
- Git：`/d/Program Files/Git/bin/git.exe`

---

## 编译编译器 (v1.4.4 stage-0 链)

**Stage 0**: gcc 编译 C 端 bootstrap → `compiler/build/bin/jhyy_stage0.exe`

```bash
gcc -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy_stage0.exe \
    -I compiler/src
```

**Stage 1**: jhyy_stage0.exe 编译 src0/main.jhyy → `compiler/build/bin/jhyy.exe` (production)

```bash
compiler/build/bin/jhyy_stage0.exe compile compiler/src0/main.jhyy \
    -o compiler/build/bin/jhyy
```

**或用 Makefile 一键**:
```bash
make           # = stage0 + stage1, 产 jhyy.exe
make stage0    # 只 stage 0 (改 src/*.c 后)
make selfhost  # stage 1 + 3 次自举 closure (v1 → v2 → v3 → v4 byte-equal)
```

构建产物:
- `compiler/build/bin/jhyy.exe` — jhyy-side 产物 (production, users invoke)
- `compiler/build/bin/jhyy_stage0.exe` — C 端 bootstrap (改 src/*.c 后重建)
- `compiler/build/bin/jhyy.exe.exe` — jhyy.exe baseline (per baseline binary hash rule)
- `compiler/build/bin/jhyy_v1.exe.exe` — v1.0.0 historical baseline (regress.py --binary=jhyy_v1.exe.exe 用, 不可退役 — v1.4.7 合并进 regress.py)

`-Wall -Wextra` 必须零警告。

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

- **`jhyy_stage0.exe`**:Makefile 直接编 `compiler/src/jhyy.rc` → `compiler/build/obj/jhyy-res.o` → 链入(`$(RES_OBJ)`)
- **`jhyy.exe`**:**以及**所有 user-compiled `.jhyy` 程序:`compiler/src/main.c` 的 `compile()` 函数在 `system()` 拼出的 gcc 命令前先调 `windres` 把 `compiler/src/jhyy.rc` 编为 `<output>.ico.o`,链接加入 gcc 命令末尾,结束后 `unlink()` 清理 tmp 文件

**改图标后必须重 build stage0 + stage1**:
```bash
make clean && make stage0 && make
```

不重 build stage0,`jhyy.exe` 内嵌的还是旧 icon(.ico 修改走 `installer/build-jhyy-icons.ps1`,deterministic 重出 6-frame ICO)。

**path 坑**:`windres` 内部走 `gcc -E` 预处理,路径里的 `\` 会被当 escape 字符吃掉。`compiler/src/main.c` 用 `path_to_fwd()` 把 `\` 全部转 `/` 才传给 windres(教训 2026-08-27 v1.8.1 patch 阶段)。

**验证**: `objdump -h compiler/build/bin/jhyy.exe | grep rsrc` 应见 `.rsrc` 段(9184B);`grep -c '89 50 4e 47' <(objdump -s -j .rsrc ...)` 应为 6(每个 ICO frame 内嵌 PNG signature)。

---

## 编译并运行

```bash
./compiler/build/bin/jhyy.exe run <file.jhyy>
```

> **注意**:**v1.x 已修** (`main.c:591` `path_to_win(exe)` 已处理 MSYS ↔ Win32 路径转换),`run` 子命令可用;v1.8.3.2 patch 加 `cmd_run main_jhyy` byte-scan pre-check (W-065,避免库 snippet 报 "undefined reference to main_jhyy")。

---

## 手动验证流水线

当需要排查 codegen / QBE / 链接问题时，手动走一遍：

```bash
# 1. 编译 .jhyy → 生成 QBE IL（停在这一步）
./compiler/build/bin/jhyy.exe compile test.jhyy -o test

# 2. 查看 QBE IL
cat compiler/build/bin/test.il

# 3. 手动调用 QBE (target 由 --target 决定,v1.x 默认 amd64_win)
./qbe/qbe.exe -t <target> -o test.s compiler/build/bin/test.il

# 4. 手动链接(需 runtime.c + jhyy_helpers.c,jhyy 编 jhyy 必需)
/c/msys64/ucrt64/bin/gcc.exe test.s compiler/runtime/runtime.c compiler/src0/jhyy_helpers.c -o test.exe -lm

# 5. 检查退出码
./test.exe; echo $?
```

---

## 多 target 编译示例 (v2.0.0+)

> v2.0.0 起 `jhyy.exe compile <src.jhyy> --target=<triple> -o <out>` CLI flag 决定目标 target;默认 `amd64_win`(v1.x 兼容)。完整 target 三元组 + ABI 差异表见 [`jhyy-abi-v1.0.0.md` § 13.1-13.2](../abis/jhyy-abi-v1.0.0.md)。

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

生成 PE/COFF x86-64 `.obj`,**不**链 ucrt / vcruntime / libc。entry 由用户 `extern fn efi_main` / `_start` 提供(per [`jhyy-lang-spec-v1.3.0.md` § 18](../abis/jhyy-lang-spec-v1.3.0.md))。**v2.3.0 已 ship** (tag `v2.3.0` commit `54d93df`, 2026-09-04) — 完整 E2E 链路:`scripts/dev/build/build-efi.sh` (jhyy → .obj → lld-link `/SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main hello.obj /OUT:hello.efi`) + `scripts/dev/test/run-ovmf.sh` (QEMU + OVMF q35 + FAT12 image + serial capture);**E2E 5/5 PASS** 同 .efi 5 次启动输出 "Hello from jhyy freestanding!\n"(详见 [`jhyy-abi-v1.0.0.md` § 13.3 freestanding 约定](../abis/jhyy-abi-v1.0.0.md))。

### amd64_sysv_stub (Linux 兼容 stub)

```bash
jhyy.exe compile hello.jhyy --target=amd64_sysv_stub -o hello.s
```

**当前 `cg_module` 在此 target 仍 fatal**(`amd64_sysv target: 实现留 v2.x M2`,per 2026-09-04 user 决定保留 fatal 不动 `codegen.jhyy:3783-3786`),只产出占位 `.s`;实实现 SysV ABI 推 v2.x M2 (跟 v2.x 中期自写 QBE 后端同期)。target_dispatch + CLI flag + `target_help` / `target_status` 已就位(per [`compiler/src0/target_dispatch.jhyy`](../../src0/target_dispatch.jhyy) v2.4.0 Stage 1),仅 codegen 路径未实现。

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

---

## 单元测试

```bash
# 单文件单元测试（独立编译运行）
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_lexer.c compiler/src/lexer.c compiler/src/arena.c \
    -o compiler/build/bin/test_lexer.exe -I compiler/src && \
    ./compiler/build/bin/test_lexer.exe

# test_sprint1b 需要链接多个模块
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_sprint1b.c \
    compiler/src/arena.c compiler/src/types.c compiler/src/symtab.c compiler/src/ast.c \
    -o compiler/build/bin/test_sprint1b.exe -I compiler/src && \
    ./compiler/build/bin/test_sprint1b.exe
```

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

## QBE 后端坑（Windows 独有）

1. **临时变量必须带字母前缀**：`%t0`, `%t1`... 不能用 `%0`, `%1`（QBE Windows 构建拒绝纯数字）
2. **缩进必须是空格**：4 空格，不能用 tab（QBE Windows 构建 tab 解析有 bug）
3. **QBE 参数顺序**：`qbe -o output.s input.il`（输出在前，和常见 CLI 相反）
4. **目标平台**：`-t <target>` 由 `--target=` CLI flag 决定(v2.0.0+,per [`jhyy-abi-v1.0.0.md` § 13.1](../abis/jhyy-abi-v1.0.0.md));v2.0 接受 `amd64_win` / `amd64_win_freestanding` / `amd64_sysv_stub` 三值,v1.x 仅 `amd64_win`(Windows x64 PE)。QBE 实际 backend 只认 `amd64_win` / `amd64_sysv` 两值,freestanding 复用 `amd64_win`(per D-GUI-12);SYSV 实 impl 推 v2.x M2

见 `docs/internal/architecture.md` 中 codegen 相关章节。

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
