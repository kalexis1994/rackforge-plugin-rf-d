"""AC consistency and control response of the forty-node cascade."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_vca_cascaded_small_signal_reference import cascaded_loaded_matrices, filter_with_cascaded_vca
from filter_vca1_loaded_small_signal_reference import loaded_matrices
from vca_cascaded_dc_reference import DEVICE_NAMES, conditional_cascaded_vca_dc


class FilterVcaCascadedSmallSignalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca1_active_small_signal_reference import FilterVca1ActiveSmallSignalTest
        FilterVca1ActiveSmallSignalTest.setUpClass()
        cls.ladder = FilterVca1ActiveSmallSignalTest.ladder
        cls.recovery = FilterVca1ActiveSmallSignalTest.recovery

    def dc(self, control):
        return conditional_cascaded_vca_dc(
            upper_supply_v=9.5, first_loudness_v=control,
            second_loudness_base_v=control,
            first_balance_left_ohm=12.5, second_balance_left_ohm=50,
            is_a={n: 1e-14 for n in DEVICE_NAMES},
            beta_forward={n: 100 for n in DEVICE_NAMES},
            beta_reverse={n: 5 for n in DEVICE_NAMES},
            temperature_k=298.15)

    def ac(self, control, frequency):
        return filter_with_cascaded_vca(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_vca_dc=self.dc(control), frequency_hz=frequency,
            r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)

    def test_matrix_shares_bases_and_removes_passive_duplicate(self):
        dc = self.dc(2)
        g, c, bus_c = cascaded_loaded_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_vca_dc=dc)
        old_g, old_c, old_bus = loaded_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery)
        self.assertEqual(len(g), 40)
        self.assertEqual(bus_c, old_bus)
        self.assertEqual(c[24][25], old_c[24][25])
        self.assertAlmostEqual(g[25][25],
                               old_g[25][25] + 1/820
                               + dc["conductance_matrix_s"][0][0],
                               delta=1e-12)
        self.assertAlmostEqual(g[26][26],
                               old_g[26][26] + 1/820 + 1/510
                               + dc["conductance_matrix_s"][1][1],
                               delta=1e-12)

    def test_control_changes_second_differential_output(self):
        off = self.ac(0, 100)
        on = self.ac(2, 100)
        self.assertLess(abs(off["second_vca_differential_collector_v_per_bus_v"]),
                        1e-8)
        self.assertGreater(abs(on["second_vca_differential_collector_v_per_bus_v"]),
                           0.1)
        self.assertGreater(abs(on["first_balance_wiper_v_per_bus_v"]), 0)
        self.assertGreater(abs(on["second_balance_wiper_v_per_bus_v"]), 0)
        self.assertEqual(len(on["vca_node_v_per_bus_v"]), 15)

    def test_ac_kcl_and_dc_blocking(self):
        for frequency in (0, 30, 100, 1000):
            with self.subTest(frequency=frequency):
                out = self.ac(2, frequency)
                self.assertLess(out["max_linear_kcl_residual_a_per_bus_v"], 1e-11)
                if frequency == 0:
                    self.assertEqual(out["second_vca_differential_collector_v_per_bus_v"], 0)
                    self.assertEqual(out["r2_current_a_per_bus_v"], 0)

    def test_invalid_r73_rejected(self):
        with self.assertRaises(ValueError):
            filter_with_cascaded_vca(
                ladder_dc=self.ladder, recovery_dc=self.recovery,
                cascaded_vca_dc=self.dc(2), frequency_hz=100,
                r14_pin7_to_pin6_ohm=0,
                r73_bottom_side_to_wiper_ohm=501)


if __name__ == "__main__":
    unittest.main()
