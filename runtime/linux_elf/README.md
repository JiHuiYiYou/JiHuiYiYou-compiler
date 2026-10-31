# runtime/linux_elf — Linux ELF 运行时

> `amd64_sysv_freestanding` 目标用的**静态链接、无 libc** 的 Linux ELF64 运行时。

| 文件 | 作用 |
|---|---|
| [`crt0.S`](crt0.S) | `_start` 入口 —— SysV psABI § 3.2.2 的 16 字节栈对齐 + Linux x86_64 系统调用表 |
| [`link.ld`](link.ld) | 链接脚本 —— 位置无关的静态可执行文件，2 个 PT_LOAD（text RX + data RW） |

产出的 ELF：**无 glibc / 无 libc 依赖**（freestanding 运行时自己管一切），
entry = `_start`，`ET_EXEC` + `EM_X86_64`。

---

## 怎么用

### 两段式（正常路径）

```bash
# 1. Windows 侧：只出 .s,不链接(Windows 上链不出 ELF)
jhyy compile hello.jhyy --target=amd64_sysv_freestanding --no-link -o hello

# 2. Linux 侧：链 + 跑
gcc -nostdlib -static -T runtime/linux_elf/link.ld \
    -o hello.elf runtime/linux_elf/crt0.S hello.s
./hello.elf
```

完整 6 用例的门（自带 docker gcc:12 chain）：

```bash
bash compiler/tests/bootstrap/sysv_full_regress.sh --runs=1
```

### 手工验证产物

```bash
readelf -h hello.elf    # 验 ET_EXEC + EM_X86_64 + entry _start
```

---

## 约定

`jhyy` 的 `cmd_run` 前置检查（per W-65）会检查这个运行时的调用约定：
`_start` 由 crt0 提供，用户程序从 `main_jhyy` 进入。

---

## 相关

- 多 target 与交叉编译 ⇒ [`docs/internal/build.md`](../../docs/internal/build.md) § 多 target
- ABI（SysV 分类）⇒ [`docs/abis/jhyy-abi-v4.0.0.md`](../../docs/abis/jhyy-abi-v4.0.0.md)
- 目标三元组清单 ⇒ [`docs/internal/FACTS.md`](../../docs/internal/FACTS.md) § 5
