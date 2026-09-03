# jhyy project — top-level Makefile
# v1.4.4: 改用 stage-0 链 — `all` 先产 jhyy_stage0.exe (C 端), 再用 stage-0
# 编译 src0/main.jhyy → jhyy.exe (jhyy-side 产物)。jhyy.exe 是 production
# binary, jhyy_stage0.exe 只用于 bootstrap (改 compiler/src/*.c 后重建)。

CC       = gcc
CFLAGS   = -std=c11 -Wall -Wextra -g -I$(SRC_DIR)
QBE      = qbe/qbe.exe
QBEFLAGS = -t amd64_win
WINDRES  = windres

# Directories
COMPILER_DIR = compiler
SRC_DIR      = $(COMPILER_DIR)/src
SRC0_DIR     = $(COMPILER_DIR)/src0
RUNTIME_DIR  = $(COMPILER_DIR)/runtime
BUILD_DIR    = $(COMPILER_DIR)/build
OBJ_DIR      = $(BUILD_DIR)/obj
BIN_DIR      = $(BUILD_DIR)/bin

# v1.8.1 patch: branded "J" icon embedded into jhyy_stage0.exe (and via main.c
# system() spawn, into jhyy.exe + every .jhyy-compiled program).
ICON_SRC = installer/assets/icons/jhyy-icon.ico
RES_OBJ  = $(OBJ_DIR)/jhyy-res.o

# Source files
SRCS = $(SRC_DIR)/main.c \
       $(SRC_DIR)/arena.c \
       $(SRC_DIR)/lexer.c \
       $(SRC_DIR)/parser.c \
       $(SRC_DIR)/ast.c \
       $(SRC_DIR)/types.c \
       $(SRC_DIR)/symtab.c \
       $(SRC_DIR)/sema.c \
       $(SRC_DIR)/ir.c \
       $(SRC_DIR)/codegen.c \
       $(SRC_DIR)/target/target_dispatch.c \
       $(SRC_DIR)/target/abi_amd64_win.c

OBJS = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRCS))
RUNTIME_OBJ = $(OBJ_DIR)/runtime.o

# v1.4.4: 4 个 binary 共存
#   jhyy_stage0.exe — C 端 (stage-0 bootstrap, only needed after src/ change)
#   jhyy.exe        — jhyy-side 产物 (production binary, what users invoke)
#   jhyy.exe.exe    — jhyy.exe 的 baseline (per feedback_regress_baseline_binary_hash)
#   jhyy_v1.exe.exe — v1.0.0 historical baseline (regress_v1.py 用, 不可退役)

.PHONY: all clean test stage0 selfhost

all: $(BIN_DIR)/jhyy.exe

# Stage 0: gcc 产 jhyy_stage0.exe (C 端 bootstrap)
stage0: $(BIN_DIR)/jhyy_stage0.exe

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/runtime.o: $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -c $< -o $@

# v1.8.1 patch: windres rule producing icon resource .o (RT_ICON group).
$(RES_OBJ): $(SRC_DIR)/jhyy.rc $(ICON_SRC)
	@mkdir -p $(OBJ_DIR)
	$(WINDRES) -i $< -O coff -o $@

# v1.4.4: C 端产物改名 jhyy_stage0.exe (runtime.o 不链入 — 它是给 jhyy.exe 用
# 的, 含重复符号 arena_alloc/main, 会跟 main.c/arena.c 冲突)
# v1.8.1: jhyy-res.o (icon RT_ICON group) 链入 stage0,branded "J" 进 exe。
$(BIN_DIR)/jhyy_stage0.exe: $(OBJS) $(RES_OBJ)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@

# v1.4.4: jhyy.exe 由 jhyy_stage0.exe 编 src0/main.jhyy 产
# 依赖 stage0 (jhyy_stage0.exe 必须先存在)
$(BIN_DIR)/jhyy.exe: $(SRC0_DIR)/main.jhyy $(SRC0_DIR)/*.jhyy $(BIN_DIR)/jhyy_stage0.exe
	@mkdir -p $(BIN_DIR)
	$(BIN_DIR)/jhyy_stage0.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy

# Self-host closure chain: v1.0.0 baseline = v1→v2→v3→v4 (Stage 2 N=3 byte-equal);
# v1.8.3 = v1→v2→v3→v4→v5 (Stage 2 N=4 byte-equal closure, sha 03a1cdd4...)
selfhost: $(BIN_DIR)/jhyy.exe
	@echo "Stage 2 closure chain: v1 → v2 → v3 → v4 → v5 byte-equal check (v1.8.3 N=4 baseline)"
	$(BIN_DIR)/jhyy.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v2
	$(BIN_DIR)/jhyy_v2.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v3
	$(BIN_DIR)/jhyy_v3.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v4
	$(BIN_DIR)/jhyy_v4.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v5
	@echo "Check: sha256sum jhyy_v2.exe jhyy_v3.exe jhyy_v4.exe jhyy_v5.exe must match"

test:
	@echo "Running tests..."
	@echo "TODO: test runner"

clean:
	rm -rf $(BUILD_DIR)