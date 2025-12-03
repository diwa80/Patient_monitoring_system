# Patient Room Environmental & Activity Monitoring System

A complete web-based monitoring system for hospitals and care homes that tracks environmental conditions and patient activity using ESP8266 sensor nodes.

## Features

- **Real-time Monitoring**: Temperature, humidity, motion, and bed position tracking
- **Alert System**: Automatic alerts for bed exits, environmental issues, and inactivity
- **Role-based Access**: Separate dashboards for administrators and nurses
- **Modern UI**: Responsive Bootstrap 5 interface with Chart.js visualizations
- **RESTful API**: HTTP endpoint for ESP8266 sensor nodes to send data
- **SQLite Database**: Lightweight database for data storage

## Tech Stack

- **Backend**: Python, Flask, SQLite3
- **Frontend**: HTML5, Bootstrap 5, JavaScript, Chart.js
- **Authentication**: Flask sessions with Werkzeug password hashing
- **Hardware**: ESP8266 with DHT22, PIR, and HC-SR04 sensors

## Project Structure

```
project/
├── server.py              # Flask application
├── database.py            # Database connection helper
├── models.py              # Data models and helper functions
├── schema.sql             # Database schema
├── requirements.txt       # Python dependencies
├── create_admin.py        # Script to create admin user
│
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard_admin.html
│   ├── dashboard_nurse.html
│   ├── bed_overview.html
│   ├── alerts.html
│   ├── user_management.html
│   ├── device_management.html
│   └── settings.html
│
└── static/
    ├── css/
    │   └── style.css
    └── js/
        ├── main.js
        └── charts.js
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialize Database

The database will be automatically created when you first run the server. To create the default admin user:

```bash
python create_admin.py
```

Default credentials:
- Username: `admin`
- Password: `admin123`

**Change these credentials immediately in production!**

### 3. Run the Server

```bash
python server.py
```

The server will start on `http://localhost:5000`

### 4. Configure ESP8266

1. Open `esp8266_example/patient_monitor_node.ino` in Arduino IDE
2. Install ESP8266 board support and required libraries (see comments in .ino file)
3. Update configuration:
   - `WIFI_SSID`: Your WiFi network name
   - `WIFI_PASSWORD`: Your WiFi password
   - `SERVER_URL`: Your Flask server IP (e.g., `http://192.168.1.100:5000/api/data`)
   - `BED_ID`: Database bed ID (create beds via admin interface first)
   - `ESP_ID`: Unique identifier for this node
4. Upload to ESP8266

## Usage

### Admin Dashboard

- View all beds and system statistics
- Manage users and nurse assignments
- Configure alert thresholds
- Monitor all devices

### Nurse Dashboard

- View only assigned beds
- Monitor patient status
- Resolve alerts

### Creating Beds

Beds can be created via the database or by adding them directly:

```python
import models
models.create_bed("Bed 1", "Room 101")
```

### API Endpoint

ESP8266 nodes send data to:

```
POST /api/data
Content-Type: application/json

{
    "bed_id": 1,
    "temperature": 23.5,
    "humidity": 55.1,
    "motion": 1,
    "distance_cm": 42.0,
    "esp_id": "NODE1"
}
```

## Configuration

Alert thresholds can be configured via the Settings page (admin only):

- Temperature range (min/max)
- Humidity range (min/max)
- Bed exit distance threshold
- No-motion timeout

## Database Schema

- `users`: System users (admin/nurse)
- `beds`: Patient beds
- `nurse_assignments`: Nurse-to-bed assignments
- `readings`: Sensor data readings
- `alerts`: Generated alerts
- `devices`: ESP8266 device registry
- `settings`: System configuration

## Security Notes

- Change default admin password immediately
- Use HTTPS in production
- Implement proper session security
- Consider adding rate limiting for API endpoints
- Use environment variables for sensitive configuration

## License

MIT License
