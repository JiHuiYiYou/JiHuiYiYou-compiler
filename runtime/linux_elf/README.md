# Linux ELF runtime for jhyy

Statically-linked, freestanding Linux ELF64 runtime for the **jhyy**
self-hosting compiler (`amd64_sysv_freestanding` target).

Mirrors the UEFI freestanding runtime template from v2.4.0
(`compiler/tests/examples/hello-freestanding/`), but for **Linux userspace**
(SysV AMD64 ABI) instead of UEFI (MS x64 + EFIAPI calling convention).

## Files

| File | Purpose |
|---|---|
| `crt0.S` | `_start` entry point: pop argc/argv, align stack to 16-byte (SysV § 3.2.2), zero frame pointer, `call main_jhyy` (jhyy convention per W-65), `SYS_exit` syscall with return code in `%edi` |
| `link.ld` | Linker script: `OUTPUT_FORMAT(elf64-x86-64)`, `ENTRY(_start)`, 2 `PT_LOAD` PHDRs (text RX + data RW), standard `.text/.rodata/.data/.bss` layout |
| `README.md` | This file — build invocations + verify commands |

## Build (jhyy → ELF executable)

```bash
# From repo root (JiHuiYiYou-axis-v2):
# 1. Compile jhyy source to amd64_sysv_freestanding target assembly:
./compiler/build/bin/jhyy.exe compile \
    --target=amd64_sysv_freestanding \
    compiler/tests/examples/hello.jhyy \
    -o compiler/build/bin/hello

# jhyy produces:
#   - compiler/build/bin/hello.il      (QBE IL, unused for elf link)
#   - compiler/build/bin/hello.s       (x86_64 assembly)
#   - compiler/build/bin/hello.exe     (Windows PE, unused on Linux)

# 2. Link with crt0 + linker script (NOT jhyy's Windows .exe):
gcc -nostdlib -static -T runtime/linux_elf/link.ld \
    -o /tmp/hello.elf \
    runtime/linux_elf/crt0.S \
    compiler/build/bin/hello.s

# 3. Verify the ELF binary:
readelf -h /tmp/hello.elf      # ET_EXEC, EM_X86_64, Entry=0x400000+...
file /tmp/hello.elf            # ELF 64-bit LSB executable, x86-64
```

## Run

### On Linux host

```bash
chmod +x /tmp/hello.elf
/tmp/hello.elf                 # runs main_jhyy, returns main_jhyy's %eax as exit code
echo $?                        # exit code
```

### On Windows via WSL (Windows Subsystem for Linux)

```bash
# Cross-build on Windows:
gcc -nostdlib -static -T runtime/linux_elf/link.ld \
    -o /tmp/hello.elf \
    runtime/linux_elf/crt0.S \
    compiler/build/bin/hello.s

# Run via WSL (binary works because it's Linux x86_64, Windows Linux
# Subsystem can load it directly):
wsl /tmp/hello.elf
```

### On Windows via QEMU (if installed)

```bash
qemu-x86_64 /tmp/hello.elf     # QEMU user-mode emulation, no Linux needed
```

## ABI compliance

Per **System V AMD64 ABI** ([psABI](https://refspecs.linuxfoundation.org/elf/x86-64-abi-0.99.pdf)):

- **§ 3.2.2** Stack alignment: 16-byte boundary at function entry → `andq $-16, %rsp` after `popq %rdi`.
- **§ 3.2.2** Frame pointer: not used (`xorq %rbp, %rbp`) → enables better backtraces.
- **§ 3.2.3** Argument passing: not applicable here (no cross-fn args in crt0; main_jhyy called with no args — argc/argv passed via global / stack).
- **§ A.4** Eightbyte classifier: N/A (no struct args in crt0).

Per **Linux x86_64 syscall table** (kernel `<asm/unistd.h>`):
- `SYS_exit` = `60` (in `%rax`), exit code in `%rdi` (low 32 bits used by kernel).

## Cross-compile workflow integration

The `compiler/build/bin/regress.py` `--cross {wsl,docker,auto,none}` flag
(v2.7.0 argparse stub; v2.7.1 Commit 2 wires it) drives this build flow:

- `--cross=wsl`: invoke `wsl.exe -d <distro> bash -c "<build invocations>"` to compile + run on Linux host
- `--cross=docker`: invoke `docker run --rm -v $PWD:/work -w /work ubuntu:22.04 bash -c "<build invocations>"` to compile + run in Linux container
- `--cross=auto`: probe `wsl.exe` then `docker` on PATH; fall back to `--cross=none` (SKIP)
- `--cross=none`: explicitly SKIP (Windows host without WSL/Docker)

## Status (2026-09-08)

- **Phase 1 of v2.7.1**: runtime files created, build verify pass-through.
- **Phase 2 of v2.7.1**: `regress.py --cross` wire (subprocess + auto-probe).
- **Phase 3 of v2.7.1**: D43 closure re-baseline + docs + ship.

## References

- v2.4.0 hello-freestanding.efi OVMF 5/5 PASS — UEFI runtime template (mirrors crt0/link.ld structure but for EFI, not Linux)
- W-65 cmd_run main_jhyy pre-check: `compiler/src0/driver.jhyy`
- SysV psABI: § 3.2.2 (stack alignment), § 3.2.3 (arg passing), § A.4 (eightbyte classifier)
- Linux x86_64 syscall table: `SYS_exit = 60`
- ELF spec: `ET_EXEC`, `EM_X86_64`, `PT_LOAD` program headers