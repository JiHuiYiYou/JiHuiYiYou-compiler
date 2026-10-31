<div align="center">

<div><img src="vscode-ext/icon-animated.svg" width="96" alt="JHYY logo"></div>

<div><img src="vscode-ext/jhyy-calligraphy.png" width="220" alt="JHYY calligraphy logo"></div>

### JHYY (机会翼游) — A self-hosted, statically typed, compiled systems programming language

**Statically typed. Expression-oriented. Compiled to native by a self-written amd64 backend.**

[![Version](https://img.shields.io/badge/version-v4.1.2-00d4aa)](CHANGELOG.md)
[![Status](https://img.shields.io/badge/self--host-byte--equal-success)](#status-v412)
[![Backend](https://img.shields.io/badge/backend-self--hosted%20amd64-blue)](#architecture)
[![Platform](https://img.shields.io/badge/platform-Windows%20x64-lightgrey)](#install)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![中文](https://img.shields.io/badge/lang-中文-red)](README.zh-CN.md)

[Quick Start](#quick-start) · [Install](#install) · [Language](#language) · [CLI](#cli) · [Architecture](#architecture) · [Status](#status-v412) · [Roadmap](#roadmap) · [Docs](#docs)

</div>

---

## What is JHYY

JHYY (机会翼游) is a self-designed, statically typed, expression-oriented, compiled systems
programming language. **The compiler is written in itself** — `compiler/src0/*.jhyy` is the
*only* implementation. `jhyy.exe` compiles `compiler/src0/main.jhyy`; the compiler that
produces compiles it again, and the closure gate **iterates until the emitted `.s` is
byte-identical** (the fixed point is reached, not assumed).

The backend is a **self-written in-memory amd64 code emitter**
(`compiler/src0/codegen_amd64_*.jhyy`) — no vendored QBE, no LLVM, no GC, no runtime.

**Design goals**:

- **Self-hosting** — the compiler compiles itself; the closure is verified by iteration to a
  fixed point (`.s` byte-identical across generations).
- **Native output** — direct amd64 code emission; PE/COFF (Windows) and ELF (Linux) binaries.
- **OS-ready** — `extern fn` FFI on the C ABI, `enum` + `match`, `#[no_std]`, `#[naked]`,
  inline `asm!`, `#[link_section]`, `volatile`, memory barriers, `defer`.

---

## A tour of the syntax

```rust
// Functions / variables / control flow / struct / match / enum / FFI
type Point = struct { x: i32, y: i32 }

fn dist_sq(a: Point, b: Point) -> i32 {
    let dx = a.x - b.x;
    let dy = a.y - b.y;
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

## Install

**End users (Windows x64)** — grab the installer from
[**GitHub Releases**](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/latest).
**MSYS2 is not required**: since v4.1.0 the installer bundles a minimal native ucrt64
toolchain (`<INSTALLDIR>\toolchain\`).

| Artifact | Size | What it is |
|---|---|---|
| [`jhyy-installer-4.1.2.exe`](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/download/v4.1.2/jhyy-installer-4.1.2.exe) | ~55 MB | GUI installer — compiler + `.jhyy` file association + VS Code extension + PATH |
| [`jhyy-compiler-4.1.2.msi`](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases/download/v4.1.2/jhyy-compiler-4.1.2.msi) | ~28 MB | Same payload, no GUI — for enterprise / SCCM distribution |

Checksums are published alongside the assets as `SHA256.txt`.

**Building from source** — needs MSYS2 + `mingw-w64-ucrt-x86_64-gcc` (the compiler
*build* host requirement; end users don't need it):

```bash
git clone https://github.com/JiHuiYiYou/JiHuiYiYou-compiler.git
cd JiHuiYiYou-compiler
make all        # → compiler/build/bin/jhyy.exe (~1.9 MB)
```

> [!IMPORTANT]
> Do NOT use the MinGW `gcc` shipped with Git Bash (`/c/Program\ Files/Git/mingw64/bin/gcc.exe`)
> — it does not support PE+ linking and fails at link time.

**Docker**:

```bash
# compiler host — full toolchain (Windows)
docker run -it msys2/mingw-w64-ucrt-x86_64 bash
# amd64_sysv target toolchain — link + run the emitted .s on Linux
# (jhyy.exe is a PE binary: it does NOT run inside this container)
docker run -it gcc:12 bash
```

**VSCode users**: opening this repo triggers `.vscode/settings.json` to add
`compiler/build/bin` and the MSYS2 ucrt64 path to the integrated terminal. Press
`Ctrl+Shift+B` to compile + run any `.jhyy` file.

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
./compiler/build/bin/jhyy.exe run hello.jhyy
echo $?    # => 42
```

### Run the regression suite

```bash
python regress.py
# => 261/261 passed (all with assertions), 0 failed, 20 skipped (of 281 total)
```

### Verify the self-host closure

```bash
make            # builds jhyy.exe, then iterates the closure to a fixed point
#   ⇒ _boot_new.s vs _boot_new2.s byte-identical
```

### Run with VSCode

With the extension installed, `.jhyy` files get a ▶ run button in the title bar
(`Ctrl+F5`).

---

## Language

| Category | Supported |
|----------|-----------|
| **Types** | `i8/i16/i32/i64`, `u8/u16/u32/u64`, `f32/f64`, `bool`, `*T`, `[T; N]`, `[*]T` (slice), `struct`, `enum`, `Cap<T>`, `PhantomData<T>` |
| **Sizes** | `sizeof(T)` / `alignof(T)` — compile-time constants |
| **Casts** | `as` — integer/float conversion, widening/narrowing, `*T ↔ i64/u64` |
| **Control flow** | `if`/`else` (expression-valued), `while`, `for i in start..end`, `break`, `continue`, `match` (literal/range/enum/wildcard, with exhaustiveness check) |
| **Cleanup** | `defer` — runs at scope exit (LIFO); not run on an implicit tail return |
| **Top-level const** | `const NAME: [T; N] = [...]` — compile-time emit to the `.data` section |
| **Logic** | `&&` / `\|\|` short-circuit, `!` / `~` unary |
| **Functions** | first-class, recursion, compound assignment (`+=` `-=` `*=` `/=` `%=`), block-expression closures (no capture — capturing is a compile error) |
| **Modules** | `import` + transitive imports, multi-file CLI, `mod::fn()` namespaces |
| **FFI** | `extern fn` calling C (printf, file I/O, multi-arg) |
| **OS / embedded** | `#[no_std]`, `#[naked]`, `#[link_section]`, `volatile`, inline `asm!`, memory barriers |
| **Stdlib** | `import mem;` / `fmt` / `io` / `math` / `string` / `vec` / `os` / `arena` — **note: no `std::` prefix** (`import std::vec;` is a compile error) |

Full specification: [`docs/abis/jhyy-lang-spec-v4.0.0.md`](docs/abis/jhyy-lang-spec-v4.0.0.md)
(locked 2026-10-24; it replaces v1.3.0 + 17 v3.x supplements, both archived to git history).
Known limitations are collected in its **Appendix B**, not scattered through the prose.

---

## CLI

```text
jhyy compile <file.jhyy> [-o output]   compile + link -> .exe
jhyy build   <file.jhyy> [-o output]   compile only -> .s (no link)
jhyy run     <file.jhyy>              compile + link + execute
jhyy dump    <file.jhyy>              ⚠️ not implemented yet (exits 1)

flags:
  --target=<triple>  select target (default amd64_win)
  --no-link          compile to .s only, skip the gcc link (for cross toolchains)
  --help             show help and exit
```

Targets: `amd64_win` (default, hosted Windows) · `amd64_win_freestanding` (UEFI) ·
`amd64_sysv` · `amd64_sysv_freestanding`.

> [!IMPORTANT]
> **The command line takes exactly one input file.** Extra `.jhyy` arguments are
> **silently ignored** — no error, no warning — so `jhyy compile main.jhyy lib.jhyy`
> compiles **only** `main.jhyy`.
> Combine files with `import` instead: put `import lib;` in `main.jhyy` and the
> compiler pulls `lib.jhyy` in along the import graph.
>
> ⚠️ **There is no `jhyy --version`** — it never existed. Running it prints
> `unknown command` and exits 1. The version banner is the **first line of
> `jhyy --help`** (and of `jhyy` with no arguments).
>
> ⚠️ `jhyy build` and `jhyy compile --no-link` are *not* equivalent: `build` does not run
> `apply_link_section_directives`, so programs using `#[link_section]` produce different
> `.s` on the two paths (see `W-170`). Prefer `compile --no-link` for tooling.

---

## Architecture

```mermaid
flowchart TB
    src[".jhyy source"] --> lex["Lexer → Token stream"]
    lex --> parse["Parser → AST"]
    parse --> sema["Sema → annotated AST"]
    sema --> il["codegen.jhyy<br/>emits QBE-style IL text to **memory**"]
    il --> sb["codegen_amd64_inmem<br/>lex → parse → emit → peephole"]
    sb --> asm[".s (amd64)"]
    asm --> ln["as + ld (gcc)"]
    ln --> exe[".exe (PE/COFF) / ELF"]
```

| Piece | Where | Role |
|-------|-------|------|
| `compiler/src0/*.jhyy` | 30 modules | **The** compiler — lexer, parser, sema, IR, codegen, target dispatch |
| `compiler/src0/codegen_amd64_*.jhyy` | self-written backend | IL lexer · emitter (`emit_call` / `emit_ctrl` / `emit_mem` / `emit_sse`) · peephole · register cache |
| `compiler/src0/std/*.jhyy` | 8 modules | `mem` `fmt` `io` `math` `string` `vec` `os` `arena` |
| `compiler/runtime/runtime.c` | C runtime | Arena allocator + `main` → `main_jhyy` bridge |
| `runtime/linux_elf/` | crt0.S + link.ld | Linux ELF runtime for the `amd64_sysv*` targets |

**Why no QBE?** QBE was removed in v4.0.0 (post-v2.16.0). The self-written backend is now
the sole codegen path — that removes a 17K-LOC vendored dependency and tightens the
iteration loop on codegen itself.

---

## Project layout

```
JiHuiYiYou-compiler/
├── compiler/
│   ├── src0/                   compiler sources (the only implementation, 30 modules + std/)
│   │   ├── std/                standard library: mem / fmt / io / math / string / vec / os / arena
│   │   └── codegen_amd64_*.jhyy self-written backend: IL lexer / emit_* / peephole / register cache
│   ├── runtime/                C runtime (arena + main entry)
│   ├── tests/
│   │   ├── examples/           integration tests (274 .jhyy files + 5 subdirectories) — run by regress.py
│   │   └── bootstrap/          fixed_point.sh · closure_check.sh · artifact_checks.sh · byte_equal*.sh
│   └── build/bin/              jhyy.exe · jhyy_v1.exe.exe (self-hosted artifacts)
├── runtime/linux_elf/          Linux ELF runtime (crt0.S + link.ld)
├── regress.py                  regression test suite (repository root)
├── docs/                       specs / internal docs / plans / changelog
├── installer/                  WiX installer + bundled ucrt64 toolchain
├── mcp-jhyy/                   Claude Code MCP server (jhyy_* tools)
├── vscode-ext/                 VS Code extension
├── scripts/dev/                development scripts (bench / test / build / install)
└── tools/                      cross-repository tools
```

---

## Status (v4.1.2)

| Metric | Value |
|--------|-------|
| `regress.py` | **261 PASS + 0 XFAIL + 0 failed + 20 SKIP** (281 total) |
| Assertion audit | 281 scanned / 261 runnable / 201 real assertions / 0 zero-signal |
| Self-host closure | `make` iterates to a fixed point — emitted `.s` byte-identical |
| `fixed_point.sh` | PASS (N=10 — `.il` and `.s` byte-equal across generations) |
| `artifact_checks.sh` | **17 PASS / 0 FAIL** |
| `closure_check.sh` | PASS (v2.s == v3.s, byte-identical) |
| ACTIVE workarounds | **1** — [`W-170`](docs/internal/workarounds.md): `jhyy build` doesn't apply `#[link_section]` |
| `jhyy-installer-4.1.2.exe` | shipped (~55 MB, includes .NET 8 Desktop Runtime + bundled ucrt64 toolchain) |
| `jhyy-compiler-4.1.2.msi` | shipped (~28 MB, includes `jhyy-setuc.exe` + bundled toolchain) |
| `jhyy-lang-4.1.2.vsix` | shipped (VS Code extension) |

**Changelog** — [`CHANGELOG.md`](CHANGELOG.md) has one line per release; the detailed
per-axis record is the v4 umbrella,
[`docs/archive/logs/v4/changelog-v4.0.0.md`](docs/archive/logs/v4/changelog-v4.0.0.md).

---

## Roadmap

v4.x is the post-merge axis. **The authoritative schedule** — one slot per version, what each
slot contains, and the stable `OS-N` identities — is
[`docs/internal/FACTS.md`](docs/internal/FACTS.md) § 4. Plans live one per version slot under
[`docs/plans/v4/`](docs/plans/v4/README.md).

**Current line**: the self-written backend's performance line (register allocation for the
self-written amd64 backend), followed by the OS line (v4.6 → v4.15, stable identity
`OS-1` … `OS-16`).

Version numbers on reserved slots are **placeholders** — each plan carries a
"check on start" checklist to be re-verified against reality when that slot is picked up.

---

## Tools & integrations

### Claude Code MCP server

`mcp-jhyy/` provides **11 MCP tools**:

| Tool | Purpose |
|------|---------|
| `jhyy_run` / `jhyy_check` / `jhyy_compile` | compile / run / check `.jhyy` |
| `jhyy_get_il` | fetch the intermediate representation (codegen debugging) |
| `jhyy_regress` | run the regression suite, returns the PASS/FAIL list |
| `jhyy_il_diff` | byte-equal check + contextual diff of two `.il` files |
| `jhyy_selfhost_check` | one-shot self-host closure verification (v1→v2→v3→v4) |
| `jhyy_workarounds` | look up the status of a W-NNN workaround |
| `jhyy_lang_ref` / `jhyy_abi_info` / `jhyy_format` | language / ABI / formatting queries |

Install with `pip install fastmcp` (⚠️ **not** `mcp[cli]` — `fastmcp` is a separate
top-level distribution). See [`mcp-jhyy/README.md`](mcp-jhyy/README.md).

### VS Code extension

`vscode-ext/` provides syntax highlighting (TextMate grammar + file icons), a native ▶
`Run JHYY File` command (`Ctrl+F5`) and a `Compile JHYY File (no run)` command. The
latest shipped build is `jhyy-lang-4.1.2.vsix`.

---

## Docs

- **All repo docs** — the map of what lives where: [`docs/internal/README.md`](docs/internal/README.md)
- **Language spec**: [`docs/abis/jhyy-lang-spec-v4.0.0.md`](docs/abis/jhyy-lang-spec-v4.0.0.md) (locked)
- **ABI whitepaper**: [`docs/abis/jhyy-abi-v4.0.0.md`](docs/abis/jhyy-abi-v4.0.0.md) (locked)
- **Binary format** (design doc, not implemented): [`docs/abis/jhyy-binary-format-v1.0.0.md`](docs/abis/jhyy-binary-format-v1.0.0.md)
- **Current facts** (version, regression count, schedule): [`docs/internal/FACTS.md`](docs/internal/FACTS.md)
- **Architecture**: [`docs/internal/architecture.md`](docs/internal/architecture.md)
- **Build & run**: [`docs/internal/build.md`](docs/internal/build.md)
- **Workarounds ledger**: [`docs/internal/workarounds.md`](docs/internal/workarounds.md)
- **Current plans**: [`docs/plans/v4/`](docs/plans/v4/README.md)
- **Cross-project design** (compiler side / OS side): [`docs/coordination/`](docs/coordination/)
- **Performance baseline**: [`docs/perf/self-backend-baseline-2026-10-29.md`](docs/perf/self-backend-baseline-2026-10-29.md)
- **Contributing**: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md)
- **Archive**: [`docs/archive/`](docs/archive/README.md) (history — superseded plans, old changelogs)

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Contributors

- **Human author:** JHYY
- **AI collaborator:** MiniMax-M3 — contributes to design, implementation, debugging and
  documentation through the [Claude Code](https://claude.ai/code) CLI workflow

Since v0.6, every sprint's implementation and documentation have been produced by JHYY
and MiniMax-M3 together.

---

<sub>v4.1.2 — 2026-10-29 · version automation (`VERSION` is the single source of truth) · self-written amd64 backend</sub>
