# Security Policy

JHYY (机会翼游) is a **pre-1.0** compiler project maintained by one person. This page
says what counts as a security problem here, how to report one without leaking it,
and what happens afterwards.

If you only want to know the short version:

> **Do not open a public issue for a suspected vulnerability.** Use
> [the private advisory form](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/security/advisories/new).

---

## Reporting a vulnerability

**Do not open a public issue for a suspected vulnerability.** Public issues are
indexed, mirrored and cached within minutes — a public report can turn a fix into an
exploit before a patch exists.

Use GitHub's private advisory flow:

**→ https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/security/advisories/new**

It opens a thread visible only to you and the maintainer. If that form is
unavailable to you, email the maintainer at **15901598712@163.com** with the same
information and ask for a receipt confirmation.

Please include:

| Item | Why it matters |
|---|---|
| **The version** — the `VERSION` file at the repository root, or the first line of `jhyy --help` | fixes land on the newest release first |
| **The reproducer** — the complete `.jhyy` source, or the exact command line | a one-line diff is the difference between a same-day fix and a week of questions |
| **Actual vs. expected** — what happened, and what should have happened | |
| **The exit code** | see the trap below |
| **Provenance** — the released binary, or a self-hosted build | the two can differ |
| **Impact** — what an attacker gains, and what they must already have | it decides severity, and severity decides the deadline |

> [!TIP]
> **Capture exit codes with a harness or Python `subprocess`, not by reading `$?` in
> MSYS2 bash.** Bash truncates exit codes to 8 bits (`value & 0xFF`), so an expected
> code ≥ 256 has to be reduced before you compare it (827 → 59, 501 → 245,
> 300 → 44, 1000 → 232). A "wrong exit code" report is often just this.

> [!NOTE]
> **You do not need to prove exploitability.** A source-level demonstration is
> enough. "Here is the `.jhyy` file that makes the compiler write outside the
> buffer" is a complete report.

---

## What counts as a vulnerability

### In scope

- **Memory-safety violations in generated code.** The compiler emits code that
  writes out of bounds, reads or writes uninitialized memory, corrupts the stack,
  or computes a wrong address — for a program that does not itself do so.
- **Memory safety inside the compiler.** A crafted `.jhyy` source, or any other
  input file the compiler reads, that makes the compiler itself corrupt memory,
  write outside an allocation, or execute attacker-controlled bytes. The compiler
  parses untrusted input; that input must not be able to take over the process.
- **Code execution through the toolchain.** Anything that makes the compiler run
  code the user did not intend to run: an import that resolves to an unexpected
  file, an argument that reaches an external program unsanitized, or a build
  directory whose contents can redirect the build.
- **Path traversal in the installer or in the release assets** — writing outside
  the directory the installer is supposed to touch.
- **Release integrity.** A published `SHA256.txt` that does not cover the asset it
  is shipped with, or a release asset that differs from what the tagged source
  produces.

### Out of scope

- **Misuse of the documented unsafe features.** Unchecked slice indexing, an
  `extern fn` declared with the wrong C signature, hand-written `asm!`,
  `#[naked]` functions — these are sharp tools with sharp edges, and the
  documentation says so.
- **Language-level gaps.** No borrow checker yet, no float formatter, no
  `Vec<T>` over element types — these are tracked in the language spec's
  Appendix B and in the public workaround ledger, not as vulnerabilities.
- **Compiler crashes on input you control**, with no memory-safety impact. These
  are bugs, and a bug report is the right channel — but they are not
  vulnerabilities. (Unless the crash is reachable from a source file you did not
  write.)
- **Bugs in the generated program's own logic.**
- **Vulnerabilities in the third-party toolchain bundled with the Windows
  installer.** Report those to their upstream projects; tell us anyway if you
  believe *the bundling* introduces a problem of its own.

---

## Supported versions

| Line | Supported |
|---|---|
| **The latest release** | ✅ security fixes |
| Earlier releases | ❌ — upgrade to the latest release |
| `main` (unreleased) | ⚠️ best effort — a fix ships with the next release |

This page deliberately names **no version numbers**: the latest release is always
the supported one. See the [releases page](https://github.com/JiHuiYiYou/JiHuiYiYou-compiler/releases)
for what is current.

---

## What happens after you report

| Stage | Target |
|---|---|
| Acknowledgement that the report was received | 7 days |
| Triage — is it a vulnerability, and how severe | 14 days |
| Fix released for a critical or high severity report | as soon as the fix is green in CI — no fixed date, but nothing is deliberately held back |
| Fix released for a medium or low severity report | the next release |

These are **targets, not guarantees** — this is a one-person project with a day job.
If a report is not acknowledged inside the window, that is a defect in this
process: say so in the same thread, and treat the silence as worth escalating.

You will be told the triage outcome even when the answer is "not a vulnerability" —
a reasoned "no" is a real answer, and it is more useful to you than silence.

---

## Disclosure

- **Give the maintainer a reasonable window to publish a fix before disclosing
  publicly.** The default expectation is **90 days** from the first report. Ask
  for more time if a fix needs it; an explicit extension is fine.
- **If a mitigation exists before the fix does** (for example: "do not compile
  untrusted `.jhyy` files with a build you do not trust"), it is published in the
  advisory immediately — you will not be asked to keep it quiet.
- **Credit** is offered in the advisory and the release notes, under the name or
  handle you prefer. Say so if you would rather stay anonymous.
- **Already public?** If the vulnerability is already described somewhere public,
  say so in the report — it changes the disclosure timeline, not whether it gets
  fixed.

---

## Security-relevant properties of this project

Facts a user should know, because they change what "vulnerable" means here.

- **The compiler is a native program that parses untrusted input.** A `.jhyy`
  source from an unknown origin is untrusted input, exactly like a file handed to
  any other parser. **There is no sandbox** — the compiler runs with your user's
  privileges, and it is not hardened against a malicious source file beyond what
  its own memory-safety fixes provide.
- **The compiler shells out to an external C toolchain to link.** It resolves a
  `gcc` path (an environment override first, then a bundled list, then `PATH`)
  and runs it. Pointing that override at an untrusted binary means running that
  binary — treat the environment as part of your trust boundary.
- **`jhyy run` executes the program it just compiled.** Compiling and running
  untrusted source is running untrusted code; the compiler adds no isolation.
- **The compiler has no network access and no telemetry.** It opens no socket,
  sends nothing anywhere, and reads no credential. The only environment variables
  it consults are the toolchain-path override and two debugging switches.
- **Generated code carries no extra hardening.** The compiler inserts no stack
  canaries and no guard pages of its own; what the linker applies is what you get.
- **The Windows installer bundles a third-party native toolchain.** That bundle is
  a supply-chain surface of its own. It is covered by the checksums published
  alongside each release, not by a copy vendored in this repository.
- **Release assets are published with a `SHA256.txt`**, and the release workflow
  verifies the checksums and refuses to publish if they do not match.

---

## Reporting something that is not a vulnerability

- **A compiler bug** (wrong output, a crash, a diagnostic that does not make
  sense) → a normal issue. The [contribution guide](CONTRIBUTING.md) has the
  reproducer format that makes such a report actionable.
- **A question about how the language works** → GitHub Discussions.
- **A known limitation you want to work on** → the roadmap is public; see
  [`docs/internal/FACTS.md`](docs/internal/FACTS.md).
- **A workaround that should be in the ledger** → the ledger is public and
  maintained at [`docs/internal/workarounds.md`](docs/internal/workarounds.md);
  entries are added, never deleted.
