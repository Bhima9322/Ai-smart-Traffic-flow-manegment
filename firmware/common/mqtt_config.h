#pragma once
#if __has_include("local_config.h")
#include "local_config.h"
#else
// Safe blank defaults allow syntax tests but deliberately prevent connectivity.
#define TRAFFIC_WIFI_SSID ""
#define TRAFFIC_WIFI_PASSWORD ""
#define TRAFFIC_MQTT_HOST ""
#define TRAFFIC_MQTT_PORT 1883
#define TRAFFIC_MQTT_USERNAME ""
#define TRAFFIC_MQTT_PASSWORD ""
#endif
