# 测试

> 集成测试清单 + 运行方法。详细每条 .jhyy 的预期值见 `compiler/tests/examples/`。
>
> **Last updated**: 2026-10-15 — `regress.py` = **173/173 PASS(全部有断言)+ 5 XFAIL + 19 SKIP**
> (197 total,连跑两次一致)。Stage 2 closure sha `da78987c`。
>
> **注意 total 从 185 变成 197**:harness 原来用 `os.listdir`(不递归),
> `arena_test/` / `hello-freestanding/` / `multi_file/` / `namespace/` 四个子目录
> 共 12 个 .jhyy **从来没进过全量回归**。已改 rglob。

## ⚠️ 引用「N/N PASS」之前先读这一段

**PASS 的强度取决于测试有没有断言,不取决于它跑没跑。**

`mcp-jhyy/jhyy_regress.py` 的 `run_test()`(约 140-275 行)只有四种判据:

| 源文件里的指令 | 实际验了什么 |
|---|---|
| `// EXPECT: 42` | 进程退出码 == 42 —— **真断言**(前提:见下第 2 条) |
| `// XFAIL: <原因>` | **真跑,应该失败**。失败记 XFAIL(预期内);**通过记 XPASS 并让 suite 失败** |
| `// EXPECT-OUT: "substr"` | **stdout 含该子串**(2026-10-15 新增)。只比 stdout 不比 stderr —— 混进诊断信息会造成假通过 |
| `// EXPECT-ERROR: "kw"` | 编译必须失败且 stderr 含该子串 |
| `// SKIP: reason` | 跳过 |
| **什么都不写** | **只要进程没崩就 PASS**(`expected is None` 分支只查 NTSTATUS) |

两个必须知道的事实:

1. **此前 stdout 从头到尾不被比较。** `output` 被捕获后只用于显示。测试打印一堆
   值而 `main_jhyy` 直接 `return 常量`,那堆输出就是摆设 —— `float_cmp.jhyy` 靠
   这个活到了今天。现已加 `// EXPECT-OUT:` 让输出能参与判定。
2. **有 `// EXPECT:` 也不等于有断言。** 若 `main_jhyy` 的返回值(显式 `return`
   或隐式末句)是字面量,且与 EXPECT 值相同,这条断言**在数学上不可能失败**。

## 断言强度审计

```bash
python scripts/dev/audit_test_assertions.py           # 报告
python scripts/dev/audit_test_assertions.py --strict   # 有违规 exit 1(挂 CI 用)
```

它机械分类每个测试,**不靠「有没有 EXPECT 指令」判断** —— 那样会被
`generics_enum.jhyy` 骗过(它有 `//EXPECT:42` 而 main 是字面 `return 42`)。
判据是「`main_jhyy` 的返回值是否从被测表达式推导」。

2026-10-15 终值(197 个 `.jhyy`,可跑 173):

| 分类 | 数量 | 实际验了什么 |
|---|---|---|
| **真断言**(`real` + `out-asserted`) | **160** | 结果正确 |
| `literal-return-ok` | 7 | 合理例外:`exit_zero_extend_*` + `hello`,被测对象就是退出码 |
| `expect-error` | 6 | 编译必须失败且 stderr 含关键字 |
| `skipped` | 10 | `// SKIP:` |
| `library` | 14 | 无 `fn main_jhyy` |

**零信号合计 0。** 曾是 54(43 个只验没崩 + 11 个有 EXPECT 但不可能失败),
2026-10-15 全部改成真断言。

regress 汇总行现在**只计有断言的**:

```
===== 173/173 passed (全部有断言), 0 failed, 19 skipped (of 197 total) =====
  ├─ NOASSERT 0  无断言,只验了「进程没崩」
  ├─ VACUOUS  0  有 EXPECT 但断言在数学上不可能失败
  ├─ XFAIL    5  预期内失败(已知 bug,真跑了)
```

**19 个 SKIP 的构成:** 14 个 library(无 `fn main_jhyy`)+ 5 个 sysv
(需 Linux)。

### sysv 那 5 个:启了 Docker 就能跑,而且立刻挂了一个

```bash
bash compiler/tests/bootstrap/sysv_full_regress.sh --runs=1
```

2026-10-15 实测 **4/5 PASS,1 FAIL**:`sysv_abi_test` 退出 22,期望 28。
逐位探针定位到根因 —— SysV callee 的参数溢出只处理 4 个整数寄存器,
第 5/6/7 个实参全部读到第 4 个的值(`%r8d`/`%r9d`/栈参数从未被读),
登记 **W-116**。

**这个门从 v2.7.0 就存在**,而验它的测试从 v2.7.0 起就标着「sysv target
requires Linux host」—— 在没装 Docker 的开发机上它**永远不会被跑到**。
这也是为什么 W-104(SysV 借 Win 分类器)能一直活着:同一个根,同一个位置。

**注意 Windows 上装了 Docker 也要手动启动 Docker Desktop** —— daemon
没起来时 `docker info` 不响应,regress 的 `--cross=auto` 会静默降级成 SKIP,
不会有任何提示。

