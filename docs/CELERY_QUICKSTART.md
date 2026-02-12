# Celery Quick Start - FIXED ✅

## Issue Resolved

The Celery command was pointing to the wrong module. This has been fixed.

## Correct Commands

### Start Celery Worker

**Windows** (use `--pool=solo`):
```bash
celery -A celery_config.celery worker --loglevel=info --pool=solo
```

**macOS/Linux**:
```bash
celery -A celery_config.celery worker --loglevel=info
```

### Start Flask App

```bash
python app.py
```

---

## Redis Setup (Required for Celery)

### Windows Options

**Option 1: Memurai (Redis for Windows)**
```bash
winget install Memurai.Memurai-Developer
# Or download from: https://www.memurai.com/
```

**Option 2: Redis via WSL**
```bash
# Install WSL first if not already installed
wsl --install

# In WSL terminal:
sudo apt update
sudo apt install redis-server
redis-server
```

**Option 3: Docker**
```bash
docker run -d -p 6379:6379 redis:alpine
```

### macOS

```bash
brew install redis
brew services start redis
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

---

## Verify Redis is Running

```bash
# Test connection
redis-cli ping
# Should return: PONG
```

---

## Testing Without Redis

If Redis is not installed, the app will still run but:
- Contact form emails will fail silently
- `.delay()` calls will raise exceptions

**Temporary workaround** (for testing only):
```python
# In app.py routes, replace:
send_contact_email.delay(contact_data)

# With:
send_contact_email(contact_data)  # Synchronous call
```

---

## File Changes Made

### ✅ Fixed Files

1. **celery_config.py**
   - Created standalone `celery` instance
   - Added `include=['tasks.email_tasks']` for auto-discovery
   - Made `make_celery()` integrate Flask context

2. **tasks/email_tasks.py**
   - Updated import: `from celery_config import celery`
   - Removed `make_celery(app)` call

3. **app.py**
   - Updated to use: `from celery_config import celery`
   - Call `make_celery(app)` to integrate Flask context

---

## Testing Celery

### 1. Start Redis
```bash
redis-server  # or appropriate command for your OS
```

### 2. Start Celery Worker (Terminal 1)
```bash
cd C:\Users\soyse.TIBURON\Documents\python-portfolio
.venv\Scripts\activate
celery -A celery_config.celery worker --loglevel=info --pool=solo
```

### 3. Start Flask App (Terminal 2)
```bash
cd C:\Users\soyse.TIBURON\Documents\python-portfolio
.venv\Scripts\activate
python app.py
```

### 4. Test Contact Form
- Go to: http://localhost:5000/contact
- Fill out form
- Submit
- Check Celery worker terminal for task execution

---

## Celery Status Commands

```bash
# Check active tasks
celery -A celery_config.celery inspect active

# Check registered tasks
celery -A celery_config.celery inspect registered

# Check worker stats
celery -A celery_config.celery inspect stats

# Purge all tasks
celery -A celery_config.celery purge
```

---

## Production Deployment

In production with systemd:

```ini
[Unit]
Description=Celery Worker for Portfolio
After=network.target redis.service

[Service]
Type=simple
User=portfolio
Group=portfolio
WorkingDirectory=/var/www/portfolio
Environment="PATH=/var/www/portfolio/venv/bin"
ExecStart=/var/www/portfolio/venv/bin/celery -A celery_config.celery worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Summary

✅ **Issue**: Wrong Celery command (`celery -A tasks.email_tasks`)  
✅ **Fix**: Use `celery -A celery_config.celery`  
✅ **Files Updated**: 3 files (celery_config.py, tasks/email_tasks.py, app.py)  
✅ **Next Step**: Install Redis and test

---

**Last Updated**: 2026-02-09  
**Status**: Fixed ✅
