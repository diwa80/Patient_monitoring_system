# Troubleshooting: No Bed/Alert Data on Dashboard

## Quick Checklist

### 1. Beds Must Exist in Database

The ESP8266 sends data with a `bed_id` (e.g., 1), but if that bed doesn't exist in the `beds` table, the data is rejected or ignored.

**Create beds via admin UI:**
1. Log in as admin
2. Go to **Settings** page
3. Look for a "Manage Beds" section (if available)

**OR directly in database (SQLite):**

Open a terminal and run:

```powershell
cd f:\Diwakar\new monitoring system
python -c "
import models
# Create some test beds
models.create_bed('Bed 1', 'Room 101')
models.create_bed('Bed 2', 'Room 102')
models.create_bed('Bed 3', 'Room 103')
print('Beds created successfully')
"
```

### 2. Verify ESP8266 is Sending Data

Check the **server logs** for POST requests:

```powershell
# While server is running (in terminal where you ran python server.py):
# You should see console output like:
# Behavior detected - Bed 1: ...
# Or look for HTTP POST requests
```

**Or check database directly:**

```powershell
python -c "
import models
readings = models.get_latest_readings_per_bed()
for r in readings:
    print(f\"Bed {r['bed_id']}: {r['temperature']}°C, {r['humidity']}%, Motion: {r['motion']}, Distance: {r['distance_cm']}cm\")
if not readings:
    print('No readings in database yet. ESP8266 may not be sending data or bed_id does not exist.')
"
```

### 3. Verify API Endpoints Are Working

Test the API manually using `curl` or Postman:

**Get all beds:**
```powershell
curl http://localhost:5000/api/beds
```

**Get latest readings:**
```powershell
curl http://localhost:5000/api/latest_readings
```

**Get all alerts:**
```powershell
curl http://localhost:5000/api/alerts
```

Each should return JSON. If you get errors, check server console for stack traces.

### 4. Check ESP8266 Serial Monitor

Make sure the ESP8266 is:
- ✅ Connecting to WiFi
- ✅ Getting IP address
- ✅ Displaying "Sending: {...esp_id...}"
- ✅ Getting "Server response code: 200" (not 400 or 500)

**If you see "POST failed" or error code 400/500:**
- Check that `BED_ID` in ESP8266 matches an existing bed in database
- Check server console for validation errors
- Verify `esp_id` field is being sent (should show MAC address)

### 5. Full Data Flow Test

1. **Create beds** (see step 1 above)
2. **Restart server** (`python server.py`)
3. **ESP8266 starts sending data** (should see 200 response in Serial Monitor)
4. **Check readings in database** (see step 2 above)
5. **Refresh dashboard** (`http://localhost:5000/`)
6. **Beds should appear with temperature/humidity**

### 6. If Dashboard Still Shows No Data

**Check browser console** (F12 → Console tab):
- Look for JavaScript errors in `/api/latest_readings` calls
- Network errors or CORS issues

**Refresh browser cache:**
```powershell
# Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
```

**Check server logs for 403/401 errors:**
- May be a session/permission issue
- Verify you're logged in as admin

### 7. Debug: Step-by-Step

Run this Python script to manually test the entire pipeline:

```python
# test_system.py
import sqlite3
from database import get_db
import models

print("=== Patient Monitoring System Diagnostic ===\n")

# 1. Check beds
db = get_db()
beds = db.execute('SELECT * FROM beds').fetchall()
print(f"Beds in database: {len(beds)}")
for bed in beds:
    print(f"  - {dict(bed)}")
db.close()

# 2. Check readings
readings = models.get_latest_readings_per_bed()
print(f"\nLatest readings: {len(readings)}")
for r in readings:
    print(f"  - Bed {r['bed_id']}: {r['temperature']}°C")

# 3. Check alerts
alerts = models.get_all_alerts()
print(f"\nAlerts in database: {len(alerts)}")
for a in alerts[:5]:
    print(f"  - Bed {a['bed_id']}: {a['alert_type']} ({a['status']})")

# 4. Check devices
db = get_db()
devices = db.execute('SELECT * FROM devices').fetchall()
print(f"\nDevices known: {len(devices)}")
for dev in devices:
    print(f"  - {dict(dev)}")
db.close()

print("\n=== End Diagnostic ===")
```

Save this as `test_system.py` and run:
```powershell
python test_system.py
```

---

## Common Issues & Solutions

| Symptom | Cause | Solution |
|---------|-------|----------|
| Dashboard shows "Loading beds..." forever | No beds in DB or API error | Create beds using step 1 |
| ESP8266 logs "POST failed" or code 400 | Bed ID doesn't exist | Create bed matching ESP8266's `BED_ID` |
| Beds appear but no temp/humidity | No readings stored | Check ESP8266 sending data (Serial Monitor) |
| "Server response code: 200" but no data appears | Readings stored but not in latest_readings query | Check readings table directly in DB |
| Permission denied error in console | Admin session expired or permissions missing | Log out and log in again as admin |

---

**Next steps:**

1. **Create beds** (most common issue)
2. **Verify ESP8266 is sending data** (check Serial Monitor and DB)
3. **Refresh dashboard** in browser
4. Run the diagnostic script if still issues

Let me know what you find!
