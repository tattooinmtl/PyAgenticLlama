"""
Arduino/ESP32 Snippets Skill for llama.cpp
──────────────────────────────────────────
Embedded systems programming patterns for Arduino, ESP8266, and ESP32.
Covers GPIO, sensors, communication, and IoT applications.

Usage:
  execute(category="basics", type="blink")
  execute(search="wifi")
  execute(list=True)
"""

SNIPPETS_DB = {
    # ──────────────────────────────────────────────────────────────────
    # BASICS
    # ──────────────────────────────────────────────────────────────────
    "basics": {
        "blink": {
            "description": "Basic LED blink - Hello World of Arduino",
            "code": """
// Pin definitions
const int LED_PIN = 13;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  
  // Set LED pin as output
  pinMode(LED_PIN, OUTPUT);
  
  Serial.println("Arduino started");
}

void loop() {
  // Turn LED on
  digitalWrite(LED_PIN, HIGH);
  Serial.println("LED ON");
  delay(1000);  // Wait 1 second
  
  // Turn LED off
  digitalWrite(LED_PIN, LOW);
  Serial.println("LED OFF");
  delay(1000);  // Wait 1 second
}
"""
        },
        "digital_io": {
            "description": "Digital input/output operations",
            "code": """
// Pin definitions
const int BUTTON_PIN = 2;
const int LED_PIN = 13;

void setup() {
  Serial.begin(9600);
  
  // Button as input with pull-up
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
}

void loop() {
  // Read button state (LOW when pressed due to pull-up)
  int buttonState = digitalRead(BUTTON_PIN);
  
  if (buttonState == LOW) {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("Button pressed, LED on");
  } else {
    digitalWrite(LED_PIN, LOW);
    Serial.println("Button released, LED off");
  }
  
  delay(50);  // Debounce delay
}

// Debounced button reading
bool readButtonDebounced(int pin) {
  static unsigned long lastDebounceTime = 0;
  static int lastState = HIGH;
  const unsigned long debounceDelay = 50;
  
  int reading = digitalRead(pin);
  
  if (reading != lastState) {
    lastDebounceTime = millis();
  }
  
  if (millis() - lastDebounceTime > debounceDelay) {
    return reading == LOW;
  }
  
  lastState = reading;
  return false;
}
"""
        },
        "analog_io": {
            "description": "Analog input/output operations",
            "code": """
// Analog pins
const int POT_PIN = A0;      // Potentiometer
const int PWM_PIN = 3;       // PWM capable pin

void setup() {
  Serial.begin(9600);
  pinMode(PWM_PIN, OUTPUT);
}

void loop() {
  // Read analog value (0-1023)
  int sensorValue = analogRead(POT_PIN);
  
  // Convert to voltage (0-5V)
  float voltage = sensorValue * (5.0 / 1023.0);
  
  // Map to PWM value (0-255)
  int pwmValue = map(sensorValue, 0, 1023, 0, 255);
  
  // Set PWM brightness
  analogWrite(PWM_PIN, pwmValue);
  
  Serial.print("Sensor: ");
  Serial.print(sensorValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage);
  Serial.print(" | PWM: ");
  Serial.println(pwmValue);
  
  delay(100);
}

// Smoothing analog readings
const int SAMPLE_SIZE = 10;
int smoothValue(int pin) {
  long sum = 0;
  for (int i = 0; i < SAMPLE_SIZE; i++) {
    sum += analogRead(pin);
  }
  return sum / SAMPLE_SIZE;
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # SENSORS
    # ──────────────────────────────────────────────────────────────────
    "sensors": {
        "temperature_humidity": {
            "description": "DHT11/DHT22 temperature and humidity sensor",
            "code": """
#include <DHT.h>

// DHT sensor
#define DHTPIN 2
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
  Serial.println("DHT sensor initialized");
}

void loop() {
  // Read humidity and temperature
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();      // Celsius
  float temperatureF = dht.readTemperature(true);  // Fahrenheit
  
  // Check if read was successful
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Failed to read from DHT sensor!");
    delay(2000);
    return;
  }
  
  // Calculate heat index
  float heatIndex = dht.computeHeatIndex(temperature, humidity, false);
  
  // Print values
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print("% | Temp: ");
  Serial.print(temperature);
  Serial.print("C (");
  Serial.print(temperatureF);
  Serial.print("F) | Heat Index: ");
  Serial.println(heatIndex);
  
  delay(2000);
}
"""
        },
        "distance_sensor": {
            "description": "Ultrasonic distance sensor (HC-SR04)",
            "code": """
// HC-SR04 pins
const int TRIG_PIN = 9;
const int ECHO_PIN = 10;

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
}

