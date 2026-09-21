# Phase 3 MQTT protocol

## Configuration

Copy `firmware/common/local_config.example.h` to
`firmware/common/local_config.h` and set the Wi-Fi and MQTT values before
uploading. `local_config.h` is Git-ignored and must never be committed. The
firmware remains offline and logs reconnect attempts if its Wi-Fi/MQTT values
are blank or invalid.

Install the Arduino libraries **PubSubClient** and **WiFi** (bundled with the
ESP32 Arduino core) before uploading.

## Topics

| Topic | Publisher | Subscriber | Purpose |
| --- | --- | --- | --- |
| `traffic/signalA/sensor` | ESP32-A | backend/monitor | IR presence values for A |
| `traffic/signalB/sensor` | ESP32-B | backend/monitor | IR presence values for B |
| `traffic/signalA/status` | ESP32-A | backend/monitor | retained A signal status |
| `traffic/signalB/status` | ESP32-B | backend/monitor | retained B signal status |
| `traffic/control` | Python/backend | both ESP32s | command a safe requested green phase |
| `traffic/emergency` | reserved | reserved | not implemented in Phase 3 |
| `traffic/system` | reserved | reserved | not implemented in Phase 3 |

Sensor and status payloads are JSON and publish every two seconds while MQTT
is connected. `sensor_1` and `sensor_2` are `true` when a normally-HIGH,
active-LOW presence sensor is asserted.

```json
{
  "signal": "B",
  "phase": 4,
  "green_time": 45,
  "sensor_1": true,
  "sensor_2": false,
  "fallback": false
}
```

## Control command: make Signal B green for 45 seconds

Publish this JSON to `traffic/control`:

```json
{"signal":"B","state":"GREEN","green_time":45,"reason":"MANUAL_TEST"}
```

Both boards must be online because each uses the same intersection phase model.
A conflicting A-green request is first sent through A yellow and the all-red
clearance interval; a command from all-red waits through the all-red interval.
The 45-second value is clamped by the firmware's 10–60 second safety bounds.

Example Python publisher (run where `paho-mqtt` is installed):

```python
import json
import os
import paho.mqtt.publish as publish

publish.single(
    "traffic/control",
    payload=json.dumps({"signal": "B", "state": "GREEN", "green_time": 45,
                        "reason": "MANUAL_TEST"}),
    hostname=os.environ["MQTT_HOST"],
    port=int(os.getenv("MQTT_PORT", "1883")),
    auth={"username": os.getenv("MQTT_USERNAME", ""),
          "password": os.getenv("MQTT_PASSWORD", "")},
)
```

## Reconnect and fallback

Each ESP32 reconnects to Wi-Fi/MQTT every five seconds. It subscribes to
`traffic/control` after every successful MQTT connection. If no healthy MQTT
connection exists for 15 seconds, its signal state machine latches
`FAILSAFE_ALL_RED`. Restart the ESP32 after restoring connectivity. This is a
low-voltage laboratory safety fallback, not a road-certified interlock.
