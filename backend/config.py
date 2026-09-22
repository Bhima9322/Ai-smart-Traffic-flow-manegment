"""Environment-based backend configuration; credentials are never committed."""
from dataclasses import dataclass
import os


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("DATABASE_PATH", "traffic.db")
    mqtt_host: str = os.getenv("MQTT_HOST", "")
    mqtt_port: int = int(os.getenv("MQTT_PORT", "1883"))
    mqtt_username: str = os.getenv("MQTT_USERNAME", "")
    mqtt_password: str = os.getenv("MQTT_PASSWORD", "")
    mqtt_enabled: bool = _as_bool(os.getenv("MQTT_ENABLED", "true"))
    simulation_mode: bool = _as_bool(os.getenv("SIMULATION_MODE", "false"))
