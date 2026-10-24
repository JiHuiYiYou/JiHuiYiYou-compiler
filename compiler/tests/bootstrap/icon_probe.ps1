# icon_probe.ps1 — 输出目标 exe 里**可取到的图标个数**(0 = 没有图标)
#
# 用法:
#   powershell -NoProfile -ExecutionPolicy Bypass -File icon_probe.ps1 <exe>
#
# 为什么不用 python(2026-10-24 实测踩了两次):
#   CI runner 的 `python` 是 MSYS2 的 /usr/bin/python(Cygwin 版)——
#     ① 它的 ctypes **没有 WinDLL** ⇒ AttributeError: module 'ctypes' has no
#        attribute 'WinDLL';
#     ② 退回 ctypes.CDLL("shell32") 也不行 —— Cygwin 的 _dlopen 走 cygwin 的
#        DLL 搜索路径,找不到 Windows 的 shell32.dll ⇒ OSError。
#   ⇒ 两条 python 路线在 CI 上都不通(本地是 Windows python 才绿 —— 典型的
#   「本地绿、CI 红」)。
#
# PowerShell 一定有 ✓、走 Windows 原生 API ✓、而且和 Explorer 用的是**同一套**
# shell32!ExtractIconExW ⇒ 判据最忠实(问的就是「Explorer 能不能拿到图标」)。
#
# 输出:一个整数。0xFFFFFFFF(取不到 / 文件不存在)归一成 0 —— 语义上
# 「这个 exe 里没有可取的图标」。

param([Parameter(Mandatory = $true)][string]$Target)

$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class JHYYIconProbe {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    public static extern uint ExtractIconEx(string f, int i, IntPtr[] l, IntPtr[] s, uint n);
}
'@

$large = New-Object IntPtr[] 1
$small = New-Object IntPtr[] 1
$r = [JHYYIconProbe]::ExtractIconEx($Target, 0, $large, $small, 1)
if ($r -eq 4294967295) { Write-Output 0 } else { Write-Output $r }
