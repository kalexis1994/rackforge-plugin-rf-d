import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from loudness_contour_reference import Controls, Network, Semiconductors
from loudness_contour_probes import OUTPUT, generate


class LoudnessContour(unittest.TestCase):
    def test_independent_fold_is_reproduced_and_not_selected(self):
        actual = generate()
        self.assertEqual(actual, json.loads(OUTPUT.read_text(encoding="utf-8")))
        self.assertFalse(actual["physical_switching_admitted"])
        for route in ("analytic", "independent_fd"):
            probe = actual["fold"][route]
            self.assertIsNone(probe["selected"])
            self.assertEqual(len(probe["roots"]), 2)
            self.assertEqual(probe["rejected"][0]["seed_policy"], "previous")
            for root in probe["roots"]:
                self.assertLess(root["diagnostics"]["max_kcl_a"], 1e-11)
                self.assertLess(root["diagnostics"]["correction_v"], 1e-8)

    def test_entire_jacobian_and_charge_history(self):
        network = Network()
        state, _ = network.initial_state()
        old = copy.deepcopy(state)
        state, _ = network.step(state, 10.0, .001)
        self.assertEqual(old.capacitor_v["C7"], 7.90777438396214e-09)
        x = [state.node_v[n] for n in network.nodes]
        _, jac = network.evaluate(x, 10.0, old, .001)
        for col in range(len(x)):
            left, right = x.copy(), x.copy()
            left[col] -= 1e-6
            right[col] += 1e-6
            a, _ = network.evaluate(left, 10.0, old, .001)
            b, _ = network.evaluate(right, 10.0, old, .001)
            for row in range(len(x)):
                fd = (b[row]-a[row])/2e-6
                self.assertLess(abs(jac[row][col]-fd), 1e-9+1e-7*abs(fd))
        snapshot = copy.deepcopy(state)
        with self.assertRaises(ValueError):
            network.step(state, 10.0, .001, iterations=1)
        self.assertEqual(state, snapshot)

    def test_exact_pot_endpoints_and_invalid_domains(self):
        for sustain in (0.0, 5000.0):
            n = Network(Controls(attack_ohm=0, decay_ohm=0, sustain_lower_ohm=sustain))
            expected = "GROUND" if sustain == 0 else "PLUS_10"
            self.assertEqual(n.alias["SUSTAIN_WIPER"], expected)
            self.assertEqual(n.alias["TIMING_C2"], n.alias["DECAY_OUT"])
            self.assertEqual(n.alias["ATTACK_PANEL_IN"], n.alias["TIMING_C2"])
        for value in (-1, 1000001, math.nan, math.inf):
            with self.assertRaises(ValueError):
                Network(Controls(attack_ohm=value))
        with self.assertRaises(ValueError):
            Network(devices=Semiconductors(beta_forward=0))
        n = Network()
        s, _ = n.initial_state()
        for source, dt in ((11, .001), (math.nan, .001), (0, 0), (0, math.inf)):
            with self.assertRaises(ValueError):
                n.probe_step_roots(s, source, dt)


if __name__ == "__main__":
    unittest.main()
