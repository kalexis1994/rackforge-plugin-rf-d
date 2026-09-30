# Build the release example first. Run from the RF-D repository root.
# The same executable contains both methods; each run warms and reinitializes.
$ErrorActionPreference = 'Stop'
$taskRepo = Split-Path -Parent $PSScriptRoot
$taskBench = Join-Path $taskRepo 'target/release/examples/bench_ladder_recovery_output.exe'
if (-not (Test-Path -LiteralPath $taskBench)) { throw 'Build the release example first.' }
$taskRows = @()
foreach ($taskRun in 1..5) {
    foreach ($taskMethod in @('nested', 'global')) {
        $taskFlag = if ($taskMethod -eq 'nested') { '--cutoff' } else { '--global' }
        $taskRaw = & $taskBench $taskFlag '--emphasis'
        if ($LASTEXITCODE -ne 0) { throw "Benchmark failed: $taskMethod run $taskRun" }
        $taskRecord = [ordered]@{ run = $taskRun; method = $taskMethod; raw = [string]$taskRaw }
        foreach ($taskMatch in [regex]::Matches($taskRaw, '(?<key>\w+)=(?<value>[-+\d.eE]+)(?:\s|$)')) {
            $taskRecord[$taskMatch.Groups['key'].Value] = [double]::Parse(
                $taskMatch.Groups['value'].Value, [System.Globalization.CultureInfo]::InvariantCulture)
        }
        $taskRows += [pscustomobject]$taskRecord
    }
}
$taskNested = ($taskRows | Where-Object method -eq 'nested' | Measure-Object mean_us -Average).Average
$taskGlobal = ($taskRows | Where-Object method -eq 'global' | Measure-Object mean_us -Average).Average
$taskWaveRaw = & $taskBench '--compare' '--emphasis'
if ($LASTEXITCODE -ne 0) { throw 'Waveform comparison gate failed.' }
$taskWave = [ordered]@{ raw = [string]$taskWaveRaw; passed = $true }
foreach ($taskMatch in [regex]::Matches($taskWaveRaw, '(?<key>\w+)=(?<value>[-+\d.eE]+)(?:\s|$)')) {
    $taskWave[$taskMatch.Groups['key'].Value] = [double]::Parse(
        $taskMatch.Groups['value'].Value, [System.Globalization.CultureInfo]::InvariantCulture)
}
$taskReport = [ordered]@{
    schema = 'rf-d/circuit66-deadline-comparison/v1'
    date = (Get-Date).ToString('yyyy-MM-dd')
    cpu = (Get-CimInstance Win32_Processor).Name.Trim()
    build = 'cargo release'
    rustc = [string](& rustc --version)
    comparison = 'same executable, alternating nested/global, five runs each'
    sample_rate_hz = 48000
    warmup_samples_per_run = 8192
    measured_samples_per_run = 8192
    block_samples = 64
    nested_mean_of_means_us = $taskNested
    global_mean_of_means_us = $taskGlobal
    mean_cost_ratio_nested_over_global = $taskNested/$taskGlobal
    nested_first_vca_kcl_tolerance_a = 1e-11
    global_kcl_tolerance_a = 1e-11
    waveform_comparison = $taskWave
    audio_fidelity_claim = $false
    runs = $taskRows
}
$taskOutput = Join-Path $taskRepo 'evidence/circuit66_deadline_comparison.json'
$taskReport | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskOutput -Encoding utf8
[pscustomobject]@{
    nested_mean_us = $taskNested
    global_mean_us = $taskGlobal
    cost_ratio = $taskNested/$taskGlobal
    global_worst_block_us = ($taskRows | Where-Object method -eq 'global' | Measure-Object max_us -Maximum).Maximum
    global_deadline_misses = ($taskRows | Where-Object method -eq 'global' | Measure-Object deadline_misses -Sum).Sum
    failures = ($taskRows | Measure-Object failures -Sum).Sum
    waveform_comparison_passed = $true
} | Format-List
