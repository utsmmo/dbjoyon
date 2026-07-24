param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$ContainerName = "hotel-review-postgres",
    [string]$DatabaseName = "hotel_review_db",
    [string]$DatabaseUser = "hotel_admin",
    [string]$DatabasePassword = "hotel_admin_123"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

$fileName = Split-Path $BackupFile -Leaf
$containerBackupPath = "/tmp/$fileName"

Write-Host "Copying backup into container..."
docker cp $BackupFile "${ContainerName}:${containerBackupPath}"

Write-Host "Restoring database from backup..."
docker exec $ContainerName sh -lc "export PGPASSWORD='$DatabasePassword'; pg_restore -U '$DatabaseUser' -d '$DatabaseName' --clean --if-exists --no-owner --no-privileges '$containerBackupPath'"

Write-Host "Cleaning temporary restore file from container..."
docker exec $ContainerName sh -lc "rm -f '$containerBackupPath'"

Write-Host "Restore completed."