void loop() {
  // Get distance
  long distance = measureDistance();
  
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(500);
}

long measureDistance() {
  // Clear the trigger pin
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  
  // Set trigger pin high for 10 microseconds
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // Measure pulse duration
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  
  // Calculate distance (speed of sound = 343 m/s)
  // Distance = (duration / 2) / 29.1
  long distance = duration / 58;
  
  return distance;
}

// Get multiple readings and average
long getAverageDistance(int samples = 5) {
  long sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += measureDistance();
    delay(20);
  }
  return sum / samples;
}
"""
        },
        "gas_sensor": {
            "description": "MQ-2 gas sensor (smoke, propane, methane)",
            "code": """
const int GAS_PIN = A0;
const int BUZZER_PIN = 8;

// Calibration for MQ-2
const float Ro = 10000.0;  // Sensor resistance at clean air
const float m = -0.318;     // Slope
const float b = 1.562;      // Intercept (ppm = 10^((log(Rs/Ro) - b) / m))

void setup() {
  Serial.begin(9600);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Calibrate sensor
  digitalWrite(BUZZER_PIN, LOW);
  delay(3000);
}

void loop() {
  // Read sensor
  int rawValue = analogRead(GAS_PIN);
  float voltage = rawValue * (5.0 / 1023.0);
  
  // Get PPM
  float ppm = getPPM(rawValue);
  
  Serial.print("Raw: ");
  Serial.print(rawValue);
  Serial.print(" | Voltage: ");
  Serial.print(voltage);
  Serial.print("V | PPM: ");
  Serial.println(ppm);
  
  // Alert if high gas
  if (ppm > 100) {
    digitalWrite(BUZZER_PIN, HIGH);
    Serial.println("WARNING: High gas detected!");
  } else {
    digitalWrite(BUZZER_PIN, LOW);
  }
  
  delay(1000);
}

