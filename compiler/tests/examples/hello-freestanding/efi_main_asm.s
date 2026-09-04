# efi_main_asm.s — pure-asm efi_main test for OVMF COM1 capture verification
#
# Built into a tiny EFI binary that prints "JHYY\n" to COM1 and returns.
# Used to validate that OVMF + QEMU -serial file: actually captures COM1
# output from our EFI app entry point — independent of jhyy compile.
#
# Build (manual, no jhyy):
#   gcc -c -o efi_main_asm.obj efi_main_asm.s
#   lld-link /SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main /MACHINE:X64 \
#           /OUT:efi_main_asm.efi efi_main_asm.obj
#
# Args (MS x64 EFIAPI): rcx = ImageHandle, rdx = *EFI_SYSTEM_TABLE.
.globl efi_main
efi_main:
    movb    $'J', %al
    movl    $0x3F8, %edx
    outb    %al, %dx
    movb    $'H', %al
    outb    %al, %dx
    movb    $'Y', %al
    outb    %al, %dx
    movb    $'Y', %al
    outb    %al, %dx
    movb    $'\n', %al
    outb    %al, %dx
    xorl    %eax, %eax
    ret