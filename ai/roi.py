"""Configurable road regions of interest for camera traffic counting."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Roi:
    road: str
    x: int
    y: int
    width: int
    height: int

    def contains(self, point_x: float, point_y: float) -> bool:
        return self.x <= point_x < self.x + self.width and self.y <= point_y < self.y + self.height

    def validate(self, frame_width: int, frame_height: int) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"ROI {self.road} must have a positive width and height")
        if self.x < 0 or self.y < 0 or self.x + self.width > frame_width or self.y + self.height > frame_height:
            raise ValueError(f"ROI {self.road} is outside the {frame_width}x{frame_height} reference frame")


def load_rois(config_path: str | Path) -> Mapping[str, Roi]:
    """Load A/B ROIs without changing counting code when camera placement changes."""
    with Path(config_path).open(encoding="utf-8") as config_file:
        config = json.load(config_file)
    reference = config["frame_reference"]
    roads = config["roads"]
    required = {"A", "B"}
    if set(roads) != required:
        raise ValueError("ROI configuration must define exactly ROAD A and ROAD B")

    rois = {
        road: Roi(road, int(raw["x"]), int(raw["y"]), int(raw["width"]), int(raw["height"]))
        for road, raw in roads.items()
    }
    for roi in rois.values():
        roi.validate(int(reference["width"]), int(reference["height"]))
    if _overlap(rois["A"], rois["B"]):
        raise ValueError("ROAD A and ROAD B ROIs must not overlap; this prevents double counting")
    return rois


def _overlap(first: Roi, second: Roi) -> bool:
    return not (
        first.x + first.width <= second.x
        or second.x + second.width <= first.x
        or first.y + first.height <= second.y
        or second.y + second.height <= first.y
    )
