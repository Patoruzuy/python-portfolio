# Login System Configuration

## 🔐 How It Works

Your admin panel uses **session-based authentication** with **password hashing**:

1. **You login** at `/admin/login`
2. **Session created** - stored in browser cookies
3. **Session persists** even after closing browser
4. **Password hashed** - never stored in plain text

✅ **Simple, secure, no database needed!**

---

## 🚀 Quick Start

### Option 1: Use Default (Testing Only)

**Default credentials:**
- Username: `admin`
- Password: `password`

⚠️ **Change this before deployment!**

### Option 2: Set Custom Password (Recommended)

**1. Generate your password hash:**
```bash
python scripts/generate_password.py
```

**2. Choose one method:**

**Method A: Using .env file (Best)**
```env
# Add to .env file
ADMIN_USERNAME=your_username
ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$...your_hash...
```

**Method B: Edit admin_routes.py directly**
```python
# Line 15-18 in admin_routes.py
ADMIN_USERNAME = 'your_username'
ADMIN_PASSWORD_HASH = 'pbkdf2:sha256:600000$...your_hash...'
```

---

## 🔒 Security Features

✅ **Password Hashing** - Uses pbkdf2:sha256 (industry standard)  
✅ **Session Security** - Encrypted session cookies  
✅ **Login Required** - Decorator protects all admin routes  
✅ **Persistent Sessions** - Stay logged in after browser close  
✅ **Flash Messages** - User feedback for login attempts  

---

## 📋 Change Your Password

**Step by step:**

1. **Run the generator:**
   ```bash
   python scripts/generate_password.py
   ```

2. **Enter your desired password** (8+ characters recommended)

3. **Copy the generated hash**

4. **Add to .env file:**
   ```env
   ADMIN_USERNAME=myusername
   ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$abc123...
   ```

5. **Restart Flask server**

6. **Login with new credentials!**

---

## 🎯 For Single User (You)

This setup is **perfect for single-user portfolios**:

- ✅ No complex user management
- ✅ No database required
- ✅ Secure password hashing
- ✅ Session-based (no tokens/JWT overhead)
- ✅ Easy to change password
- ✅ Stays logged in between sessions

---

## 🛡️ Additional Security (Optional)

For extra protection, add these to app.py:

```python
# Session security
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Auto-logout
```

---

## ❓ Troubleshooting

**Can't login with default password:**
- Make sure you're using: `admin` / `password`
- Clear browser cookies
- Check console for errors

**Generated password not working:**