# API Endpoints Documentation

Patient Room Environmental & Activity Monitoring System

---

## 🔐 Authentication & Session

### Login
- **POST** `/login`
  - **Description**: User authentication and session creation
  - **Parameters**: 
    - `username` (form): Username
    - `password` (form): Password
  - **Returns**: Redirects to dashboard or shows error
  - **Auth Required**: No
  - **Features**: 
    - Rate limiting (5 failed attempts)
    - Account lockout after 5 failures
    - Session timeout (30 minutes)

### Logout
- **GET** `/logout`
  - **Description**: End user session
  - **Returns**: Redirects to login page
  - **Auth Required**: No (but clears session if exists)
  - **Audit Log**: Yes

---

## 📊 Dashboard Pages

### Root
- **GET** `/`
  - **Description**: Root page, redirects to appropriate dashboard
  - **Returns**: Redirect to admin or nurse dashboard
  - **Auth Required**: Yes
  - **Access**: All authenticated users

### Admin Dashboard
- **GET** `/admin/dashboard`
  - **Description**: Administrator dashboard page
  - **Returns**: HTML template with admin view
  - **Auth Required**: Yes
  - **Access**: Admin only

### Nurse Dashboard
- **GET** `/nurse/dashboard`
  - **Description**: Nurse dashboard page
  - **Returns**: HTML template with nurse view
  - **Auth Required**: Yes
  - **Access**: All authenticated users

---

## 🏥 Bed Management

### View Bed Overview
- **GET** `/beds/<int:bed_id>`
  - **Description**: View detailed information for specific bed
  - **Parameters**: 
    - `bed_id` (URL): Bed ID
  - **Returns**: HTML template with bed details
  - **Auth Required**: Yes
  - **Access**: Admin or assigned nurse

### Bed Management Page
- **GET** `/beds/manage`
  - **Description**: Bed management interface
  - **Returns**: HTML template with bed list
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only

### Create Bed
- **POST** `/beds/manage`
  - **Description**: Create a new bed
  - **Parameters**: 
    - `bed_name` (form): Bed name/number
    - `room_no` (form): Room number (optional)
  - **Returns**: Redirect to bed management page
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Audit Log**: Yes

### Delete Bed
- **POST** `/beds/<int:bed_id>/delete`
  - **Description**: Delete bed and all related data
  - **Parameters**: 
    - `bed_id` (URL): Bed ID
  - **Returns**: Redirect to bed management page
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Audit Log**: Yes
  - **Note**: Also deletes readings, alerts, and nurse assignments

---

## 🔔 Alerts Management

### Alerts Page
- **GET** `/alerts`
  - **Description**: View all alerts page
  - **Returns**: HTML template with alerts interface
  - **Auth Required**: Yes
  - **Access**: All authenticated users

### Get Alerts
- **GET** `/api/alerts`
  - **Description**: Retrieve alerts with filtering
  - **Query Parameters**: 
    - `status` (optional): Filter by status ('new', 'resolved')
  - **Returns**: JSON array of alerts
  - **Auth Required**: Yes
  - **Access**: All (filtered by nurse assignment)
  - **Example Response**:
    ```json
    [
      {
        "id": 1,
        "bed_id": 1,
        "bed_name": "Bed 1",
        "room_no": "101",
        "alert_type": "bed_exit",
        "message": "Patient attempting to get off bed",
        "status": "new",
        "created_at": "2025-12-11 10:30:00"
      }
    ]
    ```

### Resolve Alert
- **POST** `/api/alerts/<int:alert_id>/resolve`
  - **Description**: Mark alert as resolved
  - **Parameters**: 
    - `alert_id` (URL): Alert ID
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: Yes
  - **Access**: All (with permission check)
  - **Audit Log**: Yes

### Clear All Alerts
- **POST** `/api/alerts/clear/all`
  - **Description**: Mark all new alerts as resolved
  - **Returns**: `{"status": "ok", "message": "All alerts cleared"}`
  - **Auth Required**: Yes (Admin with 'users' permission)
  - **Access**: Admin only

---

