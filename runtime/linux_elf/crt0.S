# crt0.S — Linux ELF _start entry point for jhyy amd64_sysv_freestanding target
#
# Per SysV psABI § 3.2.2 (16-byte stack alignment) + Linux x86_64 syscall
# table (SYS_exit = 60 in rax).
#
# Build (manual, no jhyy):
#   gcc -nostdlib -static -T runtime/linux_elf/link.ld \
#       -o hello.elf runtime/linux_elf/crt0.S \
#       compiler/tests/examples/hello.jhyy_amd64_sysv_freestanding.s
#   readelf -h hello.elf   # verify ET_EXEC + EM_X86_64 + entry _start
#
# Caller convention (jhyy W-65 cmd_run pre-check):
#   crt0 calls `main_jhyy` (NOT `main`) — jhyy program main fn is named
#   `main_jhyy` per W-65 (v1.8.3.2 ship).
#   Args from kernel: %rdi = argc, %rsi = argv (per Linux x86_64 execve ABI).
#   Return convention: %eax → %edi for SYS_exit status code.

.globl _start
.text

_start:
    # 1. Pop argc off the stack (per Linux x86_64 execve ABI: kernel puts
    #    argc at top of initial stack, argv pointer array follows).
    popq    %rdi                  # %rdi = argc
    mov %rsp, %rsi              # %rsi = argv pointer array

    # 2. Align stack to 16 bytes per SysV psABI § 3.2.2 (jhyy codegen
    #    expects %rsp % 16 == 0 on function entry, e.g. for SSE moves).
    #    Right after `popq %rdi`, %rsp is 8-byte aligned (kernel pushes
    #    8-byte argc); align to 16 by masking low 4 bits.
    andq    $-16, %rsp

    # 3. Clear frame pointer per SysV § 3.2.2 (no frame pointer convention;
    #    enables better backtraces).
    xorq    %rbp, %rbp

    # 4. Call jhyy main_jhyy (per W-65 jhyy main fn convention).
    #    jhyy codegen emits `call $main_jhyy` so the symbol must be
    #    `main_jhyy` not `main`.
    call    main_jhyy

    # 5. Exit with return code from main_jhyy in %eax (per Linux x86_64
    #    syscall convention: SYS_exit = 60 in rax, arg in rdi).
    #    Use `mov %eax, %edi` (zero-extend) since jhyy i32 return is
    #    in %eax; SYS_exit expects int in %edi.
    mov     %eax, %edi
    mov     $60, %rax             # SYS_exit
    syscall