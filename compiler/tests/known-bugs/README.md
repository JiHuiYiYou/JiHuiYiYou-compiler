# 已知缺陷的复现件（**不在回归套件里**）

> 这个目录放的是**已登记但尚未修复**的缺陷的最小复现程序。
> 它们**故意不进** `compiler/tests/examples/` —— 仓内有一条硬约束：
> **回归套件里不允许存在「预期失败」的用例**（XFAIL 恒为 0），三处同时强制：
>
> | 位置 | 强制方式 |
> |---|---|
> | `scripts/dev/docs_facts_check.py:105` | FACTS.md 回归基线那一行的正则里 XFAIL 计数**写死是 0** |
> | `scripts/dev/check_regress_facts.py:192` | `compare("审计 xfail", xfail, 0)` —— 断言审计的 xfail 桶必须是 0 |
> | `scripts/dev/audit_test_assertions.py` | XFAIL 桶单独统计（用来发现「标记过期」） |
>
> ⇒ **未修的缺陷进台账（`docs/internal/workarounds.md`），不进套件**；
> 修好之后，把复现件搬进 `examples/` 并写成正常的 `EXPECT` / `EXPECT-ERROR` 用例，
> 同时把台账条目的状态翻成 `RESOLVED`（根因修好后要回填 commit，**不要删条目**）。

## 目录内容

**当前是空的** —— 2026-11-21 之前放在这里的 8 份复现件
（**W-229 … W-236**）**全部修好了** ⇒ 已按上面的规矩搬进
`compiler/tests/examples/`，对应台账条目也一并翻成 `RESOLVED`：

| 复现件（现在在 `examples/`） | 台账条目 | 修好前 | 修好后 |
|---|---|---|---|
| `w229_fn_value_crash.jhyy` | W-229 | 编译器 **codegen 崩**（`unknown QBE IL mnemonic`），产物运行时爆栈 | 编译期报一条干净的「函数值未实装」错误 |
| `w230_null_stack_arg.jhyy` | W-230 | 退出码 **1**（栈位置实参传 `null` ⇒ callee 收到带残渣的指针） | 退出码 **0** |
| `w231_struct_lit_null_field.jhyy` | W-231 | 编译期报 `field type mismatch` | 编译通过 |
| `w232_topconst_scalar_msg.jhyy` | W-232 | 编译期报 `expected [ for const array init, got int` | 编译期报「顶层 const 只支持数组」 |
| `w233_string_literal_slice_len.jhyy` | W-233 | **编译过了，但切片的 len=0** ⇒ `len(s)` 得 0、`s[0]` **访问违例** | 转换带上长度（或明确拒绝这个转换） |
| `w234_const_array_as_elem.jhyy` | W-234 | **编译过了、不报错**，但带 `as` 的元素**读出 0** | 带 `as` 的元素也求值（或给诊断） |
| `w235_narrow_local.jhyy` | W-235 | **编译过了、不报错**，但窄类型**局部变量**既不截断也不回绕 | 局部变量也按窄类型算（回绕 + 截断） |
| `w236_call_arity_not_checked.jhyy` | W-236 | **编译过了、不报错**，但**实参个数**不对时参数**全是垃圾** | 个数不对就编译期报错 |

⇒ **下一条缺陷进来时**：复现件放这个目录 + 台账登记（`docs/internal/workarounds.md`）
⇒ 修好后搬进 `examples/` 并把台账条目翻成 `RESOLVED`。

## 怎么跑（目录里有文件时）

```bash
# 编译 + 跑（退出码 / stdout 就是「现状」）
python -m jhyy_regress --tests=... # 不行 —— 它们不在套件里
# 直接用编译器：
compiler/build/bin/jhyy.exe compile compiler/tests/known-bugs/w230_null_stack_arg.jhyy -o /tmp/w230.exe
/tmp/w230.exe; echo "exit=$?"
```

⇒ 每个复现件的头部注释里写明了「现状是什么、修好后是什么」，
断言（`EXPECT` / `EXPECT-ERROR`）也写在注释里 —— 搬进 `examples/` 时直接生效。
