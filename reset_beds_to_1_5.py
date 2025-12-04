#!/usr/bin/env python3
"""
Reset beds table so next inserted beds start at ID 1..5 by deleting current rows
and resetting sqlite_sequence for 'beds'. Then run setup_demo_beds.py to recreate beds 1-5.
"""
import os, sys, sqlite3
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(ROOT, 'patient_monitoring.db')
# Ensure project imports work
sys.path.insert(0, ROOT)

import setup_demo_beds

if not os.path.exists(DB):
    print('Database not found at', DB)
    sys.exit(1)

print('Connecting to DB:', DB)
conn = sqlite3.connect(DB)
cur = conn.cursor()
try:
    # Delete all beds
    cur.execute('DELETE FROM beds;')
    # Reset sqlite_sequence for beds so AUTOINCREMENT starts at 0 (next insert -> 1)
    cur.execute("DELETE FROM sqlite_sequence WHERE name='beds';")
    conn.commit()
    print('Cleared beds and reset sqlite_sequence for beds.')

    # Re-run setup demo
    print('Running setup_demo_beds to recreate Bed 1..5')
    setup_demo_beds.setup_demo_beds()

    # Show current beds
    cur.execute('SELECT id, bed_name, room_no FROM beds ORDER BY id')
    rows = cur.fetchall()
    print('\nCurrent beds:')
    for r in rows:
        print('  ID', r[0], r[1], r[2])

finally:
    conn.close()
