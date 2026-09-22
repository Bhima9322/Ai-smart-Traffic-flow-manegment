"""Explicit, deterministic demonstration data writer; never runs automatically."""
from datetime import datetime, timezone
from pathlib import Path

from ai.roi import load_rois
from ai.traffic_counter import Detection, RoadTrafficCounter
from backend.database import TrafficRepository

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    counter = RoadTrafficCounter(load_rois(root / "ai/config/rois.json"))
    # This is labelled sample in SQLite and is not used by live camera operation.
    result = counter.count([
        Detection("car", 0.95, 100, 400, 180, 500),
        Detection("bus", 0.90, 760, 350, 930, 520),
        Detection("truck", 0.92, 980, 350, 1160, 530),
    ], observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
    repository = TrafficRepository(root / "traffic.db")
    repository.initialize()
    repository.save_camera_result(result, source="sample")
    print(f"Saved explicit sample: A = {result.road_a_count} vehicles; B = {result.road_b_count} vehicles")
