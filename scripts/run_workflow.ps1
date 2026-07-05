$AppBase = Split-Path -Parent $PSScriptRoot

$PythonBin = "$AppBase\.venv\Scripts\python.exe"
$ConfigDir = "$AppBase\etc"

$LogDir = "$AppBase\var\log"
$WorkflowLog = "$LogDir\workflow.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Message)

    $Line = "$(Get-Date -Format s)Z $Message"
    Write-Host $Line
    Add-Content -Path $WorkflowLog -Value $Line
}

function Run-Step {
    param(
        [string]$Name,
        [string[]]$PythonArgs
    )

    Write-Log "Step: $Name"

    Write-Host "Running: $PythonBin $($PythonArgs -join ' ')"

    & $PythonBin @PythonArgs

    if ($LASTEXITCODE -ne 0) {
        Write-Log "FAILED: $Name"
        throw "$Name failed"
    }

    Write-Log "DONE: $Name"
}

Write-Log "====================================================="
Write-Log "GlobalRoamer AI workflow started"

Set-Location $AppBase

Run-Step "ingest_main" @(
    "-m", "globalroamer_ai.ingest_main",
    "--config-dir", $ConfigDir
)

Run-Step "analyze_main" @(
    "-m", "globalroamer_ai.analyze_main",
    "--config-dir", $ConfigDir,
    "--top-k", "5"
)

Run-Step "report_main" @(
    "-m", "globalroamer_ai.report_main",
    "--config-dir", $ConfigDir,
    "--max-chunks", "20"
)

Write-Log "GlobalRoamer AI workflow finished successfully"
