from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from backend.database import TrafficRepository
from backend.mqtt_client import TOPICS

class TrafficService:
    def __init__(self, repository: TrafficRepository) -> None: self.repository=repository
    @staticmethod
    def now() -> str: return datetime.now(timezone.utc).isoformat()
    def receive_mqtt(self, topic: str, payload: dict[str, Any]) -> None:
        timestamp=payload.get("timestamp",self.now())
        if topic in {TOPICS["sensor_a"],TOPICS["sensor_b"]}:
            signal="A" if topic==TOPICS["sensor_a"] else "B"; self.repository.save_signal_status(signal,{**payload,"source":"sensor"},timestamp)
        elif topic in {TOPICS["status_a"],TOPICS["status_b"]}:
            signal="A" if topic==TOPICS["status_a"] else "B"; self.repository.save_signal_status(signal,payload,timestamp)
    def receive_ai(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload.get("a"),int) or not isinstance(payload.get("b"),int): raise ValueError("AI payload requires integer a and b counts")
        self.repository.save_traffic({"a":payload["a"],"b":payload["b"],"timestamp":payload.get("timestamp",self.now())})
    def status(self) -> dict[str, Any]:
        signals=self.repository.latest_signal_payloads(); history=self.repository.history(50)
        return {"system":{"online":True,"mode":"AUTO"},"signals":{"A":signals.get("A",{}),"B":signals.get("B",{})},"history":{"traffic":history,"timing":[]},"events":self.repository.events(50)}
