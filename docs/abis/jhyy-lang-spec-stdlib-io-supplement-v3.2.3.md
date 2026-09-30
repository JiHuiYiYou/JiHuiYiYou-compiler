# stdlib IO/OS Supplement (v3.2.3)

> 锁定于 v3.2.3 (3l.2, std lib IO/OS M0)。 后续 v3.2.4+ 增量补 append。

## 1. 模块清单

`compiler/src0/std/` 新增 2 个 M0 std lib 模块(本 sprint):

| 模块 | 文件 | 行数 | 公开 API |
|------|------|------|----------|
| `std::io` | `compiler/src0/std/io.jhyy` | ~106 | `std_io_open / std_io_close / std_io_read / std_io_write / std_io_print / std_io_print_err / std_io_eprint` |
| `std::os` | `compiler/src0/std/os.jhyy` | ~155 | `std_os_open / std_os_close / std_os_read / std_os_write / std_os_exit / std_os_getenv / OS_O_RDONLY / OS_O_WRONLY / OS_O_RDWR / OS_O_CREAT / OS_O_TRUNC / OS_O_APPEND / OS_MODE_RW_R` |

## 2. 设计约束 (M0)

- **不依赖 closure / generic / 借用** — M0 简化,后续 sprint 加
- **不跨模块 import** — `inline_imports` (main.jhyy:456-559) 只支持 `main_dir/mod_name.jhyy`,不支持 subdir (`std/*`); 每个 std 模块自给自足
- **不依赖 std::mem / std::string** — 跟 v3.2.2 ship 的 4 个 std 模块完全独立,避免 cross-module import 失败(W-077 根因)
- **`std_io_*` / `std_os_*` 前缀** — per W-076 + W-079 pattern,所有函数名加前缀避免跟 runtime.c C-side 符号冲突
- **M0 Phase 1 std_os stub** — `std_os_open / close / read / write / exit` 是 stub (verify args + return success/-1 based on input validation)。 等 W-079 (QBE amd64_win mixed extern args) 真修后,接 libc POSIX 实现

## 3. std::io 公开 API 详细

### 3.1 File handle API(基于 libc fopen / fclose / fread / fwrite)

```jhyy
fn std_io_open(path: *u8, mode: *u8) -> *u8        // 打开文件;mode cstr ("r" / "w" / "wb" 等);返 FILE* / 0 on fail
fn std_io_close(f: *u8) -> i32                     // 关闭文件;f==0 → -1;返 0 ok / -1 fail
fn std_io_read(f: *u8, buf: *u8, n: i64) -> i64    // 从 f 读 n 字节到 buf;f==0 → -1; n<=0 → 0;返实际读字节数 (< n 表示 EOF / error)
fn std_io_write(f: *u8, buf: *u8, n: i64) -> i64   // 写 n 字节从 buf 到 f;f==0 → -1; n<=0 → 0;返实际写字节数
```

**FFI**: extern 调 libc `fopen / fclose / fread / fwrite`(QBE amd64_win extern args 已知 OK pattern — pointer return + 同 type args 1:1 match)。

### 3.2 stdio print API(M0 stub)

```jhyy
fn std_io_print(s: *u8) -> i32         // stdout 写 cstr;M0 stub 返 0
fn std_io_print_err(s: *u8) -> i32     // stderr 写 cstr;M0 stub 返 0
fn std_io_eprint(s: *u8) -> i32        // 别名 = std_io_print_err
```

**M0 限制**:`std_io_print / std_io_print_err / std_io_eprint` 是 stub,**不实际写 stdout/stderr**(返 0)。原因:jhyy 拿不到 stderr/stdout `FILE*` 常量地址(`FILE*` 是 libc runtime 内部静态变量)。 Phase 2+ 接 libc `fputs(stdout)` / `fputs(stderr)` 需走 C-side 静态变量 getter(`jh_stdout_get / jh_stderr_get`),per v3.x mid plan。

**当前 usage pattern**:user 测试走 `std_io_open("stdout.txt") + std_io_write` 模式,把 stdout 当文件写入(避免依赖 libc FILE* 常量)。 这样 std lib 跟 stdout 解耦,future OS kernel M11 launch 时换 syscall 实现(写 com1 / serial port 直接)只改 std_io module,test 不变。

