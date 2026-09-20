# docs/internal/ — Claude Code 项目指令

本文件是 `docs/internal/` 子目录的局部 Claude Code 指令。**只在 Claude Code 工作目录为 `docs/internal/` 或父目录加载 `workarounds.md` / 本目录其他文件时加载**。

`docs/internal/workarounds.md` 是项目 workaround 唯一权威登记。**任何 .jhyy / .c / 编译相关 workaround / 防御性代码注释都必须在这里留 entry**（per `feedback_document_workarounds_in_docs`）。

## 1. 状态枚举（5-state enum）

workarounds.md 每个 entry 顶部 `**状态:**` 行的 `<STATUS>` 字段必须为以下 5 个之一：

| 状态 | 触发条件 | 转换路径 |
|------|---------|---------|
| `ACTIVE` | 真 bug 在生产代码，fix 未 ship | `→` RESOLVED（fix ship）/ SUPERSEDED（新 workaround 取代）/ DEFERRED（推后续 sprint） |
| `RESOLVED` | Fix ship + regress verified + D43 closure hold | terminal（entry 保留历史） |
| `SUPERSEDED` | 被新 workaround 取代 OR 不是 workaround（e.g. canonical pattern / 已迁 conventions.md） | terminal，body cross-ref 取代者 |
| `DEFERRED` | 决定不在当前 sprint 修，但 bug 真实，caption 必填版本目标 | `→` ACTIVE（sprint 拾起）/ RESOLVED（fix ship） |
| `INVALID` | 归档时误判，后确认是 test artifact | terminal，entry 保留审计 trail |

历史 10+ ad-hoc label（`PARTIAL` / `FULL CLOSED` / `DEFERRED` / `INVALID` / `PAUSED` / `DOCS` / `PARTIALLY CLOSED` / `ENV-ONLY` / `STABLE-PRODUCTION` / plain `RESOLVED` 等等）v2.13.5 ship 后**全部不再使用**。若发现新 ad-hoc label 出现，先在 sprint plan 登记映射再 ship。

## 2. 状态行 schema（6-field, no emoji）

`workarounds.md` 每个 H2 entry 顶部的 `**状态:**` 行严格 6-field 格式：

```
**状态:** <STATUS> <verb> YYYY-MM-DD (vX.Y.Z) — <caption, ≤120 chars>
**Backfilled:** YYYY-MM-DD (original W-NNN reference)   // 仅补登条目
**Filed-by:** <author | audit-flip-vN.N.N | patch-C2>   // 可选
```

字段约束：

- `<STATUS>` 必须为 5 态枚举之一（见 § 1）
- `<verb>`：`ACTIVE` / `DEFERRED` / `INVALID` 用 `since`；`RESOLVED` / `SUPERSEDED` 用 `closed`
- 日期格式 `YYYY-MM-DD`
- 版本号 `(vX.Y.Z)` 必填（引入或闭合版本）
- caption `≤120` 字符，**no emoji**，no commit hash inline（commit refs 在正文）
- `**Backfilled:**` 仅补登条目使用，引用 original W-NNN
- `**Filed-by:**` 可选，author handle 或 audit-flip handle

## 3. Backfilled 规则（锁死）

适用场景：v2.13.5 refactor 时新增的 entry（之前漏登 / 后期发现需补登 / audit-flip 过程中浮现的新条目）。
1. 拿下一个可用 W-NNN（不重用旧编号，见 § 4）
2. `**Backfilled:** YYYY-MM-DD (original W-NNN reference)` 字段必填，引用追溯到原 workaround 编号或 commit
3. `**Filed-by:** <handle>` 字段必填（handle 例：`patch-C2` / `audit-flip-v2.13.4`）
4. Body 必须含 1-2 段 RCA 总结 + commit sha 引用，不能仅靠状态字段行追溯
5. 索引表里 60 行 retention：补登条目**不删除**——即使后续 audit-flip 改 status，body 保留追溯 evidence

## 4. 编号规则（锁死）

W-NNN 永远递增，**绝不重用**。任何新 workaround 必须拿下一个可用 W-NNN。

| 类型 | 格式 | 用途 |
|------|------|------|
| 主编号 | `W-NNN` | 单 workaround 单元 |
| 子编号 | `W-NNN.M` | 父 entry 的第 M 个独立 sub-bug，独立 5-state status |
| 反模式（历史） | 多个 H2 entry 共用同一 `W-NNN` | **禁止**；v2.13.5 已 flip `W-074.6` / `W-074.7` 6+1=7 个 dup entry → `W-075`..`W-081` |

