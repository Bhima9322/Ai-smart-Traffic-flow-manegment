import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from ai.roi import load_rois
from ai.traffic_counter import Detection, RoadTrafficCounter
from backend.database import TrafficRepository

ROOT = Path(__file__).resolve().parents[2]


class RoadTrafficCounterTests(unittest.TestCase):
    def setUp(self):
        self.counter = RoadTrafficCounter(load_rois(ROOT / "ai/config/rois.json"), confidence_threshold=0.5)

    def test_counts_each_road_independently(self):
        result = self.counter.count([
            Detection("car", 0.9, 100, 350, 200, 500),
            Detection("motorcycle", 0.8, 250, 360, 300, 490),
            Detection("bus", 0.95, 800, 300, 980, 500),
            Detection("person", 0.99, 800, 300, 850, 500),
            Detection("truck", 0.2, 900, 300, 1100, 500),
        ])
        self.assertEqual(result.road_a_count, 2)
        self.assertEqual(result.road_b_count, 1)

    def test_rejects_overlapping_rois(self):
        config = {"frame_reference": {"width": 100, "height": 100}, "roads": {
            "A": {"x": 0, "y": 0, "width": 60, "height": 60},
            "B": {"x": 50, "y": 0, "width": 50, "height": 50},
        }}
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "rois.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_rois(config_path)

    def test_persists_roadwise_camera_result(self):
        result = self.counter.count([], observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc))
        with tempfile.TemporaryDirectory() as directory:
            repository = TrafficRepository(Path(directory) / "traffic.db")
            repository.initialize()
            repository.save_camera_result(result)
            import sqlite3
            with sqlite3.connect(Path(directory) / "traffic.db") as connection:
                row = connection.execute("SELECT road_a_count, road_b_count, source FROM traffic_data").fetchone()
        self.assertEqual(row, (0, 0, "camera"))


if __name__ == "__main__":
    unittest.main()
