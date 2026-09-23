<div align="center">

<div><img src="vscode-ext/icon-animated.svg" width="96" alt="JHYY logo"></div>

<div><img src="vscode-ext/jhyy-calligraphy.png" width="220" alt="机会翼游 calligraphy logo"></div>

### 机会翼游 — A self-hosted, statically typed, compiled systems programming language

**Statically typed. Expression-oriented. Compiled to native via QBE.**

[![Version](https://img.shields.io/badge/version-v1.8.3-00d4aa)](docs/logs/v1/changelog-v1.8.0.md)
[![Status](https://img.shields.io/badge/self--host-byte--equal%20v1%E2%86%92v4-success)](docs/logs/v2/changelog-v2.4.0.md)
[![Backend](https://img.shields.io/badge/backend-QBE-orange)](https://c9x.me/compile/)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey)](#quick-start)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![中文](https://img.shields.io/badge/lang-中文-red)](README.zh-CN.md)

[Quick Start](#quick-start) · [Install](#install) · [Language](#language) · [CLI](#cli) · [Architecture](#architecture) · [Status](#status-v183--v1x-final) · [Roadmap](#roadmap) · [Docs](#docs)

</div>

---

## What is JHYY

JHYY (机会翼游) is a self-designed, statically typed, expression-oriented, compiled systems programming language. The backend is [QBE](https://c9x.me/compile/), producing native x86-64 Windows binaries.

**Design goals**:
- **Self-hosting** — the compiler written in itself, achieving byte-equal closure (✓ v1.0.0)
- **OS development** — aligned with the [JiHuiYiYou-OS](https://github.com/JiHuiYiYou/JiHuiYiYou-OS) project, providing OS-required extensions like inline asm / volatile / naked / `no_std` / `&mut` + lifetime (v3.x roadmap)
- **Native performance** — QBE backend, no runtime / no GC, directly produces PE/COFF binaries

## Install

**Prerequisites** (Windows; v1.x is Windows-only — Linux/macOS land in v2.x via amd64_sysv):

1. **MSYS2** — <https://www.msys2.org/> (Windows 10+ x64)
2. **GCC + binutils** (ucrt64 toolchain) — run in an MSYS2 terminal:
   ```bash
   pacman -S mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-binutils
   ```
3. **PATH** — add `C:\msys64\ucrt64\bin` to your Windows user PATH (PowerShell: `$env:Path += ";C:\msys64\ucrt64\bin"`)

**Build** (one line):

```bash
git clone https://github.com/JiHuiYiYou/JiHuiYiYou-compiler.git
cd JiHuiYiYou-compiler
make           # → compiler/build/bin/jhyy.exe (~5MB)
```

**One-shot installer** (recommended for end users): `installer/jhyy-installer-1.8.3.exe` wires up `jhyy.exe` + `.jhyy` file association + VSCode extension + PATH registration in one step. `installer/jhyy-compiler-1.8.3.msi` is the enterprise / SCCM distribution (no GUI). See [`installer/README.md`](installer/README.md).

**Docker** (optional):

```bash
docker run -it msys2/mingw-w64-ucrt-x86_64 bash
# then follow steps 1-3 above inside the container
```

**VSCode users**: opening this repo triggers `.vscode/settings.json` to add `compiler/build/bin` and MSYS2 PATH to the integrated terminal automatically — no manual setup needed.

> [!IMPORTANT]
> Do NOT use the MinGW `gcc` shipped with Git Bash (`/c/Program\ Files/Git/mingw64/bin/gcc.exe`) — it does not support PE+ linking and will fail at link time.

---

## A tour of the syntax

```rust
// Functions / variables / control flow / struct / match / enum / FFI
type Point = struct { x: i32, y: i32 }

fn dist_sq(a: Point, b: Point) -> i32 {
    let dx = a.x - b.x;
    let dy = b.y - a.y;
    dx * dx + dy * dy
}

fn classify(n: i32) -> *u8 {
    match n {
        0        => "zero",
        1..10    => "single digit",
        10 | 20  => "round number",
        _        => "other",
    }
}

extern fn printf(fmt: *u8, val: i32) -> i32;

fn main_jhyy() -> i32 {
    let p = Point { x: 3, y: 4 };
    let q = Point { x: 0, y: 0 };
    printf("d² = %d\n", dist_sq(p, q));
    printf("%s\n", classify(42));
    0
}
```

---

## Quick Start

### Hello world

```rust
// hello.jhyy
fn main_jhyy() -> i32 {
    42
}
```

```bash
./compiler/build/bin/jhyy.exe compile hello.jhyy -o hello
./hello.exe
echo $?    # => 42
```

### Run the regression suite

```bash
python compiler/build/bin/regress.py
# => 104/104 passed, 0 failed, 4 skipped (of 108 total) — v2.4.0 baseline
```

### Run with VSCode

The repo ships `.vscode/tasks.json` — open any `.jhyy` file and press **`Ctrl+Shift+B`** to compile + run it. Other tasks: `Ctrl+Shift+P` → **Tasks: Run Task** → `JHYY: Run` / `JHYY: Compile` / `JHYY: Build IR`. `.vscode/settings.json` adds `compiler/build/bin` and `C:/msys64/ucrt64/bin` to the integrated terminal PATH so you can also type `jhyy run hello.jhyy` directly. `F5` launches the compiled `.exe` under MSYS2's gdb (cppdbg).

> [!IMPORTANT]
> **MSYS2 PATH requirement** — `jhyy run` shells out to `gcc` for linking, which in turn spawns `cc1.exe` / `as.exe` / `ld.exe` from `C:\msys64\ucrt64\bin`. PowerShell / cmd users outside VSCode need MSYS2 on their system PATH (or they get a silent `gcc link failed`). `.vscode/settings.json` handles this automatically for the integrated terminal; for external shells, add `C:\msys64\ucrt64\bin` to your user PATH manually.

### Verify self-hosting closure

```bash
# Stage 2 N=4 byte-equal — jhyy compiles jhyy
# Method 1: regress through self-hosted compiler (v1.4.7+ single regress entry)
python compiler/build/bin/regress.py --all --include-informational
# Method 2: one-shot closure check via MCP (recommended)
# ask Claude Code: "verify self-host closure" → jhyy_selfhost_check
# See docs/logs/v1/changelog-v1.0.0.md for full procedure
```

---

## Language

| Category | Supported |
|----------|-----------|
| **Types** | `i8/i16/i32/i64`, `u8/u16/u32/u64`, `f32/f64`, `bool`, `*T`, `[T; N]`, `[*]T` (slice), `struct`, `enum` |
| **Casts** | `as` — integer/float conversion, widening/narrowing, `*T ↔ i64/u64` |
| **Control flow** | `if`/`else` (expression-valued), `while`, `for i in start..end`, `break`, `continue`, `match` (literal/range/enum/wildcard, with exhaustiveness check) |
| **Top-level const** | `const NAME: [T; N] = [...]` — compile-time emit to `.data` section |
| **Logic** | `&&` / `\|\|` short-circuit, `!` / `~` unary |
| **Functions** | first-class, recursion, compound assignment (`+=` `-=` `*=` `/=` `%=`), block-expression closures |
| **Modules** | `import` + transitive imports, multi-file CLI, `mod::fn()` namespaces |
| **FFI** | `extern fn` calling C (printf, file I/O, multi-arg) |
| **Memory** | runtime Arena allocator (`arena_alloc` via FFI) |

Full specification: [`docs/abis/jhyy-lang-spec-v1.3.0.md`](docs/abis/jhyy-lang-spec-v1.3.0.md) (locked; v1.3.0 = v1.1.0 + 7 v1.3.x features); known limitations in Appendix B + Appendix E.

---

## CLI

```text
jhyy compile <file.jhyy> [-o name]   compile to .exe (default amd64_win)
jhyy run     <file.jhyy>             compile and run
jhyy build   <file.jhyy> [-o name]   emit QBE IL only (.il file)
jhyy dump    <file.jhyy>             dump parsed AST to stdout (debug)
jhyy                                 print help
```

> [!TIP]
> For multi-file compilation, list every `.jhyy` source on the command line: `jhyy compile main.jhyy lib.jhyy -o app`

---

## Architecture

The JHYY compiler exists in two **fully equivalent** implementations that emit byte-equal QBE IL:

```mermaid
flowchart TB
    cs["<b>compiler/src/</b><br/>C-side · v0.x — production<br/>main.c · lexer · parser · sema<br/>ir · codegen · symtab · types"]
    cs -->|gcc builds| bin1["jhyy.exe"]
    s0["<b>compiler/src0/</b><br/>jhyy-side · v1.x — self-host<br/>main.jhyy · lexer · parser · sema<br/>ir · codegen · symtab · types"]
    bin1 -->|compiles src0| s0
    s0 --> bin2["jhyy_v1.exe.exe"]
    src[".jhyy source"] --> qbe["<b>QBE</b><br/>(qbe/qbe.exe -t amd64_win)"]
    bin1 --> qbe
    bin2 --> qbe
    qbe --> il[".il"] --> as_["as"] --> ln["link"] --> exe[".exe"]
```

| Implementation | Role | Status |
|----------------|------|--------|
| `compiler/src/*.c` | C-side compiler (v0.x era) | production path, maintained |
| `compiler/src0/*.jhyy` | jhyy-side translated source (v1.x era) | self-host path, byte-equal to C-side |
| `compiler/runtime/*.c` | C runtime (Arena + main entry) | linked at compile time |

Both paths emit **byte-equal QBE intermediate representation** — Stage 1 (`jhyy_0.exe` vs `jhyy_v1.exe.exe`) 7/7 byte-equal, Stage 2 (`jhyy_v1 → v2 → v3 → v4 → v5`) N=4 closure reached.

---

## Project layout

```
JiHuiYiYou-compiler/
├── compiler/
│   ├── src/                    C-side compiler source (10 .c / 9 .h files)
│   ├── src0/                   jhyy-side translated source (13 main modules + 11 _driver tests) — self-host path
│   ├── runtime/                C runtime (Arena + main entry)
│   ├── tests/
│   │   ├── examples/           integration tests (53 .jhyy) — regress.py auto-runs
│   │   └── unit/               C unit tests
│   └── build/
│       └── bin/
│           ├── jhyy.exe        C-side compiler binary
│           ├── jhyy_v1.exe.exe self-hosted compiler (jhyy compiled src0/)
│           └── regress.py      regression script
├── qbe/                        vendored QBE backend (c9x.me/compile)
├── mcp-jhyy/                   Claude Code MCP server (11 tools + 4 resources)
├── vscode-ext/                 VS Code language extension (syntax highlighting)
├── scripts/
│   └── dev/                    dev/ install-uninstall helpers, bench, test orchestrators (relative paths, portable)
├── docs/
│   ├── abis/                   language spec + ABI whitepaper (locked)
│   ├── plans/                  roadmap + sprint plans
│   ├── internal/               architecture / build / status / tests / workarounds
│   ├── CHANGELOG.md            changelog index (umbrella per `feedback_changelog_umbrella`)
│   └── logs/                   changelogs + sprint logs (per-version umbrella)
├── tools/
│   └── check_dangling.py       scan .md files for broken local links + hidden zero-width chars
├── Makefile                    one-line build (make)
├── .editorconfig               cross-editor indent/EOL/charset config
├── README.md                   English (this file)
└── README.zh-CN.md              简体中文
```

---

## Status (v1.8.3 — v1.x final)

`jhyy_v1 → jhyy_v2 → jhyy_v3 → jhyy_v4 → jhyy_v5` compile themselves and emit **byte-equal QBE intermediate representation**:

```
jhyy_v1.exe.exe → src0/main.jhyy → jhyy_v2.il
jhyy_v2.exe     → src0/main.jhyy → jhyy_v3.il   ← byte-equal to v2.il
jhyy_v3.exe     → src0/main.jhyy → jhyy_v4.il   ← byte-equal to v2.il
jhyy_v4.exe     → src0/main.jhyy → jhyy_v5.il   ← byte-equal to v2.il
                                                 sha 03a1cdd4… (v1.8.0 ship, frozen)
                                                 sha 51376ce5… (v2.4.0 re-baseline per D43)
```

All five raw `.il` files share an identical sha256 (1.378 MB, no fix-up post-processing). The fixed point is an attractor, not a transient. **Stage 2 N=4 byte-equal closure reached at v1.0.0 (tag `9b05c0f` / commit `eabee0d`, 2026-08-10), stable through v1.8.3 (tag `98c8272`, 2026-08-29), then re-baselined at v2.4.0 (tag `v2.4.0` / commit `7fb735b`, 2026-09-04) per D43 阶段性 self-equal hold (new sha `51376ce5…`). v1.x is now finalized; v2.0 阶段 (v2.0.0 → v2.4.0) 全 ship.**

| Metric | Value |
|--------|-------|
| `regress.py` (C-side `jhyy.exe`) | **104/104 PASS, 0 failed, 4 skipped** (108 total) |
| `regress.py --binary=jhyy_v1.exe.exe` (self-hosted `jhyy_v1.exe.exe`) | **104/104 PASS, 0 failed, 4 skipped** (parity hold) |
| Stage 1 byte-equal (`jhyy_0` vs `jhyy_v1`) | **7/7 PASS** |
| Stage 2 N=4 byte-equal (`v1→v2→v3→v4→v5`) | **stable** |
| `jhyy_v2` compiling `_repro_t0.jhyy` | `EXIT=100` ✓ |
| `jhyy_v2` compiling `fib(10)` | `EXIT=55` ✓ |
| `installer/jhyy-installer-1.8.3.exe` | shipped (~30MB, includes .NET 8 Desktop Runtime) |
| `installer/jhyy-compiler-1.8.3.msi` | shipped (~995KB, includes `jhyy-setuc.exe`) |
| `vscode-ext/jhyy-lang-1.8.3.vsix` | shipped (~13KB) |

**v1.x umbrella changelog** — [`docs/logs/v1/changelog-v1.8.0.md`](docs/logs/v1/changelog-v1.8.0.md) covers v1.8.0 main + v1.8.1 / v1.8.2 / v1.8.2 patch update / v1.8.3 / v1.8.3.1 / v1.8.3.2 patches (all `fix(v1.8.0)` commits, no new features). Historical v1.0.0 → v1.7.3 changelogs each live under `docs/logs/v1/changelog-vX.Y.Z.md`.

**W-NNN workaround status (v1.8.3 ship)**:
- ✅ W-059 defer codegen silent crash — RESOLVED 2026-08-28
- ❌ W-060 enum variant payload ABI — INVALID 2026-08-28 (bash `$?` 8-bit truncation artifact, regress.py W-028 mod-256 fix handles)
- ❌ W-061 nested struct field offset — INVALID 2026-08-28 (same reason)
- ✅ W-062 VSCode UserChoice + MSYS2 OpenWithProgids shadow — RESOLVED 2026-08-29 (v1.8.3.1 closed loop, SYSTEM-context CustomAction + 3-attempt fallback)
- ✅ W-063 UCPD.sys kernel filter — RESOLVED 2026-08-29 (v1.8.3 real fix, `jhyy-setuc.exe` .NET 8 SYSTEM-context writer)
- ✅ W-064 run_qbe stderr capture — RESOLVED 2026-09-01 (v1.8.3.2 patch, 镜像 W-045 link_with_gcc pattern, QBE 真实诊断不再丢失)
- ✅ W-065 cmd_run main_jhyy pre-check — RESOLVED 2026-09-01 (v1.8.3.2 patch, byte-scan `fn main_jhyy` 避免 link 时报 "undefined reference")
- 🟡 W-057 UTF-8 3/4-byte codepoint — DEFERRED-to-v2.x
- 🟡 W-058 vendored QBE missing `remd`/`rems` — DEFERRED-to-v2.x
- ⚠️ W-021 WiX Bal.wixext DLL naming — permanent workaround (WiX upstream won't fix)

Full index: [`docs/internal/workarounds.md`](docs/internal/workarounds.md).

**v3.0.6/Ph.1 — UTF-8 3/4-byte codepoint fold (W-057 真修) — 2026-09-23 ✅ shipped**

Per [`docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md`](docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md): axis-v3 absorbs V2.13.7 W-057 真修 (`594d00d`). 2 src0 files 改 (`lexer.jhyy` lead byte 4 类扩 + `parser.jhyy` `decode_char_literal` 3/4-byte UTF-8 decode), 跟 V2.13.7 同源。W-057 flip 🟡 DEFERRED → ✅ RESOLVED post-Ph.1 ship。2 NEW tests (`char_literal_3byte.jhyy` U+4F60 / `char_literal_4byte.jhyy` U+1F389) — verification V.0/V.1 5/5 PASS (compiled + EXIT=0); V.2 regress 139/139 PASS / 0 FAIL / 20 SKIP preserved; jhyy.exe sha `496bea91c54c2f24...` post-Phase.1 rebuild。Ph.2 (W-058 fmod) / Ph.3 (W-083 emit_sse) / Ph.4 (in-mem pipeline) / Ph.5a+5b (QBE removal + C-side parity) / Ph.6 (bench.sh) / Ph.7 (tag v3.0.6 ship) 后续 phases。

**v3.0.6/Ph.2 — codegen.jhyy W-058 fmod user-space formula trunc — 2026-09-23 ✅ shipped**

Per [`docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md`](docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md): axis-v3 absorbs V2.13.8 W-058 fmod 真修 (`16b4903`). 1 src0 file 改 (`codegen.jhyy` line 2214+ 插 45 行: TOKEN_PERCENT + QBE_D/QBE_S early return → 5 IL insns `a - trunc(a/b)*b` = div + dtosi/stosi + swtof + mul + sub, polymorphic by tok.qbe_type), 跟 V2.13.8 同源。W-058 flip 🟡 DEFERRED → ✅ RESOLVED post-Ph.2 ship (跟 V2.13.8 commit message / spec 附录 B P3 v3.0.6 revision 一致)。3 NEW tests ship (`fmod_basic.jhyy` 7.0%2.0=1.0 exit=1 / `fmod_negative.jhyy` -7.5%2.0=-1.5 trunc 区分 floor exit=99 / `fmod_f32.jhyy` 7.0_f32%2.0_f32=1.0_f32 polymorphic f32 fold exit=1)。is_f32 nested plain `if` 无 `&&`/`||` short-circuit (避免 W-081 latent phi merge gap, per `feedback_jhyy_brace_nesting`)。Verification V.1 5/5 PASS on 3 new fmod tests; V.2 regress 126/126 + 3 new = FRESH 129 with 21 sysv skip preserved (no regression)。byte-equal D26 5/5 PASS preserved; byte-equal-amd64 V3-B 10/10 PASS preserved。Self-backend W-083 closure 在 v3.0.6/Ph.3 单独 ship (跟 Ph.2 互补)。

**v3.0.6/Ph.3 — src0 codegen_amd64 self-backend conversion family (W-083 真修 Layer 1) — 2026-09-23 ✅ shipped / W-086 🟡 defer to v3.0.7**

Per [`docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md`](docs/plans/v3/v3.0.6-port-v2.16.0-src0-closure.md): axis-v3 absorbs V2.13.11 W-083 self-backend fmod 真修 (`425ab53`), 按用户 2026-09-23 "conversion 是一族, 一次补齐, 不 case-by-case" 反馈扩到 18 conv ops 一族真修 (dtosi/dtosl/dtoui/dtoul/stosi/stosl/stoui/stoul/swtof/sltof/uwtof/ultof/exts/extu/extsw/extuw/extsh/extuh/extsb/extub/truncd/truncs)。**Audit fix #2 (2026-09-23) REVERTED**: V3 当前**没有** `codegen_amd64_emit_sse.jhyy` 文件 (V3 modular split 7 files only — state/lexer/emit_mem/emit_ctrl/emit_call/regalloc/peephole 共 4594 LOC), per user "V3 modular split 不新建 SSE file" 决策 conversion 逻辑 fold 进现有 modules。4 src0 files 改: `codegen_amd64_state.jhyy` (+11 LOC, `ILTOK_CONV = 16`) + `codegen_amd64_lexer.jhyy` (+242 LOC, `next_token_conv` helper + 'd'/'s'/'u'/'e'/'t' prefix handlers 识别 18 conv ops, nested plain `if` 无 `&&`/`||` per `feedback_jhyy_brace_nesting`) + `codegen_amd64_emit_call.jhyy` (+450 LOC, `size_suffix_for_qt` 扩 "ss"/"sd" for QBE_S/QBE_D + 4 XMM/GPR scratch helpers + `emit_conv` dispatcher 18 branches 走 SSE cvttsd2si/cvttss2si/cvtsi2ss/cvtsi2sd/cltq) + `codegen_amd64.jhyy` (+5 LOC, parse_and_emit ILTOK_CONV dispatch case per W-068 fix #4 `let _ = ...` pattern)。**RCA finding (2026-09-23 Ph.3 ship 时 audit-flip closure)**: V3 self-backend `codegen_amd64_run` 对 fmod 类测试 produce 0-byte .s, root cause **多层** — **Layer 1 (W-083 真修 ✅)**: lexer 不识别 conv ops → 0-byte .s;**Layer 2 (W-086 NEW defer)**: emit_copy / emit_binop / emit_conv **字段约定冲突** (emit_copy 读 int_val=src value, emit_binop 读 int_val=dst_id, '%' LHS handler 不写 int_val/text_len → 所有 copy 写 0, 所有 binop 写 -32(%rbp));**Layer 3 (deeper)**: lexer 不 consume operand (next_token_binop/copy 等不 consume src, lex_il 跳过未知 byte)。Verification gate (revised per RCA): default QBE backend 3/3 fmod PASS ✅ (fmod_basic exit=1, fmod_negative exit=99, fmod_f32 exit=1); regress 142/142 PASS / 0 FAIL / 20 SKIP preserved ✅; `byte_equal_amd64.sh --no-strict` 5/5 PASS preserved ✅; **JHY_SELF_BACKEND=1 fmod 3/3 PASS ❌ BLOCKED by W-086** (defer 真修 to v3.0.7, mandatory 前置 Ph.5a `qbe/` git rm); jhyy.exe sha `95a68fd32083bf5f...` post-Phase.3 rebuild。**byte_equal_amd64.sh 5/5 PASS 是 false positive** (2026-09-23 发现) — 5 tests 全走 QBE fallback (default `compile --target=amd64_win` 不设 `JHY_SELF_BACKEND` → run_backend 落 run_qbe path), V3 self-backend 从未被任何 CI gate 真 exercise。**This finding 必须 escalate to user pre-Ph.5a**: Ph.5a 后 self-backend 成为 sole production path, W-086 必须真修或 Ph.5a revert。

**v0.x frozen**: `docs/logs/v0/changelog-v0.9.0.md` (3231 lines) — Stage 1 byte-equal 7-test-set wip, frozen at v1.0.0 baseline (2026-08-29). v0.x C compiler (`compiler/src/*.c`) enters maintenance-only mode; new features go through `compiler/src0/*.jhyy`. Per `docs/plans/roadmap/v1.x-phase-4-m5-boot-from-scratch.md`, M5 boot-from-scratch cleanup (delete `src/*.c` + `qbe/` + `runtime.c`) is deferred until v2.x end + v3.x end.

> [!NOTE]
> **v1.8.3 is v1.x final.** The C-side compiler (`compiler/src/*.c`) remains the production path during v1.x; `compiler/src0/*.jhyy` (the jhyy-side translated source) already produces byte-equal output. v2.0.0 阶段 (v2.0.0 → v2.4.0) shipped 2026-09-04 — multi-target dispatcher + freestanding ABI + hello-freestanding.efi E2E 5/5 PASS on OVMF (see [`docs/logs/v2/changelog-v2.{0..4}.0.md`](docs/logs/v2/changelog-v2.4.0.md) + [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md)).

---

## Verification status

| Check | Command | Expected |
|-------|---------|----------|
| C-side regression | `python compiler/build/bin/regress.py` | **104/104 PASS + 4 SKIP** (108 total) |
| Self-host regression | `python compiler/build/bin/regress.py --all --include-informational` | **104/104 PASS + 4 SKIP** (parity hold) |
| Stage 1 byte-equal (`jhyy_0` vs `jhyy_v1`) | `python compiler/tests/stage1-expanded.sh` | 7/7 PASS |
| Stage 2 N=4 byte-equal (`v1→v2→v3→v4→v5`) | MCP `jhyy_selfhost_check` | `all_byte_equal=true`, stable il_sha256 |
| MCP smoke (7 test files, 39 `def test_*` funcs) | `pytest mcp-jhyy/tests/` | all pass |
| One-line build | `make` | 0 warnings (-Wall -Wextra) |

---

## Roadmap

The project uses a **single version axis**, no phase-N numbering:

| Axis | Scope | Goal | Status |
|------|-------|------|--------|
| **v0.x** | C-side compiler itself | reach self-host threshold | **🟢 done (frozen at v1.0.0 baseline)** |
| **v1.x** | jhyy self-hosting | byte-equal `.il` closure | **🟢 v1.8.3 shipped (v1.x final)** |
| **v2.x** | full QBE rewrite + multi-target / OS prep | amd64_sysv / freestanding | **✅ v2.0 阶段 ship (2026-09-04, tags `v2.3.0` / `v2.4.0`)**; v2.x 中/末 ⏳ 未启动 (QBE 自写 / amd64_sysv 实 impl / N 代 fixed point) — design input = [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md) |
| **v3.x** | language extensions | OS-required: asm / volatile / naked / `no_std` / `&mut` + lifetime | **next** (v2.0 阶段 ✅ ship, 3a-3f 等 user 启动) — v2.x 中/末 + v3.x async parallel |

**Axis relationships**:
- `v0.x → v1.x → v2.x`: **strict order** (each is a hard prerequisite of the next)
- `v1.x → v3.x`: **strict order** (v3.0 sprint 3a-3f starts after v2.0 phase ships ✅; per 2026-09-01 user decision)
- `v2.x mid/late ⟂ v3.x`: **async parallel** (no fixed pairing; each ships independently; both done before OS M1 starts)

> [!IMPORTANT]
> **Alignment with the [JiHuiYiYou-OS](https://github.com/JiHuiYiYou/JiHuiYiYou-OS) project**: 12 cross-boundary questions + 6 decisions are closed and reflected in the OS prep plan at [docs/plans/v2/v2.0.0-os-prep.md](docs/plans/v2/v2.0.0-os-prep.md). The v2.0 sprint design input is the same plan.

---

## Tooling & Integration

### Claude Code MCP server

`mcp-jhyy/` ships **11 MCP tools** wired into the Claude Code workflow (Sprint 1 of mcp-jhyy, 2026-08-11, added 4 production-ready tools — `jhyy_regress` / `jhyy_il_diff` / `jhyy_selfhost_check` / `jhyy_workarounds` — and rebased the original 7 (`jhyy_run` / `jhyy_check` / `jhyy_compile` / `jhyy_get_il` / `jhyy_lang_ref` / `jhyy_abi_info` / `jhyy_format`) onto a thin regress.py shim):

| Tool | Purpose |
|------|---------|
| `jhyy_regress` | run C-side / jhyy-side regression, return PASS/FAIL list |
| `jhyy_il_diff` | byte-equal check on two `.il` files + contextual diff |
| `jhyy_selfhost_check` | one-shot v1→v2→v3→v4→v5 byte-equal verification |
| `jhyy_workarounds` | query W-NNN workaround status / details |
| `jhyy_run` / `jhyy_check` / `jhyy_compile` / `jhyy_get_il` | compile / run / inspect `.jhyy` |
| `jhyy_lang_ref` / `jhyy_abi_info` / `jhyy_format` | language / ABI / format queries |

Details in [`mcp-jhyy/README.md`](mcp-jhyy/README.md).

### VS Code extension

`vscode-ext/` ships syntax highlighting (TextMate grammar + file icon) + native `Run JHYY File` (`Ctrl+F5`) + `Compile JHYY File (no run)` commands. Latest shipped = `jhyy-lang-1.8.3.vsix`. Install + build instructions in [`vscode-ext/README.md`](vscode-ext/README.md).

---

## Docs

### Specification & ABI (locked)

| Doc | Description |
|-----|-------------|
| [`docs/abis/jhyy-lang-spec-v1.3.0.md`](docs/abis/jhyy-lang-spec-v1.3.0.md) | language spec v1.3.0 (v1.1.0 + 7 v1.3.x features; limitations in Appendix B + E) |
| [`docs/abis/jhyy-abi-v1.0.0.md`](docs/abis/jhyy-abi-v1.0.0.md) | ABI whitepaper v1.0.0 (struct pass-by-value / FFI / namespaces / slices) |

### Internal

| Doc | Description |
|-----|-------------|
| [`docs/internal/architecture.md`](docs/internal/architecture.md) | pipeline / modules / QBE IL cheat sheet |
| [`docs/internal/build.md`](docs/internal/build.md) | build / run / QBE backend pitfalls (Windows) |
| [`docs/internal/workarounds.md`](docs/internal/workarounds.md) | W-NNN workaround status index |
| [`docs/internal/tests.md`](docs/internal/tests.md) | integration test catalog + how to run |

### Roadmap & plans

| Doc | Description |
|-----|-------------|
| [`docs/plans/roadmap/v0.x-c-compiler-roadmap.md`](docs/plans/roadmap/v0.x-c-compiler-roadmap.md) | C compiler evolution |
| [`docs/plans/roadmap/v1.0-self-hosting.md`](docs/plans/roadmap/v1.0-self-hosting.md) | self-hosting overview |
| [`docs/plans/roadmap/v2.x-qbe-rewrite.md`](docs/plans/roadmap/v2.x-qbe-rewrite.md) | QBE rewrite direction |
| [`docs/plans/roadmap/v3.x-language-expansion.md`](docs/plans/roadmap/v3.x-language-expansion.md) | language extension direction |
| [`docs/plans/v2/v2.0.0-os-prep.md`](docs/plans/v2/v2.0.0-os-prep.md) | compiler-side authority on OS startup chain |

### Changelog

Latest: [`docs/logs/v1/changelog-v1.8.0.md`](docs/logs/v1/changelog-v1.8.0.md) — **v1.x umbrella (covers v1.8.0 main + v1.8.1 / v1.8.2 / v1.8.2 patch update / v1.8.3 / v1.8.3.1 / v1.8.3.2 patches)**

Historical index: [`docs/logs/`](docs/logs/) — v1.0.0 → v1.7.3 each have their own umbrella;v0.0.1 → v0.9.0 for C-side compiler (v0.9 frozen at v1.0.0 baseline).

---

## Contributors

- **Human author**: JHYY
- **AI collaborator**: MiniMax-M3 (working through the [Claude Code](https://claude.ai/code) CLI workflow on design, coding, debugging, documentation)

Since v0.6 every sprint's implementation + documentation has been co-authored by JHYY + MiniMax-M3.
