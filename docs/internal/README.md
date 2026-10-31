# docs/internal — 仓内文档索引

> **本文件是「有哪些文档、各自管什么、什么时候读」的索引。**
> agent 的本地提示词（仓库根 `CLAUDE.md`，不入仓）指向这里。
>
> 想知道**当前是什么状态** ⇒ 去 [`docs/internal/FACTS.md`](FACTS.md)，不要在这里找。

---

## 文档地图

| 文档 | 职责 | 什么时候读 |
|---|---|---|
| [`docs/internal/FACTS.md`](FACTS.md) | **事实单一真相源** —— 版本 / 回归数 / ACTIVE 数 / 产物尺寸 / v4.x 排期 / OS-N 映射 / 目标三元组 | 任何时候要引用一个「会变的数字」 |
| [`docs/internal/workarounds.md`](workarounds.md) | workaround 台账（**永不归档**）—— 每个 workaround 的触发条件 / 绕法 / 根因 / 状态 | 改编译器之前；怀疑某个「已知问题」时 |
| [`docs/abis/jhyy-lang-spec-v4.0.0.md`](../abis/jhyy-lang-spec-v4.0.0.md) | **语言规范**（锁定）—— 语法 / 语义 / 附录 B 已知限制 | 写或读 `.jhyy` 代码时 |
| [`docs/abis/jhyy-abi-v4.0.0.md`](../abis/jhyy-abi-v4.0.0.md) | **ABI 白皮书**（锁定）—— 类型布局 / 调用约定 | 碰 FFI / struct 传参 / 跨平台时 |
| [`docs/abis/jhyy-binary-format-v1.0.0.md`](../abis/jhyy-binary-format-v1.0.0.md) | `.jhyynb` 二进制格式（**设计稿，未实装**） | 做 OS 线 / `.jhyynb` 时 |
| [`docs/plans/v4/`](../plans/v4/) | **当前计划线**（v4.x）—— 每格一份 `vX.Y.Z-plan.md` | 启动一个新 sprint 前 |
| [`docs/coordination/`](../coordination/) | 跨项目设计基线（编译器侧 / OS 侧各一份终版）—— 跨边界的唯一依据 | 动 OS 相关设计前 |
| [`docs/perf/self-backend-baseline-2026-10-29.md`](../perf/self-backend-baseline-2026-10-29.md) | 现行性能基线（帧尺寸 / 访存占比 / 回归比） | 做性能相关改动前 |
| [`docs/internal/build.md`](build.md) | 构建 / 运行 / 工具链 / 门 / 版本号自动化 | 第一次在本机把这套东西跑起来 |
| [`docs/internal/architecture.md`](architecture.md) | 编译器架构速览（流水线 / 模块图 / 自举机制） | 要改 codegen 或搞懂 emit 路径时 |
| [`docs/archive/`](../archive/) | 历史归档（changelog / 旧计划 / 旧性能 / 审计报告） | 想追溯「当初为什么这么定」时 |

仓外：

| 文档 | 职责 |
|---|---|
| `README.md` / `README.zh-CN.md` | 仓库门面（**两份，改动必须同步**；英文 + 中文镜像） |
| `CHANGELOG.md` | 对外变更日志 —— **每版一行**；逐轴详细记录在 `docs/archive/logs/` |
| `CONTRIBUTING.md` | 对外贡献指南 —— 怎么提 issue / 怎么开 PR / 有哪些门 |
| 仓库根 `CLAUDE.md` | agent 本地提示词 —— **恒为真**的知识索引，**不入仓** |
| `.claude/working-rules.md` | 内部工作规约（提交身份 / 验证纪律 / Git 安全 / 文档措辞 / 台账纪律 / jhyy 特有规则）—— **不入仓** |

---

## 维护规则

1. **会变的数字只写在 `docs/internal/FACTS.md`**，其它地方引用，不复述。
   `scripts/dev/docs_facts_check.py` 会对拍。
2. **每个目录不再各放一个 README** —— 索引集中在 `docs/internal/README.md`（本文件）
   与 `docs/archive/README.md`。
3. **历史进 archive，不删**（git 历史也留着，但 archive 里的文件是可读的）。
4. **文档里的路径引用按「相对当前文件」写** —— 文件搬位时要一起改。
   改完跑 `python scripts/dev/docs_facts_check.py`（含断链检查）。
5. **只用简体中文，禁止繁体**。
6. **一份文档一种语言**：对外门面（`README.md` / `CONTRIBUTING.md` / `CHANGELOG.md`）**英文**，
   中文门面只有 `README.zh-CN.md`；仓内文档（`docs/**`）**中文**。
   **同一份文档里不许中英混写** —— 英文文档里的中文注释 / 中文 mermaid 标签 / 中文目录树
   注释 = 门面在骗人。
