"""
Data models and helper functions for Patient Monitoring System
"""

import sqlite3
from database import get_db
import json
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# ==================== USER MANAGEMENT ====================

def create_user(username, password, role='nurse', menu_permissions=None):
    """Create a new user with hashed password and optional menu permissions

    `menu_permissions` should be a list of permission keys; stored as JSON string.
    """
    db = get_db()
    try:
        password_hash = generate_password_hash(password)
        perms_json = json.dumps(menu_permissions) if menu_permissions else None
        cursor = db.execute(
            'INSERT INTO users (username, password_hash, role, menu_permissions) VALUES (?, ?, ?, ?)',
            (username, password_hash, role, perms_json)
        )
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        db.close()

def get_user_by_username(username):
    """Get user by username"""
    db = get_db()
    try:
        user = db.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        return dict(user) if user else None
    finally:
        db.close()

def verify_password(user, password):
    """Verify password against stored hash"""
    return check_password_hash(user['password_hash'], password)

def record_failed_login(username):
    """Record a failed login attempt and lock account if threshold exceeded"""
    db = get_db()
    try:
        user = db.execute('SELECT id, failed_login_attempts FROM users WHERE username = ?', (username,)).fetchone()
        if user:
            failed_attempts = user['failed_login_attempts'] + 1
            if failed_attempts >= 5:
                # Lock the account
                db.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?, locked_at = CURRENT_TIMESTAMP, last_login_attempt = CURRENT_TIMESTAMP
                    WHERE username = ?
                ''', (failed_attempts, username))
            else:
                db.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?, last_login_attempt = CURRENT_TIMESTAMP
                    WHERE username = ?
                ''', (failed_attempts, username))
            db.commit()
            return failed_attempts
        return 0
    finally:
        db.close()

def reset_failed_login(username):
    """Reset failed login attempts on successful login"""
    db = get_db()
    try:
        db.execute('''
            UPDATE users 
            SET failed_login_attempts = 0, last_login_attempt = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))
        db.commit()
    finally:
        db.close()

def unlock_user_account(user_id):
    """Unlock a locked user account (admin function)"""
    db = get_db()
    try:
        db.execute('''
            UPDATE users 
            SET failed_login_attempts = 0, locked_at = NULL
            WHERE id = ?
        ''', (user_id,))
        db.commit()
        return True
    finally:
        db.close()

def is_account_locked(user):
    """Check if account is locked"""
    if user.get('locked_at'):
        return True
    return False

def list_all_users():
    """Get all users"""
    db = get_db()
    try:
        users = db.execute('SELECT * FROM users ORDER BY username').fetchall()
        return [dict(u) for u in users]
    finally:
        db.close()

def toggle_user_status(user_id):
    """Toggle user status between active and disabled"""
    db = get_db()
    try:
        user = db.execute('SELECT status FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            new_status = 'disabled' if user['status'] == 'active' else 'active'
            db.execute('UPDATE users SET status = ? WHERE id = ?', (new_status, user_id))
            db.commit()
            return True
        return False
    finally:
        db.close()

def update_user_password(user_id, new_password):
    """Update user password"""
    db = get_db()
    try:
        password_hash = generate_password_hash(new_password)
        db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        db.commit()
        return True
    finally:
        db.close()

def update_user(user_id, username, role, menu_permissions=None):
    """Update user basic fields and menu permissions. Returns True on success, False if username conflict."""
    db = get_db()
    try:
        perms_json = json.dumps(menu_permissions) if menu_permissions else None
        db.execute('UPDATE users SET username = ?, role = ?, menu_permissions = ? WHERE id = ?',
                   (username, role, perms_json, user_id))
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        db.close()

def delete_user(user_id):
    """Delete a user and related nurse assignments."""
    db = get_db()
    try:
        db.execute('DELETE FROM nurse_assignments WHERE nurse_id = ?', (user_id,))
        db.execute('DELETE FROM users WHERE id = ?', (user_id,))
        db.commit()
        return True
    finally:
        db.close()

# ==================== BED MANAGEMENT ====================

def list_beds():
    """Get all beds"""
    db = get_db()
    try:
        beds = db.execute('SELECT * FROM beds ORDER BY bed_name').fetchall()
        return [dict(b) for b in beds]
    finally:
        db.close()

def get_bed(bed_id):
    """Get bed by ID"""
    db = get_db()
    try:
        bed = db.execute('SELECT * FROM beds WHERE id = ?', (bed_id,)).fetchone()
        return dict(bed) if bed else None
    finally:
        db.close()

def create_bed(bed_name, room_no=None):
    """Create a new bed"""
    db = get_db()
    try:
        cursor = db.execute(
            'INSERT INTO beds (bed_name, room_no) VALUES (?, ?)',
            (bed_name, room_no)
        )
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()

# ==================== NURSE ASSIGNMENTS ====================

def assign_nurse_to_bed(nurse_id, bed_id):
    """Assign a nurse to a bed"""
    db = get_db()
    try:
        db.execute(
            'INSERT OR IGNORE INTO nurse_assignments (nurse_id, bed_id) VALUES (?, ?)',
            (nurse_id, bed_id)
        )
        db.commit()
        return True
    except:
        return False
    finally:
        db.close()

def unassign_nurse_from_bed(nurse_id, bed_id):
    """Unassign a nurse from a bed"""
    db = get_db()
    try:
        db.execute(
            'DELETE FROM nurse_assignments WHERE nurse_id = ? AND bed_id = ?',
            (nurse_id, bed_id)
        )
        db.commit()
        return True
    finally:
        db.close()

def get_nurse_beds(nurse_id):
    """Get all beds assigned to a nurse"""
    db = get_db()
    try:
        beds = db.execute('''
            SELECT b.* FROM beds b
            INNER JOIN nurse_assignments na ON b.id = na.bed_id
            WHERE na.nurse_id = ?
            ORDER BY b.bed_name
        ''', (nurse_id,)).fetchall()
        return [dict(b) for b in beds]
    finally:
        db.close()

# ==================== READINGS ====================

def insert_reading(bed_id, temperature=None, humidity=None, motion=None, distance_cm=None):
    """Insert a new sensor reading"""
    db = get_db()
    try:
        cursor = db.execute('''
            INSERT INTO readings (bed_id, temperature, humidity, motion, distance_cm)
            VALUES (?, ?, ?, ?, ?)
        ''', (bed_id, temperature, humidity, motion, distance_cm))
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()

def get_latest_readings_per_bed():
    """Get latest reading for each bed with alert status"""
    db = get_db()
    try:
        readings = db.execute('''
            SELECT r.*, b.bed_name, b.room_no,
                   (SELECT COUNT(*) FROM alerts a 
                    WHERE a.bed_id = r.bed_id AND a.status = 'new') as active_alert_count,
                   (SELECT alert_type FROM alerts a 
                    WHERE a.bed_id = r.bed_id AND a.status = 'new' 
                    ORDER BY a.created_at DESC LIMIT 1) as latest_alert_type
            FROM readings r
            INNER JOIN beds b ON r.bed_id = b.id
            WHERE r.id IN (
                SELECT MAX(id) FROM readings GROUP BY bed_id
            )
            ORDER BY b.bed_name
        ''').fetchall()
        return [dict(r) for r in readings]
    finally:
        db.close()

def get_readings_for_bed(bed_id, hours=24, limit=1000):
    """Get readings for a specific bed within time range"""
    db = get_db()
    try:
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime('%Y-%m-%d %H:%M:%S')  # match DB timestamp format
        readings = db.execute('''
            SELECT * FROM readings
            WHERE bed_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (bed_id, cutoff_str, limit)).fetchall()
        return [dict(r) for r in readings]
    finally:
        db.close()

