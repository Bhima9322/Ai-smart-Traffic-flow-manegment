"""SQLite repository implementing the backend persistence abstraction."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from ai.traffic_counter import TrafficResult


class TrafficRepository:
    def __init__(self, database_path: str | Path) -> None: self._database_path = str(database_path)
    def _connect(self):
        connection = sqlite3.connect(self._database_path); connection.row_factory = sqlite3.Row; return connection
    def initialize(self) -> None:
        with self._connect() as c:
            c.executescript("""CREATE TABLE IF NOT EXISTS traffic_data (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, road_a_count INTEGER NOT NULL CHECK(road_a_count>=0), road_b_count INTEGER NOT NULL CHECK(road_b_count>=0), source TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS signal_status (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, signal TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS signal_events (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, event_type TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS emergency_events (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, direction TEXT, active INTEGER NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS incident_events (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS system_logs (id INTEGER PRIMARY KEY, observed_at TEXT NOT NULL, level TEXT NOT NULL, message TEXT NOT NULL);""")
    def save_camera_result(self, result: TrafficResult, source: str = "camera") -> None:
        if source not in {"camera", "sample", "ai"}: raise ValueError("source must be camera, ai, or sample")
        self.save_traffic({"a": result.road_a_count, "b": result.road_b_count, "timestamp": result.observed_at.isoformat()}, source)
    def save_traffic(self, payload: dict[str, Any], source: str = "ai") -> None:
        with self._connect() as c: c.execute("INSERT INTO traffic_data(observed_at,road_a_count,road_b_count,source) VALUES(?,?,?,?)", (payload["timestamp"], int(payload["a"]), int(payload["b"]), source))
    def save_signal_status(self, signal: str, payload: dict[str, Any], timestamp: str) -> None:
        with self._connect() as c: c.execute("INSERT INTO signal_status(observed_at,signal,payload) VALUES(?,?,?)", (timestamp, signal, json.dumps(payload)))
    def add_event(self, table: str, timestamp: str, payload: dict[str, Any], event_type: str = "EVENT") -> None:
        if table == "signal_events": columns, values = "observed_at,event_type,payload", (timestamp,event_type,json.dumps(payload))
        elif table == "emergency_events": columns, values = "observed_at,direction,active,payload", (timestamp,payload.get("direction"),int(bool(payload.get("active"))),json.dumps(payload))
        elif table == "incident_events": columns, values = "observed_at,payload", (timestamp,json.dumps(payload))
        else: raise ValueError("unsupported event table")
        with self._connect() as c: c.execute(f"INSERT INTO {table}({columns}) VALUES({','.join('?' for _ in values)})", values)
    def latest_signal_payloads(self) -> dict[str, dict[str, Any]]:
        with self._connect() as c: rows=c.execute("SELECT signal,payload FROM signal_status WHERE id IN (SELECT MAX(id) FROM signal_status GROUP BY signal)").fetchall()
        return {r["signal"]: json.loads(r["payload"]) for r in rows}
    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as c: rows=c.execute("SELECT observed_at,road_a_count,road_b_count FROM traffic_data ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [{"timestamp":r["observed_at"],"a":r["road_a_count"],"b":r["road_b_count"]} for r in reversed(rows)]
    def events(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as c: rows=c.execute("SELECT observed_at,event_type,payload FROM signal_events ORDER BY id DESC LIMIT ?",(limit,)).fetchall()
        return [{"timestamp":r["observed_at"],"type":r["event_type"],**json.loads(r["payload"])} for r in rows]
