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
            'last_temperature': None,
            'last_temperature_time': None,
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
    if motion == 1 and distance_cm > settings.get('distance_bed_exit_cm', 50.0):
        behaviors.append((
            'bed_exit',
            f'Patient attempting to get off bed: Motion detected with distance {distance_cm:.1f}cm',
            'critical'
        ))
    
    # 2. Possible fall (sudden large drop in distance)
    if state['last_distance'] is not None and distance_cm > 0 and state['last_distance'] > 0:
        distance_drop = state['last_distance'] - distance_cm
        fall_threshold = settings.get('fall_drop_threshold_cm', 30.0)
        
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
    no_motion_timeout = settings.get('no_motion_timeout_minutes', 30)
    
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
    
    # 4. Restlessness at night (frequent motion)
    current_hour = current_time.hour
    is_night = current_hour >= 22 or current_hour < 6  # 10 PM to 6 AM
    
    if is_night:
        if state['night_start'] is None:
            state['night_start'] = current_time
            state['motion_count_night'] = 0
        
        # Reset if new night period
        if (current_time - state['night_start']).total_seconds() > 28800:  # 8 hours
            state['night_start'] = current_time
            state['motion_count_night'] = 0
        
        if motion == 1:
            state['motion_count_night'] += 1
        
        # Check for restlessness (more than threshold motions in 1 hour during night)
        night_duration = (current_time - state['night_start']).total_seconds() / 3600  # hours
        if night_duration > 0:
            motion_rate = state['motion_count_night'] / night_duration
            restlessness_threshold = settings.get('restlessness_motions_per_hour', 20.0)
            
            if motion_rate > restlessness_threshold:
                behaviors.append((
                    'restlessness_night',
                    f'Restlessness detected: {state["motion_count_night"]} motions in {night_duration:.1f} hours during night (rate: {motion_rate:.1f}/hr, threshold: {restlessness_threshold}/hr)',
                    'warning'
                ))
    else:
        # Reset night tracking during day
        state['night_start'] = None
        state['motion_count_night'] = 0
    
    # 5. Sudden temperature rise (fever warning)
    if state['last_temperature'] is not None and temperature > 0:
        temp_increase = temperature - state['last_temperature']
        temp_increase_threshold = 1.5  # °C increase in short time
        
        # Check if significant increase in last 30 minutes
        if state['last_temperature_time'] is not None:
            time_diff = (current_time - state['last_temperature_time']).total_seconds() / 60  # minutes
            
            if time_diff <= 30 and temp_increase > temp_increase_threshold:
                behaviors.append((
                    'fever_warning',
                    f'Sudden temperature rise: {state["last_temperature"]:.1f}°C to {temperature:.1f}°C (+{temp_increase:.1f}°C in {time_diff:.1f} min) - Possible fever',
                    'warning'
                ))
        
        # Also check absolute high temperature
        fever_threshold = settings.get('fever_temp_threshold', 37.5)
        if temperature > fever_threshold:
            behaviors.append((
                'high_temperature',
                f'Elevated temperature detected: {temperature:.1f}°C - Possible fever (threshold: {fever_threshold}°C)',
                'warning'
            ))
    
    # Update temperature tracking
    if temperature > 0:
        state['last_temperature'] = temperature
        state['last_temperature_time'] = current_time
    
    # 6. Dangerous room humidity (breathing issues)
    # Low humidity (dry air) - can cause breathing issues
    low_humidity_threshold = settings.get('low_humidity_danger', 30.0)
    if humidity < low_humidity_threshold:
        behaviors.append((
            'low_humidity_danger',
            f'Dangerously low humidity: {humidity:.1f}% - May cause breathing discomfort (threshold: {low_humidity_threshold}%)',
            'warning'
        ))
    
    # Very high humidity - can cause breathing issues
    high_humidity_threshold = settings.get('high_humidity_danger', 70.0)
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

