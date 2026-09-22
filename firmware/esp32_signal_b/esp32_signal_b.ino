#include <WiFi.h>
#include <PubSubClient.h>
#include "../common/mqtt_config.h"
#include "../common/traffic_light_state_machine.h"

constexpr char SIGNAL[] = "B";
constexpr char SENSOR_TOPIC[] = "traffic/signalB/sensor";
constexpr char STATUS_TOPIC[] = "traffic/signalB/status";
constexpr char CONTROL_TOPIC[] = "traffic/control";
constexpr uint8_t RED = 25, YELLOW = 26, GREEN = 27, BUZZER = 14, MANUAL_BUTTON = 13;
constexpr uint8_t SENSOR_1 = 32, SENSOR_2 = 33;
constexpr uint32_t MQTT_RECONNECT_MS = 5000, STATUS_INTERVAL_MS = 2000, MQTT_FAILSAFE_MS = 15000;
const SignalTiming TIMING = {2000, 30000, 10000, 60000, 3000, 1500};
TrafficLightStateMachine controller(TIMING);
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
bool lastRawButton = HIGH, stableButton = HIGH;
uint32_t buttonChangedAtMs = 0, lastReconnectMs = 0, lastStatusMs = 0, lastMqttHealthyMs = 0;

bool commandTargetIsA(const char* payload, bool* targetA) {
  if (strstr(payload, "\"signal\":\"A\"") || strstr(payload, "\"signal\": \"A\"")) { *targetA = true; return true; }
  if (strstr(payload, "\"signal\":\"B\"") || strstr(payload, "\"signal\": \"B\"")) { *targetA = false; return true; }
  return false;
}
uint32_t greenTimeFromJson(const char* payload) {
  const char* field = strstr(payload, "\"green_time\"");
  if (!field) return TIMING.requestedGreenMs;
  const char* colon = strchr(field, ':');
  return colon ? static_cast<uint32_t>(strtoul(colon + 1, nullptr, 10) * 1000UL) : TIMING.requestedGreenMs;
}
void onMqttMessage(char* topic, byte* data, unsigned int length) {
  if (strcmp(topic, CONTROL_TOPIC) != 0 || length >= 240) return;
  char payload[240]; memcpy(payload, data, length); payload[length] = '\0';
  bool targetA = false;
  if (!commandTargetIsA(payload, &targetA) || strstr(payload, "\"state\":\"GREEN\"") == nullptr) return;
  controller.requestGreen(targetA, greenTimeFromJson(payload), millis());
  Serial.printf("MQTT priority command: Signal B GREEN for %lu ms\n", controller.activeGreenMs());
}
void writeOutputs() {
  const LocalLampState lamps = controller.lampsForB();
  digitalWrite(RED, lamps.red); digitalWrite(YELLOW, lamps.yellow); digitalWrite(GREEN, lamps.green);
  digitalWrite(BUZZER, controller.buzzerActive());
}
void publishStatus() {
  char payload[224];
  snprintf(payload, sizeof(payload), "{\"signal\":\"B\",\"phase\":%u,\"green_time\":%lu,\"sensor_1\":%s,\"sensor_2\":%s,\"fallback\":%s}",
           static_cast<unsigned>(controller.phase()), controller.activeGreenMs() / 1000UL,
           digitalRead(SENSOR_1) == LOW ? "true" : "false", digitalRead(SENSOR_2) == LOW ? "true" : "false",
           controller.isFailsafe() ? "true" : "false");
  mqtt.publish(STATUS_TOPIC, payload, true);
  mqtt.publish(SENSOR_TOPIC, payload, false);
}
void connectMqtt(uint32_t nowMs) {
  if (mqtt.connected() || nowMs - lastReconnectMs < MQTT_RECONNECT_MS) return;
  lastReconnectMs = nowMs;
  if (WiFi.status() != WL_CONNECTED) { WiFi.reconnect(); return; }
  char clientId[32]; snprintf(clientId, sizeof(clientId), "traffic-signal-B-%06X", static_cast<unsigned>(ESP.getEfuseMac()));
  const bool connected = strlen(TRAFFIC_MQTT_USERNAME) ?
      mqtt.connect(clientId, TRAFFIC_MQTT_USERNAME, TRAFFIC_MQTT_PASSWORD) : mqtt.connect(clientId);
  if (connected) { mqtt.subscribe(CONTROL_TOPIC); lastMqttHealthyMs = nowMs; Serial.println("MQTT connected"); }
  else Serial.printf("MQTT reconnect failed, rc=%d\n", mqtt.state());
}
void serviceManualButton(uint32_t nowMs) {
  const bool raw = digitalRead(MANUAL_BUTTON);
  if (raw != lastRawButton) { lastRawButton = raw; buttonChangedAtMs = nowMs; }
  if (raw != stableButton && nowMs - buttonChangedAtMs >= 40) {
    stableButton = raw; controller.setManualAllRed(stableButton == LOW, nowMs);
    Serial.println(stableButton == LOW ? "Manual ALL-RED enabled" : "Automatic mode resumed");
  }
}
void serviceSerialDebug(uint32_t nowMs) {
  while (Serial.available() > 0) {
    const char command = static_cast<char>(Serial.read());
    if (command == 'f' || command == 'F') { controller.enterFailsafe(); Serial.println("Signal B FAILSAFE ALL-RED latched"); }
    if ((command == 'r' || command == 'R') && controller.isFailsafe()) { controller.begin(nowMs); Serial.println("Signal B failsafe reset"); }
  }
}
void setup() {
  Serial.begin(115200);
  pinMode(RED, OUTPUT); pinMode(YELLOW, OUTPUT); pinMode(GREEN, OUTPUT); pinMode(BUZZER, OUTPUT);
  pinMode(MANUAL_BUTTON, INPUT_PULLUP); pinMode(SENSOR_1, INPUT); pinMode(SENSOR_2, INPUT);
  controller.begin(millis()); writeOutputs();
  WiFi.mode(WIFI_STA); WiFi.begin(TRAFFIC_WIFI_SSID, TRAFFIC_WIFI_PASSWORD);
  mqtt.setServer(TRAFFIC_MQTT_HOST, TRAFFIC_MQTT_PORT); mqtt.setCallback(onMqttMessage);
  Serial.printf("Signal B started; MQTT control topic: %s\n", CONTROL_TOPIC);
}
void loop() {
  const uint32_t nowMs = millis(); serviceManualButton(nowMs); serviceSerialDebug(nowMs); connectMqtt(nowMs);
  if (mqtt.connected()) { mqtt.loop(); lastMqttHealthyMs = nowMs; }
  else if (nowMs - lastMqttHealthyMs >= MQTT_FAILSAFE_MS) controller.enterFailsafe();
  controller.tick(nowMs); writeOutputs();
  if (mqtt.connected() && nowMs - lastStatusMs >= STATUS_INTERVAL_MS) { lastStatusMs = nowMs; publishStatus(); }
}
