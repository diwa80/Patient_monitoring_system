#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

#define DHTPIN D4
#define DHTTYPE DHT22

#define PIR_PIN D0
#define TRIG_PIN D5
#define ECHO_PIN D6

// ==== CONFIGURE THESE ====
const char* ssid     = "3MobileWiFi-BE26";
const char* password = "dYEf9if2nt2";
const char* serverUrl = "http://192.168.8.18:5000/api/data";
const int BED_ID = 1;  // unique ID per bed
const int SEND_INTERVAL = 5000;  // milliseconds between sends (5 seconds)
// =========================

DHT dht(DHTPIN, DHTTYPE);
String espId = "";  // Will hold the device's MAC address as unique ID
unsigned long lastSendTime = 0;

// Measure distance using ultrasonic sensor HC-SR04
long measureDistanceCm() {
  long duration;
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  duration = pulseIn(ECHO_PIN, HIGH, 30000); // timeout 30 ms
  long distance = duration * 0.034 / 2;
  
  // Filter out invalid readings
  if (distance == 0 || distance > 400) {
    distance = -1;  // invalid
  }
  return distance;
}

// Get MAC address as unique device ID
String getMacAddress() {
  byte mac[6];
  WiFi.macAddress(mac);
  String result = "";
  for (int i = 0; i < 6; i++) {
    if (mac[i] < 16) result += "0";
    result += String(mac[i], HEX);
    if (i < 5) result += ":";
  }
  return result;
}

void setup() {
  Serial.begin(115200);
  delay(1000);  // Give serial time to start
  
  Serial.println("\n\n=== Patient Monitor Node ===");
  Serial.print("Bed ID: ");
  Serial.println(BED_ID);
  
  // Initialize pins
  pinMode(PIR_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  digitalWrite(TRIG_PIN, LOW);

  // Initialize DHT sensor
  dht.begin();
  Serial.println("DHT sensor initialized");

  // Connect to WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  
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
    
    // Get MAC address as unique device ID
    espId = getMacAddress();
    Serial.print("Device ID (MAC): ");
    Serial.println(espId);
  } else {
    Serial.println("\nFailed to connect to WiFi!");
  }
}

void loop() {
  // Check WiFi connection periodically
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, attempting to reconnect...");
    WiFi.reconnect();
    delay(2000);
    return;
  }

  // Send data at specified interval
  unsigned long currentTime = millis();
  if (currentTime - lastSendTime < SEND_INTERVAL) {
    delay(100);
    return;
  }
  lastSendTime = currentTime;

  // Read sensor data
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature(); // Celsius
  int motion = digitalRead(PIR_PIN);
  long distance = measureDistanceCm();

  // Check for DHT read errors
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  // Prepare JSON payload
  DynamicJsonDocument doc(256);
  doc["bed_id"] = BED_ID;
  doc["temperature"] = round(temperature * 10) / 10.0;  // Round to 1 decimal
  doc["humidity"] = round(humidity * 10) / 10.0;
  doc["motion"] = motion;
  doc["distance_cm"] = distance;
  doc["esp_id"] = espId;  // REQUIRED: unique device identifier

  String payload;
  serializeJson(doc, payload);

  // Send data to server
  Serial.println("Sending: " + payload);

  WiFiClient client;
  HTTPClient http;

  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  int httpCode = http.POST(payload);

  if (httpCode > 0) {
    Serial.printf("Server response code: %d\n", httpCode);
    
    // Print response body for debugging
    if (httpCode == HTTP_CODE_OK || httpCode == HTTP_CODE_CREATED) {
      String response = http.getString();
      Serial.println("Response: " + response);
    }
  } else {
    Serial.printf("POST failed, error: %s\n", http.errorToString(httpCode).c_str());
  }

  http.end();
  client.stop();
}
