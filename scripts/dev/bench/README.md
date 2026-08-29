# scripts/dev/bench/

Performance / benchmark dev 脚本。

| 脚本 | 用途 |
|------|------|
| `self_host_bench.sh` | 测量 JHYY self-hosting compile time, mirrors TPV "self-hosting 2 min" 和 "+ llc + link 2:50" framing |

输出对比 reference:
- C-side jhyy_stage0.exe 编译 src0/main.jhyy: ~15s
- jhyy.exe → jhyy_v2.exe → jhyy_v3.exe → jhyy_v4.exe 链: ~50s total
- v1.x 真自举总时间: ~65s (Windows process startup overhead ~50-100ms × N 次)
- 退步 >1.3x 即触发排查 (per `project_v1_0_perf_baseline`)

注意: 跨平台对比时 Windows 比 Linux 慢 ~15-20% (process spawn overhead).