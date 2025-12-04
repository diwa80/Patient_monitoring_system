#!/usr/bin/env python3
"""
Create a test nurse user and assign to a single bed (Bed ID 1).
Run: python tools\create_test_nurse.py
"""
import os, sys
# Ensure project root is on sys.path so imports work when running from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import init_db
import models

init_db()

username = 'testnurse'
password = 'nurse123'

existing = models.get_user_by_username(username)
if existing:
    print(f"User '{username}' already exists (id={existing['id']}).")
    user_id = existing['id']
else:
    user_id = models.create_user(username, password, role='nurse')
    if user_id:
        print(f"Created nurse user '{username}' with password '{password}' (id={user_id}).")
    else:
        print('Failed to create user')
        raise SystemExit(1)

# Assign to bed 1 (will ignore if already assigned)
bed_id = 1
ok = models.assign_nurse_to_bed(user_id, bed_id)
if ok:
    print(f"Assigned nurse {username} (id={user_id}) to bed {bed_id}.")
else:
    print(f"Failed to assign nurse {username} to bed {bed_id}.")

print('\nDone.')
