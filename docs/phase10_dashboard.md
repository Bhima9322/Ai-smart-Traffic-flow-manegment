# Phase 10 dashboard

Open `frontend/index.html` through the same origin as the backend (or define
`window.TRAFFIC_API_URL` before loading `js/dashboard.js`). The dashboard fetches
`GET /api/status` every five seconds. It intentionally has no hard-coded traffic
or transfer values: unavailable data is rendered as `—` and a failed request as
`Backend unavailable`.

## Required response contract

```json
{
  "system": {"online": true, "mode": "AUTO", "camera": {"mode": "local", "stream_url": "/api/camera/stream"}},
  "signals": {"A": {"state": "GREEN", "vehicle_count": 4, "density": "LOW", "green_time": 30, "remaining_time": 15, "waiting_time": 0, "actual_clearance_time": 15, "unused_green_time": 15}, "B": {"state": "RED", "vehicle_count": 15, "density": "HIGH", "green_time": 45, "remaining_time": 45, "waiting_time": 30, "actual_clearance_time": null, "transferred_time": 15}},
  "transfer": {"from": "A", "to": "B", "seconds": 15, "reason": "TIME_TRANSFER"},
  "emergency": {"active": false, "direction": null}, "incident": {"active": false},
  "history": {"traffic": [{"timestamp": "2026-01-01T12:00:00Z", "a": 4, "b": 15}], "timing": [{"timestamp": "2026-01-01T12:00:00Z", "a_green": 30, "b_green": 45}]},
  "events": [{"timestamp": "2026-01-01T12:00:00Z", "message": "Transfer decision published"}]
}
```

The JSON above is a **contract example only**, not an embedded dashboard data
source. The camera URL must be reachable by the browser. A deployed web page
cannot access a developer laptop USB camera; supply a server/IP-camera stream.