float getPPM(int raw) {
  float voltage = raw * (5.0 / 1023.0);
  float Rs = (5.0 - voltage) / voltage * 10000;  // Calculate Rs
  float ratio = Rs / Ro;
  float ppm = pow(10, ((log(ratio) - b) / m));
  return ppm;
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # COMMUNICATION
    # ──────────────────────────────────────────────────────────────────
    "communication": {
        "serial_communication": {
            "description": "UART/Serial communication",
            "code": """
void setup() {
  Serial.begin(9600);  // Standard baud rate
  Serial.println("Serial initialized at 9600 baud");
}

void loop() {
  // Send data
  Serial.print("Hello at ");
  Serial.println(millis());
  
  // Read incoming data
  if (Serial.available()) {
    char incomingChar = Serial.read();
    
    // Echo back
    Serial.print("You sent: ");
    Serial.println(incomingChar);
  }
  
  delay(1000);
}

// Read complete line
void readSerialLine() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\\n');
    line.trim();  // Remove whitespace
    
    if (line.length() > 0) {
      Serial.print("Received: ");
      Serial.println(line);
    }
  }
}

// Parse CSV data
void parseCSV() {
  if (Serial.available()) {
    String line = Serial.readStringUntil('\\n');
    
    int index = 0;
    String values[5];
    
    int start = 0;
    for (int i = 0; i < line.length(); i++) {
      if (line.charAt(i) == ',') {
        values[index++] = line.substring(start, i);
        start = i + 1;
      }
    }
    values[index] = line.substring(start);
    
    // Use parsed values
    for (int i = 0; i <= index; i++) {
      Serial.println(values[i]);
    }
  }
}
"""
        },
        "esp32_wifi": {
            "description": "ESP32 WiFi connection and HTTP requests",
            "code": """
#include <WiFi.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// Server details
const char* serverName = "https://api.example.com/data";

void setup() {
  Serial.begin(115200);
  
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
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Failed to connect to WiFi");
  }
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    // Make HTTP GET request
    HTTPClient http;
    http.begin(serverName);
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode > 0) {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      
      String payload = http.getString();
      Serial.println("Payload: ");
      Serial.println(payload);
    } else {
      Serial.print("Error code: ");
      Serial.println(httpResponseCode);
    }
    
    http.end();
  }
  
  delay(10000);  // Request every 10 seconds
}

// HTTP POST with JSON
void sendJSONData() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin("https://api.example.com/sensor");
    
    http.addHeader("Content-Type", "application/json");
    
    // Create JSON payload
    String jsonData = "{\\\"temperature\\\":23.5,\\\"humidity\\\":45}";
    
    int httpResponseCode = http.POST(jsonData);
    
    Serial.print("POST Response: ");
    Serial.println(httpResponseCode);
    
    http.end();
  }
}
"""
        },
        "mqtt": {
            "description": "MQTT protocol for IoT messaging",
            "code": """
#include <PubSubClient.h>
#include <WiFi.h>

const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
const char* mqtt_server = "mqtt.example.com";
const int mqtt_port = 1883;
const char* mqtt_user = "username";
const char* mqtt_password = "password";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\\nWiFi connected");
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(onMqttMessage);
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  
  client.loop();  // Keep connection alive
  
  // Publish data every 10 seconds
  static unsigned long lastPublish = 0;
  if (millis() - lastPublish > 10000) {
    publishSensorData();
    lastPublish = millis();
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");
    
    if (client.connect("ESP32Client", mqtt_user, mqtt_password)) {
      Serial.println("Connected!");
      
      // Subscribe to topics
      client.subscribe("home/control/led");
      client.subscribe("home/control/buzzer");
    } else {
      Serial.print("Failed, rc=");
      Serial.println(client.state());
      delay(5000);
    }
  }
}

void publishSensorData() {
  float temp = 23.5;  // Get actual sensor data
  float humidity = 45.2;
  
  String payload = "{\\\"temp\\\":" + String(temp) + ",\\\"humidity\\\":" + String(humidity) + "}";
  
  client.publish("home/sensors/bme680", payload.c_str());
  Serial.println("Data published!");
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("]: ");
  
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Handle commands
  if (strcmp(topic, "home/control/led") == 0) {
    if (message == "on") {
      digitalWrite(LED_PIN, HIGH);
    } else if (message == "off") {
      digitalWrite(LED_PIN, LOW);
    }
  }
}
"""
        }
    },

    # ──────────────────────────────────────────────────────────────────
    # ADVANCED
    # ──────────────────────────────────────────────────────────────────
    "advanced": {
        "timers_interrupts": {
            "description": "Hardware timers and interrupts",
            "code": """
// Global variables
volatile int interruptCount = 0;
unsigned long lastInterruptTime = 0;

// Interrupt handler (must be fast!)
void IRAM_ATTR buttonInterruptHandler() {
  // Debounce: ignore if less than 50ms since last interrupt
  unsigned long currentTime = millis();
  if (currentTime - lastInterruptTime < 50) {
    return;
  }
  lastInterruptTime = currentTime;
  
  interruptCount++;
  Serial.println("Interrupt triggered!");
}

void setup() {
  Serial.begin(115200);
  
  // Attach interrupt to button
  const int BUTTON_PIN = 0;
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // FALLING: trigger when pin goes from HIGH to LOW
  // RISING: trigger when pin goes from LOW to HIGH
  // CHANGE: trigger on either
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonInterruptHandler, FALLING);
  
  Serial.println("Interrupt handler attached");
}

void loop() {
  Serial.print("Interrupt count: ");
  Serial.println(interruptCount);
  
  delay(1000);
}

// Hardware timer (ESP32)
hw_timer_t * timer = NULL;

void IRAM_ATTR onTimer() {
  Serial.println("Timer fired!");
}

void setupTimer() {
  // Timer: prescaler 80 (80MHz -> 1MHz), countdown, interrupt enabled
  timer = timerBegin(0, 80, true);
  timerAttachInterrupt(timer, &onTimer, true);
  timerAlarmWrite(timer, 1000000, true);  // 1 second
  timerAlarmEnable(timer);
}
"""
        },
        "low_power": {
            "description": "Low power modes and sleep for battery devices",
            "code": """
// ESP32 sleep modes
void setup() {
  Serial.begin(115200);
  
  // Wake up from sleep using RTC timer
  esp_sleep_enable_timer_wakeup(10 * 1000000);  // 10 seconds in microseconds
  
  // Wake up from external pin (GPIO0)
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_0, 0);
}

void loop() {
  Serial.println("Entering light sleep...");
  delay(100);
  
  // Light sleep
  esp_light_sleep_start();
  
  Serial.println("Woke up!");
  delay(1000);
  
  Serial.println("Entering deep sleep for 10 seconds...");
  delay(100);
  
  // Deep sleep (data in RTC memory is preserved)
  esp_deep_sleep_start();
  // Code after this won't execute until wake-up
}

// Store data in RTC memory (preserved during deep sleep)
RTC_DATA_ATTR int bootCount = 0;

void incrementBootCount() {
  bootCount++;
  Serial.print("Boot count: ");
  Serial.println(bootCount);
}

// Low power WiFi
void setupLowPowerWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(WIFI_PS_MAX_MODEM);  // Maximum power saving
}
"""
        },
        "sd_card": {
            "description": "SD card file operations",
            "code": """
#include <SD.h>
#include <SPI.h>

const int chipSelect = 5;  // CS pin for SPI

void setup() {
  Serial.begin(115200);
  
  // Initialize SD card
  if (!SD.begin(chipSelect)) {
    Serial.println("SD Card initialization failed!");
    return;
  }
  
  Serial.println("SD Card initialized");
  
  // List files
  listFiles("/");
}

void listFiles(const char * dirname) {
  File root = SD.open(dirname);
  
  if (!root) {
    Serial.println("Failed to open directory");
    return;
  }
  
  File file = root.openNextFile();
  while (file) {
    if (file.isDirectory()) {
      Serial.print("DIR : ");
      Serial.println(file.name());
    } else {
      Serial.print("FILE: ");
      Serial.print(file.name());
      Serial.print(" SIZE: ");
      Serial.println(file.size());
    }
    file = root.openNextFile();
  }
  file.close();
  root.close();
}

void writeToFile(const char* filename, const char* data) {
  File file = SD.open(filename, FILE_WRITE);
  
  if (!file) {
    Serial.println("Failed to open file for writing");
    return;
  }
  
  if (file.println(data)) {
    Serial.println("File written successfully");
  } else {
    Serial.println("Write failed");
  }
  
  file.close();
}

void readFromFile(const char* filename) {
  File file = SD.open(filename);
  
  if (!file) {
    Serial.println("Failed to open file for reading");
    return;
  }
  
  Serial.println("File contents:");
  while (file.available()) {
    Serial.write(file.read());
  }
  
  file.close();
}

// Log sensor data to CSV
void logSensorData(float temp, float humidity) {
  File file = SD.open("/data.csv", FILE_APPEND);
  
  if (!file) {
    file = SD.open("/data.csv", FILE_WRITE);
    file.println("timestamp,temperature,humidity");
  }
  
  // Write data
  file.print(millis());
  file.print(",");
  file.print(temp);
  file.print(",");
  file.println(humidity);
  
  file.close();
  Serial.println("Data logged to SD card");
}
"""
        }
    }
}