### 3.3 错误语义

| 调用 | 错误返回 |
|------|----------|
| `std_io_open` | `0 as *u8` (libc fopen 失败语义) |
| `std_io_close(f)` | `f == 0` → `-1`;否则 libc fclose 返回值 |
| `std_io_read(f, buf, n)` | `f == 0` → `-1`; `n <= 0` → `0`;否则 libc fread 返回值 |
| `std_io_write(f, buf, n)` | `f == 0` → `-1`; `n <= 0` → `0`;否则 libc fwrite 返回值 |

## 4. std::os 公开 API 详细

### 4.1 POSIX open flag / mode 常量

```jhyy
fn OS_O_RDONLY() -> i32 { return 0 as i32; }       // 0
fn OS_O_WRONLY() -> i32 { return 1 as i32; }       // 1
fn OS_O_RDWR()   -> i32 { return 2 as i32; }       // 2
fn OS_O_CREAT()  -> i32 { return 64 as i32; }      // 0x40
fn OS_O_TRUNC()  -> i32 { return 512 as i32; }     // 0x200
fn OS_O_APPEND() -> i32 { return 1024 as i32; }    // 0x400
fn OS_MODE_RW_R() -> i32 { return 420 as i32; }    // 0644 (owner-only rw / group r / other r)
```

### 4.2 File descriptor API(M0 stub — see W-079)

```jhyy
fn std_os_open(path: *u8, flags: i32, mode: i32) -> i64   // 打开文件;返 fd (i64) / -1 on fail
fn std_os_close(fd: i64) -> i32                           // 关闭 fd;返 0 ok / -1 fail
fn std_os_read(fd: i64, buf: *u8, n: i64) -> i64          // 从 fd 读 n 字节;返实际读字节数 / -1
fn std_os_write(fd: i64, buf: *u8, n: i64) -> i64         // 写 n 字节到 fd;返实际写字节数 / -1
```

**M0 stub 行为**(per W-079 workaround,Phase 2+ 接 libc POSIX):

| 调用 | M0 stub 行为 | Phase 2+ 预期行为 |
|------|--------------|-------------------|
| `std_os_open(path, flags, mode)` | `path==0` → `-1`;`flags<0` → `-1`;`mode<0` → `-1`;`mode>0777` → `-1`;否则返 `42 as i64`(模拟 fd) | libc `open(path, flags, mode)` 返 fd / -1 |
| `std_os_close(fd)` | `fd<0` → `-1`;否则返 `0`(模拟成功) | libc `close(fd)` 返 0 / -1 |
| `std_os_read(fd, buf, n)` | `fd<0` → `-1`;`buf==0` → `-1`;`n<=0` → `0`;否则返 `n`(模拟读到 n 字节) | libc `read(fd, buf, n)` 返字节数 / -1 |
| `std_os_write(fd, buf, n)` | `fd<0` → `-1`;`buf==0` → `-1`;`n<=0` → `0`;否则返 `n`(模拟写 n 字节) | libc `write(fd, buf, n)` 返字节数 / -1 |

### 4.3 Process API

```jhyy
fn std_os_exit(code: i32)                              // 终止进程;never returns
```

**M0 stub 行为**:**不**调 libc `exit()`,设置 `let _ignore = code` 后 return。 原因: M0 避免 QBE bug 触发现实进程退出(W-079 同样根因)。 Phase 2+ 接 libc `exit(code)`。

### 4.4 Environment API(jh_getenv extern — verified work)

```jhyy
fn std_os_getenv(name: *u8) -> *u8                     // 读环境变量;返 env value cstr / 0 on miss
```

**FFI**: extern 调 `jh_getenv`(jhyy_helpers.c v2.5.0) — pointer return → QBE amd64_win 已知 OK pattern(W-079 绕路,1-arg + pointer return 不触发 mixed-args bug)。

### 4.5 错误语义(M0 stub → Phase 2+ 真实)

