"""Independent KCL checks for the conditional coupled VCO 1 DC load line."""

import math
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from neg4_reference import conditional_reference_v
from vco1_ideal_dc_loadline import circuit_values, conditional_qc_drive, evaluate_current, find_candidate_roots
from vco1_ideal_pair_reference import thermal_voltage_v


CONTROLS = {name: -2.1 for name in ("BEND", "TUNE", "KEYBOARD", "MOD", "EXT", "OSC1_RANGE")}


class CoupledIdealDcTests(unittest.TestCase):
    def test_candidate_satisfies_both_kcl_nodes_and_pair_ratio(self) -> None:
        reference = conditional_reference_v(0)
        roots = find_candidate_roots(CONTROLS, 500, 0.5, reference, 1, 298.15)
        self.assertEqual(len(roots), 1)
        root = roots[0]
        values = circuit_values()
        ia = root["qa_current_a_imposed"]
        ib = root["qb_current_a_conditional"]
        emitter = root["qc_emitter_v"]
        vs, vn = values["V_NEG5"], values["V_NEG10"]
        vo = root["ic1_output_v"]
        self.assertAlmostEqual(ia, 17.0673818298e-6, places=12)
        self.assertAlmostEqual(ia + ib, (emitter - vn) / values["R79"] +
                               (emitter - vs) / values["R42"])
        summer_kcl = sum((vs - CONTROLS[name]) / resistance for name, resistance in values["inputs"].items())
        summer_kcl += (vs - vn) / (values["R37"] + 500)
        summer_kcl += (vs - vo) / values["R20"] + (vs - emitter) / values["R42"]
        self.assertAlmostEqual(summer_kcl, 0, places=14)
        log_ratio = math.log(ia / ib)
        voltage_ratio = (root["qa_base_v_ideal"] - root["qb_base_v_ideal"]) / thermal_voltage_v(298.15)
        self.assertAlmostEqual(log_ratio, voltage_ratio, places=12)
        self.assertTrue(root["ic1_output_within_schematic_rails"])
        self.assertTrue(root["qc_emitter_between_minus10_and_minus5"])

    def test_ic1_supply_trace_matches_coarse_rail_gate(self) -> None:
        import json
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        ic1 = next(part for part in graph["parts"] if part["ref"] == "IC1")
        self.assertEqual(ic1["package_pins"]["positive_supply"], 7)
        self.assertEqual(ic1["package_pins"]["negative_supply"], 4)
        self.assertEqual(ic1["terminals"]["positive_supply"], "GND")
        self.assertEqual(ic1["terminals"]["negative_supply"], "NEG10_V")

    def test_ic3_required_output_obeys_r69_r78_dc_kcl(self) -> None:
        import json
        graph = json.loads((ROOT / "evidence" / "vco1_ramp_graph.json").read_text(encoding="utf-8"))
        ic3 = next(part for part in graph["parts"] if part["ref"] == "IC3")
        self.assertEqual(ic3["package_pins"]["positive_supply"], 7)
        self.assertEqual(ic3["package_pins"]["negative_supply"], 4)
        self.assertEqual(ic3["terminals"]["positive_supply"], "POS10_V")
        self.assertEqual(ic3["terminals"]["negative_supply"], "NEG10_V")
        root = find_candidate_roots(CONTROLS, 500, 0.5, conditional_reference_v(0), 1, 298.15)[0]
        drive = conditional_qc_drive(root, 0.7)
        values = circuit_values()
        base = drive["qc_base_v_conditional"]
        output = drive["ic3_output_v_required_if_zero_base_current"]
        self.assertAlmostEqual((base - output) / values["R69"] +
                               (base - values["V_NEG10"]) / values["R78_dc"], 0, places=14)
        self.assertAlmostEqual(output, -2.8054962445, places=9)
        self.assertTrue(drive["ic3_output_between_schematic_rails"])

    def test_trim_changes_candidate_without_claiming_calibration(self) -> None:
        reference = conditional_reference_v(0)
        currents = [find_candidate_roots(CONTROLS, r11, 0.5, reference, 1, 298.15)[0]["qa_current_a_imposed"]
                    for r11 in (0, 500, 1000)]
        self.assertLess(currents[0], currents[1])
        self.assertLess(currents[1], currents[2])

    def test_search_and_nonphysical_inputs_are_explicit(self) -> None:
        reference = conditional_reference_v(0)
        with self.assertRaises(ValueError):
            find_candidate_roots(CONTROLS, 500, 0.5, reference, 1, 298.15, 1e-3, 1e-9)
        with self.assertRaises(ValueError):
            evaluate_current(1e-5, CONTROLS, 1001, 0.5, reference, 1, 298.15)
        with self.assertRaises(ValueError):
            evaluate_current(1e-5, CONTROLS, 500, 0.5, reference, 0, 298.15)
        with self.assertRaises(ValueError):
            evaluate_current(1e-5, {"KEYBOARD": -2.1}, 500, 0.5, reference, 1, 298.15)


if __name__ == "__main__":
    unittest.main()