def execute(**kwargs):
    """
    Execute the Arduino/ESP32 snippets skill.
    
    Parameters:
      category  - Category: basics, sensors, communication, advanced
      type      - Snippet type (e.g., "blink", "temperature_humidity")
      search    - Free-text search across snippets
      list      - If True, list all available snippets
    """
    
    category = str(kwargs.get("category", "")).strip().lower()
    snippet_type = str(kwargs.get("type", "")).strip().lower()
    search_term = str(kwargs.get("search", "")).strip().lower()
    list_only = bool(kwargs.get("list", False))

    # ──────────────────────────────────────────────────────────────────
    # LIST MODE
    # ──────────────────────────────────────────────────────────────────
    if list_only:
        lines = ["Available Arduino/ESP32 Snippets:\\n"]
        for cat in SNIPPETS_DB:
            lines.append(f"\\n📂 {cat.upper()}")
            for snippet_name in SNIPPETS_DB[cat]:
                desc = SNIPPETS_DB[cat][snippet_name].get("description", "")
                lines.append(f"  • {snippet_name}: {desc}")
        return "\\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # SEARCH MODE
    # ──────────────────────────────────────────────────────────────────
    if search_term:
        lines = [f"Search results for: '{search_term}'\\n"]
        found = False
        
        for cat in SNIPPETS_DB:
            for snippet_name in SNIPPETS_DB[cat]:
                snippet = SNIPPETS_DB[cat][snippet_name]
                desc = snippet.get("description", "").lower()
                
                if search_term in desc or search_term in snippet_name.lower():
                    found = True
                    lines.append(f"\\n[{cat}] {snippet_name}")
                    lines.append(f"  {snippet.get('description', '')}")
        
        if not found:
            return f"No snippets found matching '{search_term}'"
        
        return "\\n".join(lines)

    # ──────────────────────────────────────────────────────────────────
    # RETRIEVE SPECIFIC SNIPPET
    # ──────────────────────────────────────────────────────────────────
    if not category or not snippet_type:
        return "Error: Both 'category' and 'type' required. Use list=True to see options."

    if category not in SNIPPETS_DB:
        return f"Error: Category '{category}' not found."

    if snippet_type not in SNIPPETS_DB[category]:
        return f"Error: Type '{snippet_type}' not found in '{category}'."

    snippet = SNIPPETS_DB[category][snippet_type]

    # ──────────────────────────────────────────────────────────────────
    # FORMAT OUTPUT
    # ──────────────────────────────────────────────────────────────────
    output = []
    output.append(f"📍 [{category}] {snippet_type}")
    output.append(f"   {snippet.get('description', '')}\\n")
    output.append("──── ARDUINO CODE ────\\n")
    output.append(snippet.get("code", ""))

    return "\\n".join(output)
