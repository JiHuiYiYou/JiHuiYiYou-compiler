# JHYY Installer GUIDs (v1.5.0+)

> **Generated**: 2026-08-15 (v1.5.5 hotfix, replace dev placeholder GUIDs)
> **Generator**: Python `uuid.uuid4()` (RFC 4122 v4 random)
> **Format**: UPPERCASE hex with dashes (Windows Installer canonical)

**MSI UpgradeCode stays stable across versions** — identifies "this is JHYY Compiler".
If you change this, Windows Installer treats new install as a different product (not upgrade).
Only change if you fork the product (different vendor, different name).

**Bundle UpgradeCode stays stable across versions** — identifies "this is JHYY Installer bundle".
Same rule as MSI UpgradeCode.

**Component GUIDs stay stable per component identity** — change only when:
1. Component content/structure changes (different files in the Component)
2. Component is moved between Features
3. You want to force reinstall on upgrade (rare)

If a Component's GUID stays the same across versions, Windows Installer knows it's the same
file/registry/etc. and skips re-install. If you forget to change GUID when content changes,
upgrades silently keep old version (silent corruption).

---

## Stable (across v1.5.x lifetime)

| Role | GUID |
|------|------|
| MSI UpgradeCode | `FC3FC7FC-3479-43EB-A64D-490BAEB32066` |
| Bundle UpgradeCode | `E6AC60CA-8FED-4DDE-8001-9A07B40E80D3` |

## Component GUIDs

| Component | GUID |
|-----------|------|
| JhyyExe | `A76D4595-11CE-4F86-B70A-170A6FDA06B0` |
| QbeExe | `096E27A7-65E2-465C-BA58-399A02C0F000` |
| InstallVSIXBat | `5D1C3BC5-EBC3-472A-9744-1F96692A2E6F` |
| ConfigureCodeRunnerPS1 (v1.5.6-patch2) | `F7A2D6E0-9B3C-4D1A-9E5F-3C7B8A2D6E01` |
| LicenseFile | `A4874A53-15B4-4010-8AF5-E6D47BD328CB` |
| VSCodeExtVSIX | `2BD62503-5942-4364-8052-B86ABC43C5C8` |
| JhyyExeShortcut | `9F008EC5-EF58-41B9-B6BE-8C4DD707E40A` |
| JhyyDocsShortcut | `32C375AD-328D-47CF-A422-8155A092CA04` |
| JhyyQuickStartShortcut | `181ADF1A-21D7-40A0-BF9D-64695522D202` |
| JHYYFileAssocReg | `C74ED968-E9D7-4061-AFC6-8FA37401F481` |
| JhyyDocsURL | `4065743A-3D07-48DE-A0E3-7FF8D5FEFA79` |
| JhyyQuickStartURL | `98BA5444-5A01-4FD4-9995-623AC6869020` |

## Notes

- **MSYS2 `uuidgen` not used** — MSYS2 doesn't bundle `uuidgen` by default (it's in `util-linux`).
  Python `uuid.uuid4()` is portable + cross-platform identical output (RFC 4122 v4).
- **dev placeholder GUIDs replaced**:
  - `A1B2C3D4-E5F6-7890-1234-567890ABCDEF` (MSI UpgradeCode, all-component-shared prefix)
  - `B1C2D3E4-F5A6-7890-1234-567890ABCDEF` (Bundle UpgradeCode)
  - `11111111-...` / `22222222-...` / `33333333-...` / ... (`9` = component GUIDs)
- **Bundle manifest caching**: After this change, `Burn` may report "Different version already
  installed" on existing per-machine installs because ProductCode changes per build. For dev
  testing: uninstall existing via Settings → Apps → JHYY Compiler → Uninstall before re-install.
- **Scoop manifest**: `installer/scoop/jhyy.json` references the v1.5.4 dev ProductCode
  (`BBCCEEFC-6163-46BF-B72C-7B20E6812960`) in the uninstaller block — that comment needs update
  to reflect the new real ProductCode from this release's build output. The comment is
  informational only (scoop's `uninstaller.script` is for guidance, not enforced).