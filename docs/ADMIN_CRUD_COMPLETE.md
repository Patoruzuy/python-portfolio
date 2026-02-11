# Admin Panel - Complete CRUD Implementation

## ✅ What's Been Implemented

All Edit, Delete, and Upload functionality has been fully implemented! Here's what you can now do:

### 🎨 **Projects Management**
- ✅ **Edit Projects**: Click "Edit" on any project to modify all fields
- ✅ **Delete Projects**: Safely removes projects from app.py
- ✅ **Add Projects**: Create new projects via the form
- All changes are written directly to app.py and persist across restarts

### 🛍️ **Products Management**
- ✅ **Edit Products**: Full product editing with all fields
- ✅ **Delete Products**: Safely removes products from app.py
- ✅ **Add Products**: Create new products with pricing, features, etc.
- All changes persist in app.py

### 📝 **Blog Posts Management**
- ✅ **Edit Blog Posts**: Modify existing posts with frontmatter parsing
- ✅ **Delete Blog Posts**: Removes .md files from blog_posts/
- ✅ **Create Blog Posts**: Add new posts with markdown editor
- Files are renamed if title changes

### 🍓 **Raspberry Pi Projects Management**
- ✅ **Edit RPI Projects**: Modify hardware, technologies, and features
- ✅ **Delete RPI Projects**: Removes from app.py
- ✅ **Add RPI Projects**: Create new projects with all fields
- All changes persist in app.py

### 🖼️ **Image Upload System**
- ✅ **Upload Images**: Drag & drop or select image files
- ✅ **Supported Formats**: PNG, JPG, JPEG, GIF, WEBP
- ✅ **Automatic Naming**: Adds timestamp to prevent conflicts
- ✅ **Copy Path**: Easy copy/paste for use in forms
- Images saved to `static/images/`

## 🔧 How It Works

### Backend (admin_routes.py)
The system uses smart regex parsing to edit app.py safely:

```python
def add_item_to_file(list_name, item, formatter):
    # Finds the list in app.py
    # Formats the item as Python code
    # Inserts before closing bracket
    
def update_item_in_file(list_name, item_id, updated_item, formatter):
    # Finds the specific item by ID
    # Replaces with updated version
    # Preserves formatting
    
def delete_item_from_file(list_name, item_id):
    # Finds and removes the item
    # Cleans up commas
```

### Formatters
Each content type has a formatter that generates valid Python code:
- `format_project()` - Handles single quotes, None values
- `format_product()` - Handles prices, features lists
- `format_rpi_project()` - Handles hardware arrays

### Image Upload
Uses werkzeug's `secure_filename()` and adds timestamps:
```python
filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
```

## 📋 Using the Admin Panel

### Login
1. Go to `/admin/login`
2. Username: `admin`
3. Password: `password` (change this!)

### Editing Content
1. Navigate to the management page (Projects, Products, Blog, RPI)
2. Click "Edit" on any item
3. Modify the fields
4. Click "Update" - changes are written to app.py/files
5. Refresh the site to see changes

### Uploading Images
1. Click "Upload Images" from dashboard
2. Select your image file
3. Click "Upload Image"
4. Copy the displayed path (e.g., `/static/images/my-image_1234567890.jpg`)
5. Paste into the image field when editing/creating items

### Adding New Content
1. Click "+ Add" button on any management page
2. Fill in all required fields
3. For technologies/hardware: Use comma-separated values
4. For features: One per line
5. Click "Create" - item is appended to app.py

### Deleting Content
1. Click "Delete" on any item
2. Confirm the deletion
3. Item is removed from app.py (or .md file deleted)

## 🔒 Security Notes

### Change Default Password
Use the password generator to create a secure password:
```powershell
python scripts/generate_password.py
```

Then set in environment variables or update in admin_routes.py:
```python
ADMIN_PASSWORD_HASH = 'scrypt:32768:8:1$...'
```

### File Safety
- All edits use regex with validation
- Single quotes are escaped: `project['title'].replace("'", "\\'")`
- Trailing commas are cleaned up automatically
- Backups recommended before major edits

### Image Validation
- Only allowed extensions: png, jpg, jpeg, gif, webp
- Filenames sanitized with `secure_filename()`
- Timestamps prevent overwrites

## 📁 File Structure

```
admin_routes.py          # All CRUD routes + helper functions
templates/admin/
├── login.html           # Authentication page
├── dashboard.html       # Main admin view
├── projects.html        # Projects list + Edit/Delete buttons
├── project_form.html    # Add/Edit project form
├── products.html        # Products list + Edit/Delete buttons
├── product_form.html    # Add/Edit product form ✨ NEW
├── blog.html            # Blog list + Edit/Delete buttons
├── blog_form.html       # Create/Edit blog post
├── raspberry_pi.html    # RPI list + Edit/Delete buttons
├── rpi_form.html        # Add/Edit RPI project
└── upload_image.html    # Image upload interface ✨ NEW
```

## 🎯 Routes Summary

| Route | Method | Purpose |
|-------|--------|---------|
| `/admin/login` | GET/POST | Authentication |
| `/admin/dashboard` | GET | Admin overview |
| `/admin/projects` | GET | List projects |
| `/admin/projects/add` | GET/POST | Add project |
| `/admin/projects/edit/<id>` | GET/POST | Edit project ✨ |
| `/admin/projects/delete/<id>` | GET | Delete project ✨ |
| `/admin/products` | GET | List products |
| `/admin/products/add` | GET/POST | Add product ✨ |
| `/admin/products/edit/<id>` | GET/POST | Edit product ✨ |
| `/admin/products/delete/<id>` | GET | Delete product ✨ |
| `/admin/blog` | GET | List blog posts |