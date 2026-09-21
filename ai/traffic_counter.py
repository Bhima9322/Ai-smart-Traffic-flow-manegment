"""Road-wise vehicle counting from detections supplied by any detector backend."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping

from ai.roi import Roi

VEHICLE_CLASSES = frozenset({"car", "bus", "truck", "motorcycle"})


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def bottom_center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, self.y2)


@dataclass(frozen=True)
class TrafficResult:
    observed_at: datetime
    road_a_count: int
    road_b_count: int
    accepted_detections: tuple[Detection, ...]


class RoadTrafficCounter:
    """Counts only supported vehicles whose bottom-centre lies in a road ROI."""

    def __init__(self, rois: Mapping[str, Roi], confidence_threshold: float = 0.50) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1")
        if set(rois) != {"A", "B"}:
            raise ValueError("A and B ROIs are required")
        self._rois = rois
        self._confidence_threshold = confidence_threshold

    def count(self, detections: Iterable[Detection], observed_at: datetime | None = None) -> TrafficResult:
        counts = {"A": 0, "B": 0}
        accepted: list[Detection] = []
        for detection in detections:
            if detection.label.lower() not in VEHICLE_CLASSES or detection.confidence < self._confidence_threshold:
                continue
            point_x, point_y = detection.bottom_center
            for road, roi in self._rois.items():
                if roi.contains(point_x, point_y):
                    counts[road] += 1
                    accepted.append(detection)
                    break
        return TrafficResult(
            observed_at=observed_at or datetime.now(timezone.utc),
            road_a_count=counts["A"],
            road_b_count=counts["B"],
            accepted_detections=tuple(accepted),
        )

    def draw_overlay(self, frame, result: TrafficResult):
        """Draw ROIs and live A/B counts; requires an OpenCV-compatible cv2 module."""
        import cv2

        for road, roi in self._rois.items():
            color = (0, 180, 0) if road == "A" else (0, 140, 255)
            cv2.rectangle(frame, (roi.x, roi.y), (roi.x + roi.width, roi.y + roi.height), color, 2)
        for detection in result.accepted_detections:
            cv2.rectangle(frame, (int(detection.x1), int(detection.y1)), (int(detection.x2), int(detection.y2)), (255, 255, 0), 2)
            cv2.putText(frame, f"{detection.label} {detection.confidence:.2f}", (int(detection.x1), int(detection.y1) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(frame, f"A = {result.road_a_count} vehicles", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 180, 0), 2)
        cv2.putText(frame, f"B = {result.road_b_count} vehicles", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 140, 255), 2)
        return frame
