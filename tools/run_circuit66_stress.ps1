param([string]$Output = 'evidence/circuit66_long_stress.json', [switch]$CaptureProbes)
# Build the release example first; no build or timing assumptions here.
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent $PSScriptRoot
$taskBench = Join-Path $taskRepo 'target/release/examples/bench_ladder_recovery_output.exe'
if (-not (Test-Path -LiteralPath $taskBench)) { throw 'Build the release example first.' }
$taskFlag = if ($CaptureProbes) { '--stress-probes' } else { '--stress' }
$taskRaw = & $taskBench $taskFlag
$taskExit = $LASTEXITCODE
$taskReport = ($taskRaw -join "`n") | ConvertFrom-Json
if ($CaptureProbes -and $taskReport.probe_windows.Count -ne 48) { throw '48 captured windows required.' }
$taskMetadata = [ordered]@{
    date = (Get-Date).ToString('o')
    cpu = (Get-CimInstance Win32_Processor).Name.Trim()
    rustc = [string](& rustc --version)
    source_head = [string](& git rev-parse HEAD)
    executable_sha256 = (Get-FileHash -LiteralPath $taskBench -Algorithm SHA256).Hash
    scene_source_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/examples/bench_ladder_recovery_output.rs') -Algorithm SHA256).Hash
    solver_source_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/src/circuit66.rs') -Algorithm SHA256).Hash
    iterations_limit = 16
    line_search_limit = 16
    kcl_limit_a = 1e-11
    kcl_audit_stride_samples = 64
    deadline_measured = $false
}
$taskReport | Add-Member -NotePropertyName metadata -NotePropertyValue $taskMetadata
$taskReport | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Output -Encoding utf8
if ($taskExit -ne 0 -or -not $taskReport.passed) { throw "Stress failed; diagnostic report saved to $Output" }
[pscustomobject]@{
    passed = $taskReport.passed
    scenes = $taskReport.runs.Count
    accepted_samples = ($taskReport.runs | Measure-Object accepted_samples -Sum).Sum
    fallback_count = ($taskReport.runs | Measure-Object fallback_count -Sum).Sum
    kcl_audits = ($taskReport.runs | Measure-Object kcl_audits -Sum).Sum
    c10_hold_checks = ($taskReport.runs | Measure-Object c10_open_history_checks -Sum).Sum
    max_kcl_a = ($taskReport.runs | Measure-Object max_kcl_a -Maximum).Maximum
    max_audited_kcl_a = ($taskReport.runs | Measure-Object audited_kcl_max_a -Maximum).Maximum
    maximum_residual_evaluations = ($taskReport.runs | Measure-Object max_residual_evaluations -Maximum).Maximum
} | Format-List
