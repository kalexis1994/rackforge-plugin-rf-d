import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from filter_input_reference import step


class FilterInputReferenceTest(unittest.TestCase):
    def test_both_r61_readings_preserve_charge_and_kcl(self):
        for r61 in (200, 200000):
            out = step(dt_s=1e-4, bus_v=1, previous_bus_v=0,
                       previous_base_v=0, previous_bottom_v=0, r61_ohm=r61)
            self.assertAlmostEqual(out["base_kcl_residual_a"], 0, delta=1e-13)
            self.assertAlmostEqual(out["bottom_kcl_residual_a"], 0, delta=1e-13)
            self.assertGreater(out["board_input_current_a"], 0)
            self.assertGreater(out["base_v"], out["bottom_v"])
            self.assertGreater(out["bottom_v"], 0)

    def test_dc_blocks_bus_when_active_boundaries_are_zero(self):
        for r61 in (200, 200000):
            # At the settled state the ideal capacitor draws no current,
            # regardless of constant BUS voltage.
            out = step(dt_s=1e-4, bus_v=3, previous_bus_v=3,
                       previous_base_v=0, previous_bottom_v=0, r61_ohm=r61)
            self.assertAlmostEqual(out["board_input_current_a"], 0, delta=1e-13)
            self.assertAlmostEqual(out["base_v"], 0, delta=1e-13)

    def test_active_boundary_currents_enter_both_node_balances(self):
        common = dict(dt_s=1e-3, bus_v=0.6, previous_bus_v=0.2,
                      previous_base_v=0.05, previous_bottom_v=-0.02,
                      q29_base_current_a=2e-6, ladder_bottom_current_a=-5e-6)
        low = step(**common, r61_ohm=200)
        high = step(**common, r61_ohm=200000)
        for out in (low, high):
            self.assertAlmostEqual(out["base_kcl_residual_a"], 0, delta=1e-13)
            self.assertAlmostEqual(out["bottom_kcl_residual_a"], 0, delta=1e-13)
        self.assertNotAlmostEqual(low["bottom_v"], high["bottom_v"], delta=1e-5)

    def test_documentary_conflict_must_be_selected(self):
        with self.assertRaises(ValueError):
            step(dt_s=1e-4, bus_v=1, previous_bus_v=0,
                 previous_base_v=0, previous_bottom_v=0, r61_ohm=470)


if __name__ == "__main__":
    unittest.main()