**5 个 XFAIL** —— 全部对应一条已登记的 ACTIVE workaround,**真跑、真失败、
出现在每次回归输出里**:

| 测试 | 对应 |
|---|---|
| `float_cmp.jhyy` | W-109 浮点比较 |
| `generics_enum.jhyy` | W-111 泛型 enum SEGV |
| `gdb_pretty_test.jhyy` | W-114 enum match 恒取第一支 |
| `codegen_call_return_types.jhyy` | W-115 W-089 reproducer 仍 STACK_OVERFLOW |
| `borrow_check_err.jhyy` | chained `&&T` 在 parser 阶段就挂,不是 sema |

### 为什么是 XFAIL 而不是 SKIP

SKIP 是**不跑**,所以 bug 哪天被修好了它也不会吭声,标记永久失真。
XFAIL **真跑**:失败算预期,但**通过就算 XPASS 并让 suite 失败** ——
「修好了必须有人看见」是 SKIP 给不了的。

XPASS 上线当场就抓到一个过期标记:`generics_enum` 报了 XPASS,因为它其实
**没在用**那个泛型 enum(声明了但 main 从不引用),编译通过、返回 42、
PASS 了 —— 标记是假的。改成真的用上之后才成为有效的 XFAIL。

NOASSERT / VACUOUS **不是 PASS** —— 它们仍会跑(能抓编译器崩溃),但验证不了
任何计算结果。以前这两类和 PASS 在汇总行里长得一模一样,「163/163 全绿」这句话
因此不携带信息;现在不需要额外解释了。

> **这一轮补断言挖出 3 个真 bug**(W-112 / W-113 / W-114),全部是「测试名字
> 覆盖了功能,测试内容没有」:
> - `link_section_boot` —— `#[link_section]` 是 no-op,ship gate 一直空转
> - `inline_asm_cpuid` / `memory_barrier_smp` —— asm 字节被 emit 到 `ret` 之后,
>   退出码对 asm 内容零敏感
> - `gdb_pretty_test` —— 全 unit-variant 的 enum `match` 永远命中第一支
>
> 以及 `float_cmp` 挖出 W-109/W-110、`generics_enum` 挖出 W-111。
> **补断言的投产比远高于读代码找 bug。**

> **判据扫描踩过的坑(记下来免得再犯):**
> 1. 「有没有 EXPECT 指令」当判据 —— 会被 `generics_enum`(有 `//EXPECT:42`
>    而 main 是字面 `return 42`)骗过。判据必须是「返回值是否从被测表达式推导」。
> 2. 「所有 return 都是字面量」当判据 —— 会把 `return 1..9` 不同失败分支返不同
>    常量的**真断言**误判成违规。**分类器自己的假阳性比没有分类器更糟。**
> 3. 指令扫描扫全文 —— **文档里提到一个指令就会凭空生成一条断言**(实测踩过)。
>    现在只认「该行第一个不在字符串里的 `//` 之后以指令关键字开头」,
>    整行注释与行尾注释都支持。

## 集成测试位置

`compiler/tests/examples/*.jhyy`（主目录 + 子目录 `multi_file/` / `namespace/` / `arena_test/`）。

回归脚本是**仓库根目录**的 `regress.py`(不是 `compiler/build/bin/`,仓库根
relocation 之后的路径),自动跑所有有 `main_jhyy` 的 .jhyy
(`jhyy_regress.py:371` 目录扫描,不是手工枚举):

```
python regress.py                       # 全量
python regress.py --tests=foo.jhyy      # 单测(必须带 .jhyy 后缀)
python regress.py --binary=jhyy_v2.exe  # 用 self-hosted 编译器跑
```

> ⚠️ `--tests=` **必须带 `.jhyy` 后缀**。不带时 harness 不补后缀,直接
> `FileNotFoundError` 崩在 runner 里,不是干净报错。

---

## 经典测试（v0.0.1–v0.2.1）

| 测试 | 预期 | 验证内容 |
|------|------|---------|
| `hello.jhyy` | EXIT:42 | 基础流水线 |
| `demo.jhyy` | EXIT:0 | 全部 v0.0.1 特性 |
| `pointer.jhyy` | EXIT:100 | `&x`, `*p = val` |
| `struct.jhyy` | EXIT:30 | struct 定义+字面量+字段访问 |
| `match.jhyy` | EXIT:20 | match 字面量+通配符 |
| `forloop.jhyy` | EXIT:10 | for 循环 (0+0+1+2+3+4) |
| `helloworld.jhyy` | stdout: "Hello, world!" | 控制台输出 |
| `chinese.jhyy` | stdout: "你好，世界！" | UTF-8 中文输出 |
| `print_num.jhyy` | stdout: "计算结果: 42" | printf 数字输出 |
| `return_type.jhyy` | EXIT:100 | return 类型检查 + printf |
| `logical.jhyy` | EXIT:0 | && / \|\| 短路求值 |
| `import_test.jhyy` | EXIT:72 | import 模块系统 |
| `dungeon_game.jhyy` | EXIT:0 | 综合 demo |

