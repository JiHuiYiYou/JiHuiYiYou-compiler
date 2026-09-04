#!/usr/bin/env bash
# scripts/dev/build/build-efi.sh — v2.3.0 Stage 2
#
# jhyy .jhyy → .obj → lld-link → .efi (PE32+ EFI Application x86-64)
# Per docs/plans/v2/v2.3.0任务清单 + 概要设计.md § 2.1.3.
#
# Pipeline:
#   1. jhyy compile <input.jhyy> --target=amd64_win_freestanding → <base>.exe
#      (cmd_compile runs build_il + run_qbe + link_with_gcc — uses MS x64 ABI
#       per D-GUI-12; gcc link fails because no main_jhyy, but .s + .il are
#       already on disk)
#   2. gcc -c <base>.s → <base>.obj (assemble to COFF — re-use the .s we just got)
#   3. gcc -c efi_helpers.s → efi_helpers.obj (W-062 extern helpers)
#   4. lld-link /SUBSYSTEM:EFI_APPLICATION /ENTRY:efi_main /MACHINE:X64
#      <base>.obj efi_helpers.obj → <base>.efi

set -uo pipefail

INPUT="${1:?usage: build-efi.sh <input.jhyy>}"
INPUT_BASE="${INPUT%.jhyy}"
JHYY_ROOT="$(git rev-parse --show-toplevel)"
JHYY="$JHYY_ROOT/compiler/build/bin/jhyy.exe"
HELPERS_DIR="$JHYY_ROOT/compiler/tests/examples/hello-freestanding"

# Win-style paths for Windows tools
WIN_JHYY=$(cygpath -w "$JHYY")
WIN_HELPERS_DIR=$(cygpath -w "$HELPERS_DIR")

echo "==> Step 1/4: jhyy compile → .s (link step may fail, that's OK)"
# jhyy compile runs build_il + run_qbe + link_with_gcc. We expect link to fail
# (no main_jhyy for freestanding), but the .il + .s are emitted before linking.
# We capture link failure but don't abort — we still need the .s.
set +e
"$JHYY" compile "$INPUT" --target=amd64_win_freestanding 2>&1 | tail -5
set -e

if [[ ! -f "${INPUT_BASE}.s" ]]; then
    echo "ERR: ${INPUT_BASE}.s not produced — QBE step failed" >&2
    exit 1
fi

echo "==> Step 2/4: assemble ${INPUT_BASE}.s → .obj"
gcc -c -o "${INPUT_BASE}.obj" "${INPUT_BASE}.s"

echo "==> Step 3/4: assemble efi_helpers.s → efi_helpers.obj"
gcc -c -o "${INPUT_BASE}.efi_helpers.obj" "$HELPERS_DIR/efi_helpers.s"

echo "==> Step 4/4: lld-link → .efi"
lld-link \
    /SUBSYSTEM:EFI_APPLICATION \
    /ENTRY:efi_main \
    /MACHINE:X64 \
    /OUT:"${INPUT_BASE}.efi" \
    "${INPUT_BASE}.obj" \
    "${INPUT_BASE}.efi_helpers.obj"

echo ""
echo "==> Built: ${INPUT_BASE}.efi"
echo "==> Verify with: file ${INPUT_BASE}.efi"
echo "==> Boot with:    scripts/dev/test/run-ovmf.sh ${INPUT_BASE}.efi"
