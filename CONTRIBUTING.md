# Contributing to JHYY

Thanks for your interest in improving JHYY (机会翼游) — a self-hosted, statically typed,
expression-oriented systems programming language whose compiler is written in itself.

This guide covers how to report a bug, propose a change, and get a pull request merged.
It is deliberately short: everything here is something a newcomer needs before their
first patch lands.

- [Code of conduct](#code-of-conduct)
- [I have a question](#i-have-a-question)
- [Reporting a bug](#reporting-a-bug)
- [Suggesting a change](#suggesting-a-change)
- [Development setup](#development-setup)
- [Pull request process](#pull-request-process)
- [Conventions](#conventions)
- [License](#license)

---

## Code of conduct

Be respectful. Assume good faith. Technical disagreement is not personal conflict.

## I have a question

| Question | Where the answer lives |
|---|---|
| How do I write `.jhyy`? | [Language spec](docs/abis/jhyy-lang-spec-v4.0.0.md) — locked, with known limitations collected in its Appendix B |
| How does FFI / struct passing work? | [ABI whitepaper](docs/abis/jhyy-abi-v4.0.0.md) |
| What is the current state of the compiler? | [`docs/internal/FACTS.md`](docs/internal/FACTS.md) — the single source of truth for every number that changes |
| How do I build, run, and test it? | [Build & run](docs/internal/build.md) |
| How is the compiler put together? | [Architecture](docs/internal/architecture.md) |
| What changed in each release? | [`CHANGELOG.md`](CHANGELOG.md) |

## Reporting a bug

Open an issue and include:

1. **A minimal reproducer** — the full `.jhyy` source.
2. **Actual vs. expected output**, including the exit code.
3. **The version** — the first line of `jhyy --help`.
4. **Compiler provenance** — the committed `compiler/build/bin/jhyy.exe`, or a
   self-hosted build?

> [!TIP]
> Capture exit codes with a harness or Python `subprocess` rather than by reading
> `$?` in MSYS2 bash: bash truncates exit codes to 8 bits (`value & 0xFF`), so an
> expected code ≥ 256 has to be reduced before you compare it (827→59, 501→245,
> 300→44, 1000→232).

## Suggesting a change

The roadmap is public: [`docs/plans/v4/`](docs/plans/v4/) holds one plan per version
slot. Each plan carries a "re-check on start" checklist — read it before you pick up
a slot, because the numbers it quotes are from the day it was written. The
relationship between the performance line and the OS line is in
[`docs/internal/FACTS.md`](docs/internal/FACTS.md) § 4.

## Development setup

**Host:** Windows 10 + MSYS2 (`C:\msys64\mingw64\bin\bash.exe`).

```bash
# 1. Dependencies: MSYS2 + mingw-w64-ucrt-x86_64-gcc
pacman -S --needed mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-binutils

# 2. Build the compiler (jhyy compiles itself)
make all           # → compiler/build/bin/jhyy.exe

# 3. Run the regression suite
python regress.py  # at the repository root
```

> [!IMPORTANT]
> Do NOT use the MinGW `gcc` that ships with Git Bash
> (`/c/Program\ Files/Git/mingw64/bin/gcc.exe`) — it does not support PE+ linking
> and fails at link time.

Details — toolchain lookup order, the manual verification pipeline, version
automation, multi-target builds, the Linux ELF cross-link — are in
[`docs/internal/build.md`](docs/internal/build.md).

### Running the tests

```bash
python regress.py                       # full suite
python regress.py --tests=hello.jhyy    # a single case
python scripts/dev/audit_test_assertions.py --strict   # assertion-strength audit
```

**The pass count and the list of gates live in [`docs/internal/FACTS.md`](docs/internal/FACTS.md) § 2** —
don't restate those numbers anywhere else.

> [!NOTE]
> Run the gates **from the repository root** — they resolve paths relative to the current
> directory. `python scripts/dev/bump_version.py check` from a subdirectory reports every
> file as missing, which reads like a version drift but isn't one.

## Pull request process

1. One PR does one thing.
2. Run the gates. **A gate that wasn't run is a gate that didn't pass.**
3. Summarize the change in the commit message, and add a `Co-Authored-By` trailer
   for any AI assistant that contributed code to the change.
4. If you touched the documentation, keep the facts in sync — see
   [Conventions](#conventions).

Changing the compiler itself (`compiler/src0/*.jhyy`) costs considerably more than
changing documentation: adding a local variable shifts the module-level temp
numbering, which makes the self-hosted build drift, so it drags in a release-grade
process (refresh the anchor → re-pin the D43 baseline → full regression run).
Comment-only edits are free — the lexer strips comments before codegen, so the
compiler binary stays byte-identical.

## Conventions

- **Numbers that change live in [`docs/internal/FACTS.md`](docs/internal/FACTS.md).** Every other
  document links to them instead of repeating them; restating a number is how it
  starts drifting.
- **Both READMEs change together** (`README.md` and `README.zh-CN.md`) — a facade
  that has forked is worse than one that is out of date.
- **Every workaround gets an entry** in [`docs/internal/workarounds.md`](docs/internal/workarounds.md):
  what it is, when it triggers, how to work around it, and what would replace it.
  That ledger is never archived — entries are closed, not deleted.
- **Docs-only changes still have to be fact-checked**: does the limitation still
  exist? Has the sprint that fixed it shipped? A wrong document is worse than a
  stale one.
- **Prose in the Chinese-language documents uses Simplified Chinese only.**

## License

MIT — see [`LICENSE`](LICENSE).
