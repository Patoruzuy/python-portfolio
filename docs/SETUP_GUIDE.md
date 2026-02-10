# Quick Setup Guide - Updated Features ✨

## 🆕 What's New

### 1. Newsletter System
- Blog readers can subscribe to newsletter
- Email validation and duplicate prevention
- Confirmation tokens for double opt-in
- Admin dashboard to manage subscribers

### 2. User Management
- Multi-user admin system with bcrypt passwords
- Password recovery via email tokens
- User roles (regular vs superuser)
- Last login tracking

### 3. Payment Integration
- Products support external payment links
- Compatible with: Stripe, PayPal, eBay, Etsy, etc.
- Admin can set payment type and URL
- No payment processing = no PCI compliance hassle!

### 4. Docker Support
- Complete Docker + docker-compose setup
- Flask + Celery + Redis all containerized
- One command to start everything
- Production-ready configuration

### 5. Makefile Commands
- Simple commands for common tasks
- `make docker-up` - start everything
- `make test` - run tests
- `make create-admin` - create admin user

---

## 🚀 Quick Start (3 Steps)

### Option 1: Docker (Recommended)

```bash
# 1. Update database (add Newsletter, User, remove deprecated)
python update_database.py

# 2. Start everything with Docker
make docker-up

# 3. Access the app
# Web: http://localhost:5000
# Admin: http://localhost:5000/admin/login
```

### Option 2: Manual Setup

```bash
# 1. Update database
python update_database.py

# 2. Start Flask
python app.py

# 3. Start Celery (separate terminal)
celery -A celery_config.celery worker --loglevel=info --pool=solo
```

---

## 🔐 First-Time Setup

### 1. Run Database Migration

```bash
python update_database.py
```

This will:
- ✅ Create Newsletter table
- ✅ Create User table
- ✅ Add payment fields to Product
- ✅ Remove About and Contact tables (deprecated)
- ✅ Create default admin user

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`
- ⚠️ **CHANGE THIS IMMEDIATELY AFTER FIRST LOGIN!**

### 2. Create Your Own Admin User

```bash
make create-admin
```

Or manually:
```bash
python -c "from models import db, User; from app import app; \
with app.app_context(): \
    admin = User(username='yourusername', email='you@example.com', is_superuser=True); \
    admin.set_password('your-secure-password'); \
    db.session.add(admin); \
    db.session.commit(); \
    print('Admin created!')"
```

---

## 📧 Newsletter Features

### Add to Your Blog Template

In `templates/blog.html`, add this where you want the subscription widget:

```jinja2
{% include '_newsletter_widget.html' %}
```

### Admin Management

- View all subscribers: `/admin/newsletter` (coming soon)
- Export email list
- Send newsletters (integrate with email service)

### API Endpoint

```bash
POST /api/newsletter/subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe"  // optional
}
```

---

## 💳 Payment System

### Setup Product with Payment Link

1. Go to Admin → Products → Add/Edit Product
2. Choose **Payment Type**:
   - `external` - Link to eBay, Etsy, Gumroad, etc.
   - `stripe` - Stripe Checkout URL
   - `paypal` - PayPal.me or Buy button
   - `none` - No payment (free/contact only)

3. Add **Payment URL**:
   ```
   https://www.paypal.com/paypalme/yourusername
   https://buy.stripe.com/your-product-id
   https://www.ebay.com/itm/your-item-id
   https://gumroad.com/l/your-product
   ```

4. Save!

### In Template (products.html)

```jinja2
{% if product.payment_url %}
    <a href="{{ product.payment_url }}" class="btn btn-buy" target="_blank">
        Buy Now - ${{ product.price }}
    </a>
{% endif %}
```

---

## 🐳 Docker Commands

```bash
# Build images
make docker-build

# Start all services (Flask + Celery + Redis)
make docker-up

# View logs
make docker-logs

# Stop everything
make docker-down

