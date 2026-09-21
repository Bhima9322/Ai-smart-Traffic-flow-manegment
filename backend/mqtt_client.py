"""MQTT adapter; services consume this interface instead of paho directly."""
from __future__ import annotations
import json
from typing import Callable
from backend.config import Settings

TOPICS = {"sensor_a":"traffic/signalA/sensor", "sensor_b":"traffic/signalB/sensor", "status_a":"traffic/signalA/status", "status_b":"traffic/signalB/status", "control":"traffic/control", "emergency":"traffic/emergency"}

class MqttGateway:
    def __init__(self, settings: Settings) -> None:
        self._handlers: list[Callable[[str, dict], None]] = []; self._client = None; self._settings=settings
    def register_handler(self, handler: Callable[[str, dict], None]) -> None: self._handlers.append(handler)
    def start(self) -> None:
        if not self._settings.mqtt_enabled or not self._settings.mqtt_host: return
        import paho.mqtt.client as mqtt
        self._client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="traffic-backend")
        if self._settings.mqtt_username: self._client.username_pw_set(self._settings.mqtt_username,self._settings.mqtt_password)
        self._client.on_connect=lambda client, userdata, flags, reason_code, properties: [client.subscribe(topic) for topic in (TOPICS["sensor_a"],TOPICS["sensor_b"],TOPICS["status_a"],TOPICS["status_b"])]
        def on_message(client, userdata, message):
            try: payload=json.loads(message.payload.decode("utf-8"))
            except (UnicodeDecodeError,json.JSONDecodeError): return
            for handler in self._handlers: handler(message.topic,payload)
        self._client.on_message=on_message; self._client.connect_async(self._settings.mqtt_host,self._settings.mqtt_port); self._client.loop_start()
    def publish(self, topic: str, payload: dict, retain: bool=False) -> None:
        if not self._client: return
        self._client.publish(topic,json.dumps(payload),retain=retain)
    def stop(self) -> None:
        if self._client: self._client.loop_stop(); self._client.disconnect()
