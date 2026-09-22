#include <cassert>
#include <iostream>

#include "../../firmware/common/traffic_light_state_machine.h"

static void assertNoConflict(const TrafficLightStateMachine& controller) {
  const LocalLampState a = controller.lampsForA();
  const LocalLampState b = controller.lampsForB();
  assert(!(a.green && b.green));
  assert(!(a.green && a.yellow));
  assert(!(b.green && b.yellow));
}

int main() {
  const SignalTiming timing = {100, 800, 1000, 2000, 200, 300};
  TrafficLightStateMachine controller(timing);
  controller.begin(0);

  // Requested 800 ms is clamped to the 1000 ms minimum green time.
  assert(controller.activeGreenMs() == 1000);
  assert(controller.lampsForA().red && controller.lampsForB().red);
  assertNoConflict(controller);

  controller.tick(100);
  assert(controller.phase() == IntersectionPhase::A_GREEN);
  controller.tick(1099);
  assert(controller.phase() == IntersectionPhase::A_GREEN);
  controller.tick(1100);
  assert(controller.phase() == IntersectionPhase::A_YELLOW);
  assert(controller.buzzerActive());
  assertNoConflict(controller);

  controller.tick(1300);
  assert(controller.phase() == IntersectionPhase::TRANSITION_ALL_RED_TO_B);
  assert(controller.lampsForA().red && controller.lampsForB().red);
  controller.tick(1600);
  assert(controller.phase() == IntersectionPhase::B_GREEN);
  assert(!controller.buzzerActive());
  assertNoConflict(controller);

  // A B priority command during A green uses yellow then all-red, never a direct switch.
  const SignalTiming remoteTiming = {100, 30000, 10000, 60000, 200, 300};
  TrafficLightStateMachine remote(remoteTiming);
  remote.begin(0);
  remote.tick(100);  // A green
  remote.requestGreen(false, 45000, 100);
  assert(remote.phase() == IntersectionPhase::A_YELLOW);
  remote.tick(300);
  assert(remote.phase() == IntersectionPhase::TRANSITION_ALL_RED_TO_B);
  remote.tick(600);
  assert(remote.phase() == IntersectionPhase::B_GREEN);
  assert(remote.activeGreenMs() == 45000);
  assertNoConflict(remote);

  controller.setManualAllRed(true, 1600);
  assert(controller.phase() == IntersectionPhase::MANUAL_ALL_RED);
  assert(controller.lampsForA().red && controller.lampsForB().red);
  controller.setManualAllRed(false, 1700);
  assert(controller.phase() == IntersectionPhase::STARTUP_ALL_RED);
  assertNoConflict(controller);

  controller.enterFailsafe();
  assert(controller.phase() == IntersectionPhase::FAILSAFE_ALL_RED);
  assert(controller.lampsForA().red && controller.lampsForB().red);
  assertNoConflict(controller);

  // Requested 5 s is capped by a 2 s maximum green time.
  const SignalTiming maximumTest = {100, 5000, 500, 2000, 200, 300};
  TrafficLightStateMachine capped(maximumTest);
  assert(capped.activeGreenMs() == 2000);

  std::cout << "traffic light state-machine tests passed\n";
}
