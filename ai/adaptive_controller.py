"""Safety-constrained dynamic green-time transfer for a two-approach junction."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class Density(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class ControllerParameters:
    min_green: int = 10
    normal_green: int = 30
    max_green: int = 60
    all_red_time: int = 2
    max_wait_time: int = 60

    def __post_init__(self) -> None:
        if not 0 < self.min_green <= self.normal_green <= self.max_green:
            raise ValueError("green timings must satisfy 0 < min <= normal <= max")
        if self.all_red_time <= 0 or self.max_wait_time <= 0:
            raise ValueError("all_red_time and max_wait_time must be positive")


@dataclass(frozen=True)
class ApproachInput:
    vehicle_count: int
    density: Density
    waiting_time: int

    def __post_init__(self) -> None:
        if self.vehicle_count < 0 or self.waiting_time < 0:
            raise ValueError("vehicle_count and waiting_time must not be negative")


@dataclass(frozen=True)
class AdaptiveDecision:
    active_signal: str
    previous_signal: str
    allocated_time: int
    actual_clearance_time: int
    unused_time: int
    transferred_time: int
    target_signal: str | None
    final_green_time: int
    reason: str
    transition_sequence: tuple[str, ...]
    all_red_time: int


class AdaptiveTrafficController:
    """Makes a timing decision only; hardware executes its returned safe sequence."""

    def __init__(self, parameters: ControllerParameters | None = None) -> None:
        self.parameters = parameters or ControllerParameters()

    def decide(
        self,
        *,
        active_signal: str,
        traffic: Mapping[str, ApproachInput],
        allocated_green_time: int,
        actual_clearance_time: int,
    ) -> AdaptiveDecision:
        """Evaluate an early-clearance transfer without ever commanding two greens.

        `actual_clearance_time` is elapsed green time, not an estimate. A
        transfer can only begin after `min_green`; callers must execute the
        returned YELLOW -> ALL_RED -> GREEN sequence before target green.
        """
        self._validate(active_signal, traffic, allocated_green_time, actual_clearance_time)
        other = "B" if active_signal == "A" else "A"
        active = traffic[active_signal]
        target = traffic[other]
        base = dict(
            active_signal=active_signal,
            previous_signal=active_signal,
            allocated_time=allocated_green_time,
            actual_clearance_time=actual_clearance_time,
            all_red_time=self.parameters.all_red_time,
        )

        if actual_clearance_time < self.parameters.min_green:
            return AdaptiveDecision(**base, unused_time=0, transferred_time=0, target_signal=None,
                                    final_green_time=allocated_green_time, reason="MINIMUM_GREEN_NOT_MET",
                                    transition_sequence=())

        # The waiting approach must receive its normal green at the next safe
        # phase even if no early-clearance transfer is justified.
        if target.waiting_time >= self.parameters.max_wait_time:
            return self._switch(**base, unused_time=0, transferred_time=0, target_signal=other,
                                final_green_time=self.parameters.normal_green,
                                reason="MAX_WAIT_PRIORITY")

        unused = max(0, allocated_green_time - actual_clearance_time)
        if unused == 0:
            return AdaptiveDecision(**base, unused_time=0, transferred_time=0, target_signal=None,
                                    final_green_time=allocated_green_time, reason="NO_UNUSED_GREEN_TIME",
                                    transition_sequence=())
        if not self._has_higher_demand(target, active):
            return AdaptiveDecision(**base, unused_time=unused, transferred_time=0, target_signal=None,
                                    final_green_time=allocated_green_time, reason="NO_HIGHER_OPPOSITE_DEMAND",
                                    transition_sequence=())

        transfer = min(unused, self.parameters.max_green - self.parameters.normal_green)
        return self._switch(**base, unused_time=unused, transferred_time=transfer, target_signal=other,
                            final_green_time=self.parameters.normal_green + transfer,
                            reason="TIME_TRANSFER")

    def _switch(self, **values) -> AdaptiveDecision:
        return AdaptiveDecision(**values, transition_sequence=("YELLOW", "ALL_RED", "GREEN"))

    @staticmethod
    def _has_higher_demand(candidate: ApproachInput, active: ApproachInput) -> bool:
        rank = {Density.LOW: 0, Density.MEDIUM: 1, Density.HIGH: 2}
        return (candidate.vehicle_count, rank[candidate.density]) > (active.vehicle_count, rank[active.density])

    def _validate(self, active_signal: str, traffic: Mapping[str, ApproachInput], allocated: int, clearance: int) -> None:
        if active_signal not in {"A", "B"} or set(traffic) != {"A", "B"}:
            raise ValueError("exactly one active signal and A/B traffic inputs are required")
        if not self.parameters.min_green <= allocated <= self.parameters.max_green:
            raise ValueError("allocated_green_time must be within configured min/max green bounds")
        if clearance < 0 or clearance > allocated:
            raise ValueError("actual_clearance_time must be between zero and allocated_green_time")
