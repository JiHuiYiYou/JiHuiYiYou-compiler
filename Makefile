# jhyy project — top-level Makefile
#
# v4.0.21 (2026-10-25): **C 端编译器已删除**(M5 Part 1)—— `compiler/src/`
# 整个目录删掉,`make stage0` 目标随之消失。
#
# 为什么现在做:user 2026-10-25 明确「C 不用改了,早就不维护了」。而 C 端早
# 就从构建关键路径上退出(v4.0.8:`jhyy.exe` **自己**编 src0,不再经 stage0/QBE
# —— `compiler/build/bin/jhyy.exe` 本身是 git 跟踪的产物,fresh clone 里就有
# 一个可用的自举编译器)。留着它只剩三个坏处:
#   ① **两套实现分叉** —— 同一个 bug 要修两遍(W-127/128/129 就是分叉出来的),
#      而 C 侧的 W-133(聚合 ==)至今没同步 ⇒ stage0 编译**静默错值**;
#   ② stage0 是 regress 的 informational 项(v4.0.8 起),长期 39+ 个红,
#      噪音盖住信号;
#   ③ ~9800 行死代码,每个读代码的人都要先判断「这份还在用吗」。
#
# 构建语义不变、且更强:「**jhyy.exe 能把自己编成同一个东西**」——
# 见 jhyy.exe 规则里的 byte-equal 自举闭环检查。
#
# ⚠️ 本仓**没有** C 端了 ⇒ 「自举门槛」这个概念只剩 jhyy 侧一档
# (v1.x 达成的那一档就是它)。

CC       = gcc
# v4.0.0 D26: -g0 + strip build-id for byte-equal rebuilds.
# Per docs/plans/v2/v2.4.0任务清单 + 概要设计.md:26,104-124 + docs/archive/logs/v2/changelog-v2.4.0.md
# (原名 CFLAGS_STAGE0 —— C 端删掉后 "stage0" 已无指代对象,改名 CFLAGS_REPRO)
CFLAGS_REPRO = -std=c11 -Wall -Wextra -g0 -Wl,--build-id=none
SOURCE_DATE_EPOCH = 1234567890
# v4.0.9 (W-117):1 = 产物必须与提交进仓的那份逐字节相同,否则 make 失败。
# 任何要发布的人都要过这道门。CI 传 0 —— CI 不发布,它验的是提交进仓的产物,
# 跑 `make` 仅为验「工具链能编出自举闭环的编译器」。理由见 jhyy.exe 规则处。
STRICT_TOOLCHAIN ?= 1
# v4.0.21: QBE / windres 变量一并删除 —— 它们只服务于 C 端
# (QBE 由 compiler/src/main.c 拼路径调 system();windres 只给 C 端的
# compiler/src/jhyy.rc 用)。自举侧的图标走 `jhyy_helpers.c` 里的
# `jh_build_icon_obj()`(**现场生成** .rc),与 C 端无关。

# Directories
COMPILER_DIR = compiler
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

# v4.0.21: C 端 binary(jhyy_stage0.exe)随 compiler/src/ 一起删除。
# 现在只有 jhyy 侧的产物:
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

.PHONY: all clean test selfhost

all: $(JHY_RUNTIME_O) $(JHY_HELPERS_O) $(BIN_DIR)/jhyy.exe $(BIN_DIR)/jhyy_v1.exe.exe

