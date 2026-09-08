/* link.ld — Linux ELF linker script for jhyy amd64_sysv_freestanding target
 *
 * Builds a statically-linked, position-dependent Linux ELF executable that:
 *   - Has no glibc / libc dependency (jhyy freestanding runtime owns all)
 *   - Entry point = _start (per crt0.S)
 *   - ELF64 LSB executable for EM_X86_64
 *   - Standard layout: .text (RX) → .rodata (R) → .data (RW) → .bss (RW)
 *   - 2 PT_LOAD program headers (text RX + data RW)
 *
 * Used as: gcc -nostdlib -static -T runtime/linux_elf/link.ld ...
 */

OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)

PHDRS {
    text PT_LOAD FLAGS(5);          /* R-X: readable + executable */
    data PT_LOAD FLAGS(6);          /* RW-: readable + writable */
}

SECTIONS {
    /* Standard Linux x86_64 user-space base address (canonical).
     * Skip ELF header size so first PT_LOAD starts right after. */
    . = 0x400000 + SIZEOF_HEADERS;

    .text : {
        *(.text*)
        *(.text.*)
    } :text

    . = ALIGN(16);
    .rodata : {
        *(.rodata*)
        *(.rodata.*)
        *(.eh_frame*)
    }

    . = ALIGN(16);
    .data : {
        *(.data*)
        *(.data.*)
    } :data

    . = ALIGN(16);
    .bss : {
        *(.bss*)
        *(.bss.*)
        *(COMMON)
    } :data

    /DISCARD/ : {
        *(.note*)
        *(.comment*)
        *(.gnu*)
        *(.note.GNU-stack)
    }
}