# ==================== ALERTS ====================

def create_alert(bed_id, alert_type, message):
    """Create a new alert"""
    db = get_db()
    try:
        cursor = db.execute('''
            INSERT INTO alerts (bed_id, alert_type, message, status)
            VALUES (?, ?, ?, 'new')
        ''', (bed_id, alert_type, message))
        db.commit()
        return cursor.lastrowid
    finally:
        db.close()

def get_all_alerts(status=None, nurse_id=None, limit=100):
    """Get all alerts, optionally filtered by status and nurse"""
    db = get_db()
    try:
        query = '''
            SELECT a.*, b.bed_name, b.room_no
            FROM alerts a
            INNER JOIN beds b ON a.bed_id = b.id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND a.status = ?'
            params.append(status)
        
        if nurse_id:
            query += ' AND EXISTS (SELECT 1 FROM nurse_assignments na WHERE na.bed_id = a.bed_id AND na.nurse_id = ?)'
            params.append(nurse_id)
        
        query += ' ORDER BY a.created_at DESC LIMIT ?'
        params.append(limit)
        
        alerts = db.execute(query, params).fetchall()
        return [dict(a) for a in alerts]
    finally:
        db.close()

def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    db = get_db()
    try:
        db.execute('''
            UPDATE alerts 
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (alert_id,))
        db.commit()
        return True
    finally:
        db.close()

# ==================== DEVICES ====================

def update_device_status(esp_id, ip=None):
    """Update device last_seen timestamp and IP"""
    db = get_db()
    try:
        # Check if device exists
        device = db.execute('SELECT * FROM devices WHERE esp_id = ?', (esp_id,)).fetchone()
        
        if device:
            db.execute('''
                UPDATE devices 
                SET last_seen = CURRENT_TIMESTAMP, ip = ?, status = 'online'
                WHERE esp_id = ?
            ''', (ip, esp_id))
        else:
            db.execute('''
                INSERT INTO devices (esp_id, ip, last_seen, status)
                VALUES (?, ?, CURRENT_TIMESTAMP, 'online')
            ''', (esp_id, ip))
        
        db.commit()
        
        # Update offline devices (not seen in last 5 minutes)
        cutoff = datetime.now() - timedelta(minutes=5)
        db.execute('''
            UPDATE devices 
            SET status = 'offline'
            WHERE last_seen < ?
        ''', (cutoff.isoformat(),))
        db.commit()
        
        return True
    finally:
        db.close()