## v0.3 专项（数组 + bug 修复）

- `array_test.jhyy` — `[T; N]` 字面量/下标/赋值
- `bug1_ptr_bin.jhyy` — Bug 1 回归
- `bug2_if_phi.jhyy` — Bug 2 回归
- `bug3_void_if.jhyy` / `bug3_void_exact.jhyy` — Bug 3 回归
- `float_test.jhyy` — 浮点字面量

## v0.4 专项（struct pass-by-value + 多文件 + FFI）

- `struct_val_pass.jhyy` — struct 作为函数参数
- `struct_val_ret.jhyy` — 函数返回 struct
- `struct_val_assign.jhyy` — struct 赋值
- `multi_file/main.jhyy` + `lib_a.jhyy` + `lib_b.jhyy` + `lib_c.jhyy` — 传递性 import
- `ffi_multi.jhyy` — 3+ 参数 FFI
- `ffi_file.jhyy` — 文件 I/O

## v0.5 专项（浮点算术 + break/continue + 类型转换）

- `break_continue.jhyy` — while/for break/continue
- `float_arith.jhyy` / `float_arith_f32.jhyy` — 浮点 `+ - * /`
- `void_if.jhyy` — void 分支
- `nested_if.jhyy` — 嵌套 if/else
- `overflow.jhyy` — i32 二补码环绕
- `fib30.jhyy` — 递归压力
- `big_array.jhyy` — 大数组
- `big_test.jhyy` — 综合压力
- `ptr_self_assign.jhyy` — 指针自赋值

## v0.6 专项（切片 + 命名空间 + `as` 指针）

- `slice_literal.jhyy` — 切片字面量
- `slice_index.jhyy` — 切片下标
- `slice_subrange.jhyy` — 切片子范围
- `slice_len.jhyy` — 切片长度
- `array_to_slice.jhyy` — 数组 → 切片 decay
- `slice_iterate.jhyy` — 切片遍历
- `namespace/main.jhyy` + `mod_a.jhyy` + `mod_b.jhyy` — `mod::fn()` 命名空间
- `namespace_dup.jhyy` + `ns_dup_a.jhyy` + `ns_dup_b.jhyy` — 同名函数跨模块
- `cast_ptr_to_int.jhyy` — `*T ↔ i64` 互转
- `arena_test/arena_test.jhyy` + `arena.jhyy` — Stage 0 自举验证

## 库文件（SKIP，不计入 passed/failed）

- `mylib.jhyy`
- `multi_file/lib_a.jhyy`, `lib_b.jhyy`, `lib_c.jhyy`
- `namespace/mod_a.jhyy`, `mod_b.jhyy`
- `ns_dup_a.jhyy`, `ns_dup_b.jhyy`
- `arena_test/arena.jhyy`

无 `fn main_jhyy` → 回归脚本自动 SKIP。

---

## 运行方法

### 全量回归

```bash
python regress.py          # 仓库根目录,不是 compiler/build/bin/
```

当前输出:
```
===== 173/173 passed (全部有断言), 0 failed, 19 skipped (of 197 total) =====
  ├─ NOASSERT 0 / VACUOUS 0 / XFAIL 5
```

baseline 历史:
- v0.6 — 50/53 PASS + 3 SKIP
- v1.0.0 — 50/53 PASS + 3 SKIP(自举 parity)
- v1.7.3 — 96/96 PASS + 10 SKIP(106 total)
- v1.8.3 — 102/102 PASS + 4 SKIP(106 total)
- v2.0.0 → v2.4.0 — 104/104 PASS + 4 SKIP(108 total)
- **v4.0.8 — 173/173 PASS + 5 XFAIL + 19 SKIP(197 total)** ← 当前(2026-10-15 实测)

⚠️ 数量涨了不代表覆盖变强。**断言强度**和**失败模式覆盖**是两个轴:
前者今天清零了(零信号 54 → 0),后者仍然低 —— 13 条 ACTIVE 里只有 5 条有
「活的、能失败的测试」,其余的失败模式根本没有测试触及。一个没有测试的 bug,
对回归套件而言在定义上就是不可见的。**计数不是覆盖率的度量。**

### 单个测试

```bash
./compiler/build/bin/jhyy.exe compile compiler/tests/examples/hello.jhyy -o hello
./hello.exe; echo $?     # 期望 42
```

### 单元测试（不常用）

```bash
# 单文件单元测试（独立编译运行）
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_lexer.c compiler/src/lexer.c compiler/src/arena.c \
    -o compiler/build/bin/test_lexer.exe -I compiler/src && \
    ./compiler/build/bin/test_lexer.exe

# test_sprint1b 需要链接多个模块
/c/msys64/ucrt64/bin/gcc.exe -std=c11 -Wall -Wextra \
    compiler/tests/unit/test_sprint1b.c \
    compiler/src/arena.c compiler/src/types.c compiler/src/symtab.c compiler/src/ast.c \
    -o compiler/build/bin/test_sprint1b.exe -I compiler/src && \
    ./compiler/build/bin/test_sprint1b.exe
```
