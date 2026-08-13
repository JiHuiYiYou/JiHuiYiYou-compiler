<div align="center">

<img src="vscode-ext/icon.svg" width="96" alt="JHYY logo">

# JHYY

### 机会翼游 — A self-hosted, statically typed, compiled systems programming language

**Statically typed. Expression-oriented. Compiled to native via QBE.**

[![Version](https://img.shields.io/badge/version-v1.0.0-00d4aa)](docs/logs/v1/changelog-v1.0.0.md)
[![Status](https://img.shields.io/badge/self--host-byte--equal%20v1%E2%86%92v4-success)](docs/logs/v1/changelog-v1.0.0.md)
[![Backend](https://img.shields.io/badge/backend-QBE-orange)](https://c9x.me/compile/)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey)](#build)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![中文](https://img.shields.io/badge/lang-中文-red)](README.zh-CN.md)

[Quick Start](#quick-start) · [Language](#language) · [CLI](#cli) · [Architecture](#architecture) · [Roadmap](#roadmap) · [Docs](#docs)

</div>

---

## v1.0.0 — Self-hosting closure achieved

`jhyy_v1 → jhyy_v2 → jhyy_v3 → jhyy_v4` compile themselves and emit **byte-equal QBE intermediate representation**:

```
jhyy_v1.exe  → src0/main.jhyy →  jhyy_v2.il
jhyy_v2.exe  → src0/main.jhyy →  jhyy_v3.il     ← byte-equal to v2.il
jhyy_v3.exe  → src0/main.jhyy →  jhyy_v4.il     ← byte-equal to v2.il
                                                 sha 2445e97d…
```

All four raw `.il` files share an identical sha256 (1.378 MB, no fix-up post-processing). The fixed point is an attractor, not a transient. **M4 milestone reached — tagged at commit `eabee0d` on 2026-08-10.**

| Metric | Value |
|--------|-------|
| `regress.py` (C-side `jhyy.exe`) | **50/53 PASS, 0 failed** |
| `regress_v1.py` (self-hosted `jhyy_v1.exe.exe`) | **50/53 PASS, 0 failed** |
| Stage 1 byte-equal (`jhyy_0` vs `jhyy_v1`) | **7/7 PASS** |
| Stage 2 N=3 byte-equal (`v1→v2→v3→v4`) | **stable** |
| `jhyy_v2` compiling `_repro_t0.jhyy` | `EXIT=100` ✓ |
| `jhyy_v2` compiling `fib(10)` | `EXIT=55` ✓ |

> [!NOTE]
> **v1.0.0 is both a milestone and a starting point.** The C-side compiler (`compiler/src/*.c`) remains the production path; `compiler/src0/*.jhyy` (the jhyy-side translated source) already produces byte-equal output, and subsequent sprints plan to gradually migrate the production path onto the self-hosted compiler (`v1.x → v2.x` roadmap).

---

## What is JHYY

JHYY is a self-designed, statically typed, expression-oriented, compiled systems programming language. The backend is [QBE](https://c9x.me/compile/), producing native x86-64 Windows binaries.

**Design goals**:
- **Self-hosting** — the compiler written in itself, achieving byte-equal closure (✓ v1.0.0)
- **OS development** — aligned with the [JiHuiYiYou-OS](https://github.com/JiHuiYiYou/JiHuiYiYou-OS) project, providing OS-required extensions like inline asm / volatile / naked / `no_std` / `&mut` + lifetime (v3.x roadmap)
- **Native performance** — QBE backend, no runtime / no GC, directly produces PE/COFF binaries

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

### After clone — pick one

```text
just cloned? run ONE of these and you have a working jhyy.exe
```

| Platform | Command | What it does |
|----------|---------|--------------|
| **Windows (cmd / PowerShell)** | `bootstrap.cmd` | builds `jhyy.exe` from C source + runs the regression suite |
| **MSYS2 bash / Git Bash** | `./bootstrap.sh` | same |
| **MSYS2 bash** | `make` | same as `bootstrap.sh` step 1 (build only, no regression) |
| **Manual** | see [Manual build](#manual-build) below | explicit gcc invocation |

All four produce the same `compiler/build/bin/jhyy.exe` and verify against `python compiler/build/bin/regress.py` (baseline: **50/50 passed, 0 failed, 3 skipped**).

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
# => 50/50 passed, 0 failed, 3 skipped (of 53 total)
```

### Manual build

If you prefer to skip the bootstrap scripts:

```bash
git clone https://github.com/JiHuiYiYou/JiHuiYiYou-compiler
cd JiHuiYiYou-compiler

/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/src/*.c \
    -o compiler/build/bin/jhyy.exe \
    -I compiler/src
```

Or use the project-root `Makefile` from MSYS2 bash:

```bash
make
```

### Run with VSCode

The repo ships `.vscode/tasks.json` — open any `.jhyy` file and press **`Ctrl+Shift+B`** to compile + run it. Other tasks: `Ctrl+Shift+P` → **Tasks: Run Task** → `JHYY: Run` / `JHYY: Compile` / `JHYY: Build IR` / `JHYY: Bootstrap`. `.vscode/settings.json` adds `compiler/build/bin` and `C:/msys64/ucrt64/bin` to the integrated terminal PATH so you can also type `jhyy run hello.jhyy` directly. `F5` launches the compiled `.exe` under MSYS2's gdb (cppdbg).

> [!IMPORTANT]
> **MSYS2 PATH requirement** — `jhyy run` shells out to `gcc` for linking, which in turn spawns `cc1.exe` / `as.exe` / `ld.exe` from `C:\msys64\ucrt64\bin`. PowerShell / cmd users outside VSCode need MSYS2 on their system PATH (or they get a silent `gcc link failed`). `.vscode/settings.json` handles this automatically for the integrated terminal; for external shells, either run `bootstrap.cmd` once or add `C:\msys64\ucrt64\bin` to your user PATH manually.

### Verify self-hosting closure

```bash
# Stage 2 N=3 byte-equal — jhyy compiles jhyy
# Method 1: regress through self-hosted compiler
python compiler/build/bin/regress_v1.py
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
jhyy check   <file.jhyy>             syntax / semantic check only, no codegen
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
    s0 --> bin2["jhyy_v1.exe"]
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

Both paths emit **byte-equal QBE intermediate representation** — Stage 1 (`jhyy_0` vs `jhyy_v1`) 7/7 byte-equal, Stage 2 (`jhyy_v1 → v2 → v3 → v4`) N=3 closure reached.

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
│           ├── jhyy_v1.exe     self-hosted compiler (jhyy compiled src0/)
│           └── regress.py      regression script
├── qbe/                        vendored QBE backend (c9x.me/compile)
├── mcp-jhyy/                   Claude Code MCP server (11 tools)
├── vscode-ext/                 VS Code language extension (syntax highlighting)
├── docs/
│   ├── abis/                   language spec + ABI whitepaper (locked)
│   ├── plans/                  roadmap + sprint plans
│   ├── internal/               architecture / build / status / tests / workarounds
│   └── logs/                   changelogs + sprint logs
├── Makefile                    one-line build (make)
├── README.md                   English (this file)
└── README.zh-CN.md              简体中文
```

---

## Verification status

| Check | Command | Expected |
|-------|---------|----------|
| C-side regression | `python compiler/build/bin/regress.py` | 50/53 PASS |
| Self-host regression | `python compiler/build/bin/regress_v1.py` | 50/53 PASS |
| Stage 1 byte-equal (`jhyy_0` vs `jhyy_v1`) | `python compiler/tests/stage1-expanded.sh` | 7/7 PASS |
| Stage 2 N=3 byte-equal (`v1→v2→v3→v4`) | MCP `jhyy_selfhost_check` | `all_byte_equal=true`, stable il_sha256 |
| MCP smoke (14 in-process tests) | `pytest mcp-jhyy/tests/` | 14 pass |
| One-line build | `make` | 0 warnings (-Wall -Wextra) |

---

## Roadmap

The project uses a **single version axis**, no phase-N numbering:

| Axis | Scope | Goal | Status |
|------|-------|------|--------|
| **v0.x** | C-side compiler itself | reach self-host threshold | **done** |
| **v1.x** | jhyy self-hosting | byte-equal `.il` closure | **v1.0.0 tagged** |
| **v2.x** | full QBE rewrite + multi-target / OS prep | amd64_sysv / freestanding | not started |
| **v3.x** | language extensions | OS-required: asm / volatile / naked / `no_std` / `&mut` + lifetime | not started |

**Axis relationships**:
- `v0.x → v1.x → v2.x / v3.x`: **strict order** (each is a hard prerequisite of the next)
- `v2.x || v3.x`: **parallel axes** (each progresses independently; both must finish before OS M1 starts)

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
| `jhyy_selfhost_check` | one-shot v1→v2→v3→v4 byte-equal verification |
| `jhyy_workarounds` | query W-NNN workaround status / details |
| `jhyy_run` / `jhyy_check` / `jhyy_compile` / `jhyy_get_il` | compile / run / inspect `.jhyy` |
| `jhyy_lang_ref` / `jhyy_abi_info` / `jhyy_format` | language / ABI / format queries |

Details in [`mcp-jhyy/README.md`](mcp-jhyy/README.md).

### VS Code extension

`vscode-ext/` ships syntax highlighting (TextMate grammar + file icon). Install instructions in [`vscode-ext/`](vscode-ext/) (the bilingual README retains legacy VS Code setup details for the Chinese version).

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

Latest: [`docs/logs/v1/changelog-v1.0.0.md`](docs/logs/v1/changelog-v1.0.0.md) — **v1.0.0 self-hosting closure reached**

Historical index: [`docs/logs/`](docs/logs/).

---

## Contributors

- **Human author**: JHYY
- **AI collaborator**: MiniMax-M3 (working through the [Claude Code](https://claude.ai/code) CLI workflow on design, coding, debugging, documentation)

Since v0.6 every sprint's implementation + documentation has been co-authored by JHYY + MiniMax-M3.
