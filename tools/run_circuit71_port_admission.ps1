param([string]$Output = "evidence/circuit71_port_native.json")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $exe = Join-Path $root "target/release/examples/circuit71_port_admission.exe"
    if (!(Test-Path -LiteralPath $exe)) { throw "Build circuit71_port_admission --release first" }
    $report = (& $exe | ConvertFrom-Json)
    $nativeExit = $LASTEXITCODE
    $hashes = [ordered]@{}
    foreach ($path in @("crates/rf-d-circuit/src/circuit71.rs", "crates/rf-d-circuit/src/circuit66.rs",
        "crates/rf-d-circuit/src/loudness_follower.rs", "crates/rf-d-circuit/src/output_conversion.rs",
        "crates/rf-d-circuit/examples/circuit71_port_admission.rs", "crates/rf-d-circuit/examples/circuit71_admission.rs",
        "crates/rf-d-circuit/examples/bench_ladder_recovery_output.rs", "evidence/circuit71_port_vectors.json",
        "tools/circuit71_port_vectors.py", "tools/circuit71_loudness_vectors.py")) {
        $hashes[$path] = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    }
    $result = [ordered]@{
        date_utc = [DateTime]::UtcNow.ToString("o")
        git_head = (& git rev-parse HEAD).Trim()
        rustc = (& rustc --version).Trim()
        cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name.Trim()
        exe_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLowerInvariant()
        source_sha256 = $hashes
        numerical_admission = $report
        whole_engine_deadline_admitted = $false
    }
    $result | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $Output -Encoding utf8
    if ($nativeExit -ne 0 -or !$report.passed) { throw "Joint port quality failed; evidence retained at $Output" }
    $report | ConvertTo-Json -Depth 8
} finally { Pop-Location }
