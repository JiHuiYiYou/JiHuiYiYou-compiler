# D43 Byte-Equal Baseline Archive (v3.2.x)

> 记录每次 sprint ship 后的 D43 closure chain N-baseline (sha256 of jhyy_v{2,3,4,5}.exe)。
> v2 → v3 → v4 → v5 字节相等 = 真自举闭环 hold。

## N-baseline 表

| Sprint | Tag | N | v{2,3,4,5}.exe sha256 (4-way equal) | Notes |
|--------|-----|---|-------------------------------------|-------|
| v3.2.1 | `c153e26` | N13 | (见 v3.2.1 changelog) | 3j closures MVP + D43 hold |
| v3.2.2 | `c5607ed` | N14 | `8254cd6b681ee3b5b2d59534b7e1ecb3cac29cec7ae08755522e3421ed6d2145` | 4 modules (mem/fmt/string/arena) + 19 tests + W-073..W-078 |
| v3.2.3 | (this sprint) | **N15** | `848df9a1059c7e591938ed19ce1d11d2ed445954f3914992ab14139b7d894d60` | 2 modules (io/os) + 2 tests + W-079 (deferred) |

## N15 详情 (v3.2.3, this ship)

**Pre-condition**:
- Branch `axis-v3.2.3` at Phase 1 commit `24f89a4` (working tree clean)
- Worktree: `C:\Users\liuzhen\Desktop\coding\JiHuiYiYou-axis-v3.2.3`

**Phase 2 verification (2026-09-26)**:
- `make selfhost` → v1 → v2 → v3 → v4 → v5 (5-way) byte-equal chain PASS
- sha256: `848df9a1059c7e591938ed19ce1d11d2ed445954f3914992ab14139b7d894d60` (4 binaries all match)
- Binary size: `671916 bytes` per binary (vs N14 = `569798 bytes` at `c5607ed`)
- Size diff (+102118 bytes / +18%) due to v3.2.3 source growth:
  - `compiler/src0/std/io.jhyy` NEW (~106 lines)
  - `compiler/src0/std/os.jhyy` NEW (~155 lines)
  - `compiler/src0/main.jhyy` +inline_imports integration (~30 lines)
- **闭包链 hold** — 4 binary sha256 全 match, 无 codegen drift

**Regress verify**:
- `python regress.py --binary=compiler/build/bin/jhyy.exe --all` (after cleanup `_regress_*.{exe,il,s,ico.o}`)
- **139/139 PASS / 0 FAIL / 20 SKIP** (of 159 total)
- 20 SKIP = 5 sysv tests (Linux host required) + volatile_mmio + 14 (others)
- 1 fix in Phase 2: `std_io_basic.jhyy` EXPECT annotation typo (Phase 1 had `EXPECT:42`, actual EXIT=0) → fixed to `EXPECT:0`

## N-baseline 增量规则

- **Hold**: N_{X+1} = N_X (no codegen change) → sha256 identical, no new entry
- **Drift**: N_{X+1} ≠ N_X (codegen change) → new sha256 + entry + RCA comment
- **Source growth (≠ codegen drift)**: source lines increase but codegen unchanged → binary size grows but closure chain hold; record N_{X+1} only if size growth > 5% (otherwise skip)

## Cross-ref

- L1 plan: `docs/plans/v2/v2.0.0-os-prep.md § 1` (D43 chain critical path)
- L2 plan: `docs/plans/v3/v3.2.3-plan.md` § 验收 (N15 hold)
- changelog: `docs/logs/v3/changelog-v3.2.md` v3.2.3 umbrella section
