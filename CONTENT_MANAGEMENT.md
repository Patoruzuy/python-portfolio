# Content Management Guide

## How to Add/Edit Content (No Admin Panel Needed)

Your portfolio uses a **file-based system** - all content is stored in files, not a database. This makes it simple to manage without building an admin panel.

---

## 📝 Blog Posts

Blog posts are **markdown files** in the `blog_posts/` folder.

### Add a New Blog Post:

1. Create a file: `blog_posts/5-your-post-title.md`
2. Use this template:

```markdown
---
title: Your Post Title Here
excerpt: A brief description of your post (shown in listings)
author: Your Name
date: 2026-02-08
category: Python
tags: python, flask, web-development
read_time: 5 min
image: /static/images/your-image.jpg
---

# Your Post Content

Write your blog post content here using markdown.

## Code Examples

\```python
def hello():
    print("Hello World!")
\```

## Lists

- Item 1
- Item 2
- Item 3

## Links

[Link text](https://example.com)
```

3. Save the file - it will automatically appear on your blog page!

### Edit a Blog Post:

Simply edit the `.md` file in `blog_posts/` and save.

### Delete a Blog Post:

Delete the `.md` file from `blog_posts/`.

---

## 🚀 Projects

Projects are hardcoded in `app.py`. Open [app.py](app.py) and find the `PROJECTS` list (around line 125).

### Add a New Project:

```python
{
    'id': 5,  # Increment from last project
    'title': 'Your Project Name',
    'description': 'Brief description of what this project does',
    'technologies': ['Python', 'Flask', 'PostgreSQL'],  # List of technologies
    'category': 'Web Development',  # Category for filtering
    'github': 'https://github.com/username/repo',  # GitHub URL or None
    'demo': 'https://demo.example.com',  # Live demo URL or None
    'image': '/static/images/your-project.jpg',  # Image path
    'featured': False  # True to show on homepage
},
```

### Edit a Project:

Find the project in the `PROJECTS` list and update its properties.

### Delete a Project:

Remove the entire project dictionary from the `PROJECTS` list.

---

## 🍓 Raspberry Pi Projects

Similar to Projects, edit the `RASPBERRY_PI_PROJECTS` list in [app.py](app.py) (around line 160).

### Add a Raspberry Pi Project:

```python
{
    'id': 4,
    'title': 'Your IoT Project',
    'description': 'What this project does',
    'hardware': ['Raspberry Pi 4', 'DHT22 Sensor'],  # Hardware list
    'technologies': ['Python', 'GPIO', 'MQTT'],  # Software/protocols
    'features': [
        'Feature 1',
        'Feature 2',
        'Feature 3'
    ],
    'github': 'https://github.com/username/project',
    'image': '/static/images/your-rpi-project.jpg'
},
```

---

## 🛍️ Products

Edit the `PRODUCTS` list in [app.py](app.py) (around line 220).

### Add a Product:

```python
{
    'id': 5,
    'name': 'Your Product Name',
    'description': 'What this product offers',
    'price': 99.99,
    'type': 'digital',  # Options: 'digital', 'physical', 'service'
    'category': 'Course',  # Category name
    'features': [
        'Feature 1',
        'Feature 2',
        'Feature 3',
        'Feature 4'
    ],
    'image': '/static/images/your-product.jpg',
    'available': True  # True=Available Now, False=Coming Soon
},
```

### Edit/Delete a Product:

Update or remove the product dictionary in the `PRODUCTS` list.

---

## 🖼️ Images

### Add Images:

1. Place your image files in `static/images/`
2. Reference them in code as: `/static/images/filename.jpg`

### Current Images:

- `about-me.png` - Your profile photo (used in About page)
- `placeholder.jpg` - Default image for missing images

---

## 🔄 After Making Changes

1. **Save your files**
2. **Restart Flask server**:
   - Stop server (Ctrl+C)
   - Run: `python app.py`
3. **Refresh browser** to see changes

---

## 🎨 Quick Styling Tips

### Change Terminal Colors:

Edit `style.css` CSS variables:

```css
:root {
    --terminal-green: #58d68d;  /* Main accent color */
    --terminal-bg: #0d1117;     /* Background */
    --terminal-text: #c9d1d9;   /* Text color */
}
```

---

## 💡 Need an Admin Panel?

For easier content management, you could:

1. **Use a CMS**: Integrate with Contentful, Strapi, or WordPress API
2. **Build Simple Admin**: Create Flask routes with forms to edit data
3. **Use JSON files**: Move data from `app.py` to JSON files for easier editing
4. **Database**: Add SQLite/PostgreSQL for dynamic content management

### Simple Admin Panel Option:

I can help you create a basic admin panel with:
- Login authentication
- Forms to add/edit/delete content
- File upload for images
- No database required (updates app.py directly)

Would you like me to create this?

---

## 📚 Current Content Structure:

```
blog_posts/
├── 1-building-scalable-python-applications.md
├── 2-getting-started-raspberry-pi-python.md
├── 3-async-python-asyncio-concurrency.md
└── 4-building-devhost-application.md

static/images/
├── about-me.png  ✓
└── placeholder.jpg  ✓

app.py
├── PROJECTS (lines 125-165)
├── RASPBERRY_PI_PROJECTS (lines 167-215)
└── PRODUCTS (lines 220-285)
```
