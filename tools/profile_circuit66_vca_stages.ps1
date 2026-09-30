param([Parameter(Mandatory)][string]$Output,[int]$Runs=5)
$ErrorActionPreference='Stop'
if ($Runs -lt 3) { throw 'Use at least three alternating pairs.' }
$taskRepo=Split-Path -Parent $PSScriptRoot
$taskExe=Join-Path $taskRepo 'target/release/examples/circuit66_admission.exe'
$taskOracle=Get-Content (Join-Path $taskRepo 'evidence/circuit66_vca_jump_vectors.json') -Raw | ConvertFrom-Json

function Invoke-StageProbe([int]$Count) {
    $taskRaw=& $taskExe '--vca-jump' "--vca-stages=$Count"
    $taskExit=$LASTEXITCODE
    $taskReport=($taskRaw -join "`n") | ConvertFrom-Json
    if ($taskExit -ne 0 -or -not $taskReport.passed) {
        return [pscustomobject]@{stages=$Count;passed=$false;diagnostic=$taskReport;exit_code=$taskExit}
    }
    if ($taskReport.cases.Count -ne 6) { throw 'Complete six-case probe required.' }
    $taskMaxNode=0.0; $taskMaxCap=0.0; $taskMaxJack=0.0; $taskMaxTail=0.0; $taskMaxKcl=0.0
    for ($taskCase=0; $taskCase -lt 6; $taskCase++) {
        $taskNative=$taskReport.cases[$taskCase]; $taskRef=$taskOracle.cases[$taskCase]
        if ($taskNative.mode -ne $taskRef.mode -or $taskNative.r61_ohm -ne $taskRef.r61_ohm -or $taskNative.rows.Count -ne 64) { throw 'Case identity/length mismatch.' }
        for ($taskSample=0; $taskSample -lt 64; $taskSample++) {
            $taskRow=$taskNative.rows[$taskSample]; $taskExpected=$taskRef.rows[$taskSample]
            if ($taskRow.sample -ne $taskExpected.sample -or $taskRow.bus_v -ne $taskExpected.boundary.bus_v -or $taskRow.loudness_v -ne $taskExpected.boundary.loudness_v -or $taskRow.q21_base_v -ne $taskExpected.boundary.q21_base_v) { throw 'Stimulus mismatch.' }
            for ($taskNode=0; $taskNode -lt 66; $taskNode++) { $taskMaxNode=[Math]::Max($taskMaxNode,[Math]::Abs($taskRow.node_v[$taskNode]-$taskExpected.node_v[$taskNode])) }
            for ($taskCap=0; $taskCap -lt 17; $taskCap++) { $taskMaxCap=[Math]::Max($taskMaxCap,[Math]::Abs($taskRow.capacitor_v[$taskCap]-$taskExpected.capacitor_v[$taskCap])) }
            $taskMaxCap=[Math]::Max($taskMaxCap,[Math]::Abs($taskRow.c10_v-$taskExpected.c10_v))
            foreach ($taskJack in 'j7_v','j4_hi_v','j5_lo_v') { $taskMaxJack=[Math]::Max($taskMaxJack,[Math]::Abs($taskRow.$taskJack-$taskExpected.$taskJack)) }
            $taskMaxTail=[Math]::Max($taskMaxTail,[Math]::Abs($taskRow.tail_current_a-$taskExpected.tail_current_a))
            $taskMaxKcl=[Math]::Max($taskMaxKcl,$taskRow.kcl_a)
        }
    }
    $taskPassed=$taskMaxNode -lt 1e-6 -and $taskMaxCap -lt 1e-6 -and $taskMaxJack -lt 1e-6 -and $taskMaxTail -lt 1e-9 -and $taskMaxKcl -lt 1e-11
    return [pscustomobject]@{stages=$Count;passed=$taskPassed;max_node_error_v=$taskMaxNode;max_capacitor_error_v=$taskMaxCap;max_jack_error_v=$taskMaxJack;max_tail_error_a=$taskMaxTail;max_kcl_a=$taskMaxKcl;
        mean_kernel_block_us=($taskReport.cases | Measure-Object block_us -Average).Average;
        worst_sample_us=($taskReport.cases | Measure-Object max_sample_us -Maximum).Maximum;
        deadline_misses=($taskReport.cases | Where-Object block_us -gt (64/48000*1e6)).Count;
        continuations=($taskReport.cases | Measure-Object continuations -Sum).Sum;steps=384;cases=$taskReport.cases | Select-Object mode,r61_ohm,continuations,block_us,max_sample_us}
}

$taskSurvey=@(1,2,4,8,16,32 | ForEach-Object { Invoke-StageProbe $_ })
# Warm complete sweeps, excluded from the timed-pair summary.
$taskWarm=@(Invoke-StageProbe 8; Invoke-StageProbe 32)
if ($taskWarm.Where({-not $_.passed}).Count) { throw '8/32 comparison candidates failed quality gates.' }
$taskPairs=@()
foreach ($taskRun in 1..$Runs) {
    $taskOrder=if ($taskRun % 2) { @(32,8) } else { @(8,32) }
    foreach ($taskStages in $taskOrder) {
        $taskRecord=Invoke-StageProbe $taskStages
        if (-not $taskRecord.passed) { throw 'Timed candidate failed quality gates.' }
        $taskRecord | Add-Member run $taskRun
        $taskPairs+=$taskRecord
    }
}
$taskBefore=($taskPairs | Where-Object stages -eq 32 | Measure-Object mean_kernel_block_us -Average).Average
$taskAfter=($taskPairs | Where-Object stages -eq 8 | Measure-Object mean_kernel_block_us -Average).Average
$taskResult=[ordered]@{schema='rf-d/circuit66-vca-stage-profile/v1';passed=$true;date=(Get-Date).ToString('o');source_head=[string](& git rev-parse HEAD);
    cpu=(Get-CimInstance Win32_Processor).Name.Trim();rustc=[string](& rustc --version);executable_sha256=(Get-FileHash $taskExe).Hash;
    circuit_source_sha256=(Get-FileHash (Join-Path $taskRepo 'crates/rf-d-circuit/src/circuit66.rs')).Hash;
    admission_source_sha256=(Get-FileHash (Join-Path $taskRepo 'crates/rf-d-circuit/examples/circuit66_admission.rs')).Hash;
    profile_source_sha256=(Get-FileHash -LiteralPath $PSCommandPath).Hash;oracle_sha256=(Get-FileHash (Join-Path $taskRepo 'evidence/circuit66_vca_jump_vectors.json')).Hash;
    gates=[ordered]@{node_v=1e-6;capacitor_v=1e-6;jack_v=1e-6;tail_a=1e-9;kcl_a=1e-11};survey=$taskSurvey;warmup=$taskWarm;pairs=$taskPairs;
    baseline_stages=32;candidate_stages=8;baseline_mean_kernel_block_us=$taskBefore;candidate_mean_kernel_block_us=$taskAfter;cost_change_percent=100*($taskAfter/$taskBefore-1);
    timing_scope='sum of per-sample kernel clocks including primary failure and rescue; excludes JSON capture/serialization; no host deadline admission';
    audio_fidelity_claim=$false;audio_deadline_claim=$false}
$taskResult | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $Output -Encoding utf8
[pscustomobject]@{before_us=$taskBefore;after_us=$taskAfter;cost_change_percent=$taskResult.cost_change_percent} | Format-List
