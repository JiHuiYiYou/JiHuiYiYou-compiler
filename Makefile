# jhyy project — top-level Makefile
#
# v4.0.8 (2026-10-15): `all` 不再经 stage0/QBE —— `jhyy.exe` **自己**编 src0。
#
# 理由:`compiler/build/bin/jhyy.exe` 本身是 git 跟踪的产物,fresh clone 里就有
# 一个可用的自举编译器,stage0 那条链的唯一作用(「用 C 编译器编出第一个
# jhyy.exe」)因此不是必需的。QBE 更只在 **stage0 的运行期**被调用
# (main.c:489/496 的 system()),自举编译器完全不用它 —— 于是 QBE 这个第三方
# 二进制从「每次构建的必经之路」上消失,`.gitattributes` 那类「二进制被当文本
# 损坏」的故障从此没有着力点。
#
# 构建语义同时变强:不再是「C 编译器能编出 jhyy.exe」,而是
# 「**jhyy.exe 能把自己编成同一个东西**」—— 见 jhyy.exe 规则里的 byte-equal
# 自举闭环检查。
#
# 仍然保留:`make stage0` 仍能编 C 端 bootstrap(CI 也仍然验它),它只是不在
# `all` 的依赖链上。
# v4.0.0: D26 reproducibility recipe applied to stage0 build (-g0 + strip +
# SOURCE_DATE_EPOCH).

CC       = gcc
CFLAGS   = -std=c11 -Wall -Wextra -g -I$(SRC_DIR)
# v4.0.0 D26 stage0: -g0 + strip build-id for byte-equal rebuilds.
# Per docs/plans/v2/v2.4.0任务清单 + 概要设计.md:26,104-124 + docs/logs/v2/changelog-v2.4.0.md
CFLAGS_STAGE0 = -std=c11 -Wall -Wextra -g0 -Wl,--build-id=none -I$(SRC_DIR)
STRIP         = strip
SOURCE_DATE_EPOCH = 1234567890
# v4.0.9 (W-117):1 = 产物必须与提交进仓的那份逐字节相同,否则 make 失败。
# 任何要发布的人都要过这道门。CI 传 0 —— CI 不发布,它验的是提交进仓的产物,
# 跑 `make` 仅为验「工具链能编出自举闭环的编译器」。理由见 jhyy.exe 规则处。
STRICT_TOOLCHAIN ?= 1
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
# v4.0.8:预编 runtime.c / jhyy_helpers.c 的产物(link_with_gcc 优先用它们,
# 见下方规则处的完整理由)。定义放在这里是因为 `all:` 等规则会引用 —— Make 在
# 解析到使用点时就展开,定义在使用点之后等于没定义。
JHY_RUNTIME_O = $(OBJ_DIR)/_jhyy_runtime.o
JHY_HELPERS_O = $(OBJ_DIR)/_jhyy_helpers.o

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

all: $(JHY_RUNTIME_O) $(JHY_HELPERS_O) $(BIN_DIR)/jhyy.exe $(BIN_DIR)/jhyy_v1.exe.exe

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