$(OBJ_DIR)/runtime.o: $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(@D)
	# v4.0.0 D26 reproducibility: runtime.c must compile with -g0 too, else
	# the embedded debug info (incl. mingw-w64-crt build paths from crt0
	# link-in) breaks jhyy.exe byte-equal rebuilds.
	$(CC) $(CFLAGS_REPRO) -c $< -o $@

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
# v4.0.21:`make stage0` 连同 C 端一起删除 —— 它已不在 `all` 依赖链上两年,
# 现在连「能编」这件事本身也不再维护(user 2026-10-25 决策)。
$(BIN_DIR)/jhyy.exe: $(SRC0_DIR)/main.jhyy $(SRC0_DIR)/*.jhyy $(JHY_RUNTIME_O) $(JHY_HELPERS_O)
	@mkdir -p $(BIN_DIR)
	@if [ ! -f $@ ]; then \
	    echo "ERR: $@ 不存在 —— 没有它就无法自举。"; \
	    echo "     它是 git 跟踪的产物,正常 clone 就有;若被删,先 checkout 回来:"; \
	    echo "       git checkout HEAD -- compiler/build/bin/jhyy.exe"; \
	    exit 1; \
	fi
	@# ── 自举闭环门:迭代到**不动点**(W-147,2026-10-26 真修)──
	@#
	@# 为什么从「编两代比一次」改成「迭代到不动点」:
	@#
	@# 旧逻辑:锚点编出第 1 代,第 1 代再编出第 2 代,比第 1 代与第 2 代的 .s。
	@#   ⇒ 它验的是**锚点**的不动点,装出去的却是**没被验过**的第 1 代。
	@#   ⇒ 改后端时(src0 自己的 .s 编码变了)会有**一代**过渡:
	@#      第 1 代与第 2 代必然不同 ⇒ 门硬失败 ⇒ make 卡死;
	@#      而那一代恰恰是**常量错**的一代(实测:src0 里 2^63 / 2^64 被写成
	@#      9.2233720368547758 / 1.8446744073709551 —— 指数被后端丢掉)
	@#      ⇒ 就算手工绕过门装上去,装出去的是**坏产物**。
	@#
	@# 新逻辑:反复「锚点编第 N 代 → 第 N 代编第 N+1 代 → 比第 N 与第 N+1 代」,
	@#   不等就把锚点推进一代,最多 3 轮。
	@#   收敛的那一轮,第 N 代**就是不动点**(第 N+1 代与它同产物)⇒ 装它是对的。
	@#   ⇒ 门从「验锚点」升级成「验**装出去的那个产物**」—— 只会更强,不会更松。
	@#   ⇒ 过渡期自动消化,不需要任何 escape hatch(仓库规矩:门不许有后门)。
	@#
	@# 3 轮仍不收敛 ⇒ 硬失败(真正的非确定性照样被抓,见 W-121 那类)。
	@# 锚点 = 当前这个(已提交的)jhyy.exe —— 每轮开始前都重铺一遍
	@rm -f $(BIN_DIR)/_boot_anchor.exe   # 删陈旧锚点:缺 cp 时要响亮失败,不能拿旧的顶
	@cp -f $@ $(BIN_DIR)/_boot_anchor.exe
	@i=0; converged=0; \
	while [ $$i -lt 3 ]; do \
	  if ! $(BIN_DIR)/_boot_anchor.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/_boot_new >$(BIN_DIR)/_boot_new.log 2>&1; then \
	    echo "SELFFAIL: 第 $$((i+1)) 代编译失败:"; cat $(BIN_DIR)/_boot_new.log; exit 1; \
	  fi; \
	  if ! $(BIN_DIR)/_boot_new.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/_boot_new2 >$(BIN_DIR)/_boot_new2.log 2>&1; then \
	    echo "SELFFAIL: 第 $$((i+2)) 代编译失败:"; cat $(BIN_DIR)/_boot_new2.log; exit 1; \
	  fi; \
	  if cmp -s $(BIN_DIR)/_boot_new.s $(BIN_DIR)/_boot_new2.s; then converged=1; break; fi; \
	  echo "  (自举过渡:第 $$((i+1)) 代与第 $$((i+2)) 代产物不同 ⇒ 推进锚点一代)"; \
	  cp -f $(BIN_DIR)/_boot_new.exe $(BIN_DIR)/_boot_anchor.exe; \
	  i=$$((i+1)); \
	done; \
	if [ $$converged -ne 1 ]; then \
	  echo "SELFFAIL: 自举在 3 代内未收敛 —— 编译器不是不动点"; \
	  echo "          $(BIN_DIR)/_boot_new.s  vs  $(BIN_DIR)/_boot_new2.s"; \
	  exit 1; \
	fi; \
	echo "  自举闭环:第 $$((i+1)) 代收敛 ✓(不动点)"
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
	       $(BIN_DIR)/_boot_anchor.s  $(BIN_DIR)/_boot_new.s \
	       $(BIN_DIR)/_boot_new2.s \
	       $(BIN_DIR)/_boot_new.log $(BIN_DIR)/_boot_new2.log

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
# (实测);.o 在下面这组 flags 下也可复现(同 flags 两次编译 sha 相同).
#
# ⚠️ v4.0.21 (W-137)修:这两条规则原本引用 `$(CFLAGS_STAGE0)` —— 那个变量在
# M5 Part 1 (b6efe61)里被改名成 `$(CFLAGS_REPRO)`,**这两处没跟着改** ⇒
# 展开成空 ⇒ 两个 .o **不带 -std=c11 -Wall -Wextra** 编译。
# 后果不是「少几个警告」那么轻:`-Wall -Wextra` 正是会报 `-Wcomment`
# (「块注释未闭合」)的开关 —— W-136 就是靠这个洞把两个 C 桥函数吞进注释,
# 编译照过、符号没了,直到链接期才炸。详见 workarounds.md W-136 / W-137。

$(JHY_RUNTIME_O): $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(OBJ_DIR)
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(CC) $(CFLAGS_REPRO) -c $< -o $@

$(JHY_HELPERS_O): $(SRC0_DIR)/jhyy_helpers.c
	@mkdir -p $(OBJ_DIR)
	SOURCE_DATE_EPOCH=$(SOURCE_DATE_EPOCH) $(CC) $(CFLAGS_REPRO) -c $< -o $@

# v4.0.8: jhyy_v1.exe.exe = jhyy.exe 的副本,**每次构建重新生成**。
# 兑现 v1.4.4 的副本约定,同时让它不再是会腐烂的 git 快照。名字保留是因为
# fixed_point.sh / byte_equal.sh / stage1-expanded.sh 三个脚本按名引用它。
$(BIN_DIR)/jhyy_v1.exe.exe: $(BIN_DIR)/jhyy.exe
	@cp -f $< $@

# Self-host closure chain: v1→v2→v3→v4→v5 (v1 = 当前 jhyy.exe 的副本,
# 所以 v1==v2 是确定性检查,不是跨版本对比)
#
# 2026-10-18 (CI 重构): 本 target 此前编完 v2..v5 之后**只 echo 一句**
# "Check: sha256sum ... must match" 就退出 —— 真正的比对留给人工。
# 它在 ci.yml 里是 blocking step,于是「一个从不判定的步骤」拿到了
# 「一个会阻断合并的门」的权重。这比没有门更糟(feedback_ci_gate_must_exercise_path):
# 读日志的人会以为闭环验过了。
#
# 现在它自己比。比对对象是 `.s` 不是 `.exe`: `.s` 是 (源码 × 编译器) 的函数,
# 与 host gcc 版本无关; `.exe` 是 (源码 × gcc 版本) 的函数,跨 toolchain 必假阳性
# —— W-117 那条 TOOLCHAIN-DRIFT 就是拿 .exe 跨 toolchain 比出来的噪音。
#
# 语义边界(重要,别误读):本 target 与 closure_check.sh 验的都是**确定性与自洽**,
# 不是**正确性**。一个确定性的错误编译器照样闭环通过。正确性只有 regress 门管。
selfhost: $(BIN_DIR)/jhyy.exe $(BIN_DIR)/jhyy_v1.exe.exe
	@echo "Stage 2 closure chain: v1 → v2 → v3 → v4 → v5 .s byte-equal check"
	$(BIN_DIR)/jhyy.exe  compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v2
	$(BIN_DIR)/jhyy_v2.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v3
	$(BIN_DIR)/jhyy_v3.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v4
	$(BIN_DIR)/jhyy_v4.exe compile $(SRC0_DIR)/main.jhyy -o $(BIN_DIR)/jhyy_v5
	@for n in 2 3 4 5; do \
	    if [ ! -s "$(BIN_DIR)/jhyy_v$$n.s" ]; then \
	        echo "SELFFAIL: jhyy_v$$n.s 缺失或为空 —— 编译器静默 exit 0 但没产 .s(W-086 那类)"; \
	        exit 1; \
	    fi; \
	done
	@for pair in "2 3" "3 4" "4 5"; do \
	    set -- $$pair; \
	    if cmp -s "$(BIN_DIR)/jhyy_v$$1.s" "$(BIN_DIR)/jhyy_v$$2.s"; then \
	        echo "  v$$1.s == v$$2.s  ✓"; \
	    else \
	        echo "SELFFAIL: v$$1.s != v$$2.s —— 自举未闭环"; \
	        echo "  $(BIN_DIR)/jhyy_v$$1.s vs $(BIN_DIR)/jhyy_v$$2.s"; \
	        diff "$(BIN_DIR)/jhyy_v$$1.s" "$(BIN_DIR)/jhyy_v$$2.s" 2>/dev/null | head -10 | sed 's/^/    /'; \
	        exit 1; \
	    fi; \
	done
	@echo "PASS — 自举闭环达成 (v2..v5 逐字节相同)"

test:
	@echo "Running tests..."
	@echo "TODO: test runner"

clean:
	rm -rf $(OBJ_DIR)
	@# bench 输出目录(self_host_bench.sh 的产物,12.8 MB × 2)——
	@# 它在 bin/ 之外,上面的 find 覆盖不到 ⇒ 显式删。
	rm -rf $(BUILD_DIR)/bench
	@# bin/ 下**只删未跟踪**的产物。git 跟踪的两个必须留在树上:
	@#   .gitkeep  — 目录占位
	@#   jhyy.exe  — 自举锚点(fresh clone 里就有;删了就没法自举)
	@# 旧的 `rm -rf $(BUILD_DIR)` 把这两个一起删掉 ⇒ 仓库当场不可用
	@# (per feedback_make_clean_too_aggressive)。
	@find $(BIN_DIR) -maxdepth 1 -type f ! -name '.gitkeep' ! -name 'jhyy.exe' -delete 2>/dev/null || true