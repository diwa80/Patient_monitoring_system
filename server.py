"""
Flask server for Patient Room Environmental & Activity Monitoring System
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import json
import sqlite3

from database import init_db, get_db
import models
import behavior_detection
import logging

app = Flask(__name__)
app.secret_key = 'patient-monitoring-secret-key-change-in-production-2024'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize database on startup
with app.app_context():
    init_db()

# ==================== DECORATORS ====================

def login_required(f):
    """Require user to be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Require user to be admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def nurse_required(f):
    """Require user to be nurse"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'nurse':
            return jsonify({'error': 'Nurse access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def permission_required(menu_key):
    """Require that the current user either be admin or have the given menu permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            # admin always allowed
            if session.get('role') == 'admin':
                return f(*args, **kwargs)
            perms = session.get('menu_permissions') or []
            try:
                if menu_key in perms:
                    return f(*args, **kwargs)
            except Exception:
                pass
            return jsonify({'error': 'Permission required'}), 403
        return decorated_function
    return decorator

# ==================== AUTH ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
        
        user = models.get_user_by_username(username)
        
        if user and models.verify_password(user, password):
            if user['status'] != 'active':
                flash('Your account is disabled', 'error')
                return render_template('login.html')
            
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            # load menu permissions (stored as JSON string) into session as a list
            mp = user.get('menu_permissions')
            try:
                if isinstance(mp, str) and mp:
                    session['menu_permissions'] = json.loads(mp)
                elif isinstance(mp, list):
                    session['menu_permissions'] = mp
                else:
                    session['menu_permissions'] = []
            except Exception:
                session['menu_permissions'] = []
            
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

# ==================== DASHBOARD ROUTES ====================

