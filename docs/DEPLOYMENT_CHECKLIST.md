# Deployment Checklist

Use this checklist before deploying to production.

---

## 🔒 Security

- [ ] Change `SECRET_KEY` in `.env` to a strong random value
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] Update default admin credentials (admin/admin123)
  ```bash
  make create-admin
  # Or manually in admin panel: /admin/login
  ```

- [ ] Set `FLASK_ENV=production` in `.env`

- [ ] Enable HTTPS/SSL certificates
  - Use Let's Encrypt with nginx
  - Update `SESSION_COOKIE_SECURE=True`

- [ ] Configure Content Security Policy (CSP)
  - Review allowed domains in `app.py` Talisman config
  - Test with browser DevTools Console

- [ ] Review rate limiting settings
  - Adjust `RATELIMIT_ENABLED` and storage URL

---

## 📧 Email

- [ ] Configure production SMTP server
  ```env
  MAIL_SERVER=smtp.gmail.com
  MAIL_USERNAME=your-email@gmail.com
  MAIL_PASSWORD=your-app-password
  ```

- [ ] Test email sending
  ```python
  # In Python shell
  from tasks.email_tasks import send_contact_email
  send_contact_email.delay("test@example.com", "Test", "Test message")
  ```

---

## 🗄️ Database

- [ ] **Production**: Switch from SQLite to PostgreSQL
  ```env
  DATABASE_URL=postgresql://user:password@host:5432/dbname
  ```

- [ ] Run migrations
  ```bash
  make migrate
  # Or: python scripts/update_database.py
  ```

- [ ] Create database backup strategy
  ```bash
  # Cron job for daily backups
  0 2 * * * cd /app && make backup
  ```

- [ ] Test database connection
  ```bash
  curl http://localhost:5000/health
  ```

---

## 🐳 Docker

- [ ] Build production images
  ```bash
  docker-compose build --no-cache
  ```

- [ ] Set resource limits in `docker-compose.yml`
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 1G
  ```

- [ ] Configure container restart policy
  ```yaml
  restart: unless-stopped
  ```

- [ ] Remove volume mounts for production (`.:/app`)
  - Keep only data volumes: `redis_data`, `postgres_data`

---

## 🔑 Environment Variables

- [ ] Create `.env` from `.env.example`
  ```bash
  cp .env.example .env
  ```

- [ ] Set all required variables:
  - `SECRET_KEY` ✅
  - `DATABASE_URL` ✅
  - `REDIS_URL` ✅
  - `MAIL_*` settings ✅
  - `ADMIN_*` credentials ✅

- [ ] **Never** commit `.env` to version control
  ```bash
  # Verify it's in .gitignore
  grep -q "^\.env$" .gitignore && echo "OK" || echo "ADD IT!"
  ```

---

## 🚀 Server Setup

- [ ] Install Docker & Docker Compose
  ```bash
  # Ubuntu
  sudo apt-get update
  sudo apt-get install docker.io docker-compose
  sudo systemctl enable docker
  ```

- [ ] Configure nginx reverse proxy
  ```nginx
  server {
      listen 80;
      server_name yourdomain.com;
      
      location / {
          proxy_pass http://localhost:5000;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }
  ```

- [ ] Set up SSL with Certbot
  ```bash
  sudo apt-get install certbot python3-certbot-nginx
  sudo certbot --nginx -d yourdomain.com
  ```

- [ ] Configure firewall
  ```bash
  sudo ufw allow 22    # SSH
  sudo ufw allow 80    # HTTP
  sudo ufw allow 443   # HTTPS
  sudo ufw enable
  ```

---

## 📊 Monitoring

- [ ] Set up logging
  - Configure log rotation
  - Use `docker-compose logs -f` or external service

- [ ] Enable error tracking (optional)
  ```env
  SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
  ```

- [ ] Monitor disk space
  ```bash
  df -h
  docker system df
  ```

- [ ] Set up uptime monitoring
  - UptimeRobot, Pingdom, or self-hosted

---

## ✅ Testing

- [ ] Run test suite
  ```bash
  make test
  ```

- [ ] Test all endpoints manually
  - [ ] Homepage: `/`
  - [ ] Blog: `/blog`
  - [ ] Blog post: `/blog/your-slug`
  - [ ] Products: `/products`