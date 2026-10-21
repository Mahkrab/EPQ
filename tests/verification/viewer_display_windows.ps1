# Historical desktop-wide automation attempt; retained to explain the failed run.
# Use viewer_display.py for isolated checks addressed to an owned process window.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class MaelstromWindow {
 [StructLayout(LayoutKind.Sequential)] public struct RECT {public int Left,Top,Right,Bottom;}
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT r);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h,int x,int y,int w,int height,bool repaint);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int command);
 [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,uint message,IntPtr w,IntPtr l);
}
'@
function Viewer {
 $p=Get-Process | Where-Object {$_.MainWindowTitle -like '*Maelstrom*'} | Select-Object -First 1
 if (!$p) {throw 'Maelstrom window absent'}
 return $p
}
function Wait-Title([string]$Pattern) {
 $end=[DateTime]::UtcNow.AddSeconds(45)
 do {
  $p=Viewer
  if ($p.MainWindowTitle -match $Pattern) {Write-Output $p.MainWindowTitle;return}
  Start-Sleep -Milliseconds 100
 } while ([DateTime]::UtcNow -lt $end)
 throw "Timed out waiting for title pattern: $Pattern; observed $($p.MainWindowTitle)"
}
function Keys([string]$Value) {
 $p=Viewer
 [MaelstromWindow]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
 $shell=New-Object -ComObject WScript.Shell
 $shell.AppActivate($p.Id) | Out-Null
 Start-Sleep -Milliseconds 150
 [System.Windows.Forms.SendKeys]::SendWait($Value)
 Write-Output "Keys: $Value"
}
function Capture([string]$Name) {
 $p=Viewer
 [MaelstromWindow]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
 Start-Sleep -Milliseconds 700
 $r=New-Object MaelstromWindow+RECT
 if (![MaelstromWindow]::GetWindowRect($p.MainWindowHandle,[ref]$r)) {throw 'Cannot read viewer bounds'}
 $bitmap=New-Object System.Drawing.Bitmap ($r.Right-$r.Left),($r.Bottom-$r.Top)
 $graphics=[System.Drawing.Graphics]::FromImage($bitmap)
 try {
  $graphics.CopyFromScreen($r.Left,$r.Top,0,0,$bitmap.Size)
  $bitmap.Save((Join-Path $OutputDirectory "$Name.png"),[System.Drawing.Imaging.ImageFormat]::Png)
 } finally {$graphics.Dispose();$bitmap.Dispose()}
 Write-Output "Captured: $Name ($($r.Right-$r.Left)x$($r.Bottom-$r.Top))"
}
Wait-Title 'gen 1 Paused.*0/100000 steps'
Capture '01-initial'
Keys 'n'
Wait-Title 'gen 1 Paused.*1/100000 steps.*warnings 1'
Keys 'f{RIGHT}{UP}{ADD}d'
Capture '02-step-warning-camera-audit'
Keys ' '
Wait-Title 'gen 1 Running'
Keys ' '
Wait-Title 'gen 1 Paused'
Capture '03-paused-after-running'
Keys 'r'
Wait-Title 'gen 2 Paused.*0/100000 steps'
Keys '{TAB}{TAB}{TAB}{TAB}{TAB}{TAB}{ENTER}{DELETE}2{ENTER}a'
Wait-Title 'gen 3 Paused.*0/2 steps'
Keys ' '
Wait-Title 'gen 3 Completed.*2/2 steps'
Capture '04-completed'
Keys '{TAB}{ENTER}{DELETE}missing-scene.toml{ENTER}a'
Capture '05-rejected-draft'
Wait-Title 'gen 3 Completed.*2/2 steps'
Keys '1ba'
Wait-Title 'gen 4 Paused.*0/2 steps'
Keys 'n'
Wait-Title 'gen 4 Paused.*1/2 steps'
Capture '06-threaded'
Keys 'ba'
Wait-Title 'gen 5 Failed.*0/2 steps'
Capture '07-unavailable-cuda'
Keys 'o'
Wait-Title 'PRIOR gen 4 Cancelled.*1/2 steps'
Capture '08-retained-prior'
Keys 'oba'
Wait-Title 'gen 6 Paused.*0/2 steps'
Keys 'n'
Wait-Title 'gen 6 Paused.*1/2 steps'
Keys 'gh'
Capture '09-brute-force-recreated-surface'
$p=Viewer
[MaelstromWindow]::MoveWindow($p.MainWindowHandle,100,100,1000,680,$true) | Out-Null
Capture '10-resized'
[MaelstromWindow]::ShowWindow($p.MainWindowHandle,6) | Out-Null
Start-Sleep -Milliseconds 700
[MaelstromWindow]::ShowWindow($p.MainWindowHandle,9) | Out-Null
Wait-Title 'gen 6 Paused.*1/2 steps'
Keys 'h'
Capture '11-restored'
Keys 'c'
Wait-Title 'gen 6 Cancelled.*1/2 steps'
Keys '{TAB}{TAB}{TAB}{TAB}{TAB}{TAB}{ENTER}{DELETE}100000{ENTER}a'
Wait-Title 'gen 7 Paused.*0/100000 steps'
Keys ' '
Wait-Title 'gen 7 Running'
$p=Viewer
[MaelstromWindow]::PostMessage($p.MainWindowHandle,0x0010,[IntPtr]::Zero,[IntPtr]::Zero) | Out-Null
Write-Output 'Sent window close during running work'
