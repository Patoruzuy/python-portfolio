# Database Backup and Restore Utility for Python Portfolio
# Usage: .\scripts\db-backup.ps1 [command]
#
# Commands:
#   backup      - Create a timestamped backup
#   list        - List all available backups
#   restore     - Restore from a backup (interactive)
#   auto-backup - Create/update auto-backup-portfolio.db

param(
    [Parameter(Position=0)]
    [string]$Command = "backup"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$DbPath = Join-Path $ProjectRoot "instance\portfolio.db"
$BackupDir = Join-Path $ProjectRoot "backups"

# Ensure backup directory exists
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "✅ Created backups directory" -ForegroundColor Green
}

function Backup-Database {
    if (-not (Test-Path $DbPath)) {
        Write-Host "❌ Database not found: $DbPath" -ForegroundColor Red
        exit 1
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $BackupDir "portfolio_backup_$timestamp.db"
    
    try {
        Copy-Item -Path $DbPath -Destination $backupFile -Force
        $size = (Get-Item $backupFile).Length / 1KB
        Write-Host "✅ Backup created: $backupFile" -ForegroundColor Green
        Write-Host "   Size: $([math]::Round($size, 2)) KB" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Backup failed: $_" -ForegroundColor Red
        exit 1
    }
}

function AutoBackup-Database {
    if (-not (Test-Path $DbPath)) {
        Write-Host "⚠️  No database found to backup" -ForegroundColor Yellow
        return
    }

    $autoBackupFile = Join-Path $BackupDir "auto-backup-portfolio.db"
    
    try {
        Copy-Item -Path $DbPath -Destination $autoBackupFile -Force
        Write-Host "✅ Auto-backup updated: $autoBackupFile" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Auto-backup failed: $_" -ForegroundColor Red
        exit 1
    }
}

function List-Backups {
    Write-Host "`n📦 Available Database Backups:" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Gray
    
    $backups = Get-ChildItem -Path $BackupDir -Filter "*.db" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    
    if ($backups.Count -eq 0) {
        Write-Host "No backups found" -ForegroundColor Yellow
        return
    }
    
    foreach ($backup in $backups) {
        $size = $backup.Length / 1KB
        $age = (Get-Date) - $backup.LastWriteTime
        
        $ageStr = if ($age.Days -gt 0) {
            "$($age.Days)d ago"
        } elseif ($age.Hours -gt 0) {
            "$($age.Hours)h ago"
        } else {
            "$($age.Minutes)m ago"
        }
        
        $nameColor = if ($backup.Name -eq "auto-backup-portfolio.db") { "Yellow" } else { "White" }
        
        Write-Host "  📄 " -NoNewline
        Write-Host $backup.Name -ForegroundColor $nameColor -NoNewline
        Write-Host " ($([math]::Round($size, 2)) KB, $ageStr)" -ForegroundColor Gray
    }
    
    Write-Host ("=" * 80) -ForegroundColor Gray
    Write-Host ""
}

function Restore-Database {
    List-Backups
    
    Write-Host "Enter backup filename to restore (or 'q' to quit): " -NoNewline -ForegroundColor Cyan
    $filename = Read-Host
    
    if ($filename -eq 'q' -or $filename -eq '') {
        Write-Host "Restore cancelled" -ForegroundColor Yellow
        return
    }
    
    $backupFile = Join-Path $BackupDir $filename
    
    if (-not (Test-Path $backupFile)) {
        Write-Host "❌ Backup file not found: $filename" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n⚠️  WARNING: This will overwrite your current database!" -ForegroundColor Yellow
    Write-Host "Current database: $DbPath" -ForegroundColor Gray
    Write-Host "Restore from: $backupFile" -ForegroundColor Gray
    Write-Host "`nContinue? (y/N): " -NoNewline -ForegroundColor Cyan
    $confirm = Read-Host
    
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Restore cancelled" -ForegroundColor Yellow
        return
    }
    
    try {
        # Create a safety backup first
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $safetyBackup = Join-Path $BackupDir "before_restore_$timestamp.db"
        
        if (Test-Path $DbPath) {
            Copy-Item -Path $DbPath -Destination $safetyBackup -Force
            Write-Host "✅ Safety backup created: before_restore_$timestamp.db" -ForegroundColor Green
        }
        
        # Restore the backup
        Copy-Item -Path $backupFile -Destination $DbPath -Force
        Write-Host "✅ Database restored successfully!" -ForegroundColor Green
        Write-Host "   Restored from: $filename" -ForegroundColor Gray
    }
    catch {
        Write-Host "❌ Restore failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "backup" {
        Write-Host "`n🔄 Creating database backup..." -ForegroundColor Cyan
        Backup-Database
    }
    "auto-backup" {
        Write-Host "`n🔄 Creating auto-backup..." -ForegroundColor Cyan
        AutoBackup-Database
    }
    "list" {
        List-Backups
    }
    "restore" {
        Restore-Database
    }
    default {
        Write-Host "`n❌ Unknown command: $Command" -ForegroundColor Red
        Write-Host "`nUsage: .\scripts\db-backup.ps1 [command]" -ForegroundColor Yellow
        Write-Host "`nCommands:"
        Write-Host "  backup      - Create a timestamped backup"
        Write-Host "  auto-backup - Create/update auto-backup-portfolio.db"
        Write-Host "  list        - List all available backups"
        Write-Host "  restore     - Restore from a backup (interactive)"
        Write-Host ""
        exit 1
    }
}
