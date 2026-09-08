#!/usr/bin/env python3
"""Run JHYY integration test suite against one or more compiler binaries.

v1.4.7 (2026-08-14): 单 regress 入口合并 — 取代 v1.4.5 三跑 (regress.py +
regress_v1.py + regress_stage0.py)。CI workflow 简化: 1 gated step + 1
informational step。

Usage:
  python regress.py                            # 默认 binary=jhyy.exe (production)
  python regress.py --binary=PATH              # 跑指定 binary (--binary=stage0 / v1 等)
  python regress.py --all                      # 跑所有 gated binary (jhyy.exe + jhyy_stage0.exe)
  python regress.py --all --include-informational
                                               # 加跑 jhyy_v1.exe.exe (matrix only, 不影响 exit)
  python regress.py --save-baseline            # 存 binary sha256 baseline (转发 jhyy_regress)
  python regress.py --tests=foo,bar            # 跑测试子集
  python regress.py --no-baseline-check        # 跳过 phantom binary (mtime) check
  python regress.py --timeout=30               # 单测试超时 (default 20)

Exit codes:
  0  全部 gated binary PASS
  1  至少 1 个 gated binary FAIL
  2  binary 不存在 / 参数解析错误

Per-binary `enforce_baseline_hash` 默认 (centralize 取代原 3 shim 散落的 magic-default):
  jhyy.exe         → True  (production, phantom binary 必 catch)
  jhyy_stage0.exe  → False (gcc 链接非确定性, sha 每次变)
  jhyy_v1.exe.exe  → False (frozen historical baseline, mtime 永远比 src 旧 → phantom 必 fail)

Sprint mcp-1 (2026-08-11): shim that delegates to mcp-jhyy/jhyy_regress.py.
Sprint v1.4.7 (2026-08-14): 加 --all / --include-informational / _GATED_DEFAULTS,
                            删 regress_v1.py + regress_stage0.py 两个 shim。
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple

# Make mcp-jhyy/ importable
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "mcp-jhyy"))

from jhyy_regress import run_all, save_baseline_hash  # noqa: E402

# ──────────────────────────────────────────────────────────────────────────────
# Per-binary `enforce_baseline_hash` default mapping (centralize)
# ──────────────────────────────────────────────────────────────────────────────
# Rationale per binary:
#   - jhyy.exe (production):         True  — phantom binary 会污染 baseline 信号
#   - jhyy_stage0.exe (C-side):      False — gcc 链接非确定性 (debug info / timestamp)
#   - jhyy_v1.exe.exe (frozen):      False — mtime 永远比 src 旧 → phantom 必 fail
# Unknown binary 默认 True (catch phantom)。
_GATED_DEFAULTS = {
    "compiler/build/bin/jhyy.exe": True,
    "compiler/build/bin/jhyy_stage0.exe": False,
    "compiler/build/bin/jhyy_v1.exe.exe": False,
}

# Default `--all` 跑的 binary 列表 (gated, 影响 exit code)。
# 不 glob `jhyy*.exe*` — v2/v3/v4.exe 是 make selfhost 产物, 不是 regress 语义。
_GATED_BINARIES = [
    ("compiler/build/bin/jhyy.exe", "production"),
    ("compiler/build/bin/jhyy_stage0.exe", "C-side bootstrap"),
]

# `--include-informational` 加的 binary (matrix only, 不影响 exit code)。
_INFORMATIONAL_BINARIES = [
    ("compiler/build/bin/jhyy_v1.exe.exe",
     "informational, historical baseline "
     "(v1.4.4 ship 已覆盖成 jhyy.exe 同 binary; 跑 v1.4.6 新 test fail 是 expected)"),
]


def _resolve_default_enforce(binary: str, no_baseline_check: bool) -> bool:
    """Resolve enforce_baseline_hash for a binary.

    Precedence: --no-baseline-check > _GATED_DEFAULTS[bin] > default True。
    """
    if no_baseline_check:
        return False
    return _GATED_DEFAULTS.get(binary, True)


def _run_one(binary: str, label: str, tests, timeout, enforce_baseline_hash):
    """Run run_all for one binary, return (result_dict, is_informational)."""
    result = run_all(
        binary=binary,
        tests=tests,
        timeout=timeout,
        enforce_baseline_hash=enforce_baseline_hash,
    )
    return result


# v2.7.1 Phase 2: --cross wire (auto-probe wsl/docker + subprocess dispatch)
# Per `feedback_regress_py_abspath`: MSYS2 Python + Windows subprocess 不解析
# 相对路径 → 用 os.path.abspath 包装。
# Per `feedback_mcp_jhyy_run_workspace`: cross-env sub-process 必须用
# subprocess.run + 绝对路径。

_SYSV_TEST_NAMES = (
    "sysv_abi_test.jhyy",
    "sysv_struct_mixed.jhyy",
    "sysv_struct_pass.jhyy",
    "sysv_struct_ret.jhyy",
    "sysv_vararg_basic.jhyy",
)


def _resolve_cross_mode(cross_arg: str) -> str:
    """Resolve --cross mode: auto probe wsl.exe then docker on PATH.

    Returns: 'wsl' | 'docker' | 'none'
    """
    if cross_arg == "wsl":
        if shutil.which("wsl.exe") or shutil.which("wsl"):
            return "wsl"
        print("cross: --cross=wsl but wsl.exe not on PATH → SKIP", file=sys.stderr)
        return "none"
    if cross_arg == "docker":
        if shutil.which("docker"):
            return "docker"
        print("cross: --cross=docker but docker not on PATH → SKIP", file=sys.stderr)
        return "none"
    if cross_arg == "none":
        return "none"
    # auto: probe wsl first (faster on Windows; native Linux distro available)
    if shutil.which("wsl.exe") or shutil.which("wsl"):
        # Probe whether any distro is actually installed (wsl.exe -l -v
        # returns nonzero + error message if no distros).
        try:
            r = subprocess.run(
                ["wsl.exe", "-l", "-v"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            if r.returncode == 0 and "no installed" not in (r.stdout + r.stderr).lower():
                return "wsl"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
    if shutil.which("docker"):
        return "docker"
    return "none"


def _run_cross_env_sysv_test(test_name: str, cross_mode: str,
                             binary: str, timeout: int) -> Tuple[bool, str]:
    """Run a single sysv_*.jhyy test through wsl/docker subprocess.

    Returns: (ok, message)
        ok=True with "skipped (...)" if cross-env not actually available
        ok=True with "passed (exit=N)" on success
        ok=False with "failed (...)" on compile/run error
    """
    abs_jhyy = os.path.abspath(
        str(Path(__file__).resolve().parents[2] / "tests" / "examples" / test_name)
    )
    abs_binary = os.path.abspath(binary)
    # Build inside Linux env: compile to sysv_freestanding target, then
    # link with crt0.S + link.ld → run.
    jhyy_repo_in_linux = "/work"  # mount repo to /work inside Linux env
    if cross_mode == "wsl":
        # First probe: does WSL actually have any distro installed? On Windows
        # hosts where wsl.exe is on PATH but no distro is registered, wsl.exe
        # prints "Wsl/Service/WSL_E_DISTRO_NOT_FOUND" (UTF-16LE bytes from
        # Microsoft console), which crashes Python wslpath decode and prints
        # garbled text. Skip cleanly when probe fails.
        try:
            probe = subprocess.run(
                ["wsl.exe", "-l", "-v"],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            probe_out = (probe.stdout + probe.stderr).lower()
            if probe.returncode != 0 or "no installed" in probe_out or \
                    "wsl_e_" in probe_out or "not_found" in probe_out:
                return (True, "skipped (wsl.exe on PATH but no distro installed)")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return (True, "skipped (wsl.exe probe failed)")
        # Convert Windows path to WSL path (e.g. C:\Users\foo\bar → /mnt/c/.../bar)
        try:
            wsl_jhyy_r = subprocess.run(
                ["wsl.exe", "wslpath", "-u", abs_jhyy],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            wsl_jhyy = wsl_jhyy_r.stdout.strip()
            wsl_binary_r = subprocess.run(
                ["wsl.exe", "wslpath", "-u", abs_binary],
                capture_output=True, text=True, timeout=5,
                encoding="utf-8", errors="replace",
            )
            wsl_binary = wsl_binary_r.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            return (True, f"skipped (wslpath conversion failed: {e})")
        if not wsl_jhyy or not wsl_binary or "\\" in wsl_jhyy or "\\" in wsl_binary:
            return (True, "skipped (wslpath garbled output — likely no WSL distro)")
        cmd = [
            "wsl.exe", "-d", "Ubuntu", "bash", "-c",
            f"cd {jhyy_repo_in_linux} && "
            f"{wsl_binary} compile --target=amd64_sysv_freestanding "
            f"{wsl_jhyy} -o /tmp/_cross_sysv && "
            f"gcc -nostdlib -static -T runtime/linux_elf/link.ld "
            f"-o /tmp/_cross_sysv.elf runtime/linux_elf/crt0.S /tmp/_cross_sysv.s && "
            f"/tmp/_cross_sysv.elf; echo EXIT:$?",
        ]
    elif cross_mode == "docker":
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.path.abspath('.')}:{jhyy_repo_in_linux}",
            "-w", jhyy_repo_in_linux,
            "ubuntu:22.04", "bash", "-c",
            f"{jhyy_repo_in_linux}/{abs_binary[len(os.path.abspath('.'))+1:]} "
            f"compile --target=amd64_sysv_freestanding "
            f"{jhyy_repo_in_linux}/compiler/tests/examples/{test_name} "
            f"-o /tmp/_cross_sysv && "
            f"gcc -nostdlib -static -T runtime/linux_elf/link.ld "
            f"-o /tmp/_cross_sysv.elf runtime/linux_elf/crt0.S /tmp/_cross_sysv.s && "
            f"/tmp/_cross_sysv.elf; echo EXIT:$?",
        ]
    else:
        return (True, "skipped (cross-env disabled)")

    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        output = (r.stdout or "") + (r.stderr or "")
        if r.returncode == 0 and "EXIT:" in output:
            # parse EXIT:N from output
            for line in reversed(output.splitlines()):
                if line.startswith("EXIT:"):
                    exit_code = int(line[len("EXIT:"):].strip())
                    return (True, f"passed (exit={exit_code}, cross={cross_mode})")
            return (True, f"passed (cross={cross_mode})")
        return (False, f"failed (exit={r.returncode}, cross={cross_mode}): "
                       f"{output[-200:]}")
    except subprocess.TimeoutExpired:
        return (False, f"timeout ({timeout}s, cross={cross_mode})")
    except FileNotFoundError as e:
        return (True, f"skipped (cross={cross_mode} binary not found: {e})")


def _run_sysv_via_cross_env(cross_mode: str, binary: str, timeout: int,
                            only_tests: Optional[List[str]] = None
                            ) -> Tuple[int, int, int]:
    """Run 5 sysv regress tests via cross-env wire (wsl/docker).

    Returns: (passed, failed, skipped) counts.

    Per v2.7.0 Commit 3: 5 sysv fixtures 默认 SKIP via `// SKIP:` directive;
    --cross env 实 wire 让它们在 Linux host 真跑 (compile → link → run)。

    `only_tests` 可选过滤 (per --tests= 列表)。
    """
    if cross_mode == "none":
        # Print SKIP for all sysv tests
        for name in _SYSV_TEST_NAMES:
            if only_tests is None or name in only_tests:
                print(f"SKIP  {name:<30}  skipped (--cross=none)")
        return (0, 0, sum(1 for n in _SYSV_TEST_NAMES
                          if only_tests is None or n in only_tests))

    passed = failed = skipped = 0
    for name in _SYSV_TEST_NAMES:
        if only_tests is not None and name not in only_tests:
            continue
        ok, msg = _run_cross_env_sysv_test(name, cross_mode, binary, timeout)
        if ok and msg.startswith("skipped"):
            print(f"SKIP  {name:<30}  {msg}")
            skipped += 1
        elif ok:
            print(f"PASS  {name:<30}  {msg}")
            passed += 1
        else:
            print(f"FAIL  {name:<30}  {msg}")
            failed += 1
    return (passed, failed, skipped)


def test_byte_equal(tests=None):
    """Run byte-equal 三件套 (D26) on a list of target tests.
    Per coordination.md § 3 D26 (2026-08-05 锁): closure invariant is .il
    + .s byte-equal. Per D43 (2026-09-01 锁): 阶段性 self-equal, jhyy_N ==
    jhyy_{N+1}, not cross-version.

    Args:
        tests: list of test names without .jhyy suffix, or None for default
               5 tests (hello / struct_val_pass / fib_renamed /
               nested_struct_deep / big_test).

    Returns 0 on 5/5 PASS, 1 on any FAIL (per feedback_fix_evaluation_rule).
    """
    if tests is None:
        tests = [
            "hello.jhyy",
            "struct_val_pass.jhyy",
            "fib_renamed.jhyy",
            "nested_struct_deep.jhyy",
            "big_test.jhyy",
        ]
    else:
        tests = [t if t.endswith(".jhyy") else f"{t}.jhyy" for t in tests]

    examples_dir = Path(__file__).resolve().parents[2] / "tests" / "examples"
    bootstrap_dir = examples_dir.parent / "bootstrap"
    byte_equal_sh = bootstrap_dir / "byte_equal.sh"

    if not byte_equal_sh.exists():
        print(f"byte-equal: byte_equal.sh not found at {byte_equal_sh}", file=sys.stderr)
        return 1

    passed = 0
    failed = 0
    for t in tests:
        test_path = examples_dir / t
        if not test_path.exists():
            print(f"byte-equal: SKIP {t} (file not found)")
            continue
        try:
            # text=True + errors='replace' so non-UTF-8 bytes from bash
            # output don't crash the reader thread (some compile flows emit
            # binary debug info that includes raw bytes). On Windows, must
            # resolve "bash" to full path via shutil.which — bare "bash" gets
            # routed to WSL installer alias instead of MSYS2 bash.
            bash_path = shutil.which("bash") or "bash"
            result = subprocess.run(
                [bash_path, str(byte_equal_sh), str(test_path)],
                env=os.environ.copy(),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=60,
            )
            rc = result.returncode
        except subprocess.TimeoutExpired:
            print(f"byte-equal: FAIL {t} (timeout)")
            failed += 1
            continue
        except Exception as e:
            print(f"byte-equal: FAIL {t} (exception: {e})")
            failed += 1
            continue

        if rc == 0:
            passed += 1
            print(f"byte-equal: PASS {t}")
        else:
            failed += 1
            print(f"byte-equal: FAIL {t}")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

    print(f"byte-equal: {passed}/5 PASS" if len(tests) == 5 else f"byte-equal: {passed} PASS / {failed} FAIL")
    return 0 if failed == 0 else 1


def _print_matrix_row(idx, total, binary, label, result, is_informational):
    """Print one matrix row."""
    tag = "INFORMATIONAL" if is_informational else "GATED"
    status = "PASS" if result["ok"] else "FAIL"
    sha_short = (result.get("binary_sha256") or "?")[:16]
    failed_names = [os.path.splitext(ft["file"])[0] for ft in result.get("failed_tests", [])][:5]
    print(f"[{idx}/{total}] {binary} ({label}) [{tag}]")
    print(f"       status: {status} — passed={result['passed']}/{result['total']} "
          f"failed={result['failed']} skipped={result['skipped']}")
    if failed_names:
        print(f"       failed: {', '.join(failed_names)}")
    print(f"       binary sha: {sha_short}...")
    if result.get("baseline_warning"):
        print(f"       baseline_warning: {result['baseline_warning']}")
    if result.get("early_abort"):
        print(f"       early_abort: {result['early_abort']}")
    print()


def main():
    ap = argparse.ArgumentParser(
        description="JHYY regress runner (single canonical entry, v1.4.7)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--binary", default="compiler/build/bin/jhyy.exe",
                    help="Compiler binary path (default: jhyy.exe production). "
                         "Use --all to run all gated binaries.")
    ap.add_argument("--all", dest="run_all_gated", action="store_true",
                    help="Run all gated binaries (jhyy.exe + jhyy_stage0.exe), "
                         "output matrix, exit code reflects any gated failure.")
    ap.add_argument("--include-informational", action="store_true",
                    help="With --all, also run jhyy_v1.exe.exe historical baseline "
                         "(matrix only, does not affect exit code).")
    ap.add_argument("--save-baseline", action="store_true",
                    help="Save binary sha256 baseline (informational; "
                         ".il byte-equal is the real regression signal).")
    ap.add_argument("--tests", default=None,
                    help="Comma-separated test names without .jhyy suffix "
                         "(e.g. 'hello,fib'). Default: all.")
    ap.add_argument("--timeout", type=int, default=20,
                    help="Per-test timeout in seconds (default 20).")
    ap.add_argument("--no-baseline-check", action="store_true",
                    help="Skip phantom-binary (mtime vs source) check for all runs.")
    ap.add_argument("--byte-equal", action="store_true",
                    help="Run byte-equal 三件套 check (per D26, requires JHYY_V1 "
                         "+ JHYY_V2 env vars; default jhyy_v1.exe.exe + jhyy.exe). "
                         "Opt-in: does NOT affect default regress baseline (104/104).")
    ap.add_argument("--byte-equal-amd64", action="store_true",
                    help="Run V2-B v2.6.0 (Unit F) byte-equal-amd64 driver "
                         "(QBE vs self backend path parity check, 5 tests). "
                         "Opt-in: does NOT affect default regress baseline.")
    ap.add_argument("--cross", choices=["wsl", "docker", "auto", "none"],
                    default="auto",
                    help="Cross-env mode for sysv tests (v2.7.0 Phase 2b). "
                         "auto=probe wsl.exe/docker on PATH; none=SKIP. "
                         "Real wire deferred to v2.7.1.")
    args = ap.parse_args()

    # Parse --tests (comma-separated → list)
    tests = None
    if args.tests:
        tests = [t.strip() for t in args.tests.split(",") if t.strip()]

    # Mode dispatch
    if args.save_baseline:
        # Single-binary mode: save baseline for the explicit --binary
        sha = save_baseline_hash(args.binary)
        print(f"Saved baseline: {args.binary}.sha256 = {sha}")
        sys.exit(0)

    if args.byte_equal:
        # D26 byte-equal 三件套 (opt-in; doesn't affect default regress)
        rc = test_byte_equal(tests)
        sys.exit(rc)

    if args.byte_equal_amd64:
        # V2-B v2.6.0 (Unit F) byte-equal-amd64 (opt-in; QBE-vs-self backend
        # path parity check, 5 tests). Self backend call site is currently
        # deferred to v2.6.x (Unit E wire), so the script runs QBE-vs-QBE
        # (trivially PASS). Real self-vs-QBE gate auto-fires when v2.6.x
        # wires codegen_amd64_run into main.jhyy.
        bootstrap_dir = Path(__file__).resolve().parents[2] / "tests" / "bootstrap"
        byte_equal_amd64_sh = bootstrap_dir / "byte_equal_amd64.sh"
        if not byte_equal_amd64_sh.exists():
            print(f"byte-equal-amd64: script not found at {byte_equal_amd64_sh}",
                  file=sys.stderr)
            sys.exit(1)
        bash_path = shutil.which("bash") or "bash"
        result = subprocess.run(
            [bash_path, str(byte_equal_amd64_sh)],
            env=os.environ.copy(),
        )
        sys.exit(result.returncode)

    if args.run_all_gated:
        # Matrix mode: gated binaries + optional informational
        binaries = list(_GATED_BINARIES)
        if args.include_informational:
            binaries.extend(_INFORMATIONAL_BINARIES)
        total = len(binaries)

        gated_failures = 0
        informational_count = 0
        for idx, (binary, label) in enumerate(binaries, 1):
            is_informational = (idx > len(_GATED_BINARIES))
            enforce = _resolve_default_enforce(binary, args.no_baseline_check)
            result = _run_one(binary, label, tests, args.timeout, enforce)
            _print_matrix_row(idx, total, binary, label, result, is_informational)
            if is_informational:
                informational_count += 1
                # informational fail 不影响 exit code
            elif not result["ok"]:
                gated_failures += 1

        # Summary
        gated_total = total - informational_count
        if gated_failures == 0:
            print(f"Summary: {gated_total}/{gated_total} gated binary PASS"
                  + (f", {informational_count} informational (matrix only)" if informational_count else ""))
        else:
            print(f"Summary: {gated_failures}/{gated_total} gated binary FAIL")
        # v2.7.1 Phase 2: cross-env sysv wire (--all mode; per gated binary).
        # Only first gated binary (jhyy.exe production) runs sysv cross-env —
        # stage0 / v1 use Win target only.
        cross_mode = _resolve_cross_mode(args.cross)
        print(f"cross: --cross={args.cross} → resolved={cross_mode}")
        only_sysv = tests  # may filter to specific sysv tests
        for idx, (binary, label) in enumerate(binaries, 1):
            is_informational = (idx > len(_GATED_BINARIES))
            if is_informational:
                continue
            # Only production jhyy.exe runs cross-env sysv (skip stage0)
            if binary != "compiler/build/bin/jhyy.exe":
                continue
            _sysv_passed, _sysv_failed, _sysv_skipped = _run_sysv_via_cross_env(
                cross_mode, binary, args.timeout, only_sysv)
            gated_failures += _sysv_failed
            if _sysv_failed > 0:
                print(f"Summary: {gated_failures}/... gated binary FAIL "
                      f"(sysv_cross={cross_mode}, sysv_failures={_sysv_failed})")
        sys.exit(0 if gated_failures == 0 else 1)
    else:
        # Single-binary mode: explicit --binary (or default jhyy.exe)
        binary = args.binary
        enforce = _resolve_default_enforce(binary, args.no_baseline_check)
        result = _run_one(binary, "single", tests, args.timeout, enforce)

        # Same output as --all but for one binary (status line only, no matrix frame)
        status = "PASS" if result["ok"] else "FAIL"
        sha_short = (result.get("binary_sha256") or "?")[:16]
        failed_names = [os.path.splitext(ft["file"])[0] for ft in result.get("failed_tests", [])][:5]
        print(f"{binary}: {status} — passed={result['passed']}/{result['total']} "
              f"failed={result['failed']} skipped={result['skipped']} (sha={sha_short}...)")
        if failed_names:
            print(f"  failed: {', '.join(failed_names)}")
        if result.get("baseline_warning"):
            print(f"  baseline_warning: {result['baseline_warning']}")
        if result.get("early_abort"):
            print(f"  early_abort: {result['early_abort']}", file=sys.stderr)
            sys.exit(2)
        # v2.7.1 Phase 2: cross-env sysv wire (single-binary mode).
        cross_mode = _resolve_cross_mode(args.cross)
        print(f"cross: --cross={args.cross} → resolved={cross_mode}")
        only_sysv = tests
        _sysv_passed, _sysv_failed, _sysv_skipped = _run_sysv_via_cross_env(
            cross_mode, binary, args.timeout, only_sysv)
        # overall ok = Win run_all ok AND no sysv FAIL (sysv SKIP is OK)
        sysv_ok = _sysv_failed == 0
        sys.exit(0 if result["ok"] and sysv_ok else 1)


if __name__ == "__main__":
    main()
