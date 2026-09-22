#pragma once

#include <stdint.h>

// One intersection-wide phase is projected to each ESP32's local signal head.
enum class IntersectionPhase : uint8_t {
  STARTUP_ALL_RED,
  A_GREEN,
  A_YELLOW,
  TRANSITION_ALL_RED_TO_B,
  B_GREEN,
  B_YELLOW,
  TRANSITION_ALL_RED_TO_A,
  MANUAL_ALL_RED,
  FAILSAFE_ALL_RED,
};

struct SignalTiming {
  uint32_t startupAllRedMs;
  uint32_t requestedGreenMs;
  uint32_t minimumGreenMs;
  uint32_t maximumGreenMs;
  uint32_t yellowMs;
  uint32_t allRedMs;
};

struct LocalLampState {
  bool red;
  bool yellow;
  bool green;
};

/**
 * Non-blocking, fixed-time Phase 1 controller. It models the whole conflict
 * area so green can only be assigned to one approach in any valid phase.
 */
class TrafficLightStateMachine {
 public:
  explicit TrafficLightStateMachine(const SignalTiming& timing)
      : timing_(sanitize(timing)), activeGreenMs_(clampGreen(timing_.requestedGreenMs)) {}

  void begin(uint32_t nowMs) {
    phase_ = IntersectionPhase::STARTUP_ALL_RED;
    phaseStartedAtMs_ = nowMs;
    manualAllRed_ = false;
    failsafe_ = false;
  }

  void tick(uint32_t nowMs) {
    if (failsafe_) {
      phase_ = IntersectionPhase::FAILSAFE_ALL_RED;
      return;
    }
    if (manualAllRed_) {
      phase_ = IntersectionPhase::MANUAL_ALL_RED;
      return;
    }
    if (elapsed(nowMs) >= phaseDurationMs()) {
      phase_ = nextPhase(phase_);
      phaseStartedAtMs_ = nowMs;
    }
  }

  // Phase 1 deliberately provides only a safe local manual action: all-red.
  // Releasing it restarts with an all-red clearance period before auto timing.
  void setManualAllRed(bool enabled, uint32_t nowMs) {
    if (failsafe_ || enabled == manualAllRed_) return;
    manualAllRed_ = enabled;
    phase_ = enabled ? IntersectionPhase::MANUAL_ALL_RED : IntersectionPhase::STARTUP_ALL_RED;
    phaseStartedAtMs_ = nowMs;
  }

  // Request a coordinated external command. A conflicting green is first
  // terminated through yellow and an all-red clearance interval.
  void requestGreen(bool approachA, uint32_t requestedMs, uint32_t nowMs) {
    if (failsafe_ || manualAllRed_) return;
    activeGreenMs_ = clampGreen(requestedMs);
    if (approachA) {
      if (phase_ == IntersectionPhase::A_GREEN) { phaseStartedAtMs_ = nowMs; return; }
      if (phase_ == IntersectionPhase::A_YELLOW) return;
      if (phase_ == IntersectionPhase::B_GREEN) { phase_ = IntersectionPhase::B_YELLOW; phaseStartedAtMs_ = nowMs; return; }
      if (phase_ == IntersectionPhase::B_YELLOW) return;
      phase_ = IntersectionPhase::TRANSITION_ALL_RED_TO_A;
    } else {
      if (phase_ == IntersectionPhase::B_GREEN) { phaseStartedAtMs_ = nowMs; return; }
      if (phase_ == IntersectionPhase::B_YELLOW) return;
      if (phase_ == IntersectionPhase::A_GREEN) { phase_ = IntersectionPhase::A_YELLOW; phaseStartedAtMs_ = nowMs; return; }
      if (phase_ == IntersectionPhase::A_YELLOW) return;
      phase_ = IntersectionPhase::TRANSITION_ALL_RED_TO_B;
    }
    phaseStartedAtMs_ = nowMs;
  }

  void enterFailsafe() {
    failsafe_ = true;
    manualAllRed_ = false;
    phase_ = IntersectionPhase::FAILSAFE_ALL_RED;
  }

