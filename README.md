# Python Developer Portfolio

**Production-Ready Flask Portfolio** with Docker, Celery, Newsletter, User Management, and Payment Integration.

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start everything
make docker-up

# 3. Access
# - Website: http://localhost:5000
# - Admin: http://localhost:5000/admin/login
# - Default login: admin / admin123 (CHANGE THIS!)
```

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python scripts/update_database.py

# 3. Start Flask
python app.py

# 4. Start Celery (separate terminal)
celery -A celery_config.celery worker --loglevel=info --pool=solo
```

---

## 🔐 Admin Access

**Admin Panel:** http://localhost:5000/admin/login

**Default Credentials:**
- Username: `admin`
- Password: `admin123`

⚠️ **Security Notice:** 
- Change these credentials immediately in production!
- Run `python scripts/generate_password.py` to create a new password hash
- Add the hash to your `.env` file as `ADMIN_PASSWORD_HASH`
- Optionally set `ADMIN_USERNAME` in `.env`

---

## ✨ Features

- 📝 **Blog System** - Markdown posts with syntax highlighting
- 📧 **Newsletter** - Email subscription management
- 🛒 **Products** - E-commerce with external payment links
- 🔌 **Raspberry Pi Projects** - IoT showcase
- 👤 **User Management** - Multi-admin with password recovery
- ⚡ **Async Tasks** - Celery-powered background jobs
- 🔒 **Security** - CSP, CSRF, bcrypt, rate limiting
- 🐳 **Docker Ready** - Complete containerization
- ✅ **Tested** - 95 tests, 70%+ coverage

---

## 📚 Documentation

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Detailed setup instructions
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Common tasks and commands
- **[Testing](docs/TESTING.md)** - Test suite documentation
- **[Deployment](docs/DEPLOYMENT.md)** - Production deployment guide
- **[Celery](docs/CELERY_QUICKSTART.md)** - Async task configuration
- **[Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)** - Pre-deploy checklist
- **[Login Guide](docs/LOGIN_GUIDE.md)** - Admin authentication setup
- **[Admin CRUD Guide](docs/ADMIN_CRUD_COMPLETE.md)** - Admin management walkthrough

---

## 🛠️ Tech Stack

- **Backend**: Flask 3.0, SQLAlchemy 2.0, Celery 5.3
- **Database**: SQLite (dev) → PostgreSQL (production)
- **Cache/Queue**: Redis 7.0
- **Testing**: pytest 8.4, 95 tests, 70%+ coverage
- **Security**: Talisman, CSP, CSRF, bcrypt
- **Deployment**: Docker, nginx, GitHub Actions

---

## 📋 Makefile Commands

```bash
make help          # Show all commands
make docker-up     # Start all services
make docker-down   # Stop services
make test          # Run tests
make create-admin  # Create admin user
make backup        # Backup database
make generate-password  # Generate admin password hash
make reset-admin   # Reset admin credentials
make cache-bust    # Generate static asset manifest
make placeholders  # Generate placeholder images
```

---

## 🔐 Default Admin

**Login**: http://localhost:5000/admin/login
- Username: `admin`
- Password: `admin123`
- ⚠️ **CHANGE IMMEDIATELY!**

Create your own admin:
```bash
make create-admin
```

---

## 📂 Project Structure

```
python-portfolio/
├── app.py                  # Main Flask app
├── models.py               # Database models
├── admin_routes.py         # Admin panel routes
├── celery_config.py        # Async task config
├── docker-compose.yml      # Docker services
├── Dockerfile              # Container definition
├── Makefile                # Command shortcuts
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── templates/              # Jinja2 templates
├── static/                 # CSS, JS, images
├── tasks/                  # Celery tasks
└── tests/                  # Test suite
```

---

## 🌐 API Endpoints

```
POST /api/contact           # Contact form submission
POST /api/newsletter/subscribe  # Newsletter subscription
GET  /api/projects          # Projects list (JSON)
GET  /api/blog              # Blog posts (JSON)
GET  /health                # Health check
```

---

## 🚢 Deployment

### Production with Docker

```bash
# Update docker-compose.yml for production
# Set strong passwords in .env
docker-compose up -d

# Or use nginx
# See docs/DEPLOYMENT.md
```

### GitHub Actions

Push to `main` triggers automatic:
- Linting & testing
- Security scanning
- Build & deployment
- Database backup

---

## 🧪 Testing

```bash
# Run all tests
make test

# With coverage report
pytest tests/ --cov=. --cov-report=html

# View coverage
open htmlcov/index.html
```

---

## 📊 Database Models

- **User** - Admin users with password recovery
- **OwnerProfile** - Portfolio owner information
- **BlogPost** - Blog articles with auto-slug
- **Product** - Products with payment links
- **RaspberryPiProject** - IoT projects
- **Newsletter** - Email subscriptions
- **SiteConfig** - Global site settings
- **PageView** - Analytics tracking

---

## 🔒 Security

✅ Content Security Policy (CSP)  
✅ CSRF Protection  
✅ Bcrypt Password Hashing  
✅ SQL Injection Prevention  
✅ Rate Limiting  
✅ Security Headers (HSTS, X-Frame-Options)  
✅ SSL/TLS Ready  

---

## 📧 Email Configuration

Update `.env`:

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

For Gmail, use [App Passwords](https://support.google.com/accounts/answer/185833).

---

## 💳 Payment Integration

Products support external payment links:
- PayPal: `https://paypal.me/username`
- Stripe: `https://buy.stripe.com/product-id`
- eBay: `https://ebay.com/itm/item-id`
- Gumroad: `https://gumroad.com/l/product`

No payment processing = No PCI compliance hassle!

---

## 🆘 Troubleshooting

### Port Conflicts

```bash
# Redis already running locally?
make docker-down
# Kill local Redis or use Docker only
```

### Database Issues

```bash
# Reset database
python scripts/update_database.py

# Backup first
make backup
```

### Docker Issues

```bash
# Clean rebuild
make docker-down
docker system prune -a
make docker-build
make docker-up
```

---

## 📝 License

MIT License - See LICENSE file

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Write tests
4. Submit pull request

---

## 📬 Contact

- **Portfolio**: Coming soon
- **GitHub**: [My GitHub](https://github.com/Patoruzuy)
- **Email**: [patoruzuy@tutanota.com](mailto:patoruzuy@tutanota.com)

---

**Version**: 2.1.0  
**Status**: Production Ready ✅  
**Last Updated**: February 10, 2026

---

Made with ❤️ and Python 🐍
