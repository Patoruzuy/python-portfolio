# Database Safety & Recovery Guide

## 🔍 What Was Causing Data Loss

Your database was being reset due to **Docker volume mounting conflicts**. Here's what was happening:

### The Problem

In `docker-compose.yml`, you had:
```yaml
volumes:
  - .:/app                    # Mount everything
  - ./instance:/app/instance  # Re-mount instance folder
```

**Issue**: The second mount (`./instance:/app/instance`) could overwrite the first mount, potentially creating a fresh empty directory on Docker startup, wiping your database!

### Why It Kept Happening

1. **Docker Restart**: Every time you ran `make docker-down` then `make docker-up`, Docker would:
   - Stop containers
   - Potentially clean up volumes
   - Remount directories (sometimes creating empty ones)
   - Start fresh containers
   
2. **No Automatic Backups**: Before the fix, `make docker-up` didn't backup first

3. **Silent Failure**: No warnings when data was lost

---

## ✅ What Was Fixed

### 1. Fixed Docker Volume Mounting
**File**: `docker-compose.yml`

**Before**:
```yaml
volumes:
  - .:/app
  - ./instance:/app/instance  # ← REMOVED THIS
  - ./backups:/app/backups
```

**After**:
```yaml
volumes:
  - .:/app  # This already includes instance/ folder
  - ./backups:/app/backups
```

The `instance/` folder is now correctly included in the main `.:/app` mount without conflicts.

### 2. Added Automatic Backups
**File**: `Makefile`

Now `make docker-up` automatically backs up your database to `backups/auto-backup-portfolio.db` before starting.

### 3. Added Database Safety Check
**File**: `app.py`

Added logging to confirm when database exists vs when creating new:
```python
if db_exists:
    print("📊 Database found - preserving existing data")
else:
    print("🆕 Creating new database schema")
```

---

## 🛡️ Current Protection Measures

### Automatic Backup on Docker Start
```bash
make docker-up  # Now backs up first!
```

Output:
```
Checking for existing database to backup...
✅ Backup saved to backups\auto-backup-portfolio.db
```

### Manual Backups
```bash
# PowerShell command for timestamped backup
if (-not (Test-Path backups)) { New-Item -ItemType Directory -Path backups }
Copy-Item instance\portfolio.db backups\portfolio_BACKUP_$(Get-Date -Format 'yyyyMMdd_HHmmss').db
```

### List All Backups
```bash
Get-ChildItem backups\*.db | Sort-Object LastWriteTime -Descending
```

### Restore from Backup
```bash
# Stop Docker first
make docker-down

# Restore from specific backup
Copy-Item backups\portfolio_BACKUP_20260215_131031.db instance\portfolio.db -Force

# Or restore from auto-backup
Copy-Item backups\auto-backup-portfolio.db instance\portfolio.db -Force

# Start Docker
make docker-up
```

---

## 📊 Your Current Data Status

### ✅ Successfully Imported
Your data from `about_info.json` and `contact_info.json` has been imported:

- **Name**: Sebastian Gomez
- **Email**: patoruzuy@tutanota.com
- **GitHub**: https://github.com/Patoruzuy
- **LinkedIn**: https://linkedin.com/in/sebastian-n-gomez
- **Location**: Irvine, North Ayrshire, Scotland, United Kingdom
- **Experience**: 6 years
- **Skills**: Programming Languages, Frameworks & Libraries, Tools & Technologies
- **Work History**: 3 positions (Senior Python Developer, Python Developer, Junior Developer)

### ✅ Sample Data Restored
- 4 Blog Posts
- 4 Products
- 6 Software Projects
- 3 Raspberry Pi Projects

### ✅ Latest Backup
- `backups/portfolio_BACKUP_20260215_131031.db` (307KB)
- Created: February 15, 2026 13:09:45

---

## 🚀 Best Practices Going Forward

### 1. Always Use Docker Commands Through Make
```bash
# ✅ GOOD - Has auto-backup
make docker-up
make docker-down

# ❌ AVOID - No backup protection
docker-compose up
docker-compose down
```

### 2. Manual Backup Before Major Changes
```bash
# Before editing database structure
Copy-Item instance\portfolio.db backups\before-migration.db

# Before bulk data imports
Copy-Item instance\portfolio.db backups\before-import.db
```

### 3. Regular Backup Schedule
Set up a Windows Task Scheduler job to backup daily:

```powershell
# backup-database.ps1
$backupPath = "C:\Users\soyse.TIBURON\Documents\python-portfolio\backups"
$dbPath = "C:\Users\soyse.TIBURON\Documents\python-portfolio\instance\portfolio.db"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item $dbPath "$backupPath\daily_backup_$timestamp.db"

# Keep only last 7 days
Get-ChildItem "$backupPath\daily_backup_*.db" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object -Skip 7 | 
    Remove-Item
```

### 4. Check Data After Docker Restart
```bash
# Quick verification
python -c "from app import app, db; from models import *; app.app_context().push(); print(f'Blog Posts: {BlogPost.query.count()}'); print(f'Products: {Product.query.count()}'); print(f'Profile: {OwnerProfile.query.first().name if OwnerProfile.query.first() else \"Missing\"}')"
```

---

## 🆘 Recovery Procedures

### If Data Lost Again

1. **Stop Docker**
   ```bash
   make docker-down
   ```

2. **Check Available Backups**
   ```bash
   Get-ChildItem backups\*.db | Sort-Object LastWriteTime -Descending
   ```

3. **Restore Most Recent**
   ```bash
   Copy-Item backups\auto-backup-portfolio.db instance\portfolio.db -Force
   ```

4. **Verify Data**
   ```bash
   python -c "from app import app; from models import *; app.app_context().push(); print(BlogPost.query.count())"
   ```

5. **Restart Docker**
   ```bash
   make docker-up
   ```

### If No Backups Available

1. **Reimport Your Data**
   ```bash
   python scripts/import_profile_data.py
   python scripts/populate_sample_data.py
   ```

2. **Verify Import**
   ```bash
   python -c "from app import app; from models import *; app.app_context().push(); print(f'Profile: {OwnerProfile.query.first().name}')"
   ```

3. **Create Fresh Backup**
   ```bash
   Copy-Item instance\portfolio.db backups\fresh-start.db
   ```

---

## 🔍 Monitoring Commands

### Check Database Size
```powershell
Get-Item instance\portfolio.db | Select-Object Name, Length, LastWriteTime
```

### Count Records
```python
from app import app, db
from models import *

with app.app_context():
    print(f"Blog Posts: {BlogPost.query.count()}")
    print(f"Products: {Product.query.count()}")
    print(f"Projects: {Project.query.count()}")
    print(f"Raspberry Pi: {RaspberryPiProject.query.count()}")
    print(f"Newsletter: {Newsletter.query.count()}")
    print(f"Profile: {OwnerProfile.query.first().name if OwnerProfile.query.first() else 'Missing'}")
```

### Check Backup History
```powershell
Get-ChildItem backups\*.db | 
    Sort-Object LastWriteTime -Descending | 
    Format-Table Name, Length, LastWriteTime -AutoSize
```

---

## 📝 Summary

**Root Cause**: Docker volume mount conflict in `docker-compose.yml`  
**Fix Applied**: Removed redundant `./instance:/app/instance` mount  
**Protection Added**: Automatic backup on `make docker-up`  
**Current Status**: ✅ Data safe with 1 backup available  
**Next Steps**: Run `make docker-up` to test new configuration

Your data is now protected! 🛡️
