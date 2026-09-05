# V2-C batch plan — v2.8.0 (M5-bridge / N 代 fixed point + QBE 移除)

## Context

**Batch 范围**:V2-A + V2-B 完成 windows + sysv targets 自写后端 + regalloc + peephole。V2-C 是 v2 axis 收尾 batch,1 个 sub-sprint(v2.8.0),含两大动作:
1. **N≥3 代 selfhost fixed point 验算**(byte-equal .il 闭环)
2. **QBE 工具链完全移除**(`qbe.exe` 不再被 jhyy spawn;纯自写后端)

**这是 M5 deferral 的第二前置达成**(per `v1.x-phase-4-m5-boot-from-scratch.md`)。第一前置 = v2.0 阶段 ship(v2.4.0 ✅);第二前置 = QBE 移除 + 自写后端全 target 覆盖(V2-C 完成)。M5 本身(删 `src/*.c` + untrack QBE + 删 `runtime.c`)留独立 sprint 启动。

**在 v2 axis 内位置**:
- V2-A + V2-B ✅ ship(v2.5.0 + v2.6.0 + v2.7.0)
- **V2-C = 本 batch**(v2.8.0)
- 后接:M5 独立 sprint + v3 axis 持续推进

**上游依赖**:
- V2-A ✅ ship(`codegen_amd64.jhyy` 自写后端起步)
- V2-B ✅ ship(regalloc + peephole + sysv target)
- v2.1.0 ✅ ship(ABI 抽离)
- Self-equal baseline sha(V2-B ship 时锁定,记进 `changelog-v2.7.0.md`)

**跨 axis 硬前置**:**V3-C 整个 batch (v3.1.0 + v3.1.1 + v3.1.2 = 3g + 3g.5 + 3g.7)必须先 ship**:
- v2.8.0 N 代 fixed point 验算时跑 `tests/cap_test.jhyy` 需要 3g borrow check + 8 字节 layout
- 否则 N 代验算 fail(borrow check 不通过)
- V3-C ship 后才启动 V2-C

## Sub-sprint 分解

### v2.8.0 (M5-bridge: N 代 fixed point + QBE 移除 + 工具链自含闭环)

**Scope**:

#### Part 1: N≥3 代 selfhost fixed point 验算

1. 多代 fixed point 验算脚本(`compiler/tests/bootstrap/fixed_point.sh`,新,~100 行):
   - 准备 3 份 jhyy binary:`jhyy_v1.exe.exe`(v1 baseline `51376ce5...` frozen) + `jhyy_v2.exe`(v2.8.0 编出) + `jhyy_v3.exe`(jhyy_v2 编 src0 产出)
   - N=3 验算:`jhyy_v1.exe.exe src0/*.jhyy → v2.il` vs `jhyy_v2.exe src0/*.jhyy → v2.il`(byte-equal)
   - N=3 闭包:`jhyy_v2.exe src0/*.jhyy → v2.il` vs `jhyy_v3.exe src0/*.jhyy → v3.il`(byte-equal)
   - 试 N=4:N=3 + `jhyy_v4.exe src0/*.jhyy → v4.il`(byte-equal)
   - 试 N=5:N=4 + `jhyy_v5.exe src0/*.jhyy → v5.il`(byte-equal)
2. `.il` byte-equal closure gate(primary invariant,per D26 + D43):
   - 任意 2 代间 `.il` byte-equal = closed fixed point
   - 跨代 `.s` byte-equal **不**强制(v2.6.0 起 peephole + regalloc 改变 .s 内容,但 IL 闭包仍是 ground truth)
3. `tests/cap_test.jhyy` 必跑(V3-C ship 后):
   - 8 字节 layout 验证:`sizeof(Cap<i32>) == 8`(per `project_cap_abi_layout`)
   - borrow check 跨代一致(N=3 .il byte-equal 隐含 borrow check 决策跨代一致)
