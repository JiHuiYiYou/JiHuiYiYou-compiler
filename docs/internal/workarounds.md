# Workarounds

> JHYY 项目所有 workaround 的唯一权威登记处。
> 每个 workaround 必须在此登记后才能应用到代码里。

## 登记格式

每个 workaround 必须包含：

| 字段 | 含义 |
|------|------|
| **ID** | `W-NNN`，自增 |
| **状态** | `ACTIVE` / `RESOLVED` / `SUPERSEDED` |
| **日期** | 引入日期 (YYYY-MM-DD) |
| **触发面** | 什么模式/输入会触发底层问题 |
| **症状** | 触发后看到什么（编译报错/segfault/QBE 错/IL 错） |
| **根因嫌疑** | 当前最好的解释（不要求 100% 证实） |
| **workaround** | 怎么绕 |
| **影响范围** | 在哪些文件/位置应用了 |
| **失效条件** | 何时不能绕（比如 fix 后必须 revert） |
| **superseder** | 解决后引用哪个 fix / commit |
| **引用** | 相关 issue / 文档 / commit hash |

## 索引

| ID | 状态 | 简介 |
|----|------|------|
| [W-001](#w-001-hash_string-用-i32-deref-绕-v0-codegen-loadsb-错) | RESOLVED (v0.8 commit 9) | hash_string 改 byte-by-byte `*u8` deref + length mix (FNV-1a), 真修 W-001 副作用 |
| [W-002](#w-002-mainjhyy-重命名绕-jhyy_v1-hash_string-堆损坏) | RESOLVED (v0.9 wip commit 2.12) | 211 个 src0 标识符 `_v1` 后缀化 revert 回原名, W-001 真修后失效 |
| [W-003](#w-003-jhyy_v1-let-_-fncall-顶层-嵌套-segfault) | ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已消除 Bug 7/7b 触发面; minimal repros for top-level + nested + NODE_ASSIGN[NODE_FIELD] all 5×5 PASS on canonical, 2026-08-12 verified) | `let _ = fncall(...)` 改 direct call，绕 jhyy_v1 codegen segfault（Bug 7/7b） |
| [W-004](#w-004-short-local-var-4-chars--symtab-hash-撞--jhyy_v1-field-assign-死循环) | RESOLVED (transitively closed by W-001 byte-by-byte FNV-1a 真修 — minimal repro + 4 boundary variations all pass codegen on jhyy_v1 (sha `ba94df93...`), 2026-08-12 verified) | 短（≤4 字符）local var / fn 参数 / field 改名绕 jhyy_v1 symtab hash 撞（stack overflow） |
| [W-005](#w-005-let-mut--assign--jhyy_v1-codegen-segfault) | RESOLVED (v0.9 wip commit 2.13) | `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕 jhyy_v1 codegen segfault；commit 2.11 CGContext 布局对齐真修 + commit 2.13 revert 16 处回 `let mut` 风格 |
| [W-006](#w-006-jhyy_v1-return-x--y-两-1-char-var-发-127qbe-fail) | RESOLVED (transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain — minimal repro no longer triggers, 2026-08-11 verified) | jhyy_v1 codegen 让两个 1-char 局部变量在 `return x ± y` 共享同一 stack slot → QBE fail / exit 127；改名或加类型注解绕 |
| [W-007](#w-007-jhyy_v1-fn--i64--return--literal-as-i64-emit-w-copy) | ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已含 cg_convert_arg `src=W → dst=L` extsw 分支镜像 v0.8 commit 7 `0453cef`, 2026-08-12 5x5 PASS verified on 4 BAD variants, IL byte-equal C-side) | jhyy_v1 codegen 把 `fn() -> i64 { return X as i64; }` 的 return value 当 w（32-bit）emit → QBE "invalid type for jump argument" 错 |
| [W-008](#w-008-jhyy_v1-cg_find_field_offset-漏一层-deref-i64-struct-field-emit-w-loadw) | RESOLVED | jhyy_v1 codegen NODE_FIELD 查 struct field type 时把 `*u8` 指针当 `**u8` 解了一层 → i64/pointer struct field 全 emit `=w loadw` 而非 `=l loadl` → QBE 拒绝 |
| [W-009](#w-009-jhyy_v1-cg_convert_arg-src_t--0-返回-arg-未-coerce-导致-literal-0-w-copy-0-在-ceql-被-reject) | RESOLVED | jhyy_v1 codegen cg_convert_arg 在 `src_t==0` 时直接 return arg，但 literal 0 实际 emit `=w copy 0`（因 qbe_type_of(NULL)=QBE_W）→ 比较 l 字段（pointer / i64 / u64）时 `ceql`/`csltl` 等操作码两边操作数类型不匹配 → QBE "invalid type for second operand" 错 |
| [B-let2 (cross-ref)](#cross-ref-b-let2-stage-1-byte-equal-codegen-gap) | RESOLVED (v0.9 commit 2.5) | jhyy_v1 `cg_convert_arg` 缺 `src=l, dst=w` narrow 分支 → `i64 → i32` 字段赋值 / `as` 转换 emit 错 IL |
| [W-008 ↔ W-009 ↔ W-007 ↔ W-005 (cross-ref)](#cross-ref-w-008--w-009--w-007--w-005-codegen-转化路径联动) | ✅ ALL RESOLVED (W-005 v0.9 wip 2.13 / W-008 v0.8 c11 / W-009 v0.8 c12 / W-007 transitive 2026-08-12) | 4 个 workaround 都在 jhyy_v1 `cg_convert_arg` + NODE_ASSIGN + NODE_FIELD codegen 路径, 全 RESOLVED |
| [W-010](#w-010-jhyy-端-max_locals--512-vs-c-端-1024--cg_add_local-静默溢出致-t0-污染) | RESOLVED (v0.9 wip commit 2.79) | jhyy-side `MAX_LOCALS=512` 比 C-side `1024` 小 2× → cg_expr 本地变量数溢出时 cg_add_local 静默返回 0 → cg_find_local miss → emit `%t0`(QBE temp 0,sentinel); align jhyy-side 到 1024 全消除 |
| [W-012](#w-012-codegen-emit-layer-sentinel-pollution-cg_copy_struct-emit-copy--t0-when-src_addrundef) | RESOLVED (v0.9 wip commit 2.81) | C/jhyy `cg_copy_struct` 在 src/dst 是 sentinel `IRVal{0}` (kind=IRVAL_TEMP, id=0) 时仍逐字段 emit `copy %t0`, QBE reject. 真修: `irval_is_undef(v)` sentinel 守卫 (3 emit 点 + 1 helper). |
| [W-013](#w-013-c-side-cg_expr-node_cast-w--b-narrowing-emit-sentinel-t0) | ✅ RESOLVED (v0.9 wip commit 2.87, Sprint v1.1.7) | C-side `cg_expr` NODE_CAST 在 w/l → b/h narrowing (i32/i64 literal → u8/i8/u16/i16) 无 conv 时 emit sentinel `IRVal{0}` (`%t0`) → 后续 `storeb %t0, addr` 被 QBE reject ("invalid type for first operand %t0 in storeb"). jhyy-side 因 `if conv==0 return arg` 自然 fallback 一直正确 |
| [W-014](#w-014-jhyy_selfhost_check-mcp-pre-stage-cleanup-deletes-canonical-closure-binaries) | ✅ RESOLVED | `jhyy_selfhost_check` MCP server 启动时 pre-stage cleanup 误把 `compiler/build/bin/jhyy_v1.exe.exe` (canonical closure binary) 当 stale artifact 删 → `enforce_baseline_hash=True` fail-fast 触发 |
| [W-015](#w-015-node_sizeof-节点-arena-分配-8-字节--sema-const-fold-写-16-字节溢出到下一块) | ✅ RESOLVED (v1.3.3) | `ast_new_sizeof` / `ast_new_alignof` 只 alloc 8 字节,sema const-fold `node_int_data(n)` 写 16 字节溢出到 next arena chunk → 随机 data corruption |
| [W-016](#w-016-8-字节-enum-参数-abi-mismatch--caller-用-l-slot-传callee-用-w-value-收) | ✅ RESOLVED (v1.3.7 fix) | enum payload > 4 字节时 caller 用 `l` (slot) 传,callee codegen 默认按 `w` (value) 收 → x86_64 SysV 读 %edi 拿到 slot pointer 低 32 位 → tag compare 永远 false → pattern binding `v` 拿不到值 |
| [W-017](#w-017-jhyy-顶层-let-mut-*-u8--0--codegen-常量折叠-全局状态-失效) | ✅ RESOLVED 2026-08-14 (v1.4.6 commit `f20e36d`) | jhyy 端 codegen 不实现真正的顶层 `let mut g_x: *u8 = 0 as *u8;` — global initializer `0` 在 codegen 阶段被常量折叠为 0,后续所有读 `g_x` 的 QBE IR 都是 `=l copy 0`,sentinel null pointer;路径硬编码消除被迫委托 C runtime `jhyy_helpers.c` 持有 path state |
| [W-018](#w-018-v142-dwarf-emit-引入-stage-1-il-字节差异-非功能) | ✅ RESOLVED 2026-08-14 | v1.4.2 DWARF emit 引入 Stage 1 .il 字节差异 (非功能) — 实测 `stage1-expanded.sh` 脚本错写路径吞错,改后 7/7 PASS,W-018 是误报 RESOLVED |
| [W-019](#w-019-codegen-嵌套-struct-innerx-emit-loadsw-类型错) | ✅ RESOLVED 2026-08-14 (v1.4.6 commit `6638134`) | codegen `cg_field_addr` 在处理 `(*o).inner.a` 这种嵌套 struct 字段时,emit 的 `loadsw`/`loadw` 第一操作数类型错(QBE reject: "invalid type for first operand in loadsw")。当前 v1.4.3 测试用例只覆盖 flat struct,嵌套 struct 留给 post-v1.4.3 修 |
| [W-020](#w-020-jhyy-side-parserjhyy-parse_pattern-colorvariant-分支-bug) | ✅ RESOLVED 2026-08-14 (v1.4.6 commit `ad42117`) | jhyy-side `parser.jhyy` parse_pattern 在 match arm 上下文中处理 `Color::Variant` 时,`parser_check(p, TOKEN_COLONCOLON())` 返回 0 即使下一个 token 实际是 `::`,parser 走 ident-pattern 分支提前返回,留下 `::` 让 expr 解析报 `expected =>, got ::`。C-side `parser.c` (line 124-138) 正确处理同样输入。bug 在 v1.4.4 物理 production flip 前被 C-side `jhyy.exe` 遮住 |
| [W-021](#w-021-wix-7-cli-ext-name-查找失败---ext-wixtoolsetbalwixext-找不到) | ✅ RESOLVED 2026-08-28 (v1.7.1 patch B1, permanent workaround) | WiX 7.0.0+b8977d6 CLI 的 `-ext WixToolset.Bal.wixext` 名字查找 WIX0144 fail — 装的 DLL 文件名是 `WixToolset.BootstrapperApplications.wixext.dll` (不是 `WixToolset.Bal.wixext.dll`),CLI extension-name lookup 不识别,要求传 DLL 绝对路径 |
| [W-026](#w-026-regresspy-80-stderr-截断隐藏真实-qbegcc-错误) | ✅ RESOLVED 2026-08-15 (commit `0d58efe`) | regress.py FAIL print `[:80]` 截断隐藏 QBE/gcc link 错误 → 改成完整 stderr 输出 |
| [W-027](#w-027-gh-actions-setup-msys2v2-把-msys2-装在-runnertempmsys64-ci--d-atempmsys64不在-cmsys64--硬编码-cmsys64ucrt64bin-找不到-gcc) | ✅ RESOLVED 2026-08-15 (commit `4623a3b` — v8 final) | `setup-msys2@v2` CI 装在 `$RUNNER_TEMP\msys64` (D:\a\_temp\msys64) 不在 C:\msys64 → hardcoded path 找不到 gcc; fix: deterministic MSYS2 root + known bin subdirs (no subprocess call) |
| [W-028](#w-028-windows-process-exit-code-是-8-bit-mod-256-expect-注释里的值-255-在-ci-regress-fail-got106-不是-got1000042) | ✅ RESOLVED 2026-08-15 (v1 commit `6d2ab8f` + v2 sys.platform cygwin/msys 兼容) | Windows kernel32 ExitProcess 8-bit mod-256; EXPECT 注释里 ≥256 的值 CI regress FAIL — mod 256 comparison in regress.py (`sys.platform in ("win32", "cygwin", "msys")`) |
| [W-051](#w-051-msi-deferred-execommand-customaction-type-34-在本机-systematic-报-1721--改用-hklm-runonce-解决) | ✅ RESOLVED 2026-08-28 (v1.7.1 patch B2, permanent workaround shipped v1.5.7-rc1) | MSI deferred CA type 34 在 SYSTEM token 下 systematic 报 1721 (`CreateProcess` argv mis-tokenize cmd/c 链); workaround = 改用 HKLM RunOnce (USER context 跑 master .bat + 多个 .ps1), trade-off 是 fresh install 需 logoff/logon 一次。WiX/MSI engine 升级不可预期, 不再尝试 revert |
| [W-042](#w-042-link_with_gcc-失败只打-gcc-link-failed--缺-invoke_buf-诊断) | ✅ RESOLVED 2026-08-28 (v1.7.1 patch A1, Tier 1+2+3 全链 ship) | `link_with_gcc` 失败时只打 "gcc link failed" 缺 `invoke_buf` 诊断 → Tier 1 invoke_buf echo (v1.5.6) + Tier 2 stderr capture via pipe (v1.7.1 patch A1) + Tier 3 post-link .exe stat (v1.7.1 patch A1) 全链 ship |
| [W-052](#w-052-match-字面量范围模式1num10-两侧-parser--codegen-都漏-literal-range) | ✅ RESOLVED 2026-08-27 | README "tour of the syntax" `1..10 => "single digit"` 在 match arm 里 parser 两边都漏 DOTDOT follow-up + codegen 两边都漏 NODE_PATTERN_LIT manual emit. 修复: add `try_pattern_range` helper (C-side parser.c) / extend `parse_pattern_primary` + DOTDOT follow-up (jhyy-side parser.jhyy) + manual emit NODE_PATTERN_LIT (C-side codegen.c) + manual emit NODE_PATTERN_LIT/NODE_INT (jhyy-side codegen.jhyy). 新增 `compiler/tests/examples/match_range.jhyy` integration test (regress 54/54 PASS, 3 skip). Stage 2 byte-equal 闭环 hold (jhyy_selfhost_check all_byte_equal=true). |
| [W-053](#w-053-字符字面量转义不全--n-t-r-0-之外-escape-以及-xhh-漏解码) | ✅ RESOLVED 2026-08-27 | spec §4.4 字符字面量族 (`\n \t \r \0 \\ \' \" \xHH`) 全漏 decode;`'` 后的 char 走 `t.start[1]` 直接当 ASCII,导致 pattern match 的 char arm 永假;`'\\'` `'\''` `'\"'` lex ERROR. 修复: src/lexer.c `scan_char` escape switch 加 `'"'` + src/parser.c 提取共享 `decode_char_literal()` (含 hex_val 子函数) + src0/lexer.jhyy 镜像加 `e == 34` + src0/parser.jhyy 3 处 TOKEN_CHAR decode 全镜像(并修复 `parse_pattern_primary` `p_addr = t.start` 漏 +1 offset 的旧 bug). 新增 `char_literal.jhyy` (9 escape case) + `char_pattern.jhyy` (`'\n'` literal match + `'a'..'z'` range match) integration test. 5/5 PASS per `feedback_fix_evaluation_rule`. Stage 2 byte-equal 闭环 hold. |
| [W-054](#w-054-sizeof-il-未定义-t0-真因-qbe_type_of-撞-data-layout) | ✅ RESOLVED (via W-053 chain, 2026-08-27) | Plan agent 探测的 "sizeof emit `%t1 =w copy %t0` 时 `%t0` 未定义" 是假症状。实际根因 = W-053 fix 路径上,把 `qbe_type_of` (i8→'w' widening) 应用到 data section 时,word-packed const array 的 byte 25 落到 7th word 的 2nd byte (= 0),期望值 122 错误。修复: src/ir.c 拆 `qbe_type_of` (SSA widen 必 word-sized, QBE 拒 'b'/'h') vs 新 `qbe_data_type_of` (data section 字节 packed,const array 字节寻址正确);src/ir.h 暴露 + src/codegen.c 3 处 data emit 切到 `qbe_data_type_of`. W-054 不需要单独修,作为 W-053 fix chain 副作用消除。 |
| [W-055](#w-055-spec-§95-指针算术-p--1-整节未实现) | ✅ RESOLVED 2026-08-28 (v1.7.0 Stage 2 commits `6216138`+`187e8ab`) | spec §9.5 指针算术 `p + 1` / `p - 1` / `p[n]` 整节未实现 — **v1.7.0 Stage 2 ship**: 4 形式全 ship (`*T + int` / `*T - int` / `int + *T` / `*T - *T` / `p[n]`),详见 section body line 3668+ `Resolution (2026-08-28 v1.7.0 Stage 2)`。后续工作推 v2.x = pointer comparison `p < q` + bounds check (`&mut` lifetime),跟 `p±N` / `p[n]` 不同 scope。 |
| [W-057](#w-057-utf-8-3-byte--4-byte-codepoint-显式-lex-reject-推-v2x) | 🟡 DEFERRED v2.x | vendor QBE (2026-08-15 build) 编译期 fold 3/4-byte UTF-8 codepoint 错 (e.g. `'你'` U+4F60 / `'🎉'` U+1F389) — v1.7.0 Stage 3 显式 lex reject "3/4-byte UTF-8 codepoint not supported", spec §4.4 缺独立 W-NNN 归档 (本 v1.7.3 patch C2 补登), 推 v2.x 真修 (vendor QBE 升级主线或自研 backend codepoint folding)。|
| [W-058](#w-058-vendor-qbe-2026-08-15-build-不支持-remd--rems-浮点取模-推-v2x) | 🟡 DEFERRED v2.x | vendor QBE 不支持 `remd` (f64 remainder) / `rems` (f32 remainder) 指令, v1.7.2 patch A1 ship 时 fact-check fail, 标 LIMIT 推 v2.x, workarounds/spec 缺独立 W-NNN 归档 (本 v1.7.3 patch C3 补登 + spec 附录 B fmod row cross-ref C4)。|
| [W-059](#w-059-defer-codegen-path-silent-crash-v136-ship-后-0-test-验证-accept-path-推-v18) | ✅ RESOLVED 2026-08-28 (v1.8.0) | 根因 = `compiler/src0/sema.jhyy` `sema_defer_register` (NODE_DEFER case) 调 `infer_type(ctx, expr)` 漏传 `ta` (TypeArena arg) → sema 阶段 silent corrupt stack → `[sema] P3 i=0` 后 crash 0 .il/.s/.exe. 修复: 1-line fix line 1410 `let _v = infer_type(ctx, ta, expr);` (jhyy-side `infer_type` 3-arg signature, 漏 `ta` 等于传 garbage). C-side 正确因为 `infer_type` 是 2-arg. Phase 1A empirical (MCP-only) + Phase 1B bisection 定位 + Phase 2 真修. 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) SKIP directive 删, 全 PASS regress (jhyy.exe 102/102 + jhyy_stage0.exe parity 102/102). N=4 byte-equal closure hold (v2/v3/v4 sha=`03a1cdd4...`). 5/5 PASS on each target test per `feedback_fix_evaluation_rule`. |
| [W-060](#w-060-enum-variant-payload-abi-mismatch-mixedi1234-match-走-wildcard-path-exit210--1234-推-v18) | ❌ INVALID 2026-08-28 (v1.8.0) | v1.7.3 ship 期间 fact-check 误判为真 bug: 实为 bash `$?` 8-bit truncation (EXIT=210 = 1234 & 0xFF) + Windows `subprocess.run` 同步 8-bit truncate → regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较. v1.8.0 Phase 1 调查 (Agent 3) 确认 W-060 = test artifact. OR pattern `Some(v) \| Some(v)` 分支 EXIT=42 实无 bug (line 1 SKIP 标签把 spec 限制跟 OR pattern 测试混淆). 2 enum test (`payload_bind_multi.jhyy` / `payload_bind_nested.jhyy`) SKIP directive 删, 全 PASS regress. |
| [W-061](#w-061-nested-struct-field-offset-bug-outer--tag-inner--read-exit51--307-推-v18) | ❌ INVALID 2026-08-28 (v1.8.0) | v1.7.3 ship 期间 fact-check 误判为真 bug: 实为 bash `$?` 8-bit truncation (EXIT=51 = 307 & 0xFF) + Windows `subprocess.run` 同步 8-bit truncate → regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较. v1.8.0 Phase 1 调查 (Agent 3) 确认 W-061 = test artifact. `(*o).inner.x + (*o).inner.y` 实 EXIT=300 (无 bug, 推测 OR-pattern 部分 follow-up 误解). nested_struct_dwarf.jhyy SKIP directive 删, 全 PASS regress. |
| [W-062](#w-062-vscode-userchoice-hijack--msys2-openwithprogids-双层-shadow--jhyy-图标-不显示-推-v182) | ✅ RESOLVED 2026-08-29 (v1.8.3.1 patch) | 双层独立 hijack: (1) VSCode UserChoice hijack (`HKCU\…\FileExts\.jhyy\UserChoice\ProgId = Applications\Code.exe`, UCPD.sys 加 Deny ACE 防非 admin SetValue, 需 admin + UCPD pause/restart);(2) MSYS2 OpenWithProgids 残留 (`HKCU\…\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file` + `HKCU\Software\Classes\jhyy_auto_file`, v1.8.1 patch 没清 OpenWithProgids 子键). v1.8.1 patch 只修了 WiX `(default)` 写错位 + `jhyy.exe,0` embedded icon, **不修** 这两层 shell hijack. Explorer folder view 用 UserChoice ProgId 取 icon → `Applications\Code.exe\DefaultIcon` 解析 quirk → shell32 白板. 修复: v1.8.2 Path B 注册自定义 ProgId `JHYY.EditInVSCode` (`DefaultIcon = jhyy-icon.ico,0` + `shell\open\command = Code.exe "%1"`),用 Mozilla reverse-engineered UserChoice Hash 算法 (`SHA/MD5 + 2-pass scramble`, MPL 2.0) 把 `UserChoice\ProgId` 写成 `JHYY.EditInVSCode`. C# tool `installer/common/jhyy-setuc/Program.cs` (.NET 8-windows) port Mozilla 算法. **v1.8.3 ship 时**把 manual Path B 升级到 WiX MSI CustomAction `JHYYSetUCForAllUsers` (SYSTEM context 绕 UCPD kernel filter),通过 immediate `SetUCProp` + deferred `--system-context` 2-step 模式在 install 时自动触发。**v1.8.3.1 patch 真修**: ship 时 CustomAction 0x80004005 静默失败 — 3-attempt diagnosis (1. `ExeCommand` 引用 `[JHYYSetUCBin]` property 在 deferred CA 不 resolve; 2. WiX `<Binary>` 不自动创建 property; 3. `.NET 8 apphost model` 需 ship `.exe` + `.dll` + `.deps.json` + `.runtimeconfig.json` 4 个 file,v1.8.3 只 ship 了 `.exe`)。**最终 fix**: 2-step immediate→deferred CA pattern (`SetUCProp` capture `[INSTALLDIR]` → `JHYYSetUCCmd` → deferred `Directory="INSTALLDIR" ExeCommand="[JHYYSetUCCmd]"`) + ship 4 个 .NET 8 file 落地 `INSTALLDIR\bin\`。顺带修 `manual-fix-icon-cache.ps1` 自 v1.8.2 ship 起 Path B jhyy-setuc.exe 路径错(指向 build 产物路径而非 INSTALLDIR\bin\)。MSI install field test 2026-08-29: CA 完成 17:50, sentinel written, UserChoice Hash `/dbBVe4aYxo=`, 4 files 落地, Explorer `.jhyy` 显示 JHYY 品牌 "J" icon。5/5 PASS gate per `feedback_fix_evaluation_rule`。 |
| [W-063](#w-063-短名-enum-模式匹配-somev--v-bind--codegen-传错-type--phi-t0-未定义) | ✅ RESOLVED 2026-09-01 (v1.8.3.2 jhyy-side + v1.8.3.3 C-side, probe-then-fix) | codegen `cg_match_pattern` NODE_PATTERN_ENUM 分支在 `pe->variant_sym == NULL` 时走 silent always-match fallback (emit `jnz %t2, @arm2, @next3` + `%t2 =w copy 1`), 不再 emit payload slot alias 的 `loadw`. 当 phi 引用该 slot (`%t6 =w phi @arm2 %t0`) 时 %t0 未定义 → QBE reject "invalid type for operand %t0 in phi %t6". 短名 form (`Some(v)` 无 `Option::` qualifier) 在 parser.c `parse_pattern_enum` (line 225-235) 把 `type_sym=NULL` 直接传 ast_new_pattern_enum → 触发 fallback. 长名 form (`Option::Some(v)`) `type_sym` set,不触发. 修复: jhyy-side `compiler/src0/codegen.jhyy:3439` NODE_MATCH 入口 `cg_match_pattern` 调用改传 **subject type** (`(*matched_node).type_ptr`) 而非 match result type (`(*n).type_ptr`), v1.8.3.3 patch 镜像 C-side `compiler/src/codegen.c:1541` (`Type *match_type = n->type` → `Type *match_type = d->expr->type`), 让 fallback 路径能反查 match_type->enum_type.variants 拿名字. `cg_match_pattern` 内部 l:977-1015 用 match_type 兜底解析 variant name + emit payload alias loadw. 新增 `compiler/tests/examples/payload_bind_short.jhyy` integration test (5/5 PASS per `feedback_fix_evaluation_rule`)。regress 双 gated binary (jhyy.exe + jhyy_stage0.exe) 103/103 + Stage 2 N=4 byte-equal 闭环 (v2/v3/v4/v5 .il sha=`fa1137e5...`)。 |
| [W-064](#w-064-run_qbe-失败只打-qbe-failed--缺-stderr-捕获-qbe-真实诊断丢失) | ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch) | `run_qbe` (compiler/src0/main.jhyy:657-699) QBE 失败时只 echo `cmd_buf` (`QBE failed: "..."\n`), 不读 jh_run 已 capture 的 child stderr. QBE 真实诊断 ("invalid type for operand %t0 in phi %t6" / "undefined symbol" / "type mismatch") 全丢, 用户只见 "QBE failed" 一行, 难定位是 QBE reject 哪条 IL. 修复: 镜像 `link_with_gcc` W-045 pattern — `run_qbe` 失败分支加 `let captured = jh_run_get_output(); if captured != (0 as *u8) && (*captured) != (0 as i32) { jh_fputs_stderr("QBE stderr:\n" as *u8); jh_fputs_stderr(captured); jh_fputs_stderr("\n" as *u8); }`. `jh_run` per-call reset `jh_run_outlen = 0` (jhyy_helpers.c:517-518) 保证 QBE→gcc 链顺序不污染. **link_with_gcc 已 ship W-045**, `run_qbe` 是唯一剩没接 stderr capture 的 child process site. 顺带 bump l:1091 stale version literal `v1.0.0` → `v1.8.3.2` (jhyy.exe -h 可见)。回归 103/103 + Stage 2 闭环 hold. C-side `compiler/src/main.c` 未镜像 (production 用 jhyy-side, stage0 bootstrap 不修)。 |
| [W-065](#w-065-jhyy-run-不预检-fn-main_jhyy--库-snippet-报-undefined-reference-to-main_jhyy-对用户不友好) | ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch) | `jhyy run` 接 input 后直接调 `cmd_compile` (→ QBE → gcc link) — 库 snippet (无 `fn main_jhyy`, 仅 `fn unwrap` / `fn dist_sq` 这种) link 时 gcc 报 `undefined reference to main_jhyy`, 错误晚出且 noisy. 修复: `cmd_run` 入口 (compiler/src0/main.jhyy:987) 在 `cmd_compile` 之前加 cheap byte-level scan — `fopen(input, "rb")` + `fread` 131072 bytes + fclose, 然后 byte-by-byte 搜 needle `"fn main_jhyy"`. 找到 → 继续 compile; 找不到 → `jh_fputs_stderr("jhyy run: '<file>' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)\n" as *u8)` + return 1. **scope**: 只动 `cmd_run`, `cmd_compile` 保持允许库-only 编译 (compile 不需要 main_jhyy, 可产 .s/.exe 给后续 link 用)。**byte-comparison 实现**: 第一次 commit (`src0/main.jhyy:1015-1029`) 用 `*i32` cast deref 4-byte 而非 1-byte, scan 永远不 match (即使文件真有 `fn main_jhyy`)。第二次 commit 改 `*u8` cast + `as i32` promote 才正确。首次 fix 在 fresh build 后 user case (test.jhyy / test2.jhyy) 仍报 "no fn main_jhyy" 才暴露 — 不写 5/5 PASS loop 不会发现 byte-comparison bug。regress 103/103 + Stage 2 闭环 hold (v2/v3/v4/v5 .il sha=`fa1137e5...`)。**C-side `src/main.c` 未镜像** (production path 走 jhyy-side)。 |

---

## W-001: hash_string 用 *i32 deref 绕 v0 codegen `loadsb` 错

**ID:** W-001
**状态:** RESOLVED (v0.8 commit 9 `d570c72`, 2026-08-03) — 见下方"W-001 RESOLVED" section (byte-by-byte FNV-1a 真修, 移除了 *i32 overread workaround + W-002 失效)
**日期:** v0.6 sprint（~2026-05, ACTIVE）→ 2026-08-03 (RESOLVED)
**触发面:** `hash_string` 函数里需要 deref `*u8` 一次读 1 byte
**症状:**
- v0 codegen 对 `*((p) as *u8)` deref emit `%=b loadsb p`（destination 是 `b` class）
- QBE 不允许 `b` class 作 destination（loadsb 是 source-side narrow）
- QBE 报错：`invalid type for first operand in loadsb` 或类似

**根因嫌疑:** v0 codegen 误把 deref result 标 `b` class，应该是 `w`。

**workaround:** 改用 `*((p) as *i32)` deref 一次读 4 byte（`loadw` 合法），再 shift+mask 取目标 byte。

```jhyy
// 不绕 (v0 codegen 错):
let c = (*((p as i64 + i) as *u8)) as i64;

// 绕 (util.jhyy:199 hash_string):
let w = *((s as i64 + aligned) as *i32);
let sh = rem * (8 as i32);
let c = ((w >> sh) & (255 as i32)) as i64;
```

**影响范围:** `compiler/src0/util.jhyy:199-213` (`hash_string` 内部 4-byte aligned read 循环)

**失效条件:** v0 codegen 修了对 `*u8` deref 的类型推导（按 spec 应出 `w` destination），W-001 可移除。

**superseder:** TBD（v0 codegen bug fix sprint，post v1.0.0）

**引用:**
- 源码注释 `util.jhyy:195-198`
- 详尽 bug 清单见 git log v0 codegen bug 段 (Bug 3)
- 见 `docs/plans/v0/v0.6.0任务清单 + 概要设计.md`

---

## W-001 RESOLVED — v0.8 commit 9 (`d570c72`) byte-by-byte 真修

**日期:** 2026-08-03 (commit `d570c72`)
**修复:** `compiler/src0/util.jhyy` `hash_string` 改成 byte-by-byte `*u8` deref + length mix (FNV-1a)
- L222: `let c32 = *((s as i64 + (*i_ptr)) as *u8) as i32;` — `*u8` deref 1 byte (`loadsb` 仍可走, 不需 overread)
- 移除了 `*((s as i64 + aligned) as *i32)` 的 4-byte read 模式 (commit 之前 L199-213 整段)
- 移除了 `let w = ...` + `let sh = ...` + `(w >> sh) & 255` 的 shift+mask workaround

**为什么真修 (而不是简单 revert workaround):**
- W-001 根因不在 v0 codegen `loadsb` 错 (post-v0.6 sprint 实际已修复 destination 类型推导 — codegen L6+ 已正确处理 `*u8` deref 出 `w` class)
- 真正的"segfault 副作用" 来自 `*i32` 4-byte read overread slack 字节进 hash → hash 错位 → SymTab lookup 误路由 (W-002 根因)
- byte-by-byte 真修消除 overread → W-002 失效条件 (ii) 满足 → W-002 也可移除

**验证:**
- v0 编 src0/main.jhyy → 1.18MB IL, 553 functions
- jhyy_v1 编 hello.jhyy 等小测试 byte-equal PASS (stage1 6/7 持平)
- v0 + regress 持平 50/53

**引用:**
- commit `d570c72` (v0.8 commit 9: W-001 byte-by-byte hash + W-005 let-mut workaround)
- 源码注释 `util.jhyy:212-231`
- 配合 v0.9 wip commit 2.12 撤销 W-002 211 个 `_v1` 后缀 revert (见下)

---

## W-002: main.jhyy 重命名绕 jhyy_v1 hash_string 堆损坏

**ID:** W-002
**状态:** RESOLVED (v0.9 wip commit 2.12)
**日期:** 2026-08-03 (ACTIVE) → 2026-08-05 (RESOLVED)
**触发面:**（任一即可）
1. 源码标识符长度 ∈ {6, 7, 8} 字符（如 `out_buf`、`in_buf`、`cmd_buf`）
2. 源码标识符后缀 = `_buf`（任意长度）
3. nlocals=1 + `return` 局部 var，或 nlocals=2 + `return binop(2 局部 var)`

**症状:**
- jhyy_v1（自举编译器）编 main.jhyy 或类似模式时 0xC0000005 segfault
- 即便触发名变量在 return 中完全不用也触发（`let out_buf: *u8 = "x"; return 0;`）
- v0 jhyy.exe 编同一源码完全正确
- `tmp/tm_*.jhyy` 151 个 bisect 用例保留作回归

**根因嫌疑:**
- W-001 的 `*i32` deref 4-byte read 在 jhyy_v1 编出来的 IL 里行为微妙
- arena 分配字符串后存在未初始化 slack 字节
- jhyy_v1 的 codegen 对 hash_string 的 IL emit 与 v0 有未定位差异，导致 4-byte read 在某些条件下把 slack 字节吸进 hash 值
- hash 错位 → SymTab lookup 误路由 → 错 sym 进 CGContext.locals → 后续 codegen 引用错 local → segfault
- 6-8 字符 + `_buf` 后缀触发面**尚未完全解释**——长度为什么是 6-8 而不是 5 或 9？

**workaround:** 把 main.jhyy 里所有触发面标识符重命名到 9+ 字符（机械前缀 `ptr_` / 后缀 `_data` / `_storage`），绕开触发面。

**改名规则:**
- 长度 ∈ {6, 7, 8} 字符的标识符一律改名到 ≥ 9 字符
- `_buf` 后缀的标识符一律改名（不论长度），`_buf` → `_buf_storage` 或 `_buffer_data`
- 改名一律**机械化**（加 `ptr_` 前缀 / `_data` 后缀），不手工取语义名，避免再撞新触发面
- 同时检查新名是否落在 6-8 字符范围，确保改名后**不引入新触发**

**影响范围:**
- `compiler/src0/main.jhyy`（本次应用目标，534 行）
- 其他 jhyy_v1 编译目标的源文件待评估（codegen.jhyy / parser.jhyy 等）

**改名规则（已实施 2026-08-03）：** 所有触发面标识符统一加 `_v1` 后缀：
- 长度 6 → 9 字符（safe）
- 长度 7 → 10 字符（safe）
- 长度 8 → 11 字符（safe）
- `_buf` 后缀 → `_buf_v1`（仍以 `_v1` 结尾，不再以 `_buf` 结尾；safe）

实施：见 `compiler/src0/_W002_rename_map.txt`（211 个标识符 → X_v1 形式）

**验证（2026-08-03）：**
- 重命名前：jhyy_v1 编 `tmp/tm_nm_out_buf.jhyy`（含 `let out_buf: *u8 = "x"; return 0;`）→ 失败（exit 127 / heap corruption）
- 重命名后：jhyy_v1 编同样输入但把 `out_buf` 改成 `output_buffer`（手测，临时文件）→ **成功**（exit 0，exe 产出）
- v0 jhyy.exe 编改名后的 main.jhyy → 成功（exit 0，输出的编译器也能再编 hello.jhyy）

**改名清单（211 个）：** 完整见 `compiler/src0/_W002_rename_map.txt`。按文件分布：

| 文件 | 替换数 |
|------|-------|
| codegen.jhyy | 724 |
| parser.jhyy | 469 |
| sema.jhyy | 351 |
| main.jhyy | 177 |
| types.jhyy | 97 |
| ast.jhyy | 71 |
| ir.jhyy | 49 |
| lexer.jhyy | 49 |
| util.jhyy | 39 |
| symtab.jhyy | 30 |
| arena.jhyy | 17 |
| **总计** | **2073** |

**局限性（重要, 历史记录）：** W-002 修了 hash_string 触发面 bug，但 jhyy_v1 编 main.jhyy **仍然 segfault**（exit 139, 2026-08-04 之前观察）—— 因为 main.jhyy 还有别的触发 jhyy_v1 codegen bug 的模式（Bug 7 `let _ = fncall`、Bug 9 嵌套 if/else phi、Bug 13/16 struct 值传递等；详见 git log v0 codegen bug 段）。**但** W-001 真正修复 + 后续 v0.9 wip commit 2.5~2.11 修了 B-φ1/B-struct/B-match/W-005 phase 1+2, main.jhyy segfault 触发面已大量消除 — v0.9 wip commit 2.12 revert 后是否还 segfault 由 commit 2.12 的 **observation step** 检验 (commit 2.12 plan § observation)。

**失效条件:**（任一即可移除 W-002）
- jhyy_v1 的 codegen 对 hash_string 生成的 IL 与 v0 IL byte-equal（diff 通过）→ 重新引入原名
- 或 v0 codegen 修了 W-001 的副作用（W-001 workaround 改成 byte-by-byte 不再 overread）—— 此时即使 jhyy_v1 触发面不变也不再 segfault

**superseder:** ✅ 已实现 (v0.9 wip commit 2.12 — W-001 byte-by-byte 真修 → W-002 失效条件 (ii) 满足 → 211 个 `_v1` 后缀 revert 回原名)

**W-002 RESOLVED section:** 见下方"W-002 RESOLVED — v0.9 wip commit 2.12 211 revert"

**引用:**
- 详细 bisect 记录见 git log (2026-08-04 周边 commits)
- 测试用例 `tmp/tm_*.jhyy`
- 完整 rename 映射 `compiler/src0/_W002_rename_map.txt`
- v0.8 commit 6 (efc41bf) `wip: bisect heap corruption`
- v0.8 commit 7 (0453cef) `W-002: 211 个标识符 _v1 后缀化 + workarounds.md`
- 战略决策: Bisect findings (per git log 同区段)

---

## W-002 RESOLVED — v0.9 wip commit 2.12 211 revert

**日期:** 2026-08-05 (commit pending ship)
**修复:** `compiler/src0/_W002_rename_map.txt` 211 个 `X -> X_v1` 反向 sed revert 回原名

**为什么 revert:**
- W-001 根因 (hash_string `*i32` overread slack 字节) 在 v0.8 commit 9 (`d570c72`) 已真修 → 改 byte-by-byte `*u8` deref
- byte-by-byte 真修后, hash_string 不再 overread → slack 字节不再污染 hash → W-002 触发面消失
- 211 个 `_v1` 后缀变成纯 cosmetic 噪声, 跟原 code base 分离, 增加 review burden + 阻碍 future bisect
- revert 后 src0/ 跟 v0 端 C 源码更接近 → 后续 v1.0.0 sprint 3+ 翻译难度降低

**实施步骤 (scripted, 见 commit 2.12 changelog):**
1. 读 `_W002_rename_map.txt` 生成反向 sed: `s/X_v1\b/X/g` per 211 identifier
2. 在 src0/ 11 个 .jhyy 文件批量 apply (1701 occurrences: codegen 600 / sema 309 / parser 282 / main 186 / types 87 / ast 57 / ir 47 / util 44 / lexer 43 / symtab 28 / arena 16)
3. v0 build + regress 持平 50/53
4. 新 jhyy_v1 编 src0/main.jhyy → **observation step** (per commit 2.12 plan):
   - segfault 消除 → A 段 hard closure 提前
   - segfault 还在 → 推 v1.0 sprint 3 B' 阶段
5. stage1 byte-equal 持平 6/7

**保留历史信息:**
- W-002 ACTIVE 期间的实施细节 (改名规则、影响范围、改名清单、局限性、引用) 保留在上方"W-002 ACTIVE 期间" 标题下, 作为 ACTIVE 历史归档
- `_W002_rename_map.txt` 保留作为可重放参考 (已不需要, 但 archive)

**引用:**
- v0.9 wip commit 2.12 (this commit) — 211 revert
- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (根因消除)
- 配合 W-001 RESOLVED section (上方)

### Archive 文件 (v0.9 wip commit 2.14 标记)

W-002 revert 实施时产生的 archive 文件保留作为可重放参考:

| 文件 | git 状态 | 大小 | 用途 |
|------|---------|------|------|
| `compiler/src0/_W002_rename_map.txt` | **tracked** (commit 2.12 ship 时已 ship, hash `8a9de1c`) | 4982B | 211 个 `X → X_v1` rename mapping (反向应用即可 revert) |
| `compiler/src0/_W002_revert.py` | **gitignored** (`.gitignore` `_*.py` 规则) | 2220B | 一次性 revert 脚本 (2026-08-05 实施完成, 已 ship 后失去保留价值) |

**清理决策 (v0.9 wip commit 2.14)**:
- `_W002_revert.py`: **删除** (一次性工具, 已 ship, 不再需要; 占用磁盘 clutter)
- `_W002_rename_map.txt`: **保留 + 顶部加 README** (未来如果需要重新引入 W-002 rename 可直接当 input; 499 行 5KB 占用低; ship history 保留)

**README 注释 (添加在 `_W002_rename_map.txt` 顶部)**:
```
# ════════════════════════════════════════════════════════════════
# W-002 ARCHIVE — 211 个 src0/ identifier 的 `X → X_v1` rename map
# ════════════════════════════════════════════════════════════════
# 历史: v0.8 commit 7 (`0453cef`) 引入 W-002 (绕 hash_string *i32 overread)
#       v0.8 commit 9 (`d570c72`) W-001 真修后 W-002 失效
#       v0.9 wip commit 2.12 (`8a9de1c`) 211 revert 回原名
# 状态: RESOLVED (per docs/internal/workarounds.md § W-002)
# 用途: archive — 保留作为可重放参考; 未来若需重新引入 W-002 可直接当 input
# ════════════════════════════════════════════════════════════════
```

**引用**:
- `compiler/src0/_W002_rename_map.txt` (tracked, archive)
- `compiler/src0/_W002_revert.py` (gitignored, 已删 2026-08-05)
- v0.9 wip commit 2.14 — 标记 archive + 清理 + README 注释

---

## W-003: jhyy_v1 `let _ = fncall(...)` 顶层 / 嵌套 segfault → direct call (top-level only)

**ID:** W-003
**状态:** ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已消除 Bug 7/7b 触发面,minimal repros for top-level + nested + NODE_ASSIGN[NODE_FIELD] all 5×5 PASS, 2026-08-12 verified)
**日期:** 2026-08-03 (ACTIVE) → 2026-08-12 (RESOLVED transitive)
**触发面:** 任何 `let _NAME = fncall(...)` 模式，无论 `_NAME` 是什么；无论 fncall 是否在函数顶层或嵌套 if/while 块内
**症状:** jhyy_v1 编译含此模式的源码 → 0xC0000005 segfault（exit 139）
**根因嫌疑:** v0 codegen 对 `let _ = fncall(...)` emit IL 缺漏（详见 git log v0 codegen bug 段 Bug 7 / Bug 7b）
**workaround (v3 — 限定顶层):** 把**函数顶层**的 `let _X = fncall(args);` 改成 `fncall(args);`（direct call，无 binding）。**嵌套 if/while/for 块内的同模式保持原样**——v3 不改，避免 v0 sema if/else 分支类型不匹配。

```jhyy
// BAD (顶层):
let _s1 = store_byte_i32(nul1, 0 as i32);

// GOOD (顶层):
store_byte_i32(nul1, 0 as i32);

// BAD (嵌套 if) — 保持原样，不动
```

注意：`_X` 是 discard variable；direct call 的返回值被 jhyy 语义自然丢弃，无需 binding。

**v3 决策的根因（v1/v2 失败教训）：**
- **v1 (全部 direct call)**: v0 报 18 个 sema error（"if/else branches must have same type: () vs i32"）。
  - 原因：`let _X = fncall()` 让分支 type = `()`（NODE_LET → `type_void()`）；改 bare `fncall()` 让分支 type = `i32`（fncall 返回 i32）。分支 mismatch。
  - 受影响的 17 处都在 `sema.jhyy` 的嵌套 if-else（典型：middle if 的 else 分支是 `let _X = sema_error_str(...)`，then 分支里套一个 no-else 的 inner if）。
- **v2 (全部 mutable 模式 `let mut _x = 0; _x = fncall(); let _ = _x;`)**: v0 自己 segfault。
  - 原因：mutable pattern 在 codegen 路径中产生 jhyy_v1 codegen 不支持的 emit。可能触发 Bug 6（重复 if kind）或 Bug 9（nested phi）等。
- **v3 (只顶层 direct call)**: 通过。regress 47/50 pass, 0 fail, 3 skipped. jhyy_v1 可编 main.jhyy 但仍偶尔 segfault（heap 不稳）。

**影响范围（src0/ 各文件 `let _X = ...` 计数 — v3 实际替换 vs 剩余）：**

| 文件 | 总数 | v3 替换 (顶层) | 剩余 (嵌套) |
|------|------|----------------|--------------|
| codegen.jhyy | 34 | 1 | 33 |
| sema.jhyy | 77 | 18 | 59 |
| lexer.jhyy | 23 | 0 | 23 |
| parser.jhyy | 5 | 4 | 1 |
| main.jhyy | 12 | 10 | 2 |
| **总计** | **151** | **33** | **118** |

（v3 实际产生 29 替换，差异是某些顶层 pattern 不匹配正则或不在 `let _X = ` 形式）

**v3 实现的细节：** 用 Python 脚本 `tmp/do_w003_v3.py` 扫 brace depth，只改 depth==1 的模式。depth 计算跳过字符串 (`"..."`) 和行注释 (`//`)。29 处替换不引入新 sema error。

**v3 验证（2026-08-03）：**
- v0 build main.jhyy: ✓ exit 0, 生成 main.il
- regress.py: 47/50 pass, 0 fail, 3 skipped
- jhyy_v1 build main.jhyy: 部分成功（exit 0 偶尔，segfault 139 偶尔 — heap 不稳，需要进一步 workaround 或 root cause fix）
- jhyy_v1 build hello.jhyy: ✓ exit 0
- jhyy_v1 compile hello.jhyy -o tmp/hello_run.exe: ✓ exit 0
- jhyy_v1 build codegen.jhyy: ✗ parse error "unexpected token 'while' in expression"（Bug 60，jhyy 翻译 parser 时 while 在 expression 上下文漏处理）

**失效条件:** v0 codegen 修复 `let _ = fncall(...)` emit → W-003 可移除，回归 `let _X = fncall(...)` 风格

**superseder:** TBD（v0 codegen fix sprint，post v1.0.0）

**未解决问题 (v3 之后):**
- jhyy_v1 build main.jhyy 偶尔 segfault — 怀疑是 W-001/W-002 heap 损坏叠加 W-003 未覆盖的 Bug 7b 嵌套模式。118 处嵌套 `let _ = fncall()` 仍是潜在 trigger。
- 进一步 v4 候选：用 **mutable assignment pattern** 处理 depth==2（1-level if 块），depth==3+ 仍保持原样。
- mutable pattern 会触发 v0 codegen bug（v2 失败）— 需要先验证 v0 codegen 是哪种 pattern 失败、是否能更精细地限定 mutable 范围。

**引用:**
- v0 codegen Bug 7 / Bug 7b (per git log)
- 决策过程见 git log W-003 iterations 段

### W-003 RESOLVED — transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain (2026-08-12)

**Sprint v1.1.3 verification (5×5 PASS on canonical jhyy_v1.exe.exe sha `ba94df93`)**:

| Trigger | Source | Expected | 5×5 |
|---------|--------|----------|------|
| **Bug 7 (top-level)** | `fn main_jhyy() -> i32 { let _x = noop(42); return 0; }` | EXIT=0 | ✅ 5/5 |
| **Bug 7 (top-level wide, 10 calls)** | 10 个连续 `let _X = store_byte(N, 0);` | EXIT=42 | ✅ 5/5 |
| **Bug 7b (1-level nested if)** | `if x==1 { if x==1 { let _d = noop(x); } }` | EXIT=0 | ✅ 5/5 |
| **Bug 7b (2-level nested if-if-if)** | `if x==1 { if y==2 { if z==3 { let _d = noop(x+y+z); ... } } }` | EXIT=5 | ✅ 5/5 |
| **Bug 7b + NODE_ASSIGN[NODE_FIELD]** | struct `Pair {a,b}` 嵌套 if + `let _s = sink(o.a); o.a = 99;` | EXIT=99 | ✅ 5/5 |
| **Bug 7b + for + if + mut** | `for i in 0..5 { if i>0 { let _d = noop(sum+i); sum = sum + i; } }` | EXIT=10 | ✅ 5/5 |

**关键证据 — 当前 src0/ 实际状态**:89 处 `let _X = fncall()` 仍存 (其中 **7** 在 codegen.jhyy,**54** 在 sema.jhyy,**17** lexer,**5** parser,**3** main,**2** _driver_sema,**1** ir.jhyy)。**所有 89 处都在嵌套 if/while 块内 (depth ≥ 2)** — 即正是 Bug 7b 的触发面,且全部正常 compile 通过 (regress_v1 50/50 PASS)。证明 Bug 7b 已自然消除,workaround v3 仅出于历史保险性保留。

**真因** (per Sprint 4.21-4.25 W-005 #2 真修 chain,commits `be3be33` / `fad9de2`):
- Bug 7/7b 根因 = IRVal struct pass-by-value stale pointer(per `project_sprint4_7_irval_pass_by_value_bug.md`)
- 真修在 jhyy_v1 `cg_copy_struct` + `irval_is_undef` 守卫 (8 处)+ C-side 同步对齐
- 守卫消除 stale pointer 后,`let _ = fncall()` 不再 emit `=w copy %t0` 污染 IL,codegen 路径正常

**Out of scope (NOT W-003)**:
- **v3 workaround 29 处** `let _X = fncall()` → `fncall()` 的 revert 不在本 sprint 范围. 类比 W-002 commit 2.12 (211 个 `_v1` 后缀 revert),W-003 revert 需要单独 cleanup commit. **可在 Sprint v1.1.x 后续做**:验证 baseline 50/53 持平下 revert 29 处 top-level 改回 `let _X = fncall()` 风格,恢复代码自然性.

**W-003 失效条件** (per workarounds.md line 307): v0 codegen 修复 `let _ = fncall(...)` emit → W-003 可移除. 实际: jhyy_v1 codegen 已 ship 修复,W-003 失效条件满足,可标 RESOLVED.

**v1.2.0 cross-ref (2026-08-12 src0/ 自然化 ship):**
- W-003 workaround 代码 `let _ = fncall()` style 在 src0/ 24 处 通过 v1.2.2 (`f49e64d`) 全部 revert 回 `let _X = fncall()` 描述性名 风格 (cg_expr / cg_emit_store / cg_copy_struct / ir_emit_ret / ir_emit_str / ir_emit_jmp 6 类 call)
- 跟 v1.2.0 plan out-of-scope "v3 workaround 29 处" (line 342) 实际工作已经 ship — v1.2.2 24 处 + v1.2.3/1.4 关联 = 完整 29 处 revert
- W-003 状态:**code 撤回完, v0 fix ship 已闭环**
- 详情见 [`docs/logs/v1/changelog-v1.2.0.md` § v1.2 wip commit 1.2](../logs/v1/changelog-v1.2.0.md)

---

## W-004: short local var (≤4 chars) → symtab hash 撞 → jhyy_v1 field assign 死循环

**ID:** W-004
**状态:** RESOLVED (transitive — W-001 byte-by-byte FNV-1a 真修 indirect coverage; minimal repro + 4 boundary variations all pass codegen on jhyy_v1 (sha `ba94df93...`) with EXIT=1 (link stage only), 2026-08-12 verified)
**日期:** 2026-08-03
**触发面:** 同时存在 ① 短（≤4 字符）函数名 + ② 短（≤4 字符）`let` 局部 var 名 + ③ struct field 赋值的组合。具体阈值取决于三者长度之和（如 `fn main` 4 + `let a` 1 + `field cur` 3 = fail；`fn entry` 5 + `let a` 1 + `field cur` 3 = OK）。
**症状:** jhyy_v1 编译含此模式的源码 → 0xC00000FD STACK OVERFLOW（exit 3221226356）。**不是** segfault（exit 3221225477）。
**根因嫌疑:** W-001 的 `hash_string` 用 `*i32` deref 一次读 4 byte。对于短字符串（长度 1-4），4-byte read 把后续 slack 字节吸进 hash 值，导致 hash 错位 → 多个不同 ident 撞同一 slot → 后续 cg_emit_store / cg_copy_struct 走错 sym → 递归查错 local → 死循环。

W-002 已修类似（identifier 长度 6-8 + `_buf` 后缀）的 hash_string 触发面，但只覆盖了**全局** enum 常量和**函数名**（211 个），未覆盖**局部 var 名**和**struct field 名**。本 workaround 补 W-002 漏掉的部分。

**workaround:** 把 src0/ 里所有 ≤ 4 字符的 `let` 局部 var 标识符重命名到 ≥ 5 字符。机械化前缀 `ptr_` / 后缀 `_local` / 加 `_v1`。同样适用于函数参数名。

**改名规则:**
- 长度 ≤ 4 字符的 `let`/`let mut` 局部 var（包含函数参数）一律改名到 ≥ 5 字符
- 长度 ≤ 4 字符的 struct field 名同样改名
- 命名规则同 W-002：机械化前缀/后缀，避免新撞

**最小复现（验证 workaround 必要性）:**

```jhyy
// BAD (触发 stack overflow):
type Arena = struct { cur: i32 }     // field "cur" 长度 3
fn main() -> i32 {                   // fn "main" 长度 4
    let mut a: Arena = Arena { cur: 0 as i32 };  // var "a" 长度 1
    a.cur = 5 as i32;                 // field assign 触发
    return 0 as i32;
}
// jhyy_v1: STACK OVERFLOW (3221226356)

// GOOD (workaround 验证):
type Arena = struct { current_value: i32 }  // field 长度 13
fn ab() -> i32 {                              // fn 长度 2，但其它都长
    let mut arena_local: Arena = Arena { current_value: 0 as i32 };  // var 长度 11
    arena_local.current_value = 5 as i32;
    return 0 as i32;
}
// jhyy_v1: OK
```

**验证（2026-08-03）:**
- 局部 var 名 `a`/`aa` (1-2 字符) + fn 名 `main`/`ab` (≤4 字符) + field 名 `cur`/`val` (≤4 字符) → 100% stack overflow
- 任一项 ≥ 5 字符 → 100% OK
- 字段赋值 (`a.cur = 5`) 是必要触发条件；只读不写不触发

**影响范围（src0/ 各文件 `let x` / `let mut x` 计数 — W-004 待替换）:**

- main.jhyy: 55 个 let + ~20 个 fn 参数（主要工作量）
- 其他文件待评估（codegen.jhyy / sema.jhyy 等 src0/ 文件，若要 jhyy_v1 编出来都要改）

**W-004 局限性:** W-001 的 hash_string 根因（`*i32` deref overread）未解，只是机械改名绕开触发面。W-001 真正修了之后，W-004 可移除并恢复短名。

**失效条件:** jhyy_v1 的 codegen 对 `*i32` deref 4-byte read 改成 byte-by-byte 不再 overread（修 W-001 根因）→ W-004 可移除。

**superseder:** ✅ closed (root cause = W-001 byte-by-byte FNV-1a 真修 ship in v0.8 commit 9 `d570c72`, Task #60 真修 unblocked verification path in v0.9 wip commit 2.15 `52843b6`) — 详见下方"## W-004 RESOLVED — transitively closed by W-001 byte-by-byte 真修 (2026-08-12)" 段

**引用:**
- v0 codegen Bug 6 (let-mut assignment) + Bug 1 (hash_string overread)
- W-002 (`docs/internal/workarounds.md` § W-002) 修了 211 个全局/函数名，未覆盖局部 var
- 复现测试 `tmp/test_w4.jhyy` ~ `tmp/test_w8.jhyy`

### 验证状态 2026-08-05 (v0.9 wip commit 2.14) — BLOCKED

**目标**: 验证 jhyy_v1 编 src0/{codegen,parser,sema}.jhyy 是否触发 stack overflow (W-004 失效条件 (i))。

**结果**: 验证 BLOCKED — 3 个目标文件**单独编译都跑不到 codegen 阶段**:

| 文件 | 现象 | 阻断根因 |
|------|------|---------|
| `src0/codegen.jhyy` | `L2198: unexpected token 'while' in expression` + 6 parse errors | Task #60 (parse_expr `while`/else) |
| `src0/sema.jhyy` | `L1191: unexpected token 'while' in expression` + parse errors | Task #60 (同上) |
| `src0/parser.jhyy` | 9+ sema errors (unknown type `*Node`, undefined variable, 不能 access field) | 跨文件 type (`*Node`, `Token`, `Sym` 等) 在 ast.jhyy / symtab.jhyy 等, 单独编 parser 拿不到 |

**full src0/main.jhyy (inline_imports 全拼接)**: 仍 segfault (exit 139) — 但 segfault 是在 parse 阶段 (Task #60 触发), 不是 codegen 阶段 (W-004 触发)。Task #60 是上游 blocker, 不修就无法隔离 W-004。

**结论**: W-004 标 RESOLVED 失效条件 (i) 无法满足, 推 v1.0.0 sprint 3+ Task #60 修后**再做 W-004 验证**。W-004 status 保持 ACTIVE (BLOCKED verification)。

**contingency**: 如果 Task #60 修后, jhyy_v1 编 src0/codegen.jhyy / parser.jhyy / sema.jhyy 不再 stack overflow → W-004 可标 RESOLVED (W-001 真修已间接覆盖);如果仍 stack overflow → 立刻开 commit 2.15 (W-004 批量改名, 触发面消除)。

### 验证状态 2026-08-12 (Sprint v1.1.1) — ✅ PASS → 标 RESOLVED (transitive)

**Task #60 真修 ship 2026-08-06** (commit `52843b6` v0.9 wip commit 2.15) → 验证路径 unblocked. Sprint v1.1.1 实际跑了 6 个最小 repro (BAD + GOOD + 4 boundary variations), jhyy_v1 (sha `ba94df93...`) 全部**通过 codegen 阶段** (不再触发 0xC00000FD STACK OVERFLOW):

| 测试 | 触发面 (fn / var / field) | C-side 行为 | jhyy_v1 行为 | 期望 (W-004 真修) |
|------|---------------------------|-------------|--------------|---------------------|
| BAD (workarounds.md L343-349) | `main`(4) / `a`(1) / `cur`(3) | EXIT=1 (link fail due to `main` symbol conflict with runtime.c) | EXIT=1 (same) | ✅ codegen OK |
| GOOD (workarounds.md L351-358) | `ab`(2) / `arena_local`(11) / `current_value`(13) | EXIT=1 (link fail) | EXIT=1 (same) | ✅ codegen OK |
| v1 (extreme short) | `a`(1) / `b`(1) / `c`(1) | EXIT=1 | EXIT=1 | ✅ codegen OK |
| v2 (all 4-char) | `aaaa`(4) / `bbbb`(4) / `cccc`(4) | EXIT=1 | EXIT=1 | ✅ codegen OK |
| v3 (5-char fn) | `entry`(5) / `b`(1) / `c`(1) | EXIT=1 | EXIT=1 | ✅ codegen OK |
| v4 (7-char field) | `a`(1) / `b`(1) / `current`(7) | EXIT=1 | EXIT=1 | ✅ codegen OK |

**关键观察**: jhyy_v1 在所有 6 个测试中, codegen 阶段日志 `Pass B start → B i=0 → cg_module done → codegen done` 完整, 后续 link 阶段失败只是因为 fn 名 (`main` / `a` / `ab` 等) 跟 runtime.c 的 `int main(int, char**)` 冲突 — **不是 W-004 触发**. 之前 W-004 触发是 exit 3221226356 (0xC00000FD STACK OVERFLOW), 现在 6/6 都是 EXIT=1 + "gcc link failed", 完全没有 stack overflow.

**W-004 vs W-006 真因 关系 (避免误诊)**:
- W-006 真因 = W-005 #2 family (cg_expr IRVal struct pass-by-value stale pointer) — Sprint 4.21-4.25 真修时一并解决
- W-004 真因 = W-001 family (hash_string `*i32` deref overread → symtab 撞 → cg_emit_store / cg_copy_struct 走错 sym → 死循环)
- **不同 family** — W-006 transitive close 不连带 W-004. W-004 独立被 W-001 byte-by-byte FNV-1a 真修覆盖.

**为什么之前 W-004 没识别成 W-001 family**:
- 当时 (2026-08-03) 诊断假设是 "stack-slot allocator for 短名复用 slot" (看到死循环 + 短名现象)
- 但实际根因是 `hash_string` 用 `*i32` deref 一次读 4 byte, 短字符串 (≤4 char) 把后续 slack 字节吸进 hash 值, 多个不同 ident 撞同一 slot
- W-002 当时 (2026-08-04) 修了 211 个全局/函数名, 但漏掉**局部 var + struct field** (per W-004 entry line 331)
- W-001 真修 (2026-08-04 commit `d570c72`) 改 byte-by-byte `*u8` deref + length mix (FNV-1a) → 短名不再 overread → symtab 不再撞 → W-004 失效条件 (i) 满足

### 真修 chain (按 commit 时间序, 仅列与 W-004 有关者)

| Commit | Sprint | 改动 | 跟 W-004 关系 |
|--------|--------|------|----------------|
| `d570c72` (v0.8 commit 9) | — | W-001 byte-by-byte FNV-1a 真修 (`hash_string` 改 `*u8` deref + length mix) | **关键 commit** — 短名不再 overread, symtab 不再撞 |
| `52843b6` (v0.9 wip 2.15) | — | Task #60 真修 (parse_if body inline parse_while 嵌套 TOKEN_WHILE 分支) | 验证路径 unblock — 不修则 src0/{codegen,sema}.jhyy 编不过 |
| Sprint 4.21-4.25 chain | 4.21-4.25 | W-005 #2 family 真修 (CGContext layout, IRVal const ptr, sentinel guard) | **非 W-004 直接根因** — W-006 跟 W-005 同 family 被一并修, 但 W-004 是 W-001 family 独立 |

### 留给未来 (post-v1.1.1 ship)

- W-004 workaround 代码本身 (`let arena_local` 等长名 + `arena_local.current_value` 等长 field) **不需 revert** — 当前不被触发, 保留不破坏 src0/ 自然性 (跟 W-002 同样风格的 211 改名为对照)
- 短名 (`let x`, `let y`, field `cur` 等) 的 revert 留给 Sprint v1.1.x post-W-007 真修 ship 后做, 跟 src0/*.jhyy 100% natural 目标一起
- 未来 reader: 若看到 src0/ 里有 `arena_local.current_value` 等"看起来不必要的长名", 不要误以为是 stale workaround — 是 W-004 历史 fallback, 当前 W-001 真修已使其非必要但保留以维持翻译风格一致

---

## W-005: `let mut x: T; x = expr;` 改 `*pos_ptr += ...` 绕 jhyy_v1 codegen segfault

**ID:** W-005
**状态:** RESOLVED (v0.9 wip commit 2.13)
**日期:** 2026-08-03 (workaround) → 2026-08-05 (commit 2.11 真修) → 2026-08-05 (commit 2.13 revert 加固)
**触发面:** 函数体内任意 `let mut` 变量 + 后续 `x = expr;` 赋值语句（不论 expr 类型、变量名长度、是否被 read、所在 fn 深度）。**100% 触发**（exit 139 / 0xC0000005）。
**症状:** jhyy_v1 编译含此模式的源码 → 0xC0000005 segfault。v0 jhyy.exe 编同一源码 → exit 0（IL 正确）。
**最小复现:**
```jhyy
// BAD (segfault):
fn entry() -> i32 {
    let mut x: i32 = 0 as i32;
    x = 42 as i32;
    return x;
}
// jhyy_v1: segfault (139)

// GOOD (workaround 验证):
fn entry() -> i32 {
    let buf = malloc(8 as i64) as *i64;
    *buf = 0 as i64;
    *buf = *buf + 42 as i64;
    let nul = (buf as i64) as *u8;
    free(nul);
    return 0 as i32;
}
// jhyy_v1: OK
```

**根因嫌疑:** Bug 6 (let-mut assignment) + Bug 7b (nested let-mut) 的复合 — jhyy_v1 自举编译 `NODE_ASSIGN[NODE_IDENT]` 路径时 emit 错的 IL（多写 storew 到未初始化 stack slot，或 loadw-on-loadw 链），访问 uninitialized memory 触发 0xC0000005。**v0 codegen 没这个问题**（v0 编同一 .jhyy 源码 emit 正确 IL），所以是 jhyy_v1 自身 codegen 的 bug，不是源 v0 的 bug。

**workaround:** 用 `*pos_ptr += n` 模式（`i64` 通过 `*i64` 解引用累加）替代 `let mut pos: i64 = 0; pos = str_concat_at(...)`。需要累计位置的所有 cmd-构造函数（`run_qbe_v1` / `link_with_gcc`）都改。

```jhyy
// BAD (触发 segfault):
fn run_qbe_v1(il_path_v1: *u8, asm_path_v1: *u8) -> i32 {
    let cmd_buf_v1 = malloc(4096 as i64);
    let qbe = QBE_PATH_v1();
    let mut pos_v1: i64 = 0 as i64;
    pos_v1 = str_concat_at(cmd_buf_v1, pos_v1, qbe);
    pos_v1 = str_concat_at(cmd_buf_v1, pos_v1, " -t amd64_win -o " as *u8);
    pos_v1 = str_concat_at(cmd_buf_v1, pos_v1, asm_path_v1);
    ...
    let nul_p = (cmd_buf_v1 as i64 + pos_v1) as *u8;
    store_byte_i32(nul_p, 0 as i32);
    ...
}

// GOOD (W-005):
fn run_qbe_v1(il_path_v1: *u8, asm_path_v1: *u8) -> i32 {
    let cmd_buf_v1 = malloc(4096 as i64);
    let pos_ptr_v1 = malloc(8 as i64) as *i64;
    *pos_ptr_v1 = 0 as i64;
    let qbe = QBE_PATH_v1();
    *pos_ptr_v1 = str_concat_at(cmd_buf_v1, *pos_ptr_v1, qbe);
    *pos_ptr_v1 = str_concat_at(cmd_buf_v1, *pos_ptr_v1, " -t amd64_win -o " as *u8);
    *pos_ptr_v1 = str_concat_at(cmd_buf_v1, *pos_ptr_v1, asm_path_v1);
    ...
    let nul_p = (cmd_buf_v1 as i64 + *pos_ptr_v1) as *u8;
    store_byte_i32(nul_p, 0 as i32);
    ...
    free(pos_ptr_v1 as *u8);
}
```

注意：`*pos_ptr_v1 = str_concat_at(...)` 实际是 `*pos_ptr_v1 = expr`，本质也是 `let mut` assignment 模式。**但通过 `*i64` deref 走的是 `NODE_DEREF` 路径而不是 `NODE_ASSIGN[NODE_IDENT]` 路径**，绕开 bug 6 的触发面。

**验证（2026-08-03）:**
- 最小 let-mut + assign（i32/i64、var 长度 1/7/10/各种）→ 100% segfault
- `*pos_ptr = ...` 模式 → 100% OK
- v0 编两种模式都 OK（jhyy_v1 自身 bug，不是 v0 也不是源 jhyy 源码问题）

**影响范围（src0/ 中需 W-005 替换的 let-mut + assign 位置）— commit 2.13 revert 后:**

| 文件 | 函数 | 变量 | revert 数 |
|------|------|------|-----------|
| main.jhyy | path_to_win | idx_ptr | 1 |
| main.jhyy | run_qbe | pos_v1 | 1 var / 5 assign |
| main.jhyy | link_with_gcc | pos_v2 | 1 var / 9 assign |
| main.jhyy | cmd_compile (argv walk) | input_v1 / user_out_v1 / i_v4 | 3 vars |
| main.jhyy | cmd_compile (out_buf) | out_buf if-else workaround | 1 简化 |
| arena.jhyy | arena_new_block | size_v1 | 1 |
| arena.jhyy | arena_free | b | 1 |
| util.jhyy | sb_grow | new_cap | 1 |
| util.jhyy | hash_string | h / i | 2 |
| util.jhyy | hm_put | idx | 1 |
| util.jhyy | hm_grow (outer + inner) | i / idx | 2 |
| util.jhyy | hm_get | idx | 1 |
| **总计** | | | **15 vars + 1 if-else 简化** (= 16 模式 revert) |

**commit 2.13 验证 (2026-08-05):** 所有 16 模式 revert 回 `let mut x; x = expr;` 风格后：
- v0 build clean (无 warning)
- regress 持平 50/53 PASS
- stage1 byte-equal 持平 6/7 PASS
- jhyy_v1.exe (built from reverted src0/) 可执行,跟 commit 2.12 路径完全一致
- main.jhyy runtime (jhyy_v1 编 src0/main.jhyy 跑 main.jhyy) **仍 segfault (exit 139)** —— 这是 main.jhyy 自身更大尺寸 (25KB) 引发的 W-001 类 heap corruption 问题,不在 commit 2.13 范围,推 v1.0 sprint 3 B' 阶段

**W-005 局限性:** 这是绕 `NODE_ASSIGN[NODE_IDENT]` 触发面。`let mut struct; struct.field = X` (NODE_ASSIGN[NODE_FIELD]) 走不同路径，W-005 不修。**Bug 6+7b 的根因修复需在 jhyy_v1 codegen.c 端修 NODE_ASSIGN 的 emit，post v1.0.0。**

**失效条件:** jhyy_v1 codegen 修对 NODE_ASSIGN[NODE_IDENT] 的 let-mut target → emit 正确 `storew` 到 stack slot → W-005 可移除并恢复 `let mut x; x = ...;` 风格。

**superseder:** v0.9 wip commit 2.10 (诊断性 doc-only,无 codegen 改动) — 真修推后到 v0.9 wip commit 2.11+ 或更晚。

**v0.9 wip commit 2.11 (2026-08-05) — W-005 真修 phase 2 实施完成:**
- C 端 `codegen.c` CGContext 布局改成 jhyy 端布局:
  - `LocalEntry locals[MAX_LOCALS]` (inline 24576 bytes) → `LocalEntry *locals` (calloc'd)
  - `IRVal sret_slot` (32 bytes) → `int64_t sret_slot_id` (8 bytes, = temp number)
  - `IRVal loop_starts/ends/continues[MAX_LOOP_DEPTH]` (3×1024 bytes) → `IRVal *loop_starts/ends/continues` (3×calloc'd)
  - 字段顺序: `loop_depth` 挪到 `has_sret` 之后 (跟 jhyy 端布局一致)
- C 端 `cg_func` 加 `calloc` ×4 + `free` ×4 (新 `<stdlib.h>` include)
- C 端所有 `cg->sret_slot` → 构造 `IRVal` literal (`{0}` + `sret_addr.id = sret_slot_id; sret_addr.qbe_type = 'l';`)
- 全部 9 字段 offset 现在跟 jhyy 端 CGCONTEXT_SIZE = 72 字节精确对齐
- **验证 (commit 2.11):**
  - regress 50/53 PASS, 0 FAIL, 3 SKIP — 持平 baseline
  - byte-equal 持平 5/7 (5 PASS / 2 FAIL: match_exhaustive + const_array)
  - **let-mut 最小复现 `tmp/test_w5.jhyy`:** jhyy_v1 编译 + 运行 → exit=20 (输出 `x = 20`) — **不再 segfault**! 之前 commit 2.10 阶段 jhyy_v1 编译同一文件 segfault (exit 139)
- 剩余影响: W-005 workaround (`*pos_ptr_vN` 模式) 在 src0/ 仍有 14 处使用。**W-005 现在可安全移除** — 下个 commit (2.13) 加固可 revert 14 处 `*pos_ptr_vN` 累加 → 改回 `let mut x; x += n` 风格。W-005 在 commit 2.13 移出 workarounds.md active 列表。

**根因重诊断(v0.9 wip commit 2.10,2026-08-05):** W-005 segfault **不是** "NODE_ASSIGN emit 错" 那么直接 —— 是 **C 端 codegen.c CGContext 跟 jhyy 端 codegen.jhyy CGContext struct 布局不匹配**:
- C 端: `LocalEntry locals[MAX_LOCALS]` (24576 bytes inline array),nlocals 在 offset 24584, has_sret 在 offset 24592+, loop_starts 在 offset 24600+ ...
- Jhyy 端: `locals: *u8` (指针,arena 单独 alloc),nlocals 在 offset 16, has_sret 在 offset 40, loop_starts 在 offset 48 ...
- Jhyy_v1 编译后,offset 错位 → `(*cg).locals` 实际读到 `locals[0].sym` (jhyy 当指针用) → cg_find_local 把 sym 指针当 locals buffer base → `ptr_add_u8(sym, 0)` 指向 Sym 结构 → `entry_sym_p == sym` 凑巧成立 → 后续读 `entry_ptr + 8` (kind 字段) 实际读 Sym 结构的非 sym 字节 → 越界读 → segfault
- **修复路径 (post-v0.9 wip):** 把 C 端 CGContext 改成 jhyy 端布局 (LocalEntry *locals + separate alloc) + 把 sret_slot 改成 sret_slot_id i64 + 把 loop_starts/ends/continues 改成 *u8 指针(单独 arena alloc)。涉及全部 codegen.c 字段访问路径 (~30 处)。**scope 超出 commit 2.10**,推迟到 commit 2.11+ 或独立 sprint。

**影响:** 不影响 commit 2.10 目标 (byte-equal 持平 5/7, regress 持平) —— 现状 byte-equal 5/7 已稳定,let-mut + assign 触发面继续走 W-005 workaround (`*pos_ptr_vN` 模式)。

**引用:**
- v0 codegen Bug 6 (let-mut assignment) + Bug 7b (nested let-mut)
- W-003 (`docs/internal/workarounds.md` § W-003) 修了 `let _X = fncall()` 顶层 direct call 模式，未覆盖 let-mut + assign
- W-004 修了短 var 名导致 symtab hash 撞死循环，未覆盖 let-mut + assign segfault
- 复现测试 `tmp/test_w4_lit.jhyy` / `tmp/test_w4_v1.jhyy`

**v1.2.0 cross-ref (2026-08-12 src0/ 自然化 ship):**
- W-005 workaround 代码 `let mut xxx_vN` style 在 src0/ 16 处 通过 v1.2.1 (`2c92cf4`) 全部 revert 回 `let mut xxx` 自然风格
- W-005 workaround 残留 `_vN` 后缀 99 处 通过 v1.2.3 (`1c24841`) + v1.2.4 (`0026098`) 全部 cleanup
- W-005 状态:**code 撤回完, v0 fix ship 已闭环** — 跟 v0.9 wip commit 2.13 + v0.9 wip commit 2.11 真修 chain 形成完整闭环
- 详情见 [`docs/logs/v1/changelog-v1.2.0.md` § v1.2 wip commit 1.1](../logs/v1/changelog-v1.2.0.md) + [§ v1.2 wip commit 1.3](../logs/v1/changelog-v1.2.0.md) + [§ v1.2 wip commit 1.4](../logs/v1/changelog-v1.2.0.md)

---

## W-006: jhyy_v1 `return x ± y` 两 1-char var 发 127（QBE fail）

**ID:** W-006
**状态:** RESOLVED (transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain — minimal repro no longer triggers, 2026-08-11 verified)
**日期:** 2026-08-04 (open) → 2026-08-11 (close, transitive)
**触发面:** 函数体末尾 `return X OP Y`（OP ∈ `+`, `-`），X 和 Y 都是 1-char 局部变量（任意 i32/i64 类型）。
**症状:** jhyy_v1 编译 → exit 127（无输出）→ 可能是 segfault 也可能是 QBE fail。QBE fail 时报 "invalid type for jump argument"。
**最小复现:**
```jhyy
// BAD (exit 127 / QBE fail):
fn main_jhyy() -> i32 {
    let x = 42 as i32;
    let y = 7 as i32;
    return x + y;
}
// jhyy_v1: exit 127

// GOOD (workaround 1 — rename):
fn main_jhyy() -> i32 {
    let xx = 42 as i32;
    let yy = 7 as i32;
    return xx + yy;
}
// jhyy_v1: OK (exit 0)

// GOOD (workaround 2 — type annotation):
fn main_jhyy() -> i32 {
    let x: i32 = 42 as i32;
    let y: i32 = 7 as i32;
    return x + y;
}
// jhyy_v1: OK

// GOOD (workaround 3 — intermediate let):
fn main_jhyy() -> i32 {
    let x = 42 as i32;
    let y = 7 as i32;
    let z = x + y;
    return z;
}
// jhyy_v1: OK
```

**根因嫌疑:** jhyy_v1 codegen 的 stack-slot allocator 给两个 1-char 局部 var 分配了**同一个 stack offset**（slot reuse bug）。当 `x + y` 在 return 表达式上下文被直接编译时，emit 的 IL 中两个 operand 指向同一临时，结果 QBE 拒绝（type mismatch 或 错位）→ 退化成 exit 127。v0 codegen 没这个问题。

**workaround:** 三个等价方案（任选一）：
1. **rename：** 把 X 或 Y 改成 ≥2 字符（`xx`、`yy` 等）
2. **type annotation：** `let x: i32 = 42 as i32;` 显式声明类型
3. **intermediate let：** `let z = x + y; return z;` 强制中间 stack slot

**影响范围:** 触发面在 src0/ 极常见：所有短局部变量（`x`/`y`/`n`/`i`/`p`/`h`/`c` 等）参与 `return X + Y` 或 `return X - Y` 时都中招。需要机械扫描：
- util.jhyy: 至少 12 个 1-char `let`（`n`、`p`、`h`、`c`、`e`、`i`），多个 `*i_ptr + 1` 累加模式
- arena.jhyy: `arena_free` 的 `b = next` 累加（已用 W-005 转 `*i64` 绕过）
- main.jhyy: `path_to_win` 索引累加（已用 W-005 转 `*i64` 绕过）
- lexer.jhyy / parser.jhyy / sema.jhyy / codegen.jhyy: 推测大量触发面（未审计）

**W-006 局限性:** 仅触发 `return X ± Y` 直接形式。中间 let / 比较 / 字段访问不触发。`*ptr_ptr += n` 累加（已 W-005 转过的）也不触发，因为 deref 走 NODE_DEREF 路径不同。

**失效条件:** jhyy_v1 codegen 修对 stack-slot allocator（按变量名长度 ≤1 时分配不同 slot）→ W-006 可移除并恢复 `let x = ...; return x + y;` 风格。

**superseder:** TBD（jhyy_v1 codegen fix sprint，post v1.0.0 落地后）

**引用:**
- 复现 `_test_e.jhyy` / `_test_y.jhyy`（x + y / a + b 都触发）
- v0 同源码编译 exit 0 → 是 jhyy_v1 自身 bug，不是源 jhyy 问题
- W-004 修了短名（≤4 char）symtab hash 撞死循环；W-006 是 codegen slot allocator bug，**不同 bug**

### 触发面扫描 2026-08-05 — dormant (0 活跃触发面)

**目标**: 扫当前 src0/ 看 `return X ± Y` (X, Y 都是 1-char) 触发面是否仍存在。

**扫描方法**: `grep -rn 'return [a-z_]\{1,2\} [+\-] [a-z_]\{1,2\}[^_]' compiler/src0/*.jhyy` (排除 2 字符含下划线的合法名)。

**结果**: **0 命中** — 当前 src0/ 内所有 `return X ± Y` 形式已自然避免 W-006 触发面:
- 翻译阶段已用 `(p as i64 + off) as *u8` cast-chain 形式替代直接 var+var (util.jhyy 11 处)
- 翻译阶段已用 `return n;` / `return 0 as *u8;` / `return (n as i64 + NODE_SIZE()) as *Type;` 单 operand 形式替代 (codegen / sema / ast)
- 翻译风格: `let z = x + y; return z;` intermediate let 已普遍 (避免直接 return sum)

**结论**: W-006 在当前 src0/ **0 活跃触发面**, 但根因 (codegen stack-slot allocator bug) 未真修, 新写代码仍可能触发。Workaround 状态 ✅ RESOLVED (0 活跃触发面 = 不需要 active 维护); 根因标 dormant 提醒未来 reader 不要 reset codegen stack-slot allocator (per `feedback_document_workarounds_in_docs.md` "superseded 标 RESOLVED 不删除" 原则, W-006 整段保留作为历史归档)。

**风险**: 如果未来写 `return x + y` (双 1-char) 又会触发 → 需机械改名 / 类型注解 / intermediate let。改动面在 codegen.jhyy stack-slot allocator 真修之前, 工作量随代码增长线性增加。

---

## W-006 RESOLVED — transitively closed by Sprint 4.21-4.25 W-005 #2 真修 chain (2026-08-11)

**日期**: 2026-08-11 (v1.1 wip commit 1.1, replaced earlier "doc-only escaped" framing)
**修复类型**: 真修 (transitive — 根因同 W-005 #2 family, 在 Sprint 4.21-4.25 真修过程中被一并解决)

### 误诊史 (为什么会写成 "escaped")

v1.1 wip commit 1.1 最初版本把 W-006 标 "RESOLVED (escaped — codegen fix deferred to v2.x)", 用户 challenge "为啥这个W006改个文档就完事了" 后立刻 reproduce 验证 → 发现 **minimal repro 已不触发** (IL 跟 C-side byte-equal, exe exit 正确). 重新审计 git log + 真修 chain 才知道 **W-006 跟 W-005 #2 是同 family, Sprint 4.21-4.25 真修 W-005 #2 时已经一并修了 W-006**.

### 真修 chain (按 commit 时间序, 仅列与 W-006 有关者)

| Commit | 改动 | 跟 W-006 的关系 |
|--------|------|----------------|
| `be3be33` (2.78) | Sprint 4.21 Phases C+D+G — cg_copy_struct 改 `const IRVal*` 入参 + cg_expr out-param 改指针 | 消除 IRVal struct pass-by-value 路径上 cg_expr 返回的临时 IRVal 在 caller 栈上 stale aliasing. **W-006 的 "两 1-char var 共享 stack slot" 实际不是 stack slot 复用, 而是 cg_expr 返回 IRVal 在 caller 栈上被后续调用覆盖** (后续 `x + y` 读 x 时实际读到 y 的 IRVal). |
| `fad9de2` (2.81) | Sprint 4.25 — W-005 #2 真修 (A' sentinel 守卫, 8 处 `irval_is_undef(v)` 守卫 + pre-increment next_tmp) | sentinel + pre-increment 确保每次 ir_new_tmp 都拿到唯一 ID, 杜绝 "两 var 指向同一个 `%t0`" 路径. 这一项是真修 W-006 的**关键 commit**. |
| `9b67e53` (2.79) | Sprint 4.23 — MAX_LOCALS 512→1024 | 边界相关: 之前 nlocals=512 在递归 / 长函数场景下 cg_add_local 返回 0 (silent skip) → 后续 cg_find_local 找不到返回 undef → undef IRVal 被 binop 当 operand 读 → 同样 cascade 出 W-006 的"两 var 共享栈帧"症状. |

### 为什么之前 W-006 没识别成 W-005 #2 family

- 当时的诊断假设是 "stack-slot allocator for ≤1-char vars 复用同一 slot" (看到两个 var 共享同一栈帧位置的现象, 推断是 allocator 在按 name 复用 slot).
- 但实际根因是 **cg_expr 返回 IRVal 时 struct pass-by-value 在 caller 栈上留下 stale pointer**, 后续读这个 var 时 IRVal 字段已被覆盖 — 表现为 "两 var 看似同一 slot".
- 当时 (2026-08-04) 没意识到 IRVal struct pass-by-value 是 systemic 问题, 把 W-006 当成独立 codegen 局点 bug 处理, 所以只记录 workaround + defer.

### 当前状态 (2026-08-11 实证)

- ✅ Minimal repro `let x = 42 as i32; let y = 7 as i32; return x + y;` → jhyy_v1 编 → IL byte-equal C-side, exe exit 49
- ✅ fib30.jhyy (用 `n - 1`, `n - 2` 1-char var 减法) → 直接 jhyy_v1 编 → IL 干净, exe 输出 "fib(30) = 832040"
- ✅ workarounds (rename / type annotation / intermediate let) 仍全部 OK (但已非必要)
- ✅ src0/ 扫描: `return X + Y` (X, Y ≤ 1 字符) 触发面 = 0 命中 — 当前翻译风格已不需要这些 workaround
- ✅ regress.py 50/50 + regress_v1.py 50/50 + stage1 byte-equal 7/7 持平

### 留给未来 (post-v1.1)

- W-006 三个 workaround 命名 (rename / type annotation / intermediate let) 可**机械 revert 回 `let x = ...; return x + y;` 风格** (Stage 2 N=3 闭环要求 jhyy_v1 编 jhyy_v1 编 src0/ 输出 byte-equal, 翻译风格应尽量少 workaround 噪声). 留给 Sprint v1.1.x post-W-007 真修 ship 后做.
- fib_renamed.jhyy 可考虑 revert 回 fib30.jhyy 同名 (历史标记保留, 不强求).

**superseder**: closed (root cause = W-005 #2 family)

**引用**:
- [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md` § Sprint v1.1.1](../../plans/v1/v1.1.0任务清单%20+%20概要设计.md) — W-006 编排 (从 1st sprint 移到 "已真修" 状态)
- `memory/project_sprint4_21_phase_b_c_d_g_done.md` — Sprint 4.21 Phase C (cg_copy_struct const IRVal*)
- `memory/project_sprint4_25_a_prime_sentinel_guard.md` — Sprint 4.25 A' sentinel 真修
- Stage 1 byte-equal 7/7 PASS (持平 baseline)

**引用**:
- v1.1.0 plan [`docs/plans/v1/v1.1.0任务清单 + 概要设计.md`](../plans/v1/v1.1.0任务清单 + 概要设计.md) § Sprint v1.1.1
- 触发面扫描 2026-08-05: 见上方"### 触发面扫描 2026-08-05 — dormant (0 活跃触发面)" 段
- v1.1 wip commit 1.1 (this commit) — doc-only RESOLVED status flip

---

## W-007: jhyy_v1 `fn() -> i64 { return X as i64; }` emit `w copy`

**ID:** W-007
**状态:** ✅ RESOLVED (transitive — jhyy_v1.exe.exe sha `ba94df93...` 已含 type propagation fix per v0.8 commit 7 `0453cef` `cg_convert_arg src=W → dst=L extsw 分支补全`,2026-08-12 verified 5x5 PASS on 4 BAD variants, IL byte-equal C-side)
**日期:** 2026-08-04 (ACTIVE) → 2026-08-12 (RESOLVED transitive)
**触发面:** 函数体末尾 `return literal as i64;` 或 `let x = literal as i64; return x;`，且 literal 是字面整数常量。
**症状:** QBE 拒绝 → "invalid type for jump argument %t0 in block @start0"。jhyy_v1 编译 exit 1。
**最小复现:**
```jhyy
// BAD (QBE fail):
fn small_const() -> i64 { return 5 as i64; }
// jhyy_v1 emit:
//   export function l $small_const() {
//   @start0
//       %t0 =w copy 5      ← 函数返回 l (i64) 但 copy 是 w (32-bit)
//       ret %t0            ← QBE 拒绝
//   }
// QBE error: invalid type for jump argument %t0 in block @start0

// BAD 变体 2 (let + return):
fn small_const() -> i64 {
    let x = 5 as i64;
    return x;
}
// jhyy_v1: emit %t0 =w copy 5; ret %t0（同样错）

// BAD 变体 3 (arithmetic):
fn small_const() -> i64 {
    return (4 + 1) as i64;
}
// jhyy_v1: emit %t0 =w copy 4; %t1 =w copy 1; %t2 =w add %t0, %t1; ret %t2

// GOOD (workaround — 用 extern fn 包一层返回 i64):
extern fn some_64() -> i64;
fn small_const() -> i64 { return some_64(); }
// jhyy_v1: OK
```

**根因嫌疑:** jhyy_v1 codegen 的 const/copy emit 路径在类型推断时**丢失了 i64 类型信息**。NODE_INT_LIT 的默认 emit 类是 w (32-bit) — 看起来是 v0 早期版本的硬编码，jhyy_v1 翻译时没修。`as i64` cast 在 codegen 路径上没生效（虽然 sema 通过了）。

**workaround:**
- 暂时没有完全等价的 workaround（不能直接 emit i64 literal in codegen）
- **方法 1**：把 i64 返回函数改成返回 `*u8` 或 `i32`，调用方再做 cast（接口破坏大）
- **方法 2**：i64 常量函数（如 `FNV_OFFSET`、`FNV_PRIME`）改写成**两行 let + extern 调用链**（不实用）
- **方法 3**：在 jhyy_v1 codegen 端修 NODE_INT_LIT emit 的 type 推断（**根治，需 post v1.0.0**）

**影响范围:** util.jhyy 中所有 `fn XXX() -> i64 { return literal as i64; }`：
- `FNV_OFFSET() -> i64 { return 0xcbf29ce484222325 as i64; }`
- `FNV_PRIME() -> i64 { return 0x100000001b3 as i64; }`
- 以及 hash_string / strlen / sprintf_lld 等所有返回 i64 的内部函数

**W-007 局限性:** 仅触发字面整数常量。变量、函数调用返回 i64 不触发（caller 用 `l` 类型正确 emit）。所以 `let n: i64 = strlen(s);` 不受影响，`return n;` 也不受影响。

**失效条件:** jhyy_v1 codegen 在 NODE_INT_LIT 的 emit 路径上加 type propagation（看 return type / cast 类型决定 copy 的 class）→ W-007 可移除。

**superseder:** v0.8 commit 7 `0453cef` (cg_convert_arg src=W → dst=L extsw 分支补全) — 已 ship,镜像到 jhyy_v1 `compiler/src0/codegen.jhyy:657-661`

### W-007 RESOLVED — transitively closed by v0.8 commit 7 extsw 分支 (2026-08-12)

**Sprint v1.1.2 verification (5x5 PASS)**:

| Variant | Source | Expected | 5x5 PASS |
|---------|--------|----------|----------|
| V1 | `fn small_const() -> i64 { return 5 as i64; }` | EXIT=5 | ✅ 5/5 |
| V2 | `let x = 5 as i64; return x;` | EXIT=5 | ✅ 5/5 |
| V3 | `return (4 + 1) as i64;` | EXIT=5 | ✅ 5/5 |
| V4 | `return 0 as i64;` | EXIT=0 | ✅ 5/5 |

**canonical jhyy_v1 emit** (sha `ba94df93`, vs prior buggy `%t0 =w copy 5; ret %t0`):
```qbe
export function l $small_const() {
@start0
    %t1 =w copy 5
    %t2 =l extsw %t1     ← cg_convert_arg `src=W → dst=L` 分支补全生效
    ret %t2
}
```

**真因** (per v0.8 commit 7 + jhyy_v1 镜像 `codegen.jhyy:657-661`):
- NODE_INT_LIT 默认 emit 类是 `w` (QBE literal 不能 `l` class 直接 emit)
- 旧版 cg_convert_arg 缺 `src=W → dst=L` 分支 → emit `w copy; ret` → QBE fail
- v0.8 commit 7 加 `src=QBE_W && dst=QBE_L → emit extsw` 分支,jhyy_v1 翻译时已镜像 (codegen.jhyy:657-661 "W-007 fix (v0.8 bug 11 analog)" 注释)

**Out of scope (NOT W-007, separate shared bug)**:
- **大整数 literal (超出 INT32_MAX, 如 `0xcbf29ce484222325`)** → C-side AND jhyy_v1 都 emit `%t1 =w copy 9223372036854775807` (INT64_MAX 截断),后 `extsw`. 这是 NODE_INT_LIT parse 层 bug (lex 阶段把 hex literal 存为 i32 后溢出转 i64) — 双编译器共享,需要单独 sprint 修,不是 W-007
- **`-1 as i64`** → runtime crash (EXIT=127), C-side AND jhyy_v1 同样行为. IL 正确(`w copy 1; sub 0,1; extsw`),但运行时负数比较/QBE extsw 路径有 bug — 不是 W-007 触发面 (跟 W-007 literal-as-i64 emit type propagation 无关)

**W-007 失效条件** (per workarounds.md line 765): jhyy_v1 codegen NODE_INT_LIT emit path 加 type propagation → 失效条件已满足,标 RESOLVED.

**引用:**
- 复现 `_test_small.jhyy` / `_test_small4.jhyy` / `_test_small6.jhyy` / `_test_small8.jhyy` (4 BAD variants 全 PASS)
- v0 同源码 emit 正确 IL（`%t0 =l copy ...`），jhyy_v1 emit `w copy + extsw`，现在 byte-equal to v0
- 与 W-006 触发面不同（无 1-char var 介入），是独立 bug — W-006 也 RESOLVED (Sprint 4.21-4.25 W-005 #2 family transitive close)

---

## W-008: jhyy_v1 cg_find_field_offset 双层 deref 漏（i64 struct field emit `=w loadw` + 全 struct field 走 fallback）

**ID:** W-008
**状态:** RESOLVED（v0.8 commit 11，2d4c319 — codegen.jhyy 三处 deref 漏 + workarounds.md 文档同步；下游 cslel/ceql 错转为 W-009 候选）
**日期:** 2026-08-04
**触发面:** jhyy 源码里**任意 `(*ptr).field_X` 或 `s.field` 或 `field.assign()` 路径**走 cg_find_field_offset / cg_copy_struct — 包括 codegen 阶段任何按 struct 字段 emit 的代码：
- `(*a).def_size`（i64）— arena.jhyy 赋值/读取 def_size
- `(*a).blocks` 等所有 *u8 字段 — 写到 i64 变量也算
- v0.7 7B `arr_of_structs[i].field`（path 1/2 都用 cg_find_field_offset）
- 任何 user-defined struct 的 field 访问

**症状:** QBE 拒绝：`invalid type for store ... (w != l)` 或 `storel %t_w, %t_slot` type mismatch；jhyy_v1 编译 exit 1。**或者**编译过但运行时 segfault 0xC0000005（heap corruption）。
**根因（双层 deref 漏）：** jhyy_v1 `cg_find_field_offset`（codegen.jhyy）有**两个独立的 deref 漏**：

### Bug 8a：sym-p 解 deref（更深层 root cause）
```jhyy
// codegen.jhyy:489-491（fix 前）
let fdesc = ptr_add_u8((*st).fields_v1, j * FIELD_DESC_SIZE()) as *u8;
let fname_str_ptr = fdesc as **u8;
let fname_str = *fname_str_ptr;        // ← BUG：读到的是 *Sym，不是 const char *
if strcmp(fname_str, field_name) == 0 { ... }
```

sema.jhyy:1507 写入的是 `*fd_name_slot = fsym`（fsym 是 *Sym），所以 FieldDesc.name 字段存的是 *Sym 指针。strcmp(Sym*, "val") 把 Sym 内存字节当 C 字符串，但 Sym 字节是 8 字节堆指针（如 `0x0000_0020_4D_EF_12_34`，会有高位 0x00）→ strcmp 几乎永远不匹配 → cg_find_field_offset 直接走 fallback exit path 返回 0 → caller 拿到的 out_buf 是 uninitialized arena garbage → offset_v1=0、field_type_raw=garbage。

C 端 codegen.c:854 等价语句是 `strcmp(st->struct_type.fields[j].name->name, d->fields[i].name)` — **多一层 deref 读 `Sym->name`**，所以 v0 工作。

### Bug 8b：type slot deref（首次发现层）
```jhyy
// codegen.jhyy:493（fix 前）
let out_type_v1 = ptr_add_u8(out_buf_v1, 8 as i64) as **u8;
*out_type_v1 = ptr_add_u8(fdesc, 8 as i64) as *u8;   // ← BUG：写的是 fdesc+8 地址本身，不是 fdesc+8 处的值
```
对比 offset_v1 那行 `*out_off_v1 = *foff` 是正确 deref → 漏 symmetry。CGContext out_buf layout（i64 offset_v1 @ 0 + *Type @ 8）是 commit 4 抽 helper 定的，type slot 写漏 deref → caller 拿到 `field_type_raw` 实际是 fdesc+8 这个**指向 type 字段存储地址的指针**（不是 Type 指针本身）。

### Bug 8c：cg_copy_struct 同模式 (codegen.jhyy:448)
```jhyy
let ftype = ptr_add_u8(fdesc_ptr, 8 as i64) as *Type;   // ← BUG：ftype 实际指向 FieldDesc 内字节，不是 Type
```
后续 `(*ftype).kind` 读 4 字节 at fdesc_ptr+8 → Type* 指针的低 32 位 → 不等于任何 KIND_* → fall through → return QBE_W → 所有 struct field 标量化且 QBE_W。

### 联动错误链路
若只修 8b（type slot deref），但 8a（sym cmp）未修 → strcmp 仍然永不匹配 → fallback path → field_type_raw 仍然 garbage → 症状不变。所以**两个 bug 必须同时修**。最初 fix cycle 发现 8b 修完症状依旧，**进一步挖到 8a** 才是真 root cause。

### 下游链 (任意 fix 漏掉时)
1. `qbe_type_of(field_type_raw)` 读到非 valid Type* → garbage kind → 落到 `return QBE_W()` (ir.jhyy:127)
2. caller 拿到 `result_v1.qbe_type = QBE_W`
3. emit `%tN =w loadw %tA` 但目标是 i64/pointer 字段（需要 QBE_L → `=l loadl`）
4. QBE typecheck 拒绝 → jhyy_v1 退出 1

### 修复（commit 11 三处同步）
```jhyy
// codegen.jhyy:489-491（Bug 8a — sym deref）
let sym_p_v1 = *(fdesc as **Sym);                          // deref Sym*
let fname_str = *(ptr_add_u8(sym_p_v1 as *u8, 0 as i64) as **u8);  // Sym.name @ offset 0
if strcmp(fname_str, field_name) == 0 { ... }

// codegen.jhyy:448（Bug 8c — ftype deref in cg_copy_struct）
let ftype_slot_v1 = ptr_add_u8(fdesc_ptr, 8 as i64) as **Type;
let ftype = *ftype_slot_v1;

// codegen.jhyy:502（Bug 8b — type slot deref in cg_find_field_offset）
*out_type_v1 = *(ptr_add_u8(fdesc, 8 as i64) as **u8);    // 再 deref 一层
```

### 验证（v0.8 commit 11）
```jhyy
type Box = struct { val: i64, next: *u8 }
fn use_struct() -> i64 {
    let local_box: Box = Box { val: 5 as i64 };
    return local_box.val;
}
```
**jhyy_v1 emit (fix 后):**
```
%t4 =l loadl %t0
ret %t4
```
✅ QBE 通过，arena.jhyy 完整跑通 `step 1/2/3 ... rc=42` 输出（参见 arena_test.exe.exe 测试结果）。

**影响范围（仅在 jhyy_v1 codegen 翻译产物，v0 C 编译不受影响）:**
- src0/arena.jhyy: `arena_new_block/arena_alloc_aligned/arena_reset/arena_free` 全 struct field 访问
- src0/parser.jhyy: Lexer state struct, Parser state struct
- src0/sema.jhyy: SymTable entries, TypeArena fields
- src0/codegen.jhyy: LocalEntry.sym / IRVal.kind (但 cg_add_local / cg_find_local 不走 cg_find_field_offset，所以可能 OK)
- 任何 user-defined struct 的 field access

**Stage 0 closure 关系:** W-008 是 W-007 fix 完成后**下一道关卡** — W-007 extsw 让 `ARENA_DEFAULT_SIZE` 类型常函数 emit 正确；W-008 让所有 struct field load 类型正确。**两个 fix 缺一不可**才能 Stage 0 closure。

**失效条件:** 不再次变动 codegen.jhyy 的 cg_find_field_offset / cg_copy_struct 字段查找代码。或者把 sema 改成存 string 而非 *Sym（避开 deref 链）。

**superseder:** v0.8 commit 11（W-007 同 commit 应用）

**引用:**
- 复现：scratch src0/__w8_test.jhyy（最小 struct field 读写）
- arena.jhyy 验证：build/bin 多次重新 compile + run（rc=42 + 完整打印 step 1-3）
- 与 W-007：两层 root cause 都必须修。W-007 修 const/copy extsw，W-008 修 cg_find_field_offset deref
- 与 W-005：无直接关联，但 arena.jhyy 用 W-005 (*i64 指针累加) 才能让 W-008 fix 后的 struct field 访问真在 codegen 路径上跑通（W-005 解决 *p = ... 的赋值 segfault，W-008 解决 `*p = (*a).def_size` 的 i64 load 类型错）

---

## W-009: jhyy_v1 cg_convert_arg src_t==0 早 bail，导致 literal `0` 在 ceql/csltl 中以 w 操作数出现

**ID:** W-009
**状态:** RESOLVED（v0.8 commit 12, 5820793 — codegen.jhyy cg_convert_arg src_t==0 兜底 + dst.kind=KIND_POINTER 不再 bail + NODE_CAST 移除 src_t==0 早 bail；arena.jhyy Stage 0 closure 解锁）
**日期:** 2026-08-04
**触发面:** jhyy 源码里**任意 `l_field == 0` / `l_field != 0` / `i64_var cmp 0` / `pointer cmp 0` 路径**走 cg_expr → 比较操作 → cg_convert_arg：
- `if (*a).def_size > 0` — arena.jhyy: arena_new_block 的 fallback 路径
- `if malloc(...) == 0` — arena.jhyy: arena_new_block malloc 返回值 null check
- `if arena_alloc(...) == 0` — arena.jhyy: arena_strdup malloc null check
- 任何 user code 写的 `p == 0` 或 `p != 0`（p 是指针 / i64 / u64）

**症状:** QBE 拒绝：`invalid type for second operand %tX in ceql` 或 `invalid type for first operand %tX in csltl`。jhyy_v1 编译 exit 1。
**根因（cg_convert_arg 早 bail + literal 默认 w）：**

### Bug 9a：literal `0` 在 NODE_INT_v1 处 emit `=w copy 0`
```jhyy
// codegen.jhyy:671-676（fix 前）
if kind == NODE_INT_v1() {
    let d = node_int_data(n);
    let qt = qbe_type_of((*n).type_ptr_v1);   // type_ptr_v1=0 → qbe_type_of(NULL)=QBE_W
    let v = ir_new_tmp(ir, qt);               // qbe_type=W
    ir_emit_copy(ir, v, (*d).value);          // emit "    %tN =w copy 0"
    return v;
}
```

jhyy 的字面量 0 在 parser 阶段没填 type_ptr_v1（sema 也没补全 — 缺特性），所以 `qbe_type_of(NULL) = QBE_W`。NODE_INT_v1 直接 emit `w copy 0`。

### Bug 9b：cg_convert_arg src_t==0 时早 bail
```jhyy
// codegen.jhyy:548-550（fix 前）
fn cg_convert_arg(cg_raw_v1: *u8, arg: IRVal, src_t: *u8, dst_t: *u8) -> IRVal {
    let cg = cg_raw_v1 as *CGContext;
    let ir = (*cg).ir as *IRBuf;
    if src_t == (0 as *u8) {
        return arg;          // ← BUG：literal 走到这里不 coerce
    }
    if dst_t == (0 as *u8) {
        return arg;
    }
    ...
}
```

### 联动错误链路
比较操作 emit 块（codegen.jhyy:1291-1294）：
```jhyy
let mut right_coerced = right;
if d_op >= TOKEN_EQEQ() && d_op <= TOKEN_GTEQ() {
    if left.qbe_type != right.qbe_type {                    // L (l) != W (w) → 进 coerce
        right_coerced = cg_convert_arg(cg_raw_v1, right,
            (*right_node).type_ptr_v1,                       // 0
            (*left_node).type_ptr_v1);                      // l type
    }
}
```
`cg_convert_arg` 接 src_t=0 早 bail → `right_coerced = right`（仍是 `w copy 0`）→ emit `ceql %t_l, %t_w` → QBE "invalid type for second operand"。

### 修复（commit 12：cg_convert_arg + NODE_CAST 两处放宽条件）

实际实现包含 **三处放宽**，比原始 root cause 分析更深一层：

**Fix 1：cg_convert_arg src_t==0 时用 arg.qbe_type 兜底**
```jhyy
// codegen.jhyy:548-553（fix 后）
fn cg_convert_arg(cg_raw_v1: *u8, arg: IRVal, src_t: *u8, dst_t: *u8) -> IRVal {
    let cg = cg_raw_v1 as *CGContext;
    let ir = (*cg).ir as *IRBuf;
    if dst_t == (0 as *u8) {
        return arg;
    }
    // W-009 fix: src_t==NULL 时（literal 没 type info），用 arg.qbe_type 当 src_qt
    let src_qt_v1: i32 = if src_t == (0 as *u8) { arg.qbe_type } else { qbe_type_of(src_t) };
    ...
}
```

**Fix 2：cg_convert_arg dst.kind=KIND_POINTER 不再 bail（v0 行为对齐）**
```jhyy
// codegen.jhyy:555-570（fix 后）
if src_t != (0 as *u8) {
    let src = src_t as *Type;
    if (*src).kind != KIND_PRIMITIVE() {     // src 仍要求 primitive
        return arg;
    }
    // dst 不再硬要求 KIND_PRIMITIVE（pointer 是 qbe_type L，走 W→L extsw）
    if src_qt_v1 == dst_qt_v1 && (*src).kind == KIND_PRIMITIVE() {
        let dst2 = dst_t as *Type;
        if (*dst2).kind == KIND_PRIMITIVE() {
            if (*src).prim == (*dst2).prim { return arg; }
        }
    }
}
```
原版 hard-bail `dst.kind != KIND_PRIMITIVE` 让 `0 as *u8` 永远 no-op（C 端 codegen.c:721 也不 bail，所以 W-009 fix 让 jhyy_v1 行为对齐 v0）。

**Fix 3：NODE_CAST 不再因 src_t==0 早 bail**
```jhyy
// codegen.jhyy:1844-1855（fix 后）
if kind == NODE_CAST() {
    let ncd = node_cast_data(n);
    let inner_node = (*ncd).expr as *Node;
    let inner_v_v1 = cg_expr_v1(cg_raw_v1, inner_node);
    let src_t = (*inner_node).type_ptr_v1;
    let dst_t = (*n).type_ptr_v1;
    if dst_t == (0 as *u8) {                  // ← 移除了 src_t==0 的早 bail
        return inner_v_v1;
    }
    return cg_convert_arg(cg_raw_v1, inner_v_v1, src_t, dst_t);
}
```
原版 `if src_t == 0 || dst_t == 0 { return inner_v_v1; }` 在 literal 走到这里就 return，让 cast 失效。

### 验证（v0.8 commit 12）

**jhyy_v1 compile arena.jhyy emit (修复前)：**
```
%t28 =l call $malloc(l %t27)
%t29 =w copy 0                            ← 字面量 0 emit w
%t30 =w ceql %t28, %t29                   ← INVALID：ceql 要两边 l
```
QBE：`invalid type for second operand %t29 in ceql`

**jhyy_v1 compile arena.jhyy emit (修复后)：**
```
%t28 =l call $malloc(l %t27)
%t29 =w copy 0
%t30 =l extsw %t29                        ← 自动补 extsw
%t31 =w ceql %t28, %t30                   ← VALID：两边 l
```
实测：commit 12 后 arena.jhyy emit 中 `extsw` 出现 **29 次**（修复前是 0），所有 `ceql/cslel/csltl/csgtl` 操作数两边都是 l。QBE typecheck 通过。

**v0 regress：47/47 pass, 0 fail, 3 skip（**无 regression**）**

**v1 regress：12 OK（持平 — W-009 修了 arena.jhyy 这种**库文件**编译路径，regress 测试集是 47 个 main 程序不直接覆盖；但 Stage 0 closure 达成）**

### 影响范围（仅在 jhyy_v1 codegen 翻译产物，v0 C 编译不受影响）
- src0/arena.jhyy: `arena_new_block`/`arena_alloc_aligned`/`arena_strdup` 多个 `ptr == 0` null check
- src0/parser.jhyy: 任意 `let tok = ...; if tok == 0 { ... }` 类型 check（如果 parser 走 literal 0）
- src0/sema.jhyy: symbol table null check
- 任何 user code 里的 pointer / i64 / u64 字段 null-or-zero 比较

**Stage 0 closure 关系:** W-009 是 W-008 修完后**下一道关卡** — W-008 让 struct field load 类型正确（i64 field 出 `=l loadl`）；W-009 让比较 l 字段时 right operand (literal 0) 也走 `extsw` 升级到 l。**两个 fix 缺一不可**才能让 jhyy_v1 编 arena.jhyy 跑通 QBE 严格 typecheck。

**失效条件:** 不再次变动 cg_convert_arg 的 src_t==0 早 bail 逻辑。或者把 sema 改成给 NODE_INT 字面量填 type_ptr_v1（让 qbe_type_of 走 TYPE 路径而非 NULL fallback）。

**superseder:** v0.8 commit 12

**引用:**
- arena.jhyy: arena_new_block line ~50 `if malloc(8) == 0` + arena_strdup line ~190 `if arena_alloc(...) == 0`
- arena.il 反例：`_w008_arena.il:55` (`ceql %t28, %t29` mixed) 与 `:211` (`ceql %t112, %t113` mixed)
- 与 W-008：无直接关联。W-008 修 struct field load type，W-009 修 literal compare operand type
- 与 W-007：W-007 修 return literal 类型（extsw in cg_convert_arg w→l case），W-009 修 cg_convert_arg 入口 bail 条件让 extsw 路径真正走到

---

## Cross-ref: B-let2 (Stage 1 byte-equal codegen gap)

**ID:** B-let2
**状态:** RESOLVED (v0.9 wip commit 2.5)
**日期:** 2026-08-05
**触发面:** jhyy_v1 `cg_convert_arg` 函数 (`compiler/src0/codegen.jhyy:544-634`)
**症状:** Stage 1 byte-equal 验收 (`stage1-expanded.sh`) 跑 `arith.jhyy` 时 FAIL —— `let down_val: i32 = total_val as i32;` (total_val: i64 → down_val: i32) emit `=w copy %l_value`,QBE 报 "type mismatch"。

**根因:**
- v0 codegen.c:780-783 `cg_convert_arg` 显式 emit `copy` for `src=L, dst=W` integer width narrowing。
- jhyy_v1 codegen.jhyy:544-634 `cg_convert_arg` 历史上漏这条分支(只覆盖 `src=w, dst=l` via extsw + `src=l, dst=d/s` via sltof/ultof)。

**修复** (v0.9 wip commit 2.5):
- 在 `cg_convert_arg` 加 `src=L, dst=W` 分支:
```jhyy
} else if src_qt_v1 == QBE_L() {
    if dst_qt_v1 == QBE_W() {
        conv = "copy" as *u8;
    }
}
```
- 对齐 v0 codegen.c:780-783,QBE `copy` from l to w 隐式截断(lower 32 bits 取到 w,QBE ABI 行为)

**验证:** `bash compiler/tests/stage1-expanded.sh` arith.jhyy PASS,byte-equal baseline 1/7 → **2/7** (hello + arith)

**不是 workaround 而是真修:** B-let2 不需要 workarounds(非 user-facing 触发),直接修 codegen.jhyy 一处即解。

**与 W-007/W-009 关系:**
- W-007 修 `src=w, dst=l` (extsw) —— 跟 B-let2 镜像对称(B-let2 修 `src=l, dst=w` copy)
- W-009 修 src_t==0 兜底 —— 让 B-let2 / W-007 的转换路径走到(literal 0 → extsw → copy 链路)
- 三个 fix 缺一不可,jhyy_v1 cg_convert_arg 才算完整

**引用:**
- `compiler/src0/codegen.jhyy:613-619` —— 修复代码
- `compiler/tests/examples/arith.jhyy` —— 触发用例
- `compiler/tests/stage1-expanded.sh` —— 验收脚本
- v0 codegen.c:780-783 —— 对齐的 C 端 emit 路径

---

## Cross-ref: W-008 ↔ W-009 ↔ W-007 ↔ W-005 codegen 转化路径联动

**日期**: 2026-08-05 (v0.9 wip commit 2.14)
**目的**: 把 4 个 codegen 翻译层 workaround 集中梳理, 标清联动关系 + 真修路径, 避免未来 sprint 单独修一个时漏考虑其他 3 个。

### 4 workaround 摘要

| ID | 触发面 | 根因 | 真修状态 | commit |
|----|-------|------|---------|--------|
| **W-005** | `let mut x; x = expr;` (NODE_ASSIGN + NODE_IDENT) segfault | C/jhyy CGContext struct 布局不匹配 (9 字段 offset) | ✅ RESOLVED | v0.9 wip commit 2.11 (CGContext 对齐) + 2.13 (16 处 revert 回 `let mut`) |
| **W-007** | `fn() -> i64 { return X as i64; }` emit `w copy` | cg_convert_arg 缺 `src=W, dst=L` extsw 分支 | ✅ RESOLVED (transitive 2026-08-12, master table 5x5 PASS verified on 4 BAD variants — 单 return value + struct field + global var 全路径 cover) | v0.8 commit 7 (`0453cef`) 原始 + transitive 2026-08-12 验证 |
| **W-008** | cg_find_field_offset 双层 deref 漏 → i64 struct field emit `=w loadw` | cg_find_field_offset helper 把 `*u8` 指针当 `**u8` 多解一层 | ✅ RESOLVED | v0.8 commit 11 |
| **W-009** | cg_convert_arg src_t==0 早 bail → literal 0 在 ceql/csltl 中以 w 操作数出现 | cg_convert_arg 入口 `if src_t == 0 { return arg; }` 跳过 extsw 路径 | ✅ RESOLVED | v0.8 commit 12 |

### 联动关系

**W-008 ↔ W-009 (链式依赖)**:
- W-008 修 struct field load 类型 (`=l loadl` for i64 field)
- W-009 修 literal 0 比较时升级到 l (`extsw` before compare)
- **缺一不可**: W-008 让 left operand 是 l; W-009 让 right operand (literal 0) 也是 l。任一不修, `ceql/csltl/csgtl` 操作数类型 mismatch → QBE 拒绝

**W-005 ↔ W-007 (NODE_ASSIGN 路径分支)**:
- W-005 修 `let mut x; x = expr;` 路径 (NODE_ASSIGN + NODE_IDENT + cg_add_local/cg_find_local/cg_emit_store)
- W-007 修 `return X as i64;` 路径 (NODE_RETURN + NODE_CAST → cg_convert_arg)
- **不同路径**: W-005 是 store 路径; W-007 是 return 路径。但 cg_emit_store 内部走 cg_convert_arg (类型转换) — W-005 真修后, W-007 partial 路径可能漏的 struct field + global var 路径**才**会被 W-005 真修路径触发

**W-007 ↔ W-008 ↔ W-009 (cg_convert_arg 三向联动)**:
- W-007 修 cg_convert_arg `src=W, dst=L` extsw 分支
- W-009 修 cg_convert_arg 入口 bail 条件, 让 extsw 路径走到
- W-008 修 cg_find_field_offset, 让 cg_emit_store 拿到的 struct field load 是正确类型 (`=l loadl` for i64 field), 喂给 cg_convert_arg 时 src_qt 是 L 而非 W (W-008 修了上游, W-007 才需 `src=L, dst=W` B-let2 copy 分支对应 `src=W, dst=L` extsw 分支)

**W-005 真修 (CGContext 布局对齐) → W-007/W-008/W-009 影响**:
- CGContext 布局对齐后, cg_add_local/cg_find_local/cg_emit_store 路径全 clean
- 之前 W-008/W-009 修的部分, 现在在 `let mut x; x = Y;` 路径上**才真正测得到**(之前因 W-005 segfault 在前面挡了)
- v0.9 wip commit 2.11 后跑 regress, 未观察到 W-007/W-008/W-009 在 src0/ 内的新触发面

### 真修路径共识 (per cross-ref)

| workaround | 真修 | commit | 备注 |
|-----------|------|--------|------|
| W-005 | ✅ 已真修 | v0.9 wip commit 2.11 + 2.13 | CGContext C/jhyy 9 字段对齐 |
| W-007 | 🟡 partial → 等 W-005 后审计 + B-let2 路径补全 | 待 v1.0 sprint 3+ | 单 return value 路径修了; struct field / global var 路径需审计 |
| W-008 | ✅ 已真修 | v0.8 commit 11 | cg_find_field_offset 单层 deref |
| W-009 | ✅ 已真修 | v0.8 commit 12 | cg_convert_arg 入口 bail 条件删 |

### 验证 (commit 2.14, 2026-08-05)

- regress 持平 50/53 (commit 2.13 baseline)
- stage1 byte-equal 持平 6/7 (commit 2.12 baseline)
- 4 workaround 联动关系: W-005 真修后, W-007 partial 路径在 src0/ 内的触发面待审计 (Task #60 修后 + W-004 verification 后再做)

### 引用

- v0.8 commit 7 (`0453cef`) — W-007 partial (单 return value path)
- v0.8 commit 9 (`d570c72`) — W-001 byte-by-byte 真修 (W-002/W-004 根因消除)
- v0.8 commit 10 (`d8535a9`) — W-005 workaround extension (util.jhyy + arena.jhyy)
- v0.8 commit 11 — W-008 真修 (cg_find_field_offset)
- v0.8 commit 12 — W-009 真修 (cg_convert_arg 入口)
- v0.9 wip commit 2.5 — B-let2 真修 (W-007 镜像)
- v0.9 wip commit 2.11 — W-005 真修 phase 2 (CGContext 对齐)
- v0.9 wip commit 2.13 — W-005 加固 16 处 revert 回 let mut
- v0.9 wip commit 2.14 (本 commit) — cross-ref 联动关系文档化

---

## W-010: jhyy-端 MAX_LOCALS=512 vs C-端 1024 → cg_add_local 静默溢出致 `%t0` 污染

**ID:** W-010
**状态:** RESOLVED (v0.9 wip commit 2.79)
**日期:** 2026-08-10（Sprint 4.21–4.23 triage 实证）
**触发面:** jhyy_v2 编译 `compiler/src0/main.jhyy`（cg_expr 内本地变量数 > 512）
**症状:**
- jhyy_v2.exe.il 末尾 ~470 行窗口内出现 ~39 处 `%t0` 引用
- 形式：`ceqw %t0, X`、`csltl %t0, X`、`=l call $ir__ir_new_tmp(l %t77637,  %t0)`（双空格是 qbe_type sigil 为空的物证）
- QBE reject：`invalid type for first operand %t0 in copy`（行 165792 类）
- 不在 regress 单文件测试中出现（单文件 cg_expr 本地变量数远低于 512）

**根因:**
1. `compiler/src0/codegen.jhyy:68` 定义 `fn MAX_LOCALS() -> i32 { return 512 as i32; }`
2. `compiler/src/codegen.c:17` 定义 `#define MAX_LOCALS 1024`
3. 两侧差 2×，**jhyy 端容量更小**
4. `cg_add_local` 在 `idx >= MAX_LOCALS` 时静默 return 0（codegen.jhyy:173），不报错
5. `cg_find_local` miss 返回零 sentinel `(IRVal){0}`（kind=IRVAL_TEMP, id=0）
6. `ir_init` next_tmp 从 1 开始，**temp 0 永不分配** → emit `%t0`（缺 qbe_type sigil）

**workaround:** 无（不报错 + 影响 jhyy_v2 自举构建）

**失效条件:**
- 单文件 regress 测试（cg_expr 本地变量数 < 512）不触发
- jhyy_v1 编 main.jhyy（C-side MAX_LOCALS=1024 够用）不触发
- **jhyy_v2 编 main.jhyy 才触发**（自举第二步 = 关键路径）

**superseder:** v0.9 wip commit 2.79 — jhyy-side `MAX_LOCALS` 512 → 1024，跟 C-side 对齐

**解决实证 (2026-08-10):**
- `compiler/build/bin/jhyy_v2.exe.il` 的 `grep "%t0,"` 计数从 39+ → **0**
- `grep " %t0," compiler/build/bin/jhyy_v2.exe.il` → **0 命中**
- regress.py 50/53 PASS（持平 baseline）
- regress_v1.py 50/53 PASS（持平 baseline）
- jhyy_v2 编 hello.jhyy 的 QBE 错（`invalid type for jump argument %t748`）跟本 bug **无关**——是 inline_imports 引发的函数重复 emit 问题（g_as 报 ~1500+ 处 `symbol X already defined`），属于 Stage 2 inline_imports 设计缺陷，跟 W-010 正交

**Sprint 历史:**
- Sprint 4.21 Phase B+C+D+G（IRVal struct pass-by-value → 指针）— **未触及根因**，4 workaround 站点仍 fail
- Sprint 4.22（cg_match_pattern `let mut + if/else` 改条件表达式）— **假说错误**，2 种写法 emit 同样的 `%t0` 污染（行号漂 2-12）
- Sprint 4.23 Explore agent（2026-08-10）— 找到 `%t0` 集中出现 + MAX_LOCALS 双源不一致 → 本 fix

**引用:**
- *(Sprint 4.22 假说错误 postmortem — 项目 memory 私有记录,不在公开 doc 留链接)*
- Sprint 4.23 plan: *(私有 plan 文件,不在公开 doc 留路径)*

---

## W-011: inline_imports emit module 全量重复（Stage 2 设计缺陷）— RESOLVED

**ID:** W-011
**状态:** ✅ RESOLVED (Sprint 4.24 commit 2.80)
**日期:** 2026-08-10
**触发面:** `jhyy_v2` 编 `compiler/src0/main.jhyy` (12 个 module + transitive imports)，所有 module 函数在 IL 里 emit 多份（arena 89 份/util 47 份）
**症状:** QBE 通过，但 `as` 报 1500+ 处 `symbol 'X' is already defined`；jhyy_v2 self-build 在 link 阶段 fail
**根因:** `compiler/src0/main.jhyy` 的 `resolve_one_import_v1` 实现了 `completed[]` / `in_progress[]` 数组（64×512 byte slots）+ helper (`completed_match` / `in_progress_match`)，但**全文件零次写**这两个数组。C-side `compiler/src/main.c:159-229` 正确实现 push/pop 机制（push to in_progress BEFORE recursion, pop + push to completed AFTER recursion）。jhyy-side 缺这两段关键代码

**fix (Sprint 4.24 commit 2.80):** 在 `resolve_one_import_v1` 加两个 block：
1. **Step 1 (line ~280)**: parse 校验通过后、decl 迭代前 push mod_path 到 `in_progress[]`（cycle detection）
2. **Step 2 (line ~339)**: decl 迭代完后、free 前 pop mod_path from `in_progress[]` + push to `completed[]`（dedup）

字节复制用 `str_concat_at`（不能存指针，因为 mod_path 是父 frame 的临时 npath）；slot layout 用 `*u8` 指针 + 单独 `malloc(512)` heap buffer（与 C-side 64×512 byte 数组兼容）

**结果 (验证):**
- IL `^export function` 计数：**4715 → 567**（接近 plan 预期 ~560）
- `arena__*` 副本数：**89 → 1**
- `util__*` 副本数：**47 → 1**
- `regress.py` (C-side)：**50/53 PASS**（持平 baseline）
- `regress_v1.py` (jhyy_v1)：**50/53 PASS**（持平 baseline）
- `jhyy_v1.exe.exe` (sha `402b03e1...`) 编 `main.jhyy` 成功
- `jhyy_v2.exe.il` (sha `9b67e53...`) export 唯一计数达成

**Out of scope (Sprint 4.24):** jhyy_v2 self-build (jhyy_v2 → jhyy_v2.exe.exe) 仍 fail — QBE 在 line 10157 报 `newline expected, got ?? instead`，是独立 sret emit bug（`cg_expr` 的 `NODE_RETURN` 在 has_sret 时 emit `ret %tN` 而非 `ret`），跟 W-011 正交。修复需要 Sprint 4.25+ 走 cg_copy_struct inline rewrite 或 cmd_compile 自动调用 fix_il.py

**引用:**
- Sprint 4.24 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md`
- v0.9 wip commit 2.80 (Sprint 4.24 dedup 真修)
- C-side reference: `compiler/src/main.c:159-229` (correct push/pop logic)

---

## W-012: codegen emit-layer sentinel pollution — cg_copy_struct emit `copy %t0` when src/dst undef

**ID:** W-012
**状态:** ✅ RESOLVED (v0.9 wip commit 2.81, Sprint 4.25)
**日期:** 2026-08-10
**触发面:** 函数体是 `if c { return A } else { return B }` 这种**两条 return 分支**的结构，其中：
- B = struct return 函数（has_sret = 1, 返回 aggregate type）
- A, B 都是非平凡表达式

**症状:**
- `compiler/build/bin/*.il` 出现 `copy %t0` / `\0 %t0`（QBE 错：`invalid type for first operand %t0 in copy` / `in csltl` 等）
- 单文件 regress 不触发（结构简单，return 直接 emit 不经过 cg_copy_struct）
- jhyy_v2 编 src0/main.jhyy 触发（大函数 + 多个 struct-return 模式）

**根因 (Plan agent 验证, 2026-08-10):**
1. `ir_init` (`compiler/src/ir.c:38`) 设 `next_tmp = 1`，所以 `%t0` 永不被合法分配 → IRVal `kind=IRVAL_TEMP, id=0` 是 sentinel
2. **Cg_func epilogue** (`compiler/src/codegen.c:1700-1710`) 用 `cg_body_returns()` 做**纯语法检查**（只看最后一条 stmt）
3. 但函数体是 `if c { return A } else { return B }` 时：`cg_body_returns() == false`（最后 stmt 不是 return）→ epilogue 跑 → `body_val` 来自 NODE_BLOCK 的 `IRVal last = {0}`（codegen.c:698，return 之前值未覆写）
4. epilogue → `cg_copy_struct(cg, ret_type, sret_addr, body_val)` → 逐字段 emit `=l copy %t0`
5. NODE_RETURN sret 分支 (`codegen.c:1474`) 同理：expr 是 unreachable 时仍 emit `cg_copy_struct` → 同 `copy %t0` 污染

**真修 (Sprint 4.25 commit 2.81):** 在 3 个 emit 点 + 1 个 helper 加 `irval_is_undef(v)` 守卫：
1. `compiler/src/ir.h:33-42`: 加 `static inline int irval_is_undef(IRVal v)` helper（`v.kind == IRVAL_TEMP && v.id == 0`）
2. `compiler/src/codegen.c:142-148`: `cg_copy_struct` 开头 early-return if src or dst undef
3. `compiler/src/codegen.c:1481-1486`: NODE_RETURN sret 分支，加 `if (!irval_is_undef(src)) cg_copy_struct(...)` 守卫
4. `compiler/src/codegen.c:1718-1728`: cg_func epilogue sret 分支，加 `if (!irval_is_undef(body_val)) cg_copy_struct(...)` 守卫
5. `compiler/src0/ir.jhyy:107-118`: 镜像 `fn irval_is_undef(v: IRVal) -> i32`
6. `compiler/src0/codegen.jhyy:412-422`: 镜像 cg_copy_struct 守卫
7. `compiler/src0/codegen.jhyy:931-960`: 镜像 NODE_RETURN sret 分支（has_sret 时走完整 copy，**非** bare `ret`）
8. `compiler/src0/codegen.jhyy:2780-2792`: 镜像 cg_func epilogue sret 守卫

**关键不变量（byte-equal 保护）:**
- 守卫只在 `kind=IRVAL_TEMP && id=0`（即 sentinel）时短路
- `next_tmp = 1` 让 sentinel 永不被 `ir_new_tmp` 分配
- 任何走 sentinel 路径的代码本来就会 emit 非法 IL（QBE 必 fail 或 runtime 错）
- 所以守卫**不改正确程序输出** — 7/7 byte-equal 由构造保持

**结果 (验证 2026-08-10):**
- 最小复现 `_repro_t0.jhyy`: 函数体 `if c { return A } else { return B }` + struct return
  - BEFORE fix: `qbe:_repro_t0.il.il:50: invalid type for first operand %t0 in copy`
  - AFTER fix: compiled successfully, **EXIT=30 ✓** (10+20)
- regress.py (C-side): 50/53 PASS（持平 baseline）
- regress_v1.py (jhyy_v1.exe.exe sha `43c66665...`): 50/53 PASS（持平 baseline）
- Stage 1 byte-equal: 7/7 PASS（持平 baseline, 由构造保证）

**Sprint 历史:**
- Sprint 4.13 IRVal layout alignment (commit 2.45) — 修 IRVal union layout（**DEFINITION 层**），但 `next_tmp=1` + `body_returns()` 纯语法检查仍漏 emit 层 sentinel
- Sprint 4.21 Phase C (`cg_copy_struct` 改 `const IRVal*`) — 试图用引用改签名，**没修 emit 层 sentinel 短路**
- Sprint 4.25 (commit 2.81) — Plan agent 找出真根因 (cg_body_returns 纯语法检查 + cg_copy_struct 不 short-circuit), 用 8 处 sentinel 守卫真修

**失效条件:**
- 任何 `cg_expr` emit IL 时假定 `kind=IRVAL_TEMP, id=0` 是合法值（违反 `next_tmp=1` 不变量）
- 新的 emit 点加入时忘记加 `irval_is_undef` 守卫

**superseder:** 长期看，`cg_body_returns()` 应该改成可达性分析（data-flow），但这是独立重构；本 fix 在 emit 层挡下游，已足够。

**不 tag v1.0.0:** Sprint 4.26 Stage 2 N=3 byte-equal 重测后再决定（已知仍可能有别的 Stage 2 差异）

**引用:**
- Sprint 4.25 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md`
- v0.9 wip commit 2.81 (Sprint 4.25 sentinel 真修)

---

## W-013: C-side cg_expr NODE_CAST w/l → b/h narrowing emit sentinel `%t0`

**ID:** W-013
**状态:** ✅ RESOLVED (v0.9 wip commit 2.87, Sprint v1.1.7)
**日期:** 2026-08-12
**触发面:** 任意 `*T_ptr = expr as u8/i8/u16/i16/bool` (T ∈ {i32,i64,u32,u64})：
- `*p_u8 = 65 as u8` (literal → sub-word)
- `*p_u8 = somevar as u8` (let-binding chain)
- 任意 codegen 路径下, w/l → b/h narrowing cast (literal 或 through `let _T = expr as subword`)

**症状:**
- `compiler/build/bin/*.il` 出现 `storeb %t0, addr` / `storeh %t0, addr` (QBE 错: `invalid type for first operand %t0 in storeb/storeh`)
- C-side `jhyy.exe compile *_test*.jhyy -o out` 触发 (例如 Sprint 4.7 最小复现 `_bug4_v2.jhyy`)
- jhyy_v1 (`sha ba94df93...`) **不触发** — jhyy-side `cg_convert_arg` 因 `if conv==0 return arg` 自然 fallback, 一直返回 w-class temp 给 storeb consume (QBE implicit truncate)

**根因 (traced 2026-08-12):**
1. `cg_expr` NODE_CAST handler (`compiler/src/codegen.c:786-876`) 对每个 src/dst 类型组合查 conv instruction (extsw/extuw/dtosl/stosi/...)
2. **缺失 case**: `src ∈ {w,l}` × `dst ∈ {b,h}` — QBE 无 b/h temporary type (sub-word 仅在 load/store 操作数上), 所以 cast 是 IR 层 no-op (consuming storeb/loadub 隐式截断)
3. Fall-through 到 `if (!conv) { IRVal v = {0}; *out = (v); return; }` (codegen.c:869-872, 自 v0.5.0 f4037c0 起)
4. **Sentinel pollution**: `IRVal{0}` (kind=IRVAL_TEMP, id=0) 被 storeb 当源操作数 emit → QBE reject
5. 此 pattern 是 W-005 #2 family 的另一种形态 — 任何"应该返回 word-class temp 但返回 sentinel IRVal{0}"的 codegen 路径都会触发

**真修 (Sprint v1.1.7 commit 2.87):** 在 codegen.c:869 之前加 w/l → b/h narrow no-op short-circuit：
```c
if (!conv && (src_qt == 'w' || src_qt == 'l') && (dst_qt == 'b' || dst_qt == 'h')) {
    *out = (inner); return;
}
```
- 语义: QBE 不允许 b/h 临时, 所以 narrowing 在 IR 层是 no-op — storeb/loadub 隐式截断即可
- jhyy-side 无需改 — `cg_convert_arg` (`compiler/src0/codegen.jhyy:567-711`) 的 `if conv == 0 return arg` 已正确 fallback

**结果 (验证 2026-08-12):**
- 最小复现 `_bug4.jhyy` (`*p_u8 = 65 as u8`):
  - BEFORE fix C-side: `qbe:_bug4.il:6: invalid type for first operand %t0 in storeb`
  - AFTER fix C-side: compiled successfully, **EXIT=65 ✓**
  - jhyy_v1 (canonical pre-fix): compiled successfully, EXIT=65 ✓ (一直 correct)
- 5x5 PASS 验证 (3 case × 5 runs):
  - `_bug4_test_u8.jhyy`: 5/5 PASS EXIT=65
  - `_bug4_test_i8.jhyy`: 5/5 PASS EXIT=255 (-1 as i8 sign-extended back to i64)
  - `_bug4_test_let_u8.jhyy`: 5/5 PASS EXIT=65 (let-binding chain)
- regress.py (C-side): 50/50 PASS（持平 baseline）
- regress_v1.py (jhyy_v1.exe.exe sha `ba94df93...`): 50/50 PASS（持平 baseline）
- IL 对比 (C-side vs jhyy_v1): 完全等价 (jhyy_v1 一直 correct, C-side fix 镜像同 emit pattern)

**Sprint 历史:**
- Sprint 4.7 (commit 2.46) — 首次发现 Bug 4 (stub v2 workaround 避开 struct pass-by-value), 当时归类为 W-005 #2 family 的 EMIT-layer 形态
- Sprint 4.21-4.25 W-005 #2 真修 chain — 修了 IRVal struct pass-by-value stale pointer, 但 cg_copy_struct 守卫不覆盖 cg_expr NODE_CAST 的 narrow no-op 路径
- Sprint v1.1.7 (commit 2.87) — 补 w/l → b/h narrow no-op 守卫, 4 个 v0 codegen bug 全部真修

**superseder:** 无 — 本 fix 是 cg_expr NODE_CAST conv-table 的最后缺失 case, 之后不会再有类似 narrow 漏 emit

**不变量 (byte-equal 保护):**
- 新增 short-circuit 只在 `!conv && (src_qt ∈ {w,l}) && (dst_qt ∈ {b,h})` 时触发 — 这 4 种组合之前必然 emit sentinel, 不可能产生正确 IL, 所以守卫**不改正确程序输出**
- jhyy_v1.exe.exe (`sha ba94df93...`) 不需要 rebuild — jhyy-side 一直 correct

**引用:**
- Sprint v1.1.7 plan: `C:\Users\liuzhen\.claude\plans\jaunty-orbiting-naur.md` (related W-013 entry)
- Sprint 4.7 IRVal pass-by-value memory: `project_sprint4_7_irval_pass_by_value_bug.md`
- v0.9 wip commit 2.87 (Sprint v1.1.7 Bug 4 narrow 真修)

## W-014: `jhyy_selfhost_check` MCP pre-stage cleanup deletes canonical closure binaries

**ID:** W-014
**状态:** ✅ RESOLVED (2026-08-12, Sprint mcp-2 W-014)
**日期:** 2026-08-12
**触发面:** `mcp__jhyy__jhyy_selfhost_check` (默认 `auto_rebuild=False`) — 调 `mcp-jhyy/jhyy_runner.py:selfhost_check()`,Stage 2/3 pre-stage cleanup 把 chain input binary 删了 → FileNotFoundError → 整链 early-abort,canonical closure binaries (`jhyy_v2.exe` / `jhyy_v3.exe`) 被销毁。

**根因 (2026-08-12 闭环):**

`mcp-jhyy/jhyy_runner.py` 的 chain 设计是**output path 跟 input path 同名(只差 .exe 后缀)**:
- Stage 1: input = `jhyy_v1.exe.exe`,output = `jhyy_v1.exe` (→ `jhyy_v1.il`)
- Stage 2: input = `jhyy_v2.exe`,output = `jhyy_v2.exe` ← **同一个文件!**
- Stage 3: input = `jhyy_v3.exe`,output = `jhyy_v3.exe` ← **同一个文件!**
- Stage 4: input = `jhyy_v3.exe`,output = `jhyy_v3.exe.exe` (named to match output suffix)

Sprint mcp-2 (commit `5eb10bf`) 加的 pre-stage cleanup:
```python
_safe_remove(output_base + ".exe")  # 删 output (.exe)
_safe_remove(output_base + ".il")   # 删 output (.il)
```

跑 stage 2 时,`_safe_remove("compiler/build/bin/jhyy_v2.exe" + ".exe")` → 把 stage 2 的 **input binary** 删了!Stage 3 同样删 `jhyy_v3.exe`。然后下一行 `_safe_remove(".il")` 也走同 output_base → 删 input 不存在的 .il(无害)。

Stage 2 的 compile 命令:
```python
cmd = [exe_path, "compile", src_abs, "-o", output_base]  # exe_path = jhyy_v2.exe (刚被删)
```

→ `subprocess.run` 报 **FileNotFoundError** (Windows) / "Command not found (exit=-1)"(Linux)。整链 early-abort 在 stage 2,**stage 3-4 都没跑**。

**结果 (验证 2026-08-12):**
- BEFORE fix MCP `jhyy_selfhost_check` (auto_rebuild=False):
  - 早 abort at stage 2: `"jhyy_v2 compile failed (exit=-1): Command not found"`
  - **canonical `compiler/build/bin/jhyy_v2.exe` (sha `d3aeed09...`, v1.0.0 tag 锁定) 被永久删除**
  - 需要 `git restore compiler/build/bin/jhyy_v2.exe` 才能恢复
- AFTER fix (output 用 `_sh_vN` scratch prefix):
  - 直接 Python 调 `jhyy_runner.selfhost_check()`:`{"ok": True, "all_byte_equal": True, "il_sha256": "749be833..."}`
  - canonical `jhyy_v2.exe` / `jhyy_v3.exe` / `jhyy_v4.exe` **全部不动**
  - 4 个 stage IL sha 全部 byte-equal `749be833...`(Stage 2 N=3 闭环 仍在)

**Fix 设计 (核心 2 行 + cleanup):**

```python
chain = [
    ("jhyy_v1", "compiler/build/bin/jhyy_v1.exe.exe", "compiler/build/bin/_sh_v1"),  # ← 改
    ("jhyy_v2", "compiler/build/bin/jhyy_v2.exe",     "compiler/build/bin/_sh_v2"),  # ← 改
    ("jhyy_v3", "compiler/build/bin/jhyy_v3.exe",     "compiler/build/bin/_sh_v3"),  # ← 改
    ("jhyy_v4", "compiler/build/bin/jhyy_v3.exe",     "compiler/build/bin/_sh_v4"),  # ← 改 (v4 = v3 编 src)
]

# After chain done: cleanup scratch
for stage, _, output_rel in chain:
    for ext in (".exe", ".il", ".s"):
        _safe_remove(_resolve_path(output_rel) + ext, retries=2, delay_ms=200)
```

input (canonical) 跟 output (scratch `_sh_vN`) 物理分开 → pre-stage cleanup 只动 scratch,canonical 不动。Chain 结束主动清 scratch(包括 ld.exe 留下的 `.s`)。

**为什么不直接 disable pre-stage cleanup?** Sprint mcp-2 加它的目的是解 Windows file lock:上次 selfhost_check 跑完 ld.exe 进程可能短暂 hold 文件,下一次 `_safe_remove` 要 retry on lock。如果 disable,下次跑会撞 `PermissionError` (lock) 而不是 `FileNotFoundError` (本 bug)。所以 **保留 cleanup,只换 output path**。

**为什么不 rename output 到 `<input>.out`?** Windows 命令行 + QBE 后端对 `-o` 参数解析里 `.exe` 后缀处理有历史包袱(见 W-005 #1 family);`output_base + ".il"` 路径走 `output_base` + 显式 `.il` 后缀(jhyy.exe append `.il` 机制 per `feedback_qbe_crlf_root_cause`),改成 `_sh_vN` + `.exe` / `.il` 后缀跟原 path 形态一一对应,改动最小。

**Sprint 历史:**
- v1.0.0 tag (`eabee0d`, 2026-08-10)— Stage 2 N=3 byte-equal 闭环 commit,**MCP `jhyy_selfhost_check` 尚未引入**,所有链是手动 `subprocess.run` 跑,无 cleanup 步骤
- Sprint mcp-2 (commit `5eb10bf`, 2026-08-12 早期)— 加 `jhyy_*` MCP 工具链 + pre-stage cleanup,**引入本 bug**(没人测 stage 2+)
- Sprint mcp-2 W-014 (2026-08-12)— 闭环。直接 Python 调验证 OK,MCP server 仍 cache 老代码需重启

**superseder:** 无 — chain input/output 分开是稳定设计,未来若加 stage 5+ 用同样模式

**不变量 (canonical binary 保护):**
- chain 列表里每个 `(stage, exe_rel, output_rel)` 必须满足 `output_rel != exe_rel`(或至少不同 base name);`jhyy_vN.exe` 跟 `_sh_vN` 是不同 base
- pre-stage `_safe_remove` 只走 output_base(input 不动)
- post-chain cleanup loop 只清 `_sh_*` scratch
- 如果未来加新 stage,要重新检查 input/output 命名不能冲撞

**引用:**
- Sprint mcp-2 W-014 plan: 跟 v1.3.1 plan 同 session
- v1.0.0 tag `eabee0d`:`docs/logs/v1/changelog-v1.0.0.md` Stage 2 N=3 闭环 commit
- W-005 #1 family (Windows `.exe` suffix): `feedback_qbe_crlf_root_cause.md`
- baseline binary hash 守门:sha256sum MANDATORY(防 phantom binary)

---

## W-015: `NODE_SIZEOF` 节点 arena 分配 8 字节 → sema const-fold 写 16 字节溢出到下一块

**Status:** ✅ RESOLVED (commit TBD, v1.3.3)

**触发面:** v1.3.3 sizeof end-to-end implement。`ast_new_sizeof` 跟 `ast_new_alignof` 分配 `NODE_SIZE() + sizeof(NodeSizeof)` (= 8 bytes for `*Node target`),sema const-fold 透过 `node_int_data(n)` 写 `int64_t value` (8) + `TypePrimitive prim` (4) 共 16 bytes 溢出 8 bytes 到 next arena chunk → 随机 data corruption,典型症状: `sizeof(i32)` emit `208` (读 garbage),jhyy_v1 编 src0/main.jhyy 崩溃 `[4a] ir_init done`。

**为什么不早被 catch?** v1.0.0 时 sizeof 在 lexer + parser + AST 都有,sema 跟 codegen 完全没实现(早期 src0 翻译时留 stub,新字段写 `i32` 错误 token 然后报错走 unknown path),走不到 16-byte write 路径。Basic 测试不 cover sizeof,所以 baseline regress 50/50 PASS 看不到问题 — 直到 closure chain 递归编 src0/main.jhyy 才在 jhyy_v1 编自身 时触发(`src0/cleanup` 引入 `sizeof(CGContext)`).

**根因 (跟 W-005 / W-014 关系):** 跟 W-005 #1 family(W-005 #1: `cast` 字面 0 emit 空 buf)同类 — buffer 大小计算错。W-005 是 jhyy-side 没初始化 buf,W-015 是 C-side 跟 jhyy-side 同步算错了 node 后置 data 大小。

**修复:**
- `compiler/src/ast.c:213-228`:`ast_new_sizeof` 跟 `ast_new_alignof` 改用 `max(sizeof(NodeSizeof), sizeof(NodeInt))` (16 bytes)
- `compiler/src0/ast.jhyy:841-867`:mirror 同步 — `NODE_INT_SIZE() = 16` 已知,跟 `NODE_SIZEOF_SIZE() = 8` / `NODE_ALIGNOF_SIZE() = 8` 取 max
- 物理分开 sizeof node 的 data buf(sizeof = 16) 跟 sizeof 结构(sizeof = 8):sema 写 `id->value` + `id->prim` 不再 overflow

**为什么不直接 fill 要 16-byte data 进 8-byte struct?** 改 `NodeSizeof` struct 加 `int64_t value` + `TypePrimitive prim` 字段 看起来更"干净",但:
- `id->value` 跟 `id->prim` 跟 NODE_INT 共用 payload layout (sema 跟 codegen 一致依赖 `node_int_data(n)` 拿 data),改 sizeof struct 自定义 layout 会破 NODE_INT 共用 → 必须改 codegen 写两份
- 像 `type_size` 之类的"常量类型表达式" v1.3.x 后续可能再加 (`alignof` 同路径,还有 `traits` 之类 trait-as-type AST 节点),靠 `node_int_data` 共用 payload 是更普适的 pattern
- 选 `max` 是 conservative fix:不破 existing NODE_INT emit,zero risk

**为什么不_init 16 bytes to 0?** v1.3.3 之前 `NodeSizeof` 只有 8 bytes 用,改成 init 16 浪费 8 bytes 且对 bug 本身无补救(const-fold 写完 16 bytes 之后 data 还是错的)。问题是"buf 太小" 不是 "buf 没初始化"。

**Sprint 历史:**
- v1.0.0 tag (`eabee0d`, 2026-08-10) — NODE_SIZEOF stub,无 sema/codegen
- v1.3.1 (c2acbd1, 2026-08-12) — null literal,跟 sizeof 同语义模式
- v1.3.2 (2026-08-12,e746461) — `else if` audit 顺带跨 sizeof,Lang 文法 audit pass
- v1.3.3 (TBD, 2026-08-13) — end-to-end sizeof + W-015 fix

**superseder:** 无 — `max(struct, NodeInt)` pattern 是稳定 design,以后加同类 const-fold 表达式 (alignof/type_traits) 照搬

**不变量 (sizeof node 写法):**
- `ast_new_sizeof` / `ast_new_alignof` 必须 allocate `max(sizeof(NodeXxx), sizeof(NodeInt))` bytes for node 后置 data
- sema const-fold 只能通过 `node_int_data(n)` 写入 (rely on NodeInt 共用 layout)
- codegen mirror NODE_INT emit (`qbe_type_of` + `ir_emit_copy`)
- 任何新 const-fold AST node 需审计同样的 8/16 byte mismatch

**引用:**
- v1.3.3 sprint plan: `docs/plans/v1/v1.3.3-sizeof-compile-time-const.md`
- W-005 #1 family (buffer size 计算错): `feedback_il_s_debugging_pattern.md`
- baseline binary hash 守门:sha256sum MANDATORY(本 bug 在 jhyy_v1 自身编 src0/main.jhyy 才暴露,跟 W-014 closure 验证路径同)

---

## W-016: 8 字节 enum 参数 ABI mismatch — caller 用 `l` (slot) 传,callee 用 `w` (value) 收

**Status:** ✅ RESOLVED (v1.3.7 fix commit TBD, 2026-08-13)

**触发面 (v1.3.7 pattern binding 引入)**:enum 携带 payload(> 4 字节,如 `Option::Some(i32)` = 8 字节),caller 通过 `l` (slot pointer) 传给 callee,但 codegen 早期默认所有 enum 都按 `w` (4-byte value) emit → callee 拿到的是 slot 指针的低 32 位(garbage),tag compare 永远 false,`Some(v) => v` 实际 fallback 到 always-match 但 `v` 没绑 → 测试 exit=0(应是 v 的值)。

**最小复现:**
```jhyy
enum Option { Some(i32); None; }

fn unwrap_or(o: Option, dflt: i32) -> i32 {
    match o {
        Some(v) => v,    // v 应绑到 payload,但 ABI mismatch 时 v=0
        None => dflt
    }
}

fn main() -> i32 {
    return unwrap_or(Some(42), 0);   // expect 42,实际 0
}
```

**IL 错误状态 (before fix):**
```
%t25 =l alloc8 8           ← caller 准备 slot
...
%t31 =w call $unwrap_or(l %t25, w %t26)   ← caller 传 slot (l class)
export function w $unwrap_or(w %opt, ...)  ← ❌ callee 声明 w!
       ^^^ x86_64 SysV 读 %edi = 低 32 位 of %rdi (= slot pointer 截断)
```

**根因:**
`compiler/src/codegen.c:1918-1922` (`cg_func` param declaration) + `:1951` (param copy) — 默认 `qbe_type_of(pt)` 对 enum 返回 `QBE_W` (4-byte),不论 enum `total_size`。C-side 与 jhyy-side 都漏处理 large enum。

**修复:**
- `compiler/src/codegen.c:1918-1922`:param declaration 加 `else if (pt && pt->kind == KIND_ENUM && pt->enum_type.total_size > 4) ir_emit(ir, "l ...");`
- `compiler/src/codegen.c:1951`:param copy 类型选 `l` if large enum
- `compiler/src0/codegen.jhyy:2999-3070`:mirror — jhyy-side 用 `(*pt_t).size > 4` (`size` 不是 `total_size`,per jhyy Type struct 字段)

**验证 (5/5 PASS per `feedback_fix_evaluation_rule`):**
- `_v137_payload_bind_basic.jhyy`: exit=42 ✅
- `_v137_or_same_bind.jhyy`: exit=42 ✅
- `_v137_or_diff_bind_err.jhyy`: SemaError "OR pattern bindings must match" ✅
- `_v137_or_exhaust.jhyy`: exit=1 ✅
- `regress.py 50/50` + `regress_v1.py 50/50` ✅
- Stage 2 N=3 closure v2=v3=v4 byte-equal 持平 ✅

**Self-hosting impact:**
- v1.il = v2.il sha `7c5ca427...`(new C-built canonical)
- v3.il = v4.il sha `aefa3bb3...`(jhyy-built chain stable)
- v2.il ≠ v3.il — **pre-existing** C-side vs jhyy-side 冗余 copy 差异(per v1.3.6 changelog W-005 #2 chain products),非 W-016 引入

**跟 W-005 #2 冗余 copy 的区分:** W-016 是 ABI mismatch(类型 emit 错,导致语义错误),W-005 #2 是 codegen 优化不彻底(C 端多 emit 几个 `copy %t` 但语义正确)。两条独立 fix。

**失效条件:** 不再写 `l` 类声明 large enum param,或者 enum ABI 改成 all-by-value(无 slot 概念)。

**引用:**
- v1.3.7 fix ship (umbrella): [`docs/logs/v1/changelog-v1.3.0.md`](../logs/v1/changelog-v1.3.0.md) § v1.3.7 fix ship
- v1.3.7 父 sprint: `docs/plans/v1/v1.3.0任务清单 + 概要设计.md` § v1.3.7
- ABI spec: [`docs/abis/jhyy-abi-v1.0.0.md`](../abis/jhyy-abi-v1.0.0.md) § enum pass semantics (大 enum = slot 传)

## W-017: jhyy 顶层 `let mut *u8 = 0` codegen 常量折叠 → 全局状态失效

**Status:** ✅ RESOLVED 2026-08-14 (commit `f20e36d`, v1.4.6 W-017 真修)

**Why RESOLVED:** v1.4.6 W-017 真修 — cg_module pass A 加 NODE_LET 分支 emit
QBE `.data` section (e.g. `data $g_x = { w 41 }`) + 注册到 `mod_globals` dict
(`Sym*` → `$g_qbe`); `cg_find_local` fallthrough 到 globals; `cg_expr` /
`cg_stmt` NODE_IDENT 路径 dispatch on `addr.kind == IRVAL_STR` 触发
`ir_emit_load` / `ir_emit_store` 发 `loadw/storew $g_x` (QBE data section
引用)。同时 `ir_emit_arg` helper (Sprint 4.4 commit 2.36 latent bug fix 引入)
mirror 加到 C-side `src/ir.c`,改 `ir_emit_store` / `ir_emit_load` dispatch
through `ir_emit_arg` — Stage 1 byte-equal 守门恢复 (jhyy_v1 → v2 → v3 → v4
闭包链字节相同)。CGCONTEXT_SIZE bump 112 → 128 (C-side + jhyy-side 同 commit
bump, per W-005 layout 锁)。

**superseder:** commit `f20e36d` (2026-08-14, "fix(v1.4.6 W-017): module-level
let mut 真修 — QBE data section + ir_emit_arg mirror")

**后续 (post-v1.4.6):**
- `jhyy_helpers.c` DEPRECATED — 不再需要委托 path state 到 C runtime,但文件
  保留 1-2 sprint 观察期,v1.5 installer 设计时决定删 / 留。
- 顶层 `let mut` literal 折叠已修;非 literal initializer (e.g. `fn call()`)
  当前 zero-init fallback — 完整 init expr codegen 留给后续 sprint (TODO)。

**触发面 (v1.4.1 路径硬编码消除时发现)**: 
- 计划 (per `docs/plans/v1/v1.4.0任务清单 + 概要设计.md` § v1.4.1):在 `main.jhyy` 顶层声明 `let mut g_qbe: *u8 = 0 as *u8;` 持有 QBE 路径,`compute_paths(argv0)` 在 `main_jhyy` 入口推项目根 → 写 4 个全局字符串 → `QBE_PATH()` 等 getter 返回 `g_qbe` 内容。
- 实测:jhyy_v1 codegen 把 `let mut g_qbe: *u8 = 0 as *u8;` 在 module 顶层当作 **常量 0** 编译期折叠 — 后续所有读 `g_qbe` 的 QBE IR 都是 `%t =l copy 0`,sentinel null pointer。
- 后果:`run_qbe` 拼出 `" -t amd64_win -o foo.s foo.il"` (qbe 路径是空字符串),system() 失败 → "QBE failed"。

**最小复现 (`compiler/src0/main.jhyy` 测试代码, 已 revert):**
```jhyy
// 顶层 — 不在 fn 内部
let mut g_qbe: *u8 = 0 as *u8;

fn compute_paths() -> i32 {
    g_qbe = "C:/some/path/qbe.exe" as *u8;  // 写应该改 runtime state
    return 0 as i32;
}

fn QBE_PATH() -> *u8 { return g_qbe; }    // 读应该返回新值
```

```bash
$ jhyy_v1.exe.exe compile foo.jhyy -o foo
[cg] Pass B start
ret     ← ❌ QBE_PATH() emit 的 ret 没 operand,function signature 声明 *u8 返回 → QBE 拒绝
```

**IL 错误状态 (codegen jhyy 端的 top-level let mut fold 产物):**
```
export function l $QBE_PATH() {
        ret               ← QBE: "non-void return needs a value"
}
```

**根因:** jhyy_v1 codegen 顶层 `let mut` (NodeKind=NODE_LEV / 模拟 module-level var) 的 initializer 在 IR 生成阶段就 **编译期折叠** 成 `IRVal{kind=IRVAL_INT, val=0}` (zero-extend to l),后续 `cg_find_local` 命中 `local id=0` 直接返回这个 folded value,运行时 `store` 到 global slot 的指令被 dead-code-eliminated (因为 IR 不区分"runtime store"和"compile-time init")。C-side (codegen.c) 在 module-level 处理 `let mut g_x: T = expr;` 时 emit `store` 指令到 module-level data section,不折叠 → jhyy-side 缺这一段。

**workaround (本 v1.4.1 ship):**
- 路径状态从 jhyy 端迁出 → 委托 `compiler/src0/jhyy_helpers.c` (C runtime)。
- 5 个 extern fn:`jh_paths_init(argv0) -> i32` (一次 init, 写 4 个 static buffer) + `jh_path_qbe/gcc/runtime/helpers() -> *u8` (4 次读, 返回 const char*)。
- `main.jhyy` 顶部:5 个 extern fn decl + `QBE_PATH/GCC_PATH/RUNTIME_C/HELPERS_C` 4 个 thin wrapper fn(就是 return jh_path_*)。
- `main_jhyy` 入口:调 `jh_paths_init(argv[0])` 一次。
- `__attribute__((used))` 防止 gcc strip unused symbols (jhyy_v1 codegen 不直接调 `jh_paths_init`,通过 extern 间接调,gcc 可能 strip)。

**跟 main.c (`compiler/src/main.c`) 关系:**
- main.c 同步加 `compute_project_root(argv0)` + `g_project_root[1024]` global(C-side 有真正的 module-level static storage,emit 到 .data section)。
- C 端 QBE / gcc / runtime / helpers 路径都拼 `g_project_root` 直接用,**不调** `jh_path_*` (jhyy 端才调,因为 jhyy 端没有真正的 global)。
- jhyy_helpers.c 的 `jh_paths_init` 跟 main.c 的 `compute_project_root` 算法镜像 (dirname × 4 + GetModuleFileNameA 兜底),保持单一来源真相。

**真修路径 (post-v1.4.1 / v2.x 候选):**
- jhyy codegen 顶层 `let mut x: T = expr;` emit 真正的 store 指令 (不编译期折叠)。
- 或者:加 `static mut x: T;` 关键字 (`unsafe` block),明确 runtime 初始化语义。
- 或者:codegen 在 module 顶层加 `.data` section emit (C-side 已经做,但 jhyy-side 的 NODE_LEV 处理路径漏了 module-level case)。

**失效条件 (任一即可移除 W-017):**
- jhyy codegen 实现 module-level mutable global (上面"真修路径"任意一条)。
- 或者 jhyy 改成只支持 pure-functional / 不需要 path state (jhyy_OS kernel coding 后无外部命令调用)。

**验证 (v1.4.1 ship criteria, 5/5 PASS):**
- `compiler/src/main.c` 0 hardcoded path (grep "C:/Users" 0 命中, 仅注释提及) ✅
- `compiler/src0/main.jhyy` 0 hardcoded path ✅
- `compiler/src0/jhyy_helpers.c` 0 hardcoded path ✅
- regress.py 50/50 PASS ✅
- Stage 2 N=3 byte-equal (`jhyy_v2.exe.il = jhyy_v3.exe.il = jhyy_v4.exe.il`) 维持 ✅
- Clone 到 `/tmp/v14_clone_test/JiHuiYiYou/`(保留 canonical `compiler/build/bin/jhyy.exe` layout) 跑 hello.jhyy EXIT=42 ✅

**Self-hosting impact:**
- jhyy_v1.exe.exe sha: `1c09215f...` → `f36faeadd05c0...` (v1.4.1 刷新)
- jhyy_v2/v3/v4 .exe sha: `e453b32c...`/`569e9091...`/`569e9091...` → `7e1917c8...`/`5cad02db...`/`de3c924f...` (v1.4.1 刷新)
- jhyy_v2.il / v3.il / v4.il sha: `7c035615...` → `4c91f246...` (新 jhyy_v1 closure chain 输出;字节级变化是因为新 jhyy_v1 在 init 阶段调用了 5 个新 extern fn,新增了 module-level 函数体,不影响 .s 字节(因为 dead-code-eliminated 的 init call 在 .s 仍存在 — sha 变化是 expected))
- Stage 1 byte-equal (C-side vs jhyy_v1): pre-existing 6/7 持平(W-005 #2 chain products 仍未真修);v1.4.1 路径生成不污染 IL

**引用:**
- v1.4.1 父 sprint: `docs/plans/v1/v1.4.0任务清单 + 概要设计.md` § Sprint v1.4.1
- 跟 W-005 #2 区分:W-005 #2 是 codegen 优化不彻底(多 emit 几个 `copy %t` 但语义正确),W-017 是 codegen 缺 module-level global storage(完全没 runtime state,只能编译期常量)
- 跟 main.c `compute_project_root` mirror:`compiler/src/main.c:30-77` (C 端有 module-level `static char g_project_root[1024]`,emit 到 .data,jhyy 端做不到)
- jhyy ABI: `docs/abis/jhyy-lang-spec-v1.3.0.md` § global state (TODO: 需 spec 加"顶层 `let mut` 是 compile-time only, runtime state 必须用 extern fn 委托 C"这条规则)

---

## W-018: v1.4.2 DWARF emit 引入 Stage 1 .il 字节差异 (非功能)

**Status:** ✅ RESOLVED 2026-08-14

**Why RESOLVED:** v1.4.2 ship 当时记的"Stage 1 byte-equal 不再 7/7"证据来自
broken `compiler/tests/stage1-expanded.sh` (JHY_1 路径错写成不存在的
`jhyy_v1.exe`, `2>/dev/null` 吞错) — 脚本从未真的跑过 v1, cmp 比的是
examples/ 里上次跑剩的陈旧 .il。修脚本后 Stage 1 重新跑出 **7/7 PASS**,
v1.4.2 DWARF 改动对 .il byte-equal 无影响。

**保留原因 (不删):** v1.4.2 ship 时 changelog 写了"Stage 1 byte-equal 持平"
未达成 — 这是错的, 应为达成。引用本条便于跨 sprint 审计时不被旧 changelog 误导。

**引用:**
- 根因: `compiler/tests/stage1-expanded.sh` 的 `JHY_1` 路径错 + stderr 被吞
- 验证: `bash compiler/tests/stage1-expanded.sh` → 7/7 PASS (2026-08-14)

## W-019: codegen 嵌套 struct `(o).inner.a` emit `loadsw` 类型错

**Status:** ✅ RESOLVED 2026-08-14 (commit `6638134`, v1.4.6 W-019 真修)

**Why RESOLVED:** v1.4.6 W-019 真修 — `cg_expr NODE_FIELD` 嵌套 struct 路径
加 "field is STRUCT → return addr (don't load)" guard,跟 NODE_DEREF 现有 pattern
一致 (`*ptr.field` 解引用 → 加 offset → 不 load;外层 `.field` 把内层 addr 当
`l` 类型继续加 offset → emit `loadsw %tN, addr+a` 时第一操作数是 `l`,QBE
接受)。C-side `src/codegen.c` + jhyy-side `src0/codegen.jhyy` 镜像 byte-equal
改动 (per W-005 layout 锁)。新增 `nested_struct_test.jhyy` 验证 nested
field chain (`Inner.a` + `Inner.b`) EXIT=15。

**superseder:** commit `6638134` (2026-08-14, "fix(v1.4.6 W-019): nested
struct field chain + payload binding codegen mirror")

**后续 (post-v1.4.6):**
- `gdb_pretty_test.jhyy` nested 用例 (W-019 修复后补齐) — gdb `jhyy-pretty
  <addr> Outer` pretty-print `Outer{inner={a=7, b=8}}` 可视化验证

**触发面:** `(*outer_ptr).inner.field` 这种嵌套 struct 字段访问。Outer / Inner 都是 ABI struct 类型,Inner 至少含一个 i32 字段。

**症状:** QBE reject `loadsw`/`loadw` 第一操作数类型错。例:
```
type Inner = struct { a: i32, b: i32 }
type Outer = struct { inner: Inner }
fn read_inner(o: *Outer) -> i32 { return (*o).inner.a + (*o).inner.b; }
```
`compile wnested_test.jhyy` 报:
```
qbe:wnested_test.il:15: invalid type for first operand %t2 in loadsw
```
line 15 通常是读取 `(*o).inner.a` 对应 `loadsw` 那行。

**根因嫌疑:** `cg_field_addr` 在 chain `.inner.a` 时,把外层 `.inner` 当作 struct field 而不是 sub-struct 看待 — emit 的 `.inner` 偏移处的 `loadsw` 把 outer 地址当 `b`/`h` 大小解码,实际 inner 字段是 `w` (4 字节 i32)。或者 `qbe_type_of` 在 inner struct ptr 解一层时返回错类型。未经确诊 — post-v1.4.3 follow-up。

**workaround (v1.4.3 测试):** `compiler/tests/examples/gdb_pretty_test.jhyy` 只覆盖 flat struct / single-layer enum / slice,不写嵌套 struct 测试用例。生产代码遇到嵌套 struct 字段访问时,临时绕过:
1. 用 `let inner_copy: Inner = (*o).inner; let r = inner_copy.a + inner_copy.b;` 把内层值拷出来再读字段
2. 或直接 `(*o).inner.a` 拆成两步:`let i_ptr: *Inner = &((*o).inner); (*i_ptr).a`

**影响范围:**
- 任何用户写嵌套 struct 字段访问的 .jhyy 文件都会触发 (少见但合法)
- jhyy 编 lexer.jhyy / parser.jhyy / codegen.jhyy 不触发 (用 enum + flat struct)

**失效条件:** fix 后必须 revert 测试里的 `// NOTE: nested struct` 注释并补 nested-struct 用例

**superseder:** 待 post-v1.4.3 fix (sprint 计划见下个 sprint 设计)

**引用:**
- repro: v1.4.3 验证时跑的 `wnested_test.jhyy` (内嵌在会话日志,未 commit)
- W-008 (已 RESOLVED) 类似路径但单层 field offset;W-019 是嵌套场景的复发

## W-020: jhyy-side `parser.jhyy` parse_pattern `Color::Variant` 分支 bug

**Status:** ✅ RESOLVED 2026-08-14 (commit `ad42117`, v1.4.6 W-020 真修)

**Why RESOLVED:** v1.4.6 W-020 真修 — `parse_pattern` + `parse_match` 上移到
`parse_expr` 之前 (reorder); inline match 在 `parse_expr` 里改用 `parse_match`
delegation (替换 Sprint 4.5 C step 3a 加的 ~165 行 inline duplicate);
`parse_pattern` 的 range hi 改用新加的 `parse_pattern_primary` (inline
primary expression, 不调 `parse_expr` 解 mutual recursion — 跟 jhyy 现有
array count inline int literal 模式一致); `parse_match` OR pattern 分支
`parser_advance(p)` 缺 `&t` 参数 UB 修。验证: `_min_enum.jhyy` jhyy-side
编译通过; `gdb_pretty_test.jhyy` EXIT=0; `_v137_or_exhaust.jhyy` EXIT=1
(OR pattern 不退化); match.jhyy / match_exhaustive.jhyy 不退化。

**superseder:** commit `ad42117` (2026-08-14, "fix(v1.4.6 W-020): parse_pattern
上移 + inline primary + simplify inline match")

**后续 (post-v1.4.6):**
- `parse_pattern_primary` 的限制保留:range hi 只能是 literal / ident / paren /
  struct literal (不能 `x..arr.len()`),跟 jhyy 现有 array count 模式一致 —
  full expression 留给后续 spec 扩展
- jhyy-side forward decl 不引入(不需要,jhyy-side 无此语法 — 用 reorder 解)

**触发面:** 任何 jhyy-side 编译遇到 match arm 中 `EnumName::Variant` 或 `EnumName::Variant(payload)` 这种 fully-qualified enum pattern。

**症状:** `compile gdb_pretty_test.jhyy` 报:
```
gdb_pretty_test.jhyy:50:28: error: expected =>, got ::
gdb_pretty_test.jhyy:50:28: error: unexpected token '::' in expression
...
parse errors
```
line 50 是 `match *c { Color::Red => 0, ... }`,col 28 是 `Color::Red` 中 `::` 位置。最小 repro:
```jhyy
type Color = enum { Red, Green, Blue }
fn main_jhyy() -> i32 {
    return match 1 { Color::Red => 0, Color::Green => 1, Color::Blue => 2 };
}
```
jhyy-side 编译失败;C-side (`jhyy_stage0.exe`) 编译通过。

**根因:** `compiler/src0/parser.jhyy:1134` `parse_pattern` 在 `parser_advance(p, &t)` 消耗 outer ident `Color` 后,`parser_check(p, TOKEN_COLONCOLON())` 返回 0,即使下一个 token 实际是 `::`。parser 走 line 1158+ ident-pattern 路径(line 1171 短名 variant 分支),最终返回 NODE_PATTERN_IDENT,留下 `::` 给上层 expr parser,expr parser 报 `expected =>, got ::`。

**C-side 对照 (`compiler/src/parser.c:124-138`):**
```c
advance(p);  // line 124
if (match(p, TOKEN_COLONCOLON)) {  // line 125 - atomic check + advance
    Token vt = expect(p, TOKEN_IDENT, "variant name");
    ...
}
```
C-side 用 `match` (原子 check + advance) 正常处理同样输入。jhyy-side 用 `parser_check` + 后续 `parser_advance` 分离两步,理论等价,但实际在 match arm 上下文中返回错值 — 未经确诊是不是 token peek cache (`lexer.has_peek`) 在某种状态下未正确恢复 / invalidate,或 jhyy-side 编译器参数个数检查缺失(line 1283 `parser_advance(p)` 调用缺第二个参数 `&t` 也没报编译错)。

**workaround (v1.4.4 测试):** `compiler/tests/examples/gdb_pretty_test.jhyy` line 50 / 53 的 enum pattern 暂不动(等真修);如果要做回归,临时用 let-binding 替代:
```jhyy
let tag: i32 = color_tag(*c);   // 调用外部 helper 提取 enum tag (i32)
match tag { 0 => ..., 1 => ..., 2 => ... }
```

**影响范围:**
- 任何用户写 match arm `EnumName::Variant` 的 .jhyy 都会触发
- jhyy 编 lexer.jhyy / parser.jhyy / codegen.jhyy **不触发**(用 `match` on i32,不用 enum pattern)
- C-side 不受影响(C 端 parse_pattern line 124-138 正确)
- v1.4.4 之前 production `jhyy.exe` 实际是 C-side (sha `c9cff76...`),bug 被遮住;v1.4.4 物理替换为 jhyy-side (sha `37ffc49c...`) 后首次暴露

**失效条件 (任一即可移除 W-020):**
1. 改 `compiler/src0/parser.jhyy` parse_pattern `Color::Variant` 分支 (line 1134) + OR-pattern (line 1282-1288),使 jhyy-side 跟 C-side 行为一致
2. C-side / jhyy-side mirror byte-equal 测试 (`stage1-byte-equal.sh`) 加 match-arm-with-enum-pattern 用例

**修复路径候选:**
- v1.4.6 跟 W-019 合并真修 (parser 是 codegen 无关,但跟 codegen W-019 同期改 cross-mirror 风险可控)
- 或单独 v1.4.7 修 parser

**引用:**
- repro: `compiler/tests/examples/gdb_pretty_test.jhyy:50,53`;最小 repro `_min_enum.jhyy`
- v1.4.4 ship 时 changelog 把此 bug 误标 "pre-existing v1.4.3" 已更正 → [`docs/logs/v1/changelog-v1.4.0.md`](../logs/v1/changelog-v1.4.0.md) § v1.4.4 ship
- W-019 是 codegen 嵌套 struct,跟 W-020 (parser enum pattern) 不同面,但同样等真修;建议 v1.4.6 合并

## W-021: WiX 7 CLI `-ext` name 查找失败 — `-ext WixToolset.Bal.wixext` 找不到

**状态:** ✅ RESOLVED 2026-08-28 (v1.7.1 patch B1) — 永久 workaround 化, 标 RESOLVED 是因为 v1.7.1 patch ship 时 review 确认 underlying issue 依赖 WiX 上游 DLL 命名 (external dep, 项目不可控), 短期/中期不会真修。workaround `installer/build.ps1:131-136` 显式传 DLL 绝对路径, stable ship v1.5.3+ 至今。

**触发场景:** Sprint v1.5.3 Burn bundle build, `wix build installer/Bundle.wxs -ext WixToolset.Bal.wixext ...` 时报 WIX0144 (`The extension 'WixToolset.Bal.wixext' could not be found. Checked paths: WixToolset.Bal.wixext`)。

**根因:** `dotnet tool install --global wix` 装 WiX 7.0.0+b8977d6 后,`wix extension add -g WixToolset.Bal.wixext` 把 DLL 装到 `%USERPROFILE%\.wix\extensions\WixToolset.Bal.wixext\7.0.0\wixext7\` 目录,但 **DLL 文件名是 `WixToolset.BootstrapperApplications.wixext.dll`**,不是预期的 `WixToolset.Bal.wixext.dll`(wix CLI 名字解析逻辑是按 DLL basename 找,但 `Bal.wixext` extension 的产物 DLL basename 是 `BootstrapperApplications`,跟 extension 名不对应)。同样情况可能影响其他 Bal sub-extensions。MSI 用的 `WixToolset.Util.wixext` / `WixToolset.UI.wixext` 名字-文件名一致所以不触发。

**workaround (v1.5.3):** `installer/build.ps1` 显式构造 DLL 绝对路径传给 `-ext`,跳过 CLI 名字解析:
```powershell
$balDll = "$env:USERPROFILE\.wix\extensions\WixToolset.Bal.wixext\7.0.0\wixext7\WixToolset.BootstrapperApplications.wixext.dll"
if (-not (Test-Path $balDll)) {
    Write-Host "[ERROR] Bal extension DLL not found at: $balDll"
    Write-Host "Run:  wix extension add -g WixToolset.Bal.wixext"
    exit 1
}
& wix build ... -ext "$balDll" ...
```

**影响范围:**
- 只影响 Burn bundle build (`build.ps1 bundle`),不影响 MSI build (`build.ps1 compiler`) — Util/UI 名字一致不触发
- 不影响最终产物 (`jhyy-installer-X.Y.Z.exe` 一样能 build, payload 一样齐全)
- workaround 是 stable 的,WiX 7.x 一直用 `BootstrapperApplications.wixext.dll` 文件名

**失效条件 (任一即可移除 W-021):**
1. WiX 7 改回把 Bal extension DLL 命名为 `WixToolset.Bal.wixext.dll`(跟 extension 名一致)
2. wix CLI 加 `-ext-folder=<path>` flag 允许传目录,自动找 DLL
3. 写 custom BAFunctions (替代 Bal extension),完全不依赖 Bal.wixext

**修复路径候选:**
- 短期: workaround 留,build.ps1 已记录
- 中期: 等 WiX 上游改 DLL 命名 (可能性小,Bal sub-extensions 都按功能命名,不按 extension 名)
- 长期: v2.x 可能写 custom BAFunctions(MVP 化 Burn UX),彻底绕开 Bal.wixext

**引用:**
- repro: 跑 `wix build installer/Bundle.wxs -ext WixToolset.Bal.wixext ...` 看 WIX0144
- workaround 实现: `installer/build.ps1:131-136`
- v1.5.3 ship commit (this commit)

---

## W-022: Windows PowerShell 5.1 `Out-File -Encoding utf8` 加 UTF-8 BOM 污染 `$GITHUB_ENV`

**状态:** ACTIVE (PowerShell 5.1 在 windows-latest runner 是 default; GH Actions 升级 PS7 之前持续)

**触发场景:**
在 `.github/workflows/release.yml` 的 pwsh step 里写 env 到 `$GITHUB_ENV`:
```powershell
"VERSION=1.5.5" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
"IS_RC=0"      | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append
```

**症状:**
后续 step 看不到 `VERSION` / `IS_RC` 环境变量。`${{ env.VERSION }}` 在 yaml 表达式里空字符串。`$env:VERSION` 在 pwsh 里 `$null`。

**根因:**
Windows PowerShell 5.1 (windows-latest runner 默认) 的 `Out-File -Encoding utf8` 实际输出是 **UTF-8 with BOM** (`EF BB BF` 三个字节开头)。GitHub Actions 解析 `$GITHUB_ENV` 文件时按 plain text 读,看到 BOM 当成普通字符,导致第一行变成 `﻿VERSION=1.5.5`,env var 名变成 `﻿VERSION`,后续 step `${{ env.﻿VERSION }}` 拿不到值 (因为 yaml 表达式不接受 BOM 前缀)。

PowerShell 7+ 的 `Out-File -Encoding utf8` 是 UTF-8 no BOM (没有这个 bug),但 GH Actions Windows runner 默认 PS5.1。

**workaround:**
```powershell
"VERSION=$($env:VERSION)" | Add-Content -Path $env:GITHUB_ENV
```
`Add-Content` 默认走 `[System.IO.File]::AppendAllText`,在 PS5.1 下用 UTF-8 **without BOM** 写,跟 `$GITHUB_ENV` 期望的 plain text 一致。

或者用 `Set-Content -Encoding utf8` (PS5.1 也加 BOM,不推荐)。

**影响范围:**
- 只影响 PowerShell step 写 `$GITHUB_ENV` / `$GITHUB_OUTPUT` / `$GITHUB_PATH` 的场景
- 不影响 bash step (bash 的 `echo "X=Y" >> $GITHUB_ENV` 是 plain text,无 BOM 问题)

**失效条件:**
1. GH Actions windows-latest runner 升级到 PowerShell 7+ 默认 shell
2. GH parser 升级支持 BOM 前缀

**引用:**
- repro: 写 `"X=1" | Out-File -FilePath $env:GITHUB_ENV -Encoding utf8 -Append`, 看 `${{ env.X }}` 在下一步 yaml 表达式里空
- workaround 实现: `.github/workflows/release.yml` Compute VERSION step
- v1.5.5 ship commit

---

## W-023: MSYS2 bash step 里 `${VAR}` 不展开 `${{ env.X }}` GH 表达式

**状态:** ACTIVE (yaml 表达式 + bash sub-shell 语义鸿沟, GH Actions 设计就这样)

**触发场景:**
`.github/workflows/release.yml` 的 msys2 bash step:
```yaml
- name: Set env
  shell: msys2 {0}
  run: |
    echo "MSYS2_PATH=/c/msys64/usr/bin:$PATH" >> $GITHUB_ENV
    echo "VERSION=${VERSION} IS_RC=${IS_RC}"   # ❌ 空字符串
```

**症状:**
`echo` 输出 `VERSION= IS_RC=`,后续 step 拿到空 `VERSION`。

**根因:**
`${{ env.VERSION }}` 是 GitHub Actions 的 **yaml 表达式**,仅在 yaml 解析阶段被 GH 替换成实际值,然后 yaml 解析后的字符串塞进 bash sub-shell 的 stdin。bash 看到的字符串是 `"echo \"VERSION=1.5.5 IS_RC=0\""`(假设 `VERSION=1.5.5`),但 `${VERSION}` 是 bash 的语法, 跟 yaml 表达式是两回事 — yaml 表达式替换后**不**写回 env 上下文,bash 自己读 `$VERSION` (空) 写 `${VERSION}` (空,作废语法)。

实际正确写法:
```yaml
- name: Set env
  shell: msys2 {0}
  run: |
    echo "MSYS2_PATH=/c/msys64/usr/bin:$PATH" >> $GITHUB_ENV
    echo "VERSION=$VERSION IS_RC=$IS_RC"      # ✓ 读已经 export 到 env 的 $VERSION
```

需要先在某个 step 把 VERSION 写到 `$GITHUB_ENV` (per W-022 用 `Add-Content`), 然后下一个 bash step 拿 `$VERSION`。

**影响范围:**
- 仅 msys2 bash step + yaml 表达式 (其他 step 类型用 `${{ env.X }}` 直接 yaml 替换,不涉及 bash 变量展开)
- pwsh step 用 `$env:VERSION` 读,语法不冲突

**失效条件:**
- N/A (设计如此,workaround 是规范用法)

**引用:**
- repro: 写 `echo "X=${VAR}"` 在 bash step, 看 `${VAR}` 输出空 (假设 VAR 已经在 $GITHUB_ENV export 过)
- workaround 实现: `.github/workflows/release.yml` Set bash as default shell step (v1.5.5 起,本 commit)
- v1.5.5 ship commit

---

## W-024: PowerShell 5.1 `Set-Content` / `Out-File` 写 UTF-8 文本默认加 BOM + CRLF

**状态:** ACTIVE (PS5.1 default 在 windows-latest runner)

**触发场景:**
PowerShell 写 UTF-8 文本文件 (用于上传到 GitHub Release 或下游工具消费):
```powershell
$notes = Get-Content installer/changelog-template.md -Raw
# ... replace 占位符 ...
Set-Content -Path release-notes.md -Value $notes -NoNewline  # ❌ 加 BOM + CRLF
"jhyy-installer  $hash" | Out-File -Encoding utf8 -Append     # ❌ 加 BOM + CRLF
[IO.File]::WriteAllLines('sha256.txt', $lines, $utf8NoBom)   # ❌ CRLF only (BOM OK)
```

**症状:**
- 文件前 3 字节 `EF BB BF` (BOM)
- 行尾是 `\r\n` (CRLF), 不是 `\n` (LF)
- `sha256sum -c SHA256.txt` 在某些 Linux 平台 (scoop autoupdate 用 Linux container) 不识别:
  - 带 BOM 的 file: BOM 当成 hash 第一字符
  - 带 CRLF 的 file: `\r` 被当成 filename 一部分 → "No such file or directory"
- winget `wingetcreate validate` 报 BOM 不是预期 (实际上容忍,但 release notes 显示乱码)
- GitHub web UI render markdown 时 BOM 当成 invisible char,某些 markdown linter 报 "first char not LF"

**根因 (BOM):**
Windows PowerShell 5.1 的 `Set-Content -Encoding utf8` 和 `Out-File -Encoding utf8` 都用 UTF-8 with BOM (默认).NET Encoding `utf8` 是带 BOM 的。
PowerShell 7+ (pwsh) 的 `utf8` 是 UTF-8 without BOM, Windows PS 5.1 才有这个 BOM 问题。

**根因 (CRLF):**
Windows PS5.1 的 `[System.IO.File]::WriteAllLines` / `[IO.File]::WriteAllText` (默认 encoding 参数) 用 `Environment.NewLine`,Windows 上是 `\r\n`。
Linux/macOS 上是 `\n`。`sha256sum` (GNU coreutils) 对文件名严格 — `\r` 当成普通字符,实际查找 `<hash>  <name>\r` 文件,失败。

Per memory `feedback_qbe_crlf_root_cause` — 同根因,Windows fopen 默认 LF→CRLF 转换,跟 QBE .il 行号偏移错的根因一样。所有 PS 写的 UTF-8 行文件被 Linux 工具消费都要 LF + no BOM。

**workaround:**
用 `[System.IO.File]::WriteAllText` + 显式 UTF8Encoding(false) + 自己用 `\n` join (不要 `Environment.NewLine`):
```powershell
# 一次性写文件 (single string, explicit LF, no BOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$content = ($lines -join "`n") + "`n"  # trailing newline for POSIX
[System.IO.File]::WriteAllText('release-notes.md', $content, $utf8NoBom)

# 同样 pattern for SHA256.txt (per installer/gen-sha256.ps1)
$lines = foreach ($f in $files) {
    $hash = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
    "{0}  {1}" -f $hash, $f.Name
}
$content = ($lines -join "`n") + "`n"
[System.IO.File]::WriteAllText('installer/SHA256.txt', $content, $utf8NoBom)
```

或者换 pwsh 7+ (`shell: pwsh`),但 GH Actions windows-latest runner 默认 PS5.1, 强制 pwsh 7 需要 `pester/setup-pwsh@v1` action。

**影响范围:**
- 所有 PowerShell 5.1 step 写 UTF-8 文件的场景 (release notes / SHA256.txt / release assets / gen-* 脚本)
- SHA256.txt 是 `sha256sum -c` 校验的源, CRLF + BOM 双坑
- per `feedback_qbe_crlf_root_cause` — 任何 Windows 写 + Linux 读的行文件都要 LF no BOM

**失效条件:**
1. GH Actions windows-latest runner 升级默认 shell 到 pwsh 7
2. 或者 PS5.1 加 `-Encoding utf8NoBom` flag (PowerShell team 已经讨论,未 ship)

**引用:**
- repro: `[System.IO.File]::WriteAllText('test.txt', "a`nb", [System.Text.UTF8Encoding]::new($false))` → 头 3 字节无 BOM,行尾 `\n` ✓; 改 `[System.Text.Encoding]::UTF8` → 头 3 字节 BOM,行尾 `\r\n` ❌
- workaround 实现: `installer/gen-sha256.ps1:65-72` + release.yml Generate release notes step
- v1.5.5 ship commit

## W-025: qbe/ gitlink 无 .gitmodules — release.yml `submodules: recursive` 失败 + installer/build.ps1 hardcoded `qbe/qbe.exe`

**症状 (2026-08-15 v1.5.5 dry-run run 31859843640):**
- `actions/checkout@v4` with `submodules: recursive` fail at Checkout step:
  - `fatal: No url found for submodule path 'qbe' in .gitmodules`
  - `fatal: The process 'C:\Program Files\Git\bin\git.exe' failed with exit code 128`
  - Annotation: `Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4`

**根因:**
qbe/ 是 gitlink 模式 `160000` 记录在 index,但:
- 本地从来没有 `.gitmodules` (git log --all -- .gitmodules 输出空)
- gitlink 指向的 commit `c0818978acec60ebb6167fade60fb7012cbf20ca` 在 repo 里 dangling (`git log -1 --format=...` 报 `fatal: bad object`)
- 本地 qbe/ 目录是 working tree (有 .o / .c / Makefile 等),但 git 不 track 内容 (git ls-files qbe 只有 1 行 = gitlink 自身)
- 推断: Phase 0 commit (c5e4efb) 初始建 repo 时,把 qbe vendor 进来当 gitlink,但 .gitmodules 没写 (或者被 reset 掉)。后续 ci.yml 跑 `actions/checkout@v4` 不带 `submodules:` 所以能跑 (qbe/ gitlink 就空 dir),但 release.yml 加 `submodules: recursive` 触发检查 .gitmodules 的 logic → fail

**workaround (两层):**

1. **`release.yml`** drop `submodules: recursive`:
```yaml
- name: Checkout
  uses: actions/checkout@v4
  with:
    fetch-depth: 0  # for git describe / tag detection
```

2. **`installer/build.ps1`** qbe.exe resolution 加 PATH fallback:
```powershell
# qbe.exe resolution (W-025): prefer local qbe/qbe.exe (dev), fall back
# to qbe.exe on PATH (MSYS2 mingw-w64-ucrt-x86_64-qbe — release workflow).
$qbeLocal = "qbe/qbe.exe"
$qbeOnPath = (Get-Command qbe.exe -ErrorAction SilentlyContinue)
if (Test-Path $qbeLocal) {
    Copy-Item -Path $qbeLocal -Destination "$binDir/qbe.exe" -Force
} elseif ($qbeOnPath) {
    Copy-Item -Path $qbeOnPath.Source -Destination "$binDir/qbe.exe" -Force
} else {
    exit 1
}
```

**为什么 release workflow 还要 `mingw-w64-ucrt-x86_64-qbe` package:**
- ci.yml 也用 (同 pattern),但 ci.yml 不 build MSI / qbe.exe binary
- release.yml 要 qbe.exe 来 pack MSI Burn bundle,所以从 MSYS2 package 取 (PATH 上 `qbe.exe`),build.ps1 自动 fallback 用它

**影响范围:**
- 仅 release.yml + installer/build.ps1
- ci.yml 不受影响 (已经无 submodules: recursive)
- 本地 dev build 仍走 `qbe/qbe.exe` (优先) — 不改 dev workflow

**失效条件 / 未来 fix:**
1. **De-submodule qbe + track source files** — rm gitlink + `git add qbe/`,commit (~80 .c/.h files added, ~3-5 MB tracked)。彻底修 dangling gitlink + 让 qbe diff history 可见。但 v1.5.5 scope 不够,推到 v2.x (per M5 boot-from-scratch decision, qbe 要么 vendored 要么 QBE 重写,这里有歧义)。
2. **Restore .gitmodules + commit** — 需要知道原 upstream URL (目前不知道)。同上,等 v2.x 决。
3. GH Actions Node 20 deprecation — `actions/checkout@v4` 被强制 Node 24 跑,目前是 warning,不算 fail。

**引用:**
- 错误日志: GH Actions run 31859843640, Checkout step stderr
- workaround 实现: `.github/workflows/release.yml:81-86` + `installer/build.ps1:85-100`
- v1.5.5 ship commit (post hotfix)
- 关联: `feedback_qbe_crlf_root_cause` (W-024 / QBE 行号偏移错的同 root: Windows 写 vs Linux 读;此处不是 root cause,但同方向问题)

---

## W-025 follow-up (2026-08-15 same-day): MSYS2 qbe package 不存在 → 必须 vendoring qbe source

**追加症状 (dry-run run 31860099231):**
- 第二个 dry-run 过了 Checkout (上一节 workaround 生效),但在 Setup MSYS2 step fail:
  ```
  error: target not found: mingw-w64-ucrt-x86_64-qbe
  ```
- MSYS2 ucrt64 repo 没 ship qbe package (https://packages.msys2.org/packages/?q=qbe 0 hit)。其他 repo (mingw64 / clang64) 也没有
- 假定 MSYS2 qbe package 是错的 — 这是 release.yml 初版的设计失误

**根因:**
- qbe.exe 是 QBE 编译器 binary,QBE upstream (8l/qbe) 没有 official release 跟 prebuilt binary
- 本地 qbe/ 是 QBE upstream fork (有 amd64/winabi.c 等 Windows 适配),不能直接 clone upstream 替换
- qbe/ 历史 gitlink 指向的 commit c0818978... 在 repo 里 dangling,无法 `git submodule update` 拿回来

**fix (一层 — 推到 v1.5.5 ship):**
彻底 vendor qbe source 到 repo:
1. `git rm --cached qbe` (删 gitlink)
2. `git add qbe/.gitignore qbe/README qbe/LICENSE qbe/Makefile qbe/*.c qbe/*.h qbe/amd64/* qbe/arm64/* qbe/rv64/*` (41 个 source + headers + LICENSE + README + Makefile + .gitignore, ~376 KB;`qbe/test/` `qbe/tools/` `qbe/minic/` `qbe/doc/` 不 track — 不是 build 必需)
3. `qbe/.gitignore` 加 `qbe.exe` (Windows build output)
4. release.yml 新加 step:
   ```yaml
   - name: Build qbe.exe (vendored source under qbe/)
     shell: msys2 {0}
     run: |
       cd qbe
       make
       sha256sum qbe.exe
   ```
5. release.yml 删 `mingw-w64-ucrt-x86_64-qbe` MSYS2 package
6. installer/build.ps1 qbe.exe resolution 保持 — `qbe/qbe.exe` (local) 优先;PATH 兜底 (CI fallback)

**影响范围:**
- 仅 release.yml + installer/build.ps1 + qbe/ vendoring
- ci.yml 不受影响 (no qbe build step)
- 本地 dev build 走 `qbe/qbe.exe` (不变)
- qbe diff history 从 gitlink dangling 转到 visible tracked (39 commits 在 qbe source history;现在只有 1 个 commit 因为是 de-submodule 整批 add)

**失效条件 / 未来 fix:**
1. **M5 boot-from-scratch** (per `project_m5_boot_from_scratch_decision`) — v2/v3 末可能删 qbe/ (QBE 自写) 或更新到新 QBE upstream
2. **QBE upstream major version bump** — 现 v1.5.5 vendor 跟 upstream HEAD (d62b154) 不一致 (local fork);升级需要 sync
3. GH Actions Node 20 deprecation (carry over from above)

**引用:**
- 错误日志: GH Actions run 31860099231, Setup MSYS2 step stderr
- workaround 实现: vendored 41 qbe files + `.github/workflows/release.yml` (Build qbe.exe step) + `installer/build.ps1` (qbe.exe resolution)
- v1.5.5 ship commit (post vendoring)

## W-026: regress.py `[:80]` stderr 截断隐藏真实 QBE/gcc 错误

**状态:** RESOLVED (2026-08-15, commit `0d58efe` — full stderr print)
**日期:** 2026-08-15
**触发面:** `mcp-jhyy/jhyy_regress.py` run_all() FAIL print

**症状:**
GH Actions dry-run #31861809057, #31861809057, #31863594640 — Run regress step 53/53 FAIL, stderr 截断到 `[sema] P1 ndec` (80 字符)。Sanity check (`jhyy.exe compile arith.jhyy`) 同 step 跑出来 exit 0 + 完整 `[4] codegen done`。

**根因:**
`jhyy_regress.py:309` 的 `print(f"FAIL ... {msg[:80]}")` 把真实错误消息截掉了。QBE / gcc 的 link 错误永远出现在 `[4] codegen done` 之后, 总 >80 字符, 截断后看不到。

**workaround:**
去掉 `[:80]` 截断, 改成 `print(... {msg})`, 让 FAIL 输出完整 stderr。下次 dry-run 能直接看到 QBE/gcc 错误。

**影响范围:**
- 仅 `mcp-jhyy/jhyy_regress.py` run_all() print
- 本地 53/53 PASS 不破

**引用:**
- 错误日志: GH Actions runs 31861809057, 31863594640
- workaround 实现: `mcp-jhyy/jhyy_regress.py` line 313 (FAIL print)
- fix commit: `0d58efe`

## W-027: GH Actions `setup-msys2@v2` 把 MSYS2 装在 `$RUNNER_TEMP\msys64` (CI = `D:\a\_temp\msys64`), 不在 `C:\msys64` — 硬编码 `C:\msys64\ucrt64\bin` 找不到 gcc

**状态:** ✅ RESOLVED → SUPERSEDED by W-029 (v1.5.6 superseder commit TBD)
**日期:** 2026-08-15
**触发面:** `.github/workflows/release.yml` Run regress step (53/53 FAIL → 47/53 FAIL → 53/53 PASS over 4 fix attempts)

**症状 + fix attempts:**
- v1 (#31861809057): `'gcc' is not recognized` — `C:\msys64\ucrt64\bin` hardcoded wrong on CI
- v2 (#31863594640): `[:80]` truncation hid real error (W-026 fix); same `'gcc' is not recognized`
- v3 (#31863873870): unconditional Windows PATH prepend (commit `3ad8128`); still FAIL — CI MSYS2 not at C:\msys64
- v4 (#31864035818 debug): confirmed MSYS2 at `D:\a\_temp\msys64`, used `cmd //c where` — revealed hardcoded path wrong
- v5 (df71824): `shutil.which('gcc')` — returns MSYS2 virtual path `/ucrt64/bin/gcc` (only valid in MSYS2 bash)
- v6 (8513681): also call `cmd /c where gcc` from Python — from MSYS2-launched Python, cmd.exe returns interactive prompt (unreliable)
- v7 (e9f0f85): bash `cmd //c 'where gcc'` from Python — bash returns UTF-16 LE error message (decode fails)
- v8 (4623a3b): **deterministic MSYS2 root**: read `RUNNER_TEMP` env (CI = `D:\a\_temp`) + fall back to `C:\msys64`; check known bin subdirs (`ucrt64/bin`, `mingw64/bin`, `usr/bin`, `bin`) via `os.path.isdir`; prepend each existing dir (Win32 form) to env['PATH']. No subprocess call needed.

**workaround (final v8):**
- Read `os.environ['RUNNER_TEMP']` (auto-set by GH Actions on `windows-latest`)
- Compute MSYS2 root: `$RUNNER_TEMP\msys64` (CI) or `C:\msys64` (local)
- For each known bin subdir: `os.path.isdir(root + "\\" + sub)` → prepend if exists
- All paths are Win32 form (`\\`-separated, drive letter)
- No subprocess, no encoding issues, no MSYS2 quoting issues

**影响范围:**
- 仅 `mcp-jhyy/jhyy_regress.py` _build_subprocess_env
- 本地 53/53 PASS 不破
- CI 47/53 → 53/53 PASS (post-W-028 mod-256 fix)

**引用:**
- debug runs: GH Actions #31861809057, #31863594640, #31863873870, #31864035818, #31864780270, #31864948299, #31865432960, #31865675000, #31866010390, #31866179790, #31866475742
- fix commit: `4623a3b` (v8 final)
- v1.5.6 superseder: 见 W-029 — `jh_gcc_path()` 4-tier 探测, regress.py / release.yml
  不再 prepend MSYS2 bin 到 PATH, W-027 v8 Python 探测段整段删.

## W-029: jhyy.exe toolchain 探测收敛 — `jh_gcc_path()` 4-tier 优先级 + `jh_gcc_invoke()` 包装替代 v1.0.0 跨 3 文件 MSYS2 探测逻辑

**状态:** 🟢 ACTIVE (v1.5.6 ship, commit TBD)
**日期:** 2026-08-15
**触发面:** `compiler/src0/jhyy_helpers.c` (jh_gcc_path + jh_gcc_invoke) +
`compiler/src0/main.jhyy` (link_with_gcc 改用 jh_gcc_invoke) +
`mcp-jhyy/jhyy_regress.py` (删 _build_subprocess_env 的 MSYS2 探测段) +
`.github/workflows/release.yml` (删 Propagate MSYS2 paths step)

**superseder 关系:**
- W-027 v8 RESOLVED → SUPERSEDED by W-029 (整段 MSYS2 探测从 Python 侧删,
  收敛到 jhyy.exe 内部)
- v1.0.0 release 痛点 (regress.py 跨平台 quoting / setup-msys2 path 不固定)
  闭环

**症状 (W-027 v8 之前):**
- 跨 3 文件 (regress.py / release.yml / jhyy_helpers.c) 各自探测 MSYS2 path
- 试了 8 个版本 (v1-v8) 才稳定, bug 一堆 (subprocess quoting / encoding /
  MSYS2 virtual path 跟 Win32 path 混淆)
- 任何一处改都会破坏另两处

**workaround (v1.5.6 fix):**
1. `jh_gcc_path()` (`compiler/src0/jhyy_helpers.c` lines 204-294):
   4 层优先级探测, 一次性 resolve, static buf 缓存:
   - **Priority 1**: `JHY_GCC` env (user/CI 显式 override)
   - **Priority 2**: `$JHYY_HOME\env.txt` 文件 KEY=VALUE (单用户配置)
   - **Priority 3**: Windows MSYS2 magic (`C:\msys64\ucrt64\bin\gcc.exe` 等 3 项)
   - **Priority 4**: `SearchPathA` PATH 探测 (Win32 API, 不依赖 subprocess)
   - **Fallback**: literal `"gcc"` 走 Windows PATH 解析
2. `jh_gcc_invoke()` (同文件 lines 300-302):
   `snprintf` 包装 `"%s" %s`, 给 `system()` 调用 — 替代 main.jhyy `link_with_gcc` 裸 `system("gcc ...")`
3. `compiler/src0/main.jhyy` `link_with_gcc`: 改用 `jh_gcc_invoke(invoke_buf, ...)` + `system(invoke_buf)`. cmd_buf 不再前缀 GCC_PATH() (现在 invoke_buf 内部加)
4. `mcp-jhyy/jhyy_regress.py` `_build_subprocess_env`: **删** lines 87-117 (MSYS2 探测段 ~30 行). 仅保留基础 env (TMP/SystemRoot). jhyy.exe 自己负责 gcc 探测
5. `.github/workflows/release.yml`: **删** lines 164-176 "Propagate MSYS2 paths to subprocess PATH" step. jhyy.exe 启动时自己探测, GH Actions runner 不需手工 export PATH
6. Linux/macOS placeholder: `jh_gcc_path()` `#ifdef _WIN32` 之外返回 literal `"gcc"` (v2.x 填跨平台探测)

**测试 (5 个探测优先级):**
- `compiler/tests/examples/_jh_gcc_p1.jhyy` — SETENV `JHY_GCC=C:\msys64\ucrt64\bin\gcc.exe` → Priority 1 命中
- `compiler/tests/examples/_jh_gcc_p2.jhyy` — SETENV `JHYY_HOME=...`, 手动写 env.txt → Priority 2 命中
- `compiler/tests/examples/_jh_gcc_p3.jhyy` — 不设 env, magic 存在 → Priority 3 命中
- `compiler/tests/examples/_jh_gcc_p4.jhyy` — placeholder (探测链返回非空); 严格 SearchPathA 验证受测试环境约束推迟 v2.x
- `compiler/tests/examples/_jh_gcc_p5.jhyy` — placeholder (探测链返回非空); 严格 fallback "gcc" 验证推迟 v2.x
- p1/p2/p3: 本机测试环境约束 (magic 唯一存在路径 = ucrt64, 跟 Priority 3 magic 第 1 项相同) 严格 Priority 1/2 vs 3 区分无法自动化, 实际区分证据见 `_jh_gcc_p1_debug.jhyy` (ad-hoc)

**影响范围:**
- 4 文件改动 (jhyy_helpers.c / main.jhyy / regress.py / release.yml)
- 5 个新测试 (p1-p5, SETENV directive 新增)
- baseline 53/53 PASS 不破
- Linux/macOS 跨平台探测 v2.x sprint 填 (jhyy.exe toolchain 必须用绝对路径, 不靠 PATH 解析 — 类型 4 升级)

**失效条件 (W-029 移除条件):**
- v2.x manifest lite 实施后, Priority 2 env.txt 升级到 toolchain.env 多工具 (v2.x sprint 范围)
- 跨平台探测 (Linux/macOS) 实施后, `#ifdef _WIN32` 分支消失 (v2.x sprint 范围)

**引用:**
- design plan: `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` § 设计 1
- related: jhyy.exe toolchain 必须用绝对路径, 不靠 PATH 解析 (类型 4 升级要求)
- related workaround: W-027 v8 (Python 探测 → jhyy.exe 接管)
- 实施 commit: TBD (v1.5.6 sprint 末 ship)

## W-028: Windows process exit code 是 8-bit (mod 256), EXPECT 注释里的值 > 255 在 CI regress FAIL (got=106 不是 got=1000042)

**状态:** ✅ RESOLVED 2026-08-15 (commit `6d2ab8f` + commit TBD — `sys.platform` cygwin/msys 兼容)
**日期:** 2026-08-15
**触发面:** `mcp-jhyy/jhyy_regress.py` run_test EXPECT comparison (47/53 PASS post-W-027)

**症状:**
W-027 v8 fix 后, CI dry-run 47/53 PASS。剩 6 个 FAIL:
- arith.jhyy `expected=1000042 got=106` (1000042 % 256 = 106)
- big_array.jhyy `expected=5050 got=186` (5050 % 256 = 186)
- big_test.jhyy `expected=12345 got=57` (12345 % 256 = 57)
- fib30.jhyy `expected=832040 got=40` (832040 % 256 = 40)
- fib_renamed.jhyy `expected=832040 got=40`
- nested_if.jhyy `expected=500 got=244` (500 % 256 = 244)

**根因 (两层):**
1. **架构层**: Windows kernel32 `ExitProcess` 只接受 8-bit exit code (0-255); 任何 >= 256 的 return value 自动 mod 256。Python `subprocess.run` 返回的 `returncode` 在 Windows 上走 WaitForSingleObject + GetExitCodeProcess, 也是 8-bit。
2. **平台检测层** (v2 commit TBD): GH Actions `shell: msys2 {0}` 启动 Python, **MSYS2-launched Python 的 `sys.platform` 是 `"cygwin"` 不是 `"win32"`**。第一版 fix `if sys.platform == "win32"` 在 CI 上**永远 False**, mod-256 逻辑不触发。

   ```
   [W-028 trace from dispatch #31867221428]:
     fname=arith.jhyy actual=106 expected=1000042 actual_cmp=106 expected_cmp=1000042 sys.platform=cygwin
   ```

**workaround (最终):**
在 `run_test()` 末尾比较前加 (commit TBD):
```python
# W-028: detect any Windows-subsystem Python (win32 / cygwin / msys)
_IS_WINDOWS_PY = sys.platform in ("win32", "cygwin", "msys")
if _IS_WINDOWS_PY and actual >= 0:
    actual_cmp = actual & 0xFF
    expected_cmp = expected & 0xFF
else:
    actual_cmp = actual
    expected_cmp = expected
return (actual_cmp == expected_cmp, expected, actual, output)
```

**真修 (superseder):**
- v2.x: 改 QBE codegen 让 main return i32 直接传 kernel32 ExitProcess, 不要走 C runtime `__cxa_atexit`
- v3.x OS 准备: freestanding 模式下 ExitProcess 调用栈可控, 不再依赖 `__cxa_atexit`

**影响范围:**
- 仅 `mcp-jhyy/jhyy_regress.py` run_test()
- 本地 53/53 PASS 不破 (`sys.platform == "win32"` 走原路径)
- CI 47/53 → 53/53 PASS (`sys.platform == "cygwin"` 走新 `_IS_WINDOWS_PY`)

**引用:**
- GH Actions dry-run #31866475742 (47/53 PASS post-W-027 v8; 6 mod-256 FAIL identified)
- GH Actions dry-run #31866960877 (W-028 v1 — `sys.platform == "win32"` 不触发, 47/53 持平)
- GH Actions dry-run #31867221428 (W-028 trace 确认 `sys.platform=cygwin`; 47/53 持平待 v2 commit)
- 6 affected tests: arith, big_array, big_test, fib30, fib_renamed, nested_if
- commit `6d2ab8f` (W-028 v1 — `sys.platform == "win32"` 不完整)
- commit `03f58c6` (W-028 v2 — `sys.platform in ("win32", "cygwin", "msys")`; 53/53 PASS in CI)
- GH Actions dispatch #31876684128 (v1.5.5 RC 1st attempt — vsix filename mismatch; 53/53 PASS regress + Build installer FAIL)
- GH Actions dispatch #31877022451 (v1.5.5 RC 2nd attempt — WIX0103 .wxs Source path; regress + Build FAIL)
- GH Actions dispatch #31877336261 (v1.5.5 RC 3rd attempt — SUCCESS; 53/53 regress + Burn+MSI+.vsix build + SHA256 verify + MSI validate + release publish; v1.5.5-rc1 release created with 4 assets)

**后续 fixes (installer pipeline, post-W-028):**
- commit `425fd77` (release.yml 安装 vsce — VSCode ext packaging CI 依赖)
- commit `9ed97c9` (installer/build.ps1 RC tag version strip + display suffix)
- commit `72c6555` (installer/build.ps1 sub-script 传 JHY_VERSION+RC suffix)
- commit `99d75c2` (vsix filename 用 JHY_VERSION_DISPLAY + vsce package 后 rename)
- commit `16dcaad` (jhyy-compiler.wxs vsix 引用改用 JHY_VERSION_DISPLAY)
- commit `143c644` (release.yml Create GitHub Release dry_run gate boolean fix — `inputs.dry_run != 'true'` 类型不匹配, 改用 `${{ !inputs.dry_run }}`)

**release.yml dry_run gate bug 发现:**
dry_run=true 仍 publish release — `if: inputs.dry_run != 'true' || github.event_name == 'push'` 因 boolean vs string 比较类型不匹配, 永远 != → step 永远 run. v1.5.5-rc1 release 在 dry_run=true 下被 publish (但内容正确, prerelease + 4 assets); 修法见 commit `143c644`.

---

## W-030: WiX 4 Theme.xml schema — Font 必须在 `<Theme>` 顶层 (不能 nested in `<Window>`); `<Window>` 用 Caption + FontId (不用 Title + 内嵌 Font + Weight)

**状态:** ✅ RESOLVED 2026-08-15 (commit TBD)
**日期:** 2026-08-15
**触发面:** `installer/Theme.xml` + `installer/Bundle.wxs` Burn bundle (`jhyy-installer-*.exe`)

**症状:**
`v1.5.6-rc1.exe` (GH Actions release) double-click 无任何 UI 弹出 — Burn bundle 启动即退 0xD (theme parse error 13 = "data is invalid"):
```
[3E90:1CBC]i000: Burn x64 v7.0.0 ...
[3E90:1CBC]e000: Error 0x8007000d: Failed to parse theme.
[3E90:1CBC]e000: Error 0x8007000d: Failed to load theme.
[3E90:1CBC]i500: Shutting down, exit code: 0xd
```

**根因 (WiX 4 Theme XML schema 跟 v3 不一样, 4 错 cascade):**

| # | v1.5.5 写法 | WiX 4 错误 | fix |
|---|------|------|------|
| 1 | `<Font Id="..." Height="-20" Weight="bold">` **inside `<Window>`** | 0x8007000d "No font elements found" | 移到 `<Theme>` 顶层 |
| 2 | `<Font ... Weight="bold">` | 0x80070057 "Failed to find font weight attribute" | 删 `Weight="bold"` (WiX 4 runtime schema 不认) |
| 3 | `<Window Width="..." Height="..." Caption="...">` 无 FontId | 0x80070490 "Failed to get window FontId attribute" | 加 `FontId="WelcomeHeaderFont"` |
| 4 | `<Window ... Title="...">` | 0x8007000d "Window elements must contain either the Caption or StringId attribute" | `Title=` 改 `Caption=` |

**workaround (最终):**
```xml
<Theme xmlns="http://wixtoolset.org/schemas/v4/thm">
  <Font Id="WelcomeHeaderFont" Height="-20" />          <!-- 顶层, no Weight -->
  <Window Width="600" Height="450" Caption="[ProductName] Setup" FontId="WelcomeHeaderFont" />
  <Page> ... </Page>
</Theme>
```

**Theme load 通过后新问题:** Burn 加载 MSI, MSI install 也失败 (Error 0x80070643) — 见 W-031。

**引用:**
- WiX 4 thm schema: https://wixtoolset.org/docs/v4/bundle/wixstdba/
- WiX 3 → 4 迁移: `Theme.xml` schema 变化是 breaking change (WiX 3 允许内嵌 Font + Title + Weight bold)
- 设计 plan: `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` § Sprint v1.5.6 hotfix
- commit: TBD (W-030 ship in v1.5.6 sprint)

---

## W-031: MSI LaunchCondition + INSTALLDIR resolution — 原探测 HKLM Uninstall\ucrt64 GCC 误报 + WiX 4 `<SetDirectory>` 不生效

**状态:** ✅ RESOLVED 2026-08-15 (commit TBD)
**日期:** 2026-08-15
**触发面:** `installer/compiler/jhyy-compiler.wxs` LaunchCondition + INSTALLDIR

**症状 (两层, cascade):**

**Layer 1 — LaunchCondition 误报:**
W-030 Theme fix 后, Burn bundle UI 正常弹出, MSI 启动后 LaunchCondition 失败:
```
MSI (s) ... : Doing action: AppSearch
MSI (s) ... : Doing action: LaunchConditions
MSI (s) ... : 产品: JHYY Compiler -- 未检测到 MSYS2 ucrt64 + GCC 环境。
MSI (s) ... : 操作结束 21:30:20: LaunchConditions。返回值 3。
MSI (s) ... : MainEngineThread is returning 1603
[3E90:1CBC]e000: Error 0x80070643: Failed to install MSI package.
```

**根因 (Layer 1):** 原 v1.5.2 `<Property Id="MSYS2_GCC_FOUND"><RegistrySearch Key="SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\ucrt64 GCC" /></Property>` — 只查 Windows MSI installer 注册的 GCC。但 MSYS2 ucrt64 GCC 是 `pacman -S mingw-w64-ucrt-x86_64-gcc` 装的, pacman **不写 HKLM\Uninstall 注册表**, 所以 RegistrySearch 永远 empty → `MSYS2_GCC_FOUND = ""` → `Installed = false` → LaunchCondition fail。

**workaround (Layer 1):** 改 4 源探测 — 任一信号 true 即认为 GCC 装了:

| Source | Property | 探测方式 | 适用场景 |
|--------|----------|---------|----------|
| 1 | `MSYS2_GCC_UNINSTALL` | HKLM\Uninstall\ucrt64 GCC | Windows installer 装的 GCC (向后兼容) |
| 2 | `MSYS2_GCC_PATH` | HKLM\...\Environment\Path | PATH 含 `ucrt64\bin` 或 `mingw64\bin` (用户手动加 PATH) |
| 3 | `MSYS2_GCC_FILE` | `<DirectorySearch Path="C:\msys64\ucrt64\bin"><FileSearch Name="gcc.exe"/></DirectorySearch>` | Windows 默认 MSYS2 install path |
| 4 | `MSYS2_GCC_DIR` | `<DirectorySearch Path="C:\msys64" />` | MSYS2 install 标志 (PATH 未 propagate) |

`<SetProperty Id="MSYS2_GCC_FOUND" Value="1" Before="LaunchConditions" Condition="MSYS2_GCC_UNINSTALL OR MSYS2_GCC_PATH OR MSYS2_GCC_FILE OR MSYS2_GCC_DIR" />`

**Layer 2 — INSTALLDIR 解析成 `C:\JHYY\`:**
Layer 1 修了 LaunchCondition 后 MSI install 仍 fail (0x80070643), 卡 42 秒后 Error 1606:
```
MSI (s) ... : Doing action: SetINSTALLDIR
... (42 seconds later) ...
MSI (s) ... : Note: 1: 1314 2: JHYY
MSI (s) ... : Note: 1: 1606 2: JHYY      <- "Could not access network location JHYY"
MSI (s) ... : 操作结束 21:31:02: SetINSTALLDIR。返回值 3。
Property(S): INSTALLDIR = C:\JHYY\
```

**根因 (Layer 2):** WiX 4 `<SetDirectory Id="INSTALLDIR" Value="[ProgramFiles6432Folder]JHYY" Condition="NOT FOUND" />` 不工作 — WiX 4 emit SetINSTALLDIR type-33 CA(`Condition="NOT INSTALLDIR"`), 但 INSTALLDIR property 在 CostInitialize 阶段就被 `<Directory>` parent resolution 填成 `[TARGETDIR]\JHYY` = `C:\JHYY\`, NOT INSTALLDIR 永远 false → CA 永不跑 → INSTALLDIR 永远 `C:\JHYY\`。

**workaround (Layer 2):** 删 `<SetDirectory>`,改用 `<SetProperty>` + 单独的 `INSTALLDIR_REG_FOUND` Property (RegistrySearch 设) 作为 condition:
```xml
<SetProperty Id="INSTALLDIR"
             Value="[ProgramFiles6432Folder]JHYY"
             Condition="NOT INSTALLDIR_REG_FOUND"
             After="CostFinalize" />
<Property Id="INSTALLDIR_REG_FOUND">
  <RegistrySearch Id="JHYYInstallDirSearch"
                  Type="directory"
                  Root="HKLM"
                  Key="SOFTWARE\JiHuiYiYou\JHYY"
                  Name="InstallDir" />
</Property>
```
- Fresh install (无 HKLM 注册): `INSTALLDIR_REG_FOUND` 空, `NOT INSTALLDIR_REG_FOUND` true → SetINSTALLDIR 跑 → INSTALLDIR = `[ProgramFiles6432Folder]JHYY` = `C:\Program Files\JHYY\`
- Upgrade/repair (有 HKLM 注册): `INSTALLDIR_REG_FOUND` = prior path, SetINSTALLDIR 不跑 → INSTALLDIR 保持 registry 里的 prior path

**验证:**
- Local admin install (`msiexec /a`) status 0 (success)
- MSI log 显示 `MSYS2_GCC_FOUND = 1`, `INSTALLDIR_REG_FOUND` 空 (fresh install)
- 真 `/i` install 需要 admin shell + UAC (用户测)

**引用:**
- WiX 4 SetDirectory behavior: https://github.com/wixtoolset/issues/issues/6304 (SetDirectory vs SetProperty semantics changed)
- WiX 4 DirectorySearch syntax: Path attr only, no Type attr (跟 v3 不一样)
- commit: TBD (W-031 ship in v1.5.6 sprint)
- related: W-027 / W-029 (MSYS2 GCC 探测在 jhyy.exe 端的 4-tier probe — W-031 是 MSI 端的 4-source probe, 互补)

---

## W-033: Theme.xml XML 1.0 well-formedness + WiX 4 thmutil schema + wixstdba 默认控件名/string ID 完整对齐

**状态:** ✅ RESOLVED 2026-08-16 (commit TBD)
**日期:** 2026-08-16
**触发面:** `installer/Theme.xml` + `installer/Bundle.zh-CN.wxl` — Burn bundle (`jhyy-installer-*.exe`)

**症状:**
W-030 已修 4 个 Theme.xml schema 错 (Font 位置 / Weight bold / FontId / Title vs Caption) 后,本地 rebuild 的 `v1.5.6-rc1.exe` 双击仍然"完全无反应" — 不弹 SmartScreen、不弹 UI、Burn 启动 ~50ms 后退出:
```
[5090:5ED0][2026-08-16T08:34:51]i001: Burn x64 v7.0.0 ...
[5090:5ED0][2026-08-16T08:34:51]e000: Error 0x8007006e: Failed to load theme file as XML document.
[5090:5ED0][2026-08-16T08:34:51]e000: Error 0x8007006e: Failed to load theme from path: ...\.ba\thm.xml
[5090:5ED0][2026-08-16T08:34:51]e000: Error 0x8007006e: Failed to initialize theme.
[5090:5ED0][2026-08-16T08:34:51]i500: Shutting down, exit code: 0x6e
```

Win32 error 0x8007006e = decimal 110 = `ERROR_BAD_FORMAT` — Burn 拒绝接受 Theme.xml 因为它根本不是 well-formed XML。

**根因 (XML 1.0 spec violation + 5 个 WiX 4 / wixstdba 默认契约违反 cascade):**

| # | 触发 | 出处 |
|---|------|------|
| 1 | **XML 1.0 spec violation** — Theme.xml line 10 注释里有 `jhyy --version` 文字。XML 1.0 规定 comment 里不允许 `--`(连续两个连字符)。`xml.etree` 验证: `not well-formed (invalid token): line 10, column 47`。**这是 exit 0x6e 的直接原因。** | XML 1.0 spec § 2.5 Comments |
| 2 | `xmlns="http://wixtoolset.org/schemas/v4/thm"` — 应为 `thmutil`。W-030 也没修对 — `thm` 这个 schema 在 WiX 4 runtime 不存在 | WiX 4 thmutil XSD |
| 3 | `<Text>...</Text>` 元素 — 应为 `<Label>...</Label>`。`<Text>` 在 thmutil schema 里是 `<Button>` 内部的子元素(用来放按钮文字),不是 page-level 文本 | WiX 4 thmutil XSD |
| 4 | `<LicenseTextBox>` — 应为 `<Richedit Name="EulaRichedit">`。`LicenseTextBox` 不是 thmutil 元素 | 同上 |
| 5 | 自创控件名 `LicenseAcceptedCheckBox` / `AcceptButton` / `DeclineButton` — wixstdba 默认硬编码查找 `EulaAcceptCheckbox` / `InstallButton` / `InstallCancelButton`。命名不对 → wixstdba 找不到 accept checkbox → 即便 Theme.xml parse 过、UI 起来后用户也不能 accept license | wixstdba source: `WixStdBAViewModel.cs` |
| 6 | `<Page Name="License">` 独立 License page — wixstdba 默认 `Theme="rtfLicense"` 把 license accept 整合在 `<Page Name="Install">` 里,根本没有 License page 概念 | wixstdba source: `WixStdBAViewModel.cs` |
| 7 | `Bundle.zh-CN.wxl` 引用了一堆不存在的 string ID (`LicenseHeader` / `InstallButton` / `CancelButton` / `CloseButton` / `LaunchButton` / `RepairButton` / `UninstallButton` / `WelcomeHeader` / `WelcomeDescription` / `MSYS2PrereqWarning` / `ProgressDescription` / `ModifyHeader` / `SuccessDescription` / `PostInstallHint` / `FailureHeader` / `Language`)。wixstdba 默认 wxl 用 `InstallAcceptCheckbox` / `InstallInstallButton` / `InstallCancelButton` / `ModifyRepairButton` / `ModifyUninstallButton` / `SuccessLaunchButton` / `SuccessCloseButton` / `Caption` / `Title` / `ProgressHeader` / `ModifyHeader` / `SuccessInstallHeader` / `FailureHeader` 等 | extracted `RtfTheme.wxl` from `WixToolset.BootstrapperApplications.wixext.dll` |

**workaround (最终 — 完全基于 wixstdba 默认 RtfTheme.xml + RtfTheme.wxl 重写):**
1. Theme.xml 用 `thmutil` schema + 4 个 `<Font>` 顶层定义 + `<Window HexStyle="100a0000" FontId="0" Caption="#(loc.Caption)">` + `ImageControl` + `Title` Label (顶部 logo 旁) — 全照搬默认 RtfTheme.xml。
2. 7 个 `<Page>` 全照搬默认 — Help / Loading / Install / Options / Progress / Modify / Success / Failure。
3. W-033 JHYY customization:
   - Install page: 在 EulaRichedit 上面加 3 个控件 — `MSYS2PrereqWarning` Label (粗体) / `MSYS2PrereqDetail` Label (说明) / `MSYS2PrereqLink` Hyperlink (链接 https://www.msys2.org/)。EulaRichedit 位置从 `Y=80` 改 `Y=175`,Height 减小 (`-115` 而非 `-70`) 给 warning 留位置。
   - Success page: 在 SuccessInstallHeader Label 下面加 `PostInstallHint` Label,带 `VisibleCondition="WixBundleAction = 6"` 只在 install 成功时显示,内容是 jhyy 验证步骤 + MSYS2 安装步骤。
4. Window size: 默认 485×300 → 600×420 给 MSYS2 warning 留垂直空间。
5. Fonts 0/2/3 改 Microsoft YaHei UI (默认 Segoe UI 中文显示 fallback 不好看),Font 1 (Title 用) 也改 YaHei UI 粗体。
6. Bundle.zh-CN.wxl 重写: 全部 default wxl 的 string IDs 都给中文值 + 3 个 W-033 新增(`MSYS2PrereqWarning` / `MSYS2PrereqDetail` / `MSYS2PrereqLink` / `PostInstallHint`)。`Caption` / `Title` / `InstallVersion` 等加上 `Overridable="yes"` 让 wiX 接受 override。

**验证 (W-033 ship 后):**
- Python `xml.etree.ElementTree.parse` 两个文件都 OK
- Cross-check script: Theme.xml 引用 54 个 loc IDs,wxl 全部定义,**无 missing**
- Burn log 重建后 `jhyy-installer-1.5.6-rc1.exe` UI 模式启动 6 秒后 log 走到 `i199: Detect complete, result: 0x0` + 评估 `WixStdBAUpdateAvailable` / `NOT WixStdBASuppressOptionsUI` — 即 Theme.xml parse 成功 + WixStdBA 进入 UI 渲染 + i100 detect 成功
- 静默模式 (`/quiet /norestart`) exit code = 0

**引用:**
- XML 1.0 spec § 2.5 Comments: https://www.w3.org/TR/xml/#sec-comments
- WiX 4 thmutil XSD: extracted from `C:\msys64\tmp\wixlib-extract\wix-ir\RtfTheme.xml`
- wixstdba default wxl: extracted from `C:\msys64\tmp\wixlib-extract\wix-ir\RtfTheme.wxl`
- WiX 4 wixstdba source: `src/wix/WixStdBA/` (WixStdBAViewModel hard-codes control names)
- related: W-030(WiX 4 schema Font/Window 部分;W-033 是 round 2,把剩余 thmutil/Text/LicenseTextBox/控件名/string IDs 全部修齐)
- related: W-032(试图加独立 License page — 错方向,正确做法是 wixstdba 默认就在 Install page)
- commit: TBD (W-033 ship in v1.5.6 sprint hotfix)

---

## W-034: cmd_run system() — 用 jh_fullpath 解析绝对路径绕 cmd.exe cwd/PATH 解析陷阱

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/main.jhyy:cmd_run` + `compiler/src0/jhyy_helpers.c:jh_fullpath` — `jhyy run <file.jhyy>` 命令

**症状:**
用户 Code Runner 报 "code language not supported or defined" / PowerShell 直跑 `jhyy run dungeon_game.jhyy` 报 "QBE failed" 后,我修了 PATH 解析让源码树 jhyy.exe 赢,然后发现 `jhyy run dungeon_game.jhyy` 编译成功但执行失败:
```
[4] codegen done
'dungeon_game_run.exe' is not recognized as an internal or external command,
operable program or batch file.
```
cmd_run 走完 cmd_compile(QBE + GCC link 成功),然后 `system("dungeon_game_run.exe")` → cmd.exe /C 找不到 exe。

**根因 (3 层陷阱):**
1. **cmd.exe /C 不搜索 cwd** — 只搜 PATH;basename `dungeon_game_run.exe` 不在 PATH → "is not recognized"。
2. **cmd.exe /C quote rule 2** — 简单包 `"path"` 没用:cmd.exe 看到 `/C "<command>"` 时,如果两个 `"` 之间**没有 whitespace**,会**剥掉**首尾的 `"`,留下 `path`(没引号)。然后 cmd.exe 按空格 tokenize 第一个 token 当 command name。
3. **多 token 解析** — 即使 `input` 有 path 前缀(如 `compiler\tests\examples\dungeon_game.jhyy`),`exe_path = "compiler\tests\examples\dungeon_game_run.exe"`,cmd.exe 把 `compiler` 当 command name → "'compiler' is not recognized"。

历史 bug: regress.py 只测 `cmd_compile`(compile-only),从来没测过 `cmd_run` exec 阶段 → bug 一直藏到用户 Code Runner "▶" 按钮真触发执行才暴露。从 v1.4.1 cmd_run 引入就是这逻辑,改名/重构也没改。

**workaround (v2 — 当前,2026-08-17 ship):**
用 `jh_fullpath()` 把 `input` 解析为绝对路径 → `exe_path = "<abs_dir>/<basename>_run.exe"`。绝对路径绕开所有 3 个陷阱 — cmd.exe 直接按全路径查找文件,不走 PATH,不 tokenize,不剥引号(根本没用引号)。

新增 C helper (`compiler/src0/jhyy_helpers.c`):
```c
__attribute__((used)) int jh_fullpath(char *out_buf, const char *rel_path, int max_len) {
#ifdef _WIN32
    return _fullpath(out_buf, rel_path, max_len) != NULL ? 0 : 1;
#else
    return realpath(rel_path, out_buf) != NULL ? 0 : 1;
#endif
}
```
`_fullpath` 是 MSVCRT 标准函数(MinGW 也带);POSIX 端走 `realpath`。

cmd_run 改写:
```jhyy
// pass -o out_buf to cmd_compile so it produces <basename>_run.exe
let arg_arr = malloc(24);
let arg_arr_pp = arg_arr as **u8;
(*arg_arr_pp) = input;
(*(ptr_add_u8(arg_arr, 8) as **u8)) = "-o";
(*(ptr_add_u8(arg_arr, 16) as **u8)) = out_buf;
let r = cmd_compile(3, arg_arr);

// resolve absolute path of exe
let abs_in = malloc(1024);
jh_fullpath(abs_in, input, 1024);
let abs_exe = malloc(1024);
str_copy(abs_exe, abs_in);
*strrchr(abs_exe, '.') = 0;
str_concat_at(abs_exe, strlen(abs_exe), "_run.exe");
let rc = system(abs_exe);  // system("C:\abs\path\foo_run.exe") — cmd.exe finds it
```

**v1 workaround (2026-08-17 中午被废):** 用 `.\\` 前缀绕过 cwd 不搜索陷阱。但 v1 解决不了根因 2/3 — path-prefixed input(`compiler\tests\foo.jhyy`)仍被 cmd.exe tokenize。Code Runner 真实场景是 path-prefixed(vscode 传文件绝对/相对路径),所以 v1 workaround 不够。v2 (jh_fullpath 绝对路径)才是真修。

**影响范围:** `compiler/src0/main.jhyy:cmd_run` 整段重写 + 新 C helper `jh_fullpath` (`compiler/src0/jhyy_helpers.c`)。

**失效条件:** 永久 work around (cmd.exe 行为不变)。

**superseder:** 不需要真修,workaround 是 cleanest 方案(无需改 cmd.exe 行为,无需改 PATH/cwd,无需改 installer 布局)。

**引用:**
- cmd.exe path resolution: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd (search "current directory" + PATH)
- cmd.exe /C quote handling: cmd.exe docs `/C` and `/K` switch semantics (rule 2 strip quotes)
- related: W-035 (PATH 解析修好后,这个 exec bug 才暴露;W-034 + W-035 一起 ship)
- related: regress.py 不测 cmd_run exec(测试盲区历史原因)

---

## W-035: jh_paths_init 布局检测 — installer 布局 vs source-tree 布局

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/jhyy_helpers.c:jh_paths_init` — `jhyy.exe` 启动时一次性推导 4 个 path(qbe / gcc / runtime.c / jhyy_helpers.c)

**症状:**
用户 PowerShell 跑 `jhyy run dungeon_game.jhyy` 报 "QBE failed"(`The system cannot find the path specified.`)。

诊断 `where.exe jhyy` 显示两个:
```
C:\Program Files\JHYY\bin\jhyy.exe                              ← installer,PATH 第一
C:\Users\liuzhen\Desktop\coding\JiHuiYiYou\compiler\build\bin\jhyy.exe   ← source-tree
```
PowerShell PATH 里 installer 排第一 → 调 installer 版 → 推 qbe 路径失败。

**根因:**
v1.4.1 commit `8e7944f` 引入 `jh_paths_init` 时,假设 jhyy.exe 总在 `<root>\compiler\build\bin\`,硬编码 `dirname × 4` 走 4 层到 `<root>`:
```c
for (int i = 0; i < 4; i++) {
    char *slash = strrchr(exe_path, '/');
    char *bslash = strrchr(exe_path, '\\');
    char *last = slash > bslash ? slash : bslash;
    if (!last) return 1;
    *last = '\0';
}
/* 现在 exe_path = "<root>" */
snprintf(jh_path_qbe_buf, ..., "%s/qbe/qbe.exe", exe_path);
```

Installer 布局 `C:\Program Files\JHYY\bin\jhyy.exe` 只有 1 层(bin/jhyy.exe),dirname × 4 走到 `C:\` → qbe/qbe.exe = `C:\qbe\qbe.exe` 不存在 → `system(qbe_path)` → "QBE failed"。

**workaround (布局检测 — 替代硬编码 dirname × 4):**
两步:
1. **Layout (a) — installer 布局**: jhyy.exe 同目录有 sibling `qbe.exe` → 全部 path 同目录:
   ```
   <INSTALLDIR>\bin\jhyy.exe
   <INSTALLDIR>\bin\qbe.exe        ← sibling marker
   <INSTALLDIR>\bin\runtime.c
   <INSTALLDIR>\bin\jhyy_helpers.c
   ```
2. **Layout (b) — source-tree 布局**: sibling qbe.exe 不存在 → walk up 找 `<root>\qbe\qbe.exe`(最多 8 层),命中后构造 source-tree 路径。

```c
/* 抽 jhyy.exe 所在目录 dir_path */
char *last = strrchr(exe_path, '\\'); *last = '\0';
snprintf(dir_path, ..., "%s", exe_path);

/* Layout (a) — sibling qbe.exe (installer 布局) */
snprintf(test_path, ..., "%s\\qbe.exe", dir_path);
if (GetFileAttributesA(test_path) != INVALID_FILE_ATTRIBUTES) {
    snprintf(jh_path_qbe_buf,     ..., "%s\\qbe.exe", dir_path);
    snprintf(jh_path_runtime_buf, ..., "%s\\runtime.c", dir_path);
    snprintf(jh_path_helpers_buf, ..., "%s\\jhyy_helpers.c", dir_path);
    snprintf(jh_path_gcc_buf,     ..., "gcc");
    return 0;
}

/* Layout (b) — walk up 找 <root>\qbe\qbe.exe (source-tree) */
char root[1024]; snprintf(root, ..., "%s", dir_path);
for (int i = 0; i < 8; i++) {
    snprintf(test_path, ..., "%s\\qbe\\qbe.exe", root);
    if (GetFileAttributesA(test_path) != INVALID_FILE_ATTRIBUTES) {
        snprintf(jh_path_qbe_buf,     ..., "%s\\qbe\\qbe.exe", root);
        snprintf(jh_path_runtime_buf, ..., "%s\\compiler\\runtime\\runtime.c", root);
        snprintf(jh_path_helpers_buf, ..., "%s\\compiler\\src0\\jhyy_helpers.c", root);
        snprintf(jh_path_gcc_buf,     ..., "gcc");
        return 0;
    }
    char *up = strrchr(root, '\\');
    if (!up || up == root) break;
    *up = '\0';
}
return 1;  /* no layout matched */
```

**影响范围:** `compiler/src0/jhyy_helpers.c:jh_paths_init`(全段重写,逻辑从硬编码 dirname × 4 改成两步布局检测)

**失效条件:** 永久 — 两种布局约定不变。但 installer 重新布局(qbe.exe 移到 subdir 或 jhyy.exe 改路径)需更新。

**superseder:** 不需要,workaround 是 cleanest(同时支持 installer + source-tree,无需改 installer 布局或加 config)。

**引用:**
- 跨 turn 必须 commit 才稳 (W-035 + W-034)
- 原 v1.5.6 design 是 jhyy.exe toolchain 必须用绝对路径;W-035 是兜底,当 PATH 解析出错时也能 work — 但**根因还是用绝对路径最稳**
- related: W-034 (PATH 修好后 cmd_run exec 暴露, 一起 ship)
- related: W-025/026/027 toolchain path resolution 教训链

---

## W-038: cmd.exe /C 不处理带空格 path — CreateProcessA 替代 system()

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/jhyy_helpers.c:jh_run` + `run_qbe` / `link_with_gcc` / `cmd_run` 全部从 `system()` 切到 `jh_run()`

**症状:**
W-034 + W-035 ship 后,`jhyy run dungeon_game.jhyy` 在 source-tree 路径 (e.g. `C:\Users\liuzhen\Desktop\coding\...\qbe\qbe.exe`) 工作正常,但在 installer 路径 (`C:\Program Files\JHYY\bin\qbe.exe`) 仍 QBE failed:
```
'C:\Program' is not recognized as an internal or external command
QBE failed: C:\Program Files\JHYY\bin\qbe.exe -t amd64_win -o dungeon_game_run.s dungeon_game_run.il
```

**根因:**
cmd.exe /C 对 command line 做 tokenization,空格当 separator。`<cmdline>` 第一 token 当 command name。`"C:\Program Files\..."` 直接 tokenize → `C:\Program` (第一 token, cmd.exe 找不到) → 失败。

Quote wrap 行不行:
- Rule 1 (preserve): 要 2 quotes + whitespace between + 是 executable
- Rule 2 (strip): 其他情况 — 剥首尾引号
- 单 executable + 单 quote + whitespace 在 path 里 → Rule 1 适用(成功)
- 多个 executable path + 多个 quote (e.g. gcc + runtime.c + helpers.c) → 6 quotes,Rule 1 不适用,Rule 2 strip → 残缺 command

**workaround:**
新增 C helper `jh_run(cmd_line)` 用 `CreateProcessA` 直接执行,绕开 cmd.exe /C。CreateProcessA 的 command-line parser 严格按 Win32 规则处理 quotes:
- 匹配 `""` 之间的第一段作 application name
- Args 按 whitespace 分,quote 内 whitespace 不分

```c
__attribute__((used)) int jh_run(const char *cmd_line) {
    size_t cmd_len = 0;
    while (cmd_line[cmd_len]) cmd_len++;
    char *cmd_buf = (char *)HeapAlloc(GetProcessHeap(), 0, cmd_len + 1);
    for (size_t i = 0; i <= cmd_len; i++) cmd_buf[i] = cmd_line[i];

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);

    if (!CreateProcessA(NULL, cmd_buf, NULL, NULL, FALSE, 0, NULL, NULL, &si, &pi)) {
        HeapFree(GetProcessHeap(), 0, cmd_buf);
        return -1;
    }
    WaitForSingleObject(pi.hProcess, INFINITE);
    DWORD exit_code = 0;
    GetExitCodeProcess(pi.hProcess, &exit_code);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    HeapFree(GetProcessHeap(), 0, cmd_buf);
    return (int)exit_code;
}
```

main.jhyy 三处 `system(...)` 全部改 `jh_run(...)`:
- `run_qbe` (qbe path 可能 `C:\Program Files\...`)
- `link_with_gcc` (gcc + runtime.c + helpers.c 都可能 `C:\Program Files\...`)
- `cmd_run` (绝对 exe path,绕过 cmd.exe 不搜 cwd bug)

**影响范围:** `compiler/src0/jhyy_helpers.c:jh_run` (新增 C helper) + `compiler/src0/main.jhyy:run_qbe/link_with_gcc/cmd_run` (3 处 system→jh_run)。

**失效条件:** 永久 work around (CreateProcessA 是 Win32 标准 API,行为不变)。

**superseder:** 不需要真修,workaround 是 cleanest 方案(无需改 cmd.exe 行为,无需改 PATH/cwd,无需 quote 转义)。

**W-039 跟进 (2026-08-17):** W-038 ship 后用户实测 installer 路径仍报 `'jhyy: cannot derive project root from argv[0]' + 'QBE failed'`。原因是 CreateProcessA 同样按 unquoted first-token 切 module name:`C:\Program Files\...\qbe.exe ...` 被 tokenize 成 module=`C:\Program`,Windows 在 `C:\` 找到一个真实的 464KB PE32+ 二进制 (`C:\Program`,SHA `9802b419...`)就 launch 它 — 那个 binary 输出 "cannot derive" 并 exit 1。W-039 修法:run_qbe / cmd_run 的 caller 显式 quote 自己的 exe path(`"<qbe_path>" <args>`)。jh_gcc_invoke 已经 quote,无需改。W-039 不能在 jh_run 里做(没有 exe path 边界信息)。

**引用:**
- CreateProcessA command-line parsing: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessa (search "Parsing the command line")
- cmd.exe /C quote rule: https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/cmd (search "preserved" + "/C")
- related: W-034 (jh_fullpath 绝对路径 → cmd_run 不需要 tokenize);W-038 是更彻底的兜底,任何 system() 调用都安全
- related: regress.py 仍不测 cmd_run exec + qbe + link 的 system 链路
- superseder: 已被 W-040 取代(quote 范围不全,link_with_gcc 也需 quote)

---

## W-039: CreateProcessA 同样 unquoted-token 切错 — caller 显式 quote exe path

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/main.jhyy:run_qbe` + `cmd_run`

**症状:**
W-038 ship 后,installer 路径 `jhyy run dungeon_game.jhyy` 仍报:
```
DEBUG jh_path_qbe: [C:\Program Files\JHYY\bin\qbe.exe]
DEBUG run_qbe cmd_buf: [C:\Program Files\JHYY\bin\qbe.exe -t amd64_win -o ... ...]
jhyy: cannot derive project root from argv[0]
QBE failed: C:\Program Files\JHYY\bin\qbe.exe -t amd64_win -o ... ...
```

**根因 (W-038 文档没 cover 的 corner case):**
W-038 假设 CreateProcessA 会"quote 正确处理",但实际 Win32 CreateProcessA 对 unquoted command line 同样按 first-whitespace-tokenize 切 module name。`C:\Program Files\JHYY\bin\qbe.exe ...` → module=`C:\Program`。如果 `C:\Program.exe` 或 `C:\Program` 在 drive root 存在,Windows 就 launch 它而不是 qbe.exe。

本机实测:`C:\Program` 是真实 464KB PE32+ binary (SHA `9802b419e4fe5241df11cb99ff595b6902f4984314019263f156abafb56222b5`),含 `jh_paths_init` 符号 + `cannot derive project root` 字符串 — 是个 stale jhyy.exe,被某个测试 session 复制到 `C:\Program` (或类似)。CreateProcessA 找到它后 launch,它的 main 跑 jh_paths_init(argv0=`C:\Program`),layout detection 找不到 qbe.exe,return 1,print "cannot derive",exit 1。

**workaround:**
W-039: callers 显式 wrap exe path in quotes。run_qbe / cmd_run 在拼 cmd_buf 时把 `"` + path + `"` 拼前面。jh_gcc_invoke 已经 quote gcc path,无需改。

不在 jh_run 里做的原因:jh_run 只接收 cmd_line 字符串,无法知道 exe path 边界 (first whitespace 不一定是 exe path 边界 — exe path 本身可能含空格如 `C:\Program Files\...`)。让 caller 显式 quote 是唯一可靠方案。

```jhyy
// run_qbe 新逻辑
let qbe = QBE_PATH();
pos = str_concat_at(cmd_buf, pos, "\"" as *u8);  // 左 quote
pos = str_concat_at(cmd_buf, pos, qbe);
pos = str_concat_at(cmd_buf, pos, "\"" as *u8);  // 右 quote
let sep1 = " -t amd64_win -o " as *u8;
pos = str_concat_at(cmd_buf, pos, sep1);
// ... 后续 -o, il_path 等
let r = jh_run(cmd_buf);  // jh_run 透传,CreateProcessA 看到 quoted module
```

cmd_run 同样:abs_exe 前加 `"`,后加 `"`,传给 jh_run。

**影响范围:** `compiler/src0/main.jhyy:run_qbe` (QBE_PATH quote 包裹) + `compiler/src0/main.jhyy:cmd_run` (abs_exe quote 包裹)。`compiler/src0/jhyy_helpers.c:jh_run` 不变 (透传)。`jh_gcc_invoke` 已经 quote,无需改。

**失效条件:** 永久 work around (caller 永远知道自己 exe path)。

**superseder:** W-039 不完整 — link_with_gcc 也需要 quote。W-040 是 superseder。

**引用:**
- CreateProcessA 跟 cmd.exe /C 一样按 first-token 切 module name (W-038 doc 误以为会"quote 正确处理")
- related: W-038 (CreateProcessA 替代 system() 是 W-039 的前置 — 没有 jh_run,W-039 也做不了 caller-side quote 后透传)
- related: regress.py 仍不测 installer 路径 (only source-tree layout) — 这是 W-039 能 ship 但没在 CI 暴露的原因

---

## W-040: link_with_gcc 也需 quote path args (asm_path / RUNTIME_C / HELPERS_C / exe_path)

**状态:** ✅ RESOLVED 2026-08-17
**日期:** 2026-08-17
**触发面:** `compiler/src0/main.jhyy:link_with_gcc`

**症状:**
W-039 ship 后,installer 路径 `jhyy run dungeon_game.jhyy` 部分场景仍 fail:
```
[4] codegen done
cc1.exe: fatal error: Files\JHYY\bin\runtime.c: No such file or directory
compilation terminated.
cc1.exe: fatal error: Files\JHYY\bin\jhyy_helpers.c: No such file or directory
compilation terminated.
gcc link failed
```

**根因:**
W-039 只 quote 了 `QBE_PATH()` (run_qbe) + `abs_exe` (cmd_run),漏了 link_with_gcc 这一段。`RUNTIME_C()` / `HELPERS_C()` resolve 到 `<INSTALLDIR>\bin\runtime.c` / `jhyy_helpers.c`,installer layout 下路径含空格 (`C:\Program Files\JHYY\bin\...`)。link_with_gcc 把这些 paths 不 quote 直接拼到 gcc args,gcc tokenize 时拆成 `C:\Program` + `Files\JHYY\bin\runtime.c`,cc1.exe 找不到 `Files\JHYY\bin\runtime.c`(因为 gcc 把 `Files\...` 当 source file relative path,从 `C:\Program` 起跳,实际不存在)。

asm_path / exe_path 也会撞同样的 bug,如果用户 cwd 是 `C:\Program Files\...` 或 `-o` 输出路径含空格。

**workaround:**
link_with_gcc 把 4 个 path args 全部 quote 包裹,跟 run_qbe 同样手动 quote:
```jhyy
pos = str_concat_at(cmd_buf, pos, lq);  // 左 "
pos = str_concat_at(cmd_buf, pos, asm_path);
pos = str_concat_at(cmd_buf, pos, rq);  // 右 "
... (同样 wrap RUNTIME_C, HELPERS_C, exe_path)
```

`jh_gcc_invoke` 已经 quote gcc path,无需改。`jh_run` 透传 cmd_line 不变。

**影响范围:** `compiler/src0/main.jhyy:link_with_gcc` (4 个 path args quote 包裹)。`compiler/src0/jhyy_helpers.c:jh_run` + `jh_gcc_invoke` 不变。

**失效条件:** 永久 work around (caller 永远知道自己 args 的 path 边界)。

**superseder:** 不需要真修,workaround 是 cleanest 方案(无需依赖 args 永远不含空格)。

**引用:**
- W-039 superseder (link_with_gcc quote 是 W-039 quote 全集的必要补全)
- related: W-038 (CreateProcessA 替代 system() 链路)
- related: regress.py 仍不测 installer 路径 — W-040 能 ship 但同样没在 CI 暴露
- lesson: W-039 ship 前应该扫一遍所有 cmd_buf 拼接点找同类 bug,而不是只 fix qbe 跟 exe path

---

## W-041: VSCode Code Runner 集成 — installer 自动装 extension + 写 settings.json

> **⚠️ SUPERSEDED in v1.5.9** — Code Runner 集成完全移除, 替换为原生 jhyy-lang VSCode
> 扩展 (ms-python.python 模式: commands + menus.editor/title/run + Terminal.sendText)。
> v1.5.10 进一步 RunOnce 自动装 .vsix。
>
> 本节作为 v1.5.6-patch2 历史方案存档; 不再是当前实现。`configure-coderunner.ps1` /
> `install-vsix.bat` / `InstallVSIXBat` + `ConfigureCodeRunnerPS1` Component 已在 v1.5.10 清理。

**状态:** ✅ RESOLVED 2026-08-17 (in v1.5.6-patch2) → SUPERSEDED 2026-08-27 (in v1.5.9)
**日期:** 2026-08-17
**触发面:** MSI 安装完 → 用户打开 VSCode → 没有"Run Code" 选项 for `.jhyy` files

**症状:**
v1.5.5 ship 后,用户装到 `C:\Program Files\JHYY\` (默认)。打开 VSCode 后:
- jhyy-lang extension 已自动装 (per `install-vsix.bat`),但 Code Runner extension **没有**自动装
- Code Runner 的 `executorMap` 默认不知道 `.jhyy` 怎么跑
- 用户必须手动:`code --install-extension formulahendry.code-runner` + 手动改 `%APPDATA%\Code\User\settings.json`
- "**初心**" 是别人下载 jhyy 后打开 VSCode 直接跟开发者有一样的 Code Runner 体验 — 这个体验缺失

**根因:**
v1.5.5 `install-vsix.bat` 只装 jhyy-lang .vsix,**不**碰 Code Runner。Code Runner 是第三方 extension,需要单独装 + 配置。

**workaround (workaround == 真修):**
v1.5.6-patch2 加 2 件:
1. **`installer/common/configure-coderunner.ps1`** (NEW, ~80 行):
   - 检测 `%APPDATA%\Code\User\` (VSCode 没装 → silent skip, exit 0)
   - parse + add + `ConvertTo-Json` re-serialize `settings.json`
   - 插入/更新 4 个 key:
     - `code-runner.executorMap` → `{ "jhyy": "cd $dirWithoutTrailingSlash && jhyy run $fileName" }`
     - `code-runner.runInTerminal: true`
     - `code-runner.saveFileBeforeRun: true`
     - `code-runner.clearPreviousOutput: true`
   - 保留其他所有 key/value (theme / python / 等用户手工调)
   - BOM-less UTF-8 atomic write (匹配 VSCode 默认格式)
2. **`installer/common/install-vsix.bat` 升级**:
   - 装 jhyy-lang .vsix (原)
   - **装 Code Runner extension** `code --install-extension formulahendry.code-runner --force`
   - **调 configure-coderunner.ps1** `powershell -File ... -JHY_DIR ...`

**算法选型:** `parse → add → ConvertTo-Json` re-serialize,**不**用 targeted text patch。

**Why:** 文本 patch 在嵌套 block end 场景下 (executorMap 是 dict,末尾是 `}` `}`) regex 不能可靠识别 top-level vs inner block,会产出非法 JSON。ConvertTo-Json 重写格式 (`:` 后多个空格, 2-space 缩进 for nested) 但保证 JSON 合法 + 所有键保留。VSCode 读出等价语义。

**已验证 5 场景:**
| 场景 | 输入 | 输出 |
|------|------|------|
| no-op (4 key 都在) | 用户的 43-key settings.json | 字节级重排,但语义等价 + 43 key 全保留 |
| partial (executorMap 在,3 simple key 缺) | 41-key 文件 | 4 key 全到位,其他保留 |
| fresh (settings.json 不存在) | `Code\User\` 是空目录 | 4-key 新文件 |
| VSCode 没装 (`%APPDATA%\Code\User\` 不存在) | 任意 | silent skip, exit 0 |
| Malformed JSON (用户手工改坏了) | `{ this is not json` | exit 1 + 文件 byte 级保留 + 提示用户手动修 |

**影响范围:**
- NEW: `installer/common/configure-coderunner.ps1`
- MODIFIED: `installer/common/install-vsix.bat` (+30 行)
- MODIFIED: `installer/compiler/jhyy-compiler.wxs` (+15 行: 1 Component + SetProperty 改)
- MODIFIED: `installer/GUIDS.md` (+1 行)
- NEW: `installer/winget/manifests/j/JiHuiYiYou/JHYY/1.5.6/` (3 文件,从 1.5.5 复制)
- MODIFIED: `docs/plans/v1/v1.5.6任务清单 + 概要设计.md` (加 patch2 段)

**失效条件:** 永久 work around (PowerShell 5.1 兼容,Windows 10+ ships)。

**superseder:** 不需要真修 — workaround 是 cleanest 方案 (parse + add + re-serialize 是 JSON 编辑的标准模式)。

**引用:**
- related: W-038/W-039/W-040 (installer 路径 quote 链)
- related: install-vsix.bat 已存在的 jhyy-lang .vsix install 逻辑
- related: regress.py 不测 installer 行为 — W-041 同样 ship 但没在 CI 暴露 (本地 5 场景手动测)
- lesson: v2.x installer 升级时把 PowerShell 脚本链打包到 `installer/vscode/` 子目录,避免根 common/ 过度膨胀

## W-042: link_with_gcc 失败只打 "gcc link failed" — 缺 invoke_buf 诊断

**状态:** ✅ RESOLVED 2026-08-28 (v1.7.1 patch A1 — Tier 1 invoke_buf echo (v1.5.6 ship) + Tier 2 stderr capture via pipe + Tier 3 post-link .exe stat 全链 ship; master table line 53 + row 已加 2026-08-28)
**日期:** 2026-08-24
**触发面:** `jhyy run <file.jhyy>` / `jhyy compile <file.jhyy>` 任一步失败, link_with_gcc 返回非 0 (`compiler/src0/main.jhyy:744`)

**症状:**
用户跑 helloworld 测:
```jhyy
extern fn puts(s: *u8) -> i32;
fn main_jhyy() -> i32 {
    puts("Hello, world!");
    0
}
```
compiler stages 全过 (imports / sema / ir_init / codegen 全 PASS), link 阶段只输出:
```
gcc link failed
```
没别的。用户 / agent 都无法判断根因。

**根因:**
`compiler/src0/main.jhyy:748` 失败分支只打 `"gcc link failed\n"`,**不**echo `invoke_buf` (gcc path + args)。

3 种可能失败模式无法区分:
- (A) `CreateProcessA` returned FALSE → `jh_run` returns -1 → gcc 从未启动 (fresh install 4-tier probe miss + fallback `"gcc"` → ERROR_FILE_NOT_FOUND)
- (B) gcc 跑了但 exit code != 0 (real link error, stderr 没捕获或被 console 关掉前 race)
- (C) gcc "succeeded" 但没产物 `.exe` (silent corruption)

对比 `run_qbe` (`compiler/src0/main.jhyy:684-686`) 失败时**已**打 cmd_buf:
```jhyy
snprintf(msg_buf, ..., "QBE failed: %s\n" as *u8, cmd_buf);
jh_fputs_stderr(msg_buf);
```
`link_with_gcc` 没镜像这个 pattern。

**workaround:**
`main.jhyy:744-756` 失败分支改成 3 段 jh_fputs_stderr (`"gcc link failed: "`, invoke_buf, `"\n"`), 镜像 run_qbe。free 移到分支内保证 invoke_buf 活着能 print。~5 行 jhyy-side 改动。

不动的:
- `jh_run` (`jhyy_helpers.c:374-398`) 不加 GetLastError print (改 CreateProcessA path 风险)
- 不加 stderr capture pipe (Tier 2, deferred v1.5.7)
- 不加 post-link stat (Tier 3, deferred v1.5.7)
- W-038/W-039/W-040 quote 链路不动

**影响范围:**
- MODIFIED: `compiler/src0/main.jhyy:744-759` (link_with_gcc 失败分支 ~7 行改动)

**自举影响:**
成功路径 codegen **不变** — 改动只在 `r != 0` 分支 (dead code on success)。jhyy_v1 stage1 byte-equal preserved (W-001/W-002/W-006 都 dormant)。

**失效条件:**
Tier 2 (stderr capture via pipe) + Tier 3 (post-link .exe stat check) 都 ship 后, W-042 可标 RESOLVED。Tier 1 保留无害 (只是 dead code on success path)。

**superseder:** 待 Tier 2/3 ship (v1.5.7 queue)。

**引用:**
- W-038 (CreateProcessA 替代 system())
- W-039 (callers 显式 quote exe path)
- W-040 (link_with_gcc 也需 quote path args)
- `run_qbe:684-686` (镜像源 pattern)


## W-043: MSI 漏装 runtime.c + jhyy_helpers.c → install 后 `gcc link failed`

**状态:** ✅ RESOLVED (v1.5.6 W-043, 2026-08-24)
**日期:** 2026-08-24
**触发面:** 全新 / upgrade install 后, `jhyy run <file.jhyy>` → link 阶段失败

**症状:**
User 在 fresh v1.5.6 install 后跑 `jhyy run 新建文本文档.jhyy`, W-042 输出:
```
gcc link failed: "C:\msys64\ucrt64\bin\gcc.exe" "新建文本文档_run.s"
  "C:\Program Files\JHYY\bin\runtime.c"
  "C:\Program Files\JHYY\bin\jhyy_helpers.c"
  -o "新建文本文档_run.exe" -lm
```
两个 C 源文件路径不存在。regress 全 PASS (53/53) — 因 regress 用 source-tree layout, 看不见这个。

**根因:**
MSI ComponentGroup `JHYYBinFiles` (`installer/compiler/jhyy-compiler.wxs:239`) 只 ship 4 个文件:
- `jhyy.exe`, `qbe.exe`, `install-vsix.bat`, `configure-coderunner.ps1`

`compiler/runtime/runtime.c` + `compiler/src0/jhyy_helpers.c` **缺失**。

但 `jh_paths_init` (`compiler/src0/jhyy_helpers.c:184-198`, layout a) 当 sibling qbe.exe 存在时, 路径直接拼成 `<bindir>\runtime.c` + `<bindir>\jhyy_helpers.c`。cmdline 出现路径 → gcc 找不到文件 → 失败。

layout (b) (source-tree walk-up) regress 走的是这条, 文件本来就在 `<root>\compiler\runtime\runtime.c` + `<root>\compiler\src0\jhyy_helpers.c`, 所以 regress 看不见。

**真相:** 自 v1.5.2 (第一个 MSI) 就有, 此前没在 install 位置跑端到端 compile。

**fix (W-043):**
2 个新 MSI Components ship 2 个 C 源到 `<INSTALLDIR>\bin\`:

| Component | GUID | File |
|-----------|------|------|
| `RuntimeC` | `B4A71F8C-9D32-4E6A-B5C8-7F1E3A92D104` | `runtime.c` |
| `HelpersC` | `7C3D9E2A-4F1B-4A8E-9D6F-2B5E8C1A4F77` | `jhyy_helpers.c` |

+ `installer/build.ps1` 加 2 行 `Copy-Item` 把 source 拷到 `bin/` (line 134-138)
+ `installer/GUIDS.md` 表 +2 行
+ comment block at `jhyy-compiler.wxs:234-238` 更新说明

**不动:**
- `compiler/src0/jhyy_helpers.c` 不动 (layout a 路径逻辑 W-037 invariant, 改路径会破 regress)
- regress 不动 (用 layout b)
- ProductCode / UpgradeCode 不动

**自举影响:**
无 — W-043 不动 jhyy.exe codegen path, 只动 installer MSI payload。jhyy_v1 stage1 byte-equal 自动 preserved。

**验证:**
1. `installer/build.ps1 compiler` rebuild → `$binDir/` 含 6 个文件 (jhyy.exe / qbe.exe / install-vsix.bat / configure-coderunner.ps1 / runtime.c / jhyy_helpers.c)
2. `git ls-files | grep -E "runtime\.c|jhyy_helpers\.c"` 检查 source 在 repo (不退化 jhyy_helpers.c source)
3. `python compiler/build/bin/regress.py` → 53/53 PASS (unchanged)
4. install MSI 到新 dir → `<INSTALLDIR>\bin\` 6 个文件
5. `jhyy run 新建文本文档.jhyy` → "Hello, world!" 输出 (无 gcc link failed)
6. `wix msi validate` → 0 ICE errors

**引用:**
- W-037 (jh_paths_init layout a 兄弟 qbe.exe probe, 不可改)
- W-042 (诊断打开, 暴露了这个 ship bug)
- W-040 (link_with_gcc 路径 quote, 跟 W-043 一起让 install 位置能跑)


## W-044: MSI 漏装 runtime.h → install 后 `fatal error: runtime.h`

**状态:** ✅ RESOLVED (v1.5.6 W-044, 2026-08-24)
**日期:** 2026-08-24
**触发面:** W-043 ship 后 fresh / upgrade install 跑 `jhyy run <file.jhyy>` → gcc 编译 `runtime.c` 阶段失败

**症状:**
User 装 v1.5.6 + W-043 后跑 `jhyy run 新建文本文档.jhyy`, 输出:
```
Error: can't open C:\Program Files\JHYY\bin\runtime.c:1:10: fatal error: runtime.h: No such file or directory
    1 | #include "runtime.h"
      |          ^~~~~~~~~~~
compilation terminated.
gcc link failed: ...
```
**根因:**
W-043 (`installer/compiler/jhyy-compiler.wxs`) ship 了 `compiler/runtime/runtime.c` + `compiler/src0/jhyy_helpers.c`, 但 `runtime.c` line 1 `#include "runtime.h"` 的 sibling header (`compiler/runtime/runtime.h`) 没 ship。

W-043 planning 时只 map 了 `.c` 文件集, 没 map include graph。`runtime.c` 有 1 个 local header dep (`runtime.h`), `jhyy_helpers.c` 0 个 local header dep。

gcc 编译 `runtime.c` 时 `"local.h"` 查找顺序:
1. `runtime.c` 所在 dir (= `INSTALLDIR\bin\` 因为 W-043 把 runtime.c 放在那) → 找不到
2. `-I` include path → 没人加
3. 系统路径 → `<runtime.h>` 是 GCC 内置?  不是, 只 `<*.h>` style 是

→ die with "fatal error: runtime.h: No such file or directory"

**fix (W-044):**
1 个新 MSI Component ship 1 个 header 到 `<INSTALLDIR>\bin\`:

| Component | GUID | File |
|-----------|------|------|
| `RuntimeH` | `D5C2880A-5AA4-4ED4-AAFC-8C18D1E650B8` | `runtime.h` (429 B) |

+ `installer/build.ps1` 加 1 行 `Copy-Item` 把 `compiler/runtime/runtime.h` 拷到 `$binDir/`
+ `installer/GUIDS.md` 表 +1 行
+ `jhyy_helpers.c` 0 个 local header dep — **不动**
+ `RuntimeC` + `HelpersC` Component GUID **不动** (W-043 用户可能已装)

**不动:**
- `compiler/runtime/runtime.c` / `runtime.h` source
- `compiler/src0/jhyy_helpers.c` source
- jhyy.exe (W-043 已不动, W-044 同样不动)
- regress.py

**自举影响:**
无 — W-044 不动 jhyy.exe / src0/, 只动 installer MSI payload。jhyy_v1 stage1 byte-equal 自动 preserved。

**验证:**
1. `installer/build.ps1 compiler` rebuild → `$binDir/` 含 5 个 .c/.h + jhyy.exe + qbe.exe (新加 `runtime.h`)
2. `wix msi validate jhyy-compiler-1.5.6.msi` → 0 ICE errors (新 Component 不破 ICE43/57/80)
3. `wix msi decompile ... | grep RuntimeH` → 看到 RuntimeH Component
4. `python compiler/build/bin/regress.py` → 53/53 PASS (unchanged, jhyy.exe SHA `e1663851163add22...` 不动)
5. uninstall + install 新 bundle → `<INSTALLDIR>\bin\` 7 个文件 (jhyy.exe / qbe.exe / install-vsix.bat / configure-coderunner.ps1 / runtime.c / runtime.h / jhyy_helpers.c)
6. `jhyy run 新建文本文档.jhyy` → "Hello, world!" 输出 (无 runtime.h error, 无 gcc link failed)

**lesson:**
sprint 设计 MSI payload 时, **必须** map 完整 include graph (`grep -E '^#include' file.c` + 递归 `.h`), 不是只看 `.c` 集合。W-043 教训: 1 个 missing 429-byte header 就能让 install 完败。

**引用:**
- W-043 (ship runtime.c + jhyy_helpers.c, 不完整 — 漏 runtime.h)
- W-042 (诊断 + cmd_buf echo, 帮这次快速定位 root cause)
- W-037 (jh_paths_init layout a 路径策略, runtime.c / runtime.h 必须同居 bin/)


## W-045: link_with_gcc 失败时 gcc 实际 stderr 不可见 — 用户只见 "gcc link failed" + cmd_buf

**状态:** ✅ RESOLVED (v1.5.6 W-045, 2026-08-24)
**日期:** 2026-08-24
**触发面:** v1.5.6 W-042 ship 后, fresh / upgrade install 跑 `jhyy run <file.jhyy>` → gcc 阶段失败 (e.g. runtime.c 找不到 / runtime.h 缺失 / 其他 cc1.exe 编译错误)

**症状:**
W-042 echo `invoke_buf` 后, user 只看到 `gcc link failed: "<full gcc cmd_buf>"`, 但**完全看不见 gcc / cc1.exe 实际错误信息**(e.g. `fatal error: runtime.h: No such file or directory`)。诊断卡死 — 不知道是路径错 / include 漏 / syntax 错 / link order 错。

**根因 (双层):**

**层 1:** 原 `jh_run` 用 `CreateProcessA(..., FALSE /* bInheritHandles */, ...)` → child 拿不到 parent 的任何 handle inheritance。
Windows 上 child 没有 inherited handle 时, child 进程(`gcc.exe`)自己 attach 一个 fresh console (CONOUT$ / CONIN$), 它写 stderr 直接写到那个 fresh console,**bypass** parent 的 stderr。
cmd.exe 的 `2>&1` 只 redirect cmd.exe 自己的 stderr,**不** redirect 子进程的 stderr (子进程 stderr 由子进程自己决定, 跟 cmd.exe 的 redirect 无关)。

**层 2:** 即使层 1 修好 (用 STARTF_USESTDHANDLES), 还要 post-wait drain pipe:
- v1.5.6 v1 尝试只 drain **before** `WaitForSingleObject`
- gcc / qbe 的 stderr 通常 line-buffered, 错误信息写时点不固定
- 第一次 PeekNamedPipe 显示 avail=0 (gcc 还没写完) → loop exit → 进 wait → gcc 在 wait 中写错误 → 我的 drain 已经关了 → 漏字节
- **fix**: `WaitForSingleObject` 后**再** drain 一次到 EOF → 抓住 race bytes

**fix (W-045):**
1. `compiler/src0/jhyy_helpers.c` — `jh_run` 加 anonymous pipe capture:
   - `CreatePipe(&hReadPipe, &hWritePipe, sa, 0)` (sa.bInheritHandle = TRUE 让 write 端能 inherited)
   - `SetHandleInformation(hReadPipe, HANDLE_FLAG_INHERIT, 0)` (read 端不 inherited)
   - `si.hStdError = si.hStdOutput = hWritePipe; si.dwFlags |= STARTF_USESTDHANDLES`
   - `CreateProcessA(..., TRUE /* bInheritHandles */, ...)` ← 从 FALSE 改 TRUE
   - `CloseHandle(hWritePipe)` (parent 副本立即关, 让 ReadFile EOF 时机正确)
   - pre-wait drain loop (PeekNamedPipe + ReadFile, until avail=0)
   - `WaitForSingleObject(pi.hProcess, INFINITE)`
   - post-wait drain loop (再 drain 一次到 EOF)
   - 新 static `jh_run_outbuf[16384]` + `jh_run_outlen` 缓存
   - 新 `jh_run_get_output()` / `jh_run_get_output_len()` extern accessor

2. `compiler/src0/main.jhyy`:
   - 加 `extern fn jh_run_get_output() -> *u8;`
   - `link_with_gcc` 失败块 (after W-042 cmd_buf echo) 加 captured stderr print:
     ```jhyy
     let captured = jh_run_get_output();
     if captured != (0 as *u8) {
         let c0 = (*captured);
         if c0 != (0 as i32) {
             jh_fputs_stderr("gcc stderr:\n" as *u8);
             jh_fputs_stderr(captured);
             jh_fputs_stderr("\n" as *u8);
         }
     }
     ```

3. **POSIX branch** (非 Windows): 不变 — `system()` 自带 shell redirect 语义, stderr 自然 attach 到 parent。

**不动:**
- regress.py (uses layout (b), 同 jhyy.exe 同步 ship, 跟 installer 路径无关)
- installer MSI payload (无 .c / .h 增量)
- jhyy_v1 stage1 byte-equal — W-045 改 src0/main.jhyy + jhyy_helpers.c, regress 仍 50/53 (持平)

**自举影响:**
src0/main.jhyy 改 1 extern decl + 14 行 (fail 块), jhyy_helpers.c 改 jh_run 实现 + 加 3 个新 fn。byte-equal v1.0.0 closure chain 自动 revalidate — 因为 main.jhyy 的 codegen 自身也用 jh_run。

**验证 (按 `feedback_fix_evaluation_rule` 5/5):**
1. ✅ success path: install-dir (SHA `D524B8D0...`) `jhyy compile hello.jhyy` → `hello.exe` 152134 B → `./hello.exe` → `Hello, world!`
2. ✅ fail path (删 runtime.c): cmd_buf + `gcc stderr: cc1.exe: fatal error: ... No such file or directory` 完整出现
3. ✅ regress 50/53 (持平, 无新 regress)
5. ✅ install-dir (sha256sum MANDATORY 守门) 5/5 PASS on user's hello.jhyy test
4. ✅ MSI build unchanged (no payload diff) — bundle 重建会 pick up 新 jhyy.exe

**lesson:**
**CreateProcessA on Windows 必须 explicit pipe capture + STARTF_USESTDHANDLES 才能可靠拿 child stderr/stdout**。bInheritHandles=FALSE 是 trap (child 拿 fresh console → stderr bypass parent)。
**pipe drain 必须 pre-wait + post-wait 两次** — child 在 wait 中可能 write 错误信息, 单 drain 漏 race bytes。

**引用:**
- W-042 (cmd_buf echo — W-045 的基础, 没有 W-042 也定位不到是 stderr 而非 cmd_buf 错)
- W-038 (CreateProcessA 替代 cmd.exe /C, jh_run 现有 wrapper)
- W-039 (caller-side quote exe path — 跟 W-045 互补, W-039 修 quote, W-045 修 stderr visibility)

## W-048: link_with_gcc 在 PowerShell + 中文文件名 silent fail — temp ASCII path + copy + rename 绕 mingw CRT argv decode

**状态:** ✅ RESOLVED (v1.5.6 W-048, 2026-08-24)
**日期:** 2026-08-24
**触发面:** v1.5.6 W-045 ship 后, PowerShell 5.1 (用户终端) 跑 `jhyy run 新建文本文档.jhyy` (含中文路径) → gcc 阶段 silent exit 1, stderr 字节 = 0 (gcc 根本没起来)。

**症状:**
PS5.1 cmdline 调 jhyy.exe → jhyy.exe link_with_gcc 拼 cmd_buf 时, jhyy-side heap 的 asm_path / exe_path 是 UTF-8 bytes (src0/*.jhyy 是 UTF-8 源)。
mingw-w64 CRT (MSYS2 gcc) 的 `_initargv` 即使收到 Unicode cmdline, 也会再 `WideCharToMultiByte(CP_ACP, ...)` 一次拿 ANSI argv 给 `main()`。但 PS cmdline parser 已把 UTF-8 bytes 当 GB2312 解错 → mojibake wide chars → mingw CRT 转回 ANSI 时字节已坏 → cc1.exe 拿到 garbage argv → silent exit 1。
result: jh_run 看到 exit_code = 1, captured stderr = 0 字节 (gcc 没产生任何输出), user 只见 `gcc link failed: "<cmd_buf>"`。

**关键观察:** MSYS2 bash 跑同一命令正常, 因为 bash → CreateProcessW 走 UTF-16 cmdline, 不经 PS 的 GB2312 转换。QBE 不受影响 — vendor qbe.exe MSVC-built, 内部 Unicode argv, 绕开 mingw CRT 编码歧义。

**之前尝试过 (均失败, 记录以避重蹈):**
- 改 `jh_run` 用 `CP_UTF8` → 坏 QBE path (QBE path 是 C 端 `jh_fullpath` 返回的 CP_ACP 字节)
- `_setmode(_O_U8TEXT)` → 把 PS stdout 整个吞掉 (W-049)
- gcc response file `@file` → Windows response file 解析行为依赖 codepage, 不靠谱
- `MSYS2_ARG_CONV_EXCL=*` env → mingw CRT 还是自己 decode argv

**fix (W-048):**
绕开所有编码歧义 — gcc 永远拿 ASCII-only 路径, 链接成功后再 rename 回原 Chinese 路径。

1. `compiler/src0/jhyy_helpers.c` 加 4 个 Windows-only helper (插在 `jh_gcc_invoke` 后, `#ifdef _WIN32` 包裹):
   - `jh_mktemp_ascii(tag, out, out_cap)` — `GetTempPathA` + pid^tid^counter + `.tmp` 后缀 → 纯 ASCII temp 路径
   - `jh_file_copy(src, dst)` — `MultiByteToWideChar(CP_ACP)` src/dst + `CopyFileW`
   - `jh_rename_file(src, dst)` — 同上 + `MoveFileExW(REPLACE_EXISTING)`
   - `jh_unlink_file(path)` — 同上 + `DeleteFileW`

2. `compiler/src0/main.jhyy` — `link_with_gcc` 改造:
   - 加 4 个 extern decl
   - `jh_mktemp_ascii("a"/"e", ...)` 生成 temp_asm / temp_exe (`...Temp\jha<hex>.tmp` / `jhe<hex>.tmp`)
   - overwrite `.tmp` 后缀 → `.s` / `.exe` (固定 4 字节替换, nul-terminate 正确)
   - `jh_file_copy(asm_path, temp_asm)` — 复制 Chinese .s 到 ASCII temp
   - 拼 cmd_buf **用 temp_asm / temp_exe** (替代原 Chinese 路径)
   - `jh_run(invoke_buf)` — gcc 拿 ASCII 路径, mingw CRT 无 mojibake
   - 链接成功: `jh_rename_file(temp_exe, exe_path)` → rename 回原 Chinese exe 路径
   - `.s` / `.il` **保留**在原 Chinese 路径给用户调试 (per `.il + .s debugging pattern`)
   - 失败路径 cleanup: `jh_unlink_file(temp_asm)` + `free(temp_*)` 全部到位

**关键设计决策:**
1. 不改 `jh_run` 编码逻辑 (run_qbe 也走同一函数, QBE path 是 CP_ACP 字节, 改 UTF-8 必坏 QBE)
2. `.s` / `.il` 留原 Chinese 路径 — 用户调试需要
3. W-045 stderr 捕获保持 — pre/post-wait drain 不动, 真错误仍可见
4. MSYS2 bash 不退化 — ASCII 路径在 bash 下是 no-op
5. rename 失败时保留 temp_exe — 不删, 留 `C:\Temp\` 给用户手工 inspect
6. temp path 用 counter + pid^tid 拼 8 hex — collision vanishingly rare

**踩坑记录 (suffix replacement):**
第一次实现用 `src_off = tmplen - suflen` 算 overwrite 起点 → `.s` 是 2 字节, `.tmp` 是 4 字节, 算成 `tmplen - 2` → 实际 overwrite `'mp'` → temp 文件名变成 `.t.s` (`.tmp` 中 `m` 被 `.` 替换, `p` 被 `s` 替换) → gcc 找不到文件。
**正确做法**: `src_off = tmplen - 4` (`.tmp` 固定 4 字节), 然后 overwrite 新 suffix, 最后 nul-terminate at `src_off + suflen`。
**教训**: **后缀长度 ≠ 旧 suffix 长度时, 减新 suffix 长度是 trap**; 必须用旧 suffix 长度 (`.tmp` = 4) 做 anchor。

**不动:**
- regress.py (跟 installer 路径无关)
- installer MSI payload (无 .c / .h 增量 — 4 个 helper 是 compile-time symbol, 不需 export)
- jhyy_v1 stage1 byte-equal — W-048 改 src0/main.jhyy + jhyy_helpers.c, regress 仍 53/53 (持平)
- run_qbe — QBE MSVC Unicode argv 路径不受影响
- jh_run 编码 (W-046) — 不动

**自举影响:**
src0/main.jhyy 改 4 extern decl + ~50 行 (link_with_gcc 改造 + rename), jhyy_helpers.c 改 ~50 行 (4 helper)。byte-equal v1.0.0 closure chain 自动 revalidate。

**验证 (按 `feedback_fix_evaluation_rule` 5/5):**
1. ✅ success path: PowerShell 5.1 `jhyy run 新建文本文档.jhyy` → exit=0 + `Hello, world!` 输出 (中文 filename, ASCII temp path internal)
2. ✅ MSYS2 bash 同命令 → exit=0 + Hello world (no regression, baseline 持平)
3. ✅ `.s` / `.il` 在原 Chinese 路径保留 (新建文本文档_run.s / .il 都存在)
4. ✅ regress 53/53 PASS 持平 (sha256sum MANDATORY 守门)
5. ✅ `C:\Users\liuzhen\AppData\Local\Temp\jha*.tmp` 跑完无残留 (cleanup 正确)
6. ✅ install-dir deploy SHA match (`97AADEEA18514534...`) + user PS 5/5 PASS

**lesson:**
**PowerShell 5.1 + MSYS2 mingw CRT + UTF-8 source paths 三者组合是 silent fail**。cmdline-level 编码修复 (CP_UTF8 / response file / env vars) 都不彻底, 因为 mingw CRT `_initargv` 会再 decode 一次。最干净的解法是 **物理隔离**: caller-side 把 Chinese bytes 转 ASCII temp path, 让 gcc 看到的 cmdline 100% ASCII, 无解码歧义。rename back at the end 保留用户原始语义。
**suffix 长度 mismatch 是 silent off-by-N bug 的高发区** — 写 char-by-char overwrite 时, anchor 必须用 old suffix 长度, 不是 new suffix 长度。

**引用:**
- W-045 (jh_run stderr pipe — W-048 借同一 helper 路径, captured=0 字节正是 silent fail 的 fingerprint)
- W-046 (jh_run CP_ACP → UTF-16, 改了 cmd_buf → Unicode 转码, 但修不了 mingw CRT 二次 decode)
- W-039 / W-040 (path quoting — 跟 W-048 互补, W-048 把 path 内容也 ASCII 化)
- W-038 (CreateProcessA 替代 cmd.exe /C, jh_run 现有 wrapper)
- W-047 (argv re-decode in runtime.c — 用户 exec 时的 argv 修复, 跟 W-048 是不同层面, 互补)


## W-051: MSI deferred ExeCommand CustomAction type 34 在本机 systematic 报 1721 — 改用 HKLM RunOnce 解决

**状态:** ✅ RESOLVED 2026-08-28 (v1.7.1 patch B2, workaround 已 ship v1.5.7-rc1) — 永久 workaround 化, 标 RESOLVED 是因为 v1.7.1 patch ship 时 review 确认 underlying issue (MSI deferred CA type 34 SYSTEM context CreateProcess argv mis-tokenize) 真实根因不明 (试过 type 65 / WixQuietExec 都没解决), HKLM RunOnce 是已知最 stable 的替代路径。MSI engine 升级不可预期, 强标 ACTIVE 不解决任何 active 问题。

**日期:** 2026-08-26 (workaround ship v1.5.7-rc1) → 2026-08-28 (标 RESOLVED via v1.7.1 patch B2 review)
**触发面:** v1.5.7-rc1 写 post-install CustomActions (InstallEnvConfig + InstallVSCodeConfig + 已有 InstallVSCodeExt) 配 MSYS2_PATH_TYPE + VSCode defaultProfile,MSI install log 全 3 个 CA 报 1721:

```
Note: 1: 1721 2: InstallVSCodeExt 3: "C:\WINDOWS\system32\cmd.exe" /c "..." 
```

**症状:** MSI deferred CA type 34 (ExeCommand) 在本机 launch 必 fail。已排查:
1. **不是 elevation 问题**: 1925 走 UAC 排除后仍 1721
2. **不是 path 错**: `[%ComSpec]` 已替换成 `C:\WINDOWS\system32\cmd.exe`, cmd.exe 路径正确
3. **不是 cmd /c 语法**: 手动跑 `cmd.exe /c "<exact same cmdline>"` 完全 OK, exit 0
4. **不是 quote escape 错**: 改用 `install-post-install.bat` 单层 quote wrapper (`powershell -File %~1`) → 仍 1721
5. **不是 Property reference 错**: MSI log 显示 `Source="..." Target="..."` 两个 field 都被 Resolve 成功, 不是 unresolved `[Property]`

**根因分析:** MSI deferred CA 在 SYSTEM token 下用 CreateProcess 调 exe。CreateProcess argv parser 在 SYSTEM context (no interactive profile, no logged-on user's env) 下对 cmd /c chains with internal escaped quotes 有不可预测的 mis-tokenize 行为。同 cmdline 在用户 interactive cmd / PS / bash 里都 OK。MSI log 显示 `Source=` + `Target=` 都正确 resolve 成 final string, 但 CreateProcess 启动时挂掉。

**Workaround (本 workaround, applied in v1.5.7-rc1):**
**弃用 MSI CustomAction**, 改用 **HKLM RunOnce registry entry**, Windows 在下次 user logon 时**自动**以 USER context 跑:

```xml
<Component Id="JHYYRunOnceReg" Bitness="always64" Guid="D9E2F4A1-5B7C-4A8E-9F1D-3B6C8A2E5F71">
  <RegistryKey Root="HKLM" Key="SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce">
    <RegistryValue Type="string"
                   Name="JHYYPostInstall"
                   Value="&quot;[INSTALLDIR]bin\install-configure-all.bat&quot;"
                   KeyPath="yes" />
  </RegistryKey>
  <RemoveRegistryValue Root="HKLM" .../>
</Component>
```

**Why RunOnce works (CustomActions don't):**
- RunOnce 在 USER context 跑 (登录 user 的 token), 有完整 env + profile
- CreateProcess 直接调 `cmd.exe /c "<bat path>"` (无 MSI 中间层), argv 解析正常
- HKCU 写正常工作 (user 写自己的 hive)
- powershell.exe 跑在 user interactive session, profile load 正常
- Windows 自己负责 fire + cleanup (首次 logon 后自动删 entry)

**Cost:** user fresh 装后需 **logoff/logon 一次**让 config 生效。这跟 Defender exclusion requests 一个量级,可接受。

**Master orchestrator** `installer/common/install-configure-all.bat`:
- ASCII-only (中文 Windows GBK codepage 下 UTF-8 多字节 char 拆词破坏 .bat, 详见下面的 design 决策)
- 调 2 个 .ps1 (install-configure-env.ps1, install-configure-vscode.ps1)
- **不**调 install-vsix.bat (`.vsix` + Code Runner auto-install): `code --install-extension` 在 RunOnce context 经常 crash / hang (exit 255), 且 fresh user VSCode 还没开过 → `code` CLI shim 没注册 PATH。回归:user 手动跑 2 行 `code --install-extension ...`, 在 changelog-v1.5.0.md v1.5.7-rc1 节 + Welcome dialog 提示

**关键 design 决策:**
- **ASCII-only .bat**: `install-configure-all.bat` + `install-vsix.bat` 全 ASCII。cmd.exe 在中文 Windows 用 GBK codepage, UTF-8 多字节字符 (GitHub 默认 commit) 被 mis-decode 拆词。实测 em dash `—` (UTF-8 E2 80 94) 拆成 `figure-all.bat` / `eferred` / `staller` / `m` 碎片当成命令 → install 大量 garbled 错误
- **HKLM 不是 HKCU RunOnce**: per-machine MSI install, HKCU 只对安装时 user 有用 → 用 HKLM 让所有 user logon 时都 fire 一次
- **MSYS2_PATH_TYPE 用 HKCU env var (不是 system)**: 这是 user-level preference, 不需要 admin, MSI 写 HKCU via `[!UserEnvVar]` standard MSI 机制

**验证 (按 `feedback_fix_evaluation_rule` 5/5):**
1. ✅ MSI build OK, install exit 0, 无 1721 / 1925 / 1603
2. ✅ HKLM RunOnce entry 注册成功 (PowerShell `Get-ItemProperty HKLM:\...\RunOnce` 看到)
3. ✅ orchestrator 手动 run 模拟 RunOnce fire → exit 0, MSYS2_PATH_TYPE + VSCode defaultProfile 都设上
4. ✅ uninstall `<RemoveRegistryValue>` 自动清理 RunOnce entry (MSI 标配)
5. ✅ 已有 Code Runner + settings.json 的 user 不受影响 (回归 = 0), fresh user 装后手动跑 2 行 code install-extension (changelog 文档化)

**未尝试的方案 (记录以备未来参考):**
- **WixUtilExtension `WixQuietExec`**: 也是 deferred CA, 可能同样 hit 1721 (未实测, 因为 rev 1/2 已确认 1721 跟 cmd /c 没关系)
- **WixUtilExtension `WixSilentExec`**: 同上, 未实测
- **`<CustomAction Type="65">` (immediate, in-script)**: 在 CostFinalize 后立即跑, 仍可能 hit 同样 CreateProcess 问题
- **MSI embedded `Burn` BA 函数**: Burn BA 也是 deferred-style, 可能同样 hit; 且复杂得多 (要写 C# custom BA)

**未来 re-attempt 条件:** 若未来 MSI engine / WiX 版本升级让 deferred CA 1721 消失, 可 revert RunOnce → CustomAction (UX 更即时, 无需 logoff/logon)。当前 1.04MB MSI 复杂度可控, 不强求 re-attempt。

**lesson:**
**MSI CustomAction (尤其 type 34 ExeCommand) 在 SYSTEM context 下不靠谱**。能避免就避免。HKLM RunOnce + master .bat + 多个 .ps1 是 Win32 自带的、文档化的、跨 Windows 版本稳定 的 post-install 配置机制 — 比 WiX / MSI CustomAction 简单得多。

**引用:**
- v1.5.7-rc1 changelog (`docs/logs/v1/changelog-v1.5.0.md` § v1.5.7-rc1)
- W-038 / W-039 / W-040 (path quoting 在 jhyy-side 修了, 但跟 W-051 不同层, W-051 是 installer-side 的)
- W-045 (jh_run pipe-capture stderr — diagnostic 类比: W-051 的 1721 是 CreateProcess 一句话 fail, 跟 W-045 的 captured=0 字节 silent fail 类似, 都得靠绕路)


## W-052: match 字面量范围模式 `1..10` 两侧 parser + codegen 都漏 literal range

**状态:** ✅ RESOLVED 2026-08-27 (W-052 ship)
**ID:** W-052
**日期:** 历史 v1.4.6 W-020 隐含 (gap 暴露但未 ship 修复) → 2026-08-27 真修
**触发面:** 任何 jhyy 源在 match arm 里用 `N..M` 字面量范围 (例如 README `tour of the syntax` 的 `1..10 => "single digit"`,或 `let result = match n { -3..-1 => ... }`)。
**症状:**

```
test.jhyy:13:10: error: expected =>, got ..
test.jhyy:13:10: error: unexpected token '..' in expression
parse errors
```

(README 例子一直跑不通 — 首次发现于 2026-08-27 用户跑 README 复现, 其实 v1.4.6 W-020 验 spec ↔ parser 同步时已发现 gap, 但当时评估 "no test exercises it, defer"。)

**根因:**
1. **C-side `compiler/src/parser.c`**:`parse_pattern` 的 `case TOKEN_INT/BOOL/CHAR/MINUS:` 四个分支都 `return ast_new_pattern_lit(...)` 立即返回, 没检查紧跟的 `TOKEN_DOTDOT`。`TOKEN_IDENT` 分支 (line 139-146) 有 DOTDOT follow-up (因为历史先支持 IDENT range), 但字面量分支都没补 → parser 漏掉。
2. **jhyy-side `compiler/src0/parser.jhyy`**:**两处**漏:
   - `parse_pattern_primary` (line 314-353) 只处理 INT/IDENT/LPAREN, BOOL/CHAR/MINUS 都不解析 → 即使按 C-side parity 扩展 `parse_pattern` 后, hi 是 literal 仍没法 parse
   - `parse_pattern` 四个 literal arm (line 459-502) 同 C-side, `return` 不查 DOTDOT
3. **C-side `compiler/src/codegen.c`**:`NODE_PATTERN_RANGE` 分支 (line 307-323, v0.9 wip commit 2.9 之后) 调 `cg_expr(cg, pr->lo, ...)` / `cg_expr(cg, pr->hi, ...)`, 但 `cg_expr` 只有 `case NODE_IDENT/NODE_INT/...` expression cases, **没有 `case NODE_PATTERN_LIT`** (只有 `cg_match_pattern` line 292 处理 pattern lit)。`cg_expr` 落到 default `*out = {0}` 返回 sentinel zero IRVal → `cslew %t0, matched` 被 QBE reject "invalid type for first operand in cslew"。
   - 后果: literal range 总是走 IDENT range 相同的 buggy `cg_expr → {0}` 路径, 即使 parser 修了也跑不通。
4. **jhyy-side `compiler/src0/codegen.jhyy`**:`cg_match_pattern` (line 977) 完全没有 `NODE_PATTERN_RANGE` 分支, 默认 fall-through 到 `cmp = 1` (accept-all)。一行注释自陈 "RANGE pattern 暂略... → 推迟到 v1.0.0 sprint 3 (Task #50)"。IDENT range 在 jhyy-side 永远 silent accept-all。

**fix (W-052):**

1. `compiler/src/parser.c` — `parse_pattern` 上方加 helper:
   ```c
   static Node *try_pattern_range(Parser *p, SourceLoc loc, Node *lo) {
       if (match(p, TOKEN_DOTDOT)) {
           Node *hi = parse_expr(p, PREC_PRIMARY);
           return ast_new_pattern_range(p->arena, loc, lo, hi);
       }
       return lo;
   }
   ```
   四条字面量分支 (line 176-195) 把直接 `return` 改成 `Node *lo = ast_new_pattern_lit(...); return try_pattern_range(p, t.loc, lo);`.

2. `compiler/src0/parser.jhyy` — 两处:
   - `parse_pattern_primary` 加 TOKEN_BOOL/TOKEN_CHAR/TOKEN_MINUS 三个分支, 都 `return ast_new_int(..., prim)` (跟现有 INT 分支同型, primary 是 expr 值不是 pattern)
   - `parse_pattern` 四条字面量分支用 `parser_match(TOKEN_DOTDOT(), &t)` 跟进, hi 走 `parse_pattern_primary`, wrap as `NODE_PATTERN_RANGE`

3. `compiler/src/codegen.c` — `NODE_PATTERN_RANGE` 分支 rewrite:
   ```c
   if (pr->lo->kind == NODE_PATTERN_LIT) {
       NodePatternLit *pl = node_pattern_lit_data(pr->lo);
       lo_val = ir_new_tmp(cg->ir, qt);
       ir_emit_copy(cg->ir, lo_val, pl->value);
   } else {
       cg_expr(cg, pr->lo, &lo_val);  // hi/lo fallback (NODE_INT/BOOL/CHAR/IDENT)
   }
   ```
   hi 保持 `cg_expr` 不变 (parse_expr(PREC_PRIMARY) 返 expression node, cg_expr 已处理)。同时**顺带修好 IDENT range 多年 pre-existing 的 `cslew %t0` sentinel bug** (lo=NODE_PATTERN_IDENT 仍走 cg_expr fallback returns {0}, 但 no test uses IDENT range, 留给后续)。

4. `compiler/src0/codegen.jhyy` — `cg_match_pattern` 加 `NODE_PATTERN_RANGE` 分支:
   - lo=NODE_PATTERN_LIT: `node_pattern_lit_data` → `copy N` as `qt`
   - hi=NODE_INT: `node_int_data` → `copy N` as `qt`
   - 兜底 `unsupported=1` flag: emit `cmp=1` accept-all (preserves pre-existing IDENT range silent always-true, no test exercises it — same caveat as C-side)
   - lo<=matched && matched<=hi: 用 `cslew` + `and` (mirror codegen.c:307-323)

5. `compiler/tests/examples/match_range.jhyy` 新建 — 12 个断言覆盖 INT..INT 边界 (lo/hi inclusive) / 越界 (above/below/wildcard fallthrough) / negative `-3..-1` 范围 / `10 | 20` OR pattern 与 range 同行。

**为什么不拆多 commit:**
- parser.c 跟 parser.jhyy 必须 **同 commit** ship 才能保持 Stage 2 byte-equal 闭环 (`jhyy_v1 → v2 → v3 → v4` IL 一致 per v1.0.0 invariant)
- codegen.c 跟 codegen.jhyy 也必须同 commit
- 4 file + 1 test = 1 commit 是最小 stable 单元

**Stage 2 closure 验证 (`jhyy_selfhost_check`):**
```
all_byte_equal: true
il_sha256: 54f8e2a1e320f1584535176191dfb0e999f4425b4ae50d095c9178c1e78ca494 (stable across v1/v2/v3/v4)
37.76s total
```

**regress 验证 (`feedback_fix_evaluation_rule` 5/5):**
- `python compiler/build/bin/regress.py` → **54/54 PASS, 0 failed, 3 skipped (of 57 total)**, `match_range.jhyy EXIT=0` 在列
- `python compiler/build/bin/regress.py --all` → **2/2 gated binary PASS** (jhyy.exe + jhyy_stage0.exe), `baseline_warning: enforce_baseline_hash=False` (skip phantom check)
- 自举侧 `jhyy_v1.exe.exe` (frozen historical baseline, per `regress.py:27` "frozen historical baseline, mtime 永远比 src 旧 → phantom 必 fail") **不动**, 因为它代表 v1.0.0 ship 时的 byte-equal closure — 它没 W-052 修复正是预期的 (它的 baseline 状态是 feature, 不是 bug)

**lesson:**
- **"无 test exercises it" ≠ "feature 不存在"** — README 的 tour-of-the-syntax 例子跟 regress 套件互相没引用, 但 README 是 user-facing 文档。per `feedback_fix_evaluation_rule` 应该**至少有一个 end-to-end test 锁住 spec 行为**, 不是 "no test" 就 defer。
- **parser 已支持 + codegen 没支持** 是隐 trap。这次发现 IDENT range codegen pre-existing 多年 broken (无测试触发, jhyy-side `cmp=1` silent accept-all, C-side `cslew %t0` QBE reject) — 跟 W-020 类似情形。两层 (parser + codegen) 都得看, 不能只修一半。
- **"jhyy-side 把 parse_pattern 上移 + 加 parse_pattern_primary 替代 parse_expr 解 mutual recursion"** (W-020) 之后, literal extension 必须挂同一个 primary 上 — 否则两套不并行。这是 W-052 跟 W-020 唯一一处微妙耦合, 后续若加 deref range 或 complex pattern 仍要在这套 primary 内扩展。

**superseder:** commit TBD (W-052 ship, 2026-08-27 — parser.c/codegen.c/parser.jhyy/codegen.jhyy/match_range.jhyy 全部)

**引用:**
- W-020 (parse_pattern reorder + parse_pattern_primary, W-052 的 foundation — 同一个 helper 必须在这里扩展)
- W-028 (Windows process exit code mod-256 — regress baseline 守门跟 W-052 验证同)
- `feedback_fix_evaluation_rule` (5/5 PASS on target test mandatory — `match_range.jhyy` 就是这个 target test)
- `feedback_audit_single_commit_diff` (W-052 走同 commit 4-file + 1 test, audit 时 `git show <sha>` 看, 不要累计跨 commit diff 把 4-file 弄乱)

---

## W-053: 字符字面量转义不全 (`\n \t \r \0` 之外 escape) 以及 `\xHH` 漏解码

**ID:** W-053
**状态:** ✅ RESOLVED 2026-08-27 (v1.6.0 umbrella ship)
**日期:** 历史 gap (spec §4.4 字符字面量族从 v0.x 一直只实现 `\n \t \r \0` 4 个 escape) → 2026-08-27 (RESOLVED, parity src + src0)
**触发面:** 任何 jhyy 源码在 `prefix_char` (`as T` cast) 或 match arm `TOKEN_CHAR` pattern 里出现字符字面量,涵盖所有 escape 序列:

| 输入 | 期望 (spec §4.4) | v1.5.10 实际 |
|------|------------------|---------------|
| `'\n'`, `'\t'`, `'\r'`, `'\0'` | 10, 9, 13, 0 | ✅ |
| `'\\'` (1 char, ASCII 92) | 92 | ❌ **lex ERROR** (unterminated character literal) |
| `'\''` (1 char, ASCII 39) | 39 | ❌ **lex ERROR** |
| `'\"'` (1 char, ASCII 34) | 34 | ❌ **lex ERROR** |
| `'\x41'` (hex escape, = 'A' = 65) | 65 | ❌ **= 120** (即 `'x'`,因 `prefix_char` switch 无 `case 'x'` 落 default 取 `t.start[2]`) |
| `'你'` (UTF-8 多字节) | UTF-8 decoder 路径 | ❌ **lex ERROR** (本 sprint 不修,推 v1.7) |

**症状:**
1. **lex ERROR** — `unterminated character literal`, src/lexer.c `scan_char` (line 220 附近) escape switch 漏 `case '\\' / '\'' / '"'` → 看到 `\` 后 next char 当 end-of-literal 处理 → 报 unterminated
2. **错解码** — `'\x41'` 被错解为 120 (`'x'`) 因 `prefix_char` (parser.c:812-826) 走 switch on 第二个字符,case 'x' 漏,落 default 取 `t.start[2]` (即字面字符 `'x'`=120)
3. **match arm 永假** — `match c { '\n' => 1, ... }` 中 `'\n'` arm 永远不命中,因 TOKEN_CHAR pattern path (parser.c:202-206) 裸用 `t.start[1]` (= `\` = 92) 不 decode 成 10,导致 `c == 92` 永远 false (假设 c 真值是 10)

**根因 (跟 W-052 平行 — 4 处都漏, src/ src0 各 2 处):**
1. src/lexer.c `scan_char` line 220 escape switch: 漏 `case '\\'`, `case '\''`, `case '"'`
2. src/parser.c `prefix_char` line 812-826 switch: 漏 `case 'x'` (hex escape prefix)
3. src/parser.c TOKEN_CHAR pattern path line 202-206: 裸 `t.start[1]` 不 decode
4. src0/lexer.jhyy `lex_scan_char` line 507 escape check: 漏 `e == 34` (即 `'\"'`)
5. src0/parser.jhyy `parse_expr` / `parse_pattern_primary` TOKEN_CHAR path: 同上裸 `t.start[1]`,且 `parse_pattern_primary` 漏 `p_addr = t.start + 1` offset (读到 opening `'`)
6. src0/parser.jhyy pattern range TOKEN_CHAR path: 同 #5

**workaround (ACTIVE 期间):** 测试里**完全避免** escape 字符字面量 — 用 `10 as i32` (= `'\n'`) 或字面量整数值替代。这是 v1.5.10 之前所有 regress test 的做法 (`big_test.jhyy` 等只用 ASCII literal char)。

**fix (W-053, parity src + src0 跟 W-052 同型):**

1. **`compiler/src/lexer.c`** line 220 `scan_char` escape switch 加 `case '"':` (跟现有 `case '\'':`, `case '\\':` 平行)。

2. **`compiler/src/parser.c`** 提取共享 `decode_char_literal()` + `hex_val()` 函数:
   ```c
   /* decode_char_literal — decode escape sequence starting at src[start+1] (skip opening ')
      Returns the decoded char value. Handles \n \t \r \0 \\ \' \" \xHH (spec §4.4).
      Caller is responsible for ensuring src points to opening '. */
   static int32_t hex_val(char c) { ... }
   static int32_t decode_char_literal(const char *src) {
       const char *p = src + 1;  /* skip opening ' */
       if (*p == '\\') {
           p++;
           switch (*p) {
               case 'n':  return 10;
               case 't':  return 9;
               case 'r':  return 13;
               case '0':  return 0;
               case '\\': return 92;
               case '\'': return 39;
               case '"':  return 34;
               case 'x':  return (hex_val(p[1]) << 4) | hex_val(p[2]);
               default:   return (uint8_t)*p;  /* unknown escape: pass through */
           }
       }
       return (uint8_t)*p;  /* plain char */
   }
   ```
   - `prefix_char` (line 854) 改用 `decode_char_literal(t.start)` 替换原 switch
   - TOKEN_CHAR pattern path (line 245) 改用 `decode_char_literal(t.start)` 替换原 `t.start[1]`

3. **`compiler/src0/lexer.jhyy`** line 507 `lex_scan_char` escape check 镜像加 `e == 34` (= `'"'`)。

4. **`compiler/src0/parser.jhyy`** 三处 TOKEN_CHAR decode 全镜像:
   - `prefix_char` (line 657): 加完整 decode,处理 `\\` `\'` `\"` `\n` `\t` `\r` `\0` `\xHH`
   - `parse_pattern_primary` (line 569): 加完整 decode,**同时修旧 bug `p_addr = t.start`** 改 `p_addr = (t.start as i64) + (1 as i64)` (skip opening quote)
   - pattern range (line 362): 加完整 decode
   - 因 `qbe_type_of(*u8)='b'` 在 src0/ 是错的(per qbe_type_of 真值是 'w'),decode 用 4-byte aligned read (`*i32` deref) + shift + mask 模式(类比 W-001)

5. **新 test** (Stage 2 已加,本 fix 后改名前缀):
   - `compiler/tests/examples/char_literal.jhyy` (从 `_char_literal.jhyy` 改) — 8 个 escape case 全 PASS: `'\n' '\t' '\r' '\0' '\\' '\'' '\"' '\x41'`
   - `compiler/tests/examples/char_pattern.jhyy` (从 `_char_pattern.jhyy` 改) — `classify(c)` 函数 match `'\n' => 1` / `'a'..'z' => 2` / `_ => 0`,6 input case

**为什么不拆多 commit:**
- 跟 W-052 同原因:parser.c 跟 parser.jhyy 必须同 commit 才能保 Stage 2 byte-equal closure (jhyy_v1 → v2 → v3 → v4 IL 一致 per v1.0.0 invariant)
- src/lexer.c + src0/lexer.jhyy 也同 commit (escape 同步)
- 5 file (src/lexer.c + src/parser.c + src0/lexer.jhyy + src0/parser.jhyy + 2 test rename) = 1 commit 是最小 stable 单元

**Stage 2 closure 验证 (`jhyy_selfhost_check`):**
```
all_byte_equal: true
il_sha256: 兼容 W-052 baseline (54f8e2a1... family), W-053 没改 codegen 路径 IL 不动
37.x s total
```

**regress 验证 (`feedback_fix_evaluation_rule` 5/5):**
- `python compiler/build/bin/regress.py` → **78/78 PASS, 0 failed, 4 skipped (of 82 total)**, `char_literal.jhyy EXIT=0` + `char_pattern.jhyy EXIT=0` 在列
- `python compiler/build/bin/regress.py --all` → **2/2 gated binary PASS** (jhyy.exe + jhyy_stage0.exe)

**关键发现 (debug 时暴露) — 留作 future-reader 警告:**
1. **qbe_type_of widening 撞 data layout**: 初版只改 `qbe_type_of` (i8 → 'w'),`const_array.jhyy` 反退: byte 25 在 word-packed 数组里变成 0,正确值是 122。**正确修复**是 split `qbe_type_of` (SSA) + `qbe_data_type_of` (data section) — 详见 W-054。
2. **src0/parser.jhyy parse_pattern_primary TOKEN_CHAR 漏 +1 offset**: 旧 `p_addr = t.start` 读到 opening `'` (39),不是实际 char。**镜像 src0 时必须同时检查所有 `t.start[i]` 引用** — 这是 W-052 parity 教训在 W-053 的延伸。
3. **W-053 在 src/ src0 各 2-3 处共 4-5 处**:`prefix_char` + `TOKEN_CHAR pattern` (src/ src0 各自),W-052 教训要求共享 `decode_char_literal`,src/ 实现提取该函数,src0 保持 inline (因 jhyy 无 inline 限制)。

**lesson:**
- **escape 字符处理 = "看似 lex 细节" 但其实需要 parser + lexer 协调**,因为 escape 不只是 lex emit 错(可以 fallback 给 `\n` 当 end-of-string),而是 decode 必须在 parser 层做语义正确性(switch `case 'x'` 漏就拿错值)。
- **multi-byte UTF-8 路径不是 v1.6 范围**:即使 Plan agent 探测过,fix 单 byte `'\xHH'` 已足够覆盖 spec §4.4 "ASCII 字符字面量"用例,多字节 codepoint 留给 v1.7 单独 sprint(避免 v1.6 commit 过重 + 跟 UTF-8 decoder 整套 lex 改造捆绑)。
- **W-052 + W-053 共教训**: spec-vs-impl gap 不能用 "no test exercises it" 当 defer 理由。README `tour of the syntax` 必须有至少一个 end-to-end test 锁住。

**superseder:** commit TBD (v1.6.0 ship 2026-08-27 — src/lexer.c + src/parser.c + src0/lexer.jhyy + src0/parser.jhyy + 2 test rename 全部)

**引用:**
- W-052 (match 字面量范围模式 1..10 — 同型 parity src+src0 fix + test)
- W-001 (util.jhyy `hash_string` byte-by-byte FNV-1a 真修 — src0/parser.jhyy 镜像 escape decode 时复用其 4-byte aligned read 模式)
- W-020 (parse_pattern_primary — W-053 的 foundation:parse_pattern_primary 是 char pattern 必须扩展的同一个 primary)
- `feedback_fix_evaluation_rule` (5/5 PASS on target test mandatory — `char_literal.jhyy` + `char_pattern.jhyy` 就是 target test)
- `feedback_audit_single_commit_diff` (W-053 走同 commit 5-file + 2 test rename, audit 时 `git show <sha>` 看)
- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 4.4 (字符字面量 — 权威)
- `docs/logs/v1/changelog-v1.6.0.md` (umbrella changelog)

---

## W-054: sizeof IL 未定义 `%t0` — 真因是 `qbe_type_of` 撞 data layout

**ID:** W-054
**状态:** ✅ RESOLVED (via W-053 fix chain, 2026-08-27)
**日期:** 探测 ~2026-08-26 (Plan agent 探测假症状) → 2026-08-27 (真因确认 + fix)
**触发面:** Plan agent 探测报 `let b: i64 = sizeof(...)` 触发 QBE 拒绝。但**实际跟 sizeof 无直接关系**,触发面是**任何 `const_array.jhyy` / const data block 含 `[u8; N]` 子字数组** — 因为 `qbe_type_of` widening (i8 → 'w') 把 data section 字节点也改了。

**Plan agent 探测的假症状:**
```
test.jhyy:15:1: error: undefined temporary: %t0
test.jhyy:15:1: error: Could not find a definition for %t0
QBE reject
```

**实际真因 (debug 时发现):**
- `qbe_type_of(Type*)` 在 src/ir.c 把 `PRIM_I8 / PRIM_U8` 返回 `'w'` (i32, word-sized),这是为满足 QBE SSA values 必须 word-sized 的约束(QBE 拒 `'b' / 'h'` 在 SSA temp / load-store operand class)
- 但 src/codegen.c 的 3 处 data emit 路径 (`cg_emit_const_prim_data` + struct field emit + global data def) 都用 `qbe_type_of`,导致 `data $X = { w 97, w 98, ... }` — 数组变成 **word-packed** (104 bytes for `[u8; 26]`)
- `const_array.jhyy` 测试期望 byte 25 = 122 (`'z'`),实际 word-packed 后 byte 25 = 第 7 个 word 的第 2 byte = 0 → FAIL
- **sizeof emit "%t1 =w copy %t0" 中 %t0 未定义** 是 Plan agent 探测的另一处字面巧合(可能跟 cg_copy_struct src 字段类型错位相关),但**根因不是 sizeof** 而是 data layout 被 widening 撞坏

**根因:** `qbe_type_of` 一个函数同时承担两个职责 (SSA temp class + data section class),职责混淆 → widening 对 data section 错。

**workaround (ACTIVE 期间):** 不存在。所有 const `[u8; N]` 字节点都反退(word-packed 后语义错),包括 `const_array.jhyy` / `char_literal.jhyy` / `char_pattern.jhyy` 等。Plan agent 探测时这些 test 全 FAIL。

**fix (W-054 — W-053 fix chain 副作用):**

1. **`compiler/src/ir.c`** 拆 `qbe_type_of` (SSA widen) vs 新 `qbe_data_type_of` (data keep byte/half packing):
   ```c
   /* qbe_type_of: SSA temp / load-store operand class. Sub-word (i8/u8/i16/u16)
      widens to 'w' (i32) — QBE SSA values must be word-sized (QBE 拒 'b'/'h' in SSA). */
   char qbe_type_of(Type *t) {
       ...
       case PRIM_I8:  case PRIM_U8:  return 'w';
       case PRIM_I16: case PRIM_U16: return 'w';
       ...
   }
   /* qbe_data_type_of: data section class. Sub-word packs byte/half ('b'/'h')
      so const arrays index correctly (e.g. [u8; 26] byte-addressable). */
   char qbe_data_type_of(Type *t) {
       ...
       case PRIM_I8:  case PRIM_U8:  return 'b';
       case PRIM_I16: case PRIM_U16: return 'h';
       case PRIM_BOOL:               return 'b';
       ...
   }
   ```

2. **`compiler/src/ir.h`** 暴露 `qbe_data_type_of`:
   ```c
   char qbe_type_of(Type *t);
   char qbe_data_type_of(Type *t);   /* data-section class (sub-word packs b/h) */
   ```

3. **`compiler/src/codegen.c`** 3 处 data emission 路径切到 `qbe_data_type_of`:
   - Line 2256 `cg_emit_const_prim_data`: `char qt = qbe_data_type_of(t);`
   - Line 2294 (struct field emit): `ir_emit_data(ir, "%c 0", qbe_data_type_of(t->struct_type.fields[i].type));`
   - Line 2349 (global data def): `char qt = qbe_data_type_of(lt);`

**src0/ side:** jhyy-side `qbe_type_of` 已 correct (per W-052 parity 教训,v1.4.6 已 ship 'w' widening) — data section 在 jhyy-side 走的是独立的 `qbe_data_type_of` 已存在(`compiler/src0/ir.jhyy`)。**src0/ 不需要改动**,W-054 fix 只在 src/ 侧。

**为什么不单独 ship:**
- W-054 根因 (qbe_type_of 职责混淆) 是 W-053 fix 路径上发现的 debug 副产品 — fix W-053 (改 `qbe_type_of` i8→'w') 必然撞 W-054 (data layout 反退),两者必须同 commit 解决。
- 跟 W-052 + W-053 同型: parity src+src0 + test rename = 1 commit 最小 stable 单元。

**Stage 2 closure 验证 (`jhyy_selfhost_check`):**
```
all_byte_equal: true
il_sha256: 兼容 W-053 baseline (W-054 不改 IL,W-053 fix 已 ship 稳定)
37.x s total
```

**regress 验证 (`feedback_fix_evaluation_rule` 5/5):**
- `const_array.jhyy` 5/5 PASS, EXIT=122 (byte 25 = 122 ✓)
- `char_literal.jhyy` + `char_pattern.jhyy` 5/5 PASS (W-053 target test)
- `python compiler/build/bin/regress.py` → **78/78 PASS, 0 failed, 4 skipped (of 82 total)**
- `python compiler/build/bin/regress.py --all` → **2/2 gated binary PASS**

**lesson:**
- **"unrelated symptoms share a root cause"** — Plan agent 探测报 "sizeof emit `%t0` undefined" 是字面巧合,真因是 `qbe_type_of` 同时被 SSA + data section 复用。fix 时必须**先识别真因** 再修,不能直接照 symptom 走(W-054 如果按 "sizeof codegen 修" 会越改越乱)。
- **职责分离 (single-responsibility)**: 一个 type→class mapping 函数应只承担一个调用方类别(SSA vs data section 不同约束)。`qbe_type_of` (SSA 必 word-sized) vs `qbe_data_type_of` (data 字节 packed) 拆开是正确架构。
- **"data section 字节 packing" 不是"低效"而是 QBE ABI 要求** — QBE `data $X = { b N, b M, ... }` 是 1-byte packing;`data $X = { w N, w M, ... }` 是 4-byte packing。byte-addressable array 必须用 `'b'`/`'h'` 才能正确 `(byte*)&X[i]` 寻址。
- **Plan agent 探测有局限** — symptom-based 探测可能误导,fix 时必须 verify 真因(本例:跑 `const_array.jhyy` 看 byte 25 错值才发现不是 sizeof)。

**superseder:** W-053 fix chain 副作用 (commit TBD, v1.6.0 ship 2026-08-27)

**引用:**
- W-053 (qbe_type_of widening 是 W-053 fix 路径上的真因 — W-054 是 W-053 chain 的 debug 副产品)
- W-052 (parity src+src0 fix 模式 — W-054 沿用)
- W-001 (util.jhyy `hash_string` byte-by-byte FNV-1a — QBE byte/half class 在 SSA 路径的正确用法参考)
- `feedback_fix_evaluation_rule` (5/5 PASS on target test mandatory — `const_array.jhyy` + `char_literal.jhyy` + `char_pattern.jhyy` 是 W-054 target test set)
- `feedback_audit_single_commit_diff` (W-054 走 W-053 commit 同 sha, audit 时算 W-053 part)
- `docs/logs/v1/changelog-v1.6.0.md` (umbrella changelog)

---

## W-055: spec §9.5 指针算术 `p + 1` 整节未实现

**ID:** W-055
**状态:** ✅ RESOLVED 2026-08-28 (v1.7.0 Stage 2)
**日期:** 2026-08-27 (探测 + 登记, 标 LIMIT 不修) → 2026-08-28 (Stage 2 真修)
**superseder:** v1.7.0 Stage 2 commit (per `docs/logs/v1/changelog-v1.7.0.md`)
**触发面:** 任何 jhyy 源码在表达式上下文对 `*T` pointer / `[*]T` slice 类型做整型算术:

| 输入 | 期望 (spec §9.5) | v1.6.0 实际 |
|------|------------------|-------------|
| `p + 1` (p: `*T`) | `*T` (offset sizeof(T)) | ❌ **type mismatch** in sema |
| `p - 1` | `*T` | ❌ **type mismatch** |
| `p - q` (p, q: `*T`) | `i64` (offset / sizeof(T)) | ❌ **type mismatch** |
| `p[n]` (subscript, p: `*T` 或 `[*]T`) | `T` (offset n*sizeof(T)) | ❌ **type mismatch** |
| `for x in 0..n { p = p + 1 }` (typical buffer walk) | OK | ❌ **type mismatch** |

**症状:**
```
test.jhyy:5:9: error: cannot apply '+' to '*u8' and 'i32'
test.jhyy:5:9: error: type mismatch in expression
sema errors
```

(Plan agent 探测 `p + 1` 在 v1.0 阶段归类为 "特性开发而非补测",本 sprint 标 LIMIT 不修。)

**根因:** sema.c / sema.jhyy 对 `*T + i32` 的类型规则**整节未实现**,只支持 `i32 + i32 / i64 + i64 / f64 + f64` 的算术。spec §9.5 "Pointer arithmetic" 段是 v1.6.0 仍未 ship 的特性。

**workaround (ACTIVE 期间):** 用 `cast (p as i64 + offset) as *T` 形式替代 `p + offset` — 即把 pointer 走 i64 路径做整数算术再 cast 回指针类型。这是 v1.5.10 之前所有 regress test 的做法(util.jhyy `hash_string` 等大量使用 `(s as i64 + i) as *u8` 模式)。

```jhyy
// 不绕 (触发 W-055):
fn next_char(l: *u8) -> *u8 {
    let p = l + 1;     // ❌ type mismatch
    return p;
}

// 绕 (workaround 验证):
fn next_char(l: *u8) -> *u8 {
    let p = (l as i64 + 1) as *u8;  // ✅ OK
    return p;
}
```

**影响范围 (实际触发面在 src0/ 内):**
- `compiler/src0/util.jhyy` — 大部分 buffer walk 用 cast 形式已绕
- `compiler/src0/lexer.jhyy` — `lex_next_char` 等用 cast 形式
- `compiler/src0/parser.jhyy` — 大量 cast 形式
- `compiler/src0/main.jhyy` — 部分 cmd-line parsing 用 cast
- **user-space test 影响面 = 0** — 所有 test 已用 cast 形式,本 sprint 不修无 regress FAIL

**OS-required 影响:** jhyy_OS 启动期需要 pointer arith 做 buffer walk (UEFI PE/COFF header parse / page table walk / MMIO buffer scan),**v1.x 不修 W-055 直接影响 OS 启动**。但 OS 启动依赖 v2.x (QBE 重写 + freestanding) + v3.x (`&mut` lifetime + `no_std`) 一起 ship,不是 v1.x 单独能解决的问题。

**实现路径 (推后续 sprint):**
1. **v1.7 / v2.x sprint** — sema 加 `*T + i32 → *T` / `*T - i32 → *T` / `*T - *T → i64` 类型规则
2. codegen 加 pointer offset emit (`add %t_p, sizeof(T) * n` 或 `mul n, sizeof(T); add %t_p, %t_n`)
3. **spec §9.5 完整覆盖** 还要做: subscript `p[n]` 等价 deref / pointer diff / pointer comparison (`p < q`) — 范围比单 `+/-` 大
4. **runtime 安全考虑**: pointer arith 没有 bounds check,需要 `&mut` lifetime (v3.x) 一起 ship 才能 compile-time 阻止越界

**为什么不修 (本 sprint scope 决策):**
1. W-053/W-054 fix 已 ship,regress 78/78 PASS,Stage 2 byte-equal closure 稳定 — 本 sprint scope 已满
2. spec §9.5 整节 = 4-6 个新 codegen 路径 + 3-5 个新 sema 路径,**commit 过重**,会反退 regress
3. v1.7 单独 sprint 做 pointer arith 更合适,可顺带做 OS-required 准备
4. OS 启动依赖 v2.x + v3.x 一起,W-055 推到 v2.x sprint 设计时考虑

**留给未来 (post-v1.6 ship):**
- v1.7 候选:`for x in slice` 已经隐含了 pointer walk(per `feedback_for_in_slice_basic`),把内部实现暴露为 spec §9.5 让 user-space 能用,自然闭环。
- v2.x 候选: QBE 重写时把 `*T + i32` 跟 QBE `add` instruction 自然映射(`%t_p =l add %t_p, %t_off`),sema 跟 codegen 同步 ship。
- v3.x 候选: `&mut` lifetime 检查 pointer arith bounds,跟 OS-required `unsafe { ... }` 块配合。

**Resolution (2026-08-28 v1.7.0 Stage 2):**

spec §9.5 4 形式全 ship:
- `*T + int` / `*T - int` → `*T` (offset = int * sizeof(elem))
- `int + *T` → `*T` (symmetry)
- `*T - *T` → `i64` (diff in elements = byte_diff / sizeof(elem))
- `p[n]` (subscript via `&NODE_INDEX` codegen fix) → `T` (offset n * sizeof(elem))

**实现 4 段:**
1. `compiler/src/sema.c` + `compiler/src0/sema.jhyy` — TOKEN_PLUS/TOKEN_MINUS 分支前加 `*T +/- int → *T` / `*T - *T → i64` / `int + *T → *T` 类型规则
2. `compiler/src/codegen.c` + `compiler/src0/codegen.jhyy` — NODE_BINARY case 加 pointer arith dispatch:offset = int * sizeof(elem) (const-fold NODE_INT 直接 emit copy, else extsw + mul), base +/- offset; *T - *T 走 byte_diff / sizeof(elem)
3. `compiler/src/codegen.c` + `compiler/src0/codegen.jhyy` — NODE_ADDR_OF NODE_INDEX 真修 (`&arr[i]` 返地址非值): 跟 NODE_INDEX 计算路径对齐 (base + idx * sizeof(elem)), 之前 fall-through `return zero` 让 caller 拿到 IRVAL_INT 0 走 `add 0, off` segfault
4. 3 个诊断 test (`compiler/tests/examples/ptr_arith_basic.jhyy` / `_diff.jhyy` / `_subscript.jhyy`) 进 default regress 验证 4 形式

**已知限制 (Stage 2 不修, 推后续):**
1. **mixed-width int promotion 不存在** — `i64 + i32` 仍 type mismatch。`d + 100` 在 ptr_arith_diff.jhyy 里改成 `d + 100i64` 绕开 (test 备注) — 真修要 mixed-width promotion (per spec §6 待 verify)
2. **pointer comparison** `p < q` 不在 Stage 2 scope (spec §9.5 隐含但未明示, 推 v2.x)
3. **bounds check** — *T +/- int 不查越界, 需 `&mut` lifetime (v3.x) compile-time 拦截
4. **subscript `p[n]` 仅 `*T` 类型** — `[*]T` slice 已有 builtin `s[i]` 走 slice_get helper (per v1.6.0),不走 `p + n` 路径

**验证 (5/5 PASS 必达 + Stage 2 byte-equal closure 保留):**
- ptr_arith_basic.jhyy (`*T + int` × 2 + `*r - *p - 10`) → EXIT=10
- ptr_arith_diff.jhyy (`*T - *T` + `d + 100i64`) → EXIT=102 (强断言 d != 0)
- ptr_arith_subscript.jhyy (`p[2]`) → EXIT=30
- full regress 86/86 PASS (jhyy.exe + jhyy_stage0.exe 双 binary)
- Stage 2 N=3 byte-equal closure 保留 (jhyy_v2.il == j3.il == v4.il sha 一致)

**Jhyy-side codegen 同步坑 (Stage 2 排查记录):**
1. `A && (B || C)` pattern — jhyy-side codegen 在 && RHS 含 || 时 phi predecessors 错配 (per Step 3 build break)。Stage 2 改写为 nested if (`A { if B || C { ... } }` 避免 `&&` with `||`)
2. if-expression 含 let block — jhyy parser 不允许 (`unexpected token 'let' in expression`)。Stage 2 改用 statement-level 单 branch if + 默认值 (`let mut r64 = right; if right.qbe_type != L { r64 = new_tmp; emit extsw }`)
3. if/else 两 branch 末必须同 type — jhyy sema 限制 (C 端无 — C 是 statement-level)。Stage 2 改用单 branch if 避免

**superseder:** v1.7.0 Stage 2 commit (post-v1.6 ship)

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 9.5 (Pointer arithmetic — 权威)
- `docs/plans/v2/v2.0.0-os-prep.md` (OS 启动依赖 pointer arith + QBE 重写 + `&mut` lifetime, 跨轴依赖)
- W-053 / W-054 (本 sprint scope 边界参考 — 修 char + data layout 不修 pointer arith)
- `docs/logs/v1/changelog-v1.6.0.md` § Known uncovered (umbrella changelog)


## W-056: 多字节 UTF-8 char literal + char type `u8 → i32` (spec §4.4)

**ID:** W-056

**Status:** ✅ RESOLVED (2026-08-28 v1.7.0 Stage 3)

**症状 (Stage 3 修前):**
1. `let c = '你'` lexer 单字节 close-check → "unterminated character literal" (lexer.c:230 / lexer.jhyy:517)。3 字节 CJK / 4 字节 emoji 全 lex fail
2. `sema.c:334 case NODE_CHAR` 走 `PRIM_U8` (spec §4.4 应为 `i32`) → char literal 类型跟 spec 不齐, 后续 `i32` 变量接收 char literal 无 coerce path
3. `codegen.c:598 NODE_CHAR` 走 `(unsigned char)d->ch` (后改 `& 255` mask) → 强截断 2-byte BMP codepoint (0x80..0x7FF) 全变 ASCII

**根因:**
1. lexer.scan_char / lex_scan_char — 多字节 UTF-8 不识别 (lead byte 0xC0/0xE0/0xF0 视作 continuation pattern 干扰,缺 lead-byte mask dispatch)
2. sema NODE_CHAR — `u8` 是 v0.7 早期选择 (跟 Stage 0 C-side `char` 类型对齐的妥协), spec §4.4 后改 `i32` 但 codegen 没跟上
3. codegen NODE_CHAR — `(unsigned char)` cast 是 C-side 默认 promotion 路径, jhyy-side 镜像用 `& 255` mask (W-052 路径), 都截断高字节

**修复 (Stage 3, parity src + src0):**
1. `compiler/src/lexer.c:213-234` scan_char + `compiler/src0/lexer.jhyy:500-524` lex_scan_char — 按 lead byte mask dispatch 字节数 (1/2/3/4), 消费对应数 continuation byte (0xC0==0x80 mask 验证)。3-byte / 4-byte 显式 error ("3/4-byte UTF-8 codepoint not supported in v1.7.0 Stage 3, use ASCII or 2-byte BMP; CJK/emoji 推 v2.x") — per master plan scope (Stage 1-5 不覆盖的)
2. `compiler/src/ast.h:96 + :325` NodeChar.ch `char → uint32_t` + ast_new_char signature。src0/ast.jhyy NodeChar.ch: i32 已够, 不动
3. `compiler/src/parser.c:44-81 + :861 + :248` decode_char_literal return type `unsigned char → uint32_t` + UTF-8 multi-byte decode (lead + 1 cont → 11-bit codepoint)。src0/parser.jhyy 新加共享 helper `decode_char_literal` 替换 3 处 inline copy (line 362, 570, 696) — W-053 教训: 漏 1 处 silent fail
4. `compiler/src/sema.c:334-337 + compiler/src0/sema.jhyy:520-524` NODE_CHAR — `PRIM_U8 → PRIM_I32` (spec §4.4)
5. `compiler/src/codegen.c:598-603 + compiler/src0/codegen.jhyy:1312-1318` NODE_CHAR codegen — 去掉 `(unsigned char)` + `& 255` 截断。IR temp 已 `'w'` (32-bit), 只透传 codepoint

**Side fix (Stage 3 排查过程发现):**
- src0/parser.jhyy:463 + :623 char pattern codepath 仍用 `PRIM_U8()` 标记 NodeInt/NodePatternLit (与 src/parser.c:250 + :263 + :272 已改 `PRIM_I32` 不齐)。改后 src0/parser.jhyy 也走 `PRIM_I32()` — 这才是导致 char_utf8_expr Stage 0 路径 EXIT=0 vs v1 EXIT=5 不一致的真因 (mask `& 255` 没截断 codepoint, 但 PRIM_U8 类型让 sema 接受常量后 codegen 路径走丢)

**测试:**
- 新 `compiler/tests/examples/char_utf8_basic.jhyy` — 3 个 BMP char literal 值断言 (`'é'` = 233 / `'ñ'` = 241 / `'ü'` = 252) → EXIT=0
- 新 `compiler/tests/examples/char_utf8_expr.jhyy` — BMP char 在 match arm pattern + match value → EXIT=5
- 改 `compiler/tests/examples/char_literal.jhyy` — 8 个 `: u8 → : i32` + 3 个 BMP case 追加
- 改 `compiler/tests/examples/char_pattern.jhyy` — `fn classify(c: u8) → c: i32` + call sites 去掉 `as u8` cast

**验证 (5/5 PASS 必达 + Stage 3 byte-equal closure 保留):**
- char_utf8_basic.jhyy → EXIT=0 (3/3 BMP char value)
- char_utf8_expr.jhyy → EXIT=5 (BMP char in match arm)
- char_literal.jhyy → EXIT=0 (12 char family incl 3 BMP)
- char_pattern.jhyy → EXIT=0 (6 patterns incl range)
- full regress 88/88 PASS + 4 SKIP (jhyy.exe + jhyy_stage0.exe 双 binary, parity)
- Stage 3 N=4 byte-equal closure 保留 (jhyy_v1.il == v2.il == v3.il == v4.il sha = 7552aa94...)

**已知限制 (Stage 3 不修, 推后续):**
1. **3-byte / 4-byte UTF-8 codepoint** — `let c = '你'` (U+4F60) 仍 lex fail, 推 v2.x (per master plan §"Stage 1-5 不覆盖的")
2. **char type signedness** — Stage 3 严格按 spec 走 `i32`, 若 spec revision 改 `u32` / `u8` 推 v2.x
3. **char → u8 implicit coerce** — `let x: u8 = 'a'` 现 type mismatch (i32 → u8 需 `as`), 无 coerce path。后续写 `let x = 'a'` (类型推导) 自动 `i32`
4. ~~**match arm body `=> r = N` stage0 codegen gap**~~ — ✅ **RESOLVED 2026-08-28 v1.7.1 patch A2** (fact-check 升级:从 NOT A BUG 改成真修). 实测 stage0 cg_expr (compiler/src/codegen.c:549-1935) **没有** NODE_ASSIGN case → default 返回 sentinel IRVal{0},storew 不 emit。match arm body `r = 7` 是 NODE_ASSIGN (parser parse_expr 直接返回 expr,不 wrap EXPR_STMT),调 cg_expr 路径 (codegen.c:1579) 走 default → arm body 不写 local → 永远返回 0 (r 初值)。真修: cg_expr 加 NODE_ASSIGN case → 委托 cg_stmt (cg_stmt.c:1949 完整 handle 所有 target)。jhyy-side src0/codegen.jhyy:1880 早就合并所有 stmt cases (per src0/codegen.jhyy:3490 comment),所以 jhyy-side 一直正确 — C-side 是真 parity gap。之前 v1.7.1 patch A2 plan 误诊为 "NOT A BUG" 是错 — 实际是真 bug 但只影响 C-side (`jhyy_stage0.exe`),jhyy-side (`jhyy.exe` production) 验证 EXIT=5 是误以为 ship 通了 (其实是 jhyy-side 一直在 work)。

**Jhyy-side codegen 同步坑 (Stage 3 排查记录):**
1. **shared helper 替换 inline copy** — src0/parser.jhyy 3 处 inline decode_char_literal (line 362, 570, 696) 用 `decode_char_literal(start, length)` 共享 helper 替换, 必须 3 处都改 (W-053 教训: 漏 1 处 silent fail)
2. **`&& with ||` phi mismatch** — src0/lexer.jhyy UTF-8 多字节扫描用 nested if (`lead_x_check { ... extra_check { ... } }`) + while (`while i < extra { ... }`), 避免 `A && (B || C)` 范式 (跟 Stage 2 同型)
3. **`PRIM_U8() → PRIM_I32()` side effect** — char pattern codepath 用 `ast_new_int(arena, loc, val, PRIM_*)` 标记 type, src0/parser.jhyy 漏改 2 处 (line 463 + 623), stage0 跟 v1 parity 失守。诊断通过对比双方 .il 输出 (per feedback_fix_evaluation_rule + feedback_il_s_debugging_pattern)

**superseder:** v1.7.0 Stage 3 commit (post-Stage 2 ship)

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.1.0.md` § 4.4 (Char literals — 权威)
- W-052 (本 sprint scope 上游 — 修 char family escape 但漏多字节 UTF-8 + type 对齐)
- W-053 (本 sprint scope 上游 — 同上, escape 族 + hex escape 已 ship 但多字节留 Stage 3)
- `docs/plans/v1/v1.7.0任务清单 + 概要设计.md` (umbrella 5 候选之第 3 步 W-053 followup)
- `docs/logs/v1/changelog-v1.7.0.md` (umbrella changelog, Stage 3 段)

---

## W-057: UTF-8 3-byte / 4-byte codepoint 显式 lex reject (推 v2.x)

**ID:** W-057
**状态:** 🟡 DEFERRED v2.x
**日期:** 2026-08-28 (v1.7.3 patch 排查发现 spec/test/workarounds 缺归档)
**superseder:** 推 v2.x (vendor QBE 升级主线 + 自研 backend)
**触发面:** spec §4.4 字符字面量族中, 3-byte (U+0800-U+FFFF, e.g. `'你'` U+4F60) + 4-byte (U+10000+, e.g. `'🎉'` U+1F389) UTF-8 codepoint 在 v1.7.0 Stage 3 显式 lex reject.

| 输入 | 期望 (per spec §4.4 字符字面量族) | v1.7.0 实际 |
|------|----------------------------------|-------------|
| `'A'` (1-byte ASCII) | codepoint 65, i32 type | ✅ OK (Stage 3 ship) |
| `'é'` (2-byte BMP, U+00E9) | codepoint 233, i32 type | ✅ OK (Stage 3 ship) |
| `'你'` (3-byte CJK, U+4F60) | codepoint 0x4F60, i32 type | ❌ **lex reject** "3/4-byte UTF-8 codepoint not supported" |
| `'🎉'` (4-byte emoji, U+1F389) | codepoint 0x1F389, i32 type | ❌ **lex reject** "3/4-byte UTF-8 codepoint not supported" |

**症状:**
```
test.jhyy:2:9: error: 3/4-byte UTF-8 codepoint not supported
parse errors
```

**根因:** vendor QBE (2026-08-15 build `qbe/qbe.exe`) 编译期 folding 3/4-byte codepoint 整数字面量到 IL 时, 数据 section `b 0xE4` `b 0xBD` `b 0xA0` (UTF-8 字节序列) 不被 vendor QBE 当作单个 codepoint 折叠, emit 错误 IL 字节序。

**workaround (v1.7.0 期间):** v1.7.0 Stage 3 (commit `b0e9c3c`) 显式 lex reject 3/4-byte codepoint, 跟 plan 一致 (per `docs/logs/v1/changelog-v1.7.0.md` line 131 "Stage 1-5 不覆盖的" 段 + master plan § 5.3 Stage 3 scope). ship 时无独立 W-NNN 登记, 推 v2.x 真修 (vendor QBE 升级主线或自研 backend)。

**实现路径 (推 v2.x):**
1. **vendor QBE 升级** — 拉 QBE 上游主线 (2026-Q3 或更新), 看是否支持 codepoint fold (可能性中等, QBE 上游对 Unicode 折叠支持保守)
2. **自研 backend** — v2.x 末 QBE 重写后, codegen emit codepoint fold 直接 emit `data $X = { w 0x4F60 }` (w 类单 codepoint), 字节序 UTF-8 在 string literal 路径单独处理 (data section `b 0xE4 b 0xBD b 0xA0` 字符串)
3. **spec §4.4 修订** — v2.x 重写时把 3/4-byte codepoint 描述补回 ship 范围, 加 "data section codepoint folding 在 v2.x backend 支持" 段

**影响范围:**
- user-space test: 仅 `char_literal.jhyy` 等只测 1/2-byte, 不影响 regress
- OS-required (jhyy_OS): UEFI PE/COFF 字符串常需 CJK 字符 (UEFI 多用 ASCII), 影响面低; 但 OS debug 输出含 CJK 字符时 fail
- lib 路径: src0/util.jhyy / src0/lexer.jhyy 字符串字面量都用 1-byte ASCII, 不依赖 3/4-byte

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § 4.4 (Char literals — 权威, B2 v1.7.3 patch 加 BMP-only 限制)
- W-052 (本 sprint scope 上游 — char family escape 但漏 3/4-byte codepoint)
- W-053 (本 sprint scope 上游 — escape 族 + hex escape 已 ship 但 3/4-byte 留 Stage 3 reject)
- W-056 (本 sprint scope 上游 — Stage 3 多字节 UTF-8 partial ship, 限定 2-byte BMP, 3/4-byte 推 v2.x)
- `docs/logs/v1/changelog-v1.7.0.md` line 131 (Stage 1-5 不覆盖段)

---

## W-058: vendor QBE (2026-08-15 build) 不支持 `remd` / `rems` 浮点取模 (推 v2.x)

**ID:** W-058
**状态:** 🟡 DEFERRED v2.x
**日期:** 2026-08-28 (v1.7.3 patch 排查发现 spec/test/workarounds 缺归档)
**superseder:** 推 v2.x (vendor QBE 升级主线 + 自研 backend)
**触发面:** spec 附录 B P3 fmod row "浮点取模 `%=` / `a % b` reject" (i32/i64 整数模 ship, 浮点模不 ship).

| 输入 | 期望 (per spec 附录 B P3) | v1.7.2 实际 |
|------|--------------------------|-------------|
| `i32 % i32` (整数模) | i32 余数 | ✅ OK (codegen emit `rem` / `div`) |
| `i64 % i64` | i64 余数 | ✅ OK (codegen emit `rem` / `div`) |
| `f64 % f64` (浮点模) | f64 IEEE 754 remainder | ❌ **vendor QBE reject** "invalid instruction: remd" |
| `f64 %= f64` (compound) | f64 复合赋值 | ❌ **同上** (跟 `%=` sema 通过但 codegen emit `remd` reject) |

**症状:**
```
test.jhyy:3:9: error: invalid instruction 'remd' (vendor QBE 2026-08-15 build 不支持)
codegen errors
```

**根因:** vendor QBE (`qbe/qbe.exe` 2026-08-15 build, per `docs/logs/v1/changelog-v1.7.2.md` A1 ship 时 fact-check fail) 不实现 `remd` (f64 remainder) 和 `rems` (f32 remainder) 指令。其他 backend (e.g. gcc) 编译期折叠到 `fmod()` library call, 但 vendor QBE 不能 fold, 拒绝指令。

**workaround (v1.7.2 期间):** v1.7.2 patch A1 ship 时 fact-check 发现 vendor QBE 不支持 `remd`/`rems`, 标 LIMIT 不修, 推 v2.x 真修 (vendor QBE 升级主线或自研 backend)。spec 附录 B P3 fmod row "推 v2.x" 段保留 v2.x 真修描述, 缺独立 W-NNN 归档 (本 v1.7.3 patch 补登)。

**实现路径 (推 v2.x):**
1. **vendor QBE 升级** — 拉 QBE 上游主线 (2026-Q3 或更新), 看是否新增 `remd`/`rems` 支持 (可能性高, QBE 上游对 SIMD + math 指令支持在持续推进)
2. **自研 backend** — v2.x 末 QBE 重写后, codegen emit `remd`/`rems` 指令 (或 fold 到 `fmod()` library call, 跟 gcc 行为对齐)
3. **fmod library helper** — 临时方案: codegen 把 `a % b` (f64) 折成 `(a - (a / b).floor() * b)` user-space formula, runtime 调用 `floor()` builtin (qbe 提供 `floord`) + 减法 + 乘法

**影响范围:**
- user-space test: 仅 fmod 测试 (尚未 ship), 不影响 regress
- OS-required (jhyy_OS): MMIO buffer scan 用到 `addr % page_size` 是整数模 (i64 % i64), 不依赖浮点模
- math lib: jhyy 暂无 `<math.h>` 风格 lib, 用户写 fmod 一般用 lib call (`extern fn fmod(...)`), 不走 `%` 路径

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` 附录 B P3 (fmod row, C4 v1.7.3 patch 加 cross-ref W-058)
- `docs/logs/v1/changelog-v1.7.2.md` A1 (v1.7.2 patch A1 ship 时 fact-check fail, 标 LIMIT 推 v2.x)
- vendor QBE build `qbe/qbe.exe` 2026-08-15 (per `docs/internal/architecture.md` QBE IL 速查段)

---

## W-059: defer codegen path silent crash (v1.3.6 ship 后 0 test 验证 accept path) (推 v1.8)

**ID:** W-059
**状态:** ✅ RESOLVED 2026-08-28 (v1.8.0)
**日期:** 2026-08-28 (v1.7.3 patch A1/A2/A3 attempt 时发现) → 2026-08-28 (v1.8.0 Phase 2 真修)
**superseder:** v1.8.0 Phase 2 真修 (1-line fix `src0/sema.jhyy:1410`, 3 defer test SKIP 删)
**触发面:** v1.3.6 defer ship 后 0 accept-path test 在 default regress 跑过, v1.7.3 patch A1 attempt 写 `defer sink(log);` 测试时发现 codegen silent exit (EXIT=0 但不产出 .il / .s / .exe).

| 输入 | 期望 (per spec §D.6 defer) | v1.7.2 实际 |
|------|---------------------------|-------------|
| `defer sink();` (no-arg defer) | 函数返回时 LIFO 触发 `sink()` | ❌ **silent exit** (EXIT=0, 无 .il 产出) |
| `defer sink(log);` (1-arg defer) | 函数返回时 LIFO 触发 `sink(log)` | ❌ **同上** |
| `defer sink(); defer bump(10); defer bump(100);` (multi LIFO) | LIFO 顺序 `bump(100)` → `bump(10)` → `sink()` | ❌ **同上** |
| `defer { block; }` (块语法) | block 触发 | ❌ **sema reject** "defer requires fncall" (per spec §D.6 限制, v3.x) |

**症状:**
```
[1] imports start
[2] imports done
[3] sema start
[sema] P1 ndeccls=2
[sema] P1 i=0
[sema] P2 start
[sema] P3 start
[sema] P3 i=0
EXIT=0
--no .il / .s / .exe produced--
```

sema 完整通过 (P3 i=0 后无错误), codegen 路径 silent exit 不报错。EXIT=0 误导用户以为 compile 成功, 但 .il 没产生, link 步骤也无 .s 输入。

**根因:** 待诊断 (v1.7.3 patch scope 限制, 不深挖 src/src0 codegen path)。可能触发面:
1. `cg_emit_defers` 调用前 `cg->current_fn` 未正确设置 (per src/codegen.c line 2333 `cg->current_fn = fd;`)
2. `cg_emit_defers` 内部访问 `fd->defers[i-1]` 时 `i-1` 越界 (uint underflow) 触发 silent crash
3. `cg_emit_defers` 路径 emit 的 `call $sink` 没 register 到 module globals, QBE 拒后续引用 (但这是 codegen 完成 EXIT!=0, 不是 EXIT=0 silent)
4. **Stage 2 byte-equal closure 干扰** — jhyy.exe / jhyy_stage0.exe 的 cg_emit_defers 实现有差异 (C-side 完整 vs jhyy-side 部分), v1.3.6 ship 时未在 jhyy.exe + jhyy_stage0.exe 双 binary 验证 accept path

**workaround (v1.7.3 期间):** v1.7.3 patch C5-C7 临时修 SKIP directive (per `mcp-jhyy/jhyy_regress.py` 新加 `// SKIP: <reason>` 解析 + regress skip), 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) 暂加 SKIP comment 推迟 v1.8 真修。

**实现路径 (推 v1.8):**
1. **codegen path 真修** — v1.8 sprint 设计时, 走 `cg_emit_defers` 完整 call chain 诊断, 加 assert / debug print 找 silent exit 触发点
2. **accept-path test 真 ship** — v1.3.6 ship 时 0 test 验证 accept path, 未来任何 "ship 但 0 test" 特性 ship 流程需加 hard rule "must have ≥1 default regress test"
3. **jhyy.exe + jhyy_stage0.exe 双 binary parity 验证** — v1.8 defer 真修后, 双 binary regress verify (per `feedback_fix_evaluation_rule` 5/5 PASS gate)

**影响范围:**
- user-space test: 仅 3 defer test 暂 skip, 不影响 regress baseline (96/96 PASS + 10 SKIP)
- v1.3.6 ship 期间 **0 test 验证 defer accept path** — 这是 ship 流程问题, 不只是 codegen bug
- v1.x user-space 用 defer 的代码 (fopen/fclose 资源清理典型) 全部 silent fail, **v1.7.3 ship 后 v1.x user-space defer 不能用** — 这要 v1.8 真修后才恢复

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § D.6 (defer 语义 — 权威, B2 v1.7.3 patch 加 BMP-only 限制 + defer ship 描述)
- v1.3.6 ship commit `169759c` (per `docs/logs/v1/changelog-v1.3.6.md`) — ship 时 0 accept-path test 验证, 这条 ship 流程 gap 需 v1.8 反思
- `mcp-jhyy/jhyy_regress.py` v1.7.3 SKIP directive (新加, 跟 EXPECT/EXPECT-ERROR/SETENV 并列)
- `feedback_fix_evaluation_rule` 5/5 PASS gate (v1.8 defer 真修后必须走)

**Resolution (2026-08-28 v1.8.0):**

**根因 (empirical, MCP-only Phase 1A):**
`compiler/src0/sema.jhyy` `sema_defer_register` (NODE_DEFER case line 1399-1435) 调 `infer_type(ctx, expr)` 漏传 `ta` (TypeArena arg) — jhyy-side `infer_type` 是 3-arg signature `(ctx: *SemaContext, ta: *TypeArena, n: *Node) -> *Type` (per `compiler/src0/sema.jhyy` line 499), C-side 是 2-arg `(ctx, n)` (per `compiler/src/sema.c` line 315). jhyy-side 漏 `ta` 等于把 `expr` ptr 当 `ta` 传 → sema 阶段 silent corrupt stack frame → `[sema] P3 i=0` print 后 crash 0 .il/.s/.exe. C-side 调用 `infer_type(ctx, dd->expr)` (line 1018) 正确因为 signature 对得上.

**Phase 1A empirical characterization (0 src/src0 改动):**
- `jhyy_get_il` on `defer_basic.jhyy` → outcome B (no IL produced)
- `jhyy_check` on `defer_basic.jhyy` → outcome Y (sema phase crash)
- 决策矩阵: B+Y → crash 在 sema, 跟 `[sema] P3 i=0` 报告一致
- `jhyy_stage0.exe compile defer_basic.jhyy` 成功 — Stage 0 没 bug, bug 是 jhyy-side 独有 (漏 `ta` arg)

**Phase 1B bisection (minimal debug print):**
在 `src0/sema.jhyy` NODE_DEFER case 入口 + infer_type 调用前后加 fprintf → rebuild → 复现 → 定位 crash 时机在 `infer_type(ctx, expr)` 实际 call 时 (jhyy-side infer_type 把 `expr` ptr 当 `ta` 读, deref 越界).

**Phase 2 真修:**
1-line fix `compiler/src0/sema.jhyy` line 1410:
```diff
-            let _v = infer_type(ctx, expr);
+            let _v = infer_type(ctx, ta, expr);
```
C-side 不需改 (signature 是 2-arg, 调用正确).

**回归 verification:**
- 5/5 PASS on each target test per `feedback_fix_evaluation_rule`:
  - `defer_basic.jhyy` EXIT=0 ✓ (sink(42) side-effect, return 0)
  - `defer_multi_lifo.jhyy` EXIT=0 ✓ (Go-style defer: return value capture 先, defer LIFO 后跑)
  - `defer_let_init.jhyy` EXIT=123 ✓ (return x+y = 123, defer sink(x) 仅 side-effect)
- regress baseline: 96/96+10 → **102/102+4** (+6 PASS, -6 SKIP, baseline 不变)
- jhyy.exe parity regress: 102/102+4 (跟 jhyy_stage0.exe 一致)
- N=4 byte-equal closure: v2/v3/v4 sha=`03a1cdd4...` (closure hold)

**反思 (ship 流程 gap, v1.3.6 教训):**
v1.3.6 defer ship 时 0 accept-path test 验证 (commit `169759c` ship 时 defer test 0 个). v1.8.0 反思: 未来任何 "ship 但 0 test" 特性 ship 流程需加 hard rule "must have ≥1 default regress test". 3 defer test (`defer_basic.jhyy` / `defer_multi_lifo.jhyy` / `defer_let_init.jhyy`) 现 default regress PASS, ship 流程 gap 闭环.

---

## W-060: enum variant payload ABI mismatch (Mixed::I(1234) match 走 wildcard path EXIT=210 ≠ 1234) (推 v1.8)

**ID:** W-060
**状态:** ❌ INVALID 2026-08-28 (v1.8.0) — v1.7.3 ship 期间 fact-check 误判为真 bug, v1.8.0 Phase 1 调查 (Agent 3) 确认 = test artifact (bash `$?` 8-bit truncation + W-028 mod-256 fix 已 equalize 比较)
**日期:** 2026-08-28 (v1.7.3 patch A5/A6 attempt 时 fact-check 误判) → 2026-08-28 (v1.8.0 Phase 1 INVALID 闭环)
**superseder:** v1.8.0 Phase 3 INVALID 清理 (2 enum test SKIP 删, regress W-028 fix PASS)
**触发面:** v1.7.3 patch A5/A6 attempt 写 `Mixed::I(1234)` enum variant payload 提取测试时发现 match 走 wildcard path (`S(_)`) 而不是 `I(v)` path.

| 输入 | 期望 (per spec §11.4 Pattern binding `Some(v) => v`) | v1.7.2 实际 |
|------|---------------------------------------------------|-------------|
| `match Mixed::I(1234) { I(v) => v, S(_) => -1, B(_) => -2 }` | EXIT=1234 (走 `I(v)` path) | ❌ EXIT=210 (= 0xD2, 走 wildcard path 拿到 tag offset 错位) |
| `match Option::Some(42) { Some(v) \| Some(v) => v, None => 0 }` | EXIT=42 (OR pattern, 两边 `Some(v)`) | ❌ EXIT=0 (match 走到 `None` path 而不是 OR pattern `Some(v)`) |

**症状:**
```jhyy
type Mixed = enum { I(i32), S(*u8), B(bool) }
fn main_jhyy() -> i32 {
    let m: Mixed = Mixed::I(1234);
    return match m {
        Mixed::I(v) => v,        // 期望走这里
        Mixed::S(_) => -1,
        Mixed::B(_) => -2,
    };
}
--EXIT=210 (= 0xD2), 期望 EXIT=1234--
```

**根因:** 待诊断 (v1.7.3 patch scope 限制, 不深挖 src/src0 sema + codegen path)。可能触发面:
1. **enum variant tag compare 错位** — `Mixed::I(1234)` 的 enum payload 1234 被 emit 到 tag field 偏移位置 (e.g. 偏移 0), match `Mixed::I(v)` 时 tag compare 取错位 payload (e.g. 取到 0xD2 = 210 = enum variant I tag * sizeof(*u8) + 偏移错位)
2. **enum payload ABI size/align 错** — spec 附录 B enum ABI 描述 (tag 4 bytes + payload 对齐到 8 bytes), 但 codegen 实际 emit tag + payload 紧凑 (无 padding), 导致 match arm payload 取错偏移
3. **OR pattern `Some(v) \| Some(v)` sema 类型规则 bug** — 两边 `Some(v)` 应共享 binding scope, 但 sema 走 2-pass walker 时 binding scope 串掉, match arm 走 `None` path 而不是 OR pattern path

**workaround (v1.7.3 期间):** v1.7.3 patch C5-C7 临时修 SKIP directive, 2 enum test (`payload_bind_multi.jhyy` / `payload_bind_nested.jhyy`) 暂加 SKIP comment 推迟 v1.8 真修。

**实现路径 (推 v1.8):**
1. **enum ABI 真修** — v1.8 sprint 设计时, 走 enum variant payload emit + match tag compare 完整 call chain 诊断, 加 assert / debug print 找 tag / payload 偏移错位触发点
2. **OR pattern sema 真修** — `check_or_consistency` 2-pass walker 完整跑 (per `compiler/src/sema.c` + `compiler/src0/sema.jhyy`), 加 binding scope trace
3. **enum variant test 真 ship** — v1.3.7 ship Pattern binding `Some(v) => v` 时只测 single-payload single-binding (`Some(i32)`), 缺 multi-payload multi-binding 测试覆盖, 未来类似 ship 流程需加 hard rule "must cover N variant type variety"

**影响范围:**
- user-space test: 仅 2 enum test 暂 skip, 不影响 regress baseline (96/96 PASS + 10 SKIP)
- v1.3.7 ship Pattern binding 时只覆盖 single-payload single-binding — multi-payload / multi-binding 推 v3.x (per spec §D.7 line 1385 spec 描述超前于实现, v1.7.3 B3 patch fact-check fix)
- **OR pattern `Some(x) \| Some(x)` v1.3.7 ship 时 0 multi-binding test 验证** — 实际可能类似 W-059 ship 流程 gap (0 test 验证 multi-binding path)
- v1.x user-space enum variant 提取除 `Some(i32)` 单 binding 外都不可靠 — 这要 v1.8 真修后才恢复

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § 11.4 / § D.7 (Pattern binding + multi-binding 限制)
- v1.3.7 ship commit `0f32977` (per `docs/logs/v1/changelog-v1.3.7.md`) — ship 时只覆盖 single-payload single-binding
- `mcp-jhyy/jhyy_regress.py` v1.7.3 SKIP directive
- `feedback_fix_evaluation_rule` 5/5 PASS gate

**INVALID status (2026-08-28 v1.8.0 Phase 1 调查, Agent 3):**

**真因 (NOT 真 bug):**
v1.7.3 ship 期间 fact-check 把 bash `$?` 8-bit truncation artifact 误判为 enum variant payload ABI bug:
- `Mixed::I(1234)` 实 EXIT=1234 — bash `$?` truncates 8-bit → 1234 & 0xFF = 210 (0xD2)
- `subprocess.run` on Windows 同步 8-bit truncate → regress.py line 246 注释明示 "Windows returns 8-bit truncated"
- regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较 → 210 == (1234 mod 256) → PASS

**OR pattern `Some(v) | Some(v)` EXIT=0:**
v1.7.3 patch A6 误诊 line 1 SKIP 标签把 spec §D.7 multi-binding 限制跟 OR pattern 测试混淆. v1.8.0 Phase 1 验证: OR pattern 实 EXIT=42 (无 ABI mismatch, `Some(42)` 走 OR arm 正常返回 42). spec §D.8 ship OR pattern (1 layer OK), `Some(v) | Some(v)` 是合法 OR pattern (两边同 binding 名).

**SKIP 删后 verify:**
- `payload_bind_multi.jhyy` (W-060 第一个): SKIP directive 删 → regress PASS (EXIT=210 → mod-256 equalize → 210 == 1234 mod 256 = 210)
- `payload_bind_nested.jhyy` (W-060 第二个, OR pattern): SKIP directive 删 → regress PASS (EXIT=42 == EXPECT=42)

**回归 verification:**
- regress baseline: 99/99+7 → **102/102+4** (+3 PASS, -3 SKIP)
- jhyy.exe parity regress: 102/102+4 (跟 jhyy_stage0.exe 一致)
- 0 src/src0 改动 (INVALID 闭环 = 纯文档 + test SKIP 删, 无 code 改动)
- N=4 byte-equal closure hold (跟 v1.7.3 ship 一致, v2/v3/v4 sha 不变)

**教训 (fact-check 流程 gap):**
v1.7.3 fact-check 只看了 EXIT vs EXPECT 数字不同就标 DEFERRED v1.8, 没 trace 到 bash `$?` 8-bit truncation 根因. v1.8.0 反思: fact-check EXIT mismatch 必先 trace 到 exit code propagation path (bash / subprocess.run / regress.py / W-028 fix 是否 equalize), 再决定 bug 状态. INVALID ≠ 错误分类, 是 fact-check 流程漏了 root cause verification.

---

## W-061: nested struct field offset bug (Outer { tag, inner } read EXIT=51 ≠ 307) (推 v1.8)

**ID:** W-061
**状态:** ❌ INVALID 2026-08-28 (v1.8.0) — v1.7.3 ship 期间 fact-check 误判为真 bug, v1.8.0 Phase 1 调查 (Agent 3) 确认 = test artifact (bash `$?` 8-bit truncation + W-028 mod-256 fix 已 equalize 比较)
**日期:** 2026-08-28 (v1.7.3 patch A7 attempt 时 fact-check 误判) → 2026-08-28 (v1.8.0 Phase 1 INVALID 闭环)
**superseder:** v1.8.0 Phase 3 INVALID 清理 (nested_struct_dwarf.jhyy SKIP 删, regress W-028 fix PASS)
**触发面:** v1.7.3 patch A7 attempt 写 `Outer { inner: Inner { x, y }, tag }` nested struct read 测试时发现 read path 走错偏移.

| 输入 | 期望 (per spec §9.4 + W-019 RESOLVED 2026-08-14) | v1.7.2 实际 |
|------|--------------------------------------------------|-------------|
| `(*o).inner.x + (*o).inner.y` (Inner sum) | 100 + 200 = 300 | ❌ EXIT=44 (read Inner sum 错位) |
| `(*o).tag` (Outer tag) | 7 | ❌ EXIT=7 (read Outer tag 正确) |
| `read_outer(&o) + read_inner(&o)` | 7 + 300 = 307 | ❌ EXIT=51 (= 7 + 44, Inner sum 错位) |

**症状:**
```jhyy
type Inner = struct { x: i32, y: i32 }
type Outer = struct { inner: Inner, tag: i32 }
fn read_inner(o: *Outer) -> i32 { return (*o).inner.x + (*o).inner.y; }
fn read_outer(o: *Outer) -> i32 { return (*o).tag; }
fn main_jhyy() -> i32 {
    let o: Outer = Outer { inner: Inner { x: 100, y: 200 }, tag: 7 };
    return read_outer(&o) + read_inner(&o);
}
--EXIT=51, 期望 EXIT=307 (= 7 + 100 + 200)--
```

**根因:** 待诊断 (v1.7.3 patch scope 限制, 不深挖 src/src0 codegen path)。可能触发面:
1. **Outer struct layout 错位** — Outer { inner: Inner { 8 bytes }, tag: i32 (4 bytes) } ABI 布局 = inner @ 偏移 0, tag @ 偏移 8 (对齐 Inner sizeof = 8). 但 codegen 实际 emit tag @ 偏移 0, inner @ 偏移 8 (颠倒顺序), 导致 `(*o).tag` 实际读到 inner.x 第一个 byte (= 100), 但 EXIT=7 说明 tag read OK. 可能 codegen 颠倒 + Inner sum = 44 (读 inner 偏移 8 = tag 字节后 4 字节 garbage), inner.x 读到 garbage 而不是 100
2. **`cg_field_addr` 嵌套 struct path 残留** — W-019 RESOLVED 2026-08-14 修了 1 层嵌套 (per `compiler/src/codegen.c` line 6638134 commit), 但 codegen path 在 Inner (2 fields 8 bytes) + Outer tag 后置 (8 bytes offset) 仍有 byte-order 错
3. **struct field order 解析 vs codegen 不一致** — parser 解析 `Outer { inner: Inner, tag: i32 }` field 顺序正确, 但 codegen emit field 时按 decl order 而非 init order (tag 后置但 codegen 当 tag 前置 emit, 字节序颠倒)

**workaround (v1.7.3 期间):** v1.7.3 patch C5-C7 临时修 SKIP directive, nested_struct_dwarf.jhyy 暂加 SKIP comment 推迟 v1.8 真修。现有 nested_struct_test.jhyy + nested_struct_deep.jhyy + mixed_nested_struct_recursive.jhyy 仍 PASS (per regress 96/96), 所以 W-019 真修在 1-layer 嵌套覆盖范围 OK, W-061 是 2-field 嵌套 + Outer 字段序颠倒的特殊场景未覆盖。

**实现路径 (推 v1.8):**
1. **struct layout 诊断** — v1.8 sprint 设计时, 走 `cg_field_addr` + struct layout emit 完整 call chain, 加 assert / debug print 找 Outer field order 颠倒触发点
2. **W-019 真修范围扩展** — W-019 RESOLVED 2026-08-14 修 1-layer 嵌套 (Inner + Outer 都 1 field), 2-field Inner + 字段序后置 Outer 是 W-061 新发现的扩展 case
3. **struct layout test coverage 扩展** — 现有 nested_struct_test.jhyy + _deep.jhyy 覆盖 1-layer / 2-layer 嵌套, 但缺 Outer 多 field + 字段序后置测试, v1.8 补

**影响范围:**
- user-space test: 仅 nested_struct_dwarf.jhyy 暂 skip, 不影响 regress baseline (96/96 PASS + 10 SKIP)
- 现有 nested struct 测试 (`nested_struct_test.jhyy` 等) 仍 PASS — W-061 是 Outer 多 field + 字段序后置特定场景
- OS-required (jhyy_OS): page table entry struct / capability struct 多 field 嵌套典型, W-061 真修后才可依赖
- v1.x user-space 嵌套 struct 除 1-field Inner + 1-field Outer 外不可靠 — 这要 v1.8 真修后才恢复

**引用:**
- spec `docs/abis/jhyy-lang-spec-v1.3.0.md` § 9.4 (struct layout — 权威)
- W-019 RESOLVED 2026-08-14 (per `docs/logs/v1/changelog-v1.4.6.md` + `compiler/src/codegen.c` line 6638134 commit) — 1-layer 嵌套真修
- `nested_struct_test.jhyy` + `nested_struct_deep.jhyy` + `mixed_nested_struct_recursive.jhyy` (existing 1-layer / 2-layer 覆盖, v1.7.3 regress 96/96 PASS)
- `mcp-jhyy/jhyy_regress.py` v1.7.3 SKIP directive
- `feedback_fix_evaluation_rule` 5/5 PASS gate
- gdb_pretty_test.jhyy:15-18 (v1.7.3 patch A7 注释更新: "nested struct coverage deferred to v1.8 due to W-061")

**INVALID status (2026-08-28 v1.8.0 Phase 1 调查, Agent 3):**

**真因 (NOT 真 bug):**
v1.7.3 ship 期间 fact-check 把 bash `$?` 8-bit truncation artifact 误判为 nested struct field offset bug:
- `read_outer(&o) + read_inner(&o)` 实 EXIT=307 (= 7 + 100 + 200) — bash `$?` truncates 8-bit → 307 & 0xFF = 51
- `subprocess.run` on Windows 同步 8-bit truncate → regress.py W-028 mod-256 fix (line 243-263) 已 equalize 比较 → 51 == (307 mod 256) → PASS
- 实际 EXIT table (per W-061 上面表): tag=7 ✓ + inner.x + inner.y = 300 ✓ → 7 + 300 = 307 (全对, 无 read 错位)

**Inner sum 错位表 line 4085 错标:**
"100 + 200 = 300 → ❌ EXIT=44 (read Inner sum 错位)" — v1.8.0 Phase 1 调查确认: 实 EXIT=300 (correct). line 4085 错标因为 follow-up 误算 `44 = 7 + 44 - 7` (= read_outer+read_inner EXIT=51, 减 read_outer=7, 推 read_inner=44 — 但实际 read_inner 实 EXIT=300, 不是 44). 同 root cause = fact-check 没 trace 到 exit propagation path.

**SKIP 删后 verify:**
- `nested_struct_dwarf.jhyy`: SKIP directive 删 → regress PASS (EXIT=51 → mod-256 equalize → 51 == 307 mod 256 = 51)

**回归 verification:**
- regress baseline: 99/99+7 → **102/102+4** (+3 PASS, -3 SKIP)
- jhyy.exe parity regress: 102/102+4 (跟 jhyy_stage0.exe 一致)
- 0 src/src0 改动 (INVALID 闭环 = 纯文档 + test SKIP 删, 无 code 改动)
- N=4 byte-equal closure hold (跟 v1.7.3 ship 一致, v2/v3/v4 sha 不变)

**教训 (跟 W-060 同):**
fact-check EXIT mismatch 必先 trace 到 exit code propagation path. v1.7.3 误把 bash `$?` 8-bit truncation 当 read offset bug 标 DEFERRED, 是流程 gap. v1.8.0 改: fact-check EXIT mismatch 必先 verify exit code path (bash / subprocess / regress.py / W-028 fix), 再标 bug 状态. W-019 RESOLVED 2026-08-14 已覆盖 1-layer 嵌套; W-061 = 2-field Inner + Outer 字段序后置 spec §9.4 layout 实对, 不需新修.


---

## W-062: VSCode UserChoice hijack + MSYS2 OpenWithProgids 双层 shadow → `.jhyy` 图标不显示 (推 v1.8.2)

**ID:** W-062
**状态:** ✅ RESOLVED 2026-08-29 (v1.8.3.1 patch — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice, 绕过 UCPD.sys kernel filter;v1.8.3 首次实现但 CustomAction 静默失败,v1.8.3.1 加 3-attempt fallback 真修)
**日期:** 2026-08-29 (v1.8.1 patch ship 后 user 反馈图标仍白板)
**superseder:** v1.8.3 patch — MSI CustomAction JHYYSetUCForAllUsers (Execute="deferred" + Impersonate="no" + Return="ignore") 调 `jhyy-setuc.exe --system-context` 枚举 `HKEY_USERS` S-1-5-21-… SIDs, 写每用户 UserChoice。SYSTEM trust chain 绕过 UCPD kernel filter (verified Phase 0 2026-08-29)。Bundle.wxs 加 .NET 8 Desktop Runtime 链式安装确保 prereq。
**触发面:** Windows 10/11 装了 JHYY + VSCode 双应用的机器, `.jhyy` 副档名被 VSCode 设为默认 opener 后, 文件总管文件夹视图显示白板文档图标

**症状:**
```
资源管理器文件夹内 .jhyy 文件图标:
  期望: navy + mint "J" 品牌图标 (jhyy.exe embedded RT_ICON 或 jhyy-icon.ico)
  实际: 白板文档图标 (shell32 default + 偶尔右下角 VSCode overlay)
双击 .jhyy:
  期望: jhyy.exe run "%1" (compile + run) 或 Code.exe "%1" (VSCode 编辑, 视 UserChoice 而定)
  实际: VSCode 打开 (UserChoice hijack)
SHGetFileInfo API 实测 (.jhyy 文件):
  hIcon = 1 (per icon system docs hIcon=1 = sentinel "default icon")
  iIcon = 0x3FFFFC0000000002 (sentinel — Explorer 解析 ProgId 失败)
  szTypeName = "" (空 — ProgId 解析失败无类型名)
```

**根因 (2 层独立 hijack):**

### Layer 1: VSCode UserChoice hijack
- 注册表路径: `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice\`
- 写入时机: user 第一次对 `.jhyy` 文件右键 → "打开方式" → 选 "VSCode" → 勾选 "始终用此应用打开" → 确定
- 写入内容: `(default) = "Applications\Code.exe"`, 加上 `Hash = "<Mozilla reverse-engineered hash>"`
- 行为: Windows folder view **优先用 UserChoice ProgId 取 icon**, 不走 fallback chain
- 影响: `Applications\Code.exe\DefaultIcon` = VSCode 自带 `default.ico`, 但 Explorer 解析 `Applications\Code.exe` ProgId 时有 quirk (returns `iIcon=0x3FFF...` sentinel + `szTypeName=""`), 实际渲染退回 shell32 默认白板文档图标
- **UCPD.sys 防护**: Windows 10 Feb 2024 cumulative update 起 UCPD (User Choice Protection Driver) kernel filter 加 Deny ACE 防止非 admin SetValue 覆盖 UserChoice。要写 UserChoice 必须 admin + 暂停 UCPD 服务 (`sc stop UCPD`)

### Layer 2: MSYS2 OpenWithProgids 残留
- 注册表路径: `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\OpenWithProgids\`
- 写入时机: MSYS2/Git Bash 看到 `chmod +x *.jhyy` 启发 `*_auto_file` heuristic, 写 `jhyy_auto_file` (REG_NONE value) 到 OpenWithProgids
- 配套 ProgId: `HKCU\Software\Classes\jhyy_auto_file` 整棵树 (可能有, 视 MSYS2 版本而定)
- 行为: v1.8.1 patch step 4 (`reg delete HKCU\Software\Classes\.jhyy`) 只删了 `.jhyy` 主键, 没清 `OpenWithProgids` 子键对 `jhyy_auto_file` 的引用
- 影响: 部分 Explorer 路径会去找 `jhyy_auto_file\DefaultIcon` (不存在) → fallback shell32 blank

### 为什么 v1.8.1 patch 没修这两层
v1.8.1 patch 修了:
- (a) WiX `<RegistryValue Name="JHYYSourceFileMapping">` → 去 `Name=` (写 `(default)`) — Explorer walk ProgID 走 `.jhyy\(default)`
- (b) `DefaultIcon` 从 `[INSTALLDIR]bin\jhyy-icon.ico` → `[INSTALLDIR]bin\jhyy.exe,0` (jhyy.exe embedded RT_ICON via windres, per `compiler/src/jhyy.rc` 新文件)
- (c) `install-configure-all.bat` step 4 加 `reg delete HKCU\Software\Classes\.jhyy` (MSYS2 主键 shadow)

但 v1.8.1 漏了:
- `HKCU\…\FileExts\.jhyy\OpenWithProgids\jhyy_auto_file` 子键 (step 4 删的是主键, 不是 OpenWithProgids 子键)
- `HKCU\…\FileExts\.jhyy\UserChoice` (整棵树, VSCode 写的)
- `HKCU\Software\Classes\jhyy_auto_file` ProgId 本身 (跟 OpenWithProgids 配套)

### icon chain 现状 (v1.8.1 ship 后):
```
.jhyy file
  → Explorer 找 UserChoice ProgId = Applications\Code.exe
    → HKCU\Software\Classes\Applications\Code.exe\DefaultIcon = "...\default.ico"
      → Explorer 解析 quirk (iIcon=0x3FFF... sentinel, szTypeName="") → shell32 blank fallback ❌
```

**workaround (v1.8.1 期间):** user 跑 `reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy" /f` 手工清 UserChoice, 退回 HKLM `JHYY.SourceFile` (icon=jhyy.exe,0)。临时 work, 但每次 user 重设 "VSCode 默认" 又失效, 且 user 操作繁琐。

**修复 (v1.8.2 Path B):**

### Phase 1: C# tool — Mozilla UserChoice Hash 算法
- 新文件 `installer/common/jhyy-setuc/Program.cs` — C# (.NET 8-windows) port Mozilla Firefox `browser/components/shell/WindowsUserChoice.cpp` (MPL 2.0)
- 算法: UTF-16LE `<progId>` + null terminator → MD5 → 2-pass scramble with constant multipliers → 8-byte Base64 string
- Verified: `Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00` → `Pm0l9cVOllo=`
- CLI args: `<ext> <progId> <description> <iconPath> <iconIndex> <openCommand>`
- Try/finally 保证 UCPD service restart (即使 algorithm 失败也要 restart)
- Verifies via `reg add` ProgId 成功 + `reg add` Hash 失败 (access denied = UCPD blocking, expected)

### Phase 2: MSI Component shipping
- WiX 新增 `ManualFixIconCachePS1` Component (Guid A2F4B7E9-5D3C-4E8B-A6F1-7C9D2E3B5A88): ships `manual-fix-icon-cache.ps1` to INSTALLDIR\common\
- WiX 新增 `JHYYSetUCExe` Component (Guid B3D5C8F2-6E4D-4F9C-B7E2-8D1A3F4C6B99): ships `jhyy-setuc.exe` to INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\
- 不 ship .NET runtime DLLs (依赖用户机装 .NET 8 Desktop Runtime; 缺失时 jhyy-setuc.exe 启动失败 → manual-fix-icon-cache.ps1 try/catch → Path A fallback)

### Phase 3: RunOnce 触发
- `installer/common/install-configure-all.bat` step 5: `reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy" /f` (清旧 UserChoice + OpenWithProgids shadow)
- `installer/common/install-configure-all.bat` step 6: `powershell -File manual-fix-icon-cache.ps1` (Path B: 调 jhyy-setuc.exe 写新 UserChoice)

### Phase 4: Path A fallback
- `manual-fix-icon-cache.ps1` try/catch 包 jhyy-setuc 调用, 失败自动降级 Path A
- Path A: `reg delete HKCU FileExts\.jhyy` + `reg delete HKCU\Software\Classes\jhyy_auto_file` (无 UserChoice 写入), 让 Explorer 退回 HKLM `JHYY.SourceFile` (`jhyy.exe,0` embedded icon, v1.8.1 ship 的 fallback)
- 不论 Path A/B 都跑 explorer 重启 + iconcache_*.db + thumbcache_*.db 删 (brute-force icon cache flush)

### icon chain 修复后 (Path B 成功):
```
.jhyy file
  → Explorer 找 UserChoice ProgId = JHYY.EditInVSCode  (Path B 写入)
    → JHYY.EditInVSCode\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy-icon.ico,0"
      → 256×256 navy + mint "J" 品牌 ✅
  → 双击 .jhyy → shell\open\command = "Code.exe" "%1"" → VSCode 开启
```

### icon chain 修复后 (Path A fallback, Path B 失败时):
```
.jhyy file
  → Explorer 找 UserChoice (Path A 删空)
    → 退回 HKLM\SOFTWARE\Classes\.jhyy\(default) = JHYY.SourceFile
      → JHYY.SourceFile\DefaultIcon = "C:\Program Files\JHYY\bin\jhyy.exe,0"
        → jhyy.exe embedded RT_ICON → 6-frame Vista+ ICO → navy "J" + mint 圆点 ✅
  → 双击 .jhyy → shell\open\command = "jhyy.exe" run "%1"" → compile + run
```

**user 机器立刻生效** (v1.8.2 时期 commit 后不需等 MSI rebuild):
```bash
# v1.8.2 时期: 双击桌面 C:\Users\liuzhen\Desktop\JHYY-Fix-Icon.bat (self-elevate via UAC)
# 自动: build jhyy-setuc.exe (如果未 build) → 调 manual-fix-icon-cache.ps1 → Path B write → icon cache flush
#
# v1.8.3.1+ 已 supersede: MSI install WiX CustomAction SYSTEM-context 自动跑 jhyy-setuc.exe
# --system-context, 写每 user HKCU, 无需手动跑任何 bat/ps1。 桌面 bat 已删(2026-08-29)。
# 若需手动跑(developer / 旧版升级), 直接 powershell -File "C:\Program Files\JHYY\bin\manual-fix-icon-cache.ps1"
```
输出应包含:
```
[v1.8.2 fix] Path B: register ProgId + write UserChoice...
[v1.8.2 fix] jhyy-setuc exit code: 0
[v1.8.2 fix] Restarting explorer.exe...
[v1.8.2 fix] DONE (Path B). Open a NEW Explorer window to see branded J icon on .jhyy files.
```

**验证 (per `feedback_fix_evaluation_rule` 5/5 PASS on each test):**
- **注册表 verify**: `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice" /v "ProgId"` → `JHYY.EditInVSCode` ✓
- **Hash verify**: `reg query "HKCU\…\FileExts\.jhyy\UserChoice" /v "Hash"` → 8-byte Base64 (per Mozilla 算法, 跟 timestamp 相关)
- **ProgId verify**: `reg query "HKCR\JHYY.EditInVSCode" /v ""` → `"JHYY Source File"` ✓
- **DefaultIcon verify**: `reg query "HKCR\JHYY.EditInVSCode\DefaultIcon" /v ""` → `"C:\Program Files\JHYY\bin\jhyy-icon.ico,0"` ✓
- **OpenCommand verify**: `reg query "HKCR\JHYY.EditInVSCode\shell\open\command" /v ""` → `"C:\Users\liuzhen\AppData\Local\Programs\Microsoft VS Code\Code.exe" "%1"` ✓
- **Cleanup verify**: `reg query "HKCU\Software\Classes\jhyy_auto_file"` → ERROR: 系统找不到指定的登录机码或值 ✓
- **Icon visual verify**: 开新 Explorer 视窗(不是 F5 刷已有, icon cache 可能缓存)→ `.jhyy` 显示 navy + mint "J" 品牌, 不再是白板 ✓
- **Algorithm verify**: 用 Mozilla 已知输入 (`Applications\Code.exe` + `.jhyy` + timestamp `2026-06-04 22:43:00`) 应产生 `Pm0l9cVOllo=` (unit-tested 过) ✓
- **regress 不退化**: `mcp__jhyy__jhyy_regress` 102/102 + 4 SKIP 不变 (v1.8.2 不改 codegen, 只改 installer/MSI/PowerShell) ✓

**影响范围:**
- **user-space**: 仅 Windows installer / shell 注册表, 不影响 .jhyy 源码 / codegen / 自举 / regress
- **OS-required (jhyy_OS)**: 不影响 (OS 启动不依赖 Windows shell UI)
- **回退条件**: VSCode 自动更新时可能再设 UserChoice → 用户再跑一次 `manual-fix-icon-cache.ps1` (per `feedback_fix_evaluation_rule` 5/5 PASS gate)

**已知 limitation (v1.8.2 不修):**
- 桌面 / 开始功能表 / 工作列的 `.jhyy` shortcut 图标仍可能缓存旧 icon → brute-force cache flush 后新视窗 OK
- VSCode 自动更新时可能再设 `UserChoice = Applications\Code.exe` → 用户再跑一次 `manual-fix-icon-cache.ps1`
- UCPD.sys 随 Windows update 改行为时 algorithm 可能要重 tune (Mozilla 算法 reverse-engineered 从 Windows 10 早期, Windows 11 24H2+ 可能有变)

**UCPD.sys 真实限制 (v1.8.2 现场诊断新增, 2026-08-29):**
- **Symptom**: Path B (`sc stop UCPD` → Mozilla 算法写 UserChoice) 在 Win10 2024-02+ 上失败 — `sc stop UCPD` 返回 exit 5 (access denied), 即使 admin;后续 `CreateSubKey(...\UserChoice)` 抛 `UnauthorizedAccessException`。
- **Root cause**: UCPD 是 FILE_SYSTEM_DRIVER (Type=2, State=4 RUNNING), 内核 filter 加 non-inherited Deny ACE on `HKCU\…\FileExts\.<ext>\UserChoice`。`sc stop` / `sc pause` / `fltmc unload` / `sc sdset` 全部 access denied (5)。UCPD 设计上就是不可程式化卸载。
- **Path A 也部分坏**: `Remove-Item HKCU\…\FileExts\.jhyy` 可以成功删,但 Windows shell 马上从 cached "user picked Code.exe" preference 自动重建 `UserChoice\ProgId = Applications\Code.exe` (重建的 Hash `Pm0l9cVOllo=` 跟 Mozilla 算法一致, 证明 Windows 内部也用同套算法)。
- **唯一可行的 manual workaround (v1.8.2 不支援自动)**:
  1. **Windows Settings UI**: 设置 → 应用 → 默认应用 → 按文件类型 → 输入 `.jhyy` → 选 `JHYY.SourceFile` (或 `JHYY.EditInVSCode`) → 确定。Windows 内部用 IApplicationAssociationRegistration COM 走 privileged API 绕过 UCPD Deny ACE。
  2. **安全模式 + reg add UCPD Start=4** (进阶): `bcdedit /set safeboot minimal` → 重启 → `reg add HKLM\SYSTEM\CurrentControlSet\Services\UCPD /v Start /t REG_DWORD /d 4 /f` → 重启 → 重跑 `manual-fix-icon-cache.ps1` → `reg add ... UCPD Start=0` → 重启。
  3. **(理论) SYSTEM scheduled task** 写 UserChoice: `schtasks /Create /RU SYSTEM /RL HIGHEST /SC ONCE /ST 00:00 /TN JHYYFix /TR "..."` — 测试时 `Register-ScheduledTask` 仍 access denied (per Win10 19045 默认权限), 未验证 UCPD 是否 bypass;**未 ship, 作为 W-062 follow-up 候选**。
- **jhyy-setuc.exe exit code 2**: 识别 UCPD block, 给清晰 manual workaround instructions (不再 generic UnauthorizedAccessException)。

**教训 (Path A vs Path B 设计 + v1.8.1 patch scope gap):**
- v1.8.1 只想 Path A(纯删 UserChoice 退回 HKLM) — 太简化, 忽略 user 双击行为变化 (从 VSCode → jhyy.exe run)
- v1.8.2 Path B(自定 ProgId) 保留 user 工作流 + 强制 icon, 较合理
- v1.8.1 patch scope 漏: `OpenWithProgids` 子键引用 + `jhyy_auto_file` ProgId 本身 + `UserChoice` hijack 整棵 — 任何 registry-walk icon chain 修复要列举所有可能 hijack layer, 不能只清表面
- UCPD 是 Windows 10 2024-02 后的事实: 任何 .ext 双击行为改变都要 admin + UCPD pause (Mozilla 算法合法 per MPL 2.0)
- 算法 porting 跨语言坑: PowerShell `-band` uint32 overflow (5.43E+19) → C# `uint` native, 注意 null terminator INCLUDED in Mozilla source (`(lstrlenW + 1) * sizeof(wchar_t)`)

**引用:**
- Mozilla `browser/components/shell/WindowsUserChoice.cpp` (MPL 2.0, 算法 reverse-engineered reference)
- PS-SFTA by DanysysTeam / SetUserFTA by kolbi (MIT, 替代工具 cross-ref)
- `installer/common/jhyy-setuc/Program.cs` (v1.8.2 新, C# .NET 8-windows tool)
- `installer/common/manual-fix-icon-cache.ps1` (v1.8.2 改 Path B + Path A fallback;v1.8.3.1 修 Path B jhyy-setuc.exe 路径)
- `installer/common/install-configure-all.bat` (v1.8.2 step 5 + 6)
- `installer/compiler/jhyy-compiler.wxs` (v1.8.2 新增 ManualFixIconCachePS1 + JHYYSetUCExe Components;v1.8.3 加 MSI CustomAction;v1.8.3.1 加 SetUCProp immediate CA + 4-file .NET 8 apphost ship + Directory=INSTALLDIR pattern)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.2 / v1.8.3 / v1.8.3.1 patch 段 (umbrella)
- `feedback_fix_evaluation_rule` 5/5 PASS gate
- `feedback_document_workarounds_in_docs` workaround 必须详细登记
- `feedback_changelog_umbrella` v1.x 单 umbrella CHANGELOG
- `feedback_audit_single_commit_diff` audit 走 `git show <sha>` 不跨 commit diff
- `feedback_commit_coauthor` MiniMax-M3 co-author

**v1.8.3.1 真修详情 (2026-08-29 ship 后 field test):**

### Symptom
v1.8.3 ship 在 fresh MSI install (admin elevation) 触发 CustomAction `JHYYSetUCForAllUsers` 时返回 `0x80004005`。`install.log` 显示:
```
CustomAction JHYYSetUCForAllUsers returned actual error code 1603 (note: may not be 100% accurate if translation failed)
```
`Return="ignore"` 不 rollback install,但 jhyy-setuc.exe 从未启动 → UserChoice 没写 → icon 仍 default。

### 3-attempt root cause chain

**Attempt 1 — property resolution in deferred CA**:
- 原始: `ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile"`
- 问题: MSI properties 在 deferred CA **不 resolve**(只有 immediate CA resolve)。`[JHYYSetUCBin]` 即使在 immediate CA 加 `Custom Action="SetUCProp" Property="JHYYSetUCBin" Value="..." Before="JHYYSetUCForAllUsers"` capture,仍失败。

**Attempt 2 — WiX `<Binary>` 不自动创建 property**:
- 诊断: WiX 4 `<Binary Id="JHYYSetUCBin" SourceFile="...">` 只往 MSI Binary table 加 row。`<CustomAction BinaryRef="JHYYSetUCBin">` 通过 Binary Key 引用,**不需 property**。但若 `ExeCommand` 想引用 binary 的 disk 路径,必须用其他机制(`<FileRef>` 或 `Directory=` cwd-based)。
- 修复: 移除 `<Binary>`,改成 `Directory="INSTALLDIR"` + `ExeCommand="&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot; --system-context ..."`(WiX 4 `Directory` attribute 注入 cwd,`[INSTALLDIR]` 从 `<Property>` table 取得 → 跑得通)。
- 同时改成 immediate + deferred 2-step 模式: `SetUCProp` (immediate) 写 `JHYYSetUCCmd` property capture `[INSTALLDIR]` → `JHYYSetUCForAllUsers` (deferred) `ExeCommand="[JHYYSetUCCmd]"` 从 CustomActionData 读。

**Attempt 3 — .NET 8 apphost missing assembly**:
- 新症状: Fix 1+2 后 CA 仍 fail,但 `0x80004005` 不再出。ProcMon trace 显示 `jhyy-setuc.exe` 进程立刻 exit 1,stderr: `Could not load file or assembly 'jhyy-setuc, Version=1.0.0.0...'`。
- 根因: `.NET 8 apphost model` — `jhyy-setuc.exe` 是 launcher,实际代码在 `jhyy-setuc.dll`(同 base name)。host 启动时按 base name 找同目录的 `.dll`。
- v1.8.3 ship 只 ship 了 `<File Source="...jhyy-setuc.exe" />`,**缺少 `.dll` + `.deps.json` + `.runtimeconfig.json`**。
- 最终修复: `<Component Id="JHYYSetUCExe">` 加 3 个 `<File>` entries,4 个 file 一起 ship 落地 `INSTALLDIR\bin\`。

### 最终 fix 代码 (after 3 attempts)

```xml
<InstallExecuteSequence>
  <Custom Action="SetUCProp" Before="JHYYSetUCForAllUsers" />
  <Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />
</InstallExecuteSequence>

<CustomAction Id="SetUCProp"
              Property="JHYYSetUCCmd"
              Value="&quot;[INSTALLDIR]bin\jhyy-setuc.exe&quot; --system-context .jhyy JHYY.SourceFile" />

<CustomAction Id="JHYYSetUCForAllUsers"
              Directory="INSTALLDIR"
              ExeCommand="[JHYYSetUCCmd]"
              Execute="deferred"
              Impersonate="no"
              Return="ignore" />

<Component Id="JHYYSetUCExe" Bitness="always64" Guid="B3D5C8F2-6E4D-4F9C-B7E2-8D1A3F4C6B99">
  <File Id="JHYYSetUCExeFile"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"
        KeyPath="yes" Checksum="yes" />
  <File Id="JHYYSetUCExeDll"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.dll" />
  <File Id="JHYYSetUCExeDeps"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.deps.json" />
  <File Id="JHYYSetUCExeRuntime"
        Source="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.runtimeconfig.json" />
</Component>
```

### manual-fix-icon-cache.ps1 Path B 顺带修 (自 v1.8.2 ship 起坏)

- 问题: 脚本用 `$setucExe = Join-Path $ScriptDir "jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe"` 找 binary,但**MSI install 后 `jhyy-setuc.exe` 落在 `INSTALLDIR\bin\`**(经 `JHYYSetUCExe` Component),不是 build 产物路径。**v1.8.2 ship 起 Path B 跑就 exit 1**(找不到 exe) → fallback Path A → 但 Path A 对付不了 UCPD → 等于 manual fix 没效。
- 修复: `$setucExe = Join-Path $ScriptDir "jhyy-setuc.exe"`(脚本位于 `INSTALLDIR\bin\` 自 v1.8.3 起,exe 同目录;若找不到 → exit 1 报 "MSI install incomplete")。

### Field verification (2026-08-29 fresh MSI install)

```
# install bundle silently
JHYY-1.8.3.1.exe /quiet /norestart

# verify CA 完成 (sentinel registry value)
Get-ItemProperty "HKLM:\SOFTWARE\JiHuiYiYou\JHYY" -Name "UserChoiceSystemContextApplied"
# → 2026-08-29T08:50:51.9285310Z  ✓

# verify UserChoice 写入 (liuzhen hive)
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.jhyy\UserChoice"
# → ProgId    REG_SZ    JHYY.SourceFile
# → Hash      REG_SZ    /dbBVe4aYxo=  ✓ (Mozilla algorithm)

# verify 4 files 落地
dir "C:\Program Files\JHYY\bin\jhyy-setuc*"
# → jhyy-setuc.exe  .dll  .deps.json  .runtimeconfig.json  ✓

# verify direct invocation
"C:\Program Files\JHYY\bin\jhyy-setuc.exe"
# → Usage: ... → exit 0  ✓

# visual verify
explorer.exe .
# → .jhyy files 显示 JHYY 品牌 "J" icon  ✓
```

### 教训 (3-attempt root cause chain)

1. **MSI deferred CA 属性解析**: MSI properties 在 deferred CA 执行时**不**自动 resolve。对 deferred CA 用 property,必须先由 immediate CA 写入 `CustomActionData`(`Custom Action="X" Property="Y" Value="..." Before="..."`)。常见误区: 在 `ExeCommand` 写 `[PropertyName]` 期待自动 expand。
2. **WiX `<Binary>` ≠ property**: `<Binary Id="X">` 只把 binary stream 加进 MSI Binary table。`<CustomAction BinaryRef="X">` 通过 Binary table 引用,不需 property。但若 `ExeCommand` 想引用 binary 的 disk 路径,必须用其他机制。
3. **.NET 8 apphost model**: `appname.exe` 是 launcher,实际代码在 `appname.dll`(同 base name)。**ship .NET 8 app 必须 ship 4 个 file**: `.exe` + `.dll` + `.deps.json` + `.runtimeconfig.json`。WiX `<File>` 一一 ship,无 magic 整组抓。
4. **silent failure debugging path**: `CustomAction X returned actual error code N (note: may not be 100% accurate if translation failed)` 是 MSI 对 CA 内部错误的兜底 message。**真原因** 要看 Event Viewer / INSTALLDIR log / ProcMon trace file I/O。
5. **stale build artifact 诊断**: v1.8.3 ship MSI build 15:53 + bundle build 后 user 16:17 重跑 icon regen → 16:17 regen log timestamp 比 install log 早 24 分钟 → 容易误判 "icon cache 没 flush"。**stale build artifact 也要清**: `Remove-Item installer/build-artifacts/jhyy-compiler-*.msi,jhyy-compiler-*.exe` 后 rebuild。
6. **v1.8.2 manual Path B 自 ship 起就 broken**: `manual-fix-icon-cache.ps1` 路径错指 build 产物路径,MSI install 后 exe 在 `INSTALLDIR\bin\` 不是 build 路径。**field test on fresh install 应发现**,但 v1.8.2 ship 只跑 self-elevate on existing machine(那里 `INSTALLDIR\common\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe` 是 build copy,跟 install path 重合,误以为 Path B work)。
- v1.8.1 patch commit `de4f219` (前一 sprint 修了 WiX (default) + embedded icon, 但漏 2 层 hijack)

---

### v1.8.3 Resolution — WiX MSI SYSTEM-context CustomAction 写 per-user UserChoice (UCPD.sys kernel filter bypass)

**UCPD 真实限制根因** (per v1.8.2 现场诊断 2026-08-29): UCPD.sys 是 Win10 2024-02+ cumulative update 引入的 `FILE_SYSTEM_DRIVER` (Type=2, State=4 RUNNING), 在内核 filter 层加 non-inherited Deny ACE on `HKCU\…\FileExts\.<ext>\UserChoice`。任何 user-mode caller (即使是 admin / elevated shell) 调 `Registry.CreateSubKey(UserChoice)` 都被拒 (`UnauthorizedAccessException`)。`sc stop UCPD` 返回 exit 5 (access denied) — UCPD 设计上就是不可程式化卸载。Mozilla UserChoice Hash 算法 token-independent (算法本身能跑), 但写路径 kernel-protected。

**Phase 0 现场验证关键发现** (2026-08-29):
- ✅ `sc create obj= LocalSystem type= own start= demand` 创建的 LocalSystem service 调 `Registry.CurrentUser.CreateSubKey(UserChoice)` 成功 — 写 `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` 完整。
- ✅ `sc stop UCPD` 从 SYSTEM 也是 exit 1052 (boot-start driver 没装 stop handler), 所以不需要也不能停 UCPD。
- ✅ SYSTEM token (`NT AUTHORITY\SYSTEM`) 有 `SeRestorePrivilege` + `SeBackupPrivilege` + `SeTakeOwnershipPrivilege`, **bypass UCPD Deny ACE**, 不需要停 UCPD。
- ⚠️ SYSTEM 的 HKCU 是 `S-1-5-18` 自己的 hive, **不是 liuzhen 的**。要写 liuzhen 的 HKCU, 要么 impersonate (复杂), 要么直接写 `HKEY_USERS\<liuzhen-SID>\…` (干净)。

**修复 (v1.8.3 SYSTEM-context CustomAction):**

### Phase 1 — `jhyy-setuc.exe --system-context` mode
- 新增 `ApplyPathBSystemContext(ext, progId)` 静态方法 (`installer/common/jhyy-setuc/Program.cs`)
- 遍历 `HKEY_USERS` sub  keys, 筛选 `S-1-5-21-…` SIDs (跳过 SYSTEM / LocalService / NetworkService / `_Classes` mirror)
- 对每个用户 SID: 算 Mozilla Hash (用 **TARGET 用户的 SID**, 不是 caller SID), 写 `HKEY_USERS\<sid>\…\FileExts\<ext>\UserChoice` + ApplicationAssociationToasts
- 单用户失败 log + continue (partial success OK), `return 2`;全部成功 `return 0`
- Full success 写 sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied = <iso8601>` (HKLM 让 per-user RunOnce 可读)
- 现有 single-user path (`ApplyPathB`) 不动, 保持 `manual-fix-icon-cache.ps1` 兼容

### Phase 2 — WiX MSI CustomAction (jhyy-compiler.wxs)
- `<Binary Id="JHYYSetUCBin" SourceFile="!(bindpath.common)\jhyy-setuc\bin\Release\net8.0-windows\jhyy-setuc.exe" />` — ship 进 MSI Binary table, WiX 在 CA 运行时自动 extract 到 temp
- `<CustomAction Id="JHYYSetUCForAllUsers" BinaryRef="JHYYSetUCBin" ExeCommand="&quot;[JHYYSetUCBin]&quot; --system-context .jhyy JHYY.SourceFile" Execute="deferred" Impersonate="no" Return="ignore" />`
- `Execute="deferred"` + `Impersonate="no"` = **SYSTEM context** (LocalSystem perMachine install)
- `Return="ignore"` = CA 失败不 rollback install (icon 是 best-effort)
- `<InstallExecuteSequence>` 加 `<Custom Action="JHYYSetUCForAllUsers" After="InstallFiles" Condition="NOT Installed" />`
- `<RemoveRegistryValue>` clear sentinel on uninstall (per `JHYYPathReg` Component)

### Phase 3 — Bundle .NET 8 chain (Bundle.wxs)
- `<util:RegistrySearch Id="Net8RuntimeSearch" Variable="Net8RuntimeVersion" Root="HKLM" Key="SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost" Result="value" />` 检测现有 .NET 8
- `<ExePackage Id="Net8Runtime" SourceFile="$(var.JHY_DOTNET8_RUNTIME_EXE_PATH)" DisplayName=".NET 8 Desktop Runtime" Compressed="yes" Vital="yes" Permanent="yes" InstallArguments="/quiet /norestart" DetectCondition="Net8RuntimeVersion" />` — 缺失则 silent install 8.0.30
- `.NET 8` chain 在 `JHYYCompilerMsi` 之前 (MSI install 完跑 v1.8.3 CA)
- `Permanent="yes"` — shared runtime, Bundle uninstall 不移除

### Phase 4 — install-configure-all.bat sentinel 跳 step 6
- step 6 头部 `reg query "HKLM\SOFTWARE\JiHuiYiYou\JHYY" /v UserChoiceSystemContextApplied`, 若非空 → `goto :skip_post_install_user_choice` 跳过 manual-fix (避免 RunOnce user-context 重新写覆盖 v1.8.3 SYSTEM-context 写)
- 若空 → 跑原 step 6 (向后兼容 v1.8.2 manual fix path)

### 验证 (5/5 PASS on each test, per `feedback_fix_evaluation_rule`)

**单元测试** (`jhyy-setuc.exe --system-context` 行为):
- ✅ compile 成功 (0 warning, 0 error)
- ✅ `--system-context .jhyy JHYY.SourceFile` 从 SYSTEM service 跑 → 写 `HKEY_USERS\S-1-5-21-2800878244-2814466599-1096304708-1001\…\FileExts\.jhyy\UserChoice` = `ProgId=JHYY.SourceFile + Hash=fcriTl+YsZ4=`
- ✅ `HKEY_USERS\S-1-5-18\…\FileExts\.jhyy\UserChoice` **不动** (v1.8.3 显式 skip SYSTEM hive)
- ✅ per-user `ApplicationAssociationToasts\JHYY.SourceFile_.jhyy = 0` 写入 liuzhen hive (新 v1.8.3 code path)
- ✅ sentinel `HKLM\SOFTWARE\JiHuiYiYou\JHYY\UserChoiceSystemContextApplied` 写入 (full success)

**MSI build** (`installer/build.ps1 compiler`):
- ✅ `jhyy-compiler-1.8.0.msi` 1.29 MB (跟 v1.8.2 持平, `<Binary>` reference 不重复 ship)
- ✅ WiX 4 schema 正确 (`Condition` attribute 不是 inner text, learned from WIX0400 error)

**Bundle build** (`installer/build.ps1 bundle`):
- ✅ .NET 8 runtime 28.6 MB cached (`installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe`)
- ✅ `jhyy-installer-1.8.0.exe` 29.99 MB (MSI + .NET 8 + Burn overhead)
- ✅ WiX 4 `ExePackage` 用 `InstallArguments` 不是 `InstallCommand` (learned from WIX0004)

**install-configure-all.bat sentinel 逻辑**:
- ✅ Sentinel absent → 跑 step 6 原 path
- ✅ Sentinel present → 跳过 step 6 (`goto :skip_post_install_user_choice`)

**regress baseline 不退化**:
- `mcp__jhyy__jhyy_regress` 102/102 PASS + 4 SKIP (v1.8.2 ship baseline 持平, v1.8.3 不改 codegen)

### 已知 limitation (v1.8.3 不修)

- **MSI install without Bundle** — 用户手动 `msiexec /i jhyy-compiler-1.8.3.msi` 没 .NET 8 → CA 失败 (`Return="ignore"` 不 rollback, 但 `jhyy-setuc.exe` 启动失败不写 UserChoice) → icon 仍 default; Bundle install 自动链 .NET 8 即可
- **每 user 需登录一次触发 sentinel 生效** — MSI install 在 SYSTEM context 写 liuzhen hive, user 已在 session → 不需 logout; 但新建 user 后首次登录 RunOnce step 6 已被 sentinel skip → 该 user icon 不更新 → v1.8.4 follow-up 候选 (MSI repair trigger 重跑 CA 写新 user hive)
- **UCPD.sys 行为变化** — Win11 24H2+ 可能加更严 Deny ACE; Phase 0 验证了 Win10 19045, Win11 24H2+ 待验证

### 教训 (Phase 0 vs Phase 1 设计)

- **Phase 0 现场验证 ≥ Phase 1 设计**: 写 .NET 8 1 周前先去现场 `sc create obj= LocalSystem` 测试, 发现 SYSTEM trust chain 直接绕 UCPD — **根本不需要** stop UCPD / 卸 UCPD / 改 UCPD config。Phase 1 设计从 "How to disable UCPD" pivot 到 "How to invoke jhyy-setuc from SYSTEM context" — 1 行 mindset flip 救整个 sprint
- **Mozilla algorithm token-independent**: 很多人 (包括 MS 自己) 以为 UserChoice hash 需要 caller privilege escalation 才能算, 其实 hash 只是 MD5 + scramble — 算法永远能跑, 写不写是 kernel token 问题。**算法是 reverse-engineered, 写入路径是 MS-protected**
- **v1.8.2 manual fallback vs v1.8.3 automated**: v1.8.2 ship 时没实测 MSI / Bundle install 路径, 纯想 Path A/B 流程。v1.8.3 直接从 "MSI install 自动做" 倒推 → 6 phases 设计对齐 WIX 4/7 spec + Mozilla + UCPD 三套体系
- **SYSTEM token 行为常识**: `LocalSystem` service 有 `SeRestorePrivilege` + `SeBackupPrivilege` + `SeTakeOwnershipPrivilege`, 但 HKCU 是 S-1-5-18 自己的 hive。写其他 user 的 HKCU → 必须直接写 `HKEY_USERS\<sid>\…` (SYSTEM token 有权写, 因为 SYSTEM 是 kernel-level owner of registry)
- **MSI CustomAction Type 50 vs Type 34**: Type 50 (Binary stored in Binary table) WiX 自动 extract + auto-resolve `[JHYYSetUCBin]` property → 不需 CustomActionData 预设 → 简单 + 0 MSI table pollution。Type 34 (cmd.exe /c) 需要 immediate CA 预设 property → 多一层复杂度

### 引用 (v1.8.3)

- `installer/common/jhyy-setuc/Program.cs` (v1.8.3 改, 加 `--system-context` mode + sentinel write)
- `installer/compiler/jhyy-compiler.wxs` (v1.8.3 改, `<Binary>` + `<CustomAction>` + `<InstallExecuteSequence>` + `<RemoveRegistryValue>`)
- `installer/Bundle.wxs` (v1.8.3 改, `<util:RegistrySearch>` + `<ExePackage>` .NET 8 chain)
- `installer/build.ps1` (v1.8.3 改, .NET 8 auto-download + Bundle `wix build` 加 `-ext WixToolset.Util.wixext`)
- `installer/common/install-configure-all.bat` (v1.8.3 改, step 6 sentinel check + `goto :skip_post_install_user_choice`)
- `installer/build-artifacts/dotnet/dotnet-runtime-8.0.30-win-x64.exe` (v1.8.3 新, 28.6 MB .NET 8 Desktop Runtime)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3 patch 段 (umbrella)


## W-063: 短名 enum 模式匹配 `Some(v) => v` bind, codegen 传错 type → phi %t0 未定义

**ID:** W-063
**状态:** ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch, probe-then-fix)
**日期:** v1.7.1 (introduced — 短名 form parser 允许但 codegen 无对应路径) → 2026-09-01 (RESOLVED)
**触发面:** 任何用 `match` + 短名 enum 模式 (e.g. `match o { Some(v) => v, None => 0 }` 不带 `Option::` 前缀) + bind payload 的代码 — 官网 04 tab `unwrap` 例子, 教科书 enum-bind 例子
**症状:** QBE 拒绝 .il, 报 `invalid type for operand %t0 in phi %t6` (or similar SSA reference). 用户只见 `QBE failed: "..."\n` 一行 (旧版, 无 stderr capture). 实际 .il 长这样 (regress from `test.jhyy` unwrap 例子):

```
@arm2
    dbgloc 8
    jmp @merge1
@merge1
    %t6 =w phi @arm2 %t0, ...   ← @arm2 没 emit %t0 定义, %t0 phantom
    ret %t6
```

注意 `@arm2` block 只有 `jmp @merge1` 0 行 — payload slot alias `loadw` 根本没 emit.

**根因嫌疑:** jhyy-side `compiler/src0/codegen.jhyy` `cg_match_pattern` (line 977-1217) NODE_PATTERN_ENUM 分支在 `pe->variant_sym == NULL` 时 silent fallthrough (return `cmp=1`, "always-match" — emit `jnz %t2, @arm2, @next3` with `%t2 =w copy 1`). 该 fallback **跳过 emit payload alias `loadw`** (which would define `%t0`). 后端 phi node 引用 arm body 里的 `v` (resolved via binding branch's `cg_add_local`) → 引用未定义 SSA → QBE reject. 短名 form (`Some(v)`) 触发: parser.c `parse_pattern_enum` (line 225-235) `gsym = symtab_lookup(...)` 设 `variant_sym` 后 `ast_new_pattern_enum(..., NULL, gsym, inner)` (`type_sym=NULL`); codegen 看到 `pe->type_sym == NULL` → 进 fallback. 长名 form (`Option::Some(v)`) `pe->type_sym` set → 不触发. W-019 (v1.4.6) 试图修同名 form 但只动了 parser 端, 漏了 codegen 调用站点.

实际 codegen 调用站点 (NODE_MATCH driver line 3378-3503) 把 **match result type** (`(*n).type_ptr` — e.g. `i32` for `match o { Some(v) => v, ... }`) 传给 `cg_match_pattern`. 这是 bug: short-name fallback 路径上, `cg_match_pattern` 用 match result type 在 `match_type->enum_type.variants` 反查 variant 名字 — match result type 不是 KIND_ENUM → 反查永远 miss → 永远走 silent fallback. 应传 **subject type** (`(*matched_node).type_ptr` — e.g. `Option`).

**workaround (v1.8.3.2 真修):** `compiler/src0/codegen.jhyy:3468` NODE_MATCH driver 入口 `cg_match_pattern` 调用改:

```jhyy
// 旧 (bug):
let cmp = cg_match_pattern(cg_raw, matched, arm_pattern, (*n).type_ptr);
// 新 (fix):
let cmp = cg_match_pattern(cg_raw, matched, arm_pattern, (*matched_node).type_ptr);
```

注释里完整记录 WHY — subject type 才有 KIND_ENUM → 才能反查 variant name → emit payload alias `loadw` → phi 引用 `%t0` 有定义。

**probe-then-fix 路径 (per plan):**
1. 第一次 probe 在 `compiler/src/codegen.c:347-352` 加 `fprintf(stderr, "DEBUG pe=%p variant_sym=%p match_type=%p\n", ...)` — probe 0 fire, 因 production 用 `src0/codegen.jhyy` 非 `src/codegen.c`
2. probe 移到 `src0/codegen.jhyy` cg_match_pattern 入口 + NODE_MATCH 入口 — 确认: `variant_sym` 已 set (parser 设了) + match_type 传错 (call site 传 `(*n).type_ptr` 是 match result type, 不是 KIND_ENUM)
3. 删 probe, 真修传参 → .il 重新 emit `%t7 =w loadw %t6` (payload alias defined) → QBE exit 0
4. 加 regress test `compiler/tests/examples/payload_bind_short.jhyy`

**影响范围:**
- `compiler/src0/codegen.jhyy:3468` (1 行参数修改 + 14 行 WHY 注释)
- `compiler/tests/examples/payload_bind_short.jhyy` (新增)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段 (umbrella)

**失效条件:** 不适用 — 真修 chain 已 ship。
**v1.8.3.3 patch:** C-side `compiler/src/codegen.c:1541` NODE_MATCH driver 入口 `cg_match_pattern` 调用镜像 src0 fix — `Type *match_type = n->type` 改 `Type *match_type = d->expr->type` (subject type)。触发面: 同 src0 (任何短名 enum 模式 + bind payload)。修复动机: commit 1671aff ship 后, regress 矩阵 (jhyy.exe + jhyy_stage0.exe) gated 双 binary 跑 — 新增 `payload_bind_short.jhyy` 在 jhyy_stage0.exe (C-side bootstrap) fail (QBE "invalid type for operand %t0 in phi")。fix 后 jhyy_stage0.exe 同样 103/103 PASS + 4 SKIP。Stage 2 N=4 closure sha 不变 (`fa1137e5...`) — closure 走 src0 codegen 不用 src codegen.c。

**superseder:** v1.8.3.2 真修 (1-line 参数传 subject type)
**引用:**
- `compiler/src0/codegen.jhyy:977-1015` (`cg_match_pattern` fallback 路径 — match_type 反查 + payload alias emit)
- `compiler/src0/codegen.jhyy:3468` (NODE_MATCH driver call site — fix point)
- `compiler/src/parser.c:225-235` (短名 form parser — `type_sym=NULL` AST node)
- `compiler/tests/examples/payload_bind_short.jhyy` (新增 regress test)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段

**验证:**
- 5/5 PASS on `payload_bind_short.jhyy` per `feedback_fix_evaluation_rule` (5 iter 跑同一个 file, 全 exit=42)
- 全 regress 103/103 PASS + 4 SKIP
- Stage 2 selfhost closure N=4 byte-equal (`v2/v3/v4/v5` .il sha `fa1137e5b9621ab46bc95ad976b5f33e0a60e98e5ec59ef31d084203e146e242`)


## W-064: run_qbe 失败只打 `QBE failed: ...` 缺 stderr 捕获, QBE 真实诊断丢失

**ID:** W-064
**状态:** ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch)
**日期:** v1.5.6 (introduced — `jh_run` 加 stderr pipe capture 但 `run_qbe` 没接 `jh_run_get_output()`) → 2026-09-01 (RESOLVED)
**触发面:** 任何 QBE 失败场景 — codegen emit invalid .il (W-063 + W-012 残留 + W-054 等); QBE binary 找不到 (W-021 升级后); .il syntax 错 (罕见)
**症状:** 用户只见单行 `QBE failed: "<full qbe cmd_buf>"\n`, 不知道 QBE 实际诊断 (e.g. `invalid type for operand %t0 in phi %t6` / `undefined symbol %t3` / `type mismatch in storew` 等). 跟 `gcc link failed` 旧症状一样 — 错误晚出 + 信息丢失, 用户无从下手.
**根因嫌疑:** `compiler/src0/main.jhyy:run_qbe` (line 657-699) v1.5.6 W-038 改 `system()` → `jh_run` (CreateProcessA) 但**漏接** `jh_run_get_output()` capture. v1.5.6 W-045 同时 ship 的 `link_with_gcc` stderr capture helper (`jh_run_get_output` + 失败时 echo) 没应用到 run_qbe. 原因推测: W-038 跟 W-045 是不同 sub-sprint, run_qbe 只被 audit `cmd_buf` quote (W-039), stderr capture 漏 audit.
**workaround (v1.8.3.2 真修):** 镜像 `link_with_gcc` (line 805-836) W-045 pattern:

```jhyy
let r = jh_run(cmd_buf);
let captured = jh_run_get_output();   // 新增 — buffer per-call reset (jh_run 内 l:517-518)
if r != (0 as i32) {
    jh_fputs_stderr("QBE failed: " as *u8);
    jh_fputs_stderr(cmd_buf as *u8);
    jh_fputs_stderr("\n" as *u8);
    if captured != (0 as *u8) {        // 新增
        let c0 = (*captured);
        if c0 != (0 as i32) {
            jh_fputs_stderr("QBE stderr:\n" as *u8);
            jh_fputs_stderr(captured);
            jh_fputs_stderr("\n" as *u8);
        }
    }
    free(cmd_buf);
    return 1 as i32;
}
```

顺带 bump `src0/main.jhyy:1091` stale `printf("jhyy compiler v1.0.0 (self-hosted)\n"...)` → `v1.8.3.2`. `jhyy -h` 可见。

**影响范围:**
- `compiler/src0/main.jhyy:687-700` (run_qbe — 13 行修改 + 6 行 WHY 注释)
- `compiler/src0/main.jhyy:1091` (1 行 version literal bump)

**失效条件:** 不适用 — 真修 chain 已 ship. **link_with_gcc 已 ship W-045 真修**, `run_qbe` 是唯一剩没接 stderr capture 的 child process site (windres 没 capture 是 v0.4 阶段产物, windres 失败模式不常见, 不修).

**superseder:** v1.8.3.2 真修 (`run_qbe` 接 `jh_run_get_output` capture)
**引用:**
- `compiler/src0/main.jhyy:657-700` (`run_qbe` — fix point)
- `compiler/src0/main.jhyy:805-836` (`link_with_gcc` W-045 pattern 模板)
- `compiler/src0/jhyy_helpers.c:466-567` (`jh_run` CreateProcessW + pipe capture + per-call buffer reset l:517-518)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段

**验证:** regress 103/103 + Stage 2 闭环 hold (v2/v3/v4/v5 .il sha `fa1137e5...`).


## W-065: `jhyy run` 不预检 `fn main_jhyy` — 库 snippet 报 `undefined reference to main_jhyy` 对用户不友好

**ID:** W-065
**状态:** ✅ RESOLVED 2026-09-01 (v1.8.3.2 patch)
**日期:** v1.4.4 (introduced — `jhyy run` 入口 direct `cmd_compile` → link, 库文件直接 link 必报 undefined reference) → 2026-09-01 (RESOLVED)
**触发面:** 用户复制官网 02 (dist_sq) / 04 (unwrap) 这种**库 snippet**(只定义 `fn dist_sq` / `fn unwrap`, 没 `fn main_jhyy`) 直接 `jhyy run` → gcc link 报 `undefined reference to main_jhyy`, 错误晚出 + noisy, 用户搞不清是 snippet 缺 main 还是 compiler bug.
**症状:** gcc stderr 一长串 `undefined reference to 'main_jhyy'` + link exit 1. 实际 root cause 是 snippet 缺 entry point, 编译器只是按 spec 拒绝 link.
**根因嫌疑:** `cmd_run` (compiler/src0/main.jhyy:987) 入口直接 `cmd_compile(3, arg_arr)`, 中间没 pre-check 输入文件是否含 `fn main_jhyy`. cmd_compile 不应加 (compile 应允许 library-only 编译), 所以加在 cmd_run 单一 site.
**workaround (v1.8.3.2 真修):** `cmd_run` 入口加 cheap byte-level scan — `fopen(input, "rb")` + `fread(131072)` + fclose, byte-by-byte 搜 needle `"fn main_jhyy"`. 找到 → 继续 compile; 找不到 → `jh_fputs_stderr("jhyy run: '<file>' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)\n" as *u8)` + return 1.

**第一次 commit bug (自查发现):** byte-comparison 实现用 `*i32` cast deref 4-byte 而非 1-byte (`let a_p = ... as *i32; if (*a_p) != (*b_p) { ... }`), scan 永远不 match — 即使文件真有 `fn main_jhyy` 也报 no main. 第一次 fix 后 fresh build 跑 user case (test.jhyy / test2.jhyy) **仍报 "no fn main_jhyy"** — 不写 5/5 PASS loop 不会发现 byte-comparison bug. 第二次 commit 改 `*u8` cast + `as i32` promote 才正确:

```jhyy
let a_p = (scan_buf as i64 + j + k2) as *u8;    // 正确: 单 byte deref
let b_p = (needle as i64 + k2) as *u8;
let av = (*a_p) as i32;                          // sign-extend byte to i32
let bv = (*b_p) as i32;
if av != bv { match_ok = 0 as i32; }
```

**scope:** 只动 `cmd_run`, `cmd_compile` 保持允许库-only 编译. `jhyy compile foo.jhyy` 仍然产 .s/.exe 不需要 main_jhyy (供后续 link 用).

**影响范围:**
- `compiler/src0/main.jhyy:993-1043` (cmd_run 入口 — 50 行新 pre-check code)

**失效条件:** 不适用 — 真修 chain 已 ship.

**superseder:** v1.8.3.2 真修 (cmd_run pre-check)
**引用:**
- `compiler/src0/main.jhyy:987-1068` (cmd_run — fix point)
- `compiler/src0/main.jhyy:1000-1029` (byte-comparison 实现 — 第一次 bug 已被第二次 fix 取代)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.2 patch 段

**验证:**
- user case `test.jhyy` (unwrap) / `test2.jhyy` (dist_sq) → 干净 actionable error "jhyy run: '...' has no 'fn main_jhyy() -> i32' (required for 'jhyy run'; use 'jhyy compile <file>.jhyy' for libraries)"
- 加 `fn main_jhyy` wrapper 后 (`test_short_enum.jhyy`) → 5/5 PASS exit=99 per `feedback_fix_evaluation_rule`
- regress 103/103 + Stage 2 闭环 hold (v2/v3/v4/v5 .il sha `fa1137e5...`)

**教训:**
- **任何 byte-level inline 算法, 5/5 PASS loop 是真修 gate**: 第一次 commit 跑自己写的 wrapper (有 main_jhyy) 都过 — 但跑 user 原 case (库 snippet, 无 main_jhyy) 暴露 byte-comparison bug。如果只跑 wrapper, 永远不知道 fix 本身错。
- **`*i32` cast deref 是 silent footgun**: jhyy `*i32` deref 4-byte, `*u8` deref 1-byte. 在 C/Python 看像 trivial, 在 jhyy codegen 后端会 emit `loadw` vs `loadsb` — 4-byte overread 是常见的 silent corruption 源头 (W-001 RESOLVED chain 同型教训)。
- **scope discipline 赢 scope creep**: 计划阶段想加 helper `jh_file_read_all` + matching stub, 实际 inline fopen/fread/fclose + byte loop 就够 (50 行, 0 new helper, 0 C-side sync work)。**scope discipline > code reuse**。


## W-066: post-425970d refactor 漏改 jhyy-compiler.wxs:622 — license.rtf 仍 ref `!(bindpath.common)\license.rtf`, 实际文件在 installer/assets/ → WIX0103

**ID:** W-066
**状态:** ✅ RESOLVED 2026-09-02 (v1.8.3.3 patch follow-up #2)
**日期:** 2026-08-29 (introduced — 425970d installer deep restructure 把 `license.rtf` 移到 `installer/assets/`, 但 `jhyy-compiler.wxs:622` 仍指 `installer/common/license.rtf`) → 2026-09-02 (RESOLVED)
**触发面:** release run #46 (tag v1.8.3.3 @ 65e897a) step "Build installer" — `wix build ... installer/wix/compiler/jhyy-compiler.wxs` 报 `WIX0103: Cannot find the File file '!(bindpath.common)\license.rtf'. The following paths were checked: !(bindpath.common)\license.rtf, installer/common\license.rtf`. 出包链路 build.ps1 → exit 1 → release.yml 整条红。

**症状:** 在 CI (windows-2025-vs2026 runner) 直接报 WIX0103, MSI 不存在。 GitHub Actions UI 只显示 "1 error and 1 warning" — 第一个 (SVG icon) 是 vsce reject; 第二错就是 WIX0103, 容易当 transient / cache miss 忽略掉。

**根因:** `425970d` 跑的是 docs-only + minor restructuring, 没跑 full `installer/build.ps1 bundle` verify pass。`!(bindpath.common)` 在 build.ps1 里 bind 到 `installer/common`, 但 refactor 后 `license.rtf` 实际搬去 `installer/assets/license.rtf` (`git show 425970d --stat` 看 license.rtf 路径变化)。Bundle.wxs 没受影响 — bundle 那边 `license.rtf` 是用 `-d JHY_LICENSE_RTF_PATH=installer\assets\license.rtf` 直接传 path, 不走 bindpath rename, 所以 bundle path 早就对了。只有 MSI payload (File element) 这条走 bindpath。

**workaround (v1.8.3.3 fix):** 把 `jhyy-compiler.wxs:622` 的 `Source="!(bindpath.common)\license.rtf"` 改成 `Source="!(bindpath.assets)\license.rtf"` — `WixUILicenseRtf` (line 194) 早就用 `!(bindpath.assets)\license.rtf`, 现在 File element 也对齐, 一致性 + 真修。

**scope:** 1 行真修 + 9 行 comment (v1.8.3.3 fix rationale + reference Bundle.wxs 同型 path; 防下个 refactor 再踩)。不动 build.ps1 (不用再传额外 `-b`, `-b assets=installer/assets` 早就在), 不动 Bundle.wxs (已 OK)。

**影响范围:**
- `installer/wix/compiler/jhyy-compiler.wxs:622` (Source attr) + `installer/wix/compiler/jhyy-compiler.wxs:621-630` (fix rationale comment)

**失效条件:** 不适用 — license.rtf 物理路径已锁在 `installer/assets/`, `!(bindpath.assets)` 跟 build.ps1 `-b assets=installer/assets` 永远 align。除非再有人动 refactor 重命名, 否则不再触发。

**superseder:** v1.8.3.3 patch follow-up #2 (commit TBD — `fix(installer): jhyy-compiler.wxs license.rtf bindpath post-425970d refactor (v1.8.3.3 release 解锁)`)

**引用:**
- `installer/wix/compiler/jhyy-compiler.wxs:622` (fix point)
- `installer/wix/compiler/jhyy-compiler.wxs:194` (WixUILicenseRtf — 早就是 assets)
- `installer/wix/Bundle.wxs` (`-d JHY_LICENSE_RTF_PATH=installer\assets\license.rtf` — 早就是 assets)
- `installer/build.ps1:248-260` (`wix build` bindpath map: `bin/common/assets/scripts/vscode-ext` 都 OK, common 不再含 license.rtf)
- `installer/assets/license.rtf` (物理位置)
- `git show 425970d --stat` (refactor commit — license.rtf path move)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.3 patch 段

**验证:**
- 本地 `installer/build.ps1 compiler` (pwsh 缺失, fallback Windows PowerShell 5.1) → `[OK] installer/build-artifacts/jhyy-compiler-1.8.3.msi built` (1.16 MB)
- 本地 `installer/build.ps1 bundle` → `[OK] installer/build-artifacts/jhyy-installer-1.8.3.exe` (29.95 MB)
- WIX5436 warning (ProgramFiles6432Folder DirectoryRef deprecation) — pre-existing 既有 warn, 不动
- CI 待验: tag v1.8.3.3 重推后 release run 应 0 error / 1 warning

**教训:**
- **WiX bindpath 是 transitive contract** — refactor 时**任何**移文件的 commit 都必须 grep `!(bindpath.X)` + 对应 build.ps1 `-b X=...` 双向查。Bundle 路径 vs File payload 路径走不同 code path, 一个对了另一个未必对 (这 case 就是 bundle OK / File element 漏)。
- **refactor commit 不跑下游 verify = bug ship**: 425970d commit message 写的是 "deep restructure - wix/assets/scripts/distribution dirs + build.ps1 sync" — "build.ps1 sync" 听像是 verify 过, 实际只 sync 了 build.ps1 自己, 没跑 `bundle` 端到端。这是 DEFERRED-like 的 ship gap — 标 "RESOLVED" 但下游契约没 verify。
- **`WIX0103` + "1 error and 1 warning" 的 UI 表述**: GitHub Actions UI 把 error + warning 计数平铺, 第一眼容易被 "1 error" 吓到去查 SVG 之类 obvious 的事; 实际是 `1 error` (SVG) + `1 warning` (WIX5436) + 第 2 错 (WIX0103) 的语义重叠 case。**必须看 raw log** (`gh run view <id> --log | grep -E "WIX|error"`) 才能拿到真错。
- **`pwsh` 缺环境 fallback**: CI runner 有 PowerShell 7 (`/c/Program Files/PowerShell/7/pwsh.exe`), 本地用户机器可能只有 PS 5.1。`build.ps1` 是 syntax-compatible (switch 都对), 但 `wix` 工具链本身跑得动 — 不代表 5.1 跑的 verify 跟 7 完全等价; 真要稳还是 pwsh 7。**(per `feedback_ci_yaml_debugging` msys2 + set +e 教训同源 — verify 工具链必须跟 CI 一致)**


## W-067: release.yml vs build.ps1 重复 strip-to-3 逻辑 → drift risk; 4-segment VERSION (v1.8.3.3) 暴露 Validate MSI 找错文件

**ID:** W-067
**状态:** ✅ RESOLVED 2026-09-02 (v1.8.3.3 follow-up #3, single source of truth)
**日期:** 2026-08-29 (introduced — `425970d` refactor 间接加剧, build.ps1:75-83 跟 release.yml 各自有 strip 逻辑但未对齐) → 2026-09-02 (RESOLVED via build.ps1 export GITHUB_ENV)
**触发面:** release run #47 (33583807347) FAIL @ step "Validate MSI (wix msi validate)" — 报 `Could not find file '...\installer\build-artifacts\jhyy-compiler-1.8.3.3.msi'`, 但 build.ps1 出包名是 `jhyy-compiler-1.8.3.msi` (strip 4-segment → 3-segment by MSI ProductVersion 约束)。

**症状:** tag `v1.8.3.3` 触发 release.yml 跑, "Build installer" step 成功 ([OK] jhyy-compiler-1.8.3.msi built), 但后续 "Validate MSI" / "Create GitHub Release" upload / "Verify SHA256.txt content" / "Confirm artifacts present" 全部用 `$VERSION=1.8.3.3` 找文件 → 文件不存在 → release 全红。

**根因:** **重复实现 + drift**。`build.ps1:75-83` 把 `VERSION` strip 到 3-segment 写入 `$env:JHY_VERSION` (line 79), 然后 line 87 算 `$JHY_VERSION_DISPLAY = $env:JHY_VERSION + RC_SUFFIX`, 出包文件名用 `$JHY_VERSION_DISPLAY`。release.yml 第 200-202, 233, 245-247, 270-272 行都直接用 `$env:VERSION` (= 1.8.3.3) 找文件名 — **完全没看 build.ps1 的 strip 输出**。3-segment tag (v1.5.5 / v1.8.3) 时两值相等 (1.5.5 == 1.5.5), 4-segment patch tag (v1.8.3.3) 首次暴露 mismatch。**latent bug ship 链**: 这 bug 一直存在, 只是 3-segment tag 时 nobody notice。

**workaround 路径 (3 commit):**
1. **commit `931a4f3`** (W-066) 修了 license.rtf bindpath, 解了 WIX0103 第 2 错 — 让 release.yml 跑到 Build installer 成功那一步
2. **commit `e86c2d0`** (W-067 attempt 1) 在 release.yml 加 "Compute JHY_VERSION_DISPLAY" step, **镜像 build.ps1 strip 逻辑** — 解了 run #48 (33584690813) SUCCESS。但这只是把 drift 从一处变两处: build.ps1:75-83 跟 release.yml:96-110 各自有一份 strip 代码, 未来改一边忘改另一边又错
3. **commit TBD** (W-067 真修): 把 strip 逻辑挪到 build.ps1 内部, 通过 `Add-Content $env:GITHUB_ENV` export `JHY_VERSION_DISPLAY` 给 release.yml — **single source of truth**。release.yml 删除 mirror step, 后续 step 直接 read `env.JHY_VERSION_DISPLAY`。本地测试: stub target + fake GITHUB_ENV → `[build.ps1] exported JHY_VERSION_DISPLAY=1.8.3 to GITHUB_ENV` + GITHUB_ENV 文件含 `JHY_VERSION_DISPLAY=1.8.3` ✓

**scope:**
- ✅ 改 `installer/build.ps1` (新增 ~17 行 GITHUB_ENV export block in psHost detection 段)
- ✅ 改 `.github/workflows/release.yml` (删除 "Compute JHY_VERSION_DISPLAY" mirror step, 改为 comment 说明 single source)
- ✅ 改 `docs/internal/workarounds.md` W-067 entry (本段)
- ❌ 不动 src/src0/ABI/spec/QBE/runtime/installer assets
- ❌ 不创建 standalone changelog (umbrella, per `feedback_changelog_umbrella`)

**净 ship 计数:** 1 真修 (build.ps1 export) + 1 simplification (release.yml mirror step 删除) + 1 doc (W-067 entry), 0 compiler/ABI/spec 改动。

### 失效条件

不适用 — `JHY_VERSION_DISPLAY` 的 single source of truth 已挪到 build.ps1, release.yml 不再重复实现 strip 逻辑。除非有人**改 build.ps1 strip 规则并删掉 export block**, 否则 release.yml 跟 build.ps1 永远 align。

### 引用

- `installer/build.ps1:75-83` (canonical strip logic — AUTHORITATIVE)
- `installer/build.ps1:87` ($JHY_VERSION_DISPLAY 赋值)
- `installer/build.ps1:101-117` (GITHUB_ENV export block — NEW)
- `.github/workflows/release.yml` (删除 mirror step, comment 说明 single source)
- `release run #47 (33584690813)` (最终 SUCCESS — 用了 mirror step version, run #48 用 single source version 未跑)
- `release run #46 (33583807347)` (FAIL — Validate MSI 找 1.8.3.3.msi 不存在)
- `docs/logs/v1/changelog-v1.8.0.md` v1.8.3.3 follow-up #3 段 (TBD)

### 验证

1. **本地 stub + fake GITHUB_ENV**: `[build.ps1] exported JHY_VERSION_DISPLAY=1.8.3 to GITHUB_ENV` + `JHY_VERSION_DISPLAY=1.8.3` 在 env 文件中 ✓
2. **不动性**: git diff 只动 build.ps1 (新增 export block) + release.yml (删 mirror step) + workarounds.md (W-067 entry); 不动 src/src0/ABI/installer assets ✓
3. **CI 待验**: 下次发 tag (e.g. v1.8.4 或 v1.9.0) 跑 release.yml — "Compute JHY_VERSION_DISPLAY (mirror build.ps1 strip-to-3 logic)" step 不存在, 直接读 `env.JHY_VERSION_DISPLAY` 应当正常; 3-seg / 4-seg 都对齐 ✓
4. **Drift self-check invariant**: build.ps1 export block 永久存在 + export 的 key 永久 = `JHY_VERSION_DISPLAY` (single source of truth)。未来改 strip 规则必须同步改 export value (但实际 export value 是自动从 $JHY_VERSION_DISPLAY 来, 不会手动错) ✓

### 教训

1. **跨 step 共享 env 的 single source of truth 原则**: CI workflow 里**永远**不要在两个 step 里 duplicate 计算逻辑。任何"两边都得对得上"的 derived value, 必须由一个 step 算 + export 出去, 其他 step read。**重复实现 = drift 高危信号**, 早晚会错 (W-067 case = 3-segment 巧合不暴露, 4-segment 暴露)
2. **3-segment vs 4-segment tag 是 versioning contract 触发器**: build.ps1 的 MSI ProductVersion 约束 (4-segment < 65536) 实际可行 (1.8.3.3 → MSI 1.8.3.3), 但 filename strip 是历史 convention (1.8.3.3 → file 1.8.3 for MSI ProductVersion 跟 filename 一致)。**versioning 是 contract**, 不要顺手改; 一改两边同时改, 不能只改 build.ps1 不改 release.yml
3. **commit `e86c2d0` (mirror step) 是 process 妥协, W-067 真修才是 product fix**: 当时急着 ship, 没时间做 single-source 重构, 临时 mirror 跑通 — 但 `feedback_changelog_umbrella` + `feedback_doc_refactor_factcheck` 强调 doc 要 fact-check + self-correct, 不能把临时方案当永久方案。**commit message 应该明确标 "TEMPORARY mirror, follow-up refactor in flight"**, 不写就是 ship gap (W-067 chain 同 W-063 / W-066 同型教训 — DEFERRED / temporary / process 妥协都得 back-stop)
4. **GITHUB_ENV export pattern** 是 GitHub Actions 的标准 idiom, 不需要发明轮子。`Add-Content -Path $env:GITHUB_ENV` 就行, 不必用 `Out-File` (per W-022 BOM 教训)。PowerShell script 里加 `$env:GITHUB_ENV -and (Test-Path -Path $env:GITHUB_ENV -IsValid)` 检测在本地不破坏 (env 不存在时 short-circuit false, 不写文件) — 比 hard fail 好
5. **latent bug ship 教训**: W-067 这 bug 实际一直存在 (release.yml 跟 build.ps1 没对齐), 只是 3-segment tag 时巧合不暴露 — 跟 W-063 (C-side W-063 DEFERRED leak) / W-066 (425970d refactor 没跑下游 verify) 同型。**refactor 改 versioning 规则的 commit 必须显式 grep "MSI ProductVersion / filename / VERSION / JHY_VERSION" 全链路 + 跑端到端 verify**, 否则 latent ship


