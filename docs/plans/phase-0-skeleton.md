# Phase 0: 项目骨架 + QBE 工具链验证

> 目标：搭建可编译的开发环境，验证 QBE 工具链端到端可用
> 预计：约 1-2 天
> 前置：无
> 产出：可编译的目录结构 + runtime + 手工 IL → 可执行文件跑通

---

## Step 0.1: 目录结构初始化

创建以下目录树：

```
JiHuiYiYou/
├── CLAUDE.md              # [已存在] 总项目指导
├── PLAN.md                # [待创建] 总体架构概览
├── Makefile               # [待创建] 顶层构建系统
├── .gitignore             # [待创建]
│
├── compiler/              # jhyy 编译器主目录
│   ├── src/               #     Phase 1: C 源码
│   │   ├── main.c         #     CLI 入口
│   │   ├── arena.c
│   │   ├── arena.h
│   │   ├── diagnostics.c
│   │   ├── diagnostics.h
│   │   ├── lexer.c
│   │   ├── lexer.h
│   │   ├── parser.c
│   │   ├── parser.h
│   │   ├── ast.c
│   │   ├── ast.h
│   │   ├── types.c
│   │   ├── types.h
│   │   ├── symtab.c
│   │   ├── symtab.h
│   │   ├── sema.c
│   │   ├── sema.h
│   │   ├── ir.c
│   │   ├── ir.h
│   │   ├── codegen.c
│   │   ├── codegen.h
│   │   ├── util.c
│   │   └── util.h
│   ├── src0/              #     Phase 2: jhyy 自举源码 (.jhyy)
│   ├── runtime/           #     C 运行时，链接到每个 jhyy 程序
│   │   ├── runtime.c
│   │   └── runtime.h
│   ├── lib/               #     jhyy 标准库源码 (.jhyy)
│   ├── tests/             #     测试
│   │   ├── unit/          #        单元测试 (C)
│   │   ├── examples/      #        集成测试 (.jhyy)
│   │   └── bootstrap/     #        自举验证脚本
│   ├── docs/              #     编译器文档
│   │   ├── language.md    #        语言规范
│   │   ├── qbe_mapping.md #        QBE IL 映射参考
│   │   └── plans/          #       各 Phase 计划
│   └── build/             #     构建产物 (gitignored)
│       ├── obj/           #         .o 文件
│       ├── bin/           #         可执行文件
│       ├── il/            #         生成的 .il 文件
│       └── asm/           #         生成的 .s 文件
│
├── ide/                   # jhyy IDE 项目（远期，Phase 4+）
├── os/                    # jhyy OS 项目（远期，Phase 4+）
└── qbe/                   # Vendored QBE 源码
```

### 执行操作

```bash
cd JiHuiYiYou
mkdir -p compiler/src compiler/src0 compiler/runtime compiler/lib
mkdir -p compiler/tests/unit compiler/tests/examples compiler/tests/bootstrap
mkdir -p compiler/docs/plans compiler/build/obj compiler/build/bin compiler/build/il compiler/build/asm
mkdir -p ide os
```

### .gitignore 内容

```
compiler/build/
*.o
*.exe
*.ilk
*.pdb
```

### 验收标准
- [ ] 所有目录已创建
- [ ] .gitignore 已写入

---

## Step 0.2: 获取并编译 QBE

QBE 是一个轻量级编译器后端，源码约 10000 行 C 代码，编译为单个 `qbe` 可执行文件。

### 方案 A: Vendor QBE 源码（推荐）

```bash
cd JiHuiYiYou
git clone git://c9x.me/qbe.git qbe
cd qbe
make
```

成功后在 `qbe/` 目录下生成 `qbe` (Linux) 或 `qbe.exe` (需要适配)。

### 方案 B: MSYS2 下编译 QBE 的注意事项

QBE 原生目标 Linux/amd64，在 MSYS2 下编译可能需要：
- 确认 `gcc` 可用（`which gcc`）
- 可能需要修改 `Makefile` 中的 `CC` 变量
- 如果链接失败，检查 `-static` 标志

### 备选方案: 如果 QBE 编译困难

如果在 Windows 下编译 QBE 遇到阻塞问题，可以：
1. 使用 WSL (Windows Subsystem for Linux)
2. 先在 WSL 中完成整个编译流程，后续再适配原生 Windows

### 验收标准
- [ ] QBE 源码在 `qbe/` 目录下
- [ ] `qbe` 可执行文件可用
- [ ] 运行 `qbe -h` 输出帮助信息

---

## Step 0.3: 编写 runtime.c / runtime.h

这是每个 jhyy 程序链接的运行时库，提供 arena allocator 和启动支持。

### runtime.h 接口

```c
#ifndef RUNTIME_H
#define RUNTIME_H

#include <stdint.h>
#include <stddef.h>

/* Arena allocator */
typedef struct {
    char *start;
    char *cur;
    char *end;
} Arena;

/* Create arena with given capacity. Returns 0 on OOM. */
void arena_new(Arena *a, size_t size);

/* Allocate raw bytes with alignment. Returns 0 on OOM. */
void *arena_alloc(Arena *a, size_t size, size_t align);

/* Reset arena to empty (frees all at once). */
void arena_reset(Arena *a);

/* Destroy arena (free underlying memory). */
void arena_destroy(Arena *a);

/* Program entry — user defines this, runtime calls it. */
extern int main_jhyy(void);

#endif
```

