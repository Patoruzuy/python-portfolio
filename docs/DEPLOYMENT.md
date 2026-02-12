# Production Deployment Guide

## Overview

This guide covers deploying the Flask Python Portfolio to production with nginx, systemd, and CI/CD automation.

## Prerequisites

- Ubuntu 20.04/22.04 server (or similar Linux distro)
- Domain name pointed to server IP
- Root or sudo access
- Python 3.11+
- Git installed

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx redis-server supervisor git
```

### 2. Create Application User

```bash
sudo useradd -m -s /bin/bash portfolio
sudo usermod -aG sudo portfolio
```

### 3. Setup Application Directory

```bash
sudo mkdir -p /var/www/portfolio
sudo chown portfolio:portfolio /var/www/portfolio
cd /var/www/portfolio
```

### 4. Clone Repository

```bash
# As portfolio user
su - portfolio
cd /var/www/portfolio
git clone https://github.com/yourusername/portfolio.git .
```

### 5. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install waitress  # Production WSGI server
```

### 6. Environment Configuration

Create `.env` file:

```bash
nano .env
```

Add:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
ADMIN_PASSWORD_HASH=your-bcrypt-hash-from-admin-page

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-specific-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
MAIL_RECIPIENT=your-email@gmail.com

# Celery/Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Flask Environment
FLASK_ENV=production
```

**Security Note**: Generate strong SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 7. Initialize Database

```bash
source venv/bin/activate
python migrate_to_new_schema.py
```

## Systemd Service Configuration

### 1. Create Waitress Service

Create `/etc/systemd/system/portfolio.service`:

```ini
[Unit]
Description=Python Portfolio Flask Application
After=network.target redis.service

[Service]
Type=simple
User=portfolio
Group=portfolio
WorkingDirectory=/var/www/portfolio
Environment="PATH=/var/www/portfolio/venv/bin"
ExecStart=/var/www/portfolio/venv/bin/waitress-serve --host=127.0.0.1 --port=8000 --threads=4 --call app:app
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/www/portfolio

[Install]
WantedBy=multi-user.target
```

### 2. Create Celery Worker Service

Create `/etc/systemd/system/portfolio-celery.service`:

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
ExecStart=/var/www/portfolio/venv/bin/celery -A celery_config worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable portfolio
sudo systemctl enable portfolio-celery
sudo systemctl start portfolio
sudo systemctl start portfolio-celery

# Check status
sudo systemctl status portfolio
sudo systemctl status portfolio-celery
```

## Nginx Configuration

### 1. Copy Nginx Config

```bash
sudo cp /var/www/portfolio/nginx.conf /etc/nginx/sites-available/portfolio
```

### 2. Update Domain Name

Edit the file:
```bash
sudo nano /etc/nginx/sites-available/portfolio
```

Replace `example.com` with your actual domain.

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## SSL/TLS with Let's Encrypt

### 1. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtain Certificate

```bash
sudo certbot --nginx -d example.com -d www.example.com
```

### 3. Auto-renewal

Certbot creates a cron job automatically. Test renewal:

```bash
sudo certbot renew --dry-run
```

## Redis Configuration

### 1. Edit Redis Config

```bash
sudo nano /etc/redis/redis.conf
```

Set:
```
supervised systemd
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### 2. Restart Redis

```bash
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## Firewall Configuration

### 1. Setup UFW

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## Monitoring and Logging

### 1. View Application Logs

```bash
# Flask application logs
sudo journalctl -u portfolio -f

# Celery logs
sudo journalctl -u portfolio-celery -f

# Nginx access logs
sudo tail -f /var/log/nginx/portfolio_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/portfolio_error.log
```

### 2. Log Rotation

Create `/etc/logrotate.d/portfolio`:

```
/var/log/nginx/portfolio_*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}
```

## GitHub Actions CI/CD Setup

### 1. Repository Secrets

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

- `PRODUCTION_HOST`: Your server IP or domain
- `PRODUCTION_USER`: SSH username (portfolio)
- `SSH_PRIVATE_KEY`: SSH private key for authentication
- `SSH_PORT`: SSH port (default: 22)

### 2. Generate SSH Key Pair

