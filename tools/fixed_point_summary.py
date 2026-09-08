#!/usr/bin/env python3
"""fixed_point_summary.py — N≥3 selfhost closure 验算 human-readable summary
(v2.9.0 V2-C Part 1).

Usage:
  python tools/fixed_point_summary.py

输出 markdown 表格,直接进 changelog-v2.9.0.md (per feedback_changelog_umbrella)。

逻辑:
  1. 跑 compiler/tests/bootstrap/fixed_point.sh (v2.9.0 新加的 N≥3 closure 验算)
  2. 解析 stdout:N=3/4/5 sha 链 + cap_test 跨代结果
  3. 输出 markdown 表格:
     | N | expected | actual sha | result |
     |---|----------|------------|--------|
     | 3 | byte-equal | <sha> | ✅ PASS |
     | 4 | byte-equal | <sha> | ✅ PASS |
     | 5 | byte-equal | <sha> | ⚠️ INFO |

Exit code:0 = N=3 PASS,非 0 = N=3 FAIL (per feedback_fix_evaluation_rule)
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXED_POINT_SH = ROOT / "compiler" / "tests" / "bootstrap" / "fixed_point.sh"


def run_fixed_point():
    """Run fixed_point.sh and return (returncode, stdout, parsed_rows)."""
    if not FIXED_POINT_SH.exists():
        print(f"fixed_point_summary: fixed_point.sh not found at {FIXED_POINT_SH}",
              file=sys.stderr)
        return 1, "", []
    bash_path = shutil.which("bash") or "bash"
    result = subprocess.run(
        [bash_path, str(FIXED_POINT_SH)],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    rows = parse_fixed_point_output(result.stdout)
    return result.returncode, result.stdout, rows


def parse_fixed_point_output(stdout):
    """Parse fixed_point.sh stdout into [(N, sha, status), ...] tuples.

    Looks for lines like:
      [1/3] IL closure N=3 (D43 ship gate, primary):
        v1=7aeb...
        v2=7aeb...
        v3=7aeb...
      ✅ PASS (N=3 .il byte-equal)
    """
    rows = []
    current_n = None
    current_sha = None
    for line in stdout.splitlines():
        m = re.match(r"^\[(\d)/(\d)\] IL closure N=(\d)", line)
        if m:
            current_n = int(m.group(3))
            current_sha = None
            continue
        m = re.match(r"^  v\d=([0-9a-f]{64})", line)
        if m and current_n is not None:
            # 拿最后一条 v_N=N 的 sha (即 N 当前代)
            sha = m.group(1)
            if current_sha is None or len(sha) >= len(current_sha):
                current_sha = sha
            continue
        if current_n is not None and "PASS" in line and "N=" + str(current_n) in line:
            rows.append((current_n, current_sha or "?", "PASS"))
            current_n = None
            current_sha = None
            continue
        if current_n is not None and "INFO" in line and "N=" + str(current_n) in line:
            rows.append((current_n, current_sha or "?", "INFO"))
            current_n = None
            current_sha = None
            continue
        if current_n is not None and "FAIL" in line and "N=" + str(current_n) in line:
            rows.append((current_n, current_sha or "?", "FAIL"))
            current_n = None
            current_sha = None
            continue
    return rows


def render_markdown(rows):
    """Render parsed rows as markdown table."""
    lines = [
        "| N | expected | actual sha | result |",
        "|---|----------|-----------|--------|",
    ]
    for n, sha, status in rows:
        sha_short = sha[:16] + "..." if len(sha) > 16 else sha
        if status == "PASS":
            badge = "✅ PASS"
        elif status == "INFO":
            badge = "⚠️ INFO"
        else:
            badge = "❌ FAIL"
        lines.append(f"| {n} | byte-equal | `{sha_short}` | {badge} |")
    return "\n".join(lines)


def main():
    rc, stdout, rows = run_fixed_point()
    print("=== N≥3 selfhost fixed-point closure summary (v2.9.0) ===")
    print()
    if not rows:
        print("(no rows parsed from fixed_point.sh output)")
        print()
        print("--- raw stdout ---")
        print(stdout)
        return 1
    print(render_markdown(rows))
    print()
    # cap_test status (V3-C ship gate, SKIP on axis-v2 branch per v3.1.0)
    cap_status = "SKIP (V3-C only)"
    if "cap_test exit = 42" in stdout or "cap_test exit = SKIP" in stdout:
        if "❌ FAIL" in stdout and "cap_test" in stdout:
            cap_status = "❌ FAIL"
        elif "✅ PASS" in stdout and "cap_test" in stdout:
            cap_status = "✅ PASS"
        else:
            cap_status = "SKIP"
    print(f"cap_test: {cap_status}")
    print()
    print(f"(fixed_point.sh exit code: {rc})")
    return rc


if __name__ == "__main__":
    sys.exit(main())