### runtime.c 实现

```c
#include "runtime.h"
#include <stdlib.h>
#include <stdio.h>

void arena_new(Arena *a, size_t size) {
    a->start = (char *)malloc(size);
    if (!a->start) {
        a->cur = a->end = 0;
        return;
    }
    a->cur = a->start;
    a->end = a->start + size;
}

void *arena_alloc(Arena *a, size_t size, size_t align) {
    uintptr_t mask = align - 1;
    char *p = (char *)(((uintptr_t)a->cur + mask) & ~mask);
    if (p + size > a->end) return 0;
    a->cur = p + size;
    return p;
}

void arena_reset(Arena *a) {
    a->cur = a->start;
}

void arena_destroy(Arena *a) {
    free(a->start);
    a->start = a->cur = a->end = 0;
}

/* Default main — links with user's main_jhyy() */
int main(int argc, char **argv) {
    (void)argc;
    (void)argv;
    return main_jhyy();
}
```

### 验收标准
- [ ] `runtime.h` 接口定义完整
- [ ] `runtime.c` 实现 arena_new / arena_alloc / arena_reset / arena_destroy
- [ ] `gcc -c compiler/runtime/runtime.c -o compiler/build/obj/runtime.o` 编译通过

---

## Step 0.4: 手写 QBE IL 验证工具链

在写编译器之前，先手工验证整条工具链是通的。

### 测试程序: `compiler/tests/examples/hello_manual.il`

```qbe
# A simple hello-world style program
# Returns 42 as exit code

export function w $main_jhyy() {
@start
    %x =w copy 42
    ret %x
}
```

### 验证流程

```bash
# Step 1: .il → .s
qbe compiler/tests/examples/hello_manual.il -o compiler/build/asm/hello_manual.s

# Step 2: .s + runtime.c → 可执行文件
gcc compiler/build/asm/hello_manual.s compiler/runtime/runtime.c \
    -o compiler/build/bin/hello_manual.exe

# Step 3: 运行
./compiler/build/bin/hello_manual.exe
echo $?    # 应该输出 42
```

### 第二个测试: 调用 arena

```qbe
# 测试 arena allocator

export function w $main_jhyy() {
@start
    # Arena a; 在栈上分配 24 字节 (3 个 8 字节指针)
    %a =l alloc8 24

    # arena_new(&a, 1024)
    call $arena_new(l %a, l 1024)

    # arena_alloc(&a, 128, 8) → 应返回非空指针
    %p =l call $arena_alloc(l %a, l 128, l 8)

    # 检查: 如果 p == 0 返回 1 (失败), 否则返回 0 (成功)
    %is_null =w ceql %p, 0
    jnz %is_null, @fail, @ok
@fail
    ret 1
@ok
    # arena_destroy(&a)
    call $arena_destroy(l %a)
    ret 0
}
```

### 验收标准
- [ ] `hello_manual.il` 编译 → 运行 → 返回 42
- [ ] arena 测试编译 → 运行 → 返回 0（成功）

---

## Step 0.5: Makefile

顶层 Makefile 提供统一的构建入口。

```makefile
# jhyy project — top-level Makefile
CC       = gcc
CFLAGS   = -std=c11 -Wall -Wextra -g
QBE      = qbe

# Directories
COMPILER_DIR = compiler
SRC_DIR      = $(COMPILER_DIR)/src
RUNTIME_DIR  = $(COMPILER_DIR)/runtime
BUILD_DIR    = $(COMPILER_DIR)/build
OBJ_DIR      = $(BUILD_DIR)/obj
BIN_DIR      = $(BUILD_DIR)/bin
IL_DIR       = $(BUILD_DIR)/il
ASM_DIR      = $(BUILD_DIR)/asm

# Source files (Phase 1)
SRCS = $(SRC_DIR)/main.c \
       $(SRC_DIR)/arena.c \
       $(SRC_DIR)/diagnostics.c \
       $(SRC_DIR)/lexer.c \
       $(SRC_DIR)/parser.c \
       $(SRC_DIR)/ast.c \
       $(SRC_DIR)/types.c \
       $(SRC_DIR)/symtab.c \
       $(SRC_DIR)/sema.c \
       $(SRC_DIR)/ir.c \
       $(SRC_DIR)/codegen.c \
       $(SRC_DIR)/util.c

OBJS = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRCS))
RUNTIME_OBJ = $(OBJ_DIR)/runtime.o

# Targets
.PHONY: all clean test

all: $(BIN_DIR)/jhyy

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/runtime.o: $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(BIN_DIR)/jhyy: $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@

test:
	@echo "Running tests..."
	# TODO: invoke test runner

clean:
	rm -rf $(BUILD_DIR)
```

### 验收标准
- [ ] `make` 在有源文件时能编译
- [ ] `make clean` 清理所有构建产物
- [ ] 目录自动创建（`@mkdir -p`）

---

## Phase 0 完成标准

全部通过后，你拥有：

1. 完整的目录骨架
2. 可用的 QBE 工具链
3. 手工验证过的 IL → ASM → EXE 流程
4. 可用的 runtime 库（arena allocator）
5. Makefile 构建系统

可以进入 Phase 1 开始写编译器本身。