@app.route('/')
@login_required
def dashboard():
    """Redirect to appropriate dashboard based on role"""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('nurse_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if session.get('role') != 'admin':
        flash('Admin access required', 'error')
        return redirect(url_for('nurse_dashboard'))
    return render_template('dashboard_admin.html')

@app.route('/nurse/dashboard')
@login_required
def nurse_dashboard():
    """Nurse dashboard"""
    return render_template('dashboard_nurse.html')

# ==================== PAGE ROUTES ====================

@app.route('/beds/<int:bed_id>')
@login_required
def bed_overview(bed_id):
    """Bed overview page"""
    bed = models.get_bed(bed_id)
    if not bed:
        flash('Bed not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Check nurse permissions
    if session.get('role') == 'nurse':
        nurse_beds = [b['id'] for b in models.get_nurse_beds(session['user_id'])]
        if bed_id not in nurse_beds:
            flash('You do not have access to this bed', 'error')
            return redirect(url_for('nurse_dashboard'))
    
    return render_template('bed_overview.html', bed=bed)

@app.route('/alerts')
@login_required
def alerts_page():
    """Alerts page"""
    return render_template('alerts.html')

@app.route('/users')
@login_required
@permission_required('users')
def user_management():
    """User management page (permission-based access)"""
    return render_template('user_management.html')

@app.route('/devices')
@login_required
@permission_required('devices')
def device_management():
    """Device management page (permission-based access)"""
    return render_template('device_management.html')

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('settings')
def settings_page():
    """Settings page (permission-based access)"""
    if request.method == 'POST':
        settings = {
            'temp_min': float(request.form.get('temp_min')),
            'temp_max': float(request.form.get('temp_max')),
            'humidity_min': float(request.form.get('humidity_min')),
            'humidity_max': float(request.form.get('humidity_max')),
            'distance_bed_exit_cm': float(request.form.get('distance_bed_exit_cm')),
            'no_motion_timeout_minutes': float(request.form.get('no_motion_timeout_minutes')),
            'fall_drop_threshold_cm': float(request.form.get('fall_drop_threshold_cm', 30.0)),
            'restlessness_motions_per_hour': float(request.form.get('restlessness_motions_per_hour', 20.0)),
            'fever_temp_threshold': float(request.form.get('fever_temp_threshold', 37.5)),
            'fever_temp_increase': float(request.form.get('fever_temp_increase', 1.5)),
            'low_humidity_danger': float(request.form.get('low_humidity_danger', 30.0)),
            'high_humidity_danger': float(request.form.get('high_humidity_danger', 70.0))
        }
        
        for key, value in settings.items():
            models.set_setting(key, value)
        
        flash('Settings updated successfully', 'success')
        return redirect(url_for('settings_page'))
    
    return render_template('settings.html')

# ==================== API ROUTES ====================

@app.route('/api/data', methods=['POST'])
def api_data():
    """Receive sensor data from ESP8266"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required = ['bed_id', 'temperature', 'humidity', 'motion', 'distance_cm', 'esp_id']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        bed_id = int(data['bed_id'])
        temperature = float(data.get('temperature', 0))
        humidity = float(data.get('humidity', 0))
        motion = int(data.get('motion', 0))
        distance_cm = float(data.get('distance_cm', 0))
        esp_id = data['esp_id']
        ip = request.remote_addr
        
        # Insert reading
        models.insert_reading(bed_id, temperature, humidity, motion, distance_cm)
        
        # Update device status
        models.update_device_status(esp_id, ip)
        
        # Check thresholds and create alerts
        settings = models.get_all_settings()
        
        # Basic threshold checks
        # Temperature check
        if temperature < settings.get('temp_min', 18.0) or temperature > settings.get('temp_max', 24.0):
            models.create_alert(
                bed_id,
                'temp_out_of_range',
                f'Temperature {temperature:.1f}°C is outside safe range ({settings.get("temp_min", 18.0)}-{settings.get("temp_max", 24.0)}°C)'
            )
        
        # Humidity check
        if humidity < settings.get('humidity_min', 40.0) or humidity > settings.get('humidity_max', 60.0):
            models.create_alert(
                bed_id,
                'humidity_out_of_range',
                f'Humidity {humidity:.1f}% is outside safe range ({settings.get("humidity_min", 40.0)}-{settings.get("humidity_max", 60.0)}%)'
            )
        
        # Advanced behavior detection
        detected_behaviors = behavior_detection.detect_abnormal_behaviors(
            bed_id, temperature, humidity, motion, distance_cm
        )
        
        # Create alerts for detected behaviors
        for alert_type, message, severity in detected_behaviors:
            # Log the detection
            behavior_detection.log_behavior_detection(bed_id, alert_type, message, severity)
            
            # Create alert in database
            models.create_alert(bed_id, alert_type, message)
            
            # Log to console
            logging.info(f"Behavior detected - Bed {bed_id}: {alert_type} - {message}")
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest_readings')
@login_required
def api_latest_readings():
    """Get latest readings for all beds (filtered by nurse if applicable)"""
    try:
        readings = models.get_latest_readings_per_bed()
        
        # Filter by nurse assignments if nurse
        if session.get('role') == 'nurse':
            nurse_beds = [b['id'] for b in models.get_nurse_beds(session['user_id'])]
            readings = [r for r in readings if r['bed_id'] in nurse_beds]
        
        return jsonify(readings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts')
@login_required
def api_alerts():
    """Get alerts (filtered by status and nurse if applicable)"""
    try:
        status = request.args.get('status')
        nurse_id = session['user_id'] if session.get('role') == 'nurse' else None
        
        alerts = models.get_all_alerts(status=status, nurse_id=nurse_id)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bed/<int:bed_id>/readings')
@login_required
def api_bed_readings(bed_id):
    """Get readings for a specific bed"""
    try:
        # Check nurse permissions
        if session.get('role') == 'nurse':
            nurse_beds = [b['id'] for b in models.get_nurse_beds(session['user_id'])]
            if bed_id not in nurse_beds:
                return jsonify({'error': 'Access denied'}), 403
        
        hours = int(request.args.get('hours', 24))
        readings = models.get_readings_for_bed(bed_id, hours=hours)
        return jsonify(readings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/overview')
@login_required
def api_stats_overview():
    """Get overview statistics"""
    try:
        stats = models.get_stats_overview()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/temperature')
@login_required
def api_chart_temperature():
    """Get average temperature data for the last 24 hours by bed"""
    try:
        db = get_db()
        # Get average temperature per bed for last 24 hours
        cursor = db.execute('''
            SELECT 
                b.id as bed_id, 
                b.bed_name,
                ROUND(AVG(r.temperature), 1) as avg_temp
            FROM readings r
            JOIN beds b ON r.bed_id = b.id
            WHERE r.timestamp >= datetime('now', '-24 hours')
            GROUP BY r.bed_id
            ORDER BY b.bed_name
        ''')
        rows = cursor.fetchall()
        db.close()
        
        if not rows:
            # Return sample data if no readings available
            return jsonify({
                'labels': ['Bed 1', 'Bed 2', 'Bed 3'],
                'temperatures': [36.5, 37.2, 36.8]
            })
        
        labels = [row['bed_name'] for row in rows]
        temperatures = [float(row['avg_temp']) if row['avg_temp'] else 0 for row in rows]
        
        return jsonify({'labels': labels, 'temperatures': temperatures})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/alerts')
@login_required
def api_chart_alerts():
    """Get alert counts by type for the last 24 hours"""
    try:
        db = get_db()
        # Count alerts by type for last 24 hours
        cursor = db.execute('''
            SELECT 
                alert_type,
                COUNT(*) as count
            FROM alerts
            WHERE created_at >= datetime('now', '-24 hours')
            GROUP BY alert_type
            ORDER BY count DESC
        ''')
        rows = cursor.fetchall()
        db.close()
        
        if not rows:
            # Return sample data if no alerts available
            return jsonify({
                'labels': ['Fever Warning', 'Bed Exit', 'Motion Alert'],
                'counts': [5, 3, 2]
            })
        
        labels = [row['alert_type'] for row in rows]
        counts = [row['count'] for row in rows]
        
        return jsonify({'labels': labels, 'counts': counts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def api_resolve_alert(alert_id):
    """Resolve an alert"""
    try:
        # Check nurse permissions
        if session.get('role') == 'nurse':
            alert = models.get_all_alerts(nurse_id=session['user_id'])
            alert_ids = [a['id'] for a in alert]
            if alert_id not in alert_ids:
                return jsonify({'error': 'Access denied'}), 403
        
        models.resolve_alert(alert_id)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/clear/all', methods=['POST'])
@login_required
@permission_required('users')
def api_clear_all_alerts():
    """Clear all new alerts (mark as resolved)"""
    try:
        db = get_db()
        db.execute('''
            UPDATE alerts 
            SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
            WHERE status = 'new'
        ''')
        db.commit()
        db.close()
        return jsonify({'status': 'ok', 'message': 'All alerts cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== USER MANAGEMENT API ====================

@app.route('/users/create', methods=['POST'])
@login_required
@admin_required
def api_create_user():
    """Create a new user"""
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'nurse')
        # optional: beds[] and menu_permissions[]
        beds = request.form.getlist('beds[]') or request.form.getlist('beds')
        menu_permissions = request.form.getlist('menu_permissions[]') or request.form.getlist('menu_permissions')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        user_id = models.create_user(username, password, role, menu_permissions=menu_permissions if menu_permissions else None)
        if user_id:
            # assign selected beds (if any) to the user (only meaningful for nurses)
            if beds and role == 'nurse':
                for b in beds:
                    try:
                        bid = int(b)
                        models.assign_nurse_to_bed(user_id, bid)
                    except:
                        continue

            return jsonify({'status': 'ok', 'user_id': user_id})
        else:
            return jsonify({'error': 'Username already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def api_toggle_user(user_id):
    """Toggle user status"""
    try:
        if models.toggle_user_status(user_id):
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def api_reset_password(user_id):
    """Reset user password"""
    try:
        new_password = request.form.get('password')
        if not new_password:
            return jsonify({'error': 'Password required'}), 400
        
        if models.update_user_password(user_id, new_password):
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'error': 'Failed to update password'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def api_update_user(user_id):
    """Update user fields (username, role, menu_permissions)"""
    try:
        username = request.form.get('username')
        role = request.form.get('role')
        menu_permissions = request.form.getlist('menu_permissions[]') or request.form.getlist('menu_permissions')

        if not username or not role:
            return jsonify({'error': 'Username and role required'}), 400

        ok = models.update_user(user_id, username, role, menu_permissions=menu_permissions if menu_permissions else None)
        if ok:
            return jsonify({'status': 'ok'})
        else:
            return jsonify({'error': 'Username already exists or update failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>/change-password', methods=['POST'])
@login_required
@admin_required
def api_change_user_password(user_id):
    """Change user password"""
    try:
        new_password = request.form.get('new_password')
        
        if not new_password or len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Update password in database
        db = get_db()
        from werkzeug.security import generate_password_hash
        hashed = generate_password_hash(new_password)
        db.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user_id))
        db.commit()
        db.close()
        
        return jsonify({'status': 'ok', 'message': 'Password changed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def api_delete_user(user_id):
    """Delete a user and related assignments"""
    try:
        models.delete_user(user_id)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/assignments', methods=['POST'])
@login_required
@admin_required
def api_assignments():
    """Assign or unassign nurse to bed"""
    try:
        nurse_id = int(request.form.get('nurse_id'))
        bed_id = int(request.form.get('bed_id'))
        action = request.form.get('action', 'assign')
        
        if action == 'assign':
            models.assign_nurse_to_bed(nurse_id, bed_id)
        else:
            models.unassign_nurse_from_bed(nurse_id, bed_id)
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users')
@login_required
@admin_required
def api_users():
    """Get all users"""
    try:
        users = models.list_all_users()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/beds')
@login_required
def api_beds():
    """Get all beds (filtered by nurse if applicable)"""
    try:
        if session.get('role') == 'nurse':
            beds = models.get_nurse_beds(session['user_id'])
        else:
            beds = models.list_beds()
        return jsonify(beds)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices')
@login_required
@admin_required
def api_devices():
    """Get all devices"""
    try:
        devices = models.list_devices()
        return jsonify(devices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings')
@login_required
@admin_required
def api_settings():
    """Get all settings"""
    try:
        settings = models.get_all_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

