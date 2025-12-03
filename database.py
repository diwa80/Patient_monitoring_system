"""
Database helper module for Patient Monitoring System
"""

import sqlite3
import os
from pathlib import Path

DATABASE = 'patient_monitoring.db'

def get_db():
    """
    Get database connection with row factory set to Row
    Returns sqlite3 connection object
    """
    db_path = Path(DATABASE)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initialize database by running schema.sql
    Creates database file if it doesn't exist
    """
    db_path = Path(DATABASE)
    
    # Read and execute schema
    schema_path = Path(__file__).parent / 'schema.sql'
    if schema_path.exists():
        conn = get_db()
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            conn.executescript(schema_sql)
        # Ensure any new columns from updated schema are present (simple migrations)
        try:
            cur = conn.execute("PRAGMA table_info('users')").fetchall()
            cols = [r['name'] for r in cur]
            if 'menu_permissions' not in cols:
                conn.execute("ALTER TABLE users ADD COLUMN menu_permissions TEXT")
                conn.commit()
        except Exception:
            # if anything goes wrong with migration, continue without failing init
            pass
        conn.commit()
        conn.close()
        print(f"Database initialized: {db_path}")
    else:
        print(f"Warning: schema.sql not found at {schema_path}")

