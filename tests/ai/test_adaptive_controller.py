import unittest

from ai.adaptive_controller import AdaptiveTrafficController, ApproachInput, ControllerParameters, Density


def inputs(a_count=4, b_count=15, a_density=Density.LOW, b_density=Density.HIGH, a_wait=0, b_wait=0):
    return {"A": ApproachInput(a_count, a_density, a_wait), "B": ApproachInput(b_count, b_density, b_wait)}


class AdaptiveTrafficControllerTests(unittest.TestCase):
    def setUp(self):
        self.controller = AdaptiveTrafficController()

    def test_transfers_a_unused_time_to_higher_demand_b(self):
        decision = self.controller.decide(active_signal="A", traffic=inputs(), allocated_green_time=30, actual_clearance_time=15)
        self.assertEqual(decision.unused_time, 15)
        self.assertEqual(decision.transferred_time, 15)
        self.assertEqual(decision.target_signal, "B")
        self.assertEqual(decision.final_green_time, 45)
        self.assertEqual(decision.transition_sequence, ("YELLOW", "ALL_RED", "GREEN"))

    def test_transfers_b_unused_time_to_higher_demand_a(self):
        decision = self.controller.decide(active_signal="B", traffic=inputs(15, 4, Density.HIGH, Density.LOW), allocated_green_time=30, actual_clearance_time=15)
        self.assertEqual((decision.target_signal, decision.final_green_time), ("A", 45))

    def test_does_not_transfer_before_minimum_green(self):
        decision = self.controller.decide(active_signal="A", traffic=inputs(), allocated_green_time=30, actual_clearance_time=9)
        self.assertEqual(decision.reason, "MINIMUM_GREEN_NOT_MET")
        self.assertIsNone(decision.target_signal)

    def test_max_green_caps_transfer(self):
        decision = self.controller.decide(active_signal="A", traffic=inputs(), allocated_green_time=60, actual_clearance_time=10)
        self.assertEqual((decision.unused_time, decision.transferred_time, decision.final_green_time), (50, 30, 60))

    def test_no_transfer_when_opposite_demand_is_not_higher(self):
        decision = self.controller.decide(active_signal="A", traffic=inputs(10, 10, Density.HIGH, Density.MEDIUM), allocated_green_time=30, actual_clearance_time=15)
        self.assertEqual(decision.reason, "NO_HIGHER_OPPOSITE_DEMAND")
        self.assertEqual(decision.transferred_time, 0)

    def test_max_wait_prevents_starvation_with_safe_switch(self):
        decision = self.controller.decide(active_signal="A", traffic=inputs(a_wait=0, b_wait=60), allocated_green_time=30, actual_clearance_time=12)
        self.assertEqual(decision.reason, "MAX_WAIT_PRIORITY")
        self.assertEqual((decision.target_signal, decision.final_green_time), ("B", 30))
        self.assertEqual(decision.transition_sequence, ("YELLOW", "ALL_RED", "GREEN"))

    def test_no_unused_time_does_not_switch(self):
        decision = self.controller.decide(active_signal="A", traffic=inputs(), allocated_green_time=30, actual_clearance_time=30)
        self.assertEqual(decision.reason, "NO_UNUSED_GREEN_TIME")
        self.assertIsNone(decision.target_signal)

    def test_rejects_invalid_active_signal(self):
        with self.assertRaises(ValueError):
            self.controller.decide(active_signal="C", traffic=inputs(), allocated_green_time=30, actual_clearance_time=15)

    def test_timing_parameter_validation(self):
        with self.assertRaises(ValueError):
            ControllerParameters(min_green=40, normal_green=30)


if __name__ == "__main__":
    unittest.main()
