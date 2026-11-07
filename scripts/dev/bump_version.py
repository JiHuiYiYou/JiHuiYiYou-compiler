#!/usr/bin/env python3
"""版本号自动化 —— 一条命令把全仓的版本串刷成新的,不再靠手改。

## 为什么需要这个

版本号散在**仓库的不同角落、多种格式**里,而其中两处是**编译期烘进产物**的:

| 位置 | 格式 | 谁改 | 为什么不能手改 |
|---|---|---|---|
| `VERSION` | 纯文本 | **真相源** | —— |
| `compiler/src0/main.jhyy` | jhyy 源码里的字符串字面量 | 脚本 | 改完**必须重编自举产物**(`make`),忘了就是"二进制比源旧" |
| `installer/assets/license.rtf` | RTF | 脚本 | MSI 的 EULA 里显示的版本 |
| `installer/distribution/scoop/jhyy.json` | JSON | 脚本(+hash 要 post-build 填) | 手改 JSON 容易破格式 |
| `installer/distribution/winget/.../JHYY/<ver>/*.yaml` | YAML(**目录名也带版本**) | 脚本(+hash 要 post-build 填) | 目录名 / 3 个字段 / URL 里的版本要同时改 |
| `README.md` / `README.zh-CN.md` | Markdown(shields.io 徽章 URL) | 脚本 | 徽章是**读者第一眼看到的版本号** —— 它漂了 = 门面在骗人 |
| `docs/archive/logs/v4/changelog-v4.0.0.md` | Markdown | 脚本插 stub,人写正文 |
| `installer/release-notes/<ver>.md` | Markdown | 脚本建 stub,人写正文(release.yml 的 `${MAIN_CHANGES}` 从这儿取) | — |

漏改任何一处的后果都一样:**tag 上写着 v4.1.2,装出来的编译器自报 v4.1.1**。
本脚本把这件事变成一条命令 + 一道门。

## 用法

```bash
# 1. 刷版本号(改 VERSION + 上面表格里的每一处;hash 置为待填占位)
python scripts/dev/bump_version.py set 4.1.2

# 2. 重编自举产物 —— main.jhyy 的字面量变了,产物必须跟上
make

# 3. 构建安装包(产出 installer/build-artifacts/*)
pwsh -File installer/build.ps1 bundle

# 4. 回填 sha256(scoop hash + winget InstallerSha256)
python scripts/dev/bump_version.py finalize

# 5. 门:查零漂移(可挂 CI)
python scripts/dev/bump_version.py check
```

## 与 tag 的关系

**tag 才是"发布"这个动作**,而 `VERSION` 是"声明的版本"。两者必须一致,
否则会出现「tag v4.1.2 但产物自报 4.1.1」。所以:

- `check` 只查**仓内自洽**(VERSION == 每一处的版本串);
- 「VERSION == tag」由 **release.yml 在发版第一步断言**(tag 与 VERSION 不符 ⇒ 拒绝发布)。

## 为什么编译器版本号只能是字面量

`main.jhyy` 的横幅 `jhyy compiler vX.Y.Z (self-hosted)` 是一个**字符串字面量**。
它不能改成运行时读文件 / 调 extern —— 那需要新增局部变量,而**给 `main.jhyy`
加局部变量会移位模块级 temp 编号 ⇒ 自举产物行为漂移**(v4.0.20 实测:
一条 1 字节读被整条丢掉 ⇒ `--target=` 不再被识别 ⇒ 6 个 sysv 用例全红)。
字符串字面量改动是安全的 ⇒ 所以自动化只能落在"改字面量"这一层。

## 退出码

- `set` / `finalize`:0 = 成功;1 = 出错(文件缺失 / 解析失败)
- `check`:0 = 零漂移;1 = 有漂移(逐条列出)

## 引用

- 发布流程文档:[`docs/internal/build.md`](../../docs/internal/build.md) § 版本号自动化
- 分发 manifest 目录:`installer/distribution/winget/manifests/j/JiHuiYiYou/JHYY/<ver>/`
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "VERSION"

# sha256 还没回填时的占位(64 个 0 —— 长度合法但一眼看得出没填)
PENDING_SHA = "0" * 64

WINGET_BASE = Path("installer/distribution/winget/manifests/j/JiHuiYiYou/JHYY")
SCOOP_JSON = Path("installer/distribution/scoop/jhyy.json")
LICENSE_RTF = Path("installer/assets/license.rtf")
MAIN_JHYY = Path("compiler/src0/main.jhyy")
CHANGELOG = Path("docs/archive/logs/v4/changelog-v4.0.0.md")
RELEASE_NOTES_DIR = Path("installer/release-notes")

# FACTS.md § 1 的「产物 | 体积」表 —— **产物体积的落点**。
#
# 为什么体积必须**实测**:这两个数(55 / 28 MB)以前是**手打的** —— 打包变了没人知道。
# 而 docs 门 `check_artifact_sizes` 只保证「FACTS 与两份 README 一致」,
# **不保证为真**(它自己的注释就写着这句)⇒ 「一致但假」正是这个仓最防的那类失效。
# ⇒ 体积在 `finalize` 这一步量(产物就在手边),当场回填。
FACTS_MD = Path("docs/internal/FACTS.md")

# 提到产物名的**全部**文件 —— 体积要在这几处同步,否则 docs 门会因
# 「FACTS 说 56 / README 说 55」而红(那个门只比一致性,不比谁对)。
SIZE_FACADE = [FACTS_MD, Path("README.md"), Path("README.zh-CN.md")]

# 两份 README 的版本徽章 —— shields.io URL 里的 label 不同(英文 `version` / 中文 `版本`),
# 但版本串的位置一样(`badge/<label>-vX.Y.Z-<color>`)⇒ 同一个正则模板 + 各自的 label。
# **为什么要进这道门**:徽章是读者第一眼看到的版本号。2026-10-30 实测:两道门
# (脚本 + CI)都跑绿,而 README.md 的徽章停在 v4.0.0、README.zh-CN.md 停在 v1.8.3
# —— 落地文档可以整份落后 8 个 release 而门全绿。门不看它,就等于没有门。
README_BADGES = [
    (Path("README.md"), "version"),
    (Path("README.zh-CN.md"), "版本"),
]

# 两份 README 里**除徽章以外**还提到版本号的地方(2026-11-02 补)。
#
# 为什么补:实测 `fingerprints()` 只盯徽章那一处 ⇒ 一次 `set` 之后,
# 安装表里的 `jhyy-installer-4.1.2.exe`、Status 标题的 `v4.1.2`、
# 页脚的 `<sub>v4.1.2 — …</sub>` **全都留在旧版本号** ⇒
# 门面会**一边挂 v4.1.3 的徽章、一边让人下 v4.1.2 的安装包**。
#
# 形态 ⇒ (正则, 替换模板);`{v}` = 新版本号,`{d}` = 今天。
README_VERSION_SPANS = [
    (r"jhyy-installer-(\d+\.\d+\.\d+)\.exe", "jhyy-installer-{v}.exe"),
    (r"jhyy-compiler-(\d+\.\d+\.\d+)\.msi", "jhyy-compiler-{v}.msi"),
    (r"jhyy-lang-(\d+\.\d+\.\d+)\.vsix", "jhyy-lang-{v}.vsix"),
    (r"releases/download/v(\d+\.\d+\.\d+)/", "releases/download/v{v}/"),
    (r"(## (?:Status|状态) \(v)\d+\.\d+\.\d+(\))", r"\g<1>{v}\g<2>"),
    (r"(<sub>v)\d+\.\d+\.\d+( — )\d{4}-\d{2}-\d{2}", r"\g<1>{v}\g<2>{d}"),
    # 2026-11-04(v4.1.3 发版时实测):「Status (vX.Y.Z)」这个标题的**锚点**也带版本号
    #   ⇒ 徽章与目录里的链接(`#status-v412`)在版本号一变就成了**死锚点**
    #   ⇒ 文档门会报「死锚点」⇒ `set` 必须连它一起刷(否则每次发版都要手改两处)。
    #
    # ⚠️ 2026-11-07 真修:锚点里的版本号是**紧凑**的 —— GitHub 的锚点生成规则
    #   会**去掉点**(`## Status (v4.1.4)` ⇒ 锚点 `#status-v414`),
    #   而这里的模板写的是 `\d+\.\d+\.\d+` ⇒ **从来没匹配过** ⇒
    #   每次发版这两处锚点都是死的(2026-11-07 实测:文档门报
    #   「死锚点 → #status-v413」×4 —— 当年是用手改糊过去的,脚本里那道
    #   「刷锚点」的模板是**空转**的)。
    (r"(#(?:status|状态)-v)\d+", r"\g<1>{vc}"),
    # 2026-11-07:两份 README 开头那句「本页对应 vX.Y.Z / This page describes vX.Y.Z」
    #   —— 同样带版本号,同样没人刷(徽章刷了、这句话没刷 ⇒ 门面自相矛盾)。
    (r"(This page describes \*\*v)\d+\.\d+\.\d+(\*\*)", r"\g<1>{v}\g<2>"),
    (r"(本页对应 \*\*v)\d+\.\d+\.\d+(\*\*)", r"\g<1>{v}\g<2>"),
]

# changelog 里新版本段要插在它前面(该文件是**升序**的:最老在前)
CHANGELOG_ANCHOR = "## v4.x follow-on plans"

# ── 门面 changelog(仓库根 CHANGELOG.md)────────────────────────────────────
# 2026-10-31:这份文件**原来没有主人** —— `set` 只写内层 umbrella(上面那个
# CHANGELOG 常量),根 CHANGELOG.md **没有任何脚本碰** ⇒ 它可以落后任意多个
# release 而门全绿(实测:它把 v4.4.0 / v4.2.1 / v4.2.0 三条**没有 tag 的
# 变更槽**当已发布写在最上面,而 VERSION=4.1.2、git tag 也没有这三个)。
# ⇒ 这里给它定主人:`set` 往 `## Releases` 表首行插一行,`check` 断言首行
#    版本 == VERSION。门不看它,就等于没有门。
ROOT_CHANGELOG = Path("CHANGELOG.md")
ROOT_CHANGELOG_SECTION = "## Releases"

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def root_changelog_top_version(text: str) -> str | None:
    """根 CHANGELOG 的 `## Releases` 段首行版本号(取不到 ⇒ None)。

    首行 = 表里第一行 `| **vX.Y.Z** | ... |`。读**整段**而不是整份文件 ——
    下面的 `## Change slots` 段里也有 `| **vX.Y.Z** |` 行,不能串味。
    """
    sec = text.find(ROOT_CHANGELOG_SECTION)
    if sec < 0:
        return None
    m = re.search(r"\|\s*\*\*v(\d+\.\d+\.\d+)\*\*", text[sec:])
    return m.group(1) if m else None


def root_changelog_insert_row(text: str, new: str) -> str | None:
    """在根 CHANGELOG 的 `## Releases` 表首行插入一行(取不到落点 ⇒ None)。

    落点 = `## Releases` 之后的第一条表格分隔行 `|---|` 的**下一行**
    (新版本在最上面)。摘要先留 TODO —— 人写。
    """
    sec = text.find(ROOT_CHANGELOG_SECTION)
    if sec < 0:
        return None
    sep = text.find("\n|---", sec)
    if sep < 0:
        return None
    eol = text.find("\n", sep + 1)
    if eol < 0:
        return None
    row = f"| **v{new}** | (TODO - what changed in this release; fill in before publishing) |\n"
    return text[: eol + 1] + row + text[eol + 1 :]


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def read_version() -> str:
    """读 VERSION 文件(真相源)。"""
    if not VERSION_FILE.is_file():
        die(f"找不到 {VERSION_FILE.relative_to(ROOT)} —— 真相源缺失")
    text = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not SEMVER_RE.match(text):
        die(f"VERSION 内容不是 X.Y.Z: {text!r}")
    return text


def write_version(version: str) -> None:
    write_text(VERSION_FILE, version + "\n")


def die(msg: str) -> "None":
    print(f"[bump_version] ERROR: {msg}", file=sys.stderr)
    raise SystemExit(1)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str:
    """读文本(**不翻译行尾** —— CRLF/LF 原样保留,免得无端把整文件改行尾)。"""
    with path.open("r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_text(path: Path, text: str) -> None:
    """写文本(同上:行尾原样写出)。"""
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def replace_in_file(path: Path, pairs: list[tuple[str, str]], *, required: bool = True) -> int:
    """把文件里的若干 (regex, replacement) 应用一遍,返回改动次数。

    `replacement` 按 `re.sub` 的规则处理(用 `\\g<1>` 引用捕获组)——
    调用方负责把目标版本号拼进 replacement 字符串。
    """
    if not path.is_file():
        if required:
            die(f"文件不存在: {rel(path)}")
        return 0
    text = read_text(path)
    original = text
    count = 0
    for pattern, repl in pairs:
        text, n = re.subn(pattern, repl, text)
        count += n
    if text != original:
        write_text(path, text)
    return count


# --------------------------------------------------------------------------
# 各处的版本号「指纹」—— check 模式靠它确认一致性
# --------------------------------------------------------------------------
def fingerprints(version: str) -> dict[str, list[str]]:
    """返回 {位置: [该处读到的版本串, ...]} —— 全部应等于 version。"""
    out: dict[str, list[str]] = {}

    def scan(path: Path, pattern: str, label: str, *, optional: bool = False) -> None:
        if not path.is_file():
            out[label] = ["<文件缺失>"]
            return
        text = read_text(path)
        found = re.findall(pattern, text)
        if optional and not found:
            return                      # 可选的段落:没有就没事
        out[label] = found or ["<未找到>"]

    scan(MAIN_JHYY, r"jhyy compiler v(\d+\.\d+\.\d+) \(self-hosted\)", rel(MAIN_JHYY))
    scan(LICENSE_RTF, r"Version (\d+\.\d+\.\d+)", rel(LICENSE_RTF))
    scan(SCOOP_JSON, r'"version"\s*:\s*"(\d+\.\d+\.\d+)"', rel(SCOOP_JSON))

    # 两份 README 的版本徽章(见 README_BADGES 的注释:徽章漂了 = 门面在骗人)
    for path, blabel in README_BADGES:
        scan(path, r"badge/" + blabel + r"-v(\d+\.\d+\.\d+)-", rel(path) + " 徽章")
        # 徽章以外 README 里提到版本号的地方(安装表 / Status 标题 / 页脚)
        # —— 2026-11-02 补:实测 `set` 只刷徽章 ⇒ 其余 8 处留在旧版本号,
        #    门面会「挂着新徽章却让人下旧安装包」。
        for pat, label in (
            (r"jhyy-installer-(\d+\.\d+\.\d+)\.exe", "安装器名"),
            (r"jhyy-compiler-(\d+\.\d+\.\d+)\.msi", "MSI 名"),
            (r"jhyy-lang-(\d+\.\d+\.\d+)\.vsix", "扩展名"),
            (r"## (?:Status|状态) \(v(\d+\.\d+\.\d+)\)", "Status 标题"),
            (r"<sub>v(\d+\.\d+\.\d+) — ", "页脚"),
            # 2026-11-07 补:开头那句「本页对应 vX.Y.Z / This page describes vX.Y.Z」
            #   —— 徽章刷了、这句话没刷 ⇒ 门面自相矛盾(徽章 v4.1.4、这句话 v4.1.3)。
            (r"(?:This page describes|本页对应) \*\*v(\d+\.\d+\.\d+)\*\*", "页面自述版本"),
        ):
            scan(path, pat, rel(path) + " " + label, optional=True)

    # FACTS.md § 1 的产物表 —— 名字里的版本也必须 == VERSION。
    #
    # 为什么补(2026-11-05 实测):`set` 刷两份 README 的产物名,**不碰 FACTS.md**
    # ⇒ 刷完版本,README 指向新版的产物,FACTS 的产物表还写着**上一版**的名字
    # + 旧体积 —— 而**所有门都绿**(facades 门只比两份 README 互不打架)。
    # ⇒ 现在 `finalize` 会把 FACTS 的产物名 + 体积一起刷成实测值,这道门盯着它。
    for pat, label in (
        (r"jhyy-installer-(\d+\.\d+\.\d+)\.exe", "安装器名"),
        (r"jhyy-compiler-(\d+\.\d+\.\d+)\.msi", "MSI 名"),
        (r"jhyy-lang-(\d+\.\d+\.\d+)\.vsix", "扩展名"),
    ):
        scan(FACTS_MD, pat, rel(FACTS_MD) + " " + label, optional=True)

    wdir = ROOT / WINGET_BASE / version
    if not wdir.is_dir():
        out[f"{WINGET_BASE.as_posix()}/{version}/"] = ["<目录缺失>"]
    else:
        for name in (
            "JiHuiYiYou.JHYY.yaml",
            "JiHuiYiYou.JHYY.installer.yaml",
            "JiHuiYiYou.JHYY.locale.en-US.yaml",
        ):
            f = wdir / name
            if not f.is_file():
                out[f"{WINGET_BASE.as_posix()}/{version}/{name}"] = ["<文件缺失>"]
                continue
            text = read_text(f)
            found = re.findall(r"^PackageVersion:\s*(\S+)", text, re.M)
            out[f"{WINGET_BASE.as_posix()}/{version}/{name}"] = found or ["<未找到>"]

    return out


# --------------------------------------------------------------------------
# set —— 刷版本号
# --------------------------------------------------------------------------
def bump_winget(old: str, new: str) -> list[str]:
    """把 winget manifest 目录刷到新版本。

    - 目标目录不存在 ⇒ 从旧版本目录整份拷过去(**旧目录保留**,winget 的历史
      版本 manifest 本来就要留着);
    - 结构字段(PackageVersion / 注释里的版本 / InstallerUrl)刷成新版本;
    - `InstallerSha256` 置为待填占位 —— 真实值要等产物出来才有(`finalize`);
    - `ReleaseNotes` **保留历史段落**,只在最前面插一行新版本的 stub
      (版本说明是人写的,机器不该编)。
    """
    base = ROOT / WINGET_BASE
    src_dir = base / old
    dst_dir = base / new
    touched: list[str] = []

    if not dst_dir.is_dir():
        if not src_dir.is_dir():
            die(f"winget 旧版本目录不存在: {rel(src_dir)}")
        shutil.copytree(src_dir, dst_dir)
        touched.append(f"{rel(dst_dir)}/ (从 {old} 拷贝)")

    for name in (
        "JiHuiYiYou.JHYY.yaml",
        "JiHuiYiYou.JHYY.installer.yaml",
        "JiHuiYiYou.JHYY.locale.en-US.yaml",
    ):
        f = dst_dir / name
        if not f.is_file():
            continue

        # 结构字段:三个文件都要刷(PackageVersion / 注释里的版本 / URL / hash)
        # ⚠️ 这里的版本正则**不锚定 old** —— 写成"任意 X.Y.Z" ⇒ 幂等,
        # 且中途失败重跑一次就能收敛(不用先知道文件里现在写的是哪个版本)。
        n = replace_in_file(
            f,
            [
                # 注释里的版本
                (r"(?m)^(# .*?JHYY )\d+\.\d+\.\d+\b", r"\g<1>" + new),
                (r"(?m)^(# Version: )\d+\.\d+\.\d+\b", r"\g<1>" + new),
                # PackageVersion 字段
                (r"(?m)^(PackageVersion:\s*)\d+\.\d+\.\d+\b", r"\g<1>" + new),
                # 下载 URL(tag 带 v 前缀,文件名不带)
                (
                    r"/releases/download/v\d+\.\d+\.\d+/jhyy-installer-\d+\.\d+\.\d+\.exe",
                    "/releases/download/v" + new + "/jhyy-installer-" + new + ".exe",
                ),
                # 注释里引用的文件名 + hash(注释也要跟着刷,否则误导)
                (
                    r"jhyy-installer-\d+\.\d+\.\d+\.exe => [0-9a-f]{64}",
                    "jhyy-installer-" + new + ".exe => " + PENDING_SHA,
                ),
                # 真实 hash 字段
                (r"(?m)^(\s*InstallerSha256:\s*)[0-9a-fA-F]{64}\s*$", r"\g<1>" + PENDING_SHA),
            ],
        )

        # ReleaseNotes: 保留历史段落,只在最前面插一行新版本的 stub
        # (版本说明是人写的,机器不该编)
        if name.endswith("locale.en-US.yaml"):
            text = read_text(f)
            stub = f"  v{new}: (TODO: 这一版改了什么 —— 发布前补上)\n"
            if f"v{new}: (TODO" not in text:
                m = re.search(r"^ReleaseNotes:[ \t]*\|-[ \t]*$", text, re.M)
                if m:
                    insert_at = m.end()
                    text = text[:insert_at] + "\n" + stub + text[insert_at:].lstrip("\n")
                    write_text(f, text)

        touched.append(f"{rel(f)} ({n} 处)")

    return touched


def cmd_set(new: str, *, dry_run: bool = False) -> int:
    old = read_version()
    if not SEMVER_RE.match(new):
        die(f"目标版本号不是 X.Y.Z: {new!r}")

    print(f"[bump_version] {old} -> {new}")

    if dry_run:
        print("[bump_version] --dry-run: 不落盘")
        return 0

    if new != old:
        write_version(new)

    # 编译器横幅(1 处字面量 —— 2026-11-05 起:`jhyy` 与 `jhyy --help` 的两份
    # help 合成一份 `print_help()` ⇒ main.jhyy 里只剩这一处)
    n = replace_in_file(
        ROOT / MAIN_JHYY,
        [
            (
                r"(jhyy compiler v)\d+\.\d+\.\d+(\s\(self-hosted\))",
                r"\g<1>" + new + r"\g<2>",
            )
        ],
    )
    print(f"[bump_version] {rel(MAIN_JHYY)}: {n} 处")

    # license.rtf
    n = replace_in_file(
        ROOT / LICENSE_RTF,
        [(r"Version \d+\.\d+\.\d+", "Version " + new)],
    )
    print(f"[bump_version] {rel(LICENSE_RTF)}: {n} 处")

    # 两份 README 的版本徽章(shields.io URL;label 因语言而异 —— 英文 `version` / 中文 `版本`)
    for path, blabel in README_BADGES:
        n = replace_in_file(
            ROOT / path,
            [
                (
                    r"(badge/" + blabel + r"-v)\d+\.\d+\.\d+(-)",
                    r"\g<1>" + new + r"\g<2>",
                )
            ],
        )
        print(f"[bump_version] {rel(path)}: {n} 处")

        # 徽章以外的版本串(安装表 / Status 标题 / 页脚)—— 2026-11-02 补
        today = datetime.date.today().isoformat()
        for pat, tmpl in README_VERSION_SPANS:
            n = replace_in_file(
                ROOT / path,
                [(pat, tmpl.replace("{v}", new)
                          .replace("{vc}", new.replace(".", ""))
                          .replace("{d}", today))],
            )
            if n:
                print(f"[bump_version] {rel(path)}: {n} 处（{pat}）")

    # scoop manifest
    n = replace_in_file(
        ROOT / SCOOP_JSON,
        [
            (r'"version"\s*:\s*"\d+\.\d+\.\d+"', '"version": "' + new + '"'),
            (
                r"/releases/download/v\d+\.\d+\.\d+/jhyy-installer-\d+\.\d+\.\d+\.exe",
                "/releases/download/v" + new + "/jhyy-installer-" + new + ".exe",
            ),
            (r'"hash"\s*:\s*"[0-9a-fA-F]{64}"', '"hash": "' + PENDING_SHA + '"'),
        ],
    )
    print(f"[bump_version] {rel(SCOOP_JSON)}: {n} 处")

    # winget manifest
    for line in bump_winget(old, new):
        print(f"[bump_version] {line}")

    # changelog: 插一段 stub(正文是人写的)
    cl = ROOT / CHANGELOG
    if cl.is_file():
        text = read_text(cl)
        if f"## v{new} " not in text:
            if CHANGELOG_ANCHOR not in text:
                die(f"changelog 里找不到锚点 {CHANGELOG_ANCHOR!r}")
            stub = (
                f"## v{new} — TODO(这一版的标题)\n\n"
                f"> **状态**:草稿 —— 发布前把标题和正文补上。\n\n"
                f"### 改了什么\n\n"
                f"### 验证门\n\n"
                f"---\n\n"
            )
            text = text.replace(CHANGELOG_ANCHOR, stub + CHANGELOG_ANCHOR, 1)
            write_text(cl, text)
            print(f"[bump_version] {rel(cl)}: 插入 v{new} 段 stub")
        else:
            print(f"[bump_version] {rel(cl)}: v{new} 段已存在,跳过")

    # 门面 changelog(仓库根 CHANGELOG.md)—— 读者第一眼看到的「每版一行」。
    # 2026-10-31 新增:这份文件原来**没有任何脚本碰** ⇒ 它落后几个 release 门也不管。
    rcl = ROOT / ROOT_CHANGELOG
    if rcl.is_file():
        rtext = read_text(rcl)
        if root_changelog_top_version(rtext) != new:
            new_text = root_changelog_insert_row(rtext, new)
            if new_text is None:
                die(f"门面 changelog 里找不到 `{ROOT_CHANGELOG_SECTION}` 段或表格分隔行")
            write_text(rcl, new_text)
            print(f"[bump_version] {rel(rcl)}: 插入 v{new} 行")
        else:
            print(f"[bump_version] {rel(rcl)}: v{new} 行已存在,跳过")

    # release notes 片段(每版一个文件;release.yml 的 ${MAIN_CHANGES} 从这儿取)
    notes_dir = ROOT / RELEASE_NOTES_DIR
    notes_file = notes_dir / f"{new}.md"
    if not notes_file.is_file():
        notes_dir.mkdir(parents=True, exist_ok=True)
        write_text(
            notes_file,
            f"**v{new} 改了什么。**\n\n"
            f"> TODO —— 发布前把这一版的正文写在这里\n"
            f"(release.yml 的 `${{MAIN_CHANGES}}` 从这个文件取;\n"
            f"模板 `installer/changelog-template.md` 只放跟版本无关的部分)。\n",
        )
        print(f"[bump_version] {rel(notes_file)}: 新建 stub")
    else:
        print(f"[bump_version] {rel(notes_file)}: 已存在,跳过")

    print("")
    print("[bump_version] 下一步:")
    print("  1. make                      # main.jhyy 字面量变了 -> 自举产物必须重编")
    print("  2. pwsh -File installer/build.ps1 bundle")
    print("  3. python scripts/dev/bump_version.py finalize   # 回填 sha256")
    print("  4. python scripts/dev/bump_version.py check      # 零漂移门")
    print("  5. 补 changelog 正文 + installer/release-notes/<ver>.md 正文(人写)")
    print("  6. 补 CLAUDE.md 状态段(人写)")
    return 0


# --------------------------------------------------------------------------
# check —— 零漂移门
# --------------------------------------------------------------------------
def cmd_check() -> int:
    version = read_version()
    problems: list[str] = []
    pending: list[str] = []

    for label, found in fingerprints(version).items():
        for v in found:
            if v != version:
                problems.append(f"{label}: 版本串是 {v!r},期望 {version!r}")

    # changelog 路径 + 锚点必须有效 —— `set` 要往那里插新版本段。
    # 2026-10-30:文档大重构把 changelog 搬到 docs/archive/logs/ 后,这个路径没跟着改
    # ⇒ `set` 会在「找不到锚点」处 die,而 `check` 当时**不读 changelog** ⇒ 门全绿、发版流程却已坏。
    cl = ROOT / CHANGELOG
    if not cl.is_file():
        problems.append(f"{rel(CHANGELOG)}: changelog 文件不存在(`set` 会失败)")
    elif CHANGELOG_ANCHOR not in read_text(cl):
        problems.append(f"{rel(CHANGELOG)}: 找不到锚点 {CHANGELOG_ANCHOR!r}(`set` 会失败)")

    # 门面 changelog(根 CHANGELOG.md)—— 它的 `## Releases` 首行版本必须 == VERSION。
    # 2026-10-31 新增:这份文件原来没有主人(`set` 只写内层 umbrella)⇒ 实测它把
    # 三条**没有 tag** 的变更槽当已发布写在最上面,而 VERSION 是 4.1.2。
    rcl = ROOT / ROOT_CHANGELOG
    if not rcl.is_file():
        problems.append(f"{rel(ROOT_CHANGELOG)}: 门面 changelog 不存在")
    else:
        top = root_changelog_top_version(read_text(rcl))
        if top is None:
            problems.append(
                f"{rel(ROOT_CHANGELOG)}: 找不到 `{ROOT_CHANGELOG_SECTION}` 段或它的首行版本"
            )
        elif top != version:
            problems.append(
                f"{rel(ROOT_CHANGELOG)}: `{ROOT_CHANGELOG_SECTION}` 首行版本是 {top!r},"
                f"期望 {version!r}"
            )

    # sha256 占位检查(未回填只报 INFO,不算漂移 —— 那是发布流程的正常中间态)
    scoop = ROOT / SCOOP_JSON
    if scoop.is_file():
        try:
            data = json.loads(read_text(scoop))
        except json.JSONDecodeError as exc:
            problems.append(f"{rel(SCOOP_JSON)}: JSON 解析失败({exc})")
            data = None
        if data and data.get("hash") == PENDING_SHA:
            pending.append(f"{rel(SCOOP_JSON)}: hash 还没回填(finalize)")

    # README 里指向 Status 段的**锚点**必须跟着版本走。
    #
    # ⚠️ 2026-11-07 补:锚点里的版本号是**紧凑**的(GitHub 的锚点生成规则去掉点:
    #   `## Status (v4.1.4)` ⇒ `#status-v414`)⇒ 比的时候要拿**去点**的版本号。
    #   (此前 `set` 的刷锚点模板写的是带点的形态 ⇒ 从来没匹配过 ⇒ 每次发版
    #   那 4 处锚点都是死的,靠手改糊过去。)
    compact = version.replace(".", "")
    for path, _blabel in README_BADGES:
        if not path.is_file():
            continue
        for m in re.finditer(r"#(?:status|状态)-v(\d+)", read_text(path)):
            if m.group(1) != compact:
                problems.append(
                    f"{rel(path)}: Status 锚点 #{m.group(0)[1:]} 与 VERSION({version}) 不符"
                    f"(GitHub 的锚点去掉点 ⇒ 应为 #status-v{compact})"
                )

    # winget manifest —— **当前版本必须有一份**。
    #
    # ⚠️ 2026-11-06 真修:此前这段是 `if wini.is_file():` ⇒ 目录不存在就整段
    #   跳过,连 pending 都不报 ⇒ 「VERSION 对应的 winget manifest 不存在」
    #   这道零漂移门**照样报绿**。现在缺目录 = problem(硬红)。
    #   (sha256 还是占位 ⇒ 仍是 pending —— 那是发版流程的正常中间态。)
    wdir = ROOT / WINGET_BASE / version
    wini = wdir / "JiHuiYiYou.JHYY.yaml"
    if not wini.is_file():
        problems.append(
            f"{rel(wini)}: 不存在 —— 当前 VERSION 必须有一份 winget manifest"
            f"(bump_version.py set 会从上一版目录整份拷过来)"
        )
    else:
        # ⚠️ 2026-11-07 真修:占位 hash 在 **installer** manifest 里
        #   (`.installer.yaml`)—— W-203 把三件套的类型换回来之后,这段还只看
        #   `.yaml` ⇒ **占位永远看不见** ⇒ 零漂移门对着一个全 0 的 hash 报绿。
        #   ⇒ 现在扫该版本目录下的**所有** manifest。
        for wf in sorted(wdir.glob("*.yaml")):
            m = re.search(r"(?m)^\s*InstallerSha256:\s*(\S+)", read_text(wf))
            if m and m.group(1) == PENDING_SHA:
                pending.append(f"{rel(wf)}: InstallerSha256 还没回填(finalize)")
        # installer manifest 缺失 ⇒ 也是 problem(它才是带 hash 的那份)
        winst = wdir / "JiHuiYiYou.JHYY.installer.yaml"
        if not winst.is_file():
            problems.append(
                f"{rel(winst)}: 不存在 —— winget 的 installer manifest(带 "
                f"InstallerSha256 的那份)必须有"
            )

    # release notes 片段:release.yml 的 ${MAIN_CHANGES} 从这儿取 —— 缺了就发不出版
    notes_file = ROOT / RELEASE_NOTES_DIR / f"{version}.md"
    if not notes_file.is_file():
        problems.append(
            f"{rel(notes_file)}: 不存在 —— release.yml 的 ${{MAIN_CHANGES}} 没有来源"
        )

    print(f"[bump_version] VERSION = {version}")
    print("")
    if problems:
        print("[bump_version] FAIL —— 发现版本漂移:")
        for p in problems:
            print(f"  x {p}")
        return 1
    print("[bump_version] OK —— 全仓版本串一致")
    for p in pending:
        print(f"  ! {p}")
    return 0


# --------------------------------------------------------------------------
# finalize —— 回填 sha256(产物出来之后)
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# 产物体积:**实测回填**
# --------------------------------------------------------------------------
def _fmt_mb(nbytes: int) -> str:
    """字节 → `~N MB`。

    ⚠️ **必须与 release.yml 的算法一致**(那边是 `[math]::Round($bytes / 1MB)`):
    1MB = 1024²、四舍五入到整 MB。两边算出同一个数,release note 与 FACTS
    才不会各说各话。
    """
    return f"~{round(nbytes / (1024 * 1024))} MB"


def _backfill_size(path: Path, art_re: str, size: str) -> int:
    """把「提到该产物的行」上的体积改成实测值 —— 只改**第一个** MB 数字。

    只改第一个:一行里理论上可能有别的 MB(例如「含 92 MB 工具链」)⇒ 改多了
    就是替人做主。剩下的若真不一致,docs 门 `check_artifact_sizes` 会指出来。
    """
    if not path.is_file():
        return 0
    text = read_text(path)
    lines = text.split("\n")
    n = 0
    for i, line in enumerate(lines):
        if not re.search(art_re, line):
            continue
        new, k = re.subn(r"~[\d.]+\s*MB", size, line, count=1)
        if k:
            lines[i] = new
            n += k
    if n:
        write_text(path, "\n".join(lines))
    return n


def _sync_artifact_names(path: Path, version: str) -> int:
    """把产物名里的**版本段**刷成当前 VERSION。

    为什么也要刷:`bump_version.py set` 只刷两份 README,**不碰 FACTS.md**
    ⇒ 刷完版本,README 指向新版的产物,FACTS 的产物表却还写着**上一版**的
    名字 + 旧体积 —— 而当时**所有门都绿**。
    """
    if not path.is_file():
        return 0
    pairs = [
        (r"(jhyy-installer-)[\d.]+(\.exe)", rf"\g<1>{version}\g<2>"),
        (r"(jhyy-compiler-)[\d.]+(\.msi)", rf"\g<1>{version}\g<2>"),
        (r"(jhyy-lang-)[\d.]+(\.vsix)", rf"\g<1>{version}\g<2>"),
    ]
    return replace_in_file(path, pairs, required=False)


def cmd_finalize(artifact: str | None = None) -> int:
    version = read_version()
    art_dir = ROOT / "installer" / "build-artifacts"
    if artifact:
        installer_exe = Path(artifact)
        if not installer_exe.is_absolute():
            installer_exe = (ROOT / installer_exe).resolve()
    else:
        installer_exe = art_dir / f"jhyy-installer-{version}.exe"
    if not installer_exe.is_file():
        die(
            f"产物不存在: {installer_exe}\n"
            "  本地构建: pwsh -File installer/build.ps1 bundle\n"
            "  或用 --artifact 指向**已发布**的 exe(见下)"
        )

    digest = sha256_of(installer_exe)
    print(f"[bump_version] {installer_exe}")
    print(f"[bump_version]   sha256 = {digest}")

    # scoop
    scoop = ROOT / SCOOP_JSON
    if scoop.is_file():
        n = replace_in_file(
            scoop,
            [(r'"hash"\s*:\s*"[0-9a-fA-F]{64}"', '"hash": "' + digest + '"')],
        )
        print(f"[bump_version] {rel(scoop)}: {n} 处")

    # winget —— ⚠️ 2026-11-07 真修:hash 在 **installer** manifest 里
    #   (`.installer.yaml`),**不在** `.yaml`。
    #
    #   W-203(2026-11-05)把三件套的类型换回来之后,这一段还指着旧的 `.yaml`
    #   ⇒ **hash 永远填不上** —— 实测 `finalize` 报「0 处」,而发布出去的
    #   manifest 带着全 0 的占位 hash ⇒ winget 校验必红、PR 提不上去。
    #   ⇒ 现在扫**该版本目录下的所有 manifest**:谁有 `InstallerSha256` 就填谁
    #   (哪个文件持有那个字段,是 manifest 结构的事,不该由这个脚本硬编码)。
    wdir = ROOT / WINGET_BASE / version
    if wdir.is_dir():
        for wini in sorted(wdir.glob("*.yaml")):
            n = replace_in_file(
                wini,
                [
                    (
                        r"(?m)^(\s*InstallerSha256:\s*)" + PENDING_SHA + r"\s*$",
                        r"\g<1>" + digest,
                    ),
                    (
                        r"jhyy-installer-" + re.escape(version) + r"\.exe => " + PENDING_SHA,
                        "jhyy-installer-" + version + ".exe => " + digest,
                    ),
                ],
            )
            if n:
                print(f"[bump_version] {rel(wini)}: {n} 处")
    else:
        print(f"[bump_version] ⚠ {rel(wdir)} 不存在 —— winget manifest 的 sha256 没回填")

    # ── 产物体积:**实测回填**(FACTS.md § 1 + 两份 README)────────────
    #
    # 这一步**产物就在手边** ⇒ 体积就在这里量、当场回填。
    # 三个文件写的是**同一个数** ⇒ 同一份实测值写进三处:
    #   · docs 门的「一致性」成立(FACTS vs 两份 README)
    #   · 「为真」由**这次测量**保证 —— 以前它是手打的,而那个门只比一致性
    #     (`check_artifact_sizes` 的注释原话:「这只保证「一致」,不保证「为真」」)
    art_dir = ROOT / "installer" / "build-artifacts"
    msi_file = art_dir / f"jhyy-compiler-{version}.msi"
    measures = [(installer_exe, r"jhyy-installer-[\d.]+\.exe")]
    if msi_file.is_file():
        measures.append((msi_file, r"jhyy-compiler-[\d.]+\.msi"))
    else:
        print(f"[bump_version] ⚠ 找不到 {rel(msi_file)} —— MSI 体积这轮**不实测**"
              f"(FACTS.md 与两份 README 里 MSI 那行保持原样,别当成已回填)")
    jhyy_bin = ROOT / "compiler" / "build" / "bin" / "jhyy.exe"
    if jhyy_bin.is_file():
        measures.append((jhyy_bin, r"jhyy\.exe"))

    for art, art_re in measures:
        size = _fmt_mb(art.stat().st_size)
        touched = [(p, _backfill_size(p, art_re, size)) for p in SIZE_FACADE]
        where = ", ".join(f"{rel(p)}×{k}" for p, k in touched if k) or "（没找到可写的行）"
        print(f"[bump_version] {rel(art)} = {size} ({art.stat().st_size} bytes) → {where}")

    # FACTS.md 产物名里的**版本段** —— `set` 不碰 FACTS ⇒ 这一格以前没人管
    n = _sync_artifact_names(FACTS_MD, version)
    print(f"[bump_version] {rel(FACTS_MD)}: 产物名版本同步 {n} 处")

    print("")
    print("[bump_version] 回填完成。跑 `check` 确认零漂移。")
    return 0


# --------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        prog="bump_version.py",
        description="版本号自动化:单一真相源(VERSION)+ 一条命令刷全仓 + 零漂移门",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", help="把全仓版本串刷成指定版本")
    p_set.add_argument("version", help="目标版本号 X.Y.Z")
    p_set.add_argument("--dry-run", action="store_true", help="只打印,不落盘")

    sub.add_parser("check", help="查零漂移(有漂移 exit 1)—— 适合挂 CI")
    p_fin = sub.add_parser("finalize", help="回填 sha256(产物出来之后跑)")
    p_fin.add_argument(
        "--artifact",
        help=(
            "要算 sha256 的 exe 路径。默认取 installer/build-artifacts/jhyy-installer-<ver>.exe。"
            "⚠️ **发布出去的资产是 CI 构建的**,本地构建的 hash 未必相同(MSI 含时间戳)"
            "⇒ 发版后回填 manifest 请用 --artifact 指向**已发布**的那个 exe。"
        ),
    )

    args = ap.parse_args(argv)
    if args.cmd == "set":
        return cmd_set(args.version, dry_run=args.dry_run)
    if args.cmd == "check":
        return cmd_check()
    if args.cmd == "finalize":
        return cmd_finalize(args.artifact)
    die(f"未知子命令: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
