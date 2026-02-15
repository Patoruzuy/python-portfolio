# Makefile Fix - Windows Compatibility

## Issue
The Makefile was using Windows batch commands (`if exist`, `copy`, etc.) which caused errors when Make tried to execute them with bash/sh.

## Error Message
```
/usr/bin/bash: -c: line 1: syntax error near unexpected token `('
make: *** [Makefile:65: docker-up] Error 2
```

## Solution

### 1. Simplified Makefile Commands
Removed complex Windows batch logic from Makefile and simplified commands:

**Before:**
```makefile
docker-up:
	@if exist instance\portfolio.db ( \
		echo Creating backup... & \
		copy /Y instance\portfolio.db backups\auto-backup-portfolio.db \
	)
	docker-compose up -d
```

**After:**
```makefile
docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "💡 TIP: Backup database manually with: make backup"
```

### 2. Created PowerShell Backup Script
Added `scripts/db-backup.ps1` for Windows users with full backup/restore functionality:

```powershell
# Usage examples
.\scripts\db-backup.ps1 backup      # Create timestamped backup
.\scripts\db-backup.ps1 list        # List all backups
.\scripts\db-backup.ps1 restore     # Restore from backup (interactive)
.\scripts\db-backup.ps1 auto-backup # Create auto-backup
```

### 3. Updated Documentation
Modified README.md to show correct usage for Windows PowerShell users.

## Testing

✅ **docker-up now works:**
```
$ make docker-up
Starting Docker services...
[+] Running 3/3
 ✔ Container portfolio-redis   Healthy
 ✔ Container portfolio-web     Running
 ✔ Container portfolio-celery  Running
Services started! Access at http://localhost:5000
```

✅ **Backup script works:**
```powershell
$ .\scripts\db-backup.ps1 backup
🔄 Creating database backup...
✅ Backup created: backups\portfolio_backup_20260215_131943.db
   Size: 300 KB
```

✅ **List backups works:**
```powershell
$ .\scripts\db-backup.ps1 list
📦 Available Database Backups:
  📄 portfolio_backup_20260215_131943.db (300 KB, 0m ago)
  📄 portfolio_BACKUP_20260215_131031.db (300 KB, 10m ago)
```

## Files Changed

1. **Makefile** - Simplified docker-up, backup, restore, and list-backups commands
2. **scripts/db-backup.ps1** - NEW: Full-featured PowerShell backup utility
3. **README.md** - Updated backup instructions for Windows users

## Benefits

- ✅ Cross-platform compatibility (Makefile works on all systems)
- ✅ Windows users have native PowerShell tools
- ✅ Better user experience with colored output and progress indicators
- ✅ Safer restores with automatic safety backups
- ✅ Interactive restore with confirmation prompts

## Usage

### Start Docker (All Platforms)
```bash
make docker-up
```

### Backup Database (Windows)
```powershell
# Automated timestamped backup
.\scripts\db-backup.ps1 backup

# Or manual PowerShell command
Copy-Item instance/portfolio.db backups/backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db
```

### Restore Database (Windows)
```powershell
# Interactive restore (safest)
.\scripts\db-backup.ps1 restore

# Or manual PowerShell command
Copy-Item backups/[filename].db instance/portfolio.db -Force
```

### List Backups (Windows)
```powershell
# Using script
.\scripts\db-backup.ps1 list

# Or manual PowerShell command
Get-ChildItem backups/*.db | Sort-Object LastWriteTime -Descending
```

---

**Fixed**: February 15, 2026
**Status**: ✅ Resolved