历史违规案例（仅参考，**不再发生**）：
- W-074.6 双 entry（line 5170 + 5469，2 dup，v2.13.5 flip 单一编号）
- W-074.7 双 entry（line 5555 + 6194，1 dup，v2.13.5 flip 单一编号）

补登允许 reorder（按 ship 日期 / RCA 簇内逻辑排序），但 W-NNN 必须 unique + monotonic。

## 5. 登记纪律

任何 workaround / 防御性代码 / 已 ship 但未 git-blame-clean 的 code path **必须** 留 entry。

触发登记的场景：

| 场景 | 登记位置 | 状态 |
|------|---------|------|
| .jhyy / .c 代码里有 defensive guard / sentinel / 异常路径 | `workarounds.md` 新 entry | 通常 `ACTIVE` |
| 已 ship 的 fix，留下历史 RCA 文档 | `workarounds.md` 新 entry | `RESOLVED` |
| Fix 推到后续 sprint，当前 sprint 不修 | `workarounds.md` 新 entry | `DEFERRED`（caption 必填版本目标） |
| 归档时误判为 bug，后确认是 test artifact | `workarounds.md` 新 entry | `INVALID`（保留 audit trail） |
| 发现 code 中已有 workaround 注释但未登记 entry | **Backfilled 补登**（§ 3） | 视当时实际状态 |
| Canonical pattern（设计如此，不是 bug） | 迁 docs/internal/conventions.md | 不进 workarounds.md（`SUPERSEDED` 残留仅用于跨 sprint audit trail） |

登记检查清单（写 entry 前必跑）：
1. **W-NNN 唯一**：用 grep / Read 检查 `## W-{cand}:` 不存在
2. **status 枚举合规**：5 态之一（§ 1）
3. **verb 正确**：since / closed per status（§ 2）
4. **caption ≤ 120 char**，no emoji，no commit hash inline
5. **body 含 RCA 段**（最少：症状 / 根因 / workaround / 影响范围 / 失效条件）
6. **引用真实 commit sha**（不是 `<TBD>` 或 `commit TBD`，除非真 ship 还未确定）
7. **索引自动重建**：写完后跑 `python scripts/dev/v2_13_5_rebuild_index.py docs/internal/workarounds.md docs/internal/workarounds.md` 重建索引表

## 6. example entry

完整 6-field + body 模板（v2.13.5 之后唯一允许格式）：

```markdown
<a id="w-NNN"></a>
## W-NNN: <简短标题，≤60 chars>

**状态:** <STATUS> <since|closed> YYYY-MM-DD (vX.Y.Z) — <caption, ≤120 chars, no emoji>
**Filed-by:** <author | audit-flip-vN.N.N | patch-C2>   // 可选, 补登必填
**Backfilled:** YYYY-MM-DD (original W-NNN reference)   // 仅补登
**日期:** <ACTIVE 起日期> → <RESOLVED/SUPERSEDED/INVALID 收日期>

**触发面:** <文件 + 行号 + 触发条件>

**症状:**
- <可观测的现象 / 报错信息>

**根因:**
- <1-3 句 RCA>

**workaround:**
<代码片段或绕过方案说明>

**影响范围:** <哪些用户 / 哪些场景触发>

**失效条件:** <workaround 不再需要的前置条件>

**superseder:** <新编号 / plan 文件引用>   // SUPERSEDED entry 必填

**引用:**
- 源码注释 `<file>:<line>`
- commit `<sha>` (<ship date>)
- plan: `docs/plans/vX/vX.Y.Z-plan.md`
```

完整示例见 workarounds.md 中任意 RESOLVED entry（如 W-001 / W-070）。

## 附录：自动化工具

v2.13.5 ship 时同 ship 了 4 个 scripts/dev/v2_13_5_*.py 工具脚本，登记新 entry 时跑：

| 脚本 | 用途 |
|------|------|
| `v2_13_5_rewrite_workarounds.py` | emoji-laden status line → 5-state enum 批量重写（仅 1 次性，已 ship 后不再用） |
| `v2_13_5_insert_anchors.py` | 给每个 H2 前面插入 `<a id="w-NNN"></a>` 短锚（仅 1 次性） |
| `v2_13_5_rebuild_index.py` | 重建 `## 索引` 表（写完新 entry 必跑） |
| `mcp__jhyy__jhyy_workarounds` | MCP 实时查 W-XXX 状态（不走 grep / Read） |

后续登记新 entry 唯一需要跑的脚本是 `v2_13_5_rebuild_index.py`。