#!/usr/bin/env bash
# scripts/dev/test/verify-freestanding-toolchain.sh — v2.3.0 Stage 0
#
# Sanity-check freestanding toolchain: lld-link + qemu + OVMF .fd files.
# Exits 0 if all OK, 1 otherwise.

set -uo pipefail
fail=0

JHYY_ROOT="${JHYY_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo "$(cd "$(dirname "$0")/../../.." && pwd)")}"
OVMF_DIR="$JHYY_ROOT/compiler/build/ovmf"

check() {
    if command -v "$1" >/dev/null 2>&1; then
        echo "OK   $1 -> $(command -v "$1")"
    else
        echo "FAIL $1 not on PATH"
        fail=1
    fi
}

check lld-link
check qemu-system-x86_64

for f in edk2-x86_64-code.fd edk2-vars.fd; do
    if [[ -f "$OVMF_DIR/$f" ]]; then
        echo "OK   OVMF $f ($(stat -c%s "$OVMF_DIR/$f") bytes at $OVMF_DIR/$f)"
    else
        echo "FAIL OVMF $f missing at $OVMF_DIR/$f — run scripts/dev/install/install-freestanding-toolchain.sh"
        fail=1
    fi
done

if [[ $fail -eq 0 ]]; then
    echo ""
    echo "Freestanding toolchain ready."
fi
exit $fail
