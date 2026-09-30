param(
    [Parameter(Mandatory)][string]$Baseline,
    [string]$Candidate = 'target/release/examples/bench_ladder_recovery_output.exe',
    [Parameter(Mandatory)][string]$Output,
    [int]$Runs = 5
)
# Build and preserve each executable before comparing. No build overlaps timing.
$ErrorActionPreference = 'Stop'
if ($Runs -lt 3) { throw 'Use at least three alternating runs.' }
$taskBaseline = (Resolve-Path -LiteralPath $Baseline).Path
$taskCandidate = (Resolve-Path -LiteralPath $Candidate).Path
$taskRows = @()
foreach ($taskRun in 1..$Runs) {
    # Reverse pair order every run to reduce systematic order bias.
    $taskMethods = if ($taskRun % 2) { @('baseline', 'candidate') } else { @('candidate', 'baseline') }
    foreach ($taskMethod in $taskMethods) {
        $taskExe = if ($taskMethod -eq 'baseline') { $taskBaseline } else { $taskCandidate }
        $taskRaw = & $taskExe '--global' '--emphasis'
        if ($LASTEXITCODE -ne 0) { throw "Benchmark failed: $taskMethod run $taskRun" }
        $taskRecord = [ordered]@{ run = $taskRun; method = $taskMethod; raw = [string]$taskRaw }
        foreach ($taskMatch in [regex]::Matches($taskRaw, '(?<key>\w+)=(?<value>[-+\d.eE]+)(?:\s|$)')) {
            $taskRecord[$taskMatch.Groups['key'].Value] = [double]::Parse(
                $taskMatch.Groups['value'].Value, [System.Globalization.CultureInfo]::InvariantCulture)
        }
        $taskRows += [pscustomobject]$taskRecord
    }
}
$taskBefore = ($taskRows | Where-Object method -eq 'baseline' | Measure-Object mean_us -Average).Average
$taskAfter = ($taskRows | Where-Object method -eq 'candidate' | Measure-Object mean_us -Average).Average
$taskWaveRaw = & $taskCandidate '--compare' '--emphasis'
if ($LASTEXITCODE -ne 0) { throw 'Candidate waveform comparison gate failed.' }
$taskWave = [ordered]@{ raw = [string]$taskWaveRaw; passed = $true }
foreach ($taskMatch in [regex]::Matches($taskWaveRaw, '(?<key>\w+)=(?<value>[-+\d.eE]+)(?:\s|$)')) {
    $taskWave[$taskMatch.Groups['key'].Value] = [double]::Parse(
        $taskMatch.Groups['value'].Value, [System.Globalization.CultureInfo]::InvariantCulture)
}
$taskReport = [ordered]@{
    schema = 'rf-d/circuit66-variant-comparison/v1'
    date = (Get-Date).ToString('yyyy-MM-dd')
    cpu = (Get-CimInstance Win32_Processor).Name.Trim()
    rustc = [string](& rustc --version)
    source_head = [string](& git rev-parse HEAD)
    baseline_sha256 = (Get-FileHash -LiteralPath $taskBaseline -Algorithm SHA256).Hash
    candidate_sha256 = (Get-FileHash -LiteralPath $taskCandidate -Algorithm SHA256).Hash
    comparison = 'release executables, alternating pairs with reversed order every second run'
    sample_rate_hz = 48000
    warmup_samples_per_run = 8192
    measured_samples_per_run = 8192
    block_samples = 64
    baseline_mean_of_means_us = $taskBefore
    candidate_mean_of_means_us = $taskAfter
    cost_change_percent = 100 * ($taskAfter / $taskBefore - 1)
    waveform_comparison = $taskWave
    audio_fidelity_claim = $false
    runs = $taskRows
}
$taskReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding utf8
[pscustomobject]@{
    baseline_mean_us = $taskBefore
    candidate_mean_us = $taskAfter
    cost_change_percent = $taskReport.cost_change_percent
    candidate_worst_block_us = ($taskRows | Where-Object method -eq 'candidate' | Measure-Object max_us -Maximum).Maximum
    candidate_deadline_misses = ($taskRows | Where-Object method -eq 'candidate' | Measure-Object deadline_misses -Sum).Sum
    failures = ($taskRows | Measure-Object failures -Sum).Sum
    waveform_comparison_passed = $true
} | Format-List