4. `tools/fixed_point_summary.py`(新,~50 行):输出 N=3/4/5 结果表 + sha 链 + 通过/失败

#### Part 2: QBE 工具链完全移除

1. `compiler/src0/main.jhyy`:`run_backend` 去掉 QBE 分支;纯走自写 `codegen_amd64_emit`
   - 删除 `run_qbe` 函数体(保留空函数体 + 注释 "deprecated since v2.8.0, see changelog-v2.8.0.md";**不**完全删函数,留 W-XXX workaround 占位)
   - 删除 `QBE_FALLBACK=1` env var 路径(env var 读到直接 warning + 忽略)
2. `compiler/build/bin/qbe.exe`:从 git tree 删除(原 gitignored → 直接 `rm`)
3. `compiler/src/target/qbe_wrapper.{c,h}`(如果有):删除 + untrack
4. `scripts/dev/build/build-jhyy.sh`:删除 `qbe.exe` cp 步骤(原本 stage0 build 把 qbe.exe 拷到 build/bin/)
5. `docs/internal/build.md`:
   - 改:`jhyy.exe` 编 `.jhyy` → `main_jhyy.exe` **无** QBE 中间产物(直接 `jhyy.exe` → `as` → `gcc`)
   - 加一节 "Removed QBE dependency":v2.8.0 起不再 spawn `qbe.exe`;0 外部依赖闭环(除 MinGW `as` + `gcc` linker)
6. `docs/internal/architecture.md`:加 QBE 移除 changelog;模块边界图删 `qbe.exe` 节点
7. 工具链验证:procmon / strace 跑 `jhyy.exe hello.jhyy` → 不再 spawn `qbe.exe`(只 spawn `as` + `gcc` + 链接 `link.exe`)

#### Part 3: 工具链 self-contained 闭环

1. 全部 `compiler/src0/*.jhyy` 走自写后端验证:
   - `jhyy_v1.exe.exe`(v1 baseline frozen)编 `src0/main.jhyy` → `.il` + 后续 `as` + `gcc` → `.exe`
   - `jhyy.exe`(v2.8.0 编出)编同样 → `.il` byte-equal ↔ v1 baseline
   - `jhyy.exe.exe`(v2.8.0 编出,作为新 v1 baseline frozen)再编同样 → `.il` byte-equal
2. `tools/check_dangling.py` 跑 0 dangling
3. regress.py 104/104 PASS 不变(走自写后端,QBE 已删)
4. `compiler/src/`(C 端):**仍保留**(M5 留独立 sprint 删);V2-C 不动 `src/*.c`

**Key files**:
- 新建 `compiler/tests/bootstrap/fixed_point.sh`(~100 行)
- 新建 `tools/fixed_point_summary.py`(~50 行)
- 改 `compiler/src0/main.jhyy`(去 QBE 分支 + 留 W-XXX 空 stub,~50 行)
- 删 `compiler/build/bin/qbe.exe`(gitignored;`rm` 即可)
- 删 `compiler/src/target/qbe_wrapper.{c,h}`(如果存在;`git rm`)
- 改 `scripts/dev/build/build-jhyy.sh`(删 qbe.exe cp 步骤,~5 行)
- 改 `docs/internal/build.md`(~50 行新增 + 改写)
- 改 `docs/internal/architecture.md`(~30 行)
- 改 `docs/logs/v2/changelog-v2.8.0.md`(新 umbrella,~200 行:写 N=3 sha + QBE 移除步骤 + 工具链闭环验证)

**关键决策**:
- **N=3 minimum(per D43)**:试 N=4 / N=5 看能否跨更长链;N=3 ship gate 必须过;N=4/5 是 bonus
- **"工具链完全闭环"定义**:`src0/*.jhyy` 编译产物跟 v1 baseline byte-equal(`jhyy 编 jhyy`);.il 闭包,非 .s/.exe 闭包
- **run_qbe 留空函数不删**:避免破坏 ABI 兼容性 + 留 W-XXX workaround 占位方便后期参考;运行时调走 warning 路径
- **`src/*.c` + `runtime.c` 不动**:M5 独立 sprint 再砍;V2-C 范围仅限 QBE 移除 + N 代验算
- **不**做性能优化(吞吐 / codegen 速度)— 留 post-M5
- **不**做 MSYS2 工具链重打包 — 仍依赖 MinGW `as` + `gcc`(用户已装)

