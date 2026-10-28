# Run in an elevated PowerShell to restore the three previously absent values.
# Open existing keys only; never recreate or replace a driver registry branch.
$changes = @(
    @('SOFTWARE\NVIDIA Corporation\GPUDebugger', 'EnableInterface'),
    @('SYSTEM\CurrentControlSet\Services\nvlddmkm', 'EnableDebugInterface'),
    @('SYSTEM\CurrentControlSet\Services\nvlddmkm\Global\NVTweak', 'RmProfilingAdminOnly')
)
foreach ($change in $changes) {
    $key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey($change[0], $true)
    if ($null -ne $key) {
        try { $key.DeleteValue($change[1], $false) } finally { $key.Dispose() }
    }
}
