"""
Migration script to add security columns to existing database
Run this once to update existing database with new security features
"""

import sqlite3
from pathlib import Path

DATABASE = 'patient_monitoring.db'

def update_schema():
    """Add security columns to users table"""
    db_path = Path(DATABASE)
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info('users')")
    cols = [row[1] for row in cursor.fetchall()]
    
    print(f"Current columns: {cols}")
    
    # Add new columns if they don't exist
    if 'failed_login_attempts' not in cols:
        print("Adding failed_login_attempts column...")
        cursor.execute("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
        conn.commit()
        print("✓ Added failed_login_attempts")
    
    if 'locked_at' not in cols:
        print("Adding locked_at column...")
        cursor.execute("ALTER TABLE users ADD COLUMN locked_at DATETIME")
        conn.commit()
        print("✓ Added locked_at")
    
    if 'last_login_attempt' not in cols:
        print("Adding last_login_attempt column...")
        cursor.execute("ALTER TABLE users ADD COLUMN last_login_attempt DATETIME")
        conn.commit()
        print("✓ Added last_login_attempt")
    
    conn.close()
    print("\n✓ Database schema updated successfully!")
    print("\nSecurity features enabled:")
    print("  - Login rate limiting (5 attempts)")
    print("  - Account lockout on failed attempts")
    print("  - Session timeout (30 minutes)")
    print("  - Admin can unlock accounts from User Management")

if __name__ == '__main__':
    update_schema()
