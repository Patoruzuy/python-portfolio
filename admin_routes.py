from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from functools import wraps
import os
import re
import json
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from models import db, Project, About, Contact

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', 
    'scrypt:32768:8:1$zQX8DaHbhfTCvKN9$3b2f4b1c8d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3')
# Recovery Key (Set this in env or use default for dev)
RECOVERY_KEY = os.environ.get('RECOVERY_KEY', 'python-portfolio-rescue')

# Image upload configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.before_request
def make_session_permanent():
    session.permanent = True
    # Default is 30 minutes if not "remember me"
    # This is overridden in login route, but good fallback
    if 'remember_me' not in session:
        current_app.permanent_session_lifetime = timedelta(minutes=30)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        
        # Reload credentials from env in case they changed
        global ADMIN_USERNAME, ADMIN_PASSWORD_HASH
        ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', ADMIN_USERNAME)
        ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH', ADMIN_PASSWORD_HASH)

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            
            if remember:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(days=30)
                session['remember_me'] = True
            else:
                session.permanent = True
                current_app.permanent_session_lifetime = timedelta(minutes=30)
                session.pop('remember_me', None)
                
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        key = request.form.get('recovery_key')
        new_password = request.form.get('new_password')
        
        if key == RECOVERY_KEY:
            # Generate new hash
            new_hash = generate_password_hash(new_password)
            
            # Update app.py or env approach?
            # Since admin_routes.py defines the hash constant, we might need to instruct user
            # OR we can try to update the file itself if we want to be fancy.
            # But changing running code is risky.
            # Let's flash the hash and instructions for now, OR rely on session override?
            # Better: Write a .env file update if it exists, or update admin_routes.py?
            # Updating admin_routes.py is consistent with other CRUD ops in this project.
            
            update_admin_password_in_file(new_hash)
            
            # Also update in memory for immediate use
            global ADMIN_PASSWORD_HASH
            ADMIN_PASSWORD_HASH = new_hash
            
            flash('Password reset successfully! Please login with your new password.', 'success')
            return redirect(url_for('admin.login'))
        else:
            flash('Invalid Recovery Key', 'error')
            
    return render_template('admin/forgot_password.html')

def update_admin_password_in_file(new_hash):
    """Updates the ADMIN_PASSWORD_HASH in admin_routes.py"""
    with open(__file__, 'r', encoding='utf-8') as f:
        content = f.read()
    
    pattern = r"(ADMIN_PASSWORD_HASH\s*=\s*os\.environ\.get\('ADMIN_PASSWORD_HASH',\s*)(['\"].*?['\"])"
    if re.search(pattern, content):
        new_content = re.sub(pattern, f"\\1'{new_hash}'", content)
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(new_content)

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    from app import PRODUCTS, RASPBERRY_PI_PROJECTS, BLOG_POSTS
    
    # Get counts from DB
    project_count = Project.query.count()
    
    stats = {
        'projects': project_count,
        'products': len(PRODUCTS),
        'raspberry_pi': len(RASPBERRY_PI_PROJECTS),
        'blog_posts': len(BLOG_POSTS)
    }
    return render_template('admin/dashboard.html', stats=stats)

# ============ PROJECTS ============

@admin_bp.route('/projects')
@login_required
def projects():
    # Convert DB objects to dicts for template compatibility if needed, 
    # or just pass objects if template supports dot notation (likely yes)
    # The existing template probably expects dict usage like project['id'] or project.id
    # Jinja2 handles dot notation for both usually.
    all_projects = Project.query.all()
    return render_template('admin/projects.html', projects=all_projects)

