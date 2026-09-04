#!/usr/bin/env bash
# scripts/dev/test/run-ovmf.sh — v2.3.0 Stage 3
#
# Boot <input.efi> under QEMU + OVMF (UEFI mode). Captures ConOut via QEMU
# debugcon (port 0x402) which EDK2 routes the UEFI console to when launched
# with -debugcon. -nographic alone doesn't capture ConOut; for ConOut we need
# either a VGA display (-display curses) or the debug console.
#
# Per docs/plans/v2/v2.3.0任务清单 + 概要设计.md § 3.1.1, OVMF vars fd is
# copied at install time and not modified (read/write pflash, EDK2 persists
# NVRAM to it).

set -uo pipefail

EFI="${1:?usage: run-ovmf.sh <input.efi> [extra qemu args...]}"
shift || true

JHYY_ROOT="$(git rev-parse --show-toplevel)"
OVMF_DIR="$JHYY_ROOT/compiler/build/ovmf"

[[ -f "$EFI" ]] || { echo "ERR: $EFI not found"; exit 1; }
[[ -f "$OVMF_DIR/edk2-x86_64-code.fd" ]] || { echo "ERR: $OVMF_DIR/edk2-x86_64-code.fd missing — run scripts/dev/install-freestanding-toolchain.sh"; exit 1; }
[[ -f "$OVMF_DIR/edk2-vars.fd" ]] || { echo "ERR: $OVMF_DIR/edk2-vars.fd missing — run scripts/dev/install-freestanding-toolchain.sh"; exit 1; }

# Build a tiny FAT12 image with the EFI binary at /EFI/BOOT/BOOTX64.EFI
# (the standard UEFI removable-media boot path). Uses mtools (mformat/mmd/mcopy).
FAT_IMAGE="$JHYY_ROOT/compiler/build/ovmf/$(basename "${EFI%.efi}").fat.img"
truncate -s 33MiB "$FAT_IMAGE"
mformat -i "$FAT_IMAGE" -F -v "JHYYEFI" ::
mmd -i "$FAT_IMAGE" ::EFI ::EFI/BOOT
mcopy -i "$FAT_IMAGE" "$EFI" "::EFI/BOOT/BOOTX64.EFI"
trap 'rm -f "$FAT_IMAGE"' EXIT

# Start QEMU. Capture ConOut via debugcon (port 0x402 → stdio) — EDK2 routes
# the UEFI console to the debug console when launched with -debugcon file.
# EFI apps that print via ConOut->OutputString will appear here.
# -no-reboot: if the EFI app crashes, don't auto-reboot (we want to see it).
# -monitor none: no HMP monitor over stdio (would mix with debug output).
# -nographic: no SDL/VGA display.
# -nodefaults: don't auto-add any default devices.
# -machine q35: modern machine type with good UEFI support.
qemu-system-x86_64 \
    -machine q35 \
    -drive "if=pflash,format=raw,readonly=on,file=$OVMF_DIR/edk2-x86_64-code.fd" \
    -drive "if=pflash,format=raw,file=$OVMF_DIR/edk2-vars.fd" \
    -drive "format=raw,file=$FAT_IMAGE" \
    -serial stdio \
    -debugcon "file:stdio" -global "isa-debugcon.iobase=0x402" \
    -nographic -monitor none -no-reboot -nodefaults \
    "$@"