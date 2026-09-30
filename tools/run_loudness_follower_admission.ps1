param([string]$Output = "evidence/loudness_follower_native.json")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $exe = Join-Path $root "target/release/examples/loudness_follower_admission.exe"
    if (!(Test-Path -LiteralPath $exe)) { throw "Build cargo example loudness_follower_admission --release first" }
    $report = (& $exe | ConvertFrom-Json)
    $nativeExit = $LASTEXITCODE
    $hashes = [ordered]@{}
    foreach ($path in @("crates/rf-d-circuit/src/loudness_follower.rs",
        "crates/rf-d-circuit/examples/loudness_follower_admission.rs",
        "evidence/loudness_follower_vectors.json", "tools/loudness_follower_vectors.py")) {
        $hashes[$path] = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
    }
    $result = [ordered]@{
        date_utc = [DateTime]::UtcNow.ToString("o")
        git_head = (& git rev-parse HEAD).Trim()
        rustc = (& rustc --version).Trim()
        cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name.Trim()
        exe_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLowerInvariant()
        source_sha256 = $hashes
        numerical_port_admission = $report
        whole_engine_deadline_admitted = $false
    }
    $result | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath $Output -Encoding utf8
    if ($nativeExit -ne 0 -or !$report.passed) { throw "Native port quality failed; evidence retained at $Output" }
    $report | ConvertTo-Json -Depth 8
} finally { Pop-Location }
