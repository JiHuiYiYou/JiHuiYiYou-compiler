# installer/release-notes/ — 每版 release note 的「主要改动」正文

## 为什么单独放一个目录

`installer/changelog-template.md` 是 **release note 的模板**:它只放**跟版本无关**
的部分(安装 / 验证 / 卸载 / 已知问题 / 完整 changelog 链接 / 第三方包管理)。

**每版的「主要改动」在** `installer/release-notes/<版本号>.md` —— release.yml 生成
release body 时把那个文件的内容塞进模板的 `${MAIN_CHANGES}` 占位符。

以前模板里写死的是**上一版**的正文 ⇒ 每发一版都要手改模板 ⇒ 迟早有一次发出去的
release note 描述的是**上一版**的东西。

## 规则

| 规则 | 说明 |
|---|---|
| 文件名 = 版本号 | `4.1.2.md`(RC 复用正式版:找不到 `<ver>-rc1.md` 就退回 `<ver>.md`) |
| 缺失 = 发版失败 | release.yml 在生成 release body 时找不到文件 ⇒ **直接 exit 1** |
| 正文是人写的 | 机器**不编** release note —— `bump_version.py set` 只建一个 stub |
| 往前的版本不用删 | 历史版本的正文留在仓里 ⇒ 审计轨迹 |

## 新建一版时

```bash
python scripts/dev/bump_version.py set 4.1.3   # 自动建 installer/release-notes/4.1.3.md 的 stub
# ... 把 stub 里的 TODO 换成这一版真正改了什么的正文 ...
```

## 交叉引用

- 版本号本身的自动化(不是这个目录):[`docs/internal/build.md`](../../docs/internal/build.md) § 版本号自动化
- 脚本:[`scripts/dev/bump_version.py`](../../scripts/dev/bump_version.py)
