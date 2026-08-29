# Generates installer UI assets (BMPs + ICO).
# v1.5.8: recolor default WiX red+disc → mint, replace disc with J logo.
# Replaces rev 2 (navy bg + JHYY Compiler title — too dark, duplicate brand name overlap).
#
# v1.8.2 patch split SVG sources — file-type ICO uses "document-style" icon
# (米白文件 + J + 横线, 跟 Python/Java/C#/C++ 文件图标一致), while BMP/MSI/VSCode
# ext keeps "app-style" icon (深色圆角矩形 + J) since Start Menu shortcuts and MSI
# install UI want app-style, not document-style.
#
# Outputs:
#   installer/assets/icons/jhyy-icon.ico       - 16+32+48+64+128+256 multi-size ICO (file-type, 米白文件+J)
#   installer/assets/icons/jhyy-icon-N.png     - intermediate, 上面 ICO 的源 PNG (file-type)
#   installer/assets/icons/jhyy-logo-N.png     - intermediate, BMP 用的 app-style logo PNG (深底+J)
#   installer/assets/bitmaps/jhyy-banner.bmp   - 493x58 MSI banner (recolored mint + 40x40 J logo)
#   installer/assets/bitmaps/jhyy-welcome.bmp  - 493x312 MSI welcome (recolored mint + 96x96 mint box + 80x80 J logo)
#
# Pre-reqs: rsvg-convert (MSYS2 librsvg), System.Drawing (PowerShell builtin)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

# === Multi-size .ico from jhyy-file-icon.svg (file-type: 米白文件 + J) ===
$iconSizes = @(16, 32, 48, 64, 128, 256)
$pngBlobs = @()
foreach ($sz in $iconSizes) {
    $png = "installer/assets/icons/jhyy-icon-${sz}.png"
    rsvg-convert -w $sz -h $sz "installer/assets/icons/jhyy-file-icon.svg" -o $png 2>&1 | Out-Null
    $pngBlobs += ,([System.IO.File]::ReadAllBytes((Get-Item $png).FullName))
}

# === App-style logo PNGs for BMP (深底 + J, BMP mint 背景要叠在上面) ===
# BMP 用 System.Drawing.Image 直接画, 不能用 jhyy-icon-* (那是 file-type 风格)
# 单独从 vscode-ext/icon.svg 渲染 logo PNG.
rsvg-convert -w 64 -h 64 "vscode-ext/icon.svg" -o "installer/assets/icons/jhyy-logo-64.png" 2>&1 | Out-Null
rsvg-convert -w 128 -h 128 "vscode-ext/icon.svg" -o "installer/assets/icons/jhyy-logo-128.png" 2>&1 | Out-Null
$icoPath = "installer/assets/icons/jhyy-icon.ico"
$icoStream = New-Object System.IO.MemoryStream
$writer = New-Object System.IO.BinaryWriter($icoStream)
$writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]$iconSizes.Count)
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
    $writer.Write([byte]$width); $writer.Write([byte]$height)
    $writer.Write([byte]0); $writer.Write([byte]0)
    $writer.Write([uint16]1); $writer.Write([uint16]32)
    $writer.Write([uint32]$pngBlobs[$i].Length)
    $writer.Write([uint32]$offsets[$i])
}
for ($i = 0; $i -lt $iconSizes.Count; $i++) { $writer.Write($pngBlobs[$i]) }
[System.IO.File]::WriteAllBytes($icoPath, $icoStream.ToArray())
$writer.Close()
Write-Host "[OK] $icoPath ($([System.IO.File]::ReadAllBytes($icoPath).Length) bytes)"

