"""R21/active-amp Schur reduction against an explicit 65-node assembly."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from filter_emphasis_loop_small_signal_reference import series_return_admittance_s
from filter_ladder_ebers_moll_dc_reference import _solve_linear
from filter_panel_headphone_reference import panel_with_headphone_matrices
from headphone_amp_active_dc_reference import (
    NODES, conditional_headphone_amp_dc, headphone_amp_dc_jacobian)
from headphone_coupled_ac_reference import coupled_headphone_ac
from output_diode_reference import diode_model_from_reference


class HeadphoneCoupledAcTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from test_filter_vca_output_small_signal_reference import FilterVcaOutputSmallSignalTest
        FilterVcaOutputSmallSignalTest.setUpClass()
        fixture = FilterVcaOutputSmallSignalTest()
        cls.ladder = fixture.ladder
        cls.recovery = fixture.recovery
        cls.output_dc = fixture.dc()

    def args(self):
        return dict(ladder_dc=self.ladder, recovery_dc=self.recovery,
                    cascaded_output_dc=self.output_dc,
                    r20_wiper_to_ground_ohm=2500,
                    hi_load_ohm=10000, lo_load_ohm=100000,
                    r21_wiper_to_ground_ohm=2000,
                    r14_pin7_to_pin6_ohm=0,
                    r73_bottom_side_to_wiper_ohm=500,
                    transistor_is_a=1e-14, beta_forward=160,
                    beta_reverse=5, temperature_k=300,
                    diode_model=diode_model_from_reference(
                        ideality=1.5, forward_voltage_at_100ma_v=0.7,
                        temperature_k=300),
                    tip_load_ohm=32, ring_load_ohm=32)

    def test_coupling_and_sw18_off(self):
        args = self.args()
        for frequency in (0, 30, 100, 1000):
            for switch in (True, False):
                with self.subTest(frequency=frequency, sw18_on=switch):
                    result = coupled_headphone_ac(
                        **args, frequency_hz=frequency, sw18_on=switch)
                    self.assertLess(result["max_upstream_kcl_residual_a_per_bus_v"], 1e-11)
                    self.assertLess(result["max_amp_kcl_residual_a_per_pin7_v"], 1e-11)
                    self.assertEqual(result["j7_tip_v_per_bus_v"],
                                     result["j7_ring_v_per_bus_v"])
                    if not switch:
                        self.assertEqual(result["j4_hi_v_per_bus_v"], 0)
                        self.assertEqual(result["j5_lo_v_per_bus_v"], 0)
                        if frequency:
                            self.assertGreater(abs(result["j7_tip_v_per_bus_v"]), 0)
        self.assertAlmostEqual(abs(coupled_headphone_ac(
            **args, frequency_hz=100)["j7_tip_v_per_bus_v"]),
            0.050528528878621366, delta=1e-6)

    def test_one_port_reduction_matches_explicit_65_node_network(self):
        args = self.args()
        frequency = 100
        reduced = coupled_headphone_ac(**args, frequency_hz=frequency)
        s = 2j*math.pi*frequency
        g, c, bus_c = panel_with_headphone_matrices(
            ladder_dc=self.ladder, recovery_dc=self.recovery,
            cascaded_output_dc=self.output_dc,
            r20_wiper_to_ground_ohm=2500, hi_load_ohm=10000,
            lo_load_ohm=100000, r21_wiper_to_ground_ohm=2000,
            headphone_wiper_load_ohm=1e12)
        count = 65
        matrix = [[0j]*count for _ in range(count)]
        for i in range(53):
            for j in range(53):
                matrix[i][j] = -g[i][j]+s*c[i][j]
        matrix[52][52] -= 1e-12
        device = {key: args[key] for key in (
            "transistor_is_a", "beta_forward", "beta_reverse",
            "temperature_k", "diode_model")}
        dc = conditional_headphone_amp_dc(**device)
        bias = [dc["node_v"][name] for name in NODES]
        tangent = headphone_amp_dc_jacobian(bias, **device)
        for row in range(11):
            for col in range(11):
                matrix[53+row][53+col] += tangent[row][col]

        def cap(i, j, farad):
            y = s*farad
            matrix[i][i] += y
            matrix[j][j] += y
            matrix[i][j] -= y
            matrix[j][i] -= y

        cap(52, 53, 2.5e-6)  # C19 from panel R21 to Q16 base
        cap(53+7, 53+8, 220e-12)  # C15
        cap(53+10, 64, 400e-6)  # C21
        matrix[64][64] += 1/390+2/32
        return_y = series_return_admittance_s(
            frequency_hz=frequency, r14_pin7_to_pin6_ohm=0,
            r73_bottom_side_to_wiper_ohm=500)
        for i in (7, 22):
            matrix[i][i] += return_y
        matrix[7][22] -= return_y
        matrix[22][7] -= return_y
        rhs = [0j]*count
        rhs[6] = s*bus_c
        explicit = _solve_linear(matrix, rhs)
        self.assertAlmostEqual(explicit[52], reduced["r21_wiper_v_per_bus_v"],
                               delta=1e-10)
        self.assertAlmostEqual(explicit[53], reduced["q16_base_v_per_bus_v"],
                               delta=1e-10)
        self.assertAlmostEqual(explicit[64], reduced["j7_tip_v_per_bus_v"],
                               delta=1e-10)
        self.assertAlmostEqual(explicit[49], reduced["j4_hi_v_per_bus_v"],
                               delta=1e-10)


if __name__ == "__main__":
    unittest.main()
