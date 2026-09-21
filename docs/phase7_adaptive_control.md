# Phase 7: dynamic green-time transfer

`ai/adaptive_controller.py` is deliberately independent of camera, MQTT, and
ESP32 code. Give it the current active approach, A/B `ApproachInput` values
(vehicle count, `LOW`/`MEDIUM`/`HIGH` density, and waiting seconds), the
allocated green time, and actual elapsed clearance time. It returns an
immutable `AdaptiveDecision` containing the requested fields plus an explicit
safe `transition_sequence`.

Default parameters are `MIN_GREEN=10`, `NORMAL_GREEN=30`, `MAX_GREEN=60`,
`ALL_RED_TIME=2`, and `MAX_WAIT_TIME=60` seconds.

For A=4 / LOW, B=15 / HIGH, A allocated=30, and A cleared=15, the decision is:

```text
unused_time = 30 - 15 = 15
transferred_time = 15
target_signal = B
final_green_time = min(30 + 15, 60) = 45
transition_sequence = YELLOW -> ALL_RED (2 s) -> GREEN
reason = TIME_TRANSFER
```

A transfer is blocked until the actual active green reaches 10 seconds. It is
also blocked when there is no unused time or the target does not have greater
count/density demand. Transfer is capped so final green can never exceed 60.
When the waiting approach reaches 60 seconds, `MAX_WAIT_PRIORITY` safely gives
that approach the normal green at the next yellow/all-red transition, preventing
starvation. The module never represents simultaneous greens: it returns one
target and the caller must execute the transition sequence.

## Run tests

```bash
PYTHONPATH=. python -m unittest tests.ai.test_adaptive_controller
```
