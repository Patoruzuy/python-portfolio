# Admin Panel Setup

## ✅ Installation Complete!

Your admin panel is ready to use.

---

## 🔐 Access the Admin Panel

1. **Start your Flask server:**
   ```bash
   python app.py
   ```

2. **Navigate to:**
   ```
   http://localhost:5000/admin
   ```

3. **Login with default credentials:**
   - **Username:** `admin`
   - **Password:** `password`

⚠️ **IMPORTANT:** Change these credentials before deploying to production!

---

## 🔧 Change Admin Credentials

### Option 1: Environment Variables (Recommended)

Add to your `.env` file:
```env
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_secure_password
```

### Option 2: Edit Code

Open `admin_routes.py` and change lines 15-16:
```python
ADMIN_USERNAME = 'your_username'
ADMIN_PASSWORD = 'your_secure_password'
```

---

## 📋 Admin Features

### Dashboard (`/admin`)
- Overview statistics
- Quick access to all sections
- Quick action buttons

### Projects (`/admin/projects`)
- View all projects
- Add new projects
- Edit existing projects (coming soon)
- Delete projects (coming soon)

### Products (`/admin/products`)
- View all products
- Manage product listings

### Blog Posts (`/admin/blog`)
- View all blog posts
- Create new blog posts
- Edit posts (coming soon)
- Delete posts (coming soon)

---

## ✨ Features

✅ **No Database Required** - Updates files directly  
✅ **Session-based Authentication** - Secure login system  
✅ **Terminal-styled Interface** - Matches your design  
✅ **Blog Post Creation** - Create markdown posts via web form  
✅ **Project Management** - Add/edit projects through UI  
✅ **Flash Messages** - User feedback for all actions  

---

## 🚀 Usage Guide

### Creating a Blog Post:

1. Go to `/admin/blog`
2. Click "Create New Post"
3. Fill in the form:
   - Title, excerpt, author
   - Date, category, tags
   - Markdown content
4. Click "Create Post"
5. File automatically saved to `blog_posts/`

### Adding a Project:

1. Go to `/admin/projects`
2. Click "Add New Project"
3. Fill in project details
4. Click "Create Project"
5. Project added to `app.py`

---

## 🔒 Security Notes

**For Production:**

1. **Change default credentials** immediately
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Enable HTTPS** for encrypted connections
4. **Add rate limiting** to prevent brute force attacks
5. **Consider using bcrypt** for password hashing
6. **Add CSRF protection** to forms
7. **Set secure session cookies:**
   ```python
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
   ```

---

## 🐛 Troubleshooting

**Can't access admin panel:**
- Ensure server is running (`python app.py`)
- Check you're using correct URL: `http://localhost:5000/admin`
- Clear browser cookies/cache

**Login not working:**
- Verify credentials in `admin_routes.py`
- Check `.env` file if using environment variables

**Changes not appearing:**
- Restart Flask server after editing `app.py`
- Refresh browser (Ctrl+F5)

---

## 📝 Next Steps

**Planned Features:**
- Edit existing projects/products
- Delete functionality
- Image upload interface
- Bulk operations
- Export/import data
- Activity logs
- Multi-user support

---

## 🎨 Customization

The admin panel uses the same terminal theme as your main site. To customize:

- **Colors:** Edit CSS in template files
- **Layout:** Modify templates in `templates/admin/`
- **Features:** Add routes in `admin_routes.py`

---

## 📞 Support

For issues or questions, refer to:
- [CONTENT_MANAGEMENT.md](CONTENT_MANAGEMENT.md) - Content management guide
- Check Flask documentation
- Review admin_routes.py for route logic

---

**🎉 Your admin panel is ready to use!**

Access it at: **http://localhost:5000/admin**
