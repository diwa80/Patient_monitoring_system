"""
Migration script to add audit_logs table to existing database
Run this once to enable audit logging feature
"""

import sqlite3
from pathlib import Path

DATABASE = 'patient_monitoring.db'

def create_audit_logs_table():
    """Create audit_logs table and indexes"""
    db_path = Path(DATABASE)
    
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'")
    if cursor.fetchone():
        print("✓ audit_logs table already exists")
    else:
        print("Creating audit_logs table...")
        cursor.execute('''
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                details TEXT,
                ip_address TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("✓ Created audit_logs table")
    
    # Create indexes
    print("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, timestamp DESC)")
    conn.commit()
    print("✓ Created indexes")
    
    conn.close()
    
    print("\n✅ Audit logging feature enabled successfully!")
    print("\nFeatures available:")
    print("  - Track all user login/logout events")
    print("  - Monitor user creation, deletion, updates")
    print("  - Log alert resolutions")
    print("  - Track bed and settings changes")
    print("  - View audit logs from Admin panel")
    print("\n📍 Access logs at: /logs (Admin only)")

if __name__ == '__main__':
    create_audit_logs_table()
