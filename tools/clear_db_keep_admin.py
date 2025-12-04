#!/usr/bin/env python3
"""
Backup the SQLite DB and clear all data except admin users and settings.
Use with caution. This script makes a timestamped backup first.
"""
import os, shutil, sqlite3, time, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(ROOT, 'patient_monitoring.db')

if not os.path.exists(DB):
    print('Database file not found at', DB)
    sys.exit(1)

# Create backup
ts = time.strftime('%Y%m%d_%H%M%S')
backup = DB + f'.bak.{ts}'
shutil.copy2(DB, backup)
print('Backup created:', backup)

# Connect and delete rows (preserve users with role='admin' and keep settings)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

try:
    # Turn off foreign keys while truncating to avoid constraints, then re-enable
    cur.execute('PRAGMA foreign_keys = OFF;')
    conn.commit()

    # Show counts before
    def count(table):
        try:
            r = cur.execute(f'SELECT COUNT(*) as c FROM {table}').fetchone()[0]
        except Exception:
            r = None
        return r

    tables = ['readings','alerts','devices','nurse_assignments','beds','users']
    print('Row counts before:')
    for t in tables:
        print(f'  {t}:', count(t))

    # Delete data
    cur.executescript(r"""
        DELETE FROM readings;
        DELETE FROM alerts;
        DELETE FROM devices;
        DELETE FROM nurse_assignments;
        DELETE FROM beds;
        -- keep admin users only
        DELETE FROM users WHERE role != 'admin';
    """)

    conn.commit()

    # Re-enable foreign keys
    cur.execute('PRAGMA foreign_keys = ON;')
    conn.commit()

    # VACUUM to reclaim space
    print('Running VACUUM...')
    cur.execute('VACUUM;')
    conn.commit()

    # Show counts after
    print('\nRow counts after:')
    for t in tables:
        print(f'  {t}:', count(t))

    print('\nDone. Backup is at:', backup)
    print('All non-admin data cleared (settings preserved).')

except Exception as e:
    print('Error during cleanup:', e)
    print('Restoring backup')
    conn.close()
    shutil.copy2(backup, DB)
    print('Restored from', backup)
    sys.exit(1)
finally:
    conn.close()