## 跨 axis 硬约束

- **D43** 阶段性 self-equal hold:v2.8.0 是最终 baseline 锁定;N=3 .il byte-equal 是 ship gate
- **3g/3g.5/3g.7 必须先 ship**(V3-C 整个 batch):v2.8.0 N 代 fixed point 验算时跑 `cap_test.jhyy` 需要 3g borrow check + 8 字节 layout;否则 fail
- **3c volatile** 必须已 ship(V3-B v3.0.3)— V2-B v2.7.0 sysv volatile 移植依赖 3c spec
- **Regalloc vs 借用保留**(per § 4.3):v2.6.0 regalloc 不考虑借用保留;V2-C N 代验算时**实际**跑借用测试 → 如发现 fail,临时 hotfix 进 v2.7.x patch 后再 ship v2.8.0
- **M5 deferral 第二前置达成**:V2-C ship 后,M5 可独立 sprint 启动(per `v1.x-phase-4-m5-boot-from-scratch.md`)

## Batch ship gate

- **N=3 selfhost closure**:`fixed_point.sh` 输出 N=3 .il byte-equal ✅
- **`jhyy.exe` procmon / strace 验证不再 spawn `qbe.exe`**:grep `qbe.exe` in trace → 0 hit(只 spawn `as` + `gcc`)
- **全部 `src0/*.jhyy` 走自写后端**:regress.py 104/104 PASS,baseline(V2-B v2.7.0)`.il` byte-equal
- **`tools/check_dangling.py` 0 dangling**
- **`tests/cap_test.jhyy` 8 字节 layout 验证**:`sizeof(Cap<i32>) == 8`
- **`tools/fixed_point_summary.py` 输出 sha 链**:写进 `changelog-v2.8.0.md`
- **regress.py `--cross`** 5/5 PASS(amd64_sysv + sysv_freestanding 在 docker 内跑通)
- **W-067 文档登**:"QBE removal — 自写后端工具链闭环"workaround(if needed;否则标 RESOLVED 闭合 W-XXX qbe 相关 workaround)
- umbrella `docs/logs/v2/changelog-v2.8.0.md` 写 N=3 sha + 删除 qbe.exe 步骤 + 工具链闭环验证

## 风险 + 缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| N 代 fixed point 验算耗时长 | ship gate 阻塞 | N=3 跑 ~10 分钟;N=4/5 翻倍;接受;首次 ship 只要求 N=3 过 |
| QBE 移除后任何 codegen bug 没有 QBE 兜底 | regress 退步 | 必须确保 codegen_amd64 + peephole + regalloc 全覆盖 regress 104/104;`run_qbe` 留空函数体方便后期 debug(临时 `git revert` 切回 QBE 路径 — 但不推荐,regress 链会断) |
| `qbe.exe` 删除触发 git 历史不可逆操作 | 误删 | qbe.exe 是 gitignored(per `feedback_no_artifacts_in_project`);实际只 `rm -f` 本地 file;git tree 中如果曾 tracked 需 `git rm` → 这是正常操作,不可逆风险低 |
| Regalloc 跟 3g 借用保留冲突在 N 代验算时暴露 | V2-C ship 阻塞 | 已知 risk;V2-B ship gate 已包含 cap_test.jhyy 回归;V2-C 启动前再跑 cap_test + borrow check;如发现 fail,临时 hotfix 进 v2.7.x patch(不进 v2.8.0) |
| `fixed_point.sh` 用 jhyy_v1.exe.exe 需 user 提前 freeze v1 baseline | ship gate 阻塞 | user 协助;v2.4.0 ship 时已 freeze `51376ce5...` 在 git history,checkout 即可 |
| Cross-compile test(docker pull ubuntu:24.04)网络问题 | v2.7.0 + v2.8.0 ship 阻塞 | user 协助;regress.py `--cross` 默认 fail-fast + 友好提示;**不**把 docker image 缓存进 git(per `feedback_no_artifacts_in_project`) |
| N=4 / N=5 byte-equal 失败 | bonus 失败,不阻塞 ship | 接受;只要求 N=3;N=4/5 是 informational |

