"""
Quick test to verify admin panel setup
"""

print("Testing admin panel setup...\n")

# Test 1: Check if admin_routes.py exists
try:
    import app.admin_routes as admin_routes
    print("✅ admin_routes.py found")
except ImportError as e:
    print(f"❌ admin_routes.py not found: {e}")
    exit(1)

# Test 2: Check if werkzeug is available for password hashing
try:
    from werkzeug.security import generate_password_hash, check_password_hash
    print("✅ werkzeug security available")
except ImportError:
    print("❌ werkzeug not available - run: pip install werkzeug")
    exit(1)

# Test 3: Test password hashing
try:
    test_password = "password"
    test_hash = generate_password_hash(test_password)
    if check_password_hash(test_hash, test_password):
        print("✅ Password hashing works correctly")
    else:
        print("❌ Password hashing test failed")
except Exception as e:
    print(f"❌ Password hashing error: {e}")

# Test 4: Check SECRET_KEY
try:
    from app import app
    if app.config.get('SECRET_KEY'):
        print("✅ SECRET_KEY configured")
    else:
        print("⚠️  SECRET_KEY not set")
except Exception as e:
    print(f"❌ Error checking SECRET_KEY: {e}")

# Test 5: Check if admin blueprint is registered
try:
    from app import app
    blueprints = [bp.name for bp in app.blueprints.values()]
    if 'admin' in blueprints:
        print("✅ Admin blueprint registered")
    else:
        print("❌ Admin blueprint not registered")
except Exception as e:
    print(f"❌ Error checking blueprint: {e}")

# Test 6: Check template files
import os
template_files = [
    'templates/admin/login.html',
    'templates/admin/dashboard.html',
    'templates/admin/projects.html',
    'templates/admin/blog.html'
]
missing_templates = []
for template in template_files:
    if not os.path.exists(template):
        missing_templates.append(template)

if not missing_templates:
    print("✅ All admin templates found")
else:
    print(f"⚠️  Missing templates: {', '.join(missing_templates)}")

print("\n" + "="*50)
print("Setup verification complete!")
print("="*50)
print("\nTo start using the admin panel:")
print("1. Run: python app.py")
print("2. Visit: http://localhost:5000/admin")
print("3. Login: admin / password")
print("\nTo set custom password:")
print("Run: python scripts/generate_password.py")