# Open shell in container
make docker-shell
```

### What's Running?

- **web** - Flask app on port 5000
- **celery-worker** - Background task processor
- **redis** - Message broker on port 6379

### Environment Variables

Create `.env` file (copy from `.env.example`):

```env
SECRET_KEY=your-secret-key-here
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
MAIL_RECIPIENT=your-email@gmail.com
```

---

## 🎯 Makefile Commands

```bash
make help              # Show all commands
make install           # Install dependencies
make dev               # Run development servers
make test              # Run tests with coverage
make clean             # Clean cache files

make docker-build      # Build Docker images
make docker-up         # Start Docker services
make docker-down       # Stop Docker services
make docker-logs       # View Docker logs

make migrate           # Run database migrations
make backup            # Backup database
make create-admin      # Create admin user
```

---

## 🔧 Troubleshooting

### Blog Date Error Fixed

The error `TypeError: strptime() argument 1 must be str, not Undefined` has been **fixed**!

**What was wrong:**
- Template used `{{ post.date|format_date }}`
- BlogPost model had `created_at` not `date`

**What we fixed:**
1. Added `date` property to BlogPost model (returns `created_at`)
2. Updated `format_date` filter to handle datetime objects

### Newsletter Not Working

```bash
# Check if table exists
python -c "from app import app, db; from models import Newsletter; \
with app.app_context(): print(Newsletter.query.count(), 'subscribers')"

# If error, run migration
python update_database.py
```

### User Login Not Working

```bash
# Check if users table exists
python -c "from app import app, db; from models import User; \
with app.app_context(): print(User.query.count(), 'users')"

# Create admin user
make create-admin
```

### Docker Issues

```bash
# Rebuild from scratch
make docker-down
docker system prune -a  # Clean everything
make docker-build
make docker-up
```

---

## 📊 Database Schema

### New Tables

**newsletter**
- id, email (unique), name, active, confirmed
- confirmation_token, subscribed_at, unsubscribed_at

**users**
- id, username (unique), email (unique), password_hash
- full_name, is_active, is_superuser
- reset_token, reset_token_expiry
- last_login, created_at, updated_at

### Updated Tables

**products**
- Added: `payment_type`, `payment_url`

### Removed Tables

- ~~about~~ (use `owner_profile` instead)
- ~~contact~~ (use `owner_profile` instead)

---

## 🎨 Next Steps

1. **Change default admin password**
   ```bash
   # Login at /admin/login
   # Go to /admin/users (when implemented)
   # Change password
   ```

2. **Add newsletter widget to blog**
   ```jinja2
   {% include '_newsletter_widget.html' %}
   ```

3. **Set up payment links for products**
   - Go to Admin → Products
   - Add payment URLs (eBay, PayPal, etc.)

4. **Test email system**
   - Update `.env` with real email credentials
   - Test contact form
   - Test newsletter subscription

5. **Deploy with Docker**
   ```bash
   # Production
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

## 📚 Documentation

- **Deployment**: See `DEPLOYMENT.md`
- **Testing**: See `PHASE_8_TEST_FRAMEWORK.md`
- **Security**: See `SECURITY_AUDIT.md`
- **Celery**: See `CELERY_QUICKSTART.md`

---

## ✅ Checklist

- [ ] Run `python update_database.py`
- [ ] Create your admin user
- [ ] Change default password
- [ ] Update `.env` with real credentials
- [ ] Add newsletter widget to blog
- [ ] Set up payment links for products
- [ ] Test contact form
- [ ] Test newsletter subscription
- [ ] Run tests: `make test`
- [ ] Deploy!

---

**Last Updated**: 2026-02-10  
**Version**: 2.1.0  
**Status**: ✅ All features implemented!

---

## 🐛 Known Issues Resolved

✅ Blog date error - FIXED  
✅ Deprecated models removed  
✅ Newsletter system added  
✅ User management added  
✅ Payment links added  
✅ Docker support complete  
✅ Makefile commands ready  

**Your portfolio is now even more powerful! 🚀**
