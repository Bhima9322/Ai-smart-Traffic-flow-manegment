#pragma once
#include "WiFi.h"
class PubSubClient {
 public:
  explicit PubSubClient(WiFiClient&) {}
  void setServer(const char*, uint16_t) {}
  void setCallback(void (*)(char*, byte*, unsigned int)) {}
  bool connected() const { return false; }
  bool connect(const char*) { return false; }
  bool connect(const char*, const char*, const char*) { return false; }
  bool subscribe(const char*) { return true; }
  bool publish(const char*, const char*, bool) { return true; }
  void loop() {}
  int state() const { return 0; }
};