# ==================== SETTINGS ====================

def set_setting(key, value):
    """Set a setting value"""
    db = get_db()
    try:
        db.execute('''
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        ''', (key, str(value)))
        db.commit()
        return True
    finally:
        db.close()

def get_all_settings():
    """Get all settings as a dictionary"""
    db = get_db()
    try:
        settings = db.execute('SELECT key, value FROM settings').fetchall()
        result = {}
        for s in settings:
            # Time-based settings remain as strings
            if 'time' in s['key']:
                result[s['key']] = s['value']
            else:
                # Numeric settings converted to float
                try:
                    result[s['key']] = float(s['value'])
                except ValueError:
                    result[s['key']] = s['value']
        return result
    finally:
        db.close()

# ==================== STATISTICS ====================

def get_stats_overview(nurse_id=None):
    """Get overview statistics for dashboard.

    If `nurse_id` is provided, statistics are restricted to beds assigned to that nurse.
    """
    db = get_db()
    try:
        stats = {}

        # Monitored beds (total beds or beds assigned to nurse)
        if nurse_id:
            stats['monitored_beds'] = db.execute(
                'SELECT COUNT(*) as count FROM nurse_assignments WHERE nurse_id = ?', (nurse_id,)
            ).fetchone()['count']
        else:
            stats['monitored_beds'] = db.execute('SELECT COUNT(*) as count FROM beds').fetchone()['count']

        # Active movements: count distinct beds with motion detected in the last 5 minutes
        try:
            if nurse_id:
                active_movements = db.execute("""
                    SELECT COUNT(DISTINCT r.bed_id) as cnt FROM readings r
                    WHERE r.motion = 1 AND r.timestamp >= datetime('now', '-5 minutes')
                    AND EXISTS (SELECT 1 FROM nurse_assignments na WHERE na.bed_id = r.bed_id AND na.nurse_id = ?)
                """, (nurse_id,)).fetchone()['cnt']
            else:
                active_movements = db.execute("""
                    SELECT COUNT(DISTINCT bed_id) as cnt FROM readings
                    WHERE motion = 1 AND timestamp >= datetime('now', '-5 minutes')
                """).fetchone()['cnt']
        except Exception:
            active_movements = 0
        stats['active_movements'] = active_movements or 0

        # Fall risk: count of new alerts of types indicating fall/exit in the last 24 hours
        try:
            if nurse_id:
                fall_risk = db.execute("""
                    SELECT COUNT(*) as cnt FROM alerts a
                    WHERE a.status = 'new' AND (a.alert_type LIKE '%fall%' OR a.alert_type LIKE '%exit%')
                    AND a.created_at >= datetime('now', '-24 hours')
                    AND EXISTS (SELECT 1 FROM nurse_assignments na WHERE na.bed_id = a.bed_id AND na.nurse_id = ?)
                """, (nurse_id,)).fetchone()['cnt']
            else:
                fall_risk = db.execute("""
                    SELECT COUNT(*) as cnt FROM alerts
                    WHERE status = 'new' AND (alert_type LIKE '%fall%' OR alert_type LIKE '%exit%')
                    AND created_at >= datetime('now', '-24 hours')
                """).fetchone()['cnt']
        except Exception:
            fall_risk = 0
        stats['fall_risk'] = fall_risk or 0

        # Average room temperature: average of readings in last 24 hours (optionally limited to nurse beds)
        try:
            if nurse_id:
                avg_temp = db.execute("""
                    SELECT ROUND(AVG(r.temperature), 1) as avg_temp FROM readings r
                    WHERE r.temperature IS NOT NULL AND r.timestamp >= datetime('now', '-24 hours')
                    AND EXISTS (SELECT 1 FROM nurse_assignments na WHERE na.bed_id = r.bed_id AND na.nurse_id = ?)
                """, (nurse_id,)).fetchone()['avg_temp']
            else:
                avg_temp = db.execute("""
                    SELECT ROUND(AVG(temperature), 1) as avg_temp FROM readings
                    WHERE temperature IS NOT NULL AND timestamp >= datetime('now', '-24 hours')
                """).fetchone()['avg_temp']

            stats['avg_temperature'] = float(avg_temp) if avg_temp is not None else None
        except Exception:
            stats['avg_temperature'] = None

        return stats
    finally:
        db.close()


# ==================== AUDIT LOGGING ====================

def log_event(user_id, username, action, target_type=None, target_id=None, details=None, ip_address=None):
    """Log an audit event"""
    db = get_db()
    try:
        db.execute('''
            INSERT INTO audit_logs (user_id, username, action, target_type, target_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, action, target_type, target_id, details, ip_address))
        db.commit()
    finally:
        db.close()

def get_audit_logs(limit=100, user_id=None, action_filter=None):
    """Get audit logs with optional filters"""
    db = get_db()
    try:
        query = 'SELECT * FROM audit_logs WHERE 1=1'
        params = []
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if action_filter:
            query += ' AND action LIKE ?'
            params.append(f'%{action_filter}%')
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        logs = db.execute(query, params).fetchall()
        return [dict(log) for log in logs]
    finally:
        db.close()

