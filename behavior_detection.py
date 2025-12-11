"""
Abnormal Behavior Detection Module
Detects various patient behaviors using sensor data combinations
"""

import logging
from datetime import datetime, timedelta
from database import get_db
import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track state per bed
bed_state = {}

def initialize_bed_state(bed_id):
    """Initialize state tracking for a bed"""
    if bed_id not in bed_state:
        bed_state[bed_id] = {
            'last_motion_time': None,
            'last_distance': None,
            'motion_count_night': 0,
            'night_start': None,
            'last_humidity': None
        }

def detect_abnormal_behaviors(bed_id, temperature, humidity, motion, distance_cm):
    """
    Detect abnormal behaviors and return list of detected behaviors
    Returns list of tuples: (alert_type, message, severity)
    """
    behaviors = []
    settings = models.get_all_settings()
    
    # Initialize bed state if needed
    initialize_bed_state(bed_id)
    state = bed_state[bed_id]
    current_time = datetime.now()
    
    # Get recent readings for comparison
    recent_readings = models.get_readings_for_bed(bed_id, hours=1, limit=20)
    
    # 1. Patient trying to get off bed (distance + motion)
    # Already handled in server.py as 'bed_exit', but we'll enhance it
    if motion == 1 and distance_cm > float(settings.get('distance_bed_exit_cm', 50.0)):
        behaviors.append((
            'bed_exit',
            f'Patient attempting to get off bed: Motion detected with distance {distance_cm:.1f}cm',
            'critical'
        ))
    
    # 2. Possible fall (sudden large drop in distance)
    if state['last_distance'] is not None and distance_cm > 0 and state['last_distance'] > 0:
        distance_drop = state['last_distance'] - distance_cm
        fall_threshold = float(settings.get('fall_drop_threshold_cm', 30.0))
        
        if distance_drop > fall_threshold and distance_cm < 20:  # Fell close to sensor
            behaviors.append((
                'possible_fall',
                f'Possible fall detected: Distance dropped from {state["last_distance"]:.1f}cm to {distance_cm:.1f}cm (drop: {distance_drop:.1f}cm)',
                'critical'
            ))
    
    # Update last distance
    if distance_cm > 0:
        state['last_distance'] = distance_cm
    
    # 3. Long inactivity (no motion for X minutes)
    no_motion_timeout = float(settings.get('no_motion_timeout_minutes', 30))
    
    if motion == 1:
        state['last_motion_time'] = current_time
    elif state['last_motion_time'] is not None:
        inactivity_duration = (current_time - state['last_motion_time']).total_seconds() / 60
        
        if inactivity_duration > no_motion_timeout:
            # Check if we haven't already alerted for this inactivity period
            last_alert_time = state.get('last_inactivity_alert_time')
            if last_alert_time is None or (current_time - last_alert_time).total_seconds() > 300:  # Alert every 5 min max
                behaviors.append((
                    'long_inactivity',
                    f'No motion detected for {inactivity_duration:.1f} minutes (threshold: {no_motion_timeout} min)',
                    'warning'
                ))
                state['last_inactivity_alert_time'] = current_time
    
    # 4. Restlessness at night (frequent motion) - only during configured time window
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_time_str = f"{current_hour:02d}:{current_minute:02d}"
    
    # Get time window settings
    start_time_str = settings.get('restlessness_start_time', '22:00')
    end_time_str = settings.get('restlessness_end_time', '06:00')
    
    # Check if current time is within restlessness detection window
    is_in_window = False
    if start_time_str < end_time_str:  # Normal case: 8:00 to 17:00
        is_in_window = start_time_str <= current_time_str < end_time_str
    else:  # Overnight case: 22:00 to 06:00
        is_in_window = current_time_str >= start_time_str or current_time_str < end_time_str
    
    if is_in_window:
        if state['night_start'] is None:
            state['night_start'] = current_time
            state['motion_count_night'] = 0
        
        # Reset if new period
        if (current_time - state['night_start']).total_seconds() > 28800:  # 8 hours
            state['night_start'] = current_time
            state['motion_count_night'] = 0
        
        if motion == 1:
            state['motion_count_night'] += 1
        
        # Check for restlessness (more than threshold motions in 1 hour)
        night_duration = (current_time - state['night_start']).total_seconds() / 3600  # hours
        if night_duration > 0:
            motion_rate = state['motion_count_night'] / night_duration
            restlessness_threshold = float(settings.get('restlessness_motions_per_hour', 20.0))
            
            if motion_rate > restlessness_threshold:
                behaviors.append((
                    'restlessness_night',
                    f'Restlessness detected: {state["motion_count_night"]} motions in {night_duration:.1f} hours (rate: {motion_rate:.1f}/hr, threshold: {restlessness_threshold}/hr)',
                    'warning'
                ))
    else:
        # Reset tracking outside detection window
        state['night_start'] = None
        state['motion_count_night'] = 0
    
    # 5. Dangerous room humidity (breathing issues)
    # Low humidity (dry air) - can cause breathing issues
    low_humidity_threshold = float(settings.get('low_humidity_danger', 30.0))
    if humidity < low_humidity_threshold:
        behaviors.append((
            'low_humidity_danger',
            f'Dangerously low humidity: {humidity:.1f}% - May cause breathing discomfort (threshold: {low_humidity_threshold}%)',
            'warning'
        ))
    
    # Very high humidity - can cause breathing issues
    high_humidity_threshold = float(settings.get('high_humidity_danger', 70.0))
    if humidity > high_humidity_threshold:
        behaviors.append((
            'high_humidity_danger',
            f'Dangerously high humidity: {humidity:.1f}% - May cause breathing issues (threshold: {high_humidity_threshold}%)',
            'warning'
        ))
    
    return behaviors

def log_behavior_detection(bed_id, behavior_type, message, severity):
    """Log behavior detection to file"""
    log_message = f"[{datetime.now().isoformat()}] Bed {bed_id} - {severity.upper()} - {behavior_type}: {message}"
    logger.info(log_message)
    
    # Also log to database (could add a behavior_logs table)
    # For now, we'll use the alerts table

