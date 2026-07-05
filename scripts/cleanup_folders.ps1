$AppBase = Split-Path -Parent $PSScriptRoot

$LogDir = "$AppBase\var\log"
$NormalizedDir = "$AppBase\var\data\normalized_events"
$ChunksDir = "$AppBase\var\data\chunks"

$AiSummaryDir = "$AppBase\var\output\ai_summaries"
$RootCauseDir = "$AppBase\var\output\root_cause_reports"
$CampaignHealthDir = "$AppBase\var\output\campaign_health"

$CleanupLog = "$LogDir\cleanup.log"

$RetentionDays = 14
$Cutoff = (Get-Date).AddDays(-$RetentionDays)

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log {
    param([string]$Message)

    $Line = "$(Get-Date -Format s)Z $Message"
    Write-Host $Line
    Add-Content -Path $CleanupLog -Value $Line
}

function Cleanup-Folder {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        Write-Log "Skipping $Label : path not found"
        return
    }

    Write-Log "Cleaning $Label older than $RetentionDays days"

    Get-ChildItem -Path $Path -File -Recurse |
        Where-Object { $_.LastWriteTime -lt $Cutoff } |
        ForEach-Object {
            Write-Log "Deleting $($_.FullName)"
            Remove-Item $_.FullName -Force
        }
}

Write-Log "====================================================="
Write-Log "GlobalRoamer AI cleanup started"

Cleanup-Folder $LogDir "logs"
Cleanup-Folder $NormalizedDir "normalized events"
Cleanup-Folder $ChunksDir "chunks"

Cleanup-Folder $AiSummaryDir "AI summaries"
Cleanup-Folder $RootCauseDir "root-cause reports"
Cleanup-Folder $CampaignHealthDir "campaign health reports"

Write-Log "GlobalRoamer AI cleanup finished"
