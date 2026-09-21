# Phase 6: configurable ROAD A / ROAD B counting

`ai/config/rois.json` is the sole location for camera ROI coordinates. It uses
pixels relative to the declared `frame_reference` size. Update the rectangles
there after mounting/repositioning the camera; do not modify the counter code.
The loader rejects missing, out-of-bounds, or overlapping A/B areas so a
vehicle cannot be counted twice.

`RoadTrafficCounter` accepts detector results through its `Detection` type,
filters to car/bus/truck/motorcycle and the configured confidence threshold,
and assigns each accepted detection by its bottom-centre point. It returns
separate `road_a_count` and `road_b_count`, never only a total. Its optional
OpenCV overlay draws both ROIs, accepted boxes, and exactly these labels:
`A = X vehicles` and `B = Y vehicles`.

Phase 6 does not claim a YOLO model is implemented. A later detection adapter
must transform genuine model output into `Detection` objects, then call
`counter.count()` once per camera frame and save the result through
`TrafficRepository.save_camera_result(result)`.

## Database interface

`backend/database.py` provides the SQLite `traffic_data` table and
`save_camera_result`. It records the timestamp, Road A count, Road B count, and
source. Run this explicit demonstration command to verify the persistence path:

```bash
PYTHONPATH=. python backend/save_sample_traffic_results.py
sqlite3 traffic.db 'SELECT observed_at, road_a_count, road_b_count, source FROM traffic_data;'
```

The demonstration is deterministic and writes `source = sample`; it is never
run by the application and does not pretend to be live camera data.

## Tests

```bash
PYTHONPATH=. python -m unittest tests.ai.test_traffic_counter
```
