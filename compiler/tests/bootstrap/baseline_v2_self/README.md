# V2 self-backend golden .s — Gate-0 [2/4] 对照基线

## 用途

Gate-0 (`byte_equal_selfbackend.sh`) 在 V3 self-backend 修好后,需要跟一份已知的"正确答案"比对 sha。但
QBE 路径的 .s **不能** 当这个 baseline,因为 V3 self-backend 跟 QBE 是两套独立的 codegen 实现,
不可能 byte-equal(per 用户 2026-09-23 风险 #2)。需要的是 **self-backend vs self-backend** 的对照。

V2 (`axis-v2` branch, v2.16.0) self-backend 是真跑通的(V2 已有 golden 证明 exit 1/99/1 正确)。
这 3 个 .s 文件 = V2 self-backend 在 `axis-v2` HEAD (`0b4cde5`) 上对 3 个 fmod 测试实跑产出,
作为 V3 self-backend 真修后的对照 gold。

## 文件清单

| File | V2 exit | sha256 |
|---|---|---|
| `v2_self_fmod_basic.s` | 1 | `25eccf0ad9e291f185dc3a46798dfcfdb09ba560fd75524ef0a6ed7d9194a69e` |
| `v2_self_fmod_negative.s` | 99 | `8b1d6f333eb19191df14d4db0944e50e6aabc3ea2d2fc160f9d2f630d6471892` |
| `v2_self_fmod_f32.s` | 1 | `e6346d245ed4b6edbb5dcd8c7c71d38794fc5d68dfd34c5eca11e31d80b4b0b5` |

## 重生成

仅在 `axis-v2` self-backend 行为变化时(rare,需 v2.x 真修复合)重新生成:

```bash
cd axis-v2  # 或 /c/Users/liuzhen/Desktop/coding/JiHuiYiYou-axis-v2
cd compiler/tests/examples
for t in fmod_basic fmod_negative fmod_f32; do
  rm -f "$t.s" "$t.il" "$t.exe"
  JHY_SELF_BACKEND=1 ../../../compiler/build/bin/jhyy.exe compile --target=amd64_win "$t.jhyy" > /dev/null 2>&1
  cp "$t.s" "/path/to/axis-v3/compiler/tests/bootstrap/baseline_v2_self/v2_self_${t}.s"
done
sha256sum v2_self_*.s
```

预期 sha 跟上面一致。如果变化,说明 V2 self-backend 行为已变,需要重新 audit Gate-0
对照逻辑(可能需要重新 baseline,也可能 V3 真修后行为会自动跟着变)。

## Gate-0 [2/4] 比对策略

Byte-equal strict sha 是首选,如果 V3 真修后 sha 一致(完全对照 V2 实现)→ 锁死 sha 严格相等。
如果不一致(预期更可能,因为 V3 emit_conv 在 emit_call.jhyy,V2 emit_conv_* 在 emit_sse.jhyy,
两套实现选择 op coverage 可能微差)→ 降级为助记符序列比对(允许寄存器分配/指令顺序差异,
要求 op coverage 一致)。

Workarounds W-083/W-086 翻 ✅ 的硬证据 = 上面任一比对模式 3/3 PASS + exit code 匹配。
