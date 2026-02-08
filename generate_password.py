"""
Password Hash Generator for Admin Panel
Run this script to generate a secure password hash
"""

from werkzeug.security import generate_password_hash

print("=" * 50)
print("Admin Password Hash Generator")
print("=" * 50)
print()

password = input("Enter your desired password: ")
confirm = input("Confirm password: ")

if password != confirm:
    print("\n❌ Passwords don't match!")
    exit(1)

if len(password) < 8:
    print("\n⚠️  Warning: Password is less than 8 characters")
    proceed = input("Continue anyway? (y/n): ")
    if proceed.lower() != 'y':
        exit(1)

# Generate hash
password_hash = generate_password_hash(password)

print("\n" + "=" * 50)
print("✅ Password hash generated successfully!")
print("=" * 50)
print()
print("Add this to your .env file:")
print()
print(f"ADMIN_PASSWORD_HASH={password_hash}")
print()
print("Or update admin_routes.py line 18:")
print(f"ADMIN_PASSWORD_HASH = '{password_hash}'")
print()
print("=" * 50)
