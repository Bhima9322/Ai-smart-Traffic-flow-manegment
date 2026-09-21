#pragma once
#include "Arduino.h"
constexpr int WL_CONNECTED = 3;
constexpr int WIFI_STA = 1;
class WiFiClient {};
class WiFiClass {
 public:
  void mode(int) {}
  void begin(const char*, const char*) {}
  void reconnect() {}
  int status() const { return WL_CONNECTED; }
};
extern WiFiClass WiFi;
