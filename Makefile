# jhyy project — top-level Makefile
# v1.4.4: 改用 stage-0 链 — `all` 先产 jhyy_stage0.exe (C 端), 再用 stage-0
# 编译 src0/main.jhyy → jhyy.exe (jhyy-side 产物)。jhyy.exe 是 production
# binary, jhyy_stage0.exe 只用于 bootstrap (改 compiler/src/*.c 后重建)。
# v4.0.0: D26 reproducibility recipe applied to stage0 build (-g0 + strip +
# SOURCE_DATE_EPOCH); QBE still vendored for C-side bootstrap (full removal
# is M5 scope per v1.x-phase-4-m5-boot-from-scratch.md).

CC       = gcc
CFLAGS   = -std=c11 -Wall -Wextra -g -I$(SRC_DIR)
# v4.0.0 D26 stage0: -g0 + strip build-id for byte-equal rebuilds.
# Per docs/plans/v2/v2.4.0任务清单 + 概要设计.md:26,104-124 + docs/logs/v2/changelog-v2.4.0.md
CFLAGS_STAGE0 = -std=c11 -Wall -Wextra -g0 -Wl,--build-id=none -I$(SRC_DIR)
STRIP         = strip
SOURCE_DATE_EPOCH = 1234567890
# QBE removed v4.0.0 from jhyy-side compile path; still vendored for C-side
# bootstrap — compiler/src/main.c:489 拼 `%s/qbe/qbe.exe` 并在 :498 用 system()
# 调它跑 C 端 stage0。Full QBE removal 是 M5 scope(deferred — 见
# docs/plans/v4/backlog.md § 1 M5)。M5 是计划项不是 workaround,故不登记进
# workarounds.md —— 原先此处写的 `W-XXX` 是从未填过的悬空占位符。
#
# 注意:下面两个变量当前**没有任何 recipe 引用**(stage0 的 QBE 调用走 main.c
# 内部,不经过 Makefile)。保留仅为记录路径。
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
       $(SRC_DIR)/target/abi_amd64_win.c \
       $(SRC_DIR)/target/abi_amd64_win_freestanding.c

OBJS = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRCS))
RUNTIME_OBJ = $(OBJ_DIR)/runtime.o

# v1.4.4: 4 个 binary 共存
#   jhyy_stage0.exe — C 端 (stage-0 bootstrap, only needed after src/ change)
#   jhyy.exe        — jhyy-side 产物 (production binary, what users invoke)
#   jhyy.exe.exe    — jhyy.exe 的 baseline (per feedback_regress_baseline_binary_hash)
#   jhyy_v1.exe.exe — jhyy.exe 的**同内容改名副本**,由 `make` 每次构建时生成
#                     (v4.0.8 起;见下方 v1_copy 规则)
#
# v4.0.8 更正 jhyy_v1.exe.exe 的定位 —— 它此前被三个地方用三种说法描述
# (Makefile 说「v1.0.0 historical baseline, 不可退役」/ ci.yml 说「已脱节,
# v1 = 当前 production」/ 实际是 git 里一个 10-12 的静态快照)。三者互相矛盾,
# 而且快照 3 天就跟 jhyy.exe 脱钩,后果是 fixed_point.sh 的
# `v1 != v2 → re-baseline archived` 每次改后端必然触发 —— 一个恒真的断言
# 不是断言,是噪音(2026-10-15 的「v3!=v4 要到第 4 代才收敛」误读即源于此;
# 实际是 fixed_point.sh 的 N>=4 循环漏设 JHY_WRITE_IL,详见 76e3b72)。
#
# 现在 v1 = 当前 jhyy.exe 的副本,v1==v2 于是恢复成一个有意义的检查:
# **同一个二进制跑两遍必须产出相同的 .il / .s**(确定性)。re-baseline
# 归档流程随之退休 —— 没有"跨版本差异"可比了,只有"自身是否确定"。
# 它不再是 source artifact,改由 .gitignore 排除。

.PHONY: all clean test stage0 selfhost

all: $(BIN_DIR)/jhyy.exe $(BIN_DIR)/jhyy_v1.exe.exe

# Stage 0: gcc 产 jhyy_stage0.exe (C 端 bootstrap)
stage0: $(BIN_DIR)/jhyy_stage0.exe

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(@D)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/runtime.o: $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(@D)
	# v4.0.0 D26 reproducibility: runtime.c must compile with -g0 too, else
	# the embedded debug info (incl. mingw-w64-crt build paths from crt0
	# link-in) breaks jhyy.exe byte-equal rebuilds.
	$(CC) $(CFLAGS_STAGE0) -c $< -o $@

# v1.8.1 patch: windres rule producing icon resource .o (RT_ICON group).
# v4.0.0 D26 reproducibility: SOURCE_DATE_EPOCH propagated to windres so
# the .o timestamps don't break 4-rebuild byte-equal verification.
$(RES_OBJ): $(SRC_DIR)/jhyy.rc $(ICON_SRC)
	@mkdir -p $(OBJ_DIR)
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(WINDRES) -i $< -O coff -o $@

# v1.4.4: C 端产物改名 jhyy_stage0.exe (runtime.o 不链入 — 它是给 jhyy.exe 用
# 的, 含重复符号 arena_alloc/main, 会跟 main.c/arena.c 冲突)
# v1.8.1: jhyy-res.o (icon RT_ICON group) 链入 stage0,branded "J" 进 exe。
# v4.0.0 D26 reproducibility: CFLAGS_STAGE0 (no -g debug info), strip
# build-id post-link, SOURCE_DATE_EPOCH for deterministic timestamps.
# Result: 4-rebuild byte-equal per docs/plans/v2/v2.4.0 § 2.1.1 byte_equal.sh.
$(BIN_DIR)/jhyy_stage0.exe: $(OBJS) $(RES_OBJ)
	@mkdir -p $(BIN_DIR)
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(CC) $(CFLAGS_STAGE0) $^ -o $@
	$(STRIP) --strip-unneeded $@

# v1.4.4: jhyy.exe 由 jhyy_stage0.exe 编 src0/main.jhyy 产
# 依赖 stage0 (jhyy_stage0.exe 必须先存在)
$(BIN_DIR)/jhyy.exe: $(SRC0_DIR)/main.jhyy $(SRC0_DIR)/*.jhyy $(BIN_DIR)/jhyy_stage0.exe
	@mkdir -p $(BIN_DIR)
	$(BIN_DIR)/jhyy_stage0.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy

# v4.0.8: jhyy_v1.exe.exe = jhyy.exe 的副本,**每次构建重新生成**。
# 兑现 v1.4.4 的副本约定,同时让它不再是会腐烂的 git 快照。名字保留是因为
# fixed_point.sh / byte_equal.sh / stage1-expanded.sh 三个脚本按名引用它。
$(BIN_DIR)/jhyy_v1.exe.exe: $(BIN_DIR)/jhyy.exe
	@cp -f $< $@

# Self-host closure chain: v1→v2→v3→v4→v5 (v1 = 当前 jhyy.exe 的副本,
# 所以 v1==v2 是确定性检查,不是跨版本对比)
selfhost: $(BIN_DIR)/jhyy.exe $(BIN_DIR)/jhyy_v1.exe.exe
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