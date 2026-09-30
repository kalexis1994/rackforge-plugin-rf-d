param(
    [ValidateSet('temporal','stack','controls','dc-seeds','vca-release','r21','vca-dc','vca-jump')][string]$Mode = 'temporal',
    [Parameter(Mandatory)][string]$Output,
    [int]$StackKib = 2048,
    [switch]$R21Endpoints,
    [switch]$VcaDcContinuation,
    [switch]$VcaJump,
    [switch]$CommonTemporalState,
    [ValidateRange(1,32)][int]$VcaStages = 32
)
# Build the release example first. Diagnostics run outside the audio thread.
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent $PSScriptRoot
$taskBench = Join-Path $taskRepo 'target/release/examples/circuit66_admission.exe'
if (-not (Test-Path -LiteralPath $taskBench)) { throw 'Build the release example first.' }
$taskArgs = @("--$Mode")
if ($Mode -eq 'stack') { $taskArgs += "--stack-kib=$StackKib" }
if ($Mode -eq 'vca-jump') { $taskArgs += "--vca-stages=$VcaStages" }
if ($R21Endpoints) {
    if ($Mode -ne 'stack') { throw 'R21Endpoints applies only to stack mode.' }
    $taskArgs += '--stack-r21'
}
if ($VcaDcContinuation) {
    if ($Mode -ne 'stack') { throw 'VcaDcContinuation applies only to stack mode.' }
    $taskArgs += '--stack-vca-dc'
}
if ($VcaJump) {
    if ($Mode -ne 'stack') { throw 'VcaJump applies only to stack mode.' }
    $taskArgs += '--stack-vca-jump'
}
if ($CommonTemporalState) {
    if ($Mode -ne 'stack') { throw 'CommonTemporalState applies only to stack mode.' }
    $taskArgs += '--stack-common-state'
}
$taskRaw = & $taskBench @taskArgs
$taskExit = $LASTEXITCODE
$taskReport = ($taskRaw -join "`n") | ConvertFrom-Json
$taskReport | Add-Member -NotePropertyName metadata -NotePropertyValue ([ordered]@{
    date = (Get-Date).ToString('o')
    cpu = (Get-CimInstance Win32_Processor).Name.Trim()
    rustc = [string](& rustc --version)
    source_head = [string](& git rev-parse HEAD)
    executable_sha256 = (Get-FileHash -LiteralPath $taskBench -Algorithm SHA256).Hash
    admission_source_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/examples/circuit66_admission.rs') -Algorithm SHA256).Hash
    lab_source_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/examples/bench_ladder_recovery_output.rs') -Algorithm SHA256).Hash
    circuit_source_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/src/circuit66.rs') -Algorithm SHA256).Hash
    output_source_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/src/output.rs') -Algorithm SHA256).Hash
    audio_deadline_claim = $false
})
if ($Mode -eq 'stack') {
    $taskReport.metadata['windows_stack_source_sha256'] = (Get-FileHash -LiteralPath (Join-Path $taskRepo 'crates/rf-d-circuit/examples/support/windows_stack.rs') -Algorithm SHA256).Hash
}
$taskReport | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Output -Encoding utf8
if ($taskExit -ne 0 -or -not $taskReport.passed) { throw "Admission probe failed; diagnostic saved to $Output" }
[pscustomobject]@{ mode=$Mode; passed=$taskReport.passed; output=$Output } | Format-List
