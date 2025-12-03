"""
Script to create default admin user
Run this after initializing the database: python create_admin.py
"""

from database import init_db
import models

# Initialize database first
init_db()

# Create admin user
username = 'admin'
password = 'admin123'  # Change this in production!

user_id = models.create_user(username, password, 'admin')

if user_id:
    print(f"✓ Admin user '{username}' created successfully!")
    print(f"  Password: {password}")
    print("  Please change the password after first login.")
else:
    existing = models.get_user_by_username(username)
    if existing:
        print(f"⚠ User '{username}' already exists.")
    else:
        print(f"✗ Failed to create user '{username}'")