@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def add_project():
    if request.method == 'POST':
        # Create new Project from form data
        new_project = Project(
            title=request.form.get('title'),
            description=request.form.get('description'),
            technologies=request.form.get('technologies'), # Storing as string in DB
            category=request.form.get('category'),
            github_url=request.form.get('github') or None,
            demo_url=request.form.get('demo') or None,
            image_url=request.form.get('image'),
            featured=request.form.get('featured') == 'on'
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        flash('Project added successfully!', 'success')
        return redirect(url_for('admin.projects'))
    
    return render_template('admin/project_form.html', project=None)

@admin_bp.route('/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.title = request.form.get('title')
        project.description = request.form.get('description')
        project.technologies = request.form.get('technologies')
        project.category = request.form.get('category')
        project.github_url = request.form.get('github') or None
        project.demo_url = request.form.get('demo') or None
        project.image_url = request.form.get('image')
        project.featured = request.form.get('featured') == 'on'
        
        db.session.commit()
        
        flash('Project updated successfully!', 'success')
        return redirect(url_for('admin.projects'))
    
    # Template expects a dict-like object. The SQLAlchemy model will work via dot notation,
    # but we need to ensure the template uses .attribute access or we make a wrapper.
    # Checking template usage might be wise, but typically people use project.title
    # If the template does project['title'], we need a fix.
    return render_template('admin/project_form.html', project=project)

@admin_bp.route('/projects/delete/<int:project_id>')
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted successfully!', 'success')
    return redirect(url_for('admin.projects'))

# ============ PRODUCTS ============

@admin_bp.route('/products')
@login_required
def products():
    from app import PRODUCTS
    return render_template('admin/products.html', products=PRODUCTS)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        product = {
            'id': int(request.form.get('id')),
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price')),
            'type': request.form.get('type'),
            'category': request.form.get('category'),
            'features': [f.strip() for f in request.form.get('features').split('\n') if f.strip()],
            'technologies': [t.strip() for t in request.form.get('technologies').split(',')],
            'purchase_link': request.form.get('purchase_link') or None,
            'demo_link': request.form.get('demo_link') or None,
            'image': request.form.get('image')
        }
        
        add_item_to_file('PRODUCTS', product, format_product)
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', product=None)

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    from app import PRODUCTS
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin.products'))
    
    if request.method == 'POST':
        updated_product = {
            'id': int(request.form.get('id')),
            'name': request.form.get('name'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price')),
            'type': request.form.get('type'),
            'category': request.form.get('category'),
            'features': [f.strip() for f in request.form.get('features').split('\n') if f.strip()],
            'technologies': [t.strip() for t in request.form.get('technologies').split(',')],
            'purchase_link': request.form.get('purchase_link') or None,
            'demo_link': request.form.get('demo_link') or None,
            'image': request.form.get('image')
        }
        
        update_item_in_file('PRODUCTS', product_id, updated_product, format_product)
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', product=product)

@admin_bp.route('/products/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    delete_item_from_file('PRODUCTS', product_id)
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin.products'))

# ============ BLOG ============

@admin_bp.route('/blog')
@login_required
def blog():
    from app import BLOG_POSTS
    return render_template('admin/blog.html', posts=BLOG_POSTS)

@admin_bp.route('/blog/create', methods=['GET', 'POST'])
@login_required
def create_blog_post():
    if request.method == 'POST':
        from app import BLOG_POSTS
        next_id = max([p['id'] for p in BLOG_POSTS], default=0) + 1
        
        # Get slug or generate from title
        slug = request.form.get('slug')
        if not slug:
            slug = request.form.get('title')
        
        # Sanitize slug
        slug = slug.lower().strip().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        
        filename = f"{next_id}-{slug}.md"
        
        content = f"""---
title: {request.form.get('title')}
excerpt: {request.form.get('excerpt')}
author: {request.form.get('author')}
date: {request.form.get('date')}
category: {request.form.get('category')}
tags: {request.form.get('tags')}
read_time: {request.form.get('read_time')}
image: {request.form.get('image')}
---

{request.form.get('content')}
"""
        
        filepath = os.path.join('blog_posts', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        flash('Blog post created successfully!', 'success')
        return redirect(url_for('admin.blog'))
    
    return render_template('admin/blog_form.html', post=None)

@admin_bp.route('/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_blog_post(post_id):
    blog_dir = 'blog_posts'
    filename = None
    
    # Find the markdown file
    for fname in os.listdir(blog_dir):
        if fname.startswith(f"{post_id}-"):
            filename = fname
            break
    
    if not filename:
        flash('Blog post not found', 'error')
        return redirect(url_for('admin.blog'))
    
    filepath = os.path.join(blog_dir, filename)
    
    if request.method == 'POST':
        # Get slug or generate from title
        slug = request.form.get('slug')
        if not slug:
            slug = request.form.get('title')
        
        # Sanitize slug
        slug = slug.lower().strip().replace(' ', '-')
        slug = re.sub(r'[^a-z0-9-]', '', slug)
        
        new_filename = f"{post_id}-{slug}.md"
        
        content = f"""---
title: {request.form.get('title')}
excerpt: {request.form.get('excerpt')}
author: {request.form.get('author')}
date: {request.form.get('date')}
category: {request.form.get('category')}
tags: {request.form.get('tags')}
read_time: {request.form.get('read_time')}
image: {request.form.get('image')}
---

{request.form.get('content')}
"""
        
        # Remove old file if name changed
        if filename != new_filename:
            try:
                os.remove(filepath)
                filepath = os.path.join(blog_dir, new_filename)
                flash('File renamed successfully.', 'info')
            except OSError as e:
                flash(f'Error renaming file: {e}', 'error')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        flash('Blog post updated successfully!', 'success')
        return redirect(url_for('admin.blog'))
    
    # Parse existing content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract frontmatter and content
    parts = content.split('---', 2)
    if len(parts) >= 3:
        frontmatter = parts[1].strip()
        body = parts[2].strip()
        
        post = {'id': post_id}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                post[key.strip()] = value.strip()
        post['content'] = body
        # Pass current slug to template
        post['slug'] = filename.replace(f"{post_id}-", "", 1).replace(".md", "")
    else:
        post = {'id': post_id, 'title': '', 'content': content}
    
    return render_template('admin/blog_form.html', post=post)

@admin_bp.route('/blog/delete/<int:post_id>')
@login_required
def delete_blog_post(post_id):
    blog_dir = 'blog_posts'
    for filename in os.listdir(blog_dir):
        if filename.startswith(f"{post_id}-"):
            filepath = os.path.join(blog_dir, filename)
            os.remove(filepath)
            flash('Blog post deleted successfully!', 'success')
            return redirect(url_for('admin.blog'))
    
    flash('Blog post not found', 'error')
    return redirect(url_for('admin.blog'))

# ============ RASPBERRY PI ============

@admin_bp.route('/raspberry-pi')
@login_required
def raspberry_pi():
    from app import RASPBERRY_PI_PROJECTS
    return render_template('admin/raspberry_pi.html', projects=RASPBERRY_PI_PROJECTS)

@admin_bp.route('/raspberry-pi/add', methods=['GET', 'POST'])
@login_required
def add_rpi_project():
    if request.method == 'POST':
        project = {
            'id': int(request.form.get('id')),
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'hardware': [h.strip() for h in request.form.get('hardware').split(',')],
            'technologies': [t.strip() for t in request.form.get('technologies').split(',')],
            'features': [f.strip() for f in request.form.get('features').split('\n') if f.strip()],
            'github': request.form.get('github') or None,
            'image': request.form.get('image')
        }
        
        add_item_to_file('RASPBERRY_PI_PROJECTS', project, format_rpi_project)
        flash('Raspberry Pi project added successfully!', 'success')
        return redirect(url_for('admin.raspberry_pi'))
    
    return render_template('admin/rpi_form.html', project=None)

@admin_bp.route('/raspberry-pi/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_rpi_project(project_id):
    from app import RASPBERRY_PI_PROJECTS
    project = next((p for p in RASPBERRY_PI_PROJECTS if p['id'] == project_id), None)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('admin.raspberry_pi'))
    
    if request.method == 'POST':
        updated_project = {
            'id': int(request.form.get('id')),
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'hardware': [h.strip() for h in request.form.get('hardware').split(',')],
            'technologies': [t.strip() for t in request.form.get('technologies').split(',')],
            'features': [f.strip() for f in request.form.get('features').split('\n') if f.strip()],
            'github': request.form.get('github') or None,
            'image': request.form.get('image')
        }
        
        update_item_in_file('RASPBERRY_PI_PROJECTS', project_id, updated_project, format_rpi_project)
        flash('Raspberry Pi project updated successfully!', 'success')
        return redirect(url_for('admin.raspberry_pi'))
    
    return render_template('admin/rpi_form.html', project=project)

@admin_bp.route('/raspberry-pi/delete/<int:project_id>')
@login_required
def delete_rpi_project(project_id):
    delete_item_from_file('RASPBERRY_PI_PROJECTS', project_id)
    flash('Raspberry Pi project deleted successfully!', 'success')
    return redirect(url_for('admin.raspberry_pi'))

# ============ IMAGE UPLOAD ============

@admin_bp.route('/upload-image', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['image']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(datetime.now().timestamp())}{ext}"
            
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            image_path = f"/static/images/{filename}"
            flash(f'Image uploaded successfully! Path: {image_path}', 'success')
            return render_template('admin/upload_image.html', uploaded_path=image_path)
        else:
            flash('Invalid file type. Allowed: png, jpg, jpeg, gif, webp', 'error')
    
    return render_template('admin/upload_image.html')

import json

@admin_bp.route('/contact-info', methods=['GET', 'POST'])
@login_required
def contact_info():
    contact = Contact.query.first()
    if not contact:
        contact = Contact() # Should be init in app.py but fallback here
        db.session.add(contact)
        db.session.commit()
    
    if request.method == 'POST':
        contact.email = request.form.get('email')
        contact.github = request.form.get('github')
        contact.linkedin = request.form.get('linkedin')
        contact.twitter = request.form.get('twitter')
        contact.location = request.form.get('location')
        
        db.session.commit()
            
        flash('Contact information updated successfully!', 'success')
        return redirect(url_for('admin.contact_info'))
        
    # Template expects a dict 'info'. We can pass the object directly as 'info'
    return render_template('admin/contact_info.html', info=contact)

@admin_bp.route('/about-info', methods=['GET', 'POST'])
@login_required
def about_info():
    about = About.query.first()
    if not about:
        about = About()
        db.session.add(about)
        db.session.commit()
    
    if request.method == 'POST':
        # Safely validate integer inputs
        try:
            p_count = int(request.form.get('stat_projects', 0))
        except:
            p_count = 0
            
        try:
            y_count = int(request.form.get('stat_years', 0))
        except:
            y_count = 0
            
        about.intro = request.form.get('intro')
        about.summary = request.form.get('summary')
        about.journey = request.form.get('journey')
        about.interests = request.form.get('interests')
        about.profile_image = request.form.get('profile_image')
        about.projects_completed = p_count
        about.years_experience = y_count
        about.skills_json = request.form.get('skills_json') # Stored as raw JSON string from form
        about.experience_json = request.form.get('experience_json') # Stored as raw JSON string from form
        
        db.session.commit()
            
        flash('About Me information updated successfully!', 'success')
        return redirect(url_for('admin.about_info'))
        
    return render_template('admin/about_info.html', info=about)

# ============ HELPER FUNCTIONS ============

def format_project(project):
    """Format project dictionary as Python code string"""
    github = f"'{project['github']}'" if project['github'] else 'None'
    demo = f"'{project['demo']}'" if project['demo'] else 'None'
    
    return f"""    {{
        'id': {project['id']},
        'title': '{project['title'].replace("'", "\\'")}',
        'description': '{project['description'].replace("'", "\\'")}',
        'technologies': {project['technologies']},
        'category': '{project['category']}',
        'github': {github},
        'demo': {demo},
        'image': '{project['image']}',
        'featured': {project['featured']}
    }}"""

def format_product(product):
    """Format product dictionary as Python code string"""
    purchase = f"'{product['purchase_link']}'" if product.get('purchase_link') else 'None'
    demo = f"'{product['demo_link']}'" if product.get('demo_link') else 'None'
    
    return f"""    {{
        'id': {product['id']},
        'name': '{product['name'].replace("'", "\\'")}',
        'description': '{product['description'].replace("'", "\\'")}',
        'price': {product['price']},
        'type': '{product['type']}',
        'category': '{product['category']}',
        'features': {product['features']},
        'technologies': {product['technologies']},
        'purchase_link': {purchase},
        'demo_link': {demo},
        'image': '{product['image']}'
    }}"""

def format_rpi_project(project):
    """Format Raspberry Pi project dictionary as Python code string"""
    github = f"'{project['github']}'" if project['github'] else 'None'
    
    return f"""    {{
        'id': {project['id']},
        'title': '{project['title'].replace("'", "\\'")}',
        'description': '{project['description'].replace("'", "\\'")}',
        'hardware': {project['hardware']},
        'technologies': {project['technologies']},
        'features': {project['features']},
        'github': {github},
        'image': '{project['image']}'
    }}"""

def add_item_to_file(list_name, item, formatter):
    """Add an item to a list in app.py"""
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the list
    pattern = rf'({list_name} = \[)(.*?)(\n\])'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        flash(f'Could not find {list_name} in app.py', 'error')
        return
    
    # Format item
    item_str = formatter(item)
    
    # Add comma if list is not empty
    existing_content = match.group(2).strip()
    if existing_content:
        item_str = ',' + item_str
    
    # Insert before closing bracket
    new_content = content[:match.end(2)] + item_str + content[match.end(2):]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

def update_item_in_file(list_name, item_id, updated_item, formatter):
    """Update an item in a list in app.py"""
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the list
    pattern = rf'{list_name} = \[(.*?)\n\]'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        flash(f'Could not find {list_name} in app.py', 'error')
        return
    
    list_content = match.group(1)
    
    # Find and replace the specific item
    item_pattern = rf"(\{{\s*'id':\s*{item_id}.*?\}})"
    item_match = re.search(item_pattern, list_content, re.DOTALL)
    
    if not item_match:
        flash(f'Could not find item with id {item_id}', 'error')
        return
    
    # Format new item
    new_item_str = formatter(updated_item)
    
    # Replace the item
    new_list_content = list_content[:item_match.start()] + new_item_str + list_content[item_match.end():]
    new_content = content[:match.start(1)] + new_list_content + content[match.end(1):]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)

def delete_item_from_file(list_name, item_id):
    """Delete an item from a list in app.py"""
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the list
    pattern = rf'{list_name} = \[(.*?)\n\]'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        flash(f'Could not find {list_name} in app.py', 'error')
        return
    
    list_content = match.group(1)
    
    # Find and remove the specific item (including preceding comma if exists)
    item_pattern = rf",?\s*\{{\s*'id':\s*{item_id}.*?\}}"
    new_list_content = re.sub(item_pattern, '', list_content, count=1, flags=re.DOTALL)
    
    # Clean up any double commas
    new_list_content = re.sub(r',\s*,', ',', new_list_content)
    # Clean up leading comma
    new_list_content = re.sub(r'^\s*,', '', new_list_content)
    
    new_content = content[:match.start(1)] + new_list_content + content[match.end(1):]
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
