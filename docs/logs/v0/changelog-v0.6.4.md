# JHYY v0.6.4 Changelog

> **状态**: ✅ patch 已发 (`4ac1878`, 2026-07 中旬)
> **承接**: v0.6.3 之后, sprint 2 phase-2 自举翻译实测沉淀的修复
> **后续**: v0.6.5 (sema 严格化 #2 let mut dead-code)

## 版本目标

**单点修复**: parser.c `prefix_string` arena_strdup, 修 #10 imported string literal dangle。

sprint 2 v1.x 自举翻译 driver.jhyy / main.jhyy 时, parser `prefix_string` 把 imported string literal 直接用 `strdup` / raw pointer 指向 input buffer, 但 lexer 的 input buffer 在 parser 退出后就被释放 (`read_file` 后的 bump arena 生命周期结束), 留下 dangle pointer 指向 free 内存。后续 codegen / runtime 用到这些 string literal 时 (例如 `extern fn printf` 的 format 串、function name mangle 字符串) 读到 garbage → 行为随机错。

**修法**: `parser.c` `prefix_string` 改用 `arena_strdup(arena, ...)` —— 拷贝进 compiler 自身长生命周期 arena, parser 退出后仍存活。

---

## 修复详情

### parser: prefix_string arena_strdup (修 #10 imported string literal dangle)

**改动**: `compiler/src/parser.c:615-620` 附近, `prefix_string` 函数

```c
// 前: 直接返回 input buffer 内的指针
const char *prefix_string(...) {
    ...
    return &input_buffer[start_offset];   // DANGLE: input_buffer 释放后失效
}

// 后: 拷贝进 compiler 长生命周期 arena
const char *prefix_string(...) {
    ...
    const char *result = arena_strdup(ctx->arena, &input_buffer[start_offset], len);
    return result;
}
```

**根因**:
- `read_file` 把整个 input file 读进一个 temporary buffer (parser 局部 arena)
- parser `prefix_string` 直接返回该 buffer 内的指针
- parser 退出时 temporary buffer 释放 → 指针 dangle
- codegen 后期用到这些 string (printf format 串 / mangle 后函数名 / external symbol 引用) 读到 free'd 内存

**触发场景**:
- 任何 `extern fn` 调用的字符串字面量 (printf 的 format 串)
- 任何模块 mangle 后字符串 (`$mod__name`)
- 任何跨越多文件 import 链的 string literal

sprint 2 commit 3c 翻译 main.jhyy 时实测命中: jhyy_0 编 main.jhyy → jhyy_1 跑 hello.jhyy 时 stdout 输出 garbage (因为 printf format 串从 free'd 内存读)。

**测试**:
- 现有 regress.py 44/47 全过 (修了一个 hidden bug)
- sprint 2 commit 3c 翻译 driver.jhyy 后 hello.jhyy 跑 stdout 正常输出 "Hello, world!" (vs 之前 garbage)

---

## 验证

1. `python compiler/build/bin/regress.py` → **44/47 passed, 0 failed, 3 skipped**
2. sprint 2 commit 3c 翻译 driver.jhyy → jhyy_1 编 hello.jhyy → 跑 stdout 正常
3. v0.6.4 二进制编 jhyy 编 driver.jhyy 跑通 EXIT=42 (跟 v0.6.3 行为一致)

---

## 不在 v0.6.4 范围 (明确延后)

| 项 | 延后到 | 理由 |
|---|---|---|
| `#2` let mut dead-code | v0.6.5 patch | sema 严格化更干净 |
| `#5` nested struct QBE 'w' load 对齐 | v1.0.0 后 | jhyy 端用平铺 6 字段 workaround |
| `#6` qbe_type_of(i8) → 'b' | v1.0.0 后 | jhyy 端用 `*i32 + shift+mask` workaround |
| `#9` f64/f32 比较 + coercion | **v0.6.3 已 fix** | `git log -S "ceqw"` |
| `#11`+ 自举过程发现 bug 11/12/13 | v0.8 wip commit 1 | 见 `changelog-v0.8.0.md` |

---

## 兼容性

- **行为兼容**: 修了一个隐藏 bug (之前行为错, 现在行为对), .exe 行为在正确用例下完全一致
- **ABI 兼容**: 纯 parser 内部改动, .il / .s / .exe 输出形式不变
- **lang-spec 兼容**: spec v1.0.0 实现补强, 不改 spec. spec 附录 B 可把 #10 移到"已修复"

---

## 改动文件

- `compiler/src/parser.c` (`prefix_string` 改用 arena_strdup)
- `docs/logs/v0/changelog-v0.6.4.md` (本文档)
- `compiler/build/bin/jhyy.exe` (重新编译)

---

## 提交

- commit: `4ac1878 v0.6.4 patch: prefix_string arena_strdup（修 #10 imported string dangle）`
- 紧接 v0.6.3 commit 之后, 2026-07 中旬