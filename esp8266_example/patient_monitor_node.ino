/*
 * ESP8266 Patient Monitoring Sensor Node
 * Sends sensor data to Flask server via HTTP POST
 * 
 * Sensors:
 * - DHT22 (Temperature & Humidity)
 * - PIR Motion Sensor
 * - HC-SR04 Ultrasonic Sensor
 * 
 * Configuration:
 * - Update WIFI_SSID and WIFI_PASSWORD
 * - Update SERVER_URL to your Flask server IP/domain
 * - Update BED_ID to match database bed ID
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define SERVER_URL "http://192.168.1.100:5000/api/data"  // Update with your server IP

#define BED_ID 1  // Update to match your database bed ID
#define ESP_ID "NODE1"  // Unique identifier for this ESP8266

// ==================== SENSOR PINS ====================
#define DHT_PIN D4
#define DHT_TYPE DHT22
#define PIR_PIN D2
#define TRIGGER_PIN D5
#define ECHO_PIN D6

// ==================== SENSOR OBJECTS ====================
DHT dht(DHT_PIN, DHT_TYPE);

// ==================== TIMING ====================
unsigned long lastReading = 0;
unsigned long lastPost = 0;
const unsigned long READING_INTERVAL = 5000;  // Read sensors every 5 seconds
const unsigned long POST_INTERVAL = 10000;     // Post to server every 10 seconds

// ==================== SENSOR DATA ====================
struct SensorData {
    float temperature;
    float humidity;
    int motion;
    float distance;
};

SensorData currentData;

void setup() {
    Serial.begin(115200);
    delay(100);
    
    Serial.println("\n=== Patient Monitoring Sensor Node ===");
    Serial.println("ESP ID: " + String(ESP_ID));
    Serial.println("Bed ID: " + String(BED_ID));
    
    // Initialize sensors
    pinMode(PIR_PIN, INPUT);
    pinMode(TRIGGER_PIN, OUTPUT);
    pinMode(ECHO_PIN, INPUT);
    dht.begin();
    
    // Connect to WiFi
    connectToWiFi();
    
    Serial.println("Setup complete. Starting monitoring...");
}

void loop() {
    unsigned long currentMillis = millis();
    
    // Read sensors at specified interval
    if (currentMillis - lastReading >= READING_INTERVAL) {
        readSensors();
        lastReading = currentMillis;
    }
    
    // Post data to server at specified interval
    if (currentMillis - lastPost >= POST_INTERVAL) {
        postDataToServer();
        lastPost = currentMillis;
    }
    
    delay(100);
}

void connectToWiFi() {
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi connected!");
        Serial.print("IP address: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nWiFi connection failed!");
    }
}

void readSensors() {
    // Read DHT22 (Temperature & Humidity)
    float temp = dht.readTemperature();
    float hum = dht.readHumidity();
    
    if (!isnan(temp) && !isnan(hum)) {
        currentData.temperature = temp;
        currentData.humidity = hum;
    } else {
        Serial.println("Failed to read DHT22 sensor");
    }
    
    // Read PIR Motion Sensor
    currentData.motion = digitalRead(PIR_PIN) == HIGH ? 1 : 0;
    
    // Read Ultrasonic Sensor (HC-SR04)
    currentData.distance = readUltrasonicDistance();
    
    // Print to serial for debugging
    Serial.println("--- Sensor Readings ---");
    Serial.print("Temperature: ");
    Serial.print(currentData.temperature);
    Serial.println(" °C");
    Serial.print("Humidity: ");
    Serial.print(currentData.humidity);
    Serial.println(" %");
    Serial.print("Motion: ");
    Serial.println(currentData.motion ? "Detected" : "None");
    Serial.print("Distance: ");
    Serial.print(currentData.distance);
    Serial.println(" cm");
    Serial.println("----------------------");
}

float readUltrasonicDistance() {
    // Clear trigger pin
    digitalWrite(TRIGGER_PIN, LOW);
    delayMicroseconds(2);
    
    // Send 10 microsecond pulse
    digitalWrite(TRIGGER_PIN, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIGGER_PIN, LOW);
    
    // Read echo pin
    long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
    
    // Calculate distance (speed of sound = 343 m/s = 0.0343 cm/μs)
    // Divide by 2 because sound travels to object and back
    float distance = (duration * 0.0343) / 2.0;
    
    // Return valid distance (typically 2-400 cm for HC-SR04)
    if (distance > 0 && distance < 400) {
        return distance;
    } else {
        return -1;  // Invalid reading
    }
}

void postDataToServer() {
    // Check WiFi connection
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi not connected. Reconnecting...");
        connectToWiFi();
        return;
    }
    
    // Create JSON payload
    StaticJsonDocument<256> doc;
    doc["bed_id"] = BED_ID;
    doc["temperature"] = currentData.temperature;
    doc["humidity"] = currentData.humidity;
    doc["motion"] = currentData.motion;
    doc["distance_cm"] = currentData.distance;
    doc["esp_id"] = ESP_ID;
    
    // Serialize JSON
    String jsonPayload;
    serializeJson(doc, jsonPayload);
    
    Serial.println("Posting data to server...");
    Serial.println("Payload: " + jsonPayload);
    
    // Create HTTP client
    WiFiClient client;
    HTTPClient http;
    
    http.begin(client, SERVER_URL);
    http.addHeader("Content-Type", "application/json");
    
    // Send POST request
    int httpResponseCode = http.POST(jsonPayload);
    
    if (httpResponseCode > 0) {
        Serial.print("HTTP Response code: ");
        Serial.println(httpResponseCode);
        
        String response = http.getString();
        Serial.println("Response: " + response);
        
        if (httpResponseCode == 200) {
            Serial.println("Data posted successfully!");
        }
    } else {
        Serial.print("Error code: ");
        Serial.println(httpResponseCode);
        Serial.println("Failed to post data");
    }
    
    http.end();
}

/*
 * INSTALLATION INSTRUCTIONS:
 * 
 * 1. Install ESP8266 Board Support in Arduino IDE:
 *    - File → Preferences
 *    - Add to "Additional Board Manager URLs":
 *      http://arduino.esp8266.com/stable/package_esp8266com_index.json
 *    - Tools → Board → Boards Manager → Search "ESP8266" → Install
 * 
 * 2. Install Required Libraries:
 *    - Sketch → Include Library → Manage Libraries
 *    - Install:
 *      * "DHT sensor library" by Adolfo Rodriguez
 *      * "ArduinoJson" by Benoit Blanchon
 * 
 * 3. Configure:
 *    - Update WIFI_SSID and WIFI_PASSWORD
 *    - Update SERVER_URL with your Flask server IP address
 *    - Update BED_ID to match database bed ID
 *    - Update ESP_ID to unique identifier
 * 
 * 4. Wiring:
 *    DHT22:
 *      - VCC → 3.3V
 *      - GND → GND
 *      - DATA → D4
 *      - (Optional: 10kΩ pull-up resistor between DATA and VCC)
 * 
 *    PIR Sensor:
 *      - VCC → 5V
 *      - GND → GND
 *      - OUT → D2
 * 
 *    HC-SR04 Ultrasonic:
 *      - VCC → 5V
 *      - GND → GND
 *      - Trig → D5
 *      - Echo → D6
 * 
 * 5. Upload:
 *    - Select board: Tools → Board → NodeMCU 1.0 (or your ESP8266 board)
 *    - Select port: Tools → Port → (your COM port)
 *    - Click Upload
 * 
 * 6. Monitor:
 *    - Open Serial Monitor (115200 baud)
 *    - Watch for sensor readings and HTTP responses
 */

