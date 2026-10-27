param(
    [ValidateSet('check', 'start', 'running')]
    [string]$Phase = 'check',
    [ValidateRange(0, 65536)]
    [int]$GpuRequiredMiB = 0,
    [switch]$RequireGpu
)

# Conservative task limits, not manufacturer specifications or a crash guarantee.
# Exit 2 means defer/stop this task's heavy work; never terminate unrelated apps.
$ErrorActionPreference = 'Stop'
$cpuSamples = @(for ($sample = 0; $sample -lt 3; $sample++) {
    (Get-CimInstance Win32_Processor | Measure-Object LoadPercentage -Average).Average
    if ($sample -lt 2) { Start-Sleep -Milliseconds 500 }
})
$os = Get-CimInstance Win32_OperatingSystem
$memory = Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory
$ramAvailableGiB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$diskFreeGiB = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
$cpuPercent = [math]::Round(($cpuSamples | Measure-Object -Average).Average, 1)
$gpu = $null
$gpuProviderAvailable = [bool](Get-Command nvidia-smi -ErrorAction SilentlyContinue)
$gpuMetricsRequired = $RequireGpu.IsPresent -or $Phase -eq 'start' -or $GpuRequiredMiB -gt 0 -or $gpuProviderAvailable
if ($gpuProviderAvailable) {
    $gpuLine = & nvidia-smi --id=0 --query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu --format=csv,noheader,nounits
    if ($LASTEXITCODE -eq 0) {
        $fields = $gpuLine.Split(',').Trim()
        $gpu = [pscustomobject]@{
            Name = $fields[0]
            TotalMiB = [int]$fields[1]
            UsedMiB = [int]$fields[2]
            FreeMiB = [int]$fields[1] - [int]$fields[2]
            TemperatureC = [int]$fields[3]
            UtilizationPercent = [int]$fields[4]
        }
    }
}
$reasons = @()
$ramFloorGiB = if ($Phase -eq 'start') { 3.0 } else { 2.0 }
$gpuReserveMiB = if ($Phase -eq 'start') { 512 } else { 256 }
if ($cpuSamples.Count -ne 3) { $reasons += 'cpu_metrics_unavailable' }
if ($null -eq $memory.PercentCommittedBytesInUse) { $reasons += 'committed_memory_metrics_unavailable' }
if ($ramAvailableGiB -lt $ramFloorGiB) { $reasons += 'available_ram_below_task_floor' }
if ($memory.PercentCommittedBytesInUse -ge 90) { $reasons += 'committed_memory_at_task_limit' }
if ($diskFreeGiB -lt 5) { $reasons += 'disk_free_below_5_gib' }
if (($cpuSamples | Measure-Object -Minimum).Minimum -ge 95) { $reasons += 'cpu_load_high_in_all_samples' }
if ($null -eq $gpu -and $gpuMetricsRequired) { $reasons += 'gpu_metrics_unavailable' }
if ($null -ne $gpu) {
    if ($gpu.TemperatureC -ge 80) { $reasons += 'gpu_temperature_at_task_limit' }
    if ($gpu.FreeMiB -lt ($GpuRequiredMiB + $gpuReserveMiB)) { $reasons += 'gpu_headroom_below_task_floor' }
}
[pscustomobject]@{
    CheckedAtUtc = [datetime]::UtcNow.ToString('o')
    Phase = $Phase
    CpuLoadPercent = $cpuPercent
    CpuTemperatureC = $null # No reliable CPU temperature provider configured.
    RamAvailableGiB = $ramAvailableGiB
    CommittedPercent = $memory.PercentCommittedBytesInUse
    DiskFreeGiB = $diskFreeGiB
    Gpu = $gpu
    GpuMetricsRequired = $gpuMetricsRequired
    Decision = if ($reasons.Count) { 'defer_heavy_work' } else { 'within_task_limits' }
    Reasons = $reasons
} | ConvertTo-Json -Depth 3
if ($reasons.Count) { exit 2 }