# v4.0.8 (2026-10-15): jhyy.exe 改由**它自己**编 src0,不再经 stage0/QBE。
#
# 为什么改:stage0 链的唯一作用是「用 C 编译器编出第一个 jhyy.exe」,而
# `compiler/build/bin/jhyy.exe` **本身是 git 跟踪的**(实测与当前构建 byte-equal,
# sha f46d2548)。也就是说 fresh clone 里已经有一个可用的自举编译器,
# stage0 不是 bootstrapping 必需的。
#
# QBE 的处境同样如此:它只在 **stage0 的运行期**被调用(main.c:489/496 的
# system()),**自举编译器完全不用它**。于是 stage0/QBE 一起从构建关键路径上
# 消失 —— 一个第三方二进制不再位于每次构建的必经之路上,`.gitattributes`
# 那类「二进制被当文本损坏」的故障从此没有着力点。
#
# 构建语义随之变强:不再是「用 C 编译器编出 jhyy.exe」(只证明 C 侧能编),
# 而是「**jhyy.exe 能把自己编成同一个东西**」—— 下面那一步 byte-equal 就是
# 自举闭环门,任何 emit 层的非确定性都会当场炸,而不是留到 regress 才发现。
#
# `make stage0` 仍然保留(C 侧 bootstrap 本身仍要能编,CI 也仍然验它),
# 只是不再在 `all` 的依赖链上。
$(BIN_DIR)/jhyy.exe: $(SRC0_DIR)/main.jhyy $(SRC0_DIR)/*.jhyy $(JHY_RUNTIME_O) $(JHY_HELPERS_O)
	@mkdir -p $(BIN_DIR)
	@if [ ! -f $@ ]; then \
	    echo "ERR: $@ 不存在 —— 没有它就无法自举。"; \
	    echo "     它是 git 跟踪的产物,正常 clone 就有;若被删,先 checkout 回来:"; \
	    echo "       git checkout HEAD -- compiler/build/bin/jhyy.exe"; \
	    exit 1; \
	fi
	@# 锚点 = 当前这个(已提交的)jhyy.exe
	@cp -f $@ $(BIN_DIR)/_boot_anchor.exe
	@$(BIN_DIR)/_boot_anchor.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/_boot_new
	@$(BIN_DIR)/_boot_new.exe     compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/_boot_new2
	@# 自举闭环:新 exe 编 src0 的产物必须与它自己编的完全一致
	@cmp -s $(BIN_DIR)/_boot_new.s $(BIN_DIR)/_boot_new2.s || { \
	    echo "SELFFAIL: 新 jhyy.exe 编 src0 的结果与它自己编的不一致 —— 自举不闭环"; \
	    echo "          $(BIN_DIR)/_boot_new.s  vs  $(BIN_DIR)/_boot_new2.s"; \
	    exit 1; }
	@# v4.0.9 (W-117):产物还必须与**提交进仓的那个**逐字节相同,否则停下。
	@#
	@# 为什么必须硬失败而不是打个 warning:上面那条自举闭环检查只证明
	@# 「这份源码编出来的东西,自己再编一遍还是一样」—— 换成任何一套工具链
	@# 它都成立。实测 CI 上换成 setup-msys2 装的 UCRT64 gcc,闭环照样 PASS,
	@# 编出来的 jhyy.exe 却在编译三个小测试时**卡死在自己的 self-backend 里**
	@# (进程还在跑、`[4] codegen done` 之后零产物),而提交进仓的那份 3/3 全过。
	@# 也就是说:工具链一换,编译器会**静默地变成另一个**,而既有门照样全绿。
	@#
	@# 这里拦的是「换工具链」这件事本身 —— 要换的人会在这里看到明确的失败,
	@# 而不是几天后从 CI 的玄学超时里反推。
	@#
	@# 谁该被这条门拦:任何**要发布**的人。它默认开着(STRICT_TOOLCHAIN=1)。
	@# CI 传 STRICT_TOOLCHAIN=0 —— 这不是放宽判据,而是**划清职责**:
	@# CI 不发布,它验的是**提交进仓的那份产物**(回归门跑的就是它);
	@# CI 跑 `make` 只为验「工具链能编出自举闭环的编译器」,而闭环与工具链无关。
	@# 漂移检查管的是「这个编译器该不该被发布」,不是「能不能编出来」。
	@# CI 侧另有 warning 报出两个 sha 的差异 —— 不静默。
	@#
	@# ⚠️ 这道门只在**源码没动过时**才有意义:src0 一改,make 本来就该产出不同
	@# 的二进制,拿它跟提交进仓的旧产物比会挡住每一次正常的源码修改(踩过)。
	@# 所以先用 git 判断 src0/runtime 是否与 HEAD 一致;不一致就跳过并说明。
	@echo "STRICT_TOOLCHAIN=$(STRICT_TOOLCHAIN)"
	@if git diff --quiet HEAD -- $(SRC0_DIR) $(RUNTIME_DIR) 2>/dev/null; then \
	  if ! cmp -s $@ $(BIN_DIR)/_boot_new.exe; then \
	    echo "TOOLCHAIN-DRIFT (W-117): 重新编出的 jhyy.exe 与提交进仓的那份不同。"; \
	    echo "  本机工具链: $$($(CC) --version 2>/dev/null | head -1)"; \
	    echo "  已知后果:换 gcc 版本可能改变编译器行为,而自举的 byte-equal"; \
	    echo "  检查对这种改变是瞎的 —— 它只验自洽,不验与发布产物等价。"; \
	    echo "  要发布:先确认新产物过全量回归,再 git add compiler/build/bin/jhyy.exe。"; \
	    echo "  不要删掉这条检查或加 --force 来「让它过去」—— 那正是本项目栽过的坑。"; \
	    echo "  新产物留在 $(BIN_DIR)/_boot_new.exe,可自行比对。"; \
	    if [ "$(STRICT_TOOLCHAIN)" = "1" ]; then exit 1; fi; \
	    echo "  (STRICT_TOOLCHAIN=0:只报不拦 —— CI 不发布,它验的是提交进仓的产物)"; \
	  fi; \
	else \
	  echo "  (src0/runtime 与 HEAD 有改动 —— 新产物本就该不同,跳过漂移检查)"; \
	fi
	@mv -f $(BIN_DIR)/_boot_new.exe $@
	@rm -f $(BIN_DIR)/_boot_anchor.exe $(BIN_DIR)/_boot_new2.exe \
	       $(BIN_DIR)/_boot_anchor.il $(BIN_DIR)/_boot_new2.il \
	       $(BIN_DIR)/_boot_anchor.s  $(BIN_DIR)/_boot_new.s

# v4.0.8:预编 runtime.c / jhyy_helpers.c 成 .o。
#
# 为什么:实测「gcc .s + runtime.c + jhyy_helpers.c」= 5045ms,而
# 「gcc .s + 两个预编 .o」= 531ms —— `link_with_gcc` 每次都在**重复编这两个
# C 文件**,而编译器自己的活只占 ~450ms。200 个测试 × 省 4.5s ≈ 15 分钟;
# CI 的 job 上限 45 分钟,而 regress 阶段已经撞满(cancelled)。
#
# 新鲜度由这里的依赖关系保证:改了 runtime.c 跑一次 make 就重编。
# `.o` 不存在时 `link_with_gcc` 自动回退到 `.c` 路径,行为与 v4.0.7 一致。
#
# D26 可复现性:两条路径在 SOURCE_DATE_EPOCH 固定时产出**逐字节相同**的 exe
# (实测);.o 在下面这组 flags 下也可复现(同 flags 两次编译 sha 相同)。

$(JHY_RUNTIME_O): $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(OBJ_DIR)
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(CC) $(CFLAGS_STAGE0) -c $< -o $@

$(JHY_HELPERS_O): $(SRC0_DIR)/jhyy_helpers.c
	@mkdir -p $(OBJ_DIR)
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(CC) $(CFLAGS_STAGE0) -c $< -o $@

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