-- Patient Room Environmental & Activity Monitoring System Database Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'nurse')),
    menu_permissions TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS beds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bed_name TEXT NOT NULL,
    room_no TEXT
);

CREATE TABLE IF NOT EXISTS nurse_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nurse_id INTEGER NOT NULL REFERENCES users(id),
    bed_id INTEGER NOT NULL REFERENCES beds(id),
    UNIQUE(nurse_id, bed_id)
);

CREATE TABLE IF NOT EXISTS readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bed_id INTEGER NOT NULL REFERENCES beds(id),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    temperature REAL,
    humidity REAL,
    motion INTEGER,
    distance_cm REAL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bed_id INTEGER NOT NULL REFERENCES beds(id),
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    esp_id TEXT UNIQUE,
    ip TEXT,
    last_seen DATETIME,
    status TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_readings_bed_timestamp ON readings(bed_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_bed_status ON alerts(bed_id, status);
CREATE INDEX IF NOT EXISTS idx_nurse_assignments_nurse ON nurse_assignments(nurse_id);
CREATE INDEX IF NOT EXISTS idx_nurse_assignments_bed ON nurse_assignments(bed_id);

-- Insert default settings
INSERT OR IGNORE INTO settings (key, value) VALUES 
    ('temp_min', '18.0'),
    ('temp_max', '24.0'),
    ('humidity_min', '40.0'),
    ('humidity_max', '60.0'),
    ('distance_bed_exit_cm', '50.0'),
    ('no_motion_timeout_minutes', '30'),
    ('fall_drop_threshold_cm', '30.0'),
    ('restlessness_motions_per_hour', '20.0'),
    ('fever_temp_threshold', '37.5'),
    ('fever_temp_increase', '1.5'),
    ('low_humidity_danger', '30.0'),
    ('high_humidity_danger', '70.0');

-- Default admin user will be created by running: python create_admin.py
-- Or create via web interface after setting up first admin manually

