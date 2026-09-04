# efi_helpers.s — v2.3.0 Stage 1 assembly helper for hello-freestanding.efi
#
# Workaround for W-062: jhyy v2.3.0 parser rejects `fn (...) -> ...` as a type
# alias, so we cannot store EFI protocol function pointers with their signatures
# in struct fields. Instead, efi.jhyy models each protocol fn ptr as a u64
# placeholder and the user loads it manually as a u64 value, then calls through
# this helper which does the indirect MS x64 call.
#
# **ABI: MS x64** (per D-GUI-12 LOCKED: UEFI = MS x64).
#   - Integer args: rcx, rdx, r8, r9 (left-to-right).
#   - Caller reserves 32-byte shadow space on the stack before each call
#     (QBE emits `subq $32, %rsp` before every callq in hello-freestanding.s).
#   - Caller-saved regs: rax, rcx, rdx, r8-r11, xmm0-xmm5.
#   - Callee-saved regs: rbx, rbp, rdi, rsi, r12-r15, xmm6-xmm15.
#     → ALL helpers below must save+restore rbx, rbp, rdi, rsi.
#
# Signatures:
#
#   uint64_t efi_call_via_ptr(uint64_t fn_ptr, void *this, void *arg2);
#       rcx = fn_ptr (u64)
#       rdx = this    (1st arg for the callee)
#       r8  = arg2    (2nd arg for the callee)
#       Returns rax.
#
#   int64_t jhyy_ascii_to_ucs2(char *input, uint16_t *output, int64_t max_chars);
#       rcx = input  (*u8 ASCII)
#       rdx = output (*u16 UCS-2)
#       r8  = max_chars
#       Returns rax = chars written.
#
#   void serial_putc(uint64_t c);
#       rcx = c (low byte = char to write)
#
#   void serial_puts(char *s);
#       rcx = s (*u8 NUL-terminated)
#
# Linked by scripts/dev/build/build-efi.sh alongside the jhyy-compiled .obj.

.text

# ══════════════════════════════════════════════════════════════════
# efi_call_via_ptr — indirect call helper (W-062 workaround)
# ══════════════════════════════════════════════════════════════════
.globl efi_call_via_ptr
efi_call_via_ptr:
    pushq   %rbp
    movq    %rsp, %rbp
    pushq   %rbx
    pushq   %rdi
    pushq   %rsi

    movq    %rcx, %rax           # fn_ptr → rax (call target)
    movq    %rdx, %rcx           # this → rcx (callee's 1st arg slot)
    movq    %r8,  %rdx           # arg2 → rdx (callee's 2nd arg slot)
    call    *%rax

    popq    %rsi
    popq    %rdi
    popq    %rbx
    popq    %rbp
    ret

# ══════════════════════════════════════════════════════════════════
# jhyy_ascii_to_ucs2 — convert ASCII C string to UCS-2 (UTF-16 LE) buffer
# ══════════════════════════════════════════════════════════════════
.globl jhyy_ascii_to_ucs2
jhyy_ascii_to_ucs2:
    pushq   %rbp
    movq    %rsp, %rbp
    pushq   %rbx
    pushq   %rdi
    pushq   %rsi

    movq    %rcx, %rsi          # rsi = input (ASCII)
    movq    %rdx, %rdi          # rdi = output (UCS-2)
    movq    %r8,  %rcx          # rcx = max_chars (use as counter)

    xorq    %rax, %rax          # rax = chars written counter

.Lascii_loop:
    testq   %rcx, %rcx
    jz      .Lascii_done
    movb    (%rsi), %bl
    testb   %bl, %bl
    jz      .Lascii_done
    movb    %bl, (%rdi)
    xorl    %edx, %edx
    movb    %dl, 1(%rdi)
    incq    %rsi
    addq    $2, %rdi
    incq    %rax
    decq    %rcx
    jmp     .Lascii_loop

.Lascii_done:
    xorl    %edx, %edx
    movw    %dx, (%rdi)

    popq    %rsi
    popq    %rdi
    popq    %rbx
    popq    %rbp
    ret

# ══════════════════════════════════════════════════════════════════
# serial_putc — write one ASCII byte to COM1 UART (I/O port 0x3F8)
# ══════════════════════════════════════════════════════════════════
.globl serial_putc
serial_putc:
    pushq   %rbp
    movq    %rsp, %rbp
    pushq   %rbx
    pushq   %rdi
    pushq   %rsi

    movb    %cl, %al            # low byte of rcx = char
    movl    $0x3F8, %edx        # COM1 data register
    outb    %al, %dx

    popq    %rsi
    popq    %rdi
    popq    %rbx
    popq    %rbp
    ret

# ══════════════════════════════════════════════════════════════════
# serial_puts — write NUL-terminated ASCII string to COM1
# ══════════════════════════════════════════════════════════════════
.globl serial_puts
serial_puts:
    pushq   %rbp
    movq    %rsp, %rbp
    pushq   %rbx
    pushq   %rdi
    pushq   %rsi

    movq    %rcx, %rdi          # rdi = string ptr

    movb    (%rdi), %al
    testb   %al, %al
    jz      .Lputs_done
.Lputs_loop:
    movl    $0x3F8, %edx
    outb    %al, %dx
    incq    %rdi
    movb    (%rdi), %al
    testb   %al, %al
    jnz     .Lputs_loop
.Lputs_done:
    popq    %rsi
    popq    %rdi
    popq    %rbx
    popq    %rbp
    ret