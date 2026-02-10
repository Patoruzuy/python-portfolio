# Quick Reference - Admin Panel

## 🔐 Login
- URL: http://127.0.0.1:3000/admin/login
- Username: `admin`
- Password: `password`

## 📍 All Working Routes

### ✅ Projects
- **List**: `/admin/projects`
- **Add**: `/admin/projects/add`
- **Edit**: `/admin/projects/edit/1` (change ID)
- **Delete**: Click button (confirmation required)

### ✅ Products
- **List**: `/admin/products`
- **Add**: `/admin/products/add`
- **Edit**: `/admin/products/edit/1` (change ID)
- **Delete**: Click button (confirmation required)

### ✅ Blog Posts
- **List**: `/admin/blog`
- **Create**: `/admin/blog/create`
- **Edit**: `/admin/blog/edit/1` (change ID)
- **Delete**: Click button (confirmation required)

### ✅ Raspberry Pi Projects
- **List**: `/admin/raspberry-pi`
- **Add**: `/admin/raspberry-pi/add`
- **Edit**: `/admin/raspberry-pi/edit/1` (change ID)
- **Delete**: Click button (confirmation required)

### ✅ Images
- **Upload**: `/admin/upload-image`
- Saves to: `static/images/`
- Path format: `/static/images/filename_timestamp.ext`

## 🎮 Button Status

| Feature | Status |
|---------|--------|
| Edit Projects | ✅ WORKING |
| Edit Products | ✅ WORKING |
| Edit Blog | ✅ WORKING |
| Edit RPI | ✅ WORKING |
| Delete Projects | ✅ WORKING |
| Delete Products | ✅ WORKING |
| Delete Blog | ✅ WORKING |
| Delete RPI | ✅ WORKING |
| Upload Images | ✅ WORKING |
| Add Everything | ✅ WORKING |

## 🚀 Server Status
- ✅ Flask running on port 3000
- ✅ Debug mode enabled
- ✅ No errors detected
- ✅ All templates loaded
- ✅ All routes registered

## 📝 Form Fields Quick Reference

### Project Form
- ID, Title, Description
- Technologies (comma-separated)
- Category, GitHub, Demo
- Image path
- Featured (checkbox)

### Product Form
- ID, Name, Description
- Price, Type, Category
- Features (one per line)
- Technologies (comma-separated)
- Image, Purchase link, Demo link

### Blog Post Form
- Title, Excerpt, Author
- Date, Category, Tags
- Read time, Image
- Content (markdown)

### RPI Project Form
- ID, Title, Description
- Hardware (comma-separated)
- Technologies (comma-separated)
- Features (one per line)
- GitHub, Image

---

**All buttons are now functional! 🎉**

Test by logging in and clicking Edit on any item.
