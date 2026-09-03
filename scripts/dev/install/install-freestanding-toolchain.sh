#!/usr/bin/env bash
# scripts/dev/install/install-freestanding-toolchain.sh — v2.3.0 Stage 0
#
# Install lld + copy/generate OVMF firmware for freestanding EFI toolchain.
# Idempotent — re-runnable. JHYY root auto-detected; override via JHYY_ROOT env.
#
# Per docs/plans/v2/v2.3.0任务清单 + 概要设计.md + MSYS2 box audit 2026-09-03.

set -euo pipefail

JHYY_ROOT="${JHYY_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "$0")/../../.." && pwd)")}"
OVMF_SRC="/mingw64/share/qemu"
OVMF_DST="$JHYY_ROOT/compiler/build/ovmf"

echo "==> JHYY root: $JHYY_ROOT"
echo "==> OVMF dst:  $OVMF_DST"

# 1. lld-link (replaces missing MSVC link.exe in freestanding UEFI chain)
echo "==> Installing mingw-w64-x86_64-lld ..."
pacman -S --needed --noconfirm mingw-w64-x86_64-lld

# 2. OVMF code.fd (readonly firmware, copy from MSYS2 QEMU share)
mkdir -p "$OVMF_DST"
echo "==> Copying OVMF firmware from $OVMF_SRC ..."
if [[ -f "$OVMF_SRC/edk2-x86_64-code.fd" ]]; then
    cp -u "$OVMF_SRC/edk2-x86_64-code.fd" "$OVMF_DST/edk2-x86_64-code.fd"
    echo "    OK edk2-x86_64-code.fd ($(stat -c%s "$OVMF_DST/edk2-x86_64-code.fd") bytes)"
else
    echo "    FAIL edk2-x86_64-code.fd not at $OVMF_SRC" >&2
    exit 1
fi

# 3. OVMF vars.fd (NVRAM, writable; MSYS2 ships without x86_64 variant —
#    generate empty 64KB file per OVMF spec; first boot initializes it)
VARS_FD="$OVMF_DST/edk2-vars.fd"
if [[ ! -f "$VARS_FD" ]]; then
    echo "==> Generating 64KB zeroed edk2-vars.fd (MSYS2 ships no x86_64 NVRAM image) ..."
    dd if=/dev/zero of="$VARS_FD" bs=1024 count=64 status=none
    echo "    OK edk2-vars.fd (65536 bytes)"
else
    echo "    OK edk2-vars.fd already present ($(stat -c%s "$VARS_FD") bytes) — leaving untouched"
fi

# 4. Done
echo ""
echo "==> Freestanding toolchain installed. Verify with:"
echo "    scripts/dev/test/verify-freestanding-toolchain.sh"
