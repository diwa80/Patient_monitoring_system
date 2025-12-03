# ESP8266 Patient Monitor Node — Setup Guide

## Overview

This guide walks through setting up an ESP8266 microcontroller to send sensor data (temperature, humidity, motion, distance) to the Patient Monitoring System.

## Components Required

- **ESP8266 (e.g., Wemos D1 Mini or NodeMCU)**
- **DHT22 Temperature/Humidity Sensor** (or DHT11)
- **HC-SR04 Ultrasonic Distance Sensor**
- **PIR Motion Sensor**
- **USB cable** for programming
- **Jumper wires and breadboard**

## Pin Configuration

| Sensor | Pin | ESP8266 Pin |
|--------|-----|-------------|
| DHT22 Data | - | D4 |
| PIR Motion | OUT | D0 |
| HC-SR04 Trigger | TRIG | D5 |
| HC-SR04 Echo | ECHO | D6 |
| Power | VCC | 3V3 |
| Ground | GND | GND |

## Arduino IDE Setup

1. **Install ESP8266 Board**:
   - Open Arduino IDE → Preferences
   - Add to "Additional Boards Manager URLs": `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - Go to Tools → Board Manager, search "ESP8266", install latest version

2. **Install Required Libraries**:
   - Sketch → Include Library → Manage Libraries
   - Search and install:
     - `DHT sensor library` by Adafruit
     - `ArduinoJson` by Benoit Blanchon (v6.x)

3. **Select Board**:
   - Tools → Board → "ESP8266 Modules" (or your specific board)
   - Tools → Flash Size → 4M (or appropriate for your board)

## Code Configuration

Edit these lines in the sketch before uploading:

```cpp
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_SERVER_IP:5000/api/data";  // e.g. http://192.168.8.18:5000/api/data
const int BED_ID = 1;  // unique ID for this bed (1-99)
const int SEND_INTERVAL = 5000;  // milliseconds between sends (5 seconds)
```

### Key fields:
- `serverUrl`: IP/hostname of the Patient Monitoring System server (on same network or reachable)
- `BED_ID`: unique integer for this bed; must match a bed in the database (create via admin UI)
- `SEND_INTERVAL`: time in milliseconds between sensor readings (5000 = 5 seconds)

## Upload & Test

1. **Connect ESP8266 via USB**
2. **Select COM port**: Tools → Port → (choose your USB port)
3. **Upload**: Sketch → Upload (Ctrl+U)
4. **Open Serial Monitor**: Tools → Serial Monitor (set baud to 115200)
5. **Expected output**:
   ```
   === Patient Monitor Node ===
   Bed ID: 1
   Connecting to WiFi: 3MobileWiFi-BE26
   ...
   WiFi connected!
   IP address: 192.168.x.x
   Device ID (MAC): AA:BB:CC:DD:EE:FF
   Sending: {"bed_id":1,"temperature":22.5,"humidity":55.0,"motion":0,"distance_cm":85,"esp_id":"AA:BB:CC:DD:EE:FF"}
   Server response code: 200
   ```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| WiFi not connecting | Check SSID/password, ensure 2.4GHz network (ESP8266 doesn't support 5GHz) |
| "Failed to read from DHT sensor" | Check DHT wiring, try DHT11 if DHT22 fails, add 10µF capacitor across VCC/GND |
| Distance always -1 | Check HC-SR04 wiring, ensure trigger/echo pins correct, test sensor in isolation |
| "POST failed" | Check server URL is reachable from the network, verify firewall, test ping to server IP |
| Device not appearing in web UI | Check bed_id exists in database, ensure esp_id (MAC) matches in logs, verify API endpoint accepts the JSON |

## Data Flow

1. ESP8266 reads sensors every 5 seconds (configurable)
2. Constructs JSON payload with `bed_id`, sensor readings, and `esp_id` (MAC address)
3. POSTs to server `/api/data` endpoint
4. Server validates, stores reading, checks thresholds, and creates alerts if needed
5. Alerts appear in web UI for admins/nurses to view

## Example JSON Sent

```json
{
  "bed_id": 1,
  "temperature": 22.5,
  "humidity": 55.0,
  "motion": 0,
  "distance_cm": 85,
  "esp_id": "AA:BB:CC:DD:EE:FF"
}
```

All fields are required. Server will reject if any are missing.

## Production Tips

- **Power**: Use a stable 3.3V supply; USB power works but consider USB power bank for portability.
- **Sensor Placement**: Mount DHT sensor away from direct sunlight; place HC-SR04 above bed facing down; mount PIR to detect motion in bed area.
- **WiFi**: Use 2.4GHz network with good signal; consider WiFi extender if room is far from router.
- **Logging**: Check Serial Monitor periodically to confirm data is being sent and server is responding.
- **Multiple Nodes**: For multiple beds, program each with unique `BED_ID` and upload; each will auto-generate unique `esp_id` from MAC.

## Advanced: Custom Sensors

To add or modify sensors:
1. Add pin definition (e.g., `#define TEMP_PIN D8`)
2. Create read function (e.g., `readCustomSensor()`)
3. Add to JSON payload in `loop()`
4. Update server `models.py` and database schema if new sensor type

---

For more info, see `PROJECT_REPORT.md` in the main repository.
