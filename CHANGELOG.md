# Changelog

> **One line per release.** The detailed record — what changed, why, and how it was
> verified — lives in [`docs/archive/logs/`](docs/archive/logs/); the v4 axis umbrella is
> [`docs/archive/logs/v4/changelog-v4.0.0.md`](docs/archive/logs/v4/changelog-v4.0.0.md).
>
> The **single source of truth for the version number** is the `VERSION` file at the
> repository root. Never edit it by hand — run
> `python scripts/dev/bump_version.py set <X.Y.Z>`; the full flow, including the
> mandatory `make`, is in
> [`docs/internal/build.md`](docs/internal/build.md#版本号自动化).
>
> `set` also inserts the new row into the table below, and `check` asserts that this
> table's first row matches `VERSION` — so this file can no longer drift silently.

---

## Releases

> One row per **published release** — every version here has a GitHub release and a
> git tag. Changes that are in the tree but carry no release of their own are listed
> under [Change slots](#change-slots-no-release-tag) instead.

| Version | One-line summary |
|---|---|
| **v4.1.2** | `jhyy --version` never existed — said out loud, plus version-number automation (`VERSION` as the single source of truth) |
| **v4.1.1** | VS Code terminal profile probes for a real bash + a new `jhyy-bash.cmd` launcher; the "bundle a POSIX layer" plan is dropped |
| **v4.1.0** | The installer bundles a minimal native ucrt64 toolchain ⇒ end users no longer need MSYS2 |
| **v4.0.22** | Language-spec coverage audit: 34 regression gates added + three real std-lib defects and one compiler crash found |
| **v4.0.19** | The workaround ledger's ACTIVE bucket hits zero for the first time (14 → 0) |
| **v4.0.9-rc1** | The release chain itself is fixed: the regression gate now tests the compiler the job just built, tag pushes actually trigger a run, and the new SysV ABI gate caught W-116 on its first run |
| **v4.0.6** | W-101 attempt #7 succeeds — the root cause is really fixed and the v4.0.0 final tag is unblocked |
| **v4.0.2** | The first batch of real fixes on the v4.x axis (i64 literals, `mem_set` i64-store, the per-function local counter) |
| **v4.0.1** | The first real fix on the v4.x axis |
| **v4.0.0-rc1** | The v2.x and v3.x axes merge into main — one compiler instead of two; the QBE toolchain is gone, the in-memory self-backend is the only codegen path |

> `v4.0.0 final` was never promoted: the release was held back until the workaround
> ledger was clean, so the axis restarts at `v4.0.0-rc1`.

## Change slots (no release tag)

> These are **change slots, not releases** — there is no tag and no published artifact
> for them. Their content does ship, inside whichever tagged release was cut after the
> change landed. They are listed separately so that the table above stays a truthful
> record of *releases*.

| Slot | Change |
|---|---|
| v4.4.0 (stage 1) | Register allocator + safety net (byte-identical output); stage 2 is the emit layer consuming registers |
| v4.2.1 | Frame size computed from what the function actually needs (the hard-coded 8192-byte reserve is gone) ⇒ ~41% runtime |
| v4.2.0 | Runtime performance gate lands in CI (hard gate on static metrics, wall-clock only reported) + `bench.sh` timer really fixed |
| v4.0.21 | Side files are unique per PID (concurrent compiles stop colliding) + a Makefile variable that was never updated + a cross-drive rename failure + the C-side compiler deleted |
| v4.0.20 | An audit of "skipped test / new test" surfaced three problems in the gates themselves |
| v4.0.18 | Minimal exclusivity check for `&mut` + dead stub removal; lexer EOF guard; reproducible artifacts; `asm!` and memory barriers actually inlined into the function body |
| v4.0.17 | Two "allocate a fixed maximum" tables now allocate what is actually needed (which also fixed the temp table silently computing wrong values on overflow) |
| v4.0.16 | `std_os_*` wired to the real libc + `#[link_section]` lands in a real `.s` |
| v4.0.15 | `&mut` actually works |
| v4.0.14 | The enum ABI is unified on both sides (arguments by address, return value through sret) |
| v4.0.12 | SysV MEMORY class (structs larger than 16 B are passed on the stack) |
| v4.0.5 | W-101 attempt #6 (a separate address-holder pool) reverted |
| v4.0.4 | W-101 attempt #5 (the bitmap change) reverted — the logging-first RCA step shipped |
| v4.0.2.4 | W-098 i64 literal emission really fixed (three tiers: emit + IR + cast) |
| v4.0.2.3 | W-075 `mem_set` i64-store really fixed |
| v4.0.2.2 | W-096 per-function local counter really fixed on the emit side |
| v4.0.2.1 | W-074.6 multi-function emission really fixed (3 sub-bugs) + part of the W-096 1024 cap |

> **The performance line (v4.2.x, v4.4.x) shares the v4 axis, but its numbering does not
> follow the v4.0.x series** — the schedule is in [`docs/internal/FACTS.md`](docs/internal/FACTS.md) § 4.

---

## Earlier axes

- **v3.x** — language features (ended at v3.4.2)
- **v2.x** — the QBE rewrite and multi-target support (ended at v2.16.0)
- **v1.x** — self-hosting (ended at v1.8.3)
- **v0.x** — the C compiler (frozen at the v1.0.0 baseline)

Their per-version records are in [`docs/archive/logs/`](docs/archive/logs/), their
sprint plans in [`docs/archive/plans/`](docs/archive/plans/).