| 调用 | M0 stub 返回 | Phase 2+ 预期返回 |
|------|--------------|-------------------|
| `std_os_open(path, flags, mode)` | `-1` (EINVAL / 验证失败) / `42` (模拟成功) | libc `open` 返 fd / `-1` (errno) |
| `std_os_close(fd)` | `-1` (fd < 0) / `0` (模拟成功) | libc `close` 返 0 / `-1` (errno) |
| `std_os_read(fd, buf, n)` | `-1` (EINVAL) / `0` (n<=0) / `n` (模拟) | libc `read` 返字节数 / `-1` (errno) |
| `std_os_write(fd, buf, n)` | `-1` (EINVAL) / `0` (n<=0) / `n` (模拟) | libc `write` 返字节数 / `-1` (errno) |
| `std_os_exit(code)` | 不退出 (return) | libc `exit(code)` (never returns) |
| `std_os_getenv(name)` | `0` (env miss) / `*u8` (env value cstr) | 同(已接 jh_getenv) |

## 5. 已知限制 / W-XXX

- **W-079**: QBE amd64_win mixed (l, w, w) extern fn args bug + i32 return zero-extension missing。
  - **症状1**: extern fn 调 (l path, w flags, w mode) 三参数混合类型时,QBE 不 emit 完整 arg register 装载 → extern fn 拿 uninitialized registers → 行为未定义。
  - **症状2**: main_jhyy 末尾 `return std_io_close(...)` / `return std_os_open(...)` 等 i32 from extern i32 result 时,QBE 不 emit `movl %eax, %eax` zero-extend → bash exit code 拿 garbage upper bits。
  - **触发面**: external fn calls with mixed-type args OR main returning i32 from extern i32 result。
  - **workaround (M0)**:
    - `std_io_*` 走 single-type-pointer externs(`fopen / fclose / fread / fwrite`, pointer return + 同 type args,已知 OK pattern)— 已验证 PASS
    - `std_os_*` 走 M0 stubs(input validation + return success/-1),不真调 libc
    - `std_os_getenv` 走 1-arg pointer-return pattern(`jh_getenv`),已验证 PASS
  - **status**: ⏳ DEFER(per user 2026-09-26 决定)。 真修路径:QBE zero-extend 修 + std_io_print / print_err 走 C-side `jh_stdout_get / jh_stderr_get` getters。 推到 v3.x mid sprint。

## 6. 测试覆盖

`compiler/tests/examples/std_*.jhyy` 2 个新 test files:

| 模块 | 测试数 | 文件 |
|------|------|------|
| std::io | 5 sub-test(open/write/read/close roundtrip + reopen-existing) | `std_io_basic.jhyy` |
| std::os | 5 sub-test(getenv PATH / getenv missing / exit stub / open fd stub / read write stub roundtrip) | `std_os_basic.jhyy` |

每个 test inline 副本实现待测 fn 后调用验证 EXPECT 注释给出预期 exit code。

## 7. OS 启动链路位置(per v2.0.0-os-prep.md)

- **M11 launch 硬前置**(per `v2.0.0-os-prep.md § 1` M11):v3.2.0..v3.2.5 全 ship — **v3.2.3 ship 后, 3l.2 完成, 剩余 3l.3 vec/map (v3.2.4) + 3l.4 (v3.2.5)**
- **jhyy_OS kernel boot 用 `std/os.jhyy` 系统调用包装** — open / read / write / exit / getenv 5 个 fn 全部 ship (W-079 stub 不阻塞 M11 boot,因为 OS kernel 端会重新实现 std_os_* 路径接 syscall,不依赖 jhyy-side libc 调用)

## 8. Cross-ref

- L2 设计:`docs/plans/v3/v3.2.3-plan.md`
- 上游:`docs/abis/jhyy-lang-spec-stdlib-supplement-v3.2.2.md`(3l.1 mem/fmt/string/arena)
- 下游:`docs/plans/v3/v3.2.4-plan.md`(3l.3 vec/map — 依赖 closure + 3l.1 string/arena)
- Workarounds:W-079 (QBE amd64_win mixed extern + zero-extend, deferred)
- changelog:`docs/logs/v3/changelog-v3.2.md` v3.2.3 umbrella section
