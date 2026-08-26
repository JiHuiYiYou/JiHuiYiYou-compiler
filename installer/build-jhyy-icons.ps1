# Generates .ico (multi-size) + banner BMP from icon.svg for MSI installer.
# Sprint v1.5.7-rc1 rev 2: replace default Windows disc icon + red banner with
# JHYY brand (navy #1a1a2e + mint #00d4aa) for consistent installer identity.
#
# Outputs:
#   installer/jhyy-icon.ico       - 16+32+48+64+128+256 (ARPPRODUCTICON)
#   installer/jhyy-banner.bmp     - 493x58 MSI banner BMP (WixUI_Minimal top)
#   installer/jhyy-welcome.bmp    - 493x312 MSI welcome dialog bitmap
#
# Pre-reqs: rsvg-convert (MSYS2 librsvg), System.Drawing (PowerShell builtin)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

$navy = [System.Drawing.Color]::FromArgb(0x1a, 0x1a, 0x2e)
$mint = [System.Drawing.Color]::FromArgb(0x00, 0xd4, 0xaa)
$iconSizes = @(16, 32, 48, 64, 128, 256)

# 1. Render each size via rsvg-convert
$pngBlobs = @()
foreach ($sz in $iconSizes) {
    $png = "installer/jhyy-icon-${sz}.png"
    rsvg-convert -w $sz -h $sz "vscode-ext/icon.svg" -o $png 2>&1 | Out-Null
    $pngBlobs += ,([System.IO.File]::ReadAllBytes((Get-Item $png).FullName))
}

# 2. Compose multi-size .ico (PNG-in-ICO, Vista+)
$icoPath = "installer/jhyy-icon.ico"
$icoStream = New-Object System.IO.MemoryStream
$writer = New-Object System.IO.BinaryWriter($icoStream)

$writer.Write([uint16]0)
$writer.Write([uint16]1)
$writer.Write([uint16]$iconSizes.Count)

$headerSize = 6 + (16 * $iconSizes.Count)
$runningOffset = $headerSize
$offsets = @()
for ($i = 0; $i -lt $iconSizes.Count; $i++) {
    $offsets += $runningOffset
    $runningOffset += $pngBlobs[$i].Length
}

for ($i = 0; $i -lt $iconSizes.Count; $i++) {
    $sz = $iconSizes[$i]
    $width  = if ($sz -ge 256) { [byte]0 } else { [byte]$sz }
    $height = if ($sz -ge 256) { [byte]0 } else { [byte]$sz }
    $writer.Write([byte]$width)
    $writer.Write([byte]$height)
    $writer.Write([byte]0)
    $writer.Write([byte]0)
    $writer.Write([uint16]1)
    $writer.Write([uint16]32)
    $writer.Write([uint32]$pngBlobs[$i].Length)
    $writer.Write([uint32]$offsets[$i])
}
for ($i = 0; $i -lt $iconSizes.Count; $i++) {
    $writer.Write($pngBlobs[$i])
}

[System.IO.File]::WriteAllBytes($icoPath, $icoStream.ToArray())
$writer.Close()
Write-Host "[OK] $icoPath ($([System.IO.File]::ReadAllBytes($icoPath).Length) bytes, $($iconSizes.Count) sizes)"

# 3. Banner BMP (493 x 58) for MSI dialog top
$bmp = New-Object System.Drawing.Bitmap(493, 58, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$g.Clear($navy)

$icon48 = [System.Drawing.Image]::FromFile("installer/jhyy-icon-48.png")
$g.DrawImage($icon48, 5, 5, 48, 48)
$icon48.Dispose()

$fontTitle = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$brushMint = New-Object System.Drawing.SolidBrush($mint)
$g.DrawString("JHYY Compiler", $fontTitle, $brushMint, 65, 8)

$fontSub = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Regular)
$brushMintDim = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(180, $mint.R, $mint.G, $mint.B))
$g.DrawString("v1.5.7  -  self-hosted static-typed language", $fontSub, $brushMintDim, 65, 36)

$brushBottom = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(64, $mint.R, $mint.G, $mint.B))
$g.FillRectangle($brushBottom, 0, 54, 493, 4)

$fontTitle.Dispose()
$fontSub.Dispose()
$brushMint.Dispose()
$brushMintDim.Dispose()
$brushBottom.Dispose()
$g.Dispose()
$bmp.Save("installer/jhyy-banner.bmp", [System.Drawing.Imaging.ImageFormat]::Bmp)
$bmp.Dispose()
Write-Host "[OK] installer/jhyy-banner.bmp (493x58)"

# 4. Welcome BMP (493 x 312) for full welcome dialog content
$bmpW = New-Object System.Drawing.Bitmap(493, 312, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
$gW = [System.Drawing.Graphics]::FromImage($bmpW)
$gW.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$gW.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$gW.Clear($navy)

$icon64 = [System.Drawing.Image]::FromFile("installer/jhyy-icon-64.png")
$gW.DrawImage($icon64, 30, 30, 64, 64)
$icon64.Dispose()

$fontWTitle = New-Object System.Drawing.Font("Segoe UI", 18, [System.Drawing.FontStyle]::Bold)
$brushWTitle = New-Object System.Drawing.SolidBrush($mint)
$gW.DrawString("JHYY Compiler v1.5.7", $fontWTitle, $brushWTitle, 110, 38)

$fontWSub = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Regular)
$brushWSub = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(200, $mint.R, $mint.G, $mint.B))
$gW.DrawString("Self-hosted static-typed programming language", $fontWSub, $brushWSub, 110, 70)

$penMint = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(128, $mint.R, $mint.G, $mint.B), 1)
$gW.DrawLine($penMint, 30, 110, 463, 110)

$fontWBody = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Regular)
$brushWBody = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(220, 240, 240, 240))

$bodyLines = @(
    "This installer will set up the JHYY compiler on your system."
    ""
    "Components installed:"
    "  - jhyy.exe            compiler frontend + driver"
    "  - qbe.exe             QBE IL compiler (vendored)"
    "  - runtime.c/.h        JHYY runtime support"
    "  - jhyy_helpers.c      process / path helpers"
    ""
    "After install, the post-install script will:"
    "  - Set MSYS2_PATH_TYPE=inherit (User env)"
    "    so MSYS2 bash picks up the JHYY bin PATH entry"
    "  - Configure VSCode defaultProfile = bash (MSYS2)"
    "    for seamless terminal integration"
    "  - Logoff / logon once to trigger HKLM RunOnce config"
)
$y = 130
foreach ($line in $bodyLines) {
    $gW.DrawString($line, $fontWBody, $brushWBody, 30, $y)
    $y += 18
}

$fontWTitle.Dispose()
$fontWSub.Dispose()
$fontWBody.Dispose()
$brushWTitle.Dispose()
$brushWSub.Dispose()
$brushWBody.Dispose()
$penMint.Dispose()
$gW.Dispose()
$bmpW.Save("installer/jhyy-welcome.bmp", [System.Drawing.Imaging.ImageFormat]::Bmp)
$bmpW.Dispose()
Write-Host "[OK] installer/jhyy-welcome.bmp (493x312)"

Write-Host "DONE."