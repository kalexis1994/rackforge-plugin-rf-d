param([Parameter(Mandatory)][string]$HostRootPath,[Parameter(Mandatory)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$taskRoot=(Resolve-Path -LiteralPath $HostRootPath).ProviderPath
$taskCache=Join-Path $taskRoot 'target/release/deps'
$taskCache=(Resolve-Path -LiteralPath $taskCache).ProviderPath
$expectedCache=[IO.Path]::GetFullPath((Join-Path $taskRoot 'target/release/deps'))
if ($taskCache -ne $expectedCache -or -not $taskCache.StartsWith($taskRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {throw 'Cache path outside intended host workspace'}
if (Get-Process cargo,rustc -ErrorAction SilentlyContinue) {throw 'A Rust build is active; retry after it completes'}
if (Test-Path -LiteralPath $OutputDirectory) {throw 'Preserve existing cleanup receipt'}
$taskOutput=[IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $taskOutput | Out-Null
Push-Location -LiteralPath $taskRoot
try {
 $tracked=@(git ls-files -- target/release/deps)
 if ($LASTEXITCODE -ne 0 -or $tracked.Count -ne 0) {throw 'Cache must contain no tracked files'}
 $ignored=git check-ignore target/release/deps
 if ($LASTEXITCODE -ne 0) {throw 'Cache is not ignored by Git'}
 $statusBefore=@(git status --porcelain)
 $driveName=[IO.Path]::GetPathRoot($taskRoot)
 $freeBefore=([IO.DriveInfo]::new($driveName)).AvailableFreeSpace
 $extensions=@('.rlib','.rmeta','.pdb','.o','.d')
 $files=@(Get-ChildItem -LiteralPath $taskCache -File | Where-Object {$extensions -contains $_.Extension -and -not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint)})
 $runtime=@(Get-ChildItem -LiteralPath $taskCache -File | Where-Object {$_.Extension -in @('.exe','.dll')} | ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower();bytes=$_.Length}})
 $plan=@($files | ForEach-Object {@{path=$_.FullName;bytes=$_.Length}})
 $receipt=@{schema='rf-d/regenerable-build-cache-cleanup/v1';passed=$false;host_root=$taskRoot;cache_root=$taskCache;source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLower();free_before_bytes=$freeBefore;allowed_extensions=$extensions;planned=$plan;runtime_before=$runtime;git_status_before=$statusBefore;deleted=@();errors=@()}
 function Save-Receipt {ConvertTo-Json -InputObject $receipt -Depth 8 | Set-Content -LiteralPath (Join-Path $taskOutput 'receipt.json') -Encoding utf8NoBOM}
 Save-Receipt
 foreach ($file in $files) {
  $resolved=(Resolve-Path -LiteralPath $file.FullName).ProviderPath
  if (-not $resolved.StartsWith($taskCache+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetDirectoryName($resolved) -ne $taskCache) {throw 'Deletion path escaped the checked cache'}
  try {Remove-Item -LiteralPath $resolved -Force;$receipt.deleted+=@{path=$resolved;bytes=$file.Length}}
  catch {$receipt.errors+=@{path=$resolved;error=$_.Exception.Message}}
 }
 $runtimeAfter=@($runtime | ForEach-Object {@{path=$_.path;sha256=(Get-FileHash -LiteralPath $_.path -Algorithm SHA256).Hash.ToLower();bytes=(Get-Item -LiteralPath $_.path).Length}})
 $receipt.runtime_after=$runtimeAfter;$receipt.git_status_after=@(git status --porcelain)
 $receipt.free_after_bytes=([IO.DriveInfo]::new($driveName)).AvailableFreeSpace
 $receipt.deleted_logical_bytes=($receipt.deleted | Measure-Object -Property bytes -Sum).Sum
 $receipt.passed=$receipt.errors.Count -eq 0 -and (ConvertTo-Json -InputObject $runtime -Depth 4 -Compress) -eq (ConvertTo-Json -InputObject $runtimeAfter -Depth 4 -Compress) -and (ConvertTo-Json -InputObject $statusBefore -Compress) -eq (ConvertTo-Json -InputObject $receipt.git_status_after -Compress)
 Save-Receipt
 Write-Output ('BUILD_CACHE_CLEANUP '+$receipt.passed+' '+$receipt.deleted.Count+' '+$receipt.deleted_logical_bytes+' '+$receipt.free_after_bytes)
} finally {Pop-Location}
