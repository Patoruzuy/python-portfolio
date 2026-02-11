from werkzeug.security import generate_password_hash
import os
import re

# Default credentials we want to set
NEW_USER = "admin"
NEW_PASS = "admin123"

# Generate secure hash
new_hash = generate_password_hash(NEW_PASS)

print(f"Generating hash for password: '{NEW_PASS}'")

env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        content = f.read()
else:
    content = ""

# Update or Add ADMIN_USERNAME
if 'ADMIN_USERNAME=' in content:
    content = re.sub(r'ADMIN_USERNAME=.*', f'ADMIN_USERNAME={NEW_USER}', content)
else:
    content += f"\nADMIN_USERNAME={NEW_USER}"

# Update or Add ADMIN_PASSWORD_HASH
if 'ADMIN_PASSWORD_HASH=' in content:
    content = re.sub(r'ADMIN_PASSWORD_HASH=.*', f'ADMIN_PASSWORD_HASH={new_hash}', content)
else:
    content += f"\nADMIN_PASSWORD_HASH={new_hash}"

# Write back
with open(env_path, 'w') as f:
    f.write(content)

print(f"SUCCESS: .env updated.")
print(f"Username: {NEW_USER}")
print(f"Password: {NEW_PASS}")