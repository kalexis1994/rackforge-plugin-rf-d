param([Parameter(Mandatory=$true)][ValidateRange(1,99)][int]$Attempt)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$taskTag = '{0:d2}' -f $Attempt
$taskReceipt = Join-Path $taskRoot "evidence/voice_mixer_on_native_attempt$taskTag.json"
$taskProof = Get-Content -LiteralPath $taskReceipt -Raw -Encoding utf8 | ConvertFrom-Json
if (-not $taskProof.passed) { throw 'Only a completed native test build can be archived' }
$taskExpected = [IO.Path]::GetFullPath((Join-Path $taskRoot "tmp/mixer-on-native-build$taskTag"))
$taskResolved = (Resolve-Path -LiteralPath $taskExpected).Path
if ($taskResolved -ne $taskExpected -or
    $taskResolved -eq $taskRoot -or
    ((Get-Item -LiteralPath $taskResolved).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    throw 'Resolved new build target differs or is a reparse point'
}
$taskIndex = [Array]::IndexOf([string[]]$taskProof.command,'--target-dir')
if ($taskIndex -lt 0 -or [IO.Path]::GetFullPath($taskProof.command[$taskIndex+1]) -ne $taskExpected) {
    throw 'Build path is not owned by this measured attempt'
}
$taskDestination = Join-Path $taskRoot "references-local/mixer-on-native$taskTag"
$taskOutput = Join-Path $taskRoot "evidence/voice_mixer_on_build_archive$taskTag.json"
if ((Test-Path -LiteralPath $taskDestination) -or (Test-Path -LiteralPath $taskOutput)) {
    throw 'Preserve archived build attempt'
}
$taskItems = @(Get-ChildItem -LiteralPath (Join-Path $taskResolved 'debug/deps') -File |
    Where-Object { $_.Name -match '^mixer_on(?:_no_alloc)?-[a-f0-9]+\.exe$' })
if ($taskItems.Count -ne 2) { throw 'Exactly two measured native test binaries required' }
New-Item -ItemType Directory -Path $taskDestination | Out-Null
$taskKept = @()
foreach ($taskItem in $taskItems) {
    $taskSha = (Get-FileHash -LiteralPath $taskItem.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    $taskCopy = Join-Path $taskDestination $taskItem.Name
    Copy-Item -LiteralPath $taskItem.FullName -Destination $taskCopy
    if ((Get-FileHash -LiteralPath $taskCopy -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskSha) {
        throw 'Preserved binary differs; build cache stays intact'
    }
    $taskKept += @{ original_path=$taskItem.FullName; preserved_path=$taskCopy; sha256=$taskSha; bytes=$taskItem.Length }
}
$taskRecord = @{ schema='rf-d/mixer-on-build-archive/v1'; attempt=$Attempt;
    test_receipt_sha256=(Get-FileHash -LiteralPath $taskReceipt -Algorithm SHA256).Hash.ToLowerInvariant();
    helper_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant();
    resolved_build_target=$taskResolved; preserved_binaries=$taskKept;
    cache_retired=$false; historical_campaigns_touched=$false }
$taskRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskOutput -Encoding utf8NoBOM
# One checked build directory created by this attempt; preserve its test executables first.
if ((Resolve-Path -LiteralPath $taskExpected).Path -ne $taskResolved) { throw 'Build path changed' }
Remove-Item -LiteralPath $taskResolved -Recurse -Force
$taskRecord.cache_retired = -not (Test-Path -LiteralPath $taskExpected)
$taskRecord | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskOutput -Encoding utf8NoBOM
Write-Output "Preserved $($taskKept.Count) native binaries; retired only new compiler cache: $($taskRecord.cache_retired)"