## Out of scope

- **M5 本身**(删 `src/*.c` + untrack QBE + 删 `runtime.c`)— 留独立 sprint 启动
- v3 axis 任何 sub-sprint — v3 axis 独立 ship(V3-A / V3-B / V3-C)
- 性能优化(吞吐 / codegen 速度)— 留 post-M5
- MSYS2 工具链重打包 — 仍依赖 MinGW `as` + `gcc`(用户已装)
- `fixed_point.sh` 跨 Linux 平台(Wine / WSL)— 只跑 Windows native + docker ubuntu

## 文件变更清单

### 新建
- `compiler/tests/bootstrap/fixed_point.sh`(~100 行)
- `tools/fixed_point_summary.py`(~50 行)
- `docs/logs/v2/changelog-v2.8.0.md`(~200 行 umbrella)

### 改动
- `compiler/src0/main.jhyy`(去 QBE 分支 + 留空 stub,~50 行)
- `scripts/dev/build/build-jhyy.sh`(删 qbe.exe cp,~5 行)
- `docs/internal/build.md`(~50 行)
- `docs/internal/architecture.md`(~30 行)
- `docs/internal/workarounds.md`(W-067 QBE removal workaround)

### 删除
- `compiler/build/bin/qbe.exe`(gitignored → `rm -f`)
- `compiler/src/target/qbe_wrapper.{c,h}`(如存在 → `git rm`)

## Commit / tag 节奏

- **Commit 1**:`feat(fixed-point): add N=3 selfhost closure verification`(fixed_point.sh + summary)
- **Commit 2**:`feat(tools): add fixed_point_summary.py + regress integration`
- **Commit 3**:`refactor(codegen): remove QBE backend, pure self-written amd64`(main.jhyy 去 QBE 分支)
- **Commit 4**:`chore(build): drop qbe.exe from toolchain`(删 qbe.exe + build script)
- **Commit 5**:`docs: v2.8.0 batch V2-C ship + M5-bridge 达成`(umbrella changelog)
- **Tag**:`v2.8.0`(ship 后 user 确认 → tag)
- **M5 ready signal**:ship 后通知 user M5 deferral 第二前置达成,M5 独立 sprint 可启动

## Cross-ref

- 上游:`docs/plans/v2/batch-V2-A-plan.md` + `batch-V2-B-plan.md`(V2-A + V2-B 全 target 自写后端为前提)
- 上游 axis:`docs/plans/v3/batch-V3-C-plan.md`(3g + 3g.5 + 3g.7 必须在 V2-C 启动前 ship)
- 上游 axis:`docs/plans/v3/batch-V3-B-plan.md`(3c volatile 必须 ship,V2-B sysv volatile 移植依赖)
- M5 deferral:`docs/plans/v1/v1.x-phase-4-m5-boot-from-scratch.md`(V2-C 完成 = 第二前置达成,M5 可启动)
- M1-M11 链路:`docs/plans/v2/v2.0.0-os-prep.md § 1`
- 8 字节 Cap<T> layout:`memory/project_cap_abi_layout.md`
- QBE CRLF root cause(避免 reintroduce):`memory/feedback_qbe_crlf_root_cause.md`
- make clean 风险:`memory/feedback_make_clean_too_aggressive.md`(clean+build 后必 `git checkout HEAD -- compiler/build/bin/.gitkeep ...` restore)