  IntersectionPhase phase() const { return phase_; }
  uint32_t activeGreenMs() const { return activeGreenMs_; }
  bool isFailsafe() const { return failsafe_; }
  bool isManualAllRed() const { return manualAllRed_; }
  bool buzzerActive() const {
    return phase_ == IntersectionPhase::A_YELLOW || phase_ == IntersectionPhase::B_YELLOW;
  }

  LocalLampState lampsForA() const { return lampsFor(true); }
  LocalLampState lampsForB() const { return lampsFor(false); }

 private:
  SignalTiming timing_;
  uint32_t activeGreenMs_;
  IntersectionPhase phase_ = IntersectionPhase::STARTUP_ALL_RED;
  uint32_t phaseStartedAtMs_ = 0;
  bool manualAllRed_ = false;
  bool failsafe_ = false;

  static SignalTiming sanitize(SignalTiming value) {
    if (value.minimumGreenMs == 0) value.minimumGreenMs = 1000;
    if (value.maximumGreenMs < value.minimumGreenMs) value.maximumGreenMs = value.minimumGreenMs;
    if (value.yellowMs == 0) value.yellowMs = 1000;
    if (value.allRedMs == 0) value.allRedMs = 1000;
    return value;
  }

  uint32_t clampGreen(uint32_t requestedMs) const {
    if (requestedMs < timing_.minimumGreenMs) return timing_.minimumGreenMs;
    if (requestedMs > timing_.maximumGreenMs) return timing_.maximumGreenMs;
    return requestedMs;
  }

  uint32_t elapsed(uint32_t nowMs) const { return nowMs - phaseStartedAtMs_; }

  uint32_t phaseDurationMs() const {
    switch (phase_) {
      case IntersectionPhase::STARTUP_ALL_RED: return timing_.startupAllRedMs;
      case IntersectionPhase::A_GREEN:
      case IntersectionPhase::B_GREEN: return activeGreenMs_;
      case IntersectionPhase::A_YELLOW:
      case IntersectionPhase::B_YELLOW: return timing_.yellowMs;
      case IntersectionPhase::TRANSITION_ALL_RED_TO_B:
      case IntersectionPhase::TRANSITION_ALL_RED_TO_A: return timing_.allRedMs;
      case IntersectionPhase::MANUAL_ALL_RED:
      case IntersectionPhase::FAILSAFE_ALL_RED: return UINT32_MAX;
    }
    return UINT32_MAX;
  }

  static IntersectionPhase nextPhase(IntersectionPhase current) {
    switch (current) {
      case IntersectionPhase::STARTUP_ALL_RED: return IntersectionPhase::A_GREEN;
      case IntersectionPhase::A_GREEN: return IntersectionPhase::A_YELLOW;
      case IntersectionPhase::A_YELLOW: return IntersectionPhase::TRANSITION_ALL_RED_TO_B;
      case IntersectionPhase::TRANSITION_ALL_RED_TO_B: return IntersectionPhase::B_GREEN;
      case IntersectionPhase::B_GREEN: return IntersectionPhase::B_YELLOW;
      case IntersectionPhase::B_YELLOW: return IntersectionPhase::TRANSITION_ALL_RED_TO_A;
      case IntersectionPhase::TRANSITION_ALL_RED_TO_A: return IntersectionPhase::A_GREEN;
      case IntersectionPhase::MANUAL_ALL_RED:
      case IntersectionPhase::FAILSAFE_ALL_RED: return current;
    }
    return IntersectionPhase::FAILSAFE_ALL_RED;
  }

  LocalLampState lampsFor(bool approachA) const {
    const bool green = (approachA && phase_ == IntersectionPhase::A_GREEN) ||
                       (!approachA && phase_ == IntersectionPhase::B_GREEN);
    const bool yellow = (approachA && phase_ == IntersectionPhase::A_YELLOW) ||
                        (!approachA && phase_ == IntersectionPhase::B_YELLOW);
    return {!green && !yellow, yellow, green};
  }
};
