param([string]$Plan = 'tmp/lab-cleanup-plan01.json')
$ErrorActionPreference = 'Stop'
$workspaceRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$workspacePrefix = $workspaceRoot.TrimEnd('\') + '\'
$planPath = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $Plan))
if (-not $planPath.StartsWith($workspacePrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Plan outside RF-D' }
$inventory = Get-Content -LiteralPath $planPath -Raw -Encoding utf8 | ConvertFrom-Json
foreach ($source in $inventory.source_sha256.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Join-Path $workspaceRoot $source.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $source.Value) { throw 'Cleanup source changed after inventory' }
}
$allowedAreas = @('references-local/voice-circuit','references-local/vco1-circuit','references-local/filter-vca-circuit','artifacts')
if (@(Compare-Object $allowedAreas $inventory.areas).Count) { throw 'Unexpected deletion area' }
$areaPrefixes = @($allowedAreas | ForEach-Object { [IO.Path]::GetFullPath((Join-Path $workspaceRoot $_)).TrimEnd('\') + '\' })
function Get-ScopedPath([string]$relative) {
    if ([IO.Path]::IsPathRooted($relative)) { throw 'Absolute plan entry' }
    $candidate = [IO.Path]::GetFullPath((Join-Path $workspaceRoot $relative))
    if (-not $candidate.StartsWith($workspacePrefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Entry outside workspace' }
    $withinArea = $false
    foreach ($prefix in $areaPrefixes) {
        if ($candidate.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or $candidate.Equals($prefix.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase)) { $withinArea = $true }
    }
    if (-not $withinArea) { throw 'Entry outside approved generated data' }
    $ancestor = [IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($candidate))
    while ($ancestor -and $ancestor.FullName.StartsWith($workspacePrefix,[StringComparison]::OrdinalIgnoreCase)) {
        if ($ancestor.LinkTarget) { throw 'Linked ancestor' }
        $ancestor = $ancestor.Parent
    }
    return $candidate
}
$qaPath = Join-Path $workspaceRoot $inventory.qa
if ((Get-FileHash -LiteralPath $qaPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $inventory.qa_sha256) { throw 'QA changed' }
$qa = Get-Content -LiteralPath $qaPath -Raw -Encoding utf8 | ConvertFrom-Json
$protectedPaths = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($prop in $qa.private_input_sha256.PSObject.Properties) { [void]$protectedPaths.Add($prop.Name) }
# Validate the complete destructive list before removing any entry.
foreach ($entry in $inventory.files) {
    if ($protectedPaths.Contains($entry.path)) { throw 'Admitted input in deletion list' }
    $path = Get-ScopedPath $entry.path
    $item = Get-Item -LiteralPath $path -Force
    if ($item.PSIsContainer -or $item.LinkTarget -or $item.Length -ne $entry.bytes) { throw 'Changed or linked file' }
    $mtimeNs = ($item.LastWriteTimeUtc.Ticks - 621355968000000000L) * 100L
    if ($mtimeNs -ne $entry.mtime_ns) { throw 'File changed after inventory' }
}
$receiptPath = Join-Path $workspaceRoot 'evidence/lab_cleanup01.json'
if (Test-Path -LiteralPath $receiptPath) { throw 'Preserve previous receipt' }
$result = [ordered]@{ schema='rf-d/lab-cleanup/v1'; passed=$false; qa=$inventory.qa; qa_sha256=$inventory.qa_sha256; plan_sha256=(Get-FileHash -LiteralPath $planPath -Algorithm SHA256).Hash.ToLowerInvariant(); base_commit=$inventory.base_commit; source_sha256=$inventory.source_sha256; areas=$allowedAreas; planned_files=$inventory.retire_files; planned_bytes=$inventory.retire_bytes; retired_files=0; retired_bytes=0L; removed_empty_directories=0; protected_inputs=$protectedPaths.Count; admitted_inputs_retired=0; full_plan_private='tmp/lab-cleanup-plan01.json'; content_hashes_for_retired_files=$false }
try {
    foreach ($entry in $inventory.files) {
        $path = Get-ScopedPath $entry.path
        Remove-Item -LiteralPath $path -Force
        $result.retired_files++; $result.retired_bytes += $entry.bytes
        if ($result.retired_files % 10000 -eq 0) { Write-Output "Retired $($result.retired_files) generated files" }
    }
    foreach ($relative in $inventory.directories) {
        $path = Get-ScopedPath $relative
        if (-not (Test-Path -LiteralPath $path)) { continue }
        if (@(Get-ChildItem -LiteralPath $path -Force).Count -eq 0) {
            Remove-Item -LiteralPath $path -Force
            $result.removed_empty_directories++
        }
    }
    foreach ($prop in $qa.private_input_sha256.PSObject.Properties) {
        if (-not (Test-Path -LiteralPath (Join-Path $workspaceRoot $prop.Name) -PathType Leaf)) { throw "Missing admitted input $($prop.Name)" }
    }
    foreach ($entry in $inventory.kept) {
        $item = Get-Item -LiteralPath (Get-ScopedPath $entry.path) -Force
        $mtimeNs = ($item.LastWriteTimeUtc.Ticks - 621355968000000000L) * 100L
        if ($item.Length -ne $entry.bytes -or $mtimeNs -ne $entry.mtime_ns) { throw 'Kept entry changed' }
    }
    $result.passed = $true
} catch { $result.failure = $_.ToString(); throw }
finally { $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding utf8NoBOM }
Write-Output "CLEANUP_DONE $($result.retired_files) files, $($result.retired_bytes) bytes, $($result.removed_empty_directories) empty directories"