On your local machine:

```bash
ssh-keygen -t ed25519 -C "github-actions"
```

Add public key to server:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519.pub portfolio@your-server
```

Copy private key to GitHub Secrets as `SSH_PRIVATE_KEY`.

### 3. Test Deployment

Push to main branch triggers deployment:

```bash
git push origin main
```

Monitor in GitHub Actions tab.

## Maintenance Tasks

### Update Application

```bash
cd /var/www/portfolio
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart portfolio
sudo systemctl restart portfolio-celery
```

### Database Backup

Manual backup:

```bash
cd /var/www/portfolio
mkdir -p backups
cp portfolio.db backups/portfolio_$(date +%Y%m%d_%H%M%S).db
```

Automated backup (cron):

```bash
crontab -e
```

Add:

```
0 2 * * * cd /var/www/portfolio && cp portfolio.db backups/portfolio_$(date +\%Y\%m\%d).db
```

### Database Restore

```bash
cd /var/www/portfolio
sudo systemctl stop portfolio
cp backups/portfolio_YYYYMMDD.db portfolio.db
sudo systemctl start portfolio
```

### Clear Cache

```bash
# Redis cache
redis-cli FLUSHALL

# Nginx cache
sudo rm -rf /var/cache/nginx/portfolio/*
sudo systemctl reload nginx
```

## Performance Tuning

### 1. Waitress Configuration

Edit `/etc/systemd/system/portfolio.service`:

```ini
# Increase threads for high traffic
ExecStart=/var/www/portfolio/venv/bin/waitress-serve --host=127.0.0.1 --port=8000 --threads=8 --channel-timeout=60 --call app:app
```

### 2. Nginx Worker Processes

Edit `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;
worker_connections 1024;
```

### 3. Redis Memory

Edit `/etc/redis/redis.conf`:

```
maxmemory 512mb
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u portfolio -n 50

# Check Python errors
cd /var/www/portfolio
source venv/bin/activate
python app.py
```

### 502 Bad Gateway

- Check if Waitress is running: `sudo systemctl status portfolio`
- Check nginx error logs: `sudo tail /var/log/nginx/portfolio_error.log`
- Verify upstream: `curl http://127.0.0.1:8000`

### Emails Not Sending

- Check Celery is running: `sudo systemctl status portfolio-celery`
- Verify Redis connection: `redis-cli ping`
- Check email credentials in `.env`

### Database Locked

- Check file permissions: `ls -la portfolio.db`
- Restart application: `sudo systemctl restart portfolio`

## Security Checklist

- [x] SSL/TLS enabled with Let's Encrypt
- [x] Firewall configured (UFW)
- [x] Strong SECRET_KEY generated
- [x] Admin password hashed (bcrypt)
- [x] CSP headers enabled
- [x] Rate limiting configured in nginx
- [x] HSTS enabled
- [x] Sensitive files blocked in nginx
- [x] Regular security updates
- [x] Redis protected (localhost only)
- [x] Environment variables in .env (not in repo)

## Health Checks

### Quick Health Check

```bash
# Application
curl http://localhost:8000

# Nginx
curl https://your-domain.com

# Redis
redis-cli ping

# Celery
cd /var/www/portfolio
source venv/bin/activate
celery -A celery_config inspect active
```

### Automated Monitoring

Consider setting up:
- UptimeRobot for uptime monitoring
- Sentry for error tracking
- CloudWatch/DataDog for metrics
- Prometheus + Grafana for advanced monitoring

## Scaling

### Horizontal Scaling (Multiple Servers)

1. Use PostgreSQL instead of SQLite
2. Centralized Redis server
3. Load balancer (nginx/HAProxy)
4. Shared session storage
5. CDN for static assets

### Vertical Scaling (Same Server)

1. Increase Waitress threads
2. Run multiple Waitress instances
3. More Celery workers
4. Larger Redis memory
5. SSD for database

---

## Support

For issues, check:
- Application logs: `sudo journalctl -u portfolio`
- Nginx logs: `/var/log/nginx/portfolio_*.log`
- GitHub Actions logs in repository

---

**Last Updated**: 2024-01-10  
**Version**: 1.0.0