# === Banner BMP: recolor default WiX red→mint, replace disc with J logo ===
$bannerSrc = "C:/msys64/tmp/wix4-src/wix-b8977d6f88e7b68e000bac226a2814f236770570/src/ext/UI/wixlib/Bitmaps/bannrbmp.bmp"
$bannerOut = "installer/assets/bitmaps/jhyy-banner.bmp"
$src = [System.Drawing.Image]::FromFile($bannerSrc)
$w = $src.Width; $h = $src.Height
$bmp = New-Object System.Drawing.Bitmap($w, $h, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.DrawImage($src, 0, 0, $w, $h)
$src.Dispose()
$mintR = 0x00; $mintG = 0xd4; $mintB = 0xaa
for ($y = 0; $y -lt $h; $y++) {
    for ($x = 0; $x -lt $w; $x++) {
        $p = $bmp.GetPixel($x, $y)
        if ($p.R -gt 60 -and $p.R -gt ($p.G + 20) -and $p.R -gt ($p.B + 20)) {
            $intensity = [Math]::Min(1.0, ($p.R - 40) / 180.0)
            $r = [int]($mintR * $intensity)
            $gg = [int]($mintG * $intensity + ($p.G * (1.0 - $intensity) * 0.5))
            $b = [int]($mintB * $intensity + ($p.B * (1.0 - $intensity) * 0.5))
            $bmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($r, $gg, $b))
        }
    }
}
# Replace the disc (centered at X=461 Y=28, WxH=49x48) with J logo.
$icon = [System.Drawing.Image]::FromFile("installer/assets/icons/jhyy-icon-64.png")
$iconSize = 40
$iconX = 461 - $iconSize / 2
$iconY = 28 - $iconSize / 2
$g.DrawImage($icon, $iconX, $iconY, $iconSize, $iconSize)
$icon.Dispose()
Write-Host "[icon] J logo at ($iconX, $iconY) ${iconSize}x${iconSize} (replaces default disc on banner)"
$g.Dispose()
$bmp.Save($bannerOut, [System.Drawing.Imaging.ImageFormat]::Bmp)
$bmp.Dispose()
Write-Host "[OK] $bannerOut ($w x $h) — default WiX banner recolored mint + J logo at disc position"

# === Welcome BMP: recolor default WiX red→mint, tight mint box + J logo at disc area ===
$welcomeSrc = "C:/msys64/tmp/wix4-src/wix-b8977d6f88e7b68e000bac226a2814f236770570/src/ext/UI/wixlib/Bitmaps/dlgbmp.bmp"
$welcomeOut = "installer/assets/bitmaps/jhyy-welcome.bmp"
$src = [System.Drawing.Image]::FromFile($welcomeSrc)
$w = $src.Width; $h = $src.Height
$bmp = New-Object System.Drawing.Bitmap($w, $h, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.DrawImage($src, 0, 0, $w, $h)
$src.Dispose()
for ($y = 0; $y -lt $h; $y++) {
    for ($x = 0; $x -lt $w; $x++) {
        $p = $bmp.GetPixel($x, $y)
        if ($p.R -gt 60 -and $p.R -gt ($p.G + 20) -and $p.R -gt ($p.B + 20)) {
            $intensity = [Math]::Min(1.0, ($p.R - 40) / 180.0)
            $r = [int]($mintR * $intensity)
            $gg = [int]($mintG * $intensity + ($p.G * (1.0 - $intensity) * 0.5))
            $b = [int]($mintB * $intensity + ($p.B * (1.0 - $intensity) * 0.5))
            $bmp.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($r, $gg, $b))
        }
    }
}
# Tighter mint box around J logo (user wants narrow border). 96x96 box + 80x80 logo (8px pad).
# Position: upper-LEFT, replacing original disc area.
$discX = 60; $discY = 15; $discW = 96; $discH = 96
$bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, $mintR, $mintG, $mintB))
$g.FillRectangle($bgBrush, $discX, $discY, $discW, $discH)
$bgBrush.Dispose()
$icon = [System.Drawing.Image]::FromFile("installer/assets/icons/jhyy-icon-128.png")
$iconSize = 80
$iconX = $discX + ($discW - $iconSize) / 2
$iconY = $discY + ($discH - $iconSize) / 2
$g.DrawImage($icon, $iconX, $iconY, $iconSize, $iconSize)
$icon.Dispose()
Write-Host "[icon] J logo at ($iconX, $iconY) ${iconSize}x${iconSize} (tight mint box ${discW}x${discH} at upper-LEFT)"
$g.Dispose()
$bmp.Save($welcomeOut, [System.Drawing.Imaging.ImageFormat]::Bmp)
$bmp.Dispose()
Write-Host "[OK] $welcomeOut ($w x $h) — WiX default layout recolored mint + tight J logo box"

Write-Host "DONE."