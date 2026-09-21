from __future__ import annotations
from typing import Any
from backend.database import TrafficRepository
from backend.mqtt_client import MqttGateway, TOPICS
from backend.services.traffic_service import TrafficService

class ControlService:
    def __init__(self, repository: TrafficRepository, mqtt: MqttGateway, clock=TrafficService.now) -> None: self.repository,self.mqtt,self.clock=repository,mqtt,clock
    def control(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("signal") not in {"A","B"} or payload.get("state") not in {"GREEN","ALL_RED"}: raise ValueError("signal must be A/B and state must be GREEN/ALL_RED")
        if payload["state"]=="GREEN" and not isinstance(payload.get("green_time"),int): raise ValueError("GREEN control requires integer green_time")
        command={k:payload[k] for k in ("signal","state","green_time","reason") if k in payload}; command["source"]="backend"
        self.mqtt.publish(TOPICS["control"],command); self.repository.add_event("signal_events",self.clock(),command,"CONTROL"); return command
    def manual(self, payload: dict[str, Any]) -> dict[str, Any]:
        command=self.control({"signal":payload.get("signal"),"state":payload.get("state"),"green_time":payload.get("green_time"),"reason":"MANUAL"})
        return command
    def emergency(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("direction") not in {"A","B"} or not isinstance(payload.get("active"),bool): raise ValueError("emergency requires direction A/B and boolean active")
        command={"direction":payload["direction"],"active":payload["active"],"priority_duration":payload.get("priority_duration",30),"source":"backend"}
        self.mqtt.publish(TOPICS["emergency"],command); self.repository.add_event("emergency_events",self.clock(),command); return command
