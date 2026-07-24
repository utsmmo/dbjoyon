param(
    [string]$ContainerName = "hotel-review-postgres",
    [string]$DatabaseName = "hotel_review_db",
    [string]$DatabaseUser = "hotel_admin",
    [string]$DatabasePassword = "hotel_admin_123",
    [string]$OutputDir = "",
    [string]$RcloneRemote = "",
    [string]$RclonePath = "hotel-review-db/daily",
    [int]$KeepLocalDays = 14
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $projectRoot "backups"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dumpName = "${DatabaseName}-${timestamp}.dump"
$containerDumpPath = "/tmp/$dumpName"
$localDumpPath = Join-Path $OutputDir $dumpName

Write-Host "Creating database dump inside container..."
docker exec $ContainerName sh -lc "export PGPASSWORD='$DatabasePassword'; pg_dump -U '$DatabaseUser' -d '$DatabaseName' -Fc -f '$containerDumpPath'"

Write-Host "Copying dump to host..."
docker cp "${ContainerName}:${containerDumpPath}" $localDumpPath

Write-Host "Removing temporary dump from container..."
docker exec $ContainerName sh -lc "rm -f '$containerDumpPath'"

Write-Host "Local backup created: $localDumpPath"

if (-not [string]::IsNullOrWhiteSpace($RcloneRemote)) {
    $remoteTarget = "${RcloneRemote}:$RclonePath"
    Write-Host "Uploading backup to Google Drive via rclone: $remoteTarget"
    rclone copy $localDumpPath $remoteTarget
    Write-Host "Upload completed."
}

if ($KeepLocalDays -gt 0) {
    Write-Host "Cleaning local backups older than $KeepLocalDays days..."
    Get-ChildItem -Path $OutputDir -Filter "*.dump" -File |
        Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$KeepLocalDays) } |
        Remove-Item -Force
}

Write-Host "Backup job finished successfully."
