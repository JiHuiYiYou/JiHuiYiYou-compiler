# scripts/dev/build/

build-time dev 脚本占位 (Phase 5 polish 创建, 当前为空)。

预留 future 内容 (e.g.):
- `cross-compile.sh` — Linux → Windows cross build
- `release-snapshot.sh` — 截 release 镜像 + sha 校验
- `installer-pack.cmd` — 本地 WiX 包装 (vs CI runner)

任何新 build-time dev 脚本应放此处, 不散落到 `scripts/dev/` 根。