## 👥 User Management

### Users Page
- **GET** `/users`
  - **Description**: User management interface
  - **Returns**: HTML template with user management
  - **Auth Required**: Yes (Admin or with 'users' permission)
  - **Access**: Permission-based

### Get All Users
- **GET** `/api/users`
  - **Description**: Retrieve all users with bed assignments
  - **Returns**: JSON array of users with beds
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Example Response**:
    ```json
    [
      {
        "id": 1,
        "username": "admin",
        "role": "admin",
        "status": "active",
        "failed_login_attempts": 0,
        "locked_at": null,
        "menu_permissions": ["dashboard", "users", "settings"],
        "beds": []
      }
    ]
    ```

### Create User
- **POST** `/users/create`
  - **Description**: Create new user account
  - **Parameters**: 
    - `username` (form): Username
    - `password` (form): Password
    - `role` (form): User role ('admin' or 'nurse')
    - `beds[]` (form): Array of bed IDs to assign (nurses only)
    - `menu_permissions[]` (form): Array of permission keys
  - **Returns**: `{"status": "ok", "user_id": <id>}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Audit Log**: Yes

### Toggle User Status
- **POST** `/users/<int:user_id>/toggle`
  - **Description**: Enable/disable user account
  - **Parameters**: 
    - `user_id` (URL): User ID
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only

### Update User
- **POST** `/users/<int:user_id>/update`
  - **Description**: Update user details and permissions
  - **Parameters**: 
    - `user_id` (URL): User ID
    - `username` (form): New username
    - `role` (form): User role
    - `beds[]` (form): Array of bed IDs
    - `menu_permissions[]` (form): Array of permissions
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only

### Reset Password
- **POST** `/users/<int:user_id>/reset_password`
  - **Description**: Reset user password (legacy endpoint)
  - **Parameters**: 
    - `user_id` (URL): User ID
    - `password` (form): New password
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only

### Change Password
- **POST** `/users/<int:user_id>/change-password`
  - **Description**: Change user password
  - **Parameters**: 
    - `user_id` (URL): User ID
    - `new_password` (form): New password (min 6 characters)
  - **Returns**: `{"status": "ok", "message": "Password changed successfully"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Audit Log**: Yes

### Unlock User Account
- **POST** `/users/<int:user_id>/unlock`
  - **Description**: Unlock locked user account
  - **Parameters**: 
    - `user_id` (URL): User ID
  - **Returns**: `{"status": "ok", "message": "Account unlocked successfully"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Audit Log**: Yes
  - **Note**: Resets failed login attempts

### Delete User
- **POST** `/users/<int:user_id>/delete`
  - **Description**: Delete user and all assignments
  - **Parameters**: 
    - `user_id` (URL): User ID
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Audit Log**: Yes

---

## 🛏️ Nurse Assignments

### Assign/Unassign Nurse
- **POST** `/assignments`
  - **Description**: Assign or unassign nurse to bed
  - **Parameters**: 
    - `nurse_id` (form): Nurse user ID
    - `bed_id` (form): Bed ID
    - `action` (form): 'assign' or 'unassign'
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only

---

## ⚙️ Settings Management

### Settings Page
- **GET** `/settings`
  - **Description**: System settings configuration page
  - **Returns**: HTML template with settings form
  - **Auth Required**: Yes (Admin or with 'settings' permission)
  - **Access**: Permission-based

### Update Settings
- **POST** `/settings`
  - **Description**: Update system configuration
  - **Parameters**: 
    - `temp_min` (form): Minimum temperature threshold
    - `temp_max` (form): Maximum temperature threshold
    - `humidity_min` (form): Minimum humidity threshold
    - `humidity_max` (form): Maximum humidity threshold
    - `distance_bed_exit_cm` (form): Bed exit distance threshold
    - `no_motion_timeout_minutes` (form): Inactivity timeout
    - `fall_drop_threshold_cm` (form): Fall detection threshold
    - `restlessness_motions_per_hour` (form): Restlessness threshold
    - `restlessness_start_time` (form): Restlessness detection start time
    - `restlessness_end_time` (form): Restlessness detection end time
    - `low_humidity_danger` (form): Low humidity danger level
    - `high_humidity_danger` (form): High humidity danger level
  - **Returns**: Redirect to settings page with success message
  - **Auth Required**: Yes (Admin or with 'settings' permission)
  - **Access**: Permission-based
  - **Audit Log**: Yes

### Get Settings
- **GET** `/api/settings`
  - **Description**: Retrieve all system settings
  - **Returns**: JSON object with all settings
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Example Response**:
    ```json
    {
      "temp_min": 18.0,
      "temp_max": 24.0,
      "humidity_min": 40.0,
      "humidity_max": 60.0,
      "distance_bed_exit_cm": 50.0,
      "no_motion_timeout_minutes": 30.0,
      "restlessness_start_time": "22:00",
      "restlessness_end_time": "06:00"
    }
    ```

---

## 📜 Audit Logs

### Audit Logs Page
- **GET** `/logs`
  - **Description**: View audit logs page
  - **Returns**: HTML template with logs interface
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only

### Get Audit Logs
- **GET** `/api/logs`
  - **Description**: Retrieve audit logs with filtering
  - **Query Parameters**: 
    - `limit` (optional): Number of records (default: 100)
    - `user_id` (optional): Filter by user ID
    - `action` (optional): Filter by action type
  - **Returns**: JSON array of audit log entries
  - **Auth Required**: Yes (Admin)
  - **Access**: Admin only
  - **Example Response**:
    ```json
    [
      {
        "id": 1,
        "user_id": 1,
        "username": "admin",
        "action": "LOGIN_SUCCESS",
        "target_type": "user",
        "target_id": 1,
        "details": "User admin logged in",
        "ip_address": "192.168.1.100",
        "timestamp": "2025-12-11 10:30:00"
      }
    ]
    ```

---

## 📡 ESP8266 Data Collection

### Receive Sensor Data
- **POST** `/api/data`
  - **Description**: Receive sensor data from ESP8266 nodes
  - **Content-Type**: `application/json`
  - **Parameters** (JSON body):
    - `bed_id` (integer): Bed ID
    - `temperature` (float): Temperature in Celsius
    - `humidity` (float): Humidity percentage
    - `motion` (integer): Motion detected (0 or 1)
    - `distance_cm` (float): Distance from ultrasonic sensor
    - `esp_id` (string): ESP8266 device identifier
  - **Returns**: `{"status": "ok"}`
  - **Auth Required**: No
  - **Access**: Public (for IoT devices)
  - **Features**:
    - Stores reading in database
    - Updates device status
    - Checks alert thresholds
    - Triggers behavior detection
    - Creates alerts automatically
  - **Example Request**:
    ```json
    {
      "bed_id": 1,
      "temperature": 23.5,
      "humidity": 55.1,
      "motion": 1,
      "distance_cm": 42.0,
      "esp_id": "ESP_NODE_001"
    }
    ```

---

## 📈 Real-time Data APIs

### Get Latest Readings
- **GET** `/api/latest_readings`
  - **Description**: Get latest reading for each bed
  - **Returns**: JSON array of latest readings
  - **Auth Required**: Yes
  - **Access**: All (filtered by nurse assignments)
  - **Example Response**:
    ```json
    [
      {
        "id": 123,
        "bed_id": 1,
        "bed_name": "Bed 1",
        "room_no": "101",
        "temperature": 23.5,
        "humidity": 55.1,
        "motion": 1,
        "distance_cm": 42.0,
        "timestamp": "2025-12-11 10:30:00",
        "active_alert_count": 2,
        "latest_alert_type": "bed_exit"
      }
    ]
    ```

### Get Bed Readings
- **GET** `/api/bed/<int:bed_id>/readings`
  - **Description**: Get historical readings for specific bed
  - **Parameters**: 
    - `bed_id` (URL): Bed ID
  - **Query Parameters**: 
    - `hours` (optional): Time range in hours (default: 24)
  - **Returns**: JSON array of readings
  - **Auth Required**: Yes
  - **Access**: Admin or assigned nurse
  - **Example Response**:
    ```json
    [
      {
        "id": 123,
        "bed_id": 1,
        "temperature": 23.5,
        "humidity": 55.1,
        "motion": 1,
        "distance_cm": 42.0,
        "timestamp": "2025-12-11 10:30:00"
      }
    ]
    ```

### Get Overview Statistics
- **GET** `/api/stats/overview`
  - **Description**: Get dashboard statistics
  - **Returns**: JSON object with statistics
  - **Auth Required**: Yes
  - **Access**: All (filtered by nurse assignments)
  - **Example Response**:
    ```json
    {
      "monitored_beds": 5,
      "active_movements": 2,
      "fall_risk": 1,
      "avg_temperature": 23.2,
      "total_beds": 5,
      "new_alerts_today": 3,
      "devices_online": 4,
      "active_nurses": 3
    }
    ```

---

## 📊 Chart Data APIs

### Temperature Chart Data
- **GET** `/api/charts/temperature`
  - **Description**: Get average temperature per bed (24h)
  - **Returns**: JSON object with chart data
  - **Auth Required**: Yes
  - **Access**: All (filtered by nurse assignments)
  - **Example Response**:
    ```json
    {
      "labels": ["Bed 1", "Bed 2", "Bed 3"],
      "temperatures": [23.5, 24.1, 22.8]
    }
    ```

### Alerts Chart Data
- **GET** `/api/charts/alerts`
  - **Description**: Get alert counts by type (24h)
  - **Returns**: JSON object with chart data
  - **Auth Required**: Yes
  - **Access**: All authenticated users
  - **Example Response**:
    ```json
    {
      "labels": ["bed_exit", "humidity_out_of_range", "long_inactivity"],
      "counts": [5, 3, 2]
    }
    ```

---

## 🔍 Additional APIs

### Get All Beds
- **GET** `/api/beds`
  - **Description**: Get list of all beds
  - **Returns**: JSON array of beds
  - **Auth Required**: Yes
  - **Access**: All (filtered by nurse assignments)
  - **Example Response**:
    ```json
    [
      {
        "id": 1,
        "bed_name": "Bed 1",
        "room_no": "101"
      }
    ]
    ```

---

## 📝 Notes

### Authentication & Authorization
- Most endpoints require authentication via session
- Admin-only endpoints return 403 if accessed by non-admin
- Nurse endpoints are filtered by bed assignments
- Session timeout: 30 minutes of inactivity

### Rate Limiting
- Login: 5 attempts before account lockout
- Account locked for manual unlock by admin

### Audit Logging
The following actions are automatically logged:
- Login success/failure
- Logout
- User creation/deletion/unlock
- Password changes
- Settings updates
- Alert resolutions
- Bed creation/deletion

### Error Responses
All endpoints return errors in this format:
```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad request (missing parameters)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `500` - Server error

---

## 🚀 Usage Examples

### ESP8266 Data Submission
```bash
curl -X POST http://192.168.1.100:5000/api/data \
  -H "Content-Type: application/json" \
  -d '{
    "bed_id": 1,
    "temperature": 23.5,
    "humidity": 55.1,
    "motion": 1,
    "distance_cm": 42.0,
    "esp_id": "ESP_NODE_001"
  }'
```

### Get Latest Readings
```bash
curl http://192.168.1.100:5000/api/latest_readings \
  -H "Cookie: session=<session_cookie>"
```

### Resolve Alert
```bash
curl -X POST http://192.168.1.100:5000/api/alerts/5/resolve \
  -H "Cookie: session=<session_cookie>"
```

### Create User
```bash
curl -X POST http://192.168.1.100:5000/users/create \
  -H "Cookie: session=<session_cookie>" \
  -F "username=nurse1" \
  -F "password=secure123" \
  -F "role=nurse" \
  -F "beds[]=1" \
  -F "beds[]=2"
```

---

**Total Endpoints: 33**
- **Page Routes (HTML)**: 10
- **API Routes (JSON)**: 23
  - **GET**: 10
  - **POST**: 13
