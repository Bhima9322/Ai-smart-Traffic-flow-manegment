# Flask backend

Run after installing dependencies:

```bash
python -m pip install -r requirements.txt
PYTHONPATH=. python -m backend.app
```

Configuration is environment-only; copy `.env.example` into your deployment
configuration. `MqttGateway` subscribes to ESP32 sensor/status topics and
passes parsed JSON to `TrafficService`. Services store it in SQLite; Flask
routes only delegate to services. Replace `TrafficRepository` with a MySQL or
Firebase implementation that preserves its methods to change persistence later.

## API

- `GET /api/status`, `/api/traffic`, `/api/signals`, `/api/history`, `/api/events`
- `POST /api/traffic` accepts AI `{ "a": 4, "b": 15, "timestamp": "..." }`
- `POST /api/control` accepts `{ "signal":"B", "state":"GREEN", "green_time":45, "reason":"TIME_TRANSFER" }`
- `POST /api/manual` accepts the same signal/state/green-time fields and records `MANUAL`.
- `POST /api/emergency` accepts `{ "direction":"B", "active":true, "priority_duration":30 }`.

Control publishes to `traffic/control`; emergency publishes to
`traffic/emergency`. MQTT host/user/password come only from environment.
