# AI-Based Adaptive Traffic Signal Control

An incremental academic prototype for two ESP32 traffic signal heads with
future camera analysis and IoT coordination.

## Implemented: Phase 3 — ESP32 traffic-light firmware + MQTT

Phase 1 delivers fixed-time, non-blocking firmware for ESP32-A and ESP32-B.
It controls red/yellow/green LEDs, a yellow-phase buzzer, a debounced manual
all-red button, serial debugging, sensor presence publishing, MQTT control,
minimum/maximum green constraints, yellow and all-red clearance phases, and a
safe fallback state after an MQTT outage. It does not include AI, a website, or
a database.

See [`docs/hardware.md`](docs/hardware.md) for wiring and bench testing, and
[`docs/mqtt_protocol.md`](docs/mqtt_protocol.md) for credential configuration,
topics, payloads, reconnect behavior, and the exact Python command test.

### Host test

```bash
g++ -std=c++17 -Wall -Wextra -Werror tests/firmware/test_traffic_light_state_machine.cpp -o /tmp/traffic-light-test
/tmp/traffic-light-test

# Host syntax checks for both Arduino sketches (not a hardware upload)
tests/firmware/compile_sketches.sh
```

## Implemented: Phase 6 — configurable road-wise counting

`ai/config/rois.json` defines distinct ROAD A and ROAD B regions. The counter
filters vehicle detections, returns independent A/B counts, can draw
`A = X vehicles` / `B = Y vehicles` on an OpenCV frame, and persists results
through the SQLite repository interface. See [`docs/phase6_road_counting.md`](docs/phase6_road_counting.md).

## Implemented: Phase 7 — dynamic green-time transfer

The pure-Python adaptive controller calculates unused green time, bounded
transfer time, maximum-wait priority, and the required yellow/all-red/green
transition sequence. See [`docs/phase7_adaptive_control.md`](docs/phase7_adaptive_control.md).

## Implemented: Flask backend

The Flask application factory exposes REST APIs for status, traffic, signals,
history, events, controls, manual commands, and emergency priority. Its MQTT
adapter and SQLite persistence are documented in [`docs/backend.md`](docs/backend.md).
